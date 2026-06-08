# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A companion guide `.github/copilot-instructions.md` carries the same domain
rules targeted at GitHub Copilot (and any other agent that reads that
standard path). Both files MUST stay in sync — if you change one, check
the other.

## Repository state

In-progress MVP. The monorepo layout (per `docs/concepts/naming-und-setup.md` §3):

- `/core` — Pure-Python compute + DB layer. `core/extract.py` (skeleton + distance transform), `core/template.py` (canonical sampling + outline + slant), `core/chart.py` (load + `crop_with_mask` — freeform eraser mask), `core/pipeline.py` (`canonical_from_path`, `diagnostic_for_glyph`), `core/fit.py` (M4: `fit_template_to_instance`, `fit_glyph_to_crop` — regularised template-to-skeleton fit), `core/database/` (SQLAlchemy `Style` + `Hand` + `Source` + `Bbox` + `Template` + `Instance` + `Aggregate` + repositories).
- `/api` — FastAPI service. Routers in `api/routers/`: `health`, `styles`, `hands`, `sources`, `chart`, `bboxes`, `templates`. All data lives in Postgres (DB `kurrentschrift` on the anyplot Cloud SQL instance, see `.env` — local dev writes the SAME Cloud SQL DB, there is no separate local DB).
- `/app` — React 19 + Vite + MUI SPA (anyplot-stil). Today admin-only: drag a rough bbox on the Loth chart, then a step-by-step **Einrichtungs-Wizard** (Ausschluss/freehand eraser → Lineatur → Schräge (one or more individually-placed slant lines) → Weg → Übersicht/approve→lock) authors the canonical; stylus stroke capture (Samsung S-Pen). The wizard is the single editing surface (the old standalone EditorPage was retired); a separate **Diagnose modal** (`DiagnosticDialog`, opened by the chart toolbar's "Diagnose" button) shows the 3-column SVG diagnostic (Loth crop · skeleton+anchors · canonical template) plus the M4 fit, rendered from `/diagnostic` + `/fit` JSON. UI terminology is German per DIN/Süß lineature (Grundlinie · Mittellinie · Oberlinie · Unterlinie; zones Oberlänge · Mittellänge · Unterlänge). Post-MVP it grows to host the end-user website (animation, lineature configurator, HTR upload, Lese-Lupe, style analysis, hands comparison, open-data page) — admin routes will move behind `/admin/*` with auth (Cloudflare Access or GCP IAP). See `docs/concepts/architektur.md` §16 and `docs/reference/frontend-stack.md`.
- `/alembic` — Schema migrations. `0004_library_schema.py` rebuilds the model into `styles` + `hands` + `sources` + `bboxes` + `templates` + `instances` + `aggregates` and seeds the three Grundvorlagen (Kurrent · Sütterlin · Offenbacher) + the Loth 1866 chart source under Kurrent.
- `/data` — Sources, corpora, variants, samples, derived stats (see Data & licensing below). PD source bytes (Loth chart.jpg) stay on disk; the DB only stores the relative `chart_path`.

The earlier `/mvp/` folder (CLI tools + JSON files in the repo) was retired in favour of this DB-backed architecture. The data model splits **canonical templates** from **per-text instances** (architektur.md §3): the authored Grundvorlage lives in `templates.anchors`/`half_widths`/`raw_path` (JSONB, per `(style, glyph, position, variant)`); per-occurrence fits + statistics live in `instances.measurements` (filled by the post-MVP import); per-hand aggregates in `aggregates` (§12). `n_anchors` can be changed retroactively and stats are aggregatable in SQL.

**Local dev** (three steps): `uv run alembic upgrade head` (schema), `uv run uvicorn api.main:app --reload --port 8000`, then `cd app && npm install && npm run dev` (Vite on :3000 with `/api` proxy to the API). See `.claude/commands/start.md` for the slash command. Admin **write** endpoints are gated by `require_admin`: in prod via the Cloudflare Access cookie, locally via a shared secret — set `ADMIN_TOKEN=<x>` for the API and the matching `VITE_ADMIN_TOKEN=<x>` in `app/.env` so the SPA sends `X-Admin-Token` (without it, local saves/traces return 401).

## Read these before substantive work

The design is already settled in the docs; do not re-litigate decisions that have an explicit "verworfen" (rejected) section. Start at `docs/index.md`.

- `docs/concepts/architektur.md` — architecture. §1 (problem split, indexes all sections), §2 (analysis-by-synthesis), §3 (library schema), §4 (ligature exception), §5 (Schwellzug vs ink + width-profile resolver), §6 (3-stage quality pipeline), §7 (the one real research risk), §8 (MVP — four gates), §9 (test words), §10 (build order, post-MVP phases P1–P5). Post-MVP sections: §11 (animation render path), §12 (style analysis pipeline), §13 (HTR integration), §14 (Lese-Lupe), §15 (print pipeline), §16 (frontend architecture), §17 (open-data export).
- `docs/concepts/mvp-roadmap.md` — actionable breakdown of §8 into Schritt 0 + M0–M7 milestones (M7 = abgespeckte animation, MVP gate 4)
- `docs/concepts/naming-und-setup.md` — repo/name/license/layout/frontend-stack/hosting decisions
- `docs/reference/sprachregelung.md` — language rules (see below)
- `docs/reference/quellen-und-rechte.md` + `docs/reference/datenablage.md` — data/licensing rules (see below)

**Read situatively** (only when working on the respective section):
- `docs/reference/htr-integration.md` — Transkribus API + TrOCR fallback details, PAGE-XML, free-tier logic
- `docs/reference/animation-rendering.md` — stroke-dashoffset (MVP) and Canvas-2D-stroker (post-MVP) algorithms
- `docs/reference/styleanalyse.md` — per-instance/per-hand/Hinge-feature layers, heatmap layouts
- `docs/reference/frontend-stack.md` — React+Vite+MUI build, deploy, auth, route map

## Language conventions (strict)

From `docs/reference/sprachregelung.md`:

- **Code (identifiers, docstrings, comments): English, no exceptions.** Including commit messages.
- **README + GitHub description: English** (audience includes English-speaking genealogy).
- **Internal docs under `docs/`: German.** This is deliberate — the domain is German.
- **Website v1: German.**

German technical terms without an established English translation get an English identifier and one explanatory comment, e.g. `width_profile  # Schwellzug: pressure-driven stroke-width modulation`.

Characters themselves are *data, not code* — schema keys stay English, but values are the actual glyphs: `{"glyph": "ſt", "position": "medial", "variant": 0}`.

## The core architectural commitment

**Analysis-by-synthesis with a ductus prior.** The image supplies geometry + ink width; the canonical ductus template supplies stroke order and crossing resolution. A canonical template's key is `(style, glyph, position, variant)` — `style` is the Grundvorlage/script family (Kurrent · Sütterlin · Offenbacher; `templates.style_id`), the rest is the library unit within a style, not just glyph. Allographs (e.g. medial ſ vs. final s) are *separate glyphs* with separate ductus, not one glyph with variants. Positionally-sanctioned form variants (the "A = A" on teaching charts) are separate templates, not parameter deviations. In the admin, the same authored form applies to all positions by default (fan-out write across initial/medial/final); differentiate a single position later — the positional connection strokes are *generated* from `entry`/`exit` tangents, so the base form is usually identical across positions.

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

## MVP gates

Four gates in `architektur.md` §8 — all four required for the kernel to count as validated:

1. **Stability** — ≥10 fits per core glyph cluster cleanly (`ſ`-med, `s`-final, `e`-med).
2. **Allograph separation** — cross-fit between medial ſ and final s separates per hand.
3. **Word rendering** — majority of seven MVP words reconstructed *and* `denen` rendered from aggregated per-glyph stats in the same hand.
4. **Animation (slim)** — one MVP glyph plays back with correct stroke order via `stroke-dashoffset` on the centerline (no Schwellzug yet; full Canvas-2D stroker is post-MVP §11).

If gates 1–4 hold, kernel is validated; otherwise valuable negative result in days.

## Test words

`lesen` (medial ſ, repeated e, ascender, u/n confusable final n) + `das` (final s) is the §9 Pflicht-Anker pair for the MVP. See `docs/concepts/architektur.md` §9 for the full MVP word set (incl. `denen` as the generalisation target).

## Two channels, kept separate

- **Width = pressure (Schwellzug):** from `skeletonize` + `distance_transform_edt`, measured on the mask, independent of darkness. Robust to fading.
- **Darkness = ink quantity:** separate grayscale channel; carries the dip-pen refill trace. For authentic rendering, not for geometry.

Binarization is the trap: too aggressive and a faded thick downstroke disappears, the skeleton breaks, and it gets misread as a hairline. Adaptive binarization + keep the intensity channel alongside.
