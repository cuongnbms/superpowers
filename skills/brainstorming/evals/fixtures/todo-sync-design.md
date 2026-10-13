# todo sync: design

Date: 2026-10-01
Status: design approved in conversation; written spec awaiting review.

## Goal

One person, two machines (laptop, desktop), occasional offline edits. After `todo sync` on
both machines, both show the same list. Correctness over cleverness; the list stays at a few
hundred items.

## Terms

- **Replica**: any copy of the list: the laptop's `todo.json`, the desktop's, and the server's
  `server_todo.json`.
- **Sync**: one bidirectional exchange between a replica and the server.

## Data

Items become `{id, text, done, updated_at, deleted}`.

- `updated_at`: ISO-8601 UTC string, set on every mutation.
- `deleted`: `true` for a tombstone. The server drops tombstones older than 30 days.

## Protocol

`POST /sync` with body `{"items": [...]}`, the replica's full list. The server merges and
returns `{"items": [...]}`, the merged list, which replaces the local file.

Merge rule, per `id`: the item with the greater `updated_at` wins; on a tie the server's copy
wins. A tombstone is an item like any other, so a delete wins over an older live copy.

## Components

- `server.py`: stdlib `http.server`, one handler for `POST /sync`, state in
  `server_todo.json`, started with `python server.py --port 8787`. About 60 lines.
- `todo.py`:
  - new `sync` subcommand; the server URL comes from `TODO_SYNC_URL`.
  - `add`, `done`, and `rm` set `updated_at`; `rm` now writes a tombstone instead of removing
    the item.
- A shared `merge(local, remote)` function in `todo.py`, imported by `server.py`.

## Error handling

- Connection failure: print one line, exit 2, local file untouched.
- Non-200 response: print the status and body, exit 2, local file untouched.
- Malformed response (not a JSON object with an `items` list): reject it, keep the local file.

No authentication in v1; the server binds to a LAN address the user controls.

## Testing

- Unit tests for `merge`: newer wins, tie keeps the server's copy, tombstone beats an older live
  item, tombstone expiry.
- An integration test that runs the server in a thread and syncs two temporary replicas through
  it, asserting they converge.
- Existing tests unchanged apart from the new `updated_at` field in fixtures.

## Non-goals

Multi-user, authentication, conflict prompts, an operation log.
