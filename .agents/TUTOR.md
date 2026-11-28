# Tutor guide 🧑‍🏫

How the lab's skills work and how to adapt them. To install the lab and set up your agent, go back to the [README](../README.md).

## Index 🗺

- 🔍 [`review-exercise`: before the session](#review-exercise-your-tutor-before-the-session-)
- 🧩 [`live-gaps`: after the session](#live-gaps-your-tutor-after-the-session-)
- ✨ [The `refine/session_XX` branch](#what-is-the-refinesession_xx-branch-)
- 📚 [About the LIDR reference](#about-the-lidr-reference-)
- 🔧 [Make it yours](#make-it-yours-)

## `review-exercise`: your tutor before the session 🔍

- 📋 **Needs:** a `session_XX` branch and the exercise prompt in `sXX_exercise.txt`, in the repo root. If the branch is missing, it explains how to create it and stops. If the prompt is missing, it asks you to paste it, creates the file on your session branch, and asks whether you want to commit it.
- ⚙️ **What it does:** creates a rubric from the exercise and reviews your committed code against it. It compares the mandatory requirements and the architecture and design with LIDR's solved exercise; security and functionality are not compared.
- 📄 **What it generates:** `reports/session_XX_review.md`, with the verdict, what you did well, all findings (critical, important and nice to have) in detail, questions to reflect on, the rubric, the tests and the review context.
- 🗺️ **How to read the report:** start with the index, the verdict and the findings sorted by priority. At the end, "Detailed evaluation" explains each status emoji and shows the rubric table and the tests.
- 🏗️ **What it values:** design, architecture, prompts and good use of the stack. Using a model, provider or library different from the one in the exercise is not penalized if it fills the same role. Using it badly is flagged. The agent first creates a rubric from the exercise (`reports/sXX_rubric_*.json`) and reuses it while the exercise doesn't change, so two reviews of the same exercise are comparable.
- 🔑 **Possible keys:** if the scan finds something that could be a key and it can't be confirmed or ruled out, it's an important finding, not a critical one. It also appears as a note in the review context, so you can check the line. A committed secrets file is still critical.
- 🧪 **Tests:** if your project is well structured and documents how to run its tests, a subagent runs them on a temporary copy of the committed code, without your `.env` or your keys and without paid integration tests. It may install the dependencies you declare (it uses the network). This is code that runs on your machine: the copy is not a sandbox. If you started from LIDR's code, or the tests need something more (Docker, external services…), it asks you first. If a test fails, it reports the failure with its error, without retrying it or investigating the cause: if you want to go deeper, ask for it. If your agent can't start subagents, it gives you the commands instead.
- 🔍 **Unverified points:** if neither a test nor the code can check a point, the agent creates `reports/sXX_questions.md` and asks you a yes/no question about each one. "Yes" completes the item and "No" marks it as not met. The report shows it as "Confirmed by the student", and a "Yes" can lead to the verdict "Great job!", with a note saying so. If you don't know, answer "don't know": the item stays unverified and the report includes a note asking you to clarify it. Your answer never changes what a failing test or a defect in the code already shows.
- 🤝 **Fair play:** features reserved for the live class don't count against you. Points that need the running app are not guessed: they are asked about or left as unverified.

## `live-gaps`: your tutor after the session 🧩

- 📋 **Needs:** a `session_XX` branch, once the live class has happened. The exercise file is optional, but it helps to know what was asked before the class.
- ⚙️ **What it does:** compares your code with the LIDR live-session branch for that session.
- 📄 **What it generates:** `reports/session_XX_gaps_report.md`, which links each gap to the affected files, why it matters and how to close it. Optionally, code changes on `refine/session_XX`.

The review, the gaps report and the conversation with the tutor are all in **English**. Git ignores the reports, so they stay on your machine and remain there when you switch branches. To version one in Git: `git add -f reports/<file>.md`.

### What is the `refine/session_XX` branch? ✨

It's an optional branch to **improve your exercise with what you learned in the live class**, without touching what you submitted. `session_XX` stays as a record of what you did on your own; `refine/session_XX` is that same work plus the gap fixes.

- ⏰ **When it's created:** only if you say yes after reading the gaps report. Asking for fixes in your first `/live-gaps` request doesn't count: the agent asks again and waits for your answer.
- 📍 **Where it starts:** from the commit of your session branch that was compared. There must be no pending changes; if there are, the agent asks you to commit or stash first.
- 📦 **What it contains:** only the gaps you choose (all of them, or specific IDs such as `G1` and `G3`), adapted to your structure, your names and your model provider. It does not copy LIDR's project over yours.
- ♻️ **If it already exists:** the agent asks whether to continue on it or use another name, such as `refine/session_XX_2`. It never resets or deletes it.
- 🏁 **When it finishes:** the agent shows what changed and what it skipped or couldn't verify, and asks before committing. It doesn't push or merge. You stay on the refine branch.

To compare it with your submission, after committing: `git diff session_XX refine/session_XX`. Your next session can [start from this branch](../README.md#2-create-the-session-branch-).

## About the LIDR reference 📚

The skills keep a separate, read-only copy of the [LIDR repo](https://github.com/LIDR-academy-temp/ai-engineering) in `.lab-cache/`. It doesn't add any remote, branch or commit to your repo, and you can delete it whenever you want.

> [!NOTE]
> Your agent sends the code it reads to its model provider. Don't put secrets or private client data in your project.

## Make it yours 🔧

- 🎛️ **Tune the tutor.** Edit the personality, strictness or priorities in the `SKILL.md` files, or the report format: in `live-gaps`, in its `assets/` folder; in `review-exercise`, in `scripts/review_tool.py`.
- ➕ **Add a skill.** Create `.agents/skills/<name>/SKILL.md`:

  ```markdown
  ---
  name: quiz
  description: Quiz me on the concepts of a session. Use when the student asks for a quiz or wants to test what they understood.
  ---

  Read sXX_exercise.txt and ask me 5 questions, one at a time...
  ```

  The folder name must match `name`, which only allows lowercase letters, numbers and hyphens (no underscores). Agents use `description` to decide when to use the skill. Don't reuse the name of a built-in command. For Claude Code, add the link: `ln -s ../../.agents/skills/quiz .claude/skills/quiz`. Then list it in `AGENTS.md`.

- 💡 **Ideas:** a `python-expert` tutor for students coming from other programming languages, concept quizzes, architecture diagrams, interview preparation, prompt critiques, "explain this diff".
- 🤗 **Share it.** Open a PR or publish your fork for your classmates. Share the *skills*, not your solutions or your reports.
