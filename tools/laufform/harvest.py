"""Laufform harvest: median running forms + per-occurrence rows.

The jul31 doctrine split (qualitaetsmetrik.md §6): the chart cell is the
DUCTUS PRIOR (stroke order, crossings), the written specimen words are the
FORM MODEL. This tool M4-fits every letter occurrence of the frozen word
fixtures onto the plates and produces two artefacts:

* per-letter MEDIANS over the clean fits (the running shape with the
  template's own topology intact), written as `templates` Laufform-variant
  DRAFT rows through the admin API
  (`PUT /sources/{id}/templates/{key}/laufform`), and
* every clean per-occurrence fit itself (handmodell plan H1 — occurrences,
  not just medians), written as `instances` rows in one batch
  (`PUT /sources/{id}/instances`, `replace: true`) under the specimen hand, and
* one traced WORD record per specimen (the full learning template: slot
  labels + the fitted letter strokes in the word's registration frame),
  written as `word_instances` rows (`PUT /sources/{id}/word-instances` —
  authored rows survive, the endpoint skips them).

Two fitting paths (`--path`), and the SAME artefacts out of both:

* **`slot`** (default) — every letter fitted on its own, against a
  letter-local skeleton window, exactly as this tool has always done. A word
  record therefore holds the letters and nothing between them.
* **`chain`** (issue #278 Stage B) — every RUN of joined slots
  (`tools.pairlab.chain.chain_runs`) fitted as ONE chain
  `[L, C, L, C, …]` with the seams tied by shared anchors
  (`fit_word_chain`). The per-slot grid fits still run: they supply each
  letter's coverage window and the fallback diagnosis. The letters come out
  as occurrences under the gate cascade of `letter_gate`, and the word record
  gains the CONNECTORS — the pen run really continues
  `last body stroke of Lᵢ → connectorᵢ → first body stroke of Lᵢ₊₁`, which is
  what closes the dead authored branch the word editor has been drawing over.
  The gate and the trace answer different questions: the gate decides what
  becomes a MEASUREMENT (occurrences, medians), the trace shows the whole
  solved run — a letter the gate rejected is flagged in `measurements`, not
  cut out of the pen path.
  Deliberately NO `pair_instances` are written or drafted here: the measured
  join geometry stays a REPORT column (`--diag-csv`), and `glyph_pairs` stays
  the sparse verbatim override.

Dry run prints the per-letter stats and writes ``laufform_drafts.json`` +
``laufform_occurrences.json``; ``--apply`` PUTs both (requires ``--base-url``
and the ``ADMIN_TOKEN`` env var) and is available for the DEFAULT configuration
only — the chain path and the non-`words` sets are report-only until the
measurement round says otherwise. Never run `--apply` against prod without an
explicit go — the composer picks the Laufform rows up immediately for every
flowing /write/word (the occurrence rows never affect rendering).

    uv run python -m tools.laufform.harvest [--style suetterlin]
        [--sets words,pairs] [--path slot|chain] [--jobs 4]
        [--min-n 4] [--rmse-max 2.2] [--out laufform_drafts.json]
        [--occ-out laufform_occurrences.json] [--diag-csv laufform_diag.csv]
        [--apply --base-url http://localhost:8000 --source-id <id>
         --hand-id suetterlin-1922-norm]
"""

from __future__ import annotations

import argparse
import csv
import functools
import json
import os
import urllib.request
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from scipy.ndimage import distance_transform_edt

from core.aggregate import loop_ranges
from core.compose import CAP_RESTART_BASES, _key_base
from core.fit import fit_template_to_instance
from core.laufform import anchor_spike_ratio
from tools.pairlab.analyze import TRACE_WINDOW_MARGIN, _body_items, _fit_letter, _ink_extent_x, _to_px
from tools.pairlab.anchors import LOOP_AWARE_REPAIR, repair_stranded_anchors
from tools.pairlab.chain import chain_runs, fit_word_chain
from tools.pairlab.connector_qc import connector_degenerate, connector_signals
from tools.pairlab.ink_evidence import InkEvidenceOptions, ink_evidence_case
from tools.pairlab.marks import mark_refit_summary, refit_word_marks

# The word-trace assembly lives in `tools.pairlab.trace` so the ink-follower can
# use it without the import cycle `pairlab -> laufform -> pairlab`; re-exported
# here because this module is where its consumers historically found it.
from tools.pairlab.trace import (
    DIACRITIC_MIN_Y,
    MAX_STROKE_POINTS,
    MAX_WORD_STROKES,
    SEAM_DEDUP_PX,
    _is_diacritic,
    _px_to_word_units,
    assemble_word_strokes,
    cap_word_strokes,
    diacritic_stroke_units,
)
from tools.wordlab.cases import iter_fixture_word_cases
from tools.wordlab.derive import WordDeriveResult, derive_word


# The re-exports above, declared (as in `tools.pairlab.gradlab`) so they read as
# deliberate rather than as unused imports. Not this module's whole public API —
# nothing star-imports the harvest, every caller names what it needs.
__all__ = [
    "DIACRITIC_MIN_Y",
    "MAX_STROKE_POINTS",
    "MAX_WORD_STROKES",
    "SEAM_DEDUP_PX",
    "assemble_word_strokes",
    "cap_word_strokes",
]

# „Anker im leeren Papier" (glossar.md §4, qualitaetsmetrik.md §7): the spike
# ratio above which a fitted anchor chain is no longer a measurement of the
# hand. A pen writes arcs and straight lines; a single anchor that leaves the
# stroke and returns one step later is physically impossible, but invisible to
# the fit's objective, where everything is a mean (`e_geo` over
# DEFAULT_N_SAMPLES, `e_reg` over K anchors, MAX_ANCHOR_DELTA far too loose) —
# the measured Sütterlin capital S in „Sprünge" passed QC at
# geo_rmse_px = 1.261 with one anchor 12 px from the nearest ink.
#
# Calibrated on the 245 stored occurrences of the Sütterlin harvest — which are
# ALL chain-path fits (`measurements.fit_path == "chain"`, 245 of 245), so the
# calibration and the gated path are the same population. Distribution of the
# per-stroke ratio: median 2.68, p75 3.86, p90 7.28, p99 23.29, max 32.9. At 8.0
# exactly 23 occurrences (9.4 %) are rejected and NOT ONE glyph drops below
# `core.aggregate.LAUFFORM_MIN_OCCURRENCES` = 3 — nor below the harvest's own
# `--min-n` default of 4. At 6.0 the glyph „g" would fall below the floor, which
# is why the threshold sits here and not lower.
#
# Why 8.0 and not 6.0: at 6.0 the glyph „g" falls from 3 occurrences to 2. On
# its own that would be a QUALITY threshold calibrated on a COVERAGE side
# effect. It only carries together with the reason the floor sits at 3 — from
# three occurrences on, the per-anchor median outvotes one bad one — so „g" at
# n = 3 is precisely the case the floor was built for, and a fourth gate on top
# would take its Laufform away without the existing guard having failed.
#
# Effect on the accepted set (measured in the §7 re-run frame, NOT on the stored
# rows): the worst distance of a fitted centerline to the measured ink drops
# from 0.613 to 0.258 x-heights, its p90 from 0.194 to 0.149. This catches
# DISCONTINUITIES; it is deliberately not an off-the-ink detector, and a smooth
# deviation spread over many anchors passes it untouched.
MAX_ANCHOR_SPIKE_RATIO = 8.0

