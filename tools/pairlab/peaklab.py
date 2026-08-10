"""The fast loop on a small working set: where are the peaks, and did they go?

Built against the owner's constraint that a round has to take minutes, not
hours. It fits ONE named set of words (default: the words whose outliers the
author marked in `data/humanbench/`, plus clean controls), reports the lone
excursions per letter occurrence, and — with `--png` — draws the fitted chain
over the specimen ink with every peak circled, so the question „is it gone"
is answered by looking rather than by a table.

    uv run --extra viz python -m tools.pairlab.peaklab --png temp/peaks.png
    uv run --extra viz python -m tools.pairlab.peaklab --repair --png temp/peaks-repaired.png
    uv run --extra viz python -m tools.pairlab.peaklab --compare --png temp/peaks-ab.png

`--compare` runs both arms over the same solves and draws them side by side.
The solve is IDENTICAL in both — the repair is a post-processing step on the
fitted anchors, so nothing about the fit changes and the comparison is exact.

Measurement only: no DB, no API, no writes to `core/`, nothing that renders
into the product.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from tools.laufform.harvest import (
    SPIKE_REPAIR_RATIO,
    _chainable_runs,
    _grid_fits,
    anchor_spike_ratio,
    repair_anchor_spikes,
)
from tools.pairlab.chain import fit_word_chain
from tools.wordlab.cases import iter_fixture_word_cases
from tools.wordlab.derive import derive_word


# The working set. Five words carrying outliers the AUTHOR marked in the blind
# judgement rounds, plus three he passed as clean — a round with no controls
# cannot tell „the peaks are gone" from „everything got flattened".
PEAK_CASES = ("Sprünge", "schießen", "wenn", "zwei", "daß")
CONTROL_CASES = ("und-2", "ein", "muß")
WORKING_SET = PEAK_CASES + CONTROL_CASES


def peaks_of(anchors: np.ndarray, stroke_starts) -> list[int]:
    """Indices of the lone excursions — the same rule `repair_anchor_spikes` uses.

    Read through the repair itself rather than reimplemented, so the detector
    and the fix can never disagree about what a peak is.
    """
    _, repairs = repair_anchor_spikes(anchors, stroke_starts, ratio=SPIKE_REPAIR_RATIO)
    return [r["index"] for r in repairs]


def measure(case_ids: tuple[str, ...], style: str) -> list[dict]:
    """One row per fitted letter occurrence of the working set."""
    wanted = set(case_ids)
    cases = [c for c in iter_fixture_word_cases(which="words", style=style) if c.id in wanted]
    missing = wanted - {c.id for c in cases}
    if missing:
        print(f"  ! not in the frozen fixtures: {', '.join(sorted(missing))}")
    rows: list[dict] = []
    for case in cases:
        try:
            result = derive_word(case)
        except Exception as exc:  # noqa: BLE001 — one bad case must not end the round
            print(f"  skip {case.id}: derive failed ({exc})")
            continue
        grids = _grid_fits(case, result)
        for run_slots in _chainable_runs(case, grids):
            fit = fit_word_chain(
                case, run_slots, result=result, windows_px={s: grids[s]["window"] for s in run_slots}, keep_solve=True
            )
            if fit is None:
                continue
            problem, params = fit.problem, fit.params
            placed = problem.free_anchors(params)
            for n, seg in enumerate([s for s in fit.segments if s.kind == "letter"]):
                if seg.fitted_anchors is None:
                    continue
                chart = case.templates.get(seg.key) or {}
                starts = (chart.get("trace_meta") or {}).get("stroke_starts") or [0]
                a0, a1 = seg.anchor_slice
                # The PLACED anchors, so they can be drawn in the crop's own
                # pixels over the ink. Detection and midpoint are both
                # translation-invariant, so repairing here is the same repair
                # the stored (centered) chain would get.
                raw = placed[a0:a1]
                fixed, repairs = repair_anchor_spikes(raw, starts)

                def to_px(a: np.ndarray, p: object = problem) -> np.ndarray:
                    """Template units → crop pixels, in the solve's own frame."""
                    return np.column_stack([p.x_origin_px + a[:, 0] * p.unit_px, p.baseline_y_px - a[:, 1] * p.unit_px])

                rows.append(
                    {
                        "case": case.id,
                        "slot": fit.slots[n],
                        "key": seg.key,
                        "px_raw": to_px(raw),
                        "px_repaired": to_px(fixed),
                        "peaks": [r["index"] for r in repairs],
                        "moved": [r["moved"] for r in repairs],
                        "spike_raw": anchor_spike_ratio(raw, starts),
                        "spike_repaired": anchor_spike_ratio(fixed, starts),
                        "stroke_starts": starts,
                        "skel": case.skel,
                        "geo_rmse_px": float(seg.geo_rmse_px),
                        "xh": float(result.xh_px),
                        "control": case.id in CONTROL_CASES,
                    }
                )
    return rows


