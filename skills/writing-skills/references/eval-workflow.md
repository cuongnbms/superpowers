# Eval workflow (detailed)

Step-by-step mechanics for the loop in SKILL.md. Run every `python -m scripts.X` command from
the writing-skills directory (the base directory announced when this skill loads). Tooling
adapted from Anthropic's `skill-creator` plugin (Apache 2.0, see LICENSE.txt).

## Contents

- Workspace layout
- Step 1: spawn runs
- Step 2: draft assertions while runs are in progress
- Step 3: capture timing
- Step 4: grade, aggregate, launch the viewer
- Step 5: read feedback
- Iteration loop
- Blind comparison
- Description optimization
- Claude.ai and Cowork adaptations
- Packaging

## Workspace layout

Put results in `<skill-name>-workspace/` **outside the repo** (a scratchpad or temp dir), never
inside the skill directory. Organize by iteration, then eval, then configuration, then run:

```
<workspace>/
  skill-snapshot/                     # copy of the old version when improving an existing skill
  iteration-1/
    eval-0-<descriptive-name>/
      eval_metadata.json
      with_skill/run-1/outputs/       # plus grading.json and timing.json in run-1/
      without_skill/run-1/outputs/    # or old_skill/ when improving an existing skill
    eval-1-.../
    benchmark.json, benchmark.md
    feedback.json
  iteration-2/
```

The aggregator requires the `run-N/` level and a `summary` block in each grading.json (see
references/schemas.md). The viewer finds any directory containing `outputs/` and reads
`grading.json` from that directory or its parent.

Save test cases to `<skill>/evals/evals.json` (prompts first, assertions later). Keep input
fixtures under `<skill>/evals/fixtures/` so evals are reproducible, and reference them with
paths relative to `evals/`.

## Step 1: spawn runs (with-skill and baseline in the same turn)

For each test case, spawn two subagents at once so they finish together.

With-skill run prompt:

```
Execute this task.
First, read the skill at <path-to-skill>/SKILL.md and follow it. Do not load any other skill.
Task: <eval prompt>
Input files (read-only): <paths or "none">
Save outputs to: <workspace>/iteration-<N>/eval-<ID>-<name>/with_skill/run-1/outputs/
Outputs to save: <what the user cares about>
```

Baseline run: same prompt with no skill (new skill) or pointed at `skill-snapshot/`
(improving an existing skill), saving to `without_skill/` or `old_skill/`.

Write `eval_metadata.json` per eval with a descriptive `eval_name`, the prompt, and an empty
`assertions` list for now.

## Step 2: draft assertions while runs are in progress

Good assertions are objectively verifiable and read clearly in the viewer. Write a small
script for anything grep-able (heading present, forbidden phrase absent, count below N) and
leave judgment calls to a grader pass. Subjective qualities (style, design) are better judged
by the human in the viewer; do not force assertions onto them.

Watch for false positives in mechanical checks: a skill that *quotes* a forbidden phrase in
order to reject it will match a naive regex. Read every flagged match.

Update `eval_metadata.json` and `evals/evals.json` with the assertion texts.

## Step 3: capture timing

Each subagent completion notification carries `total_tokens` and `duration_ms`. Save them
immediately to `timing.json` in the run directory; they are not persisted anywhere else.

```json
{"total_tokens": 84852, "duration_ms": 23332, "total_duration_seconds": 23.3}
```

## Step 4: grade, aggregate, launch the viewer

1. Grade each run into `grading.json`. Use `agents/grader.md` for a grader subagent, or grade
   inline. Required fields per expectation: `text`, `passed`, `evidence`. Add a `summary`
   block: `{"total", "passed", "failed", "pass_rate"}`.
2. Aggregate:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
   Produces `benchmark.json` and `benchmark.md` with pass rate, time, and tokens per
   configuration, mean and stddev, and the delta.
