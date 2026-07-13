"""Snapshot templates + frozen word-scoring references for the word bench.

Mirrors tools/glyphbench/export_fixtures.py: this is the ONLY module in the
package that touches the DB — read-only SELECTs — and it freezes everything a
bench run scores against, so an experiment on the composer cannot move the
goalposts. Frozen per word: the crop (from the committed page bytes + the
words.json sidecar), the binarized scoring mask, the skeleton + EDT width map,
and the SHAPED SLOTS (so a later shaping change is a deliberate re-baseline,
not a silent input shift). Frozen per source: the template rows the words need
and the source-pooled Gleichzug nib.

Sidecar entries may carry (all optional, additive):
  id     — unique fixture key; defaults to the word text. Required in practice
           for repeated words on the plate ("und" appears three times).
  kind   — "word" (default) or "pair" (isolated letter-pair joins, Abb. 20).
           Falls back to "pair" for entries on a pairs-* page.
  set    — explicit fixture-set name for entries that must NOT join the
           default sets (e.g. "abb22" for the Schülerschrift plate: same
           norm, DIFFERENT writer — never averaged into the same-hand
           headline). Defaults to "words"/"pairs" by kind.
  slots  — explicit slot list [{key, text, position, ligature?}] overriding
           shape_text, for pairs whose isolated drawing does not match
           word-context shaping.

Each set freezes into its own SIBLING root (``<source_id>``,
``<source_id>-pairs``, ``<source_id>-<set>``) with its own manifest, so
exporting one set never regenerates another and headline numbers never mix.

Entries needing a template that is not authored yet freeze with
``scorable: false`` — the runner skips and reports them instead of drowning
the headline in 1.0s (a missing capital is an authoring gap, not a
composition failure; a template that exists but composes badly still scores).

Fixture layout (gitignored — regenerate at will):

    fixtures/<style_id>/<source_id>[-<set>]/   # words -> <source_id>, pairs/custom -> suffixed
      manifest.json            # export stamp, set, page sha256s, style ratio/resolver, pooled nib, word index
      templates.json           # glyph_key -> template row (anchors, half_widths, trace_meta, entry, exit_pt, advance)
      <id>/
        word.json              # id, text, kind, rect, lineature, frozen slots, scorable
        crop.png               # grayscale crop (excludes applied) — overlay background
        ref_mask.png           # FROZEN binarized scoring reference
        ref_skel.npz           # FROZEN skeleton (bool) + EDT half-width map (float32)

Usage:
    uv run python -m tools.wordbench.export_fixtures [--source suetterlin-1922]
        [--set words|pairs|<custom set like abb22>|all] [--out tools/wordbench/fixtures]
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import statistics
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from dotenv import load_dotenv
from PIL import Image
from scipy.ndimage import label as cc_label

from core.extract import binarize_adaptive, skeleton_and_width
from core.shaping import GlyphSlot, decompose_ligature_slot, glyph_keys_of, shape_text


if TYPE_CHECKING:
    from core.database.models import Template


DEFAULT_SOURCE_ID = "suetterlin-1922"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _template_dict(t: Template) -> dict:
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


def load_page(path: Path) -> np.ndarray:
    """Page image as float grayscale in [0, 1] (same convention as core.chart)."""
    return np.asarray(Image.open(path).convert("L"), dtype=np.float64) / 255.0


# Paper grain survives the adaptive binarisation as scattered 1–10 px specks;
# their skeletons would put a noise floor under the reverse chamfer. Real marks
# stay: the smallest genuine ink component (an i-dot) is ~50 px² at this scale.
DESPECKLE_MIN_AREA_PX = 24

# A connected component whose pixels lie at least this fraction inside the
# entry's exclude rects is foreign ink and removed WHOLE (tails included).
# The jul05 export instead painted the excludes paper-white BEFORE binarising;
# the hard white→paper step at the painted border binarised as a fake
# full-width ink line whose skeleton dominated the references of exactly the
# excluded words (up to 30 % of wenn-2's skeleton pixels — wordlab finding,
# 2026-07-08). Binarising the unpainted crop creates no such edge; the auto
# excludes are the foreign components' own bounding boxes, so they contain
# their component almost entirely.
EXCLUDE_COMPONENT_FRAC = 0.5


def clear_excluded(mask: np.ndarray, rects: list[tuple[int, int, int, int]]) -> np.ndarray:
    """Remove foreign ink under crop-local exclude rects from a binarised mask.

    Two layers: every pixel strictly inside a rect is cleared, and every
    connected component with ≥ EXCLUDE_COMPONENT_FRAC of its area inside the
    rect union is removed whole — so a descender tail poking out of its rect
    does not survive as an ink stub (its skeleton would poison the reverse
    chamfer). Word ink is safe: it never lies half inside an exclude.
    """
    if not rects:
        return mask
    inside = np.zeros_like(mask)
    for x0, y0, x1, y1 in rects:
        inside[max(0, y0) : max(0, y1), max(0, x0) : max(0, x1)] = True
    labels, n = cc_label(mask)
    if n:
        sizes = np.bincount(labels.ravel(), minlength=n + 1)
        inside_sizes = np.bincount(labels[inside].ravel(), minlength=n + 1)
        kill = inside_sizes >= EXCLUDE_COMPONENT_FRAC * sizes
        kill[0] = False
        mask = mask & ~kill[labels]
    return mask & ~inside


def despeckle(mask: np.ndarray) -> np.ndarray:
    labels, n = cc_label(mask)
    if not n:
        return mask
    sizes = np.bincount(labels.ravel())
    keep = sizes >= DESPECKLE_MIN_AREA_PX
    keep[0] = False
    return keep[labels]


def _kind(w: dict) -> str:
    return w.get("kind") or ("pair" if w["page"].startswith("pairs") else "word")


def _set_name(w: dict) -> str:
    """Fixture set of a sidecar entry: explicit ``set`` or the kind default.

    ``all`` is reserved for the runner's aggregate mode — a fixture set named
    that way could never be run explicitly. The name becomes a single fixture
    directory component (``<source>-<set>``); the runner and wordlab discover
    roots with a one-level ``*/manifest.json`` glob, so a name with a path
    separator or whitespace would export into an undiscoverable nested path —
    reject it as a path-unsafe token instead.
    """
    name = w.get("set") or ("pairs" if _kind(w) == "pair" else "words")
    if name == "all":
        raise SystemExit(f"sidecar entry {_entry_id(w)!r} uses the reserved set name 'all'")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        raise SystemExit(
            f"sidecar entry {_entry_id(w)!r} has a path-unsafe set name {name!r} "
            "(allowed: letters, digits, '.', '_', '-')"
        )
    return name


def _root_name(source_id: str, set_name: str) -> str:
    return source_id if set_name == "words" else f"{source_id}-{set_name}"


def _entry_id(w: dict) -> str:
    return w.get("id", w["word"])


def _shape_entry(w: dict, have: set[str]) -> list[GlyphSlot]:
    """Frozen slots for one sidecar entry: explicit override or shape_text with
    the ligature-decompose fallback against the current template inventory."""
    if "slots" in w:
        return [
            GlyphSlot(
                key=s["key"],
                text=s.get("text", w["word"]),
                position=s.get("position"),
                ligature=bool(s.get("ligature", False)),
                space=False,
            )
            for s in w["slots"]
        ]
    slots = shape_text(w["word"])
    if any(s.ligature and s.key and s.key not in have for s in slots):
        slots = [
            d
            for s in slots
            for d in ((decompose_ligature_slot(s) or [s]) if s.ligature and s.key and s.key not in have else [s])
        ]
    return slots


async def export(source_id: str, out_dir: Path, which: str) -> None:
    sidecar_path = REPO_ROOT / "data" / "sources" / source_id / "words.json"
    if not sidecar_path.exists():
        raise SystemExit(f"no word sidecar at {sidecar_path}")
    sidecar = json.loads(sidecar_path.read_text())
    entries = [w for w in sidecar["words"] if which == "all" or _set_name(w) == which]
    if not entries:
        known = sorted({_set_name(w) for w in sidecar["words"]})
        raise SystemExit(f"no {which!r} entries in {sidecar_path} (sets present: {known})")
    id_counts = Counter(_entry_id(w) for w in sidecar["words"])
    dupes = [i for i, n in id_counts.items() if n > 1]
    if dupes:
        raise SystemExit(f"duplicate sidecar ids {sorted(dupes)} — give repeated words an explicit 'id'")

    # Imported here, after load_dotenv(): the connection module reads env at import time.
    from core.database.connection import get_db_context
    from core.database.repositories import SourceRepository, StyleRepository, TemplateRepository

    async with get_db_context() as session:
        source = await SourceRepository(session).get(source_id)
        if source is None:
            raise SystemExit(f"source {source_id!r} not found")
        style = await StyleRepository(session).get(source.style_id)
        repo = TemplateRepository(session)

        # Shape every entry, apply the ligature-decompose fallback against the
        # CURRENT template inventory, and freeze the resulting slots.
        shaped: dict[str, list[dict]] = {}
        needed: dict[str, dict[str, None]] = {}
        for w in entries:
            keys = glyph_keys_of(shape_text(w["word"]))
            have = {t.glyph_key for t in await repo.get_many(source.style_id, keys)}
            slots = _shape_entry(w, have)
            shaped[_entry_id(w)] = [asdict(s) for s in slots]
            for k in glyph_keys_of(slots):
                needed.setdefault(_set_name(w), {}).setdefault(k)

        all_keys = list({k: None for keys in needed.values() for k in keys})
        templates = {t.glyph_key: _template_dict(t) for t in await repo.get_many(source.style_id, all_keys)}
        # Source-pooled Gleichzug nib, frozen at export (api.rendering computes
        # the same live; freezing keeps bench numbers stable across re-traces).
        profiles = await repo.half_widths_for_source(source.style_id, source_id)
        nibs = [statistics.median(hw) for hw in profiles if hw]
        constant_nib_units = float(statistics.mean(nibs)) if nibs else None

    pages: dict[str, np.ndarray] = {}
    page_shas: dict[str, str] = {}
    for w in entries:
        page = w["page"]
        if page not in pages:
            page_path = REPO_ROOT / "data" / "sources" / source_id / page
            pages[page] = load_page(page_path)
            page_shas[page] = hashlib.sha256(page_path.read_bytes()).hexdigest()

    for set_name in sorted(needed):
        kind_entries = [w for w in entries if _set_name(w) == set_name]
        if not kind_entries:
            continue
        fixture_root = out_dir / source.style_id / _root_name(source_id, set_name)
        fixture_root.mkdir(parents=True, exist_ok=True)
        kind_templates = {k: templates[k] for k in needed[set_name] if k in templates}
        (fixture_root / "templates.json").write_text(json.dumps(kind_templates, ensure_ascii=False))

        index = []
        for w in kind_entries:
            entry_id = _entry_id(w)
            slots = [GlyphSlot(**s) for s in shaped[entry_id]]
            missing = [k for k in glyph_keys_of(slots) if k not in templates]
            entry_dir = fixture_root / entry_id
            entry_dir.mkdir(exist_ok=True)

            crop = pages[w["page"]][w["y0"] : w["y1"], w["x0"] : w["x1"]].copy()
            rects = [
                (ex0 - w["x0"], ey0 - w["y0"], ex1 - w["x0"], ey1 - w["y0"])
                for ex0, ey0, ex1, ey1 in w.get("exclude", [])
            ]
            # Binarise the UNPAINTED crop (a painted-white exclude would leave a
            # fake ink line along its border — see clear_excluded), then remove
            # the foreign ink component-wise and despeckle the rest.
            mask = despeckle(clear_excluded(binarize_adaptive(crop), rects))
            # The saved crop is the human/overlay view: paint the excludes out.
            for x0, y0, x1, y1 in rects:
                crop[max(0, y0) : max(0, y1), max(0, x0) : max(0, x1)] = 1.0
            skel, width_map = skeleton_and_width(mask)

            (entry_dir / "word.json").write_text(
                json.dumps(
                    {
                        "id": entry_id,
                        "word": w["word"],
                        "kind": _kind(w),
                        "page": w["page"],
                        "rect": [w["x0"], w["y0"], w["x1"], w["y1"]],
                        "baseline_y": w["baseline_y"],
                        "midband_y": w["midband_y"],
                        "slots": shaped[entry_id],
                        "missing_at_export": missing,
                        "scorable": not missing,
                    },
                    ensure_ascii=False,
                )
            )
            Image.fromarray((np.clip(crop, 0.0, 1.0) * 255).astype(np.uint8), mode="L").save(entry_dir / "crop.png")
            Image.fromarray((mask * 255).astype(np.uint8), mode="L").save(entry_dir / "ref_mask.png")
            np.savez_compressed(entry_dir / "ref_skel.npz", skel=skel, width_map=width_map.astype(np.float32))
            index.append(
                {
                    "id": entry_id,
                    "word": w["word"],
                    "kind": _kind(w),
                    "page": w["page"],
                    "missing_at_export": missing,
                    "scorable": not missing,
                }
            )

        manifest = {
            "exported_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "source_id": source_id,
            "style_id": source.style_id,
            "set": set_name,
            "page_sha256": {p: s for p, s in page_shas.items() if any(w["page"] == p for w in kind_entries)},
            "style_ratio": source.style_ratio or (style.default_style_ratio if style else None),
            "width_resolver": style.width_resolver if style else None,
            "constant_nib_units": constant_nib_units,
            "words": index,
        }
        (fixture_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
        unscorable = [w for w in index if not w["scorable"]]
        print(f"exported {len(index)} {set_name} to {fixture_root} ({len(unscorable)} unscorable)")
        if unscorable:
            print(f"  missing templates: {[(w['id'], w['missing_at_export']) for w in unscorable]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE_ID, help="source id (default: suetterlin-1922)")
    parser.add_argument(
        "--set", dest="which", default="words", help="sidecar set to freeze (words | pairs | a custom set name | all)"
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR, help="fixtures output dir")
    args = parser.parse_args()

    load_dotenv()  # before any core.database import — env is read at import time
    asyncio.run(export(args.source, args.out, args.which))


if __name__ == "__main__":
    main()
