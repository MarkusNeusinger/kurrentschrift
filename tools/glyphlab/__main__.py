"""glyphlab CLI — render glyph derivation overlays to a PNG you can open.

Examples:
    # final overlay (centerline + silhouette + corners) for a few fixtures
    python -m tools.glyphlab i-initial u-initial n-initial

    # every Sütterlin form, anchor-dot style (as the admin shows them)
    python -m tools.glyphlab --all --style dots

    # the four derivation stages of one glyph, side by side
    python -m tools.glyphlab i-initial --stages

    # the live (DB) trace instead of the frozen fixture (read-only)
    python -m tools.glyphlab i-initial --live --source suetterlin-1922

Output goes to $GLYPHLAB_OUT (else the project temp/ dir); the path is printed.
On WSL, point it at Windows to view: GLYPHLAB_OUT=/mnt/c/Users/<you>/Desktop/glyphlab
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .cases import GlyphCase, fixture_case, iter_fixture_cases, live_case_sync
from .derive import derive, derive_stages
from .render import GREEN, figure, panel, save, stage_panels


def _resolve_cases(args: argparse.Namespace) -> list[GlyphCase]:
    if args.all:
        return iter_fixture_cases(only=args.keys or None)
    if not args.keys:
        raise SystemExit("give one or more glyph_keys, or --all")
    if args.live:
        return [live_case_sync(args.source, k) for k in args.keys]
    return [fixture_case(k) for k in args.keys]


def main() -> None:
    p = argparse.ArgumentParser(
        prog="glyphlab", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("keys", nargs="*", help="glyph_keys, e.g. i-initial u-medial")
    p.add_argument("--all", action="store_true", help="all fixture forms (optionally filtered by keys)")
    p.add_argument("--live", action="store_true", help="read the trace from the DB (read-only) instead of the fixture")
    p.add_argument("--source", default="suetterlin-1922", help="source id for --live (default: suetterlin-1922)")
    p.add_argument("--stages", action="store_true", help="show snap/smooth/resample/verticalize (Gleichzug only)")
    p.add_argument("--style", choices=["spline", "dots", "line"], default="spline", help="centerline style")
    p.add_argument("--no-silhouette", action="store_true", help="hide the filled stroke body")
    p.add_argument("--no-skeleton", action="store_true", help="hide the skeleton")
    p.add_argument("--n-anchors", type=int, default=None, help="resample target (default: per-bbox / pipeline default)")
    p.add_argument("--dpi", type=int, default=140, help="output resolution (default 140)")
    p.add_argument("--cols", type=int, default=None, help="montage columns (default: all in one row)")
    p.add_argument("--out", default=None, help="output filename (default: derived from keys)")
    p.add_argument("--out-dir", default=None, help="output directory (default: $GLYPHLAB_OUT or project temp/)")
    args = p.parse_args()

    cases = _resolve_cases(args)
    out_dir = Path(args.out_dir) if args.out_dir else None
    panels = []

    for case in cases:
        res = derive(case, n_anchors=args.n_anchors)
        if args.stages:
            panels.extend(stage_panels(res, derive_stages(case, n_anchors=args.n_anchors)))
        else:
            panels.append(
                panel(
                    res,
                    title=f"{case.key} [{case.origin}]",
                    style=args.style,
                    silhouette=not args.no_silhouette,
                    skeleton=not args.no_skeleton,
                    color=GREEN,
                )
            )

    cols = args.cols or (4 if (args.stages or len(panels) > 6) else len(panels))
    fig = figure(panels, cols=cols, dpi=args.dpi)
    name = args.out or ("stages_" + cases[0].key if args.stages else "glyphlab_" + "_".join(c.key for c in cases[:4]))
    path = save(fig, name, out_dir=out_dir)
    print(f"wrote {path}  ({len(panels)} panel(s))")


if __name__ == "__main__":
    main()
