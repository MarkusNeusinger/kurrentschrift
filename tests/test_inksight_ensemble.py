"""Unit tests for the InkSight best-of-N ensemble (tools/inksight, measure B1).

No TensorFlow anywhere — the model stage is untestable in this environment by
construction (`tests/test_inksight_pipeline.py` says why), so what is pinned here
is everything the ensemble decides WITHOUT the model:

* the augmented affine chain, in both directions and through the JSON sidecar —
  an inversion that is off by a pixel would be reported as model error;
* the variant list, which must be a named deterministic grid rather than a draw,
  or a measurement cannot be re-derived from its manifest;
* the ranker's ORDER on synthetic paths, including the rule that a contract
  violation is disqualified rather than crashed on — and that a disqualified
  variant loses even when its geometry ranks best;
* the candidate contract the bench reads, and that the winner travels unchanged.

The ranker's target is the MEASURED INK (`ref_skel.npz`), never a reference
trace. That is the property the whole measure stands on, so the fixtures here
carry a skeleton and nothing that could be mistaken for a hand trace.
"""

from __future__ import annotations

import json

import numpy as np
import pytest
from PIL import Image

from tools.inksight.augment import (
    DEFAULT_MANIFEST_NAME,
    DEFAULT_ROTATIONS,
    DEFAULT_SCALES,
    IDENTITY_VARIANT,
    crop_to_model_px,
    model_to_crop_px,
    plan_variant,
    prepare_variants,
    render_variant,
    variant_frame_of,
    variant_grid,
    variant_name,
    variant_record,
)
from tools.inksight.augment import main as augment_main
from tools.inksight.ensemble import (
    INK_MASK_FILE,
    SKELETON_FILE,
    TOOL_NAME,
    build_ensemble_row,
    build_variant_row,
    evaluate_variant,
    load_ink_points,
    rank_against_ink,
    rank_points,
)
from tools.inksight.prepare import MODEL_SIZE, grid_step_crop_px, pad_to_model_frame, plan_affine
from tools.inksight.to_candidate import CANDIDATE_FRAME, MAX_ABS_COORD


CROP_W, CROP_H = 224, 112
# The synthetic entry's lineature: baseline 80 crop px below the crop top,
# midband one x-height (20 px) above it.
BASELINE_Y, MIDBAND_Y = 80.0, 60.0
XH = BASELINE_Y - MIDBAND_Y


# ------------------------------------------------------------- the variant grid


def test_the_grid_is_a_named_deterministic_list() -> None:
    first = variant_grid()
    second = variant_grid()
    assert first == second
    assert len(first) == len(DEFAULT_ROTATIONS) * len(DEFAULT_SCALES) == 10
    names = [variant_name(rot, scale) for rot, scale in first]
    assert len(set(names)) == len(names)
    # The identity member exists and comes FIRST, so a run cut short still has
    # the plain baseline and a tie can only ever be won by it.
    assert names[0] == IDENTITY_VARIANT
    assert first[0] == (0.0, 1.0)


def test_variant_names_are_file_safe_and_readable() -> None:
    assert variant_name(0.0, 1.0) == "rot+0_s100"
    assert variant_name(-4.0, 0.92) == "rot-4_s092"
    assert variant_name(2.5, 1.0) == "rot+2p5_s100"
    assert all(char not in variant_name(-2.0, 0.92) for char in "./\\ ")


def test_a_colliding_grid_is_refused_rather_than_silently_shrunk() -> None:
    # Two scales that round to the same name would overwrite one another's PNG
    # AND one another's answer — the ensemble would quietly lose a member.
    with pytest.raises(ValueError, match="collide"):
        variant_grid((0.0,), (1.0, 0.999))


# -------------------------------------------------------------- the affine chain


@pytest.mark.parametrize("crop", [(300, 120), (120, 300), (224, 224), (154, 86), (37, 41)])
@pytest.mark.parametrize("member", [(0.0, 1.0), (-4.0, 1.0), (2.0, 0.92), (4.0, 0.92)])
def test_the_chain_round_trips_between_crop_and_model_frame(crop, member) -> None:
    crop_w, crop_h = crop
    frame = plan_variant(crop_w, crop_h, *member)
    for x, y in ((0.0, 0.0), (crop_w / 2, crop_h / 3), (float(crop_w), float(crop_h)), (1.5, 2.5)):
        u, v = crop_to_model_px(x, y, frame)
        back_x, back_y = model_to_crop_px(u, v, frame)
        assert back_x == pytest.approx(x, abs=1e-9)
        assert back_y == pytest.approx(y, abs=1e-9)


