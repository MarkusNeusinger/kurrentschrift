"""Inventory of the stored Laufform rows against their chart forms (LF7–LF10) —
the „Bestandsaufnahme" of qualitaetsmetrik.md §14.

Measurement layer only (docs/reference/werkzeuge.md): reads `templates.json`
(chart rows) + `templates_laufform.json` (the stored running forms) of ONE
fixture root and prints, per row, the ROW GATE quantity — the anchor spike
ratio (`core.laufform.anchor_spike_ratio`, „Anker im leeren Papier", measured
on the row over the chart's stroke starts; LF8) — beside the report columns of
LF7 (the geometry-only naturalness of chart and row and their gap Δ) and the
row's evidence count, the HEAD GATE quantity of LF9 — the row's head
deviation (`core.laufform.head_deviation`: how far the first stroke's landing
direction turns away from the chart's, in degrees) — and the FORM DISTANCE of
LF10 (`core.laufform.form_distance`: per anchor the distance to the other
side's rendered centerline of the same stroke, in chart nib radii, both
directions; the column `form` is the worse directional p90, `f-med` the worse
median). The pre-registered gate rules are applied on top: τ = the largest
spike ratio among the rows with n ≥ LAUFFORM_MIN_OCCURRENCES, rounded up to
0.01, the doctrine-derived head gate LAUFFORM_HEAD_DEVIATION_MAX, and τ_form =
the largest form p90 among the same trusted rows, rounded up to 0.01 (LF10 —
measured, not adopted: no write path reads it); every row over any of them is
listed — those are the rows the author decides about.

    uv run python -m tools.laufform.inventory [--root DIR] [--json out.json]
    uv run --extra viz python -m tools.laufform.inventory --png inventory.png [--only K,t,E]
    uv run python -m tools.laufform.inventory --laufform drafts.json

`--laufform` measures CANDIDATE rows over the root's chart rows — a harvest
draft file, a row backup, an extraction from an archive snapshot — in the
harvest-draft shape `{key: {anchors, n_occurrences}}` (the same file
`wordbench.run --laufform` takes). Candidates are listed with `*` beside the
stored rows and never join the trusted population: every τ is derived from the
stored rows alone. `--png` draws each selected row over its chart form
(anchors, both in template units; the row's anchors at or above its own form
p90 marked black) — the picture the word ruler never looks at. Never writes
to the DB or the fixture root.
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
    form_distance,
    head_deviation,
    naturalness_gap,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "tools" / "wordbench" / "fixtures" / "suetterlin" / "suetterlin-1922"

# The pre-registered sensitivity checks of LF10 (qualitaetsmetrik.md §14
# `sep01`), each a variant of the gate quantity — reported with its own τ,
# never a gate: (a) median · (b) maximum · (c) one direction only · (d) the
# index-wise correspondence distance · (e) any stroke · (f) anchor polyline.
FORM_VARIANTS = ("p90", "median", "max", "row_to_chart", "chart_to_row", "correspondence", "any_stroke", "polyline")


def _chart_view(chart: dict) -> SimpleNamespace:
    return SimpleNamespace(
        anchors=chart["anchors"], half_widths=chart["half_widths"], trace_meta=chart.get("trace_meta") or {}
    )


def _form_columns(chart: dict, anchors: list) -> dict:
    """The LF10 gate quantity plus every pre-registered variant of it."""
    view = _chart_view(chart)
    f = form_distance(view, anchors)
    ranges_hint = f["p90_direction"]
    worst = f[ranges_hint]["argmax"]
    starts = sorted({0, *((chart.get("trace_meta") or {}).get("stroke_starts") or [0])})
    stroke = sum(1 for s in starts if s <= worst) - 1
    return {
        "form": {
            "p90": f["p90"],
            "median": f["median"],
            "max": f["max"],
            "row_to_chart": f["row_to_chart"]["p90"],
            "chart_to_row": f["chart_to_row"]["p90"],
            "correspondence": f["correspondence"]["p90"],
            "any_stroke": form_distance(view, anchors, same_stroke=False)["p90"],
            "polyline": form_distance(view, anchors, rendered=False)["p90"],
            "direction": ranges_hint,
            "worst_anchor": worst,
            "worst_stroke": stroke,
            "nib_radius": f["nib_radius"],
            "row_to_chart_values": f["row_to_chart"]["values"],
            "chart_to_row_values": f["chart_to_row"]["values"],
        }
    }


def _row_record(key: str, chart: dict, anchors: list, n: int, *, candidate: bool) -> dict:
    starts = (chart.get("trace_meta") or {}).get("stroke_starts")
    g = naturalness_gap(_chart_view(chart), anchors)
    comp_gap = {
        k: round(g["candidate"]["components"][k] - g["chart"]["components"][k], 4) for k in g["chart"]["components"]
    }
    return {
        "glyph_key": key,
        "candidate": candidate,
        "n_occurrences": n,
        "spike_ratio": round(anchor_spike_ratio(anchors, starts), 4),
        "chart_spike_ratio": round(anchor_spike_ratio(chart["anchors"], starts), 4),
        "head_deviation": round(head_deviation(_chart_view(chart), anchors), 2),
        "gap": g["gap"],
        "chart_naturalness": g["chart"]["naturalness"],
        "row_naturalness": g["candidate"]["naturalness"],
        "component_gap": comp_gap,
        "applicable": g["candidate"]["applicable"],
        **_form_columns(chart, anchors),
    }


def _ceil_2(value: float) -> float:
    return math.ceil(value * 100.0) / 100.0


def inventory(root: Path, candidates: dict | None = None) -> tuple[list[dict], dict]:
    """Per stored row: n, spike ratio (row and chart), head deviation,
    naturalness gap and the LF10 form distance; plus the taus.

    `candidates` are extra rows in the harvest-draft shape, measured over the
    root's chart rows and flagged `candidate`; they never enter a τ. Returns
    the rows sorted by form p90 (largest first) and a dict of taus: `spike`
    (LF8), `form` (LF10, the gate quantity) and one per variant in
    FORM_VARIANTS — each None when the root holds no row at or above the
    evidence floor (then there is no trusted population to derive a gate from,
    and the rule says so instead of guessing).
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
        rows.append(_row_record(key, chart, row["anchors"], int(meta.get("n_occurrences") or 0), candidate=False))
    for key in sorted(candidates or {}):
        chart = templates.get(key)
        if chart is None:
            continue
        draft = candidates[key]
        rows.append(_row_record(key, chart, draft["anchors"], int(draft.get("n_occurrences") or 0), candidate=True))
    trusted = [r for r in rows if not r["candidate"] and r["n_occurrences"] >= LAUFFORM_MIN_OCCURRENCES]
    taus: dict[str, float | None] = {
        "spike": _ceil_2(max(r["spike_ratio"] for r in trusted)) if trusted else None,
        "form": _ceil_2(max(r["form"]["p90"] for r in trusted)) if trusted else None,
    }
    for variant in FORM_VARIANTS:
        taus[f"form_{variant}"] = _ceil_2(max(r["form"][variant] for r in trusted)) if trusted else None
    rows.sort(key=lambda r: -r["form"]["p90"])
    return rows, taus


