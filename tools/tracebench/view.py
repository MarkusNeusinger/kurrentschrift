"""The duel viewer: every method's word trace over the plate, and how it is written.

`tools/tracebench/run.py` says WHICH tracing is closer. It cannot say what the
difference looks like, and it cannot say anything at all about the half of the
question the owner asked on 2026-08-14: the methods next to each other AND next
to the author's own pen re-tracing, both as the FINAL trace over the crop and as
the writing ORDER that produced it.

So this module builds one self-contained HTML page (the `tools/fitview`
discipline: data:-URI images, inline CSS and JS, no fonts, no CDN, no network at
view time) with, per word:

* the crop at 2x with an SVG overlay in CROP-PIXEL coordinates — one `<g>` per
  method plus one for the hand reference, toggleable, consistently coloured;
* the per-word numbers of a `--rows` report beside each method, so "it looks
  worse here" and "it measures worse here" are read in one place;
* a writing-order animation over `stroke-dasharray`/`stroke-dashoffset`
  (`docs/reference/animation-rendering.md` §1), all VISIBLE methods started in
  sync, each stroke's duration proportional to its arc length (constant pen
  speed) and every pen lift a real pause and a real gap.

Two rules it keeps rather than trusts:

* **The frame math is never re-derived.** Both sides travel through
  `BenchFrame.trace_to_bench` and back out through `bench_to_crop_px`, exactly
  as the bench measures them. A viewer that placed the ink by its own arithmetic
  would show a disagreement the ruler never saw.
* **The bytes are deterministic.** Nothing here reads a clock; the run stamp is
  passed in via `--title`, so the same inputs produce the same file and a
  chronik entry can be diffed against its predecessor.

No DB, no API, no writes into the repository tree: candidates come from the
file-provider contract, the reference and the crop from the frozen fixture root.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from PIL import Image

from tools.tracebench.candidates import STATUS_OK, Candidate, file_provider
from tools.tracebench.counters import (
    RESAMPLE_STEP_UNITS,
    classified_pass_points,
    crossing_points,
    resampled_strokes,
    structure_zones,
)
from tools.tracebench.frames import BenchFrame, arc_length, classify_strokes, concat_body
from tools.tracebench.metric import dtw
from tools.tracebench.reference import DEFAULT_FIXTURES_DIR, Reference, ReferenceEntry, load_reference
from tools.tracebench.run import find_fixture_root
from tools.tracebench.sets import TRACEBENCH_DEV_IDS
from tools.tracebench.soll import SollRow, ductus_soll


# The crop `tools/wordbench/export_fixtures.py` freezes beside `word.json` —
# the same background `tools/wordbench/run.py` and `tools/wordlab` draw over.
CROP_FILE = "crop.png"

# The stage: the crop at 2x. Small enough to keep a ten-word page light, large
# enough that a 0.1 xh deviation is visible at a normal reading distance.
STAGE_ZOOM = 2
# Strokes are drawn NON-SCALING (`vector-effect`), so these are screen pixels at
# any zoom rather than crop units — a hairline stays a hairline.
STROKE_WIDTH = 1.5
# Marks (i-dot, u-Deckstrich, umlaut) are thinner: they are not body ink, and
# the eye should not read a dot as a stroke (`frames.classify_strokes`).
MARK_STROKE_WIDTH = 1.0
# The detected-structure markers (screen px like the stroke widths): a crossing
# is a small ring, a retrace zone a wide translucent band along its pass.
CROSS_MARK_RADIUS_PX = 3.0
# Path coordinates are rounded, which is what makes two runs byte-identical.
COORD_DECIMALS = 2

# Constant pen speed, measured in X-HEIGHTS per second rather than pixels: a
# plate scanned at twice the resolution must not write at twice the speed.
PEN_SPEED_XH_PER_S = 6.0
# A pen lift is a pause, never a bridge (`animation-rendering.md` §1.5).
PEN_LIFT_PAUSE_MS = 120
# Playback rates the toolbar offers; 1.0 must be among them.
SPEED_CHOICES = (0.5, 1.0, 2.0)

# The hand re-tracing is GREEN — `WERKBANK_COLORS.traceOverInk` of
# `app/src/sections/admin/shell/model.ts`, i.e. the exact colour the word editor
# draws a stored trace over plate ink in. The same ink means the same thing on
# both surfaces.
COLOR_REFERENCE = "#00b37e"
# The chain baseline is the engine's own answer, so it takes the Werkbank's
# engine red; the follower takes fitview's marker blue.
COLOR_CHAIN = "#e02030"
COLOR_FOLLOWER = "#1565c0"
# The prior-free control gets a pinned high-chroma cyan: the palette's
# order-based hand-out gave it the brown, which disappears against the
# sepia plate ink (owner review 2026-08-15).
COLOR_CONTROL = "#00acc1"
# Everything else, handed out in order — deterministic, never random.
PALETTE = ("#8e24aa", "#ef6c00", "#c2185b", "#3949ab", "#00838f", "#6d4c41")

# Label fragments that pin a colour by MEANING rather than by call order, so the
# chain stays red and the follower blue however the CLI arguments are ordered.
CHAIN_MARKERS = ("chain", "kette")
FOLLOWER_MARKERS = ("follow", "folger", "wächter", "waechter", "guard")
CONTROL_MARKERS = ("kontrolle", "routeg", "control", "nullprobe")
# The Lotse (tools/inkpilot) gets a pinned vivid pink: the order-based
# palette handed it a hue that vanished against the sepia plate (owner
# review of the first inspection page, 2026-08-16).
COLOR_PILOT = "#e91e63"
PILOT_MARKERS = ("lotse", "pilot")

REFERENCE_LABEL = "Hand (Referenz)"

# ---- the residual profile: candidate minus hand, along the headline's own DTW.
# Plot geometry in CSS pixels — fixed, so two chronik pages diff cleanly.
RESID_PLOT_W = 860
RESID_PLOT_H = 120
RESID_MARGIN_L = 44
RESID_MARGIN_R = 10
RESID_MARGIN_T = 8
RESID_MARGIN_B = 26
# Peak-preserving decimation: at most this many chart samples per candidate.
# Within each stride window the WORST sample survives, so a genuine spike can
# never be smoothed away by the display — only the flat stretches thin out.
RESID_MAX_SAMPLES = 500
# The y-axis never collapses below this, so a clean word still shows its scale
# and two words' profiles stay visually comparable.
RESID_MIN_YMAX_XH = 0.3
# Hover map decimation: the probe that jumps to the word image needs ~0.1 xh
# of arc precision, not the full 0.02 xh sampling.
RESID_MAP_STRIDE = 5


# ------------------------------------------------------------------ geometry


@dataclass(frozen=True)
class StrokePath:
    """One pen stroke, ready to draw: its path data, its length, its class."""

    d: str
    length: float  # crop pixels — the arc the animation spends time on
    mark: bool


@dataclass(frozen=True)
class Layer:
    """One method's trace over one word (the hand reference is a layer too)."""

    label: str
    color: str
    kind: str  # "reference" | "candidate"
    strokes: list[StrokePath]
    status: str = STATUS_OK
    detail: str = ""
    numbers: dict[str, Any] | None = None
    structure: "StructureMarks | None" = None

    @property
    def ok(self) -> bool:
        return self.status == STATUS_OK and bool(self.strokes)


