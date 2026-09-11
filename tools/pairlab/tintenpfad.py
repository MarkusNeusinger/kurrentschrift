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
  where the thinning's raster staircase is removed at its source. The
  measured arm `rail="tentfit"` reads the same distance transform wider — a
  least-squares tent over ±2 px along the normal — and `edt_upsample > 1`
  reads it on a finer raster whose boundary is the crop's grey cut by the
  mask's own adaptive threshold inside the mask's edge pixels: the binary
  boundary is a pixel staircase, and the ridge of its distance transform
  inherits that staircase whatever the reading; the grey knows where inside
  the edge pixel the ink ends.
* **Stage 2 — Strang-Dekodierung (order only).** The composed word, placed by
  the frozen registration and per slot moved by the Gauß-Verschiebung
  (`affinereg.register_letters`, the night loop's `--chain-seed affine`), is
  resampled in writing order with a slot label and a stroke index per sample.
  A Viterbi over the seed samples decodes it through the strands: states are
  strand pixels × two travel directions plus one PAPER state; the emission
  prices deviation and tangent disagreement; transitions price a ride along a
  strand per pixel advanced (monotone — never a pixel re-laid), a hairpin on
  the same strand once (`turn_cost`, a pen event), a jump to another strand
  within `jump_radius_xh` by gap and turning (with `self_jump` also to a pixel
  of the SAME strand beyond the ride cap — a loop that returns onto its own
  stem passes one node twice on one strand, and beyond the cap a strand is
  another strand), and every boarding into or out of
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
within the jump radius, and is a pen LIFT otherwise — unless the Tinten-Brücke
(`ink_bridge_xh`, off by default) reads faint ink on the crop across the
straight gap, in which case the gap is bridged like a jump: a hairline the
binarisation lost is ink read, not ink invented. The runs are emitted
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
from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path
from typing import Any

import numpy as np
from scipy.ndimage import binary_dilation, binary_erosion, distance_transform_edt, map_coordinates, zoom
from scipy.spatial import cKDTree
from skimage.filters import threshold_local

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
# The tent fit (`rail="tentfit"`): the apex offset is searched on this grid and
# refined parabolically; a fit needs this many in-ink samples, and a slope this
# steep — a distance transform falls at unit slope, so a much flatter profile
# is a plateau where two strokes fuse, not a tent with a readable apex.
TENTFIT_GRID_PX = 0.02
TENTFIT_MIN_SAMPLES = 4
TENTFIT_MIN_SLOPE = 0.3
# The fine raster (`edt_upsample > 1`) cuts the bilinearly interpolated crop
# with the SAME adaptive threshold the frozen mask came from
# (`core.extract.binarize_adaptive` defaults, used by the fixture export), so
# the fine boundary is the mask's own edge read at sub-pixel precision.
FINE_MASK_BLOCK_PX = 51
FINE_MASK_OFFSET = 0.03


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
    # "subpixel": three-point tent apex on the EDT along the normal · "tentfit":
    # least-squares tent over ±fit_half_px along the normal · "raw": the pixel chain
    rail: str = "subpixel"
    fit_half_px: float = 2.0  # half window of the tent fit along the normal
    fit_step_px: float = 0.5  # sample spacing of the tent fit along the normal
    # 1 = the binary mask's distance transform; > 1 = the same distance
    # transform on a raster this many times finer, whose boundary is the crop's
    # grey cut by the mask's own adaptive threshold inside the mask's edge pixels
    # (measured as arm 3 „Normalen-Fit", not part of the delivered default).
    edt_upsample: int = 1
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
    # Selbstsprung (arm E „fit-absetzer", off by default): beyond the ride cap
    # a strand is another strand. A transition between two pixels of the SAME
    # strand that is neither a ride nor a hairpin (|adv| > ride_cap) is priced
    # like a jump between strands when the pixels lie within `jump_radius_xh`
    # — a loop that returns onto its own stem (the l, the G) passes the same
    # node twice on one strand, and without this the paper state was the only
    # way across: 2 × paper_board + paper_w, a wormhole whose exit landed a
    # lift or a bridge depending on 0.04 px of the rail. A backward step within
    # the cap stays forbidden — never a pixel re-laid. `self_jump_node_px`
    # binds the jump to the NODES the strand passes: both pixels must lie
    # within this many strand pixels of a junction index or a strand end
    # (0 = anywhere on the strand — measured first, and it cut across the G's
    # counter 6 px before the node; the bound version is the delivered arm).
    self_jump: bool = False
    self_jump_node_px: float = 3.0
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
    # Haken-Spitze (arm A of the „Ecken" round, off by default): the tip
    # reading applied at a HAIRPIN on one strand. The decoder turns at the
    # last boarded strand pixel, and the thinning stops half a nib short of
    # the ink's tip, so the corner is cut off and the turn comes too early.
    # With this on, the strand's rest beyond the turning pixel and the
    # EDT-ridge walk to the end of the mask (`read_tip`, the same rule as at a
    # run end, capped by `tip_read_cap_xh`) are laid out AND back — a reading
    # of the ink the pen must have covered, never a point off the mask.
    hairpin_tip: bool = False
    # Grauwert-Stopp (arm D of the „Ecken" round, off by default): the tip walk
    # also stops one step before the crop's GREY reads paper — the nearest
    # pixel's grey above the midpoint of this crop's ink and paper levels, the
    # reversal sensor's own paper test. The frozen mask's adaptive threshold
    # keeps a pale halo around a round cap through which the walk otherwise
    # runs on; the darkness channel is a second reading of the ink beside the
    # mask, never a walk of its own — it does nothing unless `tip_read` is on.
    tip_grey_stop: bool = False
    # Spurs at strand ENDS are the stroke's continuation the thinning broke off
    # (an Anstrich), not a lateral artefact: with this on, a node whose non-spur
    # edges number at most one keeps its spurs instead of pruning them.
    spur_at_ends: bool = False
    # Tinten-Brücke: a decoder lift (a paper gap wider than `jump_radius_xh`
    # between two boarded pixels) whose straight gap is at most this long is
    # tested for FAINT ink on the crop — grey below the paper level by
    # `ink_bridge_margin` of the crop's paper−ink contrast on at least
    # `ink_bridge_share` of the chord samples outside the frozen mask, each
    # sample read as the darkest grey within ±`ink_bridge_band_px` along the
    # chord normal — and bridged only when the test passes; a hairline the
    # binarisation lost is a reading of the ink, a blank gap stays a lift.
    # 0 = off (measured as arm 4 of the 2026-09-11 round, off by default).
    ink_bridge_xh: float = 0.0
    ink_bridge_margin: float = 0.25
    ink_bridge_share: float = 0.6
    ink_bridge_band_px: float = 1.0
    # Rückfahrt statt Absetzen (arm C of the 2026-09-11 Ecken round, off by
    # default): a DECODER rule, not a reading. At a seed pen lift whose next
    # boarded pixel lies on the strand the pen stands on (or within the jump
    # radius of it), BEHIND the pen in its travel direction, the assembly
    # rides that strand back to the landing instead of lifting — the hand
    # wrote the stem twice (the ß stem: down, and up again into the bow).
    # Once per strand; every laid vertex is a rail pixel.
    ride_back: bool = False
    # Optional ink evidence for the rule (the Doppelstrich reading, measured
    # inert on the printed 1922 plate: 0 of 63 words at 1.4 × pen): with a
    # ratio > 0 the ride is licensed only where the strand's ink width (2 × EDT
    # along the rail) exceeds `ride_back_ink_ratio` × the word's pen width —
    # the median 2 × EDT over the skeleton — over ≥ `ride_back_min_xh` of
    # contiguous arc. 0 = no evidence required (the rule alone).
    ride_back_ink_ratio: float = 0.0
    ride_back_min_xh: float = 0.5

    def __post_init__(self) -> None:
        if self.rail not in ("subpixel", "tentfit", "raw"):
            raise ValueError(f"rail must be 'subpixel', 'tentfit' or 'raw', not {self.rail!r}")
        if self.edt_upsample < 1:
            raise ValueError(f"edt_upsample must be >= 1, not {self.edt_upsample!r}")
        if self.fit_half_px <= 0.0 or self.fit_step_px <= 0.0 or self.fit_step_px > self.fit_half_px:
            raise ValueError("fit_step_px must lie in (0, fit_half_px]")
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


@dataclass(frozen=True)
class EdtField:
    """A distance transform in crop px, held on a raster `up` times finer.

    Reads take crop-pixel coordinates and return crop-pixel distances; with
    `up == 1` the read is the plain bilinear `map_coordinates` call, so the
    delivered rail's numbers are untouched to the last bit.
    """

    edt: np.ndarray
    up: int = 1

    @property
    def shape(self) -> tuple[int, int]:
        return self.edt.shape[0] // self.up, self.edt.shape[1] // self.up

    def read(self, pts: np.ndarray) -> np.ndarray:
        if self.up == 1:
            return map_coordinates(self.edt, [pts[:, 1], pts[:, 0]], order=1, mode="constant", cval=0.0)
        # A crop pixel is a cell of `up × up` fine pixels: its centre `x` sits
        # at fine index `(x + 0.5) · up − 0.5` (scipy's `grid_mode=True`).
        fine = (np.asarray(pts, dtype=float) + 0.5) * self.up - 0.5
        return map_coordinates(self.edt, [fine[:, 1], fine[:, 0]], order=1, mode="constant", cval=0.0) / self.up


def fine_edt(mask: np.ndarray, crop: np.ndarray, up: int) -> tuple[EdtField, float]:
    """The mask's distance transform on an `up`× finer raster, plus the share of
    the mask's boundary pixels the fine raster agrees with.

    The crop's grey and the adaptive threshold the frozen mask came from are
    both interpolated bilinearly onto the fine raster; INSIDE the mask's
    one-pixel boundary band a fine pixel is ink where the grey falls below
    that threshold, everywhere else the mask decides (nearest). The mask thus
    keeps deciding WHAT is ink — a Fleck stays removed, a counter stays open —
    and the grey only decides WHERE inside an edge pixel the edge lies.
    """
    mask = np.asarray(mask, dtype=bool)
    gray = np.asarray(crop, dtype=float)
    threshold = threshold_local(gray, block_size=FINE_MASK_BLOCK_PX, method="gaussian", offset=FINE_MASK_OFFSET)
    gray_fine = zoom(gray, up, order=1, mode="nearest", grid_mode=True)
    threshold_fine = zoom(threshold, up, order=1, mode="nearest", grid_mode=True)
    cell = np.ones((up, up), dtype=bool)
    band = binary_dilation(mask) & ~binary_erosion(mask)
    fine = np.where(np.kron(band, cell), gray_fine < threshold_fine, np.kron(mask, cell))
    h, w = mask.shape
    coverage = fine.reshape(h, up, w, up).mean(axis=(1, 3))
    agreement = float(((coverage >= 0.5) == mask)[band].mean()) if band.any() else 1.0
    return EdtField(distance_transform_edt(fine), up), agreement


def subpixel_rail(points: np.ndarray, tan: np.ndarray, edt: np.ndarray | EdtField) -> np.ndarray:
    """Each pixel moved along its normal onto the apex of the ink's distance tent.

    The EDT read at −1, 0, +1 px along the local normal is `w − |x − δ|` inside
    a stroke of half-width `w`, so `δ = (f(+1) − f(−1)) / 2` exactly — a
    parabola would halve it. Reads that fall off the ink (a stroke edge, a
    counter) leave the pixel where the thinning put it.
    """
    field = edt if isinstance(edt, EdtField) else EdtField(edt)
    h, w = field.shape
    out = np.asarray(points, dtype=float).copy()
    normal = np.column_stack([-tan[:, 1], tan[:, 0]])
    f_plus = field.read(out + normal)
    f_minus = field.read(out - normal)
    delta = 0.5 * (f_plus - f_minus)
    valid = (f_plus > 0.0) & (f_minus > 0.0) & (np.abs(delta) <= SUBPIXEL_MAX_PX)
    inside = (out[:, 0] >= 1) & (out[:, 0] <= w - 2) & (out[:, 1] >= 1) & (out[:, 1] <= h - 2)
    move = valid & inside
    out[move] += normal[move] * delta[move, None]
    return out


def tentfit_rail(
    points: np.ndarray, tan: np.ndarray, edt: np.ndarray | EdtField, half_px: float, step_px: float
) -> np.ndarray:
    """Each pixel moved along its normal onto the apex of a least-squares tent
    `a − b·|x − δ|` fitted to the EDT over ±`half_px` at `step_px` spacing.

    Only the contiguous run of in-ink samples around the pixel enters the fit
    (a counter or the paper beyond a stroke edge is not part of this stroke's
    tent); `δ` is searched on `TENTFIT_GRID_PX` and refined parabolically. A
    pixel whose run is too short for a tent, or whose fitted slope is too flat
    for a distance, falls back to the apex of the outermost symmetric pair
    `(f(+s) − f(−s)) / 2` — the three-point reading at that scale — and stays
    where the thinning put it when no symmetric pair lies in the ink. Every
    read is along the normal: a reading of the distance transform, never a
    filter along the path.
    """
    field = edt if isinstance(edt, EdtField) else EdtField(edt)
    h, w = field.shape
    out = np.asarray(points, dtype=float).copy()
    n = len(out)
    if n == 0:
        return out
    normal = np.column_stack([-tan[:, 1], tan[:, 0]])
    k_half = max(1, int(round(half_px / step_px)))
    offs = np.arange(-k_half, k_half + 1) * step_px
    m = len(offs)
    c = k_half
    f = np.stack([field.read(out + normal * o) for o in offs], axis=1)
    positive = f > 0.0
    sel = np.zeros_like(positive)
    sel[:, c] = positive[:, c]
    for j in range(c - 1, -1, -1):
        sel[:, j] = sel[:, j + 1] & positive[:, j]
    for j in range(c + 1, m):
        sel[:, j] = sel[:, j - 1] & positive[:, j]
    n_sel = sel.sum(axis=1)
    has_both = sel[:, :c].any(axis=1) & sel[:, c + 1 :].any(axis=1)
    selw = sel.astype(float)
    n_grid = int(round(SUBPIXEL_MAX_PX / TENTFIT_GRID_PX))
    deltas = np.arange(-n_grid, n_grid + 1) * TENTFIT_GRID_PX
    res = np.full((n, len(deltas)), np.inf)
    slope = np.zeros((n, len(deltas)))
    s_w = np.maximum(n_sel, 1).astype(float)
    s_y = (selw * f).sum(axis=1)
    for k, dlt in enumerate(deltas):
        g = -np.abs(offs - dlt)
        s_g = selw @ g
        s_gg = selw @ (g * g)
        s_gy = (selw * f) @ g
        den = s_w * s_gg - s_g * s_g
        ok = den > 1e-9
        b = np.where(ok, (s_w * s_gy - s_g * s_y) / np.where(ok, den, 1.0), 0.0)
        a = (s_y - b * s_g) / s_w
        r = selw * (f - a[:, None] - b[:, None] * g[None, :])
        res[:, k] = np.where(ok, (r * r).sum(axis=1), np.inf)
        slope[:, k] = b
    best = np.argmin(res, axis=1)
    rows = np.arange(n)
    delta = deltas[best]
    fit_res = res[rows, best]
    r0 = res[rows, np.maximum(best - 1, 0)]
    r2 = res[rows, np.minimum(best + 1, len(deltas) - 1)]
    # A pixel with no fit at all carries `inf` residuals; it gets no refinement.
    interior = (best > 0) & (best < len(deltas) - 1) & np.isfinite(r0) & np.isfinite(fit_res) & np.isfinite(r2)
    r0, r1, r2 = (np.where(interior, r, 0.0) for r in (r0, fit_res, r2))
    curv = r0 - 2.0 * r1 + r2
    refine = np.where(interior & (curv > 1e-12), 0.5 * (r0 - r2) / np.where(curv > 1e-12, curv, 1.0), 0.0)
    delta = delta + refine * TENTFIT_GRID_PX
    fit_ok = (
        (n_sel >= TENTFIT_MIN_SAMPLES)
        & has_both
        & np.isfinite(fit_res)
        & (slope[rows, best] >= TENTFIT_MIN_SLOPE)
        & (np.abs(delta) <= SUBPIXEL_MAX_PX)
    )
    # Fallback: the outermost symmetric pair still inside the ink.
    pair_delta = np.zeros(n)
    pair_ok = np.zeros(n, dtype=bool)
    for j in range(1, c + 1):
        both = sel[:, c - j] & sel[:, c + j]
        pair_delta = np.where(both, 0.5 * (f[:, c + j] - f[:, c - j]), pair_delta)
        pair_ok |= both
    pair_ok &= np.abs(pair_delta) <= SUBPIXEL_MAX_PX
    move_delta = np.where(fit_ok, delta, pair_delta)
    valid = fit_ok | pair_ok
    inside = (out[:, 0] >= 1) & (out[:, 0] <= w - 2) & (out[:, 1] >= 1) & (out[:, 1] <= h - 2)
    move = valid & inside
    out[move] += normal[move] * move_delta[move, None]
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


def refine_strands(
    strands: list[Strand], mask: np.ndarray, weights: TintenpfadWeights, crop: np.ndarray | None = None
) -> dict[str, Any]:
    """The sub-pixel reading of every strand, in place; tangents re-read afterwards.

    Returns the diagnostics of the reading — empty for the delivered default,
    so the default's diagnostics and strokes stay identical (the weight
    fields themselves ride into every artefact); the fine raster reports how
    well its boundary agrees with the frozen mask's.
    """
    diag: dict[str, Any] = {}
    edt: np.ndarray | EdtField = distance_transform_edt(np.asarray(mask, dtype=bool))
    if weights.edt_upsample > 1 and crop is not None:
        edt, agreement = fine_edt(mask, crop, weights.edt_upsample)
        diag["edt_upsample"] = weights.edt_upsample
        diag["fine_mask_band_agreement"] = round(agreement, 4)
    for s in strands:
        if weights.rail == "tentfit":
            s.points = tentfit_rail(s.points, s.tan, edt, weights.fit_half_px, weights.fit_step_px)
        else:
            s.points = subpixel_rail(s.points, s.tan, edt)
        s.tan = strand_tangents(s.points, weights.tangent_window_px, s.closed)
    return diag


@dataclass
class DoubleInk:
    """The Doppelstrich reading per strand: which rail pixels sit in ink wider
    than `ratio × pen`, the arc position of every pixel, and the minimum
    contiguous wide arc (px) a ride must cover to count as evidence."""

    wide: list[np.ndarray]  # per strand, bool per pixel
    arc: list[np.ndarray]  # per strand, cumulative arc in px
    min_run_px: float
    pen_px: float

    def qualifies(self, strand: int, lo: int, hi: int) -> bool:
        """True when the pixels `lo..hi` (inclusive) of `strand` hold one
        contiguous wide run of at least `min_run_px` of arc."""
        flag = self.wide[strand][lo : hi + 1]
        arc = self.arc[strand][lo : hi + 1]
        return longest_true_run(flag, arc) >= self.min_run_px


def longest_true_run(flag: np.ndarray, arc: np.ndarray) -> float:
    """The arc length spanned by the longest contiguous True run of `flag`."""
    best = 0.0
    j = 0
    n = len(flag)
    while j < n:
        if flag[j]:
            k = j
            while k + 1 < n and flag[k + 1]:
                k += 1
            best = max(best, float(arc[k] - arc[j]))
            j = k + 1
        else:
            j += 1
    return best


def double_ink_of(
    strands: Sequence[Strand], mask: np.ndarray, skel: np.ndarray, xh: float, weights: TintenpfadWeights
) -> DoubleInk:
    """The Doppelstrich evidence read off the ink: the width of every strand
    pixel against the word's own pen width. With `ride_back_ink_ratio` 0 every
    pixel counts as wide — the ride needs no evidence (the decoder rule alone)."""
    edt = distance_transform_edt(np.asarray(mask, dtype=bool))
    pen = float(np.median(2.0 * edt[np.asarray(skel, dtype=bool)])) if np.any(skel) else 0.0
    ratio = weights.ride_back_ink_ratio
    wide: list[np.ndarray] = []
    arc: list[np.ndarray] = []
    for s in strands:
        w = 2.0 * map_coordinates(edt, [s.points[:, 1], s.points[:, 0]], order=1, mode="nearest")
        wide.append(w > ratio * pen if ratio > 0.0 else np.ones(len(w), bool))
        arc.append(np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(s.points, axis=0).T))]))
    return DoubleInk(wide, arc, weights.ride_back_min_xh * xh, pen)


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


