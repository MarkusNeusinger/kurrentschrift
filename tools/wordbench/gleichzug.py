"""Report-only Gleichzug audit — the one-flow, one-width invariant.

The user's physical invariant (2026-07-30, qualitaetsmetrik.md §6 Runde
jul29/30): a Sütterlin word is written in ONE flow (pen lifts only for
diacritics/detached marks) with a line that is ALWAYS one nib wide. Two
violations are detectable on the composed centerline path alone, without any
specimen reference:

1. FLOW GAP — consecutive pen-down items must join end-to-start; a gap means
   the pen teleported. Generated strokes overlap their neighbours by
   CONNECT_OVERLAP (compose), so the tolerance sits above that.
2. PARALLEL DOUBLING — two path stretches running near-parallel at a
   separation between the retrace epsilon and ~1.35x the nib read as one
   stroke of double width, which a one-width nib cannot write. Exact
   retraces (separation below the epsilon) and transversal crossings are
   legitimate pen behaviour; near-parallel pairs INSIDE one letter are its
   authored form (letterform domain, not compose) and are classified out
   via the provenance slot tags.

Report-only: consumed by tools/wordbench/run.py as extra columns, never part
of the loss (precedent: the slant column).
"""

from __future__ import annotations

import math

import numpy as np

from core.compose import CONNECT_OVERLAP


# Continuity tolerance: CONNECT_OVERLAP extends a connector's first sample
# back INTO the previous ink, so the raw start-to-end distance of a healthy
# handoff is exactly the overlap; anything clearly above it is a real gap.
GAP_EPS = CONNECT_OVERLAP + 0.02
STEP = 0.012  # resample step along the pen path, x-height units
MIN_ARC_APART = 0.22  # closer along the path = the same stroke bending
PARALLEL_DEG = 22.0  # tangent difference below this (mod 180) = parallel
DOUBLE_MIN = 0.035  # absolute floor: closer = retrace/coincident, allowed
# Calibrated against the user-approved renders (jul30): two runs closer than
# half a nib merge into ONE smoothly swelling stroke (the ſ-hook junction —
# pen-authentic ink pooling, sep ~0.06 at nib 0.147), so the lower band edge
# scales with the nib.
DOUBLE_MIN_NIB_FACTOR = 0.5
DOUBLE_MAX_FACTOR = 1.35  # x nib width; farther = visibly separate lines
# Short side-by-side lobes are junction knots (the approved arm-fusion seams
# measure 0.17–0.22 of arc); only a LONGER double-track reads as the
# forbidden double-width stroke.
MIN_EVENT_ARC = 0.25


def _resample(points: list, step: float) -> np.ndarray:
    pts = np.asarray(points, dtype=float)
    if len(pts) < 2:
        return pts
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(s[-1])
    if total <= 0:
        return pts[:1]
    si = np.linspace(0.0, total, max(2, int(total / step) + 1))
    return np.stack([np.interp(si, s, pts[:, 0]), np.interp(si, s, pts[:, 1])], axis=1)


