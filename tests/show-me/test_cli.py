import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "skills" / "show-me" / "scripts" / "server.py"
KEYS = {"url", "screen_dir", "session_dir", "port", "pid", "reused"}


def load_server():
    spec = importlib.util.spec_from_file_location("show_me_server_cli", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if k != "SSH_CONNECTION"}
    env.update(extra)
    return env


def run(*args, env=None, cwd=None):
    return subprocess.run([sys.executable, str(SERVER)] + list(args), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, universal_newlines=True,
                          env=env or clean_env(), cwd=cwd, timeout=30)


def fetch(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)  # registered first, so it runs after the stop cleanups below
        self.base = Path(self.tmp.name)
        self.project = self.base / "proj"
        self.project.mkdir()
        self.session = self.project / ".superpowers" / "show-me"

    def tearDown(self):
        run("stop", "--project-dir", str(self.project))

    def start(self, *extra, env=None):
        r = run("start", "--project-dir", str(self.project), *extra, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.strip().splitlines()
        self.assertEqual(len(lines), 1, r.stdout)
        return json.loads(lines[0])

    def info(self):
        return json.loads((self.session / "server.json").read_text())

    def test_start_prints_contract_and_writes_session(self):
        out = self.start()
        self.assertEqual(set(out), KEYS)
        self.assertFalse(out["reused"])
        self.assertEqual(Path(out["session_dir"]), self.session.resolve())
        self.assertEqual(Path(out["screen_dir"]), (self.session / "screens").resolve())
        self.assertTrue(Path(out["screen_dir"]).is_dir())
        self.assertEqual((self.session / ".gitignore").read_text(), "*\n")
        info = self.info()
        self.assertEqual(set(info), {"pid", "port", "host", "url", "key", "started_at"})
        self.assertRegex(info["key"], r"^[0-9a-f]{32}$")
        self.assertEqual(info["host"], "127.0.0.1")
        self.assertEqual(info["pid"], out["pid"])
        self.assertEqual(out["url"], "http://localhost:%d/?key=%s" % (out["port"], info["key"]))
        self.assertEqual(fetch(out["url"]), 200)

    def test_server_json_is_private_to_its_owner(self):
        self.start()
        self.assertEqual((self.session / "server.json").stat().st_mode & 0o777, 0o600)

    def test_start_twice_reuses_the_running_server(self):
        first = self.start()
        second = self.start()
        self.assertTrue(second["reused"])
        self.assertEqual((second["port"], second["pid"], second["url"]),
                         (first["port"], first["pid"], first["url"]))

    def test_status_and_stop_exit_codes(self):
        out = self.start()
        st = run("status", "--project-dir", str(self.project))
        self.assertEqual(st.returncode, 0)
        self.assertEqual(json.loads(st.stdout)["pid"], out["pid"])
        self.assertEqual(run("stop", "--project-dir", str(self.project)).returncode, 0)
        st = run("status", "--project-dir", str(self.project))
        self.assertEqual((st.returncode, st.stdout), (1, ""))
        self.assertEqual(run("stop", "--project-dir", str(self.project)).returncode, 0)
        self.assertIsNone(self.info()["pid"])

    def test_restart_keeps_port_and_key(self):
        first = self.start()
        run("stop", "--project-dir", str(self.project))
        second = self.start()
        self.assertFalse(second["reused"])
        self.assertEqual(second["url"], first["url"])
        self.assertEqual(fetch(second["url"]), 200)

    def test_taken_port_moves_to_a_free_one(self):
        first = self.start()
        run("stop", "--project-dir", str(self.project))
        blocker = socket.socket()
        self.addCleanup(blocker.close)
        blocker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # ignore TIME_WAIT left by fetch
        blocker.bind(("127.0.0.1", first["port"]))
        blocker.listen(1)
        second = self.start()
        self.assertNotEqual(second["port"], first["port"])
        self.assertEqual(fetch(second["url"]), 200)

    def test_stale_pid_is_neither_reused_nor_killed(self):
        self.start()
        run("stop", "--project-dir", str(self.project))
        info = self.info()
        info["pid"] = os.getpid()
        (self.session / "server.json").write_text(json.dumps(info))
        self.assertEqual(run("stop", "--project-dir", str(self.project)).returncode, 0)
        out = self.start()
        self.assertFalse(out["reused"])
        self.assertNotEqual(out["pid"], os.getpid())
        self.assertEqual(fetch(out["url"]), 200)

    def test_ssh_connection_sets_bind_and_url_hosts(self):
        out = self.start(env=clean_env(SSH_CONNECTION="10.0.0.9 5000 10.0.0.5 22"))
        self.assertTrue(out["url"].startswith("http://10.0.0.5:%d/?key=" % out["port"]), out["url"])
        info = self.info()
        self.assertEqual(info["host"], "0.0.0.0")
        self.assertEqual(fetch("http://127.0.0.1:%d/?key=%s" % (out["port"], info["key"])), 200)

    def test_derive_hosts(self):
        srv = load_server()
        ssh = {"SSH_CONNECTION": "10.0.0.9 5000 10.0.0.5 22"}
        self.assertEqual(srv.derive_hosts(ssh, None, None), ("0.0.0.0", "10.0.0.5"))
        self.assertEqual(srv.derive_hosts({}, None, None), ("127.0.0.1", "localhost"))
        self.assertEqual(srv.derive_hosts(ssh, "127.0.0.1", "devbox"), ("127.0.0.1", "devbox"))
        self.assertEqual(srv.derive_hosts({"SSH_CONNECTION": "garbage"}, None, None), ("127.0.0.1", "localhost"))

    def test_idle_timeout_stops_the_server(self):
        self.start("--idle-minutes", "0.02")
        deadline = time.time() + 15
        while time.time() < deadline:
            stopped = run("status", "--project-dir", str(self.project)).returncode == 1
            if stopped and self.info()["pid"] is None:
                return
            time.sleep(0.3)
        self.fail("server still running 15 s after a 1.2 s idle timeout")

    def test_foreground_prints_json_then_serves(self):
        proc = subprocess.Popen([sys.executable, str(SERVER), "start", "--foreground",
                                 "--project-dir", str(self.project)],
                                stdout=subprocess.PIPE, universal_newlines=True, env=clean_env())
        self.addCleanup(proc.stdout.close)
        self.addCleanup(proc.wait, 10)
        self.addCleanup(proc.terminate)
        out = json.loads(proc.stdout.readline())
        self.assertEqual(set(out), KEYS)
        self.assertEqual(out["pid"], proc.pid)
        self.assertEqual(fetch(out["url"]), 200)

    def test_default_project_dir_is_the_git_toplevel(self):
        repo = self.base / "repo"
        (repo / "sub").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        self.addCleanup(run, "stop", "--project-dir", str(repo))
        r = run("start", cwd=str(repo / "sub"))
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(Path(out["screen_dir"]), (repo / ".superpowers" / "show-me" / "screens").resolve())

    def test_outside_a_repo_uses_tmpdir(self):
        plain = self.base / "plain"
        plain.mkdir()
        tmpdir = self.base / "t"
        tmpdir.mkdir()
        env = clean_env(TMPDIR=str(tmpdir))
        self.addCleanup(run, "stop", cwd=str(plain), env=env)
        r = run("start", cwd=str(plain), env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        session = Path(json.loads(r.stdout)["session_dir"])
        rel = session.relative_to(tmpdir.resolve())
        self.assertRegex(rel.parts[0], r"^show-me-[0-9a-f]{12}$")
        self.assertEqual(rel.parts[1:], (".superpowers", "show-me"))
