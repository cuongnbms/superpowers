# Epics: Write the Split Down, Start the Next Feature From a File — Design

Date: 2026-10-09
Status: approved by the user (in-session, three sections)
Branch: `feat/epics` off `dev`

## Problem

A real session on devtuf, `bmx-marine-web`, Claude Code session `70825d09`
("mô tả doc @../bmx-fenew/docs/DEVELOPER-HANDOFF.md"):

- Brainstorming ran a gap analysis and split the handoff into sub-projects
  A–D. The split, the gap table, and "each conflict is asked when we reach the
  sub-project it belongs to" lived only in chat.
- A was designed and planned there, executed in another session (`9df4c968`,
  via sdd-in-new-session), and finished with option 1 (merge locally).
- To start B the user went back to the original session, copied B's
  description, and pasted it into a new session (`1c17328d`).
- Spec A's header carried a one-line "A → B → C → D" summary, on the agent's
  own initiative; the skill does not ask for it. Detail was lost on the way:
  B re-asked "is the Earth preview in B?", and C's scope shrank to "point panel
  and verify additions".

Fork v6.4.23 and upstream v6.4.2 share the same two-sentence rule
(`skills/brainstorming/SKILL.md:149-152`: decompose, then brainstorm the first
sub-project). Nothing writes the split down, and finishing-a-development-branch
ends at cleanup without naming what comes next.

## Goal

When brainstorming splits a request, the split is written once, as an epic, on
the branch the features will branch from. A fresh session handed the epic file
starts the next feature from the epic's scope and deferred questions: no
re-pasted description, no repeated survey. When a feature's branch finishes,
finishing-a-development-branch names the next feature and prints a prompt to
paste into a new session.

Success: the old-vs-new evals below discriminate (new passes, old fails) on
cases 9, 10, 11 and the finishing case, and cases 0, 3, 7, 8 hold on the new
skill.

## Terms

Settled with the user; written to a new root `CONTEXT.md`.

- **Epic**: a file recording how one request was split into features: the
  findings and shared decisions behind the split, and the features in build
  order with their scope and deferred questions. No dates, estimates, or
  status. _Avoid_: roadmap, program, breakdown.
- **Feature**: one unit of work with its own spec, plan, and branch, merged or
  discarded as one; within an epic, one lettered entry. _Avoid_: sub-project,
  story.

## Decisions

1. **The epic is committed on the current branch at the split's approval.**
   That is the branch Isolate later branches each feature from. The approval
   ask for the split names the path and the branch, so one yes covers both. It
   is the only write before Isolate: the epic belongs to no single feature,
   dropping feature A must not drop it, and feature B started before A merges
   must see it. Rejected: committing the epic with feature A's spec on A's
   branch (B cannot see it until A merges; discarding A deletes it).
2. **State is derived from git, never stored.** Each feature's spec carries
   `> **Epic:** <epic path> § <letter>`; a `git grep` over local and remote
   branches tells which features have a spec and where. Rejected: a status
   table edited by brainstorming and finishing (a commit per status change,
   and parallel feature branches conflict on the table when they merge).
3. **Continuation needs the epic path in the request.** Epics are occasional;
   the user passes the file (`@docs/superpowers/epics/...md`, or the prompt
   finishing printed). Brainstorming does not list `docs/superpowers/epics/`.
4. **Agile terms: Epic and Feature** (Azure DevOps: Epic › Feature › User
   Story › Task). Feature, not Story: a story is sprint-sized, while a feature
   here spans a spec and a multi-task plan, and brainstorming's Workspace
   section already calls the unit on one branch "the feature". Cost: the fork
   departs from upstream's "sub-project" wording at
   `skills/brainstorming/SKILL.md:149-152` and `skills/writing-plans/SKILL.md:30`;
   re-apply on each upstream sync.
5. **Finishing prints the next feature; it does not start it.** The finishing
   session's context is full of the feature just finished.
6. **Out of scope:** finishing opening a new Herdr pane to brainstorm the next
   feature.

## Design

### The epic file

Path: `docs/superpowers/epics/YYYY-MM-DD-<topic>.md` (the user's preferred
location overrides it, as for specs). The format lives in a new
`skills/brainstorming/epic-format.md`, read only when splitting a request or
continuing an epic:

```markdown
# Epic: <topic>

> Source: <the request, or the documents read and the commit they were read at>.
> Split on YYYY-MM-DD and approved.

## Findings
<what exploration found that shapes more than one feature: already done /
missing / blocked / conflicts / not ported; a compact table is fine>

## Shared decisions
<decisions made while splitting that bind more than one feature, including
where an item was placed and why>

## Features

### A. <name>
Scope: <bullets>
Depends on: <letters, or —>
Decide when brainstormed: <conflicts and questions deferred to this feature>

### B. <name>
...
```

Rules in `epic-format.md`:

- No dates, estimates, owners, story points, or status column. State comes
  from git.
- Letters are stable. A new feature takes the next unused letter. A feature
  that is dropped or folded into another keeps its letter, with one line
  saying so and why.
- Findings are facts the features share, not a plan; each feature's design
  happens in its own brainstorm.

### Writing the epic (brainstorming)

The decomposition bullet in "Understanding the idea" is rewritten:

