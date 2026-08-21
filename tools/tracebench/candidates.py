"""What the bench grades: a candidate word trace, and the four ways to get one.

A candidate is LITERALLY a `word_instances` row — strokes plus the registration
they are labelled in plus the row's x-height (`docs/proposals/tintenfolger.md`
§2.4). The bench input is therefore the product's own storage format, which is
what keeps "it scored well on the bench" and "it can be stored and drawn" from
being two different claims. Every provider hands back the same shape, so a
follower, the chain baseline and the human reference are read by one scorer.

The four providers, and why each exists:

* `authored_provider` — the reference rows themselves. Scoring them against
  their own reference is the IDENTITY GATE: dtw = 0, every counter matched, or
  the ruler is broken and no candidate number is read (§14 Kill-Kriterien).
* `traced_provider` — the stored harvest rows. Empty for the ten development
  words, because a specimen holds exactly ONE stored row and those ten are the
  manually re-traced `authored` ones. That emptiness is not a defect: it is
  precisely why the chain baseline is RECOMPUTED rather than read.
* `chain_provider` — the Stage-B chain fit, run through the harvest's own code
  (`tools.laufform.harvest.chain_word_strokes`), never a reimplementation.
* `file_provider` — anything outside this repo's process: the ink-follower's
  output, an InkSight decode. Requires the literal `"frame":
  "word_registration"` so a file in some other frame is refused instead of
  silently measured as a tracing error.

Failure is a ROW, never an exception: a provider that cannot produce a trace for
one word returns `Candidate(status="failed"/"skipped", detail=…)` and the run
reports it beside the words it could score. One unauthored letter must not take
a bench run down.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.tracebench.reference import DEFAULT_FIXTURES_DIR, Reference, ReferenceRow


# `api.schemas.WordInstanceItem`'s wire caps, re-declared rather than imported:
# a measuring tool must not pull the API package (pydantic, the DB models) into
# a bench process. `tests/test_tracebench_candidates.py` pins the equality, so
# the two cannot drift apart silently.
MAX_WORD_STROKES = 128
MAX_STROKE_POINTS = 4096
MIN_STROKE_POINTS = 2
MAX_ABS_COORD = 100.0

# The file provider's mandatory literal (§2.4). Not a default and not inferred:
# a candidate file states the frame its numbers live in, or it is not read.
CANDIDATE_FRAME = "word_registration"

STATUS_OK = "ok"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"


@dataclass(frozen=True)
class Candidate:
    """One candidate word trace in the stored wire shape.

    Frozen on purpose: a candidate travels from a provider through the scorer
    (and, with `--jobs`, through a process boundary) and nothing along that way
    may adjust it. A validation failure is expressed as `status`/`detail`, not
    as a mutated geometry.
    """

    strokes: list[list[list[float]]]
    registration_px: dict[str, Any]
    xh_px: float | None
    status: str = STATUS_OK
    detail: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == STATUS_OK


def wire_violation(strokes: Any) -> str:
    """Why these strokes could not be stored — `""` when they could.

    The same bounds `api.schemas.WordInstanceItem` enforces, checked HERE so a
    candidate that could never be written to the database is caught by the
    bench rather than praised by it.
    """
    if not isinstance(strokes, list) or not strokes:
        return "no strokes"
    if len(strokes) > MAX_WORD_STROKES:
        return f"{len(strokes)} strokes over the {MAX_WORD_STROKES} cap"
    for i, stroke in enumerate(strokes):
        if not isinstance(stroke, list):
            return f"stroke {i} is not a list of points"
        if len(stroke) < MIN_STROKE_POINTS or len(stroke) > MAX_STROKE_POINTS:
            return f"stroke {i} has {len(stroke)} points ({MIN_STROKE_POINTS}..{MAX_STROKE_POINTS} allowed)"
        for point in stroke:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                return f"stroke {i} has a point that is not an [x, y] pair"
            try:
                coords = [float(v) for v in point]
            except (TypeError, ValueError):
                return f"stroke {i} has a non-numeric coordinate"
            if not all(abs(v) <= MAX_ABS_COORD for v in coords):
                return f"stroke {i} leaves the +-{MAX_ABS_COORD:g} template-unit range"
    return ""


def candidate_from_wire(
    strokes: Any, registration_px: Any, xh_px: Any, *, meta: dict[str, Any] | None = None
) -> Candidate:
    """Build a validated candidate from a stored-shape row's three fields."""
    violation = wire_violation(strokes)
    registration = dict(registration_px or {})
    try:
        xh = float(xh_px) if xh_px is not None else None
    except (TypeError, ValueError):
        xh, violation = None, violation or f"xh_px {xh_px!r} is not a number"
    if not violation and (xh is None or xh <= 0.0):
        violation = f"xh_px {xh_px!r} is not a positive pixel scale"
    if not violation and "baseline_row" not in registration:
        violation = "registration_px carries no baseline_row"
    return Candidate(
        # Deep-copied: the frozen dataclass must own its geometry — an aliased
        # caller list could be mutated after construction and change what gets
        # measured, silently breaking determinism.
        strokes=copy.deepcopy(strokes) if isinstance(strokes, list) else [],
        registration_px=registration,
        xh_px=xh,
        status=STATUS_FAILED if violation else STATUS_OK,
        detail=violation,
        meta=dict(meta or {}),
    )


