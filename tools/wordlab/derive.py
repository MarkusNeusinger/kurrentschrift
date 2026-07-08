"""Compose a `WordCase` through the real composer, plus per-segment attribution.

`derive_word` runs the exact production path a word-bench run runs — render each
glyph via `core.pipeline.render_payload_for_template`, lay them out and generate
the Übergänge via `core.compose.compose_word` (with provenance so segments can
be attributed), and, when the case carries a specimen, score it with the FROZEN
ruler (`tools.wordbench.metric.score_word` + `score_word_segments`) on the same
registration the metric reports. Nothing here re-implements composition or
scoring: the numbers are exactly what the bench sees.

The result bundles the render transform (`xh_px`, `baseline_row`, `registration`)
so the panel maps composed template-frame points to crop pixels the same way
the metric and the bench overlay do. A live case has no specimen, so it carries
render-only defaults (baseline at 0, a fixed unit scale) and no score.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.compose import compose_word
from core.pipeline import render_payload_for_template

from .cases import WordCase


# Pixels per x-height unit for a live case (no specimen to measure against). The
# value is arbitrary — the panel uses equal aspect — but a concrete scale keeps
# the composed-frame → "pixel" transform identical in code to the specimen path.
LIVE_XH_PX = 40.0


@dataclass
class WordDeriveResult:
    """Production composition of one case + everything to render and explain it."""

    case: WordCase
    payloads: dict[str, dict | None]  # glyph_key -> render payload (None = unauthored)
    composed: dict  # compose_word(..., provenance=True): items / bounds / guides / missing
    report: dict | None  # score_word report (None when the case has no specimen)
    segments: list[dict] | None  # score_word_segments rows in writing order (None w/o specimen)
    xh_px: float  # pixels per x-height unit for the render transform
    baseline_row: float  # crop-pixel y of the baseline (0 for a live case)
    registration: dict  # {tx, ty, xh_px} — the fitted shift (zero for a live case)


def _payloads_for(case: WordCase) -> dict[str, dict | None]:
    """Render every distinct slot glyph once (cache per key), None if unauthored."""
    cache: dict[str, dict | None] = {}
    for slot in case.slots:
        if not slot.key or slot.key in cache:
            continue
        row = case.templates.get(slot.key)
        cache[slot.key] = (
            render_payload_for_template(row, case.style_ratio, case.width_resolver, case.nib_units) if row else None
        )
    return cache


def derive_word(case: WordCase) -> WordDeriveResult:
    """Compose the case (provenance on) and, if it has a specimen, score it.

    A composition missing a template still returns a result — `report` is then
    the failed dict and `segments` is None — so the panel can draw what exists
    and name the hole instead of raising.
    """
    payloads = _payloads_for(case)
    composed = compose_word(case.slots, payloads, provenance=True)

    report: dict | None = None
    segments: list[dict] | None = None
    if case.has_specimen:
        from tools.wordbench.metric import score_word, score_word_segments  # noqa: PLC0415

        word_meta = {"rect": case.rect, "baseline_y": case.baseline_y, "midband_y": case.midband_y}
        report = score_word(composed, word_meta, case.skel, case.nib_units)
        if not report.get("failed") and report.get("registration"):
            segments = score_word_segments(composed, word_meta, case.skel, case.nib_units, report["registration"])

    # Render transform. Specimen: scale + baseline from the measured lineature,
    # the fitted shift from the metric (0 when it could not score). Live: a fixed
    # unit scale, baseline at 0, no shift.
    if case.has_specimen:
        xh_px = float(case.baseline_y - case.midband_y)
        baseline_row = float(case.baseline_y - case.rect[1])
    else:
        xh_px = LIVE_XH_PX
        baseline_row = 0.0
    registration = (
        report["registration"] if report and report.get("registration") else {"tx": 0.0, "ty": 0.0, "xh_px": xh_px}
    )

    return WordDeriveResult(
        case=case,
        payloads=payloads,
        composed=composed,
        report=report,
        segments=segments,
        xh_px=xh_px,
        baseline_row=baseline_row,
        registration=registration,
    )
