---
name: vr-mod-test-harness
description: Build and use a VR mod test harness with eye-image checks, scripted inputs/poses, capability-specific gameplay observations and short verdicts. Use when setting up launch/test tooling, reproducing control or rendering issues, or checking what can be verified without a human in the headset.
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
- **A fallback can pass a frame check.** If the mod falls back to a flat panel or mono view when
  stereo stops, "frames submitted" keeps climbing. Run checkers should require the primary path
  (real stereo pairs from the stereo producer) and fail on any stop or fallback line. Prove each
  checker on a known-bad run before trusting its PASS.
- **A crop passes a size check.** An eye image of the right size with no letterbox can still be
  the left half of a wider frame at twice the magnification. Compare aspect at every stage (swap
  chain, eye copies, colour targets, upscaler input) and compare a capture against a known whole
  eye at the same pose: a crop differs far more than a resize does.
- **Focus trap.** Bringing the mirror window to the foreground takes focus from the game, which can
  stop the game's controller input. Make the mod survive focus loss, and prefer having the mod save
  its own per-eye snapshots (an opt-in flag) so tests never touch the mirror.

## Play

A test driver feeds scripted controller actions and poses in at the VR backend boundary, through
the same applicable recognizers and integration routes as real controllers. Contract and
melee, puzzle and vehicle examples:
[references/test-driver.md](references/test-driver.md).

Use it to reproduce every reported control issue before fixing it. "Sideways dodges go forward"
becomes a direction/view-heading test measuring displacement; "the lever doesn't operate"
becomes a selected-target interaction test measuring puzzle state. Use poses to test recognizers,
action inputs to test mapping, and game observations to test outcomes. A requested input is
never proof the game performed it. Keep the failing scenario as a regression after fixing it
(check that removing the fix fails it). Write the pass condition as an `expect` list and judge each run
with `scripts/check_expect.py scenario.json run.metrics.json`, so a run reads as a few PASS/FAIL
lines and the trace is only opened when something fails.

**Replay recorded traces through the production rules.** When a playtest says a gesture "stopped
working", feed the human's recorded traces through the same recognizer code the mod runs,
offline, and count outcomes per motion: which were rejected, and by which gate. Retune, then
replay every recorded session before a live run, with a flag to switch each change off, so a fix
for one complaint is shown not to break earlier ones (intentional swings counted rise, incidental
motions counted stay at zero). It needs the recognizer built as a library the replay tool can
link, and traces carrying every input the recognizer reads.

## Measure and record

- **Trace**: a fixed-rate JSON-lines log of the player, the game's view of the player, and every
  decision the mod made. Fields: [references/trace.md](references/trace.md).
- **Session summary script**: boils a trace down to one page (requested versus observed actions,
  context changes, gesture outcomes, warnings and relevant capability metrics). Offset/drift
  measurements apply only where tracked body/camera alignment is meaningful. Read it after
  every run; human feedback still decides feel and comfort.
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
- **Transient failures:** one refused capture, one stale poll or one late frame is normal. Don't
  switch a feature off for the run on the first; require a run of consecutive failures with no
  success between (30 is a starting point), log the first with its cause, and carry the count in
  the periodic status line.
- **Driving menus**: computer use can click through menus, but synthetic key taps may not reach the
  game; send mod hotkeys as window messages. Every computer-use step returns a screenshot, so
  clicking through menus and watching loading screens is the most image-hungry thing an agent
  does. Skip menus with a direct test-scene launch, and have the mod log a `scene_ready` event
  (or similar) that the launcher waits on instead of watching the screen.
