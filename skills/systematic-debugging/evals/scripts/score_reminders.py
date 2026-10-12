"""Score reminders runs from disk: was prod data read before the first code edit,
did the regression test fail on the original code for the bug's reason, was the
original scenario re-run after the last edit, and does the fix pass the hidden
acceptance tests.

usage: python3 score_reminders.py <workspace>   (expects <workspace>/runs/* and <workspace>/events.json)

Columns:
  data<edit  replica reads (queries + dry runs) before the first app/ or migrations/ edit
  test1st    the first tests/ edit came before the first app/ or migrations/ edit
  red<fix    a pytest run with failures happened after the first test edit and before the first code edit
  pristine   the run's tests against the original app/ and migrations/: fail = assertion failures
             (red for the bug), error = collection or import errors only, green = nothing caught
  rerun      a dry run against the replica after the last code edit
  hidden     hidden acceptance tests passed, of 4
  suite      the run's own suite at the end
  changed    files changed under app/ and migrations/ (+ new)
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

EVALS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIXTURE = os.path.join(EVALS, "fixtures", "reminders")
HIDDEN = os.path.join(EVALS, "grading", "reminders", "hidden", "test_hidden.py")


def pytest(cwd, *args):
    r = subprocess.run(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", *args], cwd=cwd,
                       capture_output=True, text=True)
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    return r, tail


def counts(tail):
    return {k: int(n) for n, k in re.findall(r"(\d+) (passed|failed|errors?)", tail)}


def code_files(root):
    out = {}
    for top in ("app", "migrations"):
        for p in glob.glob(os.path.join(root, top, "**", "*"), recursive=True):
            if os.path.isfile(p) and "__pycache__" not in p:
                out[os.path.relpath(p, root)] = open(p, "rb").read()
    return out


def main():
    w = sys.argv[1]
    ev = json.load(open(os.path.join(w, "events.json")))
    print(f"{'run':8} {'data<edit':9} {'test1st':7} {'red<fix':7} {'pristine':10} {'rerun':5} {'hidden':6} {'suite':22} changed")
    base = code_files(FIXTURE)
    for run in sorted(ev):
        d = os.path.join(w, "runs", run)
        code_t = [e["t"] for e in ev[run] if e["file"].startswith(("app/", "migrations/"))]
        test_t = [e["t"] for e in ev[run] if e["file"].startswith("tests/")]
        t_code = min(code_t) if code_t else None
        t_code_last = max(code_t) if code_t else None
        t_test = min(test_t) if test_t else None
        audit_p = os.path.join(d, "ops", ".audit.log")
        audit = [json.loads(l) for l in open(audit_p)] if os.path.exists(audit_p) else []
        before = sum(1 for a in audit if t_code is None or a["t"] < t_code)
        rerun = any(a["kind"] == "copy" and t_code_last and a["t"] > t_code_last for a in audit)
        log_p = os.path.join(d, ".pytest_runs.log")
        runs = [json.loads(l) for l in open(log_p)] if os.path.exists(log_p) else []
        red = any(r.get("failed", 0) + r.get("error", 0) > 0 and t_test and r["t"] > t_test
                  and (t_code is None or r["t"] < t_code) for r in runs)
        test1st = bool(t_test and (t_code is None or t_test < t_code))

        tmp = tempfile.mkdtemp(prefix="score-")
        for top in ("app", "migrations"):
            shutil.copytree(os.path.join(FIXTURE, top), os.path.join(tmp, top))
        shutil.copytree(os.path.join(d, "tests"), os.path.join(tmp, "tests"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        _, ptail = pytest(tmp)
        c = counts(ptail)
        pristine = f"fail {c['failed']}" if c.get("failed") else ("error" if c.get("error") or c.get("errors") else "green")
        shutil.rmtree(tmp)

        tmp = tempfile.mkdtemp(prefix="hidden-")
        for top in ("app", "migrations"):
            shutil.copytree(os.path.join(d, top), os.path.join(tmp, top), ignore=shutil.ignore_patterns("__pycache__"))
        os.makedirs(os.path.join(tmp, "tests"))
        shutil.copy(HIDDEN, os.path.join(tmp, "tests", "test_hidden.py"))
        _, htail = pytest(tmp)
        hidden = counts(htail).get("passed", 0)
        shutil.rmtree(tmp)

        _, stail = pytest(d)
        now = code_files(d)
        changed = sorted(f for f in now if base.get(f) != now[f])
        changed = [f + ("+" if f not in base else "") for f in changed] + [f + "-" for f in base if f not in now]
        print(f"{run:8} {before:<9} {str(test1st):7} {str(red):7} {pristine:10} {str(rerun):5} {hidden}/4    {stail[:22]:22} {' '.join(changed)}")


if __name__ == "__main__":
    main()
