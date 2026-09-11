"""`tools.pairlab.tintenpfad` — the strand decode, pinned on synthetic ink.

Everything here runs on plain numpy arrays: an X drawn as two diagonals, a
ring, a straight rail with a seed that rides, retraces or wanders into the
paper. No fixture root, no DB, no solve — except the one substrate test at
the end, which skips unless the frozen words root of digest `ccb036a5eb20`
is present, and then pins the strand set every path of the method rests on.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt
from skimage.morphology import skeletonize

from core.extract import binarize_adaptive
from tools.pairlab.tintenpfad import (
    LEGACY_P5,
    SUBPIXEL_MAX_PX,
    EdtField,
    Seed,
    TintenpfadWeights,
    assemble,
    decode,
    decode_with_hysteresis,
    fine_edt,
    hermite_bridge,
    read_tips,
    reentries,
    refine_strands,
    resample_run,
    spans_of,
    strands_of,
    subpixel_rail,
    tentfit_rail,
    tintenpfad_payload,
    tip_tail,
    weights_from_overrides,
)
from tools.tracebench.candidates import wire_violation


XH = 32.0


def _seed_along(points: np.ndarray, step: float = 1.0, stroke: int = 0, slot: int = 0) -> Seed:
    """A seed resampled along a polyline at `step` px, one stroke, one slot."""
    pts = np.asarray(points, dtype=float)
    arc = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    n = max(2, int(arc[-1] / step) + 1)
    s = np.linspace(0.0, arc[-1], n)
    xy = np.column_stack([np.interp(s, arc, pts[:, 0]), np.interp(s, arc, pts[:, 1])])
    tan = np.gradient(xy, axis=0)
    nrm = np.linalg.norm(tan, axis=1)
    tan = tan / np.where(nrm > 0, nrm, 1.0)[:, None]
    return Seed(xy=xy, tan=tan, slot=np.full(n, slot), stroke=np.full(n, stroke))


def _x_skeleton(size: int = 41) -> np.ndarray:
    skel = np.zeros((size, size), dtype=bool)
    for i in range(size):
        skel[i, i] = True
        skel[i, size - 1 - i] = True
    return skel


def _ring_skeleton(radius: float = 14.0, size: int = 41) -> np.ndarray:
    skel = np.zeros((size, size), dtype=bool)
    c = size // 2
    for t in np.linspace(0.0, 2 * np.pi, 400, endpoint=False):
        skel[int(round(c + radius * np.sin(t))), int(round(c + radius * np.cos(t)))] = True
    return skeletonize(skel)


def _rail_skeleton(length: int = 80, y: int = 20, width: int = 41) -> np.ndarray:
    skel = np.zeros((width, length), dtype=bool)
    skel[y, 4 : length - 4] = True
    return skel


# ----------------------------------------------------------------- stage 1


def test_an_x_crossing_pairs_into_two_straight_strands() -> None:
    """Both diagonals go straight through the crossing — two strands, four ends kept."""
    diag: dict = {}
    strands = strands_of(_x_skeleton(), XH, TintenpfadWeights(rail="raw"), diag)
    assert len(strands) == 2
    assert diag["spurs_pruned"] == 0 and diag["junctions_too_dense"] == 0
    for s in strands:
        span = s.points.max(axis=0) - s.points.min(axis=0)
        assert span.min() >= 38  # each strand runs corner to corner, not corner to centre
    # the two strands are the two diagonals: their end-to-end directions are perpendicular
    d = [s.points[-1] - s.points[0] for s in strands]
    d = [v / np.linalg.norm(v) for v in d]
    assert abs(float(d[0] @ d[1])) < 0.1


def test_a_ring_is_one_closed_strand() -> None:
    diag: dict = {}
    strands = strands_of(_ring_skeleton(), XH, TintenpfadWeights(rail="raw"), diag)
    assert len(strands) == 1 and strands[0].closed
    assert diag["closed_strands"] == 1


def test_the_subpixel_rail_moves_a_staircase_onto_the_stroke_axis() -> None:
    """A 22.5° stroke thins to a staircase; the tent fit on the EDT along the
    normal puts every pixel back on the axis within a fraction of a pixel."""
    mask = np.zeros((60, 120), dtype=bool)
    x0, y0, angle = 10.0, 15.0, np.radians(22.5)
    direction = np.array([np.cos(angle), np.sin(angle)])
    normal = np.array([-direction[1], direction[0]])
    yy, xx = np.mgrid[0:60, 0:120]
    rel = np.stack([xx - x0, yy - y0], axis=-1)
    along = rel @ direction
    across = rel @ normal
    mask[(along >= 0) & (along <= 95) & (np.abs(across) <= 2.5)] = True
    skel = skeletonize(mask)
    weights = TintenpfadWeights(rail="subpixel")
    strands = strands_of(skel, XH, weights, {})
    assert len(strands) == 1
    raw = strands[0].points.copy()
    refine_strands(strands, mask, weights)
    refined = strands[0].points
    inner = slice(8, -8)  # away from the stroke ends, where the tent is clean
    off_raw = np.abs((raw[inner] - [x0, y0]) @ normal)
    off_ref = np.abs((refined[inner] - [x0, y0]) @ normal)
    assert off_ref.mean() < off_raw.mean()
    assert off_ref.max() < 0.35
    assert np.abs(refined - raw).max() <= 0.75 + 1e-9


def _slanted_stroke(angle_deg: float = 22.5, length: float = 95.0, half_width: float = 2.5):
    """A capsule — a pen stroke with ROUNDED ends, so its medial axis ends on the
    axis (a flat-cut end forks toward its two corners)."""
    mask = np.zeros((60, 120), dtype=bool)
    x0, y0, angle = 10.0, 15.0, np.radians(angle_deg)
    direction = np.array([np.cos(angle), np.sin(angle)])
    normal = np.array([-direction[1], direction[0]])
    yy, xx = np.mgrid[0:60, 0:120]
    rel = np.stack([xx - x0, yy - y0], axis=-1)
    along = np.clip(rel @ direction, 0.0, length)
    foot = np.stack([x0 + along * direction[0], y0 + along * direction[1]], axis=-1)
    mask[np.hypot(xx - foot[..., 0], yy - foot[..., 1]) <= half_width] = True
    return mask, np.array([x0, y0]), direction, normal


def test_the_tip_reading_lays_the_unvisited_rail_and_walks_to_the_end_of_the_mask() -> None:
    """A run that stops five pixels short of the strand's free end is completed
    along the strand, then read on along the EDT ridge until the ink ends —
    every added vertex on ink, the last one within a pixel of the mask's tip."""
    mask, origin, direction, normal = _slanted_stroke()
    weights = TintenpfadWeights(rail="subpixel", tip_read=True)
    strands = strands_of(skeletonize(mask), XH, weights, {})
    assert len(strands) == 1 and strands[0].free_ends == (True, True)
    refine_strands(strands, mask, weights)
    n = len(strands[0].points)
    stop = n - 6
    runs = [strands[0].points[: stop + 1].copy()]
    labels = [np.zeros(stop + 1, dtype=int)]
    kinds = [np.zeros(stop + 1, dtype=int)]
    samples = [np.arange(stop + 1)]
    states = [(0, 0, 1), (0, stop, 1)]
    diag = read_tips(runs, labels, kinds, samples, strands, states, mask, cap_px=XH)
    assert diag["ends_read"] == 2 and diag["blocked"] == {"not_free": 0, "junction": 0, "visited": 0, "ambiguous": 0}
    assert diag["rail_points"] == 5 and diag["rail_points_in_mask"] == 5
    assert diag["walk_points"] > 0 and diag["walk_points_in_mask"] == diag["walk_points"]
    assert diag["stops"] == {"mask": 2, "rise": 0, "cap": 0, "edge": 0}
    along = (runs[0] - origin) @ direction
    across = (runs[0] - origin) @ normal
    # The skeleton stopped ~half a width short of both tips (the caps reach
    # along = -2.5 and 97.5); the reading gets within a pixel of each tip, on the axis.
    assert along.max() > 97.5 - 1.0 and along.min() < -2.5 + 1.0
    assert np.abs(across[kinds[0] == 2]).max() < 1.0
    assert (kinds[0] == 2).sum() == diag["rail_points"] + diag["walk_points"]
    assert len(labels[0]) == len(runs[0]) == len(samples[0])


