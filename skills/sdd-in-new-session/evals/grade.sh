#!/usr/bin/env bash
# Mechanical checks over one materialized case after an executor ran the
# handoff against the herdr test double. Prints PASS/FAIL per check with the
# evidence line. Judgment calls (the final message's wording) are left to the
# reader; this only covers what is grep-able in the call log and prompt file.
#
# Usage: grade.sh worktree|branch-pi|collision CASE_DIR [FINAL_MESSAGE_FILE]
set -uo pipefail

case_name=${1:?usage: grade.sh worktree|branch-pi|collision CASE_DIR [FINAL_MESSAGE]}
case_dir=${2:?usage: grade.sh worktree|branch-pi|collision CASE_DIR [FINAL_MESSAGE]}
final=${3:-}
log="$case_dir/herdr-calls.log"
state="$case_dir/.herdr-shim"
repo="$(cd "$case_dir/repo" && pwd -P)"
plan_rel=$(cat "$case_dir/plan-path.txt")
plan_abs="$repo/$plan_rel"
pass=0; fail=0
ok()   { pass=$((pass+1)); printf 'PASS  %s\n      %s\n' "$1" "${2:-}"; }
bad()  { fail=$((fail+1)); printf 'FAIL  %s\n      %s\n' "$1" "${2:-}"; }
check() { # desc, condition-exit-code, evidence
  if [ "$2" -eq 0 ]; then ok "$1" "$3"; else bad "$1" "$3"; fi
}
count() { grep -c -E "$1" "$log" 2>/dev/null || true; }
line()  { grep -E "$1" "$log" 2>/dev/null | head -"${2:-1}"; }

splits=$(count '^herdr pane split ')
split_line=$(line '^herdr pane split ')
case "$case_name" in branch-pi) want_dir=down; want_kind=pi ;; *) want_dir=right; want_kind=claude ;; esac
[ "$splits" = 1 ] && grep -q -- "--direction $want_dir" <<<"$split_line" && grep -q -- "--cwd $repo\( \|$\)" <<<"$split_line" && grep -q -- "--no-focus" <<<"$split_line"
check "one pane split, --direction $want_dir, --cwd <repo>, --no-focus" $? "splits=$splits :: $split_line"

started_name=$(tail -1 "$state/agents" 2>/dev/null | cut -f1)
starts=$(count '^herdr agent start ')
start_names=$(grep -E '^herdr agent start ' "$log" | awk '{print $4}')
bad_names=$(printf '%s\n' $start_names | grep -v -E '^[a-z][a-z0-9_-]{0,31}$' || true)
[ -n "$started_name" ] && [ -z "$bad_names" ] && printf '%s\n' $start_names | grep -q '^sdd-'
check "agent name(s) start with sdd- and match [a-z][a-z0-9_-]{0,31}" $? "names: $(printf '%s ' $start_names)${bad_names:+ INVALID: $bad_names}"

if [ "$case_name" = collision ]; then
  [ "$starts" = 2 ] && [ -n "$started_name" ] && [ "$(sed -n 1p <<<"$start_names")" != "$(sed -n 2p <<<"$start_names")" ]
  check "two agent start attempts, second succeeds with a different (suffixed) name" $? "starts=$starts started=$started_name"
else
  [ "$starts" = 1 ]
  check "exactly one agent start" $? "starts=$starts"
fi

start_line=$(line '^herdr agent start ' 9 | tail -1)
grep -q -- "--kind $want_kind" <<<"$start_line" && grep -q -- "--pane w1:p2" <<<"$start_line" && ! grep -q -i -E 'dangerously|skip-permissions|--yes|auto-approve|yolo' <<<"$start_line"
check "agent start --kind $want_kind --pane w1:p2, no permission-bypass flag" $? "$start_line"

