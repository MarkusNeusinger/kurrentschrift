"""One word's row, the run's block, and the paired comparison between two runs.

This is the layer that turns the ruler (`metric`, `frames`, `counters`) into the
columns `docs/reference/qualitaetsmetrik.md` §14 pre-registered — and it holds
to that list rather than inventing a folded score. There is deliberately no
`trace_loss`: a weight between "0.02 xh of body error" and "one missing i-dot"
is a number nobody has measured, so `dtw_xh` is the headline, missing marks and
lost crossings are co-primary GATES a distance gain cannot buy back, and `aiou`,
the two chamfer halves and `retrace_arc_ratio` are cost watchdogs.

Everything flows through the bench frame: both traces travel from their OWN
stored registration back to crop pixels and from there into x-heights, marks are
split off before the body DTW, and every counter reads the same discretisation
the distance does. The only column that leaves that frame is `aiou`, which is
rasterised back into crop pixels because it grades against the frozen ink mask
rather than against a reference trace.
"""

from __future__ import annotations

import time
from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np

from tools.tracebench.candidates import STATUS_FAILED, STATUS_OK, Candidate
from tools.tracebench.counters import (
    RESAMPLE_STEP_UNITS,
    count_crossings,
    count_retraces,
    resampled_strokes,
    structure_zones,
)
from tools.tracebench.frames import (
    MARK_MAX_ARC_UNITS,
    classify_strokes,
    concat_body,
    concat_strokes,
    lift_stats,
    match_marks,
)
from tools.tracebench.metric import aiou, chamfer, dtw
from tools.tracebench.reference import ReferenceEntry


# How many delayed marks a glyph's written form carries. The keys are
# `core.shaping`'s registry keys — the umlauts are ascii-safe bases (ä → "ae",
# ö → "oe", ü → "ue"), which is why this is a KEY set and not a character set,
# and `tests/test_tracebench_summary.py` pins every one of them against
# `core.shaping.is_registry_glyph_key` so a typo cannot pass as "no marks here".
#
# Deliberately CONSERVATIVE — one mark per key even where a form could be read
# as carrying two (the ü's umlaut over a u that also wants its Deckstrich).
# The number is a CROSS-CHECK, never a gate: where the reference's own mark
# count disagrees with it, the row is stamped `marks_uncertain` and the human
# reads the mark columns with that in mind. Guessing higher would turn an
# uncertainty into a fabricated "spurious mark".
MARKS_PER_KEY: dict[str, int] = {
    "i": 1,  # i-Punkt
    "j": 1,  # the same dot, on the descender
    "u": 1,  # u-Deckstrich (tintenfolger.md §2.3 names it a mark)
    "ae": 1,  # ä
    "oe": 1,  # ö
    "ue": 1,  # ü
    "Ae": 1,
    "Oe": 1,
    "Ue": 1,
}

# Report-only columns whose medians the block prints, in the order §14 lists them.
_MEDIAN_COLUMNS = ("dtw_xh", "aiou", "chamfer_cand_ref_xh", "chamfer_ref_cand_xh", "retrace_arc_ratio")
# The hard-spot totals — the co-primary gates plus their refusal counts.
_TOTAL_COLUMNS = (
    "marks_missing",
    "marks_spurious",
    "marks_ambiguous",
    "cross_missing",
    "cross_spurious",
    "cross_ambiguous",
    "retrace_missing",
    "retrace_spurious",
    "touch_ref",
    "touch_cand",
    "overlap_ref",
    "overlap_cand",
    "direction_uncertain",
)


def expected_marks(slot_keys: Sequence[str]) -> int:
    """How many delayed marks this word's frozen slots ask for."""
    return sum(MARKS_PER_KEY.get(str(key), 0) for key in slot_keys)


def _point_count(strokes: Sequence[np.ndarray]) -> int:
    return int(sum(len(np.asarray(s).reshape(-1, 2)) for s in strokes))


