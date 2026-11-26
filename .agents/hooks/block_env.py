"""Block agent tool calls that would touch a .env file (templates are allowed).

Reads the hook payload (JSON) on stdin. It understands the payload shapes of
several agents by looking only at the fields that hold a path or a shell command.

This is a guardrail against accidents, not a sandbox: see README, ".env protection".
"""

import fnmatch
import json
import re
import shlex
import sys

ALLOWED_SUFFIXES = (".env.example", ".env.examples")
# Code expressions that end in ".env" but are not files.
NOT_FILES = {"process.env", "import.meta.env", "meta.env", "deno.env", "bun.env"}

PATH_KEYS = {
    "file_path", "filepath", "filePath", "path", "paths", "notebook_path", "uri",
    "glob", "include", "include_pattern",
    "AbsolutePath", "TargetFile", "SearchPath",
}
COMMAND_KEYS = {"command", "cmd", "CommandLine"}
# Probes that a wildcard must not be able to match.
GLOB_PROBES = (".env", ".env.local", ".env.production")


def is_env_file(value):
    name = re.split(r"[/\\]", value.strip().rstrip("/\\"))[-1].lower()
    if not name or name.endswith(ALLOWED_SUFFIXES) or name in NOT_FILES:
        return False
    if name == ".envrc" or name.startswith(".env.") or name.endswith(".env"):
        return True
    # Wildcards such as ".env*" or ".en?" (but not a bare ".*").
    if name.startswith(".e") and any(c in name for c in "*?["):
        return any(fnmatch.fnmatchcase(probe, name) for probe in GLOB_PROBES)
    return False


def tokenize(command):
    try:
        lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars="();<>|&`")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:  # unbalanced quotes: fall back to a rough split
        return re.split(r"[\s;|&<>()`'\"]+", command)


def env_in_command(command, depth=0):
    # apply_patch (Codex): only the file headers are paths, the rest is file content.
    if command.lstrip().startswith("*** Begin Patch"):
        headers = re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", command, re.M)
        return next((h for h in headers if is_env_file(h)), None)

    previous = ""
    for token in tokenize(command):
        # bash -c "cat .env"  /  eval "cat .env"
        if depth < 3 and previous in ("-c", "-lc", "eval"):
            hit = env_in_command(token, depth + 1)
            if hit:
                return hit
        previous = token
        # Quoted text with spaces (e.g. a commit message) is not a path.
        if any(c.isspace() for c in token):
            continue
        # Covers --env-file=.env, HEAD:.env, @.env and {.env,x}
        for part in re.split(r"[=:@{},$]", token):
            if is_env_file(part):
                return part
    return None


def find_env_access(node, key=None):
    if isinstance(node, dict):
        for k, v in node.items():
            hit = find_env_access(v, k)
            if hit:
                return hit
    elif isinstance(node, list):
        for item in node:
            hit = find_env_access(item, key)
            if hit:
                return hit
    elif isinstance(node, str):
        if key in COMMAND_KEYS:
            return env_in_command(node)
        if key in PATH_KEYS and is_env_file(node):
            return node
    return None


def tool_arguments(payload):
    """Return the part of the payload that describes what the tool will do."""
    if "tool_input" in payload:  # Claude Code, Codex, Gemini CLI, Cursor preToolUse, Devin
        args = payload["tool_input"]
    elif "toolCall" in payload:  # Antigravity
        args = payload["toolCall"].get("args", {})
    elif "toolArgs" in payload:  # GitHub Copilot
        args = payload["toolArgs"]
    else:  # Cursor beforeReadFile / beforeShellExecution (skip "content": it isn't a path)
        args = {k: v for k, v in payload.items() if k in PATH_KEYS | COMMAND_KEYS}
    return json.loads(args) if isinstance(args, str) and args.startswith("{") else args


def main():
    style = sys.argv[1] if len(sys.argv) > 1 else "claude"
    try:
        args = tool_arguments(json.load(sys.stdin))
        hit = find_env_access({"command": args} if isinstance(args, str) else args)
        reason = hit and (
            f"BLOCKED: '{hit}' looks like a .env file, which may hold secrets. "
            "Agents must not open or touch it. Use .env.example instead, or ask the "
            "student to do this step themselves. Don't try to get around this."
        )
    except Exception as error:  # fail closed
        reason = f"BLOCKED: the .env protection hook could not check this call ({type(error).__name__})."

    if style == "antigravity":
        print(json.dumps({"decision": "deny", "reason": reason} if reason else {"decision": "allow"}))
        return 0
    if reason:
        print(reason, file=sys.stderr)
        return 2
    if style == "cursor":
        print(json.dumps({"permission": "allow"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
