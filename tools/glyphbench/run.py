"""Glyph bench runner — score the CURRENT pipeline code against frozen references.

Runs **one script per invocation** (`--style suetterlin` by default, `--style
kurrent` for the pressure script): Kurrent and Sütterlin use different writing
instruments and so different quality metrics, and averaging a Schwellzug score
with a Gleichzug score is meaningless — there is no combined `bench_loss`.

Per glyph: re-derive the canonical from the committed chart bytes + the
snapshotted raw trace with the production path (`canonical_suetterlin_from_path`
for the Gleichzug script, `canonical_from_path` for pressure), render the
silhouette, and score it against the FROZEN reference mask/skeleton:

  * Sütterlin (`width_resolver == "constant"`): `suetterlin_quality_metrics` —
    intrinsic naturalness (smoothness, verticality, corner crispness, crossing
    collinearity, retrace) gated by a tolerant coverage of the crop.
  * Kurrent (`width_resolver == "pressure"`): `template_quality_metrics` — the
    Schwellzug pixel/width metric, unchanged.

The pipeline under test recomputes everything; only the scoring target is frozen
— extraction changes show up in the numbers but cannot move the goalposts.

Stdout contract (stable, greppable — the experiment loop parses the footer):

    glyph <key>  loss <f>  smooth <f> vert <f> corner <f> cross <f> ...   (Sütterlin)
    glyph <key>  loss <f>  iou <f>  chamfer_px <f>  geo_rmse_px <f>  ...   (Kurrent)
    ---
    bench_loss:      <mean per-glyph loss; a crashed glyph counts 1.0>
    median_iou:      <median over scored glyphs>
    worst_glyph:     <key> <loss>
    glyphs_scored:   <n>
    glyphs_failed:   <n>
    runtime_s:       <s>
    --- components (mean penalty, lower better) ---   (Sütterlin only)
    comp_<name>:     <mean over scored>

Usage:
    uv run python -m tools.glyphbench.run [--style suetterlin|kurrent]
        [--fixtures DIR] [--glyphs a-medial,K-initial] [--artifacts DIR]
        [--json report.json] [--compare prev_report.json]
"""

from __future__ import annotations

import argparse
import json
import time
import traceback
from pathlib import Path

import numpy as np
from PIL import Image

from core.pipeline import DEFAULT_N_ANCHORS, canonical_from_path
from core.quality import crop_local_anchors, silhouette_mask, template_quality_metrics
from core.quality_suetterlin import suetterlin_quality_metrics
from core.suetterlin import canonical_suetterlin_from_path

from .overlay import write_overlay_png


DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
CRASH_LOSS = 1.0

# --style maps to the source's stored width_resolver. Offenbacher (broad_nib)
# derives through the pressure pipeline and scores with the Schwellzug pixel
# metric for now — that metric scores the MEASURED profile against the ink,
# so it is honest for broad-nib extraction too; a dedicated width-direction
# naturalness metric (w(phi) = W·|sin(phi−alpha)| fit) is designed in
# docs/concepts/federmodelle.md and waits for enough authored templates to
# calibrate against.
STYLE_TO_RESOLVER = {"suetterlin": "constant", "kurrent": "pressure", "offenbacher": "broad_nib"}

# Sütterlin per-glyph component order (and the footer's comp_<name> means).
COMPONENT_KEYS = ["smoothness", "verticality", "corner", "collinearity", "retrace", "coverage", "naturalness"]