DIAG_FIELDS = (
    "specimen_id",
    "kind",
    "word",
    "path",
    "slot",
    "keyed_slot",
    "glyph_key",
    "run",
    "accepted",
    "gate",
    "grid_at_bound",
    "grid_resid_before",
    "grid_resid_after",
    "converged",
    "converged_local",
    "geo_rmse_px",
    "cov_rmse_px",
    "cov_rmse_local_px",
    "n_cov",
    "n_cov_local",
    "chain_at_bound",
    "anchor_count_ok",
    # „Anker im leeren Papier": largest in-stroke anchor step over the median
    # one. Reported on every fitted row, so a run says how far the rejected
    # ones were over `MAX_ANCHOR_SPIKE_RATIO` and how much air the kept ones had.
    "anchor_spike_ratio",
    # Post-gate repair (`tools.pairlab.anchors`): how many anchors of this
    # letter were interpolated over before storage. Only ever non-zero on an
    # ACCEPTED row — the gate and `anchor_spike_ratio` judge the UNREPAIRED
    # geometry; a repair is a near-rejection, never a pass.
    "n_repaired",
    "shift_x_units",
    "shift_y_units",
    "conn_reason_adjacent",
    "conn_reason",
    "conn_arc_units",
    "conn_chord_units",
    "conn_seam_left_units",
    "conn_seam_right_units",
    "conn_forward_ratio",
    "conn_gap_units",
    # Chain path only: where this slot's translation block STARTED (xh units).
    # Empty under the composed init; under --chain-seed grid it is the grid
    # placement the descent began from — read `shift_x_units` against it to see
    # how far the solve moved beyond its seed.
    "seed_x_units",
    "seed_y_units",
    "n_params",
    # Chain path only: how many L-BFGS-B iterations the run's solve took and
    # whether the BUDGET stopped it. A capped solve was still descending, so
    # every geometry column in this row is a snapshot of an unfinished descent
    # — read these two before drawing a conclusion from the rest.
    "iterations",
    "hit_iteration_cap",
    "max_iter",
    "seconds",
)


@dataclass(frozen=True)
class HarvestOptions:
    """Everything one case's harvest needs to know — the ProcessPool payload."""

    style: str = "suetterlin"
    rmse_max: float = 2.2
    path: str = "slot"  # "slot" (per-letter M4 fits) | "chain" (word-chain fits)
    # Where the chain's translation blocks START. "composed" is the historical
    # init (blocks at zero = the composed layout); "grid" seeds each block at
    # the letter's own grid placement on its ink — the counter to the placement
    # collapse of uebergaenge-befund.md §5c, where the composed start sits in a
    # basin that stacks a high-exit pair and runs the connector backwards. The
    # objective is identical either way; only the entered basin changes. A grid
    # fit resting on its own search bound is NOT used as a seed (that placement
    # is itself suspect), so such slots keep the composed start.
    chain_seed: str = "composed"  # "composed" | "grid"
    # Measure A1 (`docs/proposals/tintenfolger.md` §7.3): after the body solve,
    # refit each MARK stroke (i-dot, umlaut, u-bow) onto the ink the body did
    # not claim (`tools.pairlab.marks`). Default OFF and deliberately without a
    # CLI flag on the harvest itself: what the harvest STORES is the trace
    # bench's `chain` baseline, and a baseline that quietly changed would make
    # every measured delta unreadable. The bench turns it on for a candidate run
    # (`tools.tracebench.run --mark-refit`); adopting it into the stored trace
    # is a separate, measured decision.
    mark_refit: bool = False
    # K-A (§14 `aug19`), ADOPTED as Kette v2: emit the word's diacritic
    # strokes AFTER all body strokes, in the composed engine order the hand
    # shares — the v1 per-run assembly interleaved them between the runs, and
    # the trace bench paid the sequence inversion as the whole unter/muß
    # collapse class (measured: unter 0.4503 -> 0.0854, muß family -0.12 to
    # -0.14, every other word and every geometry column byte-identical). A
    # pure ORDER change of the assembled stroke list — no point moves. True
    # is the v2 baseline (a dated re-baseline of the bench); False reproduces
    # the v1 ordering for archaeology.
    marks_last: bool = True
    # K-B (§14 `aug19`), ADOPTED as Kette v3: repair the §11 outlier class (a
    # lone anchor excursion — the i-dot V, the p-head needle) on the
    # assembled TRACE strokes, with the very detector the statistics layer
    # has used since §11e (`tools.pairlab.anchors`, scale-free step ratios,
    # runs replaced by the chord of their unflagged neighbours, never snapped
    # to ink, count logged as `trace_repaired`). The A1 pattern: changes what
    # the trace SHOWS, never what the harvest MEASURES. Measured: Galoppieren
    # 0.233 -> 0.040 (the missing i-mark heals), retrace/touch counters fall
    # toward the hand, no word moves beyond +0.0016. True is the v3
    # baseline; False shows the raw needles for inspection archaeology.
    trace_repair: bool = True
    # K-C (§14 `aug20`, the author's "Flecken" find): drop paper-grey non-main
    # ink components (specks, show-through) from the evidence the CHAIN is
    # pulled by — `tools.pairlab.ink_evidence`, applied once at the top of
    # `chain_word_strokes`, after `derive_word` took ruler and registration on
    # the full ink. Unlike A1/K-A/K-B this changes what the harvest MEASURES
    # (the solve sees different ink), so it was declared-off and measured on
    # the follower first; all six aug20 gates passed and the author's go made
    # True the Kette v4 baseline (§14 `aug21` re-baseline) — the same evidence
    # on follower, harvest and the tracebench chain provider. False is the
    # pre-v4 archaeology path: the case object passes through untouched,
    # byte-identical. A production re-harvest of the stored `traced` rows
    # stays behind owner-go + dbsnapshot, as for every trace-shaping default.
    ink_evidence: bool = True
    # K-E stage 1 (§14 `aug21`, K-E2 form): the mark-claim separation — a
    # composed mark stroke claims its dark ink component, the claim splits
    # distance field and coverage pot per stroke class inside
    # `fit_word_chain` (the width fields stay whole). Declared-off on the
    # harvest (the K-C pattern: measured on the follower first; adoption
    # into what the harvest measures is its own decision).
    mark_claim: bool = False
    # LF14 (§14 `sep06`): let the post-gate stranded-anchor repair skip the
    # anchors that sit inside a loop the CHART row draws — the apex of a counter
    # answers the detector's step-ratio description too, and chording it to its
    # neighbours (which lie on the two strands) closes the counter. Default is
    # the module switch `tools.pairlab.anchors.LOOP_AWARE_REPAIR`, which is off:
    # this changes what the harvest MEASURES, so it follows the K-C pattern —
    # declared off, measured, adopted only by a passed gate. Only the OCCURRENCE
    # repair reads it; the trace repair (K-B) works on assembled word strokes,
    # which carry no anchor ranges.
    loop_aware_repair: bool = LOOP_AWARE_REPAIR


@dataclass
class CaseHarvest:
    """`harvest_case`'s four artefacts for ONE specimen word.

    `fits_by_key` are the CENTERED fitted anchor arrays the medians are taken
    over, `occurrences` the `InstanceItem` rows, `word_record` the single
    `WordInstanceItem` row (None when no letter survived) and `diag_rows` one
    row per slot for `--diag-csv`.
    """

    fits_by_key: dict[str, list[np.ndarray]] = field(default_factory=dict)
    occurrences: list[dict] = field(default_factory=list)
    word_record: dict | None = None
    diag_rows: list[dict] = field(default_factory=list)


# ------------------------------------------------------------- pure geometry


# `anchor_spike_ratio` — the „Anker im leeren Papier" detector — lives in
# `core/laufform.py` since LF8 (messjournal.md §14 `aug29`) and is imported
# above: the same function scores every single fit here (against
# MAX_ANCHOR_SPIKE_RATIO) and the ROW about to be written at the API's row gate
# (against LAUFFORM_SPIKE_RATIO_MAX). Its per-stroke design and the measured
# reason for it (ue in „Zügel": 7.21 pooled, 10.61 per stroke — a needle the
# pooled form silently kept) are documented on the function itself.


@functools.lru_cache(maxsize=None)
def _loop_ranges_cached(
    anchors: tuple[float, ...],
    half_widths: tuple[float, ...],
    stroke_starts: tuple[int, ...] | None,
    corner_anchors: tuple[int, ...] | None,
) -> tuple[tuple[int, int], ...]:
    """`core.aggregate.loop_ranges` on hashable arguments — the memo's own body.

    The geometry costs a rendered centerline plus an O(n²) crossing walk per
    glyph, and a word set hands the same chart row in dozens of times. Keyed on
    the ROW, not on the glyph key, so a second fixture root in the same process
    cannot inherit the first one's ranges.
    """
    return tuple(
        loop_ranges(
            np.asarray(anchors, dtype=float).reshape(-1, 2),
            np.asarray(half_widths, dtype=float),
            stroke_starts,
            corner_anchors,
        )
    )


