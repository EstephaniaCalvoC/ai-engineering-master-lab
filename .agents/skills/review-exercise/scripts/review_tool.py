#!/usr/bin/env python3
"""Check and render the review-exercise JSON files. Standard library only.

  review_tool.py check     --rubric FILE [--review FILE]
  review_tool.py questions --rubric FILE --review FILE --out FILE [--overwrite]
  review_tool.py answer    --rubric FILE --review FILE --questions FILE --set ID=yes|no|skip ...
  review_tool.py render    --rubric FILE --review FILE --out FILE [--overwrite]

check      validates the rubric and, when given, the verification file against it.
questions  writes the Spanish list of unverified items and their yes/no questions.
answer     records the student's answers in the verification file and the questions file.
render     runs the same checks, then writes the Spanish report.

Exit codes: 0 ok, 1 validation errors, 2 unreadable input or unusable output path.
"""

import argparse
import json
import re
import sys
import types
import typing
from collections import Counter
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 1

# Vocabulary. The JSON uses these English tags; the Spanish text lives in the renderer.
KINDS = ("checklist", "optional", "deferred")
ITEM_TYPES = (
    "Mandatory requirement",
    "Functionality",
    "Security",
    "Architecture and design",
)
VALIDATIONS = ("Test", "Code")
STATUSES = ("MET", "PARTIAL", "NOT_MET", "NOT_VERIFIED")
SOURCES = ("code", "test", "student", "none")
ANSWERS = ("yes", "no", "skip")
ANSWER_STATUS = {"yes": "MET", "no": "NOT_MET"}
VERDICTS = ("ready", "almost_ready", "needs_work")
PRIORITY_RANK = {"C": 0, "I": 1, "D": 2}
KEY_TYPES = ("Mandatory requirement", "Security", "Functionality")


def _field(*, choices=None, pattern=None, json_name=None, nonempty=False, const=None):
    meta = {}
    if choices is not None:
        meta["choices"] = choices
    if pattern is not None:
        meta["pattern"] = pattern
    if json_name is not None:
        meta["json"] = json_name
    if nonempty:
        meta["nonempty"] = True
    if const is not None:
        meta["const"] = const
    return field(metadata=meta)


# ---------------------------------------------------------------- schema

@dataclass
class RubricItem:
    id: str = _field(pattern=r"R\d{2,}")
    kind: str = _field(choices=KINDS)
    item: str = _field(nonempty=True)
    item_type: str | None = _field(choices=ITEM_TYPES, json_name="type")
    criteria: str | None = _field()
    validation: str | None = _field(choices=VALIDATIONS)


