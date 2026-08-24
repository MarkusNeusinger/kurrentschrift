"""Shaped coverage bookkeeping + strip-plan invariants of the Eigenhand tools."""

from __future__ import annotations

import json

import pytest

from core.eigenhand import coverage
from core.eigenhand import plan as plan_mod
from core.eigenhand.plan import STREIFEN_JSON
from tools.eigenhand import pool, progression, universe
from tools.eigenhand.corpus import pool_entries, shaping_form


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
        assert plan["format"] == plan_mod.PLAN_FORMAT
        ids = sorted(plan["strips"], key=lambda s: int(s[1:]))
        assert ids[0] == "S0001"
        assert [int(s[1:]) for s in ids] == list(range(1, len(ids) + 1))  # dense numbering
        assert all(plan["strips"][sid]["words"] for sid in ids)
        listed = [sid for wave in plan["waves"] for sid in wave["strips"]]
        assert sorted(listed) == sorted(ids)

    def test_the_plan_carries_every_shaping_form_it_needs(self):
        # The plan is the API's ONLY word source: a reader without the
        # curation module must still shape `Amtszeit` as `Amts|zeit`.
        plan = plan_mod.load_plan()
        curated = {entry["word"]: shaping_form(entry) for entry in pool_entries()}
        for sid, strip in plan["strips"].items():
            for word in strip["words"]:
                assert plan_mod.shaping_form_of(plan, word) == curated[word], f"{sid}: {word} shapes differently"


class TestDetachedGlyphs:
    """Digits and punctuation carry glyph-position Soll but never joins."""

    def test_digits_carry_positions_but_no_joins(self):
        assert coverage.join_items("1922") == []
        assert coverage.glyph_position_items("1922") == ["1@initial", "9@medial", "2@medial", "2@final"]

    def test_punctuation_at_a_word(self):
        items = coverage.glyph_position_items("ja!")
        assert "exclam@initial" in items
        assert coverage.join_items("ja!") == ["j>a"]


class TestProgression:
    PLAN = {
        "format": 1,
        "waves": [{"wave": 0, "strips": ["S0001", "S0002", "S0003"]}],
        "strips": {
            "S0001": {"wave": 0, "words": ["lesen"]},
            "S0002": {"wave": 0, "words": ["1922"]},
            "S0003": {"wave": 0, "words": ["Wer"]},
        },
    }

    def test_classify_buckets(self):
        assert progression.classify_key("a") == "klein"
        assert progression.classify_key("longs") == "klein"
        assert progression.classify_key("W") == "gross"
        assert progression.classify_key("Ue") == "gross"
        assert progression.classify_key("ch") == "ligatur"
        assert progression.classify_key("7") == "ziffer"
        assert progression.classify_key("quote-low") == "zeichen"

    def test_checkpoints_are_cumulative_and_include_the_final_partial(self):
        points = progression.checkpoints(self.PLAN, step=2, universe_items=None)
        assert [p["strips"] for p in points] == [2, 3]
        first, last = points
        assert first["glyphs"]["ziffer"] == {"1": 1, "2": 2, "9": 1}
        assert first["glyphs"]["gross"] == {}
        assert last["glyphs"]["gross"] == {"W": 1}
        assert last["glyphs"]["klein"]["e"] == 3  # lesen + Wer
        assert last["joins_distinct"] >= first["joins_distinct"]

    def test_quotas_appear_with_a_universe(self):
        points = progression.checkpoints(self.PLAN, step=3, universe_items={"l>e": 10.0, "x>y": 5.0})
        quotas = points[-1]["quotas"]
        assert 0.0 < quotas["erstbeleg_weighted"] < 1.0  # l>e covered, x>y not
        assert quotas["erstbeleg"] <= 1.0


class TestGlyphFloor:
    """Every glyph key is planned at least GLYPH_MIN_PLANNED times (owner rule)."""

    @staticmethod
    def _reachable_keys() -> set[str]:
        """Every glyph key any Wortvorrat word can supply — the honest universe."""
        keys: set[str] = set()
        for entry in pool_entries():
            for item in coverage.word_items(shaping_form(entry)):
                if coverage.JOIN_SEP not in item:
                    keys.add(item.split(coverage.POSITION_SEP)[0])
        return keys

    def test_committed_plan_meets_the_floor(self):
        plan = json.loads(STREIFEN_JSON.read_text(encoding="utf-8"))
        points = progression.checkpoints(plan, step=10_000, universe_items=None)
        totals = {key: count for bucket in points[-1]["glyphs"].values() for key, count in bucket.items()}
        # Counted over the reachable keys, not over what the plan happens to
        # contain: a key missing from the plan entirely is the silent failure
        # this floor exists to prevent.
        missing = sorted(self._reachable_keys() - set(totals))
        assert not missing, f"reachable glyphs never planned: {missing}"
        under = {key: totals[key] for key in self._reachable_keys() if totals[key] < pool.GLYPH_MIN_PLANNED}
        assert not under, f"glyphs under the floor: {under}"

    def test_builder_tops_up_starved_glyphs(self):
        # A universe that only rewards l>e would leave rare carriers at one
        # occurrence; phase A2 lifts every glyph to the floor regardless of
        # weight, given enough strips.
        plan, stats = pool.build_wave({"format": 1, "waves": [], "strips": {}}, 120, {"l>e": 100.0})
        assert stats["floor_unmet"] == []
        points = progression.checkpoints(plan, step=10_000, universe_items=None)
        totals = {key: count for bucket in points[-1]["glyphs"].values() for key, count in bucket.items()}
        # Every reachable key, again — "floor met" must not mean "met among the
        # keys that happened to make it into the plan".
        assert not self._reachable_keys() - set(totals)
        assert min(totals.values()) >= pool.GLYPH_MIN_PLANNED

    def test_unreachable_floor_is_reported_not_silent(self):
        # Too few strips to satisfy the floor: the leftovers must be NAMED in
        # the stats (and warned about), never quietly dropped.
        _plan, stats = pool.build_wave({"format": 1, "waves": [], "strips": {}}, 12, {"l>e": 100.0})
        assert stats["floor_unmet"], "a wave too small to meet the floor must report it"


class TestProgressionCli:
    def test_a_step_of_zero_is_refused_before_it_reaches_range(self):
        # range(step, n, 0) raises deep inside checkpoints(); the CLI says so.
        with pytest.raises(SystemExit):
            progression.main(["--step", "0", "--no-universe"])


class TestUniverseFormat:
    """The weight table is a local artefact — a format bump must be loud."""

    def test_a_foreign_format_is_refused(self, tmp_path):
        path = tmp_path / "uebergangsraum.json"
        path.write_text(json.dumps({"format": 99, "items": {}}), encoding="utf-8")
        with pytest.raises(SystemExit, match="unsupported format"):
            universe.load_universe(path)

    def test_the_current_format_loads(self, tmp_path):
        path = tmp_path / "uebergangsraum.json"
        path.write_text(json.dumps({"format": universe.UNIVERSE_FORMAT, "items": {"l>e": 1.0}}), encoding="utf-8")
        assert universe.load_universe(path)["items"] == {"l>e": 1.0}
