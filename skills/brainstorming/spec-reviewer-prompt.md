# Spec Reviewer Prompt Template

Use this template when dispatching the spec reviewer on the architectural path, after the
self-review and before your human partner reads the spec. The reviewer has no stake in the
design and time to check it against the code, which the author, at the end of a long
brainstorm, rarely spends.

**Purpose:** find where the spec is wrong about this codebase or its libraries, will not work
as written, or leaves out something the build needs.

```
Subagent (general-purpose):
  description: "Review spec against code"
  model: [MODEL: the session's own model; this review is judgment-heavy]
  prompt: |
    You are reviewing a design document before anyone plans or builds from it.
    You did not write it and cannot ask the person who did.

    Spec: [SPEC_PATH]
    Repository: [REPO_PATH]

    The spec makes claims about this codebase and the libraries it uses: what
    a function returns, what a migration can do, what a config option does,
    which tests touch what. Verify each claim that the design depends on
    against the source, including the installed library source. Where reading
    leaves a doubt, a small trial in a scratch directory outside the
    repository settles it.

    Then walk the design through the scenarios that apply to this project:
    - a fresh install following the README or setup docs
    - an upgrade of an existing installation and its data
    - the existing test suite: which tests break, which shared fixtures change
    - the main user flows, including the error and permission paths

    Also check the spec itself:
    - placeholders: "TBD", "TODO", incomplete sections, vague requirements
    - consistency: sections that contradict each other, an architecture that
      does not deliver the features
    - scope: more than one implementation plan's worth of work
    - ambiguity: a requirement a builder could read two ways

    Report every place where the spec is wrong, will not work as written, or
    leaves out something the build needs, including problems the builder
    could fix alone: the author fixes them in the spec now, before a plan is
    built on top. For each finding give where in the spec, what is wrong, the
    evidence (file:line in the repo or library, or what your trial showed),
    and the fix you suggest. If a fix needs a decision only the author's
    human partner can make (scope, product behaviour, a trade-off between
    stated goals), say so.

    Rank findings by how much they would change what gets built. List minor
    findings last, one line each. If nothing important is wrong, say
    "nothing important found".

    Do not modify the repository, and do not dispatch subagents. Your final
    message is the report: findings only, no preamble or summary.
```

**Placeholders:**
- `[SPEC_PATH]`: the spec file you just committed
- `[REPO_PATH]`: the repository root (the worktree, when the work lives in one)
- `[MODEL]`: the session's own model; say so explicitly on harnesses that require a model

**Reviewer returns:** findings ranked by impact, each with location, evidence, and a suggested
fix, decisions for your human partner marked; or "nothing important found".
