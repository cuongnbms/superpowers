#!/usr/bin/env bash
# Materialize one eval case as a real git repo: copy the notes-cli fixture,
# put it on a feature branch, and plant the ledger state the case needs.
#
#   fresh    plan only — no ledger; pre-flight must find the Task 1/Task 2
#            name mismatch (parse_tags vs extract_tags) and rule on it
#   resume   Task 1 done and ledgered; a stray flat ledger for another plan
#            sits at .superpowers/sdd/progress.md — next dispatch is Task 2
#   midloop  Task 2 has been through fix rounds 1-3 with one finding still
#            open — next dispatch is fix round 4 (fresh implementer, higher tier)
#
# Usage: setup-case.sh fresh|resume|midloop DEST_DIR
set -euo pipefail

case_name=${1:?usage: setup-case.sh fresh|resume|midloop DEST_DIR}
dest=${2:?usage: setup-case.sh fresh|resume|midloop DEST_DIR}
here="$(cd "$(dirname "$0")" && pwd)"
plan="docs/superpowers/plans/2026-09-05-notes-tags.md"
ws=".superpowers/sdd/2026-09-05-notes-tags"

mkdir -p "$dest"
cp -R "$here/fixtures/notes-cli/." "$dest/"
cd "$dest"
git init -q -b main .
git_id=(-c user.email=eval@example.com -c user.name=eval -c commit.gpgsign=false)
git add -A && git "${git_id[@]}" commit -qm "chore: notes-cli baseline"
git checkout -q -b feature/notes-tags

[ "$case_name" = fresh ] && exit 0

# --- Task 1 really implemented, two commits (tests, then code) ---
cat > tests/test_tags.py <<'EOF'
from notes.tags import parse_tags


def test_extracts_tags_lowercase():
    assert parse_tags("Ship the #Go build and #Docs") == ["go", "docs"]


def test_ignores_bare_hash_and_punctuation():
    assert parse_tags("price is # 5, see #v2.") == ["v2"]


def test_dedupes_preserving_first_occurrence():
    assert parse_tags("#a #b #A #b") == ["a", "b"]


def test_returns_empty_for_no_tags():
    assert parse_tags("nothing here") == []
EOF
git add tests/test_tags.py && git "${git_id[@]}" commit -qm "test: parse_tags cases"
cat > notes/tags.py <<'EOF'
import re

_TAG = re.compile(r"(?<![\w#])#([A-Za-z0-9_]+)")
MAX_TAGS = 5


def parse_tags(text: str) -> list[str]:
    """Return the distinct lowercase tags in text, first occurrence first, at most MAX_TAGS."""
    seen: list[str] = []
    for match in _TAG.finditer(text):
        tag = match.group(1).lower()
        if tag not in seen:
            seen.append(tag)
    return seen[:MAX_TAGS]
EOF
git add notes/tags.py && git "${git_id[@]}" commit -qm "feat: parse inline #tags from note text"
t1_base=$(git rev-parse --short HEAD~2)
t1_head=$(git rev-parse --short HEAD)

mkdir -p "$ws" .superpowers/sdd
printf '*\n' > .superpowers/sdd/.gitignore

# stray flat ledger from another plan (old layout) — must be left alone
cat > .superpowers/sdd/progress.md <<'EOF'
# SDD ledger — plan: docs/superpowers/plans/2026-08-01-search.md
Task 1: complete (commits 1a2b3c4..5d6e7f8, review clean)
Task 2: complete (commits 5d6e7f8..9a8b7c6, review clean)
EOF

cat > "$ws/task-1-report.md" <<EOF
# Task 1 report

Implemented parse_tags in notes/tags.py with tests in tests/test_tags.py.
Tests: python -m pytest tests/test_tags.py -q -> 4 passed.
TDD: RED ImportError before implementation; GREEN 4 passed after.
Commits: $t1_base..$t1_head
EOF

cat > "$ws/progress.md" <<EOF
# SDD ledger — plan: $plan