def stroke_path_data(points_px: np.ndarray) -> str:
    """A crop-pixel polyline as SVG path data — rounded, hence deterministic."""
    pts = np.asarray(points_px, dtype=float).reshape(-1, 2)
    if len(pts) == 0:
        return ""
    head = f"M {pts[0][0]:.{COORD_DECIMALS}f},{pts[0][1]:.{COORD_DECIMALS}f}"
    tail = "".join(f" L {x:.{COORD_DECIMALS}f},{y:.{COORD_DECIMALS}f}" for x, y in pts[1:])
    return head + tail


def mark_flags(strokes_bench: Sequence[np.ndarray]) -> list[bool]:
    """Per stroke: is this a delayed mark? — `classify_strokes`' own verdict.

    The classifier returns a partition into `(body, marks)` and loses the index,
    but it fills both lists in input order, so walking the input against the
    mark list in one pass restores the per-stroke answer. The `index > 0` guard
    is the classifier's own first rule, restated here only so two identical
    strokes cannot shift the walk (a word never opens with its own diacritic).

    The rule itself is NOT reimplemented: whatever `classify_strokes` decides is
    what gets drawn thin.
    """
    _, marks = classify_strokes([np.asarray(s, dtype=float).reshape(-1, 2) for s in strokes_bench])
    flags: list[bool] = []
    at = 0
    for index, stroke in enumerate(strokes_bench):
        pts = np.asarray(stroke, dtype=float).reshape(-1, 2)
        is_mark = (
            index > 0 and at < len(marks) and marks[at].shape == pts.shape and bool(np.array_equal(marks[at], pts))
        )
        if is_mark:
            at += 1
        flags.append(is_mark)
    return flags


@dataclass(frozen=True)
class StructureMarks:
    """The DETECTED structures of one layer, ready to draw over its trace."""

    crossings: list[tuple[float, float]]  # crop px
    passes: list[tuple[str, str]]  # (pass path data in crop px, class: retrace | touch | overlap)
    zones: int = 0  # merged retrace ZONES — the ruler's own count (`structure_zones`)
    touches: int = 0  # touch zones (writing past each other)
    overlaps: int = 0  # overlap zones (a mark riding the body)


def structure_marks(frame: BenchFrame, strokes_bench: list[np.ndarray]) -> StructureMarks:
    """Display-only detections — the COUNTERS' own v2 classification, drawn.

    Everything comes from `tools.tracebench.counters` (§14 v2): the piercing
    crossings as rings, and every kept anti-parallel pass with its class —
    retrace (one stroke writing the same ink twice), touch (writing past each
    other) and overlap (a mark riding the body). The page draws what the ruler
    counts, so the owner's audit reads one truth, not two.
    """
    strokes = [np.asarray(s, dtype=float).reshape(-1, 2) for s in strokes_bench]
    crossings = [(float(x), float(y)) for x, y in frame.bench_to_crop_px(crossing_points(strokes))]
    class_zones = structure_zones(strokes)
    passes = [
        (stroke_path_data(frame.bench_to_crop_px(pass_pts)), cls) for pass_pts, cls in classified_pass_points(strokes)
    ]
    return StructureMarks(
        crossings=crossings,
        passes=passes,
        zones=int(len(class_zones.retrace_mids)),
        touches=int(len(class_zones.touch_mids)),
        overlaps=int(len(class_zones.overlap_mids)),
    )


def layer_paths(
    frame: BenchFrame, strokes: Sequence[Any], registration_px: dict[str, Any] | None, xh_px: float | None
) -> tuple[list[StrokePath], StructureMarks]:
    """A stored trace -> drawable crop-pixel paths + its detected structures.

    `trace_to_bench` applies the row's own registration and `bench_to_crop_px`
    the inverse of the frame — the identical two hops the scorer makes, so the
    page cannot show an alignment the measurement did not use.
    """
    bench = frame.trace_to_bench(list(strokes), registration_px, xh_px)
    flags = mark_flags(bench)
    out: list[StrokePath] = []
    for stroke, is_mark in zip(bench, flags, strict=True):
        px = frame.bench_to_crop_px(stroke)
        out.append(StrokePath(d=stroke_path_data(px), length=arc_length(px), mark=is_mark))
    return [s for s in out if s.d], structure_marks(frame, bench)


def trace_paths(
    frame: BenchFrame, strokes: Sequence[Any], registration_px: dict[str, Any] | None, xh_px: float | None
) -> list[StrokePath]:
    """The paths half of `layer_paths` — kept for callers that draw only ink."""
    return layer_paths(frame, strokes, registration_px, xh_px)[0]


# `SollRow`/`ductus_soll` moved to `tools.tracebench.soll` — the bench report
# consumes the same targets, so the one place the Soll is computed serves both.


# ------------------------------------------------------------------ residuals


@dataclass(frozen=True)
class ResidualLine:
    """One candidate's residual profile: (arc position, distance) in x-heights."""

    label: str
    color: str
    points: np.ndarray  # (k, 2) — x = arc along the REFERENCE body ink, y = distance


def body_arc_positions(resampled_body: list[np.ndarray]) -> tuple[np.ndarray, list[float]]:
    """Per concatenated body sample: its INK arc position, plus the pen lifts.

    Arc accumulates within a stroke and adds NOTHING at a pen lift — the jump
    between two strokes is never written ink (`metric.rasterise_strokes` keeps
    the same rule). The second value is the arc position of every lift, which
    is where the chart draws its stroke-boundary markers.
    """
    xs: list[np.ndarray] = []
    lifts: list[float] = []
    offset = 0.0
    for index, stroke in enumerate(resampled_body):
        pts = np.asarray(stroke, dtype=float).reshape(-1, 2)
        seg = np.hypot(*np.diff(pts, axis=0).T) if len(pts) > 1 else np.zeros(0)
        arc = np.concatenate([[0.0], np.cumsum(seg)])[: len(pts)]
        xs.append(offset + arc)
        offset += float(arc[-1]) if len(arc) else 0.0
        if index < len(resampled_body) - 1:
            lifts.append(offset)
    return (np.concatenate(xs) if xs else np.zeros(0)), lifts


def residual_values(ref_seq: np.ndarray, cand_seq: np.ndarray) -> np.ndarray:
    """Per reference sample: mean matched distance of the headline's own DTW.

    The alignment is `metric.dtw`'s optimal warping path — the exact pairing
    `dtw_xh` averages over, never a nearest-neighbour re-derivation (which
    would read a backwards stroke as agreement). Equal point counts are not
    assumed: where several candidate points are absorbed by one reference
    sample, that sample carries their mean distance.
    """
    result = dtw(ref_seq, cand_seq)
    matched_ref = np.asarray(ref_seq, dtype=float)[result.pairs[:, 0]]
    matched_cand = np.asarray(cand_seq, dtype=float)[result.pairs[:, 1]]
    d = np.hypot(*(matched_ref - matched_cand).T)
    sums = np.zeros(len(ref_seq))
    counts = np.zeros(len(ref_seq))
    np.add.at(sums, result.pairs[:, 0], d)
    np.add.at(counts, result.pairs[:, 0], 1.0)
    return sums / np.maximum(counts, 1.0)


