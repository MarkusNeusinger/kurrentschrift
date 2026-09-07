"""The counter constraint: the plate's open Binnenflächen as a term IN the solve.

Rescue path (3) of the R3 row in `tintenfolger.md` §7.9, and the arm R3c of §14.
R3 (`sep07`) put the same statement about the ink BEHIND the follower as a
point-wise push and measured the formulation out: 107 of 108 counters opened,
but the aperture landed within the pre-registered ±0.02 xh in only 83 of them
and the correction added 1626 `kink` events, because the blend windows are
declared in pen widths while the trace carries a support point every 0.0265 xh.
Both readings hang on the SAME length, so a post-hoc correction has to choose
between hitting its target and staying smooth. R3b moved that length one rung up
the frozen ladder and confirmed the trade in both directions.

**This module states the same condition where the smoothness already comes
from.** The follower's rounds solve for ANCHORS and read the fields at SAMPLES:
a per-sample force folds back through the sampling operator onto a much sparser
anchor set, and the Tikhonov, connector-smoothness and structure terms are all
in the same objective. So the solver resolves aperture and smoothness against
each other with the machinery that already keeps the trace smooth, instead of a
fade whose length has to be guessed.

THE CONDITION, unchanged from R3 and stated once. A Gleichzug pen of half width
`w` paints the Minkowski sum of its path with a disc of radius `w`, so a point
of the plate's counter is inked exactly when some pen sample lies within `w` of
it. Read backwards: **no pen sample may sit closer than `w_pen` to a counter the
plate holds open.** `w_pen` is the plate's own nib (0.0968 xh, #551), frozen in
`tools.tracebench.kringel` and never softened here — lowering it until fewer
loops need correcting is the pen softening the Kringel diagnosis rules out.

WHAT THE SOLVE SEES. A single scalar field per word — the SIGNED distance to the
union of the in-scope counters, positive outside and negative inside — and a
quadratic hinge on it:

    e_counter = mean_i max(0, w_target − φ(p_i))² / unit²

normalised exactly like `e_geo`, so its weight is directly comparable to the ink
term's 1.0. Outside a counter φ is bit-for-bit the distance field R3 pushed
along (`distance_transform_edt` of the counter's complement), so the two arms
aim at the same level set; inside it R3 had to REFUSE (no outward direction to
push along), while the signed field simply carries on and the hinge grows — the
solve gets a well-defined outward force where the post-hoc path had none.

THREE THINGS THIS ARM DELIBERATELY DOES NOT BRING ALONG from R3:

* **No fade, no anti-raster average.** They exist only because a point-wise push
  has no other way to be smooth. Here the anchors are the smoothing.
* **No closure acceptance rule.** R3 had to revert a push that pulled a loop's
  own self-crossing open (`REFUSAL_CLOSURE_LOST`, 10 of 108). The follower
  already rejects exactly that: `structure_guard` with the composition Soll
  refuses a round that LOSES an initialisation crossing. One acceptance rule,
  not two.
The SIZE CLASSES stay R3's (`klein`, `mittel`), which the first draft of this
module got wrong and a calibration probe corrected before any arm number: a
`gross` counter is not satisfied at the base either, so it binds — hardest of
all, because it is the widest — while buying nothing, since three quarters of a
large hole survives any pen and the loop is open at 0.097 with or without the
condition. See `COUNTER_SIZE_CLASSES`.

SCOPE, and it is the catalogue's. A counter enters the field when the frozen
catalogue (`tools/tracebench/kringel_catalogue.json`, #556) registers the loop
it belongs to as `offen` in size class `klein` or `mittel` AND the plate shows
the hole in this very occurrence.
Which counter belongs to which loop is #556's Slot-Lineal, taken verbatim from
`tools.pairlab.zweizuege.catalogue_targets` rather than re-implemented — a flat
proximity search hands a loop the NEIGHBOUR's hole (#553).

Measurement layer only: no DB, no `core/` byte, no ruler. `fit_word_chain` is
untouched, so every consumer of the chain outside the follower — the harvest
included — is byte-identical by construction.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from core.fit import DIST_FIELD_SIGMA_PX
from tools.pairlab.zweizuege import (
    MATCH_RADIUS_UNITS,
    MIN_COUNTER_PX,
    RASTER_HALF_PIXEL,
    ZweiZuegeOptions,
    catalogue_targets,
    loop_aperture_near,
    plate_counters,
)
from tools.tracebench.kringel import PLATE_PEN_HALF_WIDTH_UNITS, SIZE_CLASSES, catalogue_source, load_catalogue


# The states whose counters the condition applies to. `offen` and nothing else:
# a `wechselnd` loop is one the PLATE closes in some occurrences, and `punkt` is
# a loop with no aperture to hold — constraining either would be the instrument
# overruling the evidence.
COUNTER_STATES = ("offen",)

# R3's own two classes, and the calibration probe of `sep07` is why. The first
# draft of this arm took every size class on the reasoning that a satisfied
# constraint is inert — true, but the Kette's LARGE loops are not satisfied
# either (they run tight like the small ones; that is the Kringel diagnosis),
# so a `gross` counter binds hardest of all while contributing nothing to the
# defect count it is aimed at: three quarters of a large hole survives any pen,
# so the loop is open at 0.097 either way. On `das` the `s`#0 counter (0.6121,
# target D0 0.8057) dominated the whole word and the structure guard rejected
# the round outright. Two reasons to stay with R3's classes: the movement buys
# nothing measurable, and a conversion arm that changes the SCOPE as well as the
# placement of the condition is no longer a single-factor step against the round
# it converts. The wider scope stays reachable through `--counter-size-classes`
# as an arm of its own.
COUNTER_SIZE_CLASSES = ("klein", "mittel")
COUNTER_SIZE_CLASSES_ALL = tuple(SIZE_CLASSES)

# Half a pixel, the same declared convention R3 states and for the same reason:
# a distance transform measures centre to centre, so a hole's raster reading is
# half a pixel generous on each side and BOTH sides of the arithmetic have to be
# read the same generous way. The condition therefore aims at `w_pen + 0.5 px`,
# the level set at which a pen of `w_pen` stroked on the same raster leaves the
# hole uncovered including its half-pixel rim.

# The field is smoothed with the ink field's own sigma before the objective
# reads it — the same machinery, for the same two reasons: a bilinear read of a
# smoothed field gives L-BFGS-B a landscape of the class it already descends,
# and one pixel of blur is what filters the ±0.5 px raster noise that R3's §14
# entry names as the cause of its 1626 kinks. It has a declared price: blurring
# a signed distance field moves its level set inward by about κσ²/2, i.e. ~0.15
# px ≈ 0.005 xh at the tightest counters. That is NOT compensated for anywhere —
# it shows up in the measured aperture of gate (a) instead of being assumed
# away.
COUNTER_FIELD_SIGMA_PX = DIST_FIELD_SIGMA_PX

REFUSAL_NO_MASK = "no frozen ink mask on the case"
REFUSAL_FOREIGN_HAND = "the catalogue belongs to another hand"
REFUSAL_NO_TARGET = "no catalogue counter of this word is in scope"


@dataclass(frozen=True)
class CounterFieldOptions:
    """One configuration of the constraint — frozen, stamped into every artefact."""

    half_width_units: float = PLATE_PEN_HALF_WIDTH_UNITS
    states: tuple[str, ...] = COUNTER_STATES
    size_classes: tuple[str, ...] = COUNTER_SIZE_CLASSES
    min_counter_px: int = MIN_COUNTER_PX
    sigma_px: float = COUNTER_FIELD_SIGMA_PX


@dataclass
class CounterField:
    """The word's counter condition: one field, one level set, and its scope."""

    field_px: np.ndarray
    """Signed distance to the union of the in-scope counters, in crop pixels —
    positive outside, negative inside, smoothed with `sigma_px`."""
    raw_px: np.ndarray
    """The same field UNSMOOTHED, for the report path; the objective never
    reads it (the `dist_raw`/`dist_smooth` split of `_ChainProblem`)."""
    target_px: float
    """`w_pen · xh + 0.5 px` — the level set no sample may cross."""
    rows: list[dict[str, Any]] = field(default_factory=list)
    """One row per catalogue loop in scope, constrained or not: slot, glyph,
    loop rank, class, state, the plate counter's aperture, the expectation
    `counter + 2·w_pen` it implies and — for the constrained ones — the composed
    loop's centre, which is where the aperture is read. A loop the plate shows
    no hole for carries its refusal, because a refusal is as much of a reading
    as a constraint."""
    reason: str = ""
    """Empty exactly when the field constrains something."""

    @property
    def active(self) -> bool:
        return not self.reason

    def as_dict(self) -> dict[str, Any]:
        return {
            "target_px": round(float(self.target_px), 4),
            "n_counters": sum(1 for r in self.rows if r.get("target_d0_units") is not None),
            "n_rows": len(self.rows),
            "reason": self.reason,
            "rows": self.rows,
        }


