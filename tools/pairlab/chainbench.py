"""Stage-A evaluation harness: the pair-scale chain fit against the independent
one, occurrence by occurrence (issue #278).

`tools/pairlab/analyze.py` fits the two letters of a join INDEPENDENTLY and
regenerates the connector between them; `tools/pairlab/chain.py` fits
`letter → connector → letter` as ONE problem with the two seams tied by shared
anchors. This module runs BOTH paths over the same occurrences of the same
frozen specimens and prints the four Stage-A metrics plus the kill-criterion
signals that decide whether the chain is worth a Stage B:

* **M1 — convergence.** Does the chain converge at least as often as the two
  independent M4 traces? Pooled rate, per-letter rate and the PAIRED table
  (chain-only wins · baseline-only wins · both · neither), so a wash between
  two equal rates cannot hide a swap.
* **M2 — joins that are empty today.** Where the letters touch on the plate,
  `analyze._real_join` returns nothing and the occurrence contributes no
  measured join at all. The chain has ink under its connector regardless — how
  many of those joins does it recover (connector segment converged and
  attributed coverage points)?
* **M3 — connector shape.** `dconn` against the specimen's own joining stroke,
  computed with `tools/wordbench/pairmeas.py`'s exact formula (arc-length
  resample to `core.aggregate.PAIR_CONNECTOR_POINTS`, each start-aligned, mean
  pointwise distance), for the GENERATED connector and the CHAIN's — the
  generated number is the bar, the chain's is the candidate.
* **M4 — letter shape.** How far the chain moves each letter away from the
  independent trace, against the per-anchor MAD of the hand's own aggregates as
  the noise floor. A difference below the hand's own spread is not a difference.

and the kill criteria:

* **tail-stub trend** — if the chain's coupling stub systematically has to move
  FURTHER than the independent trace's, the shared seam is being paid for by
  the glyph, which is the failure mode the chain exists to avoid.
* **capital partition** — capitals are where the independent path is already
  weakest; a chain that diverges exactly there buys nothing.
* **seam calibration** — how much arc the chain's connector claims left of the
  left letter's ink and right of the right letter's, against the baseline's
  measured `tail_adapt`/`head_adapt` and against the 0.2–0.4 xh per-side
  stub-replacement zone measured in `docs/proposals/uebergaenge-befund.md` §5.

Measurement only: reads frozen fixtures, writes JSON/CSV under `temp/`, never
touches the DB, the API, `core/` or rendering. The chain path is optional at
runtime — an occurrence whose chain fit raises is counted and reported, and the
baseline half of the report still stands.

Usage:
    uv run python -m tools.pairlab.chainbench --set pairs
    uv run python -m tools.pairlab.chainbench --set all --jobs 8 --json temp/stage_a.json
    uv run python -m tools.pairlab.chainbench --set all --pairs de,on,bi --max-occ 4
    uv run python -m tools.pairlab.chainbench --set pairs --pairs longs:t --csv temp/stage_a.csv
"""

from __future__ import annotations

import argparse
import csv
import functools
import json
import math
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from core.aggregate import PAIR_CONNECTOR_POINTS, _resample_polyline
from core.compose import _key_base
from tools.pairlab import chain as chain_mod
from tools.pairlab.analyze import JoinDissection, _ink_extent_x, _stub_vs_body_delta, dissect_occurrence
from tools.pairlab.harvest import _adjacent_joined, _px_to_units, connector_points
from tools.wordlab.cases import DEFAULT_FIXTURES_DIR, REPO_ROOT, WordCase, _root_for, iter_fixture_word_cases
from tools.wordlab.derive import WordDeriveResult, derive_word


# Points both fitted centerlines are arc-length-resampled to before the
# chain-vs-trace shape delta is taken. The two paths sample the same template
# with different plans, so index correspondence has to be re-established; arc
# length is the same parameter `core.aggregate._resample_polyline` uses for
# connectors.
SHAPE_SAMPLES = 64
# Per-side arc (xh) the specimen's stub-replacement zone was measured at
# (uebergaenge-befund.md §5). The seam calibration reports how much of the
# chain's connector falls outside this band — a connector that routinely
# swallows much more has moved the seam into the glyph.
SEAM_TARGET_UNITS = (0.2, 0.4)
# A pair's exit class, keyed by the LEFT letter — the grouping the befund found
# the deviations cluster by (§5: d-Schleife · Deckstrich-Bogen · r-Arm ·
# Versalien · everything else, the plain arcade diagonal).
_LOOP_EXIT_BASES = frozenset({"d", "longs"})
_DECKSTRICH_BASES = frozenset({"o", "b", "v", "w", "r"})


# --------------------------------------------------------------- pure helpers


def pair_class(left_base: str) -> str:
    """Exit class of a join, from the LEFT letter (uebergaenge-befund.md §5)."""
    if left_base[:1].isupper():
        return "capital"
    if left_base in _LOOP_EXIT_BASES:
        return "loop_exit"
    if left_base in _DECKSTRICH_BASES:
        return "deckstrich_arm"
    return "arcade_diagonal"


def parse_pair_filter(spec: str) -> set[tuple[str, str]]:
    """`--pairs` spec → the set of base pairs to keep.

    Comma separates the pairs, so a multi-character base (long s, umlauts) uses
    the colon form: ``de,on,longs:t``. A two-character entry is split per
    letter, exactly like `analyze.pair_bases`' short form.
    """
    out: set[tuple[str, str]] = set()
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        if ":" in token:
            left, _, right = token.partition(":")
            if not left or not right:
                raise SystemExit(f"--pairs entry {token!r}: expected left:right (e.g. longs:t)")
            out.add((left, right))
        elif len(token) == 2:
            out.add((token[0], token[1]))
        else:
            raise SystemExit(f"--pairs entry {token!r}: give two letters ('de') or the colon form ('longs:t')")
    return out


