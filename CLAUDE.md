# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A companion guide `.github/copilot-instructions.md` carries the same domain
rules targeted at GitHub Copilot (and any other agent that reads that
standard path). Both files MUST stay in sync — if you change one, check
the other.

## Repository state

In-progress MVP. Monorepo per `docs/concepts/naming-und-setup.md` §3; the map
below says what lives where and which invariants bind — details live in the
named docs, and any change to a `/write/*` route, a metric or a migration
updates its owning doc in the same PR.

- **`/core`** — pure-Python compute + DB layer (no HTTP, no I/O beyond the DB
  repositories). `pipeline.py` (chart → canonical), `template.py` (sampling/
  outline/slant), `shaping.py` (text → glyph keys; Python twin of the SPA's
  `shaping.ts` — keep in sync, pinned by `tests/fixtures/shaping_cases.json`),
  `compose.py` (THE single composition source of truth, pinned by the golden
  parity fixture `tests/fixtures/compose_golden.json.gz` — letter-only output
  with `pen=None` stays byte-identical; declared re-baselines only),
  `widths.py` (pen models per `docs/concepts/federmodelle.md`), `fit.py` (M4),
  `word_metric.py` (the FROZEN wordbench ruler — never edited during an
  optimization run), `aggregate.py` (hand statistics H1/H2), `quality*.py`
  (per-script metrics — two scripts, two metrics, never combined),
  `eigenhand/` (the PURE half of the own-hand capture chain — frozen strip
  plan, page geometry, PDF writer, coverage, Bestand; it lives here because
  the API serves it, `docs/proposals/eigenhand-erfassung.md` §7.1),
  `database/` (SQLAlchemy models + repositories). Architecture: `docs/concepts/
  architektur.md` §3–§6; the pipeline walk-through incl. per-module roles:
  `docs/concepts/vom-scan-zum-schreiben.md`; metric rules: `docs/reference/
  qualitaetsmetrik.md`; every Fachbegriff with its module anchor:
  `docs/reference/glossar.md`.
- **`/api`** — FastAPI. Public reads are cached + gzip; admin WRITES and the
  raw single-template read are gated by `require_admin` (Cloudflare Access in
  prod, `ADMIN_TOKEN`/`X-Admin-Token` locally — the open-core moat,
  `docs/reference/quellen-und-rechte.md` §5). Renderers: `/write/glyphs` +
  `/write/word` (contract in `docs/reference/write-api.md` — anyone changing a
  `/write/*` route updates it). Occurrence/statistics/work-item routers and
  their doctrine: `docs/proposals/optimierungs-werkbank.md`. `/eigenhand/*` is
  the own-hand Bestand + Bogen printer + the stored STRIPS (bookkeeping and
  strip images — never a whole scan; the strips are admin-gated, `private,
  no-store`, never in the repo, and the private archive stays their master;
  `docs/proposals/eigenhand-erfassung.md` §7.1–§7.2, §8.1). All data lives in
  the SHARED Cloud SQL DB — local dev writes prod data.
- **`/app`** — React 19 + Vite + MUI SPA. Public: three areas (Schriftkunde ·
  Lesen · Schreiben) + landing; admin: ONE workbench in three views
  (`/admin/buchstaben` · `/uebergaenge` · `/woerter`) over one chosen Vorlage,
  plus `/admin/eigenhand` beside them (hand-scoped, not Vorlage-scoped).
  Build spec: `docs/concepts/design-system.md` (BINDING for public styling);
  stack/deploy/routes: `docs/reference/frontend-stack.md`; workbench doctrine:
  `docs/proposals/optimierungs-werkbank.md`. UI terminology is German per
  DIN/Süß lineature. Wire types in `app/src/lib/api/` are hand-synced with
  `api/schemas.py`.
- **`/alembic`** — migrations; every schema change ships as a new revision and
  passes `/verify-migrations` locally before the shared DB sees it. What each
  revision did: the revision files themselves + `CHANGELOG.md`.
