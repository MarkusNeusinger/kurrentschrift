"""Width-profile resolver + pen models per script family (architektur.md §5).

The library stores ONE measured `half_widths` profile per template regardless
of style; `styles.width_resolver` selects how the renderer interprets it. The
stored profile always stays the measurement (non-destructive, re-derivable) —
resolution happens at render time, never at derivation time.

Resolvers:
- ``pressure``  — Kurrent Spitzfeder: the measured profile IS the Schwellzug
  (pressure-driven stroke-width modulation); render it as-is. Generated
  strokes (Übergänge, Endstrich) are Haarstriche by rule — pressure lives on
  the Grundstriche only, pushing a pointed nib upward digs it into the paper.
- ``constant``  — Suetterlin Gleichzug (ball-tipped Redisfeder, no pressure
  variation): collapse the profile to one width. MVP simplification: median
  per glyph; §5 ultimately wants the mean width per *source*, which needs a
  cross-glyph aggregate (post-MVP).
- ``broad_nib`` — Offenbacher Bandzugfeder: width is a pure function of stroke
  direction vs. the fixed nib angle (Koch 1928: the nib is guided WITHOUT
  pressure, edge held at a constant ~15° to the horizontal). On the writing
  path the widths are REGENERATED from the model (`BroadNib`), because the
  measured profile stops being valid the moment the path is warped (slant
  normalisation, fluent widening) and because generated Übergänge have no
  measurement at all; the measurement is used to CALIBRATE the nib per source
  (see `api/rendering.py::pooled_broad_nib`). The diagnostic keeps comparing
  the measured profile against the chart ink — the model would hide
  extraction errors there.
"""

import math
from dataclasses import dataclass

import numpy as np


# Bandzugfeder defaults — primary source Rudolf Koch, *Die Offenbacher
# Schrift* (1928): nib edge at a constant 15° to the horizontal (p. 10),
# upstroke ≈ ¼ of the downstroke width (p. 11) — which the |sin| law
# reproduces at the taught stroke directions. Width/edge measured on the
# repo's Koch chart (x-height ≈ 7–9 nib widths; hairline ≈ ¼ of the full
# width); both are per-source calibration values, the pooled measurement
# overrides these fallbacks (api/rendering.py).
BROAD_NIB_ANGLE_DEG = 15.0
BROAD_NIB_WIDTH_UNITS = 0.13  # full nib width W, x-height units
BROAD_NIB_EDGE_FRACTION = 0.25  # edge thickness t as a fraction of W


@dataclass(frozen=True)
class BroadNib:
    """The Bandzugfeder as a W × t rectangle held at the fixed angle alpha.

    Angles are degrees counter-clockwise from +x in template space (y up,
    baseline = 0). The effective ink width perpendicular to a stroke moving
    at direction ``phi`` is the rectangle's support width normal to travel —
    exact for the Minkowski sweep:

        w_perp(phi) = W·|sin(phi − alpha)| + t·|cos(phi − alpha)|

    (METAFONT's ``penrazor`` is the t=0 ideal; the t term is the physical
    nib edge that never writes a zero-width line.)
    """

    width_units: float = BROAD_NIB_WIDTH_UNITS
    angle_deg: float = BROAD_NIB_ANGLE_DEG
    edge_fraction: float = BROAD_NIB_EDGE_FRACTION

    @property
    def edge_units(self) -> float:
        return self.edge_fraction * self.width_units

    @property
    def half_vector(self) -> tuple[float, float]:
        """Half-nib vector h = (W/2)·(cos α, sin α) — the constant offset of
        the swept ribbon's rails from the centerline."""
        r = math.radians(self.angle_deg)
        return (0.5 * self.width_units * math.cos(r), 0.5 * self.width_units * math.sin(r))

    @property
    def edge_vector(self) -> tuple[float, float]:
        """Half-edge vector e = (t/2)·(−sin α, cos α), perpendicular to the nib."""
        r = math.radians(self.angle_deg)
        return (-0.5 * self.edge_units * math.sin(r), 0.5 * self.edge_units * math.cos(r))

    def half_width_at(self, tangent_deg: float) -> float:
        """Half of w_perp at one stroke direction (degrees, template space)."""
        d = math.radians(tangent_deg - self.angle_deg)
        return 0.5 * (self.width_units * abs(math.sin(d)) + self.edge_units * abs(math.cos(d)))


@dataclass(frozen=True)
class PenStyle:
    """Render-time pen behaviour, resolved once per (style, source) request.

    ``kind`` mirrors `styles.width_resolver`. ``nib`` carries the calibrated
    Bandzugfeder for broad_nib; ``hairline_half`` the pooled Haarstrich
    half-width (P10 of the source's measured profiles) that pressure-style
    generated strokes (Übergänge, Endstrich) are drawn at.
    """

    kind: str  # 'constant' | 'pressure' | 'broad_nib'
    nib: BroadNib | None = None
    hairline_half: float | None = None


def _per_stroke_tangents_deg(points: np.ndarray, stroke_starts: list[int] | None) -> np.ndarray:
    """Per-point travel direction (degrees) along a polyline, never bridging a
    pen lift: each stroke slice gets its own gradient."""
    points = np.asarray(points, dtype=float)
    n = len(points)
    out = np.zeros(n)
    starts = [s for s in (stroke_starts or [0]) if 0 <= s < n] or [0]
    if starts[0] != 0:
        starts = [0, *starts]
    bounds = [*starts, n]
    for a, b in zip(bounds[:-1], bounds[1:], strict=True):
        if b - a < 2:
            continue
        dx = np.gradient(points[a:b, 0])
        dy = np.gradient(points[a:b, 1])
        out[a:b] = np.degrees(np.arctan2(dy, dx))
    return out


def broad_nib_half_widths(points: np.ndarray, nib: BroadNib, stroke_starts: list[int] | None = None) -> np.ndarray:
    """Model half-widths of the fixed-angle nib along a polyline (per point)."""
    tangents = _per_stroke_tangents_deg(points, stroke_starts)
    d = np.radians(tangents - nib.angle_deg)
    return 0.5 * (nib.width_units * np.abs(np.sin(d)) + nib.edge_units * np.abs(np.cos(d)))


def resolve_half_widths(
    half_widths: np.ndarray,
    resolver: str,
    *,
    points: np.ndarray | None = None,
    stroke_starts: list[int] | None = None,
    nib: BroadNib | None = None,
) -> np.ndarray:
    """Apply the style's width resolver to a measured half-width profile.

    ``broad_nib`` regenerates the widths from the nib model when the geometry
    (``points``, same length as the profile) is supplied; without geometry it
    falls back to the measured profile, which on Breitfeder ink already
    carries the direction-dependent widths.
    """
    half_widths = np.asarray(half_widths, dtype=float)
    if resolver == "constant" and half_widths.size:
        return np.full_like(half_widths, float(np.median(half_widths)))
    if resolver == "broad_nib" and points is not None and len(points) == half_widths.size and half_widths.size >= 2:
        return broad_nib_half_widths(np.asarray(points, dtype=float), nib or BroadNib(), stroke_starts)
    return half_widths
