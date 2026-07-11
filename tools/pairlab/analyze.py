"""Independent-fit dissection of one letter join against the real specimens.

The word bench scores a join at the COMPOSED placement, so a bad connector and
a bad placement are entangled: when the composition packs two letters closer
than the plate does, even a perfectly shaped Übergang lands on the wrong ink.
This module removes that confound. For every real occurrence of a letter pair
in the Abb.-19 words / Abb.-20 pairs it

1. composes the word with the production composer (provenance on),
2. re-fits EVERY letter independently — a small bounded translation grid per
   glyph, minimising the mean skeleton distance of its own body strokes — so
   each letter sits where THIS specimen actually wrote it,
3. regenerates the connector between the two independently placed letters with
   the production connector maths (same constants and guards as
   ``core.compose``), and
4. dissects the join: the specimen's own connecting stroke (skeleton pixels in
   the inter-letter gap, ordered into a polyline), the tangents at both of its
   ends, and — the core question — the DEVIATION PROFILE along the first
   letter's tail and the second letter's head: how far INTO each glyph does
   the specimen depart from the template before the join begins?

A large ``tail_adapt``/``head_adapt`` means the real pen reshapes the letter's
own last/first piece for the join (the chart-cell coupling stub is replaced,
not extended) — evidence that generating only exit→entry cannot reach the
plate's form for that pair. Diagnostics only: nothing here feeds production
or the frozen bench metric.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.ndimage import distance_transform_edt

from core.compose import (
    BOW_EXIT_Y,
    BOW_LAUNCH_DEG,
    CONNECT_SAMPLES,
    DESCENDER_EXIT_Y,
    HIGH_EXIT_Y,
    JOIN_BAND_Y,
    _endpoint_tangent,
    _key_base,
    _sample_bezier,
    _unit,
)
from tools.wordlab.cases import WordCase, iter_fixture_word_cases
from tools.wordlab.derive import WordDeriveResult, derive_word


# Independent-fit bounds per letter (x-height units): wide enough to absorb the
# composition's spacing error (which accumulates along a long word), narrow
# enough that a letter rarely reaches its neighbour's column; a fit that ends
# ON the bound is flagged (``LetterFit.at_bound``) — treat its numbers with
# suspicion.
FIT_DX_UNITS = 0.6
FIT_DY_UNITS = 0.20
# Deviation above which the specimen is judged to have DEPARTED from the
# template shape (mean authoring noise along well-fit letters is ~0.05 xh).
ADAPT_THRESH_UNITS = 0.12
# The departure must stay below threshold this long (arc) to count as "back on
# the template" — a single sub-threshold sample inside the stub must not end
# the adaptation zone.
ADAPT_PERSIST_UNITS = 0.12
# How far into each letter the tail/head deviation profile is measured.
PROFILE_LEN_UNITS = 1.2
# Arc window for the specimen-side tangents of the real join (matches the
# composer's TANGENT_WINDOW spirit, in px it is scaled by xh).
REAL_TANGENT_UNITS = 0.18


Point = tuple[float, float]


@dataclass
class LetterFit:
    """One letter re-fit independently onto the specimen skeleton."""

    slot_index: int
    key: str
    base: str
    ddx_px: float  # shift ON TOP of the word-level registration (crop px)
    ddy_px: float
    at_bound: bool  # the optimum sits on the search boundary — fit is suspect
    resid_before: float  # mean skeleton distance of the body samples (xh units)
    resid_after: float
    body_px: list[np.ndarray]  # body strokes at the OPTIMAL placement (crop px)
    composed_px: list[np.ndarray]  # the same strokes at the composed placement


@dataclass
class JoinDissection:
    """Everything measured about ONE real occurrence of a letter pair."""

    case: WordCase
    result: WordDeriveResult
    slot_a: int  # slot index of the first letter (the pair is slots a, a+1)
    fits: dict[int, LetterFit]  # every letter of the word, keyed by slot index
    a: LetterFit
    b: LetterFit
    # --- generated connector between the two INDEPENDENTLY placed letters ---
    exit_px: Point  # A's template exit at optimal placement (crop px)
    entry_px: Point  # B's template entry at optimal placement
    exit_deg: float  # rendered tangents (composed units, y up)
    entry_deg: float
    gen_px: np.ndarray  # the regenerated connector polyline (crop px)
    gen_chamfer: float  # mean skeleton distance of its samples (xh units)
    # --- the specimen's own connecting stroke ---
    real_px: np.ndarray  # ordered skeleton polyline in the inter-letter gap (may be empty)
    real_exit_deg: float | None  # specimen tangent leaving A / entering B (units frame)
    real_entry_deg: float | None
    real_depart_y: float | None  # y (units) where the real stroke leaves A's ink column
    real_arrive_y: float | None  # y (units) where it reaches B's ink column
    # --- adaptation profiles: does the GLYPH's own end reshape for the join? ---
    tail_profile: np.ndarray  # (n, 2): arc from A's exit (units) → deviation (units)
    head_profile: np.ndarray  # (n, 2): arc from B's entry (units) → deviation (units)
    tail_adapt: float  # arc length of A's tail the specimen re-shapes (units)
    head_adapt: float


def pair_bases(arg: str) -> tuple[str, str]:
    """CLI pair spec → two glyph-key bases: ``re`` → (r, e); ``longs,t`` for
    multi-char bases (long s, umlauts: ``ue`` etc.)."""
    if "," in arg:
        a, _, b = arg.partition(",")
        if a and b:
            return (a, b)
    elif len(arg) == 2:
        return (arg[0], arg[1])
    raise SystemExit(f"pair {arg!r}: give two letters ('re') or two comma-separated bases ('longs,t')")


def find_occurrences(
    bases: tuple[str, str], *, sets: tuple[str, ...] = ("words", "pairs"), style: str = "suetterlin"
) -> list[tuple[WordCase, int]]:
    """All (case, slot_index) whose slots write ``bases`` as adjacent joined letters."""
    out: list[tuple[WordCase, int]] = []
    for which in sets:
        for case in iter_fixture_word_cases(which=which, style=style):
            if not case.scorable:
                continue
            for i in range(len(case.slots) - 1):
                s0, s1 = case.slots[i], case.slots[i + 1]
                if s0.space or s1.space or not s0.key or not s1.key or not (s0.joins and s1.joins):
                    continue
                if (_key_base(s0.key, s0.position), _key_base(s1.key, s1.position)) == bases:
                    out.append((case, i))
    return out


def _to_px(pts: list | np.ndarray, xh: float, tx: float, ty: float, baseline_row: float) -> np.ndarray:
    """Composed-frame points (x right, y up, baseline 0) → crop pixels (the
    metric's mapping, including the word-level registration shift)."""
    a = np.asarray(pts, dtype=float).reshape(-1, 2)
    out = np.empty_like(a)
    out[:, 0] = a[:, 0] * xh + tx
    out[:, 1] = baseline_row - a[:, 1] * xh + ty
    return out


def _edt_at(edt: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Distance at (possibly out-of-crop) positions; leaving the crop adds the
    clamp distance (same rule as the bench metric)."""
    h, w = edt.shape
    cx = np.clip(pts[:, 0], 0, w - 1)
    cy = np.clip(pts[:, 1], 0, h - 1)
    base = edt[cy.round().astype(int), cx.round().astype(int)]
    return base + np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)


def _body_items(result: WordDeriveResult, slot_index: int) -> list[dict]:
    """The slot's NON-diacritic glyph strokes, in writing order."""
    return [
        it
        for it in result.composed["items"]
        if "rings" in it and it.get("slot_index") == slot_index and not it.get("diacritic")
    ]


def _fit_letter(edt: np.ndarray, strokes_px: list[np.ndarray], xh: float) -> tuple[float, float, bool, float, float]:
    """Bounded integer grid search of one letter's translation. Returns
    (ddx, ddy, at_bound, resid_before, resid_after) — residuals in xh units."""
    samples = np.vstack(strokes_px)
    dx_span = int(round(FIT_DX_UNITS * xh))
    dy_span = int(round(FIT_DY_UNITS * xh))
    before = float(_edt_at(edt, samples).mean()) / xh
    best = (math.inf, 0, 0)
    for ddx in range(-dx_span, dx_span + 1):
        for ddy in range(-dy_span, dy_span + 1):
            d = float(_edt_at(edt, samples + np.array([ddx, ddy])).mean())
            if d < best[0]:
                best = (d, ddx, ddy)
    at_bound = abs(best[1]) == dx_span or abs(best[2]) == dy_span
    return float(best[1]), float(best[2]), at_bound, before, best[0] / xh


def _generate_connector(p0: Point, exit_deg: float, p3: Point, entry_deg: float) -> list[Point]:
    """The production connector between two endpoints — the exact maths of
    ``core.compose.compose_word``'s join block (same constants, same guards),
    lifted out so it can run between INDEPENDENTLY placed letters. Composed
    units in, composed units out."""
    span = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
    hspan = abs(p3[0] - p0[0])
    handle = max(0.05, min(span * 0.4, hspan * 0.5))
    d_out = _unit(exit_deg)
    backward = d_out[0] <= 0.0
    high_reversal = p0[1] > HIGH_EXIT_Y and p3[1] < p0[1]
    if ((p0[1] < DESCENDER_EXIT_Y and d_out[1] < 0) or backward or high_reversal) and span > 0:
        d_out = ((p3[0] - p0[0]) / span, (p3[1] - p0[1]) / span)
    elif BOW_EXIT_Y < p0[1] <= HIGH_EXIT_Y and p3[1] < p0[1]:
        launch = math.degrees(math.atan2(d_out[1], d_out[0]))
        clamped = min(max(launch, BOW_LAUNCH_DEG[0]), BOW_LAUNCH_DEG[1])
        if clamped != launch:
            d_out = _unit(clamped)
    d_in = _unit(entry_deg)
    p1 = (p0[0] + handle * d_out[0], p0[1] + handle * d_out[1])
    p2 = (p3[0] - handle * d_in[0], p3[1] - handle * d_in[1])
    return _sample_bezier(p0, p1, p2, p3, CONNECT_SAMPLES)


def _real_join(
    skel: np.ndarray, a_max_x: float, b_min_x: float, seed_y: float, baseline_row: float, xh: float
) -> np.ndarray:
    """The specimen's own connecting stroke: skeleton pixels between the two
    letters' ink columns inside the join band, tracked column by column into a
    polyline. Where a column holds several strokes (r's Deckstrich arm above
    the actual join), the tracker keeps the y closest to the previous column
    (seeded near A's exit height) instead of blurring them into a median.
    Empty array when the letters touch/overlap."""
    row_top = baseline_row - JOIN_BAND_Y[1] * xh
    row_bot = baseline_row - JOIN_BAND_Y[0] * xh
    ys, xs = np.nonzero(skel)
    sel = (xs > a_max_x) & (xs < b_min_x) & (ys >= row_top) & (ys <= row_bot)
    if not sel.any():
        return np.zeros((0, 2))
    xs, ys = xs[sel], ys[sel]
    prev_y = float(np.clip(seed_y, row_top, row_bot))
    pts: list[list[float]] = []
    for c in np.unique(xs):
        candidates = ys[xs == c].astype(float)
        y = float(candidates[np.argmin(np.abs(candidates - prev_y))])
        pts.append([float(c), y])
        prev_y = y
    return np.asarray(pts, dtype=float)


def _polyline_tangent_deg(pts: np.ndarray, xh: float, at_end: bool) -> float | None:
    """Tangent (degrees, y UP / units frame) at one end of a px polyline,
    measured over REAL_TANGENT_UNITS of horizontal run."""
    if len(pts) < 2:
        return None
    win = REAL_TANGENT_UNITS * xh
    if at_end:
        seg = pts[pts[:, 0] >= pts[-1, 0] - win]
        a, b = seg[0], seg[-1]
    else:
        seg = pts[pts[:, 0] <= pts[0, 0] + win]
        a, b = seg[0], seg[-1]
    if b[0] == a[0]:
        return None
    return math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))  # px y down → units y up