- **`/data`** — sources/corpora/derived under per-source licenses; commit
  classes and rules in `docs/reference/datenablage.md` +
  `docs/reference/quellen-und-rechte.md` (see "Data & licensing" below).
- **`/infra`** — the Cloudflare configuration that would otherwise live only in
  the dashboard: `infra/cloudflare/kurrentschrift-api-proxy.js` is the Worker
  behind the admin route `kurrentschrift.ink/api/*`, and it stamps the origin
  secret itself because a Worker subrequest skips its own zone's Transform
  Rules. **The `.js` mirrors the deployed bytes** — change it and deploy it,
  change the dashboard and pull it back — so a `diff` stays meaningful.
  Settings, deploy path and the `off`/`off-seen`/`ok` measurement:
  `infra/cloudflare/README.md`.
- **Measurement tools** (`tools/`) — the bench/lab family (wordbench,
  glyphbench, tracebench, glyphlab/wordlab/pairlab, humanbench, inksight,
  routeg, inkpilot) plus the LOCAL half of the own-hand capture chain
  `tools/eigenhand` (word pool → printed Bogen sheets → scan Siebung → local
  strip store → `sync` pushes the counts up, and the strips on
  `--mit-streifen`; `sync --from <archive snapshot>` is the restore path;
  the pure compute is
  `core/eigenhand`, doctrine in `docs/proposals/eigenhand-erfassung.md`; its
  `data/samples/own-hand/` bytes stay gitignored — reserved dataset,
  backed up to the private archive): inventory + operation in
  `docs/reference/werkzeuge.md`,
  method + numbers in `docs/reference/messjournal.md` (esp. §14) and
  `docs/reference/menschliche-bewertung.md`, vocabulary in
  `docs/reference/glossar.md`. Invariants: measurement layer only — no DB
  writes, no `core/` edits from tools; **and never the reverse import —
  `core/`, `api/` and `alembic/` must not import `tools`, because the API
  image does not ship it** (pinned by `tests/test_imports.py`; a deferred
  import inside a function is the same bug, just later); frozen rulers and
  fixture roots stay frozen during optimization runs; solver comparisons pin
  BLAS threads.

**Local dev** (two steps): `uv run uvicorn
api.main:app --reload --port 8000` · `cd app && npm install --no-audit --no-fund && npm run dev`
(`/api` proxy on :3000; `.claude/commands/start.md`). **Never `alembic upgrade
head` as a setup step** — there is no local DB, so that runs DDL against the
shared Cloud SQL instance (`alembic/env.py` calls `load_dotenv()`); schema
changes ride the `kurrentschrift-migrate` job, verified first via
`/verify-migrations`. Admin writes locally need
`ADMIN_TOKEN` + matching `VITE_ADMIN_TOKEN`. Against the DEPLOYED API the
header works ONLY via `https://api.kurrentschrift.ink` (the apex 302s at the
Access edge); never create a secret version with `echo` (trailing newline).
Cloud sessions have no `.env` and no Cloud SQL egress — the deployed API is the
only admin path there; fixture roots rebuild over HTTPS via
`uv run python -m tools.wordbench.fetch_fixtures --set all --verify` — run
`uv sync --all-extras` FIRST: the verify path imports matplotlib from the
`viz` extra and fails on a fresh cloud venv without it (2026-08-21)
(details: `docs/reference/werkzeuge.md`).

