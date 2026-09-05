# Notes CLI: Tags Design

## Goal

Let a note carry hashtags written inline in its text, and let the CLI list
notes by tag.

## Behavior

- A tag is a `#` followed by one or more letters, digits, or underscores,
  delimited by whitespace or punctuation. `#Go`, `#go` and `#GO` are the same
  tag: tags are stored lowercase.
- A note carries at most 5 tags. Duplicates within one note count once.
- `notes list --tag TAG` prints only notes carrying that tag, newest first,
  in the same one-line format `list` already uses. Matching is
  case-insensitive on the command-line argument (`--tag Go` finds `#go`).
- A note with no tags is unchanged in every existing output.

## Constraints

- Python 3.11 or newer; standard library only at runtime.
- Tests use pytest. No test may read the clock or sleep.
- The one-line `list` format (`<id>\t<text>`) does not change.

## Non-goals

Editing tags after creation. Tag autocomplete. Persistence beyond the
in-memory store.
