"""Guards for the quiz word generator (tools/quizgen).

Keeps the committed seed (`quiz_words.json`, loaded by migration 0010) in lock
step with the generator, and pins the Python similarity twin's behaviour.
"""

from __future__ import annotations

from tools.quizgen.build import OUT, _dump, _validate, build
from tools.quizgen.similarity import is_plausible_distractor, similarity


def test_quiz_words_json_up_to_date() -> None:
    """Committed seed == generator output; regen with `python -m tools.quizgen.build`."""
    assert OUT.read_text(encoding="utf-8") == _dump(build())


def test_generated_rows_are_valid() -> None:
    _validate(build())  # raises on any duplicate/era/distractor/fugen problem


def test_fugen_strips_to_word() -> None:
    for row in build():
        if "fugen" in row:
            assert row["fugen"].replace("|", "") == row["word"]


def test_similarity_rules() -> None:
    # shares start + end, differences are cursive-plausible → usable
    assert is_plausible_distractor("lesen", "leben")
    # different case pattern (noun vs. lowercase) → rejected
    assert similarity("Haus", "maus") == 0
    # length too far apart → rejected
    assert similarity("das", "dasselbe") == 0
    # shares neither first nor last letter → rejected
    assert similarity("und", "tor") == 0
