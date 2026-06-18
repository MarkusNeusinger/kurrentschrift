"""Sütterlin (Gleichzug) quality metric — intrinsic naturalness, not pixel-match.

A metric *separate* from `core.quality.template_quality_metrics` (the Kurrent /
Schwellzug pixel-and-width metric), because the two scripts use different writing
instruments and so have different definitions of "looks hand-written": Kurrent is
a Spitzfeder (pressure-variable width); Sütterlin is a Redisfeder (Gleichzug,
constant width). Sharing one metric — or one bench number — would hide
regressions in both. Only genuinely identical machinery is reused (silhouette
rasterisation, the boundary chamfer, the EDT field sampler, the pure geometry
primitives in `core.geometry`).

The credo: a synthesised Sütterlin glyph should be **indistinguishable from one a
human wrote with a pen** — not pixel-identical to a pixelated scan. So the metric
is built in two tiers:

* **Coverage = a gate, not the goal.** Dice + a *dead-banded* boundary chamfer +
  a *dead-banded* centerline-to-skeleton RMSE confirm the glyph is the right
  letter in the right place. The dead-band (`DEAD_BAND_PX`) means disagreement
  within the scan's own ~1px quantisation costs nothing — sub-pixel fidelity to a
  jagged scan is neither rewarded nor punished. The three combine into a gate
  `G ∈ [0, 1]` that *multiplies* the score, so a smooth glyph in the wrong place
  cannot score well.

* **Naturalness = the discriminator (reference-free).** Measured on the rendered
  centerline alone — robust to scan pixelation by construction: curve smoothness
  (no Zacken), verticality of straight downstrokes, corner crispness, collinearity
  of a stroke through a crossing, and (v1) parallelism of a retrace's two passes.
  Each term is a 0–1 quality; the weighted mean over the *applicable* terms is `N`.

`score = 100 · G**GATE_EXPONENT · N`, `loss = 1 − score/100` — same headline keys
and 0–100 / `1−score/100` contract as the Kurrent metric, so the glyph bench reads
either generically.

Anti-gaming note (v1): the feature terms are scored only where the *render* shows
the feature, which in principle invites "hide the feature to dodge the penalty".
For Sütterlin this is defused by the derivation itself: `core.suetterlin` is
*skeleton-locked* (it snaps to the medial axis), and the coverage gate's
`Q_geo`/`Q_chamfer` punish any drift off that skeleton — so a render cannot hide a
feature the ink has without tanking the gate. A skeleton-side "presence oracle"
(zero a term when the ink has the feature but the render omits it) is the v2
hardening for a generator that is *not* skeleton-locked; deliberately deferred
(a flaky oracle would inject the scan pixelation back into the metric).

All constants below are calibration targets — tuned against the locked Sütterlin
fixtures so the metric's per-glyph ranking tracks a human naturalness ranking
(see `docs/reference/qualitaetsmetrik.md`). The terms' *direction* (more vertical
→ higher, jaggier → lower) is pinned by tests; only the magnitudes are tuned.
Everything here is deterministic: no RNG, no time.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter1d

from core.fit import bilinear
from core.geometry import (
    acute_angle_between,
    arc_length,
    detect_crossing_passages,
    detect_retrace_pairs,
    detect_vertical_runs,
    discrete_curvature,
    fit_line_tls,
    point_line_perp_distance,
    run_is_straight_residual,
    stroke_bounds,
    unit_tangents,
)
from core.quality import QUALITY_N_SAMPLES, _sample_and_rings, chamfer_boundary_stats, rasterize_silhouette


# --- naturalness weights (renormalised over the APPLICABLE terms each glyph) ---
W_SMOOTH = 0.30  # Zacken-freeness — the most universal naturalness cue, always applies
W_VERT = 0.25  # straight downstrokes truly vertical
W_CORNER = 0.20  # corner reversals crisp, not rounded
W_CROSS = 0.15  # a stroke stays collinear through a crossing
W_RETRACE = 0.10  # an out-and-back retrace's two passes stay parallel (v1)

# --- decays (each maps a non-negative penalty to a 0–1 quality via exp(−·)) ---
SMOOTH_DECAY = 0.6  # mean |Δ²κ̂| (curvature 2nd difference) per step; calibration target
SMOOTH_KAPPA_SIGMA = 2.0  # Gaussian (in samples) denoising the curvature before differencing
VERT_DECAY = 0.02  # RMS horizontal wander of a "vertical" run, in x-heights
CORNER_STRAIGHT_DECAY = 0.5  # straightness residual of a corner's two approaches (looser; clean ≈ 0.9)
CROSS_ANG_DECAY = 0.10  # rad (~5.7°) — direction mismatch across a crossing
CROSS_OFF_DECAY = 0.03  # x-heights — lateral offset of the two fitted lines
RETRACE_ANG_DECAY = 0.10  # rad — non-parallelism of the two retrace passes

# --- coverage gate (reference-anchored, with a pixelation dead-band) ---
DEAD_BAND_PX = 0.75  # boundary/centerline disagreement below this is free (scan jaggedness)
CHAMFER_DECAY_UNITS = 0.05  # matches the Kurrent metric / fit convergence tolerance
GEO_DECAY_UNITS = 0.08
GATE_EXPONENT = 0.5  # G**0.5: the gate must be decent, then naturalness drives the ranking

# --- feature-detection thresholds (mirror core.suetterlin generation) ---
VERTICAL_ANGLE_DEG = 15.0
VERTICAL_MIN_LEN_UNITS = 0.45
VERTICAL_STRAIGHT_TOL = 0.10
CORNER_WINDOW_UNITS = 0.12  # = core.pipeline.CORNER_WINDOW_UNITS
CROSS_WINDOW_UNITS = 0.35  # arc each side of a crossing used to fit the through-line
CROSS_STRAIGHT_TOL = 0.12  # an approach bowed more than this is a curved loop, not a through-line
# Applicability of the collinearity term: only where before/after genuinely look
# like ONE straight line crossed (a t-bar, ſt). Tight, because Sütterlin
# lowercase has essentially no straight-straight crossings — almost every
# detected crossing is a curved loop self-crossing (d, e, l, g, b, h), which must
# be N/A, not penalised. The term is then mostly dormant on lowercase and only
# bites a genuine through-line that kinks (its whole point: "identical line
# before and after"), incl. during Phase B generation tuning.
CROSS_APPLY_ANGLE_DEG = 10.0  # before/after beyond this angle aren't one line through → N/A
CROSS_APPLY_OFFSET_UNITS = 0.12  # …or beyond this lateral offset (x-heights) → N/A
CROSSING_MIN_ANGLE_DEG = 25.0
CROSSING_MIN_ARC_FACTOR = 3.0
RETRACE_WINDOW_UNITS = 0.20  # arc each side used to judge a retrace pass's local straightness
RETRACE_STRAIGHT_TOL = 0.12  # a pass bowed more than this is a curved loop, not an out-and-back retrace
PROX_FLOOR_UNITS = 0.10  # crossing/retrace proximity floor (x-heights)
PROX_NIB_FACTOR = 3.0  # …or this multiple of the nib radius, whichever is larger
MIN_RETRACE_PAIRS = 3  # fewer matched pairs than this is a coincidental touch, not a retrace
RETRACE_MAX_GAP_NIB = 2.5  # the two passes must be within this many nib widths (genuinely the same ink)
RETRACE_APPLY_ANGLE_DEG = 15.0  # passes diverging beyond this aren't an out-and-back retrace → N/A


def centerline_smoothness(
    sx: np.ndarray,
    sy: np.ndarray,
    sample_starts: Sequence[int] | None,
    corner_sample_idx: Sequence[int] | None,
    unit_px: float,
) -> float:
    """Quality (0–1) of curve smoothness: 1 = no Zacken, lower = jaggy.

    Measured as the mean absolute SECOND difference of the normalised curvature
    along each pen-stroke (excluding the samples at/adjacent to a within-stroke
    corner knot — those are intentional C0 reversals scored by `corner_crispness`).
    The second difference is the right Zacken detector: it is ~0 not only for a
    straight line and a constant-curvature arc but also for a *smooth* ramp
    straight→curve→straight (a legitimately flowing shoulder), and only spikes
    where the curvature oscillates — exactly the pixel-jaggedness a constant nib
    turns into visible notches. (The first difference cannot tell a smooth ramp
    from a saw-tooth; the second can.)
    """
    sx = np.asarray(sx, dtype=float)
    sy = np.asarray(sy, dtype=float)
    pts = np.column_stack([sx, sy])
    corners = {int(c) for c in (corner_sample_idx or [])}
    # Exclude a window around each corner wide enough to cover where the Gaussian
    # smear of the corner's curvature spike still dominates the 2nd difference.
    block_radius = 1 + int(np.ceil(2.0 * SMOOTH_KAPPA_SIGMA))
    total_abs, n_steps = 0.0, 0
    for a, b in stroke_bounds(len(pts), sample_starts):
        seg = pts[a:b]
        if len(seg) < 4:
            continue
        # Denoise the curvature along arc before differencing: the rendered
        # spline faithfully traces ~1px skeleton jitter into sub-visual curvature
        # wiggle the eye never reads as a Zacke. A small Gaussian (in samples)
        # removes that jitter while leaving a real notch — the analogue of the
        # coverage dead-band, in the curvature channel.
        kappa = gaussian_filter1d(discrete_curvature(seg, unit_px), SMOOTH_KAPPA_SIGMA, mode="nearest")
        block = np.zeros(len(seg), dtype=bool)
        for c in corners:
            if a <= c < b:
                lc = c - a
                block[max(0, lc - block_radius) : min(len(seg), lc + block_radius + 1)] = True
        d2 = np.abs(np.diff(kappa, n=2))  # indexed at interior points 1..len-2
        valid = ~(block[:-2] | block[1:-1] | block[2:])
        total_abs += float(d2[valid].sum())
        n_steps += int(valid.sum())
    jerk = total_abs / n_steps if n_steps else 0.0
    return float(np.exp(-jerk / SMOOTH_DECAY))


def verticality(
    sx: np.ndarray, sy: np.ndarray, sample_starts: Sequence[int] | None, unit_px: float
) -> tuple[float, int]:
    """Quality (0–1) that the rendered straight downstrokes are truly vertical.

    Returns `(quality, n_runs)`; `n_runs == 0` means no vertical run exists (the
    term is not applicable). For each detected run the residual is its RMS
    horizontal wander in x-heights; the arc-length-weighted mean residual maps
    through `exp(−R/VERT_DECAY)`.
    """
    runs = detect_vertical_runs(
        sx,
        sy,
        sample_starts,
        unit_px,
        angle_deg=VERTICAL_ANGLE_DEG,
        min_len_units=VERTICAL_MIN_LEN_UNITS,
        straight_tol=VERTICAL_STRAIGHT_TOL,
    )
    if not runs:
        return 1.0, 0
    pts = np.column_stack([np.asarray(sx, dtype=float), np.asarray(sy, dtype=float)])
    num, den = 0.0, 0.0
    for lo, hi in runs:
        seg = pts[lo : hi + 1]
        x = seg[:, 0]
        rms = float(np.sqrt(np.mean((x - x.mean()) ** 2))) / unit_px
        length = float(arc_length(seg)[-1])
        num += length * rms
        den += length
    residual = num / den if den else 0.0
    return float(np.exp(-residual / VERT_DECAY)), len(runs)


def corner_crispness(
    sx: np.ndarray,
    sy: np.ndarray,
    sample_starts: Sequence[int] | None,
    corner_sample_idx: Sequence[int] | None,
    unit_px: float,
) -> tuple[float, int]:
    """Quality (0–1) that within-stroke reversals are crisp, straight-approached corners.

    Returns `(quality, n_corners)`. A clean corner — "90° down, stop, 40° up" —
    has STRAIGHT approaches on both sides that meet at the apex; a rounded or
    wobbly reversal bows those approaches near the apex. So the score is purely
    the approach straightness `exp(−(s_in+s_out)/decay)` over a window each side.
    No absolute corner angle is targeted (the 90°/40° is letterform data); and
    apex-concentration is deliberately NOT scored — at 240 samples a true C0 kink
    still spreads its turn over a few samples, so concentration read every clean
    corner as half-rounded. Straight approaches are the robust, visible cue.
    """
    corners = [int(c) for c in (corner_sample_idx or [])]
    if not corners:
        return 1.0, 0
    pts = np.column_stack([np.asarray(sx, dtype=float), np.asarray(sy, dtype=float)])
    window_px = max(3.0, CORNER_WINDOW_UNITS * unit_px)
    bounds = stroke_bounds(len(pts), sample_starts)
    qs: list[float] = []
    for c in corners:
        owner = next(((a, b) for a, b in bounds if a <= c < b), None)
        if owner is None:
            continue
        a, b = owner
        seg = pts[a:b]
        arc = arc_length(seg)
        cl = c - a
        # Approaches EXCLUDE the apex sample itself: a sharp kink's apex is an
        # outlier to each approach line, so including it would penalise the
        # crisp corner more than a rounded one. A rounded reversal instead bows
        # the approach samples themselves → higher residual → lower quality.
        left = seg[(arc < arc[cl]) & (arc >= arc[cl] - window_px)]
        right = seg[(arc > arc[cl]) & (arc <= arc[cl] + window_px)]
        s_in = run_is_straight_residual(left) if len(left) >= 3 else 0.0
        s_out = run_is_straight_residual(right) if len(right) >= 3 else 0.0
        qs.append(float(np.exp(-(s_in + s_out) / CORNER_STRAIGHT_DECAY)))
    if not qs:
        return 1.0, 0
    return float(np.mean(qs)), len(qs)


def crossing_collinearity(
    sx: np.ndarray, sy: np.ndarray, sample_starts: Sequence[int] | None, prox_px: float, unit_px: float
) -> tuple[float, int]:
    """Quality (0–1) that a stroke stays collinear through a transversal crossing.

    Returns `(quality, n_passages)`. For each crossed stroke run, fit a TLS line
    to the through-stroke just before and just after the crossing blob (within
    `CROSS_WINDOW_UNITS` of arc each side, the blob itself blanked). The two lines
    should match in direction (acute angle `δθ`) and offset (perpendicular
    distance of one centroid from the other line, `δd` in x-heights) — exactly
    "the line equation before and after the crossing is identical".
    """
    passages = detect_crossing_passages(
        sx,
        sy,
        sample_starts,
        prox_px=prox_px,
        min_arc_factor=CROSSING_MIN_ARC_FACTOR,
        min_angle_deg=CROSSING_MIN_ANGLE_DEG,
    )
    if not passages:
        return 1.0, 0
    pts = np.column_stack([np.asarray(sx, dtype=float), np.asarray(sy, dtype=float)])
    window_px = max(3.0, CROSS_WINDOW_UNITS * unit_px)
    # The OTHER pass must be locally straight too: a genuine crossing is two
    # straight lines meeting (a t-bar, ſt), NOT a curve cutting across a loop
    # (d), a stroke turning out of a loop (e), or a loop side grazing a stem (l).
    straight = _locally_straight_mask(pts, sample_starts, max(3.0, RETRACE_WINDOW_UNITS * unit_px), CROSS_STRAIGHT_TOL)
    qs: list[float] = []
    for a, b, lo, hi, partner in passages:
        if partner < 0 or not straight[partner]:
            continue
        seg = pts[a:b]
        arc = arc_length(seg)
        before = seg[(arc < arc[lo - a]) & (arc >= arc[lo - a] - window_px)]
        after = seg[(arc > arc[hi - a]) & (arc <= arc[hi - a] + window_px)]
        if len(before) < 3 or len(after) < 3:
            continue
        # The through-stroke must be straight on BOTH sides too — "fit a line
        # before and after". A curved through-pass has no through-line and is skipped.
        if (
            run_is_straight_residual(before) > CROSS_STRAIGHT_TOL
            or run_is_straight_residual(after) > CROSS_STRAIGHT_TOL
        ):
            continue
        c1, u1 = fit_line_tls(before)
        c2, u2 = fit_line_tls(after)
        dtheta = acute_angle_between(u1, u2)
        ddist = point_line_perp_distance(c2, c1, u1) / unit_px
        # Applicability: this is only a "straight line crossed" if before and
        # after are roughly ONE line. A single-stroke loop self-crossing (d, e,
        # l, g, b) has its two sides at a large angle/offset — not a through-line,
        # so N/A (skip), not penalised. Within the through-line case, the precise
        # δθ/δd then score how cleanly the line continues.
        if dtheta > np.deg2rad(CROSS_APPLY_ANGLE_DEG) or ddist > CROSS_APPLY_OFFSET_UNITS:
            continue
        qs.append(float(np.exp(-dtheta / CROSS_ANG_DECAY)) * float(np.exp(-ddist / CROSS_OFF_DECAY)))
    if not qs:
        return 1.0, 0
    return float(np.mean(qs)), len(qs)


def _locally_straight_mask(
    pts: np.ndarray, sample_starts: Sequence[int] | None, window_px: float, tol: float
) -> np.ndarray:
    """Per-sample flag: the centerline is straight within `window_px` of arc here.

    Used to confine the crossing/retrace terms to genuinely straight passes — a
    curved loop side (the l/b/h loop, the e-eye) is neither "fit a line through a
    crossing" nor "out and back the same path", so it must not trip those terms.
    """
    n = len(pts)
    ok = np.zeros(n, dtype=bool)
    for a, b in stroke_bounds(n, sample_starts):
        seg = pts[a:b]
        if len(seg) < 3:
            continue
        arc = arc_length(seg)
        for k in range(len(seg)):
            w = (arc >= arc[k] - window_px) & (arc <= arc[k] + window_px)
            if int(w.sum()) >= 3 and run_is_straight_residual(seg[w]) <= tol:
                ok[a + k] = True
    return ok


def retrace_parallelism(
    sx: np.ndarray, sy: np.ndarray, sample_starts: Sequence[int] | None, prox_px: float, unit_px: float, r_px: float
) -> tuple[float, int]:
    """Quality (0–1) that an out-and-back retrace's two STRAIGHT passes stay parallel (v1).

    Returns `(quality, n_pairs)`. The two anti-parallel passes of an `s`/`f`/`t`
    retrace should run *parallel* — the user's "die Linien laufen auseinander"
    (the passes spread) is exactly non-parallelism, so the acute angle between a
    pass's tangent and its matched opposite tangent is the v1 signal. A pair is a
    genuine retrace only if BOTH passes are locally straight AND the two passes
    are essentially coincident — within `RETRACE_MAX_GAP_NIB` nib widths of each
    other (the pen went back over the SAME ink). That excludes a loop side merely
    grazing a stem (the l/b/h loop), which is not an out-and-back retrace. The
    Spitze (tip) sharpness and verifying the legitimate ~2× silhouette width are a
    v2 concern (they need the medial axis of the *rendered* silhouette).
    """
    idx, partner = detect_retrace_pairs(
        sx,
        sy,
        sample_starts,
        prox_px=prox_px,
        min_arc_factor=CROSSING_MIN_ARC_FACTOR,
        max_angle_deg=CROSSING_MIN_ANGLE_DEG,
    )
    if len(idx) < MIN_RETRACE_PAIRS:
        return 1.0, 0
    pts = np.column_stack([np.asarray(sx, dtype=float), np.asarray(sy, dtype=float)])
    straight = _locally_straight_mask(
        pts, sample_starts, max(3.0, RETRACE_WINDOW_UNITS * unit_px), RETRACE_STRAIGHT_TOL
    )
    gaps = np.hypot(*(pts[idx] - pts[partner]).T)
    keep = straight[idx] & straight[partner] & (gaps <= RETRACE_MAX_GAP_NIB * max(r_px, 1e-6))
    idx, partner = idx[keep], partner[keep]
    if len(idx) < MIN_RETRACE_PAIRS:
        return 1.0, 0
    tang = np.zeros((len(pts), 2))
    for a, b in stroke_bounds(len(pts), sample_starts):
        if b - a >= 2:
            tang[a:b] = unit_tangents(pts[a:b])
    angles = np.array([acute_angle_between(tang[i], tang[j]) for i, j in zip(idx, partner, strict=True)])
    # Applicability: a genuine retrace's passes are roughly parallel to begin
    # with. Pairs beyond RETRACE_APPLY_ANGLE are a loop side merely grazing a
    # stem (l/b/h), not an out-and-back — drop them; if too few remain, N/A.
    apply = angles <= np.deg2rad(RETRACE_APPLY_ANGLE_DEG)
    if int(apply.sum()) < MIN_RETRACE_PAIRS:
        return 1.0, 0
    return float(np.exp(-float(np.mean(angles[apply])) / RETRACE_ANG_DECAY)), int(apply.sum())


def suetterlin_quality_metrics(
    anchors_px: np.ndarray,
    half_widths_px: np.ndarray,
    stroke_starts: Sequence[int] | None,
    mask: np.ndarray,
    skel: np.ndarray,
    width_map: np.ndarray,
    *,
    unit_px: float,
    corner_anchors: Sequence[int] | None = None,
    n: int = QUALITY_N_SAMPLES,
) -> dict:
    """Score a Sütterlin template (crop-local px anchors + constant half-width).

    Renders the silhouette exactly like the diagnostic (per-stroke capsule union
    at `n` samples), then combines a tolerant coverage gate against the binarized
    crop with the reference-free naturalness terms. Returns a flat dict: the
    aggregate `score` (0–100) / `loss`, a `components` sub-dict of 0–1 penalties
    (1 − quality, so 0 = perfect; non-applicable feature terms read 0), the
    raw coverage diagnostics, and per-term applicability counts. `width_map` is
    unused (Gleichzug width is a single constant) but kept in the signature so the
    bench can call either metric with the same arguments.
    """
    anchors_px = np.asarray(anchors_px, dtype=float)
    half_widths_px = np.asarray(half_widths_px, dtype=float)
    if len(anchors_px) < 2:
        raise ValueError("need at least 2 anchors to render a silhouette")
    if unit_px <= 0:
        raise ValueError(f"unit_px must be positive, got {unit_px}")

    h, w = mask.shape
    worst_px = float(np.hypot(h, w))

    sx, sy, _sw, sample_starts, corner_sample_idx, stroke_rings = _sample_and_rings(
        anchors_px, half_widths_px, stroke_starts, n, corner_anchors
    )
    pred_mask = rasterize_silhouette(stroke_rings, (h, w))

    # --- coverage gate (tolerant: a pixelation dead-band absorbs scan jaggedness) ---
    intersection = int(np.logical_and(pred_mask, mask).sum())
    union = int(np.logical_or(pred_mask, mask).sum())
    area_sum = int(pred_mask.sum()) + int(mask.sum())
    iou = intersection / union if union else 1.0
    dice = 2.0 * intersection / area_sum if area_sum else 1.0

    chamfer = chamfer_boundary_stats(pred_mask, mask, dead_band_px=DEAD_BAND_PX)
    if skel.any():
        d_skel = bilinear(distance_transform_edt(~skel), sx, sy)
        geo_db_rmse = float(np.sqrt(np.mean(np.maximum(0.0, d_skel - DEAD_BAND_PX) ** 2)))
    else:
        geo_db_rmse = worst_px

    q_chamfer = float(np.exp(-chamfer["chamfer_mean_px"] / (CHAMFER_DECAY_UNITS * unit_px)))
    q_geo = float(np.exp(-geo_db_rmse / (GEO_DECAY_UNITS * unit_px)))
    gate = dice * q_chamfer * q_geo

    # --- naturalness (reference-free, on the rendered centerline) ---
    r_px = float(np.median(half_widths_px)) if len(half_widths_px) else 1.0
    prox_px = max(PROX_NIB_FACTOR * r_px, PROX_FLOOR_UNITS * unit_px)

    q_smooth = centerline_smoothness(sx, sy, sample_starts, corner_sample_idx, unit_px)
    q_vert, n_vert = verticality(sx, sy, sample_starts, unit_px)
    q_corner, n_corner = corner_crispness(sx, sy, sample_starts, corner_sample_idx, unit_px)
    q_cross, n_cross = crossing_collinearity(sx, sy, sample_starts, prox_px, unit_px)
    q_retrace, n_retrace = retrace_parallelism(sx, sy, sample_starts, prox_px, unit_px, r_px)

    applicable = [(W_SMOOTH, q_smooth)]
    if n_vert:
        applicable.append((W_VERT, q_vert))
    if n_corner:
        applicable.append((W_CORNER, q_corner))
    if n_cross:
        applicable.append((W_CROSS, q_cross))
    if n_retrace:
        applicable.append((W_RETRACE, q_retrace))
    naturalness = sum(weight * q for weight, q in applicable) / sum(weight for weight, _ in applicable)

    score = 100.0 * (gate**GATE_EXPONENT) * naturalness
    return {
        "iou": round(iou, 4),
        "dice": round(dice, 4),
        **chamfer,
        "geo_db_rmse_px": round(geo_db_rmse, 3),
        "gate": round(gate, 4),
        "naturalness": round(naturalness, 4),
        "components": {
            "smoothness": round(1.0 - q_smooth, 4),
            "verticality": round(1.0 - q_vert, 4),
            "corner": round(1.0 - q_corner, 4),
            "collinearity": round(1.0 - q_cross, 4),
            "retrace": round(1.0 - q_retrace, 4),
            "coverage": round(1.0 - gate, 4),
            "naturalness": round(1.0 - naturalness, 4),
        },
        "applicable": {
            "vertical_runs": int(n_vert),
            "corners": int(n_corner),
            "crossings": int(n_cross),
            "retrace_pairs": int(n_retrace),
        },
        "pred_area_px": int(pred_mask.sum()),
        "ink_area_px": int(mask.sum()),
        "score": round(score, 2),
        "loss": round(1.0 - score / 100.0, 6),
        "n_samples": int(n),
    }
