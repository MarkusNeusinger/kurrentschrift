"""Load a glyph's derivation inputs from a frozen fixture or (read-only) the DB.

A `GlyphCase` is everything `core` needs to re-derive one canonical: the dense
stylus `raw_path`, the `bbox` calibration (crop rect + eraser/ink brushes +
baseline/midband), the chart bytes path, and the style's `width_resolver` (which
picks the Sütterlin Gleichzug path vs. the pressure path). Two sources:

* `fixture_case` / `iter_fixture_cases` — the frozen glyph-bench fixtures
  (`tools/glyphbench/fixtures`). Fully offline, deterministic, no DB.
* `live_case` — a READ-ONLY pull of the authored template from Cloud SQL, to
  inspect what a user actually has stored (which can differ from the fixture).
  No writes are ever issued. Needs `DATABASE_URL` in the environment; `.env` is
  auto-loaded if present so `python -m tools.glyphlab --live` just works.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES_DIR = REPO_ROOT / "tools" / "glyphbench" / "fixtures"


@dataclass
class GlyphCase:
    """All inputs needed to re-derive one canonical, plus its provenance label."""

    key: str  # glyph_key, e.g. "i-initial"
    glyph: str  # the character, e.g. "i"
    position: str  # "initial" | "medial" | "final"
    raw_path: list[dict]
    bbox: dict
    chart_path: str  # relative to repo root
    width_resolver: str = "pressure"  # "constant" (Gleichzug) routes to suetterlin
    origin: str = ""  # human label, e.g. "fixture:suetterlin-1922" / "live:suetterlin-1922"
    extra: dict = field(default_factory=dict)  # locked, updated_at, … (informational)

    @property
    def is_constant(self) -> bool:
        return self.width_resolver == "constant"


def _abs_chart(chart_path: str) -> str:
    """Resolve a repo-relative chart path against the repo root if needed."""
    p = Path(chart_path)
    return str(p if p.is_absolute() else REPO_ROOT / p)


def _normalise_bbox(bbox: dict) -> dict:
    """Fill the optional brush/coupling keys so derivation never KeyErrors."""
    out = dict(bbox)
    out.setdefault("mask_strokes", [])
    out.setdefault("ink_strokes", [])
    out.setdefault("fill_holes_max_area", 0)
    out.setdefault("entry_coupling", "baseline")
    out.setdefault("exit_coupling", "baseline")
    return out


# ------------------------------------------------------------------- fixtures


def _manifest_for(key: str, fixtures_root: Path, source_id: str | None = None) -> tuple[Path, dict] | None:
    """Locate the manifest holding `key`, preferring `source_id` when given.

    A glyph_key (e.g. `f-final`, `longs-final`) can exist in BOTH the Kurrent and
    the Sütterlin fixture sets. Without a preference the first manifest alphabetically
    (kurrent < suetterlin) wins, which silently renders the wrong script's glyph.
    Preferring the caller's `source_id` (the CLI `--source`, default suetterlin-1922)
    picks the right one; it still falls back to any match for keys absent from that source.
    """
    candidates: list[tuple[Path, dict]] = []
    for manifest_path in sorted(fixtures_root.rglob("manifest.json")):
        manifest = json.loads(manifest_path.read_text())
        if any(g["glyph_key"] == key for g in manifest["glyphs"]):
            candidates.append((manifest_path, manifest))
    if not candidates:
        return None
    if source_id is not None:
        preferred = [c for c in candidates if c[1].get("source_id") == source_id]
        if preferred:
            return preferred[0]
    return candidates[0]


def _case_from(manifest_path: Path, manifest: dict, key: str) -> GlyphCase:
    """Build a GlyphCase from an already-loaded manifest (no manifest rescan)."""
    glyph_dir = manifest_path.parent / key
    tpl = json.loads((glyph_dir / "template.json").read_text())
    bbox = json.loads((glyph_dir / "bbox.json").read_text())
    return GlyphCase(
        key=key,
        glyph=tpl["glyph"],
        position=tpl["position"],
        raw_path=tpl["raw_path"],
        bbox=_normalise_bbox(bbox),
        chart_path=_abs_chart(manifest["chart_path"]),
        width_resolver=manifest.get("width_resolver", "pressure"),
        origin=f"fixture:{manifest_path.parent.name}",
    )


def fixture_case(key: str, fixtures_root: Path = DEFAULT_FIXTURES_DIR, source_id: str | None = None) -> GlyphCase:
    """Load one frozen fixture by glyph_key, preferring `source_id` on a key collision."""
    found = _manifest_for(key, fixtures_root, source_id)
    if found is None:
        raise KeyError(f"no fixture {key!r} under {fixtures_root}")
    return _case_from(*found, key)


def iter_fixture_cases(
    fixtures_root: Path = DEFAULT_FIXTURES_DIR, *, only: list[str] | None = None, source_id: str | None = None
) -> list[GlyphCase]:
    """All fixture cases (optionally filtered to `only` glyph_keys), sorted by key.

    Each manifest is read once and its cases built directly from it (no per-key
    rescan), so `--all` stays linear in the number of fixtures. When `source_id` is
    given, only that source's manifest is scanned — so `--all` shows one script's
    forms, not a Kurrent/Sütterlin mix where a shared key would otherwise collide.
    """
    cases: list[GlyphCase] = []
    seen: set[str] = set()
    for manifest_path in sorted(fixtures_root.rglob("manifest.json")):
        manifest = json.loads(manifest_path.read_text())
        if source_id is not None and manifest.get("source_id") != source_id:
            continue
        for entry in manifest["glyphs"]:
            key = entry["glyph_key"]
            if (only is not None and key not in only) or key in seen:
                continue
            seen.add(key)
            cases.append(_case_from(manifest_path, manifest, key))
    return sorted(cases, key=lambda c: c.key)


# ----------------------------------------------------------------- live (DB)


def _load_dotenv() -> None:
    """Populate os.environ from a repo `.env` if present (idempotent, no deps).

    Called only on the live path, BEFORE importing the DB modules, because
    `core.database.connection` reads `DATABASE_URL` at import time.
    """
    env = REPO_ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


async def live_case(source_id: str, glyph_key: str) -> GlyphCase:
    """READ-ONLY: build a GlyphCase from the authored template stored in Cloud SQL.

    Issues only SELECTs (Source/Style/Bbox/Template). Raises if the source,
    bbox or template is missing, or if the DB is not configured.
    """
    _load_dotenv()
    from core.database.connection import close_db, get_db_context  # noqa: PLC0415 — import after dotenv
    from core.database.repositories import (  # noqa: PLC0415
        BboxRepository,
        SourceRepository,
        StyleRepository,
        TemplateRepository,
    )

    try:
        async with get_db_context() as s:
            src = await SourceRepository(s).get(source_id)
            if src is None:
                raise KeyError(f"no source {source_id!r} in DB")
            style = await StyleRepository(s).get(src.style_id)
            bbox = await BboxRepository(s).get(source_id, glyph_key)
            tpl = await TemplateRepository(s).get(src.style_id, glyph_key)
            if bbox is None or tpl is None:
                missing = "bbox" if bbox is None else "template"
                raise KeyError(f"no {missing} for {glyph_key!r} under source {source_id!r}")
            bbox_dict = _normalise_bbox(
                {
                    "x0": bbox.x0,
                    "x1": bbox.x1,
                    "y0": bbox.y0,
                    "y1": bbox.y1,
                    "baseline_y": bbox.baseline_y,
                    "midband_y": bbox.midband_y,
                    "mask_strokes": bbox.mask_strokes or [],
                    "ink_strokes": bbox.ink_strokes or [],
                    "fill_holes_max_area": bbox.fill_holes_max_area,
                    "n_anchors": bbox.n_anchors,
                }
            )
            return GlyphCase(
                key=glyph_key,
                glyph=tpl.glyph,
                position=tpl.position,
                raw_path=tpl.raw_path,
                bbox=bbox_dict,
                chart_path=_abs_chart(src.chart_path),
                width_resolver=(style.width_resolver if style else "pressure"),
                origin=f"live:{source_id}",
                extra={"locked": bbox.locked, "updated_at": str(tpl.updated_at)},
            )
    finally:
        await close_db()


def live_case_sync(source_id: str, glyph_key: str) -> GlyphCase:
    """Blocking wrapper around `live_case` for scripts/CLI."""
    import asyncio  # noqa: PLC0415

    return asyncio.run(live_case(source_id, glyph_key))
