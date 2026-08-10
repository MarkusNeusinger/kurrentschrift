"""The pre-registered A/B for the letter neighbour-binding term.

Criteria, ladder and split are fixed in `qualitaetsmetrik.md` §11b and were
committed BEFORE this ran. This module only executes them; it does not choose
them, and it prints every pre-registered number whether it flatters the term or
not.

What it does per arm: re-run the harvest's own chain solves
(`tools.laufform.harvest._grid_fits` + `_chainable_runs` + `chain.fit_word_chain`)
at one `bind_weight`, and record one row per LETTER occurrence — the harvest's
own gate verdict, its residuals, and the pre-registered benefit measure.

The benefit measure is deliberately NOT `anchor_spike_ratio` (§11 correction 1:
it is nearly the statistic the term penalises, so any weight lowers it by
construction). It is the share of a letter's anchors whose RAW EDT exceeds
`INK_OFF_UNITS` **at the anchor's own position** — unsmoothed where the
objective reads the smoothed field, at a place the objective never evaluates,
and a threshold share rather than a quadratic sum. At the anchor because the
anchor is what gets STORED and runs through the per-anchor medians into the
Laufform the live system writes.

Everything is paired per occurrence: arms differ only in the weight, so the
same `(set, specimen, run, slot)` is the same letter on the same ink.

    uv run python -m tools.pairlab.bindab --set words --jobs 4 --out temp/bindab-dev
    uv run python -m tools.pairlab.bindab --set pairs --weights 0,<chosen> --out temp/bindab-conf

Measurement only: no DB, no API, no writes to `core/`, nothing that renders.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics as st
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from core.fit import bilinear
from tools.laufform.harvest import _chainable_runs, _connector_diag, _grid_fits, anchor_spike_ratio, letter_gate
from tools.pairlab.chain import fit_word_chain
from tools.pairlab.gradlab import stranded_anchors
from tools.wordlab.cases import iter_fixture_word_cases
from tools.wordlab.derive import derive_word


# Pre-registered in §11b. `CHAIN_OVERLAP_RADIUS_UNITS`' rationale — the repo's
# already-calibrated "still inside one drawn stroke" distance; beyond it the
# anchor is outside the ink.
INK_OFF_UNITS = 0.15
# The harvest's own acceptance threshold, so a row's gate here is the gate that
# decides whether the occurrence reaches `instances` in production.
RMSE_MAX = 2.2
# Run 2's ladder (§11c). Run 1's — 1e-4 · 1e-3 · 1e-2 — was taken by analogy to
# `core.fit.DEFAULT_SMOOTH_WEIGHT` and never switched the term on: at its top
# rung the weighted bind energy was 4.9e-6 against `e_geo` 2.2e-3, i.e. 450x
# smaller. Measured on BASELINE solves only (weight 0, so nothing about the
# effect leaks), `e_geo / e_bind` is 3.2 in the median (p10 1.5, p90 5.3), so
# these rungs put the binding at roughly 3 %, 10 %, 31 % and 100 % of the
# geometry term. Geometric spacing x3.16.
PRE_REGISTERED_LADDER = (0.0, 0.1, 0.32, 1.0, 3.2)


def off_ink_share(problem, params, a0: int, a1: int) -> tuple[float, int]:
    """Share (and count) of a letter's anchors sitting outside the ink.

    Read at the ANCHOR positions — `problem.to_pixels` returns the SAMPLE row,
    which is a different set of points (`vom-scan-zum-schreiben.md` Schritt 4).
    """
    free = problem.free_anchors(params)[a0:a1]
    px = problem.x_origin_px + free[:, 0] * problem.unit_px
    py = problem.baseline_y_px - free[:, 1] * problem.unit_px
    d = bilinear(problem.dist_raw, px, py) / problem.unit_px
    n_off = int((d > INK_OFF_UNITS).sum())
    return (n_off / len(d) if len(d) else 0.0), n_off


def _rows_for_arm(case, which: str, weight: float, result, grids) -> list[dict]:
    """One row per letter occurrence of one case at one weight."""
    rows: list[dict] = []
    xh = result.xh_px
    registration = {
        "tx": result.registration["tx"],
        "ty": result.registration["ty"],
        "baseline_row": result.baseline_row,
    }
    for run_slots in _chainable_runs(case, grids):
        fit = fit_word_chain(
            case,
            run_slots,
            result=result,
            windows_px={s: grids[s]["window"] for s in run_slots},
            keep_solve=True,
            bind_weight=weight,
        )
        if fit is None:
            continue
        problem, params = fit.problem, fit.params
        conn_reasons, _ = _connector_diag(fit, xh, registration)
        letters = [seg for seg in fit.segments if seg.kind == "letter"]
        specs = [s for s in problem.specs if s.kind == "letter"]
        for n, (seg, spec) in enumerate(zip(letters, specs, strict=True)):
            slot_index = fit.slots[n]
            a0, a1 = seg.anchor_slice
            chart = case.templates.get(seg.key) or {}
            n_chart = len(chart.get("anchors") or [])
            fitted = np.asarray(seg.fitted_anchors, dtype=float) if seg.fitted_anchors is not None else np.zeros((0, 2))
            spike = anchor_spike_ratio(fitted, (chart.get("trace_meta") or {}).get("stroke_starts") or [0])
            gate = letter_gate(
                converged_local=bool(seg.converged_local),
                geo_rmse_px=float(seg.geo_rmse_px),
                rmse_max=RMSE_MAX,
                at_bound=bool(fit.slot_at_bound.get(slot_index, False)),
                anchors_ok=len(fitted) == n_chart and n_chart > 0,
                spike_ratio=spike,
                connector_reasons=[conn_reasons.get(n - 1) if n else None, conn_reasons.get(n)],
            )
            share, n_off = off_ink_share(problem, params, a0, a1)
            local = problem.anchors_free[a0:a1] + problem.unpack(params)[3][a0:a1]
            rows.append(
                {
                    "set": which,
                    "weight": weight,
                    "specimen": case.id,
                    "run": "-".join(str(s) for s in fit.slots),
                    "slot": slot_index,
                    "key": seg.key,
                    "gate": gate,
                    "accepted": int(gate == "ok"),
                    "converged_local": int(bool(seg.converged_local)),
                    "geo_rmse_px": float(seg.geo_rmse_px),
                    "cov_rmse_local_px": float(seg.cov_rmse_local_px),
                    "off_ink_share": share,
                    "n_off_ink": n_off,
                    "n_anchors": a1 - a0,
                    "n_stranded": len(stranded_anchors(local, spec.stroke_starts)),
                    # Reported, never a criterion — see §11 correction 1.
                    "anchor_spike_ratio": float(spike),
                    "iterations": int(fit.fit_meta.get("iterations", 0)),
                    "hit_iteration_cap": int(bool(fit.fit_meta.get("hit_iteration_cap", False))),
                }
            )
    return rows


def case_arms(job: tuple[str, object, tuple[float, ...]]) -> list[dict]:
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
    print(f"  {which}/{case.id:<24} {len(rows):>4} rows over {len(weights)} arms", flush=True)
    return rows


# ------------------------------------------------------------------ statistics


def _paired(rows: list[dict], base: float, weight: float, field: str) -> list[tuple[float, float]]:
    """`(baseline, arm)` per occurrence — the pairing §11 correction 3 demands."""
    key = ("set", "specimen", "run", "slot")
    a = {tuple(r[k] for k in key): r for r in rows if r["weight"] == base}
    b = {tuple(r[k] for k in key): r for r in rows if r["weight"] == weight}
    return [(a[k][field], b[k][field]) for k in sorted(a.keys() & b.keys())]


def _rel_change(pairs: list[tuple[float, float]]) -> dict:
    """Median and p90 of the per-occurrence RELATIVE change, plus how many worsened.

    Relative per occurrence rather than a ratio of medians: a ratio of
    aggregates hides that a few occurrences carry the whole cost.
    """
    rel = [(y - x) / x for x, y in pairs if x > 0.0]
    if not rel:
        return {"n": 0}
    rel.sort()
    return {
        "n": len(rel),
        "median_pct": 100.0 * st.median(rel),
        "p90_pct": 100.0 * rel[min(len(rel) - 1, int(0.9 * len(rel)))],
        "worse": sum(1 for v in rel if v > 1e-12),
        "better": sum(1 for v in rel if v < -1e-12),
    }


def mcnemar(pairs: list[tuple[float, float]]) -> dict:
    """Exact two-sided McNemar over the discordant gate flips.

    §11 correction 3: „under 23 rejections" is a coarse integer where 23 → 22
    is noise. What carries information is which occurrences FLIPPED, and in
    which direction.
    """
    gained = sum(1 for x, y in pairs if not x and y)  # baseline rejected, arm accepted
    lost = sum(1 for x, y in pairs if x and not y)
    n = gained + lost
    if n == 0:
        return {"gained": 0, "lost": 0, "p": 1.0}
    # Exact binomial, two-sided, under p = 0.5.
    k = min(gained, lost)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2.0**n)
    return {"gained": gained, "lost": lost, "p": min(1.0, 2.0 * tail)}


def evaluate(rows: list[dict], base: float, weight: float) -> dict:
    """Every pre-registered number for one arm against the baseline."""
    off = _paired(rows, base, weight, "off_ink_share")
    x = [a for a, _ in off]
    y = [b for _, b in off]
    off_base = float(np.mean(x)) if x else 0.0
    off_arm = float(np.mean(y)) if y else 0.0
    gate = [(bool(a), bool(b)) for a, b in _paired(rows, base, weight, "accepted")]
    geo = _rel_change(_paired(rows, base, weight, "geo_rmse_px"))
    cov = _rel_change(_paired(rows, base, weight, "cov_rmse_local_px"))
    flips = mcnemar(gate)
    accepted_base = sum(1 for a, _ in gate if a)
    accepted_arm = sum(1 for _, b in gate if b)
    benefit_pct = 100.0 * (off_arm - off_base) / off_base if off_base > 0.0 else 0.0
    it = _paired(rows, base, weight, "iterations")
    return {
        "weight": weight,
        "n_occurrences": len(off),
        # benefit (pre-registered: relative fall of >= 25 %)
        "off_ink_share_base": off_base,
        "off_ink_share_arm": off_arm,
        "off_ink_rel_pct": benefit_pct,
        "benefit_ok": benefit_pct <= -25.0,
        # costs
        "geo_rmse": geo,
        "cov_rmse_local": cov,
        "accepted_base": accepted_base,
        "accepted_arm": accepted_arm,
        "gate_flips": flips,
        "cost_ok": (
            geo.get("median_pct", 0.0) <= 5.0
            and geo.get("p90_pct", 0.0) <= 10.0
            and cov.get("median_pct", 0.0) <= 2.0
            and accepted_arm >= accepted_base
            and not (flips["lost"] > flips["gained"] and flips["p"] < 0.05)
        ),
        # not-just-different-arithmetic (correction 4)
        "iterations_median_base": st.median([a for a, _ in it]) if it else 0,
        "iterations_median_arm": st.median([b for _, b in it]) if it else 0,
        "capped_base": sum(r["hit_iteration_cap"] for r in rows if r["weight"] == base),
        "capped_arm": sum(r["hit_iteration_cap"] for r in rows if r["weight"] == weight),
        # reported, never a criterion
        "spike_ratio_median_base": st.median([r["anchor_spike_ratio"] for r in rows if r["weight"] == base] or [0]),
        "spike_ratio_median_arm": st.median([r["anchor_spike_ratio"] for r in rows if r["weight"] == weight] or [0]),
        "stranded_base": sum(r["n_stranded"] for r in rows if r["weight"] == base),
        "stranded_arm": sum(r["n_stranded"] for r in rows if r["weight"] == weight),
    }


def print_report(evals: list[dict]) -> None:
    print()
    print("PRE-REGISTERED (§11b) — benefit: off-ink anchor share must fall >= 25 % relative")
    print(f"{'weight':>9} {'n':>5} {'off-ink base':>13} {'arm':>9} {'rel':>9}  verdict")
    for e in evals:
        print(
            f"{e['weight']:>9.0e} {e['n_occurrences']:>5} {e['off_ink_share_base']:>13.4f} "
            f"{e['off_ink_share_arm']:>9.4f} {e['off_ink_rel_pct']:>8.1f}%  "
            f"{'PASS' if e['benefit_ok'] else 'fail'}"
        )
    print()
    print("costs — paired per occurrence")
    print(f"{'weight':>9} {'geo med':>9} {'geo p90':>9} {'cov med':>9} {'acc':>11} {'flips':>13} {'p':>7}  verdict")
    for e in evals:
        g, c, f = e["geo_rmse"], e["cov_rmse_local"], e["gate_flips"]
        print(
            f"{e['weight']:>9.0e} {g.get('median_pct', 0):>8.2f}% {g.get('p90_pct', 0):>8.2f}% "
            f"{c.get('median_pct', 0):>8.2f}% {e['accepted_base']:>4}->{e['accepted_arm']:<5} "
            f"{'+' + str(f['gained']) + '/-' + str(f['lost']):>13} {f['p']:>7.3f}  "
            f"{'PASS' if e['cost_ok'] else 'fail'}"
        )
    print()
    print("not-a-conditioning-artefact (correction 4) + reported-only figures")
    print(f"{'weight':>9} {'nit base':>9} {'nit arm':>9} {'capped':>10} {'spike med':>18} {'stranded':>14}")
    for e in evals:
        print(
            f"{e['weight']:>9.0e} {e['iterations_median_base']:>9.0f} {e['iterations_median_arm']:>9.0f} "
            f"{str(e['capped_base']) + '->' + str(e['capped_arm']):>10} "
            f"{e['spike_ratio_median_base']:>8.2f}->{e['spike_ratio_median_arm']:<9.2f} "
            f"{str(e['stranded_base']) + '->' + str(e['stranded_arm']):>14}"
        )
    winners = [e for e in evals if e["weight"] > 0 and e["benefit_ok"] and e["cost_ok"]]
    print()
    if winners:
        w = min(winners, key=lambda e: e["weight"])
        print(f"SMALLEST EFFECTIVE WEIGHT on this set: {w['weight']:.0e}")
    else:
        print("NO weight of the pre-registered ladder passes both criteria on this set.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--set", dest="which", default="words", choices=["words", "pairs"])
    parser.add_argument("--style", default="suetterlin")
    parser.add_argument(
        "--weights",
        default=",".join(f"{w:g}" for w in PRE_REGISTERED_LADDER),
        help="comma-separated; the pre-registered ladder is the default",
    )
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--out", type=Path, default=Path("temp/bindab"))
    args = parser.parse_args()

    weights = tuple(float(w) for w in args.weights.split(","))
    if weights[0] != 0.0:
        raise SystemExit("the first weight must be 0.0 — the baseline arm is re-fitted in the SAME run")
    cases = list(iter_fixture_word_cases(which=args.which, style=args.style))
    if args.max_cases:
        cases = cases[: args.max_cases]
    jobs = [(args.which, c, weights) for c in cases]
    print(f"{len(cases)} cases x {len(weights)} arms, set={args.which}")

    if args.jobs > 1:
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            produced = list(pool.map(case_arms, jobs))
    else:
        produced = [case_arms(j) for j in jobs]
    rows = [r for batch in produced for r in batch]
    if not rows:
        raise SystemExit("no occurrences measured — are the frozen fixtures present?")

    evals = [evaluate(rows, 0.0, w) for w in weights]
    print_report(evals)

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "occurrences.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    (args.out / "evaluation.json").write_text(json.dumps({"set": args.which, "arms": evals}, indent=2))
    print(f"\nwrote {args.out}/occurrences.csv ({len(rows)} rows) and evaluation.json")


if __name__ == "__main__":
    main()
