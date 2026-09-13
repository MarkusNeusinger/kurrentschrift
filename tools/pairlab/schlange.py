"""Schlange — an elastic-curve (snake) follower as a stand-alone module (Hook B).

MEASUREMENT LAYER ONLY (2026-09-11, the „Wellen" design round): reads the frozen
fixture, composes, applies the K-C ink evidence and the Gauß-Verschiebung seed
exactly as `tools.pairlab.follow.follow_derived` does, then evolves every WELDED
pen run (letter stroke → connector → letter stroke, cut only at pen lifts) as a
discrete snake in a coarse-to-fine EDT valley, and writes a `tools.tracebench`
file-provider candidate. `_ChainProblem`, its bounds, guard, retrace cage and
zonal pinning are untouched — this module is a SECOND follower beside the
chain, never a switch inside it. No DB, no `core/` change, no fixture change.

Three coherence mechanisms act, in this order, and the pre-registration names
them as such (two are a metric, one is an energy):

1. the STEP is a wave — every update is the force field convolved with the
   Green's function of (I + beta_s·D2ᵀD2), beta_s = ell⁴, so within one
   iteration a node cannot move without its ~ell neighbours (a Sobolev /
   semi-implicit step: the fixed points are those of the forces alone, the
   PATH to them is coherent — this is not the rejected bind penalty);
2. arc-length reparametrisation after EVERY step — nodes are redistributed at
   the fixed spacing `h_px` along the current curve with every ductus corner
   kept as a breakpoint node, so tangential clustering, overtaking or an
   eroded cusp are not states the snake can be in;
3. the equilibrium prices bending of the CURVE with beta_e·|D2 x|², exempt at
   the corner nodes (Kass: beta = 0 at a corner). The EQUILIBRIUM attenuation
   of a per-node force of wavelength lambda nodes is
   beta_e·q² / (beta_e·q² + k_data) with q = 4·sin²(π/lambda) and
   k_data ≈ 1.8/px measured (blurred-EDT valley curvature 0.80/px at
   sigma = 1 plus the ≈1.0/px coverage spring): at beta_e = 4 an 8-px ripple
   is damped ×0.57, at beta_e = 64 ×0.076 while a 1.1-xh wave still passes
   ×0.985. The energy-PRICING ratio (ripple vs loop, k⁴) is much larger than
   that; it is not the suppression and is not quoted as such.

h-dependence, stated once: `beta_e` and `beta_s = ell⁴` are in raw
second-difference units at spacing `h_px` — the unnormalised D2ᵀD2 already
scales as h_px⁴ on a fixed smooth curve, so it is `beta_e` (and `beta_s`)
that must scale as h_px⁻⁴, not the reverse, to hold the same PHYSICAL
bending/metric strength; the coupling length scales as ell·h_px. `h_px` is
PART of the declared setting — whoever changes the node spacing
re-expresses both.

BLAS: this follower is BLAS-insensitive — `solve_banded` is LAPACK gbsv, the
rest is `scipy.ndimage` and `cKDTree`; the path was measured bit-identical
pinned and unpinned (see the 2026-09-11 ledger). The repo rule still pins the
threads on every measurement command line, nothing here pretends to.

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run python -m tools.pairlab.schlange \\
        --set words --jobs 2 --candidate-out <dir>/cand.json --json <dir>/schlange.json \\
        --expect-root ccb036a5eb20 fechten kann unter …
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import solve_banded
from scipy.ndimage import gaussian_filter, map_coordinates, spline_filter, uniform_filter1d
from scipy.spatial import cKDTree

from tools.laufform.harvest import _chainable_runs, _grid_fits, _word_record
from tools.pairlab.affinereg import register_letters
from tools.pairlab.analyze import _to_px
from tools.pairlab.chain import ChainSegmentSpec, _connector_spec, _letter_spec, _prepare_fields
from tools.pairlab.follow import (
    CANDIDATE_FRAME,
    STATUS_FAILED,
    STATUS_OK,
    STATUS_SKIPPED,
    _registration_of,
    _restart_slots,
    _source_id_of,
)
from tools.pairlab.ink_evidence import InkEvidenceOptions, ink_evidence_case
from tools.pairlab.trace import assemble_word_strokes, cap_word_strokes
from tools.wordbench.roots import add_expect_root_argument, announce_roots
from tools.wordlab.cases import DEFAULT_FIXTURES_DIR, WordCase, _root_for, iter_fixture_word_cases
from tools.wordlab.derive import WordDeriveResult, derive_word


SCHLANGE_TOOL_NAME = "pairlab.schlange"
SCHLANGE_ARTIFACT_VERSION = "1"
# The loop words of the 2026-09-11 round (fixture ids; `die` brings `die-2`).
LOOP_WORDS = (
    "fechten",
    "kann",
    "unter",
    "streiten",
    "regieren",
    "Sporn",
    "haben",
    "han",
    "die",
    "das",
    "Soldaten",
    "Galoppieren",
)
# Iterations between two plateau readings of the normal residual (see `evolve_curve`).
PLATEAU_WINDOW = 200
# A stage whose windowed residual falls by less than this fraction has reached
# the ownership-flip chatter floor — the honest stop when `tol_px` cannot fire.
PLATEAU_MIN_DROP = 0.02
# Nodes of the moving average that separates a curve's ripple from its shape:
# a quarter x-height, the band the design round measured the Zittern in.
RIPPLE_WINDOW_XH = 0.25
# Coherence quotient lag (px): the karte's own 1.2 px, so the chain's anchor
# field and the snake's node field are read at ONE lag (D2 scales with lag²).
COHERENCE_LAG_PX = 1.2


@dataclass
class SnakeParams:
    """Every knob of one arm, stamped into the candidate file (`weights`).

    Defaults are the declared setting of the round: the prototype's arm q with
    the judges' corner fix (`corner_halo` 0), the swept `beta_e` (64) and the
    plateau stop; `h_px` is frozen with them, see the module docstring for why.
    """

    h_px: float = 0.8  # node spacing after every reparametrisation (= the chain's median sample spacing)
    sigmas_px: tuple[float, ...] = (2.0, 1.0)  # EDT-valley blur ladder; 1.0 = core.fit.DIST_FIELD_SIGMA_PX
    # 4 px measured dead (prototype arm a): it merges the two sides of an e-loop
    # (inner width ≈ 0.3 xh ≈ 10 px) into ONE valley and the loop collapses.
    cov_weight: float = 1.0  # skeleton→curve force (recall); 0 = the pure Kass snake (misses the a-bowl, arm e)
    cov_cap_px: float = 6.0  # Huber-like cap on one pull, ≈ 0.2 xh (chain: CHAIN_COVERAGE_CAP_UNITS 0.30)
    cov_soft_k: int = 0  # 0 = hard nearest-node ownership; k > 0 = Gaussian responsibilities over the k nearest nodes
    cov_soft_sigma_px: float = 2.0  # width of those responsibilities (only with cov_soft_k > 0)
    ell_nodes: float = 7.0  # metric kernel width in nodes: beta_s = ell⁴ (measured ripple period ≈ 10 samples)
    # Bending ENERGY on the curve, raw second-difference units at spacing h_px.
    # Swept {4, 16, 64, 256} on the twelve loop words (2026-09-11): ink
    # reversals 113 / 105 / 78 / 54, paper 5.54 / 5.34 / 4.47 / 4.17 xh, paired
    # dtw delta +0.0044 / +0.0040 / +0.0010 / +0.0010, absorption 102 / 99 /
    # 104 / 186 — 256 starts to lose structure (2 stranded curves, unter loses
    # a crossing), 64 is the declared setting.
    beta_e: float = 64.0
    alpha_e: float = 0.0  # tension energy (0: the reparametrisation already keeps the spacing)
    gamma: float = 0.02  # letter home spring per px; ladder 0.05 / 0.02 / 0.01 = paper 8.3 / 5.3 / 3.3 xh (arms i/q/r)
    gamma_connector: float = 0.0  # home spring on CONNECTOR nodes (the chain's reg_w = 0 on connector interiors)
    tau: float = 0.5  # step (px per unit force); stable up to beta_e = 64 with ell = 7, measured
    max_iter: int = 20000  # per stage — a CAP that the plateau rule is meant to make unreachable
    tol_px: float = 1e-3  # stop when the largest NORMAL node move stays below this for `quiet_iters`
    quiet_iters: int = 3
    # Plateau stop: a stage ends when the windowed normal residual (median over
    # PLATEAU_WINDOW iterations) falls by less than this fraction against the
    # previous window. 0 disables it — then only tol_px or max_iter end a stage
    # (the cap-independence arm).
    plateau_drop: float = PLATEAU_MIN_DROP
    corner_halo: int = 0  # bending rows freed on either side of a corner; 1 measured as an isolated node (judges)
    stranded_px: float = 1.0  # a curve whose nodes sit further than this from the skeleton on average is FLAGGED
    seed: str = "affine"  # Gauß-Verschiebung seed, as in iteration 17
    bar_bridge: bool = True
    ink_evidence: bool = True


# ------------------------------------------------------------------ the seed


def run_pieces(
    case: WordCase, result: WordDeriveResult, run: list[int], affines: dict, *, bar_bridge: bool = True
) -> list[dict] | None:
    """The run's segments as ordered pen-down pieces with weld flags and corners.

    A piece is one (segment, stroke) of the chain's own specs — letters cut at
    their FINAL `stroke_starts` (after the bar bridge), connectors whole — and
    carries `w_in` / `w_out` (does it hold the seam anchor shared with the
    previous / next segment), which is all the weld rule needs.
    """
    specs: list[ChainSegmentSpec] = []
    for n, slot in enumerate(run):
        made = _letter_spec(case, result, slot, bar_bridge=bar_bridge, affine=affines.get(slot))
        if made is None:
            return None
        spec, _offset = made
        if n:
            conn = _connector_spec(result, run[n - 1])
            if conn is None:
                return None
            specs.append(conn)
        specs.append(spec)
    # The composed connector starts/ends where the UNSHIFTED letters were; the
    # affine seed moved both. Blend its two ends onto the seams it must meet
    # (the chain does this through the shared seam parameter + the exit ramp).
    for i, sp in enumerate(specs):
        if sp.kind != "connector":
            continue
        prev, nxt = specs[i - 1], specs[i + 1]
        a = np.asarray(prev.anchors[prev.seam_out], dtype=float)
        b = np.asarray(nxt.anchors[nxt.seam_in], dtype=float)
        c = np.asarray(sp.anchors, dtype=float).copy()
        steps = np.linalg.norm(np.diff(c, axis=0), axis=1)
        arc = np.concatenate([[0.0], np.cumsum(steps)])
        t = arc / arc[-1] if arc[-1] > 0 else np.linspace(0.0, 1.0, len(c))
        c += (1.0 - t)[:, None] * (a - c[0]) + t[:, None] * (b - c[-1])
        sp.anchors = c
    pieces: list[dict] = []
    for i, sp in enumerate(specs):
        k = len(sp.anchors)
        if sp.kind == "connector":
            pieces.append(
                {
                    "seg": i,
                    "stroke": 0,
                    "kind": "connector",
                    "slot": None,
                    "key": None,
                    "pts": np.asarray(sp.anchors, dtype=float),
                    "corners": [],
                    "w_in": True,
                    "w_out": True,
                }
            )
            continue
        starts = [int(s) for s in sp.stroke_starts if int(s) < k]
        bounds = [*starts, k] if starts else [0, k]
        for si, (a, b) in enumerate(zip(bounds[:-1], bounds[1:], strict=True)):
            corners = [int(c) - a for c in sp.corner_anchors if a < int(c) < b - 1]
            pieces.append(
                {
                    "seg": i,
                    "stroke": si,
                    "kind": "letter",
                    "slot": sp.slot_index,
                    "key": sp.key,
                    "pts": np.asarray(sp.anchors[a:b], dtype=float),
                    "corners": corners,
                    "w_in": sp.seam_in is not None and a <= sp.seam_in < b,
                    "w_out": sp.seam_out is not None and a <= sp.seam_out < b,
                }
            )
    return pieces


def weld_pieces(pieces: Sequence[dict]) -> list[list[dict]]:
    """Pieces → welded pen runs: the assembler's rule, applied BEFORE the solve.

    A connector attaches to the current curve iff that curve's last piece holds
    the seam-out anchor; a letter piece holding the seam-in anchor attaches iff
    the current curve ends in a connector; a piece holding neither seam (an
    interior lift, an i-dot, a u-breve) is its own pen run.
    """
    curves: list[list[dict]] = []
    current: list[dict] | None = None
    for p in pieces:
        if p["kind"] == "connector":
            if current is not None and current[-1]["w_out"]:
                current.append(p)
            else:
                if current is not None:
                    curves.append(current)
                current = [p]
            continue
        if p["w_in"] and current is not None and current[-1]["kind"] == "connector":
            current.append(p)
        elif p["w_in"] or p["w_out"]:
            if current is not None:
                curves.append(current)
            current = [p]
        else:
            curves.append([p])
    if current is not None:
        curves.append(current)
    return curves


def seed_curve(curve: Sequence[dict], xh: float, tx: float, ty: float, baseline_row: float) -> dict:
    """One welded run in crop px: polyline, seed arc length, piece bounds, corners.

    The seam anchor two pieces share is kept ONCE; every piece's bounds and
    every corner are recorded as SEED ARC-LENGTH coordinates (`s0`), the
    material label that survives all reparametrisations.
    """
    pts_list: list[np.ndarray] = []
    piece_bounds: list[tuple[float, float]] = []
    connector_spans: list[tuple[float, float]] = []
    corner_s: list[float] = []
    total = 0.0
    tail: np.ndarray | None = None
    for p in curve:
        px = _to_px(p["pts"], xh, tx, ty, baseline_row)
        if tail is not None and len(px) and np.allclose(tail, px[0], atol=1e-6):
            px_eff = px[1:]
        else:
            px_eff = px
        if tail is not None:
            px_eff = np.vstack([tail[None, :], px_eff]) if len(px_eff) else tail[None, :]
        steps = np.linalg.norm(np.diff(px_eff, axis=0), axis=1) if len(px_eff) > 1 else np.zeros(0)
        cum = total + np.concatenate([[0.0], np.cumsum(steps)])
        # Shared seam (px[0] dropped, tail takes its place 1:1): px_eff has the
        # SAME length as px, so corner index c still points at px_eff[c]. No
        # shared seam (tail prepended in full): px_eff is one LONGER than px,
        # so every c shifts by one.
        off = 0 if tail is None else (0 if len(px_eff) == len(px) else 1)
        for c in p["corners"]:
            j = c + off
            if 0 <= j < len(cum):
                corner_s.append(float(cum[j]))
        piece_bounds.append((float(cum[0]), float(cum[-1])))
        if p["kind"] == "connector":
            connector_spans.append((float(cum[0]), float(cum[-1])))
        pts_list.append(px_eff if tail is None else px_eff[1:])
        total = float(cum[-1])
        tail = px_eff[-1]
    pts = np.vstack(pts_list)
    steps = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    keep = np.concatenate([[True], steps > 1e-9])
    pts = pts[keep]
    steps = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(steps)])
    return {
        "pts": pts,
        "cum": cum,
        "piece_bounds": piece_bounds,
        "connector_spans": connector_spans,
        "corner_s": np.asarray(corner_s, dtype=float),
        "pieces": list(curve),
    }


# ----------------------------------------------------------------- the snake


def resample_curve(
    x: np.ndarray, s0: np.ndarray, h: float, corner_s: np.ndarray | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Uniform arc-length resampling at spacing `h` with every ductus corner kept
    as a NODE (a breakpoint of the resampling).

    Linear resampling across a cusp would chop it by up to h/2 per step, and
    over thousands of steps that erodes a real corner into an arc the reversal
    sensor then cannot see (the first prototype reported ink reversals 0 that
    way — a false pass on the loop's primary sensor). `s0` is interpolated
    linearly in arc length: nodes slide, the seed correspondence does not.
    """
    d = np.linalg.norm(np.diff(x, axis=0), axis=1)
    keep = np.concatenate([[True], d > 1e-9])
    x, s0 = x[keep], s0[keep]
    if len(x) < 2:
        return x, s0
    d = np.linalg.norm(np.diff(x, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(d)])
    breaks = [0.0]
    if corner_s is not None and len(corner_s):
        inside = corner_s[(corner_s > s0[0]) & (corner_s < s0[-1])]
        breaks.extend(float(c) for c in np.interp(np.sort(inside), s0, cum))
    breaks.append(float(cum[-1]))
    ts: list[np.ndarray] = []
    for a, b in zip(breaks[:-1], breaks[1:], strict=True):
        if b - a <= 1e-9:
            continue
        n = max(2, int(round((b - a) / h)) + 1)
        seg = np.linspace(a, b, n)
        ts.append(seg if not ts else seg[1:])
    t = np.concatenate(ts) if ts else np.array([0.0, cum[-1]])
    if len(t) < 3:
        t = np.linspace(0.0, cum[-1], 3)
    xn = np.column_stack([np.interp(t, cum, x[:, 0]), np.interp(t, cum, x[:, 1])])
    return xn, np.interp(t, cum, s0)