def chart_loop_ranges(row: dict, enabled: bool = True) -> tuple[tuple[int, int], ...]:
    """The anchor ranges over which THIS chart row's ductus closes a loop.

    Read off the chart, never off the occurrence: the same occurrence-independent
    ranges the running-form estimator aligns on (`core.aggregate.loop_ranges`,
    LF13). They are what `LOOP_AWARE_REPAIR` needs to tell a counter's apex from
    an anchor stranded in empty paper — and reading them per occurrence would
    make the repair depend on the excursion it is judging.

    `enabled` is the switch itself rather than a check at the call site: with the
    repair loop-blind nothing reads the result, so the geometry is skipped
    entirely and the harvest costs exactly what it cost before the switch existed.
    """
    if not enabled:
        return ()
    meta = row.get("trace_meta") or {}
    starts, corners = meta.get("stroke_starts"), meta.get("corner_anchors")
    return _loop_ranges_cached(
        tuple(np.asarray(row["anchors"], dtype=float).ravel().tolist()),
        tuple(np.asarray(row["half_widths"], dtype=float).ravel().tolist()),
        None if starts is None else tuple(int(s) for s in starts),
        None if corners is None else tuple(int(c) for c in corners),
    )


def _strokes_to_word_units(
    fitted: np.ndarray, stroke_starts: list[int], fit_frame: dict, registration: dict
) -> list[list[list[float]]]:
    """The fitted letter path in the WORD's registration frame (template units,
    baseline = 0, x from the word origin), one polyline per pen-down stroke.

    The fit returns anchors in its own letter frame (x_origin_px = px of
    template x 0, baseline_y_px = px of the baseline incl. the letter nudge);
    going through page px and back into the shared word frame keeps every
    letter on the word's common axes."""
    xh = fit_frame["xh"]
    px_x = fit_frame["x_origin_px"] + fitted[:, 0] * xh
    px_y = fit_frame["baseline_y_px"] - fitted[:, 1] * xh
    pts = _px_to_word_units(px_x, px_y, xh, registration)
    bounds = [*list(stroke_starts), len(pts)]
    return [pts[a:b].tolist() for a, b in zip(bounds, bounds[1:], strict=False) if b - a >= 2]


def letter_gate(
    *,
    converged_local: bool,
    geo_rmse_px: float,
    rmse_max: float,
    at_bound: bool,
    anchors_ok: bool,
    # REQUIRED, deliberately not defaulted: a gate input with a passing default
    # is the exact failure this check was born from — a caller that forgets the
    # keyword would silently disable it with the whole suite still green.
    spike_ratio: float,
    connector_reasons: Sequence[str | None] = (),
) -> str:
    """The chain path's per-letter gate cascade — `"ok"` or the first reason.

    Fixed order, so a row's reason code is stable and the per-reason histogram
    counts each letter once:

    1. `not_converged_local` — `core.fit`'s own convergence gate on the
       LETTER-LOCAL coverage window, the like-for-like statement against the
       independent M4 fit (`chain.ChainSegment.converged_local`).
    2. `geo_rmse` — the same `--rmse-max` the slot path applies. Both of the
       first two are reported as their own code, so „which of the two bit" is
       readable off the CSV rather than inferred.
    3. `at_bound` — the letter's translation block rests on its
       `analyze.FIT_DX_UNITS`/`FIT_DY_UNITS` bound: the placement is suspect.
    4. `anchor_count` — the fitted array no longer matches the chart row (a
       template changed under the run); nothing downstream could median it.
    5. `anchor_spike` — „Anker im leeren Papier": a single anchor left the
       stroke and came back (`anchor_spike_ratio` over
       `MAX_ANCHOR_SPIKE_RATIO`). AFTER `anchor_count`, because the ratio of a
       mis-shaped array says nothing; before the connector reason, because this
       is the letter's OWN chain rather than a neighbour's damage. Not a repair
       — a chain with a discontinuity in it never measured the hand, and the
       fit's own QC cannot see it (every term in that objective is a mean).
    6. `connector_degenerate` — a connector ADJACENT to this letter derailed
       (`tools.pairlab.connector_qc`). The letter is rejected with it: the
       seam is a shared parameter, so a runaway connector has already paid for
       itself out of the letter's own tail.
    """
    if not converged_local:
        return "not_converged_local"
    if geo_rmse_px > rmse_max:
        return "geo_rmse"
    if at_bound:
        return "at_bound"
    if not anchors_ok:
        return "anchor_count"
    if spike_ratio > MAX_ANCHOR_SPIKE_RATIO:
        return "anchor_spike"
    if any(connector_reasons):
        return "connector_degenerate"
    return "ok"


# ------------------------------------------------------------- one case, two paths


def _keyed_indices(case) -> dict[int, int]:
    """slot index → index into the word record's `slots` list (keyless slots
    are filtered out there, so the two spaces differ)."""
    out: dict[int, int] = {}
    keyed = -1
    for i, slot in enumerate(case.slots):
        if slot.key:
            keyed += 1
            out[i] = keyed
    return out


def _diag_row(case, opts: HarvestOptions, slot_index: int, keyed: int | None, key: str | None, **extra) -> dict:
    row = {
        "specimen_id": case.id,
        "kind": case.kind,
        "word": case.word,
        "path": opts.path,
        "slot": slot_index,
        "keyed_slot": keyed,
        "glyph_key": key,
    }
    row.update(extra)
    return row


def _word_record(case, strokes: list[list[list[float]]], registration: dict, xh: float, measurements: dict) -> dict:
    return {
        "kind": case.kind,
        "specimen_id": case.id,
        "word": case.word,
        "slots": [s.key for s in case.slots if s.key],
        "strokes": strokes,
        "provenance": "traced",
        "measurements": {
            "registration_px": {
                "tx": round(float(registration["tx"]), 2),
                "ty": round(float(registration["ty"]), 2),
                "baseline_row": int(registration["baseline_row"]),
            },
            "xh_px": round(float(xh), 2),
            **measurements,
        },
    }