def node_near(strands: Sequence[Strand], node_px: float) -> np.ndarray:
    """Per board pixel: does it lie within `node_px` strand pixels of a node the
    strand passes — a junction index, or an open strand's end (a ring's cut is
    not a node)? `node_px <= 0` marks every pixel."""
    flags = []
    for s in strands:
        n = len(s.points)
        if node_px <= 0:
            flags.append(np.ones(n, dtype=bool))
            continue
        nodes = list(s.junction_idx) if s.closed else [0, n - 1, *s.junction_idx]
        idx = np.arange(n)
        near = np.zeros(n, dtype=bool)
        for j in nodes:
            near |= np.abs(idx - int(j)) <= node_px
        flags.append(near)
    return np.concatenate(flags) if flags else np.zeros(0, dtype=bool)


def _branches(board: _Board, order: np.ndarray, gap: int) -> dict[int, int]:
    """Per ball pixel, which BRANCH of its strand it lies on: the strand's ball
    pixels sorted by index, split where consecutive indices are more than
    `gap` apart (on a ring the run across the cut is one run). A strand that
    passes the ball twice — the loop side and the stem of the same l — is two
    branches, each of which the kept set must reach."""
    by_strand: dict[int, list[int]] = {}
    for p in order:
        by_strand.setdefault(int(board.sid[p]), []).append(int(p))
    branch: dict[int, int] = {}
    for pixels in by_strand.values():
        pixels.sort(key=lambda p: int(board.idx[p]))
        b = 0
        prev: int | None = None
        for p in pixels:
            i = int(board.idx[p])
            if prev is not None and i - prev > gap:
                b += 1
            branch[p] = b
            prev = i
        if b > 0 and board.closed[pixels[0]]:
            n = int(board.n[pixels[0]])
            if n - int(board.idx[pixels[-1]]) + int(board.idx[pixels[0]]) <= gap:
                for p in pixels:
                    if branch[p] == b:
                        branch[p] = 0
    return branch


