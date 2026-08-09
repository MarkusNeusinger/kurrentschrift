"""Build one round of the human fit-judgement instrument: payload, key, stamp.

    uv run python -m tools.humanbench.build --round 2 --n-label 150 --repeats 12
    uv run python -m tools.humanbench.build --round 3 --paired old.json new.json

The generalised form of the round-2 scratchpad builder. Two modes:

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
disk. Outputs land under `temp/` — a payload is occurrence geometry and stays
out of the repository (quellen-und-rechte.md §5).
"""

from __future__ import annotations

import argparse
import base64
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

from core.chart import load_chart_grayscale, load_word_samples
from core.word_metric import skeleton_for_sample


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = "data/sources/suetterlin-1922"
DEFAULT_OUT_ROOT = "temp/humanbench"
DEFAULT_API = "https://api.kurrentschrift.ink"

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
    """
    return [
        {
            "uid": entry["uid"],
            "glyph": entry["glyph"],
            "word": entry["word"],
            "slot": entry["slot"],
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


def provenance(args: argparse.Namespace, *, mode: str, seed: int, counts: dict, repeats: dict, api_used: bool) -> dict:
    """The stamp: what this payload is, and against which state of the code."""
    return {
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
            "only": str(args.only) if args.only else None,
            "api": args.api if api_used else None,
        },
        "counts": counts,
        "repeats": repeats,
    }


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
    parser.add_argument("--min-repeat-gap", type=int, default=40, help="minimum screens between the two showings [40]")
    parser.add_argument("--bands", type=int, default=5, help="severity bands the sequence is dealt from [5]")
    parser.add_argument("--seed", type=int, default=None, help=f"shuffle seed [{SEED_BASE} + round]")
    parser.add_argument("--zoom", type=int, default=4, help="pixel magnification of the crop [4]")
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
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    seed = args.seed if args.seed is not None else SEED_BASE + args.round
    rng = random.Random(seed)

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
