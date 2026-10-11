"""Record when each run's source and test files change.

usage: python3 watch.py <runs-dir> <events.json> <seconds>

Start it after every run directory exists and before the first agent starts:
it snapshots the directories once at startup and rewrites <events.json> on
every tick.
"""
import glob
import json
import os
import sys
import time


def snap(d):
    r = {}
    paths = (glob.glob(os.path.join(d, "src", "*.py"))
             + glob.glob(os.path.join(d, "tests", "**", "*.py"), recursive=True)
             + glob.glob(os.path.join(d, "test*.py")))
    for p in paths:
        try:
            r[os.path.relpath(p, d)] = os.stat(p).st_mtime_ns
        except FileNotFoundError:
            pass
    return r


def main():
    runs, out, dur = sys.argv[1], sys.argv[2], float(sys.argv[3])
    dirs = sorted(glob.glob(os.path.join(runs, "*")))
    last = {d: snap(d) for d in dirs}
    events = {os.path.basename(d): [] for d in dirs}
    end = time.time() + dur
    while time.time() < end:
        for d in dirs:
            cur = snap(d)
            for f, m in cur.items():
                if last[d].get(f) != m:
                    events[os.path.basename(d)].append({"t": time.time(), "file": f})
            last[d] = cur
        with open(out, "w") as fh:
            json.dump(events, fh)
        time.sleep(0.1)


if __name__ == "__main__":
    main()
