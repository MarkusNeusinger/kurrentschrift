"""Unit tests for the rect repair that re-encloses clipped specimen ink.

Synthetic plates, no committed data: each case is one drawn shape whose right
answer a reader can see in the numbers. What has to hold, because every one of
these was a wrong repair the tool proposed before the rule existed:

* a diacritic sliced by the top edge pulls the edge out — that is the whole
  point (the cut i-Strich of „einer", the cut u-Bogen of „zum");
* a comma trailing the last letter never does, however close it sits: the
  stored `word` carries letters only, and the first pass proposed four
  right-edge repairs that were all commas;
* ink from the neighbouring line never does either, whether it floats above
  the rect (foxing, bleed-through) or dips into it (a descender);
* a rect whose ink already has the plate's standard clearance is left BYTE for
  byte alone — every rect this tool touches is a fixture and a stored trace
  registration that has to move with it.
"""

from __future__ import annotations

import json

import numpy as np
from PIL import Image

from tools.wordbench import repair_boxes, shift_registrations


# The synthetic plate's lineature, chosen like the real Abb. 19: x-height 30 px.
MIDBAND, BASELINE = 130, 160
XH = BASELINE - MIDBAND


def _plate(tmp_path, shapes: list[tuple[int, int, int, int, int]], name="plate.png"):
    """A white page with black boxes: (x0, y0, x1, y1, gray)."""
    arr = np.full((400, 500), 255, dtype=np.uint8)
    for x0, y0, x1, y1, gray in shapes:
        arr[y0:y1, x0:x1] = gray
    Image.fromarray(arr, mode="L").save(tmp_path / name)
    return tmp_path / name


def _entry(rect, **extra):
    x0, y0, x1, y1 = rect
    return {
        "word": "probe",
        "page": "plate.png",
        "x0": x0,
        "y0": y0,
        "x1": x1,
        "y1": y1,
        "baseline_y": BASELINE,
        "midband_y": MIDBAND,
        **extra,
    }


def _sidecar(tmp_path, entries: list[dict]) -> None:
    (tmp_path / "words.json").write_text(json.dumps({"words": entries}), encoding="utf-8")


def _plan(src, monkeypatch, shapes, entries):
    _plate(src, shapes)
    _sidecar(src, entries)
    # plan_repairs resolves REPO_ROOT/data/sources/<id>/, and `src` IS that
    # directory — so the root is three levels up.
    monkeypatch.setattr(repair_boxes, "REPO_ROOT", src.parent.parent.parent)
    return repair_boxes.plan_repairs(src.name)


def _dirs(tmp_path):
    """A data/sources/<id>/ layout whose <id> directory is tmp_path itself."""
    src = tmp_path / "data" / "sources" / "plate-src"
    src.mkdir(parents=True)
    return src


# The word body: a solid bar across the x-height band, dark ink.
BODY = (150, MIDBAND, 300, BASELINE, 30)


def test_repairs_a_diacritic_cut_by_the_top_edge(tmp_path, monkeypatch):
    src = _dirs(tmp_path)
    dot = (200, MIDBAND - 25, 214, MIDBAND - 13, 30)  # floats above the body
    # The rect starts BELOW the dot's top: the mark is sliced, exactly the
    # committed „einer" case.
    repairs, refused = _plan(src, monkeypatch, [BODY, dot], [_entry((147, MIDBAND - 20, 303, BASELINE + 3))])
    assert not refused
    assert len(repairs) == 1
    r = repairs[0]
    assert r.new[1] == dot[1] - repair_boxes.PAD_PX  # top pulled out to clear the mark
    assert r.new[0::2] == r.old[0::2]  # the sides it did not need to move stay put
    # The correction a stored trace must follow is the origin's own shift.
    assert r.registration_shift == (0, r.old[1] - r.new[1])


def test_leaves_a_rect_with_standard_clearance_alone(tmp_path, monkeypatch):
    src = _dirs(tmp_path)
    pad = repair_boxes.MIN_CLEARANCE_PX
    rect = (BODY[0] - pad, BODY[1] - pad, BODY[2] + pad, BODY[3] + pad)
    repairs, refused = _plan(src, monkeypatch, [BODY], [_entry(rect)])
    assert (repairs, refused) == ([], [])


def test_never_grows_over_trailing_punctuation(tmp_path, monkeypatch):
    src = _dirs(tmp_path)
    # A comma: below the Mittellinie, just past the last letter — and here it
    # even overlaps the body's rows, which is why "sits beside the word" was
    # not enough of a rule.
    comma = (306, BASELINE - 6, 318, BASELINE + 10, 30)
    repairs, _ = _plan(src, monkeypatch, [BODY, comma], [_entry((147, MIDBAND - 3, 303, BASELINE + 3))])
    assert all(r.new[2] <= 303 for r in repairs), "the rect grew out over the comma"


