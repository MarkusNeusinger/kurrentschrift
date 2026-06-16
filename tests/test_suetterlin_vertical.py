"""Corner-aware verticalization of Sütterlin downstrokes (fixture-free, synthetic).

Covers `_verticalize_downstrokes`: a vertical downstroke that ends at a
within-stroke corner (Umkehrpunkt) must run straight to the corner and pull the
corner anchor onto the stem (the written model "down at 90°, stop, away again"),
without disturbing the up-going exit stroke past the corner. The bench is blind
to this sub-pixel shift, so it is asserted directly here.
"""

from __future__ import annotations

import numpy as np

from core.suetterlin import _verticalize_downstrokes


UNIT_PX = 65.0
STEM_X = 5.0


def _i_like_stroke() -> tuple[np.ndarray, int]:
    """A long vertical stem that drifts left into a bottom corner, then exits up-right."""
    down = [(STEM_X, y) for y in np.arange(10.0, 49.0, 1.0)]  # straight vertical, ~38px (> 0.45 x-height)
    drift = [(4.6, 49.0)]  # the skeleton's leftward pool just before the reversal
    corner = (3.8, 50.0)  # the bottom corner (Umkehrpunkt), veered left
    exit_up = [(6.5, 49.0), (8.0, 48.0), (9.5, 47.0)]  # the ~45° Aufstrich
    pts = np.array([*down, *drift, corner, *exit_up], dtype=float)
    corner_idx = len(down) + len(drift)
    return pts, corner_idx


def test_corner_pulled_onto_stem_only_when_corner_aware() -> None:
    pts, c = _i_like_stroke()
    old = _verticalize_downstrokes(pts, [0], UNIT_PX, None)  # legacy: no corner awareness
    new = _verticalize_downstrokes(pts, [0], UNIT_PX, [c])  # corner-aware

    assert old[c, 0] < STEM_X - 0.5  # legacy leaves the corner veered left
    assert abs(new[c, 0] - STEM_X) < 0.2  # corner-aware snaps it squarely below the stem


def test_exit_stroke_past_corner_is_untouched() -> None:
    pts, c = _i_like_stroke()
    new = _verticalize_downstrokes(pts, [0], UNIT_PX, [c])
    # The Aufstrich after the reversal keeps its own geometry (weight zeroed past the corner).
    assert np.allclose(new[c + 1 :, 0], pts[c + 1 :, 0])


def test_no_corner_keeps_the_easing_fillet() -> None:
    # Without a corner in range, behaviour is the legacy fillet: the bottom of the
    # run is NOT hard-snapped to the stem (a tangential ease into whatever follows).
    pts, c = _i_like_stroke()
    no_corner = _verticalize_downstrokes(pts, [0], UNIT_PX, [])
    legacy = _verticalize_downstrokes(pts, [0], UNIT_PX, None)
    assert np.allclose(no_corner, legacy)
