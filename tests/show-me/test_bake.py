import http.client
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "show-me" / "scripts"
SERVER = SCRIPTS / "server.py"
KEY = "0123456789abcdef0123456789abcdef"
FRAGMENT = '<h1>Login flow</h1>\n<figure class="diagram"><pre class="mermaid">flowchart LR\n  a --> b</pre></figure>'
DOCUMENT = "<!DOCTYPE html>\n<html><head><title>Mine</title></head><body><p>own</p></body></html>"


def load_server():
    spec = importlib.util.spec_from_file_location("show_me_server_bake", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


srv = load_server()


def boot_of(body):
    m = re.search(r'<script id="sm-boot" type="application/json">(.*?)</script>', body, re.S)
    assert m, "no sm-boot script in page"
    return json.loads(m.group(1))


def run(*args, cwd=None):
    env = {k: v for k, v in os.environ.items() if k != "SSH_CONNECTION"}
    return subprocess.run([sys.executable, str(SERVER)] + list(args), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, universal_newlines=True, env=env, cwd=cwd, timeout=30)


class BakeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.screens = self.root / "screens"
        self.screens.mkdir()
        self.out = self.root / "standalone"
        self.frame = self.root / "frame.html"
        shutil.copy(str(SCRIPTS / "frame.html"), str(self.frame))

    def write(self, name, text, mtime):
        p = self.screens / name
        p.write_text(text, encoding="utf-8")
        os.utime(str(p), (mtime, mtime))
        return p

    def test_fragment_is_baked_into_the_frame_without_live_refresh(self):
        src = self.write("flow.html", FRAGMENT, 1000)
        out = srv.bake_screen(src, self.out, self.frame, "demo")
        self.assertEqual(out, self.out / "flow.html")
        body = out.read_text(encoding="utf-8")
        self.assertTrue(body.startswith("<!doctype html>"))
        self.assertIn("<title>Login flow</title>", body)
        self.assertIn("<style>", body)
        self.assertIn(FRAGMENT, body)
        self.assertNotIn("data-show-me-poll", body)
        self.assertEqual(boot_of(body), {
            "screen": "flow.html", "newest": "flow.html", "screens": [],
            "project": "demo", "address": "", "standalone": True,
        })

    def test_full_document_is_copied_byte_for_byte(self):
        src = self.write("full.html", DOCUMENT, 1000)
        out = srv.bake_screen(src, self.out, self.frame, "demo")
        self.assertEqual(out.read_bytes(), src.read_bytes())

    def test_sync_bakes_new_and_changed_screens_only(self):
        now = time.time()
        os.utime(str(self.frame), (now - 100, now - 100))
        self.write("a.html", FRAGMENT, now - 50)
        self.write("b.html", DOCUMENT, now - 50)
        (self.screens / "notes.txt").write_text("skip")
        self.assertEqual(sorted(p.name for p in srv.sync_standalone(self.screens, self.out, self.frame, "demo")),
                         ["a.html", "b.html"])
        self.assertEqual(srv.sync_standalone(self.screens, self.out, self.frame, "demo"), [])
        self.write("a.html", "<h1>v2</h1>", time.time() + 5)
        self.assertEqual([p.name for p in srv.sync_standalone(self.screens, self.out, self.frame, "demo")],
                         ["a.html"])
        self.assertIn("<h1>v2</h1>", (self.out / "a.html").read_text(encoding="utf-8"))
        os.utime(str(self.frame), (time.time() + 10, time.time() + 10))
        self.assertEqual(sorted(p.name for p in srv.sync_standalone(self.screens, self.out, self.frame, "demo")),
                         ["a.html", "b.html"])

    def test_sync_skips_a_screen_it_cannot_read_and_bakes_the_rest(self):
        self.write("a.html", FRAGMENT, 1000)
        self.write("b.html", FRAGMENT, 1000)
        real = srv.bake_screen

        def flaky(src, *rest):
            if Path(src).name == "a.html":
                raise FileNotFoundError(str(src))  # deleted between listing and reading
            return real(src, *rest)

        srv.bake_screen = flaky
        self.addCleanup(setattr, srv, "bake_screen", real)
        self.assertEqual([p.name for p in srv.sync_standalone(self.screens, self.out, self.frame, "demo")],
                         ["b.html"])

    def test_standalone_files_never_become_tabs(self):
        self.write("a.html", FRAGMENT, 1000)
        srv.sync_standalone(self.screens, self.out, self.frame, "demo")
        self.assertEqual([s["name"] for s in srv.list_screens(self.screens)], ["a.html"])
        self.assertNotIn(self.screens.resolve(), self.out.resolve().parents)

    def test_api_screens_bakes_while_serving(self):
        httpd = srv.make_server(self.screens, KEY, "127.0.0.1", 0, "localhost", "demo", self.frame,
                                standalone_dir=self.out)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        self.write("flow.html", FRAGMENT, time.time())
        conn = http.client.HTTPConnection("127.0.0.1", httpd.server_address[1], timeout=5)
        conn.request("GET", "/api/screens?key=" + KEY)
        self.assertEqual(conn.getresponse().status, 200)
        conn.close()
        self.assertIn(FRAGMENT, (self.out / "flow.html").read_text(encoding="utf-8"))


class BakeCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "proj"
        self.project.mkdir()
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        self.session = self.project / ".superpowers" / "show-me"
        self.screens = self.session / "screens"
        self.screens.mkdir(parents=True)
        (self.screens / "flow.html").write_text(FRAGMENT, encoding="utf-8")
        (self.screens / "full.html").write_text(DOCUMENT, encoding="utf-8")

    def bake(self, *args):
        r = run("bake", "--project-dir", str(self.project), *args)
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.strip().splitlines()
        self.assertEqual(len(lines), 1, r.stdout)
        return json.loads(lines[0])

    def test_bake_all_writes_standalone_dir_ignored_by_git(self):
        out = self.bake("--all")
        standalone = (self.session / "standalone").resolve()
        self.assertEqual(Path(out["standalone_dir"]), standalone)
        self.assertEqual(sorted(Path(p).name for p in out["baked"]), ["flow.html", "full.html"])
        self.assertIn("Login flow", (standalone / "flow.html").read_text(encoding="utf-8"))
        ignored = subprocess.run(["git", "-C", str(self.project), "check-ignore", "-q",
                                  str(standalone / "flow.html")])
        self.assertEqual(ignored.returncode, 0)

    def test_bake_named_screen_to_another_dir(self):
        dest = Path(self.tmp.name) / "elsewhere"
        out = self.bake("flow.html", "--out", str(dest))
        self.assertEqual(out["baked"], [str((dest / "flow.html").resolve())])
        self.assertFalse((self.session / "standalone").exists())

    def test_bake_needs_a_screen_or_all(self):
        self.assertNotEqual(run("bake", "--project-dir", str(self.project)).returncode, 0)
        r = run("bake", "--project-dir", str(self.project), "missing.html")
        self.assertEqual(r.returncode, 1)
        self.assertIn("missing.html", r.stderr)

    def test_running_server_bakes_new_screens(self):
        self.addCleanup(run, "stop", "--project-dir", str(self.project))
        r = run("start", "--project-dir", str(self.project))
        self.assertEqual(r.returncode, 0, r.stderr)
        started = json.loads(r.stdout)
        target = Path(started["standalone_dir"]) / "late.html"
        (self.screens / "late.html").write_text("<h1>Late</h1>", encoding="utf-8")
        with urllib.request.urlopen(started["url"].replace("/?key=", "/api/screens?key="), timeout=5) as resp:
            self.assertEqual(resp.status, 200)
        self.assertIn("<h1>Late</h1>", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
