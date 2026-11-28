#!/usr/bin/env python3
"""PreToolUse hook: keep secrets and paid integration runs out of Claude's tool calls.

Exit code 2 blocks the call, and the stderr message is sent back to Claude.
The hook only sees Claude's own tool calls. Commands you run in your own terminal are not affected.
"""

import json
import re
import sys

# Matches .env and .env.integration, but not .env.example
SECRET_FILE = re.compile(r"\.env(\.integration)?(?![\w.-])")
INTEGRATION_RUN = re.compile(r"--run-integration")


def block(reason: str) -> None:
    print(f"Blocked by .claude/hooks/block_secrets.py: {reason}", file=sys.stderr)
    sys.exit(2)


def main() -> None:
    event = json.load(sys.stdin)
    tool = event.get("tool_name", "")
    data = event.get("tool_input") or {}

    if tool == "Bash":
        command = data.get("command", "")
        if SECRET_FILE.search(command):
            block("this command touches a .env file, which holds real API keys.")
        if INTEGRATION_RUN.search(command):
            block(
                "integration tests call real LLM APIs and cost money. Ask the user to run them."
            )

    elif tool in ("Read", "Edit", "Write", "NotebookEdit"):
        path = data.get("file_path") or data.get("notebook_path") or ""
        if SECRET_FILE.search(path):
            block("this file holds real API keys. Do not read or edit it.")

    elif tool in ("Grep", "Glob"):
        for key in ("path", "pattern", "glob"):
            if SECRET_FILE.search(data.get(key) or ""):
                block("searching .env files would expose real API keys.")

    sys.exit(0)


if __name__ == "__main__":
    main()
