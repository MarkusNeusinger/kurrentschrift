"""The skeleton segment graph — stage 2's substrate, re-exported from `core`.

The construction moved to `core/skeleton_graph.py` unchanged when the
Streifen-Befund (`core/eigenhand/befund.py`) needed the same nodes and edges:
the API image ships `core/` and not `tools/`, so a reading the server has to
serve cannot live here. Nothing about the graph changed with the move — the
node/edge rules, the cluster merge and the closed-loop break are the same
lines — and this module keeps the import path every routeg consumer uses.

Read the doctrine at the new home; this file is deliberately only the door.
"""

from __future__ import annotations

from core.skeleton_graph import CONNECTIVITY, Edge, SkeletonGraph, build_graph, neighbour_counts


__all__ = ["CONNECTIVITY", "Edge", "SkeletonGraph", "build_graph", "neighbour_counts"]
