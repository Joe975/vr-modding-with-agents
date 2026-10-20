"""Check VR eye captures and print a verdict, so the agent reads one line per check instead of
looking at the images.

  python frame_check.py left.png [right.png] [--ref golden.png] [--reject waiting.png ...]

Checks, cheapest first:
  blank   every image has some contrast (catches black, white and flat loading frames)
  reject  no image looks like a known-bad reference (the runtime's waiting screen, a loading screen)
  ref     the left image looks like a golden capture taken at the same scripted pose
  stereo  the two eyes show the same scene, are not identical copies, and line up vertically

Exit code 0 when everything passes, 1 otherwise. On a failure it writes `<image>.preview.png`
beside each image, downscaled to --max-side (720 px by default), for the agent to look at. The
thresholds are starting defaults: calibrate them on your own captures.
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


def shift(a, b):
    """Phase correlation: (dx, dy) in pixels such that a is roughly b moved by (dx, dy)."""
    window = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    fa = np.fft.fft2((a - a.mean()) * window)
    fb = np.fft.fft2((b - b.mean()) * window)
    cross = fa * np.conj(fb)
    peak = np.fft.ifft2(cross / (np.abs(cross) + 1e-12)).real
    y, x = np.unravel_index(np.argmax(peak), peak.shape)
    h, w = peak.shape
    return (x - w if x > w // 2 else x), (y - h if y > h // 2 else y)


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


def run_checks(images, ref=None, reject=(), min_contrast=0.02, min_ref=0.6, max_reject=0.85,
               min_corr=0.4, max_dy=0.02):
    """images: {name: gray array}, first is the left eye. Returns [(ok, line)]."""
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
    if len(images) == 2:
        (_, left), (_, right) = images.items()
        st = stereo(left, right)
        results.append((not st["identical"], "stereo  eyes are " + ("identical copies (mono?)" if st["identical"] else "different images")))
        results.append((st["corr"] >= min_corr, f"stereo  correlation {st['corr']:.2f} (min {min_corr})"))
        results.append((abs(st["dy"]) <= max_dy,
                        f"stereo  shift dx {st['dx']:+.3f} dy {st['dy']:+.3f} of frame (|dy| max {max_dy})"))
    return results


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
    args = parser.parse_args(argv)
    if len(args.images) > 2:
        parser.error("give one or two images")
    labels = ["left", "right"] if len(args.images) == 2 else ["image"]
    images = {f"{label} {p.name}": load_gray(p) for label, p in zip(labels, args.images)}
    results = run_checks(
        images,
        ref=(args.ref.name, load_gray(args.ref)) if args.ref else None,
        reject=[(p.name, load_gray(p)) for p in args.reject],
        min_contrast=args.min_contrast, min_ref=args.min_ref, max_reject=args.max_reject,
        min_corr=args.min_corr, max_dy=args.max_dy)
    failed = sum(not ok for ok, _ in results)
    for ok, line in results:
        print(("PASS " if ok else "FAIL ") + line)
    if failed:
        previews = [write_preview(p, args.max_side) for p in args.images]
        print(f"VERDICT FAIL ({failed} of {len(results)} checks). Previews: " + ", ".join(str(p) for p in previews))
        return 1
    print(f"VERDICT PASS ({len(results)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
