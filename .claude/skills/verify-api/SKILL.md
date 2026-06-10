---
name: verify-api
description: Run and exercise the FastAPI backend — start uvicorn, sweep the read endpoints with curl, check the diagnostic/fit/crop payloads against the live DB, and probe the admin write gate. Use when asked to run, start, test, or verify the API, a router, an endpoint, or a backend change.
---

# Verify the API against the live server

FastAPI service in `api/` (routers in `api/routers/`), data in the
shared Cloud SQL Postgres (`.env` → `DATABASE_URL`). **Local dev talks
to the SAME Cloud SQL DB as prod — there is no separate local DB.**
Treat every write as touching real data. All paths relative to the
repo root; the harness is `curl` + `python3` for JSON checks.

## 1 · Start the server (skip if already up)

```bash
curl -fsS http://localhost:8000/health
```

If not running, start in the background (Bash `run_in_background: true`):

```bash
uv run uvicorn api.main:app --reload --port 8000
```

Expected: `{"status":"healthy","database_configured":true}`. If the
schema is stale: `uv run alembic upgrade head` — but **only after the
DB-target preflight from the Gotchas below** (alembic is DDL against
the shared DB). Without `DATABASE_URL` every endpoint except `/` and
`/health` returns 503.
OpenAPI UI: `http://localhost:8000/docs` (returns 200).

## 2 · Read-endpoint sweep (agent path, safe)

All of these are GET and safe against the shared DB:

```bash
curl -fsS http://localhost:8000/styles | python3 -c 'import json,sys; d=json.load(sys.stdin); print([s["id"] for s in d])'
curl -fsS http://localhost:8000/hands
curl -fsS http://localhost:8000/sources/loth-1866/bboxes | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d), [b["glyph_key"] for b in d])'
curl -fsS http://localhost:8000/sources/loth-1866/templates | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d), [t["glyph_key"] for t in d])'
```

Expected baseline (2026-06): styles = `['kurrent', 'offenbacher',
'suetterlin']` (the three seeded Grundvorlagen); `hands` = `[]`;
bboxes and templates each list the authored glyph keys (currently the
`a`/`u` clusters across initial/medial/final — the count grows as
glyphs get authored, so check shape, not exact numbers).

The compute-heavy read endpoints (these run the real extract/fit
pipeline server-side on the Loth chart, so a 200 with the right keys
verifies core + DB + chart file together):

```bash
curl -fsS http://localhost:8000/sources/loth-1866/templates/u-medial/diagnostic | python3 -c 'import json,sys; print(sorted(json.load(sys.stdin).keys()))'
curl -fsS http://localhost:8000/sources/loth-1866/templates/u-medial/fit | python3 -c 'import json,sys; print(sorted(json.load(sys.stdin).keys()))'
curl -fsS -o /dev/null -w '%{content_type} %{http_code}\n' http://localhost:8000/sources/loth-1866/bboxes/u-medial/crop
```

Expected: diagnostic keys include `anchors_template`,
`outline_polygons`, `skeleton_polyline_px`, `template_guides`; fit
keys include `fitted_polyline_px`, `canonical_polyline_px`,
`placement`; crop returns `image/png 200`.

## 3 · Admin write gate (probe only — do not write)

Write endpoints (`PUT`/`DELETE` bboxes, `POST …/trace`,
`POST …/resample`, `DELETE` templates) are gated by `require_admin`.
The safe probe is the unauthorized request:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X PUT -H 'Content-Type: application/json' -d '{}' http://localhost:8000/sources/loth-1866/bboxes/u-medial
```

Expected: `401` with `ADMIN_TOKEN` configured — or `503` when neither
`ADMIN_TOKEN` nor Cloudflare Access is configured (`require_admin`
fails closed, `api/auth.py`); a 503 here means the env is missing the
token, not that the gate is broken. **Do not send authorized writes
as part of routine verification** — with `ADMIN_TOKEN`/`X-Admin-Token` they mutate the
shared Cloud SQL data that the admin UI authored. Only exercise an
authorized write when the task explicitly is about that endpoint, and
prefer a glyph key the user designates as scratch.

## 4 · Tests

The API/compute test suite (synthetic fixtures, no DB or network
needed) is the same one CI runs:

```bash
uv run --extra test pytest
```

Expected: all pass (29 tests, ~15 s as of 2026-06). CI
(`.github/workflows/ci.yml`) runs this plus ruff on every push/PR —
see the `verify-core` skill for the lint commands.

## Gotchas

- **The DB is shared.** A locally "tested" PUT/POST/DELETE lands in
  the same Cloud SQL instance prod reads. The 401 probe is the only
  write-shaped request that is always safe.
- **Check which DB `.env` points at before ANY alembic/DDL command** —
  the local `.env` has pointed at the anyplot database before, and a
  destructive migration against the shared DB once took prod down.
  Preflight (must print `user=kurrentschrift db=kurrentschrift`,
  anything else → stop):

  ```bash
  python3 -c "
  import re
  url = next(l.split('=',1)[1].strip() for l in open('.env') if l.startswith('DATABASE_URL='))
  m = re.search(r'//([^:]+):[^@]*@[^/]+/([^?\s]+)', url)
  print(f'user={m.group(1)} db={m.group(2)}')"
  ```

  Prod schema changes go through the `kurrentschrift-migrate` Cloud
  Run job that the deploy pipeline executes (`api/cloudbuild.yaml`),
  never ad-hoc DDL.
- **`hands` being empty is normal** at the current MVP stage — don't
  read it as a broken endpoint.
- **`/diagnostic` and `/fit` are slow-ish by design** (they run
  skeletonisation + the regularised fit on the chart crop per call);
  a sub-second JSON response is still the norm locally.
- **Router prefixes nest under sources**: bboxes and templates live at
  `/sources/{source_id}/…`, not top-level. The only seeded source is
  `loth-1866`.

## Troubleshooting

- `uv run uvicorn …` → "address already in use": the server is
  already running (that's why §1 checks first); just use it.
- Endpoints (except `/`, `/health`) return 503: `DATABASE_URL` not
  loaded — check `.env` exists in the repo root.
