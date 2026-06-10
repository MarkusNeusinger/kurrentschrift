# kurrentschrift

**→ [kurrentschrift.ink](https://kurrentschrift.ink)**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-in--progress%20MVP-orange.svg)](docs/concepts/architektur.md)

> Reading and re-inking historical German Kurrent script via ductus-model template fitting on scans.

---

## What this is

Two problems live under "historical German handwriting":

1. **Read it.** Already solved. [Transkribus](https://transkribus.org/) ships public Kurrent models at ~5–7% CER; a custom model needs ~50 transcribed pages. Integration work, not research.
2. **Write it — so the output looks like ink, not a font.** No off-the-shelf product exists. This is where the project sits.

The hard part of (2) is the **crossing problem**: from a still image of cursive script, the skeleton alone can't tell which stroke passed under which at a loop crossing. Blind skeleton tracing fails. OpenType fonts with contextual alternates fake connections and never look inked. ML synthesis (e.g. Cursive Transformer, 2025) needs *online* stroke data — pen path over time — but historical material is offline, image only.

## The approach: analysis-by-synthesis with a ductus prior

The image supplies geometry + ink width. The **ductus** — stroke order and pen-lift points — is known *a priori* for normed pre-1900 Kurrent and supplies the missing dimension. A canonical ductus template is fitted to the scan's skeleton and distance-transform profile.

The library unit is `(glyph, position, variant)`, not just glyph:

- **Position** (allograph): initial / medial / final. Medial `ſ` and final `s` are *different glyphs* with different ductus — not one `s` with a context switch.
- **Variant**: sanctioned form-of-the-norm choices (the "A = A" on teaching charts). Distinct topology, not deviation.
- **Per-instance deviation**: how a single fit departs from the canonical.

Transitions between glyphs aren't data — they fall out of `exit`/`entry` tangents + coupling height, so there's no bigram explosion. The closed set of taught ligature units (`ch`, `ck`, `tz`, `ſt`, `qu`, `ß`) is the exception: those are first-class library entries.

Two channels stay separate. **Width** (pressure / Schwellzug) is measured on the binarized mask via skeleton + distance transform — independent of darkness, robust to fading. **Darkness** is the ink-quantity trace from the dip pen refill cycle. Different signals, different purposes.

## The honest open question

How tight to make the template:

- Too rigid → won't fit real historical hands (every scribe breaks the norm).
- Too loose → crossing resolution becomes ambiguous again — the very problem the prior was supposed to solve.

This trade-off has to be found empirically. It's the project's research kernel; the MVP below is designed to find or falsify it cheaply.

## Status

In-progress MVP. Design docs are settled; the public site at [kurrentschrift.ink](https://kurrentschrift.ink) (worksheet generator + letter quiz) is live; the admin setup wizard, canonical extraction and the template-to-instance fit routine are implemented; own-hand scans, per-instance fit validation and aggregation are the next milestones.

**Next: the [§8 MVP](docs/concepts/architektur.md#8-der-mvp-kleinster-lauffähiger-renderkern).** A six-letter lowercase Kurrent alphabet (`a · d · e · l · n · ſ · s` — seven glyphs, since medial `ſ` and final `s` are separate allographs of one letter) plus seven short words covering all three positions (initial/medial/final). Scan the author's own hand, fit the canonical ductus templates per glyph, aggregate the per-glyph cluster stats, then re-render both the seven input words *and at least one new word* (e.g. `denen`) in the same hand. One to two weekends, not a quarter. If the **four** validation gates (stability, allograph separation, word rendering, slim animation playback) hold → kernel validated, rest is engineering. If not → valuable negative result in days.

Mandatory anchor pair (Pflicht-Anker): `lesen` (medial ſ, repeated `e`, ascender, u/n-confusable final `n`) + `das` (final `s`). See [`docs/concepts/mvp-roadmap.md`](docs/concepts/mvp-roadmap.md) for the actionable breakdown.

## What sits around the engine

The render kernel is the hard part. Around it, [`kurrentschrift.ink`](https://kurrentschrift.ink) wraps seven end-user goals clustered into Writing / Reading / Research (see [`docs/concepts/vision.md`](docs/concepts/vision.md)):

**Writing**

1. Onboarding (history, alphabet table, reading rules).
2. Practice sheets with configurable ruling (Lineatur) and content-aware text.
3. Animated letter table (stroke order + Schwellzug build-up, live).

**Reading**

4. Render arbitrary modern text in a trained Kurrent hand.
5. Reading help for historical letters via HTR (Transkribus + free-tier) — including a reading magnifier that explains confusing letters with structured rules.

**Research**

6. Style analysis of your own hand (glyph spread, slant, swell, transition angles) — with optimise / new-style-as-basis / hand-comparison paths.
7. Open-data release of the canonical glyph dataset (Zenodo DOI, CC-BY 4.0).

Bilingual DE/EN is a cross-cutting guiding principle (German first; English follows).

The post-MVP roadmap in [`architektur.md` §10](docs/concepts/architektur.md#10-reihenfolge--post-mvp-roadmap) sequences these as five phases: Reading help → Practice sheets → Style analysis → Hand comparison → Open data.

## Project structure

```
kurrentschrift/
├── core/       # Pure-Python compute + DB layer (extractor, template, Postgres models)
├── api/        # FastAPI service (thin routing over /core)
├── app/        # React 19 + Vite + MUI SPA — public site (landing, worksheet generator,
│               # letter quiz) + admin behind /admin/* (Cloudflare Access in prod)
├── alembic/    # Schema migrations (styles, hands, sources, bboxes, templates, instances, aggregates)
├── data/       # Sources, variants, samples (separate licensing — see below)
└── docs/       # Design rationale (German); references with technical specs
```

### Local dev

Three steps:

```bash
# Step 1 — once, or whenever the schema changes
uv run alembic upgrade head

# Step 2 — Python backend on :8000
uv run uvicorn api.main:app --reload --port 8000

# Step 3 — Vite dev server on :3000 with /api proxy to :8000
cd app && npm install && npm run dev
```

Browser at `http://localhost:3000` — that is the public landing page; the admin lives under `/admin` and loads the Loth chart, where a step-by-step setup wizard handles per-glyph excludes, ruling, slant and the stroke path (traced with a stylus). For local admin saves, set `ADMIN_TOKEN=<x>` for the API and the matching `VITE_ADMIN_TOKEN=<x>` in `app/.env` (without them, write requests return 401). All canonicals live in Postgres — point `DATABASE_URL` (see `.env.example`) at any empty PostgreSQL database; `alembic upgrade head` creates the schema and seeds the base styles. The admin's SVG diagnostic modal renders Loth-crop, skeleton+anchors, and the canonical template side by side from JSON the backend serves.

## Documentation

Start at [`docs/index.md`](docs/index.md). Highlights:

**Concepts** (the *why*):

- **[Vision der Website](docs/concepts/vision.md)** — seven end-user goals in three clusters (Writing / Reading / Research), guiding principles, target audiences, non-goals, position relative to existing tools
- **[Architektur-Referenz](docs/concepts/architektur.md)** — §1–§17: analysis-by-synthesis, library schema, three-stage quality pipeline, research risk, MVP (four gates), post-MVP phases, animation, style analysis, HTR, Lese-Lupe, print, frontend, open-data
- **[MVP-Roadmap](docs/concepts/mvp-roadmap.md)** — Schritt 0 + M0–M7 milestones, validation gates, verification plan
- **[Naming und OSS-Setup](docs/concepts/naming-und-setup.md)** — name, domain, license, frontend stack, hosting

**Reference** (the *how*):

- **[Sprachregelung](docs/reference/sprachregelung.md)** — German/English per artifact
- **[Quellen- und Rechte-Policy](docs/reference/quellen-und-rechte.md)** — what may enter the public repo
- **[Datenablage](docs/reference/datenablage.md)** — `/data` layout, commit classes, `SOURCE.md` fields
- **[HTR-Integration](docs/reference/htr-integration.md)** — Transkribus API (≈ €0.12/page via paid credits, CER 5–7%; the free tier is app-side quota logic), TrOCR fallback (CER 2.65%), PAGE-XML
- **[Animation-Rendering](docs/reference/animation-rendering.md)** — `stroke-dashoffset` (MVP) and Canvas-2D stroker (post-MVP), Schwellzug sampling, WAAPI choreography
- **[Stil-Analyse](docs/reference/styleanalyse.md)** — per-instance / per-hand / Hinge-feature layers, heatmap layouts
- **[Frontend-Stack](docs/reference/frontend-stack.md)** — React+Vite+MUI build, deploy on Cloud Run, i18n, auth-gated admin routes

**Schriftkunde** (script facts):

- **[Orthographie-Regeln](docs/schriftkunde/orthographie-regeln.md)** — Rund-s, ligatures, mixed-script reading rules
- **Script families** — [overview](docs/schriftkunde/allgemein.md) · [Kurrent](docs/schriftkunde/kurrent.md) · [Sütterlin](docs/schriftkunde/suetterlin.md) · [Offenbacher](docs/schriftkunde/offenbacher.md)

**For AI agents:** [`CLAUDE.md`](CLAUDE.md) (Claude Code) and [`.github/copilot-instructions.md`](.github/copilot-instructions.md) (GitHub Copilot) — kept in sync.

Internal docs are in German (the domain is German). Code, commit messages, and this README are English.

## Data & licensing

Code is MIT. **Data is not.** Each source under `/data/sources/` carries its own license (see its `SOURCE.md`); corpora live outside git; NC-SA-derived materials never reach committed outputs.

First source: the [Loth 1866 Kurrent table](data/sources/loth-1866/SOURCE.md) — Public Domain Mark 1.0, via Wikimedia Commons — the geometry baseline for the MVP. Modern copyrighted teaching books (Süß and similar) stay out of the repo entirely; bibliographic reference only.

## Contributing

This is an in-progress MVP portfolio project — issues (including discussion of the approach) are welcome, external PRs are premature until the four MVP gates land. See **[Contributing Guide](docs/contributing.md)** for what's useful to send right now.

## Citation

If the methodology is useful to your work, see [CITATION.cff](CITATION.cff) for citation metadata.

## License

MIT — see [LICENSE](LICENSE). **Data is separately licensed** (each source under `/data/` carries its own; see [DATA_PROVENANCE.md](data/DATA_PROVENANCE.md)).

---

**Built by [Markus Neusinger](https://linkedin.com/in/markus-neusinger/)**
