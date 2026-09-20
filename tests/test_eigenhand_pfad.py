"""The Streifen-Pfad's pure half: where a word box sits, and what a path may be.

Four things are tested here. Two are arithmetic the server and the local
follower must agree on to the pixel: the frame a word box spans inside a stored
strip (`frame_for_box`), and the refusals that keep a pushed path from being
stored against the wrong ink (`check_paths`). The third is which words a strip
follow can even take on — the ductus seed it composes with, and the two ways
that seam used to refuse the author's own hand (`TestDuctusSeed`). The fourth
is the rule that a hand-drawn path outranks a followed one
(`displaced_authored`, `TestAuthoredRule`). Since the per-box write there is a
fifth: the content token the two write doors are held against (`pfad_etag`,
`TestPfadEtag`).
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest

from core.eigenhand import tintentreue
from core.eigenhand.pfad import (
    AUTHORED,
    FIELD_PATH,
    FIELD_SPANS,
    MAX_DETAIL,
    MAX_SLOT,
    MAX_UNIT,
    PFAD_FORMAT,
    SKIP_AND_SPAN_FORMAT,
    SKIP_REASONS,
    SUPPORTED_FORMATS,
    check_paths,
    displaced_authored,
    format_of_entries,
    frame_for_box,
    frames_of_row,
    nominal_xh_px,
    pfad_etag,
    push_body,
)
from tools.eigenhand.apiclient import StaleRead


# The token a stubbed read hands out. Opaque on purpose — the tool has to pass
# it through untouched, and a value that looked computable would invite a test
# that recomputes it instead of checking that it travelled.
STUB_TAG = '"the-list-this-run-read"'

# 10 px per mm, a strip 190 mm wide cut at x 10..200 and y 20..60.
SCALE = 10.0
WIDTH_PX = 1900
HEIGHT_PX = 400
ORIGIN_MM = [10.0, 20.0]

ROW = {
    "strip": "S0001",
    "cut_mm": [10.0, 20.0, 200.0, 60.0],
    "band_mm": {"asc_top": 24.0, "waist": 32.0, "baseline": 44.0, "desc_bot": 56.0},
    "boxes": [{"word": "lesen", "x0_mm": 15.0, "x1_mm": 45.0}, {"word": "das", "x0_mm": 55.0, "x1_mm": 75.0}],
}


def _frame(index: int = 0, **overrides):
    row = {**ROW, **overrides}
    return frame_for_box(row, ORIGIN_MM, WIDTH_PX, HEIGHT_PX, index)


def _stub_run(monkeypatch, *, fresh: list[dict], stored: list[dict]) -> None:
    """Stub everything around the merge — fixtures, listing, follower, network.

    What is left running is `main` plus `_merged`, so an assertion reads
    exactly the list the tool would have pushed, without a fixture root or a
    network.
    """
    from tools.eigenhand import pfad as tool

    merged = tool._merged
    monkeypatch.setattr(tool, "api_base", lambda _api: "https://example.invalid")
    monkeypatch.setattr(tool, "admin_token", lambda _token: "token")
    monkeypatch.setattr(tool, "style_of_hand", lambda _hand: "suetterlin")
    monkeypatch.setattr(tool, "_style_constants", lambda _style: {"manifest": {}, "source_id": "suetterlin-1922"})
    monkeypatch.setattr(tool, "LiveDuctus", lambda *_a: SimpleNamespace(have=set()))
    monkeypatch.setattr(
        tool, "_strip_rows", lambda *_a: [{"strip": "S0001", "fassung": "F01", "sheet": "B0001", "row_index": 0}]
    )
    monkeypatch.setattr(tool, "follow_row", lambda *_a: fresh)
    # The read hands its `ETag` back beside the body, the way the real client
    # does: the push is guarded by the token of THIS read, so a stub that
    # answered a body alone would make the tool's push untestable.
    monkeypatch.setattr(
        tool, "_merged", lambda *args, **kwargs: merged(*args, **kwargs, _get=lambda *_a: ({"pfade": stored}, STUB_TAG))
    )


def _dry_run(tmp_path, monkeypatch, *, fresh: list[dict], stored: list[dict], argv: list[str]) -> list[dict]:
    """Run the tool's dry path over a stubbed API and hand back the filed body."""
    from tools.eigenhand import pfad as tool

    _stub_run(monkeypatch, fresh=fresh, stored=stored)
    monkeypatch.setattr(tool, "request_json", lambda *_a, **_k: pytest.fail("a dry run must not write"))

    out = tmp_path / "pfade.json"
    assert tool.main([*argv, "--out", str(out)]) == 0
    return json.loads(out.read_text())["pfade"]


def _kartei_with(entries: list[dict]) -> dict:
    """A Kartei that has already pulled these Bahnen for S0001/F01.

    The shape `tools.eigenhand.pull --pfade` writes — built through the real
    `pfad_record`, so a change to the envelope shows up here rather than
    silently making the refusal below untestable.
    """
    from tools.eigenhand.kartei import pfad_record

    return {
        "format": 1,
        "hand": "mn-suetterlin",
        "style": "suetterlin",
        "sheets": {},
        "strips": {"S0001": {"fassungen": [{"id": "F01", "pfade": pfad_record(entries, 1, "2026-09-20")}]}},
        "redo": [],
    }


def _apply_run(
    monkeypatch, *, fresh: list[dict], stored: list[dict], argv: list[str], archived: list[dict] | None = None
) -> tuple[str, dict]:
    """Run the tool's `--apply` path over a stubbed API; the URL and DOCUMENT it PUT.

    The whole envelope, not just its entries: the declared `format` is part of
    what a push is, and a merged body carrying entries this run did not produce
    has to be declared for what it IS (review, PR #639).

    `archived` is what this machine's Kartei holds — the condition
    `--replace-authored` is held against since author decision B.
    """
    from tools.eigenhand import pfad as tool

    _stub_run(monkeypatch, fresh=fresh, stored=stored)
    monkeypatch.setattr(tool, "load_kartei", lambda _hand: _kartei_with(archived or []))
    sent: dict = {}

    def _put(method: str, url: str, token: str, payload: dict | None = None, *, if_match=None):
        assert method == "PUT", method
        sent["url"], sent["payload"], sent["if_match"] = url, payload, if_match
        return payload

    monkeypatch.setattr(tool, "request_json", _put)
    assert tool.main([*argv, "--apply"]) == 0
    assert sent["payload"]["format"] in SUPPORTED_FORMATS
    # Every push names the list its merge was made on. The server demands it,
    # and a merge assembled from one read and pushed against another is the
    # lost update the token exists to refuse — so this is checked on every run
    # here rather than in one test of its own.
    assert sent["if_match"] == STUB_TAG
    return sent["url"], sent["payload"]


def _path(**overrides) -> dict:
    return {
        "box_index": 0,
        "word": "lesen",
        "strokes": [[[0.0, 0.0], [0.5, 1.0], [1.0, 0.0]]],
        "registration_px": {"tx": 40.0, "ty": 0.0, "baseline_row": 240.0},
        "xh_px": 120.0,
        "verfahren": "tintenpfad",
        **overrides,
    }


def _span(**overrides) -> dict:
    """One letter boundary of `_path`'s three-point stroke."""
    return {"stroke": 0, "slot": 0, "first": 0, "last": 2, "herkunft": "auto", **overrides}


def _skip(**overrides) -> dict:
    """A box that carries no path, and says why (format 2)."""
    return {
        "box_index": 0,
        "word": "lesen",
        "status": "skipped",
        "grund": "unauthored",
        "strokes": [],
        "verfahren": "tintenpfad",
        **overrides,
    }


# One followed word as `tools.pairlab.tintenpfad.follow_case` hands it back —
# registered against the CROP, with the diagnosis block the projection reads.
# `letter_spans` sits in the free `meta` because that is where the follower
# still puts it; what the tool does with it is the assertion, not this shape.
_INFO = {
    "strokes": [[[0.0, 0.0], [1.0, 1.0]]],
    "registration_px": {"tx": 3.0, "ty": -1.0, "baseline_row": 240.0},
    "xh_px": 118.0,
    "meta": {
        "letter_spans": [[[0, 0, 1]]],
        "tintenpfad": {
            "runs": 2,
            "strands": 1,
            "jumps": 0,
            "hairpins": 0,
            "paper_lifts": 1,
            "ink_unvisited_share": 0.02,
        },
    },
}


class TestFrameForBox:
    """The nominal frame — printed ruling, strip pixels, never the word crop's."""

    def test_the_lineature_comes_out_in_strip_pixels_off_the_printed_band(self):
        frame = _frame()
        # baseline 44 mm, waist 32 mm, crop starting at 20 mm, 10 px/mm.
        assert frame["baseline_row"] == pytest.approx(240.0)
        assert frame["waist_row"] == pytest.approx(120.0)
        assert frame["xh_px"] == pytest.approx(120.0)
        assert frame["px_per_mm"] == pytest.approx(SCALE)

    def test_the_rectangle_is_the_word_crops_own_padded_and_full_height(self):
        # The same arithmetic the word-crop route cuts with: 1 mm of padding on
        # both sides, the full strip height, clamped to the strip.
        assert _frame(0)["rect_px"] == [40, 0, 360, HEIGHT_PX]
        assert _frame(1)["rect_px"] == [440, 0, 660, HEIGHT_PX]
        assert _frame(1)["word"] == "das"

    def test_a_box_the_row_does_not_have_is_refused(self):
        with pytest.raises(ValueError, match="there is no box 2"):
            _frame(2)

    def test_a_bogen_without_ruling_or_cut_geometry_is_refused_not_guessed(self):
        with pytest.raises(ValueError, match="band_mm"):
            _frame(0, band_mm={"asc_top": 24.0})
        with pytest.raises(ValueError, match="Schnittband"):
            _frame(0, cut_mm=[])

    def test_a_row_whose_geometry_is_missing_yields_no_frames_rather_than_failing(self):
        # The listing must not break over an old Bogen: a strip without
        # rectangles simply has none to offer.
        assert frames_of_row({**ROW, "cut_mm": []}, ORIGIN_MM, WIDTH_PX, HEIGHT_PX) is None
        assert len(frames_of_row(ROW, ORIGIN_MM, WIDTH_PX, HEIGHT_PX)) == 2


