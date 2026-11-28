# ai-engineering-master-lab 🧪

> [!WARNING]
> **This is not an official LIDR repository.** It's a community project made by students and for students. LIDR doesn't maintain or endorse it, and the AI feedback **is not a grade**. Official instructions, due dates and grading always come from the program.

🌱 A clean starting point for your weekly exercises, plus a tutor 🧑‍🏫 that lives inside the coding agent you already use.

## Index 🗺

- 🤔 [Why does it exist?](#why-does-it-exist-)
  - 🔁 [The weekly cycle](#the-weekly-cycle-)
- 🚀 [Quick start](#quick-start-)
  1. 📥 [Get your copy](#1-get-your-copy-)
  2. 🌿 [Create the session branch](#2-create-the-session-branch-)
  3. 📝 [Add the exercise](#3-add-the-exercise-)
  4. 🔨 [Build it, commit, and request the review](#4-build-it-commit-and-request-the-review-)
  5. 🎓 [After the live class](#5-after-the-live-class-)
  6. 🔀 [(Optional) Merge the improvements](#6-optional-merge-the-improvements-)
- 🧠 [How the skills work](#how-the-skills-work-)
- 🔐 [`.env` protection](#env-protection-)
- 🤖 [Agent-specific setup](#agent-specific-setup-)

## Why does it exist? 🤔

Two things needed fixing:

- 🍝 **Forking the official repo doesn't mean starting from scratch.** Its `main` already has the finished project, so you end up fighting orphan branches before writing a line of code.
- 😕 **"Completed ✅" isn't feedback.** You submit an exercise and learn it's approved, but not what you did well or what to fix.

Here, `main` has no solution code or exercise prompts: only documentation and two skills.

### The weekly cycle 🔁

| Phase | What you do | What the lab does |
|---|---|---|
| 📖 1. **Preparation** | You study and build the pre-session exercise | `review-exercise` gives you detailed feedback |
| 🎥 2. **Live session** | 2-hour class: concepts, reference solution and questions | Nothing. Enjoy it 🙂 |
| 🔎 3. **Post-session review** | You compare your work with what was built live | `live-gaps` shows what's missing and why it matters. If you want, it also creates [`refine/session_XX`](.agents/TUTOR.md#what-is-the-refinesession_xx-branch-) to close those gaps |

## Quick start 🚀

You need a coding agent to run the skills ([set it up](#agent-specific-setup-) after cloning), plus Bash (on Windows, WSL or Git Bash) and [uv](https://docs.astral.sh/uv/). The lab scripts use Python 3.11 through uv, which downloads it if you don't have it. We also recommend enabling the [`.env` protection hook](#env-protection-), which also needs uv.

### 1. Get your copy 📥

Click **Use this template** on GitHub (don't fork LIDR's repo), then:

```bash
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>
```

### 2. Create the session branch 🌿

Create a branch for the current session's exercise. You can start from the point you prefer:

- 🆕 **`main`:** start from scratch.
- ➡️ **`session_XX` (your previous session):** continue from your previous exercise.
- ✨ **`refine/session_XX` (your previous session):** continue from its refined version.
- 🎥 **A LIDR live branch:** start from the live-session version in LIDR's repo. LIDR's branches don't include the lab files, so restore them from your `main`. For example, to start session 3 from the session 2 live class:

```bash
git fetch https://github.com/LIDR-academy-temp/ai-engineering.git session_2_live
git switch -c session_03 FETCH_HEAD
git checkout main -- .agents manuals README.md AGENTS.md CLAUDE.md .gitignore
git commit -m "chore: add lab files"
```

  This replaces LIDR's root `README.md`, `CLAUDE.md` and `.gitignore` with the lab's. Then move the LIDR code you'll start from into [`project/`](#where-your-work-goes-) with `git mv`. LIDR's branch names vary (`session_2_live`, `session_05_live`), so confirm the exact name in their repo. The skills detect this starting point and don't count LIDR's code as your work.

#### Where your work goes 📁

All your work goes inside **`project/`**: it's one product that grows session by session. The folder already exists on `main`, with a `.gitkeep`. Work inside it on your session branch.

```text
project/          your work
  README.md       how to run and test it
  .gitignore      your project's rules
  backlog.md      your notes, if you have any
  my-app/         your code, tests and dependency manifest
```

- Document in `project/` how to run the app and its tests.
- The exception is **`.github/`**: GitHub only reads workflows from the repo root, and it also counts as your work.
- The root `README.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore` and `sXX_exercise.txt` files belong to the lab. The review doesn't grade them, even if you edit them.
- If there are other new or changed files outside those folders, the agent asks whether they're part of your work.
- Got an earlier branch without `project/`? The agent explains this structure and asks before reviewing it where it is.

### 3. Add the exercise 📝

On the session branch, save the exercise prompt in the repo root as `sXX_exercise.txt`, with two digits (for example, `s03_exercise.txt`), and commit it. It doesn't need to be on `main`. Include the verification checklist and the note about the live session, if there is one: the review uses them to decide what to evaluate.

You can skip this step: if the file is missing, `review-exercise` asks you for the prompt, creates the file, and asks whether you want to commit it.

### 4. Build it, commit, and request the review 🔨

Do the exercise yourself inside [`project/`](#where-your-work-goes-), then commit (the review only reads **committed** work).

In your agent:

```text
/review-exercise session_02
```

or just say *"review my session 2 exercise"*. See the [configuration table](#agent-specific-setup-).

### 5. After the live class 🎓

```text
/live-gaps session_02
```

You'll get a report, and the agent will ask whether you want to close the gaps on `refine/session_02`. Nothing changes unless you say yes. If you accept, review the diff and commit on that branch.

### 6. (Optional) Merge the improvements 🔀

Your next session can start directly from `refine/session_02`, so merging is optional. If you want `session_02` to include them (it will stop being your original submission, so tag it first):

```bash
git switch session_02
git tag submission/session_02
git merge --no-ff refine/session_02
```

Keep the project code **out of `main`**.

## How the skills work 🧠

The tutor is two skills: `review-exercise` reviews your exercise before the live session, and `live-gaps` compares it afterwards with what was built in class. [The tutor guide](.agents/TUTOR.md) explains how each one works, what it values, the reports it generates, the `refine/session_XX` branch, and how to adapt it to your taste.

## `.env` protection 🔐

**We recommend enabling the hook** that stops your agent from opening or touching `.env` files, so your API keys don't end up in the chat or with the model provider. The scripts are in [`.agents/hooks/`](.agents/hooks/), but each agent needs its own local configuration: follow [how to enable it](manuals/agent-setup.md#env-protection-hook-) in the setup guide. **Without that configuration, nothing in the lab stops your agent from reading `.env`.**

With or without the hook, do the steps like `cp .env.example .env` and fill in your keys yourself.

## Agent-specific setup 🤖

Each agent is configured once per clone: for some, access to the skills and, as a recommendation, the `.env` hook. Follow [the agent setup guide](manuals/agent-setup.md), which also explains how to run the skills in each agent.

Happy building! 🚀
