"""Tintenpfad — ink first, letters later: the strand decode of the Tintenfolger.

The author's two sentences of 2026-09-11 — „erst mal wirklich der Tinte folgen,
erst danach überlegen, welcher Bereich der gefolgten Tinte welchem Buchstaben
entspricht" and „die Punkte können sich nur so, wie so eine Welle,
zusammenhängend verschieben" — taken literally. The pen path here is a
concatenation of WHOLE skeleton strands, the ink's own maximal smooth chains;
the composed word is only a weak prior for ORDER and DIRECTION. There are no
per-point degrees of freedom: a point cannot dart sideways because a point has
no parameter, and the only free variables are discrete — which strand next, in
which direction, where the pen lifts — each of which moves a whole strand at
once. The wave is a property of the substrate, not a penalty.

Two stages, strictly separated:

* **Stage 1 — Strang (ink only, no prior).** `core.skeleton_graph.build_graph`
  on the frozen skeleton after the K-C ink evidence (the same evidence the
  chain follower reads) → degree-1 edges shorter than `spur_xh` are thinning
  spurs and are pruned → at every node each edge-end's leaving direction is
  read over `dir_window_xh` of arc, and the ends are paired by the matching
  that minimises Σ(1 + cos) over pairs plus `stop_cost` per unpaired end (brute
  force; an X that thinned to two T's finds both straight-through pairs at
  their own T) → the pairings are walked into strands. With `rail="subpixel"`
  every strand pixel is moved along its local normal onto the ridge of the
  ink's distance transform: the EDT profile across a stroke is a TENT (it is a
  distance), so the tent's apex `(f(+1) − f(−1)) / 2` is the exact sub-pixel
  centre — a reading of the ink, not a smoothing of the path, and the place
  where the thinning's raster staircase is removed at its source.
* **Stage 2 — Strang-Dekodierung (order only).** The composed word, placed by
  the frozen registration and per slot moved by the Gauß-Verschiebung
  (`affinereg.register_letters`, the night loop's `--chain-seed affine`), is
  resampled in writing order with a slot label and a stroke index per sample.
  A Viterbi over the seed samples decodes it through the strands: states are
  strand pixels × two travel directions plus one PAPER state; the emission
  prices deviation and tangent disagreement; transitions price a ride along a
  strand per pixel advanced (monotone — never a pixel re-laid), a hairpin on
  the same strand once (`turn_cost`, a pen event), a jump to another strand
  within `jump_radius_xh` by gap and turning, and every boarding into or out of
  the paper (`paper_board`, a lift-class event — without it the paper state is
  a wormhole through which a strand can be teleported along; measured on
  `das`). A seed pen lift frees every transition. Out-and-back jumps (leave a
  strand, come straight back within `reentry_window` samples with no net travel
  on it) are the hysteresis hole the judges named: after each decode they are
  found on the state sequence, the intermediate strands are forbidden for those
  samples, and the decode is repeated (`reentry_passes`). Every emitted pixel
  inherits the slot of the seed sample that decoded it, so the letter
  assignment IS the alignment; `meta.letter_spans` is checked afterwards
  against a monotone DTW of the finished path (`label_agreement`) rather than
  produced by one.

The output is assembled from the decoded states: consecutive states on one
strand emit the strand's pixels between them (the rail, in the travelled
direction); a jump emits a tangent-continuous Hermite bridge between the
leaving and entering tangents, resampled at the rail's own step and capped in
its LATERAL excursion as well as its gap (`bridge="chord"` is the prototype's
two-vertex chord, kept as the measured control); a paper gap between two
boarded pixels is drawn as rail when it is a legal forward ride, bridged when
within the jump radius, and is a pen LIFT otherwise. The runs are emitted
arc-length-uniform at `resample_step_xh` (a redistribution of vertices along
the polyline, never a move off it — declared, and the kink reading on the raw
chain is reported beside it), converted to the word's registration frame and
written through `follow.candidate_payload`.

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run python -m tools.pairlab.tintenpfad \
        [--all | ids…] [--set words] [--expect-root <digest>] [--jobs 2] \
        [--candidate-out cand.json] [--json report.json] [--legacy-p5] [--weight NAME=VALUE …]

Measurement layer only: reads the frozen fixtures, writes a candidate file and
a report. No DB, no edits to `core/` — `core.skeleton_graph` and
`core.continuity` are imported read-only. Every default of `TintenpfadWeights`
is the arm as delivered; `--legacy-p5` restores the prototype's measured
configuration so the ladder row it produced can be reproduced from this tool.
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path
from typing import Any

import numpy as np
from scipy.ndimage import distance_transform_edt, map_coordinates
from scipy.spatial import cKDTree

from core.continuity import kink_events, stroke_profile
from core.skeleton_graph import build_graph
from tools.pairlab.affinereg import _affine_matrix, register_letters
from tools.pairlab.follow import STATUS_FAILED, STATUS_OK, STATUS_SKIPPED, _source_id_of, candidate_payload
from tools.pairlab.ink_evidence import INK_EVIDENCE_PAPER_FRACTION, InkEvidenceOptions, ink_evidence_case
from tools.pairlab.trace import _px_to_word_units, cap_word_strokes
from tools.tracebench.metric import dtw as ruler_dtw
from tools.wordbench.roots import add_expect_root_argument, announce_roots
from tools.wordlab.cases import DEFAULT_FIXTURES_DIR, WordCase, fixture_root_for, iter_fixture_word_cases
from tools.wordlab.derive import WordDeriveResult, derive_word


TINTENPFAD_TOOL_NAME = "wellen.tintenpfad"
TINTENPFAD_ARTIFACT_VERSION = "1"
# A forbidden (sample, strand) pair costs this much more than any legal path —
# the hysteresis is a constraint, not a price to be traded against a ride.
FORBID_COST = 1.0e6
# Hermite bridges are sampled at the rail's own step: one pixel.
BRIDGE_STEP_PX = 1.0
# The largest normal offset the sub-pixel reading may move a skeleton pixel: a
# thinning pixel sits within half a pixel of the medial axis, and a larger
# read is the tent breaking at a stroke edge, not a centre.
SUBPIXEL_MAX_PX = 0.75


@dataclass(frozen=True)
class TintenpfadWeights:
    """Every constant of both stages, frozen and carried into the artefact.

    All lengths in x-heights unless the name says `_px`. The defaults are the
    arm as delivered; the prototype's ladder row p5 is `LEGACY_P5`.
    """

    # ---- stage 1: strands
    spur_xh: float = 0.15  # degree-1 edges shorter than this are thinning spurs
    dir_window_xh: float = 0.12  # arc over which an edge-end's direction is read (≈ 4 px)
    stop_cost: float = 1.0  # an unpaired end costs as much as a 90° turn; a pair must beat 2 × this
    min_strand_xh: float = 0.10  # strands shorter than this after pairing are dropped
    tangent_window_px: int = 3  # half window of the strand tangent, in pixels
    rail: str = "subpixel"  # "subpixel": tent fit on the EDT along the normal · "raw": the pixel chain
    # ---- stage 2: seed
    affine_seed: bool = True  # the Gauß-Verschiebung per slot; off = the plain composition
    seed_step_xh: float = 0.03  # seed resampling (≈ the chain's sample spacing)
    # ---- stage 2: candidate states per sample
    board_radius_xh: float = 0.60  # a seed sample may board any strand pixel within this radius
    candidates: str = "strand"  # "strand": nearest pixels of EVERY strand in the ball · "distance": the nearest overall
    strand_cand: int = 3  # pixels kept per strand in the ball ("strand" mode)
    max_cand: int = 24  # pixels kept per sample after the per-strand pick (never drops a strand's nearest)
    # ---- stage 2: prices (the Lotse's px prices rescaled to the 0.03-xh step)
    dev_w: float = 0.5  # per px of sample→pixel deviation
    tan_w: float = 1.0  # × (1 − cos(seed tangent, travel direction))
    ride_w: float = 1.0  # per px advanced along a strand
    ride_cap_xh: float = 0.96  # more than this between two samples is not a ride
    back_tol_px: float = 0.0  # 0 = strictly monotone; the prototype tolerated 2 px of re-laid rail
    turn_cost: float = 8.0  # a hairpin on the same strand (a retrace turn), priced once
    jump_radius_xh: float = 0.35  # strand→strand jump allowed within this gap
    jump_base: float = 4.0
    gap_w: float = 1.0  # per px of jump gap
    jump_turn_w: float = 8.0  # × (1 − cos) between leaving and entering directions
    paper_w: float = 12.0  # per sample in the paper state
    paper_board: float = 20.0  # per boarding into or out of the paper (the wormhole closer)
    # ---- stage 2: the re-entry hysteresis
    reentry_window: int = 12  # samples; 0 = off
    reentry_net_xh: float = 0.10  # "came straight back": exit and re-entry pixel this close
    reentry_passes: int = 4  # decode repetitions with the excursion strands forbidden
    # ---- assembly
    bridge: str = "hermite"  # "hermite": tangent-continuous, resampled, laterally capped · "chord": two vertices
    bridge_lateral_cap_xh: float = 0.15  # a bridge may bow this far from its chord
    resample_step_xh: float = 0.02  # arc-length-uniform output; 0 = the pixel chain as emitted
    # A run end is walked on along its own tangent to the ink's tip, at most
    # this far, while the distance transform keeps falling (a tip, never a
    # junction): the thinning stops half a nib short of every stroke end and
    # the spur pruning may have taken an Anstrich with it. 0 = off (measured
    # as arm K-tips, not part of the delivered default).
    tip_extend_xh: float = 0.0
    # The tip READING (arm „Spitzen", off by default): a run end that sits on a
    # FREE strand end (a skeleton end with no other alive edge at its node) is
    # walked on along the EDT ridge until the frozen ink mask ends — no fixed
    # amount, the mask is the stop; a rising EDT is a junction and stops it too.
    # `tip_read_cap_xh` is a safety cap against a runaway walk, counted when it binds.
    tip_read: bool = False
    tip_read_cap_xh: float = 1.0
    # Spurs at strand ENDS are the stroke's continuation the thinning broke off
    # (an Anstrich), not a lateral artefact: with this on, a node whose non-spur
    # edges number at most one keeps its spurs instead of pruning them.
    spur_at_ends: bool = False

    def __post_init__(self) -> None:
        if self.rail not in ("subpixel", "raw"):
            raise ValueError(f"rail must be 'subpixel' or 'raw', not {self.rail!r}")
        if self.candidates not in ("strand", "distance"):
            raise ValueError(f"candidates must be 'strand' or 'distance', not {self.candidates!r}")
        if self.bridge not in ("hermite", "chord"):
            raise ValueError(f"bridge must be 'hermite' or 'chord', not {self.bridge!r}")


# The prototype's ladder row p5 (temp/wellen-sep11/tintenpfad/ladder.txt), so
# the tool can reproduce it before any new measurement.
LEGACY_P5 = TintenpfadWeights(
    rail="raw",
    candidates="distance",
    max_cand=12,
    back_tol_px=2.0,
    reentry_window=0,
    bridge="chord",
    resample_step_xh=0.0,
)

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


@dataclass
class Strand:
    """One maximal smooth chain of the skeleton, in crop px and traversal order."""

    points: np.ndarray  # (n, 2)
    edges: list[int]
    closed: bool = False
    tan: np.ndarray = field(default=None)  # (n, 2) unit tangents along `points`
    # Per end (points[0], points[-1]): a skeleton end with no other alive edge at
    # its node — a stroke TIP the thinning stopped short of, never a junction end.
    free_ends: tuple[bool, bool] = (False, False)
    # Indices into `points` where the strand passes THROUGH a junction node.
    junction_idx: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=int))

    @property
    def length(self) -> float:
        return polyline_len(self.points)


@dataclass
class Seed:
    """The composed word resampled in writing order, in crop px."""

    xy: np.ndarray  # (n, 2)
    tan: np.ndarray  # (n, 2) unit tangents by central difference
    slot: np.ndarray  # (n,) slot index, −1 for a connector
    stroke: np.ndarray  # (n,) stroke index, +1 at every pen lift


# ------------------------------------------------------------ stage 1: strands


def polyline_len(p: np.ndarray) -> float:
    p = np.asarray(p, dtype=float).reshape(-1, 2)
    return float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum()) if len(p) > 1 else 0.0


def end_direction(points: np.ndarray, end: int, window_px: float) -> np.ndarray:
    """Unit direction LEAVING the node at `end` (0 = points[0], 1 = points[-1])."""
    p = points if end == 0 else points[::-1]
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    k = int(np.searchsorted(arc, window_px))
    k = max(1, min(k, len(p) - 1))
    v = p[k] - p[0]
    n = float(np.hypot(*v))
    return v / n if n > 0 else np.zeros(2)


def best_matching(
    ends: Sequence[tuple[int, int]], dirs: Sequence[np.ndarray], stop_cost: float
) -> dict[tuple[int, int], tuple[int, int] | None]:
    """Smoothest pairing of the edge-ends meeting at one node (brute force, ≤ 8 ends).

    A pair costs `1 + cos` of its two leaving directions (0 = straight through,
    2 = a hairpin), an unpaired end `stop_cost`; a pair is only worth forming
    when it beats stopping both ends.
    """
    n = len(ends)
    cost = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            cost[i, j] = 1.0 + float(dirs[i] @ dirs[j])
    best: tuple[float, list[tuple[int, int]]] = (float("inf"), [])

    def rec(remaining: list[int], acc: float, pairs: list[tuple[int, int]]) -> None:
        nonlocal best
        if acc >= best[0]:
            return
        if not remaining:
            best = (acc, list(pairs))
            return
        i = remaining[0]
        rest = remaining[1:]
        rec(rest, acc + stop_cost, pairs)
        for j in rest:
            if cost[i, j] < 2.0 * stop_cost:
                rec([r for r in rest if r != j], acc + cost[i, j], pairs + [(i, j)])

    rec(list(range(n)), 0.0, [])
    partner: dict[tuple[int, int], tuple[int, int] | None] = dict.fromkeys(ends)
    for i, j in best[1]:
        partner[ends[i]] = ends[j]
        partner[ends[j]] = ends[i]
    return partner


def strand_tangents(points: np.ndarray, window_px: int, closed: bool = False) -> np.ndarray:
    """Unit tangent per point over ±`window_px` points (wrapped on a ring)."""
    n = len(points)
    t = np.zeros((n, 2))
    for i in range(n):
        if closed and n > 2 * window_px + 1:
            a, b = (i - window_px) % n, (i + window_px) % n
        else:
            a, b = max(0, i - window_px), min(n - 1, i + window_px)
        v = points[b] - points[a]
        nv = float(np.hypot(*v))
        t[i] = v / nv if nv > 0 else (1.0, 0.0)
    return t


def subpixel_rail(points: np.ndarray, tan: np.ndarray, edt: np.ndarray) -> np.ndarray:
    """Each pixel moved along its normal onto the apex of the ink's distance tent.

    The EDT read at −1, 0, +1 px along the local normal is `w − |x − δ|` inside
    a stroke of half-width `w`, so `δ = (f(+1) − f(−1)) / 2` exactly — a
    parabola would halve it. Reads that fall off the ink (a stroke edge, a
    counter) leave the pixel where the thinning put it.
    """
    h, w = edt.shape
    out = np.asarray(points, dtype=float).copy()
    normal = np.column_stack([-tan[:, 1], tan[:, 0]])
    plus = out + normal
    minus = out - normal
    f_plus = map_coordinates(edt, [plus[:, 1], plus[:, 0]], order=1, mode="constant", cval=0.0)
    f_minus = map_coordinates(edt, [minus[:, 1], minus[:, 0]], order=1, mode="constant", cval=0.0)
    delta = 0.5 * (f_plus - f_minus)
    valid = (f_plus > 0.0) & (f_minus > 0.0) & (np.abs(delta) <= SUBPIXEL_MAX_PX)
    inside = (out[:, 0] >= 1) & (out[:, 0] <= w - 2) & (out[:, 1] >= 1) & (out[:, 1] <= h - 2)
    move = valid & inside
    out[move] += normal[move] * delta[move, None]
    return out


def strands_of(skel: np.ndarray, xh: float, weights: TintenpfadWeights, diag: dict[str, Any]) -> list[Strand]:
    """Stage 1: the ink's maximal smooth chains, from the skeleton alone."""
    g = build_graph(skel)
    edges = [(e.a, e.b, np.asarray(e.points, dtype=float)) for e in g.edges]
    incident: dict[int, list[int]] = {n: [] for n in range(len(g.nodes))}
    for i, (a, b, _) in enumerate(edges):
        incident[a].append(i)
        if b != a:
            incident[b].append(i)
    spur = np.zeros(len(edges), dtype=bool)
    for i, (a, b, pts) in enumerate(edges):
        deg_a, deg_b = len(incident[a]), len(incident[b])
        if (deg_a == 1 or deg_b == 1) and not (deg_a == 1 and deg_b == 1) and polyline_len(pts) < weights.spur_xh * xh:
            spur[i] = True
    kept_at_ends = 0
    if weights.spur_at_ends:
        # Judged against the ORIGINAL spur set: a node whose non-spur edges
        # number at most one would become a strand end without its spurs, so
        # they are the stroke's continuation and stay.
        candidates = spur.copy()
        for i in np.flatnonzero(candidates):
            a, b, _ = edges[i]
            junction = b if len(incident[a]) == 1 else a
            others = sum(1 for j in incident[junction] if j != i and not candidates[j])
            if others <= 1:
                spur[i] = False
                kept_at_ends += 1
    alive = ~spur
    diag["spurs_pruned"] = int((~alive).sum())
    if weights.spur_at_ends:
        diag["spurs_kept_at_ends"] = kept_at_ends
    diag["junctions_too_dense"] = 0
    partner: dict[tuple[int, int], tuple[int, int] | None] = {}
    alive_ends: dict[int, int] = {}
    for node in range(len(g.nodes)):
        ends: list[tuple[int, int]] = []
        dirs: list[np.ndarray] = []
        for i in incident[node]:
            if not alive[i]:
                continue
            a, b, pts = edges[i]
            for end in (0, 1):
                if (end == 0 and a == node) or (end == 1 and b == node):
                    ends.append((i, end))
                    dirs.append(end_direction(pts, end, weights.dir_window_xh * xh))
        alive_ends[node] = len(ends)
        if len(ends) <= 1:
            for e in ends:
                partner[e] = None
            continue
        if len(ends) > 8:
            for e in ends:
                partner[e] = None
            diag["junctions_too_dense"] += 1
            continue
        partner.update(best_matching(ends, dirs, weights.stop_cost))
    diag["junction_pairs"] = sum(1 for v in partner.values() if v is not None) // 2
    used = np.zeros(len(edges), dtype=bool)
    used[~alive] = True
    strands: list[Strand] = []

    def walk(start_end: tuple[int, int]) -> Strand:
        pts: list[np.ndarray] = []
        eds: list[int] = []
        e, end = start_end
        node_first = edges[e][0] if end == 0 else edges[e][1]
        closed = False
        joins: list[int] = []
        while True:
            used[e] = True
            _a, _b, p = edges[e]
            seg = p if end == 0 else p[::-1]
            if pts:
                joins.append(len(pts) - 1)
            pts.extend(seg[1:] if pts else seg)
            eds.append(e)
            nxt = partner.get((e, 1 - end))
            if nxt is None:
                break
            if used[nxt[0]]:
                closed = nxt == start_end
                break
            e, end = nxt
        node_last = edges[e][1] if end == 0 else edges[e][0]
        free = (False, False) if closed else (alive_ends.get(node_first) == 1, alive_ends.get(node_last) == 1)
        return Strand(
            np.asarray(pts, dtype=float).reshape(-1, 2),
            eds,
            closed,
            free_ends=free,
            junction_idx=np.asarray(joins, dtype=int),
        )

    for (e, end), p in partner.items():
        if p is None and not used[e]:
            strands.append(walk((e, end)))
    for e in range(len(edges)):
        if not used[e]:
            strands.append(walk((e, 0)))
    strands = [s for s in strands if s.length >= weights.min_strand_xh * xh]
    for s in strands:
        s.tan = strand_tangents(s.points, weights.tangent_window_px, s.closed)
    diag["strands"] = len(strands)
    diag["closed_strands"] = sum(1 for s in strands if s.closed)
    return strands