def _deviation_profile(edt: np.ndarray, stroke_px: np.ndarray, xh: float, from_end: bool) -> np.ndarray:
    """(arc from the join end, deviation) along one stroke, both in xh units,
    up to PROFILE_LEN_UNITS. ``from_end=True`` walks A's exit stroke backwards
    from its exit; ``False`` walks B's first stroke forwards from its entry."""
    pts = stroke_px[::-1] if from_end else stroke_px
    devs = _edt_at(edt, pts) / xh
    seg = np.hypot(*(np.diff(pts, axis=0).T)) / xh
    arcs = np.concatenate([[0.0], np.cumsum(seg)])
    keep = arcs <= PROFILE_LEN_UNITS
    return np.column_stack([arcs[keep], devs[keep]])


def _adaptation_length(profile: np.ndarray) -> float:
    """Arc length from the join over which the specimen deviates from the
    template: the first arc position where the deviation drops below
    ADAPT_THRESH_UNITS and STAYS below for ADAPT_PERSIST_UNITS."""
    if len(profile) == 0:
        return 0.0
    arcs, devs = profile[:, 0], profile[:, 1]
    below = devs <= ADAPT_THRESH_UNITS
    for i in range(len(arcs)):
        if not below[i]:
            continue
        j = np.searchsorted(arcs, arcs[i] + ADAPT_PERSIST_UNITS)
        if below[i : max(j, i + 1)].all():
            return float(arcs[i])
    return float(arcs[-1])


