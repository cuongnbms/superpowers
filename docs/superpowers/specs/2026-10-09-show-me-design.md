# show-me: Draw It in a Browser Tab When Asked — Design

Date: 2026-10-09
Status: approved by the user (in-session, four sections)
Branch: `dev` (the user chose to stay on `dev`)

## Problem

Fork v6.4.24 removed brainstorming's visual companion (commit `131bf23`): the
section in `skills/brainstorming/SKILL.md`, `visual-companion.md`,
`skills/brainstorming/scripts/` (a 723-line Node server with WebSocket click
events, session key, owner-PID checks, Windows/Gemini/Copilot branches), and
`tests/brainstorm-server/`. The user removed it for one reason: it was tied to
brainstorming. The mechanism itself was fine.

The need is still there. Some things are hard to picture from chat: a screen
layout, how services talk, what a data structure looks like, which functions a
request passes through. The user wants to say "vẽ ra cho tôi xem" at any point
in any task and get a page in the browser.

## Goal

A standalone skill, `show-me`, that the agent loads only when the user asks to
see something. It starts (or reuses) a small local server, writes one HTML
fragment per screen, and gives the user a URL. The tab the user keeps open
switches to each new screen by itself. Feedback stays in the terminal.

Success: the evals under Testing pass on the new skill, the no-skill baseline
fails cases 1 and 2 (no browser page), and the server tests pass on both the
Mac and devtuf.

## Decisions

Settled with the user in this session:

1. **Standalone, user-invoked only.** The agent never offers it. Natural
   requests ("vẽ ra cho tôi xem", "show me", "mock it up") must still load it,
   so `disable-model-invocation` is not set; the description is written narrow
   instead. Brainstorming is not edited and does not mention it.
2. **One request spans its revisions.** The user asks for a picture, the agent
   pushes a screen; feedback such as "make the sidebar wider" produces a `-v2`
   of the same request. Later questions, even visual ones, are answered in the
   terminal unless the user asks to see something again. The server keeps
   running between requests.
3. **View only.** No click/selection events back to the agent. The user replies
   in the terminal. This removes WebSocket, the events file, and the client
   helper from the old design.
4. **Mac and devtuf.** The agent runs on either. On devtuf (LAN
   `192.168.1.89`) the user opens the URL from the Mac browser. Agents in Herdr
   panes on devtuf carry `SSH_CONNECTION=<client> <port> 192.168.1.89 22`
   (verified on running `claude` processes); its third field is the address the
   Mac reaches.
5. **Python 3 standard library server.** `/usr/bin/python3` is on devtuf's
   non-interactive PATH; `node` is only there through mise in interactive
   shells. This departs from upstream's Node server on purpose.
6. **Access key on.** A random key in the URL, remembered in a cookie, because
   on devtuf the server listens on the LAN and screens can show project code.
7. **Look C, "workbench".** Chosen from three directions on a sample page
   (`2026-10-09-show-me-looks.html` next to this spec; open it with
   `?look=workbench`). Screens are editor-like tabs, a status bar shows live
   state, code traces step like a debugger. The user asked for a polished
   template; the sample is the floor, not the target.
8. **Name `show-me`**, chosen by the user over gerund forms.
9. **Mermaid and highlight.js from a CDN**, pinned versions. The Mac browser
   has internet; vendoring Mermaid (~2.5 MB) would bloat the plugin and the
   Codex sync.

No glossary term or ADR: "screen" is vocabulary internal to the skill, and the
Python-over-Node choice is a rewrite of about 150 lines to reverse, so it fails
the hard-to-reverse test. The upstream departure is recorded in RELEASE-NOTES.

## Design

### Skill surface

`skills/show-me/SKILL.md` frontmatter:

```yaml
name: show-me
description: Shows what is hard to picture in chat (UI mockups and layouts, architecture and flow diagrams, data structures, how code runs) as pages in a browser tab that refreshes itself. Use only when the user asks to see something drawn or mocked up ("vẽ ra cho tôi xem", "show me", "mock it up"); do not offer it on your own.
```

