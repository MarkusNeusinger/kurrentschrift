# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Every PR adds its entries under `[Unreleased]`; a release moves that section under a new
version heading. Code changes are covered here — data-only commits (chart sources,
authored templates) are covered by their `SOURCE.md` provenance records instead.

## [Unreleased]

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
