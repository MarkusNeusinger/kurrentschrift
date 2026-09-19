---
name: verify-frontend
description: Run and visually verify the kurrentschrift app after frontend changes — start the dev servers (a write flow against a throwaway Postgres, never the shared DB), click through ONLY the flows the change touches (chrome-devtools MCP where it exists, otherwise playwright-core against an already-installed Chromium), watch the console and network, check style fidelity, legibility and colour-vision safety at desktop, tablet and phone viewports, and record a performance trace when the change can move performance. Use when asked to run, start, screenshot, verify, test in the browser, or visually check the app or a frontend change.
---

# Verify the frontend in the browser

React 19 + Vite SPA (`app/`, port 3000) backed by a FastAPI service
(`api/`, port 8000) and, for a read-only run, the shared Cloud SQL
Postgres (`.env`) — **a run that WRITES uses the throwaway stack of
§1b instead.** The preferred browser harness is the **chrome-devtools
MCP server**, which needs no driver script. It comes from the author's
user-level Claude config, not from this repo: verify availability via
ToolSearch (§2), and fall back to §2b's probe when it is absent. All
paths below are relative to the repo root.

> **Environment note:** the chrome-devtools MCP comes from the author's
> user-level config and is **not always there** — it is absent on Claude
> Code on the web, and it is absent in delegated/worktree sessions on the
> local machine too (measured 2026-09-18). If ToolSearch (§2) finds no
> `mcp__chrome-devtools__*` tools, **this is not a dead end:** drive the
> live app through `playwright-core` against an already-installed
> Chromium instead — `/opt/pw-browsers/` in the cloud container,
> `~/.cache/ms-playwright/` on the local box. See **§2b · Probe
> fallback**, which looks in both. Only when *no* Chromium is found at
> all do you fall back to the static gates (`npm run build`,
> type-check) — and then say plainly that no flow was driven rather than
> claiming one was. The Playwright **MCP plugin** stays forbidden as
> this project's harness (Troubleshooting); `playwright-core` driven
> from a script is a different thing and is the sanctioned path.

This skill is a **feedback loop**: after a frontend change, don't just
confirm the page loads — drive it like a user and observe four channels:
interaction (snapshots/clicks), console + network, visual style &
legibility (screenshots at the three viewports of §2, actually looked
at), and performance (trace). Report findings; don't silently fix
design questions.

**Scope: only what the change touches.** Derive the affected pages and
flows from the diff (`git diff --name-only` + the component→route
mapping in `app/src/routes/`) and drive exactly those — a full-app
sweep is not the job here and wastes a round per page. Shared code
(context, lib/api, locales, components/) widens the scope to the
surfaces that consume it; when a shared change has both an admin and a
public consumer, check one representative flow on each side. Everything
the diff cannot reach is out of scope.

## 1 · Start the servers (skip if already up)

Check first — the servers are often already running:

```bash
curl -fsS http://localhost:8000/health && curl -fsS -o /dev/null -w 'vite:%{http_code}\n' http://localhost:3000/
```

If not, start both in the background (Bash `run_in_background: true`),
then re-run the check until healthy (~10 s for uvicorn, ~5 s for Vite):

```bash
uv run uvicorn api.main:app --reload --port 8000
```

```bash
cd app && npm install --no-audit --no-fund && npm run dev
```

Expected: `{"status":"healthy","database_configured":true}` and
`vite:200`. `curl -fsS http://localhost:8000/sources` must list the
four seeded sources incl. `suetterlin-1922` (the public default) —
that proves the DB path works. If the schema is stale:
`uv run alembic upgrade head` — but **only after the DB-target
preflight from `/verify-api`** (alembic is DDL against the shared
Cloud SQL DB, and `.env` has pointed at the wrong database before).
Without `DATABASE_URL` every endpoint except `/health` and `/`
returns 503.

Admin preflight — **mandatory whenever the flow under test writes**
(saves, traces, wizard finish). Without both tokens every save fails
silently with 401; this has shipped "test it in the browser" advice
that could not work. On the throwaway stack the API's token comes from
the export instead (§1b) and only the `app/.env` half of this check
applies:

