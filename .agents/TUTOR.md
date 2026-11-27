# Guía del tutor 🧑‍🏫

Cómo funcionan las skills del lab y cómo adaptarlas. Para instalar el lab y configurar tu agente, vuelve al [README](../README.md).

## Índice 🗺

- 🔍 [`review-exercise`: antes de la sesión](#review-exercise-tu-tutor-antes-de-la-sesión-)
- 🧩 [`live-gaps`: después de la sesión](#live-gaps-tu-tutor-después-de-la-sesión-)
- ✨ [La rama `refine/session_XX`](#qué-es-la-rama-refinesession_xx-)
- 📚 [Sobre la referencia de LIDR](#sobre-la-referencia-de-lidr-)
- 🔧 [Hazlo tuyo](#hazlo-tuyo-)

## `review-exercise`: tu tutor antes de la sesión 🔍

- 📋 **Necesita:** una rama `session_XX` y el enunciado en `sXX_exercise.txt`, en la raíz del repo. Si falta la rama, te explica cómo crearla y se detiene. Si falta el enunciado, te pide que lo pegues, crea el archivo en tu rama de sesión y te pregunta si quieres hacer commit.
- ⚙️ **Qué hace:** crea una rúbrica a partir del ejercicio y revisa con ella tu código commiteado. Compara con el ejercicio resuelto de LIDR los requisitos obligatorios y la arquitectura y diseño; la seguridad y la funcionalidad no se comparan.
- 📄 **Qué genera:** `reports/session_XX_review.md`, con el veredicto, lo que hiciste bien, todos los hallazgos (críticos, importantes y deseables) en detalle, preguntas para reflexionar, la rúbrica, los tests y el contexto de la revisión.
- 🗺️ **Cómo leer el informe:** empieza con un índice, el veredicto y los hallazgos ordenados por prioridad. Al final, «Evaluación detallada» explica cada emoji de estado y muestra la tabla de la rúbrica y los tests.
- 🏗️ **Qué se valora:** el diseño, la arquitectura, los prompts y que uses bien el stack tecnológico. Usar un modelo, proveedor o librería distinto al del enunciado no resta si cumple la misma función. Usarlo mal sí se señala. El agente crea primero una rúbrica a partir del enunciado (`reports/sXX_rubric_*.json`) y la reutiliza mientras el enunciado no cambie, para que dos revisiones del mismo ejercicio se comparen bien.
- 🔑 **Posibles claves:** si el escaneo encuentra algo que podría ser una clave y no se puede confirmar ni descartar, es un hallazgo importante, no crítico. Aparece también como nota en el contexto de la revisión, para que revises la línea. Un archivo de secretos commiteado sigue siendo crítico.
- 🧪 **Tests:** si tu proyecto está bien estructurado y documenta cómo ejecutar sus tests, un subagente los ejecuta sobre una copia temporal del código commiteado, sin tu `.env` ni tus claves y sin tests de integración de pago. Puede instalar las dependencias que declares (usa la red). Es código que se ejecuta en tu máquina: la copia no es un sandbox. Si partiste de código de LIDR, o los tests requieren algo más (Docker, servicios externos…), te pregunta antes. Si un test falla, lo informa con su error, sin reintentarlo ni investigar la causa: si quieres profundizar, pídeselo. Si tu agente no admite subagentes, te da los comandos.
- 🔍 **Puntos sin verificar:** si ni un test ni el código permiten comprobar un punto, el agente crea `reports/sXX_questions.md` y te hace una pregunta de sí o no sobre cada uno. Con «Sí» queda cumplido y con «No», no cumplido. En el informe aparece como «Confirmado por el estudiante», y un «Sí» puede llevar al veredicto «¡Lo hiciste genial!», con una nota que lo indica. Si no lo sabes, responde «no sé»: sigue como «no verificado» y el informe incluye una nota para que lo aclares. Tu respuesta no cambia lo que ya demuestran un test que falla o un defecto en el código.
- 🤝 **Juego limpio:** las funcionalidades reservadas para la clase en vivo no te restan. Los puntos que requieren la aplicación en ejecución no se adivinan: se te preguntan o quedan como «no verificados».

## `live-gaps`: tu tutor después de la sesión 🧩

- 📋 **Necesita:** una rama `session_XX`, una vez hecha la clase en vivo. El archivo del ejercicio es opcional, pero ayuda a saber qué se pedía antes de la clase.
- ⚙️ **Qué hace:** compara tu código con la rama de la sesión en vivo de LIDR.
- 📄 **Qué genera:** `reports/session_XX_gaps_report.md`, que relaciona cada brecha con los archivos afectados, por qué importa y cómo cerrarla. Opcionalmente, cambios de código en `refine/session_XX`.

La revisión, el informe de brechas y la conversación con el tutor son **en español**. Git ignora los informes, así que se quedan en tu máquina y siguen ahí al cambiar de rama. Para versionar alguno en Git: `git add -f reports/<archivo>.md`.

### ¿Qué es la rama `refine/session_XX`? ✨

Es una rama opcional para **mejorar tu ejercicio con lo aprendido en la clase en vivo**, sin tocar lo que entregaste. `session_XX` queda como registro de lo que hiciste por tu cuenta; `refine/session_XX` es ese mismo trabajo más las correcciones de las brechas.

- ⏰ **Cuándo se crea:** solo si dices que sí después de leer el informe de brechas. Pedir las correcciones en tu primera petición de `/live-gaps` no cuenta: el agente vuelve a preguntar y espera tu respuesta.
- 📍 **De dónde parte:** del commit de tu rama de sesión que se comparó. No puede haber cambios pendientes; si los hay, el agente te pide que hagas commit o stash primero.
- 📦 **Qué contiene:** solo las brechas que elijas (todas, o IDs concretos como `G1` y `G3`), adaptadas a tu estructura, tus nombres y tu proveedor de modelos. No copia el proyecto de LIDR encima del tuyo.
- ♻️ **Si ya existe:** el agente te pregunta si quieres continuar en ella o usar otro nombre, como `refine/session_XX_2`. Nunca la resetea ni la borra.
- 🏁 **Al terminar:** el agente muestra qué cambió y qué omitió o no pudo verificar, y pregunta antes de hacer commit. No hace push ni merge. Te quedas en la rama refine.

Para compararla con tu entrega, después del commit: `git diff session_XX refine/session_XX`. Tu siguiente sesión puede [partir de esta rama](../README.md#2-crea-la-rama-de-la-sesión-).

## Sobre la referencia de LIDR 📚

Las skills guardan una copia aparte y de solo lectura del [repo de LIDR](https://github.com/LIDR-academy-temp/ai-engineering) en `.lab-cache/`. No añade ningún remoto, rama ni commit a tu repo, y puedes borrarla cuando quieras.

> [!NOTE]
> Tu agente envía el código que lee a su proveedor de modelos. No metas secretos ni datos privados de clientes en tu proyecto.

## Hazlo tuyo 🔧

- 🌍 **Cambia el idioma.** El programa es para hispanohablantes, así que todo viene en español. Si lo prefieres en otro idioma, en tu copia cambia la regla **Language** de [AGENTS.md](../AGENTS.md) y de los dos `SKILL.md`, traduce la plantilla de la carpeta `assets/` de `live-gaps`, los textos de los informes de `review-exercise` (en `scripts/review_tool.py`), los README y esta guía. En el `SKILL.md` de `review-exercise` cambia también los nombres de las prioridades y los veredictos, y en el de `live-gaps` los de las categorías y prioridades.
- 🎛️ **Ajusta el tutor.** Edita la personalidad, la exigencia o las prioridades en los archivos `SKILL.md`, o el formato de los informes: en `live-gaps`, en su carpeta `assets/`; en `review-exercise`, en `scripts/review_tool.py`.
- ➕ **Añade una skill.** Crea `.agents/skills/<nombre>/SKILL.md`:

  ```markdown
  ---
  name: quiz
  description: Pregúntame sobre los conceptos de una sesión. Úsala cuando el estudiante pida un quiz o quiera poner a prueba lo que entendió.
  ---

  Lee sXX_exercise.txt y haz 5 preguntas, una por una...
  ```

  El nombre de la carpeta debe coincidir con `name`, que solo admite minúsculas, números y guiones (sin guiones bajos). Los agentes usan `description` para decidir cuándo usar la skill. No reutilices el nombre de un comando integrado. Para Claude Code, añade el enlace: `ln -s ../../.agents/skills/quiz .claude/skills/quiz`. Después, inclúyela en `AGENTS.md`.

- 💡 **Ideas:** un tutor `python-expert` para estudiantes que vienen de otros lenguajes de programación, quizzes de conceptos, diagramas de arquitectura, preparación de entrevistas, críticas de prompts, «explícame este diff».
- 🤗 **Compártelo.** Abre un PR o publica tu fork para tus compañeros. Comparte las *skills*, no tus soluciones ni tus informes.
