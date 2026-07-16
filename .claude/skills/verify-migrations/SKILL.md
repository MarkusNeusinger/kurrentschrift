---
name: verify-migrations
description: Verify Alembic schema migrations locally against a throwaway PostgreSQL — full upgrade chain incl. seeds, model↔migration drift via alembic check, and a downgrade/upgrade roundtrip — without ever touching the shared Cloud SQL DB. Use when asked to verify, test, or check a migration, a schema change, or alembic revisions before pushing.
---

# Verify migrations against a throwaway Postgres

The shared Cloud SQL DB must never see an untested revision. This skill
runs the exact sequence the CI `migrations` job runs
(`.github/workflows/ci.yml`), locally, against a disposable PostgreSQL —
so a broken revision, a model↔migration drift or a missing downgrade is
caught before the push.

## 1 · Start a throwaway Postgres

**With Docker (local machine):**

```bash
docker run --rm -d --name pg-migrate-check -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=kurrentschrift -p 55432:5432 postgres:16
```

**Without Docker (Claude Code web container — Postgres 16 is installed,
but initdb refuses root, so run it as an unprivileged user under
`/var/tmp`; the scratchpad mount denies other users):**

```bash
useradd -m pguser 2>/dev/null; mkdir -p /var/tmp/pgscratch && chown -R pguser /var/tmp/pgscratch
su pguser -c "/usr/lib/postgresql/16/bin/initdb -D /var/tmp/pgscratch/data -U postgres --auth=trust -E UTF8 >/dev/null \
  && /usr/lib/postgresql/16/bin/pg_ctl -D /var/tmp/pgscratch/data -o '-p 55432 -k /var/tmp/pgscratch' -l /var/tmp/pgscratch/pg.log start \
  && /usr/lib/postgresql/16/bin/createdb -h /var/tmp/pgscratch -p 55432 -U postgres kurrentschrift"
```

## 2 · The three checks (same as CI)

```bash
export DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:55432/kurrentschrift'
uv run alembic upgrade head        # full chain incl. seeds
uv run alembic check               # model ↔ migration drift (autogenerate diff)
uv run alembic downgrade -1 && uv run alembic upgrade head   # newest revision reversible
```

Expected: upgrade ends at head; check prints "No new upgrade operations
detected."; the roundtrip runs both directions without error.

## 3 · Tear down

```bash
docker rm -f pg-migrate-check            # docker variant
su pguser -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/tmp/pgscratch/data stop" && rm -rf /var/tmp/pgscratch   # container variant
```

**Unset `DATABASE_URL` (or close the shell) afterwards** so no later
command accidentally runs against the throwaway URL — or worse, so you
don't forget it and export the shared `.env` URL into an alembic call.

## Gotchas

- **`alembic check` needs the DB already migrated to head** — run it
  after `upgrade head`, never against an empty DB (everything would
  look like drift).
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