def _harvest_case_slots(case, result: WordDeriveResult, opts: HarvestOptions) -> CaseHarvest:
    """The per-letter M4 path — this tool's original loop, unchanged.

    Every letter is fitted on its own against a letter-local skeleton window;
    the word record therefore holds the letters and nothing between them.
    """
    per_key: dict[str, list[np.ndarray]] = defaultdict(list)
    occurrences: list[dict] = []
    diag_rows: list[dict] = []
    xh = result.xh_px
    tx, ty = result.registration["tx"], result.registration["ty"]
    baseline_row = result.baseline_row
    edt = distance_transform_edt(~case.skel)
    word_strokes: list[list[list[float]]] = []
    fitted_slots: list[int] = []
    unfitted_slots: list[int] = []
    rmse_by_slot: dict[str, float] = {}
    # The word record's slot indices index into its stored `slots` list,
    # which filters keyless slots out — track that KEYED index alongside
    # the full one (`i` stays the composer/pair-instance slot space).
    keyed_i = -1
    for i, slot in enumerate(case.slots):
        if slot.key:
            keyed_i += 1
        items = _body_items(result, i)
        row = case.templates.get(slot.key) if slot.key else None
        if not items or row is None or case.width_map is None:
            if slot.key:
                unfitted_slots.append(keyed_i)
                diag_rows.append(_diag_row(case, opts, i, keyed_i, slot.key, accepted=False, gate="no_template"))
            continue
        strokes_px = [_to_px(it["centerline"], xh, tx, ty, baseline_row) for it in items]
        ddx, ddy, at_bound, _before, _after = _fit_letter(edt, strokes_px, xh)
        grid = {
            "grid_at_bound": at_bound,
            "grid_resid_before": round(float(_before), 4),
            "grid_resid_after": round(float(_after), 4),
        }
        if at_bound:
            unfitted_slots.append(keyed_i)
            diag_rows.append(_diag_row(case, opts, i, keyed_i, slot.key, accepted=False, gate="grid_at_bound", **grid))
            continue
        anchors = np.asarray(row["anchors"], dtype=float)
        meta = row.get("trace_meta") or {}
        body = np.vstack(strokes_px) + np.array([ddx, ddy])
        cols = np.arange(case.skel.shape[1])
        keep = (cols >= body[:, 0].min() - TRACE_WINDOW_MARGIN * xh) & (
            cols <= body[:, 0].max() + TRACE_WINDOW_MARGIN * xh
        )
        skel_local = case.skel & keep[None, :]
        if not skel_local.any():
            unfitted_slots.append(keyed_i)
            diag_rows.append(_diag_row(case, opts, i, keyed_i, slot.key, accepted=False, gate="empty_window", **grid))
            continue
        payload = result.payloads.get(slot.key) or {}
        first_template = (payload.get("centerlines_template") or [[[0.0, 0.0]]])[0][0]
        dxc = items[0]["centerline"][0][0] - first_template[0]
        stroke_starts = meta.get("stroke_starts") or [0]
        baseline_y_px = baseline_row + ty + ddy
        x_origin_px = dxc * xh + tx + ddx - anchors[0, 0] * xh
        try:
            fr = fit_template_to_instance(
                anchors,
                np.asarray(row["half_widths"], dtype=float),
                skel_local,
                np.where(keep[None, :], case.width_map, 0.0),
                unit_px=xh,
                baseline_y_px=baseline_y_px,
                x_origin_px=x_origin_px,
                stroke_starts=stroke_starts,
                corner_anchors=meta.get("corner_anchors") or [],
            )
        except Exception as exc:  # noqa: BLE001 — survey tool: skip, but say so
            print(f"  fit failed: {case.id} slot {i} ({slot.key}): {exc}", flush=True)
            unfitted_slots.append(keyed_i)
            diag_rows.append(_diag_row(case, opts, i, keyed_i, slot.key, accepted=False, gate="fit_error", **grid))
            continue
        converged = bool(fr.fit_meta.get("converged"))
        geo_rmse = float(fr.fit_meta.get("geo_rmse_px", 99))
        if not converged or geo_rmse > opts.rmse_max:
            unfitted_slots.append(keyed_i)
            diag_rows.append(
                _diag_row(
                    case,
                    opts,
                    i,
                    keyed_i,
                    slot.key,
                    accepted=False,
                    gate="not_converged" if not converged else "geo_rmse",
                    converged=converged,
                    geo_rmse_px=round(geo_rmse, 3),
                    **grid,
                )
            )
            continue
        fitted_raw = np.asarray(fr.anchors, dtype=float)
        if fitted_raw.shape != anchors.shape:
            unfitted_slots.append(keyed_i)
            diag_rows.append(
                _diag_row(case, opts, i, keyed_i, slot.key, accepted=False, gate="anchor_count", converged=True, **grid)
            )
            continue
        # „Anker im leeren Papier": one anchor left the stroke and came back.
        # The fit's own QC cannot see it (every term in the objective is a
        # mean), and the occurrence median would carry the needle straight into
        # the Laufform — so the OCCURRENCE is rejected here. Not a repair of the
        # fit: a chain with a discontinuity in it never measured the hand.
        spike_ratio = anchor_spike_ratio(fitted_raw, stroke_starts)
        if spike_ratio > MAX_ANCHOR_SPIKE_RATIO:
            unfitted_slots.append(keyed_i)
            diag_rows.append(
                _diag_row(
                    case,
                    opts,
                    i,
                    keyed_i,
                    slot.key,
                    accepted=False,
                    gate="anchor_spike",
                    converged=True,
                    geo_rmse_px=round(geo_rmse, 3),
                    anchor_spike_ratio=round(spike_ratio, 2),
                    **grid,
                )
            )
            continue
        # Post-gate repair (`tools.pairlab.anchors`): the gate above judged the
        # UNREPAIRED geometry, and the stored `anchor_spike_ratio` stays that
        # number — a repair is a near-rejection, never a pass. Only what an
        # ACCEPTED occurrence contributes onward (the centering, the stored
        # anchors, the medians) uses the interpolated array; with nothing
        # flagged it IS `fitted_raw` (identity return).
        repaired, repaired_indices = repair_stranded_anchors(
            fitted_raw, stroke_starts, chart_loop_ranges(row, opts.loop_aware_repair), loop_aware=opts.loop_aware_repair
        )
        shift = np.median(repaired - anchors, axis=0)
        fitted = repaired - shift  # shapes, not placements
        per_key[slot.key].append(fitted)
        # The word trace (handmodell word level): this letter's UNCENTERED
        # fitted strokes in the word's shared frame, in writing order — built
        # from the UNREPAIRED fit on purpose: the trace is the inspection layer
        # showing what the fit actually did, needle and all.
        fitted_slots.append(keyed_i)
        rmse_by_slot[str(keyed_i)] = round(geo_rmse, 3)
        word_strokes.extend(
            _strokes_to_word_units(
                fitted_raw,
                stroke_starts,
                {"xh": xh, "x_origin_px": x_origin_px, "baseline_y_px": baseline_y_px},
                {"tx": tx, "ty": ty, "baseline_row": baseline_row},
            )
        )
        # The occurrence row (handmodell H1): centered shape as anchors,
        # placement + fit context in measurements, crop in page pixels.
        rx, ry = (case.rect[0], case.rect[1]) if case.rect else (0, 0)
        prev_slot = case.slots[i - 1] if i > 0 else None
        next_slot = case.slots[i + 1] if i + 1 < len(case.slots) else None
        occurrences.append(
            {
                "glyph_key": slot.key,
                "glyph": row.get("glyph") or slot.key,
                "position": slot.position or "medial",
                "variant": 0,
                "y0": int(round(body[:, 1].min())) + ry,
                "y1": int(round(body[:, 1].max())) + ry,
                "x0": int(round(body[:, 0].min())) + rx,
                "x1": int(round(body[:, 0].max())) + rx,
                "anchors": fitted.round(4).tolist(),
                "half_widths": [],
                "measurements": {
                    "specimen_id": case.id,
                    "slot": i,
                    "prev_key": prev_slot.key if prev_slot and not prev_slot.space else None,
                    "next_key": next_slot.key if next_slot and not next_slot.space else None,
                    "shift_xh": [round(float(shift[0]), 4), round(float(shift[1]), 4)],
                    "registration_px": [round(float(ddx), 2), round(float(ddy), 2)],
                    "geo_rmse_px": round(geo_rmse, 3),
                    "xh_px": round(float(xh), 2),
                    # Absent when untouched: absence must mean the stored
                    # anchors are exactly the fitted ones.
                    **({"repaired_anchors": repaired_indices} if repaired_indices else {}),
                },
            }
        )
        diag_rows.append(
            _diag_row(
                case,
                opts,
                i,
                keyed_i,
                slot.key,
                accepted=True,
                gate="ok",
                converged=True,
                geo_rmse_px=round(geo_rmse, 3),
                anchor_spike_ratio=round(spike_ratio, 2),
                n_repaired=len(repaired_indices),
                **grid,
            )
        )

    word_record = None
    if word_strokes:
        word_record = _word_record(
            case,
            cap_word_strokes(word_strokes, label=f"{case.id} (slot)"),
            {"tx": tx, "ty": ty, "baseline_row": baseline_row},
            xh,
            {"fitted_slots": fitted_slots, "unfitted_slots": unfitted_slots, "geo_rmse_px_by_slot": rmse_by_slot},
        )
    print(f"fitted {case.id}", flush=True)
    return CaseHarvest(dict(per_key), occurrences, word_record, diag_rows)


