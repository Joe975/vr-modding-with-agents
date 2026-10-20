# [Game] VR mod

Adds VR to [game] ([engine], [graphics API]) for [headset]. [If the game has anti-cheat or online
play: offline/single-player only.]

## Before you change anything

- Read `STATUS.md` (the shared scratch pad; add a dated entry before you stop) and `RESEARCH.md`
  if it exists. Build on what's there; don't redo or undo another agent's work. Old handoff notes
  are historical: check the latest status before acting on them.
- Decisions, measurements and open issues go in versioned files with dates and run or commit IDs.
  Nothing should depend on chat history or private memory.

## Rules

- **Don't ask the human to check what you can check.** You can see the headset through SteamVR's
  VR View (or the mod's own eye snapshots), drive the controllers with the test driver, and read
  the trace and logs. Ask for the headset only for feel and comfort.
- **Look, don't count.** A submission counter going up isn't proof an image reached the headset.
  Confirm with an image.
- **Reproduce before you fix.** Every reported issue gets a failing reproduction (test driver
  script, eye snapshot comparison, trace check or unit test) before the fix, and the same check
  passing after. If you can't reproduce it, say what you'd need.
- **One run owns the game install.** Whoever has the game running owns its files and the headset;
  other sessions don't launch the game or install or replace the mod's files until that run ends.
- **Always clean up.** The launcher removes the mod after every run, even on failure.
- **Never** touch anti-cheat, online play or anything that would help bypass them.
- Every tunable value (thresholds, offsets, angles) is a live setting, not a constant.

## Commands

Fill these in as the tooling gets built.

- Build: [command]
- Tests: [command]
- Launch a test run: [command, e.g. scripts/run.ps1 -DirectLaunch -Trace -Seconds 1200]
- Test driver: [command]
- Voice playtest: see the vr-playtest-loop skill

## Skills

- `vr-mod-research`: the research pass. Run it before writing mod code.
- `vr-mod-test-harness`: see, play and measure without the human.
- `vr-playtest-loop`: voice-recorded playtests and the reproduce-before-fix loop.
- `vr-controls-design`: control archetypes, body zones and default controls.
