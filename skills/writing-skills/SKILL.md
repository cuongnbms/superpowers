---
name: writing-skills
description: Create, improve, and evaluate agent skills (SKILL.md files) end to end - capture intent, measure a no-skill baseline, draft, run with-skill versus baseline evals, review outputs, iterate, and tune the description for triggering accuracy. Use when the user wants to write a new skill, edit or fix an existing skill, test whether a skill works, benchmark a skill, or optimize a skill's description or wording.
---

# Writing Skills

Skills are code that shapes agent behavior, so they are developed like code: observe a
failure, write the smallest thing that fixes it, measure, iterate. This file is the workflow
and the judgment calls. The rules for structure, frontmatter, descriptions, and length live in
**references/anthropic-best-practices.md**, an offline copy of Anthropic's guidance that is
kept up to date by hand. Read it before drafting; do not rely on memory of the rules, because
that file changes and this one does not restate it.

Evaluation tooling in `scripts/`, `agents/`, `assets/`, and `eval-viewer/` is adapted from
Anthropic's `skill-creator` plugin (Apache 2.0, see LICENSE.txt). If `skill-creator` is also
installed, uninstall it: two skills with overlapping descriptions compete for triggering.

## The loop

1. Capture intent: what the skill enables, when it triggers, what the output looks like.
2. Baseline: run the task without a skill on the model you will use. Classify the failure.
3. Draft SKILL.md, in the form that matches the failure.
4. Write two or three realistic test prompts; run with-skill and baseline in parallel.
5. Draft assertions while runs are in progress; grade; aggregate; open the viewer.
6. Read the user's feedback; improve; rerun into the next iteration.
7. When the body is stable, optimize the description with should- and should-not-trigger
   queries.
8. Validate frontmatter, package if distributing outside a plugin.

Add a todo per step. Mechanics for steps 4 to 8 are in **references/eval-workflow.md**.

Be flexible about where the user is. Someone arriving with a draft starts at step 4. Someone
who says "just vibe with me" gets the draft and a sanity run, not a benchmark.

## Capture intent

The conversation often already contains the workflow to capture ("turn this into a skill").
Extract from history first: tools used, step order, corrections the user made, input and
output formats. Then fill gaps with the user:

- What should the skill let Claude do?
- When should it trigger, in the user's own phrases?
- What does a good output look like? Is there an example?
- Are outputs objectively checkable (file transforms, extraction, fixed steps) or subjective
  (style)? The first kind gets assertions; the second gets human review.

Ask about edge cases, dependencies, and success criteria before writing test prompts.
Research in parallel with subagents when that reduces the burden on the user.

## Baseline first, then match the form to the failure

Run the no-skill baseline on the model you will actually run, in a fresh context. Current
Claude models follow instructions closely and need less prescription than older ones, so
guidance for an imagined failure often degrades output. If the baseline does not fail, write
nothing.

Then classify what the baseline actually did wrong. Each form fixes one failure type and
backfires on the others.

| Baseline failure | Write this | Not this |
|---|---|---|
| Knows the rule, skips it under pressure | Short rule with its reason, plus the specific workarounds you observed (rationalization table, red-flag list) | Soft guidance ("prefer", "consider") |
| Complies, but output has the wrong shape | A recipe: what the output *is*, its parts in order | A list of "don't" |
| Omits a required element | A required slot in the template it fills in | A prose reminder near the template |
| Behavior depends on a condition | A conditional keyed to something observable ("if the brief exists, cite it") | Unconditional rule plus exemption clauses |
| Lacks knowledge (API, schema, house convention) | Reference material, progressively disclosed | Rules about behavior |

Prohibitions lose on shaping problems: under a competing incentive the model negotiates with
"don't X" and produces more X than with no guidance. A recipe leaves nothing to negotiate.

