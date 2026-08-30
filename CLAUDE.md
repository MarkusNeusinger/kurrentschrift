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

**Local dev** (three steps): `uv run alembic upgrade head` · `uv run uvicorn
api.main:app --reload --port 8000` · `cd app && npm install && npm run dev`
(`/api` proxy on :3000; `.claude/commands/start.md`). Admin writes locally need
`ADMIN_TOKEN` + matching `VITE_ADMIN_TOKEN`. Against the DEPLOYED API the
header works ONLY via `https://api.kurrentschrift.ink` (the apex 302s at the
Access edge); never create a secret version with `echo` (trailing newline).
Cloud sessions have no `.env` and no Cloud SQL egress — the deployed API is the
only admin path there; fixture roots rebuild over HTTPS via
`uv run python -m tools.wordbench.fetch_fixtures --set all --verify` — run
`uv sync --all-extras` FIRST: the verify path imports matplotlib from the
`viz` extra and fails on a fresh cloud venv without it (2026-08-21)
(details: `docs/reference/werkzeuge.md`).

## Read these before substantive work

The design is already settled in the docs; do not re-litigate decisions that have an explicit "verworfen" (rejected) section. Start at `docs/index.md`.

- `docs/concepts/vision.md` — the end-user vision (seven goals in three clusters — Writing · Reading · Research — plus Leitprinzipien and non-goals); every architecture section maps back to a vision pillar via architektur.md §1
- `docs/concepts/architektur.md` — architecture. §1 (problem split, indexes all sections), §2 (analysis-by-synthesis), §3 (library schema), §4 (ligature exception), §5 (Schwellzug vs ink + width-profile resolver), §6 (3-stage quality pipeline), §7 (the one real research risk), §8 (MVP — four gates), §9 (test words), §10 (build order, post-MVP phases P1–P5). Post-MVP sections: §11 (animation render path), §12 (style analysis pipeline), §13 (HTR integration), §14 (Lese-Lupe), §15 (print pipeline), §16 (frontend architecture), §17 (open-data export).
- `docs/concepts/mvp-roadmap.md` — actionable breakdown of §8 into Schritt 0 + M0–M7 milestones (M7 = abgespeckte animation, MVP gate 4)
- `docs/concepts/naming-und-setup.md` — repo/name/license/layout/frontend-stack/hosting decisions
- `docs/reference/glossar.md` — the project vocabulary: every Fachbegriff and repo idiom from the docs/issues/UI (Duktus-Prior, Laufform, Schwellzug, `gen_chamfer`/`doff`/`dconn`, Bézier-Handle-Floor, Cusp-Connector, the Stage-A metrics M1–M4, AIoU/LDTW …) with a plain-language explanation plus the module/constant anchor to dig deeper. Look a term up here instead of reverse-engineering it; **a PR that coins a new term or metric adds its entry in the same PR**
- `docs/reference/sprachregelung.md` — language rules (see below)
- `docs/reference/quellen-und-rechte.md` + `docs/reference/datenablage.md` — data/licensing rules (see below)

