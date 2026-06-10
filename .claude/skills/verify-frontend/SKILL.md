---
name: verify-frontend
description: Run and visually verify the kurrentschrift app after frontend changes — start the dev servers, click through the UI like a user via the chrome-devtools MCP, watch the console and network, check style fidelity and legibility at a desktop AND a mobile viewport, and record a performance trace. Use when asked to run, start, screenshot, verify, test in the browser, or visually check the app or a frontend change.
---

# Verify the frontend in the browser

React 19 + Vite SPA (`app/`, port 3000) backed by a FastAPI service
(`api/`, port 8000) and the shared Cloud SQL Postgres (`.env`). The
browser harness is the **chrome-devtools MCP server** — no custom
driver script is needed. It comes from the author's user-level Claude
config, not from this repo: verify availability via ToolSearch (§2)
before relying on it. All paths below are relative to the repo root.

This skill is a **feedback loop**: after a frontend change, don't just
confirm the page loads — drive it like a user and observe four channels:
interaction (snapshots/clicks), console + network, visual style &
legibility (screenshots at two viewports, actually looked at), and
performance (trace). Report findings; don't silently fix design
questions.

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
cd app && npm install && npm run dev
```

Expected: `{"status":"healthy","database_configured":true}` and
`vite:200`. `curl -fsS http://localhost:8000/sources` must list
`loth-1866` — that proves the DB path works. If the schema is stale:
`uv run alembic upgrade head` first. Without `DATABASE_URL` every
endpoint except `/health` and `/` returns 503.

Admin preflight — **mandatory whenever the flow under test writes**
(saves, traces, wizard finish). Without both tokens every save fails
silently with 401; this has shipped "test it in the browser" advice
that could not work:

```bash
grep -q '^ADMIN_TOKEN=' .env && echo "OK: ADMIN_TOKEN in .env" || echo "MISSING: ADMIN_TOKEN in .env"
grep -q '^VITE_ADMIN_TOKEN=' app/.env 2>/dev/null && echo "OK: VITE_ADMIN_TOKEN in app/.env" || echo "MISSING: VITE_ADMIN_TOKEN in app/.env"
```

If either is missing, stop and say so. During the browser run, confirm
one real save returned 2xx in `list_network_requests` before telling
the user a write flow works. Public pages and read endpoints need no
token.

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
   wide and short. Check **both** sizes — this is mandatory, not
   optional: `resize_page` 1440×900 (desktop) and 390×844 (mobile).
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
6. `list_console_messages` after each flow — expect **zero** messages
   apart from the known `favicon.ico` 404. Any new error/warning is a
   finding.
7. `list_network_requests` once per page — scan for 4xx/5xx. The quiz
   feedback loads Loth crops from
   `/api/sources/loth-1866/bboxes/<glyph>-<position>/crop`; a 200
   there proves the Vite-proxy → API → DB → chart-crop path end to end.

**Verify the changed path itself, not a proxy.** For a write flow,
perform the real UI write end-to-end and confirm persistence with a
follow-up read — injecting state via the API or only rendering the
result does not count (a wizard fix once shipped "verified" while its
actual write path was never run). For UI that displays factual or
derived values (presets, size chips), cross-check the displayed
numbers against their source of truth in the same run — a
chips/preset mismatch once shipped and was found on a printout.

Flows worth a round-trip (all verified): landing → „Schreiben üben" →
switch Start-Schrift presets (Sütterlin sets 1:1:1 and disables the
Schräglage) → „Schulheft um 1900" (blue ruling + „Rote Randleiste"
switch appears) — and `/quiz`: „Auswahl (Multiple Choice)" → „Quiz
starten" → answer (choices vs. zones: of h/j/a/l only `a` stays within
the Mittellänge) → „beenden" → Auswertung.

## 3 · Style fidelity & legibility check

Judge every screenshot against `docs/concepts/style-guide.md` (and the
binding Leitsatz: **Lesbarkeit vor Epoche** — no broken/unreadable type
in UI, headlines or body; historic forms only as marked specimens):

Don't restate the style guide's facts (palette values, font names) —
read them fresh each run: the prose decisions live in the style guide,
the tokens in `app/src/styles/paper.ts` (single source for palette and
type voices). What the skill prescribes is the **method**:

- Compare each screenshot against what guide + tokens prescribe
  (paper ground, ink text, display vs. body voice, the showpiece
  script never as UI chrome).
- To check which type voice an element actually uses, computed styles
  beat squinting at pixels: `evaluate_script` with
  `() => { const h1 = document.querySelector('h1'); return getComputedStyle(h1).fontFamily; }`
  and match the first family in the returned stack against the tokens
  exported by `app/src/styles/paper.ts`.
- Legibility: at 390 px width nothing may clip, overlap, or fall under
  ~13 px button text; faint elements (exercise-book blue guides) must
  still read against the paper.

Style questions you find are **findings to report**, not things to
silently "fix" — the style decisions R1–R9 are recorded in the style
guide and must not be re-litigated.

## 4 · Performance trace

Navigate to the target URL first, then:

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
- **`favicon.ico` 404** appears in console + network on every page
  load. Known noise — don't chase it, but don't let it mask other 404s.
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