def _candidate_pixels(
    board: _Board, point: np.ndarray, radius: float, weights: TintenpfadWeights, branch_gap: int | None = None
) -> tuple[np.ndarray, int, int]:
    """The strand pixels one seed sample may board, how many pixels the ball
    held, and how many STRANDS the ball held (each of which the kept set
    must still reach — the judges' effective-radius test).

    With `branch_gap` (the Selbstsprung arm: the ride cap in pixels) the
    per-strand pick is per BRANCH of a strand — beyond the ride cap a strand
    is another strand here too, or the far branch of a loop that returns
    onto its own stem could never be boarded from a sample near the stem."""
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
    branch = _branches(board, order, branch_gap) if branch_gap is not None else {}
    firsts: list[int] = []
    others: list[int] = []
    seen: dict[tuple[int, int], int] = {}
    for p in order:
        s = (int(board.sid[p]), branch.get(int(p), 0))
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
    at_node = node_near(strands, weights.self_jump_node_px) if weights.self_jump else None
    branch_gap = int(ride_cap) if weights.self_jump else None
    n = len(seed.xy)
    inf = float("inf")
    s_pix: list[np.ndarray] = []
    s_dir: list[np.ndarray] = []
    s_emit: list[np.ndarray] = []
    held_counts, kept_counts, strands_held, strands_kept = [], [], [], []
    for k in range(n):
        idx, held, n_strands = _candidate_pixels(board, seed.xy[k], radius, weights, branch_gap)
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
                jump_price = weights.jump_base + weights.gap_w * gap + weights.jump_turn_w * (1.0 - cosj)
                sub = np.where(okj, jump_price, sub)
                if at_node is not None:
                    # Beyond the ride cap a strand is another strand: the
                    # same-strand pairs no ride or hairpin can reach take the
                    # jump price within the jump radius (the ride and hairpin
                    # masks cover |adv| ≤ ride_cap, so nothing is re-priced),
                    # from a node the strand passes to a node it passes.
                    okself = same & (np.abs(adv) > ride_cap) & (gap <= jump_r)
                    okself &= at_node[ia][:, None] & at_node[ib][None, :]
                    sub = np.where(okself, jump_price, sub)
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


