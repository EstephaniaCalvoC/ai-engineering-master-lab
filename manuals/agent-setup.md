# Configuración según tu agente 🤖

[← Volver al README](../README.md)

La única fuente de verdad es [AGENTS.md](../AGENTS.md) junto con [.agents/skills/](../.agents/skills/). Basado en la documentación de cada herramienta a noviembre de 2026. La configuración de cada agente es local: Git ignora `.claude/`, `.codex/`, `.cursor/` y `.gemini/` en la raíz. Créala una vez en cada clon. Estas herramientas cambian rápido y no hemos probado las skills en todas, así que los PR con correcciones son bienvenidos.

La tabla muestra lo necesario para usar las skills. Además, te recomendamos [añadir el hook de `.env`](#hook-de-protección-de-env-) en cualquier agente que lo admita.

| Agente | Configuración para las skills | Cómo ejecutar la skill |
|---|---|---|
| Claude Code | [Enlaces a las skills](#claude-code-) | `/review-exercise session_02`, `/live-gaps session_02`, o pídelo con tus palabras |
| Cursor | Ninguna | Escribe `/` y elige la skill, o pídelo con tus palabras |
| Codex CLI | Ninguna | `$review-exercise session_02`, `$live-gaps session_02`, o `/skills` |
| GitHub Copilot (VS Code) | Ninguna | Menú `/` en el chat, o pídelo con tus palabras |
| Antigravity | Ninguna | `/review-exercise session_02`, `/live-gaps session_02`, o pídelo con tus palabras |
| Gemini CLI | [Contexto](#gemini-cli--antigravity-) | Pídelo con tus palabras; `/skills list` para comprobarlo |
| Windsurf / Devin Desktop | Ninguna | Pídelo con tus palabras |

## Hook de protección de `.env` 🔐

Recomendado. Impide que tu agente abra o toque `.env`, `.env.local`, `prod.env`, `.envrc` y similares. Las plantillas `.env.example` y `.env.examples` están permitidas. Necesita Bash y **uv** (ejecuta Python 3.11 y lo descarga si no lo tienes).

Se añade en este orden:

1. **Usa los scripts** de `.agents/hooks/`, que vienen en el repo. Hazlo antes del paso 2: si la configuración apunta a un script que no existe, o falta uv, el hook bloquea las llamadas a herramientas.
2. **Conéctalo con tu agente** usando la configuración de su sección.
3. **Pruébalo:** crea un `.env` con un valor **falso** y pídele al agente que lo lea. Debería bloquearlo. Sin agente, desde la raíz del repo, `echo '{"tool_input":{"command":"cat .env"}}' | bash .agents/hooks/block-env.sh claude; echo $?` debe imprimir `2`.

Los scripts de `.agents/hooks/` están en el repo, así que siguen ahí al cambiar de rama. Git ignora `.agents/hooks.json` y la configuración de tu agente, que son locales.

Cada agente necesita un archivo de configuración que llame a los scripts. Crea solo el de tu agente:

| Archivo | Lo lee | Qué contiene |
|---|---|---|
| `.agents/hooks/block-env.sh` y `block_env.py` | Todos, a través de su configuración | La lógica del bloqueo. Necesitan uv |
| `.claude/settings.json` | Claude Code (Copilot y Devin también lo leen) | El hook y las reglas `deny` de lectura para los nombres habituales de `.env` |
| `.cursor/hooks.json` | Cursor | El hook en `preToolUse`, `beforeReadFile` y `beforeShellExecution` |
| `.codex/hooks.json` | Codex CLI | El hook. Hay que marcar el proyecto como de confianza y aprobarlo con `/hooks` |
| `.gemini/settings.json` | Gemini CLI | El hook `BeforeTool` y la carga de `AGENTS.md` |
| `.agents/hooks.json` | Antigravity | El hook `PreToolUse` |

Git ignora todos estos archivos excepto los scripts. Si el hook no encuentra los scripts, bloquea todas las llamadas a herramientas: revisa primero que la ruta de tu configuración sea la de la tabla. En Claude Code, la ruta usa `CLAUDE_PROJECT_DIR`, que el propio Claude Code define; si pruebas el comando a mano desde una subcarpeta, ejecútalo desde la raíz del repo.

Los scripts están en el repo: [`.agents/hooks/block-env.sh`](../.agents/hooks/block-env.sh) y [`.agents/hooks/block_env.py`](../.agents/hooks/block_env.py). No hace falta copiarlos. Si cambias algo, hazlo en esos archivos.

| Agente | Configuración del hook | Estado |
|---|---|---|
| Claude Code | `.claude/settings.json` (hook y reglas de denegación para los nombres habituales) | ✅ Probado con v2.1.326 |
| Cursor | `.cursor/hooks.json` | 🧪 Sin probar |
| Codex CLI | `.codex/hooks.json`. Marca el proyecto como de confianza y aprueba el hook con `/hooks`: **no se ejecuta hasta que lo hagas** | 🧪 Sin probar |
| GitHub Copilot (VS Code) | Lee `.claude/settings.json`. Requiere una carpeta de confianza, y la configuración de tu organización puede desactivarlo | 🧪 Sin probar |
| Gemini CLI | `.gemini/settings.json` | 🧪 Sin probar |
| Antigravity | `.agents/hooks.json` | 🧪 Sin probar; su documentación no dice qué pasa si un hook falla |
| Devin Desktop | Lee `.claude/settings.json` | 🧪 Sin probar |

«Sin probar» significa que la configuración sigue la documentación de la herramienta, pero no la hemos ejecutado en ella.

> [!IMPORTANT]
> Protege contra accidentes. No es un sandbox. Se le puede escapar una búsqueda en toda una carpeta (`grep -r CLAVE .`), un script que abra el archivo por su cuenta o un archivo que adjuntes o pegues tú en el chat. Los agentes sin soporte de hooks no están cubiertos.

## Claude Code 🟠

[CLAUDE.md](../CLAUDE.md) solo importa `@AGENTS.md`.

Claude Code busca las skills en `.claude/skills/`, así que crea enlaces simbólicos desde la raíz del repo. Los mismos comandos sirven para repararlos:

```bash
rm -rf .claude/skills/review-exercise .claude/skills/live-gaps
mkdir -p .claude/skills
ln -s ../../.agents/skills/review-exercise .claude/skills/review-exercise
ln -s ../../.agents/skills/live-gaps       .claude/skills/live-gaps
```

Ejecuta `/skills` para comprobar que aparecen.

¿No puedes usar enlaces simbólicos? Ejecuta `cp -r .agents/skills/review-exercise .agents/skills/live-gaps .claude/skills/` y vuelve a copiar después de cada cambio.

**Hook de `.env` (recomendado):** con los scripts de `.agents/hooks/` ya en su sitio (ver [el hook](#hook-de-protección-de-env-)), crea `.claude/settings.json`:

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

Si no quieres el hook, puedes dejar solo el bloque `permissions`: no necesita los scripts, pero cubre menos casos.

## Cursor 🎯

Lee `.agents/skills/` directamente. Abre la raíz del repo y comprueba que el agente conoce `AGENTS.md`. Si también creaste los enlaces de `.claude/skills/`, puede que los vea; son los mismos archivos.

**Hook de `.env` (recomendado):** con los scripts de `.agents/hooks/` ya en su sitio (ver [el hook](#hook-de-protección-de-env-)), crea `.cursor/hooks.json`:

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

Lee `AGENTS.md` y `.agents/skills/` directamente. Inicia `codex` desde dentro del repo. La primera descarga del repo de LIDR necesita acceso a la red, así que apruébalo si el sandbox te lo pide.

**Hook de `.env` (recomendado):** con los scripts de `.agents/hooks/` ya en su sitio (ver [el hook](#hook-de-protección-de-env-)), crea `.codex/hooks.json`:

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

Después, marca el proyecto como de confianza y aprueba el hook con `/hooks`.

## GitHub Copilot 🐙

VS Code lee `.agents/skills/`; usa el modo agente. No necesitas un `.github/copilot-instructions.md`. Si tu configuración ignora `AGENTS.md`, crea ese archivo con esta línea:

```markdown
Follow the instructions in AGENTS.md at the repository root.
```

Para el hook de `.env`, crea `.claude/settings.json` como se indica en [Claude Code](#claude-code-). No necesitas los enlaces.

## Gemini CLI / Antigravity 💎

Google reemplazó Gemini CLI por **Antigravity CLI** en junio de 2026. Antigravity lee `.agents/skills/` (ejecuta `/skills reload` después de añadir una).

¿Sigues usando Gemini CLI? También lee `.agents/skills/` y te pide permiso antes de activar una skill. Para que cargue `AGENTS.md` y use el [hook de `.env`](#hook-de-protección-de-env-) (recomendado; los scripts ya están en `.agents/hooks/`), crea `.gemini/settings.json`. Sin el hook, deja solo el bloque `context`:

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

**Hook de `.env` en Antigravity (recomendado):** con los scripts de `.agents/hooks/` ya en su sitio (ver [el hook](#hook-de-protección-de-env-)), crea `.agents/hooks.json`:

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

## Windsurf (ahora Devin Desktop) y otros agentes 🌊

La documentación de Devin indica que lee `AGENTS.md` y `.agents/skills/`. Para el hook de `.env`, crea `.claude/settings.json` como se indica en [Claude Code](#claude-code-). Con cualquier otro agente compatible con `AGENTS.md` que no admita skills, di:

> Lee `.agents/skills/review-exercise/SKILL.md` y síguelo para la sesión 2.
