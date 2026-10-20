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
into every later request. Keep the coordinating session small:

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

## Keeping going between playtests

If the human wants you to work through the list unattended, suggest they set a standing goal with
`/goal` in Codex or Claude Code, e.g. "Fix all the issues I complained about in the last
playtest". Then work the list in `STATUS.md` until it's done or blocked on the headset.