1. Say the request holds several features; propose the split (pieces, how
   they relate, build order).
2. The approval ask names the epic path and the current branch, e.g. "...If
   this split looks right I'll commit it as an epic at
   `docs/superpowers/epics/2026-10-08-handoff.md` on `dev` and start
   brainstorming A." If your human partner names another branch, use it.
3. On yes: write the epic per `epic-format.md`, `git add` only that file,
   commit. Then brainstorm feature A as usual: its workspace is chosen at A's
   design approval, from a HEAD that carries the epic.

The Workspace section gains one sentence: the epic is the one write before
Isolate, because it belongs to no single feature.

### The spec header

Architectural checklist step 7: a spec for a feature of an epic starts with
`> **Epic:** <epic path> § <letter>`. Non-goals refer to other features by
letter ("Themes: B") instead of restating their scope. Self-review item 3
("needs decomposition?") points at the epic flow.

### Deriving state

```bash
EPIC=docs/superpowers/epics/2026-10-08-handoff.md
git grep -n "Epic:.*$(basename "$EPIC")" \
  $(git for-each-ref --format='%(refname:short)' refs/heads refs/remotes) -- '*.md'
```

Per feature letter, against the branch that carries the epic (the current
branch in brainstorming, the base branch in finishing):

- **not started**: no spec on any branch names it;
- **on branch X**: a spec names it only on unmerged branches (list them);
- **on `<base>`**: a spec naming it is on the base. Under a "stay on main"
  workspace the spec reaches the base before the code, so report it as "spec
  on `<base>`", not "done".

The next feature is the first not-started feature in epic order. When one of
its `Depends on` letters is not on the base yet, say so alongside it.

### Continuing an epic (brainstorming)

Only when the request carries an epic path. Then:

1. Read the epic and derive state.
2. Report it in one line ("Epic handoff: A on `dev`, B on `feat/shell-theme-b`,
   next is C").
3. Take the next feature, or the one the request names (warn if its
   dependencies are not on the base).
4. Its scope, its "Decide when brainstormed" items, and the shared decisions
   are the starting brief; invite correction as for any brief.
5. Do not re-split or redo what Findings records. Read only the code this
   feature touches.

A request without an epic path is an ordinary brainstorm.

### Editing the epic during a later feature

When designing B moves an item to C, or splits B, the epic edit is committed
with B's spec on B's branch and reaches the base when B merges. A feature
session never writes the epic on the base directly.

### finishing-a-development-branch

- **Step 3** also finds the spec this branch implements: the plan's `**Spec:**`
  header when the plan is known, else the spec file in
  `git diff --name-only <base>...HEAD`. Read its `Epic:` line. This happens
  before Step 5 because option 1 deletes the branch.
- **New Step 7**, after cleanup, when the spec has an `Epic:` line and the
  work was not discarded: derive state as above (the derivation command is
  repeated here, two lines, so the skill stands alone) and print:

  ```
  Feature A of docs/superpowers/epics/2026-10-08-handoff.md is merged into dev.
  Next: B. Shell + theme + branding: <one-line scope from the epic>.
  Start it in a new session with:

    Brainstorm feature B of docs/superpowers/epics/2026-10-08-handoff.md
  ```

  Option 2's first line says the feature is in PR `<url>`; option 3's says it
  stays on `<branch>`. A pending dependency gets one extra line. When every
  feature has a spec, list where each one is and print no prompt.

### Other touches

- `skills/writing-plans/SKILL.md:30`: "sub-project specs during brainstorming"
  becomes "features of an epic during brainstorming".
- `skills/using-git-worktrees/SKILL.md`, Isolate entry point: one sentence that
  an epic, when brainstorming splits a request, is committed on the current
  branch before Isolate.
- Unchanged: subagent-driven-development, executing-plans, sdd-in-new-session
  (all end in finishing), using-superpowers.

## Testing

Opus subagents, old vs new by swapping the skill files, as in earlier fork
evals. Fixture: `todo-cli`. Git state for cases 10, 11 and the finishing case
is built by a setup script in the eval workspace (a fixture cannot carry a
nested `.git`).

| Case | Situation | New skill must |
|---|---|---|
| 9 `decompose-names-epic` | Request with several features | propose the split; the approval ask names the epic path and branch; write no file |
| 10 `decompose-approved-writes-epic` | Transcript ends "agreed, start A" | commit only the epic file on `main` with Findings, Shared decisions, and per-feature Scope / Depends on / Decide when brainstormed; write no spec; ask A's first question |
| 11 `continue-epic` | Epic and spec A on `main`, spec B on `feat/b`; request carries `@epic` | report A on `main`, B on `feat/b`, next C; carry C's deferred questions; not re-split |
| finishing (new `evals.json`) | Branch `feat/a` of an epic, user picks 1 | after the merge, print feature B with its scope and a prompt holding the epic path; not start brainstorming B |

Case 11 is the sharpest contrast: only the new skill finds B on another branch.
Regression on the new skill: cases 0, 3, 7, 8.

## Release

Fork v6.4.24: RELEASE-NOTES section, the version files, tag, `main`
fast-forward, GitHub release, as for v6.4.22–23. Update the memory notes.