class TestCheckPaths:
    """What a pushed path has to be before it is stored against a strip."""

    @staticmethod
    def _check(paths, **kwargs):
        return check_paths(paths, ROW, WIDTH_PX, HEIGHT_PX, **kwargs)

    def test_a_well_formed_path_survives_and_carries_its_provenance(self):
        stored = self._check([_path(erzeugt_am="2026-09-12", flecken_n=3, konfiguration={"rail": "tentfit"})])
        assert len(stored) == 1
        assert stored[0]["verfahren"] == "tintenpfad"
        assert stored[0]["erzeugt_am"] == "2026-09-12"
        assert stored[0]["flecken_n"] == 3
        assert stored[0]["konfiguration"] == {"rail": "tentfit"}
        assert stored[0]["registration_px"] == {"tx": 40.0, "ty": 0.0, "baseline_row": 240.0}

    def test_the_stored_list_comes_back_in_box_order(self):
        second = _path(box_index=1, word="das", registration_px={"tx": 440.0, "ty": 0.0, "baseline_row": 240.0})
        assert [p["box_index"] for p in self._check([second, _path()])] == [0, 1]

    def test_a_box_that_is_not_on_this_row_is_refused(self):
        with pytest.raises(ValueError, match="not a box of this row"):
            self._check([_path(box_index=7)])

    def test_two_paths_for_one_box_are_refused(self):
        with pytest.raises(ValueError, match="two paths"):
            self._check([_path(), _path()])

    def test_a_word_that_contradicts_the_printed_box_is_refused(self):
        with pytest.raises(ValueError, match="the printed box carries"):
            self._check([_path(word="Galopp")])

    def test_a_word_that_contradicts_the_frozen_plan_is_refused(self):
        # The plan is the strip's identity: a layout that somehow disagreed
        # with it must not put a path under a word the strip never held.
        with pytest.raises(ValueError, match="the frozen plan says"):
            self._check([_path()], words=["Galopp", "das"])
        assert self._check([_path()], words=["lesen", "das"])

    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"strokes": []}, "non-empty"),
            ({"strokes": [[[0.0, 0.0]]]}, "2..4096 points"),
            ({"strokes": [[[0.0, 0.0, 1.0], [1.0, 1.0, 1.0]]]}, r"\[x, y\] pairs"),
            ({"strokes": [[[0.0, 0.0], [MAX_UNIT + 1, 1.0]]]}, "out of range"),
            ({"verfahren": ""}, "verfahren"),
            ({"erzeugt_am": "gestern"}, "ISO date"),
            # A length check let this one through and the workbench printed it
            # as provenance (Copilot review, PR #598).
            ({"erzeugt_am": "2026-99-99"}, "ISO date"),
            ({"xh_px": 0.0}, "not a scale"),
            ({"flecken_n": -1}, "flecken_n"),
        ],
    )
    def test_a_malformed_entry_is_refused_rather_than_repaired(self, overrides: dict, message: str):
        with pytest.raises(ValueError, match=message):
            self._check([_path(**overrides)])

    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"strokes": [[[0.0, 0.0], [float("nan"), 1.0]]]}, "finite"),
            ({"strokes": [[[0.0, 0.0], [float("inf"), 1.0]]]}, "finite"),
            ({"xh_px": float("nan")}, "not a scale"),
            ({"registration_px": {"tx": float("nan"), "ty": 0.0, "baseline_row": 240.0}}, "finite"),
        ],
    )
    def test_a_non_finite_number_is_refused_before_any_range_check(self, overrides: dict, message: str):
        # Every comparison against NaN is False, so a range check alone lets it
        # through — and it reaches the overlay as a NaN SVG coordinate, which
        # draws nothing and explains nothing (Copilot review, PR #598).
        with pytest.raises(ValueError, match=message):
            self._check([_path(**overrides)])

    @pytest.mark.parametrize(
        "registration",
        [
            {"tx": 99_000.0, "ty": 0.0, "baseline_row": 240.0},
            {"tx": 40.0, "ty": 0.0, "baseline_row": 99_000.0},
            {"tx": 40.0, "ty": 0.0},
            # Well inside a "fraction of the image" bound and still off the
            # strip: the allowance is x-heights, not image widths (Copilot
            # review, PR #598). xh here is 120 px, so the bound is ±240.
            {"tx": WIDTH_PX + 600.0, "ty": 0.0, "baseline_row": 240.0},
            {"tx": 40.0, "ty": 0.0, "baseline_row": HEIGHT_PX + 300.0},
        ],
    )
    def test_a_registration_that_does_not_lie_on_this_strip_is_refused(self, registration: dict):
        # The one error that would otherwise draw a perfectly well-formed path
        # over the wrong ink — silently, and forever.
        with pytest.raises(ValueError):
            self._check([_path(registration_px=registration)])

    def test_a_word_that_starts_a_little_left_of_the_strip_is_still_accepted(self):
        # A word's own origin may sit left of the ink (the composition starts
        # at the Anstrich) and a descender reaches past the cut, so the bound is
        # two x-heights of slack rather than zero.
        assert self._check([_path(registration_px={"tx": -20.0, "ty": 0.0, "baseline_row": 240.0})])
        assert self._check([_path(registration_px={"tx": float(WIDTH_PX) + 100.0, "ty": 0.0, "baseline_row": 240.0})])

    @pytest.mark.parametrize("xh", [1300.0, 240.1, 59.9, 0.5])
    def test_an_x_height_the_printed_ruling_could_not_have_is_refused(self, xh: float):
        # The row's printed band is 12 mm at 10 px/mm, so 120 px is the nominal
        # x-height and half to double it is every hand this Bogen could hold.
        with pytest.raises(ValueError, match="not a scale"):
            self._check([_path(xh_px=xh)])
        assert self._check([_path(xh_px=60.0)]) and self._check([_path(xh_px=240.0)])

    def test_an_inflated_x_height_cannot_buy_slack_for_an_off_strip_frame(self):
        # The registration slack is measured in the path's OWN x-height, so an
        # unbounded `xh_px` disabled the very check it is measured with: at a
        # declared 1300 px, `tx = 2500` on this strip passed (review of PR
        # #598). Now the x-height is refused before it can widen anything.
        off_strip = {"tx": WIDTH_PX + 600.0, "ty": 0.0, "baseline_row": 240.0}
        with pytest.raises(ValueError, match="not a scale"):
            self._check([_path(xh_px=1300.0, registration_px=off_strip)])
        # …and the honest x-height still refuses the same frame, as before.
        with pytest.raises(ValueError, match="outside the strip"):
            self._check([_path(registration_px=off_strip)])

    def test_without_a_printed_ruling_the_strip_itself_bounds_the_x_height(self):
        # An old Bogen has no band to compare against; the strip's own height
        # is then the only witness left, and it is still a bound.
        row = {**ROW, "band_mm": {}}
        assert nominal_xh_px(row, WIDTH_PX) is None
        assert nominal_xh_px(ROW, WIDTH_PX) == pytest.approx(120.0)
        assert check_paths([_path(xh_px=120.0)], row, WIDTH_PX, HEIGHT_PX)
        with pytest.raises(ValueError, match="not a scale"):
            check_paths([_path(xh_px=HEIGHT_PX * 3.0)], row, WIDTH_PX, HEIGHT_PX)

    def test_an_empty_push_is_a_reading_and_not_a_refusal(self):
        # „followed, nothing found" — the same distinction the Fleckenmaske
        # draws between an empty list and NULL.
        assert check_paths([], ROW, WIDTH_PX, HEIGHT_PX) == []

    def test_a_hand_drawn_path_is_pushed_like_any_other(self):
        # Deliberately NOT refused here: the entry-level check never sees who
        # is pushing, and the surface that lets the author draw one has to be
        # able to send it. What the word „authored" buys is protection from
        # the NEXT push, and that is stored state — `displaced_authored`.
        assert self._check([_path(verfahren=AUTHORED)])[0]["verfahren"] == AUTHORED

    def test_a_format_1_entry_keeps_exactly_the_shape_migration_0031_stored(self):
        # Stamped 1 EXPLICITLY, because the default moved with the second
        # release: what a format-1 row stores is frozen by the rows already in
        # the database and must not come back carrying format-2 keys.
        assert set(self._check([_path()], pfad_format=1)[0]) == {
            "box_index",
            "word",
            "strokes",
            "registration_px",
            "xh_px",
            "verfahren",
            "konfiguration",
            "meta",
            "erzeugt_am",
            "flecken_n",
        }


