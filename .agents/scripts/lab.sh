#!/usr/bin/env bash
# Shared helper for the `review-exercise` and `live-gaps` skills.
#
#   lab.sh local <session>      validate the student's branch and exercise file (offline)
#   lab.sh upstream <session>   refresh the LIDR cache and resolve the reference branches
#   lab.sh secrets <session>    look for committed secrets (prints locations and masked
#                               context, never values)
#   lab.sh snapshot <session> [branch]
#                               copy a branch's committed files to a temp dir, without secret files
#
# <session> accepts 3, 03, s3, s03, session_3, session_03.
#
# Git hygiene: LIDR is mirrored into a separate bare repo under .lab-cache/.
# The student's repo gets no new remote, ref or object, and nothing is checked out.
set -euo pipefail

UPSTREAM_URL="${LIDR_UPSTREAM_URL:-https://github.com/LIDR-academy-temp/ai-engineering.git}"

die() { echo "ERROR: $*" >&2; exit 1; }

USAGE="usage: lab.sh local|upstream|secrets <session> | snapshot <session> [branch]"
[ $# -ge 2 ] || die "$USAGE"
CMD="$1"
BRANCH="${3:-}"
[ $# -eq 2 ] || { [ $# -eq 3 ] && [ "$CMD" = snapshot ]; } || die "$USAGE"
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
    names+=("${p}_exercise.txt")
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

# Turns `git grep -n` lines (ref:file:line:text) into locations plus masked context.
# No character of a hit is printed. Text after a hit is dropped, because it may hold
# the rest of a split key. Before it, only plain words and punctuation survive.
# (No regex intervals below: some awk versions don't support them.)
mask_key_hits() {
  LC_ALL=C awk '
    # Only short names in a single case, without digits or hyphens.
    function plain(w) {
      return length(w) <= 24 && w ~ /^_*(([a-z]+_*)+|([A-Z]+_*)+)$/ && w !~ /^(sk|ant|proj)$/
    }
    function redact(s,    out, w) {
      out = ""
      while (match(s, /[A-Za-z0-9_-]+/)) {
        w = substr(s, RSTART, RLENGTH)
        out = out substr(s, 1, RSTART - 1) (plain(w) ? w : "<x>")
        s = substr(s, RSTART + RLENGTH)
      }
      return out s
    }
    function longest_run(s,    n, i, part, max) {
      n = split(s, part, /[_-]/)
      max = 0
      for (i = 1; i <= n; i++) if (length(part[i]) > max) max = length(part[i])
      return max
    }
    function yn(c) { return c ? "yes" : "no" }
    {
      split($0, f, ":")
      loc = f[1] ":" f[2] ":" f[3]
      print "POSSIBLE_KEY=" loc
      rest = substr($0, length(loc) + 2)
      seen = ""
      while (match(rest, /sk-[A-Za-z0-9_-]+/)) {
        start = RSTART
        len = RLENGTH
        hit = substr(rest, start, len)
        before = seen substr(rest, 1, start - 1)
        seen = before hit
        rest = substr(rest, start + len)
        if (len < 23) continue

        body = substr(hit, 4)
        glued = before ~ /[A-Za-z0-9_-]$/
        url = before ~ /:\/\/[^ \t"\047<>]*$/
        facts = "length=" len " longest_run=" longest_run(body)
        facts = facts " digits=" yn(body ~ /[0-9]/) " uppercase=" yn(body ~ /[A-Z]/)
        facts = facts " inside_word=" yn(glued) " in_url=" yn(url)
        facts = facts " placeholder_word=" yn(tolower(body) ~ /fake|dummy|test|example|placeholder|your|xxxx/)

        # Whatever touches the hit belongs to the same token, so it is masked too.
        if (glued) { sub(/[A-Za-z0-9_-]+$/, "", before); tail = "<x>" } else tail = ""
        gsub(/:\/\/[^\/ ]*@/, "://<x>@", before)
        # Mask first, then shorten: cutting first could leave a fragment that looks plain.
        ctx = redact(before) tail "<KEY>"
        if (length(ctx) > 80) ctx = "..." substr(ctx, length(ctx) - 79)
        print "  KEY_FACTS=" facts
        print "  KEY_CONTEXT=" ctx
      }
    }'
}

# Never prints secret values. Template files are expected to exist.
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
      mask_key_hits
  done
}

# Committed files only, outside the repo, so tests can't reach the working tree or local secrets.
cmd_snapshot() {
  local branches b="$BRANCH" dir
  branches="$(student_branches)"
  if [ -z "$b" ]; then
    [ "$(printf '%s' "$branches" | grep -c .)" -eq 1 ] ||
      die "name the branch: lab.sh snapshot $NN <branch>"
    b="$branches"
  fi
  printf '%s\n' "$branches" | grep -qxF -- "$b" || die "'$b' is not a branch of session $NN"

  dir="$(mktemp -d "${TMPDIR:-/tmp}/lab-snapshot.XXXXXX")"
  git archive "$b" | tar -x -C "$dir"
  # Drop committed secret files, and absolute symlinks that could point back to real ones.
  find "$dir" \( -type f -o -type l \) \
    \( -name '.env' -o -name '.env.*' -o -name '*.env' -o -name '.envrc' -o -name 'secrets.toml' \) \
    ! -name '.env.example' ! -name '.env.examples' -delete
  find "$dir" -type l -lname '/*' -delete

  echo "SNAPSHOT_BRANCH=$b $(git rev-parse --short "$b")"
  echo "SNAPSHOT_DIR=$dir"
}

case "$CMD" in
  local) cmd_local ;;
  upstream) cmd_upstream ;;
  secrets) cmd_secrets ;;
  snapshot) cmd_snapshot ;;
  *) die "unknown command '$CMD'" ;;
esac
