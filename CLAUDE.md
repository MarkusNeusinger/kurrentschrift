# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A companion guide `.github/copilot-instructions.md` carries the same domain
rules targeted at GitHub Copilot (and any other agent that reads that
standard path). Both files MUST stay in sync — if you change one, check
the other.

## Repository state

In-progress MVP. The monorepo layout (per `docs/concepts/naming-und-setup.md` §3):

- `/core` — Pure-Python compute + DB layer. `core/extract.py` (skeleton + distance transform; `fill_small_holes` — per-glyph speck auto-fill folded into `binarize_adaptive`), `core/template.py` (canonical sampling + outline + slant), `core/chart.py` (load + `crop_with_mask` — freeform eraser, inserted donor cells (`patches`) **and** ink-brush applied before binarisation; `crop_mask_to_png_bytes` — the binarised mask preview, auto-fill colour-coded), `core/pipeline.py` (`canonical_from_path`, `diagnostic_for_glyph`), `core/widths.py` (`resolve_half_widths` — the per-style width resolver from architektur.md §5, applied at render time: `pressure` keeps the measured Schwellzug, `constant` renders Sütterlin Gleichzug, `broad_nib` is a post-MVP stub; stored `half_widths` always stay the measurement), `core/fit.py` (M4: `fit_template_to_instance`, `fit_glyph_to_crop` — regularised template-to-skeleton fit), `core/database/` (SQLAlchemy `Style` + `Hand` + `Source` + `Bbox` + `Template` + `Instance` + `Aggregate` + repositories).
- `/api` — FastAPI service. Routers in `api/routers/`: `health`, `styles`, `hands`, `sources`, `chart`, `bboxes`, `templates`, `write` (public read: per-glyph render payloads for the writer, batched under `/sources/{id}/write/glyphs`, no chart I/O, Cache-Control + gzip; the admin keeps the uncached `/diagnostic`). Style resolution + the memoised source-pooled nib live in `api/rendering.py`. All data lives in Postgres (DB `kurrentschrift` on the anyplot Cloud SQL instance, see `.env` — local dev writes the SAME Cloud SQL DB, there is no separate local DB).
- `/app` — React 19 + Vite + MUI SPA (anyplot-stil). Public pages (paper-&-ink identity per `docs/concepts/style-guide.md`): `/` landing (the hero writes a word live with the word renderer, the font specimen as graceful fallback), `/schriftkunde` a compact, fully-sourced overview (the renamed former `/lehrbuch`) of the German cursive scripts — Grundbegriffe, the three Ausgangsschriften (Kurrent · Sütterlin · Offenbacher) with one specimen each (Kurrent in the show-script font, Sütterlin written live by the engine, Offenbacher names its PD source), the three Federn, Tinte & Papier, Buchstaben-Besonderheiten, Zahlen & Zeichen and a chronology; section titles use the shared `CategoryHeading` (viridian Kurrent initial on a hairline, also on `/impressum`), and the copyrighted Süß textbook is named + linked to its neutral DNB record, never reproduced; the public tools sit under two hub pages so the top nav stays at **three areas** (Schriftkunde · Lesen · Schreiben): `/lesen` (→ `/quiz` letter quiz + `/tafel` Schreibtafel) and `/schreiben` (→ `/schreiben/uebungsblatt` worksheet generator + `/federprobe` live word/sentence writing — type any text → the synthesised Sütterlin ductus writes it with generated Übergänge); the admin lives behind `/admin/*` (Cloudflare Access in prod): the active source chart with bbox editing (switchable at runtime via the sidebar's Vorlage select, persisted per browser in localStorage; `CONFIG.sourceId` in `app/src/global-config.ts` is the source the PUBLIC pages render — currently the Sütterlin 1922 Ausgangsschrift — and the admin's default), the step-by-step **Einrichtungs-Wizard** (Ausschluss — freehand eraser (Radierer) **plus** a manual ink brush (Tinte), a per-glyph speck auto-fill (Lücken füllen) and an inserted donor cell (Zelle einsetzen — copy ink from another chart cell into this crop via a `DonorPicker`, so a glyph with no own cell like ü/ö is authored from a u/o base plus the ä umlaut → stored as `bboxes.patches`), with a binarised "Maske zeigen" preview that colour-codes what the auto-fill swallowed → Lineatur → Schräglage (one or more individually-placed slant lines) → Weg → Übersicht/approve→lock) as the single editing surface, stylus stroke capture (Samsung S-Pen). The **Weg** step records the ductus as one or more pen-strokes — each pen lift (Absetzen, e.g. between a u's two downstrokes) starts a new stroke instead of bridging it with a line; a Zeichnen/Anpassen toggle lets the drawn line be warp-dragged (a falloff-radius nudge) to iron out a wobble in the draft before saving. A separate **Diagnose modal** (`DiagnosticDialog`) shows the 3-column SVG diagnostic (chart crop · skeleton+anchors · canonical template) plus the M4 fit, rendered from `/diagnostic` + `/fit` JSON. UI terminology is German per DIN/Süß lineature (Grundlinie · Mittellinie · Oberlinie · Unterlinie; zones Oberlänge · Mittellänge · Unterlänge). `app/src` layout: `routes/` (paths.ts route constants + lazy public/admin sections), `theme/` (MUI theme split, tokens from `styles/paper.ts` — the single palette source), `lib/api/` (fetch client with cold-start retry + typed `ApiError`, endpoints, wire types hand-synced with `api/schemas.py`, and `renderCache.ts` — the ONE shared render-data cache all "as written" surfaces fetch through, batching per word/Tafel via `/write/glyphs`), `domain/` (`glyphs.ts` alphabet/glyph-key registry + lock/split helpers; `shaping.ts` text → ordered glyph_keys with positions, long-s rule + closed ligature set; `compose.ts` lays glyphs on one baseline + generates the connecting strokes, and defers each glyph's diacritic strokes — the marks that float above the midband: i-/j-dot, the Sütterlin u-bow, the ä/ö/ü umlaut — to the end of the word (the join to the next letter leaves from the body's exit, never the floating mark) — all framework-free), `context/AdminContext.tsx`, `locales/de/` (all German UI strings as pre-i18n namespaces; react-i18next comes post-MVP), `components/` (reusable: PaperBackground, PublicHeader (3-area nav), PublicFooter, **PageContainer** — one shared content column with three calibrated widths (narrow 760 · text 1152 · wide 1280, replaces the per-section MUI `<Container>`), **Prose** — the ~66-character reading measure for running text, **PageHeader** — the one shared page-header (area eyebrow on a hairline + Playfair title + intro; every public page bar the landing hero, so title font/eyebrow/left-edge never drift), CategoryHeading — shared *section* title (viridian Kurrent initial, /schriftkunde + /impressum + /tafel + /landing), WrittenGlyph — one glyph "as written"; WrittenWord — a whole word/line composed from per-glyph diagnostics + Übergänge, revealed in writing order; BootStatus), `layouts/admin/`, `hooks/`, `sections/` (feature views: `landing/`, `schriftkunde/` (the `/schriftkunde` overview), `hub/` (the `/lesen` + `/schreiben` area hubs), `worksheet/`, `scribe/` (the `/federprobe` live writer), `quiz/` incl. `useQuizEngine`, `admin/{chart,setup-wizard,diagnostics,sidebar}` incl. `useChartViewport`/`useBboxEditing`/`useWizard`/`useCropView`), and thin `pages/` mounts. Post-MVP the public side grows (animation, HTR upload, Lese-Lupe, style analysis, hands comparison, open-data page). See `docs/concepts/architektur.md` §16 and `docs/reference/frontend-stack.md`.
- `/alembic` — Schema migrations. `0004_library_schema.py` rebuilds the model into `styles` + `hands` + `sources` + `bboxes` + `templates` + `instances` + `aggregates` and seeds the three Grundvorlagen (Kurrent · Sütterlin · Offenbacher) + the Loth 1866 chart source under Kurrent. `0006_suetterlin_source.py` seeds the Sütterlin 1922 Ausgangsschrift chart source and fixes the Sütterlin style ratio to 1:1:1. `0007_bbox_ink_and_fill.py` adds `bboxes.ink_strokes` (the manual ink brush, eraser's positive twin) + `bboxes.fill_holes_max_area` (per-glyph speck auto-fill threshold, 0 = off) — both additive, default off. `0009_bbox_patches.py` adds `bboxes.patches` (donor regions copied from elsewhere on the same chart, composited into the crop by darken before binarisation — for glyphs with no own cell, e.g. Sütterlin ü/ö borrowing the ä umlaut over a u/o base; additive, default off).
- `/data` — Sources, corpora, variants, samples, derived stats (see Data & licensing below). PD source bytes (chart.jpg per source, e.g. Loth 1866, Sütterlin 1922, plus reserve plates such as the Offenbacher Koch-1928 German alphabet under `data/sources/koch-1928/`) stay on disk; the DB only stores the relative `chart_path`.

The earlier `/mvp/` folder (CLI tools + JSON files in the repo) was retired in favour of this DB-backed architecture. The data model splits **canonical templates** from **per-text instances** (architektur.md §3): the authored Grundvorlage lives in `templates.anchors`/`half_widths`/`raw_path` (JSONB, per `(style, glyph, position, variant)`; a multi-stroke ductus is a flat `raw_path` with sparse `pen_up` markers + `stroke_starts` in `trace_meta`, so the canonical, the diagnostic outline and the M4 fit treat each pen-stroke separately and never bridge a lift); per-occurrence fits + statistics live in `instances.measurements` (filled by the post-MVP import); per-hand aggregates in `aggregates` (§12). `n_anchors` can be changed retroactively and stats are aggregatable in SQL.

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
- `docs/reference/qualitaetsmetrik.md` — score/bench_loss definition, frozen-reference rule, baseline history, experiment learnings incl. verworfen items (read BEFORE any /optimize-glyphs run or metric question). **Two metrics, one per script** (different writing instruments): §1–§4 = Kurrent/Schwellzug (`core/quality.py`, pixel/width); §5 = Sütterlin/Gleichzug naturalness (`core/quality_suetterlin.py` on `core/geometry.py` — smoothness/verticality/corner/collinearity/retrace, gated by a tolerant coverage). The bench runs ONE script per run (`--style suetterlin` default · `--style kurrent`), no combined `bench_loss`.
- `docs/reference/frontend-stack.md` — React+Vite+MUI build, deploy, auth, route map
- `docs/concepts/design-system.md` — the binding build spec for the public UI: colour tokens, the 19px type ladder (variants + Playfair-600 heading rule), the PageContainer width system (760/1152/1280) + Prose ~66-char reading measure, the surface rule (identity = paper, work surfaces white), navigation/IA (three areas + hubs), component inventory. Read before any public-page styling; pairs with `style-guide.md` (rationale/history).
- `docs/schriftkunde/` — source-backed script facts (lineature, Schräglage convention 90°=upright, nib types, per-script data incl. the measured Loth-1866 slant ~50° vs. 60–70° for Kurrent um 1900)

## Self-verification (feedback loops)

Every layer has a verified feedback-loop skill under `.claude/skills/` — use them instead of ad-hoc checking, picked by what the diff touches:

- `/verify-frontend` — drive the UI via the chrome-devtools MCP: console + network clean, style fidelity & legibility judged at 1440×900 **and** 390×844, perf trace on demand.
- `/verify-api` — curl sweep of the read endpoints against the live (shared!) Cloud SQL DB plus the admin-gate 401 probe; routine verification never sends authorized writes.
- `/verify-core` — `uv run --extra test pytest`, ruff via `--extra dev`, direct-invocation smoke of the pipeline on a synthetic chart (no DB/HTTP).
- `/write-docs` — docs conventions (German, index upkeep, CLAUDE.md ↔ copilot-instructions sync).
- `/audit-licenses` — license/provenance battery before any `/data` commit and before going public.
- `/open-pr` — diff → PR. The local gates are a hard precondition (the pipeline must never fail on pytest/ruff); after opening, watch CI **and** the Copilot review, fix sensible findings and resolve the threads. **Never merge unless explicitly asked.**
- `/optimize-glyphs` — autonomous keep/discard experiment loop on the glyph pipeline: hypothesize → edit `core/` → run the hermetic glyph bench (`tools/glyphbench`, one script per run, frozen scoring references) → results.tsv → keep or revert. Never touches the DB; the bench/metric/tests (incl. `core/quality_suetterlin.py` + `core/geometry.py`) are frozen during a run.
- `/optimize-skills` — periodic retro: mine past session transcripts for recurring friction and fold the patterns back into skills/memory/this file.

`tools/glyphlab` (a dev tool, not a skill) renders matplotlib overlays of a glyph's derivation — crop · skeleton · centerline · corners · filled silhouette — from a fixture or a **read-only** live DB pull: `python -m tools.glyphlab <key> [--live] [--stages] [--style dots]` (output to `temp/`; matplotlib is the dev-only `viz` extra, run with `uv run --extra viz`). Use it to *see* ductus quality during `/optimize-glyphs`. For Sütterlin the bench now scores ductus naturalness directly (so `bench_loss` does move on centerline/corner shifts), and glyphlab annotates each panel with its per-category penalty (where the points went) — the number says how much, the overlay says why. Prefer it over hand-rolled plotting scripts.

Routing is mandatory, not advisory: any "commit/push/PR this" request goes through `/open-pr`; never hand-roll the type-check/build/push/PR/Copilot loop, and check Copilot comments as part of the loop instead of waiting to be asked.

Known gaps without a loop yet: Alembic/schema changes (shared DB, no scratch instance), admin write flows (they would mutate shared data), post-deploy prod smoke.

## Working guardrails (from session retros)

- **Never commit on `main`** — branch first, even for a quick "commit and push" outside `/open-pr`.
- **Prod-touching actions need explicit in-session confirmation first** (Cloud SQL DDL/queries, Secret Manager access, Cloudflare Access policies): name the exact action, resource, and any email/secret id, and ask before acting.
- **Never echo secret values into the transcript** — verify by exit code or metadata.
- **Modify repo files only with the Edit/Write tools, never via Bash heredocs/sed.** When a Bash command legitimately mutates a tracked file (formatter, codegen, `git checkout`), Read the file again before the next Edit on it — stale-state errors cascade otherwise.

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