def test_a_junction_end_and_a_visited_tail_are_never_read() -> None:
    """A T: the stem's end at the bar is a junction end, not a tip; and a tail
    another run already laid is not laid twice."""
    skel = np.zeros((50, 80), dtype=bool)
    skel[20, 5:76] = True
    skel[20:41, 40] = True
    strands = strands_of(skel, XH, TintenpfadWeights(rail="raw"), {})
    assert len(strands) == 2
    stem = next(s for s in strands if len(s.points) < 30)
    bar = next(s for s in strands if len(s.points) >= 30)
    assert bar.free_ends == (True, True)
    assert sorted(stem.free_ends) == [False, True]
    junction_end = 0 if stem.free_ends[1] else 1
    i = len(stem.points) // 2
    toward_junction = stem.points[-1 if junction_end == 1 else 0] - stem.points[i]
    rng, _, why = tip_tail(stem, i, toward_junction / np.linalg.norm(toward_junction), (i, i))
    assert why == "not_free" and rng == []
    toward_tip = -toward_junction
    rng, outward, why = tip_tail(stem, i, toward_tip / np.linalg.norm(toward_tip), (i, i))
    assert why == "" and len(rng) == len(stem.points) - 1 - i
    assert float(outward @ toward_tip) > 0.0
    # The same tail with a state beyond `i` on it: already laid by another run.
    _, _, why = tip_tail(stem, i, toward_tip / np.linalg.norm(toward_tip), (0, len(stem.points) - 1))
    assert why == "visited"


