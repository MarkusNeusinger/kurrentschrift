"""Build an LF11 „glatte Zeile" candidate map from harvested occurrences.

Measurement layer only (docs/reference/werkzeuge.md): reads the per-occurrence
fits a harvest wrote (`--occ-out laufform_occurrences.json`) plus the chart rows
of ONE frozen fixture root, and writes the rows the write path WOULD produce if
the running form were medianed in a smooth basis instead of anchor by anchor
(`core.aggregate.spline_basis_median`, qualitaetsmetrik.md §14 `sep02`). Output
is full fixture rows, so `wordbench.run --laufform`, `wordlab --laufform` and
`humanbench.wordarm --laufform` take them verbatim.

    uv run python -m tools.laufform.harvest --path chain --sets words --min-n 1 \\
        --jobs 4 --occ-out temp/lf11/occ.json
    uv run python -m tools.laufform.smoothrow --occurrences temp/lf11/occ.json \\
        --knots 0.16 --out temp/lf11/cand-k016.json
    uv run python -m tools.laufform.smoothrow --occurrences temp/lf11/occ.json \\
        --knots 0 --out temp/lf11/cand-median.json

`temp/` because a harvest artefact is derived from the reserved dataset and is
never committed (`/temp/` is gitignored, the repo root's `runs/` is not).

`--knots 0` is the CONTROL arm: the same occurrences through the plain
per-anchor median, i.e. today's estimator. It exists because a fresh harvest is
already a different derivation from the stored rows (a later chain, repaired
rectangles, different n), so without it the smoothing could not be told apart
from the drift. The candidate and the control name exactly the same keys.

By default the map names exactly the keys the ROOT already has a stored row for
(`--keys stored`): a map that introduced extra rows would compose a different
letter set from the base it is measured against, and the comparison would be
none. `--keys harvested` lifts that for a diagnostic run. A stored key the
harvest produced no fits for keeps its stored row verbatim.

Never writes to the DB or the fixture root.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from core.aggregate import spline_basis_median
from core.laufform import head_gate, smoothness_gap, spike_gate
from tools.wordbench.fetch_fixtures import laufform_row_from_payload


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "tools" / "wordbench" / "fixtures" / "suetterlin" / "suetterlin-1922"


def _chart_view(chart: dict) -> SimpleNamespace:
    return SimpleNamespace(
        anchors=chart["anchors"], half_widths=chart["half_widths"], trace_meta=chart.get("trace_meta") or {}
    )


def occurrences_by_key(occurrences: list[dict]) -> dict[str, list[list[list[float]]]]:
    """Group the harvest's occurrence rows by glyph key, variant 0 only.

    Rows whose anchor count deviates from their group's modal count are dropped,
    exactly as `aggregate_instances` drops them: a different anchor sampling is a
    different measurement and cannot be stacked.
    """
    grouped: dict[str, list[list[list[float]]]] = defaultdict(list)
    for row in occurrences:
        if int(row.get("variant", 0) or 0) != 0:
            continue
        grouped[str(row["glyph_key"])].append(row["anchors"])
    out: dict[str, list[list[list[float]]]] = {}
    for key, anchor_sets in grouped.items():
        counts: dict[int, int] = defaultdict(int)
        for anchors in anchor_sets:
            counts[len(anchors)] += 1
        modal = max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]
        out[key] = [a for a in anchor_sets if len(a) == modal]
    return out


def build_candidates(
    root: Path, occurrences: list[dict], knot_spacing: float, *, keys: str = "stored"
) -> tuple[dict[str, dict], list[str]]:
    """Every eligible key's running form, medianed in the chosen basis.

    `knot_spacing` of 0 selects the per-anchor median (the control arm). Returns
    the candidate rows keyed by glyph_key and one report line per key.
    """
    templates = json.loads((root / "templates.json").read_text())
    stored = json.loads((root / "templates_laufform.json").read_text())
    grouped = occurrences_by_key(occurrences)
    wanted = sorted(stored) if keys == "stored" else sorted(set(grouped) & set(templates))

    rows: dict[str, dict] = {}
    report: list[str] = []
    for key in wanted:
        chart = templates.get(key)
        if chart is None:
            report.append(f"  skip {key}: no chart row in the root")
            continue
        anchor_sets = grouped.get(key) or []
        if not anchor_sets or len(anchor_sets[0]) != len(chart["anchors"]):
            if key in stored:
                rows[key] = stored[key]
                report.append(f"  {key:6s} stored row kept verbatim (no usable fits: n={len(anchor_sets)})")
            else:
                report.append(f"  skip {key}: no usable fits")
            continue
        stack = np.asarray(anchor_sets, dtype=float)
        meta = chart.get("trace_meta") or {}
        notes: list[str] = []
        if knot_spacing <= 0.0:
            median = np.median(stack, axis=0)
        else:
            median, notes = spline_basis_median(
                stack,
                chart["anchors"],
                meta.get("stroke_starts"),
                meta.get("corner_anchors"),
                knot_spacing=knot_spacing,
            )
        anchors = median.round(4).tolist()
        row = laufform_row_from_payload(
            chart, anchors, {"derived_from": "lf11-smoothrow", "n_occurrences": len(anchor_sets)}
        )
        rows[key] = row
        view = _chart_view(chart)
        zig = smoothness_gap(view, row["anchors"])
        spike, head = spike_gate(view, row["anchors"]), head_gate(view, row["anchors"])
        moved = np.asarray(row["anchors"], dtype=float) - np.asarray(chart["anchors"], dtype=float)
        head_move = math.hypot(*(np.asarray(row["anchors"][0]) - median[0]))
        tail_move = math.hypot(*(np.asarray(row["anchors"][-1]) - median[-1]))
        report.append(
            f"  {key:6s} n={len(anchor_sets):>2}  zig {zig['candidate']:6.2f} (chart {zig['chart']:5.2f}, "
            f"Δ {zig['gap']:+6.2f})  spike {spike['ratio']:5.2f}{'!' if spike['exceeded'] else ' '} "
            f"head {head['deviation']:5.1f}°{'!' if head['exceeded'] else ' '} "
            f"vs chart {float(np.hypot(*moved.T).mean()):.3f} xh  ends {head_move:.3f}/{tail_move:.3f}"
            + (f"  [{'; '.join(notes)}]" if notes else "")
        )
    return rows, report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="fixture root (default: the frozen words root)")
    ap.add_argument("--occurrences", type=Path, required=True, help="the harvest's --occ-out file")
    ap.add_argument(
        "--knots", type=float, required=True, help="interior knot spacing in x-heights (0 = per-anchor median control)"
    )
    ap.add_argument(
        "--keys",
        choices=["stored", "harvested"],
        default="stored",
        help="which keys the map names (default: exactly the root's stored rows)",
    )
    ap.add_argument("--out", type=Path, required=True, help="candidate map (glyph_key -> full fixture row)")
    args = ap.parse_args()

    occurrences = json.loads(args.occurrences.read_text())
    rows, report = build_candidates(args.root, occurrences, args.knots, keys=args.keys)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rows, ensure_ascii=False))
    arm = "per-anchor median (control)" if args.knots <= 0 else f"spline basis, knots {args.knots} xh"
    print(f"LF11 {arm} · root={args.root.name}: {len(rows)} candidate rows → {args.out}")
    print("\n".join(report))


if __name__ == "__main__":
    main()