def audit_composed(composed: dict) -> dict:
    """Audit a compose_word(..., provenance=True) result.

    Returns {"gaps": [...], "doublings": [...], "nib": float} — one gap dict
    per flow break {x, y, dist}, one doubling dict per parallel event
    {x0, x1, y, arc, sep}. Empty lists = the invariant holds.
    """
    items = [it for it in composed["items"] if not it.get("diacritic")]
    nib = max((it.get("stroke_width", 0.15) for it in items if not it.get("rings")), default=0.15)

    gaps: list[dict] = []
    prev_end = None
    for it in items:
        cl = it["centerline"]
        if not cl:
            continue
        if prev_end is not None and not it.get("lift"):
            d = math.hypot(cl[0][0] - prev_end[0], cl[0][1] - prev_end[1])
            if d > GAP_EPS:
                gaps.append({"x": round(prev_end[0], 3), "y": round(prev_end[1], 3), "dist": round(d, 3)})
        prev_end = cl[-1]

    # Resample PER pen-down run (split at lift): concatenating across a lift
    # would interpolate phantom bridge segments that flag as doublings.
    runs: list[list] = []
    run_src: list[list] = []
    glyph_raw: list = []
    for idx, it in enumerate(items):
        pts = it["centerline"]
        if not pts:
            continue
        gen = 0 if it.get("rings") else 1
        slot = it.get("slot_index", -100 - idx)
        if it.get("lift") or not runs:
            runs.append([])
            run_src.append([])
        runs[-1].extend(pts)
        run_src[-1].extend([(slot, gen)] * len(pts))
        if not gen:
            glyph_raw.extend((tuple(p), slot) for p in pts)

    P_parts: list[np.ndarray] = []
    slot_parts: list[np.ndarray] = []
    gen_parts: list[np.ndarray] = []
    run_parts: list[np.ndarray] = []
    arc_parts: list[np.ndarray] = []
    tan_parts: list[np.ndarray] = []
    for ri, (pts, srcs) in enumerate(zip(runs, run_src, strict=True)):
        if len(pts) < 2:
            continue
        Pr = _resample(pts, STEP)
        raw = np.asarray(pts, dtype=float)
        nearest = np.argmin(np.linalg.norm(Pr[:, None, :] - raw[None, :, :], axis=2), axis=1)
        slots_r = np.asarray([s[0] for s in srcs])[nearest]
        gens_r = np.asarray([s[1] for s in srcs])[nearest]
        d = np.diff(Pr, axis=0)
        ang = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
        tan_r = np.concatenate([ang, ang[-1:]]) if len(ang) else np.zeros(len(Pr))
        P_parts.append(Pr)
        slot_parts.append(slots_r)
        gen_parts.append(gens_r)
        run_parts.append(np.full(len(Pr), ri))
        arc_parts.append(np.arange(len(Pr)) * STEP)
        tan_parts.append(tan_r)
    if not P_parts:
        return {"gaps": gaps, "doublings": [], "nib": nib}
    P = np.concatenate(P_parts)
    s_slot = np.concatenate(slot_parts)
    s_gen = np.concatenate(gen_parts)
    run_id = np.concatenate(run_parts)
    arc = np.concatenate(arc_parts)
    tangents = np.concatenate(tan_parts)
    if len(P) < 4:
        return {"gaps": gaps, "doublings": [], "nib": nib}
    # A generated sample retracing authored ink doubles its own line exactly —
    # reclassify it as that glyph's ink.
    if glyph_raw:
        G = np.asarray([p for p, _ in glyph_raw], dtype=float)
        Gslot = np.asarray([s for _, s in glyph_raw])
        dg = np.min(np.linalg.norm(P[:, None, :] - G[None, :, :], axis=2), axis=1)
        on_ink = (s_gen == 1) & (dg < DOUBLE_MIN)
        if on_ink.any():
            near_g = np.argmin(np.linalg.norm(P[on_ink][:, None, :] - G[None, :, :], axis=2), axis=1)
            s_slot[on_ink] = Gslot[near_g]
            s_gen[on_ink] = 0

    dmat = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
    tdiff = np.abs(tangents[:, None] - tangents[None, :]) % 180.0
    tdiff = np.minimum(tdiff, 180.0 - tdiff)
    # The doubling band gates on the PERPENDICULAR offset from the local
    # tangent, not the euclidean distance: two strokes riding the SAME line
    # (a retrace) have sliding pairs at every euclidean distance but ~zero
    # perpendicular offset — only a true side-by-side offset doubles the ink.
    rad = np.radians(tangents)
    dxm = P[None, :, 0] - P[:, None, 0]
    dym = P[None, :, 1] - P[:, None, 1]
    perp = np.abs(np.cos(rad)[:, None] * dym - np.sin(rad)[:, None] * dxm)
    compose_pair = (s_gen[:, None] | s_gen[None, :]).astype(bool) | (s_slot[:, None] != s_slot[None, :])
    far_apart = (run_id[:, None] != run_id[None, :]) | (np.abs(arc[:, None] - arc[None, :]) > MIN_ARC_APART)
    double_lo = max(DOUBLE_MIN, DOUBLE_MIN_NIB_FACTOR * nib)
    bad = (
        (dmat < DOUBLE_MAX_FACTOR * nib)
        & (perp > double_lo)
        & (perp < DOUBLE_MAX_FACTOR * nib)
        & far_apart
        & (tdiff < PARALLEL_DEG)
        & compose_pair
    )

    flagged = np.where(bad.any(axis=1))[0]
    events: list[tuple[int, int]] = []
    if len(flagged):
        start = prev = flagged[0]
        for i in flagged[1:]:
            if i - prev > 3:
                events.append((start, prev))
                start = i
            prev = i
        events.append((start, prev))
    doublings = []
    for a, b in events:
        if (b - a) * STEP < MIN_EVENT_ARC:
            continue
        seps = perp[a : b + 1][bad[a : b + 1]]
        doublings.append(
            {
                "x0": round(float(P[a][0]), 3),
                "x1": round(float(P[b][0]), 3),
                "y": round(float((P[a][1] + P[b][1]) / 2), 3),
                "arc": round((b - a) * STEP, 3),
                "sep": round(float(seps.mean()), 3),
            }
        )
    return {"gaps": gaps, "doublings": doublings, "nib": nib}
