"""Unit tests for tools/humanbench/build.py — the sampling half of the round.

The builder decides WHICH occurrences a human spends hours on, and every rule in
it was bought with a round that measured the wrong thing. Those rules are pure
functions over plain rows, so they can be checked without a chart, a database or
an API — which is the whole reason they are worth checking: the alternative is
finding out afterwards, when the hours are already spent.

Two of the tests below grade the safeguard against the failure it was added for
rather than against a snapshot: the within-band shuffle is compared with the
unshuffled deal that made the cleanest occurrences unreachable, and the repeat
gaps are measured on the FINISHED sequence rather than at insertion time.

Everything is synthetic — a real payload carries occurrence geometry, which
stays out of this repo (``docs/reference/quellen-und-rechte.md`` §5).
"""

from __future__ import annotations

import base64
import json
import random
from collections import Counter

import numpy as np
import pytest

from tools.humanbench.build import (
    REPEAT_JITTER,
    REPEAT_MIN_GLYPH_COUNT,
    Occurrence,
    crop_window,
    identities_from,
    insert_repeats,
    match_pairs,
    occurrence_rows,
    parse_args,
    pick_repeats,
    polyline_strokes,
    provenance,
    rank_rows,
    render_item,
    slim_key,
    stratify,
)


BANDS = 5
POPULATION = 245  # the round-1 population, so the numbers below are its numbers


def occurrence(index: int, *, glyph: str = "e", word: str = "wenn", slot: int = 0, peak: float = 0.0) -> Occurrence:
    return Occurrence(
        glyph_key=glyph,
        specimen_id=word,
        slot=slot,
        sample={"id": word, "page": "p.png", "x0": 0, "y0": 0, "x1": 100, "y1": 60},
        xh=20.0,
        points=np.array([[float(index), 1.0], [float(index) + 5, 9.0]]),
        stroke_starts=[0],
        peak=peak,
        peak_at=0,
        n_anchors=12,
    )


def population(n: int = POPULATION) -> list[Occurrence]:
    """`n` occurrences, worst first, over enough glyphs to draw repeats from."""
    glyphs = ["e", "n", "a", "r", "s", "t", "S"]
    rows = [
        occurrence(i, glyph=glyphs[i % len(glyphs)], word=f"w{i // 7}", slot=i % 4, peak=1.0 - i / (2 * n))
        for i in range(n)
    ]
    return rank_rows(rows)


def deal_without_shuffle(rows: list[Occurrence], bands: int) -> list[Occurrence]:
    """The round-1 draft: round-robin across the bands, sorted WITHIN each."""
    size = (len(rows) + bands - 1) // bands
    banded = [rows[i * size : (i + 1) * size] for i in range(bands)]
    return [band[i] for i in range(size) for band in banded if i < len(band)]


# ------------------------------------------------------------------ stratifying


def test_stratify_keeps_every_row_and_holds_the_tail_back():
    rows = population()
    label, reserve, band_size = stratify(rows, BANDS, 150, random.Random(20260808))
    assert (len(label), len(reserve)) == (150, 95)
    assert band_size == 49
    assert {r.identity for r in label} | {r.identity for r in reserve} == {r.identity for r in rows}
    assert not ({r.identity for r in label} & {r.identity for r in reserve})


