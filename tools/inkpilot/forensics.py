"""Where the Lotse leaves the ink, and which of its mechanisms put it there.

A diagnostic sensor, not an arm: it changes no constant of `pilot.py` and
produces no candidate. It answers one question the route ledger had open —
the pilot rides the measured skeleton by construction, so every point of its
output that lies OUTSIDE the inked body was placed there by a named mechanism
of the follower, and this module says which one, where, and how far.

Three pieces:

* `ink_slack_field` — the signed distance from the inked BODY, per crop pixel.
  The fixtures carry the skeleton plus `width_map` (the EDT half width per
  skeleton pixel, the Schwellzug channel), so the body is the union of disks
  of radius `width_map[p]` around each skeleton pixel `p`. Under the usual
  medial-axis approximation (judge a point by its NEAREST skeleton pixel) that
  union has the closed form `slack = edt - width_map[nearest]`: negative
  inside the ink, positive outside, in crop pixels.

* `traced_pilot_word` — `pilot.pilot_word` re-run with a provenance label on
  every emitted point. It deliberately MIRRORS the orchestration instead of
  importing a hook into it, so the follower stays untouched during a
  measurement round; the duplication is made safe by `assert_matches_pilot`,
  which holds the traced strokes against the real ones bit for bit.

* `jump_events` — maximal runs of points outside the body, each attributed to
  the mechanism that emitted them and annotated with the ink it left behind
  (junction degree, local half width, whether the map crosses itself there).

The cause vocabulary is the follower's own, one label per mechanism that can
put a point somewhere other than a rail:

* `bridge_no_rail` — the Viterbi's BRIDGE state where the map has NO rail
  within `BOARD_RADIUS_UNITS`. The pilot did not choose to leave the ink;
  the map led it over blank paper. This is a composition placement finding,
  not a follower finding.
* `bridge_priced_out` — the BRIDGE state WITH rails in reach: the ride was
  dearer than the bridge's per-sample price, or `MAX_RIDE_UNITS` cut the
  walk. This one is the follower's economy.
* `forced_window` — v0.8/v0.9 map right-of-way in a pinned crossing window.
* `double_zone` — v0.5/v0.7 map right-of-way in a ride-double zone.
* `tail_runout` — v0.16 rail continuation past the map's end.
* `rail` — an ordinary ride point, on the skeleton by construction.

Two mechanisms MOVE points rather than emitting them, so they are recorded as
modifiers next to the cause: `pin` (v0.9/v0.11 window and knot pinning) and
`untwist` (v0.13 pairwise mirroring).

Measurement layer only: reads the frozen fixtures, writes CSV and PNG. No DB,
no `core/` write, no candidate.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

from tools.inkpilot import pilot
from tools.inkpilot.pilot import (
    MAP_CROSSING_WINDOW_UNITS,
    MAP_RUN_PIN_KNOTS,
    RIDE_DOUBLE_MAP_PRIORITY,
    RIDE_DOUBLE_ZONE_MARGIN_UNITS,
    SAMPLE_STEP_UNITS,
    TAIL_RUNOUT_MAX_UNITS,
    UNTWIST_WINDOW_UNITS,
    PilotGraph,
    map_crossing_masks,
    map_self_intersections,
    map_strokes_px,
    pin_run_mask,
    resample,
    ride_double_min_gap,
)
from tools.wordlab.cases import WordCase
from tools.wordlab.derive import derive_word


# Point causes, ordered by precedence when several apply to one sample.
CAUSE_FORCED = "forced_window"
CAUSE_ZONE = "double_zone"
CAUSE_NO_RAIL = "bridge_no_rail"
CAUSE_PRICED = "bridge_priced_out"
CAUSE_TAIL = "tail_runout"
CAUSE_RAIL = "rail"

MAP_CAUSES = (CAUSE_FORCED, CAUSE_ZONE, CAUSE_NO_RAIL, CAUSE_PRICED)


@dataclass
class JumpEvent:
    """One maximal run of emitted points outside the inked body."""

    word: str
    stroke: int
    first: int  # point index within the stroke
    last: int
    cause: str  # the dominant emitting mechanism of the run
    causes: dict[str, int] = field(default_factory=dict)
    modifiers: dict[str, int] = field(default_factory=dict)
    max_slack_xh: float = 0.0
    mean_slack_xh: float = 0.0
    arc_xh: float = 0.0
    x_xh: float = 0.0  # position of the deepest point, crop px / xh
    y_xh: float = 0.0
    entry_dir_deg: float = 0.0  # heading before the run
    exit_dir_deg: float = 0.0  # heading after it
    turn_deg: float = 0.0  # the direction change across the run
    near_degree: int = 0  # skeleton node degree at the deepest point
    local_halfwidth_xh: float = 0.0  # ink half width where it left
    map_selfcross_xh: float = 0.0  # distance to the nearest map self-crossing
    # The composed MAP's own slack at the same place. It splits the blame:
    # a departure whose map was already outside the ink is inherited from the
    # composition, one whose map sat ON the ink was manufactured by the ride.
    map_slack_xh: float = 0.0


def ink_slack_field(skel: np.ndarray, width_map: np.ndarray | None) -> np.ndarray:
    """Signed distance from the inked BODY per crop pixel, in crop px.

    Negative inside the ink, positive outside. With no `width_map` the body
    collapses to the skeleton itself and the field is the plain EDT.
    """
    skel = np.asarray(skel, dtype=bool)
    edt, idx = distance_transform_edt(~skel, return_indices=True)
    if width_map is None:
        return np.asarray(edt, dtype=float)
    widths = np.asarray(width_map, dtype=float)
    return np.asarray(edt, dtype=float) - widths[idx[0], idx[1]]


def sample_field(field_px: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Nearest-pixel read of a per-pixel field at float crop coordinates.

    Points off the crop are read at the clamped border and get the border's
    value plus their overshoot, so a run-out over the page edge still scores
    as leaving the ink rather than silently as ink.
    """
    h, w = field_px.shape
    x = np.asarray(pts[:, 0], dtype=float)
    y = np.asarray(pts[:, 1], dtype=float)
    xi = np.clip(np.rint(x), 0, w - 1).astype(int)
    yi = np.clip(np.rint(y), 0, h - 1).astype(int)
    over = np.hypot(x - xi, y - yi)
    return field_px[yi, xi] + np.maximum(over - 0.75, 0.0)