def _grid_fits(case, result: WordDeriveResult) -> dict[int, dict]:
    """Per-slot bounded grid search — the chain path's window supplier.

    The chain needs a crop-column window per letter for its coverage GATE (and
    their union is the band the fit itself sees), and the grid search is the
    same placement diagnosis the slot path starts from — so it stays, and its
    `at_bound` verdict is carried into the diagnostics rather than acted on
    (the chain has its own bounded translation block, which is what
    `letter_gate` judges).
    """
    xh = result.xh_px
    tx, ty = result.registration["tx"], result.registration["ty"]
    baseline_row = result.baseline_row
    edt = distance_transform_edt(~case.skel)
    out: dict[int, dict] = {}
    for i, slot in enumerate(case.slots):
        items = _body_items(result, i)
        row = case.templates.get(slot.key) if slot.key else None
        if not items or row is None or case.width_map is None:
            continue
        strokes_px = [_to_px(it["centerline"], xh, tx, ty, baseline_row) for it in items]
        ddx, ddy, at_bound, before, after = _fit_letter(edt, strokes_px, xh)
        body = np.vstack(strokes_px) + np.array([ddx, ddy])
        out[i] = {
            "window": (
                float(body[:, 0].min()) - TRACE_WINDOW_MARGIN * xh,
                float(body[:, 0].max()) + TRACE_WINDOW_MARGIN * xh,
            ),
            "at_bound": bool(at_bound),
            "resid_before": round(float(before), 4),
            "resid_after": round(float(after), 4),
            # The grid's placement delta in xh units — the chain's optional
            # block seed (HarvestOptions.chain_seed == "grid").
            "shift_units": (float(ddx) / xh, float(ddy) / xh),
        }
    return out


def _chainable_runs(case, grids: dict[int, dict]) -> list[list[int]]:
    """`chain_runs` narrowed to slots that HAVE a grid window, kept consecutive.

    A keyed slot whose template is unauthored (or whose composition produced no
    body strokes) cannot be a chain segment at all, and `fit_word_chain` would
    return None for the whole run because of it. Cutting the run there keeps the
    rest of the word measurable.
    """
    out: list[list[int]] = []
    for run in chain_runs(case):
        current: list[int] = []
        for slot_index in run:
            if slot_index in grids:
                current.append(slot_index)
                continue
            if current:
                out.append(current)
            current = []
        if current:
            out.append(current)
    return out


def _connector_diag(fit, xh: float, registration: dict) -> tuple[dict[int, str | None], dict[int, dict]]:
    """Per-join degeneracy verdict + the signals behind it.

    The verdict is `connector_qc.connector_degenerate` on the chain's own
    connector polyline against the two letters' facing ink edges, all in the
    composed frame the connector is reported in; `connector_signals` is called
    beside it purely so the CSV can carry the numbers a flagged row is argued
    with.
    """
    baseline_y_px = registration["baseline_row"] + registration["ty"]
    body_px: dict[int, list[np.ndarray]] = defaultdict(list)
    for entry in fit.stroke_polylines_px:
        if entry["kind"] != "letter" or _is_diacritic(entry, xh, registration):
            continue
        pts = np.asarray(entry["points_px"], dtype=float).reshape(-1, 2)
        if len(pts):
            body_px[int(entry["slot_index"])].append(pts)

    reasons: dict[int, str | None] = {}
    signals: dict[int, dict] = {}
    for j, conn in enumerate(fit.connector_units):
        left, right = fit.slots[j], fit.slots[j + 1]
        if left not in body_px or right not in body_px:
            reasons[j] = None
            continue
        _, a_max_px = _ink_extent_x(body_px[left], baseline_y_px, xh)
        b_min_px, _ = _ink_extent_x(body_px[right], baseline_y_px, xh)
        a_max = (a_max_px - registration["tx"]) / xh
        b_min = (b_min_px - registration["tx"]) / xh
        reasons[j] = connector_degenerate(conn, a_max, b_min)
        sig = connector_signals(conn, a_max, b_min)
        if sig is not None:
            signals[j] = {
                "conn_arc_units": round(sig.arc_units, 4),
                "conn_chord_units": round(sig.chord_units, 4),
                "conn_seam_left_units": round(sig.seam_left_units, 4),
                "conn_seam_right_units": round(sig.seam_right_units, 4),
                "conn_forward_ratio": round(sig.forward_ratio, 4),
                "conn_gap_units": round(sig.gap_units, 4),
            }
    return reasons, signals


@dataclass(frozen=True)
class ChainRunFit:
    """One run of joined slots as the chain solved it — `fit is None` when it did not."""

    slots: list[int]
    fit: Any | None


def chain_word_strokes(case, result: WordDeriveResult, opts: HarvestOptions) -> tuple[list[list[list[float]]], dict]:
    """The chain path's TRACE half: solve every run of joined slots, weld the pen path.

    Lifted out of `_harvest_case_chain` (which now calls it) so that a consumer
    wanting the PEN PATH and nothing else runs the harvest's own code — the
    trace bench's `chain` candidate (`tools/tracebench`,
    `docs/proposals/tintenfolger.md` §2.4). A baseline the bench measures has to
    be the thing the harvest stores, byte for byte; rebuilt beside it, the two
    would drift and the bench would grade a candidate nobody ships.

    Returns `(strokes, meta)`. `strokes` are capped and in the word's
    registration frame — literally what `word_instances.strokes` holds. `meta`
    carries everything the GRADING half needs so nothing is solved twice:

    * `runs` — one `ChainRunFit` per run, in solve order (the fit is `None`
      where `fit_word_chain` gave up, which the caller reports as `chain_failed`);
    * `grids` — the per-slot grid fits the windows and the fallback diagnosis
      come from (an EDT per case, computed once);
    * `registration` / `xh` — the frame the strokes are expressed in;
    * `traced_slots`, `run_slots`, `cut_indices`, `n_params`, `seconds` — the
      pooled solve diagnostics the word record stores;
    * `mark_refit` — the A1 roll-up plus one row per mark, `None` while the
      measure is off (which is the default, and then this function's output is
      byte-identical to what it produced before A1 existed).

    The solves and the assembly are two loops rather than one because the
    optional mark refit sits between them and has to see the WHOLE word: its
    body claim must cover every run, or a mark of one run could be pulled onto
    ink another run's letter already accounts for. With the measure off the
    entries handed to the assembler are literally `fit.stroke_polylines_px`, in
    the same order, so nothing about the baseline changes.
    """
    xh = result.xh_px
    registration = {
        "tx": result.registration["tx"],
        "ty": result.registration["ty"],
        "baseline_row": result.baseline_row,
    }
    # K-C: one evidence for seed windows, solve and mark refit — off → identity.
    case, ink_report = ink_evidence_case(case, InkEvidenceOptions() if opts.ink_evidence else None)
    grids = _grid_fits(case, result)
    restart_slots = {i for i, s in enumerate(case.slots) if s.key and _key_base(s.key, s.position) in CAP_RESTART_BASES}

    runs: list[ChainRunFit] = []
    solved: list[Any] = []  # the fits whose pen path goes into the trace, in solve order
    word_strokes: list[list[list[float]]] = []
    traced: set[int] = set()
    run_slots: list[list[int]] = []
    cut_indices: list[list[list[int]]] = []
    n_params = 0
    seconds = 0.0

    for run in _chainable_runs(case, grids):
        windows = {s: grids[s]["window"] for s in run}
        seeds = (
            {s: grids[s]["shift_units"] for s in run if not grids[s]["at_bound"]} if opts.chain_seed == "grid" else None
        )
        fit = fit_word_chain(
            case, run, result=result, windows_px=windows, slot_shift_init=seeds, mark_claim=opts.mark_claim
        )
        runs.append(ChainRunFit(list(run), fit))
        if fit is None:
            continue
        run_slots.append(list(fit.slots))
        traced.update(int(s) for s in fit.slots)
        cut_indices.append([[int(a), int(b)] for a, b in fit.cut_indices])
        n_params += int(fit.fit_meta.get("n_params", 0))
        seconds += float(fit.fit_meta.get("seconds", 0.0))
        solved.append(fit)

    entries_by_run = [fit.stroke_polylines_px for fit in solved]
    mark_meta: dict | None = None
    if opts.mark_refit:
        # A1 (tintenfolger.md §7.3): the marks alone, moved onto the ink the
        # body left over. It changes only diacritic polylines and only by a
        # translation, so no body anchor and no seam can move here — and it
        # COPIES rather than mutates, so `fit.stroke_polylines_px` stays the
        # solve's own output and the gates, the connector QC and the occurrence
        # rows below keep judging the unrefitted geometry. The refit changes
        # what the trace SHOWS, never what the harvest MEASURES (the same
        # separation `tools.pairlab.anchors`' repair keeps).
        entries_by_run, mark_reports = refit_word_marks(
            entries_by_run, xh=xh, registration=registration, skeleton=case.skel, options=None
        )
        mark_meta = {**mark_refit_summary(mark_reports), "rows": [asdict(r) for r in mark_reports]}

    for fit, entries in zip(solved, entries_by_run, strict=True):
        # The whole solved run goes into the trace — a gate verdict decides what
        # is measured, not what was written (the per-slot verdicts stay readable
        # in `gates`/`converged_local` beside it). Since the K-B adoption
        # (Kette v3) the trace is a PRODUCT surface of the Tintenfolger
        # campaign and gets the §11 outlier repair below (`trace_repair`);
        # the raw needle-and-all inspection view stays reachable with
        # `trace_repair=False`.
        word_strokes.extend(
            assemble_word_strokes(
                entries, traced_slots=set(fit.slots), xh=xh, registration=registration, restart_slots=restart_slots
            )
        )

    if opts.marks_last:
        # K-A: stable partition — diacritics (the assembler's OWN criterion,
        # read off the word-units strokes) move behind every body stroke,
        # order inside both groups untouched, no point moves.
        body = [s for s in word_strokes if not diacritic_stroke_units(s)]
        marks = [s for s in word_strokes if diacritic_stroke_units(s)]
        word_strokes = body + marks

    trace_repaired = 0
    if opts.trace_repair:
        # K-B: the §11 outlier repair on the TRACE strokes — the shared
        # detector, per stroke, scale-free; logged, never a snap to ink.
        repaired_strokes: list[list[list[float]]] = []
        for stroke in word_strokes:
            pts = np.asarray(stroke, dtype=float).reshape(-1, 2)
            repaired, indices = repair_stranded_anchors(pts, None)
            trace_repaired += len(indices)
            repaired_strokes.append(repaired.tolist() if indices else stroke)
        word_strokes = repaired_strokes

    meta = {
        "runs": runs,
        "grids": grids,
        "registration": registration,
        "xh": xh,
        "traced_slots": sorted(traced),
        "run_slots": run_slots,
        "cut_indices": cut_indices,
        "n_params": n_params,
        "seconds": round(seconds, 3),
        "mark_refit": mark_meta,
        **({"trace_repaired": trace_repaired} if opts.trace_repair else {}),
        **({"ink_evidence": ink_report.as_dict()} if ink_report is not None else {}),
    }
    return cap_word_strokes(word_strokes, label=f"{case.id} (chain)"), meta