def test_spurs_at_a_strand_end_stay_with_the_switch_and_lateral_spurs_still_go() -> None:
    """Two short prongs at the end of a rail (the thinning's fork at a stroke
    tip) are pruned by default and kept with `spur_at_ends`; a short spur off
    the SIDE of a rail is a thinning artefact and is pruned either way."""
    fork = np.zeros((40, 40), dtype=bool)
    fork[5:31, 20] = True
    for k in (1, 2, 3):
        fork[30 + k, 20 - k] = True
        fork[30 + k, 20 + k] = True
    diag_off: dict = {}
    off = strands_of(fork, XH, TintenpfadWeights(rail="raw"), diag_off)
    assert diag_off["spurs_pruned"] == 2 and "spurs_kept_at_ends" not in diag_off  # the OFF artefact is untouched
    assert len(off) == 1 and off[0].points[:, 1].max() == 30
    diag_on: dict = {}
    on = strands_of(fork, XH, TintenpfadWeights(rail="raw", spur_at_ends=True), diag_on)
    assert diag_on["spurs_pruned"] == 0 and diag_on["spurs_kept_at_ends"] == 2
    # The rail pairs straight through into one prong; the other prong is its own
    # short strand whose junction end is NOT free — only its tip is.
    on.sort(key=lambda s: -len(s.points))
    assert len(on) == 2 and on[0].points[:, 1].max() == 33 and on[1].points[:, 1].max() == 33
    assert on[0].free_ends == (True, True) and sorted(on[1].free_ends) == [False, True]
    lateral = np.zeros((40, 40), dtype=bool)
    lateral[5:36, 20] = True
    for k in (1, 2, 3):
        lateral[20 + k, 20 + k] = True
    diag_lat: dict = {}
    strands_of(lateral, XH, TintenpfadWeights(rail="raw", spur_at_ends=True), diag_lat)
    assert diag_lat["spurs_pruned"] == 1 and diag_lat["spurs_kept_at_ends"] == 0