class TestFormatTwo:
    """What format 2 adds — the Skip-Eintrag and the checked Buchstabengrenzen."""

    @staticmethod
    def _check(paths, pfad_format: int = SKIP_AND_SPAN_FORMAT, **kwargs):
        return check_paths(paths, ROW, WIDTH_PX, HEIGHT_PX, pfad_format=pfad_format, **kwargs)

    def test_what_this_image_writes_is_a_subset_of_what_it_reads(self):
        # The whole design rests on this, and the next bump moves the WRITE
        # constant in a different place from the read tuple. A mismatch would
        # make the image push a number its own 409 refuses, on every run
        # (found in review, PR #639).
        assert PFAD_FORMAT in SUPPORTED_FORMATS
        assert SKIP_AND_SPAN_FORMAT in SUPPORTED_FORMATS
        assert max(SUPPORTED_FORMATS) == SKIP_AND_SPAN_FORMAT

    def test_a_skipped_box_carries_its_reason_instead_of_a_path(self):
        # The entry type author decision C asked for: no strokes, a mandatory
        # reason, registration and x-height optional — a box refused before
        # anything was registered has neither.
        stored = self._check([_skip(detail="unauthored: y")])[0]
        assert (stored["status"], stored["grund"], stored["detail"]) == ("skipped", "unauthored", "unauthored: y")
        assert stored["strokes"] == [] and stored["registration_px"] is None and stored["xh_px"] is None

    def test_a_followed_entry_says_so_rather_than_leaving_it_to_be_guessed(self):
        stored = self._check([_path()])[0]
        assert (stored["status"], stored["grund"], stored["letter_spans"]) == ("ok", None, None)

    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"grund": None}, "grund"),
            ({"grund": "keine-lust"}, "grund"),
            ({"grund": "unauthored", "strokes": [[[0.0, 0.0], [1.0, 1.0]]]}, "carries no strokes"),
            ({"status": "vielleicht"}, "status"),
            ({"detail": "x" * 201}, "detail"),
        ],
    )
    def test_a_malformed_skip_is_refused_rather_than_repaired(self, overrides: dict, message: str):
        with pytest.raises(ValueError, match=message):
            self._check([_skip(**overrides)])

    def test_every_reason_of_the_closed_list_is_accepted(self):
        # Closed on purpose: the four cases triage differently, and a free
        # string would merge them again. `other` is where a fifth one goes.
        assert [self._check([_skip(grund=grund)])[0]["grund"] for grund in SKIP_REASONS] == list(SKIP_REASONS)

    def test_a_reason_on_a_followed_path_is_refused(self):
        with pytest.raises(ValueError, match="SKIPPED"):
            self._check([_path(grund="gave_up")])

    def test_a_skip_may_not_claim_the_provenance_of_a_drawing(self):
        # `is_authored` reads `verfahren` alone, and everything downstream
        # assumes a drawing: the 409 locks the box, `pull --pfade` archives it,
        # `--replace-authored` demands it be archived first. An authored SKIP
        # would be a phantom drawing — and on an empty row `displaced_authored`
        # has nothing stored to catch it with (found in review, PR #639).
        with pytest.raises(ValueError, match="cannot claim `verfahren"):
            self._check([_skip(verfahren=AUTHORED)])

    def test_a_skip_that_does_bring_its_frame_is_still_held_to_it(self):
        # Optional is not unchecked: a registration that names another image
        # would draw the same wrong overlay whether a path hangs off it or not.
        assert self._check([_skip(registration_px={"tx": 40.0, "ty": 0.0, "baseline_row": 240.0}, xh_px=120.0)])
        with pytest.raises(ValueError, match="outside the strip"):
            self._check([_skip(registration_px={"tx": 99_000.0, "ty": 0.0, "baseline_row": 240.0}, xh_px=120.0)])

    def test_the_letter_boundaries_carry_their_own_provenance(self):
        stored = self._check([_path(letter_spans=[_span(last=1), _span(slot=1, first=2, herkunft=AUTHORED)])])[0]
        assert [span["herkunft"] for span in stored["letter_spans"]] == ["auto", AUTHORED]

    @pytest.mark.parametrize(
        ("span", "message"),
        [
            ({"last": 3}, "which has 3 point"),
            ({"stroke": 1}, "this path has 1 stroke"),
            ({"first": 2, "last": 1}, "starts at sample 2"),
            ({"herkunft": "geraten"}, "herkunft"),
            ({"slot": -1}, "non-negative integer `slot`"),
        ],
    )
    def test_a_boundary_that_does_not_fit_its_stroke_is_refused(self, span: dict, message: str):
        # The spans index the samples the FOLLOWER decoded; the entry stores the
        # CAPPED strokes (`tools.pairlab.trace.cap_word_strokes` downsamples
        # past 4096 points and thins past 128 runs). Nothing checked the two
        # against each other, and a desynchronised span is well-formed in every
        # number it carries.
        with pytest.raises(ValueError, match=message):
            self._check([_path(letter_spans=[_span(**span)])])

    def test_a_skipped_box_has_no_samples_to_index(self):
        with pytest.raises(ValueError, match="0 stroke"):
            self._check([_skip(letter_spans=[_span()])])

    def test_two_boundaries_may_not_claim_the_same_ink(self):
        # Held against each other, not only against their stroke: one sample
        # belongs to one letter, and two boundaries over the same samples are
        # well-formed in every number they carry — they would reach the
        # Span-Zuordner's training set as ground truth (review, PR #639).
        with pytest.raises(ValueError, match="both claim sample"):
            self._check([_path(letter_spans=[_span(), _span()])])
        with pytest.raises(ValueError, match="both claim sample\\(s\\) 1..1 of stroke 0"):
            self._check([_path(letter_spans=[_span(slot=0, first=0, last=1), _span(slot=1, first=1, last=2)])])
        # …touching is not overlapping: `spans_of` hands back gapless spans.
        assert self._check([_path(letter_spans=[_span(slot=0, first=0, last=1), _span(slot=1, first=2, last=2)])])

    def test_one_slot_may_be_written_in_two_strokes(self):
        # The i-dot and the umlaut: one letter, two pen-downs. Refusing a
        # repeated slot outright would refuse every marked letter there is.
        two_strokes = [[[0.0, 0.0], [0.5, 0.5], [1.0, 0.0]], [[0.4, 1.4], [0.5, 1.5]]]
        stored = self._check([_path(strokes=two_strokes, letter_spans=[_span(), _span(stroke=1, first=0, last=1)])])[0]
        assert [span["stroke"] for span in stored["letter_spans"]] == [0, 1]

    def test_a_slot_number_no_word_could_have_is_refused(self):
        # The one bound with nothing in the entry to hold it: `stroke`, `first`
        # and `last` are bounded by the stroke they index, `slot` is not — and
        # the wire capped it while core did not, so the two layers refused
        # different things (review, PR #639).
        with pytest.raises(ValueError, match=f"at most {MAX_SLOT}"):
            self._check([_path(letter_spans=[_span(slot=MAX_SLOT + 1)])])

    @pytest.mark.parametrize("field", ["status", "grund", "detail", "letter_spans"])
    def test_a_format_2_field_pushed_under_format_1_is_refused(self, field: str):
        # A row is stamped with what it was pushed under, so a cell carrying
        # fields its number does not know is the mislabelling the stored marker
        # exists to prevent — one layer further down.
        entry = _path(**{field: {"status": "ok", "grund": "other", "detail": "x", "letter_spans": [_span()]}[field]})
        with pytest.raises(ValueError, match=f"`{field}`"):
            self._check([entry], pfad_format=1)

    def test_a_push_is_declared_by_what_it_carries_not_by_a_constant(self):
        # Both writers push entries they did not produce — the merge keeps the
        # boxes a run did not follow and carries the author's boundaries onto
        # its own result — so a declaration read off `PFAD_FORMAT` would be
        # refused by the content rule above (review, PR #639).
        assert format_of_entries([]) == PFAD_FORMAT
        assert format_of_entries([_path()]) == PFAD_FORMAT
        assert format_of_entries([_path(), _skip(box_index=1, word="das")]) == SKIP_AND_SPAN_FORMAT
        assert format_of_entries([_path(letter_spans=[_span()])]) == SKIP_AND_SPAN_FORMAT
        # And a row cannot quietly slide back down: everything `check_paths`
        # accepts under format 2 comes out carrying a `status`, so the next
        # push of that same list declares 2 again.
        assert format_of_entries(self._check([_path()])) == SKIP_AND_SPAN_FORMAT

    def test_a_promoted_body_gives_up_the_free_meta_boundaries_it_still_carries(self):
        # The two formats disagree about WHERE boundaries live, and a follower
        # run still writes its own into the free `meta`. A body promoted to
        # format 2 because it carries a skip would then be refused over the
        # entries the run produced itself (found in review, PR #639) — so the
        # meta copy goes, the caller is told which boxes lost one, and the rest
        # of `meta` travels on untouched.
        run = _path(meta={"letter_spans": [[[0, 0, 2]]], "tintenpfad": {"runs": 2}})
        body, pfad_format, dropped = push_body([run, _skip(box_index=1, word="das")])
        assert (pfad_format, dropped) == (SKIP_AND_SPAN_FORMAT, [0])
        assert body[0]["meta"] == {"tintenpfad": {"runs": 2}}
        # …and the promoted body is one the server really accepts, which is the
        # cross-check the whole promotion exists for.
        assert self._check(body)

    def test_the_second_release_declares_format_2_for_the_body_it_makes_itself(self):
        # Since 2026-09-20 this image WRITES 2, so an ordinary run's body is
        # declared 2 even when every entry in it is plain. Nothing is given up
        # on that push: the tool stopped putting its own boundaries in the free
        # `meta` in the same release, so there is nothing there to strip.
        assert PFAD_FORMAT == SKIP_AND_SPAN_FORMAT
        run = _path(meta={"tintenpfad": {"runs": 2}})
        body, pfad_format, dropped = push_body([run])
        assert (pfad_format, dropped) == (SKIP_AND_SPAN_FORMAT, [])
        assert body[0]["meta"] == {"tintenpfad": {"runs": 2}}

    def test_the_boundaries_may_not_also_hide_in_the_free_meta(self):
        # Two sets of boundaries on one box would contradict each other the
        # first time one of them is corrected.
        with pytest.raises(ValueError, match="free `meta`"):
            self._check([_path(meta={"letter_spans": [[[0, 0, 2]]]})])
        # …the rest of `meta` travels on untouched, as it always did.
        assert self._check([_path(meta={"tintenpfad": {"runs": 2}})])[0]["meta"] == {"tintenpfad": {"runs": 2}}


