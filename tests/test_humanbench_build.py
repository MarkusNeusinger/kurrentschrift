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
from PIL import Image

from tools.humanbench.build import (
    REPEAT_JITTER,
    REPEAT_MIN_GLYPH_COUNT,
    SIDE_BASE,
    SIDE_CANDIDATE,
    WORD_MIN_REPEAT_GAP,
    WORD_ZOOM,
    ArmStroke,
    ArmWord,
    Occurrence,
    WordCase,
    arm_gap,
    build_word,
    check_arm_scope,
    clipped_words,
    context_strokes,
    crop_window,
    identities_from,
    insert_repeats,
    load_arm,
    match_pairs,
    occurrence_rows,
    parse_args,
    pick_repeats,
    pick_word_repeats,
    polyline_strokes,
    provenance,
    rank_rows,
    render_item,
    render_word_item,
    slim_key,
    stratify,
    to_crop,
    word_cases,
    word_trace_context,
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


# ------------------------------------------------- the pen path around a letter
#
# Round 1 drew each letter's own anchors and nothing else, while the harvest
# fits a whole word as one chain — so every joined letter ended in mid-air and
# 23 % of the round was filed as „the entry stroke is missing". Re-measured
# afterwards, the ink beyond the letter sat 0.02 xh from the stored pen path.
# These tests exist so that drawing cannot silently lose the connectors again.


def test_a_word_trace_lands_in_crop_pixels_the_way_the_spa_maps_it():
    """px = u·xh + tx, py = (baseline_row + ty) − v·xh (registration.ts).

    Getting this wrong is not subtle — the trace then misses the letters by
    whole x-heights — but it IS silent, so the mapping is pinned here.
    """
    samples = {"lesen": {"id": "lesen", "y0": 100, "baseline_y": 180, "midband_y": 150}}
    traces = [
        {
            "specimen_id": "lesen",
            "strokes": [[[0.0, 0.0], [1.0, 1.0]]],
            "measurements": {"xh_px": 30.0, "registration_px": {"tx": 12.0, "ty": -2.0, "baseline_row": 70}},
        }
    ]
    context = word_trace_context(traces, samples)
    assert list(context) == ["lesen"]
    # baseline row 70 + ty −2 = 68; v = 1 is one x-height ABOVE it, y counted down.
    assert context["lesen"][0].tolist() == [[12.0, 68.0], [42.0, 38.0]]


def test_a_trace_without_a_measured_frame_falls_back_to_the_sidecar_lineature():
    samples = {"w": {"id": "w", "y0": 100, "baseline_y": 180, "midband_y": 150}}
    context = word_trace_context(
        [{"specimen_id": "w", "strokes": [[[0.0, 0.0], [2.0, 0.0]]], "measurements": {}}], samples
    )
    assert context["w"][0].tolist() == [[0.0, 80.0], [60.0, 80.0]]  # xh 30 from the lineature, baseline row 80


def test_traces_without_a_specimen_or_without_strokes_are_skipped_not_guessed():
    samples = {"w": {"id": "w", "y0": 0, "baseline_y": 30, "midband_y": 0}}
    traces = [
        {"specimen_id": "unknown", "strokes": [[[0, 0], [1, 1]]], "measurements": {}},
        {"specimen_id": "w", "strokes": [], "measurements": {}},
        {"specimen_id": "w", "strokes": [[[0, 0]]], "measurements": {}},  # a single point is not a line
    ]
    assert word_trace_context(traces, samples) == {}


def test_context_is_placed_in_the_same_window_as_the_judged_line():
    """Both go through the crop window, so they cannot drift apart on screen."""
    window = (10, 20, 60, 70)
    drawn = polyline_strokes(np.array([[10.0, 20.0], [20.0, 30.0]]), [0], window, 2)
    context = context_strokes([np.array([[10.0, 20.0], [30.0, 40.0]])], window, 2)
    assert drawn[0][0] == context[0][0] == [0.0, 0.0]
    assert context[0][1] == [40.0, 40.0]


def test_a_context_free_round_still_renders():
    """A word of one letter has no connectors; that is a round, not a failure."""
    assert context_strokes([], (0, 0, 10, 10), 2) == []
    assert context_strokes([np.array([[1.0, 1.0]])], (0, 0, 10, 10), 2) == []


# ------------------------------------------------------------------ the word mode
#
# The third mode judges two COMPOSITIONS of one specimen word against each other
# on the authenticity question. It is the only one that can see the defects
# every frozen ruler resamples away, so what is guarded here is that it draws
# the ink it claims to draw, in the frame it claims to draw it in, and that the
# arms cannot leak which side is which.


def arm_word(xh: float = 20.0, tx: float = 0.0, ty: float = 0.0, *, dy: float = 0.0, width: float = 0.15) -> ArmWord:
    line = np.array([[0.0, 0.0 + dy], [1.0, 1.0 + dy], [2.0, 0.0 + dy]])
    # One pen stroke's silhouette: an exterior ring plus the counter it encloses.
    outer = np.array([[0.0, 0.0], [1.0, 0.2], [1.0, -0.2], [0.0, -0.2]])
    hole = np.array([[0.3, 0.05], [0.6, 0.05], [0.6, -0.05], [0.3, -0.05]])
    return ArmWord(xh=xh, tx=tx, ty=ty, strokes=(ArmStroke(line, width),), fills=((outer, hole),))


def word_case(entry_id: str = "unter", **arms) -> WordCase:
    drawn = {SIDE_BASE: arm_word(), SIDE_CANDIDATE: arm_word(dy=0.1), **arms}
    return WordCase(
        entry_id=entry_id,
        text=entry_id,
        crop=np.zeros((60, 120), dtype=np.uint8),
        baseline_row=40.0,
        xh=20.0,
        arms=drawn,
        peak=0.1,
    )


def fixture_root(tmp_path, ids=("unter", "das", "lesen")):
    """A minimal word bench fixture root — manifest, word.json, crop.png.

    Written here rather than copied: the real roots are gitignored learned data
    (quellen-und-rechte.md §5), so a test that needed one could not run in CI at
    all — and the builder only ever reads these three things.
    """
    root = tmp_path / "suetterlin-1922"
    root.mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps({"source_id": "suetterlin-1922", "words": [{"id": i, "word": i, "scorable": True} for i in ids]})
    )
    for entry_id in ids:
        word_dir = root / entry_id
        word_dir.mkdir()
        (word_dir / "word.json").write_text(
            json.dumps({"id": entry_id, "word": entry_id, "rect": [0, 0, 120, 60], "baseline_y": 40, "midband_y": 20})
        )
        Image.fromarray(np.full((60, 120), 200, dtype=np.uint8), "L").save(word_dir / "crop.png")
    return root


