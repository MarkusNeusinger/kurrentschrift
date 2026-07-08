"""wordlab CLI — render composed-word overlays to a PNG you can open.

Examples:
    # three words over their specimens, with per-connector penalty callouts
    python -m tools.wordlab Einen zu wenn-2

    # a letter-pair from Abb. 20 (the isolated-join set)
    python -m tools.wordlab bs on --set pairs

    # every word of the set, one per row
    python -m tools.wordlab --all

    # colour the connectors green→red by penalty instead of flat red
    python -m tools.wordlab Einen --heatmap

    # sweep one compose constant across values for ONE word (one column each)
    python -m tools.wordlab Einen --sweep core.compose.INK_CLEARANCE=0.10,0.14,0.18

    # compose LIVE from the DB (read-only) — any text, no specimen to score
    python -m tools.wordlab "unser Haus" --live --source suetterlin-1922

Output goes to $WORDLAB_OUT (else the project temp/ dir); the path is printed.
On WSL, point it at Windows to view: WORDLAB_OUT=/mnt/c/Users/<you>/Desktop/wordlab
"""

from __future__ import annotations

import argparse
import importlib
import os
import re
from pathlib import Path

from tools.glyphlab.__main__ import parse_sweep
from tools.glyphlab.render import save, tile

from .cases import REPO_ROOT, WordCase, fixture_word_case, iter_fixture_word_cases, live_word_case_sync
from .derive import WordDeriveResult, derive_word
from .render import word_panel


# Word panels are wide (a word crop is ~5:1), so montages default to a single
# column with a tall-ish panel; two side by side is the most that stays legible.
PANEL_SIZE = 4.5


def _default_out_dir() -> Path:
    env = os.environ.get("WORDLAB_OUT")
    return Path(env) if env else REPO_ROOT / "temp"


def _safe_name(name: str) -> str:
    """Filesystem-safe filename stem — a --live case id is raw user text
    (spaces, '/', shell metacharacters), and $WORDLAB_OUT may be a Windows
    mount where even more characters are invalid."""
    return re.sub(r"[^\w.\-]+", "_", name) or "word"


def _resolve_cases(args: argparse.Namespace) -> list[WordCase]:
    if args.all:
        return iter_fixture_word_cases(which=args.which, style=args.style, only=args.ids or None)
    if not args.ids:
        raise SystemExit("give one or more word ids/texts, or --all")
    if args.live:
        return [live_word_case_sync(t, args.source) for t in args.ids]
    return [fixture_word_case(i, which=args.which, style=args.style) for i in args.ids]


def _summary(result: WordDeriveResult) -> str:
    """One stdout line per case: id, loss, penalties, worst connector."""
    report = result.report
    if report is None:
        missing = result.composed["missing"]
        tail = f"  missing {missing}" if missing else ""
        return f"{result.case.id:<16} live (no specimen){tail}"
    if report.get("failed"):
        return f"{result.case.id:<16} FAILED  missing {report.get('missing')}"
    worst = max(
        (s for s in (result.segments or []) if s["kind"] == "connector"), key=lambda s: s["penalty"], default=None
    )
    from .render import _seg_label  # noqa: PLC0415 — label helper, kept next to the panel

    worst_txt = f"{_seg_label(worst)} {worst['penalty']:.2f}" if worst else "-"
    return (
        f"{result.case.id:<16} loss {report['loss']:.3f}  "
        f"trans {report['transition']:.3f} cover {report['coverage']:.3f} width {report['width']:.3f}  "
        f"worst {worst_txt}"
    )