def refine_strands(strands: list[Strand], mask: np.ndarray, weights: TintenpfadWeights) -> None:
    """The sub-pixel reading of every strand, in place; tangents re-read afterwards."""
    edt = distance_transform_edt(np.asarray(mask, dtype=bool))
    for s in strands:
        s.points = subpixel_rail(s.points, s.tan, edt)
        s.tan = strand_tangents(s.points, weights.tangent_window_px, s.closed)


# --------------------------------------------------------------- stage 2: seed


def seed_samples(
    result: WordDeriveResult, xh: float, weights: TintenpfadWeights, affreg: dict[int, dict] | None = None
) -> Seed:
    """The composed word in crop px, per slot moved by the registered affine
    (about the slot's entry point, exactly `affinereg._apply`), a connector
    between two moved letters carried by the linear blend of its neighbours'
    end offsets, everything resampled at `seed_step_xh` in writing order."""
    reg = result.registration
    tx, ty, base = float(reg.get("tx", 0.0)), float(reg.get("ty", 0.0)), float(result.baseline_row)
    items = [it for it in result.composed["items"] if len(it.get("centerline") or []) >= 2]
    px_items = []
    for it in items:
        c = np.asarray(it["centerline"], dtype=float).reshape(-1, 2)
        px_items.append(np.column_stack([c[:, 0] * xh + tx, base - c[:, 1] * xh + ty]))
    entries: dict[int, np.ndarray] = {}
    for it, pts in zip(items, px_items, strict=True):
        s = it.get("slot_index")
        if s is not None and s not in entries:
            entries[s] = pts[0].copy()
    moved = []
    for it, pts in zip(items, px_items, strict=True):
        s = it.get("slot_index")
        if affreg and s is not None and s in affreg:
            theta = np.asarray(affreg[s]["theta"], dtype=float)
            moved.append(entries[s] + (pts - entries[s]) @ _affine_matrix(theta).T + theta[:2])
        else:
            moved.append(pts.copy())
    if affreg:
        for k, it in enumerate(items):
            if it.get("slot_index") is None and 0 < k < len(items) - 1:
                off_a = moved[k - 1][-1] - px_items[k - 1][-1]
                off_b = moved[k + 1][0] - px_items[k + 1][0]
                w = np.linspace(0.0, 1.0, len(px_items[k]))[:, None]
                moved[k] = px_items[k] + (1 - w) * off_a + w * off_b
    xs, slots, strokes = [], [], []
    stroke, prev = 0, None
    for it, pts in zip(items, moved, strict=True):
        slot = int(it["slot_index"]) if it.get("slot_index") is not None else -1
        if it.get("lift") and prev is not None:
            stroke += 1
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        arc = np.concatenate([[0.0], np.cumsum(seg)])
        n = max(2, int(arc[-1] / (weights.seed_step_xh * xh)) + 1)
        s_ = np.linspace(0.0, arc[-1], n)
        xs.append(np.column_stack([np.interp(s_, arc, pts[:, 0]), np.interp(s_, arc, pts[:, 1])]))
        slots.append(np.full(n, slot))
        strokes.append(np.full(n, stroke))
        prev = pts[-1]
    xy = np.vstack(xs)
    tan = np.gradient(xy, axis=0)
    nrm = np.linalg.norm(tan, axis=1)
    tan = tan / np.where(nrm > 0, nrm, 1.0)[:, None]
    return Seed(xy=xy, tan=tan, slot=np.concatenate(slots), stroke=np.concatenate(strokes))