**Read situatively** (only when working on the respective section):
- `docs/proposals/optimierungs-werkbank.md` — the Werkbank direction (ONE admin page: word spine + context lenses + Auftragskorb) and the BINDING stage/role doctrine: manual input only where it creates ground truth (chart ductus in the wizard, word re-tracing where the auto-fit fails, pair overrides as last resort); everything GENERATED (Laufform, join grammar, placement) gets flagged, never hand-patched. MUST-read before working off any `work_items` Auftrag — §5 defines the AI's triage duty (chart → Laufform/fit → class rule → placement → only then override), rule-fix-before-override, the `resolution` format and the "Rückgabe an Autor" path. Since W4 that protocol is enforced by the API (restate the task and say whether it reproduced BEFORE working; diagnosed stage + resolution to close), and `/work-basket` is the skill that runs it.
- `docs/proposals/tintenfolger.md` — the word-tracing campaign: the frozen reference set, routes (Kette · Lotse · InkSight · Nullprobe, display names in the glossary's „Duell-Namen"), the per-method optimization plan (§7) and the standing rescue-path register (§7.9); numbers and pre-registrations live in `qualitaetsmetrik.md` §14
- `docs/reference/htr-integration.md` — Transkribus API + TrOCR fallback details, PAGE-XML, free-tier logic
- `docs/reference/animation-rendering.md` — stroke-dashoffset (MVP) and Canvas-2D-stroker (post-MVP) algorithms
- `docs/reference/styleanalyse.md` — per-instance/per-hand/Hinge-feature layers, heatmap layouts
- `docs/reference/qualitaetsmetrik.md` — score/bench_loss definition, frozen-reference rule, baseline history, experiment learnings incl. verworfen items (read BEFORE any /optimize-glyphs run or metric question). **Two metrics, one per script** (different writing instruments): §1–§4 = Kurrent/Schwellzug (`core/quality.py`, pixel/width); §5 = Sütterlin/Gleichzug naturalness (`core/quality_suetterlin.py` on `core/geometry.py` — smoothness/verticality/corner/collinearity/retrace, gated by a tolerant coverage). The bench runs ONE script per run (`--style suetterlin` default · `--style kurrent`), no combined `bench_loss`.
- `docs/reference/menschliche-bewertung.md` — the method of the blind human judgement pass over the fits (`tools/humanbench`): the six-category defect taxonomy, the instrument's construction rules each next to the failure it was added for, the pre-registered analysis plan, what is kept and what is not; read it before building or evaluating a round — the findings of a round live in `qualitaetsmetrik.md`, not here
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
| Auftragskorb work | `/work-basket` (protocol enforced by the API) |
| session retros | `/optimize-skills` |

Known gaps without a loop: admin write flows against the LIVE DB (HTTP suites
cover them on SQLite; see `admin-write-repro-harness` pattern). Dev tools
(glyphlab/wordlab/pairlab/…) are not skills — `docs/reference/werkzeuge.md`.

## Working guardrails (from session retros)

- **Never commit on `main`** — branch first, even for a quick "commit and push" outside `/open-pr`.
- **Every PR updates `CHANGELOG.md`** (`[Unreleased]`, Keep-a-Changelog categories, English, bold-titled bullets like the existing entries) — that file is how releases get posted; a PR without its entry is incomplete. The file merges by union (`.gitattributes`, since 2026-08-30), so parallel PRs never conflict in it — the one rule that keeps union safe: put a new bullet on TOP of its category and never rewrite existing lines in passing (a line changed on both sides would appear twice). Data-only commits (chart sources, authored templates) are exempt — their provenance lives in `SOURCE.md`. **A GitHub release is that section condensed, never copied** (owner rule, 2026-08-28): same headings, one bullet per NOTABLE entry (chores, dependency bumps and small fixes are left out; no fixed count), at most two lines each — bold title, one clause, PR reference — under an intro line (merge count, PR range, link to the file) and over a compare link; the full text stays in the CHANGELOG. The cut procedure itself is in the CHANGELOG's header.
- **New terms coined by a PR get a glossary entry in the same PR** — any new Fachbegriff, metric, named failure mode or repo idiom (`gen_chamfer`, „Cusp-Connector“, „like-for-like Gate“) is added to `docs/reference/glossar.md`, themed section plus alphabetical Schnellindex, so the vocabulary never outruns the place people look it up. Format and scope: `/write-docs` § "New terms go in the glossary".
- **Don't re-request a Copilot review after every push** (owner, 2026-08-23; PR #406 collected ~15 requests in a day). Each request is a full re-read of the whole diff, and the bot then surfaces „previously missed" findings in files the push never touched — a one-line docstring fix draws a finding somewhere else, which draws another push, which draws another request. Request a fresh review only after a SUBSTANTIVE change (new behaviour, a reworked mechanism), and stop re-requesting once a round yields no new inline comments but only carried-over suppressed items: the field is grazed. A PR that is green with no open threads needs no further round — say so and let the owner merge.
- **Prod-touching actions need explicit in-session confirmation first** (Cloud SQL DDL/queries, Secret Manager access, Cloudflare Access policies): name the exact action, resource, and any email/secret id, and ask before acting.
- **Archive snapshots: create freely, never destroy** (`tools/dbsnapshot`, owner directive 2026-08-08). The archive holds the only copy of what no recomputation brings back — `bboxes` and `templates.raw_path`. Cloud SQL's own backups are instance-wide and keep 7 days; this project's failure mode is slower (a bad apply noticed weeks later), so the archive is what covers it.
  - **Take one freely, and DO take one before anything that can overwrite geometry**: `apply-laufform`, a migration with DROP/rewrite, a harvest with `replace`, any DDL — and after an authoring session in which letters were traced.
  - **Every snapshot is a new timestamped directory. Never write into an existing one, never delete, move or rename one** — not to tidy up, not when disk is short. Report instead of acting. Note that the archive lives OUTSIDE the working tree precisely because `git clean -xfd` deletes gitignored files.
  - **Check plausibility before filing** (row counts per table, and the tool already fails a run that would file fewer rows than the previous one). A silent empty snapshot is worse than none because it looks like safety.
  - **Never print archive contents into the transcript** — that is the reserved dataset.
  - **Restoring is prod-touching** and needs the author's explicit say-so in the same session. `restore.py` is built for drills against a throwaway PostgreSQL: it refuses a URL equal to `DATABASE_URL`, refuses an occupied target without `--replace`, and writes nothing without `--apply`.
- **Never echo secret values into the transcript** — verify by exit code or metadata.
- **Modify repo files only with the Edit/Write tools, never via Bash heredocs/sed — appending with `>>` counts** (2026-08-21 slip: a §14 entry went in via `cat >>`; appending at the end of a file is exactly the forbidden path, however little it "feels" like editing). When a Bash command legitimately mutates a tracked file (formatter, codegen, `git checkout`), Read the file again before the next Edit on it — stale-state errors cascade otherwise. The moment this rule gets broken is when an Edit ANCHOR fails ("string not found", "file modified since read") — the answer is a fresh targeted Read plus a longer anchor, never a python-heredoc regex rewrite (2026-08-14 retro: ~15 heredoc writes to glossar/CHANGELOG/qualitaetsmetrik crept in exactly this way).
- **Manual author tasks go to Todoist** (owner directive, 2026-08-07): whenever
  a session identifies a step only the human can or should do (a wizard
  re-trace, a rendering-affecting DB apply that needs a go, a decision on a
  bulk re-derive), create a task in the owner's Todoist project
  **kurrentschrift** (Todoist MCP tools) naming the concrete action and its
  context — instead of leaving it buried in a chat reply. Korb rows still
  carry the protocol; the Todoist task is the actionable pointer.
- **The perfect result, not the fast one** (owner directive, 2026-08-05): when a cheap symptomatic fix and a correct structural fix compete, take the structural one — even when it looks like a regression at first (the ceiling question of the writing-systems research note). Concretely: fix the model/objective/rule, never mute the alarm; measure with a pre-registered A/B against ground truth (the measured ink) before adopting; an honest negative result that redirects the work is a valid outcome. CPU time on offline measurement runs is not a reason to cut a corner.
- **Every rejected measure names its rescue paths** (owner directive, 2026-08-16): a §14 entry that closes as an honest negative ends with the named ways it could still reach the goal (new mechanism, new evidence, new sensor — each with a fresh pre-registration; never the same knob re-run with softer gates), and the standing table `docs/proposals/tintenfolger.md` §7.9 gets its row in the same PR.
- **The owner merges PRs live, and squash-merges can race your last pushes** (seen twice on 2026-08-16): announce "green and review-clean" and prefer waiting for the merge before pushing more; after a race, recover by cutting a fresh branch from the merged main and cherry-picking exactly the missing commits — never re-push the stale branch.
- **Restarting a mandated branch after its squash-merge, when force-push is blocked** (cloud auto-mode classifier, 2026-08-21): `git checkout -B <branch> origin/main`, work, and at the FIRST push integrate the stale remote tip via a content-neutral merge — its content is already inside the squash. The recipe is strict because `git add -A` during an unresolved merge commits conflict markers (it did, once): resolve EVERY conflicted file with `git checkout --ours`, require `git diff --name-only --diff-filter=U` to come back empty, grep the tree for conflict markers (the seven-fold `<` — spelled out here it would make this very file a permanent false positive of its own check), and require `git diff ORIG_HEAD HEAD` to be EMPTY before committing (`ORIG_HEAD` is the pre-merge head, set by `git merge` itself); only then push normally.
- **Delegated agents and workflows run on Opus by default** (owner directive, 2026-08-11; refined 2026-08-16): pass `model: opus` when spawning subagents/workflows. Escalate to Fable for genuinely hard tasks that need deep reasoning, drop to Sonnet for simple mechanical grinding — but in most cases Opus is the right tier. Escalation is for WEICHENSTELLUNGEN, not for every detail: within its briefed scope a delegate decides routine matters itself and just documents them — otherwise delegation gains nothing. What comes BACK to the Fable main loop (which keeps the overview) are genuine judgment calls: anything that changes scope, contradicts the brief or the docs, touches a frozen ruler/pre-registration, or would be expensive to redo. Prompts to delegated agents state this split explicitly (decide-and-document vs. return-as-finding).
- **Solver measurement runs must pin BLAS threads** (`OPENBLAS_NUM_THREADS`/`OMP_NUM_THREADS`, finding of 2026-08-16, `qualitaetsmetrik.md` §14 „Wächter als Produktions-Kette"): the chain solve is not bit-reproducible across thread environments, so cross-run comparisons are only valid within one pinned setting — and pinning also collapses runtimes (63-word chain: 87 → 2.7 min).
- **No AI-development disclosure on the public site** (owner directive): legal/about pages carry no „KI-gestützt entwickelt" notices; strip AI credits inherited from anyplot templates.
- **Legibility over period authenticity in UI** (owner Leitsatz): no broken type in navigation, headlines or body copy; historic letterforms appear only as clearly marked specimens.

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

**Analysis-by-synthesis with a ductus prior.** The image supplies geometry + ink width; the canonical ductus template supplies stroke order and crossing resolution. A canonical template's key is `(style, glyph, variant)` — `style` is the Grundvorlage/script family (Kurrent · Sütterlin · Offenbacher; `templates.style_id`), the rest is the library unit within a style, not just glyph. Since the R2 position removal (schreibsystem-redesign.md, migration `0017`) glyph_keys are bare base keys (`a`, `longs`, `ch`) — ONE authored form per glyph, no initial/medial/final triplication; the word position is assigned per slot by `core/shaping.py` as RENDER context only (Anstrich/Auslauf, long-vs-round s choice). Allographs (e.g. long ſ = `longs` vs. round s = `s`) are *separate glyphs* with separate ductus, not one glyph with variants. Positionally-sanctioned form variants (the "A = A" on teaching charts) are separate templates (`variant`), not parameter deviations — the positional connection strokes are *generated* from `entry`/`exit` tangents.

The closed ligature set (`ch`, `ck`, `tz`, `ſt`, `qu`, `ß`) are first-class library entries, not exit→entry chains. Enumerate, don't generate. Arbitrary letter pairs *are* generated from `exit`/`entry` tangents + coupling height — that's the whole point of avoiding a bigram explosion.

When in doubt about what's a glyph vs. a variant vs. a deviation, re-read `docs/concepts/architektur.md` §3 and §4.

## Data & licensing (this repo is unusual here)

Code is MIT. **Data is not covered by the code license** — each source carries its own. The `/data` tree lives outside `/core`, `/api`, `/app` precisely to keep this boundary visible.

Three commit classes, kept strictly separate (see `docs/reference/datenablage.md` §1):

1. **Committable:** `/data/sources/` (public-domain only, e.g. Loth 1866 SVG) and `/data/samples/own-hand/` (author's own copyright). Each gets a `SOURCE.md` with permalink, license, attribution, retrieval date. Exception (owner decision 2026-08-22): the own-hand STRIP SCANS stay gitignored despite the owner's copyright — they are part of the reserved dataset, backed up to the private archive; only `SOURCE.md` + `README.md` are committed (`docs/proposals/eigenhand-erfassung.md` §8).
2. **Gitignored:** `/data/corpora/` — only `SOURCE.md` + `fetch_corpus.py` are committed, never the data files. Pin DOI versions.
3. **Mixed:** `/data/derived/from-cc-by/` is committable; `/data/derived/from-nc-sa/` is gitignored (NC-SA collides with MIT).

Hard rules:

- **Süß' Lehrbuch and similar copyrighted works never enter the repo** — not as scans, not as redrawn glyphs, not as derived images. Bibliographic reference in prose is fine.
- A scan is not automatically free under German law (§72 UrhG). Prefer in order: own hand → explicit PD/CC0 → own photo of a PD original.
- "Script-downloaded" ≠ "license-free." The license of the bytes follows the bytes, not the fetch mechanism.
- **The LEARNED dataset stays out of the repo (open-core moat).** The authored ductus templates, Laufformen and occurrence statistics — the DB contents — are reserved outside the MIT grant (README "License"). Technically enforced: bench fixtures stay gitignored, harvest artefacts are never committed, and the raw single-template API read is admin-gated; the public `/write` payloads are deliberate product surface under the README reservation + crawler policy. A public dataset only ever happens as a deliberate Ziel-7 release (architektur.md §17). See quellen-und-rechte.md §5 „Open-Core-Absicherung".
- Variant 0 (`v0-loth-1866`) is the canonical geometry baseline for first tests. The ductus prior is *the author's own contribution layered over* this PD geometry — Loth supplies shapes, not stroke order.

Before any data commit: *is this my expression or the expression of a protected source?* If unclear, link to the original rather than committing it.

## MVP gates

Four gates in `architektur.md` §8 — all four required for the kernel to count as validated:

1. **Stability** — ≥10 fits per core glyph cluster cleanly (`ſ`-med, `s`-final, `e`-med).
2. **Allograph separation** — cross-fit between medial ſ and final s separates per hand.
3. **Word rendering** — majority of seven MVP words reconstructed *and* `denen` rendered from aggregated per-glyph stats in the same hand.
4. **Animation (slim)** — one MVP glyph plays back with correct stroke order via `stroke-dashoffset` on the centerline (no Schwellzug yet; full Canvas-2D stroker is post-MVP §11).

If gates 1–4 hold, kernel is validated; otherwise valuable negative result in days.

## Test words

`lesen` (medial ſ, repeated e, ascender, u/n confusable final n) + `das` (final s) is the §9 Pflicht-Anker pair for the MVP. See `docs/concepts/architektur.md` §9 for the full MVP word set (incl. `denen` as the generalisation target).

## Two channels, kept separate

- **Width = pressure (Schwellzug):** from `skeletonize` + `distance_transform_edt`, measured on the mask, independent of darkness. Robust to fading.
- **Darkness = ink quantity:** separate grayscale channel; carries the dip-pen refill trace. For authentic rendering, not for geometry.

Binarization is the trap: too aggressive and a faded thick downstroke disappears, the skeleton breaks, and it gets misread as a hairline. Adaptive binarization + keep the intensity channel alongside.
