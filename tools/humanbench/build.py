"""Build one round of the human fit-judgement instrument: payload, key, stamp.

    uv run python -m tools.humanbench.build --round 2 --n-label 150 --repeats 12
    uv run python -m tools.humanbench.build --round 3 --paired old.json new.json
    uv run python -m tools.humanbench.build --round 4 --word-arms basis.json lf11.json

The generalised form of the round-2 scratchpad builder. Three modes:

* **single** (default) — one occurrence per screen; the judge names the defect.
  Writes `payload.json`, `key.json`, `vorkommen.json`, `reserve.json`,
  `provenance.json`. Of those, only `vorkommen.json` and `provenance.json` may
  be archived alongside the judgements — see `slim_key`.
* **paired** (`--paired OLD NEW`) — the SAME occurrence twice, one fit from each
  of two instance snapshots, side by side on ONE shared crop image. Which side
  carries which snapshot is drawn from the seed and written to the key only;
  the payload contains no marking of any kind, and the two panels differ in
  nothing but the drawn line. That is the point of the mode: a before/after the
  fix's own author cannot read the answer off.
* **word** (`--word-arms BASE CANDIDATE`) — the same WHOLE specimen word with
  two compositions drawn over it as INK, judged on the authenticity question
  („welche sieht echter geschrieben aus?", menschliche-bewertung.md §8). It is
  the only mode that can see the three defects every frozen ruler is blind to
  (the anchor-median zigzag of a Laufform row, the too-thin stroke, the kink at
  a connector's seam): the first two are invisible to a per-letter centerline
  screen, and the third sits behind the letter's own window.

The word mode composes NOTHING itself. Both arms arrive as files, exactly the
way the paired mode takes two instance snapshots — an instrument that computed
its own candidate could drift away from the ruler that has to confirm it later,
and the round would then compare two things nobody else can reproduce.
``tools/humanbench/wordarm.py`` is the reference producer; any arm (a candidate
Laufform card, a different nib, a connector trim) writes the same file:

    {"arm": "LF11", "style": "suetterlin", "set": "words",
     "source_id": "suetterlin-1922", "fixture_root": "suetterlin-1922",
     "words": {"<entry id>": {
         "registration": {"xh_px": 33.0, "tx": 12.0, "ty": -1.0},
         "strokes": [{"points": [[x, y], ...], "width": 0.14}],
         "fills":   [[[[x, y], ...], [[x, y], ...]]]}}}

Coordinates are the composer's own WORD FRAME (x to the right in x-heights,
y UP in x-heights from the baseline, i.e. ``composed["items"][*]["centerline"]``
and ``["rings"]``); ``width`` is a stroke width in x-heights. ``fills`` is one
entry per pen stroke and each entry is that stroke's RING LIST — the exterior
plus the counters it encloses, exactly as ``compose_word`` groups them, because
the grouping is the only thing that says which ring is a hole. The registration
maps that frame onto the fixture crop and is the arm's OWN — see
``word_cases`` for why, and for when to pin it instead.

Every safeguard below cost a round to learn and is kept here so the next round
does not have to rediscover it. The reason each exists sits next to it in the
code, because a safeguard without its failure is the first thing a later edit
removes as noise:

* proportional crop padding rather than a fixed pixel pad (`crop_window`),
* seeded shuffling WITHIN the severity bands, not just across them (`stratify`),
* a held-out reserve that is never labelled (`stratify`),
* blind repeats, drawn only from the first half and from frequent, unmemorable
  glyphs (`pick_repeats`),
* polylines split at every pen lift (`polyline_strokes`).

Payload contract (`PAYLOAD_FORMAT`), which is all the page may read:

    {"id": "S001", "w": 312, "h": 208, "img": "<base64 PNG>",
     "panels": [{"strokes": [[[x, y], …], …]}, …]}

One panel in the single mode, two in the paired one, in the order they are to
be shown. Everything that could identify a panel — glyph, word, snapshot,
severity — lives in `key.json` and never in the payload, so a page cannot leak
it even by accident.

Inputs. The occurrences come from stored fits: either from files
(`--instances`, or the two files of `--paired`) or, absent those, over the
deployed read API. Stroke starts come from the templates (`--starts` or the
admin-gated single-template read). Chart bytes are read from `--source` on
disk. The word mode reads neither: its specimen crops come from a frozen word
bench fixture root (`--fixtures`), so a word round is scored against exactly
the reference the automatic ruler uses. Outputs land under `temp/` — a payload
is occurrence geometry and stays out of the repository
(quellen-und-rechte.md §5).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import random
import subprocess
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

from core.chart import load_chart_grayscale, load_word_samples
from core.word_metric import skeleton_for_sample


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = "data/sources/suetterlin-1922"
DEFAULT_OUT_ROOT = "temp/humanbench"
DEFAULT_API = "https://api.kurrentschrift.ink"
# The word mode judges against the SAME frozen references the word bench scores
# against, so a human verdict and the ruler can never be about different pixels.
DEFAULT_FIXTURES = "tools/wordbench/fixtures"
DEFAULT_STYLE = "suetterlin"

# Bumped whenever the payload shape changes, so a page built for an older round
# fails loudly instead of drawing nothing. v2 replaced the single `strokes`
# array with `panels[]`, which is what makes the paired mode possible at all.
PAYLOAD_FORMAT = 2

# Seeds are per round by default: two rounds drawing the same permutation would
# silently correlate their fatigue and order effects. The resolved integer is
# recorded in the stamp, so any round can be rebuilt exactly.
SEED_BASE = 20260000

# A repeat exists to measure the judge against themselves, so it must be judged
# again rather than remembered. Three rules follow, all in `pick_repeats`:
REPEAT_MIN_GLYPH_COUNT = 6  # only glyphs seen often enough that one is not distinctive
REPEAT_JITTER = 25  # random extra distance, so repeats are not a rhythm to spot
# Glyph keys never repeated: the capital S is this project's known-bad letter
# and instantly recognisable — repeating it measures memory, not judgement.
DEFAULT_REPEAT_EXCLUDE = ("S",)

# Display ids. `S…` for a first showing, `R…` for a blind repeat — kept from
# round 2 so the returned result lines parse the same way across rounds. The
# NUMBER is the screen's position in this round, not its severity (round 2
# numbered by peak rank, which made the two look like the same thing); what
# joins a judgement to an occurrence across rounds is `key.identity`.
ITEM_PREFIX = "S"
REPEAT_PREFIX = "R"

# Snapshot labels of the paired mode. They appear in the KEY, never in the payload.
SIDE_OLD = "old"
SIDE_NEW = "new"

# Arm labels of the word mode — same rule: key and stamp only.
SIDE_BASE = "base"
SIDE_CANDIDATE = "candidate"

# The word mode's own defaults. A word set is ~63 entries against the letter
# mode's 245, so the repeat distance cannot be the letter mode's 40 and stay
# placeable: `pick_word_repeats` may only draw from screens that still have
# `min_gap + REPEAT_JITTER` room after them, and 40 + 25 leaves none. That is
# affordable HERE and nowhere else, because a word repeat is shown MIRRORED
# (menschliche-bewertung.md §8) — the mirroring, not the distance, is what
# forces the verdict to be made again; the distance only keeps the two showings
# from sitting next to each other.
WORD_MIN_REPEAT_GAP = 15
# A word crop is a whole word rather than one letter, so it carries four times
# the pixels; at the letter mode's 4× a 75-screen round would not fit under the
# Artifact ceiling (page.py::SIZE_WARN_MB). At 2× the x-height of the Sütterlin
# plate is still ~66 screen pixels.
WORD_ZOOM = 2
NO_STRATUM = "-"
# 2 groups a pen stroke's silhouette rings into ONE shape. Format 1 listed them
# flat, which lost the only information that says which ring is a hole, and the
# page painted every loop counter solid.
WORD_ARM_FORMAT = 2

# One screen, and the key fields a mode adds to a repeat of it.
Renderer = Callable[[str, "Occurrence", dict], dict]
Patch = Callable[[dict], dict]


# --------------------------------------------------------------- occurrences


@dataclass
class Occurrence:
    """One stored fit of one letter in one specimen word, in crop pixels."""

    glyph_key: str
    specimen_id: str
    slot: int
    sample: dict
    xh: float
    points: np.ndarray  # the fitted centerline, crop-local pixels
    stroke_starts: list[int]
    peak: float  # largest distance from the specimen's own ink skeleton, x-heights
    peak_at: int  # anchor index of that distance
    n_anchors: int
    rank: int = -1  # position in the peak-sorted order, filled by `rank_rows`
    uid: str = ""  # display id, filled when the round is assembled

    @property
    def identity(self) -> tuple[str, str, int]:
        """What makes two rounds joinable: the occurrence, not its display id."""
        return (self.glyph_key, self.specimen_id, self.slot)


class Specimens:
    """Per-sample crop pixels and distance-to-ink field, computed once each."""

    def __init__(self, source_dir: Path) -> None:
        self.source_dir = source_dir
        self.chart_path = str(source_dir / "chart.jpg")
        self._pages: dict[str, np.ndarray] = {}
        self._crops: dict[str, np.ndarray] = {}
        self._edt: dict[str, np.ndarray] = {}

    def crop(self, sample: dict) -> np.ndarray:
        sid = str(sample["id"])
        if sid not in self._crops:
            page = self._pages.setdefault(
                str(sample["page"]), load_chart_grayscale(str(self.source_dir / str(sample["page"])))
            )
            self._crops[sid] = page[sample["y0"] : sample["y1"], sample["x0"] : sample["x1"]].copy()
        return self._crops[sid]

    def ink_distance(self, sample: dict) -> np.ndarray:
        """Distance from every crop pixel to the nearest skeleton pixel.

        The skeleton is `core.word_metric.skeleton_for_sample` — the SAME
        reference the word bench scores against, imported rather than restated
        so a human round and the automatic ruler can never drift apart in what
        they call "the ink".
        """
        sid = str(sample["id"])
        if sid not in self._edt:
            self._edt[sid] = distance_transform_edt(~skeleton_for_sample(self.chart_path, sample))
        return self._edt[sid]


def occurrence_rows(
    instances: list[dict],
    samples: dict[str, dict],
    starts: dict[str, list[int]],
    specimens: Specimens,
    dropped: Counter | None = None,
) -> list[Occurrence]:
    """Stored instance rows → occurrences placed in their specimen's crop.

    `dropped` collects, by reason, the rows that do not become occurrences —
    the round's population is a FILTERED set, and a filter nobody counted looks
    exactly like an empty one. The stamp carries the tally so a later round can
    tell „the harvest changed" from „the filter did".
    """
    rows: list[Occurrence] = []
    for row in instances:
        measurements = row.get("measurements") or {}
        sample = samples.get(measurements.get("specimen_id"))
        # Variant rows are derived forms, not observations: an occurrence of a
        # running form would be judged against ink it was never fitted to.
        if not row.get("anchors"):
            _count(dropped, "no_anchors")
            continue
        if sample is None:
            _count(dropped, "specimen_not_measured")
            continue
        if int(row.get("variant", 0) or 0) != 0:
            _count(dropped, "derived_variant")
            continue
        anchors = np.asarray(row["anchors"], dtype=float)
        xh = float(measurements["xh_px"])
        # Anchors are stored in the glyph's own frame (x-height units, baseline
        # 0, left-aligned); the stored box puts them back into the crop.
        px = ((row["x0"] - sample["x0"]) - anchors[:, 0].min() * xh) + anchors[:, 0] * xh
        py = ((row["y1"] - sample["y0"]) + anchors[:, 1].min() * xh) - anchors[:, 1] * xh
        edt = specimens.ink_distance(sample)
        distance = (
            edt[
                np.clip(np.round(py).astype(int), 0, edt.shape[0] - 1),
                np.clip(np.round(px).astype(int), 0, edt.shape[1] - 1),
            ]
            / xh
        )
        rows.append(
            Occurrence(
                glyph_key=row["glyph_key"],
                specimen_id=str(measurements["specimen_id"]),
                slot=int(measurements.get("slot", -1)),
                sample=sample,
                xh=xh,
                points=np.column_stack([px, py]),
                stroke_starts=list(starts.get(row["glyph_key"], [0])),
                peak=float(distance.max()),
                peak_at=int(np.argmax(distance)),
                n_anchors=len(anchors),
            )
        )
    return rows


def _count(dropped: Counter | None, reason: str) -> None:
    if dropped is not None:
        dropped[reason] += 1


def rank_rows(rows: list[Occurrence]) -> list[Occurrence]:
    """Sort worst-first and stamp the rank the severity bands are cut from."""
    rows.sort(key=lambda r: -r.peak)
    for i, row in enumerate(rows):
        row.rank = i
    return rows


# ------------------------------------------------------------------ rendering


def crop_window(points: np.ndarray, xh: float, crop_shape: tuple[int, ...], pad_xh: float) -> tuple[int, int, int, int]:
    """Bounds around the drawn line, padded PROPORTIONALLY to the x-height.

    A fixed pixel pad hides the evidence exactly where it matters: the worst
    deviations of round 2 reached a third of an x-height, so with a flat 8 px
    the ink the line SHOULD have been on could sit outside the crop — the judge
    would then be asked what the fit missed while being shown neither the miss
    nor the target.
    """
    pad = max(6, int(round(pad_xh * xh)))
    x0 = max(0, int(points[:, 0].min()) - pad)
    x1 = min(crop_shape[1], int(points[:, 0].max()) + pad)
    y0 = max(0, int(points[:, 1].min()) - pad)
    y1 = min(crop_shape[0], int(points[:, 1].max()) + pad)
    return x0, y0, x1, y1


def polyline_strokes(
    points: np.ndarray, stroke_starts: list[int], window: tuple[int, int, int, int], zoom: int
) -> list[list[list[float]]]:
    """Screen-space polylines, SPLIT at every pen lift.

    A lift is not a line. Bridged, it draws a stroke the writer never made, and
    the judge would correctly report a defect the fit does not have — the
    instrument would be manufacturing its own findings.
    """
    x0, y0 = window[0], window[1]
    local = (points - np.array([x0, y0])) * zoom
    bounds = sorted({0, *(int(s) for s in stroke_starts if 0 < int(s) < len(local)), len(local)})
    return [
        [[round(float(p[0]), 1), round(float(p[1]), 1)] for p in local[start:end]]
        for start, end in zip(bounds[:-1], bounds[1:], strict=True)
        if end - start >= 2
    ]


def context_strokes(context: list[np.ndarray], window: tuple[int, int, int, int], zoom: int) -> list[list[list[float]]]:
    """The surrounding PEN PATH in screen space — the connectors, drawn faintly.

    Round 1 shipped without this and it cost the round's headline finding. The
    harvest fits a whole word as ONE chain (`_harvest_case_chain`), so the
    connectors belong to the chain's connector segments and are absent from a
    letter's own anchors. Showing the letter alone made every joined letter end
    in mid-air, and the judge — correctly reporting what was on screen — filed
    23 % of the round as „the entry stroke is missing". Re-measured afterwards:
    the ink beyond the letter sits 0.25 xh from the drawn line but 0.02 xh from
    the stored pen path, so the fit had it all along.

    The control that settles it: the GOOD screens carry the same undrawn
    connector ink, and MORE of it (0.50 xh vs 0.25). The judgements were not
    wrong about the pixels — the drawing was incomplete, and the defect they
    were pointing at turned out to sit at the SEAM between letter and
    connector, which cannot be seen at all when the connector is missing.
    """
    x0, y0 = window[0], window[1]
    out = []
    for path in context:
        local = (path - np.array([x0, y0])) * zoom
        if len(local) >= 2:
            out.append([[round(float(p[0]), 1), round(float(p[1]), 1)] for p in local])
    return out


def render_item(
    uid: str,
    panels: list[Occurrence],
    specimens: Specimens,
    *,
    zoom: int,
    pad_xh: float,
    context: dict[str, list[np.ndarray]] | None = None,
) -> dict:
    """One screen: the crop image ONCE, plus one polyline set per panel.

    The shared image is what keeps the paired mode blind. Cropping each panel
    to its own line would give the two sides different pixel dimensions and a
    different view of the neighbouring ink — a tell that has nothing to do with
    the fits, and one the judge would learn within a dozen screens.

    `context` carries the specimen's stored pen path per specimen id. It is
    shared by both panels on purpose: it is the same measured word either way,
    so drawing it once cannot leak which panel is which.
    """
    sample = panels[0].sample
    crop = specimens.crop(sample)
    xh = max(p.xh for p in panels)
    window = crop_window(np.vstack([p.points for p in panels]), xh, crop.shape, pad_xh)
    x0, y0, x1, y1 = window
    width, height = (x1 - x0) * zoom, (y1 - y0) * zoom

    sub = (np.clip(crop[y0:y1, x0:x1], 0, 1) * 255).astype(np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(sub, "L").resize((width, height), Image.LANCZOS).save(buffer, format="PNG", optimize=True)
    item = {
        "id": uid,
        "w": width,
        "h": height,
        "img": base64.b64encode(buffer.getvalue()).decode(),
        "panels": [{"strokes": polyline_strokes(p.points, p.stroke_starts, window, zoom)} for p in panels],
    }
    paths = (context or {}).get(panels[0].specimen_id)
    if paths:
        item["context"] = context_strokes(paths, window, zoom)
    return item


# ---------------------------------------------------------------- stratifying


def stratify(rows: list[Occurrence], bands: int, n_label: int, rng: random.Random) -> tuple[list, list, int]:
    """Deal peak-sorted rows across severity bands, shuffled WITHIN each band.

    Two safeguards in one step, and the second is why the first alone failed.
    Dealing round-robin across the bands makes any PREFIX of the sequence span
    the whole severity range — necessary, because a judge who stops early must
    still leave a representative sample, and a detector scored only on defects
    cannot be told from one that calls everything a defect. But within a band
    the order stayed peak-descending, so a 150-item prefix reached ranks 0–215
    of 245 and the cleanest cases — where the false positives live — were
    unreachable. The within-band shuffle is seeded, so the round stays exactly
    reproducible from the stamp.

    The tail beyond `n_label` is the RESERVE: never labelled, band-balanced by
    construction, and therefore a usable held-out set. Without it, a detector
    built to see what this round found would be tuned and confirmed on the same
    labels.
    """
    size = (len(rows) + bands - 1) // bands
    banded = [rows[i * size : (i + 1) * size] for i in range(bands)]
    for band in banded:
        rng.shuffle(band)
    dealt: list[Occurrence] = []
    for i in range(size):
        for band in banded:
            if i < len(band):
                dealt.append(band[i])
    return dealt[:n_label], dealt[n_label:], size


def pick_repeats(
    label: list[Occurrence],
    *,
    band_size: int,
    bands: int,
    n_repeats: int,
    min_gap: int,
    exclude: tuple[str, ...],
    rng: random.Random,
) -> list[Occurrence]:
    """Choose the blind repeats — the round's own reliability measurement.

    Without them no per-category number can be told from label noise: if the
    judge agrees with themselves on a category only 6 times out of 12, a
    PERFECT detector for it tops out near that, and "our features are blind to
    this defect" becomes unfalsifiable.

    Three constraints, each so the repeat is judged again rather than recalled:
    only from glyphs seen often enough that no single one is memorable, never
    from `exclude` (see DEFAULT_REPEAT_EXCLUDE), and only from far enough up the
    sequence that `min_gap` plus the jitter still fits after it — a repeat that
    lands seven screens later measures memory rather than judgement.
    """
    counts = Counter(row.glyph_key for row in label)
    common = {glyph for glyph, count in counts.items() if count >= REPEAT_MIN_GLYPH_COUNT}
    early = {row.uid for row in label[: max(0, len(label) - min_gap - REPEAT_JITTER)]}
    pool = [r for r in label if r.glyph_key in common and r.glyph_key not in exclude and r.uid in early]
    rng.shuffle(pool)

    by_band: dict[int, list[Occurrence]] = {}
    for row in pool:
        by_band.setdefault(min(row.rank // band_size, bands - 1), []).append(row)

    picks: list[Occurrence] = []
    while len(picks) < n_repeats:
        added = False
        for band in range(bands):
            if len(picks) < n_repeats and by_band.get(band):
                picks.append(by_band[band].pop())
                added = True
        if not added:  # the pool is exhausted — fewer repeats, reported, never silently
            break
    return picks


def insert_repeats(
    items: list[dict],
    key: list[dict],
    picks: list[Occurrence],
    render: Renderer,
    *,
    min_gap: int,
    rng: random.Random,
    patch: Patch | None = None,
) -> list[int]:
    """Splice each repeat in at least `min_gap` screens after its first showing.

    The distance is jittered so the repeats are not a rhythm a judge can start
    anticipating. `patch` lets a mode change what the second showing is (the
    paired round mirrors it); whatever it returns goes into the key AND is
    handed to the renderer, so the screen and its record cannot disagree.

    Returns the realised gaps: a repeat that landed too close measures
    short-term memory and has to be visible as such, not averaged into a
    reliability figure. Measured on the FINISHED sequence, not at insertion
    time — a later repeat spliced in between the two showings pushes them
    further apart, so the insertion-time distance is not the distance the judge
    walks, and the reported number has to be the one that was actually walked.
    """
    inserted: list[str] = []
    for n, row in enumerate(picks):
        uid = f"{REPEAT_PREFIX}{n + 1:02d}"
        first = next(i for i, entry in enumerate(key) if entry["uid"] == row.uid)
        extra = patch(key[first]) if patch else {}
        at = min(len(items), first + min_gap + rng.randrange(0, REPEAT_JITTER + 1))
        items.insert(at, render(uid, row, extra))
        key.insert(at, {**key[first], "uid": uid, "repeat_of": row.uid, **extra})
        inserted.append(uid)
    position = {entry["uid"]: i for i, entry in enumerate(key)}
    return [position[uid] - position[row.uid] for uid, row in zip(inserted, picks, strict=True)]


# ------------------------------------------------------------------- the modes


def build_single(
    rows: list[Occurrence],
    specimens: Specimens,
    args: argparse.Namespace,
    rng: random.Random,
    context: dict[str, list[np.ndarray]] | None = None,
) -> tuple[list[dict], list[dict], list[dict], dict]:
    """The round-2 design: one occurrence per screen, judged into categories."""
    label, reserve, band_size = stratify(rows, args.bands, args.n_label, rng)
    for i, row in enumerate(label):
        row.uid = f"{ITEM_PREFIX}{i + 1:03d}"

    def render(uid: str, row: Occurrence, _extra: dict | None = None) -> dict:
        return render_item(uid, [row], specimens, zoom=args.zoom, pad_xh=args.pad_xh, context=context)

    items = [render(row.uid, row) for row in label]
    key = [_key_entry(row) for row in label]
    picks = pick_repeats(
        label,
        band_size=band_size,
        bands=args.bands,
        n_repeats=args.repeats,
        min_gap=args.min_repeat_gap,
        exclude=tuple(args.repeat_exclude),
        rng=rng,
    )
    gaps = insert_repeats(items, key, picks, render, min_gap=args.min_repeat_gap, rng=rng)
    reserve_rows = [_key_entry(row, display=False) for row in reserve]
    return items, key, reserve_rows, _repeat_report(picks, gaps)


def build_paired(
    pairs: list[tuple[Occurrence, Occurrence]],
    specimens: Specimens,
    args: argparse.Namespace,
    rng: random.Random,
    context: dict[str, list[np.ndarray]] | None = None,
) -> tuple[list[dict], list[dict], list[dict], dict]:
    """The before/after round: the same occurrence twice, blind.

    Banding runs on the OLD fit's peak, so a band means exactly what it meant in
    the previous round and the two are comparable. The side each snapshot lands
    on is drawn per screen from the seed: a judge who quietly prefers the left
    panel then spreads that bias evenly over both snapshots instead of handing
    it to one of them.
    """
    old_rows = [old for old, _ in pairs]
    by_identity = {old.identity: new for old, new in pairs}
    # Re-stamp the rank over the MATCHED rows before banding. `stratify` cuts
    # its bands by position in this list, while `pick_repeats` maps a row to a
    # band by `rank // band_size`; left at the full snapshot's rank, every
    # occurrence the new snapshot lost would shift its neighbours into a band
    # the bands were never cut at, and the repeats would pile into the last one.
    # The peak ORDER is untouched, so a band still means what it meant before.
    for i, row in enumerate(old_rows):
        row.rank = i
    label, reserve, band_size = stratify(old_rows, args.bands, args.n_label, rng)
    for i, row in enumerate(label):
        row.uid = f"{ITEM_PREFIX}{i + 1:03d}"

    # Drawn once per screen, up front, so the order does not depend on the
    # sequence the items happen to be rendered in.
    order = {row.uid: ([SIDE_OLD, SIDE_NEW] if rng.random() < 0.5 else [SIDE_NEW, SIDE_OLD]) for row in label}

    def render(uid: str, row: Occurrence, extra: dict | None = None) -> dict:
        sides = (extra or {}).get("order") or order[row.uid]
        sided = {SIDE_OLD: row, SIDE_NEW: by_identity[row.identity]}
        return render_item(
            uid, [sided[side] for side in sides], specimens, zoom=args.zoom, pad_xh=args.pad_xh, context=context
        )

    items = [render(row.uid, row) for row in label]
    key = [_paired_key_entry(row, by_identity[row.identity], order[row.uid]) for row in label]

    picks = pick_repeats(
        label,
        band_size=band_size,
        bands=args.bands,
        n_repeats=args.repeats,
        min_gap=args.min_repeat_gap,
        exclude=tuple(args.repeat_exclude),
        rng=rng,
    )

    # A repeat is shown MIRRORED. The identical screen can be answered from "I
    # picked left last time"; mirrored, the verdict has to be made again about
    # the ink, and a systematic side preference then shows up as disagreement
    # instead of hiding inside the agreement rate.
    def mirror(entry: dict) -> dict:
        return {"order": list(reversed(entry["order"])), "mirrored": True}

    gaps = insert_repeats(items, key, picks, render, min_gap=args.min_repeat_gap, rng=rng, patch=mirror)
    reserve_rows = [_key_entry(row, display=False) for row in reserve]
    return items, key, reserve_rows, _repeat_report(picks, gaps)


def _key_entry(row: Occurrence, *, display: bool = True) -> dict:
    entry = {
        "glyph": row.glyph_key,
        "word": row.specimen_id,
        "slot": row.slot,
        "peak": round(row.peak, 4),
        "at": row.peak_at,
        "n": row.n_anchors,
        "rank": row.rank,
    }
    if display:
        # `uid` is this round's screen; `identity` is the occurrence itself and
        # is what joins one round to the next — display ids are not stable
        # across rounds and must never be used for that.
        return {"uid": row.uid, "identity": list(row.identity), "repeat_of": None, **entry}
    return {"identity": list(row.identity), **entry}


def _paired_key_entry(old: Occurrence, new: Occurrence, order: list[str]) -> dict:
    return {
        "uid": old.uid,
        "identity": list(old.identity),
        "repeat_of": None,
        "order": order,  # panels[0], panels[1] — the ONLY record of which is which
        "mirrored": False,
        "glyph": old.glyph_key,
        "word": old.specimen_id,
        "slot": old.slot,
        "peak_old": round(old.peak, 4),
        "peak_new": round(new.peak, 4),
        "at_old": old.peak_at,
        "at_new": new.peak_at,
        "n_old": old.n_anchors,
        "n_new": new.n_anchors,
        "rank": old.rank,
    }


def slim_key(key: list[dict]) -> list[dict]:
    """The committable half of the key: what a uid MEANS, and nothing measured.

    A result line is `S026:AW#81,76`. Without a key it is a string nothing can
    read back, and the hours the round cost would be archived in an unreadable
    form. Which letter of which word of a public-domain plate a screen showed is
    not learned geometry — severity, rank and every per-occurrence number are,
    and they stay in `key.json` (quellen-und-rechte.md §5).

    `slot` is in here on purpose: it is the third part of the identity that
    joins one round to the next, and without it two occurrences of the same
    letter in the same word — round 1 had three such pairs — cannot be told
    apart when the judgements are carried forward.

    Written by the builder rather than hand-derived per round, so the archived
    key is a COPY of the key that was judged against instead of a second,
    slightly different artefact assembled months later.

    A word round has no glyph and no slot: its identity is the fixture entry,
    and what a uid means is that entry plus the word it spells. The declared
    suspicion class travels with it, because a per-class reading of the verdict
    is part of the pre-registered plan and would otherwise need the full key.
    """
    return [
        {
            "uid": entry["uid"],
            **(
                {"entry": entry["entry"], "text": entry["text"], "stratum": entry["stratum"]}
                if "entry" in entry
                else {"glyph": entry["glyph"], "word": entry["word"], "slot": entry["slot"]}
            ),
            "repeat_of": entry["repeat_of"],
        }
        for entry in key
    ]


def identities_from(entries: list[dict]) -> set[tuple[str, str, int]]:
    """Occurrence identities named by a key or reserve file, for ``--only``.

    Accepts both shapes the builder writes: an explicit `identity` triple, or
    the flat `glyph`/`word`/`slot` fields of the slim key.
    """
    wanted: set[tuple[str, str, int]] = set()
    for entry in entries:
        triple = entry.get("identity") or [entry.get("glyph"), entry.get("word"), entry.get("slot", -1)]
        if triple[0] is None or triple[1] is None:
            continue
        wanted.add((str(triple[0]), str(triple[1]), int(triple[2])))
    return wanted


def _repeat_report(picks: list[Occurrence], gaps: list[int]) -> dict:
    return {
        "n_repeats": len(picks),
        "gap_min": min(gaps) if gaps else None,
        "gap_max": max(gaps) if gaps else None,
        "glyphs": sorted({row.glyph_key for row in picks}),
    }


# ------------------------------------------------------------------ the word mode


@dataclass(frozen=True)
class ArmStroke:
    """One drawn stroke of an arm, in the composer's word frame."""

    points: np.ndarray
    width: float  # stroke width in x-heights; 0 draws as the page's hairline


