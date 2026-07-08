# Copilot Instructions

This file provides guidance to GitHub Copilot (and any other AI agent that
reads `.github/copilot-instructions.md`) when working in this repository.

A companion guide `CLAUDE.md` at the repo root contains the same domain
information targeted at Claude Code. Both files MUST stay in sync — if you
change one, check the other.

---

## Important Rules

- **Language conventions (strict)** — from
  `docs/reference/sprachregelung.md`:
  - **Code (identifiers, docstrings, comments): English, no exceptions.**
    Including commit messages and PR descriptions.
  - **README + GitHub description: English** (audience includes English-
    speaking genealogy).
  - **Internal docs under `docs/`: German.** Deliberate — the domain is
    German.
  - **Website v1: German;** English follows (Vision Leitprinzip
    „Zweisprachig").
  - German technical terms without an established English translation get
    an English identifier and one explanatory comment, e.g.
    `width_profile  # Schwellzug: pressure-driven stroke-width modulation`.
  - Characters themselves are **data, not code** — schema keys stay
    English, but values are the actual glyphs:
    `{"glyph": "ſt", "position": "medial", "variant": 0}`.
- **Do not re-litigate settled decisions.** The design docs under
  `docs/concepts/` have explicit *verworfen* (rejected) sections; do not
  propose alternatives those sections already considered and ruled out
  (OpenType fonts, blind skeleton tracing, bigram databases, SVG stroke-
  animation libraries for Schwellzug, AGPL, etc.).
- **Data is not covered by the code license.** See "Data & licensing"
  below — this is the single most error-prone area for an AI agent.

---

## Task Suitability

**Good tasks for Copilot in this repo:**

- Frontend feature work that follows the existing `/app/` patterns
  (drag-on-canvas, stylus capture, diagnostic panels).
- New FastAPI routes that mirror the `api/routers/{health,styles,hands,
  sources,chart,bboxes,templates,write}.py` shape.
- Adding numpy/scipy/scikit-image pipeline steps inside `core/`.
- Writing/improving unit tests under `tests/` (no tests exist yet — adding
  them is welcome).
- Refactors within established patterns.
- Updating documentation under `docs/` (mind the German/English split).
- Fixing ruff / TypeScript / ESLint findings.

**Tasks requiring human review:**

- Schema migrations in `alembic/versions/` (touch the Postgres source of
  truth — author them, then ask before applying).
- Changes to the ductus prior or analysis-by-synthesis core logic
  (`core/template.py`, `core/pipeline.py`) — that's the research kernel
  (§7).
- Anything touching `/data/` — licensing implications.
- Authentication and admin-route configuration.
- Pricing/quota logic for the HTR free-tier (§13).

**How to iterate:**

- Use `@copilot` in PR comments with specific, actionable feedback.
- Reference doc sections by number (e.g. „architektur.md §3") rather than
  copying prose — the docs are the source of truth.
- Link to relevant `docs/reference/*.md` files for technical specs.

---

## Project Overview

**kurrentschrift** is a modern toolkit for the German Kurrent script
(pre-1900 normed handwriting). The vision is a single web app at
[kurrentschrift.ink](https://kurrentschrift.ink) that combines:

**Writing pillar**

1. **Onboarding** — history in two sentences, alphabet table, key reading
   and writing rules.
2. **Content-aware practice sheets** — configurable lineature ratios,
   arbitrary input text, printable PDFs.
3. **Animated letter tables** — every letter played back with stroke order
   and pressure build-up (true Schwellzug).

**Reading pillar**

4. **Modern text rendered in a trained Kurrent hand** — practice reading
   without depending on a stream of historical examples.
5. **Reading help for historical texts via HTR** (Transkribus default,
   TrOCR fallback) — extended with a **reading magnifier (Lese-Lupe)**:
   click on a confusing letter, get a structured explanation referencing
   orthography rules.

**Research pillar**

6. **Style analysis** — upload a sample, get statistics (slant, swell,
   transition angles, per-glyph cluster spread), with three follow-on
   paths: optimise, new-style-as-basis, hand comparison (heatmaps).
7. **Open data** — canonical glyph data (anchors, swell profiles, ductus
   order) as a citable Zenodo release.

Bilingual DE/EN is a cross-cutting guiding principle (German first;
English follows).

The full vision is in `docs/concepts/vision.md` (seven goals, three
pillars). The settled architecture (§1–§17) is in
`docs/concepts/architektur.md`. **Read those two before substantive work.**

### The core architectural commitment

**Analysis-by-synthesis with a ductus prior.** The image supplies geometry
+ ink width; the canonical ductus template supplies stroke order and
crossing resolution. A canonical template's key is `(style, glyph,
position, variant)` — `style` is the Grundvorlage/script family (Kurrent ·
Sütterlin · Offenbacher), the rest is the library unit within a style, not
just glyph. Allographs (e.g. medial ſ vs. final s) are *separate glyphs*
with separate ductus, not one glyph with variants. Positionally-sanctioned
form variants (the "A = A" on teaching charts) are separate templates, not
parameter deviations. In the admin the authored form applies to all
positions by default (fan-out across initial/medial/final); positional
connection strokes are *generated* from `entry`/`exit` tangents.

The closed ligature set (`ch`, `ck`, `tz`, `ſt`, `qu`, `ß`) are first-
class library entries, not exit→entry chains. Enumerate, don't generate.
Arbitrary letter pairs *are* generated from `exit`/`entry` tangents +
coupling height — that's the whole point of avoiding a bigram explosion.

When in doubt about what's a glyph vs. a variant vs. a deviation, re-read
`docs/concepts/architektur.md` §3 and §4.

---

## Repository Layout

```
kurrentschrift/
├── core/             # Pure-Python compute + DB layer
│   ├── extract.py    # skeleton + distance transform; fill_small_holes (per-glyph speck fill)
│   ├── template.py   # canonical sampling + outline + slant
│   ├── chart.py      # load + crop_with_mask (eraser + patches + ink brush); crop_mask_to_png_bytes (mask preview)
│   ├── pipeline.py   # canonical_from_path, diagnostic_for_glyph, render_payload_for_template
│   ├── shaping.py    # text → glyph_keys (long-s + Fuge marker `|` for round Schluss-s in compounds, ligatures, decompose fallback; twin of app shaping.ts)
│   ├── compose.py    # word composition (placement + Übergänge; single source of truth, golden-pinned)
│   ├── widths.py     # resolve_half_widths — per-style width resolver (§5), render-time
│   ├── fit.py        # M4: fit_template_to_instance, fit_glyph_to_crop
│   └── database/     # SQLAlchemy Style + Hand + Source + Bbox + Template + Instance + Aggregate + QuizWord + repos
├── api/              # FastAPI service (thin)
│   ├── main.py
│   ├── schemas.py
│   ├── dependencies.py
│   ├── rendering.py  # style resolution + memoised source-pooled nib (templates + write)
│   └── routers/      # health, styles, hands, sources, chart, bboxes, templates,
│                     #   write (public batched render payloads + /word server-side composition,
│                     #   cached, no chart I/O), quiz_words (public GET /quiz-words reading-drill bank:
│                     #   ~500 words, ONE pinned anchor distractor each, rest drawn at runtime by the
│                     #   shared similarity rules — docs/reference/quiz-wortbank.md)
├── app/              # React 19 + Vite + MUI SPA (anyplot-style)
│   └── src/
│       ├── routes/      # paths.ts route constants + lazy public/admin route sections
│       ├── pages/       # thin default-export route mounts only
│       ├── sections/    # feature views: landing/, schriftkunde/ (/schriftkunde overview),
│       │                #   hub/ (/lesen + /schreiben area hubs), worksheet/,
│       │                #   scribe/ (/federprobe live writer), quiz/ (useQuizEngine),
│       │                #   admin/{chart,setup-wizard,diagnostics,sidebar}
│       ├── components/  # reusable UI: PaperBackground, PublicHeader (3-area nav), PublicFooter,
│       │                #   PageContainer (one column: narrow 760/text 1152/wide 1280), Prose (~66ch
│       │                #   reading measure), PageHeader (shared page-header: area eyebrow + Playfair
│       │                #   title + intro; every public page bar the landing hero), WrittenGlyph (one glyph), WrittenWord (word/line +
│       │                #   Übergänge as written), CategoryHeading (section title), BootStatus
│       ├── layouts/     # admin shell (AdminLayout + AdminModals)
│       ├── theme/       # MUI theme split; colors sourced from styles/paper.ts (single source)
│       ├── lib/api/     # fetch client (cold-start retry, typed ApiError), endpoints,
│       │                #   wire types hand-synced with api/schemas.py, renderCache.ts
│       │                #   (shared render-data cache, batches /write/glyphs per word)
│       ├── domain/      # glyphs.ts (registry + lock/split); shaping.ts (text → glyph_keys —
│       │                #   quiz word-bank gating only; word composition moved server-side
│       │                #   to core/shaping.py + core/compose.py, compose.ts is gone)
│       ├── context/     # AdminContext (admin boot data + selection state)
│       ├── locales/     # de/ namespaces — ALL German UI strings (pre-i18n layer)
│       └── hooks/, styles/, global-config.ts
├── alembic/          # Postgres migrations
│   └── versions/     # 0004 library schema + seeds … 0006 Sütterlin 1922 source
├── data/             # Sources, samples, derived — SEPARATE LICENSING
│   ├── sources/      # public-domain originals (Loth 1866, Sütterlin 1922 incl. connected-writing
│   │                 #   plates + words.json word rects for the word bench, Koch 1928 reserve, …)
│   ├── samples/      # own-hand scans
│   └── derived/      # mixed licensing — see datenablage.md
├── docs/             # German concept + reference docs
│   ├── concepts/     # vision, architektur (§1–§17), mvp-roadmap, naming
│   ├── reference/    # language rules, licensing, HTR, animation, …
│   └── proposals/    # staged not-yet-approved changes
├── .github/          # this file + workflows
├── CLAUDE.md         # sibling guide for Claude Code
└── README.md         # public pitch (English)
```

`/app/` serves the public pages (`/` landing, `/schriftkunde` a compact
source-cited overview of the three Ausgangsschriften (Grundbegriffe · the three
scripts with one specimen each · Federn · Tinte · Buchstaben/Zahlen · chronology;
section titles share the viridian-Kurrent-initial `CategoryHeading` with
`/impressum`, `/tafel` and `/landing`; the copyrighted Süß textbook is named + linked to its DNB record,
never reproduced); the tools group under two hubs so the top nav stays at three
areas (Schriftkunde · Lesen · Schreiben): `/lesen` (→ `/quiz` letter quiz +
`/tafel` Schreibtafel) and `/schreiben` (→ `/schreiben/uebungsblatt` worksheet
generator + `/federprobe` live word/sentence writing, synthesised Sütterlin
ductus with generated Übergänge) — paper-&-ink identity
per `docs/concepts/style-guide.md` + `docs/concepts/design-system.md`) and the admin behind `/admin/*`
(Cloudflare Access in prod). **Post-MVP** the public side grows
(`/animation`, `/lese-hilfe`, `/lese-lupe/:job`, `/stil-analyse`,
`/vergleich`, `/open-data`). See `docs/reference/frontend-stack.md`.

---

## Development Setup

Three steps (see `.claude/commands/start.md` for the slash command):

```bash
# Schema (run once or after migrations)
uv run alembic upgrade head

# Backend on :8000
uv run uvicorn api.main:app --reload --port 8000

# Frontend on :3000 with /api proxy to :8000
cd app && npm install && npm run dev
```

Python package manager: **uv**. Frontend: **npm** (note: anyplot uses
yarn, kurrentschrift uses npm — `package-lock.json` is checked in).

Browser at `http://localhost:3000` loads the admin UI: the active source
chart (switchable at runtime via the sidebar's Vorlage select, persisted per
browser; `CONFIG.sourceId` in `app/src/global-config.ts` is the source the
PUBLIC pages render — currently the Sütterlin 1922 Ausgangsschrift — and the
admin's default) with a draggable rough bbox, then the step-by-step Einrichtungs-Wizard (Ausschluss —
freehand eraser + manual ink brush + per-glyph speck auto-fill + inserted donor cell (Zelle einsetzen —
copy ink from another chart cell into the crop, stored as `bboxes.patches`, so ü/ö are authored from a
u/o base plus the ä umlaut), with a binarised "Maske zeigen" preview
→ Lineatur → Schräglage → Weg → Übersicht/approve→lock) for
canonical extraction, and the 3-column SVG diagnostic from `/diagnostic`
JSON. The Weg step records the ductus as one or more pen-strokes — each pen
lift (Absetzen, e.g. a u's two downstrokes) starts a new stroke rather than
bridging it; the flat `raw_path` carries sparse `pen_up` markers and the
canonical stores `stroke_starts` in `trace_meta`, so the diagnostic outline
and the M4 fit keep the strokes separate. A Zeichnen/Anpassen toggle lets the
drawn line be warp-dragged (a falloff-radius nudge) to smooth a wobble in the
draft before saving. UI labels are German per DIN/Süß
lineature (Grundlinie · Mittellinie · Oberlinie · Unterlinie; zones Oberlänge
· Mittellänge · Unterlänge).

---

## Code Standards

### Python Style

- **Linter/Formatter**: Ruff (when configured — `pyproject.toml`).
- **Type hints**: required for all functions.
- **Docstrings**: explanatory line for non-obvious functions; identifiers
  carry most of the meaning.
- **Import order**: standard library → third-party → local.
- **No comments narrating WHAT**; well-named identifiers do that. Comments
  explain WHY when it's non-obvious (invariant, workaround, surprising
  behavior).

### TypeScript / React Style

- React 19 functional components with hooks.
- MUI 9 + Emotion for styling.
- Types over interfaces by default.
- `app/src/constants.ts` is the canonical place for shared constants
  (Position type, KNOWN_GLYPHS list).
- Do not introduce a state-management framework (Redux/Zustand) — Context
  + local state are sufficient for our use cases.

### Database Schema (Postgres + SQLAlchemy async)

- Tables: `styles`, `hands`, `sources`, `bboxes`, `templates`,
  `instances`, `aggregates`.
- `styles` is the Grundvorlage/script family (Kurrent · Sütterlin ·
  Offenbacher); it carries `width_resolver` (§5) + lineature defaults.
  The resolver is applied at render time by
  `core/widths.py::resolve_half_widths` (`pressure` = measured Schwellzug,
  `constant` = Sütterlin Gleichzug, `broad_nib` = post-MVP stub); stored
  `half_widths` always stay the measurement.
- `templates` are the canonical Grundvorlagen, unique on
  `(style_id, glyph, position, variant)` — the identifying tuple, **not**
  `glyph_key` (UI-only). `instances` hold per-text occurrences (the fit +
  `measurements`, §12 layer 1, filled by the post-MVP import); `aggregates`
  are per-hand stats (§12 layer 2).
- `position` is the **chart role** (where Loth teaches it), not the
  text-position — see `app/src/constants.ts` comments and architektur.md
  §3. The admin authors one form for all positions by default (fan-out).
- `bboxes` carries the chart crop + freeform eraser `mask_strokes` (replaces
  the old rectangle `excludes`) + baseline/midband calibration + `guides` +
  `locked`. JSONB columns hold structured data; aggregate stats in SQL.

### Testing Standards

- No tests exist yet. **Adding them is welcome.**
- When you do add tests, mirror the source structure
  (`tests/unit/core/test_template.py` for `core/template.py`, etc.).
- Use pytest fixtures; SQLite-in-memory for integration tests if/when
  needed.

---

## Architecture Highlights

The architecture is documented in `docs/concepts/architektur.md` (§1–§17,
about 17 sections after the May 2026 holistic restructure). Quick index:

| Section | Topic |
|---|---|
| §1 | Five-pillar problem split (Synthesis / Recognition / Analysis / Content / Data Export) — also the index to all following sections |
| §2 | Analysis-by-synthesis with ductus prior (rejected alternatives noted) |
| §3 | Library schema `(glyph, position, variant)` |
| §4 | Transitions are consequences (closed ligature set is the exception) |
| §5 | Width = pressure (Schwellzug) vs. darkness = ink; width-profile resolver per source (Kurrent / Sütterlin) |
| §6 | Three-stage quality pipeline (statistics → closed-loop → curation) |
| §7 | The one real research risk (template tightness) |
| §8 | MVP — six-letter alphabet + ſ/s split, four validation gates |
| §9 | Test words (`lesen` + `das` = Pflicht-Anker pair) |
| §10 | Post-MVP roadmap as five phases (Reading → Lineature → Style → Compare → Open Data) |
| §11 | Animation render path (Canvas-2D stroker with offset curves) |
| §12 | Style analysis pipeline (per-instance / per-hand / Hinge features) |
| §13 | HTR integration (Transkribus default with free-tier, TrOCR fallback) |
| §14 | Reading magnifier (own glyph recognition as didactic layer) |
| §15 | Print pipeline (WeasyPrint, configurable lineature) |
| §16 | Frontend architecture (anyplot-style React+Vite+MUI SPA) |
| §17 | Open-data export (Zenodo + DOI, CC-BY 4.0) |

Technical specs sit in `docs/reference/*.md`:

- `htr-integration.md` — Transkribus API, TrOCR fallback, PAGE-XML
- `animation-rendering.md` — stroke-dashoffset (MVP) + Canvas-2D (post-MVP)
- `styleanalyse.md` — Hinge features, heatmap layouts
- `qualitaetsmetrik.md` — score/bench_loss definition, frozen-reference
  rule, baseline history, experiment learnings incl. verworfen items.
  TWO metrics, one per script: §1–§4 Kurrent/Schwellzug
  (`core/quality.py`, pixel/width), §5 Sütterlin/Gleichzug naturalness
  (`core/quality_suetterlin.py` + `core/geometry.py`). Bench runs one
  script per run (`--style suetterlin|kurrent`), no combined bench_loss.
- `frontend-stack.md` — build, deploy, auth, routes

The binding public-UI build spec is `docs/concepts/design-system.md` (colour
tokens, 19px type ladder + Playfair-600 heading rule, PageContainer widths
760/1152/1280 + Prose ~66ch measure, surface rule = identity-paper /
work-surfaces-white, IA = three areas + hubs, component inventory). Read it
before any public-page styling; it pairs with `concepts/style-guide.md`
(rationale/history).

Source-backed script facts (lineature terms, Schräglage convention
90° = upright, nib types, per-script data — incl. the measured ~50°
slant of the Loth 1866 chart vs. 60–70° for Kurrent um 1900) live in
`docs/schriftkunde/`.

---

## Test Words

`lesen` (medial ſ, repeated `e`, ascender, u/n confusable final `n`) +
`das` (final `s`) is the Pflicht-Anker pair for the MVP. The full MVP
word set:

```
lesen · das · den · lese · lasen · als · dann
```

Generalisation target (not written, rendered from aggregated stats):
`denen`. See `docs/concepts/architektur.md` §9.

---

## Two Channels, Kept Separate

- **Width = pressure (Schwellzug):** from `skeletonize` +
  `distance_transform_edt`, measured on the mask, independent of darkness.
  Robust to fading.
- **Darkness = ink quantity:** separate grayscale channel; carries the
  dip-pen refill trace. For authentic rendering, not for geometry.

Binarisation is the trap: too aggressive and a faded thick downstroke
disappears, the skeleton breaks, and it gets misread as a hairline.
Adaptive binarisation + keep the intensity channel alongside.

---

## Data & Licensing (this repo is unusual here)

Code is **MIT**. **Data is not covered by the code license** — each
source carries its own. The `/data` tree lives outside `/core`, `/api`,
`/app` precisely to keep this boundary visible.

Three commit classes, kept strictly separate (see
`docs/reference/datenablage.md` §1):

1. **Committable:** `/data/sources/` (public-domain only, e.g. Loth 1866
   SVG) and `/data/samples/own-hand/` (author's own copyright). Each gets
   a `SOURCE.md` with permalink, license, attribution, retrieval date.
2. **Gitignored:** `/data/corpora/` — only `SOURCE.md` + `fetch_corpus.py`
   are committed, never the data files. Pin DOI versions.
3. **Mixed:** `/data/derived/from-cc-by/` is committable;
   `/data/derived/from-nc-sa/` is gitignored (NC-SA collides with MIT).

Hard rules:

- **Süß' Lehrbuch and similar copyrighted works never enter the repo** —
  not as scans, not as redrawn glyphs, not as derived images. Bibliographic
  reference in prose is fine.
- A scan is not automatically free under German law (§72 UrhG). Prefer in
  order: own hand → explicit PD/CC0 → own photo of a PD original.
- "Script-downloaded" ≠ "license-free." The license of the bytes follows
  the bytes, not the fetch mechanism.
- Variant 0 (`v0-loth-1866`) is the canonical geometry baseline for first
  tests. The ductus prior is *the author's own contribution layered over*
  this PD geometry — Loth supplies shapes, not stroke order.

Before any data commit: *is this my expression or the expression of a
protected source?* If unclear, link to the original rather than committing
it.

---

## Tech Stack (today + planned)

- **Backend:** Python 3.13+, FastAPI, SQLAlchemy async, asyncpg, Postgres,
  uv (package manager).
- **Pipeline:** numpy, scipy, scikit-image, Pillow.
- **Frontend:** React 19, TypeScript 6, Vite 8 (with SWC plugin), MUI 9,
  React Router 7, npm.
- **Planned additions (post-MVP):** `react-helmet-async` (SEO),
  `react-i18next` (DE/EN), WeasyPrint (PDF), httpx (Transkribus client),
  optionally TrOCR via HuggingFace Transformers for self-hosted HTR.
- **Linting (when configured):** ruff (Python), ESLint (TypeScript).

---

## Deployment (post-MVP target)

The project will run on **Google Cloud Platform** (eigenes GCP-Projekt,
same pattern as anyplot.ai):

| Service | Component | Purpose |
|---|---|---|
| Cloud Run | `kurrentschrift` | FastAPI + Vite-build in one container |
| Cloud SQL | PostgreSQL | `kurrentschrift` DB (currently on anyplot's Cloud SQL instance) |
| Cloud Build | Triggers | Auto-deploy on push to main (Dockerfile + cloudbuild.yaml are placeholders today) |
| Cloudflare Access *or* GCP IAP | edge | Admin-route auth (Google identity) |

Today the `Dockerfile` and `cloudbuild.yaml` placeholders are unactivated;
deployment is local-only (`npm run dev` + `uvicorn --reload`).

---

## GitHub Workflow

No automated AI workflows are configured yet (in contrast to
anyplot which has spec-create / impl-generate / impl-review / impl-merge
pipelines for plot specifications). For now:

- **Issues** are welcome for design discussion (pre-MVP this is the main
  contribution channel — see `docs/contributing.md`).
- **PRs** should reference the relevant `docs/concepts/architektur.md`
  section and any `docs/reference/*.md` they touch.
- **Branch policy:** main is protected; feature branches with PRs.
- **Commit messages:** English, focused on WHY, conventional-commit prefix
  optional (`docs:`, `feat:`, `fix:`, `refactor:`).
- **Pre-commit hooks:** none configured yet — when added, do not bypass
  with `--no-verify`.
- **Verification before a PR:** run the local CI equivalents first —
  `uv run --extra test pytest`, `uv run --extra dev ruff check .`,
  `uv run --extra dev ruff format --check .`, plus `npm run build` in
  `app/` when the frontend changed. The pipeline should never fail on
  tests or lint. (Claude Code sessions encode these loops as skills
  under `.claude/skills/` — verify-frontend / verify-api / verify-core,
  write-docs, audit-licenses, open-pr, optimize-glyphs.)
- **Glyph-pipeline changes are benchmarked:** `tools/glyphbench` scores
  every authored glyph against frozen references, ONE script per run
  (`uv run python -m tools.glyphbench.run --style suetterlin|kurrent`,
  headline `bench_loss:` — lower is better; Sütterlin also prints
  `comp_<name>:` per-category means, `--compare prev.json` diffs them).
  A PR touching `core/` extraction or rendering should quote before/after
  numbers; the bench never touches the DB (fixtures exported once,
  read-only). One level up, `tools/wordbench` scores COMPOSED words
  (placement + Übergänge from core/shaping.py + core/compose.py) against
  frozen same-hand word specimens the same way — the Abb. 19 words AND,
  as a separate set with its own `pair_loss` headline, the Abb. 20
  letter-pair joins
  (`uv run python -m tools.wordbench.run --style suetterlin [--set
  words|pairs|all]`; unauthored templates are frozen `scorable: false`
  and skipped+reported, never averaged in; see
  docs/reference/qualitaetsmetrik.md §6) — a PR touching core/compose.py
  should quote its before/after `bench_loss:` (and `pair_loss:`) too.
- **Glyph inspection (see, don't just score):** `tools/glyphlab` renders
  matplotlib overlays of a glyph's derivation (crop · skeleton ·
  centerline · corners · silhouette) to `temp/`, from a fixture or a
  read-only live DB pull — `python -m tools.glyphlab <key> [--live]
  [--stages]` (matplotlib is the dev-only `viz` extra), annotating each
  panel with its per-category penalty. For Sütterlin the bench scores
  ductus naturalness directly (so `bench_loss` moves on centerline/corner
  shifts); the overlay says *why* a glyph lost points, the number *how much*.
  Its word-level sibling `tools/wordlab` draws a COMPOSED word over its
  wordbench specimen with per-connector penalty callouts
  (`compose_word(..., provenance=True)` + `score_word_segments` attribute a
  deviation to a letter or a specific join) — `python -m tools.wordlab <id>
  [--set pairs] [--live] [--sweep core.compose.CONST=v1,v2]`. The provenance
  flag is diagnostics-only and default OFF: the `/write/word` payload and the
  compose golden fixture stay byte-identical.
- **Never merge a PR yourself** — open it, get it green and
  review-clean (address Copilot review comments, then resolve the
  threads); merging is the maintainer's call.

---

## Acceptance Criteria

Before completing any task:

1. Code conforms to the language conventions above (English identifiers
   and comments, no exceptions).
2. Type hints / TS types are included for all new functions and
   components.
3. New decisions that contradict an existing doc are documented either as
   a `docs/proposals/` entry or via an explicit `docs/concepts/` update —
   **don't silently diverge** from settled docs.
4. Data changes follow the three-commit-classes rule. No copyrighted
   source bytes enter the repo.
5. If you add/change a public API route, update `api/schemas.py` and any
   `docs/reference/*.md` that describes it.
6. If you change frontend routing or the auth shape, update
   `docs/reference/frontend-stack.md`.

---

## Getting Help

- **Documentation:** start at `docs/index.md`.
- **Code patterns:** the existing `/app/src/components/wizard/SetupWizard.tsx`
  shows the canonical pattern for an interactive stylus/guide tool;
  `core/pipeline.py` shows the pipeline composition pattern.
- **Sibling AI guide:** `CLAUDE.md` (this file's twin for Claude Code).
- **Vision-to-architecture mapping:** `docs/concepts/architektur.md` §1
  is the index — every Vision pillar points to a specific architecture
  section.
