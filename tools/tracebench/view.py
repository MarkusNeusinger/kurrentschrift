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

from core.geometry import detect_retrace_pairs, stroke_bounds
from tools.tracebench.candidates import STATUS_OK, Candidate, file_provider
from tools.tracebench.counters import (
    RESAMPLE_STEP_UNITS,
    RETRACE_MIN_PAIRS,
    RETRACE_PROX_UNITS,
    crossing_points,
    resampled_strokes,
)
from tools.tracebench.frames import BenchFrame, arc_length, classify_strokes, concat_strokes
from tools.tracebench.reference import DEFAULT_FIXTURES_DIR, Reference, ReferenceEntry, load_reference
from tools.tracebench.run import find_fixture_root
from tools.tracebench.sets import TRACEBENCH_DEV_IDS


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
# Everything else, handed out in order — deterministic, never random.
PALETTE = ("#8e24aa", "#ef6c00", "#6d4c41", "#c2185b", "#3949ab", "#00838f")

# Label fragments that pin a colour by MEANING rather than by call order, so the
# chain stays red and the follower blue however the CLI arguments are ordered.
CHAIN_MARKERS = ("chain", "kette")
FOLLOWER_MARKERS = ("follow", "folger")

REFERENCE_LABEL = "Hand (Referenz)"


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
    retraces: list[tuple[str, bool]]  # (pass path data in crop px, overlap across strokes)


def structure_marks(frame: BenchFrame, strokes_bench: list[np.ndarray]) -> StructureMarks:
    """Display-only detections, at the ruler's own frozen thresholds.

    The counters stay the ruler — this reads the same frozen primitives so a
    human can audit the detector against the ink (the owner's standing check:
    when the detected structures disagree with what the ductus prescribes,
    something is still wrong — possibly the detection itself). One distinction
    the ruler does not draw yet is made VISIBLE here: a retrace pass whose
    partner samples lie in ANOTHER pen stroke is an overlap (a mark riding the
    body, e.g. the t crossbar along the entry connector), not an out-and-back
    retrace of one stroke — the page dashes it so the two read differently.
    """
    pts, starts = concat_strokes(resampled_strokes(list(strokes_bench), RESAMPLE_STEP_UNITS))
    if len(pts) < 2:
        return StructureMarks(crossings=[], retraces=[])
    crossings = [(float(x), float(y)) for x, y in frame.bench_to_crop_px(crossing_points(list(strokes_bench)))]
    idx, partner = detect_retrace_pairs(pts[:, 0], pts[:, 1], starts, prox_px=RETRACE_PROX_UNITS)
    retraces: list[tuple[str, bool]] = []
    if len(idx):
        stroke_of = np.zeros(len(pts), dtype=int)
        for s, (lo, hi) in enumerate(stroke_bounds(len(pts), starts)):
            stroke_of[lo:hi] = s
        partner_of = dict(zip(idx.tolist(), partner.tolist(), strict=True))
        run: list[int] = []
        for i in [*np.sort(idx).tolist(), None]:
            contiguous = bool(run) and i is not None and i == run[-1] + 1 and stroke_of[i] == stroke_of[run[-1]]
            if contiguous:
                run.append(i)
                continue
            if len(run) >= RETRACE_MIN_PAIRS:
                seg = frame.bench_to_crop_px(pts[run[0] : run[-1] + 1])
                overlap = any(stroke_of[int(partner_of[k])] != stroke_of[k] for k in run)
                retraces.append((stroke_path_data(seg), overlap))
            run = [] if i is None else [i]
    return StructureMarks(crossings=crossings, retraces=retraces)


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
  section.word > h2 { font-size: 16px; margin: 0 0 8px; }
  g.structure circle.cross { fill: none; stroke-width: 1.4; }
  g.structure path.retrace { fill: none; stroke-width: 7; opacity: 0.22; }
  g.structure path.retrace.overlap { stroke-dasharray: 5 4; stroke-width: 4; opacity: 0.4; }
  body.nostructure g.structure { display: none; }