def _orientation_reversed(ref: np.ndarray, cand: np.ndarray) -> bool:
    """Does this candidate stroke read better END-first against its reference?

    Endpoint concordance, not a distance: `d(start, start) + d(end, end)`
    against the crossed pairing. Cheap, and it answers exactly the question the
    forward-only DTW cannot — whether the two hands travelled the same way.
    """
    a, b = np.asarray(ref, dtype=float).reshape(-1, 2), np.asarray(cand, dtype=float).reshape(-1, 2)
    if len(a) < 2 or len(b) < 2:
        return False
    aligned = float(np.hypot(*(a[0] - b[0])) + np.hypot(*(a[-1] - b[-1])))
    crossed = float(np.hypot(*(a[0] - b[-1])) + np.hypot(*(a[-1] - b[0])))
    return crossed < aligned


def direction_audit(body_ref: list[np.ndarray], body_cand: list[np.ndarray]) -> tuple[int, int]:
    """`(strokes flagged, strokes compared)` — the §2.3 reference-set audit.

    Order-matched, because the writing ORDER is the truth the bench rests on:
    the n-th body stroke of one side is held against the n-th of the other. A
    flag is a FIXTURE-QUALITY signal, not a candidate error — the human trace
    may simply have been drawn backwards, and with a forward-only DTW that
    would otherwise be read as a model failure.
    """
    pairs = list(zip(body_ref, body_cand, strict=False))
    return sum(1 for a, b in pairs if _orientation_reversed(a, b)), len(pairs)


