"""The skeleton segment graph — stage 2's substrate, pure geometry.

A thinned ink mask becomes nodes and edges the way every writing-order-recovery
paper builds them (Diaz et al. 2022 §3.1, the `PointClassification` +
`LocalExamination/Clusters` half of the reference implementation): skeleton
pixels of degree != 2 are the NODES — endpoints (degree 1) and branch points
(degree >= 3) — and the degree-2 pixel chains between them are the EDGES.

Two details that decide whether the graph describes the ink or an artefact of
the thinning:

* **Adjacent branch pixels are ONE node.** An X-crossing rarely thins to a
  single 4-neighbour pixel; it usually leaves two or three adjacent 3-neighbour
  pixels. Labelling the node mask 8-connected merges them, which is exactly the
  "cluster" the paper resolves a crossing at. Without the merge a single
  crossing appears as two branch points joined by a one-pixel edge, and the
  traversal spends its good-continuation decision on that stub.
* **The merge also swallows one-pixel stubs.** An END pixel that touches a
  branch pixel is itself degree != 2, so it joins that node and the stub between
  them stops being an edge. That is deliberate — the reference implementation
  removes such pixels as "false trace points", and the alternative would be a
  node-to-node edge with no pixel of its own, i.e. a branch decision about
  nothing. The price is that a genuine two-pixel stroke is lost, which the
  bench's AIoU column prices.
* **A component with no node at all is a closed loop.** An `o` whose thinning
  has neither an end nor a fork carries no degree-!=2 pixel, so it would vanish
  from a graph built on nodes alone. Such a chain gets a synthetic node at its
  leftmost pixel and becomes a self-loop edge — broken somewhere, because a pen
  has to start somewhere, and the leftmost pixel is the choice that does not
  need to know which letter this is.

No project imports beyond numpy/scipy, no prior, no template, no ground truth:
everything here is a function of the ink mask alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import label


# 8-connectivity, the convention every skeleton-graph paper uses: a diagonal
# step is a step. `skimage.morphology.skeletonize` thins to an 8-connected
# skeleton, so anything less would cut chains at their diagonal links.
CONNECTIVITY = np.ones((3, 3), dtype=int)


@dataclass(frozen=True)
class Edge:
    """One degree-2 pixel chain, from node `a` to node `b`.

    `points` is `(n, 2)` in `(x, y)` crop pixels and INCLUDES both node
    representatives, so consecutive edges of a traversal meet at a shared point
    and the recovered pen path stays continuous across a crossing.
    """

    a: int
    b: int
    points: np.ndarray

    @property
    def reversed_points(self) -> np.ndarray:
        return self.points[::-1]


@dataclass
class SkeletonGraph:
    """Nodes, edges and the connected component each of them belongs to."""

    nodes: np.ndarray  # (n_nodes, 2) representative (x, y) per node cluster
    edges: list[Edge]
    node_component: np.ndarray  # (n_nodes,) skeleton component id per node
    incident: dict[int, list[int]] = field(default_factory=dict)
    isolated_pixels: int = 0

    def __post_init__(self) -> None:
        if not self.incident:
            incident: dict[int, list[int]] = {i: [] for i in range(len(self.nodes))}
            for index, edge in enumerate(self.edges):
                incident[edge.a].append(index)
                if edge.b != edge.a:
                    incident[edge.b].append(index)
            self.incident = incident

    def edge_component(self, edge: Edge) -> int:
        return int(self.node_component[edge.a])


def neighbour_counts(skel: np.ndarray) -> np.ndarray:
    """8-neighbour count per skeleton pixel (0 off the skeleton)."""
    padded = np.pad(skel.astype(np.int16), 1)
    total = np.zeros_like(padded)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            total += np.roll(np.roll(padded, dy, axis=0), dx, axis=1)
    return (total[1:-1, 1:-1] * skel).astype(np.int16)


def _neighbours(pixel: tuple[int, int], member: set[tuple[int, int]]) -> list[tuple[int, int]]:
    row, col = pixel
    out = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            candidate = (row + dr, col + dc)
            if candidate in member:
                out.append(candidate)
    return out


def _order_chain(pixels: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """A degree-2 pixel component walked end to end (deterministically).

    A chain with two free ends starts at the smaller `(row, col)` of them; a
    closed one — no free end — starts at its smallest `(row, col)`. Both rules
    are pure tie-breaks on the pixel raster, so the same mask always yields the
    same chain, which a measurement input has to.
    """
    member = set(pixels)
    ends = sorted(p for p in pixels if len(_neighbours(p, member)) <= 1)
    start = ends[0] if ends else min(pixels)
    ordered = [start]
    visited = {start}
    while True:
        options = [p for p in _neighbours(ordered[-1], member) if p not in visited]
        if not options:
            break
        # A staircase can leave two unvisited neighbours at the very first step;
        # the 4-connected one is the chain, the diagonal one its shortcut.
        step = min(options, key=lambda p: (abs(p[0] - ordered[-1][0]) + abs(p[1] - ordered[-1][1]), p))
        ordered.append(step)
        visited.add(step)
    return ordered


def _representative(pixels: np.ndarray) -> tuple[int, int]:
    """The cluster pixel closest to its own centroid — a point ON the skeleton.

    The centroid itself would sit off the ink for an L-shaped cluster, and a
    recovered trace that leaves the ink at every crossing is a worse control
    than one that stays on it.
    """
    centre = pixels.mean(axis=0)
    index = int(np.argmin(((pixels - centre) ** 2).sum(axis=1)))
    return int(pixels[index, 0]), int(pixels[index, 1])


def build_graph(skel: np.ndarray) -> SkeletonGraph:
    """The segment graph of a thinned ink mask, in `(x, y)` crop pixels."""
    skel = np.asarray(skel, dtype=bool)
    degree = neighbour_counts(skel)
    node_mask = skel & (degree != 2)
    link_mask = skel & (degree == 2)

    components, _ = label(skel, structure=CONNECTIVITY)
    node_labels, n_nodes = label(node_mask, structure=CONNECTIVITY)
    link_labels, n_links = label(link_mask, structure=CONNECTIVITY)

    node_rc: list[tuple[int, int]] = []
    node_of_pixel: dict[tuple[int, int], int] = {}
    isolated = 0
    for index in range(1, n_nodes + 1):
        pixels = np.argwhere(node_labels == index)
        rep = _representative(pixels)
        node_rc.append(rep)
        for row, col in pixels:
            node_of_pixel[(int(row), int(col))] = len(node_rc) - 1
        if len(pixels) == 1 and degree[rep] == 0:
            isolated += 1

    node_pixels = set(node_of_pixel)
    edges: list[Edge] = []
    for index in range(1, n_links + 1):
        chain = _order_chain([(int(r), int(c)) for r, c in np.argwhere(link_labels == index)])
        touching = [sorted({node_of_pixel[p] for p in _neighbours(end, node_pixels)}) for end in (chain[0], chain[-1])]
        if not touching[0] and not touching[1]:
            # A closed loop with no fork and no end anywhere (an `o` that thinned
            # into a bare ring): break it at its leftmost pixel — a pen has to
            # start somewhere, and that choice needs no knowledge of the letter.
            leftmost = min(range(len(chain)), key=lambda i: (chain[i][1], chain[i][0]))
            chain = chain[leftmost:] + chain[:leftmost]
            node_rc.append(chain[0])
            node_of_pixel[chain[0]] = len(node_rc) - 1
            node_pixels.add(chain[0])
            touching = [[len(node_rc) - 1], [len(node_rc) - 1]]
        if len(chain) == 1 and len(touching[0]) == 2:
            # A one-pixel link between two clusters: its single pixel is BOTH
            # ends, so the two touching nodes have to be split between them or
            # the edge would collapse onto one of them and disappear.
            touching = [[touching[0][0]], [touching[0][1]]]
        a, b = (side[0] if side else other[0] for side, other in zip(touching, touching[::-1], strict=True))
        # Node pixels and chain pixels are disjoint, so the two node
        # representatives extend the chain — except at a synthetic ring node,
        # which IS the chain's first pixel. Dropping the repeat there keeps the
        # ring closing on its start without a zero-length first step.
        points = [node_rc[a], *chain, node_rc[b]]
        points = [p for i, p in enumerate(points) if i == 0 or p != points[i - 1]]
        xy = np.array([[float(c), float(r)] for r, c in points], dtype=float)
        edges.append(Edge(a=int(a), b=int(b), points=xy))

    nodes = np.array([[float(c), float(r)] for r, c in node_rc], dtype=float).reshape(-1, 2)
    node_component = np.array([components[r, c] for r, c in node_rc], dtype=int)
    return SkeletonGraph(nodes=nodes, edges=edges, node_component=node_component, isolated_pixels=isolated)


__all__ = ["CONNECTIVITY", "Edge", "SkeletonGraph", "build_graph", "neighbour_counts"]