def arm_file(tmp_path, name, ids, *, dy=0.0, width=0.15, xh=20.0):
    path = tmp_path / f"{name}.json"
    path.write_text(
        json.dumps(
            {
                "arm": name,
                "words": {
                    entry_id: {
                        "registration": {"xh_px": xh, "tx": 1.0, "ty": 0.0},
                        "strokes": [{"points": [[0.0, dy], [1.0, 1.0 + dy], [2.0, dy]], "width": width}],
                        "fills": [[[[0.0, 0.0], [1.0, 0.2], [1.0, -0.2]]]],
                    }
                    for entry_id in ids
                },
            }
        )
    )
    return path


def test_load_arm_reads_the_contract_and_stamps_the_bytes(tmp_path):
    """The digest is not decoration: an arm is produced outside this tool, and
    without it a round names a file that may since have been rewritten."""
    arm = load_arm(arm_file(tmp_path, "LF11", ["unter"]))
    assert arm.name == "LF11" and len(arm.digest) == 16
    drawn = arm.words["unter"]
    assert drawn.xh == 20.0 and drawn.tx == 1.0
    assert len(drawn.strokes) == 1 and drawn.strokes[0].width == 0.15
    assert len(drawn.fills) == 1


def test_an_arm_keeps_a_pen_stroke_s_rings_together_as_one_shape(tmp_path):
    """The grouping is the only thing that says which ring is a HOLE.

    A silhouette is an exterior plus the counters it encloses — the „Z" of
    „Zorn" ships 155 + 36 + 16 points. Flattened into independent shapes, every
    loop interior is painted solid and the writing reads as a blob exactly
    where it has a loop; the round would then be judging the renderer.
    """
    path = tmp_path / "arm.json"
    path.write_text(
        json.dumps(
            {
                "words": {
                    "Zorn": {
                        "registration": {"xh_px": 20.0},
                        "fills": [[[[0, 0], [4, 0], [4, 4], [0, 4]], [[1, 1], [3, 1], [3, 3]]]],
                    }
                }
            }
        )
    )
    fills = load_arm(path).words["Zorn"].fills
    assert len(fills) == 1, "one pen stroke, one shape"
    assert [len(ring) for ring in fills[0]] == [4, 3], "exterior and its counter stay together"


