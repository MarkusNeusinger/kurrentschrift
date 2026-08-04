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

### Fixed

- **Generated Übergänge were drawn mirrored below the baseline.** The two SVG
  path helpers disagreed on the y sign — `ringsToPathD` keeps y by default,
  `polylineToPathD` always negated it — so any surface drawing both kinds of
  item under one y-flipping `<g>` got the letters (rings) right side up and the
  generated connectors (polylines) flipped a second time. They left the word
  and reappeared as loose strokes under it, in the word cards, the specimen
  comparison overlay and the pair editor's live preview and its own
  pointer-drawn connector. Verified in the browser before and after: the
  connectors of `muß` sat at y [−0.73, −0.48] and [−0.70, −0.40] against a
  payload of [+0.48, +0.73] and [+0.40, +0.70], an exact sign flip, and the pair
  editor showed letters at y [0, 1.01] beside a connector at [−0.74, −0.49].
  `polylineToPathD` now takes the same explicit `flipY` its ring twin has; the
  asymmetric defaults stay (the public "as written" surfaces rely on them) and a
  unit test states the rule so the trap cannot be re-entered silently.

- **The engine ink was drawn in the wrong place on every word card.** The
  overlay that projects a composed word onto its specimen pixels pinned the
  composition's left edge to the crop's left edge — a convention, not a
  measurement. Over the 63 Sütterlin word rows that put the engine a median
  **8.9 px (~0.3 xh) left** of the ink it was supposed to be compared against,
  so every composition read worse than it is and the deviation an admin saw was
  mostly registration error. The trace and the composition live in the identical
  frame (baseline = 0, 1 unit = x-height), so the row's own measured
  registration places both: the median left-edge error drops to **1.1 px**, and
  what remains at the right edge is the real width difference — the thing worth
  looking at. Extracted as the shared, unit-tested
  `shell/model.ts::traceFrameOf`/`traceMatrix` and applied to the word cards
  AND the specimen overview list; the left-edge pin survives only as the
  fallback for a sample no harvest ever traced.

### Changed

- **A word card is two faces now, like a letter tile.** One frame held the
  plate crop, the green trace and — overlapping both — the red engine ink, which
  is three answers to two different questions in one picture. Left is now the
  MEASUREMENT (plate ink + the traced pen path + the clickable letter boxes and
  join dots; the engine joins it translucently only when the Überlagern switch
  is on), right is what the engine writes on its own. Both faces are drawn at
  the same px-per-unit on the same baseline row, so „trifft der Fit das Wort?"
  and „was macht das System daraus?" are two glances instead of one untangling,
  and a width or slant difference is a difference rather than a rendering
  artefact.

- **The first Stage-B chain harvest is written, and the running forms are now
  derived from whole-word pen paths.** Until now every occurrence in the
  statistics layer came from fitting one letter at a time; the chain fit
  (`tools/pairlab/chain.py`) solves letter–connector–letter as a single pen
  path, and its first full harvest replaced the layer wholesale: **232
  occurrences** (up from 218, and for the first time including letters read off
  the Abb. 20 pair drills) and **77 word traces** (up from 58) that carry their
  connector strokes instead of the letters alone. Rebuilding the hand's
  aggregates over them yields 35 keys, of which **15 running forms were
  applied** — `a d e g h i l m n r u w` refreshed, and `S`, `sz` (ß) and `z`
  given a running form for the very first time. `t`, `o`, `c` and `b` were deliberately
  withheld and are reported as excluded; `t`'s stored running form is
  consequently, and correctly, stale until its sample recovers. The wordbench
  headline moves from **0.116886 to 0.115623** on the words (the pairs give up
  0.001013, the same trade the July running-form round documented: the pair
  drills are written close to the chart). Documented as a dated re-baseline in
  `docs/reference/qualitaetsmetrik.md` §6, together with the second effect that
  fell in the same window — fixtures built from the exact pooled nib rather
  than the four-decimal readback, which confirms the previously documented
  headline was right and the export was what had drifted.
- **The admin header is the public header.** The workbench sat under a 48 px
  strip of Garamond-13 buttons while every public page carried the 67 px bar
  with the wordmark and the Playfair nav — two houses in one product, and the
  shabbier one was where the actual work happens. The shared chrome now lives
  in `components/HeaderBar/HeaderBar.tsx`: the sticky, blurred, hairlined bar
  with an optional content-width cap, the `•kurrentschrift.ink` wordmark with
  its viridian dot and italic TLD, and the Playfair nav link with the animated
  viridian underline and `aria-current`. `components/PublicHeader` and
  `sections/admin/shell/AdminHeader` are both written on top of it; the public
  bar is visually unchanged, and the admin bar keeps exactly the differences it
  has reasons for — full-bleed instead of capped, because the workbench needs
  the width; `zIndex` 1100, so the Korb drawer (1200) and the LetterPicker
  popover (1300) still sit above it; and its two extra slots, the Vorlage chip
  (now a link back to the Vorlagen-Auswahl) and the Korb ⚑ badge. Its nav lost
  the `overflowX: auto` that grew a scrollbar around the hover underline
  sitting four pixels below the links.
- **The admin follows the public type system instead of its own hard-coded
  sizes.** `/admin` opens with `PageContainer` + `PageHeader` (eyebrow
  „Werkbank", Playfair title, `Prose` intro) over a three-column card grid
  whose cards name the plate and not only the script; `shell/Panel.tsx`'s
  `ViewHeader` gained an `eyebrow` (the three views pass their area) and
  replaced its hard-coded `fontFamily: display, fontSize: 24` with
  `variant="h4"` plus the design-system heading rule — size from the ladder,
  face and weight in `sx`; panel titles became `h2` elements; the occurrence
  caption left 10 px for the 14 px caption floor. The workbench is the surface
  this project is used from most and should not read as the draft version of
  its own design system.
- **The Petzendorfer 1889 chart is hidden from the Vorlagen-Auswahl — hidden,
  not removed.** Two cards both labelled „Kurrent" make the one choice the
  whole admin hangs off ambiguous, and the second cannot be authored against
  yet: it was seeded ahead of time for the digits row Loth 1866 lacks, written
  by a different hand at ~57° against Loth's ~50°. The new
  `CONFIG.hiddenSourceIds` filters it out in the two places in
  `context/AdminContext.tsx` that can produce a selection — the source list
  itself and the persisted choice read back from localStorage, because a stored
  hidden id would strand the admin on a Vorlage with no card to switch away
  from. Nothing is deleted: no migration, no DB change, the row, its chart
  bytes and every API route stay exactly as they are, and taking the id out of
  the list brings the card back.
- **The admin is one workbench in three views instead of five pages with tabs
  and a permanent letter sidebar.** Entering `/admin` now asks the one question
  everything below depends on — which Vorlage — because every letter, join and
  word belongs to exactly one source and its hand; the chosen script is named
  in the header and one click goes back to switch it. Under it sit exactly
  three views, each following the same overview ⇄ detail pattern:
  **`/admin/buchstaben`** carries a letter's whole life in one column (the
  chart cell with the Einrichtungs-Wizard, the Diagnose modal and the
  collapsible chart editor, the Tafel-Form beside the derived Laufform, every
  harvested occurrence as a crop cut-out, the H1 statistics with its median
  sketch, and chips onward to the letter's joins and words);
  **`/admin/uebergaenge`** puts the generated join first, the H2 „Gemessen vs.
  komponiert" measurement beside it and the pair editor last, in the order the
  stage doctrine triages; **`/admin/woerter`** writes any text, breaks it into
  the letters and joins it consists of (each a jump into the other two views)
  and shows the traced specimen with its clickable occurrence overlay wherever
  a plate of this hand wrote the same word. This completes the absorption of
  `/admin/vergleich`, `/admin/paare` and `/admin/belege` into the Werkbank that
  `optimierungs-werkbank.md` §2/§6 announced — the tools themselves are
  unchanged and simply lost their own routes; the old paths stay as redirects
  so bookmarks and work-item links keep working.
- **Every level of the admin now accepts freely typed targets, not only what a
  plate happens to contain.** Any two-letter combination and any word can be
  typed, written by the engine and complained about — most combinations were
  never written by hand anywhere, they still have to look right, and until now
  there was nowhere in the admin to look at one. A filed `work_item` for such a
  target carries no specimen reference and says so, rather than inventing one.
- **One shared data layer and one header above the three views.** The
  occurrence reads and the per-hand statistics load once for the whole
  workbench (`sections/admin/shell/WorkbenchData.tsx`), so walking letter →
  join → word costs no refetch; the Auftragskorb moved into a header drawer, so
  ⚑ works from wherever the complaint arose. The subject of each view lives in
  the query string (`shell/focus.ts`, pure and unit-tested), which makes every
  cross-jump a plain link, the back button an inspection history and a reload
  land where the work was. The desktop/mobile split is gone with the sidebar:
  one layout serves both, and the letter grid became an on-demand picker.

### Fixed

- **The gate decides what becomes a measurement, not what the trace shows.** The
  chain harvest wrote word traces that broke into disconnected fragments:
  `tools/laufform/harvest.py` assembled the pen path out of the letters its gate
  cascade had ACCEPTED, so a letter that merely wobbled took itself and the
  connectors on either side out of the drawing — `Einen` (E-i-n-e-n) was one
  chain solve over all five slots and came out as three pieces because slots 2
  and 4 failed `not_converged_local`. Two layers, two questions: `instances` is
  the statistics layer and stays gated exactly as before (a wobbly letter must
  not pollute a Laufform median), while `word_instances` is the inspection layer
  and now carries the WHOLE solved run — every letter segment and every
  connector the chain produced. Only a slot the chain could not fit at all (no
  template, no window, `chain_failed`) stays out, because it has no geometry;
  a trace that splits for that reason is honest. The per-slot verdicts stay
  readable beside the geometry, and the two sets are two explicit fields rather
  than one overloaded key: `measurements.traced_slots` is what is drawn,
  `fitted_slots`/`unfitted_slots` keep meaning "accepted as an occurrence", with
  `gates`, `converged_local` and `geo_rmse_px_by_slot` unchanged. Measured over
  the frozen words + pairs fixtures: 27 of the 77 previously written records
  still hold more than one body stroke, down from 32, and every remaining split
  is a genuine pen lift (the `E`/`P` ornaments, the u-Bogen, `t`'s crossbar,
  `ß`, the ä/ü umlauts) or a chain that really did stop — no split is caused by
  a gate any more. 19 further specimens gain a trace at all, having had every
  letter rejected and therefore been dropped whole. The occurrence layer is
  byte-identical across the change (232 rows, the same Laufform drafts), and the
  longer welded runs stay inside the wire caps (longest stroke 2277 of 4096
  points, `Galoppieren`; at most 4 of 128 strokes), with the downsampling guard
  in `cap_word_strokes` reporting rather than 422-ing if they ever do not.
- **A glyph with two coincident anchors returned a 500 — and took the whole
  batch with it.** `core/template.py::sample_polyline` builds its spline
  parameter from the cumulative chord length, and a zero-length chord leaves
  that parameter flat, on which `CubicSpline` raises "`x` must be strictly
  increasing sequence". Not a theoretical input: anchors are stored rounded to
  four decimals, so the apex of a short out-and-back stroke can round its two
  samples onto the same point — the Sütterlin `period` does exactly that — and
  that one key failed the whole 60-key render batch the new letter overview
  asks for. The repeat is dropped before splining (a zero-length chord carries
  no geometry, only the same position twice); a path without one keeps every
  anchor and every sample byte-identical, which the compose golden fixture
  confirms. Two unit tests in `tests/test_template.py`.
- **Occurrence thumbnails cut into the letter.** The crop left a fixed 4 crop px
  of air around the stored occurrence box, but that box comes from the M4 fit
  and hugs the centerline, so the ink runs past it on every side. The margin
  scales with the box now (`max(7, 0.18 · √(w·h))`) and the thumbnail row grew
  from 64 to 80 px.
- **pairlab measured the loop-exit join class against a reference that was not
  there, and on an arc that was not matched.** `analyze._real_join` read the
  specimen's own joining stroke only inside `JOIN_BAND_Y`'s 0.8 xh ceiling — the
  composer's clearance band, not a statement about where joins live — while a
  loop exit departs at y ≈ 1.04–1.13 xh and runs level at ≈ 0.9–1.0 xh: the
  tracker saw 4 of 18 gap columns, every `d→*` occurrence fell back to the
  straight exit→entry chord, and the clipped seed latched onto the ink below the
  join (a following descender in `b→p`, empty space in `o→r`). The band ceiling
  now follows the exit, which needs no new constant and leaves every pair whose
  exit sits inside the band bit-identical. On top of that
  `chainbench.dconn_matched_arc` clipped all three curves to one x-interval,
  which is an arc match only while a curve is single-valued in x — a loop-exit
  chain connector owns the near-vertical descent off the loop and the plunge
  into the next letter, so its clipped piece carried 1.69× the reference's arc
  at the same x-span and `dconn` compared physically different positions; the
  reference now defines the stretch and the other curves are trimmed to it.
  Together this turns M3's last open class from `gen 0.058 → chain 0.228` into
  `0.074 → 0.050` (on the word plates alone `0.081 → 0.034`) and the pooled
  paired delta from +0.008 (p 3e-5) into +0.002 (p 0.48); M1, M4 and the kill
  criteria come out field-for-field identical because `chain.py` never reads
  `_real_join`. See `docs/proposals/uebergaenge-befund.md` §5c, Nachtrag
  „loop-exit" — which also records why the `pair_aggregates` ban stays anyway.
- **The pair-chain fit no longer stalls on letters that are composed on top of
  each other.** `analyze._generate_connector` emits its full Bézier subdivision
  whatever room the placement leaves and floors its handle at 0.05 xh, so where
  two letters touch or overlap the cubic doubles back into a cusp carrying two
  dozen anchors inside ~0.05 xh of arc. `chain._second_difference_operator`
  scales as 1/ds², which put the connector's smoothness block into the Hessian
  ~10⁷ times stiffer than on a normal join: `e_smooth(x0)` 5.2e6 against 53.7,
  `f(x0)` 51.9 against 0.026, and 24 of the 248 Stage-A occurrences — every
  `c→h`, `r→e`, `m→u`, `n→e` — burned their whole iteration budget unbending
  that connector while `e_geo`, `e_cov` and `e_wid` never moved from their
  starting values at all. `chain.regularise_connector_anchors` now
  re-discretises a connector whose chord is below
  `CHAIN_CONNECTOR_MIN_SPAN_UNITS`: the same curve, resampled by arc length to
  the anchor count that chord can carry (endpoints exact, so the shared seam
  anchors survive, and nothing above the threshold is touched). The affected
  occurrences go from 4 to 20 of 24 converged on the letter-local gate.
- **`chainbench` exported an optimizer status key `chain.py` never writes.** The
  row read `fit_meta["status"]` while the fit writes `"message"`, so
  `chain_status_msg` was the empty string on every row and the L-BFGS-B
  termination reason — the one column that identifies a stalled solve — was
  invisible. The termination message, `optimizer_success`, the iteration and
  evaluation counts and the per-term energies at `x0` against `x*` are now all
  exported, with an explicit flag for a non-finite initial energy (which `_r`
  would otherwise round into an indistinguishable `None`).
- **The registered overlay of engine ink over the specimen pixels is back — and
  now also sits on the word evidence card.** The redesign had left it wired to
  a hardcoded `false`, so the sharpest error-finding view in the project was
  dead code while the surrounding copy still promised it. It returns as a
  switch (on by default) in the Wörter overview, and the traced-word card now
  draws the composed word in the same registered frame as the specimen and the
  trace — original ink, hand trace and engine output in one picture.
- **A failed occurrence load is now visible instead of spinning forever.** The
  shared data layer set its error flag but kept the lists at `null`, so
  `loading` never ended and every occurrence panel sat on a spinner that could
  not resolve; the state is now ended by the error and reported as one quiet
  line per block.
- **Filed tasks in the Auftragskorb link to their subject.** The basket named
  what was wrong and offered no way to it, although the three views are one
  link away for exactly those keys — a letter/pair/word row now navigates and
  closes the drawer.
- **German singulars:** „1 Beleg" and „1 Vorlage" instead of „1 Belege" /
  „1 Vorlagen".

### Added

- **The word harvest can fit whole words as one pen chain (`--path chain`,
  report-only).** `tools/laufform/harvest.py` gained the Stage-B integration
  of issue #278: after the existing per-slot grid fits (which keep supplying
  each letter's local window and the fallback diagnosis), every maximal run of
  joined slots is fitted as ONE `fit_word_chain` chain, letters pass a
  five-gate cascade (like-for-like coverage · geo RMSE · placement bound ·
  anchor count · a degenerate adjacent connector rejects the letter too —
  seam parameters are shared), and the word records are welded WITH their
  connectors for the first time — a `traced` row is finally "the word as
  written", closing the dead `authored` branch. Plus `--jobs` (ProcessPool
  over cases, order-independent medians), `--sets words,pairs` (the pair
  drills flow through the same code path), `--diag-csv` (34 columns incl.
  per-join connector signals), `--max-cases`. The old path stays the default
  and byte-identical (`--path slot`, pinned by a golden test); `--apply` is
  refused outside `--path slot --sets words` so the chain path stays
  report-only until its measurement round passes. 24 new unit tests.
