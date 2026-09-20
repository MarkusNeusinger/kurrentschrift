"""The paper-excursion kernel — the measurement, without the bench around it.

`tools.tracebench.excursions` is the K-D closure's standing sensor and it is
REFERENCE-FREE: it reads the distance from a path to the specimen's own ink.
Only its wiring is bench-shaped (frozen fixture root, bench frame, candidate
files), and the strip half of the repo needs the same number on another
substrate — its own binarised mask, at 300 dpi, on a hand nobody has traced
(`tools.eigenhand.pfad`, the Tintentreue sensor „Papier-Exkursion").

So the kernel is tested here on a synthetic mask, where the right answer is
known by construction, and the fixtures stay out of it entirely.
"""

from __future__ import annotations

import numpy as np
import pytest

from tools.tracebench.excursions import EXCURSION_THRESHOLDS, excursion_readings, ink_distance_px


# One horizontal ink line, 100 px long, on a 60x140 grid.
MASK = np.zeros((60, 140), dtype=bool)
MASK[30, 10:110] = True
XH_PX = 20.0


def _on_the_line(points: np.ndarray) -> np.ndarray:
    """Word units → this grid's pixels: x from 10, y measured up from row 30."""
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    return np.column_stack([pts[:, 0] * XH_PX + 10.0, 30.0 - pts[:, 1] * XH_PX])


def _readings(v: float, length: float = 4.0) -> dict[str, float]:
    reading = excursion_readings([[[0.0, v], [length, v]]], _on_the_line, ink_distance_px(MASK), XH_PX)
    assert reading is not None
    return reading


def test_the_distance_field_is_zero_on_the_ink_and_grows_off_it():
    dist = ink_distance_px(MASK)
    assert dist[30, 50] == 0.0
    assert dist[25, 50] == pytest.approx(5.0)


def test_a_path_that_rides_the_ink_has_no_excursion():
    reading = _readings(0.0)
    assert reading["max"] == 0.0
    assert all(reading[f"arc_{t}"] == 0.0 for t in EXCURSION_THRESHOLDS)


def test_a_path_beside_the_ink_is_measured_in_x_heights():
    # Half an x-height above the line: 10 px at xh = 20 px, and the whole path
    # is out there, so every threshold below it collects the full arc.
    reading = _readings(0.5)
    assert reading["max"] == pytest.approx(0.5, abs=0.02)
    assert reading[f"arc_{EXCURSION_THRESHOLDS[0]}"] == pytest.approx(4.0, abs=0.05)
    assert reading[f"arc_{EXCURSION_THRESHOLDS[1]}"] == 0.0


def test_the_arc_length_is_a_length_and_not_a_sample_count():
    # The doubling is the assertion: resampling at the ruler's own step is what
    # makes `arc_<t>` comparable between two paths of different densities.
    assert _readings(0.5, length=8.0)[f"arc_{EXCURSION_THRESHOLDS[0]}"] == pytest.approx(
        2 * _readings(0.5, length=4.0)[f"arc_{EXCURSION_THRESHOLDS[0]}"], rel=0.02
    )


def test_a_path_with_nothing_in_it_is_no_reading_rather_than_a_zero():
    assert excursion_readings([], _on_the_line, ink_distance_px(MASK), XH_PX) is None
