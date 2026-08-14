"""Stage 2 of route G: the prior-free traversal, and the CLI that runs it.

    uv run python -m tools.routeg.recover
        [--frames tools/routeg/out/frames.json] [--out tools/routeg/out/raw]

Reads the FROZEN skeleton of each fixture entry (`ref_skel.npz`, the thinning of
the same `ref_mask.png` the bench's AIoU column grades against), builds the
segment graph and walks it. Output per word: ordered pen runs in crop pixels,
which `to_candidate.py` converts into the stored trace frame.

## The three decisions, and the fact that they are the whole method

This is a CONTROL, and its value comes from being obviously simple — every place
where the ductus prior would say something, this says the cheapest geometric
thing instead:

1. **Where the pen starts.** The leftmost endpoint of the leftmost component.
   No letter identity and no learned start-point statistics: the reference
   implementation ships `statisticalInitialPointComputed.mat`, a 2-D Gaussian
   over first-point positions fitted on SIGNATURE data (SigComp2009), and a
   table learned from signatures is exactly the kind of borrowed knowledge a
   control must not have. Its documented fallback when that prior finds nothing
   is the leftmost end point — which is what this always does.
2. **Which branch continues.** At a node, the unvisited edge whose direction
   best continues the incoming one — Gestalt good continuation, the criterion
   Diaz et al. resolve their crossing clusters with, reduced to a single dot
   product: no weighted `π_ij` over external angles, internal angles and
   curvature, no rank classification of the cluster (T-pattern / retraced /
   married), no Dijkstra through the cluster's own adjacency, no lookahead.
3. **When the pen lifts.** When the current node has no unvisited edge left. The
   next run starts at the leftmost node that still has one (the reference picks
   the nearest untraced end point instead; leftmost is the cheaper rule and the
   one that needs no notion of where the pen currently is).

What it therefore CANNOT do, stated up front so a bad number is read as the
method's limit rather than as a bug: it never retraces a stroke it has already
walked (a doubled downstroke is written once), it has no model of delayed marks
(an i-dot is written when its x-position comes up, not after the word), and it
cannot know that two ink components belong to one pen run.

Only numpy/scipy plus the frozen fixture bytes: no DB, no API, no `core/`
mutation, no rendering, no learning, no ground truth of any kind.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from tools.routeg.graph import Edge, SkeletonGraph, build_graph
from tools.routeg.prepare import DEFAULT_FIXTURES_ROOT, DEFAULT_OUT, load_skeleton


# How many points a direction is read over. One step is a single pixel and
# therefore quantised to eight angles, which decides crossings by raster
# accident; five steps span the stroke width of these plates without reaching
# around a curve.
DIRECTION_WINDOW = 5


def _unit(vector: np.ndarray) -> np.ndarray:
    norm = float(np.hypot(*vector))
    return vector / norm if norm > 0 else np.zeros(2)


def lead_direction(points: np.ndarray, window: int = DIRECTION_WINDOW) -> np.ndarray:
    """Unit direction leaving `points[0]`."""
    end = min(window, len(points) - 1)
    return _unit(points[end] - points[0]) if end > 0 else np.zeros(2)


def tail_direction(points: np.ndarray, window: int = DIRECTION_WINDOW) -> np.ndarray:
    """Unit direction arriving at `points[-1]`."""
    start = max(0, len(points) - 1 - window)
    return _unit(points[-1] - points[start]) if start < len(points) - 1 else np.zeros(2)


def _oriented(edge: Edge, from_node: int) -> np.ndarray:
    """This edge's points, starting at `from_node`."""
    return edge.points if edge.a == from_node else edge.reversed_points


def _other_end(edge: Edge, node: int) -> int:
    return edge.b if edge.a == node else edge.a


