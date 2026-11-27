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
- 🔐 [Protección de `.env`](#protección-de-env-)
- 🤖 [Configuración según tu agente](#configuración-según-tu-agente-)

## ¿Por qué existe? 🤔

Había dos cosas por mejorar:

- 🍝 **Hacer un fork del repo oficial no es empezar de cero.** Su `main` ya tiene el proyecto terminado, así que acabas peleándote con ramas huérfanas antes de escribir una línea de código.
- 😕 **«Completado ✅» no es feedback.** Entregas un ejercicio y te enteras de que está aprobado, pero no de qué hiciste bien ni de qué deberías corregir.

Aquí, `main` no tiene código de la solución ni enunciados: solo documentación y dos skills.

### El ciclo semanal 🔁

| Fase | Qué haces tú | Qué hace el lab |
|---|---|---|
| 📖 1. **Preparación** | Estudias y construyes el ejercicio previo a la sesión | `review-exercise` te da feedback detallado |
| 🎥 2. **Sesión en vivo** | Clase de 2 h: conceptos, solución de referencia y preguntas | Nada. Disfrútala 🙂 |
| 🔎 3. **Repaso posterior** | Comparas tu trabajo con lo construido en vivo | `live-gaps` muestra qué falta y por qué importa. Si quieres, también crea [`refine/session_XX`](.agents/TUTOR.md#qué-es-la-rama-refinesession_xx-) para cerrar esas brechas |

## Inicio rápido 🚀

Necesitas un agente de programación para ejecutar las skills ([configúralo](#configuración-según-tu-agente-) después de clonar), además de Bash (en Windows, WSL o Git Bash) y [uv](https://docs.astral.sh/uv/). Los scripts del lab usan Python 3.11 a través de uv, que lo descarga si no lo tienes. Te recomendamos también activar el [hook de protección de `.env`](#protección-de-env-), que también necesita uv.

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
git checkout main -- .agents manuals README.md AGENTS.md CLAUDE.md .gitignore
git commit -m "chore: add lab files"
```

  Esto reemplaza el `README.md`, el `CLAUDE.md` y el `.gitignore` raíz de LIDR por los del lab. Después, mueve con `git mv` el código de LIDR del que vayas a partir a [`project/`](#dónde-va-tu-trabajo-). Los nombres de las ramas de LIDR varían (`session_2_live`, `session_05_live`), así que confirma el nombre exacto en su repo. Las skills detectan este punto de partida y no cuentan el código de LIDR como trabajo tuyo.

#### Dónde va tu trabajo 📁

Todo tu trabajo va dentro de **`project/`**: es un solo producto que crece sesión a sesión. La carpeta ya existe en `main`, con un `.gitkeep`. Trabaja dentro de ella en tu rama de sesión.

```text
project/          tu trabajo
  README.md       cómo ejecutarlo y probarlo
  .gitignore      reglas de tu proyecto
  backlog.md      tus notas, si las tienes
  mi-app/         tu código, tests y manifiesto de dependencias
```

- Documenta en `project/` cómo ejecutar la app y sus tests.
- La excepción es **`.github/`**: GitHub solo lee los workflows desde la raíz del repo, y también cuenta como trabajo tuyo.
- El `README.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore` y los archivos `sXX_exercise.txt` de la raíz son del lab. La revisión no los evalúa, aunque los edites.
- Si hay otros archivos nuevos o modificados fuera de esas carpetas, el agente te pregunta si son parte de tu trabajo.
- ¿Tienes una rama anterior sin `project/`? El agente te explica esta estructura y te pregunta antes de revisarla donde está.

### 3. Añade el ejercicio 📝

En la rama de la sesión, guarda el enunciado en la raíz del repo como `sXX_exercise.txt`, con dos dígitos (por ejemplo, `s03_exercise.txt`), y haz commit. No hace falta que esté en `main`. Incluye el checklist de verificación y la nota sobre la sesión en vivo, si la hay: la revisión los usa para decidir qué evaluar.

Puedes saltarte este paso: si falta el archivo, `review-exercise` te pide el enunciado, lo crea y te pregunta si quieres hacer commit.

### 4. Constrúyelo, haz commit y pide la revisión 🔨

Haz el ejercicio por tu cuenta dentro de [`project/`](#dónde-va-tu-trabajo-) y luego haz commit (la revisión solo lee el trabajo **commiteado**).

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

El tutor son dos skills: `review-exercise` revisa tu ejercicio antes de la sesión en vivo y `live-gaps` lo compara después con lo construido en clase. En [la guía del tutor](.agents/TUTOR.md) tienes cómo funciona cada una, qué se valora, los informes que generan, la rama `refine/session_XX` y cómo adaptarlo a tu gusto.

## Protección de `.env` 🔐

**Te recomendamos activar el hook** que impide a tu agente abrir o tocar archivos `.env`, para que tus claves de API no acaben en el chat ni en el proveedor del modelo. Los scripts vienen en [`.agents/hooks/`](.agents/hooks/), pero cada agente necesita su propia configuración local: sigue [cómo activarlo](manuals/agent-setup.md#hook-de-protección-de-env-) en la guía de configuración. **Sin esa configuración, nada del lab impide que tu agente lea `.env`.**

Con o sin hook, haz tú los pasos como `cp .env.example .env` y rellenar tus claves.

## Configuración según tu agente 🤖

Cada agente se configura una vez en cada clon: en algunos, el acceso a las skills y, como recomendación, el hook de `.env`. Sigue [la guía de configuración de agentes](manuals/agent-setup.md), que también explica cómo ejecutar las skills en cada uno.

¡A construir! 🚀
