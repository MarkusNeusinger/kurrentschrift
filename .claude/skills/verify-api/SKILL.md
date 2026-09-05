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

All of these are GET and safe against the shared DB. `suetterlin-1922`
is the public site's source (`CONFIG.sourceId`) and the most-authored
one, so sweep against it:

```bash
curl -fsS http://localhost:8000/styles | python3 -c 'import json,sys; d=json.load(sys.stdin); print([s["id"] for s in d])'
curl -fsS http://localhost:8000/sources | python3 -c 'import json,sys; d=json.load(sys.stdin); print([s["id"] for s in d])'
curl -fsS http://localhost:8000/quiz-words | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))'
curl -fsS http://localhost:8000/sources/suetterlin-1922/bboxes/status | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d), sum(1 for b in d if b["locked"]))'
curl -fsS http://localhost:8000/sources/suetterlin-1922/templates | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d))'
```

Expected baseline: styles = `['kurrent', 'offenbacher', 'suetterlin']`
(three seeded Grundvorlagen); sources = `['koch-1928', 'loth-1866',
'petzendorfer-1889', 'suetterlin-1922']` (four seeded chart sources);
quiz-words ≈ 640 and grows with every re-seed (641 on 2026-09-02). Bbox
status + templates list the authored glyph keys — the counts grow as glyphs
get authored, so check shape, not exact numbers.

**`/hands` is NOT in this sweep** — it is admin-gated since 2026-08-28
(`api/routers/hands.py`: the writer registry is the index of the reserved
dataset). It belongs to the 401 probes in §3.

The public write/render endpoints (the engine behind Federprobe, Tafel
and the quiz — a 200 with `items`/`glyphs` verifies core + DB + chart
file together, and both carry Cache-Control):

```bash
curl -fsS 'http://localhost:8000/sources/suetterlin-1922/write/word?text=lesen' | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d["items"]), d["missing"])'
curl -fsS 'http://localhost:8000/sources/suetterlin-1922/write/glyphs?keys=n' | python3 -c 'import json,sys; d=json.load(sys.stdin); print([g["glyph_key"] for g in d["glyphs"]], d["missing"])'
curl -fsS -o /dev/null -w '%{content_type} %{http_code}\n' http://localhost:8000/sources/suetterlin-1922/bboxes/n/crop
```

Expected: word compose returns draw items (missing = `[]` for a fully
authored word); `write/glyphs` returns `['n'] []`; crop returns
`image/png 200`.

**glyph_keys are BARE** (`n`, `longs`, `ch`) since migration `0017`
(2026-07-17) removed the position suffix. A positional key like `n-medial`
is not an error you can read — it silently answers `{"glyphs":[],
"missing":["n-medial"]}` and the crop 404s. If a sweep line comes back
empty, check the key shape before suspecting the data.

## 3 · Admin write gate (probe only — do not write)

Write endpoints (`PUT`/`DELETE` bboxes, `POST …/trace`,
`POST …/trace-preview`, `POST …/resample`, `DELETE` templates) AND a set of
READS are gated by `require_admin`: everything that hands out a bbox row, a
template row, an occurrence, a pair override, a hand, an aggregate or the
own-hand Bestand. That is the open-core reservation, not a performance
guard — `/hands`, the raw `GET …/templates/{key}`, `…/diagnostic`, `…/fit`
and `…/quality` all answer 401 unauthenticated, and each of those 401s is
correct, not a regression. The safe probe is the unauthorized request:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X PUT -H 'Content-Type: application/json' -d '{}' http://localhost:8000/sources/suetterlin-1922/bboxes/n
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/sources/suetterlin-1922/templates/n/fit
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/sources/suetterlin-1922/templates/n/diagnostic
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/hands
```

Expected: `401` for all four with `ADMIN_TOKEN` configured — or `503` when neither
`ADMIN_TOKEN` nor Cloudflare Access is configured (`require_admin`
fails closed, `api/auth.py`); a 503 here means the env is missing the
token, not that the gate is broken. **Do not send authorized writes
as part of routine verification** — with `ADMIN_TOKEN`/`X-Admin-Token` they mutate the
shared Cloud SQL data that the admin UI authored. Only exercise an
authorized write when the task explicitly is about that endpoint, and
prefer a glyph key the user designates as scratch.

**A tool that writes shared state carries its contract version, and the
SERVER refuses a stale one.** The rule is a design duty for any new
admin-write path, not just a check: whenever the API and the pushing tool
must agree on how the data is computed, the payload carries a marker of that
agreement and the route answers `409` on a mismatch. `tools.lesarten.sync` is
the worked example (#534): the bucket keys are computed in `add_forms` on the
server, so a newer loader pushed at an older API would fill the table with
the OLD buckets while labelling them with the new fold — a vocabulary that
reports itself current and no reader can reach. `api/routers/lesarten.py`
compares `core.lesarten.LESART_KEY_VERSION` against the marker in the build's
source label and answers „deploy the new fold first". Version-free legacy
labels stay allowed and simply read as stale, which is the truth about them.

Two properties to keep when you add such a path: the refusal is the
SERVER's (a tool that checks itself is a tool that can be run with an old
copy), and the mismatch message names both versions and the direction to
fix. The probe is cheap — push a payload with a bumped marker at a server
that has not been deployed yet and expect a 409, never a silent 200.

## 4 · Tests

The API/compute test suite (synthetic fixtures, no DB or network
needed) is the same one CI runs:

```bash
uv run --extra test pytest
```

Expected: all pass (a handful of tool-fixture tests skip when the
local-only bench fixtures are absent — that's normal). Check "all
pass", not an exact count; the suite grows continuously. CI
(`.github/workflows/ci.yml`) runs this plus ruff on every push/PR —
see the `verify-core` skill for the lint commands. The HTTP-level API
suites (`tests/test_api_http.py`, `tests/test_api_admin_writes.py`,
`tests/test_api_auth.py`) already cover the gate, the authorized write
paths and the CF-Access branch against in-memory SQLite — no live DB
needed for those.

**`tests/test_api_public_surface.py` is the authority on which read is
public and which is reserved** — it enumerates every GET route of the app
and fails when one is in neither set, so the split can never drift
silently. Read it before moving a line between §2 and §3 here, and add the
route there in the same PR as any new read endpoint. When a sweep line and
that file disagree, the file is right and this skill is stale.

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
- **`/hands` answers 401, and that is correct** since 2026-08-28 — it is
  the writer registry of the reserved dataset, not a broken endpoint. An
  older reading of this skill expected `[]`; it never will again.
- **`/diagnostic` is admin-gated AND slow-ish** (it runs skeletonisation on
  the chart crop per call). Authorized, a sub-second JSON response is the
  norm locally with keys `anchors_template`, `outline_polygons`,
  `template_guides`. Unauthorized it is a 401 like `/fit` + `/quality` —
  probe for the 401, don't expect a public 200.
- **Router prefixes nest under sources**: bboxes and templates live at
  `/sources/{source_id}/…`, not top-level. Seeded sources:
  `loth-1866` + `petzendorfer-1889` (Kurrent), `suetterlin-1922`
  (the public default), `koch-1928` (Offenbacher).

## Troubleshooting

- `uv run uvicorn …` → "address already in use": the server is
  already running (that's why §1 checks first); just use it.
- Endpoints (except `/`, `/health`) return 503: `DATABASE_URL` not
  loaded — check `.env` exists in the repo root.