@pytest.mark.parametrize("member", [(0.0, 1.0), (-2.0, 1.0), (4.0, 0.92)])
def test_the_chain_survives_the_json_sidecar(member) -> None:
    frame = plan_variant(CROP_W, CROP_H, *member)
    # Exactly the trip the manifest makes: dataclass → record → JSON → record.
    record = json.loads(json.dumps(variant_record(frame, "x.png")))
    restored = variant_frame_of(record)
    assert restored == frame
    for x, y in ((0.0, 0.0), (100.0, 50.0), (float(CROP_W), float(CROP_H))):
        assert crop_to_model_px(x, y, restored) == pytest.approx(crop_to_model_px(x, y, frame), abs=1e-12)
        u, v = crop_to_model_px(x, y, restored)
        assert model_to_crop_px(u, v, restored) == pytest.approx((x, y), abs=1e-9)


@pytest.mark.parametrize("degrees", [-4.0, -2.0, 0.0, 2.0, 4.0])
def test_the_rotation_box_holds_the_whole_crop(degrees) -> None:
    frame = plan_variant(CROP_W, CROP_H, degrees, 1.0)
    rotation = frame.rotation
    corners = ((0.0, 0.0), (CROP_W, 0.0), (CROP_W, CROP_H), (0.0, CROP_H))
    for x, y in corners:
        u, v = crop_to_model_px(x, y, frame)
        # Every corner lands inside the model frame, i.e. the turn does not push
        # ink off the input the model is shown.
        assert -1e-9 <= u <= MODEL_SIZE + 1e-9
        assert -1e-9 <= v <= MODEL_SIZE + 1e-9
    assert rotation.width >= CROP_W if degrees else rotation.width == CROP_W
    assert rotation.height >= CROP_H if degrees else rotation.height == CROP_H


def test_the_identity_member_is_the_plain_pipeline_byte_for_byte() -> None:
    crop = Image.effect_noise((CROP_W, CROP_H), 40).convert("RGB")
    plain, affine = pad_to_model_frame(crop)
    frame = plan_variant(CROP_W, CROP_H, 0.0, 1.0)
    assert frame.is_identity
    assert frame.affine == affine
    assert render_variant(crop, frame).tobytes() == plain.tobytes()


def test_the_grid_step_is_the_plain_number_for_the_identity_and_coarser_below_it() -> None:
    identity = plan_variant(448, 100, 0.0, 1.0)
    affine, _, _ = plan_affine(448, 100)
    assert grid_step_crop_px(identity.affine) == pytest.approx(grid_step_crop_px(affine))
    # A smaller fill factor spends fewer model pixels on the same crop, so one
    # token step covers MORE crop pixels — the resolution floor gets worse.
    shrunk = plan_variant(448, 100, 0.0, 0.92)
    assert grid_step_crop_px(shrunk.affine) > grid_step_crop_px(identity.affine)


# --------------------------------------------------------------- the ink ranker


def _ink_column(x: int, y0: int = 10, y1: int = 60) -> np.ndarray:
    """A one-pixel-wide vertical ink column as a crop-pixel point cloud."""
    return np.array([[float(x), float(y)] for y in range(y0, y1 + 1)], dtype=float)


def test_rank_points_resamples_along_the_line_and_never_bridges_a_lift() -> None:
    cloud = rank_points([[[0.0, 0.0], [10.0, 0.0]], [[50.0, 0.0], [52.0, 0.0]]], step=1.0)
    assert len(cloud) == 11 + 3
    # Nothing between the two strokes: the gap is a pen lift, not ink.
    assert not ((cloud[:, 0] > 10.0) & (cloud[:, 0] < 50.0)).any()


def test_the_closer_path_wins() -> None:
    ink = _ink_column(100)
    on_ink = rank_against_ink([[[100.0, 10.0], [100.0, 60.0]]], ink, XH)
    beside_ink = rank_against_ink([[[105.0, 10.0], [105.0, 60.0]]], ink, XH)
    assert on_ink["rank_sum_xh"] < beside_ink["rank_sum_xh"]
    assert on_ink["rank_sum_xh"] == pytest.approx(0.0, abs=1e-6)
    assert beside_ink["chamfer_cand_ink_xh"] == pytest.approx(5.0 / XH, abs=1e-3)