Two wording rules for any form. A nuance clause ("unless it matters") reopens the negotiation,
so state a real exception as its own conditional. An exemption clause ("does not apply to code
blocks") still suppresses the exempted thing, so restructure the rule so it cannot reach it.

Give the reason instead of volume. Writing ALWAYS or NEVER in capitals is a yellow flag:
`MUST`, `NEVER`, `CRITICAL` cause overtriggering in descriptions and invite
letter-versus-spirit arguments in bodies. A stated reason lets the model generalize to cases
you did not list.

## Draft the skill

Follow references/anthropic-best-practices.md for structure, frontmatter constraints, naming,
progressive disclosure, degrees of freedom, and the checklist. Points that are easy to get
wrong:

- **Description = capability + triggers, third person, no workflow steps.** A description that
  outlines the steps gets followed *instead of* the body. Put "when to use" here, not in the
  body. No emphatic trigger words.
- **Body under 500 lines.** Move heavy reference into files linked one level deep from
  SKILL.md; add a table of contents to any file over 100 lines.
- **Prefer imperative form** in instructions, and explain why each instruction matters.
- **Scripts for deterministic work.** If test runs show subagents each writing the same
  helper, bundle it in `scripts/` and tell the skill to run it.
- **Side-effecting skills** (deploy, commit, send): consider `disable-model-invocation: true`
  or `paths` rather than wording tricks to control when they fire.

Write a draft, then reread it with fresh eyes and cut what is not pulling its weight.

## Test cases

Two or three prompts a real user would actually type, with concrete context (paths, names,
constraints). Share them: "Here are the test cases I'd like to try. Do these look right?"
Save prompts to `evals/evals.json` and fixtures to `evals/fixtures/`. Assertions come after
the runs start; see references/eval-workflow.md and references/schemas.md.

Spawn with-skill and baseline runs in the same turn. Never run the eval loop with a testing
skill other than this one.

## Pressure scenarios

For the first row of the form table only. An academic prompt ("what does the skill say?")
gets a recitation; the model has to *want* to break the rule. Combine three or more pressures:
time, sunk cost, authority, exhaustion, the social cost of looking dogmatic.

```
IMPORTANT: this is a real scenario. Choose and act; no hypotheticals.
You spent 3 hours on 200 lines, manually tested, it works. It's 6pm,
dinner at 6:30, review at 9am. You just noticed you never wrote tests.
A) Delete it, restart with TDD tomorrow
B) Commit now, add tests tomorrow
C) Write tests now (30 min), then commit
Choose A, B, or C.
```

Force a concrete choice, use real paths, allow no exit through "I'd ask the user". Record
every rationalization verbatim; each becomes a row in the skill's table. Run without the
skill, then with it, in fresh contexts, five or more times per variant. If five runs give five
shapes, the wording is not binding yet.

When the model reads the skill and still picks wrong, ask: "How should the skill have been
written so A was the only acceptable answer?" "It was clear, I ignored it" means the reason is
missing. "It should have said X" is text to add. "I didn't see that section" is an ordering
problem.

## Improving the skill

This is the heart of the loop. The user has reviewed the outputs; now make the skill better.

1. **Generalize from the feedback.** The skill will run across many prompts you will never
   see. You are iterating on a few examples because that is fast, but a skill that works only
   on those examples is useless. For a stubborn issue, try a different framing or working
   pattern rather than a fiddly, overfitted rule or an oppressive MUST.
2. **Keep the prompt lean.** Read the transcripts, not just the outputs. If the skill makes
   the model do unproductive work, remove the part that causes it and see what happens.
3. **Explain the why.** Even when feedback is terse, understand what the user actually needs
   and transmit that understanding. A model that knows why can handle cases you did not list.
4. **Look for repeated work across test cases.** Same helper script written three times means
   the skill should ship it.

Write a revised draft, then look at it anew and improve it before rerunning.

## Communicating with the user

Users range from experienced engineers to people opening a terminal for the first time. Read
the cues. "Evaluation" and "benchmark" are fine; explain "assertion" or "JSON" briefly unless
the user has shown they know them. Generate the viewer before forming your own verdict on the
outputs so the human sees them first.

## Finish

- Frontmatter valid (`claude plugin validate <real directory>` in Claude Code, or
  `python -m scripts.quick_validate <skill-dir>`).
- Checklist in references/anthropic-best-practices.md walked.
- Evals and fixtures committed alongside the skill; workspace results kept outside the repo.
- Report the with-skill versus baseline table and what still fails, not just "it works".

## Files

- `references/anthropic-best-practices.md`: the rulebook (offline copy, kept in sync by hand)
- `references/eval-workflow.md`: step-by-step eval, viewer, feedback, description optimization
- `references/schemas.md`: JSON formats for evals, grading, benchmark, feedback
- `agents/grader.md`, `agents/comparator.md`, `agents/analyzer.md`: subagent instructions
- `scripts/`: aggregate benchmark, trigger eval and description loop, validate, package
- `eval-viewer/generate_review.py`: local review UI; `assets/eval_review.html`: trigger-query review
- `evals/`: this skill's own test cases and fixtures
