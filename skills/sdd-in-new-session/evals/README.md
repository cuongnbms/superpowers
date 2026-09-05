# sdd-in-new-session evals

The skill only runs inside Herdr, so these evals replace the `herdr` CLI with a
test double (`fixtures/bin/herdr`) that logs every invocation and answers with
JSON shaped like the real socket API. No Herdr server is involved.

## Files

- `evals.json` — three cases with prompts and expectations
- `fixtures/repo/` — a small Python project with a committed plan
- `fixtures/bin/herdr` — the test double; knobs are documented at its top
- `setup-case.sh <case> DEST` — materializes a case: git repo, shim on PATH,
  and `DEST/env.sh` that makes a shell look like a Herdr pane (cwd = repo,
  `HERDR_ENV=1`, pane ids, shim log paths)
- `grade.sh <case> DEST [final-message.md]` — mechanical PASS/FAIL over the
  call log, the prompt file, and the final message

## Running a case

```bash
evals/setup-case.sh collision /tmp/sdd-collision
# executor: "source /tmp/sdd-collision/env.sh" at the start of every shell
# command, then perform the handoff as the skill says
evals/grade.sh collision /tmp/sdd-collision /tmp/final-message.md
```

Artifacts to read by hand: `DEST/herdr-calls.log`,
`DEST/.herdr-shim/prompt-<agent>.txt`, `DEST/.herdr-shim/renames`.

## Cases

| case | pane | flags | what it exercises |
|---|---|---|---|
| worktree | 220x50 | none | split right, claude, worktree prompt, `--until working`, return at once |
| branch-pi | 80x60 | `--branch --pi` | split down, pi, no-worktree prompt naming the checkout, shared-tree warning |
| collision | 220x50 | none, 52-char slug | first `agent start` rejected as `agent_name_taken`; retry name must still fit 32 chars; pane relabeled |

Waits that would block until the agent's turn ends (bare `--wait`, `agent wait`,
`pane wait-output`) sleep `HERDR_SHIM_TURN_SECONDS` (default 25) so they show up
in timing as well as in the log.

## What the evals cannot cover

- Whether Herdr classifies the spawned agent as `working` without the claude/pi
  integration hooks installed (`herdr integration status`)
- How the spawned agent reconciles the `--branch` prompt with
  subagent-driven-development's worktree setup step