def test_the_two_halves_are_kept_apart_so_a_half_written_word_shows_up() -> None:
    # Ink is two columns; the candidate writes only the left one. Everything it
    # drew is on ink (first half ~0), but half the ink has nothing near it.
    ink = np.vstack([_ink_column(20), _ink_column(120)])
    half = rank_against_ink([[[20.0, 10.0], [20.0, 60.0]]], ink, XH)
    assert half["chamfer_cand_ink_xh"] == pytest.approx(0.0, abs=1e-6)
    assert half["chamfer_ink_cand_xh"] > 2.0
    assert half["rank_sum_xh"] == pytest.approx(half["chamfer_cand_ink_xh"] + half["chamfer_ink_cand_xh"])


def test_an_empty_answer_is_unrankable_rather_than_perfect() -> None:
    ranks = rank_against_ink([], _ink_column(100), XH)
    assert np.isinf(ranks["rank_sum_xh"])


def test_load_ink_points_prefers_the_skeleton_and_falls_back_to_the_mask(tmp_path) -> None:
    entry = tmp_path / "wort"
    entry.mkdir()
    skel = np.zeros((10, 10), dtype=bool)
    skel[5, 2:8] = True
    mask = np.zeros((10, 10), dtype=bool)
    mask[4:7, 2:8] = True
    Image.fromarray(np.where(mask, 255, 0).astype(np.uint8)).save(entry / INK_MASK_FILE)
    with pytest.raises(FileNotFoundError):
        load_ink_points(tmp_path / "nothing")

    points, source = load_ink_points(entry)
    assert source == INK_MASK_FILE
    assert len(points) == int(mask.sum())

    np.savez_compressed(entry / SKELETON_FILE, skel=skel, width_map=skel.astype(np.float32))
    points, source = load_ink_points(entry)
    assert source == SKELETON_FILE
    assert len(points) == int(skel.sum())
    # (x, y) crop pixels, not (row, col).
    assert points[:, 1].tolist() == [5.0] * 6


# ------------------------------------------------- selection + candidate contract


def _word_json() -> dict:
    return {
        "id": "wort",
        "word": "wort",
        "kind": "word",
        "rect": [10, 20, 10 + CROP_W, 20 + CROP_H],
        "baseline_y": 20.0 + BASELINE_Y,
        "midband_y": 20.0 + MIDBAND_Y,
    }


def _frame_record(names: list[str]) -> dict:
    return {
        "id": "wort",
        "word": "wort",
        "kind": "word",
        "crop_w": CROP_W,
        "crop_h": CROP_H,
        "variants": {name: {} for name in names},
    }


def _registration() -> dict:
    return {"tx": 0, "ty": 0, "baseline_row": BASELINE_Y}


def _raw(strokes_crop: list[list[list[float]]], frame) -> dict:
    """A raw answer whose model-frame strokes decode back to these crop points."""
    return {
        "id": "wort",
        "word": "wort",
        "prompt": "Derender the ink.",
        "prompt_key": "derender",
        "recognized_text": None,
        "n_ink_tokens": 4 * sum(len(s) for s in strokes_crop),
        "n_invalid_tokens": 0,
        "strokes_224": [[list(crop_to_model_px(x, y, frame)) for x, y in stroke] for stroke in strokes_crop],
    }


def _evaluation(strokes_crop, member, ink, order: int) -> dict:
    frame = plan_variant(CROP_W, CROP_H, *member)
    record = variant_record(frame, f"wort.{frame.name}.png")
    return evaluate_variant(_raw(strokes_crop, frame), record, _registration(), XH, ink, order)


