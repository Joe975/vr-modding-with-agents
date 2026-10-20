"""Query a JSON-lines gameplay trace without reading it: a few columns, a time window, a row cap.

  python trace_query.py trace.jsonl --count
  python trace_query.py trace.jsonl --type event --limit 40
  python trace_query.py trace.jsonl --around dodge --window 1 --fields t,metrics.head_offset_metres --every 3

Each line of the trace is one JSON object with a time field `t` (seconds) and a `type`
("header", "sample", "event"); events name themselves in `event`. Fields are dotted paths into
the object (`metrics.head_offset_metres`, `input.left.pos.1`). Output is tab-separated with one
header row: missing values print as `-`, floats to 3 decimals, lists comma-joined.
"""
import argparse
import json
import sys
from collections import Counter


def get(obj, path):
    for part in path.split("."):
        if isinstance(obj, dict):
            obj = obj.get(part)
        elif isinstance(obj, list) and part.lstrip("-").isdigit() and -len(obj) <= int(part) < len(obj):
            obj = obj[int(part)]
        else:
            return None
    return obj


def cell(value):
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, list):
        return ",".join(cell(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, separators=(",", ":"))
    return str(value)


def read(lines):
    for line in lines:
        line = line.strip()
        if line:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def windows(records, around, width):
    try:
        centres = [float(around)]
    except ValueError:
        centres = [r.get("t", 0.0) for r in records if r.get("event") == around]
    return [(c - width, c + width) for c in centres]


def query(records, type_=None, event=None, around=None, width=1.0, start=None, end=None, every=1):
    records = list(records)
    spans = windows(records, around, width) if around is not None else None
    picked = []
    for r in records:
        t = r.get("t")
        if type_ and r.get("type") != type_:
            continue
        if event and r.get("event") != event:
            continue
        if start is not None and (t is None or t < start):
            continue
        if end is not None and (t is None or t > end):
            continue
        if spans is not None and not any(lo <= (t or 0.0) <= hi for lo, hi in spans):
            continue
        picked.append(r)
    # Downsample samples only; events are rare and always matter.
    out, n = [], 0
    for r in picked:
        if r.get("type") == "sample":
            n += 1
            if (n - 1) % every:
                continue
        out.append(r)
    return out


def default_fields(rows):
    if rows and all(r.get("type") == "event" for r in rows):
        keys = []
        for r in rows:
            keys += [k for k in r if k not in keys]
        return keys
    return ["t", "type", "event"]


def format_rows(rows, fields, limit):
    lines = ["\t".join(fields)]
    lines += ["\t".join(cell(get(r, f)) for f in fields) for r in rows[:limit]]
    if len(rows) > limit:
        lines.append(f"... {len(rows) - limit} more rows (narrow the window, raise --every or --limit)")
    return "\n".join(lines)


def counts(records):
    records = list(records)
    times = [r["t"] for r in records if isinstance(r.get("t"), (int, float))]
    c = Counter(r.get("type", "?") if r.get("type") != "event" else f"event {r.get('event')}" for r in records)
    span = f"{min(times):.3f}-{max(times):.3f} s" if times else "no times"
    return "\n".join([f"{len(records)} records, {span}"] + [f"{n}\t{k}" for k, n in c.most_common()])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("trace")
    parser.add_argument("--count", action="store_true", help="records per type and event, then stop")
    parser.add_argument("--type", dest="type_", help="sample, event, header")
    parser.add_argument("--event", help="only events with this name")
    parser.add_argument("--around", help="event name or time in seconds to centre windows on")
    parser.add_argument("--window", type=float, default=1.0, help="seconds either side of --around")
    parser.add_argument("--from", dest="start", type=float)
    parser.add_argument("--to", dest="end", type=float)
    parser.add_argument("--fields", help="comma-separated dotted paths (default: t,type,event)")
    parser.add_argument("--every", type=int, default=1, help="keep every Nth sample")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args(argv)
    with open(args.trace, encoding="utf-8") as handle:
        records = read(handle)
        if args.count:
            print(counts(records))
            return 0
        rows = query(records, args.type_, args.event, args.around, args.window, args.start, args.end, max(1, args.every))
    fields = args.fields.split(",") if args.fields else default_fields(rows)
    print(format_rows(rows, fields, args.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