def _assemble_traced(
    pg: PilotGraph,
    samples: np.ndarray,
    seq: list,
    map_mask: np.ndarray | None,
    sample_cause: list[str],
    sample_pinned: np.ndarray,
) -> tuple[np.ndarray, list[str], list[bool]]:
    """`pilot._assemble_ride` with a cause and a pin flag per emitted point."""
    out: list[np.ndarray] = []
    causes: list[str] = []
    pinned: list[bool] = []
    prev = None
    for k, (s, loc) in enumerate(zip(samples, seq, strict=True)):
        if loc is None or (map_mask is not None and map_mask[k]):
            out.append(s)
            causes.append(sample_cause[k])
            pinned.append(bool(sample_pinned[k]))
            prev = None
            continue
        chain = [pg.px_of(loc)] if prev is None else list(pg.ride(prev, loc)[1:])
        out.extend(chain)
        causes.extend([CAUSE_RAIL] * len(chain))
        pinned.extend([False] * len(chain))
        prev = loc
    pts = np.asarray(out, dtype=float).reshape(-1, 2)
    keep = np.ones(len(pts), dtype=bool)
    keep[1:] = np.hypot(*np.diff(pts, axis=0).T) > 1e-9
    kept = np.flatnonzero(keep)
    return pts[keep], [causes[i] for i in kept], [pinned[i] for i in kept]


