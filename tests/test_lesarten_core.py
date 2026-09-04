"""core.lesarten — the look-alike classes, the bucket key, the ranking; and the
Python table pinned to its TypeScript twin (app/src/lib/lesarten.ts)."""

from __future__ import annotations

import re
from pathlib import Path

import core.lesarten as lesarten
from core.lesarten import (
    LESART_KEY_VERSION,
    LOOKALIKES,
    MAX_TEXT_LEN,
    WORD_MAX,
    key_marker,
    key_signature,
    lesart_key,
    rank_readings,
    swap_cost,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_table_is_symmetric() -> None:
    for a, tos in LOOKALIKES.items():
        for b in tos:
            assert a in LOOKALIKES[b], f"{a} → {b} has no way back"


def test_table_matches_the_typescript_twin() -> None:
    """One table, two languages: the SPA's letter detail and the API's
    readings must agree on what looks alike."""
    src = (REPO_ROOT / "app" / "src" / "lib" / "lesarten.ts").read_text(encoding="utf-8")
    block = src.split("export const LOOKALIKES")[1].split("};")[0]
    ts: dict[str, tuple[str, ...]] = {}
    for m in re.finditer(r"^\s*'?(\S+?)'?:\s*\[(.*?)\],", block, re.M):
        ts[m.group(1)] = tuple(re.findall(r"'([^']+)'", m.group(2)))
    assert ts == LOOKALIKES


def test_key_buckets_readable_variants_together() -> None:
    assert lesart_key("Muhme") == lesart_key("Mühme") == lesart_key("Nuhme")
    assert lesart_key("lesen") == lesart_key("lefen")  # ſ ↔ f
    assert lesart_key("das") != lesart_key("daf")[:2] + "x"
    assert lesart_key("Haus") != lesart_key("Hans") or lesart_key("u") == lesart_key("n")
    # Case matters: capital clusters are their own classes.
    assert lesart_key("Nuhme") != lesart_key("nuhme")
    assert len(lesart_key("ß.,")) == 3  # letters outside the table map to themselves


def test_g_and_p_are_one_class() -> None:
    """The descender pair (owner 2026-09-04, orthographie-regeln.md §3): the g
    closes a round loop below the line, the p goes down straight. It is a class
    of its own — the fold must not drag it into the n/u component."""
    assert swap_cost("g", "p") == 1 and swap_cost("p", "g") == 1
    assert lesart_key("Rappe") == lesart_key("Ragge")
    assert swap_cost("g", "n") is None and swap_cost("p", "u") is None


def test_key_signature_names_the_version_and_the_whole_table() -> None:
    """What the loader hashes into a build: change either half and the build is
    a different one, so the server cannot refuse the reload as already live."""
    sig = key_signature()
    assert sig.startswith(key_marker()) and f"v{LESART_KEY_VERSION}" in key_marker()
    assert "g>p" in sig and "p>g" in sig
    assert key_marker(LESART_KEY_VERSION - 1) != key_marker()


def test_key_signature_follows_a_changed_table(monkeypatch) -> None:
    before = key_signature()
    monkeypatch.setitem(lesarten.LOOKALIKES, "x", ("y",))
    assert key_signature() != before


def test_swap_cost_is_graph_distance() -> None:
    assert swap_cost("n", "n") == 0
    assert swap_cost("n", "u") == 1
    assert swap_cost("u", "e") == 2  # u → n → e
    assert swap_cost("n", "x") is None
    assert swap_cost("s", "f") == 1 and swap_cost("f", "s") == 1


def test_rank_prefers_cheap_swaps_then_bank_then_short() -> None:
    candidates = [("Mühme", False), ("Nuhme", False), ("Mühle", True), ("Muhme", False), ("Mxhme", False)]
    readings = rank_readings("Muhme", candidates)
    words = [r.word for r in readings]
    assert "Muhme" not in words and "Mxhme" not in words
    assert words[:2] == ["Mühme", "Nuhme"]  # cost 1 each, alphabetical
    assert readings[0].swaps[0].index == 1 and readings[0].swaps[0].from_ == "u" and readings[0].swaps[0].to == "ü"
    assert rank_readings("Muhme", candidates, limit=1) == readings[:1]


def test_word_bound_is_the_column_it_stands_for() -> None:
    """WORD_MAX is the load's cap because the column cannot hold more — the two
    must never drift apart."""
    from core.database.models import LesartForm

    assert WORD_MAX == LesartForm.__table__.c.word.type.length
    assert WORD_MAX > MAX_TEXT_LEN  # a guess is always short enough to have readings


def test_text_bound_is_shared_with_the_page() -> None:
    src = (REPO_ROOT / "app" / "src" / "sections" / "vergleichen" / "VergleichenView.tsx").read_text(encoding="utf-8")
    m = re.search(r"const MAX_LEN = (\d+);", src)
    assert m and int(m.group(1)) == MAX_TEXT_LEN
