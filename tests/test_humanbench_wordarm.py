"""Unit tests for tools/humanbench/wordarm.py — the arm producer.

The fixture-walking half needs a word bench root, which is gitignored learned
data (quellen-und-rechte.md §5) and cannot exist in CI. What CAN be checked
here is everything that decides what a judge ends up looking at: that a
composed word turns into the ink the page draws, that the file the producer
writes is the file the BUILDER accepts, that pinning a registration does what
it claims, and that the synthetic defect is the size it says it is.

The round-trip is the important one. Producer and consumer sit on opposite
sides of a JSON contract, and a contract nothing crosses in a test is a
contract that drifts — the first time anyone notices would be a round that
draws half a word after the hours are already booked.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from tools.humanbench import wordarm
from tools.humanbench.build import load_arm
from tools.humanbench.wordarm import ZIGZAG_AMPLITUDE, arm_drawing, load_laufform_draft, pin_registration, zigzag


REGISTRATION = {"xh_px": 31.0, "tx": 10.0, "ty": 1.0}

# One composed word as `compose_word` returns it: a letter body carrying its
# silhouette rings, and a generated connector carrying a constant width.
COMPOSED = {
    "items": [
        {
            "centerline": [[0.0, 0.0], [0.5, 1.0], [1.0, 0.0]],
            # A loop glyph's silhouette: the exterior plus the counter it
            # encloses — what `compose_word` ships for a `Z`, `e` or `l`.
            "rings": [
                [[0.0, 0.1], [1.0, 0.1], [1.0, -0.1], [0.0, -0.1]],
                [[0.3, 0.05], [0.6, 0.05], [0.6, -0.05], [0.3, -0.05]],
            ],
            "mask_width": 0.19,
        },
        {"centerline": [[1.0, 0.0], [1.4, 0.3], [1.8, 0.0]], "stroke_width": 0.145, "lift": False},
    ]
}


def test_arm_drawing_ships_bodies_as_ink_and_connectors_as_capsules():
    """A hairline shows neither a zigzag nor a stroke a quarter too thin, so
    the body travels as its silhouette and the connector as its own width."""
    drawn = arm_drawing(COMPOSED, REGISTRATION)
    assert drawn["registration"] == {"xh_px": 31.0, "tx": 10.0, "ty": 1.0}
    # ONE shape for the pen stroke, carrying both of its rings: the grouping is
    # the only thing that says the second ring is a HOLE. Flattened, the loop
    # interior is painted solid and the writing reads as a blob.
    assert len(drawn["fills"]) == 1
    assert [len(ring) for ring in drawn["fills"][0]] == [4, 4]
    assert len(drawn["strokes"]) == 1
    assert drawn["strokes"][0]["width"] == pytest.approx(0.145)
    # The body's centerline is NOT drawn a second time — the silhouette is the ink.
    assert drawn["strokes"][0]["points"][0] == [1.0, 0.0]


def test_a_body_without_rings_falls_back_to_its_own_centerline():
    """A template with no outline still has to reach the screen; it just
    arrives as a stroke rather than as a filled shape."""
    bare = {"items": [{"centerline": [[0.0, 0.0], [1.0, 1.0]]}]}
    drawn = arm_drawing(bare, REGISTRATION)
    assert drawn["fills"] == []
    assert drawn["strokes"][0]["width"] == 0.0  # no width known -> the page's hairline


def test_what_the_producer_writes_is_what_the_builder_reads(tmp_path):
    """The contract seam, crossed once: producer and consumer are two modules
    either side of a JSON file, and nothing else checks that they agree."""
    path = tmp_path / "arm.json"
    path.write_text(json.dumps({"arm": "LF11", "words": {"unter": arm_drawing(COMPOSED, REGISTRATION)}}))
    arm = load_arm(path)
    assert arm.name == "LF11"
    word = arm.words["unter"]
    assert (word.xh, word.tx, word.ty) == (31.0, 10.0, 1.0)
    assert len(word.strokes) == 1 and word.strokes[0].width == pytest.approx(0.145)
    assert len(word.fills) == 1


def test_pinning_a_registration_takes_the_other_arm_s_and_names_what_it_lacks():
    """A candidate that sits systematically lower is readable as a group even
    though the seed randomises the sides — so a mechanism that does not move
    the placement borrows the base's instead of searching its own."""
    words = {"unter": arm_drawing(COMPOSED, REGISTRATION), "das": arm_drawing(COMPOSED, REGISTRATION)}
    reference = {"unter": {"registration": {"xh_px": 33.0, "tx": 4.0, "ty": -2.0}}}
    missing = pin_registration(words, reference)
    assert words["unter"]["registration"] == {"xh_px": 33.0, "tx": 4.0, "ty": -2.0}
    assert missing == ["das"]  # reported, not silently left at its own placement
    assert words["das"]["registration"] == REGISTRATION