def candidate_from_row(row: ReferenceRow) -> Candidate:
    """A stored reference row read back as a candidate (identity gate, `traced`)."""
    return candidate_from_wire(
        row.strokes,
        row.registration_px,
        row.xh_px,
        meta={"provenance": row.provenance, **({"fit_path": row.fit_path} if row.fit_path else {})},
    )


Provider = Callable[[Reference, Sequence[str]], dict[str, Candidate]]


def _rows_by_provenance(reference: Reference, specimen_ids: Sequence[str], provenance: str) -> dict[str, Candidate]:
    out: dict[str, Candidate] = {}
    for specimen_id in specimen_ids:
        entry = reference.entries.get(specimen_id)
        if entry is None:
            out[specimen_id] = Candidate([], {}, None, STATUS_SKIPPED, "no scoreable row in the artifact")
            continue
        if entry.row.provenance != provenance:
            out[specimen_id] = Candidate(
                [], {}, None, STATUS_SKIPPED, f"stored row is {entry.row.provenance!r}, not {provenance!r}"
            )
            continue
        out[specimen_id] = candidate_from_row(entry.row)
    return out


def authored_provider(reference: Reference, specimen_ids: Sequence[str]) -> dict[str, Candidate]:
    """The `authored` rows as candidates — the identity gate's input."""
    return _rows_by_provenance(reference, specimen_ids, "authored")


def traced_provider(reference: Reference, specimen_ids: Sequence[str]) -> dict[str, Candidate]:
    """The stored `traced` harvest rows as candidates.

    A specimen holds one stored row, so this is empty wherever the author
    re-traced by hand — i.e. on the whole development split. The bench does not
    paper over that: the chain baseline is recomputed by `chain_provider`, and
    every word without a traced row is reported as `skipped`.
    """
    return _rows_by_provenance(reference, specimen_ids, "traced")


