# Performance and development workarounds

Use this when rendering costs change, a broad workaround is added, a new scene type is reached or
a player release is prepared. Keep decisions in `STATUS.md`; keep raw logs in the consuming mod's
run folders. Performance success also requires [correct stereo](rendering-compatibility.md).

## Register shortcuts when adding them

Record disabled occlusion/frustum/distance culling, forced cache/shadow refresh, duplicated passes,
extra waits, global feature suppression, widened bounds and larger buffers. One entry contains:

- ID, introducing commit, failing correctness reproduction and evidence it fixes the fault.
- Exact scope, effective default, activation/refusal log and A/B switch in an otherwise normal run.
- Costs and correctness by representative scene, including unknown costs and missing telemetry.
- A narrower replacement/removal criterion and next experiment. Revisit on a new scene type,
  changed graphics defaults or game build, and before release; don't bury it in an old handoff.

Prefer fixing the incorrect eye/view ownership or duplicate work over a permanent global bypass.
A correctness workaround may remain, but only with a recorded cost, limitation and release decision.
Missing results keep the gate open. Never remove a necessary correctness fix just to improve FPS.

## Compare matched real gameplay

Choose applicable fixed checkpoints/routes: a small controlled scene, dense interior with occluders,
open terrain with shadows/foliage, and the busiest representative gameplay (combat, puzzle effects,
traffic or another actual workload). Record why a category is inapplicable. Exercise loads/settings
and long-session resource growth separately from steady-state throughput.

1. Record game/mod/package hashes, hardware/driver/runtime, camera/scale, actual AA and input/output
   sizes, quality settings, active workarounds and profiler configuration. Save the effective state.
2. Warm up shader compilation, streaming and stereo. Use equal measurement windows and the same
   view/route. Compare unmodded mono where practical, modded mono, previous accepted stereo and
   candidate stereo. A scoped mono/stereo switch helps separate simulation, rendering and bridge cost.
3. Isolate one change; alternate repeated A/B runs (at least A/B/A/B as a starting plan). Report
   per-run results and spread. Repeat or mark inconclusive when scene variation exceeds the effect.
   Compare a regression at the same AA/quality; compare different AA paths separately as trade-offs.
4. Exclude menus, pause, cutscenes and loading from gameplay throughput. Report their stalls and
   recovery separately rather than discarding them. A run that never reaches the intended scene or
   produces only flat fallback is invalid as a stereo benchmark.

Don't infer a mission bottleneck from a test room or assume lower input resolution helps. Vary one
cost and inspect CPU/GPU timing and waits. Render-thread wall time may be a wait, not CPU execution.
Record instrumentation overhead with a lighter capture; full-resolution readback and verbose logging
can change the result being measured.

## Report what reaches the player

For each scene/window, report these observations with source, units and availability:

| Observation | What to distinguish |
|---|---|
| CPU and GPU frame/phase time, p50/p95/p99 in ms | Active CPU work, scheduling/waits, GPU work and runtime/bridge cost |
| Fresh stereo pairs delivered per second | Rendered pairs, submitted pairs, flat panels and repeated/reprojected frames |
| Delivery gaps and dropped/replaced pairs | Counts and longest gap; a high average can hide stalls |
| Pose age at submission, p50/p95/max in ms | Throughput gain versus stale tracking; identify which clock/pose was measured |
| Resource usage over time | VRAM/owned pools/queues where observable; settings changes must not grow them without bound |
| Both-eye correctness | Missing geometry, shadows, flicker, ghosting and recovery at the measured settings |

Use graphics API timestamps and platform/runtime measurements where available; vendor tools are
optional additions. Mark absent values `null` with reasons and retain the limitation. Missing GPU
measurements cannot establish a CPU bottleneck. If a metric required by the project's gate is absent,
that gate is incomplete; either obtain it or record a reviewed limitation, never substitute zero.

## Decide before release

Set project-specific frame-time, delivery-gap, pose-age and resource budgets before comparing the
candidate. Define configurable regression review triggers; for example, a repeatable increase over
5% in median frame time or 10% in p95 may trigger review. These are starting triggers, not universal
playability guarantees. Also review a material loss of delivered stereo, worse tails/pose age, any
correctness failure or cost that moves to another scene. A faster median alone cannot pass.

Resolve each trigger or record the measured trade-off, reason and explicit release decision. Narrow
claims for untested hardware/scenes. At release audit the hashed player package's effective profile
(hooks, workarounds, AA/resolution, buffers, overlays and trace); repeat the representative checks
with shipped defaults, normal launch and diagnostics off. Verify settings/load recovery. Carry the
remaining hardware, visual/comfort and measurement gaps into the release notes.

For machine-readable review use the existing `scripts/check_expect.py` with
[rendering-review.json](rendering-review.json). It is an example acceptance contract for a consuming
mod's measured summary, not a driver or a universal profiler. Its fractional regression limits are
configurable examples: change them for the project before use. The consuming mod must compute the
metrics and attach run/image evidence; these fixture values are not live validation. A failed numeric
trigger means review is required, not automatic rejection of a justified correctness change.