def decimate_peaks(points: np.ndarray, max_samples: int = RESID_MAX_SAMPLES) -> np.ndarray:
    """At most `max_samples` chart points — per window, the WORST one survives.

    Plain striding could drop a one-window spike and show "sauber" where the
    ruler measured "daneben"; keeping each window's maximum preserves every
    peak exactly (a clean stretch stays near zero either way).
    """
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    if len(pts) <= max_samples:
        return pts
    stride = int(np.ceil(len(pts) / max_samples))
    keep = [
        pts[start : start + stride][int(np.argmax(pts[start : start + stride, 1]))]
        for start in range(0, len(pts), stride)
    ]
    return np.asarray(keep, dtype=float).reshape(-1, 2)


# -------------------------------------------------------------------- colours


def assign_colors(labels: Sequence[str]) -> dict[str, str]:
    """One colour per candidate label — by meaning first, then by order.

    Deterministic for a given label list, and stable across rounds for the two
    labels that matter: a chain baseline is always red, a follower always blue,
    so two chronik entries months apart are read the same way.
    """
    colors: dict[str, str] = {}
    taken = 0
    for label in labels:
        lowered = label.lower()
        if any(marker in lowered for marker in CHAIN_MARKERS):
            colors[label] = COLOR_CHAIN
        elif any(marker in lowered for marker in FOLLOWER_MARKERS):
            colors[label] = COLOR_FOLLOWER
        elif any(marker in lowered for marker in CONTROL_MARKERS):
            colors[label] = COLOR_CONTROL
        elif any(marker in lowered for marker in PILOT_MARKERS):
            colors[label] = COLOR_PILOT
        else:
            colors[label] = PALETTE[taken % len(PALETTE)]
            taken += 1
    return colors


# ------------------------------------------------------------------ selection


def select_ids(reference: Reference, split: str, words: str | None) -> list[str]:
    """Specimen ids to show, in manifest order.

    The frozen split constant is IMPORTED (`TRACEBENCH_DEV_IDS`), the bench's
    refusals deliberately are not: `run.select_split` dies on a confirmation set
    under five words and warns that `--split all` is not a held-out number.
    Both are rules about REPORTING a number. This page reports none — it shows
    ink — and refusing to draw three words would only push the work back onto
    screenshots.

    `--words` names its subjects outright and therefore overrides the split
    rather than intersecting with it.
    """
    authored = reference.authored_ids()
    if words:
        wanted = {w.strip() for w in words.split(",") if w.strip()}
        return [i for i in authored if i in wanted or reference.entries[i].word in wanted]
    if split == "dev":
        return [i for i in authored if i in TRACEBENCH_DEV_IDS]
    if split == "confirm":
        return [i for i in authored if i not in TRACEBENCH_DEV_IDS]
    return list(authored)


def parse_pairs(values: Sequence[str], *, flag: str) -> list[tuple[str, Path]]:
    """`LABEL=PATH` arguments, in the order given, refusing the ambiguous ones."""
    pairs: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for raw in values or []:
        label, sep, path = raw.partition("=")
        label, path = label.strip(), path.strip()
        if not sep or not label or not path:
            raise SystemExit(f"{flag} {raw!r}: expected LABEL=PATH (e.g. {flag} chain=temp/chain.json)")
        if label == REFERENCE_LABEL:
            raise SystemExit(f"{flag} {raw!r}: {REFERENCE_LABEL!r} is the hand reference's own label")
        if label in seen:
            raise SystemExit(f"{flag} {raw!r}: label {label!r} was given twice")
        seen.add(label)
        pairs.append((label, Path(path)))
    return pairs


def load_report_rows(path: Path) -> dict[str, dict[str, Any]]:
    """A tracebench `--json` report as `{specimen_id: row}`."""
    try:
        payload = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"--rows {path}: {exc}") from None
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise SystemExit(f"--rows {path}: no 'rows' list — this is not a tracebench --json report")
    return {str(r["id"]): r for r in rows if isinstance(r, dict) and r.get("id")}


# ------------------------------------------------------------------- the page


_CSS = """
  :root { color-scheme: light; }
  body { font: 14px/1.45 system-ui, sans-serif; margin: 20px; background: #fafaf7; color: #222; }
  h1 { font-size: 20px; margin: 0 0 4px; }
  .meta { color: #555; margin-bottom: 14px; }
  .bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px; }
  .tabs { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
  button { font: inherit; padding: 3px 10px; border: 1px solid #ccc; border-radius: 4px;
           background: #fff; color: #222; cursor: pointer; }
  button[aria-current="true"] { border-color: #00806a; background: #e8f6f1; font-weight: 600; }
  .stage { position: relative; display: inline-block; background: #fff; border: 1px solid #ddd; }
  .stage img { display: block; }
  .stage svg { position: absolute; left: 0; top: 0; overflow: visible; }
  .legend { margin: 10px 0 6px; display: flex; flex-wrap: wrap; gap: 14px; align-items: center; }
  .legend label { display: inline-flex; align-items: center; gap: 5px; }
  .swatch { display: inline-block; width: 12px; height: 12px; border-radius: 2px; vertical-align: -1px; }
  table.numbers { border-collapse: collapse; font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; }
  table.numbers th, table.numbers td { border: 1px solid #e2e2dd; padding: 2px 8px; text-align: right; }
  table.numbers th:first-child, table.numbers td:first-child { text-align: left; }
  table.numbers thead th { background: #f2f2ec; font-weight: 600; }
  .detail { color: #b45309; }
  .hint { color: #666; margin-top: 8px; }
  details.methods { margin: 6px 0 12px; color: #444; }
  details.methods summary { cursor: pointer; font-weight: 600; }
  details.methods ul { margin: 6px 0 0; padding-left: 18px; }
  details.methods li { margin-bottom: 4px; max-width: 78ch; }
  details.methods .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%;
                         margin-right: 6px; vertical-align: -1px; }
  section.word > h2 { font-size: 16px; margin: 0 0 8px; }
  tr.soll-row td { color: #6b6b64; background: #f4f4ee; font-style: italic; }
  g.structure circle.cross { fill: none; stroke-width: 1.4; }
  g.structure path.zone { fill: none; stroke-width: 7; opacity: 0.22; }
  g.structure path.zone.overlap { stroke-dasharray: 5 4; stroke-width: 4; opacity: 0.4; }
  g.structure path.zone.touch { stroke-dasharray: 1.5 4; stroke-width: 4; opacity: 0.4; stroke-linecap: round; }
  body.nostructure g.structure { display: none; }
  .resid { margin-top: 12px; }
  svg.resid-chart { display: block; background: #fff; border: 1px solid #ddd; touch-action: none; }
  svg.resid-chart text { font: 10px system-ui, sans-serif; fill: #666; }
  svg.resid-chart rect.plot { fill: none; stroke: #e2e2dd; }
  svg.resid-chart line.grid { stroke: #f0f0ea; }
  svg.resid-chart line.lift { stroke: #bbb; stroke-dasharray: 3 3; }
  svg.resid-chart polyline { fill: none; stroke-width: 1.5; }
  svg.resid-chart line.resid-cursor { stroke: #f59e0b; visibility: hidden; }
  circle.probe { fill: none; stroke: #f59e0b; stroke-width: 2; visibility: hidden; }
"""