@dataclass(frozen=True)
class ArmWord:
    """One arm's composition of one specimen word, plus where it sits."""

    xh: float  # x-height in crop pixels
    tx: float
    ty: float
    strokes: tuple[ArmStroke, ...]
    # One entry per pen stroke: its silhouette as an exterior ring plus the
    # counters it encloses, GROUPED. The grouping is what makes a hole a hole
    # (drawn evenodd); flattened, every loop interior fills in solid.
    fills: tuple[tuple[np.ndarray, ...], ...]


@dataclass(frozen=True)
class Arm:
    """One side of a word round: a named composition over a fixture set."""

    name: str
    path: Path
    digest: str
    words: dict[str, ArmWord]
    meta: dict


@dataclass
class WordCase:
    """One specimen word with both arms drawn into its own crop."""

    entry_id: str
    text: str
    crop: np.ndarray  # the FROZEN fixture crop, 8-bit grayscale
    baseline_row: float
    xh: float  # the specimen's measured lineature, crop pixels
    arms: dict[str, ArmWord]
    peak: float  # how far the two arms part, in x-heights — the severity key
    stratum: str = NO_STRATUM
    rank: int = -1
    uid: str = ""

    @property
    def identity(self) -> tuple[str]:
        """What joins one word round to the next: the fixture entry id."""
        return (self.entry_id,)


