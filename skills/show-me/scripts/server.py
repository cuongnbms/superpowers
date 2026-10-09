#!/usr/bin/env python3
"""show-me: serve agent-written HTML screens in a browser tab (standard library only)."""

import argparse
import hashlib
import hmac
import html
import http.server
import json
import mimetypes
import os
import re
import secrets
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.request
from datetime import datetime
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple
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


# --- CLI and server lifecycle -------------------------------------------------

DEFAULT_IDLE_MINUTES = 240.0
_KEY_RE = re.compile(r"^[0-9a-f]{32}$")
_PORT_IN_USE_EXIT = 3


def derive_hosts(env: Mapping[str, str], host: Optional[str], url_host: Optional[str]) -> Tuple[str, str]:
    bind, shown = "127.0.0.1", "localhost"
    fields = env.get("SSH_CONNECTION", "").split()
    if len(fields) >= 3:
        bind, shown = "0.0.0.0", fields[2]
    return host or bind, url_host or shown


def resolve_project_dir(arg: Optional[str], cwd: Path) -> Path:
    if arg:
        return Path(arg).resolve()
    try:
        r = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           universal_newlines=True, timeout=10)
        top = r.stdout.strip()
        if r.returncode == 0 and top:
            return Path(top).resolve()
    except (OSError, subprocess.SubprocessError):
        pass
    digest = hashlib.sha1(str(Path(cwd).resolve()).encode("utf-8")).hexdigest()[:12]
    return (Path(tempfile.gettempdir()) / ("show-me-" + digest)).resolve()


def _session_dir(project_dir: Path) -> Path:
    return project_dir / ".superpowers" / "show-me"