def test_the_synthetic_zigzag_is_the_size_it_claims_and_alternates_sides():
    """It stands in for the anchor-median saw-tooth of a Laufform row — a few
    hundredths of an x-height, which is exactly what the rulers resample away.
    Applied to the drawn ink, because that is what a human sees."""
    words = {"unter": arm_drawing(COMPOSED, REGISTRATION)}
    before = np.asarray(words["unter"]["fills"][0][0], dtype=float)
    zigzag(words)
    after = np.asarray(words["unter"]["fills"][0][0], dtype=float)
    # The shape grouping survives the injection — a counter that lost its
    # exterior would be drawn as a solid blob.
    assert [len(ring) for ring in words["unter"]["fills"][0]] == [4, 4]
    offsets = np.hypot(*(after - before).T)
    # Tolerance is the file's own display precision (six decimals), not slack.
    assert offsets == pytest.approx(np.full(len(before), ZIGZAG_AMPLITUDE), abs=1e-5)
    # Successive vertices are pushed to OPPOSITE sides, which is what makes it
    # a saw-tooth rather than a fattened outline.
    deltas = after - before
    assert np.dot(deltas[0], deltas[1]) < 0
    assert words["unter"]["strokes"][0]["points"] != COMPOSED["items"][1]["centerline"]


def test_a_path_too_short_to_have_a_direction_is_left_alone():
    two_points = {"w": {"registration": REGISTRATION, "strokes": [{"points": [[0.0, 0.0], [1.0, 0.0]]}], "fills": []}}
    zigzag(two_points)
    assert two_points["w"]["strokes"][0]["points"] == [[0.0, 0.0], [1.0, 0.0]]


def test_load_laufform_draft_accepts_both_shapes_the_word_bench_accepts(tmp_path):
    """A harvest draft and a full fixture row set are both legitimate inputs,
    so the arm producer takes whichever the candidate happens to live in."""
    flat = tmp_path / "flat.json"
    flat.write_text(json.dumps({"e": {"anchors": [[0, 0]]}}))
    nested = tmp_path / "nested.json"
    nested.write_text(json.dumps({"rows": {"e": {"anchors": [[0, 0]]}}}))
    assert load_laufform_draft(flat) == load_laufform_draft(nested)
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps([1, 2, 3]))
    with pytest.raises(SystemExit, match="mapping glyph_key"):
        load_laufform_draft(broken)


# ------------------------------------------------- the arm switches reach compose
#
# Every candidate the instrument can judge today is a knob the composition path
# already has. The failure mode of adding one is not that it computes the wrong
# thing — it is that the flag is parsed, printed into the settings, and never
# handed to `compose_word`, so the round compares the base against itself and
# says „kein Unterschied" 63 times, and nothing about the run looks wrong.
#
# Two levels, because one alone would not catch it. The CLI test below stops at
# `compose_arm`; the ones after it run the REAL `compose_arm` over a stand-in
# root and capture the call `compose_word` actually receives. The real roots are
# gitignored learned data (quellen-und-rechte.md §5), so the root is synthetic —
# but the forwarding under test is not.


def stand_in_root(tmp_path):
    """The three files `compose_arm` reads, and nothing else.

    `compose_word` and `score_word` are captured by the caller, so the geometry
    in here never has to be real — only the shape has to be.
    """
    root = tmp_path / "suetterlin-1922"
    (root / "unter").mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "style_ratio": [1, 1, 1],
                "width_resolver": "constant",
                "constant_nib_units": 0.07251,
                "exported_at": "2026-09-02T22:16:06+00:00",
                "words": [{"id": "unter", "word": "unter", "scorable": True}],
            }
        )
    )
    (root / "templates.json").write_text(json.dumps({"u": {"anchors": [[0, 0]]}}))
    (root / "templates_laufform.json").write_text(json.dumps({}))
    (root / "unter" / "word.json").write_text(
        json.dumps(
            {
                "rect": [0, 0, 120, 60],
                "baseline_y": 40,
                "midband_y": 20,
                "slots": [{"key": "u", "text": "u", "position": "initial", "ligature": False, "space": False}],
            }
        )
    )
    np.savez(root / "unter" / "ref_skel.npz", skel=np.zeros((60, 120), dtype=bool))
    return root


