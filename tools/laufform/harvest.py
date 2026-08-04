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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import numpy as np
from scipy.ndimage import distance_transform_edt

from core.fit import fit_template_to_instance
from tools.pairlab.analyze import TRACE_WINDOW_MARGIN, _body_items, _fit_letter, _ink_extent_x, _to_px
from tools.pairlab.chain import chain_runs, fit_word_chain
from tools.pairlab.connector_qc import connector_degenerate, connector_signals
from tools.wordlab.cases import iter_fixture_word_cases
from tools.wordlab.derive import WordDeriveResult, derive_word


# `api.schemas.WordInstanceItem`'s wire caps. A word trace that would exceed
# them is downsampled with a warning here rather than 422-ing at the endpoint.
MAX_WORD_STROKES = 128
MAX_STROKE_POINTS = 4096
# A stroke floating entirely above the midband is a diacritic and never carries
# a join — `tools.pairlab.chain._letter_cut_anchors`' rule, mirrored here
# because the assembly reads pen-down POLYLINES, not anchors.
DIACRITIC_MIN_Y = 1.0
# Two consecutive polylines meet AT the shared seam anchor, so the second one's
# first sample repeats the first one's last. Dropped when they are welded into
# one pen run (px tolerance — the two come out of the same parameter).
SEAM_DEDUP_PX = 1e-6

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
    "n_params",
    "seconds",
)


@dataclass(frozen=True)
class HarvestOptions:
    """Everything one case's harvest needs to know — the ProcessPool payload."""

    style: str = "suetterlin"
    rmse_max: float = 2.2
    path: str = "slot"  # "slot" (per-letter M4 fits) | "chain" (word-chain fits)


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


def _px_to_word_units(px_x: np.ndarray, px_y: np.ndarray, xh: float, registration: dict) -> np.ndarray:
    """Crop pixels → the WORD's registration frame (template units, baseline 0,
    midband 1, x from the word origin), rounded to the stored precision."""
    ux = (np.asarray(px_x, dtype=float) - registration["tx"]) / xh
    uy = (registration["baseline_row"] + registration["ty"] - np.asarray(px_y, dtype=float)) / xh
    return np.column_stack([ux, uy]).round(4)


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


def cap_word_strokes(strokes: list[list[list[float]]], label: str = "") -> list[list[list[float]]]:
    """Fit a word trace into `api.schemas.WordInstanceItem`'s wire caps.

    A pen run longer than `MAX_STROKE_POINTS` is downsampled by uniform index
    (endpoints kept), and a trace with more than `MAX_WORD_STROKES` runs keeps
    the longest ones in writing order. Both print a warning: a silently
    truncated trace would be worse than a loud one, and a 422 at the endpoint
    would be worse than both.
    """
    out: list[list[list[float]]] = []
    for stroke in strokes:
        if len(stroke) > MAX_STROKE_POINTS:
            keep = np.linspace(0, len(stroke) - 1, MAX_STROKE_POINTS).round().astype(int)
            print(f"  warn: {label} stroke of {len(stroke)} points downsampled to {MAX_STROKE_POINTS}", flush=True)
            stroke = [stroke[i] for i in keep]
        out.append(stroke)
    if len(out) > MAX_WORD_STROKES:
        order = sorted(range(len(out)), key=lambda i: -len(out[i]))[:MAX_WORD_STROKES]
        print(f"  warn: {label} has {len(out)} strokes, keeping the {MAX_WORD_STROKES} longest", flush=True)
        out = [out[i] for i in sorted(order)]
    return out


def _is_diacritic(entry: dict, xh: float, registration: dict) -> bool:
    """`chain._letter_cut_anchors`' rule on a pen-down polyline: a letter stroke
    that is not the first and floats entirely above the midband is a diacritic
    (the i's dot does not connect to the next letter)."""
    if entry["kind"] != "letter" or int(entry.get("stroke_index", 0)) <= 0:
        return False
    pts = np.asarray(entry["points_px"], dtype=float).reshape(-1, 2)
    if not len(pts):
        return False
    uy = (registration["baseline_row"] + registration["ty"] - pts[:, 1]) / xh
    return bool((uy > DIACRITIC_MIN_Y).all())


