---
name: using-git-worktrees
description: Chooses and sets up where feature work lives - a worktree under .worktrees/, a new branch in this checkout, or the current branch - the same way for every agent kind, then prepares the workspace (dependencies, clean test baseline). Use right before the first write to a repository during brainstorming or planning (the spec, the first code edit) and again at execution setup to verify the choice and prepare the workspace.
---

# Using Git Worktrees

## Overview

Make sure work lands where your human partner wants it, and make that decision once, before anything is committed. A worktree is shared infrastructure: the agent that plans in it, the agent that executes in it (often a different kind: claude, pi, codex), and finishing-a-development-branch that cleans it up all need the same location and the same lifecycle. So every agent creates worktrees the same way, with git, at one standard path; a harness's native worktree tool is used only to move a session into a worktree that already exists.

**Core principle:** Detect existing isolation first. Create with git at the standard path, from the current HEAD. Enter with the native tool when the harness has one. Never leave a worktree only the creating session knows about.

**Announce at start:** "I'm using the using-git-worktrees skill to set up the workspace."

## Two entry points

- **Isolate (Steps 0 and 1):** run right before the first write to the repository. On the architectural path that is the spec file (brainstorming, after the design is approved); on the bounded path it is the first code edit; when a plan arrives from elsewhere it is the plan file. From then on the spec, the plan, and the code ride one branch, and finishing-a-development-branch merges or discards them together. Isolating later leaves the spec and plan committed on the branch you started from, usually main, whether or not the feature ships. When brainstorming splits a request into features, the epic is committed on the current branch before Isolate, since it belongs to no single feature.
- **Prepare (Steps 2 and 3):** run at execution setup (subagent-driven-development, executing-plans). Installing dependencies and running the baseline suite pays off when code is about to be written, not while the design is still being discussed.

A caller that reaches Prepare without an Isolate decision in this conversation runs Steps 0 and 1 first.

## Step 0: Detect Existing Isolation

**Before creating anything, check if you are already in an isolated workspace.**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

**Submodule guard:** `GIT_DIR != GIT_COMMON` is also true inside git submodules. Before concluding "already in a worktree," verify you are not in a submodule:

```bash
# If this returns a path, you're in a submodule, not a worktree — treat as normal repo
git rev-parse --show-superproject-working-tree 2>/dev/null
```

**If `GIT_DIR != GIT_COMMON` (and not a submodule):** You are already in a linked worktree. Skip to Step 2 (Project Setup) when preparing, or stop here when isolating. Do NOT create another worktree.

Report with branch state:
- On a branch: "Already in isolated workspace at `<path>` on branch `<name>`."
- Detached HEAD: "Already in isolated workspace at `<path>` (detached HEAD, externally managed). Branch creation needed at finish time."

**If `GIT_DIR == GIT_COMMON` (or in a submodule):** You are in a normal repo checkout.

If the workspace was already chosen earlier in this conversation, or your instructions declare a preference, honor it without asking. Otherwise ask once, with a recommendation, and let the answer to the approval you are already asking for cover it when the two coincide (brainstorming folds it into the design approval so the yes is one word):

> "Where should this work live? (1) a new worktree under `.worktrees/`, so this checkout stays free for other work; (2) a new branch `<topic>` in this checkout; (3) stay on `<current branch>`. I'd go with <1 or 2> because <the reason: uncommitted changes here, you may want to keep working on this checkout, or the branch is main>."

Recommend a worktree when the checkout has uncommitted work or your human partner is likely to keep using it while this runs; a branch in this checkout otherwise. Recommend staying only when the current branch is already the one for this work.

Record the answer. "Stay" on main or master is the explicit consent that the execution skills require before implementing on the default branch; they do not ask again. If the answer is a branch in this checkout:

```bash
git switch -c "$BRANCH_NAME"
```

Then stop (isolating) or continue to Step 2 (preparing). If the answer is a worktree, continue to Step 1.

## Step 1: Create Isolated Workspace

Two parts, in this order: create with git, then enter.

### 1a. Create the worktree with git