# ------------------------------------------------------------- stage 2: decode


@dataclass
class _Board:
    """Every strand pixel as one flat table, for the vectorised transitions."""

    xy: np.ndarray
    sid: np.ndarray
    idx: np.ndarray
    tan: np.ndarray
    n: np.ndarray
    closed: np.ndarray
    tree: cKDTree

    @classmethod
    def of(cls, strands: Sequence[Strand]) -> _Board:
        xy = np.vstack([s.points for s in strands])
        sid = np.concatenate([np.full(len(s.points), i) for i, s in enumerate(strands)])
        idx = np.concatenate([np.arange(len(s.points)) for s in strands])
        tan = np.vstack([s.tan for s in strands])
        n = np.concatenate([np.full(len(s.points), len(s.points)) for s in strands])
        closed = np.concatenate([np.full(len(s.points), bool(s.closed)) for s in strands])
        return cls(xy, sid, idx, tan, n, closed, cKDTree(xy))


def _candidate_pixels(
    board: _Board, point: np.ndarray, radius: float, weights: TintenpfadWeights
) -> tuple[np.ndarray, int, int]:
    """The strand pixels one seed sample may board, how many pixels the ball
    held, and how many STRANDS the ball held (each of which the kept set
    must still reach — the judges' effective-radius test)."""
    ball = board.tree.query_ball_point(point, r=radius)
    held = len(ball)
    if held == 0:
        return np.zeros(0, dtype=int), 0, 0
    ball = np.asarray(ball, dtype=int)
    n_strands = len(set(board.sid[ball].tolist()))
    d = np.linalg.norm(board.xy[ball] - point, axis=1)
    order = ball[np.argsort(d, kind="stable")]
    if weights.candidates == "distance":
        return order[: weights.max_cand], held, n_strands
    # Per strand: its nearest pixel first, so no strand inside the ball is
    # ever unreachable because a nearer strand filled the set; then up to
    # `strand_cand` per strand, then the cap — nearest-of-strand pixels are
    # never the ones dropped.
    firsts: list[int] = []
    others: list[int] = []
    seen: dict[int, int] = {}
    for p in order:
        s = int(board.sid[p])
        c = seen.get(s, 0)
        if c == 0:
            firsts.append(int(p))
        elif c < weights.strand_cand:
            others.append(int(p))
        seen[s] = c + 1
    picked = firsts + others[: max(0, weights.max_cand - len(firsts))]
    picked.sort(key=lambda p: float(np.linalg.norm(board.xy[p] - point)))
    return np.asarray(picked, dtype=int), held, n_strands


def decode(
    strands: Sequence[Strand],
    seed: Seed,
    xh: float,
    weights: TintenpfadWeights,
    forbid: dict[int, set[int]] | None = None,
) -> tuple[list[tuple[int, int, int] | None], float, dict[str, Any]]:
    """Viterbi over the seed samples; per sample a (strand, index, dir) or None (paper)."""
    board = _Board.of(strands)
    radius = weights.board_radius_xh * xh
    ride_cap = weights.ride_cap_xh * xh
    jump_r = weights.jump_radius_xh * xh
    n = len(seed.xy)
    inf = float("inf")
    s_pix: list[np.ndarray] = []
    s_dir: list[np.ndarray] = []
    s_emit: list[np.ndarray] = []
    held_counts, kept_counts, strands_held, strands_kept = [], [], [], []
    for k in range(n):
        idx, held, n_strands = _candidate_pixels(board, seed.xy[k], radius, weights)
        held_counts.append(held)
        kept_counts.append(len(idx))
        strands_held.append(n_strands)
        strands_kept.append(len(set(board.sid[idx].tolist())) if len(idx) else 0)
        pix = np.concatenate([idx, idx, [-1]])
        dr = np.concatenate([np.ones(len(idx)), -np.ones(len(idx)), [0]])
        emit = np.full(len(pix), weights.paper_w)
        if len(idx):
            dev = np.linalg.norm(board.xy[idx] - seed.xy[k], axis=1)
            cos_f = board.tan[idx] @ seed.tan[k]
            emit[: len(idx)] = weights.dev_w * dev + weights.tan_w * (1.0 - cos_f)
            emit[len(idx) : 2 * len(idx)] = weights.dev_w * dev + weights.tan_w * (1.0 + cos_f)
            if forbid and k in forbid:
                banned = np.isin(board.sid[idx], list(forbid[k]))
                emit[: len(idx)][banned] += FORBID_COST
                emit[len(idx) : 2 * len(idx)][banned] += FORBID_COST
        s_pix.append(pix)
        s_dir.append(dr)
        s_emit.append(emit)
    cost = s_emit[0].copy()
    back: list[np.ndarray] = []
    for k in range(1, n):
        pa, da = s_pix[k - 1], s_dir[k - 1]
        pb, db = s_pix[k], s_dir[k]
        lift = seed.stroke[k] != seed.stroke[k - 1]
        a_n, b_n = len(pa), len(pb)
        trans = np.full((a_n, b_n), inf)
        paper_a = pa < 0
        paper_b = pb < 0
        if lift:
            trans[:, :] = 0.0
        else:
            trans[paper_a, :] = weights.paper_board
            trans[:, paper_b] = weights.paper_board
            trans[np.ix_(paper_a, paper_b)] = 0.0
            ra, rb = ~paper_a, ~paper_b
            if ra.any() and rb.any():
                ia, ib = pa[ra], pb[rb]
                sa, sb = board.sid[ia], board.sid[ib]
                xa, xb = board.xy[ia], board.xy[ib]
                dda, ddb = da[ra], db[rb]
                same = sa[:, None] == sb[None, :]
                adv = (board.idx[ib][None, :] - board.idx[ia][:, None]) * dda[:, None]
                # A ring has no end: the graph cut it at an arbitrary pixel, so
                # the advance is read modulo its length (shortest signed way round).
                ring = same & board.closed[ia][:, None]
                nn = board.n[ia][:, None].astype(float)
                adv_wrapped = np.mod(adv, nn)
                adv_wrapped = np.where(adv_wrapped > nn / 2.0, adv_wrapped - nn, adv_wrapped)
                adv = np.where(ring, adv_wrapped, adv)
                samedir = dda[:, None] == ddb[None, :]
                ok = same & samedir & (adv >= -weights.back_tol_px) & (adv <= ride_cap)
                sub = np.where(ok, weights.ride_w * np.maximum(adv, 0.0), inf)
                okh = same & ~samedir & (np.abs(adv) <= ride_cap)
                sub = np.where(okh, weights.turn_cost + weights.ride_w * np.abs(adv), sub)
                gap = np.linalg.norm(xa[:, None, :] - xb[None, :, :], axis=2)
                ta = board.tan[ia] * dda[:, None]
                tb = board.tan[ib] * ddb[:, None]
                cosj = np.einsum("ik,jk->ij", ta, tb)
                okj = ~same & (gap <= jump_r)
                sub = np.where(okj, weights.jump_base + weights.gap_w * gap + weights.jump_turn_w * (1.0 - cosj), sub)
                trans[np.ix_(ra, rb)] = sub
        tot = cost[:, None] + trans
        arg = np.argmin(tot, axis=0)
        cost = tot[arg, np.arange(b_n)] + s_emit[k]
        back.append(arg)
    j = int(np.argmin(cost))
    states: list[tuple[int, int, int] | None] = [None] * n
    for k in range(n - 1, -1, -1):
        p, d = s_pix[k][j], s_dir[k][j]
        states[k] = None if p < 0 else (int(board.sid[p]), int(board.idx[p]), int(d))
        if k > 0:
            j = int(back[k - 1][j])
    held = np.asarray(held_counts)
    kept = np.asarray(kept_counts)
    s_held = np.asarray(strands_held)
    s_kept = np.asarray(strands_kept)
    # The judges' effective-radius test: a sample whose ball held a strand the
    # kept set does not reach was truncated — that strand is unreachable there
    # whatever `board_radius_xh` says.
    diag = {
        "cand_kept_median": float(np.median(kept)) if n else 0.0,
        "cand_held_median": float(np.median(held)) if n else 0.0,
        "strands_in_ball_median": float(np.median(s_held)) if n else 0.0,
        "cand_truncated_share": round(float((s_kept < s_held).mean()), 3) if n else 0.0,
    }
    return states, float(np.min(cost)), diag


