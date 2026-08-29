# Copilot Instructions

This file provides guidance to GitHub Copilot (and any other AI agent that
reads `.github/copilot-instructions.md`) when working in this repository.

A companion guide `CLAUDE.md` at the repo root contains the same domain
information targeted at Claude Code. Both files MUST stay in sync — if you
change one, check the other. Both are deliberately SHORT: they say where
things live and which rules bind, while what is *true* about a subsystem
lives in the German design docs under `docs/` (start at `docs/index.md`).

---

## Important Rules

- **Language conventions (strict)** — from
  `docs/reference/sprachregelung.md`:
  - **Code (identifiers, docstrings, comments): English, no exceptions.**
    Including commit messages and PR descriptions.
  - **README + GitHub description: English** (audience includes English-
    speaking genealogy).
  - **Internal docs under `docs/`: German.** Deliberate — the domain is
    German.
  - **Website v1: German;** English follows (Vision Leitprinzip
    „Zweisprachig").
  - **English artifacts follow the Google developer documentation style
    guide as a FALLBACK** (`sprachregelung.md` §4, owner decision
    2026-08-18): it answers style questions the repo has no rule for;
    named house rules win (ISO dates, spaced dashes, narrative
    rationale style, untranslated German domain terms). Forward-only —
    never restyle-sweep existing text.
  - German technical terms without an established English translation get
    an English identifier and one explanatory comment, e.g.
    `width_profile  # Schwellzug: pressure-driven stroke-width modulation`.
  - Characters themselves are **data, not code** — schema keys stay
    English, but values are the actual glyphs:
    `{"glyph": "ſt", "variant": 0}`.
- **Do not re-litigate settled decisions.** The design docs under
  `docs/concepts/` have explicit *verworfen* (rejected) sections; do not
  propose alternatives those sections already considered and ruled out
  (OpenType fonts, blind skeleton tracing, bigram databases, SVG stroke-
  animation libraries for Schwellzug, AGPL, etc.).
- **Data is not covered by the code license.** See "Data & licensing"
  below — this is the single most error-prone area for an AI agent.

---

## Working Guardrails

These operational rules mirror `CLAUDE.md`'s guardrails and apply to any
agent working in this repo:

- **Never commit on `main`.** Branch first, even for a quick
  "commit and push". `main` is protected; land changes via a PR.
- **Every PR updates `CHANGELOG.md`** under `[Unreleased]`
  (Keep-a-Changelog categories, English, bold-titled bullets) — a PR
  without its entry is incomplete. Data-only commits (chart sources,
  authored templates) are exempt; their provenance lives in `SOURCE.md`.
  A GitHub release is that section condensed, never copied (owner rule,
  2026-08-28): same headings, one bullet per NOTABLE entry (chores,
  dependency bumps and small fixes are left out; no fixed count), at most
  two lines each — bold title, one clause, PR reference — under an intro
  line (merge count, PR range, link to the file) and over a compare link;
  the full text stays in the CHANGELOG, whose header holds the cut
  procedure.
- **New terms coined by a PR get a glossary entry in the same PR.** Any
  new Fachbegriff, metric, named failure mode or repo idiom (`gen_chamfer`,
  „Cusp-Connector“, „like-for-like Gate“) is added to
  `docs/reference/glossar.md` — themed section plus the alphabetical
  Schnellindex — so the vocabulary never outruns the place people look it
  up. Purely internal identifiers with no story stay out; the glossary is
  for terms a human meets in prose, an issue or the UI.
- **Prod-touching actions need explicit confirmation first.** Cloud SQL
  DDL/queries, Secret Manager access, and Cloudflare Access policy changes
  are not routine — name the exact action, resource, and any secret id,
  and ask before acting.
- **Never echo secret values** into logs, comments, or commits — verify by
  exit code or metadata instead.
- **Archive snapshots: create freely, never destroy** (`tools/dbsnapshot`,
  owner directive 2026-08-08). The archive holds the only copy of what no
  recomputation brings back — `bboxes` and `templates.raw_path`. Cloud
  SQL's own backups are instance-wide and keep 7 days; this project's
  failure mode is slower (a bad apply noticed weeks later).
  - Take one freely, and DO take one **before** anything that can
    overwrite geometry: `apply-laufform`, a migration with DROP/rewrite, a
    harvest with `replace`, any DDL — and after an authoring session in
    which letters were traced.
  - Every snapshot is a new timestamped directory. **Never write into an
    existing one, never delete, move or rename one** — not to tidy up, not
    when disk is short; report instead. The archive lives outside the
    working tree precisely because `git clean -xfd` deletes gitignored
    files.
  - Check plausibility before filing (row counts per table; the tool fails
    a run that would file fewer rows than the previous one). A silent
    empty snapshot is worse than none — it looks like safety.
  - Never print archive contents into logs or comments; that is the
    reserved dataset.
  - **Restoring is prod-touching** and needs explicit confirmation.
    `restore.py` is built for drills against a throwaway PostgreSQL: it
    refuses a URL equal to `DATABASE_URL`, refuses an occupied target
    without `--replace`, and writes nothing without `--apply`.
- **Do not mutate tracked files via shell heredocs/`sed`** that bypass
  normal review — appending with `>>` counts; edit through the editor.
  When a command legitimately rewrites a tracked file (formatter,
  codegen), re-read it before the next edit. A failed edit anchor
  ("string not found") means re-read and re-anchor — never fall back to a
  script-driven rewrite.
- **Manual author tasks are tracked in the owner's Todoist** (project
  "kurrentschrift", owner directive 2026-08-07): an agent that identifies a
  step only the human can do (wizard re-trace, rendering-affecting DB apply,
  bulk re-derive decision) files it there when it has Todoist access —
  otherwise it names the concrete step prominently in its summary.