def load_arm(path: Path) -> Arm:
    """Read one arm file (see the module docstring for the contract).

    Validated here rather than at draw time: a malformed arm is a round that
    cannot be built, and the alternative is a page that silently draws half a
    word. The file's SHA-256 goes into the stamp — an arm is a candidate
    somebody produced, and a round is only reproducible if it says which bytes
    it drew.
    """
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"{path}: not readable as JSON ({exc})") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("words"), dict):
        raise SystemExit(f"{path}: an arm file needs a 'words' object keyed by fixture entry id")
    words: dict[str, ArmWord] = {}
    for entry_id, drawing in payload["words"].items():
        words[str(entry_id)] = _arm_word(drawing, f"{path}:{entry_id}")
    if not words:
        raise SystemExit(f"{path}: the arm draws no word")
    meta = {k: v for k, v in payload.items() if k != "words"}
    return Arm(
        name=str(payload.get("arm") or path.stem),
        path=path,
        digest=hashlib.sha256(raw).hexdigest()[:16],
        words=words,
        meta=meta,
    )


def _arm_word(drawing: Any, where: str) -> ArmWord:
    if not isinstance(drawing, dict):
        raise SystemExit(f"{where}: each word must be an object")
    registration = drawing.get("registration") or {}
    try:
        xh = float(registration["xh_px"])
        tx = float(registration.get("tx", 0.0))
        ty = float(registration.get("ty", 0.0))
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f"{where}: registration needs a numeric xh_px ({exc})") from exc
    strokes = tuple(_arm_stroke(s, where) for s in drawing.get("strokes") or [])
    fills = tuple(shape for shape in (_arm_shape(raw, where) for raw in drawing.get("fills") or []) if shape)
    if not strokes and not fills:
        raise SystemExit(f"{where}: nothing drawable — an empty panel is a broken screen, not a round")
    return ArmWord(xh=xh, tx=tx, ty=ty, strokes=strokes, fills=fills)