def _ink_extent_x(strokes_px: list[np.ndarray], baseline_row: float, xh: float) -> tuple[float, float]:
    """Horizontal extent of the letter's body samples inside the join band (px)."""
    row_top = baseline_row - JOIN_BAND_Y[1] * xh
    row_bot = baseline_row - JOIN_BAND_Y[0] * xh
    pts = np.vstack(strokes_px)
    band = pts[(pts[:, 1] >= row_top) & (pts[:, 1] <= row_bot)]
    if len(band) == 0:
        band = pts
    return float(band[:, 0].min()), float(band[:, 0].max())


def dissect_occurrence(case: WordCase, slot_a: int) -> JoinDissection | None:
    """Independent-fit dissection of the join between slots ``slot_a`` and
    ``slot_a + 1``. None when the composition is missing a template."""
    result = derive_word(case)
    if result.composed["missing"] or result.report is None or result.report.get("failed"):
        return None

    xh = result.xh_px
    tx, ty = result.registration["tx"], result.registration["ty"]
    baseline_row = result.baseline_row
    edt = distance_transform_edt(~case.skel)

    def to_px(pts) -> np.ndarray:
        return _to_px(pts, xh, tx, ty, baseline_row)

    # --- independent per-letter fits, every letter of the word ---
    fits: dict[int, LetterFit] = {}
    for i, slot in enumerate(case.slots):
        items = _body_items(result, i)
        if not items or not slot.key:
            continue
        strokes_px = [to_px(it["centerline"]) for it in items]
        ddx, ddy, at_bound, before, after = _fit_letter(edt, strokes_px, xh)
        fits[i] = LetterFit(
            slot_index=i,
            key=slot.key,
            base=_key_base(slot.key, slot.position),
            ddx_px=ddx,
            ddy_px=ddy,
            at_bound=at_bound,
            resid_before=before,
            resid_after=after,
            body_px=[s + np.array([ddx, ddy]) for s in strokes_px],
            composed_px=strokes_px,
        )
    if slot_a not in fits or slot_a + 1 not in fits:
        return None
    a, b = fits[slot_a], fits[slot_a + 1]

    # --- the two letters' join geometry at their independent placements ---
    a_items = _body_items(result, slot_a)
    b_items = _body_items(result, slot_a + 1)
    a_exit_line = a_items[-1]["centerline"]  # composed units, y up
    b_first_line = b_items[0]["centerline"]
    exit_deg = _endpoint_tangent([tuple(p) for p in a_exit_line], at_end=True)
    entry_deg = _endpoint_tangent([tuple(p) for p in b_first_line], at_end=False)

    # Independent shifts in composed units (px y down → units y up).
    a_shift = (a.ddx_px / xh, -a.ddy_px / xh)
    b_shift = (b.ddx_px / xh, -b.ddy_px / xh)
    p0 = (a_exit_line[-1][0] + a_shift[0], a_exit_line[-1][1] + a_shift[1])
    p3 = (b_first_line[0][0] + b_shift[0], b_first_line[0][1] + b_shift[1])
    gen_units = _generate_connector(p0, exit_deg, p3, entry_deg)
    gen_px = to_px(gen_units)
    gen_chamfer = float(_edt_at(edt, gen_px).mean()) / xh

    # --- the specimen's own connecting stroke between the ink columns ---
    _, a_max_x = _ink_extent_x(a.body_px, baseline_row, xh)
    b_min_x, _ = _ink_extent_x(b.body_px, baseline_row, xh)
    exit_row = to_px([p0])[0, 1]  # seed the tracker at A's exit height
    real_px = _real_join(case.skel, a_max_x, b_min_x, exit_row, baseline_row, xh)
    real_exit_deg = _polyline_tangent_deg(real_px, xh, at_end=False)
    real_entry_deg = _polyline_tangent_deg(real_px, xh, at_end=True)
    to_units_y = lambda row: (baseline_row - row) / xh  # noqa: E731
    real_depart_y = to_units_y(real_px[0, 1]) if len(real_px) else None
    real_arrive_y = to_units_y(real_px[-1, 1]) if len(real_px) else None

    # --- adaptation profiles along A's tail and B's head ---
    tail_profile = _deviation_profile(edt, a.body_px[-1], xh, from_end=True)
    head_profile = _deviation_profile(edt, b.body_px[0], xh, from_end=False)

    return JoinDissection(
        case=case,
        result=result,
        slot_a=slot_a,
        fits=fits,
        a=a,
        b=b,
        exit_px=tuple(to_px([p0])[0]),
        entry_px=tuple(to_px([p3])[0]),
        exit_deg=exit_deg,
        entry_deg=entry_deg,
        gen_px=gen_px,
        gen_chamfer=gen_chamfer,
        real_px=real_px,
        real_exit_deg=real_exit_deg,
        real_entry_deg=real_entry_deg,
        real_depart_y=real_depart_y,
        real_arrive_y=real_arrive_y,
        tail_profile=tail_profile,
        head_profile=head_profile,
        tail_adapt=_adaptation_length(tail_profile),
        head_adapt=_adaptation_length(head_profile),
    )


