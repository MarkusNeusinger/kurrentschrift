"""Affine registration of a letter's composed stroke against the ink — the Gauß-Verschiebung.

The author's picture (2026-09-11): lay two signals over each other and move them
until the difference is minimal, in 2D, because the plate's Gleichzug stroke has
one width everywhere. That is image registration, coarse to fine. Per letter
slot the composed body centerline is the moving signal, the frozen ink mask the
fixed one; both are read through a Gaussian of falling width (`SIGMAS_PX`), and
an affine map about the letter's ENTRY point — shift, x and y scale, rotation,
shear — is optimised per scale with Powell. The cost is symmetric so a letter
can neither collapse onto a neighbour's stem nor stretch over one:

* precision — mean over the transformed samples of `1 − ink_σ(sample)`, the
  blurred ink read bilinearly, so a sample on the stroke's axis costs nothing;
* recall — mean over the ink pixels inside the letter's own window (the
  composed body's box widened by `WINDOW_PAD_UNITS`) of `1 − exp(−d²/2σ²)` with
  `d` the distance to the nearest transformed sample — the same Gaussian, read
  from the ink's side;
* a soft prior toward the identity, so a letter moves only when the ink pays
  for it.

No solve, no DB: reads the case's mask and the composition. Returns, per slot,
the 2×2 matrix and the shift in COMPOSED units (y up), ready for
`chain._letter_spec(affine=…)`, plus the cost before and after.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.optimize import minimize
from scipy.spatial import cKDTree

from tools.pairlab.analyze import _body_items
from tools.pairlab.analyze import _to_px as _to_px_composed
from tools.wordlab.cases import WordCase
from tools.wordlab.derive import WordDeriveResult


SIGMAS_PX = (4.0, 2.0, 1.0)
WINDOW_PAD_UNITS = 0.5
# Soft prior scales: one unit of each parameter costs as much as a whole stroke
# off the ink would. Shift in xh, the rest dimensionless (log scale, radians).
PRIOR_SHIFT_UNITS = 0.6
PRIOR_LOG_SCALE = 0.4
PRIOR_ROTATION = 0.35
PRIOR_SHEAR = 0.35
PRIOR_WEIGHT = 0.05


def _affine_matrix(theta: np.ndarray) -> np.ndarray:
    """(sx, sy, rot, shear) → the 2×2 map, y-down pixel frame."""
    _dx, _dy, lsx, lsy, rot, shear = theta
    scale = np.array([[np.exp(lsx), shear], [0.0, np.exp(lsy)]])
    c, s = np.cos(rot), np.sin(rot)
    return np.array([[c, -s], [s, c]]) @ scale


def _apply(theta: np.ndarray, pts: np.ndarray, entry: np.ndarray) -> np.ndarray:
    return entry + (pts - entry) @ _affine_matrix(theta).T + theta[:2]


def _cost(
    theta: np.ndarray,
    pts: np.ndarray,
    entry: np.ndarray,
    ink_blur: np.ndarray,
    targets: np.ndarray,
    sigma: float,
    xh: float,
) -> float:
    moved = _apply(theta, pts, entry)
    h, w = ink_blur.shape
    ys = np.clip(moved[:, 1], 0, h - 1)
    xs = np.clip(moved[:, 0], 0, w - 1)
    precision = 1.0 - float(map_coordinates(ink_blur, [ys, xs], order=1, mode="nearest").mean())
    if len(targets):
        d = cKDTree(moved).query(targets)[0]
        recall = float((1.0 - np.exp(-(d**2) / (2.0 * sigma**2))).mean())
    else:
        recall = 0.0
    dx, dy, lsx, lsy, rot, shear = theta
    prior = PRIOR_WEIGHT * (
        (dx / (PRIOR_SHIFT_UNITS * xh)) ** 2
        + (dy / (0.5 * PRIOR_SHIFT_UNITS * xh)) ** 2
        + (lsx / PRIOR_LOG_SCALE) ** 2
        + (lsy / PRIOR_LOG_SCALE) ** 2
        + (rot / PRIOR_ROTATION) ** 2
        + (shear / PRIOR_SHEAR) ** 2
    )
    return precision + recall + prior


def register_letters(case: WordCase, result: WordDeriveResult) -> dict[int, dict]:
    """Per slot: the affine that lays the composed body onto the ink, coarse to fine."""
    if case.mask is None:
        return {}
    mask = np.asarray(case.mask, dtype=bool)
    xh = float(result.xh_px)
    tx, ty = float(result.registration["tx"]), float(result.registration["ty"])
    baseline_row = float(result.baseline_row)
    ink_pts = np.argwhere(mask)[:, ::-1].astype(float)
    blurs = {}
    for sigma in SIGMAS_PX:
        b = gaussian_filter(mask.astype(float), sigma)
        blurs[sigma] = b / max(float(b.max()), 1e-9)
    out: dict[int, dict] = {}
    for i, slot in enumerate(case.slots):
        items = _body_items(result, i)
        if not items or not slot.key:
            continue
        pts = np.vstack([_to_px_composed(it["centerline"], xh, tx, ty, baseline_row) for it in items])
        entry = pts[0].copy()
        pad = WINDOW_PAD_UNITS * xh
        lo, hi = pts.min(axis=0) - pad, pts.max(axis=0) + pad
        targets = ink_pts[
            (ink_pts[:, 0] >= lo[0]) & (ink_pts[:, 0] <= hi[0]) & (ink_pts[:, 1] >= lo[1]) & (ink_pts[:, 1] <= hi[1])
        ]
        theta = np.zeros(6)
        cost0 = _cost(theta, pts, entry, blurs[SIGMAS_PX[-1]], targets, SIGMAS_PX[-1], xh)
        for sigma in SIGMAS_PX:
            res = minimize(
                _cost,
                theta,
                args=(pts, entry, blurs[sigma], targets, sigma, xh),
                method="Powell",
                options={"xtol": 1e-3, "ftol": 1e-5, "maxfev": 4000},
            )
            theta = res.x
        cost1 = _cost(theta, pts, entry, blurs[SIGMAS_PX[-1]], targets, SIGMAS_PX[-1], xh)
        a_px = _affine_matrix(theta)
        flip = np.diag([1.0, -1.0])  # pixel y runs down, composed y runs up
        a_units = flip @ a_px @ flip
        t_units = np.array([theta[0] / xh, -theta[1] / xh])
        out[i] = {
            "key": slot.key,
            "A": a_units,
            "t": t_units,
            "theta": theta,
            "cost_before": round(cost0, 4),
            "cost_after": round(cost1, 4),
            "shift_units": (float(theta[0]) / xh, float(-theta[1]) / xh),
            "window": (float(lo[0]), float(hi[0])),
        }
    return out