def _arm_shape(raw: Any, where: str) -> tuple[np.ndarray, ...]:
    """One pen stroke's silhouette: its exterior ring plus its counters.

    A flat ring (format 1, ``[[x, y], …]``) is REFUSED rather than accepted as
    a one-ring shape. It parses perfectly and draws a filled blob where the
    writing has a loop, so the failure would be silent exactly where it costs a
    judging session — better to name it and have the arm re-produced.
    """
    rings = [np.asarray(ring, dtype=float) for ring in raw or []]
    # ndim 1 = a list of POINTS where a list of rings belongs (a flat ring),
    # ndim 0 = a bare coordinate (a single point handed in as a shape).
    if rings and all(ring.ndim <= 1 for ring in rings):
        raise SystemExit(
            f"{where}: 'fills' looks like format {WORD_ARM_FORMAT - 1} — a flat ring list. Its loop counters "
            f"would be drawn filled; re-produce the arm with tools.humanbench.wordarm."
        )
    return tuple(ring for ring in rings if ring.ndim == 2 and ring.shape[0] >= 3 and ring.shape[1] >= 2)


def _arm_stroke(raw: Any, where: str) -> ArmStroke:
    points = raw.get("points") if isinstance(raw, dict) else raw
    width = float(raw.get("width", 0.0)) if isinstance(raw, dict) else 0.0
    array = np.asarray(points, dtype=float)
    if array.ndim != 2 or array.shape[0] < 2 or array.shape[1] < 2:
        raise SystemExit(f"{where}: a stroke needs at least two [x, y] points")
    return ArmStroke(points=array[:, :2], width=width)


def to_crop(points: np.ndarray, arm: ArmWord, baseline_row: float) -> np.ndarray:
    """Word frame → crop pixels: ``px = x·xh + tx``, ``py = baseline_row + ty − y·xh``.

    The same mapping the word bench draws its overlays with
    (``tools/wordbench/run.py::_overlay``). Restating it across a module
    boundary is unavoidable; getting it wrong is not silent, because the
    composition then misses the specimen by whole x-heights instead of the
    fraction it lands within when the frame is right.
    """
    return np.column_stack([points[:, 0] * arm.xh + arm.tx, baseline_row + arm.ty - points[:, 1] * arm.xh])


def arm_paths_px(arm: ArmWord, baseline_row: float) -> list[np.ndarray]:
    """Every drawn path of one arm, in crop pixels — strokes and fills alike."""
    return [to_crop(s.points, arm, baseline_row) for s in arm.strokes] + [
        to_crop(ring, arm, baseline_row) for shape in arm.fills for ring in shape
    ]


def arm_gap(left: list[np.ndarray], right: list[np.ndarray], xh: float) -> float:
    """How far the two arms part on this word, in x-heights (symmetric, worst point).

    The word mode's severity key, and the analogue of the letter mode's
    „largest distance from the ink": there the bands are cut by how bad a fit
    is, here by how much the candidate MOVED — because a screen on which the
    two arms are identical is exactly where a silent side preference shows up,
    and §3.1's prefix rule needs those screens reachable from the start.
    """
    a, b = np.vstack(left), np.vstack(right)
    tree_a, tree_b = cKDTree(a), cKDTree(b)
    return float(max(tree_b.query(a)[0].max(), tree_a.query(b)[0].max()) / xh)