```bash
grep -q '^ADMIN_TOKEN=.' .env && echo "OK: ADMIN_TOKEN non-empty in .env" || echo "MISSING/EMPTY: ADMIN_TOKEN in .env"
grep -q '^VITE_ADMIN_TOKEN=.' app/.env 2>/dev/null && echo "OK: VITE_ADMIN_TOKEN non-empty in app/.env" || echo "MISSING/EMPTY: VITE_ADMIN_TOKEN in app/.env"
```

(The `=.` matters: a bare `ADMIN_TOKEN=` line would pass a key-only
grep and still 401 every save.)

If either is missing, stop and say so. During the browser run, confirm
one real save returned 2xx in `list_network_requests` before telling
the user a write flow works. Public pages and read endpoints need no
token.

## 1b · Throwaway stack — mandatory for every admin WRITE flow

§1 starts the servers against the SHARED Cloud SQL database. That is
survivable for reads and not for writes: a browser run that saves a
trace, finishes a wizard, applies a Laufform or pushes a Streifen-Pfad
writes the author's hand-made data, and no undo exists for it. So a
write flow is driven against a **throwaway Postgres**, and the PR body
says which stack the flow ran on. Read-only frontend work keeps using
§1 as before.

**The nested-worktree trap, measured.** `api/main.py:9`,
`alembic/env.py:20` and `tools/dbsnapshot/__init__.py:40` call
`load_dotenv()`, which walks UP from the calling file's directory; a
fourth reader, `core/config.py:28`, names `.env` through pydantic's
`env_file`. A fresh worktree under `.claude/worktrees/…` has no `.env`
of its own — and that walk reaches the main checkout anyway:

```
$ uv run python -c "from dotenv import find_dotenv; print(find_dotenv())"
/home/…/projects/kurrentschrift/.env
```

„No `.env` here" is therefore not safety. What makes it safe is an
EXPORTED `DATABASE_URL`: `load_dotenv()` defaults to `override=False`
and pydantic-settings puts the process environment above the file, so
the export wins over all four.

### The exports — all four in the SAME bash call

They do not survive between Bash invocations
(`/verify-migrations` §0), so every command below runs in a shell that
carries them:

```bash
export DATABASE_URL='postgresql+asyncpg://postgres@/kurrentschrift?host=/var/tmp/pg-kurrent-<tag>'
export ADMIN_TOKEN='local-throwaway-token'
export ENVIRONMENT='development'
export EIGENHAND_API='http://localhost:8000'
```

- `<tag>` is yours alone — parallel agents each need their own cluster
  directory, or they migrate and seed on top of each other.
- `ENVIRONMENT=development` because `core/config.py` drives the CORS
  regex and the analytics default off it.
- `EIGENHAND_API` because `tools/eigenhand/apiclient.py:45` defaults to
  `https://api.kurrentschrift.ink` — without it every `python -m
  tools.eigenhand.*` call in the same session writes to PRODUCTION.
- `ADMIN_TOKEN` is made up on the spot. Never fetch the real one from
  Secret Manager for a local stack, and never echo a real secret.

### The preflight, before anything else in that shell

```bash
uv run python - <<'EOF'
import os, sys
from urllib.parse import parse_qs, urlsplit
url = os.environ.get("DATABASE_URL", "")
if not url:
    sys.exit("DATABASE_URL not exported — this process would fall back to .env (SHARED Cloud SQL). STOP.")
parts = urlsplit(url)
host = parts.hostname or (parse_qs(parts.query).get("host") or [""])[0]
print("DATABASE_URL host:", host or "(none)")
if host not in {"127.0.0.1", "localhost", "::1"} and not host.startswith("/var/tmp/"):
    sys.exit(f"refusing: {host!r} is neither a loopback host nor a /var/tmp throwaway socket")
print("target: LOCAL THROWAWAY — safe to migrate, seed and write")
EOF
```

**Why the socket branch is narrow:** „contains no remote hostname" is
not a test, because Cloud SQL is reached over a unix socket too
(`host=/cloudsql/<project>:<region>:<instance>`). Only `/var/tmp/…`
passes — the directory `/verify-migrations` §1 puts the throwaway
cluster in. (A heredoc into `uv run python` is a *command*, not a
repo-file edit; the Edit/Write rule is untouched.)

**In a worktree-isolated session the harness may refuse a heredoc** —
and a compound `export … && …` with it — as "too complex to verify".
Then write these lines and the exports into two files in the session
scratchpad (never into the repo) and run one small `bash` script that
sources the one and runs the other. Same shell, same exports, same
preflight; only the shape changes.