**Pre-commit hooks exist** (`.pre-commit-config.yaml`, since #204): a local
ruff `check` + `format` gate running THROUGH uv, so the version is always the
one `uv.lock` pins. Install once with `uvx pre-commit install`;
`uvx pre-commit run --all-files` is the same gate on demand. ESLint and Vitest
stay deliberately CI-only. Never bypass with `--no-verify`.

## Read these before substantive work

The design is already settled in the docs; do not re-litigate decisions that have an explicit "verworfen" (rejected) section. Start at `docs/index.md`.

- `docs/concepts/vision.md` — the end-user vision (seven goals in three clusters — Writing · Reading · Research — plus Leitprinzipien and non-goals); every architecture section maps back to a vision pillar via architektur.md §1
- `docs/concepts/architektur.md` — architecture. §1 (problem split, indexes all sections), §2 (analysis-by-synthesis), §3 (library schema), §4 (ligature exception), §5 (Schwellzug vs ink + width-profile resolver), §6 (3-stage quality pipeline), §7 (the one real research risk), §8 (MVP — four gates), §9 (test words), §10 (build order, post-MVP phases P1–P5). Post-MVP sections: §11 (animation render path), §12 (style analysis pipeline), §13 (HTR integration), §14 (Lese-Lupe), §15 (print pipeline), §16 (frontend architecture), §17 (open-data export).
- `docs/concepts/mvp-roadmap.md` — actionable breakdown of §8 into Schritt 0 + M0–M7 milestones (M7 = abgespeckte animation, MVP gate 4)
- `docs/concepts/naming-und-setup.md` — repo/name/license/layout/frontend-stack/hosting decisions
- `docs/reference/kurzglossar.md` — the 77 terms that actually occur in code identifiers, this file, the skills and recent PR bodies (Duktus-Prior, Laufform, Schwellzug, `gen_chamfer`/`doff`/`dconn`, Bézier-Handle-Floor, Cusp-Connector, the Stage-A metrics M1–M4, AIoU/LDTW …), one or two sentences each. Look a term up here instead of reverse-engineering it. The FULL vocabulary with module and constant anchors stays `docs/reference/glossar.md` — read it per term, not per session; **a PR that coins a new term or metric adds its entry there in the same PR**, and adds the short entry here once the term reaches code or an agent file
- `docs/reference/sprachregelung.md` — language rules (see below)
- `docs/reference/quellen-und-rechte.md` + `docs/reference/datenablage.md` — data/licensing rules (see below)

**Reading paths per track** (token counts are tiktoken `o200k_base`, on top of the mandatory list above — take the path your diff belongs to, not the whole doc):

| Track | Read | ≈ tokens |
|---|---|---|
| Mess-Runde (`/verify-trace`) | `messjournal.md` head — Stand block + register + headline ledger, **not** the entries — · `qualitaetsmetrik.md` Stand block + §2 (frozen references) · `tintenfolger.md` Stand block + §7.11 (open arms) · `verfahren.md` | ≈ 15k, plus the route's own `verfahren-*.md` (1–6k) and the one entry you cite (2–3.5k each) |
| Glyph-Optimierung (`/optimize-glyphs`) | `qualitaetsmetrik.md` Stand block + §1 (score) + §2 (frozen references) + §3 (baseline history) + §5 (Sütterlin metric) | ≈ 8k |
| Komposition / Rendering (`core/`) | `architektur.md` Stand block + §3 (schema) + §4 (ligature exception) + §5 (Schwellzug vs ink) + §6 (quality pipeline) · `write-api.md` | ≈ 8.5k |
| Frontend (`app/`) | `design-system.md` (binding, whole) · `frontend-stack.md` Stand block + §2 (routes); + §5 (auth) when the diff touches a gate | ≈ 13k (+2k) |
| Werkbank / Auftragskorb (`/work-basket`) | `optimierungs-werkbank.md` §3 (Stufen-Doktrin) + §5 (triage duty, `resolution`) · `frontend-stack.md` §2 for the admin routes | ≈ 4.5k |
| Werkzeug bauen oder ändern | `werkzeuge.md` Stand block + the one section of that tool | ≈ 2k |
| Doku- und Repo-Pflege (`/write-docs`) | `docs/index.md` (the map) · `docs/dokument-status.md` (lifecycle + Nachzieh-Pflichten) | ≈ 6k |

**Read situatively** (only when working on the respective section):
- `docs/proposals/optimierungs-werkbank.md` — the Werkbank direction (ONE admin page: word spine + context lenses + Auftragskorb) and the BINDING stage/role doctrine: manual input only where it creates ground truth (chart ductus in the wizard, word re-tracing where the auto-fit fails, pair overrides as last resort); everything GENERATED (Laufform, join grammar, placement) gets flagged, never hand-patched. MUST-read before working off any `work_items` Auftrag — §5 defines the AI's triage duty (chart → Laufform/fit → class rule → placement → only then override), rule-fix-before-override, the `resolution` format and the "Rückgabe an Autor" path. Since W4 that protocol is enforced by the API (restate the task and say whether it reproduced BEFORE working; diagnosed stage + resolution to close), and `/work-basket` is the skill that runs it.
- `docs/proposals/tintenfolger.md` — the word-tracing campaign: the frozen reference set, routes (Kette · Lotse · InkSight · Nullprobe, display names in the glossary's „Duell-Namen"), the per-method optimization plan (§7) and the standing rescue-path register (§7.9); numbers and pre-registrations live in `messjournal.md` §14
- `docs/reference/htr-integration.md` — Transkribus API + TrOCR fallback details, PAGE-XML, free-tier logic
- `docs/reference/animation-rendering.md` — stroke-dashoffset (MVP) and Canvas-2D-stroker (post-MVP) algorithms
- `docs/reference/styleanalyse.md` — per-instance/per-hand/Hinge-feature layers, heatmap layouts
- `docs/reference/qualitaetsmetrik.md` — score/bench_loss definition, frozen-reference rule, baseline history, experiment learnings incl. verworfen items (read BEFORE any /optimize-glyphs run or metric question). Rules only: since 2026-09-04 the campaign journal §14 lives in `docs/reference/messjournal.md`. **Two metrics, one per script** (different writing instruments): §1–§4 = Kurrent/Schwellzug (`core/quality.py`, pixel/width); §5 = Sütterlin/Gleichzug naturalness (`core/quality_suetterlin.py` on `core/geometry.py` — smoothness/verticality/corner/collinearity/retrace, gated by a tolerant coverage). The bench runs ONE script per run (`--style suetterlin` default · `--style kurrent`), no combined `bench_loss`.
- `docs/reference/messjournal.md` — the campaign journal (§14, until 2026-09-04 a section of `qualitaetsmetrik.md`): 81 dated entries with every pre-registration, measurement and verdict of the Tintenfolger/Laufform rounds. Enter through the **register table** at the head — one row per entry with date, route, type · verdict and the finding in one line — and jump to the one entry you need instead of reading the file
- `docs/reference/menschliche-bewertung.md` — the method of the blind human judgement pass over the fits (`tools/humanbench`): the six-category defect taxonomy, the instrument's construction rules each next to the failure it was added for, the pre-registered analysis plan, what is kept and what is not; read it before building or evaluating a round — the findings of a round live in `messjournal.md`, not here
- `docs/reference/write-api.md` — the public render endpoints `/write/glyphs`, `/write/glyphs/{glyph_key}` + `/write/word` (shaping → composition → payload, cache behaviour, `missing` semantics); anyone changing a `/write/*` route must update it
- `docs/reference/frontend-stack.md` — React+Vite+MUI build, deploy, auth, route map
- `docs/reference/quiz-wortbank.md` — the reading-quiz word bank: sources, the pin+runtime distractor model, Fugen-marker rules, extension workflow
- `docs/reference/crawler-richtlinie.md` — who may read the site: everything is open — search, AI retrieval/citation AND training (`ai-train=yes`, decision 2026-08-28) — except Bytespider; the open-core reservation is enforced by the API's auth gate, never by robots (`tests/test_api_public_surface.py` pins the public/reserved split of every GET route; the API host's own `robots.txt` keeps the `/write` renders out of training), `app/public/robots.txt` carries the full policy (single source of truth, same shape as anyplot's), Cloudflare AI Crawl Control is the enforcement layer; crawlers get PRERENDERED pages (the nginx `$is_bot` map is anyplot's verbatim — change both files in the same breath; `app/src/lib/seo/prerender.ts` → committed `app/prerender/`, served by the API's `/seo-proxy`, guarded daily by `bot-serving-check.yml`); read before touching `robots.txt`/`llms.txt`/`nginx.conf` or answering a crawler question
- `docs/concepts/design-system.md` — the binding build spec for the public UI: colour tokens, the 19px type ladder (variants + Playfair-600 heading rule), the PageContainer width system (760/1152/1280) + Prose ~66-char reading measure, the surface rule (identity = paper, work surfaces white), navigation/IA (three areas + hubs), component inventory. Read before any public-page styling; pairs with `style-guide.md` (rationale/history).
- `docs/schriftkunde/` — source-backed script facts (lineature, Schräglage convention 90°=upright, nib types, per-script data incl. the measured Loth-1866 slant ~50° vs. 60–70° for Kurrent um 1900)

## Self-verification (feedback loops)

Every layer has a verified skill under `.claude/skills/` — the skill file is
the manual and loads when invoked; route by what the diff touches:

| Diff touches | Skill |
|---|---|
| `app/` | `/verify-frontend` |
| `api/` | `/verify-api` (read sweep + 401 probe; never authorized writes) |
| `core/`, `tests/` | `/verify-core` |
| `alembic/` | `/verify-migrations` (BEFORE the shared DB sees a revision) |
| `docs/`, `CLAUDE.md` | `/write-docs` |
| `/data`, binaries, licenses | `/audit-licenses` |
| commit/push/PR requests | `/open-pr` (mandatory routing, never hand-rolled) |
| glyph-pipeline experiments | `/optimize-glyphs` (frozen bench discipline) |
| Tintenfolger measurement rounds | `/verify-trace` (BLAS pinned, same stack but one knob; afterwards the §14 entry appended to `docs/reference/messjournal.md` — §14 is a closed section and the only one in that file — plus its register row and the ledger line) |
| Auftragskorb work | `/work-basket` (protocol enforced by the API) |
| anything that can overwrite geometry | `/dbsnapshot` (create freely, never destroy) |
| cutting a release | `/release` (fold fragments, tag the merge commit, condensed notes) |
| the weekly dependency batch | `/dependabot` (never update-branch a bot PR) |
| session retros | `/optimize-skills` |

Known gaps without a loop: admin write flows against the LIVE DB (HTTP suites
cover them on SQLite; see `admin-write-repro-harness` pattern). Dev tools
(glyphlab/wordlab/pairlab/…) are not skills — `docs/reference/werkzeuge.md`.

## Working guardrails (from session retros)

Each rule below is binding as written. The incident behind it, the recipe it
implies and the numbers that make it credible live in `.claude/guardrails.md`
— read that when you actually hit the situation, not on every turn.

- **Never commit on `main`** — branch first, even for a quick "commit and push" outside `/open-pr`.
- **A PR that finishes an issue closes it** — `Fixes #N` (or `Closes #N`) on its own line in the PR body; a bare mention closes nothing (author directive, 2026-08-16).
- **Carry a good solution straight to the sibling repo** — kurrentschrift and anyplot share stack and deploy pattern, so an asymmetry rots in the weaker one; transfer in the same round, one PR per repo (author directive, 2026-09-01).
- **Use an asymmetric finding, don't discard it** — a lopsided better:worse ratio means the losers are a decomposition task, not a rejection reason; verify base and arm are the same stack first, and get a second opinion before booking a negative (author directive, 2026-08-26).
- **The author authors in the PROD admin, so admin-UI reports are against `origin/main`** — which can be AHEAD of your branch; check for a stale tab too, cut the fix branch from `origin/main`, and never touch his authored glyphs (2026-07-25).
- **Every PR adds a changelog fragment** — `changelog.d/<slug>.md` in the CHANGELOG's own format (`changelog.d/README.md`), NEVER a new bullet in `CHANGELOG.md` (correcting the wording of one `[Unreleased]` already carries is fine — the bold title is a bullet's identity), and no bare `(#NNN)` placeholder: fill the number in or leave the reference out. The CI job „Changelog (fragment)" enforces all of it, and `uv run python -m tools.changelog check --base origin/main` is the same gate locally. Exempt: data-only commits, a `skip-changelog` label, Dependabot. Cutting a release is `/release`.
- **New terms coined by a PR get a glossary entry in the same PR** — every new Fachbegriff, metric, named failure mode or repo idiom goes into `docs/reference/glossar.md`, themed section plus alphabetical Schnellindex. Format and scope: `/write-docs` § "New terms go in the glossary".
- **Don't re-request a Copilot review after every push** — each request re-reads the whole diff and surfaces findings in untouched files; ask again only after a SUBSTANTIVE change (author, 2026-08-23).
- **Prod-touching actions need explicit in-session confirmation first** (Cloud SQL DDL/queries, Secret Manager access, Cloudflare Access policies): name the exact action, resource, and any email/secret id, and ask before acting.
- **Archive snapshots: create freely, never destroy** — take one before anything that can overwrite geometry AND after an authoring session in which letters were traced, never write into or remove an existing one, check row counts before filing, never print archive contents, and treat restoring as prod-touching (`tools/dbsnapshot`, author directive 2026-08-08; the runbook is `/dbsnapshot`).
- **Never echo secret values into the transcript** — verify by exit code or metadata.
- **Modify repo files only with the Edit/Write tools, never via Bash heredocs/sed — appending with `>>` counts.** When a command legitimately rewrites a tracked file (formatter, codegen, `git checkout`), re-read it before the next edit; a failed edit anchor means re-read and re-anchor, never a scripted rewrite (2026-08-14 and 2026-08-21 slips).
- **Manual author tasks go to Todoist** — a step only the human can do (wizard re-trace, rendering-affecting apply, bulk re-derive decision) becomes a task in the author's project **kurrentschrift**, not a line buried in a chat reply (author directive, 2026-08-07).
- **The perfect result, not the fast one** — fix the model, objective or rule rather than muting the alarm; measure a pre-registered A/B against the measured ink before adopting; an honest negative that redirects the work is a valid outcome (author directive, 2026-08-05).
- **Every rejected measure names its rescue paths** — a §14 entry closing as an honest negative names how the goal could still be reached, each with a fresh pre-registration, and `docs/proposals/tintenfolger.md` §7.9 gets its row in the same PR (author directive, 2026-08-16).
- **The author merges PRs live, and squash-merges can race your last pushes** — announce green, prefer waiting; after a race, branch from the merged main and cherry-pick, never re-push the stale branch (2026-08-16).
- **Restarting a mandated branch after its squash-merge** needs the content-neutral merge recipe when force-push is blocked — `git add -A` during an unresolved merge once committed conflict markers (2026-08-21).
- **Delegated agents and workflows run on Opus by default** — escalate to Fable only for genuine Weichenstellungen, drop to Sonnet for mechanical grinding; a delegate decides routine matters itself and returns scope changes, contradictions and frozen-ruler questions as findings (author directive, 2026-08-11, refined 2026-08-16).
- **Solver measurement runs must pin BLAS threads** (`OPENBLAS_NUM_THREADS`/`OMP_NUM_THREADS`) — the chain solve is not bit-reproducible across thread environments, so comparisons hold only within one pinned setting (2026-08-16; executable form in `/verify-trace`).
- **No AI-development disclosure on the public site** (author directive): legal/about pages carry no „KI-gestützt entwickelt" notices; strip AI credits inherited from anyplot templates.
- **Legibility over period authenticity in UI** (author Leitsatz): no broken type in navigation, headlines or body copy; historic letterforms appear only as clearly marked specimens.

## Code standards

Mirrored with `.github/copilot-instructions.md` § "Code Standards", which carries the long form.

- **Python:** type hints on every function; imports stdlib → third-party → local; comments explain WHY, never WHAT (identifiers carry that); ruff is the formatter and CI-gates both `check` and `format --check`.
- **TypeScript/React:** types over interfaces; shared constants live in `app/src/domain/glyphs.ts` (there is no `app/src/constants.ts`); **no state-management framework** — Context + local state are sufficient, so don't introduce Redux or Zustand.
- **Tests:** flat `tests/test_<module>.py`, named after the module. Prefer a pure core extracted from DB/async wrappers — those are the cheap, high-value tests; DB/HTTP-only lines are covered by the API sweep instead.
- **Codecov is a reviewer, not a hard gate:** uncovered NEW logic a unit test can reach cheaply gets a test in the same PR; lines only a live DB/HTTP flow exercises don't.
- **A `core/` PR that changes extraction, composition or rendering quotes before/after bench numbers** in its body. Standing invariants: benches never touch the DB, rulers and fixture roots stay frozen during a run, unauthored templates are reported not averaged in, an override run is its own number and never the headline, and the cross-hand Abb.-22 set (`--set abb22`) is NEVER part of a same-hand headline.
- **Never merge a PR yourself.** Open it, get it green and review-clean; merging is the author's call (he merges live). Merge only on an explicit request in the same session.
- **Never silently diverge from a settled doc.** A decision that contradicts one is written down — a `docs/proposals/` entry or an explicit `docs/concepts/` update — in the same PR.

## Language conventions (strict)

From `docs/reference/sprachregelung.md`:

- **Code (identifiers, docstrings, comments): English, no exceptions.** Including commit messages and PR descriptions.
- **README + GitHub description: English** (audience includes English-speaking genealogy).
- **Internal docs under `docs/`: German.** This is deliberate — the domain is German.
- **Website v1: German;** English follows (Vision Leitprinzip „Zweisprachig").
- **English artifacts follow the Google developer documentation style guide as a FALLBACK** (`sprachregelung.md` §4, owner decision 2026-08-18): it answers style questions the repo has no rule for; named house rules win (ISO dates, spaced dashes, narrative rationale style, untranslated German domain terms). Forward-only — never restyle-sweep existing text.

German technical terms without an established English translation get an English identifier and one explanatory comment, e.g. `width_profile  # Schwellzug: pressure-driven stroke-width modulation`.

Characters themselves are *data, not code* — schema keys stay English, but values are the actual glyphs: `{"glyph": "ſt", "variant": 0}`.

## The core architectural commitment

**Analysis-by-synthesis with a ductus prior.** The image supplies geometry + ink width; the canonical ductus template supplies stroke order and crossing resolution. A canonical template's key is `(style, glyph, variant)` — `style` is the Grundvorlage/script family (Kurrent · Sütterlin · Offenbacher; `templates.style_id`), the rest is the library unit within a style, not just glyph. Since the R2 position removal (`docs/proposals/schreibsystem-redesign.md`, migration `0017`) glyph_keys are bare base keys (`a`, `longs`, `ch`) — ONE authored form per glyph, no initial/medial/final triplication; the word position is assigned per slot by `core/shaping.py` as RENDER context only (Anstrich/Auslauf, long-vs-round s choice). Allographs (e.g. long ſ = `longs` vs. round s = `s`) are *separate glyphs* with separate ductus, not one glyph with variants. Positionally-sanctioned form variants (the "A = A" on teaching charts) are separate templates (`variant`), not parameter deviations — the positional connection strokes are *generated* from `entry`/`exit` tangents.

The closed ligature set (`ch`, `ck`, `tz`, `ſt`, `qu`, `ß` — plus `St`, the one CASED cluster: the 1922 plate writes capital S into t without a lift) are first-class library entries, not exit→entry chains. Enumerate, don't generate. Arbitrary letter pairs *are* generated from `exit`/`entry` tangents + coupling height — that's the whole point of avoiding a bigram explosion.

When in doubt about what's a glyph vs. a variant vs. a deviation, re-read `docs/concepts/architektur.md` §3 and §4.

## Data & licensing (this repo is unusual here)

Code is MIT. **Data is not covered by the code license** — each source carries its own. The `/data` tree lives outside `/core`, `/api`, `/app` precisely to keep this boundary visible.

Three commit classes, kept strictly separate (see `docs/reference/datenablage.md` §1):

1. **Committable:** `/data/sources/` (public-domain only, e.g. Loth 1866 SVG) and `/data/samples/own-hand/` (author's own copyright). Each gets a `SOURCE.md` with permalink, license, attribution, retrieval date. Exception (owner decision 2026-08-22): the own-hand STRIP SCANS stay gitignored despite the owner's copyright — they are part of the reserved dataset, backed up to the private archive; only `SOURCE.md` + `README.md` are committed (`docs/proposals/eigenhand-erfassung.md` §8).
2. **Gitignored:** `/data/corpora/` — only `SOURCE.md` + `fetch_*.py` are committed, never the data files. Pin DOI versions.
3. **Mixed:** `/data/derived/from-cc-by/` is committable; `/data/derived/from-nc-sa/` is gitignored (NC-SA collides with MIT).

Hard rules:

- **Süß' Lehrbuch and similar copyrighted works never enter the repo** — not as scans, not as redrawn glyphs, not as derived images. Bibliographic reference in prose is fine.
- A scan is not automatically free under German law (§72 UrhG). Prefer in order: own hand → explicit PD/CC0 → own photo of a PD original.
- "Script-downloaded" ≠ "license-free." The license of the bytes follows the bytes, not the fetch mechanism.
- **Copyleft word lists are server data, never repo content** (author's decision 2026-08-30): the GPL German dictionary (`data/corpora/igerman98`) lives only in the shared DB (`lesart_forms`, loaded by `tools.lesarten.sync`); `GET /lesarten?text=` answers a handful of words per request, never the list — no bytes in the repo, the image or the bundle (`docs/reference/quellen-und-rechte.md` §5).
- **The LEARNED dataset stays out of the repo (open-core moat).** The authored ductus templates, Laufformen and occurrence statistics — the DB contents — are reserved outside the MIT grant (README "License"). Technically enforced: bench fixtures stay gitignored, harvest artefacts are never committed, and the raw single-template API read is admin-gated; the public `/write` payloads are deliberate product surface under the README reservation + crawler policy. A public dataset only ever happens as a deliberate Ziel-7 release (architektur.md §17). See quellen-und-rechte.md §5 „Open-Core-Absicherung".
- Variant 0 (`v0-loth-1866`) is the canonical geometry baseline for first tests. The ductus prior is *the author's own contribution layered over* this PD geometry — Loth supplies shapes, not stroke order.

Before any data commit: *is this my expression or the expression of a protected source?* If unclear, link to the original rather than committing it.

## MVP gates

Four gates in `docs/concepts/architektur.md` §8 — stability, allograph separation, word rendering, slim animation. All four required for the kernel to count as validated; the wording and the thresholds live in §8, not here.

## Test words

`lesen` (medial ſ, repeated e, ascender, u/n confusable final n) + `das` (final s) is the §9 Pflicht-Anker pair for the MVP. See `docs/concepts/architektur.md` §9 for the full MVP word set (incl. `denen` as the generalisation target).

## Two channels, kept separate

- **Width = pressure (Schwellzug):** from `skeletonize` + `distance_transform_edt`, measured on the mask, independent of darkness. Robust to fading.
- **Darkness = ink quantity:** separate grayscale channel; carries the dip-pen refill trace. For authentic rendering, not for geometry.

Binarization is the trap: too aggressive and a faded thick downstroke disappears, the skeleton breaks, and it gets misread as a hairline. Adaptive binarization + keep the intensity channel alongside.
