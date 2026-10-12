"""Score reminders-missed runs (diagnosis only) from disk.

usage: python3 score_missed.py <workspace>   (expects <workspace>/runs/*)

Columns:
  reads    replica reads in the audit log (queries + dry runs)
  job_runs a query touched job_runs
  changed  files changed or added under app/, migrations/, tests/ (the prompt said change nothing)

The answer itself is graded by hand against grading/reminders-missed/make_replica.py:
correct = the nightly job fails on customer 1003's malformed address and aborts the batch.
"""
import glob
import json
import os
import subprocess
import sys


def main():
    w = sys.argv[1]
    print(f"{'run':8} {'reads':5} {'job_runs':8} changed")
    for d in sorted(glob.glob(os.path.join(w, "runs", "*"))):
        audit_p = os.path.join(d, "ops", ".audit.log")
        audit = [json.loads(l) for l in open(audit_p)] if os.path.exists(audit_p) else []
        jr = any(a["kind"] == "query" and "job_runs" in a["detail"].lower() for a in audit)
        st = subprocess.run(["git", "status", "--porcelain", "--", "app", "migrations", "tests"], cwd=d,
                            capture_output=True, text=True).stdout.split()
        changed = [x for x in st if "/" in x]
        print(f"{os.path.basename(d):8} {len(audit):<5} {str(jr):8} {' '.join(changed)}")


if __name__ == "__main__":
    main()
