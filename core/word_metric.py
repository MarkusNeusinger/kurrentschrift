"""Word-level scoring: composed draw items vs a frozen specimen crop.

Lives in core (moved from tools/wordbench/metric.py, which re-exports it
unchanged) so the admin score endpoint can serve the SAME ruler the bench
runs — one implementation, no drift. Also carries the specimen reference
builder (binarise → clear excludes → despeckle → skeleton) shared by the
wordbench exporter and the API.

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
- `score_word_segments` adds per-connector/per-glyph attribution rows (for
  tools/wordlab) on the same registration and saturation scale — diagnostics
  only, never part of the headline.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt
from scipy.ndimage import label as cc_label


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


# ---------------------------------------------------------- specimen reference
# Moved from tools/wordbench/export_fixtures.py so the API scores against the
# exact same reference the bench freezes.

# Paper grain survives the adaptive binarisation as scattered 1–10 px specks;
# their skeletons would put a noise floor under the reverse chamfer. Real marks
# stay: the smallest genuine ink component (an i-dot) is ~50 px² at this scale.
DESPECKLE_MIN_AREA_PX = 24

# A connected component whose pixels lie at least this fraction inside the
# entry's exclude rects is foreign ink and removed WHOLE (tails included).
# Binarising the unpainted crop avoids the painted-border fake-ink line the
# jul05 export suffered (see the wordbench exporter history).
EXCLUDE_COMPONENT_FRAC = 0.5


def clear_excluded(mask: np.ndarray, rects: list[tuple[int, int, int, int]]) -> np.ndarray:
    """Remove foreign ink under crop-local exclude rects from a binarised mask.

    Two layers: every pixel strictly inside a rect is cleared, and every
    connected component with ≥ EXCLUDE_COMPONENT_FRAC of its area inside the
    rect union is removed whole — so a descender tail poking out of its rect
    does not survive as an ink stub (its skeleton would poison the reverse
    chamfer). Word ink is safe: it never lies half inside an exclude.
    """
    if not rects:
        return mask
    inside = np.zeros_like(mask)
    for x0, y0, x1, y1 in rects:
        inside[max(0, y0) : max(0, y1), max(0, x0) : max(0, x1)] = True
    labels, n = cc_label(mask)
    if n:
        sizes = np.bincount(labels.ravel(), minlength=n + 1)
        inside_sizes = np.bincount(labels[inside].ravel(), minlength=n + 1)
        kill = inside_sizes >= EXCLUDE_COMPONENT_FRAC * sizes
        kill[0] = False
        mask = mask & ~kill[labels]
    return mask & ~inside


def despeckle(mask: np.ndarray) -> np.ndarray:
    labels, n = cc_label(mask)
    if not n:
        return mask
    sizes = np.bincount(labels.ravel())
    keep = sizes >= DESPECKLE_MIN_AREA_PX
    keep[0] = False
    return keep[labels]


def specimen_reference(page: np.ndarray, sample: dict) -> tuple[np.ndarray, np.ndarray]:
    """The (mask, skeleton) scoring reference for one words.json sample.

    Exactly the exporter pipeline: crop the raw plate, binarise the UNPAINTED
    crop, clear the exclude rects component-wise, despeckle, skeletonise.
    `sample` is a `core.chart.load_word_samples` entry (page-pixel coords).
    """
    from core.extract import binarize_adaptive, skeleton_and_width

    crop = page[sample["y0"] : sample["y1"], sample["x0"] : sample["x1"]].copy()
    x0, y0 = sample["x0"], sample["y0"]
    rects = [(int(ex[0]) - x0, int(ex[1]) - y0, int(ex[2]) - x0, int(ex[3]) - y0) for ex in sample.get("exclude") or []]
    mask = despeckle(clear_excluded(binarize_adaptive(crop), rects))
    skel, _width_map = skeleton_and_width(mask)
    return mask, skel


@lru_cache(maxsize=256)
def _skeleton_cached(page_path: str, sample_blob: tuple) -> np.ndarray:
    from core.chart import load_chart_grayscale

    sample = dict(sample_blob)
    sample["exclude"] = [list(e) for e in sample.get("exclude") or ()]
    page = load_chart_grayscale(page_path)
    _mask, skel = specimen_reference(page, sample)
    skel.setflags(write=False)
    return skel


def skeleton_for_sample(chart_path: str, sample: dict) -> np.ndarray:
    """Cached scoring skeleton for a sample — the plates are immutable per
    deploy, so the expensive binarise+skeletonise runs once per sample."""
    from core.chart import resolve_chart_path

    page_path = str(resolve_chart_path(chart_path).parent / str(sample["page"]))
    blob = (
        ("x0", int(sample["x0"])),
        ("y0", int(sample["y0"])),
        ("x1", int(sample["x1"])),
        ("y1", int(sample["y1"])),
        ("page", str(sample["page"])),
        ("exclude", tuple(tuple(int(v) for v in e[:4]) for e in sample.get("exclude") or [])),
    )
    return _skeleton_cached(page_path, blob)


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


def score_word_segments(
    composed: dict, word_meta: dict, skel: np.ndarray, nib_units: float | None, registration: dict
) -> list[dict]:
    """Per-segment attribution of a scored word, in writing order. ADDITIVE
    diagnostics — `score_word` and the headline number are untouched, and this
    function is frozen together with it during an experiment loop.

    Reuses the registration `score_word` already reports (its ``registration``
    dict) — the segments explain THE SAME fit, never a second chance to slide
    the word. One row per segment, on the headline's ingredients and
    saturation scale (CHAMFER_SAT_UNITS·xh):

    - connector (one row each): forward chamfer of ITS samples to the specimen
      skeleton + reverse chamfer of the specimen skeleton inside ITS x-span to
      the full composed raster → ``transition``. The headline pools these over
      all connectors; a row says how much THIS join contributed.
    - glyph (body strokes + its deferred diacritics, grouped): the same two
      chamfers over the glyph's own samples/x-span → ``coverage``.

    ``penalty`` mirrors the row's headline component so a caller can rank
    segments uniformly. Labels (``glyph_key``, ``pair``, slot indices) come
    from compose provenance (``compose_word(..., provenance=True)``); without
    it they are None and strokes cannot be grouped per glyph.
    """
    items = composed["items"]
    if composed["missing"] or not items:
        return []
    ys, xs = np.nonzero(skel)
    if len(xs) == 0:
        return []

    xh = float(registration["xh_px"])
    shift = np.array([float(registration["tx"]), float(registration["ty"])])
    baseline_row = float(word_meta["baseline_y"] - word_meta["rect"][1])
    sat = CHAMFER_SAT_UNITS * xh

    edt = distance_transform_edt(~skel)
    all_px = [_to_px(np.asarray(it["centerline"], dtype=float), xh, baseline_row) for it in items]
    stroke_px = max(2, int(round(2 * (nib_units or 0.07) * xh)))
    raster = _rasterize([p + shift for p in all_px], skel.shape, stroke_px)
    edt_composed = distance_transform_edt(~raster)

    # Segments in writing order: each connector is its own segment; glyph
    # strokes (incl. the diacritics deferred to the word end) group by their
    # provenance slot_index, anchored where the glyph body first appears.
    segments: list[dict] = []
    by_slot: dict[int, dict] = {}
    for it, px in zip(items, all_px, strict=True):
        if "rings" not in it:  # connector (same predicate as score_word)
            segments.append(
                {
                    "kind": "connector",
                    "pair": it.get("pair"),
                    "from_slot": it.get("from_slot"),
                    "to_slot": it.get("to_slot"),
                    "samples": [px],
                }
            )
            continue
        slot = it.get("slot_index")
        seg = by_slot.get(slot) if slot is not None else None
        if seg is None:
            seg = {"kind": "glyph", "glyph_key": it.get("glyph_key"), "slot_index": slot, "samples": []}
            segments.append(seg)
            if slot is not None:
                by_slot[slot] = seg
        seg["samples"].append(px)

    rows: list[dict] = []
    for seg in segments:
        samples = np.vstack(seg.pop("samples"))
        fwd = float(_edt_lookup(edt, samples + shift).mean())
        lo = float(samples[:, 0].min() + shift[0])
        hi = float(samples[:, 0].max() + shift[0])
        in_span = (xs >= lo) & (xs <= hi)
        rev = float(edt_composed[ys[in_span], xs[in_span]].mean()) if in_span.any() else fwd
        penalty = min(1.0, 0.5 * (fwd + rev) / sat)
        row = dict(seg)
        row["transition" if seg["kind"] == "connector" else "coverage"] = penalty
        row.update({"penalty": penalty, "fwd_px": fwd, "rev_px": rev, "x_span_px": [lo, hi]})
        rows.append(row)
    return rows