class TestAuthoredRule:
    """Hand work is never taken away by a followed push — per box AND per field."""

    def test_a_stored_hand_drawn_path_the_push_leaves_out_is_named(self):
        # The write is a FULL replacement, so an omitted box is a deleted one.
        stored = [_path(verfahren=AUTHORED)]
        assert displaced_authored(stored, []) == [(0, FIELD_PATH)]
        assert displaced_authored(stored, [_path(box_index=1, word="das")]) == [(0, FIELD_PATH)]

    def test_a_stored_hand_drawn_path_answered_by_a_followed_one_is_named(self):
        assert displaced_authored([_path(verfahren=AUTHORED)], [_path()]) == [(0, FIELD_PATH)]

    def test_the_author_may_correct_his_own_hand_drawn_path(self):
        # Authored over authored is the author correcting his own trace — the
        # case that keeps a hand-drawing surface possible at all.
        assert displaced_authored([_path(verfahren=AUTHORED)], [_path(verfahren=AUTHORED)]) == []

    def test_a_followed_path_is_the_runs_own_and_may_be_replaced(self):
        assert displaced_authored([_path()], [_path()]) == []
        assert displaced_authored([_path()], []) == []

    def test_a_fassung_nobody_has_followed_has_nothing_to_protect(self):
        # `pfade` is NULL before the first follow — the reason the helper takes
        # the stored list as it comes off the row rather than a checked one.
        assert displaced_authored(None, [_path()]) == []
        assert displaced_authored([], [_path()]) == []

    def test_every_displaced_box_is_named_once_and_in_order(self):
        stored = [_path(box_index=1, word="das", verfahren=AUTHORED), _path(box_index=0, verfahren=AUTHORED)]
        assert displaced_authored(stored, []) == [(0, FIELD_PATH), (1, FIELD_PATH)]
        # …and one rescued box does not rescue the other.
        assert displaced_authored(stored, [_path(box_index=0, verfahren=AUTHORED)]) == [(1, FIELD_PATH)]

    def test_a_hand_corrected_boundary_survives_an_ordinary_re_follow(self):
        # The box-level rule got this wrong in both directions: it would have
        # locked a box that only carries corrected boundaries, and it waved a
        # push through that kept the `verfahren` and dropped them.
        stored = [_path(letter_spans=[_span(herkunft=AUTHORED)])]
        assert displaced_authored(stored, [_path(letter_spans=[_span(herkunft=AUTHORED)])]) == []
        assert displaced_authored(stored, [_path()]) == [(0, FIELD_SPANS)]
        assert displaced_authored(stored, []) == [(0, FIELD_SPANS)]

    def test_a_boundary_the_follower_assigned_is_the_runs_own(self):
        # `auto` is a derivation like the Bahn it sits on; only a corrected
        # boundary is ground truth.
        stored = [_path(letter_spans=[_span()])]
        assert displaced_authored(stored, [_path()]) == []

    def test_a_corrected_boundary_may_not_be_turned_back_into_an_assigned_one(self):
        # Same numbers, other provenance — that IS the loss, and comparing the
        # spans without their `herkunft` would have missed it.
        stored = [_path(letter_spans=[_span(herkunft=AUTHORED)])]
        assert displaced_authored(stored, [_path(letter_spans=[_span()])]) == [(0, FIELD_SPANS)]

    def test_a_box_names_the_one_piece_of_hand_work_it_loses(self):
        # Where the Bahn itself goes, its boundaries go with it; saying so
        # twice would only make the refusal longer.
        stored = [_path(verfahren=AUTHORED, letter_spans=[_span(herkunft=AUTHORED)])]
        assert displaced_authored(stored, [_path()]) == [(0, FIELD_PATH)]

    def test_the_author_may_redraw_a_box_whose_boundaries_he_had_corrected(self):
        # Both fields pass for an answer BY HAND, and they have to: boundaries
        # are drawn on a Bahn and do not outlive it. Guarding them against the
        # author's own re-draw left him no move at all — dropping them was a
        # 409 and bringing them back a 422, because they index samples the new
        # Bahn no longer has (found in review, PR #639).
        stored = [_path(verfahren=AUTHORED, letter_spans=[_span(herkunft=AUTHORED)])]
        redrawn = _path(verfahren=AUTHORED, strokes=[[[0.0, 0.0], [0.4, 0.2]]])
        assert displaced_authored(stored, [redrawn]) == []
        # …and the fresh Bahn really is one the old boundaries could not fit.
        with pytest.raises(ValueError, match="which has 2 point"):
            check_paths(
                [{**redrawn, "letter_spans": [_span(herkunft=AUTHORED)]}],
                ROW,
                WIDTH_PX,
                HEIGHT_PX,
                pfad_format=SKIP_AND_SPAN_FORMAT,
            )

    def test_a_skip_never_passes_as_the_author_correcting_his_own_trace(self):
        # A Skip-Eintrag says there is no path in this box. Letting it through
        # on its `verfahren` alone would delete a drawing with neither a 409
        # nor the archive check that hangs off `--replace-authored` — a hole
        # opened by the very entry type this format adds (review, PR #639).
        stored = [_path(verfahren=AUTHORED)]
        assert displaced_authored(stored, [_skip(verfahren=AUTHORED)]) == [(0, FIELD_PATH)]
        assert displaced_authored(stored, [_skip()]) == [(0, FIELD_PATH)]
        # …and the boundaries of a followed box are not its to drop either.
        assert displaced_authored([_path(letter_spans=[_span(herkunft=AUTHORED)])], [_skip(verfahren=AUTHORED)]) == [
            (0, FIELD_SPANS)
        ]


class TestPfadEtag:
    """The token that keeps two write doors from overwriting each other."""

    def test_the_same_stored_list_gives_the_same_token(self):
        # Two readings of one cell have to agree, or the lock refuses every
        # write instead of the racing ones.
        assert pfad_etag([_path()], PFAD_FORMAT) == pfad_etag([_path()], PFAD_FORMAT)

    def test_a_token_is_an_http_entity_tag(self):
        # Quoted, so a caller echoes the header value it was handed rather than
        # reassembling one (RFC 9110).
        token = pfad_etag(None, 1)
        assert token.startswith('"') and token.endswith('"')
        assert len(token) == 66

    def test_anything_the_cell_says_moves_the_token(self):
        base = pfad_etag([_path()], PFAD_FORMAT)
        assert pfad_etag([_path(erzeugt_am="2026-09-20")], PFAD_FORMAT) != base
        assert pfad_etag([_path(), _path(box_index=1, word="das")], PFAD_FORMAT) != base
        assert pfad_etag([], PFAD_FORMAT) != base
        # The format marker is half the statement — a list and the semantics
        # its entries obey are one thing, so a token over only the entries
        # would start lying the first time the two can move apart.
        assert pfad_etag([_path()], PFAD_FORMAT + 1) != base

    def test_a_fassung_nobody_has_followed_still_has_a_token(self):
        # The per-box write starts on an empty row — that is the normal case
        # for a box the author draws first — so NULL needs a token too, and one
        # that is not the empty list's („nobody looked" is not „nothing found").
        assert pfad_etag(None, 1) != pfad_etag([], 1)

    def test_the_key_order_of_a_stored_entry_does_not_matter(self):
        # JSONB hands the keys back in its own order; a token that followed it
        # would refuse a write nobody raced.
        entry = _path()
        shuffled = dict(reversed(list(entry.items())))
        assert pfad_etag([shuffled], PFAD_FORMAT) == pfad_etag([entry], PFAD_FORMAT)


