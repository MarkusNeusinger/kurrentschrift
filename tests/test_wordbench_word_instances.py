"""Unit tests for the frozen word-trace artifact (word_instances.json).

Pure functions, no DB and no fixtures: hand-written rows against hand-written
sidecar entries, so the lean projection, the set scoping and the frame gate
(the #334/#336 class — a sidecar rect edited under a stored trace) are pinned
by numbers a reader can recompute. The artifact is the tracebench reference
(docs/proposals/tintenfolger.md): its `authored` rows are the ground truth an
automatic tracer is measured against, which is why a stale frame must be
STAMPED and counted rather than silently frozen or silently dropped.
"""

from __future__ import annotations

from tools.wordbench.export_fixtures import FRAME_BASELINE_TOL_PX, WORD_MEASUREMENT_KEYS, word_instances_payload


def _entry(y0: int = 100, baseline_y: int = 160, midband_y: int = 130) -> dict:
    # Crop-local baseline = baseline_y - y0 = 60, xh = baseline_y - midband_y = 30.
    return {"y0": y0, "baseline_y": baseline_y, "midband_y": midband_y}


def _row(
    specimen_id: str = "wenn",
    kind: str = "word",
    provenance: str = "traced",
    baseline_row: float = 60.0,
    ty: float = 0.0,
    xh: float = 30.0,
    hand_id: str | None = "suetterlin-1922-norm",
    **measurements,
) -> dict:
    return {
        "kind": kind,
        "specimen_id": specimen_id,
        "word": specimen_id,
        "slots": ["w", "e", "n", "n"],
        "provenance": provenance,
        "strokes": [[[0.1, 0.2], [0.3, 0.4]]],
        "hand_id": hand_id,
        "measurements": {
            "registration_px": {"tx": 11.0, "ty": ty, "baseline_row": baseline_row},
            "xh_px": xh,
            **measurements,
        },
    }


def test_the_payload_stays_lean_and_keeps_the_frame():
    row = _row(fit_path="chain", fitted_slots=[0, 1], geo_rmse_px_by_slot={"0": 1.2}, gates={"0": "ok"})
    payload = word_instances_payload([row], {"word"}, {"wenn"}, {"wenn": _entry()})
    (out,) = payload["rows"]
    # Exactly the lean keys travel — the harvest's per-slot auto-fit QC stays
    # in the DB, so authored and traced rows keep the same shape.
    assert set(out["measurements"]) == set(WORD_MEASUREMENT_KEYS)
    assert out["measurements"]["registration_px"] == {"tx": 11.0, "ty": 0.0, "baseline_row": 60.0}
    assert out["measurements"]["xh_px"] == 30.0
    assert out["measurements"]["fit_path"] == "chain"
    assert out["strokes"] == [[[0.1, 0.2], [0.3, 0.4]]]
    assert "hand_id" not in out  # modal at top level, never per row


def test_rows_are_scoped_to_the_sets_kind_and_specimens():
    rows = [
        _row("wenn"),
        _row("abb22-wenn"),  # same kind, DIFFERENT set — must not leak
        _row("re", kind="pair"),
    ]
    payload = word_instances_payload(rows, {"word"}, {"wenn"}, {"wenn": _entry()})
    assert [r["specimen_id"] for r in payload["rows"]] == ["wenn"]


def test_rows_sort_by_kind_then_specimen_and_the_hand_is_modal():
    rows = [_row("zwei", hand_id="hand-b"), _row("re", kind="pair", hand_id="hand-a"), _row("die", hand_id="hand-a")]
    entries = {i: _entry() for i in ("die", "zwei", "re")}
    payload = word_instances_payload(rows, {"word", "pair"}, {"die", "zwei", "re"}, entries)
    assert [(r["kind"], r["specimen_id"]) for r in payload["rows"]] == [
        ("pair", "re"),
        ("word", "die"),
        ("word", "zwei"),
    ]
    assert payload["hand_id"] == "hand-a"


def test_the_frame_gate_tolerates_the_score_grids_search_range():
    # ty is folded into the comparison: baseline_row + ty against the sidecar.
    ok = [
        _row(baseline_row=60.0),
        _row(baseline_row=57.0, ty=3.0),  # sums to 60 exactly
        _row(baseline_row=60.0 + FRAME_BASELINE_TOL_PX - 1.0),  # inside the search range
        _row(xh=30.5),  # inside the half-pixel rounding allowance
    ]
    payload = word_instances_payload(ok, {"word"}, {"wenn"}, {"wenn": _entry()})
    assert all("frame_stale" not in r for r in payload["rows"])


def test_a_moved_rect_is_stamped_not_dropped():
    # The #336 case in miniature: the sidecar rect moved 18 px up, the stored
    # registration still describes the old crop.
    row = _row(baseline_row=60.0)
    moved = _entry(y0=82)  # expected baseline becomes 78
    payload = word_instances_payload([row], {"word"}, {"wenn"}, {"wenn": moved})
    (out,) = payload["rows"]
    assert "baseline_row 60" in out["frame_stale"]
    assert "78" in out["frame_stale"]  # the expectation is named, not just flagged
    assert out["strokes"]  # stamped, never dropped


def test_a_moved_lineature_is_stamped_via_xh():
    payload = word_instances_payload(
        [_row(xh=31.0)], {"word"}, {"wenn"}, {"wenn": _entry(midband_y=128)}
    )  # expected xh 32, stored 31 — beyond the half-pixel rounding allowance
    (out,) = payload["rows"]
    assert "xh_px 31" in out["frame_stale"]


def test_a_refill_gates_against_the_roots_own_frozen_entries(tmp_path):
    # An --only refill drops fresh rows into an EXISTING root, so the gate
    # reference is the root's frozen word.json — not today's sidecar. This is
    # the #336 case: the sidecar rect moved after the root froze, the DB row
    # was re-registered to the NEW rect, and against the OLD frozen crop the
    # row must read as stale.
    from tools.wordbench.export_fixtures import _frozen_gate_entries

    entry_dir = tmp_path / "zwei"
    entry_dir.mkdir()
    (entry_dir / "word.json").write_text('{"rect": [1038, 1136, 1264, 1219], "baseline_y": 1182, "midband_y": 1152}')
    entries = _frozen_gate_entries(tmp_path, {"zwei", "absent"})
    assert entries == {"zwei": {"y0": 1136, "baseline_y": 1182, "midband_y": 1152}}

    row = _row("zwei", provenance="authored", baseline_row=64.0)  # re-registered to the widened rect
    payload = word_instances_payload([row], {"word"}, {"zwei"}, entries)
    assert "baseline_row 64 vs expected 46" in payload["rows"][0]["frame_stale"]


def test_a_row_without_registration_or_entry_is_stamped():
    bare = _row()
    bare["measurements"] = {}
    payload = word_instances_payload([bare], {"word"}, {"wenn"}, {"wenn": _entry()})
    assert payload["rows"][0]["frame_stale"] == "no stored registration"

    payload = word_instances_payload([_row()], {"word"}, {"wenn"}, {})
    assert payload["rows"][0]["frame_stale"] == "no reference entry"
