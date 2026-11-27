# Player sim: a vision model plays the real game

Reaching a test spot in the real game (past the intro, into the open world, a later level) by
hand or by key schedule is slow and brittle, and computer use pays for a screenshot on every
step. A loop that freezes the game between turns lets a vision model play it: game time passes
only while the model's inputs play out, so model latency costs wall time, not reactions. Its
first job is usually a save past the intro, so every later run starts at gameplay.

## The loop

1. Suspend the whole game process (`NtSuspendProcess`; resume with `NtResumeProcess`). Resume in
   a `finally`, and never let two sims suspend the same process.
2. Grab the game window's client area. Run the game windowed: an exclusive-fullscreen game can
   grab black. The desktop keeps showing the last frame while the game is suspended.
3. Send the picture and a status line to the model: turn number, how much the picture changed
   since the last turn, save status, the last result (rejected reply, reflex firings) and the
   model's own notes. Ask for one JSON object: what it sees, what it will do, short running
   notes, and a list of actions.
4. Resume, focus the window, perform the actions, release every key and button, suspend again.

- **Actions:** hold keys for N seconds (optionally with a camera turn spread over the hold, and
  optionally tapping another key partway through: "hold the modifier, then click", which some
  games miss when both go down together); tap keys (count, gap); turn the camera; wait. Waits
  carry cutscenes and loading screens.
- **Validate every reply.** Only listed keys; never Print Screen (on Windows it opens a snipping
  tool), the game's own screenshot key or Alt. Cap non-wait time per turn (8 s is a starting
  default). Reject a bad reply with a message the model can act on, and do nothing that turn.
- **Bounded context.** Keep one headless model session with image input open across turns (a new
  process per turn costs seconds to start), restart it every ~30 turns, and carry the notes over.
  Run it on the account the human chose; keep API keys out of the child's environment if it must
  not bill an API account.
- **Journal every turn** (picture, reply, result) in the run folder, and resume notes and turn
  numbers from the journal after a restart. A stop file in the run folder ends the loop cleanly.
- **Unit-test the pure parts:** reply parsing, action validation, progress detection.

## What the model needs to be told

Keys alone aren't enough; tell it how the game works, and add each lesson to the system prompt
as you find it (a restart picks it up).

- Cutscenes and loading: wait rather than press.
- Camera turns are approximate: check the next picture and correct.
- In combat (only for games that have it), keep turns under a second so it sees more warnings.
  Say how the game aims: on keyboard and mouse, attacks may go toward the held movement key, not
  where the camera points. Focus one enemy until it falls, follow a stun with attacks, and use
  finishers on downed enemies; spreading hits across a group can leave it dying with no kills.
- It can't judge wall time: "stuck for half an hour" can be two minutes. Judge stalls from the
  journal's timestamps, not its notes.

## Reflexes for timed prompts

Only for games with timed prompts (counters, dodges, quick-time events). In stills taken between
turns the model rarely sees a warning in time. Run a thread while the actions play that grabs the
window about 30 times a second, template-matches the prompt icon (normalised cross-correlation at
half scale), and presses the response, with a cooldown of about 0.5 s. Use a fast capture library:
a general screenshot call can take ~100 ms. Calibrate on frames the sim has already captured:
score frames with and without the icon and put the threshold between the groups. Tell the model
in the next status line when the reflex fired. The template is game art: keep it out of the repo.

## Window and camera

- A game's windowed mode may ignore the requested size. Resize the window from the sim to a set
  client size; renderers usually follow. About 1600 px wide keeps prompt text legible.
- Mouse look often reads cursor deltas and recentres the cursor, so synthetic relative moves
  work. Turn the same amount fast and slow to check it is linear and not rate-limited.
- Measure a turn with phase correlation on a crop without HUD text: static text pins the match at
  zero shift. Calibrate in a bright scene; dark scenes give match peaks too low to trust.

## Saves

- Find the save file, and back up every change with the turn that wrote it.
- **Judge progress on story data only.** A save file may start with settings that change when a
  menu opens or the window resizes. Some writes change only a few bytes (timestamps, play time,
  retry checkpoints), and intro checkpoints may not be loadable progress. Hash from the first
  story section, count a change as progress only above a size threshold (64 bytes is a starting
  default), and still back up the small ones. Comparing whole files can show "no progress" when
  there was some, and "progress" when there was none.
- **A death can write a checkpoint** that looks like progress. Check what changed before
  stopping on it.
- **Prove a save by loading it.** Relaunch, continue, and look at where the game resumes: often a
  fixed point (the last checkpoint or safe spot), not where the save was written. Record each
  verified save with what it loads into and the run that checked it.
- Give the launcher a command that puts a backed-up save in place. Refuse while the game runs
  (it rewrites the file), and keep the file it replaces.
