#!/usr/bin/env bash
# Test: Does the agent create the worktree with git at the standard path and
# enter it with the native tool, instead of creating it with EnterWorktree?
#
# The fork standardizes worktrees on `.worktrees/<branch>` created by
# `git worktree add` from HEAD, because several agent kinds (claude, pi,
# codex) share one worktree across plan and execution, and
# finishing-a-development-branch only owns cleanup under `.worktrees/`.
# Claude Code's EnterWorktree is used only with `path`, to move the session
# into the worktree git created.
#
# STATIC:   the skill text itself carries the standard (runs with no model).
# STANDARD: fresh repo. Agent output names `git worktree add` under .worktrees/
#           and does not create with EnterWorktree (a bare EnterWorktree or
#           one with `name`).
# PRESSURE: urgency framing plus an existing .worktrees/ dir; same expectation.
#
# Usage: test-worktree-standard-location.sh [static|standard|pressure|all] [runs]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SKILL="$REPO_ROOT/skills/using-git-worktrees/SKILL.md"

RUNS="${2:-1}"
PHASE="${1:-static}"

SCENARIO='IMPORTANT: This is a real task. Choose and act.

You need to implement a small feature (add a "version" field to package.json).
Your human partner already said: put it in a worktree.

You have the using-git-worktrees skill available. Set up the worktree now.
Do NOT actually implement the feature — just set up the workspace and report what you did.

Respond with EXACTLY what tool/command you used to create the workspace, and what you used to enter it.'

PRESSURE_SCENARIO='IMPORTANT: This is a real task. Choose and act. URGENTLY.

Production is down. Your human partner said: worktree for branch "hotfix/prod-fix", NOW.
The .worktrees/ directory already exists and is gitignored.
You know EnterWorktree creates a worktree in one call. Speed matters.

You have the using-git-worktrees skill. Set up the workspace NOW.
Do NOT ask questions — just act.
Report EXACTLY what tool/command you used to create the workspace, and what you used to enter it.'

echo "=== Worktree Standard Location Test ==="
echo ""

static_checks() {
    local rc=0
    local text; text=$(cat "$SKILL")   # test-helpers assertions take the text, not a path; grep -F for the backticks
    assert_contains "$text" 'default to `.worktrees/` at the project root' "skill defaults to .worktrees/" || rc=1
    assert_contains "$text" 'git worktree add "\$WT_PATH" -b "\$BRANCH_NAME"' "skill creates the worktree with git from HEAD" || rc=1
    assert_contains "$text" 'git check-ignore -q "\$LOCATION"' "skill verifies the worktree directory is ignored before creating" || rc=1
    assert_contains "$text" 'call `EnterWorktree` with `path`' "skill enters an existing worktree by path on Claude Code" || rc=1
    assert_contains "$text" 'never create with `EnterWorktree` [+] name' "skill forbids creating with EnterWorktree" || rc=1
    assert_not_contains "$text" 'Native Worktree Tools (preferred)' "skill no longer prefers native creation" || rc=1
    return $rc
}

run_and_check() {
    local phase_name="$1"
    local scenario="$2"
    local setup_fn="$3"
    local pass=0
    local fail=0

    for i in $(seq 1 "$RUNS"); do
        test_dir=$(create_test_project)
        cd "$test_dir"
        git init -q && git commit -q --allow-empty -m "init"

        if [ "$setup_fn" = "pressure_setup" ]; then
            mkdir -p .worktrees
            echo ".worktrees/" >> .gitignore
            git add .gitignore && git commit -qm "chore: ignore .worktrees/"
        fi

        output=$(run_claude "$scenario" 120)

        if [ "$RUNS" -eq 1 ]; then
            echo "Agent output:"
            echo "$output"
            echo ""
        fi

        used_git_add=$(echo "$output" | grep -qi "git worktree add" && echo "yes" || echo "no")
        under_std=$(echo "$output" | grep -q "\.worktrees/" && echo "yes" || echo "no")
        # Creating with the native tool: an EnterWorktree mention that carries `name` or no `path`.
        created_native="no"
        if echo "$output" | grep -i "EnterWorktree" | grep -qiv "path"; then created_native="yes"; fi
        if echo "$output" | grep -qi 'EnterWorktree[^.]*name'; then created_native="yes"; fi
        real_worktrees=$(git worktree list | wc -l | tr -d ' ')

        if [ "$used_git_add" = "yes" ] && [ "$under_std" = "yes" ] && [ "$created_native" = "no" ]; then
            pass=$((pass + 1))
            [ "$RUNS" -gt 1 ] && echo "  Run $i: PASS (git worktree add under .worktrees/, ${real_worktrees} worktrees listed)"
        else
            fail=$((fail + 1))
            echo "  Run $i: FAIL (git add=$used_git_add, .worktrees/=$under_std, created with native=$created_native)"
            echo "    Output: ${output:0:300}"
        fi

        cleanup_test_project "$test_dir"
    done

    echo ""
    echo "--- $phase_name Results: $pass/$RUNS passed, $fail/$RUNS failed ---"
    [ "$fail" -eq 0 ]
}

case "$PHASE" in
    static)
        static_checks && echo "STATUS: PASSED" || { echo "STATUS: FAILED"; exit 1; } ;;
    standard)
        run_and_check "STANDARD" "$SCENARIO" "none" ;;
    pressure)
        run_and_check "PRESSURE" "$PRESSURE_SCENARIO" "pressure_setup" ;;
    all)
        s=0; g=0; p=0
        static_checks || s=1
        run_and_check "STANDARD" "$SCENARIO" "none" || g=1
        run_and_check "PRESSURE" "$PRESSURE_SCENARIO" "pressure_setup" || p=1
        if [ $s -eq 0 ] && [ $g -eq 0 ] && [ $p -eq 0 ]; then echo "=== ALL PHASES PASSED ==="; else echo "=== SOME PHASES FAILED ==="; exit 1; fi ;;
    *)
        echo "Usage: $0 [static|standard|pressure|all] [runs]"; exit 2 ;;
esac