def test_a_flat_ring_list_is_refused_instead_of_read_as_one_shape(tmp_path):
    """Format 1 parses perfectly and fails SILENTLY — filled loop counters on
    every screen. Named, so the arm gets re-produced instead of judged."""
    path = tmp_path / "old.json"
    # Format 1: `fills` was a list of RINGS, not a list of shapes.
    path.write_text(
        json.dumps({"words": {"a": {"registration": {"xh_px": 20.0}, "fills": [[[0, 0], [4, 0], [4, 4]]]}}})
    )
    with pytest.raises(SystemExit, match="looks like format 1"):
        load_arm(path)


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"arm": "x"}, "needs a 'words' object"),
        ({"words": {"a": {"strokes": [{"points": [[0, 0], [1, 1]]}]}}}, "numeric xh_px"),
        ({"words": {"a": {"registration": {"xh_px": 20}, "strokes": [], "fills": []}}}, "nothing drawable"),
        ({"words": {"a": {"registration": {"xh_px": 20}, "strokes": [{"points": [[0, 0]]}]}}}, "at least two"),
    ],
)
def test_load_arm_refuses_what_would_draw_half_a_word(tmp_path, payload, message):
    path = tmp_path / "broken.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(SystemExit, match=message):
        load_arm(path)


def test_to_crop_maps_the_word_frame_the_way_the_word_bench_draws_it():
    """px = x·xh + tx, py = baseline_row + ty − y·xh (wordbench/run.py::_overlay).

    Restating the formula across a module boundary is unavoidable and getting it
    wrong is not subtle — the composition then misses the specimen by whole
    x-heights — but it IS silent, so it is pinned here.
    """
    arm = arm_word(xh=30.0, tx=12.0, ty=-2.0)
    points = np.array([[0.0, 0.0], [1.0, 1.0]])
    # baseline row 40 + ty −2 = 38; y = 1 is one x-height ABOVE it, y counted down.
    assert to_crop(points, arm, 40.0).tolist() == [[12.0, 38.0], [42.0, 8.0]]


def test_arm_gap_is_symmetric_and_measured_in_x_heights():
    """The word mode's severity key: how far the candidate MOVED the word."""
    left = [np.array([[0.0, 0.0], [10.0, 0.0]])]
    right = [np.array([[0.0, 4.0], [10.0, 4.0]])]
    assert arm_gap(left, right, 20.0) == pytest.approx(0.2)
    assert arm_gap(right, left, 20.0) == pytest.approx(0.2)


def test_word_cases_discard_and_count_a_word_only_one_arm_draws(tmp_path):
    """§8's rule, one layer up: a change that quietly stops composing a word is
    a RESULT, and must not vanish into a shorter round that looks complete."""
    root = fixture_root(tmp_path, ids=("unter", "das", "lesen", "keins"))
    base = load_arm(arm_file(tmp_path, "base", ["unter", "das", "lesen"]))
    candidate = load_arm(arm_file(tmp_path, "cand", ["unter", "lesen"], dy=0.1))
    dropped: Counter = Counter()
    cases = word_cases(root, base, candidate, dropped=dropped)
    assert [c.entry_id for c in cases] == ["unter", "lesen"]
    # Counted apart: a word the CANDIDATE lost is a result, one neither arm
    # composed says nothing about the candidate at all.
    assert dict(dropped) == {"only_base": 1, "neither_arm": 1}
    assert cases[0].baseline_row == 40.0 and cases[0].xh == 20.0
    assert cases[0].peak > 0  # the arms differ, so the severity key is non-zero


