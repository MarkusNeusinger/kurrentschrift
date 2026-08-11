"""Probe for the crossing-landmark correspondence term — calibration + effect.

This is NOT the pre-registered A/B. It answers the two questions that have to be
answered BEFORE one is written, on the one glyph whose landmark drift is measured
(`qualitaetsmetrik.md` §13a, the Sütterlin `d`):

1. **Scale** (`--calibrate`). At the BASELINE optimum — weight 0, so nothing
   about the effect leaks — what is `e_geo / e_landmark`? That ratio is the
   weight at which the correspondence weighs as much as the geometry term. §11c
   is why this step exists at all: the neighbour-binding ladder was chosen by
   analogy to another fit path's constant, put the term at 0.2 % of this
   objective's energy scale, and produced an EMPTY experiment that measured
   nothing about the hypothesis.
2. **Effect** (the default run). At weight 0 and at the weights that follow from
   step 1, where does the FITTED crossing sit, how much of the measured 0.218 xh
   gap on a joined `d` does each weight close, and what does it cost in
   `geo_rmse_px`, `cov_rmse_local_px` and convergence?

Deliberately no default weight is proposed here, and no verdict is drawn: the
development set is 14 occurrences of ONE glyph, the word-final arm is 4
occurrences of a single word („und"), and choosing a weight off the same set that
measured the effect is what a pre-registered A/B on the untouched confirmation
set exists to prevent.

    uv run python -m tools.pairlab.landmarklab --calibrate --jobs 4
    uv run python -m tools.pairlab.landmarklab --weights 0,<w1>,<w2>,<w3> --jobs 4

Measurement only: no DB, no API, no writes to `core/`, nothing that renders.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics as st
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from tools.laufform.harvest import _chainable_runs, _connector_diag, _grid_fits, anchor_spike_ratio, letter_gate
from tools.pairlab.chain import _ChainProblem, _slots_join, fit_word_chain
from tools.wordlab.cases import WordCase, iter_fixture_word_cases
from tools.wordlab.derive import WordDeriveResult, derive_word


# The glyph §13a measured. Its crossing lies on the AUSLAUF path (anchor 59/110),
# which is where the transition dependence shows up at all — at `a`, `l`, `r`, `h`
# the crossing is NOT transition-dependent (p = 0.67–0.75), so a probe on those
# would measure a term against a null effect.
PROBE_KEY = "d"
# The harvest's own acceptance threshold, so a row's gate here is the gate that
# decides whether the occurrence reaches `instances` in production.
RMSE_MAX = 2.2


def _kept_landmarks(problem: _ChainProblem) -> list[tuple[int | None, dict]]:
    """`(row index into landmark_op | None, report entry)` for every DETECTED landmark.

    The row index is None for a dropped correspondence — such a landmark is still
    a measurable point of the fitted geometry, it just has no ink counterpart to
    be pulled towards, and the probe has to be able to report its position either
    way.
    """
    out: list[tuple[int | None, dict]] = []
    row = 0
    for entry in problem.landmark_report:
        if entry["reason"] == "ok":
            out.append((row, entry))
            row += 1
        else:
            out.append((None, entry))
    return out


def fitted_crossing(problem: _ChainProblem, entry: dict, params: np.ndarray) -> np.ndarray:
    """The landmark's fitted position (template units) — the objective's own estimate.

    Rebuilt from the FROZEN chord indices and parameters rather than re-detected,
    for the same reason the term is linearised that way: re-detecting at the
    optimum would answer a different question (where does the fitted polyline
    cross itself NOW) than the term optimises (where does the frozen
    correspondence sit).
    """
    ap = problem.plan_anchors(params)
    p0, _ = problem.plan_slices[int(entry["segment"])]
    i, j = p0 + int(entry["seg_i"]), p0 + int(entry["seg_j"])
    t_i, t_j = float(entry["t_i"]), float(entry["t_j"])
    return 0.5 * (ap[i] + t_i * (ap[i + 1] - ap[i])) + 0.5 * (ap[j] + t_j * (ap[j + 1] - ap[j]))


def _rows_for_arm(
    case: WordCase, which: str, weight: float, result: WordDeriveResult, grids: dict[int, dict]
) -> list[dict]:
    """One row per `PROBE_KEY` landmark of one case at one weight."""
    rows: list[dict] = []
    xh = result.xh_px
    registration = {
        "tx": result.registration["tx"],
        "ty": result.registration["ty"],
        "baseline_row": result.baseline_row,
    }
    for run_slots in _chainable_runs(case, grids):
        if not any(case.slots[s].key == PROBE_KEY for s in run_slots):
            continue
        fit = fit_word_chain(
            case,
            run_slots,
            result=result,
            windows_px={s: grids[s]["window"] for s in run_slots},
            keep_solve=True,
            landmark_weight=weight,
        )
        if fit is None:
            continue
        problem, params = fit.problem, fit.params
        terms = problem.energy_terms(params)
        conn_reasons, _ = _connector_diag(fit, xh, registration)
        letters = [seg for seg in fit.segments if seg.kind == "letter"]
        for n, seg in enumerate(letters):
            if seg.key != PROBE_KEY:
                continue
            slot_index = fit.slots[n]
            joined = slot_index + 1 < len(case.slots) and _slots_join(
                case.slots[slot_index], case.slots[slot_index + 1]
            )
            chart = case.templates.get(seg.key) or {}
            n_chart = len(chart.get("anchors") or [])
            fitted = np.asarray(seg.fitted_anchors, dtype=float) if seg.fitted_anchors is not None else np.zeros((0, 2))
            gate = letter_gate(
                converged_local=bool(seg.converged_local),
                geo_rmse_px=float(seg.geo_rmse_px),
                rmse_max=RMSE_MAX,
                at_bound=bool(fit.slot_at_bound.get(slot_index, False)),
                anchors_ok=len(fitted) == n_chart and n_chart > 0,
                spike_ratio=anchor_spike_ratio(fitted, (chart.get("trace_meta") or {}).get("stroke_starts") or [0]),
                connector_reasons=[conn_reasons.get(n - 1) if n else None, conn_reasons.get(n)],
            )
            segment_index = next(
                i for i, spec in enumerate(problem.specs) if spec.kind == "letter" and spec.slot_index == slot_index
            )
            for row_ix, entry in _kept_landmarks(problem):
                if int(entry["segment"]) != segment_index:
                    continue
                p_fit = fitted_crossing(problem, entry, params)
                target = problem.landmark_targets[row_ix] if row_ix is not None else None
                rows.append(
                    {
                        "set": which,
                        "weight": weight,
                        "specimen": case.id,
                        "run": "-".join(str(s) for s in fit.slots),
                        "slot": slot_index,
                        "key": seg.key,
                        "joined": int(bool(joined)),
                        "landmark": f"{entry['seg_i']}-{entry['seg_j']}",
                        "assigned": entry["reason"],
                        # y in the letter-local frame of §13a: baseline 0, y up,
                        # 1 unit = x-height. x is composed-frame and only carried
                        # so a row can be located, never pooled.
                        "y_fit": float(p_fit[1]),
                        "x_fit": float(p_fit[0]),
                        "y_target": None if target is None else float(target[1]),
                        "gap_y": None if target is None else float(p_fit[1] - target[1]),
                        "dist_xy": None if target is None else float(np.hypot(*(p_fit - target))),
                        # The term's row weights sum to 1, so a rigid TRANSLATION
                        # of the letter moves the crossing one-for-one and is the
                        # cheapest way to satisfy it. These two say whether a
                        # weight moved the STRUCTURE or just slid the letter —
                        # without them the effect column could not be read
                        # honestly.
                        "slot_dy": float(fit.slot_shift_units.get(slot_index, (0.0, 0.0))[1]),
                        "slot_dx": float(fit.slot_shift_units.get(slot_index, (0.0, 0.0))[0]),
                        "global_dy": float(fit.global_shift_units[1]),
                        "geo_rmse_px": float(seg.geo_rmse_px),
                        "cov_rmse_local_px": float(seg.cov_rmse_local_px),
                        "converged_local": int(bool(seg.converged_local)),
                        "gate": gate,
                        "accepted": int(gate == "ok"),
                        "e_geo": float(terms["e_geo"]),
                        "e_landmark": float(terms["e_landmark"]),
                        "n_landmarks": int(problem.landmark_op.shape[0]),
                        "n_landmarks_dropped": sum(1 for e in problem.landmark_report if e["reason"] != "ok"),
                        # …and WHY they were dropped. A term that quietly assigns
                        # nothing is inert for a reason that has to be readable
                        # off the run rather than reconstructed afterwards.
                        "dropped_ambiguous": sum(1 for e in problem.landmark_report if e["reason"] == "ambiguous"),
                        "dropped_no_candidate": sum(
                            1 for e in problem.landmark_report if e["reason"] == "no_candidate"
                        ),
                        "iterations": int(fit.fit_meta.get("iterations", 0)),
                        "hit_iteration_cap": int(bool(fit.fit_meta.get("hit_iteration_cap", False))),
                        "seconds": float(fit.fit_meta.get("seconds", 0.0)),
                    }
                )
    return rows


def case_arms(job: tuple[str, WordCase, tuple[float, ...]]) -> list[dict]:
    """Every arm of ONE case — composed once, solved once per weight."""
    which, case, weights = job
    try:
        result = derive_word(case)
    except Exception as exc:  # noqa: BLE001 — one bad case must not end the run
        print(f"  skip {which}/{case.id}: derive failed ({exc})", flush=True)
        return []
    grids = _grid_fits(case, result)
    rows: list[dict] = []
    for weight in weights:
        rows.extend(_rows_for_arm(case, which, weight, result, grids))
    print(f"  {which}/{case.id:<24} {len(rows):>3} rows over {len(weights)} arms", flush=True)
    return rows


# ------------------------------------------------------------------ statistics


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, int(round(q * (len(ordered) - 1)))))]


def calibration(rows: list[dict]) -> dict:
    """`e_geo / e_landmark` over the BASELINE solves — the scale of the term.

    One entry per distinct solve (a run may carry several landmarks; the energies
    are properties of the solve, not of a landmark), read at weight 0 only.
    """
    seen: dict[tuple[str, str], tuple[float, float]] = {}
    for r in rows:
        if r["weight"] != 0.0 or r["e_landmark"] <= 0.0:
            continue
        seen[(r["specimen"], r["run"])] = (r["e_geo"], r["e_landmark"])
    ratios = [geo / lm for geo, lm in seen.values()]
    if not ratios:
        return {"n": 0}
    return {
        "n": len(ratios),
        "e_geo_median": st.median(geo for geo, _ in seen.values()),
        "e_landmark_median": st.median(lm for _, lm in seen.values()),
        "ratio_median": st.median(ratios),
        "ratio_p10": _quantile(ratios, 0.10),
        "ratio_p90": _quantile(ratios, 0.90),
    }


def _pool(rows: list[dict], weight: float, joined: int, field: str) -> list[float]:
    return [r[field] for r in rows if r["weight"] == weight and r["joined"] == joined and r[field] is not None]


def _paired(rows: list[dict], base: float, weight: float, field: str) -> list[tuple[float, float]]:
    key = ("set", "specimen", "run", "slot", "landmark")
    a = {tuple(r[k] for k in key): r for r in rows if r["weight"] == base}
    b = {tuple(r[k] for k in key): r for r in rows if r["weight"] == weight}
    return [(a[k][field], b[k][field]) for k in sorted(a.keys() & b.keys()) if a[k][field] is not None]


def arm_summary(rows: list[dict], base: float, weight: float) -> dict:
    """Everything one arm has to state — pooled by joined vs. word-final."""
    out: dict = {"weight": weight}
    for label, joined in (("joined", 1), ("final", 0)):
        gaps = _pool(rows, weight, joined, "gap_y")
        ys = _pool(rows, weight, joined, "y_fit")
        tgt = _pool(rows, weight, joined, "y_target")
        out[label] = {
            "n": len(gaps),
            "y_fit_median": st.median(ys) if ys else None,
            "y_target_median": st.median(tgt) if tgt else None,
            "gap_median": st.median(gaps) if gaps else None,
            "gap_abs_median": st.median([abs(g) for g in gaps]) if gaps else None,
        }
    # Did the crossing move because the STRUCTURE moved, or because the letter
    # slid? The term's rows sum to 1, so a translation satisfies it one-for-one —
    # the difference has to be reported, not assumed.
    out["move"] = {
        name: st.median([y - x for x, y in _paired(rows, base, weight, field)])
        if _paired(rows, base, weight, field)
        else None
        for name, field in (("d_y_fit", "y_fit"), ("d_slot_dy", "slot_dy"), ("d_global_dy", "global_dy"))
    }
    geo = _paired(rows, base, weight, "geo_rmse_px")
    cov = _paired(rows, base, weight, "cov_rmse_local_px")
    conv = _paired(rows, base, weight, "converged_local")
    acc = _paired(rows, base, weight, "accepted")
    out["cost"] = {
        "geo_rel_pct": 100.0 * st.median([(y - x) / x for x, y in geo if x > 0]) if geo else None,
        "cov_rel_pct": 100.0 * st.median([(y - x) / x for x, y in cov if x > 0]) if cov else None,
        "geo_worse": sum(1 for x, y in geo if y > x + 1e-12),
        "converged_base": sum(1 for x, _ in conv if x),
        "converged_arm": sum(1 for _, y in conv if y),
        "accepted_base": sum(1 for x, _ in acc if x),
        "accepted_arm": sum(1 for _, y in acc if y),
        "n_paired": len(geo),
    }
    return out


def print_report(rows: list[dict], weights: tuple[float, ...], calib: dict) -> None:
    print()
    print("CALIBRATION — baseline (weight 0) solves only, so nothing about the effect leaks")
    if calib.get("n"):
        print(
            f"  solves {calib['n']}   e_geo median {calib['e_geo_median']:.3e}   "
            f"e_landmark median {calib['e_landmark_median']:.3e}"
        )
        print(
            f"  e_geo / e_landmark:  median {calib['ratio_median']:.3g}   "
            f"p10 {calib['ratio_p10']:.3g}   p90 {calib['ratio_p90']:.3g}"
        )
        print(f"  => weight putting the landmark term ON A PAR with geometry: {calib['ratio_median']:.3g}")
    else:
        print("  no baseline solve carried an assigned landmark — nothing to calibrate")

    print()
    print("PER OCCURRENCE — fitted crossing height (letter-local, y up from baseline, 1 unit = xh)")
    header = f"{'specimen':<12}{'slot':>5}{'j':>3}{'ink':>8}" + "".join(f"{w:>10.4g}" for w in weights)
    print(header)
    key = ("specimen", "slot", "landmark")
    ids = sorted({tuple(r[k] for k in key) for r in rows})
    for ident in ids:
        by_w = {r["weight"]: r for r in rows if tuple(r[k] for k in key) == ident}
        any_row = next(iter(by_w.values()))
        tgt = any_row["y_target"]
        line = f"{ident[0]:<12}{ident[1]:>5}{any_row['joined']:>3}" + (
            f"{tgt:>8.3f}" if tgt is not None else f"{'--':>8}"
        )
        for w in weights:
            r = by_w.get(w)
            line += f"{r['y_fit']:>10.3f}" if r else f"{'--':>10}"
        print(line)

    print()
    print("POOLED — how much of the joined-d gap each weight closes")
    print(f"{'weight':>10} {'arm':>7} {'n':>4} {'y_fit':>8} {'y_ink':>8} {'gap':>8} {'closed':>8}")
    summaries = [arm_summary(rows, weights[0], w) for w in weights]
    base_gap = {a: summaries[0][a]["gap_median"] for a in ("joined", "final")}
    for s in summaries:
        for arm in ("joined", "final"):
            d = s[arm]
            if not d["n"]:
                continue
            closed = ""
            if base_gap[arm] not in (None, 0.0) and d["gap_median"] is not None:
                closed = f"{100.0 * (1.0 - d['gap_median'] / base_gap[arm]):>7.1f}%"
            print(
                f"{s['weight']:>10.4g} {arm:>7} {d['n']:>4} {d['y_fit_median']:>8.3f} "
                f"{d['y_target_median']:>8.3f} {d['gap_median']:>8.3f} {closed:>8}"
            )

    print()
    print("COSTS — paired per occurrence against weight 0")
    print(
        f"{'weight':>10} {'geo med':>9} {'cov med':>9} {'geo worse':>10} {'conv':>9} {'accepted':>10} {'iter med':>9}"
    )
    for s in summaries:
        c = s["cost"]
        it = _paired(rows, weights[0], s["weight"], "iterations")
        if s["weight"] == weights[0]:
            print(
                f"{s['weight']:>10.4g} {'--':>9} {'--':>9} {'--':>10} "
                f"{c['converged_base']:>9} {c['accepted_base']:>10} "
                f"{st.median([x for x, _ in it]) if it else 0:>9.0f}"
            )
            continue
        print(
            f"{s['weight']:>10.4g} {c['geo_rel_pct'] or 0.0:>8.2f}% {c['cov_rel_pct'] or 0.0:>8.2f}% "
            f"{str(c['geo_worse']) + '/' + str(c['n_paired']):>10} "
            f"{str(c['converged_base']) + '->' + str(c['converged_arm']):>9} "
            f"{str(c['accepted_base']) + '->' + str(c['accepted_arm']):>10} "
            f"{st.median([y for _, y in it]) if it else 0:>9.0f}"
        )
    print()
    print("STRUCTURE OR SLIDE — median change vs. weight 0 (a translation satisfies the term too)")
    print(f"{'weight':>10} {'d y_fit':>9} {'d slot_dy':>11} {'d global_dy':>12}")
    for s in summaries[1:]:
        m = s["move"]
        print(
            f"{s['weight']:>10.4g} {m['d_y_fit'] or 0.0:>9.3f} {m['d_slot_dy'] or 0.0:>11.3f} "
            f"{m['d_global_dy'] or 0.0:>12.3f}"
        )

    print()
    print("A PROBE, NOT THE PRE-REGISTERED A/B: one glyph, 14 occurrences, the word-final")
    print("arm is 4 occurrences of one word. No default weight follows from these numbers.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--set", dest="which", default="words", choices=["words", "pairs"])
    parser.add_argument("--style", default="suetterlin")
    parser.add_argument("--weights", default="0", help="comma-separated; the first must be 0 (the baseline arm)")
    parser.add_argument("--calibrate", action="store_true", help="weight 0 only — report the energy-scale ratio")
    parser.add_argument("--only", default="", help="comma-separated case ids; default = every case containing a `d`")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--out", type=Path, default=Path("temp/landmarklab"))
    args = parser.parse_args()

    weights = (0.0,) if args.calibrate else tuple(float(w) for w in args.weights.split(","))
    if weights[0] != 0.0:
        raise SystemExit("the first weight must be 0.0 — the baseline arm is re-fitted in the SAME run")
    only = [s for s in args.only.split(",") if s] or None
    cases = [
        c
        for c in iter_fixture_word_cases(which=args.which, style=args.style, only=only)
        if any(slot.key == PROBE_KEY for slot in c.slots)
    ]
    print(f"{len(cases)} cases with a `{PROBE_KEY}` x {len(weights)} arms, set={args.which}")
    print("  " + ", ".join(c.id for c in cases))

    jobs = [(args.which, c, weights) for c in cases]
    if args.jobs > 1:
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            produced = list(pool.map(case_arms, jobs))
    else:
        produced = [case_arms(j) for j in jobs]
    rows = [r for batch in produced for r in batch]
    if not rows:
        raise SystemExit("no landmark measured — are the frozen fixtures present?")

    calib = calibration(rows)
    print_report(rows, weights, calib)

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "landmarks.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    (args.out / "evaluation.json").write_text(
        json.dumps(
            {
                "set": args.which,
                "weights": list(weights),
                "calibration": calib,
                "arms": [arm_summary(rows, weights[0], w) for w in weights],
            },
            indent=2,
        )
    )
    print(f"\nwrote {args.out}/landmarks.csv ({len(rows)} rows) and evaluation.json")


if __name__ == "__main__":
    main()
