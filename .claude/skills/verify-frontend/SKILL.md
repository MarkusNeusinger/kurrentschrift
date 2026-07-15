---
name: verify-frontend
description: Run and visually verify the kurrentschrift app after frontend changes — start the dev servers, click through ONLY the flows the change touches (chrome-devtools MCP locally, or playwright-core against the pre-installed Chromium in the cloud), watch the console and network, check style fidelity and legibility at a desktop AND a mobile viewport, and record a performance trace when the change can move performance. Use when asked to run, start, screenshot, verify, test in the browser, or visually check the app or a frontend change.
---

# Verify the frontend in the browser

React 19 + Vite SPA (`app/`, port 3000) backed by a FastAPI service
(`api/`, port 8000) and the shared Cloud SQL Postgres (`.env`). The
browser harness is the **chrome-devtools MCP server** — no custom
driver script is needed. It comes from the author's user-level Claude
config, not from this repo: verify availability via ToolSearch (§2)
before relying on it. All paths below are relative to the repo root.

> **Environment note:** the chrome-devtools MCP is a **local-only**
> harness — it is not present on Claude Code on the web. If ToolSearch
> (§2) finds no `mcp__chrome-devtools__*` tools, you are in the cloud.
> **This is not a dead end:** the remote container ships a Chromium under
> `/opt/pw-browsers/` (`PLAYWRIGHT_BROWSERS_PATH`), so you can still drive
> the live app — just via `playwright-core` directly instead of the MCP.
> See **§2b · Cloud fallback**. Only when *both* the MCP is absent *and*
> no Chromium is found under `PLAYWRIGHT_BROWSERS_PATH` do you fall back to
> the static gates (`npm run build`, type-check) — and then say plainly
> that no flow was driven rather than claiming one was.

This skill is a **feedback loop**: after a frontend change, don't just
confirm the page loads — drive it like a user and observe four channels:
interaction (snapshots/clicks), console + network, visual style &
legibility (screenshots at two viewports, actually looked at), and
performance (trace). Report findings; don't silently fix design
questions.

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
cd app && npm install && npm run dev
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
that could not work:

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
   wide and short. For every surface in scope check **both** sizes:
   `resize_page` 1440×900 (desktop) and 390×844 (mobile). Surfaces the
   diff doesn't touch don't get a viewport pass at all.
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

## 2b · Cloud fallback — drive Chromium via Playwright (no MCP)

When ToolSearch finds no `mcp__chrome-devtools__*` tools you are on
Claude Code on the web. The MCP is gone but the browser is not: the
container ships Chromium under `PLAYWRIGHT_BROWSERS_PATH`
(`/opt/pw-browsers/chromium-<rev>/chrome-linux/chrome`). Drive it with
`playwright-core` and you keep the core channels — interaction, console +
network, and screenshots (a perf trace is reachable via a CDP session but
is rarely worth it in the cloud). This path is **verified working in
this environment**; it does not replace §2 locally (the MCP is richer and
interactive) — it is the cloud-only substitute.

One-time setup (per container — the scratchpad is ephemeral):

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

It prints, per URL × viewport (default `1440,390,360,320`; override with
`WIDTHS=`): horizontal **overflow** + the widest offending element,
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
