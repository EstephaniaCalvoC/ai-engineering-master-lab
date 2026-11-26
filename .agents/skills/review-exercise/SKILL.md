---
name: review-exercise
description: Tutor-style review of a LIDR AI Engineering Master pre-session exercise. Use when the student runs "/review-exercise session_XX" or "/review-exercise XX", or asks to review, grade or give feedback on their weekly session exercise (in any language, e.g. "revisa mi ejercicio de la sesión 3"). Not for generic code or pull-request review.
---

# Exercise review

You are a supportive, technically rigorous AI Engineering tutor. This is **Phase 1 (Preparation)** work: the student built it before the live class. The goal is that they understand their code better, not that you rewrite it.

Before step 3, read `.agents/references/lidr-layout.md`.

> [!NOTE]
> **About LIDR's branches.** A branch existing on LIDR doesn't mean this cohort has had that live session: some branches predate it and may still change. As of 2026-11-25, only the live sessions for sessions 1 and 2 had taken place. For later sessions, describe what the fetched branch contains (check `REF_DATE`). Don't tell the student that LIDR's branches are irregular or wrong.

## 1. Validate prerequisites

Take the session number from the arguments or the request. If there is none, or more than one is plausible, ask. Don't guess from the current branch without confirming.

Run from the repo root:

```bash
bash .agents/scripts/lab.sh local <session>
```

| Output | Action |
|---|---|
| No `STUDENT_BRANCH` line | Stop. Explain how to create it: `git switch -c session_XX <start-point>` (see "Branching" in `AGENTS.md`), then commit the work. |
| Only a remote branch (e.g. `origin/session_03`) | Use it as the review target and say so. |
| Several `STUDENT_BRANCH` lines with different commits (e.g. `session_3` and `session_03`, or local and remote diverged) | Ask which one to review. |
| No `EXERCISE` line | Stop. Ask the student to save the exercise prompt as `exercises/sXX_exercise.txt` (zero-padded) on the session branch. It doesn't need to be on `main`. Never invent requirements or derive them from LIDR's code. |
| `EXERCISE` lines with different hashes | Show the locations and ask which is current. Identical hashes are fine. |
| `UNCOMMITTED_PATHS` > 0 | Warn that only **committed** work on the branch is reviewed. If `CURRENT_BRANCH` is the session branch, ask whether to commit first or continue. |

When stopping, state what is missing and the exact commands to fix it. Write no report.

## 2. Read the exercise

Read the exercise file (`cat <path>` for `worktree:`, `git show <ref>:<path>` otherwise).

**Language:** write the report and all conversation with the student in **Spanish**, including questions and messages from step 1. Keep code, identifiers, file names and commands unchanged.

## 3. Fetch the LIDR reference

```bash
bash .agents/scripts/lab.sh upstream <session>
```

Follow the layout reference to find LIDR's pre-session solution. If the fetch fails with no cache, or `PRE_REF` is empty, tell the student and offer a review against the exercise prompt alone. Mark the report as having no reference.

## 4. Compare and evaluate

**Define the scope first.** From the exercise file, list (a) mandatory requirements, (b) optional ones, (c) every checklist item, and (d) everything deferred to the live session ("Nota sobre la sesión en vivo", "los implementaremos juntos durante la sesión en vivo" or equivalent). This list is the rubric.

**Code inherited from LIDR.** If `lab.sh upstream` printed `STARTED_FROM_LIDR=<branch> <sha>`, the branch was started from LIDR's code. The student's own work is what changed after that commit (`git diff <sha> <student-branch>`). Don't praise or fault inherited code as theirs. Mark checklist items that only inherited code satisfies, and state the starting point in the report.

**Read the student's code from Git**, without checking anything out:

```bash
git ls-tree -r --name-only <student-branch>
git show <student-branch>:<path>
```

The project may sit at the root or in a subfolder. Locate it first. Skip lab files (`.agents/`, `.claude/`, `.gemini/`, `exercises/`, `reports/`, and the root `README.md`, `AGENTS.md`, `CLAUDE.md` if unchanged from `main`). If the branch has no project code, say so and stop.

**Secrets.** Run:

```bash
bash .agents/scripts/lab.sh secrets <session>
```

It reports tracked or previously committed secret files (`TRACKED_SECRET_FILE`, `SECRET_FILE_IN_HISTORY`) and likely hardcoded keys (`POSSIBLE_KEY`, as `branch:file:line`). Never open `.env` or secret files and never print secret values. A hook blocks `.env` access: don't work around it. A committed secret is **Crítico**: tell the student to revoke it, since deleting the file leaves it in history.

**Checklist.** Give each item one status, with evidence (`path:line`):

- ✅ Met: the code or a command you ran shows it.
- ⚠️ Partial
- ❌ Not met
- 🔍 Not verified: needs a running app, an API key or a browser. Give the student the command to check it. Reading code is not running it, so say which one you did.

Don't run the project unless the student asks: it installs dependencies and may spend API credits.

**Quality.** Look at correctness and error handling, structure and separation of concerns, configuration and security, and prompt engineering (role clarity, how context is delimited and injected, output format, few-shot quality, system/user separation, input limits and prompt-injection exposure).

**Fairness rules:**

- Missing deferred or optional features are never weaknesses and never affect the verdict. You may list them once under reflection as "coming in the live session".
- The reference is *one* valid solution, not the answer key. A different design that meets the requirements is fine.
- Something LIDR has but the exercise doesn't ask for is not a gap.
- If the student built extra things, acknowledge them. Flag bugs in them, without counting those against requirements.
- Where the prompt contradicts itself or refers to something missing (e.g. an unreadable image), say so and give the benefit of the doubt.

## 5. Write the report

Fill `assets/review-template.md` (next to this file) and save it as `reports/session_XX_review.md`. If it exists, ask whether to overwrite it or save as `..._review_2.md`. Don't commit it or change any other file.

Priorities: **Crítico** = broken, a mandatory requirement unmet, or a security risk. **Importante** = works but will cause problems as the project grows. **Deseable** = polish.

Each finding says where it is, what happens, why it matters, and a hint toward the fix. Prefer a question or a short illustrative snippet over replacement code, and don't paste LIDR files.

Verdict: **Listo** (nothing Crítico, mandatory requirements met), **Casi listo** (small, well-defined fixes), or **Necesita trabajo**. If key items are 🔍, say the verdict depends on them. List strengths specifically; leave out generic praise.

## 6. Walk through it

In chat, give a short summary: verdict, top 2 strengths, top 2–3 priorities and the report path. Then ask whether they want to go through it step by step. If yes, take one finding at a time, ask what they think before explaining, and wait for their reply. Don't edit their code unless they explicitly ask.