class TestFollowerHandover:
    """The seam between the local follower and what the API stores."""

    def test_the_crop_frame_is_translated_into_the_strips_own_frame(self):
        # The follower registers against the CROP it was handed; the stored
        # frame is the STRIP's. Getting this wrong would draw every path of
        # every word on top of the first one.
        from tools.eigenhand.pfad import _entry

        frame = _frame(1)
        entry = _entry(_INFO, frame, flecken_n=2, today="2026-09-12", sensors={})
        assert entry["box_index"] == 1
        assert entry["word"] == "das"
        assert entry["registration_px"] == {"tx": 3.0 + frame["rect_px"][0], "ty": -1.0, "baseline_row": 240.0}
        assert entry["flecken_n"] == 2
        assert entry["erzeugt_am"] == "2026-09-12"
        # And what comes out of the follower has to pass the API's own gate.
        assert check_paths([entry], ROW, WIDTH_PX, HEIGHT_PX, ["lesen", "das"], PFAD_FORMAT)

    def test_every_sensor_the_traffic_light_reads_is_in_the_stored_projection(self):
        # The projection is a fixed tuple, so a sensor missing from it is
        # computed, printed and then never reaches the database — afterwards
        # indistinguishable from „measured 0". This is the one assertion that
        # notices, so the keys are DERIVED from the module that grades them
        # rather than listed here: a list would go stale on the seventh sensor,
        # which is the exact drift this pin exists for.
        from tools.eigenhand.pfad import STORED_SENSORS

        graded = {value for name, value in vars(tintentreue).items() if name.startswith("KEY_")}
        assert len(graded) >= 6
        assert graded <= set(STORED_SENSORS)

    def test_the_stored_sensor_block_is_exactly_the_projection(self):
        # Neither more nor less: the follower's diagnosis carries dozens of
        # decoder internals a shared row is not a dumping ground for, and a
        # sensor the light reads must be present even when nothing measured it
        # (as an explicit null, never as a missing key).
        from tools.eigenhand.pfad import STORED_SENSORS, _entry

        entry = _entry(_INFO, _frame(1), flecken_n=None, today="2026-09-20", sensors={})
        assert set(entry["meta"]["tintenpfad"]) == set(STORED_SENSORS)
        assert entry["meta"]["tintenpfad"]["runs"] == 2
        assert entry["meta"]["tintenpfad"][tintentreue.KEY_AIOU] is None
        # And the follower's own free-meta boundaries do not travel: format 2
        # keeps them in a checked field, and `check_paths` refuses the copy.
        assert "letter_spans" not in entry["meta"]

    def test_the_measured_sensors_land_in_the_row_the_light_reads(self):
        from tools.eigenhand.pfad import _entry

        sensors = {tintentreue.KEY_EXKURSION: 0.11, tintentreue.KEY_AIOU: 0.83}
        entry = _entry(_INFO, _frame(1), flecken_n=None, today="2026-09-20", sensors=sensors)
        stored = check_paths([entry], ROW, WIDTH_PX, HEIGHT_PX, ["lesen", "das"], PFAD_FORMAT)[0]
        urteil = tintentreue.tintentreue(stored, hand="mn-suetterlin", pfade_format=PFAD_FORMAT, maske_n=None)
        assert urteil.gemessen
        assert {wert.name: wert.wert for wert in urteil.sensoren}[tintentreue.SENSOR_AIOU] == 0.83

    def test_a_box_the_row_does_not_have_stops_the_run_before_it_can_erase(self):
        # `--box` narrows the follow, and the write is a FULL replacement — so
        # a typo would follow nothing, push an empty list and wipe the
        # Fassung's stored paths while reporting success (Copilot review,
        # PR #598). Refused where the row's real boxes are known.
        from tools.eigenhand.pfad import follow_row

        row = {"strip": "S0001", "fassung": "F01", "boxes": [{"index": 0, "word": "lesen"}]}
        with pytest.raises(SystemExit, match="no box 7"):
            follow_row("https://example.invalid", "token", "mn-suetterlin", row, {}, [7])

    def test_a_narrowed_run_keeps_the_paths_of_the_boxes_it_did_not_follow(self):
        # The other half of the same finding: re-following ONE word must not
        # drop the rest of the row.
        from tools.eigenhand import pfad as tool

        stored = [{"box_index": 0, "word": "lesen"}, {"box_index": 1, "word": "das"}]
        fresh = [{"box_index": 1, "word": "das", "verfahren": "tintenpfad"}]
        merged, handed_over, etag = tool._merged(
            "https://example.invalid", "token", "u", fresh, _get=lambda *_: ({"pfade": stored}, STUB_TAG)
        )
        assert etag == STUB_TAG  # the push is guarded by the token of THIS read
        assert [entry["box_index"] for entry in merged] == [0, 1]
        assert merged[1] is fresh[0]  # the followed box is the NEW one, not the stored copy
        assert handed_over is False

    def test_the_dry_run_files_the_body_the_apply_path_would_send(self, tmp_path, monkeypatch):
        # The dry run is the review surface `--apply` is decided on, so it has
        # to file the MERGED list — filing only the followed boxes made a
        # narrowed run look like a whole-row replacement (review of PR #598).
        body = _dry_run(
            tmp_path,
            monkeypatch,
            fresh=[{"box_index": 1, "word": "das", "verfahren": "tintenpfad"}],
            stored=[{"box_index": 0, "word": "lesen"}, {"box_index": 1, "word": "das"}],
            argv=["--hand", "mn-suetterlin", "--strip", "S0001", "--box", "1"],
        )
        assert [entry["box_index"] for entry in body] == [0, 1]

    def test_a_whole_row_run_keeps_the_paths_of_the_boxes_it_could_not_follow(self, tmp_path, monkeypatch):
        # A run over the WHOLE row drops boxes too — `follow_row` skips one
        # whose Bogen has no frame, whose glyphs are unauthored or whose
        # follower gives up. The write is a full replacement, so sending only
        # what came back would delete those boxes' stored paths and report
        # success (Copilot review, PR #598). Box 0 is the skipped one here.
        body = _dry_run(
            tmp_path,
            monkeypatch,
            fresh=[{"box_index": 1, "word": "das", "erzeugt_am": "2026-09-13"}],
            stored=[
                {"box_index": 0, "word": "lesen", "erzeugt_am": "2026-09-11"},
                {"box_index": 1, "word": "das", "erzeugt_am": "2026-09-11"},
            ],
            argv=["--hand", "mn-suetterlin", "--strip", "S0001"],
        )
        assert [entry["box_index"] for entry in body] == [0, 1]
        assert body[0]["erzeugt_am"] == "2026-09-11"  # the skipped box keeps the path it had
        assert body[1]["erzeugt_am"] == "2026-09-13"  # the re-followed box is the fresh one

    def test_a_hand_drawn_path_survives_a_run_that_followed_the_same_box(self, tmp_path, monkeypatch):
        # The server refuses a push that would displace a hand-drawn path
        # (409), so the tool has to merge AROUND it — otherwise re-following a
        # whole row would fail over the one word the author drew himself.
        body = _dry_run(
            tmp_path,
            monkeypatch,
            fresh=[
                {"box_index": 0, "word": "lesen", "verfahren": "tintenpfad"},
                {"box_index": 1, "word": "das", "verfahren": "tintenpfad"},
            ],
            stored=[{"box_index": 0, "word": "lesen", "verfahren": AUTHORED}],
            argv=["--hand", "mn-suetterlin", "--strip", "S0001"],
        )
        assert [entry["verfahren"] for entry in body] == [AUTHORED, "tintenpfad"]

    def test_a_hand_corrected_boundary_rides_along_onto_the_fresh_bahn(self, tmp_path, monkeypatch):
        # The field rule's local half: the box may be followed again, but the
        # boundaries on it are the author's own — the server refuses a push
        # that drops them, so the tool carries them over. The run's own spans
        # on a hand-corrected STROKE step aside: a boundary is only meaningful
        # beside the ones next to it.
        corrected = _span(herkunft=AUTHORED)
        body = _dry_run(
            tmp_path,
            monkeypatch,
            fresh=[_path(erzeugt_am="2026-09-20", letter_spans=[_span(first=1)])],
            stored=[_path(erzeugt_am="2026-09-11", letter_spans=[corrected])],
            argv=["--hand", "mn-suetterlin", "--strip", "S0001"],
        )
        assert body[0]["erzeugt_am"] == "2026-09-20"  # the Bahn IS the fresh one
        assert body[0][FIELD_SPANS] == [corrected]
        assert displaced_authored([_path(letter_spans=[corrected])], body) == []

    def test_a_fresh_bahn_that_cannot_hold_the_boundaries_keeps_the_stored_one(self, tmp_path, monkeypatch):
        # Re-indexing a hand-corrected boundary onto a different Bahn is the
        # Span-Zuordner's work, not a silent repair inside a merge — and the
        # push would be refused as a desynchronised span anyway. So the run's
        # own result for that box is dropped, loudly.
        body = _dry_run(
            tmp_path,
            monkeypatch,
            fresh=[_path(erzeugt_am="2026-09-20", strokes=[[[0.0, 0.0], [1.0, 1.0]]])],
            stored=[_path(erzeugt_am="2026-09-11", letter_spans=[_span(herkunft=AUTHORED)])],
            argv=["--hand", "mn-suetterlin", "--strip", "S0001"],
        )
        assert body[0]["erzeugt_am"] == "2026-09-11"
        assert body[0][FIELD_SPANS] == [_span(herkunft=AUTHORED)]

    def test_the_boundaries_are_not_what_replace_authored_hands_over(self, monkeypatch):
        # `--replace-authored` gives up a BAHN. On a box whose stored Bahn is a
        # follow, the corrected boundaries ride along as always — with the
        # override set the server's own refusal is switched off, so this merge
        # is all that stands between a re-follow and a silent loss.
        drawing = {"box_index": 1, "word": "das", "verfahren": AUTHORED}
        corrected = _span(herkunft=AUTHORED)
        _, sent = _apply_run(
            monkeypatch,
            fresh=[_path(), {"box_index": 1, "word": "das", "verfahren": "tintenpfad"}],
            stored=[_path(letter_spans=[corrected]), drawing],
            archived=[drawing],
            argv=["--hand", "mn-suetterlin", "--strip", "S0001", "--replace-authored"],
        )
        body = sent["pfade"]
        assert [entry["verfahren"] for entry in body] == ["tintenpfad", "tintenpfad"]
        assert body[0][FIELD_SPANS] == [corrected]
        # And the push says what it IS: the carried boundaries are a format-2
        # field, so declaring this image's own `PFAD_FORMAT` over them would be
        # refused by the server's content rule (review, PR #639).
        assert sent["format"] == SKIP_AND_SPAN_FORMAT

    def test_the_push_declares_the_format_the_merged_body_is_actually_in(self, monkeypatch):
        # The carry-over could not land on the one kind of box it exists for:
        # the run's own result is format 1, the boundaries it carries are a
        # format-2 field, and the server refuses every format-2 field under a
        # format-1 declaration. So the tool would have built a body its own
        # push could not store (review, PR #639). Held here against the gate
        # the API runs on it, which is the cross-check that was missing.
        corrected = _span(herkunft=AUTHORED)
        _, sent = _apply_run(
            monkeypatch,
            fresh=[_path()],
            stored=[_path(letter_spans=[corrected])],
            argv=["--hand", "mn-suetterlin", "--strip", "S0001"],
        )
        assert sent["format"] == SKIP_AND_SPAN_FORMAT
        assert check_paths(sent["pfade"], ROW, WIDTH_PX, HEIGHT_PX, pfad_format=sent["format"])

    def test_a_hand_corrected_stroke_keeps_its_WHOLE_stored_boundary_set(self, monkeypatch):
        # A stroke usually carries one corrected boundary among several the
        # follower assigned. Carrying only the corrected one would leave the
        # letters beside it unlabelled and call that a rescue (review, PR #639)
        # — so every stored boundary of that stroke travels with it.
        corrected = _span(slot=1, first=1, last=1, herkunft=AUTHORED)
        neighbours = [_span(slot=0, first=0, last=0), _span(slot=2, first=2, last=2)]
        _, sent = _apply_run(
            monkeypatch,
            fresh=[_path(letter_spans=[_span(slot=0, first=0, last=2)])],
            stored=[_path(letter_spans=[neighbours[0], corrected, neighbours[1]])],
            argv=["--hand", "mn-suetterlin", "--strip", "S0001"],
        )
        assert sent["pfade"][0][FIELD_SPANS] == [neighbours[0], corrected, neighbours[1]]
        assert check_paths(sent["pfade"], ROW, WIDTH_PX, HEIGHT_PX, pfad_format=sent["format"])

    def test_a_stored_meta_boundary_is_given_up_when_the_push_is_promoted(self, monkeypatch, capsys):
        # Format 2 refuses letter boundaries in the free `meta`, and a row
        # written before it carries exactly those. A merge promoted for
        # carrying a skip would otherwise build a body its own push could not
        # store (review, PR #639). Given up, and said out loud — and it is the
        # STORED entry that loses them, since `_entry` stopped writing the copy.
        _, sent = _apply_run(
            monkeypatch,
            fresh=[_skip(grund="gave_up")],
            stored=[_path(box_index=1, word="das", meta={"letter_spans": [[[0, 0, 2]]], "tintenpfad": {"runs": 2}})],
            argv=["--hand", "mn-suetterlin", "--strip", "S0001", "--box", "0"],
        )
        assert sent["format"] == SKIP_AND_SPAN_FORMAT
        assert sent["pfade"][1]["meta"] == {"tintenpfad": {"runs": 2}}
        assert check_paths(sent["pfade"], ROW, WIDTH_PX, HEIGHT_PX, pfad_format=sent["format"])
        assert "letter boundaries a stored entry carries at box 1" in capsys.readouterr().out

    def test_a_stored_skip_travels_back_up_under_a_number_that_knows_it(self, monkeypatch):
        # The other half: `_merged` keeps every box this run did not follow, so
        # once a row holds format-2 entries the tool pushes them back — and a
        # format-1 declaration over them would lock this follower out of that
        # row for good.
        _, sent = _apply_run(
            monkeypatch,
            fresh=[_path()],
            stored=[_path(), _skip(box_index=1, word="das")],
            argv=["--hand", "mn-suetterlin", "--strip", "S0001", "--box", "0"],
        )
        assert sent["format"] == SKIP_AND_SPAN_FORMAT
        assert [entry.get("status") for entry in sent["pfade"]] == [None, "skipped"]
        assert check_paths(sent["pfade"], ROW, WIDTH_PX, HEIGHT_PX, pfad_format=sent["format"])

    def test_the_dry_run_files_the_format_the_apply_path_would_declare(self, tmp_path, monkeypatch):
        # The dry run is the surface `--apply` is decided on, so the file has
        # to be the DOCUMENT that would be sent, envelope and all.
        from tools.eigenhand import pfad as tool

        _stub_run(monkeypatch, fresh=[_path()], stored=[_path(letter_spans=[_span(herkunft=AUTHORED)])])
        monkeypatch.setattr(tool, "request_json", lambda *_a, **_k: pytest.fail("a dry run must not write"))
        out = tmp_path / "pfade.json"
        assert tool.main(["--hand", "mn-suetterlin", "--strip", "S0001", "--out", str(out)]) == 0
        assert json.loads(out.read_text())["format"] == SKIP_AND_SPAN_FORMAT

    def test_the_terminal_flag_is_what_gives_an_archived_hand_drawn_path_up(self, monkeypatch, capsys):
        # The only way past — and it has to reach the SERVER, since the tool's
        # own merge is not what the stored row is protected by.
        drawing = {"box_index": 0, "word": "lesen", "verfahren": AUTHORED}
        url, sent = _apply_run(
            monkeypatch,
            fresh=[{"box_index": 0, "word": "lesen", "verfahren": "tintenpfad"}],
            stored=[drawing],
            archived=[drawing],
            argv=["--hand", "mn-suetterlin", "--strip", "S0001", "--replace-authored"],
        )
        assert url.endswith("?replace_authored=true")
        assert [entry["verfahren"] for entry in sent["pfade"]] == ["tintenpfad"]
        # The destructive path has to be the loud one: nothing else in the run
        # names the hand work it just handed over — and what the check proved
        # is only that the copy is in this machine's Kartei, on one disk, so
        # the line has to name the archive step too.
        out = capsys.readouterr().out
        assert "box 0" in out
        assert "snapshot --hand mn-suetterlin" in out

    def test_the_flag_refuses_while_the_drawing_is_not_archived(self, monkeypatch):
        # Author decision B, 2026-09-20: nothing can follow a drawing again, so
        # the terminal may not turn the last copy into none. One command fixes
        # it, and the refusal has to name that command.
        with pytest.raises(SystemExit, match=r"pull --hand mn-suetterlin --pfade"):
            _apply_run(
                monkeypatch,
                fresh=[{"box_index": 0, "word": "lesen", "verfahren": "tintenpfad"}],
                stored=[{"box_index": 0, "word": "lesen", "verfahren": AUTHORED}],
                archived=[],
                argv=["--hand", "mn-suetterlin", "--strip", "S0001", "--replace-authored"],
            )

    def test_an_archived_copy_of_an_older_drawing_does_not_count(self, monkeypatch):
        # „Is there a record" is not the question: the author may have corrected
        # his own trace since the last pull, and then the Kartei holds a
        # DIFFERENT Bahn than the one this run would hand over.
        with pytest.raises(SystemExit, match="not archived"):
            _apply_run(
                monkeypatch,
                fresh=[{"box_index": 0, "word": "lesen", "verfahren": "tintenpfad"}],
                stored=[{"box_index": 0, "word": "lesen", "verfahren": AUTHORED, "erzeugt_am": "2026-09-20"}],
                archived=[{"box_index": 0, "word": "lesen", "verfahren": AUTHORED, "erzeugt_am": "2026-09-14"}],
                argv=["--hand", "mn-suetterlin", "--strip", "S0001", "--replace-authored"],
            )

    def test_an_ordinary_apply_asks_for_no_override(self, monkeypatch):
        url, sent = _apply_run(
            monkeypatch,
            fresh=[{"box_index": 0, "word": "lesen", "verfahren": "tintenpfad"}],
            stored=[{"box_index": 0, "word": "lesen", "verfahren": AUTHORED}],
            argv=["--hand", "mn-suetterlin", "--strip", "S0001"],
        )
        assert "replace_authored" not in url
        assert [entry["verfahren"] for entry in sent["pfade"]] == [AUTHORED]
        # Nothing format-2 in this body, so the push says what this image
        # writes — the declaration follows the content, and never up for free.
        assert sent["format"] == PFAD_FORMAT

    def test_a_dry_run_says_it_WOULD_hand_the_drawing_over(self, tmp_path, monkeypatch, capsys):
        # Nothing is given up until the PUT, and the merge runs before the two
        # paths part ways — so a dry run must not claim the Kartei is the last
        # copy while the database still holds the drawing (review, PR #635).
        from tools.eigenhand import pfad as tool

        drawing = {"box_index": 0, "word": "lesen", "verfahren": AUTHORED}
        _stub_run(monkeypatch, fresh=[{"box_index": 0, "word": "lesen", "verfahren": "tintenpfad"}], stored=[drawing])
        monkeypatch.setattr(tool, "load_kartei", lambda _hand: _kartei_with([drawing]))
        monkeypatch.setattr(tool, "request_json", lambda *_a, **_k: pytest.fail("a dry run must not write"))
        out = tmp_path / "pfade.json"
        assert tool.main(["--hand", "mn-suetterlin", "--strip", "S0001", "--replace-authored", "--out", str(out)]) == 0
        printed = capsys.readouterr().out
        assert "WOULD hand" in printed
        assert "snapshot --hand" not in printed

    def test_the_override_rides_only_on_a_row_that_gives_a_drawing_up(self, monkeypatch):
        # The flag is set once for a whole strip. A row that carries no
        # hand-drawn path at all must still go up WITHOUT it — otherwise the
        # server's 409, the one check that does not run on this machine, is
        # switched off for boxes the local guard never looked at.
        url, _sent = _apply_run(
            monkeypatch,
            fresh=[{"box_index": 0, "word": "lesen", "verfahren": "tintenpfad"}],
            stored=[{"box_index": 1, "word": "das", "verfahren": "tintenpfad"}],
            archived=[],
            argv=["--hand", "mn-suetterlin", "--strip", "S0001", "--replace-authored"],
        )
        assert "replace_authored" not in url

    def test_a_list_that_moved_under_the_run_stops_it_and_names_the_re_run(self, monkeypatch):
        # The server refuses a push whose token no longer matches (412) — the
        # author drew a box in the workbench while this run was following. The
        # refusal is the server's; the NEXT STEP is the terminal's, and it has
        # to be a line the operator can run rather than „read the Fassung
        # again". Re-running follows the ink a second time, which is cheap, and
        # the fresh read carries the drawing.
        from tools.eigenhand import pfad as tool

        _stub_run(monkeypatch, fresh=[{"box_index": 0, "word": "lesen", "verfahren": "tintenpfad"}], stored=[])

        def _refuse(*_args, **_kwargs):
            raise StaleRead("PUT … → 412: the stored paths have moved on since this was read")

        monkeypatch.setattr(tool, "request_json", _refuse)
        with pytest.raises(SystemExit) as refused:
            tool.main(["--hand", "mn-suetterlin", "--strip", "S0001", "--box", "0", "--apply"])
        message = str(refused.value)
        assert "moved on since this was read" in message  # the server's own words survive
        # The line is THIS run again, narrowing included — an operator who
        # followed one box is not told to re-follow the whole row.
        assert "pfad --hand mn-suetterlin --strip S0001 --fassung F01 --box 0 --apply" in message
        # Never the destructive flag: whatever landed in between is exactly
        # what a blanket override would give up again.
        assert "--replace-authored" not in message

    def test_the_declared_configuration_is_one_the_follower_accepts(self):
        # The arms are named in the tool and stored with every path; a renamed
        # weight would otherwise only surface on a real run against real ink.
        from tools.eigenhand.pfad import KONFIGURATION
        from tools.pairlab.tintenpfad import TintenpfadWeights

        weights = TintenpfadWeights(**KONFIGURATION)
        assert (weights.rail, weights.edt_upsample, weights.ink_bridge_xh) == ("tentfit", 4, 1.0)
        assert all(
            getattr(weights, arm) for arm in ("tip_read", "hairpin_tip", "ride_back", "tip_grey_stop", "self_jump")
        )


