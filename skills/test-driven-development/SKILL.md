---
name: test-driven-development
description: Use when implementing any feature or bugfix, before writing implementation code
---

# Test-Driven Development

TDD is the red → green → refactor loop, run in vertical slices. Red comes first for one reason: a test you never saw fail may pass for any reason, so it proves nothing about the code. Watching it fail, for the reason you expected, is what turns a test into evidence.

This skill is the reference for every cycle: what a good test is, where tests go, the anti-patterns, and the rules of the loop.

## What a good test is

A good test checks behavior through a public interface and reads like a spec: `rejects an unknown coupon` says what the code promises, and it survives a rewrite of the internals.

- **It names the break it catches.** Before writing the body, name the production change that would make it fail: a wrong branch, a missing validation, an off-by-one boundary. A test that no realistic bug can fail checks nothing.
- **Its expected value comes from outside the code.** Use a literal or a worked example from the spec, never a value recomputed the way the code computes it.
- **It runs the real code.** Mock only system boundaries: network, clock, randomness, paid services. Before adding a mock, a test double, or a helper only tests use, or when the thing under test is a script or a document, read [writing-good-tests.md](writing-good-tests.md).

## Seams

A **seam** is the public boundary you test at: the function, endpoint, or command where behavior is observable without reaching inside. Before the first test, write down the seams you will test, one line each on what it catches. Choose them yourself; when you work from a plan, the task's interface is the seam.

## Anti-patterns

- **Implementation-coupled**: mocks your own collaborators, tests private functions, or verifies through a side channel (reading the database instead of calling the interface). The tell: it breaks on a refactor that kept the behavior.
- **Tautological**: the expected value restates the implementation (`assert add(a, b) == a + b`), so the test passes by construction.
- **Asserting on a mock**: the assertion checks that a mock exists or was called, not what the real code did.
- **Horizontal slicing**: all the tests first, then all the code. A batch written up front verifies imagined behavior, commits to a test structure before you understand the problem, and goes red for reasons you then untangle together. Work in **vertical slices** instead: each test is a **tracer bullet**, shaped by what the last cycle taught you.

## Rules of the loop

A **slice** is one pass through this loop, not a group of tests:

1. **Red.** Write one test, for the next behavior only. Run it and watch it fail with the message you expected: a failed assertion, not an import error or a typo.
2. **Green.** Write the least code that passes it, with no option or branch a test has not asked for. Run it again.
3. **Refactor**, only while green: remove duplication, improve names, extract helpers. Rerun after each change; the behavior stays the same.
4. **Next slice.** Back to red for the next behavior.

Each red run shows exactly one new failure: the test you just wrote. Two or more new failures in one run mean you wrote ahead, and those tests were shaped before the code taught you anything. A list of the behaviors you still have to cover is fine; their tests come one per slice.

When a rule depends on an earlier rule's result, give it a slice where both apply, with the expected value worked by hand: slices that each test one rule alone miss the order and the amount a rule is applied to.

A bug is a behavior too: its first red is a test that reproduces it.

The work is done when the project's whole suite is green. Run the repo's test command (bare `pytest`, `npm test`, `cargo test`), not only your file. A task that names one test file bounds what you deliver, not what you verify. Report every failure that run shows by name, including ones you did not cause.

## Code that has no test yet

Code without tests that already exists when you start (inherited, or written earlier without them) stays. For each behavior it has: write the test, break the code that produces the behavior (comment out the branch, flip the comparison), and watch the test go red; restore the code and watch it go green. That is red before green, applied to code that came first. The change you are making now still starts from its own red test.

## Exceptions

Throwaway prototypes, generated code, and configuration files: ask your human partner whether to test them.
