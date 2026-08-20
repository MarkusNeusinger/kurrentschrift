"""The pilot walk: composed map -> skeleton-graph ride -> pen strokes.

The algorithm, stated once:

1. THE MAP. `tools.wordlab.derive.derive_word` composes the word exactly as
   production would and the row's fitted registration places it over the crop
   (`x_px = u*xh + tx`, `y_px = baseline_row - v*xh + ty` — the same transform
   the metric and the wordlab overlay use). Composed items are walked in
   writing order; items joined without a pen lift concatenate into one map
   stroke, `lift: true` starts the next one. Deferred marks arrive as their
   own strokes, exactly where the engine writes them.

2. THE WATERWAY. `tools.routeg.graph.build_graph` turns the frozen skeleton
   into nodes (endpoints, junctions) and edges (ordered pixel chains) — the
   same graph the prior-free control walks. Every skeleton pixel knows its
   edge and index, and a KD-tree answers "which ridge points lie near this
   map sample".

3. THE RIDE. Each map stroke is resampled to a regular step and projected
   onto the skeleton with CONTINUITY: among the ridge points near a sample,
   the pilot picks the one cheapest to reach from its previous position
   ALONG THE GRAPH (graph distance + deviation from the map sample), then
   walks the connecting pixel chain. Junction decisions therefore fall out
   of the map's own route — "links oder rechts" is answered by where the
   composed path goes next. Edges may be walked twice (a retrace is the
   same channel ridden again). Where no ridge lies within reach (hairline
   break, a connector the ink never wrote), the pilot BRIDGES with the
   map's own points and re-boards the skeleton when ink returns.

Measurement only. The output is a tracebench file-provider candidate in the
stored `word_instances` frame.
"""

from __future__ import annotations

import heapq
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from core.geometry import detect_retrace_pairs
from tools.routeg.graph import SkeletonGraph, build_graph
from tools.tracebench.counters import crossing_points
from tools.wordlab.cases import WordCase
from tools.wordlab.derive import WordDeriveResult, derive_word