def reentries(
    states: Sequence[tuple[int, int, int] | None],
    strands: Sequence[Strand],
    seed: Seed,
    xh: float,
    weights: TintenpfadWeights,
) -> list[tuple[int, int]]:
    """Out-and-back jumps: samples `[k, j)` spent on other strands between
    leaving strand A at `k − 1` and re-boarding it at `j ≤ k − 1 + window`
    with no lift between and no net travel on A."""
    out: list[tuple[int, int]] = []
    n = len(states)
    net = weights.reentry_net_xh * xh
    k = 1
    while k < n:
        a, b = states[k - 1], states[k]
        if a is None or b is None or seed.stroke[k] != seed.stroke[k - 1] or a[0] == b[0]:
            k += 1
            continue
        exit_px = strands[a[0]].points[a[1]]
        j = k
        found = None
        while j < n and j <= k - 1 + weights.reentry_window and seed.stroke[j] == seed.stroke[k - 1]:
            st = states[j]
            if st is None:
                break
            if st[0] == a[0]:
                if float(np.hypot(*(strands[st[0]].points[st[1]] - exit_px))) <= net:
                    found = j
                break
            j += 1
        if found is not None:
            out.append((k, found))
            k = found
        else:
            k += 1
    return out


def decode_with_hysteresis(
    strands: Sequence[Strand], seed: Seed, xh: float, weights: TintenpfadWeights
) -> tuple[list[tuple[int, int, int] | None], float, dict[str, Any]]:
    """The decode, repeated with each pass's out-and-back excursions forbidden."""
    forbid: dict[int, set[int]] = {}
    removed = 0
    passes = 0
    while True:
        states, total, diag = decode(strands, seed, xh, weights, forbid or None)
        passes += 1
        if weights.reentry_window <= 0 or passes > weights.reentry_passes:
            break
        found = reentries(states, strands, seed, xh, weights)
        if not found:
            break
        for k, j in found:
            for q in range(k, j):
                st = states[q]
                if st is not None:
                    forbid.setdefault(q, set()).add(st[0])
        removed += len(found)
    diag.update(
        {
            "reentry_passes": passes,
            "reentries_forbidden": removed,
            "reentries_left": len(reentries(states, strands, seed, xh, weights)) if weights.reentry_window > 0 else -1,
        }
    )
    return states, total, diag


# ----------------------------------------------------------------- assembly


def hermite_bridge(
    p0: np.ndarray, t0: np.ndarray, p1: np.ndarray, t1: np.ndarray, step_px: float, lateral_cap_px: float
) -> np.ndarray:
    """A tangent-continuous bridge from `p0` (leaving along `t0`) to `p1`
    (entering along `t1`), sampled at `step_px`, WITHOUT `p0` and WITH `p1`.

    Cubic Hermite with both tangents scaled to the gap; when the bow leaves the
    chord SEGMENT by more than the cap — sideways, or past either end (a
    tangent pointing away from the target would loop out and back) — the
    tangents are halved until it fits; at zero the bridge is the chord itself,
    so the cap is always met.
    """
    p0, p1 = np.asarray(p0, dtype=float), np.asarray(p1, dtype=float)
    gap = float(np.hypot(*(p1 - p0)))
    if gap <= 1e-9:
        return p1[None, :]
    n = max(2, int(np.ceil(gap / step_px)) + 1)
    u = np.linspace(0.0, 1.0, n)[1:]
    h00 = 2 * u**3 - 3 * u**2 + 1
    h10 = u**3 - 2 * u**2 + u
    h01 = -2 * u**3 + 3 * u**2
    h11 = u**3 - u**2
    chord = (p1 - p0) / gap
    normal = np.array([-chord[1], chord[0]])
    scale = gap
    for _ in range(8):
        m0, m1 = np.asarray(t0, dtype=float) * scale, np.asarray(t1, dtype=float) * scale
        pts = h00[:, None] * p0 + h10[:, None] * m0 + h01[:, None] * p1 + h11[:, None] * m1
        rel = pts - p0
        along = rel @ chord
        lateral = np.abs(rel @ normal)
        overshoot = np.maximum(0.0, np.maximum(-along, along - gap))
        if float(np.hypot(lateral, overshoot).max()) <= lateral_cap_px:
            return pts
        scale *= 0.5
    return p0 + (p1 - p0) * u[:, None]


def assemble(
    strands: Sequence[Strand],
    states: Sequence[tuple[int, int, int] | None],
    seed: Seed,
    xh: float,
    weights: TintenpfadWeights,
) -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray], list[np.ndarray], dict[str, int]]:
    """Decoded states → pen runs of strand pixels (+ bridges), each vertex with
    its slot label, its kind (0 rail · 1 bridge) and the seed sample that laid it."""
    runs: list[list[np.ndarray]] = []
    labels: list[list[int]] = []
    kinds: list[list[int]] = []
    samples: list[list[int]] = []
    n_jump = n_paper_bridges = n_hairpin = n_paper_lifts = 0
    ride_cap = weights.ride_cap_xh * xh
    jump_r = weights.jump_radius_xh * xh
    lateral_cap = weights.bridge_lateral_cap_xh * xh
    paper_run = 0
    prev: tuple[int, int, int] | None = None

    def emit(pt: np.ndarray, k: int, kind: int) -> None:
        runs[-1].append(np.asarray(pt, dtype=float))
        labels[-1].append(int(seed.slot[k]))
        kinds[-1].append(kind)
        samples[-1].append(k)

    def bridge_to(ps: tuple[int, int, int], st: tuple[int, int, int], k: int) -> None:
        s0, i0, d0 = ps
        s1, i1, d1 = st
        p0, p1 = strands[s0].points[i0], strands[s1].points[i1]
        if weights.bridge == "hermite":
            pts = hermite_bridge(
                p0, strands[s0].tan[i0] * d0, p1, strands[s1].tan[i1] * d1, BRIDGE_STEP_PX, lateral_cap
            )
            for q in pts:
                emit(q, k, 1)
        else:
            emit(p1, k, 1)

    def rail_between(s: int, pi: int, i: int, pd: int, d: int) -> tuple[list[int], bool]:
        """Indices to lay after `pi` up to `i` on strand `s`, and whether it is a hairpin."""
        pts = strands[s].points
        n_pts = len(pts)
        if strands[s].closed:
            delta = (i - pi) % n_pts
            if delta > n_pts / 2:
                delta -= n_pts
            if d == pd:
                return ([(pi + d * q) % n_pts for q in range(1, abs(delta) + 1)] if delta * d > 0 else []), False
            sgn = 1 if delta > 0 else -1
            return [(pi + sgn * q) % n_pts for q in range(1, abs(delta) + 1)], True
        if d == pd:
            step = 1 if d > 0 else -1
            return (list(range(pi + step, i + step, step)) if (i - pi) * d > 0 else []), False
        step = 1 if i > pi else -1
        return (list(range(pi + step, i + step, step)) if i != pi else []), True

    for k, st in enumerate(states):
        lift = k > 0 and seed.stroke[k] != seed.stroke[k - 1]
        if lift:
            prev = None
            paper_run = 0
        if st is None:
            if prev is not None:
                paper_run += 1
            continue
        s, i, d = st
        pts = strands[s].points
        if prev is not None and paper_run and not lift:
            # A paper gap between two boarded pixels: the rail when it is a
            # legal forward ride (the seed merely sampled nothing there), a
            # bridge when within the jump radius, a pen LIFT otherwise.
            ps, pi, pd = prev
            legal_ride = False
            if s == ps:
                n_pts = len(pts)
                delta = (i - pi) * pd
                if strands[s].closed:
                    delta = delta % n_pts
                    delta = delta - n_pts if delta > n_pts / 2 else delta
                legal_ride = -weights.back_tol_px <= delta <= ride_cap * (paper_run + 1) and d == pd
            gap = float(np.hypot(*(pts[i] - strands[ps].points[pi])))
            if not legal_ride and gap > jump_r:
                n_paper_lifts += 1
                prev = None
            elif not legal_ride:
                n_paper_bridges += 1
                bridge_to(prev, st, k)
                prev = st
                paper_run = 0
                continue
        paper_run = 0
        if prev is None or lift:
            if runs and len(runs[-1]) < 2:
                runs.pop()
                labels.pop()
                kinds.pop()
                samples.pop()
            runs.append([])
            labels.append([])
            kinds.append([])
            samples.append([])
            emit(pts[i], k, 0)
            prev = st
            continue
        ps, pi, pd = prev
        if s == ps:
            rng, hairpin = rail_between(s, pi, i, pd, d)
            n_hairpin += int(hairpin)
            for q in rng:
                emit(pts[q], k, 0)
        else:
            n_jump += 1
            bridge_to(prev, st, k)
        prev = st
    out_runs, out_labels, out_kinds, out_samples = [], [], [], []
    for r, lab, kd, sm in zip(runs, labels, kinds, samples, strict=True):
        if len(r) < 2:
            continue
        arr = np.asarray(r, dtype=float)
        keep = np.ones(len(arr), dtype=bool)
        keep[1:] = np.hypot(*np.diff(arr, axis=0).T) > 1e-9
        out_runs.append(arr[keep])
        out_labels.append(np.asarray(lab)[keep])
        out_kinds.append(np.asarray(kd)[keep])
        out_samples.append(np.asarray(sm)[keep])
    counts = {"jumps": n_jump, "paper_bridges": n_paper_bridges, "hairpins": n_hairpin, "paper_lifts": n_paper_lifts}
    return out_runs, out_labels, out_kinds, out_samples, counts


