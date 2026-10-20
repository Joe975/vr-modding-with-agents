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
  ]
}
```

Keyframes hold until the next one. Name buttons by what they do (`dodge`, `parry`), not by
controller button, so scenarios survive remapping. Add wrist and head poses as keyframes when a
gesture is under test.

## Queueing

A small CLI writes a request into a mailbox folder the running mod polls (every 50 ms or so): `run <scenario.json>`, `status`, `stop`. Each request gets a unique ID, its exact JSON is
saved beside the mailbox so it can be re-queued, and a new launch uses a fresh mailbox so stale
requests never replay. Reject a start while another scenario is active.

## Using it

1. Write a scenario that should show the reported problem.
2. Run it and check the trace: it should fail the way the human described.
3. Fix, re-run, and keep the scenario as a regression. Confirm removing the fix fails it.