def dconn(a: Sequence | np.ndarray, b: Sequence | np.ndarray) -> float | None:
    """Connector shape distance, `tools/wordbench/pairmeas.py`'s exact formula.

    Both polylines are arc-length-resampled to `PAIR_CONNECTOR_POINTS` and then
    shifted so their own first sample sits at the origin, which makes the number
    translation-free: placement is not this column's business, shape and sweep
    are. None when either side is degenerate.
    """
    pa = np.asarray(a, dtype=float).reshape(-1, 2)
    pb = np.asarray(b, dtype=float).reshape(-1, 2)
    if len(pa) < 2 or len(pb) < 2:
        return None
    ra = _resample_polyline(pa, PAIR_CONNECTOR_POINTS)
    rb = _resample_polyline(pb, PAIR_CONNECTOR_POINTS)
    return float(np.linalg.norm((ra - ra[0]) - (rb - rb[0]), axis=1).mean())


def arc_share(poly_px: np.ndarray, x_split: float, *, keep_left: bool, xh: float) -> float:
    """Arc length (xh units) of the part of a px polyline on one side of a
    vertical line, crossing segments split by linear interpolation.

    The seam calibration asks how much of the chain's connector reaches back
    INTO the left letter's ink column (`keep_left`, against
    `analyze._ink_extent_x`'s `a_max_x`) and how far it reaches into the right
    letter's (`keep_left=False`, against `b_min_x`).
    """
    pts = np.asarray(poly_px, dtype=float).reshape(-1, 2)
    if len(pts) < 2 or xh <= 0:
        return 0.0
    total = 0.0
    for p, q in zip(pts[:-1], pts[1:], strict=True):
        seg = float(np.hypot(q[0] - p[0], q[1] - p[1]))
        if seg == 0.0:
            continue
        inside_p = (p[0] < x_split) if keep_left else (p[0] > x_split)
        inside_q = (q[0] < x_split) if keep_left else (q[0] > x_split)
        if inside_p and inside_q:
            total += seg
        elif inside_p or inside_q:
            t = (x_split - p[0]) / (q[0] - p[0])
            total += seg * abs(t if inside_p else 1.0 - t)
    return total / xh


def polyline_shape_delta(a_px: np.ndarray, b_px: np.ndarray, xh: float) -> tuple[float, float] | None:
    """(mean, P90) pointwise distance between two fitted centerlines of the SAME
    letter, in xh units, with the residual global shift removed.

    Both are resampled to `SHAPE_SAMPLES` arc-length-uniform points, and the
    median distance is subtracted before taking absolutes — `analyze._stub_vs_body_delta`'s
    idiom: a pure translation between two fits of the same ink is registration,
    not a shape difference.
    """
    pa = np.asarray(a_px, dtype=float).reshape(-1, 2)
    pb = np.asarray(b_px, dtype=float).reshape(-1, 2)
    if len(pa) < 2 or len(pb) < 2 or xh <= 0:
        return None
    ra = _resample_polyline(pa, SHAPE_SAMPLES)
    rb = _resample_polyline(pb, SHAPE_SAMPLES)
    d = np.hypot(*(ra - rb).T) / xh
    d = np.abs(d - np.median(d))
    return float(d.mean()), float(np.percentile(d, 90))


def anchor_deltas(chart: np.ndarray, fitted: np.ndarray) -> np.ndarray | None:
    """Per-anchor displacement (units, residual global shift removed) of a fit
    against the chart row it started from — `analyze._stub_vs_body_delta`'s
    first three lines, kept per anchor instead of averaged."""
    a = np.asarray(chart, dtype=float).reshape(-1, 2)
    b = np.asarray(fitted, dtype=float).reshape(-1, 2)
    if len(a) == 0 or len(a) != len(b):
        return None
    d = np.hypot(*(b - a).T)
    return np.abs(d - np.median(d))


def body_stroke_bounds(anchors: np.ndarray, stroke_starts: Sequence[int]) -> tuple[list[int], int, int]:
    """(anchor bounds, first body stroke, last body stroke) under the composer's
    diacritic rule — a non-first stroke floating entirely above the midband is a
    diacritic. Mirrors `analyze.trace_letter_ductus` so the chain's stub numbers
    are cut at the same strokes the baseline's are."""
    bounds = [*(s for s in stroke_starts if 0 <= s < len(anchors)), len(anchors)]
    if bounds[0] != 0:
        bounds = [0, *bounds]
    diacritic = [
        si > 0 and bool((anchors[a:b, 1] > 1.0).all())
        for si, (a, b) in enumerate(zip(bounds[:-1], bounds[1:], strict=True))
    ]
    body = [i for i, d in enumerate(diacritic) if not d] or [0]
    return bounds, body[0], body[-1]