def load_fixture_words(root: Path) -> list[dict]:
    """The scorable entries of a frozen word bench fixture root, in export order."""
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"{root}: no manifest.json — point --fixtures at a word bench fixture root")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = []
    for entry in manifest.get("words") or []:
        entry_id = str(entry.get("id") or entry["word"])
        if entry.get("scorable", not entry.get("missing_at_export")):
            entries.append({**entry, "id": entry_id})
    return entries


def word_cases(
    root: Path,
    base: Arm,
    candidate: Arm,
    *,
    strata: dict[str, str] | None = None,
    only: set[str] | None = None,
    dropped: Counter | None = None,
) -> list[WordCase]:
    """Join both arms onto the frozen fixture words they were composed from.

    A word only ONE arm draws is discarded and counted, for the reason §8 gives
    for the paired mode: a change that quietly stops producing a composition is
    a result, and it must not vanish into a shorter round that still looks
    complete.

    Each arm is drawn at its OWN registration, the one its producer measured.
    That is right for the authenticity question — a translation is not what is
    being judged — but it is also the one place where blindness can leak: an
    arm that sits systematically lower is readable as a group even though the
    seed randomises the sides. A producer whose mechanism does not move the
    placement therefore pins both arms to one registration
    (``wordarm.py --registration-from``), and the stamp records whether it did.
    """
    cases: list[WordCase] = []
    for entry in load_fixture_words(root):
        entry_id = entry["id"]
        if only is not None and entry_id not in only:
            _count(dropped, "not_in_entries")
            continue
        left, right = base.words.get(entry_id), candidate.words.get(entry_id)
        if left is None or right is None:
            # Counted apart, because they mean different things: a word only
            # the base draws is a composition the candidate LOST, one neither
            # draws was never in the fixture set's reach at all.
            _count(
                dropped,
                "neither_arm"
                if left is None and right is None
                else ("only_base" if right is None else "only_candidate"),
            )
            continue
        word_dir = root / entry_id
        meta = json.loads((word_dir / "word.json").read_text(encoding="utf-8"))
        crop = np.asarray(Image.open(word_dir / "crop.png").convert("L"))
        baseline_row = float(meta["baseline_y"] - meta["rect"][1])
        xh = float(meta["baseline_y"] - meta["midband_y"])
        cases.append(
            WordCase(
                entry_id=entry_id,
                text=str(meta.get("word") or entry.get("word") or entry_id),
                crop=crop,
                baseline_row=baseline_row,
                xh=xh,
                arms={SIDE_BASE: left, SIDE_CANDIDATE: right},
                peak=arm_gap(arm_paths_px(left, baseline_row), arm_paths_px(right, baseline_row), xh),
                stratum=(strata or {}).get(entry_id, NO_STRATUM),
            )
        )
    return cases


def screen_path(points: np.ndarray, window: tuple[int, int, int, int], zoom: int) -> list[list[float]]:
    """Crop pixels → the panel's own pixel frame, at display precision."""
    local = (points - np.array([window[0], window[1]])) * zoom
    return [[round(float(p[0]), 1), round(float(p[1]), 1)] for p in local]


def render_word_item(
    uid: str, case: WordCase, sides: list[str], *, zoom: int, pad_xh: float
) -> tuple[dict, tuple[int, int, int, int]]:
    """One word screen: the specimen crop ONCE, plus one inked panel per arm.

    Both panels share the image AND the window — the window is cut around the
    union of both arms, never around each arm's own extent. Two windows would
    give the sides different pixel dimensions and a different view of the
    neighbouring ink, which is the tell §8 rules out.

    Unlike the letter modes this draws the INK, not a centerline: filled
    silhouette rings for the letter bodies, capsules of their own width for the
    generated connectors. That is the whole reason the mode exists — a stroke
    that is a quarter too thin is invisible on a hairline, and the authenticity
    question is about how the writing looks, not where its middle runs.
    """
    drawn = [case.arms[side] for side in sides]
    everything = np.vstack([path for arm in drawn for path in arm_paths_px(arm, case.baseline_row)])
    window = crop_window(everything, case.xh, case.crop.shape, pad_xh)
    x0, y0, x1, y1 = window
    width, height = (x1 - x0) * zoom, (y1 - y0) * zoom

    buffer = io.BytesIO()
    Image.fromarray(case.crop[y0:y1, x0:x1], "L").resize((width, height), Image.LANCZOS).save(
        buffer, format="PNG", optimize=True
    )
    item = {
        "id": uid,
        "w": width,
        "h": height,
        "img": base64.b64encode(buffer.getvalue()).decode(),
        "panels": [_word_panel(arm, case, window, zoom) for arm in drawn],
    }
    return item, window


def _word_panel(arm: ArmWord, case: WordCase, window: tuple[int, int, int, int], zoom: int) -> dict:
    panel: dict[str, list] = {"strokes": [], "widths": [], "fills": []}
    for stroke in arm.strokes:
        path = screen_path(to_crop(stroke.points, arm, case.baseline_row), window, zoom)
        panel["strokes"].append(path)
        # A width of 0 means „the producer had none" and falls back to the
        # page's hairline; anything else is the composed stroke width, carried
        # to the screen in panel pixels so a nib change is visible as one.
        panel["widths"].append(round(stroke.width * arm.xh * zoom, 1))
    for shape in arm.fills:
        # Grouped, so the page can draw the shape as ONE evenodd path and its
        # counters stay paper — see `_arm_shape`.
        panel["fills"].append([screen_path(to_crop(ring, arm, case.baseline_row), window, zoom) for ring in shape])
    return {key: value for key, value in panel.items() if value}


def clipped_words(cases: list[WordCase], pad_xh: float) -> list[str]:
    """Words whose composition runs outside its own crop, and is therefore cut.

    §3.4's rule with a word-sized failure: the crop is the frozen fixture rect,
    so nothing can be padded INTO existence beyond it. A composition that runs
    past the plate's own word box is shown truncated, and the judge would then
    be asked about writing they cannot see — reported by name rather than
    quietly drawn.
    """
    cut = []
    for case in cases:
        points = np.vstack([p for arm in case.arms.values() for p in arm_paths_px(arm, case.baseline_row)])
        pad = max(6.0, pad_xh * case.xh)
        height, width = case.crop.shape[:2]
        if (
            points[:, 0].min() < -pad
            or points[:, 1].min() < -pad
            or points[:, 0].max() > width + pad
            or points[:, 1].max() > height + pad
        ):
            cut.append(case.entry_id)
    return cut


def pick_word_repeats(
    label: list[WordCase], *, n_repeats: int, min_gap: int, exclude: tuple[str, ...], rng: random.Random
) -> list[WordCase]:
    """Choose the blind repeats of a word round — dealt round-robin over STRATA.

    This is the construction lesson §3.2 wrote down after round 01 and then
    failed to apply twice: repeats drawn by frequency measure the reliability
    of whatever happens to be common, and the categories the round is actually
    about end up with one positive pair or none. A word round cannot draw by
    frequency at all (every word appears once), so the pool is dealt over the
    suspected-defect classes the round declared — and where none were declared,
    over the severity bands, which is what `stratum` falls back to.

    What the repeats measure here is NOT a category's reliability but the
    judge's side preference (§8): a mirrored second showing of the same word
    answered the same way names the same ARM, answered by position names the
    same SIDE. Spreading them over the classes only makes sure that preference
    is measured across the round rather than inside one class of words.
    """
    early = {case.uid for case in label[: max(0, len(label) - min_gap - REPEAT_JITTER)]}
    pool = [case for case in label if case.uid in early and case.entry_id not in exclude]
    rng.shuffle(pool)
    by_stratum: dict[str, list[WordCase]] = {}
    for case in pool:
        by_stratum.setdefault(case.stratum, []).append(case)

    picks: list[WordCase] = []
    while len(picks) < n_repeats:
        added = False
        for stratum in sorted(by_stratum):
            if len(picks) < n_repeats and by_stratum[stratum]:
                picks.append(by_stratum[stratum].pop())
                added = True
        if not added:  # exhausted — fewer repeats, reported, never silently
            break
    return picks


def build_word(
    cases: list[WordCase], args: argparse.Namespace, rng: random.Random
) -> tuple[list[dict], list[dict], list[dict], dict]:
    """The authenticity round: one specimen word, two compositions, blind."""
    rank_rows(cases)
    label, reserve, band_size = stratify(cases, args.bands, args.n_label, rng)
    for i, case in enumerate(label):
        case.uid = f"{ITEM_PREFIX}{i + 1:03d}"
        if case.stratum == NO_STRATUM:
            # No declared classes: the severity bands stand in, so the repeats
            # still span the round instead of clustering where nothing moved.
            case.stratum = f"band-{min(case.rank // band_size, args.bands - 1)}"

    order = {
        case.uid: ([SIDE_BASE, SIDE_CANDIDATE] if rng.random() < 0.5 else [SIDE_CANDIDATE, SIDE_BASE]) for case in label
    }

    def render(uid: str, case: WordCase, extra: dict | None = None) -> dict:
        sides = (extra or {}).get("order") or order[case.uid]
        item, _window = render_word_item(uid, case, sides, zoom=args.zoom, pad_xh=args.pad_xh)
        return item

    items = [render(case.uid, case) for case in label]
    key = [_word_key_entry(case, order[case.uid]) for case in label]
    picks = pick_word_repeats(
        label, n_repeats=args.repeats, min_gap=args.min_repeat_gap, exclude=tuple(args.repeat_exclude), rng=rng
    )

    def mirror(entry: dict) -> dict:
        return {"order": list(reversed(entry["order"])), "mirrored": True}

    gaps = insert_repeats(items, key, picks, render, min_gap=args.min_repeat_gap, rng=rng, patch=mirror)
    reserve_rows = [_word_key_entry(case, None, display=False) for case in reserve]
    report = {
        "n_repeats": len(picks),
        "gap_min": min(gaps) if gaps else None,
        "gap_max": max(gaps) if gaps else None,
        "strata": sorted({case.stratum for case in picks}),
    }
    return items, key, reserve_rows, report


