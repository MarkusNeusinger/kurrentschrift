"""Unit tests for the Gleichzug audit (tools/wordbench/gleichzug.py)."""

from tools.wordbench.gleichzug import DOUBLE_MIN, GAP_EPS, audit_composed


def _glyph(slot: int, line: list) -> dict:
    return {
        "centerline": [list(p) for p in line],
        "rings": [[[0, 0], [0, 1], [1, 1]]],
        "lift": False,
        "slot_index": slot,
    }


def _conn(line: list) -> dict:
    return {"centerline": [list(p) for p in line], "stroke_width": 0.15, "lift": False}


def _composed(items: list) -> dict:
    return {"items": items, "bounds": {}, "guides": None, "missing": []}


def _diag(x0: float, y0: float, n: int = 40, dx: float = 0.02, dy: float = 0.02) -> list:
    return [(x0 + i * dx, y0 + i * dy) for i in range(n)]


def test_clean_flow_passes() -> None:
    a = _diag(0.0, 0.0)
    conn = _diag(a[-1][0], a[-1][1], n=10)
    b = _diag(conn[-1][0], conn[-1][1])
    report = audit_composed(_composed([_glyph(0, a), _conn(conn), _glyph(1, b)]))
    assert report["gaps"] == []
    assert report["doublings"] == []


def test_flow_gap_is_flagged() -> None:
    a = _diag(0.0, 0.0)
    b = _diag(a[-1][0] + 3 * GAP_EPS, a[-1][1])  # pen teleports
    report = audit_composed(_composed([_glyph(0, a), _glyph(1, b)]))
    assert len(report["gaps"]) == 1


def test_lift_is_not_a_gap() -> None:
    a = _diag(0.0, 0.0)
    b = dict(_glyph(1, _diag(3.0, 0.0)), lift=True)  # i-dot style pen lift
    report = audit_composed(_composed([_glyph(0, a), b]))
    assert report["gaps"] == []


def test_parallel_doubling_across_slots_is_flagged() -> None:
    a = _diag(0.0, 0.0, n=60)
    b = [(x + 0.07, y - 0.07) for x, y in a]  # parallel at ~0.10 separation
    report = audit_composed(_composed([_glyph(0, a), dict(_glyph(1, b), lift=True)]))
    assert report["doublings"]


def test_exact_retrace_is_allowed() -> None:
    a = _diag(0.0, 0.0, n=60)
    b = [(x + DOUBLE_MIN / 4, y - DOUBLE_MIN / 4) for x, y in a]  # rides the same line
    report = audit_composed(_composed([_glyph(0, a), dict(_glyph(1, b), lift=True)]))
    assert report["doublings"] == []


def test_transversal_crossing_is_allowed() -> None:
    a = _diag(0.0, 0.0, n=60)  # rising 45
    b = [(0.0 + i * 0.02, 1.2 - i * 0.02) for i in range(60)]  # falling 45, crosses
    report = audit_composed(_composed([_glyph(0, a), dict(_glyph(1, b), lift=True)]))
    assert report["doublings"] == []


def test_same_slot_parallel_is_letterform_not_compose() -> None:
    a = _diag(0.0, 0.0, n=60)
    b = [(x + 0.07, y - 0.07) for x, y in a]
    items = [_glyph(0, a), dict(_glyph(0, b), lift=True)]  # SAME slot: e's two strokes
    report = audit_composed(_composed(items))
    assert report["doublings"] == []
