# Epic: todo everywhere

> Source: the request "sync todo-cli between my laptop and desktop, share a list with my
> family, and tick items off from my phone", read against `main` at the baseline commit.
> Split on 2026-10-01 and approved.

## Findings

| Area | State |
|---|---|
| Storage | one `todo.json` beside the script; no list name, no owner |
| Ids | `len(items) + 1`: two machines adding offline produce the same id |
| Network | none |
| Tests | `test_todo.py`, two cases |

## Shared decisions

- Stdlib only, on the client and the server: no third-party packages.
- Ids become UUID4 strings in A; B and C rely on that.
- One self-hosted server serves every feature.

## Features

### A. Sync
Scope:
- `server.py` (stdlib `http.server`), `POST /sync` merging full lists
- `todo sync`, reading `TODO_SYNC_URL`
- UUID ids, `updated_at` on every mutation, tombstones for deletes
Depends on: —
Decide when brainstormed: the conflict rule when two machines edit the same item offline (last write wins, or keep both and flag)

### B. Sharing
Scope:
- named lists; a list can be shared with another person
- `todo share <list> <person>`
Depends on: A
Decide when brainstormed: share by link token or by per-person account; whether a shared list is read-only for the other person

### C. Phone web page
Scope:
- one HTML page served by the sync server: list items, tick them done
Depends on: A
Decide when brainstormed: served from `server.py` or as a separate static file; how the page authenticates on the LAN