3. Analyst pass: read `agents/analyzer.md` ("Analyzing Benchmark Results"). Look for
   assertions that pass regardless of skill (non-discriminating), high-variance evals (flaky),
   and time/token trade-offs. Aggregate stats hide the qualitative difference between two
   passing outputs; read both.
4. Launch the viewer:
   ```bash
   nohup python eval-viewer/generate_review.py <workspace>/iteration-N \
     --skill-name "<name>" --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   ```
   Add `--previous-workspace <workspace>/iteration-<N-1>` from iteration 2 on. It serves on
   a local port (check the process's listening port if the browser does not open). In headless
   environments use `--static <output.html>`.
5. Tell the user: the Outputs tab shows each test case with a feedback box; the Benchmark tab
   shows the numbers; "Submit All Reviews" writes `feedback.json`.

## Step 5: read feedback

`feedback.json` has one entry per run id. Empty feedback means fine. Focus on the cases with
specific complaints. Kill the viewer process when done.

## Iteration loop

1. Apply improvements to the skill.
2. Rerun all test cases into `iteration-<N+1>/`, including baselines.
3. Launch the viewer with `--previous-workspace`.
4. Wait for the user's feedback, read it, improve again.

Stop when the user is happy, feedback is all empty, or progress stalls. Then expand the test
set and run once more at larger scale.

## Blind comparison

When the question is "is the new version actually better?", give two outputs to an
independent agent without saying which is which (`agents/comparator.md`), then analyze why the
winner won (`agents/analyzer.md`). Optional; human review is usually enough.

## Description optimization

The description decides whether the skill triggers. After the body is stable:

1. **Generate 20 trigger eval queries**, half should-trigger and half should-not-trigger, as
   `[{"query": "...", "should_trigger": true}, ...]`. Queries must be realistic and specific:
   file paths, job context, column names, casual phrasing, typos, varied length. The valuable
   negatives are near-misses that share vocabulary with the skill but need something else.
   "Write a fibonacci function" as a negative for a PDF skill tests nothing.
2. **Review with the user.** Fill `assets/eval_review.html` (replace
   `__EVAL_DATA_PLACEHOLDER__`, `__SKILL_NAME_PLACEHOLDER__`,
   `__SKILL_DESCRIPTION_PLACEHOLDER__`), write it to a temp file, open it. The user edits and
   exports `eval_set.json` (lands in `~/Downloads`; take the newest).
3. **Run the loop** in the background (Claude Code only; it shells out to `claude -p`):
   ```bash
   python -m scripts.run_loop --eval-set <eval_set.json> --skill-path <skill-dir> \
     --model <model id powering this session> --max-iterations 5 --verbose
   ```
   It splits 60/40 train/test, evaluates the current description three times per query,
   proposes improvements from the failures, re-evaluates, and returns `best_description`
   chosen by held-out test score. Tail the output periodically to report progress.
4. **Apply** `best_description` to the frontmatter; show before/after and the scores.

Do not hand-add emphatic words to raise the trigger rate. Current models over-trigger on
them (see references/anthropic-best-practices.md, model notes). Let the measurement decide,
and prefer a more specific description or `disable-model-invocation: true` when the skill
fires on adjacent requests.

## Claude.ai and Cowork adaptations

**Claude.ai** (no subagents): run each test case yourself, one at a time, after reading the
skill. Skip baselines and quantitative benchmarking; present outputs inline and ask for
feedback. Description optimization needs the `claude` CLI, so skip it. Packaging works.

**Cowork** (subagents, no display): the main loop works; run test prompts in series if
timeouts bite. Generate the viewer with `--static` and give the user the file; feedback
downloads as `feedback.json`. Generate the viewer before forming your own opinion of the
outputs so the human sees them first.

**Updating an installed skill** from a read-only location: copy to a writable directory,
preserve the original `name`, edit and package the copy.

## Packaging

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

Validates frontmatter (`scripts/quick_validate.py`, needs PyYAML) and produces a `.skill`
archive. Only relevant when distributing outside a plugin.