def _harvest_case_chain(case, result: WordDeriveResult, opts: HarvestOptions) -> CaseHarvest:
    """The word-chain path (Stage B): one solve per run of joined slots.

    Everything the slot path produces comes out here too — the same centered
    occurrence anchors, the same medians, one word record — with two
    differences: a letter is graded by `letter_gate` (which includes the
    ADJACENT connectors' degeneracy verdict, because the seam is a shared
    parameter), and the word record's strokes carry the connectors, so the
    stored trace is the pen path instead of a set of disconnected letters.

    The gate and the trace answer different questions, so they read different
    sets. `accepted` (gate `"ok"`) is the STATISTICS layer: the medians and the
    `instances` rows, where one wobbly letter would pollute a Laufform. The
    trace is the INSPECTION layer and shows every slot the chain solved, gate
    or no gate — `measurements` keeps both readable side by side
    (`traced_slots` vs. `fitted_slots`/`unfitted_slots`, plus `gates`,
    `converged_local` and `geo_rmse_px_by_slot` per slot).
    """
    per_key: dict[str, list[np.ndarray]] = defaultdict(list)
    occurrences: list[dict] = []
    diag_rows: list[dict] = []
    # The solves and the pen path come from the shared trace half — the same
    # code the trace bench's `chain` candidate runs, so a measured baseline and
    # a stored trace can never be two different things.
    word_strokes, chain_meta = chain_word_strokes(case, result, opts)
    xh = chain_meta["xh"]
    registration = chain_meta["registration"]
    grids = chain_meta["grids"]
    keyed = _keyed_indices(case)

    accepted: set[int] = set()  # gate "ok" — the occurrences and the medians
    traced: set[int] = set(chain_meta["traced_slots"])  # every slot the chain solved — the word trace
    gate_by_slot: dict[int, str] = {}
    converged_by_slot: dict[int, bool] = {}
    rmse_by_slot: dict[str, float] = {}
    run_slots: list[list[int]] = chain_meta["run_slots"]
    cut_indices: list[list[list[int]]] = chain_meta["cut_indices"]
    n_params = chain_meta["n_params"]
    seconds = chain_meta["seconds"]

    for i, unfittable in enumerate(case.slots):
        if unfittable.key and i not in grids:
            gate_by_slot[i] = "no_template"
            diag_rows.append(_diag_row(case, opts, i, keyed.get(i), unfittable.key, accepted=False, gate="no_template"))

    for chain_run in chain_meta["runs"]:
        run, fit = chain_run.slots, chain_run.fit
        run_label = "-".join(str(s) for s in run)
        if fit is None:
            for slot_index in run:
                gate_by_slot[slot_index] = "chain_failed"
                diag_rows.append(
                    _diag_row(
                        case,
                        opts,
                        slot_index,
                        keyed.get(slot_index),
                        case.slots[slot_index].key,
                        run=run_label,
                        accepted=False,
                        gate="chain_failed",
                        grid_at_bound=grids[slot_index]["at_bound"],
                        grid_resid_before=grids[slot_index]["resid_before"],
                        grid_resid_after=grids[slot_index]["resid_after"],
                    )
                )
            continue

        conn_reasons, conn_signals = _connector_diag(fit, xh, registration)
        letters = [seg for seg in fit.segments if seg.kind == "letter"]

        for n, seg in enumerate(letters):
            slot_index = fit.slots[n]
            slot = case.slots[slot_index]
            row = case.templates[slot.key]
            anchors = np.asarray(row["anchors"], dtype=float)
            fitted_raw = (
                np.asarray(seg.fitted_anchors, dtype=float) if seg.fitted_anchors is not None else np.zeros((0, 2))
            )
            adjacent = [conn_reasons.get(n - 1) if n else None, conn_reasons.get(n)]
            stroke_starts = (row.get("trace_meta") or {}).get("stroke_starts") or [0]
            # Measured on the UNREPAIRED `fitted_raw` — the gate's verdict and
            # the stored ratio always describe what the fit actually produced
            # (the centering below is a single translation, which leaves every
            # inter-anchor step — and therefore the ratio — unchanged).
            spike_ratio = anchor_spike_ratio(fitted_raw, stroke_starts)
            gate = letter_gate(
                converged_local=bool(seg.converged_local),
                geo_rmse_px=float(seg.geo_rmse_px),
                rmse_max=opts.rmse_max,
                at_bound=bool(fit.slot_at_bound.get(slot_index, False)),
                anchors_ok=fitted_raw.shape == anchors.shape,
                spike_ratio=spike_ratio,
                connector_reasons=adjacent,
            )
            gate_by_slot[slot_index] = gate
            converged_by_slot[slot_index] = bool(seg.converged_local)
            # Post-gate repair (`tools.pairlab.anchors`), ACCEPTED letters only:
            # a repair is a near-rejection, never a pass — the gate above judged
            # the unrepaired geometry, and a rejected letter is never repaired
            # into acceptance. The interpolated array is what flows onward into
            # the centering, the stored occurrence anchors and the medians.
            repaired, repaired_indices = (
                repair_stranded_anchors(
                    fitted_raw,
                    stroke_starts,
                    chart_loop_ranges(row, opts.loop_aware_repair),
                    loop_aware=opts.loop_aware_repair,
                )
                if gate == "ok"
                else (fitted_raw, [])
            )
            shift_block = fit.slot_shift_units.get(slot_index, (0.0, 0.0))
            total_shift = (fit.global_shift_units[0] + shift_block[0], fit.global_shift_units[1] + shift_block[1])
            diag = _diag_row(
                case,
                opts,
                slot_index,
                keyed.get(slot_index),
                slot.key,
                run=run_label,
                accepted=gate == "ok",
                gate=gate,
                grid_at_bound=grids[slot_index]["at_bound"],
                grid_resid_before=grids[slot_index]["resid_before"],
                grid_resid_after=grids[slot_index]["resid_after"],
                converged=bool(seg.converged),
                converged_local=bool(seg.converged_local),
                geo_rmse_px=round(float(seg.geo_rmse_px), 3),
                cov_rmse_px=round(float(seg.cov_rmse_px), 3),
                cov_rmse_local_px=round(float(seg.cov_rmse_local_px), 3),
                n_cov=int(seg.n_cov),
                n_cov_local=int(seg.n_cov_local),
                chain_at_bound=bool(fit.slot_at_bound.get(slot_index, False)),
                anchor_count_ok=fitted_raw.shape == anchors.shape,
                anchor_spike_ratio=round(spike_ratio, 2),
                n_repaired=len(repaired_indices),
                shift_x_units=round(float(total_shift[0]), 4),
                shift_y_units=round(float(total_shift[1]), 4),
                **dict(
                    zip(
                        ("seed_x_units", "seed_y_units"),
                        fit.fit_meta.get("slot_shift_init", {}).get(str(slot_index), ("", "")),
                        strict=True,
                    )
                ),
                conn_reason_adjacent=",".join(r for r in adjacent if r),
                conn_reason=conn_reasons.get(n) or "",
                n_params=int(fit.fit_meta.get("n_params", 0)),
                iterations=int(fit.fit_meta.get("iterations", 0)),
                hit_iteration_cap=bool(fit.fit_meta.get("hit_iteration_cap", False)),
                max_iter=int(fit.fit_meta.get("max_iter", 0)),
                seconds=round(float(fit.fit_meta.get("seconds", 0.0)), 3),
                **conn_signals.get(n, {}),
            )
            diag_rows.append(diag)
            if gate != "ok":
                continue

            accepted.add(slot_index)
            shift = np.median(repaired - anchors, axis=0)
            fitted = repaired - shift  # shapes, not placements
            per_key[slot.key].append(fitted)
            rmse_by_slot[str(keyed[slot_index])] = round(float(seg.geo_rmse_px), 3)
            body = np.asarray(seg.polyline_px, dtype=float).reshape(-1, 2)
            rx, ry = (case.rect[0], case.rect[1]) if case.rect else (0, 0)
            prev_slot = case.slots[slot_index - 1] if slot_index > 0 else None
            next_slot = case.slots[slot_index + 1] if slot_index + 1 < len(case.slots) else None
            occurrences.append(
                {
                    "glyph_key": slot.key,
                    "glyph": row.get("glyph") or slot.key,
                    "position": slot.position or "medial",
                    "variant": 0,
                    "y0": int(round(body[:, 1].min())) + ry,
                    "y1": int(round(body[:, 1].max())) + ry,
                    "x0": int(round(body[:, 0].min())) + rx,
                    "x1": int(round(body[:, 0].max())) + rx,
                    "anchors": fitted.round(4).tolist(),
                    "half_widths": [],
                    "measurements": {
                        "specimen_id": case.id,
                        "slot": slot_index,
                        "prev_key": prev_slot.key if prev_slot and not prev_slot.space else None,
                        "next_key": next_slot.key if next_slot and not next_slot.space else None,
                        "shift_xh": [round(float(shift[0]), 4), round(float(shift[1]), 4)],
                        "registration_px": [
                            round(float(total_shift[0] * xh), 2),
                            round(float(-total_shift[1] * xh), 2),
                        ],
                        "geo_rmse_px": round(float(seg.geo_rmse_px), 3),
                        "cov_rmse_local_px": round(float(seg.cov_rmse_local_px), 3),
                        "xh_px": round(float(xh), 2),
                        "fit_path": "chain",
                        "run_slots": list(fit.slots),
                        # Absent when untouched: absence must mean the stored
                        # anchors are exactly the fitted ones.
                        **({"repaired_anchors": repaired_indices} if repaired_indices else {}),
                    },
                }
            )

    word_record = None
    if word_strokes:
        word_record = _word_record(
            case,
            word_strokes,
            registration,
            xh,
            {
                # `fitted_slots`/`unfitted_slots` keep their meaning: ACCEPTED as
                # occurrences (gate "ok"), the same statement the slot path
                # makes. `traced_slots` is the trace's own set — every slot whose
                # geometry is in `strokes`, gate or no gate — so "shown" and
                # "measured" are two readable fields instead of one overloaded
                # one. A slot in `traced_slots` but not in `fitted_slots` is a
                # letter the admin should see flagged, not a letter that is gone.
                "fitted_slots": sorted(keyed[s] for s in accepted),
                "unfitted_slots": sorted(k for s, k in keyed.items() if s not in accepted),
                "traced_slots": sorted(keyed[s] for s in traced if s in keyed),
                "geo_rmse_px_by_slot": rmse_by_slot,
                "fit_path": "chain",
                "run_slots": run_slots,
                "cut_indices": cut_indices,
                "converged_local": {str(keyed[s]): v for s, v in converged_by_slot.items()},
                "gates": {str(keyed[s]): g for s, g in gate_by_slot.items() if s in keyed},
                "n_params": n_params,
                "seconds": seconds,
            },
        )
    print(
        f"chained {case.id}: {len(accepted)}/{len(keyed)} letters accepted, "
        f"{len(traced)} traced, {len(word_strokes)} pen runs",
        flush=True,
    )
    return CaseHarvest(dict(per_key), occurrences, word_record, diag_rows)


