"""Unit tests for the InkSight pipeline's pure parts (tools/inksight).

No TensorFlow anywhere: `run_inksight.py` is the only module that imports it
and cannot run in this environment at all (the repo needs Python >= 3.13,
tensorflow-text caps at 3.11). What IS testable is what the three stages agree
on across that process boundary — the token decode, the affine prepare writes
and to_candidate inverts, and the candidate contract the bench reads — and
those are exactly the places where a silent disagreement would show up as
"model error" in a measurement.
"""

from __future__ import annotations

import json

import pytest
from PIL import Image

from tools.inksight.prepare import (
    MODEL_SIZE,
    Affine,
    crop_to_model,
    grid_step_crop_px,
    model_to_crop,
    pad_to_model_frame,
    plan_affine,
    prepare_entry,
)
from tools.inksight.to_candidate import (
    CANDIDATE_FRAME,
    MAX_WORD_STROKES,
    build_row,
    derive_set_labels,
    registration_of,
    validate_strokes,
)
from tools.inksight.tokens import STROKE_START_TOKEN, TOKENS_PER_DIMENSION, decode_ink, tokens_to_strokes


def _ink(*tokens: int) -> str:
    return "".join(f"<ink_token_{t}>" for t in tokens)


# ------------------------------------------------------------- token decoding


def test_decode_reads_x_y_pairs_with_the_y_offset() -> None:
    # x = 10, y = 240 - 225 = 15; x = 20, y = 250 - 225 = 25.
    ink = decode_ink(_ink(STROKE_START_TOKEN, 10, 240, 20, 250))
    assert ink.strokes == [[[10.0, 15.0], [20.0, 25.0]]]
    assert ink.n_ink_tokens == 5
    assert ink.n_invalid_tokens == 0


def test_stroke_start_token_opens_a_new_stroke() -> None:
    ink = decode_ink(_ink(STROKE_START_TOKEN, 1, 226, 2, 227, STROKE_START_TOKEN, 3, 228, 4, 229))
    assert ink.strokes == [[[1.0, 1.0], [2.0, 2.0]], [[3.0, 3.0], [4.0, 4.0]]]
    # A leading start token must not produce an empty stroke.
    assert all(stroke for stroke in ink.strokes)


def test_grid_bounds_are_inclusive_at_both_ends() -> None:
    # x 0 / y 0 and x 224 / y 224 (the extreme legal tokens) both survive.
    strokes, invalid = tokens_to_strokes([0, TOKENS_PER_DIMENSION, 224, STROKE_START_TOKEN - 1])
    assert strokes == [[[0.0, 0.0], [224.0, 224.0]]]
    assert invalid == 0


def test_invalid_tokens_are_dropped_and_counted() -> None:
    # 999 is out of the vocabulary, the trailing 7 never gets its y token, and
    # a y token without a pending x is dropped as well.
    strokes, invalid = tokens_to_strokes([999, 300, 5, 230, 7])
    assert strokes == [[[5.0, 5.0]]]
    assert invalid == 3


def test_two_x_tokens_in_a_row_drop_the_stranded_one() -> None:
    strokes, invalid = tokens_to_strokes([5, 6, 231])
    assert strokes == [[[6.0, 6.0]]]
    assert invalid == 1


def test_recognized_text_is_the_answer_without_its_ink() -> None:
    ink = decode_ink("laden" + _ink(STROKE_START_TOKEN, 3, 228))
    assert ink.text_without_ink == "laden"
    assert ink.strokes == [[[3.0, 3.0]]]


# -------------------------------------------------------------------- affine


@pytest.mark.parametrize("size", [(300, 120), (120, 300), (224, 224), (1000, 61), (37, 41)])
def test_affine_round_trips_between_crop_and_model_frame(size: tuple[int, int]) -> None:
    crop_w, crop_h = size
    affine, _, _ = plan_affine(crop_w, crop_h)
    for x, y in ((0.0, 0.0), (crop_w / 2, crop_h / 3), (float(crop_w), float(crop_h)), (1.5, 2.5)):
        u, v = crop_to_model(x, y, affine)
        back_x, back_y = model_to_crop(u, v, affine)
        assert back_x == pytest.approx(x, abs=1e-9)
        assert back_y == pytest.approx(y, abs=1e-9)


