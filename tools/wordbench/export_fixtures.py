"""Snapshot templates + frozen word-scoring references for the word bench.

Mirrors tools/glyphbench/export_fixtures.py: this is the ONLY module in the
package that touches the DB — read-only SELECTs — and it freezes everything a
bench run scores against, so an experiment on the composer cannot move the
goalposts. Frozen per word: the crop (from the committed page bytes + the
words.json sidecar), the binarized scoring mask, the skeleton + EDT width map,
and the SHAPED SLOTS (so a later shaping change is a deliberate re-baseline,
not a silent input shift). Frozen per source: the template rows the words need
and the source-pooled Gleichzug nib.

Fixture layout (gitignored — regenerate at will):

    fixtures/<style_id>/<source_id>/
      manifest.json            # export stamp, page sha256s, style ratio/resolver, pooled nib, word index
      templates.json           # glyph_key -> template row (anchors, half_widths, trace_meta, entry, exit_pt, advance)
      <word>/
        word.json              # text, rect, lineature, frozen slots
        crop.png               # grayscale crop (excludes applied) — overlay background
        ref_mask.png           # FROZEN binarized scoring reference
        ref_skel.npz           # FROZEN skeleton (bool) + EDT half-width map (float32)

Usage:
    uv run python -m tools.wordbench.export_fixtures [--source suetterlin-1922]
        [--out tools/wordbench/fixtures]
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import statistics
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from PIL import Image
from scipy.ndimage import label as cc_label

from core.extract import binarize_adaptive, skeleton_and_width
from core.shaping import decompose_ligature_slot, glyph_keys_of, shape_text


DEFAULT_SOURCE_ID = "suetterlin-1922"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _template_dict(t) -> dict:
    return {
        "glyph_key": t.glyph_key,
        "glyph": t.glyph,
        "position": t.position,
        "advance": t.advance,
        "entry": t.entry,
        "exit_pt": t.exit_pt,
        "anchors": t.anchors,
        "half_widths": t.half_widths,
        "trace_meta": t.trace_meta,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _load_page(path: Path) -> np.ndarray:
    """Page image as float grayscale in [0, 1] (same convention as core.chart)."""
    return np.asarray(Image.open(path).convert("L"), dtype=np.float64) / 255.0


# Paper grain survives the adaptive binarisation as scattered 1–10 px specks;
# their skeletons would put a noise floor under the reverse chamfer. Real marks
# stay: the smallest genuine ink component (an i-dot) is ~50 px² at this scale.
DESPECKLE_MIN_AREA_PX = 24


def _despeckle(mask: np.ndarray) -> np.ndarray:
    labels, n = cc_label(mask)
    if not n:
        return mask
    sizes = np.bincount(labels.ravel())
    keep = sizes >= DESPECKLE_MIN_AREA_PX
    keep[0] = False
    return keep[labels]


async def export(source_id: str, out_dir: Path) -> None:
    sidecar_path = REPO_ROOT / "data" / "sources" / source_id / "words.json"
    if not sidecar_path.exists():
        raise SystemExit(f"no word sidecar at {sidecar_path}")
    sidecar = json.loads(sidecar_path.read_text())
    words = sidecar["words"]

    # Imported here, after load_dotenv(): the connection module reads env at import time.
    from core.database.connection import get_db_context
    from core.database.repositories import SourceRepository, StyleRepository, TemplateRepository

    async with get_db_context() as session:
        source = await SourceRepository(session).get(source_id)
        if source is None:
            raise SystemExit(f"source {source_id!r} not found")
        style = await StyleRepository(session).get(source.style_id)
        repo = TemplateRepository(session)

        # Shape every word, apply the ligature-decompose fallback against the
        # CURRENT template inventory, and freeze the resulting slots.
        shaped: dict[str, list[dict]] = {}
        needed: dict[str, None] = {}
        for w in words:
            slots = shape_text(w["word"])
            keys = glyph_keys_of(slots)
            have = {t.glyph_key for t in await repo.get_many(source.style_id, keys)}
            if any(s.ligature and s.key and s.key not in have for s in slots):
                slots = [
                    d
                    for s in slots
                    for d in (
                        (decompose_ligature_slot(s) or [s]) if s.ligature and s.key and s.key not in have else [s]
                    )
                ]
            shaped[w["word"]] = [asdict(s) for s in slots]
            for k in glyph_keys_of(slots):
                needed.setdefault(k)

        templates = {t.glyph_key: _template_dict(t) for t in await repo.get_many(source.style_id, list(needed))}
        # Source-pooled Gleichzug nib, frozen at export (api.rendering computes
        # the same live; freezing keeps bench numbers stable across re-traces).
        profiles = await repo.half_widths_for_source(source.style_id, source_id)
        nibs = [statistics.median(hw) for hw in profiles if hw]
        constant_nib_units = float(statistics.mean(nibs)) if nibs else None

    pages: dict[str, np.ndarray] = {}
    page_shas: dict[str, str] = {}
    for w in words:
        page = w["page"]
        if page not in pages:
            page_path = REPO_ROOT / "data" / "sources" / source_id / page
            pages[page] = _load_page(page_path)
            page_shas[page] = hashlib.sha256(page_path.read_bytes()).hexdigest()

    fixture_root = out_dir / source.style_id / source_id
    fixture_root.mkdir(parents=True, exist_ok=True)
    (fixture_root / "templates.json").write_text(json.dumps(templates, ensure_ascii=False))

    word_index = []
    for w in words:
        missing = [k for k in glyph_keys_of([_slot(s) for s in shaped[w["word"]]]) if k not in templates]
        word_dir = fixture_root / w["word"]
        word_dir.mkdir(exist_ok=True)

        crop = pages[w["page"]][w["y0"] : w["y1"], w["x0"] : w["x1"]].copy()
        # Foreign ink from neighbouring lines: paint paper-white before binarising.
        for ex0, ey0, ex1, ey1 in w.get("exclude", []):
            crop[max(0, ey0 - w["y0"]) : max(0, ey1 - w["y0"]), max(0, ex0 - w["x0"]) : max(0, ex1 - w["x0"])] = 1.0
        mask = _despeckle(binarize_adaptive(crop))
        skel, width_map = skeleton_and_width(mask)

        (word_dir / "word.json").write_text(
            json.dumps(
                {
                    "word": w["word"],
                    "page": w["page"],
                    "rect": [w["x0"], w["y0"], w["x1"], w["y1"]],
                    "baseline_y": w["baseline_y"],
                    "midband_y": w["midband_y"],
                    "slots": shaped[w["word"]],
                    "missing_at_export": missing,
                },
                ensure_ascii=False,
            )
        )
        Image.fromarray((np.clip(crop, 0.0, 1.0) * 255).astype(np.uint8), mode="L").save(word_dir / "crop.png")
        Image.fromarray((mask * 255).astype(np.uint8), mode="L").save(word_dir / "ref_mask.png")
        np.savez_compressed(word_dir / "ref_skel.npz", skel=skel, width_map=width_map.astype(np.float32))
        word_index.append({"word": w["word"], "page": w["page"], "missing_at_export": missing})

    manifest = {
        "exported_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_id": source_id,
        "style_id": source.style_id,
        "page_sha256": page_shas,
        "style_ratio": source.style_ratio or (style.default_style_ratio if style else None),
        "width_resolver": style.width_resolver if style else None,
        "constant_nib_units": constant_nib_units,
        "words": word_index,
    }
    (fixture_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    print(f"exported {len(word_index)} words to {fixture_root}")
    incomplete = [w for w in word_index if w["missing_at_export"]]
    if incomplete:
        print(f"  words with missing templates at export: {[(w['word'], w['missing_at_export']) for w in incomplete]}")


def _slot(d: dict):
    from core.shaping import GlyphSlot

    return GlyphSlot(**d)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE_ID, help="source id (default: suetterlin-1922)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR, help="fixtures output dir")
    args = parser.parse_args()

    load_dotenv()  # before any core.database import — env is read at import time
    asyncio.run(export(args.source, args.out))


if __name__ == "__main__":
    main()