def test_ignores_ink_from_the_neighbouring_line(tmp_path, monkeypatch):
    src = _dirs(tmp_path)
    # A descender from the line above: starts far above this line's ascender
    # zone and dips into the rect, so most of it is INSIDE — the majority test
    # alone would have adopted it.
    descender = (200, MIDBAND - 90, 210, MIDBAND + 20, 30)
    repairs, _ = _plan(src, monkeypatch, [BODY, descender], [_entry((147, MIDBAND - 3, 303, BASELINE + 3))])
    assert all(r.new[1] >= MIDBAND - repair_boxes.ASCENDER_XH * XH for r in repairs)


def test_ignores_pale_bleed_through(tmp_path, monkeypatch):
    src = _dirs(tmp_path)
    # Diacritic-shaped and inside the ascender zone, but far paler than the
    # word's own stroke: foxing or a verso ghost, not this word's mark.
    ghost = (200, MIDBAND - 25, 214, MIDBAND - 13, 205)
    repairs, refused = _plan(src, monkeypatch, [BODY, ghost], [_entry((147, MIDBAND - 3, 303, BASELINE + 3))])
    assert (repairs, refused) == ([], [])


def test_refuses_a_growth_beyond_one_x_height(tmp_path, monkeypatch):
    src = _dirs(tmp_path)
    # Punctuation FUSED to the last letter's exit stroke (the committed
    # „regieren" case): one component, so no positional rule separates it —
    # the cap is what stops the box from swallowing it. Reported, never applied.
    fused = (150, BASELINE - 6, 360, BASELINE, 30)
    repairs, refused = _plan(src, monkeypatch, [BODY, fused], [_entry((147, MIDBAND - 3, 303, BASELINE + 3))])
    assert repairs == []
    assert [r.sample_id for r in refused] == ["probe"]


def test_apply_touches_only_the_rect(tmp_path, monkeypatch):
    src = _dirs(tmp_path)
    dot = (200, MIDBAND - 25, 214, MIDBAND - 13, 30)
    entry = _entry((147, MIDBAND - 20, 303, BASELINE + 3), id="probe", exclude=[[1, 2, 3, 4]], note="keep me")
    repairs, _ = _plan(src, monkeypatch, [BODY, dot], [entry])
    repair_boxes.apply_repairs(src.name, repairs)
    stored = json.loads((src / "words.json").read_text(encoding="utf-8"))["words"][0]
    assert stored["y0"] == repairs[0].new[1]
    # Page-coordinate lineature does not move with the crop origin, and the
    # entry's other hand-maintained fields survive the rewrite untouched.
    assert (stored["baseline_y"], stored["midband_y"]) == (BASELINE, MIDBAND)
    assert (stored["exclude"], stored["note"]) == ([[1, 2, 3, 4]], "keep me")


# ------------------------------- the other half: traces move with their crop


def _trace(specimen_id="probe", baseline_row=60.0, tx=4.0, **extra):
    return {
        "kind": "word",
        "specimen_id": specimen_id,
        "word": "probe",
        "slots": ["p"],
        "strokes": [[[0, 0], [1, 1]]],
        "provenance": "authored",
        "measurements": {"registration_px": {"tx": tx, "ty": 0.0, "baseline_row": baseline_row}, **extra},
    }


SHIFT = {"probe": {"dx": 0, "dy": 11}}
# Crop-local Grundlinie before and after the rect grew 11 px upward.
ROWS = {"probe": (60, 71)}


def test_shift_moves_a_trace_left_behind_by_the_repair():
    todo = shift_registrations.plan([_trace(baseline_row=60.0)], SHIFT, ROWS)
    assert len(todo) == 1
    moved = shift_registrations.shifted(todo[0], SHIFT)
    assert moved["measurements"]["registration_px"]["baseline_row"] == 71.0
    # An authored row stays authored: coercing it to `traced` would hand the
    # author's own pen work to the next harvest to overwrite.
    assert moved["provenance"] == "authored"


def test_shift_is_idempotent():
    """A row already sitting in the repaired crop is left alone — running the
    correction twice must not double-shift it."""
    assert shift_registrations.plan([_trace(baseline_row=71.0)], SHIFT, ROWS) == []


def test_shift_skips_rows_of_untouched_specimens_and_rows_without_registration():
    rows = [_trace(specimen_id="other", baseline_row=60.0), {**_trace(), "measurements": {}}]
    assert shift_registrations.plan(rows, SHIFT, ROWS) == []
