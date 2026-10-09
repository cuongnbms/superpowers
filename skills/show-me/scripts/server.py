#!/usr/bin/env python3
"""show-me: serve agent-written HTML screens in a browser tab (standard library only)."""

import hmac
import html
import http.server
import json
import mimetypes
import re
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urlsplit, parse_qs

POLL_SCRIPT = """<script data-show-me-poll>
(function () {
  var newest = __SM_NEWEST__;
  var fails = 0;
  function next() { setTimeout(poll, Math.min(1000 + 1000 * fails, 5000)); }
  function poll() {
    fetch("/api/screens", { credentials: "same-origin", cache: "no-store" })
      .then(function (r) {
        if (!r.ok) { throw new Error("poll failed"); }
        return r.json();
      })
      .then(function (d) {
        var recovered = fails > 0;
        fails = 0;
        if (d.newest !== newest) { location.href = "/"; return; }
        if (recovered) { location.reload(); return; }
        next();
      })
      .catch(function () { fails += 1; next(); });
  }
  setTimeout(poll, 1000);
})();
</script>"""

_PLACEHOLDER = re.compile(r"\{\{(TITLE|CONTENT|BOOT)\}\}")
_H1 = re.compile(r"<h1\b[^>]*>(.*?)</h1\s*>", re.I | re.S)
_TAG = re.compile(r"<[^>]*>")
_BODY_CLOSE = re.compile(r"</body\s*>", re.I)

mimetypes.add_type("image/svg+xml", ".svg")


def list_screens(screen_dir: Path) -> List[Dict[str, Any]]:
    screens = []  # type: List[Dict[str, Any]]
    try:
        entries = list(Path(screen_dir).iterdir())
    except OSError:
        return screens
    for p in entries:
        if p.name.startswith(".") or p.suffix != ".html":
            continue
        try:
            if not p.is_file():
                continue
            screens.append({"name": p.name, "mtime": p.stat().st_mtime})
        except OSError:
            continue
    screens.sort(key=lambda s: (s["mtime"], s["name"]))
    return screens


def screen_title(fragment: str, name: str) -> str:
    m = _H1.search(fragment)
    if m:
        text = " ".join(html.unescape(_TAG.sub("", m.group(1))).split())
        if text:
            return html.escape(text)
    return html.escape(name)


def _is_full_document(content: str) -> bool:
    head = content.lstrip().lower()
    return head.startswith("<!doctype") or head.startswith("<html")


def _inject_poll(doc: str, newest: Optional[str]) -> str:
    script = POLL_SCRIPT.replace("__SM_NEWEST__", json.dumps(newest).replace("</", "<\\/"))
    last = None
    for last in _BODY_CLOSE.finditer(doc):
        pass
    if last is None:
        return doc + script
    return doc[:last.start()] + script + doc[last.start():]


def render_page(frame: str, title: str, content: str, boot: Dict[str, Any]) -> str:
    if _is_full_document(content):
        return _inject_poll(content, boot.get("newest"))
    values = {
        "TITLE": title,
        "CONTENT": content,
        "BOOT": json.dumps(boot).replace("</", "<\\/"),
    }
    return _PLACEHOLDER.sub(lambda m: values[m.group(1)], frame)


def make_server(screen_dir: Path, key: str, bind_host: str, port: int, url_host: str,
                project: str, frame_path: Path) -> http.server.ThreadingHTTPServer:
    screen_dir = Path(screen_dir)
    key_bytes = key.encode("utf-8")

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002
            pass

        def _port(self) -> int:
            return self.server.server_address[1]

        def _send(self, status: int, body: bytes, ctype: str, extra: Optional[Dict[str, str]] = None) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _text(self, status: int, text: str, extra: Optional[Dict[str, str]] = None) -> None:
            self._send(status, text.encode("utf-8"), "text/plain; charset=utf-8", extra)

        def _html(self, text: str, extra: Optional[Dict[str, str]]) -> None:
            self._send(200, text.encode("utf-8"), "text/html; charset=utf-8", extra)

        def _matches(self, candidate: Optional[str]) -> bool:
            if not candidate:
                return False
            return hmac.compare_digest(candidate.encode("utf-8"), key_bytes)

        def do_GET(self) -> None:
            parts = urlsplit(self.path)
            cookie_name = "show_me_key_%d" % self._port()
            extra = {}  # type: Dict[str, str]
            query_key = (parse_qs(parts.query).get("key") or [None])[0]
            if self._matches(query_key):
                extra["Set-Cookie"] = "%s=%s; HttpOnly; SameSite=Strict; Path=/" % (cookie_name, key)
            else:
                cookie_key = None
                try:
                    jar = SimpleCookie(self.headers.get("Cookie", ""))
                    if cookie_name in jar:
                        cookie_key = jar[cookie_name].value
                except Exception:
                    cookie_key = None
                if not self._matches(cookie_key):
                    self._text(403, "forbidden")
                    return
            path = unquote(parts.path)
            if path == "/":
                self._screen(None, extra)
            elif path.startswith("/s/"):
                self._screen(path[3:], extra)
            elif path == "/api/screens":
                screens = list_screens(screen_dir)
                data = {"screens": screens, "newest": screens[-1]["name"] if screens else None}
                self._send(200, json.dumps(data).encode("utf-8"), "application/json; charset=utf-8", extra)
            elif path.startswith("/files/"):
                self._file(path[7:], extra)
            else:
                self._text(404, "not found", extra)

        def _screen(self, name: Optional[str], extra: Dict[str, str]) -> None:
            screens = list_screens(screen_dir)
            newest = screens[-1]["name"] if screens else None
            if name is None:
                name = newest
            elif name not in [s["name"] for s in screens]:
                self._text(404, "not found", extra)
                return
            content = ""
            if name is not None:
                try:
                    content = (screen_dir / name).read_text(encoding="utf-8", errors="replace")
                except OSError:
                    self._text(404, "not found", extra)
                    return
            boot = {
                "screen": name,
                "newest": newest,
                "screens": screens,
                "project": project,
                "address": "%s:%d" % (url_host, self._port()),
            }
            frame = Path(frame_path).read_text(encoding="utf-8")
            title = screen_title(content, name) if name is not None else "show-me"
            self._html(render_page(frame, title, content, boot), extra)

        def _file(self, rel: str, extra: Dict[str, str]) -> None:
            base = screen_dir.resolve()
            try:
                target = (base / rel).resolve()
                target.relative_to(base)
                if target == base or not target.is_file():
                    raise ValueError("not a file inside screens")
                data = target.read_bytes()
            except (ValueError, OSError):
                self._text(404, "not found", extra)
                return
            ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            self._send(200, data, ctype, extra)

    return http.server.ThreadingHTTPServer((bind_host, port), Handler)
