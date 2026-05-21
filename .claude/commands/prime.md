# Prime

> Lightweight orientation for everyday work on kurrentschrift. CLAUDE.md is auto-loaded — the strict rules (German docs / English code, data-licensing tripwires, analysis-by-synthesis architecture) are already in context.

## Run

```bash
git status --short --branch
git log --oneline -5
gh pr list --limit 5 2>/dev/null || echo "(gh CLI not available)"
```

## What this project is

**kurrentschrift**: analysis-by-synthesis re-inking of normed pre-1900 German Kurrent script. The image supplies geometry + ink width; a canonical *ductus* template supplies stroke order and crossing resolution. Library unit is `(glyph, position, variant)`. See `docs/concepts/architektur.md` §2 for the core commitment.

## Where things live

- `core/` — pure-Python compute + DB layer:
  - `core/config.py` — pydantic-settings
  - `core/database/` — SQLAlchemy: `Source`, `Bbox`, `Glyph` + repositories
  - `core/chart.py` — load chart + crop with excludes
  - `core/extract.py` — binarize + skeleton + distance transform (Schwellzug)
  - `core/template.py` — canonical sampling / outline / slant-shear
  - `core/pipeline.py` — `canonical_from_path` + `diagnostic_for_glyph`
- `api/` — FastAPI:
  - `api/main.py`, `api/dependencies.py`, `api/schemas.py`
  - `api/routers/{health,sources,chart,bboxes,glyphs}.py`
- `app/` — React + Vite + TS + MUI admin UI:
  - `app/src/constants.ts` — `SOURCE_ID` + `KNOWN_GLYPHS`
  - `app/src/state.tsx` — admin context
  - `app/src/components/{GlyphSidebar,DiagnosticView}.tsx`
  - `app/src/pages/{ChartPage,EditorPage}.tsx`
- `alembic/` — schema migrations (`versions/0001_initial_schema.py` is the genesis)
- `data/sources/loth-1866/` — Public Domain chart + `SOURCE.md` (bytes on disk; DB only stores the relative path)
- `docs/` — German design docs; `docs/concepts/architektur.md` is the canonical reference

## Stack

Python 3.13+ (`uv`) · PostgreSQL (Cloud SQL on the anyplot instance via `DATABASE_URL` or Cloud SQL Connector) · React 19 + Vite 8 + TypeScript 6 + MUI 9.

## Key design decisions to respect

- **Schema is data, not code**: `style_ratio` ([ascender, x-height, descender]) and `slant_deg` live on `sources` rows. Don't hardcode 2:1:2 or 65° anywhere — read them from the row.
- **Two channels stay separate**: width comes from `distance_transform_edt` on the binarized mask; pen pressure is stored on `raw_path[].pressure` but not used as Schwellzug in v1.
- **Three commit classes** for data (see `docs/reference/datenablage.md` §1): PD/own-hand → committable; corpora → gitignored; NC-SA derivatives → gitignored. Süß-Lehrbuch never enters the repo.
- **German UI, English code/identifiers/commits** — see `docs/reference/sprachregelung.md`.

## Common workflows

- **New migration**: `uv run alembic revision -m "describe change"` → edit `alembic/versions/00xx_*.py` → `uv run alembic upgrade head`.
- **Trace a glyph through the UI**: pick glyph in sidebar → drag bbox on chart → set baseline/midband in editor → switch mode to "Strich zeichnen" → trace with stylus → "Canonical speichern".
- **Resample without redrawing**: change `n_anchors` in editor → "Neu abtasten" (uses stored `raw_path`).

## Need more?

- `/start` — start backend + frontend dev servers in the background
- `docs/concepts/architektur.md` — full architecture
- `docs/concepts/mvp-roadmap.md` — milestone breakdown
- `docs/reference/quellen-und-rechte.md` + `docs/reference/datenablage.md` — data/licensing policy