def extend_tip(points: np.ndarray, edt: np.ndarray, cap_px: float, *, at_end: bool, step_px: float = 0.5) -> np.ndarray:
    """The run walked on past its end along its end tangent, to the ink's tip.

    Steps of `step_px` while the point stays inside the ink and the distance
    transform does not RISE (rising means the walk entered a wider body — a
    junction, not a tip); at most `cap_px`. Returns the points to append (in
    walking order), possibly none.
    """
    pts = np.asarray(points, dtype=float)
    if len(pts) < 3:
        return np.zeros((0, 2))
    tail = pts[-4:] if at_end else pts[:4][::-1]
    v = tail[-1] - tail[0]
    nv = float(np.hypot(*v))
    if nv <= 1e-9:
        return np.zeros((0, 2))
    v = v / nv
    h, w = edt.shape
    origin = tail[-1]
    f0 = float(map_coordinates(edt, [[origin[1]], [origin[0]]], order=1, mode="constant", cval=0.0)[0])
    out = []
    walked = 0.0
    last = f0
    while walked + step_px <= cap_px:
        walked += step_px
        p = origin + v * walked
        if not (0 <= p[0] <= w - 1 and 0 <= p[1] <= h - 1):
            break
        f = float(map_coordinates(edt, [[p[1]], [p[0]]], order=1, mode="constant", cval=0.0)[0])
        if f <= 0.3 or f > last + 0.25:
            break
        out.append(p)
        last = f
    return np.asarray(out).reshape(-1, 2)


def extend_tips(
    runs: list[np.ndarray],
    labels: list[np.ndarray],
    kinds: list[np.ndarray],
    samples: list[np.ndarray],
    edt: np.ndarray,
    cap_px: float,
) -> int:
    """Both ends of every run extended in place; returns the number of ends that moved."""
    moved = 0
    for i, r in enumerate(runs):
        head = extend_tip(r, edt, cap_px, at_end=False)
        tail = extend_tip(r, edt, cap_px, at_end=True)
        if len(head):
            runs[i] = np.vstack([head[::-1], runs[i]])
            labels[i] = np.concatenate([np.full(len(head), labels[i][0]), labels[i]])
            kinds[i] = np.concatenate([np.zeros(len(head), dtype=int), kinds[i]])
            samples[i] = np.concatenate([np.full(len(head), samples[i][0]), samples[i]])
            moved += 1
        if len(tail):
            runs[i] = np.vstack([runs[i], tail])
            labels[i] = np.concatenate([labels[i], np.full(len(tail), labels[i][-1])])
            kinds[i] = np.concatenate([kinds[i], np.zeros(len(tail), dtype=int)])
            samples[i] = np.concatenate([samples[i], np.full(len(tail), samples[i][-1])])
            moved += 1
    return moved


def _edt_at(edt: np.ndarray, p: np.ndarray) -> float:
    return float(map_coordinates(edt, [[p[1]], [p[0]]], order=1, mode="constant", cval=0.0)[0])


