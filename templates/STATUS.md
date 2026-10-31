# Status

The agents' scratch pad for this mod. Every session reads this first and adds a dated entry to the
Log (newest first) before it stops: what changed, the evidence (commit, run folder, test result),
and what's next. Keep the sections above the Log current. Keep it factual; it's how the next
session (or the other agent) picks up the work.

## Current state

- Runtime: [OpenXR (default) / OpenVR, and why]
- Stereo: [alternate-eye / same-frame]
- Camera mode(s): [embodied / cockpit / external / tabletop / other, per context]
- Input mode(s): [existing controls / tracked pointing / tracked interaction / mixed, per context]
- Capabilities and action mappings: [RESEARCH.md / CONTROLS.md; confirmed hooks and unknowns]
- Publisher guidance and chosen scope: [dated sources in RESEARCH.md; user decision and unknowns]
- Launch for testing: [command]
- Who owns the game install right now: [nobody / session, run folder, deadline]

## Rendering compatibility

- Minimum capabilities: [graphics API/features, formats/resource operations, runtime and memory
  requirements; confirmed versus unknown; vendor-neutral AA/stereo baseline]
- Evidence matrix: [GPU model/driver, OS/runtime/headset, game/mod build, AA, actual input/output
  size, scenes, run IDs, image checks, recovery, performance and human comfort verdict]
- Claims: [tested / experimental / untested / unsupported per combination; missing vendor
  middleware test is separate from real hardware validation]
- Unsupported settings: [visible fallback/reason and how supported stereo resumes]

## Rendering workarounds

One entry per broad workaround; link longer evidence rather than copying logs here.

- [ ] [ID / introduced commit: optimisation disabled or work forced; correctness reproduction;
  exact scope and activation log; A/B switch; costs by representative scene (unknown stays
  unknown); narrower replacement or removal criterion; revisit on new scene types and release]

## Performance and release evidence

- Baselines and budgets: [fixed checkpoints/routes, matched settings and builds, repeated A/B
  runs, timing/throughput/tail/pose-age budgets and configurable regression review triggers]
- Results: [small scene plus applicable dense interior, terrain and busiest gameplay; CPU/GPU
  times, fresh delivered stereo, gaps/drops and pose age; missing metrics and profiler overhead]
- Package audit: [package hash, effective defaults/settings, active workaround IDs, diagnostics
  off, normal-launch and settings/load recovery checks; evidence and untested gaps]

## Waiting on the human

- [ ] [Headset checks that need a person: what to launch, what to do, what to look for]

## Open issues

- [ ] [Issue: how to reproduce it, current evidence]

## Log

### [YYYY-MM-DD] [agent]: [what this session did]

[What changed, with commit and run IDs. Tests run and results. Anything left half done.]