# Map sampling step and boarding radius, in x-heights. The step is finer than
# any structure the counters see (0.35 xh arc separation); the radius must
# reach the right rail even where the composed map runs an arcade narrow
# (the P1 drift find: arcades alias by up to ~1 xh) — the global ride below,
# not the radius, is what keeps the pilot off the WRONG rail.
SAMPLE_STEP_UNITS = 0.12
BOARD_RADIUS_UNITS = 0.6
MAX_CANDIDATES = 14
# Ride prices for the global (Viterbi) assignment: graph travel per pixel,
# deviation per pixel of distance map-sample -> ridge point, and the bridge
# state priced so that riding within the radius always beats bridging, while
# a detour around the block (ride far above the direct hop) does not.
RIDE_WEIGHT = 1.0
DEVIATION_WEIGHT = 2.0
BRIDGE_EMIT_FACTOR = 2.5  # x radius, the bridge state's per-sample price
MAX_RIDE_FACTOR = 8.0  # rides above this x step are treated as unreachable
# A5, the offset double pass (v0.2 arm, pre-registered): every ride point on a
# skeleton pixel the WORD rides more than once shifts by this fraction of the
# local EDT half-width to the RIGHT of its travel direction — opposite-running
# passes separate onto opposite sides (the hand's sign convention), single
# passes and bridges stay mid-ink. 0.0 = off. Measured-and-rejected aug16
# (near-parallel offset lines never cross transversally); kept declared.
DOUBLE_PASS_OFFSET_FRACTION = 0.0
# The junction chord (v0.3 arm, pre-registered): every maximal run of ride
# points inside a branch node's neighbourhood (radius = this fraction of the
# local EDT half-width) is replaced by the straight chord of its boundary
# points — the pen went straight through where the skeleton's shared rail
# forces a corner, and two passes from different direction pairs cross
# transversally where their chords intersect. Runs longer than
# JUNCTION_CHORD_MAX_ARC_FACTOR x radius merely skirt the node and stay.
# 0.0 = off.
JUNCTION_CHORD_RADIUS_FRACTION = 0.0
JUNCTION_CHORD_MAX_ARC_FACTOR = 4.0
# Map right-of-way in double-pass zones (v0.4 arm, pre-registered): where the
# MAP retraces itself the skeleton rail is degenerate (it merges the hand's
# two passes over the whole overlap) while the composed map carries the
# crossing — there the ride takes the map itself (bridge state forced),
# everywhere else nothing changes. Zones come from the frozen ruler's own
# retrace detector, read on the map samples.
MAP_PRIORITY_IN_RETRACE = False
MAP_RETRACE_PROX_UNITS = 0.15  # the ruler's own proximity (core.geometry)
# Rail run-out (pre-registered; owner find "the d line stops at the
# crossing"): when a ride stroke ends on a rail that runs WITHOUT branching
# into a degree-1 skeleton endpoint closer than this (in x-heights), the ride
# continues to the rail's end — the map undershoots the inked tip (loop-exit
# trim, the +7-10% reach find), the ink does not. Symmetric at stroke starts.
# 0.0 = off. ADOPTED aug16 at 1.0 (dev: dtw median 0.119 -> 0.101, the und
# outlier 0.343 -> 0.087, aiou up, spurious marks halved, structure untouched).
TAIL_RUNOUT_MAX_UNITS = 1.0
# v0.5 (pre-registered): map geometry in RIDE-side double zones — a sample
# whose assigned rail pixel is already occupied by an EARLIER pass of the
# word rides the MAP instead (the skeleton merged the hand's two passes
# there; the composed map carries the crossing). The first pass keeps the
# ink's mid-line, every later one takes the composed geometry. Re-occupation
# within the same pass (dense samples on one pixel) does not count.
# ADOPTED aug16 (dev: dtw 0.101 -> 0.085, und 0.087 -> 0.043 — now beating
# the chain there —, 5 of 23 missing crossings return, arc ratio 2.48 ->
# 1.66, aiou -0.002).
RIDE_DOUBLE_MAP_PRIORITY = True
RIDE_DOUBLE_MIN_GAP = 4  # samples between visits before it counts as a pass
# v0.7 (pre-registered, L1 of the aug17 round): widen each v0.5-triggered
# sample's map right-of-way to its neighbours within this arc distance (in
# x-heights, along the sample chain of the same stroke). At a junction pinch
# the later pass re-occupies only 1-3 corridor pixels, so v0.5 rides the map
# for 1-2 samples — too narrow to turn the two tangential merges into a
# transversal crossing. The trigger stays; its EFFECT becomes a zone. 0.0 = off.
# ADOPTED aug17 at 0.35 (dev-19: cross missing 31 -> 27, net defects 35 -> 32,
# retrace-arc gap 0.285 -> 0.044, touch 41 -> 38 at dtw +0.0008 / aiou -0.014 —
# all gates pass; 0.7 rejected by the aiou kill). Honest miss: the recovered
# crossings are the POINT-pinch subclass; the loop class (the up-pass boards
# the merged rail AT crossing height, so no pixel is ever re-occupied there)
# stays and is the v0.8 arm's target.
RIDE_DOUBLE_ZONE_MARGIN_UNITS = 0.35
# v0.8 (pre-registered, L1b): map right-of-way around the MAP's own
# self-intersections. The loop class of missing crossings is not a double
# occupancy — the ride REPLACES the map's self-crossing with a tangential
# board-hop onto the merged rail, so no occupancy trigger can see it. The map
# HAS the crossing (the soll is ductus-deterministic and its self-intersections
# are computable): map samples of BOTH involved passes within this arc window
# (in x-heights) of a self-intersection ride the map (bridge state forced in
# the Viterbi — the v0.4 geometry with the right trigger). 0.0 = off.
# Measured-and-rejected aug17 as RAW map geometry (structure lands completely:
# net crossing defects 32 -> 4, dtw median under the chain — but the map's
# local offset to the ink breaches the aiou kill). ADOPTED aug17 at 0.35 in
# the PINNED v0.9 form below (dev-19: net crossing defects 32 -> 7, dtw
# median 0.0858 -> 0.0578 — level with the chain, paired Δ-median -24 % —,
# p90 0.118 vs chain 0.236, aiou -0.0142 within the kill; 0.6 rejected by
# the aiou kill at -0.039). The residual defects are soll-vs-hand
# disagreements (Galoppieren's p loops missing from the composition itself,
# linken/mit-2 soll crossings this hand does not write), not ride failures.
MAP_CROSSING_WINDOW_UNITS = 0.35
# v0.9 (pre-registered, L1c): pin each forced-window run onto the ink. The
# window's map sub-polyline is shifted as a whole so its ends meet the
# neighbouring boarding points of the ride (linearly interpolated offset
# between the two end offsets; a run at a stroke end uses its one available
# offset as a constant). Topology and crossing angle stay the map's, the
# POSITION comes from the ink — the doctrine applied to the window itself.
# Natural bridges (missing ink) and the adopted v0.5/v0.7 zones are untouched.
MAP_CROSSING_PIN = True
# Same-stroke arc floor for a MAP self-intersection: two chords closer than
# this along the chain meet at a polyline corner, not a crossing. Mirrors the
# counters' 0.35-xh arc rule (`tools/pairlab/landmarks.py::
# LANDMARK_MIN_ARC_SEPARATION_UNITS`) as a SNAPSHOT — deliberately not
# imported, so a dated ruler re-baseline cannot silently move an adopted
# candidate mechanism.
MAP_CROSSING_MIN_ARC_UNITS = 0.35
# v0.6 (pre-registered): the smoothing pass over the 8-connected pixel
# zigzag — per iteration the local mean (1, 2, 1) / 4 over each stroke with
# FIXED endpoints. Structure is a GATE, not code: the bench counters must
# stay byte-identical or the arm is rejected. 0 = off.
SMOOTH_ITERATIONS = 0
# v0.13 (pre-registered, L1g): pairwise untwisting of weave duplicates. The
# duplicate-X sites are WEAVES — several intersection events of the same
# pass pair inside a small window (3/5/6 raw events where the hand crosses
# 1/1/0 times), so removal must be PAIRWISE to keep the parity (the v0.12
# chord removed all of them and the crossing with it). A pair = two events
# whose arc gaps on BOTH sides are <= this window (in xh) and whose crossing
# points lie within half of it; the WIGGLE arc between the pair's parameters
# (the side with the larger chord deviation — the pre-reg precision pinned
# by the unit test) is MIRRORED across the chord P1->P2 — both crossings of
# the pair vanish, direction and parametrisation stay, the geometry stays
# within the wiggle's own amplitude. Iterated to a fixed cap, count logged.
# ADOPTED aug19 at 0.5 (dev-19: net crossing defects 7 -> 6, will's
# duplicate heals, everything else within gates); 0.8 rejected by its own
# kill (it untwists genuinely close REAL pairs — mit's t double at 0.07 xh).
# The remaining duplicates need the soll-budgeted discriminator (§7.9).
UNTWIST_WINDOW_UNITS = 0.5
UNTWIST_MAX_PASSES = 8
# v0.15 (pre-registered, L1h): the soll-budgeted untwist. Geometry alone
# cannot tell a weave duplicate from a genuinely close REAL pair, but the
# MAP knows its own self-intersections — a pair may only untwist where the
# neighbourhood does not fall BELOW its soll afterwards
# (n_events_near - 2 >= n_soll_near, counted in the fixed matcher-radius
# snapshot below). mit's t double (soll 2) is protected by construction;
# the weaves (soll 0-1, events 3-6) fall pairwise. False = v0.13 behaviour.
# v0.16 (L1i): the soll SOURCE is the RULER's own crossing detector on the
# map (pierce filter, arc floor, merge) — the aug20 autopsy found the raw
# segment enumeration double-counts every map crossing (will 10 raw vs 4
# counted), which is exactly v0.15's false veto at will. ADOPTED aug20 with
# the "bridges" stage (dev-19: counter-identical to the v0.13 base at every
# site, mit's retrace heals, and the budget is free on "windows").
UNTWIST_SOLL_BUDGET = True
UNTWIST_SOLL_RADIUS_UNITS = 0.55  # the ruler's matcher radius, as a snapshot
# v0.17 (pre-registered, L1j): the RESERVATION veto — the standing §7.9
# rescue (position matching instead of the count). The radius COUNT inherits
# event inflation in dense neighbourhoods (the 0.8-window kill at unter
# fired with n_events - 2 >= n_soll although the pair carried real
# crossings), and a per-pair matched-count DELTA fails the same site as a
# commons problem: with 12 events over 1 soll every single removal is
# covered by a substitute, the cascade still empties the site (matched
# 2 -> ... -> 0, the aug20 unter dump). "reserve" therefore matches the
# ruler soll to the events one-to-one ONCE per pass; a reserved event is
# unpairable — the map knows that crossing, it is untouchable.
# "radius" = the v0.15/v0.16 count. ADOPTED aug20 per the pre-declared
# parity rule: dev-19 counter-identical to v0.16 on both roots (every
# gate PASS), the protective class pinned by the unit test, fewer
# needless mirrors (Galoppieren 15 -> 11).
UNTWIST_SOLL_MATCHING = "reserve"
# v0.10 (pre-registered, L1d): junction-anchored pinning of map runs. The
# owner's visual find (the k curl untraced, the W riding air) autopsied to
# MERGED crossing windows — where map self-intersections sit densely the
# +-0.35-xh windows chain into runs of up to 4.3 xh, and the v0.9 end-only
# interpolation passes the raw (locally offset) map form through their
# middle — plus the still-raw v0.5/v0.7 zone rides and natural bridges.
# The generalisation: every map run is pinned over an offset polyline whose
# KNOTS are the run boundaries (the v0.9 math, unchanged) PLUS one anchor
# per map self-intersection inside the run — offset = nearest skeleton
# BRANCH node (within PIN_KNOT_NODE_RADIUS_UNITS) minus the intersection
# point; linear between knots, constant beyond the outermost, raw without
# any. "off" = v0.9 · "windows" = knot pinning for the forced crossing
# windows only · "all" = the same for double-zone rides and bridges too ·
# v0.16 selective stages (L1i): "bridges" = every natural bridge, "zones"
# = the forced windows plus the double-zone rides; the stages overlap
# where a widened zone reaches into a bridge, and bridges UNION zones =
# all.
# v0.10 (raw point knots) measured-and-rejected aug19: the point field
# shears at the crossings it anchors. ADOPTED aug19 as v0.11 "windows"
# (plateau field below): dev-19 net crossing defects 7 (= v0.9) with the
# missing class healed to 1 (Galoppieren's two composition-missing p
# crossings return), crossing position error 0.116 -> 0.066 xh, aiou
# +0.008, p90 0.118 -> 0.113; "all" rejected (net 8 — one duplicate X
# beyond the gate). ADOPTED aug20 as v0.16 "bridges" (with the ruler-soll
# budget below): structure counter-identical to the v0.13/LF3b base at
# every site, pure ink gains (p90 0.1129 -> 0.1122, chamfer 0.0410 ->
# 0.0404, four words -0.0035..-0.0059 dtw, no loser); "zones"/"all" fail
# their net gate by exactly the Galoppieren p osculation (+1 spurious,
# placement family) while the budget keeps the G head X — re-submission
# after the p placement arm (tintenfolger.md §7.9).
MAP_RUN_PIN_KNOTS = "bridges"
PIN_KNOT_NODE_RADIUS_UNITS = 1.0  # fixed anchor search radius, not a ladder knob
# v0.11 (pre-registered, L1e): each anchor offset acts as a rigid PLATEAU of
# this half-width (in xh) instead of a point knot — a crossing survives a
# locally constant offset field exactly (both passes translate equally, the X
# moves rigidly), while v0.10's point knots sheared the field at the crossing
# itself (merge/osculation in dense clusters, the measured aug19 negative).
# Overlapping plateaus fuse into one interval carrying the mean of their
# anchor offsets; interpolation continues between plateaus and run
# boundaries. 0.0 = point knots (the rejected v0.10 field).
PIN_KNOT_PLATEAU_UNITS = 0.35
# v0.12 (pre-registered, L1f): the plateau chord. 4 of v0.11's 6 spurious
# crossings are DOUBLE-X duplicates — a pinned window pass wiggles through
# the node neighbourhood and cuts the other pass twice. Inside every fused
# plateau interval each pass's sub-path is replaced by its CHORD (interior
# samples linear between the interval's own boundary samples): two chords
# cross at most once, so the duplicate is constructively impossible. Unlike
# the rejected v0.3 junction chord this straightens only MAP geometry that
# already sits in a rigid plateau (deviation bounded by the plateau width);
# rail rides are untouched. False = the v0.11 field.
PIN_PLATEAU_CHORD = False


@dataclass(frozen=True)
class PixelLoc:
    """One skeleton pixel as (edge index, index along the edge's chain)."""

    edge: int
    index: int