def scoped_arm(tmp_path, name, **meta):
    path = tmp_path / f"{name}.json"
    payload = {
        "arm": name,
        **meta,
        "words": {"unter": {"registration": {"xh_px": 20.0}, "strokes": [{"points": [[0, 0], [1, 1]]}]}},
    }
    path.write_text(json.dumps(payload))
    return load_arm(path)


def test_two_arms_from_the_same_reference_pass_the_scope_check(tmp_path):
    scope = {"style": "suetterlin", "source_id": "suetterlin-1922", "settings": {"exported_at": "2026-08-14T06:02"}}
    base = scoped_arm(tmp_path, "base", **scope)
    candidate = scoped_arm(tmp_path, "cand", **scope)
    assert check_arm_scope(base, candidate, style="suetterlin", source_id="suetterlin-1922") == []
    # An arm that declares nothing cannot be checked — and is not refused for it.
    assert check_arm_scope(scoped_arm(tmp_path, "bare"), base, style="suetterlin", source_id="suetterlin-1922") == []


@pytest.mark.parametrize(
    "left, right, message",
    [
        ({"style": "suetterlin"}, {"style": "kurrent"}, "style: base says"),
        ({"source_id": "suetterlin-1922"}, {"source_id": "suetterlin-1922-abb22"}, "source_id: base says"),
        ({"fixture_root": "/a"}, {"fixture_root": "/b"}, "fixture_root: base says"),
        (
            {"settings": {"exported_at": "2026-08-14"}},
            {"settings": {"exported_at": "2026-09-01"}},
            "a re-exported root is a re-baseline",
        ),
    ],
)
def test_arms_from_different_references_are_refused(tmp_path, left, right, message):
    """The round's whole claim is that the two panels differ in the composition
    and in nothing else. Two fixture roots carry different crops, slots and
    registrations — and the round would still build, cleanly, over two things
    that were never the same measurement."""
    problems = check_arm_scope(
        scoped_arm(tmp_path, "base", **left),
        scoped_arm(tmp_path, "cand", **right),
        style="suetterlin",
        source_id="suetterlin-1922",
    )
    assert any(message in p for p in problems), problems


def test_an_arm_that_disagrees_with_the_round_itself_is_refused(tmp_path):
    problems = check_arm_scope(
        scoped_arm(tmp_path, "base", style="kurrent"),
        scoped_arm(tmp_path, "cand", style="kurrent"),
        style="suetterlin",
        source_id="suetterlin-1922",
    )
    assert len(problems) == 2  # both arms named, both wrong for this round
    assert all("the round builds 'suetterlin'" in p for p in problems)


def test_word_cases_take_the_declared_suspicion_class(tmp_path):
    root = fixture_root(tmp_path, ids=("unter",))
    base = load_arm(arm_file(tmp_path, "base", ["unter"]))
    candidate = load_arm(arm_file(tmp_path, "cand", ["unter"], dy=0.1))
    cases = word_cases(root, base, candidate, strata={"unter": "naht"})
    assert cases[0].stratum == "naht"


def test_a_word_screen_shares_one_crop_and_inks_both_arms():
    """One image, one window, two panels — the shared frame is what keeps the
    comparison blind, and the ink is what makes stroke weight judgeable."""
    case = word_case()
    item, window = render_word_item("S001", case, [SIDE_BASE, SIDE_CANDIDATE], zoom=2, pad_xh=0.4)
    assert set(item) == {"id", "w", "h", "img", "panels"}
    assert [sorted(panel) for panel in item["panels"]] == [["fills", "strokes", "widths"]] * 2
    assert item["panels"][0]["strokes"] != item["panels"][1]["strokes"]
    # The stroke width reaches the screen in panel pixels: 0.15 xh · 20 px · 2×.
    assert item["panels"][0]["widths"] == [pytest.approx(6.0)]
    assert base64.b64decode(item["img"])[:8] == b"\x89PNG\r\n\x1a\n"
    assert window[2] - window[0] > 0 and window[3] - window[1] > 0


