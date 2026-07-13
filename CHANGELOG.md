# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Every PR adds its entries under `[Unreleased]`; a release moves that section under a new
version heading. Code changes are covered here — data-only commits (chart sources,
authored templates) are covered by their `SOURCE.md` provenance records instead.

## [Unreleased]

### Added

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

### Changed

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

### Added

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