The description must also keep it apart from `excalidraw-diagram` and
`drawio-diagram` (user-level skills that produce diagram files): show-me is for
looking at something during the conversation, not for a file to keep. Final
wording is tuned during evals.

Body (short; the component catalog lives in a reference file; the fork's voice,
"your human partner", as in the other skills):

1. **Start or reuse the server**: `python3 <skill-dir>/scripts/server.py start`.
   Read `url` and `screen_dir` from its JSON. Codex: add `--foreground` and run
   it with the harness's background mechanism (Codex reaps detached
   processes).
2. **Pick the form for the content**:
   - flows, architecture, sequences, state machines, ERDs, git history:
     Mermaid in a `diagram` block;
   - screens and layouts: the mock kit, side by side in `compare` when there
     are options;
   - data shapes, config files, directory trees: `tree`;
   - how code runs: `trace` (steps with file:line and the code), or a Mermaid
     sequence diagram when it crosses services.
   Read `references/components.md` the first time a conversation writes a
   screen.
3. **Write the screen** with the file tool to `<screen_dir>/<semantic-name>.html`:
   a fragment by default; a full document (starts with `<!doctype` or `<html`)
   only when the frame gets in the way. Never reuse a name; revisions are
   `-v2`, `-v3`.
4. **Reply and stop**: the full URL including `?key=` every time, plus one or
   two sentences on what the screen shows. End the turn; feedback comes in the
   terminal.

Out of the body on purpose: the old "continuing in terminal" waiting screen
(every screen here is one the user asked for, so leaving it up is right), and
stopping the server (the idle timeout handles it).

### Server: `skills/show-me/scripts/server.py`

Standard library only, Python 3.8+ (devtuf has 3.12, the Mac 3.14).

**Commands**

```
python3 server.py start [--project-dir DIR] [--host H] [--url-host H]
                        [--port N] [--idle-minutes N] [--foreground]
python3 server.py status [--project-dir DIR]
python3 server.py stop   [--project-dir DIR]
```

`start` prints one JSON line:
`{"url", "screen_dir", "session_dir", "port", "pid", "reused"}`. `status`
prints the same JSON and exits 0 when running, exits 1 otherwise. `stop` kills
the server and exits 0 whether or not it was running.

**Session directory.** `--project-dir` defaults to the git toplevel of the
current directory; outside a repository, `$TMPDIR/show-me-<hash of cwd>`. The
session lives in `<project-dir>/.superpowers/show-me/`:

- `screens/`: what the agent writes;
- `server.json`: `pid`, `port`, `host`, `url`, `key`, `started_at`;
- `server.log`: daemon output;
- `.gitignore` containing `*`, written on first start, so the project's own
  `.gitignore` is never touched.

One server per checkout or worktree. Two agents in one checkout share it; the
newest screen wins.

**Start is idempotent.** If `server.json` names a live pid and
`/api/screens` answers with the stored key, print it with `reused: true`.
Otherwise start a new server, reusing the stored `port` and `key` so an open tab
(holding the old cookie) reconnects without a new URL. If the stored port is
taken by another process, pick a free one and print the new URL. Default mode
daemonizes (fork, `setsid`, output to `server.log`); the parent waits until the
server answers, then prints the JSON. `--foreground` serves in-process and
prints the JSON as soon as it listens.

**Host and URL.** With `SSH_CONNECTION` set: bind `0.0.0.0`, URL host = its
third field. Without: bind `127.0.0.1`, URL host `localhost`. `--host` and
`--url-host` override.

**Key.** 32 hex characters, generated once per session directory and kept
across restarts. A request passes when `?key=` matches or the cookie
`show_me_key_<port>` matches (compared with `hmac.compare_digest`). A query key
sets that cookie (`HttpOnly; SameSite=Strict; Path=/`). The port is in the
cookie name because cookies are per host, not per port: two projects' servers
on one machine would otherwise overwrite each other's cookie. Anything else
gets 403.

