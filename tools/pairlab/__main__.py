"""pairlab CLI — dissect real occurrences of letter pairs join by join.

Examples:
    # every real occurrence of r→e in the Abb.-19 words + Abb.-20 pairs
    uv run --extra viz python -m tools.pairlab re

    # several pairs, capped at 4 occurrences each, plus a JSON dump
    uv run --extra viz python -m tools.pairlab re en er nn --max-occ 4 --json temp/pairs.json

    # multi-char glyph bases (long s, umlauts) comma-separated
    uv run --extra viz python -m tools.pairlab longs,e ue,b

    # whole-word overlays instead of the default join close-up
    uv run --extra viz python -m tools.pairlab re --full-word

Output goes to $PAIRLAB_OUT (else the project temp/ dir); paths are printed.
One PNG per pair: rows = occurrences, columns = overlay + deviation profile.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

from tools.wordlab.cases import REPO_ROOT

from .analyze import dissect_occurrence, find_occurrences, pair_bases, summary_row
from .render import overlay_panel, profile_panel, save, tile


PANEL_SIZE = 4.2


def _default_out_dir() -> Path:
    env = os.environ.get("PAIRLAB_OUT")
    return Path(env) if env else REPO_ROOT / "temp"


def _deg(value: float | None) -> str:
    """Real-tangent column: signed degrees, or an em dash when untrackable."""
    return "—" if value is None else f"{value:+.0f}°"


def _print_summary(rows: list[dict]) -> None:
    for r in rows:
        print(
            f"  {r['id']:<14} [{r['kind']}]{'!' if r['at_bound'] else ' '} "
            f"A {r['a_shift_units'][0]:+.2f},{r['a_shift_units'][1]:+.2f}  "
            f"B {r['b_shift_units'][0]:+.2f},{r['b_shift_units'][1]:+.2f}  "
            f"gen {r['gen_chamfer']:.3f}  tail {r['tail_adapt']:.2f}  head {r['head_adapt']:.2f}  "
            f"exit {r['exit_deg']:+.0f}°/{_deg(r['real_exit_deg'])}  "
            f"entry {r['entry_deg']:+.0f}°/{_deg(r['real_entry_deg'])}"
            + (
                f"  fit exit y{r['target_exit_y']:+.2f}@{r['target_exit_deg']:+.0f}°"
                f" entry y{r['target_entry_y']:+.2f}@{r['target_entry_deg']:+.0f}°"
                f"{'' if r['trace_converged'] else ' (FAIL)'}"
                if r.get("target_exit_y") is not None and r.get("target_entry_y") is not None
                else ""
            )
        )
    if len(rows) > 1:
        tails = [r["tail_adapt"] for r in rows]
        heads = [r["head_adapt"] for r in rows]
        gens = [r["gen_chamfer"] for r in rows]
        print(
            f"  median          tail {np.median(tails):.2f}  head {np.median(heads):.2f}  "
            f"gen {np.median(gens):.3f}  (n={len(rows)})"
        )


def main() -> None:
    p = argparse.ArgumentParser(
        prog="pairlab", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("pairs", nargs="+", help="letter pairs: 're', or comma form 'longs,e' for multi-char bases")
    p.add_argument(
        "--set",
        dest="which",
        choices=["words", "pairs", "all"],
        default="all",
        help="fixture sets to search (default: all)",
    )
    p.add_argument("--style", default="suetterlin", help="fixture style dir (default: suetterlin)")
    p.add_argument("--max-occ", type=int, default=6, help="occurrences rendered per pair (default 6; 0 = all)")
    p.add_argument("--full-word", action="store_true", help="show the whole word instead of the pair close-up")
    p.add_argument(
        "--no-trace",
        action="store_true",
        help="skip the ductus traces (M4 fit of both templates onto the real ink; adds ~1–2 s per letter)",
    )
    p.add_argument("--json", type=Path, help="write all summary rows here")
    p.add_argument("--dpi", type=int, default=140, help="output resolution (default 140)")
    p.add_argument("--out-dir", default=None, help="output directory (default: $PAIRLAB_OUT or project temp/)")
    args = p.parse_args()

    sets = ("words", "pairs") if args.which == "all" else (args.which,)
    out_dir = Path(args.out_dir) if args.out_dir else _default_out_dir()
    all_rows: list[dict] = []

    for pair_arg in args.pairs:
        bases = pair_bases(pair_arg)
        occurrences = find_occurrences(bases, sets=sets, style=args.style)
        label = f"{bases[0]}→{bases[1]}"
        if not occurrences:
            print(f"{label}: no scorable occurrence in {'/'.join(sets)}")
            continue
        if args.max_occ:
            occurrences = occurrences[: args.max_occ]
        print(f"{label}: {len(occurrences)} occurrence(s)")

        draws = []
        rows = []
        for case, slot_a in occurrences:
            d = dissect_occurrence(case, slot_a, trace=not args.no_trace)
            if d is None:
                print(f"  {case.id:<14} SKIP (missing template / unscorable)")
                continue
            rows.append(summary_row(d))
            draws.append(overlay_panel(d, zoom=not args.full_word))
            draws.append(profile_panel(d))
        _print_summary(rows)
        all_rows.extend(rows)
        if draws:
            fig = tile(draws, cols=2, panel_size=PANEL_SIZE, dpi=args.dpi)
            name = f"pairlab_{bases[0]}_{bases[1]}"
            print(f"  wrote {save(fig, name, out_dir=out_dir)}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(all_rows, indent=1, ensure_ascii=False))
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
