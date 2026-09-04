"""``dspan`` — the extension-normalized shape distance of a letter join.

The rescue path of the #488 negative (`docs/reference/messjournal.md` §14
„Übergänge J4b", Rettungsweg 2), built as a NEW sensor beside the frozen ruler,
never as an edit of it: `core/word_metric.py` is untouched, `dconn` in
`tools/wordbench/pairmeas.py` is untouched, and nothing here enters
``bench_loss``/``pair_loss``.

What it is for
--------------
``dconn`` lays the composed and the measured connector on their own FIRST
sample and compares point i with point i. That is exactly right while both
curves cover the same stretch of pen path — and wrong the moment a rule moves
the boundary between letter and connector. The exit trim of arm J4 is such a
rule: after the cut the letter no longer writes its stub, so the connector
draws that piece instead and comes out LONGER at the head, with its shape over
the shared stretch unchanged. ``dconn`` books the extra head as a shape
difference. §14 „Übergänge J4" measured how much: of the +0.043 xh rise that
failed the arm's gate, about two thirds (median +0.051 of the per-join
difference) were this frame artifact, and the hand-cleaned reading fell the
other way (0.102 → 0.099, down in 51 % of joins instead of 20 %).

The sizes are what make this a measurement problem rather than a nuisance. The
word ruler's sensitivity window is 0.05–0.12 xh; the trim's own arc has a
median of 0.185 xh (p90 0.469). The artifact is LARGER than the defect it
hides, so no threshold on ``dconn`` can separate them — the normalisation has
to happen inside the measure.

The measure
-----------
Both connectors of a join end at the same event: the pen's arrival on B. So the
arrival is the anchor, and the shared stretch is the last ``L = min(arc)`` of
each curve:

1. clip both curves from their END back to arc length ``L`` (the cut point is
   interpolated, so a coarse sample step cannot move it);
2. resample both to ``PAIR_CONNECTOR_POINTS`` arc-length-uniformly — the same
   budget ``dconn`` and the pair aggregation use;
3. put each on its own first sample of that clipped span (start-aligned, hence
   translation-free: placement stays ``doff``'s column alone);
4. ``dspan`` = mean pointwise Euclidean distance, in x-height units.

Two consequences, both deliberate and both stated before the first number:

* ``dspan`` is BLIND to a pure extension at the head — that is the artifact it
  exists to remove, not an oversight. Whether a join *should* run longer is a
  question about the departure point, which is placement's and the seam angle's
  business, not this column's.
* ``dspan`` is not ``dconn`` with a correction term. The two agree only where
  the spans already match; where they do not, ``dspan`` answers a narrower
  question (is the shared piece the same shape?) and answers it cleanly.

Report-only, like ``doff``/``dconn``: a monotone signal per join — same join,
smaller number = closer to the specimen — never a calibrated absolute.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from core.aggregate import PAIR_CONNECTOR_POINTS, _resample_polyline
from core.compose import compose_word
from tools.wordbench.pairmeas import body_lines, join_pair_keys, load_measured, rows_for_entry
from tools.wordlab.cases import DEFAULT_FIXTURES_DIR, WordCase, _root_for, iter_fixture_word_cases
from tools.wordlab.derive import laufform_payloads_for, payloads_for


def arc_length(points: np.ndarray) -> float:
    """Total arc length of an open polyline."""
    a = np.asarray(points, dtype=float).reshape(-1, 2)
    if len(a) < 2:
        return 0.0
    return float(np.hypot(*np.diff(a, axis=0).T).sum())


def clip_tail(points: np.ndarray, keep: float) -> np.ndarray:
    """The last ``keep`` of arc of a polyline, cut point interpolated.

    Walks back from the end; the segment the cut falls inside is split at the
    exact arc position, so the result covers ``keep`` regardless of how coarsely
    the curve is sampled. ``keep`` at or above the total length returns the
    curve unchanged; a degenerate curve is returned as it is.
    """
    a = np.asarray(points, dtype=float).reshape(-1, 2)
    if len(a) < 2 or keep <= 0.0:
        return a
    seg = np.hypot(*np.diff(a, axis=0).T)
    total = float(seg.sum())
    if keep >= total or total <= 1e-12:
        return a
    # Arc measured backwards from the last sample.
    from_end = np.concatenate([[0.0], np.cumsum(seg[::-1])])[::-1]  # per sample
    first_kept = int(np.searchsorted(-from_end, -keep, side="left"))
    if first_kept <= 0:
        return a
    prev, nxt = a[first_kept - 1], a[first_kept]
    overshoot = keep - from_end[first_kept]
    step = float(np.hypot(*(nxt - prev)))
    if step <= 1e-12:
        return a[first_kept:]
    t = 1.0 - overshoot / step
    cut = prev + (nxt - prev) * t
    return np.vstack([cut, a[first_kept:]])


def common_span(composed: np.ndarray, measured: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Both curves reduced to the same extension, measured back from their end."""
    keep = min(arc_length(composed), arc_length(measured))
    return clip_tail(composed, keep), clip_tail(measured, keep)


