#!/usr/bin/env bash
# Materialize the finishing case as a real git repo: copy the todo-cli fixture,
# commit it on main, and plant an epic whose feature A is ready to integrate.
#
#   epic-a  the epic is committed on main and pushed to a bare origin
#           ($DEST.origin.git). feat/a holds feature A's spec (with its Epic:
#           header), its plan, and the finished slice: three commits ahead of
#           main, tests green. Feature B has no spec anywhere. HEAD ends on
#           feat/a.
#
# Usage: setup-case.sh epic-a DEST_DIR
set -euo pipefail

usage="usage: setup-case.sh epic-a DEST_DIR"
case_name=${1:?$usage}
dest=${2:?$usage}
case "$case_name" in
  epic-a) ;;
  *) echo "$usage" >&2; exit 2 ;;
esac
here="$(cd "$(dirname "$0")" && pwd)"
epic="docs/superpowers/epics/2026-10-01-todo-everywhere.md"

mkdir -p "$dest"
dest=$(cd "$dest" && pwd -P)
cp -R "$here/fixtures/todo-cli/." "$dest/"
cd "$dest"
git init -q -b main .
git_id=(-c user.email=eval@example.com -c user.name=eval -c commit.gpgsign=false)
git add -A && git "${git_id[@]}" commit -qm "chore: todo-cli baseline"

# --- the epic, committed on main and pushed ---
mkdir -p docs/superpowers/epics docs/superpowers/specs docs/superpowers/plans
cp "$here/../../brainstorming/evals/fixtures/epic-todo-everywhere.md" "$epic"
git add -A && git "${git_id[@]}" commit -qm "docs: epic todo everywhere"
git init -q --bare -b main "$dest.origin.git"
git remote add origin "$dest.origin.git"
git push -q -u origin main

# --- feature A on feat/a: spec, plan, then the slice ---
git checkout -q -b feat/a
cat > docs/superpowers/specs/2026-10-02-sync-design.md <<EOF2
# Sync — Design

> **Epic:** $epic § A

Goal: keep todo-cli lists in step between the laptop and the desktop.
A small stdlib HTTP server merges full lists posted by \`todo sync\`.
Ids become UUID4 strings so offline adds stop colliding.
EOF2
git add -A && git "${git_id[@]}" commit -qm "docs: sync design"
cat > docs/superpowers/plans/2026-10-02-sync.md <<'EOF2'
# Sync Implementation Plan

**Spec:** docs/superpowers/specs/2026-10-02-sync-design.md

### Task 1: Stamp items with updated_at

`cmd_add` stores `updated_at` on every new item, so the sync server can
merge by recency. Test: `test_add_sets_updated_at`.
EOF2
git add -A && git "${git_id[@]}" commit -qm "docs: sync plan"

python3 - <<'EOF2'
p = "todo.py"
s = open(p).read()
old_import = "import sys\n"
new_import = "import sys\nfrom datetime import datetime, timezone\n"
old_add = '    items.append({"id": len(items) + 1, "text": args.text, "done": False})\n'
new_add = ('    items.append({"id": len(items) + 1, "text": args.text, "done": False,\n'
           '                  "updated_at": datetime.now(timezone.utc).isoformat()})\n')
assert s.count(old_import) == 1 and s.count(old_add) == 1
open(p, "w").write(s.replace(old_import, new_import).replace(old_add, new_add))

p = "test_todo.py"
s = open(p).read()
old = '\n\nif __name__ == "__main__":\n'
new = ('\n    def test_add_sets_updated_at(self):\n'
       '        self.run_cli("add", "milk")\n'
       '        items = json.loads(todo.STORE.read_text())\n'
       '        self.assertIn("updated_at", items[0])\n'
       '\n\nif __name__ == "__main__":\n')
assert s.count(old) == 1
open(p, "w").write(s.replace(old, new))
EOF2
git add -A && git "${git_id[@]}" commit -qm "feat: stamp items with updated_at"
