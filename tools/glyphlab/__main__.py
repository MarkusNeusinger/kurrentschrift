"""glyphlab CLI — render glyph derivation overlays to a PNG you can open.

Examples:
    # final overlay (centerline + silhouette + corners) for a few fixtures
    python -m tools.glyphlab i-initial u-initial n-initial

    # every Sütterlin form, anchor-dot style (as the admin shows them)
    python -m tools.glyphlab --all --style dots

    # the four derivation stages of one glyph, side by side
    python -m tools.glyphlab i-initial --stages

    # rendered-ink-vs-crop error map, zoomed to the tip region (under=blue, over=red)
    python -m tools.glyphlab longs-final t-final --fill-diff --zoom-top 0.4

    # sweep one tuning constant across values for ONE glyph (one column each)
    python -m tools.glyphlab longs-final --sweep core.suetterlin.RETRACE_TAPER_NIB=0.5,1.0,1.5

    # the live (DB) trace instead of the frozen fixture (read-only)
    python -m tools.glyphlab i-initial --live --source suetterlin-1922

Output goes to $GLYPHLAB_OUT (else the project temp/ dir); the path is printed.
On WSL, point it at Windows to view: GLYPHLAB_OUT=/mnt/c/Users/<you>/Desktop/glyphlab
"""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path

from .cases import GlyphCase, fixture_case, iter_fixture_cases, live_case_sync
from .derive import derive, derive_stages
from .render import GREEN, figure, panel, save, stage_panels


def _resolve_cases(args: argparse.Namespace) -> list[GlyphCase]:
    if args.all:
        return iter_fixture_cases(only=args.keys or None, source_id=args.source)
    if not args.keys:
        raise SystemExit("give one or more glyph_keys, or --all")
    if args.live:
        return [live_case_sync(args.source, k) for k in args.keys]
    # --source disambiguates a shared glyph_key (e.g. f-final exists in both the Kurrent
    # and Sütterlin sets); default suetterlin-1922 so a fixture render is no longer
    # silently the Kurrent glyph.
    return [fixture_case(k, source_id=args.source) for k in args.keys]


def parse_sweep(spec: str) -> tuple[str, str, list[float]]:
    """Parse `module.path.CONST=v1,v2,...` → (module_path, attr_name, [floats]).

    The dotted path's last segment is the constant; everything before it is the
    importable module. Values are parsed as floats (the only thing we tune here).
    Public: tools/wordlab reuses it for its own `--sweep` (two CLIs, one core).
    """
    dotted, _, raw_values = spec.partition("=")
    if not raw_values:
        raise SystemExit(f"--sweep needs DOTTED.PATH=v1,v2,...; got {spec!r}")
    module_path, _, attr = dotted.rpartition(".")
    if not module_path or not attr:
        raise SystemExit(f"--sweep path must be module.attr, got {dotted!r}")
    try:
        values = [float(v) for v in raw_values.split(",") if v.strip()]
    except ValueError as exc:
        raise SystemExit(f"--sweep values must be floats: {raw_values!r} ({exc})") from exc
    if not values:
        raise SystemExit(f"--sweep needs at least one value; got {raw_values!r}")
    return module_path, attr, values


