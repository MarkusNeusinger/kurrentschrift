"""Decoding of InkSight's `<ink_token_N>` output into strokes.

Kept in its own module because it is the ONE piece of the pipeline both the
TensorFlow venv (`run_inksight.py`, which produces the raw text) and the repo
environment (the unit tests) need — and it must be importable without
TensorFlow.

Token layout of the released Small-p checkpoint, adapted from the public
InkSight inference notebook
(https://github.com/google-research/inksight, `colab.ipynb`):

* the ink lives in a 225-level grid over the 224 px model frame, so a
  coordinate token is `0 .. COORDINATE_LENGTH` (225 values per dimension);
* x tokens come first, y tokens are the same values shifted by
  `TOKENS_PER_DIMENSION`, i.e. `225 .. 449`;
* `STROKE_START_TOKEN` (450) opens a new stroke.

The decoder is deliberately forgiving about a malformed stream (a truncated
decode can end mid-pair) and deliberately does NOT clean up the geometry: it
reports what the model emitted, including single-point strokes, and counts
what it had to discard. Cleanup would be a modelling decision, and this is a
measurement tool.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# The model frame is 224 px wide/high; the token grid has one level per pixel
# boundary, hence 225 values per dimension.
COORDINATE_LENGTH = 224
TOKENS_PER_DIMENSION = COORDINATE_LENGTH + 1
STROKE_START_TOKEN = 2 * TOKENS_PER_DIMENSION  # 450

INK_TOKEN_RE = re.compile(r"<ink_token_(\d+)>")


@dataclass
class DecodedInk:
    """One decoded model answer.

    `strokes` are in the 224 px model frame (x right, y down — image
    coordinates), exactly as emitted. `n_ink_tokens` is the number of
    `<ink_token_N>` tokens the answer contained: the decoder context is 1024
    tokens, so a word that silently hit the ceiling must be visible as a number
    rather than as a short stroke list.
    """

    strokes: list[list[list[float]]] = field(default_factory=list)
    n_ink_tokens: int = 0
    n_invalid_tokens: int = 0
    text_without_ink: str = ""


def parse_ink_tokens(text: str) -> list[int]:
    """Every `<ink_token_N>` of the answer, in order."""
    return [int(m) for m in INK_TOKEN_RE.findall(text)]


def strip_ink_tokens(text: str) -> str:
    """The answer without its ink tokens — for `Recognize and derender.`, whose
    output carries the recognised text beside the ink."""
    return INK_TOKEN_RE.sub("", text).strip()


def tokens_to_strokes(tokens: list[int]) -> tuple[list[list[list[float]]], int]:
    """Ink tokens → strokes in the 224 px model frame, plus the invalid count.

    A token is read by the range it falls in rather than by position, so a
    truncated or misaligned stream degrades locally instead of shifting every
    following coordinate: an x token arriving while an x is already pending
    means the pending one never got its y (counted, dropped), and a y token
    with nothing pending is counted and dropped as well.
    """
    strokes: list[list[list[float]]] = []
    current: list[list[float]] = []
    pending_x: int | None = None
    invalid = 0

    for token in tokens:
        if token == STROKE_START_TOKEN:
            if pending_x is not None:
                invalid += 1
                pending_x = None
            if current:
                strokes.append(current)
            current = []
            continue
        if 0 <= token < TOKENS_PER_DIMENSION:
            if pending_x is not None:
                invalid += 1
            pending_x = token
            continue
        if TOKENS_PER_DIMENSION <= token < STROKE_START_TOKEN:
            if pending_x is None:
                invalid += 1
                continue
            current.append([float(pending_x), float(token - TOKENS_PER_DIMENSION)])
            pending_x = None
            continue
        invalid += 1

    if pending_x is not None:
        invalid += 1
    if current:
        strokes.append(current)
    return strokes, invalid


def decode_ink(text: str) -> DecodedInk:
    """The full decode of one model answer."""
    tokens = parse_ink_tokens(text)
    strokes, invalid = tokens_to_strokes(tokens)
    return DecodedInk(
        strokes=strokes, n_ink_tokens=len(tokens), n_invalid_tokens=invalid, text_without_ink=strip_ink_tokens(text)
    )