def harvest_case(case, opts: HarvestOptions) -> CaseHarvest:
    """One specimen word → its fits, occurrences, word record and diagnostics.

    The ProcessPool unit of work: ONE `derive_word` per case whichever path
    runs, and nothing shared with its siblings.
    """
    if not case.scorable:
        return CaseHarvest({}, [], None, [])
    result = derive_word(case)
    if result.composed["missing"] or result.report is None or result.report.get("failed"):
        return CaseHarvest({}, [], None, [])
    if opts.path == "chain":
        return _harvest_case_chain(case, result, opts)
    return _harvest_case_slots(case, result, opts)


# ------------------------------------------------------------------ the run


def harvest(
    style: str,
    min_n: int,
    rmse_max: float,
    *,
    sets: Sequence[str] = ("words",),
    path: str = "slot",
    jobs: int = 1,
    max_cases: int = 0,
    chain_seed: str = "composed",
    loop_aware_repair: bool = LOOP_AWARE_REPAIR,
) -> tuple[dict[str, dict], list[dict], list[dict], list[dict]]:
    """Per-letter median fitted anchors over the clean word occurrences, plus
    every clean fit as an occurrence record (`InstanceItem` wire shape), plus
    one traced word record per specimen (`WordInstanceItem` wire shape), plus
    the per-slot diagnostics rows.

    `sets` iterates the frozen fixture roots in order (the pair drills carry
    everything a two-slot case needs, so they flow through the same code path);
    `jobs > 1` pools over CASES, which keeps every case's `derive_word` inside
    one worker. Iteration order — and therefore the medians — is independent of
    the job count: `ProcessPoolExecutor.map` yields in input order.
    """
    opts = HarvestOptions(
        style=style, rmse_max=rmse_max, path=path, chain_seed=chain_seed, loop_aware_repair=loop_aware_repair
    )
    cases = [c for which in sets for c in iter_fixture_word_cases(which=which, style=style)]
    if max_cases:
        cases = cases[:max_cases]

    per_key: dict[str, list[np.ndarray]] = defaultdict(list)
    tpl_by_key: dict[str, dict] = {}
    occurrences: list[dict] = []
    word_records: list[dict] = []
    diag_rows: list[dict] = []
    worker = functools.partial(harvest_case, opts=opts)
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            produced = list(pool.map(worker, cases))
    else:
        produced = [worker(case) for case in cases]
    for case, out in zip(cases, produced, strict=True):
        for key, fits in out.fits_by_key.items():
            per_key[key].extend(fits)
            if key in case.templates:
                tpl_by_key.setdefault(key, case.templates[key])
        occurrences.extend(out.occurrences)
        if out.word_record:
            word_records.append(out.word_record)
        diag_rows.extend(out.diag_rows)

    out_drafts: dict[str, dict] = {}
    for key, fits in sorted(per_key.items(), key=lambda kv: -len(kv[1])):
        if len(fits) < min_n:
            continue
        med = np.median(np.stack(fits), axis=0)
        tpl = np.asarray(tpl_by_key[key]["anchors"], dtype=float)
        out_drafts[key] = {"anchors": med.round(4).tolist(), "n_occurrences": len(fits)}
        print(f"{key:>6}  n={len(fits):>2}  median-vs-chart {float(np.hypot(*(med - tpl).T).mean()):.3f} xh")
    return out_drafts, occurrences, word_records, diag_rows