- **The perfect result, not the fast one** (owner directive, 2026-08-05):
  when a cheap symptomatic fix and a correct structural fix compete, take
  the structural one — fix the model/objective/rule, never mute the alarm;
  measure with a pre-registered A/B against ground truth (the measured ink)
  before adopting; an honest negative result that redirects the work is a
  valid outcome. CPU time on offline measurement runs is not a reason to
  cut a corner.
- **Every rejected measure names its rescue paths** (owner directive,
  2026-08-16): a `qualitaetsmetrik.md` §14 entry that closes as an honest
  negative ends with the named ways it could still reach the goal (new
  mechanism, new evidence, new sensor — each with a fresh pre-registration;
  never the same knob re-run with softer gates), and the standing table
  `docs/proposals/tintenfolger.md` §7.9 gets its row in the same PR.
- **Solver measurement runs must pin BLAS threads**
  (`OPENBLAS_NUM_THREADS`/`OMP_NUM_THREADS`; finding of 2026-08-16,
  `qualitaetsmetrik.md` §14): the chain solve is not bit-reproducible across
  thread environments, so cross-run comparisons are only valid within one
  pinned setting.
- **Don't re-request a Copilot review after every push** (owner,
  2026-08-23; PR #406 collected ~15 requests in a day). Each request is a
  full re-read of the whole diff, and the bot then surfaces „previously
  missed" findings in files the push never touched — a one-line docstring
  fix draws a finding elsewhere, which draws another push, which draws
  another request. Request a fresh review only after a SUBSTANTIVE change
  (new behaviour, a reworked mechanism), and stop once a round yields no
  new inline comments but only carried-over suppressed items. A PR that is
  green with no open threads needs no further round.
- **No AI-development disclosure on the public site** (owner directive):
  legal/about pages carry no „KI-gestützt entwickelt" notices.
- **Legibility over period authenticity in UI** (owner Leitsatz): no broken
  type in navigation, headlines or body copy; historic letterforms appear
  only as clearly marked specimens.
- **Claude Code sessions** additionally route work through verified skills
  under `.claude/skills/`; Copilot can't invoke those, but the same gates
  apply manually (see "GitHub Workflow" → "Verification before a PR").

---

## Task Suitability

**Good tasks for Copilot in this repo:**

- Frontend feature work that follows the existing `/app/` patterns
  (drag-on-canvas, stylus capture, diagnostic panels).
- New FastAPI routes that mirror the `api/routers/{health,styles,hands,
  sources,chart,bboxes,templates,pairs,instances,aggregates,write,
  word_samples,work_items,quiz_words}.py` shape.
- Adding numpy/scipy/scikit-image pipeline steps inside `core/`.
- Writing/improving unit tests under `tests/` (a pytest suite already
  exists — mirror the existing flat `tests/test_<module>.py` layout).
- Refactors within established patterns.
- Updating documentation under `docs/` (mind the German/English split).
- Fixing ruff / TypeScript / ESLint findings.

**Tasks requiring human review:**

- Schema migrations in `alembic/versions/` (touch the Postgres source of
  truth — author them, then ask before applying).
- Changes to the ductus prior or analysis-by-synthesis core logic
  (`core/template.py`, `core/pipeline.py`) — that's the research kernel
  (§7).
- Anything touching `/data/` — licensing implications.
- Authentication and admin-route configuration.
- Pricing/quota logic for the HTR free-tier (§13).

**How to iterate:**