def signed_counter_distance(counter_mask: np.ndarray) -> np.ndarray:
    """Signed distance to a pixel set: `+` outside, `−` inside, zero between.

    Outside the set this is exactly `distance_transform_edt(~mask)` — the very
    field R3's push read — so the two arms aim at the same level set and their
    apertures are comparable without a conversion. The inside branch is the
    addition: R3 had to refuse a sample that had wandered INTO a counter (no
    outward direction to push along, 19 of its 162 loops), whereas a signed
    field gives the solver a force there that grows with the depth.
    """
    from scipy.ndimage import distance_transform_edt  # noqa: PLC0415 — heavy import, few call sites

    sel = np.asarray(counter_mask, dtype=bool)
    if not sel.any():
        # „Everywhere is far from nothing", as a finite number: an infinity here
        # would survive the caller's Gaussian as a NaN and turn an empty scope
        # into a broken objective instead of an inert one.
        return np.full(sel.shape, float(sum(sel.shape)), dtype=float)
    return distance_transform_edt(~sel) - distance_transform_edt(sel)


def build_counter_field(
    *,
    mask: np.ndarray | None,
    composed_items: Sequence[dict[str, Any]],
    catalogue: dict[str, list[dict[str, Any]]],
    xh_px: float,
    tx: float,
    ty: float,
    baseline_row: float,
    options: CounterFieldOptions | None = None,
) -> CounterField:
    """The signed counter field of ONE word, plus the scope it was built from.

    Pure geometry on the frozen mask and the frozen catalogue — no case object,
    no fixture root, no DB, so a synthetic blob is a first-class caller.
    """
    from scipy.ndimage import distance_transform_edt, gaussian_filter  # noqa: PLC0415

    opts = options or CounterFieldOptions()
    empty = np.zeros((1, 1))
    if mask is None:
        return CounterField(field_px=empty, raw_px=empty, target_px=0.0, reason=REFUSAL_NO_MASK)
    ink = np.asarray(mask, dtype=bool)
    labels, counters = plate_counters(ink, min_px=opts.min_counter_px)
    # The scope is #556's Slot-Lineal, run through R3's own reader rather than a
    # second implementation: same catalogue, same one-to-one match inside the
    # letter, same refusal vocabulary. Only the two class filters differ, and
    # they are arguments.
    targets, rows = catalogue_targets(
        composed_items,
        catalogue,
        counters,
        distance_transform_edt(ink),
        xh_px=xh_px,
        tx=tx,
        ty=ty,
        baseline_row=baseline_row,
        options=ZweiZuegeOptions(
            half_width_units=opts.half_width_units,
            states=tuple(opts.states),
            size_classes=tuple(opts.size_classes),
            min_counter_px=opts.min_counter_px,
        ),
    )
    # The composed loop's centre travels with the row: it is WHERE gate (a)
    # reads the aperture, and `LoopCorrection` carries it only in the tuple.
    # Keyed by identity because the entries in `targets` ARE the ones in `rows`.
    centres = {id(entry): centre for _counter, entry, centre in targets}
    row_dicts = [
        {**row.as_dict(), "counter_centre_units": [round(c, 4) for c in centres[id(row)]]}
        if id(row) in centres
        else row.as_dict()
        for row in rows
    ]
    if not targets:
        return CounterField(field_px=empty, raw_px=empty, target_px=0.0, rows=row_dicts, reason=REFUSAL_NO_TARGET)
    in_scope = sorted({int(counter.label) for counter, _entry, _centre in targets})
    raw = signed_counter_distance(np.isin(labels, in_scope))
    return CounterField(
        field_px=gaussian_filter(raw, opts.sigma_px) if opts.sigma_px > 0.0 else raw,
        raw_px=raw,
        target_px=float(opts.half_width_units) * float(xh_px) + RASTER_HALF_PIXEL,
        rows=row_dicts,
    )