def write_diag_csv(rows: list[dict], path: Path) -> None:
    """One row per slot, fixed header — the gate cascade's audit trail."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(DIAG_FIELDS), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def print_gate_table(rows: list[dict]) -> None:
    """The yield table: how many letters each gate cost, per set."""
    per_set: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        per_set[str(row.get("kind", "?"))][str(row.get("gate", "?"))] += 1
    for kind, gates in sorted(per_set.items()):
        total = sum(gates.values())
        ok = gates.get("ok", 0)
        print(f"\n  {kind}: {ok}/{total} letters accepted ({ok / total:.0%})" if total else f"\n  {kind}: 0 letters")
        for gate, n in sorted(gates.items(), key=lambda kv: -kv[1]):
            print(f"    {gate:>22}  {n:>5}")
    conn = defaultdict(int)
    for row in rows:
        if row.get("conn_reason"):
            conn[str(row["conn_reason"])] += 1
    if conn:
        print(f"\n  connectors flagged: {sum(conn.values())}")
        for reason, n in sorted(conn.items(), key=lambda kv: -kv[1]):
            print(f"    {reason:>22}  {n:>5}")


def apply_drafts(
    drafts: dict[str, dict], base_url: str, source_id: str, token: str, min_occurrences: int | None = None
) -> None:
    """PUT every draft as the glyph's running-form row.

    The endpoint enforces the evidence floor (`LAUFFORM_MIN_OCCURRENCES`, §14
    LF7) and the row gate; `min_occurrences` lowers the floor EXPLICITLY for
    this run (`?min_occurrences=N`, the LF1 author statement) — never silently.
    A refused draft is reported per key, the run goes on.
    """
    failed: list[str] = []
    query = f"?min_occurrences={min_occurrences}" if min_occurrences is not None else ""
    for key, d in drafts.items():
        req = urllib.request.Request(
            f"{base_url}/sources/{source_id}/templates/{key}/laufform{query}",
            data=json.dumps(d).encode(),
            method="PUT",
            headers={"Content-Type": "application/json", "X-Admin-Token": token},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                print(f"PUT {key}: {res.status}")
        except Exception as exc:  # noqa: BLE001 — keep going, report at the end
            print(f"PUT {key}: FAILED — {exc}")
            failed.append(key)
    if failed:
        raise SystemExit(f"{len(failed)} letters failed: {', '.join(failed)} — re-run --apply to retry")


def apply_batch(
    endpoint: str, items: list[dict], base_url: str, source_id: str, token: str, hand_id: str, hand_label: str
) -> None:
    """One replace-batch: the harvest walks ALL specimen words, so the stored
    rows are exactly this run's clean fits. (`word-instances` spares authored
    rows on replace and reports them as skipped — manual traces survive.)"""
    body = {"hand": {"id": hand_id, "label": hand_label, "era": "1922"}, "replace": True, "items": items}
    req = urllib.request.Request(
        f"{base_url}/sources/{source_id}/{endpoint}",
        data=json.dumps(body).encode(),
        method="PUT",
        headers={"Content-Type": "application/json", "X-Admin-Token": token},
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        print(f"PUT {endpoint}: {res.status} {res.read().decode()[:200]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--style", default="suetterlin")
    ap.add_argument("--sets", default="words", help="comma-separated fixture sets (words,pairs)")
    ap.add_argument("--path", choices=["slot", "chain"], default="slot", help="per-letter M4 fits or word chains")
    ap.add_argument(
        "--chain-seed",
        choices=["composed", "grid"],
        default="composed",
        help="where the chain's translation blocks start: the composed layout, or each letter's own grid placement",
    )
    ap.add_argument("--jobs", type=int, default=1, help="parallel worker processes over CASES (default 1)")
    ap.add_argument("--max-cases", type=int, default=0, help="cap the cases per run (0 = all)")
    ap.add_argument("--min-n", type=int, default=4)
    ap.add_argument("--rmse-max", type=float, default=2.2)
    ap.add_argument(
        "--loop-aware-repair",
        action="store_true",
        help="LF14 arm: the post-gate repair leaves anchors inside a chart loop alone (default off)",
    )
    ap.add_argument("--out", type=Path, default=Path("laufform_drafts.json"))
    ap.add_argument("--occ-out", type=Path, default=Path("laufform_occurrences.json"))
    ap.add_argument("--word-out", type=Path, default=Path("laufform_words.json"))
    ap.add_argument("--diag-csv", type=Path, help="per-slot gate diagnostics (one row per slot)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--min-occurrences",
        type=int,
        default=None,
        help="lower the endpoint's evidence floor for THIS --apply (LF1 author statement; default: the server floor)",
    )
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--source-id")
    ap.add_argument("--hand-id", default="suetterlin-1922-norm")
    ap.add_argument("--hand-label", default="Suetterlin norm hand (Leitfaden 1922, Abb. 19/20)")
    args = ap.parse_args()
    if args.jobs < 1:
        raise SystemExit(f"--jobs must be >= 1, got {args.jobs}")
    if args.chain_seed != "composed" and args.path != "chain":
        raise SystemExit("--chain-seed grid only applies to --path chain")
    if args.max_cases < 0:
        raise SystemExit(f"--max-cases must be >= 0 (0 = all), got {args.max_cases}")

    sets = tuple(s.strip() for s in args.sets.split(",") if s.strip())
    if not sets:
        raise SystemExit("--sets needs at least one fixture set")
    if args.apply and (args.path != "slot" or sets != ("words",)):
        # The chain path and the extra sets are MEASUREMENT surfaces until the
        # Stage-B measurement round says otherwise; --apply keeps writing
        # exactly what it has always written.
        raise SystemExit("--apply is available for --path slot --sets words only (report-only otherwise)")

    drafts, occurrences, word_records, diag_rows = harvest(
        args.style,
        args.min_n,
        args.rmse_max,
        sets=sets,
        path=args.path,
        jobs=args.jobs,
        max_cases=args.max_cases,
        chain_seed=args.chain_seed,
        loop_aware_repair=args.loop_aware_repair or LOOP_AWARE_REPAIR,
    )
    for target in (args.out, args.occ_out, args.word_out):
        target.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(drafts))
    args.occ_out.write_text(json.dumps(occurrences))
    args.word_out.write_text(json.dumps(word_records))
    print(
        f"wrote {args.out} ({len(drafts)} letters) + {args.occ_out} ({len(occurrences)} occurrences)"
        f" + {args.word_out} ({len(word_records)} word traces)"
    )
    print_gate_table(diag_rows)
    if args.diag_csv:
        write_diag_csv(diag_rows, args.diag_csv)
        print(f"wrote {args.diag_csv} ({len(diag_rows)} slot rows)")
    if args.apply:
        token = os.environ.get("ADMIN_TOKEN")
        if not token or not args.source_id:
            raise SystemExit("--apply needs --source-id and the ADMIN_TOKEN env var")
        base = args.base_url.rstrip("/")
        apply_drafts(drafts, base, args.source_id, token, min_occurrences=args.min_occurrences)
        apply_batch("instances", occurrences, base, args.source_id, token, args.hand_id, args.hand_label)
        apply_batch("word-instances", word_records, base, args.source_id, token, args.hand_id, args.hand_label)


if __name__ == "__main__":
    main()
