---
name: sdd-in-new-session
description: Hands a written implementation plan to a fresh claude or pi coding agent in a new Herdr tab, where it runs subagent-driven-development in its own context while this session stays free for other work. Use when running inside Herdr (HERDR_ENV=1) and the user picks the new-session option after writing-plans, or asks to execute a plan in a separate tab, pane or agent.
---

# SDD In New Session

Hand a plan to a fresh agent in a new Herdr tab named after it, confirm the handoff, and return. This session never waits for the plan to finish. Reached from the Execution Handoff in superpowers:writing-plans, or directly as `/sdd-in-new-session [PLAN_PATH] [--branch] [--pi]`.

The `herdr` skill (installed, or printed by `herdr --skill`) is the reference for CLI syntax, JSON shapes, and safety rules. Two of its defaults are overridden here on purpose:

- It waits on a prompt with bare `--wait`, which returns at the first settled `idle`/`done`/`blocked`. Here that is the end of the agent's turn, potentially the whole plan, so the wait is `--until working`: the moment the agent picks the prompt up.
- It keeps the caller's `$PWD` and never creates a worktree. Here the tab opens in the plan's workspace, and who creates that workspace depends on where the plan already lives (see "Where the plan lives"). The point of the option is that this session stays free, so the two sessions must not share a working tree unless `--branch` asks for exactly that.

## Arguments

| Arg | Default | Effect |
|---|---|---|
| `PLAN_PATH` | plan written in this conversation; else newest file in `docs/superpowers/plans/` | Plan to execute |
| `--branch` | off → worktree | Spawned agent works in THIS checkout, on the plan's branch when there is one, else on a new branch from HEAD. The working tree is then shared with this session. |
| `--pi` | off → `claude` | Start `--kind pi` on the mid-tier model instead of `--kind claude` |

## Preflight

1. `test "${HERDR_ENV:-}" = 1` — otherwise say you are not inside Herdr and stop.
2. `PLAN=$(realpath "$PLAN_PATH")` — must exist. The spawned agent may work in another directory, so only an absolute path survives; "Where the plan lives" may rewrite it.
3. `ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)`.
4. Agent name — must match `[a-z][a-z0-9_-]{0,31}`, so the `sdd-` prefix is load-bearing (plan slugs start with a date). Cut at 26 so a `-2`/`-3` collision suffix still fits in 32:
   ```bash
   NAME="sdd-$(basename "$PLAN" .md | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}-//; s/[^a-z0-9_-]/-/g' | cut -c1-26 | sed 's/-$//')"
   ```
5. Detect where the plan lives (next section) and set `CWD`, `PLAN`, `ISOLATION`.

## Where the plan lives

