"""Run the word bench: compose every fixture word with CURRENT code, score frozen.

Hermetic and deterministic — no DB, no HTTP: templates + slots + scoring
references come from the fixture snapshot (tools/wordbench/export_fixtures.py).
The code under test per run is COMPOSITION + RENDERING (core/compose.py +
core/pipeline.render_payload_for_template). Shaping is deliberately NOT under
test: the slots are frozen at export, so a core/shaping.py change moves the
numbers only after an explicit re-export (= a re-baseline). ONE script per
run, like the glyph bench: Kurrent and Sütterlin words are never averaged —
and neither are words and pairs: ``--set`` selects the fixture set, and the
pairs of Abb. 20 report their own ``pair_loss`` headline. Entries frozen as
``scorable: false`` (a needed template is not authored yet) are skipped and
reported by name — an authoring gap is not a composition failure; a crash of
an authored entry still counts 1.0.

Usage:
    uv run python -m tools.wordbench.run [--style suetterlin] [--set words|pairs|all]
        [--words unter,das] [--artifacts DIR] [--json report.json] [--compare old.json]

Output contract (parsed by the experiment loop — keep the words block stable):

    word unter           loss 0.312345  trans 0.301 cover 0.322 width 0.310  (tx=12, ty=-1)
    ---
    bench_loss:      0.298765
    worst_word:      haben 0.412345
    words_scored:    15
    words_skipped:   0
    words_failed:    0
    --- components (mean penalty, lower better) ---
    comp_transition: 0.301234
    comp_coverage:   0.288888
    comp_width:      0.150000

The pairs block (``--set pairs``/``all``) mirrors it with ``pair_loss:``,
``worst_pair:``, ``pairs_scored/skipped/failed`` and ``pair_comp_*`` lines.
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


def _print_block(reports: list[dict], skipped: list[dict], kind: str) -> None:
    """One headline block per fixture set. The words block is the experiment
    loop's stable contract; the pairs block mirrors it under its own names."""
    loss_label, worst_label, noun, comp_prefix = (
        ("bench_loss", "worst_word", "words", "comp")
        if kind == "word"
        else ("pair_loss", "worst_pair", "pairs", "pair_comp")
    )
    scored = [r for r in reports if not r["failed"]]
    losses = [r["loss"] for r in reports]
    headline = float(np.mean(losses)) if losses else 1.0
    worst = max(reports, key=lambda r: r["loss"]) if reports else None
    print("---")
    print(f"{loss_label}:      {headline:.6f}")
    if worst:
        print(f"{worst_label}:      {worst['id']} {worst['loss']:.6f}")
    print(f"{noun}_scored:    {len(scored)}")
    print(f"{noun}_skipped:   {len(skipped)}")
    print(f"{noun}_failed:    {len(reports) - len(scored)}")
    if skipped:
        print(f"{noun}_skipped_ids: {','.join(s['id'] for s in skipped)}")
    if scored:
        print("--- components (mean penalty, lower better) ---")
        for comp, label in (("transition", "transition"), ("coverage", "coverage"), ("width", "width")):
            print(f"{comp_prefix}_{label}: {float(np.mean([r[comp] for r in scored])):.6f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--style", default="suetterlin", choices=STYLES)
    parser.add_argument(
        "--set",
        dest="which",
        default="words",
        help="fixture set to run (words | pairs | a custom set name | all). 'all' covers ONLY the "
        "canonical same-hand sets (words + pairs) — a custom cross-hand set like abb22 must be "
        "named explicitly so it can never mix into the same-hand headlines.",
    )
    parser.add_argument("--fixtures", type=Path, default=FIXTURES, help="fixture root (default: the frozen set)")
    parser.add_argument("--words", help="comma-separated id/word filter")
    parser.add_argument("--artifacts", type=Path, help="write overlay PNGs here")
    parser.add_argument("--json", type=Path, help="write the full report here")
    parser.add_argument("--compare", type=Path, help="previous --json report to diff against")
    args = parser.parse_args()

    t0 = time.perf_counter()
    style_root = args.fixtures / args.style
    # 'all' aggregates reports across the selected manifests, so it must stay
    # scoped to the canonical SAME-HAND sets — a custom cross-hand set (abb22)
    # would otherwise silently join the words headline.
    wanted = ("words", "pairs") if args.which == "all" else (args.which,)
    manifests = [
        p for p in sorted(style_root.glob("*/manifest.json")) if json.loads(p.read_text()).get("set", "words") in wanted
    ]
    if not manifests:
        raise SystemExit(f"no {args.which} fixtures under {style_root} — run tools/wordbench/export_fixtures first")

    word_filter = set(args.words.split(",")) if args.words else None
    reports: list[dict] = []
    skipped: list[dict] = []
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
            entry_id = entry.get("id", entry["word"])
            kind = entry.get("kind", "word")
            if word_filter and entry_id not in word_filter and entry["word"] not in word_filter:
                continue
            if not entry.get("scorable", not entry.get("missing_at_export")):
                skipped.append({"id": entry_id, "kind": kind, "missing": entry.get("missing_at_export", [])})
                continue
            word_dir = root / entry_id
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
            report["id"] = entry_id
            report["word"] = entry["word"]
            report["kind"] = kind
            report["source_id"] = manifest["source_id"]
            reports.append(report)
            if args.artifacts and composed is not None:
                args.artifacts.mkdir(parents=True, exist_ok=True)
                _overlay(word_dir, word_meta, composed, report, args.artifacts / f"{entry_id}.png")

    for r in sorted(reports, key=lambda r: r["id"]):
        if r["failed"]:
            reason = r.get("error") or f"missing {r.get('missing')}"
            print(f"word {r['id']:<15} loss {r['loss']:.6f}  FAILED ({reason})")
        else:
            reg = r["registration"]
            print(
                f"word {r['id']:<15} loss {r['loss']:.6f}  "
                f"trans {r['transition']:.3f} cover {r['coverage']:.3f} width {r['width']:.3f}  "
                f"(tx={reg['tx']:.0f}, ty={reg['ty']:.0f})"
            )

    result: dict = {"style": args.style, "set": args.which}
    for kind in ("word", "pair"):
        kind_reports = [r for r in reports if r["kind"] == kind]
        kind_skipped = [s for s in skipped if s["kind"] == kind]
        if not kind_reports and not kind_skipped:
            continue
        _print_block(kind_reports, kind_skipped, kind)
        headline = float(np.mean([r["loss"] for r in kind_reports])) if kind_reports else 1.0
        result["bench_loss" if kind == "word" else "pair_loss"] = headline
    print(f"runtime_s:       {time.perf_counter() - t0:.1f}")

    if args.json:
        result["words"] = reports
        result["skipped"] = skipped
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=1))
    if args.compare:
        old = json.loads(args.compare.read_text())
        old_by_id = {w.get("id", w["word"]): w for w in old["words"]}
        for label in ("bench_loss", "pair_loss"):
            if label in old and label in result:
                print(f"--- compare vs {args.compare} (Δ{label}, negative = better) ---")
                print(f"{label}: {old[label]:.6f} -> {result[label]:.6f}  Δ {result[label] - old[label]:+.6f}")
        for r in sorted(reports, key=lambda r: r["loss"] - old_by_id.get(r["id"], {}).get("loss", r["loss"])):
            o = old_by_id.get(r["id"])
            if o:
                print(f"  {r['id']:<15} {o['loss']:.4f} -> {r['loss']:.4f}  Δ {r['loss'] - o['loss']:+.4f}")


if __name__ == "__main__":
    main()
