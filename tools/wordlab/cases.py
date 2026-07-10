"""Load a word's composition inputs from a frozen fixture or (read-only) the DB.

A `WordCase` is everything the composer needs to lay one word out — its shaped
`slots` (frozen at export, so a shaping change is a deliberate re-baseline) and
the per-glyph `templates` — plus the same-hand specimen a word bench run scores
against (the crop, its skeleton and the measured lineature). Two sources:

* `fixture_word_case` / `iter_fixture_word_cases` — the frozen word-bench
  fixtures (`tools/wordbench/fixtures`, exported by
  `tools/wordbench/export_fixtures.py`). Fully offline, deterministic, no DB;
  carries the specimen so the overlay and the metric both work.
* `live_word_case` — a READ-ONLY pull mirroring the `/word` endpoint: shape the
  text, fetch the templates that exist, resolve the style + source-pooled nib.
  No writes are ever issued, and there is NO specimen (crop/skel/rect are None),
  so it renders the composed word in its own units. Needs `DATABASE_URL`; `.env`
  is auto-loaded so `python -m tools.wordlab --live` just works.
"""

from __future__ import annotations

import json
import os
import statistics
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from core.shaping import GlyphSlot


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES_DIR = REPO_ROOT / "tools" / "wordbench" / "fixtures"


@dataclass
class WordCase:
    """All inputs needed to compose + score one word, plus its provenance label.

    The specimen fields (`rect`, `baseline_y`, `midband_y`, `crop`, `skel`) are
    all None for a live case — it has no reference to overlay or score against.
    """

    id: str  # fixture entry id, e.g. "Einen" / "wenn-2"; the text for a live case
    word: str  # the display text
    kind: str  # "word" | "pair"
    slots: list[GlyphSlot]
    templates: dict[str, dict]  # glyph_key -> template row (render_payload_for_template input)
    style_ratio: list[float]
    width_resolver: str  # "constant" (Gleichzug) | "pressure" | "broad_nib"
    nib_units: float | None  # source-pooled Gleichzug nib radius (x-height units)
    origin: str = ""  # human label, e.g. "fixture:suetterlin-1922" / "live:suetterlin-1922"
    scorable: bool = True  # a needed template is unauthored → the metric cannot score it
    # ---- specimen (None for a live case) ----
    rect: list[int] | None = None  # [x0, y0, x1, y1] crop on the source page
    baseline_y: int | None = None  # page-pixel lineature (crop-local = value - rect[1])
    midband_y: int | None = None
    crop: np.ndarray | None = None  # float [0, 1], shape (H, W) — overlay background
    skel: np.ndarray | None = None  # bool, the frozen scoring skeleton
    extra: dict = field(default_factory=dict)  # updated_at, … (informational)

    @property
    def has_specimen(self) -> bool:
        """True only when EVERY specimen field is present — derive/render use
        the lineature and rect as unconditionally as the crop and skeleton."""
        return (
            self.crop is not None
            and self.skel is not None
            and self.rect is not None
            and self.baseline_y is not None
            and self.midband_y is not None
        )


def _load_page_float(path: Path) -> np.ndarray:
    """Grayscale image as float in [0, 1] (same convention as core.chart / the crop)."""
    return np.asarray(Image.open(path).convert("L"), dtype=np.float64) / 255.0


# ------------------------------------------------------------------- fixtures


def _root_for(fixtures_root: Path, style: str, which: str) -> Path:
    """Return the fixture root whose manifest `set` matches `which` under `style`.

    A word set freezes into `<source_id>` and its pairs into `<source_id>-pairs`
    (sibling roots with their own manifests), so the manifest's `set` field — not
    the directory name — is the reliable discriminator; the first match wins (one
    source per style today).
    """
    style_root = fixtures_root / style
    for manifest_path in sorted(style_root.glob("*/manifest.json")):
        if json.loads(manifest_path.read_text()).get("set", "words") == which:
            return manifest_path.parent
    raise KeyError(f"no {which!r} fixtures under {style_root} — run tools/wordbench/export_fixtures first")


def _case_from(root: Path, manifest: dict, templates: dict, entry: dict) -> WordCase:
    """Build a WordCase from an already-loaded manifest entry (no rescan)."""
    entry_id = entry.get("id", entry["word"])
    word_meta = json.loads((root / entry_id / "word.json").read_text())
    skel = np.load(root / entry_id / "ref_skel.npz")["skel"]
    crop = _load_page_float(root / entry_id / "crop.png")
    return WordCase(
        id=entry_id,
        word=word_meta["word"],
        kind=word_meta.get("kind", "word"),
        slots=[GlyphSlot(**s) for s in word_meta["slots"]],
        templates=templates,
        style_ratio=manifest.get("style_ratio") or [1, 1, 1],
        width_resolver=manifest.get("width_resolver") or "pressure",
        nib_units=manifest.get("constant_nib_units"),
        origin=f"fixture:{root.name}",
        scorable=bool(word_meta.get("scorable", not word_meta.get("missing_at_export"))),
        rect=word_meta["rect"],
        baseline_y=word_meta["baseline_y"],
        midband_y=word_meta["midband_y"],
        crop=crop,
        skel=skel,
    )


