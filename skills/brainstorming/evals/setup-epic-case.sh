#!/usr/bin/env bash
# Materialize one eval case as a real git repo: copy the todo-cli fixture,
# commit it on main, and plant the epic state the case needs.
#
#   split     baseline only: one commit on main, clean tree. The request has
#             not been split yet, or the split was just approved and nothing
#             is written down.
#   continue  the epic is committed on main. Feature A has a spec on feat/a
#             that is merged into main (feat/a is kept). Feature B has a spec
#             on feat/b, cut from main, unmerged. Feature C has no spec. HEAD
#             ends on main.
#
# Usage: setup-epic-case.sh split|continue DEST_DIR
set -euo pipefail

usage="usage: setup-epic-case.sh split|continue DEST_DIR"
case_name=${1:?$usage}
dest=${2:?$usage}
case "$case_name" in
  split|continue) ;;
  *) echo "$usage" >&2; exit 2 ;;
esac
here="$(cd "$(dirname "$0")" && pwd)"
epic="docs/superpowers/epics/2026-10-01-todo-everywhere.md"

mkdir -p "$dest"
cp -R "$here/fixtures/todo-cli/." "$dest/"
cd "$dest"
git init -q -b main .
git_id=(-c user.email=eval@example.com -c user.name=eval -c commit.gpgsign=false)
git add -A && git "${git_id[@]}" commit -qm "chore: todo-cli baseline"

[ "$case_name" = split ] && exit 0

# --- the epic, committed on main ---
mkdir -p docs/superpowers/epics docs/superpowers/specs
cp "$here/fixtures/epic-todo-everywhere.md" "$epic"
git add -A && git "${git_id[@]}" commit -qm "docs: epic todo everywhere"

# --- feature A: spec on feat/a, merged into main, branch kept ---
git checkout -q -b feat/a
cat > docs/superpowers/specs/2026-10-02-sync-design.md <<EOF2
# Sync — Design

> **Epic:** $epic § A

Goal: keep todo-cli lists in step between the laptop and the desktop.
A small stdlib HTTP server merges full lists posted by \`todo sync\`.
Ids become UUID4 strings so offline adds stop colliding.
EOF2
git add -A && git "${git_id[@]}" commit -qm "docs: sync design"
git checkout -q main
git "${git_id[@]}" merge --no-ff -q feat/a -m "Merge feat/a"

# --- feature B: spec on feat/b, cut from main, unmerged ---
git checkout -q -b feat/b main
cat > docs/superpowers/specs/2026-10-05-sharing-design.md <<EOF2
# Sharing — Design

> **Epic:** $epic § B

Goal: let a named list be shared with another person.
\`todo share <list> <person>\` grants access through the sync server.
Builds on the UUID ids and the server from feature A.
EOF2
git add -A && git "${git_id[@]}" commit -qm "docs: sharing design"
git checkout -q main
