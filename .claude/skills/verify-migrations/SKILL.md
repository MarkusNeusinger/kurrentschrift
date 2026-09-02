---
name: verify-migrations
description: Verify Alembic schema migrations locally against a throwaway PostgreSQL — single-head check, full upgrade chain incl. seeds, model↔migration drift via alembic check, and a downgrade/upgrade roundtrip — without ever touching the shared Cloud SQL DB. Use when asked to verify, test, or check a migration, a schema change, or alembic revisions before pushing.
---

# Verify migrations against a throwaway Postgres

The shared Cloud SQL DB must never see an untested revision. This skill
runs the CI `migrations` job's sequence (`.github/workflows/ci.yml`) plus a
single-head check, locally, against a disposable PostgreSQL — so a broken
revision, a model↔migration drift, a dual-heads state or a missing downgrade
is caught before the push.

## 0 · The `.env` trap (read first)

`alembic/env.py` calls `load_dotenv()`. Any alembic command run WITHOUT
`DATABASE_URL` exported silently falls back to whatever `.env` holds — and
in this repo's local-dev setup that is the SHARED Cloud SQL DB (there is no
separate local DB; `/verify-api` §1). Exported env vars win over `.env`, but
they do not survive between Bash invocations, so every check below runs with
the throwaway URL exported **in the same Bash call**. A destructive
migration against the shared DB once took prod down; this section is why the
skill exists.

## 1 · Start a throwaway Postgres

**Preferred — the `pgserver` wheel (rootless, no Docker; verified end to end
here on 2026-09-02):**

```bash
uv run --no-project --with pgserver --python 3.12 python - <<'EOF'
import pgserver
db = pgserver.get_server('/var/tmp/pg-kurrent-check', cleanup_mode=None)
db.psql('CREATE DATABASE kurrentschrift;')
print("URI:", db.get_uri())
EOF
```

`--no-project --python 3.12`: pgserver ships no wheels for the project's
Python 3.13, and `--no-project` sidesteps the `requires-python >=3.13`
constraint — the server is a separate process, alembic still runs in the
project env. The bundled server is ~16.x, which is what these checks need.

**Use `/var/tmp/…`, not the session scratchpad.** A Unix socket path is
capped at 107 characters (`sockaddr_un`), and the server appends
`/.s.PGSQL.5432` — 14 of them — to whatever directory you name. A session
scratchpad path already runs to ~91 characters before that suffix, which
leaves no usable margin and varies with the session id, so the server may or
may not come up depending on the session. `/var/tmp/pg-kurrent-check` is
short and always works.

**With Docker (local machine, if the daemon is available):**

```bash
docker run --rm -d --name pg-migrate-check -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=kurrentschrift -p 55432:5432 postgres:16
```

**Claude Code web container** (Postgres 16 installed, but `initdb` refuses
root, so run it as an unprivileged user under `/var/tmp`; the scratchpad
mount denies other users):

```bash
useradd -m pguser 2>/dev/null; mkdir -p /var/tmp/pgscratch && chown -R pguser /var/tmp/pgscratch
su pguser -c "/usr/lib/postgresql/16/bin/initdb -D /var/tmp/pgscratch/data -U postgres --auth=trust -E UTF8 >/dev/null \
  && /usr/lib/postgresql/16/bin/pg_ctl -D /var/tmp/pgscratch/data -o '-p 55432 -k /var/tmp/pgscratch' -l /var/tmp/pgscratch/pg.log start \
  && /usr/lib/postgresql/16/bin/createdb -h /var/tmp/pgscratch -p 55432 -U postgres kurrentschrift"
```

Neither of the two lower paths exists on the maintainer's WSL machine
(`which docker` empty, no `/usr/lib/postgresql/`) — that is why pgserver
leads.

## 2 · The four checks (ONE Bash invocation)

```bash
# pgserver variant (Unix socket):
export DATABASE_URL='postgresql+asyncpg://postgres@/kurrentschrift?host=/var/tmp/pg-kurrent-check'
# Docker/web-container variant instead:
# export DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:55432/kurrentschrift'
uv run alembic heads                                         # exactly ONE head
uv run alembic upgrade head                                  # full chain incl. seeds
uv run alembic check                                         # model ↔ migration drift (autogenerate diff)
uv run alembic downgrade -1 && uv run alembic upgrade head   # newest revision reversible
```

Expected: `heads` prints a single revision (`0028 (head)` on 2026-09-02);
the upgrade ends at head; `check` prints "No new upgrade operations
detected." after a wall of `Detected sequence … assuming SERIAL and
omitting` INFO lines (those are normal, not drift); the roundtrip runs both
directions without error.

## 2a · Before a revision with DROP or a rewrite

A revision that drops or rewrites a column is exactly the class CLAUDE.md's
archive rules name: **take a `tools/dbsnapshot` archive snapshot before the
shared DB ever runs it.** The archive holds the only copy of what no
recomputation brings back (`bboxes`, `templates.raw_path`) — Cloud SQL's own
backups are instance-wide and keep 7 days, while this project's failure mode
is a bad apply noticed weeks later. Create freely, never destroy; the full
rules and the entry command are in `/dbsnapshot`.

## 3 · Tear down

```bash
# pgserver variant:
uv run --no-project --with pgserver --python 3.12 python - <<'EOF'
import pgserver, shutil
pgserver.get_server('/var/tmp/pg-kurrent-check').cleanup()
shutil.rmtree('/var/tmp/pg-kurrent-check', ignore_errors=True)
EOF
```

```bash
docker rm -f pg-migrate-check            # docker variant
su pguser -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/tmp/pgscratch/data stop" && rm -rf /var/tmp/pgscratch   # web-container variant
```

**Unset `DATABASE_URL` (or close the shell) afterwards** so no later
command accidentally runs against the throwaway URL — or worse, so you
don't forget it and export the shared `.env` URL into an alembic call.

## Gotchas

- **`alembic check` needs the DB already migrated to head** — run it
  after `upgrade head`, never against an empty DB (everything would
  look like drift).
- **The URL must keep the `+asyncpg` driver** (`postgresql+asyncpg://…`) —
  `env.py` runs migrations through the async engine when `DATABASE_URL` is
  set. Note also that pgserver's own `get_uri()` names the `postgres`
  database, not the one you just created: take the host from it, write
  `/kurrentschrift` yourself.
- **The downgrade roundtrip only exercises the NEWEST revision** — when a PR
  adds several, widen it (`downgrade -<n>`, then `upgrade head`).
- **A `modify_nullable` finding is usually a forgotten
  `nullable=False`** in a revision, not a model bug — 0004 declares it
  on every `created_at`; new tables must too (0010 forgot it once,
  fixed by 0013).
- **Never point this flow at the shared DB.** The preflight from
  `/verify-api` (user=kurrentschrift db=kurrentschrift means SHARED)
  applies to every alembic command; this skill exists precisely so the
  shared instance never runs experimental DDL.
- Prod schema changes still go through the `kurrentschrift-migrate`
  Cloud Run job in the deploy pipeline (`api/cloudbuild.yaml`), never
  ad-hoc DDL.