def read_tip(
    origin: np.ndarray,
    direction: np.ndarray,
    mask: np.ndarray,
    edt: np.ndarray,
    cap_px: float,
    *,
    step_px: float = 0.5,
    rise_px: float = 0.25,
) -> tuple[np.ndarray, str]:
    """The ink read on from a free strand end to the end of the mask.

    From `origin` along `direction` in steps of `step_px`; every step is
    re-centred on the apex of the EDT tent across the stroke (the sub-pixel
    rail's own reading) and the direction is re-read from the walked points, so
    the walk follows the ridge of the ink rather than a straight line. It stops
    at the first step whose nearest pixel is not ink (the tip), at a step where
    the EDT RISES by more than `rise_px` (the walk entered a wider body — a
    junction, not a tip) or at `cap_px`. Returns the points to append (in
    walking order) and the stop reason (`mask` · `rise` · `cap` · `edge`).
    """
    h, w = mask.shape
    v = np.asarray(direction, dtype=float)
    nv = float(np.hypot(*v))
    if nv <= 1e-9:
        return np.zeros((0, 2)), "edge"
    v = v / nv
    p = np.asarray(origin, dtype=float).copy()
    trail = [p]
    out: list[np.ndarray] = []
    last = _edt_at(edt, p)
    for _ in range(int(cap_px // step_px)):
        q = p + v * step_px
        normal = np.array([-v[1], v[0]])
        f_plus, f_minus = _edt_at(edt, q + normal), _edt_at(edt, q - normal)
        if f_plus > 0.0 and f_minus > 0.0:
            q = q + normal * float(np.clip(0.5 * (f_plus - f_minus), -SUBPIXEL_MAX_PX, SUBPIXEL_MAX_PX))
        ix, iy = int(round(q[0])), int(round(q[1]))
        if not (0 <= ix < w and 0 <= iy < h):
            return np.asarray(out).reshape(-1, 2), "edge"
        if not mask[iy, ix]:
            return np.asarray(out).reshape(-1, 2), "mask"
        f = _edt_at(edt, q)
        if f > last + rise_px:
            return np.asarray(out).reshape(-1, 2), "rise"
        out.append(q)
        trail.append(q)
        # Direction over ~2 px of walked trail: long enough that the lateral
        # re-centring does not swing it, short enough to follow a curving tip.
        dv = q - trail[max(0, len(trail) - 5)]
        if float(np.hypot(*dv)) > 1e-9:
            v = dv / float(np.hypot(*dv))
        p, last = q, f
    return np.asarray(out).reshape(-1, 2), "cap"


def _pixel_key(p: np.ndarray) -> tuple[float, float]:
    return (round(float(p[0]), 6), round(float(p[1]), 6))


def tip_tail(strand: Strand, i: int, travel: np.ndarray, visited: tuple[int, int]) -> tuple[list[int], np.ndarray, str]:
    """What lies beyond pixel `i` of `strand` in the direction `travel` (a unit
    vector along the pen's motion at that end): the indices of the strand's own
    unvisited pixels up to its end, the OUTWARD direction at that end, and why
    the tail is not readable — `not_free` (the strand's end there is a junction
    end), `junction` (the strand passes a node before its end), `visited`
    (another run laid that tail already), or "" when it is."""
    n = len(strand.points)
    toward_last = float(travel @ strand.tan[i]) >= 0.0
    lo, hi = visited
    if strand.closed or not strand.free_ends[1 if toward_last else 0]:
        return [], np.zeros(2), "not_free"
    if toward_last:
        if i < hi:
            return [], np.zeros(2), "visited"
        if np.any(strand.junction_idx > i):
            return [], np.zeros(2), "junction"
        rng = list(range(i + 1, n))
    else:
        if i > lo:
            return [], np.zeros(2), "visited"
        if np.any(strand.junction_idx < i):
            return [], np.zeros(2), "junction"
        rng = list(range(i - 1, -1, -1))
    k = min(3, n - 1)
    outward = strand.points[-1] - strand.points[-1 - k] if toward_last else strand.points[0] - strand.points[k]
    return rng, outward, ""


def read_tips(
    runs: list[np.ndarray],
    labels: list[np.ndarray],
    kinds: list[np.ndarray],
    samples: list[np.ndarray],
    strands: Sequence[Strand],
    states: Sequence[tuple[int, int, int] | None],
    mask: np.ndarray,
    cap_px: float,
) -> dict[str, Any]:
    """Both ends of every run read on to the ink's tip, in place.

    A run ends on the pixel the seed's last sample boarded, which is short of
    the strand's end whenever the composition is shorter than the ink. Where
    the strand runs on in the travel direction to a FREE end — no junction
    node before it, no other run on that tail — its remaining pixels are laid
    (`rail_points`, skeleton pixels), and from the free end the EDT-ridge walk
    of `read_tip` reads on to the end of the mask (`walk_points`). Tip vertices
    carry kind 2; every appended vertex is checked against the mask, and the
    counts returned are the proof that nothing was invented.
    """
    edt = distance_transform_edt(np.asarray(mask, dtype=bool))
    pixel_of: dict[tuple[float, float], list[tuple[int, int]]] = {}
    for si, s in enumerate(strands):
        for pi, p in enumerate(s.points):
            pixel_of.setdefault(_pixel_key(p), []).append((si, pi))
    visited: dict[int, tuple[int, int]] = {}
    for st in states:
        if st is None:
            continue
        lo, hi = visited.get(st[0], (st[1], st[1]))
        visited[st[0]] = (min(lo, st[1]), max(hi, st[1]))
    stops = {"mask": 0, "rise": 0, "cap": 0, "edge": 0}
    blocked = {"not_free": 0, "junction": 0, "visited": 0, "ambiguous": 0}
    ends_read = rail_added = rail_inside = walk_added = walk_inside = 0
    rail_lengths: list[float] = []
    walk_lengths: list[float] = []
    h, w = mask.shape

    def in_mask(pts: np.ndarray) -> int:
        ix = np.rint(pts[:, 0]).astype(int)
        iy = np.rint(pts[:, 1]).astype(int)
        ok = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
        hit = np.zeros(len(pts), dtype=bool)
        hit[ok] = mask[iy[ok], ix[ok]]
        return int(hit.sum())

    for ri, r in enumerate(runs):
        for at_end in (False, True):
            end_pt = r[-1] if at_end else r[0]
            travel = (r[-1] - r[-2]) if at_end else (r[0] - r[1])
            nt = float(np.hypot(*travel))
            found = pixel_of.get(_pixel_key(end_pt), [])
            if len(found) != 1 or nt <= 1e-9:
                blocked["ambiguous"] += 1
                continue
            si, pi = found[0]
            strand = strands[si]
            rng, outward, why = tip_tail(strand, pi, travel / nt, visited.get(si, (pi, pi)))
            if why:
                blocked[why] += 1
                continue
            rail = strand.points[rng] if rng else np.zeros((0, 2))
            tip_start = rail[-1] if len(rail) else end_pt
            walk, stop = read_tip(tip_start, outward, mask, edt, cap_px)
            stops[stop] += 1
            pts = np.vstack([rail, walk])
            if not len(pts):
                continue
            ends_read += 1
            rail_added += len(rail)
            rail_inside += in_mask(rail) if len(rail) else 0
            walk_added += len(walk)
            walk_inside += in_mask(walk) if len(walk) else 0
            rail_lengths.append(polyline_len(np.vstack([end_pt[None, :], rail])) if len(rail) else 0.0)
            walk_lengths.append(polyline_len(np.vstack([tip_start[None, :], walk])) if len(walk) else 0.0)
            if at_end:
                runs[ri] = np.vstack([runs[ri], pts])
                labels[ri] = np.concatenate([labels[ri], np.full(len(pts), labels[ri][-1])])
                kinds[ri] = np.concatenate([kinds[ri], np.full(len(pts), 2, dtype=int)])
                samples[ri] = np.concatenate([samples[ri], np.full(len(pts), samples[ri][-1])])
            else:
                runs[ri] = np.vstack([pts[::-1], runs[ri]])
                labels[ri] = np.concatenate([np.full(len(pts), labels[ri][0]), labels[ri]])
                kinds[ri] = np.concatenate([np.full(len(pts), 2, dtype=int), kinds[ri]])
                samples[ri] = np.concatenate([np.full(len(pts), samples[ri][0]), samples[ri]])
    return {
        "free_ends": int(sum(int(s.free_ends[0]) + int(s.free_ends[1]) for s in strands)),
        "run_ends": 2 * len(runs),
        "ends_read": ends_read,
        "blocked": blocked,
        "rail_points": rail_added,
        "rail_points_in_mask": rail_inside,
        "rail_len_px_max": round(max(rail_lengths), 2) if rail_lengths else 0.0,
        "rail_len_px_total": round(sum(rail_lengths), 2),
        "walk_points": walk_added,
        "walk_points_in_mask": walk_inside,
        "walk_len_px_max": round(max(walk_lengths), 2) if walk_lengths else 0.0,
        "walk_len_px_total": round(sum(walk_lengths), 2),
        "stops": stops,
    }


def resample_run(points: np.ndarray, step_px: float, *carried: np.ndarray) -> tuple[np.ndarray, ...]:
    """Arc-length-uniform vertices along the polyline (endpoints exact), every
    carried per-vertex array re-read at the nearest original vertex."""
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    arc = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(arc[-1])
    if total <= 0.0 or step_px <= 0.0 or len(pts) < 2:
        return (pts, *carried)
    n = max(2, int(round(total / step_px)) + 1)
    t = np.linspace(0.0, total, n)
    xy = np.column_stack([np.interp(t, arc, pts[:, 0]), np.interp(t, arc, pts[:, 1])])
    src = np.rint(np.interp(t, arc, np.arange(len(pts)))).astype(int)
    return (xy, *(np.asarray(c)[src] for c in carried))


def spans_of(labels: Sequence[np.ndarray]) -> list[list[list[int]]]:
    """`[[slot, first, last], …]` per run; connector samples inherit the nearest letter label."""
    spans = []
    for lab in labels:
        lab = np.asarray(lab).copy()
        idx = np.flatnonzero(lab >= 0)
        if len(idx):
            for i in np.flatnonzero(lab < 0):
                lab[i] = lab[idx[np.argmin(np.abs(idx - i))]]
        run_spans, start = [], 0
        for i in range(1, len(lab) + 1):
            if i == len(lab) or lab[i] != lab[start]:
                run_spans.append([int(lab[start]), int(start), int(i - 1)])
                start = i
        spans.append(run_spans)
    return spans


# ---------------------------------------------------------------- sensors


def excursions_of(
    points: np.ndarray, kinds: np.ndarray, *, win: float = 0.30, amp: float = 0.15, net: float = 0.10
) -> tuple[int, int, float]:
    """Out-and-back excursions of one run in x-height units: windows of at most
    `win` of arc whose ends are within `net` while the path leaves by more
    than `amp`. Counted as bridge-borne when a bridge vertex lies inside (the
    judges' „chord chatter"), rail-borne otherwise (a hairpin on the ink).
    Returns (bridge-borne, rail-borne, worst amplitude)."""
    p = np.asarray(points, dtype=float).reshape(-1, 2)
    n = len(p)
    if n < 3:
        return 0, 0, 0.0
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])
    bridge = rail = 0
    worst = 0.0
    i = 0
    while i < n - 2:
        hit = None
        j = i + 2
        while j < n and s[j] - s[i] <= win:
            if float(np.hypot(*(p[j] - p[i]))) <= net:
                a = float(np.max(np.hypot(*(p[i + 1 : j] - p[i]).T)))
                if a > amp:
                    hit = (j, a)
                    break
            j += 1
        if hit is None:
            i += 1
            continue
        j, a = hit
        if np.any(np.asarray(kinds)[i + 1 : j + 1] == 1):
            bridge += 1
        else:
            rail += 1
        worst = max(worst, a)
        i = j
    return bridge, rail, worst


def turn_angles_deg(points: np.ndarray) -> np.ndarray:
    """The turn at every interior vertex of a polyline (zero-length segments dropped)."""
    p = np.asarray(points, dtype=float).reshape(-1, 2)
    seg = np.diff(p, axis=0)
    norm = np.linalg.norm(seg, axis=1)
    seg = seg[norm > 1e-12]
    norm = norm[norm > 1e-12]
    if len(seg) < 2:
        return np.zeros(0)
    unit = seg / norm[:, None]
    cos = np.clip(np.einsum("ij,ij->i", unit[:-1], unit[1:]), -1.0, 1.0)
    return np.degrees(np.arccos(cos))


def kink_reading(strokes_units: Sequence[np.ndarray]) -> dict[str, float]:
    """`core.continuity` on the emitted runs: median kink and events per 100 measured samples."""
    n_events = n_meas = 0
    kinks = []
    for pts in strokes_units:
        prof = stroke_profile(np.asarray(pts, dtype=float))
        if prof is None:
            continue
        measured = prof["inside"] & ~prof["corner"]
        n_events += len(kink_events(prof["kink"], measured, prof["pts"], prof["s"]))
        n_meas += int(measured.sum())
        kinks.append(prof["kink"][measured])
    k = np.concatenate(kinks) if kinks else np.zeros(1)
    return {
        "kink_median_deg": round(float(np.median(k)), 2),
        "kink_p90_deg": round(float(np.percentile(k, 90)), 2),
        "kink_per100": round(100.0 * n_events / max(1, n_meas), 2),
    }


