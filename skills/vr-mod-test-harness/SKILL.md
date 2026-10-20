---
name: vr-mod-test-harness
description: Build and use the test harness that lets the agent check a VR mod without a human in the headset - seeing the headset image (SteamVR VR View or eye snapshots), driving controllers and poses with a scripted test driver, and measuring with a gameplay trace and benchmark. Use when tempted to ask the human to "put the headset on and check", when an issue can't be reproduced, or when setting up launch/test tooling for a VR mod.
---

# VR mod test harness

The human is the slowest part of the loop. Before asking them to put the headset on, check
whether you can see, play or measure it yourself. Their headset time is for feel and fun.

## See

- **SteamVR's VR View** mirrors the headset to a desktop window. Set it to Both Eyes; a screenshot
  of it is a screenshot of the headset.
- **Look, don't count.** A mod can report thousands of submitted stereo pairs with zero failures
  while the headset shows SteamVR's Waiting screen. Only an image settles it.
- **Focus trap.** Bringing the mirror window to the foreground takes focus from the game, which can
  stop the game's controller input. Make the mod survive focus loss, and prefer having the mod save
  its own per-eye snapshots (an opt-in flag) so tests never touch the mirror.

## Play

A test driver feeds scripted controller actions and poses in at the VR backend boundary, through
the same gesture detectors and pad mapping as real controllers. Contract:
[references/test-driver.md](references/test-driver.md).

Use it to reproduce every reported control issue before fixing it. "Sideways dodges go forward"
becomes a scripted dodge per direction and view heading that measures displacement in the trace;
it fails before the fix, passes after, and stays as a regression (check that removing the fix
fails it).

## Measure and record

- **Trace**: a fixed-rate JSON-lines log of the player, the game's view of the player, and every
  decision the mod made. Fields: [references/trace.md](references/trace.md).
- **Session summary script**: boils a trace down to one page (offset medians, drift per minute
  split at re-anchor points, presses per action, gesture outcomes, warnings). Read it after every
  run instead of asking how it felt.
- **Benchmark**: PresentMon (pinned version) at a fixed checkpoint, with a mode switch that
  isolates costs (tracking only / copy only / full submit). Reject captures taken in menus, pause
  or cutscenes. Per-frame costs hiding in setup code (like re-validating the graphics adapter
  every frame) show up here long before anyone notices them in play.

## Plumbing

- **Launcher**: installs the mod, launches straight into a test scene if the game has a modders'
  autostart or scene argument, waits with a deadline, collects logs, trace and snapshots into a
  per-run folder, and always removes the mod afterwards.
- **Fake eyes**: a synthetic mode with per-frame head poses and per-eye projections so stereo code
  runs with no headset attached.
- **Tests on real code**: real detours, a mock of the game's middleware, and real GPU work where
  you can get it (on D3D12, the WARP software device can copy eye textures and read them back).
- **Headset awake**: an unworn headset stops the runtime rendering. Cover the proximity sensor, or
  turn off SteamVR's "Pause VR when headset is idle".
- **Hot reload** for anything tuned by feel (head height, wrist angle).
- **Driving menus**: computer use can click through menus, but synthetic key taps may not reach the
  game; send mod hotkeys as window messages. Skipping menus with a direct test-scene launch is
  better still.
