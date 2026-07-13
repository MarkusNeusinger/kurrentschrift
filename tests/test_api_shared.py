"""Unit tests for the shared API helpers and wire-type bounds (issue #183).

Pure, DB-free coverage for the consolidated pieces: the one Bbox→pipeline-dict
serializer, the shared anchor-count bound, and the quiz `era` enum. The async
DB/HTTP endpoints themselves stay the `/verify-api` sweep's job.
"""

import pytest
from pydantic import ValidationError

from api.rendering import bbox_to_pipeline_dict
from api.schemas import BboxIn, QuizWordOut, ResampleRequest, TraceRequest
from core.database import Bbox


def _bbox(**overrides) -> Bbox:
    base = {
        "y0": 10,
        "y1": 40,
        "x0": 5,
        "x1": 35,
        "mask_strokes": [{"points": [[1, 2]], "radius": 3.0}],
        "ink_strokes": [{"points": [[4, 5]], "radius": 2.0}],
        "patches": [{"src": [0, 0, 2, 2], "dst": [1, 1]}],
        "fill_holes_max_area": 120,
        "baseline_y": 38,
        "midband_y": 20,
        "n_anchors": 48,
        "guides": {},
    }
    base.update(overrides)
    return Bbox(**base)


def test_bbox_to_pipeline_dict_maps_all_fields():
    d = bbox_to_pipeline_dict(_bbox())
    assert d["y0"] == 10 and d["y1"] == 40 and d["x0"] == 5 and d["x1"] == 35
    assert d["mask_strokes"] == [{"points": [[1, 2]], "radius": 3.0}]
    assert d["ink_strokes"] == [{"points": [[4, 5]], "radius": 2.0}]
    assert d["patches"] == [{"src": [0, 0, 2, 2], "dst": [1, 1]}]
    assert d["fill_holes_max_area"] == 120 and isinstance(d["fill_holes_max_area"], int)
    assert d["baseline_y"] == 38 and d["midband_y"] == 20 and d["n_anchors"] == 48


def test_bbox_to_pipeline_dict_coupling_defaults_to_baseline():
    # No guides => both couplings fall back to baseline.
    assert bbox_to_pipeline_dict(_bbox(guides={}))["entry_coupling"] == "baseline"
    d = bbox_to_pipeline_dict(_bbox(guides={"entry_coupling": "midband", "exit_coupling": "ascender"}))
    assert d["entry_coupling"] == "midband" and d["exit_coupling"] == "ascender"


def test_bbox_to_pipeline_dict_tolerates_null_guides():
    # A row whose guides column is NULL must not blow up (guides or {}).
    assert bbox_to_pipeline_dict(_bbox(guides=None))["exit_coupling"] == "baseline"


@pytest.mark.parametrize("model", [BboxIn, TraceRequest, ResampleRequest])
@pytest.mark.parametrize("bad", [3, 0, -1, 1001])
def test_n_anchors_bound_rejects_out_of_range(model, bad):
    kwargs = {"n_anchors": bad}
    if model is BboxIn:
        kwargs.update(y0=0, y1=1, x0=0, x1=1, baseline_y=2, midband_y=1)
    if model is TraceRequest:
        kwargs.update(glyph="a", position="medial", raw_path=[])
    with pytest.raises(ValidationError):
        model(**kwargs)


@pytest.mark.parametrize("model", [BboxIn, TraceRequest, ResampleRequest])
def test_n_anchors_none_is_allowed(model):
    kwargs: dict = {}
    if model is BboxIn:
        kwargs.update(y0=0, y1=1, x0=0, x1=1, baseline_y=2, midband_y=1)
    if model is TraceRequest:
        kwargs.update(glyph="a", position="medial", raw_path=[])
    assert model(**kwargs).n_anchors is None


@pytest.mark.parametrize("era", ["modern", "historic"])
def test_quiz_word_era_accepts_known(era):
    assert QuizWordOut(word="Tag", distractors=[], era=era).era == era


def test_quiz_word_era_rejects_unknown():
    with pytest.raises(ValidationError):
        QuizWordOut(word="Tag", distractors=[], era="ancient")
