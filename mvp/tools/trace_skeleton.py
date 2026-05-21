"""Skeleton-driven canonical-anchor extraction from the Loth 1866 chart.

Replaces hand-typed anchor coordinates in mvp/canonical/<glyph>_<position>_v0.json
with values measured off the actual chart ink: the M0 pipeline (binarize +
skeletonize + distance transform) gives a pixel-accurate centerline and per-
pixel half-stroke-width; this tool walks that centerline from a user-specified
start_xy, resamples to N evenly-spaced anchors, and converts them into the
template's normalised (baseline=0, midband=1) coordinate frame.

The ductus contribution that *can't* come from the image stays user-specified:
  - start_xy decides which endpoint of the stroke counts as "entry";
  - branch_choices (optional) decides which branch to follow at each junction
    when "straightest continuation" would pick the wrong one (e.g. the
    medial-e Schleife where the stroke must cross itself rather than turn
    back on the visually-closer pixel).
The .coupling enums (baseline / midband / ascender / descender) and the _note
fields are likewise preserved from the existing canonical JSON — they're
human judgments, not image measurements.

Usage:
    uv run python -m mvp.tools.trace_skeleton <glyph_key>
e.g. `s-medial`, `s-final`, `e-medial`. The glyph_key must exist in
mvp/canonical/loth_bboxes.json with at minimum baseline_y, midband_y, start_xy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import label as connected_components

from mvp.extract import binarize_adaptive, skeleton_and_width
from mvp.tools.loth import CANONICAL_DIR, REPO_ROOT, crop_with_excludes, load_bboxes, load_chart_grayscale


DEFAULT_N_ANCHORS = 14
DEFAULT_PRUNE_SPUR_PX = 6
# 8-connectivity: same kernel as run_demo.py for both component labelling and
# neighbour-counting on the thin skeleton; 4-conn would split diagonal steps.
NEIGHBOURS_8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def neighbour_pixels(py: int, px: int, skel: np.ndarray) -> list[tuple[int, int]]:
    """All skeleton-pixel neighbours of (py, px) within bounds, 8-connectivity."""
    h, w = skel.shape
    out = []
    for dy, dx in NEIGHBOURS_8:
        ny, nx = py + dy, px + dx
        if 0 <= ny < h and 0 <= nx < w and skel[ny, nx]:
            out.append((ny, nx))
    return out


def prune_spurs(skel: np.ndarray, max_spur: int = DEFAULT_PRUNE_SPUR_PX) -> np.ndarray:
    """Remove dead-end branches shorter than `max_spur` pixels.

    A spur is a sequence starting at a skeleton endpoint (1 neighbour) and
    ending at a junction (≥3 neighbours). Skeletonization of thick strokes
    or U-turn peaks often grows 1–5 px perpendicular nubs that derail greedy
    traversal — pruning them flattens the graph to its real topology while
    leaving genuine features (Schleife loops, ascender peaks) intact since
    they're significantly longer than a few pixels.
    """
    out = skel.copy()
    while True:
        any_pruned = False
        ys, xs = np.where(out)
        for y, x in zip(ys, xs):
            if not out[y, x]:
                continue
            if len(neighbour_pixels(int(y), int(x), out)) != 1:
                continue
            path = [(int(y), int(x))]
            prev = None
            for _ in range(max_spur + 1):
                cur = path[-1]
                nbrs = [n for n in neighbour_pixels(*cur, out) if n != prev]
                if len(nbrs) != 1:
                    break
                prev = cur
                path.append(nbrs[0])
            final = path[-1]
            if len(neighbour_pixels(*final, out)) >= 3 and len(path) - 1 < max_spur:
                for (py, px) in path[:-1]:
                    out[py, px] = False
                any_pruned = True
        if not any_pruned:
            break
    return out


def snap_to_any_skel_pixel(point_xy_local: tuple[int, int], skel: np.ndarray) -> tuple[int, int]:
    """Snap to the closest skeleton pixel (any kind — endpoint, junction, or mid-stroke).

    Used for waypoints, which the user places anywhere along the stroke,
    not just at endpoints. The walk uses BFS shortest path between
    consecutive snapped waypoints.
    """
    ys, xs = np.where(skel)
    if len(ys) == 0:
        raise RuntimeError("no skeleton pixels in crop — binarization likely failed")
    sx, sy = point_xy_local
    d2 = (xs - sx) ** 2 + (ys - sy) ** 2
    k = int(np.argmin(d2))
    return int(ys[k]), int(xs[k])


def bfs_shortest_path(skel: np.ndarray, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    """Unweighted BFS shortest skeleton path between two pixels in the same component."""
    if start == end:
        return [start]
    from collections import deque
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    q: deque[tuple[int, int]] = deque([start])
    while q:
        cur = q.popleft()
        if cur == end:
            out: list[tuple[int, int]] = []
            node: tuple[int, int] | None = cur
            while node is not None:
                out.append(node)
                node = parent[node]
            return list(reversed(out))
        for n in neighbour_pixels(cur[0], cur[1], skel):
            if n not in parent:
                parent[n] = cur
                q.append(n)
    raise RuntimeError(f"no skeleton path between {start} and {end} — different components?")


def walk_through_waypoints(
    skel: np.ndarray,
    start: tuple[int, int],
    waypoints_local: list[tuple[int, int]],
) -> tuple[list[tuple[int, int]], list[dict]]:
    """Chain BFS shortest paths from `start` through each waypoint in order.

    Pixels CAN be revisited — this is essential for Kurrent glyphs that
    draw a stroke up, then retrace it back down before branching off
    (the medial-e being the canonical example: pen goes up to peak 1,
    back down past the junction, branches to peak 2, etc.).

    `waypoints_local` are already snapped skeleton pixels (py, px).
    """
    path: list[tuple[int, int]] = [start]
    cur = start
    junctions: list[dict] = []
    for k, wp in enumerate(waypoints_local):
        segment = bfs_shortest_path(skel, cur, wp)
        if len(segment) > 1:
            path.extend(segment[1:])  # avoid duplicating the start-of-segment pixel
        junctions.append({
            "waypoint_index": k,
            "from_px": (int(cur[1]), int(cur[0])),
            "to_px": (int(wp[1]), int(wp[0])),
            "segment_length_px": len(segment) - 1,
            "source": "waypoint",
        })
        cur = wp
    return path, junctions


def resolve_walk_start(start_xy_local: tuple[int, int], skel: np.ndarray) -> tuple[tuple[int, int], np.ndarray]:
    """Pick the walk's start endpoint and isolate its connected component.

    Two-pass logic:
      1. Snap to the closest skeleton pixel (any kind) — gives us the
         connected component the user's start_xy hint sits inside, even
         when bleed-in fragments from neighbour glyphs share the crop.
      2. Within that component, snap to the closest *endpoint* (skeleton
         pixel with one neighbour). Snapping to any pixel is unsafe: for
         a long stroke, the nearest pixel to the hint is usually a
         mid-stroke pixel, from which the walk traces only half the
         glyph. Endpoints are the only valid stroke-starts.
    """
    ys, xs = np.where(skel)
    if len(ys) == 0:
        raise RuntimeError("no skeleton pixels in crop — binarization likely failed")
    sx, sy = start_xy_local
    d2_any = (xs - sx) ** 2 + (ys - sy) ** 2
    seed_k = int(np.argmin(d2_any))
    seed = (int(ys[seed_k]), int(xs[seed_k]))

    labelled, _ = connected_components(skel, structure=np.ones((3, 3), dtype=np.int8))
    component = labelled == labelled[seed[0], seed[1]]

    ys2, xs2 = np.where(component)
    endpoints = [(int(y), int(x)) for y, x in zip(ys2, xs2)
                 if len(neighbour_pixels(int(y), int(x), component)) == 1]
    if not endpoints:
        # Closed loop with no endpoints — fall back to the seed.
        return seed, component
    ep_arr = np.array(endpoints, dtype=float)
    d2_eps = (ep_arr[:, 1] - sx) ** 2 + (ep_arr[:, 0] - sy) ** 2
    return endpoints[int(np.argmin(d2_eps))], component


def walk_skeleton(
    skel: np.ndarray,
    start: tuple[int, int],
    branch_choices: list[int] | None = None,
) -> tuple[list[tuple[int, int]], list[dict]]:
    """Find the longest simple path through the skeleton from `start`.

    Greedy walking dies on glyphs whose skeletons have multiple junctions
    (e.g. the medial-e's zigzag peaks, or the final-s's loop): at each
    junction the greedy rule picks one branch and dead-ends if that branch
    is short. DFS searches all simple paths from start and returns the
    longest one — which for our pruned skeletons is the intended traversal
    (visiting every peak/valley/loop), since spurs have been removed and
    anything left is real ink.

    `branch_choices` is preserved as an escape hatch: if the longest path
    isn't the right one (e.g. a stroke should deliberately traverse a
    shorter loop), the user can force individual junction picks. Indices
    refer to junctions encountered along the *longest* path in walk order;
    setting branch_choices[k] overrides the k-th junction's branch with
    the listed index (0-based in the neighbour ordering at that junction).

    Junctions are reported with the branch picked at each, so the user
    can see what was chosen and override if needed.
    """
    longest_path: list[tuple[int, int]] = [start]
    visited: set[tuple[int, int]] = {start}
    current: list[tuple[int, int]] = [start]

    def dfs(cur: tuple[int, int]) -> None:
        nonlocal longest_path
        extended = False
        for n in neighbour_pixels(cur[0], cur[1], skel):
            if n in visited:
                continue
            visited.add(n)
            current.append(n)
            extended = True
            dfs(n)
            current.pop()
            visited.remove(n)
        if not extended and len(current) > len(longest_path):
            longest_path = list(current)

    import sys as _sys
    prev_limit = _sys.getrecursionlimit()
    _sys.setrecursionlimit(max(prev_limit, int(skel.sum()) + 100))
    try:
        dfs(start)
    finally:
        _sys.setrecursionlimit(prev_limit)

    # Compute the junction log along the chosen path (for reporting only).
    junctions: list[dict] = []
    for i in range(1, len(longest_path) - 1):
        py, px = longest_path[i]
        nbrs = neighbour_pixels(py, px, skel)
        if len(nbrs) < 3:
            continue
        prev_p = longest_path[i - 1]
        next_p = longest_path[i + 1]
        chosen_dir = (next_p[0] - py, next_p[1] - px)
        chosen_tangent = float(np.degrees(np.arctan2(-chosen_dir[0], chosen_dir[1])))
        alts = []
        for n in nbrs:
            if n == prev_p or n == next_p:
                continue
            alts.append(round(float(np.degrees(np.arctan2(-(n[0] - py), n[1] - px))), 1))
        junctions.append({
            "at_px": (int(px), int(py)),
            "chosen_tangent_deg": round(chosen_tangent, 1),
            "alternatives_deg": alts,
            "source": "longest-path-dfs",
        })

    # `branch_choices`, if provided, override individual junctions by index.
    # Re-walk: from start, greedy step by step, but at each junction along
    # the longest path use the listed branch instead.
    if branch_choices:
        overrides = list(branch_choices)
        overridden_path, override_log = _walk_with_overrides(skel, start, overrides)
        if overridden_path:
            longest_path = overridden_path
            junctions = override_log

    return longest_path, junctions


def _walk_with_overrides(
    skel: np.ndarray,
    start: tuple[int, int],
    branch_choices: list[int],
) -> tuple[list[tuple[int, int]], list[dict]]:
    """Greedy walk with explicit branch index per junction (escape hatch)."""
    visited: set[tuple[int, int]] = {start}
    path: list[tuple[int, int]] = [start]
    junctions: list[dict] = []
    junction_idx = 0
    while True:
        cur = path[-1]
        neigh = [n for n in neighbour_pixels(cur[0], cur[1], skel) if n not in visited]
        if not neigh:
            break
        if len(neigh) == 1:
            chosen = neigh[0]
        else:
            if junction_idx >= len(branch_choices):
                # No override for this junction; fall back to first neighbour.
                chosen = neigh[0]
                source = "default (no override)"
            else:
                idx = branch_choices[junction_idx]
                if not 0 <= idx < len(neigh):
                    raise RuntimeError(f"branch_choices[{junction_idx}]={idx} out of range (only {len(neigh)} branches)")
                chosen = neigh[idx]
                source = f"branch_choices[{junction_idx}]={idx}"
            junctions.append({
                "at_px": (int(cur[1]), int(cur[0])),
                "chosen_tangent_deg": round(float(np.degrees(np.arctan2(-(chosen[0] - cur[0]), chosen[1] - cur[1]))), 1),
                "alternatives_deg": [round(float(np.degrees(np.arctan2(-(n[0] - cur[0]), n[1] - cur[1]))), 1) for n in neigh if n != chosen],
                "source": source,
            })
            junction_idx += 1
        visited.add(chosen)
        path.append(chosen)
    return path, junctions


def resample_polyline(path: list[tuple[int, int]], n: int) -> tuple[np.ndarray, float]:
    """Resample a pixel polyline to n equally-spaced (in chord length) points.

    Returns (resampled, total_length_px). `resampled` has shape (n, 2) with
    columns (px, py) — column 0 is x to match the (x, y) convention used in
    the canonical JSON.
    """
    pts = np.array([(px, py) for (py, px) in path], dtype=float)
    diffs = np.diff(pts, axis=0)
    segs = np.hypot(diffs[:, 0], diffs[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(segs)])
    total = float(cum[-1])
    if total == 0:
        return pts[:1].repeat(n, axis=0), 0.0
    t = np.linspace(0.0, total, n)
    x = np.interp(t, cum, pts[:, 0])
    y = np.interp(t, cum, pts[:, 1])
    return np.column_stack([x, y]), total


def normalise(
    pixel_xy: np.ndarray,
    baseline_y: int,
    midband_y: int,
    x_origin_px: float,
) -> np.ndarray:
    """Pixel coords → template coords (baseline=0, midband=1, x grows right)."""
    unit_px = baseline_y - midband_y  # positive: image-y grows downward
    if unit_px <= 0:
        raise ValueError(f"baseline_y ({baseline_y}) must be > midband_y ({midband_y})")
    x_norm = (pixel_xy[:, 0] - x_origin_px) / unit_px
    y_norm = (baseline_y - pixel_xy[:, 1]) / unit_px
    return np.column_stack([x_norm, y_norm])


def tangent_deg(prev_xy: np.ndarray, next_xy: np.ndarray) -> float:
    """Tangent direction in degrees, for entry/exit fields (template coords)."""
    dx = float(next_xy[0] - prev_xy[0])
    dy = float(next_xy[1] - prev_xy[1])
    return float(np.degrees(np.arctan2(dy, dx)))


def trace_glyph(glyph_key: str) -> None:
    bboxes = load_bboxes()
    if glyph_key not in bboxes or bboxes[glyph_key] is None:
        raise SystemExit(f"glyph_key {glyph_key!r} has no bbox in loth_bboxes.json")
    bbox = bboxes[glyph_key]
    for required in ("baseline_y", "midband_y", "start_xy"):
        if bbox.get(required) is None:
            raise SystemExit(f"{glyph_key}: missing required field '{required}' in loth_bboxes.json")

    chart_gray = load_chart_grayscale()
    crop = crop_with_excludes(chart_gray, bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    skel_raw, width = skeleton_and_width(mask)
    skel = prune_spurs(skel_raw)

    # start_xy is in chart-global coords; translate into crop-local before snapping.
    sx_global, sy_global = bbox["start_xy"]
    sx_local = sx_global - bbox["x0"]
    sy_local = sy_global - bbox["y0"]
    if not (0 <= sx_local < crop.shape[1] and 0 <= sy_local < crop.shape[0]):
        raise SystemExit(f"start_xy {bbox['start_xy']} is outside the bbox crop")
    snapped, skel_component = resolve_walk_start((sx_local, sy_local), skel)

    # If the user specified waypoints (a stroke-ordered list of points to
    # pass through), chain BFS shortest paths between consecutive waypoints.
    # This handles strokes that retrace themselves — the medial-e draws each
    # peak as up-then-back-down before branching, so the skeleton path must
    # revisit pixels. Otherwise fall back to longest-path-DFS (single visit).
    waypoints_chart = bbox.get("waypoints")
    if waypoints_chart:
        snapped_wps: list[tuple[int, int]] = []
        for wp in waypoints_chart:
            wx_local = wp[0] - bbox["x0"]
            wy_local = wp[1] - bbox["y0"]
            if not (0 <= wx_local < crop.shape[1] and 0 <= wy_local < crop.shape[0]):
                raise SystemExit(f"waypoint {wp} is outside the bbox crop")
            snapped_wps.append(snap_to_any_skel_pixel((wx_local, wy_local), skel_component))
        path, junctions = walk_through_waypoints(skel_component, snapped, snapped_wps)
    else:
        path, junctions = walk_skeleton(skel_component, snapped, bbox.get("branch_choices"))

    n_anchors = int(bbox.get("n_anchors") or DEFAULT_N_ANCHORS)
    pixel_xy_local, path_length_px = resample_polyline(path, n_anchors)
    # Translate back to chart-global pixel coords for the provenance record.
    pixel_xy_global = pixel_xy_local + np.array([bbox["x0"], bbox["y0"]])

    # Half-width per anchor: sample distance-transform at the nearest skeleton
    # pixel along the path (interpolation along a noisy width signal is
    # unhelpful — just take the value at the resampled position).
    hw_px = []
    for (lx, ly) in pixel_xy_local:
        ix, iy = int(round(lx)), int(round(ly))
        ix = int(np.clip(ix, 0, width.shape[1] - 1))
        iy = int(np.clip(iy, 0, width.shape[0] - 1))
        hw_px.append(float(width[iy, ix]))
    hw_px = np.array(hw_px, dtype=float)

    baseline_y = bbox["baseline_y"]
    midband_y = bbox["midband_y"]
    unit_px = float(baseline_y - midband_y)
    x_origin_global_px = float(pixel_xy_global[0, 0])
    norm_xy = normalise(pixel_xy_global, baseline_y, midband_y, x_origin_global_px)
    hw_norm = (hw_px / unit_px).tolist()

    # Build the JSON. Merge with existing file to preserve _note + coupling enums.
    canonical_path = CANONICAL_DIR / f"{glyph_key}_v0.json"
    if canonical_path.exists():
        prev = json.loads(canonical_path.read_text(encoding="utf-8"))
    else:
        prev = {}
    glyph_name = prev.get("glyph", _default_glyph_name(glyph_key))
    position = prev.get("position", glyph_key.split("-")[-1])
    entry_coupling = prev.get("entry", {}).get("coupling", "baseline")
    exit_coupling = prev.get("exit", {}).get("coupling", "baseline")
    note = prev.get("_note", "")

    entry_xy = norm_xy[0].tolist()
    exit_xy = norm_xy[-1].tolist()
    entry_tangent_deg = tangent_deg(norm_xy[0], norm_xy[1])
    exit_tangent_deg = tangent_deg(norm_xy[-2], norm_xy[-1])
    advance = float(max(0.1, norm_xy[:, 0].max() - norm_xy[:, 0].min()))

    data = {
        "version": "v0",
        "glyph": glyph_name,
        "position": position,
        "variant": int(prev.get("variant", 0)),
        "advance": advance,
        "_note": note,
        "_trace": {
            "source": "loth-1866",
            "chart_size": [1633, 1869],
            "bbox": {k: bbox[k] for k in ("y0", "y1", "x0", "x1")},
            "baseline_y": baseline_y,
            "midband_y": midband_y,
            "unit_px": unit_px,
            "n_anchors": n_anchors,
            "path_length_px": round(path_length_px, 1),
            "pixel_anchors": [[round(float(x), 2), round(float(y), 2)] for x, y in pixel_xy_global],
            "half_widths_px": [round(h, 2) for h in hw_px.tolist()],
            "junctions": junctions,
        },
        "entry": {
            "xy": [round(entry_xy[0], 4), round(entry_xy[1], 4)],
            "tangent_deg": round(entry_tangent_deg, 1),
            "coupling": entry_coupling,
        },
        "exit": {
            "xy": [round(exit_xy[0], 4), round(exit_xy[1], 4)],
            "tangent_deg": round(exit_tangent_deg, 1),
            "coupling": exit_coupling,
        },
        "strokes": [
            {
                "curve_type": "bspline",
                "anchors": [[round(float(x), 4), round(float(y), 4)] for x, y in norm_xy],
                "half_widths": [round(h, 4) for h in hw_norm],
            }
        ],
    }

    canonical_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {canonical_path.relative_to(REPO_ROOT)}")
    print(f"  n_anchors        : {n_anchors}")
    print(f"  path length      : {path_length_px:.1f} px  =  {path_length_px / unit_px:.2f} unit")
    print(f"  half-width px    : median={np.median(hw_px):.2f}  min={hw_px.min():.2f}  max={hw_px.max():.2f}")
    print(f"  half-width norm  : median={np.median(hw_px / unit_px):.3f}  max={hw_px.max() / unit_px:.3f}")
    print(f"  y_norm range     : min={norm_xy[:, 1].min():.2f}  max={norm_xy[:, 1].max():.2f}")
    print(f"  junctions        : {len(junctions)}")
    for k, j in enumerate(junctions):
        if j.get("source") == "waypoint":
            print(f"    [{k}] segment {j['from_px']} → {j['to_px']}  length={j['segment_length_px']}px  (waypoint)")
        else:
            print(f"    [{k}] at {j['at_px']}  chose {j['chosen_tangent_deg']}° (alts {j['alternatives_deg']})  via {j['source']}")


def _default_glyph_name(glyph_key: str) -> str:
    """Fallback glyph name if the canonical JSON didn't exist yet."""
    base = glyph_key.split("-")[0]
    # special-case: long-s allograph
    return "ſ" if base == "s" and glyph_key.startswith("s-medial") else base


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: python -m mvp.tools.trace_skeleton <glyph_key>")
    trace_glyph(sys.argv[1])


if __name__ == "__main__":
    main()
