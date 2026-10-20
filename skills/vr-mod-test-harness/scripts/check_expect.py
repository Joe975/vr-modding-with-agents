"""Check a test-driver run's metrics against the scenario's `expect` list and print PASS/FAIL.

  python check_expect.py scenario.json run.metrics.json

The scenario carries its own expectations, so a run is judged by numbers rather than by reading
the trace:

  "expect": [
    {"metric": "root_displacement.right_metres", "min": 0.5, "why": "dodge went sideways"},
    {"metric": "root_displacement.forward_metres", "max": 0.08},
    {"metric": "terminal", "equals": "completed"}
  ]

`metric` is a dotted path into the metrics JSON the mod writes for the run (list items by index,
e.g. `dodge_windows.0.right_metres`); `count` of a list is `path.#`. Each expectation needs at
least one of `min`, `max`, `equals`. Exit code 0 when all pass, 1 otherwise.
"""
import json
import sys


def get(obj, path):
    for part in path.split("."):
        if part == "#" and isinstance(obj, list):
            obj = len(obj)
        elif isinstance(obj, dict):
            obj = obj.get(part)
        elif isinstance(obj, list) and part.lstrip("-").isdigit() and -len(obj) <= int(part) < len(obj):
            obj = obj[int(part)]
        else:
            return None
    return obj


def check(expect, metrics):
    """Returns [(ok, line)] for each expectation."""
    results = []
    for e in expect:
        path = e["metric"]
        value = get(metrics, path)
        bounds = {k: e[k] for k in ("min", "max", "equals") if k in e}
        if not bounds:
            raise ValueError(f"expectation for {path} has no min, max or equals")
        if value is None:
            ok = False
        elif "equals" in bounds:
            ok = value == bounds["equals"]
        else:
            ok = isinstance(value, (int, float)) and not isinstance(value, bool)
            ok = ok and ("min" not in bounds or value >= bounds["min"]) and ("max" not in bounds or value <= bounds["max"])
        shown = "missing" if value is None else (f"{value:.3f}" if isinstance(value, float) else json.dumps(value))
        rule = ", ".join(f"{k} {json.dumps(v)}" for k, v in bounds.items())
        why = f"  [{e['why']}]" if e.get("why") else ""
        results.append((ok, f"{path} = {shown} ({rule}){why}"))
    return results


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print(__doc__)
        return 2
    with open(argv[0], encoding="utf-8") as handle:
        expect = json.load(handle).get("expect", [])
    with open(argv[1], encoding="utf-8") as handle:
        metrics = json.load(handle)
    if not expect:
        print("FAIL scenario has no expect list: add one so the run can be judged without the trace")
        return 1
    results = check(expect, metrics)
    for ok, line in results:
        print(("PASS " if ok else "FAIL ") + line)
    failed = sum(not ok for ok, _ in results)
    print(f"VERDICT {'FAIL' if failed else 'PASS'} ({len(results) - failed} of {len(results)} passed)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