def traced_pilot_word(case: WordCase) -> tuple[list[np.ndarray], list[list[str]], list[list[set]], dict]:
    """`pilot.pilot_word`, with a cause and a modifier set per emitted point.

    Mirrors the orchestration step by step. `assert_matches_pilot` is the
    guard that keeps the mirror honest.
    """
    result = derive_word(case)
    pg = PilotGraph(np.asarray(case.skel, dtype=bool))
    xh_px = float(result.registration.get("xh_px", result.xh_px))
    maps = map_strokes_px(result)
    samples_per = [resample(s, SAMPLE_STEP_UNITS * xh_px) for s in maps]
    forced = (
        map_crossing_masks(samples_per, MAP_CROSSING_WINDOW_UNITS)
        if MAP_CROSSING_WINDOW_UNITS > 0.0
        else [None] * len(maps)
    )
    raw = [
        pilot._assign_stroke(pg, s, xh_px, samples=sp, forced_priority=f)
        for s, sp, f in zip(maps, samples_per, forced, strict=True)
    ]

    masks = None
    if RIDE_DOUBLE_MAP_PRIORITY:
        seen: dict[tuple[int, int], int] = {}
        counter = 0
        min_gap = ride_double_min_gap()
        masks = []
        for samples, seq, _ in raw:
            mask = np.zeros(len(samples), dtype=bool)
            for k, loc in enumerate(seq):
                counter += 1
                if loc is None:
                    continue
                px = pg.px_of(loc)
                key = (int(round(px[0])), int(round(px[1])))
                last = seen.get(key)
                if last is not None and counter - last > min_gap:
                    mask[k] = True
                else:
                    seen[key] = counter
            masks.append(mask)
        if RIDE_DOUBLE_ZONE_MARGIN_UNITS > 0.0:
            reach = int(round(RIDE_DOUBLE_ZONE_MARGIN_UNITS / SAMPLE_STEP_UNITS))
            widened = []
            for mask in masks:
                out = mask.copy()
                for k in np.flatnonzero(mask):
                    lo = max(0, k - reach)
                    out[lo : k + reach + 1] = True
                widened.append(out)
            masks = widened

    board_radius = pilot.BOARD_RADIUS_UNITS * xh_px
    assignments = []
    pin_flags: list[np.ndarray] = []
    if MAP_RUN_PIN_KNOTS == "off":
        for samples, seq, forced_mask in raw:
            assignments.append((pilot._pin_forced_runs(pg, samples, seq, forced_mask), seq))
            pin_flags.append(np.asarray(forced_mask, dtype=bool))
    else:
        knot_rows = pilot.map_crossing_knots(pg, [s for s, _, _ in raw], xh_px)
        for si, (samples, seq, forced_mask) in enumerate(raw):
            bridge = np.asarray([loc is None for loc in seq], dtype=bool)
            zone = masks[si] if masks is not None else np.zeros(len(samples), dtype=bool)
            run_mask = pin_run_mask(MAP_RUN_PIN_KNOTS, bridge, np.asarray(forced_mask, dtype=bool), zone)
            assignments.append((pilot._pin_map_runs(pg, samples, seq, run_mask, knot_rows[si]), seq))
            pin_flags.append(np.asarray(run_mask, dtype=bool))

    strokes: list[np.ndarray] = []
    causes: list[list[str]] = []
    mods: list[list[set]] = []
    for si, ((samples, seq), (raw_samples, _, forced_mask)) in enumerate(zip(assignments, raw, strict=True)):
        fm = np.asarray(forced_mask, dtype=bool)
        zone = masks[si] if masks is not None else np.zeros(len(samples), dtype=bool)
        # A sample's cause is the mechanism that made it emit the MAP point.
        # Rails within boarding radius separate the two bridge classes: the
        # map over blank paper is a composition finding, a bridge next to a
        # usable rail is the follower's own price.
        near = (
            pg.tree.query_ball_point(raw_samples, r=board_radius)
            if pg.tree is not None
            else [[] for _ in range(len(raw_samples))]
        )
        sample_cause: list[str] = []
        for k, loc in enumerate(seq):
            if fm[k]:
                sample_cause.append(CAUSE_FORCED)
            elif loc is None:
                sample_cause.append(CAUSE_NO_RAIL if not near[k] else CAUSE_PRICED)
            elif zone[k]:
                sample_cause.append(CAUSE_ZONE)
            else:
                sample_cause.append(CAUSE_RAIL)
        pts, cs, pinned = _assemble_traced(
            pg, samples, seq, masks[si] if masks is not None else None, sample_cause, pin_flags[si]
        )
        strokes.append(pts)
        causes.append(cs)
        mods.append([{"pin"} if p else set() for p in pinned])

    keep = [i for i, s in enumerate(strokes) if len(s) >= 2]
    strokes = [strokes[i] for i in keep]
    causes = [causes[i] for i in keep]
    mods = [mods[i] for i in keep]

    if TAIL_RUNOUT_MAX_UNITS > 0.0:
        grown = pilot.run_out_tails(strokes, pg, xh_px, TAIL_RUNOUT_MAX_UNITS)
        for i, (old, new) in enumerate(zip(strokes, grown, strict=True)):
            head = len(new) - len(old)
            if head <= 0:
                continue
            # `run_out_tails` extends the end first, then the reversed start,
            # so the old chain sits unchanged somewhere inside the new one —
            # find the offset instead of reasoning about the two growths.
            lead = next((k for k in range(head + 1) if np.allclose(new[k : k + len(old)], old)), 0)
            tail = head - lead
            causes[i] = [CAUSE_TAIL] * lead + causes[i] + [CAUSE_TAIL] * tail
            mods[i] = [set() for _ in range(lead)] + mods[i] + [set() for _ in range(tail)]
        strokes = grown

    untwisted = 0
    if UNTWIST_WINDOW_UNITS > 0.0:
        soll = map_self_intersections(samples_per, xh_px) if pilot.UNTWIST_SOLL_BUDGET else None
        before = [s.copy() for s in strokes]
        strokes, untwisted = pilot.untwist_strokes(strokes, xh_px, UNTWIST_WINDOW_UNITS, soll_points=soll)
        for i, (old, new) in enumerate(zip(before, strokes, strict=True)):
            if len(old) != len(new):
                continue  # the mirror preserves lengths; be defensive anyway
            moved = ~np.all(np.isclose(old, new), axis=1)
            for k in np.flatnonzero(moved):
                mods[i][int(k)] = mods[i][int(k)] | {"untwist"}

    detail = {
        "xh_px": xh_px,
        "registration": result.registration,
        "baseline_row": result.baseline_row,
        "untwisted": untwisted,
        "map_selfcross": map_self_intersections(samples_per, xh_px),
        "map_samples": samples_per,
    }
    return strokes, causes, mods, detail