def _read_info(session: Path) -> Optional[Dict[str, Any]]:
    try:
        data = json.loads((session / "server.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _write_info(session: Path, info: Dict[str, Any]) -> None:
    tmp = session / ("server.json.%d.tmp" % os.getpid())
    tmp.write_text(json.dumps(info), encoding="utf-8")
    os.replace(str(tmp), str(session / "server.json"))


def _pid_alive(pid: Any) -> bool:
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _is_live(info: Optional[Dict[str, Any]]) -> bool:
    if not info or not _pid_alive(info.get("pid")):
        return False
    host = info.get("host")
    probe = "127.0.0.1" if host == "0.0.0.0" else host
    if not probe or not isinstance(info.get("port"), int) or not info.get("key"):
        return False
    url = "http://%s:%d/api/screens?key=%s" % (probe, info["port"], info["key"])
    try:
        with urllib.request.urlopen(url, timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


def _report(info: Dict[str, Any], session: Path, reused: bool) -> Dict[str, Any]:
    return {
        "url": info["url"],
        "screen_dir": str(session / "screens"),
        "session_dir": str(session),
        "port": info["port"],
        "pid": info["pid"],
        "reused": reused,
    }


def _fail(message: str) -> int:
    sys.stderr.write("show-me: %s\n" % message)
    return 1


def _log(session: Path, text: str) -> None:
    try:
        with open(str(session / "server.log"), "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (datetime.now().astimezone().isoformat(timespec="seconds"), text))
    except OSError:
        pass


def _serve(args: argparse.Namespace, foreground: bool) -> int:
    project_dir = resolve_project_dir(args.project_dir, Path.cwd())
    session = _session_dir(project_dir)
    screens = session / "screens"
    screens.mkdir(parents=True, exist_ok=True)
    (session / ".gitignore").write_text("*\n", encoding="utf-8")
    prior = _read_info(session) or {}
    key = prior.get("key") if isinstance(prior.get("key"), str) and _KEY_RE.match(prior["key"]) else None
    key = key or secrets.token_hex(16)
    bind_host, url_host = derive_hosts(os.environ, args.host, args.url_host)
    frame = Path(__file__).with_name("frame.html")

    def bind(port: int) -> http.server.ThreadingHTTPServer:
        return make_server(screens, key, bind_host, port, url_host, project_dir.name, frame)

    try:
        if args.port is not None:
            httpd = bind(args.port)
        else:
            stored = prior.get("port")
            httpd = None
            if isinstance(stored, int) and not isinstance(stored, bool) and stored > 0:
                try:
                    httpd = bind(stored)
                except OSError:
                    httpd = None
            if httpd is None:
                httpd = bind(0)
    except OSError as e:
        if args.port is not None:
            sys.stderr.write("show-me: port %d is in use\n" % args.port)
            return 1 if foreground else _PORT_IN_USE_EXIT
        sys.stderr.write("show-me: cannot bind: %s\n" % e)
        return 1

    port = httpd.server_address[1]
    started = time.time()
    me = os.getpid()
    info = {
        "pid": me,
        "port": port,
        "host": bind_host,
        "url": "http://%s:%d/?key=%s" % (url_host, port, key),
        "key": key,
        "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    _write_info(session, info)
    _log(session, "started pid=%d port=%d host=%s" % (me, port, bind_host))
    if foreground:
        print(json.dumps(_report(info, session, False)))
        sys.stdout.flush()

    def stop_async(*_args: Any) -> None:
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop_async)
    idle_seconds = args.idle_minutes * 60.0
    if idle_seconds > 0:
        def watch() -> None:
            interval = min(30.0, max(0.2, idle_seconds / 4))
            while True:
                time.sleep(interval)
                screens_now = list_screens(screens)
                last = max([started] + [s["mtime"] for s in screens_now])
                if time.time() - last >= idle_seconds:
                    _log(session, "idle for %.1f minutes, stopping" % (args.idle_minutes,))
                    httpd.shutdown()
                    return
        threading.Thread(target=watch, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception:
        _log(session, traceback.format_exc())
    finally:
        httpd.server_close()
        current = _read_info(session)
        if current is not None and current.get("pid") == me:
            current["pid"] = None
            _write_info(session, current)
        _log(session, "exited pid=%d" % me)
    return 0


def _cmd_start(args: argparse.Namespace) -> int:
    project_dir = resolve_project_dir(args.project_dir, Path.cwd())
    session = _session_dir(project_dir)
    existing = _read_info(session)
    if _is_live(existing):
        print(json.dumps(_report(existing, session, True)))
        return 0
    if args.foreground:
        return _serve(args, True)
    session.mkdir(parents=True, exist_ok=True)
    log = session / "server.log"
    cmd = [sys.executable, os.path.abspath(__file__), "serve", "--project-dir", str(project_dir),
           "--idle-minutes", repr(args.idle_minutes)]
    for flag, value in (("--host", args.host), ("--url-host", args.url_host), ("--port", args.port)):
        if value is not None:
            cmd += [flag, str(value)]
    with open(str(log), "ab") as out:
        proc = subprocess.Popen(cmd, start_new_session=True, stdin=subprocess.DEVNULL,
                                stdout=out, stderr=out)
    deadline = time.time() + 10
    while time.time() < deadline:
        code = proc.poll()
        if code is not None:
            if code == _PORT_IN_USE_EXIT and args.port is not None:
                return _fail("port %d is in use" % args.port)
            break
        info = _read_info(session)
        if info and info.get("pid") == proc.pid and _is_live(info):
            print(json.dumps(_report(info, session, False)))
            return 0
        time.sleep(0.1)
    if proc.poll() is None:
        try:
            proc.terminate()
        except OSError:
            pass
    return _fail("server did not start, see %s" % log)


def _cmd_status(args: argparse.Namespace) -> int:
    session = _session_dir(resolve_project_dir(args.project_dir, Path.cwd()))
    info = _read_info(session)
    if not _is_live(info):
        return 1
    print(json.dumps(_report(info, session, True)))
    return 0


def _cmd_stop(args: argparse.Namespace) -> int:
    session = _session_dir(resolve_project_dir(args.project_dir, Path.cwd()))
    info = _read_info(session)
    if not _is_live(info):
        return 0
    pid = info["pid"]
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    deadline = time.time() + 5
    while time.time() < deadline and _pid_alive(pid):
        time.sleep(0.05)
    current = _read_info(session)
    if current is not None and current.get("pid") == pid:
        current["pid"] = None
        _write_info(session, current)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="server.py", description="show-me server")
    sub = parser.add_subparsers(dest="command")
    sub.required = True
    for name in ("start", "status", "stop", "serve"):
        p = sub.add_parser(name, help=argparse.SUPPRESS if name == "serve" else None)
        p.add_argument("--project-dir")
        if name in ("start", "serve"):
            p.add_argument("--host")
            p.add_argument("--url-host")
            p.add_argument("--port", type=int)
            p.add_argument("--idle-minutes", type=float, default=DEFAULT_IDLE_MINUTES)
        if name == "start":
            p.add_argument("--foreground", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "start":
        return _cmd_start(args)
    if args.command == "serve":
        return _serve(args, False)
    if args.command == "status":
        return _cmd_status(args)
    return _cmd_stop(args)


if __name__ == "__main__":
    sys.exit(main())