def counter_field_for_case(case: Any, result: Any, *, options: CounterFieldOptions | None = None) -> CounterField:
    """`build_counter_field` for a `WordCase` + its derivation — the caller's door.

    Two refusals live here rather than in the geometry, exactly as in
    `zweizuege.correct_case_strokes`: a catalogue that cannot be read, and a
    catalogue read off ANOTHER hand. The Kringel catalogue is one hand with one
    pen. Neither costs the caller its run; both cost the constraint and say why.
    """
    opts = options or CounterFieldOptions()
    try:
        catalogue = load_catalogue()
        source = catalogue_source()
    except (OSError, ValueError) as exc:  # noqa: BLE001 — a missing catalogue is a refusal, not a crash
        empty = np.zeros((1, 1))
        return CounterField(
            field_px=empty, raw_px=empty, target_px=0.0, reason=f"catalogue unavailable ({type(exc).__name__}: {exc})"
        )
    measured_on = str((source.get("measured_on") or [{}])[0].get("name", ""))
    origin = str(getattr(case, "origin", "") or "").split(":", 1)[-1]
    if measured_on != origin:
        empty = np.zeros((1, 1))
        return CounterField(
            field_px=empty,
            raw_px=empty,
            target_px=0.0,
            reason=f"{REFUSAL_FOREIGN_HAND}: catalogue on {measured_on or '?'}, case from {origin or '?'}",
        )
    return build_counter_field(
        mask=getattr(case, "mask", None),
        composed_items=result.composed["items"],
        catalogue=catalogue,
        xh_px=float(result.xh_px),
        tx=float(result.registration["tx"]),
        ty=float(result.registration["ty"]),
        baseline_row=float(result.baseline_row),
        options=opts,
    )


