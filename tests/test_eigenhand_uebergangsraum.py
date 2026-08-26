"""The Soll universe's one derivation, its push payload, and the archive's copy.

`coverage.soll_from_weights` is the target derivation both surfaces share
(the local `pool.soll_model` after its pool union, the server over the stored
row); `universe.push_payload` is what leaves the machine — the COMPLETE table,
never the corpus bytes. No network, no DB: the push itself is exercised
against a fake `request_json`, the sync tests' pattern.
"""

from __future__ import annotations

import json

import pytest

from core.eigenhand import coverage
from tools.eigenhand import pool, universe


class TestSollFromWeights:
    def test_targets_scale_against_the_tables_own_maximum(self):
        weights, targets = coverage.soll_from_weights({"a@medial": 100.0, "b@medial": 25.0, "Z@initial": 0.0})
        assert weights == {"a@medial": 100.0, "b@medial": 25.0, "Z@initial": 0.0}
        assert targets["a@medial"] == coverage.TARGET_CEIL
        assert targets["Z@initial"] == coverage.TARGET_FLOOR
        assert coverage.TARGET_FLOOR < targets["b@medial"] < coverage.TARGET_CEIL

    def test_the_local_soll_model_is_the_same_derivation_after_its_union(self):
        # pool.soll_model = union with the curated pool, then soll_from_weights.
        weights, targets = pool.soll_model({"e@medial": 10.0})
        union = pool.soll_weights({"e@medial": 10.0})
        assert weights == union
        assert targets == coverage.soll_from_weights(union)[1]
        assert len(union) > 1 and all(w == 0.0 for k, w in union.items() if k != "e@medial")

    def test_an_empty_table_yields_an_empty_model(self):
        assert coverage.soll_from_weights({}) == ({}, {})


class TestItemKeys:
    @pytest.mark.parametrize("key", ["l>e", "longs>ch", "e@medial", "paren-open@initial", "7@final", "Ae>u"])
    def test_real_keys_pass(self, key):
        assert coverage.is_item_key(key)

    @pytest.mark.parametrize("key", ["", "e", "e medial", "e@middle", "l>e>r", "l>", "@medial", "e@Medial"])
    def test_misspelled_keys_fail(self, key):
        assert not coverage.is_item_key(key)


class TestPushPayload:
    def _table(self) -> dict:
        return {
            "format": universe.UNIVERSE_FORMAT,
            "en_weight": 0.25,
            "corpora": {"de_50k.txt": "a" * 64, "en_50k.txt": "b" * 64},
            "words_used": {"de": 3, "en": 2},
            "items": {"e@medial": 100.0, "l>e": 40.0},
        }

    def test_the_payload_is_the_complete_soll_universe_with_provenance(self):
        payload = universe.push_payload(self._table())
        assert payload["name"] == "uebergangsraum"
        assert payload["corpus_items"] == 2 and len(payload["items"]) == len(pool.soll_weights(self._table()["items"]))
        assert payload["items"]["e@medial"] == 100.0 and payload["items"]["l>e"] == 40.0
        assert payload["min_count"] == universe.MIN_COUNT and payload["min_word_len"] == universe.MIN_WORD_LEN
        assert payload["corpora"] == self._table()["corpora"]
        assert len(payload["pool_sha256"]) == 64
        assert all(coverage.is_item_key(item) for item in payload["items"])
        assert "de_50k" not in json.dumps(payload["items"]), "corpus bytes never ride along"

    def test_the_pool_stamp_is_stable_for_the_same_pool(self):
        assert (
            universe.push_payload(self._table())["pool_sha256"] == universe.push_payload(self._table())["pool_sha256"]
        )

    def test_push_is_a_dry_run_without_a_token_and_a_put_with_one(self, monkeypatch):
        table = self._table()
        assert universe.push(table, api=None, token=None, dry_run=True).startswith("dry run")

        calls: list[tuple] = []

        def fake_request_json(method, url, token, body=None, allow_404=False):
            calls.append((method, url, token, body))
            return {"stored": True, "replaced": False, "sha256": "f" * 64}

        monkeypatch.setattr("tools.eigenhand.apiclient.request_json", fake_request_json)
        line = universe.push(table, api="https://example.test", token="t", dry_run=False)
        assert calls and calls[0][:3] == ("PUT", "https://example.test/eigenhand/uebergangsraum", "t")
        assert calls[0][3]["items"]["e@medial"] == 100.0
        assert line.startswith("stored at https://example.test")
