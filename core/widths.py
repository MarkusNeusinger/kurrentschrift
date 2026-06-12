"""Width-profile resolver per script family (architektur.md §5).

The library stores ONE measured `half_widths` profile per template regardless
of style; `styles.width_resolver` selects how the renderer interprets it. The
stored profile always stays the measurement (non-destructive, re-derivable) —
resolution happens at render time, never at derivation time.

Resolvers:
- ``pressure``  — Kurrent Spitzfeder: the measured profile IS the Schwellzug
  (pressure-driven stroke-width modulation); render it as-is.
- ``constant``  — Suetterlin Gleichzug (ball-tipped Redisfeder, no pressure
  variation): collapse the profile to one width. MVP simplification: median
  per glyph; §5 ultimately wants the mean width per *source*, which needs a
  cross-glyph aggregate (post-MVP).
- ``broad_nib`` — Offenbacher Bandzugfeder: width is a function of stroke
  direction vs. nib angle. Not modelled yet (post-MVP §11 Canvas stroker);
  falls back to the measured profile, which on Breitfeder ink already carries
  the direction-dependent widths.
"""

import numpy as np


def resolve_half_widths(half_widths: np.ndarray, resolver: str) -> np.ndarray:
    """Apply the style's width resolver to a measured half-width profile."""
    half_widths = np.asarray(half_widths, dtype=float)
    if resolver == "constant" and half_widths.size:
        return np.full_like(half_widths, float(np.median(half_widths)))
    return half_widths