- **Four faces per letter in the Buchstaben overview, and a grid that can sort
  itself worst-first.** Original (the chart crop) · Tafel-Form (the authored
  chart ductus, variant 0) · Laufform (the derived running form, variant 100) ·
  „Median & Vorkommen" (the H1 aggregate: the per-anchor median with the
  occurrence chains thin behind it, the MAD circles, and the Laufform actually
  in use drawn dashed against it) — the source, the two forms the engine can
  write from it and the statistics they came from, in one row per letter,
  where the overview used to show chart against written and nothing else. Every
  face has an honest empty state instead of a blank box: „noch keine Laufform"
  where none was derived, and for the sketch a hint that distinguishes loading
  from no hand, from an unavailable admin read, from genuinely no aggregate.
  Overlay mode still collapses the first two faces into the red silhouette
  overlay, and the faces are `flex: 1 1 150px`, so they break to 2 × 2 on a
  phone. The new sort toggle (Alphabet · „Schlechteste zuerst") turns the
  alphabet into a work list. The sketch itself moved out of
  `shell/LensStats.tsx` into `shell/AggregateSketch.tsx` plus the pure
  `shell/sketchGeometry.ts`, so the miniature in the grid is the same drawing
  as the one in the statistics block, only shorter.
- **The key numbers under each of them — occurrences, mean fit residual, the
  stored score and where its points went — and the whole alphabet's scores in
  one read.** New `GET /sources/{id}/templates/quality` (admin-gated like the
  raw template row per quellen-und-rechte.md §5, uncached, and declared above
  `GET /{glyph_key}` so FastAPI cannot swallow the literal path as a glyph key)
  serves `templates.trace_meta["quality"]` for every row of the style, extracted
  in SQL by the new `TemplateRepository.list_quality` rather than dragging the
  dense `pixel_anchors`/`half_widths_px` arrays along with it: 0.145 s for all
  80 rows, against 0.44 s for a SINGLE glyph through the recomputing per-glyph
  `/quality`. What it serves is the score at AUTHORING time — the number the
  derivation stamped onto the row, not a re-score with today's metric code —
  which the chip tooltip says, and only variant 0 is read, because a Laufform
  row inherits the chart row's `trace_meta` and its stamped score is therefore
  a copy, never a verdict on the median geometry. The rest of the grid is as
  cheap: the render payloads come from two batch requests (`renderCache`'s
  `fetchRenderGlyphs` gained `variant` and `bust`, which is what makes a
  Laufform batch possible at all), the statistics from the shared workbench
  context, and the expensive per-glyph `/diagnostic` is now fetched only for
  the overlay mode that needs its outline geometry — the grid used to fire one
  per card, some thirty per visit. Score colour, the score chip and the
  per-category breakdown moved out of the wizard into
  `sections/admin/quality/scoreParts.tsx` and are now shared by the wizard
  preview, the overview and the Diagnose modal, which gained the breakdown it
  had never shown although its payload always carried it.
- **A connector degeneracy guard (`tools/pairlab/connector_qc.py`) — the QC
  the loop-exit fix showed was missing.** On the Abb.-20 pair drills the chain
  connector silently degenerates in 11 of 23 occurrences (a long straight
  diagonal through both letters, every convergence gate green). Four pure
  geometry signals behind a minimum-chord gate — seam share, forward ratio
  (`net_dx / arc`), arc-vs-gap, straightness×length — calibrated in-sample
  against the 11 known-bad rows: 11/11 flagged, one demonstrable false
  positive across 179 labelable word rows (raw flag rate 4.2%, chosen for
  recall since the guard's job is keeping contaminated joins out of the
  `gen_chamfer` audit; the stricter setting is one `dataclasses.replace`
  away and documented). Reported as a `chain_conn_degenerate` column and a
  worst-first block in the chainbench; the precondition before any chain
  connector may feed `pair_aggregates`, and gate 5 of the coming word
  harvest (a flagged connector rejects its adjacent letters too — seam
  parameters are shared).
- **`GET /sources/{id}/render-context` — the resolved render context of a
  source at full precision, admin-gated.** Everything a render resolves before
  it draws (lineature, width resolver, the source-pooled Gleichzug nib and the
  pooled pen), unrounded, where the public `/write` payloads carry the same
  numbers rounded to the four decimals the renderer draws at. It exists for the
  one job that needs to reproduce a served payload bit-for-bit offline: the
  fixture rebuild without Cloud SQL access (`tools/wordbench/fetch_fixtures.py`)
  used to recover the pooled nib by reading a rounded half width back off
  `/write/glyphs`, and that ≤5e-5 xh error flipped knife-edge ink-clearance
  decisions into up to ~0.02 xh of glyph-placement jitter. The fetcher now asks
  for the exact value first and falls back to the readback on an API that
  predates the endpoint, records which it got as the manifest's
  `nib_precision`, and tightens its own acceptance gate accordingly — a root
  frozen with the exact nib must compose bit-for-bit against `/write/word`
  instead of within the old jitter allowance. Admin-gated like the raw template
  read (quellen-und-rechte.md §5): the pool spans every authored template of
  the source, including variant rows no endpoint serves. The payload rounding
  itself stays at four decimals — it is part of the frozen render contract, and
  a fifth decimal would cost ~7 % payload size for nothing the exact scalar
  does not already fix.
- **A glossary of the project's own vocabulary — `docs/reference/glossar.md`.**
  The docs, issues and admin UI have grown a private language across the
  optimisation rounds: palaeography (Duktus, Schwellzug, Anstrich/Auslauf),
  architecture (Bibliothekseinheit, Laufform, Prüfstein, open-core moat),
  measurement (Kettenfit, Naht, like-for-like Gate, matched arc,
  Bézier-Handle-Floor, Cusp-Connector, degenerierte Solves) and house metrics
  (`gen_chamfer`, `doff`, `dconn`, `bench_loss`/`pair_loss`, MAD hull) — none of
  it explained where a newcomer meets it. Around 115 entries in six themed sections
  with an alphabetical quick index: each one a plain-language explanation that
  assumes nothing, plus, where it helps, the formula name and the module or
  constant it lives in (`core/fit.py::CONVERGED_GEO_RMSE_UNITS`), deliberately
  enough anchor vocabulary that pasting an entry into any AI chat lets the
  reader dig further. Includes the four Stage-A chain metrics **M1–M4** with
  what each asks, how it is computed and where it stands — plus an explicit
  warning that M1–M4 (chain), M0–M7 (MVP milestones, hence "M4-Fit") and H/R/W
  numbering are four independent schemes — and a research section (AIoU, LDTW,
  DTW, HWD, Sigma-Lognormal, G1/G2 continuity) that places the house metrics
  against the published state of the art.
- **A standing upkeep rule so the vocabulary cannot outrun the glossary.** Any
  doc or PR that coins a new Fachbegriff, metric, named failure mode or repo
  idiom adds its entry in the same change — recorded in `CLAUDE.md` §
  „Working guardrails", mirrored into `.github/copilot-instructions.md`, spelled
  out with the entry format in the `/write-docs` skill and enforced at PR time
  as a gate in `/open-pr`.
- **The two preconditions Stage A put in front of issue #278's Stage B are
  measured, and they do not both fall the same way.** Stage A compared the chain
  fit against the independent one under two silently different rules, and said
  so; `chainbench` now removes both differences and re-measures. **M1** grades a
  chain letter in its own letter-local coverage window — the window the
  independent M4 trace was always graded in — while the fit keeps seeing the
  whole pair window, since owning the connector's ink is the chain's entire
  point; the report carries the union gate, the like-for-like gate and, as the
  symmetric alternative, the baseline re-graded on the union window. **M3**
  clips generated, chained and ink-read connector to one common arc (the
  specimen's ink gap intersected with each curve's own x-span) before applying
  the unchanged pairmeas formula, because the chain connector owns the two stub
  zones the ink-read one does not have. The verdict changes accordingly:
  three quarters of M3's Stage-A gap was definitional (chain 0.086 → 0.040 xh
  against a bar of 0.034 → 0.028) and what remains sits in a single exit class,
  while M1's shortfall survives the like-for-like comparison (0.665 → 0.690
  against an unmoved 0.746) and is therefore a real property of the coupled
  problem rather than a grading artifact. Written up in
  `docs/proposals/uebergaenge-befund.md` §5c: the conditional go becomes a go,
  with the M1 deficit carried into Stage B as a named floor and the
  `pair_aggregates` ban kept for the loop-exit class. The fit itself is
  untouched — M2, M4 and all three kill criteria reproduce number for number.
- **`pairlab` can fit a letter join the way it was written — as one continuous
  pen path — and Stage A of issue #278 measured whether that is worth doing.**
  `tools/pairlab/chain.py` fits `letter → connector → letter` as ONE problem:
  both chart rows (never the composed Laufform geometry) plus the generated
  connector, whose interior points are free anchors with no form
  regularisation, with the two seams tied by *shared anchor indices* rather
  than a continuity penalty — so the letter/connector boundary stops depending
  on whether the letters happen to touch on this specimen, which is exactly
  where today's ink-gap dissection returns nothing. Placement stays a separate
  unregularised per-slot translation block, the coverage window closes the hole
  between the letters, and the coverage distance is Huber-capped so foreign ink
  has bounded leverage. `tools/pairlab/chainbench.py` runs the chain and
  today's independent fit over the same 248 frozen occurrences and reports the
  four Stage-A metrics plus the kill-criterion signals. The verdict is mixed
  and written up honestly in `docs/proposals/uebergaenge-befund.md` §5c: no
  kill criterion fires, 87 % of the joins that are unmeasurable today become
  measurable, and the chain deforms letters less than the independent fit — but
  convergence and connector shape do not pass as specified, so Stage B is a
  *conditional* go with two named preconditions. Measurement only: nothing here
  touches the DB, the API, `core/` or rendering.
- **The word-bench fixtures can be rebuilt from the deployed API, not only from
  Cloud SQL.** `tools/wordbench/fetch_fixtures.py` is a read-only sibling of
  `export_fixtures.py` that produces byte-compatible fixture roots over HTTP,
  reusing the exporter's pure pieces and replacing only the DB block — so a
  session without Cloud SQL egress (a cloud session, a fresh checkout) can
  still run the word bench, pairlab and chainbench. GETs only, `ADMIN_TOKEN`
  from the environment and never echoed, with a `--verify` gate that composes
  the rebuilt cases locally and compares them against `/write/word`.
