"""The blind calibration pass that replaces the borrowed Tintentreue bounds.

    # build the pass (reads over the admin-gated API, writes nothing anywhere)
    ADMIN_TOKEN=… uv run python -m tools.eigenhand.tintentreue_calibration build \
        --hand mn-suetterlin --round 1

    # afterwards, the pre-registered evaluation of the pasted result text
    uv run python -m tools.eigenhand.tintentreue_calibration analyse \
        --round-dir temp/tintentreue-kalibrierung/r1 --result urteile.txt

Every bound in ``core.eigenhand.tintentreue`` ships labelled „vorläufig" and
BORROWED: two come off the 1922 plate at 30–35 px x-height, one off the dev-19
set of that same plate, one is a rule with no measurement behind it at all —
and the single measured value among them belongs to a known coverage failure.
A strip is scanned at 300 dpi and is another hand's writing, so not one of the
eight is measured on what it judges. This is the instrument that measures them,
ONCE per hand (author decision Q10 b, 2026-09-18): 30 word boxes judged blind,
the bounds set once, dated, frozen, never a slider.

THE METHOD IS THE DOCUMENT, NOT THIS FILE. What is asked, which categories
exist, how they map onto the three steps and in which order the evaluation runs
is `docs/reference/menschliche-bewertung.md` §8b, written BEFORE this module
because that file's own Nachzieh-Anlass says a round whose setup departs from
it is described there first. The round's pre-registration — the numbers below,
with their reasons and their kill criteria — is `docs/reference/messjournal.md`
§14 „Tintentreue-Kalibrierung `sep20`". A constant here that disagrees with
either is a bug in this file.

WHY A SIBLING RATHER THAN A MODE OF ``tools.humanbench.build``. Four
properties of that builder do not hold here, and each alone would be enough:
it cuts its crops out of a word-bench fixture root and refuses a directory
without a ``manifest.json``, while the strip pixels are in no fixture root at
all; its taxonomy has six fit categories against three traffic-light steps; its
object is a letter inside a plate word rather than a word box of the author's
own hand; and its page is published as an Artifact, which these crops may
never be. What the two rounds share is therefore exactly one thing, and it is
shared rather than copied: the PAGE (``tools.humanbench.page``, the fourth
category set ``STRIP_CATEGORIES``) with its casing, its per-judgement clock,
its resume key and its result format.

WHAT IT READS, AND THE ONE WAY IT MAY. Only the admin-gated API: the hand's
box states with their sensor readings (``GET /eigenhand/pfade/{hand}``, the
meta-only read — no path points on the wire), then, for the drawn boxes alone,
the stored Bahn (``…/pfade``) and the word crop the server cuts
(``…?box=<n>&lineatur=ohne``). A direct SQLAlchemy read would reach the SHARED
production database from a local machine, and the strips are the reserved
own-hand dataset — so there is no local-file path in here at all, not even a
convenient one.

WHAT IT WRITES: four files and a page, under ``temp/`` and gitignored. The
page carries the reserved pixels, so it is opened from that file and never
published, never committed, never sent (`quellen-und-rechte.md` §5). Nothing
goes into the database: this tool reads, the author judges, and the adoption
of the measured bounds is a separate, dated commit of his.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import random
import struct
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from core.config import REPO_ROOT
from core.eigenhand.tintentreue import (
    SENSOR_ABSETZER,
    SENSOR_AIOU,
    SENSOR_EXKURSION,
    SENSOR_SPRUENGE,
    SENSOR_UNBESUCHT,
    SENSOREN_MIT_SCHWELLE,
    STUFEN,
    Schwellen,
    schwellen_of,
)
from tools.eigenhand.apiclient import admin_token, api_base, request_bytes, request_json
from tools.eigenhand.store import check_hand_id
from tools.humanbench.analyse import RESULT_HEAD, RESULT_LINE, TALLY_LINE, ResultFormatError
from tools.humanbench.page import STRIP_CATEGORIES, STRIP_TAG, write_page


# ---------------------------------------------------------- the pre-registered
# Every number below is fixed by `messjournal.md` §14
# „Tintentreue-Kalibrierung `sep20`" and may not be tuned after the labels
# exist. They are constants and not flags for exactly that reason: a flag is an
# invitation to try the other value once the answer is visible.

PAYLOAD_FORMAT = 1
DEFAULT_OUT_ROOT = "temp/tintentreue-kalibrierung"
SEED_BASE = 20260920

# 30 boxes, author decision Q10 (b), verbatim.
N_LABEL = 30
# Eight blind repeats, of which at least six have to come back as complete
# pairs — the same floor the paired rounds carry (`analyse.MIN_PAIRED_REPEATS`)
# and for the same reason: below it the round measures nothing about itself.
N_REPEATS = 8
MIN_REPEATS = 6
# Far enough apart that the second showing is judged again rather than recalled,
# plus a random offset so the repeats are not a rhythm to anticipate. Smaller
# than humanbench's 15 because the whole pass is 38 screens rather than 250 —
# the gap is a share of the sequence, not an absolute memory span.
MIN_REPEAT_GAP = 8
REPEAT_JITTER = 4

# Reliability: exact step agreement over the repeat pairs, and the one kind of
# disagreement that is not noise but a broken instrument — the same box called
# „folgt" once and „folgt nicht" the other time.
RELIABLE_EXACT = 2 / 3
MAX_FAR_PAIRS = 1

# A step carrying fewer boxes than this bounds nothing; the sensors that would
# hang off it stay borrowed and are reported as borrowed.
MIN_PER_STEP = 5

# The cut: the green bound is the 90 % quantile of the readings over the boxes
# judged „folgt", the yellow one the same over „folgt" ∪ „folgt teils" — from
# BELOW (10 %) for a sensor where larger is better. Nearest-rank, so the bound
# is always a value the hand actually produced.
GREEN_QUANTILE = 0.90
# Rounded in the STRICTER direction: a false green is the only error class that
# creates work in the wrong place (gate (C) of „Tintentreue `sep20`").
ROUND_DIGITS = 2

# The Absetzer (`KEY_ABSETZER = "paper_lifts"`) is an integer rule rather than a
# quantile: its yellow bound drops from ±1 to 0 only if at least this many boxes
# are off by exactly one run and most of them are judged „folgt nicht".
PEN_LIFT_TIGHTEN_MIN = 5
# Jumps and hairpins carry no bound today. One is PROPOSED only on this many
# flagged boxes AND a clean separation — anything less would be the unanchored
# threshold the pre-registration exists to prevent.
JUMPS_MIN_POSITIVES = 5

# Gates (A), (B) and (C) of „Tintentreue `sep20`", restated as numbers so the
# report can name them without a lookup.
AGREEMENT_GATE = 0.70
AGREEMENT_KILL = 0.50
FALSE_GREEN_MAX = 0.10
# Gate (B): a graded sensor that names no box over the whole pass is a dead
# branch. Two of the four dead kills the round — the sensor set is then the
# thing to re-cut, and no bound is frozen on top of it.
DEAD_BRANCH_KILL = 2

# The verdict vocabulary comes from the instrument itself so parser and page
# cannot drift apart.
FOLLOWS = "F"  # „folgt" — the step the bounds are drawn around
PARTLY = "T"
FAILS = "N"
UNRATABLE = "X"  # the `K` of §2 one layer down: an exclusion, not a severity
UNSURE = "U"

SOLO_CODES: tuple[str, ...] = tuple(c.code for c in STRIP_CATEGORIES if c.kind == "solo")
# The three GRADED steps, in severity order — `UNRATABLE` is a solo on the page
# and a non-answer here, so it is named out rather than filtered by position.
STEP_CODES: tuple[str, ...] = tuple(code for code in SOLO_CODES if code != UNRATABLE)
DETAIL_CODES: tuple[str, ...] = tuple(c.code for c in STRIP_CATEGORIES if c.kind == "detail")
ALL_CODES: tuple[str, ...] = tuple(c.code for c in STRIP_CATEGORIES)
CODE_LABEL: dict[str, str] = {c.code: c.tally for c in STRIP_CATEGORIES}
TALLY_CODE: dict[str, str] = {c.tally: c.code for c in STRIP_CATEGORIES}

# Which human step means which of `core.eigenhand.tintentreue.STUFEN`. The
# mapping is the identity by construction (§8b: „sie ist nicht interpretativ"),
# and it is spelled out anyway — the day someone adds a fourth step, this is
# the line that has to refuse.
# Zipped STRICTLY rather than written out: the day a fourth step is added to
# either vocabulary, this line raises at import instead of silently pairing
# three of four.
STEP_OF_CODE: dict[str, str] = dict(zip(STEP_CODES, STUFEN, strict=True))

# Which defect names which sensor. AIoU deliberately has no mark: the area
# average sees „Tinte ohne Bahn" and „Bahn auf Papier" a second time and less
# sharply, so a question of its own would count one observation twice. Its
# bound therefore hangs on the STEP alone, which §8b names as the weakest
# derivation of the round.
SENSOR_OF_DETAIL: dict[str, str] = {
    "O": SENSOR_UNBESUCHT,
    "P": SENSOR_EXKURSION,
    "A": SENSOR_ABSETZER,
    "H": SENSOR_SPRUENGE,
}

# The sensors a cut is derived for, and in which direction each one is better.
# `SENSOR_ABSETZER` is absent: it is the integer rule above, not a quantile.
SMALLER_IS_BETTER = (SENSOR_UNBESUCHT, SENSOR_EXKURSION)
LARGER_IS_BETTER = (SENSOR_AIOU,)

# Which `Schwellen` field each derived bound belongs to, so the report can
# print a block that is pasted rather than transcribed.
BOUND_FIELDS: dict[str, tuple[str, str]] = {
    SENSOR_UNBESUCHT: ("unbesucht_gruen", "unbesucht_gelb"),
    SENSOR_EXKURSION: ("exkursion_gruen_xh", "exkursion_gelb_xh"),
    SENSOR_AIOU: ("aiou_gruen", "aiou_gelb"),
}


# --------------------------------------------------------------- what is drawn


@dataclass
class Box:
    """One word box of one Fassung, as the sampling reads it.

    Everything here except `uid` comes off the meta-only read, which is the
    whole point of sampling there: it answers „which boxes does this hand hold,
    in which state, with which readings" without a single path point or pixel
    on the wire.
    """

    strip: str
    fassung: str
    box_index: int
    word: str
    step: str
    sensor: str | None
    readings: dict[str, float | None]
    # How many joined body runs the script writes this word in. Read off the
    # box rather than recomputed: the API answers it so the editor's target and
    # the Absetzer sensor cannot disagree, and a third computation here would
    # be a third opinion about the same word.
    absetzer_soll: float | None = None
    uid: str = ""

    @property
    def identity(self) -> tuple[str, str, int]:
        """What names this box across rounds — never shown, only recorded."""
        return (self.strip, self.fassung, self.box_index)


def boxes_of_hand(base: str, token: str, hand: str) -> list[Box]:
    """Every MEASURED word box of one hand, off the meta-only read.

    Grey boxes and Skip-Einträge are dropped here rather than later: there is
    nothing to calibrate on a box whose sensors nobody computed, and leaving
    them in would let the stratification hand the judge screens whose answer
    cannot move a bound.
    """
    answer = request_json("GET", f"{base}/eigenhand/pfade/{quote(hand)}", token) or {}
    out: list[Box] = []
    for fassung in answer.get("fassungen", []):
        for box in fassung.get("kaesten", []):
            verdict = box.get("tintentreue") or {}
            if not verdict.get("gemessen"):
                continue
            readings = {
                str(sensor.get("name")): sensor.get("wert")
                for sensor in verdict.get("sensoren", [])
                if sensor.get("name")
            }
            out.append(
                Box(
                    strip=fassung["strip"],
                    fassung=fassung["fassung"],
                    box_index=int(box["box_index"]),
                    word=str(box.get("word") or ""),
                    step=str(verdict.get("stufe") or ""),
                    sensor=verdict.get("sensor"),
                    readings=readings,
                    absetzer_soll=box.get("absetzer_soll"),
                )
            )
    return out


def stratify(rows: list[Box], n_label: int, rng: random.Random) -> tuple[list[Box], list[Box]]:
    """Deal the boxes across the three PROVISIONAL steps, shuffled within each.

    Two reasons, and the second is the one that is specific to this round.
    Dealing round-robin makes every PREFIX of the sequence span the steps, so a
    judge who stops early still leaves a usable sample (`menschliche-bewertung`
    §3.1). And without it a pass over a hand in good shape would be almost all
    green boxes — while the bound being looked for lives exactly where the
    cases are thin. The price is stated rather than hidden: the prevalence of
    this round says nothing about the hand.

    Each round the deal takes is SHUFFLED before it is appended, and that is
    not cosmetic: dealt strictly in band order, the position of a screen would
    name the step the machine gave it — screen 1 green, screen 2 yellow, screen
    3 red, and round again — which is exactly the tell the judge must not have
    (§8b, „was er dabei NICHT sieht"). Shuffling inside the round keeps every
    prefix step-balanced to within one box and takes the pattern away.

    The tail beyond `n_label` is the reserve (§3.3): never judged, step-balanced
    by construction, and reachable again with `--only`.
    """
    banded = [[row for row in rows if row.step == step] for step in STUFEN]
    for band in banded:
        rng.shuffle(band)
    dealt: list[Box] = []
    for index in range(max((len(band) for band in banded), default=0)):
        group = [band[index] for band in banded if index < len(band)]
        rng.shuffle(group)
        dealt.extend(group)
    return dealt[:n_label], dealt[n_label:]


def pick_repeats(label: list[Box], n_repeats: int, min_gap: int, rng: random.Random) -> list[Box]:
    """Choose the blind repeats, dealt across the STEPS rather than by frequency.

    `humanbench` draws them by glyph frequency and band; neither applies here —
    every word appears once, and there is no known-broken letter to keep out.
    What does apply is the lesson under that rule (§3.2): a reliability figure
    that comes only from agreement about the green boxes says nothing about the
    bound. So the repeats are dealt across the three steps, and only from far
    enough up the sequence that the gap plus its jitter still fits behind them.
    """
    early = label[: max(0, len(label) - min_gap - REPEAT_JITTER)]
    banded = [[row for row in early if row.step == step] for step in STUFEN]
    for band in banded:
        rng.shuffle(band)
    picks: list[Box] = []
    while len(picks) < n_repeats:
        added = False
        for band in banded:
            if len(picks) < n_repeats and band:
                picks.append(band.pop())
                added = True
        if not added:  # the pool is exhausted — fewer repeats, said out loud, never silently
            break
    return picks


def insert_repeats(
    items: list[dict],
    key: list[dict],
    picks: list[Box],
    render: Callable[[str, Box], dict],
    *,
    min_gap: int,
    rng: random.Random,
) -> list[int]:
    """Splice each repeat in at least `min_gap` screens after its first showing.

    The realised gaps are returned and reported: a repeat that landed too close
    measures short-term memory, and that has to be visible rather than averaged
    into a reliability figure. Measured on the FINISHED sequence, because a
    later repeat spliced in between two showings pushes them apart — the
    distance at insertion time is not the one the judge walks.
    """
    inserted: list[str] = []
    for number, row in enumerate(picks):
        uid = f"R{number + 1:02d}"
        first = next(index for index, entry in enumerate(key) if entry["uid"] == row.uid)
        at = min(len(items), first + min_gap + rng.randrange(0, REPEAT_JITTER + 1))
        items.insert(at, render(uid, row))
        key.insert(at, {**key[first], "uid": uid, "repeat_of": row.uid})
        inserted.append(uid)
    position = {entry["uid"]: index for index, entry in enumerate(key)}
    return [position[uid] - position[row.uid] for uid, row in zip(inserted, picks, strict=True)]


# --------------------------------------------------------- reading the pixels


def png_size(raw: bytes) -> tuple[int, int]:
    """Width and height out of a PNG's IHDR — without an image library.

    The builder needs the served crop's dimensions to hold them against the box
    rectangle it drew the Bahn into (§8b, rule 2). Parsing 24 bytes is cheaper
    than importing the image stack for a number that is printed in the file's
    own header, and it keeps this module free of the heavy dependency the
    follower carries.
    """
    if len(raw) < 24 or raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
        raise SystemExit("the API did not answer with a PNG — refusing to judge an unknown image")
    width, height = struct.unpack(">II", raw[16:24])
    return int(width), int(height)


def fetch_paths(base: str, token: str, hand: str, strip: str, fassung: str) -> dict:
    """One Fassung's stored paths together with its box rectangles.

    Both in one read on purpose: the rectangle is what turns the path's STRIP
    frame into the crop's, and taking the two from different answers is the
    silent version of the defect §3.6a was written for — the Bahn would sit a
    few pixels off over someone else's ink and the judge would report a fault
    the follower never made.
    """
    url = f"{base}/eigenhand/strips/{quote(hand)}/{quote(strip)}/{quote(fassung)}/pfade"
    return request_json("GET", url, token) or {}


def fetch_crop(base: str, token: str, hand: str, strip: str, fassung: str, box_index: int) -> bytes:
    """The word crop as the SERVER cuts it — specks removed, rulings lifted.

    `lineatur=ohne` so a printed ruling is not read as ink, and the Fleckenmaske
    is the route's default. Neither is a view this module could reproduce, and
    both are what the follower read: the judge has to see the ink the Bahn was
    laid over, not a different rendering of it.
    """
    url = f"{base}/eigenhand/strips/{quote(hand)}/{quote(strip)}/{quote(fassung)}?box={box_index}&lineatur=ohne"
    raw = request_bytes("GET", url, token)
    if not raw:
        raise SystemExit(f"{strip}/{fassung} box {box_index}: the strip crop came back empty")
    return raw


def panel_strokes(entry: Mapping[str, Any], rect: Sequence[float]) -> list[list[list[float]]]:
    """The stored Bahn in the CROP's own pixels, one polyline per pen run.

    ``px = (u·xh_px + tx, baseline_row + ty − v·xh_px)`` is the stored frame
    (`core.eigenhand.pfad`), and it is the STRIP's; the crop's is that minus the
    box rectangle. Every run stays its own polyline — bridging them would draw
    a stroke the hand never made, and the „Absetzer falsch" mark would get its
    positives from the renderer (§3.6).
    """
    registration = entry.get("registration_px") or {}
    xh_px = float(entry["xh_px"])
    tx = float(registration["tx"])
    ty = float(registration.get("ty", 0.0))
    baseline_row = float(registration["baseline_row"])
    x0, y0 = float(rect[0]), float(rect[1])
    out: list[list[list[float]]] = []
    for stroke in entry.get("strokes") or []:
        points = [
            [round(point[0] * xh_px + tx - x0, 2), round(baseline_row + ty - point[1] * xh_px - y0, 2)]
            for point in stroke
        ]
        if len(points) >= 2:
            out.append(points)
    return out


@dataclass
class Drawing:
    """What one box contributes to the page: the crop and the Bahn over it."""

    width: int
    height: int
    png: bytes
    strokes: list[list[list[float]]]


def drawing_of(base: str, token: str, hand: str, box: Box, paths: Mapping[str, Any]) -> Drawing:
    """Resolve one box into its drawable form, or refuse with a reason.

    The dimension check is the rule of §8b: the crop and the rectangle must be
    the same arithmetic, and the two come from different routes. If they ever
    disagree, every Bahn on the page is offset by that difference — invisibly,
    because a slightly misplaced line looks exactly like a slightly wrong one.
    """
    entries = {entry.get("box_index"): entry for entry in (paths.get("pfade") or []) if isinstance(entry, dict)}
    entry = entries.get(box.box_index)
    if entry is None or not entry.get("strokes"):
        raise SystemExit(f"{box.strip}/{box.fassung} box {box.box_index}: measured, but no stored Bahn — stale read?")
    # `boxes[]` keys its rows `index` and `pfade[]` keys its rows `box_index`
    # — two names for the same address, one route (`api.schemas`:
    # `EigenhandStripBoxOut.index` against `EigenhandPfad.box_index`).
    frames = {frame.get("index"): frame for frame in (paths.get("boxes") or []) if isinstance(frame, dict)}
    frame = frames.get(box.box_index) or {}
    rect = frame.get("rect_px")
    if not rect or len(rect) < 4:
        raise SystemExit(
            f"{box.strip}/{box.fassung} box {box.box_index}: no box rectangle — its Bogen predates the cut "
            f"geometry, so the Bahn cannot be placed over a crop"
        )
    png = fetch_crop(base, token, hand, box.strip, box.fassung, box.box_index)
    width, height = png_size(png)
    expected = (int(rect[2]) - int(rect[0]), int(rect[3]) - int(rect[1]))
    if (width, height) != expected:
        raise SystemExit(
            f"{box.strip}/{box.fassung} box {box.box_index}: the served crop is {width}x{height} but its "
            f"rectangle says {expected[0]}x{expected[1]} — the Bahn would be drawn offset"
        )
    return Drawing(width=width, height=height, png=png, strokes=panel_strokes(entry, rect))


def item_of(uid: str, drawing: Drawing) -> dict:
    """One screen, stripped to what is drawn.

    Nothing about the box travels into the payload — not the strip, not the
    word, not a reading and above all not the step the traffic light would have
    given it. That lives in the key (`menschliche-bewertung.md` §3.8); a judge
    who opens the page source finds a crop and a polyline.
    """
    return {
        "id": uid,
        "w": drawing.width,
        "h": drawing.height,
        "img": base64.b64encode(drawing.png).decode("ascii"),
        "strokes": drawing.strokes,
    }


def reserve_entry(box: Box) -> dict:
    """One held-out box: enough to restrict a confirmation pass to it, no more.

    Written alongside the key so a later round can be limited to exactly these
    identities with `--only` instead of being drawn afresh — a second draw with
    a new seed mixes judged and held-out boxes, and the reserve is spent as a
    confirmation set the moment it does (`menschliche-bewertung.md` §3.3).
    """
    return {"strip": box.strip, "fassung": box.fassung, "box_index": box.box_index, "word": box.word, "stufe": box.step}


def key_entry(box: Box, uid: str) -> dict:
    """The record that maps a screen back to its box — and never leaves `temp/`."""
    return {
        "uid": uid,
        "strip": box.strip,
        "fassung": box.fassung,
        "box_index": box.box_index,
        "word": box.word,
        # The provisional answer, kept so the round can be held against it
        # (gates (A)–(C)) — and kept out of the payload for the same reason.
        "stufe": box.step,
        "sensor": box.sensor,
        "readings": box.readings,
        "absetzer_soll": box.absetzer_soll,
    }


# ------------------------------------------------------------- the provenance


def git_short_sha(*args: str) -> str:
    """Short HEAD SHA (or branch), empty where git cannot answer."""
    try:
        done = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["git", *(args or ("rev-parse", "--short", "HEAD"))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


def provenance(args: argparse.Namespace, *, seed: int, thresholds: Schwellen, counts: dict, repeats: dict) -> dict:
    """The stamp: which round this is, and under which numbers it was drawn.

    The bounds travel in it although they are in the code as well, and that is
    the field this stamp exists for: the round's stratification is a function
    of the PROVISIONAL numbers, and replacing them is its entire purpose. Once
    they are replaced, nothing else could reconstruct the draw.
    """
    return {
        "format": PAYLOAD_FORMAT,
        "round": args.round,
        "mode": "strip",
        "question": "tintentreue",
        "hand": args.hand,
        "built_at": args.stamp or datetime.now(UTC).isoformat(timespec="seconds"),
        "seed": seed,
        "n_label": args.n_label,
        "min_repeat_gap": args.min_repeat_gap,
        "repeat_jitter": REPEAT_JITTER,
        "schwellen": {"stand": thresholds.stand, "vorlaeufig": thresholds.vorlaeufig, **_bounds_dict(thresholds)},
        "code_commit": git_short_sha(),
        "code_branch": git_short_sha("rev-parse", "--abbrev-ref", "HEAD"),
        "code_dirty": bool(git_short_sha("status", "--porcelain")),
        "inputs": {"api": api_base(args.api), "only": str(args.only) if args.only else None},
        "counts": counts,
        "repeats": repeats,
    }


def _bounds_dict(thresholds: Schwellen) -> dict[str, float]:
    """The eight numbers, by field name."""
    return {
        "unbesucht_gruen": thresholds.unbesucht_gruen,
        "unbesucht_gelb": thresholds.unbesucht_gelb,
        "absetzer_gelb": thresholds.absetzer_gelb,
        "exkursion_gruen_xh": thresholds.exkursion_gruen_xh,
        "exkursion_gelb_xh": thresholds.exkursion_gelb_xh,
        "aiou_gruen": thresholds.aiou_gruen,
        "aiou_gelb": thresholds.aiou_gelb,
    }


def round_store(stamp: dict, items: list[dict]) -> str:
    """This round's own browser-storage namespace.

    Keyed on the round's identity AND on what is drawn, exactly as the
    humanbench page is: a rebuilt page whose drawing moved must start clean
    rather than replay old verdicts by index onto new screens.
    """
    identity = {k: v for k, v in stamp.items() if k not in ("built_at", "code_commit", "code_branch", "code_dirty")}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, default=str).encode())
    digest.update(json.dumps(items, sort_keys=True, separators=(",", ":"), default=str).encode())
    return f"tintentreue-r{stamp.get('round')}-{digest.hexdigest()[:10]}"


@dataclass
class Built:
    """One built round, ready to be written."""

    items: list[dict] = field(default_factory=list)
    key: list[dict] = field(default_factory=list)
    reserve: list[dict] = field(default_factory=list)
    stamp: dict = field(default_factory=dict)


def write_round(out: Path, built: Built, *, force: bool) -> Path:
    """Write payload, key, reserve, stamp and the page itself.

    Under `temp/` and gitignored, and the page stays there: its crops are the
    reserved own-hand pixels, so it is opened as a local file and never
    published the way a humanbench round is (§8b, rule 1).
    """
    if out.exists() and any(out.iterdir()) and not force:
        raise SystemExit(f"{out} is not empty — a round is written once; pass --force to overwrite")
    out.mkdir(parents=True, exist_ok=True)
    envelope = {
        "round": built.stamp.get("round"),
        "question": "tintentreue",
        "store": round_store(built.stamp, built.items),
        "items": built.items,
    }
    (out / "payload.json").write_text(json.dumps(envelope, separators=(",", ":")), encoding="utf-8")
    for name, rows in (("key.json", built.key), ("reserve.json", built.reserve)):
        (out / name).write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "provenance.json").write_text(
        json.dumps(built.stamp, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    return write_page(envelope, out / "seite.html", round_label=str(built.stamp.get("round") or ""))


# -------------------------------------------------------------- the judgements


@dataclass(frozen=True)
class Verdict:
    """One judged screen, as the result text carries it."""

    uid: str
    codes: tuple[str, ...]
    seconds: int | None
    note: str | None
    position: int

    @property
    def step(self) -> str | None:
        """The one step code of this screen, or None where none was set."""
        steps = [code for code in self.codes if code in STEP_CODES]
        return steps[0] if len(steps) == 1 else None

    @property
    def details(self) -> tuple[str, ...]:
        return tuple(code for code in self.codes if code in DETAIL_CODES)

    @property
    def unsure(self) -> bool:
        return UNSURE in self.codes


def result_tag(round_label: Any) -> str:
    """The header tag the page stamps on THIS round's result file."""
    return f"{STRIP_TAG}/{round_label}"


def parse_result(text: str, expect_tag: str | None = None) -> list[Verdict]:
    """Parse the text the page's „fertig" screen emits.

    The three line shapes come from `tools.humanbench.analyse` rather than from
    a second copy of the regexes: the page that writes this file is the same
    one, and two spellings of its format would drift the first time either
    moves. What is this round's own is the VOCABULARY — a fit verdict pasted in
    here has to be refused rather than read as an unknown code.

    The vocabulary alone does not separate the two rounds, which is why
    `expect_tag` exists: both mint `S###`/`R##` ids, and `A`, `U` and `-` are
    legal in either, so a fit result can be read a long way in before a letter
    shows up that does not belong. The header names the round it came out of,
    and holding it against the one being evaluated is the cheap answer.
    """
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ResultFormatError("empty result")
    head = RESULT_HEAD.match(lines[0])
    if not head:
        raise ResultFormatError(f"no header line, got {lines[0]!r}")
    if expect_tag is not None and head.group("tag") != expect_tag:
        raise ResultFormatError(
            f"the result is headed {head.group('tag')!r} but this round is {expect_tag!r} — "
            f"wrong round, or a fit round's file?"
        )
    verdicts: list[Verdict] = []
    seen: set[str] = set()
    tallies = False
    for position, line in enumerate(lines[1:]):
        tally = TALLY_LINE.match(line)
        if tally and tally.group("label").strip() in TALLY_CODE:
            tallies = True
            continue
        if tallies:
            raise ResultFormatError(f"line {position + 2}: verdict line behind the tally block: {line!r}")
        match = RESULT_LINE.match(line)
        if not match:
            raise ResultFormatError(f"line {position + 2} does not parse: {line!r}")
        raw = match.group("verdict")
        codes = tuple(dict.fromkeys(raw)) if raw != "-" else ()
        unknown = [code for code in codes if code not in ALL_CODES]
        if unknown:
            raise ResultFormatError(
                f"line {position + 2}: {''.join(unknown)} is not a Tintentreue code — is this a fit round?"
            )
        uid = match.group("uid")
        if uid in seen:
            raise ResultFormatError(f"line {position + 2}: {uid} judged twice")
        seen.add(uid)
        verdicts.append(
            Verdict(
                uid=uid,
                codes=codes,
                seconds=int(match.group("seconds")) if match.group("seconds") else None,
                note=match.group("note"),
                position=position,
            )
        )
    return verdicts


# --------------------------------------------------------- the evaluation plan
# The order below is the pre-registered one and it is code so that it cannot be
# reordered after the labels exist (`menschliche-bewertung.md` §8b).


def reliability(verdicts: Sequence[Verdict], key: Mapping[str, dict]) -> dict[str, Any]:
    """Step 1 — the blind repeats, before any bound is computed.

    Two figures, because two different things can go wrong: exact agreement
    says how often the judge repeats himself, and „two steps apart" counts the
    pairs where he called the same box „folgt" once and „folgt nicht" the
    other time. The second is not noise; it says the question was not answered
    the same way twice, and no quantile over such labels means anything.
    """
    answers = {verdict.uid: verdict for verdict in verdicts}
    pairs: list[tuple[str, str]] = []
    far = 0
    for uid, entry in key.items():
        origin = entry.get("repeat_of")
        if not origin or uid not in answers or origin not in answers:
            continue
        first, second = answers[origin].step, answers[uid].step
        if first is None or second is None:
            continue
        pairs.append((first, second))
        if abs(STEP_CODES.index(first) - STEP_CODES.index(second)) >= 2:
            far += 1
    agree = sum(1 for first, second in pairs if first == second)
    share = agree / len(pairs) if pairs else 0.0
    return {
        "pairs": len(pairs),
        "agree": agree,
        "share": share,
        "far": far,
        "enough": len(pairs) >= MIN_REPEATS and share >= RELIABLE_EXACT and far <= MAX_FAR_PAIRS,
    }


def occupancy(judged: Sequence[Verdict]) -> dict[str, int]:
    """Step 2 — how many boxes each step actually carries."""
    counts = dict.fromkeys(STEP_CODES, 0)
    for verdict in judged:
        step = verdict.step
        if step:
            counts[step] += 1
    return counts


def _first_showings(verdicts: Sequence[Verdict], key: Mapping[str, dict]) -> list[Verdict]:
    """The judged screens minus the repeats and minus the unrated ones.

    A repeat is the SAME box a second time; counting it would weight that box
    twice in every quantile. `X` is an exclusion, exactly as `K` is in §2.
    """
    return [
        verdict
        for verdict in verdicts
        if not (key.get(verdict.uid) or {}).get("repeat_of") and UNRATABLE not in verdict.codes and verdict.step
    ]


def dead_branches(judged: Sequence[Verdict], key: Mapping[str, dict]) -> dict[str, Any]:
    """Step 4, gate (B) — does every graded sensor NAME a box over the pass?

    The light reports one sensor per box („woran es lag"), and that name is
    what the key carries. A sensor that never comes up across the whole pass is
    a dead branch: it is graded, it is printed, and nothing ever routes through
    it. Freezing a bound onto such a branch would freeze a number that has no
    case behind it, so the pre-registration kills the round at
    `DEAD_BRANCH_KILL` of them rather than calibrating around it.

    Counted on the FIRST showings only, for the same reason every other figure
    here is: a repeat would weight its own sensor twice.
    """
    counts = dict.fromkeys(SENSOREN_MIT_SCHWELLE, 0)
    for verdict in judged:
        named = (key.get(verdict.uid) or {}).get("sensor")
        if named in counts:
            counts[named] += 1
    dead = [sensor for sensor, count in counts.items() if count == 0]
    return {"counts": counts, "dead": dead, "kill": len(dead) >= DEAD_BRANCH_KILL}


def against_the_light(judged: Sequence[Verdict], key: Mapping[str, dict]) -> dict[str, Any]:
    """Step 4 — the provisional traffic light held against the human.

    Gates (A) and (C) of „Tintentreue `sep20`": agreement, the monotone order
    of the three steps, and the false-green rate — a box the judge calls bad
    that the light calls „folgt". The last one is reported separately because
    it is the only error class that creates work in the wrong place.

    The false-green figure comes back twice. `false_green_share` is over ALL
    judged boxes and is the number the pre-registration named; `false_green_of_green`
    is over the light-green ones alone. Only the second is invariant under the
    stratification — the share of green boxes in this round is a property of
    the draw, not of the hand (§8b, rule 4) — so it is the one the kill
    criterion is read on, and both are printed so the difference is visible.
    """
    rows = [(verdict, key.get(verdict.uid) or {}) for verdict in judged]
    matched = sum(1 for verdict, entry in rows if STEP_OF_CODE.get(verdict.step or "") == entry.get("stufe"))
    good_share: dict[str, float | None] = {}
    for step in STUFEN:
        of_step = [verdict for verdict, entry in rows if entry.get("stufe") == step]
        good_share[step] = (
            None if not of_step else sum(1 for verdict in of_step if verdict.step == FOLLOWS) / len(of_step)
        )
    measured = [share for share in good_share.values() if share is not None]
    green = [(verdict, entry) for verdict, entry in rows if entry.get("stufe") == STUFEN[0]]
    false_green = sum(1 for verdict, _ in green if verdict.step in (PARTLY, FAILS))
    return {
        "n": len(rows),
        "agreement": matched / len(rows) if rows else 0.0,
        "good_share": good_share,
        "monotone": all(first >= second for first, second in zip(measured, measured[1:], strict=False)),
        "false_green": false_green,
        "n_green": len(green),
        "false_green_share": false_green / len(rows) if rows else 0.0,
        "false_green_of_green": false_green / len(green) if green else None,
    }


def rank_value(values: Sequence[float], quantile: float) -> float:
    """The nearest-rank quantile: always a value the hand actually produced.

    An interpolated quantile would invent a reading between two boxes, and at
    thirty boxes that invented number would be the bound. Ascending order,
    rank ``ceil(q·n)``, clamped into the list.
    """
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(quantile * len(ordered)) - 1))
    return ordered[index]