def summary_row(d: JoinDissection) -> dict:
    """Flat per-occurrence numbers for stdout / JSON aggregation."""
    xh = d.result.xh_px
    return {
        "id": d.case.id,
        "kind": d.case.kind,
        "pair": f"{d.a.base}→{d.b.base}",
        "slot": d.slot_a,
        "a_shift_units": [round(d.a.ddx_px / xh, 3), round(-d.a.ddy_px / xh, 3)],
        "b_shift_units": [round(d.b.ddx_px / xh, 3), round(-d.b.ddy_px / xh, 3)],
        "at_bound": d.a.at_bound or d.b.at_bound,
        "a_resid": round(d.a.resid_after, 3),
        "b_resid": round(d.b.resid_after, 3),
        "gen_chamfer": round(d.gen_chamfer, 3),
        "tail_adapt": round(d.tail_adapt, 3),
        "head_adapt": round(d.head_adapt, 3),
        "exit_deg": round(d.exit_deg, 1),
        "real_exit_deg": None if d.real_exit_deg is None else round(d.real_exit_deg, 1),
        "entry_deg": round(d.entry_deg, 1),
        "real_entry_deg": None if d.real_entry_deg is None else round(d.real_entry_deg, 1),
        "real_depart_y": None if d.real_depart_y is None else round(d.real_depart_y, 3),
        "real_arrive_y": None if d.real_arrive_y is None else round(d.real_arrive_y, 3),
    }