def _r(value: Any, digits: int = 3) -> float | None:
    """Round to a JSON/CSV-safe float; None for missing or non-finite."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return round(v, digits) if math.isfinite(v) else None


# ------------------------------------------------------- MAD noise floor (M4)


def load_anchor_mad(
    style: str, sets: Sequence[str], *, path: Path | None = None, fixtures_root: Path = DEFAULT_FIXTURES_DIR
) -> dict:
    """The hand's per-anchor MAD hull, if the fixture root carries one.

    The aggregates are the H1 statistics layer (`GET /hands/{id}/aggregates`,
    `hull.anchor_mad`); a fixture root that was frozen with them has an
    `aggregates.json` beside `templates.json`. Absent — the usual case — M4
    reports the deltas with a pooled reference and says so, rather than
    inventing a floor.

    Returns `{"by_key": {glyph_key: (K, 2) array}, "pooled": float | None,
    "source": str}`.
    """
    payload: Any = None
    if path is not None:
        candidates = [path]
    else:
        candidates = []
        for which in sets:
            try:
                candidates.append(_root_for(fixtures_root, style, which) / "aggregates.json")
            except (KeyError, OSError):
                continue
    source = "none"
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            payload = json.loads(candidate.read_text())
        except (OSError, ValueError) as exc:
            print(f"warning: ignoring {candidate} ({type(exc).__name__}: {exc}) — M4 runs without a MAD floor")
            continue
        source = str(candidate)
        break

    rows: Iterable[Any]
    if isinstance(payload, dict):
        rows = [{"glyph_key": k, **v} for k, v in payload.items() if isinstance(v, dict)]
    elif isinstance(payload, list):
        rows = [r for r in payload if isinstance(r, dict)]
    else:
        rows = []

    by_key: dict[str, np.ndarray] = {}
    for row in rows:
        key = row.get("glyph_key")
        if not key or int(row.get("variant", 0) or 0) != 0:
            continue
        mad = (row.get("hull") or {}).get("anchor_mad")
        if not mad:
            continue
        arr = np.asarray(mad, dtype=float).reshape(-1, 2)
        if len(arr):
            by_key[str(key)] = arr
    pooled = None
    if by_key:
        pooled = float(np.median(np.concatenate([np.hypot(a[:, 0], a[:, 1]) for a in by_key.values()])))
    return {"by_key": by_key, "pooled": pooled, "source": source}


def _mad_reference(mad_table: dict, key: str, n_anchors: int) -> tuple[np.ndarray | None, str]:
    """Per-anchor MAD magnitudes for one glyph, or the pooled scalar broadcast.

    The pooled fallback is explicitly labelled: 49 of the 62 authored Sütterlin
    glyphs have no aggregate row, and a pooled floor is a reference, not this
    glyph's own measured spread.
    """
    arr = (mad_table.get("by_key") or {}).get(key)
    if arr is not None and len(arr) == n_anchors:
        return np.hypot(arr[:, 0], arr[:, 1]), "aggregate"
    pooled = mad_table.get("pooled")
    if pooled is not None:
        return np.full(n_anchors, float(pooled)), "pooled"
    return None, "none"


# ------------------------------------------------------------- per occurrence


def _units_from_px(pts_px: np.ndarray, xh: float, tx: float, ty: float, baseline_row: float) -> np.ndarray:
    """Crop px → composed word frame (x right, y up, baseline 0) — the inverse
    of `analyze._to_px`."""
    a = np.asarray(pts_px, dtype=float).reshape(-1, 2)
    return np.column_stack([(a[:, 0] - tx) / xh, (baseline_row + ty - a[:, 1]) / xh])


def _fill_baseline(row: dict, d: JoinDissection) -> None:
    """The independent-fit half of one occurrence row."""
    row["base_gen_chamfer"] = _r(d.gen_chamfer)
    row["base_tail_adapt"] = _r(d.tail_adapt)
    row["base_head_adapt"] = _r(d.head_adapt)
    row["base_at_bound"] = bool(d.a.at_bound or d.b.at_bound)
    row["base_a_resid"] = _r(d.a.resid_after)
    row["base_b_resid"] = _r(d.b.resid_after)
    row["base_real_pts"] = int(len(d.real_px))
    row["base_empty_join"] = bool(len(d.real_px) == 0)
    for tag, trace in (("a", d.a_trace), ("b", d.b_trace)):
        row[f"base_{tag}_converged"] = None if trace is None else bool(trace.converged)
        row[f"base_{tag}_geo_rmse_px"] = None if trace is None else _r(trace.geo_rmse_px)
        row[f"base_{tag}_body_delta"] = None if trace is None else _r(trace.body_delta)
    row["base_a_tail_stub_delta"] = None if d.a_trace is None else _r(d.a_trace.tail_stub_delta)
    row["base_b_head_stub_delta"] = None if d.b_trace is None else _r(d.b_trace.head_stub_delta)
    row["base_converged"] = (
        None if d.a_trace is None or d.b_trace is None else bool(d.a_trace.converged and d.b_trace.converged)
    )


def _fill_chain_segments(row: dict, fit: Any) -> tuple[Any, Any, Any]:
    """Per-segment residuals and gates; returns (L, C, R)."""
    letters = [s for s in fit.segments if s.kind == "letter"]
    connectors = [s for s in fit.segments if s.kind == "connector"]
    left = letters[0] if letters else None
    right = letters[-1] if len(letters) > 1 else None
    conn = connectors[0] if connectors else None
    for tag, seg in (("l", left), ("c", conn), ("r", right)):
        row[f"chain_{tag}_converged"] = None if seg is None else bool(seg.converged)
        row[f"chain_{tag}_geo_rmse_px"] = None if seg is None else _r(seg.geo_rmse_px)
        row[f"chain_{tag}_cov_rmse_px"] = None if seg is None else _r(seg.cov_rmse_px)
        row[f"chain_{tag}_n_cov"] = None if seg is None else int(seg.n_cov)
        row[f"chain_{tag}_max_anchor_delta"] = None if seg is None else _r(seg.max_anchor_delta)
    row["chain_converged"] = bool(fit.converged)
    row["chain_connector_yielded"] = bool(conn is not None and conn.converged and conn.n_cov > 0)
    return left, conn, right


def _fill_chain_placement(row: dict, fit: Any, slot_a: int) -> None:
    shifts = dict(fit.slot_shift_units or {})
    bounds = dict(fit.slot_at_bound or {})
    for tag, slot in (("l", slot_a), ("r", slot_a + 1)):
        shift = shifts.get(slot)
        row[f"chain_{tag}_dx"] = None if shift is None else _r(shift[0])
        row[f"chain_{tag}_dy"] = None if shift is None else _r(shift[1])
        row[f"chain_{tag}_at_bound"] = bool(bounds.get(slot, False))
    row["chain_at_bound"] = bool(row["chain_l_at_bound"] or row["chain_r_at_bound"])
    gx, gy = fit.global_shift_units
    row["chain_global_dx"] = _r(gx)
    row["chain_global_dy"] = _r(gy)
    row["chain_cut_l"], row["chain_cut_r"] = (int(fit.cut_indices[0]), int(fit.cut_indices[1]))
    meta = dict(fit.fit_meta or {})
    row["chain_status_msg"] = str(meta.get("status", ""))[:80]
    row["chain_n_params"] = meta.get("n_params")


def _fill_letter_shape(
    row: dict, tag: str, case: WordCase, slot_index: int, seg: Any, trace: Any, mad_table: dict, xh: float
) -> None:
    """M4 for one letter: the chain's own displacement from the chart row
    against the MAD floor, plus its distance to the independent trace.

    The per-anchor chain-vs-trace comparison the plan sketches is not
    reachable — `analyze.DuctusTrace` publishes the independent fit's anchor
    displacements only as the `tail_stub_delta`/`head_stub_delta`/`body_delta`
    means, and re-running `fit_template_to_instance` per letter to recover them
    would double the harness' cost. So M4 reports two comparable numbers
    instead: the ANCHOR-space displacement from the shared chart reference (the
    quantity the MAD hull is expressed in, available for the chain; the trace's
    published means are its counterpart) and the SAMPLE-space distance between
    the two fitted centerlines, which is the direct chain-vs-trace shape delta.
    """
    slot = case.slots[slot_index]
    tpl = case.templates.get(slot.key) if slot.key else None
    row[f"chain_{tag}_key"] = slot.key or ""
    if seg is None or tpl is None:
        return
    chart = np.asarray(tpl["anchors"], dtype=float)
    fitted = seg.fitted_anchors
    if fitted is not None:
        deltas = anchor_deltas(chart, np.asarray(fitted, dtype=float))
        if deltas is not None:
            row[f"chain_{tag}_delta_mean"] = _r(float(deltas.mean()), 4)
            row[f"chain_{tag}_delta_p90"] = _r(float(np.percentile(deltas, 90)), 4)
            mad, source = _mad_reference(mad_table, slot.key or "", len(deltas))
            row[f"chain_{tag}_mad_source"] = source
            row[f"chain_{tag}_frac_within_mad"] = None if mad is None else _r(float((deltas <= mad).mean()))
        stub_bounds, first_body, last_body = body_stroke_bounds(
            chart, ((tpl.get("trace_meta") or {}).get("stroke_starts") or [0])
        )
        if len(chart) == len(np.asarray(fitted, dtype=float)):
            from_end = tag == "l"
            si = last_body if from_end else first_body
            stub, body = _stub_vs_body_delta(
                chart, np.asarray(fitted, dtype=float), (stub_bounds[si], stub_bounds[si + 1]), from_end=from_end
            )
            row[f"chain_{tag}_stub_delta"] = _r(stub)
            row[f"chain_{tag}_body_delta"] = _r(body)
    if trace is not None:
        delta = polyline_shape_delta(seg.polyline_px, trace.polyline_px, xh)
        if delta is not None:
            row[f"chain_{tag}_vs_trace_mean"] = _r(delta[0], 4)
            row[f"chain_{tag}_vs_trace_p90"] = _r(delta[1], 4)


def _fill_connector_metrics(row: dict, d: JoinDissection, fit: Any, conn: Any) -> None:
    """M3 (`dconn` for the generated and the chained connector) and the seam
    calibration shares."""
    xh = d.result.xh_px
    tx, ty = d.result.registration["tx"], d.result.registration["ty"]
    baseline_row = d.result.baseline_row
    exit_u = _px_to_units(d.exit_px, xh, tx, ty, baseline_row)
    entry_u = _px_to_units(d.entry_px, xh, tx, ty, baseline_row)

    ink_conn = None
    if len(d.real_px):
        ink_u = _units_from_px(d.real_px, xh, tx, ty, baseline_row)
        # `end_dy=0` deliberately: the harvest's baseline-lock shear exists to
        # store an override for the baseline-locked COMPOSER, while both curves
        # here are read in this occurrence's own fitted frame. Applying it to
        # one side only would inject exactly the artifact `dconn` avoids.
        ink_conn = connector_points(exit_u, entry_u, ink_u, end_dy=0.0)

    gen_u = _units_from_px(d.gen_px, xh, tx, ty, baseline_row)
    if ink_conn is not None:
        row["dconn_gen"] = _r(dconn(gen_u, ink_conn))

    chain_u = np.asarray(getattr(fit, "connector_units", None), dtype=float).reshape(-1, 2)
    if len(chain_u) >= 2:
        # Same construction as the ink side (strictly-between clip, smoothing,
        # downsampling), so the two curves differ by geometry alone.
        chain_conn = connector_points(tuple(chain_u[0]), tuple(chain_u[-1]), chain_u[1:-1], end_dy=0.0)
        if ink_conn is not None:
            row["dconn_chain"] = _r(dconn(chain_conn, ink_conn))
            if row.get("dconn_gen") is not None and row.get("dconn_chain") is not None:
                row["dconn_delta"] = _r(row["dconn_chain"] - row["dconn_gen"])

    if conn is not None and len(np.asarray(conn.polyline_px, dtype=float).reshape(-1, 2)) >= 2:
        _, a_max_x = _ink_extent_x(d.a.body_px, baseline_row, xh)
        b_min_x, _ = _ink_extent_x(d.b.body_px, baseline_row, xh)
        row["chain_tail_share"] = _r(arc_share(conn.polyline_px, a_max_x, keep_left=True, xh=xh))
        row["chain_head_share"] = _r(arc_share(conn.polyline_px, b_min_x, keep_left=False, xh=xh))


def occurrence_row(case: WordCase, slot_a: int, result: WordDeriveResult, mad_table: dict) -> dict:
    """Run both paths on ONE occurrence and flatten everything into one row."""
    left = _key_base(case.slots[slot_a].key, case.slots[slot_a].position)
    right = _key_base(case.slots[slot_a + 1].key, case.slots[slot_a + 1].position)
    row: dict[str, Any] = {
        "id": case.id,
        "word": case.word,
        "kind": case.kind,
        "slot": slot_a,
        "left": left,
        "right": right,
        "pair": f"{left}→{right}",
        "pair_class": pair_class(left),
        "capital": bool(left[:1].isupper()),
        "status": "ok",
        "detail": "",
        "chain_status": "skipped",
    }
    d = dissect_occurrence(case, slot_a, trace=True, result=result)
    if d is None:
        row["status"] = "skipped"
        row["detail"] = "dissection returned None (missing template / unscorable)"
        return row
    _fill_baseline(row, d)

    started = time.perf_counter()
    try:
        fit = chain_mod.fit_pair_chain(case, slot_a, d, result=result)
    except Exception as exc:  # noqa: BLE001 — one bad occurrence must not end the run
        row["chain_status"] = "error"
        row["detail"] = f"{type(exc).__name__}: {exc}"[:200]
        return row
    row["chain_secs"] = _r(time.perf_counter() - started, 2)
    if fit is None:
        row["chain_status"] = "none"
        return row
    row["chain_status"] = "ok"
    left_seg, conn_seg, right_seg = _fill_chain_segments(row, fit)
    _fill_chain_placement(row, fit, slot_a)
    _fill_letter_shape(row, "l", case, slot_a, left_seg, d.a_trace, mad_table, d.result.xh_px)
    _fill_letter_shape(row, "r", case, slot_a + 1, right_seg, d.b_trace, mad_table, d.result.xh_px)
    _fill_connector_metrics(row, d, fit, conn_seg)
    return row


def case_rows(job: tuple[WordCase, list[int]], mad_table: dict) -> list[dict]:
    """Every selected occurrence of ONE case — composed once, dissected per join.

    This is the ProcessPoolExecutor unit of work: a word with five joins runs
    `derive_word` ONCE (the `result=` kwarg on `dissect_occurrence` and
    `fit_pair_chain`) instead of ten times. Nothing raised inside can end the
    run — a failure is a row.
    """
    case, slots = job
    try:
        result = derive_word(case)
    except Exception as exc:  # noqa: BLE001
        detail = f"{type(exc).__name__}: {exc}"[:200]
        return [
            {"id": case.id, "kind": case.kind, "slot": s, "status": "error", "detail": detail, "chain_status": "error"}
            for s in slots
        ]
    rows = []
    for slot_a in slots:
        try:
            rows.append(occurrence_row(case, slot_a, result, mad_table))
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    "id": case.id,
                    "kind": case.kind,
                    "slot": slot_a,
                    "status": "error",
                    "detail": f"{type(exc).__name__}: {exc}"[:200],
                    "chain_status": "error",
                }
            )
    return rows


# ------------------------------------------------------------------ selection


def plan_occurrences(
    sets: Sequence[str],
    style: str,
    *,
    pairs: set[tuple[str, str]] | None = None,
    ids: set[str] | None = None,
    max_occ: int = 0,
) -> list[tuple[WordCase, list[int]]]:
    """The occurrences to run, grouped per case in deterministic order.

    Iteration order is set → manifest order → slot, so `--max-occ` always caps
    the SAME occurrences of a pair and two runs are comparable.
    """
    per_pair: Counter[tuple[str, str]] = Counter()
    jobs: list[tuple[WordCase, list[int]]] = []
    for which in sets:
        for case in iter_fixture_word_cases(which=which, style=style):
            if not case.scorable or not case.has_specimen:
                continue
            if ids and case.id not in ids:
                continue
            slots = []
            for slot_a, left, right in _adjacent_joined(case):
                if pairs and (left, right) not in pairs:
                    continue
                if max_occ and per_pair[(left, right)] >= max_occ:
                    continue
                per_pair[(left, right)] += 1
                slots.append(slot_a)
            if slots:
                jobs.append((case, slots))
    return jobs


# ----------------------------------------------------------------- aggregation


def _values(rows: Iterable[dict], field: str) -> list[float]:
    return [float(r[field]) for r in rows if r.get(field) is not None]


def summarize(values: Sequence[float]) -> dict:
    """n / median / mean / P90 of a value column (all None when empty)."""
    if not values:
        return {"n": 0, "median": None, "mean": None, "p90": None}
    arr = np.asarray(values, dtype=float)
    return {
        "n": len(arr),
        "median": round(float(np.median(arr)), 4),
        "mean": round(float(arr.mean()), 4),
        "p90": round(float(np.percentile(arr, 90)), 4),
    }


def paired_counts(rows: Iterable[dict], base_field: str, chain_field: str) -> dict:
    """The paired convergence table over the rows where BOTH gates are known.

    A pooled rate can stay flat while the two paths swap which occurrences they
    win, so the chain-only / baseline-only cells are the actual M1 answer.
    """
    both = chain_only = base_only = neither = 0
    base_true = chain_true = 0
    n = 0
    for r in rows:
        b, c = r.get(base_field), r.get(chain_field)
        if b is None or c is None:
            continue
        n += 1
        base_true += bool(b)
        chain_true += bool(c)
        if b and c:
            both += 1
        elif c:
            chain_only += 1
        elif b:
            base_only += 1
        else:
            neither += 1
    return {
        "n": n,
        "both": both,
        "chain_only": chain_only,
        "base_only": base_only,
        "neither": neither,
        "base_rate": round(base_true / n, 3) if n else None,
        "chain_rate": round(chain_true / n, 3) if n else None,
    }


def per_letter_rates(rows: Iterable[dict]) -> dict[str, dict]:
    """Convergence per glyph key — a letter is counted once per occurrence it
    takes part in, on whichever side of the join it sits."""
    out: dict[str, dict] = {}
    for r in rows:
        for key_field, base_field, chain_field in (
            ("chain_l_key", "base_a_converged", "chain_l_converged"),
            ("chain_r_key", "base_b_converged", "chain_r_converged"),
        ):
            key = r.get(key_field) or ""
            b, c = r.get(base_field), r.get(chain_field)
            if not key or b is None or c is None:
                continue
            entry = out.setdefault(key, {"n": 0, "base": 0, "chain": 0})
            entry["n"] += 1
            entry["base"] += bool(b)
            entry["chain"] += bool(c)
    return out


def empty_join_gain(rows: Iterable[dict]) -> dict:
    """M2 — of the joins whose specimen ink `_real_join` cannot read today, how
    many does the chain's connector yield?"""
    per_pair: dict[str, dict] = {}
    n_empty = n_gained = 0
    for r in rows:
        if not r.get("base_empty_join"):
            continue
        n_empty += 1
        gained = bool(r.get("chain_connector_yielded"))
        n_gained += gained
        entry = per_pair.setdefault(r.get("pair", "?"), {"empty": 0, "gained": 0})
        entry["empty"] += 1
        entry["gained"] += gained
    return {"n_empty": n_empty, "n_gained": n_gained, "per_pair": per_pair}