### The freshness proof, immediately before `alembic upgrade head`

The URL check above proves the ENDPOINT is local. It does not prove the
DATABASE is disposable — a Cloud SQL Auth Proxy or an SSH tunnel puts
the shared database on `127.0.0.1:5432`, and then a loopback URL would
wave a schema migration through. So ask the database itself what it
holds, in the same exported shell, **before** the first DDL:

```bash
uv run python - <<'EOF'
import asyncio, os, sys
from urllib.parse import parse_qs, urlsplit
import asyncpg

# The reserved dataset: rows no migration ever creates. Empty (or absent)
# is the signature of a throwaway; one row is the signature of production.
RESERVED = ("templates", "bboxes", "eigenhand_fassungen", "word_instances")

async def main():
    parts = urlsplit(os.environ["DATABASE_URL"].replace("+asyncpg", ""))
    query = parse_qs(parts.query)
    conn = await asyncpg.connect(
        user=parts.username or "postgres", password=parts.password,
        database=(parts.path or "/postgres").lstrip("/"),
        host=(query.get("host") or [parts.hostname])[0], port=parts.port or 5432,
    )
    try:
        filled = []
        for table in RESERVED:
            if await conn.fetchval("SELECT to_regclass($1)", f"public.{table}") is None:
                continue
            count = await conn.fetchval(f"SELECT count(*) FROM {table}")
            if count:
                filled.append(f"{table}={count}")
    finally:
        await conn.close()
    if filled:
        sys.exit(f"refusing: this database already holds the reserved dataset ({', '.join(filled)}) — NOT a throwaway")
    print("freshness: reserved tables absent or empty — this is a throwaway database")

asyncio.run(main())
EOF
```

Measured on three states (2026-09-18): an empty database before any
migration passes, a database migrated to head with the reserved tables
empty passes, and a single row in `templates` refuses. Re-running it on
a cluster you already migrated is therefore free — it is not a one-shot
gate but the sentence you put in front of every `alembic`, and the same
question the seeder's hand check asks one layer up.

### Bring it up

1. **Cluster** — the `pgserver` recipe of `/verify-migrations` §1, with
   your own `/var/tmp/pg-kurrent-<tag>` directory.
2. **Schema** — the freshness proof, then `uv run alembic upgrade head`
   inside the exported shell. This is the one place CLAUDE.md's „never
   `alembic upgrade head` as a setup step" does not bite, *because* the
   two preflights above just proved the target: local endpoint AND
   empty of the reserved dataset.
3. **API** — `uv run uvicorn api.main:app --port 8000` (background) in
   that same shell. `core/database/connection.py:24` reads the URL at
   IMPORT time, so a server started in a shell without the export
   silently serves the shared DB and nothing later can fix it.
4. **SPA** — `app/.env` with `VITE_ADMIN_TOKEN=` matching
   `ADMIN_TOKEN` (gitignored), then `cd app && npm run dev`.
   **The API port is not free to choose:** `app/vite.config.ts:21`
   hardcodes the proxy target `http://127.0.0.1:8000`, so a full SPA
   stack owns port 8000 and only one can run per machine. A second,
   API-only stack may take any port.

### The positive discriminator — run it BEFORE the first write

```bash
curl -fsS localhost:8000/health
curl -s localhost:8000/eigenhand/hands -H "X-Admin-Token: $ADMIN_TOKEN"
```

`{"hands":[],"styles":[…]}` is the proof. No migration seeds a hand —
hands, templates, bboxes, occurrences and every Eigenhand row are the
reserved dataset and live only in the shared DB — so an **empty** hand
list can only be a fresh local database. A populated one means the
process found `.env` after all: stop, fix the export, and restart the
server rather than clicking on.

### Seed something to click

A migrated local database has the three styles, the four chart sources
and the quiz words, and nothing else — the letters/joins/words views
open empty and cannot be judged locally (say so plainly in the PR body
when your flow needed them). The Eigenhand chain is the exception: its
inputs are the committed strip plan and a synthetic PNG, so it can be
seeded whole.

```bash
uv run python .claude/skills/verify-frontend/seed-local-admin.py
```

