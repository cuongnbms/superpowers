# Epic format

Read this when splitting a request into features or continuing an epic.

An epic is a file recording how one request was split into features: the findings and shared
decisions behind the split, and the features in build order with their scope and deferred
questions. It holds no dates, estimates, or status.

Path: `docs/superpowers/epics/YYYY-MM-DD-<topic>.md` (your human partner's preferred location
overrides it, as for specs).

## Template

```markdown
# Epic: <topic>

> Source: <the request, or the documents read and the commit they were read at>.
> Split on YYYY-MM-DD and approved.

## Findings
<what exploration found that shapes more than one feature: already done / missing / blocked /
conflicts / not ported; a compact table is fine>

## Shared decisions
<decisions made while splitting that bind more than one feature, including where an item was
placed and why>

## Features

### A. <name>
Scope: <bullets>
Depends on: <letters, or —>
Decide when brainstormed: <conflicts and questions deferred to this feature>

### B. <name>
...
```

## Rules

- No dates, estimates, owners, story points, or status column. State comes from git, so a
  status written here would only go stale.
- Letters are stable, because specs and Non-goals refer to features by letter. A new feature
  takes the next unused letter. A feature that is dropped or folded into another keeps its
  letter, with one line saying so and why.
- Findings are facts the features share, not a plan. Each feature's design happens in its own
  brainstorm.

## Deriving state

Each feature's spec carries `> **Epic:** <epic path> § <letter>` under its title. Search every
local and remote branch for those headers:

```bash
EPIC=<epic path>
git grep -n "Epic:.*$(basename "$EPIC")" $(git for-each-ref --format='%(refname:short)' refs/heads refs/remotes) -- '*.md'
```

Per feature letter, against the branch that carries the epic (the current branch in
brainstorming):

- `not started`: no spec on any branch names it.
- `on <branch>`: a spec names it only on unmerged branches; list them.
- `on <base>`: a spec naming it is on the base branch. The base wins over the same letter on
  any other branch, because a branch that still exists after its merge says nothing about
  where the feature is.

Under a "stay on main" workspace the spec reaches the base before the code does, so report
`spec on <base>`, not done.

The next feature is the first `not started` one in epic order. When a letter in its
`Depends on` is not on the base yet, say so alongside it.

## Editing during a later feature

When designing B moves an item to C, or splits B, commit the epic edit with B's spec, on B's
branch. It reaches the base when B merges. A feature session never writes the epic on the
base directly, since the base may be moving under other features.
