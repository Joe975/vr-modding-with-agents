---
name: vr-mod-test-harness
description: Build and use a VR mod test harness with eye-image checks, both-eye headset recording, per-eye flicker measurement, scripted inputs/poses, capability-specific gameplay observations and short verdicts. Use when setting up launch/test tooling, reproducing control or rendering issues (including flicker or lighting that differs between the eyes), or checking what can be verified without a human in the headset.
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
- Flicker: `scripts/eye_flicker.py` on a both-eye recording, never the video itself.
- When an orchestrating agent hands a check to a worker or sub-agent, ask for the verdict lines
  and file paths back, not the evidence.

Scripts need `pip install -r scripts/requirements.txt` (numpy, Pillow) in the repo's venv.

## See

- **SteamVR's VR View** mirrors the headset to a desktop window. Set it to Both Eyes; a screenshot
  of it is a screenshot of the headset.
- **Record both eyes, not OBS.** OBS's OpenVR capture records one eye (a right-eye checkbox), so a
  clip can show the worse eye without anyone knowing. `scripts/mirror_capture/` builds a
  background OpenVR client that records both eyes' mirror textures, downscaled on the GPU, with a
  clock time per frame and no window focus change. Method:
  [references/eye-flicker.md](references/eye-flicker.md).
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

The same works for any rule that decides from recorded inputs: camera holds, held-item state,
pause timing. Prove the replay first: with the new rule off, it should reproduce what the run
logged. Then count the rule over every recorded run, and cut the frames around the complaint into
a small fixture for a regression test.

**The test scene is not the real game.** A direct test launch can use a different character, level
or asset set from a normal launch, so a check can pass there while the feature does nothing for
players. Have each feature log what it changed (parts written, not just "ran"), make every refusal
name the field that failed, and have the run report flag a feature that ran with zero effect on a
normal launch. Two mechanisms for one job hide this: while one half works, nobody notices the
other never applied.

**Check the outcome, not the label.** A check that reads a state ("held in the right hand") passes
while the result is wrong (the weapon tens of degrees off). Assert what the player would see. When
a fault turns up, reread the numbers in the last passing checks: it's often already there, in a
column nobody asserted.

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
- **Run report against known states**: a script that reads any run's mod log (the agent's or a
  playtest's) and lists the game states, refusal and error codes, fallbacks, stops, recoveries and
  hangs it saw, marking anything missing from a versioned known-states table as `NEW`. A strict
  mode exits non-zero on a `NEW` item or a verdict (stereo stopped for good, a hang); a learn mode
  adds a run's states once a human has looked. Seed it from every old log: that alone tends to turn
  up faults nobody reported.
- **Hang watchdog**: when no frame is presented for ~10 s, the mod writes one thread-stack dump.
  It is one per process, so a stall at startup can use it up; the launcher should also detect a
  hang (status lines stop, window not responding) and take stacks itself.
- **Benchmark**: PresentMon (pinned version) at a fixed checkpoint, with a mode switch that
  isolates costs (tracking only / copy only / full submit). Reject captures taken in menus, pause
  or cutscenes. Per-frame costs hiding in setup code (like re-validating the graphics adapter
  every frame) show up here long before anyone notices them in play.

## Stereo side effects

When the second eye is drawn by adding a camera or view to the game's own render list, the game
runs its per-view code for both eyes, but also any per-frame code that happens to sit inside the
view pass. Per-frame work done twice causes bugs that look unrelated to stereo: a resource release
that isn't idempotent corrupts bookkeeping until a level teardown hangs; a temporal effect (eye
adaptation, history ping-pong) steps twice per frame and the second eye runs ahead of the first.
The extra view can also shift the game's own views (picture-in-picture, mirrors) into different
slots, and anything the game derives from a slot number then indexes out of range.

