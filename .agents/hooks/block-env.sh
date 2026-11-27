#!/usr/bin/env bash
# Pre-tool hook entry point: stops coding agents from touching .env files.
#   block-env.sh [claude|cursor|antigravity]     (default: claude)
# Runs block_env.py with uv and Python 3.11 (uv downloads 3.11 if it's missing).
# Fails closed: if the check can't run, the tool call is blocked.
DIR="$(cd "$(dirname "$0")" && pwd)" || exit 2
if ! command -v uv >/dev/null 2>&1; then
  echo "BLOCKED: the .env protection hook needs uv. Install it and try again." >&2
  exit 2
fi
uv run --quiet --no-project --python 3.11 python -I "$DIR/block_env.py" "${1:-claude}" || exit 2
exit 0
