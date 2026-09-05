---
name: sdd-in-new-session
description: Hands a written implementation plan to a fresh claude or pi coding agent in a sibling Herdr pane, where it runs subagent-driven-development in its own context while this session stays free for other work. Use when running inside Herdr (HERDR_ENV=1) and the user picks the new-session option after writing-plans, or asks to execute a plan in a separate pane or agent.
---

# SDD In New Session

Hand a plan to a fresh agent in a sibling Herdr pane, confirm the handoff, and return. This session never waits for the plan to finish. Reached from the Execution Handoff in superpowers:writing-plans, or directly as `/sdd-in-new-session [PLAN_PATH] [--branch] [--pi]`.

**REQUIRED BACKGROUND:** read and follow the installed `herdr` skill for CLI syntax, split-direction rule, and safety rules.

## Arguments

| Arg | Default | Effect |
|---|---|---|
| `PLAN_PATH` | plan written in this conversation; else newest file in `docs/superpowers/plans/` | Plan to execute |
| `--branch` | off → worktree | Spawned agent creates a new branch in THIS checkout instead of a worktree. The working tree is then shared with this session. |
| `--pi` | off → `claude` | Start `--kind pi` instead of `--kind claude` |

## Preflight

1. `test "${HERDR_ENV:-}" = 1` — otherwise say you are not inside Herdr and stop.
2. `PLAN=$(realpath "$PLAN_PATH")` — must exist. The spawned agent changes directory into a worktree, so only an absolute path survives.
3. `ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)`.
4. `git status --porcelain -- "$PLAN"` non-empty → plan is uncommitted. Do not commit it yourself; note it in the final report (it will be absent from the worktree and from any merged branch until committed).
5. Agent name — must match `[a-z][a-z0-9_-]{0,31}`, so the `sdd-` prefix is load-bearing (plan slugs start with a date):
   ```bash
   NAME="sdd-$(basename "$PLAN" .md | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}-//; s/[^a-z0-9_-]/-/g' | cut -c1-28)"
   ```
   If `herdr agent list` already shows `$NAME`, append `-2`, `-3`, …

## Steps

```bash
herdr pane layout --current      # wide → right, narrow/tall → down
PANE=$(herdr pane split --current --direction right --cwd "$ROOT" --no-focus | jq -r '.result.pane.pane_id')
herdr pane rename "$PANE" "$NAME"                            # label the pane so it is findable in the sidebar
herdr agent start "$NAME" --kind claude --pane "$PANE"       # --kind pi when --pi
herdr agent prompt "$NAME" "$PROMPT" --wait --until working --timeout 15000
```

- No permission-bypass agent flags: the user sits beside the pane and approves interactively.
- Do not use `herdr worktree create`; the spawned agent owns its isolation.
- `--until working` is the handoff check: it returns within seconds once the agent picks the prompt up. Bare `--wait` matches `idle`/`done`, which is the end of the agent's turn — potentially the entire plan. Never use bare `--wait`, `agent wait --until done`, or `pane wait-output` here.

## Prompt template

Build `$PROMPT` with a quoted heredoc and pass it as one argument.

```text
Execute the implementation plan at <ABS_PLAN_PATH> using superpowers:subagent-driven-development skill.

Isolation: <ISOLATION>

Read the plan from the absolute path above (it may not be committed yet).
```

`<ISOLATION>`:
- default: `create a new git worktree via superpowers:using-git-worktrees and do all work inside it.`
- `--branch`: `do NOT create a worktree. Create a new branch from the current HEAD in this checkout (<ROOT>) and do all work on that branch.`

With `--pi`, the prompt still names the superpowers skills; the plan header's "REQUIRED SUB-SKILL" line is the fallback if pi lacks them.

## After handoff

Return immediately — no polling, no `agent wait`, no reading the transcript. Report:

- pane id and label, agent name, plan path, isolation mode (worktree | branch `<name>`)
- check-in commands: `herdr agent get NAME`, `herdr agent read NAME --source recent-unwrapped --lines 80`
- with `--branch`: the working tree is shared — editing files here before the agent finishes will collide
- if the plan was uncommitted: say so

Leave the pane open; never close a pane hosting a live agent.

## Failures

| Result | Do |
|---|---|
| `agent_not_ready` on start | `herdr agent read NAME` — usually a trust or permission dialog. Tell the user; do not resend. |
| `agent_blocked` on prompt | Read the pane, surface the dialog, ask the user before answering it. |
| `agent_prompt_stalled` / timeout on `--until working` | `herdr agent get NAME`. If already `working`, handoff succeeded. Otherwise report the pane state; never resend the prompt. |
| Name taken | Append `-2`, `-3`, … and retry `agent start`. |