def _run_sweep(args: argparse.Namespace, out_dir: Path | None) -> None:
    """Render ONE glyph across several values of a module-level constant (columns).

    The constant is patched in place, the glyph re-derived per value, then the
    ORIGINAL value is always restored in a `finally` so the live module is left
    untouched. Honours --fill-diff / --zoom-top styling for the panels.
    """
    if len(args.keys) != 1:
        raise SystemExit("--sweep renders exactly ONE glyph key; give a single key")
    module_path, attr, values = parse_sweep(args.sweep)
    module = importlib.import_module(module_path)
    if not hasattr(module, attr):
        raise SystemExit(f"--sweep: {module_path!r} has no attribute {attr!r}")
    case = _resolve_cases(args)[0]

    original = getattr(module, attr)
    panels = []
    try:
        for value in values:
            setattr(module, attr, value)
            res = derive(case, n_anchors=args.n_anchors)
            panels.append(
                panel(
                    res,
                    title=f"{case.key} · {attr}={value:g}",
                    style=args.style,
                    silhouette=not args.no_silhouette,
                    skeleton=not args.no_skeleton,
                    scores=not args.no_scores,
                    color=GREEN,
                    fill_diff=args.fill_diff,
                    zoom_top=args.zoom_top,
                )
            )
    finally:
        setattr(module, attr, original)  # never leave the patched constant behind

    cols = args.cols or len(panels)
    fig = figure(panels, cols=cols, dpi=args.dpi)
    name = args.out or f"sweep_{case.key}_{attr}"
    path = save(fig, name, out_dir=out_dir)
    print(f"wrote {path}  ({len(panels)} panel(s))")


def main() -> None:
    p = argparse.ArgumentParser(
        prog="glyphlab", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("keys", nargs="*", help="glyph_keys, e.g. i-initial u-medial")
    p.add_argument("--all", action="store_true", help="all fixture forms (optionally filtered by keys)")
    p.add_argument("--live", action="store_true", help="read the trace from the DB (read-only) instead of the fixture")
    p.add_argument(
        "--source",
        default="suetterlin-1922",
        help="source id — used for --live AND to disambiguate a shared fixture key (default: suetterlin-1922)",
    )
    p.add_argument("--stages", action="store_true", help="show snap/smooth/resample/verticalize (Gleichzug only)")
    p.add_argument(
        "--fill-diff",
        action="store_true",
        help="error map: rendered ink vs crop ink (gray=correct, blue=under-fill, red=over-splay)",
    )
    p.add_argument(
        "--zoom-top",
        type=float,
        default=None,
        metavar="FRAC",
        help="crop the view to the top FRAC of the glyph height (the tip region), e.g. 0.4",
    )
    p.add_argument(
        "--sweep",
        default=None,
        metavar="DOTTED.PATH=v1,v2,...",
        help="render ONE glyph across values of a module constant, e.g. core.suetterlin.RETRACE_TAPER_NIB=0.5,1.0,1.5",
    )
    p.add_argument("--style", choices=["spline", "dots", "line"], default="spline", help="centerline style")
    p.add_argument("--no-silhouette", action="store_true", help="hide the filled stroke body")
    p.add_argument("--no-skeleton", action="store_true", help="hide the skeleton")
    p.add_argument("--no-scores", action="store_true", help="hide the per-component quality breakdown")
    p.add_argument("--n-anchors", type=int, default=None, help="resample target (default: per-bbox / pipeline default)")
    p.add_argument("--dpi", type=int, default=140, help="output resolution (default 140)")
    p.add_argument("--cols", type=int, default=None, help="montage columns (default: all in one row)")
    p.add_argument("--out", default=None, help="output filename (default: derived from keys)")
    p.add_argument("--out-dir", default=None, help="output directory (default: $GLYPHLAB_OUT or project temp/)")
    args = p.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else None
    if args.sweep:
        _run_sweep(args, out_dir)
        return

    cases = _resolve_cases(args)
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
                    scores=not args.no_scores,
                    color=GREEN,
                    fill_diff=args.fill_diff,
                    zoom_top=args.zoom_top,
                )
            )

    # Cap columns so a multi-glyph montage stays legible (wrap to rows) rather
    # than one ultra-wide row that downscales each panel to a sliver.
    cols = args.cols or (4 if args.stages else min(3, len(panels)))
    fig = figure(panels, cols=cols, dpi=args.dpi)
    if args.out:
        name = args.out
    elif args.stages:
        name = "stages_" + cases[0].key
    else:
        prefix = "filldiff_" if args.fill_diff else "glyphlab_"
        name = prefix + "_".join(c.key for c in cases[:4])
    path = save(fig, name, out_dir=out_dir)
    print(f"wrote {path}  ({len(panels)} panel(s))")


if __name__ == "__main__":
    main()
