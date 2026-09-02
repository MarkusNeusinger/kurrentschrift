"""tools.lesarten.sync — the build the loader pushes: what it drops and why the
content hash follows the drop. Pure functions, no dictionary bytes, no network.
"""

from __future__ import annotations

import pytest

from core.lesarten import WORD_MAX
from tools.lesarten import sync


def test_drop_overlong_splits_at_the_column_bound() -> None:
    long_one = "Grundstücksverkehrsgenehmigungszuständigkeitsübertragungsverordnung"
    assert len(long_one) > WORD_MAX
    kept, dropped = sync.drop_overlong(["Muhme", long_one, "a" * WORD_MAX, long_one + "en"])
    assert kept == ["Muhme", "a" * WORD_MAX]  # the bound itself still fits
    assert dropped == [long_one, long_one + "en"]


def test_build_drops_overlong_words_and_reports_them(monkeypatch, capsys) -> None:
    """The API refuses a whole batch that carries an unstorable word — the first
    production load died on exactly that — so the build never sends one."""
    long_one = "x" * (WORD_MAX + 3)
    monkeypatch.setattr(sync, "load_forms", lambda: {"Muhme", "lesen", long_one})
    monkeypatch.setattr(sync, "bank_words", lambda: {"Wittib"})

    pairs, digest = sync.build()

    assert [w for w, _ in pairs] == ["Muhme", "Wittib", "lesen"]  # sorted, the long one gone
    assert [w for w, bank in pairs if bank] == ["Wittib"]
    out = capsys.readouterr().out
    assert f"dropped 1 words longer than {WORD_MAX} characters" in out

    # The hash covers what is pushed: a build without the long word is a
    # different build from one that would have carried it.
    monkeypatch.setattr(sync, "load_forms", lambda: {"Muhme", "lesen"})
    assert sync.build()[1] == digest


@pytest.mark.parametrize("words", [[], ["kurz"]])
def test_drop_overlong_leaves_short_lists_alone(words: list[str]) -> None:
    assert sync.drop_overlong(words) == (words, [])
