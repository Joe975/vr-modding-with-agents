# Test driver contract

A scripted stand-in for the human's controllers, for any mod that reads controllers through its
own VR backend.

## Where it plugs in

Scripted actions and poses replace the controller samples at the mod's VR backend boundary. The
rest of the mod runs unchanged: one tracking/action sample per frame, gesture detection, arm IK,
weapon aim, and the virtual gamepad the game reads. The driver never teleports the character and
never reports a requested action as a successful game action: check the trace for what actually
happened.

- Opt-in at launch (e.g. `-TestDriver`); normal launches are unchanged.
- While enabled it owns both controllers, including when idle. Real HMD tracking stays live unless
  a scripted-head option is also set.
- Completion, a STOP request, focus loss or tracking loss releases every emitted control.

## Scenario files

JSON, one per scenario, versioned in the mod repo:

```json
{
  "description": "Hold left, request dodge, then release. Measure root displacement in the trace.",
  "duration_ms": 4500,
  "frames": [
    {"ms": 0},
    {"ms": 500, "move": [-1, 0]},
    {"ms": 800, "move": [-1, 0], "buttons": ["dodge"]},
    {"ms": 1000, "move": [-1, 0]},
    {"ms": 1400},
    {"ms": 4500}
  ],
  "expect": [
    {"metric": "root_displacement_view_axes.right_metres", "max": -0.5, "why": "moved left"},
    {"metric": "root_displacement_view_axes.forward_metres", "min": -0.08, "max": 0.08},
    {"metric": "terminal", "equals": "completed"}
  ]
}
```

`expect` is the pass condition, written against the metrics file the run writes (next section);
`scripts/check_expect.py` turns it into PASS/FAIL lines. Keyframes hold until the next one. Name buttons by what they do (`dodge`, `parry`), not by
controller button, so scenarios survive remapping. Add wrist and head poses as keyframes when a
gesture is under test.

## Queueing

A small CLI writes a request into a mailbox folder the running mod polls (every 50 ms or so):
`run <scenario.json>`, `status`, `stop`. Each request gets a unique ID, its exact JSON is saved
beside the mailbox so it can be re-queued, and a new launch uses a fresh mailbox so stale
requests never replay. Reject a start while another scenario is active.

## Run output

Each run writes a small metrics JSON beside its trace slice: the request ID, how it ended
(`completed`, `stopped`, `focus_lost`), and the numbers the scenario is about, already worked
out (root displacement in body and view axes, camera offset before and after, gesture outcomes).
Write it compact (no indentation) and list each event once. The agent reads the verdict and this
file; the trace is for when they disagree or something fails.

## Using it

1. Write a scenario that should show the reported problem, with an `expect` list for the fixed
   behaviour.
2. Run it: `check_expect.py` should fail the way the human described.
3. Fix, re-run until it passes, and keep the scenario as a regression. Confirm removing the fix
   fails it.