It prints one Bogen, accepts its rows, stores a flat grey stand-in
strip per row and follows every word with a three-point polyline,
carrying invented `meta.tintenpfad` numbers spread over a good, a
middling and a bad WORD BOX (including a `0.0` and a `null`, the two
values a `||` reader gets wrong); the cycle turns per box, so one strip
already shows all three levels. The seeded hand is
**`wegwerf-suetterlin`** — never the author's `mn-suetterlin`, because
the first call is a `PUT /eigenhand/setups/<hand>` that the API
documents as a plain overwrite. It refuses any non-loopback `--api`,
and it stops dead when the API reports a hand it did not write itself —
that check is not reachable by `--reseed`, which only re-runs over the
seeder's own hand. A second helping on a stack that is already seeded
needs a Fassung of its own (`uq_eigenhand_fassung` is unique on hand ·
strip · Fassung, and a repeat on `F01` comes back as a 500):

```bash
uv run python .claude/skills/verify-frontend/seed-local-admin.py --reseed --fassung F02
```

Everything it writes is synthetic and **must never be measured** — it
is material to click on, not data.

### Teardown

Stop both servers, drop the cluster with the `/verify-migrations` §3
snippet against your own `<tag>`, and `unset DATABASE_URL ADMIN_TOKEN
ENVIRONMENT EIGENHAND_API` (or close the shell) so no later command
runs against a URL that no longer exists — or, worse, so you do not
forget which database the next command means.

### The `/dbsnapshot` trap

`tools/dbsnapshot/__init__.py:40` calls `load_dotenv()`, and
`load_dotenv()` does not override exports. A snapshot taken **inside**
the throwaway shell therefore snapshots the THROWAWAY: an almost-empty
archive that looks like safety. A prod snapshot is taken in a shell
WITHOUT these exports, and its row counts are checked before filing.
Conversely `tools/dbsnapshot/restore.py:171-173` refuses a target equal
to `DATABASE_URL`, so a restore drill into the throwaway needs a second
database name.

## 2 · Drive the app (agent path)

The chrome-devtools MCP tools are deferred — load them first with one
ToolSearch `select:` query, joining the names below comma-separated
**without any whitespace** (a wrapped/spaced query matches nothing).
Tools needed (all prefixed `mcp__chrome-devtools__`):

`new_page` · `navigate_page` · `take_snapshot` · `take_screenshot` ·
`click` · `fill` · `wait_for` · `resize_page` · `evaluate_script` ·
`list_console_messages` · `list_network_requests` ·
`performance_start_trace` · `performance_analyze_insight`

The loop, per page/flow you changed:

1. `new_page` → `http://localhost:3000/` (first time), then
   `navigate_page` for further URLs.
2. **Resize before judging anything.** The default window is unusually
   wide and short. **The three viewports, named once for the whole
   skill — §1b, §2 and §2b all mean these and no others:**

   | Viewport | Why this one |
   |---|---|
   | **1440×900** | the desktop the workbench is built for |
   | **1024×768** | the TABLET the author re-traces words on — a real device in the loop, not a breakpoint sample |
   | **390×844** | the phone, where clipping and the type floor show first |

   `resize_page` to each for every surface in scope. Surfaces the diff
   doesn't touch don't get a viewport pass at all. Narrower widths
   (360, 320) are a column-overflow hunt, not part of the three — reach
   for them with `WIDTHS=` (§2b) when a layout looks fragile.
3. After every navigation to a lazy route: `wait_for` a text unique to
   the target page, **then** `take_snapshot`. Pick text that is *not*
   CSS-uppercased (see Gotchas).
4. Interact via snapshot uids: `click`, `fill`. Re-snapshot after any
   DOM change — uids from older snapshots go stale. For transient
   states (quiz feedback), pass `includeSnapshot: true` on the click
   itself instead of racing a separate screenshot.
5. `take_screenshot` to `/tmp/kurrentschrift-ui/<page>-<viewport>.png`
   and **Read the file — actually look at it**. A snapshot proves the
   DOM is there; only the screenshot shows clipped layouts, broken
   paper texture, unreadable type.
6. `list_console_messages` after each flow — expect **zero** messages.
   `app/public/favicon.ico` ships since 2026-07, so a favicon 404 is
   now a regression, not known noise. Any error/warning is a finding.
7. `list_network_requests` once per page — scan for 4xx/5xx. The quiz
   boots from `/api/sources/suetterlin-1922/bboxes/status` +
   `/templates` and renders its prompts via the shared render cache
   (`/write/glyphs` batches); a 200 on those proves the Vite-proxy →
   API → DB path end to end (chart crops are only the fallback).

