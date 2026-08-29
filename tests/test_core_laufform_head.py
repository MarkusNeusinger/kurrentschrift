"""The head gate on a Laufform row (qualitaetsmetrik.md §14 LF9): how far the
row's first stroke lands from the chart's landing direction, over the join
grammar's own arc window on the RENDERED centerline — the Korb #7 t, whose
fitted head starts up-left where the chart rises, and which the spike gate
cannot see."""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

import core.laufform as laufform_mod
from core.laufform import LAUFFORM_HEAD_DEVIATION_MAX, anchor_spike_ratio, head_deviation, head_gate


# A 45° diagonal, anchors 0.0707 apart: the window (0.12) reaches anchor 2.
CHART = [[i * 0.05, i * 0.05] for i in range(11)]


def _chart(anchors=CHART, stroke_starts=(0,)) -> SimpleNamespace:
    return SimpleNamespace(
        anchors=anchors, half_widths=[0.05] * len(anchors), trace_meta={"stroke_starts": list(stroke_starts)}
    )


def _turned(dx: float = 0.04, dy: float = -0.03) -> list[list[float]]:
    """The Korb #7 head: anchor 0 pulled right of / below anchor 1, so the
    first segment points up-left while the rest of the stroke is the chart."""
    row = [list(p) for p in CHART]
    row[0] = [CHART[1][0] + dx, CHART[1][1] + dy]
    return row


def test_a_rigid_shift_keeps_the_chart_direction():
    assert head_deviation(_chart(), [[x + 0.3, y - 0.1] for x, y in CHART]) == pytest.approx(0.0, abs=0.05)


def test_the_turned_head_is_read_off_the_rendered_line_over_the_grammar_window():
    row = _turned()
    dev = head_deviation(_chart(), row)
    # The spline through the pulled anchor lands well off the 45° chart line —
    # between the raw first segment (up-left, ~143°) and the chart.
    seg = math.degrees(math.atan2(row[1][1] - row[0][1], row[1][0] - row[0][0]))
    assert LAUFFORM_HEAD_DEVIATION_MAX < dev < abs(seg - 45.0)
    # …and it is no anchor jump: the spike gate lets exactly this row through.
    assert anchor_spike_ratio(row, [0]) < 2.0


def test_only_the_first_stroke_is_judged():
    # A wild second stroke leaves the head deviation untouched — the chart's
    # stroke starts cut the row where the chart's first stroke ends.
    two = CHART + [[1.0, 1.0], [1.1, 0.2], [0.4, 0.9]]
    row = [list(p) for p in two]
    row[11] = [2.0, -1.0]
    chart = _chart(two, (0, 11))
    assert head_deviation(chart, row) == pytest.approx(0.0, abs=0.05)
    turned = _turned() + two[11:]
    # The turned head still fails the gate — the exact angle shifts a few
    # degrees with the sample density the second stroke takes from the plan
    # (the gate judges the head as the renderer draws it, §14 LF9).
    assert head_deviation(chart, turned) > LAUFFORM_HEAD_DEVIATION_MAX


def test_degenerate_heads_are_never_a_refusal():
    assert head_deviation(_chart(), [[0.0, 0.0]] * 11) == 0.0
    assert head_deviation(_chart([[0.0, 0.0]]), [[0.0, 0.0]]) == 0.0
    assert head_deviation(_chart([]), []) == 0.0


def test_deviation_is_the_smaller_angle_between_the_directions():
    # A head reversed against the chart reads 180, never 0 or 360.
    reversed_row = [[-x, -y] for x, y in CHART]
    assert head_deviation(_chart(), reversed_row) == pytest.approx(180.0, abs=0.05)


def test_head_gate_reads_the_chart_row_and_the_adopted_gate(monkeypatch: pytest.MonkeyPatch):
    chart = _chart()
    assert LAUFFORM_HEAD_DEVIATION_MAX == 15.0
    ok = head_gate(chart, [[x + 0.3, y] for x, y in CHART])
    assert ok["max"] == LAUFFORM_HEAD_DEVIATION_MAX and not ok["exceeded"] and ok["deviation"] < 0.1
    bad = head_gate(chart, _turned())
    assert bad["exceeded"] and bad["deviation"] > LAUFFORM_HEAD_DEVIATION_MAX
    monkeypatch.setattr(laufform_mod, "LAUFFORM_HEAD_DEVIATION_MAX", None)
    off = head_gate(chart, _turned())
    assert off["max"] is None and not off["exceeded"] and off["deviation"] == bad["deviation"]