# `__SPEED__`/`__PAUSE__` are substituted below. Written as a plain string (not
# an f-string) so the JS braces stay JS braces.
_JS = r"""
(function () {
  var SPEED_XH_PER_S = __SPEED__;
  var PAUSE_MS = __PAUSE__;
  var sections = [].slice.call(document.querySelectorAll('section.word'));
  var tabs = [].slice.call(document.querySelectorAll('button.word-tab'));
  var running = [];
  var index = 0;
  var rate = 1;

  function stop() {
    running.forEach(function (a) { try { a.cancel(); } catch (err) { /* already gone */ } });
    running = [];
  }
  function finalState() {
    stop();
    // The resting trace carries NO dash at all: dasharray + pathLength +
    // non-scaling-stroke mis-scale in some engines and swallow the tail of
    // the longest paths (seen: the hand trace of "unter" ending at the t).
    // The dash exists only while the writing animation runs.
    [].slice.call(document.querySelectorAll('path.ink')).forEach(function (p) {
      p.style.strokeDasharray = 'none';
      p.style.strokeDashoffset = '0';
    });
  }
  function show(next) {
    index = Math.max(0, Math.min(sections.length - 1, next));
    sections.forEach(function (s, n) { s.hidden = n !== index; });
    tabs.forEach(function (b, n) { b.setAttribute('aria-current', n === index ? 'true' : 'false'); });
    finalState();
  }
  function play() {
    stop();
    var section = sections[index];
    if (!section) { return; }
    var xh = parseFloat(section.getAttribute('data-xh')) || 1;
    [].slice.call(section.querySelectorAll('g.layer')).forEach(function (g) {
      if (g.style.display === 'none') { return; }
      var t = 0;
      [].slice.call(g.querySelectorAll('path.ink')).forEach(function (p) {
        var len = parseFloat(p.getAttribute('data-len')) || 0;
        // Dash in REAL user units via getTotalLength — the normalised
        // unit-pathLength + dash + non-scaling-stroke combination
        // mis-renders during the animation in some engines (ink appearing
        // to write on the left while erasing on the right; owner review
        // 2026-08-15). The geometric length avoids the buggy code path.
        var geo = len;
        try { geo = p.getTotalLength() || len; } catch (err) { /* keep data-len */ }
        // Constant pen speed: the arc decides the duration, the rate only
        // scales it. The duration uses the SAME geometric length as the dash
        // (the rounded path differs slightly from the unrounded data-len).
        var dur = Math.max(80, (geo / xh) / SPEED_XH_PER_S * 1000) / rate;
        if (typeof p.animate === 'function') {
          p.style.strokeDasharray = geo + ' ' + geo;
          p.style.strokeDashoffset = String(geo);
          running.push(p.animate(
            [{ strokeDashoffset: String(geo) }, { strokeDashoffset: '0' }],
            { duration: dur, delay: t, fill: 'forwards', easing: 'linear' }
          ));
        } else {
          p.style.strokeDasharray = 'none';
          p.style.strokeDashoffset = '0';
        }
        t += dur + PAUSE_MS / rate;  // the pen lift: a pause, never a bridge
      });
    });
    // When the writing finishes NATURALLY, drop back into the dash-free
    // resting state — otherwise the finished strokes keep their dash and the
    // tail-clip this page just fixed can reappear. A cancelled run (word
    // switch, replay) rejects the promise and has already been cleaned up.
    if (running.length) {
      Promise.all(running.map(function (a) { return a.finished; }))
        .then(function () { finalState(); })
        .catch(function () { /* cancelled elsewhere */ });
    }
  }
  function setVisible(label, visible) {
    [].slice.call(document.querySelectorAll('g.layer')).forEach(function (g) {
      if (g.getAttribute('data-label') === label) { g.style.display = visible ? '' : 'none'; }
    });
    [].slice.call(document.querySelectorAll('input.toggle')).forEach(function (c) {
      if (c.getAttribute('data-label') === label) { c.checked = visible; }
    });
  }
  // Feinschliff — a pure DISPLAY stage at the consumer, per the v0.6 verdict
  // (messjournal §14: the ruler never sees the pixel zigzag, so smoothing
  // belongs to the renderer, never into the measured candidate). Candidates
  // only; the hand reference and the mark dots stay raw.
  function smoothD(d, iters) {
    var nums = d.match(/-?\d+(?:\.\d+)?/g);
    if (!nums || nums.length < 8) { return d; }
    var xs = [], ys = [], i, k;
    for (i = 0; i < nums.length - 1; i += 2) { xs.push(parseFloat(nums[i])); ys.push(parseFloat(nums[i + 1])); }
    for (i = 0; i < iters; i++) {
      var nx = xs.slice(), ny = ys.slice();
      for (k = 1; k < xs.length - 1; k++) {
        nx[k] = (xs[k - 1] + 2 * xs[k] + xs[k + 1]) / 4;
        ny[k] = (ys[k - 1] + 2 * ys[k] + ys[k + 1]) / 4;
      }
      xs = nx; ys = ny;
    }
    var out = 'M ' + xs[0].toFixed(2) + ',' + ys[0].toFixed(2);
    for (k = 1; k < xs.length; k++) { out += ' L ' + xs[k].toFixed(2) + ',' + ys[k].toFixed(2); }
    return out;
  }
  function setFeinschliff(on) {
    [].slice.call(document.querySelectorAll('g.layer[data-kind="candidate"] path.ink')).forEach(function (p) {
      if (p.classList.contains('mark')) { return; }
      if (!p.getAttribute('data-d-raw')) { p.setAttribute('data-d-raw', p.getAttribute('d')); }
      p.setAttribute('d', on ? smoothD(p.getAttribute('data-d-raw'), 3) : p.getAttribute('data-d-raw'));
    });
    finalState();
  }
  document.addEventListener('change', function (ev) {
    var t = ev.target;
    if (!t) { return; }
    if (t.classList && t.classList.contains('toggle')) { setVisible(t.getAttribute('data-label'), t.checked); }
    if (t.id === 'speed') { rate = parseFloat(t.value) || 1; }
    if (t.id === 'structure') { document.body.classList.toggle('nostructure', !t.checked); }
    if (t.id === 'feinschliff') { setFeinschliff(t.checked); }
  });
  document.addEventListener('click', function (ev) {
    var t = ev.target;
    if (!t || !t.id && !(t.classList && t.classList.contains('word-tab'))) { return; }
    if (t.classList && t.classList.contains('word-tab')) { show(parseInt(t.getAttribute('data-index'), 10)); }
    else if (t.id === 'prev') { show(index - 1); }
    else if (t.id === 'next') { show(index + 1); }
    else if (t.id === 'play') { play(); }
    else if (t.id === 'final') { finalState(); }
  });
  document.addEventListener('keydown', function (ev) {
    var tag = (ev.target && ev.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') { return; }
    if (ev.key === 'ArrowLeft') { show(index - 1); ev.preventDefault(); }
    else if (ev.key === 'ArrowRight') { show(index + 1); ev.preventDefault(); }
  });
  // The residual probe: hovering the profile finds the nearest reference
  // sample by arc position and pins the orange probe onto that spot of the
  // hand's trace in the stage above — "the mountain in the chart is HERE in
  // the word".
  [].slice.call(document.querySelectorAll('svg.resid-chart')).forEach(function (svg) {
    var section = svg.closest('section.word');
    if (!section) { return; }
    var mapEl = section.querySelector('script.resid-map');
    var probe = section.querySelector('circle.probe');
    var cursor = svg.querySelector('line.resid-cursor');
    var data = null;
    svg.addEventListener('pointermove', function (ev) {
      if (!mapEl || !cursor) { return; }
      if (!data) {
        try { data = JSON.parse(mapEl.textContent); } catch (err) { data = { arc: [], px: [] }; }
      }
      if (!data.arc.length) { return; }
      var rect = svg.getBoundingClientRect();
      var ml = parseFloat(svg.getAttribute('data-ml')) || 0;
      var pw = parseFloat(svg.getAttribute('data-pw')) || 1;
      var arcTotal = parseFloat(svg.getAttribute('data-arc')) || 1;
      var a = (ev.clientX - rect.left - ml) / pw * arcTotal;
      a = Math.max(0, Math.min(arcTotal, a));
      var lo = 0, hi = data.arc.length - 1;
      while (lo < hi) { var mid = (lo + hi) >> 1; if (data.arc[mid] < a) { lo = mid + 1; } else { hi = mid; } }
      var x = ml + a / arcTotal * pw;
      cursor.setAttribute('x1', x.toFixed(1));
      cursor.setAttribute('x2', x.toFixed(1));
      cursor.style.visibility = 'visible';
      if (probe && data.px[lo]) {
        probe.setAttribute('cx', data.px[lo][0]);
        probe.setAttribute('cy', data.px[lo][1]);
        probe.style.visibility = 'visible';
      }
    });
    svg.addEventListener('pointerleave', function () {
      if (cursor) { cursor.style.visibility = 'hidden'; }
      if (probe) { probe.style.visibility = 'hidden'; }
    });
  });
  show(0);
})();
"""


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "–"
    if isinstance(value, bool):
        return "ja" if value else "nein"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _numbers_cells(numbers: dict[str, Any] | None) -> str:
    """The four §14 columns a `--rows` report contributes, or dashes."""
    row = numbers or {}
    cross = "–"
    if row.get("cross_matched") is not None or row.get("cross_spurious") is not None:
        cross = f"{row.get('cross_matched', 0)}/{row.get('cross_spurious', 0)}"
    return (
        f"<td>{_fmt(row.get('dtw_xh'))}</td>"
        f"<td>{_fmt(row.get('aiou'), 3)}</td>"
        f"<td>{cross}</td>"
        f"<td>{_fmt(row.get('retrace_arc_ratio'), 2)}</td>"
    )