def score_word(
    reference_entry: ReferenceEntry,
    candidate: Candidate,
    *,
    label: str = "",
    split: str = "",
    resample_step: float = RESAMPLE_STEP_UNITS,
    mark_arc_cap: float = MARK_MAX_ARC_UNITS,
) -> dict[str, Any]:
    """One word: the flat §14 row for this candidate against its reference.

    A candidate that never arrived (`status != "ok"`) still produces a row —
    with the reference side filled in and every measured column `None` — so the
    report can never lose a word to a provider failure.

    `mark_arc_cap` reaches both sides of the classification and nothing else.
    Its default is the ruler as it stands (1.5 since §14 „Lineal L-U"); pass
    0.8 to reproduce any number recorded before `aug26`.
    """
    started = time.perf_counter()
    entry = reference_entry
    frame = entry.frame
    ref_strokes = frame.trace_to_bench(entry.row.strokes, entry.row.registration_px, entry.row.xh_px)
    ref_body, ref_marks = classify_strokes(ref_strokes, mark_arc_cap)
    expected = expected_marks(entry.slots)

    row: dict[str, Any] = {
        "id": entry.specimen_id,
        "word": entry.word,
        "kind": entry.kind,
        "split": split,
        "candidate": label,
        "status": candidate.status,
        "detail": candidate.detail,
        "ref_strokes": len(ref_strokes),
        "ref_points": _point_count(ref_strokes),
        "ref_marks": len(ref_marks),
        "cand_strokes": 0,
        "cand_points": 0,
        "cand_marks": 0,
        "marks_expected": expected,
        "marks_uncertain": len(ref_marks) != expected,
    }
    for key in (
        "dtw_xh",
        "dtw_reversed_better",
        "dtw_max_absorption",
        "dtw_path_len",
        "aiou",
        "aiou_k",
        "chamfer_cand_ref_xh",
        "chamfer_ref_cand_xh",
        "retrace_arc_ratio",
        "mark_pos_err_xh",
        "cross_pos_err_xh",
        "retrace_pos_err_xh",
        "lift_pos_err_xh",
    ):
        row[key] = None
    if not candidate.ok:
        row["secs"] = round(time.perf_counter() - started, 3)
        return row

    cand_strokes = frame.trace_to_bench(candidate.strokes, candidate.registration_px, candidate.xh_px)
    cand_body, cand_marks = classify_strokes(cand_strokes, mark_arc_cap)
    row.update(cand_strokes=len(cand_strokes), cand_points=_point_count(cand_strokes), cand_marks=len(cand_marks))
    if not ref_body or not cand_body:
        side = "reference" if not ref_body else "candidate"
        row["status"] = STATUS_FAILED
        row["detail"] = f"{side} has no body stroke (everything classified as a mark)"
        row["secs"] = round(time.perf_counter() - started, 3)
        return row

    # ---- the headline: body DTW in writing order, marks held out ----------
    # Resampled per STROKE and only then concatenated: resampling the joined
    # sequence would lay samples along the jump between two pen strokes, i.e.
    # invent ink across a lift.
    ref_seq = concat_body(resampled_strokes(ref_body, resample_step))
    cand_seq = concat_body(resampled_strokes(cand_body, resample_step))
    forward = dtw(ref_seq, cand_seq)
    reversed_run = dtw(ref_seq, cand_seq[::-1])
    row.update(
        dtw_xh=forward.mean_xh,
        dtw_path_len=forward.path_len,
        dtw_max_absorption=forward.max_absorption,
        dtw_reversed_better=bool(reversed_run.mean_xh < forward.mean_xh),
    )

    # ---- the two chamfer halves, over the WHOLE trace ---------------------
    # Marks included on both sides: a lost i-dot must inflate the recall half,
    # which is the one thing a body-only distance can never say.
    ref_cloud = concat_strokes(resampled_strokes(ref_strokes, resample_step))[0]
    cand_cloud = concat_strokes(resampled_strokes(cand_strokes, resample_step))[0]
    cand_ref, ref_cand = chamfer(cand_cloud, ref_cloud)
    row.update(chamfer_cand_ref_xh=cand_ref, chamfer_ref_cand_xh=ref_cand)

    # ---- AIoU against the frozen ink, in crop pixels ----------------------
    ink = entry.ink_mask()
    aiou_result = aiou([frame.bench_to_crop_px(s) for s in cand_strokes], ink)
    row.update(aiou=aiou_result.value, aiou_k=aiou_result.k, aiou_iou_k0=aiou_result.iou_k0)

    # ---- the counters at the hard places ----------------------------------
    marks = match_marks(ref_marks, cand_marks)
    row.update(
        marks_ref=marks.ref,
        marks_cand=marks.cand,
        marks_matched=marks.matched,
        marks_missing=marks.missing,
        marks_spurious=marks.spurious,
        marks_ambiguous=marks.ambiguous,
        mark_pos_err_xh=marks.pos_err_xh,
    )
    crossings = count_crossings(ref_strokes, cand_strokes, resample_step=resample_step)
    row.update(
        cross_ref=crossings.ref,
        cross_cand=crossings.cand,
        cross_matched=crossings.matched,
        cross_missing=crossings.missing,
        cross_spurious=crossings.spurious,
        cross_ambiguous=crossings.ambiguous,
        cross_pos_err_xh=crossings.pos_err_xh,
    )
    retraces = count_retraces(ref_strokes, cand_strokes, resample_step=resample_step)
    row.update(
        retrace_ref=retraces.ref,
        retrace_cand=retraces.cand,
        retrace_matched=retraces.matched,
        retrace_missing=retraces.missing,
        retrace_spurious=retraces.spurious,
        retrace_ambiguous=retraces.ambiguous,
        retrace_pos_err_xh=retraces.pos_err_xh,
        retrace_arc_ref=retraces.arc_ref,
        retrace_arc_cand=retraces.arc_cand,
        # The robust half of the retrace measurement: how much ink was written
        # twice, candidate over reference. None where the reference retraced
        # nothing at all — a ratio against zero is not a number, and the two
        # arcs stay in the row for the reader.
        retrace_arc_ratio=(retraces.arc_cand / retraces.arc_ref) if retraces.arc_ref > 0 else None,
    )
    # The v2 classes beside the retrace (§14 `aug16`): writing PAST each other
    # (touch) and a mark riding the body (overlap) — counted and reported per
    # side, never matched and never part of any loss.
    zones_ref = structure_zones(ref_strokes, resample_step=resample_step)
    zones_cand = structure_zones(cand_strokes, resample_step=resample_step)
    row.update(
        touch_ref=len(zones_ref.touch_mids),
        touch_cand=len(zones_cand.touch_mids),
        overlap_ref=len(zones_ref.overlap_mids),
        overlap_cand=len(zones_cand.overlap_mids),
    )
    row.update(lift_stats(ref_body, cand_body))
    flagged, compared = direction_audit(ref_body, cand_body)
    row.update(direction_uncertain=flagged, direction_checked=compared)
    row["secs"] = round(time.perf_counter() - started, 3)
    return row


# ------------------------------------------------------------------ the block


def _values(rows: Iterable[dict], column: str) -> list[float]:
    return [float(r[column]) for r in rows if r.get(column) is not None]


def _median(values: Sequence[float]) -> float | None:
    return float(np.median(values)) if len(values) else None


def _p90(values: Sequence[float]) -> float | None:
    return float(np.percentile(values, 90)) if len(values) else None


