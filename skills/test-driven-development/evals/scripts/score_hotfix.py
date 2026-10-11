"""Score hotfix runs: was the test edited before src, and was red seen before the fix?

usage: python3 score_hotfix.py <workspace>   (expects <workspace>/runs/* and <workspace>/events.json)
"""
import json
import os
import subprocess
import sys

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fixtures", "hotfix")


def main():
    w = sys.argv[1]
    ev = json.load(open(os.path.join(w, "events.json")))
    print(f"{'run':6} {'1st edit':9} {'red-before-fix':15} {'final':22} {'tests+':6} {'src diff':8} runs(pass/fail)")
    for run in sorted(ev):
        d = os.path.join(w, "runs", run)
        tt = [e["t"] for e in ev[run] if e["file"].startswith("test")]
        ts = [e["t"] for e in ev[run] if e["file"].startswith("src")]
        t_test, t_src = (min(tt) if tt else None), (min(ts) if ts else None)
        first = "test" if t_test and (not t_src or t_test < t_src) else "src"
        log = os.path.join(d, ".pytest_runs.log")
        runs = [json.loads(line) for line in open(log)] if os.path.exists(log) else []
        red = any(r.get("failed", 0) > 0 and t_test and r["t"] > t_test and (not t_src or r["t"] < t_src) for r in runs)
        final = subprocess.run(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=d,
                               capture_output=True, text=True).stdout.strip().splitlines()[-1]
        added = sum(1 for line in open(os.path.join(d, "tests", "test_pagination.py")) if line.startswith("def test_")) - 3
        diff = subprocess.run(["diff", os.path.join(FIXTURE, "src", "pagination.py"), os.path.join(d, "src", "pagination.py")],
                              capture_output=True, text=True).stdout
        dl = sum(1 for line in diff.splitlines() if line[:1] in "<>")
        seq = " ".join(f"{r.get('passed', 0)}/{r.get('failed', 0)}" for r in runs)
        print(f"{run:6} {first:9} {str(red):15} {final[:22]:22} {added:<6} {dl:<8} {seq}")


if __name__ == "__main__":
    main()
