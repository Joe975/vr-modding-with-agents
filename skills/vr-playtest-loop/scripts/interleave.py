"""Merge a voice_capture.py transcript with a game/mod log by time.

Each note gets the log lines from the CONTEXT seconds before it (and a few after), so the agent
sees what was happening when the human spoke. Log lines need a timestamp: an ISO 8601 datetime
anywhere in the line, or a bare HH:MM:SS(.fff) time (dated from the transcript's first note).
Lines without one are skipped.

Usage: python interleave.py transcript.md game.log [more.log ...] [--context 15] [--after 3]
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

NOTE = re.compile(r"^- \[(?P<stamp>[^\]]+)\] (?P<text>.+)$")
ISO = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")
CLOCK = re.compile(r"(?<!\d)(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(?!\d)")


def parse_notes(text):
    notes = []
    for line in text.splitlines():
        m = NOTE.match(line.strip())
        if m:
            notes.append((dt.datetime.fromisoformat(m["stamp"]), m["text"]))
    return notes


def stamp_line(line, day, tz):
    """Return the line's timestamp as an aware datetime, or None."""
    m = ISO.search(line)
    if m:
        stamp = dt.datetime.fromisoformat(m.group(0).replace(" ", "T").replace("Z", "+00:00"))
        return stamp if stamp.tzinfo else stamp.replace(tzinfo=tz)
    m = CLOCK.search(line)
    if m:
        frac = (m.group(4) or "0").ljust(6, "0")
        return dt.datetime.combine(day, dt.time(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(frac)), tz)
    return None


def interleave(notes, log_lines, context=15.0, after=3.0):
    if not notes:
        return "No notes found in the transcript.\n"
    day, tz = notes[0][0].date(), notes[0][0].tzinfo
    events = sorted((s, line.rstrip()) for line in log_lines if (s := stamp_line(line, day, tz)))
    out = ["# Playtest timeline", ""]
    for stamp, text in notes:
        out.append(f"## {stamp.strftime('%H:%M:%S')} \"{text}\"")
        window = [line for s, line in events
                  if stamp - dt.timedelta(seconds=context) <= s <= stamp + dt.timedelta(seconds=after)]
        out.extend(["", "```", *(window or ["(no log lines in this window)"]), "```", ""])
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("logs", type=Path, nargs="+")
    parser.add_argument("--context", type=float, default=15.0, help="seconds of log before each note")
    parser.add_argument("--after", type=float, default=3.0, help="seconds of log after each note")
    args = parser.parse_args(argv)
    notes = parse_notes(args.transcript.read_text(encoding="utf-8"))
    lines = [line for log in args.logs for line in log.read_text(encoding="utf-8", errors="replace").splitlines()]
    sys.stdout.write(interleave(notes, lines, args.context, args.after))


if __name__ == "__main__":
    main()
