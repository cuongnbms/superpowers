---
name: writing-plans
description: Writes a task-by-task implementation plan from an approved spec or requirements - exact files, test code, implementation code, and commit steps per task, so an engineer or subagent with no context can execute it. Use when the user has a spec or requirements for a multi-step change and needs an implementation plan, or asks to plan the work before touching code.
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as small tasks made of single-action steps. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Save plans to:** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

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
inside a task, 2-5 minutes of work.

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

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## No Placeholders

A task's implementer sees only their own task: not the spec, not the other
tasks, not this conversation, and often not in order. Whatever a step leaves
out, they have to invent, and they will invent it differently from the
neighboring task. So every step carries the actual content an engineer
needs. These are plan failures:

- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code; they cannot see Task N)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Placeholder scan:** Search your plan for red flags — any of the patterns from the "No Placeholders" section above. Fix them.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.

## Commit the Plan

After self-review and before handoff, commit the completed plan so new
sessions and worktrees can access the exact reviewed version.

```bash
git add docs/superpowers/plans/<filename>.md
git commit -m "docs: add <feature-name> implementation plan"
```

## Execution Handoff

After saving the plan, offer execution choice. Option 2 exists only inside
Herdr: run `test "${HERDR_ENV:-}" = 1` first, and outside Herdr list the
other two.

**"Plan complete, saved to `docs/superpowers/plans/<filename>.md`, and committed. Execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task in this session and review between tasks; fast iteration

**2. New Session** - same subagent-driven process, run by a fresh `claude` or `pi` agent in a sibling Herdr pane; this session stays free for other work

**3. Inline Execution** - execute tasks in this session using executing-plans, batch execution with checkpoints; for harnesses without subagents

**Which approach?"**

- Subagent-Driven chosen: use superpowers:subagent-driven-development (fresh subagent per task, two-stage review).
- New Session chosen: use superpowers:sdd-in-new-session with the plan path; add `--pi` when the user wants pi, `--branch` when they want a branch in this checkout instead of a worktree.
- Inline Execution chosen: use superpowers:executing-plans (batch execution with checkpoints for review).
