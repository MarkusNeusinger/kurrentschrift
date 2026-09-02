"""Unit tests for tools/humanbench/page.py.

The page is the instrument a human spends hours in, and its output is the only
part of the chain that cannot be recomputed. So the tests here guard the two
things that would waste those hours: the payload must stay blind, and the
result file the page emits must be one the analyser can actually read back.

Everything is synthetic — a real payload carries occurrence geometry, which
stays out of this repo (``docs/reference/quellen-und-rechte.md`` §5).
"""

from __future__ import annotations

import copy
import re

import pytest

from tools.humanbench.analyse import RESULT_HEAD, parse_paired_result, parse_result
from tools.humanbench.page import build_page, normalise


# A 1x1 PNG is enough: nothing here judges pixels, only the wrapper around them.
PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

SINGLE = [
    {"id": "S001", "w": 40, "h": 30, "img": PNG, "strokes": [[[0, 0], [10, 10]], [[20, 20], [30, 25]]]},
    {"id": "S002", "w": 40, "h": 30, "img": PNG, "strokes": [[[1, 1], [9, 9]]]},
]

PAIRED = [
    {
        "id": "S001",
        "w": 40,
        "h": 30,
        "img": PNG,
        "panels": [{"strokes": [[[0, 0], [10, 10]]]}, {"strokes": [[[2, 2], [12, 12]]]}],
    }
]

# A WORD screen: the same specimen crop, two compositions drawn as INK —
# silhouette rings for the letter bodies, capsules of their own width for the
# generated connectors.
INKED = [
    {
        "id": "S001",
        "w": 120,
        "h": 40,
        "img": PNG,
        "panels": [
            {"strokes": [[[0, 0], [10, 10]]], "widths": [6.0], "fills": [[[0, 0], [4, 0], [4, 4]]]},
            {"strokes": [[[0, 0], [10, 10]]], "widths": [9.0], "fills": [[[0, 0], [5, 0], [5, 5]]]},
        ],
    }
]


def config_of(html: str, field: str) -> str:
    """Read one string field out of the page's inlined CONFIG object."""
    match = re.search(rf'"{field}":"([^"]*)"', html)
    assert match, f"no {field} in the emitted CONFIG"
    return match.group(1)


# ----------------------------------------------------- the result-file contract


def test_note_is_flattened_to_one_line():
    """A newline in a note must never reach the result file.

    The emitter is browser JavaScript and cannot be imported, so the contract is
    pinned on the template text. It is worth pinning: a bare Enter in the note
    textarea is a NEWLINE by design (the keydown handler keeps it, so a
    half-written thought is never submitted by reflex), the result format is one
    line per screen, and the file is committed verbatim. Without the flattening
    a single Enter makes a whole judged round unparseable — see
    `test_parser_rejects_a_note_that_broke_across_lines` for what that looks
    like from the other end.
    """
    html = build_page(SINGLE)
    assert re.search(r"notes\[i\]\.replace\(/\\s\+/g, ' '\)", html), "the note is no longer whitespace-flattened"


def test_parser_rejects_a_note_that_broke_across_lines():
    """The other end of the same contract: a multi-line note is not readable."""
    broken = 'BEFUND/3 geprueft=2 von 2\nS001:W "eckiger kringel\nund zu spaet"\nS002:G@4s\n'
    with pytest.raises(Exception, match="does not parse"):
        parse_result(broken)


@pytest.mark.parametrize("round_label", ["2 (nachtrag)", "runde 2", " "])
def test_a_tag_with_whitespace_is_refused_at_build_time(round_label):
    """A spaced tag would emit a header no result file could be read from.

    Refused while building rather than after judging: the page would emit
    `BEFUND/2 (nachtrag) geprueft=…`, and the header only parses as a single
    whitespace-free token.
    """
    with pytest.raises(ValueError, match="whitespace-free token"):
        build_page(SINGLE, round_label=round_label)


def test_the_emitted_header_tag_parses_as_a_header():
    html = build_page(SINGLE, round_label="3")
    tag = config_of(html, "tag")
    assert tag == "BEFUND/3"
    assert RESULT_HEAD.match(f"{tag} geprueft=2 von 2")


def test_paired_pages_tag_themselves_differently():
    assert config_of(build_page(PAIRED, round_label="3"), "tag") == "VERGLEICH/3"