## Pre-flight scan
| pair | produces | consumes | finding |
|------|----------|----------|---------|
| Task 1 / Task 2 | parse_tags (notes/tags.py) | extract_tags | name mismatch |
| Task 2 / Task 3 | NoteStore.list_by_tag | NoteStore.list_by_tag | agree |
| Task 1 | tests vs code agree | | clean |
| Task 2 | tests vs code agree | | clean |
| Task 3 | tests vs code agree | | clean |
Ruling: Task 2 imports parse_tags, not extract_tags — Task 1 defines parse_tags and the spec names no function — costs a one-word rename in Task 2 if wrong.

Task 1: complete (commits $t1_base..$t1_head, review clean)
EOF

[ "$case_name" = resume ] && exit 0

# --- Task 2 implemented with a defect that three fix rounds failed to clear ---
cat > notes/store.py <<'EOF'
from dataclasses import dataclass, field

from notes.tags import parse_tags


@dataclass
class Note:
    id: int
    text: str
    tags: list[str] = field(default_factory=list)


class NoteStore:
    def __init__(self) -> None:
        self._notes: list[Note] = []

    def add(self, text: str) -> Note:
        note = Note(id=len(self._notes) + 1, text=text, tags=parse_tags(text))
        self._notes.append(note)
        return note

    def list(self) -> list[Note]:
        return list(self._notes)

    def list_by_tag(self, tag: str) -> list[Note]:
        wanted = tag.lower()
        return [n for n in self._notes if wanted in n.tags]
EOF
cat >> tests/test_store.py <<'EOF'


def test_add_records_tags():
    store = NoteStore()
    note = store.add("Fix the #Build on #ci")
    assert note.tags == ["build", "ci"]


def test_list_by_tag_unknown_is_empty():
    store = NoteStore()
    store.add("#go one")
    assert store.list_by_tag("rust") == []
EOF
git add -A && git "${git_id[@]}" commit -qm "feat: record note tags and list notes by tag"
t2_base=$t1_head
t2_impl=$(git rev-parse --short HEAD)

fix_sha=()
for r in 1 2 3; do
  printf '\n# fix round %s: touched ordering comment\n' "$r" >> notes/store.py
  git add -A && git "${git_id[@]}" commit -qm "fix: list_by_tag ordering attempt $r"
  fix_sha+=("$(git rev-parse --short HEAD)")
done

# brief as a prior session would have written it (task text)
"$here/../scripts/task-brief" "$plan" 2 "$ws/task-2-brief.md" >/dev/null 2>&1 || true

cat > "$ws/task-2-report.md" <<EOF
# Task 2 report

Implemented Note.tags and NoteStore.list_by_tag in notes/store.py; tests appended to tests/test_store.py.
Ruling from controller applied: import parse_tags (not extract_tags).
Tests: python -m pytest -q -> 8 passed.
Commits: $t2_base..$t2_impl

## Fix round 1
Finding: list_by_tag returns oldest first; brief requires newest first.
Changed: reviewed the loop, added ordering comment. Tests: python -m pytest tests/test_store.py -q -> 4 passed.

## Fix round 2
Finding: still open. Changed: revisited comment; believe insertion order is what the store already guarantees. Tests: 4 passed.

## Fix round 3
Finding: still open. Changed: added note explaining ordering. Tests: 4 passed.
EOF

cat >> "$ws/progress.md" <<EOF
Task 2: dispatched (implementer model: cheapest tier / haiku; base $t2_base; brief $ws/task-2-brief.md; report $ws/task-2-report.md)
Task 2: fix round 1/5 (0 addressed, 1 open — list_by_tag returns oldest first, brief and spec require newest first (notes/store.py:24); commits $t2_impl..${fix_sha[0]})
Task 2: fix round 2/5 (0 addressed, 1 open — list_by_tag ordering unchanged (notes/store.py:24); commits ${fix_sha[0]}..${fix_sha[1]})
Task 2: fix round 3/5 (0 addressed, 1 open — list_by_tag ordering unchanged (notes/store.py:24); commits ${fix_sha[1]}..${fix_sha[2]})
EOF