def _antialiased_stroke(angle_deg: float, half_w: float, size: tuple[int, int] = (80, 160), supersample: int = 8):
    """A grey crop in [0, 1] (0 = ink) of one straight stroke with coverage
    anti-aliasing — the sub-pixel edge information a scan carries — plus the
    stroke's axis origin and unit normal."""
    h, w = size
    angle = np.radians(angle_deg)
    direction = np.array([np.cos(angle), np.sin(angle)])
    normal = np.array([-direction[1], direction[0]])
    origin = np.array([12.0, 20.0])
    yy, xx = np.mgrid[0 : h * supersample, 0 : w * supersample]
    x = (xx + 0.5) / supersample - 0.5 - origin[0]
    y = (yy + 0.5) / supersample - 0.5 - origin[1]
    along = x * direction[0] + y * direction[1]
    across = x * normal[0] + y * normal[1]
    inside = (along >= 0) & (along <= 130) & (np.abs(across) <= half_w)
    coverage = inside.reshape(h, supersample, w, supersample).mean(axis=(1, 3))
    return 1.0 - coverage, origin, normal


def test_the_tent_fit_on_the_fine_edt_reads_the_axis_closer_than_the_three_point_tent() -> None:
    """A 22.5° stroke of half-width 1.5 px: the binary boundary is a staircase
    and the ridge of its distance transform inherits it; the same distance
    transform on the grey's finer raster, read by the ±2 px tent fit, puts the
    strand closer to the true axis — and never moves a pixel past the cap."""
    gray, origin, normal = _antialiased_stroke(22.5, 1.5)
    mask = binarize_adaptive(gray)
    strands = strands_of(skeletonize(mask), XH, TintenpfadWeights(rail="raw"), {})
    assert len(strands) == 1
    raw = strands[0].points.copy()
    tan = strands[0].tan
    coarse = subpixel_rail(raw, tan, distance_transform_edt(mask))
    field, agreement = fine_edt(mask, gray, 4)
    assert isinstance(field, EdtField) and field.up == 4 and field.shape == mask.shape
    assert agreement > 0.9  # the fine boundary is the mask's own edge, read finer
    fit = tentfit_rail(raw, tan, field, 2.0, 0.5)
    inner = slice(10, -10)
    off_coarse = np.abs((coarse[inner] - origin) @ normal)
    off_fit = np.abs((fit[inner] - origin) @ normal)
    assert off_fit.mean() < 0.75 * off_coarse.mean()
    assert np.abs(fit - raw).max() <= SUBPIXEL_MAX_PX + 1e-9
    # the field reads CROP-pixel distances (not fine ones): the adaptive mask's
    # edge sits ~1.5–2 px from the axis, a fine-pixel reading would say ~8
    assert 1.2 < float(np.median(field.read(fit[inner]))) < 2.4


def test_the_tent_fit_on_the_binary_edt_is_a_tent_apex_not_a_parabola() -> None:
    """On an exact continuous tent the least-squares tent recovers the apex
    offset itself (a parabola would read 70 % of it)."""
    edt = np.zeros((41, 41))
    delta = 0.3
    yy = np.arange(41, dtype=float)
    edt[:] = np.maximum(0.0, 4.0 - np.abs(yy - (20.0 + delta)))[:, None]
    pts = np.column_stack([np.arange(5.0, 36.0), np.full(31, 20.0)])
    tan = np.tile([1.0, 0.0], (31, 1))
    fit = tentfit_rail(pts, tan, edt, 2.0, 0.5)
    assert np.allclose(fit[:, 1], 20.0 + delta, atol=0.03)
    assert np.allclose(fit[:, 0], pts[:, 0])  # moved along the normal only


def test_the_default_rail_ignores_the_fit_fields() -> None:
    """`refine_strands` at the delivered default is the three-point tent on the
    binary EDT, whatever the fit fields say — the byte-identity of the default."""
    gray, _origin, _normal = _antialiased_stroke(30.0, 2.0)
    mask = binarize_adaptive(gray)
    weights = TintenpfadWeights(fit_half_px=3.0, fit_step_px=0.25)
    strands = strands_of(skeletonize(mask), XH, weights, {})
    expected = subpixel_rail(strands[0].points, strands[0].tan, distance_transform_edt(mask))
    diag = refine_strands(strands, mask, weights, crop=gray)
    assert diag == {}
    assert np.array_equal(strands[0].points, expected)
    fine_weights = TintenpfadWeights(rail="tentfit", edt_upsample=4)
    strands = strands_of(skeletonize(mask), XH, fine_weights, {})
    diag = refine_strands(strands, mask, fine_weights, crop=gray)
    assert diag["edt_upsample"] == 4 and 0.0 <= diag["fine_mask_band_agreement"] <= 1.0


