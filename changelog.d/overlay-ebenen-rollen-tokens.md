### Added

- **Overlay layer and role tokens, plus a `mono` token.** `app/src/styles/paper.ts`
  gains `layer`/`layerDash` (Spur · Pfad · Engine), `role`/`roleDash`
  (Tafel · Platte · Eigenhand) and a system monospace stack, and the design
  system carries them as a binding rule: a layer or a role is recognised from
  **Rollen-Etikett + Position + Strichart**, never from colour alone. A new
  `paper.test.ts` enforces it — every layer clears 3:1 against white AND against
  the plate ink, every role against both paper grounds, no token wears viridian,
  and each pair's deuteranope separation is asserted with the one collision the
  period palette cannot resolve (Ocker vs Zinnober) named so it can never widen
  unnoticed. The role tokens ship ahead of their consumer, which arrives with the
  Rollen-Spalte.

### Fixed

- **The admin's overlay colours were unreadable twice over.** The pen-path green
  reached only 2.71:1 on the white work surfaces it is drawn on, and over plate
  ink it met the engine's red in a pair no reader with a red-green deficiency can
  separate; a second such pair sat inside the token map, where the aggregate
  sketch drew vermilion against dark green. Both are gone: the traced line is one
  blue on both grounds, the engine keeps the red and is dashed where it lies over
  a crop, and the Laufform reference has a name of its own instead of borrowing
  the selection colour. Seven files had the hexes hard-wired, including the
  tracebench figures, which now agree with the admin on the engine.

### Changed

- **The German admin copy stops naming colours.** „erster Zug grün, letzter blau"
  is the exact sentence a colour-blind reader cannot use, and it breaks again on
  every palette tune. The captions name the meaning; the layer legend carries the
  colour and, since it now draws the line's stroke style rather than a dot, the
  distinction as well.
- **A terminal command is readable at the size it is meant to be typed at.**
  `TerminalCommand` takes the `mono` token and its size from `variant="body2"`
  (17 px) instead of a hard 14 px below the caption floor, and the sixteen other
  places that spelled `'monospace'` by hand now read the same token.