def summarize(rows: Sequence[dict], *, excluded: dict[str, int] | None = None) -> dict[str, Any]:
    """The run's block: the §14 medians, the p90 cost column and the hard-spot totals.

    Medians run over the SCORED rows only; a failed or skipped word is counted
    (and named) instead of being averaged in as a value it never produced.
    """
    scored = [r for r in rows if r.get("status") == STATUS_OK]
    out: dict[str, Any] = {
        "rows": len(rows),
        "scored": len(scored),
        "failed": sum(1 for r in rows if r.get("status") == STATUS_FAILED),
        "skipped": len(rows) - len(scored) - sum(1 for r in rows if r.get("status") == STATUS_FAILED),
    }
    for column in _MEDIAN_COLUMNS:
        out[f"{column}_median"] = _median(_values(scored, column))
    # The only p90 the criteria table asks for: the cost side of the headline.
    out["dtw_xh_p90"] = _p90(_values(scored, "dtw_xh"))
    out["dtw_xh_worst"] = max(
        ((r["dtw_xh"], r["id"]) for r in scored if r.get("dtw_xh") is not None), default=(None, None)
    )
    for column in _TOTAL_COLUMNS:
        out[column] = int(sum(int(r.get(column) or 0) for r in scored))
    out["dtw_reversed_better"] = int(sum(1 for r in scored if r.get("dtw_reversed_better")))
    out["marks_uncertain"] = int(sum(1 for r in rows if r.get("marks_uncertain")))
    out["lift_delta_total"] = int(sum(int(r.get("lift_delta") or 0) for r in scored))
    out["dtw_max_absorption_max"] = max((int(r["dtw_max_absorption"]) for r in scored), default=None)
    out["secs"] = round(float(sum(float(r.get("secs") or 0.0) for r in rows)), 2)
    out["excluded"] = dict(excluded or {})
    return out


def identity_gate(rows: Sequence[dict]) -> list[str]:
    """Why `authored` vs. `authored` was not an exact identity — `[]` when it was.

    §14's third kill criterion, and the one that runs FIRST: a trace scored
    against itself must land on dtw = 0, chamfer = 0 and every counter matched.
    Anything else means the ruler is broken — a frame that moves, a detector
    that cannot find its own structure, a resampling that is not idempotent —
    and no candidate number is read until it is fixed.
    """
    failures: list[str] = []
    for row in rows:
        name = row.get("id", "?")
        if row.get("status") != STATUS_OK:
            failures.append(f"{name}: {row.get('status')} ({row.get('detail')})")
            continue
        if row.get("dtw_xh") != 0.0:
            failures.append(f"{name}: dtw_xh {row.get('dtw_xh')!r} != 0")
        for column in ("chamfer_cand_ref_xh", "chamfer_ref_cand_xh"):
            if row.get(column) != 0.0:
                failures.append(f"{name}: {column} {row.get(column)!r} != 0")
        for prefix in ("marks", "cross", "retrace"):
            for suffix in ("missing", "spurious", "ambiguous"):
                if row.get(f"{prefix}_{suffix}"):
                    failures.append(f"{name}: {prefix}_{suffix} = {row.get(f'{prefix}_{suffix}')}")
        if row.get("lift_delta"):
            failures.append(f"{name}: lift_delta = {row.get('lift_delta')}")
        if row.get("dtw_reversed_better"):
            failures.append(f"{name}: dtw_reversed_better on an identity")
    return failures


# -------------------------------------------------------------- the comparison


def _sign_test():
    """`tools.pairlab.chainbench.sign_test` — imported, never restated.

    The chain bench already owns the project's two-sided sign test; a second
    implementation would be a second definition of the same statistic, and the
    two would drift. Imported lazily because `chainbench` pulls the whole fit
    stack (and matplotlib through `tools.wordlab`), which a bench run that only
    scores a candidate file has no business loading.
    """
    from tools.pairlab.chainbench import sign_test  # noqa: PLC0415

    return sign_test


