"""Record spoken playtest feedback: continuous WAV plus timestamped Whisper text.

Long commentary is split into bounded chunks; transcription never needs a network
connection once the model is cached. Closes on the spoken trigger alone ("go ahead"),
a STOP file in the session folder, Ctrl+C or the time limit.
"""
import argparse
from collections import deque
import datetime as dt
import json
from pathlib import Path
import queue
import re
import time
import wave

import numpy as np

RATE = 16000
BLOCK = 480


def is_trigger(text, phrase="go ahead"):
    normalize = lambda value: " ".join(re.findall(r"[a-z0-9]+", value.lower()))
    return bool(phrase.strip()) and normalize(text) == normalize(phrase)


class Segmenter:
    """Energy gate with pre-roll, pause flush, and a hard continuous-speech limit."""
    def __init__(self, threshold=0.006, silence=1.2, maximum=20):
        self.threshold = threshold
        self.silence_limit = max(1, round(silence * RATE / BLOCK))
        self.maximum = max(1, round(maximum * RATE / BLOCK))
        self.pre = deque(maxlen=6)
        self.frames = []
        self.start = None
        self.quiet = 0
        self.voiced = 0

    def feed(self, block, stamp):
        loud = float(np.sqrt(np.mean(block ** 2))) >= self.threshold
        if not self.frames:
            if not loud:
                self.pre.append((block, stamp))
                return None
            self.frames = [item[0] for item in self.pre]
            self.start = self.pre[0][1] if self.pre else stamp
            self.pre.clear()
        self.frames.append(block)
        self.voiced += int(loud)
        self.quiet = 0 if loud else self.quiet + 1
        if self.quiet >= self.silence_limit or len(self.frames) >= self.maximum:
            return self.flush()
        return None

    def flush(self):
        result = (self.start, np.concatenate(self.frames)) if self.frames and self.voiced >= 5 else None
        self.frames = []
        self.start = None
        self.quiet = self.voiced = 0
        return result


def resolve_device(devices, requested):
    candidates = [(i, d) for i, d in enumerate(devices) if d["max_input_channels"] > 0]
    if requested.isdecimal():
        for i, d in candidates:
            if i == int(requested):
                return i, d
    else:
        for i, d in candidates:
            if requested.lower() in d["name"].lower():
                return i, d
    raise ValueError(f"No input microphone matches {requested!r}; use --list-devices")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--device", default="Valve", help="name substring or index (Index headset mic by default)")
    parser.add_argument("--title", default="VR playtest feedback")
    parser.add_argument("--model", default="small.en")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--trigger", default="go ahead")
    parser.add_argument("--seconds", type=float, default=3600)
    parser.add_argument("--threshold", type=float, default=0.006)
    args = parser.parse_args()
    import sounddevice as sd
    if args.list_devices:
        print(sd.query_devices())
        return
    if not args.out or not args.out.is_absolute():
        parser.error("--out must be an absolute new session directory")
    if args.seconds <= 0 or args.threshold <= 0:
        parser.error("--seconds and --threshold must be positive")
    device, info = resolve_device(sd.query_devices(), args.device)
    sd.check_input_settings(device=device, channels=1, samplerate=RATE, dtype="float32")
    from faster_whisper import WhisperModel
    print(f"Loading cached {args.model}, CPU/int8, 4 threads; microphone: {info['name']}", flush=True)
    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=4, local_files_only=True)
    args.out.mkdir(parents=True, exist_ok=False)
    transcript = args.out / "transcript.md"
    started = dt.datetime.now().astimezone()
    metadata = {"started": started.isoformat(), "microphone": info["name"], "model": args.model,
                "sample_rate": RATE, "trigger": args.trigger, "max_seconds": args.seconds}
    (args.out / "session.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    transcript.write_text(f"# {args.title}\n\nStarted: {started.isoformat()}\nMicrophone: {info['name']}\n\n", encoding="utf-8")
    (args.out.parent / "CURRENT_SESSION.txt").write_text(str(args.out), encoding="utf-8")
    audio_q = queue.Queue()
    segmenter = Segmenter(threshold=args.threshold)

    def callback(indata, frames, timing, status):
        stamp = dt.datetime.now().astimezone() - dt.timedelta(seconds=frames / RATE)
        audio_q.put((indata[:, 0].copy(), stamp, str(status) if status else ""))

    def transcribe(part):
        if part is None:
            return False
        stamp, audio = part
        segments, _ = model.transcribe(audio, language="en", vad_filter=True, beam_size=1,
                                       condition_on_previous_text=False)
        text = " ".join(s.text.strip() for s in segments).strip()
        if not text:
            return False
        line = f"- [{stamp.isoformat(timespec='milliseconds')}] {text}\n"
        with transcript.open("a", encoding="utf-8") as output:
            output.write(line)
        print(line.strip(), flush=True)
        return is_trigger(text, args.trigger)

    reason = "duration limit"
    try:
        with wave.open(str(args.out / "audio.wav"), "wb") as recording:
            recording.setnchannels(1)
            recording.setsampwidth(2)
            recording.setframerate(RATE)
            with sd.InputStream(samplerate=RATE, channels=1, blocksize=BLOCK, dtype="float32",
                                device=device, callback=callback):
                deadline = time.monotonic() + args.seconds
                print(f"LISTENING: {transcript}\nSay only '{args.trigger}' to finish; or create {args.out / 'STOP'}", flush=True)
                while time.monotonic() < deadline:
                    if (args.out / "STOP").exists():
                        reason = "stop file"
                        break
                    try:
                        block, stamp, status = audio_q.get(timeout=0.25)
                    except queue.Empty:
                        continue
                    recording.writeframes((np.clip(block, -1, 1) * 32767).astype("<i2").tobytes())
                    if status:
                        with transcript.open("a", encoding="utf-8") as output:
                            output.write(f"<!-- {stamp.isoformat()} audio status: {status} -->\n")
                    if transcribe(segmenter.feed(block, stamp)):
                        reason = "spoken trigger"
                        break
                if reason != "spoken trigger":
                    transcribe(segmenter.flush())
    except KeyboardInterrupt:
        reason = "keyboard stop"
        transcribe(segmenter.flush())
    except Exception as exc:
        reason = f"error: {exc}"
        raise
    finally:
        metadata.update(ended=dt.datetime.now().astimezone().isoformat(), end_reason=reason)
        (args.out / "session.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        with transcript.open("a", encoding="utf-8") as output:
            output.write(f"\n<!-- Closed {metadata['ended']}: {reason} -->\n")
        print(f"CLOSED: {reason}; feedback in {transcript}", flush=True)


if __name__ == "__main__":
    main()
