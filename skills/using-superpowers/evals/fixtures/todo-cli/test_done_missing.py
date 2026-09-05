import subprocess, sys, json
from pathlib import Path

def test_done_unknown_id_reports_error(tmp_path, monkeypatch):
    store = Path(__file__).with_name("todo.json")
    store.write_text("[]")
    r = subprocess.run([sys.executable, "todo.py", "done", "99"], capture_output=True, text=True, cwd=Path(__file__).parent)
    assert r.returncode != 0
    assert "not found" in r.stderr