Since brainstorming chooses the workspace before the spec is written, the plan is usually already on its feature branch, in a worktree or in this checkout. Detect which, with using-git-worktrees' Step 0 signals:

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
DEFAULT=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||'); DEFAULT=${DEFAULT:-main}
```

| State | Default | `--branch` |
|---|---|---|
| **A.** `GIT_DIR != GIT_COMMON` (linked worktree, not a submodule): this session is in the plan's worktree | Hand this worktree over: `CWD=$ROOT`, `PLAN` unchanged, `ISOLATION` = *in place*. Then this session leaves it (below). | Same as default; there is no second checkout to share. |
| **B.** Normal checkout on a feature branch (`BRANCH` non-empty and not `$DEFAULT`): the plan's branch is checked out here | This session creates the agent's worktree (below): `CWD=$WT`, `PLAN=$WT/<plan path relative to $ROOT>`, `ISOLATION` = *in place*. | `CWD=$ROOT`, `PLAN` unchanged, `ISOLATION` = *shared*. |
| **C.** Normal checkout on `$DEFAULT`, or detached: no workspace was chosen | `CWD=$ROOT`, `PLAN` unchanged, `ISOLATION` = *agent creates worktree*. | `CWD=$ROOT`, `ISOLATION` = *agent creates branch*. |

**A, leaving the worktree.** This session is about to stop touching a tree another agent edits. Call `ExitWorktree` with `action: "keep"` when the tool exists: it returns the session to the main checkout and never removes a worktree that was entered by `path` (the standard from using-git-worktrees). If the tool reports no active worktree session, `cd "$(dirname "$GIT_COMMON")"` (the main checkout) instead. The user's choice of this option is the request to leave; say in the report that this session moved.

**B, creating the agent's worktree.** `git worktree add <path> $BRANCH` refuses while the branch is checked out here, so this checkout steps off it first. The worktree goes to the standard `.worktrees/<branch>` from using-git-worktrees, and this session does not enter it: the agent in the pane does. finishing-a-development-branch owns cleanup under `.worktrees/`.

```bash
test -z "$(git status --porcelain)" || { echo "uncommitted changes on $BRANCH; commit or stash first"; exit 1; }
REL=${PLAN#"$ROOT"/}   # plan path relative to the checkout (portable; BSD realpath has no --relative-to)
BASE=<the branch this work forked from, known from the workspace choice; ask if unknown>
git switch "$BASE"
git check-ignore -q .worktrees || { echo ".worktrees/" >> .gitignore; git add .gitignore && git commit -m "chore: ignore .worktrees/"; }   # on $BASE, so every branch from here inherits it
WT="$ROOT/.worktrees/$BRANCH"
git worktree add "$WT" "$BRANCH"
PLAN="$WT/$REL"; CWD="$WT"
```

## Steps

```bash
# A tab per worker keeps this session's tab uncluttered and gives the worker a full screen and a named sidebar entry.
PANE=$(herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$CWD" --label "$NAME" | jq -r '.result.root_pane.pane_id')
herdr pane rename "$PANE" "$NAME"                            # the agent list shows pane labels
herdr agent start "$NAME" --kind claude --pane "$PANE"
# --pi instead: herdr agent start "$NAME" --kind pi --pane "$PANE" -- --model alias/mid-model --thinking medium
# 15000 ms: herdr reports agent_prompt_stalled itself after 5 s with no lifecycle change, so 15 s is ample and a hung wait still returns.
herdr agent prompt "$NAME" "$PROMPT" --wait --until working --timeout 15000
```

- `tab create` opens the tab without focusing it, so the user's view stays on this session.
- With `--pi`, name the model at start. pi launched without `--model` has come up on a model other than its settings default (observed: `xai/grok-4.7` instead of `alias/main`), and the controller then runs, and bills, on whatever that was. The SDD controller takes the mid tier from subagent-driven-development's harness table.
```

- No permission-bypass agent flags: the user sits beside the pane and approves interactively.
- Do not use `herdr worktree create`; the workspace is either the plan's existing one or the git worktree made above.
- The worker gets its own tab, not a split of this one: a split shares this session's screen and sidebar entry.
- `--until working` is the handoff check. Bare `--wait`, `agent wait --until done`, and `pane wait-output` all wait for the agent's turn to end, which here is the plan.

## Prompt template

Build `$PROMPT` with an unquoted heredoc so `$PLAN`, `$CWD` and `$BRANCH` expand, then pass it as one argument:

```bash
PROMPT=$(cat <<EOF
Execute the implementation plan at $PLAN using superpowers:subagent-driven-development skill.

Isolation: $ISOLATION

Read the plan from the absolute path above.
EOF
)
```

`$ISOLATION` (double-quoted so the variables expand):
- *in place* (A, B default): `ISOLATION="you are already in this plan's workspace at $CWD on branch $BRANCH; verify it with superpowers:using-git-worktrees Step 0 and create no other worktree or branch."`
- *shared* (B with `--branch`): `ISOLATION="work in this checkout ($CWD) on its current branch $BRANCH, which another session also has open; create no worktree or branch."`
- *agent creates worktree* (C default): `ISOLATION="create a new git worktree via superpowers:using-git-worktrees and do all work inside it."`
- *agent creates branch* (C with `--branch`): `ISOLATION="do NOT create a worktree. Create a new branch from the current HEAD in this checkout ($CWD) and do all work on that branch."`

With `--pi`, join the prompt into one line before sending it: `PROMPT=$(printf '%s' "$PROMPT" | tr '\n' ' ')`. pi submits on Enter, and a multi-line prompt pasted into its input stays there unsubmitted (`agent_prompt_stalled`). The prompt still names the superpowers skills; the plan header's "REQUIRED SUB-SKILL" line is the fallback if pi lacks them.

## After handoff

Return immediately — no polling, no `agent wait`, no reading the transcript. Report:

- tab id, pane id and label, agent name, plan path, workspace (worktree `<path>` | branch `<name>` in this checkout) and who created it
- in state A: that this session left the worktree and where it now is
- check-in commands: `herdr agent get NAME`, `herdr agent read NAME --source recent-unwrapped --lines 80`
- with `--branch`: the working tree is shared — editing files here before the agent finishes will collide

Leave the tab open; never close a tab or pane hosting a live agent.

## Failures

| Result | Do |
|---|---|
| Name taken on `agent start` | Append `-2`, `-3`, … to `$NAME`, rename the tab (`herdr tab rename`) and the pane to match, retry `agent start`. |
| `agent_not_ready` on start | `herdr agent read NAME` — usually a trust or permission dialog. Tell the user; do not resend. |
| `agent_blocked` on prompt | Read the pane, surface the dialog, ask the user before answering it. |
| `agent_prompt_stalled` / timeout on `--until working` | `herdr agent get NAME`. If already `working`, handoff succeeded. Otherwise report the pane state; never resend the prompt. |
| `git worktree add` refused in state B | The branch is still checked out somewhere (`git worktree list`). Do not force; report and let the user pick `--branch`. |
