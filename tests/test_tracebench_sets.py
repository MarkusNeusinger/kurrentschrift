"""Tests for the frozen development split (`tools.tracebench.sets`).

Three lines of code, and the only thing standing between "the follower improved
by 25 %" and a number fitted to the ten words it was tuned on. The split is
therefore pinned literally: the ids, the count, and the immutability of the
container itself.
"""

from __future__ import annotations

import pytest

from tools.tracebench.sets import TRACEBENCH_DEV_IDS


def test_the_development_split_is_exactly_the_ten_hand_traced_words() -> None:
    assert TRACEBENCH_DEV_IDS == {"die", "laden", "linken", "mit", "muß", "und", "unter", "Wer", "will", "zwei"}
    assert len(TRACEBENCH_DEV_IDS) == 10


def test_the_split_cannot_be_appended_to() -> None:
    """Append-never is a property of the container, not only of the docstring.

    Every word traced after this list was frozen is confirmation material by
    definition; a mutable set would let a later session widen the dev split by
    accident and quietly turn a held-out word into a tuned-on one.
    """
    assert isinstance(TRACEBENCH_DEV_IDS, frozenset)
    with pytest.raises(AttributeError):
        TRACEBENCH_DEV_IDS.add("regieren")  # type: ignore[attr-defined]