- Before acting on a `work_items` task (the admin's Auftragskorb): read
  `docs/proposals/optimierungs-werkbank.md` — its stage/role doctrine is
  binding (triage the pipeline stage first; rule-fix before override;
  manual input only where it creates ground truth). §5 is a protocol the
  API enforces: reproduce the complaint and PATCH `status: ack` with your
  own restatement (`understanding` + `reproduced`) before changing
  anything, then close with `stage` + `resolution` — an incomplete close
  returns 422. The queue is source-free: `GET /work-items?status=open`.
- Use `@copilot` in PR comments with specific, actionable feedback.
- Reference doc sections by number (e.g. „architektur.md §3") rather than
  copying prose — the docs are the source of truth.
- Link to relevant `docs/reference/*.md` files for technical specs.

---

## Project Overview

**kurrentschrift** is a modern toolkit for the German Kurrent script
(pre-1900 normed handwriting): one web app at
[kurrentschrift.ink](https://kurrentschrift.ink) pursuing seven goals in
three pillars —

- **Writing** — onboarding (history in two sentences, alphabet table,
  reading and writing rules) · content-aware practice sheets (configurable
  lineature ratios, arbitrary input text, printable PDFs) · animated letter
  tables with stroke order and pressure build-up (true Schwellzug).
- **Reading** — modern text rendered in a trained Kurrent hand · reading
  help for historical texts via HTR (Transkribus default, TrOCR fallback),
  extended by the **Lese-Lupe**: click a confusing letter, get a structured
  explanation referencing orthography rules.
- **Research** — style analysis (slant, swell, transition angles, per-glyph
  cluster spread) with three follow-on paths (optimise, new-style-as-basis,
  hand comparison) · open data as a citable Zenodo release.

Bilingual DE/EN is a cross-cutting guiding principle (German first; English
follows). The full vision is in `docs/concepts/vision.md` (seven goals,
three pillars), the settled architecture in
`docs/concepts/architektur.md` (§1–§17). **Read those two before
substantive work.**

### The core architectural commitment

**Analysis-by-synthesis with a ductus prior.** The image supplies geometry
+ ink width; the canonical ductus template supplies stroke order and
crossing resolution. A canonical template's key is `(style, glyph,
variant)` — `style` is the Grundvorlage/script family (Kurrent ·
Sütterlin · Offenbacher), the rest is the library unit within a style, not
just glyph. Since the R2 position removal (schreibsystem-redesign.md,
migration 0017) glyph_keys are bare base keys (`a`, `longs`, `ch`) — ONE
authored form per glyph, no initial/medial/final triplication; the word
position is per-slot RENDER context from `core/shaping.py` (Anstrich/
Auslauf, long-vs-round s). Allographs (long ſ = `longs` vs. round s = `s`)
are *separate glyphs* with separate ductus, not one glyph with variants.
Positionally-sanctioned form variants (the "A = A" on teaching charts) are
separate templates (`variant`), not parameter deviations; positional
connection strokes are *generated* from `entry`/`exit` tangents.

The closed ligature set (`ch`, `ck`, `tz`, `ſt`, `qu`, `ß`) are first-
class library entries, not exit→entry chains. Enumerate, don't generate.
Arbitrary letter pairs *are* generated from `exit`/`entry` tangents +
coupling height — that's the whole point of avoiding a bigram explosion.

When in doubt about what's a glyph vs. a variant vs. a deviation, re-read
`docs/concepts/architektur.md` §3 and §4.

---

## Repository Layout

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
  passes the migrations gate locally before the shared DB sees it. What each
  revision did: the revision files themselves + `CHANGELOG.md`.
- **`/data`** — sources/corpora/derived under per-source licenses; commit
  classes and rules in `docs/reference/datenablage.md` +
  `docs/reference/quellen-und-rechte.md` (see "Data & licensing" below).
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
  method + numbers in `docs/reference/qualitaetsmetrik.md` (esp. §14) and
  `docs/reference/menschliche-bewertung.md`, vocabulary in
  `docs/reference/glossar.md`. Invariants: measurement layer only — no DB
  writes, no `core/` edits from tools; **and never the reverse import —
  `core/`, `api/` and `alembic/` must not import `tools`, because the API
  image does not ship it** (pinned by `tests/test_imports.py`; a deferred
  import inside a function is the same bug, just later); frozen rulers and
  fixture roots stay frozen during optimization runs; solver comparisons pin
  BLAS threads.

Beside those: `tests/` (the flat CI pytest suite, see "Testing Standards"),
`docs/` (the German design docs — the layer taxonomy concepts · reference ·
schriftkunde · proposals · research · notes is explained at the top of
`docs/index.md`), and `.github/` (this file + the CI workflows).

---

## Development Setup

Three steps (see `.claude/commands/start.md` for the slash command):

```bash
# Schema (run once or after migrations)
uv run alembic upgrade head

# Backend on :8000
uv run uvicorn api.main:app --reload --port 8000

# Frontend on :3000 with /api proxy to :8000
cd app && npm install && npm run dev
```

Python package manager: **uv**. Frontend: **npm** (note: anyplot uses
yarn, kurrentschrift uses npm — `package-lock.json` is checked in).

Admin writes locally need `ADMIN_TOKEN` for the API + a matching
`VITE_ADMIN_TOKEN` in `app/.env` so the SPA sends `X-Admin-Token` (without
it, local saves return 401). Against the DEPLOYED API the header works
ONLY via `https://api.kurrentschrift.ink` (the apex `/api/*` 302s at the
Cloudflare Access edge before the header reaches Cloud Run); never create a
secret version with `echo` (the trailing newline no header can carry made
the gate reject every value for two months). Cloud sessions have no `.env`
and no Cloud SQL egress — the deployed API is the only admin path there;
the gitignored wordbench fixture roots rebuild over HTTPS via
`uv run python -m tools.wordbench.fetch_fixtures --set all --verify` —
run `uv sync --all-extras` first: the verify path imports matplotlib from
the `viz` extra and fails with `ModuleNotFoundError` on a fresh cloud venv
without it (details: `docs/reference/frontend-stack.md` and
`docs/reference/werkzeuge.md`).

`http://localhost:3000/admin` opens the workbench: first the Vorlage
picker, then the three views. UI labels are German per DIN/Süß lineature
(Grundlinie · Mittellinie · Oberlinie · Unterlinie; zones Oberlänge ·
Mittellänge · Unterlänge).

---

## Code Standards

### Python Style

- **Linter/Formatter**: Ruff — configured in `pyproject.toml` and CI-gated
  (`ruff check` + `ruff format --check` run on every PR).
- **Type hints**: required for all functions.
- **Docstrings**: explanatory line for non-obvious functions; identifiers
  carry most of the meaning.
- **Import order**: standard library → third-party → local.
- **No comments narrating WHAT**; well-named identifiers do that. Comments
  explain WHY when it's non-obvious (invariant, workaround, surprising
  behavior).

