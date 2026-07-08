# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Every PR adds its entries under `[Unreleased]`; a release moves that section under a new
version heading. Code changes are covered here — data-only commits (chart sources,
authored templates) are covered by their `SOURCE.md` provenance records instead.

## [Unreleased]

### Added

- **Broad-nib pen model — the Offenbacher Bandzugfeder writes for real.** `core/widths.py`
  gains the `BroadNib` model (`w(φ) = W·|sin(φ−α)| + t·|cos(φ−α)|` at Koch's constant 15°
  edge angle, primary source *Die Offenbacher Schrift*, 1928) and
  `core/template.py::chisel_union_rings` sweeps the W×t nib rectangle along the centerline,
  so chisel ends fall out naturally — never round caps. The writing path regenerates widths
  from the model (warp-invariant, inks generated connectors, repairs scan noise); the stored
  measurement is untouched and keeps serving the diagnostic. `api/rendering.py::pooled_pen`
  calibrates the nib per source from the pooled measured profiles.
- **Digits and punctuation as detached glyphs.** `0–9` and `. , ; : ! ? ' „ “ - – ( ) §`
  are real glyphs with `joins: false` in both shaping twins (`core/shaping.py`,
  `app/src/domain/{glyphs,shaping}.ts`): written without any Übergang, placed by whole-ink
  clearance, pen lift into them, Endstrich + diacritic flush before them. ASCII `-` maps to
  the historical double-stroke hyphen; straight `"` pairs low-then-high by occurrence
  parity. The admin sidebar gains Ziffern/Satzzeichen groups; digits are quizzable,
  punctuation is not; unauthored marks surface in the Federprobe "noch nicht kuratiert"
  note instead of failing silently.
- **Pen-aware composition.** `compose_word(…, pen=…)`: `pressure` (Kurrent Spitzfeder) caps
  generated strokes at the source's pooled hairline — pressure never travels between
  letters; `broad_nib` ships connectors as swept-nib rings (the client already fills rings,
  zero client changes). `pen=None` stays byte-identical: golden fixture, wordbench 0.125337
  and both glyph benches (Sütterlin 0.1865, Kurrent 0.1251) reproduce their baselines.
- **Design doc `docs/concepts/federmodelle.md`** — three pens, one render path: the
  Bandzugfeder law + chisel sweep, Spitzfeder hairline rules and the planned synthesis
  model/naturalness metric, the digits/punctuation glyph space, per-script authoring
  sources, and the rejected alternatives.
- **`tools/glyphbench --style offenbacher`** routes through the pressure derivation and the
  Schwellzug pixel metric (honest for extraction quality — it scores the measured profile)
  until a dedicated width-direction naturalness metric is calibrated.

### Fixed

- **Trailing punctuation no longer steals the round Schluss-s.** Positions are assigned per
  run of same joins-class, so `"Haus,"` keeps `s-final` (previously the comma made the s
  read as medial → long-ſ).

## Releases

No tagged release yet — the project is an in-progress MVP; entries accumulate under
`[Unreleased]` until the first cut.