def file_provider(path: Path | str) -> Provider:
    """Candidates from a JSON file — the route for anything outside this process.

    Shape (the frozen artifact's, so a candidate file and a stored set read the
    same way)::

        {"frame": "word_registration",
         "label": "inksight-t0",
         "rows": [{"specimen_id": "die",
                   "strokes": [[[x, y], ...], ...],
                   "measurements": {"registration_px": {"tx":…, "ty":…, "baseline_row":…},
                                    "xh_px": 30.0}}]}

    `registration_px`/`xh_px` are also accepted at the row's top level (a
    generator that never had `measurements` to fill). The `frame` literal is
    MANDATORY: a trace in crop pixels or in some model's own grid would
    otherwise be measured as a catastrophic tracing error instead of being
    refused. Ids the file carries but the run did not ask for are reported, not
    an error — a file usually covers more words than one split.
    """
    source = Path(path)

    def provide(reference: Reference, specimen_ids: Sequence[str]) -> dict[str, Candidate]:
        try:
            payload = json.loads(source.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"--candidate-file {source}: {exc}") from None
        if not isinstance(payload, dict):
            raise SystemExit(f"--candidate-file {source}: expected a JSON object")
        frame = payload.get("frame")
        if frame != CANDIDATE_FRAME:
            raise SystemExit(
                f"--candidate-file {source}: frame {frame!r} — this bench only reads {CANDIDATE_FRAME!r} "
                "(strokes in the word's registration frame, exactly as word_instances stores them)"
            )
        rows = payload.get("rows")
        if not isinstance(rows, list):
            raise SystemExit(f"--candidate-file {source}: 'rows' must be a list")

        by_id: dict[str, dict] = {}
        malformed = 0
        for raw in rows:
            if not isinstance(raw, dict) or not raw.get("specimen_id"):
                malformed += 1
                continue
            by_id[str(raw["specimen_id"])] = raw
        if malformed:
            print(f"  {source.name}: {malformed} rows without a specimen_id ignored")
        unknown = sorted(set(by_id) - set(reference.entries))
        if unknown:
            print(f"  {source.name}: {len(unknown)} ids with no frozen entry ignored ({', '.join(unknown[:6])}…)")

        out: dict[str, Candidate] = {}
        for specimen_id in specimen_ids:
            raw = by_id.get(specimen_id)
            if raw is None:
                out[specimen_id] = Candidate([], {}, None, STATUS_SKIPPED, f"not in {source.name}")
                continue
            measurements = raw.get("measurements") or {}
            out[specimen_id] = candidate_from_wire(
                raw.get("strokes"),
                measurements.get("registration_px", raw.get("registration_px")),
                measurements.get("xh_px", raw.get("xh_px")),
                meta={"source": source.name, **({"label": payload["label"]} if payload.get("label") else {})},
            )
        return out

    return provide


# The four seams to the harvest, each a module-level function with a DEFERRED
# import. Deferred because `tools.laufform.harvest` pulls `tools.wordlab` (and
# with it matplotlib) plus the whole fit stack, and a run that scores a
# candidate FILE must not need any of it. Module level because a test has to be
# able to replace the fixture loader without replacing the code under test —
# the solve, the assembly and the record builder stay the harvest's own.


def _chain_cases(*, which: str, style: str, only: Sequence[str], fixtures_root: Path) -> dict[str, Any]:
    from tools.wordlab.cases import iter_fixture_word_cases  # noqa: PLC0415

    cases = iter_fixture_word_cases(which=which, style=style, only=list(only), fixtures_root=fixtures_root)
    return {c.id: c for c in cases}


def _chain_derive(case: Any) -> Any:
    from tools.wordlab.derive import derive_word  # noqa: PLC0415

    return derive_word(case)


def _chain_strokes(case: Any, result: Any, opts: Any) -> tuple[list, dict]:
    from tools.laufform.harvest import chain_word_strokes  # noqa: PLC0415

    return chain_word_strokes(case, result, opts)


def _chain_record(case: Any, strokes: list, registration: dict, xh: float) -> dict:
    from tools.laufform.harvest import _word_record  # noqa: PLC0415

    return _word_record(case, strokes, registration, xh, {})


def _chain_options(
    style: str,
    chain_seed: str,
    mark_refit: bool = False,
    marks_last: bool = True,
    trace_repair: bool = True,
    ink_evidence: bool = True,
) -> Any:
    from tools.laufform.harvest import HarvestOptions  # noqa: PLC0415

    return HarvestOptions(
        style=style,
        path="chain",
        chain_seed=chain_seed,
        mark_refit=mark_refit,
        marks_last=marks_last,
        trace_repair=trace_repair,
        ink_evidence=ink_evidence,
    )


