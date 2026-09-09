"""The seed-gap inventory: how far the chain's SEED lies from the plate ink.

The diagnosis round 9 asked for (§14 „Kette K-E `sep09`"). The judge's question
was why the same letter pair reads well in one word and „richtig schlimm" in
another, and the answer named in the aug20 K-C autopsy (finding (d)) is the
START, not the solve: the Kette is seeded from the COMPOSED word
(`chain_seed="composed"`, the follower's default), and a seed that starts on
the wrong ink settles there, leaving the zig-zag zones the paper-reversal
sensor counts.

**What this sensor measured, and it corrects the premise it was built on**
(§14 „Kette K-G Saat-Registrierung `sep09`"): „the seed lies farther away than
the solver's per-anchor travel budget" (`core.fit.MAX_ANCHOR_DELTA`, 0.75 xh)
is FALSE as a distance. No seed anchor of the 63 frozen words sits more than
0.68 xh from *some* ink, so `seed_over` is empty across the set. The error is
a CORRESPONDENCE — comfortably near the WRONG ink — which is why the two
halves below, and not the raw distance, are what the columns report.

Per letter slot this reports the seed's distance to the ink twice, because the
two halves have different cures:

* **Saat-Versatz** — the whole-letter translation the bounded grid search finds
  (`tools.laufform.harvest._grid_fits`, the follower's own window supplier).
  A pure placement error; the chain's per-slot translation block can absorb it
  as far as its own bounds (`FIT_DX_UNITS` 0.6 / `FIT_DY_UNITS` 0.20 xh) reach,
  and `--chain-seed grid` hands it to the solve as the starting point.
* **Saat-Rest** — the per-anchor distance that REMAINS after that best
  translation. No placement can remove it: it is the letter's shape not being
  the hand's shape (the composed `e` 1.32 xh wide against the hand's 0.65 xh).
  Anchors whose Saat-Rest exceeds `MAX_ANCHOR_DELTA` are the **Saat-Überschuss**
  — the seed error the solver is formally unable to travel.

Reads the frozen root, composes each word once and runs no solve: a report, not
a ruler, bound to no gate. No DB, no network.

    uv run python -m tools.pairlab.seedgap --all --expect-root <digest-prefix>
    uv run python -m tools.pairlab.seedgap --words unter Wer --json out.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

from core.fit import MAX_ANCHOR_DELTA
from tools.laufform.harvest import _chainable_runs, _grid_fits
from tools.pairlab.chain import _letter_spec
from tools.pairlab.ink_evidence import InkEvidenceOptions, ink_evidence_case
from tools.tracebench.reference import DEFAULT_FIXTURES_DIR
from tools.tracebench.run import find_fixture_root
from tools.wordbench.roots import add_expect_root_argument, announce_roots
from tools.wordlab.cases import WordCase, iter_fixture_word_cases
from tools.wordlab.derive import WordDeriveResult, derive_word


# The quantile reported beside the median and the maximum. The maximum alone is
# one anchor and reads as an outlier; the median alone hides a tail that is
# exactly the defect. p90 is the same pair the dev-19 dtw column reports.
SEED_QUANTILE = 0.9


def _distances_units(edt_px: np.ndarray, points_px: np.ndarray, xh: float) -> np.ndarray:
    """Nearest-ink distance of each point, in x-heights — `analyze._edt_at`'s rule.

    A seed anchor may lie OUTSIDE the crop, and reading the EDT at the clamped
    border pixel would then report it as if it already sat on the border. The
    clamp distance is added back, exactly as the grid search this sensor is
    measured against does it.
    """
    height, width = edt_px.shape
    cx = np.clip(points_px[:, 0], 0, width - 1)
    cy = np.clip(points_px[:, 1], 0, height - 1)
    base = edt_px[cy.round().astype(int), cx.round().astype(int)]
    return (base + np.hypot(points_px[:, 0] - cx, points_px[:, 1] - cy)) / xh


def _slot_row(
    case: WordCase, result: WordDeriveResult, slot_index: int, grid: dict, edt_px: np.ndarray
) -> dict[str, float | str | int | bool] | None:
    """One letter slot's seed gap — the chain's own seed anchors, measured."""
    made = _letter_spec(case, result, slot_index)
    if made is None:
        return None
    spec, _offset = made
    xh = float(result.xh_px)
    x_origin = float(result.registration["tx"])
    baseline_y = float(result.baseline_row) + float(result.registration["ty"])
    seed_px = np.column_stack([x_origin + spec.anchors[:, 0] * xh, baseline_y - spec.anchors[:, 1] * xh])
    shift_units = grid["shift_units"]
    shifted_px = seed_px + np.array([shift_units[0] * xh, shift_units[1] * xh])

    seed = _distances_units(edt_px, seed_px, xh)
    rest = _distances_units(edt_px, shifted_px, xh)
    return {
        "slot": int(slot_index),
        "key": str(spec.key or ""),
        "n_anchors": int(len(seed)),
        "seed_med": float(np.median(seed)),
        "seed_p90": float(np.quantile(seed, SEED_QUANTILE)),
        "seed_max": float(seed.max()),
        "seed_over": int((seed > MAX_ANCHOR_DELTA).sum()),
        "shift_x": float(shift_units[0]),
        "shift_y": float(shift_units[1]),
        "shift_abs": float(np.hypot(*shift_units)),
        # The grid search wanted more than its own window can give — read off
        # ITS verdict, never recomputed from the normalised shift: `_fit_letter`
        # rounds the pixel limit (`round(FIT_DX_UNITS * xh)`), so an optimum AT
        # the bound can normalise just below it and a recomputation would call
        # it free. This flag decides which slots `--chain-seed grid` skips, so
        # it has to be the follower's own answer.
        "shift_at_block_bound": bool(grid["at_bound"]),
        "rest_med": float(np.median(rest)),
        "rest_p90": float(np.quantile(rest, SEED_QUANTILE)),
        "rest_max": float(rest.max()),
        "rest_over": int((rest > MAX_ANCHOR_DELTA).sum()),
    }


def word_rows(case: WordCase) -> dict | None:
    """The per-slot seed gaps of one word, plus the word-level summary."""
    result = derive_word(case)
    if result.composed["missing"] or result.report is None or result.report.get("failed"):
        return None
    # The follower's own evidence: `_grid_fits`, the solve fields and the
    # coverage targets all read the K-C-cleaned ink, so the seed gap has to be
    # measured against the same ink or it is not the gap the solver sees.
    clean, _report = ink_evidence_case(case, InkEvidenceOptions())
    if clean.skel is None:
        return None
    grids = _grid_fits(clean, result)
    edt_px = distance_transform_edt(~clean.skel)
    rows = [
        row
        for run in _chainable_runs(clean, grids)
        for slot_index in run
        if (row := _slot_row(clean, result, slot_index, grids[slot_index], edt_px)) is not None
    ]
    if not rows:
        return None
    shift_x = [r["shift_x"] for r in rows]
    return {
        "specimen_id": case.id,
        "word": case.word,
        "slots": rows,
        "n_slots": len(rows),
        "seed_max": max(r["seed_max"] for r in rows),
        "seed_over": sum(r["seed_over"] for r in rows),
        "slots_over": sum(1 for r in rows if r["seed_over"]),
        "rest_max": max(r["rest_max"] for r in rows),
        "rest_p90_max": max(r["rest_p90"] for r in rows),
        "rest_over": sum(r["rest_over"] for r in rows),
        "slots_rest_over": sum(1 for r in rows if r["rest_over"]),
        "shift_max": max(r["shift_abs"] for r in rows),
        # The word-level statement the per-slot shifts add up to: a word whose
        # letters pull APART by more than the chain's global translation can
        # ever repair (one number for the whole run) is a word the composition
        # laid out at the wrong LENGTH — the width story of the aug20 K-C
        # autopsy, read without needing a per-letter ink segmentation.
        "shift_span_x": float(max(shift_x) - min(shift_x)),
        "n_at_block_bound": sum(1 for r in rows if r["shift_at_block_bound"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(prog="pairlab.seedgap", description=__doc__)
    parser.add_argument("--all", action="store_true", help="every word of the frozen words root")
    parser.add_argument("--words", nargs="+", help="specimen ids (or words) to measure")
    parser.add_argument("--top", type=int, default=20, help="rows to print (default 20)")
    parser.add_argument("--json", type=Path, help="write the full inventory here")
    add_expect_root_argument(parser)
    args = parser.parse_args()
    if not args.all and not args.words:
        parser.error("pass --all or --words")

    root = find_fixture_root(DEFAULT_FIXTURES_DIR, "suetterlin", "words")
    announce_roots([root], args.expect_root)
    cases = iter_fixture_word_cases(which="words", only=None if args.all else list(args.words))
    out = [row for case in cases if (row := word_rows(case)) is not None]
    print(f"budget MAX_ANCHOR_DELTA = {MAX_ANCHOR_DELTA} xh   ({len(out)} of {len(cases)} words measured)")
    print(
        f"{'word':16s} {'slots':>5s} {'span_x':>7s} {'shiftmx':>7s} {'restmx':>7s} {'restp90':>7s} {'seedmx':>7s} {'bnd':>4s}"
    )
    for row in sorted(out, key=lambda r: -r["shift_span_x"])[: args.top]:
        print(
            f"{row['specimen_id']:16s} {row['n_slots']:5d} {row['shift_span_x']:7.3f} {row['shift_max']:7.3f} "
            f"{row['rest_max']:7.3f} {row['rest_p90_max']:7.3f} {row['seed_max']:7.3f} {row['n_at_block_bound']:4d}"
        )
    n_over = sum(1 for r in out if r["seed_over"])
    print(f"words with at least one anchor over the budget: {n_over} of {len(out)}")
    print(f"  … still over after the grid shift:            {sum(1 for r in out if r['rest_over'])} of {len(out)}")
    print(
        f"  … with a slot at the translation block bound: {sum(1 for r in out if r['n_at_block_bound'])} of {len(out)}"
    )
    spans = np.array([r["shift_span_x"] for r in out])
    print(
        f"shift_span_x over the set: median {np.median(spans):.3f}  p90 {np.quantile(spans, 0.9):.3f}  max {spans.max():.3f} xh"
    )
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(out, indent=1, ensure_ascii=False))
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
