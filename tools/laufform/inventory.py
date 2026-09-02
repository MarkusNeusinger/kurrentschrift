"""Inventory of the stored Laufform rows against their chart forms (LF7/LF8) —
the „Bestandsaufnahme" of qualitaetsmetrik.md §14.

Measurement layer only (docs/reference/werkzeuge.md): reads `templates.json`
(chart rows) + `templates_laufform.json` (the stored running forms) of ONE
fixture root and prints, per row, the ROW GATE quantity — the anchor spike
ratio (`core.laufform.anchor_spike_ratio`, „Anker im leeren Papier", measured
on the row over the chart's stroke starts; LF8) — beside the report columns of
LF7 (the geometry-only naturalness of chart and row and their gap Δ) and the
row's evidence count, the HEAD GATE quantity of LF9 — the row's head
deviation (`core.laufform.head_deviation`: how far the first stroke's landing
direction turns away from the chart's, in degrees) — and the SMOOTHNESS SENSOR
of LF11 (`core.laufform.zigzag_rate`: how often the rendered row reverses its
curvature per x-height, printed beside its own chart row's rate; report-only,
and the one column that names the wobble no frozen ruler sees). The pre-registered gate
rules are applied on top: τ = the largest spike ratio among the rows with
n ≥ LAUFFORM_MIN_OCCURRENCES, rounded up to 0.01, and the doctrine-derived
head gate LAUFFORM_HEAD_DEVIATION_MAX; every row over either is listed — those
are the rows the author decides about.

    uv run python -m tools.laufform.inventory [--root DIR] [--json out.json]
    uv run --extra viz python -m tools.laufform.inventory --png inventory.png [--only K,t,E]

`--png` draws each selected row over its chart form (anchors, both in
template units) — the picture the word ruler never looks at. Never writes to
the DB or the fixture root.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from types import SimpleNamespace

from core.aggregate import LAUFFORM_MIN_OCCURRENCES
from core.laufform import (
    LAUFFORM_HEAD_DEVIATION_MAX,
    anchor_spike_ratio,
    head_deviation,
    naturalness_gap,
    smoothness_gap,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "tools" / "wordbench" / "fixtures" / "suetterlin" / "suetterlin-1922"


def _chart_view(chart: dict) -> SimpleNamespace:
    return SimpleNamespace(
        anchors=chart["anchors"], half_widths=chart["half_widths"], trace_meta=chart.get("trace_meta") or {}
    )


def inventory(root: Path) -> tuple[list[dict], float | None]:
    """Per stored row: n, spike ratio (row and chart), naturalness gap; plus τ.

    Returns the rows sorted by spike ratio (largest first) and τ — None when
    the root holds no row at or above the evidence floor (then there is no
    trusted population to derive a gate from, and the rule says so instead of
    guessing).
    """
    templates = json.loads((root / "templates.json").read_text())
    stored = json.loads((root / "templates_laufform.json").read_text())
    rows: list[dict] = []
    for key in sorted(stored):
        chart = templates.get(key)
        if chart is None:
            continue
        row = stored[key]
        meta = (row.get("trace_meta") or {}).get("laufform") or {}
        n = int(meta.get("n_occurrences") or 0)
        starts = (chart.get("trace_meta") or {}).get("stroke_starts")
        g = naturalness_gap(_chart_view(chart), row["anchors"])
        zig = smoothness_gap(_chart_view(chart), row["anchors"])
        comp_gap = {
            k: round(g["candidate"]["components"][k] - g["chart"]["components"][k], 4) for k in g["chart"]["components"]
        }
        rows.append(
            {
                "glyph_key": key,
                "n_occurrences": n,
                "spike_ratio": round(anchor_spike_ratio(row["anchors"], starts), 4),
                "chart_spike_ratio": round(anchor_spike_ratio(chart["anchors"], starts), 4),
                "head_deviation": round(head_deviation(_chart_view(chart), row["anchors"]), 2),
                "zigzag_rate": zig["candidate"],
                "chart_zigzag_rate": zig["chart"],
                "zigzag_gap": zig["gap"],
                "gap": g["gap"],
                "chart_naturalness": g["chart"]["naturalness"],
                "row_naturalness": g["candidate"]["naturalness"],
                "component_gap": comp_gap,
                "applicable": g["candidate"]["applicable"],
            }
        )
    trusted = [r["spike_ratio"] for r in rows if r["n_occurrences"] >= LAUFFORM_MIN_OCCURRENCES]
    tau = math.ceil(max(trusted) * 100.0) / 100.0 if trusted else None
    rows.sort(key=lambda r: -r["spike_ratio"])
    return rows, tau


def print_table(rows: list[dict], tau: float | None) -> None:
    head_max = LAUFFORM_HEAD_DEVIATION_MAX
    head = (
        f"{'key':6s} {'n':>3s} {'spike':>6s} {'chart':>6s} {'head°':>6s} {'zig':>6s} {'chart':>6s}   "
        f"{'Δ nat':>7s}  smooth  vert   corner cross   gates"
    )
    print(head)
    for r in rows:
        cg = r["component_gap"]
        flags = []
        if tau is not None and r["spike_ratio"] > tau:
            flags.append("über τ")
        if head_max is not None and r["head_deviation"] > head_max:
            flags.append("Kopf")
        flag = f"  ← {' · '.join(flags)}" if flags else ""
        print(
            f"{r['glyph_key']:6s} {r['n_occurrences']:3d} {r['spike_ratio']:6.2f} {r['chart_spike_ratio']:6.2f} "
            f"{r['head_deviation']:6.1f} {r['zigzag_rate']:6.2f} {r['chart_zigzag_rate']:6.2f}   "
            f"{r['gap']:+7.4f}  {cg['smoothness']:+.3f} {cg['verticality']:+.3f} "
            f"{cg['corner']:+.3f} {cg['collinearity']:+.3f}{flag}"
        )
    trusted = [r for r in rows if r["n_occurrences"] >= LAUFFORM_MIN_OCCURRENCES]
    print(
        f"τ (max spike ratio over the {len(trusted)} rows with n ≥ {LAUFFORM_MIN_OCCURRENCES}, ceil 0.01): "
        f"{'—' if tau is None else f'{tau:.2f}'}"
    )
    if tau is not None:
        over = [r["glyph_key"] for r in rows if r["spike_ratio"] > tau]
        print(f"rows over τ: {', '.join(over) if over else 'none'}")
    if head_max is not None:
        turned = [f"{r['glyph_key']} {r['head_deviation']:.1f}°" for r in rows if r["head_deviation"] > head_max]
        print(f"rows over the head gate ({head_max:.0f}°, LF9): {', '.join(turned) if turned else 'none'}")


def draw(root: Path, rows: list[dict], only: set[str] | None, out: Path) -> None:
    """One panel per selected row: chart (grey) under the Laufform (red)."""
    import matplotlib  # noqa: PLC0415 — viz extra, dev-only

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: PLC0415

    templates = json.loads((root / "templates.json").read_text())
    stored = json.loads((root / "templates_laufform.json").read_text())
    picked = [r for r in rows if only is None or r["glyph_key"] in only]
    if not picked:
        raise SystemExit("nothing to draw")
    cols = min(4, len(picked))
    n_rows = (len(picked) + cols - 1) // cols
    fig, axes = plt.subplots(n_rows, cols, figsize=(4.2 * cols, 4.6 * n_rows), squeeze=False)
    for ax in axes.flat:
        ax.axis("off")
    for ax, r in zip(axes.flat, picked, strict=False):
        key = r["glyph_key"]
        ca, la = templates[key]["anchors"], stored[key]["anchors"]
        ax.axis("on")
        ax.plot([p[0] for p in ca], [p[1] for p in ca], "-", color="0.6", lw=3, alpha=0.7, label="Tafel")
        ax.plot([p[0] for p in la], [p[1] for p in la], "-", color="tab:red", lw=1.2, label="Laufform")
        ax.plot([p[0] for p in la], [p[1] for p in la], ".", color="tab:red", ms=2)
        for y in (0.0, 1.0):
            ax.axhline(y, color="0.85", lw=0.5)
        ax.set_aspect("equal")
        ax.set_title(f"{key}  n={r['n_occurrences']}  spike {r['spike_ratio']:.2f}  Δ={r['gap']:+.3f}", fontsize=10)
        ax.tick_params(labelsize=7)
    axes.flat[0].legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f"wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="fixture root (default: the frozen words root)")
    ap.add_argument("--json", type=Path, default=None, help="write the table + τ as JSON")
    ap.add_argument("--png", type=Path, default=None, help="draw the selected rows over their chart forms")
    ap.add_argument("--only", default=None, help="comma-separated glyph keys for --png (default: all rows)")
    args = ap.parse_args()

    rows, tau = inventory(args.root)
    print_table(rows, tau)
    if args.json:
        args.json.write_text(
            json.dumps({"root": args.root.name, "tau": tau, "rows": rows}, ensure_ascii=False, indent=1)
        )
        print(f"wrote {args.json}")
    if args.png:
        draw(args.root, rows, set(args.only.split(",")) if args.only else None, args.png)


if __name__ == "__main__":
    main()