**Routes**

| Route | Returns |
|-------|---------|
| `/` | newest screen, wrapped in the frame (empty state when there are none) |
| `/s/<name>` | that screen, wrapped |
| `/api/screens` | `{"screens": [{"name", "mtime"}], "newest": name or null}`, sorted by mtime, hidden files and non-`.html` skipped |
| `/files/<path>` | static file under `screens/` (path traversal rejected) |

A fragment is wrapped in the frame. A full document is served as is, with the
poll script injected before `</body>`; it gets live switching but no tab bar or
status bar.

**Idle timeout.** The server exits after `--idle-minutes` (default 240) with no
new screen; the clock starts at the later of server start and the newest
screen's mtime. `server.json` stays, so the next start reuses port and key.
Polls from an open tab do not count as activity.

Dropped from the old server: WebSocket, the events file, owner-PID checks, and
the Windows, Gemini and Copilot launch branches.

### Frame: `skills/show-me/scripts/frame.html`

The server fills placeholders: the fragment, the screen name, the document
title (first `<h1>` text, else the file name), and an initial JSON blob
(`screens`, `project`, `host:port`) so the tab bar renders before the first
poll.

**Look C tokens** (start here; refine during implementation):

| Token | Light | Dark |
|-------|-------|------|
| `--bg` | `#E9ECF0` | `#1B1E23` |
| `--surface` | `#FFFFFF` | `#23272E` |
| `--node` | `#FFFFFF` | `#2A2F37` |
| `--ink` | `#1D232B` | `#D8DDE5` |
| `--ink-soft` | `#5E6772` | `#8B94A2` |
| `--line` | `#4A525E` | `#AAB3C0` |
| `--rule` | `#D3D8DE` | `#343A44` |
| `--accent` (amber, the "current" color) | `#A35F00` | `#F0B54A` |
| `--accent-2` | `#2C6BD3` | `#71A5F7` |
| `--ok` | `#2E7D4F` | `#8FD19E` |
| `--mark` | `rgba(240,181,74,.24)` | `rgba(240,181,74,.15)` |
| `--code-bg` | `#F6F7F9` | `#1E2228` |
| `--chrome` | `#DCE0E6` | `#16191D` |

Type: Geist and Geist Mono from Google Fonts, system fallbacks. Light/dark
follows `prefers-color-scheme`, with a toggle in the status bar remembered in
`localStorage` (wrapped in try/catch).

**Chrome**

- Tab bar: one tab per screen, file name as label, current one marked with an
  amber top edge; scrolls horizontally when long. Clicking a tab opens
  `/s/<name>`.
- Status bar (sticky bottom): live dot, `host:port`, screen count, project
  name, theme toggle.
- When `/api/screens` reports a newest screen other than the newest one known
  at page load, the tab goes to `/` (the newest), whichever screen it was
  showing. The comparison is against the newest at load, not the displayed
  screen, so viewing an older tab does not bounce straight back.
- When a poll fails: the live dot turns red, a banner says the server stopped
  and that the tab reconnects when the agent starts it again; polling backs off
  from 1 s to 5 s and reloads when the server answers.
- Empty state on `/` with no screens: one line saying the agent's first screen
  will appear here.

Chrome text is English and minimal; screen content is in whatever language the
agent writes.

**Rendering**

- `pre.mermaid` blocks: Mermaid 11 (pinned ESM build from jsdelivr), `theme:
  'base'` with `themeVariables` read from the CSS tokens, re-rendered on theme
  toggle. A node with `class X accent` gets the amber stroke. On load or render
  failure the block shows its source instead of nothing.
- `pre > code.language-*`: highlight.js 11 (pinned, cdnjs), token colors mapped
  to the frame tokens.
- `trace`: frame JS adds line numbers from `data-start`, highlights
  `data-hl`, shows `data-why` above the code, and steps with buttons and the
  arrow keys.

