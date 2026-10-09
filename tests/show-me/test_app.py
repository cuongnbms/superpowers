import http.client
import importlib.util
import json
import os
import re
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "show-me" / "scripts"
KEY = "0123456789abcdef0123456789abcdef"


def load_server():
    spec = importlib.util.spec_from_file_location("show_me_server", SCRIPTS / "server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


srv = load_server()


def boot_of(body):
    m = re.search(r'<script id="sm-boot" type="application/json">(.*?)</script>', body, re.S)
    assert m, "no sm-boot script in page"
    return json.loads(m.group(1))


class Resp:
    def __init__(self, status, headers, body):
        self.status, self.headers, self.body = status, headers, body

    def header(self, name):
        return self.headers.get(name.lower())


class AppTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.screens = self.root / "screens"
        self.screens.mkdir()
        self.port = self.serve("demo")

    def serve(self, project):
        httpd = srv.make_server(self.screens, KEY, "127.0.0.1", 0, "localhost", project, SCRIPTS / "frame.html")
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        return httpd.server_address[1]

    def tearDown(self):
        self.tmp.cleanup()

    def get(self, path, cookie=None, port=None):
        conn = http.client.HTTPConnection("127.0.0.1", port or self.port, timeout=5)
        conn.request("GET", path, headers={"Cookie": cookie} if cookie else {})
        r = conn.getresponse()
        resp = Resp(r.status, {k.lower(): v for k, v in r.getheaders()}, r.read().decode("utf-8"))
        conn.close()
        return resp

    def authed(self, path, port=None):
        sep = "&" if "?" in path else "?"
        return self.get(path + sep + "key=" + KEY, port=port)

    def write(self, name, text, mtime):
        p = self.screens / name
        p.write_text(text, encoding="utf-8")
        os.utime(str(p), (mtime, mtime))

    def test_no_key_is_403_on_every_route(self):
        for path in ["/", "/api/screens", "/s/a.html", "/files/a.svg", "/nope"]:
            self.assertEqual(self.get(path).status, 403, path)

    def test_wrong_key_is_403(self):
        self.assertEqual(self.get("/?key=" + "f" * 32).status, 403)

    def test_query_key_sets_cookie_named_by_port(self):
        r = self.authed("/")
        self.assertEqual(r.status, 200)
        cookie = r.header("Set-Cookie")
        self.assertTrue(cookie.startswith("show_me_key_%d=%s" % (self.port, KEY)), cookie)
        for attr in ("HttpOnly", "SameSite=Strict", "Path=/"):
            self.assertIn(attr, cookie)

    def test_cookie_alone_passes(self):
        r = self.get("/api/screens", cookie="show_me_key_%d=%s" % (self.port, KEY))
        self.assertEqual(r.status, 200)

    def test_cookie_for_another_port_fails(self):
        r = self.get("/api/screens", cookie="show_me_key_%d=%s" % (self.port + 1, KEY))
        self.assertEqual(r.status, 403)

    def test_api_screens_sorted_by_mtime_skipping_hidden_and_non_html(self):
        self.write("b.html", "<p>b</p>", 1000)
        self.write("a.html", "<p>a</p>", 2000)
        self.write(".draft.html", "<p>hidden</p>", 3000)
        self.write("notes.txt", "not a screen", 4000)
        data = json.loads(self.authed("/api/screens").body)
        self.assertEqual([s["name"] for s in data["screens"]], ["b.html", "a.html"])
        self.assertEqual(data["screens"][0]["mtime"], 1000)
        self.assertEqual(data["newest"], "a.html")

    def test_missing_screen_dir_is_an_empty_list_and_empty_page(self):
        self.screens.rmdir()
        self.assertEqual(json.loads(self.authed("/api/screens").body), {"screens": [], "newest": None})
        r = self.authed("/")
        self.assertEqual(r.status, 200)
        boot = boot_of(r.body)
        self.assertIsNone(boot["screen"])
        self.assertEqual(boot["screens"], [])

    def test_fragment_is_wrapped_in_frame(self):
        self.write("flow.html", "<h1>Luồng <em>đăng   nhập</em></h1>\n<p>body</p>", 1000)
        r = self.authed("/")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.header("Content-Type"), "text/html; charset=utf-8")
        self.assertIn("<title>Luồng đăng nhập</title>", r.body)
        self.assertRegex(r.body, r'id="sm-content"[^>]*>\s*<h1>Luồng <em>đăng   nhập</em></h1>\n<p>body</p>')
        self.assertEqual(boot_of(r.body), {
            "screen": "flow.html", "newest": "flow.html",
            "screens": [{"name": "flow.html", "mtime": 1000}],
            "project": "demo", "address": "localhost:%d" % self.port,
        })

    def test_title_falls_back_to_file_name(self):
        self.write("no-heading.html", "<p>x</p>", 1000)
        self.assertIn("<title>no-heading.html</title>", self.authed("/").body)

    def test_full_document_is_served_as_is_with_poll_script(self):
        doc = "<!DOCTYPE html>\n<html><head><title>Mine</title></head><body><p>own</p></body></html>"
        self.write("full.html", doc, 1000)
        body = self.authed("/").body
        self.assertTrue(body.startswith("<!DOCTYPE html>"))
        self.assertNotIn('id="sm-tabs"', body)
        self.assertIn("<p>own</p>", body)
        self.assertLess(body.index("data-show-me-poll"), body.rindex("</body>"))

    def test_named_screen_with_non_ascii_name(self):
        self.write("sơ đồ.html", "<h1>Cũ</h1>", 1000)
        self.write("moi.html", "<h1>Mới</h1>", 2000)
        r = self.authed("/s/" + quote("sơ đồ.html"))
        self.assertEqual(r.status, 200)
        self.assertIn("<h1>Cũ</h1>", r.body)
        boot = boot_of(r.body)
        self.assertEqual(boot["screen"], "sơ đồ.html")
        self.assertEqual(boot["newest"], "moi.html")

    def test_unknown_or_escaping_screen_is_404(self):
        self.assertEqual(self.authed("/s/missing.html").status, 404)
        self.assertEqual(self.authed("/s/" + quote("../frame.html", safe="")).status, 404)

    def test_files_route_serves_assets_and_rejects_traversal(self):
        (self.screens / "img.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
        (self.root / "secret.txt").write_text("secret", encoding="utf-8")
        r = self.authed("/files/img.svg")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.header("Content-Type"), "image/svg+xml")
        self.assertEqual(self.authed("/files/../secret.txt").status, 404)
        self.assertEqual(self.authed("/files/%2e%2e/secret.txt").status, 404)

    def test_placeholder_text_inside_a_fragment_stays_literal(self):
        self.write("raw.html", "<p>{{TITLE}} {{CONTENT}} {{BOOT}}</p>", 1000)
        body = self.authed("/").body
        self.assertIn("<p>{{TITLE}} {{CONTENT}} {{BOOT}}</p>", body)
        self.assertEqual(boot_of(body)["screen"], "raw.html")

    def test_boot_survives_script_close_in_project_name(self):
        port = self.serve("a</script>b")
        body = self.authed("/", port=port).body
        self.assertEqual(boot_of(body)["project"], "a</script>b")
