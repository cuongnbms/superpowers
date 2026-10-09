---
name: brainstorming
description: Turns an idea or change request into an approved design before implementation - explores intent, requirements, and trade-offs at the depth the task needs, from a two-sentence check-in for a small change to a written spec for a new subsystem. Use when the user wants to build, add, create, extend, or redesign something, or asks whether an approach is feasible. Not for diagnosing bugs.
---

# Brainstorming Ideas Into Designs

Turn ideas into designs through collaborative dialogue: classify how much process the request
needs, understand the context, refine the idea, present a design, and get your human partner's
approval before implementation starts.

## The approval gate

Every path below ends with your human partner approving what you intend before you invoke an
implementation skill, write code, or scaffold anything. The artifact scales with the task: two
sentences in chat for a config change, a written spec for a new subsystem. The approval does
not scale. Small tasks are where unexamined assumptions waste the most work, and a design
presented and started in the same breath gives your human partner nothing to veto. Present, then stop
until you hear yes.

A yes approves the stage actually presented. On the architectural path, approving the idea or
the feature scope permits writing the spec, and approving the written spec permits invoking
writing-plans; neither approves an artifact that does not exist yet. Resume at the earliest
stage still missing its approval.

The approval that precedes the first write also settles where the work lives (see "Workspace"
below). Creating a branch or worktree is not implementation; it is where the spec, the plan,
and the code will land.

## Classify first