class TestSkipEntries:
    """Every way a box loses its path, and the reason it is stored under.

    Getting this mapping wrong is worse than writing no skip at all: the
    Nachfahr-Liste routes the author's work by `grund` — „unauthored" is a jump
    to the plate, „no_geometry" a Bogen to re-measure, and only „gave_up" is
    follower work.
    """

    ROW_IN = {
        "strip": "S0001",
        "fassung": "F01",
        "sheet": "B0001",
        "row_index": 0,
        "crop_origin_mm": ORIGIN_MM,
        "width_px": WIDTH_PX,
        "height_px": HEIGHT_PX,
        "flecken": [],
        "boxes": [{"index": 0, "word": "lesen"}],
    }

    def _follow(self, monkeypatch, *, no_geometry=False, missing=(), info=None) -> list[dict]:
        """`follow_row` with the ink, the network and the follower stubbed out."""
        import tools.pairlab.tintenpfad as follower
        from tools.eigenhand import pfad as tool

        monkeypatch.setattr(tool, "request_json", lambda *_a, **_k: {"rows": [ROW]})
        monkeypatch.setattr(tool, "_strip_plane", lambda *_a: np.zeros((HEIGHT_PX, WIDTH_PX)))
        monkeypatch.setattr(tool, "_paper_sensors", lambda *_a: {})
        case = SimpleNamespace(mask=np.zeros((10, 10), dtype=bool))
        monkeypatch.setattr(tool, "_case_for_box", lambda *_a: (case, list(missing)))
        monkeypatch.setattr(follower, "follow_case", lambda *_a: info)
        if no_geometry:
            monkeypatch.setattr(
                tool, "frame_for_box", lambda *_a: (_ for _ in ()).throw(ValueError("no printed `band_mm.waist`"))
            )
        return tool.follow_row("https://example.invalid", "t", "mn-suetterlin", dict(self.ROW_IN), {}, None)

    def _stored(self, entries: list[dict]) -> dict:
        """What the API makes of them — the shape check every skip has to pass."""
        return check_paths(entries, ROW, WIDTH_PX, HEIGHT_PX, ["lesen", "das"], PFAD_FORMAT)[0]

    def test_a_bogen_without_cut_geometry_is_a_no_geometry_skip(self, monkeypatch):
        entry = self._follow(monkeypatch, no_geometry=True)[0]
        assert (entry["grund"], entry["status"]) == ("no_geometry", "skipped")
        assert "band_mm" in entry["detail"]
        # No frame existed, so the entry claims no registration and no x-height
        # rather than the printed ruling: that would be a nominal number in a
        # measured field.
        stored = self._stored([entry])
        assert stored["registration_px"] is None and stored["xh_px"] is None and stored["strokes"] == []
        # The arms had no bearing on the outcome — the follower never ran.
        assert stored["konfiguration"] == {}

    def test_a_no_geometry_skip_takes_its_word_from_the_printed_layout(self, monkeypatch):
        # `check_paths` holds every entry's word against the LAYOUT's box, the
        # same source `_entry` takes it from. A skip built from the strip
        # listing instead would be refused wherever the two disagree.
        from tools.eigenhand import pfad as tool

        row = {**self.ROW_IN, "boxes": [{"index": 0, "word": "Lesen"}]}
        monkeypatch.setattr(tool, "request_json", lambda *_a, **_k: {"rows": [ROW]})
        monkeypatch.setattr(tool, "_strip_plane", lambda *_a: np.zeros((HEIGHT_PX, WIDTH_PX)))
        monkeypatch.setattr(
            tool, "frame_for_box", lambda *_a: (_ for _ in ()).throw(ValueError("no printed `band_mm.waist`"))
        )
        entry = tool.follow_row("https://example.invalid", "t", "mn-suetterlin", row, {}, None)[0]
        assert entry["word"] == "lesen"
        assert self._stored([entry])["word"] == "lesen"

    def test_a_box_the_printed_row_does_not_have_stays_a_gap(self, monkeypatch):
        # The other way `frame_for_box` refuses: a strip listing box the layout
        # row has no entry for. A skip carrying that index is refused by
        # `check_paths` — and takes the whole Fassung's push with it, where the
        # box alone is in doubt. So it costs that box, never the row.
        from tools.eigenhand import pfad as tool

        row = {**self.ROW_IN, "boxes": [{"index": 0, "word": "lesen"}, {"index": 2, "word": "sonne"}]}
        monkeypatch.setattr(tool, "request_json", lambda *_a, **_k: {"rows": [ROW]})
        monkeypatch.setattr(tool, "_strip_plane", lambda *_a: np.zeros((HEIGHT_PX, WIDTH_PX)))
        monkeypatch.setattr(tool, "_case_for_box", lambda *_a: (SimpleNamespace(mask=None), ["y"]))
        entries = tool.follow_row("https://example.invalid", "t", "mn-suetterlin", row, {}, None)
        assert [entry["box_index"] for entry in entries] == [0]

    def test_a_word_the_plate_cannot_compose_is_an_unauthored_skip(self, monkeypatch):
        entry = self._follow(monkeypatch, missing=["y", "q"])[0]
        assert (entry["grund"], entry["detail"]) == ("unauthored", "y q")
        assert self._stored([entry])["konfiguration"] == {}

    def test_a_follower_that_gives_up_says_so_under_its_own_configuration(self, monkeypatch):
        entry = self._follow(monkeypatch, info={"status": "unvisited", "detail": "0.42 of the ink is unvisited"})[0]
        assert entry["grund"] == "gave_up"
        assert entry["detail"] == "unvisited: 0.42 of the ink is unvisited"
        # This one DID read ink, so the arms it read it with travel into the row.
        assert self._stored([entry])["konfiguration"]["rail"] == "tentfit"

    def test_a_narrowed_run_says_nothing_about_the_boxes_it_did_not_look_at(self, monkeypatch):
        # `not_selected` is in the vocabulary and is deliberately never written
        # here: `--box` narrows THIS run, the write is a full replacement, and
        # declaring the other boxes skipped would overwrite the rest of the row.
        from tools.eigenhand import pfad as tool

        row = {**self.ROW_IN, "boxes": [{"index": 0, "word": "lesen"}, {"index": 1, "word": "das"}]}
        monkeypatch.setattr(tool, "request_json", lambda *_a, **_k: {"rows": [ROW]})
        monkeypatch.setattr(tool, "_strip_plane", lambda *_a: np.zeros((HEIGHT_PX, WIDTH_PX)))
        monkeypatch.setattr(tool, "_case_for_box", lambda *_a: (SimpleNamespace(mask=None), ["y"]))
        entries = tool.follow_row("https://example.invalid", "t", "mn-suetterlin", row, {}, [1])
        assert [entry["box_index"] for entry in entries] == [1]
        assert all(entry["grund"] != "not_selected" for entry in entries)

    def test_a_skip_never_gives_up_a_stored_path(self, monkeypatch, capsys):
        # „Unauthored" depends on which glyphs the plate carries TODAY and
        # „gave up" on the arms of this run, so a box followed cleanly last week
        # can produce a skip this week. Storing it would throw a good Bahn away
        # to record that this run did not reproduce it.
        from tools.eigenhand import pfad as tool

        merged, handed_over, _etag = tool._merged(
            "https://example.invalid", "t", "u", [_skip(grund="gave_up")], _get=lambda *_: ({"pfade": [_path()]}, None)
        )
        assert merged == [_path()] and handed_over is False
        assert "keeping the stored path at box 0" in capsys.readouterr().out

    def test_a_skip_does_land_in_a_box_that_holds_nothing(self, monkeypatch):
        from tools.eigenhand import pfad as tool

        merged, _handed, _etag = tool._merged(
            "https://example.invalid", "t", "u", [_skip(grund="gave_up")], _get=lambda *_: ({"pfade": []}, None)
        )
        assert [entry["status"] for entry in merged] == ["skipped"]

    def test_the_reason_is_one_the_schema_knows(self):
        # A free string would merge the four states back into one within a
        # month — the tool must only ever write reasons out of the closed list.
        from tools.eigenhand.pfad import _skip as skip_entry

        entry = skip_entry(0, "lesen", "gave_up", "x" * 400, None, "2026-09-20", ran=True)
        assert entry["grund"] in SKIP_REASONS
        # And a follower message longer than the bound is cut rather than
        # costing the whole run a 422.
        assert len(self._stored([entry])["detail"]) == MAX_DETAIL