def bending_apply(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    """(D2ᵀ diag(w) D2) x for one open curve (`w` has n−2 rows)."""
    dd = x[:-2] - 2.0 * x[1:-1] + x[2:]
    g = w[:, None] * dd
    out = np.zeros_like(x)
    out[:-2] += g
    out[1:-1] -= 2.0 * g
    out[2:] += g
    return out


def metric_banded(n: int, beta_s: float, alpha_s: float = 0.0) -> np.ndarray:
    """`ab` for `solve_banded((2, 2), …)` of I + beta_s·D2ᵀD2 + alpha_s·D1ᵀD1 (open ends)."""
    w = np.full(n - 2, beta_s)
    diag = np.ones(n)
    diag[:-2] += w
    diag[1:-1] += 4.0 * w
    diag[2:] += w
    up1 = np.zeros(n - 1)
    up1[:-1] -= 2.0 * w
    up1[1:] -= 2.0 * w
    up2 = w.copy()
    if alpha_s:
        a = np.full(n - 1, alpha_s)
        diag[:-1] += a
        diag[1:] += a
        up1 -= a
    ab = np.zeros((5, n))
    ab[0, 2:] = up2
    ab[1, 1:] = up1
    ab[2] = diag
    ab[3, :-1] = up1
    ab[4, :-2] = up2
    return ab


def metric_dense(n: int, beta_s: float, alpha_s: float = 0.0) -> np.ndarray:
    """The same operator as a dense matrix — the test oracle for `metric_banded`."""
    d2 = np.zeros((n - 2, n))
    for i in range(n - 2):
        d2[i, i : i + 3] = (1.0, -2.0, 1.0)
    d1 = np.zeros((n - 1, n))
    for i in range(n - 1):
        d1[i, i : i + 2] = (-1.0, 1.0)
    return np.eye(n) + beta_s * d2.T @ d2 + alpha_s * d1.T @ d1


def bending_weights(n: int, s0: np.ndarray, corner_s: np.ndarray, beta_e: float, halo: int) -> np.ndarray:
    """Per-row bending weight: `beta_e` everywhere, 0 on the row whose middle
    node is a corner (and `halo` rows on either side).

    Row j of D2 is centred on node j+1. With halo 0 exactly the corner's own
    row is free — the cusp may kink, its neighbours stay coupled (the judges'
    point-force probe: nb/peak 0.47 at halo 0, 0.00 at halo 1)."""
    w = np.full(n - 2, beta_e)
    if len(corner_s) and beta_e:
        idx = np.searchsorted(s0, corner_s)
        for j in idx:
            lo, hi = max(0, j - 1 - halo), min(n - 2, j - 1 + halo + 1)
            w[lo:hi] = 0.0
    return w


def coverage_force(x: np.ndarray, cov_pts: np.ndarray, prm: SnakeParams) -> np.ndarray:
    """Recall: every skeleton pixel pulls the node(s) that own it.

    Hard ownership (default): the nearest node; the pull is capped Huber-like
    at `cov_cap_px`, per node the MEAN of its pulls clipped to unit magnitude,
    so a stranded node is never hit by the 32× force the chain's decomposition
    measured, and the metric step then spreads it over the neighbourhood.
    Soft ownership (`cov_soft_k` > 0): Gaussian responsibilities over the k
    nearest nodes, normalised per pixel — the CPD-style fix for the
    ownership-flip chatter, a switch of its own.
    """
    n = len(x)
    k = int(prm.cov_soft_k)
    if k <= 0:
        dist, owner = cKDTree(x).query(cov_pts)
        vec = cov_pts - x[owner]
        scale = np.minimum(1.0, prm.cov_cap_px / np.maximum(dist, 1e-9))
        pull = np.zeros_like(x)
        np.add.at(pull, owner, vec * scale[:, None])
        count = np.bincount(owner, minlength=n).astype(float)
    else:
        k = min(k, n)
        dist, owner = cKDTree(x).query(cov_pts, k=k)
        dist = dist.reshape(len(cov_pts), k)
        owner = owner.reshape(len(cov_pts), k)
        resp = np.exp(-0.5 * (dist / prm.cov_soft_sigma_px) ** 2)
        resp /= np.maximum(resp.sum(axis=1, keepdims=True), 1e-12)
        vec = cov_pts[:, None, :] - x[owner]
        scale = np.minimum(1.0, prm.cov_cap_px / np.maximum(dist, 1e-9)) * resp
        pull = np.zeros_like(x)
        np.add.at(pull, owner.ravel(), (vec * scale[:, :, None]).reshape(-1, 2))
        count = np.bincount(owner.ravel(), weights=resp.ravel(), minlength=n)
    pull /= np.maximum(count, 1.0)[:, None]
    mag = np.linalg.norm(pull, axis=1)
    pull *= np.minimum(1.0, 1.0 / np.maximum(mag, 1e-9))[:, None]
    return prm.cov_weight * pull


def _unit_tangent(x: np.ndarray) -> np.ndarray:
    tang = np.gradient(x, axis=0)
    return tang / np.maximum(np.linalg.norm(tang, axis=1), 1e-9)[:, None]


def field_wobble(x: np.ndarray, pot_c: np.ndarray, xh: float, h: float, half_range_px: float = 2.0) -> dict:
    """How much of the curve's residual ripple is the EVIDENCE's own wobble.

    Along the final curve the valley of the blurred EDT is located on each
    node's normal (parabolic sub-pixel refinement of the minimum over
    ±`half_range_px`); the valley offset high-passed by a moving average over
    a quarter x-height is the field's wobble under the curve, the curve's own
    lateral residual against the same moving average its ripple. Both in px
    RMS, so "ripple minus wobble" is a like-for-like subtraction.
    """
    n = len(x)
    if n < 8:
        return {"field_wobble_px": None, "curve_ripple_px": None}
    tang = _unit_tangent(x)
    nrm = np.column_stack([-tang[:, 1], tang[:, 0]])
    offs = np.linspace(-half_range_px, half_range_px, int(round(8 * half_range_px)) + 1)
    hgt, wid = pot_c.shape
    vals = np.empty((n, len(offs)))
    for j, o in enumerate(offs):
        p = x + o * nrm
        vals[:, j] = map_coordinates(
            pot_c,
            [np.clip(p[:, 1], 0, hgt - 1), np.clip(p[:, 0], 0, wid - 1)],
            order=3,
            mode="nearest",
            prefilter=False,
        )
    j0 = np.argmin(vals, axis=1)
    valley = offs[j0].astype(float)
    inner = (j0 > 0) & (j0 < len(offs) - 1)
    if inner.any():
        ii = np.flatnonzero(inner)
        ym, y0, yp = vals[ii, j0[ii] - 1], vals[ii, j0[ii]], vals[ii, j0[ii] + 1]
        denom = ym - 2 * y0 + yp
        ok = denom > 1e-12
        step = offs[1] - offs[0]
        valley[ii[ok]] += 0.5 * (ym[ok] - yp[ok]) / denom[ok] * step
    win = max(3, int(round(RIPPLE_WINDOW_XH * xh / h)))
    wob = valley - uniform_filter1d(valley, win, mode="nearest")
    lat = ((x - uniform_filter1d(x, win, axis=0, mode="nearest")) * nrm).sum(1)
    return {
        "field_wobble_px": round(float(np.sqrt((wob**2).mean())), 4),
        "curve_ripple_px": round(float(np.sqrt((lat**2).mean())), 4),
    }


def evolve_curve(seed: dict, fields: dict, prm: SnakeParams, xh: float) -> dict:
    """Run the sigma ladder on one welded curve; returns nodes, s0 and diagnostics.

    Per stage the CONVERGENCE STATEMENT is the normal residual: the largest
    and the RMS normal component of tau·v over the last `PLATEAU_WINDOW`
    iterations (tangential circulation never stops under reparametrisation and
    never changes the curve). A stage ends on `tol` (largest normal move below
    `tol_px` for `quiet_iters`), on `plateau` (the windowed residual stopped
    falling — the chatter floor of hard ownership) or, as a failure it reports,
    on `cap`.
    """
    x0_pts, x0_cum = seed["pts"], seed["cum"]
    corner_s = seed["corner_s"]
    x, s0 = resample_curve(x0_pts, x0_cum, prm.h_px, corner_s)
    if len(x) < 3:
        return {"x": x, "s0": s0, "stages": [], "n_nodes": len(x), "wobble": {}}
    hgt, wid = fields["dist_raw"].shape
    beta_s = float(prm.ell_nodes) ** 4
    stages: list[dict] = []
    cov_pts = np.asarray(fields["cov_pts"], dtype=float).reshape(-1, 2)
    pot_c = None
    for sigma in prm.sigmas_px:
        pot = gaussian_filter(fields["dist_raw"], sigma) if sigma > 0 else np.asarray(fields["dist_raw"], dtype=float)
        gy, gx = np.gradient(pot)
        # Cubic-spline coefficients once per stage: a bilinear read of a lattice
        # gradient jumps at every pixel edge and the nodes chatter on those
        # jumps instead of settling.
        gx_c, gy_c = spline_filter(gx, order=3), spline_filter(gy, order=3)
        pot_c = spline_filter(pot, order=3)
        n_it = 0
        quiet = 0
        stop = "cap"
        hist: list[float] = []
        hist_rms: list[float] = []
        prev_window: float | None = None
        for n_it in range(1, prm.max_iter + 1):
            n = len(x)
            ys = np.clip(x[:, 1], 0, hgt - 1)
            xs = np.clip(x[:, 0], 0, wid - 1)
            f = -np.column_stack(
                [
                    map_coordinates(gx_c, [ys, xs], order=3, mode="nearest", prefilter=False),
                    map_coordinates(gy_c, [ys, xs], order=3, mode="nearest", prefilter=False),
                ]
            )
            if prm.cov_weight and len(cov_pts):
                f += coverage_force(x, cov_pts, prm)
            home = np.column_stack([np.interp(s0, x0_cum, x0_pts[:, 0]), np.interp(s0, x0_cum, x0_pts[:, 1])])
            gam = np.full(n, prm.gamma)
            for a_s, b_s in seed["connector_spans"]:
                gam[(s0 > a_s) & (s0 < b_s)] = prm.gamma_connector
            f -= gam[:, None] * (x - home)
            f -= bending_apply(x, bending_weights(n, s0, corner_s, prm.beta_e, prm.corner_halo))
            if prm.alpha_e:
                d1 = np.diff(x, axis=0)
                t_ = np.zeros_like(x)
                t_[:-1] += d1
                t_[1:] -= d1
                f += prm.alpha_e * t_
            v = solve_banded((2, 2), metric_banded(n, beta_s), f)
            step = prm.tau * v
            tang = _unit_tangent(x)
            normal_step = step - (step * tang).sum(1)[:, None] * tang
            nmag = np.linalg.norm(normal_step, axis=1)
            max_move = float(nmag.max())
            hist.append(max_move)
            hist_rms.append(float(np.sqrt((nmag**2).mean())))
            x = x + step
            x, s0 = resample_curve(x, s0, prm.h_px, corner_s)
            quiet = quiet + 1 if max_move < prm.tol_px else 0
            if quiet >= prm.quiet_iters:
                stop = "tol"
                break
            if prm.plateau_drop > 0 and n_it % PLATEAU_WINDOW == 0:
                window = float(np.median(hist[-PLATEAU_WINDOW:]))
                if prev_window is not None and window >= (1.0 - prm.plateau_drop) * prev_window:
                    stop = "plateau"
                    break
                prev_window = window
        ys = np.clip(np.round(x[:, 1]).astype(int), 0, hgt - 1)
        xs = np.clip(np.round(x[:, 0]).astype(int), 0, wid - 1)
        tail = hist[-PLATEAU_WINDOW:]
        tail_rms = hist_rms[-PLATEAU_WINDOW:]
        stages.append(
            {
                "sigma": sigma,
                "iters": n_it,
                "stop": stop,
                "hit_cap": stop == "cap",
                "last_move_px": round(hist[-1], 5) if hist else None,
                "residual_max_px": round(float(np.median(tail)), 5) if tail else None,
                "residual_rms_px": round(float(np.median(tail_rms)), 5) if tail_rms else None,
                "mean_dist_px": round(float(fields["dist_raw"][ys, xs].mean()), 3),
                "n_nodes": len(x),
            }
        )
    wobble = field_wobble(x, pot_c, xh, prm.h_px) if pot_c is not None else {}
    return {"x": x, "s0": s0, "stages": stages, "n_nodes": len(x), "wobble": wobble}


def coherence_stats(x: np.ndarray, s0: np.ndarray, seed: dict, xh: float, lag_px: float = COHERENCE_LAG_PX) -> dict:
    """The karte's statistic on the FINAL displacement field d = x − x0(s0):
    RMS D2(d) / RMS d, the field resampled at `lag_px` along the curve. 0 for a
    rigid or linear (perfectly coherent) motion, ≈4 for alternating signs.

    Reported for the whole curve AND at the corner nodes alone (the lag
    samples nearest each corner), so a freed cusp cannot hide in a median.
    """
    home = np.column_stack(
        [np.interp(s0, seed["cum"], seed["pts"][:, 0]), np.interp(s0, seed["cum"], seed["pts"][:, 1])]
    )
    d = x - home
    steps = np.linalg.norm(np.diff(x, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(steps)])
    if cum[-1] < 3 * lag_px:
        return {"ratio": None, "ratio_corners": None, "rms_d_xh": None, "n": len(x)}
    t = np.arange(0.0, cum[-1], lag_px)
    dl = np.column_stack([np.interp(t, cum, d[:, 0]), np.interp(t, cum, d[:, 1])])
    d2 = dl[:-2] - 2 * dl[1:-1] + dl[2:]
    rms_d = float(np.sqrt((dl**2).sum(1).mean()))
    rms_d2 = float(np.sqrt((d2**2).sum(1).mean()))
    ratio_corners = None
    corner_s = seed["corner_s"]
    if len(corner_s) and len(d2):
        c_cum = np.interp(corner_s, s0, cum)
        j = np.clip(np.searchsorted(t, c_cum) - 1, 0, len(d2) - 1)
        rms_d2_c = float(np.sqrt((d2[j] ** 2).sum(1).mean()))
        ratio_corners = round(rms_d2_c / rms_d, 3) if rms_d > 1e-9 else None
    # Neighbour-angle statistic (the author's picture of the defect: one point
    # darts off, the next comes back): the angle between the displacement
    # vectors of two lag-neighbours, over pairs where both exceed 0.5 px — a
    # smooth field passing through zero makes tiny opposite vectors, which is
    # not the defect. Reported as max, p95 and the share over 90 degrees.
    ang_max = ang_p95 = over_90 = None
    nrm = np.linalg.norm(dl, axis=1)
    ok = (nrm[:-1] > 0.5) & (nrm[1:] > 0.5)
    if ok.any():
        cosang = (dl[:-1] * dl[1:]).sum(1)[ok] / (nrm[:-1] * nrm[1:])[ok]
        ang = np.degrees(np.arccos(np.clip(cosang, -1, 1)))
        ang_max = round(float(ang.max()), 1)
        ang_p95 = round(float(np.percentile(ang, 95)), 1)
        over_90 = round(float((ang > 90).mean()), 4)
    return {
        "ratio": round(rms_d2 / rms_d, 3) if rms_d > 1e-9 else None,
        "ratio_corners": ratio_corners,
        "rms_d_xh": round(rms_d / xh, 4),
        "max_d_xh": round(float(np.linalg.norm(d, axis=1).max()) / xh, 4),
        "neighbour_angle_max_deg": ang_max,
        "neighbour_angle_p95_deg": ang_p95,
        "neighbour_over_90_frac": over_90,
        "n_pairs": int(ok.sum()),
        "n": len(x),
    }


def cut_back(x: np.ndarray, s0: np.ndarray, seed: dict) -> list[dict]:
    """Nodes → one polyline per (segment, stroke) piece, sharing the boundary points."""
    entries = []
    for p, (sa, sb) in zip(seed["pieces"], seed["piece_bounds"], strict=True):
        inside = (s0 > sa) & (s0 < sb)
        head = np.array([np.interp(sa, s0, x[:, 0]), np.interp(sa, s0, x[:, 1])])
        tail = np.array([np.interp(sb, s0, x[:, 0]), np.interp(sb, s0, x[:, 1])])
        pts = np.vstack([head[None, :], x[inside], tail[None, :]])
        entries.append(
            {
                "kind": p["kind"],
                "segment_index": p["seg"],
                "slot_index": p["slot"],
                "key": p["key"],
                "stroke_index": p["stroke"],
                "points_px": pts,
            }
        )
    return entries


def ductus_order(entries: list[dict]) -> list[dict]:
    """Entries sorted by (segment, stroke): the assembler ranks pen runs by their
    first entry, and a diacritic emitted before the body run would put the
    i-dot FIRST in the stroke list (prototype arm a: marks missing 0 → 4 and
    the order-aware dtw paid 0.06 xh on every word)."""
    return sorted(entries, key=lambda e: (int(e["segment_index"]), int(e["stroke_index"])))


# ------------------------------------------------------------------ per word


def _row(case: WordCase, status: str, detail: str) -> dict:
    """An empty candidate-shaped row — the shape `follow_case` returns when the
    word never reaches the snake."""
    return {
        "kind": case.kind,
        "specimen_id": case.id,
        "word": case.word,
        "strokes": [],
        "registration_px": {},
        "xh_px": None,
        "status": status,
        "detail": detail,
        "meta": {},
    }


def follow_case(case: WordCase, prm: SnakeParams | None = None) -> dict:
    """The whole word — the candidate-shaped row (`follow_derived`'s shape).

    A case the fixtures froze as unscorable (an unauthored template), a
    composition missing a glyph and any exception on the way each come back as
    a `skipped`/`failed` ROW, never as a raised exception: one word must not
    take a sweep down — `tools.pairlab.follow.follow_case`'s doctrine, and the
    one `run_cases` relies on, because an exception escaping
    `ProcessPoolExecutor.map` aborts the whole `--all` run.
    """
    prm = prm or SnakeParams()
    started = time.perf_counter()
    if not case.scorable:
        return _row(case, STATUS_SKIPPED, "frozen unscorable (unauthored template)")
    try:
        result = derive_word(case)
    except Exception as exc:  # noqa: BLE001 — one bad case must not end the run
        return _row(case, STATUS_FAILED, f"{type(exc).__name__}: {exc}")
    if result.composed.get("missing"):
        return _row(case, STATUS_SKIPPED, f"composition missing {result.composed['missing']}")
    try:
        return _follow_derived(case, result, prm, started)
    except Exception as exc:  # noqa: BLE001 — a solver crash is one word's row
        return _row(case, STATUS_FAILED, f"{type(exc).__name__}: {exc}")


def _follow_derived(case: WordCase, result: WordDeriveResult, prm: SnakeParams, started: float) -> dict:
    """The snake itself, on an already-derived word (`follow_case` owns the
    guards around it)."""
    xh = float(result.xh_px)
    registration = _registration_of(result)
    tx, ty, baseline_row = float(registration["tx"]), float(registration["ty"]), float(registration["baseline_row"])
    ink_report = None
    if prm.ink_evidence:
        # K-C: AFTER derive_word (ruler and registration on the full ink), BEFORE
        # any window or field — one evidence for seed, fields and coverage.
        case, ink_report = ink_evidence_case(case, InkEvidenceOptions())
    grids = _grid_fits(case, result)
    affreg = register_letters(case, result) if prm.seed == "affine" else {}
    word_strokes: list[list[list[float]]] = []
    traced: set[int] = set()
    runs_meta: list[dict] = []
    flagged: list[dict] = []
    for run in _chainable_runs(case, grids):
        affines = {s: (affreg[s]["A"], affreg[s]["t"]) for s in run if s in affreg}
        pieces = run_pieces(case, result, run, affines, bar_bridge=prm.bar_bridge)
        if pieces is None:
            runs_meta.append({"run": run, "status": "no seed"})
            continue
        wins = [grids[s]["window"] for s in run]
        fields = _prepare_fields(case, min(w[0] for w in wins), max(w[1] for w in wins))
        if fields is None:
            runs_meta.append({"run": run, "status": "no ink"})
            continue
        entries: list[dict] = []
        curves_meta: list[dict] = []
        for curve in weld_pieces(pieces):
            seed = seed_curve(curve, xh, tx, ty, baseline_row)
            ev = evolve_curve(seed, fields, prm, xh)
            if len(ev["x"]) < 3:
                entries.extend(
                    {
                        "kind": p["kind"],
                        "segment_index": p["seg"],
                        "slot_index": p["slot"],
                        "key": p["key"],
                        "stroke_index": p["stroke"],
                        "points_px": _to_px(p["pts"], xh, tx, ty, baseline_row),
                    }
                    for p in curve
                )
                continue
            entries.extend(cut_back(ev["x"], ev["s0"], seed))
            final = ev["stages"][-1] if ev["stages"] else {}
            stranded = bool(final and final["mean_dist_px"] > prm.stranded_px)
            cm = dict(
                pieces=[(p["kind"], p["key"], p["stroke"]) for p in curve],
                seed_len_xh=round(float(seed["cum"][-1]) / xh, 3),
                n_corners=int(len(seed["corner_s"])),
                stages=ev["stages"],
                coherence=coherence_stats(ev["x"], ev["s0"], seed, xh),
                stranded=stranded,
                **ev["wobble"],
            )
            curves_meta.append(cm)
            if stranded:
                flagged.append({"run": run, "pieces": cm["pieces"], "mean_dist_px": final["mean_dist_px"]})
        strokes = assemble_word_strokes(
            ductus_order(entries),
            traced_slots=set(run),
            xh=xh,
            registration=registration,
            restart_slots=_restart_slots(case),
        )
        word_strokes.extend(strokes)
        traced.update(run)
        runs_meta.append({"run": run, "status": "ok", "curves": curves_meta})
    meta: dict[str, Any] = {
        "fit_path": "schlange",
        "weights": asdict(prm),
        "runs": runs_meta,
        "traced_slots": sorted(traced),
        "flagged_curves": flagged,
        "hit_cap": any(s["hit_cap"] for r in runs_meta for c in r.get("curves", []) for s in c["stages"]),
        "seconds": round(time.perf_counter() - started, 2),
        **({"ink_evidence": ink_report.as_dict()} if ink_report is not None else {}),
    }
    if not word_strokes:
        return {
            "kind": case.kind,
            "specimen_id": case.id,
            "word": case.word,
            "strokes": [],
            "registration_px": {},
            "xh_px": None,
            "status": STATUS_FAILED,
            "detail": "the snake produced no pen path",
            "meta": meta,
        }
    record = _word_record(case, cap_word_strokes(word_strokes, label=f"{case.id} (schlange)"), registration, xh, {})
    return {
        "kind": record["kind"],
        "specimen_id": record["specimen_id"],
        "word": record["word"],
        "strokes": record["strokes"],
        "registration_px": record["measurements"]["registration_px"],
        "xh_px": record["measurements"]["xh_px"],
        "status": STATUS_OK,
        "detail": "",
        "meta": meta,
    }


def snake_payload(
    infos: Sequence[dict], *, style: str, source_id: str, which: str, label: str, prm: SnakeParams
) -> dict:
    """The rows as a `tools.tracebench` FILE-provider candidate, every stamped
    field the snake's own (`follow.candidate_payload` would stamp
    `FollowWeights` defaults and `provisional` from an unrelated dataclass).
    Rows without a pen path are counted under `excluded`, never written empty.
    """
    rows = [
        {
            "kind": i.get("kind"),
            "specimen_id": i["specimen_id"],
            "word": i.get("word"),
            "registration_px": i["registration_px"],
            "xh_px": i["xh_px"],
            "strokes": i["strokes"],
            "status": i.get("status", STATUS_OK),
            "meta": i.get("meta", {}),
        }
        for i in infos
        if i.get("status") == STATUS_OK and i.get("strokes")
    ]
    excluded = [
        {"specimen_id": i["specimen_id"], "status": i.get("status"), "detail": i.get("detail", "")}
        for i in infos
        if i.get("status") != STATUS_OK or not i.get("strokes")
    ]
    return {
        "tool": SCHLANGE_TOOL_NAME,
        "version": SCHLANGE_ARTIFACT_VERSION,
        "label": label,
        "style": style,
        "source_id": source_id,
        "set": which,
        "frame": CANDIDATE_FRAME,
        "weights": asdict(prm),
        "provisional": True,
        "excluded": excluded,
        "rows": rows,
    }


# --------------------------------------------------------------------- the CLI


def _job(job: tuple[WordCase, dict]) -> dict:
    case, prm_dict = job
    prm = SnakeParams(**prm_dict)
    prm.sigmas_px = tuple(prm.sigmas_px)
    return follow_case(case, prm)


def run_cases(cases: Sequence[WordCase], prm: SnakeParams, *, jobs: int = 1) -> list[dict]:
    payload = [(c, asdict(prm)) for c in cases]
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            return list(pool.map(_job, payload))
    return [_job(j) for j in payload]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pairlab.schlange", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("ids", nargs="*", help="fixture case ids (or words); default with --all: the whole set")
    parser.add_argument("--all", action="store_true", help="every case of the set")
    parser.add_argument("--set", dest="which", default="words", choices=["words", "pairs"])
    parser.add_argument("--style", default="suetterlin")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES_DIR)
    add_expect_root_argument(parser)
    parser.add_argument("--label", default="schlange")
    parser.add_argument("--jobs", type=int, default=1, help="worker processes, pooled over CASES")
    parser.add_argument("--json", type=Path, help="write the full report here")
    parser.add_argument("--candidate-out", type=Path, help="write a tracebench file-provider candidate here")
    defaults = SnakeParams()
    for f in fields(SnakeParams):
        flag = f"--{f.name.replace('_', '-')}"
        if f.name == "sigmas_px":
            parser.add_argument(
                "--sigmas",
                default=None,
                help=f"comma list of blur sigmas in px (default {','.join(str(s) for s in defaults.sigmas_px)})",
            )
        elif f.type == "bool":
            parser.add_argument(
                f"--no-{f.name.replace('_', '-')}",
                dest=f.name,
                action="store_false",
                default=None,
                help=f"switch {f.name} off (default on)",
            )
        elif f.name == "seed":
            parser.add_argument(flag, choices=("affine", "composed"), default=None, help=f"default {defaults.seed}")
        elif f.type == "int":
            parser.add_argument(flag, type=int, default=None, help=f"default {getattr(defaults, f.name)}")
        else:
            parser.add_argument(flag, type=float, default=None, help=f"default {getattr(defaults, f.name)}")
    return parser


