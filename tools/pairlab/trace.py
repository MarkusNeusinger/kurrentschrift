"""Word-trace assembly: a chain fit's pen-down polylines → one word record.

Pure geometry, no I/O: the fitted chain arrives as the `stroke_polylines_px`
entries `tools.pairlab.chain.fit_word_chain` emits, and what leaves is the
stroke list `api.schemas.WordInstanceItem` takes — welded across the seams the
hand did not lift at, in the word's registration frame, inside the wire caps.

Why `tools/pairlab` and not `tools/laufform`, where this code was written: the
ink-follower (`tools/pairlab/follow.py`, `docs/proposals/tintenfolger.md` §3)
needs the same assembler, and `tools.pairlab` importing `tools.laufform` would
be an import CYCLE — the harvest already imports `pairlab.chain`,
`pairlab.anchors` and `pairlab.connector_qc`. One shared module below both
consumers is the same resolution `tools/pairlab/anchors.py` took for the
stranded-anchor detector. `tools.laufform.harvest` re-exports every name here,
so its own callers and tests are unaffected.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

import numpy as np


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


def _px_to_word_units(px_x: np.ndarray, px_y: np.ndarray, xh: float, registration: dict) -> np.ndarray:
    """Crop pixels → the WORD's registration frame (template units, baseline 0,
    midband 1, x from the word origin), rounded to the stored precision."""
    ux = (np.asarray(px_x, dtype=float) - registration["tx"]) / xh
    uy = (registration["baseline_row"] + registration["ty"] - np.asarray(px_y, dtype=float)) / xh
    return np.column_stack([ux, uy]).round(4)


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
    entries: Sequence[dict],
    *,
    traced_slots: set[int],
    xh: float,
    registration: dict,
    restart_slots: set[int] | frozenset[int] = frozenset(),
) -> list[list[list[float]]]:
    """A chain fit's pen-down polylines → the word record's strokes.

    The pen run continues `last body stroke of Lᵢ → connectorᵢ → first body
    stroke of Lᵢ₊₁` — one polyline where the hand did not lift — with the
    duplicated seam sample dropped (the two sides share one anchor parameter,
    so the samples coincide exactly). A diacritic and every interior pen lift
    stay their own polyline.

    ``restart_slots`` (Korb #5, „Säbel" S→ä): slot indices of the restart-class
    capitals (CAP_RESTART_BASES). The writer LIFTS after such a capital and
    sets down fresh near the baseline (Grundlinie) — the composed connector's retrace
    prefix (ductus end → working exit, duplicating the capital's own ink) is a
    render construct, not a pen movement the trace may claim. The run ends at
    the capital's body; the connector keeps only its piece from the lowest
    point onward (the fresh set-down, Ansatz, rising into the next letter).

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
            if left is not None and letter_slot[left] in restart_slots:
                # Pen lift after a restart capital: cut the retrace prefix
                # (crop px, y grows downward — argmax y is the baseline turn)
                # and start the fresh set-down as its own stroke.
                flush()
                pts = pts[int(np.argmax(pts[:, 1])) :]
                if len(pts) >= 2:
                    current = [items[0][0], pts]
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


__all__ = [
    "DIACRITIC_MIN_Y",
    "MAX_STROKE_POINTS",
    "MAX_WORD_STROKES",
    "SEAM_DEDUP_PX",
    "assemble_word_strokes",
    "cap_word_strokes",
]
