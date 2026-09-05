#!/usr/bin/env bash
# Materialize one eval case: a real git repo with a committed plan, a `herdr`
# test double on PATH, and an env.sh that makes a shell look like a Herdr pane.
# Nothing here talks to a real Herdr server.
#
#   worktree   wide pane, plan 2026-09-05-notes-tags.md, no flags
#   branch-pi  tall pane, same plan, invoked with --branch --pi
#   collision  wide pane, long plan slug, first `agent start` is rejected as
#              name_taken so the caller must retry with a suffix that still fits
#
# Usage: setup-case.sh worktree|branch-pi|collision DEST_DIR
set -euo pipefail

case_name=${1:?usage: setup-case.sh worktree|branch-pi|collision DEST_DIR}
dest=${2:?usage: setup-case.sh worktree|branch-pi|collision DEST_DIR}
here="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$dest/repo" "$dest/bin"
cp -R "$here/fixtures/repo/." "$dest/repo/"
cp "$here/fixtures/bin/herdr" "$dest/bin/herdr"
chmod +x "$dest/bin/herdr"

layout=wide
reject_first=0
plan="docs/superpowers/plans/2026-09-05-notes-tags.md"
case "$case_name" in
  worktree) ;;
  branch-pi) layout=tall ;;
  collision)
    reject_first=1
    long="docs/superpowers/plans/2026-09-05-add-tag-based-filtering-and-search-to-notes-cli.md"
    mv "$dest/repo/$plan" "$dest/repo/$long"
    plan=$long ;;
  *) echo "unknown case: $case_name" >&2; exit 2 ;;
esac

cd "$dest/repo"
git init -q -b main .
git -c user.email=eval@example.com -c user.name=eval -c commit.gpgsign=false add -A
git -c user.email=eval@example.com -c user.name=eval -c commit.gpgsign=false commit -qm "chore: notes-cli baseline with plan"

dest_abs="$(cd "$dest" && pwd -P)"
cat > "$dest_abs/env.sh" <<EOF
# Source this at the start of every shell command to be "inside Herdr", in the repo.
cd "$dest_abs/repo"
export HERDR_ENV=1
export HERDR_WORKSPACE_ID=w1
export HERDR_TAB_ID=w1:t1
export HERDR_PANE_ID=w1:p1
export PATH="$dest_abs/bin:\$PATH"
export HERDR_SHIM_LOG="$dest_abs/herdr-calls.log"
export HERDR_SHIM_STATE="$dest_abs/.herdr-shim"
export HERDR_SHIM_LAYOUT=$layout
export HERDR_SHIM_REJECT_FIRST_START=$reject_first
EOF
: > "$dest_abs/herdr-calls.log"
printf '%s\n' "$plan" > "$dest_abs/plan-path.txt"
echo "case=$case_name repo=$dest_abs/repo plan=$plan env=$dest_abs/env.sh"