def _word_key_entry(case: WordCase, order: list[str] | None, *, display: bool = True) -> dict:
    entry = {
        "entry": case.entry_id,
        "text": case.text,
        "stratum": case.stratum,
        "arm_gap": round(case.peak, 4),
        "rank": case.rank,
    }
    if not display:
        return {"identity": list(case.identity), **entry}
    return {
        "uid": case.uid,
        "identity": list(case.identity),
        "repeat_of": None,
        "order": order,  # panels[0], panels[1] — the ONLY record of which is which
        "mirrored": False,
        **entry,
    }


# What an arm may declare about the reference it was composed against. All of
# it is optional — a third-party arm is allowed to carry nothing — but whatever
# IS there has to agree, on pain of aborting the build.
ARM_SCOPE = ("style", "source_id", "fixture_root")


def check_arm_scope(base: Arm, candidate: Arm, *, style: str, source_id: str) -> list[str]:
    """Refuse two arms that were not composed against the same reference.

    A word round's whole claim is that the two panels differ in the composition
    and in NOTHING else. Arms from two fixture roots — a different style, a
    different plate, or the same plate re-exported — carry different crops,
    different frozen slots and different registrations, and the round would
    still build: 63 screens, a clean verdict, and a comparison of two things
    that were never the same measurement. Silent is the dangerous part, so this
    aborts rather than warns.

    Only what an arm actually declares is checked, and the settings' export
    timestamp is checked too — a re-exported root is a re-baseline, and two
    arms across one of those are the same trap wearing the same name. An arm
    that declares nothing cannot be checked and is reported as such.
    """
    problems = []
    for name in ARM_SCOPE:  # the two arms against each other
        left, right = base.meta.get(name), candidate.meta.get(name)
        if left is not None and right is not None and str(left) != str(right):
            problems.append(f"{name}: base says {left!r}, candidate says {right!r}")
    for name, expected in (("style", style), ("source_id", source_id)):  # and against the round
        for arm in (base, candidate):
            value = arm.meta.get(name)
            if value is not None and str(value) != str(expected):
                problems.append(f"{name}: arm {arm.name!r} says {value!r}, the round builds {expected!r}")
    exports = [(arm.meta.get("settings") or {}).get("exported_at") for arm in (base, candidate)]
    if all(exports) and exports[0] != exports[1]:
        problems.append(
            f"fixture export: base {exports[0]!r} vs candidate {exports[1]!r} — "
            f"a re-exported root is a re-baseline, so the two arms are not one measurement"
        )
    return problems


# ----------------------------------------------------------------- the inputs


def fetch_instances(api: str, source_id: str) -> list[dict]:
    """Stored occurrences over the deployed read API (public, GET only)."""
    return _client(api).get(f"/sources/{source_id}/instances")


def fetch_word_traces(api: str, source_id: str) -> list[dict]:
    """Stored word traces — the pen path incl. connectors (public, GET only)."""
    return _client(api).get(f"/sources/{source_id}/word-instances")


def word_trace_context(traces: list[dict], samples: dict[str, dict]) -> dict[str, list[np.ndarray]]:
    """Stored word traces → crop-pixel polylines, per specimen id.

    The trace lives in the word's registration frame — baseline v = 0, midband
    v = 1, y UP — so it is mapped exactly the way the SPA maps it
    (`app/src/sections/admin/belege/registration.ts::traceToCrop`):
    ``px = u·xh + tx`` and ``py = (baseline_row + ty) − v·xh``. Restating the
    formula is unavoidable across the language boundary; getting it wrong is
    not silent, because the trace then misses the letters by whole x-heights
    instead of the ~0.01 xh it lands within when the frame is right.
    """
    out: dict[str, list[np.ndarray]] = {}
    for row in traces:
        specimen = row.get("specimen_id")
        measurements = row.get("measurements") or {}
        registration = measurements.get("registration_px") or {}
        sample = samples.get(specimen)
        if sample is None or not row.get("strokes"):
            continue
        xh = float(measurements.get("xh_px") or (sample["baseline_y"] - sample["midband_y"]))
        tx = float(registration.get("tx", 0.0))
        baseline_row = float(registration.get("baseline_row", sample["baseline_y"] - sample["y0"])) + float(
            registration.get("ty", 0.0)
        )
        paths = []
        for stroke in row["strokes"]:
            points = np.asarray(stroke, dtype=float)
            if points.ndim == 2 and points.shape[0] >= 2 and points.shape[1] >= 2:
                paths.append(np.column_stack([points[:, 0] * xh + tx, baseline_row - points[:, 1] * xh]))
        if paths:
            out[specimen] = paths
    return out


def fetch_stroke_starts(api: str, source_id: str, glyph_keys: list[str]) -> dict[str, list[int]]:
    """Pen-lift anchor indices per glyph, from the stored templates.

    Admin-gated: the single-template read is the open-core moat (the authored
    ductus). Only `trace_meta.stroke_starts` is kept here — the round needs to
    know where the pen left the paper, nothing else about the template.
    """
    client = _client(api)
    starts: dict[str, list[int]] = {}
    for key in sorted(set(glyph_keys)):
        # Glyph keys are path segments and are data, not code (`ae`, `sz`, `ch`,
        # and whatever a future script adds) — quoted, never interpolated raw.
        row = client.get(f"/sources/{source_id}/templates/{quote(key, safe='')}", admin=True, allow_404=True)
        if row:
            starts[key] = list((row.get("trace_meta") or {}).get("stroke_starts") or [0])
    return starts


def _client(api: str):  # noqa: ANN202 — the client type is an implementation detail
    """The word bench's read-only client: GETs only, no redirects, no writes.

    Imported here rather than at module import time so a run that reads its
    occurrences from files never pays for the API stack — and imported rather
    than restated so there is exactly one place where "this tool cannot write"
    is true.
    """
    from tools.wordbench.fetch_fixtures import ApiClient

    return ApiClient(api, token=os.environ.get("ADMIN_TOKEN"))


def load_instance_file(path: Path) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise SystemExit(f"{path}: expected a list of instance rows")
    return rows


def match_pairs(old: list[Occurrence], new: list[Occurrence]) -> tuple[list[tuple[Occurrence, Occurrence]], dict]:
    """Join two snapshots on the occurrence identity, not on row order.

    Occurrences present in only one snapshot are dropped and COUNTED: a change
    that quietly stops producing a fit is a result, and it must not disappear
    into a shorter round that still looks complete.
    """
    new_by_identity = {row.identity: row for row in new}
    old_by_identity = {row.identity: row for row in old}
    pairs = [(row, new_by_identity[row.identity]) for row in old if row.identity in new_by_identity]
    return pairs, {
        "matched": len(pairs),
        "only_old": sorted("/".join(map(str, i)) for i in old_by_identity.keys() - new_by_identity.keys()),
        "only_new": sorted("/".join(map(str, i)) for i in new_by_identity.keys() - old_by_identity.keys()),
    }


# -------------------------------------------------------------------- the stamp


def git_short_sha(repo_root: Path, *args: str) -> str:
    """Short HEAD SHA (or branch), empty when git cannot answer.

    Tolerant on purpose: a missing stamp field must never abort a round that is
    otherwise fine — but the field itself is not optional. Without it nobody can
    later say WHICH state of the fit a set of judgements applies to, and a
    second round then cannot be compared with the first, which is the entire
    reason this tool exists rather than a script per round.
    """
    try:
        done = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["git", *(args or ("rev-parse", "--short", "HEAD"))],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


