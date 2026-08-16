# Copilot Instructions

This file provides guidance to GitHub Copilot (and any other AI agent that
reads `.github/copilot-instructions.md`) when working in this repository.

A companion guide `CLAUDE.md` at the repo root contains the same domain
information targeted at Claude Code. Both files MUST stay in sync — if you
change one, check the other.

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
  normal review; edit through the editor. When a command legitimately
  rewrites a tracked file (formatter, codegen), re-read it before the next
  edit. A failed edit anchor ("string not found") means re-read and
  re-anchor — never fall back to a script-driven rewrite.
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
- **No AI-development disclosure on the public site** (owner directive):
  legal/about pages carry no „KI-gestützt entwickelt" notices.
- **Legibility over period authenticity in UI** (owner Leitsatz): no broken
  type in navigation, headlines or body copy; historic letterforms appear
  only as clearly marked specimens.
- **Claude Code sessions** additionally route work through verified skills
  under `.claude/skills/` (`verify-core` / `verify-api` / `verify-frontend` /
  `verify-migrations`, `write-docs`, `audit-licenses`, `open-pr`,
  `optimize-glyphs`, `optimize-skills`); Copilot can't invoke those, but the
  same gates apply manually (see "GitHub Workflow" → "Verification before a PR").

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
(pre-1900 normed handwriting). The vision is a single web app at
[kurrentschrift.ink](https://kurrentschrift.ink) that combines:

**Writing pillar**

1. **Onboarding** — history in two sentences, alphabet table, key reading
   and writing rules.
2. **Content-aware practice sheets** — configurable lineature ratios,
   arbitrary input text, printable PDFs.
3. **Animated letter tables** — every letter played back with stroke order
   and pressure build-up (true Schwellzug).

**Reading pillar**

4. **Modern text rendered in a trained Kurrent hand** — practice reading
   without depending on a stream of historical examples.
5. **Reading help for historical texts via HTR** (Transkribus default,
   TrOCR fallback) — extended with a **reading magnifier (Lese-Lupe)**:
   click on a confusing letter, get a structured explanation referencing
   orthography rules.

**Research pillar**

6. **Style analysis** — upload a sample, get statistics (slant, swell,
   transition angles, per-glyph cluster spread), with three follow-on
   paths: optimise, new-style-as-basis, hand comparison (heatmaps).
7. **Open data** — canonical glyph data (anchors, swell profiles, ductus
   order) as a citable Zenodo release.

Bilingual DE/EN is a cross-cutting guiding principle (German first;
English follows).

The full vision is in `docs/concepts/vision.md` (seven goals, three
pillars). The settled architecture (§1–§17) is in
`docs/concepts/architektur.md`. **Read those two before substantive work.**

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

```
kurrentschrift/
├── core/             # Pure-Python compute + DB layer
│   ├── extract.py    # skeleton + distance transform; fill_small_holes (per-glyph speck fill)
│   ├── template.py   # canonical sampling + outline + slant; sample_polyline drops a
│   │                 #   coincident anchor pair before splining (4-decimal storage can
│   │                 #   round the apex of a short out-and-back stroke onto one point,
│   │                 #   the chord-length parameter goes flat and CubicSpline raises
│   │                 #   "`x` must be strictly increasing sequence" — a 500 on every
│   │                 #   render of such a glyph, e.g. the Sütterlin `period`, killing
│   │                 #   its whole batch; without a repeat every sample is byte-identical)
│   ├── chart.py      # load + crop_with_mask (eraser + patches + ink brush); crop_mask_to_png_bytes (mask preview)
│   ├── pipeline.py   # canonical_from_path, diagnostic_for_glyph, render_payload_for_template
│   ├── shaping.py    # text → glyph_keys (long-s + Fuge marker `|` for round Schluss-s in compounds, ligatures, decompose fallback; digits/punctuation as detached `joins: false` glyphs, positions per joins-run; twin of app shaping.ts)
│   ├── compose.py    # word composition (placement + Übergänge; detached ink-clearance placement for non-joining glyphs; optional `pen` inks generated strokes per script; `pair_overrides` renders approved glyph_pairs rows verbatim (R3), no-override path byte-identical; single source of truth, golden-pinned)
│   ├── widths.py     # resolve_half_widths + pen models (§5, docs/concepts/federmodelle.md): BroadNib w(φ)-law + PenStyle, render-time
│   ├── fit.py        # M4: fit_template_to_instance, fit_glyph_to_crop
│   ├── word_metric.py # the FROZEN wordbench ruler (score_word/score_word_segments +
│   │                 #   specimen-reference builder with per-sample skeleton cache; moved from
│   │                 #   tools/wordbench/metric.py — which stays as a re-export shim — because
│   │                 #   the API image ships no tools/ and the admin score endpoint serves the
│   │                 #   SAME metric; the freeze rule covers it through the shim)
│   ├── aggregate.py  # Stufenplan H1: instances → per-hand aggregates (per-anchor median =
│   │                 #   the Laufform, MAD hull, pooled layer-1 stats) + laufform_deviation;
│   │                 #   H2: aggregate_pair_instances — pair_instances → one aggregate per
│   │                 #   (left_key, right_key): median offset + per-point median of the
│   │                 #   arc-length-resampled connectors (_resample_polyline, 24 samples) +
│   │                 #   MAD hulls + pooled dissection QC;
│   │                 #   pure numpy in core/ because the API image ships no tools/
│   └── database/     # SQLAlchemy Style + Hand + Source + Bbox + Template + Instance + Aggregate
│                     #   + PairAggregate + QuizWord + repos
├── api/              # FastAPI service (thin)
│   ├── main.py
│   ├── schemas.py
│   ├── dependencies.py
│   ├── rendering.py  # style resolution + memoised source-pooled nib (templates + write)
│   └── routers/      # health, styles, hands, sources, chart, bboxes,
│                     #   templates (public list = geometry-free summaries, the
│                     #   single-template GET admin-gated (open-core moat) and takes
│                     #   ?variant= so the STORED derived rows (Laufform 100) are
│                     #   readable — the wordbench fixture layer freezes them
│                     #   verbatim instead of rebuilding them, issue #311; beside it
│                     #   the admin-gated uncached batch read GET /sources/{id}/
│                     #   templates/quality → list[TemplateQualityOut] (glyph_key,
│                     #   variant, quality) served straight from the STORED
│                     #   templates.trace_meta["quality"] via
│                     #   TemplateRepository.list_quality, which JSON-indexes the
│                     #   column instead of loading the dense pixel_anchors/
│                     #   half_widths_px — the whole alphabet in one request
│                     #   (0.145 s for 80 rows vs. 0.44 s for ONE glyph through the
│                     #   recomputing /{glyph_key}/quality) because nothing is
│                     #   recomputed: it is the score AT AUTHORING TIME the derivation
│                     #   stamped, null for rows older than the metric, and the route
│                     #   is declared ABOVE GET /{glyph_key} so the literal path is
│                     #   not swallowed as a glyph key),
│                     #   pairs (R3 glyph-pair overrides: public reads + admin PUT/DELETE,
│                     #   only approved rows reach the composer),
│                     #   write (public batched render payloads + /word server-side composition,
│                     #   cached, no chart I/O; module-level compose_word_payload is the ONE
│                     #   shared shape+compose path), word_samples (public reads over the committed
│                     #   words.json sidecar: /word-samples metadata incl. the sample's page
│                     #   `rect` (page px — the origin that puts a page-pixel occurrence box
│                     #   inside a crop) + /crop PNG with excludes
│                     #   painted white — public like the bbox crops, <img> can't send the
│                     #   admin header; plus the admin-gated uncached /word-samples/{id}/score —
│                     #   R1b Stufe 2: the frozen core/word_metric.py ruler on the same
│                     #   composition /write/word serves, provenance=True, per-letter/per-join
│                     #   segment attribution, missing template ⇒ failed/1.0),
│                     #   quiz_words (public GET /quiz-words reading-drill bank:
│                     #   ~500 words, ONE pinned anchor distractor each, rest drawn at runtime by the
│                     #   shared similarity rules — docs/reference/quiz-wortbank.md),
│                     #   work_items (Werkbank W1+W4 Auftragskorb: FULLY admin-gated
│                     #   GET/POST/PATCH/DELETE per source PLUS the source-free
│                     #   GET/PATCH /work-items a session reads its queue from —
│                     #   filed letter/pair/word tasks plus the target-less kind
│                     #   'note' (a general Kleinigkeit — UI wrinkle, wording slip —
│                     #   whose whole content is the note text, filed in the Korb
│                     #   drawer, no migration: kind was always a plain string);
│                     #   the API ENFORCES the §5
│                     #   protocol: ack needs understanding + reproduced, done/returned
│                     #   need stage (fixed §3 vocabulary) + resolution, else 422 —
│                     #   a 'note' closes on resolution alone, the stage vocabulary
│                     #   names stages of the WRITING path),
│                     #   aggregates (Stufenplan H1: FULLY admin-gated GET /hands/{id}/aggregates
│                     #   + POST …/rebuild — condenses a hand's instances into per-anchor
│                     #   median (= the Laufform) + MAD hull + pooled layer-1 stats per
│                     #   (glyph_key, variant); reports laufform_dev_xh as the H1 Prüfstein.
│                     #   The LIST read carries the freshness pair per row — laufform_anchors
│                     #   (the rendered variant-100 form) + laufform_dev_xh (its distance to
│                     #   the median) — so "is what the engine writes still what the stats
│                     #   say?" is answerable without DOING anything; nulls where the compare
│                     #   is meaningless (non-base variant, no stored row, anchor mismatch).
│                     #   Median math in the pure core/aggregate.py; read+rebuild affect no
│                     #   rendering; letter rebuild min_n defaults to 1 since #273 (a key seen
│                     #   once is visible as a statistic — the caution lives in the apply).
│                     #   POST …/apply-laufform closes H1: the STORED aggregates
│                     #   (no recompute) become the style's variant-100 Laufform templates —
│                     #   selectable per glyph via the repeated glyph_keys query param
│                     #   (absent = all; the dialog pre-ticks n >= 3, flags thinner rows) —
│                     #   median = anchors, widths/topology/entry/exit/advance from the chart
│                     #   row via the SHARED templates.py::build_laufform_canonical the manual
│                     #   PUT …/templates/{key}/laufform uses. Own step because it DOES affect
│                     #   rendering; only base-variant aggregates feed it (never variant 100
│                     #   itself), missing chart row / anchor-count mismatch is reported as
│                     #   skipped, each applied key reports its pre-write laufform_dev_xh.
│                     #   It ENFORCES the occurrence floor too (core.aggregate.
│                     #   LAUFFORM_MIN_OCCURRENCES = 3 — where a per-anchor median first
│                     #   outvotes one bad anchor; at n=2 it is their mean, so one blown-up
│                     #   fit reaches the writing path at half amplitude — the capital S's
│                     #   spike): thinner aggregates are skipped as below_min_occurrences
│                     #   with their count however the request named them, ?min_occurrences=
│                     #   lowers it deliberately, and the dialog's LOW_N only mirrors it.
│                     #   The SAME module carries the pair twin (Stufenplan H2): admin-gated
│                     #   GET /hands/{id}/pair-aggregates + POST …/rebuild?min_n=1 — condenses a
│                     #   hand's pair_instances across sources into the own additive table
│                     #   pair_aggregates (migration 0023, keyed (hand, left_key, right_key)):
│                     #   median placement offset + per-point median of the arc-length-resampled
│                     #   connector centerlines + MAD hulls + pooled dissection QC (gen_chamfer =
│                     #   the „gemessen vs. komponiert" audit number, ink-gap share, word-plate/
│                     #   pair-drill histogram); kind is pooled (same hand, same transition),
│                     #   min_n defaults to 1 because pairs are sparse and n_instances rides
│                     #   along. Deliberately NO apply step — the pair statistics are read-only,
│                     #   glyph_pairs stays the verbatim override, the §4 generator stays the
│                     #   default, rendering untouched)
├── app/              # React 19 + Vite + MUI SPA (anyplot-style)
│   └── src/
│       ├── routes/      # paths.ts route constants + lazy public/admin route sections
│       ├── pages/       # thin default-export route mounts only
│       ├── sections/    # feature views: landing/, schriftkunde/ (/schriftkunde overview),
│       │                #   hub/ (/lesen + /schreiben area hubs), worksheet/,
│       │                #   scribe/ (/federprobe live writer), tafel/ (/tafel Schreibtafel),
│       │                #   quiz/ (useQuizEngine), impressum/,
│       │                #   admin/shell (the workbench hull shared by all three views:
│       │                #   AdminHeader (3 areas + Vorlage chip + Korb badge) — built on
│       │                #   the SHARED components/HeaderBar since the design round, so the
│       │                #   admin bar has the public bar's height, wordmark and nav face
│       │                #   instead of its old 48px Garamond-13 strip; the deliberate
│       │                #   differences stay: full-bleed (maxWidth="none", the workbench
│       │                #   needs the width), zIndex 1100 (under Korb drawer 1200 and
│       │                #   LetterPicker popover 1300), the Vorlage chip (a RouterLink chip
│       │                #   to /admin) + the Korb ⚑ badge, and no overflowX: auto on the nav
│       │                #   (the hover underline sits 4px below the links and grew a
│       │                #   scrollbar), StartView
│       │                #   (/admin = the Vorlage picker the area is entered through, on
│       │                #   PageContainer + PageHeader (eyebrow „Werkbank", Playfair h1,
│       │                #   Prose intro) over a 3-column card grid that names the plate
│       │                #   title; it offers only the sources CONFIG.hiddenSourceIds does
│       │                #   not hide — petzendorfer-1889 today, the second Kurrent chart
│       │                #   (another hand ~57° vs. Loth ~50°) seeded ahead of the Kurrent
│       │                #   digits row Loth 1866 lacks, since two cards both labelled
│       │                #   „Kurrent" only make the entry choice ambiguous. The list is
│       │                #   applied in context/AdminContext.tsx at exactly two points (the
│       │                #   one narrowing of the source list + the persisted-selection read,
│       │                #   so a stored hidden id can't strand the admin on a Vorlage with
│       │                #   no card to switch away from); NOTHING is deleted — no migration,
│       │                #   no DB change, the row, its chart bytes and every API route stay
│       │                #   as they are, removing the id brings it back),
│       │                #   LetterPicker (the letter grid as an on-demand popover — the
│       │                #   permanent sidebar is gone), WorkbenchData (THE shared data
│       │                #   layer: per-source occurrences + per-hand statistics, mounted
│       │                #   above the outlet so letter → join → word costs no refetch),
│       │                #   KorbContext/KorbPanel/MarkDialog (⚑ from anywhere, Korb as a
│       │                #   header drawer), LensStats, AggregateSketch (the H1 aggregate
│       │                #   drawing lifted out of LensStats behind a `height` prop, so the
│       │                #   miniature in the letter grid is the same drawing) + the pure
│       │                #   sketchGeometry.ts (isPoint/boundsOf/pathOf/letterSketchAnchors/
│       │                #   occurrenceChainsOf/SKETCH_FRAME), OccurrenceThumb (the crop's
│       │                #   air is proportional — max(7, 0.18·√(w·h)) crop px instead of a
│       │                #   fixed 4, THUMB_H 80 instead of 64: the stored box comes from the
│       │                #   M4 fit and hugs the centerline, so the tight crop cut into the
│       │                #   ink), Panel/ViewHeader (ViewHeader takes an `eyebrow` the three
│       │                #   views pass and uses variant="h4" + display/600/letterpress
│       │                #   instead of a hard-coded fontFamily/fontSize — size from the
│       │                #   ladder, face and weight in sx, per the design-system heading
│       │                #   rule; Panel titles are component="h2"),
│       │                #   and the pure, unit-tested focus.ts (subject ⇄ URL) + model.ts),
│       │                #   admin/{letters,joins,words} (the three views: /admin/buchstaben
│       │                #   ?g= · /admin/uebergaenge ?l=&r= · /admin/woerter ?w=&s=, each
│       │                #   overview ⇄ detail; every level also takes FREELY TYPED targets
│       │                #   that no plate ever wrote — they still have to look right, and
│       │                #   work_items takes the specimen ref as optional), plus the
│       │                #   routeless tool folders admin/{chart,setup-wizard,diagnostics,
│       │                #   compare,pairs,belege,quality} the views embed — admin/quality/
│       │                #   scoreParts.tsx holds scoreColor + the score chip + the
│       │                #   per-category breakdown, moved out of the wizard so the wizard
│       │                #   preview, the Diagnose modal (which gained the breakdown it
│       │                #   never showed although its payload carried it) and the letter
│       │                #   overview read the same number the same way, while
│       │                #   setup-wizard/steps/previewParts.tsx keeps only the silhouette
│       │                #   overlay. Admin redesign 2026-08
│       │                #   ("aus einem Guss") completed the absorption announced in
│       │                #   optimierungs-werkbank.md §2/§6; the old paths (/admin/chart,
│       │                #   /vergleich, /paare, /belege, /werkbank) stay as redirects.
│       │                #   (compare/GlyphComparison = the Buchstaben overview — every
│       │                #   authored letter as FOUR faces per tile since the design round:
│       │                #   Original (chart crop) · Tafel-Form (variant 0) · Laufform
│       │                #   (variant 100) · "Median & Vorkommen" (the H1 aggregate sketch:
│       │                #   per-anchor median, occurrence chains thin behind it, MAD
│       │                #   circles, the rendered Laufform dashed), each with an honest
│       │                #   empty state ("noch keine Laufform"; the sketch distinguishes
│       │                #   loading / no hand / admin read unavailable / genuinely no
│       │                #   aggregate); faces are flex: 1 1 150px so they break to 2×2 on
│       │                #   a phone, overlay mode still collapses the first two into the
│       │                #   red-silhouette overlay, and each tile carries its key numbers
│       │                #   (occurrence count, mean fit residual over the stored
│       │                #   occurrences, the stored image-space score + its per-category
│       │                #   deductions) plus a sort toggle (Alphabet · Schlechteste
│       │                #   zuerst) that turns the grid into a work list, each tile
│       │                #   opening its letter. Cost stayed flat: TWO batch render
│       │                #   requests for the whole alphabet (renderCache.fetchRenderGlyphs
│       │                #   gained variant + bust so a Laufform batch is possible at all),
│       │                #   the statistics from the shared workbench context (no request),
│       │                #   the scores from the ONE admin templates/quality read — and the
│       │                #   expensive per-glyph /diagnostic, once fired per card, is now
│       │                #   fetched ONLY for the overlay mode that needs its outline
│       │                #   geometry. Only variant 0's stamped score is used (a Laufform
│       │                #   row inherits the chart row's trace_meta, so its score is a
│       │                #   copy) and the chip tooltip says it is the score at authoring
│       │                #   time, not a re-score;
│       │                #   compare/WordComparison — words.json specimens vs /write/word, overlay
│       │                #   registered over the sidecar lineature; "Scores berechnen &
│       │                #   sortieren" fetches the admin /score per card sequentially, loss
│       │                #   chip + worst-first sort; pair cards link into the pair editor
│       │                #   with the specimen crop as registered underlay (R1b→R3 circle);
│       │                #   every pair card also carries the "Gemessen" chip row
│       │                #   (compare/PairMeasuredChips.tsx + compare/pairMeasurement.ts,
│       │                #   Handmodell H2): occurrence count + gen_chamfer mean, fuller
│       │                #   pooled QC in the tooltip, "Fit unsicher" when this specimen's
│       │                #   own occurrence has fit_ok: false — loaded once per source
│       │                #   (public pair-instances + admin-gated pair-aggregates of the
│       │                #   derived modal hand, a failed admin read degrades to the
│       │                #   occurrence numbers), numbers only (the median sketch stays in
│       │                #   the pair lens, no registered overlay);
│       │                #   the Fremdhand list is never scored and never measured);
│       │                #   pairs/PairMatrix.tsx = the Übergänge overview: every 2-letter
│       │                #   combination of a chosen letter, server-composed, capitals only
│       │                #   left — redesign R1; override badges + cell click focuses that
│       │                #   join, whose detail offers pairs/PairEditorDialog.tsx LAST
│       │                #   (R3 stage 2: draw the connector, approve, live preview — the
│       │                #   class rule comes first, per the §3/§4 doctrine);
│       │                #   words/WordSpineCard.tsx = TWO faces like a letter tile: left
│       │                #   the MEASUREMENT — a stored word-occurrence trace (green) over
│       │                #   its specimen crop (GET /word-instances + word-samples crop)
│       │                #   with dashed letter boxes from `instances` and a join dot
│       │                #   between adjacent boxes, all clickable into the other two
│       │                #   views — right the ENGINE'S own composition alone, at the SAME
│       │                #   px-per-unit on the SAME baseline row, so width/slant/rhythm
│       │                #   compare without rescaling. Both inks use the row's MEASURED
│       │                #   registration through the shared, tested shell/model.ts
│       │                #   traceFrameOf/traceMatrix (trace and composition share the
│       │                #   frame: baseline = 0, 1 unit = x-height); the old left-edge pin
│       │                #   sat a median 8.9 px (~0.3 xh) left of the ink over the 63
│       │                #   Sütterlin word rows and survives only where no trace exists.
│       │                #   The error-finding surface over the occurrence layer,
│       │                #   worst-first; "Nachfahren" opens
│       │                #   belege/WordTraceEditorDialog.tsx (Werkbank W3: re-trace the
│       │                #   ductus over the crop, pen lift = new stroke, undo/reset, save
│       │                #   as an `authored` word_instance via a single-item batch PUT —
│       │                #   crop↔trace mapping in the pure belege/registration.ts);
│       │                #   the Stufen-Einsicht (W5) shows the hand-model statistics
│       │                #   layers in the two views that own them (shell/LensStats.tsx —
│       │                #   "Statistik der Hand" under a letter, "Gemessen vs. komponiert"
│       │                #   under a join): letter = the H1
│       │                #   aggregate's anchor median + per-anchor MAD circles over
│       │                #   baseline/midband plus pooled layer-1 stats; pair = "Gemessen
│       │                #   vs. komponiert", every occurrence connector thin, the H2 median
│       │                #   connector bold on top, median offset as a dot with MAD whisker
│       │                #   (one shared left-exit frame, no /write/word overlay) beside the
│       │                #   dissection QC (gen_chamfer as the audit number). The hand is
│       │                #   derived from the loaded rows (modal non-null hand_id), never
│       │                #   hardcoded, and named in each block (warning line when the rows
│       │                #   name more than one); the admin-gated reads live in their own
│       │                #   per-layer effects so a 401 degrades to "keine Statistik" and a
│       │                #   rebuild refetches only its layer (previous rows stay mounted);
│       │                #   the sketches drop occurrences the rebuild skipped as fit_bad
│       │                #   (from the polylines AND the bounds, counted in the caption) and
│       │                #   print no "±" without a stored MAD; a quiet rebuild button per
│       │                #   layer. apply-laufform — the ONE rendering-changing
│       │                #   step — is deliberately NOT among these inspection
│       │                #   controls: it lives at the foot of the Buchstaben
│       │                #   view in its own set-apart block behind
│       │                #   letters/LaufformApplyDialog (warning → per-glyph
│       │                #   preview → confirmation → report), and the letter's
│       │                #   freshness ("Laufform aktuell/veraltet · Abstand")
│       │                #   plus the dashed rendered-Laufform chain in the
│       │                #   sketch come from laufform_dev_xh/laufform_anchors
│       │                #   on GET /hands/{id}/aggregates (issue #270) — plus
│       │                #   the Auftragskorb over work_items in the header drawer above
│       │                #   all three views; the ⚑ dialog asks the §4 pre-sort question
│       │                #   for letters (solo-wrong → wizard, files nothing). Needs
│       │                #   WordSampleOut.rect (page px) to place the page-pixel
│       │                #   occurrence boxes inside a crop)
│       ├── components/  # reusable UI: PaperBackground, HeaderBar (the shared header chrome:
│       │                #   HeaderBar (sticky, blurred, hairlined, optional content-width cap
│       │                #   + z-index) + Wordmark (•kurrentschrift.ink, viridian dot, italic
│       │                #   TLD) + HeaderNavLink (Playfair link, animated viridian underline,
│       │                #   aria-current) — PublicHeader AND admin/shell/AdminHeader are both
│       │                #   built on it, so entering the workbench does not change the
│       │                #   furniture; the public bar is visually unchanged),
│       │                #   PublicHeader (3-area nav, on HeaderBar), PublicFooter,
│       │                #   PageContainer (one column: narrow 760/text 1152/wide 1280), Prose (~66ch
│       │                #   reading measure), PageHeader (shared page-header: area eyebrow + Playfair
│       │                #   title + intro; every public page bar the landing hero), WrittenGlyph (one glyph), WrittenWord (word/line +
│       │                #   Übergänge as written), CategoryHeading (section title),
│       │                #   InfoHint (Kurrent-"i" popover, the one info affordance app-wide),
│       │                #   inkReveal/ (shared "as written" reveal primitives: silhouette masked
│       │                #   by a swept centerline + ink-bleed/settle — used by WrittenGlyph,
│       │                #   WrittenWord and the Tafel sheet), BootStatus
│       ├── layouts/     # admin shell (AdminLayout + AdminModals)
│       ├── theme/       # MUI theme split; colors sourced from styles/paper.ts (single source)
│       ├── lib/         # framework-free helpers: strokeTiming.ts (two-thirds-power-law +
│       │                #   isochrony timing for the reveal animation), svg.ts (ring-geometry →
│       │                #   SVG path d), bbox.ts, lineatur.ts, pdf.ts
│       ├── lib/api/     # fetch client (cold-start retry, typed ApiError), endpoints,
│       │                #   wire types hand-synced with api/schemas.py, renderCache.ts
│       │                #   (shared render-data cache, batches /write/glyphs per word;
│       │                #   fetchRenderGlyphs keyed by variant + bust, so a whole-alphabet
│       │                #   Laufform batch is one request)
│       ├── domain/      # glyphs.ts (registry + lock/quiz helpers); shaping.ts (text → glyph_keys —
│       │                #   quiz word-bank gating only; word composition moved server-side
│       │                #   to core/shaping.py + core/compose.py, compose.ts is gone)
│       ├── context/     # AdminContext (admin boot data + selection state)
│       ├── locales/     # de/ namespaces — ALL German UI strings (pre-i18n layer)
│       └── hooks/, styles/, global-config.ts
├── alembic/          # Postgres migrations
│   └── versions/     # 0004 library schema + seeds … 0006 Sütterlin 1922 source …
│   │                 #   0012 Petzendorfer 1889 as a SEPARATE Kurrent source (another hand
│   │                 #   at ~57°, the only PD Kurrent digits row — never merged into loth-1866)
│   │                 #   … 0013 quiz_words.created_at NOT NULL, 0014 Gulden gloss fix (silver),
│   │                 #   0015 unique (style_id, glyph_key, variant) on templates,
│   │                 #   0017 position removal (R2): base glyph_keys, sibling collapse,
│   │                 #   drop templates.position + bboxes.split, unique (style, glyph, variant),
│   │                 #   0018 glyph_pairs (R3): additive pair-override table, approved gate,
│   │                 #   0019 pair_instances + word_instances (handmodell H1/H2): observed
│   │                 #   join occurrences (unique source+kind+specimen+slot) and traced
│   │                 #   word templates (traced/authored, authored survives re-harvests),
│   │                 #   0020 work_items (Werkbank W1): the Auftragskorb — filed
│   │                 #   letter/pair/word tasks (later also the target-less 'note'
│   │                 #   kind — no migration, kind is a plain string),
│   │                 #   open → done + resolution,
│   │                 #   0021 aggregates re-keyed to (hand_id, glyph_key, variant)
│   │                 #   (Stufenplan H1; drop+recreate — the table was never populated),
│   │                 #   0022 work_items protocol columns (Werkbank W4): understanding,
│   │                 #   reproduced, stage, acked_at, closed_at — additive + nullable,
│   │                 #   0023 pair_aggregates (Stufenplan H2): additive pair twin of
│   │                 #   aggregates, one row per (hand_id, left_key, right_key), nothing
│   │                 #   seeded — the rebuild endpoint is its first writer
├── data/             # Sources, samples, derived — SEPARATE LICENSING
│   ├── sources/      # public-domain originals (Loth 1866, Sütterlin 1922 incl. connected-writing
│   │                 #   plates + words.json word rects for the word bench, Koch 1928 Offenbacher
│   │                 #   chart (live seeded source),
│   │                 #   Petzendorfer 1889 Kurrent chart, …)
│   ├── samples/      # own-hand scans
│   └── derived/      # mixed licensing — see datenablage.md
├── tools/            # Dev tooling: glyphbench/wordbench (frozen-reference scoring),
│                     #   glyphlab/wordlab/pairlab (matplotlib inspection labs),
│                     #   quizgen (quiz word-bank generator)
├── tests/            # CI pytest suite (flat test_<module>.py + shared fixtures)
├── docs/             # German design docs (start at docs/index.md)
│   ├── concepts/     # decisions + the core docs that follow from them (vision, architektur §1–§17, …)
│   ├── reference/    # look-up docs (language rules, licensing, metrics, tools, …) — status per doc
│   ├── schriftkunde/ # source-backed factsheets on the scripts themselves
│   ├── research/     # external research/literature notes feeding ideas (EN allowed)
│   ├── proposals/    # implementation proposals + their protocols (status in each doc's header)
│   └── notes/        # operational, dated journals
├── .github/          # this file + workflows
├── CLAUDE.md         # sibling guide for Claude Code
└── README.md         # public pitch (English)
```

`/app/` serves the public pages (`/` landing, `/schriftkunde` a compact
source-cited overview of the three Ausgangsschriften (Grundbegriffe · the three
scripts with one specimen each · Federn · Tinte · Buchstaben/Zahlen · chronology;
section titles share the viridian-Kurrent-initial `CategoryHeading` with
`/impressum`, `/tafel` and `/landing`; the copyrighted Süß textbook is named + linked to its DNB record,
never reproduced); the tools group under two hubs so the top nav stays at three
areas (Schriftkunde · Lesen · Schreiben): `/lesen` (→ `/quiz` reading quiz (letters + whole words) +
`/tafel` Schreibtafel) and `/schreiben` (→ `/schreiben/uebungsblatt` worksheet
generator + `/federprobe` live word/sentence writing, synthesised Sütterlin
ductus with generated Übergänge) — paper-&-ink identity
per `docs/concepts/style-guide.md` + `docs/concepts/design-system.md`) and the admin behind `/admin/*`
(Cloudflare Access in prod). Since the 2026-08 redesign the admin is ONE
workbench in three views over ONE chosen Vorlage: `/admin` is the Vorlage
picker (offering only the sources `CONFIG.hiddenSourceIds` does not hide —
`petzendorfer-1889` today; nothing is deleted server-side), then
`/admin/buchstaben` (its overview shows every letter as four faces — chart
crop · Tafel-Form · Laufform · aggregate median with its occurrences — with
key numbers, the stored quality score and a worst-first sort; its detail is
chart cell · wizard · diagnose · chart
editor · Tafel-Form vs. Laufform · occurrences · H1 statistics),
`/admin/uebergaenge` (generated join · H2 "Gemessen vs. komponiert" ·
dissected occurrences · pair matrix · pair editor as the last resort) and
`/admin/woerter` (any typed text written by the engine · what it consists of ·
the traced specimen with its occurrence overlay · score · word editor). Each
view is overview ⇄ detail with its subject in the query string, and each takes
freely typed targets that no plate ever wrote. **Post-MVP**
the public side grows
(`/animation`, `/lese-hilfe`, `/lese-lupe/:job`, `/stil-analyse`,
`/vergleich`, `/open-data`). See `docs/reference/frontend-stack.md`.

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

Admin write endpoints are gated by `require_admin`: set `ADMIN_TOKEN=<x>`
for the API and the matching `VITE_ADMIN_TOKEN=<x>` in `app/.env` so the
SPA sends `X-Admin-Token` (without it, local saves return 401). Against
the DEPLOYED API the same header works **only** via
`https://api.kurrentschrift.ink` — the apex `/api/*` 302s at the
Cloudflare Access edge before the header reaches Cloud Run. Never create
a secret version with `echo`: Cloud Run injects the bytes verbatim, and a
trailing newline no header can carry made the token gate reject every
value for two months (`docs/reference/frontend-stack.md`).

In a cloud session without Cloud SQL egress, the gitignored wordbench
fixture roots can be rebuilt entirely over the deployed API:
`uv run python -m tools.wordbench.fetch_fixtures --set all --verify`
(GETs only). The source-pooled Gleichzug nib comes exactly from the
admin-gated `GET /sources/{id}/render-context` (manifest `nib_precision:
"exact"`, verify gate bit-exact); an API predating that endpoint falls
back to the 4-decimal `/write/glyphs` readback (up to ~0.02 xh placement
jitter). The nib pools ALL template variants of the source — including
rows no read endpoint serves individually — so it cannot be recomputed
from fetched chart rows. The Laufform rows are likewise read VERBATIM
(single-template GET with `?variant=`, manifest `laufform_precision:
"stored"`; an older deployment detectably falls back to the aggregate
reconstruction, issue #311), and the verify gate cache-busts its own
`/write` reads so it compares against the origin, never the edge cache.

Browser at `http://localhost:3000/admin` loads the workbench: first the Vorlage
picker (the choice persists per browser; `CONFIG.sourceId` in
`app/src/global-config.ts` is the source the PUBLIC pages render — currently
the Sütterlin 1922 Ausgangsschrift — and the admin's default, while
`CONFIG.hiddenSourceIds` lists the sources the picker does not offer —
`petzendorfer-1889` today, a purely client-side omission applied in
`context/AdminContext.tsx`: nothing is deleted, no migration, the row and its
API routes stay, removing the id brings the card back), then
`/admin/buchstaben?g=<key>`, whose Tafel panel opens the source chart with a
draggable rough bbox and the step-by-step Einrichtungs-Wizard (Ausschluss —
freehand eraser + manual ink brush + per-glyph speck auto-fill + inserted donor cell (Zelle einsetzen —
copy ink from another chart cell into the crop, stored as `bboxes.patches`, so ü/ö are authored from a
u/o base plus the ä umlaut), with a binarised "Maske zeigen" preview
→ Lineatur (incl. Schräglage on the same canvas — no standalone slant step) → Weg → Übersicht/approve→lock) for
canonical extraction, and the 3-column SVG diagnostic from `/diagnostic`
JSON. The Weg step records the ductus as one or more pen-strokes — each pen
lift (Absetzen, e.g. a u's two downstrokes) starts a new stroke rather than
bridging it; the flat `raw_path` carries sparse `pen_up` markers and the
canonical stores `stroke_starts` in `trace_meta`, so the diagnostic outline
and the M4 fit keep the strokes separate. A Zeichnen/Anpassen toggle lets the
drawn line be warp-dragged (a falloff-radius nudge) to smooth a wobble in the
draft before saving. UI labels are German per DIN/Süß
lineature (Grundlinie · Mittellinie · Oberlinie · Unterlinie; zones Oberlänge
· Mittellänge · Unterlänge).

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

- Tables: `styles`, `hands`, `sources`, `bboxes`, `templates`,
  `glyph_pairs`, `instances`, `pair_instances`, `word_instances`,
  `aggregates`, `pair_aggregates`, `work_items` (the Werkbank's Auftragskorb — filed
  optimization tasks per letter/pair/word, plus the target-less `note`
  kind for a general Kleinigkeit; `open` → `ack` (the session's
  own restatement + whether it reproduced the complaint) → `done` with
  the diagnosed `stage` + `resolution`, or `returned` when the author
  has to supply ground truth; a `note` closes without a `stage`),
  `quiz_words` (the flat reading-quiz word bank — word +
  JSONB `distractors` + `era`/`note`/`fugen`).
- `styles` is the Grundvorlage/script family (Kurrent · Sütterlin ·
  Offenbacher); it carries `width_resolver` (§5) + lineature defaults.
  The resolver is applied at render time by
  `core/widths.py::resolve_half_widths` (`pressure` = measured Schwellzug,
  `constant` = Sütterlin Gleichzug, `broad_nib` = widths regenerated from
  the `BroadNib` model — w(φ) = W·|sin(φ−α)| + t·|cos(φ−α)|, constant 15°
  Federwinkel per Koch 1928, calibrated per source by
  `api/rendering.py::pooled_pen`; see docs/concepts/federmodelle.md); stored
  `half_widths` always stay the measurement.
- `templates` are the canonical Grundvorlagen, with **two** unique
  constraints since migration 0017: `(style_id, glyph, variant)`
  (the library tuple, architektur.md §3) **and**
  `(style_id, glyph_key, variant)` — every read keys on `glyph_key`, so it
  is identifying too; the API's 409 backstops are UX on top of the DB
  constraints, not the only defense. `instances` hold per-text occurrences
  (the fit + `measurements`, §12 layer 1 — filled by the laufform occurrence
  harvest since handmodell H1); `pair_instances` hold observed letter-join
  occurrences (handmodell H2, geometry in the `glyph_pairs` frame);
  `word_instances` hold one traced word per specimen sample (slot labels +
  pen-path strokes; provenance traced/authored — authored rows are manual
  admin traces that re-harvests never overwrite); `aggregates` are per-hand
  stats (§12 layer 2), keyed `(hand_id, glyph_key, variant)` since migration
  0021 and filled by the admin-gated rebuild endpoint (Stufenplan H1):
  per-anchor median = the Laufform, MAD hull, pooled layer-1 stats;
  `pair_aggregates` (migration 0023) is their pair twin, keyed
  `(hand_id, left_key, right_key)` and filled by the admin-gated
  pair-aggregates rebuild (Stufenplan H2): median placement offset,
  median connector centerline, MAD hulls, pooled dissection QC —
  read-only statistics, `glyph_pairs` and the join generator untouched.
- `bboxes` carries the chart crop + freeform eraser `mask_strokes` (replaces
  the old rectangle `excludes`) + baseline/midband calibration + `guides` +
  `locked`. JSONB columns hold structured data; aggregate stats in SQL.

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

## Architecture Highlights

The architecture is documented in `docs/concepts/architektur.md` (§1–§17,
about 17 sections after the May 2026 holistic restructure). Quick index:

| Section | Topic |
|---|---|
| §1 | Five-pillar problem split (Synthesis / Recognition / Analysis / Content / Data Export) — also the index to all following sections |
| §2 | Analysis-by-synthesis with ductus prior (rejected alternatives noted) |
| §3 | Library schema `(glyph, variant)`; word position = render context since R2 |
| §4 | Transitions are consequences (closed ligature set is the exception) |
| §5 | Width = pressure (Schwellzug) vs. darkness = ink; width-profile resolver per source (Kurrent / Sütterlin) |
| §6 | Three-stage quality pipeline (statistics → closed-loop → curation) |
| §7 | The one real research risk (template tightness) |
| §8 | MVP — six-letter alphabet + ſ/s split, four validation gates |
| §9 | Test words (`lesen` + `das` = Pflicht-Anker pair) |
| §10 | Post-MVP roadmap as five phases (Reading → Lineature → Style → Compare → Open Data) |
| §11 | Animation render path (Canvas-2D stroker with offset curves) |
| §12 | Style analysis pipeline (per-instance / per-hand / Hinge features) |
| §13 | HTR integration (Transkribus default with free-tier, TrOCR fallback) |
| §14 | Reading magnifier (own glyph recognition as didactic layer) |
| §15 | Print pipeline (WeasyPrint, configurable lineature) |
| §16 | Frontend architecture (anyplot-style React+Vite+MUI SPA) |
| §17 | Open-data export (Zenodo + DOI, CC-BY 4.0) |

Technical specs sit in `docs/reference/*.md`:

- `glossar.md` — the project vocabulary in six themed blocks (script &
  palaeography · architecture & data model · measurement/fit · metrics &
  benchmarks · workbench & process · external research), each entry a
  plain-language explanation plus the module/constant/formula anchor to
  dig deeper, with an alphabetical quick index on top. Read it when a term
  in a doc, issue or PR is unfamiliar; **extend it in the same PR that
  coins a new term or metric**
- `htr-integration.md` — Transkribus API, TrOCR fallback, PAGE-XML
- `animation-rendering.md` — stroke-dashoffset (MVP) + Canvas-2D (post-MVP)
- `styleanalyse.md` — Hinge features, heatmap layouts
- `qualitaetsmetrik.md` — score/bench_loss definition, frozen-reference
  rule, baseline history, experiment learnings incl. verworfen items.
  TWO metrics, one per script: §1–§4 Kurrent/Schwellzug
  (`core/quality.py`, pixel/width), §5 Sütterlin/Gleichzug naturalness
  (`core/quality_suetterlin.py` + `core/geometry.py`). Bench runs one
  script per run (`--style suetterlin|kurrent`), no combined bench_loss.
- `menschliche-bewertung.md` — the method of the blind human judgement
  pass over the fits (`tools/humanbench`): the six-category defect
  taxonomy, the instrument's construction rules each next to the failure
  it was added for, the pre-registered analysis plan, what is kept and
  what is not. Read it before building or evaluating a round; the
  findings of a round live in `qualitaetsmetrik.md`, not here
- `write-api.md` — the public render endpoints `/write/glyphs`,
  `/write/glyphs/{glyph_key}` + `/write/word`: shaping → composition →
  payload, cache behaviour, `missing` semantics (update it when changing
  any `/write/*` route)
- `quiz-wortbank.md` — the reading-quiz word bank: sources, the
  pin+runtime distractor model, Fugen-marker rules, extension workflow
- `crawler-richtlinie.md` — who may read the site: AI retrieval/citation
  allowed, AI training declined (`ai-train=no` as the express
  reservation of rights), `app/public/robots.txt` as the single source
  of truth, Cloudflare AI Crawl Control as the enforcement layer
- `frontend-stack.md` — build, deploy, auth, routes

The binding public-UI build spec is `docs/concepts/design-system.md` (colour
tokens, 19px type ladder + Playfair-600 heading rule, PageContainer widths
760/1152/1280 + Prose ~66ch measure, surface rule = identity-paper /
work-surfaces-white, IA = three areas + hubs, component inventory). Read it
before any public-page styling; it pairs with `concepts/style-guide.md`
(rationale/history).

Source-backed script facts (lineature terms, Schräglage convention
90° = upright, nib types, per-script data — incl. the measured ~50°
slant of the Loth 1866 chart vs. 60–70° for Kurrent um 1900) live in
`docs/schriftkunde/`.

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
pattern as anyplot.ai). Two Cloud Run services, live since 2026-05
(authoritative spec: `docs/reference/frontend-stack.md` §6):

| Service | Component | Purpose |
|---|---|---|
| Cloud Run | `kurrentschrift-api` | FastAPI (`api/Dockerfile`); `api/cloudbuild.yaml` runs an Alembic migrate job (`kurrentschrift-migrate`) before rollout, deploys `--no-traffic`, smokes the candidate revision and only then promotes traffic — serves api.kurrentschrift.ink |
| Cloud Run | `kurrentschrift-app` | static Vite build behind nginx-unprivileged (`app/Dockerfile` + `app/cloudbuild.yaml`) — serves kurrentschrift.ink |
| Cloud SQL | PostgreSQL | `kurrentschrift` DB (on anyplot's Cloud SQL instance — local dev writes the SAME DB) |
| Cloud Build | Triggers | one trigger per service (deploy-api / deploy-app), deploys from `main` |
| Cloudflare | edge | Cloudflare Access gates `/admin/*` (Google identity); a Cloudflare Worker in front of the app routes `/api/*` to api.kurrentschrift.ink (nginx in the app container knows no `/api`) |

Region europe-west4, min instances 0 (cold start acceptable for a
learning site).

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
  their `SOURCE.md`.
- **Codecov:** the bot comments the patch coverage on every PR (backend
  only). Treat it like a reviewer, not a hard gate: uncovered NEW logic
  that a unit test can reach cheaply gets a test in the same PR
  (prefer extracting a pure core from DB/async wrappers); lines only a
  live DB/HTTP flow exercises are covered by the API verification
  sweep instead.
- **Pre-commit hooks:** none configured yet — when added, do not bypass
  with `--no-verify`.
- **Verification before a PR:** run the local CI equivalents first —
  `uv run --extra test pytest`, `uv run --extra dev ruff check .`,
  `uv run --extra dev ruff format --check .`, plus `npm run lint`,
  `npm run test` and `npm run build` in `app/` when the frontend changed.
  The pipeline should never fail on tests or lint. (Claude Code sessions encode these loops as skills
  under `.claude/skills/` — verify-frontend / verify-api / verify-core /
  verify-migrations, write-docs, audit-licenses, open-pr, optimize-glyphs,
  optimize-skills.)
- **Glyph-pipeline changes are benchmarked:** `tools/glyphbench` scores
  every authored glyph against frozen references, ONE script per run
  (`uv run python -m tools.glyphbench.run --style suetterlin|kurrent`,
  headline `bench_loss:` — lower is better; Sütterlin also prints
  `comp_<name>:` per-category means, `--compare prev.json` diffs them).
  A PR touching `core/` extraction or rendering should quote before/after
  numbers; the bench never touches the DB (fixtures exported once,
  read-only). One level up, `tools/wordbench` scores COMPOSED words
  (placement + Übergänge from core/shaping.py + core/compose.py) against
  frozen same-hand word specimens the same way — the Abb. 19 words AND,
  as a separate set with its own `pair_loss` headline, the Abb. 20
  letter-pair joins
  (`uv run python -m tools.wordbench.run --style suetterlin [--set
  words|pairs|all]`; composition mirrors production incl. the frozen
  Laufform variants (`templates_laufform.json` → `laufform_by_key`,
  `--no-laufform` = chart-only diagnostic); unauthored templates are
  frozen `scorable: false`
  and skipped+reported, never averaged in; the metric lives in
  `core/word_metric.py` with `tools/wordbench/metric.py` as its
  re-export shim; see
  docs/reference/qualitaetsmetrik.md §6) — a PR touching core/compose.py
  should quote its before/after `bench_loss:` (and `pair_loss:`) too.
  A third, CROSS-HAND set exists: the Abb.-22 Schülerschrift plate
  (words-abb22.png, 106 words, Breitkantfeder, a pupil following the
  same norm — sidecar entries carry `set: "abb22"`, frozen into the
  sibling root `suetterlin-1922-abb22`, run via `--set abb22`); its
  numbers track generalisation and are NEVER part of the same-hand
  headlines.
- **Glyph inspection (see, don't just score):** `tools/glyphlab` renders
  matplotlib overlays of a glyph's derivation (crop · skeleton ·
  centerline · corners · silhouette) to `temp/`, from a fixture or a
  read-only live DB pull — `python -m tools.glyphlab <key> [--live]
  [--stages]` (matplotlib is the dev-only `viz` extra), annotating each
  panel with its per-category penalty. For Sütterlin the bench scores
  ductus naturalness directly (so `bench_loss` moves on centerline/corner
  shifts); the overlay says *why* a glyph lost points, the number *how much*.
  Its word-level sibling `tools/wordlab` draws a COMPOSED word over its
  wordbench specimen with per-connector penalty callouts
  (`compose_word(..., provenance=True)` + `score_word_segments` attribute a
  deviation to a letter or a specific join) — `python -m tools.wordlab <id>
  [--set pairs] [--live] [--sweep core.compose.CONST=v1,v2]`. The provenance
  flag is diagnostics-only and default OFF: the `/write/word` payload and the
  compose golden fixture stay byte-identical. `tools/pairlab` dissects ONE
  letter join against its real specimen occurrences with every letter re-fit
  INDEPENDENTLY (separates connector-shape from placement error and measures
  how far the specimen reshapes each glyph's own tail/head for the join) —
  `python -m tools.pairlab re [longs,a] [--set words|pairs|all]`; findings +
  solution options in `docs/proposals/uebergaenge-befund.md`. Its harvest
  sibling `tools/pairlab/harvest.py` (redesign R3 Erstbefüllung, no viz
  extra) turns those dissections into `glyph_pairs` override DRAFTS — offset
  from the rigid fits, connector from the specimen's joining stroke,
  baseline-locked — written through the admin API (`--apply`,
  `--approve left:right` only for measured winners); measure the composed
  effect with `tools/wordbench/run.py --overrides <harvest.json>` (an
  override run is its own number, never the headline). Its chain sibling
  `tools/pairlab/chain.py` (issue #278 Stufe A, no viz extra) fits the
  SAME join as ONE continuous pen path instead — both chart rows plus
  the form-unregularised connector as three segments of one anchor
  array, the seams tied by SHARED anchor indices rather than a penalty,
  placement kept separate as an unregularised per-slot translation block
  — so the letter/connector cut stops depending on whether the letters
  touch (where `_real_join` returns nothing today);
  `tools/pairlab/chainbench.py` runs the chain and the independent fit
  over the same frozen occurrences and reports the four Stage-A metrics
  + kill criteria (`--set all` = words+pairs of the same hand, never the
  Abb.-22 writer; `--aggregates <file>` supplies M4's MAD floor from
  `GET /hands/{id}/aggregates`). M1 prints THREE convergence gates over
  the same solves — the chain's union window, the LETTER-LOCAL window the
  independent trace was always graded in (`ChainSegmentSpec.cov_window_px`,
  the like-for-like column and the one Stage B must quote) and the baseline
  re-graded on the union window — and M3 prints `dconn` both whole-curve
  and ARC-MATCHED (all curves clipped to the specimen's ink gap ∩ their own
  x-spans, since the chain connector owns the stub zones the ink-read one
  lacks). Measurement only — no DB, no API, no `core/`, no rendering; the
  measured verdict (after the Stage-B preconditions were re-measured: go,
  with the `pair_aggregates` ban kept for the loop-exit class) is
  `docs/proposals/uebergaenge-befund.md` §5c. The M1 deficit that verdict
  named turned out to be an INITIALISATION bug and is gone (0,690 →
  0,754, §5c Nachtrag): where two letters are composed on top of each
  other the generator's handle floor makes the connector a cusp of
  ~0.05 xh carrying all its points, and the curvature-change term (scale
  1/ds²) then dominated the objective by ~7 orders of magnitude and ate
  the whole iteration budget while the letters never moved.
  `chain.regularise_connector_anchors` re-discretises such a connector to
  the anchor count its chord can carry — same shape, same endpoints,
  nothing above `CHAIN_CONNECTOR_MIN_SPAN_UNITS` touched. Its diagnostic
  sibling `tools/pairlab/gradlab.py` (no viz extra) answers the question
  that comes BEFORE any new fit term: at the found optimum, which term
  holds a stranded anchor where it is? An optimum is a point where the
  forces cancel, so this is a measurement, not a guess —
  `chain._ChainProblem.gradient_terms` splits the objective into its
  seven weighted forces (`geo` · `crop` · `width` · `coverage` ·
  `overlap` · `smooth` · `reg`) per free anchor, all folded through the
  SAME chain rule and packing the objective uses, and
  `chain.gradient_decomposition` re-adds the split and RAISES unless it
  reproduces the gradient L-BFGS-B actually followed (measured 2.7e-14
  relative) — a decomposition that does not is diagnosing a different
  objective. `chain.sample_slice_of_anchor` supplies the reading at the
  samples between an anchor's two neighbours, i.e. where the objective
  reads the field at all (never at an anchor;
  `vom-scan-zum-schreiben.md` Schritt 4). The sweep re-runs the
  harvest's own solves (`fit_word_chain(keep_solve=True)`, same
  cases/windows), flags strandings by the shape the author's markings
  have (both neighbouring steps ≥ 3× the median step of their own
  pen-stroke, never across a lift) and carries every other letter anchor
  as a CONTROL population — a term pulling as hard at a healthy anchor
  as at a stranded one explains nothing. Measurement only: no DB, no
  API, no `core/`, no rendering; method and criteria in
  `docs/reference/qualitaetsmetrik.md` §11. The stranded anchor itself
  is REPAIRED at harvest since `aug11` (`tools/pairlab/anchors.py` —
  the ONE shared detector + `repair_stranded_anchors`, interpolation of
  the unflagged stroke neighbours, never a snap; wired post-gate into
  both storage paths of `tools/laufform/harvest.py`, logged as
  `measurements.repaired_anchors`, the gate keeps judging the
  UNREPAIRED geometry — the four objective-side terms are all
  measured-and-rejected, §11e). Its two human-loop viewers:
  `tools/fitview` (no viz extra — the judged humanbench screens re-fit
  live and drawn before/after in the SAME window-pad/4×-zoom frame the
  judgement used, owner markers as crosses, one self-contained HTML)
  and `tools/pairlab/peaklab.py` (`viz` extra — a small NAMED working
  set incl. control words, anchor chain over the skeleton with lone
  excursions circled, `--compare` for fitted vs. repaired; minutes per
  round, the fast loop for the peak class). Its landmark siblings supply
  what §13 named as the missing piece: `tools/pairlab/landmarks.py` (no
  viz extra) is the ONE shared detector — a ductus polyline's proper
  self-intersections classified as landmarks (≥ 15°, ≥ 0.35 xh arc
  separation, co-located duplicates merged, never bridging a pen lift)
  plus the ink side's skeleton branch points, an ambiguous assignment
  REFUSED rather than guessed — and `chain.py` prices that
  correspondence as its first DATA term (*this point belongs on that
  point*, not the proxies of §7/§8/§10/§11d), linearised like every
  other chain operator (chord pair and parameters frozen at the initial
  anchors, exact gradient) with `landmark` added to `GRADIENT_TERMS` and
  weight `CHAIN_LANDMARK_WEIGHT` **default 0.0**, so every solve stays
  byte-identical until a weight is calibrated.
  `tools/pairlab/landmarklab.py` (no viz extra) is that calibration lab:
  `--calibrate` reads `e_geo / e_landmark` at the BASELINE optimum
  (§11c's lesson — a ladder chosen by analogy measures nothing), the
  effect run reports the fitted crossing height against the ink target
  with its costs. Measurement only: no DB, no API, no `core/`, no
  rendering; no default weight is proposed from a 14-occurrence
  single-glyph set (`docs/reference/qualitaetsmetrik.md` §13a).
  `tools/wordbench/fetch_fixtures.py` is the read-only API twin of
  `export_fixtures.py` for sessions without Cloud SQL egress —
  byte-compatible fixture roots over HTTPS, GETs only, `--verify`
  composes the rebuilt cases against `/write/word`. The bench also
  reports a slant column (`slant <spec>/<comp>` per row + medians,
  `tools/wordbench/slant.py`, 90° = upright) and, third in that
  report-column lineage (slant → Gleichzug → meas), the
  **gemessen-vs-komponiert** column (`tools/wordbench/pairmeas.py`,
  handmodell H2): per row `meas n=<matched>/<joins> doff=… dconn=…` plus
  block medians + `meas_excluded` — the composed join against the
  specimen's own dissected one, `doff` = the HORIZONTAL placement delta
  in the harvest's BODY frame (the left glyph's last non-diacritic
  stroke end → the right glyph's first, against the measured
  `geometry.offset`'s x; the composer's coupling anchors sit up to ~2 xh
  away after a capital ornament, and the measured y is by construction
  the composed Δy, so neither is compared), `dconn` = connector shape
  (mean pointwise distance, arc-length-resampled to
  `core.aggregate.PAIR_CONNECTOR_POINTS` and each start-aligned, hence
  translation-free; the composed line still carries its overlap
  extension/capital retrace, so it is a monotone signal, not a
  calibrated distance). QC-rejected dissections (`fit_ok`) and
  override-rendered joins are excluded and counted, never averaged. It
  reads the NEW frozen fixture artifact `pair_instances.json` (per set,
  written atomically by `export_fixtures.py`; `--only pair-instances`
  fills it into existing roots without re-freezing anything else — a
  corrupt one costs the columns and one warning line, never the run) and
  needs `compose_word(..., provenance=True)`, which tags glyph items
  with `slot_index` and states each join's `exit`/`entry` in word
  coordinates. All of these are report-only, never part of the loss — a
  headline must stay byte-identical across their introduction.
- **Human judgement (what no metric sees):** `tools/humanbench` is the
  one tool whose sensor is a HUMAN rather than a metric — the blind
  judgement pass over the stored fits, answering „which kind of defect
  does any of our numbers see at all?". `build.py` draws a round
  (stratified by severity with a seeded shuffle INSIDE the bands, blind
  repeats as the reliability bound, a held-out reserve; `--only` restricts
  a round to an earlier round's reserve, which is how the pre-registered
  confirmation pass is run) and writes payload + key + slim key +
  provenance stamp under `temp/humanbench/runde-<n>/`;
  `page.py` renders one self-contained HTML page from it (category mode
  with one panel per screen, paired before/after with two — the side
  assignment lives in the key alone); `analyse.py` evaluates the emitted
  result text in the order the plan fixed BEFORE the labels existed
  (`--union W,B` is the plan's fallback column for two categories the
  judge does not separate — asked for, never default) —
  `python -m tools.humanbench.{build,page,analyse}`, no `viz` extra. No
  writes anywhere; `build.py` reads GET-only over the deployed read API
  when no instance file is supplied. Method in
  `docs/reference/menschliche-bewertung.md`, findings in
  `qualitaetsmetrik.md`. Committed under `data/humanbench/` are the
  judgements AND the builder-written slim key (`*-vorkommen.json`: uid →
  glyph, specimen word, slot, `repeat_of`) — a result line is
  `S026:AW#81,76`, so without a key the human work would be filed
  unreadably, and which letter sits in which word of a public-domain plate
  is not learned geometry; the `slot` is in there because the cross-round
  identity is (glyph, word, slot). The full key (severity, rank), the
  payload and every per-occurrence metric table stay out
  (`quellen-und-rechte.md` §5); `analyse.py` runs without them and reports
  which steps it skipped — and nothing in the repo produces those metric
  tables yet, so a category round's steps 3-5 still need that module.
- **Never merge a PR yourself** — open it, get it green and
  review-clean (address Copilot review comments, then resolve the
  threads); merging is the maintainer's call.

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
   `docs/reference/*.md` that describes it.
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
