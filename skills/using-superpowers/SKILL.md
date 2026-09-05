---
name: using-superpowers
description: Use when starting any conversation - establishes how to find and use skills, and when to check for a matching skill before the first response or action
disable-model-invocation: true
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

You have a library of skills: tested workflows for building, debugging, planning, and shipping. They change how the work is done, not just how it is checked, so they only help when invoked before the work starts.

## The Rule

**Invoke relevant or requested skills BEFORE any response or action** — including clarifying questions, exploring the codebase, or checking files. The skill tells you what to look for and what to ask, so orientation done before it is done again inside it. If the skill turns out wrong for the situation, set it aside and say so.

Which skill comes first:

| Request | First skill |
|---------|-------------|
| "Let's build X", add, change, or extend something, at any size (a flag or an option counts) | superpowers:brainstorming |
| Something is broken: failing test, error, wrong output | superpowers:systematic-debugging |
| Execute a written plan | superpowers:executing-plans or superpowers:subagent-driven-development |
| Anything else a skill in your list describes | that skill |

A question answered from the code or the conversation, a read-only look at a file or config, or an opinion on something you are not being asked to change needs no skill. Answer it directly. If it turns into a change request, invoke the skill then.

**Before entering plan mode:** if you haven't already brainstormed, invoke the brainstorming skill first.

Then announce "Using [skill] to [purpose]" and follow the skill exactly. If it has a checklist, create a todo per item.

## Skill Priority

When multiple skills apply, process skills come first — they set the approach, then implementation skills (frontend-design, etc.) carry it out. Brainstorming and systematic-debugging are Superpowers' most common process skills, but the rule holds for any of them.

- "Let's build X" → superpowers:brainstorming first, then implementation skills.
- "Fix this bug" → superpowers:systematic-debugging first, then domain skills.

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought | Reality |
|---------|---------|
| "I'll start by looking at the file / the failing test" | That is the step the skill scripts. Invoke it first; it tells you what to read. |
| "Let me get oriented first, then bring in the skill" | In practice the skill call never comes: sessions that orient first finish the task without it. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "The skill is overkill" | Small tasks are where tests get skipped and designs go unstated. The bounded paths are short. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Platform Adaptation

If your harness appears here, read its reference file for special instructions:

- Codex: `references/codex-tools.md`
- Antigravity: `references/antigravity-tools.md`
- Hermes Agent: `references/hermes-tools.md`

## User Instructions

User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc, direct requests) take precedence over skills, which in turn override default behavior. Only skip skill workflows or instructions when your human partner has explicitly told you to.
