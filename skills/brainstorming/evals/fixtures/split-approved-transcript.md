# Conversation so far (brainstorming session in progress)

**User:** I want the todo-cli in this repo to work everywhere: sync between my laptop and my desktop, share a list with my family, and tick items off from my phone. Let's build it.

**Assistant:** This is architectural: it adds a server, a protocol, sharing, and a web page, so I'll go the full route. I've read `todo.py`, `test_todo.py`, and the README: one `todo.json` beside the script, items have `id`, `text`, `done`, and ids are `len(items) + 1`, so two machines adding offline would produce the same id. There is no GLOSSARY.md. The repo is on `main` with a clean tree.

Before anything else: who uses this besides you, and what does "done" look like for you?

**User:** Me, my partner, and our two kids. Done is: we each tick things off the shared groceries list from our phones, and I still use the CLI on my laptop and desktop. Everything self-hosted on the home server, no third-party packages.

**Assistant:** That is three features, each needing its own spec, plan, and branch:

- **A. Sync**: `server.py` on the home server, `todo sync` on each machine, UUID ids so offline adds stop colliding. B and C build on it.
- **B. Sharing**: named lists, `todo share <list> <person>`. Depends on A.
- **C. Phone web page**: one page served by the sync server to list and tick items. Depends on A.

Shared by all three: stdlib only, one self-hosted server, ids become UUID4 strings in A. Questions I'd leave for each feature's own brainstorm: for A, the conflict rule when two machines edit the same item offline; for B, share by link token or per-person account, and whether a shared list is read-only for the others; for C, served from `server.py` or a separate static file, and how the page authenticates on the LAN.

If this split looks right I'll commit it as an epic at `docs/superpowers/epics/2026-10-09-todo-everywhere.md` on `main` and start brainstorming A.

**User:** Agreed, start with A.
