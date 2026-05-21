# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

In-progress MVP. The monorepo layout (per `docs/concepts/naming-und-setup.md` §3):

- `/core` — Pure-Python compute + DB layer. `core/extract.py` (skeleton + distance transform), `core/template.py` (canonical sampling + outline + slant), `core/chart.py` (load + crop with excludes), `core/pipeline.py` (`canonical_from_path`, `diagnostic_for_glyph`), `core/database/` (SQLAlchemy `Source` + `Bbox` + `Glyph` + repositories).
- `/api` — FastAPI service. Routers in `api/routers/`: `health`, `sources`, `chart`, `bboxes`, `glyphs`. All data lives in Postgres (DB `kurrentschrift` on the anyplot Cloud SQL instance, see `.env`).
- `/app` — React + Vite admin frontend (MUI). Single-page UI: drag bboxes/excludes on the Loth chart with mouse, draw stroke paths with stylus (Samsung S-Pen). Editor shows the 3-column SVG diagnostic (Loth crop · skeleton+anchors · canonical template) rendered from `/diagnostic` JSON. v1 only does canonical extraction.
- `/alembic` — Schema migrations. `0001_initial_schema.py` creates `sources` + `bboxes` + `glyphs` and seeds the Loth 1866 source row.
- `/data` — Sources, corpora, variants, samples, derived stats (see Data & licensing below). PD source bytes (Loth chart.jpg) stay on disk; the DB only stores the relative `chart_path`.

The earlier `/mvp/` folder (CLI tools + JSON files in the repo) was retired in favour of this DB-backed architecture. All canonicals now live in `glyphs.anchors`/`half_widths`/`raw_path`/`measurements` (JSONB columns), so `n_anchors` can be changed retroactively and per-instance stats are aggregatable in SQL.

**Local dev** (three steps): `uv run alembic upgrade head` (schema), `uv run uvicorn api.main:app --reload --port 8000`, then `cd app && npm install && npm run dev` (Vite on :3000 with `/api` proxy to the API). See `.claude/commands/start.md` for the slash command.

## Read these before substantive work

The design is already settled in the docs; do not re-litigate decisions that have an explicit "verworfen" (rejected) section. Start at `docs/index.md`.

- `docs/concepts/architektur.md` — architecture. §2 (analysis-by-synthesis), §3 (library schema), §4 (ligature exception), §5 (Schwellzug vs ink), §6 (3-stage quality pipeline), §7 (the one real research risk), §8 (MVP), §9 (test words), §10 (build order)
- `docs/concepts/mvp-roadmap.md` — actionable breakdown of §8 into Schritt 0 + M0–M6 milestones
- `docs/concepts/naming-und-setup.md` — repo/name/license/layout decisions
- `docs/reference/sprachregelung.md` — language rules (see below)
- `docs/reference/quellen-und-rechte.md` + `docs/reference/datenablage.md` — data/licensing rules (see below)

## Language conventions (strict)

From `docs/reference/sprachregelung.md`:

- **Code (identifiers, docstrings, comments): English, no exceptions.** Including commit messages.
- **README + GitHub description: English** (audience includes English-speaking genealogy).
- **Internal docs under `docs/`: German.** This is deliberate — the domain is German.
- **Website v1: German.**

German technical terms without an established English translation get an English identifier and one explanatory comment, e.g. `width_profile  # Schwellzug: pressure-driven stroke-width modulation`.

Characters themselves are *data, not code* — schema keys stay English, but values are the actual glyphs: `{"glyph": "ſt", "position": "medial", "variant": 0}`.

## The core architectural commitment

**Analysis-by-synthesis with a ductus prior.** The image supplies geometry + ink width; the canonical ductus template supplies stroke order and crossing resolution. The library unit is `(glyph, position, variant)`, not just glyph. Allographs (e.g. medial ſ vs. final s) are *separate glyphs* with separate ductus, not one glyph with variants. Positionally-sanctioned form variants (the "A = A" on teaching charts) are separate templates, not parameter deviations.

The closed ligature set (`ch`, `ck`, `tz`, `ſt`, `qu`, `ß`) are first-class library entries, not exit→entry chains. Enumerate, don't generate. Arbitrary letter pairs *are* generated from `exit`/`entry` tangents + coupling height — that's the whole point of avoiding a bigram explosion.

When in doubt about what's a glyph vs. a variant vs. a deviation, re-read `docs/concepts/architektur.md` §3 and §4.

## Data & licensing (this repo is unusual here)

Code is MIT. **Data is not covered by the code license** — each source carries its own. The `/data` tree lives outside `/core`, `/api`, `/app` precisely to keep this boundary visible.

Three commit classes, kept strictly separate (see `docs/reference/datenablage.md` §1):

1. **Committable:** `/data/sources/` (public-domain only, e.g. Loth 1866 SVG) and `/data/samples/own-hand/` (author's own copyright). Each gets a `SOURCE.md` with permalink, license, attribution, retrieval date.
2. **Gitignored:** `/data/corpora/` — only `SOURCE.md` + `fetch_corpus.py` are committed, never the data files. Pin DOI versions.
3. **Mixed:** `/data/derived/from-cc-by/` is committable; `/data/derived/from-nc-sa/` is gitignored (NC-SA collides with MIT).

Hard rules:

- **Süß' Lehrbuch and similar copyrighted works never enter the repo** — not as scans, not as redrawn glyphs, not as derived images. Bibliographic reference in prose is fine.
- A scan is not automatically free under German law (§72 UrhG). Prefer in order: own hand → explicit PD/CC0 → own photo of a PD original.
- "Script-downloaded" ≠ "license-free." The license of the bytes follows the bytes, not the fetch mechanism.
- Variant 0 (`v0-loth-1866`) is the canonical geometry baseline for first tests. The ductus prior is *the author's own contribution layered over* this PD geometry — Loth supplies shapes, not stroke order.

Before any data commit: *is this my expression or the expression of a protected source?* If unclear, link to the original rather than committing it.

## Test words

`lesen` (medial ſ, repeated e, ascender, u/n confusable final n) + `das` (final s) is the §9 Pflicht-Anker pair for the MVP. See `docs/concepts/architektur.md` §9 for the full MVP word set (incl. `denen` as the generalisation target).

## Two channels, kept separate

- **Width = pressure (Schwellzug):** from `skeletonize` + `distance_transform_edt`, measured on the mask, independent of darkness. Robust to fading.
- **Darkness = ink quantity:** separate grayscale channel; carries the dip-pen refill trace. For authentic rendering, not for geometry.

Binarization is the trap: too aggressive and a faded thick downstroke disappears, the skeleton breaks, and it gets misread as a hairline. Adaptive binarization + keep the intensity channel alongside.
