"""tools.lesarten.sync — the build the loader pushes: what it drops and why the
content hash follows the drop. Pure functions, no dictionary bytes, no network.
"""

from __future__ import annotations

import pytest

from core.lesarten import WORD_MAX, key_marker
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


def test_build_hash_follows_the_fold_as_well_as_the_words(monkeypatch) -> None:
    """A changed look-alike table re-buckets the vocabulary, so the same word
    list has to arrive as a NEW build: the server refuses a hash that is
    already live, and the words the new pair moved would stay unfindable in
    the stored generation."""
    monkeypatch.setattr(sync, "load_forms", lambda: {"Muhme", "lesen"})
    monkeypatch.setattr(sync, "bank_words", lambda: set())
    words, digest = sync.build()

    monkeypatch.setattr(sync, "key_signature", lambda: "lesart-key/v99 a>b")
    changed_words, changed_digest = sync.build()

    assert changed_words == words  # not a single word moved …
    assert changed_digest != digest  # … and it is a different build all the same


def test_source_label_names_the_fold_it_was_bucketed_with() -> None:
    """The API reads the marker back off the live build to flag a stale one."""
    assert key_marker() in sync.SOURCE_LABEL


@pytest.mark.parametrize("words", [[], ["kurz"]])
def test_drop_overlong_leaves_short_lists_alone(words: list[str]) -> None:
    assert sync.drop_overlong(words) == (words, [])
