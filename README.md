# ai-engineering-master-lab 🧪

> [!WARNING]
> **Este no es un repositorio oficial de LIDR.** Es un proyecto de la comunidad hecho por estudiantes y para estudiantes. LIDR no lo mantiene ni lo respalda, y el feedback de la IA **no es una calificación**. Las instrucciones, las fechas de entrega y la evaluación oficiales vienen siempre del programa.

🌱 Un punto de partida limpio para tus ejercicios semanales, más un tutor 🧑‍🏫 que vive dentro del agente de programación que ya usas.

## Índice 🗺

- 🤔 [¿Por qué existe?](#por-qué-existe-)
  - 🔁 [El ciclo semanal](#el-ciclo-semanal-)
- 🚀 [Inicio rápido](#inicio-rápido-)
  1. 📥 [Consigue tu copia](#1-consigue-tu-copia-)
  2. 🌿 [Crea la rama de la sesión](#2-crea-la-rama-de-la-sesión-)
  3. 📝 [Añade el ejercicio](#3-añade-el-ejercicio-)
  4. 🔨 [Constrúyelo, haz commit y pide la revisión](#4-constrúyelo-haz-commit-y-pide-la-revisión-)
  5. 🎓 [Después de la clase en vivo](#5-después-de-la-clase-en-vivo-)
  6. 🔀 [(Opcional) Haz merge de las mejoras](#6-opcional-haz-merge-de-las-mejoras-)
- 🧠 [Cómo funcionan las skills](#cómo-funcionan-las-skills-)
  - 🔍 [`review-exercise`: antes de la sesión](#review-exercise-tu-tutor-antes-de-la-sesión-)
  - 🧩 [`live-gaps`: después de la sesión](#live-gaps-tu-tutor-después-de-la-sesión-)
  - ✨ [La rama `refine/session_XX`](#qué-es-la-rama-refinesession_xx-)
  - 📚 [Sobre la referencia de LIDR](#sobre-la-referencia-de-lidr-)
- 🔐 [Protección de `.env`](#protección-de-env-)
- 🤖 [Configuración según tu agente](#configuración-según-tu-agente-)
- 🔧 [Hazlo tuyo](#hazlo-tuyo-)

## ¿Por qué existe? 🤔

Había dos cosas por mejorar:

- 😕 **«Completado ✅» no es feedback.** Entregas un ejercicio y te enteras de que está aprobado, pero no de qué hiciste bien ni de qué deberías corregir.
- 🍝 **Hacer un fork del repo oficial no es empezar de cero.** Su `main` ya tiene el proyecto terminado, así que acabas peleándote con ramas huérfanas antes de escribir una línea de código.

Aquí, `main` no tiene código de la solución: solo documentación, enunciados y dos skills.

### El ciclo semanal 🔁

| Fase | Qué haces tú | Qué hace el lab |
|---|---|---|
| 📖 1. **Preparación** | Estudias y construyes el ejercicio previo a la sesión | `review-exercise` te da feedback detallado |
| 🎥 2. **Sesión en vivo** | Clase de 2 h: conceptos, solución de referencia y preguntas | Nada. Disfrútala 🙂 |
| 🔎 3. **Repaso posterior** | Comparas tu trabajo con lo construido en vivo | `live-gaps` muestra qué falta y por qué importa. Si quieres, también crea [`refine/session_XX`](#qué-es-la-rama-refinesession_xx-) para cerrar esas brechas |

## Inicio rápido 🚀

Necesitas un agente de programación para ejecutar las skills, además de Bash (en Windows, WSL o Git Bash) y Python 3 para el [hook de protección de `.env`](#protección-de-env-). Sin Python 3, el hook bloquea todas las llamadas a herramientas.

### 1. Consigue tu copia 📥

Haz clic en **Use this template** en GitHub (no hagas fork del repo de LIDR) y después:

```bash
git clone https://github.com/<tu-usuario>/<tu-repo>.git
cd <tu-repo>
```

### 2. Crea la rama de la sesión 🌿

Crea una rama para el ejercicio de la sesión actual. Puedes partir del punto que prefieras:

- 🆕 **`main`:** empiezas desde cero.
- ➡️ **`session_XX` (tu sesión anterior):** continúas desde tu ejercicio anterior.
- ✨ **`refine/session_XX` (tu sesión anterior):** continúas desde su versión refinada.
- 🎥 **Una rama en vivo de LIDR:** partes de la versión de la sesión en vivo del repo de LIDR. Las ramas de LIDR no incluyen los archivos del lab, así que recupéralos de tu `main`. Por ejemplo, para empezar la sesión 3 desde la clase en vivo de la sesión 2:

```bash
git fetch https://github.com/LIDR-academy-temp/ai-engineering.git session_2_live
git switch -c session_03 FETCH_HEAD
git checkout main -- .agents .claude .codex .cursor .gemini AGENTS.md CLAUDE.md .gitignore exercises reports/.gitkeep
git commit -m "chore: add lab files"
```

  Esto reemplaza el `CLAUDE.md` y el `.gitignore` raíz de LIDR por los del lab. Los nombres de las ramas de LIDR varían (`session_2_live`, `session_05_live`), así que confirma el nombre exacto en su repo. Las skills detectan este punto de partida y no cuentan el código de LIDR como trabajo tuyo.

### 3. Añade el ejercicio 📝

En la rama de la sesión, guarda el enunciado como `exercises/sXX_exercise.txt` (por ejemplo, `exercises/s03_exercise.txt`) y haz commit. No hace falta que esté en `main`. Los de S2 y S3 ya vienen incluidos.

### 4. Constrúyelo, haz commit y pide la revisión 🔨

Haz el ejercicio por tu cuenta y luego haz commit (la revisión solo lee el trabajo **commiteado**).

En tu agente:

```text
/review-exercise session_02
```

o simplemente di *«revisa mi ejercicio de la sesión 2»*. Consulta la [tabla de configuración](#configuración-según-tu-agente-).

### 5. Después de la clase en vivo 🎓

```text
/live-gaps session_02
```

Recibirás un informe y el agente te preguntará si quieres cerrar las brechas en `refine/session_02`. No se cambia nada a menos que digas que sí. Si aceptas, revisa el diff y haz commit en esa rama.

### 6. (Opcional) Haz merge de las mejoras 🔀

Tu siguiente sesión puede partir directamente de `refine/session_02`, así que el merge es opcional. Si quieres que `session_02` las incluya (dejará de ser tu entrega original, así que primero ponle un tag):

```bash
git switch session_02
git tag submission/session_02
git merge --no-ff refine/session_02
```

Mantén el código del proyecto **fuera de `main`**.

## Cómo funcionan las skills 🧠

### `review-exercise`: tu tutor antes de la sesión 🔍

- 📋 **Necesita:** una rama `session_XX` y `exercises/sXX_exercise.txt`. Si falta alguno, te explica cómo solucionarlo y se detiene.
- ⚙️ **Qué hace:** compara tu código commiteado con el ejercicio, su checklist y el ejercicio resuelto de LIDR.
- 📄 **Qué genera:** `reports/session_XX_review.md`, con un veredicto, lo que hiciste bien, el checklist, las mejoras ordenadas por prioridad y preguntas para reflexionar. Después te ofrece un recorrido paso a paso.
- 🤝 **Juego limpio:** las funcionalidades reservadas para la clase en vivo no te restan. Los puntos que requieren la aplicación en ejecución se marcan como «no verificados» en lugar de adivinarse.

### `live-gaps`: tu tutor después de la sesión 🧩

- 📋 **Necesita:** una rama `session_XX`, una vez hecha la clase en vivo. El archivo del ejercicio es opcional, pero ayuda a saber qué se pedía antes de la clase.
- ⚙️ **Qué hace:** compara tu código con la rama de la sesión en vivo de LIDR.
- 📄 **Qué genera:** `reports/session_XX_gaps_report.md`, que relaciona cada brecha con los archivos afectados, por qué importa y cómo cerrarla. Opcionalmente, cambios de código en `refine/session_XX`.

La revisión, el informe de brechas y la conversación con el tutor son **en español**. Git ignora los informes, así que se quedan en tu máquina y siguen ahí al cambiar de rama. Para versionar alguno en Git: `git add -f reports/<archivo>.md`.

#### ¿Qué es la rama `refine/session_XX`? ✨

Es una rama opcional para **mejorar tu ejercicio con lo aprendido en la clase en vivo**, sin tocar lo que entregaste. `session_XX` queda como registro de lo que hiciste por tu cuenta; `refine/session_XX` es ese mismo trabajo más las correcciones de las brechas.

- ⏰ **Cuándo se crea:** solo si dices que sí después de leer el informe de brechas. Pedir las correcciones en tu primera petición de `/live-gaps` no cuenta: el agente vuelve a preguntar y espera tu respuesta.
- 📍 **De dónde parte:** del commit de tu rama de sesión que se comparó. No puede haber cambios pendientes; si los hay, el agente te pide que hagas commit o stash primero.
- 📦 **Qué contiene:** solo las brechas que elijas (todas, o IDs concretos como `G1` y `G3`), adaptadas a tu estructura, tus nombres y tu proveedor de modelos. No copia el proyecto de LIDR encima del tuyo.
- ♻️ **Si ya existe:** el agente te pregunta si quieres continuar en ella o usar otro nombre, como `refine/session_XX_2`. Nunca la resetea ni la borra.
- 🏁 **Al terminar:** el agente muestra qué cambió y qué omitió o no pudo verificar, y pregunta antes de hacer commit. No hace push ni merge. Te quedas en la rama refine.

Para compararla con tu entrega, después del commit: `git diff session_XX refine/session_XX`. Tu siguiente sesión puede [partir de esta rama](#2-crea-la-rama-de-la-sesión-).

### Sobre la referencia de LIDR 📚

Las skills guardan una copia aparte y de solo lectura del [repo de LIDR](https://github.com/LIDR-academy-temp/ai-engineering) en `.lab-cache/`. No añade ningún remoto, rama ni commit a tu repo, y puedes borrarla cuando quieras.

> [!NOTE]
> Tu agente envía el código que lee a su proveedor de modelos. No metas secretos ni datos privados de clientes en tu proyecto.

## Protección de `.env` 🔐

Un hook impide que tu agente abra o toque archivos `.env`, para que tus claves de API no acaben en el chat ni en el proveedor del modelo. Cubre `.env`, `.env.local`, `prod.env`, `.envrc` y similares. Las plantillas `.env.example` y `.env.examples` están permitidas.

La comprobación está en [.agents/hooks/](.agents/hooks/), y cada agente tiene un pequeño archivo de configuración que la llama:

| Agente | Configuración | Estado |
|---|---|---|
| Claude Code | `.claude/settings.json` (hook y reglas de denegación para los nombres habituales) | ✅ Probado con v2.1.326 |
| Cursor | `.cursor/hooks.json` | 🧪 Sin probar |
| Codex CLI | `.codex/hooks.json`. Marca el proyecto como de confianza y aprueba el hook con `/hooks`: **no se ejecuta hasta que lo hagas** | 🧪 Sin probar |
| GitHub Copilot (VS Code) | Lee `.claude/settings.json`. Requiere una carpeta de confianza, y la configuración de tu organización puede desactivarlo | 🧪 Sin probar |
| Gemini CLI | `.gemini/settings.json` | 🧪 Sin probar |
| Antigravity | `.agents/hooks.json` | 🧪 Sin probar; su documentación no dice qué pasa si un hook falla |
| Devin Desktop | Lee `.claude/settings.json` | 🧪 Sin probar |

«Sin probar» significa que la configuración sigue la documentación de la herramienta, pero no la hemos ejecutado en ella. Para comprobar la tuya, crea un `.env` con un valor **falso** y pídele al agente que lo lea. Debería bloquearlo.

> [!IMPORTANT]
> Protege contra accidentes. No es un sandbox. Se le puede escapar una búsqueda en toda una carpeta (`grep -r CLAVE .`), un script que abra el archivo por su cuenta o un archivo que adjuntes o pegues tú en el chat. Los agentes sin soporte de hooks no están cubiertos.

Como los agentes no pueden tocar `.env`, haz tú los pasos como `cp .env.example .env` y rellenar tus claves.

## Configuración según tu agente 🤖

La única fuente de verdad es [AGENTS.md](AGENTS.md) junto con [.agents/skills/](.agents/skills/). Basado en la documentación de cada herramienta a noviembre de 2026. Estas herramientas cambian rápido y no hemos probado las skills en todas, así que los PR con correcciones son bienvenidos.

| Agente | Configuración extra | Cómo ejecutar la skill |
|---|---|---|
| Claude Code | Ninguna (ya incluida) | `/review-exercise session_02`, `/live-gaps session_02`, o pídelo con tus palabras |
| Cursor | Ninguna | Escribe `/` y elige la skill, o pídelo con tus palabras |
| Codex CLI | [Aprobar el hook](#protección-de-env-) | `$review-exercise session_02`, `$live-gaps session_02`, o `/skills` |
| GitHub Copilot (VS Code) | Ninguna | Menú `/` en el chat, o pídelo con tus palabras |
| Antigravity | Ninguna | `/live-gaps session_02`, o pídelo con tus palabras |
| Gemini CLI | Ninguna (ya incluida) | Pídelo con tus palabras; `/skills list` para comprobarlo |
| Windsurf / Devin Desktop | Ninguna | Pídelo con tus palabras |

### Claude Code 🟠

[CLAUDE.md](CLAUDE.md) solo importa `@AGENTS.md`. Claude Code busca las skills en `.claude/skills/`, así que el repo incluye enlaces simbólicos. Ejecuta `/skills` para comprobar que aparecen.

Si los enlaces simbólicos se rompieron (es habitual en Windows sin WSL o sin el modo de desarrollador), vuelve a crearlos:

```bash
rm -rf .claude/skills/review-exercise .claude/skills/live-gaps
mkdir -p .claude/skills
ln -s ../../.agents/skills/review-exercise .claude/skills/review-exercise
ln -s ../../.agents/skills/live-gaps       .claude/skills/live-gaps
```

¿No puedes usar enlaces simbólicos? Ejecuta `cp -r .agents/skills/review-exercise .agents/skills/live-gaps .claude/skills/` y vuelve a copiar después de cada cambio (no hagas commit de las copias en lugar de los enlaces).

### Cursor 🎯

Lee `.agents/skills/` directamente. Abre la raíz del repo y comprueba que el agente conoce `AGENTS.md`. Puede que también vea los enlaces de `.claude/skills/`; son los mismos archivos.

### OpenAI Codex CLI 💻

Lee `AGENTS.md` y `.agents/skills/` directamente. Inicia `codex` desde dentro del repo. La primera descarga del repo de LIDR necesita acceso a la red, así que apruébalo si el sandbox te lo pide.

### GitHub Copilot 🐙

VS Code lee `.agents/skills/`; usa el modo agente. No necesitas un `.github/copilot-instructions.md`. Si tu configuración ignora `AGENTS.md`, crea ese archivo con esta línea:

```markdown
Follow the instructions in AGENTS.md at the repository root.
```

### Gemini CLI / Antigravity 💎

Google reemplazó Gemini CLI por **Antigravity CLI** en junio de 2026. Antigravity lee `.agents/skills/` (ejecuta `/skills reload` después de añadir una).

¿Sigues usando Gemini CLI? También lee `.agents/skills/`, y el archivo [.gemini/settings.json](.gemini/settings.json) incluido le indica que cargue `AGENTS.md`. Te pide permiso antes de activar una skill.

### Windsurf (ahora Devin Desktop) y otros agentes 🌊

La documentación de Devin indica que lee `AGENTS.md` y `.agents/skills/`. Con cualquier otro agente compatible con `AGENTS.md` que no admita skills, di:

> Lee `.agents/skills/review-exercise/SKILL.md` y síguelo para la sesión 2.

## Hazlo tuyo 🔧

- 🌍 **Cambia el idioma.** El programa es para hispanohablantes, así que todo viene en español. Si lo prefieres en otro idioma, en tu copia cambia la regla **Language** de [AGENTS.md](AGENTS.md) y de los dos `SKILL.md`, traduce las plantillas de las carpetas `assets/` y traduce los README. En el `SKILL.md` de `review-exercise` cambia también los nombres de las prioridades y los veredictos, y en el de `live-gaps` los de las categorías y prioridades.
- 🎛️ **Ajusta el tutor.** Edita la personalidad, la exigencia o las prioridades en los archivos `SKILL.md`, o el formato de los informes en la carpeta `assets/` de cada skill.
- ➕ **Añade una skill.** Crea `.agents/skills/<nombre>/SKILL.md`:

  ```markdown
  ---
  name: quiz
  description: Pregúntame sobre los conceptos de una sesión. Úsala cuando el estudiante pida un quiz o quiera poner a prueba lo que entendió.
  ---

  Lee exercises/sXX_exercise.txt y haz 5 preguntas, una por una...
  ```

  El nombre de la carpeta debe coincidir con `name`, que solo admite minúsculas, números y guiones (sin guiones bajos). Los agentes usan `description` para decidir cuándo usar la skill. No reutilices el nombre de un comando integrado. Para Claude Code, añade el enlace: `ln -s ../../.agents/skills/quiz .claude/skills/quiz`. Después, inclúyela en `AGENTS.md`.

- 💡 **Ideas:** un tutor `python-expert` para estudiantes que vienen de otros lenguajes de programación, quizzes de conceptos, diagramas de arquitectura, preparación de entrevistas, críticas de prompts, «explícame este diff».
- 🤗 **Compártelo.** Abre un PR o publica tu fork para tus compañeros. Comparte las *skills*, no tus soluciones ni tus informes.

¡A construir! 🚀