def grey_levels(crop: np.ndarray, mask: np.ndarray) -> tuple[float, float]:
    """(ink, paper) grey of THIS crop — the mean inside and outside the frozen
    mask, exactly the two levels the reversal sensor's paper test is built on."""
    crop = np.asarray(crop, dtype=float)
    mask = np.asarray(mask, dtype=bool)
    ink = float(crop[mask].mean()) if mask.any() else 0.0
    paper = float(crop[~mask].mean()) if (~mask).any() else 1.0
    return ink, paper


def grey_paper_of(crop: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, float]:
    """Where THIS crop's grey reads paper: above the midpoint of its ink and
    paper levels — the reversal sensor's own paper test, so a walk the sensor
    would book as Papier-Strecke is stopped by the same reading that books it.
    Returns the boolean image and the midpoint."""
    ink, paper = grey_levels(crop, mask)
    midpoint = 0.5 * (ink + paper)
    return np.asarray(crop, dtype=float) > midpoint, midpoint


def ink_bridge_test(
    crop: np.ndarray,
    mask: np.ndarray,
    p0: np.ndarray,
    p1: np.ndarray,
    *,
    ink_level: float,
    paper_level: float,
    margin: float,
    share: float,
    band_px: float,
) -> dict[str, Any]:
    """Is the straight gap `p0 → p1` covered by faint ink the binarisation lost?

    The chord is sampled at 1-px steps; a sample whose nearest pixel is inside
    the frozen mask is the strand ends' own ink and is left out. Each remaining
    sample reads the DARKEST bilinear grey at normal offsets −band … +band (a
    hairline the chord misses by a pixel is still read), and counts as faint
    ink below `paper − margin × (paper − ink)`. The test passes when at least
    `share` of the paper-mask samples are faint ink; a chord with fewer than
    two paper-mask samples runs through continuous ink and passes.
    """
    crop = np.asarray(crop, dtype=float)
    mask = np.asarray(mask, dtype=bool)
    h, w = crop.shape
    p0, p1 = np.asarray(p0, dtype=float), np.asarray(p1, dtype=float)
    gap = float(np.hypot(*(p1 - p0)))
    n = max(2, int(np.ceil(gap)))
    ts = (np.arange(n) + 0.5) / n
    pts = p0 + ts[:, None] * (p1 - p0)
    col = np.clip(np.rint(pts[:, 0]).astype(int), 0, w - 1)
    row = np.clip(np.rint(pts[:, 1]).astype(int), 0, h - 1)
    outside = ~mask[row, col]
    threshold = paper_level - margin * (paper_level - ink_level)
    if int(outside.sum()) < 2:
        return {"gap_xh": None, "paper_samples": int(outside.sum()), "faint_share": 1.0, "bridged": True}
    chord = (p1 - p0) / gap if gap > 0 else np.array([1.0, 0.0])
    normal = np.array([-chord[1], chord[0]])
    offsets = np.arange(-np.floor(band_px), np.floor(band_px) + 1.0)
    darkest = np.full(n, np.inf)
    for off in offsets:
        q = pts + off * normal
        g = map_coordinates(crop, [q[:, 1], q[:, 0]], order=1, mode="nearest")
        darkest = np.minimum(darkest, g)
    faint = float((darkest[outside] < threshold).mean())
    return {
        "gap_xh": None,
        "paper_samples": int(outside.sum()),
        "faint_share": round(faint, 3),
        "bridged": faint >= share,
    }