def assert_matches_pilot(case: WordCase, strokes: list[np.ndarray]) -> None:
    """The mirror's guard: traced strokes must equal the follower's, bit for bit."""
    real, _ = pilot.pilot_word(case)
    if len(real) != len(strokes):
        raise AssertionError(f"{case.id}: traced {len(strokes)} strokes, pilot {len(real)}")
    for i, (a, b) in enumerate(zip(real, strokes, strict=True)):
        if a.shape != b.shape or not np.array_equal(a, b):
            raise AssertionError(f"{case.id}: stroke {i} diverges from pilot_word")


def _headings(pts: np.ndarray, first: int, last: int) -> tuple[float, float, float]:
    """Heading before and after a run, plus the turn across it, in degrees."""

    def ang(a: np.ndarray, b: np.ndarray) -> float:
        d = b - a
        return float(np.degrees(np.arctan2(d[1], d[0]))) if np.hypot(*d) > 1e-9 else 0.0

    entry = ang(pts[max(0, first - 2)], pts[first]) if first > 0 else ang(pts[first], pts[min(len(pts) - 1, first + 1)])
    exit_ = (
        ang(pts[last], pts[min(len(pts) - 1, last + 2)])
        if last < len(pts) - 1
        else ang(pts[max(0, last - 1)], pts[last])
    )
    turn = (exit_ - entry + 180.0) % 360.0 - 180.0
    return entry, exit_, turn