def chain_provider(
    *,
    style: str = "suetterlin",
    which: str = "words",
    fixtures_root: Path | None = None,
    chain_seed: str = "composed",
    mark_refit: bool = False,
    marks_last: bool = True,
    trace_repair: bool = True,
    ink_evidence: bool = True,
) -> Provider:
    """The Stage-B chain fit — run through the HARVEST's own code path.

    `tools.laufform.harvest.chain_word_strokes` is literally the first half of
    `_harvest_case_chain`: the per-slot grid windows, one `fit_word_chain` per
    run of joined slots, the welded pen path and the wire caps; the row is then
    shaped by the harvest's own `_word_record`, so the registration the bench
    maps with is the one the row would be STORED with (rounded tx/ty, integer
    baseline row). Nothing is re-derived here, because a baseline that is a
    reimplementation of the thing that ships stops being the baseline the moment
    the two drift — which is what
    `tests/test_tracebench_candidates.py` asserts on the harvest's own synthetic
    specimen.

    `mark_refit` is measure A1 of `docs/proposals/tintenfolger.md` §7.3 — the
    marks refitted onto their own ink after the body solve
    (`tools.pairlab.marks`). Default False, because with it the candidate is no
    longer the stored baseline but a variant of it; a run that switches it on is
    its OWN pre-registered measurement and says so in its label.
    """
    root = Path(fixtures_root) if fixtures_root is not None else DEFAULT_FIXTURES_DIR

    def provide(reference: Reference, specimen_ids: Sequence[str]) -> dict[str, Candidate]:
        ids = list(specimen_ids)
        opts = _chain_options(style, chain_seed, mark_refit, marks_last, trace_repair, ink_evidence)
        cases = _chain_cases(which=which, style=style, only=ids, fixtures_root=root)
        out: dict[str, Candidate] = {}
        for specimen_id in ids:
            case = cases.get(specimen_id)
            if case is None:
                out[specimen_id] = Candidate([], {}, None, STATUS_SKIPPED, f"no {which!r} fixture case")
                continue
            if not case.scorable:
                out[specimen_id] = Candidate([], {}, None, STATUS_SKIPPED, "frozen unscorable (unauthored template)")
                continue
            try:
                result = _chain_derive(case)
                if result.composed.get("missing"):
                    out[specimen_id] = Candidate(
                        [], {}, None, STATUS_SKIPPED, f"composition missing {result.composed['missing']}"
                    )
                    continue
                strokes, meta = _chain_strokes(case, result, opts)
            except Exception as exc:  # a solver crash is one word's row, not the run
                out[specimen_id] = Candidate([], {}, None, STATUS_FAILED, f"{type(exc).__name__}: {exc}")
                continue
            if not strokes:
                out[specimen_id] = Candidate([], {}, None, STATUS_FAILED, "the chain produced no pen path")
                continue
            record = _chain_record(case, strokes, meta["registration"], meta["xh"])
            runs = meta["runs"]
            out[specimen_id] = candidate_from_wire(
                record["strokes"],
                record["measurements"]["registration_px"],
                record["measurements"]["xh_px"],
                meta={
                    "fit_path": "chain",
                    "chain_seed": chain_seed,
                    "runs": len(runs),
                    "runs_failed": sum(1 for r in runs if r.fit is None),
                    "traced_slots": meta["traced_slots"],
                    "run_slots": meta["run_slots"],
                    "n_params": meta["n_params"],
                    "seconds": meta["seconds"],
                    # Absent (not None) while A1 is off, so a baseline row and
                    # an A1 row are distinguishable in the report itself.
                    **({"mark_refit": meta["mark_refit"]} if meta.get("mark_refit") is not None else {}),
                },
            )
        return out

    return provide


PROVIDER_NAMES = ("chain", "authored", "traced", "file")


__all__ = [
    "CANDIDATE_FRAME",
    "MAX_ABS_COORD",
    "MAX_STROKE_POINTS",
    "MAX_WORD_STROKES",
    "MIN_STROKE_POINTS",
    "PROVIDER_NAMES",
    "STATUS_FAILED",
    "STATUS_OK",
    "STATUS_SKIPPED",
    "Candidate",
    "Provider",
    "authored_provider",
    "candidate_from_row",
    "candidate_from_wire",
    "chain_provider",
    "file_provider",
    "traced_provider",
    "wire_violation",
]
