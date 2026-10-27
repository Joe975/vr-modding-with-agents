"""Measure one-frame flicker in each eye of a both-eye mirror recording, and how much of it shows
in one eye only.

  python eye_flicker.py <prefix>[.rgb] [--marks marks.txt] [--from HH:MM:SS] [--to HH:MM:SS]
                        [--events] [--save-events DIR] [--max-one-eye 1.0]

The recording comes from `mirror_capture/openvr_mirror_capture <prefix> stream <seconds>`:
<prefix>.rgb (both eyes side by side), <prefix>.times and <prefix>.json.

  blip       a cell of an 8x8 grid over the eye that jumps by more than 8 luma levels for one game
             frame and comes straight back: a light or shadow switching on or off for one frame.
             Camera motion moves a cell steadily, so it rarely does this, but fast motion still
             makes more, so counts are binned by image motion (mean absolute luma change).
  one-eye    a blip in one eye with no blip near the same cell and frame in the other (within 1
             frame, 1 row and 2 columns). A real scene event (a spark, a blinking lamp) blips in
             both eyes; a fault in one eye's rendering blips in one.

Repeated captures of the same game frame are dropped first, per grid cell rather than by the whole
image's mean, which would drop a frame where one cell blips while the view is still.

--marks splits the counts by condition: one line per change, `HH:MM:SS[.mmm] label`, on the same
local clock as <prefix>.times (for example grepped from the mod's log). --same-pose reports the
difference between the eyes after the best horizontal shift, for a run where both eyes render the
same pose. --max-one-eye prints a PASS/FAIL line and exits 1 when either eye's one-eye rate (per
100 game frames) is above it. Thresholds are starting defaults.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

GRID = 8
REPEAT = 0.3  # largest cell luma change under which a capture frame repeats the previous game frame
BLIP = 8.0  # luma levels a cell must leave both neighbours by
MOTION_BINS = (0, 2, 4, 6, 9, 13, 1000)
CLOCK = re.compile(r"(\d{1,2}):(\d\d):(\d\d)(?:\.(\d{1,3}))?")


def clock_seconds(text):
    m = CLOCK.search(text)
    if not m:
        raise ValueError(f"no HH:MM:SS clock in {text!r}")
    h, mi, s, ms = m.groups()
    return int(h) * 3600 + int(mi) * 60 + int(s) + int((ms or "0").ljust(3, "0")) / 1000


def clock_text(t):
    t = round(t * 1000)
    return f"{t // 3600000:02d}:{t // 60000 % 60:02d}:{t // 1000 % 60:02d}.{t % 1000:03d}"


def luma(rgb):
    rgb = np.asarray(rgb, np.float32)
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


def cells(gray):
    n, h, w = gray.shape
    return gray[:, : h - h % GRID, : w - w % GRID].reshape(n, GRID, h // GRID, GRID, w // GRID).mean(axis=(2, 4))


def unique_frames(gray):
    """Indices of capture frames that show a new game frame: some grid cell changed."""
    c = cells(gray)
    keep = [0]
    for i in range(1, len(gray)):
        if np.abs(c[i] - c[keep[-1]]).max() > REPEAT:
            keep.append(i)
    return np.array(keep)


def _blip_grid(c):
    a, b, n = c[:-2], c[1:-1], c[2:]
    return (np.abs(b - a) > BLIP) & (np.abs(b - n) > BLIP) & (np.abs(a - n) < BLIP / 3) & (np.sign(b - a) == np.sign(b - n))


def blip_cells(gray):
    """Per frame (aligned with gray[1:-1]): the boolean grid of cells that blip."""
    return _blip_grid(cells(gray))


def blips(gray):
    """Per frame (aligned with gray[1:-1]): cells that blip brighter, cells that blip darker, motion."""
    c = cells(gray)
    hit, a, b = _blip_grid(c), c[:-2], c[1:-1]
    up = (hit & (b > a)).sum(axis=(1, 2))
    down = (hit & (b < a)).sum(axis=(1, 2))
    motion = 0.5 * (np.abs(gray[1:-1] - gray[:-2]).mean(axis=(1, 2)) + np.abs(gray[2:] - gray[1:-1]).mean(axis=(1, 2)))
    return up, down, motion


def _near(hit, reach):
    out = np.zeros_like(hit)
    n, gy, gx = hit.shape
    dt, dy, dx = reach
    for t in range(-dt, dt + 1):
        for y in range(-dy, dy + 1):
            for x in range(-dx, dx + 1):
                out[max(0, t):n + min(0, t), max(0, y):gy + min(0, y), max(0, x):gx + min(0, x)] |= \
                    hit[max(0, -t):n - max(0, t), max(0, -y):gy - max(0, y), max(0, -x):gx - max(0, x)]
    return out


def one_eye_flags(left, right, reach=(1, 1, 2)):
    """Per game frame of a stereo stream: (left-only blip, right-only blip, kept capture indices).
    The flags line up with keep[1:-1]. `reach` is (frames, rows, columns) of the grid."""
    keep = unique_frames(np.concatenate([left, right], axis=2))
    hl, hr = blip_cells(left[keep]), blip_cells(right[keep])
    return (hl & ~_near(hr, reach)).any(axis=(1, 2)), (hr & ~_near(hl, reach)).any(axis=(1, 2)), keep


def one_eye_blips(left, right, reach=(1, 1, 2)):
    """(frames with a left-only blip, frames with a right-only blip, game frames)."""
    only_left, only_right, _ = one_eye_flags(left, right, reach)
    return int(only_left.sum()), int(only_right.sum()), len(only_left)


def aligned_difference(left, right, max_shift=None):
    """For eyes rendering the same pose: (dx, median absolute luma difference) at the horizontal shift
    dx where right[..., x + dx] best matches left[..., x] (least mean difference). The eyes' asymmetric fields of view put
    the same pose at a fixed offset in the two mirror images, so diff only after undoing it."""
    left, right = np.asarray(left, np.float32), np.asarray(right, np.float32)
    w = left.shape[-1]
    max_shift = w // 4 if max_shift is None else max_shift
    best = None
    for dx in range(-max_shift, max_shift + 1):
        a = left[..., max(0, -dx): w - max(0, dx)]
        b = right[..., max(0, dx): w - max(0, -dx)]
        d = float(np.abs(a - b).mean())
        if best is None or d < best[1]:
            best = (dx, d, float(np.median(np.abs(a - b))))
    return best[0], best[2]


def read_marks(lines):
    """[(clock seconds, label)] from `HH:MM:SS[.mmm] label` lines, in time order."""
    marks = []
    for line in lines:
        m = CLOCK.match(line.strip())
        if m:
            marks.append((clock_seconds(m.group(0)), line.strip()[m.end():].strip() or "unlabelled"))
    return sorted(marks)


def labels_at(times, marks):
    labels = np.full(len(times), "before marks", dtype=object)
    for t, label in marks:
        labels[np.asarray(times) >= t] = label
    return labels


def load_stream(prefix):
    """(left frames, right frames, local clock seconds per frame, info) from a mirror stream."""
    prefix = Path(str(prefix).removesuffix(".rgb").removesuffix(".json").removesuffix(".times"))
    info = json.loads(Path(f"{prefix}.json").read_text())
    frames = np.fromfile(f"{prefix}.rgb", np.uint8).reshape(-1, info["height"], info["width"], 3)
    times = np.array([clock_seconds(line.split()[1]) for line in Path(f"{prefix}.times").read_text().splitlines() if line.strip()])
    n = min(len(frames), len(times))
    eye = info["eye_width"]
    return frames[:n, :, :eye], frames[:n, :, eye:], times[:n], info


def per100(count, frames):
    return 100 * count / frames if frames else 0.0


def summarise(left, right, times, marks=(), events=False):
    """Report lines and the worst one-eye rate per 100 game frames."""
    gl, gr = luma(left), luma(right)
    per_eye = {}
    for name, gray in (("left", gl), ("right", gr)):
        keep = unique_frames(gray)
        up, down, motion = blips(gray[keep])
        per_eye[name] = (times[keep[1:-1]], up, down, motion)
    only_left, only_right, keep = one_eye_flags(gl, gr)
    joint_times = times[keep[1:-1]]
    lines, worst = [], 0.0
    for label in dict.fromkeys(labels_at(times, marks)) if marks else [None]:
        if label is not None:
            lines.append(f"== {label}")
        for name, (t, up, down, motion) in per_eye.items():
            sel = labels_at(t, marks) == label if label is not None else np.ones(len(t), bool)
            hit = (up + down)[sel] > 0
            lines.append(f"{name} eye: {sel.sum()} game frames, {hit.sum()} with a blip ({per100(hit.sum(), sel.sum()):.2f} per 100; "
                         f"cells up {up[sel].sum()}, down {down[sel].sum()})")
            for lo, hi in zip(MOTION_BINS[:-1], MOTION_BINS[1:]):
                b = (motion[sel] >= lo) & (motion[sel] < hi)
                if b.any():
                    lines.append(f"  motion {lo:>3}-{hi:<4} frames {b.sum():5d}  blips {hit[b].sum():4d}  per 100 {per100(hit[b].sum(), b.sum()):5.2f}")
        sel = labels_at(joint_times, marks) == label if label is not None else np.ones(len(joint_times), bool)
        nl, nr, n = int(only_left[sel].sum()), int(only_right[sel].sum()), int(sel.sum())
        worst = max(worst, per100(nl, n), per100(nr, n))
        lines.append(f"one eye only: {n} game frames; left-only {nl} ({per100(nl, n):.2f} per 100), right-only {nr} ({per100(nr, n):.2f} per 100)")
        if events:
            for t, l, r in zip(joint_times[sel], only_left[sel], only_right[sel]):
                if l or r:
                    lines.append(f"  {clock_text(t)}  {'left' if l else 'right'}-only")
    return lines, worst


def save_events(frames, left, right, times, folder, limit=20):
    """One PNG per one-eye blip: before, during and after, both eyes side by side. Returns the paths."""
    from PIL import Image  # only this option needs Pillow
    only_left, only_right, keep = one_eye_flags(luma(left), luma(right))
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for j in np.flatnonzero(only_left | only_right)[:limit]:
        strip = np.concatenate([frames[keep[j + k]] for k in range(3)], axis=0)
        path = folder / f"{clock_text(times[keep[j + 1]]).replace(':', '-')}_{'left' if only_left[j] else 'right'}.png"
        Image.fromarray(strip).save(path)
        paths.append(path)
    return paths


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("prefix", help="the stream's prefix (or its .rgb file)")
    p.add_argument("--marks", type=Path, help="condition changes, `HH:MM:SS[.mmm] label` per line")
    p.add_argument("--from", dest="start", help="first local clock time to read, HH:MM:SS[.mmm]")
    p.add_argument("--to", dest="end", help="last local clock time to read")
    p.add_argument("--events", action="store_true", help="list each one-eye blip's clock time")
    p.add_argument("--save-events", type=Path, metavar="DIR", help="save a before/during/after PNG per one-eye blip (first 20)")
    p.add_argument("--same-pose", action="store_true", help="report the eyes' difference after the best horizontal shift")
    p.add_argument("--max-one-eye", type=float, help="FAIL above this many one-eye blips per 100 game frames in either eye")
    a = p.parse_args(argv)
    left, right, times, info = load_stream(a.prefix)
    sel = np.ones(len(times), bool)
    if a.start:
        sel &= times >= clock_seconds(a.start)
    if a.end:
        sel &= times <= clock_seconds(a.end)
    left, right, times = left[sel], right[sel], times[sel]
    if len(times) < 3:
        print("too few frames in the window")
        return 1
    print(f"stream: {len(times)} frames, {times[-1] - times[0]:.1f} s, {info['eye_width']}x{info['height']} per eye "
          f"(downscale {info.get('downscale', '?')}), {clock_text(times[0])}-{clock_text(times[-1])}")
    marks = read_marks(a.marks.read_text(encoding="utf-8", errors="replace").splitlines()) if a.marks else []
    lines, worst = summarise(left, right, times, marks, a.events)
    print("\n".join(lines))
    if a.same_pose:
        dx, diff = aligned_difference(luma(left[::10]), luma(right[::10]))
        print(f"same pose: right image shifted {dx:+d} px, median difference {diff:.2f} luma levels")
    if a.save_events:
        both = np.concatenate([left, right], axis=2)
        for path in save_events(both, left, right, times, a.save_events):
            print(f"  saved {path}")
    if a.max_one_eye is not None:
        ok = worst <= a.max_one_eye
        print(f"{'PASS' if ok else 'FAIL'} one-eye blips: worst eye {worst:.2f} per 100 (max {a.max_one_eye})")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
