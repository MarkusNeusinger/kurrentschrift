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

THE MEASUREMENT IS REFERENCE-FREE, and only the plumbing around it is not:
the distance is read against the specimen's OWN ink, never against a reference
trace. That is why `ink_distance_px` and `excursion_readings` sit apart from
the fixture wiring — an own-hand strip has no reference by doctrine
(`docs/proposals/eigenhand-erfassung.md` §12) and no bench frame either, but it
has a binarised ink mask and a followed Bahn, which is all the kernel needs
(`tools.eigenhand.pfad`, the Tintentreue sensor „Papier-Exkursion").

    uv run python -m tools.tracebench.excursions temp/candidate.json
    uv run python -m tools.tracebench.excursions a.json b.json --top 12
        [--expect-root <digest-prefix>]

The inventory reads the frozen words root, so it names it (``root:`` /
``digest=``) before the first distance and accepts ``--expect-root`` to make
that base a precondition — the sensor of #478, applied to the sensors.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

from tools.tracebench.candidates import file_provider
from tools.tracebench.counters import RESAMPLE_STEP_UNITS, resampled_strokes
from tools.tracebench.reference import DEFAULT_FIXTURES_DIR, Reference, load_reference
from tools.tracebench.run import find_fixture_root
from tools.wordbench.roots import add_expect_root_argument, announce_roots


# The pre-registered inventory thresholds (§14 „Kette K-D `aug21`"), in
# x-heights: the aug20 needle class sat at 0.5–0.83 xh, ordinary on-ink
# riding stays well under 0.35.
EXCURSION_THRESHOLDS = (0.35, 0.5)
# The ruler's own resample step, imported so the sensor can never drift from
# the counters/DTW discretisation.
INVENTORY_STEP_UNITS = RESAMPLE_STEP_UNITS


def ink_distance_px(ink: np.ndarray) -> np.ndarray:
    """Per image pixel: the distance to the nearest ink pixel, in that image's px.

    The one place the transform is spelled, so a caller outside the bench reads
    the same field this inventory reads. What counts as ink is the CALLER's
    question — the bench hands in the K-C-cleaned evidence, a strip its own
    binarised mask — and that is the whole difference between the two.
    """
    return distance_transform_edt(~np.asarray(ink, dtype=bool))


def excursion_readings(
    strokes_units: Sequence[Sequence[Sequence[float]]],
    to_image_px: Callable[[np.ndarray], np.ndarray],
    dist_px: np.ndarray,
    xh_px: float,
) -> dict[str, float] | None:
    """How far one path strays from the ink under it — the kernel, without fixtures.

    `strokes_units` are pen runs in x-height units, `to_image_px` maps such
    points onto the grid `dist_px` was built on, and `xh_px` is that grid's
    x-height. `None` where the path has nothing to measure.

    The resampling happens in UNIT space at the ruler's own step, so every
    sample stands for the same arc length and `arc_<t>` is a length rather than
    a pixel count. Keeping it in here is the point of the function: a second
    caller that resampled in pixels would report arc lengths in another unit
    and nobody would see it in the number.
    """
    parts = [stroke for stroke in resampled_strokes(strokes_units, INVENTORY_STEP_UNITS) if len(stroke)]
    if not parts:
        return None
    px = to_image_px(np.vstack(parts))
    r = np.clip(np.round(px[:, 1]).astype(int), 0, dist_px.shape[0] - 1)
    c = np.clip(np.round(px[:, 0]).astype(int), 0, dist_px.shape[1] - 1)
    d_units = dist_px[r, c] / xh_px
    return {
        "max": float(d_units.max()),
        **{f"arc_{t}": float((d_units > t).sum() * INVENTORY_STEP_UNITS) for t in EXCURSION_THRESHOLDS},
    }


def _cleaned_ink_distance_px(specimen_id: str, reference: Reference) -> np.ndarray | None:
    """EDT (crop px) of the K-C-cleaned evidence ink for one specimen."""
    from tools.pairlab.ink_evidence import InkEvidenceOptions, ink_evidence_case  # noqa: PLC0415
    from tools.wordlab.cases import iter_fixture_word_cases  # noqa: PLC0415

    case = next(iter(iter_fixture_word_cases(which="words", style="suetterlin", only=[specimen_id])), None)
    if case is None or case.width_map is None:
        return None
    clean, _report = ink_evidence_case(case, InkEvidenceOptions())
    return ink_distance_px(clean.width_map > 0)


def inventory(
    candidate_path: Path, reference: Reference, dist_cache: dict[str, np.ndarray | None] | None = None
) -> dict[str, dict[str, float]]:
    """`{specimen_id: {max, arc_<t>...}}` — excursions in xh for one candidate file.

    `dist_cache` carries the per-specimen evidence EDTs across candidate files
    (they depend on the fixtures only, never on the candidate) — a
    multi-candidate run pays the fixture I/O and distance transforms once.
    """
    cands = file_provider(str(candidate_path))(reference, reference.order)
    cache = dist_cache if dist_cache is not None else {}
    rows: dict[str, dict[str, float]] = {}
    for sid in reference.order:
        cand, entry = cands.get(sid), reference.entries[sid]
        if cand is None or not cand.ok:
            continue
        if sid not in cache:
            cache[sid] = _cleaned_ink_distance_px(sid, reference)
        dist_px = cache[sid]
        if dist_px is None:
            continue
        strokes = entry.frame.trace_to_bench(cand.strokes, cand.registration_px, cand.xh_px)
        row = excursion_readings(strokes, entry.frame.bench_to_crop_px, dist_px, entry.frame.xh)
        if row is None:
            continue
        rows[sid] = row
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(prog="tracebench.excursions", description=__doc__)
    parser.add_argument("candidates", nargs="+", type=Path, help="tracebench file-provider candidate JSONs")
    parser.add_argument("--top", type=int, default=12, help="rows to print per candidate (default 12)")
    parser.add_argument("--json", type=Path, help="write the full inventory here")
    add_expect_root_argument(parser)
    args = parser.parse_args()

    root = find_fixture_root(DEFAULT_FIXTURES_DIR, "suetterlin", "words")
    # The sensor reads the evidence ink of a root, so its numbers belong to
    # that root — named before the first distance, pinnable like every bench.
    announce_roots([root], args.expect_root)
    reference = load_reference(root)
    dist_cache: dict[str, np.ndarray | None] = {}
    out: dict[str, dict[str, dict[str, float]]] = {}
    for path in args.candidates:
        rows = inventory(path, reference, dist_cache)
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