def test_a_variant_is_inverted_through_its_own_chain() -> None:
    ink = _ink_column(100)
    # The same crop-pixel line, decoded from two different variants: both must
    # land on the same word-unit geometry, or the inversion is variant-blind.
    straight = _evaluation([[[100.0, 10.0], [100.0, 60.0]]], (0.0, 1.0), ink, 0)
    turned = _evaluation([[[100.0, 10.0], [100.0, 60.0]]], (4.0, 0.92), ink, 1)
    assert np.allclose(straight["strokes"][0], turned["strokes"][0], atol=1e-3)
    assert straight["rank_sum_xh"] == pytest.approx(turned["rank_sum_xh"], abs=1e-3)
    # Baseline → 0, midband → 1 (the stored word frame).
    on_baseline = _evaluation([[[0.0, BASELINE_Y], [0.0, MIDBAND_Y]]], (0.0, 1.0), ink, 0)
    assert on_baseline["strokes"][0][0] == pytest.approx([0.0, 0.0], abs=1e-3)
    assert on_baseline["strokes"][0][1] == pytest.approx([0.0, 1.0], abs=1e-3)


def test_the_best_ranked_conforming_variant_wins_and_travels_unchanged() -> None:
    ink = _ink_column(100)
    near = _evaluation([[[100.0, 10.0], [100.0, 60.0]]], (0.0, 1.0), ink, 0)
    far = _evaluation([[[112.0, 10.0], [112.0, 60.0]]], (-2.0, 1.0), ink, 1)
    row = build_ensemble_row([far, near], _frame_record([near["variant"], far["variant"]]), _word_json(), "x", 2)

    assert row["status"] == "ok"
    assert row["meta"]["variant"] == near["variant"]
    # Verbatim: the winner's geometry is the emitted geometry, object for object.
    assert row["strokes"] == near["strokes"]
    assert row["meta"]["ensemble_n"] == 2
    assert row["meta"]["ensemble_n_valid"] == 2
    assert row["meta"]["ensemble_n_planned"] == 2
    assert [line["variant"] for line in row["meta"]["ranking"]] == [near["variant"], far["variant"]]
    assert row["meta"]["rank_metric"] == "chamfer_sum_xh_vs_measured_ink"


def test_a_contract_violation_is_disqualified_even_when_it_ranks_best() -> None:
    ink = _ink_column(100)
    # Dead on the ink — but a single-point stroke cannot be stored, so it must
    # lose to the conforming variant that sits 12 px beside the ink.
    broken = _evaluation([[[100.0, 35.0]]], (0.0, 1.0), ink, 0)
    usable = _evaluation([[[112.0, 10.0], [112.0, 60.0]]], (-2.0, 1.0), ink, 1)
    assert broken["status"] == "failed"
    assert broken["rank_sum_xh"] < usable["rank_sum_xh"]

    row = build_ensemble_row(
        [broken, usable], _frame_record([broken["variant"], usable["variant"]]), _word_json(), "x", 2
    )
    assert row["status"] == "ok"
    assert row["meta"]["variant"] == usable["variant"]
    assert row["meta"]["ensemble_n_valid"] == 1
    # The loser stays in the record with its reason: a disqualification is
    # reported, not deleted.
    disqualified = next(line for line in row["meta"]["ranking"] if line["variant"] == broken["variant"])
    assert "1 point" in disqualified["detail"]


def test_an_all_broken_ensemble_still_produces_a_failed_row() -> None:
    ink = _ink_column(100)
    worse = _evaluation([[[140.0, 35.0]]], (0.0, 1.0), ink, 0)
    better = _evaluation([[[100.0, 35.0]]], (-2.0, 1.0), ink, 1)
    row = build_ensemble_row(
        [worse, better], _frame_record([worse["variant"], better["variant"]]), _word_json(), "x", 2
    )
    assert row["status"] == "failed"
    # Among failures the ranking still decides, so the row that travels is the
    # least bad one rather than the first one on disk.
    assert row["meta"]["variant"] == better["variant"]
    assert "detail" in row["meta"]
    assert row["meta"]["ensemble_n_valid"] == 0


def test_every_variant_can_be_emitted_as_its_own_bench_row() -> None:
    # The §14 oracle column needs each variant scored against the hand trace on
    # its own, so each must be expressible in the same contract — with ITS
    # geometry and ITS rank numbers, and without the winner's ranking table.
    ink = _ink_column(100)
    near = _evaluation([[[100.0, 10.0], [100.0, 60.0]]], (0.0, 1.0), ink, 0)
    far = _evaluation([[[112.0, 10.0], [112.0, 60.0]]], (-2.0, 1.0), ink, 1)
    frame_record = _frame_record([near["variant"], far["variant"]])

    rows = [build_variant_row(item, frame_record, _word_json(), SKELETON_FILE) for item in (near, far)]

    assert [row["meta"]["variant"] for row in rows] == [near["variant"], far["variant"]]
    assert rows[0]["strokes"] == near["strokes"]
    assert rows[1]["strokes"] == far["strokes"]
    assert rows[0]["meta"]["rank_sum_xh"] < rows[1]["meta"]["rank_sum_xh"]
    assert all("ranking" not in row["meta"] for row in rows)
    assert all(row["registration_px"] == {"tx": 0, "ty": 0, "baseline_row": BASELINE_Y} for row in rows)
    # A losing variant is a perfectly valid row: the oracle needs the losers.
    assert all(row["status"] == "ok" for row in rows)


