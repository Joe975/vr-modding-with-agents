# Gameplay trace

A fixed-rate JSON-lines file the mod writes during a run (30 Hz is a starting point; opt-in). It
lets the agent check "the parry didn't fire", "the lever didn't move" or "steering stuck" against data.
Build it before the first playtest that's about feel.

## Header

- Wall-clock start time (with timezone), so it lines up with voice notes.
- Mod version/commit, settings in force, sample rate.
- Supported input/output routes and telemetry groups, including coordinate frames and units.
  State which observations are available; don't infer successful gameplay from requested input.

## Every sample

- **Common envelope:** `t` in seconds from run start and `type` (`header`, `sample`, `event`).
- **Context:** gameplay mode, focus/tracking validity and camera mode, as available.
- **Input and intent:** controller states/poses used by the mod and the named actions recognized,
  including digital edges, analog values, targets and rejection reasons.
- **Integration output:** what the mod emitted, with route and context (key/mouse, pad, engine
  action, target or pose update). A pad state is only required for a pad integration.
- **Observed result:** what the game actually read or did, where measurable. Keep this separate
  from intent: attack accepted, selected object, puzzle state, vehicle response, or another outcome.

## Optional telemetry groups

Add only groups used by the chosen interactions and checks:

- Tracking/camera: raw head/hands in metres, rig anchor and per-eye poses.
- Embodied character: animated bones, IK targets/results and offsets in declared character axes.
- Combat: aim ray, weapon transforms, attack acceptance and hit outcomes if observable.
- Objects/UI: selected target, interaction state, tool state, puzzle value or command result.
- Vehicles: steering/throttle received by the game, vehicle transform/speed and cockpit anchor.

These are example groups, not required field names. Keep advertised fields stable; use `null`
for a missing observation rather than zero. Omit inapplicable groups and declare that in the
header. Games without skeletal hooks don't need fake bones, IK or weapon metrics.
JSON lines repeat every key on every row, so a trace grows to megabytes a minute. That's fine on
disk; never read it raw. Agents query it with `scripts/trace_query.py`.

## Events

- Action edges and analog changes, named by context and intent ("combat.parry down",
  "puzzle.interact up", "vehicle.steer 0.5"), with the physical binding recorded separately.
- Every gesture decision, near misses included ("guard rejected, controller pointed forward",
  "grenade put back, release at 0.4 m/s").
- Context entry/exit, cutscenes, pause, focus/tracking loss and return, recentres, controlled
  subject changes, cancellations and re-arming.
- Animation takeovers if a body is tracked (knockback, grabs). Prefer the game's animation state;
  if unavailable, label any inference as such. For example, flag a possible takeover when the
  animated head bone moves 25 cm from its usual spot for 200 ms, then calibrate for this game.
  Leave those spans out of drift numbers.

## Session summary

A script that turns a trace into one page: actions requested versus observed, rejected/conflicting
interactions, context changes and warnings. Add relevant metrics: skeletal offsets/drift only
for an embodied character, puzzle progress for object interactions, steering response for a
vehicle. Split drift at legitimate re-anchors (recentre, cutscene, subject change). Report
unavailable evidence rather than treating it as success. Read the summary after every run; use
`trace_query.py --around <event>` only for what the summary flags.