def sign_test(deltas: Sequence[float], *, eps: float = 1e-9) -> dict:
    """Two-sided sign test on paired differences — the non-parametric trend
    statement M4.2's kill criterion needs (are the chain's stub deltas LARGER
    than the independent trace's more often than chance?)."""
    pos = sum(1 for d in deltas if d > eps)
    neg = sum(1 for d in deltas if d < -eps)
    ties = len(deltas) - pos - neg
    n = pos + neg
    p = None
    if n:
        k = min(pos, neg)
        tail = sum(math.comb(n, i) for i in range(k + 1))
        p = min(1.0, 2.0 * tail / (2**n))
    return {"n": n, "pos": pos, "neg": neg, "ties": ties, "p": None if p is None else round(p, 5)}


def paired_deltas(rows: Iterable[dict], chain_field: str, base_field: str) -> list[float]:
    return [
        float(r[chain_field]) - float(r[base_field])
        for r in rows
        if r.get(chain_field) is not None and r.get(base_field) is not None
    ]


# -------------------------------------------------------------------- reports


def _pct(num: int, den: int) -> str:
    return f"{num}/{den} ({100.0 * num / den:.0f}%)" if den else f"{num}/0 (—)"


def _fmt(value: Any, digits: int = 3) -> str:
    return "—" if value is None else f"{float(value):.{digits}f}"


