# Evals for subagent-driven-development

Three dry-run cases. The controller is asked to do everything the skill
says up to its next subagent dispatch, write that dispatch prompt to
`dispatch.md` at the repo root, and stop. This keeps a run to one agent
and a few dozen tool calls while still exercising setup, ledger resume,
pre-flight rulings, brief generation, and fix-loop routing.

- `evals.json` — prompts and expectations (see `../../writing-skills/references/schemas.md`)
- `fixtures/notes-cli/` — tiny Python project plus a 3-task plan and its spec.
  The plan carries one planted conflict: Task 1 produces `parse_tags`,
  Task 2 consumes `extract_tags`.
- `setup-case.sh CASE DEST` — materializes a case as a real git repo on
  `feature/notes-tags`: `fresh` (no ledger), `resume` (Task 1 complete,
  stray flat ledger from another plan), `midloop` (Task 2 at fix round 3/5
  with one finding still open).

Grade from artifacts: the plan ledger, the brief file, `dispatch.md`, and
the final message. Mechanical checks produce false positives (a `?` in a
quoted plan line, a model name mentioned while explaining a choice); read
every hit before counting it.