def bound_of(values: Sequence[float], *, smaller_is_better: bool) -> float:
    """One bound out of one pool — `GREEN_QUANTILE` of it, rounded strictly.

    A sensor where LARGER is better is read through its own mirror rather than
    through a second convention: the readings are negated, the one rank rule
    applies, and the result is negated back. Two conventions would differ in
    exactly one place — how many boxes may fall outside the bound — and that is
    the number the bound IS.
    """
    pool = list(values) if smaller_is_better else [-value for value in values]
    cut = rank_value(pool, GREEN_QUANTILE)
    return _round_strict(cut if smaller_is_better else -cut, smaller_is_better=smaller_is_better)


def _round_strict(value: float, *, smaller_is_better: bool) -> float:
    """Round to `ROUND_DIGITS`, always towards the stricter side.

    Stricter means DOWN for a ceiling („at most 0,05 unvisited") and UP for a
    floor („at least 0,75 AIoU"). Never the arithmetic rounding: half of the
    time that loosens the bound, and a bound loosened by a rounding step is the
    false green gate (C) is about.
    """
    scale = 10**ROUND_DIGITS
    strict = math.floor(value * scale) if smaller_is_better else math.ceil(value * scale)
    return strict / scale


def cuts(judged: Sequence[Verdict], key: Mapping[str, dict], thresholds: Schwellen) -> dict[str, dict[str, Any]]:
    """Step 5 — the green and yellow bound of every quantile sensor.

    Green over the boxes judged „folgt", yellow over „folgt" ∪ „folgt teils",
    both at the 90 % quantile — or at 10 % from below where larger is better.
    A pair that does not come out STRICTLY ordered is refused rather than
    smoothed, and equality is the ordinary way that happens: it means the
    sensor does not separate the two steps on this round, and a yellow band of
    zero width would quietly turn the three-step light into a two-step one. The
    borrowed value stays, with its label on.
    """
    readings_of = {verdict.uid: (key.get(verdict.uid) or {}).get("readings") or {} for verdict in judged}
    steps = {verdict.uid: verdict.step for verdict in judged}
    out: dict[str, dict[str, Any]] = {}
    for sensor in (*SMALLER_IS_BETTER, *LARGER_IS_BETTER):
        smaller = sensor in SMALLER_IS_BETTER
        green_pool = [
            float(readings_of[uid][sensor])
            for uid, step in steps.items()
            if step == FOLLOWS and isinstance(readings_of[uid].get(sensor), (int, float))
        ]
        yellow_pool = green_pool + [
            float(readings_of[uid][sensor])
            for uid, step in steps.items()
            if step == PARTLY and isinstance(readings_of[uid].get(sensor), (int, float))
        ]
        borrowed_green, borrowed_yellow = (
            getattr(thresholds, BOUND_FIELDS[sensor][0]),
            getattr(thresholds, BOUND_FIELDS[sensor][1]),
        )
        row: dict[str, Any] = {
            "n_green": len(green_pool),
            "n_yellow": len(yellow_pool),
            "borrowed": (borrowed_green, borrowed_yellow),
            "green": None,
            "yellow": None,
            "why": "",
        }
        if len(green_pool) < MIN_PER_STEP or len(yellow_pool) < MIN_PER_STEP:
            row["why"] = f"zu wenig Daten ({len(green_pool)}/{len(yellow_pool)} < {MIN_PER_STEP}) — bleibt geborgt"
            out[sensor] = row
            continue
        green = bound_of(green_pool, smaller_is_better=smaller)
        yellow = bound_of(yellow_pool, smaller_is_better=smaller)
        ordered = green < yellow if smaller else green > yellow
        if not ordered:
            row["why"] = f"grün {green} / gelb {yellow} nicht geordnet — verworfen, bleibt geborgt"
            out[sensor] = row
            continue
        row["green"], row["yellow"] = green, yellow
        row["why"] = "gemessen"
        out[sensor] = row
    return out


