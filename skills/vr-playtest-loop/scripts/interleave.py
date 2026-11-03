"""Merge a voice_capture.py transcript with a game/mod log by time.

Each note gets the log lines from the CONTEXT seconds before it (and a few after), so the agent
sees what was happening when the human spoke. Log lines need a timestamp: an ISO 8601 datetime
anywhere in the line, or a bare HH:MM:SS(.fff) time (dated from the transcript's first note).
Lines without one are skipped.

A JSON-lines gameplay trace works too. Its records carry `t` in seconds from the run's start, so
its header record must carry that start as `"start": "<ISO 8601 with timezone>"`. Header and event
records are placed at start + t; samples are left out (query them with trace_query.py using the
`t` shown).

Usage: python interleave.py transcript.md game.log [trace.jsonl ...] [--context 15] [--after 3]
Exit code 0, or 1 when the transcript has no notes. Output is UTF-8.
"""
import argparse
import datetime as dt
import json
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


def trace_lines(lines):
    """A trace's header and event records as ISO-stamped log lines; None if `lines` isn't a trace."""
    records = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            return None
        if not isinstance(record, dict) or not isinstance(record.get("t"), (int, float)):
            return None
        records.append(record)
    if not records:
        return None
    header = next((r for r in records if r.get("type") == "header"), {})
    if not header.get("start"):
        raise ValueError('trace has no wall-clock start: add "start": "<ISO 8601 with timezone>" to its header record')
    start = dt.datetime.fromisoformat(header["start"].replace("Z", "+00:00"))
    out = []
    for r in records:
        if r.get("type") in ("header", "event"):
            rest = {k: v for k, v in r.items() if k not in ("t", "type", "event", "start")}
            label = r.get("event") or r.get("type")
            stamp = (start + dt.timedelta(seconds=r["t"])).isoformat(timespec="milliseconds")
            out.append(f"{stamp} [trace t={r['t']:.3f}] {label}" + (f" {json.dumps(rest)}" if rest else ""))
    return out


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
    # Windows consoles and `> timeline.md` default to a legacy code page that can't hold every
    # character people say or logs print.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    notes = parse_notes(args.transcript.read_text(encoding="utf-8"))
    if not notes:
        print(f"No notes found in {args.transcript}: expected lines like `- [<ISO time>] text`.", file=sys.stderr)
        return 1
    lines = []
    for log in args.logs:
        text = log.read_text(encoding="utf-8", errors="replace").splitlines()
        trace = trace_lines(text)
        lines += text if trace is None else trace
    sys.stdout.write(interleave(notes, lines, args.context, args.after))
    return 0


if __name__ == "__main__":
    sys.exit(main())