def compare(rows_a: Sequence[dict], rows_b: Sequence[dict]) -> dict[str, Any]:
    """B against A, paired per word — the §14 criteria as numbers, not verdicts.

    `a` is the earlier run (the baseline), `b` the current one, and every delta
    is `b - a`, so a negative `dtw` delta is an improvement. The pairing is by
    specimen id over the words BOTH runs scored: a word one side could not score
    is reported in `unpaired` rather than compared against a hole.

    The primary criterion is stated twice on purpose. `dtw_delta_median` is the
    median of the paired differences (§14's own wording) and `dtw_rel_median`
    the median of the per-word RELATIVE differences — with ten words the two can
    disagree, and a run that quotes only the flattering one is not measuring.
    """
    by_id_a = {r["id"]: r for r in rows_a if r.get("status") == STATUS_OK}
    by_id_b = {r["id"]: r for r in rows_b if r.get("status") == STATUS_OK}
    shared = [i for i in by_id_b if i in by_id_a]
    deltas: list[float] = []
    relatives: list[float] = []
    per_word: list[dict] = []
    for specimen_id in shared:
        a, b = by_id_a[specimen_id], by_id_b[specimen_id]
        if a.get("dtw_xh") is None or b.get("dtw_xh") is None:
            continue
        delta = float(b["dtw_xh"]) - float(a["dtw_xh"])
        deltas.append(delta)
        if float(a["dtw_xh"]) > 0.0:
            relatives.append(delta / float(a["dtw_xh"]))
        per_word.append({"id": specimen_id, "a": float(a["dtw_xh"]), "b": float(b["dtw_xh"]), "delta": delta})

    summary_a = summarize(rows_a)
    summary_b = summarize(rows_b)
    out: dict[str, Any] = {
        "paired": len(deltas),
        "unpaired": sorted(set(by_id_a) ^ set(by_id_b)),
        "dtw_delta_median": _median(deltas),
        "dtw_delta_p90": _p90(deltas),
        "dtw_rel_median": _median(relatives),
        "sign_test": _sign_test()(deltas),
        "per_word": sorted(per_word, key=lambda r: r["delta"]),
    }
    # The gates and the cost watchdogs as (a, b, delta) triples — a structure
    # defect vetoes a distance gain, so they are reported beside the headline
    # rather than folded into it.
    for column in ("marks_missing", "cross_missing", "cross_spurious", "failed", "skipped", "dtw_reversed_better"):
        out[f"{column}_ab"] = (summary_a.get(column), summary_b.get(column))
    for column in ("aiou_median", "chamfer_ref_cand_xh_median", "chamfer_cand_ref_xh_median"):
        a_value, b_value = summary_a.get(column), summary_b.get(column)
        out[f"{column}_ab"] = (a_value, b_value)
        out[f"{column}_delta"] = None if a_value is None or b_value is None else b_value - a_value
    # Distance from 1.0 — the direction that matters for a ratio whose ideal is
    # neither larger nor smaller but equal.
    gaps = []
    for summary in (summary_a, summary_b):
        median = summary.get("retrace_arc_ratio_median")
        gaps.append(None if median is None else abs(median - 1.0))
    out["retrace_arc_ratio_gap_ab"] = tuple(gaps)
    out["retrace_arc_ratio_gap_delta"] = None if None in gaps else gaps[1] - gaps[0]
    return out


# ---------------------------------------------------------------- the printing


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def print_rows(rows: Sequence[dict]) -> None:
    """One stable line per word — the parseable half of the report.

    Every scored row prints every column, zeros included: a parser must not have
    to infer a missing one (the wordbench/chainbench discipline).
    """
    for row in rows:
        if row.get("status") != STATUS_OK:
            print(f"word {row['id']:<15} {row.get('status', '?'):<8} ({row.get('detail') or 'no detail'})")
            continue
        print(
            f"word {row['id']:<15} dtw {_fmt(row['dtw_xh'])}  "
            f"aiou {_fmt(row['aiou'], 3)}  cham c>r {_fmt(row['chamfer_cand_ref_xh'], 3)} "
            f"r>c {_fmt(row['chamfer_ref_cand_xh'], 3)}  "
            f"marks {row['marks_matched']}/{row['marks_ref']}"
            f"{'+' + str(row['marks_spurious']) if row['marks_spurious'] else ''}  "
            f"cross {row['cross_matched']}/{row['cross_ref']}"
            f"{'+' + str(row['cross_spurious']) if row['cross_spurious'] else ''}  "
            f"retrace {row['retrace_matched']}/{row['retrace_ref']} r={_fmt(row['retrace_arc_ratio'], 2)}  "
            f"lift {row['lift_delta']:+d}"
            # The ductus target rides at the end of the line when the run could
            # compute it — appended, so older lines stay parseable unchanged.
            + (
                f"  soll c{row['soll_cross']}/z{row['soll_zones']}"
                if row.get("soll_cross") is not None and row.get("soll_zones") is not None
                else ""
            )
            + f"  {row['secs']:.1f}s"
        )