def pen_lift_cut(judged: Sequence[Verdict], key: Mapping[str, dict], thresholds: Schwellen) -> dict[str, Any]:
    """Step 5, the integer half — the Absetzer bound is a rule, not a quantile.

    It drops from ±1 to 0 only where the round actually shows that one
    unexplained pen event is already fatal: at least `PEN_LIFT_TIGHTEN_MIN`
    boxes off by exactly one run, most of them judged „folgt nicht".
    """
    off_by_one: list[Verdict] = []
    for verdict in judged:
        entry = key.get(verdict.uid) or {}
        reading = (entry.get("readings") or {}).get(SENSOR_ABSETZER)
        expected = entry.get("absetzer_soll")
        if reading is None or expected is None:
            continue
        if abs(float(reading) - float(expected)) == 1:
            off_by_one.append(verdict)
    fails = sum(1 for verdict in off_by_one if verdict.step == FAILS)
    tighten = len(off_by_one) >= PEN_LIFT_TIGHTEN_MIN and fails * 2 > len(off_by_one)
    return {
        "n": len(off_by_one),
        "fails": fails,
        "gelb": 0 if tighten else thresholds.absetzer_gelb,
        "why": "verschärft auf 0" if tighten else "bleibt bei ±1",
    }


def jumps_proposal(judged: Sequence[Verdict], key: Mapping[str, dict]) -> dict[str, Any]:
    """Step 6 — the open item: do jumps and hairpins separate at all?

    A bound is PROPOSED only on a clean split: at least `JUMPS_MIN_POSITIVES`
    boxes carry the mark and the smallest flagged reading is above the largest
    unflagged one. Anything short of that leaves the sensor ungraded, which is
    where it stands today and where an unanchored number would be worse than
    nothing.
    """
    marked = next(code for code, sensor in SENSOR_OF_DETAIL.items() if sensor == SENSOR_SPRUENGE)
    flagged: list[float] = []
    rest: list[float] = []
    for verdict in judged:
        reading = ((key.get(verdict.uid) or {}).get("readings") or {}).get(SENSOR_SPRUENGE)
        if not isinstance(reading, (int, float)):
            continue
        (flagged if marked in verdict.details else rest).append(float(reading))
    clean = bool(flagged) and bool(rest) and min(flagged) > max(rest)
    proposed = None
    if len(flagged) >= JUMPS_MIN_POSITIVES and clean:
        proposed = round((min(flagged) + max(rest)) / 2, ROUND_DIGITS)
    return {
        "flagged": len(flagged),
        "rest": len(rest),
        "clean": clean,
        "proposed": proposed,
        "why": "Vorschlag" if proposed is not None else "bleibt ungewertet",
    }