def jump_events(
    case: WordCase,
    strokes: list[np.ndarray],
    causes: list[list[str]],
    mods: list[list[set]],
    detail: dict,
    *,
    threshold_xh: float = 0.0,
    min_points: int = 2,
) -> list[JumpEvent]:
    """Maximal runs of emitted points outside the inked body, attributed."""
    xh = float(detail["xh_px"])
    slack_field = ink_slack_field(case.skel, case.width_map)
    pg_skel = np.asarray(case.skel, dtype=bool)
    ys, xs = np.nonzero(pg_skel)
    skel_xy = np.column_stack([xs.astype(float), ys.astype(float)])
    widths = np.asarray(case.width_map, dtype=float) if case.width_map is not None else None
    selfcross = np.asarray(detail.get("map_selfcross")).reshape(-1, 2)
    map_pts = np.vstack(detail["map_samples"]).astype(float).reshape(-1, 2)
    map_slack = sample_field(slack_field, map_pts) / xh
    # Node degree per skeleton pixel is only needed near the deepest point of
    # an event, so it is read off the graph lazily through the nearest node.
    graph = PilotGraph(pg_skel).graph
    node_xy = np.asarray([[float(x), float(y)] for x, y in graph.nodes], dtype=float).reshape(-1, 2)
    node_deg = [len(graph.incident.get(i, [])) for i in range(len(graph.nodes))]

    events: list[JumpEvent] = []
    for si, pts in enumerate(strokes):
        slack = sample_field(slack_field, pts) / xh
        off = slack > threshold_xh
        if not off.any():
            continue
        edges = np.flatnonzero(np.diff(np.concatenate([[False], off, [False]]).astype(int)))
        for a, b in zip(edges[0::2], edges[1::2], strict=True):
            first, last = int(a), int(b) - 1
            if last - first + 1 < min_points:
                continue
            run_causes = causes[si][first : last + 1]
            counts: dict[str, int] = {}
            for c in run_causes:
                counts[c] = counts.get(c, 0) + 1
            mod_counts: dict[str, int] = {}
            for m in mods[si][first : last + 1]:
                for name in m:
                    mod_counts[name] = mod_counts.get(name, 0) + 1
            # The dominant cause ignores `rail` unless the run is ALL rail —
            # a rail point drifting outside a thin body is a width artefact,
            # a map point next to it is the actual departure.
            ranked = {k: v for k, v in counts.items() if k != CAUSE_RAIL} or counts
            cause = max(ranked.items(), key=lambda kv: (kv[1], kv[0]))[0]
            seg = pts[first : last + 1]
            deep = first + int(np.argmax(slack[first : last + 1]))
            arc = float(np.hypot(*np.diff(seg, axis=0).T).sum()) / xh if len(seg) > 1 else 0.0
            entry, exit_, turn = _headings(pts, first, last)
            d_node = np.hypot(*(node_xy - pts[deep]).T) if len(node_xy) else np.asarray([np.inf])
            near_i = int(np.argmin(d_node))
            d_skel = np.hypot(*(skel_xy - pts[deep]).T)
            nearest_skel = int(np.argmin(d_skel))
            hw = float(widths[int(ys[nearest_skel]), int(xs[nearest_skel])]) / xh if widths is not None else 0.0
            d_cross = float(np.min(np.hypot(*(selfcross - pts[deep]).T))) / xh if len(selfcross) else float("inf")
            events.append(
                JumpEvent(
                    word=case.id,
                    stroke=si,
                    first=first,
                    last=last,
                    cause=cause,
                    causes=counts,
                    modifiers=mod_counts,
                    max_slack_xh=float(slack[deep]),
                    mean_slack_xh=float(np.mean(slack[first : last + 1])),
                    arc_xh=arc,
                    x_xh=float(pts[deep][0]) / xh,
                    y_xh=float(pts[deep][1]) / xh,
                    entry_dir_deg=entry,
                    exit_dir_deg=exit_,
                    turn_deg=turn,
                    near_degree=int(node_deg[near_i]) if len(node_xy) and d_node[near_i] < xh else 0,
                    local_halfwidth_xh=hw,
                    map_selfcross_xh=d_cross,
                    map_slack_xh=float(map_slack[int(np.argmin(np.hypot(*(map_pts - pts[deep]).T)))]),
                )
            )
    return events


CSV_COLUMNS = [
    "word",
    "stroke",
    "first",
    "last",
    "cause",
    "cause_mix",
    "modifiers",
    "max_slack_xh",
    "mean_slack_xh",
    "arc_xh",
    "x_xh",
    "y_xh",
    "entry_dir_deg",
    "exit_dir_deg",
    "turn_deg",
    "near_degree",
    "local_halfwidth_xh",
    "map_selfcross_xh",
    "map_slack_xh",
]


