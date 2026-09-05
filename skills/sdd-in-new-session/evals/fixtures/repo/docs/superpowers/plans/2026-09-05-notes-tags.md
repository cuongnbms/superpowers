# Notes Tags Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Notes carry inline `#tags`; `notes list --tag TAG` filters by tag.

**Architecture:** A pure `parse_tags` function extracts tags from text. `NoteStore` records each note's tags at add time and answers `list_by_tag`. The CLI's `list` subcommand gains a `--tag` option that calls `list_by_tag` and prints with the existing formatter.

**Tech Stack:** Python 3.11, argparse, pytest.

**Spec:** docs/superpowers/specs/2026-09-05-notes-tags-design.md

## Global Constraints

- Python 3.11 or newer; standard library only at runtime (no new dependencies).
- Tags are stored lowercase.
- A note carries at most 5 tags; duplicates within one note count once.
- The one-line `list` output format `<id>\t<text>` does not change.
- Tests use pytest; no test reads the clock or sleeps.

---

## Task Structure

### Task 1: parse_tags

**Files:**
- Create: `notes/tags.py`
- Create: `tests/test_tags.py`

**Interfaces:**
- Produces: `parse_tags(text: str) -> list[str]` in `notes/tags.py`

**Steps:**

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_tags.py
from notes.tags import parse_tags


def test_extracts_tags_lowercase():
    assert parse_tags("Ship the #Go build and #Docs") == ["go", "docs"]


def test_ignores_bare_hash_and_punctuation():
    assert parse_tags("price is # 5, see #v2.") == ["v2"]


def test_dedupes_preserving_first_occurrence():
    assert parse_tags("#a #b #A #b") == ["a", "b"]


def test_returns_empty_for_no_tags():
    assert parse_tags("nothing here") == []
```

- [ ] **Step 2: Run the tests, expect failure**

Run: `python -m pytest tests/test_tags.py -q`
Expected: ImportError (no module `notes.tags`).

- [ ] **Step 3: Implement**

```python
# notes/tags.py
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
```

- [ ] **Step 4: Run the tests, expect success**

Run: `python -m pytest tests/test_tags.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add notes/tags.py tests/test_tags.py
git commit -m "feat: parse inline #tags from note text"
```

### Task 2: Store tags and list by tag

**Files:**
- Modify: `notes/store.py`
- Modify: `tests/test_store.py`

**Interfaces:**
- Consumes: `extract_tags(text: str) -> list[str]` from `notes/tags.py` (Task 1)
- Produces: `Note.tags: list[str]` field; `NoteStore.list_by_tag(tag: str) -> list[Note]`, newest first

**Steps:**

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_store.py`:

```python
def test_add_records_tags():
    store = NoteStore()
    note = store.add("Fix the #Build on #ci")
    assert note.tags == ["build", "ci"]


def test_list_by_tag_newest_first_case_insensitive():
    store = NoteStore()
    first = store.add("#go one")
    store.add("#docs two")
    third = store.add("#Go three")
    assert store.list_by_tag("GO") == [third, first]


def test_list_by_tag_unknown_is_empty():
    store = NoteStore()
    store.add("#go one")
    assert store.list_by_tag("rust") == []
```

- [ ] **Step 2: Run the tests, expect failure**

Run: `python -m pytest tests/test_store.py -q`
Expected: AttributeError on `note.tags` / `list_by_tag`.

- [ ] **Step 3: Implement**

Replace `notes/store.py` with:

```python
from dataclasses import dataclass, field

from notes.tags import extract_tags


@dataclass
class Note:
    id: int
    text: str
    tags: list[str] = field(default_factory=list)


class NoteStore:
    def __init__(self) -> None:
        self._notes: list[Note] = []

    def add(self, text: str) -> Note:
        note = Note(id=len(self._notes) + 1, text=text, tags=extract_tags(text))
        self._notes.append(note)
        return note

    def list(self) -> list[Note]:
        return list(self._notes)

    def list_by_tag(self, tag: str) -> list[Note]:
        wanted = tag.lower()
        return [n for n in reversed(self._notes) if wanted in n.tags]
```

- [ ] **Step 4: Run the tests, expect success**

Run: `python -m pytest -q`
Expected: all tests pass (existing store tests plus 3 new, plus Task 1's 4).

- [ ] **Step 5: Commit**

```bash
git add notes/store.py tests/test_store.py
git commit -m "feat: record note tags and list notes by tag"
```

### Task 3: CLI --tag filter

**Files:**
- Modify: `notes/cli.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `NoteStore.list_by_tag(tag: str) -> list[Note]` (Task 2)
- Produces: `notes list --tag TAG` subcommand option

**Steps:**

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cli.py`:

```python
def test_list_with_tag_filters_newest_first(capsys):
    store = NoteStore()
    store.add("#go one")
    store.add("#docs two")
    store.add("#Go three")
    run(["list", "--tag", "go"], store)
    assert capsys.readouterr().out == "3\t#Go three\n1\t#go one\n"


def test_list_without_tag_is_unchanged(capsys):
    store = NoteStore()
    store.add("#go one")
    run(["list"], store)
    assert capsys.readouterr().out == "1\t#go one\n"
```

- [ ] **Step 2: Run the tests, expect failure**

Run: `python -m pytest tests/test_cli.py -q`
Expected: argparse error `unrecognized arguments: --tag`.

- [ ] **Step 3: Implement**

In `notes/cli.py`, add the option to the `list` subparser and route it:

```python
    list_parser = sub.add_parser("list")
    list_parser.add_argument("--tag", default=None)
```

and in `run`, replace the `list` branch with:

```python
    if args.command == "list":
        notes = store.list_by_tag(args.tag) if args.tag else store.list()
        for note in notes:
            print(format_line(note))
        return 0
```

- [ ] **Step 4: Run the tests, expect success**

Run: `python -m pytest -q`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add notes/cli.py tests/test_cli.py
git commit -m "feat: notes list --tag filter"
```