# ----------------------------------------------------- the gate (a) instrument


def loop_apertures_of_trace(
    strokes_units: Sequence[Sequence[Sequence[float]]],
    counter_field: CounterField,
    *,
    xh_px: float,
    tx: float,
    ty: float,
    baseline_row: float,
    radius_units: float = MATCH_RADIUS_UNITS,
) -> list[dict[str, Any]]:
    """Per in-scope loop: the aperture THIS trace draws around that counter.

    The reading is R3's, verbatim (`zweizuege.loop_aperture_near`): the diameter
    of the largest circle inside the region the closed centreline loop encloses,
    rastered in a window around the counter, no splinter floor — a COLLAPSED
    loop has to stay visible as a small number rather than be filtered away.
    Comparing it against `counter + 2·w_pen` is gate (a), and running it from
    here rather than inside the arm is what lets base and arm be read with one
    instrument.
    """
    out: list[dict[str, Any]] = []
    for row in counter_field.rows:
        target = row.get("target_d0_units")
        if target is None:
            out.append({**row, "d0": None})
            continue
        centre = row.get("counter_centre_units")
        if centre is None:
            out.append({**row, "d0": None})
            continue
        d0 = loop_aperture_near(strokes_units, (float(centre[0]), float(centre[1])), radius_units=radius_units)
        out.append({**row, "d0": None if d0 is None else round(float(d0), 4)})
    return out


def _load_candidate(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    """Print the per-loop aperture table of one candidate, optionally paired.

    The gate (a) reader of the R3c round: for every catalogue loop in scope it
    lists the plate's counter, the expectation `counter + 2·w_pen`, and the
    aperture the candidate's own trace draws around it. With `--base` the same
    table for a second candidate is put beside it, one row per loop.
    """
    parser = argparse.ArgumentParser(prog="pairlab.counterfield", description=main.__doc__)
    parser.add_argument("candidate", type=Path, help="a follower candidate JSON")
    parser.add_argument("--base", type=Path, help="a second candidate, read with the same instrument")
    parser.add_argument("--style", default="suetterlin")
    parser.add_argument("--which", default="words", choices=["words", "pairs"])
    parser.add_argument("--fixtures", type=Path, default=Path("tools/wordbench/fixtures"))
    parser.add_argument("--json", type=Path, help="write the full per-loop rows here")
    args = parser.parse_args()

    from tools.wordlab.cases import iter_fixture_word_cases  # noqa: PLC0415
    from tools.wordlab.derive import derive_word  # noqa: PLC0415

    arm = {row["specimen_id"]: row for row in _load_candidate(args.candidate)["rows"]}
    base = {row["specimen_id"]: row for row in _load_candidate(args.base)["rows"]} if args.base else {}
    cases = {
        c.id: c
        for c in iter_fixture_word_cases(
            which=args.which, style=args.style, only=list(arm), fixtures_root=args.fixtures
        )
    }
    rows_out: list[dict[str, Any]] = []
    for specimen_id, row in arm.items():
        case = cases.get(specimen_id)
        if case is None:
            continue
        result = derive_word(case)
        cf = counter_field_for_case(case, result)
        if not cf.rows:
            continue
        frame = {
            "xh_px": float(row["xh_px"]),
            "tx": float(result.registration["tx"]),
            "ty": float(result.registration["ty"]),
            "baseline_row": float(result.baseline_row),
        }
        arm_rows = loop_apertures_of_trace(row["strokes"], cf, **frame)
        base_rows = (
            loop_apertures_of_trace(base[specimen_id]["strokes"], cf, **frame) if specimen_id in base else arm_rows
        )
        for a, b in zip(arm_rows, base_rows, strict=True):
            rows_out.append({"specimen_id": specimen_id, **a, "d0_base": b["d0"]})
    print(f"{len(rows_out)} catalogue loops in scope over {len(cases)} words")
    for row in rows_out:
        target = row.get("target_d0_units")
        print(
            f"  {row['specimen_id']:<16} {str(row['glyph']):>4}#{row['loop']}  {row['state']:<9}"
            f" {row['size_class']:<7} target={'—' if target is None else f'{target:.4f}'}"
            f" base={'—' if row['d0_base'] is None else f'{row["d0_base"]:.4f}'}"
            f" arm={'—' if row['d0'] is None else f'{row["d0"]:.4f}'}"
            f"  {row.get('reason', '')}"
        )
    if args.json:
        args.json.write_text(json.dumps(rows_out, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