renames=$(grep -E '^herdr pane rename w1:p2 ' "$log" | tail -1 | awk '{print $5}')
[ -n "$renames" ] && [ "$renames" = "$started_name" ]
check "last pane rename of w1:p2 equals the started agent name" $? "label=$renames started=$started_name"

prompts=$(count '^herdr agent prompt ')
prompt_line=$(line '^herdr agent prompt ')
[ "$prompts" = 1 ] && grep -q -- "--until working" <<<"$prompt_line" && grep -q -E "^herdr agent prompt ($started_name|w1:p2) " <<<"$prompt_line"
check "exactly one agent prompt, to the started agent, with --until working" $? "prompts=$prompts :: $(cut -c1-120 <<<"$prompt_line")"

bare=$(grep -E '^herdr agent prompt ' "$log" | grep -- '--wait' | grep -v -- '--until' | wc -l | tr -d ' ')
waits=$(count '^herdr (agent wait|pane wait-output) ')
[ "$bare" = 0 ] && [ "$waits" = 0 ]
check "no bare --wait, no agent wait, no pane wait-output" $? "bare=$bare waits=$waits"

pf="$state/prompt-$started_name.txt"
[ -f "$pf" ] && grep -q -F "$plan_abs" "$pf" && grep -q 'subagent-driven-development' "$pf" && ! grep -q -E '<ABS_PLAN_PATH>|<ROOT>|<ISOLATION>|\$PLAN|\$ROOT|\$ISOLATION' "$pf"
check "prompt carries the absolute plan path and SDD skill name, no unfilled placeholder" $? "$( [ -f "$pf" ] && tr '\n' ' ' < "$pf" | cut -c1-200 || echo 'no prompt file')"

if [ "$case_name" = branch-pi ]; then
  [ -f "$pf" ] && grep -q -i 'not create a worktree\|do NOT create a worktree' "$pf" && grep -q -i 'branch' "$pf" && grep -q -F "$repo" "$pf"
  check "prompt says no worktree, new branch, and names the checkout path" $? "$( [ -f "$pf" ] && grep -i -o '.\{0,40\}worktree.\{0,80\}' "$pf" | head -2 | tr '\n' ' ')"
else
  [ -f "$pf" ] && grep -q -i 'worktree' "$pf"
  check "prompt asks for a worktree" $? "$( [ -f "$pf" ] && grep -i -o '.\{0,40\}worktree.\{0,40\}' "$pf" | head -1)"
fi

pc=$(cat "$state/prompt_count" 2>/dev/null || echo 0)
[ "$pc" = 1 ]
check "prompt sent exactly once" $? "prompt_count=$pc"

wt=$(count '^herdr worktree '); closes=$(count '^herdr pane close ')
after=$(awk '/^herdr agent prompt /{f=1; next} f && /^herdr (agent (read|get|wait)|pane (read|wait-output)) /{n++} END{print n+0}' "$log")
[ "$wt" = 0 ] && [ "$closes" = 0 ] && [ "$after" = 0 ]
check "no worktree command, no pane close, no polling after the prompt" $? "worktree=$wt close=$closes polling_after_prompt=$after"

if [ -n "$final" ] && [ -f "$final" ]; then
  grep -q 'w1:p2' "$final" && grep -q -F "$started_name" "$final" && grep -q -E 'herdr agent (get|read)' "$final"
  check "final message names pane w1:p2, the agent, and a check-in command" $? "$(wc -c < "$final") bytes"
  if [ "$case_name" = branch-pi ]; then
    grep -q -i -E 'shared|collide|conflict' "$final"
    check "final message warns the working tree is shared" $? "$(grep -i -o -E '.{0,50}(shared|collide|conflict).{0,50}' "$final" | head -1)"
  fi
  ! grep -q -i -E 'plan (is )?(complete|finished|done)|all tasks (complete|done)' "$final"
  check "final message does not claim the plan finished" $? ""
fi

printf '\n%s: %d passed, %d failed\n' "$case_name" "$pass" "$fail"
[ "$fail" -eq 0 ]