def test_the_reserve_is_band_balanced_and_therefore_usable_as_a_hold_out():
    """Develop on the labelled set, confirm on the reserve — only if it is a
    sample of the same population rather than the leftovers of one band."""
    _label, reserve, band_size = stratify(population(), BANDS, 150, random.Random(20260808))
    per_band = Counter(min(r.rank // band_size, BANDS - 1) for r in reserve)
    assert set(per_band) == set(range(BANDS))
    assert max(per_band.values()) - min(per_band.values()) <= 1


def test_the_within_band_shuffle_is_what_reaches_the_cleanest_cases():
    """The failure the shuffle was added for, measured against it.

    Dealing round-robin across severity bands is not enough: with the order
    INSIDE a band left peak-descending, a 150-item prefix reached ranks 0-215 of
    245 and the cleanest occurrences — where every metric's false positives
    live — were unreachable.
    """
    rows = population()
    label, _reserve, _size = stratify(rows, BANDS, 150, random.Random(20260808))
    unshuffled = deal_without_shuffle(rows, BANDS)

    assert max(r.rank for r in unshuffled[:100]) == 215  # the round-1 draft, verbatim
    assert max(r.rank for r in label[:100]) >= 235  # the fix reaches the tail
    assert min(r.rank for r in label[:100]) <= 5


def test_stratify_is_reproducible_from_the_seed():
    rows = population()
    first = [r.identity for r in stratify(rows, BANDS, 150, random.Random(4711))[0]]
    again = [r.identity for r in stratify(population(), BANDS, 150, random.Random(4711))[0]]
    assert first == again
    other = [r.identity for r in stratify(population(), BANDS, 150, random.Random(4712))[0]]
    assert other != first


# --------------------------------------------------------------------- repeats


def label_set(n_label: int = 150) -> tuple[list[Occurrence], int]:
    label, _reserve, band_size = stratify(population(), BANDS, n_label, random.Random(20260808))
    for i, row in enumerate(label):
        row.uid = f"S{i + 1:03d}"
    return label, band_size


def picks_of(label, band_size, **kwargs):
    options = {
        "band_size": band_size,
        "bands": BANDS,
        "n_repeats": 12,
        "min_gap": 40,
        "exclude": ("S",),
        "rng": random.Random(99),
    }
    return pick_repeats(label, **{**options, **kwargs})


def test_repeats_come_from_frequent_glyphs_only():
    """A glyph seen once is memorable on its own; repeating it measures memory."""
    label, band_size = label_set()
    counts = Counter(row.glyph_key for row in label)
    for row in picks_of(label, band_size):
        assert counts[row.glyph_key] >= REPEAT_MIN_GLYPH_COUNT


def test_the_known_bad_letter_is_never_repeated():
    label, band_size = label_set()
    assert any(row.glyph_key == "S" for row in label), "the fixture must contain the excluded glyph"
    assert all(row.glyph_key != "S" for row in picks_of(label, band_size))


def test_repeats_are_drawn_only_from_far_enough_up_the_sequence():
    """A repeat needs `min_gap` plus the jitter of room after it; one that lands
    seven screens later measures short-term memory rather than judgement."""
    label, band_size = label_set()
    positions = {row.uid: i for i, row in enumerate(label)}
    latest = len(label) - 40 - REPEAT_JITTER
    assert all(positions[row.uid] < latest for row in picks_of(label, band_size))


def test_repeats_spread_over_the_severity_bands():
    label, band_size = label_set()
    picks = picks_of(label, band_size)
    assert len(picks) == 12
    assert len({min(row.rank // band_size, BANDS - 1) for row in picks}) == BANDS


def test_an_exhausted_pool_yields_fewer_repeats_instead_of_raising():
    """Reported, never silent: a round with no repeats has no reliability bound
    to put next to its per-category numbers."""
    label, band_size = label_set()
    picks = picks_of(label, band_size, n_repeats=500)
    assert 0 < len(picks) < 500


def test_no_repeat_pool_at_all_is_an_empty_list():
    lonely = [occurrence(i, glyph=f"g{i}", word=f"w{i}") for i in range(30)]
    for i, row in enumerate(lonely):
        row.rank = i
        row.uid = f"S{i + 1:03d}"
    assert picks_of(lonely, 6) == []


# ------------------------------------------------------------------- splicing


def render_stub(uid: str, row: Occurrence, extra: dict | None = None) -> dict:
    return {"id": uid, "w": 10, "h": 10, "img": "", "panels": [{"strokes": [[[0, 0], [1, 1]]]}], "extra": extra or {}}


def spliced(n_repeats: int = 12, min_gap: int = 40, patch=None):
    label, band_size = label_set()
    items = [render_stub(row.uid, row) for row in label]
    key = [
        {
            "uid": row.uid,
            "identity": list(row.identity),
            "repeat_of": None,
            "glyph": row.glyph_key,
            "word": row.specimen_id,
            "slot": row.slot,
            "rank": row.rank,
            "order": ["old", "new"],
        }
        for row in label
    ]
    picks = picks_of(label, band_size, n_repeats=n_repeats, min_gap=min_gap)
    gaps = insert_repeats(items, key, picks, render_stub, min_gap=min_gap, rng=random.Random(7), patch=patch)
    return items, key, picks, gaps


def test_every_realised_gap_clears_the_minimum_on_the_finished_sequence():
    """Measured after all splicing, not at insertion time.

    A later repeat inserted between the two showings pushes them apart, so the
    insertion-time distance is not the one the judge walks — and the reported
    number has to be the walked one, or „gaps 40-65" is a claim about a sequence
    that was never shown.
    """
    items, key, _picks, gaps = spliced()
    position = {entry["uid"]: i for i, entry in enumerate(key)}
    for entry in key:
        if entry["repeat_of"]:
            assert position[entry["uid"]] - position[entry["repeat_of"]] >= 40
    assert min(gaps) >= 40
    assert [item["id"] for item in items] == [entry["uid"] for entry in key]


def test_a_repeat_copies_its_first_showing_and_is_marked_only_in_the_key():
    _items, key, picks, _gaps = spliced()
    by_uid = {entry["uid"]: entry for entry in key}
    for entry in key:
        if not entry["repeat_of"]:
            continue
        first = by_uid[entry["repeat_of"]]
        assert entry["identity"] == first["identity"]
        assert entry["glyph"] == first["glyph"] and entry["word"] == first["word"]
    assert sum(1 for e in key if e["repeat_of"]) == len(picks)


def test_a_mode_can_patch_the_second_showing_and_screen_and_key_agree():
    """The paired round mirrors its repeats: the identical screen could be
    answered with „I picked left last time", mirrored it has to be judged again.
    Whatever the patch returns has to reach BOTH the drawn screen and the record.
    """
    items, key, _picks, _gaps = spliced(patch=lambda entry: {"order": list(reversed(entry["order"])), "mirrored": True})
    by_id = {item["id"]: item for item in items}
    repeats = [entry for entry in key if entry["repeat_of"]]
    assert repeats, "the fixture must place repeats"
    for entry in repeats:
        assert entry["order"] == ["new", "old"] and entry["mirrored"] is True
        assert by_id[entry["uid"]]["extra"]["order"] == entry["order"]


# ---------------------------------------------------------------- the two sets


def test_match_pairs_joins_on_identity_and_counts_what_only_one_side_has():
    """A change that quietly stops producing a fit is a result — it must not
    disappear into a shorter round that still looks complete."""
    old = [occurrence(0, glyph="a", word="das", slot=1), occurrence(1, glyph="e", word="lesen", slot=2)]
    new = [occurrence(9, glyph="e", word="lesen", slot=2), occurrence(8, glyph="n", word="denen", slot=3)]
    pairs, report = match_pairs(old, new)
    assert [(o.identity, n.identity) for o, n in pairs] == [(("e", "lesen", 2), ("e", "lesen", 2))]
    assert report == {"matched": 1, "only_old": ["a/das/1"], "only_new": ["n/denen/3"]}


# ------------------------------------------------------------------- rendering


def test_crop_window_pads_proportionally_to_the_x_height():
    """A fixed pad hides the evidence exactly where it matters: the worst
    deviations reach a third of an x-height, so the ink the line SHOULD have
    been on could sit outside the crop."""
    points = np.array([[100.0, 100.0], [140.0, 130.0]])
    assert crop_window(points, 50.0, (400, 400), 0.4) == (80, 80, 160, 150)  # 20 px around the line
    assert crop_window(points, 25.0, (400, 400), 0.4) == (90, 90, 150, 140)  # half the x-height, half the pad
    assert crop_window(points, 10.0, (400, 400), 0.4) == (94, 94, 146, 136)  # the 6 px floor, not 4
    assert crop_window(points, 500.0, (400, 400), 0.4) == (0, 0, 340, 330)  # clamped to the crop, never past it


def test_polyline_strokes_never_bridges_a_pen_lift():
    """A lift drawn as a line is a stroke the writer never made, and the judge
    would report a defect the fit does not have."""
    points = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0], [10.0, 10.0], [11.0, 11.0]])
    strokes = polyline_strokes(points, [0, 3], (0, 0, 20, 20), 2)
    assert strokes == [[[0.0, 0.0], [2.0, 2.0], [4.0, 4.0]], [[20.0, 20.0], [22.0, 22.0]]]
    assert polyline_strokes(points, [0], (0, 0, 20, 20), 1)[0][-1] == [11.0, 11.0]  # one stroke stays whole


def test_polyline_strokes_drops_a_lift_that_would_leave_a_single_point():
    points = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    assert polyline_strokes(points, [0, 2], (0, 0, 9, 9), 1) == [[[0.0, 0.0], [1.0, 1.0]]]


class FakeSpecimens:
    """Just the crop and the distance field — no chart bytes, no skeleton."""

    def __init__(self, shape=(60, 90)) -> None:
        self._crop = np.zeros(shape, dtype=float)

    def crop(self, _sample: dict) -> np.ndarray:
        return self._crop

    def ink_distance(self, _sample: dict) -> np.ndarray:
        return np.zeros(self._crop.shape, dtype=float)


def test_a_paired_screen_draws_both_fits_on_one_image_and_says_nothing_else():
    """The shared crop is what keeps the comparison blind: separate crops would
    differ in size and in their view of the neighbouring ink — a tell that has
    nothing to do with the fits."""
    old = occurrence(10, glyph="a", word="das")
    new = occurrence(10, glyph="a", word="das")
    new.points = old.points + 3.0
    item = render_item("S001", [old, new], FakeSpecimens(), zoom=2, pad_xh=0.4)
    assert set(item) == {"id", "w", "h", "img", "panels"}
    assert [set(panel) for panel in item["panels"]] == [{"strokes"}, {"strokes"}]
    assert item["panels"][0]["strokes"] != item["panels"][1]["strokes"]
    assert base64.b64decode(item["img"])[:8] == b"\x89PNG\r\n\x1a\n"


def test_ineligible_instance_rows_are_counted_by_reason():
    """The population of a round is a FILTERED set, and a filter nobody counted
    looks exactly like an empty one — the stamp has to be able to tell „the
    harvest changed" from „the filter did"."""
    sample = {"id": "das", "page": "p.png", "x0": 0, "y0": 0, "x1": 90, "y1": 60}
    anchors = [[0.0, 0.0], [0.5, 0.4], [1.0, 0.0]]
    rows = [
        {
            "glyph_key": "a",
            "variant": 0,
            "anchors": anchors,
            "x0": 10,
            "y1": 50,
            "measurements": {"specimen_id": "das", "xh_px": 20.0, "slot": 1},
        },
        {
            "glyph_key": "a",
            "variant": 100,
            "anchors": anchors,
            "x0": 10,
            "y1": 50,
            "measurements": {"specimen_id": "das", "xh_px": 20.0, "slot": 1},
        },
        {
            "glyph_key": "a",
            "variant": 0,
            "anchors": [],
            "x0": 10,
            "y1": 50,
            "measurements": {"specimen_id": "das", "xh_px": 20.0, "slot": 2},
        },
        {
            "glyph_key": "a",
            "variant": 0,
            "anchors": anchors,
            "x0": 10,
            "y1": 50,
            "measurements": {"specimen_id": "unvermessen", "xh_px": 20.0, "slot": 3},
        },
    ]
    dropped = Counter()
    kept = occurrence_rows(rows, {"das": sample}, {"a": [0]}, FakeSpecimens(), dropped)
    assert [row.identity for row in kept] == [("a", "das", 1)]
    assert dict(dropped) == {"derived_variant": 1, "no_anchors": 1, "specimen_not_measured": 1}


# --------------------------------------------------------- key, stamp, --only


def test_the_slim_key_carries_the_identity_and_no_measurement():
    """What a uid means may be archived; what it scored may not."""
    key = [
        {
            "uid": "S001",
            "identity": ["a", "das", 1],
            "repeat_of": None,
            "glyph": "a",
            "word": "das",
            "slot": 1,
            "peak": 0.31,
            "at": 4,
            "n": 12,
            "rank": 7,
        }
    ]
    assert slim_key(key) == [{"uid": "S001", "glyph": "a", "word": "das", "slot": 1, "repeat_of": None}]


def test_the_slim_key_keeps_two_occurrences_of_one_letter_in_one_word_apart():
    """Round 1's archive dropped `slot`, and three of its screens were a letter
    that appears twice in the same word — indistinguishable once carried
    forward."""
    key = [
        {"uid": "S001", "glyph": "n", "word": "einen", "slot": 2, "repeat_of": None},
        {"uid": "S002", "glyph": "n", "word": "einen", "slot": 4, "repeat_of": None},
    ]
    slim = slim_key(key)
    assert len({(e["glyph"], e["word"], e["slot"]) for e in slim}) == 2


def test_identities_from_reads_both_file_shapes():
    """`--only` is pointed at a reserve file (identity triples) or at the slim
    key of an earlier round (flat fields)."""
    assert identities_from([{"identity": ["a", "das", 1]}]) == {("a", "das", 1)}
    assert identities_from([{"glyph": "e", "word": "lesen", "slot": 2}]) == {("e", "lesen", 2)}
    assert identities_from([{"word": "lesen"}, {"glyph": "e"}]) == set()


def test_the_stamp_records_what_a_rebuild_needs():
    """Including the two repeat rules that are constants rather than flags, and
    whether the tree the commit names was actually clean."""
    args = parse_args(["--round", "2", "--seed", "20260808", "--only", "reserve.json"])
    stamp = provenance(
        args, mode="single", seed=20260808, counts={"screens": 162}, repeats={"n_repeats": 12}, api_used=False
    )
    assert stamp["seed"] == 20260808 and stamp["round"] == 2
    assert stamp["repeat_min_glyph_count"] == REPEAT_MIN_GLYPH_COUNT
    assert stamp["repeat_jitter"] == REPEAT_JITTER
    assert set(stamp) >= {"code_commit", "code_branch", "code_dirty", "built_at", "format"}
    assert stamp["inputs"]["only"] == "reserve.json"
    assert stamp["inputs"]["api"] is None
    assert json.dumps(stamp)  # the stamp is written as JSON, so it has to be serialisable


@pytest.mark.parametrize("argv", [["--round", "2"], ["--round", "3", "--paired", "a.json", "b.json"]])
def test_parse_args_resolves_the_round_directory(argv):
    args = parse_args(argv)
    assert args.out.name == f"runde-{args.round}"
    assert args.source_id == "suetterlin-1922"
