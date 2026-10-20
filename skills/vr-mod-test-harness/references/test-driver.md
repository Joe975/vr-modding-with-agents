# Test driver contract

A scripted stand-in for the human's controllers, for any mod that reads controllers through its
own VR backend.

## Where it plugs in

Scripted actions and poses replace the controller samples at the mod's VR backend boundary. The
rest of the mod runs unchanged: one tracking/action sample per frame, relevant recognizers and
the chosen game integration. Arm IK, weapon aim and virtual pads are optional. The driver never
teleports the controlled subject or directly sets the desired puzzle/vehicle/combat outcome, and
never reports a requested action as a successful game action: check the trace for what actually
happened.

- Opt-in at launch (e.g. `-TestDriver`); normal launches are unchanged.
- While enabled it owns the declared controller inputs, including when idle. Real HMD tracking
  stays live unless a scripted-head option is also set.
- Completion, a STOP request, focus loss or tracking loss releases every emitted control.

## Scenario files

JSON, one per scenario, versioned in the mod repo:

```json
{
  "description": "In a fixed puzzle scene, target the lever, interact, then release. Observe the lever and door.",
  "duration_ms": 1500,
  "frames": [
    {"ms": 0},
    {"ms": 500, "buttons": ["interact"]},
    {"ms": 650},
    {"ms": 1500}
  ],
  "expect": [
    {"metric": "puzzle.lever_fraction", "min": 0.95, "max": 1.0},
    {"metric": "puzzle.door_open", "equals": true},
    {"metric": "unintended_actions.#", "equals": 0},
    {"metric": "terminal", "equals": "completed"}
  ]
}
```

`expect` is the pass condition, written against the metrics file the run writes (next section);
`scripts/check_expect.py` turns it into PASS/FAIL lines. Each keyframe defines a complete input
state held until the next one; omitted controls are neutral. The final keyframe is neutral.
`buttons` names digital input actions (`interact`, `attack`, `parry`), not physical buttons, so
scenarios survive remapping. `move`, if used, is a two-component locomotion input; `axes` maps
named analog inputs to values with ranges declared by the mod's driver. Neutralise all axes on
stop as well as releasing digital actions.

For a gesture test, add raw wrist/head pose keyframes and run through the real recognizer;
requesting its output action directly only tests downstream mapping. For physical steering or a
lever, replay poses through the real interaction code, rather than setting the game object's
transform from the driver. Context changes must follow the game's real entry/exit path.

These are contracts to implement in the mod, not a driver supplied by this kit. Reject unknown
actions, axes or unsupported pose fields instead of silently ignoring them. Extend the schema
only for inputs the mod actually needs.

## Examples across game types

- [Melee action](scenarios/melee.json): a button attack accepted by the game against a fixed target.
  This tests action mapping, not swing recognition or physical blade collision.
- [Puzzle interaction](scenarios/puzzle.json): the lever and door actually change state.
- [Vehicle input](scenarios/vehicle.json): analog steering/throttle produce movement and turning.

Each assumes a prepared deterministic scene and initial target/context. Adapt timing and bounds
to that scene; the numbers aren't genre-wide defaults. Record the setup with the scenario.
Add negative runs (no action, wrong context, interruption) and pose-based scenarios for chosen
gestures. These examples and the kit's tests exercise expectation checking; they don't prove a
live game or driver works.

## Queueing

A small CLI writes a request into a mailbox folder the running mod polls (every 50 ms or so):
`run <scenario.json>`, `status`, `stop`. Each request gets a unique ID, its exact JSON is saved
beside the mailbox so it can be re-queued, and a new launch uses a fresh mailbox so stale
requests never replay. Reject a start while another scenario is active.

## Run output

Each run writes a small metrics JSON beside its trace slice: the request ID, how it ended
(`completed`, `stopped`, `focus_lost`), and the numbers the scenario is about, already worked
out (for example, interaction completion, vehicle response, displacement, camera offset or
gesture outcomes). Choose metrics for this game's capabilities; skeletal/weapon data isn't required.
Write it compact (no indentation) and list each event once. The agent reads the verdict and this
file; the trace is for when they disagree or something fails.

## Using it

1. Write a scenario that should show the reported problem, with an `expect` list for the fixed
   behaviour.
2. Run it: `check_expect.py` should fail the way the human described.
3. Fix, re-run until it passes, and keep the scenario as a regression. Confirm removing the fix
   fails it.