The worktree is created with `git worktree add`, whatever harness you run in. A native creation tool (Claude Code's `EnterWorktree` with a name, `WorktreeCreate`, `/worktree`) puts the worktree in a harness-specific directory, branches from the remote default branch rather than from here, and ties cleanup to the session that created it. None of that survives a handoff to another agent, and finishing-a-development-branch does not own that directory.

#### Directory Selection

Follow this priority order. Explicit user preference always beats observed filesystem state.

1. **Check your instructions for a declared worktree directory preference.** If the user has already specified one, use it without asking.

2. **Check for an existing project-local worktree directory:**
   ```bash
   ls -d .worktrees 2>/dev/null     # Preferred (hidden)
   ls -d worktrees 2>/dev/null      # Alternative
   ```
   If found, use it. If both exist, `.worktrees` wins.

3. **If there is no other guidance available**, default to `.worktrees/` at the project root.

#### Make sure the directory is ignored

Run this every time, before `git worktree add`; an unignored worktree directory commits a whole second checkout into the repository the first time anyone runs `git add -A`.

```bash
git check-ignore -q "$LOCATION" || {
  echo "$LOCATION/" >> .gitignore
  git add .gitignore && git commit -m "chore: ignore $LOCATION/" \
    || echo "$LOCATION/" >> "$(git rev-parse --git-common-dir)/info/exclude"   # cannot commit here (detached, hooks): local exclude
}
```

The `.gitignore` commit is preferred over the local exclude file because the other agents, and the other machines, that work on this repository inherit it.

#### Create the Worktree

```bash
WT_PATH="$LOCATION/$BRANCH_NAME"               # not `path`: in zsh that name is tied to PATH and clears it
git worktree add "$WT_PATH" -b "$BRANCH_NAME"  # from the current HEAD: local commits are included
```

**Sandbox fallback:** If `git worktree add` fails with a permission error (sandbox denial), tell the user the sandbox blocked worktree creation and you're working in the current directory instead. Then run setup and baseline tests in place.

### 1b. Enter the worktree

In Claude Code, `cd` in a shell moves only that shell; the session's own working directory, which `Read`, `Edit`, and relative paths resolve against, stays in the main checkout, and edits meant for the worktree land there. Move the session:

- **Claude Code:** call `EnterWorktree` with `path` set to the worktree you just created. It accepts any worktree listed by `git worktree list`. Leaving later is `ExitWorktree` with `action: "keep"`; the tool never removes a worktree entered by path, so cleanup stays with finishing-a-development-branch.
- **Other harnesses** (pi, codex, a plain shell): `cd "$WT_PATH"` and keep every path you hand to tools absolute.

Then stop (isolating) or continue to Step 2 (preparing).

## Step 2: Project Setup

Auto-detect and run appropriate setup:

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

## Step 3: Verify Clean Baseline

Run tests to ensure workspace starts clean:

```bash
# Use project-appropriate command
npm test / cargo test / pytest / go test ./...
```

**If tests fail:** Report failures, ask whether to proceed or investigate.

**If tests pass:** Report ready.

### Report

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| Isolating (first write: spec, plan, or code) | Steps 0 and 1 only |
| Preparing (execution setup) | Step 0 to verify; Steps 2 and 3; Step 1 only if no choice was made yet |
| Already in linked worktree | Skip creation (Step 0) |
| In a submodule | Treat as normal repo (Step 0 guard) |
| Workspace chosen earlier in this conversation | Honor it, do not re-ask |
| Answer: branch in this checkout | `git switch -c`, no worktree |
| Answer: stay on main/master | That is the consent execution skills need; record it |
| Answer: worktree | `git worktree add` at the standard path (1a), then enter (1b) |
| Claude Code | Enter with `EnterWorktree` + `path`; never create with `EnterWorktree` + name |
| pi, codex, shell | `cd` into the worktree, absolute paths from then on |
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check instruction file, then default `.worktrees/` |
| Directory not ignored | Add to .gitignore + commit; local exclude only if the commit is impossible |
| Permission error on create | Sandbox fallback, work in place |
| Tests fail during baseline | Report failures + ask |
| No package.json/Cargo.toml | Skip dependency install |

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'll commit the spec here and branch off at execution time" | The spec is the feature's first commit. Committed on main it stays there if the feature is dropped. Choose the workspace before the first write. |
| "I'm obviously not in a worktree — no need to check" | Run Step 0. Harness-created isolation and submodules both fool eyeballing; the detection commands settle it. |
| "`EnterWorktree` with a name is one call, git is three" | That one call puts the worktree in `.claude/worktrees/`, branched from the remote default, owned by this session. The pi agent that executes the plan, and finishing-a-development-branch that cleans up, both expect `.worktrees/<branch>` from HEAD. Create with git, enter with the tool. |
| "I `cd`-ed into the worktree, the session is there now" | In Claude Code only the shell moved. Call `EnterWorktree` with `path`, or the next `Edit` writes to the main checkout. |
| "The worktree directory is surely ignored already" | Run `git check-ignore`. An unignored worktree directory commits the whole tree into the repo. |
| "Any directory name works" | Explicit instructions beat an existing project-local directory, which beats the `.worktrees/` default. |
| "I'll install dependencies now, while we design" | Prepare belongs to execution setup. A design that changes the stack wastes the install, and the baseline run delays the conversation. |
| "The workspace is fresh — baseline tests can wait" | A dirty baseline makes every later failure ambiguous. Run the tests now; proceeding past failures is your human partner's call. |
