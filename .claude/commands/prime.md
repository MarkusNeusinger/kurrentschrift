# Prime

> Lightweight orientation for everyday work on kurrentschrift. CLAUDE.md is auto-loaded — the strict rules (German docs / English code, data-licensing tripwires, analysis-by-synthesis architecture) are already in context.

## Run

```bash
git status --short --branch
git log --oneline -5
gh pr list --limit 5 2>/dev/null || echo "(no gh — on Claude Code web, list PRs via mcp__github__list_pull_requests instead)"
```

> **Environment note:** locally the `gh` CLI is available; on Claude
> Code on the web it is **not** — use the GitHub MCP tools
> (`mcp__github__*`, loaded via `ToolSearch`) for any PR/issue/CI work
> there. `/open-pr` §0 has the full `gh` ↔ MCP mapping.

## What this project is

**kurrentschrift**: analysis-by-synthesis re-inking of the normed German cursive scripts (Kurrent · Sütterlin · Offenbacher). The image supplies geometry + ink width; a canonical *ductus* template supplies stroke order and crossing resolution. Library unit is `(style, glyph, position, variant)`. See `docs/concepts/architektur.md` §2 for the core commitment.

## Where things live

- `core/` — pure-Python compute + DB layer:
  - `core/config.py` — pydantic-settings
  - `core/database/` — SQLAlchemy: `Style` · `Hand` · `Source` · `Bbox` · `Template` · `Instance` · `Aggregate` · `QuizWord` + repositories
  - `core/chart.py` — load chart + crop (eraser/ink/patches applied pre-binarisation)
  - `core/extract.py` — binarize + skeleton + distance transform (Schwellzug)
  - `core/template.py` — canonical sampling / outline / slant-shear / chisel sweep
  - `core/pipeline.py` — `canonical_from_path` + `diagnostic_for_glyph` + `render_payload_for_template`
  - `core/shaping.py` + `core/compose.py` — text → glyph_keys → composed word (THE composition source of truth, pinned by `tests/fixtures/compose_golden.json.gz`)
  - `core/widths.py` — pen models (pressure · constant · broad_nib) · `core/fit.py` — M4 template-to-instance fit
  - `core/quality.py` (Kurrent) + `core/quality_suetterlin.py` (Gleichzug) — the two frozen bench metrics
- `api/` — FastAPI:
  - `api/main.py`, `api/dependencies.py`, `api/schemas.py`, `api/auth.py` (Cloudflare Access JWT + X-Admin-Token), `api/rendering.py` (style resolution + pooled nib)
  - `api/routers/{health,styles,hands,sources,chart,bboxes,templates,write,quiz_words}.py` — public reads incl. `/write/glyphs` + `/write/word`; admin writes behind `require_admin`; `/fit` + `/quality` are admin-gated too
- `app/` — React 19 + Vite + TS + MUI SPA (public site + admin):
  - `app/src/domain/glyphs.ts` — alphabet/glyph-key registry (canonical constants home) · `domain/shaping.ts` — quiz-gating twin of `core/shaping.py`
  - `app/src/context/AdminContext.tsx` — admin state · `lib/api/` — fetch client + endpoints + `renderCache.ts`
  - `app/src/sections/{landing,schriftkunde,hub,worksheet,scribe,tafel,quiz,impressum,admin/*}` + thin `pages/` mounts · `routes/paths.ts`
  - `app/src/components/` — PageContainer · PageHeader · CategoryHeading · PaperCardLink · inkReveal · WrittenGlyph · WrittenWord …
- `alembic/` — schema migrations (`0004_library_schema.py` rebuilt the model; seeds for the three styles + four chart sources)
- `data/sources/` — PD chart bytes + `SOURCE.md` per source (loth-1866 · suetterlin-1922 · koch-1928 · petzendorfer-1889; DB only stores the relative path)
- `tools/` — glyphbench/wordbench (frozen benches) · glyphlab/wordlab/pairlab (viz) · quizgen (word bank)
- `docs/` — German design docs; `docs/concepts/architektur.md` is the canonical reference

## Stack

Python 3.13+ (`uv`) · PostgreSQL (Cloud SQL on the anyplot instance via `DATABASE_URL` or Cloud SQL Connector) · React 19 + Vite 8 + TypeScript 6 + MUI 9.

## Key design decisions to respect

- **Schema is data, not code**: `style_ratio` ([ascender, x-height, descender]) and `slant_deg` live on `styles`/`sources` rows. Don't hardcode 2:1:2 or 65° anywhere — read them from the row.
- **Two channels stay separate**: width comes from `distance_transform_edt` on the binarized mask; darkness is a separate intensity channel.
- **Three commit classes** for data (see `docs/reference/datenablage.md` §1): PD/own-hand → committable; corpora → gitignored; NC-SA derivatives → gitignored. Süß-Lehrbuch never enters the repo.
- **German UI, English code/identifiers/commits** — see `docs/reference/sprachregelung.md`.
- **The benches are frozen during optimization loops** — edit the composer/pipeline, never the ruler (`docs/reference/qualitaetsmetrik.md`).

## Common workflows

- **New migration**: `uv run alembic revision -m "describe change"` → edit `alembic/versions/00xx_*.py` → `uv run alembic upgrade head`.
- **Author a glyph**: admin sidebar → letter → Einrichtungs-Wizard (Ausschluss → Lineatur → Schräglage → Weg → Übersicht/lock); the Weg step records the ductus per pen-stroke.
- **Re-derive after pipeline changes**: per-glyph "Neu abtasten" (uses stored `raw_path`) or the diagnostics' re-derive.

## Need more?

- `/start` — start backend + frontend dev servers in the background
- `docs/concepts/architektur.md` — full architecture · `docs/concepts/design-system.md` — public-UI build spec
- `docs/concepts/mvp-roadmap.md` — milestone breakdown
- `docs/reference/quellen-und-rechte.md` + `docs/reference/datenablage.md` — data/licensing policy