def test_padding_puts_the_long_side_on_224_and_centres_the_short_one() -> None:
    padded, affine = pad_to_model_frame(Image.new("RGB", (300, 120), (0, 0, 0)))
    assert padded.size == (MODEL_SIZE, MODEL_SIZE)
    assert affine.dx == 0 and affine.dy > 0
    # The pad is white, the ink area is not.
    assert padded.getpixel((MODEL_SIZE // 2, 0)) == (255, 255, 255)
    assert padded.getpixel((MODEL_SIZE // 2, MODEL_SIZE // 2)) == (0, 0, 0)


def test_grid_step_is_clamped_at_one_crop_pixel() -> None:
    # A 448 px crop halves the token resolution; a small crop never claims
    # sub-pixel precision.
    assert grid_step_crop_px(448, 100) == pytest.approx(2.0)
    assert grid_step_crop_px(100, 80) == pytest.approx(1.0)


def test_prepare_entry_writes_the_input_and_its_frame_record(tmp_path) -> None:
    root = tmp_path / "fixtures"
    (root / "die").mkdir(parents=True)
    Image.new("RGB", (154, 86), (255, 255, 255)).save(root / "die" / "crop.png")
    (root / "die" / "word.json").write_text(
        json.dumps({"id": "die", "word": "die", "kind": "word", "rect": [838, 73, 992, 159]}), encoding="utf-8"
    )

    frame = prepare_entry(root, "die", tmp_path / "inputs")

    assert (tmp_path / "inputs" / "die.png").is_file()
    with Image.open(tmp_path / "inputs" / "die.png") as written:
        assert written.size == (MODEL_SIZE, MODEL_SIZE)
    assert frame["crop_w"] == 154 and frame["crop_h"] == 86
    assert frame["word"] == "die"
    assert frame["grid_step_crop_px"] == pytest.approx(1.0)


# --------------------------------------------------------- candidate contract


def _word_json() -> dict:
    # The real `die` entry: crop-local baseline 145 - 73 = 72, xh = 145 - 114 = 31.
    return {
        "id": "die",
        "word": "die",
        "kind": "word",
        "rect": [838, 73, 992, 159],
        "baseline_y": 145,
        "midband_y": 114,
    }


def _frame() -> dict:
    affine, _, _ = plan_affine(154, 86)
    return {
        "id": "die",
        "word": "die",
        "kind": "word",
        "crop_w": 154,
        "crop_h": 86,
        "ratio": affine.ratio,
        "scale_x": affine.scale_x,
        "scale_y": affine.scale_y,
        "dx": affine.dx,
        "dy": affine.dy,
        "grid_step_crop_px": 1.0,
    }


def _raw(strokes: list[list[list[float]]]) -> dict:
    return {
        "id": "die",
        "word": "die",
        "prompt": "Derender the ink.",
        "prompt_key": "derender",
        "recognized_text": None,
        "n_ink_tokens": 4 * sum(len(s) for s in strokes),
        "n_invalid_tokens": 0,
        "strokes_224": strokes,
    }


def test_registration_is_crop_local_with_zero_translation() -> None:
    registration, xh = registration_of(_word_json())
    assert registration == {"tx": 0, "ty": 0, "baseline_row": 72.0}
    assert xh == pytest.approx(31.0)


def test_build_row_maps_the_baseline_to_zero_and_the_midband_to_one() -> None:
    affine = Affine(**{k: _frame()[k] for k in ("ratio", "scale_x", "scale_y", "dx", "dy")})
    # Two crop points with known answers: the baseline at the crop's left edge
    # (0, 72) -> (0, 0), and the midband (0, 41) -> (0, 1).
    on_baseline = crop_to_model(0.0, 72.0, affine)
    on_midband = crop_to_model(0.0, 41.0, affine)

    row = build_row(_raw([[list(on_baseline), list(on_midband)]]), _frame(), _word_json())

    assert row["status"] == "ok"
    assert row["strokes"][0][0] == pytest.approx([0.0, 0.0], abs=1e-3)
    assert row["strokes"][0][1] == pytest.approx([0.0, 1.0], abs=1e-3)
    assert row["kind"] == "word"
    assert row["specimen_id"] == "die"
    assert row["xh_px"] == pytest.approx(31.0)
    assert row["meta"]["prompt"] == "Derender the ink."
    assert row["meta"]["grid_step_crop_px"] == 1.0
    assert "detail" not in row["meta"]


def test_a_single_point_stroke_fails_the_row_instead_of_being_cleaned_up() -> None:
    row = build_row(_raw([[[10.0, 10.0], [20.0, 20.0]], [[30.0, 30.0]]]), _frame(), _word_json())
    assert row["status"] == "failed"
    assert "stroke 1 has 1 point" in row["meta"]["detail"]
    # The offending geometry is kept — a failed row must stay inspectable.
    assert len(row["strokes"]) == 2


def test_an_empty_answer_fails_the_row() -> None:
    row = build_row(_raw([]), _frame(), _word_json())
    assert row["status"] == "failed"
    assert row["meta"]["detail"] == "no strokes decoded"


def test_validate_strokes_covers_the_wire_bounds() -> None:
    assert validate_strokes([[[0.0, 0.0], [1.0, 1.0]]]) is None
    assert "wire cap" in (validate_strokes([[[0.0, 0.0], [1.0, 1.0]]] * (MAX_WORD_STROKES + 1)) or "")
    assert "coordinate range" in (validate_strokes([[[0.0, 0.0], [101.0, 1.0]]]) or "")
    assert "not an [x, y] pair" in (validate_strokes([[[0.0, 0.0], [1.0, 1.0, 1.0]]]) or "")


def test_candidate_frame_literal_and_set_labels() -> None:
    from pathlib import Path

    assert CANDIDATE_FRAME == "word_registration"
    assert derive_set_labels(Path("tools/wordbench/fixtures/suetterlin/suetterlin-1922")) == (
        "suetterlin",
        "suetterlin-1922",
        "words",
    )
    assert derive_set_labels(Path("x/suetterlin/suetterlin-1922-pairs")) == ("suetterlin", "suetterlin-1922", "pairs")