def _layer_svg(layer: Layer, layer_id: str) -> str:
    paths = "".join(
        f'<path class="ink{" mark" if s.mark else ""}" d="{s.d}" data-len="{s.length:.2f}" '
        f'stroke-width="{MARK_STROKE_WIDTH if s.mark else STROKE_WIDTH}" '
        f'vector-effect="non-scaling-stroke"></path>'
        for s in layer.strokes
    )
    structure = ""
    if layer.structure and (layer.structure.crossings or layer.structure.passes):
        rings = "".join(
            f'<circle class="cross" cx="{x:.{COORD_DECIMALS}f}" cy="{y:.{COORD_DECIMALS}f}" '
            f'r="{CROSS_MARK_RADIUS_PX:g}" vector-effect="non-scaling-stroke"></circle>'
            for x, y in layer.structure.crossings
        )
        zones = "".join(
            f'<path class="zone {cls}" d="{d}" vector-effect="non-scaling-stroke"></path>'
            for d, cls in layer.structure.passes
        )
        structure = f'<g class="structure">{zones}{rings}</g>'
    return (
        f'<g class="layer" id="{layer_id}" data-label="{html.escape(layer.label, quote=True)}" '
        f'data-kind="{html.escape(layer.kind, quote=True)}" '
        f'fill="none" stroke="{layer.color}" stroke-linecap="round" stroke-linejoin="round">'
        f"{structure}{paths}</g>"
    )


def _legend_item(layer: Layer) -> str:
    note = "" if layer.ok else f'<span class="detail"> · {html.escape(layer.status)}</span>'
    return (
        f'<label><input class="toggle" type="checkbox" checked '
        f'data-label="{html.escape(layer.label, quote=True)}">'
        f'<span class="swatch" style="background:{layer.color}"></span>'
        f"{html.escape(layer.label)}{note}</label>"
    )


def _numbers_row(layer: Layer) -> str:
    note = "" if layer.ok else f' <span class="detail">{html.escape(layer.detail or layer.status)}</span>'
    # Every layer — the hand INCLUDED — states its own detected counts, from the
    # very detectors that placed the rings and bands on the stage (the owner's
    # check: the numbers must be there and must agree with what is drawn). Only
    # the four report columns stay relative-to-reference and dash out for the
    # reference itself.
    if layer.structure is not None:
        own = (
            f"<td>{len(layer.structure.crossings)}</td><td>{layer.structure.zones}</td>"
            f"<td>{layer.structure.touches}</td><td>{layer.structure.overlaps}</td>"
        )
    else:
        own = "<td>–</td>" * 4
    cells = _numbers_cells(layer.numbers) if layer.kind == "candidate" else "<td>–</td>" * 4
    return (
        f'<tr class="layer-row"><td><span class="swatch" style="background:{layer.color}"></span> '
        f"{html.escape(layer.label)}{note}</td><td>{len(layer.strokes)}</td>{own}{cells}</tr>"
    )


def _soll_row(row: SollRow) -> str:
    title = f' title="{html.escape(row.per_letter, quote=True)}"' if row.per_letter else ""
    strokes = "–" if row.strokes is None else str(row.strokes)
    return (
        f'<tr class="soll-row"{title}><td>◇ {html.escape(row.label)}</td><td>{strokes}</td>'
        f"<td>{row.crossings}</td><td>{row.zones}</td><td>{row.touches}</td><td>{row.overlaps}</td>"
        + "<td>–</td>" * 4
        + "</tr>"
    )


def _resid_grid_step(ymax: float) -> float:
    """Horizontal gridline spacing that keeps the label count readable."""
    if ymax <= 0.6:
        return 0.1
    if ymax <= 1.2:
        return 0.2
    return 0.5