class TestPaperSensors:
    """The two sensors this tool measures itself, against the strip's own ink."""

    MASK = np.zeros((60, 140), dtype=bool)
    MASK[30, 10:110] = True

    @staticmethod
    def _info(v: float) -> dict:
        """A one-stroke Bahn along `v`, registered so `v = 0` lies on the ink.

        4.5 x-heights long, which is 90 px inside the 100 px ink line: an
        excursion reads the distance to the nearest ink pixel, so a Bahn
        running past the END of the ink would measure its own overshoot.
        """
        return {
            "strokes": [[[0.0, v], [4.5, v]]],
            "registration_px": {"tx": 10.0, "ty": 0.0, "baseline_row": 30.0},
            "xh_px": 20.0,
        }

    def test_a_bahn_on_the_ink_reads_as_no_excursion_and_a_high_aiou(self):
        from tools.eigenhand.pfad import _paper_sensors

        sensors = _paper_sensors(self.MASK, self._info(0.0))
        assert sensors[tintentreue.KEY_EXKURSION] == 0.0
        assert sensors[tintentreue.KEY_AIOU] > 0.9

    def test_a_bahn_beside_the_ink_reads_as_a_full_x_height_away(self):
        from tools.eigenhand.pfad import _paper_sensors

        # One x-height above the ink line: 20 px at xh = 20 px.
        sensors = _paper_sensors(self.MASK, self._info(1.0))
        assert sensors[tintentreue.KEY_EXKURSION] == pytest.approx(1.0, abs=0.05)
        assert sensors[tintentreue.KEY_AIOU] < 0.1

    def test_a_reading_the_traffic_light_can_grade_comes_out(self):
        # The point of the pair: they are measured so the light does not have
        # to compute, and the light has to find them under its own key names.
        from tools.eigenhand.pfad import MEASURED_SENSORS, _paper_sensors

        assert set(_paper_sensors(self.MASK, self._info(0.0))) == set(MEASURED_SENSORS)

    def test_a_bahn_without_a_single_point_is_not_measured_as_zero(self):
        # 0.0 is the BEST reading an excursion can get and the WORST an AIoU
        # can; „nothing to measure" is neither, and a null is how the row says
        # so (`core.eigenhand.tintentreue.Rohzahlen`).
        from tools.eigenhand.pfad import _paper_sensors

        assert _paper_sensors(self.MASK, {**self._info(0.0), "strokes": []}) == {
            tintentreue.KEY_EXKURSION: None,
            tintentreue.KEY_AIOU: None,
        }