class PilotGraph:
    """The skeleton graph plus everything the ride needs precomputed."""

    def __init__(self, skel: np.ndarray) -> None:
        self.graph: SkeletonGraph = build_graph(skel)
        coords: list[tuple[float, float]] = []
        locs: list[PixelLoc] = []
        for ei, edge in enumerate(self.graph.edges):
            for pi, (x, y) in enumerate(np.asarray(edge.points, dtype=float)):
                coords.append((x, y))  # edge.points is already (x, y) crop px
                locs.append(PixelLoc(ei, pi))
        self.coords = np.asarray(coords, dtype=float).reshape(-1, 2)
        self.locs = locs
        self.tree = cKDTree(self.coords) if len(self.coords) else None
        self._node_dist_cache: dict[int, dict[int, float]] = {}

    # ------------------------------------------------------------- geometry
    def px_of(self, loc: PixelLoc) -> np.ndarray:
        x, y = self.graph.edges[loc.edge].points[loc.index]
        return np.asarray([float(x), float(y)])

    def _edge_len(self, ei: int) -> int:
        return len(self.graph.edges[ei].points)

    # ------------------------------------------------------- graph distance
    def _node_dists(self, start: int) -> dict[int, float]:
        """Dijkstra over nodes, edge length = pixel count (cached per node)."""
        hit = self._node_dist_cache.get(start)
        if hit is not None:
            return hit
        dist = {start: 0.0}
        heap = [(0.0, start)]
        adj: dict[int, list[tuple[int, float]]] = {}
        for edge in self.graph.edges:
            n = float(len(edge.points))
            adj.setdefault(edge.a, []).append((edge.b, n))
            adj.setdefault(edge.b, []).append((edge.a, n))
        while heap:
            d, node = heapq.heappop(heap)
            if d > dist.get(node, float("inf")):
                continue
            for other, n in adj.get(node, ()):
                nd = d + n
                if nd < dist.get(other, float("inf")):
                    dist[other] = nd
                    heapq.heappush(heap, (nd, other))
        self._node_dist_cache[start] = dist
        return dist

    def ride_cost(self, a: PixelLoc, b: PixelLoc) -> float:
        """Approximate pixel count of the cheapest skeleton walk a -> b."""
        if a.edge == b.edge:
            return float(abs(a.index - b.index))
        ea, eb = self.graph.edges[a.edge], self.graph.edges[b.edge]
        best = float("inf")
        for node_a, off_a in ((ea.a, a.index), (ea.b, self._edge_len(a.edge) - 1 - a.index)):
            dists = self._node_dists(node_a)
            for node_b, off_b in ((eb.a, b.index), (eb.b, self._edge_len(b.edge) - 1 - b.index)):
                d = dists.get(node_b)
                if d is not None:
                    best = min(best, off_a + d + off_b)
        return best

    def ride(self, a: PixelLoc, b: PixelLoc) -> list[np.ndarray]:
        """The pixel chain of the cheapest walk a -> b (endpoints included)."""
        if a.edge == b.edge:
            pts = np.asarray(self.graph.edges[a.edge].points, dtype=float)
            lo, hi = sorted((a.index, b.index))
            seg = pts[lo : hi + 1]
            if a.index > b.index:
                seg = seg[::-1]
            return [np.asarray(p) for p in seg]
        # Route through the best node pair, then splice the partial edges and
        # the node-to-node walk (re-derived edge by edge along predecessor-free
        # Dijkstra: cheap because the per-word graphs are tens of nodes).
        ea, eb = self.graph.edges[a.edge], self.graph.edges[b.edge]
        best: tuple[float, int, int] | None = None
        for node_a, off_a in ((ea.a, a.index), (ea.b, self._edge_len(a.edge) - 1 - a.index)):
            dists = self._node_dists(node_a)
            for node_b, off_b in ((eb.a, b.index), (eb.b, self._edge_len(b.edge) - 1 - b.index)):
                d = dists.get(node_b)
                if d is not None and (best is None or off_a + d + off_b < best[0]):
                    best = (off_a + d + off_b, node_a, node_b)
        if best is None:
            return [self.px_of(a), self.px_of(b)]
        _, node_a, node_b = best
        out = self._partial(a, node_a)
        out.extend(self._node_walk(node_a, node_b)[1:])
        tail = self._partial(b, node_b)
        out.extend(reversed(tail[:-1]))
        out.append(self.px_of(b))
        return out

    def _partial(self, loc: PixelLoc, node: int) -> list[np.ndarray]:
        """Pixels from `loc` to the chosen end node of its edge (inclusive)."""
        edge = self.graph.edges[loc.edge]
        pts = np.asarray(edge.points, dtype=float)
        seg = pts[: loc.index + 1][::-1] if node == edge.a else pts[loc.index :]
        return [np.asarray(p) for p in seg]

    def _node_walk(self, start: int, goal: int) -> list[np.ndarray]:
        """Pixel chain of the shortest node-to-node walk (Dijkstra + path)."""
        if start == goal:
            return [self._node_px(start)]
        adj: dict[int, list[tuple[int, int, float]]] = {}
        for ei, edge in enumerate(self.graph.edges):
            n = float(len(edge.points))
            adj.setdefault(edge.a, []).append((edge.b, ei, n))
            adj.setdefault(edge.b, []).append((edge.a, ei, n))
        dist = {start: 0.0}
        prev: dict[int, tuple[int, int]] = {}
        heap = [(0.0, start)]
        while heap:
            d, node = heapq.heappop(heap)
            if node == goal:
                break
            if d > dist.get(node, float("inf")):
                continue
            for other, ei, n in adj.get(node, ()):
                nd = d + n
                if nd < dist.get(other, float("inf")):
                    dist[other] = nd
                    prev[other] = (node, ei)
                    heapq.heappush(heap, (nd, other))
        if goal not in prev:
            return [self._node_px(start), self._node_px(goal)]
        hops: list[tuple[int, int]] = []
        node = goal
        while node != start:
            parent, ei = prev[node]
            hops.append((parent, ei))
            node = parent
        out = [self._node_px(start)]
        for parent, ei in reversed(hops):
            edge = self.graph.edges[ei]
            pts = np.asarray(edge.points, dtype=float)
            seg = pts if edge.a == parent else pts[::-1]
            out.extend(np.asarray(p) for p in seg[1:])
        return out

    def _node_px(self, node: int) -> np.ndarray:
        x, y = self.graph.nodes[node]
        return np.asarray([float(x), float(y)])


# ------------------------------------------------------------------ the map


def map_strokes_px(result: WordDeriveResult) -> list[np.ndarray]:
    """The composed word as pen strokes in crop px, in writing order."""
    reg = result.registration
    xh = float(reg.get("xh_px", result.xh_px))
    tx = float(reg.get("tx", 0.0))
    ty = float(reg.get("ty", 0.0))
    base = float(result.baseline_row)

    def to_px(pts: list) -> np.ndarray:
        a = np.asarray(pts, dtype=float).reshape(-1, 2)
        out = np.empty_like(a)
        out[:, 0] = a[:, 0] * xh + tx
        out[:, 1] = base - a[:, 1] * xh + ty
        return out

    strokes: list[np.ndarray] = []
    current: list[np.ndarray] = []
    for item in result.composed["items"]:
        pts = to_px(item.get("centerline") or [])
        if len(pts) < 2:
            continue
        if item.get("lift") and current:
            strokes.append(np.vstack(current))
            current = []
        current.append(pts)
    if current:
        strokes.append(np.vstack(current))
    return strokes


def resample(stroke: np.ndarray, step_px: float) -> np.ndarray:
    seg = np.hypot(*np.diff(stroke, axis=0).T)
    arc = np.concatenate([[0.0], np.cumsum(seg)])
    if arc[-1] <= step_px:
        return stroke[[0, -1]]
    targets = np.arange(0.0, arc[-1] + step_px / 2, step_px)
    xs = np.interp(targets, arc, stroke[:, 0])
    ys = np.interp(targets, arc, stroke[:, 1])
    return np.column_stack([xs, ys])