def fixture_word_case(
    entry_id: str, *, which: str = "words", style: str = "suetterlin", fixtures_root: Path = DEFAULT_FIXTURES_DIR
) -> WordCase:
    """Load one frozen word-bench fixture by id (its `word` text is accepted too).

    `which` in {"words", "pairs"} selects the sibling root. A frozen-unscorable
    entry (a needed template is unauthored) still loads — you may want to LOOK at
    what composes — with `scorable=False`; the derivation reports the hole.
    """
    root = _root_for(fixtures_root, style, which)
    manifest = json.loads((root / "manifest.json").read_text())
    templates = json.loads((root / "templates.json").read_text())
    for entry in manifest["words"]:
        if entry.get("id", entry["word"]) == entry_id or entry["word"] == entry_id:
            return _case_from(root, manifest, templates, entry)
    raise KeyError(
        f"no fixture entry {entry_id!r} under {root} (ids: {[w.get('id', w['word']) for w in manifest['words']][:8]}…)"
    )


def iter_fixture_word_cases(
    *,
    which: str = "words",
    style: str = "suetterlin",
    only: list[str] | None = None,
    fixtures_root: Path = DEFAULT_FIXTURES_DIR,
) -> list[WordCase]:
    """All fixture word cases of a set (optionally filtered to `only` ids/words).

    The manifest + templates are read once and each case built directly from
    them (no per-entry rescan), so `--all` stays linear in the number of words.
    """
    root = _root_for(fixtures_root, style, which)
    manifest = json.loads((root / "manifest.json").read_text())
    templates = json.loads((root / "templates.json").read_text())
    cases: list[WordCase] = []
    for entry in manifest["words"]:
        entry_id = entry.get("id", entry["word"])
        if only is not None and entry_id not in only and entry["word"] not in only:
            continue
        cases.append(_case_from(root, manifest, templates, entry))
    return cases


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


def _template_row(t) -> dict:
    """ORM Template → the plain dict render_payload_for_template consumes."""
    return {
        "anchors": list(t.anchors),
        "half_widths": list(t.half_widths),
        "trace_meta": dict(t.trace_meta or {}),
        "entry": dict(t.entry) if t.entry else {},
        "exit_pt": dict(t.exit_pt) if t.exit_pt else {},
        "advance": t.advance,
    }


async def live_word_case(text: str, source_id: str = "suetterlin-1922") -> WordCase:
    """READ-ONLY: shape `text` and pull the templates it needs from Cloud SQL.

    Mirrors the public `/word` endpoint: NFC-normalise + trim, shape (long-s
    rule + closed ligature set), fetch the templates that exist with the
    ligature-decompose fallback, resolve the style ratio/resolver and the
    source-pooled Gleichzug nib (median per profile, mean over profiles — the
    same pooling as export_fixtures / api.rendering). Issues only SELECTs. A
    one-letter text is a valid case; whatever has no template composes as a gap.
    """
    normalized = unicodedata.normalize("NFC", text).strip()
    if not normalized:
        raise ValueError("text must contain at least one non-space character")

    _load_dotenv()
    from core.database.connection import close_db, get_db_context  # noqa: PLC0415 — import after dotenv
    from core.database.repositories import SourceRepository, StyleRepository, TemplateRepository  # noqa: PLC0415
    from core.shaping import decompose_ligature_slot, glyph_keys_of, shape_text  # noqa: PLC0415

    try:
        async with get_db_context() as s:
            src = await SourceRepository(s).get(source_id)
            if src is None:
                raise KeyError(f"no source {source_id!r} in DB")
            style = await StyleRepository(s).get(src.style_id)
            if style is None:
                raise KeyError(f"source {source_id!r} references unknown style {src.style_id!r}")
            repo = TemplateRepository(s)

            slots = shape_text(normalized)
            keys = glyph_keys_of(slots)
            rows = {t.glyph_key: _template_row(t) for t in await repo.get_many(src.style_id, keys)}
            # Ligature fallback (one extra query, only when something is missing) —
            # mirrors write.py so a closed-set cluster without a canonical decomposes.
            if any(sl.ligature and sl.key and sl.key not in rows for sl in slots):
                expanded: list[GlyphSlot] = []
                for sl in slots:
                    if sl.ligature and sl.key and sl.key not in rows:
                        expanded.extend(decompose_ligature_slot(sl) or [sl])
                    else:
                        expanded.append(sl)
                slots = expanded
                keys = glyph_keys_of(slots)
                extra = [k for k in keys if k not in rows]
                for t in await repo.get_many(src.style_id, extra):
                    rows[t.glyph_key] = _template_row(t)

            style_ratio = list(src.style_ratio) if src.style_ratio is not None else list(style.default_style_ratio)
            nib_units = None
            if style.width_resolver == "constant":
                profiles = await repo.half_widths_for_source(src.style_id, source_id)
                nibs = [statistics.median(hw) for hw in profiles if hw]
                nib_units = float(statistics.mean(nibs)) if nibs else None

            missing = [k for k in keys if k not in rows]
            return WordCase(
                id=normalized,
                word=normalized,
                kind="word",
                slots=slots,
                templates=rows,
                style_ratio=style_ratio,
                width_resolver=style.width_resolver,
                nib_units=nib_units,
                origin=f"live:{source_id}",
                scorable=not missing,
            )
    finally:
        await close_db()


def live_word_case_sync(text: str, source_id: str = "suetterlin-1922") -> WordCase:
    """Blocking wrapper around `live_word_case` for scripts/CLI."""
    import asyncio  # noqa: PLC0415

    return asyncio.run(live_word_case(text, source_id))
