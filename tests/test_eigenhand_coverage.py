"""Shaped coverage bookkeeping + strip-plan invariants of the Eigenhand tools."""

from __future__ import annotations

import json

import pytest

from tools.eigenhand import coverage, pool
from tools.eigenhand.store import STREIFEN_JSON


class TestShapedJoins:
    """Coverage runs on SHAPED glyph keys, never raw characters."""

    def test_ligature_swallows_the_raw_pair(self):
        joins = coverage.join_items("Buch")
        assert "u>ch" in joins
        assert "c>h" not in joins

    def test_sz_carries_no_s_join(self):
        joins = coverage.join_items("Fuß")
        assert joins == ["F>u", "u>sz"]

    def test_fuge_forces_round_s_and_blocks_ligature(self):
        joins = coverage.join_items("Haus|tür")
        assert "u>s" in joins  # round s, not longs
        assert "s>t" in joins  # separate letters — the ſt ligature is blocked
        assert not any("longst" in j for j in joins)

    def test_longst_ligature_inside_a_morpheme(self):
        assert "e>longst" in coverage.join_items("fest")

    def test_digits_and_punctuation_contribute_nothing(self):
        assert coverage.join_items("1922") == []
        assert coverage.join_items("Haus,") == ["H>a", "a>u", "u>s"]

    def test_positions_come_from_shaping(self):
        items = coverage.glyph_position_items("lesen")
        assert items == ["l@initial", "e@medial", "longs@medial", "e@medial", "n@final"]


class TestTargets:
    def test_floor_and_ceiling(self):
        assert coverage.target_for_weight(0.0, 100.0) == coverage.TARGET_FLOOR
        assert coverage.target_for_weight(100.0, 100.0) == coverage.TARGET_CEIL

    def test_sqrt_scaling_between(self):
        quarter = coverage.target_for_weight(25.0, 100.0)  # sqrt(0.25) = 0.5
        assert quarter == round(coverage.TARGET_FLOOR + 0.5 * (coverage.TARGET_CEIL - coverage.TARGET_FLOOR))


class TestStripPlan:
    UNIVERSE = {"l>e": 100.0, "e>longs": 50.0, "e>n": 80.0, "d>a": 30.0, "a>s": 20.0, "e@medial": 90.0}

    def test_build_is_deterministic(self):
        plan_a, _ = pool.build_wave({"format": 1, "waves": [], "strips": {}}, 3, dict(self.UNIVERSE))
        plan_b, _ = pool.build_wave({"format": 1, "waves": [], "strips": {}}, 3, dict(self.UNIVERSE))
        assert plan_a == plan_b

    def test_append_never_guard_raises_on_mutation(self):
        before = {
            "format": 1,
            "waves": [{"wave": 0, "strips": ["S0001"]}],
            "strips": {"S0001": {"wave": 0, "words": ["lesen"]}},
        }
        after = json.loads(json.dumps(before))
        after["strips"]["S0001"]["words"] = ["anders"]
        with pytest.raises(SystemExit, match="append-never"):
            pool.verify_immutable(before, after)

    def test_appending_a_wave_keeps_existing_strips_verbatim(self):
        plan, _ = pool.build_wave({"format": 1, "waves": [], "strips": {}}, 2, dict(self.UNIVERSE))
        frozen = json.loads(json.dumps(plan["strips"]))
        plan2, _ = pool.build_wave(plan, 2, dict(self.UNIVERSE))
        for sid, strip in frozen.items():
            assert plan2["strips"][sid] == strip
        assert len(plan2["waves"]) == 2
        new_ids = plan2["waves"][1]["strips"]
        assert new_ids and all(sid not in frozen for sid in new_ids)

    def test_committed_wave0_is_wellformed(self):
        plan = json.loads(STREIFEN_JSON.read_text(encoding="utf-8"))
        assert plan["format"] == pool.PLAN_FORMAT
        ids = sorted(plan["strips"], key=lambda s: int(s[1:]))
        assert ids[0] == "S0001"
        assert [int(s[1:]) for s in ids] == list(range(1, len(ids) + 1))  # dense numbering
        assert all(plan["strips"][sid]["words"] for sid in ids)
        listed = [sid for wave in plan["waves"] for sid in wave["strips"]]
        assert sorted(listed) == sorted(ids)