def _segment_intersections(a: np.ndarray, b: np.ndarray, min_sep: int | None) -> list[tuple[int, int]]:
    """Index pairs (i, j) where segment a[i:i+2] properly crosses b[j:j+2].

    Proper crossing only (both parameters strictly inside), so shared sample
    points of consecutive segments never count. `min_sep` — for the
    same-stroke case — additionally drops pairs closer than that many samples
    along the chain: neighbouring segments of one polyline meet at their
    joint, which is a corner, not a self-crossing.
    """
    if len(a) < 2 or len(b) < 2:
        return []
    p, r = a[:-1], a[1:] - a[:-1]
    q, s = b[:-1], b[1:] - b[:-1]
    rxs = r[:, None, 0] * s[None, :, 1] - r[:, None, 1] * s[None, :, 0]
    qp = q[None, :, :] - p[:, None, :]
    qpxr = qp[..., 0] * r[:, None, 1] - qp[..., 1] * r[:, None, 0]
    qpxs = qp[..., 0] * s[None, :, 1] - qp[..., 1] * s[None, :, 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        t = qpxs / rxs
        u = qpxr / rxs
    hit = (np.abs(rxs) > 1e-12) & (t > 0.0) & (t < 1.0) & (u > 0.0) & (u < 1.0)
    ij = np.argwhere(hit)
    if min_sep is not None and len(ij):
        ij = ij[np.abs(ij[:, 0] - ij[:, 1]) >= min_sep]
    return [(int(i), int(j)) for i, j in ij]


def map_crossing_masks(samples_per_stroke: list[np.ndarray], window_units: float) -> list[np.ndarray]:
    """v0.8: per-stroke masks of samples near a MAP self-intersection.

    Both passes through each self-crossing of the composed map get map
    right-of-way for `window_units` of arc to either side, so the ride draws
    the map's own X instead of board-hopping onto the merged rail. The
    same-stroke separation floor mirrors the counters' 0.35-xh arc rule — a
    polyline corner is not a crossing.
    """
    masks = [np.zeros(len(s), dtype=bool) for s in samples_per_stroke]
    reach = int(round(window_units / SAMPLE_STEP_UNITS))
    min_sep = max(2, int(round(MAP_CROSSING_MIN_ARC_UNITS / SAMPLE_STEP_UNITS)))
    for ai in range(len(samples_per_stroke)):
        for bi in range(ai, len(samples_per_stroke)):
            pairs = _segment_intersections(
                samples_per_stroke[ai], samples_per_stroke[bi], min_sep if ai == bi else None
            )
            for i, j in pairs:
                masks[ai][max(0, i - reach) : i + reach + 2] = True
                masks[bi][max(0, j - reach) : j + reach + 2] = True
    return masks


# ----------------------------------------------------------------- the ride


def _assign_stroke(
    pg: PilotGraph,
    stroke_px: np.ndarray,
    xh_px: float,
    samples: np.ndarray | None = None,
    forced_priority: np.ndarray | None = None,
) -> tuple[np.ndarray, list[PixelLoc | None], np.ndarray]:
    """The GLOBAL sample->ridge assignment of one map stroke.

    Returns `(samples, seq, forced)`: the (possibly trimmed) samples, their
    per-sample assignment (`PixelLoc` or `None` for the bridge state), and the
    equally trimmed v0.8 forced-window mask so the caller can pin exactly
    those runs (`_pin_forced_runs`).

    Solved as a Viterbi over the sample chain: a greedy walk boards the first
    plausible rail and then cascades — on the composed m, whose arcade runs
    narrower than the ink's, it boarded the wrong rail and bridged across the
    counters (the „mit" finding of the first inspection page). States per
    sample are the nearby ridge points plus one BRIDGE state; transitions
    price the graph ride, emissions the deviation from the map. Leading and
    trailing bridge runs that never re-board are TRIMMED — ink that does not
    exist (a composed run-out over blank paper) is not a pen stroke.
    """
    if samples is None:
        samples = resample(stroke_px, SAMPLE_STEP_UNITS * xh_px)
    radius = BOARD_RADIUS_UNITS * xh_px
    max_ride = MAX_RIDE_FACTOR * SAMPLE_STEP_UNITS * xh_px
    bridge_emit = BRIDGE_EMIT_FACTOR * radius
    n = len(samples)

    # v0.4 map right-of-way: samples inside the MAP's own retrace zones ride
    # the map (bridge state forced) — the rail is degenerate there, the map
    # carries the crossing. Zones from the frozen ruler's own detector.
    # v0.8 adds `forced_priority`: samples near a MAP self-intersection ride
    # the map too (the loop class of the missing crossings — the ride's
    # board-hop otherwise replaces the map's X with a tangential merge).
    map_priority = np.zeros(n, dtype=bool)
    if MAP_PRIORITY_IN_RETRACE and n >= 4:
        ia, ib = detect_retrace_pairs(samples[:, 0], samples[:, 1], None, prox_px=MAP_RETRACE_PROX_UNITS * xh_px)
        for arr in (ia, ib):
            map_priority[np.asarray(arr, dtype=int)] = True
    forced = np.zeros(n, dtype=bool)
    if forced_priority is not None:
        forced = np.asarray(forced_priority, dtype=bool)[:n].copy()
        map_priority |= forced

    # States per sample: [(loc | None for bridge, emission cost), ...]
    states: list[list[tuple[PixelLoc | None, float]]] = []
    for k, s in enumerate(samples):
        if map_priority[k]:
            states.append([(None, 0.0)])
            continue
        idx = pg.tree.query_ball_point(s, r=radius) if pg.tree is not None else []
        if len(idx) > MAX_CANDIDATES:
            idx = sorted(idx, key=lambda i: float(np.hypot(*(pg.coords[i] - s))))[:MAX_CANDIDATES]
        row: list[tuple[PixelLoc | None, float]] = [
            (pg.locs[i], DEVIATION_WEIGHT * float(np.hypot(*(pg.coords[i] - s)))) for i in idx
        ]
        row.append((None, bridge_emit))
        states.append(row)

    # Viterbi over the chain. Transition loc->loc = the graph ride (capped);
    # any transition into or out of the bridge state is free — its price sits
    # entirely in the emission, so long bridges cost per sample, not per hop.
    INF = float("inf")
    cost = [e for _, e in states[0]]
    back: list[list[int]] = []
    for k in range(1, n):
        row = states[k]
        prev_row = states[k - 1]
        new_cost = [INF] * len(row)
        new_back = [0] * len(row)
        for j, (loc, emit) in enumerate(row):
            best, arg = INF, 0
            for i, (ploc, _) in enumerate(prev_row):
                if cost[i] >= INF:
                    continue
                if loc is None or ploc is None:
                    trans = 0.0
                else:
                    ride = pg.ride_cost(ploc, loc)
                    if ride > max_ride:
                        continue
                    trans = RIDE_WEIGHT * ride
                c = cost[i] + trans
                if c < best:
                    best, arg = c, i
            new_cost[j] = best + emit if best < INF else INF
            new_back[j] = arg
        cost, back = new_cost, back + [new_back]

    # Backtrack to the state sequence.
    j = int(np.argmin(cost))
    seq: list[PixelLoc | None] = [states[-1][j][0]]
    for k in range(n - 1, 0, -1):
        j = back[k - 1][j]
        seq.append(states[k - 1][j][0])
    seq.reverse()

    # Trim bridge runs at the ends that never (re)board — forced map-priority
    # samples count as boarded (the map IS the ride there, not missing ink).
    def rides(k: int) -> bool:
        return seq[k] is not None or bool(map_priority[k])

    first = next((k for k in range(len(seq)) if rides(k)), None)
    if first is None:
        return samples, [None] * len(samples), forced  # pure bridge: no ink under the map
    last = max(k for k in range(len(seq)) if rides(k))
    return samples[first : last + 1], seq[first : last + 1], forced[first : last + 1]


def _assemble_ride(
    pg: PilotGraph, samples: np.ndarray, seq: list[PixelLoc | None], map_mask: np.ndarray | None = None
) -> np.ndarray:
    """Assembled pen stroke: rails between assignments, map points elsewhere.

    ``map_mask`` marks samples that ride the MAP regardless of their rail
    assignment (the v0.5 double-zone right-of-way).
    """
    out: list[np.ndarray] = []
    prev: PixelLoc | None = None
    for k, (s, loc) in enumerate(zip(samples, seq, strict=True)):
        if loc is None or (map_mask is not None and map_mask[k]):
            out.append(s)
            prev = None
            continue
        if prev is None:
            out.append(pg.px_of(loc))
        else:
            out.extend(pg.ride(prev, loc)[1:])
        prev = loc
    pts = np.asarray(out, dtype=float).reshape(-1, 2)
    keep = np.ones(len(pts), dtype=bool)
    keep[1:] = np.hypot(*np.diff(pts, axis=0).T) > 1e-9
    return pts[keep]


def _pin_forced_runs(pg: PilotGraph, samples: np.ndarray, seq: list[PixelLoc | None], forced: np.ndarray) -> np.ndarray:
    """v0.9: shift each forced-window run so its ends meet the boarding points.

    The window keeps the map's topology and crossing angle; its POSITION comes
    from the ink — the offset between the run's boundary map samples and their
    neighbouring rail assignments is interpolated linearly across the run. A
    run bordered by a natural bridge inherits a zero offset on that side, a
    run at a stroke end uses its one available offset as a constant, and a
    stroke that is forced in its entirety stays raw.
    """
    if not MAP_CROSSING_PIN or not bool(forced.any()):
        return samples
    out = samples.astype(float).copy()
    n = len(samples)
    k = 0
    while k < n:
        if not (forced[k] and seq[k] is None):
            k += 1
            continue
        end = k
        while end + 1 < n and forced[end + 1] and seq[end + 1] is None:
            end += 1
        d_a = d_b = None
        if k > 0:
            d_a = (pg.px_of(seq[k - 1]) - samples[k - 1]) if seq[k - 1] is not None else np.zeros(2)
        if end + 1 < n:
            d_b = (pg.px_of(seq[end + 1]) - samples[end + 1]) if seq[end + 1] is not None else np.zeros(2)
        if d_a is None and d_b is None:
            k = end + 1
            continue
        if d_a is None:
            d_a = d_b
        if d_b is None:
            d_b = d_a
        span = float((end + 1) - (k - 1))
        for i in range(k, end + 1):
            t = (i - (k - 1)) / span
            out[i] = samples[i] + (1.0 - t) * d_a + t * d_b
        k = end + 1
    return out


def pin_run_mask(stage: str, bridge: np.ndarray, forced: np.ndarray, zone: np.ndarray) -> np.ndarray:
    """The samples one pinning stage covers (v0.10/v0.16 stage semantics).

    "windows" pins only the forced crossing windows on bridges; "bridges"
    every natural bridge; "zones" the forced windows plus the double-zone
    rides. The two selective stages deliberately overlap where the widened
    double zone reaches into a bridge — their UNION is exactly "all", their
    difference is which run segmentation those samples fall into.
    """
    if stage == "windows":
        return bridge & forced
    if stage == "bridges":
        return bridge.copy()
    if stage == "zones":
        return (bridge & forced) | zone
    if stage == "all":
        return bridge | zone
    raise ValueError(f"unknown pin stage {stage!r}")


def map_crossing_knots(
    pg: PilotGraph, samples_per_stroke: list[np.ndarray], xh_px: float
) -> list[list[tuple[int, np.ndarray]]]:
    """v0.10: one anchor knot per map self-intersection, per stroke.

    For every self-intersection of the (unpinned) map samples the nearest
    skeleton BRANCH node within PIN_KNOT_NODE_RADIUS_UNITS names where the ink
    itself puts that crossing; the knot's offset moves the intersection point
    onto the node. Both involved passes receive the same anchor, so the map's
    X lands on the ink's junction constructively. Intersections without a
    branch node in reach contribute no knot (the boundary interpolation of
    `_pin_map_runs` covers them, which is exactly the v0.9 behaviour).

    v0.11's declared plateau semantics ("a dense cluster shifts rigidly as a
    whole") is GLOBAL across passes: anchors whose plateaus chain-overlap
    along any stroke form one cluster, and every member carries the cluster's
    mean offset — two crossing passes therefore translate equally and their X
    survives exactly. The clustering happens here (union-find over anchor
    identities, which the per-stroke view of `_pin_map_runs` cannot see).
    """
    branch = [n for n in range(len(pg.graph.nodes)) if len(pg.graph.incident.get(n, [])) >= 3]
    centers = np.asarray([pg.graph.nodes[n] for n in branch], dtype=float).reshape(-1, 2)
    if not len(centers):
        return [[] for _ in samples_per_stroke]
    radius = PIN_KNOT_NODE_RADIUS_UNITS * xh_px
    min_sep = max(2, int(round(MAP_CROSSING_MIN_ARC_UNITS / SAMPLE_STEP_UNITS)))
    offsets: list[np.ndarray] = []  # per anchor id
    placements: list[list[tuple[int, int]]] = [[] for _ in samples_per_stroke]  # (index, anchor_id)
    for ai in range(len(samples_per_stroke)):
        for bi in range(ai, len(samples_per_stroke)):
            a, b = samples_per_stroke[ai], samples_per_stroke[bi]
            for i, j in _segment_intersections(a, b, min_sep if ai == bi else None):
                pt = _intersection_point(a[i], a[i + 1], b[j], b[j + 1])
                d = np.hypot(centers[:, 0] - pt[0], centers[:, 1] - pt[1])
                best = int(np.argmin(d))
                if float(d[best]) > radius:
                    continue
                anchor_id = len(offsets)
                offsets.append(centers[best] - pt)
                placements[ai].append((i, anchor_id))
                placements[bi].append((j, anchor_id))
    if not offsets:
        return [[] for _ in samples_per_stroke]
    # Union-find over anchors whose plateaus chain-overlap along any stroke.
    parent = list(range(len(offsets)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    reach = PIN_KNOT_PLATEAU_UNITS / SAMPLE_STEP_UNITS if PIN_KNOT_PLATEAU_UNITS > 0.0 else 0.0
    for per in placements:
        per.sort()
        for (i_a, id_a), (i_b, id_b) in zip(per, per[1:], strict=False):
            if i_b - i_a <= 2 * reach:
                parent[find(id_a)] = find(id_b)
    clusters: dict[int, list[int]] = {}
    for anchor_id in range(len(offsets)):
        clusters.setdefault(find(anchor_id), []).append(anchor_id)
    fused = {root: np.mean(np.asarray([offsets[m] for m in members]), axis=0) for root, members in clusters.items()}
    out: list[list[tuple[int, np.ndarray]]] = []
    for per in placements:
        seen: dict[int, np.ndarray] = {}
        for i, anchor_id in per:
            seen.setdefault(i, fused[find(anchor_id)])
        out.append(sorted(seen.items()))
    return out


def _intersection_point(p0: np.ndarray, p1: np.ndarray, q0: np.ndarray, q1: np.ndarray) -> np.ndarray:
    """The proper intersection of two segments (midpoint fallback if parallel)."""
    r, s = p1 - p0, q1 - q0
    rxs = float(r[0] * s[1] - r[1] * s[0])
    if abs(rxs) < 1e-12:
        return (p0 + p1 + q0 + q1) / 4.0
    qp = q0 - p0
    t = float(qp[0] * s[1] - qp[1] * s[0]) / rxs
    return p0 + t * r


def _pin_map_runs(
    pg: PilotGraph,
    samples: np.ndarray,
    seq: list[PixelLoc | None],
    run_mask: np.ndarray,
    knots: list[tuple[int, np.ndarray]],
) -> np.ndarray:
    """v0.10: pin every masked map run over its offset-knot polyline.

    Knots per run: the neighbouring boarding points (a bridge neighbour
    contributes a zero offset, exactly as v0.9's `_pin_forced_runs`) plus the
    junction anchors of `map_crossing_knots` that fall inside the run. Linear
    interpolation between consecutive knots, constant beyond the outermost;
    a run without any knot stays raw.
    """
    if not bool(run_mask.any()):
        return samples
    out = samples.astype(float).copy()
    n = len(samples)
    k = 0
    while k < n:
        if not run_mask[k]:
            k += 1
            continue
        end = k
        while end + 1 < n and run_mask[end + 1]:
            end += 1
        pts: list[tuple[float, np.ndarray]] = []
        if k > 0:
            d_a = (pg.px_of(seq[k - 1]) - samples[k - 1]) if seq[k - 1] is not None else np.zeros(2)
            pts.append((float(k - 1), d_a))
        anchors = [(float(i), off) for i, off in knots if k <= i <= end]
        plateaus: list[tuple[float, float, list[np.ndarray]]] = []
        if PIN_KNOT_PLATEAU_UNITS > 0.0 and anchors:
            # v0.11: rigid plateaus — constant offset over +-plateau around
            # each anchor, overlapping plateaus fused to one interval with
            # the mean of their anchors' offsets, clipped to the run.
            reach = PIN_KNOT_PLATEAU_UNITS / SAMPLE_STEP_UNITS
            for i, off in anchors:
                lo, hi = max(float(k), i - reach), min(float(end), i + reach)
                if plateaus and lo <= plateaus[-1][1]:
                    prev_lo, prev_hi, offs = plateaus[-1]
                    plateaus[-1] = (prev_lo, max(prev_hi, hi), [*offs, off])
                else:
                    plateaus.append((lo, hi, [off]))
            for lo, hi, offs in plateaus:
                mean = np.mean(np.asarray(offs), axis=0)
                pts.append((lo, mean))
                if hi > lo:
                    pts.append((hi, mean))
        else:
            pts.extend(anchors)
        if end + 1 < n:
            d_b = (pg.px_of(seq[end + 1]) - samples[end + 1]) if seq[end + 1] is not None else np.zeros(2)
            pts.append((float(end + 1), d_b))
        if pts:
            pts.sort(key=lambda p: p[0])
            xs = np.asarray([p[0] for p in pts])
            offs = np.asarray([p[1] for p in pts]).reshape(-1, 2)
            idx = np.arange(k, end + 1, dtype=float)
            out[k : end + 1, 0] = samples[k : end + 1, 0] + np.interp(idx, xs, offs[:, 0])
            out[k : end + 1, 1] = samples[k : end + 1, 1] + np.interp(idx, xs, offs[:, 1])
            if PIN_PLATEAU_CHORD:
                # v0.12: straighten each pass's sub-path inside a fused
                # plateau to its chord — two chords cross at most once.
                for lo, hi, _ in plateaus:
                    lo_i, hi_i = int(np.ceil(lo)), int(np.floor(hi))
                    if hi_i - lo_i >= 2:
                        t = np.linspace(0.0, 1.0, hi_i - lo_i + 1)[:, None]
                        out[lo_i : hi_i + 1] = (1.0 - t) * out[lo_i] + t * out[hi_i]
        k = end + 1
    return out


def pilot_stroke(pg: PilotGraph, stroke_px: np.ndarray, xh_px: float) -> np.ndarray:
    """One map stroke ridden along the skeleton (assignment + assembly)."""
    samples, seq, forced = _assign_stroke(pg, stroke_px, xh_px)
    samples = _pin_forced_runs(pg, samples, seq, forced)
    return _assemble_ride(pg, samples, seq)


def offset_double_passes(strokes: list[np.ndarray], width_map: np.ndarray, fraction: float) -> list[np.ndarray]:
    """A5: shift multiply-ridden skeleton pixels off the shared rail.

    Ride points ARE skeleton pixels (integer coordinates), so provenance is a
    coordinate lookup; bridge points (fractional map samples) never match and
    stay untouched. Every point whose pixel the whole WORD visits more than
    once moves by ``fraction`` of the local EDT half-width to the RIGHT of its
    travel direction — opposite-running passes land on opposite flanks of the
    stroke and cross transversally where the hand's two passes do.
    """
    if fraction <= 0.0:
        return strokes
    visits: dict[tuple[int, int], int] = {}
    keys_per_stroke: list[list[tuple[int, int] | None]] = []
    h, w = width_map.shape
    for pts in strokes:
        keys: list[tuple[int, int] | None] = []
        for x, y in pts:
            xi, yi = int(round(x)), int(round(y))
            on_skel = abs(x - xi) < 1e-6 and abs(y - yi) < 1e-6 and 0 <= yi < h and 0 <= xi < w
            key = (xi, yi) if on_skel else None
            keys.append(key)
            if key is not None:
                visits[key] = visits.get(key, 0) + 1
        keys_per_stroke.append(keys)
    out: list[np.ndarray] = []
    for pts, keys in zip(strokes, keys_per_stroke, strict=True):
        shifted = pts.astype(float).copy()
        if len(pts) >= 2:
            tangents = np.gradient(pts.astype(float), axis=0)
            norms = np.hypot(tangents[:, 0], tangents[:, 1])
            norms[norms == 0] = 1.0
            tangents /= norms[:, None]
            for k, key in enumerate(keys):
                if key is None or visits.get(key, 0) < 2:
                    continue
                half = float(width_map[key[1], key[0]])
                dx, dy = tangents[k]
                # Right of travel in image coordinates (y down): (-dy, dx).
                shifted[k, 0] += -dy * fraction * half
                shifted[k, 1] += dx * fraction * half
        out.append(shifted)
    return out


def cut_junction_chords(
    strokes: list[np.ndarray], pg: PilotGraph, width_map: np.ndarray, fraction: float
) -> list[np.ndarray]:
    """v0.3: straighten every branch-node passage to its entry->exit chord.

    Branch nodes (>= 3 incident edges) collapse the ink's crossing region onto
    one shared rail with a forced corner; the pen went straight through. Every
    maximal run of ride points within ``fraction`` x local half-width of such a
    node is replaced by the straight chord of its boundary points — short runs
    only (a stroke that merely skirts the node keeps its curve), and two
    passes from different direction pairs regain their transversal crossing
    where the chords intersect.
    """
    if fraction <= 0.0:
        return strokes
    branch_nodes = [n for n in range(len(pg.graph.nodes)) if len(pg.graph.incident.get(n, [])) >= 3]
    if not branch_nodes:
        return strokes
    h, w = width_map.shape
    centers = np.asarray([pg.graph.nodes[n] for n in branch_nodes], dtype=float)  # (x, y)
    radii = np.empty(len(branch_nodes))
    for i, (x, y) in enumerate(centers):
        xi, yi = int(round(x)), int(round(y))
        half = float(width_map[yi, xi]) if 0 <= yi < h and 0 <= xi < w else 1.5
        radii[i] = max(1.5, fraction * half)
    out: list[np.ndarray] = []
    for pts in strokes:
        d = np.hypot(pts[:, None, 0] - centers[None, :, 0], pts[:, None, 1] - centers[None, :, 1])
        near = (d <= radii[None, :]).any(axis=1)
        keep = np.ones(len(pts), dtype=bool)
        k = 0
        while k < len(pts):
            if not near[k]:
                k += 1
                continue
            j = k
            while j < len(pts) and near[j]:
                j += 1
            # Run k..j-1 sits inside a node neighbourhood. Replace its interior
            # by the chord (drop the interior points) when the run is short.
            run = pts[k:j]
            arc = float(np.hypot(*np.diff(run, axis=0).T).sum()) if len(run) > 1 else 0.0
            r_here = float(radii[np.argmin(d[k])])
            if 0 < k and j < len(pts) and arc <= JUNCTION_CHORD_MAX_ARC_FACTOR * r_here:
                keep[k:j] = False
            k = j
        out.append(pts[keep] if keep.sum() >= 2 else pts)
    return out


def run_out_tails(strokes: list[np.ndarray], pg: PilotGraph, xh_px: float, max_units: float) -> list[np.ndarray]:
    """Owner-find arm: continue a ride to the rail's inked end.

    The map undershoots the inked tip (the loop-exit trim, the +7-10% reach
    find), so a ride stroke can stop mid-rail while the ink runs on. When the
    stroke's end sits on a rail that reaches a DEGREE-1 skeleton endpoint
    without branching, closer than ``max_units`` x-heights, the ride continues
    to the rail's end. Symmetric at stroke starts (via reversal). A degree-1
    run-out can neither cross nor retrace — structure is untouched by
    construction.
    """
    if max_units <= 0.0:
        return strokes
    by_px: dict[tuple[int, int], list[PixelLoc]] = {}
    for coord, loc in zip(pg.coords, pg.locs, strict=True):
        by_px.setdefault((int(round(coord[0])), int(round(coord[1]))), []).append(loc)
    max_px = max_units * xh_px

    def key_of(pt: np.ndarray) -> tuple[int, int]:
        return (int(round(float(pt[0]))), int(round(float(pt[1]))))

    def extend_end(pts: np.ndarray) -> np.ndarray:
        if len(pts) < 2:
            return pts
        locs = by_px.get(key_of(pts[-1]))
        if not locs:
            return pts
        travel = pts[-1] - pts[-2]
        best: np.ndarray | None = None
        best_arc = 0.0
        for loc in locs:
            edge = pg.graph.edges[loc.edge]
            chain = np.asarray(edge.points, dtype=float)
            for rest, node in ((chain[loc.index + 1 :], edge.b), (chain[: loc.index][::-1], edge.a)):
                if len(rest) == 0 or len(pg.graph.incident.get(node, [])) != 1:
                    continue
                step = rest[0] - pts[-1]
                if float(step @ travel) <= 0.0:
                    continue  # that side runs backwards against the stroke
                arc = float(np.hypot(*np.diff(np.vstack([pts[-1:], rest]), axis=0).T).sum())
                if arc <= max_px and arc > best_arc:
                    best, best_arc = rest, arc
        return np.vstack([pts, best]) if best is not None else pts

    out = []
    for pts in strokes:
        pts = extend_end(pts)
        pts = extend_end(pts[::-1])[::-1]
        out.append(pts)
    return out


def _chain_intersections(pts: np.ndarray, min_arc_px: float, arc: np.ndarray) -> list[tuple[int, int, np.ndarray]]:
    """Proper self-intersections of one point chain: `(i, j, point)` with i < j.

    Pairs closer than `min_arc_px` ALONG the chain are polyline corners, not
    crossings — the counters' own same-stroke floor, applied in arc length so
    the mixed sampling density of rail and map stretches cannot bias it.
    """
    p = pts[:-1]
    r = pts[1:] - pts[:-1]
    out: list[tuple[int, int, np.ndarray]] = []
    n = len(p)
    for i in range(n):
        rxs = r[i, 0] * r[:, 1] - r[i, 1] * r[:, 0]
        qp = p - p[i]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (qp[:, 0] * r[:, 1] - qp[:, 1] * r[:, 0]) / rxs
            u = (qp[:, 0] * r[i, 1] - qp[:, 1] * r[i, 0]) / rxs
        ok = (np.abs(rxs) > 1e-12) & (t > 0.0) & (t < 1.0) & (u > 0.0) & (u < 1.0)
        ok[: i + 1] = False  # each pair once, i < j
        for j in np.flatnonzero(ok):
            if arc[j] - arc[i] < min_arc_px:
                continue
            out.append((i, int(j), p[i] + t[j] * r[i]))
    return out


def map_self_intersections(samples_per_stroke: list[np.ndarray], xh_px: float) -> np.ndarray:
    """The RULER's crossing population of the composed map, in crop px.

    v0.16: the soll source of the untwist budget is the frozen crossing
    detector itself (`crossing_points`: pierce filter, arc floor, merge) on
    the xh-scaled map — the raw segment enumeration double-counts every map
    crossing (~2x, the aug20 autopsy), which was exactly v0.15's false veto.
    """
    scaled = [np.asarray(s, dtype=float) / xh_px for s in samples_per_stroke]
    pts = crossing_points(scaled)
    return np.asarray(pts, dtype=float).reshape(-1, 2) * xh_px


def _greedy_soll_reserved(points: list[np.ndarray], soll: np.ndarray, radius_px: float) -> set[int]:
    """Indices of the event points a one-to-one soll match reserves.

    Nearest-first greedy at the ruler's matcher radius — the same semantics
    the ruler's own matcher uses. The v0.17 reservation veto makes these
    events unpairable for the untwist.
    """
    if not points or not len(soll):
        return set()
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    d = np.linalg.norm(pts[:, None, :] - soll[None, :, :], axis=2)
    order = np.dstack(np.unravel_index(np.argsort(d, axis=None), d.shape))[0]
    used_p: set[int] = set()
    used_s: set[int] = set()
    for pi, si in order:
        if d[pi, si] > radius_px:
            break
        if int(pi) in used_p or int(si) in used_s:
            continue
        used_p.add(int(pi))
        used_s.add(int(si))
    return used_p


def untwist_strokes(
    strokes: list[np.ndarray], xh_px: float, window_units: float, soll_points: np.ndarray | None = None
) -> tuple[list[np.ndarray], int]:
    """v0.13: remove weave duplicates pairwise by mirroring the wiggle arc.

    Two intersection events form a pair when both their arc gaps are within
    the window and their crossing points within half of it — genuinely
    separate crossings (the l loops, a full x-height apart) never qualify.
    THE WIGGLE — the side with the larger maximal chord deviation (the
    pre-reg precision pinned by the unit test) — is mirrored across the
    chord P1->P2: both crossings of the pair vanish, the parity of the site
    is preserved (3 -> 1, 5 -> 1, 6 -> 0), direction stays untouched. A
    wiggle spanning a pen lift is left alone — a mirror across strokes would
    invent pen travel.

    v0.15 (`soll_points`, with `UNTWIST_SOLL_BUDGET`): the MAP's own
    self-intersections budget every neighbourhood — a pair may only untwist
    when `n_events_near - 2 >= n_soll_near` in the fixed matcher-radius
    snapshot, so a genuinely close REAL pair (mit's t double, soll 2) is
    protected by construction while the weaves (soll 0-1) fall pairwise.
    v0.17 (`UNTWIST_SOLL_MATCHING = "reserve"`): the soll is matched to the
    events one-to-one once per pass and the matched events are unpairable —
    a per-pair count (radius or delta) dissolves in dense event clusters,
    where every single removal finds a substitute (the aug20 unter dump).
    """
    if window_units <= 0.0 or not strokes:
        return strokes, 0
    window_px = window_units * xh_px
    soll = None
    if UNTWIST_SOLL_BUDGET and soll_points is not None:
        soll = np.asarray(soll_points, dtype=float).reshape(-1, 2)
    soll_radius_px = UNTWIST_SOLL_RADIUS_UNITS * xh_px
    lengths = [len(s) for s in strokes]
    bounds = np.cumsum([0, *lengths])
    pts = np.vstack(strokes).astype(float)
    total = 0
    for _ in range(UNTWIST_MAX_PASSES):
        seg = np.vstack([np.zeros((1, 2)), np.diff(pts, axis=0)])
        arc = np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))
        events = _chain_intersections(pts, MAP_CROSSING_MIN_ARC_UNITS * xh_px, arc)
        # Cross-stroke "intersections" of the concatenated chain via the
        # virtual lift segment are impossible here: each stroke keeps its own
        # rows, and a segment index on a boundary row belongs to the lift —
        # exclude it.
        lift_rows = {int(b) - 1 for b in bounds[1:-1]}
        events = [e for e in events if e[0] not in lift_rows and e[1] not in lift_rows]
        events.sort(key=lambda e: (e[0], e[1]))
        reserved: set[int] = set()
        if soll is not None and UNTWIST_SOLL_MATCHING == "reserve":
            # v0.17: one-to-one soll match once per pass; reserved events are
            # unpairable — the map knows those crossings.
            reserved = _greedy_soll_reserved([pe for _, _, pe in events], soll, soll_radius_px)
        fixed_any = False
        used: set[int] = set()
        dirty: list[tuple[int, int]] = []  # mirrored point ranges of THIS pass
        for a in range(len(events)):
            if a in used or a in reserved:
                continue
            i1, j1, p1 = events[a]
            if any(lo_ - 1 <= s <= hi_ for s in (i1, j1) for lo_, hi_ in dirty):
                continue
            best = None
            for b in range(a + 1, len(events)):
                if b in used or b in reserved:
                    continue
                i2, j2, p2 = events[b]
                if any(lo_ - 1 <= s <= hi_ for s in (i2, j2) for lo_, hi_ in dirty):
                    continue
                if abs(arc[i2] - arc[i1]) > window_px or abs(arc[j2] - arc[j1]) > window_px:
                    continue
                if float(np.hypot(*(p2 - p1))) > window_px / 2.0:
                    continue
                if soll is not None and UNTWIST_SOLL_MATCHING != "reserve":
                    # v0.15 budget: never untwist a neighbourhood below its
                    # soll. Events and soll crossings counted around the
                    # pair's midpoint in the fixed matcher radius. (Under
                    # "reserve" the reservation above IS the veto.)
                    mid = (p1 + p2) / 2.0
                    n_events = sum(1 for _, _, pe in events if float(np.hypot(*(pe - mid))) <= soll_radius_px)
                    n_soll = int(np.sum(np.hypot(soll[:, 0] - mid[0], soll[:, 1] - mid[1]) <= soll_radius_px))
                    if n_events - 2 < n_soll:
                        continue
                best = b
                break
            if best is None:
                continue
            i2, j2, p2 = events[best]
            # The two candidate wiggles, as half-open index ranges of points
            # strictly between the pair's segments; the VALID one (non-empty,
            # within one pen stroke) with the larger chord deviation is
            # mirrored — see the wiggle selection below.
            chord = p2 - p1
            norm = float(np.hypot(*chord))
            if norm < 1e-9:
                continue
            d = chord / norm
            # THE WIGGLE is the side with the larger maximal chord deviation
            # (pre-reg precision, pinned by the unit test: the chord-side
            # counterpart has arc ~ chord length, so an arc-length pick is
            # degenerate and its mirror a no-op). A side without measurable
            # deviation is never the wiggle.
            sides = []
            for lo_, hi_ in ((min(i1, i2) + 1, max(i1, i2) + 1), (min(j1, j2) + 1, max(j1, j2) + 1)):
                if hi_ <= lo_:
                    continue
                stroke_of = np.searchsorted(bounds, [lo_, hi_ - 1], side="right")
                if stroke_of[0] != stroke_of[1]:
                    continue  # the wiggle spans a pen lift
                rel_ = pts[lo_:hi_] - p1
                dev = float(np.max(np.abs(rel_[:, 0] * d[1] - rel_[:, 1] * d[0]), initial=0.0))
                if dev > 1e-6:
                    sides.append((dev, lo_, hi_))
            if not sides:
                continue
            _, lo, hi = max(sides)
            rel = pts[lo:hi] - p1
            along = rel @ d
            across = rel - np.outer(along, d)
            pts[lo:hi] = p1 + np.outer(along, d) - across  # the mirror
            used.update((a, best))
            dirty.append((lo, hi))
            total += 1
            fixed_any = True
        if not fixed_any:
            break
    if not total:
        return strokes, 0
    return [pts[bounds[k] : bounds[k + 1]] for k in range(len(strokes))], total


def smooth_strokes(strokes: list[np.ndarray], iterations: int) -> list[np.ndarray]:
    """v0.6: iterations of the (1, 2, 1)/4 local mean, endpoints fixed."""
    if iterations <= 0:
        return strokes
    out = []
    for pts in strokes:
        p = pts.astype(float).copy()
        for _ in range(iterations):
            if len(p) < 3:
                break
            p[1:-1] = (p[:-2] + 2.0 * p[1:-1] + p[2:]) / 4.0
        out.append(p)
    return out


def pilot_word(case: WordCase) -> tuple[list[np.ndarray], dict]:
    """All strokes of one word, plus provenance details for the record."""
    result = derive_word(case)
    pg = PilotGraph(np.asarray(case.skel, dtype=bool))
    xh_px = float(result.registration.get("xh_px", result.xh_px))
    maps = map_strokes_px(result)
    samples_per = [resample(s, SAMPLE_STEP_UNITS * xh_px) for s in maps]
    if MAP_CROSSING_WINDOW_UNITS > 0.0:
        forced = map_crossing_masks(samples_per, MAP_CROSSING_WINDOW_UNITS)
    else:
        forced = [None] * len(maps)
    raw_assignments = [
        _assign_stroke(pg, s, xh_px, samples=sp, forced_priority=f)
        for s, sp, f in zip(maps, samples_per, forced, strict=True)
    ]
    masks: list[np.ndarray] | None = None
    if RIDE_DOUBLE_MAP_PRIORITY:
        # Word-global double detection in WRITING order: the first pass of a
        # rail pixel keeps the rail, every later pass rides the map.
        seen: dict[tuple[int, int], int] = {}
        # The counter is a WRITING-ORDER clock, deliberately ticking on every
        # sample including bridges: a pen that leaves a pixel — even over a
        # gap in the ink — and comes back has made a second pass; only dense
        # consecutive samples parked on one pixel are the same visit.
        counter = 0
        masks = []
        for samples, seq, _ in raw_assignments:
            mask = np.zeros(len(samples), dtype=bool)
            for k, loc in enumerate(seq):
                counter += 1
                if loc is None:
                    continue
                px = pg.px_of(loc)
                key = (int(round(px[0])), int(round(px[1])))
                last = seen.get(key)
                if last is not None and counter - last > RIDE_DOUBLE_MIN_GAP:
                    mask[k] = True
                else:
                    seen[key] = counter
            masks.append(mask)
        if RIDE_DOUBLE_ZONE_MARGIN_UNITS > 0.0:
            # v0.7 zone widening: dilate each stroke's mask along its sample
            # chain. Samples are equally spaced at SAMPLE_STEP_UNITS, so the
            # margin converts to a fixed sample radius.
            reach = int(round(RIDE_DOUBLE_ZONE_MARGIN_UNITS / SAMPLE_STEP_UNITS))
            widened: list[np.ndarray] = []
            for mask in masks:
                out = mask.copy()
                for k in np.flatnonzero(mask):
                    lo = max(0, k - reach)
                    out[lo : k + reach + 1] = True
                widened.append(out)
            masks = widened
    if MAP_RUN_PIN_KNOTS == "off":
        assignments = [
            (_pin_forced_runs(pg, samples, seq, forced_mask), seq) for samples, seq, forced_mask in raw_assignments
        ]
    else:
        # v0.10: knot pinning — junction anchors from the UNPINNED samples,
        # then one generalized pinning pass per mode ("windows" pins the
        # forced crossing windows with interior knots; "all" additionally
        # pins the double-zone rides and the natural bridges).
        knot_rows = map_crossing_knots(pg, [samples for samples, _, _ in raw_assignments], xh_px)
        assignments = []
        for si, (samples, seq, forced_mask) in enumerate(raw_assignments):
            bridge = np.asarray([loc is None for loc in seq], dtype=bool)
            zone = masks[si] if masks is not None else np.zeros(len(samples), dtype=bool)
            run_mask = pin_run_mask(MAP_RUN_PIN_KNOTS, bridge, np.asarray(forced_mask, dtype=bool), zone)
            assignments.append((_pin_map_runs(pg, samples, seq, run_mask, knot_rows[si]), seq))
    if masks is not None:
        strokes = [
            _assemble_ride(pg, samples, seq, mask) for (samples, seq), mask in zip(assignments, masks, strict=True)
        ]
    else:
        strokes = [_assemble_ride(pg, samples, seq) for samples, seq in assignments]
    strokes = [s for s in strokes if len(s) >= 2]
    if TAIL_RUNOUT_MAX_UNITS > 0.0:
        strokes = run_out_tails(strokes, pg, xh_px, TAIL_RUNOUT_MAX_UNITS)
    if JUNCTION_CHORD_RADIUS_FRACTION > 0.0 and case.width_map is not None:
        strokes = cut_junction_chords(
            strokes, pg, np.asarray(case.width_map, dtype=float), JUNCTION_CHORD_RADIUS_FRACTION
        )
    if DOUBLE_PASS_OFFSET_FRACTION > 0.0 and case.width_map is not None:
        strokes = offset_double_passes(strokes, np.asarray(case.width_map, dtype=float), DOUBLE_PASS_OFFSET_FRACTION)
    if SMOOTH_ITERATIONS > 0:
        strokes = smooth_strokes(strokes, SMOOTH_ITERATIONS)
    untwisted = 0
    if UNTWIST_WINDOW_UNITS > 0.0:
        soll_pts = map_self_intersections(samples_per, xh_px) if UNTWIST_SOLL_BUDGET else None
        strokes, untwisted = untwist_strokes(strokes, xh_px, UNTWIST_WINDOW_UNITS, soll_points=soll_pts)
    detail = {
        "nodes": len(pg.graph.nodes),
        "edges": len(pg.graph.edges),
        "map_strokes": len(strokes),
        "registration": result.registration,
        "baseline_row": result.baseline_row,
        "xh_px": xh_px,
        **({"untwisted": untwisted} if UNTWIST_WINDOW_UNITS > 0.0 else {}),
    }
    return strokes, detail


def strokes_to_word_units(strokes: list[np.ndarray], reg: dict, baseline_row: float) -> list[list[list[float]]]:
    """Crop px -> the stored trace frame (inverse of the map transform)."""
    xh = float(reg.get("xh_px", 1.0))
    tx = float(reg.get("tx", 0.0))
    ty = float(reg.get("ty", 0.0))
    out = []
    for s in strokes:
        u = (s[:, 0] - tx) / xh
        v = (baseline_row - (s[:, 1] - ty)) / xh
        out.append([[round(float(a), 4), round(float(b), 4)] for a, b in zip(u, v, strict=True)])
    return out


def candidate_row(case: WordCase, strokes: list[np.ndarray], detail: dict) -> dict:
    reg = detail["registration"]
    return {
        "specimen_id": case.id,
        "strokes": strokes_to_word_units(strokes, reg, detail["baseline_row"]),
        "measurements": {
            "registration_px": {
                "tx": float(reg.get("tx", 0.0)),
                "ty": float(reg.get("ty", 0.0)),
                "baseline_row": float(detail["baseline_row"]),
            },
            "xh_px": float(detail["xh_px"]),
            "fit_path": "inkpilot",
        },
    }


def write_candidates(rows: list[dict], out: Path, label: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"frame": "word_registration", "label": label, "rows": rows}, ensure_ascii=False))