def write_csv(events: list[JumpEvent], out: Path) -> None:
    """One row per jump event, in the order the pilot wrote them."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_COLUMNS)
        for e in events:
            writer.writerow(
                [
                    e.word,
                    e.stroke,
                    e.first,
                    e.last,
                    e.cause,
                    ";".join(f"{k}={v}" for k, v in sorted(e.causes.items())),
                    ";".join(f"{k}={v}" for k, v in sorted(e.modifiers.items())),
                    f"{e.max_slack_xh:.4f}",
                    f"{e.mean_slack_xh:.4f}",
                    f"{e.arc_xh:.4f}",
                    f"{e.x_xh:.3f}",
                    f"{e.y_xh:.3f}",
                    f"{e.entry_dir_deg:.1f}",
                    f"{e.exit_dir_deg:.1f}",
                    f"{e.turn_deg:.1f}",
                    e.near_degree,
                    f"{e.local_halfwidth_xh:.4f}",
                    "" if e.map_selfcross_xh == float("inf") else f"{e.map_selfcross_xh:.3f}",
                    f"{e.map_slack_xh:.4f}",
                ]
            )


def blame(event: JumpEvent, *, tol_xh: float = 0.02) -> str:
    """Who put the pen outside the ink: the map, or the ride itself.

    `inherited` — the composed map was already that far out and the follower
    reproduced it; `pin` / `untwist` / `ride` — the departure exceeds the
    map's own by more than `tol_xh`, so a mechanism of the ride made it.
    """
    if event.max_slack_xh - event.map_slack_xh <= tol_xh:
        return "inherited"
    if "untwist" in event.modifiers:
        return "untwist"
    if "pin" in event.modifiers:
        return "pin"
    return "ride"


def _draw_event(ax, case: WordCase, strokes: list[np.ndarray], detail: dict, event: JumpEvent) -> None:
    """The panel body: crop, ink outline, map, ride, and the marked run."""
    xh = float(detail["xh_px"])
    pts = strokes[event.stroke]
    seg = pts[event.first : event.last + 1]
    h, w = np.asarray(case.skel).shape
    pad = 1.6 * xh
    x0 = max(0.0, float(seg[:, 0].min()) - pad)
    x1 = min(float(w - 1), float(seg[:, 0].max()) + pad)
    y0 = max(0.0, float(seg[:, 1].min()) - pad)
    y1 = min(float(h - 1), float(seg[:, 1].max()) + pad)

    if case.crop is not None:
        # The crop is a float intensity image: 0 = ink, 1 = paper.
        ax.imshow(np.asarray(case.crop, dtype=float), cmap="gray", vmin=0.0, vmax=1.0, origin="upper")
    body = ink_slack_field(case.skel, case.width_map) <= 0.0
    ax.contour(body.astype(float), levels=[0.5], colors=["#3f7fbf"], linewidths=0.9)
    for m in detail["map_samples"]:
        ax.plot(m[:, 0], m[:, 1], color="#c8a23c", lw=1.1, alpha=0.85, zorder=3)
    for s in strokes:
        ax.plot(s[:, 0], s[:, 1], color="#2f2f2f", lw=1.3, zorder=4)
    ax.plot(seg[:, 0], seg[:, 1], color="#c0392b", lw=2.6, zorder=5)
    ax.scatter(seg[:, 0], seg[:, 1], s=9, color="#c0392b", zorder=6)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(
        f"{event.word} · {event.cause} · {blame(event)}\n"
        f"Stift {event.max_slack_xh:.3f} xh neben der Tinte, Karte {event.map_slack_xh:+.3f} xh",
        fontsize=8.5,
    )


LEGEND_LABELS = (
    ("#3f7fbf", 0.9, "Tintenkörper (Rand)"),
    ("#c8a23c", 1.1, "Karte (komponiert)"),
    ("#2f2f2f", 1.3, "Ritt (Lotse)"),
    ("#c0392b", 2.6, "Absprung"),
)


def _legend_handles():
    import matplotlib.pyplot as plt

    return [plt.Line2D([], [], color=c, lw=w, label=t) for c, w, t in LEGEND_LABELS]


def plot_event(case: WordCase, strokes: list[np.ndarray], detail: dict, event: JumpEvent, out: Path) -> None:
    """One figure for one jump event."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5.2, 4.4), dpi=150)
    _draw_event(ax, case, strokes, detail, event)
    ax.legend(handles=_legend_handles(), fontsize=6.5, loc="lower right", framealpha=0.9)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def plot_panel(panels: list[tuple[WordCase, list[np.ndarray], dict, JumpEvent]], out: Path) -> None:
    """Several events side by side — the figure a doc can carry."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, len(panels), figsize=(4.3 * len(panels), 3.9), dpi=130)
    axes = np.atleast_1d(axes)
    for ax, (case, strokes, detail, event) in zip(axes, panels, strict=True):
        _draw_event(ax, case, strokes, detail, event)
    axes[-1].legend(handles=_legend_handles(), fontsize=6.5, loc="lower right", framealpha=0.9)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*", help="fixture case ids; default: the frozen dev split")
    parser.add_argument("--set", dest="which", default="words", choices=["words", "pairs"])
    parser.add_argument("--style", default="suetterlin")
    parser.add_argument("--threshold", type=float, default=0.0, help="slack in xh above which a point is off the ink")
    parser.add_argument("--min-points", type=int, default=2)
    parser.add_argument("--csv", type=Path, default=Path("runs/lotse-forensics/events.csv"))
    parser.add_argument("--png-dir", type=Path, default=None, help="render one figure per event above --png-depth")
    parser.add_argument("--png-depth", type=float, default=0.10, help="min max_slack_xh for a figure")
    parser.add_argument("--no-verify", action="store_true", help="skip the bit-equality guard against pilot_word")
    parser.add_argument(
        "--panel", default="", help="comma-separated WORD:FIRST event keys to render side by side (see --panel-out)"
    )
    parser.add_argument("--panel-out", type=Path, default=None)
    args = parser.parse_args(argv)

    from tools.tracebench.sets import TRACEBENCH_DEV_IDS
    from tools.wordlab.cases import iter_fixture_word_cases

    wanted = set(args.ids) or set(TRACEBENCH_DEV_IDS)
    panel_keys = [k for k in args.panel.split(",") if k]
    panels: dict[str, tuple] = {}
    events: list[JumpEvent] = []
    for case in iter_fixture_word_cases(which=args.which, style=args.style):
        if not case.scorable or case.skel is None or case.id not in wanted:
            continue
        strokes, causes, mods, detail = traced_pilot_word(case)
        if not args.no_verify:
            assert_matches_pilot(case, strokes)
        found = jump_events(
            case, strokes, causes, mods, detail, threshold_xh=args.threshold, min_points=args.min_points
        )
        events.extend(found)
        total = sum(len(s) for s in strokes)
        off = sum(e.last - e.first + 1 for e in found)
        print(f"  {case.id:14} events {len(found):3d}  off-ink points {off:4d}/{total:5d}", flush=True)
        if args.png_dir is not None:
            for e in found:
                if e.max_slack_xh < args.png_depth:
                    continue
                name = f"{e.word}-{e.first}-{e.cause}-{blame(e)}.png"
                plot_event(case, strokes, detail, e, args.png_dir / name)
        for e in found:
            key = f"{e.word}:{e.first}"
            if key in panel_keys:
                panels[key] = (case, strokes, detail, e)

    write_csv(events, args.csv)
    if args.panel_out is not None and panel_keys:
        missing = [k for k in panel_keys if k not in panels]
        if missing:
            print(f"panel: no such event(s): {', '.join(missing)}", file=sys.stderr)
        else:
            plot_panel([panels[k] for k in panel_keys], args.panel_out)
            print(f"wrote {args.panel_out}")
    print(f"\nwrote {args.csv} ({len(events)} events)")
    print(f"{'cause':<16}{'blame':<12}{'n':>4}  {'depth med':>10}{'excess med':>12}")
    grouped: dict[tuple[str, str], list[JumpEvent]] = {}
    for e in events:
        grouped.setdefault((e.cause, blame(e)), []).append(e)
    for (cause, who), group in sorted(grouped.items(), key=lambda kv: -len(kv[1])):
        depth = float(np.median([e.max_slack_xh for e in group]))
        excess = float(np.median([e.max_slack_xh - e.map_slack_xh for e in group]))
        print(f"{cause:<16}{who:<12}{len(group):>4}  {depth:>10.4f}{excess:>+12.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
