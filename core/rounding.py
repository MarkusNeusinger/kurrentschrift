"""The 4-decimal wire contract of the render payloads — one implementation.

`core/pipeline.py` rounds every number it puts into a stored row or a render
payload to four decimals, and `docs/reference/write-api.md` states that as the
frozen render contract. Composition does NOT round: `core/compose.py` places
glyphs, generates the Übergänge and scales the Laufform by multiplying those
rounded inputs back apart to full float64 width, so `/write/word` used to ship
`0.015600000000000001` for a third of its numbers — noise below the contract's
own resolution, paid for in wire bytes on the API's most-requested route.

This module is the walk that puts the contract back on at the boundary. It
lives in `core/` and not next to the router because the fixture rebuild
(`tools/wordbench/fetch_fixtures.py --verify`) holds locally composed cases
against what `GET /write/word` serves, so both sides must round with the SAME
function or the bit-exact gate fails on the serialisation alone. `tools` may
import `core`; `core` and `api` must never import `tools`
(`tests/test_imports.py`).

Serialisation only: nothing here touches `core/compose.py`, the golden parity
fixture or a stored row. Rounding an already-rounded value is a no-op, so the
walk is idempotent and `/write/glyphs` (rounded by the pipeline already) goes
over the wire byte for byte as before.
"""

from __future__ import annotations

from typing import Any


# The contract's resolution. One template unit is the midband height, so the
# last kept digit is 1e-4 xh — well under a tenth of a pixel at any rendering
# size the site uses, while a digit less (1e-3 xh ≈ 0.2 px) would be visible.
WIRE_DECIMALS = 4


def round_wire_numbers(value: Any, ndigits: int = WIRE_DECIMALS) -> Any:
    """Return `value` with every float rounded to `ndigits`, containers walked.

    Ints (indices, counts) and bools pass through untouched — `isinstance` on
    `float` excludes both, since `bool` derives from `int`, not from `float`.
    Tuples become lists, which is what JSON serialisation makes of them anyway.
    """
    if isinstance(value, float):
        return round(value, ndigits)
    if isinstance(value, dict):
        return {key: round_wire_numbers(item, ndigits) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [round_wire_numbers(item, ndigits) for item in value]
    return value
