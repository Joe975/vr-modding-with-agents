---
name: vr-playtest-loop
description: Run a voice-recorded VR playtest and turn the human's spoken complaints into reproduced, fixed and proven work items. Use when the human is about to playtest in the headset, says "record my feedback", "process the playtest", or hands over playtest notes.
---

# VR playtest loop

1. The human plays with the mic recording and complains about everything that's wrong.
2. For each complaint, make sure you can reproduce it (test driver, eye snapshots, trace; see the
   vr-mod-test-harness skill). If you can't, come back to the human for guidance.
3. Fix it and prove the fix against your own reproduction.
4. The human goes back in only to check it feels right, after a batch of fixes rather than each one.

## Recording

`scripts/voice_capture.py` (in this skill's folder, e.g. `.agents/skills/vr-playtest-loop/scripts/`)
records the mic for the whole session, keeps the full WAV, and appends timestamped faster-whisper
lines to `transcript.md`. Transcription runs locally on the CPU and never needs the network once the
model is downloaded.

One-time setup, from the mod repo's venv:

```
python -m pip install -r .agents/skills/vr-playtest-loop/scripts/requirements.txt
python -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8')"
```

The second line downloads the `small.en` model (a few hundred MB) into the Hugging Face cache. Ask
the human before running it.

Each session:

```
python .agents/skills/vr-playtest-loop/scripts/voice_capture.py --list-devices
python .agents/skills/vr-playtest-loop/scripts/voice_capture.py --device "[mic name]" --out [absolute path]/sessions/session-YYYYMMDD_HHMM
```

- `--device` matches part of the microphone's name or its index ("Valve" picks a Valve Index
  headset mic). `--out` must be an absolute path to a new folder.
- Start it as a background task you'll be notified about, and confirm it printed `LISTENING`
  before telling the human to start.
- It closes when the human says only "go ahead", when a `STOP` file appears in the session folder,
  or at the time limit. Humans forget the phrase: use the STOP file to close it yourself.

## Lining it up with the game

`scripts/interleave.py` merges the transcript with the mod's log or trace by time, and attaches
the game events before each note:

```
python .agents/skills/vr-playtest-loop/scripts/interleave.py [session]/transcript.md [mod log] --context 15 > timeline.md
```

Now "the gun's aiming low" sits next to an aim/hit event, or "the lever didn't move" next to an
interaction request and the unchanged puzzle state. Record the active context (on foot, vehicle,
menu, etc.) so the same binding's different uses aren't confused. Expect transcription errors
and off-topic chatter; the timestamps matter more than the words.

## Turning notes into work

For each note: reproduce it without the human (a test driver script, eye snapshots, the trace),
show it failing, fix it, and show it passing. Record each one in `STATUS.md`.

If an issue can't be reproduced, either the harness has a gap to fix, or the note needs a better
description from the human. Say which, and what you'd need.

## Splitting the work

A long session that does everything itself carries every screenshot, log and file it has read
into every later request. The same goes outside the loop: start a new session for each new feature
or unrelated change. Keep the coordinating session small:

- **One orchestrator** holds the complaint list in `STATUS.md`, decides the order, and owns the
  game install and headset. It doesn't read code, traces or images itself.
- **One worker per complaint or feature**, each in its own git worktree with a fresh context. The
  worker reproduces, fixes and proves its one item, commits, and reports back a few lines:
  verdict, commit, the evidence file paths and anything it needs from the human.
- **Checks go to throwaway contexts too.** Launch, run the scenario, read `frame_check.py` and
  `check_expect.py`, and return the verdict lines. If a worker needs to look at an image, it
  looks at the failure preview, in its own context.
- **One run at a time.** Worktrees are separate, but the game install, the runtime and the headset
  are shared. The orchestrator queues runs (or workers take a lock file) and every run removes
  the mod afterwards.

When a worker's report doesn't settle it, the orchestrator asks that worker a follow-up question
rather than reading the evidence itself.

## Guards, not one-off fixes

After a few playtests, fixes tend to arrive one screen at a time: this menu, that loading screen,
this cutscene. Each is proven against its own reproduction, and the next playtest finds the next
one. When that happens, stop and sort the recent fixes into families, then build one shared guard
per family that would have caught the next case. Prove each guard changes no existing decision
(sweep every input combination against the old rules) before switching consumers to it.
Families that recur in VR mods:

- **What is on screen.** Gameplay, menu, loading, cutscene, photo mode: if several parts of the
  mod each read the game's raw state flags their own way, a new flag combination is gameplay to
  some and a menu to others. Put one classifier in front of the flags. Unknown bits don't change
  the mode; log each new mask the first time it's seen.
- **The headset always shows something.** Stereo when the mod can produce it, the flat game on a
  panel whenever it isn't flowing (a short stall, e.g. 500 ms, is enough), never the runtime's
  waiting screen.
- **Stereo stops for good.** If every recovery is a special case, stopping is the default. Add a
  last rung that resets the whole stereo stack to its startup state without needing the cause,
  once it has been stopped a few seconds and no load is in progress, with a budget (e.g. three
  restarts in ten minutes) before it gives up for the session. Also guard the other way stereo
  disappears: nothing stopped, but readiness refusing every job for a player-state reason.
- **Gates that refuse while a state is unknown.** Each is a deadlock risk when the refused action
  is what would resolve the state (a draw that would tell you which weapon is held; a trigger that
  never fires for an unrecognised weapon). One rule: refuse a brief unknown, then act on the best
  default after a grace period (2 s is a start).
- **Tables keyed by per-level game objects.** They fill after enough level loads and then refuse
  the player's own objects. Evict the least recently seen row once it's stale; never evict live
  rows.
- **Timers that outlived their cause.** A hold added while chasing a bug often stays after the real
  cause is found, costing a degraded view every time it fires and hiding the next cause. Audit
  them: what each was for, whether the cause is known now, and a switch to test without it.
- **Controls that can't reach an action.** A test presses every controller input in each mode
  (menus first) and checks the union reaching the game covers every native button, with listed,
  reasoned gaps. Check it by mutation: dropping one route must fail it.

## Keeping going between playtests

If the human wants you to work through the list unattended, suggest they set a standing goal with
`/goal` in Codex or Claude Code, e.g. "Fix all the issues I complained about in the last
playtest". Then work the list in `STATUS.md` until it's done or blocked on the headset.
