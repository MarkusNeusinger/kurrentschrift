"""Word-level scoring: composed draw items vs a frozen specimen crop.

FROZEN together with the fixtures during an experiment loop (like
core/quality*.py for the glyph bench): an experiment edits the composer, never
the ruler. Design per docs/reference/qualitaetsmetrik.md §6:

- Registration is BOUNDED and reported: scale comes from the specimen's
  measured lineature (x-height in px), the translation from a small grid
  search (±0.6 x-heights horizontally, ±4 px vertically) that minimises the
  forward chamfer — wide enough to absorb measuring tolerance, far too narrow
  to hide a bad composition by sliding it around.
- Three penalties in [0, 1], lower better:
    transition — forward chamfer of the GENERATED connector samples to the
        specimen skeleton, plus the reverse chamfer of specimen skeleton
        pixels inside the connector x-spans to the full composed centerline
        raster. The headline signal: are the Übergänge where the real pen went?
    coverage — symmetric chamfer between ALL composed centerlines and the
        specimen skeleton (letters included). Moves with authoring quality
        too, so it gates rather than decides.
    width — |log| ratio of composed vs specimen ink width: rhythm/advance
        errors that per-point chamfer barely sees.
  loss = 0.45·transition + 0.35·coverage + 0.20·width
- A word whose composition is missing a template scores 1.0 (a hole is a
  failure, not a skipped case), mirroring the glyph bench's crash rule.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt


# Registration bounds (see module docstring).
TX_RANGE_UNITS = 0.6
TY_RANGE_PX = 4
# Chamfer normalisation: a mean deviation of 0.6 x-heights saturates the penalty.
CHAMFER_SAT_UNITS = 0.6
# Width penalty saturates at a 1.5× (or 1/1.5) total-width mismatch.
WIDTH_SAT_LOG = math.log(1.5)

W_TRANSITION = 0.45
W_COVERAGE = 0.35
W_WIDTH = 0.20


def _to_px(points: np.ndarray, xh: float, baseline_row: float) -> np.ndarray:
    """Composed-frame points (x right, y up, baseline 0) → crop pixel coords."""
    out = np.empty_like(points)
    out[:, 0] = points[:, 0] * xh
    out[:, 1] = baseline_row - points[:, 1] * xh
    return out


def _edt_lookup(edt: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Distance at (possibly out-of-crop) sample positions; leaving the crop
    adds the clamp distance so an escaped composition cannot score free."""
    h, w = edt.shape
    xs = pts[:, 0]
    ys = pts[:, 1]
    cx = np.clip(xs, 0, w - 1)
    cy = np.clip(ys, 0, h - 1)
    base = edt[cy.round().astype(int), cx.round().astype(int)]
    return base + np.hypot(xs - cx, ys - cy)


def _rasterize(polylines: list[np.ndarray], shape: tuple[int, int], stroke_px: int) -> np.ndarray:
    img = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(img)
    for line in polylines:
        if len(line) < 2:
            continue
        d.line([(float(x), float(y)) for x, y in line], fill=255, width=stroke_px, joint="curve")
    return np.asarray(img) > 0


def score_word(composed: dict, word_meta: dict, skel: np.ndarray, nib_units: float | None) -> dict:
    """Score one composed word against its frozen skeleton. Returns the report dict."""
    x0, y0, _x1, _y1 = word_meta["rect"]
    xh = float(word_meta["baseline_y"] - word_meta["midband_y"])
    baseline_row = float(word_meta["baseline_y"] - y0)

    items = composed["items"]
    if composed["missing"] or not items:
        return {"loss": 1.0, "failed": True, "missing": composed["missing"]}

    glyph_lines = [np.asarray(it["centerline"], dtype=float) for it in items if "rings" in it]
    connector_lines = [np.asarray(it["centerline"], dtype=float) for it in items if "rings" not in it]
    all_px = [_to_px(line, xh, baseline_row) for line in glyph_lines + connector_lines]
    conn_px = [_to_px(line, xh, baseline_row) for line in connector_lines]
    samples = np.vstack(all_px)

    ys, xs = np.nonzero(skel)
    if len(xs) == 0:
        return {"loss": 1.0, "failed": True, "missing": []}
    edt = distance_transform_edt(~skel)

    # --- bounded registration: initial tx aligns left ink edges, then grid-search
    tx0 = float(xs.min() - samples[:, 0].min())
    best = (math.inf, tx0, 0.0)
    tx_span = int(round(TX_RANGE_UNITS * xh))
    for tx in range(int(tx0) - tx_span, int(tx0) + tx_span + 1):
        for ty in range(-TY_RANGE_PX, TY_RANGE_PX + 1):
            d = float(_edt_lookup(edt, samples + np.array([tx, ty])).mean())
            if d < best[0]:
                best = (d, float(tx), float(ty))
    _, tx, ty = best
    shift = np.array([tx, ty])

    sat = CHAMFER_SAT_UNITS * xh

    # --- coverage: symmetric chamfer over everything
    fwd = float(_edt_lookup(edt, samples + shift).mean())
    stroke_px = max(2, int(round(2 * (nib_units or 0.07) * xh)))
    raster = _rasterize([p + shift for p in all_px], skel.shape, stroke_px)
    edt_composed = distance_transform_edt(~raster)
    rev = float(edt_composed[ys, xs].mean())
    coverage = min(1.0, 0.5 * (fwd + rev) / sat)

    # --- transition: connectors → skeleton, and specimen ink inside connector spans → composition
    if conn_px:
        conn_samples = np.vstack(conn_px) + shift
        t_fwd = float(_edt_lookup(edt, conn_samples).mean())
        spans = [(p[:, 0].min() + tx, p[:, 0].max() + tx) for p in conn_px]
        in_span = np.zeros(len(xs), dtype=bool)
        for a, b in spans:
            in_span |= (xs >= a) & (xs <= b)
        t_rev = float(edt_composed[ys[in_span], xs[in_span]].mean()) if in_span.any() else t_fwd
        transition = min(1.0, 0.5 * (t_fwd + t_rev) / sat)
    else:
        transition = coverage  # single-letter word: no connectors to judge

    # --- width: total-ink-width ratio (rhythm / advance errors)
    composed_w = (samples[:, 0].max() - samples[:, 0].min()) or 1.0
    specimen_w = float(xs.max() - xs.min()) or 1.0
    width = min(1.0, abs(math.log(composed_w / specimen_w)) / WIDTH_SAT_LOG)

    loss = W_TRANSITION * transition + W_COVERAGE * coverage + W_WIDTH * width
    return {
        "loss": float(loss),
        "failed": False,
        "transition": float(transition),
        "coverage": float(coverage),
        "width": float(width),
        "registration": {"tx": tx, "ty": ty, "xh_px": xh},
        "missing": [],
    }