def residual_chart(lines: list[ResidualLine], lifts: list[float], arc_total: float) -> str:
    """The residual profile of one word as a self-contained SVG.

    x = arc along the hand's body ink, y = distance to the candidate along the
    headline's own DTW pairing — flat near zero reads "sauber", a mountain
    reads "daneben", and hovering asks the map script where in the word it is.
    """
    if not lines or arc_total <= 0.0:
        return ""
    ymax = max(RESID_MIN_YMAX_XH, float(np.ceil(max(float(line.points[:, 1].max()) for line in lines) * 10.0) / 10.0))
    width = RESID_MARGIN_L + RESID_PLOT_W + RESID_MARGIN_R
    height = RESID_MARGIN_T + RESID_PLOT_H + RESID_MARGIN_B

    def sx(a: float) -> float:
        return RESID_MARGIN_L + a / arc_total * RESID_PLOT_W

    def sy(v: float) -> float:
        return RESID_MARGIN_T + RESID_PLOT_H * (1.0 - v / ymax)

    grid: list[str] = []
    step = _resid_grid_step(ymax)
    v = 0.0
    while v <= ymax + 1e-9:
        y = sy(v)
        grid.append(
            f'<line class="grid" x1="{RESID_MARGIN_L}" y1="{y:.1f}" '
            f'x2="{RESID_MARGIN_L + RESID_PLOT_W}" y2="{y:.1f}"></line>'
            f'<text x="{RESID_MARGIN_L - 5}" y="{y + 3.5:.1f}" text-anchor="end">{v:.1f}</text>'
        )
        v += step
    x_step = 2.0 if arc_total <= 12.0 else 5.0
    a = 0.0
    while a <= arc_total + 1e-9:
        x = sx(a)
        grid.append(
            f'<line class="grid" x1="{x:.1f}" y1="{RESID_MARGIN_T}" '
            f'x2="{x:.1f}" y2="{RESID_MARGIN_T + RESID_PLOT_H}"></line>'
            f'<text x="{x:.1f}" y="{RESID_MARGIN_T + RESID_PLOT_H + 12}" text-anchor="middle">{a:g}</text>'
        )
        a += x_step
    lift_marks = "".join(
        f'<line class="lift" x1="{sx(lift):.1f}" y1="{RESID_MARGIN_T}" '
        f'x2="{sx(lift):.1f}" y2="{RESID_MARGIN_T + RESID_PLOT_H}"></line>'
        for lift in lifts
    )
    # The candidate groups reuse the trace layers' class + data-label, so the
    # legend checkbox that hides a method's ink hides its profile with it.
    curves = "".join(
        f'<g class="layer" data-label="{html.escape(line.label, quote=True)}">'
        f'<polyline stroke="{line.color}" points="'
        + " ".join(f"{sx(px):.1f},{sy(py):.1f}" for px, py in line.points)
        + '"></polyline></g>'
        for line in lines
    )
    caption = (
        f'<text x="{RESID_MARGIN_L + RESID_PLOT_W / 2:.0f}" y="{height - 3}" text-anchor="middle">'
        f"Bogenlänge entlang der Hand-Nachfahrung (xh) → Abstand des Verfahrens (xh)</text>"
    )
    cursor = (
        f'<line class="resid-cursor" x1="0" y1="{RESID_MARGIN_T}" x2="0" y2="{RESID_MARGIN_T + RESID_PLOT_H}"></line>'
    )
    return (
        f'<svg class="resid-chart" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'data-ml="{RESID_MARGIN_L}" data-pw="{RESID_PLOT_W}" data-arc="{arc_total:.2f}">'
        f'<rect class="plot" x="{RESID_MARGIN_L}" y="{RESID_MARGIN_T}" '
        f'width="{RESID_PLOT_W}" height="{RESID_PLOT_H}"></rect>'
        f"{''.join(grid)}{lift_marks}{curves}{cursor}{caption}</svg>"
    )


def residual_map_json(arc_x: np.ndarray, crop_pts: np.ndarray) -> str:
    """The hover map: decimated `(arc, crop px)` pairs, hand-formatted JSON.

    Hand-formatted so the byte layout is fixed — `json.dumps` float repr would
    couple the page bytes to the platform's shortest-repr behaviour.
    """
    idx = list(range(0, len(arc_x), RESID_MAP_STRIDE))
    # The last sample always rides along: the cursor clamps to the full arc,
    # so a stride that ends short would leave the probe unable to reach the
    # word's end (Copilot review, PR #388).
    if idx and idx[-1] != len(arc_x) - 1:
        idx.append(len(arc_x) - 1)
    arc = ",".join(f"{arc_x[i]:.2f}" for i in idx)
    px = ",".join(f"[{crop_pts[i][0]:.1f},{crop_pts[i][1]:.1f}]" for i in idx)
    return f'{{"arc":[{arc}],"px":[{px}]}}'


def word_section(
    index: int,
    entry: ReferenceEntry,
    crop_uri: str,
    size: tuple[int, int],
    layers: list[Layer],
    soll: tuple[SollRow, ...] = (),
    resid: str = "",
) -> str:
    """One word's stage, legend and numbers table — hidden unless it is current."""
    width, height = size
    # Paint order is not reading order: the hand reference goes LAST so that no
    # candidate can cover it — a hidden ground truth reads as agreement. The
    # legend and the table keep the reference first, where it belongs.
    painted = [layer for layer in layers if layer.kind != "reference"] + [
        layer for layer in layers if layer.kind == "reference"
    ]
    svg_layers = "".join(_layer_svg(layer, f"w{index}-l{n}") for n, layer in enumerate(painted))
    legend = "".join(_legend_item(layer) for layer in layers)
    reference_rows = [layer for layer in layers if layer.kind == "reference"]
    candidate_rows = [layer for layer in layers if layer.kind != "reference"]
    rows = (
        "".join(_numbers_row(layer) for layer in reference_rows)
        + "".join(_soll_row(row) for row in soll)
        + "".join(_numbers_row(layer) for layer in candidate_rows)
    )
    return (
        f'<section class="word" data-id="{html.escape(entry.specimen_id, quote=True)}" '
        f'data-word="{html.escape(entry.word, quote=True)}" data-xh="{entry.frame.xh:.4f}" hidden>'
        f"<h2>„{html.escape(entry.word)}“ · {html.escape(entry.specimen_id)} · {html.escape(entry.kind)}</h2>"
        f'<div class="stage" style="width:{width * STAGE_ZOOM}px;height:{height * STAGE_ZOOM}px">'
        f'<img src="{crop_uri}" width="{width * STAGE_ZOOM}" height="{height * STAGE_ZOOM}" '
        f'alt="Ausschnitt „{html.escape(entry.word, quote=True)}“">'
        f'<svg viewBox="0 0 {width} {height}" width="{width * STAGE_ZOOM}" height="{height * STAGE_ZOOM}">'
        f'{svg_layers}<circle class="probe" r="4" vector-effect="non-scaling-stroke"></circle></svg></div>'
        f'<div class="legend">{legend}</div>'
        f'<table class="numbers"><thead><tr><th>Verfahren</th><th>Striche</th><th>Kreuzungen</th>'
        f"<th>Retrace-Zonen</th><th>Berührungen</th><th>Überlagerungen</th><th>dtw_xh</th><th>aiou</th>"
        f"<th>cross m/s</th><th>retrace</th></tr></thead><tbody>{rows}</tbody></table>"
        f"{resid}"
        f"</section>"
    )