def report(rows: list[dict]) -> None:
    hit = [r for r in rows if r["peaks"]]
    print()
    print(f"{'word':<12} {'slot':>4} {'key':>5} {'peaks':>6} {'spike raw':>10} {'repaired':>9} {'moved xh':>9}")
    for r in sorted(rows, key=lambda r: (-len(r["peaks"]), r["case"])):
        if not r["peaks"] and not r["control"]:
            continue
        moved = f"{max(r['moved']):.3f}" if r["moved"] else "—"
        tag = " (Kontrolle)" if r["control"] else ""
        print(
            f"{r['case']:<12} {r['slot']:>4} {r['key'] or '?':>5} {len(r['peaks']):>6} "
            f"{r['spike_raw']:>10.2f} {r['spike_repaired']:>9.2f} {moved:>9}{tag}"
        )
    n_ctrl_hit = sum(1 for r in hit if r["control"])
    print()
    print(f"occurrences {len(rows)} · with a lone excursion {len(hit)} · of those in a CONTROL word {n_ctrl_hit}")
    if hit:
        print(
            f"spike ratio over the affected: {np.median([r['spike_raw'] for r in hit]):.2f} "
            f"-> {np.median([r['spike_repaired'] for r in hit]):.2f}"
        )


def draw(rows: list[dict], path: Path, *, compare: bool) -> None:
    """The picture: fitted chain over the ink, peaks circled."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    hit = [r for r in rows if r["peaks"]]
    if not hit:
        print("nothing to draw — no lone excursion in this set")
        return
    cols = 2 if compare else 1
    fig, axes = plt.subplots(len(hit), cols, figsize=(5.0 * cols, 3.4 * len(hit)), squeeze=False)
    for row_i, r in enumerate(hit):
        arms = [("gefittet", r["px_raw"])] + ([("repariert", r["px_repaired"])] if compare else [])
        # One window per row, from the UNION of both arms, so the two panels of
        # a comparison are at the same scale and a shift is not a zoom.
        both = np.vstack([r["px_raw"], r["px_repaired"]])
        pad = 0.45 * r["xh"]
        x0, y0 = both.min(axis=0) - pad
        x1, y1 = both.max(axis=0) + pad
        for col, (label, xy) in enumerate(arms):
            ax = axes[row_i][col]
            skel = np.asarray(r["skel"])
            ax.imshow(skel, cmap="Greys", interpolation="nearest", alpha=0.85, zorder=0)
            for lo, hi in zip(
                sorted({0, *(s for s in r["stroke_starts"] if 0 < s < len(xy)), len(xy)})[:-1],
                sorted({0, *(s for s in r["stroke_starts"] if 0 < s < len(xy)), len(xy)})[1:],
                strict=True,
            ):
                ax.plot(xy[lo:hi, 0], xy[lo:hi, 1], "-", lw=1.0, color="#2f6f62", zorder=2)
            ax.plot(xy[:, 0], xy[:, 1], ".", ms=2.6, color="#2f6f62", zorder=3)
            for i in r["peaks"]:
                ax.plot(xy[i, 0], xy[i, 1], "o", ms=13, mfc="none", mec="#c0392b", mew=1.9, zorder=4)
            spike = r["spike_raw"] if label == "gefittet" else r["spike_repaired"]
            ax.set_title(f"{r['case']} · {r['key']}@{r['slot']} — {label} (Sprung {spike:.1f}×)", fontsize=9)
            ax.set_xlim(x0, x1)
            ax.set_ylim(y1, y0)  # image rows run downward
            ax.set_aspect("equal")
            ax.axis("off")
    fig.suptitle("Einzelner Ausreißer im gefitteten Ankerzug über der Tinte (rot markiert)", fontsize=11)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    print(f"\nwrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cases", default=",".join(WORKING_SET), help="comma-separated fixture ids")
    parser.add_argument("--style", default="suetterlin")
    parser.add_argument("--compare", action="store_true", help="draw fitted and repaired side by side")
    parser.add_argument("--png", type=Path, default=None)
    args = parser.parse_args()

    ids = tuple(c.strip() for c in args.cases.split(",") if c.strip())
    print(f"working set: {', '.join(ids)}")
    rows = measure(ids, args.style)
    if not rows:
        raise SystemExit("nothing measured — are the frozen fixtures present?")
    report(rows)
    if args.png:
        draw(rows, args.png, compare=args.compare)


if __name__ == "__main__":
    main()