def dspan(composed: np.ndarray, measured: np.ndarray, *, points: int = PAIR_CONNECTOR_POINTS) -> float:
    """Extension-normalized shape distance of two connector centerlines (xh)."""
    c, m = common_span(composed, measured)
    if len(c) < 2 or len(m) < 2:
        return float("nan")
    a = _resample_polyline(c, points)
    b = _resample_polyline(m, points)
    return float(np.linalg.norm((a - a[0]) - (b - b[0]), axis=1).mean())


def dconn(composed: np.ndarray, measured: np.ndarray, *, points: int = PAIR_CONNECTOR_POINTS) -> float:
    """``pairmeas``'s start-aligned shape distance, recomputed here for the split.

    Same formula, same budget — quoted next to ``dspan`` so a run can report how
    much of a move was extension and how much was shape. The frozen column in
    `tools/wordbench/pairmeas.py` stays the one the bench prints.
    """
    a = _resample_polyline(np.asarray(composed, dtype=float), points)
    b = _resample_polyline(np.asarray(measured, dtype=float), points)
    return float(np.linalg.norm((a - a[0]) - (b - b[0]), axis=1).mean())


def compare_joins(composed: dict, slots: Sequence[Any], measured: Iterable[dict]) -> list[dict]:
    """One row per join that has a comparable measured occurrence.

    The exclusions are ``pairmeas.compare_joins``'s, for the same reasons: an
    approved override is its own source specimen, a dissection the harvest
    distrusts (``fit_ok`` unset) must not carry a median, and a frozen slot list
    that moved under the harvest is not comparable. Rows carry ``dconn``
    alongside ``dspan`` plus both arc lengths, so the extension share of a move
    is readable per join instead of inferred.
    """
    by_slot = {int(r["slot"]): r for r in measured}
    bodies = body_lines(composed)
    rows: list[dict] = []
    for item in composed.get("items", []):
        pair = item.get("pair")
        if not pair or pair[1] is None or item.get("override"):
            continue
        row = by_slot.get(item.get("from_slot"))
        if row is None:
            continue
        left, right = join_pair_keys(slots, item)
        if (row["left_key"], row["right_key"]) != (left, right):
            continue
        if not (row.get("measurements") or {}).get("fit_ok"):
            continue
        if not bodies.get(item.get("from_slot")) or not bodies.get(item.get("to_slot")):
            continue
        c = np.asarray(item["centerline"], dtype=float)
        m = np.asarray(row["geometry"]["connector"], dtype=float)
        if len(c) < 2 or len(m) < 2:
            continue
        arc_c, arc_m = arc_length(c), arc_length(m)
        rows.append(
            {
                "slot": int(row["slot"]),
                "pair": [left, right],
                "dspan": round(dspan(c, m), 4),
                "dconn": round(dconn(c, m), 4),
                "arc_composed": round(arc_c, 4),
                "arc_measured": round(arc_m, 4),
                "clipped": round(abs(arc_c - arc_m), 4),
            }
        )
    return rows


# ----------------------------------------------------------------- fixture run


def _compose_case(case: WordCase, *, exit_trim: bool, exit_trim_min_kink_deg: float) -> dict:
    """The bench's composition of one fixture entry, with the J4 switch exposed.

    Same inputs `tools/wordbench/run.py` composes with on a headline run
    (provenance on, Laufform rows applied, no overrides), so a row measured here
    describes the same join the bench scores.
    """
    return compose_word(
        case.slots,
        payloads_for(case),
        provenance=True,
        laufform_by_key=laufform_payloads_for(case) or None,
        exit_trim=exit_trim,
        exit_trim_min_kink_deg=exit_trim_min_kink_deg,
    )


