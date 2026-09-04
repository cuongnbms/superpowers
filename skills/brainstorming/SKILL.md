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
| "I understand this kind of app, so it's bounded" | A new project has no existing flow. It is architectural. |
| "The spike works, so I'll keep the code" | A spike's output is an answer. Keeping the code is a new request. |
| "It grew, but I'm almost done" | Hidden complexity upgrades the path. Stop and say so. |

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
3. Present a short design in chat: approach, files touched, testing
4. Get approval: stop and wait for an explicit yes
5. Implement through the normal development workflow (TDD applies); no plan document

**Architectural**
1. Explore project context: files, docs, recent commits
2. Ask clarifying questions, one at a time: purpose, constraints, success criteria
3. Propose 2-3 approaches with trade-offs and your recommendation
4. Present the design in sections scaled to their complexity; get approval after each section
5. Write the spec to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` and commit it
6. Self-review the spec (below) and fix inline
7. Ask the user to review the written spec; wait for approval
8. Invoke the writing-plans skill. It is the only skill that follows an architectural
   brainstorm; frontend-design, mcp-builder, and other implementation skills come after the plan.

The visual companion (last section) is offered just-in-time on the architectural path, never
upfront.

## Understanding the idea

- Check the current project state first: files, docs, recent commits.
- Assess scope before detailed questions. If the request describes several independent
  subsystems ("a platform with chat, file storage, billing, and analytics"), say so and help
  decompose: what the independent pieces are, how they relate, what order to build them. Then
  brainstorm the first sub-project; each gets its own spec, plan, and implementation cycle.
- One question per message. Prefer multiple choice when the options are known; open-ended is
  fine. Focus on purpose, constraints, and success criteria.

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

**Spec.** Write the validated design to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
(the user's preferred location overrides this default) and commit it.

**Self-review.** Read the spec with fresh eyes and fix inline, no second pass:

1. Placeholders: any "TBD", "TODO", incomplete sections, or vague requirements?
2. Consistency: do sections contradict each other? Does the architecture match the features?
3. Scope: focused enough for a single implementation plan, or does it need decomposition?
4. Ambiguity: could a requirement be read two ways? Pick one and make it explicit.

**User review.** Then:

> "Spec written and committed to `<path>`. Please review it and let me know if you want to
> make any changes before we start writing out the implementation plan."

Wait. If they request changes, make them and re-run the self-review. Once approved, invoke
writing-plans.

## Visual companion

A browser-based tool for mockups, diagrams, and side-by-side visual options. It is a tool, not
a mode: accepting it means it is available for questions that benefit from being shown.

**Offer it just-in-time, never upfront.** The first time a question would be clearer shown than
described (a real mockup, layout, or diagram question, not merely a UI topic), offer it in its
own message with nothing else in it, and wait:

> "This next part might be easier if I show you — I can put together mockups, diagrams, and
> comparisons in a browser tab as we go. It's still new and can be token-intensive. Want me to?
> I'll open it for you."

If they decline, continue text-only and do not offer again unless they raise it. If no visual
question ever arises, never offer it.

**Per question, decide browser or terminal.** The test: would the user understand this better
by seeing it than reading it? Mockups, wireframes, layout comparisons, and architecture
diagrams go to the browser. Requirements, conceptual choices, trade-off lists, and scope
decisions stay in the terminal. "Which wizard layout works better?" is visual; "what does
personality mean here?" is not.

If they accept, read `visual-companion.md` in this skill's directory for the server workflow,
screen authoring, and feedback collection, then start the server with `--open`.