def _flags(r: dict, taus: dict) -> list[str]:
    flags = []
    if taus["spike"] is not None and r["spike_ratio"] > taus["spike"]:
        flags.append("über τ")
    if LAUFFORM_HEAD_DEVIATION_MAX is not None and r["head_deviation"] > LAUFFORM_HEAD_DEVIATION_MAX:
        flags.append("Kopf")
    if taus["form"] is not None and r["form"]["p90"] > taus["form"]:
        flags.append("Form")
    return flags


def print_table(rows: list[dict], taus: dict) -> None:
    head_max = LAUFFORM_HEAD_DEVIATION_MAX
    print(
        f"{'key':7s} {'n':>3s} {'spike':>6s} {'chart':>6s} {'head°':>6s} {'form':>6s} {'f-med':>6s} {'f-max':>6s} "
        f"dir   {'Δ nat':>7s}  smooth  vert   corner cross   gates"
    )
    for r in rows:
        cg = r["component_gap"]
        f = r["form"]
        flags = _flags(r, taus)
        flag = f"  ← {' · '.join(flags)}" if flags else ""
        key = f"{r['glyph_key']}{'*' if r['candidate'] else ''}"
        direction = "Z→T" if f["direction"] == "row_to_chart" else "T→Z"
        print(
            f"{key:7s} {r['n_occurrences']:3d} {r['spike_ratio']:6.2f} {r['chart_spike_ratio']:6.2f} "
            f"{r['head_deviation']:6.1f} {f['p90']:6.2f} {f['median']:6.2f} {f['max']:6.2f} {direction}   "
            f"{r['gap']:+7.4f}  {cg['smoothness']:+.3f} {cg['verticality']:+.3f} "
            f"{cg['corner']:+.3f} {cg['collinearity']:+.3f}{flag}"
        )
    trusted = [r for r in rows if not r["candidate"] and r["n_occurrences"] >= LAUFFORM_MIN_OCCURRENCES]
    n_trusted = len(trusted)
    tau = taus["spike"]
    print(
        f"τ (max spike ratio over the {n_trusted} stored rows with n ≥ {LAUFFORM_MIN_OCCURRENCES}, ceil 0.01): "
        f"{'—' if tau is None else f'{tau:.2f}'}"
    )
    if tau is not None:
        over = [r["glyph_key"] for r in rows if r["spike_ratio"] > tau]
        print(f"rows over τ: {', '.join(over) if over else 'none'}")
    if head_max is not None:
        turned = [f"{r['glyph_key']} {r['head_deviation']:.1f}°" for r in rows if r["head_deviation"] > head_max]
        print(f"rows over the head gate ({head_max:.0f}°, LF9): {', '.join(turned) if turned else 'none'}")
    tau_form = taus["form"]
    if tau_form is not None:
        setter = max(trusted, key=lambda r: r["form"]["p90"])
        fs = setter["form"]
        direction = "Zeile→Tafel" if fs["direction"] == "row_to_chart" else "Tafel→Zeile"
        print(
            f"τ_form (max form p90 over the same {n_trusted} rows, ceil 0.01, LF10): {tau_form:.2f} — set by "
            f"{setter['glyph_key']} ({fs['p90']:.2f} nib radii, {direction}, worst anchor {fs['worst_anchor']} "
            f"in stroke {fs['worst_stroke']})"
        )
        over_form = [
            f"{r['glyph_key']}{'*' if r['candidate'] else ''} {r['form']['p90']:.2f}"
            for r in rows
            if r["form"]["p90"] > tau_form
        ]
        print(f"rows over τ_form: {', '.join(over_form) if over_form else 'none'}")
        print("LF10 sensitivity (variant: τ_variant · rows over it):")
        for variant in FORM_VARIANTS:
            t = taus[f"form_{variant}"]
            over_v = [
                f"{r['glyph_key']}{'*' if r['candidate'] else ''} {r['form'][variant]:.2f}"
                for r in rows
                if r["form"][variant] > t
            ]
            print(f"  {variant:>14s}: {t:.2f} · {', '.join(over_v) if over_v else 'none'}")
    else:
        print("τ_form: — (no stored row at or above the evidence floor)")