# --------------------------------------------------------------------- the CLI


def _seed(round_number: int, explicit: int | None) -> int:
    return explicit if explicit is not None else SEED_BASE + round_number


def _only(path: Path) -> set[tuple[str, str, int]]:
    """The identities a confirmation pass restricts itself to (§3.3).

    Read from a `reserve.json` or a `key.json`, and applied BEFORE the
    stratification, so the steps are cut over the set that is really judged
    rather than over one with holes in it.
    """
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {(row["strip"], row["fassung"], int(row["box_index"])) for row in rows}


def cmd_build(args: argparse.Namespace) -> int:
    check_hand_id(args.hand)
    base, token = api_base(args.api), admin_token(args.token)
    thresholds = schwellen_of(args.hand)
    seed = _seed(args.round, args.seed)
    rng = random.Random(seed)

    rows = boxes_of_hand(base, token, args.hand)
    if args.only:
        wanted = _only(args.only)
        rows = [row for row in rows if row.identity in wanted]
    if not rows:
        raise SystemExit(
            f"{args.hand} has no MEASURED word box — a grey box carries no reading to calibrate on. "
            f"Follow a Fassung first: uv run python -m tools.eigenhand.pfad --hand {args.hand} --strip S… --apply"
        )
    label, reserve = stratify(rows, args.n_label, rng)
    if len(label) < args.n_label:
        print(
            f"warning: {len(label)} measured boxes for a pass of {args.n_label} — the round is short, "
            f"and a short round carries no adoption claim",
            file=sys.stderr,
        )

    items: list[dict] = []
    key: list[dict] = []
    paths_cache: dict[tuple[str, str], dict] = {}
    # The drawing is cached per BOX, not only per Fassung, and that is a
    # property of the round rather than a saved request: a repeat has to be the
    # same screen down to the pixel. Two independently fetched crops would
    # almost always be identical — and „almost" is a tell the judge could learn
    # before anyone noticed it existed.
    drawings: dict[tuple[str, str, int], Drawing] = {}

    def render(uid: str, box: Box) -> dict:
        drawing = drawings.get(box.identity)
        if drawing is None:
            paths = paths_cache.get((box.strip, box.fassung))
            if paths is None:
                paths = fetch_paths(base, token, args.hand, box.strip, box.fassung)
                paths_cache[(box.strip, box.fassung)] = paths
            drawing = drawing_of(base, token, args.hand, box, paths)
            drawings[box.identity] = drawing
        return item_of(uid, drawing)

    for index, box in enumerate(label):
        box.uid = f"S{index + 1:03d}"
        items.append(render(box.uid, box))
        key.append(key_entry(box, box.uid))

    picks = pick_repeats(label, args.repeats, args.min_repeat_gap, rng)
    gaps = insert_repeats(items, key, picks, render, min_gap=args.min_repeat_gap, rng=rng)
    if len(picks) < MIN_REPEATS:
        print(
            f"warning: only {len(picks)} repeats placed ({MIN_REPEATS} is the floor) — the pass measures "
            f"no reliability of its own, so it carries no adoption claim",
            file=sys.stderr,
        )

    counts = {"population": len(rows), "label": len(label), "reserve": len(reserve), "screens": len(items)}
    counts["per_step"] = {step: sum(1 for row in label if row.step == step) for step in STUFEN}
    stamp = provenance(
        args,
        seed=seed,
        thresholds=thresholds,
        counts=counts,
        repeats={"placed": len(picks), "gaps": gaps, "min_gap": args.min_repeat_gap},
    )
    out = Path(args.out) / f"r{args.round}"
    built = Built(items=items, key=key, reserve=[reserve_entry(box) for box in reserve], stamp=stamp)
    page = write_round(out, built, force=args.force)

    print(f"round {args.round} for {args.hand}: {len(items)} screens ({len(label)} boxes + {len(picks)} repeats)")
    print(
        f"  population {len(rows)} measured boxes, per step "
        + " · ".join(f"{step} {counts['per_step'][step]}" for step in STUFEN)
    )
    print(f"  reserve {len(reserve)} boxes — a confirmation pass runs with --only {out / 'reserve.json'}")
    print(f"  repeat gaps {gaps}")
    print(f"  thresholds {thresholds.stand}" + (" (vorläufig)" if thresholds.vorlaeufig else " (kalibriert)"))
    print(f"  wrote {page}")
    print("  the page carries reserved own-hand pixels: open it locally, never publish it, never commit it")
    return 0


