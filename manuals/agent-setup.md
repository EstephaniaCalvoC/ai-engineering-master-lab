# Agent-specific setup 🤖

[← Back to the README](../README.md)

The single source of truth is [AGENTS.md](../AGENTS.md) together with [.agents/skills/](../.agents/skills/). Based on each tool's documentation as of November 2026. Configuration is local to each agent: Git ignores `.claude/`, `.codex/`, `.cursor/` and `.gemini/` at the root. Create it once per clone. These tools change quickly and we haven't tested the skills in all of them, so PRs with corrections are welcome.

The table shows what's needed to use the skills. We also recommend [adding the `.env` hook](#env-protection-hook-) in any agent that supports it.

| Agent | Configuration for the skills | How to run the skill |
|---|---|---|
| Claude Code | [Links to the skills](#claude-code-) | `/review-exercise session_02`, `/live-gaps session_02`, or ask in your own words |
| Cursor | None | Type `/` and pick the skill, or ask in your own words |
| Codex CLI | None | `$review-exercise session_02`, `$live-gaps session_02`, or `/skills` |
| GitHub Copilot (VS Code) | None | `/` menu in the chat, or ask in your own words |
| Antigravity | None | `/review-exercise session_02`, `/live-gaps session_02`, or ask in your own words |
| Gemini CLI | [Context](#gemini-cli--antigravity-) | Ask in your own words; `/skills list` to check |
| Windsurf / Devin Desktop | None | Ask in your own words |

## `.env` protection hook 🔐

Recommended. It stops your agent from opening or touching `.env`, `.env.local`, `prod.env`, `.envrc` and similar files. The templates `.env.example` and `.env.examples` are allowed. It needs Bash and **uv** (it runs Python 3.11 and downloads it if you don't have it).

Add it in this order:

1. **Use the scripts** in `.agents/hooks/`, which come with the repo. Do this before step 2: if the configuration points to a script that doesn't exist, or uv is missing, the hook blocks tool calls.
2. **Connect it to your agent** using the configuration in its section.
3. **Test it:** create a `.env` with a **fake** value and ask the agent to read it. It should be blocked. Without an agent, from the repo root, `echo '{"tool_input":{"command":"cat .env"}}' | bash .agents/hooks/block-env.sh claude; echo $?` should print `2`.

The scripts in `.agents/hooks/` are in the repo, so they stay there when you switch branches. Git ignores `.agents/hooks.json` and your agent's configuration, which are local.

Each agent needs a configuration file that calls the scripts. Create only the one for your agent:

| File | Read by | What it contains |
|---|---|---|
| `.agents/hooks/block-env.sh` and `block_env.py` | All of them, through their configuration | The blocking logic. They need uv |
| `.claude/settings.json` | Claude Code (Copilot and Devin also read it) | The hook and `deny` read rules for the usual `.env` names |
| `.cursor/hooks.json` | Cursor | The hook on `preToolUse`, `beforeReadFile` and `beforeShellExecution` |
| `.codex/hooks.json` | Codex CLI | The hook. Mark the project as trusted and approve it with `/hooks` |
| `.gemini/settings.json` | Gemini CLI | The `BeforeTool` hook and the loading of `AGENTS.md` |
| `.agents/hooks.json` | Antigravity | The `PreToolUse` hook |

Git ignores all of these files except the scripts. If the hook can't find the scripts, it blocks every tool call: first check that your configuration's path matches the table. In Claude Code, the path uses `CLAUDE_PROJECT_DIR`, which Claude Code sets itself; if you test the command by hand from a subfolder, run it from the repo root.

The scripts are in the repo: [`.agents/hooks/block-env.sh`](../.agents/hooks/block-env.sh) and [`.agents/hooks/block_env.py`](../.agents/hooks/block_env.py). You don't need to copy them. If you change something, change it in those files.

| Agent | Hook configuration | Status |
|---|---|---|
| Claude Code | `.claude/settings.json` (hook and deny rules for the usual names) | ✅ Tested with v2.1.326 |
| Cursor | `.cursor/hooks.json` | 🧪 Untested |
| Codex CLI | `.codex/hooks.json`. Mark the project as trusted and approve the hook with `/hooks`: **it doesn't run until you do** | 🧪 Untested |
| GitHub Copilot (VS Code) | Reads `.claude/settings.json`. Requires a trusted folder, and your organization's configuration may disable it | 🧪 Untested |
| Gemini CLI | `.gemini/settings.json` | 🧪 Untested |
| Antigravity | `.agents/hooks.json` | 🧪 Untested; its documentation doesn't say what happens if a hook fails |
| Devin Desktop | Reads `.claude/settings.json` | 🧪 Untested |

"Untested" means the configuration follows the tool's documentation, but we haven't run it in that tool.

> [!IMPORTANT]
> It protects against accidents. It is not a sandbox. It can be bypassed by a search across a whole folder (`grep -r KEY .`), a script that opens the file on its own, or a file you attach or paste into the chat yourself. Agents without hook support are not covered.

## Claude Code 🟠

[CLAUDE.md](../CLAUDE.md) only imports `@AGENTS.md`.

Claude Code looks for skills in `.claude/skills/`, so create symbolic links from the repo root. The same commands also repair them:

```bash
rm -rf .claude/skills/review-exercise .claude/skills/live-gaps
mkdir -p .claude/skills
ln -s ../../.agents/skills/review-exercise .claude/skills/review-exercise
ln -s ../../.agents/skills/live-gaps       .claude/skills/live-gaps
```

Run `/skills` to check that they appear.

Can't use symbolic links? Run `cp -r .agents/skills/review-exercise .agents/skills/live-gaps .claude/skills/` and copy again after every change.

**`.env` hook (recommended):** with the scripts in `.agents/hooks/` already in place (see [the hook](#env-protection-hook-)), create `.claude/settings.json`:

```json
{
  "permissions": {
    "deny": [
      "Read(**/.env)",
      "Read(**/.env.local)",
      "Read(**/.env.development)",
      "Read(**/.env.staging)",
      "Read(**/.env.production)",
      "Read(**/.env.test)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PROJECT_DIR:-.}/.agents/hooks/block-env.sh\" || exit 2"
          }
        ]
      }
    ]
  }
}
```

If you don't want the hook, you can keep only the `permissions` block: it doesn't need the scripts, but it covers fewer cases.

## Cursor 🎯

Reads `.agents/skills/` directly. Open the repo root and check that the agent knows about `AGENTS.md`. If you also created the `.claude/skills/` links, it may see them too; they're the same files.

**`.env` hook (recommended):** with the scripts in `.agents/hooks/` already in place (see [the hook](#env-protection-hook-)), create `.cursor/hooks.json`:

```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [
      { "command": "bash .agents/hooks/block-env.sh cursor", "failClosed": true }
    ],
    "beforeReadFile": [
      { "command": "bash .agents/hooks/block-env.sh cursor", "failClosed": true }
    ],
    "beforeShellExecution": [
      { "command": "bash .agents/hooks/block-env.sh cursor", "failClosed": true }
    ]
  }
}
```

## OpenAI Codex CLI 💻

Reads `AGENTS.md` and `.agents/skills/` directly. Start `codex` from inside the repo. The first download of the LIDR repo needs network access, so approve it if the sandbox asks.

**`.env` hook (recommended):** with the scripts in `.agents/hooks/` already in place (see [the hook](#env-protection-hook-)), create `.codex/hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$(git rev-parse --show-toplevel)/.agents/hooks/block-env.sh\" || exit 2"
          }
        ]
      }
    ]
  }
}
```

Then mark the project as trusted and approve the hook with `/hooks`.

## GitHub Copilot 🐙

VS Code reads `.agents/skills/`; use agent mode. You don't need a `.github/copilot-instructions.md`. If your configuration ignores `AGENTS.md`, create that file with this line:

```markdown
Follow the instructions in AGENTS.md at the repository root.
```

For the `.env` hook, create `.claude/settings.json` as described in [Claude Code](#claude-code-). You don't need the links.

## Gemini CLI / Antigravity 💎

Google replaced Gemini CLI with **Antigravity CLI** in June 2026. Antigravity reads `.agents/skills/` (run `/skills reload` after adding one).

Still using Gemini CLI? It also reads `.agents/skills/` and asks your permission before activating a skill. To load `AGENTS.md` and use the [`.env` hook](#env-protection-hook-) (recommended; the scripts are already in `.agents/hooks/`), create `.gemini/settings.json`. Without the hook, keep only the `context` block:

```json
{
  "context": {
    "fileName": ["AGENTS.md", "GEMINI.md"]
  },
  "hooks": {
    "BeforeTool": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "name": "block-env",
            "type": "command",
            "command": "bash \"$GEMINI_PROJECT_DIR/.agents/hooks/block-env.sh\" || exit 2"
          }
        ]
      }
    ]
  }
}
```

**`.env` hook in Antigravity (recommended):** with the scripts in `.agents/hooks/` already in place (see [the hook](#env-protection-hook-)), create `.agents/hooks.json`:

```json
{
  "block-env": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          { "command": "bash \"$(git rev-parse --show-toplevel)/.agents/hooks/block-env.sh\" antigravity" }
        ]
      }
    ]
  }
}
```

## Windsurf (now Devin Desktop) and other agents 🌊

Devin's documentation says it reads `AGENTS.md` and `.agents/skills/`. For the `.env` hook, create `.claude/settings.json` as described in [Claude Code](#claude-code-). With any other agent that supports `AGENTS.md` but not skills, say:

> Read `.agents/skills/review-exercise/SKILL.md` and follow it for session 2.
