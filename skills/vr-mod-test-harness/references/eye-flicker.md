# Per-eye flicker: record both eyes, find the eye, find the cause

Use this when a playtester reports flicker, lights popping or shading that "looks bad" in the
headset, and the flat game doesn't do it. The usual cause in a stereo mod is the second eye
reusing something the first eye computed.

## Record both eyes

- **OBS's OpenVR capture records one eye.** Its source has a right-eye checkbox. A playtest clip
  can show the worse eye without anyone knowing. Don't measure per-eye problems from it.
- **Record the SteamVR mirror instead**, both eyes, with
  [`scripts/mirror_capture/openvr_mirror_capture.cpp`](../scripts/mirror_capture/openvr_mirror_capture.cpp):

  ```
  cmake -S .agents/skills/vr-mod-test-harness/scripts/mirror_capture -B build/mirror_capture -DOPENVR_SDK_DIR=<openvr sdk>
  cmake --build build/mirror_capture --config Release
  openvr_mirror_capture C:/runs/r1/eyes stream 36 16
  ```

  It is a background OpenVR client: it needs SteamVR running, never takes focus and never touches
  the game. It works for OpenXR games too. Each eye's mirror is shrunk on the GPU (a mip chain)
  and only the small level is read back. Reading full eyes back is several GB/s and drops frames;
  a downscale of 16 gave about 37 new frames a second at roughly 190x210 per eye. It writes only
  frames that changed, with a local clock time per frame. Create `<prefix>.stop` to end early.
  `snap` mode writes one PPM per eye for `frame_check.py`.
- Drive the view with the test driver (scripted head and actions), not by hand, so runs repeat.

## Measure

```
python .agents/skills/vr-mod-test-harness/scripts/eye_flicker.py C:/runs/r1/eyes --events --max-one-eye 1.0
```

- **Blip**: a cell of an 8x8 grid that jumps more than 8 luma levels for one game frame and comes
  straight back. That is a light or shadow switching for one frame. Camera motion moves cells
  steadily, so it rarely does this.
- **Bin by image motion.** Fast motion makes more blips, so compare conditions at the same motion.
  A still view should have none; if it does, look for per-frame noise (film grain, dithering).
- **Dedupe per cell, not by image mean.** The compositor repeats game frames. A whole-image mean
  drops the frame where one cell blips on a still view.
- **One-eye blips are the measure that works.** Count a blip only when the other eye has no blip
  within 1 frame, 1 grid row and 2 columns. Real scene events (sparks, a blinking lamp) blip in
  both eyes; a fault in one eye's rendering blips in one. Plain per-eye counts are too noisy at
  around ten events a run.
- **Alternate A/B runs** (A, B, A, B, same route) rather than one run each. Use `--marks` to split
  one recording by condition when the mod logs its mode changes with clock times.
- `--save-events DIR` writes before/during/after strips of both eyes for each one-eye blip. Look
  at a few; don't open the recording.
- **Capture timing is not rendering.** The two mirror textures can update a frame apart. A change
  that appears equally and oppositely in both eyes, one frame apart, is the capture.

## Does it follow the render pass or the eye?

With same-frame stereo (two render passes per game frame), let the mod choose which eye's pose
and projection each pass renders, from a test-only switch:

- `native`: pass 0 renders the left eye, pass 1 the right.
- `swap`: pass 0 renders the right eye's pose, pass 1 the left's.
- `same`: both passes render one eye's pose, a fraction of a millimetre apart so any
  "are the eyes separate" checks still pass.

If one-eye blips stay with pass 1 under `swap`, the fault follows the render pass, not the eye.
If pass 1 matches pass 0 under `same`, the second pass is reusing view-dependent state from the
first pass or from shared storage: harmless when the views match, visible when they differ. Views
that differ more (fast sideways motion, a large world-scale baseline) flicker more.

In `same` mode the two mirror images still differ by a fixed horizontal shift, from the eyes'
asymmetric fields of view. Align before diffing: `eye_flicker.py --same-pose` finds the shift and
reports the median difference after it (under one luma level means the passes match).

## Likely causes

Things an engine may compute per view but store or index in a way the second view shares:

- **Per-view selection into a shared atlas.** Each view picks its own shadowed lights (by
  frustum, distance, occlusion), but all views render into one shadow atlas indexed by list
  position. When the lists disagree, a tile holds one light for one view and another for the
  other, so lights and shadows flip for a frame. Share a stable atlas selection only if it covers
  both eyes. Copying the first view's selection is a diagnostic or a qualified fix, not a general
  rule: it can omit lights or objects only the other eye needs. A capped union can also drop needed
  entries. Keep per-eye lists where required and use a stable selection rule.
- **Shared temporal history.** A history that should advance once per frame (volumetric fog,
  TAA-style accumulation, exposure) advances once per view, so each eye reprojects the other
  eye's history. Give view-dependent accumulation its own history per eye. Share genuinely
  view-independent state only with an explicit once-per-frame update contract; skipping one update
  is not a substitute for private TAA history.
- Selection that waits on an earlier frame's occlusion query can also lag under fast motion, but
  test it: forcing everything visible is a quick A/B. Register the bypass and measure its real-scene
  cost before keeping it. The full ownership and either-eye visibility checks are in
  [rendering-compatibility.md](rendering-compatibility.md).

## Test a hypothesis without a rebuild

If the game has no anti-cheat and you're allowed to mod it, a small tool can read the renderer's
live per-view state from another process (`ReadProcessMemory`) at a few hundred Hz and log the
times when the two views disagree (for example, different shadowed-light lists). Correlate those
times with the one-eye blip times from `eye_flicker.py --events`. Blips within a frame or two of a
disagreement support the hypothesis; blips far from any disagreement mean something else also
contributes. This takes minutes, where a speculative fix and a headset run take an hour.

After a fix, measure how much of the second pass's excess it removed (one-eye rate in pass 1
minus pass 0, before and after). A real cause can still be only part of the excess.