**Components** (catalog with snippets in `references/components.md`; markup as
on the sample page): `diagram` (figure with `pre.mermaid` and optional
caption); `compare` and `option` (with `letter`); mock kit (`mock`, `mock-bar`,
`mock-url`, `mock-body`, `mock-nav`, `mock-tabs`, `mock-form`, `field`,
`input`, `toggle`, `btn`, `mock-actions`, `placeholder`); `pin` and `legend`
for annotations; `tree` (`tree-head`, `row` with `k`/`t`/`v`/`n`, and
`data-depth` for nesting so directory and object trees work); `trace`;
`callout`; plain `table`.

Quality floor: responsive to phone width, visible focus, reduced motion
respected, contrast checked in both modes.

### Files

New:

- `skills/show-me/SKILL.md`
- `skills/show-me/references/components.md`
- `skills/show-me/scripts/server.py`
- `skills/show-me/scripts/frame.html`
- `skills/show-me/agents/openai.yaml` (display name and short description for
  Codex, as in `skills/domain-modeling/agents/openai.yaml`)
- `skills/show-me/evals/evals.json` (and fixtures if a case needs one)
- `tests/show-me/test_server.py`
- `docs/superpowers/specs/2026-10-09-show-me-looks.html` (the sample page,
  committed with this spec)

Edited:

- `README.md`: add show-me to the Collaboration list.
- `RELEASE-NOTES.md`: an entry noting the upstream departure (upstream keeps
  the companion inside brainstorming; the fork keeps skipping every upstream
  companion change on sync and has show-me instead).

## Testing

**Server** (`python3 -m unittest discover tests/show-me`, runs on the Mac and
on devtuf):

- `start` twice returns the same server with `reused: true`; after `stop`,
  `start` reuses the stored port and key; `status` exits 1 when stopped.
- No key gives 403; a query key sets `show_me_key_<port>`; the cookie alone
  passes; a wrong key gives 403.
- A fragment comes back inside the frame; a full document comes back as is
  with the poll script injected.
- `/api/screens` orders by mtime, names the newest, skips hidden and
  non-`.html` files; `/` with no screens returns the empty state.
- `/files/../server.json` is rejected.
- With `SSH_CONNECTION="10.0.0.9 5000 10.0.0.5 22"` the URL host is
  `10.0.0.5` and the bind host `0.0.0.0`; without it, `localhost` and
  `127.0.0.1`.
- A tiny `--idle-minutes` (fractional allowed) makes the server exit.
- The session directory holds a `.gitignore` containing `*`.

**Frame**: no automated test. During implementation, screenshot light and dark
at desktop and phone width with all four content types, plus the empty state
and the stopped banner, and fix what looks wrong.

**Skill evals** (superpowers:writing-skills, Opus subagents, all runs in one
final task):

1. "Vẽ ra cho tôi xem luồng X" in a fixture repo: loads show-me, starts the
   server, writes a screen using Mermaid, replies with the full URL and a short
   summary, ends the turn.
2. "Mock up 2 layouts cho trang Y": uses `compare` with the mock kit, a
   fragment rather than a full document.
3. Negative: "Trang settings nên dùng sidebar hay tab?": answered in text;
   show-me is not loaded.
4. Competition: "Vẽ sơ đồ kiến trúc rồi lưu thành file .excalidraw": show-me
   is not loaded.

Plus a no-skill baseline on cases 1 and 2. Trigger claims (cases 3 and 4) are
checked by hand with `claude -p --output-format stream-json`, since the
`run_loop` trigger detector is unreliable in this repo.

## Non-goals

- Click or selection feedback from the browser.
- Any edit to brainstorming, or the agent offering show-me on its own.
- Windows, Gemini CLI and Copilot CLI launch paths.
- Vendored Mermaid or highlight.js, offline rendering.
- More than one look.

## Release

On `dev` with the user's chosen release mechanics (next v6.4.2x), when the
user asks: version bump across the version files, RELEASE-NOTES entry, tag,
fast-forward `main`.
