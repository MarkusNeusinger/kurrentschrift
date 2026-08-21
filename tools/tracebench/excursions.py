"""The paper-excursion inventory: how far a candidate's path leaves the ink.

The standing sensor of the K-D closure (§14 „Kette K-D `aug21`"): the ink
corridor was closed as objectless because this inventory found no word above
0.35 xh of paper excursion once the v4 evidence mask had healed the needle
class at its root. The §7.9 revival trigger reads this tool — a future
candidate showing a new paper-needle class re-opens the corridor with a fresh
pre-registration.

Per word: the candidate's strokes are mapped through the bench frame,
resampled at the ruler's step, and each sample's distance to the
K-C-CLEANED evidence ink is read (foreign ink does not count as ink).
Reported per word: the maximum excursion in x-heights and the arc length of
samples beyond each threshold. Reads only fixtures and a candidate file —
no DB, no network, no solve.

    uv run python -m tools.tracebench.excursions temp/candidate.json
    uv run python -m tools.tracebench.excursions a.json b.json --top 12
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

from tools.tracebench.candidates import file_provider
from tools.tracebench.counters import resampled_strokes
from tools.tracebench.reference import DEFAULT_FIXTURES_DIR, Reference, load_reference
from tools.tracebench.run import find_fixture_root


# The pre-registered inventory thresholds (§14 „Kette K-D `aug21`"), in
# x-heights: the aug20 needle class sat at 0.5–0.83 xh, ordinary on-ink
# riding stays well under 0.35.
EXCURSION_THRESHOLDS = (0.35, 0.5)
# The ruler's own resample step (counters.RESAMPLE_STEP_UNITS is the scoring
# default); the inventory samples the path at the same granularity.
INVENTORY_STEP_UNITS = 0.02


def _cleaned_ink_distance_px(specimen_id: str, reference: Reference) -> np.ndarray | None:
    """EDT (crop px) of the K-C-cleaned evidence ink for one specimen."""
    from tools.pairlab.ink_evidence import InkEvidenceOptions, ink_evidence_case  # noqa: PLC0415
    from tools.wordlab.cases import iter_fixture_word_cases  # noqa: PLC0415

    case = next(iter(iter_fixture_word_cases(which="words", style="suetterlin", only=[specimen_id])), None)
    if case is None or case.width_map is None:
        return None
    clean, _report = ink_evidence_case(case, InkEvidenceOptions())
    return distance_transform_edt(~np.asarray(clean.width_map > 0))


def inventory(candidate_path: Path, reference: Reference) -> dict[str, dict[str, float]]:
    """`{specimen_id: {max, arc_<t>...}}` — excursions in xh for one candidate file."""
    cands = file_provider(str(candidate_path))(reference, reference.order)
    rows: dict[str, dict[str, float]] = {}
    for sid in reference.order:
        cand, entry = cands.get(sid), reference.entries[sid]
        if cand is None or not cand.ok:
            continue
        dist_px = _cleaned_ink_distance_px(sid, reference)
        if dist_px is None:
            continue
        strokes = entry.frame.trace_to_bench(cand.strokes, cand.registration_px, cand.xh_px)
        parts = [s for s in resampled_strokes(strokes, INVENTORY_STEP_UNITS) if len(s)]
        if not parts:
            continue
        px = entry.frame.bench_to_crop_px(np.vstack(parts))
        r = np.clip(np.round(px[:, 1]).astype(int), 0, dist_px.shape[0] - 1)
        c = np.clip(np.round(px[:, 0]).astype(int), 0, dist_px.shape[1] - 1)
        d_units = dist_px[r, c] / entry.frame.xh
        rows[sid] = {
            "max": float(d_units.max()),
            **{f"arc_{t}": float((d_units > t).sum() * INVENTORY_STEP_UNITS) for t in EXCURSION_THRESHOLDS},
        }
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(prog="tracebench.excursions", description=__doc__)
    parser.add_argument("candidates", nargs="+", type=Path, help="tracebench file-provider candidate JSONs")
    parser.add_argument("--top", type=int, default=12, help="rows to print per candidate (default 12)")
    parser.add_argument("--json", type=Path, help="write the full inventory here")
    args = parser.parse_args()

    root = find_fixture_root(DEFAULT_FIXTURES_DIR, "suetterlin", "words")
    reference = load_reference(root)
    out: dict[str, dict[str, dict[str, float]]] = {}
    for path in args.candidates:
        rows = inventory(path, reference)
        out[path.name] = rows
        print(f"== {path.name} ({len(rows)} words)")
        for sid, row in sorted(rows.items(), key=lambda kv: -kv[1]["max"])[: args.top]:
            arcs = "   ".join(f"arc>{t}: {row[f'arc_{t}']:.2f}" for t in EXCURSION_THRESHOLDS)
            print(f"  {sid:14s} max {row['max']:.3f} xh   {arcs}")
        for t in EXCURSION_THRESHOLDS:
            hits = sorted(s for s, row in rows.items() if row["max"] >= t)
            print(f"  words with max excursion >= {t}: {len(hits)}{' -> ' + ', '.join(hits) if hits else ''}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(out, indent=1))
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
