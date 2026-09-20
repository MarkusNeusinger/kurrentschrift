"""The Span-Zuordner's pure half: matching, run compression, and the checked field.

Everything here runs without a fixture root, a strip or a network. The heavy
part of the assigner is the seed — a composition registered on real ink — and
that is exactly the part `tools.eigenhand.spans` keeps behind one function, so
the three rules worth pinning can be tested on geometry a reader can see:

* the matching rule really is monotone where it claims to be, and the control
  really is not (`TestMatching`);
* the run compression is the follower's own, sample for sample (`TestRuns`) —
  the §14 round compares the two assignments, so a differently-cut version of
  the same labels would make the comparison meaningless;
* boundaries are refused rather than written where the strokes were re-cut
  underneath them (`TestFlatSpans`), which is the one failure
  `core.eigenhand.pfad` cannot see: every index is still well-formed.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from core.eigenhand.pfad import AUTHORED, SPAN_AUTO, check_paths
from tools.eigenhand.spans import (
    DEFAULT_WOBBLE_XH,
    METHODS,
    crop_points,
    flat_spans,
    label_strokes,
    match_seed,
    runs_of,
    seed_distance_xh,
    wobbled,
)


# A seed that walks out along y = 0 and comes back over itself — the shape the
# order constraint exists for. Two slots, the second one passing within a
# hundredth of an x-height of the first.
LOOPING_SEED = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
LOOPING_SLOTS = np.array([0, 0, 0, 1, 1])


class TestMatching:
    def test_a_straight_bahn_over_a_straight_seed_takes_the_slots_in_order(self):
        seed = np.array([[float(x), 0.0] for x in range(6)])
        slots = np.array([0, 0, 0, 1, 1, 1])
        drawn = [np.array([[float(x), 0.02] for x in range(6)])]
        for method in METHODS:
            labels = label_strokes(drawn, seed, slots, method=method)
            assert labels[0].tolist() == [0, 0, 0, 1, 1, 1], method

    def test_the_standard_rule_never_walks_the_seed_backwards(self):
        # The contract of `dtw`, and the whole reason it exists: a sample that
        # lies near an earlier letter cannot be given that letter once the
        # stroke has moved past it.
        drawn = np.array([[0.0, 0.01], [1.0, 0.01], [2.0, 0.01], [1.0, 0.99], [0.9, 0.02]])
        matched = match_seed(drawn, LOOPING_SEED, method="dtw")
        assert np.all(np.diff(matched) >= 0)

    def test_the_control_does_walk_it_backwards(self):
        # Stated as its own test rather than as a remark on the one above: if
        # `nearest` were monotone here too, the round would be comparing a rule
        # against itself and the number would mean nothing.
        drawn = np.array([[0.0, 0.01], [1.0, 0.01], [2.0, 0.01], [1.0, 0.99], [0.9, 0.02]])
        matched = match_seed(drawn, LOOPING_SEED, method="nearest")
        assert not np.all(np.diff(matched) >= 0)

    def test_an_unknown_rule_is_refused_rather_than_falling_back(self):
        with pytest.raises(ValueError, match="unknown matching rule"):
            match_seed(np.zeros((2, 2)), LOOPING_SEED, method="whatever")

    def test_an_empty_bahn_and_an_empty_seed_are_answers_not_crashes(self):
        for method in METHODS:
            assert match_seed(np.zeros((0, 2)), LOOPING_SEED, method=method).tolist() == []
            assert match_seed(np.zeros((3, 2)), np.zeros((0, 2)), method=method).tolist() == [0, 0, 0]

    def test_the_seed_distance_is_read_in_x_heights(self):
        seed = np.array([[0.0, 0.0], [10.0, 0.0]])
        drawn = np.array([[0.0, 5.0], [10.0, 0.0]])
        readings = seed_distance_xh(drawn, seed, np.array([0, 1]), xh_px=10.0)
        assert readings.tolist() == [0.5, 0.0]


class TestCropPoints:
    def test_it_is_the_exact_inverse_of_what_the_follower_maps(self):
        # The one arithmetic the whole assignment stands on: a Bahn stored in
        # word units has to land back on the pixels it was drawn over, or every
        # boundary is placed against the wrong ink.
        from tools.eigenhand.pfad import _crop_px

        registration = {"tx": 12.0, "ty": -3.0, "baseline_row": 90.0}
        stroke = [[0.0, 0.0], [1.5, 1.0], [3.0, -0.4]]
        assert np.allclose(crop_points(stroke, registration, 31.0), _crop_px(stroke, registration, 31.0))


class TestRuns:
    def test_the_compression_is_the_followers_own_sample_for_sample(self):
        # Pinned against the original rather than described: the §14 round
        # compares this module's assignment with the follower's, and two
        # different cuts of the same labels would look like a disagreement
        # about letters.
        from tools.pairlab.tintenpfad import spans_of

        rng = np.random.default_rng(20260920)
        for _ in range(20):
            labels = [rng.integers(-1, 4, size=int(rng.integers(1, 40))) for _ in range(int(rng.integers(1, 4)))]
            assert runs_of(labels) == spans_of(labels)

    def test_a_connector_inherits_the_nearest_letter(self):
        assert runs_of([np.array([0, 0, -1, -1, 1, 1])]) == [[[0, 0, 2], [1, 3, 5]]]

    def test_a_stroke_the_seed_never_labelled_stays_unlabelled(self):
        assert runs_of([np.array([-1, -1, -1])]) == [[[-1, 0, 2]]]


class TestFlatSpans:
    def test_it_produces_the_field_the_api_checks(self):
        strokes = [[[0.0, 0.0], [0.5, 1.0], [1.0, 0.0]]]
        spans = flat_spans([[[0, 0, 1], [1, 2, 2]]], strokes)
        assert spans == [
            {"stroke": 0, "slot": 0, "first": 0, "last": 1, "herkunft": SPAN_AUTO},
            {"stroke": 0, "slot": 1, "first": 2, "last": 2, "herkunft": SPAN_AUTO},
        ]
        entry = {
            "box_index": 0,
            "word": "lesen",
            "strokes": strokes,
            "registration_px": {"tx": 40.0, "ty": 0.0, "baseline_row": 240.0},
            "xh_px": 120.0,
            "verfahren": "tintenpfad",
            "letter_spans": spans,
        }
        row = {
            "cut_mm": [10.0, 20.0, 200.0, 60.0],
            "band_mm": {"asc_top": 24.0, "waist": 32.0, "baseline": 44.0, "desc_bot": 56.0},
            "boxes": [{"word": "lesen", "x0_mm": 15.0, "x1_mm": 45.0}],
        }
        assert check_paths([entry], row, 1900, 400, ["lesen"], 2)[0]["letter_spans"] == spans

    def test_auto_is_not_a_default_here_but_the_only_value_on_offer(self):
        # An `authored` boundary minted by the assigner would pass the field
        # check and then be protected forever by `displaced_authored` — a guess
        # frozen as ground truth, and handed straight back to this very
        # assigner as training material. So there is no knob, and the signature
        # is asserted rather than described (found in review, this PR).
        spans = flat_spans([[[0, 0, 1]]], [[[0.0, 0.0], [1.0, 1.0]]])
        assert spans and [span["herkunft"] for span in spans] == [SPAN_AUTO] != [AUTHORED]
        assert list(inspect.signature(flat_spans).parameters) == ["nested", "strokes"]

    def test_a_stretch_the_seed_never_labelled_is_dropped_not_written_as_minus_one(self):
        # Slot −1 means „no letter here"; stored, it would read as letter
        # number minus one in every consumer.
        assert flat_spans([[[-1, 0, 1], [3, 2, 2]]], [[[0.0, 0.0]] * 3]) == [
            {"stroke": 0, "slot": 3, "first": 2, "last": 2, "herkunft": SPAN_AUTO}
        ]
        assert flat_spans([[[-1, 0, 2]]], [[[0.0, 0.0]] * 3]) is None

    @pytest.mark.parametrize(
        "nested",
        [
            pytest.param([[[0, 0, 1]]], id="the stroke is longer than the labels cover"),
            pytest.param([[[0, 0, 1], [1, 3, 4]]], id="a sample belongs to no span at all"),
            pytest.param([[[0, 0, 4]], [[0, 0, 0]]], id="one span list too many"),
        ],
    )
    def test_boundaries_that_no_longer_describe_these_strokes_are_refused(self, nested):
        # The failure `core.eigenhand.pfad._checked_spans` cannot see: after
        # `cap_word_strokes` downsamples a Bahn every index is still in range
        # and points at the wrong ink. Both producers cover a stroke sample for
        # sample, so anything less means the strokes were re-cut underneath.
        assert flat_spans(nested, [[[0.0, 0.0]] * 5]) is None

    def test_a_box_past_the_stored_bound_gives_its_boundaries_up_whole(self):
        # The bound belongs to the stored field and is answered here, once: a
        # box over it would otherwise take the whole Fassung's push down with a
        # 422 over boundaries nobody looked at, and an `auto` boundary is a
        # derivation the next run makes again.
        from core.eigenhand.pfad import MAX_SPANS

        alternating = [[[slot % 2, slot, slot] for slot in range(MAX_SPANS + 1)]]
        assert flat_spans(alternating, [[[0.0, 0.0]] * (MAX_SPANS + 1)]) is None


class TestAssignReasons:
    """What a REFUSAL says. A reason is read instead of opening the strip.

    So naming the wrong one sends the operator to the wrong place: the stored
    bound is a bookkeeping limit, a seed that named no letter is a composition
    question, and neither of them is re-cut ink.
    """

    def _reason(self, monkeypatch, seed_xy, seed_slot, strokes) -> str:
        import tools.eigenhand.spans as module

        monkeypatch.setattr(module, "seed_for_case", lambda *_a: (seed_xy, np.asarray(seed_slot), 1.0))
        spans, diag = module.assign(None, strokes, {"tx": 0.0, "ty": 0.0, "baseline_row": 0.0}, 1.0, None)
        assert spans is None
        return diag["reason"]

    def test_a_seed_that_labelled_nothing_here_is_not_reported_as_re_cut_ink(self, monkeypatch):
        # The seed HAS letters — just none of them anywhere near this Bahn, so
        # every sample took a connector. Coverage was perfect; saying it was not
        # would point at `cap_word_strokes`, which had nothing to do with it.
        seed = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [90.0, 90.0]])
        reason = self._reason(monkeypatch, seed, [-1, -1, -1, 0], [[[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]]])
        assert reason == "the seed labelled no letter anywhere on this Bahn"

    def test_a_box_over_the_stored_bound_says_so_by_the_number(self, monkeypatch):
        from core.eigenhand.pfad import MAX_SPANS

        walk = [[float(step), 0.0] for step in range(MAX_SPANS + 1)]
        seed = np.asarray(walk)
        reason = self._reason(monkeypatch, seed, [step % 2 for step in range(MAX_SPANS + 1)], [walk])
        assert reason == f"{MAX_SPANS + 1} boundaries — at most {MAX_SPANS} are stored per box"

    def test_a_bahn_without_a_sample_is_its_own_finding(self, monkeypatch):
        assert self._reason(monkeypatch, np.zeros((2, 2)), [0, 1], [[]]) == "the Bahn carries no samples"


class TestCheckCli:
    def test_the_round_carries_the_house_root_precondition(self, monkeypatch):
        # Every entry point that reads a frozen root takes `--expect-root` and
        # enforces it BEFORE the first measurement. The roots are gitignored, so
        # a re-export leaves no diff: without the precondition the command
        # quoted in a §14 entry would quietly answer with a different set of
        # numbers instead of aborting (`werkzeuge.md`, „Die Wurzel-Angabe jedes
        # Messlaufs"; Copilot review, this PR).
        import tools.eigenhand.spans as module

        seen: dict = {}
        monkeypatch.setattr(module, "check", lambda *_a, **kwargs: seen.update(kwargs) or {"arms": {}})
        assert module.main(["--check", "--expect-root", "5d4556b87573"]) == 0
        assert seen["expect_root"] == "5d4556b87573"

    def test_measuring_is_the_only_thing_this_module_does_from_the_command_line(self):
        # The assigner itself runs from `pfad --spans`; a bare invocation here
        # must not look like it assigned anything.
        with pytest.raises(SystemExit):
            from tools.eigenhand.spans import main

            main([])


class TestWobble:
    def test_it_is_deterministic_in_the_word(self):
        stroke = [np.column_stack([np.linspace(0.0, 60.0, 40), np.zeros(40)])]
        first = wobbled(stroke, 30.0, DEFAULT_WOBBLE_XH, "unter")
        assert np.allclose(first[0], wobbled(stroke, 30.0, DEFAULT_WOBBLE_XH, "unter")[0])
        assert not np.allclose(first[0], wobbled(stroke, 30.0, DEFAULT_WOBBLE_XH, "die")[0])

    def test_the_amplitude_is_what_the_typical_sample_is_pushed_by(self):
        # Scaled on the median displacement, not the peak — an arm described as
        # 0.15 xh has to have moved the Bahn by 0.15 xh, or the entry quotes a
        # stronger simulation than the one that ran.
        stroke = [np.column_stack([np.linspace(0.0, 60.0, 200), np.zeros(200)])]
        moved = wobbled(stroke, 30.0, 0.15, "Galoppieren")[0]
        offsets = np.hypot(*(moved - stroke[0]).T) / 30.0
        assert float(np.median(offsets)) == pytest.approx(0.15, abs=1e-9)

    def test_a_stroke_too_short_to_drift_is_handed_back_unchanged(self):
        stroke = [np.array([[1.0, 2.0]])]
        assert wobbled(stroke, 30.0, 0.15, "er")[0].tolist() == [[1.0, 2.0]]