### TypeScript / React Style

- React 19 functional components with hooks.
- MUI 9 + Emotion for styling.
- Types over interfaces by default.
- `app/src/domain/glyphs.ts` is the canonical place for shared constants
  (the `Position` type, `POSITIONS`, the `LETTERS` registry and the
  `KNOWN_GLYPHS` list). There is no `app/src/constants.ts`.
- Do not introduce a state-management framework (Redux/Zustand) — Context
  + local state are sufficient for our use cases.

### Database Schema (Postgres + SQLAlchemy async)

Tables: `styles`, `hands`, `sources`, `bboxes`, `templates`, `glyph_pairs`,
`instances`, `pair_instances`, `word_instances`, `aggregates`,
`pair_aggregates`, `work_items`, `quiz_words`. What each one holds and why:
`docs/concepts/architektur.md` §3 + §12 (canonical templates vs.
per-occurrence instances vs. per-hand aggregates),
`docs/proposals/handmodell-stufenplan.md` (the H1/H2 statistics layers),
`docs/proposals/optimierungs-werkbank.md` §5 (the `work_items` Auftragskorb
and its enforced `stage`/`resolution` protocol),
`docs/reference/quiz-wortbank.md` (the reading-quiz word bank) — and
`docs/reference/glossar.md` for a single term.

Binding when you touch the schema:

- `styles` is the Grundvorlage/script family (Kurrent · Sütterlin ·
  Offenbacher); it carries `width_resolver` (§5) + lineature defaults. The
  resolver is applied at RENDER time by
  `core/widths.py::resolve_half_widths` (`pressure` = measured Schwellzug,
  `constant` = Sütterlin Gleichzug, `broad_nib` = widths regenerated from
  the `BroadNib` model; see `docs/concepts/federmodelle.md`); stored
  `half_widths` always stay the measurement.
- `templates` carry **two** unique constraints since migration `0017`:
  `(style_id, glyph, variant)` (the library tuple, architektur.md §3)
  **and** `(style_id, glyph_key, variant)` — every read keys on
  `glyph_key`, so it is identifying too. The API's 409 backstops are UX on
  top of the DB constraints, not the only defense.
- JSONB columns hold the structured payloads (anchors, half widths, mask
  strokes, measurements); aggregate statistics are computed in SQL.
- Every schema change ships as a new Alembic revision and is verified
  against a throwaway Postgres before the shared Cloud SQL DB sees it.

### Testing Standards

- A pytest suite already exists under `tests/` (flat layout —
  `tests/test_<module>.py`, e.g. `tests/test_tri_script.py`,
  plus `conftest.py` and `tests/fixtures/`). It runs in CI on every PR.
- Add new tests in the same flat layout; name a module's tests after the
  module.
- Prefer pure, deterministic core logic (extract a pure core from
  DB/async wrappers where needed) — those are the cheap, high-value
  tests. DB/HTTP-only lines are covered by the API verification sweep.
- Use pytest fixtures; the compose golden fixture
  (`tests/fixtures/compose_golden.json.gz`) pins `core/compose.py` output.
