"""Run the word bench: compose every fixture word with CURRENT code, score frozen.

Hermetic and deterministic — no DB, no HTTP: templates + slots + scoring
references come from the fixture snapshot (tools/wordbench/export_fixtures.py);
the code under test is core/shaping.py (frozen slots bypass it deliberately) +
core/pipeline.render_payload_for_template + core/compose.py. ONE script per
run, like the glyph bench: Kurrent and Sütterlin words are never averaged.

Usage:
    uv run python -m tools.wordbench.run [--style suetterlin] [--words unter,das]
        [--artifacts DIR] [--json report.json] [--compare old.json]

Output contract (parsed by the experiment loop — keep stable):

    word unter           loss 0.312345  trans 0.301 cover 0.322 width 0.310  (tx=12, ty=-1)
    ---
    bench_loss:      0.298765
    worst_word:      haben 0.412345
    words_scored:    15
    words_failed:    0
    runtime_s:       3.2
    --- components (mean penalty, lower better) ---
    comp_transition: 0.301234
    comp_coverage:   0.288888
    comp_width:      0.150000
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from core.compose import compose_word
from core.pipeline import render_payload_for_template
from core.shaping import GlyphSlot
from tools.wordbench.metric import score_word


FIXTURES = Path(__file__).resolve().parent / "fixtures"
STYLES = ("suetterlin", "kurrent", "offenbacher")


def _overlay(word_dir: Path, word_meta: dict, composed: dict, report: dict, out_path: Path) -> None:
    """Crop background, specimen skeleton in blue, composed centerlines in red
    (connectors bright, glyph bodies dark, diacritics orange) at the fitted
    registration — the metric is a proxy, the overlay is the truth."""
    crop = Image.open(word_dir / "crop.png").convert("RGB")
    skel = np.load(word_dir / "ref_skel.npz")["skel"]
    px = np.array(crop)  # writable copy
    px[skel] = (90, 140, 220)
    img = Image.fromarray(px)
    d = ImageDraw.Draw(img)
    reg = report.get("registration")
    if reg:
        xh, tx, ty = reg["xh_px"], reg["tx"], reg["ty"]
        baseline_row = word_meta["baseline_y"] - word_meta["rect"][1]
        for it in composed["items"]:
            pts = [(x * xh + tx, baseline_row - y * xh + ty) for x, y in it["centerline"]]
            if "rings" in it:
                color = (230, 140, 30) if it.get("diacritic") else (150, 30, 40)
            else:
                color = (235, 40, 40)
            d.line(pts, fill=color, width=2, joint="curve")
    img.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--style", default="suetterlin", choices=STYLES)
    parser.add_argument("--words", help="comma-separated word filter")
    parser.add_argument("--artifacts", type=Path, help="write overlay PNGs here")
    parser.add_argument("--json", type=Path, help="write the full report here")
    parser.add_argument("--compare", type=Path, help="previous --json report to diff against")
    args = parser.parse_args()

    t0 = time.perf_counter()
    style_root = FIXTURES / args.style
    manifests = sorted(style_root.glob("*/manifest.json"))
    if not manifests:
        raise SystemExit(f"no fixtures under {style_root} — run tools/wordbench/export_fixtures first")

    word_filter = set(args.words.split(",")) if args.words else None
    reports: list[dict] = []
    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text())
        root = manifest_path.parent
        templates = json.loads((root / "templates.json").read_text())
        nib = manifest.get("constant_nib_units")
        resolver = manifest.get("width_resolver") or "pressure"
        style_ratio = manifest.get("style_ratio") or [1, 1, 1]

        payload_cache: dict[str, dict | None] = {}

        def payload_for(
            key: str,
            cache: dict = payload_cache,
            rows: dict = templates,
            ratio: list = style_ratio,
            width_resolver: str = resolver,
            nib_units: float | None = nib,
        ) -> dict | None:
            if key not in cache:
                row = rows.get(key)
                cache[key] = render_payload_for_template(row, ratio, width_resolver, nib_units) if row else None
            return cache[key]

        for entry in manifest["words"]:
            word = entry["word"]
            if word_filter and word not in word_filter:
                continue
            word_dir = root / word
            word_meta = json.loads((word_dir / "word.json").read_text())
            skel = np.load(word_dir / "ref_skel.npz")["skel"]
            slots = [GlyphSlot(**s) for s in word_meta["slots"]]
            try:
                composed = compose_word(slots, {s.key: payload_for(s.key) for s in slots if s.key})
                report = score_word(
                    composed,
                    {
                        "rect": word_meta["rect"],
                        "baseline_y": word_meta["baseline_y"],
                        "midband_y": word_meta["midband_y"],
                    },
                    skel,
                    nib,
                )
            except Exception as exc:  # a crash counts 1.0 — one regressed word always moves the number
                composed = None
                report = {"loss": 1.0, "failed": True, "error": f"{type(exc).__name__}: {exc}", "missing": []}
            report["word"] = word
            report["source_id"] = manifest["source_id"]
            reports.append(report)
            if args.artifacts and composed is not None:
                args.artifacts.mkdir(parents=True, exist_ok=True)
                _overlay(word_dir, word_meta, composed, report, args.artifacts / f"{word}.png")

    for r in sorted(reports, key=lambda r: r["word"]):
        if r["failed"]:
            reason = r.get("error") or f"missing {r.get('missing')}"
            print(f"word {r['word']:<15} loss {r['loss']:.6f}  FAILED ({reason})")
        else:
            reg = r["registration"]
            print(
                f"word {r['word']:<15} loss {r['loss']:.6f}  "
                f"trans {r['transition']:.3f} cover {r['coverage']:.3f} width {r['width']:.3f}  "
                f"(tx={reg['tx']:.0f}, ty={reg['ty']:.0f})"
            )

    scored = [r for r in reports if not r["failed"]]
    losses = [r["loss"] for r in reports]
    bench_loss = float(np.mean(losses)) if losses else 1.0
    worst = max(reports, key=lambda r: r["loss"]) if reports else None
    print("---")
    print(f"bench_loss:      {bench_loss:.6f}")
    if worst:
        print(f"worst_word:      {worst['word']} {worst['loss']:.6f}")
    print(f"words_scored:    {len(scored)}")
    print(f"words_failed:    {len(reports) - len(scored)}")
    print(f"runtime_s:       {time.perf_counter() - t0:.1f}")
    if scored:
        print("--- components (mean penalty, lower better) ---")
        for comp, label in (("transition", "comp_transition"), ("coverage", "comp_coverage"), ("width", "comp_width")):
            print(f"{label}: {float(np.mean([r[comp] for r in scored])):.6f}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"style": args.style, "bench_loss": bench_loss, "words": reports}, indent=1))
    if args.compare:
        old = json.loads(args.compare.read_text())
        old_by_word = {w["word"]: w for w in old["words"]}
        print(f"--- compare vs {args.compare} (Δloss, negative = better) ---")
        print(f"bench_loss: {old['bench_loss']:.6f} -> {bench_loss:.6f}  Δ {bench_loss - old['bench_loss']:+.6f}")
        for r in sorted(reports, key=lambda r: r["loss"] - old_by_word.get(r["word"], {}).get("loss", r["loss"])):
            o = old_by_word.get(r["word"])
            if o:
                print(f"  {r['word']:<15} {o['loss']:.4f} -> {r['loss']:.4f}  Δ {r['loss'] - o['loss']:+.4f}")


if __name__ == "__main__":
    main()