def method_explainer(labels: Sequence[str], colors: dict[str, str]) -> str:
    """A lay one-liner per layer: what each method USES (owner review 2026-08-15).

    Matched on the same label markers the colours use, with an honest generic
    fallback — a page must never invent a description for an unknown candidate.
    """
    lines = [
        (
            COLOR_REFERENCE,
            REFERENCE_LABEL,
            "die eigene Nachfahrung am Tablet — die Messlatte, gegen die alle anderen antreten (nutzt: Mensch + Stift).",
        )
    ]
    for label in labels:
        lowered = label.lower()
        if any(m in lowered for m in FOLLOWER_MARKERS):
            text = (
                "wie die Kette, zieht die Bahn danach näher an die Tinte — ein Wächter verbietet dabei, "
                "neue Kreuzungen oder Doppelstriche zu erfinden (nutzt: Duktus-Bibliothek + Tinte)."
            )
        elif any(m in lowered for m in CHAIN_MARKERS):
            text = (
                "der Kettenfit: legt unsere Duktus-Vorlagen (Strichfolge, Kreuzungswissen) an die Tinte "
                "und verformt sie elastisch; ein Wächter verbietet dabei, Kreuzungen oder Doppelstriche "
                "zu erfinden (nutzt: Duktus-Bibliothek + Tinte)."
            )
        elif "inksight" in lowered:
            text = (
                "InkSight, ein offenes Google-Modell (Apache 2.0): hat Schreibbewegungen aus Millionen "
                "moderner Schriftproben gelernt, kennt weder Sütterlin noch unsere Vorlagen — hier roh "
                "angewendet (nutzt: gelerntes Modell, keinen Duktus)."
            )
        elif any(m in lowered for m in CONTROL_MARKERS):
            text = (
                "die Nullprobe: reine Bildverarbeitung (Skelett + plausibelste Wegfortsetzung), "
                "kein Modell, kein Duktus — die Probe ohne Wirkstoff, die zeigt, was das Duktus-Wissen wert ist."
            )
        elif any(m in lowered for m in PILOT_MARKERS):
            text = (
                "der Lotse: fährt die gemessene Tinten-Mitte direkt (Skelettgraph) und fragt an jeder "
                "Abzweigung den Duktus wie eine Karte — links oder rechts? (nutzt: Tinte als Geometrie, "
                "Duktus als Route)."
            )
        else:
            text = "Kandidat aus Datei (keine hinterlegte Kurzbeschreibung)."
        lines.append((colors.get(label, "#555"), label, text))
    items = "".join(
        f'<li><span class="dot" style="background:{color}"></span><b>{html.escape(label)}</b> — {html.escape(text)}</li>'
        for color, label, text in lines
    )
    return f'<details class="methods" open><summary>Die Verfahren in einem Satz</summary><ul>{items}</ul></details>'


def render_html(sections: list[str], tabs: list[tuple[str, str]], *, title: str, meta: str, explainer: str = "") -> str:
    """The whole page: title block, word tabs, playback controls, the words."""
    heading = "tracebench — Duell"
    page_title = f"{heading} · {title}" if title else heading
    tab_html = "".join(
        f'<button class="word-tab" type="button" data-index="{n}" aria-current="false">{html.escape(word)}</button>'
        for n, (word, _) in enumerate(tabs)
    )
    speeds = "".join(
        f'<option value="{rate:g}"{" selected" if rate == 1.0 else ""}>{f"{rate:g}".replace(".", ",")}×</option>'
        for rate in SPEED_CHOICES
    )
    js = _JS.replace("__SPEED__", f"{PEN_SPEED_XH_PER_S:g}").replace("__PAUSE__", f"{PEN_LIFT_PAUSE_MS:g}")
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(page_title)}</title>
<style>{_CSS}</style>
</head>
<body>
<h1>{html.escape(heading)}</h1>
<div class="meta">{meta}</div>
{explainer}
<div class="tabs">{tab_html}</div>
<div class="bar">
  <button id="prev" type="button">← zurück</button>
  <button id="next" type="button">weiter →</button>
  <button id="play" type="button">Schreiben abspielen</button>
  <button id="final" type="button">Fertige Bahn</button>
  <label for="speed">Tempo</label>
  <select id="speed">{speeds}</select>
  <label><input type="checkbox" id="structure" checked> Struktur</label>
  <label><input type="checkbox" id="feinschliff"> Feinschliff (nur Anzeige)</label>
