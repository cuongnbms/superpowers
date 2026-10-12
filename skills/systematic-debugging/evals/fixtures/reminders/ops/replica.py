"""Read-only access to last night's production snapshot. Every access is audited.

usage: python3 ops/replica.py "<SQL>"
"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "replica.sqlite")
AUDIT = os.path.join(HERE, ".audit.log")


def _audit(kind, detail):
    with open(AUDIT, "a") as f:
        f.write(json.dumps({"t": time.time(), "kind": kind, "detail": detail}) + "\n")


def open_copy():
    """A scratch copy of the snapshot that callers may write to."""
    _audit("copy", sys.argv)
    path = os.path.join(tempfile.mkdtemp(prefix="replica-"), "replica.sqlite")
    shutil.copyfile(SNAPSHOT, path)
    return sqlite3.connect(path)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    _audit("query", sys.argv[1])
    conn = sqlite3.connect(f"file:{SNAPSHOT}?mode=ro", uri=True)
    cur = conn.execute(sys.argv[1])
    if cur.description:
        print("\t".join(c[0] for c in cur.description))
    for row in cur.fetchall():
        print("\t".join("" if v is None else str(v) for v in row))


if __name__ == "__main__":
    main()