def displacement_coherence(
    runs_px: Sequence[np.ndarray], samples: Sequence[np.ndarray], seed: Seed
) -> dict[str, float]:
    """How coherently neighbouring vertices moved away from the seed.

    Each vertex's displacement is `vertex − the seed sample that decoded it`;
    reported are the angle between neighbouring displacement vectors and the
    ratio of the displacement's second difference to its magnitude — the
    author's wave, read off the delivered path.
    """
    angles, ratios = [], []
    for r, sm in zip(runs_px, samples, strict=True):
        d = np.asarray(r, dtype=float) - seed.xy[np.asarray(sm)]
        if len(d) < 3:
            continue
        nrm = np.linalg.norm(d, axis=1)
        ok = (nrm[:-1] > 1e-9) & (nrm[1:] > 1e-9)
        cos = np.einsum("ij,ij->i", d[:-1], d[1:]) / np.where(ok, nrm[:-1] * nrm[1:], 1.0)
        angles.append(np.degrees(np.arccos(np.clip(cos[ok], -1.0, 1.0))))
        second = np.linalg.norm(d[2:] - 2 * d[1:-1] + d[:-2], axis=1)
        mid = nrm[1:-1]
        ratios.append(second[mid > 0.5] / mid[mid > 0.5])
    a = np.concatenate(angles) if angles else np.zeros(1)
    q = np.concatenate(ratios) if ratios else np.zeros(1)
    return {
        "disp_angle_median_deg": round(float(np.median(a)), 2),
        "disp_angle_p90_deg": round(float(np.percentile(a, 90)), 2),
        "disp_angle_max_deg": round(float(a.max()), 2),
        "disp_second_ratio_median": round(float(np.median(q)), 4),
        "disp_second_ratio_p90": round(float(np.percentile(q, 90)), 4),
    }


def span_checks(
    runs_px: Sequence[np.ndarray],
    labels: Sequence[np.ndarray],
    states: Sequence[tuple[int, int, int] | None],
    seed: Seed,
    xh: float,
) -> dict[str, Any]:
    """The letter-assignment claim measured: label backsteps within runs, the
    agreement with a monotone DTW of the finished path against the seed, and
    per slot the share of its seed samples that boarded ink."""
    filled = []
    for lab in labels:
        lab = np.asarray(lab).copy()
        idx = np.flatnonzero(lab >= 0)
        for i in np.flatnonzero(lab < 0):
            lab[i] = lab[idx[np.argmin(np.abs(idx - i))]] if len(idx) else -1
        filled.append(lab)
    backsteps = int(sum(int((np.diff(lab) < 0).sum()) for lab in filled))
    path = np.vstack(runs_px) / xh
    order = np.argsort(seed.stroke, kind="stable")
    letters = seed.slot >= 0
    ref = seed.xy[order][letters[order]] / xh
    ref_slot = seed.slot[order][letters[order]]
    agreement = None
    if len(ref) > 1 and len(path) > 1:
        pairs = ruler_dtw(path, ref).pairs
        dtw_label = np.full(len(path), -1)
        dtw_label[pairs[:, 0]] = ref_slot[pairs[:, 1]]
        mine = np.concatenate(filled)
        agreement = round(float((dtw_label == mine).mean()), 3)
    coverage = {}
    for s in sorted({int(v) for v in seed.slot if v >= 0}):
        sel = seed.slot == s
        boarded = sum(1 for k in np.flatnonzero(sel) if states[k] is not None)
        coverage[str(s)] = round(boarded / max(1, int(sel.sum())), 3)
    return {"span_backsteps": backsteps, "label_agreement": agreement, "slot_boarded_share": coverage}


# ----------------------------------------------------------------- the word


def follow_word(case: WordCase, weights: TintenpfadWeights) -> dict[str, Any]:
    """One word, both stages — the candidate-shaped row (`follow_derived`'s shape)."""
    base = {"kind": case.kind, "specimen_id": case.id, "word": case.word}
    started = time.perf_counter()
    if not case.scorable:
        return {
            **base,
            "strokes": [],
            "registration_px": {},
            "xh_px": None,
            "status": STATUS_SKIPPED,
            "detail": "frozen as unscorable (a needed template is unauthored)",
            "meta": {},
        }
    if not case.has_specimen or case.mask is None:
        return {
            **base,
            "strokes": [],
            "registration_px": {},
            "xh_px": None,
            "status": STATUS_SKIPPED,
            "detail": "no specimen",
            "meta": {},
        }
    result = derive_word(case)
    if result.report is None or result.report.get("failed") or not result.registration:
        detail = (result.report or {}).get("reason") or (result.report or {}).get("detail") or "composition failed"
        return {
            **base,
            "strokes": [],
            "registration_px": {},
            "xh_px": None,
            "status": STATUS_FAILED,
            "detail": str(detail),
            "meta": {},
        }
    xh = float(result.xh_px)
    case_ev, _ = ink_evidence_case(case, InkEvidenceOptions(paper_fraction=INK_EVIDENCE_PAPER_FRACTION))
    diag: dict[str, Any] = {}
    strands = strands_of(np.asarray(case_ev.skel, dtype=bool), xh, weights, diag)
    if weights.rail == "subpixel":
        refine_strands(strands, np.asarray(case_ev.mask, dtype=bool), weights)
    affreg = None
    if weights.affine_seed:
        affreg = register_letters(case_ev, result)
        diag["affine_gain"] = {int(s): round(float(v["cost_before"] - v["cost_after"]), 4) for s, v in affreg.items()}
    seed = seed_samples(result, xh, weights, affreg)
    t_seed = time.perf_counter()
    if not strands:
        return {
            **base,
            "strokes": [],
            "registration_px": {},
            "xh_px": None,
            "status": STATUS_FAILED,
            "detail": "no strand survived stage 1",
            "meta": {"tintenpfad": diag},
        }
    states, total, ddiag = decode_with_hysteresis(strands, seed, xh, weights)
    diag.update(ddiag)
    runs, labels, kinds, samples, counts = assemble(strands, states, seed, xh, weights)
    diag.update(counts)
    if not runs:
        return {
            **base,
            "strokes": [],
            "registration_px": {},
            "xh_px": None,
            "status": STATUS_FAILED,
            "detail": "nothing decoded onto the ink",
            "meta": {"tintenpfad": diag},
        }
    mask = np.asarray(case_ev.mask, dtype=bool)
    if weights.tip_read:
        diag["tip_read"] = read_tips(runs, labels, kinds, samples, strands, states, mask, weights.tip_read_cap_xh * xh)
    if weights.tip_extend_xh > 0.0:
        edt = distance_transform_edt(mask)
        diag["tips_extended"] = extend_tips(runs, labels, kinds, samples, edt, weights.tip_extend_xh * xh)
    raw_units = [_px_to_word_units(r[:, 0], r[:, 1], xh, _registration(result)) for r in runs]
    diag["raw_chain"] = {
        **kink_reading(raw_units),
        "vertices": int(sum(len(r) for r in runs)),
        **_step_and_turn(raw_units),
    }
    if weights.resample_step_xh > 0.0:
        resampled = [
            resample_run(r, weights.resample_step_xh * xh, lab, kd, sm)
            for r, lab, kd, sm in zip(runs, labels, kinds, samples, strict=True)
        ]
        runs = [r[0] for r in resampled]
        labels = [r[1] for r in resampled]
        kinds = [r[2] for r in resampled]
        samples = [r[3] for r in resampled]
    if weights.tip_read:
        # The no-invention proof repeated on the DELIVERED vertices: every
        # resampled tip vertex must still sit on ink.
        tip_pts = np.vstack([r[np.asarray(k) == 2] for r, k in zip(runs, kinds, strict=True)] or [np.zeros((0, 2))])
        ix, iy = np.rint(tip_pts[:, 0]).astype(int), np.rint(tip_pts[:, 1]).astype(int)
        ok = (ix >= 0) & (ix < mask.shape[1]) & (iy >= 0) & (iy < mask.shape[0])
        diag["tip_read"]["resampled_total"] = int(len(tip_pts))
        diag["tip_read"]["resampled_in_mask"] = int(mask[iy[ok], ix[ok]].sum())
    reg = _registration(result)
    units = [_px_to_word_units(r[:, 0], r[:, 1], xh, reg) for r in runs]
    visited = {st[0] for st in states if st is not None}
    skel_len = sum(s.length for s in strands)
    unvisited_len = sum(s.length for i, s in enumerate(strands) if i not in visited)
    exc = [excursions_of(u, kd) for u, kd in zip(units, kinds, strict=True)]
    diag.update(
        {
            "runs": len(runs),
            "seed_lifts": int(seed.stroke.max()),
            "paper_samples": int(sum(1 for s in states if s is None)),
            "seed_samples": int(len(states)),
            "strands_unvisited": len(strands) - len(visited),
            "ink_unvisited_share": round(unvisited_len / skel_len, 3) if skel_len else 0.0,
            "decode_cost": round(total, 1),
            "path_len_xh": round(sum(polyline_len(r) for r in runs) / xh, 2),
            "bridge_vertices": int(sum(int((np.asarray(k) == 1).sum()) for k in kinds)),
            "excursions_bridge": int(sum(e[0] for e in exc)),
            "excursions_rail": int(sum(e[1] for e in exc)),
            "excursion_worst_xh": round(max(e[2] for e in exc), 3),
            **_step_and_turn(units),
            **kink_reading(units),
            **displacement_coherence(runs, samples, seed),
            **span_checks(runs, labels, states, seed, xh),
            "seconds_seed": round(t_seed - started, 2),
            "seconds": round(time.perf_counter() - started, 2),
        }
    )
    strokes = cap_word_strokes([u.tolist() for u in units], label=f"{case.id} (tintenpfad)")
    return {
        **base,
        "strokes": strokes,
        "registration_px": {
            "tx": round(float(reg["tx"]), 2),
            "ty": round(float(reg["ty"]), 2),
            "baseline_row": int(reg["baseline_row"]),
        },
        "xh_px": round(xh, 2),
        "status": STATUS_OK,
        "detail": "",
        "meta": {
            "fit_path": "tintenpfad",
            "weights": asdict(weights),
            "tintenpfad": diag,
            "letter_spans": spans_of(labels),
            "timings": {"seconds": diag["seconds"]},
        },
    }


def _registration(result: WordDeriveResult) -> dict[str, float]:
    return {
        "tx": float(result.registration["tx"]),
        "ty": float(result.registration["ty"]),
        "baseline_row": float(result.baseline_row),
    }