# ------------------------------------------------------- the two paired questions
#
# „welche Linie folgt der Tinte besser?" and „welche sieht echter geschrieben
# aus?" measure different properties and their rounds are not comparable
# (menschliche-bewertung.md §8). The instrument therefore carries the question
# into the RESULT FILE's own header, so a text can never be filed under the
# wrong one months later.


def test_the_authenticity_question_tags_its_result_file_differently():
    html = build_page(INKED, round_label="4", question="authentic")
    tag = config_of(html, "tag")
    assert tag == "ECHTHEIT/4"
    assert RESULT_HEAD.match(f"{tag} geprueft=1 von 1")
    assert parse_paired_result(f"{tag} geprueft=1 von 1\nS001:L@4s\n").tag == "ECHTHEIT/4"


def test_the_authenticity_page_asks_about_writing_and_not_about_accuracy():
    """The wording is the measurement: asked as an accuracy question, the round
    would score the same two panels on the property it exists to look past."""
    html = build_page(INKED, question="authentic")
    assert "Welche Zeile sieht echter geschrieben aus?" in html
    assert "Links sieht echter aus" in html and "Links folgt besser" not in html
    assert config_of(html, "question") == "authentic"
    assert config_of(build_page(PAIRED), "question") == "ink"


def test_a_category_round_cannot_be_given_a_two_way_question():
    with pytest.raises(ValueError, match="need two panels"):
        build_page(SINGLE, question="authentic")


def test_an_unknown_question_is_refused_at_build_time():
    with pytest.raises(ValueError, match="is not one of"):
        build_page(PAIRED, question="schoenheit")


# ------------------------------------------------------------------ inked panels


def test_an_inked_panel_carries_its_own_widths_and_fills():
    """Stroke weight is the datum: a word round exists partly because a stroke a
    quarter too thin is invisible on a hairline centerline."""
    items, _ = normalise(INKED)
    panels = items[0]["panels"]
    assert [p["widths"] for p in panels] == [[6.0], [9.0]]
    assert [len(p["fills"]) for p in panels] == [1, 1]


def test_a_panel_may_draw_only_fills_but_never_nothing():
    """The word mode's letter bodies are rings and only the connectors are
    strokes, so a panel with no polyline is legitimate — an empty one is not."""
    fills_only = [{"id": "S001", "w": 40, "h": 30, "img": PNG, "panels": [{"fills": [[[0, 0], [4, 0], [4, 4]]]}] * 2}]
    items, _ = normalise(fills_only)
    assert [sorted(p) for p in items[0]["panels"]] == [["fills"]] * 2
    # And the refusal names BOTH counts, because a ring too short to enclose
    # anything looks from the outside exactly like a missing stroke.
    with pytest.raises(ValueError, match=r"a stroke \(2\+ points\) or a ring \(3\+ points\)"):
        normalise([{"id": "S001", "w": 40, "h": 30, "img": PNG, "panels": [{"fills": [[[0, 0], [4, 0]]]}] * 2}])


def test_a_short_widths_array_is_refused():
    """It would silently ink the tail of a word at the wrong weight."""
    broken = copy.deepcopy(INKED)
    broken[0]["panels"][0]["strokes"].append([[1, 1], [2, 2]])
    with pytest.raises(ValueError, match="one per stroke or none"):
        normalise(broken)


def test_the_inked_payload_still_carries_nothing_but_geometry():
    raw = copy.deepcopy(INKED)
    raw[0]["arm"] = "LF11"
    raw[0]["panels"][0]["arm"] = "base"
    items, _ = normalise(raw)
    assert set(items[0]) == {"id", "w", "h", "img", "panels"}
    assert [sorted(p) for p in items[0]["panels"]] == [["fills", "strokes", "widths"]] * 2


def test_the_drawn_ink_is_never_inherited_from_the_item():
    """The two panels are being compared ON the ink; a panel that fell back to
    an item-level `strokes`/`fills` would draw the other arm's writing. Pinned
    on the emitted script, which cannot be imported."""
    html = build_page(INKED)
    for field in ("strokes", "widths", "fills"):
        assert re.search(rf"{field}: p\.{field} \|\| \[\]", html), f"{field} gained an item-level fallback"


