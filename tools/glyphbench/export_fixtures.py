"""Snapshot locked templates + frozen scoring references from the DB to disk.

The glyph bench (`tools/glyphbench/run.py`) must be hermetic and fast: every
experiment iteration re-derives canonicals from the committed chart bytes plus
the snapshotted raw traces, with NO database access. This script is the single
place that touches the DB — read-only (repository SELECTs, nothing else) — and
freezes the scoring references (binarized mask, skeleton, EDT width map) at
export time, so a pipeline experiment cannot "improve" the metric by moving
the target (e.g. by loosening the binarization). Re-running the export is an
explicit human re-baseline.

Only rows the bench can actually re-derive are exported: a template needs a
stylus path, so the Laufform variant (a median over word occurrences, no chart
cell) and any untraced form variant are skipped and named in the run's output.
The root is REPLACED on every export, never merged into — glyph_keys change
shape between schemas, and a stray directory from an older one is invisible.
The replacement runs through a staging sibling and a final swap, so a failed
export leaves the previous root intact rather than half of a new one.

Fixture layout (gitignored — regenerate at will):

    fixtures/<style_id>/<source_id>/
      manifest.json            # export stamp, chart sha256, glyph index
      <glyph_key>/
        template.json          # full template row (anchors, raw_path, trace_meta, ...)
        bbox.json              # crop rect, eraser mask, calibration, n_anchors, locked
        crop.png               # grayscale crop with eraser applied (overlay background)
        ref_mask.png           # FROZEN binarized scoring reference
        ref_skel.npz           # FROZEN skeleton (bool) + EDT half-width map (float32)

Usage:
    uv run python -m tools.glyphbench.export_fixtures [--source loth-1866]
        [--out tools/glyphbench/fixtures] [--include-unlocked] [--no-dedupe]
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from PIL import Image

from core.chart import crop_with_mask, load_chart_grayscale, resolve_chart_path
from core.extract import binarize_adaptive, skeleton_and_width


DEFAULT_SOURCE_ID = "loth-1866"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent / "fixtures"


def _bbox_dict(bbox) -> dict:
    return {
        "glyph_key": bbox.glyph_key,
        "y0": bbox.y0,
        "y1": bbox.y1,
        "x0": bbox.x0,
        "x1": bbox.x1,
        "mask_strokes": bbox.mask_strokes or [],
        "baseline_y": bbox.baseline_y,
        "midband_y": bbox.midband_y,
        "n_anchors": bbox.n_anchors,
        "locked": bbox.locked,
    }


def _template_dict(template) -> dict:
    return {
        "glyph_key": template.glyph_key,
        "glyph": template.glyph,
        "variant": template.variant,
        "advance": template.advance,
        "entry": template.entry,
        "exit_pt": template.exit_pt,
        "anchors": template.anchors,
        "half_widths": template.half_widths,
        "raw_path": template.raw_path,
        "trace_meta": template.trace_meta,
        "measurements": template.measurements,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }


def _dedupe_templates(entries: list[tuple[dict, dict]]) -> tuple[list[tuple[dict, dict, list[str]]], int]:
    """Collapse identical fan-out copies (same glyph, raw_path AND crop config) to one entry.

    The wizard writes the same authored form across initial/medial/final by
    default — benching all three runs the identical computation three times.
    The digest covers everything the bench computation depends on: the raw
    trace plus the computation-relevant bbox fields (rect, eraser mask,
    calibration, anchor count) — positions that genuinely differ in any of
    these stay separate entries. Returns (kept entries with their covered
    positions, number dropped).
    """
    by_key: dict[tuple[str, str], tuple[dict, dict, list[str]]] = {}  # insertion order = first occurrence
    for template, bbox in sorted(entries, key=lambda e: e[0]["glyph_key"]):
        computation_inputs = {
            "raw_path": template["raw_path"],
            "bbox": {
                k: bbox[k] for k in ("y0", "y1", "x0", "x1", "mask_strokes", "baseline_y", "midband_y", "n_anchors")
            },
        }
        digest = hashlib.sha256(json.dumps(computation_inputs, sort_keys=True).encode()).hexdigest()
        key = (template["glyph"], digest)
        if key in by_key:
            by_key[key][2].append(template["glyph_key"])
        else:
            by_key[key] = (template, bbox, [template["glyph_key"]])
    kept = list(by_key.values())
    return kept, len(entries) - len(kept)


def select_exportable(
    templates: Sequence, bboxes: Mapping[str, object], include_unlocked: bool
) -> tuple[list[tuple[dict, dict]], int, list[str]]:
    """The rows the bench can actually score, plus what was left behind and why.

    Two filters, and the second one is the reason this function exists. A
    template needs a bbox and (unless `include_unlocked`) a locked one — that
    has always been true. It ALSO needs a stylus path: the bench re-derives
    every canonical from the chart bytes plus that path, and every row lands in
    the shared per-key directory `<glyph_key>/`, so a row without a path both
    fails to score and OVERWRITES the chart row that would have.

    That is what the Laufform rows (variant 100) did once the 1922 source
    acquired them. A Laufform is a median over word occurrences — no chart
    cell, no trace — and because the export walks templates ordered by
    `(glyph_key, variant)` it ran last and won. The first re-export after the
    LF11 write came back with 22 keys whose `template.json` was the Laufform
    and 44 crashes (each such key appeared twice in the index).

    The test is the PATH, not the variant number: an authored form variant that
    was never traced is just as underivable, and the 1922 `i` at variant 1 is
    exactly that case.

    Returns the (template, bbox) dicts to export, how many rows were skipped as
    unlocked, and a `glyph_key#variant` label for every row skipped for want of
    a trace — named rather than counted, because a silently shrinking export is
    the failure this whole function guards against.
    """
    entries: list[tuple[dict, dict]] = []
    skipped_unlocked = 0
    skipped_no_trace: list[str] = []
    for template in templates:
        bbox = bboxes.get(template.glyph_key)
        if bbox is None:
            continue
        if not bbox.locked and not include_unlocked:
            skipped_unlocked += 1
            continue
        if len(template.raw_path or []) < 2:
            skipped_no_trace.append(f"{template.glyph_key}#{template.variant}")
            continue
        entries.append((_template_dict(template), _bbox_dict(bbox)))
    return entries, skipped_unlocked, skipped_no_trace


def write_fixture_root(
    fixture_root: Path, kept: list[tuple[dict, dict, list[str]]], chart_gray, manifest_base: dict
) -> list[dict]:
    """Serialise the whole root into a staging sibling, then swap it in.

    Replace rather than merge: glyph_keys change shape over time (the position
    suffixes of `A-final` died with migration `0017`), and a directory left
    behind from an older schema sits in the tree looking exactly like a current
    one — the June 2026 root still carried 52 such strays when this was written.

    But replacing cannot mean deleting first. A frozen root IS the reference
    every quoted number stands on, so a crop, binarisation or write failure
    halfway through must not leave the tree with neither the old baseline nor a
    usable new one. Everything is built beside the root and moved into place at
    the end; a failure removes the staging directory and leaves the previous
    root exactly as it was.

    The manifest is written last, so a staging directory that somehow survives
    is visibly incomplete rather than plausible.

    Returns the glyph index that went into the manifest.
    """
    staging = fixture_root.with_name(f"{fixture_root.name}.staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    try:
        glyph_index: list[dict] = []
        for template, bbox, positions in kept:
            glyph_dir = staging / template["glyph_key"]
            glyph_dir.mkdir(exist_ok=True)

            crop = crop_with_mask(chart_gray, bbox, fill=1.0)
            mask = binarize_adaptive(crop)
            skel, width_map = skeleton_and_width(mask)

            (glyph_dir / "template.json").write_text(json.dumps(template, ensure_ascii=False))
            (glyph_dir / "bbox.json").write_text(json.dumps(bbox, ensure_ascii=False))
            Image.fromarray((np.clip(crop, 0.0, 1.0) * 255).astype(np.uint8), mode="L").save(glyph_dir / "crop.png")
            Image.fromarray((mask * 255).astype(np.uint8), mode="L").save(glyph_dir / "ref_mask.png")
            np.savez_compressed(glyph_dir / "ref_skel.npz", skel=skel, width_map=width_map.astype(np.float32))

            glyph_index.append(
                {
                    "glyph_key": template["glyph_key"],
                    "glyph": template["glyph"],
                    # Carried so a second row on the same key is VISIBLE in the
                    # index; without it the two entries a key with a Laufform
                    # produced were indistinguishable, and the bench dutifully
                    # scored the same directory twice.
                    "variant": template["variant"],
                    "positions": sorted(positions),
                    "n_anchors": bbox["n_anchors"],
                    "locked": bbox["locked"],
                    "updated_at": template["updated_at"],
                }
            )

        manifest = {
            "exported_at": datetime.now(UTC).isoformat(timespec="seconds"),
            **manifest_base,
            "glyphs": glyph_index,
        }
        (staging / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    # From here only two directory operations remain.
    if fixture_root.exists():
        shutil.rmtree(fixture_root)
    staging.rename(fixture_root)
    return glyph_index


async def export(source_id: str, out_dir: Path, include_unlocked: bool, dedupe: bool) -> None:
    # Imported here, after load_dotenv(): the connection module reads env at import time.
    from core.database.connection import get_db_context
    from core.database.repositories import BboxRepository, SourceRepository, StyleRepository, TemplateRepository

    async with get_db_context() as session:
        source = await SourceRepository(session).get(source_id)
        if source is None:
            raise SystemExit(f"source {source_id!r} not found")
        style = await StyleRepository(session).get(source.style_id)
        bboxes = {b.glyph_key: b for b in await BboxRepository(session).list(source_id)}
        templates = await TemplateRepository(session).list(source.style_id)

    entries, skipped_unlocked, skipped_no_trace = select_exportable(templates, bboxes, include_unlocked)

    if dedupe:
        kept, n_deduped = _dedupe_templates(entries)
    else:
        kept = [(t, b, [t["glyph_key"]]) for t, b in sorted(entries, key=lambda e: e[0]["glyph_key"])]
        n_deduped = 0

    chart_abs = resolve_chart_path(source.chart_path)
    chart_sha256 = hashlib.sha256(chart_abs.read_bytes()).hexdigest()
    chart_gray = load_chart_grayscale(source.chart_path)

    fixture_root = out_dir / source.style_id / source_id
    manifest_base = {
        "source_id": source_id,
        "style_id": source.style_id,
        "chart_path": source.chart_path,
        "chart_sha256": chart_sha256,
        "style_ratio": source.style_ratio or (style.default_style_ratio if style else None),
        "slant_deg": source.slant_deg or (style.default_slant_deg if style else None),
        "width_resolver": style.width_resolver if style else None,
    }
    glyph_index = write_fixture_root(fixture_root, kept, chart_gray, manifest_base)

    print(f"exported {len(glyph_index)} glyphs to {fixture_root}")
    print(f"  deduped fan-out copies: {n_deduped}")
    print(f"  skipped unlocked:       {skipped_unlocked}" + ("" if not include_unlocked else " (included)"))
    print(
        f"  skipped without trace:  {len(skipped_no_trace)}"
        + (f" ({', '.join(skipped_no_trace)})" if skipped_no_trace else "")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE_ID, help="source id (default: loth-1866)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR, help="fixtures output dir")
    parser.add_argument(
        "--include-unlocked", action="store_true", help="also export templates whose bbox is not locked"
    )
    parser.add_argument("--no-dedupe", action="store_true", help="keep identical positional fan-out copies")
    args = parser.parse_args()

    load_dotenv()  # before any core.database import — env is read at import time
    asyncio.run(export(args.source, args.out, args.include_unlocked, not args.no_dedupe))


if __name__ == "__main__":
    main()