Before your first question, classify the request and say the classification out loud ("this
looks bounded, so I'll present a short design here rather than write a spec") so your human partner
can override it.

- **Spike**: a feasibility question ("can we...", "is it possible...", "quick and dirty is
  fine") whose output is an answer, not code you keep. Present the question and what you will
  try in 2-3 sentences, get a nod, then find out as cheaply as correctness allows. Report a
  recommendation; anything built stays labeled throwaway.
- **Bounded**: a well-scoped change to a flow that already exists in this repo, such as a new
  flag, a small endpoint, or a one-file fix. Bounded measures the repo, not your familiarity
  with the kind of app: if there is no existing flow to read and change, the task is not
  bounded. Ask the clarifying questions that matter, present a short design in chat (a few
  sentences to a few short paragraphs), and stop for approval. No spec file, no plan document.
- **Architectural**: new projects, new subsystems, changes that restructure how components fit
  together or alter interfaces others depend on. Full process: questions, approaches, sectioned
  design, written spec, then the writing-plans skill.

When in doubt between two paths, take the heavier one. The ratchet is one-way: hidden complexity
discovered mid-task upgrades the path (stop, say so, step up); nothing downgrades mid-task.
Each request gets its own classification and its own approval, including a follow-up to an
approved spike.

## Rationalizations

| Thought | Reality |
|---------|---------|
| "This is too simple to need a design" | Simple means a short design, not no design. Two sentences in chat, then approval. |
| "I'll call it bounded and skip the spec" | Reaching for a label to skip work is the doubt. Take the heavier path. |
| "The design is obvious, I'll start while they read it" | The gate is the approval, not the design's length. |
| "They told me not to ask questions, just do it" | Stating your intent in two sentences is not a question. It costs one message and catches the wrong assumption before the diff exists. |
| "Their message already contains the design and the approval" | A request is not an approval of your reading of it. Restate it in two sentences; if you read it right, the yes costs one word. |
| "They said the scope is fine, so I can start building" | They approved the scope, not a spec or plan they have not seen. Continue at the next stage of the path. |
| "I understand this kind of app, so it's bounded" | A new project has no existing flow. It is architectural. |
| "The spike works, so I'll keep the code" | A spike's output is an answer. Keeping the code is a new request. |
| "It grew, but I'm almost done" | Hidden complexity upgrades the path. Stop and say so. |
| "I'll commit the spec here and let execution branch off" | The spec is the feature's first commit. Written on main it stays there if the feature is dropped, and the branch created later starts without it unless someone remembers to cherry-pick. Choose the workspace before the first write. |

## Path checklists

Announce the path, create a task per item, complete them in order.

**Spike**
1. Explore project context, enough to frame the probe
2. Present question and probe plan, 2-3 sentences
3. Get approval (a nod is enough)
4. Investigate as cheaply as correctness allows
5. Report findings as a recommendation; label anything built as throwaway

**Bounded**
1. Explore project context: files, docs, recent commits
2. Ask clarifying questions, one at a time, only the ones that matter
3. Present a short design in chat: approach, files touched, testing, and where the work will
   live (worktree, new branch here, or this branch; see "Workspace")
4. Get approval: stop and wait for an explicit yes
5. Set up the chosen workspace with superpowers:using-git-worktrees (Isolate), then implement
   through the normal development workflow (TDD applies); no plan document

**Architectural**
1. Explore project context: files, docs, recent commits
2. Invoke the superpowers:domain-modeling skill (see "Domain modeling" below)
3. Ask clarifying questions, one at a time: purpose, constraints, success criteria
4. Propose 2-3 approaches with trade-offs and your recommendation
5. Present the design in sections scaled to their complexity; get approval after each section.
   The last section's approval ask also names where the work will live (see "Workspace")
6. Set up the chosen workspace with superpowers:using-git-worktrees (Isolate) before writing
   any file of this feature; an epic, when there is one, is already committed (see "Epics")
7. Write the spec to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`, together with the
   glossary terms and ADRs resolved along the way, and commit it. A feature of an epic starts
   with `> **Epic:** <epic path> § <letter>` directly under the title, and its Non-goals name
   other features by letter instead of restating their scope
8. Self-review the spec (below) and fix inline
9. Ask the user to review the written spec; wait for approval
10. Invoke the writing-plans skill. It is the only skill that follows an architectural
    brainstorm; frontend-design, mcp-builder, and other implementation skills come after the plan.

## Workspace

The first write to the repository is the spec on the architectural path and the first code
edit on the bounded path. The one exception is an epic (see "Epics"): it belongs to no single
feature, so it is written and committed before Isolate. Everything after the first write
(plan, code, fixes) belongs to the same feature, and finishing-a-development-branch merges or
discards them as one unit. So the workspace is chosen before that first write, not at
execution time: a spec committed on main stays on main if the feature is dropped, and the
branch or worktree made later has to be created from a HEAD that already carries it.

Do not add a separate question for it. Name your choice inside the approval ask you are
already making, with the alternatives in the same sentence, so a one-word yes covers both:

> "...If that looks right I'll do this on a new branch `todo-done-flag` in this checkout (or
> say worktree for `.worktrees/todo-done-flag`, or stay on `main`)."

Recommend a worktree when the checkout has uncommitted work or your human partner will keep
using it while this runs; a new branch in this checkout otherwise; staying only when the
current branch is already this feature's. A "stay" on main or master is the consent the
execution skills need to implement there, so they do not ask again. Once approved, invoke
superpowers:using-git-worktrees (its Isolate steps) and only then write the spec or the first
edit. Spikes skip this: their output is an answer, and anything built is throwaway.

## Domain modeling

Design conversations are where a project's vocabulary gets settled, and what is settled only
in chat is lost. On the architectural path, invoke superpowers:domain-modeling right after
exploring the project context and keep it active for the rest of the brainstorm: it challenges
vague or conflicting terms, stress-tests relationships with concrete scenarios, and records the
glossary (`CONTEXT.md`) and hard-to-reverse decisions (ADRs). Its write timing already fits
the approval gate: terms resolved inside an unapproved design are written once the design is
approved, alongside the spec. The trade-off chosen in step 4 is the usual ADR candidate; apply
domain-modeling's three-part test before creating one.

On the bounded path, invoke it only when the request uses a term that conflicts with an
existing `CONTEXT.md`. A new flag or a one-file fix does not change the domain model, and
loading the skill adds questions the task does not need. Spikes never invoke it: their output
is an answer, not a model.

## Understanding the idea

- Check the current project state first: files, docs, recent commits.
- Assess scope before detailed questions. If the request describes several independent
  subsystems ("a platform with chat, file storage, billing, and analytics"), say so and help
  decompose: what the independent pieces are, how they relate, what order to build them. Then
  brainstorm the first feature; each gets its own spec, plan, and implementation cycle (see
  "Epics").
- Find out why before proposing what. Knowing the genre of app does not tell you why your
  human partner wants it: who it is for, what they will do with it, what success looks like.
  When the request and context do not say, ask one focused question about purpose before
  proposing features or an approach. When they already say, do not ask again.
- Write your understanding back in a short note (intended outcome, constraints, success
  criteria) with what they said kept separate from what you assumed, and invite correction.
  The corrected note is the brief the design is checked against.
- One question per message. Prefer multiple choice when the options are known; open-ended is
  fine. Focus on purpose, constraints, and success criteria.

## Epics

An epic records a split so the features after the first are not lost when this conversation
ends. Its format is in `epic-format.md`.

**Writing one.** The split approval ask names the epic path and the base branch in the same
sentence, so one yes covers both. The base is the branch each feature branches from: normally
the current branch; on a feature branch (a split found after Isolate), the branch it was cut
from.

> "...If this split looks right I'll commit it as an epic at
> `docs/superpowers/epics/2026-10-08-handoff.md` on `dev` and start brainstorming A."

Your human partner may name another branch; use that one. On yes, read `epic-format.md`, write
the epic, `git add` only that file, and commit it on that branch. The epic is the only write
before Isolate: it belongs to no single feature, so dropping feature A must not drop it, and
feature B started before A merges must see it. Write nothing before the yes. Then brainstorm
feature A as usual; its workspace is chosen at A's design approval, from a HEAD that carries
the epic.

**Continuing one.** Only when the request carries an epic path; do not go looking for epics
otherwise, and treat a request without one as an ordinary brainstorm. Read `epic-format.md`,
read the epic, derive state, and report it in one line ("Epic handoff: A on `dev`, B on
`feat/shell-theme-b`, next is C"). Take the next feature, or the one the request names, and
warn if its dependencies are not on the base yet. Its workspace starts from the base, not from
the current branch when that is another feature's; give the base as the start point at Isolate.
Its Scope, its Decide when brainstormed items, and the Shared decisions are the starting brief;
write them back and invite correction as for any brief. Do not re-split and do not redo what
Findings records: read only the code this feature touches, then ask your first question.

## Exploring approaches (architectural)

- Propose 2-3 approaches with trade-offs. Lead with your recommendation and why.
- YAGNI ruthlessly: remove unnecessary features from every approach and from the design.

## Presenting the design (architectural)

- Scale each section to its complexity: a few sentences if straightforward, up to 200-300
  words if nuanced. Ask after each section whether it looks right so far.
- Cover architecture, components, data flow, error handling, and testing.
- Favor units with one clear purpose and well-defined interfaces, small enough to hold in
  context at once; that is where your own edits are most reliable.
- In an existing codebase, follow existing patterns. Where existing code has problems that
  affect this work (a file grown too large, tangled responsibilities), include targeted
  improvements in the design, the way a good developer improves code they are working in.
  Do not propose unrelated refactoring.

## After the design (architectural)

**Workspace.** Set up the approved workspace first with superpowers:using-git-worktrees
(Isolate). The spec is the feature's first commit and must land on the feature's branch.

**Spec.** Write the validated design to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
(the user's preferred location overrides this default). Write the glossary terms and ADRs that
domain-modeling resolved during the conversation in the same pass, then commit it all.

**Self-review.** Read the spec with fresh eyes and fix inline, no second pass:

1. Placeholders: any "TBD", "TODO", incomplete sections, or vague requirements?
2. Consistency: do sections contradict each other? Does the architecture match the features?
3. Scope: focused enough for a single implementation plan, or does it hold several features (see "Epics")?
4. Ambiguity: could a requirement be read two ways? Pick one and make it explicit.

**User review.** Then:

> "Spec written and committed to `<path>`. Please review it and let me know if you want to
> make any changes before we start writing out the implementation plan."

Wait. If they request changes, make them and re-run the self-review. Once approved, invoke
writing-plans.