**Verify the changed path itself, not a proxy.** For a write flow,
perform the real UI write end-to-end and confirm persistence with a
follow-up read — injecting state via the API or only rendering the
result does not count (a wizard fix once shipped "verified" while its
actual write path was never run). The admin's **bulk / state-toggle
writes are the ones that silently no-op**: „Alle Glyphen neu ableiten"
reported per-glyph deltas while persisting nothing — a re-run gave the
same non-zero deltas instead of 0 — and an unlock left the lock in the
DB so the sidebar and quiz never updated. For these the follow-up read
is non-negotiable: re-run the bulk action and expect delta 0, or read
the bbox/template back and confirm the new `locked`/`anchors`. A 2xx in
`list_network_requests` is necessary but not sufficient — only a read
that shows the mutation proves it. For UI that displays factual or
derived values (presets, size chips), cross-check the displayed
numbers against their source of truth in the same run — a
chips/preset mismatch once shipped and was found on a printout.

Reference flows — pick **only** those the diff touches, this is a
catalog, not a checklist: landing → „Schreiben üben" →
switch Start-Schrift presets (Sütterlin sets 1:1:1 and disables the
Schräglage) → „Schulheft um 1900" (blue ruling + „Rote Randleiste"
switch appears) — and `/quiz`: „Auswahl (Multiple Choice)" → „Quiz
starten" → answer (choices vs. zones: of h/j/a/l only `a` stays within
the Mittellänge) → „beenden" → Auswertung.

**Admin flows are the most regression-prone surface and the least
covered by the catalog above — drive them whenever the diff touches
`app/src/sections/admin/`, `app/src/layouts/admin/`,
`app/src/context/AdminContext.tsx`, or `app/src/domain/glyphs.ts`.**
Each of these shipped broken to `main` and
was caught only by the user clicking the live admin: the Vorlage/source
switcher not switching the rendered chart; a setup-wizard bbox
letterboxed (small, black border) in one step but full-width in
another; the Lücken-füllen / Radierer-Tinte mask not changing the chart
preview; lock state not fanning out from the admin to the sidebar icon
and the quiz. Two invariants they share: (1) **cross-step / cross-layer
state needs the SAME entity checked on BOTH surfaces in one run** —
switch the source and confirm the picker AND the chart image change;
lock a glyph and confirm the sidebar icon AND the quiz de-dup; compare
a glyph's crop across the Ausschluss and Lineatur steps at the same
viewport. (2) **a wizard control that drives a derived preview
(hole-fill, eraser/ink mask, slant) is only verified once you move the
control and see the preview pixels change** — a 200 on the mask/crop
request is not proof.

## 2b · Probe fallback — drive Chromium via Playwright (no MCP)

When ToolSearch finds no `mcp__chrome-devtools__*` tools the MCP is
gone but the browser is not. `cloud-probe.mjs` looks for an
already-installed Chromium in three places, in order:
`$PLAYWRIGHT_BROWSERS_PATH`, `/opt/pw-browsers` (the cloud container)
and `~/.cache/ms-playwright` (a local box that ever ran `playwright
install` — the maintainer's WSL machine has exactly this and no
`/opt`). Drive it with `playwright-core` and you keep the core
channels — interaction, console + network, and screenshots (a perf
trace is reachable via a CDP session but is rarely worth it here). The
name still says „cloud" for history; the path is **verified working
locally and in the cloud container**. It does not replace §2 where the
MCP exists (the MCP is richer and interactive) — it is the substitute
wherever it does not.

One-time setup (per container/session — the scratchpad is ephemeral):

```bash
# SCRATCH is not pre-provided — set it yourself, to the session scratchpad dir named in the prompt
SCRATCH=<the session scratchpad dir named in the prompt>
cd "$SCRATCH" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i playwright-core
```

`PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` is load-bearing: it stops npm from
re-fetching a browser — you want the pre-installed one, pointed at via
`executablePath`. **Never run `playwright install`.**

Then start the servers (§1) and run the bundled probe — it reports the
routine layout channels as machine-readable lines (exact pixels, not
vibes) and writes a screenshot per viewport:

```bash
NODE_PATH="$SCRATCH/node_modules" SHOTS=/tmp/kurrentschrift-ui \
  node .claude/skills/verify-frontend/cloud-probe.mjs \
  http://localhost:3000/ http://localhost:3000/quiz
```