def test_a_disqualified_variant_keeps_its_reason_in_its_own_row() -> None:
    ink = _ink_column(100)
    broken = _evaluation([[[100.0, 35.0]]], (0.0, 1.0), ink, 0)
    row = build_variant_row(broken, _frame_record([broken["variant"]]), _word_json(), SKELETON_FILE)
    assert row["status"] == "failed"
    assert "1 point" in row["meta"]["detail"]
    assert len(row["strokes"]) == 1


def test_the_row_is_the_candidate_contract_the_bench_reads() -> None:
    ink = _ink_column(100)
    evaluation = _evaluation([[[100.0, 10.0], [100.0, 60.0]]], (0.0, 1.0), ink, 0)
    row = build_ensemble_row([evaluation], _frame_record([evaluation["variant"]]), _word_json(), SKELETON_FILE, 10)

    assert CANDIDATE_FRAME == "word_registration"
    assert TOOL_NAME == "inksight-smallp-bestofN"
    assert row["kind"] == "word"
    assert row["specimen_id"] == "wort"
    assert row["registration_px"] == {"tx": 0, "ty": 0, "baseline_row": BASELINE_Y}
    assert row["xh_px"] == pytest.approx(XH)
    assert all(abs(value) <= MAX_ABS_COORD for stroke in row["strokes"] for point in stroke for value in point)
    assert row["meta"]["ink_source"] == SKELETON_FILE
    assert row["meta"]["ensemble_n_planned"] == 10
    assert row["meta"]["prompt"] == "Derender the ink."
    assert row["meta"]["grid_step_crop_px"] == pytest.approx(1.0)


# ------------------------------------------------------------------- the sidecar


def _write_entry(root, entry_id: str = "wort") -> None:
    entry = root / entry_id
    entry.mkdir(parents=True)
    Image.new("RGB", (CROP_W, CROP_H), (255, 255, 255)).save(entry / "crop.png")
    entry.joinpath("word.json").write_text(json.dumps(_word_json() | {"id": entry_id}), encoding="utf-8")


def test_prepare_variants_writes_every_member_and_its_record(tmp_path) -> None:
    _write_entry(tmp_path)
    record = prepare_variants(tmp_path, "wort", tmp_path / "inputs")

    assert record["crop_w"] == CROP_W and record["crop_h"] == CROP_H
    assert list(record["variants"]) == [variant_name(rot, scale) for rot, scale in variant_grid()]
    for name, variant in record["variants"].items():
        written = tmp_path / "inputs" / variant["image"]
        assert written.is_file()
        with Image.open(written) as image:
            assert image.size == (MODEL_SIZE, MODEL_SIZE)
        assert variant_frame_of(variant).name == name


def test_augment_main_writes_a_manifest_the_ensemble_can_read(tmp_path) -> None:
    _write_entry(tmp_path)
    out = tmp_path / "out"
    assert augment_main(["--fixtures-root", str(tmp_path), "--ids", "wort", "--out", str(out)]) == 0

    payload = json.loads((out / DEFAULT_MANIFEST_NAME).read_text(encoding="utf-8"))
    assert payload["model_size"] == MODEL_SIZE
    assert payload["fixtures_root"] == str(tmp_path)
    assert payload["inputs_dir"] == str(out / "inputs_ensemble")
    assert payload["grid"]["identity"] == IDENTITY_VARIANT
    assert payload["grid"]["rotations_deg"] == list(DEFAULT_ROTATIONS)
    assert payload["grid"]["scales"] == list(DEFAULT_SCALES)
    variants = payload["frames"]["wort"]["variants"]
    assert len(variants) == len(variant_grid())
    assert all((out / "inputs_ensemble" / variant["image"]).is_file() for variant in variants.values())