def _step_and_turn(strokes_units: Sequence[np.ndarray]) -> dict[str, float]:
    steps = np.concatenate([np.hypot(*np.diff(np.asarray(s), axis=0).T) for s in strokes_units if len(s) > 1])
    turns = np.concatenate([turn_angles_deg(s) for s in strokes_units]) if strokes_units else np.zeros(0)
    if not len(turns):
        turns = np.zeros(1)
    return {
        "step_median_xh": round(float(np.median(steps)), 4),
        "step_p90_xh": round(float(np.percentile(steps, 90)), 4),
        "step_max_xh": round(float(steps.max()), 4),
        "turn_median_deg": round(float(np.median(turns)), 2),
        "turn_p75_deg": round(float(np.percentile(turns, 75)), 2),
        "turn_p90_deg": round(float(np.percentile(turns, 90)), 2),
        "turn_over30_share": round(float((turns > 30.0).mean()), 4),
    }


def follow_case(case: WordCase, weights: TintenpfadWeights | None = None) -> dict[str, Any]:
    """`follow_word` that never raises: one word must not take a sweep down."""
    weights = weights or TintenpfadWeights()
    try:
        return follow_word(case, weights)
    except Exception as exc:  # noqa: BLE001 — reported per row, the doctrine of every bench tool
        return {
            "kind": case.kind,
            "specimen_id": case.id,
            "word": case.word,
            "strokes": [],
            "registration_px": {},
            "xh_px": None,
            "status": STATUS_FAILED,
            "detail": f"{type(exc).__name__}: {exc}",
            "meta": {},
        }


def _run_one(job: tuple[WordCase, TintenpfadWeights]) -> dict[str, Any]:
    case, weights = job
    info = follow_case(case, weights)
    d = info.get("meta", {}).get("tintenpfad", {})
    if info["status"] == STATUS_OK:
        print(
            f"  {case.id:<12} runs {d['runs']:2d} strands {d['strands']:3d} jumps {d['jumps']:3d} hairpins {d['hairpins']:2d}"
            f" plifts {d['paper_lifts']:2d} paper {d['paper_samples']:3d}/{d['seed_samples']:4d} unvisited {d['ink_unvisited_share']:.2f}"
            f" exc b/r {d['excursions_bridge']}/{d['excursions_rail']} reentry {d['reentries_forbidden']}/{d['reentries_left']}"
            f" kink {d['kink_median_deg']:5.2f}° turn90 {d['turn_p90_deg']:5.1f}° {d['seconds']:5.1f}s"
            + (
                f" tips {d['tip_read']['ends_read']}/{d['tip_read']['run_ends']}"
                f" rail +{d['tip_read']['rail_points']} walk +{d['tip_read']['walk_points']}"
                f" in-mask {d['tip_read']['walk_points_in_mask']}"
                if "tip_read" in d
                else ""
            ),
            flush=True,
        )
    else:
        print(f"  {case.id:<12} {info['status']:<8} {info['detail']}", flush=True)
    return info


def run_cases(cases: Sequence[WordCase], weights: TintenpfadWeights, *, jobs: int = 1) -> list[dict[str, Any]]:
    """Every case at ONE configuration, in fixture order (pooling is per case)."""
    payloads = [(c, weights) for c in cases]
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            return list(pool.map(_run_one, payloads))
    return [_run_one(p) for p in payloads]


def tintenpfad_payload(
    infos: Sequence[dict[str, Any]], *, style: str, source_id: str, which: str, label: str, weights: TintenpfadWeights
) -> dict[str, Any]:
    """`follow.candidate_payload` with this tool's name and weights."""
    payload = candidate_payload(infos, style=style, source_id=source_id, which=which, label=label)
    payload["tool"] = TINTENPFAD_TOOL_NAME
    payload["version"] = TINTENPFAD_ARTIFACT_VERSION
    payload["weights"] = asdict(weights)
    payload["provisional"] = True
    return payload


# ----------------------------------------------------------------- the CLI


def weights_from_overrides(base: TintenpfadWeights, overrides: Sequence[str]) -> TintenpfadWeights:
    """`NAME=value` pairs applied to a configuration, typed by the field's default."""
    kwargs: dict[str, Any] = {}
    known = {f.name: f for f in fields(TintenpfadWeights)}
    for item in overrides:
        name, _, raw = item.partition("=")
        name = name.strip()
        if name not in known:
            raise SystemExit(f"--weight {name!r} is not a TintenpfadWeights field; known: {', '.join(sorted(known))}")
        current = getattr(base, name)
        if isinstance(current, bool):
            kwargs[name] = raw.strip().lower() in ("1", "true", "on", "yes")
        elif isinstance(current, int):
            kwargs[name] = int(float(raw))
        elif isinstance(current, float):
            kwargs[name] = float(raw)
        else:
            kwargs[name] = raw.strip()
    return replace(base, **kwargs)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pairlab.tintenpfad", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("ids", nargs="*", help="fixture case ids (or words); default: the twelve loop words")
    parser.add_argument("--all", action="store_true", help="every case of the set")
    parser.add_argument("--set", dest="which", default="words", choices=["words", "pairs"])
    parser.add_argument("--style", default="suetterlin")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES_DIR)
    add_expect_root_argument(parser)
    parser.add_argument(
        "--legacy-p5", action="store_true", help="the prototype's measured configuration (ladder row p5)"
    )
    parser.add_argument(
        "--weight",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="override one TintenpfadWeights field (repeatable)",
    )
    parser.add_argument(
        "--jump-radius", type=float, help="jump_radius_xh — the lift-vs-chord choice, presented to the author as a pair"
    )
    parser.add_argument("--board-radius", type=float, help="board_radius_xh")
    parser.add_argument("--turn-cost", type=float, help="turn_cost")
    parser.add_argument("--no-affine-seed", action="store_true", help="seed = the plain composition")
    parser.add_argument("--jobs", type=int, default=1, help="worker processes, pooled over CASES")
    parser.add_argument("--label", default="tintenpfad")
    parser.add_argument("--json", type=Path, help="write the full report here")
    parser.add_argument("--candidate-out", type=Path, help="write a tracebench file-provider candidate here")
    return parser


def weights_from_args(args: argparse.Namespace) -> TintenpfadWeights:
    base = LEGACY_P5 if args.legacy_p5 else TintenpfadWeights()
    kwargs: dict[str, Any] = {}
    if args.jump_radius is not None:
        kwargs["jump_radius_xh"] = args.jump_radius
    if args.board_radius is not None:
        kwargs["board_radius_xh"] = args.board_radius
    if args.turn_cost is not None:
        kwargs["turn_cost"] = args.turn_cost
    if args.no_affine_seed:
        kwargs["affine_seed"] = False
    return weights_from_overrides(replace(base, **kwargs), args.weight)


def main() -> None:
    args = build_parser().parse_args()
    ids = list(args.ids) if args.ids or args.all else list(LOOP_WORDS)
    started = time.perf_counter()
    try:
        root = fixture_root_for(args.which, style=args.style, fixtures_root=args.fixtures)
    except (KeyError, OSError) as exc:
        raise SystemExit(str(exc)) from None
    root_meta = announce_roots([root], args.expect_root)
    cases = iter_fixture_word_cases(
        which=args.which, style=args.style, only=None if args.all else ids, fixtures_root=args.fixtures
    )
    if not cases:
        raise SystemExit(f"no case matched {ids!r} in the {args.which!r} set")
    weights = weights_from_args(args)
    print(
        f"tintenpfad: {len(cases)} cases · set {args.which} · rail {weights.rail} · candidates {weights.candidates} · bridge {weights.bridge} · reentry {weights.reentry_window} · PROVISIONAL weights"
    )
    infos = run_cases(cases, weights, jobs=max(1, args.jobs))
    runtime = round(time.perf_counter() - started, 1)
    print(f"runtime {runtime}s")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "tool": TINTENPFAD_TOOL_NAME,
            "version": TINTENPFAD_ARTIFACT_VERSION,
            "style": args.style,
            "set": args.which,
            "roots": root_meta,
            "weights": asdict(weights),
            "runtime_s": runtime,
            "rows": [{k: v for k, v in info.items() if k != "strokes"} for info in infos],
        }
        args.json.write_text(json.dumps(report, indent=1, ensure_ascii=False))
        print(f"wrote {args.json}")
    if args.candidate_out:
        payload = tintenpfad_payload(
            infos,
            style=args.style,
            source_id=_source_id_of(args.fixtures, args.style, args.which),
            which=args.which,
            label=args.label,
            weights=weights,
        )
        args.candidate_out.parent.mkdir(parents=True, exist_ok=True)
        args.candidate_out.write_text(json.dumps(payload, ensure_ascii=False))
        print(f"wrote {args.candidate_out} ({len(payload['rows'])} rows, {len(payload['excluded'])} excluded)")


__all__ = [
    "LEGACY_P5",
    "LOOP_WORDS",
    "TINTENPFAD_ARTIFACT_VERSION",
    "TINTENPFAD_TOOL_NAME",
    "Seed",
    "Strand",
    "TintenpfadWeights",
    "assemble",
    "best_matching",
    "decode",
    "decode_with_hysteresis",
    "displacement_coherence",
    "excursions_of",
    "extend_tip",
    "extend_tips",
    "follow_case",
    "follow_word",
    "hermite_bridge",
    "read_tip",
    "read_tips",
    "reentries",
    "refine_strands",
    "resample_run",
    "run_cases",
    "seed_samples",
    "span_checks",
    "spans_of",
    "strand_tangents",
    "strands_of",
    "subpixel_rail",
    "tintenpfad_payload",
    "turn_angles_deg",
    "weights_from_overrides",
]


if __name__ == "__main__":
    main()
