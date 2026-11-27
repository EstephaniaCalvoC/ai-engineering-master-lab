# Checking the student's security

This covers the `Security` rubric items (step 5 of `SKILL.md`). Don't compare them with LIDR.

## 1. Read the code

Read the student's committed code looking for security problems, in the `Security` items and beyond them.

Don't report missing endpoint authentication or rate limiting unless the exercise asks for it (the session 2 exercise doesn't).

## 2. Scan for secrets

The scan covers the whole branch, including lab files.

```bash
bash .agents/scripts/lab.sh secrets <session>
```

It reports tracked or previously committed secret files (`TRACKED_SECRET_FILE`, `SECRET_FILE_IN_HISTORY`) and likely hardcoded keys (`POSSIBLE_KEY`, as `branch:file:line`, with masked context). Never open `.env` or secret files and never print secret values. A hook blocks `.env` access: don't work around it. A committed secret is **Crítico**: tell the student to revoke it, since deleting the file leaves it in history.

## 3. Triage each `POSSIBLE_KEY` hit

Use the script's output and the file path only. Never open or print a flagged line, even masked by your own command. A line can have several `KEY_FACTS`: it is cleared only if each one passes the same rule below.

- **Part of a URL** (`inside_word=yes`, `in_url=yes` and `longest_run` under 16) → false positive.
- **Placeholder** (`placeholder_word=yes` and `longest_run` under 16, in a test, example or documentation file) → false positive.
- **Anything else** → an Importante finding, never Crítico, since it can't be ruled out or confirmed. Say that it's a possible key that wasn't confirmed, and tell the student to check the line and, if the key is real, to revoke it, since deleting it leaves it in history.

These rules apply to `POSSIBLE_KEY` only, not to `TRACKED_SECRET_FILE` or `SECRET_FILE_IN_HISTORY`.

## 4. Use the results

- An unconfirmed hit never makes a row `NOT_MET` or `PARTIAL` on its own. If it's the only thing keeping a secrets row from `MET`, mark the row `NOT_VERIFIED` and give the hit as the `reason`.
- Add one short entry to `context.notes` for each hit, with its location: the reason it was cleared, or that it's a possible key to check, with the revoke advice above.
- Add the `I` finding for each unconfirmed hit.
