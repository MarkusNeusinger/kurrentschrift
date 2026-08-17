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
# v0.6 (pre-registered): the smoothing pass over the 8-connected pixel
# zigzag — per iteration the local mean (1, 2, 1) / 4 over each stroke with
# FIXED endpoints. Structure is a GATE, not code: the bench counters must
# stay byte-identical or the arm is rejected. 0 = off.
SMOOTH_ITERATIONS = 0


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


# ----------------------------------------------------------------- the ride


def _assign_stroke(pg: PilotGraph, stroke_px: np.ndarray, xh_px: float) -> tuple[np.ndarray, list[PixelLoc | None]]:
    """The GLOBAL sample->ridge assignment of one map stroke (samples, seq).

    Solved as a Viterbi over the sample chain: a greedy walk boards the first
    plausible rail and then cascades — on the composed m, whose arcade runs
    narrower than the ink's, it boarded the wrong rail and bridged across the
    counters (the „mit" finding of the first inspection page). States per
    sample are the nearby ridge points plus one BRIDGE state; transitions
    price the graph ride, emissions the deviation from the map. Leading and
    trailing bridge runs that never re-board are TRIMMED — ink that does not
    exist (a composed run-out over blank paper) is not a pen stroke.
    """
    samples = resample(stroke_px, SAMPLE_STEP_UNITS * xh_px)
    radius = BOARD_RADIUS_UNITS * xh_px
    max_ride = MAX_RIDE_FACTOR * SAMPLE_STEP_UNITS * xh_px
    bridge_emit = BRIDGE_EMIT_FACTOR * radius
    n = len(samples)

    # v0.4 map right-of-way: samples inside the MAP's own retrace zones ride
    # the map (bridge state forced) — the rail is degenerate there, the map
    # carries the crossing. Zones from the frozen ruler's own detector.
    map_priority = np.zeros(n, dtype=bool)
    if MAP_PRIORITY_IN_RETRACE and n >= 4:
        ia, ib = detect_retrace_pairs(samples[:, 0], samples[:, 1], None, prox_px=MAP_RETRACE_PROX_UNITS * xh_px)
        for arr in (ia, ib):
            map_priority[np.asarray(arr, dtype=int)] = True

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
        return samples, [None] * len(samples)  # pure bridge: no ink under the map
    last = max(k for k in range(len(seq)) if rides(k))
    return samples[first : last + 1], seq[first : last + 1]


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


def pilot_stroke(pg: PilotGraph, stroke_px: np.ndarray, xh_px: float) -> np.ndarray:
    """One map stroke ridden along the skeleton (assignment + assembly)."""
    samples, seq = _assign_stroke(pg, stroke_px, xh_px)
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
    assignments = [_assign_stroke(pg, s, xh_px) for s in map_strokes_px(result)]
    if RIDE_DOUBLE_MAP_PRIORITY:
        # Word-global double detection in WRITING order: the first pass of a
        # rail pixel keeps the rail, every later pass rides the map.
        seen: dict[tuple[int, int], int] = {}
        # The counter is a WRITING-ORDER clock, deliberately ticking on every
        # sample including bridges: a pen that leaves a pixel — even over a
        # gap in the ink — and comes back has made a second pass; only dense
        # consecutive samples parked on one pixel are the same visit.
        counter = 0
        masks: list[np.ndarray] = []
        for samples, seq in assignments:
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
    detail = {
        "nodes": len(pg.graph.nodes),
        "edges": len(pg.graph.edges),
        "map_strokes": len(strokes),
        "registration": result.registration,
        "baseline_row": result.baseline_row,
        "xh_px": xh_px,
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