def cmd_analyse(args: argparse.Namespace) -> int:
    room = Path(args.round_dir)
    key = {entry["uid"]: entry for entry in json.loads((room / "key.json").read_text(encoding="utf-8"))}
    stamp = json.loads((room / "provenance.json").read_text(encoding="utf-8"))
    thresholds = schwellen_of(str(stamp.get("hand") or ""))
    verdicts = parse_result(Path(args.result).read_text(encoding="utf-8"), result_tag(stamp.get("round")))
    unknown = [verdict.uid for verdict in verdicts if verdict.uid not in key]
    if unknown:
        raise SystemExit(f"the result names screens this round does not have: {', '.join(unknown[:5])}")

    print(f"Tintentreue-Kalibrierung — Runde {stamp.get('round')}, Hand {stamp.get('hand')}")
    print(
        f"  Schwellen der Ziehung: {stamp.get('schwellen', {}).get('stand')} "
        f"({'vorläufig' if stamp.get('schwellen', {}).get('vorlaeufig') else 'kalibriert'})"
    )

    # 1 — reliability, before anything else.
    reliable = reliability(verdicts, key)
    print(
        f"\n1 Verlässlichkeit: {reliable['agree']}/{reliable['pairs']} Paare gleich "
        f"({reliable['share']:.0%}), {reliable['far']} zwei Stufen auseinander — "
        f"{'trägt' if reliable['enough'] else 'TRÄGT NICHT'} "
        f"(Schranke {RELIABLE_EXACT:.0%}, ≥ {MIN_REPEATS} Paare, ≤ {MAX_FAR_PAIRS} weit)"
    )

    judged = _first_showings(verdicts, key)
    unsure_free = [verdict for verdict in judged if not verdict.unsure]

    # 2 — occupancy.
    counts = occupancy(judged)
    print("\n2 Besetzung: " + " · ".join(f"{CODE_LABEL[code]} {counts[code]}" for code in STEP_CODES))
    thin = [CODE_LABEL[code] for code in (FOLLOWS, PARTLY) if counts[code] < MIN_PER_STEP]
    if thin:
        print(f"  zu wenig Daten für: {', '.join(thin)} — die davon abhängigen Grenzen bleiben geborgt")

    # 3 — the mapping is the identity; `X` and the repeats are already out.
    excluded = sum(1 for verdict in verdicts if UNRATABLE in verdict.codes)
    print(f"\n3 Abbildung angewandt: {len(judged)} Kästen gewertet, {excluded} nicht beurteilbar (ausgeschlossen)")

    # 4 — the light against the human, with and without the unsure ones.
    for label, rows in (("alle", judged), ("ohne unsichere", unsure_free)):
        if not rows:
            continue
        seen = against_the_light(rows, key)
        of_green = seen["false_green_of_green"]
        print(
            f"\n4 Ampel gegen Mensch ({label}, n = {seen['n']}): Übereinstimmung {seen['agreement']:.0%} "
            f"(Gate ≥ {AGREEMENT_GATE:.0%}, Kill < {AGREEMENT_KILL:.0%}) · "
            f"{'monoton' if seen['monotone'] else 'NICHT MONOTON'}"
        )
        print(
            f"  falsch grün {seen['false_green']} von {seen['n_green']} ampelgrünen "
            f"({'—' if of_green is None else format(of_green, '.0%')}, Kill > {FALSE_GREEN_MAX:.0%}) · "
            f"über alle gewerteten {seen['false_green_share']:.0%}"
        )
        shares = " · ".join(
            f"{step} {'—' if share is None else format(share, '.0%')}" for step, share in seen["good_share"].items()
        )
        print(f"  Anteil {STUFEN[0]} je Ampelstufe: {shares}")

    # 4, gate (B) — a graded sensor that names nothing is a dead branch.
    branches = dead_branches(judged, key)
    named = " · ".join(f"{sensor} {count}" for sensor, count in branches["counts"].items())
    print(f"\n4b Kein toter Zweig — benannte Kästen je Sensor: {named}")
    if branches["dead"]:
        print(
            f"  ohne Nennung: {', '.join(branches['dead'])} — "
            + ("KILL (Gate (B))" if branches["kill"] else f"unter dem Kill von {DEAD_BRANCH_KILL}")
        )

    if not reliable["enough"]:
        print("\n5 Keine Grenze gesetzt — die Verlässlichkeit trägt nicht (Gate (F)). Die acht Zahlen bleiben geborgt.")
        return 0

    # 5 — the bounds.
    print("\n5 Grenzen je Sensor (nächstrangiges Quantil, strenger gerundet):")
    derived = cuts(judged, key, thresholds)
    for sensor, row in derived.items():
        borrowed = row["borrowed"]
        if row["green"] is None:
            print(f"  {sensor}: {row['why']} (geborgt grün {borrowed[0]} / gelb {borrowed[1]})")
        else:
            print(
                f"  {sensor}: grün {row['green']} / gelb {row['yellow']} "
                f"(geborgt {borrowed[0]} / {borrowed[1]}, n = {row['n_green']}/{row['n_yellow']})"
            )
    pen_lifts = pen_lift_cut(judged, key, thresholds)
    print(
        f"  {SENSOR_ABSETZER}: {pen_lifts['why']} ({pen_lifts['fails']} von {pen_lifts['n']} Kästen mit Abweichung 1)"
    )

    # 6 — the open item.
    jumps = jumps_proposal(judged, key)
    print(
        f"\n6 {SENSOR_SPRUENGE}: {jumps['why']}"
        + (f" — Grenze {jumps['proposed']}" if jumps["proposed"] is not None else "")
        + f" ({jumps['flagged']} markiert, {jumps['rest']} nicht, Trennung "
        f"{'sauber' if jumps['clean'] else 'überlappt'})"
    )

    # 7 — one set, one date. The adoption itself is the author's commit.
    print("\n7 Ein Satz, ein Datum — Vorschlag für `SCHWELLEN_JE_HAND` (Übernahme ist ein Schritt des Autors):")
    print(_thresholds_block(str(stamp.get("hand") or ""), derived, pen_lifts, thresholds))
    return 0