It prints, per URL × viewport (default `1440,1024,390` — the three of
§2; override with `WIDTHS=` for a 360/320 column hunt): horizontal
**overflow** + the widest offending element,
the `h1` computed font-size + family (type-voice check, §3), and a
deduped count of JS errors / 4xx-5xx requests with their paths. Then
**Read the screenshots** under
`SHOTS` — the same "actually look at it" rule as §2 step 5. `NODE_PATH`
is needed because `playwright-core` lives in the scratchpad, not the
repo; the probe loads it via `createRequire` (ESM bare imports ignore
`NODE_PATH`).

The probe covers the 80 % case (did my change break layout / spew
errors). For anything custom — a size **ratio**, a specific element's
rect, a multi-step flow (`click`/`fill`/`wait_for` exist on the
`playwright-core` `page` too) — copy it as a starting point and add the
measurement inside its `page.evaluate()` block, or write a one-off
`.mjs` in the scratchpad. Getting **exact numbers** out of
`getComputedStyle`/`getBoundingClientRect` is the point: it lets you tune
`clamp()` values by calculation instead of eyeballing screenshots. Keep
ad-hoc scripts in the scratchpad (throwaway); only the reusable
`cloud-probe.mjs` is committed. All other rules below (§3 style, §4
trace, Gotchas) apply unchanged — the lazy-route `wait_for` and
scroll-into-view behave the same through Playwright.

## 3 · Style fidelity & legibility check

**`docs/concepts/design-system.md` is the BINDING spec for public
styling** — read it, not a memory of it: the colour tokens, the 19 px type
ladder (its variants plus the Playfair-600 heading rule), the PageContainer
width system (760 / 1152 / 1280) with the Prose ~66-character reading
measure, the surface rule (identity surfaces = paper, work surfaces =
white), and the navigation/IA of the three areas. `style-guide.md` sits
beside it for **rationale and history** (the closed rounds R1–R9) and says
so itself: numbers and tokens are not maintained there any more. Judging a
screenshot against the style guide alone means never seeing the ladder, the
width system or the surface rule.

The binding Leitsatz applies on top: **Lesbarkeit vor Epoche** — no
broken/unreadable type in UI, headlines or body; historic forms only as
marked specimens.

Don't restate either document's facts (palette values, font names) — read
them fresh each run: the tokens live in `app/src/styles/paper.ts` (single
source for palette and type voices). What the skill prescribes is the
**method**:

