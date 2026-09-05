#!/usr/bin/env bash
# Tests for scripts/task-brief: the brief carries the plan's Global
# Constraints plus exactly one task's text — no trailing plan sections, no
# neighbouring tasks, fenced headings ignored.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TASK_BRIEF="$REPO_ROOT/skills/subagent-driven-development/scripts/task-brief"

FAILURES=0
TEST_ROOT=""

pass() { echo "  [PASS] $1"; }
fail() {
    echo "  [FAIL] $1"
    FAILURES=$((FAILURES + 1))
}

cleanup() {
    if [[ -n "$TEST_ROOT" && -d "$TEST_ROOT" ]]; then
        rm -rf "$TEST_ROOT"
    fi
}

# brief PLAN N -> prints the brief's content (explicit OUTFILE so no git repo is needed)
brief() {
    local out="$TEST_ROOT/brief-$2.md"
    "$TASK_BRIEF" "$1" "$2" "$out" >/dev/null 2>"$TEST_ROOT/stderr-$2"
    cat "$out"
}

main() {
    echo "=== Test: task-brief ==="

    TEST_ROOT="$(mktemp -d)"
    trap cleanup EXIT

    cat > "$TEST_ROOT/plan.md" <<'PLAN'
# Feature Implementation Plan

**Spec:** docs/spec.md

## Global Constraints

- Go 1.22 minimum
- No new dependencies

---

## Task Structure

### Task 1: Alpha

Alpha body.

#### Step 1.1

```bash
# Task 2: this heading lives inside a fence
## Global Constraints inside a fence
```

Alpha tail.

### Task 2: Beta

Beta body.

### Task 10: Gamma

Gamma body.

## Self-Review

Trailing section that belongs to the plan, not to Task 10.
PLAN

    local b1 b2 b10
    b1="$(brief "$TEST_ROOT/plan.md" 1)"
    b2="$(brief "$TEST_ROOT/plan.md" 2)"
    b10="$(brief "$TEST_ROOT/plan.md" 10)"

    # --- Global Constraints travel with every brief ---
    if [[ "$b1" == *"- Go 1.22 minimum"* && "$b2" == *"- Go 1.22 minimum"* && "$b10" == *"- Go 1.22 minimum"* ]]; then
        pass "every brief starts with the plan's Global Constraints"
    else
        fail "every brief starts with the plan's Global Constraints"
    fi

    if [[ "$b1" == "## Global Constraints"* && "$b1" != *"---"* ]]; then
        pass "constraints come first and the closing --- rule is dropped"
    else
        fail "constraints come first and the closing --- rule is dropped"
        echo "    got: $(printf '%s' "$b1" | head -5)"
    fi

    # --- task boundaries ---
    if [[ "$b1" == *"Alpha body."* && "$b1" == *"Alpha tail."* && "$b1" == *"#### Step 1.1"* && "$b1" != *"Beta body."* ]]; then
        pass "task brief keeps its own subsections and stops at the next task"
    else
        fail "task brief keeps its own subsections and stops at the next task"
    fi

    if [[ "$b1" == *"# Task 2: this heading lives inside a fence"* && "$b1" != *"inside a fence"$'\n'*"Beta body"* ]]; then
        pass "headings inside fenced code blocks do not end the task"
    else
        fail "headings inside fenced code blocks do not end the task"
    fi

    if [[ "$b10" == *"Gamma body."* && "$b10" != *"Self-Review"* && "$b10" != *"Trailing section"* ]]; then
        pass "last task's brief excludes trailing plan sections"
    else
        fail "last task's brief excludes trailing plan sections"
        echo "    got: $b10"
    fi

    if [[ "$b1" != *"Gamma body."* && "$b10" != *"Alpha body."* ]]; then
        pass "Task 1 and Task 10 are not confused"
    else
        fail "Task 1 and Task 10 are not confused"
    fi

    if [[ "$b2" != *"Task Structure"* && "$b2" != *"Spec:"* ]]; then
        pass "plan header and section wrappers stay out of the brief"
    else
        fail "plan header and section wrappers stay out of the brief"
    fi

    # --- missing task ---
    local rc=0
    "$TASK_BRIEF" "$TEST_ROOT/plan.md" 7 "$TEST_ROOT/brief-7.md" >/dev/null 2>&1 || rc=$?
    if [[ "$rc" -eq 3 && ! -e "$TEST_ROOT/brief-7.md" ]]; then
        pass "unknown task exits 3 and leaves no file"
    else
        fail "unknown task exits 3 and leaves no file"
        echo "    exit: $rc"
    fi

    # --- constraints followed directly by a deeper Task heading (no --- rule) ---
    cat > "$TEST_ROOT/tight.md" <<'PLAN'
# Tight plan

## Global Constraints

- Python 3.11+

### Task 1: One

One body.

### Task 2: Two

Two body.
PLAN
    local t1 t2
    t1="$(brief "$TEST_ROOT/tight.md" 1)"
    t2="$(brief "$TEST_ROOT/tight.md" 2)"
    if [[ "$t1" == "## Global Constraints"* && "$t1" == *"- Python 3.11+"* && "$t1" == *"One body."* && "$t1" != *"Two body."* ]]; then
        pass "a deeper Task heading closes the constraints block"
    else
        fail "a deeper Task heading closes the constraints block"
        echo "    got: $t1"
    fi
    if [[ "$t2" == *"- Python 3.11+"* && "$t2" != *"One body."* && "$t2" == *"Two body."* ]]; then
        pass "later tasks in a tight plan get constraints without earlier tasks"
    else
        fail "later tasks in a tight plan get constraints without earlier tasks"
        echo "    got: $t2"
    fi

    # --- plan without constraints ---
    cat > "$TEST_ROOT/bare.md" <<'PLAN'
# Bare plan

## Task 1: Only

Only body.
PLAN
    local bare
    bare="$(brief "$TEST_ROOT/bare.md" 1)"
    if [[ "$bare" == "## Task 1: Only"* && "$bare" == *"Only body."* ]]; then
        pass "plan without Global Constraints yields the task text alone"
    else
        fail "plan without Global Constraints yields the task text alone"
        echo "    got: $bare"
    fi
    if grep -q "no 'Global Constraints' section" "$TEST_ROOT/stderr-1"; then
        pass "missing constraints are noted on stderr"
    else
        fail "missing constraints are noted on stderr"
    fi

    echo ""
    if [[ "$FAILURES" -ne 0 ]]; then
        echo "FAILED: $FAILURES assertion(s)."
        exit 1
    fi
    echo "PASS"
}

main "$@"
