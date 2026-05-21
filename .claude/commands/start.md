# Start Development Servers

Start the FastAPI backend and the React (Vite) frontend in the background so they keep running while you work.

## Instructions

Use `run_in_background: true` on each Bash call so they don't block the conversation.

1. **Backend** — FastAPI on `:8000` (loads `.env` via `python-dotenv` for `DATABASE_URL`):

   ```bash
   uv run uvicorn api.main:app --reload --port 8000
   ```

2. **Frontend** — Vite dev server on `:3000` (port pinned in `app/vite.config.ts`):

   ```bash
   cd app && npm install && npm run dev
   ```

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
- If the schema is out of date: `uv run alembic upgrade head` before starting the API.
- Stop the servers with the matching background-process controls when finished.
