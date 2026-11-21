"""Check VR eye captures and print a verdict, so the agent reads one line per check instead of
looking at the images.

  python frame_check.py left.png [right.png] [--ref golden.png] [--reject waiting.png ...]
                        [--near x0,y0,x1,y1 --far x0,y0,x1,y1] [--same-pose]

Checks, cheapest first:
  blank   every image has some contrast (catches black, white and flat loading frames)
  reject  no image looks like a known-bad reference (the runtime's waiting screen, a loading screen)
  ref     the left image looks like a golden capture taken at the same scripted pose
  stereo  the two eyes show the same scene, are not identical copies, and line up vertically
  depth   parts of the scene sit at different disparities; one disparity across the whole frame
          is a flat picture (a 2D panel, a mono image shown at one depth), not a rendered scene.
          Tiles are searched around the eyes' overall offset, so an asymmetric headset field of
          view doesn't push them out of reach. Too few matched tiles can't judge depth (UNSURE).
  near    with --near and --far (boxes as fractions of the image), the near box's disparity
          (left position minus right position, in source pixels) exceeds the far box's
  pose    with --same-pose, for eyes rendered from one pose (zero separation): every region of the
          two eyes lines up within --max-pose-px. A post effect that warps the finished image
          (lens distortion, a projection warp) shows here as a few pixels, often mirrored

The last line is the verdict, with its exit code:
  0  VERDICT PASS          every check passed, and there was enough to judge
  1  VERDICT FAIL          a check failed
  2  VERDICT INCONCLUSIVE  nothing failed, but a check couldn't judge (UNSURE), one image can't
                           show stereo, or without --reject or --ref nothing tells the game's view
                           from another screen
  2  ERROR                 the script couldn't run (unreadable image, bad arguments)
On FAIL or INCONCLUSIVE it writes `<image>.preview.png` beside each image, downscaled to
--max-side (720 px by default), for the agent to look at. The thresholds are starting defaults:
calibrate them on your own captures.
"""
import argparse
import sys
from pathlib import Path

import numpy as np


def load_gray(path):
    from PIL import Image  # only the CLI needs Pillow; the checks work on arrays
    return np.asarray(Image.open(path).convert("L"), dtype=np.float64) / 255.0


