# Conversation so far (brainstorming session in progress)

**User:** I want the todo-cli in this repo to sync between my laptop and my desktop. I'm thinking a small HTTP server I self-host plus a `todo sync` command. Let's build it.

**Assistant:** This is architectural: it adds a server, a network protocol, and a new command, so I'll go the full route with questions, approaches, and a written spec before any code. I've read `todo.py`, `test_todo.py`, and the README: state is a single `todo.json` next to the script, items have `id`, `text`, `done`; there is no CONTEXT.md in the repo yet. I'll also be sharpening vocabulary as we go so the spec and the code end up using the same words.

First question: when both machines change the same todo while offline, what should happen on sync?
  (a) Last write wins by timestamp
  (b) Keep both and flag a conflict for you to resolve
  (c) Something else

**User:** (a) last write wins is fine, this is just for me.

**Assistant:** Got it. Before the next question I want to pin a term, because the design will hinge on it. You've said "laptop", "desktop", "machine", and "client" for the things that hold a copy of the list. The server holds one too. Do you want one word for "a copy of the todo list that can be edited and synced", and if so which? Options: "replica", "node", "device", or keep "client" and treat the server as special.

**User:** Let's call them replicas. The server is also a replica, just the one they all talk to. And yes, sync means bidirectional in one command, don't split it into push and pull. Consider that settled.
