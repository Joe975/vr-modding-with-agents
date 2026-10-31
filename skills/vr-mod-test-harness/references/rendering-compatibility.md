# Rendering compatibility and stereo correctness

Use this when changing AA/upscaling, frame tracking, eye resources, visibility or hardware support.
Keep evidence in the consuming mod's `STATUS.md`, with longer reports linked from there.

## Capabilities are not tested hardware

Define the minimum graphics API/features, texture formats, resource creation/copy/sharing operations,
runtime requirements and memory budget the baseline needs. Check capabilities at startup and name
the failed requirement. Unknown minimums stay unknown until measured; a powerful development GPU
doesn't establish a minimum GPU or VRAM requirement.

Provide a vendor-neutral AA/stereo path. Optional vendor upscalers may improve it, but frame IDs,
pose association, capture, readiness and essential diagnostics must also work without their SDK,
markers or utilities. Prefer graphics API timestamps and runtime/platform counters for telemetry;
vendor tools are optional supplements. Missing telemetry is `null` with a reason, never zero or
evidence that a different component is the bottleneck.

Record GPU model/driver, OS, runtime/headset, game build, mod/package hash, AA, actual input/output
dimensions, route/scene, run IDs and separate image, recovery, performance and human-comfort results.
Use explicit states: tested, experimental, untested or unsupported. Plan these matrix rows:

| Row | Required evidence |
|---|---|
| Vendor-neutral baseline on the development GPU | Both-eye images and the normal player launch |
| Baseline with optional vendor middleware/markers absent | Frame identity, history continuity, stereo delivery and telemetry availability |
| Real NVIDIA, AMD and Intel hardware within the intended scope | Baseline correctness, representative performance and recovery on each tested model/driver |
| Older/non-accelerated cards, if claimed supported | Baseline without the optional upscaler; measured limits |
| Each advertised AA/upscaling mode and camera/runtime mode | Image correctness, effective dimensions, transitions and recovery |
| Unsupported modes or missing capabilities | Named fallback/refusal, no crash, and supported-mode recovery |

Test applicable combinations; mark the others untested or out of scope with a reason. Hiding an SDK
on one GPU proves only that dependency test. It does not simulate another driver's allocations or
formats. Don't claim all GPU brands work from API portability or lack of vendor checks alone.

## A mode is supported only when its output is stereo

For each advertised path, capture both eyes at known poses in still and moving scenes. Reject a
flat panel, Waiting screen, stale image, identical eye copy or wrong scene even if submission
counters rise. Simple image disparity checks are one part of this evidence, not a complete visual
proof. Check UI trails, missing geometry, fine-detail shimmer and moving-object ghosting too.

Exercise a normal launch, AA switches in both directions, render/output-size changes, applicable
dynamic resolution, pool/device rebuilds and mono suspension followed by stereo recovery. Verify
actual effective settings and dimensions, not just the request. An unsupported selection must name
the reason and show a usable fallback or clear refusal. Switching to a supported mode must recover
without restart where the game permits it; document any restart requirement and test that route.
Count flat fallback separately from fresh stereo. Check comfort with a human after automated checks.

## Temporal inputs belong to the eye that rendered them

Inventory AA/upscaler histories, exposure, fog, bloom and other temporal resources. Label each
per-eye or genuinely shared, with its owner and update frequency. For each temporal AA path:

- Trace that each eye reads its own last valid image and writes a distinct destination, including
  ping-pong parity. A pass executing successfully is not proof it used the correct predecessor.
- Check current/unjittered/previous matrices, actual raster jitter and its units/sign against the
  inputs the AA pass receives. Derive the relation from the renderer; don't blindly copy one eye's
  matrices or require equal jitter without establishing the engine's sampling convention.
- Verify matching per-eye depth and motion vectors, coordinate space/scales, resolution and jitter
  convention, including camera motion. Test head motion, moving objects and newly exposed surfaces.
- Reset on discontinuity, mode changes, invalid predecessor and rebuilt resources. Rebind histories
  to the new size and generation; never continue with the other eye's or retired pool's image.
  Bound bootstrap/failure handling, log refusals, and use the named fallback if ownership cannot be
  proved. Test repeated transitions, not only first creation.

Keep genuinely view-independent state on a once-per-frame contract. Skipping a second update does
not repair a shared view-dependent history. Record unknown inputs as open checks rather than
claiming an isolated history fix proves temporal correctness.

## Visibility must preserve either eye's view

Classify frustum/depth/cluster data as per-eye geometry; classify visibility sets, atlas selection,
LOD and caches by their actual coverage and lifetime. A shared culling decision must conservatively
keep an object needed by either eye. A left-eye-only occlusion result is not sufficient around an
occluder's edge. Do not widen the raster camera to fix a separate selection/culling error.

Check near occluders, peripheral and asymmetric frusta, fast head turns, disocclusion, differing eye
order and every supported world scale/camera mode. A small physical IPD can become a large world
baseline in an external/tabletop camera. Compare both eyes against a temporary no-culling reference
at the same pose; any missing visible object fails correctness, even if the candidate is faster.

Share shadow maps/atlas selections only when their fit and stable selection cover both eyes. Keep
screen-space masks and depth-dependent work per-eye. Copying the first eye's list or taking a capped
union can omit entries the other eye needs; preserve per-eye lists where necessary. Validate shadows,
lights, particles and LOD transitions, not only solid meshes.

Disabling culling, refitting shadows every eye or forcing visibility is a diagnostic/possible
workaround, not a completed optimisation. Register and cost it using [performance.md](performance.md).
Use [eye-flicker.md](eye-flicker.md) to isolate render-pass faults and measure remaining one-eye excess.
