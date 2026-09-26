---
name: writing-plans
description: Writes a task-by-task implementation plan from an approved spec or requirements - exact files, signatures, test assertions, and commit steps per task, so an engineer or subagent with no context can execute it. Use when the user has a spec or requirements for a multi-step change and needs an implementation plan, or asks to plan the work before touching code.
---

# Writing Plans

## Overview

Write implementation plans for an engineer who has not seen this codebase or this spec. Assume they write idiomatic code in the project's language once they know the exact interface and the exact test, and that they will make a reasonable choice wherever the plan leaves one open. What they cannot know is what you decided: which files, which names and signatures, which values from the spec, which tests prove each task. Document those. Give them the whole plan as small tasks made of single-action steps. DRY. YAGNI. TDD. Frequent commits.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Save plans to:** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

**Planning is reading; execution is running.** Check the plan against the
spec and the codebase by reading them (`grep`, `go doc`, the existing
tests). Building or running the plan's code, in the repo or in a scratch
copy, is execution, and execution starts after your human partner has
reviewed the plan. A plan whose values were confirmed by a scratch build
has spent the executor's work before the plan was approved.

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Tasks and Steps

A plan has two levels. A **task** is the smallest unit that carries its own
test cycle and is worth a fresh reviewer's gate. A **step** is one action
inside a task with a checkable result.

**Drawing task boundaries:** fold setup, configuration, scaffolding, and
documentation steps into the task whose deliverable needs them; split only
where a reviewer could meaningfully reject one task while approving its
neighbor. Each task ends with an independently testable deliverable.

**Steps inside a task**, each one action:
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

Every plan starts with this exact header. Executors read Spec and Global
Constraints by name (the orchestrator loads the spec and copies the
constraints into every task brief), so keep the field labels as written.

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Spec:** [path to the spec/design doc this plan implements — the plan
argues from the spec, so the spec travels with it; executors read both]

## Global Constraints

[The spec's project-wide requirements — version floors, dependency limits,
naming and copy rules, platform requirements — one line each, with exact
values copied verbatim from the spec. Every task's requirements implicitly
include this section.]

## Review Focus

[Up to five input classes or failure modes the spec implies but no task's
tests exercise, the ones most likely to bite a person using this software
— one line each, naming the input or condition and the behavior a
reasonable person would expect, most likely first. The spec is a vision
document: it says what the software must do, not everything it will
meet, and its silence on an input is not permission for that input to
break the program. Write the list here, once, with the spec in front of
you. Then, for each line, add the test that pins it to the task that
owns the code, in that task's own step style.]

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Interfaces:**
- Consumes: [what this task uses from earlier tasks — exact signatures]
- Produces: [what later tasks rely on — exact function names, parameter
  and return types. A task's implementer sees only their own task; this
  block is how they learn the names and types neighboring tasks use.]

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Implement `function(input: InputType) -> ResultType` in `exact/path/to/file.py`**

One line on the approach when the signature and the test leave a choice
(which library call, which data structure); a code block only for an
algorithm they do not determine.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## What a Step Contains

A task's implementer sees only their own task: not the spec, not the other
tasks, not this conversation, and often not in order. A step is done when
they can write exactly one reasonable thing from it. That is the whole
requirement: unambiguous, not complete. Each kind of step carries what
makes it unambiguous and nothing more:

- **A test step:** the complete test as code, runnable as written, with
  the spec's exact values in its assertions and the fixtures, helpers and
  imports it needs. The test is the contract the reviewer grades the task
  against; an outline, a commented assertion, or a fixture described in
  prose lets the implementer pin less than the spec requires.
- **A code step:** the exact signature (name, parameters, return type), the
  file it lives in, and the specific values the spec pins. The implementer
  writes the body. A body appears only for an algorithm the signature and
  tests do not determine, or for exact copy the spec fixes.
- **A verification step:** the command to run and the output that means it
  passed.
- **A reference to another task:** that task's Interfaces block says what
  to use; the plan does not repeat that task's code. "Similar to Task N"
  fails for the same reason: they cannot see Task N.

A plan is the set of decisions the implementer cannot make alone. A plan
whose implementation steps are longer than the code they describe has
written the code instead. Lines that decide nothing ("TBD", "handle edge
cases", "add appropriate validation", "write tests for the above", a type
or function no task defines) are the opposite failure, and the self-review
catches both.

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Step scan:** Every step must let the implementer write exactly one reasonable thing, and no step may carry more than that: a line that decides nothing is a gap, a function body the signature and tests already determine is a transcript. Fix both.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

**4. Review Focus:** For each input class or failure mode the spec implies, is there a task whose tests exercise it? The uncovered ones most likely to bite a person go in the Review Focus section, and each line there gets its test added to the owning task. An empty section means you checked and found none, not that you skipped the check.

**5. Proportion:** Compare the plan's length to the spec's. A plan several times longer than the spec it implements is a transcript of the program, not a plan. If implementation bodies are most of the document, replace them with signatures and the values the spec pins, and check that each step is still unambiguous. Test code is the plan's decisions and stays complete.

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.

## Commit the Plan

After self-review and before handoff, commit the completed plan so new
sessions and worktrees can access the exact reviewed version.

```bash
git add docs/superpowers/plans/<filename>.md
git commit -m "docs: add <feature-name> implementation plan"
```

## Execution Handoff

After committing the plan, link it for your human partner to read, and wait
for their review before any implementation starts: approving an idea, a
scope, or a spec is not approving a plan they have not seen. If they ask
for changes, edit the plan and commit again before handing off.

If they already chose an execution method, keep it and ask only for the
review:

**"Plan complete, saved to `docs/superpowers/plans/<filename>.md`, and committed. Please review it. Does it capture what you want?"**

Otherwise offer the execution choice with the review. Option 2 exists only
inside Herdr: run `test "${HERDR_ENV:-}" = 1` first, and outside Herdr list
the other two.

**"Plan complete, saved to `docs/superpowers/plans/<filename>.md`, and committed. Please review it. Execution options:**

**1. Subagent-Driven** - I dispatch a fresh subagent per task in this session, a fresh reviewer checks each task before the next starts, then a whole-branch review at the end. Most thorough; costs a fresh context per task and per review

**2. Subagent-Driven in new session** - same subagent-driven process, run by a fresh `claude` or `pi` agent in a sibling Herdr pane; this session stays free for other work

**3. Inline Execution** - I implement every task myself in this session using executing-plans, without pausing between tasks, then one fresh reviewer on the most capable model checks the whole branch. Cheapest and fastest; no independent review until the end. Runs well on a mid-tier session model, and is the option for harnesses without subagents

**For this plan I recommend <one option>, because <one sentence drawn from the plan: how much the tasks depend on each other's interfaces, how many there are, what a shipped mistake would cost>. Does the plan capture what you want, and which approach should we use?"**

- Subagent-Driven chosen: use superpowers:subagent-driven-development (fresh subagent per task, two-stage review).
- Subagent-Driven in new session chosen: use superpowers:sdd-in-new-session with the plan path; add `--pi` when the user wants pi, `--branch` when they want a branch in this checkout instead of a worktree.
- Inline Execution chosen: use superpowers:executing-plans (continuous inline execution, one whole-branch review at the end).
