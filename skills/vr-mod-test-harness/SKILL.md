---
name: vr-mod-test-harness
description: Build and use the test harness that lets the agent check a VR mod without a human in the headset - seeing the headset image (SteamVR VR View or eye snapshots), driving controllers and poses with a scripted test driver, and measuring with a gameplay trace and benchmark, all returning short verdicts instead of images and raw logs. Use when tempted to ask the human to "put the headset on and check", when an issue can't be reproduced, when setting up launch/test tooling for a VR mod, or when screenshots and trace reading are eating the context.
---

# VR mod test harness

The human is the slowest part of the loop. Before asking them to put the headset on, check
whether you can see, play or measure it yourself. Their headset time is for feel and fun.

## Verdicts, not pixels

Every image or log you read stays in your context and is paid for again on every later request.
A screenshot or a raw trace is the most expensive way to learn "it worked". So every check
should print a verdict first, and you only open the evidence when the verdict is FAIL:

- Images: `scripts/frame_check.py` (below). Look at the preview it writes on failure, not the
  full-size capture: a 720 px preview costs roughly a quarter of a full eye, a crop less still.
- Runs: an `expect` list in each scenario, judged by `scripts/check_expect.py`.
- Traces: `scripts/trace_query.py` for a few columns around an event, never the whole file.
- When an orchestrating agent hands a check to a worker or sub-agent, ask for the verdict lines
  and file paths back, not the evidence.

Scripts need `pip install -r scripts/requirements.txt` (numpy, Pillow) in the repo's venv.

## See

- **SteamVR's VR View** mirrors the headset to a desktop window. Set it to Both Eyes; a screenshot
  of it is a screenshot of the headset.
- **Look, don't count.** A mod can report thousands of submitted stereo pairs with zero failures
  while the headset shows SteamVR's Waiting screen. Only an image settles it, but a script can
  do the looking:

  ```
  python scripts/frame_check.py left.png right.png --reject waiting.png --ref golden_left.png
  ```

  It checks each eye isn't blank, doesn't match a known-bad screen (save one capture of the
  runtime's Waiting or loading screen as `--reject`), matches a golden capture taken at the same
  scripted pose (`--ref`), and that the eyes are a real stereo pair: not identical copies (mono),
  the same scene once the left/right offset is undone, and no vertical offset between them. One
  PASS/FAIL line per check, exit code 1 on failure, previews only on failure. Thresholds are
  starting defaults; calibrate them on a few known-good and known-bad captures of your own.
  Golden images only work for captures at a fixed scripted pose in a fixed scene.
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
fails it). Write the pass condition into the scenario as an `expect` list and judge each run
with `scripts/check_expect.py scenario.json run.metrics.json`, so a run reads as a few PASS/FAIL
lines and the trace is only opened when something fails.

## Measure and record

- **Trace**: a fixed-rate JSON-lines log of the player, the game's view of the player, and every
  decision the mod made. Fields: [references/trace.md](references/trace.md).
- **Session summary script**: boils a trace down to one page (offset medians, drift per minute
  split at re-anchor points, presses per action, gesture outcomes, warnings). Read it after every
  run instead of asking how it felt.
- **Query, don't read.** A trace runs to megabytes per minute. Use
  `scripts/trace_query.py trace.jsonl --count` for what's in it, then `--around <event> --window 1
  --fields t,<path>,... --every 3` for the few seconds that matter. Output is tab-separated and
  capped at 50 rows.
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
  game; send mod hotkeys as window messages. Every computer-use step returns a screenshot, so
  clicking through menus and watching loading screens is the most image-hungry thing an agent
  does. Skip menus with a direct test-scene launch, and have the mod log a `scene_ready` event
  (or similar) that the launcher waits on instead of watching the screen.