- **Count calls per eye.** Using hooks the mod already installs (no new ones to port per game
  patch), count each hook's calls per frame in mono and in stereo. Label each hook per-view (should
  double) or per-frame (must not). Flag a per-frame hook above ~1.25x its mono rate and a per-view
  hook below ~1.75x (it skipped an eye); report mixed hooks without flagging. Wait for enough frames
  in both buckets (loads and recoveries are mono, so a normal run has both).
- **Audit the view pass once**, read-only: list the per-frame work inside it and say what would
  confirm or rule out each risk. Turn the confirmed ones into guards that skip exactly the
  duplicate, and log how often each guard fires and from which call site.
- **Flicker in one eye** usually means the second view reuses view-dependent state from the
  first: a per-view selection (shadowed lights) written into a shared atlas by list position, or a
  temporal history advanced once per view. Measure one-eye blips, then swap which pose each pass
  renders and try both passes at the same pose:
  [references/eye-flicker.md](references/eye-flicker.md).
- **Check the game's other views** while stereo is on: where they land in the render list, and
  whether anything is indexed by that position. Holding stereo off while one is showing is a safe
  first fix.

## The image matches the camera

Each eye's image must show the world where that eye's projection says it is. A post effect that
warps the finished image (lens distortion, barrel or panini projection, a sprint FOV kick, an
upscaler fed the wrong input rectangle) breaks that without breaking anything you'd notice in one
eye. A warp of a few pixels pushed outward in both eyes is a vergence error over the whole world:
it looks roughly right, scale feels a bit off, and nobody reports it. It shows up when the mod draws
something in 3D (a crosshair, a marker, a guide) and the player sees it double while looking at
what it marks.

- **Check where the image says straight ahead is.** In an eye snapshot at a known pose, pick lines
  that run straight away from the camera in the world (floor grid lines, corridor edges), fit them,
  and find where they meet at the horizon. Project the same direction through the eye's own world
  and projection matrices. They should agree to a pixel or two. An offset mirrored in the two eyes
  (left eye out to the left, right eye out to the right) is a warp, not a pose error. Record the
  matrices beside every snapshot so this needs no guessing.
- **Find the stage.** Rerun at native render resolution (no upscaler) and then with each suspect
  post effect off (most engines expose them as data presets). The run where the offset drops to
  about zero names the cause. Switch it off for the headset in the mod's data, and rerun the
  check after every rebuild of that data.
- **Check overlays against the scene, not against your own maths.** A test that the overlay lands
  where your projection puts it only proves the projection agrees with itself. Measure the
  horizontal shift between the eyes of the overlay and of the surface it marks, and compare: equal
  shift means it sits on that surface. Match on a feature that doesn't repeat (an edge, a shadow
  boundary); a regular texture or grid matches at several shifts and fools the comparison.
- **Measure after stereo settles.** Many mods restart stereo a few times in the first seconds.
  A mode switch or measurement in that window picks up its gaps and looks like a regression;
  wait until stereo has run cleanly for a while, then switch.

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
  does. Skip menus with a direct test-scene launch for most runs, and have the mod log a
  `scene_ready` event (or similar) that the launcher waits on instead of watching the screen.
- **But script the real menu flow too.** A direct launch never exercises startup screens, pause
  menus, level exits or loads, so their bugs only turn up in playtests. Drive them with key presses
  into the game window, keyed off the game's menu/loading state as the mod logs it rather than
  screenshots, and keep a fixed tour (startup, into the game, pause, back, quit to title) that each
  build runs, followed by the run report. Pitfalls: menus that open with nothing selected (the
  first press only selects, so every count is off by one); keys only land while the game window
  is in front, and the OS may refuse to bring a window started from a background process forward;
  screenshotting a hung window blocks forever; a run whose VR session never started is testing a
  different mod, so fail it; a launcher killed mid-run skips its cleanup, so check for leftover mod
  files before the next launch. Read menu item positions off a screenshot once and record them;
  don't guess.
- **Bisect with switches**: let the launcher take one named feature switch out of an otherwise
  normal launch, or add one diagnostic switch, and clear everything it doesn't set. Swapping in an
  older build of the mod answers "is this a regression?".