- Frontend unit tests run via **Vitest** (`npm run test` in `app/`,
  CI-gated since PR #198): `app/src/domain/shaping.test.ts` pins the
  `shaping.ts` ↔ `core/shaping.py` twin against the shared fixture
  `tests/fixtures/shaping_cases.json` (the Python side asserts the same
  fixture in `tests/test_tri_script.py`).

---

## Read These Before Substantive Work

The design is already settled in the docs; do not re-litigate decisions that have an explicit "verworfen" (rejected) section. Start at `docs/index.md`.

- `docs/concepts/vision.md` — the end-user vision (seven goals in three clusters — Writing · Reading · Research — plus Leitprinzipien and non-goals); every architecture section maps back to a vision pillar via architektur.md §1
- `docs/concepts/architektur.md` — architecture. §1 (problem split, indexes all sections), §2 (analysis-by-synthesis), §3 (library schema), §4 (ligature exception), §5 (Schwellzug vs ink + width-profile resolver), §6 (3-stage quality pipeline), §7 (the one real research risk), §8 (MVP — four gates), §9 (test words), §10 (build order, post-MVP phases P1–P5). Post-MVP sections: §11 (animation render path), §12 (style analysis pipeline), §13 (HTR integration), §14 (Lese-Lupe), §15 (print pipeline), §16 (frontend architecture), §17 (open-data export).
- `docs/concepts/mvp-roadmap.md` — actionable breakdown of §8 into Schritt 0 + M0–M7 milestones (M7 = abgespeckte animation, MVP gate 4)
- `docs/concepts/naming-und-setup.md` — repo/name/license/layout/frontend-stack/hosting decisions
- `docs/reference/glossar.md` — the project vocabulary: every Fachbegriff and repo idiom from the docs/issues/UI (Duktus-Prior, Laufform, Schwellzug, `gen_chamfer`/`doff`/`dconn`, Bézier-Handle-Floor, Cusp-Connector, the Stage-A metrics M1–M4, AIoU/LDTW …) with a plain-language explanation plus the module/constant anchor to dig deeper. Look a term up here instead of reverse-engineering it; **a PR that coins a new term or metric adds its entry in the same PR**
- `docs/reference/sprachregelung.md` — language rules (see below)
- `docs/reference/quellen-und-rechte.md` + `docs/reference/datenablage.md` — data/licensing rules (see below)

**Read situatively** (only when working on the respective section):
- `docs/proposals/optimierungs-werkbank.md` — the Werkbank direction (ONE admin page: word spine + context lenses + Auftragskorb) and the BINDING stage/role doctrine: manual input only where it creates ground truth (chart ductus in the wizard, word re-tracing where the auto-fit fails, pair overrides as last resort); everything GENERATED (Laufform, join grammar, placement) gets flagged, never hand-patched. MUST-read before working off any `work_items` Auftrag — §5 defines the AI's triage duty (chart → Laufform/fit → class rule → placement → only then override), rule-fix-before-override, the `resolution` format and the "Rückgabe an Autor" path. Since W4 that protocol is enforced by the API (restate the task and say whether it reproduced BEFORE working; diagnosed stage + resolution to close).
- `docs/proposals/tintenfolger.md` — the word-tracing campaign: the frozen reference set, routes (Kette · Lotse · InkSight · Nullprobe, display names in the glossary's „Duell-Namen"), the per-method optimization plan (§7) and the standing rescue-path register (§7.9); numbers and pre-registrations live in `qualitaetsmetrik.md` §14
- `docs/reference/htr-integration.md` — Transkribus API + TrOCR fallback details, PAGE-XML, free-tier logic
- `docs/reference/animation-rendering.md` — stroke-dashoffset (MVP) and Canvas-2D-stroker (post-MVP) algorithms
- `docs/reference/styleanalyse.md` — per-instance/per-hand/Hinge-feature layers, heatmap layouts
- `docs/reference/qualitaetsmetrik.md` — score/bench_loss definition, frozen-reference rule, baseline history, experiment learnings incl. verworfen items (read BEFORE any bench run or metric question). **Two metrics, one per script** (different writing instruments): §1–§4 = Kurrent/Schwellzug (`core/quality.py`, pixel/width); §5 = Sütterlin/Gleichzug naturalness (`core/quality_suetterlin.py` on `core/geometry.py` — smoothness/verticality/corner/collinearity/retrace, gated by a tolerant coverage). The bench runs ONE script per run (`--style suetterlin` default · `--style kurrent`), no combined `bench_loss`.
- `docs/reference/menschliche-bewertung.md` — the method of the blind human judgement pass over the fits (`tools/humanbench`): the six-category defect taxonomy, the instrument's construction rules each next to the failure it was added for, the pre-registered analysis plan, what is kept and what is not; read it before building or evaluating a round — the findings of a round live in `qualitaetsmetrik.md`, not here
- `docs/reference/write-api.md` — the public render endpoints `/write/glyphs`, `/write/glyphs/{glyph_key}` + `/write/word` (shaping → composition → payload, cache behaviour, `missing` semantics); anyone changing a `/write/*` route must update it
- `docs/reference/quiz-wortbank.md` — the reading-quiz word bank: sources, the pin+runtime distractor model, Fugen-marker rules, extension workflow
- `docs/reference/frontend-stack.md` — React+Vite+MUI build, deploy, auth, route map
- `docs/reference/crawler-richtlinie.md` — who may read the site: everything is open — search, AI retrieval/citation AND training (`ai-train=yes`, decision 2026-08-28) — except Bytespider; the open-core reservation is enforced by the API's auth gate, never by robots (`tests/test_api_public_surface.py` pins the public/reserved split of every GET route; the API host's own `robots.txt` keeps the `/write` renders out of training), `app/public/robots.txt` carries the full policy (single source of truth, same shape as anyplot's), Cloudflare AI Crawl Control is the enforcement layer; crawlers get PRERENDERED pages (the nginx `$is_bot` map is anyplot's verbatim — change both files in the same breath; `app/src/lib/seo/prerender.ts` → committed `app/prerender/`, served by the API's `/seo-proxy`, guarded daily by `bot-serving-check.yml`); read before touching `robots.txt`/`llms.txt`/`nginx.conf` or answering a crawler question
- `docs/concepts/design-system.md` — the binding build spec for the public UI: colour tokens, the 19px type ladder (variants + Playfair-600 heading rule), the PageContainer width system (760/1152/1280) + Prose ~66-char reading measure, the surface rule (identity = paper, work surfaces white), navigation/IA (three areas + hubs), component inventory. Read before any public-page styling; pairs with `style-guide.md` (rationale/history).
- `docs/schriftkunde/` — source-backed script facts (lineature, Schräglage convention 90°=upright, nib types, per-script data incl. the measured Loth-1866 slant ~50° vs. 60–70° for Kurrent um 1900)

---

## Test Words

`lesen` (medial ſ, repeated `e`, ascender, u/n confusable final `n`) +
`das` (final `s`) is the Pflicht-Anker pair for the MVP. The full MVP
word set:

```
lesen · das · den · lese · lasen · als · dann
```

Generalisation target (not written, rendered from aggregated stats):
`denen`. See `docs/concepts/architektur.md` §9.

---

## Two Channels, Kept Separate

- **Width = pressure (Schwellzug):** from `skeletonize` +
  `distance_transform_edt`, measured on the mask, independent of darkness.
  Robust to fading.
- **Darkness = ink quantity:** separate grayscale channel; carries the
  dip-pen refill trace. For authentic rendering, not for geometry.

Binarisation is the trap: too aggressive and a faded thick downstroke
disappears, the skeleton breaks, and it gets misread as a hairline.
Adaptive binarisation + keep the intensity channel alongside.

---

## Data & Licensing (this repo is unusual here)

Code is **MIT**. **Data is not covered by the code license** — each
source carries its own. The `/data` tree lives outside `/core`, `/api`,
`/app` precisely to keep this boundary visible.

Three commit classes, kept strictly separate (see
`docs/reference/datenablage.md` §1):

1. **Committable:** `/data/sources/` (public-domain only, e.g. Loth 1866
   SVG; `/data/sources/suetterlin-leitfaden-1926/` archives 22 PD-marked pages
   of the SUB-Hamburg Leitfaden full digitization — hands-gallery
   cross-hand material, never a same-hand bench reference) and
   `/data/samples/own-hand/` (author's own copyright). Each gets
   a `SOURCE.md` with permalink, license, attribution, retrieval date.
   Exception (owner decision 2026-08-22): the own-hand STRIP SCANS stay
   gitignored despite the owner's copyright — reserved dataset, backed up
   to the private archive; only `SOURCE.md` + `README.md` are committed
   (`docs/proposals/eigenhand-erfassung.md` §8).
2. **Gitignored:** `/data/corpora/` — only `SOURCE.md` + `fetch_corpus.py`
   are committed, never the data files. Pin DOI versions.
3. **Mixed:** `/data/derived/from-cc-by/` is committable;
   `/data/derived/from-nc-sa/` is gitignored (NC-SA collides with MIT).

Hard rules:

- **Süß' Lehrbuch and similar copyrighted works never enter the repo** —
  not as scans, not as redrawn glyphs, not as derived images. Bibliographic
  reference in prose is fine.
- A scan is not automatically free under German law (§72 UrhG). Prefer in
  order: own hand → explicit PD/CC0 → own photo of a PD original.
- "Script-downloaded" ≠ "license-free." The license of the bytes follows
  the bytes, not the fetch mechanism.
- **The LEARNED dataset stays out of the repo (open-core moat).** The
  authored ductus templates, Laufformen and occurrence statistics — the DB
  contents — are reserved outside the MIT grant (README "License").
  Technically enforced: bench fixtures stay gitignored, harvest artefacts
  are never committed, the raw single-template API GET is admin-gated; the
  public `/write` payloads are deliberate product surface under the README
  reservation + crawler policy. A public dataset only ever happens as a
  deliberate goal-7 release. See quellen-und-rechte.md §5.
- Variant 0 (`v0-loth-1866`) is the canonical geometry baseline for first
  tests. The ductus prior is *the author's own contribution layered over*
  this PD geometry — Loth supplies shapes, not stroke order.

Before any data commit: *is this my expression or the expression of a
protected source?* If unclear, link to the original rather than committing
it.

---

## Tech Stack (today + planned)

- **Backend:** Python 3.13+, FastAPI, SQLAlchemy async, asyncpg, Postgres,
  uv (package manager).
- **Pipeline:** numpy, scipy, scikit-image, Pillow.
- **Frontend:** React 19, TypeScript 6, Vite 8 (with SWC plugin), MUI 9,
  React Router 7, npm.
- **Planned additions (post-MVP):** `react-helmet-async` (SEO),
  `react-i18next` (DE/EN), WeasyPrint (PDF), httpx (Transkribus client),
  optionally TrOCR via HuggingFace Transformers for self-hosted HTR.
- **Linting/Testing:** ruff (Python) is configured and CI-gated. The SPA
  has a flat ESLint config (`app/eslint.config.js`: JS + typescript-eslint
  recommended + react-hooks); `npm run lint`, `npm run test` (Vitest —
  the shaping-twin fixture test) and the type-check (`tsc` via
  `npm run build`) all run in CI.

---

## Deployment (live since May 2026)

The project runs on **Google Cloud Platform** (own GCP project, same
pattern as anyplot.ai), live since 2026-05 — authoritative spec:
`docs/reference/frontend-stack.md` §6. Two Cloud Run services in
europe-west4. Since 2026-08-30 the API runs with **min instances 1** (its
measured cold start is p50 9.4 s, not the ~3 s once assumed, and 60 % of
hours see no request at all); the app stays at 0 because it boots in
170 ms:

- `kurrentschrift-api` — FastAPI (`api/Dockerfile`); `api/cloudbuild.yaml`
  runs an Alembic migrate job (`kurrentschrift-migrate`) before rollout,
  deploys `--no-traffic`, smokes the candidate revision and only then
  promotes traffic. Serves api.kurrentschrift.ink.
- `kurrentschrift-app` — the static Vite build behind nginx-unprivileged
  (`app/Dockerfile` + `app/cloudbuild.yaml`). Serves kurrentschrift.ink.

Postgres is the `kurrentschrift` DB on anyplot's Cloud SQL instance — the
SAME DB local dev writes. Cloudflare Access gates `/admin/*` (Google
identity) and a Cloudflare Worker in front of the app routes `/api/*` to
api.kurrentschrift.ink (nginx in the app container knows no `/api`). One
Cloud Build trigger per service, deploying from `main`.

---

## GitHub Workflow

CI runs on every PR via `.github/workflows/ci.yml`: a backend job
(ruff lint + `ruff format --check` + pytest with Codecov upload), a
frontend job (`npm run lint`, then `npm run test` — the Vitest
shaping-twin fixture run — then `npm run build`, i.e. ESLint + Vitest +
`tsc && vite build`), and a migrations job (`alembic upgrade head` +
`alembic check` + a downgrade/upgrade roundtrip against a throwaway
Postgres 16 service, so a broken or drifting revision never reaches the
shared Cloud SQL instance). There are no anyplot-style spec-create /
impl-generate pipelines. Conventions:

- **Issues** are welcome for design discussion (pre-MVP this is the main
  contribution channel — see `docs/contributing.md`).
- **PRs** should reference the relevant `docs/concepts/architektur.md`
  section and any `docs/reference/*.md` they touch.
- **Branch policy:** main is protected; feature branches with PRs.
- **Commit messages:** English, focused on WHY, conventional-commit prefix
  optional (`docs:`, `feat:`, `fix:`, `refactor:`).
- **Changelog:** every PR adds its entries to `CHANGELOG.md` under
  `[Unreleased]` (Keep-a-Changelog categories, English, bold-titled
  bullets like the existing entries) — that file is how releases get
  posted; a PR without its entry is incomplete. Data-only commits
  (chart sources, authored templates) are exempt — provenance lives in
  their `SOURCE.md`. A GitHub release is the section condensed, never
  copied: same headings, one bullet per notable entry (chores and small
  fixes left out, no fixed count), at most two lines each (bold title,
  one clause, PR reference), intro line + compare link.
- **Codecov:** the bot comments the patch coverage on every PR (backend
  only). Treat it like a reviewer, not a hard gate: uncovered NEW logic
  that a unit test can reach cheaply gets a test in the same PR
  (prefer extracting a pure core from DB/async wrappers); lines only a
  live DB/HTTP flow exercises are covered by the API verification
  sweep instead.
- **Pre-commit hooks:** none configured yet — when added, do not bypass
  with `--no-verify`.
- **Glyph- and word-pipeline changes are benchmarked:** a PR touching
  `core/` extraction, composition or rendering quotes before/after bench
  numbers. `tools/glyphbench` scores every authored glyph against frozen
  references, ONE script per run (`uv run python -m tools.glyphbench.run
  --style suetterlin|kurrent`, headline `bench_loss:` — lower is better).
  One level up, `tools/wordbench` scores COMPOSED words (placement +
  Übergänge from `core/shaping.py` + `core/compose.py`) against frozen
  same-hand word specimens, with the letter-pair joins as their own set
  and their own `pair_loss:` headline (`uv run python -m
  tools.wordbench.run --style suetterlin [--set words|pairs|all]`).
  Standing invariants: the benches never touch the DB (fixtures exported
  once, read-only), the rulers and fixture roots stay FROZEN during a run
  (edit the composer, never the ruler), unauthored templates are skipped
  and reported rather than averaged in, an override run is its own number
  and never the headline, and the CROSS-HAND Abb.-22 Schülerschrift set
  (`--set abb22`) tracks generalisation and is NEVER part of a same-hand
  headline. Inventory and operation of the whole bench/lab family:
  `docs/reference/werkzeuge.md`; method, pre-registrations and numbers:
  `docs/reference/qualitaetsmetrik.md` (esp. §11–§14) and
  `docs/reference/menschliche-bewertung.md`.
- **Never merge a PR yourself** — open it, get it green and
  review-clean (address Copilot review comments, then resolve the
  threads); merging is the maintainer's call.

### Verification before a PR

Run the local CI equivalents first — `uv run --extra test pytest`,
`uv run --extra dev ruff check .`, `uv run --extra dev ruff format --check
.`, plus `npm run lint`, `npm run test` and `npm run build` in `app/` when
the frontend changed. The pipeline should never fail on tests or lint.

The maintainer's Claude Code sessions encode the same gates as verified
skills under `.claude/skills/`, routed by what the diff touches. Copilot
cannot invoke them, but the gate each one stands for still applies:

| Diff touches | Skill (Claude Code) — the gate it stands for |
|---|---|
| `app/` | `/verify-frontend` — drive the touched flows, console/network clean, desktop AND mobile viewport |
| `api/` | `/verify-api` — read sweep + 401 probe; never authorized writes |
| `core/`, `tests/` | `/verify-core` — pytest + ruff + a direct pipeline smoke |
| `alembic/` | `/verify-migrations` — the full chain against a throwaway Postgres BEFORE the shared DB sees a revision |
| `docs/`, `CLAUDE.md`, this file | `/write-docs` — docs conventions + the CLAUDE.md ↔ copilot-instructions sync |
| `/data`, binaries, licenses | `/audit-licenses` — provenance battery |
| commit/push/PR requests | `/open-pr` — the local gates, then CI + review to green |
| glyph-pipeline experiments | `/optimize-glyphs` — frozen bench discipline |
| Auftragskorb work | `/work-basket` — the protocol the API enforces |
| session retros | `/optimize-skills` — recurring friction folded back into the skills |

Known gaps without a loop: admin write flows against the LIVE DB (the HTTP
suites cover them on SQLite; a live write would mutate shared data).

---

## Acceptance Criteria

Before completing any task:

1. Code conforms to the language conventions above (English identifiers
   and comments, no exceptions).
2. Type hints / TS types are included for all new functions and
   components.
3. New decisions that contradict an existing doc are documented either as
   a `docs/proposals/` entry or via an explicit `docs/concepts/` update —
   **don't silently diverge** from settled docs.
4. Data changes follow the three-commit-classes rule. No copyrighted
   source bytes enter the repo.
5. If you add/change a public API route, update `api/schemas.py` and any
   `docs/reference/*.md` that describes it (a `/write/*` route always
   updates `docs/reference/write-api.md`).
6. If you change frontend routing or the auth shape, update
   `docs/reference/frontend-stack.md`.

---

## Getting Help

- **Documentation:** start at `docs/index.md`.
- **Code patterns:** the `app/src/sections/admin/setup-wizard/` tree
  (e.g. `WizardCanvas.tsx` + `useWizard.ts`) shows the canonical pattern
  for an interactive stylus/guide tool; `core/pipeline.py` shows the
  pipeline composition pattern.
- **Sibling AI guide:** `CLAUDE.md` (this file's twin for Claude Code).
- **Vision-to-architecture mapping:** `docs/concepts/architektur.md` §1
  is the index — every Vision pillar points to a specific architecture
  section.
