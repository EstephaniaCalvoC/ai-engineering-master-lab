# System prompt log

Version history of the estimation system prompt. The text and examples for each version are in `app/context/estimation_<version>.json` (for example `estimation_1_0_0.json`).

Each estimate returns the version that produced it (`system_prompt_version`). The active version is `ACTIVE_PROMPT_VERSION` in `app/context/estimation_system_prompt.py`. Evals can load any version with `load_system_prompt(version)`.

When you change the prompt or the examples:

1. Add a new JSON file named after the new version (for example `estimation_1_1_0.json`). Do not edit an existing version file, so old estimates stay traceable.
2. Choose the version (semver: major for a change in the output contract, minor for a new instruction or example, patch for wording), and set `ACTIVE_PROMPT_VERSION` if it should be live.
3. Add an entry at the top of this log with the version, the date, and what changed and why.

## 1.2.7 (2026-11-21)

- Adds an eighth example: a discovery call for LácteosSur (plant monitoring and HACCP station), with a 13-phase estimate of 1800 hours over 24–30 weeks. Stored in `estimation_1_2_7.json`.
- Template and `render_format` (`"json"`) unchanged from 1.2.0. Not set as the active version.

## 1.2.6 (2026-11-21)

- Adds a discovery call for Clínica Sonríe (marketing website with CMS), with a 6-phase estimate of 110 hours over 3–4 weeks. Stored in `estimation_1_2_6.json`.
- Template and `render_format` unchanged from 1.2.0. Not set as the active version.

## 1.2.5 (2026-11-21)

- Adds a discovery call for Seguros Andina (policy administration system modernization), with a 9-phase estimate of 2408 hours over 30–36 weeks. Stored in `estimation_1_2_5.json`.
- Template and `render_format` unchanged from 1.2.0. Not set as the active version.

## 1.2.4 (2026-11-21)

- Adds a discovery call for Mercado Verde (retail analytics platform), with a 9-phase estimate of 1405 hours over 16–20 weeks. Stored in `estimation_1_2_4.json`.
- Template and `render_format` unchanged from 1.2.0. Not set as the active version.

## 1.2.3 (2026-11-21)

- Adds a discovery call for Studio Ritmo (class booking mobile app), with a 9-phase estimate of 1102 hours over 14–17 weeks. Stored in `estimation_1_2_3.json`.
- Template and `render_format` unchanged from 1.2.0. Not set as the active version.

## 1.2.2 (2026-11-21)

- Adds a discovery call for RutaFix (multi-tenant SaaS rebuild), with a 13-phase estimate of 2055 hours over 24–28 weeks. Stored in `estimation_1_2_2.json`.
- Template and `render_format` unchanged from 1.2.0. Not set as the active version.

## 1.2.1 (2026-11-21)

- Adds a discovery call for Ingenia Consultores (internal knowledge assistant with RAG), with a 10-phase estimate of 900 hours over 14–16 weeks. Stored in `estimation_1_2_1.json`.
- Template and `render_format` unchanged from 1.2.0. Not set as the active version.

## 1.2.0 (2026-11-21)

- Improved template, based on 1.1.1 (same JSON example and `render_format: "json"`). Stored in `estimation_1_2_0.json`. Set as the active version (`ACTIVE_PROMPT_VERSION`).
- Role: senior software delivery consultant, with the purpose of the estimate stated (quoting and planning real projects).
- Examples: the prompt now says what to learn from them (structure, task detail, hour scale, contingency) and not to copy their tasks, hours or technologies.
- Method: an 8-step procedure. Read the input (scope, exclusions, constraints, stack, assumptions), choose phases that fit, write concrete tasks, include easy-to-forget work, avoid out-of-scope work and invented requirements, size in hours, finish with a Contingency phase, and recommend a team and duration that agree with the total hours.
- Output contract is unchanged: `phases`, `team` and `duration`, with no totals.

## 1.1.1 (2026-11-21)

- Same project as 1.1.0, with the example rewritten as JSON objects. Stored in `estimation_1_1_1.json`. The meeting summary is split into named sections, and the estimate into `phases`, `team` and `duration`.
- `render_format` changed from `"markdown"` to `"json"`, so the example is rendered as indented JSON.
- Template adds the output contract: return only a JSON object with `phases` (each with a name and a list of tasks with name and hours, ending with a Contingency phase), `team` (role, count, part_time) and `duration` (min_weeks, max_weeks). No total, since it is computed from the phases.

## 1.1.0 (2026-11-21)

- Example replaced: the 1.0.0 example is swapped for a full discovery-call summary (Norte Distribuciones) and its detailed estimate. Stored in `estimation_1_1_0.json`. `render_format` is still `"markdown"`.
- Template unchanged from 1.0.0.

## 1.0.0 (2026-11-20)

- Initial versioned prompt, stored in `estimation_1_0_0.json`. The wording is unchanged from the unversioned prompt, and the rendered prompt is identical.
- Role: expert in software project estimation.
- Examples: one historical estimate, moved from the former `app/context/examples.py` into the JSON file. Historical estimates are inserted between `---` markers.
- Task: generate a detailed estimate for the described project.
- Note: the example estimates keep the indentation they had in code. Cleaning that up changes the prompt, so it belongs in a new version.
