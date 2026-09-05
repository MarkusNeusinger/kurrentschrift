"""Per-term, per-anchor gradient decomposition of the chain fit at its optimum.

The step `qualitaetsmetrik.md` §11 puts BEFORE any new term is built. The
stranded anchor — one anchor of a fitted letter standing in blank paper while
its neighbours sit on the ink — is a stationary point of the chain objective.
A stationary point with a live field force means **some other term balances
it**, and until that term is named, a new one is a guess.

What this module measures, per solve, at the argmin the harvest actually used:

* **The force of every term on every free anchor.** Weighted exactly as the
  objective weighs it, folded through the objective's own chain rule, and
  checked: the seven terms must re-add to the gradient L-BFGS-B followed
  (`chain.gradient_decomposition`). A decomposition that does not reproduce
  the gradient describes a different problem.
* **The field where the objective actually reads it.** `d` at the SAMPLES
  between the stranded anchor's two neighbours — never at the anchor itself.
  The anchor-site measurement of §11 („|∇d| median 0.898, 0 of 49 on a ridge")
  quantifies a force the optimiser cannot feel, because no anchor is ever
  queried (`vom-scan-zum-schreiben.md` Schritt 4). This is the same reading at
  the place the energy is summed.
* **A control population.** Every OTHER letter anchor of the same solves. „The
  reg term holds it" means nothing until it is clear what the reg term does at
  an anchor that behaves.

Measurement only: no DB, no API, no writes to `core/`, nothing that renders.
The solves are the harvest's own (`tools.laufform.harvest._grid_fits` +
`_chainable_runs` + `chain.fit_word_chain`), so the optimum inspected here is
the optimum the 245 stored occurrences came from.

    uv run python -m tools.pairlab.gradlab --set all --out temp/gradlab
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from tools.laufform.harvest import _chainable_runs, _grid_fits

# The detector lives in `tools.pairlab.anchors` so the harvest's repair, the
# A/B and this diagnosis can never drift apart; re-exported here because this
# module is where its consumers historically found it.
from tools.pairlab.anchors import MIN_STROKE_STEPS, STRANDED_STEP_RATIO, stranded_anchors  # noqa: E402  (re-export)
from tools.pairlab.chain import (
    GRADIENT_TERMS,
    _bilinear_with_grad,
    _ChainProblem,
    fit_word_chain,
    gradient_decomposition,
    sample_slice_of_anchor,
)
from tools.wordbench.roots import add_expect_root_argument, announce_roots
from tools.wordlab.cases import DEFAULT_FIXTURES_DIR, _root_for, iter_fixture_word_cases
from tools.wordlab.derive import derive_word


__all__ = ["MIN_STROKE_STEPS", "STRANDED_STEP_RATIO", "stranded_anchors"]


def field_at_samples(problem: _ChainProblem, params: np.ndarray | None, lo: int, hi: int) -> dict[str, float | int]:
    """`d` and `|grad d|` at the samples the objective reads for one anchor.

    The smoothed field, because that is the one in the energy; the raw EDT
    alongside, because that is the honest distance to ink.
    """
    if hi <= lo:
        return {"n_samples": 0}
    px, py = problem.to_pixels(params)
    px, py = px[lo:hi], py[lo:hi]
    d, dx, dy = _bilinear_with_grad(problem.dist_smooth, px, py)
    d_raw, _, _ = _bilinear_with_grad(problem.dist_raw, px, py)
    grad_norm = np.hypot(dx, dy)
    return {
        "n_samples": int(hi - lo),
        "d_smooth_mean_px": float(np.mean(d)),
        "d_smooth_max_px": float(np.max(d)),
        "d_raw_mean_px": float(np.mean(d_raw)),
        "d_raw_max_px": float(np.max(d_raw)),
        "grad_d_mean": float(np.mean(grad_norm)),
        "grad_d_max": float(np.max(grad_norm)),
    }


def _rows_for_fit(case, fit, *, which: str) -> tuple[list[dict], float]:
    """Every LETTER anchor of one solve, stranded flag and all forces attached."""
    problem, params = fit.problem, fit.params
    report = gradient_decomposition(problem, params)  # raises if the split drifts
    per_anchor = report["per_anchor"]
    _, _, _, deltas = problem.unpack(params)
    unit = float(problem.unit_px)

    rows: list[dict] = []
    for seg, spec in zip(fit.segments, problem.specs, strict=True):
        if seg.kind != "letter":
            continue
        a0, a1 = seg.anchor_slice
        local = problem.anchors_free[a0:a1] + deltas[a0:a1]
        marks = stranded_anchors(local, spec.stroke_starts)
        neigh = np.hypot(*deltas[a0:a1].T)
        for i in range(a1 - a0):
            free_i = a0 + i
            around = [j for j in (i - 1, i + 1) if 0 <= j < a1 - a0]
            row = {
                "set": which,
                "specimen": case.id,
                "word": case.word,
                "run": "-".join(str(s) for s in fit.slots),
                "slot": seg.slot_index,
                "key": seg.key,
                "anchor": i,
                "free_anchor": free_i,
                "stranded": int(i in marks),
                "step_ratio_prev": round(marks[i][0], 3) if i in marks else "",
                "step_ratio_next": round(marks[i][1], 3) if i in marks else "",
                "delta_units": round(float(neigh[i]), 5),
                "delta_neighbours_units": round(float(np.mean(neigh[around])), 5) if around else "",
                "converged_local": int(bool(seg.converged_local)),
                "geo_rmse_px": round(float(seg.geo_rmse_px), 3),
            }
            # Forces in TEMPLATE units per unit of energy — the parameter the
            # optimiser moves is a delta in template units, so this is the
            # gradient as felt, no rescaling.
            for name in (*GRADIENT_TERMS, "total"):
                fx, fy = per_anchor[name][free_i]
                row[f"f_{name}_x"] = float(fx)
                row[f"f_{name}_y"] = float(fy)
                row[f"f_{name}"] = float(np.hypot(fx, fy))
            lo, hi = sample_slice_of_anchor(problem, free_i)
            row["sample_lo"], row["sample_hi"] = lo, hi
            at = field_at_samples(problem, params, lo, hi)
            row.update({k: (round(v, 4) if isinstance(v, float) else v) for k, v in at.items()})
            row["d_smooth_mean_xh"] = round(at.get("d_smooth_mean_px", 0.0) / unit, 4) if at["n_samples"] else ""
            rows.append(row)
    return rows, report["residual_rel"]


def case_rows(job: tuple[str, object]) -> tuple[list[dict], float, int, int]:
    """Every anchor of ONE case — composed once, one solve per chainable run.

    The unit of parallelism, because `derive_word` is the expensive shared
    prefix of a case's runs (the same reason `laufform.harvest` pools over
    cases). Nothing raised inside may end the sweep.
    """
    which, case = job
    try:
        result = derive_word(case)
    except Exception as exc:  # noqa: BLE001 — one bad case must not end the run
        print(f"  skip {which}/{case.id}: derive failed ({exc})")
        return [], 0.0, 0, 0
    rows: list[dict] = []
    worst = 0.0
    n_solves = n_failed = 0
    grids = _grid_fits(case, result)
    for run_slots in _chainable_runs(case, grids):
        fit = fit_word_chain(
            case, run_slots, result=result, windows_px={s: grids[s]["window"] for s in run_slots}, keep_solve=True
        )
        if fit is None:
            n_failed += 1
            continue
        n_solves += 1
        new, residual = _rows_for_fit(case, fit, which=which)
        worst = max(worst, residual)
        rows.extend(new)
    print(f"  {which}/{case.id:<24} {len(rows):>5} anchors, {n_solves} solves", flush=True)
    return rows, worst, n_solves, n_failed


def run(sets: tuple[str, ...], style: str, max_cases: int, jobs: int = 1) -> tuple[list[dict], dict]:
    jobs_list: list[tuple[str, object]] = []
    for which in sets:
        cases = list(iter_fixture_word_cases(which=which, style=style))
        jobs_list.extend((which, c) for c in (cases[:max_cases] if max_cases else cases))

    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            produced = list(pool.map(case_rows, jobs_list))
    else:
        produced = [case_rows(job) for job in jobs_list]

    rows: list[dict] = []
    worst_residual = 0.0
    n_solves = n_failed = 0
    for new, worst, solved, failed in produced:
        rows.extend(new)
        worst_residual = max(worst_residual, worst)
        n_solves += solved
        n_failed += failed
    return rows, {
        "n_solves": n_solves,
        "n_failed_solves": n_failed,
        "n_anchors": len(rows),
        "n_stranded": sum(r["stranded"] for r in rows),
        "worst_sum_residual_rel": worst_residual,
    }


def _median(values) -> float | None:
    vals = [v for v in values if isinstance(v, (int, float))]
    return float(statistics.median(vals)) if vals else None


def summarize(rows: list[dict]) -> dict:
    """Median force per term, stranded against the control population.

    The comparison IS the finding: a term whose force is the same at a stranded
    anchor as at a healthy one is not what holds the stranding.
    """
    hot = [r for r in rows if r["stranded"]]
    cold = [r for r in rows if not r["stranded"]]
    out: dict = {"n_stranded": len(hot), "n_control": len(cold), "terms": {}}
    for name in (*GRADIENT_TERMS, "total"):
        out["terms"][name] = {
            "stranded_median": _median(r[f"f_{name}"] for r in hot),
            "control_median": _median(r[f"f_{name}"] for r in cold),
        }
    for label, pop in (("stranded", hot), ("control", cold)):
        out[f"{label}_field"] = {
            "d_smooth_mean_px": _median(r.get("d_smooth_mean_px") for r in pop),
            "d_raw_mean_px": _median(r.get("d_raw_mean_px") for r in pop),
            "grad_d_mean": _median(r.get("grad_d_mean") for r in pop),
            "delta_units": _median(r["delta_units"] for r in pop),
            "delta_neighbours_units": _median(r["delta_neighbours_units"] for r in pop),
        }
    return out


def print_report(summary: dict, meta: dict) -> None:
    print()
    print(f"solves {meta['n_solves']} ({meta['n_failed_solves']} failed) · anchors {meta['n_anchors']}")
    print(f"sum check: worst |sum(terms) - grad| / |grad|max = {meta['worst_sum_residual_rel']:.3e}")
    print()
    print(f"{'term':>10} {'stranded':>14} {'control':>14}   ratio")
    for name, vals in summary["terms"].items():
        s, c = vals["stranded_median"], vals["control_median"]
        ratio = f"{s / c:8.2f}x" if s is not None and c not in (None, 0.0) else "       —"
        print(f"{name:>10} {s if s is None else f'{s:14.3e}'} {c if c is None else f'{c:14.3e}'} {ratio}")
    print()
    print(f"{'field / anchor':>24} {'stranded':>14} {'control':>14}")
    for field in ("d_smooth_mean_px", "d_raw_mean_px", "grad_d_mean", "delta_units", "delta_neighbours_units"):
        s = summary["stranded_field"][field]
        c = summary["control_field"][field]
        print(f"{field:>24} {s if s is None else f'{s:14.4f}'} {c if c is None else f'{c:14.4f}'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--set", dest="sets", default="all", choices=["words", "pairs", "all"])
    parser.add_argument("--style", default="suetterlin")
    parser.add_argument("--max-cases", type=int, default=0, help="cut the case list (a smoke run)")
    parser.add_argument("--jobs", type=int, default=1, help="worker processes, pooled over CASES")
    parser.add_argument("--out", type=Path, default=Path("temp/gradlab"))
    add_expect_root_argument(parser)
    args = parser.parse_args()

    sets = ("words", "pairs") if args.sets == "all" else (args.sets,)
    # The gradient decomposition is a measurement (qualitaetsmetrik.md §11), so
    # it names its base before it measures like the benches do.
    announce_roots([_root_for(DEFAULT_FIXTURES_DIR, args.style, which) for which in sets], args.expect_root)
    rows, meta = run(sets, args.style, args.max_cases, jobs=args.jobs)
    if not rows:
        raise SystemExit("no anchors measured — are the frozen fixtures present?")
    summary = summarize(rows)
    print_report(summary, meta)

    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "anchors.csv"
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    (args.out / "summary.json").write_text(json.dumps({"meta": meta, "summary": summary}, indent=2))
    print(f"\nwrote {csv_path} ({len(rows)} rows) and summary.json")


if __name__ == "__main__":
    main()
