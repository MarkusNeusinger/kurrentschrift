### Added

- **The Gleichzug score now says where it takes its points off.** A new pure
  module, `core/quality_localize.py`, re-scores one stored Sütterlin chart
  letter against its crop with the frozen naturalness metric, called
  unchanged, and splits each of the six deductions („Abzüge“) into located
  sites (Abzugsstellen) in the crop-pixel frame the ruler measured in. Ecken
  and Kreuzungsflucht are split per corner and per passage as the literal
  `(1 − q)/N`, Doppelzug per missed ink pixel as `1/denominator`; Glätte,
  Senkrechte and Deckungslücke are split in proportion, the last one across
  Dice · Chamfer · Geo by its exactly additive log terms. The quantised edge
  rim is kept as one site „ohne Ort“ instead of a thousand one-pixel marks,
  and a recomputation that ever disagreed with the metric would drop its map,
  context included, rather than draw a wrong one. Geometry with a non-finite
  number or a non-positive x-height is refused up front instead of being
  apportioned as NaN. The promise the lens is built around holds on
  all 62 frozen Sütterlin letters with zero difference: a category's sites
  add up to the number shown for it, to its fourth digit (the unrounded parts
  as well as the apportioned four-place values). The five costliest sites
  across all categories are ranked as pins by linearised score points. The
  glyph bench is byte-identical before and after (`bench_loss` 0.212277,
  every per-glyph metric dict unchanged), because no frozen ruler was
  touched; the lens costs about 100 ms per letter on top of the chart load.
- **`GET /sources/{id}/templates/{glyph_key}/penalty-sites`, the lens's
  read.** Admin-gated and `private, no-store` like `/quality`, classified
  RESERVED in the public-surface pin, computed in the threadpool from the
  chart row (variant 0) and today's ruler rather than the stamp — the stored
  components ride along as `stamped` for the „gespeichert“ line. A legacy row
  without pixel-space trace meta answers 409, and so does a row the lens
  refuses (non-finite geometry, a non-positive x-height); a Kurrent or
  Offenbacher letter answers `sites: null` with `reason: "no_components"`,
  because its metric has no deduction categories and the two metrics are
  never mixed. The overlay itself follows in the admin UI.