def print_block(summary: dict[str, Any], *, label: str = "", split: str = "") -> None:
    """The run's block — keys exactly as §14 names them, one per line."""
    print("---")
    print(f"candidate:       {label or '-'}")
    print(f"split:           {split or '-'}")
    print(f"words_scored:    {summary['scored']}")
    print(f"words_failed:    {summary['failed']}")
    print(f"words_skipped:   {summary['skipped']}")
    print(f"dtw_xh_median:   {_fmt(summary['dtw_xh_median'], 6)}")
    print(f"dtw_xh_p90:      {_fmt(summary['dtw_xh_p90'], 6)}")
    worst, worst_id = summary["dtw_xh_worst"]
    print(f"dtw_xh_worst:    {worst_id or '-'} {_fmt(worst, 6)}")
    print(f"aiou_median:     {_fmt(summary['aiou_median'], 4)}")
    print(f"chamfer_cand_ref_median: {_fmt(summary['chamfer_cand_ref_xh_median'])}")
    print(f"chamfer_ref_cand_median: {_fmt(summary['chamfer_ref_cand_xh_median'])}")
    print(f"retrace_arc_ratio_median: {_fmt(summary['retrace_arc_ratio_median'], 3)}")
    for column in _TOTAL_COLUMNS:
        print(f"{column}: {summary[column]}")
    print(f"lift_delta_total: {summary['lift_delta_total']}")
    print(f"dtw_reversed_better: {summary['dtw_reversed_better']}")
    print(f"dtw_max_absorption_max: {_fmt(summary['dtw_max_absorption_max'])}")
    print(f"marks_uncertain: {summary['marks_uncertain']}")
    excluded = summary.get("excluded") or {}
    print(f"excluded: {' '.join(f'{k}={v}' for k, v in sorted(excluded.items())) or 'none'}")


def print_comparison(result: dict[str, Any], *, against: str) -> None:
    """The paired block against an earlier `--json` report (deltas are b - a)."""
    print(f"--- compare vs {against} (Δ = this run - that one, negative = better) ---")
    print(f"paired_words:    {result['paired']}")
    print(f"dtw_delta_median: {_fmt(result['dtw_delta_median'], 6)}")
    print(f"dtw_delta_p90:   {_fmt(result['dtw_delta_p90'], 6)}")
    print(f"dtw_rel_median:  {_fmt(result['dtw_rel_median'], 4)}")
    sign = result["sign_test"]
    print(f"sign_test:       n={sign['n']} pos={sign['pos']} neg={sign['neg']} ties={sign['ties']} p={sign['p']}")
    for column in ("marks_missing", "cross_missing", "cross_spurious", "failed", "skipped", "dtw_reversed_better"):
        a_value, b_value = result[f"{column}_ab"]
        print(f"{column}: {a_value} -> {b_value}")
    for column in ("aiou_median", "chamfer_ref_cand_xh_median", "chamfer_cand_ref_xh_median"):
        a_value, b_value = result[f"{column}_ab"]
        print(f"{column}: {_fmt(a_value)} -> {_fmt(b_value)}  Δ {_fmt(result[f'{column}_delta'])}")
    gap_a, gap_b = result["retrace_arc_ratio_gap_ab"]
    print(
        f"retrace_arc_ratio_gap: {_fmt(gap_a, 3)} -> {_fmt(gap_b, 3)}  Δ {_fmt(result['retrace_arc_ratio_gap_delta'])}"
    )
    if result["unpaired"]:
        print(f"unpaired_words:  {','.join(result['unpaired'])}")
    for row in result["per_word"]:
        print(f"  {row['id']:<15} {row['a']:.4f} -> {row['b']:.4f}  Δ {row['delta']:+.4f}")


__all__ = [
    "MARKS_PER_KEY",
    "compare",
    "direction_audit",
    "expected_marks",
    "identity_gate",
    "print_block",
    "print_comparison",
    "print_rows",
    "score_word",
    "summarize",
]