def print_rows(rows: Sequence[dict]) -> None:
    """One line per occurrence, in `tools/pairlab/__main__.py`'s summary idiom."""
    for r in rows:
        if r.get("status") != "ok":
            print(f"  {r.get('id', '?'):<14} slot {r.get('slot')} {r.get('status').upper()}: {r.get('detail', '')}")
            continue
        gate = lambda v: "—" if v is None else ("Y" if v else "n")  # noqa: E731
        print(
            f"  {r['id']:<14} [{r['kind']}]{'!' if r.get('base_at_bound') else ' '} {r['pair']:<12} "
            f"conv base {gate(r.get('base_a_converged'))}{gate(r.get('base_b_converged'))} "
            f"chain {gate(r.get('chain_l_converged'))}{gate(r.get('chain_c_converged'))}{gate(r.get('chain_r_converged'))}  "
            f"dconn gen {_fmt(r.get('dconn_gen'))} chain {_fmt(r.get('dconn_chain'))}  "
            f"stub {_fmt(r.get('base_a_tail_stub_delta'), 2)}->{_fmt(r.get('chain_l_stub_delta'), 2)}  "
            f"seam {_fmt(r.get('chain_tail_share'), 2)}/{_fmt(r.get('chain_head_share'), 2)}"
            + ("" if r.get("chain_status") == "ok" else f"  [chain {r.get('chain_status')}: {r.get('detail', '')}]")
        )


