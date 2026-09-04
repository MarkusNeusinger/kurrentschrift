"""Build an LF11 smooth-row candidate map („glatte Zeile") from harvested occurrences.

Measurement layer only (docs/reference/werkzeuge.md): reads the per-occurrence
fits a harvest wrote (`--occ-out laufform_occurrences.json`) plus the chart rows
of ONE frozen fixture root, and writes the rows the write path WOULD produce if
the running form were medianed in a smooth basis instead of anchor by anchor
(`core.aggregate.spline_basis_median`, messjournal.md §14 `sep02`). Output
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
none. `--keys harvested` lifts that for a diagnostic run.

`--floor` is the evidence floor of the write path (`LAUFFORM_MIN_OCCURRENCES`,
the same number `PUT …/templates/{key}/laufform` refuses below): a key whose
FRESH harvest carries fewer occurrences is not re-derived from too little
evidence at all. The audit of 2026-09-02 (Befund 35) found two rows live that
had passed the endpoint on an explicit author statement, and the estimator does
not care how thin the stack under it is. `--floor 1` is that author statement,
spelled out.

**A key the run does not derive is left OUT of the map**, whether the floor
stopped it or the harvest produced no usable fit. It costs nothing in
measurement, because the file is an OVERLAY — `wordbench.run --laufform` and
its siblings leave every key the map does not name on its frozen row, which is
exactly the row a carried-over entry would have repeated. The report names each
omitted key with its reason, and `--keep-stored` puts the copies back for a run
that wants the map to be a complete snapshot rather than a write list
(`--floor 1 --keep-stored` is the behaviour this tool had before either
argument existed, and reproduces the LF11 card of `sep02`).

Every run closes by saying whether the map can be walked with a PUT per key,
measured against ALL THREE gates the endpoint stands on — the floor and the two
row gates, spike (LF8) and head (LF9). The floor alone would not answer the
question: the `--knots 0` control arm carries spikes the spline basis does not,
and a map that called itself writable on the strength of the floor would hand
those to the endpoint as 422s.

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

from core.aggregate import LAUFFORM_MIN_OCCURRENCES, spline_basis_median
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


def write_blockers(root: Path, rows: dict[str, dict], floor: int) -> list[str]:
    """Every row of a map that `PUT …/templates/{key}/laufform` would refuse.

    The endpoint stands on THREE gates, not one: the evidence floor and the two
    row gates, spike (LF8) and head (LF9). Reporting only the floor would let a
    map claim it is writable while a row waits to come back as a 422 — the
    `--knots 0` control arm is exactly that case, since the per-anchor median
    carries spikes the spline basis does not.
    """
    templates = json.loads((root / "templates.json").read_text())
    blocked: list[str] = []
    for key in sorted(rows):
        chart = templates.get(key)
        if chart is None:
            continue
        row = rows[key]
        n = int(((row.get("trace_meta") or {}).get("laufform") or {}).get("n_occurrences") or 0)
        view = _chart_view(chart)
        spike, head = spike_gate(view, row["anchors"]), head_gate(view, row["anchors"])
        reasons = []
        if n < floor:
            reasons.append(f"n={n} < floor {floor}")
        if spike["exceeded"]:
            reasons.append(f"spike {spike['ratio']:.2f} > {spike['max']:.2f}")
        if head["exceeded"]:
            reasons.append(f"head {head['deviation']:.1f}° > {head['max']:.0f}°")
        if reasons:
            blocked.append(f"{key} ({'; '.join(reasons)})")
    return blocked


def build_candidates(
    root: Path,
    occurrences: list[dict],
    knot_spacing: float,
    *,
    keys: str = "stored",
    floor: int = LAUFFORM_MIN_OCCURRENCES,
    keep_stored: bool = False,
) -> tuple[dict[str, dict], list[str]]:
    """Every eligible key's running form, medianed in the chosen basis.

    `knot_spacing` of 0 selects the per-anchor median (the control arm).
    `floor` is the evidence floor: a key with fewer fresh occurrences is not
    re-derived at all and drops out of the map, so every row that remains is one
    the write path accepts. `keep_stored` puts the dropped keys back as verbatim
    copies of their stored rows — the same geometry an overlay would have used
    anyway, but a map that then no longer travels as a write list. Returns the
    candidate rows keyed by glyph_key and one report line per key.
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
        usable = bool(anchor_sets) and len(anchor_sets[0]) == len(chart["anchors"])
        if not usable or len(anchor_sets) < floor:
            # Two different reasons, one behaviour: the row this run would
            # produce here is not one the write path accepts, so the map leaves
            # the key out and the overlay falls back to the frozen row by
            # itself. Saying WHICH reason is the point — "no fits" is a gap in
            # the harvest, "under the floor" is a gap in the evidence.
            why = f"no usable fits: n={len(anchor_sets)}" if not usable else f"n={len(anchor_sets)} < floor {floor}"
            if keep_stored and key in stored:
                rows[key] = stored[key]
                report.append(f"  {key:6s} stored row kept verbatim ({why})")
            else:
                report.append(f"  {key:6s} left out of the map ({why})")
            continue
        stack = np.asarray(anchor_sets, dtype=float)
        meta = chart.get("trace_meta") or {}
        notes: list[str] = []
        # The per-anchor median is computed either way: for `--knots 0` it IS
        # the arm, and for a spline rung it is what the head/tail columns below
        # measure the smoothing's end movement against (the pre-registration
        # left the ends free and promised to report how far they travelled).
        plain = np.median(stack, axis=0)
        median = plain
        if knot_spacing > 0.0:
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
        head_move = math.hypot(*(median[0] - plain[0]))
        tail_move = math.hypot(*(median[-1] - plain[-1]))
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
    ap.add_argument(
        "--floor",
        type=int,
        default=LAUFFORM_MIN_OCCURRENCES,
        help=f"evidence floor for a re-derived row (default: the write path's {LAUFFORM_MIN_OCCURRENCES}); "
        "a thinner key drops out of the map. Pass 1 as an explicit author statement",
    )
    ap.add_argument(
        "--keep-stored",
        action="store_true",
        help="copy the stored row of every key this run does not derive into the map — a complete snapshot "
        "instead of a write list (the overlay behaves identically either way)",
    )
    ap.add_argument("--out", type=Path, required=True, help="candidate map (glyph_key -> full fixture row)")
    args = ap.parse_args()
    if args.knots < 0.0:
        # Exactly 0 is the control arm and says so in the header; a negative
        # would quietly select it too, and a run whose arm nobody can read off
        # the command that produced it is not a measurement.
        raise SystemExit(f"--knots must be 0 (control arm) or a positive spacing, got {args.knots}")

    if args.floor < 1:
        raise SystemExit(f"--floor must be at least 1, got {args.floor}")

    occurrences = json.loads(args.occurrences.read_text())
    rows, report = build_candidates(
        args.root, occurrences, args.knots, keys=args.keys, floor=args.floor, keep_stored=args.keep_stored
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rows, ensure_ascii=False))
    arm = "per-anchor median (control)" if args.knots == 0.0 else f"spline basis, knots {args.knots} xh"
    print(f"LF11 {arm} · root={args.root.name} · floor {args.floor}: {len(rows)} candidate rows → {args.out}")
    print("\n".join(report))
    # Whether the map can be walked with a PUT per key is a property of the
    # FILE, so it is stated on the file rather than inferred from the arguments:
    # a copied row can sit under the floor, and an arm like `--knots 0` can
    # carry a spike the endpoint refuses even where the floor is satisfied.
    blocked = write_blockers(args.root, rows, args.floor)
    if blocked:
        print(f"rows the write path would refuse: {len(blocked)} — {', '.join(blocked)}")
        print("this map is NOT a write list")
    else:
        print(f"rows the write path would refuse: none — all {len(rows)} rows pass floor, spike and head")


if __name__ == "__main__":
    main()