def draw(root: Path, rows: list[dict], only: set[str] | None, out: Path, candidates: dict | None = None) -> None:
    """One panel per selected row: chart (grey) under the Laufform (red); the
    row's anchors at or above its own form p90 are marked black."""
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
        ca = templates[key]["anchors"]
        la = (candidates or {})[key]["anchors"] if r["candidate"] else stored[key]["anchors"]
        ax.axis("on")
        ax.plot([p[0] for p in ca], [p[1] for p in ca], "-", color="0.6", lw=3, alpha=0.7, label="Tafel")
        ax.plot([p[0] for p in la], [p[1] for p in la], "-", color="tab:red", lw=1.2, label="Laufform")
        ax.plot([p[0] for p in la], [p[1] for p in la], ".", color="tab:red", ms=2)
        values = r["form"]["row_to_chart_values"]
        threshold = r["form"]["row_to_chart"]
        far = [p for p, v in zip(la, values, strict=True) if v >= threshold]
        if far:
            ax.plot([p[0] for p in far], [p[1] for p in far], "o", color="black", ms=3, label="≥ p90")
        for y in (0.0, 1.0):
            ax.axhline(y, color="0.85", lw=0.5)
        ax.set_aspect("equal")
        ax.set_title(
            f"{key}{'*' if r['candidate'] else ''}  n={r['n_occurrences']}  spike {r['spike_ratio']:.2f}  "
            f"form {r['form']['p90']:.2f}",
            fontsize=10,
        )
        ax.tick_params(labelsize=7)
    axes.flat[0].legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f"wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="fixture root (default: the frozen words root)")
    ap.add_argument("--json", type=Path, default=None, help="write the table + taus as JSON")
    ap.add_argument("--png", type=Path, default=None, help="draw the selected rows over their chart forms")
    ap.add_argument("--only", default=None, help="comma-separated glyph keys for --png (default: all rows)")
    ap.add_argument(
        "--laufform",
        type=Path,
        default=None,
        help="candidate rows to measure beside the stored ones ({key: {anchors, n_occurrences}}); never enter a τ",
    )
    args = ap.parse_args()

    candidates = json.loads(args.laufform.read_text()) if args.laufform else None
    rows, taus = inventory(args.root, candidates)
    print_table(rows, taus)
    if args.json:
        args.json.write_text(
            json.dumps({"root": args.root.name, "taus": taus, "rows": rows}, ensure_ascii=False, indent=1)
        )
        print(f"wrote {args.json}")
    if args.png:
        draw(args.root, rows, set(args.only.split(",")) if args.only else None, args.png, candidates)


if __name__ == "__main__":
    main()
