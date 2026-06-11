"""Glyph bench runner — score the CURRENT pipeline code against frozen references.

Per glyph: re-derive the canonical from the committed chart bytes + the
snapshotted raw trace (`core.pipeline.canonical_from_path`, exactly the
production path), render the silhouette, score it against the FROZEN reference
mask/skeleton via `core.quality.template_quality_metrics`. The pipeline under
test recomputes everything; only the scoring target is frozen — so extraction
changes show up in the numbers but cannot move the goalposts.

Stdout contract (stable, greppable — the experiment loop parses the footer):

    glyph <key>  loss <f>  iou <f>  chamfer_px <f>  geo_rmse_px <f>  waviness <f>
    ---
    bench_loss:      <mean per-glyph loss; a crashed glyph counts 1.0>
    median_iou:      <median over scored glyphs>
    worst_glyph:     <key> <loss>
    glyphs_scored:   <n>
    glyphs_failed:   <n>
    runtime_s:       <s>

Usage:
    uv run python -m tools.glyphbench.run [--fixtures DIR] [--glyphs a-medial,K-initial]
        [--artifacts DIR] [--json report.json]
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

from .overlay import write_overlay_png


DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
CRASH_LOSS = 1.0


def _load_refs(glyph_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ref_mask = np.asarray(Image.open(glyph_dir / "ref_mask.png")) > 127
    with np.load(glyph_dir / "ref_skel.npz") as refs:
        skel = refs["skel"].astype(bool)
        width_map = refs["width_map"].astype(float)
    return ref_mask, skel, width_map


def run_glyph(glyph_dir: Path, chart_path: str, artifacts_dir: Path | None, refine: bool) -> dict:
    """Re-derive one glyph with current code and score it against its frozen refs."""
    template = json.loads((glyph_dir / "template.json").read_text())
    bbox = json.loads((glyph_dir / "bbox.json").read_text())
    ref_mask, skel, width_map = _load_refs(glyph_dir)

    canon = canonical_from_path(
        raw_path=template["raw_path"],
        bbox=bbox,
        chart_path=chart_path,
        glyph=template["glyph"],
        position=template["position"],
        # Mirror the /resample default (the production write-back path): the
        # bench measures what a "Neu ableiten" would actually store, not the
        # possibly stale per-bbox anchor count frozen into the fixture.
        n_anchors=DEFAULT_N_ANCHORS,
        refine=refine,
    )
    tm = canon["trace_meta"]
    anchors_px = crop_local_anchors(tm["pixel_anchors"], bbox)
    half_widths_px = np.asarray(tm["half_widths_px"], dtype=float)
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES_DIR, help="fixtures root dir")
    parser.add_argument("--glyphs", default=None, help="comma-separated glyph_key filter (default: all)")
    parser.add_argument("--artifacts", type=Path, default=None, help="write per-glyph overlay PNGs to this dir")
    parser.add_argument("--json", dest="json_path", type=Path, default=None, help="write the full report as JSON")
    parser.add_argument(
        "--no-refine", action="store_true", help="skip the image-space refinement (isolates extraction changes)"
    )
    args = parser.parse_args()

    manifests = sorted(args.fixtures.rglob("manifest.json"))
    if not manifests:
        raise SystemExit(f"no manifest.json under {args.fixtures} — run export_fixtures first")
    glyph_filter = set(args.glyphs.split(",")) if args.glyphs else None
    if args.artifacts is not None:
        args.artifacts.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    results: list[dict] = []
    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text())
        chart_path = manifest["chart_path"]
        for entry in sorted(manifest["glyphs"], key=lambda g: g["glyph_key"]):
            key = entry["glyph_key"]
            if glyph_filter is not None and key not in glyph_filter:
                continue
            glyph_dir = manifest_path.parent / key
            try:
                metrics = run_glyph(glyph_dir, chart_path, args.artifacts, not args.no_refine)
                results.append({"glyph_key": key, "status": "scored", "metrics": metrics})
                print(
                    f"glyph {key:<14} loss {metrics['loss']:.6f}  iou {metrics['iou']:.3f}  "
                    f"chamfer_px {metrics['chamfer_mean_px']:.2f}  geo_rmse_px {metrics['geo_rmse_px']:.2f}  "
                    f"waviness {metrics['waviness_ratio']:.2f}"
                )
            except Exception as exc:  # noqa: BLE001 — a broken glyph must not kill the bench
                results.append({"glyph_key": key, "status": "crash", "error": traceback.format_exc()})
                print(f"glyph {key:<14} CRASH: {exc}")

    runtime_s = time.monotonic() - started
    losses = [r["metrics"]["loss"] if r["status"] == "scored" else CRASH_LOSS for r in results]
    scored = [r for r in results if r["status"] == "scored"]
    failed = [r for r in results if r["status"] == "crash"]
    bench_loss = float(np.mean(losses)) if losses else CRASH_LOSS
    median_iou = float(np.median([r["metrics"]["iou"] for r in scored])) if scored else 0.0
    if results:
        worst_idx = int(np.argmax(losses))
        worst_label = f"{results[worst_idx]['glyph_key']} {losses[worst_idx]:.6f}"
    else:
        worst_label = "- 0.000000"

    if args.json_path is not None:
        report = {
            "fixtures": str(args.fixtures),
            "bench_loss": bench_loss,
            "median_iou": median_iou,
            "worst_glyph": worst_label,
            "glyphs_scored": len(scored),
            "glyphs_failed": len(failed),
            "runtime_s": round(runtime_s, 1),
            "glyphs": results,
        }
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


if __name__ == "__main__":
    main()
