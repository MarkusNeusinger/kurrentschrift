"""`tools.pairlab.affinereg` — the Gauß-Verschiebung seed: an affine per letter, registered on the ink image.

The registration is tested on what it claims: a stroke drawn onto a blank page,
then shifted, scaled and rotated, is found again from its unmoved twin — coarse
to fine, through the same cost the follower seeds from.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize

from tools.pairlab.affinereg import SIGMAS_PX, _affine_matrix, _apply, _cost


def _stroke(n: int = 120) -> np.ndarray:
    """An S-shaped stroke in pixel space, about 40 px tall."""
    t = np.linspace(0.0, 1.0, n)
    return np.column_stack([60.0 + 25.0 * np.sin(2.0 * np.pi * t), 30.0 + 40.0 * t])


def _ink_of(pts: np.ndarray, shape: tuple[int, int] = (100, 140), width: int = 2) -> np.ndarray:
    mask = np.zeros(shape, dtype=bool)
    for x, y in pts:
        xi, yi = int(round(x)), int(round(y))
        mask[max(0, yi - width) : yi + width + 1, max(0, xi - width) : xi + width + 1] = True
    return mask


def _register(pts: np.ndarray, mask: np.ndarray, xh: float = 30.0) -> np.ndarray:
    ink_pts = np.argwhere(mask)[:, ::-1].astype(float)
    theta = np.zeros(6)
    for sigma in SIGMAS_PX:
        blur = gaussian_filter(mask.astype(float), sigma)
        blur /= max(float(blur.max()), 1e-9)
        theta = minimize(
            _cost, theta, args=(pts, pts[0].copy(), blur, ink_pts, sigma, xh), method="Powell", options={"xtol": 1e-3}
        ).x
    return theta


def test_identity_is_the_identity() -> None:
    pts = _stroke()
    assert np.allclose(_affine_matrix(np.zeros(6)), np.eye(2))
    assert np.allclose(_apply(np.zeros(6), pts, pts[0].copy()), pts)


def test_a_shifted_and_scaled_stroke_is_found_again() -> None:
    """The moved twin's ink, registered from the unmoved stroke: the recovered
    map lands the stroke back on the ink within a pixel."""
    pts = _stroke()
    truth = np.array([9.0, -6.0, np.log(1.25), np.log(0.9), 0.12, 0.05])
    moved_truth = _apply(truth, pts, pts[0].copy())
    mask = _ink_of(moved_truth)
    theta = _register(pts, mask)
    recovered = _apply(theta, pts, pts[0].copy())
    assert float(np.abs(recovered - moved_truth).max()) < 2.0
    # and the cost really went down against the untransformed start
    blur = gaussian_filter(mask.astype(float), SIGMAS_PX[-1])
    blur /= blur.max()
    ink_pts = np.argwhere(mask)[:, ::-1].astype(float)
    before = _cost(np.zeros(6), pts, pts[0].copy(), blur, ink_pts, SIGMAS_PX[-1], 30.0)
    after = _cost(theta, pts, pts[0].copy(), blur, ink_pts, SIGMAS_PX[-1], 30.0)
    assert after < 0.5 * before


def test_a_stroke_already_on_its_ink_stays_put() -> None:
    """The prior toward the identity: with nothing to gain, the map stays near it."""
    pts = _stroke()
    mask = _ink_of(pts)
    theta = _register(pts, mask)
    assert float(np.abs(_apply(theta, pts, pts[0].copy()) - pts).max()) < 1.5