def run_set(
    which: str,
    *,
    style: str = "suetterlin",
    fixtures_root: Path = DEFAULT_FIXTURES_DIR,
    exit_trim: bool = False,
    exit_trim_min_kink_deg: float = 0.0,
) -> list[dict]:
    """Every comparable join of one fixture set, with its id and word attached."""
    artifact = load_measured(_root_for(fixtures_root, style, which))
    if artifact is None:
        return []
    out: list[dict] = []
    for case in iter_fixture_word_cases(which=which, style=style, fixtures_root=fixtures_root):
        if not case.scorable:
            continue
        composed = _compose_case(case, exit_trim=exit_trim, exit_trim_min_kink_deg=exit_trim_min_kink_deg)
        if composed["missing"]:
            continue
        for row in compare_joins(composed, case.slots, rows_for_entry(artifact, case.kind, case.id)):
            out.append({"id": case.id, "word": case.word, "kind": case.kind, **row})
    return out


def _median(values: list[float]) -> float | None:
    return round(statistics.median(values), 4) if values else None


def summarise(rows: list[dict]) -> dict:
    """Medians and the extension share over a run's rows."""
    return {
        "n": len(rows),
        "dspan_median": _median([r["dspan"] for r in rows]),
        "dconn_median": _median([r["dconn"] for r in rows]),
        "clipped_median": _median([r["clipped"] for r in rows]),
        "n_clipped": sum(1 for r in rows if r["clipped"] > 1e-6),
    }


def compare_runs(base: list[dict], arm: list[dict]) -> dict:
    """Per-join change between two runs of the same set — the arm's own number.

    Joins are matched on ``(id, slot)``; a join present in only one run is
    counted, never silently dropped, because an arm that changes WHICH joins are
    comparable has changed its population, not its numbers.
    """
    by_key = {(r["id"], r["slot"]): r for r in base}
    paired = [(by_key[k], r) for r in arm if (k := (r["id"], r["slot"])) in by_key]
    moved = [(b, a) for b, a in paired if abs(a["dspan"] - b["dspan"]) > 1e-9]
    return {
        "n_base": len(base),
        "n_arm": len(arm),
        "n_paired": len(paired),
        "unmatched": len(base) + len(arm) - 2 * len(paired),
        "n_moved": len(moved),
        "dspan_base_median": _median([b["dspan"] for b, _ in paired]),
        "dspan_arm_median": _median([a["dspan"] for _, a in paired]),
        "dconn_base_median": _median([b["dconn"] for b, _ in paired]),
        "dconn_arm_median": _median([a["dconn"] for _, a in paired]),
        "dspan_falls": sum(1 for b, a in moved if a["dspan"] < b["dspan"]),
        "dconn_falls": sum(1 for b, a in moved if a["dconn"] < b["dconn"]),
        "dspan_fall_share": round(sum(1 for b, a in moved if a["dspan"] < b["dspan"]) / len(moved), 3)
        if moved
        else None,
        "dconn_fall_share": round(sum(1 for b, a in moved if a["dconn"] < b["dconn"]) / len(moved), 3)
        if moved
        else None,
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="pairlab.spanmeas", description=__doc__.split("\n\n")[0])
    p.add_argument("--set", dest="which", choices=["words", "pairs"], default="words")
    p.add_argument("--style", default="suetterlin")
    p.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES_DIR, help="fixture root (default: the frozen one)")
    p.add_argument("--exit-trim", action="store_true", help="compose with the J4 exit trim on (candidate arm)")
    p.add_argument(
        "--exit-trim-min-kink", type=float, default=0.0, help="J4b: only trim joins whose base departure kinks by this"
    )
    p.add_argument("--json", type=Path, help="write the per-join rows here")
    p.add_argument("--base", type=Path, help="a rows JSON of the same set to compare against (the arm's own number)")
    args = p.parse_args()

    rows = run_set(
        args.which,
        style=args.style,
        fixtures_root=args.fixtures,
        exit_trim=args.exit_trim,
        exit_trim_min_kink_deg=args.exit_trim_min_kink,
    )
    print(json.dumps(summarise(rows), indent=1))
    if args.base:
        print(json.dumps(compare_runs(json.loads(args.base.read_text()), rows), indent=1))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(rows, indent=1, ensure_ascii=False))
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
