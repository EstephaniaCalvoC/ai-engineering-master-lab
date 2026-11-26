#!/usr/bin/env bash
# Pre-tool hook entry point: stops coding agents from touching .env files.
#   block-env.sh [claude|cursor|antigravity]     (default: claude)
# Fails closed: if the check can't run, the tool call is blocked.
DIR="$(cd "$(dirname "$0")" && pwd)" || exit 2
for py in python3 python; do
  # "-c" also rules out the Windows Store placeholder, which exists but can't run.
  if "$py" -c 'import sys; sys.exit(sys.version_info[0] != 3)' >/dev/null 2>&1; then
    "$py" -I "$DIR/block_env.py" "${1:-claude}" || exit 2
    exit 0
  fi
done
echo "BLOCKED: the .env protection hook needs Python 3. Install it and try again." >&2
exit 2