# ----------------------------------------------------------------- stage 2


def _decode_on(skel: np.ndarray, seed: Seed, weights: TintenpfadWeights):
    strands = strands_of(skel, XH, weights, {})
    states, cost, ddiag = decode_with_hysteresis(strands, seed, XH, weights)
    runs, labels, kinds, samples, counts = assemble(strands, states, seed, XH, weights)
    return strands, states, runs, counts, ddiag


def test_a_seed_around_a_ring_rides_across_the_cut_without_a_hairpin() -> None:
    """The graph cut the ring at one pixel; a seed that goes once round,
    crossing the cut, decodes as ONE monotone ride, not a hairpin."""
    skel = _ring_skeleton()
    c, r = 20.0, 14.0
    t = np.linspace(0.6, 0.6 + 2 * np.pi * 0.97, 300)  # starts away from the leftmost pixel, passes it
    seed = _seed_along(np.column_stack([c + r * np.cos(t), c + r * np.sin(t)]))
    weights = TintenpfadWeights(rail="raw", resample_step_xh=0.0)
    strands, states, runs, counts, _ = _decode_on(skel, seed, weights)
    assert strands[0].closed
    assert all(s is not None and s[0] == 0 for s in states)
    assert counts["hairpins"] == 0 and counts["jumps"] == 0 and counts["paper_lifts"] == 0
    assert len(runs) == 1
    length = float(np.hypot(*np.diff(runs[0], axis=0).T).sum())
    assert abs(length - 2 * np.pi * r * 0.97) < 0.12 * 2 * np.pi * r


def test_a_seed_retrace_over_one_rail_is_a_single_priced_hairpin() -> None:
    skel = _rail_skeleton()
    seed = _seed_along(np.array([[8.0, 20.0], [70.0, 20.0], [8.0, 20.0]]))
    weights = TintenpfadWeights(rail="raw", resample_step_xh=0.0)
    _, states, runs, counts, _ = _decode_on(skel, seed, weights)
    assert counts["hairpins"] == 1 and counts["jumps"] == 0
    assert len(runs) == 1
    length = float(np.hypot(*np.diff(runs[0], axis=0).T).sum())
    assert abs(length - 124.0) < 6.0
    # the turn happens at the far end, and the ride is monotone on either side
    dirs = [s[2] for s in states if s is not None]
    flips = int((np.diff(dirs) != 0).sum())
    assert flips == 1


def test_a_bulge_within_reach_stays_on_the_rail_and_never_re_lays_a_pixel() -> None:
    """A seed that bulges 12 px off the rail (inside the board radius): the
    decode dwells on the rail through the bulge — no paper state, one run,
    no hairpin — and the ride is monotone, so no pixel is laid twice."""
    skel = _rail_skeleton()
    bump = np.array([[8.0, 20.0], [30.0, 20.0], [36.0, 8.0], [44.0, 8.0], [50.0, 20.0], [72.0, 20.0]])
    seed = _seed_along(bump)
    _, states, runs, counts, _ = _decode_on(skel, seed, TintenpfadWeights(rail="raw", resample_step_xh=0.0))
    assert sum(1 for s in states if s is None) == 0
    assert len(runs) == 1 and counts["hairpins"] == 0 and counts["paper_lifts"] == 0
    idx = [s[1] for s in states]
    assert all(b >= a for a, b in zip(idx[:-1], idx[1:], strict=True))


def _boardings(states) -> int:
    """Rail→paper and paper→rail transitions of a state sequence (one stroke)."""
    return sum(1 for a, b in zip(states[:-1], states[1:], strict=True) if (a is None) != (b is None))