def test_both_panels_of_a_word_screen_are_cut_from_the_SAME_window():
    """Separate windows would give the sides different pixel dimensions — the
    tell §8 rules out, and here it would also change the apparent letter size."""
    case = word_case()
    forward, window_a = render_word_item("S001", case, [SIDE_BASE, SIDE_CANDIDATE], zoom=2, pad_xh=0.4)
    mirrored, window_b = render_word_item("R01", case, [SIDE_CANDIDATE, SIDE_BASE], zoom=2, pad_xh=0.4)
    assert window_a == window_b
    assert (forward["w"], forward["h"], forward["img"]) == (mirrored["w"], mirrored["h"], mirrored["img"])
    assert forward["panels"][0] == mirrored["panels"][1]  # the same arm, the other side


def test_clipped_words_names_a_composition_that_runs_past_its_own_crop():
    """§3.4 with a word-sized failure: the crop IS the frozen fixture rect, so
    nothing can be padded into existence beyond it — a composition that overruns
    it is shown truncated and the judge would be asked about writing they cannot
    see. Reported by name rather than quietly drawn."""
    inside = word_case("unter")
    outside = word_case("weit", **{SIDE_CANDIDATE: arm_word(tx=400.0)})
    assert clipped_words([inside], 0.4) == []
    assert clipped_words([inside, outside], 0.4) == ["weit"]


def word_round(n=60, repeats=6, strata=None, seed=4711):
    # 60 words, because a repeat may only be drawn from a screen that still has
    # `min_gap + REPEAT_JITTER` room after it — the same arithmetic that decides
    # how many repeats a real 63-word round can place.
    cases = [
        WordCase(
            entry_id=f"w{i}",
            text=f"w{i}",
            crop=np.zeros((40, 80), dtype=np.uint8),
            baseline_row=30.0,
            xh=20.0,
            arms={SIDE_BASE: arm_word(), SIDE_CANDIDATE: arm_word(dy=0.02 * i)},
            peak=0.02 * i,
            stratum=(strata or {}).get(f"w{i}", "-"),
        )
        for i in range(n)
    ]
    args = parse_args(
        ["--round", "4", "--word-arms", "a.json", "b.json", "--repeats", str(repeats), "--zoom", "1", "--bands", "5"]
    )
    return build_word(cases, args, random.Random(seed))


def test_a_word_round_mirrors_its_repeats_and_says_so_only_in_the_key():
    """The identical screen could be answered with „I picked left last time";
    mirrored, the verdict has to be made about the writing again — and a
    systematic side preference then shows up as disagreement instead of hiding
    inside the agreement rate (§8)."""
    items, key, _reserve, report = word_round()
    by_uid = {entry["uid"]: entry for entry in key}
    repeats = [entry for entry in key if entry["repeat_of"]]
    assert repeats and report["n_repeats"] == len(repeats)
    for entry in repeats:
        first = by_uid[entry["repeat_of"]]
        assert entry["order"] == list(reversed(first["order"]))
        assert entry["mirrored"] is True and first["mirrored"] is False
    # Nothing in the drawn payload says which panel is which.
    assert all(set(item) == {"id", "w", "h", "img", "panels"} for item in items)


def test_word_repeats_are_dealt_over_the_suspicion_classes():
    """The construction lesson §3.2 wrote down after round 01 and then failed to
    apply twice: repeats drawn by frequency measure whatever is common, and the
    classes the round is about end up with one pair or none."""
    strata = {f"w{i}": ["naht", "zickzack", "breite"][i % 3] for i in range(60)}
    _items, key, _reserve, report = word_round(strata=strata, repeats=6)
    assert set(report["strata"]) == {"naht", "zickzack", "breite"}
    assert report["n_repeats"] == 6


def test_without_declared_classes_the_severity_bands_stand_in():
    _items, key, _reserve, report = word_round()
    assert {entry["stratum"] for entry in key} <= {f"band-{i}" for i in range(5)}
    assert len(report["strata"]) > 1