def fit(gray, shape):
    """Area-average down by a whole factor, then nearest-sample to exactly `shape`."""
    factor = max(1, min(gray.shape[0] // shape[0], gray.shape[1] // shape[1]) // 2)
    h, w = (gray.shape[0] // factor) * factor, (gray.shape[1] // factor) * factor
    small = gray[:h, :w].reshape(h // factor, factor, w // factor, factor).mean((1, 3))
    rows = (np.arange(shape[0]) * small.shape[0] / shape[0]).astype(int)
    cols = (np.arange(shape[1]) * small.shape[1] / shape[1]).astype(int)
    return small[np.ix_(rows, cols)]


def working_shape(gray, long_side=256):
    h, w = gray.shape
    scale = long_side / max(h, w)
    return max(8, round(h * scale)), max(8, round(w * scale))


def contrast(gray):
    return float(gray.std())


def similarity(a, b, block=8):
    """Mean SSIM over non-overlapping blocks, after fitting both images to the same small size."""
    shape = working_shape(a)
    a, b = fit(a, shape), fit(b, shape)
    h, w = (shape[0] // block) * block, (shape[1] // block) * block
    A = a[:h, :w].reshape(h // block, block, w // block, block)
    B = b[:h, :w].reshape(h // block, block, w // block, block)
    ma, mb = A.mean((1, 3)), B.mean((1, 3))
    va, vb = A.var((1, 3)), B.var((1, 3))
    cov = ((A - ma[:, None, :, None]) * (B - mb[:, None, :, None])).mean((1, 3))
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    ssim = ((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2))
    return float(ssim.mean())


def correlation_peak(a, b):
    window = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    fa = np.fft.fft2((a - a.mean()) * window)
    fb = np.fft.fft2((b - b.mean()) * window)
    cross = fa * np.conj(fb)
    peak = np.fft.ifft2(cross / (np.abs(cross) + 1e-12)).real
    y, x = np.unravel_index(np.argmax(peak), peak.shape)
    return peak, int(y), int(x)


def shift(a, b):
    """Phase correlation: (dx, dy) in pixels such that a is roughly b moved by (dx, dy)."""
    peak, y, x = correlation_peak(a, b)
    h, w = peak.shape
    return (x - w if x > w // 2 else x), (y - h if y > h // 2 else y)


def subpixel_shift(a, b):
    """As shift(), refined to a fraction of a pixel by a parabola through the peak's neighbours."""
    peak, y, x = correlation_peak(a, b)
    h, w = peak.shape

    def refine(before, at, after):
        bend = before - 2 * at + after
        return 0.0 if abs(bend) < 1e-12 else 0.5 * (before - after) / bend

    fx = x + refine(peak[y, (x - 1) % w], peak[y, x], peak[y, (x + 1) % w])
    fy = y + refine(peak[(y - 1) % h, x], peak[y, x], peak[(y + 1) % h, x])
    return (fx - w if fx > w / 2 else fx), (fy - h if fy > h / 2 else fy)


def parse_box(text):
    """'x0,y0,x1,y1' as fractions of the image (0-1)."""
    box = tuple(float(v) for v in text.split(","))
    if len(box) != 4 or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
        raise ValueError(f"box {text!r}: give x0,y0,x1,y1 as fractions with x0 < x1 and y0 < y1")
    return box


def crop(gray, box):
    h, w = gray.shape
    return gray[round(box[1] * h):round(box[3] * h), round(box[0] * w):round(box[2] * w)]


def region_shift(left, right, box, long_side=512, min_contrast=0.02):
    """(dx, dy) of a box of the left eye against the same box of the right eye, in the left
    image's source pixels: dx is the left position minus the right position. None if the box has
    too little texture to tell."""
    a, b = crop(left, box), crop(right, box)
    if min(a.shape) < 8 or min(b.shape) < 8 or a.std() < min_contrast or b.std() < min_contrast:
        return None
    factor = max(1, -(-max(a.shape) // long_side))  # whole-factor block means keep sub-pixel detail
    shape = (min(a.shape[0], b.shape[0]) // factor, min(a.shape[1], b.shape[1]) // factor)

    def down(g):
        g = g[:shape[0] * factor, :shape[1] * factor]
        return g.reshape(shape[0], factor, shape[1], factor).mean((1, 3))

    dx, dy = subpixel_shift(down(a), down(b))
    return dx * factor, dy * factor


def same_pose(left, right, grid=(3, 4), min_contrast=0.02):
    """Shifts of a grid of regions between two eyes rendered from one pose: [(box, dx, dy)]."""
    found = []
    for row in range(grid[0]):
        for col in range(grid[1]):
            box = (col / grid[1], row / grid[0], (col + 1) / grid[1], (row + 1) / grid[0])
            s = region_shift(left, right, box, min_contrast=min_contrast)
            if s is not None:
                found.append((box, *s))
    return found


def stereo(left, right):
    shape = working_shape(left)
    l, r = fit(left, shape), fit(right, shape)
    dx, dy = shift(l, r)
    # Correlate after undoing the shift, so ordinary disparity doesn't read as a mismatch.
    h, w = shape
    la = l[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)]
    ra = r[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    corr = float(np.corrcoef(la.ravel(), ra.ravel())[0, 1]) if la.size > 1 and la.std() and ra.std() else 0.0
    return {
        "identical": left.shape == right.shape and float(np.abs(left - right).max()) < 1 / 255,
        "corr": corr,
        "dx": dx / shape[1],
        "dy": dy / shape[0],
    }


def disparities(left, right, grid=(3, 4), reach=0.15, min_contrast=0.02, min_match=0.6, center=0):
    """Horizontal disparity of each textured tile of the left eye, in working-size pixels, found
    by sliding the tile along the same rows of the right eye, within `reach` of the frame width
    around `center` (the eyes' overall offset, in the same units as the result). Tiles that match
    nowhere are left out."""
    shape = working_shape(left)
    l, r = fit(left, shape), fit(right, shape)
    h, w = shape
    th, tw, most = h // grid[0], w // grid[1], int(w * reach)
    found = []
    for y in range(0, th * grid[0], th):
        for x in range(0, tw * grid[1], tw):
            tile = l[y:y + th, x:x + tw]
            if tile.std() < min_contrast:
                continue
            tile = (tile - tile.mean()) / tile.std()
            best, best_dx = min_match, None
            for dx in range(center - most, center + most + 1):  # left[x] is right[x - dx], as in shift()
                if 0 <= x - dx and x - dx + tw <= w:
                    other = r[y:y + th, x - dx:x - dx + tw]
                    if other.std() > 1e-6:
                        score = float((tile * (other - other.mean())).mean() / other.std())
                        if score > best:
                            best, best_dx = score, dx
            if best_dx is not None:
                found.append(best_dx)
    return found


def depth(found, min_px=2):
    """How many tiles sit at least min_px away from the most common disparity."""
    if not found:
        return 0
    values, counts = np.unique(found, return_counts=True)
    mode = values[np.argmax(counts)]
    return int(sum(abs(d - mode) >= min_px for d in found))


def run_checks(images, ref=None, reject=(), min_contrast=0.02, min_ref=0.6, max_reject=0.85,
               min_corr=0.4, max_dy=0.02, min_depth_tiles=2, min_matched_tiles=4,
               near=None, far=None, min_near_far_px=1.0, same_pose_mode=False, max_pose_px=1.0):
    """images: {name: gray array}, first is the left eye. Returns [(ok, line)], where ok is True,
    False, or None when the check couldn't judge."""
    results = []
    for name, gray in images.items():
        c = contrast(gray)
        results.append((c >= min_contrast, f"blank   {name}: contrast {c:.3f} (min {min_contrast})"))
        for bad_name, bad in reject:
            s = similarity(gray, bad)
            results.append((s <= max_reject, f"reject  {name} vs {bad_name}: similarity {s:.2f} (max {max_reject})"))
    first_name, first = next(iter(images.items()))
    if ref is not None:
        s = similarity(first, ref[1])
        results.append((s >= min_ref, f"ref     {first_name} vs {ref[0]}: similarity {s:.2f} (min {min_ref})"))
    if len(images) == 2 and same_pose_mode:
        (_, left), (_, right) = images.items()
        found = same_pose(left, right, min_contrast=min_contrast)
        if not found:
            results.append((None, "pose    no region has enough texture to compare"))
        else:
            box, dx, dy = max(found, key=lambda f: max(abs(f[1]), abs(f[2])))
            worst = max(abs(dx), abs(dy))
            results.append((worst <= max_pose_px,
                            f"pose    worst of {len(found)} regions dx {dx:+.2f} dy {dy:+.2f} px at "
                            f"x {box[0]:.2f}-{box[2]:.2f} y {box[1]:.2f}-{box[3]:.2f} (max {max_pose_px} px)"))
    elif len(images) == 2:
        (_, left), (_, right) = images.items()
        st = stereo(left, right)
        results.append((not st["identical"], "stereo  eyes are " + ("identical copies (mono?)" if st["identical"] else "different images")))
        results.append((st["corr"] >= min_corr, f"stereo  correlation {st['corr']:.2f} (min {min_corr})"))
        results.append((abs(st["dy"]) <= max_dy,
                        f"stereo  shift dx {st['dx']:+.3f} dy {st['dy']:+.3f} of frame (|dy| max {max_dy})"))
        found = disparities(left, right, center=round(st["dx"] * working_shape(left)[1]))
        off = depth(found)
        if len(found) < min_matched_tiles:
            results.append((None, f"depth   only {len(found)} tiles matched (min {min_matched_tiles}): "
                                  f"can't tell depth"))
        else:
            results.append((off >= min_depth_tiles,
                            f"depth   {off} of {len(found)} matched tiles at another disparity "
                            f"(min {min_depth_tiles}; 0 means one flat picture)"))
        if near is not None and far is not None:
            n, f = region_shift(left, right, near), region_shift(left, right, far)
            if n is None or f is None:
                results.append((None, "near    a box has too little texture to measure"))
            else:
                results.append((n[0] - f[0] >= min_near_far_px,
                                f"near    near box disparity {n[0]:+.2f} px, far box {f[0]:+.2f} px "
                                f"(near must exceed far by {min_near_far_px} px)"))
    return results


def verdict(results, images, ref=None, reject=()):
    """('PASS' | 'FAIL' | 'INCONCLUSIVE', reason)."""
    failed = sum(ok is False for ok, _ in results)
    if failed:
        return "FAIL", f"{failed} of {len(results)} checks"
    missing = [line.split()[0] + " couldn't judge" for ok, line in results if ok is None]
    if len(images) < 2:
        missing.append("one image can't show stereo: give both eyes")
    if ref is None and not reject:
        missing.append("nothing tells the game's view from another screen: add --reject <the runtime's "
                       "waiting screen> or --ref <golden capture>")
    if missing:
        passed = sum(ok is True for ok, _ in results)
        return "INCONCLUSIVE", f"{passed} checks passed, but " + "; ".join(missing)
    return "PASS", f"{len(results)} checks"


def write_preview(path, max_side):
    from PIL import Image
    out = Path(path).with_suffix(".preview.png")
    with Image.open(path) as image:
        image.thumbnail((max_side, max_side))
        image.save(out)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("images", nargs="+", type=Path, help="left eye, then optionally the right eye")
    parser.add_argument("--ref", type=Path, help="golden capture of the left eye at the same pose")
    parser.add_argument("--reject", type=Path, action="append", default=[], help="known-bad screen; repeatable")
    parser.add_argument("--max-side", type=int, default=720, help="preview size on failure")
    parser.add_argument("--min-contrast", type=float, default=0.02)
    parser.add_argument("--min-ref", type=float, default=0.6)
    parser.add_argument("--max-reject", type=float, default=0.85)
    parser.add_argument("--min-corr", type=float, default=0.4)
    parser.add_argument("--max-dy", type=float, default=0.02)
    parser.add_argument("--min-depth-tiles", type=int, default=2)
    parser.add_argument("--min-matched-tiles", type=int, default=4)
    parser.add_argument("--near", type=parse_box, help="box on something near the eyes: x0,y0,x1,y1 fractions")
    parser.add_argument("--far", type=parse_box, help="box on something far away: x0,y0,x1,y1 fractions")
    parser.add_argument("--min-near-far-px", type=float, default=1.0)
    parser.add_argument("--same-pose", action="store_true",
                        help="the eyes were rendered from one pose (zero separation): they must line up")
    parser.add_argument("--max-pose-px", type=float, default=1.0)
    args = parser.parse_args(argv)
    if len(args.images) > 2:
        parser.error("give one or two images")
    if (args.near is None) != (args.far is None):
        parser.error("give --near and --far together")
    try:
        labels = ["left", "right"] if len(args.images) == 2 else ["image"]
        images = {f"{label} {p.name}": load_gray(p) for label, p in zip(labels, args.images)}
        ref = (args.ref.name, load_gray(args.ref)) if args.ref else None
        reject = [(p.name, load_gray(p)) for p in args.reject]
        results = run_checks(
            images, ref=ref, reject=reject,
            min_contrast=args.min_contrast, min_ref=args.min_ref, max_reject=args.max_reject,
            min_corr=args.min_corr, max_dy=args.max_dy, min_depth_tiles=args.min_depth_tiles,
            min_matched_tiles=args.min_matched_tiles, near=args.near, far=args.far,
            min_near_far_px=args.min_near_far_px, same_pose_mode=args.same_pose,
            max_pose_px=args.max_pose_px)
        for ok, line in results:
            print({True: "PASS ", False: "FAIL ", None: "UNSURE "}[ok] + line)
        word, reason = verdict(results, images, ref, reject)
        if word == "PASS":
            print(f"VERDICT PASS ({reason})")
            return 0
        previews = [write_preview(p, args.max_side) for p in args.images]
        print(f"VERDICT {word} ({reason}). Previews: " + ", ".join(str(p) for p in previews))
        return 1 if word == "FAIL" else 2
    except Exception as error:  # a crash is not a FAIL: nothing was judged
        print(f"ERROR {type(error).__name__}: {error}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