def test_the_paper_wormhole_is_closed_by_the_boarding_price() -> None:
    """A seed that leaves the rail beyond every strand's reach is forced into
    the paper; each boarding into or out of it is priced as a lift-class
    event — the `das` mechanism (p2 → p4: a free paper state let the decode
    teleport along a strand; dtw 0.0986 → 0.0336 once it was priced)."""
    skel = _rail_skeleton(length=120)
    tall = np.array([[8.0, 20.0], [40.0, 20.0], [44.0, -12.0], [56.0, -12.0], [60.0, 20.0], [110.0, 20.0]])
    seed = _seed_along(tall)
    closed = TintenpfadWeights(rail="raw", resample_step_xh=0.0)
    open_ = weights_from_overrides(closed, ["paper_board=0"])
    strands = strands_of(skel, XH, closed, {})
    states_c, cost_c, _ = decode(strands, seed, XH, closed)
    states_o, cost_o, _ = decode(strands, seed, XH, open_)
    assert sum(1 for s in states_c if s is None) > 0 and sum(1 for s in states_o if s is None) > 0
    n_board = _boardings(states_c)
    assert n_board == 2
    if states_c == states_o:
        assert cost_c - cost_o == pytest.approx(closed.paper_board * n_board)
    else:
        assert cost_c > cost_o
    # and the ride resumes AHEAD of where it left, monotone — never a re-laid rail
    idx = [s[1] for s in states_c if s is not None]
    assert all(b >= a for a, b in zip(idx[:-1], idx[1:], strict=True))


def test_back_tol_zero_never_re_lays_a_pixel() -> None:
    skel = _rail_skeleton()
    wobble = np.column_stack([np.linspace(8.0, 72.0, 200), 20.0 + 2.0 * np.sin(np.linspace(0, 12 * np.pi, 200))])
    seed = _seed_along(wobble)
    _, states, runs, counts, _ = _decode_on(skel, seed, TintenpfadWeights(rail="raw", resample_step_xh=0.0))
    assert counts["hairpins"] == 0
    idx = [s[1] for s in states if s is not None]
    assert all(b >= a for a, b in zip(idx[:-1], idx[1:], strict=True))


def _two_rails() -> np.ndarray:
    skel = np.zeros((41, 80), dtype=bool)
    skel[20, 4:76] = True
    skel[14, 4:76] = True
    return skel


def test_reentries_finds_an_out_and_back_jump_but_not_a_detour() -> None:
    """Leave strand 0 at pixel 30, ride strand 1 for three samples, re-board
    strand 0 two pixels on: an out-and-back. Re-board it twenty pixels on:
    a detour the gap grew across, not an excursion."""
    weights = TintenpfadWeights(rail="raw")
    strands = strands_of(_two_rails(), XH, weights, {})
    lower = next(i for i, s in enumerate(strands) if s.points[0, 1] == 20.0)
    upper = 1 - lower
    seed = _seed_along(np.array([[8.0, 20.0], [72.0, 20.0]]))
    ride = [(lower, i, 1) for i in range(20, 31)]
    away = [(upper, i, 1) for i in (30, 31, 32)]
    back_close = [(lower, i, 1) for i in range(32, 45)]
    back_far = [(lower, i, 1) for i in range(50, 63)]
    n_close = len(ride) + len(away) + len(back_close)
    seed_close = Seed(seed.xy[:n_close], seed.tan[:n_close], seed.slot[:n_close], seed.stroke[:n_close])
    found = reentries(ride + away + back_close, strands, seed_close, XH, weights)
    assert found == [(len(ride), len(ride) + len(away))]
    n_far = len(ride) + len(away) + len(back_far)
    seed_far = Seed(seed.xy[:n_far], seed.tan[:n_far], seed.slot[:n_far], seed.stroke[:n_far])
    assert reentries(ride + away + back_far, strands, seed_far, XH, weights) == []


