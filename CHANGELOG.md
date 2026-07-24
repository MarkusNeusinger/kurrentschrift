# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Every PR adds its entries under `[Unreleased]`; a release moves that section under a new
version heading AND bumps `CITATION.cff` (`version` + `date-released`) and
`pyproject.toml` (`project.version` — `/docs` reads it at runtime) in the same commit.
Code changes are covered here — data-only commits (chart sources,
authored templates) are covered by their `SOURCE.md` provenance records instead.

## [Unreleased]

### Added

- **Straight-fit flank coupling for sawtooth letter pairs (the "ne" kink).**
  Between two mid-band diagonals whose entry foot sits at/below the previous
  exit (n→e and friends), no spacing can make the generated connector
  collinear — the taut cubic ran visibly flatter than both ink flanks (n→e
  chord −7° between 41°/39° tangents on the golden payloads), the kink the
  connected-writing review kept flagging. `core/compose.py` now solves the
  PAIR DISTANCE together with the coupling point, in two stages. Fusion
  (`_fused_flank_placement`): the join continues the stroke direction
  itself — the pair is pushed together until the line through the exit at
  the FULL mean ink tangent meets the rising lead-in flank, the connector
  degenerates to a short collinear piece and the stub below the coupling
  point is absorbed by the join (the O2 trim mechanism, silhouette
  included); since fusing stroke ends overlap in x by design, legitimacy is
  judged by a new height-aware per-y-bin clearance guard
  (`_fused_clearance_ok`) instead of the column ink floor. Fallback
  (`_flank_couple_steepest`): a rejected fusion places at the stub-relaxed
  column floor and couples the steepest reachable straight line instead of
  dipping below both flanks; connectors whose crossing already lies inside
  the couple-able window (a→n, g→e) degenerate to the exact straight middle
  piece at unchanged placement. On the golden payloads n→e goes from a −7°
  dipping cubic to a 39.9° straight between 41.2°/40.9° flanks — seam kinks
  −1.3°/+1.0°, one continuous diagonal. Guarded to the sawtooth class: both
  tangents inside `ALIGN_TAN_DEG`, coupling below `ALIGN_MAX_ENTRY_Y`, entry
  drop bounded by `FLANK_COUPLE_MAX_DROP` so the nested-fall letters (t's
  bar, f's flag) keep their bench-confirmed authentic S-join. Golden fixture
  deliberately re-pinned; the wordbench headline still needs a re-measure in
  a DB-connected session (qualitaetsmetrik.md §6).

- **Harvest importer for glyph-pair overrides (redesign R3 Erstbefüllung).**
  `tools/pairlab/harvest.py` dissects every adjacent joined pair in the frozen
  Abb.-20 pair fixtures (independent rigid fits + M4 ductus traces) and derives
  the `PairGeometry` the composer replays verbatim: placement offset from the
  rigid fits, connector centerline from the specimen's own joining stroke,
  baseline-locked so the stored path meets the composed entry
  (`connector[-1] == offset`). One best occurrence per pair with QC (fit
  residuals, gap ink, harvested vs generated chamfer); `--apply` PUTs
  unapproved `harvested` drafts through the admin API's validation and
  `--approve left:right` flags measured winners in the same upsert. The word
  bench gains `--overrides <harvest.json>` — an override run is its own
  measurement, never the headline; with only the four capital pairs B:i, I:n,
  D:u, O:f overridden, `pair_loss` falls 0.1918 → 0.1864 on the frozen
  fixtures.

- **Slant report column in the word bench (redesign R5, stage 1).**
  `tools/wordbench/slant.py` implements the shear-search estimator from the
  redesign findings (−30°…+30° in 0.25° steps, maximum sum of squared column
  profile; 90° = upright, < 90 = right-leaning). Every scored row reports
  `slant <specimen>/<composed>` plus per-block medians; report-only —
  headlines and per-word losses verified byte-identical. On the frozen
  references it reproduces the d-loop finding: das 86.2°, der 87.2°,
  die 88.0° against a rigid ~90° engine.

### Changed

- **The SPA lint gate now enforces the React Compiler rules
  (`eslint-plugin-react-hooks` 5 → 7).** v7 folds the stabilised React Compiler
  rule set into `recommended`: 16 rules where v5 shipped two, of which **11 are
  enforced at error** — previously only `rules-of-hooks` was. Ten of the newly
  adopted error-level rules (`purity`, `immutability`,
  `preserve-manual-memoization`, `static-components`, `error-boundaries`,
  `set-state-in-render`, `globals`, `use-memo`, `config`, `gating`) are already
  clean on the tree, so the gate gets strictly stronger at no cost. The two
  that are not — `react-hooks/refs` (the latest-ref `ref.current = prop` write
  during render, 4 sites) and `react-hooks/set-state-in-effect` (the "reset
  transient state when the input prop changes" effects, 21 sites) — are
  configured as warnings rather than switched off, because clearing them is a
  behavioural refactor of `WrittenGlyph`/`WrittenWord`, the diagnostics dialogs
  and the admin compare views, tracked with every site listed in issue #227.
  `npm run lint` therefore
  reports 0 errors / 45 warnings (20 pre-existing `react-refresh` + the 25
  above); tests, build and `npm ci` are unaffected.

- **Ruff no longer formats the Markdown docs.** Ruff 0.16 extends `ruff format`
  to Python code blocks inside Markdown, which reflows the illustrative
  snippets under `docs/` and in the tool READMEs — schema sketches,
  pseudo-code and column-aligned trailing comments whose alignment is the
  point. `*.md` therefore joins `[tool.ruff] exclude`; the formatter's scope
  stays the 128 Python files it always covered. Unblocks the ruff
  0.15.20 → 0.16.0 bump.

- **Public `/write` endpoints: p95 latency ~1100 ms → ~100 ms (rendered
  geometry byte-identical).** A cProfile of a realistic workload (real
  120-anchor Sütterlin templates, mixed words up to the 160-char cap, gzip
  on) showed 74 % of request CPU re-rendering the SAME glyph payloads per
  request, dominated by per-segment Python-loop shapely buffers plus
  `union_all`, with FastAPI's `jsonable_encoder` walk and level-9 gzip on
  top. Four independent, output-preserving fixes: (1) `api/rendering.py`
  memoises `render_payload_for_template` per
  `(style, glyph_key, template id+updated_at, resolver, ratio, nib, pen)`
  with the same TTL + invalidation discipline as the pooled-nib cache
  (admin template writes clear the style's entries; callers copy before
  annotating — the shared payloads are never mutated, pinned by the golden
  parity fixture); (2) `core/template.py` builds the capsule/chisel
  silhouette geometries with shapely 2.x vectorized array calls instead of
  93k Python-level `buffer()` calls — bit-identical output verified against
  the previous implementation on all fixture glyphs plus randomized
  degenerate inputs (capsule 1.6×, chisel 3.5× faster); (3) the three write
  endpoints serialize straight through `orjson` (new runtime dependency),
  bypassing the `jsonable_encoder` walk over ~100k floats per response, and
  the write-path template fetches defer the unused `raw_path`/`measurements`
  JSONB columns (~100 KB per glyph off every request); (4) `GZipMiddleware`
  drops from the implicit compresslevel 9 to 6 (~3× faster on the large
  geometry bodies for ~1 % more bytes). In-process benchmark, 84 mixed
  requests: `/write/word` p95 1116 → 100 ms (max 217 ms), the 23-key
  `/write/glyphs` batch p95 1031 → 26 ms.

- **Composer placement: nested-fall class rule (redesign R4).** With the
  global advance bias gone, the pairlab residuals are class-shaped: rising
  mid-band exits whose neighbour enters below them (t's bar, f's flag, c's
  hook — no sawtooth pass-through possible) composed up to 0.34 xh too wide
  because their far-right ink pinned the clearance floor. On the plates the
  next letter nests under that ink: the ink floor now relaxes to
  `ALIGN_MIN_CLEARANCE` for exactly this class. Words bench 0.1185 → 0.1178,
  pairs unchanged. Re-evaluated and again rejected in the same loop: the
  ligature-remnant tuck and the O3 A-side d-stub trim — the latter with a
  sharpened diagnosis (the trimmed stub retraces the loop's crossing stretch,
  which carries real specimen ink; both headlines regress).

- **Bound d leans its ascender loop like the school hand (redesign R5,
  stage 2).** The measured d-Oberlängen-Schleife leans 4–5° right in
  connected writing while the chart cell stands upright. A bound d in a
  joined run of ≥ 3 letters now shears its above-midband part 4.5° right at
  render time — centerlines, silhouette rings and every downstream
  measurement consistently; the stored template stays the chart measurement,
  a solitary d and the isolated two-letter drills (measured upright) render
  chart-true. Bench-neutral within ruler noise; decided by the slant
  measurement and the das/der overlays. Extending the class to b/h/k was
  checked and not adopted (no measured lean). The compose golden fixture is
  deliberately re-pinned for this intentional output change.

- **Pair cards link into the pair editor with the specimen as underlay.**
  Closing the redesign's R1b→R3 circle: every letter-pair card in the
  `/admin/vergleich` Verbindungen tab gets an "Im Paar-Editor öffnen" action
  that opens the pair editor for exactly that join, with the Abb.-20 specimen
  crop rendered as a semi-transparent, lineature-registered underlay in the
  drawing scene (baseline on y = 0, scale from the sidecar lineature; a
  "Vorlage unterlegen" toggle hides it) — the connector is drawn over the
  real pen's path instead of from memory. Saving an override invalidates
  that card's cached score; pairs that don't shape to exactly two slots
  offer no link. The shared `pairKeysOf` helper moved to its own module.

- **Specimen scores in the admin word comparison (redesign R1b, stage 2).**
  New admin-gated endpoint `GET /sources/{id}/word-samples/{sample_id}/score`:
  it runs the frozen wordbench ruler on the same composition `/write/word`
  serves (shared `compose_word_payload`, approved pair overrides included)
  and returns loss/components plus per-letter/per-join segment attribution
  from compose provenance; a specimen with a missing template scores
  `failed`/1.0 (the bench crash rule). The `/admin/vergleich` word and pair
  tabs gain a "Scores berechnen & sortieren" action that fetches each card's
  score sequentially, shows a colour-coded loss chip (tooltip: the three
  worst segments) and sorts worst-first; the other-hand tab is deliberately
  never scored. To serve the metric from the API image (which ships no
  `tools/`), the ruler moved to `core/word_metric.py` — together with the
  exporter's specimen-reference pipeline and a per-sample skeleton cache —
  while `tools/wordbench/metric.py` remains as a re-export shim, so the
  bench's frozen import path and behaviour are unchanged.

- **Pair editor + override badges (redesign R3, stage 2).** Clicking a cell
  in `/admin/paare` opens the new `PairEditorDialog`: both letters rendered
  at an adjustable coupling offset (right entry relative to left exit), the
  connector drawn directly with the pointer/stylus, an approval checkbox and
  a cache-busted live `/write/word` preview. Freehand saves are stored as
  `authored`; approving an untouched harvested row keeps its provenance and
  specimen citation. Matrix cells show green (approved) / orange (draft)
  override badges; ligature-folding cells (ch, ck, …) have no join and stay
  non-clickable. New client endpoints for `/pairs` CRUD.

- **Glyph-pair override layer (redesign R3, stage 1).** New `glyph_pairs`
  table (migration `0018`): sparse per-pair overrides over the §4 join
  generator, carrying a connector centerline + placement offset relative to
  the left glyph's exit, with `provenance` (harvested/authored), a specimen
  reference and an `approved` gate. `core/compose.py` renders an approved
  override verbatim for exactly its adjacent pair (left-to-right precedence);
  with no override the generator path stays byte-identical (golden-pinned).
  `GET /sources/{id}/write/word` fetches the approved rows in one query;
  new public reads + admin-gated writes under `/sources/{id}/pairs/…` with
  registry-key and geometry validation. The harvest importer and the pair
  editor follow as the next slices.

### Changed

- **Position removal (redesign R2).** One authored form per glyph:
  glyph_keys lose their `-initial/-medial/-final` suffix (`a-medial` → `a`;
  the s-allographs untangle to `longs` — historically `s-medial` — and `s`),
  the admin fan-out/split machinery is gone, `templates.position` and
  `bboxes.split` are dropped and the identity constraint becomes
  `(style_id, glyph, variant)` (migration `0017`, which collapses sibling
  rows — a genuinely differing sibling survives as an extra `variant`, bbox
  locks are OR-merged). The word position stays per-slot render context in
  `core/shaping.py`/`shaping.ts`. Render output is unchanged: the compose
  golden fixture stays byte-identical in geometry (only key names moved).
  `architektur.md` §3 updated in the same change.

### Added

- **Admin pair matrix (`/admin/paare`, redesign R1).** Every two-letter
  combination of a chosen letter (capitals only on the left), composed
  server-side via the cacheable `/write/word` and rendered lazily per
  IntersectionObserver — an unnatural join is visible directly instead of
  hiding inside a longer word.
- **Word-specimen comparison on `/admin/vergleich` (redesign R1b, stage 1).**
  The page now has tabs — Buchstaben (the existing per-letter view) plus
  Wörter/Verbindungen/Andere Hand: every connected-writing specimen from the
  source's `words.json` sidecar next to the same word written by the engine,
  side-by-side or with the engine ink overlaid on the specimen pixels,
  registered exactly over the sidecar lineature (baseline/midband → scale);
  unauthored letters surface as `missing` chips, the other-hand plate
  (Abb. 22) is labeled as view-only context.
- **Public word-sample reads.** New `word_samples` router:
  `GET /sources/{id}/word-samples` (metadata with crop-local lineature) and
  `GET /sources/{id}/word-samples/{sample_id}/crop` (grayscale PNG, exclude
  rects painted paper-white), backed by `core/chart.py::load_word_samples` +
  `word_sample_crop_to_png_bytes` over the committed sidecar — public like
  the bbox crops (`<img>` cannot send the admin header), cached, covered by
  a new HTTP test suite.

- **Writing-system redesign proposal (`docs/proposals/schreibsystem-redesign.md`).**
  Records the accepted direction from the 2026-07-17 review: one authored
  form per glyph with the position triplication removed (R2), an admin
  pair-matrix view over `/write/word` (R1), sparse *harvested* pair
  overrides with capital-joins first as the concrete form of proposal B
  (R3), placement-residual + O3 re-evaluation (R4), and a new measured
  slant finding — the specimen hand's d-ascender loop leans ~4–5° right
  of the upright chart cell while medians match (R5). Cross-referenced
  from `docs/index.md` and `planaenderungen.md` (proposals B and D).

- **"Einen alten Brief entziffern" section on /schriftkunde.** A method-only
  five-step decipherment guide (anchors first, stock formulas, chart
  side-by-side, the classic f/ſ–n/u–e/n traps, skip-and-return) with a
  pointer to the Schreibtafel — the practical how-to the page's own intro
  audience was missing.
- **Quiz provenance caption.** The quiz setup now names its source like the
  Tafel and Federprobe do ("Nachgebildet aus der gemeinfreien
  Sütterlin-Ausgangsschrift von 1922.").
- **Structured data + meta polish.** Static `WebSite`/`Person` JSON-LD in
  `index.html`, a `twitter:image:alt`, and `<lastmod>` on every sitemap entry.
- **`docs/reference/werkzeuge.md`.** Human-facing entry point for
  glyphlab/wordlab/pairlab (exact CLI, `--live` read-only pulls, `temp/`
  output) with pointers to the bench and quizgen docs; indexed in
  `docs/index.md`.
- **Admin `useInView` hook.** `/admin/vergleich` gates each card's heavy
  diagnostic fetch behind an IntersectionObserver and lazy-loads crop images
  instead of firing ~30 JSON requests on mount.

- **HTTP tests for the admin compute endpoints + the untested public reads.**
  New `tests/test_api_compute_endpoints.py` (15 tests): `/trace-preview`
  (pressure raw/refined + the constant-style compute-once branch, dry-run
  proof), the full `/resample` 409/404/409/423 ladder incl. the legacy
  no-raw_path row, `/diagnostic` 404s + payload, `/quality` 409 without
  pixel meta + a real stored/candidate score, `/fit` 404, both chart image
  endpoints (PNG magic + cache headers), the single-glyph `/write` read,
  `/write/word` input bounds + the ligature-decompose fallback over HTTP,
  the new bbox geometry 422s, and the styles/sources/hands get-by-id 404s.
  `api/routers` coverage: templates 41→57 %, chart 47→84 %, write 61→67 %.
- **Pooled nib/pen memoisation unit tests.** `tests/test_rendering_pool.py`
  pins the TTL cache the admin-trace→public-render coherence hangs on
  (hit, expiry, explicit invalidation, no-scan for constant styles) with a
  fake repository and a frozen clock — `api/rendering.py` 68→90 %.
- **Guard against silent lab-test skip rot.** The glyphlab/wordlab/pairlab
  suites skip in CI on gitignored fixtures by design, so a renamed export
  dir would disable them forever without anyone noticing;
  `tests/test_lab_fixture_wiring.py` pins the consumers' fixture dirs to
  the exporters' output dirs and the shared manifest name.
- **Vitest suite for the glyph lock/split helpers.** `domain/glyphs.test.ts`
  (10 tests) pins `siblingKeys` (incl. the s/ſ allograph overrides),
  `isLetterSplit`'s `.some` contract and `quizKeysFromLocked` (lock-as-one
  collapse, canonical-preferring representative, split units, punctuation
  exclusion, allograph separation).
- **Own-code deprecations now fail the test suite.** The deprecated
  `HTTP_422_UNPROCESSABLE_ENTITY` starlette constant (9 accumulated
  warnings) is renamed to `HTTP_422_UNPROCESSABLE_CONTENT` across the
  routers, and `filterwarnings` turns DeprecationWarnings raised from
  `api`/`core`/`tools` code into errors — third-party warnings stay
  warnings.
- **`/verify-migrations` skill + a hardened CI migrations job.** The CI job now
  runs the full sequence — `alembic upgrade head`, `alembic check`
  (model↔migration autogenerate drift) and a `downgrade -1`/`upgrade head`
  roundtrip — against its throwaway Postgres 16; the new skill runs the exact
  same sequence locally (Docker or the container's unprivileged Postgres), so
  the shared Cloud SQL DB never sees an untested revision. This closes the
  Alembic entry in CLAUDE.md's "known gaps without a loop".
- **Post-deploy prod smoke.** `api/cloudbuild.yaml` ends with a smoke step
  against the freshly deployed revision: `/health`, `/styles` non-empty,
  `/write/word?text=lesen` returns items, and an uncredentialed write answers
  401 (fail-closed gate proven live) — a bad image that still answers /health
  can no longer ship silently.
- **Frontend coverage reporting.** `npm run test -- --coverage`
  (`@vitest/coverage-v8`) uploads to Codecov under a new `frontend` flag
  (informational patch status to start); `app/` is no longer ignored in
  `codecov.yml`, so SPA regressions become visible to the patch gate.
- **`REGEN_SHAPING=1` regen path for the shaping-twin fixture.** Mirrors the
  compose-golden pattern: a legitimate shaping change regenerates
  `tests/fixtures/shaping_cases.json` from the Python source of truth instead
  of hand-editing JSON that two suites assert.
- **Pre-commit config.** `ruff-check` + `ruff-format` hooks (same versions CI
  pins), so format-only red CI runs stop happening; ESLint stays CI-only.
- **`docs/reference/write-api.md`.** The shipped public render endpoints
  (`/write/glyphs` + `/write/word`) graduate from the proposal into a proper
  reference doc (pipeline, wire format, cache semantics, render-cache
  consumption), indexed in `docs/index.md`.

### Fixed

- **Admin writes answered with the state from *before* the write.** Every
  repository `upsert` writes through a Core insert-on-conflict the ORM session
  cannot see, then re-selects the row — and a plain re-select returns the
  instance already in the session's identity map, unrefreshed. Since the
  handlers load the row first (the bbox PUT's coalesce lookup, the `/trace`
  identity guard), every response carried the pre-write values. The setup
  wizard builds each next edit on the last response, so it re-sent a
  one-edit-old bbox: guide drags snapped back to their old position before
  jumping forward a round trip later, and every second eraser/ink stroke was
  silently dropped — erased neighbour ink reappeared as the crop "jumped back
  and forth". The three upserts (bbox, template, glyph pair) now re-select with
  `populate_existing`.
- **Wizard gestures no longer snap back for the duration of their save.** The
  in-flight drag/stroke preview (Grundlinie, Mittellinie, Schräglage, donor
  cell, eraser and ink brush) was cleared *before* the PUT resolved, so the
  guide line or stroke rendered from the still-unsaved bbox for one round trip.
  The preview now hands over to the stored value only once the commit lands,
  cleared by gesture identity so a gesture started during the save survives.
- **Cross-source render-cache poisoning.** `WrittenGlyph` seeded admin
  payloads from the runtime-switched active source under the *public*
  source's cache keys, so after a source switch in the admin, `/quiz` and
  `/tafel` could serve the wrong script in the same SPA session. The
  component now takes a `sourceId` prop used for peek/seed/fetch alike,
  threaded from all three admin surfaces.
- **Quiz word bank no longer degrades silently on cold start.** The boot
  read now retries like its siblings instead of falling back to the small
  bundled bank for the whole session after one failed fetch.
- **Out-of-chart bboxes are rejected (422)** instead of storing a box that
  later 500s the public `/crop` with a zero-size crop.
- **DELETE /templates and /bboxes return 404 for nonexistent rows** instead
  of a false 204 on a typo'd glyph key.
- **Error details no longer leak internals.** The public chart 404 hid the
  absolute container path and the style-resolution 500 its referential
  detail; specifics now go to the server log.
- **`/hands` responses carry the shared Cache-Control** like styles/sources.
- **`/fit` query params are bounded**; `require_db`'s 503 distinguishes
  "not configured" from "initialisation failed".
- **Quiz results word render falls back to plain type on error** instead of
  spinning forever after a cache eviction + failed refetch.
- **`/diagnostic` is admin-gated like its compute siblings.** The 3-column
  diagnostic re-runs the image pipeline (chart decode + binarise +
  skeletonise, ~0.2 s CPU) per request; `/fit` and `/quality` were gated for
  exactly that reason but `/diagnostic` stayed public and uncached on the
  max-instances=1 service. Only admin surfaces consume it — the public
  renderer reads the cached `/write` payloads. The admin-gate HTTP test
  matrix now includes it.
- **Structural uniqueness for `glyph_key`.** Every template read — including
  the public `/write` endpoints — keys on `glyph_key` via
  `scalar_one_or_none()`, so two rows sharing `(style, glyph_key, variant)`
  would turn every read into a 500; the API's 409 backstops are
  read-then-write and bypassable out of band. Migration 0015 adds the unique
  constraint (mirrored in the model), making the backstops UX instead of the
  only defense.
- **Bbox saves reject degenerate rectangles.** `PUT /bboxes/{key}` accepted
  inverted or negative rectangles (`x1 <= x0`, `y1 <= y0`), which stored fine
  and then 500ed the public crop/derivation paths on an empty crop; the
  handler now 422s with a clear message, alongside the existing
  baseline/midband check.
- **Cross-source pen-pool invalidation.** A style can pool from several chart
  sources (Kurrent: loth-1866 + petzendorfer-1889); a trace/resample/delete
  issued through source A that touches a template whose provenance is B left
  B's pooled nib/pen stale for the 10-minute TTL. Template writes now clear
  the whole style's pools (they are tiny), with a unit test pinning it.
- **Cache-Control on the remaining public reads.** `GET /bboxes/status` (the
  quiz boot) and the crop PNGs (quiz prompt fallback; the wizard busts via
  its version param) now carry the shared public cache header; `GET
  /templates` deliberately stays uncached — the admin sidebar reads the same
  list and needs a fresh `has_data` right after a trace, and the code now
  says so.

- **Fact-checked public copy, with the fact sheets updated to match.** A
  research pass with primary sources settled the audit's content findings:
  the Schriftkunde chronology note claimed the Swiss cantons dropped Kurrent
  "um 1900" while the geography section of the same page (correctly, per the
  cited ZB Zürich source) says 1890–1930 — the note now matches. The 1941
  passage attributes the "foreigners can't read it" justification precisely
  (Lammers, Chef der Reichskanzlei, forwarding note of 13 Jan 1941) and the
  fact sheets now name Bormann's party-office circular (3 Jan), Lammers'
  forwarding (13 Jan) and the Reich education ministry's school decree
  (1 Sept) with sources. The Gleichzugfeder blurb no longer claims Sütterlin
  "setzte sich in den 1920er Jahren durch" (Prussia from 1915, most Länder
  only around 1930). The Sütterlin-never-in-Switzerland claim is now backed
  by a direct ZB Zürich quote in the fact sheet, and the Swiss 1890–1930
  range gained an academic reference (Boser/Hofmann 2019).
- **Quiz gloss for "Gulden": silver, not gold.** The 19th-century South
  German Gulden was a silver coin (only the name derives from the medieval
  gold "guldin"); the generator source, `quiz_words.json` and — via new
  migration 0014 — the already-seeded DB row now read "alte Silbermünze
  (süddeutsche Währung)".
- **Impressum/llms.txt no longer overclaim synthesis.** "Alle gezeigten
  Schriftzüge sind … kein historisches Original" contradicted the
  Schreibtafel's genuine public-domain scans and the Koch 1928 original on
  /schriftkunde; both texts now distinguish synthesized forms (marked as
  such) from the PD originals shown with provenance. The privacy section's
  "keine personenbezogenen Daten" now carves out the 30-day server logs the
  same page already discloses (IPs are personal data).
- **Copy polish across the public pages.** Landing no longer claims all
  three scripts are engine-written ("die Sütterlin schreibt hier schon");
  the Federprobe card invites a word *or short sentence* (the input takes
  48 chars); "↻ noch einmal schreiben" matches the other replay labels;
  the worksheet intro gains its missing article; the written-glyph aria
  label says "alte Schreibschrift" instead of naming Kurrent while the
  engine writes Sütterlin; trailing ellipses uniformly get their narrow
  space; the Schwellzug explainer no longer has the *pen* swelling; the
  show-script font is consistently "GL-GermanCursive"; the sources intro
  points readers to the GitHub fact sheets.

- **Straight-quote pairing spans the whole text, not one word.** The shaping
  twins (`core/shaping.py` + `app/src/domain/shaping.ts`) reset the
  low/high quote parity per whitespace-split word, so a multi-word quote —
  `"Guten Tag"` in the Federprobe — rendered two opening „ quotes. The parity
  now threads through `shape_text`/`shapeText`; the shared fixture gained the
  multi-word case and was regenerated via `REGEN_SHAPING=1`.
- **Quiz word prompt no longer spins forever on a failed compose.** The word
  branch of the question card passed no `onError` to `WrittenWord`, so a
  compose request that died mid-cold-start (the render cache's retry budget is
  much shorter than the boot loads') left an infinite `CircularProgress`. The
  prompt now offers the same retry affordance as the Federprobe — a plain-type
  fallback would hand the solution to the learner, so it retries instead; the
  post-answer comparison forms fall back to plain type.
- **Quiz keyboard focus survives a correct answer.** Focus moved to "Weiter"
  only on a wrong pick; on a correct one every answer button disables and focus
  fell to `<body>` — reduced-motion users got a "Weiter" button that never
  received focus, everyone else lost their tab position each auto-advance. The
  advance control now receives focus on every verdict, and after the advance
  focus returns to the answer grid.

- **`quiz_words.created_at` is NOT NULL like every other `created_at`.**
  Migration 0010 forgot `nullable=False` (0004 declares it on all other
  tables) while the model implies NOT NULL — the very first `alembic check`
  run caught the drift; migration 0013 tightens the column (safe: it carries
  `server_default=now()`).

- **Slim public reads for the heavy list payloads.** New
  `GET /sources/{id}/bboxes/status` returns only the availability flags
  (glyph_key, locked, split) and `TemplateRepository.list_summaries()` feeds
  the template list from a column-select — the admin sidebar and the public
  quiz no longer decode multi-MB of `raw_path`/`anchors`/mask/ink/patch JSONB
  for six scalar fields. The quiz left the pinned AdminProvider entirely: a
  new `useQuizSource` hook boots from source + template summaries + status
  flags (same cold-start retry), so `/quiz` stops downloading the full
  crop-editing bbox payload.

- **jsx-a11y lint gate.** `eslint-plugin-jsx-a11y` (recommended rules) now runs
  in the frontend lint, so the mechanical accessibility slips on the SVG-heavy
  custom surfaces get caught before review.
- **`PaperCardLink` + `PaperCardCta`.** The public "paper card that is a link"
  (hover/focus lift, viridian border, focus ring, CTA underline sweep) that
  LandingView, HubView and the Schriftkunde try-cards each copy-pasted is now
  one shared component — contrast and focus fixes land once.

- **Authorized admin-write and Cloudflare-Access test suites.** New
  `tests/test_api_admin_writes.py` exercises the gated handlers with a CORRECT
  token: bbox PUT/GET roundtrip incl. the coalesce contract (omitted
  `locked`/`n_anchors` preserve stored values), the full `/trace` pipeline
  against the on-disk synthetic chart (persisted template, list `has_data`,
  bbox anchor-count sync), the 423 lock + `force` override, and DELETE
  semantics for bboxes and templates. New `tests/test_api_auth.py` covers the
  JWT branch that actually gates prod: listed email → authorized, unlisted →
  hard 403 (no token fallback), unverifiable JWT → break-glass token path, plus
  unit tests of `_verify_cf_access_jwt` (lowercasing, PyJWTError → None,
  missing email claim, unconfigured). The shared ASGI harness moved from
  `test_api_http.py` into `tests/api_harness.py` + a conftest `api` fixture so
  all three API suites reuse it.
- **HTTP-level API test suite + an Alembic migration check in CI.** New
  `tests/test_api_http.py` runs the FastAPI app under pytest against an
  in-memory aiosqlite session (dependency-overridden `get_db`, no
  Postgres/network): the admin gate (401 on missing/wrong token, fail-closed
  503 when unconfigured) is asserted for every write endpoint incl. the newly
  gated `/fit` + `/quality`, plus Cache-Control on the public reads and
  `/write/glyphs` + `/write/word` end-to-end with synthetically seeded
  templates. A new `migrations` CI job runs `alembic upgrade head` (schema +
  seeds) against a throwaway Postgres 16 service on every PR, so a broken
  revision can no longer reach the shared Cloud SQL instance. Vitest gains
  `renderCache.test.ts` (request batching, in-flight dedupe, cache hits,
  missing-as-null, error eviction, cold-start retry).
- **Brand icons + social preview image.** `favicon.ico` (multi-size),
  `apple-touch-icon.png` and a 1200×630 `og.png` — the viridian Kurrent K on
  the paper gradient, rendered from the bundled GLKurrent face — wired into
  `index.html` with a `summary_large_image` twitter card; link previews and
  browser tabs stop being generic.
- **Shareable Federprobe.** The typed text syncs to a `?text=` URL parameter
  (debounced, history-friendly) with a "Link kopieren" button and a character
  counter on the input — the page's output is now deep-linkable.
- **"Jetzt ausprobieren" cross-links on `/schriftkunde`.** The primer closes
  with hub-style cards into the quiz, the Schreibtafel and the Federprobe
  instead of dead-ending after the chronology.
- **Chart image LRU cache + Cache-Control on stable reads.** Decoded chart
  grayscale arrays are cached per resolved path (read-only, max 4 entries), so
  repeated crops/diagnostics/fits stop re-decoding the same immutable PD scan;
  `/styles` and `/sources` responses now carry the shared cache policy and the
  chart image caches for a day.
- **Direct unit tests for the pure-math core modules + a mechanical shaping twin
  guard.** New `tests/test_geometry.py` and `tests/test_widths.py` pin the
  deterministic numeric helpers in `core/geometry.py` (tangents, arc length,
  curvature, straightness residual, TLS line fit, vertical-run/crossing/retrace
  detectors) and `core/widths.py` (the `BroadNib` law + vectors, per-stroke
  tangents, every `resolve_half_widths` branch) with known inputs/outputs, so the
  upcoming core-dedup refactor has a behavioural net; `_locally_straight_mask`
  gains direct coverage in `tests/test_quality_components.py`. The
  `core/shaping.py` ↔ `app/src/domain/shaping.ts` twin is now enforced by a shared
  fixture (`tests/fixtures/shaping_cases.json`, generated from the Python source of
  truth) asserted by both `tests/test_tri_script.py` and a new Vitest test
  (`app/src/domain/shaping.test.ts`) — mutating one shaping without the other fails
  CI. Wires a `test` script + `vitest` into `app/` and a Vitest step into the
  frontend CI job (build-only before).
- **Third wordbench set: the Abb. 22 Schülerschrift plate (cross-hand reference).** The
  1922 Leitfaden's only other connected Ausgangsschrift specimen — a pupil's hand
  (Bruno Krüger, 3rd school year, Breitkantfeder, 106 words of Hoffmann von
  Fallersleben's "Hab' Dank, du lieber Wind!") — is now measured like Abb. 19
  (`words-abb22.png` + 106 sidecar entries, boxes proposed, line-QC'd and hand-corrected).
  Sidecar entries carry a new optional `set` field; `export_fixtures`/`run`/`wordlab`
  accept custom set names, so the plate freezes into its own sibling fixture root
  (`suetterlin-1922-abb22`, `--set abb22`) and its cross-writer numbers are never averaged
  into the same-hand headlines. Provenance + PD rationale in the source's `SOURCE.md`.
- **ESLint gate for the SPA.** Added a flat `app/eslint.config.js` (JS +
  typescript-eslint recommended + `react-hooks`, react-refresh as warnings),
  a `npm run lint` script, and an ESLint step to the CI frontend job — the
  `react-hooks/exhaustive-deps` suppressions in the tree are now enforced
  instead of inert. Fixed the findings this surfaced: `prefer-const` in
  `TafelView.tsx`, a missing hook dep in `RederiveAllDialog.tsx`, and added
  the missing justification to a `WrittenWord.tsx` suppression; kept the
  `_`-prefix unused-args convention and allowed intentional non-breaking
  spaces in UI strings. Updated `.github/copilot-instructions.md` to record
  that ESLint is now configured.
- **`tools/pairlab` — independent-fit dissection of letter joins.** For every real
  occurrence of a letter pair in the Abb.-19/Abb.-20 specimens it re-fits each letter
  INDEPENDENTLY onto the frozen skeleton (bounded translation grid), regenerates the
  production connector between the two placements (same constants/guards as
  `core/compose.py`), tracks the specimen's own connecting stroke through the
  inter-letter gap, and measures tail/head adaptation profiles — how far into each
  glyph the real pen departs from the template before the join. Separates the three
  entangled failure modes (connector shape · placement · glyph-end adaptation) the
  word bench cannot tell apart. Additionally it TRACES the real pair along the known
  ductus: the M4 fit (`core/fit.py`) warps both templates onto the specimen ink, so
  every occurrence yields its ground-truth target — true coupling heights/tangents
  per join class and the stub-trim signal (fitted endpoint vs. tracked departure).
  Overlay + deviation-profile PNGs per occurrence, JSON aggregation, unit-tested
  pure geometry core (`tests/test_pairlab.py`).
- **Transition findings 2026-07-11** (`docs/proposals/uebergaenge-befund.md`): the
  pairlab survey over 87 occurrences / 45 pairs. Placement is the largest single
  error (39/87 need ≥ 0.25 xh correction); the standard diagonal join is generically
  right once letters sit correctly (f→e/t→e's bench penalty was placement); high
  exits (d loop, o/b/v/w Deckstrich bows, the r arm) systematically REPLACE both
  coupling stubs (0.2–0.4 xh per side) with one diagonal into the next letter's
  first-downstroke apex — confirming the stub hypothesis class-wise, not per pair.
  Solution options O1–O3 (placement first, coupling anchors, gated pair overrides)
  with cross-references from `qualitaetsmetrik.md` §6 and Vorschlag B.
- **Connectors follow the school hand's join grammar.** The jul09/10 join audit (all
  generated Übergänge ranked with seam-kink angles against the Abb. 19/20/22 specimens)
  adds the plates' entry-class join grammar on top of the jul11 coupling composer:
  arcade entries (n m i u …) that must lose height now couple low through a baseline
  garland that merges tangentially onto their lead-in line (bi/on originals), the r-arm
  sets off with its authentic Absatz corner before a deep garland, clamped bow exits
  roll G1 over the crest instead of cornering (the b→e "extra Zacken"), sawtooth pairs
  (e→n family) pull onto one continuous diagonal instead of leaving a mid-height shelf,
  and the low-exit word-final Endstrich is a two-tangent quadratic that flattens like the
  plates (short flick after descender exits) while high forward exits keep the jul11 level
  Auslauf. Round bodies after a high exit stay on the jul11 rising-flank coupling anchor
  (O2), which subsumes the garland there. Measured standalone against the pre-jul11 base
  the grammar scored words 0.1253 → 0.1241 / pairs 0.1992 → 0.1927; the combined headline
  on top of jul11 was not re-measured in the merge environment (the wordbench needs the
  shared DB), but both composer unit-suites (`test_compose_coupling`, `test_compose_joins`)
  pass and the compose golden fixture is deliberately re-pinned.
- **WCAG AA contrast for viridian text and the quiz answered state.** New
  `paper.viridianText` (#2e6152 — derived for contrast, not a period hex;
  5.15:1 on the paper ground vs 3.28:1 for the accent #40826d) is used
  wherever viridian is body-size text: card CTAs, the hub/landing links, the
  quiz score and verdict, the Scribe copy confirmation, Tafel chip/provenance
  links, prose-link hovers. `quiz.resolvedText` darkened to #6e5c42 (5.5:1 on
  the answered button face, was 3.61:1). The accent #40826d stays for large
  display, initials, borders, fills and focus rings.
- **Contiguous heading outline on every public page.** Card titles now carry
  explicit heading components (hub cards `h2` under the page `h1`; landing,
  Schriftkunde and Tafel cards `h3` under their `h2` section headings), and
  MUI's default subtitle→`<h6>` mapping is overridden to `<p>` at the theme
  level — definition-row terms and timeline years no longer appear as phantom
  section headings to screen readers.
- **The nav marks the current area.** PublicHeader links carry
  `aria-current="page"` plus a visible active state (ink colour + full
  viridian underline) for the area whose page is open.
- **`/trace` can no longer cross-link template rows.** The template upsert
  conflicts on `(style, glyph, position, variant)` while reads go by
  `glyph_key`, so a client bug pairing a wrong URL key with a payload identity
  could conflict-update another row and rewrite its `glyph_key` — reads then
  silently 404 on the shared prod DB. `POST /trace` now derives the expected
  key from the shared registry (`core.shaping.expected_glyph_key`, the Python
  twin of `glyphs.ts`; `{base}-{position}` convention as fallback) and rejects
  a mismatch with 422.
- **DB engine init race closed.** The lazy `asyncio.Lock` getter in
  `core/database/connection.py` was itself check-then-set, so two first
  requests could each mint their own lock, both enter `init_db()`, and the
  loser's engine (and Cloud SQL connector) leaked without `dispose()`. The
  lock is now created at import; the dead `_sync_init_lock` is gone.
- **No more raw English error strings on public pages.** `/quiz` and `/tafel`
  showed `String(e)` (e.g. "TypeError: Failed to fetch") as the BootStatus
  detail under a German title; both now show a fixed German sentence
  (`common.boot.sourceUnreachableDetail`) and log the exception to the console.
- **A late word-compose rejection can no longer evict a fresh cache entry.**
  `fetchRenderWord`'s error eviction now checks entry identity before deleting
  (like the glyph cache): after a FIFO eviction + re-fetch under the same key,
  the old promise's rejection used to delete the new, valid entry.
- **The nav's current-area marker covers the standalone tool routes.** /quiz
  and /tafel light up Lesen, /federprobe lights up Schreiben (they keep their
  stable top-level URLs and are not nested under the hubs); only the exactly
  matching page uses `aria-current="page"`, area membership uses `"true"`.
- **CHANGELOG `[Unreleased]` consolidated to one heading per category.**
  Successive PR insertions had produced duplicate Added/Changed/Fixed headings
  with bullets filed under the wrong category; regrouped per Keep-a-Changelog.
- **The Cloud SQL connector fallback is now truly async.** The
  `INSTANCE_CONNECTION_NAME` path built a *sync* pg8000 engine and handed it to
  `async_sessionmaker(..., class_=AsyncSession)` — the first session would have
  raised `ArgumentError` and `close_db` would have crashed on `await
  engine.dispose()`; it now uses the native async Cloud SQL Connector with an
  asyncpg `async_creator`. A failing lazy `init_db()` in the session dependency
  is also caught and surfaces as the clean 503 instead of an unhandled 500.
- **Wizard brush commits can no longer overwrite each other.** All bbox writes
  are serialized through one queue and compute their payload from the
  then-current bbox at write time — two quick eraser/ink strokes (S-Pen taps
  faster than the PUT round-trip) used to both build on the same stale state,
  silently dropping the first stroke. Bbox saves also stopped echoing a stale
  `n_anchors` back, which used to revert the server-side sync with the derived
  canonical (`_sync_bbox_anchor_count`); and the canvas renders committed
  strokes/patches/saved-trace through memoised layers, so a 240 Hz pen gesture
  only re-renders the in-flight stroke.
- **Federprobe and Schreibtafel fail loudly instead of silently.** A failed
  compose fetch on `/federprobe` now shows an error message with a retry button
  instead of an endless spinner, and a failed letter batch on the Tafel shows a
  notice + retry instead of silently rendering an empty ruled sheet.
- **Mask preview halves its binarisation work.** The "Maske zeigen" preview
  derives the filled mask from the already-thresholded raw mask via
  `fill_small_holes` instead of running the adaptive threshold twice
  (identical output).

### Changed

- **CORS is now environment-scoped.** Production allows only the
  `kurrentschrift.ink` origins; the localhost/LAN developer conveniences no
  longer apply to prod (where `allow_credentials` rides the CF Access
  cookie). An env override remains available.
- **Template writes commit before invalidating the pooled-nib cache**, so a
  concurrent public read can no longer repopulate the 600 s TTL cache from
  pre-write state.
- **Ligatures require both characters lowercase** in the shaping twins
  (Python + TS): `sT` / `McHale` no longer swallow capitals into
  `longst`/`ch` ligatures; pinned by new shared fixture cases.
- **Wizard stroke capture stores relative timestamps.** Points now carry
  `performance.now() - traceEpoch` instead of a `t=0` first point followed
  by raw epoch values — saved traces become usable for the post-MVP
  velocity/style analysis.
- **Quiz play/results panels use semantic headings and the type ladder.**
  Section titles are real `h2`/`h3`s in ladder variants (Playfair-600 rule);
  ad-hoc pixel sizes are mapped to the nearest rung, deliberate display
  figures are marked as such.
- **Public copy audit fixes.** The Gleichzugfeder paragraph no longer calls
  the *pen* a school script; the 1915 timeline entry drops the four-year
  hedge; the Schriftkunde lead anakoluth is split; the Tafel intro says
  "Schreibvorlagen" instead of claiming "die drei Ausgangsschriften"; the
  hero caption is honest about being type, not the engine; the quiz SEO line
  no longer overclaims; the Federprobe page finally carries its own name as
  the h1; "kuratiert" jargon is replaced; the worksheet uses the DIN/Süß
  terms (Ober-/Mittel-/Unterlänge, "Mittellänge (Schreibhöhe)") instead of
  Band/x-Höhe.
- **Impressum wording made defensible.** EU data-centre claim now names
  Google/Cloudflare as US providers certified under the EU-US Data Privacy
  Framework; the rights paragraph is reconciled with the 30-day server logs;
  date bumped to July 2026.
- **Quiz gloss corrections.** "Groschen" (era-scoped: 10-Pfennig piece only
  in the Kaiserreich) and "Witwe" (precise definition) fixed in the
  generator, the regenerated word bank, the bundled fallback bank, and
  in place via migration `0016_quiz_gloss_fixes`.
- **The quiz is named "Lese-Quiz" in the UI too.** The six "Buchstaben-Quiz"
  strings (page title, hub/landing/Schriftkunde cards, SEO title) and the
  letters-only SEO/landing descriptions now match the shipped scope
  (letters + whole words), consistent with the docs rename below.
- **Docs sync.** copilot-instructions' schema section now states both
  template unique constraints (the `(style_id, glyph_key, variant)` one
  shipped in 0015) instead of calling `glyph_key` UI-only;
  `write-api.md` documents the single-glyph read; the letter quiz is renamed
  to the shipped reading quiz (letters + words) across README/docs/guides;
  the two agent guides agree on read-first and language rules; implemented
  proposals are annotated in `docs/index.md`; README explains the
  Sütterlin-first validation order and lists `tools/`/`tests/`.
- **Cloud Run request timeout lowered to 60 s** (from 600) — nothing
  legitimate runs ten minutes.
- **Deploys go no-traffic → smoke → promote.** `api/cloudbuild.yaml` used to
  route 100 % of traffic and only then smoke — a bad revision served users
  until the build went red. The deploy now carries `--no-traffic` +
  `--tag=candidate` + a deterministic `--revision-suffix`, the smoke suite
  probes the candidate's tag URL (and asserts the tag still points at this
  build's revision), and a final `update-traffic --to-revisions` step promotes
  exactly the smoked revision — never a concurrent build's unsmoked one.
- **The Tafel boots from the slim bbox read.** `BboxStatusOut` gains the six
  layout scalars (`x0/x1/y0/y1/baseline_y` + flags) the sheet layout needs,
  and `useGrundtafeln` switches from the full `BboxOut` list — the same
  multi-MB mask/ink/patch JSONB payload the quiz was weaned off in the last
  audit round — to `GET /bboxes/status`. The three chart scans (~1.4 MB of
  JPEG, two below the fold) now load lazily like the other public images.
- **One version source for the API.** `api/main.py` read `0.2.0` while
  pyproject said `0.1.0` and the last release was 0.13.0; `/docs` now reads
  `project.version` from the shipped `pyproject.toml` (bumped to 0.13.0), and
  the release note covers the bump.
- **pre-commit runs ruff through uv.** The mirror-based hooks pinned their own
  `rev` that Dependabot never bumps — pre-commit-green/CI-red was weeks away;
  the hooks are now `repo: local` `uv run --extra dev ruff …`, so uv.lock is
  the single ruff version source.
- **Palette rgba literals replaced with `alpha(token, …)`.** The quiz panels
  and the Tafel sheet baked `paper.viridian`/`pigment.vermilion`/`paper.line`
  into rgba strings a palette retune would silently miss — `PublicHeader`'s
  bar background had in fact already drifted from a pre-retune `paper.bg`
  (rgb 231,221,193 vs the token's 231,218,191); all derive from the tokens now.
- **Docs drift pass from the audit.** `animation-rendering.md` §1 now
  describes the SHIPPED engine — WAAPI via `useStrokeReveal`/`el.animate`
  with two-thirds-law keyframes and isochrony from `lib/strokeTiming`, not
  the "CSS keyframes, constant speed" it claimed — and its §3 sketch uses the
  real `width_resolver == "constant"` property and the `/write` payload path;
  the `/open-pr` skill learns CI's third job (migrations) and the
  `/verify-migrations` precondition; `CITATION.cff` catches up to release
  0.13.0/2026-07-09 and the CHANGELOG header makes the bump part of every
  release; `quiz-wortbank.md` states the real 75/25 modern/historic ratio
  (was 60/40); `docs/index.md` names the full library tuple
  `(style, glyph, position, variant)` and a current status line;
  `frontend-stack.md`'s route map stops claiming a live-written hero;
  `design-system.md`'s colour table gains the shipped `paper.viridianText`
  token + its usage rule; `planaenderungen.md` Vorschlag D gets a status
  note (core/shaping.py is the shipped precursor; the `glyphs` table is
  `templates` since 0004); `[Unreleased]` regrouped to one heading per
  category.
- **CI frontend job on Node 22** (20 reached EOL 2026-04-30); `app` engines
  field now requires `>=22`.
- **Docs and agent-surface refresh from the audit.** `.claude/commands/prime.md`
  rewritten from the current repo layout (it described the pre-library-schema
  world: `glyphs.py` router, `constants.ts`, `state.tsx`); `verify-api` skill
  aligned with reality (admin-gated `/fit`+`/quality`, four seeded sources,
  `/write/*` + `/quiz-words` + `/bboxes/status` in the sweep); `verify-core`
  drops stale test counts; `verify-frontend` drops the obsolete favicon-404
  gotcha and describes the render-cache quiz boot; `write-docs` matches the
  real `docs/index.md` structure (notes/ IS indexed, `schriftkunde/` exists);
  CLAUDE.md corrections (hero is font-first with an open engine seam,
  koch-1928 is a live seeded source, migration 0008 listed, known-gaps
  updated) mirrored to `.github/copilot-instructions.md` (CI = three jobs);
  `naming-und-setup.md` §1 reflects the Sütterlin pivot; `docs/index.md`
  prose sections list style-guide/design-system/federmodelle/qualitaetsmetrik;
  `frontend-stack.md` names `HeroWritten` and clarifies "keine eigene
  Komponenten-Bibliothek"; `animation-rendering.md` §1 describes the
  render-cache data path; `contributing.md` names the full live feature set;
  `sprachregelung.md` documents the EN-proposals exception.
- **Public copy pass from the content audit.** /schriftkunde's intro no longer
  switches to Sie-form on an otherwise du-form site; German closing quotes are
  typographic („…“) everywhere; the hub/SEO texts stop promising trace-along
  words the worksheet generator doesn't produce and stop overclaiming the
  Tafel ("jeder Buchstabe, wie ihn die Feder schreibt" → only the Sütterlin is
  engine-written); the landing quiz card stops calling the Sütterlin-only quiz
  "Kurrent-Buchstaben" (and fixes "weist" → "zeigt"); quiz feedback "Super
  Übereinstimmung" → "Richtig gelesen."; quiz/tafel availability notes use the
  same wording (freigegeben instead of admin-jargon "kalibriert und gesperrt");
  the worksheet tool is consistently named "Übungsblatt" and the presets
  "Ausgangsschrift"; fact fixes against docs/schriftkunde: Sütterlin school
  introduction 1915 (Prussia) / ~1930 elsewhere instead of "1920er Jahre" and
  "Schulschrift von 1911", the Swiss phase-out 1890–1930 instead of "um 1900",
  the ß note now attributes the ſ+s reading to the Antiqua tradition, the
  1915/1918 timeline entry carries the divergent-sources caveat, and Kurrent is
  "die alte Alltagsschrift, ohne einheitliche Norm" instead of "die ältere
  Norm"; grammar fixes ("Das Schreiben lernte man …", "niederschrieben");
  the static `<title>`/description in `index.html` now match the SEO catalogue
  (full home title for no-JS crawlers, description trimmed to ~155 chars).
- **`/fit` and `/quality` are admin-gated; the crop endpoint leaves the event
  loop.** Both diagnostics cost seconds of pure CPU per call and back
  admin-only workflows, so they now require the admin credential like the
  writes (the SPA already sends it on every request); `GET /crop` runs its
  chart decode + binarisation in the threadpool like the other CPU-bound
  endpoints instead of freezing concurrent public requests.
- **Admin locale namespaces left the public bundle.** The `admin`/`wizard`
  message catalogs moved from the shared locales barrel into a new
  `@/locales/admin` superset barrel imported only by admin code — ~24 kB of
  admin-only German strings no longer ship to every visitor (locales chunk
  51.7 → 45.5 kB gzip).
- **Boot states keep the navigation, and the cold-start copy speaks German,
  not ops.** The quiz and Tafel cold-start/loading/error states render inside
  the public layout (header + footer stay usable through the ~47 s worst
  case), and the boot message now says the server is waking up instead of
  "Cold Start".
- **Accessibility polish on the public pages.** The quiz verdict line is an
  `aria-live` region and focus moves to "Weiter" after a wrong answer (the
  disabled answer buttons used to drop focus on `<body>`); landing cards and
  header nav links gained visible `:focus-visible` outlines; the Federprobe
  disclaimer switched from the too-light `sepiaFaint` to readable `sepia`; the
  404 page sets its own title.
- **Portable JSON column type.** Model columns now declare
  `JSON().with_variant(JSONB, "postgresql")` — identical behaviour on
  Postgres, creatable on SQLite for the new API test harness; migrations keep
  their own explicit JSONB types.
- **Docs refreshed to current reality.** The agent guides
  (`copilot-instructions`, `CLAUDE.md`) now describe the live two-service
  Cloud Run deployment, the CI-gated Vitest suite and the full UI inventory
  (`inkReveal`, `InfoHint`, `tafel/`, `impressum/`, `/admin/vergleich`);
  `frontend-stack.md` §2/§7 carry the real route map (three areas, hubs,
  `/federprobe`, `/tafel`) with planned P1+ routes split out; the README's
  "what you can use today" covers Schriftkunde, Tafel and Federprobe;
  `style-guide.md` §3 states the 19/17/14 px type floor;
  `sprachregelung.md` documents the English `contributing.md` exception;
  `mvp-roadmap`/`architektur` §16/`qualitaetsmetrik`/`docs/index` status
  lines corrected.
- **Deduped shared geometry/payload helpers and decomposed the oversized `core/`
  functions (no behaviour change).** The two canonical derivations now share one
  `_assemble_canonical_payload` (+ `_serialize_raw_path`) in `core/pipeline.py`
  instead of ~45 near-verbatim lines each — the pixel→template normalisation,
  entry/exit tangents, raw-path pen-lift serialization and the wire dict live
  once; the per-script differences (`method`, the Sütterlin `nib_radius_px`/
  `smooth`/`vertical` keys and the snap/refine notes) ride in one `method` string
  plus an `extra_trace_meta` dict. `bilinear` moved from `core/fit.py` to
  `core/geometry.py`, so `core/quality.py` and `core/quality_suetterlin.py` sample
  the shared field without importing the heavy `fit` module; `suetterlin`'s
  `_unit_tangents` now reuses `geometry.unit_tangents` and `compose`'s `_median`
  reuses `statistics.median`. The multi-closure giants are stage-extracted into
  named module-level helpers: `compose_word`'s pen/Endstrich/connector geometry
  became `_apply_pen`/`_endstrike_centerline`/`_connector_centerline`, and
  `fit_template_to_instance`'s objective/energy closures became an `_InstanceFit`
  dataclass mirroring the existing `_RefineRound` idiom. The compose golden fixture
  stays byte-identical and the full core suite is unchanged.
- **Unified the "as written" ink-reveal across the three surfaces into a shared
  primitive.** `WrittenGlyph`, `WrittenWord` and `WrittenSheet` each
  reimplemented the identical SVG reveal technique (y-negated centerline paths,
  the `feTurbulence`/`feDisplacementMap` ink-bleed filter, the swept
  `stroke-dashoffset` mask, the iron-gall settle, the faint baseline/midband
  guides, the replay button). That lives once now in
  `app/src/components/inkReveal` (`InkBleedFilter` · `RevealMask` · `InkGuides` ·
  `ReplayButton` · `inkGroupSx` settle helper); the y-negating polyline path
  moved to `lib/svg.ts` (`polylineToPathD`, replacing the three per-file
  `pathD`/`lineD` copies); and the timing magic numbers moved to
  `lib/strokeTiming.ts` as named, justified defaults plus one shared
  `sequenceReveal` cursor walk — reconciling the drifted pen-lift pause (was
  110/130/150 ms across siblings → one `PEN_PAUSE_MS = 130`). The three surfaces
  are now thin consumers. No SVG/filter/timing behaviour change beyond that pause
  reconciliation.
- **Folded `WrittenWord`'s private `/write/word` cache into `renderCache.ts`.**
  The composed-word FIFO cache lived in a second module-level `Map` inside
  `WrittenWord` with its own key scheme, undermining the "ONE shared render
  cache" invariant. It is now `fetchRenderWord` alongside the glyph cache
  (same key helper, same cold-start retry, same evict-on-error) — no private
  render cache remains outside `renderCache.ts`.

- **Trimmed `app/src/domain/shaping.ts` to the quiz-gating subset.** With word
  composition living server-side (`core/compose.py`), the TS shaper only needs the
  `text → glyph_keys` mapping the quiz word-bank gating consumes (`shapeText` +
  `glyphKeysOf`). Dropped the now-dead exports `decomposeLigatureSlot` and
  `stripFugen`, and made `shapeWord`/`FUGE` module-private; the header note now
  states the reduced scope and points at the shared fixture that keeps the mapping
  in sync with `core/shaping.py`. No runtime behaviour change (the quiz imports are
  untouched).
- **API helper consolidation (no behaviour change).** Collapsed copy-pasted `api/`
  boilerplate onto single sources of truth: `resolve_render_context(source, db)` in
  `api/rendering.py` now resolves the style + source-pooled nib/pen for every write and
  template render path, so the "constant nib if constant else None" branch lives in one
  place; `Bbox.to_pipeline_dict()` is the ONE crop-affecting serializer consumed by the
  crop preview, the trace/resample/diagnostic derivation and the bbox read response (a
  new crop-affecting field can no longer be added to one and dropped from the others);
  `put_bbox` loads the stored row once and coalesces the optional fields via one
  `_coalesce` helper; `CACHE_CONTROL` moved to a shared `api/http.py`; the `n_anchors`
  bound is one `NAnchors` annotated type and `QuizWordOut.era` is a
  `Literal["modern", "historic"]`; `GET /styles` fetches all sources in one query and
  groups in Python (no more per-style N+1, chart `.exists()` memoised); and the router
  `HTTPException`s use named `status.*` constants. Response shapes are unchanged.
- **Pairlab-calibrated placement (O1).** `core/compose.py` places letters with two
  measured corrections: a HIGH exit is treated as a coupling-stub tip, not the pen's
  true departure — the next letter tucks back under it proportionally to the exit
  height (`TUCK_RATE`·(exit − 0.6)⁺; the d-class needed −0.33 xh) — and a BACKWARD
  exit tangent (the w/v bow) gets `BACKWARD_INK_CLEARANCE` 0.30 instead of 0.14 (the
  join must clear the whole bow; w joins measured +0.23 xh too tight). Re-measured
  against the pairlab independent fits over all 48 scorable specimen words: joins
  needing ≥ 0.25 xh correction drop from 31 to 21 of 146 (d-class −0.33 → −0.07,
  w-class +0.23 → +0.08 median).
- **Coupling anchors for high-exit joins (O2, B side).** After a Deckstrich bow,
  d-loop or r-arm exit (≥ 0.7 xh) the generated connector no longer bridges to the
  next letter's entry-stub foot ("shelf") but falls onto the RISING flank of its
  first downstroke at y 0.78, and the chart cell's stub piece below the anchor is
  removed from the centerline and the filled silhouette (new
  `core/template.py::erase_silhouette_piece`). Word-initial stubs stay — they are
  the Anstrich; low arcade joins are untouched (the standard diagonal is generically
  right per the pairlab findings).
- **Level Auslauf for high word-final exits.** A word ending on a high forward exit
  (the r-arm) now runs a short level finishing stroke (0.25 xh) like the plates,
  instead of stopping dead at the arm end — `der`/`der-2` carried the bench's
  largest width penalties for the missing stroke. Words ending low keep their
  rising Endstrich.
- **Word bench headline** 0.1253 → 0.1183 (−5.6 %) over the frozen `jul08`
  references; `pair_loss` (report-only) 0.199 → 0.195. Loop protocol, keeps,
  discards (incl. the measured-but-rejected A-side d-stub trim) in
  `docs/reference/qualitaetsmetrik.md` §6, Lauf `jul11`; the compose golden fixture
  is deliberately re-pinned.
- **Doc & instruction-sync hygiene.** Re-aligned `.github/copilot-instructions.md`
  with `CLAUDE.md`: corrected the stale "no tests exist yet", "ruff/ESLint when
  configured" and "no automated AI workflows configured" claims (a pytest suite,
  ruff, and `.github/workflows/ci.yml` all exist); fixed the dead `app/src/constants.ts`
  and `app/src/components/wizard/SetupWizard.tsx` paths to `app/src/domain/glyphs.ts`
  and `app/src/sections/admin/setup-wizard/`; added `quiz_words` to the schema table;
  and added the missing Working Guardrails section. Removed the stale references to the
  deleted `app/src/domain/compose.ts` in `app/src/domain/shaping.ts`,
  `app/src/sections/scribe/ScribeView.tsx` and the `schreibsystem-und-wortbench.md` proposal. Added the `kurrent-writer-and-recognizer.md`
  proposal and `docs/notes/` to `docs/index.md`.

### Removed

- **Orphaned design artifacts in `docs/reference/`.** The pre-design-system
  landing mockup `kurrentschrift-landing.html` (Google-Fonts era, referenced
  by nothing) and the duplicate `gl-germancursive.woff2` (the live copy is
  `app/src/assets/fonts/`) are gone.
- **Unused runtime dependencies `cairosvg` and `python-multipart`.** Neither is
  referenced anywhere in the codebase; both (plus cairosvg's native transitive
  chain) leave the Cloud Run image.

## [0.13.0] — 2026-07-09 — Tri-script pen foundation + human writing kinematics

### Added

- **`llms.txt` for agentic browsing.** The site now serves a spec-compliant `/llms.txt`
  (H1, summary, linked sections: the three public areas, legal, GitHub, the open read
  API's OpenAPI docs) so AI agents get a crawlable map instead of the SPA's index.html
  fallback — fixes the Chrome "agentic browsing" audit error (#174).
- **The public repository is linked.** Every public page's footer now carries a GitHub
  link next to the Impressum link (on phones the row wraps onto its own line), and the
  Impressum's "Quellen & Lizenzen" no longer announces the repository as planned but links
  it directly. A "Weitere Projekte" block (mirroring the anyplot legal page) lists
  anyplot.ai and cite-citadel after the operator disclaimer — deliberately in the
  Impressum and not in the footer (#172).
- **Petzendorfer 1889 seeded as a separate Kurrent source** (migration 0012): the only PD
  Kurrent chart with a digits row — the Kurrent digit templates' authoring source. A
  deliberately separate hand (~57° calligraphic Kurrent), never merged into loth-1866
  (#171).
- **Broad-nib pen model — the Offenbacher Bandzugfeder writes for real.** `core/widths.py`
  gains the `BroadNib` model (`w(φ) = W·|sin(φ−α)| + t·|cos(φ−α)|` at Koch's constant 15°
  edge angle, primary source *Die Offenbacher Schrift*, 1928) and
  `core/template.py::chisel_union_rings` sweeps the W×t nib rectangle along the centerline,
  so chisel ends fall out naturally — never round caps. The writing path regenerates widths
  from the model (warp-invariant, inks generated connectors, repairs scan noise); the stored
  measurement is untouched and keeps serving the diagnostic. `api/rendering.py::pooled_pen`
  calibrates the nib per source from the pooled measured profiles (#170).
- **Digits and punctuation as detached glyphs.** `0–9` and `. , ; : ! ? ' „ “ - – ( ) §`
  are real glyphs with `joins: false` in both shaping twins (`core/shaping.py`,
  `app/src/domain/{glyphs,shaping}.ts`): written without any Übergang, placed by whole-ink
  clearance, pen lift into them, Endstrich + diacritic flush before them. ASCII `-` maps to
  the historical double-stroke hyphen; straight `"` pairs low-then-high by occurrence
  parity. The admin sidebar gains Ziffern/Satzzeichen groups; digits are quizzable,
  punctuation is not; unauthored marks surface in the Federprobe "noch nicht kuratiert"
  note instead of failing silently (#170).
- **Pen-aware composition.** `compose_word(…, pen=…)`: `pressure` (Kurrent Spitzfeder) caps
  generated strokes at the source's pooled hairline — pressure never travels between
  letters; `broad_nib` ships connectors as swept-nib rings (the client already fills rings,
  zero client changes). `pen=None` stays byte-identical: golden fixture, wordbench 0.125337
  and both glyph benches (Sütterlin 0.1865, Kurrent 0.1251) reproduce their baselines
  (#170).
- **Design doc `docs/concepts/federmodelle.md`** — three pens, one render path: the
  Bandzugfeder law + chisel sweep, Spitzfeder hairline rules and the planned synthesis
  model/naturalness metric, the digits/punctuation glyph space, per-script authoring
  sources, and the rejected alternatives (#170).
- **`tools/glyphbench --style offenbacher`** routes through the pressure derivation and the
  Schwellzug pixel metric (honest for extraction quality — it scores the measured profile)
  until a dedicated width-direction naturalness metric is calibrated (#170).

### Changed

- **The handwriting reveal follows human kinematics.** `lib/strokeTiming` applies the
  two-thirds power law (the pen visibly slows in curves — non-linear dashoffset keyframes
  per stroke) and isochrony (stroke durations grow sublinearly with length) to
  `WrittenWord` and `WrittenGlyph`, replacing the constant-speed sweep
  (docs/concepts/federmodelle.md §5) (#171).
- **The Schreibtafel writes with the same hand.** `WrittenSheet` (the `/tafel` alphabet
  rows) now runs through the shared kinematic reveal (strokeTiming + the WAAPI hook)
  instead of its own linear keyframes — the most glyph-dense writing surface no longer
  sweeps at machine-constant speed; cascade stagger, tap-replay and the ink settle are
  unchanged (#173).

### Fixed

- **Trailing punctuation no longer steals the round Schluss-s.** Positions are assigned per
  run of same joins-class, so `"Haus,"` keeps `s-final` (previously the comma made the s
  read as medial → long-ſ) (#170).

## [0.12.0] — 2026-07-08 — Word bench full coverage + compose loop

### Added

- **All 63 Abb.-19 words + 33 Abb.-20 letter pairs annotated**; the word bench scores pairs
  separately with their own `pair_loss` headline (#163).
- **Word diagnostics layer**: `tools/wordlab` overlays a composed word on its specimen with
  per-connector penalty callouts; compose provenance + segment metric (#166).
- **Word-final Endstrich**: the composer generates the finishing upswing of the school hand
  (words bench 0.1284 → 0.1240) (#168).

### Changed

- **Fluent body widening**: the chart-pinched round letters (e/a/u/o) open to the connected
  hand's measured pitch at render time (#169).

## [0.11.0] — 2026-07-04 — Repo goes public

### Added

- **Community files + public README** with hero image and live-first structure (#151, #162);
  Codecov coverage reporting for the backend (#161).

### Changed

- Dependency refresh across Python, npm and Actions via grouped Dependabot PRs (#152–#160).

## [0.10.0] — 2026-07-03 — Server-side word composition + word bench

### Added

- **Public write API** (`/write/glyphs`, `/write/word`) with a shared render cache — whole
  words compose server-side in one cacheable request (#142, #143).
- **The word bench**: frozen same-hand word specimens (Sütterlin Abb. 19) scored against the
  composer, `tools/wordbench` (#144); first transition-redesign loop against it (#145).
- **Quiz word mode + "Tinte & Vergleich" redesign** (#139), an expanded ~500-word reading
  bank with runtime distractor draw (#148, #149, #150).

### Changed

- Sütterlin diacritics defer to the end of the word; connectors join on rendered-centerline
  tangents (#136, #137); public reads route via the open `api.` subdomain (#140).

## [0.9.0] — 2026-06-26 — Public redesign: three areas + Schreibtafel

### Added

- **The word-composition engine**: glyphs connect into live-written words (#112).
- **Public Schreibtafel** with written-letter playback and all three Grundtafeln (#114, #123,
  #127–#130); the `/lehrbuch` primer, later renamed and expanded to `/schriftkunde` (#116–#118).
- **ü/ö/Ü/Ö authored from two chart pieces** (crop patches) in the admin (#135).

### Changed

- **Public redesign**: width/typo/surface foundation, three-area nav + hubs, single-column
  written-word hero, unified PageHeader, SEO baseline (#120, #122, #124–#126, #131).

## [0.8.0] — 2026-06-21 — Sütterlin naturalness metric

### Added

- **The Gleichzug naturalness metric** (`core/quality_suetterlin.py`) with bench + glyphlab
  tooling (#96) and two deliberate re-baselines (#97, #106).
- Admin wizard: per-category score breakdown in Optimieren, the Weg "Anpassen" nudge tool
  (#101, #102); a decluttered admin with one action hub (#111, #113).

### Changed

- Sütterlin ductus tuning: through-stem straightening, Spitze-tip retrace collapse then
  taper (#103–#105); `/quality` scores with the style's own metric (#98).

## [0.7.0] — 2026-06-17 — Sütterlin writes (Gleichzug derivation)

### Added

- **Skeleton-locked Gleichzug derivation** for Sütterlin (#83) with edge-following in merged
  double-stroke regions (#92), smooth strokes + the source-pooled nib (#93), corner-aware
  verticalization + the glyphlab inspection tool (#95).
- Wizard ink brush + per-glyph speck auto-fill + mask preview (#80); admin glyph comparison
  view (#82); InfoHint affordance + legibility pass (#89).

### Changed

- Quiz UX rounds: written/crop toggle, steady prompt, compact setup, crop-overlay reveal
  (#84–#88).

## [0.6.0] — 2026-06-12 — Glyph quality pipeline + the Sütterlin pivot

### Added

- **Image-space quality metric + the hermetic glyph bench** (#63), corner knots + template
  refinement (#64), the `/optimize-glyphs` experiment-loop skill (#65), admin quality
  feedback + re-derive flows (#66, #68–#70, #73, #74).
- **Medial-axis snap + crossing-width resolution** for the drawn ductus (#61).
- `/impressum` with period letter-register copy (#75).

### Changed

- **Pivot to Sütterlin as the active public script**: PD 1922 chart seeded, width resolver
  activated, runtime source switcher (#77–#79); experiment run pressure-cone prior + refine
  tuning, bench 0.1339 → 0.1251 (#71, documented in the new Qualitätsmetrik reference #72).

## [0.5.0] — 2026-06-10 — Paper & ink identity (style rounds R1–R9)

### Added

- **The period visual identity**: pigment palette, ink settle + fibre-wicked edges, Schulheft
  ruling, exercise-book blue guides, letterpress deboss + Playfair Display, static paper
  grain (#47–#53, decisions recorded in the style guide #54).
- The self-verification skill family + working guardrails (#55); Schriftkunde docs + PD
  chart sources with corrected slant geometry (#57, #58).

### Changed

- **App restructure**: components/layouts/sections/hooks refolder, lazy routes, typed API
  layer, German locales namespaces, split quiz/chart/wizard modules (#33, #34, #38–#46);
  quiz letters render "as written" via the ductus (#32).

## [0.4.0] — 2026-06-08 — Library schema + setup wizard

### Added

- **The library schema** (styles/templates/instances) with German lineature terms and the
  step-by-step setup wizard as the admin's single editing surface (#25, #26).
- **Multi-stroke ductus capture** — pen lifts no longer bridge strokes (#29); per-line slant,
  box move/resize/lock, zoom + pan, mobile fixes (#22–#24, #27, #28, #30).

## [0.3.0] — 2026-06-04 — Public site v1: landing, quiz, worksheet

### Added

- **Public letter-recognition quiz** (`/quiz`) with end-screen stats (#12, #13, #15);
  the Lineatur worksheet generator (#11); the serif landing with ductus timeline, rebuilt
  in the "paper & ink" identity (#9, #19–#21).
- **M4 fit routine** + editor fit overlay (#8); CI pipeline (ruff + pytest) (#14); alembic
  migrations run on deploy (#18).

## [0.2.0] — 2026-05-29 — Deployed: Cloud Run + Cloudflare Access

### Added

- **Cloud Run + Cloudflare Access deploy bootstrap** (#5) with operational status notes
  (#6); Plausible analytics routed off the Access-gated apex.
- Vision + architecture docs restructured holistically (#1–#4).

## [0.1.0] — 2026-05-22 — MVP kernel: ductus extraction

### Added

- **Two-channel ink extraction** (width = pressure via skeleton + distance transform,
  darkness = ink) on the PD Loth 1866 Kurrent chart (M0).
- **Canonical ductus templates** for the §9 core glyphs with editable bboxes, exclude
  regions and a chart annotator (M3 Phase A).
- **The admin**: web UI for canonical extraction, from CLI tooling (v1) to real UI with
  2:1:2 calibration + resample (v2) to `/core` + Postgres + Alembic + SVG diagnostic (v3).
- The founding design docs (analysis-by-synthesis architecture, MVP gates, naming/licensing)
  and the first PD source.
