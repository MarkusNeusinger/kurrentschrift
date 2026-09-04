"""Run the PRODUCTION Übergang generator at a placement the composer never chose.

pairlab's whole method is to remove the placement confound: it re-fits every
letter of a specimen word independently and then asks what the join between
those two letters should look like. That second half needs the production join
grammar evaluated at coordinates ``compose_word`` never produced — and until
2026-09-04 it got a hand-written copy of that grammar instead
(``analyze._generate_connector``, frozen 2026-07-11 while
``core.compose._connector_centerline`` was rebuilt three times: #308, #358,
#366; audit 2026-09-02, Befund 18).

This module removes the copy. The grammar is never re-implemented here; it is
RECORDED as production runs it and REPLAYED with translated geometry:

1. ``recording()`` swaps ``core.compose._connector_centerline`` for a delegating
   recorder for the duration of one composition. The recorder calls the real
   function, keeps its arguments and its result, and returns that result
   unchanged — the composition it wraps is byte-identical to an unwrapped one
   (pinned by ``tests/test_pairlab_connector_parity.py``).
2. ``replay()`` calls the SAME production function again with the recorded
   arguments, translating only what the independent fit moved: A's exit anchor
   (and the two A-side handshakes read in word coordinates, ``fork_line`` and
   ``stem_launch``) by A's shift, and B's lead-in by B's — the y component on
   ``first_line`` itself, the x component on ``dx``, because that is exactly how
   ``_connector_centerline`` places B (``p3 = first_line[k][0] + dx``).

Everything that DECIDES a join — the garland branch, the fork retrace, the
Absatz ride, the crest roll, every constant and guard — stays in `core`. A
future rebuild of the join block reaches pairlab on its next run, without a
line changing here. That is the property the frozen mirror could not have.

Why a recorder and not a reconstruction of the call arguments: two of the
inputs are not observable in the composed output. ``first_line`` is B's
UNTRIMMED first stroke, but the emitted item is already cut by ``entry_trim`` —
the connector's own return value — and on the frozen Sütterlin sets that cut
fires on 88 of 248 joins (35 %); a capital's ``exit``/``tangent_deg`` come from
the ornament retrace, not from the body endpoint. Reconstructing them means
re-deriving glyph preparation (Ascender-Lean, Laufform width) outside `core`,
which is the mirror problem again, one level down. See the finding in the PR
that introduced this module for the smallest core-side seam that would make
the recorder unnecessary.

Measurement layer: this module imports `core`, never the other way round.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass

import core.compose as compose
from tools.wordlab.cases import WordCase
from tools.wordlab.derive import WordDeriveResult, derive_word, laufform_payloads_for


Point = tuple[float, float]

# One recording at a time per process: the recorder swaps a module attribute of
# `core.compose`, so two overlapping recordings would interleave their calls and
# the outer one would restore a patched function. Recording is a diagnostic
# step, never a hot path — serialising it costs nothing and makes the swap
# provably balanced. REENTRANT so a nested recording (a caller that dissects
# inside its own recording block) cannot deadlock: the inner one captures the
# outer recorder as its ``original``, delegates to it — so both lists fill —
# and restores it on the way out.
_RECORD_LOCK = threading.RLock()

# The A-side keyword arguments `_connector_centerline` reads in WORD
# coordinates: a replay that moves A must move them with it, or the fork
# retrace and the bar launch would aim at the letter's old position.
_EXIT_SIDE_LINE_FLAGS = ("fork_line",)
_EXIT_SIDE_POINT_FLAGS = ("stem_launch",)


@dataclass(frozen=True)
class JoinCall:
    """One production call of ``core.compose._connector_centerline``, verbatim.

    ``from_slot``/``to_slot`` are attached afterwards from the composed
    connector items (the generator emits one item per generated join, in
    composition order — the same order the calls arrive in). Everything else is
    the call itself: its positional arguments, the keyword flags production
    computed for this join, and what came back.
    """

    exit_pt: Point
    exit_tangent_deg: float
    first_line: tuple[Point, ...]
    dx: float
    flags: Mapping[str, object]
    centerline: tuple[Point, ...]  # what production drew, in word coordinates
    entry_trim: int
    from_slot: int = -1
    to_slot: int = -1
    pair: tuple[str | None, str | None] = (None, None)


@contextmanager
def recording() -> Iterator[list[JoinCall]]:
    """Record every ``_connector_centerline`` call made inside the block.

    The yielded list fills as compositions run and keeps composition order. The
    recorder delegates to the real function and returns its result untouched, so
    nothing composed inside the block differs from the same composition outside
    it.
    """
    with _RECORD_LOCK:
        calls: list[JoinCall] = []
        original = compose._connector_centerline

        def recorder(
            exit_pt: Point, exit_tangent_deg: float, first_line: list[Point], dx: float, **flags: object
        ) -> tuple[list[Point], int]:
            centerline, entry_trim = original(exit_pt, exit_tangent_deg, first_line, dx, **flags)
            calls.append(
                JoinCall(
                    exit_pt=(float(exit_pt[0]), float(exit_pt[1])),
                    exit_tangent_deg=float(exit_tangent_deg),
                    first_line=tuple((float(x), float(y)) for x, y in first_line),
                    dx=float(dx),
                    flags=dict(flags),
                    centerline=tuple((float(x), float(y)) for x, y in centerline),
                    entry_trim=int(entry_trim),
                )
            )
            return centerline, entry_trim

        compose._connector_centerline = recorder  # type: ignore[assignment]
        try:
            yield calls
        finally:
            compose._connector_centerline = original  # type: ignore[assignment]


def label_calls(composed: dict, calls: Sequence[JoinCall]) -> dict[int, JoinCall]:
    """Recorded calls keyed by the LEFT slot index of the join they drew.

    ``compose_word(provenance=True)`` emits one connector item per generated
    join, carrying ``from_slot``/``to_slot``/``pair``, in the order the joins
    were drawn — the order the calls were recorded in. An APPROVED pair override
    draws its stored centerline without calling the generator and is therefore
    absent from both sequences; the word-final Endstrich carries ``pair`` with a
    None right half and is no join at all.

    Raises ``ValueError`` when the two sequences do not line up: a silent
    misalignment would attribute one join's geometry to another, and every
    number downstream would be quietly wrong.
    """
    items = [
        item
        for item in composed.get("items", [])
        if item.get("pair") and item["pair"][1] is not None and not item.get("override")
    ]
    if len(items) != len(calls):
        raise ValueError(
            f"connector items ({len(items)}) and recorded generator calls ({len(calls)}) disagree — "
            "the composition was not the one that was recorded"
        )
    out: dict[int, JoinCall] = {}
    for item, call in zip(items, calls, strict=True):
        from_slot = int(item["from_slot"])
        pair = item["pair"]
        out[from_slot] = JoinCall(
            exit_pt=call.exit_pt,
            exit_tangent_deg=call.exit_tangent_deg,
            first_line=call.first_line,
            dx=call.dx,
            flags=call.flags,
            centerline=call.centerline,
            entry_trim=call.entry_trim,
            from_slot=from_slot,
            to_slot=int(item["to_slot"]),
            pair=(pair[0], pair[1]),
        )
    return out


def derive_with_joins(case: WordCase) -> tuple[WordDeriveResult, dict[int, JoinCall]]:
    """``derive_word`` plus the production join calls it made, keyed by left slot."""
    with recording() as calls:
        result = derive_word(case)
    return result, label_calls(result.composed, calls)


def joins_for(result: WordDeriveResult) -> dict[int, JoinCall]:
    """The join calls of an ALREADY derived case, without re-scoring it.

    Recomposes from the result's own payloads under the recorder — the same
    inputs `derive_word` used, so the composition is the one whose items label
    the calls (``label_calls`` raises if it ever is not). Costs one composition,
    never the metric run; a caller that composes anyway should prefer
    ``derive_with_joins``.
    """
    with recording() as calls:
        compose.compose_word(
            result.case.slots,
            result.payloads,
            provenance=True,
            laufform_by_key=laufform_payloads_for(result.case) or None,
        )
    return label_calls(result.composed, calls)


def replay(call: JoinCall, *, exit_shift: Point = (0.0, 0.0), entry_shift: Point = (0.0, 0.0)) -> list[Point]:
    """The production connector of ``call``, with A moved by ``exit_shift`` and
    B by ``entry_shift`` (composed units, y up).

    Both shifts default to zero, in which case the returned centerline is the
    recorded one point for point — the parity the test asserts. The grammar is
    not touched: which branch fires at the shifted geometry is production's own
    decision, evaluated on the moved inputs, exactly as it would be for a
    composition that had placed the letters there.

    What this is NOT is the drawn stroke. ``compose_word`` still prepends a
    capital's ornament retrace and overlap-extends both ends by
    ``CONNECT_OVERLAP`` before emitting the item, and neither belongs to the
    join's shape: the retrace is ink the LETTER already drew, and the extension
    is an inking allowance so the round cap tucks under the neighbouring stroke.
    Every consumer here wants the bare join — the dissection measures the
    generated curve against the specimen, and ``chain._connector_spec`` says so
    in as many words. That the two dressings are the ONLY difference is asserted
    against the emitted item in ``tests/test_pairlab_connector_parity.py``, so
    the parity proof is not self-referential.

    **The one standing blind spot, named so it cannot rot.** Not every decision
    about a join happens inside ``_connector_centerline``. The exit trim
    (``exit_trim``, arm J4) REPLACES the returned centerline afterwards, in
    ``compose_word``'s own block — so a replay reproduces the join as it would
    be WITHOUT that rule, and any future rule that post-processes the connector
    the same way would be invisible here too. Harmless today: the switch is off
    by default, so on every headline run the replay is the whole story. Should
    such a rule ever become the default, this function has to grow the same
    post-processing or the dissection will quietly measure the wrong curve.
    ``spanmeas`` sidesteps the question entirely by reading the DRAWN join and
    undoing only the two dressings (``spanmeas.drawn_join``), which is why the
    J4 arm moves there and would not move here.
    """
    flags = dict(call.flags)
    if exit_shift != (0.0, 0.0):
        for name in _EXIT_SIDE_LINE_FLAGS:
            line = flags.get(name)
            if line:
                flags[name] = [(x + exit_shift[0], y + exit_shift[1]) for x, y in line]  # type: ignore[union-attr]
        for name in _EXIT_SIDE_POINT_FLAGS:
            point = flags.get(name)
            if point:
                flags[name] = (point[0] + exit_shift[0], point[1] + exit_shift[1])  # type: ignore[index]
    # B's lead-in lives in the pre-placement frame: `_connector_centerline`
    # couples at `(first_line[k][0] + dx, first_line[k][1])`, so B's horizontal
    # move belongs on `dx` and only its vertical move on the line itself.
    first_line = (
        [(x, y + entry_shift[1]) for x, y in call.first_line] if entry_shift[1] else [tuple(p) for p in call.first_line]
    )
    centerline, _ = compose._connector_centerline(
        (call.exit_pt[0] + exit_shift[0], call.exit_pt[1] + exit_shift[1]),
        call.exit_tangent_deg,
        first_line,
        call.dx + entry_shift[0],
        **flags,  # type: ignore[arg-type]
    )
    return centerline