def _load_refs(glyph_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ref_mask = np.asarray(Image.open(glyph_dir / "ref_mask.png")) > 127
    with np.load(glyph_dir / "ref_skel.npz") as refs:
        skel = refs["skel"].astype(bool)
        width_map = refs["width_map"].astype(float)
    return ref_mask, skel, width_map


def run_glyph(
    glyph_dir: Path, chart_path: str, artifacts_dir: Path | None, refine: bool, width_resolver: str = "pressure"
) -> dict:
    """Re-derive one glyph with current code and score it against its frozen refs.

    Routes BOTH derivation and metric per the source's `width_resolver`, exactly
    like the production API: constant-width styles (Sütterlin Gleichzug) go
    through the skeleton-locked derivation and the naturalness metric; everything
    else through the pressure pipeline and the Schwellzug metric.
    """
    template = json.loads((glyph_dir / "template.json").read_text())
    bbox = json.loads((glyph_dir / "bbox.json").read_text())
    ref_mask, skel, width_map = _load_refs(glyph_dir)

    common = {
        "raw_path": template["raw_path"],
        "bbox": bbox,
        "chart_path": chart_path,
        "glyph": template["glyph"],
        # Mirror the /resample default (the production write-back path): the
        # bench measures what a "Neu ableiten" would actually store, not the
        # possibly stale per-bbox anchor count frozen into the fixture.
        "n_anchors": DEFAULT_N_ANCHORS,
    }
    if width_resolver == "constant":
        canon = canonical_suetterlin_from_path(**common)
    else:
        canon = canonical_from_path(**common, refine=refine)
    tm = canon["trace_meta"]
    anchors_px = crop_local_anchors(tm["pixel_anchors"], bbox)
    half_widths_px = np.asarray(tm["half_widths_px"], dtype=float)
    if width_resolver == "constant":
        metrics = suetterlin_quality_metrics(
            anchors_px,
            half_widths_px,
            tm["stroke_starts"],
            ref_mask,
            skel,
            width_map,
            unit_px=float(tm["unit_px"]),
            corner_anchors=tm.get("corner_anchors"),
        )
    else:
        metrics = template_quality_metrics(
            anchors_px,
            half_widths_px,
            tm["stroke_starts"],
            ref_mask,
            skel,
            width_map,
            unit_px=float(tm["unit_px"]),
            crossing_anchors=tm.get("crossing_anchors"),
            corner_anchors=tm.get("corner_anchors"),
        )

    if artifacts_dir is not None:
        crop = np.asarray(Image.open(glyph_dir / "crop.png"), dtype=float) / 255.0
        pred_mask = silhouette_mask(
            anchors_px, half_widths_px, tm["stroke_starts"], ref_mask.shape, corner_anchors=tm.get("corner_anchors")
        )
        write_overlay_png(artifacts_dir / f"{glyph_dir.name}.png", crop, pred_mask, ref_mask)

    return metrics


def _print_glyph_line(key: str, metrics: dict) -> None:
    """One greppable per-glyph line; metric-aware (Sütterlin components vs Kurrent)."""
    if "components" in metrics:
        c = metrics["components"]
        print(
            f"glyph {key:<14} loss {metrics['loss']:.6f}  "
            f"smooth {c['smoothness']:.3f}  vert {c['verticality']:.3f}  corner {c['corner']:.3f}  "
            f"cross {c['collinearity']:.3f}  retr {c['retrace']:.3f}  "
            f"cover {c['coverage']:.3f}  nat {c['naturalness']:.3f}"
        )
    else:
        print(
            f"glyph {key:<14} loss {metrics['loss']:.6f}  iou {metrics['iou']:.3f}  "
            f"chamfer_px {metrics['chamfer_mean_px']:.2f}  geo_rmse_px {metrics['geo_rmse_px']:.2f}  "
            f"waviness {metrics['waviness_ratio']:.2f}"
        )


def _component_means(scored: list[dict]) -> dict[str, float] | None:
    """Mean per-component penalty over scored glyphs that carry components, or None."""
    with_components = [r for r in scored if "components" in r["metrics"]]
    if not with_components:
        return None
    return {k: float(np.mean([r["metrics"]["components"][k] for r in with_components])) for k in COMPONENT_KEYS}


def _arrow(delta: float) -> str:
    # ASCII (not ↓/↑) so --compare output never trips a non-UTF-8 terminal.
    # Penalties are lower-is-better: "better" = improved, "WORSE" = regressed.
    return "better" if delta < -1e-9 else "WORSE" if delta > 1e-9 else "same"


def _print_comparison(prev: dict, bench_loss: float, comp_means: dict | None, results: list[dict]) -> None:
    """Per-component and per-glyph delta tables vs a previous --json report.

    Penalties are lower-is-better, so a negative delta ("better") is an improvement.
    """
    print(
        f"\n=== compare: {prev.get('fixtures', '?')} @ bench_loss {prev.get('bench_loss', float('nan')):.6f}"
        f" → current bench_loss {bench_loss:.6f} ==="
    )
    print(f"{'metric':<16}{'old':>10}{'new':>10}{'Δ':>11}")
    d = bench_loss - float(prev.get("bench_loss", float("nan")))
    print(f"{'bench_loss':<16}{prev.get('bench_loss', float('nan')):>10.6f}{bench_loss:>10.6f}{d:>+10.6f} {_arrow(d)}")
    prev_means = prev.get("components_mean") or {}
    if comp_means and prev_means:
        for k in COMPONENT_KEYS:
            old, new = float(prev_means.get(k, float("nan"))), comp_means[k]
            dd = new - old
            print(f"{'  ' + k:<16}{old:>10.4f}{new:>10.4f}{dd:>+10.4f} {_arrow(dd)}")

    prev_by_key = {g["glyph_key"]: g for g in prev.get("glyphs", [])}
    cur_by_key = {r["glyph_key"]: r for r in results}

    def _loss(entry: dict | None) -> float | None:
        if not entry or entry.get("status") != "scored":
            return None
        return float(entry["metrics"]["loss"])

    print(f"\n{'glyph':<16}{'old':>10}{'new':>10}{'Δ':>11}  worst component move")
    rows = []
    for key in sorted(set(prev_by_key) | set(cur_by_key)):
        old_loss, new_loss = _loss(prev_by_key.get(key)), _loss(cur_by_key.get(key))
        rows.append((key, old_loss, new_loss))
    # Biggest movers first; new/removed glyphs sort last.
    rows.sort(
        key=lambda r: abs((r[2] or 0.0) - (r[1] or 0.0)) if r[1] is not None and r[2] is not None else -1.0,
        reverse=True,
    )
    for key, old_loss, new_loss in rows:
        if old_loss is None and new_loss is not None:
            print(f"{key:<16}{'--':>10}{new_loss:>10.4f}{'new':>11}")
            continue
        if new_loss is None and old_loss is not None:
            print(f"{key:<16}{old_loss:>10.4f}{'--':>10}{'gone':>11}")
            continue
        dd = (new_loss or 0.0) - (old_loss or 0.0)
        move = ""
        pe, ce = prev_by_key.get(key), cur_by_key.get(key)
        if pe and ce and "components" in pe.get("metrics", {}) and "components" in ce.get("metrics", {}):
            pc, cc = pe["metrics"]["components"], ce["metrics"]["components"]
            wk = max(COMPONENT_KEYS, key=lambda k: abs(cc[k] - pc[k]))
            move = f"{wk} {cc[wk] - pc[wk]:+.3f}"
        print(f"{key:<16}{old_loss:>10.4f}{new_loss:>10.4f}{dd:>+10.4f} {_arrow(dd)}  {move}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--style", choices=sorted(STYLE_TO_RESOLVER), default="suetterlin", help="which script to bench (one per run)"
    )
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES_DIR, help="fixtures root dir")
    parser.add_argument("--glyphs", default=None, help="comma-separated glyph_key filter (default: all)")
    parser.add_argument("--artifacts", type=Path, default=None, help="write per-glyph overlay PNGs to this dir")
    parser.add_argument("--json", dest="json_path", type=Path, default=None, help="write the full report as JSON")
    parser.add_argument(
        "--compare", type=Path, default=None, help="diff component/glyph deltas vs a previous --json report"
    )
    parser.add_argument(
        "--no-refine", action="store_true", help="skip the image-space refinement (isolates extraction changes)"
    )
    args = parser.parse_args()

    manifests = sorted(args.fixtures.rglob("manifest.json"))
    if not manifests:
        raise SystemExit(f"no manifest.json under {args.fixtures} — run export_fixtures first")
    want_resolver = STYLE_TO_RESOLVER[args.style]
    glyph_filter = set(args.glyphs.split(",")) if args.glyphs else None
    if args.artifacts is not None:
        args.artifacts.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    results: list[dict] = []
    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text())
        width_resolver = manifest.get("width_resolver", "pressure")
        if width_resolver != want_resolver:  # one script per run — Kurrent and Sütterlin stay separate
            continue
        chart_path = manifest["chart_path"]
        for entry in sorted(manifest["glyphs"], key=lambda g: g["glyph_key"]):
            key = entry["glyph_key"]
            if glyph_filter is not None and key not in glyph_filter:
                continue
            glyph_dir = manifest_path.parent / key
            try:
                metrics = run_glyph(glyph_dir, chart_path, args.artifacts, not args.no_refine, width_resolver)
                results.append({"glyph_key": key, "status": "scored", "metrics": metrics})
                _print_glyph_line(key, metrics)
            except Exception as exc:  # noqa: BLE001 — a broken glyph must not kill the bench
                results.append({"glyph_key": key, "status": "crash", "error": traceback.format_exc()})
                print(f"glyph {key:<14} CRASH: {exc}")

    if not results:
        raise SystemExit(
            f"no fixtures with width_resolver={want_resolver!r} (--style {args.style}) under {args.fixtures}"
        )

    runtime_s = time.monotonic() - started
    losses = [r["metrics"]["loss"] if r["status"] == "scored" else CRASH_LOSS for r in results]
    scored = [r for r in results if r["status"] == "scored"]
    failed = [r for r in results if r["status"] == "crash"]
    bench_loss = float(np.mean(losses)) if losses else CRASH_LOSS
    median_iou = float(np.median([r["metrics"]["iou"] for r in scored])) if scored else 0.0
    comp_means = _component_means(scored)
    worst_idx = int(np.argmax(losses))
    worst_label = f"{results[worst_idx]['glyph_key']} {losses[worst_idx]:.6f}"

    if args.json_path is not None:
        report = {
            "fixtures": str(args.fixtures),
            "style": args.style,
            "bench_loss": bench_loss,
            "median_iou": median_iou,
            "worst_glyph": worst_label,
            "glyphs_scored": len(scored),
            "glyphs_failed": len(failed),
            "runtime_s": round(runtime_s, 1),
            "glyphs": results,
        }
        if comp_means is not None:
            report["components_mean"] = comp_means
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(report, ensure_ascii=False, indent=1))
        print(f"report written to {args.json_path}")
    if args.artifacts is not None:
        print(f"overlays written to {args.artifacts}")

    print("---")
    print(f"bench_loss:      {bench_loss:.6f}")
    print(f"median_iou:      {median_iou:.6f}")
    print(f"worst_glyph:     {worst_label}")
    print(f"glyphs_scored:   {len(scored)}")
    print(f"glyphs_failed:   {len(failed)}")
    print(f"runtime_s:       {runtime_s:.1f}")
    if comp_means is not None:
        print("--- components (mean penalty, lower better) ---")
        for k in COMPONENT_KEYS:
            print(f"comp_{k}: {comp_means[k]:.6f}")

    if args.compare is not None:
        prev = json.loads(args.compare.read_text())
        _print_comparison(prev, bench_loss, comp_means, results)


if __name__ == "__main__":
    main()
