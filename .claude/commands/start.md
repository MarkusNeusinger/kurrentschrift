# Start Development Servers

Start the FastAPI backend and the React (Vite) frontend in the background so they keep running while you work.

## Instructions

Use `run_in_background: true` on each Bash call so they don't block the conversation.

1. **Backend** — FastAPI on `:8000` (`core/config.py` reads `.env` via pydantic-settings for `DATABASE_URL`):

   ```bash
   uv run uvicorn api.main:app --reload --port 8000
   ```

2. **Frontend** — Vite dev server on `:3000` (port pinned in `app/vite.config.ts`):

   ```bash
   cd app && npm install --no-audit --no-fund && npm run dev
   ```

   (`--no-audit --no-fund`: the audit step turns a 13-second install into
   eight minutes of silence on this machine.)

After starting, verify both responded successfully:

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/sources    # should list at least loth-1866
```

…and confirm the Vite output printed `Local: http://localhost:3000/`. Report any startup errors to the user instead of declaring success.

## Notes

- Backend: `http://localhost:8000` · OpenAPI at `/docs`
- Frontend: `http://localhost:3000` (do **not** assume Vite's default 5173)
- DB: Postgres `kurrentschrift` on the anyplot Cloud SQL instance — see `.env` for `DATABASE_URL`. The API will run without a DB but every endpoint except `/health` and `/` will return 503.
- Schema out of date? **Do not migrate from here.** That DB is the shared Cloud SQL instance prod reads, and `alembic/env.py` calls `load_dotenv()` — so a bare `uv run alembic upgrade head` runs DDL against production. Schema changes ride the `kurrentschrift-migrate` Cloud Run job in the deploy pipeline (`api/cloudbuild.yaml`); to check a revision locally, run `/verify-migrations` against a throwaway Postgres.
- Admin writes locally need `ADMIN_TOKEN` for the API plus a matching `VITE_ADMIN_TOKEN` in `app/.env`, so the SPA sends `X-Admin-Token`; without them every save returns 401.
- Stop the servers with the matching background-process controls when finished.
