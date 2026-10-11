import json
import os
import time


def pytest_sessionfinish(session, exitstatus):
    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    stats = {k: len(v) for k, v in (tr.stats.items() if tr else []) if k in ("passed", "failed", "error")}
    with open(os.path.join(os.path.dirname(__file__), ".pytest_runs.log"), "a") as f:
        f.write(json.dumps({"t": time.time(), "exit": int(exitstatus), **stats}) + "\n")