- Compare each screenshot against what design system + tokens prescribe
  (paper ground, ink text, display vs. body voice, the showpiece
  script never as UI chrome, the container width for the page's kind).
- To check which type voice an element actually uses, computed styles
  beat squinting at pixels: `evaluate_script` with
  `() => { const h1 = document.querySelector('h1'); return getComputedStyle(h1).fontFamily; }`
  and match the first family in the returned stack against the tokens
  exported by `app/src/styles/paper.ts`.
- Legibility: at 390 px width nothing may clip, overlap, or fall under
  ~13 px button text; faint elements (exercise-book blue guides) must
  still read against the paper.

**Colour-vision-deficiency pass — whenever colour carries meaning.**
Run it on any surface where a colour IS the information: overlay
layers (ink · trace · Laufform · Pfad), status chips, a traffic light,
a legend, an „erster Zug grün, letzter blau" sentence. Three questions,
in this order:

1. **Is the colour alone the message?** If the only way to tell two
   things apart is hue, the surface fails before any simulation — add
   the second channel (a dash pattern, a shape, a label) rather than
   picking a nicer hue.
2. **Contrast against its own ground.** A non-text graphical object
   needs 3:1 (WCAG 1.4.11), and the work surfaces are WHITE, not paper
   — the old overlay green `#00b37e` cleared the paper and failed
   against `#fff` at 2.71:1, which is what retired it on 2026-09-19.
   Measure it, don't eyeball it: read the computed colour with
   `evaluate_script`/`page.evaluate` and compute the ratio — and where
   the mark is TRANSLUCENT (`fill-opacity`, `stroke-opacity`),
   alpha-composite it over its ground first. The declared hex is not
   what the eye gets: the engine overlay's Zinnober clears 3:1 opaque
   and composites to 1.81:1 at its drawn 0.42. A translucent
   comparison overlay over a scan is a documented exception (§2 of
   `design-system.md`), so report the composited number rather than
   the token's.
3. **Deuteranope separation.** Simulate (any LMS deuteranopia matrix in
   the same `evaluate` block) and check each PAIR that must stay
   distinguishable, not each colour on its own. Red/green pairs are the
   usual culprits, and the second pair is easy to miss because it goes
   through tokens rather than a literal hex.

Report what you measured, with the numbers. A residual collision that
is carried by a second channel is a documented exception — name it and
the channel that rescues it; a silent one is a finding.

Style questions you find are **findings to report**, not things to
silently "fix" — the style decisions R1–R9 are recorded in the style
guide and must not be re-litigated.

## 3a · Static gates (what CI checks)

Driving the browser does not cover the checks that fail the pipeline. Run
these too, from `app/` — they are the same three the CI „Frontend (build)"
job runs after `npm ci`:

```bash
cd app && npm run lint && npm run test && npm run build
```

`lint` is ESLint, `test` is the Vitest run that pins the `shaping.ts` ↔
`core/shaping.py` twin against `tests/fixtures/shaping_cases.json`, and
`build` is `tsc && vite build`, so it carries the type-check (a bare
`npm run type-check` exists too). A clean click-through with a red ESLint
or a red Vitest still fails in Actions.

## 3b · Numeric rules: focus rings, the type floor, any floor or cap

Every check below has already produced a wrong answer once — measure them
the way this section says, not the obvious way.

**The general rule: a numeric UI rule is verified against the MEASURED
result in the browser, never against the planned one.** A floor, a minimum
size, a cap, a hit-target — the verification names the rule and the number
it measured, on every surface the rule reaches, at all three viewports (§2).
PR #535 shipped a 14 px x-height floor for written lines whose planner sized
lines from the average advance per character; the plan met the floor and the
widest real line did not, because the ink frame's own padding scales with
the writing and was not in the budget. `/lesen/vergleichen` came out at
**13.9 px** — a rule broken by the code that enforces it, and only the
measurement on the page could say so. The fix was to re-plan from the
measured line (`padUnits` in `app/src/lib/lineWrap.ts`), and the honest
consequence is written next to it: a single unbreakable word still falls
below the floor.

- **`element.focus()` from a script does NOT trigger `:focus-visible`.**
  The browser only sets that state for input it considers keyboard-driven,
  so a scripted focus leaves the ring unstyled and a screenshot then
  "proves" a missing focus ring that is perfectly present for a real user.
  The first focus-ring measurement of the audit was a false negative for
  exactly this reason. **Drive focus with real key events**: a Tab walk via
  chrome-devtools `press_key` (or CDP `Input.dispatchKeyEvent` directly),
  then read the ring off the element that actually holds focus —
  `document.activeElement` plus its computed `outline`/`box-shadow`.
  Walking with Tab has a second payoff: it shows the focus ORDER, which a
  per-element `focus()` never can.
- **A type-floor sweep may only count elements that carry their own text.**
  A MUI switch hides a real `<input>` under the rendered track at
  `opacity: 0`; it measures ~13.33 px and trips a naive "below the 13 px
  floor" scan, while nobody can read it either way because it is invisible
  by design. Counting such nodes buries the genuine findings in noise.
  Restrict the sweep to elements with non-empty visible text, and skip
  anything at `opacity: 0`, `visibility: hidden` or zero size. The scan is
  checked in as `app/scripts/type-floor.mjs` (added by PR #485) — use it
  rather than re-deriving the selector logic per session.

### The two grids, and the `--admin` run

```bash
cd app
node scripts/type-floor.mjs    --base http://localhost:<vite>            # public
node scripts/touch-targets.mjs --base http://localhost:<vite>
node scripts/type-floor.mjs    --admin --base http://localhost:<vite>    # workbench
node scripts/touch-targets.mjs --admin --base http://localhost:<vite>
```

`--admin` is a SEPARATE run and not part of the default list, for a reason
worth knowing before you trust either number: without `VITE_ADMIN_TOKEN` in
the dev server's env every admin read 401s, `AdminLayout` shows its
boot-error screen, and the sweep measures THAT. Measured 2026-09-19 on one
build: **411 targets with the token, 11 without** — one „Erneut versuchen"
per route —, and the type-floor run over those eleven boot screens reported
*„All routes clear"*. A literal false green. So run `--admin` only against
the seeded throwaway stack of §1b, and say in the PR body which stack the
numbers come from.

**Two things the scripts cannot reach, and you do by hand:**

- **The Eigenhand tiles.** A hand is a deliberate pick kept in
  `localStorage`, and both scripts launch Chrome on a fresh profile. The two
  `/admin/eigenhand` rows therefore measure the page's chrome only. Drive
  that surface with a **persistent** Playwright profile
  (`chromium.launchPersistentContext`), pick the hand once, and walk it.
- **The keyboard.** No script replaces a Tab walk with real key events
  (see the `:focus-visible` gotcha above). Per list: Tab in, ↑/↓, ←/→,
  `Home`/`End`, Tab out, reading `document.activeElement` and its computed
  `outline` after every press. Per detail: `Alt+Shift+←/→` steps the
  subject, the caption names the order, the list state and `h=` survive it.
  Then the three guards — in a text field nothing fires, with the
  „Kurztasten" switch off nothing fires and the ‹ › buttons still work by
  click, and `Alt+←` is never `preventDefault`ed (dispatch it and read
  `defaultPrevented`; driving the browser's own Back from a page script is
  not something Playwright can do, so that is the honest test).

## 4 · Performance trace

Only when the change can plausibly move performance (data loading,
render loops, bundle/chunk changes) or the user asks — skip it for
pure copy, wiring or admin-tooling changes. Navigate to the target URL
first, then:

- `performance_start_trace` with `reload: true`, `autoStop: true`,
  `filePath: /tmp/kurrentschrift-ui/trace-<page>.json.gz`
- The summary returns lab LCP/CLS plus insight sets; drill in with
  `performance_analyze_insight` (e.g. `LCPBreakdown`, `CLSCulprits`).

Dev-server baseline (this is unbundled Vite dev mode — don't compare
against prod budgets): landing LCP ≈ 670 ms (≈99 % render delay from
the dev-mode module waterfall, LCP element is the hero headline),
CLS 0.00, TTFB ≈ 4 ms. **CLS > 0 or LCP regressions of several hundred
ms against this baseline are real findings; the absolute LCP number is
not.**

## 5 · Run (human path)

`/start` slash command, or the two commands from §1 in two terminals,
then open `http://localhost:3000/` (Vite is pinned to 3000 — not 5173).

## Gotchas (all hit in real runs)

- **Lazy routes race the snapshot.** After `click` on a nav link the
  URL changes immediately but the snapshot still shows the *previous*
  view until the chunk loads. Always `wait_for` target text first.
- **`wait_for` matches DOM text, not rendered text.** Section labels
  like „START-SCHRIFT" are `Start-Schrift` in the DOM with
  `text-transform: uppercase` — waiting for the uppercase form times
  out. Wait for the h1 („Lineatur-Vorlage zum Schreiben") instead.
- **The quiz auto-advances 650 ms after a correct answer** (timer in
  `app/src/sections/quiz/useQuizEngine.ts`). The feedback alert (with
  the Loth crop) is gone before a follow-up screenshot lands. Capture
  it via `includeSnapshot: true` on the answer click.
- **Snapshot uids go stale** after DOM changes (uid namespace prefix
  changes per snapshot). Never reuse uids across interactions that
  mutate the page.
- **Clicking scrolls the element into view**, so the next viewport
  screenshot may show a different page region. Reset with
  `evaluate_script` → `window.scrollTo(0, 0)` before screenshotting.
- **Worksheet preset buttons fan out**: picking „Sütterlin" rewrites
  ratio, x-height, Schräglage *and* the title field — expected
  behaviour, not a bug.

## Troubleshooting

- `wait_for` times out although the page is visibly loaded → you are
  waiting for CSS-uppercased text; wait for non-transformed text (see
  Gotchas).
- "Browser is already in use" pointing at `~/.cache/ms-playwright/…` →
  a stale Chrome from the Playwright MCP plugin holds the profile
  (SingletonLock). Kill those chrome processes and remove the
  profile's `SingletonLock`/`SingletonSocket`, then continue with the
  chrome-devtools tools — the Playwright plugin tools are not the
  harness for this project (a Playwright `browser_navigate` once hung
  a whole session).
- `uv run uvicorn …` fails with "address already in use" → the server
  is already running; just use it (that's why §1 checks first).