def test_the_hysteresis_leaves_no_reentry_behind() -> None:
    """Two parallel rails; a seed that dips from the lower to the upper one
    and back within a few pixels. Whatever the raw decode chooses, after the
    hysteresis no out-and-back jump is left and the path is one run."""
    path = np.array([[8.0, 20.0], [30.0, 20.0], [31.0, 14.0], [33.0, 14.0], [32.5, 20.0], [72.0, 20.0]])
    seed = _seed_along(path)
    on = TintenpfadWeights(rail="raw", resample_step_xh=0.0)
    strands = strands_of(_two_rails(), XH, on, {})
    states_on, _, ddiag = decode_with_hysteresis(strands, seed, XH, on)
    assert ddiag["reentries_left"] == 0
    runs, _, _, _, counts = assemble(strands, states_on, seed, XH, on)
    assert len(runs) == 1 and counts["paper_lifts"] == 0


def test_hermite_bridge_is_tangent_continuous_and_capped() -> None:
    p0, p1 = np.array([0.0, 0.0]), np.array([10.0, 0.0])
    t0, t1 = np.array([1.0, 0.0]), np.array([1.0, 0.0])
    pts = hermite_bridge(p0, t0, p1, t1, 1.0, 5.0)
    assert np.allclose(pts[-1], p1)
    assert np.abs(pts[:, 1]).max() < 1e-9  # aligned tangents: the chord itself
    assert len(pts) == 10
    # a tangent pointing sideways bows, but never past the cap
    pts = hermite_bridge(p0, np.array([0.0, 1.0]), p1, t1, 1.0, 2.0)
    assert np.abs(pts[:, 1]).max() <= 2.0 + 1e-9
    assert pts[0][1] > 0.0  # it does leave along the leaving tangent
    # a tangent pointing AWAY from the target would overshoot behind p0: capped too
    pts = hermite_bridge(p0, np.array([-1.0, 0.0]), p1, t1, 1.0, 1.0)
    assert pts[:, 0].min() >= -1.0 - 1e-9 and pts[:, 0].max() <= 11.0 + 1e-9


def test_resample_run_is_arclength_uniform_and_carries_labels() -> None:
    pts = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [3.0, 1.0], [3.0, 4.0]])
    labels = np.array([0, 0, 1, 1, 2])
    xy, lab = resample_run(pts, 0.5, labels)
    steps = np.hypot(*np.diff(xy, axis=0).T)
    assert np.allclose(xy[0], pts[0]) and np.allclose(xy[-1], pts[-1])
    assert steps.max() - steps.min() < 0.05
    assert lab[0] == 0 and lab[-1] == 2 and set(lab.tolist()) == {0, 1, 2}


def test_spans_fill_connector_labels_from_the_nearest_letter() -> None:
    spans = spans_of([np.array([0, 0, -1, -1, 1, 1, 1])])
    assert spans == [[[0, 0, 2], [1, 3, 6]]]


def test_the_candidate_payload_passes_the_wire_check() -> None:
    info = {
        "kind": "word",
        "specimen_id": "x",
        "word": "x",
        "strokes": [[[0.0, 0.0], [0.5, 0.2], [1.0, 0.1]]],
        "registration_px": {"tx": 1.0, "ty": 0.0, "baseline_row": 40},
        "xh_px": 32.0,
        "status": "ok",
        "detail": "",
        "meta": {},
    }
    failed = {**info, "specimen_id": "y", "strokes": [], "status": "failed", "detail": "nothing decoded"}
    payload = tintenpfad_payload(
        [info, failed], style="suetterlin", source_id="s", which="words", label="t", weights=LEGACY_P5
    )
    assert payload["tool"] == "wellen.tintenpfad" and payload["frame"] == "word_registration"
    assert payload["weights"]["back_tol_px"] == 2.0 and payload["weights"]["rail"] == "raw"
    assert [r["specimen_id"] for r in payload["rows"]] == ["x"]
    assert payload["excluded"] == [{"specimen_id": "y", "status": "failed", "detail": "nothing decoded"}]
    assert wire_violation(payload["rows"][0]["strokes"]) == ""