"""

# `__SPEED__`/`__PAUSE__` are substituted below. Written as a plain string (not
# an f-string) so the JS braces stay JS braces.
_JS = """
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
    [].slice.call(document.querySelectorAll('path.ink')).forEach(function (p) {
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
        // Constant pen speed: the arc decides the duration, the rate only scales it.
        var dur = Math.max(80, (len / xh) / SPEED_XH_PER_S * 1000) / rate;
        p.style.strokeDashoffset = '1';
        if (typeof p.animate === 'function') {
          running.push(p.animate(
            [{ strokeDashoffset: '1' }, { strokeDashoffset: '0' }],
            { duration: dur, delay: t, fill: 'forwards', easing: 'linear' }
          ));
        } else {
          p.style.strokeDashoffset = '0';
        }
        t += dur + PAUSE_MS / rate;  // the pen lift: a pause, never a bridge
      });
    });
  }
  function setVisible(label, visible) {
    [].slice.call(document.querySelectorAll('g.layer')).forEach(function (g) {
      if (g.getAttribute('data-label') === label) { g.style.display = visible ? '' : 'none'; }
    });
    [].slice.call(document.querySelectorAll('input.toggle')).forEach(function (c) {
      if (c.getAttribute('data-label') === label) { c.checked = visible; }
    });
  }
  document.addEventListener('change', function (ev) {
    var t = ev.target;
    if (!t) { return; }
    if (t.classList && t.classList.contains('toggle')) { setVisible(t.getAttribute('data-label'), t.checked); }
    if (t.id === 'speed') { rate = parseFloat(t.value) || 1; }
    if (t.id === 'structure') { document.body.classList.toggle('nostructure', !t.checked); }
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
        f'pathLength="1" stroke-dasharray="1" stroke-dashoffset="0" '
        f'stroke-width="{MARK_STROKE_WIDTH if s.mark else STROKE_WIDTH}" '
        f'vector-effect="non-scaling-stroke"></path>'
        for s in layer.strokes
    )
    structure = ""
    if layer.structure and (layer.structure.crossings or layer.structure.retraces):
        rings = "".join(
            f'<circle class="cross" cx="{x:.{COORD_DECIMALS}f}" cy="{y:.{COORD_DECIMALS}f}" '
            f'r="{CROSS_MARK_RADIUS_PX:g}" vector-effect="non-scaling-stroke"></circle>'
            for x, y in layer.structure.crossings
        )
        zones = "".join(
            f'<path class="retrace{" overlap" if overlap else ""}" d="{d}" vector-effect="non-scaling-stroke"></path>'
            for d, overlap in layer.structure.retraces
        )
        structure = f'<g class="structure">{zones}{rings}</g>'
    return (
        f'<g class="layer" id="{layer_id}" data-label="{html.escape(layer.label, quote=True)}" '
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
    # The reference is not a candidate and is never scored against itself here;
    # its row carries the stroke count (the pen-lift comparison) and dashes.
    cells = _numbers_cells(layer.numbers) if layer.kind == "candidate" else "<td>–</td>" * 4
    return (
        f'<tr class="layer-row"><td><span class="swatch" style="background:{layer.color}"></span> '
        f"{html.escape(layer.label)}{note}</td><td>{len(layer.strokes)}</td>{cells}</tr>"
    )


def word_section(index: int, entry: ReferenceEntry, crop_uri: str, size: tuple[int, int], layers: list[Layer]) -> str:
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
    rows = "".join(_numbers_row(layer) for layer in layers)
    return (
        f'<section class="word" data-id="{html.escape(entry.specimen_id, quote=True)}" '
        f'data-word="{html.escape(entry.word, quote=True)}" data-xh="{entry.frame.xh:.4f}" hidden>'
        f"<h2>„{html.escape(entry.word)}“ · {html.escape(entry.specimen_id)} · {html.escape(entry.kind)}</h2>"
        f'<div class="stage" style="width:{width * STAGE_ZOOM}px;height:{height * STAGE_ZOOM}px">'
        f'<img src="{crop_uri}" width="{width * STAGE_ZOOM}" height="{height * STAGE_ZOOM}" '
        f'alt="Ausschnitt „{html.escape(entry.word, quote=True)}“">'
        f'<svg viewBox="0 0 {width} {height}" width="{width * STAGE_ZOOM}" height="{height * STAGE_ZOOM}">'
        f"{svg_layers}</svg></div>"
        f'<div class="legend">{legend}</div>'
        f'<table class="numbers"><thead><tr><th>Verfahren</th><th>Striche</th><th>dtw_xh</th><th>aiou</th>'
        f"<th>cross m/s</th><th>retrace</th></tr></thead><tbody>{rows}</tbody></table>"
        f"</section>"
    )


def render_html(sections: list[str], tabs: list[tuple[str, str]], *, title: str, meta: str) -> str:
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
<div class="tabs">{tab_html}</div>
<div class="bar">
  <button id="prev" type="button">← zurück</button>
  <button id="next" type="button">weiter →</button>
  <button id="play" type="button">Schreiben abspielen</button>
  <button id="final" type="button">Fertige Bahn</button>
  <label for="speed">Tempo</label>
  <select id="speed">{speeds}</select>
  <label><input type="checkbox" id="structure" checked> Struktur</label>
</div>
{"".join(sections)}
<div class="hint">Die Seite öffnet mit der FERTIGEN Bahn; „Schreiben abspielen“ schreibt alle
eingeschalteten Verfahren gleichzeitig in Schreibreihenfolge — Strichdauer proportional zur Bogenlänge
(konstante Federgeschwindigkeit), jedes Absetzen eine echte Pause. Pfeiltasten ←/→ wechseln das Wort.
„Struktur“ zeigt je Ebene die DETEKTIERTEN Strukturen an den eingefrorenen Schwellen des Lineals:
Ringe = Schleifenkreuzungen, breite Bänder = Retrace-Zonen — gestrichelt, wenn die Zone eine
ÜBERLAGERUNG zweier Striche ist (z.&nbsp;B. der t-Querstrich über dem Körper) statt eines
Hin-und-zurück in einem Strich. So prüft das Auge den Detektor gegen die Tinte.</div>
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
) -> tuple[str, list[str]]:
    """`(html, warnings)` — the page over the selected words."""
    colors = assign_colors([label for label, _ in candidates])
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
        sections.append(word_section(len(sections), entry, crop_uri, size, layers))
        # The tab label is the SPECIMEN id, not the word text: repeated words
        # ("und", "und-2", "und-3") would otherwise render three identical tabs
        # and make the arrow navigation ambiguous. For non-repeats id == word.
        tabs.append((specimen_id, specimen_id))
    return render_html(sections, tabs, title=title, meta=meta), warnings


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
    page, warnings = build_page(reference, ids, candidates, reports, title=args.title, meta=meta)
    for line in warnings:
        print(f"  {line}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8")
    print(f"wrote {args.out} — {len(ids) - len(warnings)} words, {len(candidate_specs) + 1} layers each")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
