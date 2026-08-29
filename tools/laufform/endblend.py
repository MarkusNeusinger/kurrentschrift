"""Build an LF5 end-blend candidate map from a frozen wordbench fixture root.

Measurement layer only (docs/reference/werkzeuge.md): reads `templates.json`
(chart rows) + `templates_laufform.json` (the stored running forms) of ONE
fixture root and writes the rows the write path WOULD produce when every stored
row is re-derived through `build_laufform_canonical` with the end blend at the
given window — full fixture rows, so `wordbench.run --laufform` and
`wordlab --laufform` take them verbatim (no second derivation, no double blend).

    uv run python -m tools.laufform.endblend --window 0.25 --out cand-w025.json
    uv run python -m tools.laufform.endblend --window 0.25 --chart-fallback K --out cand-w025-k0.json

`--chart-fallback KEY` (repeatable) writes the CHART row for that key instead —
composition-identical to having no Laufform row at all (the composer takes the
chart payload either way; LAUFFORM_SX has no entry for these keys) — the K0 arm
of the LF5/LF6 pre-registrations. `--window 0` copies the stored rows VERBATIM
(so a K0 map moves nothing but the fallback keys); `--full-blend` selects the
LF5 full cross-fade instead of the LF6 transverse-only default. Both rungs of
both modes were REJECTED on the frozen word ruler (qualitaetsmetrik.md §14
`aug29`) — the tool stays so the arms remain reproducible. Never writes to the
DB or the fixture root.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from tools.wordbench.fetch_fixtures import laufform_row_from_payload


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "tools" / "wordbench" / "fixtures" / "suetterlin" / "suetterlin-1922"


def _max_move(a: list[list[float]], b: list[list[float]]) -> float:
    return max(math.hypot(p[0] - q[0], p[1] - q[1]) for p, q in zip(a, b, strict=True))


def build_candidates(
    root: Path, window: float, chart_fallback: set[str] | None = None, *, transverse_only: bool = True
) -> tuple[dict[str, dict], list[str]]:
    """Every stored Laufform row of `root`, re-derived with the end blend.

    A window of 0 copies the stored rows VERBATIM (no re-derivation, so not
    even a rounding pass moves a row) — the pure chart-fallback arm. Returns the
    candidate rows keyed by glyph_key and one report line per key (max anchor
    move against the stored row, the end pieces' moves).
    """
    templates = json.loads((root / "templates.json").read_text())
    stored = json.loads((root / "templates_laufform.json").read_text())
    fallback = chart_fallback or set()
    rows: dict[str, dict] = {}
    report: list[str] = []
    for key in sorted(stored):
        chart = templates.get(key)
        if chart is None:
            report.append(f"  skip {key}: no chart row in the root")
            continue
        old = stored[key]
        meta = dict((old.get("trace_meta") or {}).get("laufform") or {})
        if key in fallback:
            meta = {"derived_from": "chart-fallback", "n_occurrences": 0}
            row = laufform_row_from_payload(chart, chart["anchors"], meta, end_window=0.0)
            rows[key] = row
            report.append(f"  {key:6s} chart-fallback (K0 arm): row == chart")
            continue
        if window <= 0.0:
            rows[key] = old
            report.append(f"  {key:6s} verbatim (window 0)")
            continue
        row = laufform_row_from_payload(chart, old["anchors"], meta, end_window=window, transverse_only=transverse_only)
        rows[key] = row
        move = _max_move(row["anchors"], old["anchors"])
        head = math.hypot(*(row["anchors"][0][i] - old["anchors"][0][i] for i in (0, 1)))
        tail = math.hypot(*(row["anchors"][-1][i] - old["anchors"][-1][i] for i in (0, 1)))
        report.append(
            f"  {key:6s} n={meta.get('n_occurrences', '?'):>2}  max move {move:.3f} xh  "
            f"head {head:.3f}  tail {tail:.3f}  advance {old.get('advance', 0):.3f} → {row['advance']:.3f}"
        )
    return rows, report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="fixture root (default: the frozen words root)")
    ap.add_argument("--window", type=float, required=True, help="end-blend window in x-height units (0 = off)")
    ap.add_argument("--chart-fallback", action="append", default=[], metavar="KEY", help="emit the chart row for KEY")
    ap.add_argument(
        "--full-blend",
        action="store_true",
        help="LF5 mode: cross-fade the whole end residual (default: LF6, transverse component only)",
    )
    ap.add_argument("--out", type=Path, required=True, help="candidate map (glyph_key -> full fixture row)")
    args = ap.parse_args()

    rows, report = build_candidates(
        args.root, args.window, set(args.chart_fallback), transverse_only=not args.full_blend
    )
    args.out.write_text(json.dumps(rows, ensure_ascii=False))
    print(f"endblend window={args.window} root={args.root.name}: {len(rows)} candidate rows → {args.out}")
    print("\n".join(report))


if __name__ == "__main__":
    main()