@pytest.mark.parametrize("state", ["at", "seen", "notes", "spent", "spots", "answers", "picks"])
def test_every_answer_the_result_is_built_from_survives_a_reload(state):
    """Whatever the result file is assembled from has to be in `save()`.

    This is the round-1 bug, pinned so it cannot come back: that page wrote
    `{at, seen, notes, stamps, picks}` and its `restore()` read `raw.spots` —
    a field nothing ever stored. One reload therefore dropped every marker
    placed so far, silently, and the markers are the one part of the pass that
    is independent of our own numbers. The asymmetry is invisible while the tab
    stays open, which is exactly when nobody looks.
    """
    html = build_page(SINGLE)
    saved = re.search(r"localStorage\.setItem\(CONFIG\.store, JSON\.stringify\((\{.*?\})\)\)", html, re.S)
    restored = re.search(r"function restore\(\) \{(.*?)\n\}", html, re.S)
    assert saved and restored, "the resume machinery is no longer recognisable"
    assert re.search(rf"\b{state}\b", saved.group(1)), f"{state} is not written — a reload would drop it"
    assert re.search(rf"\b{state}\b", restored.group(1)), f"{state} is written but never read back"


# ------------------------------------------------------------------ blindness


def test_the_paired_payload_carries_nothing_but_geometry():
    """Which side is the new fit must not be readable off the page source."""
    items, _ = normalise(
        [
            {
                **PAIRED[0],
                "glyph": "a",
                "word": "das",
                "arm": "baseline",
                "panels": [{"strokes": [[[0, 0], [10, 10]]], "arm": "old"}, {"strokes": [[[2, 2], [12, 12]]]}],
            }
        ]
    )
    assert set(items[0]) == {"id", "w", "h", "img", "panels"}
    assert [set(p) for p in items[0]["panels"]] == [{"strokes"}, {"strokes"}]


def test_a_shared_crop_is_inlined_once():
    """Both panels draw on one image; inlining it twice would double the page."""
    items, _ = normalise(PAIRED)
    assert "img" in items[0] and all("img" not in p for p in items[0]["panels"])


def test_a_shared_pen_path_is_hoisted_like_the_crop():
    """It is the specimen's own measured path, identical for both panels."""
    raw = copy.deepcopy(PAIRED)
    raw[0]["context"] = [[[0, 0], [5, 5]]]
    items, _ = normalise(raw)
    assert items[0]["context"] == [[[0.0, 0.0], [5.0, 5.0]]]
    assert all("context" not in p for p in items[0]["panels"])


def test_panels_with_DIFFERENT_pen_paths_keep_their_own():
    """Hoisting the first would draw one panel's surroundings around the other —
    the same class of error as showing a letter without its connectors."""
    raw = copy.deepcopy(PAIRED)
    raw[0]["panels"][0]["context"] = [[[0, 0], [5, 5]]]
    raw[0]["panels"][1]["context"] = [[[9, 9], [1, 1]]]
    items, _ = normalise(raw)
    assert "context" not in items[0]
    assert [p["context"] for p in items[0]["panels"]] == [[[[0.0, 0.0], [5.0, 5.0]]], [[[9.0, 9.0], [1.0, 1.0]]]]


# ------------------------------------------------------------- self-containment


def test_the_page_loads_nothing_external():
    html = build_page(SINGLE)
    external = [u for u in re.findall(r"https?://[^\s\"')]+", html) if not u.startswith("http://www.w3.org/")]
    assert external == [], f"page reaches for {external}"
    assert "<script src" not in html and '<link rel="stylesheet"' not in html


def test_inline_script_cannot_be_closed_early_by_the_payload():
    """A payload string containing `</script>` must not end the inline script."""
    html = build_page([{**SINGLE[0], "id": "S</script>001"}])
    assert "</script>001" not in html


# ------------------------------------------------------------------ rejections


@pytest.mark.parametrize(
    "payload, message",
    [
        ([], "payload is empty"),
        ([{"w": 1, "h": 1, "img": PNG, "strokes": [[[0, 0], [1, 1]]]}], "needs a non-empty 'id'"),
        ([SINGLE[0], SINGLE[0]], "duplicate id"),
        ([{**SINGLE[0], "img": "https://example.invalid/x.png"}], "must not load anything external"),
        ([{**SINGLE[0], "strokes": [[[0, 0]]]}], "nothing drawable"),
        ([{**SINGLE[0], "w": 0}], "not drawable"),
        ([SINGLE[0], {**PAIRED[0], "id": "S002"}], "mixes one-panel and two-panel"),
    ],
)
def test_normalise_refuses_a_payload_that_would_mislead_the_judge(payload, message):
    with pytest.raises(ValueError, match=message):
        normalise(payload)