def assemble_word_strokes(
    entries: Sequence[dict], *, traced_slots: set[int], xh: float, registration: dict
) -> list[list[list[float]]]:
    """A chain fit's pen-down polylines → the word record's strokes.

    The pen run continues `last body stroke of Lᵢ → connectorᵢ → first body
    stroke of Lᵢ₊₁` — one polyline where the hand did not lift — with the
    duplicated seam sample dropped (the two sides share one anchor parameter,
    so the samples coincide exactly). A diacritic and every interior pen lift
    stay their own polyline.

    `traced_slots` is every slot the chain actually SOLVED — deliberately not
    the gate's accepted set. The gate decides what becomes a measurement, not
    what the trace shows: a wobbly letter must not pollute a Laufform median,
    but it was still written, and dropping it (plus the connectors on either
    side) tore the pen path of an otherwise intact run into fragments. A slot
    the chain never fitted at all — no template, no window, `chain_failed` —
    has no geometry to show and legitimately stays out, taking its adjacent
    connectors with it, which would otherwise dangle into a letter that is not
    in the trace. Output is in the word's registration frame, ready for
    `WordInstanceItem.strokes`.
    """
    by_segment: dict[int, list[tuple[int, dict]]] = defaultdict(list)
    for i, entry in enumerate(entries):
        by_segment[int(entry["segment_index"])].append((i, entry))
    order = sorted(by_segment)
    letter_slot = {
        seg: by_segment[seg][0][1].get("slot_index") for seg in order if by_segment[seg][0][1]["kind"] == "letter"
    }

    runs: list[list] = []  # [first entry index, points]
    current: list | None = None

    def flush() -> None:
        nonlocal current
        if current is not None:
            runs.append(current)
            current = None

    def weld(tail: np.ndarray, pts: np.ndarray) -> np.ndarray:
        """Append across a seam, dropping the sample the two sides share."""
        if len(tail) and len(pts) and np.allclose(tail[-1], pts[0], rtol=0.0, atol=SEAM_DEDUP_PX):
            pts = pts[1:]
        return np.vstack([tail, pts]) if len(pts) else tail

    for seg in order:
        items = by_segment[seg]
        if items[0][1]["kind"] == "connector":
            # A connector survives only BETWEEN two traced letters — on either
            # side of an untraced one it would dangle into a letter that is not
            # in the trace at all.
            left = max((s for s in order if s < seg and s in letter_slot), default=None)
            right = min((s for s in order if s > seg and s in letter_slot), default=None)
            joins_traced = (
                left is not None
                and right is not None
                and letter_slot[left] in traced_slots
                and letter_slot[right] in traced_slots
            )
            pts = np.asarray(items[0][1]["points_px"], dtype=float).reshape(-1, 2)
            if not joins_traced or not len(pts):
                flush()
                continue
            if current is None:
                current = [items[0][0], pts]
            else:
                current[1] = weld(current[1], pts)
            continue

        if letter_slot[seg] not in traced_slots:
            flush()
            continue
        body = [(i, e) for i, e in items if not _is_diacritic(e, xh, registration)]
        diacritics = [(i, e) for i, e in items if _is_diacritic(e, xh, registration)]
        if not body:
            flush()
        for n, (i, entry) in enumerate(body):
            pts = np.asarray(entry["points_px"], dtype=float).reshape(-1, 2)
            if not len(pts):
                continue
            if n == 0 and current is not None:
                current[1] = weld(current[1], pts)
                continue
            # every further body stroke is an interior pen lift
            flush()
            current = [i, pts]
        for i, entry in diacritics:
            pts = np.asarray(entry["points_px"], dtype=float).reshape(-1, 2)
            if len(pts):
                runs.append([i, pts])
    flush()

    strokes: list[list[list[float]]] = []
    for _, run in sorted(runs, key=lambda r: r[0]):
        if len(run) < 2:
            continue
        strokes.append(_px_to_word_units(run[:, 0], run[:, 1], xh, registration).tolist())
    return strokes