class TestDuctusSeed:
    """Which words a strip can be followed at all — the seed, not the ink.

    Both defects fixed here refused the author's OWN hand: a word holding a
    ligature nothing authors (`ch`) and a word holding a letter the word bench
    has no use for (`y`). Everything is stubbed at the API seam, so no test
    here needs a fixture root or the network.
    """

    # The live source's authored inventory, cut down to what these words need.
    # `ch` is deliberately absent — it is authored nowhere, by design.
    LIVE = {"K", "u", "r", "e", "n", "t", "longs", "c", "h", "i", "f", "m", "d", "a", "l", "y", "g", "o", "z"}
    # What the frozen word fixtures carry: the bench's 34 keys have no `y`.
    BENCH = LIVE - {"y", "K"}

    @staticmethod
    def _api(have: set[str], laufform: set[str] = frozenset()):
        """A stand-in for `request_json` serving one source's template reads."""

        def get(method: str, url: str, _token: str, *_args, **_kwargs):
            assert method == "GET"
            head, _, query = url.partition("?")
            if head.endswith("/templates"):
                return [{"glyph_key": key, "glyph": key, "variant": 0, "has_data": True} for key in sorted(have)] + [
                    {"glyph_key": key, "glyph": key, "variant": 100, "has_data": True} for key in sorted(laufform)
                ]
            key = head.rsplit("/", 1)[-1]
            variant = int(query.removeprefix("variant=") or 0)
            return {
                "glyph_key": key,
                "glyph": key,
                "variant": variant,
                "advance": 1.0,
                "entry": {},
                "exit_pt": {},
                "anchors": [[0.0, 0.0], [1.0, 1.0]],
                "half_widths": [0.07, 0.07],
                "trace_meta": {"variant": variant},
            }

        return get

    def _case(self, word: str, have: set[str], laufform: set[str] = frozenset()):
        from tools.eigenhand.pfad import LiveDuctus, _case_for_box

        seed = LiveDuctus("https://example.invalid", "token", "suetterlin-1922", get=self._api(have, laufform))
        prior = {"manifest": {"width_resolver": "constant"}, "source_id": "suetterlin-1922", "seed": seed}
        # A plane with a little ink in it: the crop is binarised and skeletonised
        # on the way into the case, and the seed question is orthogonal to it.
        plane = np.ones((HEIGHT_PX, WIDTH_PX), dtype=np.float64)
        plane[180:200, 60:340] = 0.1
        return _case_for_box(prior, plane, _frame(0), word, word, f"S0001/F01#0-{word}")

    def test_a_ligature_without_a_template_decays_into_its_letters(self):
        # `ch` is authored nowhere — the frozen root stores `fechten` as
        # `f e c h t e n` — so the author's own `Kurrentschrift` was refused as
        # unauthored instead of composing c + h with a generated Übergang.
        case, missing = self._case("Kurrentschrift", self.LIVE)
        keys = [slot.key for slot in case.slots]
        assert "ch" not in keys
        assert keys[keys.index("longs") + 1 : keys.index("longs") + 3] == ["c", "h"]
        assert missing == []
        assert case.scorable
        assert set(case.templates) >= {"K", "longs", "c", "h"}

    def test_the_decayed_letters_bring_their_own_laufform_rows(self):
        # The decay changes the key list, so the running forms have to be
        # fetched for the letters — not for the cluster that never existed.
        case, _ = self._case("Kurrentschrift", self.LIVE, laufform={"c", "h", "r", "u"})
        assert set(case.laufform) == {"c", "h", "r", "u"}
        assert all(row["trace_meta"]["variant"] == 100 for row in case.laufform.values())

    def test_sz_stays_atomic_and_is_reported_rather_than_split(self):
        # `decompose_ligature_slot` refuses to split ß: its historic
        # decomposition is an allograph question, and a naive split would write
        # ſſ mid-word. So a source without `sz` gets an honest refusal.
        case, missing = self._case("groß", self.LIVE - {"sz"})
        assert [slot.key for slot in case.slots] == ["g", "r", "o", "sz"]
        assert missing == ["sz"]
        assert not case.scorable

    def test_a_letter_the_bench_lacks_but_the_hand_has_is_followable(self):
        # The second defect: the seed used to be the frozen WORD FIXTURE root,
        # which carries only the 34 keys its 63 bench words need. `y` is
        # authored and has data on the live source — the author's own
        # `immediately` was refused for a bench rule that does not bind a strip.
        case, missing = self._case("immediately", self.LIVE)
        assert "y" in {slot.key for slot in case.slots}
        assert missing == []
        assert case.scorable
        # …and against the bench's own inventory the very same word is not.
        assert self._case("immediately", self.BENCH)[1] == ["y"]

    def test_the_case_says_the_seed_was_read_live(self):
        # The origin label is what a reader of a filed path sees; a strip must
        # not claim a frozen root it never read.
        case, _ = self._case("doctor", self.LIVE)
        assert case.origin == "eigenhand:live:suetterlin-1922"

    def test_the_rows_are_fetched_once_per_glyph_and_then_cached(self):
        from tools.eigenhand.pfad import LiveDuctus

        calls: list[str] = []
        inner = self._api(self.LIVE)

        def counting(method: str, url: str, token: str, *args, **kwargs):
            calls.append(url)
            return inner(method, url, token, *args, **kwargs)

        seed = LiveDuctus("https://example.invalid", "token", "suetterlin-1922", get=counting)
        assert seed.rows_for(["d", "o"])[0].keys() == {"d", "o"}
        assert seed.rows_for(["o", "c"])[0].keys() == {"o", "c"}
        # One inventory read plus one read per distinct glyph — `o` only once.
        assert len(calls) == 1 + 3

    def test_the_style_constants_no_longer_need_the_frozen_templates(self, tmp_path, monkeypatch):
        # The frozen root keeps exactly one job for a strip: the manifest's
        # style-level constants. The BENCH loader still reads its templates out
        # of the same root, unchanged — that is the point of the split, and a
        # root holding only a manifest shows both halves at once.
        from tools.eigenhand.pfad import _style_constants
        from tools.wordlab import cases

        root = tmp_path / "suetterlin" / "suetterlin-1922"
        root.mkdir(parents=True)
        (root / "manifest.json").write_text(
            json.dumps(
                {
                    "set": "words",
                    "source_id": "suetterlin-1922",
                    "style_ratio": [1.0, 1.0, 1.0],
                    "width_resolver": "constant",
                    "constant_nib_units": 0.072,
                    "words": [{"word": "lesen"}],
                }
            )
        )
        monkeypatch.setattr(cases, "fixture_root_for", lambda **_kwargs: root)
        constants = _style_constants("suetterlin")
        assert constants["source_id"] == "suetterlin-1922"
        assert constants["manifest"]["constant_nib_units"] == 0.072
        with pytest.raises(FileNotFoundError):
            cases.iter_fixture_word_cases(style="suetterlin", fixtures_root=tmp_path)

    def test_a_manifest_without_a_source_is_refused_rather_than_guessed(self, tmp_path, monkeypatch):
        from tools.eigenhand.pfad import _style_constants
        from tools.wordlab import cases

        root = tmp_path / "suetterlin" / "suetterlin-1922"
        root.mkdir(parents=True)
        (root / "manifest.json").write_text(json.dumps({"set": "words", "words": []}))
        monkeypatch.setattr(cases, "fixture_root_for", lambda **_kwargs: root)
        with pytest.raises(SystemExit, match="names no source_id"):
            _style_constants("suetterlin")
