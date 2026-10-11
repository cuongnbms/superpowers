"""Score pricing runs: hidden acceptance tests, mutant kill rate, and red->green cycles.

usage: python3 score_pricing.py <workspace>   (expects <workspace>/runs/* and <workspace>/events.json)

Columns: hidden = the run's src passes grading/hidden; testsOnRef = the run's tests pass on the
reference implementation; killed = mutants in grading/mutants its tests fail on; 1st = first file
edited; redRuns = pytest runs with a failure; R->G = red runs followed by a green run;
maxNewRed = the largest number of failures in one run (more than 1 means tests were written ahead).
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

GRADING = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "grading")


def check(impl, tests):
    """Run the tests in <tests> against <impl> copied in as src/pricing.py; return pass or fail."""
    w = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(w, "src"))
        open(os.path.join(w, "src", "__init__.py"), "w").close()
        shutil.copy(impl, os.path.join(w, "src", "pricing.py"))
        shutil.copytree(tests, os.path.join(w, "tests"), ignore=shutil.ignore_patterns("__pycache__"))
        r = subprocess.run(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"], cwd=w,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "pass" if r.returncode == 0 else "fail"
    finally:
        shutil.rmtree(w)


def count_tests(d):
    out = subprocess.run(["python3", "-m", "pytest", "-q", "--collect-only", "-p", "no:cacheprovider", "tests"],
                         cwd=d, capture_output=True, text=True).stdout
    return sum(1 for line in out.splitlines() if "::" in line)


def bad(r):
    return r.get("failed", 0) + r.get("error", 0)


def main():
    w = sys.argv[1]
    ref = os.path.join(GRADING, "ref_pricing.py")
    mutants = sorted(glob.glob(os.path.join(GRADING, "mutants", "*.py")))
    ev = json.load(open(os.path.join(w, "events.json")))
    print(f"{'run':7} {'hidden':7} {'testsOnRef':10} {'killed':7} {'#tests':6} {'1st':5} {'redRuns':7} {'R->G':5} {'maxNewRed':9} seq")
    for run in sorted(ev):
        d = os.path.join(w, "runs", run)
        hidden = check(os.path.join(d, "src", "pricing.py"), os.path.join(GRADING, "hidden"))
        on_ref = check(ref, os.path.join(d, "tests"))
        killed = sum(check(m, os.path.join(d, "tests")) == "fail" for m in mutants) if on_ref == "pass" else "n/a"
        tt = [e["t"] for e in ev[run] if e["file"].startswith("test")]
        ts = [e["t"] for e in ev[run] if e["file"].startswith("src")]
        first = "test" if tt and (not ts or min(tt) < min(ts)) else "src"
        log = os.path.join(d, ".pytest_runs.log")
        runs = [json.loads(line) for line in open(log)] if os.path.exists(log) else []
        reds = sum(1 for r in runs if bad(r))
        rg = sum(1 for a, b in zip(runs, runs[1:]) if bad(a) and not bad(b))
        max_red = max([bad(r) for r in runs] or [0])
        seq = " ".join(f"{r.get('passed', 0)}/{bad(r)}" for r in runs)
        print(f"{run:7} {hidden:7} {on_ref:10} {str(killed):7} {count_tests(d):<6} {first:5} {reds:<7} {rg:<5} {max_red:<9} {seq}")


if __name__ == "__main__":
    main()