def assemble(
    strands: Sequence[Strand],
    states: Sequence[tuple[int, int, int] | None],
    seed: Seed,
    xh: float,
    weights: TintenpfadWeights,
    ink_test: Callable[[np.ndarray, np.ndarray], dict[str, Any]] | None = None,
    hairpin_tip: Callable[[int, int, int], np.ndarray] | None = None,
    double_ink: DoubleInk | None = None,
) -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray], list[np.ndarray], dict[str, Any]]:
    """Decoded states → pen runs of strand pixels (+ bridges), each vertex with
    its slot label, its kind (0 rail · 1 bridge · 2 tip) and the seed sample
    that laid it.

    With `ink_test` (the Tinten-Brücke, `ink_bridge_xh > 0`) a would-be lift
    whose gap is within `ink_bridge_xh` is bridged when the test says the
    plate carries faint ink across it; every tested gap is recorded. With
    `hairpin_tip` (the Haken-Spitze, `HairpinTipReader`) every hairpin on one
    strand is handed its turning pixel and travel direction, and the vertices
    it returns — the tip beyond the turn, out and back — are laid there.

    With `double_ink` given (Rückfahrt statt Absetzen, `ride_back`), a seed
    pen lift whose next boarded pixel lies on the strand the pen stands on
    (or within the jump radius of its nearest pixel), BEHIND the pen in its
    travel direction, is ridden back over that rail instead of lifted — the
    hand wrote the stem twice; once per strand. The `DoubleInk` carries the
    optional ink evidence the ride must cover (none when the ratio is 0)."""
    runs: list[list[np.ndarray]] = []
    labels: list[list[int]] = []
    kinds: list[list[int]] = []
    samples: list[list[int]] = []
    n_jump = n_paper_bridges = n_hairpin = n_paper_lifts = n_ink_bridges = n_ride_back = 0
    ink_tests: list[dict[str, Any]] = []
    self_jump_gaps: list[float] = []
    ride_cap = weights.ride_cap_xh * xh
    jump_r = weights.jump_radius_xh * xh
    ink_bridge_r = weights.ink_bridge_xh * xh
    lateral_cap = weights.bridge_lateral_cap_xh * xh
    paper_run = 0
    prev: tuple[int, int, int] | None = None
    # The pen state before a seed lift, kept until the new stroke boards ink.
    pending: tuple[int, int, int] | None = None
    ride_used: set[int] = set()

    def ride_back_to(ps_state: tuple[int, int, int], st: tuple[int, int, int]) -> int | None:
        """The pixel of the pen's strand to ride back to, or None when the rule does not apply."""
        if double_ink is None:
            return None
        ps, pi, pd = ps_state
        s, i, _d = st
        if ps in ride_used or strands[ps].closed:
            return None
        if s == ps:
            j = i
        else:
            dist = np.linalg.norm(strands[ps].points - strands[s].points[i], axis=1)
            j = int(np.argmin(dist))
            if float(dist[j]) > jump_r:
                return None
        if (j - pi) * pd >= 0:
            return None
        return j if double_ink.qualifies(ps, min(pi, j), max(pi, j)) else None

    def emit(pt: np.ndarray, k: int, kind: int) -> None:
        runs[-1].append(np.asarray(pt, dtype=float))
        labels[-1].append(int(seed.slot[k]))
        kinds[-1].append(kind)
        samples[-1].append(k)

    def bridge_to(ps: tuple[int, int, int], st: tuple[int, int, int], k: int, *, chord: bool = False) -> None:
        s0, i0, d0 = ps
        s1, i1, d1 = st
        p0, p1 = strands[s0].points[i0], strands[s1].points[i1]
        # An ink bridge is emitted as the CHORD the grey test read, never as
        # a Hermite bow that could leave the tested faint ink.
        if weights.bridge == "hermite" and not chord:
            pts = hermite_bridge(
                p0, strands[s0].tan[i0] * d0, p1, strands[s1].tan[i1] * d1, BRIDGE_STEP_PX, lateral_cap
            )
            for q in pts:
                emit(q, k, 1)
        else:
            emit(p1, k, 1)

    def advance(s: int, pi: int, i: int, pd: int) -> int:
        """Signed index advance from `pi` to `i` along the travel direction `pd`
        (the shortest way round on a ring) — the decoder's own `adv`."""
        adv = (i - pi) * pd
        if strands[s].closed:
            n_pts = len(strands[s].points)
            adv = adv % n_pts
            adv = adv - n_pts if adv > n_pts / 2 else adv
        return int(adv)

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
            pending = prev if double_ink is not None else None
            prev = None
            paper_run = 0
        if st is None:
            if prev is not None:
                paper_run += 1
            continue
        s, i, d = st
        pts = strands[s].points
        if pending is not None and prev is None:
            # The new stroke's first boarded pixel: when it lies behind the pen
            # on the pen's own strand, ride that strand back to it instead of
            # lifting (Rückfahrt statt Absetzen).
            j = ride_back_to(pending, st)
            ps, pi, pd = pending
            pending = None
            if j is not None:
                step = 1 if j > pi else -1
                for q in range(pi + step, j + step, step):
                    emit(strands[ps].points[q], k, 0)
                n_ride_back += 1
                ride_used.add(ps)
                if s != ps:
                    bridge_to((ps, j, -pd), st, k)
                prev = st
                paper_run = 0
                continue
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
                # The Tinten-Brücke: the lift stands unless the plate shows
                # faint ink across the straight gap — then the chord is a
                # reading of that ink, not an invention.
                verdict = None
                if ink_test is not None and gap <= ink_bridge_r:
                    verdict = ink_test(strands[ps].points[pi], pts[i])
                    verdict["gap_xh"] = round(gap / xh, 3)
                    verdict["sample"] = int(k)
                    ink_tests.append(verdict)
                if verdict is not None and verdict["bridged"]:
                    n_ink_bridges += 1
                    bridge_to(prev, st, k, chord=True)
                    prev = st
                    paper_run = 0
                    continue
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
        if s == ps and weights.self_jump and abs(advance(s, pi, i, pd)) > ride_cap:
            # The Selbstsprung is bridged like a jump — never laid as rail over
            # the indices between, which would draw the whole loop backwards.
            self_jump_gaps.append(round(float(np.hypot(*(pts[i] - pts[pi]))), 2))
            bridge_to(prev, st, k)
        elif s == ps:
            rng, hairpin = rail_between(s, pi, i, pd, d)
            n_hairpin += int(hairpin)
            tip_pts = np.zeros((0, 2))
            turn_at_i = False
            if hairpin and hairpin_tip is not None and not strands[s].closed:
                # The pen turns at whichever of the two boarded pixels lies
                # further along the OLD travel direction; the tip is read
                # beyond that pixel, and laid where the turn happens.
                turn_at_i = (i - pi) * pd > 0
                tip_pts = hairpin_tip(s, i if turn_at_i else pi, pd)
            if not turn_at_i:
                for q in tip_pts:
                    emit(q, k, 2)
            for q in rng:
                emit(pts[q], k, 0)
            if turn_at_i:
                for q in tip_pts:
                    emit(q, k, 2)
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
    counts: dict[str, Any] = {
        "jumps": n_jump,
        "paper_bridges": n_paper_bridges,
        "hairpins": n_hairpin,
        "paper_lifts": n_paper_lifts,
    }
    if ink_test is not None:
        # Only with the arm on, so the default artefact keeps its bytes.
        counts["ink_bridges"] = n_ink_bridges
        counts["ink_bridge_tests"] = ink_tests
    if double_ink is not None:
        counts["ride_backs"] = n_ride_back
    if weights.self_jump:
        counts["self_jumps"] = len(self_jump_gaps)
        counts["self_jump_gaps_px"] = self_jump_gaps
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
    grey_paper: np.ndarray | None = None,
) -> tuple[np.ndarray, str]:
    """The ink read on from a free strand end to the end of the mask.

    From `origin` along `direction` in steps of `step_px`; every step is
    re-centred on the apex of the EDT tent across the stroke (the sub-pixel
    rail's own reading) and the direction is re-read from the walked points, so
    the walk follows the ridge of the ink rather than a straight line. It stops
    at the first step whose nearest pixel is not ink (the tip), at a step where
    the EDT RISES by more than `rise_px` (the walk entered a wider body — a
    junction, not a tip) or at `cap_px`. With `grey_paper` (a boolean image,
    True where the crop's grey reads paper) it also stops at the first step
    whose nearest pixel reads paper by the grey — the step is not appended, so
    the walk ends one step before the halo the mask still calls ink. Returns
    the points to append (in walking order) and the stop reason (`mask` ·
    `grey` · `rise` · `cap` · `edge`).
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
        if grey_paper is not None and grey_paper[iy, ix]:
            return np.asarray(out).reshape(-1, 2), "grey"
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


def _visited_ranges(
    states: Sequence[tuple[int, int, int] | None], also: Sequence[tuple[int, int]] = ()
) -> dict[int, tuple[int, int]]:
    """Per strand the (lowest, highest) pixel index any state boarded — plus
    the `also` pixels, which count as boarded too."""
    visited: dict[int, tuple[int, int]] = {}
    for st in states:
        if st is None:
            continue
        lo, hi = visited.get(st[0], (st[1], st[1]))
        visited[st[0]] = (min(lo, st[1]), max(hi, st[1]))
    for si, pi in also:
        lo, hi = visited.get(si, (pi, pi))
        visited[si] = (min(lo, pi), max(hi, pi))
    return visited


def _in_mask_count(mask: np.ndarray, pts: np.ndarray) -> int:
    h, w = mask.shape
    ix = np.rint(pts[:, 0]).astype(int)
    iy = np.rint(pts[:, 1]).astype(int)
    ok = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
    hit = np.zeros(len(pts), dtype=bool)
    hit[ok] = mask[iy[ok], ix[ok]]
    return int(hit.sum())


class HairpinTipReader:
    """The tip reading at a HAIRPIN (arm „Haken-Spitze"), called by `assemble`
    with the strand, the turning pixel and the travel direction of every
    same-strand hairpin.

    The rule is the run end's own (`tip_tail` + `read_tip`): the strand's
    unvisited rest beyond the turning pixel up to a FREE end, then the
    EDT-ridge walk to the end of the mask; the vertices come back out AND
    back — the pen went to the tip and returned over the same ink. A junction
    end, a node on the rest or a pixel some sample boarded beyond the turn
    blocks the reading, counted by reason. The strand ends read here are
    `claimed`, so the run-end reading afterwards never lays them twice.
    """

    def __init__(
        self,
        strands: Sequence[Strand],
        states: Sequence[tuple[int, int, int] | None],
        mask: np.ndarray,
        cap_px: float,
        grey_paper: np.ndarray | None = None,
    ) -> None:
        self.strands = strands
        self.mask = np.asarray(mask, dtype=bool)
        self.edt = distance_transform_edt(self.mask)
        self.cap_px = cap_px
        # The Grauwert-Stopp reaches the hairpin walks too: the same second
        # reading of the ink that stops a run end's walk stops a hairpin's.
        self.grey_paper = grey_paper
        self.visited = _visited_ranges(states)
        self.claimed: list[tuple[int, int]] = []
        self.rail_lengths: list[float] = []
        self.walk_lengths: list[float] = []
        self.diag: dict[str, Any] = {
            "hairpins": 0,
            "read": 0,
            "blocked": {"not_free": 0, "junction": 0, "visited": 0},
            "rail_points": 0,
            "rail_points_in_mask": 0,
            "walk_points": 0,
            "walk_points_in_mask": 0,
            "stops": {"mask": 0, "rise": 0, "cap": 0, "edge": 0, "grey": 0},
        }

    def __call__(self, s: int, i: int, travel_dir: int) -> np.ndarray:
        """The vertices to lay at the turn: the tip beyond pixel `i` of strand
        `s` in travel direction `travel_dir`, out and back (ending on `i`'s
        pixel again), or none when the tail is not readable."""
        strand = self.strands[s]
        self.diag["hairpins"] += 1
        rng, outward, why = tip_tail(strand, i, strand.tan[i] * travel_dir, self.visited.get(s, (i, i)))
        if why:
            self.diag["blocked"][why] += 1
            return np.zeros((0, 2))
        rail = strand.points[rng] if rng else np.zeros((0, 2))
        tip_start = rail[-1] if len(rail) else strand.points[i]
        walk, stop = read_tip(tip_start, outward, self.mask, self.edt, self.cap_px, grey_paper=self.grey_paper)
        self.diag["stops"][stop] += 1
        out = np.vstack([rail, walk])
        if not len(out):
            return out
        self.diag["read"] += 1
        self.diag["rail_points"] += len(rail)
        self.diag["rail_points_in_mask"] += _in_mask_count(self.mask, rail) if len(rail) else 0
        self.diag["walk_points"] += len(walk)
        self.diag["walk_points_in_mask"] += _in_mask_count(self.mask, walk) if len(walk) else 0
        self.rail_lengths.append(polyline_len(np.vstack([strand.points[i][None, :], rail])) if len(rail) else 0.0)
        self.walk_lengths.append(polyline_len(np.vstack([tip_start[None, :], walk])) if len(walk) else 0.0)
        self.claimed.append((s, rng[-1] if rng else i))
        return np.vstack([out, out[-2::-1], strand.points[i][None, :]])

    def report(self) -> dict[str, Any]:
        return {
            **self.diag,
            "rail_len_px_max": round(max(self.rail_lengths), 2) if self.rail_lengths else 0.0,
            "rail_len_px_total": round(sum(self.rail_lengths), 2),
            "walk_len_px_max": round(max(self.walk_lengths), 2) if self.walk_lengths else 0.0,
            "walk_len_px_total": round(sum(self.walk_lengths), 2),
        }


def read_tips(
    runs: list[np.ndarray],
    labels: list[np.ndarray],
    kinds: list[np.ndarray],
    samples: list[np.ndarray],
    strands: Sequence[Strand],
    states: Sequence[tuple[int, int, int] | None],
    mask: np.ndarray,
    cap_px: float,
    *,
    claimed: Sequence[tuple[int, int]] = (),
    grey_paper: np.ndarray | None = None,
) -> dict[str, Any]:
    """Both ends of every run read on to the ink's tip, in place.

    A run ends on the pixel the seed's last sample boarded, which is short of
    the strand's end whenever the composition is shorter than the ink. Where
    the strand runs on in the travel direction to a FREE end — no junction
    node before it, no other run on that tail — its remaining pixels are laid
    (`rail_points`, skeleton pixels), and from the free end the EDT-ridge walk
    of `read_tip` reads on to the end of the mask (`walk_points`). Tip vertices
    carry kind 2; every appended vertex is checked against the mask, and the
    counts returned are the proof that nothing was invented. `claimed` pixels
    (the strand ends a `HairpinTipReader` already laid) count as visited.
    With `grey_paper`
    (the Grauwert-Stopp) the walk also ends where the crop's grey reads paper;
    the rail pixels are the thinning's own ink and are never gated by it, only
    counted (`rail_points_grey_paper`), and `walk_points_grey_paper` is the
    proof the stop held on every emitted walk vertex.
    """
    edt = distance_transform_edt(np.asarray(mask, dtype=bool))
    pixel_of: dict[tuple[float, float], list[tuple[int, int]]] = {}
    for si, s in enumerate(strands):
        for pi, p in enumerate(s.points):
            pixel_of.setdefault(_pixel_key(p), []).append((si, pi))
    visited = _visited_ranges(states, claimed)
    stops = {"mask": 0, "rise": 0, "cap": 0, "edge": 0}
    if grey_paper is not None:
        stops["grey"] = 0
    blocked = {"not_free": 0, "junction": 0, "visited": 0, "ambiguous": 0}
    ends_read = rail_added = rail_inside = walk_added = walk_inside = 0
    rail_grey = walk_grey = 0
    rail_lengths: list[float] = []
    walk_lengths: list[float] = []

    def hits(pts: np.ndarray, image: np.ndarray) -> int:
        h, w = image.shape
        ix = np.rint(pts[:, 0]).astype(int)
        iy = np.rint(pts[:, 1]).astype(int)
        ok = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
        hit = np.zeros(len(pts), dtype=bool)
        hit[ok] = image[iy[ok], ix[ok]]
        return int(hit.sum())

    def in_mask(pts: np.ndarray) -> int:
        return hits(pts, mask)

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
            walk, stop = read_tip(tip_start, outward, mask, edt, cap_px, grey_paper=grey_paper)
            stops[stop] += 1
            pts = np.vstack([rail, walk])
            if not len(pts):
                continue
            ends_read += 1
            rail_added += len(rail)
            rail_inside += in_mask(rail) if len(rail) else 0
            walk_added += len(walk)
            walk_inside += in_mask(walk) if len(walk) else 0
            if grey_paper is not None:
                rail_grey += hits(rail, grey_paper) if len(rail) else 0
                walk_grey += hits(walk, grey_paper) if len(walk) else 0
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
    out = {
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
    if grey_paper is not None:
        out["rail_points_grey_paper"] = rail_grey
        out["walk_points_grey_paper"] = walk_grey
    return out


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
    if weights.rail in ("subpixel", "tentfit"):
        diag.update(refine_strands(strands, np.asarray(case_ev.mask, dtype=bool), weights, crop=case_ev.crop))
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
    ink_test = None
    if weights.ink_bridge_xh > 0.0:
        crop = np.asarray(case_ev.crop, dtype=float)
        mask = np.asarray(case_ev.mask, dtype=bool)
        ink_level, paper_level = grey_levels(crop, mask)
        diag["grey_levels"] = {"ink": round(ink_level, 4), "paper": round(paper_level, 4)}

        def ink_test(p0: np.ndarray, p1: np.ndarray) -> dict[str, Any]:
            return ink_bridge_test(
                crop,
                mask,
                p0,
                p1,
                ink_level=ink_level,
                paper_level=paper_level,
                margin=weights.ink_bridge_margin,
                share=weights.ink_bridge_share,
                band_px=weights.ink_bridge_band_px,
            )

    mask = np.asarray(case_ev.mask, dtype=bool)
    grey_paper = None
    grey_midpoint = 0.0
    if weights.tip_read and weights.tip_grey_stop:
        grey_paper, grey_midpoint = grey_paper_of(np.asarray(case_ev.crop, dtype=float), mask)
    hairpin_reader = None
    if weights.hairpin_tip:
        hairpin_reader = HairpinTipReader(strands, states, mask, weights.tip_read_cap_xh * xh, grey_paper=grey_paper)
    double_ink = None
    if weights.ride_back:
        double_ink = double_ink_of(
            strands, np.asarray(case_ev.mask, dtype=bool), np.asarray(case_ev.skel, dtype=bool), xh, weights
        )
        if weights.ride_back_ink_ratio > 0.0:
            runs_xh = [longest_true_run(w, a) / xh for w, a in zip(double_ink.wide, double_ink.arc, strict=True)]
            diag["double_ink_pen_px"] = round(double_ink.pen_px, 2)
            diag["double_ink_strands"] = int(sum(1 for r in runs_xh if r >= weights.ride_back_min_xh))
            diag["double_ink_run_xh"] = round(max(runs_xh), 3) if runs_xh else 0.0
    runs, labels, kinds, samples, counts = assemble(
        strands, states, seed, xh, weights, ink_test, hairpin_tip=hairpin_reader, double_ink=double_ink
    )
    diag.update(counts)
    if hairpin_reader is not None:
        diag["hairpin_tip"] = hairpin_reader.report()
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
    if weights.tip_read:
        diag["tip_read"] = read_tips(
            runs,
            labels,
            kinds,
            samples,
            strands,
            states,
            mask,
            weights.tip_read_cap_xh * xh,
            claimed=hairpin_reader.claimed if hairpin_reader is not None else (),
            grey_paper=grey_paper,
        )
        if grey_paper is not None:
            diag["tip_read"]["grey_midpoint"] = round(grey_midpoint, 4)
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
        if grey_paper is not None:
            # The raster corner: a resampled vertex sits between two walk
            # vertices and may round to a pixel the grey calls paper.
            diag["tip_read"]["resampled_grey_paper"] = int(grey_paper[iy[ok], ix[ok]].sum())
    if hairpin_reader is not None:
        # The same proof for the hairpin tips: every kind-2 vertex of the
        # delivered runs (run ends and hairpins together) sits on ink.
        tip_pts = np.vstack([r[np.asarray(k) == 2] for r, k in zip(runs, kinds, strict=True)] or [np.zeros((0, 2))])
        diag["hairpin_tip"]["resampled_total"] = int(len(tip_pts))
        diag["hairpin_tip"]["resampled_in_mask"] = _in_mask_count(mask, tip_pts)
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
            )
            + (
                f" haken {d['hairpin_tip']['read']}/{d['hairpin_tip']['hairpins']}"
                f" rail +{d['hairpin_tip']['rail_points']} walk +{d['hairpin_tip']['walk_points']}"
                if "hairpin_tip" in d
                else ""
            )
            + (f" selfjumps {d['self_jumps']}" if "self_jumps" in d else ""),
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
    "DoubleInk",
    "EdtField",
    "HairpinTipReader",
    "Seed",
    "Strand",
    "TintenpfadWeights",
    "assemble",
    "best_matching",
    "decode",
    "decode_with_hysteresis",
    "displacement_coherence",
    "double_ink_of",
    "excursions_of",
    "extend_tip",
    "extend_tips",
    "fine_edt",
    "follow_case",
    "follow_word",
    "grey_levels",
    "grey_paper_of",
    "hermite_bridge",
    "ink_bridge_test",
    "longest_true_run",
    "node_near",
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
    "tentfit_rail",
    "tintenpfad_payload",
    "turn_angles_deg",
    "weights_from_overrides",
]


if __name__ == "__main__":
    main()