def _run_sweep(args: argparse.Namespace, out_dir: Path) -> None:
    """Compose ONE word across several values of a module-level constant (columns).

    The constant is patched in place, the word re-derived per value, then the
    ORIGINAL value is ALWAYS restored in a `finally` so the live module is left
    untouched (mirrors glyphlab's `_run_sweep`).
    """
    if len(args.ids) != 1:
        raise SystemExit("--sweep renders exactly ONE word id; give a single id")
    module_path, attr, values = parse_sweep(args.sweep)
    module = importlib.import_module(module_path)
    if not hasattr(module, attr):
        raise SystemExit(f"--sweep: {module_path!r} has no attribute {attr!r}")
    case = _resolve_cases(args)[0]

    original = getattr(module, attr)
    draws = []
    try:
        for value in values:
            setattr(module, attr, value)
            result = derive_word(case)
            print(_summary(result) + f"   [{attr}={value:g}]")
            draws.append(
                word_panel(
                    result,
                    title=f"{case.id} · {attr}={value:g}",
                    callouts=not args.no_callouts,
                    heatmap=args.heatmap,
                    skeleton=not args.no_skeleton,
                )
            )
    finally:
        setattr(module, attr, original)  # never leave the patched constant behind

    cols = args.cols or len(draws)  # one column per swept value
    fig = tile(draws, cols=cols, panel_size=PANEL_SIZE, dpi=args.dpi)
    name = args.out or f"sweep_{_safe_name(case.id)}_{attr}"
    print(f"wrote {save(fig, name, out_dir=out_dir)}  ({len(draws)} panel(s))")


def main() -> None:
    p = argparse.ArgumentParser(
        prog="wordlab", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("ids", nargs="*", help="fixture word ids/words, or texts with --live")
    p.add_argument("--all", action="store_true", help="all words of the set (optionally filtered by ids)")
    p.add_argument(
        "--set", dest="which", choices=["words", "pairs"], default="words", help="fixture set (default: words)"
    )
    p.add_argument("--live", action="store_true", help="compose from the DB (read-only) instead of a fixture")
    p.add_argument("--source", default="suetterlin-1922", help="source id for --live (default: suetterlin-1922)")
    p.add_argument("--style", default="suetterlin", help="fixture style dir (default: suetterlin)")
    p.add_argument("--no-callouts", action="store_true", help="hide the per-connector penalty callouts")
    p.add_argument("--heatmap", action="store_true", help="colour connectors green→red by penalty")
    p.add_argument("--no-skeleton", action="store_true", help="hide the blue specimen skeleton")
    p.add_argument(
        "--zoom-x",
        default=None,
        metavar="LO,HI",
        help="crop the view to this horizontal fraction of the crop, e.g. 0.4,0.8 (join close-up)",
    )
    p.add_argument(
        "--sweep",
        default=None,
        metavar="DOTTED.PATH=v1,v2,...",
        help="compose ONE word across values of a module constant, e.g. core.compose.INK_CLEARANCE=0.10,0.14,0.18",
    )
    p.add_argument(
        "--cols",
        type=int,
        default=None,
        help="montage columns (default: 1–2 words side by side, >2 words stacked; one column per sweep value)",
    )
    p.add_argument("--dpi", type=int, default=140, help="output resolution (default 140)")
    p.add_argument("--out", default=None, help="output filename (default: derived from ids)")
    p.add_argument("--out-dir", default=None, help="output directory (default: $WORDLAB_OUT or project temp/)")
    args = p.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else _default_out_dir()
    if args.sweep:
        _run_sweep(args, out_dir)
        return

    zoom_x = None
    if args.zoom_x:
        lo, _, hi = args.zoom_x.partition(",")
        try:
            zoom_x = (float(lo), float(hi))
        except ValueError:
            raise SystemExit(f"--zoom-x needs LO,HI fractions, got {args.zoom_x!r}") from None
        if not (0.0 <= zoom_x[0] < zoom_x[1] <= 1.0):
            raise SystemExit(f"--zoom-x fractions must satisfy 0 <= LO < HI <= 1, got {args.zoom_x!r}")

    cases = _resolve_cases(args)
    draws = []
    for case in cases:
        result = derive_word(case)
        print(_summary(result))
        draws.append(
            word_panel(
                result,
                title=f"{case.id} [{case.origin}]",
                callouts=not args.no_callouts,
                heatmap=args.heatmap,
                skeleton=not args.no_skeleton,
                zoom_x=zoom_x,
            )
        )

    # Word panels are wide (a crop is ~5:1), so stack >2 in a single column
    # (each gets the full width); one or two sit side by side.
    cols = args.cols or (1 if len(draws) > 2 else min(2, len(draws)))
    fig = tile(draws, cols=cols, panel_size=PANEL_SIZE, dpi=args.dpi)
    name = args.out or ("wordlab_" + "_".join(_safe_name(c.id) for c in cases[:4]))
    print(f"wrote {save(fig, name, out_dir=out_dir)}  ({len(draws)} panel(s))")


if __name__ == "__main__":
    main()