def test_weights_are_frozen_and_typed() -> None:
    w = weights_from_overrides(
        TintenpfadWeights(), ["turn_cost=30", "max_cand=12.0", "affine_seed=off", "bridge=chord"]
    )
    assert w.turn_cost == 30.0 and w.max_cand == 12 and w.affine_seed is False and w.bridge == "chord"
    # The Spitzen arm is off in the delivered default and switches on by --weight.
    default = TintenpfadWeights()
    assert default.tip_read is False and default.spur_at_ends is False and default.tip_extend_xh == 0.0
    arm = weights_from_overrides(default, ["tip_read=1", "spur_at_ends=on"])
    assert arm.tip_read is True and arm.spur_at_ends is True
    with pytest.raises(SystemExit):
        weights_from_overrides(TintenpfadWeights(), ["no_such=1"])
    with pytest.raises(ValueError):
        TintenpfadWeights(rail="smooth")
    arm = weights_from_overrides(TintenpfadWeights(), ["rail=tentfit", "edt_upsample=4"])
    assert arm.rail == "tentfit" and arm.edt_upsample == 4 and arm.fit_half_px == 2.0
    with pytest.raises(ValueError):
        TintenpfadWeights(edt_upsample=0)
    with pytest.raises(ValueError):
        TintenpfadWeights(fit_step_px=3.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        TintenpfadWeights().turn_cost = 1.0  # type: ignore[misc]


# ------------------------------------------------------------ the substrate

# The strand set of the 13 loop rows at the frozen words root ccb036a5eb20:
# (strands, closed strands, spurs pruned, junction pairs, junctions too dense).
# Every path of the method is a function of this set; a Flecken or evidence
# change upstream would rewrite all 63 words with no other sensor firing.
SUBSTRATE_CCB036A5EB20 = {
    "unter": (10, 0, 6, 19, 0),
    "die": (3, 0, 2, 9, 0),
    "haben": (8, 0, 2, 18, 0),
    "das": (4, 0, 0, 9, 0),
    "regieren": (16, 0, 8, 27, 0),
    "Soldaten": (14, 0, 2, 29, 0),
    "han": (7, 0, 2, 13, 0),
    "die-2": (5, 0, 1, 7, 0),
    "streiten": (16, 0, 8, 29, 0),
    "fechten": (14, 0, 4, 30, 0),
    "kann": (11, 1, 2, 19, 0),
    "Galoppieren": (14, 1, 9, 41, 0),
    "Sporn": (10, 0, 3, 18, 0),
}


def test_the_strand_set_of_the_frozen_root_is_stable() -> None:
    from tools.pairlab.ink_evidence import INK_EVIDENCE_PAPER_FRACTION, InkEvidenceOptions, ink_evidence_case
    from tools.wordbench.roots import root_digest
    from tools.wordlab.cases import DEFAULT_FIXTURES_DIR, iter_fixture_word_cases

    root = Path(DEFAULT_FIXTURES_DIR) / "suetterlin" / "suetterlin-1922"
    if not (root / "manifest.json").exists():
        pytest.skip("frozen words root not present")
    if not root_digest(root).startswith("ccb036a5eb20"):
        pytest.skip("frozen words root is not ccb036a5eb20 — the substrate pin belongs to that digest")
    cases = iter_fixture_word_cases(
        which="words", style="suetterlin", only=list(SUBSTRATE_CCB036A5EB20), fixtures_root=DEFAULT_FIXTURES_DIR
    )
    seen = {}
    for case in cases:
        case_ev, _ = ink_evidence_case(case, InkEvidenceOptions(paper_fraction=INK_EVIDENCE_PAPER_FRACTION))
        xh = float(case.baseline_y - case.midband_y)
        diag: dict = {}
        strands = strands_of(np.asarray(case_ev.skel, dtype=bool), xh, TintenpfadWeights(rail="raw"), diag)
        seen[case.id] = (
            len(strands),
            diag["closed_strands"],
            diag["spurs_pruned"],
            diag["junction_pairs"],
            diag["junctions_too_dense"],
        )
    assert seen == SUBSTRATE_CCB036A5EB20