def provenance(
    args: argparse.Namespace,
    *,
    mode: str,
    seed: int,
    counts: dict,
    repeats: dict,
    api_used: bool,
    arms: list[dict] | None = None,
) -> dict:
    """The stamp: what this payload is, and against which state of the code."""
    stamp = {
        "format": PAYLOAD_FORMAT,
        "round": args.round,
        "mode": mode,
        # Never a guessed date: either the caller states it or the clock is read
        # at build time.
        "built_at": args.stamp or datetime.now(UTC).isoformat(timespec="seconds"),
        "source": str(args.source),
        "source_id": args.source_id,
        "seed": seed,
        "bands": args.bands,
        "zoom": args.zoom,
        "pad_xh": args.pad_xh,
        "min_repeat_gap": args.min_repeat_gap,
        "repeat_exclude": list(args.repeat_exclude),
        # The two repeat rules that are module constants rather than flags. A
        # rebuild is only exact if they are the same, so they belong in the
        # stamp — an edit to either silently changes which screens repeat.
        "repeat_min_glyph_count": REPEAT_MIN_GLYPH_COUNT,
        "repeat_jitter": REPEAT_JITTER,
        "code_commit": git_short_sha(REPO_ROOT),
        "code_branch": git_short_sha(REPO_ROOT, "rev-parse", "--abbrev-ref", "HEAD"),
        # A commit only says which code built the round if the tree was clean.
        # False also when git cannot answer at all — same as an empty commit.
        "code_dirty": bool(git_short_sha(REPO_ROOT, "status", "--porcelain")),
        "inputs": {
            "instances": str(args.instances) if args.instances else None,
            "starts": str(args.starts) if args.starts else None,
            "word_instances": str(args.word_instances) if args.word_instances else None,
            "paired": [str(p) for p in args.paired] if args.paired else None,
            "word_arms": [str(p) for p in args.word_arms] if args.word_arms else None,
            "fixtures": str(args.fixtures) if args.word_arms else None,
            "strata": str(args.strata) if args.strata else None,
            "only": str(args.only) if args.only else None,
            "api": args.api if api_used else None,
        },
        "counts": counts,
        "repeats": repeats,
    }
    if arms is not None:
        # WHICH bytes were drawn on which side. An arm is a candidate somebody
        # produced outside this tool; without its digest a word round names a
        # file that may since have been rewritten, and „the candidate won" would
        # point at nothing.
        stamp["arms"] = arms
    return stamp


# --------------------------------------------------------------------- the run


@dataclass
class Round:
    """One built round, ready to be written."""

    items: list[dict] = field(default_factory=list)
    key: list[dict] = field(default_factory=list)
    reserve: list[dict] = field(default_factory=list)
    stamp: dict = field(default_factory=dict)


