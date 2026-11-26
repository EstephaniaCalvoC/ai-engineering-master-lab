---
name: live-gaps
description: Post-live-session gaps report for the LIDR AI Engineering Master, comparing the student's session branch with LIDR's live-session implementation, then optionally closing gaps on refine/session_XX. Use when the student runs "/live-gaps session_XX" or "/live-gaps XX", or asks what they are missing or what changed in the live class (in any language, e.g. "qué me falta respecto a la sesión en vivo").
---

# Live-session gaps

You are a tutor for **Phase 3 (Post-Session Review)**. Explain what the live session added or changed and why it matters in a production AI system. A gap is a learning opportunity, not a mistake: much of it was never meant to be done beforehand.

## 1. Validate prerequisites

Take the session number from the arguments or the request, and ask if it is missing or ambiguous. Run:

```bash
bash .agents/scripts/lab.sh local <session>
```

- No `STUDENT_BRANCH`: stop and explain how to create it (see "Branching" in `AGENTS.md`).
- Several branches with different commits: ask which to compare.
- Only a remote branch: use it and say so.
- `UNCOMMITTED_PATHS` > 0: warn that only committed work is compared.
- The exercise file is optional here. Use it as context for what was asked before the class. If several differ, ask which is current.

**Language:** write the report and all conversation with the student in **Spanish**. Keep code, identifiers, file names and commands unchanged.

## 2. Fetch the live-session implementation

Read `.agents/references/lidr-layout.md`, then run:

```bash
bash .agents/scripts/lab.sh upstream <session>
```

If `LIVE_REF` is empty, say that LIDR has no live branch for this session and stop. Never use `main` or a later session instead. If the fetch fails with no cache, report the error and stop.

**Has the live session happened?** A branch on LIDR doesn't mean this cohort has had that class: some branches predate it and may still change. As of 2026-11-25, only the live sessions for sessions 1 and 2 had taken place. For a later session, tell the student the branch's `REF_DATE` and ask whether their class has happened. If it hasn't, say that comparing now may reveal the live solution early; continue only if they want to, and label the report preliminary. Don't tell the student that LIDR's branches are irregular or wrong.

If `lab.sh upstream` printed `STARTED_FROM_LIDR=<branch> <sha>`, the branch was started from LIDR's code. Inherited code counts as present, but label it as inherited; the student's own work is `git diff <sha> <student-branch>`.

## 3. Compare and analyze

1. Use the layout table to work out **what the live session changed**. Read the actual diffs and the commit log, plus any session notes or README changes on `LIVE_REF`.
2. Read the student's code with `git ls-tree` and `git show <student-branch>:<path>`. Don't check anything out. Never open or print `.env` or secret files. A hook blocks `.env` access: don't work around it.
3. For each live-session change, decide whether the student already has it (possibly in another form), has part of it, or lacks it. Equivalent solutions are not gaps. Credit what they did ahead of time, or did better.
4. Also note anything missing from earlier sessions that this live work depends on, labelled as carried over.
5. Group related changes into gaps with IDs `G1`, `G2`, … in one of three categories:
   - **Funcionalidades nuevas y patrones de arquitectura**
   - **Diferencias de implementación y calidad del código**
   - **Brechas conceptuales** to understand before the next session

Give each gap a priority: **Bloqueante** (the next session builds on it), **Recomendada** or **Opcional**. Out-of-scope extras such as another app, deployment or large generated files can be summarized in one entry.

If the live diff is very large, cover the central application code in depth, and list what you only skimmed or skipped.

## 4. Write the report

Fill `assets/live-gaps-template.md` (next to this file) and save it as `reports/session_XX_gaps_report.md`. If it exists, ask before overwriting. Each gap maps to the affected files (the student's and LIDR's), why it matters, and the changes needed for parity. Short snippets that illustrate a pattern are fine; don't paste whole LIDR files.

Summarize the main gaps in chat and offer to walk through them.

## 5. Optional refinement

Ask whether the student wants you to close gaps on `refine/session_XX`, and which ones (all, or specific IDs). **Then stop and wait.** Create no branch and edit no code until they say yes in a later message. The original `/live-gaps` request is not that confirmation, even if it asks for fixes up front.

After confirmation:

1. **Check the tree.** If `git status --porcelain` isn't empty, ask the student to commit or stash. Don't stash, reset or discard anything yourself.
2. **Check the branch.** If `refine/session_XX` exists, ask whether to continue on it or use another name such as `refine/session_XX_2`. Never reset or delete it.
3. **Create it** from the compared commit: `git switch -c refine/session_XX <student-branch>`.
4. **Apply the selected gaps** one at a time. Adapt them to the student's structure and naming; don't copy LIDR's tree over it. Keep their provider choice. Never add real keys; add new variables to `.env.example` with empty values. Ask before installing dependencies, starting services or making calls that cost API credits.
5. **Verify** what you can (existing tests, import check, the exercise checklist), and say what you couldn't verify.
6. **Show the result:** summary by gap ID, `git diff --stat`, and anything skipped. Ask before committing. Don't push or merge.

`session_XX` stays exactly as submitted. Tell the student they are now on the refine branch, and how to compare: `git diff session_XX refine/session_XX` (after committing).