def params_from_args(args: argparse.Namespace) -> SnakeParams:
    prm = SnakeParams()
    for f in fields(SnakeParams):
        if f.name == "sigmas_px":
            if args.sigmas:
                prm.sigmas_px = tuple(float(s) for s in args.sigmas.split(","))
            continue
        v = getattr(args, f.name, None)
        if v is not None:
            setattr(prm, f.name, v)
    return prm


def main() -> None:
    args = build_parser().parse_args()
    if not args.ids and not args.all:
        raise SystemExit("name at least one case id, or pass --all")
    started = time.perf_counter()
    try:
        root = _root_for(Path(args.fixtures), args.style, args.which)
    except (KeyError, OSError):
        root = None
    root_meta = announce_roots([root], args.expect_root) if root is not None else []
    try:
        cases = iter_fixture_word_cases(
            which=args.which, style=args.style, only=list(args.ids) or None, fixtures_root=args.fixtures
        )
    except (KeyError, OSError) as exc:
        raise SystemExit(f"{exc.args[0] if exc.args else exc} (or tools/wordbench/fetch_fixtures)") from None
    if not cases:
        raise SystemExit(f"no case matched {args.ids!r} in the {args.which!r} set")
    prm = params_from_args(args)
    print(f"schlange: {len(cases)} cases · set {args.which} · {json.dumps(asdict(prm))}")
    infos = run_cases(cases, prm, jobs=max(1, args.jobs))
    for info in infos:
        meta = info.get("meta") or {}
        line = [
            f"{info['specimen_id']:<12} {info['status']:<7} {meta.get('seconds')} s  cap {meta.get('hit_cap')}  flagged {len(meta.get('flagged_curves', []))}"
        ]
        for run in meta.get("runs", []):
            for c in run.get("curves", []):
                st = c["stages"]
                name = "+".join(k or "C" for _, k, _ in c["pieces"])[:28]
                line.append(
                    f"   {name:<28} nodes {st[-1]['n_nodes'] if st else 0:4d}"
                    f" iters {'/'.join(str(s['iters']) for s in st)} stop {'/'.join(s['stop'] for s in st)}"
                    f" resid {'/'.join(str(s['residual_max_px']) for s in st)} dist {'/'.join(str(s['mean_dist_px']) for s in st)}"
                    f" coh {c['coherence'].get('ratio')} corners {c['coherence'].get('ratio_corners')}"
                    f" wobble {c.get('field_wobble_px')} ripple {c.get('curve_ripple_px')}{' STRANDED' if c['stranded'] else ''}"
                )
        print("\n".join(line), flush=True)
    runtime = round(time.perf_counter() - started, 1)
    print(f"runtime {runtime}s")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "tool": SCHLANGE_TOOL_NAME,
                    "version": SCHLANGE_ARTIFACT_VERSION,
                    "style": args.style,
                    "set": args.which,
                    "roots": root_meta,
                    "weights": asdict(prm),
                    "provisional": True,
                    "runtime_s": runtime,
                    "rows": infos,
                },
                indent=1,
                ensure_ascii=False,
            )
        )
        print(f"wrote {args.json}")
    if args.candidate_out:
        payload = snake_payload(
            infos,
            style=args.style,
            source_id=_source_id_of(args.fixtures, args.style, args.which),
            which=args.which,
            label=args.label,
            prm=prm,
        )
        payload["runtime_s"] = runtime
        args.candidate_out.parent.mkdir(parents=True, exist_ok=True)
        args.candidate_out.write_text(json.dumps(payload, ensure_ascii=False))
        print(f"wrote {args.candidate_out} ({len(payload['rows'])} rows, {len(payload['excluded'])} excluded)")


__all__ = [
    "COHERENCE_LAG_PX",
    "LOOP_WORDS",
    "PLATEAU_MIN_DROP",
    "PLATEAU_WINDOW",
    "SCHLANGE_ARTIFACT_VERSION",
    "SCHLANGE_TOOL_NAME",
    "SnakeParams",
    "bending_apply",
    "bending_weights",
    "build_parser",
    "coherence_stats",
    "coverage_force",
    "cut_back",
    "ductus_order",
    "evolve_curve",
    "field_wobble",
    "follow_case",
    "metric_banded",
    "metric_dense",
    "params_from_args",
    "resample_curve",
    "run_cases",
    "run_pieces",
    "seed_curve",
    "snake_payload",
    "weld_pieces",
]


if __name__ == "__main__":
    main()