def print_report(rows: Sequence[dict], *, mad_table: dict, sets: Sequence[str], style: str) -> None:
    """The four Stage-A metric blocks + the kill-criterion blocks."""
    ok = [r for r in rows if r.get("status") == "ok"]
    chained = [r for r in ok if r.get("chain_status") == "ok"]
    print()
    print("=== n (restated, never asserted) ===")
    print(
        f"  sets {'+'.join(sets)} · style {style} · occurrences {len(rows)}  "
        f"(ok {len(ok)} · skipped {sum(1 for r in rows if r.get('status') == 'skipped')} · "
        f"error {sum(1 for r in rows if r.get('status') == 'error')})"
    )
    print(
        f"  chain: ok {len(chained)} · none {sum(1 for r in ok if r.get('chain_status') == 'none')} · "
        f"error {sum(1 for r in ok if r.get('chain_status') == 'error')}"
    )
    print(
        f"  distinct pairs {len({r['pair'] for r in ok})} · distinct specimens {len({r['id'] for r in ok})} · "
        f"kinds {dict(Counter(r['kind'] for r in ok))}"
    )
    for detail, count in Counter(r.get("detail", "") for r in rows if r.get("detail")).most_common(5):
        print(f"  ! {count}x {detail}")

    print()
    print("=== M1 — convergence (chain vs. the two independent M4 traces) ===")
    table = paired_counts(chained, "base_converged", "chain_converged")
    print(f"  pooled  baseline {_fmt(table['base_rate'], 3)}  chain {_fmt(table['chain_rate'], 3)}  (n={table['n']})")
    print(
        f"  paired  both {table['both']} · chain-only {table['chain_only']} · "
        f"baseline-only {table['base_only']} · neither {table['neither']}"
    )
    letters = per_letter_rates(chained)
    if letters:
        print("  per letter (worst chain rate first):")
        ranked = sorted(letters.items(), key=lambda kv: (kv[1]["chain"] / kv[1]["n"], -kv[1]["n"]))
        for key, e in ranked[:20]:
            print(f"    {key:<8} n {e['n']:>3}  base {_pct(e['base'], e['n']):<14} chain {_pct(e['chain'], e['n'])}")

    print()
    print("=== M2 — joins with no readable specimen ink today ===")
    gain = empty_join_gain(chained)
    print(
        f"  empty joins {gain['n_empty']} of {len(chained)} chained occurrences · "
        f"yielded by the chain {_pct(gain['n_gained'], gain['n_empty'])}"
    )
    for pair, e in sorted(gain["per_pair"].items(), key=lambda kv: -kv[1]["empty"]):
        print(f"    {pair:<12} empty {e['empty']:>2}  gained {e['gained']:>2}")

    print()
    print("=== M3 — connector shape (dconn vs. the specimen's own joining stroke) ===")
    gen = summarize(_values(chained, "dconn_gen"))
    ch = summarize(_values(chained, "dconn_chain"))
    print(
        f"  generated  n {gen['n']:>3}  median {_fmt(gen['median'])}  mean {_fmt(gen['mean'])}  p90 {_fmt(gen['p90'])}"
    )
    print(f"  chain      n {ch['n']:>3}  median {_fmt(ch['median'])}  mean {_fmt(ch['mean'])}  p90 {_fmt(ch['p90'])}")
    deltas = _values(chained, "dconn_delta")
    if deltas:
        st = sign_test(deltas)
        print(
            f"  paired Δ (chain − generated)  median {_fmt(float(np.median(deltas)), 4)}  "
            f"better {st['neg']} · worse {st['pos']} · p {st['p']}"
        )
    by_class: dict[str, list[dict]] = defaultdict(list)
    for r in chained:
        by_class[r.get("pair_class", "?")].append(r)
    for cls, group in sorted(by_class.items()):
        g, c = summarize(_values(group, "dconn_gen")), summarize(_values(group, "dconn_chain"))
        print(f"    {cls:<16} n {c['n']:>3}  gen median {_fmt(g['median'])}  chain median {_fmt(c['median'])}")

    print()
    print("=== M4 — letter shape vs. the MAD noise floor ===")
    print(f"  MAD source: {mad_table.get('source')}  pooled per-anchor MAD {_fmt(mad_table.get('pooled'), 4)}")
    if mad_table.get("source") == "none":
        print("  ! no aggregates.json in the fixture root — deltas are reported WITHOUT a measured floor")
    vs_trace = summarize(_values(chained, "chain_l_vs_trace_mean") + _values(chained, "chain_r_vs_trace_mean"))
    p90 = summarize(_values(chained, "chain_l_vs_trace_p90") + _values(chained, "chain_r_vs_trace_p90"))
    print(
        f"  chain vs. independent trace (sample space, xh)  n {vs_trace['n']:>3}  "
        f"mean-Δ median {_fmt(vs_trace['median'], 4)}  P90-Δ median {_fmt(p90['median'], 4)}"
    )
    anchor = summarize(_values(chained, "chain_l_delta_mean") + _values(chained, "chain_r_delta_mean"))
    frac = summarize(_values(chained, "chain_l_frac_within_mad") + _values(chained, "chain_r_frac_within_mad"))
    base_body = summarize(_values(chained, "base_a_body_delta") + _values(chained, "base_b_body_delta"))
    print(
        f"  displacement from the chart row (anchor space, xh)  chain median {_fmt(anchor['median'], 4)}  "
        f"trace body-delta median {_fmt(base_body['median'], 4)}"
    )
    print(f"  anchors within their MAD  median share {_fmt(frac['median'])}  (n {frac['n']})")
    sources = Counter(
        r.get(f"chain_{t}_mad_source") for r in chained for t in ("l", "r") if r.get(f"chain_{t}_mad_source")
    )
    print(f"  MAD reference per letter: {dict(sources)}")

    print()
    print("=== kill — tail-stub trend (chain's coupling stub vs. the trace's) ===")
    stub_deltas = paired_deltas(chained, "chain_l_stub_delta", "base_a_tail_stub_delta")
    st = sign_test(stub_deltas)
    print(
        f"  paired Δ  n {st['n']}  median {_fmt(float(np.median(stub_deltas)) if stub_deltas else None, 4)}  "
        f"chain larger {st['pos']} · smaller {st['neg']} · ties {st['ties']} · p {st['p']}"
    )
    for cls, group in sorted(by_class.items()):
        d = paired_deltas(group, "chain_l_stub_delta", "base_a_tail_stub_delta")
        print(f"    {cls:<16} n {len(d):>3}  median Δ {_fmt(float(np.median(d)) if d else None, 4)}")

    print()
    print("=== kill — capital partition ===")
    for label, group in (
        ("capital", [r for r in chained if r.get("capital")]),
        ("lowercase", [r for r in chained if not r.get("capital")]),
    ):
        conv = paired_counts(group, "base_converged", "chain_converged")
        geo = summarize(_values(group, "chain_l_geo_rmse_px") + _values(group, "chain_r_geo_rmse_px"))
        mad = summarize(_values(group, "chain_l_max_anchor_delta") + _values(group, "chain_r_max_anchor_delta"))
        print(
            f"  {label:<10} n {len(group):>3}  base {_fmt(conv['base_rate'])} chain {_fmt(conv['chain_rate'])}  "
            f"geo rmse median {_fmt(geo['median'], 2)} px  max anchor delta median {_fmt(mad['median'])}"
        )

    print()
    print("=== kill — seam calibration ===")
    tail = summarize(_values(chained, "chain_tail_share"))
    head = summarize(_values(chained, "chain_head_share"))
    base_tail = summarize(_values(chained, "base_tail_adapt"))
    base_head = summarize(_values(chained, "base_head_adapt"))
    lo, hi = SEAM_TARGET_UNITS
    print(f"  target zone {lo}–{hi} xh per side (uebergaenge-befund.md §5)")
    print(
        f"  chain tail share  median {_fmt(tail['median'])}  p90 {_fmt(tail['p90'])}   "
        f"baseline tail_adapt median {_fmt(base_tail['median'])}"
    )
    print(
        f"  chain head share  median {_fmt(head['median'])}  p90 {_fmt(head['p90'])}   "
        f"baseline head_adapt median {_fmt(base_head['median'])}"
    )
    over = sum(1 for v in _values(chained, "chain_tail_share") + _values(chained, "chain_head_share") if v > hi)
    total = len(_values(chained, "chain_tail_share")) + len(_values(chained, "chain_head_share"))
    print(f"  shares above {hi} xh: {_pct(over, total)}  → calibrate CHAIN_CONNECTOR_SMOOTH_WEIGHT / lambda if high")
    for cls, group in sorted(by_class.items()):
        t, h = summarize(_values(group, "chain_tail_share")), summarize(_values(group, "chain_head_share"))
        print(f"    {cls:<16} n {t['n']:>3}  tail {_fmt(t['median'])}  head {_fmt(h['median'])}")