@dataclass
class Rubric:
    schema_version: int = _field(const=SCHEMA_VERSION)
    session: str = _field(pattern=r"\d{2}")
    created_at: str = _field(pattern=r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")
    exercise_path: str = _field(nonempty=True)
    items: list[RubricItem] = _field()


@dataclass
class Reviewed:
    branch: str = _field(nonempty=True)
    sha: str = _field(pattern=r"[0-9a-f]{7,40}")
    project_dir: str | None = _field()
    note: str | None = _field()


@dataclass
class Reference:
    ref: str = _field(nonempty=True)
    sha: str = _field(pattern=r"[0-9a-f]{7,40}")
    note: str | None = _field()


@dataclass
class Context:
    notes: list[str] = _field()


@dataclass
class Strength:
    decision: str = _field(nonempty=True)
    location: str = _field(nonempty=True)
    why: str = _field(nonempty=True)


@dataclass
class VerificationRow:
    item_id: str = _field(pattern=r"R\d{2,}")
    label: str = _field(nonempty=True)
    status: str = _field(choices=STATUSES)
    source: str = _field(choices=SOURCES)
    test_names: list[str] = _field()
    evidence: list[str] = _field()
    notes: str = _field()
    reason: str | None = _field()
    question: str | None = _field()
    student_answer: str | None = _field(choices=ANSWERS)


@dataclass
class Failure:
    test: str = _field(nonempty=True)
    error: str = _field(nonempty=True)


@dataclass
class TestRun:
    ran: bool = _field()
    reason: str | None = _field()
    command: str | None = _field()
    passed: int | None = _field()
    failed: int | None = _field()
    skipped: int | None = _field()
    failures: list[Failure] = _field()


@dataclass
class Finding:
    id: str = _field(pattern=r"[CID]\d+")
    title: str = _field(nonempty=True)
    location: str = _field(nonempty=True)
    what_happens: str = _field(nonempty=True)
    why_matters: str = _field(nonempty=True)
    hint: str = _field(nonempty=True)
    rubric_item_ids: list[str] = _field()


@dataclass
class Reflection:
    conclusion: str = _field(nonempty=True)
    question: str = _field(nonempty=True)
    live_session: list[str] = _field()


@dataclass
class Review:
    schema_version: int = _field(const=SCHEMA_VERSION)
    session: str = _field(pattern=r"\d{2}")
    date: str = _field(pattern=r"\d{4}-\d{2}-\d{2}")
    reviewed: Reviewed = _field()
    exercise_path: str = _field(nonempty=True)
    rubric_file: str = _field(nonempty=True)
    reference: Reference | None = _field()
    context: Context = _field()
    verdict: str = _field(choices=VERDICTS)
    verdict_notes: list[str] = _field()
    strengths: list[Strength] = _field()
    verification: list[VerificationRow] = _field()
    optional_notes: list[str] = _field()
    test_run: TestRun = _field()
    findings: list[Finding] = _field()
    reflection: Reflection = _field()


# ---------------------------------------------------------------- loading

def _coerce(tp, value, where, meta, errors):
    origin = typing.get_origin(tp)
    if origin in (typing.Union, types.UnionType):
        args = typing.get_args(tp)
        if value is None:
            if type(None) not in args:
                errors.append(f"{where}: null is not allowed")
            return None
        inner = next(a for a in args if a is not type(None))
        return _coerce(inner, value, where, meta, errors)
    if origin is list:
        if not isinstance(value, list):
            errors.append(f"{where}: expected a list")
            return None
        (elem,) = typing.get_args(tp)
        return [_coerce(elem, v, f"{where}[{i}]", {}, errors) for i, v in enumerate(value)]
    if is_dataclass(tp):
        return _build(tp, value, where, errors)
    if value is None:
        errors.append(f"{where}: null is not allowed")
        return None
    if tp is str:
        if not isinstance(value, str):
            errors.append(f"{where}: expected a string")
            return None
        if "pattern" in meta and not re.fullmatch(meta["pattern"], value):
            errors.append(f"{where}: {value!r} does not match {meta['pattern']}")
        elif meta.get("nonempty") and not value.strip():
            errors.append(f"{where}: must not be empty")
        if "choices" in meta and value not in meta["choices"]:
            errors.append(f"{where}: {value!r} must be one of: {', '.join(meta['choices'])}")
        return value
    if tp is bool:
        if not isinstance(value, bool):
            errors.append(f"{where}: expected true or false")
            return None
        return value
    if tp is int:
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{where}: expected an integer")
            return None
        if "const" in meta and value != meta["const"]:
            errors.append(f"{where}: must be {meta['const']}")
        return value
    raise TypeError(f"unsupported schema type: {tp}")


def _build(cls, data, where, errors):
    if not isinstance(data, dict):
        errors.append(f"{where}: expected an object")
        return None
    hints = typing.get_type_hints(cls)
    spec = {f.metadata.get("json", f.name): f for f in fields(cls)}
    for key in data:
        if key not in spec:
            errors.append(f"{where}.{key}: unknown field")
    values, complete = {}, True
    for json_name, f in spec.items():
        here = f"{where}.{json_name}"
        if json_name not in data:
            errors.append(f"{here}: missing")
            complete = False
            continue
        values[f.name] = _coerce(hints[f.name], data[json_name], here, f.metadata, errors)
    return cls(**values) if complete else None


def load(path, cls, label):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    errors = []
    return _build(cls, data, label, errors), errors


# ---------------------------------------------------------------- checks

def check_rubric(rubric, rubric_path):
    errors = []
    for dup in (k for k, n in Counter(i.id for i in rubric.items).items() if n > 1):
        errors.append(f"rubric: duplicate id {dup}")
    for it in rubric.items:
        where = f"rubric {it.id}"
        if it.kind == "checklist":
            if not it.item_type:
                errors.append(f"{where}: checklist items need a type")
            if not it.validation:
                errors.append(f"{where}: checklist items need a validation (Test or Code)")
            if not (it.criteria or "").strip():
                errors.append(f"{where}: checklist items need compliance criteria")
            if it.validation == "Test" and it.item_type not in ("Functionality", "Mandatory requirement"):
                errors.append(f"{where}: Test is only for behavior (Functionality or Mandatory requirement); use Code")
        elif it.item_type is not None or it.validation is not None:
            errors.append(f"{where}: {it.kind} items have no type or validation")
    if not any(i.kind == "checklist" and i.item_type == "Functionality" for i in rubric.items):
        errors.append("rubric: needs at least one Functionality item (the main behavior)")
    try:
        stamp = datetime.strptime(rubric.created_at, "%Y-%m-%d %H:%M").strftime("%Y%m%d-%H%M")
    except ValueError:
        errors.append(f"rubric: created_at {rubric.created_at!r} is not a valid date and time")
    else:
        expected = f"s{rubric.session}_rubric_{stamp}.json"
        if Path(rubric_path).name != expected:
            errors.append(f"rubric: file should be named {expected} (from created_at)")
    return errors


def required_priority(item, row):
    """Lowest priority a failing row may get. A finding may rank higher, never lower."""
    if row.status == "NOT_MET" and row.source == "test":
        return "C"
    if item.item_type in KEY_TYPES:
        return "C" if row.status == "NOT_MET" else "I"
    return "I"


def check_review(rubric, review, rubric_path):
    errors = []
    checklist = {i.id: i for i in rubric.items if i.kind == "checklist"}
    if review.session != rubric.session:
        errors.append(f"review session {review.session} does not match rubric session {rubric.session}")
    if Path(review.rubric_file).name != Path(rubric_path).name:
        errors.append(f"review.rubric_file {review.rubric_file!r} is not the rubric being checked")

    # Coverage: every checklist item has exactly one verification row, and nothing else.
    counts = Counter(r.item_id for r in review.verification)
    for rid in checklist:
        if counts[rid] != 1:
            errors.append(f"verification {rid}: needs exactly one row (found {counts[rid]})")
    for rid in counts:
        if rid not in checklist:
            errors.append(f"verification {rid}: not a checklist item in the rubric")

    tr = review.test_run
    failed_names = {f.test for f in tr.failures}
    for row in review.verification:
        item = checklist.get(row.item_id)
        if item is None:
            continue
        where = f"verification {row.item_id}"
        if row.status == "NOT_VERIFIED":
            if row.source != "none":
                errors.append(f"{where}: NOT_VERIFIED needs source 'none'")
            if not (row.reason or "").strip():
                errors.append(f"{where}: NOT_VERIFIED needs a reason")
            if not (row.question or "").strip():
                errors.append(f"{where}: NOT_VERIFIED needs a yes/no question for the student")
            if row.student_answer in ANSWER_STATUS:
                errors.append(f"{where}: answered {row.student_answer!r}, so it can't stay NOT_VERIFIED")
        elif row.source == "none":
            errors.append(f"{where}: {row.status} needs a source (code or test)")
        if row.source == "student":
            if ANSWER_STATUS.get(row.student_answer) != row.status:
                errors.append(f"{where}: source 'student' needs answer 'yes' with MET or 'no' with NOT_MET")
            if not (row.question or "").strip() or not (row.reason or "").strip():
                errors.append(f"{where}: source 'student' keeps the question and the reason it was unverified")
            if failed_names.intersection(row.test_names):
                errors.append(f"{where}: a student answer can't settle a row that cites a failed test")
        elif row.status != "NOT_VERIFIED" and row.student_answer is not None:
            errors.append(f"{where}: student_answer is only for source 'student' or unverified rows")
        if row.source == "code":
            if item.validation == "Test" and row.status == "MET":
                errors.append(f"{where}: reading the code cannot mark a Test item MET, only PARTIAL or NOT_MET")
            if not row.evidence:
                errors.append(f"{where}: source 'code' needs evidence (path:line)")
        if row.source == "test":
            if item.validation == "Code":
                errors.append(f"{where}: a Code item cannot be settled by a test")
            if not row.test_names:
                errors.append(f"{where}: source 'test' needs test_names")
            if not tr.ran:
                errors.append(f"{where}: source 'test' but test_run.ran is false")
        if row.status == "MET" and failed_names.intersection(row.test_names):
            errors.append(f"{where}: MET, but it cites a test that failed")

    # Test run: counts must agree with the failures listed.
    if tr.ran:
        if not tr.command:
            errors.append("test_run: ran, but no command")
        for name in ("passed", "failed", "skipped"):
            if getattr(tr, name) is None or getattr(tr, name) < 0:
                errors.append(f"test_run.{name}: required when tests ran")
        if tr.failed is not None and tr.failed != len(tr.failures):
            errors.append(f"test_run: {tr.failed} failed but {len(tr.failures)} failures listed")
    else:
        if not (tr.reason or "").strip():
            errors.append("test_run.reason: required when tests did not run")
        if tr.command or tr.failures or any(v is not None for v in (tr.passed, tr.failed, tr.skipped)):
            errors.append("test_run: tests did not run, so no command, counts or failures")

    # Findings: IDs, titles, rubric references.
    for letter in PRIORITY_RANK:
        nums = sorted(int(f.id[1:]) for f in review.findings if f.id[0] == letter)
        if nums != list(range(1, len(nums) + 1)):
            errors.append(f"findings: {letter} ids must run {letter}1..{letter}{len(nums)} with no gaps")
    for f in review.findings:
        if "`" in f.title or "\n" in f.title:
            errors.append(f"finding {f.id}: title must not contain backticks or line breaks (it becomes a heading)")
        for rid in f.rubric_item_ids:
            if rid not in checklist:
                errors.append(f"finding {f.id}: {rid} is not a checklist item")

    # Priority floor: failing items need a finding at or above their floor.
    for row in review.verification:
        item = checklist.get(row.item_id)
        if item is None or row.status not in ("NOT_MET", "PARTIAL"):
            continue
        floor = required_priority(item, row)
        covering = [f for f in review.findings if row.item_id in f.rubric_item_ids]
        if not covering:
            errors.append(f"verification {row.item_id}: {row.status} needs a finding of priority {floor} or higher")
        elif min(PRIORITY_RANK[f.id[0]] for f in covering) > PRIORITY_RANK[floor]:
            errors.append(f"verification {row.item_id}: {row.status} is below its floor; needs priority {floor} or higher")

    # Verdict.
    has_critical = any(f.id[0] == "C" for f in review.findings)
    if has_critical and review.verdict == "ready":
        errors.append("verdict: 'ready' is not allowed with a C finding")
    for row in review.verification:
        item = checklist.get(row.item_id)
        if review.verdict == "ready" and item and item.item_type == "Mandatory requirement" and row.status != "MET":
            errors.append(f"verdict: 'ready' needs every mandatory item MET ({row.item_id} is {row.status})")
    depends = [r.item_id for r in review.verification
               if r.item_id in checklist and r.status == "NOT_VERIFIED"
               and checklist[r.item_id].item_type in KEY_TYPES]
    if depends and not review.verdict_notes:
        errors.append(f"verdict: depends on unverified items {', '.join(depends)}; say so in verdict_notes")
    confirmed = [r.item_id for r in review.verification
                 if r.item_id in checklist and r.source == "student" and r.status == "MET"
                 and checklist[r.item_id].item_type in KEY_TYPES]
    if confirmed and not review.verdict_notes:
        errors.append(f"verdict: relies on the student's answer for {', '.join(confirmed)}; say so in verdict_notes")

    return errors


def validate(rubric_path, review_path=None):
    rubric, errors = load(rubric_path, Rubric, "rubric")
    if rubric is None:
        return None, None, errors
    errors += check_rubric(rubric, rubric_path)
    review = None
    if review_path:
        review, review_errors = load(review_path, Review, "review")
        errors += review_errors
        if review is not None and not review_errors:
            errors += check_review(rubric, review, rubric_path)
    return rubric, review, errors


# ---------------------------------------------------------------- rendering

STATUS_LEGEND = [
    "- ✅: Cumplido, o test que pasa. Solo si la evidencia lo confirma",
    "- ⚠️: Cumplido parcialmente",
    "- ❌: No cumplido, o test que falla",
    "- 🔍: No verificado: ni un test ni el código permiten comprobarlo (por ejemplo, requiere la app en "
    "ejecución, una API key o un navegador) y no hubo un sí o un no como respuesta",
    "- «Confirmado por el estudiante»: el estado se basa en tu respuesta, no en un test ni en el código",
]

STATUS_EMOJI = {"MET": "✅", "PARTIAL": "⚠️", "NOT_MET": "❌", "NOT_VERIFIED": "🔍"}
VERDICT_ES = {
    "ready": ("🚀", "¡Lo hiciste genial!", "El proyecto no tiene puntos críticos y cumple los requisitos obligatorios."),
    "almost_ready": ("💪", "¡Casi lo tienes!", "El proyecto necesita arreglos pequeños y bien definidos."),
    "needs_work": ("🚧", "Necesita trabajo.", "El proyecto tiene problemas que requieren más que pequeños arreglos."),
}
SOURCE_ES = {"code": "«Leer el código»", "student": "«Confirmado por el estudiante»", "none": "—"}
ANSWER_ES = {None: "Pendiente", "yes": "Sí", "no": "No", "skip": "Sin respuesta"}
UNVERIFIED_NOTE = ("> 🔍 **Aclara los puntos no verificados:** revisa cada ítem marcado con 🔍. Compruébalo antes de la "
                   "sesión en vivo y, si no sabes cómo hacerlo, pregúntale a tu tutor.")
CRIT_INTRO = ("Todos los hallazgos de esta sección se refieren a código no funcional, requisitos "
              "obligatorios no cumplidos o riesgo de seguridad.")
IMP_INTRO = ("Todos los hallazgos de esta sección se refieren a problemas de escalabilidad, diseño, "
             "arquitectura o mal uso del stack.")
DES_INTRO = ("Estos hallazgos solo se refieren a cuestiones cosméticas, de pulido o pequeños detalles "
             "sin impacto en el funcionamiento ni en la escalabilidad.")


def slug(text):
    """Anchor as the review template defines it: lowercase, punctuation out, spaces to hyphens."""
    text = re.sub(r"[^\w\s-]|_", "", text.lower())
    return re.sub(r"\s+", "-", text.strip())


def _cell(text):
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def _finding_block(f):
    return [
        f"### {f.id}. {f.title}",
        f"- **Dónde:** `{f.location}`",
        f"- **Qué pasa:** {f.what_happens}",
        f"- **Por qué importa:** {f.why_matters}",
        f"- **Pista:** {f.hint}",
    ]


def _validation(row):
    if row.source == "test":
        return "Test: " + ", ".join(f"`{n}`" for n in row.test_names)
    return SOURCE_ES[row.source]


def render(review, rubric):
    order = {item.id: n for n, item in enumerate(rubric.items)}
    rows = sorted(review.verification, key=lambda r: order[r.item_id])
    crit = [f for f in review.findings if f.id[0] == "C"]
    imp = [f for f in review.findings if f.id[0] == "I"]
    des = [f for f in review.findings if f.id[0] == "D"]
    tr = review.test_run
    rv = review.reviewed

    # Header. The review metadata goes in the closing context section.
    head = [f"# Sesión {review.session} — Revisión del ejercicio", ""]
    notes = [p for p in (rv.note, f"el proyecto está en `{rv.project_dir}/`" if rv.project_dir else None) if p]
    if review.reference:
        ref = review.reference
        ref_text = f"`{ref.ref}` @ `{ref.sha}`" + (f" ({ref.note})" if ref.note else "")
    else:
        ref_text = "«ninguna»"

    # Sections: (title, body lines), in report order.
    sections = []

    emoji, label, meaning = VERDICT_ES[review.verdict]
    summary = [f"**{emoji} {label}** {meaning}", ""]
    for note in review.verdict_notes:
        summary += [f"**Nota:** {note}", ""]
    summary += ["### Lo que hiciste bien"]
    summary += [f"- **{s.decision}** (`{s.location}`): {s.why}" for s in review.strengths] or ["- Ninguno."]
    sections.append(("Veredicto", summary))

    def finding_section(title, intro, findings, empty_text):
        if not findings:
            return (title, [empty_text])
        body = [intro]
        for f in findings:
            body += [""] + _finding_block(f)
        return (title, body)

    sections.append(finding_section("Hallazgos críticos", CRIT_INTRO, crit, "No se encontró ningún hallazgo crítico."))
    sections.append(finding_section("Hallazgos importantes", IMP_INTRO, imp, "No se encontró ninguno."))
    sections.append(finding_section("Hallazgos deseables", DES_INTRO, des, "No se encontró ninguno."))

    refl = review.reflection
    sections.append(("Conclusiones y preguntas para reflexionar", [
        f"- **Conclusión:** {refl.conclusion}",
        f"- **Pregunta:** {refl.question}",
        f"- **Lo que viene en la sesión en vivo (no se evalúa):** {'; '.join(refl.live_session) or 'ninguno'}",
    ]))

    detail = ["", "### Rúbrica", *STATUS_LEGEND, "",
              "| Ítem | Estado | Comentarios | Método de validación |", "|---|---|---|---|"]
    for r in rows:
        status = STATUS_EMOJI[r.status]
        comments = " ".join(x for x in ((r.reason if r.status == "NOT_VERIFIED" else None), r.notes) if x)
        detail.append(f"| {_cell(r.label)} | {status} | {_cell(comments)} | {_cell(_validation(r))} |")
    if any(r.status == "NOT_VERIFIED" for r in rows):
        detail += ["", UNVERIFIED_NOTE]
    if review.optional_notes:
        detail += ["", "Ítems opcionales o diferidos (listados, no penalizados): " + "; ".join(review.optional_notes) + "."]

    detail += ["", "### Ejecución de tests"]
    if tr.ran:
        detail.append(f"- **Comando:** `{tr.command}`")
        detail.append(f"- **Resultado:** {tr.passed} pasados, {tr.failed} fallidos, {tr.skipped} omitidos")
        if tr.failures:
            detail.append("- **Fallos:**")
            detail += [f"  - `{f.test}`: {f.error}" for f in tr.failures]
            detail.append("- **Causa de los fallos:** no se investigó. Si quieres profundizar en alguno, pídeselo a tu tutor.")
        else:
            detail.append("- **Fallos:** ninguno")
    else:
        detail.append(f"- **Resultado:** no se ejecutaron: {tr.reason}")
    unverified = [r for r in rows if r.status == "NOT_VERIFIED"]
    if unverified:
        detail.append("- **No verificado:**")
        detail += [f"  - {r.label}: {r.reason}" for r in unverified]
    else:
        detail.append("- **No verificado:** ninguno")
    sections.append(("Evaluación detallada", detail))

    if not tr.ran:
        not_run = tr.reason
    elif tr.skipped:
        not_run = "1 test omitido" if tr.skipped == 1 else f"{tr.skipped} tests omitidos"
    else:
        not_run = "Ninguno"
    ctx = [
        f"- **Revisado:** `{rv.branch}` @ `{rv.sha}`" + (f" ({'; '.join(notes)})" if notes else ""),
        f"- **Ejercicio:** `{review.exercise_path}`",
        f"- **Referencia de LIDR:** {ref_text}",
        f"- **Rúbrica:** `{review.rubric_file}`",
        f"- **Fecha:** {review.date}",
        f"- **Tests que no se ejecutaron:** {not_run}",
    ]
    ctx += [f"- {note}" for note in review.context.notes]
    sections.append(("Contexto de la revisión", ctx))

    # Index, built from the sections actually written.
    toc = ["## Índice"]
    for n, (title, _) in enumerate(sections, 1):
        toc.append(f"{n}. [{title}](#{slug(title)})")
    toc.append("")

    out = head + toc
    for title, body in sections:
        out += [f"## {title}"] + body + [""]
    return "\n".join(out).rstrip() + "\n"


def render_questions(review, rubric):
    order = {item.id: n for n, item in enumerate(rubric.items)}
    rows = sorted((r for r in review.verification if r.status == "NOT_VERIFIED" or r.source == "student"),
                  key=lambda r: order[r.item_id])
    out = [f"# Sesión {review.session} — Puntos por verificar", "",
           "Ni un test ni el código permitieron comprobar estos puntos. Cada pregunta se responde con Sí o No."]
    for r in rows:
        out += ["", f"## {r.item_id}. {r.label}",
                f"- **Por qué no se pudo verificar:** {r.reason}",
                f"- **Pregunta:** {r.question}",
                f"- **Respuesta:** {ANSWER_ES[r.student_answer]}"]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- CLI

def _report(errors, ok_message):
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        print(f"FAILED: {len(errors)} problem(s)")
        return 1
    print(f"OK: {ok_message}")
    return 0


def cmd_check(args):
    rubric, review, errors = validate(args.rubric, args.review)
    if errors:
        return _report(errors, "")
    parts = [f"rubric {len(rubric.items)} items"]
    if review:
        parts.append(f"verification {len(review.verification)} rows, {len(review.findings)} findings, verdict {review.verdict}")
    return _report([], "; ".join(parts))


def cmd_render(args):
    rubric, review, errors = validate(args.rubric, args.review)
    if errors:
        return _report(errors, "")
    return _write_new(args, render(review, rubric))


def _write(path, text):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        print(f"cannot write {path}: {exc}", file=sys.stderr)
        return 2
    print(f"OK: wrote {path}")
    return 0


def _write_new(args, text):
    out_path = Path(args.out)
    if out_path.exists() and not args.overwrite:
        print(f"ERROR: {out_path} exists; choose another name or pass --overwrite")
        return 1
    return _write(out_path, text)


def cmd_questions(args):
    rubric, review, errors = validate(args.rubric, args.review)
    if errors:
        return _report(errors, "")
    if not any(r.status == "NOT_VERIFIED" for r in review.verification):
        return _report([], "no unverified items; no questions file written")
    return _write_new(args, render_questions(review, rubric))


def cmd_answer(args):
    rubric, review, errors = validate(args.rubric, args.review)
    if errors:
        return _report(errors, "")
    if not Path(args.questions).is_file():
        print(f"ERROR: {args.questions} not found; run the questions command first")
        return 1

    # Only unverified rows take an answer, so it can never replace a test or code result.
    pending = {r.item_id for r in review.verification if r.status == "NOT_VERIFIED"}
    answers = {}
    for entry in args.set:
        item_id, _, value = entry.partition("=")
        if item_id not in pending:
            errors.append(f"answer {entry!r}: {item_id} is not an unverified item")
        elif value not in ANSWERS:
            errors.append(f"answer {entry!r}: the value must be one of: {', '.join(ANSWERS)}")
        elif item_id in answers:
            errors.append(f"answer {entry!r}: {item_id} is answered twice")
        else:
            answers[item_id] = value
    if errors:
        return _report(errors, "")

    data = json.loads(Path(args.review).read_text(encoding="utf-8"))
    for raw, row in zip(data["verification"], review.verification):
        value = answers.get(row.item_id)
        if value is None:
            continue
        row.student_answer = raw["student_answer"] = value
        if value in ANSWER_STATUS:
            row.status = raw["status"] = ANSWER_STATUS[value]
            row.source = raw["source"] = "student"

    code = _write(Path(args.review), json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    code = code or _write(Path(args.questions), render_questions(review, rubric))
    if code:
        return code

    # A new answer can require a finding or a different verdict: list what is left to update.
    todo = check_review(rubric, review, args.rubric)
    for problem in todo:
        print(f"TODO: {problem}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="validate a rubric and, optionally, a verification file")
    p_check.add_argument("--rubric", required=True)
    p_check.add_argument("--review")
    p_check.set_defaults(func=cmd_check)

    p_questions = sub.add_parser("questions", help="write the unverified items and their yes/no questions")
    p_questions.add_argument("--rubric", required=True)
    p_questions.add_argument("--review", required=True)
    p_questions.add_argument("--out", required=True)
    p_questions.add_argument("--overwrite", action="store_true")
    p_questions.set_defaults(func=cmd_questions)

    p_answer = sub.add_parser("answer", help="record the student's answers")
    p_answer.add_argument("--rubric", required=True)
    p_answer.add_argument("--review", required=True)
    p_answer.add_argument("--questions", required=True)
    p_answer.add_argument("--set", action="append", required=True, metavar="ID=yes|no|skip")
    p_answer.set_defaults(func=cmd_answer)

    p_render = sub.add_parser("render", help="validate, then write the Spanish report")
    p_render.add_argument("--rubric", required=True)
    p_render.add_argument("--review", required=True)
    p_render.add_argument("--out", required=True)
    p_render.add_argument("--overwrite", action="store_true")
    p_render.set_defaults(func=cmd_render)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
