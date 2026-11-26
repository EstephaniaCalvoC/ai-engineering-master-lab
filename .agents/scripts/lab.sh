#!/usr/bin/env bash
# Shared helper for the `review-exercise` and `live-gaps` skills.
#
#   lab.sh local <session>      validate the student's branch and exercise file (offline)
#   lab.sh upstream <session>   refresh the LIDR cache and resolve the reference branches
#   lab.sh secrets <session>    look for committed secrets (prints locations, never values)
#
# <session> accepts 3, 03, s3, s03, session_3, session_03.
#
# Git hygiene: LIDR is mirrored into a separate bare repo under .lab-cache/.
# The student's repo gets no new remote, ref or object, and nothing is checked out.
set -euo pipefail

UPSTREAM_URL="${LIDR_UPSTREAM_URL:-https://github.com/LIDR-academy-temp/ai-engineering.git}"

die() { echo "ERROR: $*" >&2; exit 1; }

[ $# -eq 2 ] || die "usage: lab.sh local|upstream|secrets <session>"
CMD="$1"
RAW="$(printf '%s' "$2" | tr '[:upper:]' '[:lower:]')"
[[ "$RAW" =~ ^(session[_-]?|s)?([0-9]{1,2})$ ]] || die "cannot read a session number from '$2' (try: 3, 03, session_03)"
N=$((10#${BASH_REMATCH[2]}))
[ "$N" -ge 2 ] || die "exercises start at session 2 (session 1 is introductory)"
NN="$(printf '%02d' "$N")"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not inside a Git repository (run: git init -b main)"
cd "$ROOT"

# Local and remote branches that belong to this session (padded or not).
student_branches() {
  git for-each-ref --format='%(refname:short)' refs/heads refs/remotes |
    { grep -E "(^|/)session_0*${N}$" || true; } |
    { grep -vE '(^|/)refine/' || true; }
}

cmd_local() {
  echo "SESSION=$NN"
  echo "CURRENT_BRANCH=$(git branch --show-current)"

  # Reports and the cache are gitignored, so they never count as dirty.
  local dirty
  dirty="$(git status --porcelain | wc -l | tr -d ' ')"
  echo "UNCOMMITTED_PATHS=$dirty"

  # One line per matching branch. Two or more local matches means ambiguous.
  student_branches | while read -r b; do
    echo "STUDENT_BRANCH=$b $(git rev-parse --short "$b")"
  done

  if git show-ref --verify --quiet "refs/heads/refine/session_$NN"; then
    echo "REFINE_BRANCH=refine/session_$NN"
  fi

  # Exercise file: working tree, then the session branch, then main.
  local names=() p ref
  for p in "s$NN" "s$N"; do
    names+=("exercises/${p}_exercise.txt" "${p}_exercise.txt")
    [ "$N" -ge 10 ] && break
  done
  for p in "${names[@]}"; do
    [ -f "$p" ] && echo "EXERCISE=worktree:$p $(git hash-object "$p")"
  done
  local refs=("session_$NN")
  [ "$N" -lt 10 ] && refs+=("session_$N")
  refs+=(main)
  for ref in "${refs[@]}"; do
    git rev-parse --verify --quiet "refs/heads/$ref" >/dev/null || continue
    for p in "${names[@]}"; do
      if git cat-file -e "$ref:$p" 2>/dev/null; then
        echo "EXERCISE=$ref:$p $(git rev-parse "$ref:$p")"
      fi
    done
  done
}

cmd_upstream() {
  local cache="$ROOT/.lab-cache/lidr.git"
  if [ ! -d "$cache" ]; then
    git init --quiet --bare "$cache"
  fi
  if ! git --git-dir="$cache" fetch --quiet --no-tags --prune "$UPSTREAM_URL" \
    '+refs/heads/session_*:refs/heads/session_*'; then
    [ -n "$(git --git-dir="$cache" for-each-ref refs/heads)" ] ||
      die "could not fetch $UPSTREAM_URL and there is no cached copy"
    echo "WARNING=fetch failed; using the cached copy, which may be stale"
  fi

  # LIDR mixes padded and unpadded names (session_5 vs session_05_live).
  find_ref() { # <number> <suffix>
    git --git-dir="$cache" for-each-ref --format='%(refname:short)' refs/heads |
      { grep -E "^session_0*$1$2$" || true; }
  }
  one_ref() { # <number> <suffix>
    local m
    m="$(find_ref "$1" "$2")"
    [ "$(printf '%s' "$m" | grep -c .)" -le 1 ] || die "ambiguous LIDR branches for session $1$2: $(echo $m)"
    printf '%s' "$m"
  }

  local pre live base="" m
  pre="$(one_ref "$N" "")"
  live="$(one_ref "$N" "_live")"
  for ((m = N - 1; m >= 2; m--)); do
    base="$(one_ref "$m" "_live")"
    [ -n "$base" ] || base="$(one_ref "$m" "")"
    [ -z "$base" ] || break
  done

  echo "SESSION=$NN"
  echo "LIDR_GIT_DIR=$cache"
  echo "PRE_REF=$pre"
  echo "LIVE_REF=$live"
  echo "BASE_REF=$base"

  if [ -z "$pre" ] && [ -z "$live" ]; then
    echo "AVAILABLE=$(git --git-dir="$cache" for-each-ref --format='%(refname:short)' refs/heads | sort -V | tr '\n' ' ')"
    die "LIDR has no branch for session $NN"
  fi

  # Last commit date of each reference: helps judge which cohort published it.
  local ref
  for ref in "$pre" "$live"; do
    [ -z "$ref" ] || echo "REF_DATE=$ref $(git --git-dir="$cache" log -1 --format=%cs "$ref")"
  done

  # A student may start a branch from LIDR code. Report the newest LIDR commit
  # in their history, so inherited code isn't taken for their own work.
  local b inherited
  student_branches | while read -r b; do
    inherited="$(git rev-list "$b" |
      { grep -m1 -Fx -f <(git --git-dir="$cache" rev-list --all) || true; })"
    [ -z "$inherited" ] || echo "STARTED_FROM_LIDR=$b $inherited"
  done

  # If the live branch adds no real files on top of the pre-session branch,
  # pre-session and live work can't be told apart by branch name.
  if [ -n "$pre" ] && [ -n "$live" ]; then
    local changed
    changed="$(git --git-dir="$cache" diff --name-only "$pre" "$live" |
      { grep -vE '(^|/)\.gitignore$|\.md$' || true; } | grep -c . || true)"
    echo "PRE_TO_LIVE_CODE_FILES=$changed"
    if [ "$changed" -eq 0 ]; then
      echo "LAYOUT=merged"
    else
      echo "LAYOUT=split"
    fi
  elif [ -n "$pre" ]; then
    echo "LAYOUT=pre_only"
  else
    echo "LAYOUT=live_only"
  fi
}

# Prints file names and line numbers only. Template files are expected to exist.
cmd_secrets() {
  echo "SESSION=$NN"
  local b
  student_branches | while read -r b; do
    echo "SCANNED=$b"
    git ls-tree -r --name-only "$b" |
      { grep -E '(^|/)(\.env(\..+)?|[^/]+\.env|secrets\.toml)$' || true; } |
      { grep -vE '\.env\.examples?$' || true; } |
      sed "s|^|TRACKED_SECRET_FILE=$b:|"
    git log --format= --name-only "$b" -- '*.env' '*.env.*' '*secrets.toml' |
      { grep -vE '\.env\.examples?$' || true; } | sort -u |
      sed "/^$/d; s|^|SECRET_FILE_IN_HISTORY=$b:|"
    { git grep -nIE 'sk-(ant-|proj-)?[A-Za-z0-9_-]{20,}' "$b" -- . ':!.agents' || true; } |
      cut -d: -f1-3 | sed 's|^|POSSIBLE_KEY=|'
  done
}

case "$CMD" in
  local) cmd_local ;;
  upstream) cmd_upstream ;;
  secrets) cmd_secrets ;;
  *) die "unknown command '$CMD'" ;;
esac