</div>
{"".join(sections)}
<div class="hint">Die Seite öffnet mit der FERTIGEN Bahn; „Schreiben abspielen“ schreibt alle
eingeschalteten Verfahren gleichzeitig in Schreibreihenfolge — Strichdauer proportional zur Bogenlänge
(konstante Federgeschwindigkeit), jedes Absetzen eine echte Pause. Pfeiltasten ←/→ wechseln das Wort.
„Struktur“ zeigt je Ebene die DETEKTIERTEN Strukturen der v2-Zähler (messjournal §14):
Ringe = DURCHSTOSS-Kreuzungen (eine Linie kommt auf einer Seite herein und auf der anderen
heraus), breite Bänder = Retrace-Zonen (ein Strich schreibt dieselbe Tinte zweimal, bogen-nah),
gestrichelt = ÜBERLAGERUNG zweier Striche (z.&nbsp;B. der t-Querstrich über dem Körper),
gepunktet = BERÜHRUNG (Vorbeischreiben — nahe und entgegengesetzt, aber mit langem Weg
dazwischen). „Feinschliff (nur Anzeige)“ glättet die KANDIDATEN-Bahnen für das Auge
((1,&nbsp;2,&nbsp;1)/4, Endpunkte fix — die Darstellungsstufe des v0.6-Verdikts: das Lineal sieht den
Pixel-Zickzack nie, also gehört Glättung zum Konsumenten und nie in den gemessenen Kandidaten);
die Hand-Referenz und alle Zahlen bleiben roh. So prüft das Auge den Zähler gegen die Tinte. Die ◇-Zeilen sind
das DUKTUS-SOLL: die Summe der isolierten Buchstaben (Maus darüber zeigt das Budget je Buchstabe)
und die ganze Komposition mit Verbindern — die Differenz der beiden ist der Beitrag der
Verbindungen (ein einlaufender Verbinder kann eine Schleife schließen, die der Buchstabe allein
nicht hat). Weicht die Hand von beiden ab, ist etwas falsch — im Template, in der Join-Grammatik
oder in der Nachfahrung.</div>
<div class="hint"><b>Was die Zahlenspalten bedeuten:</b>
<b>dtw_xh</b> = mittlerer Abstand der Bahn zur Hand-Nachfahrung nach bestmöglicher
Punkt-zu-Punkt-Zuordnung, in x-Höhen — die Kopfzahl, klein ist gut.
<b>aiou</b> = wie gut die Bahn die TINTE überdeckt (Pixel-Überlappung nach Aufdickung, groß ist
gut) — Warnung: sie misst nur, WO Tinte liegt, nicht WIE sie durchlaufen wird; die chaotische
Kontrolle schlägt hier sogar die Hand, deshalb ist aiou nie die Kopfzahl.
<b>cross m/s</b> = Schleifen-Kreuzungen: getroffen (m) / erfunden (s) gegenüber der Hand.
<b>retrace</b> = Bogen-Verhältnis doppelt beschriebener Tinte (1,0 = wie die Hand; darunter
verliert das Verfahren Deckstriche, darüber erfindet es welche).
Diese vier decken ABSTAND und TOPOLOGIE ab; der Bench misst mehr (Marken-Orte, Absetzer,
Chamfer in beide Richtungen) — und ehrlich benannt fehlt allen eine GLÄTTE-Spalte: die
Mikro-Wackler, die man einer Bahn beim Nachschreiben mit fester Stiftdicke ansieht, bestraft
heute keine dieser Zahlen.</div>
<div class="hint"><b>Residualprofil</b> (die Kurve unter der Tabelle): zieht die Hand-Nachfahrung
von jeder Methoden-Bahn ab — aber nicht Punkt n gegen Punkt n (bei gleicher Punktzahl wäre nach
der ersten Extraschleife alles Folgende verschoben und ein Phantomfehler), sondern entlang der
optimalen DTW-Zuordnung, mit der auch die Kopfzahl gemessen wird: beide Körper-Bahnen werden
bogenlängen-gleichmäßig abgetastet (0,02&nbsp;xh), und jedes Referenz-Sample trägt den mittleren
Abstand seiner zugeordneten Kandidaten-Punkte, in x-Höhen. Der Mittelwert über alle
Zuordnungspaare IST <b>dtw_xh</b> — das Profil zeigt, WO die Zahl herkommt: flach nahe 0 =
sauber, Berge = daneben. Gestrichelte Senkrechte = Absetzer der Hand; Marken (i-Punkte,
u-Bögen, Umlaute) bleiben wie in der Kopfzahl außen vor. Maus über dem Profil setzt eine orange
Sonde an die entsprechende Stelle der Hand-Bahn im Bild; die Legenden-Häkchen schalten die
Kurve mit der Bahn zusammen.</div>
<script>{js}</script>
</body>
</html>
"""


# ------------------------------------------------------------------------ CLI


def build_page(
    reference: Reference,
    ids: Sequence[str],
    candidates: list[tuple[str, dict[str, Candidate]]],
    reports: dict[str, dict[str, Any]],
    *,
    title: str,
    meta: str,
    soll: dict[str, tuple[SollRow, ...]] | None = None,
) -> tuple[str, list[str]]:
    """`(html, warnings)` — the page over the selected words."""
    colors = assign_colors([label for label, _ in candidates])
    explainer = method_explainer([label for label, _ in candidates], colors)
    sections: list[str] = []
    tabs: list[tuple[str, str]] = []
    warnings: list[str] = []
    for specimen_id in ids:
        entry = reference.entries[specimen_id]
        crop_path = entry.directory / CROP_FILE
        if not crop_path.exists():
            warnings.append(f"{specimen_id}: no {CROP_FILE} in {entry.directory} — word skipped")
            continue
        with Image.open(crop_path) as img:
            size = img.size
        crop_uri = "data:image/png;base64," + base64.b64encode(crop_path.read_bytes()).decode()

        ref_strokes, ref_structure = layer_paths(
            entry.frame, entry.row.strokes, entry.row.registration_px, entry.row.xh_px
        )
        layers = [
            Layer(
                label=REFERENCE_LABEL,
                color=COLOR_REFERENCE,
                kind="reference",
                strokes=ref_strokes,
                structure=ref_structure,
            )
        ]
        # The residual profile compares BODY sequences exactly as the headline
        # does: marks held out, per-stroke arc-length resampling at the ruler's
        # own step, concatenation in writing order.
        ref_bench = entry.frame.trace_to_bench(entry.row.strokes, entry.row.registration_px, entry.row.xh_px)
        ref_body_rs = resampled_strokes(classify_strokes(ref_bench)[0], RESAMPLE_STEP_UNITS)
        ref_seq = concat_body(ref_body_rs)
        arc_x, lifts = body_arc_positions(ref_body_rs)
        resid_lines: list[ResidualLine] = []
        for label, by_id in candidates:
            candidate = by_id.get(specimen_id)
            if candidate is None or not candidate.ok:
                layers.append(
                    Layer(
                        label=label,
                        color=colors[label],
                        kind="candidate",
                        strokes=[],
                        status=candidate.status if candidate else "skipped",
                        detail=candidate.detail if candidate else "no candidate for this word",
                    )
                )
                continue
            cand_strokes, cand_structure = layer_paths(
                entry.frame, candidate.strokes, candidate.registration_px, candidate.xh_px
            )
            layers.append(
                Layer(
                    label=label,
                    color=colors[label],
                    kind="candidate",
                    strokes=cand_strokes,
                    structure=cand_structure,
                    numbers=(reports.get(label) or {}).get(specimen_id),
                )
            )
            cand_bench = entry.frame.trace_to_bench(candidate.strokes, candidate.registration_px, candidate.xh_px)
            cand_seq = concat_body(resampled_strokes(classify_strokes(cand_bench)[0], RESAMPLE_STEP_UNITS))
            if len(ref_seq) and len(cand_seq):
                profile = np.column_stack([arc_x, residual_values(ref_seq, cand_seq)])
                resid_lines.append(ResidualLine(label=label, color=colors[label], points=decimate_peaks(profile)))
        resid = ""
        if resid_lines and len(arc_x):
            chart = residual_chart(resid_lines, lifts, float(arc_x[-1]))
            if chart:
                map_json = residual_map_json(arc_x, entry.frame.bench_to_crop_px(ref_seq))
                resid = (
                    f'<div class="resid">{chart}'
                    f'<script type="application/json" class="resid-map">{map_json}</script></div>'
                )
        sections.append(
            word_section(
                len(sections), entry, crop_uri, size, layers, soll=(soll or {}).get(specimen_id, ()), resid=resid
            )
        )
        # The tab label is the SPECIMEN id, not the word text: repeated words
        # ("und", "und-2", "und-3") would otherwise render three identical tabs
        # and make the arrow navigation ambiguous. For non-repeats id == word.
        tabs.append((specimen_id, specimen_id))
    return render_html(sections, tabs, title=title, meta=meta, explainer=explainer), warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.tracebench.view",
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--style", default="suetterlin")
    parser.add_argument("--set", dest="which", default="words", help="fixture set (words | pairs | a custom set name)")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES_DIR, help="fixture root")
    parser.add_argument("--split", default="dev", choices=("dev", "confirm", "all"))
    parser.add_argument("--words", help="comma-separated id/word list — overrides --split")
    parser.add_argument(
        "--candidate",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help="a candidate file (the file-provider contract, frame 'word_registration'); repeatable",
    )
    parser.add_argument(
        "--rows",
        action="append",
        default=[],
        metavar="LABEL=BENCHJSON",
        help="a tracebench --json report whose per-word numbers belong to LABEL; repeatable",
    )
    parser.add_argument("--title", default="", help="run label(s) and date — injected, never read from a clock")
    parser.add_argument("--out", type=Path, default=Path("temp/duell.html"), help="output HTML [temp/duell.html]")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = find_fixture_root(args.fixtures, args.style, args.which)
    try:
        reference = load_reference(root)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from None

    ids = select_ids(reference, args.split, args.words)
    if not ids:
        raise SystemExit(f"no words selected (split {args.split!r}, set {args.which!r}, words {args.words!r})")

    candidate_specs = parse_pairs(args.candidate, flag="--candidate")
    row_specs = parse_pairs(args.rows, flag="--rows")
    candidates = [(label, file_provider(path)(reference, ids)) for label, path in candidate_specs]
    reports = {label: load_report_rows(path) for label, path in row_specs}
    # The label ORDER is the argument order, never a set's iteration order — the
    # page has to come out byte-identical from identical inputs.
    labels = [label for label, _ in candidate_specs]
    for label in reports:
        if label not in labels:
            print(f"  --rows {label}: no candidate with that label — numbers ignored")

    meta = html.escape(
        f"{args.style} · Satz {args.which} · Split {args.split} · {len(ids)} Wörter · Wurzel {root.name} · "
        f"Verfahren: {', '.join([REFERENCE_LABEL, *labels])}" + (f" · {args.title}" if args.title else "")
    )
    soll, soll_warnings = ductus_soll(ids, which=args.which, style=args.style, fixtures_root=args.fixtures)
    page, warnings = build_page(reference, ids, candidates, reports, title=args.title, meta=meta, soll=soll)
    for line in [*soll_warnings, *warnings]:
        print(f"  {line}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8")
    print(f"wrote {args.out} — {len(ids) - len(warnings)} words, {len(candidate_specs) + 1} layers each")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