def test_pick_word_repeats_leaves_room_for_the_gap_it_promises():
    cases = [
        WordCase(f"w{i}", f"w{i}", np.zeros((4, 4), np.uint8), 2.0, 2.0, {}, peak=0.0, stratum="a", uid=f"S{i:03d}")
        for i in range(40)
    ]
    picks = pick_word_repeats(cases, n_repeats=99, min_gap=5, exclude=(), rng=random.Random(1))
    positions = {case.uid: i for i, case in enumerate(cases)}
    assert picks and all(positions[p.uid] < 40 - 5 - REPEAT_JITTER for p in picks)
    # Exhausted rather than raising: a round with too few repeats has to be
    # visible as such, and the builder says so out loud.
    assert len(picks) == 10
    assert (
        pick_word_repeats(cases, n_repeats=3, min_gap=5, exclude=(f"w{i}" for i in range(40)), rng=random.Random(1))
        == []
    )


def test_a_word_round_is_reproducible_from_the_seed():
    """Sides, sequence and repeats all come out of one seeded generator, so a
    round can be rebuilt exactly from its stamp."""
    first = [(e["uid"], e["entry"], tuple(e["order"] or ())) for e in word_round(seed=4711)[1]]
    again = [(e["uid"], e["entry"], tuple(e["order"] or ())) for e in word_round(seed=4711)[1]]
    other = [(e["uid"], e["entry"], tuple(e["order"] or ())) for e in word_round(seed=4712)[1]]
    assert first == again
    assert other != first


def test_the_sides_are_drawn_from_the_seed_and_not_all_the_same():
    _items, key, _reserve, _report = word_round()
    orders = Counter(tuple(entry["order"]) for entry in key if not entry["repeat_of"])
    assert set(orders) == {(SIDE_BASE, SIDE_CANDIDATE), (SIDE_CANDIDATE, SIDE_BASE)}
    # A judge who quietly prefers one panel spreads that bias over both arms.
    assert min(orders.values()) >= 15


def test_the_slim_key_of_a_word_round_carries_the_entry_and_its_class():
    """What a uid MEANS may be archived; what it measured may not. The class
    travels because a per-class reading of the verdict is part of the plan."""
    _items, key, _reserve, _report = word_round(strata={f"w{i}": "naht" for i in range(60)})
    slim = slim_key(key)
    assert set(slim[0]) == {"uid", "entry", "text", "stratum", "repeat_of"}
    assert "arm_gap" not in slim[0] and "rank" not in slim[0]


def test_parse_args_gives_the_word_mode_its_own_zoom_and_repeat_gap():
    """A word set is a quarter the size of a letter round and its crops four
    times the pixels, so two defaults follow the mode rather than the flag."""
    word = parse_args(["--round", "4", "--word-arms", "a.json", "b.json"])
    letter = parse_args(["--round", "2"])
    assert (word.zoom, word.min_repeat_gap) == (WORD_ZOOM, WORD_MIN_REPEAT_GAP)
    assert (letter.zoom, letter.min_repeat_gap) == (4, 40)
    # The letter default excludes the capital S by GLYPH key; in a word round
    # the same list would name a fixture entry.
    assert word.repeat_exclude == [] and letter.repeat_exclude == ["S"]
    assert parse_args(["--round", "4", "--word-arms", "a.json", "b.json", "--zoom", "3"]).zoom == 3


def test_the_stamp_of_a_word_round_names_the_arms_it_drew(tmp_path):
    args = parse_args(["--round", "4", "--word-arms", str(tmp_path / "a.json"), str(tmp_path / "b.json")])
    arms = [{"side": SIDE_BASE, "name": "Basis", "sha256_16": "abc"}]
    stamp = provenance(args, mode="word", seed=1, counts={}, repeats={}, api_used=False, arms=arms)
    assert stamp["arms"] == arms
    assert stamp["inputs"]["word_arms"] == [str(tmp_path / "a.json"), str(tmp_path / "b.json")]
    assert stamp["inputs"]["fixtures"] is not None
    assert json.dumps(stamp)  # the stamp is written as JSON, so it has to be serialisable