@pytest.mark.parametrize("switch, expected", [({}, False), ({"exit_trim": True}, True)])
def test_compose_arm_hands_exit_trim_to_compose_word(tmp_path, monkeypatch, switch, expected):
    """The forwarding itself, not the parsing: delete `exit_trim=exit_trim` from
    the `compose_word` call and this is the test that goes red."""
    calls: list[dict] = []

    def fake_compose(slots, payloads, **kwargs):
        calls.append(kwargs)
        return {"items": COMPOSED["items"], "missing": []}

    monkeypatch.setattr(wordarm, "compose_word", fake_compose)
    monkeypatch.setattr(wordarm, "score_word", lambda *a, **k: {"registration": REGISTRATION})
    monkeypatch.setattr(wordarm, "render_payload_for_template", lambda *a, **k: {"anchors": []})

    words, settings = wordarm.compose_arm(stand_in_root(tmp_path), **switch)
    assert list(words) == ["unter"], settings["failed"]
    assert calls and calls[0]["exit_trim"] is expected
    assert settings["exit_trim"] is expected


def test_compose_arm_hands_the_nib_to_the_resolver(tmp_path, monkeypatch):
    """The nib reaches the payloads, not just the settings line."""
    seen: list = []
    monkeypatch.setattr(wordarm, "compose_word", lambda *a, **k: {"items": COMPOSED["items"], "missing": []})
    monkeypatch.setattr(wordarm, "score_word", lambda *a, **k: {"registration": REGISTRATION})
    monkeypatch.setattr(
        wordarm, "render_payload_for_template", lambda row, ratio, resolver, nib: seen.append(nib) or {"anchors": []}
    )
    _words, settings = wordarm.compose_arm(stand_in_root(tmp_path), nib=0.097)
    assert seen and set(seen) == {0.097}
    assert settings["nib_units"] == 0.097 and settings["nib_overridden"] is True


def _settings(**kwargs) -> dict:
    """What `compose_arm` reports back, as the CLI's summary line expects it."""
    return {
        "nib_units": kwargs.get("nib") or 0.07251,
        "nib_overridden": kwargs.get("nib") is not None,
        "laufform": "frozen",
        "exit_trim": kwargs.get("exit_trim", False),
        "failed": [],
    }


def _capture_compose_arm(monkeypatch):
    seen: dict = {}

    def fake(root, **kwargs):
        seen.update(kwargs)
        seen["root"] = root
        return ({"unter": arm_drawing(COMPOSED, REGISTRATION)}, _settings(**kwargs))

    monkeypatch.setattr(wordarm, "compose_arm", fake)
    return seen


@pytest.mark.parametrize(
    "argv, expected",
    [
        ([], {"exit_trim": False, "nib": None, "no_laufform": False}),
        (["--exit-trim"], {"exit_trim": True}),
        (["--nib", "0.097"], {"nib": 0.097}),
        (["--no-laufform"], {"no_laufform": True}),
    ],
)
def test_every_arm_switch_reaches_the_composer(tmp_path, monkeypatch, argv, expected):
    seen = _capture_compose_arm(monkeypatch)
    wordarm.main(["--arm", "X", "--out", str(tmp_path / "arm.json"), *argv])
    for key, value in expected.items():
        assert seen[key] == value, f"--{key.replace('_', '-')} never reached compose_word"


def test_the_arm_file_records_the_switch_it_was_composed_with(tmp_path, monkeypatch):
    """The stamp copies the arm's settings, and „which knob was on" is the one
    thing a round cannot reconstruct from the drawn geometry afterwards."""
    _capture_compose_arm(monkeypatch)
    out = tmp_path / "j4.json"
    wordarm.main(["--arm", "J4", "--exit-trim", "--out", str(out)])
    written = json.loads(out.read_text())
    assert written["settings"]["exit_trim"] is True
    assert written["arm"] == "J4"