def traverse(graph: SkeletonGraph) -> list[np.ndarray]:
    """Every edge walked once, as ordered pen runs in `(x, y)` crop pixels."""
    degree = {node: len(edges) for node, edges in graph.incident.items()}
    by_component: dict[int, list[int]] = {}
    for node in range(len(graph.nodes)):
        by_component.setdefault(int(graph.node_component[node]), []).append(node)

    runs: list[np.ndarray] = []
    unvisited = set(range(len(graph.edges)))
    order = sorted(by_component, key=lambda c: (float(graph.nodes[by_component[c], 0].min()), c))
    for component in order:
        nodes = by_component[component]
        while True:
            # The pen starts at a free end where there is one — an endpoint is
            # where a stroke genuinely begins — and otherwise at the leftmost
            # node that still owes a branch.
            available = [n for n in nodes if any(e in unvisited for e in graph.incident[n])]
            if not available:
                break
            start = min(available, key=lambda n: (degree[n] != 1, float(graph.nodes[n, 0]), n))
            runs.append(_walk(graph, start, unvisited))
    return [run for run in runs if len(run) >= 2]


def _walk(graph: SkeletonGraph, start: int, unvisited: set[int]) -> np.ndarray:
    """One pen run: good-continuation steps from `start` until nothing is left."""
    points: list[np.ndarray] = []
    node = start
    incoming: np.ndarray | None = None
    while True:
        candidates = [e for e in graph.incident[node] if e in unvisited]
        if not candidates:
            break
        if incoming is None:
            # Nothing to continue yet. Latin script runs left to right, so the
            # most rightward departure is the choice — the one geometric
            # assumption about writing this control makes, and it is about the
            # SCRIPT's direction, not about any letter's ductus.
            chosen = max(candidates, key=lambda e: (float(lead_direction(_oriented(graph.edges[e], node))[0]), -e))
        else:
            chosen = max(
                candidates, key=lambda e: (float(incoming @ lead_direction(_oriented(graph.edges[e], node))), -e)
            )
        segment = _oriented(graph.edges[chosen], node)
        unvisited.discard(chosen)
        points.extend(segment[1:] if points and np.array_equal(points[-1], segment[0]) else segment)
        incoming = tail_direction(segment)
        node = _other_end(graph.edges[chosen], node)
    return np.array(points, dtype=float).reshape(-1, 2)


def recover_strokes(skel: np.ndarray) -> tuple[list[np.ndarray], dict]:
    """A thinned ink mask → ordered pen runs plus what the recovery saw."""
    graph = build_graph(skel)
    runs = traverse(graph)
    return runs, {
        "skeleton_px": int(np.asarray(skel, dtype=bool).sum()),
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "components": len(set(graph.node_component.tolist())),
        "isolated_pixels": graph.isolated_pixels,
        "strokes": len(runs),
        "points": int(sum(len(run) for run in runs)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--frames", type=Path, default=DEFAULT_OUT / "frames.json")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT / "raw")
    parser.add_argument("--fixtures-root", type=Path, default=None, help="default: the root prepare.py recorded")
    args = parser.parse_args(argv)

    payload = json.loads(args.frames.read_text(encoding="utf-8"))
    root = args.fixtures_root or Path(payload.get("fixtures_root", DEFAULT_FIXTURES_ROOT))
    args.out.mkdir(parents=True, exist_ok=True)

    for entry_id, frame in sorted(payload["frames"].items()):
        record = {"id": entry_id, "word": frame.get("word")}
        try:
            runs, meta = recover_strokes(load_skeleton(root / entry_id))
            record["strokes_px"] = [run.round(4).tolist() for run in runs]
            record["meta"] = meta
        except Exception as exc:  # one word's failure is a row, never the run
            record["error"] = f"{type(exc).__name__}: {exc}"
            record["meta"] = {}
            print(f"  ! {entry_id}: {record['error']}")
        (args.out / f"{entry_id}.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        meta = record.get("meta") or {}
        if meta:
            print(
                f"  {entry_id:<12} skel {meta['skeleton_px']:>4} px  nodes {meta['nodes']:>3}  "
                f"edges {meta['edges']:>3}  comp {meta['components']:>2}  "
                f"strokes {meta['strokes']:>2}  points {meta['points']:>4}"
            )
    print(f"recovered → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
