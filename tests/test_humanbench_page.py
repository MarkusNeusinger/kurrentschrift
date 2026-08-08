"""Unit tests for tools/humanbench/page.py.

The page is the instrument a human spends hours in, and its output is the only
part of the chain that cannot be recomputed. So the tests here guard the two
things that would waste those hours: the payload must stay blind, and the
result file the page emits must be one the analyser can actually read back.

Everything is synthetic — a real payload carries occurrence geometry, which
stays out of this repo (``docs/reference/quellen-und-rechte.md`` §5).
"""

from __future__ import annotations

import re

import pytest

from tools.humanbench.analyse import RESULT_HEAD, parse_result
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
        ([{**SINGLE[0], "strokes": [[[0, 0]]]}], "no drawable stroke"),
        ([{**SINGLE[0], "w": 0}], "not drawable"),
        ([SINGLE[0], {**PAIRED[0], "id": "S002"}], "mixes one-panel and two-panel"),
    ],
)
def test_normalise_refuses_a_payload_that_would_mislead_the_judge(payload, message):
    with pytest.raises(ValueError, match=message):
        normalise(payload)