# ------------------------------------------------------------------------ CLI


def write_json(rows: Sequence[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(rows), indent=1, ensure_ascii=False))
    print(f"wrote {path}")


def write_csv(rows: Sequence[dict], path: Path) -> None:
    """Flat CSV over the union of all row keys (a row that failed early simply
    leaves its columns empty)."""
    fields: list[str] = []
    seen: set[str] = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                fields.append(k)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path}")


def main() -> None:
    p = argparse.ArgumentParser(
        prog="chainbench", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--set",
        dest="which",
        choices=["words", "pairs", "all"],
        default="pairs",
        help="fixture sets to run (default: pairs — the Abb.-20 drills, ~4 min)",
    )
    p.add_argument("--style", default="suetterlin", help="fixture style dir (default: suetterlin)")
    p.add_argument("--pairs", help="restrict to base pairs, comma separated ('de,on' or the colon form 'longs:t')")
    p.add_argument("--ids", help="restrict to specimen ids, comma separated (e.g. Bi,Du)")
    p.add_argument("--max-occ", type=int, default=0, help="cap occurrences per pair (0 = all)")
    p.add_argument("--jobs", type=int, default=1, help="parallel worker processes over CASES (default 1)")
    p.add_argument("--json", type=Path, help="write the flat rows here (e.g. temp/stage_a.json)")
    p.add_argument("--csv", type=Path, help="write the flat rows here as CSV (e.g. temp/stage_a.csv)")
    p.add_argument("--aggregates", type=Path, help="aggregates JSON supplying the M4 MAD floor (default: fixture root)")
    args = p.parse_args()

    sets = ("words", "pairs") if args.which == "all" else (args.which,)
    pairs = parse_pair_filter(args.pairs) if args.pairs else None
    ids = {s.strip() for s in args.ids.split(",") if s.strip()} if args.ids else None

    try:
        jobs = plan_occurrences(sets, args.style, pairs=pairs, ids=ids, max_occ=args.max_occ)
    except KeyError as exc:
        raise SystemExit(f"{exc} — chainbench needs the frozen word-bench fixtures") from exc
    n_occ = sum(len(s) for _, s in jobs)
    if not n_occ:
        raise SystemExit(f"no matching occurrence in {'/'.join(sets)}")
    mad_table = load_anchor_mad(args.style, sets, path=args.aggregates)
    print(f"chainbench: {n_occ} occurrence(s) over {len(jobs)} case(s) · sets {'/'.join(sets)} · jobs {args.jobs}")

    started = time.perf_counter()
    rows: list[dict] = []
    worker = functools.partial(case_rows, mad_table=mad_table)
    if args.jobs > 1:
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            for produced in pool.map(worker, jobs):
                rows.extend(produced)
    else:
        for job in jobs:
            rows.extend(worker(job))
    print_rows(rows)
    print_report(rows, mad_table=mad_table, sets=sets, style=args.style)
    print(f"\n  wall {time.perf_counter() - started:.1f}s  (repo root {REPO_ROOT})")

    if args.json:
        write_json(rows, args.json)
    if args.csv:
        write_csv(rows, args.csv)


if __name__ == "__main__":
    main()