- **The Laufform can be adopted from the admin — deliberately, with the
  difference visible first and a confirmation in front of it.** `apply-laufform`
  is the one step of the whole hand model that changes what the engine writes,
  and until now it existed only as a curl call (#270). It gets a surface that
  matches that weight rather than hiding it: at the foot of the Buchstaben view,
  in its own set-apart block, a dialog that warns this leaves the measuring half
  of the system, previews per glyph what would change (occurrences, distance to
  the Laufform in use, „neu" for a first write, „unverändert" at distance 0),
  requires an explicit confirmation, and afterwards reports what was written and
  what was skipped and why. It stays hand-wide because the endpoint is — a UI
  implying per-glyph choice would lie about what the button does.
- **Every letter says whether the form the engine writes is still the form the
  statistics say.** A chip („Laufform aktuell" · „Laufform veraltet · Abstand
  0,05" · „noch keine Laufform"), and in the median sketch the currently
  rendered running form drawn dashed against the median that would replace it —
  the difference is there to look at before anything is overwritten.
- **`GET /hands/{hand_id}/aggregates` carries the freshness pair per row:**
  `laufform_anchors` (the rendered variant-100 form) and `laufform_dev_xh` (its
  distance to the median). The Prüfstein used to exist only as a by-product of
  a rebuild or an apply, so answering "is this stale?" required doing something
  first. Null wherever the comparison is meaningless: a non-base variant, no
  stored running form, a differing anchor count.
- **The letter statistics draw every occurrence behind the median.** The MAD
  circles gave the spread as a number; the bundle of thin occurrence chains
  gives it as a shape — ten forms hugging the median and one outlier read very
  differently from an evenly scattered set, and that is the question ("are the
  occurrences alike at all?") the layer exists to answer. Same reading as the
  pair sketch already had, in the same frame (occurrence anchors are stored
  centered, exactly like the median).
- **`GET /write/glyphs` takes a `variant` parameter.** Default 0 is the
  authored chart ductus every public surface writes with; `100` renders the
  derived Laufform, which is what lets the Buchstaben view show the two side by
  side. A glyph without a row for the asked variant lands in `missing` exactly
  like an unknown key, so asking for the Laufform of a letter that never got
  one is an empty answer rather than a silent fallback to the chart form.

- **End-to-end overview doc `docs/concepts/vom-scan-zum-schreiben.md`: how the
  writing system emerges from a chart, the specimen plates and the author's
  tracing.** The pipeline was documented stage by stage — schema in
  `architektur.md`, ruler in `qualitaetsmetrik.md`, occurrence and statistics
  layers in the Handmodell plan, doctrine in the Werkbank proposal — but
  nowhere as one narrative, so the shape of the whole (what is input, what is
  derived, what actually renders) had to be reassembled from six documents
  every time. The new doc walks the six steps once in plain German prose, each
  with a tight `Fachlich:` / `Im Admin:` / `Wer macht was:` triple, and then
  answers the three questions the stage-by-stage docs leave implicit: which
  artefacts are on the writing path at all (`templates` + approved
  `glyph_pairs` as data, shaping/compose/pen models as rules — everything else
  measures and never writes), why there is no context-forked `a`-before-`b`
  template (occurrence anchors are stored centered, so the letter median is the
  context-free body while transitions are their own per-pair measurement
  objects — with the honest limit named: body reshaping smears into the letter
  median, visible as fat exit-side MAD circles), and what goes stale (the
  Laufform is a materialised snapshot behind explicit manual steps; generated
  transitions read the current form's exit/entry at every compose and follow
  automatically, approved overrides deliberately do not). Closes with the six
  known gaps as of 2026-08-02 and a mapping list into the detail docs. Every
  route, endpoint, table and constant it names is verified against the repo.
- **Lifecycle status headers on every doc under `docs/`, a living-docs table
  with named update triggers, and a `write-docs` duty that keeps them true.**
  The docs tree had grown past thirty files in which a settled decision, an
  already-shipped proposal and a pure sketch looked exactly alike — a reader
  (human or agent) had to reconstruct from PR archaeology whether
  `htr-integration.md` describes running code (it does not) or whether the
  Handmodell stages were still ahead (H0–H2 shipped in v0.22.0). Each doc now
  opens with one blockquote directly under its H1, dated absolutely and drawn
  from a deliberately small vocabulary — `bindend`, `lebend`,
  `teil-umgesetzt`, `umgesetzt-historisch`, `offen`, `Befund-Journal`,
  `statisch` — that states what is built, with PR and migration evidence, and
  what is still future. `docs/index.md` gains a "Dokument-Status" section
  explaining the vocabulary plus a table of the living documents with the
  concrete files whose change obliges an update (for example: `write-api.md`
  follows every `/write/*` route, `core/shaping.py` and `core/compose.py`;
  `werkzeuge.md` follows every entry script under `tools/`), and three
  section-wise obligations for docs that are only partly implemented
  (`animation-rendering.md` §1/§3, `styleanalyse.md` layers 1–2,
  `quellen-und-rechte.md` §5). The proposals list carries each stage's status
  as a short tag, so a shipped stage can no longer read as open work. The
  `write-docs` skill gets the matching duty: implementing part of a proposal
  updates its header and its index tag in the SAME PR as the code, a new
  proposal starts at `offen`, and a doc that turns `lebend` is added to the
  trigger table. The audit that produced the headers also found stale claims,
  all fixed in this pass rather than merely flagged: the Laufform rows live on
  `variant=100` (not `1`), `werkzeuge.md` was missing both harvest tools and
  the wordbench report modules, the `sprachregelung.md` schema example still
  carried the `position` key removed by migration `0017`,
  `qualitaetsmetrik.md` still headlined a July run, `quellen-und-rechte.md` §5
  did not name the admin-gated aggregate reads, `offenbacher.md` claimed the
  Koch 1928 chart was unseeded (it has rendered on the public Tafel since
  migration `0008`), `architektur.md` §4 still called the pair-override layer
  a staging proposal, `design-system.md` was missing `PaperCardLink`, and the
  animation width-resolver table listed no `broad_nib`.

## [0.22.0] — 2026-08-02 — Hand model statistics: aggregates + gemessen vs. komponiert

### Added

- **Wordbench "gemessen vs. komponiert" columns (Handmodell H2): every composed
  letter join is now reported against the specimen's own dissected one.** The
  pair layer already knew what the writer did at each join — `pair_instances`
  holds one dissection per adjacent joined pair of the very specimens the bench
  scores — but the bench never looked at it, so a worse word said only *that*
  it got worse. `tools/wordbench/pairmeas.py` puts the two side by side per
  join: `doff`, the HORIZONTAL placement delta read in the frame the harvest
  measured in — the two letters' body endpoints (left glyph's last
  non-diacritic stroke end, right glyph's first non-diacritic stroke start)
  against the measured `geometry.offset`'s x — and `dconn`, the mean pointwise
  distance between the two connector centerlines, arc-length-resampled to the
  same 24 points the pair aggregation uses and then each shifted onto its own
  first sample, i.e. a translation-free shape-and-sweep distance. The frame is
  the whole point: the composer's coupling anchors sit up to ~2 xh away from
  the body endpoints after a capital ornament or a trimmed lead-in, so
  comparing them against a body-frame measurement reports an artifact rather
  than an error (`Of` read 2.06 that way, now 0.07). The measured offset's y is
  excluded by construction — the harvest cancels the relative vertical fit
  shift, so it is the composed body Δy at harvest time and would measure the
  composer against itself. The run prints `meas n=<matched>/<joins> doff=…
  dconn=…` on every scored row (zeros included, `-` where nothing matched) and
  appends `meas_matched`/`meas_excluded`/`meas_doff_median`/`meas_dconn_median`
  after the stable headline block, `pair_`-prefixed for the pairs set. Two
  kinds of join stay out of the medians and are counted instead: a dissection
  the harvest's own QC rejected (`fit_ok`, the gate the pair-aggregate rebuild
  applies too — 11 of 199 word rows, 3 of 33 pair rows), and a join rendered
  from an approved override, which IS a harvested centerline and would score
  ~0 against its own source. `compose_word(..., provenance=True)` additionally
  states each join's coupling endpoints `exit`/`entry` in word coordinates (the
  Endstrich has no `entry`) — not readable off the emitted centerline, kept for
  overlay diagnostics, deliberately not used by `doff`. The measured joins
  freeze as a new per-set fixture artifact `pair_instances.json`
  (`export_fixtures.py`, written atomically, with `--only pair-instances` to
  fill it into existing fixture roots without re-freezing — and thereby
  re-baselining — crops, masks, slots or templates); a corrupt or unreadable
  one costs the columns and one warning line, never the run. Report-only in the
  strict sense, like the slant column and the Gleichzug audit before it:
  computed under its own guard so a crash cannot move the number (and says so
  once per run), matched by `(kind, specimen_id, from_slot)` plus agreeing base
  keys so a shifted slot counts unmatched rather than comparing the wrong
  transition, and verified byte-identical — `bench_loss` 0.116886 and
  `pair_loss` 0.164506 to the last digit before and after, every per-entry loss
  unchanged. Null line: words 188/214 matched, doff median 0.135 · dconn median
  0.115; pairs 30/34, 0.192 · 0.217. The public `/write/word` payload and the
  compose golden fixture are untouched (provenance stays off by default) (#268).
- **"Gemessen vs. komponiert" on the Vergleich page's pair cards (Handmodell
  H2, read surface).** The Verbindungen tab showed a specimen beside the
  composed pair and left the verdict entirely to the eye, while the occurrence
  and aggregate layers already knew how far the generator sits from the measured
  median for exactly that join. Each pair card now carries a compact "Gemessen"
  chip row between header and body: the occurrence count (the aggregate's
  `n_instances`, falling back to the matched `pair_instances` OF THAT SAME HAND
  so a card keeps a number without the admin-gated layer, and a second hand
  harvested on the source can never inflate a number the tooltip credits to one
  writer) and the `gen_chamfer` mean — the audit number this layer exists for —
  with the fuller pooled QC in the tooltip (chamfer max, harvest chamfer, fit
  residual, offset ± MAD, ink-gap share, plate-kind histogram, the named hand),
  plus a "Fit unsicher" chip when THIS specimen's own occurrence carries
  `fit_ok: false`. A card without a median says WHICH of the four reasons
  applies, in the Werkbank's own wording — still loading, no hand on the
  occurrences, never rebuilt, or not loadable — so "keine Messung" is left to
  the one case it describes (the hand's aggregates are there, this join is not
  among them). Both lists load once per source rather than per card — the public
  pair occurrences, and the pair aggregates of the hand DERIVED from those rows
  (modal non-null `hand_id`, never a constant), reused as-is when the tab is
  left and re-entered; a failing admin read degrades to the occurrence numbers
  behind one quiet notice instead of emptying the tab. Deliberately numbers
  only: the median-connector sketch stays in the Werkbank's pair lens, and a
  registered overlay of measured connector on composed pair is not attempted
  (different frames — a false superposition would read as evidence). Scoped to
  the Verbindungen tab; the Fremdhand tab stays view-only and unmeasured, and
  the numbers are matched by the same base-key pair the pair-editor deep link
  uses, so a card's readout and its "Im Paar-Editor öffnen" can never describe
  two different joins. Frontend-only, no API change (#267).
- **Werkbank "Stufen-Einsicht" (W5): the hand-model statistics layers are now
  visible inside the context lenses.** Both aggregate layers existed and had no
  reader — H1 medians and H2 pair medians were numbers only a rebuild response
  ever printed, while the surface where a complaint is made showed the chart
  form and the raw occurrences with the whole condensation step invisible
  between them. The letter lens now draws the stored aggregate between the two:
  the per-anchor median as an anchor chain with per-anchor MAD circles over the
  baseline/midband hairlines („Aggregat-Median (Laufform-Quelle)"), plus the
  pooled layer-1 numbers (occurrences, specimens, fit RMSE ⌀/max, x-height,
  position histogram). The pair lens gains „Gemessen vs. komponiert": every
  loaded occurrence connector thin, the median connector bold on top and the
  median offset as a dot with its MAD whisker — occurrences, median and hull all
  share the one left-exit frame, so the sketch needs no registration, and a
  `/write/word` overlay is deliberately not attempted (different frame; the
  comparison stays side-by-side) — beside the pooled dissection QC with
  `gen_chamfer` as the audit number. The hand is derived from the loaded rows
  (the modal non-null `hand_id`, never a constant: the Werkbank shows exactly
  one source and therefore one hand) and is NAMED in every block's header, with
  a quiet warning when the occurrences do not all name the same one — one
  hand's medians over another hand's occurrences must never happen silently.
  The two layers load and refetch independently (own state, own error flag), so
  a failing pair read never mutes the letter block and a rebuild leaves the
  other lens — and its own result caption — untouched; the admin-gated reads sit
  outside the spine's load, so a 401 or an empty statistics table degrades to a
  quiet caption and leaves the spine and both lenses fully usable. Each block
  carries a quiet per-layer rebuild button — that recomputes statistics and
  touches no rendering, which is also why `apply-laufform` has no button here:
  it writes Laufform rows, and this surface displays generated stages rather
  than editing them (optimierungs-werkbank.md §3/§7). The sketches stay honest
  about their own material: occurrences the rebuild skipped as `fit_bad` are
  left out of the pair sketch and its bounds (and counted in the caption)
  instead of squashing the median they never fed, an absent MAD prints no „±"
  clause, and an aggregate missing for the selected key reads differently from a
  hand that was never rebuilt at all (#266).
- **Pair aggregates (Handmodell H2): the statistics layer over the observed
  letter joins.** `pair_instances` has held every dissected join since H1/H2,
  but nothing condensed them — the pair level had occurrences and no medians.
  Migration `0023` adds the additive `pair_aggregates` table, the pair twin of
  `aggregates`, keyed `(hand_id, left_key, right_key)`, and the admin-gated
  `GET /hands/{hand_id}/pair-aggregates` + `POST …/rebuild?min_n=1` fill it
  from a hand's occurrences across all sources. The math lives in the pure
  `core/aggregate.py::aggregate_pair_instances`: the placement offset condenses
  to a per-axis median, the connector centerlines are resampled to 24
  arc-length-uniform points (`_resample_polyline` — differently-sampled traces
  of one stroke only line up over arc length) and reduced to a per-point
  median, both with a MAD hull, alongside pooled dissection QC (`gen_chamfer`
  as the „gemessen vs. komponiert" audit number, ink-gap share, the
  word-plate/pair-drill histogram, distinct specimens). `kind` is pooled — an
  Abb.-19 word join and an Abb.-20 pair drill are the same hand writing the
  same transition — and `min_n` defaults to 1 rather than the glyph layer's 4,
  because pairs are sparse (87 occurrences over 45 pairs on the 1922 plates)
  and one clean dissection is still the only measured truth about that
  transition; `n_instances` rides along so consumers can weigh it. Deliberately
  without an `apply` counterpart: the pair statistics are read-only by design —
  `glyph_pairs` stays the sparse verbatim override, the §4 join generator stays
  the default, and nothing here reaches the writing path (#265).
- **Auftragskorb protocol (Werkbank W4): a filed task now has to be understood
  before it can be worked, and diagnosed before it can be closed.** A
  `work_items` row used to carry only the admin's note and a free-text
  resolution — the handling doctrine
  (`docs/proposals/optimierungs-werkbank.md` §5) lived purely in prose, and a
  bare `PATCH {status: "done"}` closed anything. Migration `0022` adds
  `understanding` · `reproduced` · `stage` · `acked_at` · `closed_at`
  (additive, nullable) and the status vocabulary grows to `open` → `ack` →
  `done`, plus `returned` for the hand-back the doctrine used to express as a
  string prefix. The API enforces the transitions in the pure, unit-tested
  `check_transition`: acking requires the session's own restatement of the task
  and whether it could reproduce the complaint, closing requires that
  restatement plus a `stage` from the fixed §3 vocabulary (`chart_ductus` ·
  `laufform` · `join_rule` · `composition` · `pair_override` · `word_trace` ·
  `not_reproducible`) and a non-empty `resolution` — anything less is a 422
  naming the missing field. Acking is deliberately its own call: a protocol
  field may not travel on a status-less PATCH, and closing needs the
  restatement to be *stored*, so it cannot be produced at the same moment as
  the result. What accumulates is the point: a searchable archive of symptom →
  verified reproduction → diagnosed stage → change → measured effect, instead
  of a wall of „erledigt" (#264).
- **A source-free work-item queue, so a session can find its own tasks.**
  Reading the basket used to require knowing a `source_id` first, which sent a
  session guessing `/work-items`, collecting a bare `{"detail":"Not Found"}`
  and grepping the router source for valid ids. The queue is now reachable
  without any prior knowledge: `GET /work-items[?status=&source_id=]`,
  `GET/PATCH /work-items/{item_id}`, with each row carrying its own
  `source_id` back and an unknown `source_id` answering 404 instead of a
  quietly empty list. The source-scoped routes stay for the SPA. Round start is
  wired up too — `/prime` lists the open items, and the new `/work-basket`
  skill runs the protocol end to end (reproduce → restate → triage → rule-fix
  before override → measure → close) (#264).
- **Word editor (Werkbank W3): every stored word occurrence can now be
  re-traced by hand.** Each card on `/admin/belege` opens the new
  `WordTraceEditorDialog` — the specimen crop as underlay with the row's own
  registration frame drawn on it (Grundlinie + Mittellinie), the stored trace as
  the starting point, and pointer/S-Pen capture in which every pen lift
  (Absetzen) starts a new stroke, exactly like the wizard's Weg step. Per-stroke
  undo, clear and reset-to-stored; saving writes the path as an `authored`
  `word_instance` through the existing batch endpoint with a SINGLE item and
  without `replace`, so the server's overwrite protection re-traces exactly that
  occurrence and leaves every other row — and every other authored trace —
  untouched. Slot labels are preserved and the registration (`registration_px`,
  `xh_px`) is carried over so the row stays displayable, while the replaced
  path's automatic fit QC is dropped instead of ranking a hand-fixed word by
  dead numbers. The crop↔trace mapping moved into the pure, unit-tested
  `sections/admin/belege/registration.ts` shared by the list and the editor, and
  the frontend API layer grew `putWordInstances` + `getHand` (the occurrence's
  writer is echoed back as read, so saving a trace cannot wipe the hand's
  era/note). Authored traces are ground truth for statistics and training, never
  a rendering patch (optimierungs-werkbank.md §3/§6) (#261).
- **Aggregates rebuild (Handmodell H1): the statistics layer finally gets
  filled.** `aggregates` has existed since migration `0004` and never held a
  row; the admin-gated `GET /hands/{hand_id}/aggregates` and
  `POST …/aggregates/rebuild?min_n=4` now condense a hand's stored `instances`
  into one aggregate per `(glyph_key, variant)` — the per-anchor elementwise
  median (which IS the running form, because occurrence anchors are stored
  centered: "shapes, not placements"), the per-anchor spread as a median
  absolute deviation hull, the pooled layer-1 statistics (fit RMSE, x-height,
  position histogram, distinct specimens) and `n_instances`. The median math
  lives in the new pure `core/aggregate.py` (no DB imports — the API image
  ships no `tools/`, same rationale as `core/word_metric.py`). The rebuild
  response reports the H1 Prüfstein per key: `laufform_dev_xh`, the mean anchor
  distance between the recomputed median and the stored Laufform (template
  variant 100). Reads are admin-gated too — an aggregate is learned geometry,
  not public product surface (quellen-und-rechte.md §5) — and nothing here
  touches rendering. Migration `0021` re-keys the table to
  `(hand_id, glyph_key, variant)` following the R2 position removal (drop +
  recreate: the table was empty) (#259).
- **The Laufform row is now DERIVED from the aggregate (Handmodell H1
  complete).** `POST /hands/{hand_id}/aggregates/apply-laufform` (admin-gated)
  writes the hand's stored aggregates into the style's running-form templates
  (variant 100): the per-anchor median becomes the anchors — occurrence anchors
  are stored centered, so the median already sits in the chart row's frame —
  while widths, stroke topology and entry/exit/advance keep coming from the
  chart template, through the very `build_laufform_canonical` helper the manual
  `PUT …/templates/{key}/laufform` uses. With that the variant-100 row stops
  being the harvest's end product and becomes a derivation from the persisted
  occurrences, and a following rebuild reports the H1 Prüfstein
  `laufform_dev_xh` as 0. It reads the STORED aggregates and never recomputes
  them: writing templates affects rendering, so promoting a statistic into a
  rendered form stays a deliberate, separate step from the rebuild. Only
  base-variant aggregates feed it (a variant-100 occurrence would let the row
  derive from itself); keys without a chart template or with a deviating anchor
  count are reported as skipped with their reason, never guessed at. The
  response reports the pre-write distance per key, so the answer shows what the
  apply actually changed (#260).

### Fixed

- **The `X-Admin-Token` break-glass path could never authenticate against the
  deployed API.** The `ADMIN_TOKEN` secret version had been created with a
  trailing newline; Cloud Run injects secret bytes verbatim, so
  `settings.admin_token` carried that newline while an HTTP header physically
  cannot transport one — `secrets.compare_digest` in `api/auth.py` therefore
  rejected *every* possible token value with 401, and no amount of re-copying
  the token could fix it. `core/config.py` now strips surrounding whitespace
  from all four Secret-Manager-backed settings (`database_url`,
  `cf_access_team_domain`, `cf_access_aud`, `admin_token`) and maps a
  whitespace-only value to `None`, so the admin gate still fails closed with 503
  when nothing is configured instead of comparing against an empty string. The
  malformed secret version was replaced in Secret Manager as well; the new
  `tests/test_config.py` pins both the stripping and the outage itself.
  `docs/reference/frontend-stack.md` now documents the two rules this cost us:
  a self-set `X-Admin-Token` only ever reaches Cloud Run via
  `api.kurrentschrift.ink` (the apex `/api/*` 302s at the Cloudflare Access edge
  first), and Secret Manager versions must be created with `printf '%s'`, never
  `echo` — with the byte-count diagnosis, because command substitution hides the
  newline and makes a fingerprint comparison report a false match (#262, #263).

## [0.21.0] — 2026-08-01 — Optimierungs-Werkbank + open-core moat

### Added

- **The Optimierungs-Werkbank page (`/admin/werkbank`, stage W2): word spine,
  switching context lens, Auftragskorb.** One admin surface where the three
  occurrence layers finally meet, per the doctrine in
  `docs/proposals/optimierungs-werkbank.md` §2. The left column is the word
  spine — every stored trace over its specimen crop, worst first — now with an
  interactive overlay: a dashed box per fitted letter and a dot on every join
  between two adjacent letters. Clicking one switches the right column's lens:
  a LETTER shows its chart form plus every stored occurrence as a cut-out
  thumbnail (worst residual first, click to jump back into that word) and
  offers the wizard jump; a JOIN lists its dissected occurrences with the
  generated connector's distance from the plate ink and opens the pair editor
  for exactly that pair. ⚑ (or shift-click) files the element into the
  Auftragskorb — the `work_items` backend from W1 — where a letter first has to
  pass the one pre-sort question §4 puts on the human ("does it look wrong on
  its own too?"): yes routes to the wizard and files nothing, no files the
  complaint. `WordSampleOut` gained the specimen's page `rect` so page-pixel
  occurrence boxes can be placed inside a crop; the existing pages
  (Vergleich · Paare · Belege) stay untouched until the Werkbank absorbs them (#255).

### Changed

- **The Auftragskorb card shows what a session understood, and lets the admin
  say it got it wrong.** `KorbPanel` groups by protocol state — handed back on
  top (those wait on the author), then the queue, then what is in work, with
  the archive behind the existing toggle — and renders the session's
  restatement as its own block with chips for „nachvollzogen" and the
  diagnosed stage. An acked item carries a `missverstanden` button: one click
  opens a correction field and puts the row back to `open` with the correction
  appended to the note, while the rejected restatement stays on the record. The
  round is deliberately NOT blocking — a session acks and keeps working; the
  veto exists so a misunderstanding costs one click instead of a whole round.
- **The word bench now composes with the frozen Laufform variants — the
  measurement stand catches up to production (handmodell plan H0).** The
  fixture export freezes the `LAUFFORM_VARIANT` template rows (median running
  forms) as `templates_laufform.json` next to `templates.json`, the runner
  passes them into `compose_word` exactly like `/write/word` does
  (`--no-laufform` keeps a chart-only diagnostic run), and `tools/wordlab`
  (fixture and live path) composes identically so its overlays show what the
  bench scores. Documented re-baseline in `qualitaetsmetrik.md` §6: words
  0.1208 → 0.1169, pairs flat at 0.1645 — decomposed into the export shift
  (five words + one pair newly scorable through the authored capitals) and
  the Laufform effect proper (−0.0053 on words) (#256).
- **Open-core moat hardened: the learned dataset is no longer publicly
  exfiltrable.** The README has always reserved the authored data (ductus
  templates, running forms, statistics) outside the MIT grant; now the
  technical side matches: `GET /sources/{id}/templates/{glyph_key}` — the
  full authored row incl. the raw stylus path, used by no public surface —
  is admin-gated (the public list keeps serving geometry-free summaries),
  the design-sync preview data file that embedded real diagnostic payloads
  is untracked (local-only, regenerate against the local API), and
  `quellen-und-rechte.md` §5 documents the whole enforcement picture: bench
  fixtures stay gitignored, `/write` payloads remain deliberate product
  surface under the README reservation + crawler policy, the compose-golden
  parity fixture (11 rendered words, no templates) is the accepted known
  exception with a follow-up to regenerate it from synthetic templates, and
  a public dataset only ever ships as a deliberate goal-7 release (#254).
- **The Optimierungs-Werkbank direction and its binding stage/role doctrine,
  documented.** `docs/proposals/optimierungs-werkbank.md` records the
  2026-07-31 decisions (ONE admin workbench page — word spine + letter/pair
  context lenses + Auftragskorb; the Korb as a `work_items` table the AI reads
  per API) and, centrally, the doctrine that prevents misunderstandings on
  both sides of a fix task: manual input only where it creates ground truth
  (chart ductus, word re-tracing where the auto-fit fails, pair overrides as
  last resort), everything generated gets flagged rather than hand-patched, a
  Korb entry names where the problem was SEEN while the stage triage (chart →
  Laufform/fit → class rule → placement → override) is the AI's duty, with a
  fixed `resolution` format and a "Rückgabe an Autor" path for ground-truth
  gaps. Indexed in `docs/index.md`; CLAUDE.md and the Copilot twin point to it
  as mandatory reading before working off a work item (#253).
- **The Auftragskorb: filed optimization tasks instead of screenshots
  (Werkbank stage W1).** The admin's channel into a working session gets a
  backend: the new additive `work_items` table (migration `0020`) holds one
  row per marked element — `kind` names the level (`letter` | `pair` |
  `word`), the key columns name the element, `specimen_kind`/`specimen_id`
  name the words.json sample the issue was seen in (same namespace semantics
  as the occurrence rows), and `note` carries the observation. A working
  session lists the open items at round start, works them off and closes each
  with status `done` plus a `resolution` note (what changed, PR reference).
  All of it runs over the new admin-gated
  `GET/POST /sources/{id}/work-items` + `PATCH/DELETE …/{item_id}` — unlike
  the occurrence reads even the list is gated, because these are internal work
  notes, not measurement or public content. Filing validates that the target
  is actually workable (a letter item needs its glyph_key, a pair both sides,
  a word its text or specimen) and that the keys are registry glyphs. Nothing
  here affects rendering (#252).

### Fixed

- **Werkbank: the context lens and Auftragskorb now stay beside the word being
  inspected.** The sticky positioning sat on the lens card, whose parent column
  is content-sized — no room to travel, so clicking far down the word spine
  showed the lens only after scrolling back to the top. The whole right column
  now sticks against the tall spine track (scrolling internally when taller
  than the viewport; single-column layouts stay in flow) (#257).

## [0.20.0] — 2026-07-31 — Hand model: occurrence layer + Belege

### Changed

- **Admin Belege page (`/admin/belege`) — the stored word traces, browsable.**
  Every word-occurrence trace of the active source rendered over its specimen
  crop (public `GET /word-instances` joined with the word-samples metadata,
  registered via the row's stored registration), sorted worst-first: unfitted
  letters weigh heaviest, mean fit RMSE breaks ties — the error-finding surface
  over the new occurrence layer and the designated entry point for the coming
  word editor (manual `authored` re-tracing). Cards carry provenance
  (traced/authored), fitted-count, unfitted-letter and RMSE chips (per-letter
  values in the tooltip) plus a word filter; a sidebar icon links the page (#251).
- **Occurrence persistence: every clean specimen fit becomes a database row
  (hand-model plan H1/H2).** Per the decision to store occurrences, not just
  medians: the laufform harvest now persists each clean per-occurrence M4 fit
  as an `instances` row (centered shape anchors; placement, specimen/slot
  context, neighbours and RMSE in `measurements`) and the pairlab harvest can
  persist EVERY dissected letter join as a row in the new additive
  `pair_instances` table (migration `0019` — geometry in the `glyph_pairs`
  frame plus dissection QC, unique per `(source, kind, specimen, slot)` since
  the word plates and the Abb.-20 drills are separate id namespaces). The
  word level completes the training template: `word_instances` stores one
  traced word per specimen sample — slot labels plus the fitted letter
  strokes as a pen path in the word's registration frame, pairing with the
  specimen crop the word-samples endpoints already serve. Word traces carry
  provenance `traced`/`authored`: an authored row (the future manual admin
  trace — the training-set growth loop) is never overwritten or replace-wiped
  by a re-harvest, and `DELETE` spares it unless explicitly included. All
  three flow through new admin-gated batch endpoints
  (`PUT /sources/{id}/instances` + `/pair-instances` + `/word-instances`,
  public reads alongside) that get-or-create the writer's `hands` row — the
  first real inhabitants of the statistics layer defined in migration 0004.
  Occurrence rows never affect rendering; the composer path is untouched (#250).
- **The staged hand-model plan and the July specimen-source research, documented.**
  `docs/proposals/handmodell-stufenplan.md` consolidates the Laufform round into
  a staged proposal (H0–H5): confirm the role model (chart cell = ductus prior,
  the written words of exactly ONE hand = form model, foreign hands = context,
  never averaged), then fill the schema's empty statistics layer — persist the
  per-occurrence M4 fits into `instances`/`hands` instead of discarding them
  after the median, add per-pair join statistics for observed pairs, move
  measurable hand constants from `core/compose.py` into per-hand aggregates
  behind a simplification gate, prove hand-genericity on a second historical
  hand, and finish on the user's own hand ("any text, in my own hand" — vision
  goal 6, "in meiner Hand, aber jeden Text").
  `docs/notes/quellen-recherche-2026-07.md` preserves the source-research round
  (ranked committable finds, rejected items with license reasoning, possible
  archive requests recorded but not commissioned); `docs/index.md` indexes both
  and syncs the stale R3–R5 status line (#249).

## [0.19.0] — 2026-07-31 — Laufformen: the running hand's letterforms

### Added

- **Laufform variants: median running forms as a reserved templates
  variant.** The doctrine split settled with the author: the chart cell is the ductus prior
  (stroke order, crossings), the written specimen words are the form model.
  A new admin endpoint `PUT/DELETE /sources/{id}/templates/{key}/laufform`
  stores a per-letter median running form (validated one-to-one against the
  chart row's anchor topology; entry/exit/advance ride their end anchors),
  and `/write/word` renders it for glyphs in a flowing run (≥ 3, the
  ascender-lean gate) — solo payloads, the Tafel and short drills stay
  chart-true, and the per-letter width factor stays as fallback for letters
  without a stored form. `tools/laufform/harvest.py` derives the medians
  from the frozen word fixtures (M4 fit per occurrence, clean-fit guards)
  and writes drafts through the admin API. The experiment run measured
  words bench 0.1208 → 0.1136 with the median shapes; the headline moves
  only once the rows are written and the fixtures re-exported (documented
  re-baseline). Without variant rows every composition stays
  byte-identical (golden fixture untouched) (#246, #247).

### Changed

- **Capital handover: the join leaves the capital's WORKING exit, never its
  ornament.** Prompted by the user spotting that Soldaten's S→o kept a high
  covering line where the 1922 plate restarts at the baseline; measuring all
  22 joined capital→lowercase plate occurrences confirmed no capital ever
  hands over high. Crest and low-ending capitals (S/O/B/K/P) now depart at
  their last low body pass (local minimum at/below 0.55 x-heights) with the
  ornament fully drawn and retraced over its own ink; descender-loop
  capitals (G/Z) already took the fork join; mid enders (E/F/W/I/D) keep
  their true exit. The round-body top coupling is suppressed after any
  capital (contradicted by every plate case — round bodies are met on their
  rising flank with the lead-in intact), capital joins never garland (they
  rise monotonically on the plates) and get the plates' wider clearance.
  Words bench 0.121625 → 0.120793, pairs 0.169987 → **0.165297**, and the
  words Gleichzug audit is **completely clean for the first time** (0
  gaps, 0 doublings; pairs keep 6 in the parked d→descender class).
  Seiten 0.101 → 0.068, Silber 0.120 → 0.098, Säbel 0.165 → 0.115. Golden
  re-pinned (qualitaetsmetrik.md §6 „Kapital-Runde jul31") (#245).
- **Running-form width (Laufform): bound letters render at their measured
  running width.** M4-fitting all 257 letter occurrences of the specimen
  words onto the plates shows the running hand writes most letters 3–11%
  wider than their chart cells (e/r/h/l/ſ up to +11%) — the plates get
  their word width from wider letters with tighter gaps, the composer so
  far from chart-narrow letters with wider gaps (the root of the
  "stretched" impression). The target-based fluent body widening already
  covers the round bodies (its jul08 targets match the new medians
  independently); the new `LAUFFORM_SX` rule scales the remaining letters
  (i/l/h/n/r/w/ſ wider, t/d slightly narrower) in bound context only —
  solitary glyphs and the Tafel stay chart-true, like the ascender lean.
  Words bench 0.130253 → **0.121625** (largest single improvement since
  the garland round; 28 words improve, e.g. Gewehr −0.060, Einen −0.048),
  pairs 0.169987, Gleichzug zero line unchanged, gap-rhythm spread
  0.197 → 0.186. Golden re-pinned (qualitaetsmetrik.md §6
  „Laufform-Runde jul31") (#244).

### Fixed

- **Laufform rows move to reserved variant 100 — variant 1 belongs to the
  authored chart-form variants.** The live check after the first Laufform
  write-up found the collision: authored "A = A" teaching-chart variants
  already occupy variants 1..n (Sütterlin Q and ü carry 1+2), so
  `/write/word` had started rendering those authored alternatives as
  running forms in flowing words, and the Laufform upsert for `i` silently
  overwrote a pre-existing authored variant-1 row (its content needs a
  backup restore or re-authoring; Q/ü were untouched). The Laufform
  endpoint, the `/write/word` fetch and the harvest tool now use the
  reserved `LAUFFORM_VARIANT` (100), the 13 derived rows were migrated
  there and the 12 freshly-created variant-1 rows removed, and a
  regression test pins that an authored variant-1 row is never picked up
  as a running form (#247).

## [0.18.0] — 2026-07-31 — One-flow writing: six connection classes + Gleichzug audit

### Changed

- **A Gleichzug audit as wordbench report columns — the one-flow, one-width
  invariant made measurable.** A Sütterlin word is written in one flow (pen
  lifts only for diacritics) with a line that is always one nib wide; the new
  `tools/wordbench/gleichzug.py` detects the two violations on the composed
  centerline path alone — flow gaps (the pen teleports between items) and
  parallel doublings (two near-parallel stretches at a perpendicular offset
  between the retrace epsilon and ~1.35× the nib read as a double-width
  stroke, which a one-width nib cannot write). Retraces, transversal
  crossings and near-parallel pairs inside ONE letter (authored letterform)
  are classified out via the compose provenance tags. Report-only like the
  slant column (`flow gaps=… dbl=…` per entry, `gleichzug_*` totals per
  block), verified headline-neutral to the last byte; unit-tested. Current
  zero line after the join round: 0 gaps everywhere; after calibrating the
  doubling band against the user-approved renders (fully-merged runs below
  half a nib and short junction lobes are pen-authentic — the lower band
  edge scales with the nib, minimum event arc 0.25, parallel threshold 22°)
  the doubling worklist is 3 words / 17 pairs, concentrated in three known
  classes (capital joins, d into descenders, ſ into hanging bowls). The
  wordbench fixtures were also
  re-exported after the author completed the letter set — words 58/63
  scorable (only the five ß words remain), pairs 32/33, abb22 106/106; the
  new headlines (words 0.131392, pairs 0.182982) are a documented
  re-baseline, not comparable to the jul08-fixture numbers
  (qualitaetsmetrik.md §6) (#240, #241).
- **Fork joins for the long-s and the t/f bar — the two plate-measured
  stem-launch classes.** After a long-s the rising connector no longer
  climbs 0.08 x-heights BESIDE the stem (a sustained parallel track the
  plates never write — the Gleichzug audit's ſ shortlist): it rejoins the
  stem, retraces it to a fork at ~0.4 of the coupling height and swings
  out on a straight diagonal into a high coupling; hanging bowls place on
  the 45° line from the fork while c/t keep their calibrated run-down
  placement (overlay-verified plate-exact) and couple mid-flank. For t/f
  the second specimen measurement (all 8 joined occurrences) showed the
  plates end t's crossbar AT the stem (right of it: no ink — the long
  chart bar is table form) and leave the STEM on a shallow 16–27° rise
  into the next letter's apex: in bound context the rendered bar is cut
  at its own last ink crossing (word-final keeps the chart form) and the
  join is one straight rise, with placement on that line. Also fixes a
  latent shared-payload mutation (the stub/bar cuts edited cached stroke
  lists in place — a word-final t after any bound t lost its bar and
  Endstrich in cached-payload runs like the wordbench). Words bench
  0.130439 → 0.130253, pairs 0.174158 → 0.170674, Gleichzug doublings
  3 → 1 (words) / 17 → 9 (pairs); golden re-pinned
  (qualitaetsmetrik.md §6 „Gabel-Runde jul30") (#243).
- **Height-aware join kerning — ink at different heights may overlap columns
  like on the teaching plates.** The specimen gap measurement (every letter
  of all 58 Abb.-19 words re-fit independently onto its plate) showed the
  composed rhythm, not the total width, is what reads as stretched: the
  overall width ratio is 0.96 and the join-advance median ±0.00, but
  high-exit classes sat 0.13–0.36 x-heights wider than the plate (t/f bar,
  c/b/l/o arcs — the plate even slides the next letter's body under the
  t-bar) while baseline diagonals already matched. Joined placement now
  judges clearance per y-bin (the nine fusion-guard bins) between A's
  rightmost and B's leftmost band ink — bins where only one side has ink
  impose nothing, which is exactly the plates' tuck-under; the covering-arm
  exemption (r/p) collapses into it as a special case and backward bow exits
  (w/v) keep the scalar clearance. Words bench 0.131392 → 0.130439, pairs
  0.182982 → 0.174158, Gleichzug zero line unchanged (3/17), per-class
  advance error halved (c→h −0.26 → −0.13, b→e −0.28 → −0.14, l to 0.00);
  compose golden fixture deliberately re-pinned. The t/f bar class needs a
  fork join (retrace the own stroke, then fall) — measured on the plates for
  both the bar and the ſ ascent — and follows as its own round
  (qualitaetsmetrik.md §6 „Dehn-Runde Stufe 1") (#242).
- **A sketch-driven join round: six Sütterlin connection classes rebuilt
  toward "one flow, one nib width".** An annotated feedback loop (the user
  marking defects directly on rendered words) rebuilt the generated
  Übergänge in `core/compose.py`, each as a letter-CLASS rule, never a
  bigram: (1) a descender-loop exit (ſ) returns THROUGH the baseline and
  rides the next Anstrich letter's lead-in line up from the Grundlinie
  (class `{c, t}`; hanging bowls keep their direct coupling); (2) the
  Deckstrich arm (r/p) is classified exhaustively in the bow band — no
  crest-roll above the arm (the double-wave), and the covering arm no
  longer kerns the next letter away (arm-exempt clearance with a
  height-aware knob guard); (3) the arm FUSES onto the next letter's
  lead-in crest apex (round bodies + r + i, `ARM_FUSE_GAP` 0.02) — the bow
  rolls over in one motion, no parallel double-stroke; (4) same-slant
  sawtooth diagonals (e→n, i→n, …) couple as ONE straight through-line
  arriving high on the flank, placement untouched; (5) a bound loop-return
  letter (d, round s) no longer writes the chart cell's finishing stub at
  all — the return crosses the stem and continues in one motion into the
  next letter (word-final keeps the complete chart form plus a new
  level-launch late-rise loop finial); this supersedes the twice-rejected
  O3 stub trim, which fails only with a tip-anchored connector
  (qualitaetsmetrik.md §6); (6) every generated stroke now overlaps its
  neighbours' ink by `CONNECT_OVERLAP` under the round cap, closing the
  hairline white cracks at item handoffs. Wordbench: words
  0.123703 → 0.122287, pairs 0.191805 → 0.183317; compose golden re-pinned
  deliberately per stage (#239).

## [0.17.0] — 2026-07-28 — Fast public writes + crawler policy

### Changed

- **A written-down crawler policy — AI retrieval welcome, AI training declined.**
  Cloudflare answered every AI user agent with a hard `403` across the whole
  zone, `llms.txt` and `api.kurrentschrift.ink` included, so the file written
  for AI agents was unreachable to every agent it was written for — and
  user-directed fetches (`Claude-User`, `ChatGPT-User`, i.e. a human asking
  their assistant to open the page) were blocked along with the scrapers.
  `app/public/robots.txt` now carries the whole policy itself — the content
  signals incl. `ai-train=no` as the express reservation of rights under
  Art. 4 EU-DSM, the welcomed retrieval/citation agents, the declined training
  collectors — so it holds with Cloudflare's managed block turned off. The new
  `docs/reference/crawler-richtlinie.md` records the measurement, the decision,
  the dashboard steps that lift the block and the rejected alternatives;
  lifting it at the edge is a Cloudflare action, not a repo change (#232).
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
  above); tests, build and `npm ci` are unaffected (#190).
- **Ruff no longer formats the Markdown docs.** Ruff 0.16 extends `ruff format`
  to Python code blocks inside Markdown, which reflows the illustrative
  snippets under `docs/` and in the tool READMEs — schema sketches,
  pseudo-code and column-aligned trailing comments whose alignment is the
  point. `*.md` therefore joins `[tool.ruff] exclude`; the formatter's scope
  stays the 128 Python files it always covered. Unblocks the ruff
  0.15.20 → 0.16.0 bump (#226).
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
  `/write/glyphs` batch p95 1031 → 26 ms (#225).

### Fixed

- **Eraser mask correctly applies to inserted donor cells ("Patches").**
  Previously, when placing a second cell (Zelle einsetzen) into a crop via the
  admin wizard, the eraser tool (Ausschluss/Radierer) could not remove its ink
  because patches were composited *after* the eraser ran. The crop pipeline now
  composites patches before the eraser, matching the frontend's visual layering
  and allowing the eraser to clean up unwanted ink from donor cells (#238).
- **Robust `_rasterize_strokes` against malformed payloads.**
  The `core/chart.py` rasterizer now uses `isinstance` checks and `try...except` 
  blocks when parsing `mask_strokes` and `ink_strokes`. A malformed JSON row in 
  the database (e.g. flat integers instead of coordinate pairs) will now be 
  safely skipped instead of crashing the pipeline with a 500 error (#238).
- **Wizard gestures stranded by their own save — the eraser that kept
  painting and the Grundlinie that blocked the Weg.** Handing the preview
  over only once the commit lands (above) clears the gesture by identity,
  but nothing ended the POINTER's turn at pen-up: every pointer-move during
  the ~round trip replaced that same state with a new object, so the identity
  clear found a stranger and skipped. The gesture then lived forever — the
  red Ausschluss draft kept growing on plain hover moves and only vanished on
  the next press, and a leaked Grundlinie/Mittellinie drag survived the step
  change and swallowed every pointer sample on the Weg step (`if (calibDrag)`
  returns ahead of the trace branch), so the ductus could not be drawn at all
  and the stale value was committed on the next click. `WizardCanvas` now
  separates the two lifetimes explicitly (`gestureUtils.ts`): a pointer
  **grip** claimed at pen-down and released at the top of pointer-up, before
  the commit is awaited — so the preview still waits for its write while no
  sample can rewrite it. The grip also makes one pointer own the canvas (a
  palm resting beside the S-Pen no longer hijacks a stroke, and only the
  owning pointer's release commits), adds a `buttons === 0` backstop that
  finishes a gesture whose pointer-up never arrived, and a step change is now
  a hard gesture boundary (#231).
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
  `populate_existing` (#230).
- **Wizard gestures no longer snap back for the duration of their save.** The
  in-flight drag/stroke preview (Grundlinie, Mittellinie, Schräglage, donor
  cell, eraser and ink brush) was cleared *before* the PUT resolved, so the
  guide line or stroke rendered from the still-unsaved bbox for one round trip.
  The preview now hands over to the stored value only once the commit lands,
  cleared by gesture identity so a gesture started during the save survives (#230).

## [0.16.0] — 2026-07-20 — Writing-system redesign: one form per glyph + pair overrides

### Added

- **Admin pair matrix (`/admin/paare`, redesign R1).** Every two-letter
  combination of a chosen letter (capitals only on the left), composed
  server-side via the cacheable `/write/word` and rendered lazily per
  IntersectionObserver — an unnatural join is visible directly instead of
  hiding inside a longer word (#213).
- **Word-specimen comparison on `/admin/vergleich` (redesign R1b, stage 1).**
  The page now has tabs — Buchstaben (the existing per-letter view) plus
  Wörter/Verbindungen/Andere Hand: every connected-writing specimen from the
  source's `words.json` sidecar next to the same word written by the engine,
  side-by-side or with the engine ink overlaid on the specimen pixels,
  registered exactly over the sidecar lineature (baseline/midband → scale);
  unauthored letters surface as `missing` chips, the other-hand plate
  (Abb. 22) is labeled as view-only context (#213).
- **Public word-sample reads.** New `word_samples` router:
  `GET /sources/{id}/word-samples` (metadata with crop-local lineature) and
  `GET /sources/{id}/word-samples/{sample_id}/crop` (grayscale PNG, exclude
  rects painted paper-white), backed by `core/chart.py::load_word_samples` +
  `word_sample_crop_to_png_bytes` over the committed sidecar — public like
  the bbox crops (`<img>` cannot send the admin header), cached, covered by
  a new HTTP test suite (#213).
- **Writing-system redesign proposal (`docs/proposals/schreibsystem-redesign.md`).**
  Records the accepted direction from the 2026-07-17 review: one authored
  form per glyph with the position triplication removed (R2), an admin
  pair-matrix view over `/write/word` (R1), sparse *harvested* pair
  overrides with capital-joins first as the concrete form of proposal B
  (R3), placement-residual + O3 re-evaluation (R4), and a new measured
  slant finding — the specimen hand's d-ascender loop leans ~4–5° right
  of the upright chart cell while medians match (R5). Cross-referenced
  from `docs/index.md` and `planaenderungen.md` (proposals B and D) (#212).

### Changed

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
  a DB-connected session (qualitaetsmetrik.md §6) (#221).
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
  fixtures (#220).
- **Slant report column in the word bench (redesign R5, stage 1).**
  `tools/wordbench/slant.py` implements the shear-search estimator from the
  redesign findings (−30°…+30° in 0.25° steps, maximum sum of squared column
  profile; 90° = upright, < 90 = right-leaning). Every scored row reports
  `slant <specimen>/<composed>` plus per-block medians; report-only —
  headlines and per-word losses verified byte-identical. On the frozen
  references it reproduces the d-loop finding: das 86.2°, der 87.2°,
  die 88.0° against a rigid ~90° engine (#220).
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
  which carries real specimen ink; both headlines regress) (#220).
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
  deliberately re-pinned for this intentional output change (#220).
- **Pair cards link into the pair editor with the specimen as underlay.**
  Closing the redesign's R1b→R3 circle: every letter-pair card in the
  `/admin/vergleich` Verbindungen tab gets an "Im Paar-Editor öffnen" action
  that opens the pair editor for exactly that join, with the Abb.-20 specimen
  crop rendered as a semi-transparent, lineature-registered underlay in the
  drawing scene (baseline on y = 0, scale from the sidecar lineature; a
  "Vorlage unterlegen" toggle hides it) — the connector is drawn over the
  real pen's path instead of from memory. Saving an override invalidates
  that card's cached score; pairs that don't shape to exactly two slots
  offer no link. The shared `pairKeysOf` helper moved to its own module (#219).
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
  bench's frozen import path and behaviour are unchanged (#217).
- **Pair editor + override badges (redesign R3, stage 2).** Clicking a cell
  in `/admin/paare` opens the new `PairEditorDialog`: both letters rendered
  at an adjustable coupling offset (right entry relative to left exit), the
  connector drawn directly with the pointer/stylus, an approval checkbox and
  a cache-busted live `/write/word` preview. Freehand saves are stored as
  `authored`; approving an untouched harvested row keeps its provenance and
  specimen citation. Matrix cells show green (approved) / orange (draft)
  override badges; ligature-folding cells (ch, ck, …) have no join and stay
  non-clickable. New client endpoints for `/pairs` CRUD (#216).
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
  editor follow as the next slices (#215).
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
  `architektur.md` §3 updated in the same change (#214).

## [0.15.0] — 2026-07-17 — Full-repo audit: hardening, tests, deploy gating

### Added

- **"Einen alten Brief entziffern" section on /schriftkunde.** A method-only
  five-step decipherment guide (anchors first, stock formulas, chart
  side-by-side, the classic f/ſ–n/u–e/n traps, skip-and-return) with a
  pointer to the Schreibtafel — the practical how-to the page's own intro
  audience was missing (#211).
- **Quiz provenance caption.** The quiz setup now names its source like the
  Tafel and Federprobe do ("Nachgebildet aus der gemeinfreien
  Sütterlin-Ausgangsschrift von 1922.") (#211).
- **Structured data + meta polish.** Static `WebSite`/`Person` JSON-LD in
  `index.html`, a `twitter:image:alt`, and `<lastmod>` on every sitemap entry (#211).
- **`docs/reference/werkzeuge.md`.** Human-facing entry point for
  glyphlab/wordlab/pairlab (exact CLI, `--live` read-only pulls, `temp/`
  output) with pointers to the bench and quizgen docs; indexed in
  `docs/index.md` (#211).
- **Admin `useInView` hook.** `/admin/vergleich` gates each card's heavy
  diagnostic fetch behind an IntersectionObserver and lazy-loads crop images
  instead of firing ~30 JSON requests on mount (#211).
- **HTTP tests for the admin compute endpoints + the untested public reads.**
  New `tests/test_api_compute_endpoints.py` (15 tests): `/trace-preview`
  (pressure raw/refined + the constant-style compute-once branch, dry-run
  proof), the full `/resample` 409/404/409/423 ladder incl. the legacy
  no-raw_path row, `/diagnostic` 404s + payload, `/quality` 409 without
  pixel meta + a real stored/candidate score, `/fit` 404, both chart image
  endpoints (PNG magic + cache headers), the single-glyph `/write` read,
  `/write/word` input bounds + the ligature-decompose fallback over HTTP,
  the new bbox geometry 422s, and the styles/sources/hands get-by-id 404s.
  `api/routers` coverage: templates 41→57 %, chart 47→84 %, write 61→67 % (#208).
- **Pooled nib/pen memoisation unit tests.** `tests/test_rendering_pool.py`
  pins the TTL cache the admin-trace→public-render coherence hangs on
  (hit, expiry, explicit invalidation, no-scan for constant styles) with a
  fake repository and a frozen clock — `api/rendering.py` 68→90 % (#208).
- **Guard against silent lab-test skip rot.** The glyphlab/wordlab/pairlab
  suites skip in CI on gitignored fixtures by design, so a renamed export
  dir would disable them forever without anyone noticing;
  `tests/test_lab_fixture_wiring.py` pins the consumers' fixture dirs to
  the exporters' output dirs and the shared manifest name (#208).
- **Vitest suite for the glyph lock/split helpers.** `domain/glyphs.test.ts`
  (10 tests) pins `siblingKeys` (incl. the s/ſ allograph overrides),
  `isLetterSplit`'s `.some` contract and `quizKeysFromLocked` (lock-as-one
  collapse, canonical-preferring representative, split units, punctuation
  exclusion, allograph separation) (#208).
- **Own-code deprecations now fail the test suite.** The deprecated
  `HTTP_422_UNPROCESSABLE_ENTITY` starlette constant (9 accumulated
  warnings) is renamed to `HTTP_422_UNPROCESSABLE_CONTENT` across the
  routers, and `filterwarnings` turns DeprecationWarnings raised from
  `api`/`core`/`tools` code into errors — third-party warnings stay
  warnings (#208).
- **`/verify-migrations` skill + a hardened CI migrations job.** The CI job now
  runs the full sequence — `alembic upgrade head`, `alembic check`
  (model↔migration autogenerate drift) and a `downgrade -1`/`upgrade head`
  roundtrip — against its throwaway Postgres 16; the new skill runs the exact
  same sequence locally (Docker or the container's unprivileged Postgres), so
  the shared Cloud SQL DB never sees an untested revision. This closes the
  Alembic entry in CLAUDE.md's "known gaps without a loop" (#204).
- **Post-deploy prod smoke.** `api/cloudbuild.yaml` ends with a smoke step
  against the freshly deployed revision: `/health`, `/styles` non-empty,
  `/write/word?text=lesen` returns items, and an uncredentialed write answers
  401 (fail-closed gate proven live) — a bad image that still answers /health
  can no longer ship silently (#204).
- **Frontend coverage reporting.** `npm run test -- --coverage`
  (`@vitest/coverage-v8`) uploads to Codecov under a new `frontend` flag
  (informational patch status to start); `app/` is no longer ignored in
  `codecov.yml`, so SPA regressions become visible to the patch gate (#204).
- **`REGEN_SHAPING=1` regen path for the shaping-twin fixture.** Mirrors the
  compose-golden pattern: a legitimate shaping change regenerates
  `tests/fixtures/shaping_cases.json` from the Python source of truth instead
  of hand-editing JSON that two suites assert (#204).
- **Pre-commit config.** `ruff-check` + `ruff-format` hooks (same versions CI
  pins), so format-only red CI runs stop happening; ESLint stays CI-only (#204).
- **`docs/reference/write-api.md`.** The shipped public render endpoints
  (`/write/glyphs` + `/write/word`) graduate from the proposal into a proper
  reference doc (pipeline, wire format, cache semantics, render-cache
  consumption), indexed in `docs/index.md` (#204).

### Changed

- **CORS is now environment-scoped.** Production allows only the
  `kurrentschrift.ink` origins; the localhost/LAN developer conveniences no
  longer apply to prod (where `allow_credentials` rides the CF Access
  cookie). An env override remains available (#211).
- **Template writes commit before invalidating the pooled-nib cache**, so a
  concurrent public read can no longer repopulate the 600 s TTL cache from
  pre-write state (#211).
- **Ligatures require both characters lowercase** in the shaping twins
  (Python + TS): `sT` / `McHale` no longer swallow capitals into
  `longst`/`ch` ligatures; pinned by new shared fixture cases (#211).
- **Wizard stroke capture stores relative timestamps.** Points now carry
  `performance.now() - traceEpoch` instead of a `t=0` first point followed
  by raw epoch values — saved traces become usable for the post-MVP
  velocity/style analysis (#211).
- **Quiz play/results panels use semantic headings and the type ladder.**
  Section titles are real `h2`/`h3`s in ladder variants (Playfair-600 rule);
  ad-hoc pixel sizes are mapped to the nearest rung, deliberate display
  figures are marked as such (#211).
- **Public copy audit fixes.** The Gleichzugfeder paragraph no longer calls
  the *pen* a school script; the 1915 timeline entry drops the four-year
  hedge; the Schriftkunde lead anakoluth is split; the Tafel intro says
  "Schreibvorlagen" instead of claiming "die drei Ausgangsschriften"; the
  hero caption is honest about being type, not the engine; the quiz SEO line
  no longer overclaims; the Federprobe page finally carries its own name as
  the h1; "kuratiert" jargon is replaced; the worksheet uses the DIN/Süß
  terms (Ober-/Mittel-/Unterlänge, "Mittellänge (Schreibhöhe)") instead of
  Band/x-Höhe (#211).
- **Impressum wording made defensible.** EU data-centre claim now names
  Google/Cloudflare as US providers certified under the EU-US Data Privacy
  Framework; the rights paragraph is reconciled with the 30-day server logs;
  date bumped to July 2026 (#211).
- **Quiz gloss corrections.** "Groschen" (era-scoped: 10-Pfennig piece only
  in the Kaiserreich) and "Witwe" (precise definition) fixed in the
  generator, the regenerated word bank, the bundled fallback bank, and
  in place via migration `0016_quiz_gloss_fixes` (#211).
- **The quiz is named "Lese-Quiz" in the UI too.** The six "Buchstaben-Quiz"
  strings (page title, hub/landing/Schriftkunde cards, SEO title) and the
  letters-only SEO/landing descriptions now match the shipped scope
  (letters + whole words), consistent with the docs rename below (#211).
- **Docs sync.** copilot-instructions' schema section now states both
  template unique constraints (the `(style_id, glyph_key, variant)` one
  shipped in 0015) instead of calling `glyph_key` UI-only;
  `write-api.md` documents the single-glyph read; the letter quiz is renamed
  to the shipped reading quiz (letters + words) across README/docs/guides;
  the two agent guides agree on read-first and language rules; implemented
  proposals are annotated in `docs/index.md`; README explains the
  Sütterlin-first validation order and lists `tools/`/`tests/` (#211).
- **Cloud Run request timeout lowered to 60 s** (from 600) — nothing
  legitimate runs ten minutes (#211).
- **Deploys go no-traffic → smoke → promote.** `api/cloudbuild.yaml` used to
  route 100 % of traffic and only then smoke — a bad revision served users
  until the build went red. The deploy now carries `--no-traffic` +
  `--tag=candidate` + a deterministic `--revision-suffix`, the smoke suite
  probes the candidate's tag URL (and asserts the tag still points at this
  build's revision), and a final `update-traffic --to-revisions` step promotes
  exactly the smoked revision — never a concurrent build's unsmoked one (#210).
- **The Tafel boots from the slim bbox read.** `BboxStatusOut` gains the six
  layout scalars (`x0/x1/y0/y1/baseline_y` + flags) the sheet layout needs,
  and `useGrundtafeln` switches from the full `BboxOut` list — the same
  multi-MB mask/ink/patch JSONB payload the quiz was weaned off in the last
  audit round — to `GET /bboxes/status`. The three chart scans (~1.4 MB of
  JPEG, two below the fold) now load lazily like the other public images (#210).
- **One version source for the API.** `api/main.py` read `0.2.0` while
  pyproject said `0.1.0` and the last release was 0.13.0; `/docs` now reads
  `project.version` from the shipped `pyproject.toml` (bumped to 0.13.0), and
  the release note covers the bump (#210).
- **pre-commit runs ruff through uv.** The mirror-based hooks pinned their own
  `rev` that Dependabot never bumps — pre-commit-green/CI-red was weeks away;
  the hooks are now `repo: local` `uv run --extra dev ruff …`, so uv.lock is
  the single ruff version source (#210).
- **Palette rgba literals replaced with `alpha(token, …)`.** The quiz panels
  and the Tafel sheet baked `paper.viridian`/`pigment.vermilion`/`paper.line`
  into rgba strings a palette retune would silently miss — `PublicHeader`'s
  bar background had in fact already drifted from a pre-retune `paper.bg`
  (rgb 231,221,193 vs the token's 231,218,191); all derive from the tokens now (#210).
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
  category (#209).
- **CI frontend job on Node 22** (20 reached EOL 2026-04-30); `app` engines
  field now requires `>=22` (#204).
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
  `sprachregelung.md` documents the EN-proposals exception (#204).
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
  (full home title for no-JS crawlers, description trimmed to ~155 chars) (#202).
- **`/fit` and `/quality` are admin-gated; the crop endpoint leaves the event
  loop.** Both diagnostics cost seconds of pure CPU per call and back
  admin-only workflows, so they now require the admin credential like the
  writes (the SPA already sends it on every request); `GET /crop` runs its
  chart decode + binarisation in the threadpool like the other CPU-bound
  endpoints instead of freezing concurrent public requests (#201).
- **Admin locale namespaces left the public bundle.** The `admin`/`wizard`
  message catalogs moved from the shared locales barrel into a new
  `@/locales/admin` superset barrel imported only by admin code — ~24 kB of
  admin-only German strings no longer ship to every visitor (locales chunk
  51.7 → 45.5 kB gzip) (#201).
- **Boot states keep the navigation, and the cold-start copy speaks German,
  not ops.** The quiz and Tafel cold-start/loading/error states render inside
  the public layout (header + footer stay usable through the ~47 s worst
  case), and the boot message now says the server is waking up instead of
  "Cold Start" (#201).
- **Accessibility polish on the public pages.** The quiz verdict line is an
  `aria-live` region and focus moves to "Weiter" after a wrong answer (the
  disabled answer buttons used to drop focus on `<body>`); landing cards and
  header nav links gained visible `:focus-visible` outlines; the Federprobe
  disclaimer switched from the too-light `sepiaFaint` to readable `sepia`; the
  404 page sets its own title (#201).
- **Portable JSON column type.** Model columns now declare
  `JSON().with_variant(JSONB, "postgresql")` — identical behaviour on
  Postgres, creatable on SQLite for the new API test harness; migrations keep
  their own explicit JSONB types (#201).
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
  lines corrected (#201).
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
  stays byte-identical and the full core suite is unchanged (#200).
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
  reconciliation (#199).
- **Folded `WrittenWord`'s private `/write/word` cache into `renderCache.ts`.**
  The composed-word FIFO cache lived in a second module-level `Map` inside
  `WrittenWord` with its own key scheme, undermining the "ONE shared render
  cache" invariant. It is now `fetchRenderWord` alongside the glyph cache
  (same key helper, same cold-start retry, same evict-on-error) — no private
  render cache remains outside `renderCache.ts` (#199).
- **Trimmed `app/src/domain/shaping.ts` to the quiz-gating subset.** With word
  composition living server-side (`core/compose.py`), the TS shaper only needs the
  `text → glyph_keys` mapping the quiz word-bank gating consumes (`shapeText` +
  `glyphKeysOf`). Dropped the now-dead exports `decomposeLigatureSlot` and
  `stripFugen`, and made `shapeWord`/`FUGE` module-private; the header note now
  states the reduced scope and points at the shared fixture that keeps the mapping
  in sync with `core/shaping.py`. No runtime behaviour change (the quiz imports are
  untouched) (#198).
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
  `HTTPException`s use named `status.*` constants. Response shapes are unchanged (#197).

### Removed

- **Orphaned design artifacts in `docs/reference/`.** The pre-design-system
  landing mockup `kurrentschrift-landing.html` (Google-Fonts era, referenced
  by nothing) and the duplicate `gl-germancursive.woff2` (the live copy is
  `app/src/assets/fonts/`) are gone (#209).
- **Unused runtime dependencies `cairosvg` and `python-multipart`.** Neither is
  referenced anywhere in the codebase; both (plus cairosvg's native transitive
  chain) leave the Cloud Run image (#201).

### Fixed

- **Cross-source render-cache poisoning.** `WrittenGlyph` seeded admin
  payloads from the runtime-switched active source under the *public*
  source's cache keys, so after a source switch in the admin, `/quiz` and
  `/tafel` could serve the wrong script in the same SPA session. The
  component now takes a `sourceId` prop used for peek/seed/fetch alike,
  threaded from all three admin surfaces (#211).
- **Quiz word bank no longer degrades silently on cold start.** The boot
  read now retries like its siblings instead of falling back to the small
  bundled bank for the whole session after one failed fetch (#211).
- **Out-of-chart bboxes are rejected (422)** instead of storing a box that
  later 500s the public `/crop` with a zero-size crop (#211).
- **DELETE /templates and /bboxes return 404 for nonexistent rows** instead
  of a false 204 on a typo'd glyph key (#211).
- **Error details no longer leak internals.** The public chart 404 hid the
  absolute container path and the style-resolution 500 its referential
  detail; specifics now go to the server log (#211).
- **`/hands` responses carry the shared Cache-Control** like styles/sources (#211).
- **`/fit` query params are bounded**; `require_db`'s 503 distinguishes
  "not configured" from "initialisation failed" (#211).
- **Quiz results word render falls back to plain type on error** instead of
  spinning forever after a cache eviction + failed refetch (#211).
- **`/diagnostic` is admin-gated like its compute siblings.** The 3-column
  diagnostic re-runs the image pipeline (chart decode + binarise +
  skeletonise, ~0.2 s CPU) per request; `/fit` and `/quality` were gated for
  exactly that reason but `/diagnostic` stayed public and uncached on the
  max-instances=1 service. Only admin surfaces consume it — the public
  renderer reads the cached `/write` payloads. The admin-gate HTTP test
  matrix now includes it (#207).
- **Structural uniqueness for `glyph_key`.** Every template read — including
  the public `/write` endpoints — keys on `glyph_key` via
  `scalar_one_or_none()`, so two rows sharing `(style, glyph_key, variant)`
  would turn every read into a 500; the API's 409 backstops are
  read-then-write and bypassable out of band. Migration 0015 adds the unique
  constraint (mirrored in the model), making the backstops UX instead of the
  only defense (#207).
- **Bbox saves reject degenerate rectangles.** `PUT /bboxes/{key}` accepted
  inverted or negative rectangles (`x1 <= x0`, `y1 <= y0`), which stored fine
  and then 500ed the public crop/derivation paths on an empty crop; the
  handler now 422s with a clear message, alongside the existing
  baseline/midband check (#207).
- **Cross-source pen-pool invalidation.** A style can pool from several chart
  sources (Kurrent: loth-1866 + petzendorfer-1889); a trace/resample/delete
  issued through source A that touches a template whose provenance is B left
  B's pooled nib/pen stale for the 10-minute TTL. Template writes now clear
  the whole style's pools (they are tiny), with a unit test pinning it (#207).
- **Cache-Control on the remaining public reads.** `GET /bboxes/status` (the
  quiz boot) and the crop PNGs (quiz prompt fallback; the wizard busts via
  its version param) now carry the shared public cache header; `GET
  /templates` deliberately stays uncached — the admin sidebar reads the same
  list and needs a fresh `has_data` right after a trace, and the code now
  says so (#207).
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
  range gained an academic reference (Boser/Hofmann 2019) (#206).
- **Quiz gloss for "Gulden": silver, not gold.** The 19th-century South
  German Gulden was a silver coin (only the name derives from the medieval
  gold "guldin"); the generator source, `quiz_words.json` and — via new
  migration 0014 — the already-seeded DB row now read "alte Silbermünze
  (süddeutsche Währung)" (#206).
- **Impressum/llms.txt no longer overclaim synthesis.** "Alle gezeigten
  Schriftzüge sind … kein historisches Original" contradicted the
  Schreibtafel's genuine public-domain scans and the Koch 1928 original on
  /schriftkunde; both texts now distinguish synthesized forms (marked as
  such) from the PD originals shown with provenance. The privacy section's
  "keine personenbezogenen Daten" now carves out the 30-day server logs the
  same page already discloses (IPs are personal data) (#206).
- **Copy polish across the public pages.** Landing no longer claims all
  three scripts are engine-written ("die Sütterlin schreibt hier schon");
  the Federprobe card invites a word *or short sentence* (the input takes
  48 chars); "↻ noch einmal schreiben" matches the other replay labels;
  the worksheet intro gains its missing article; the written-glyph aria
  label says "alte Schreibschrift" instead of naming Kurrent while the
  engine writes Sütterlin; trailing ellipses uniformly get their narrow
  space; the Schwellzug explainer no longer has the *pen* swelling; the
  show-script font is consistently "GL-GermanCursive"; the sources intro
  points readers to the GitHub fact sheets (#206).
- **Straight-quote pairing spans the whole text, not one word.** The shaping
  twins (`core/shaping.py` + `app/src/domain/shaping.ts`) reset the
  low/high quote parity per whitespace-split word, so a multi-word quote —
  `"Guten Tag"` in the Federprobe — rendered two opening „ quotes. The parity
  now threads through `shape_text`/`shapeText`; the shared fixture gained the
  multi-word case and was regenerated via `REGEN_SHAPING=1` (#205).
- **Quiz word prompt no longer spins forever on a failed compose.** The word
  branch of the question card passed no `onError` to `WrittenWord`, so a
  compose request that died mid-cold-start (the render cache's retry budget is
  much shorter than the boot loads') left an infinite `CircularProgress`. The
  prompt now offers the same retry affordance as the Federprobe — a plain-type
  fallback would hand the solution to the learner, so it retries instead; the
  post-answer comparison forms fall back to plain type (#205).
- **Quiz keyboard focus survives a correct answer.** Focus moved to "Weiter"
  only on a wrong pick; on a correct one every answer button disables and focus
  fell to `<body>` — reduced-motion users got a "Weiter" button that never
  received focus, everyone else lost their tab position each auto-advance. The
  advance control now receives focus on every verdict, and after the advance
  focus returns to the answer grid (#205).
- **`quiz_words.created_at` is NOT NULL like every other `created_at`.**
  Migration 0010 forgot `nullable=False` (0004 declares it on all other
  tables) while the model implies NOT NULL — the very first `alembic check`
  run caught the drift; migration 0013 tightens the column (safe: it carries
  `server_default=now()`) (#204).
- **Slim public reads for the heavy list payloads.** New
  `GET /sources/{id}/bboxes/status` returns only the availability flags
  (glyph_key, locked, split) and `TemplateRepository.list_summaries()` feeds
  the template list from a column-select — the admin sidebar and the public
  quiz no longer decode multi-MB of `raw_path`/`anchors`/mask/ink/patch JSONB
  for six scalar fields. The quiz left the pinned AdminProvider entirely: a
  new `useQuizSource` hook boots from source + template summaries + status
  flags (same cold-start retry), so `/quiz` stops downloading the full
  crop-editing bbox payload (#202).
- **jsx-a11y lint gate.** `eslint-plugin-jsx-a11y` (recommended rules) now runs
  in the frontend lint, so the mechanical accessibility slips on the SVG-heavy
  custom surfaces get caught before review (#202).
- **`PaperCardLink` + `PaperCardCta`.** The public "paper card that is a link"
  (hover/focus lift, viridian border, focus ring, CTA underline sweep) that
  LandingView, HubView and the Schriftkunde try-cards each copy-pasted is now
  one shared component — contrast and focus fixes land once (#202).
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
  all three API suites reuse it (#202).
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
  missing-as-null, error eviction, cold-start retry) (#201).
- **Brand icons + social preview image.** `favicon.ico` (multi-size),
  `apple-touch-icon.png` and a 1200×630 `og.png` — the viridian Kurrent K on
  the paper gradient, rendered from the bundled GLKurrent face — wired into
  `index.html` with a `summary_large_image` twitter card; link previews and
  browser tabs stop being generic (#201).
- **Shareable Federprobe.** The typed text syncs to a `?text=` URL parameter
  (debounced, history-friendly) with a "Link kopieren" button and a character
  counter on the input — the page's output is now deep-linkable (#201).
- **"Jetzt ausprobieren" cross-links on `/schriftkunde`.** The primer closes
  with hub-style cards into the quiz, the Schreibtafel and the Federprobe
  instead of dead-ending after the chronology (#201).
- **Chart image LRU cache + Cache-Control on stable reads.** Decoded chart
  grayscale arrays are cached per resolved path (read-only, max 4 entries), so
  repeated crops/diagnostics/fits stop re-decoding the same immutable PD scan;
  `/styles` and `/sources` responses now carry the shared cache policy and the
  chart image caches for a day (#201).
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
  frontend CI job (build-only before) (#198).
- **WCAG AA contrast for viridian text and the quiz answered state.** New
  `paper.viridianText` (#2e6152 — derived for contrast, not a period hex;
  5.15:1 on the paper ground vs 3.28:1 for the accent #40826d) is used
  wherever viridian is body-size text: card CTAs, the hub/landing links, the
  quiz score and verdict, the Scribe copy confirmation, Tafel chip/provenance
  links, prose-link hovers. `quiz.resolvedText` darkened to #6e5c42 (5.5:1 on
  the answered button face, was 3.61:1). The accent #40826d stays for large
  display, initials, borders, fills and focus rings (#202).
- **Contiguous heading outline on every public page.** Card titles now carry
  explicit heading components (hub cards `h2` under the page `h1`; landing,
  Schriftkunde and Tafel cards `h3` under their `h2` section headings), and
  MUI's default subtitle→`<h6>` mapping is overridden to `<p>` at the theme
  level — definition-row terms and timeline years no longer appear as phantom
  section headings to screen readers (#202).
- **The nav marks the current area.** PublicHeader links carry
  `aria-current="page"` plus a visible active state (ink colour + full
  viridian underline) for the area whose page is open (#202).
- **`/trace` can no longer cross-link template rows.** The template upsert
  conflicts on `(style, glyph, position, variant)` while reads go by
  `glyph_key`, so a client bug pairing a wrong URL key with a payload identity
  could conflict-update another row and rewrite its `glyph_key` — reads then
  silently 404 on the shared prod DB. `POST /trace` now derives the expected
  key from the shared registry (`core.shaping.expected_glyph_key`, the Python
  twin of `glyphs.ts`; `{base}-{position}` convention as fallback) and rejects
  a mismatch with 422 (#202).
- **DB engine init race closed.** The lazy `asyncio.Lock` getter in
  `core/database/connection.py` was itself check-then-set, so two first
  requests could each mint their own lock, both enter `init_db()`, and the
  loser's engine (and Cloud SQL connector) leaked without `dispose()`. The
  lock is now created at import; the dead `_sync_init_lock` is gone (#202).
- **No more raw English error strings on public pages.** `/quiz` and `/tafel`
  showed `String(e)` (e.g. "TypeError: Failed to fetch") as the BootStatus
  detail under a German title; both now show a fixed German sentence
  (`common.boot.sourceUnreachableDetail`) and log the exception to the console (#202).
- **A late word-compose rejection can no longer evict a fresh cache entry.**
  `fetchRenderWord`'s error eviction now checks entry identity before deleting
  (like the glyph cache): after a FIFO eviction + re-fetch under the same key,
  the old promise's rejection used to delete the new, valid entry (#202).
- **The nav's current-area marker covers the standalone tool routes.** /quiz
  and /tafel light up Lesen, /federprobe lights up Schreiben (they keep their
  stable top-level URLs and are not nested under the hubs); only the exactly
  matching page uses `aria-current="page"`, area membership uses `"true"` (#202).
- **CHANGELOG `[Unreleased]` consolidated to one heading per category.**
  Successive PR insertions had produced duplicate Added/Changed/Fixed headings
  with bullets filed under the wrong category; regrouped per Keep-a-Changelog (#202).
- **The Cloud SQL connector fallback is now truly async.** The
  `INSTANCE_CONNECTION_NAME` path built a *sync* pg8000 engine and handed it to
  `async_sessionmaker(..., class_=AsyncSession)` — the first session would have
  raised `ArgumentError` and `close_db` would have crashed on `await
  engine.dispose()`; it now uses the native async Cloud SQL Connector with an
  asyncpg `async_creator`. A failing lazy `init_db()` in the session dependency
  is also caught and surfaces as the clean 503 instead of an unhandled 500 (#201).
- **Wizard brush commits can no longer overwrite each other.** All bbox writes
  are serialized through one queue and compute their payload from the
  then-current bbox at write time — two quick eraser/ink strokes (S-Pen taps
  faster than the PUT round-trip) used to both build on the same stale state,
  silently dropping the first stroke. Bbox saves also stopped echoing a stale
  `n_anchors` back, which used to revert the server-side sync with the derived
  canonical (`_sync_bbox_anchor_count`); and the canvas renders committed
  strokes/patches/saved-trace through memoised layers, so a 240 Hz pen gesture
  only re-renders the in-flight stroke (#201).
- **Federprobe and Schreibtafel fail loudly instead of silently.** A failed
  compose fetch on `/federprobe` now shows an error message with a retry button
  instead of an endless spinner, and a failed letter batch on the Tafel shows a
  notice + retry instead of silently rendering an empty ruled sheet (#201).
- **Mask preview halves its binarisation work.** The "Maske zeigen" preview
  derives the filled mask from the already-thresholded raw mask via
  `fill_small_holes` instead of running the adaptive threshold twice
  (identical output) (#201).

## [0.14.0] — 2026-07-13 — Specimen-true joins + compose calibration

### Changed

- **Pairlab-calibrated placement (O1).** `core/compose.py` places letters with two
  measured corrections: a HIGH exit is treated as a coupling-stub tip, not the pen's
  true departure — the next letter tucks back under it proportionally to the exit
  height (`TUCK_RATE`·(exit − 0.6)⁺; the d-class needed −0.33 xh) — and a BACKWARD
  exit tangent (the w/v bow) gets `BACKWARD_INK_CLEARANCE` 0.30 instead of 0.14 (the
  join must clear the whole bow; w joins measured +0.23 xh too tight). Re-measured
  against the pairlab independent fits over all 48 scorable specimen words: joins
  needing ≥ 0.25 xh correction drop from 31 to 21 of 146 (d-class −0.33 → −0.07,
  w-class +0.23 → +0.08 median) (#179).
- **Coupling anchors for high-exit joins (O2, B side).** After a Deckstrich bow,
  d-loop or r-arm exit (≥ 0.7 xh) the generated connector no longer bridges to the
  next letter's entry-stub foot ("shelf") but falls onto the RISING flank of its
  first downstroke at y 0.78, and the chart cell's stub piece below the anchor is
  removed from the centerline and the filled silhouette (new
  `core/template.py::erase_silhouette_piece`). Word-initial stubs stay — they are
  the Anstrich; low arcade joins are untouched (the standard diagonal is generically
  right per the pairlab findings) (#179).
- **Level Auslauf for high word-final exits.** A word ending on a high forward exit
  (the r-arm) now runs a short level finishing stroke (0.25 xh) like the plates,
  instead of stopping dead at the arm end — `der`/`der-2` carried the bench's
  largest width penalties for the missing stroke. Words ending low keep their
  rising Endstrich (#179).
- **Word bench headline** 0.1253 → 0.1183 (−5.6 %) over the frozen `jul08`
  references; `pair_loss` (report-only) 0.199 → 0.195. Loop protocol, keeps,
  discards (incl. the measured-but-rejected A-side d-stub trim) in
  `docs/reference/qualitaetsmetrik.md` §6, Lauf `jul11`; the compose golden fixture
  is deliberately re-pinned (#179).
- **Doc & instruction-sync hygiene.** Re-aligned `.github/copilot-instructions.md`
  with `CLAUDE.md`: corrected the stale "no tests exist yet", "ruff/ESLint when
  configured" and "no automated AI workflows configured" claims (a pytest suite,
  ruff, and `.github/workflows/ci.yml` all exist); fixed the dead `app/src/constants.ts`
  and `app/src/components/wizard/SetupWizard.tsx` paths to `app/src/domain/glyphs.ts`
  and `app/src/sections/admin/setup-wizard/`; added `quiz_words` to the schema table;
  and added the missing Working Guardrails section. Removed the stale references to the
  deleted `app/src/domain/compose.ts` in `app/src/domain/shaping.ts`,
  `app/src/sections/scribe/ScribeView.tsx` and the `schreibsystem-und-wortbench.md` proposal. Added the `kurrent-writer-and-recognizer.md`
  proposal and `docs/notes/` to `docs/index.md` (#186).

### Fixed

- **Third wordbench set: the Abb. 22 Schülerschrift plate (cross-hand reference).** The
  1922 Leitfaden's only other connected Ausgangsschrift specimen — a pupil's hand
  (Bruno Krüger, 3rd school year, Breitkantfeder, 106 words of Hoffmann von
  Fallersleben's "Hab' Dank, du lieber Wind!") — is now measured like Abb. 19
  (`words-abb22.png` + 106 sidecar entries, boxes proposed, line-QC'd and hand-corrected).
  Sidecar entries carry a new optional `set` field; `export_fixtures`/`run`/`wordlab`
  accept custom set names, so the plate freezes into its own sibling fixture root
  (`suetterlin-1922-abb22`, `--set abb22`) and its cross-writer numbers are never averaged
  into the same-hand headlines. Provenance + PD rationale in the source's `SOURCE.md` (#188).
- **ESLint gate for the SPA.** Added a flat `app/eslint.config.js` (JS +
  typescript-eslint recommended + `react-hooks`, react-refresh as warnings),
  a `npm run lint` script, and an ESLint step to the CI frontend job — the
  `react-hooks/exhaustive-deps` suppressions in the tree are now enforced
  instead of inert. Fixed the findings this surfaced: `prefer-const` in
  `TafelView.tsx`, a missing hook dep in `RederiveAllDialog.tsx`, and added
  the missing justification to a `WrittenWord.tsx` suppression; kept the
  `_`-prefix unused-args convention and allowed intentional non-breaking
  spaces in UI strings. Updated `.github/copilot-instructions.md` to record
  that ESLint is now configured (#187).
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
  pure geometry core (`tests/test_pairlab.py`) (#178).
- **Transition findings 2026-07-11** (`docs/proposals/uebergaenge-befund.md`): the
  pairlab survey over 87 occurrences / 45 pairs. Placement is the largest single
  error (39/87 need ≥ 0.25 xh correction); the standard diagonal join is generically
  right once letters sit correctly (f→e/t→e's bench penalty was placement); high
  exits (d loop, o/b/v/w Deckstrich bows, the r arm) systematically REPLACE both
  coupling stubs (0.2–0.4 xh per side) with one diagonal into the next letter's
  first-downstroke apex — confirming the stub hypothesis class-wise, not per pair.
  Solution options O1–O3 (placement first, coupling anchors, gated pair overrides)
  with cross-references from `qualitaetsmetrik.md` §6 and Vorschlag B (#178).
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
  pass and the compose golden fixture is deliberately re-pinned (#188).

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