def letter_gate(
    *,
    converged_local: bool,
    geo_rmse_px: float,
    rmse_max: float,
    at_bound: bool,
    anchors_ok: bool,
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
    5. `connector_degenerate` — a connector ADJACENT to this letter derailed
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
        shift = np.median(fitted_raw - anchors, axis=0)
        fitted = fitted_raw - shift  # shapes, not placements
        per_key[slot.key].append(fitted)
        # The word trace (handmodell word level): this letter's UNCENTERED
        # fitted strokes in the word's shared frame, in writing order.
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
    xh = result.xh_px
    tx, ty = result.registration["tx"], result.registration["ty"]
    baseline_row = result.baseline_row
    registration = {"tx": tx, "ty": ty, "baseline_row": baseline_row}
    keyed = _keyed_indices(case)
    grids = _grid_fits(case, result)

    accepted: set[int] = set()  # gate "ok" — the occurrences and the medians
    traced: set[int] = set()  # every slot the chain solved — the word trace
    gate_by_slot: dict[int, str] = {}
    converged_by_slot: dict[int, bool] = {}
    rmse_by_slot: dict[str, float] = {}
    word_strokes: list[list[list[float]]] = []
    run_slots: list[list[int]] = []
    cut_indices: list[list[list[int]]] = []
    n_params = 0
    seconds = 0.0

    for i, unfittable in enumerate(case.slots):
        if unfittable.key and i not in grids:
            gate_by_slot[i] = "no_template"
            diag_rows.append(_diag_row(case, opts, i, keyed.get(i), unfittable.key, accepted=False, gate="no_template"))

    for run in _chainable_runs(case, grids):
        windows = {s: grids[s]["window"] for s in run}
        fit = fit_word_chain(case, run, result=result, windows_px=windows)
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

        run_slots.append(list(fit.slots))
        traced.update(int(s) for s in fit.slots)
        cut_indices.append([[int(a), int(b)] for a, b in fit.cut_indices])
        n_params += int(fit.fit_meta.get("n_params", 0))
        seconds += float(fit.fit_meta.get("seconds", 0.0))
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
            gate = letter_gate(
                converged_local=bool(seg.converged_local),
                geo_rmse_px=float(seg.geo_rmse_px),
                rmse_max=opts.rmse_max,
                at_bound=bool(fit.slot_at_bound.get(slot_index, False)),
                anchors_ok=fitted_raw.shape == anchors.shape,
                connector_reasons=adjacent,
            )
            gate_by_slot[slot_index] = gate
            converged_by_slot[slot_index] = bool(seg.converged_local)
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
                shift_x_units=round(float(total_shift[0]), 4),
                shift_y_units=round(float(total_shift[1]), 4),
                conn_reason_adjacent=",".join(r for r in adjacent if r),
                conn_reason=conn_reasons.get(n) or "",
                n_params=int(fit.fit_meta.get("n_params", 0)),
                seconds=round(float(fit.fit_meta.get("seconds", 0.0)), 3),
                **conn_signals.get(n, {}),
            )
            diag_rows.append(diag)
            if gate != "ok":
                continue

            accepted.add(slot_index)
            shift = np.median(fitted_raw - anchors, axis=0)
            fitted = fitted_raw - shift  # shapes, not placements
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
                    },
                }
            )

        # The whole solved run goes into the trace — a gate verdict decides what
        # is measured, not what was written (the per-slot verdicts stay readable
        # in `gates`/`converged_local` beside it).
        word_strokes.extend(
            assemble_word_strokes(
                fit.stroke_polylines_px, traced_slots=set(fit.slots), xh=xh, registration=registration
            )
        )

    word_record = None
    if word_strokes:
        word_record = _word_record(
            case,
            cap_word_strokes(word_strokes, label=f"{case.id} (chain)"),
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
                "seconds": round(seconds, 3),
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
    opts = HarvestOptions(style=style, rmse_max=rmse_max, path=path)
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


def apply_drafts(drafts: dict[str, dict], base_url: str, source_id: str, token: str) -> None:
    failed: list[str] = []
    for key, d in drafts.items():
        req = urllib.request.Request(
            f"{base_url}/sources/{source_id}/templates/{key}/laufform",
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
    ap.add_argument("--jobs", type=int, default=1, help="parallel worker processes over CASES (default 1)")
    ap.add_argument("--max-cases", type=int, default=0, help="cap the cases per run (0 = all)")
    ap.add_argument("--min-n", type=int, default=4)
    ap.add_argument("--rmse-max", type=float, default=2.2)
    ap.add_argument("--out", type=Path, default=Path("laufform_drafts.json"))
    ap.add_argument("--occ-out", type=Path, default=Path("laufform_occurrences.json"))
    ap.add_argument("--word-out", type=Path, default=Path("laufform_words.json"))
    ap.add_argument("--diag-csv", type=Path, help="per-slot gate diagnostics (one row per slot)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--source-id")
    ap.add_argument("--hand-id", default="suetterlin-1922-norm")
    ap.add_argument("--hand-label", default="Suetterlin norm hand (Leitfaden 1922, Abb. 19/20)")
    args = ap.parse_args()
    if args.jobs < 1:
        raise SystemExit(f"--jobs must be >= 1, got {args.jobs}")
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
        args.style, args.min_n, args.rmse_max, sets=sets, path=args.path, jobs=args.jobs, max_cases=args.max_cases
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
        apply_drafts(drafts, base, args.source_id, token)
        apply_batch("instances", occurrences, base, args.source_id, token, args.hand_id, args.hand_label)
        apply_batch("word-instances", word_records, base, args.source_id, token, args.hand_id, args.hand_label)


if __name__ == "__main__":
    main()
