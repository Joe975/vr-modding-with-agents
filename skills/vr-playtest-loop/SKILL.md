---
name: vr-playtest-loop
description: Run a voice-recorded VR playtest and turn the human's spoken complaints into reproduced, fixed and proven work items. Use when the human is about to playtest in the headset, says "record my feedback", "process the playtest", or hands over playtest notes; also for setting development goals between sessions.
---

# VR playtest loop

1. The human plays with the mic recording and complains about everything that's wrong.
2. For each complaint, make sure you can reproduce it (test driver, eye snapshots, trace; see the
   vr-mod-test-harness skill). If you can't, come back to the human for guidance.
3. Fix it and prove the fix against your own reproduction.
4. The human goes back in only to check it feels right, after a batch of fixes rather than each one.

## Recording

`scripts/voice_capture.py` records the mic for the whole session, keeps the full WAV, and appends
timestamped faster-whisper lines to `transcript.md`. Transcription is local (CPU, int8).

```
python -m pip install -r scripts/requirements.txt
python scripts/voice_capture.py --list-devices
python scripts/voice_capture.py --device "Valve" --out C:/abs/path/sessions/session-YYYYMMDD_HHMM
```

- Download the Whisper model once beforehand (`small.en` by default); the script runs offline.
- Start it as a background task you'll be notified about, and confirm it printed `LISTENING`
  before telling the human to start.
- It closes when the human says only "go ahead", when a `STOP` file appears in the session folder,
  or at the time limit. Humans forget the phrase: use the STOP file to close it yourself.

## Lining it up with the game

`scripts/interleave.py` merges the transcript with the mod's log or trace by time, and attaches
the game events before each note:

```
python scripts/interleave.py transcript.md mod.log --context 15 > timeline.md
```

Now "the gun's aiming low" sits next to `fire aim=(0.02,-0.31,0.95) hit=no`. Expect transcription
errors and off-topic chatter; the timestamps matter more than the words.

## Turning notes into work

> For each note, reproduce it without me: a test driver script, eye snapshots, the trace. Show it
> failing, fix it, show it passing. If you can't reproduce something, tell me what you'd need.

If an issue can't be reproduced, either the harness has a gap to fix, or the note needs a better
description from the human. Say which.

## Between sessions

Agents stop when they think they're done. Set the goal explicitly with `/goal` (Codex and Claude
Code), e.g. "Fix all the issues I complained about in the last playtest".