def _thresholds_block(hand: str, derived: Mapping[str, dict], pen_lifts: Mapping[str, Any], borrowed: Schwellen) -> str:
    """The pasteable block — with every value that stayed borrowed named as such.

    Printed rather than written: adopting a calibration edits `core/`, dates a
    set and drops a label, and that is a decision with a commit behind it. A
    tool that wrote the file would make it a side effect of running a report.

    The LABEL follows the numbers rather than the occasion: `vorlaeufig` falls
    only where every bound of the set was measured on this hand. A set that
    drops it while half its values are still read off the plate would claim a
    calibration that did not happen — which is the one thing the label exists
    to prevent.
    """

    def value(sensor: str, which: int, fallback: float) -> tuple[float, bool]:
        row = derived.get(sensor) or {}
        measured = row.get("green" if which == 0 else "yellow")
        return (fallback, False) if measured is None else (measured, True)

    fields: list[tuple[str, float, bool]] = []
    for sensor, (green_field, yellow_field) in BOUND_FIELDS.items():
        green, green_measured = value(sensor, 0, getattr(borrowed, green_field))
        yellow, yellow_measured = value(sensor, 1, getattr(borrowed, yellow_field))
        fields.append((green_field, green, green_measured))
        fields.append((yellow_field, yellow, yellow_measured))
    # The Absetzer counts as measured once the rule could actually fire — the
    # round then KEPT ±1 rather than never having tested it.
    fields.append(("absetzer_gelb", pen_lifts["gelb"], pen_lifts["n"] >= PEN_LIFT_TIGHTEN_MIN))
    today = datetime.now(UTC).date().isoformat()
    complete = all(measured for _, _, measured in fields)
    label = "    vorlaeufig=False," if complete else "    vorlaeufig=True,  # nicht jede Grenze ist gemessen"
    lines = [f'SCHWELLEN_JE_HAND["{hand}"] = Schwellen(', f'    stand="{today}",', label]
    lines += [
        f"    {name}={number}," + ("" if measured else "  # geborgt — diese Runde hat sie nicht gemessen")
        for name, number, measured in fields
    ]
    lines.append(")")
    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tools.eigenhand.tintentreue_calibration",
        description="The blind calibration pass for the Tintentreue bounds of ONE hand.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="draw the boxes, fetch the crops, write the round and its page")
    build.add_argument("--hand", required=True, help="hand id, e.g. mn-suetterlin")
    build.add_argument("--round", type=int, required=True, help="pass number — heads the result file")
    build.add_argument("--api", default=None, help="API base URL (default: $EIGENHAND_API or production)")
    build.add_argument("--token", default=None, help="admin token (default: $ADMIN_TOKEN)")
    build.add_argument("--n-label", type=int, default=N_LABEL, help=f"boxes to judge [{N_LABEL}]")
    build.add_argument("--repeats", type=int, default=N_REPEATS, help=f"blind repeats [{N_REPEATS}]")
    build.add_argument(
        "--min-repeat-gap", type=int, default=MIN_REPEAT_GAP, help=f"screens before a repeat [{MIN_REPEAT_GAP}]"
    )
    build.add_argument("--seed", type=int, default=None, help=f"shuffle seed [{SEED_BASE} + round]")
    build.add_argument("--only", type=Path, default=None, help="restrict to the identities in this reserve/key file")
    build.add_argument("--out", default=DEFAULT_OUT_ROOT, help=f"output root [{DEFAULT_OUT_ROOT}]")
    build.add_argument("--stamp", default="", help="build timestamp (default: now) — for a reproducible rebuild")
    build.add_argument("--force", action="store_true", help="overwrite an existing round directory")
    build.set_defaults(func=cmd_build)

    analyse = sub.add_parser("analyse", help="the pre-registered evaluation of a judged round")
    analyse.add_argument("--round-dir", required=True, help="the directory `build` wrote")
    analyse.add_argument("--result", required=True, help="the result text pasted out of the page")
    analyse.set_defaults(func=cmd_analyse)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
