#!/usr/bin/env bash
# Materialize the spec-review case as a real git repo: the todo-cli fixture committed on main,
# then branch todo-sync carrying the committed todo sync spec (the state right after
# architectural step 7).
#
# Usage: setup-spec-review-case.sh DEST_DIR
set -euo pipefail

dest=${1:?usage: setup-spec-review-case.sh DEST_DIR}
here="$(cd "$(dirname "$0")" && pwd)"
spec="docs/superpowers/specs/2026-10-01-todo-sync-design.md"

mkdir -p "$dest"
cp -R "$here/fixtures/todo-cli/." "$dest/"
cd "$dest"
git init -q -b main .
git_id=(-c user.email=eval@example.com -c user.name=eval -c commit.gpgsign=false)
git add -A && git "${git_id[@]}" commit -qm "chore: todo-cli baseline"
git switch -q -c todo-sync
mkdir -p "$(dirname "$spec")"
cp "$here/fixtures/todo-sync-design.md" "$spec"
git add -A && git "${git_id[@]}" commit -qm "docs(sync): todo sync design"