def write_round(out: Path, built: Round, *, force: bool) -> None:
    if out.exists() and any(out.iterdir()) and not force:
        raise SystemExit(f"{out} is not empty — a round is written once; pass --force to overwrite")
    out.mkdir(parents=True, exist_ok=True)
    # Compact payload, readable key: the payload is machine input for one HTML
    # page, the key and stamp are read by humans doing the evaluation.
    (out / "payload.json").write_text(json.dumps(built.items, separators=(",", ":")), encoding="utf-8")
    for name, rows in (
        ("key.json", built.key),
        ("vorkommen.json", slim_key(built.key)),  # the committable half — see `slim_key`
        ("reserve.json", built.reserve),
    ):
        (out / name).write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "provenance.json").write_text(
        json.dumps(built.stamp, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tools.humanbench.build",
        description="Build one blind round of the human fit-judgement instrument (payload + key + stamp).",
    )
    parser.add_argument("--round", type=int, required=True, help="round number; names the output directory")
    parser.add_argument(
        "--source", default=DEFAULT_SOURCE, help=f"source directory with the chart bytes [{DEFAULT_SOURCE}]"
    )
    parser.add_argument("--source-id", default=None, help="API source id [derived from --source]")
    parser.add_argument("--n-label", type=int, default=150, help="occurrences to be judged; the rest is reserved [150]")
    parser.add_argument("--repeats", type=int, default=12, help="blind repeats for test-retest reliability [12]")
    parser.add_argument(
        "--min-repeat-gap",
        type=int,
        default=None,
        help=f"minimum screens between the two showings [40, word mode {WORD_MIN_REPEAT_GAP}]",
    )
    parser.add_argument("--bands", type=int, default=5, help="severity bands the sequence is dealt from [5]")
    parser.add_argument("--seed", type=int, default=None, help=f"shuffle seed [{SEED_BASE} + round]")
    parser.add_argument(
        "--zoom", type=int, default=None, help=f"pixel magnification of the crop [4, word mode {WORD_ZOOM}]"
    )
    parser.add_argument("--pad-xh", type=float, default=0.4, help="crop padding in x-heights [0.4]")
    parser.add_argument(
        "--repeat-exclude",
        nargs="*",
        default=list(DEFAULT_REPEAT_EXCLUDE),
        help=f"glyph keys never repeated {list(DEFAULT_REPEAT_EXCLUDE)}",
    )
    parser.add_argument("--out", default=None, help=f"output directory [{DEFAULT_OUT_ROOT}/runde-<round>]")
    parser.add_argument("--force", action="store_true", help="overwrite an existing round directory")
    parser.add_argument(
        "--paired",
        nargs=2,
        metavar=("OLD", "NEW"),
        default=None,
        help="two instance snapshots — builds a blind before/after round instead of a category round",
    )
    parser.add_argument(
        "--word-arms",
        nargs=2,
        metavar=("BASE", "CANDIDATE"),
        default=None,
        help="two composed-word arm files — builds the WORD round on the authenticity question",
    )
    parser.add_argument(
        "--fixtures",
        default=DEFAULT_FIXTURES,
        help=f"word bench fixture root the specimen crops come from [{DEFAULT_FIXTURES}]",
    )
    parser.add_argument("--style", default=DEFAULT_STYLE, help=f"fixture style directory [{DEFAULT_STYLE}]")
    parser.add_argument(
        "--strata",
        default=None,
        help="entry id → suspected-defect class as JSON; the repeats are dealt over these classes "
        "[the severity bands, with a warning]",
    )
    parser.add_argument("--entries", default=None, help="comma-separated fixture entry ids the word round is cut to")
    parser.add_argument("--instances", default=None, help="instance rows as JSON [fetched from the API]")
    parser.add_argument("--starts", default=None, help="glyph_key → stroke starts as JSON [fetched from the API]")
    parser.add_argument(
        "--word-instances",
        default=None,
        help="stored word traces as JSON — the pen path drawn faintly behind each letter "
        "so a joined letter does not appear to stop short [fetched from the API]",
    )
    parser.add_argument(
        "--only",
        default=None,
        help="restrict to the occurrences a key or reserve file names — how the held-out reserve of an "
        "earlier round is judged as its own confirmation pass",
    )
    parser.add_argument(
        "--api",
        default=os.environ.get("API_BASE_URL") or DEFAULT_API,
        help=f"deployed read API, used for whatever is not supplied as a file [{DEFAULT_API}]",
    )
    parser.add_argument("--stamp", default=None, help="build timestamp [the system clock at build time]")
    args = parser.parse_args(argv)

    args.source = (REPO_ROOT / args.source).resolve() if not Path(args.source).is_absolute() else Path(args.source)
    args.source_id = args.source_id or args.source.name
    args.out = Path(args.out) if args.out else REPO_ROOT / DEFAULT_OUT_ROOT / f"runde-{args.round}"
    args.paired = [Path(p) for p in args.paired] if args.paired else None
    args.word_arms = [Path(p) for p in args.word_arms] if args.word_arms else None
    args.fixtures = Path(args.fixtures) if Path(args.fixtures).is_absolute() else REPO_ROOT / args.fixtures
    args.entries = {e.strip() for e in args.entries.split(",") if e.strip()} if args.entries else None
    # Two defaults follow the mode rather than the flag, because the word set is
    # a quarter the size of a letter round: at 40 screens' distance no repeat is
    # placeable at all, and at 4× a word round outgrows the Artifact ceiling.
    if args.min_repeat_gap is None:
        args.min_repeat_gap = WORD_MIN_REPEAT_GAP if args.word_arms else 40
    if args.zoom is None:
        args.zoom = WORD_ZOOM if args.word_arms else 4
    # `--repeat-exclude` names glyph keys in the letter modes and fixture entry
    # ids in the word one; the letter default („never repeat the capital S")
    # would be an entry id there and is dropped unless the caller asked for it.
    if args.word_arms and args.repeat_exclude == list(DEFAULT_REPEAT_EXCLUDE):
        args.repeat_exclude = []
    return args


def run_word_round(args: argparse.Namespace, seed: int, rng: random.Random) -> int:
    """The authenticity round: two composed arms over the frozen specimen words."""
    root = args.fixtures / args.style / args.source_id
    base, candidate = (load_arm(path) for path in args.word_arms)
    mismatched = check_arm_scope(base, candidate, style=args.style, source_id=args.source_id)
    if mismatched:
        raise SystemExit(
            "the two arms were not composed against the same reference — a round over them would compare two "
            "different measurements:\n  " + "\n  ".join(mismatched)
        )
    if not any(arm.meta.get(field) for arm in (base, candidate) for field in ARM_SCOPE):
        print("  WARNING: neither arm declares its style/source/fixture root — nothing to check them against")
    strata = json.loads(Path(args.strata).read_text(encoding="utf-8")) if args.strata else None
    if isinstance(strata, dict) and isinstance(strata.get("strata"), dict):
        strata = strata["strata"]

    dropped: Counter = Counter()
    cases = word_cases(root, base, candidate, strata=strata, only=args.entries, dropped=dropped)
    if not cases:
        raise SystemExit(f"{root}: the two arms share no scorable fixture word — nothing to compare")

    counts: dict[str, Any] = {
        "words": len(cases),
        "dropped": dict(sorted(dropped.items())),
        "fixture_entries": len(load_fixture_words(root)),
    }
    if strata:
        counts["strata_declared"] = len({case.stratum for case in cases if case.stratum != NO_STRATUM})

    items, key, reserve, repeats = build_word(cases, args, rng)
    counts.update({"screens": len(items), "labelled": len(items) - repeats["n_repeats"], "reserved": len(reserve)})
    arms = [
        {"side": side, "name": arm.name, "file": str(arm.path), "sha256_16": arm.digest, "meta": arm.meta}
        for side, arm in ((SIDE_BASE, base), (SIDE_CANDIDATE, candidate))
    ]
    stamp = provenance(args, mode="word", seed=seed, counts=counts, repeats=repeats, api_used=False, arms=arms)
    stamp["question"] = "authentic"  # §8: the question belongs in the record, not only in the plan
    stamp["fixture_root"] = str(root)
    write_round(args.out, Round(items, key, reserve, stamp), force=args.force)

    shown = [entry for entry in key if not entry["repeat_of"]]
    ranks = [entry["rank"] for entry in shown[:100]]
    print(f"round {args.round} · word · seed {seed} · {len(cases)} words · {base.name} vs {candidate.name}")
    print(f"  {counts['labelled']} to judge · {len(reserve)} reserved as held-out · {len(items)} screens")
    if counts["dropped"]:
        print(f"  not eligible: {counts['dropped']}")
    if ranks:
        print(f"  prefix check — first {len(ranks)} span ranks {min(ranks)}–{max(ranks)} of 0–{len(cases) - 1}")
    print(
        f"  {repeats['n_repeats']} repeats, gaps {repeats['gap_min']}–{repeats['gap_max']} positions, "
        f"strata {repeats['strata']}"
    )
    if not strata:
        print(
            "  WARNING: no --strata — the repeats are dealt over the SEVERITY bands, not over the suspected "
            "defect classes. The round then measures the side preference across the arm-gap range; a per-class "
            "reading of the verdict has no repeats under it (menschliche-bewertung.md §3.2)."
        )
    cut = clipped_words(cases, args.pad_xh)
    if cut:
        print(
            f"  WARNING: {len(cut)} word(s) compose past their own fixture crop and are shown TRUNCATED: "
            f"{', '.join(cut[:8])}"
        )
    if repeats["n_repeats"] < args.repeats:
        print(
            f"  WARNING: {repeats['n_repeats']} of {args.repeats} repeats placed — too few early screens for "
            f"--min-repeat-gap {args.min_repeat_gap} in {counts['labelled']} words"
        )
    print(f"  wrote {args.out} ({sum(len(i['img']) for i in items) / 1e6:.1f} MB of crops)")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    seed = args.seed if args.seed is not None else SEED_BASE + args.round
    rng = random.Random(seed)
    if args.word_arms:
        if args.paired or args.instances:
            raise SystemExit("--word-arms builds a word round; --paired/--instances belong to the letter modes")
        return run_word_round(args, seed, rng)

    specimens = Specimens(args.source)
    samples = {str(entry["id"]): entry for entry in load_word_samples(specimens.chart_path)}
    if not samples:
        raise SystemExit(f"{args.source}: no words.json specimens — nothing to judge fits against")

    if args.paired and args.instances:
        raise SystemExit("--paired brings its own two snapshots; --instances would be ignored")
    snapshots = args.paired or ([Path(args.instances)] if args.instances else [])
    raw = [load_instance_file(path) for path in snapshots] or [fetch_instances(args.api, args.source_id)]
    if args.starts:
        starts = json.loads(Path(args.starts).read_text(encoding="utf-8"))
    else:
        starts = fetch_stroke_starts(args.api, args.source_id, [r["glyph_key"] for rows in raw for r in rows])
    api_used = not snapshots or not args.starts or not args.word_instances
    # A glyph absent from `starts` is drawn as ONE bridged polyline — the §3.6
    # failure, where the page shows a stroke the writer never made and the judge
    # correctly reports a defect the fit does not have. It returns silently
    # because the template read is admin-gated: without ADMIN_TOKEN nothing
    # resolves and every multi-stroke glyph bridges its lifts. A key present
    # with `[0]` is a genuinely single-stroke glyph and not a problem.
    unlifted = sorted({str(row["glyph_key"]) for rows in raw for row in rows} - set(starts))

    # The pen path the letters were fitted inside. Without it a joined letter
    # ends in mid-air on screen and the round measures the drawing instead of
    # the fit — that is what cost round 1 its headline finding, see
    # `context_strokes`. Absent traces are a warning, never a silent omission.
    if args.word_instances:
        traces = json.loads(Path(args.word_instances).read_text(encoding="utf-8"))
    else:
        traces = fetch_word_traces(args.api, args.source_id)
    context = word_trace_context(traces, samples)
    # Counted per SPECIMEN, not as an all-or-nothing check: traces for some
    # words and none for others reproduces the round-1 defect on exactly those
    # screens, and a partial failure that only shows up as silence is the one
    # this rule exists to prevent.
    uncovered = sorted({str(row["measurements"]["specimen_id"]) for rows in raw for row in rows} - set(context))
    if uncovered:
        print(
            f"WARNING: no word trace for {len(uncovered)} specimen(s) — their letters are drawn WITHOUT "
            f"connectors (round-1 defect): {', '.join(uncovered[:12])}"
            + (f" … +{len(uncovered) - 12}" if len(uncovered) > 12 else "")
        )

    wanted = identities_from(json.loads(Path(args.only).read_text(encoding="utf-8"))) if args.only else None
    sets, dropped = [], Counter()
    for rows in raw:
        # Restricted BEFORE ranking, so the severity bands are cut over the
        # population that is actually judged — a reserve pass is its own round,
        # not a sample with holes in its ranks.
        occurrences = occurrence_rows(rows, samples, starts, specimens, dropped)
        if wanted is not None:
            kept = [row for row in occurrences if row.identity in wanted]
            dropped["not_in_only"] += len(occurrences) - len(kept)
            occurrences = kept
        sets.append(rank_rows(occurrences))
    if not sets[0]:
        raise SystemExit(f"no occurrence to judge{f' — --only {args.only} matched none' if wanted else ''}")
    # The population of a round is a FILTERED set; the filter is part of the
    # stamp, so „the harvest changed" stays distinguishable from „the filter did".
    counts: dict[str, Any] = {"occurrences": [len(rows) for rows in sets], "dropped": dict(sorted(dropped.items()))}
    counts["glyphs"] = len({row.glyph_key for row in sets[0]})
    counts["specimens"] = len({row.specimen_id for row in sets[0]})
    if wanted is not None:
        counts["only_named"] = len(wanted)

    if args.paired:
        pairs, report = match_pairs(sets[0], sets[1])
        counts.update(report)
        if not pairs:
            raise SystemExit("the two snapshots share no occurrence — nothing to compare")
        if report["only_old"] or report["only_new"]:
            print(f"unmatched: {len(report['only_old'])} only in OLD, {len(report['only_new'])} only in NEW")
        items, key, reserve, repeats = build_paired(pairs, specimens, args, rng, context)
        mode, banded = "paired", len(pairs)
    else:
        items, key, reserve, repeats = build_single(sets[0], specimens, args, rng, context)
        mode, banded = "single", len(sets[0])

    counts.update({"screens": len(items), "labelled": len(items) - repeats["n_repeats"], "reserved": len(reserve)})
    stamp = provenance(args, mode=mode, seed=seed, counts=counts, repeats=repeats, api_used=api_used)
    built = Round(items, key, reserve, stamp)
    write_round(args.out, built, force=args.force)

    shown = [entry for entry in key if not entry["repeat_of"]]
    ranks = [entry["rank"] for entry in shown[:100]]
    print(f"round {args.round} · {mode} · seed {seed} · {counts['occurrences']} occurrences")
    print(
        f"  {counts['labelled']} to judge · {len(reserve)} reserved as held-out · {len(items)} screens"
        f" · {counts['glyphs']} glyphs over {counts['specimens']} specimens"
    )
    if counts["dropped"]:
        print(f"  not eligible: {counts['dropped']}")
    if ranks:
        # The prefix check that caught the round-1 failure: if the opening
        # screens do not span the whole rank range, the sequence is not a
        # representative sample and the round measures the wrong population.
        # Graded against the POPULATION, never against the drawn sample's own
        # rank range — that range shrinks with the very tail the check is
        # supposed to catch, so a sample missing the cleanest cases would score
        # a full span against itself. The population is the one that was BANDED
        # (in the paired mode the matched rows, not the whole old snapshot).
        print(f"  prefix check — first {len(ranks)} span ranks {min(ranks)}–{max(ranks)} of 0–{banded - 1}")
    print(
        f"  {repeats['n_repeats']} repeats, gaps {repeats['gap_min']}–{repeats['gap_max']} positions, "
        f"glyphs {repeats['glyphs']}"
    )
    if unlifted:
        print(
            f"  WARNING: no stroke starts for {len(unlifted)} glyph key(s) — {unlifted[:8]}; their pen lifts are "
            f"drawn as ONE bridged line, which makes the page show strokes the writer never made "
            f"(ADMIN_TOKEN missing, or --starts incomplete)"
        )
    if repeats["n_repeats"] < args.repeats:
        # Said out loud, because a round that quietly placed no repeats reports
        # per-category numbers with no reliability bound to put next to them —
        # and that is how a label-noise artefact becomes a "finding".
        print(
            f"  WARNING: {repeats['n_repeats']} of {args.repeats} repeats placed — too few frequent, early "
            f"glyphs for --min-repeat-gap {args.min_repeat_gap} in {counts['labelled']} screens"
        )
    print(f"  wrote {args.out} ({sum(len(i['img']) for i in items) / 1e6:.1f} MB of crops)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
