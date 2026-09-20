"""Assign the letter boundaries of a Bahn nobody decoded — the Span-Zuordner.

A followed Bahn gets its boundaries for free. The Tintenpfad decodes the ink
against a composed seed, every emitted sample inherits the slot of the seed
sample that put it there, and the letter assignment IS the alignment
(``tools.pairlab.tintenpfad``, ``spans_of``). A Bahn the AUTHOR drew has no
decode behind it: there is no seed sample per drawn point, and there is nothing
to inherit from. So the assignment is new work rather than a call into
something that exists — the author's own note A48 of 2026-09-13 says exactly
that, and this module is what it asked for.

WHAT IT DOES. The same seed the follower would have decoded against is built
for the word box — the composition, registered to the ink by ``derive_word``
and moved per letter by ``register_letters``, resampled in writing order with a
slot label per sample. Then every sample of the DRAWN Bahn is matched to a seed
sample and takes its slot. Two matching rules exist and only the first is the
standard one:

* ``dtw`` — a monotone alignment: over one drawn stroke the matched seed index
  may only move forward, so the letters come out in writing order even where a
  loop passes close to the letter before it;
* ``nearest`` — each sample alone with its nearest seed sample. The control the
  monotone rule is measured against (messjournal §14 „Span-Zuordner `sep20`"),
  kept because a base nobody can re-run is not a base.

Strokes are matched INDEPENDENTLY of one another. A mark written after the body
— the i-dot, an umlaut — is a later pen-down over an earlier letter, so a rule
that forced the seed index forward across strokes would push exactly those
marks onto the wrong letter.

WHAT IT NEVER DOES. It never replaces a boundary the author corrected by hand.
That rule lives in the field guard (``core.eigenhand.pfad``, `herkunft`) and is
enforced server-side, but the tool does not even try: an authored boundary and
the whole stored set of its stroke travel untouched, and the run says so. An
`auto` boundary is a derivation a later run makes again; an authored one is
ground truth and the training material of this very assigner.

THE SEED IS A PRIOR, NOT A MEASUREMENT. It says where the letters of this word
WOULD sit if the hand wrote the plate's forms. The drawn Bahn is the hand. So
the assignment is only as good as the two agreeing, which is why every run
reports how far the Bahn sat from the seed rather than hiding it in a verdict.
"""

from __future__ import annotations

import os


# Before numpy: the composition and the affine registration behind the seed are
# the same chain solve `tools.eigenhand.pfad` pins its threads for, and an
# assignment that differed between two machines would be unreadable as a
# measurement (CLAUDE.md, the BLAS rule of 2026-08-16). Defaults only.
for _var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
from collections.abc import Mapping, Sequence  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

import numpy as np  # noqa: E402

from core.eigenhand.pfad import MAX_SPANS, SPAN_AUTO  # noqa: E402


# The matching rules, standard first. A name outside this tuple is refused
# rather than falling back: a run whose arm silently became another arm is the
# failure the campaign has twice paid for (`/verify-trace`, step 2).
METHODS = ("dtw", "nearest")
DEFAULT_METHOD = "dtw"

# How far the round's hand simulator pushes a followed Bahn off the seed, in
# x-heights (`wobbled`). A sixth of a letter body: enough that the Bahn is no
# longer the seed's own product, little enough that it is still this word.
DEFAULT_WOBBLE_XH = 0.15


def crop_points(stroke: Any, registration: Mapping[str, Any], xh_px: float) -> np.ndarray:
    """Word units → the CROP's own pixels, the frame the seed is built in.

    The twin of `tools.eigenhand.pfad._crop_px`, and deliberately its own copy
    for the same reason that one is: this is the arithmetic the whole
    assignment stands on, and the follower's private inverse is not a contract.
    """
    pts = np.asarray(stroke, dtype=float).reshape(-1, 2)
    tx, ty = float(registration["tx"]), float(registration.get("ty", 0.0))
    baseline_row = float(registration["baseline_row"])
    return np.column_stack([pts[:, 0] * xh_px + tx, baseline_row + ty - pts[:, 1] * xh_px])


def _prefix_argmin(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Running minimum of `values` and, beside it, the index it came from.

    numpy has `minimum.accumulate` but no `argmin.accumulate`, and the
    alignment needs both: the cost to carry forward and the seed index to walk
    back through. A position starts a new minimum exactly where its value is
    below every value before it, and the argument is then the running maximum
    over those positions — two accumulations instead of a Python loop over the
    seed.
    """
    running = np.minimum.accumulate(values)
    fresh = np.empty(len(values), dtype=bool)
    fresh[0] = True
    fresh[1:] = values[1:] < running[:-1]
    return running, np.maximum.accumulate(np.where(fresh, np.arange(len(values)), 0))


def match_seed(drawn: np.ndarray, seed_xy: np.ndarray, *, method: str = DEFAULT_METHOD) -> np.ndarray:
    """The seed sample each drawn sample belongs to — one index per drawn point.

    `nearest` answers per point and knows nothing about order. `dtw` is the
    standard rule: the matched seed index may never move backwards along the
    stroke, and it may jump forward as far as it likes — a hand writes one
    letter after the other, but it does not spend the same arc on every one, so
    a step-by-step alignment would be a claim about speed rather than order.

    The distance matrix is never materialised. One drawn sample against the
    whole seed is a vector; the alignment needs only the previous row's running
    minimum, so the cost of a long word is its backtrack table and not an
    (n × m) float plane.
    """
    if method not in METHODS:
        raise ValueError(f"unknown matching rule {method!r} — one of {', '.join(METHODS)}")
    points = np.asarray(drawn, dtype=float).reshape(-1, 2)
    seed = np.asarray(seed_xy, dtype=float).reshape(-1, 2)
    if not len(points) or not len(seed):
        return np.zeros(len(points), dtype=np.int64)
    if method == "nearest":
        return np.array(
            [int(np.argmin(np.hypot(seed[:, 0] - p[0], seed[:, 1] - p[1]))) for p in points], dtype=np.int64
        )
    cost = np.hypot(seed[:, 0] - points[0, 0], seed[:, 1] - points[0, 1])
    back = np.empty((len(points), len(seed)), dtype=np.int32)
    for i in range(1, len(points)):
        running, where = _prefix_argmin(cost)
        back[i] = where
        cost = np.hypot(seed[:, 0] - points[i, 0], seed[:, 1] - points[i, 1]) + running
    out = np.empty(len(points), dtype=np.int64)
    j = int(np.argmin(cost))
    out[-1] = j
    for i in range(len(points) - 1, 0, -1):
        j = int(back[i, j])
        out[i - 1] = j
    return out


def seed_distance_xh(drawn: np.ndarray, seed_xy: np.ndarray, matched: np.ndarray, xh_px: float) -> np.ndarray:
    """How far each drawn sample sat from the seed sample it was given, in x-heights.

    Reported rather than acted on. The seed says where the letters WOULD sit if
    this hand wrote the plate's forms; a Bahn that sits far from it is still the
    hand, so a threshold here would silently refuse the very material the own
    hand exists to collect. What it is good for is reading a bad assignment
    afterwards without opening the strip.
    """
    points = np.asarray(drawn, dtype=float).reshape(-1, 2)
    seed = np.asarray(seed_xy, dtype=float).reshape(-1, 2)
    if not len(points) or not len(seed):
        return np.zeros(0)
    picked = seed[np.asarray(matched, dtype=int)]
    return np.hypot(picked[:, 0] - points[:, 0], picked[:, 1] - points[:, 1]) / float(xh_px)


def label_strokes(
    strokes_px: Sequence[np.ndarray], seed_xy: np.ndarray, seed_slot: np.ndarray, *, method: str = DEFAULT_METHOD
) -> list[np.ndarray]:
    """One slot label per sample of every drawn stroke, connectors included as −1."""
    slots = np.asarray(seed_slot, dtype=int)
    return [slots[match_seed(stroke, seed_xy, method=method)] for stroke in strokes_px]


def runs_of(labels: Sequence[np.ndarray]) -> list[list[list[int]]]:
    """`[[slot, first, last], …]` per stroke — the twin of `tintenpfad.spans_of`.

    Spelled here rather than imported so that reading a stored Bahn does not
    pull in the follower's whole solver stack, and pinned against the original
    by `tests/test_eigenhand_spans.py`: the two shapes have to stay identical
    or the §14 round compares an assignment with a differently-cut version of
    itself rather than with the follower's.

    A connector sample (−1) inherits the nearest letter label, exactly as the
    follower's spans do — a boundary is a seam between two letters, and leaving
    the ink between them unlabelled would make every join a gap the editor
    cannot drag across.
    """
    out: list[list[list[int]]] = []
    for label in labels:
        lab = np.asarray(label, dtype=int).copy()
        known = np.flatnonzero(lab >= 0)
        if len(known):
            for position in np.flatnonzero(lab < 0):
                lab[position] = lab[known[np.argmin(np.abs(known - position))]]
        spans, start = [], 0
        for position in range(1, len(lab) + 1):
            if position == len(lab) or lab[position] != lab[start]:
                spans.append([int(lab[start]), int(start), int(position - 1)])
                start = position
        out.append(spans)
    return out


def flat_spans(
    nested: Sequence[Sequence[Sequence[int]]], strokes: Sequence[Sequence[Any]], *, herkunft: str = SPAN_AUTO
) -> list[dict[str, Any]] | None:
    """The nested per-stroke shape as the checked `letter_spans` field, or None.

    `None` where the boundaries do not describe THESE strokes any more, and the
    check is deliberately stricter than „every index is in range". Both
    producers cover a stroke sample for sample — the follower's `spans_of` and
    `runs_of` above —, so anything short of full, gapless coverage means the
    strokes were re-cut underneath the labels: `tools.pairlab.trace.
    cap_word_strokes` thins a Bahn past 128 runs and downsamples past 4096
    points, and after a downsample every index is still well-formed and points
    at the wrong ink. That is the silent failure `core.eigenhand.pfad.
    _checked_spans` would never catch, because it can only ask whether an index
    exists.

    A span whose slot is −1 is dropped rather than written: it means the seed
    had no letter at all anywhere on that stroke, which is „no letter here" and
    not letter number minus one.

    `MAX_SPANS` is answered here and nowhere else in this chain. The bound
    belongs to the stored field, and a box that crossed it would otherwise take
    the whole Fassung's push down with a 422 over boundaries nobody looked at —
    a derivation the next run makes again is not worth that.
    """
    if len(nested) != len(strokes):
        return None
    out: list[dict[str, Any]] = []
    for stroke_index, (spans, stroke) in enumerate(zip(nested, strokes, strict=True)):
        cursor = 0
        for slot, first, last in spans:
            if first != cursor or last < first:
                return None
            cursor = last + 1
            if slot >= 0:
                out.append(
                    {
                        "stroke": stroke_index,
                        "slot": int(slot),
                        "first": int(first),
                        "last": int(last),
                        "herkunft": herkunft,
                    }
                )
        if cursor != len(stroke):
            return None
    return None if len(out) > MAX_SPANS else (out or None)


def seed_for_case(case: Any, weights: Any) -> tuple[np.ndarray, np.ndarray, float] | None:
    """The composed word registered on this box's ink: sample positions, slots, x-height.

    Built exactly as `tools.pairlab.tintenpfad.follow_word` builds it, down to
    the ink evidence the per-letter affine is registered on — the point of this
    module is that a drawn Bahn is matched against the SAME seed a followed one
    was decoded against, so a difference in the assignment is a difference in
    the matching rule and nothing else.

    `None` where the composition itself failed; the caller reports that as the
    reason there are no boundaries, which is a different finding from „the
    assignment was poor".

    The heavy imports sit inside the function like the follower's own: reading
    a stored path and printing it must not pull in the solver stack.
    """
    from tools.pairlab.affinereg import register_letters
    from tools.pairlab.ink_evidence import INK_EVIDENCE_PAPER_FRACTION, InkEvidenceOptions, ink_evidence_case
    from tools.pairlab.tintenpfad import seed_samples
    from tools.wordlab.derive import derive_word

    result = derive_word(case)
    if result.report is None or result.report.get("failed") or not result.registration:
        return None
    xh_px = float(result.xh_px)
    evidence, _ = ink_evidence_case(case, InkEvidenceOptions(paper_fraction=INK_EVIDENCE_PAPER_FRACTION))
    affine = register_letters(evidence, result) if weights.affine_seed else None
    seed = seed_samples(result, xh_px, weights, affine)
    return np.asarray(seed.xy, dtype=float), np.asarray(seed.slot, dtype=int), xh_px


def assign(
    case: Any,
    strokes: Sequence[Sequence[Sequence[float]]],
    registration: Mapping[str, Any],
    xh_px: float,
    weights: Any,
    *,
    method: str = DEFAULT_METHOD,
) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    """The letter boundaries of one drawn Bahn, plus what the run should print.

    `registration` is the CROP's frame, not the strip's — the seed is built in
    the crop the composition was registered on, and the caller that holds a
    stored strip entry subtracts the box rectangle first (the inverse of what
    `tools.eigenhand.pfad._entry` adds on the way in).

    The second element always says something, including on a refusal: `reason`
    is what the operator reads when no boundaries came out, and it is a
    statement about THIS box rather than about the assigner.
    """
    if not strokes or not any(len(stroke) for stroke in strokes):
        return None, {"reason": "the Bahn carries no samples"}
    built = seed_for_case(case, weights)
    if built is None:
        return None, {"reason": "the composition could not be registered on this box's ink"}
    seed_xy, seed_slot, _ = built
    if not (seed_slot >= 0).any():
        return None, {"reason": "the composed seed carries no letter at all"}
    drawn = [crop_points(stroke, registration, xh_px) for stroke in strokes]
    # Matched once and used twice. The alignment is the expensive half, and a
    # second call for the distance reading would quietly double the cost of
    # every box while answering a question the first call already knows.
    matched = [match_seed(stroke, seed_xy, method=method) for stroke in drawn]
    runs = runs_of([seed_slot[picked] for picked in matched])
    spans = flat_spans(runs, strokes)
    if spans is None:
        boundaries = sum(len(stroke_runs) for stroke_runs in runs)
        return None, {
            "reason": (
                f"{boundaries} boundaries — at most {MAX_SPANS} are stored per box"
                if boundaries > MAX_SPANS
                else "the assignment does not cover these strokes sample for sample"
            )
        }
    distances = np.concatenate(
        [
            seed_distance_xh(stroke, seed_xy, picked, xh_px)
            for stroke, picked in zip(drawn, matched, strict=True)
            if len(stroke)
        ]
    )
    return spans, {
        "method": method,
        "spans": len(spans),
        "seed_distance_median_xh": round(float(np.median(distances)), 3),
        "seed_distance_p90_xh": round(float(np.percentile(distances, 90)), 3),
    }


# ------------------------------------------------- the round's own instrument


def _labels_from_nested(
    nested: Sequence[Sequence[Sequence[int]]], strokes: Sequence[Sequence[Any]]
) -> list[np.ndarray]:
    """A per-sample label array back out of the nested span shape."""
    out = []
    for spans, stroke in zip(nested, strokes, strict=True):
        label = np.full(len(stroke), -1, dtype=int)
        for slot, first, last in spans:
            label[first : last + 1] = slot
        out.append(label)
    return out


def _seam_displacement_xh(
    mine: Sequence[np.ndarray], theirs: Sequence[np.ndarray], drawn: Sequence[np.ndarray], xh_px: float
) -> list[float]:
    """Per boundary of `theirs`: the arc distance to the nearest boundary of `mine`.

    Measured in ARC rather than in samples, because a sample is a different
    length on every Bahn and the question is how far a handle would have to be
    dragged.
    """
    out: list[float] = []
    for ours, reference, points in zip(mine, theirs, drawn, strict=True):
        if len(points) < 2:
            continue
        step = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(points, axis=0).T))]) / float(xh_px)
        ours_at = np.flatnonzero(np.diff(ours) != 0)
        for boundary in np.flatnonzero(np.diff(reference) != 0):
            if not len(ours_at):
                out.append(float(step[-1]))
                continue
            out.append(float(np.min(np.abs(step[ours_at] - step[boundary]))))
    return out


def wobbled(strokes_px: Sequence[np.ndarray], xh_px: float, amplitude_xh: float, key: str) -> list[np.ndarray]:
    """The same Bahn, pushed off the seed by a slow drift — the round's hand simulator.

    A Bahn the FOLLOWER delivered was produced by decoding against the very
    seed the assigner then matches it back to, so recovering the decode's own
    labels on it is an upper bound and says little about a Bahn the seed never
    produced. A hand does not wander sample by sample; it drifts over a letter
    and comes back. So the offset is a handful of control values interpolated
    along the stroke's arc, not noise — and it is deterministic in the word's
    id, so the round re-runs to the same numbers.

    It is a SIMULATION and is reported as one. The material that would settle
    the question is the author's own drawn Bahnen, and on the day of this round
    there is not one of them.
    """
    out: list[np.ndarray] = []
    for index, stroke in enumerate(strokes_px):
        points = np.asarray(stroke, dtype=float)
        if len(points) < 2:
            out.append(points.copy())
            continue
        digest = hashlib.sha256(f"{key}#{index}".encode()).digest()
        rng = np.random.default_rng(int.from_bytes(digest[:8], "big"))
        control = rng.normal(size=(5, 2))
        arc = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(points, axis=0).T))])
        at = arc / (arc[-1] or 1.0)
        knots = np.linspace(0.0, 1.0, len(control))
        offset = np.column_stack([np.interp(at, knots, control[:, 0]), np.interp(at, knots, control[:, 1])])
        # Scaled on the MEDIAN displacement, not the peak: the amplitude is then
        # what the typical sample is actually pushed by, which is the number the
        # arm is described with. Normalising on the peak made the same 0.15
        # read as a median drift of 0.04 and would have quoted a stronger
        # simulation than the one that ran.
        scale = float(np.median(np.hypot(offset[:, 0], offset[:, 1]))) or 1.0
        out.append(points + offset * (amplitude_xh * float(xh_px) / scale))
    return out


def _reading(values: Sequence[float]) -> dict[str, float | int]:
    array = np.asarray(values, dtype=float)
    if not len(array):
        return {"n": 0}
    return {
        "n": int(len(array)),
        "median": round(float(np.median(array)), 4),
        "p90": round(float(np.percentile(array, 90)), 4),
        "max": round(float(array.max()), 4),
    }


def check(
    fixtures_root: Path,
    *,
    style: str,
    which: str,
    only: list[str] | None,
    methods: Sequence[str],
    wobble_xh: float = 0.0,
) -> dict[str, Any]:
    """The §14 round: follow the frozen words, then assign „as if drawn by hand".

    The plan asks for green AUTO strip Bahnen with known boundaries. Those live
    only in the shared database and the gitignored strip store, and a
    measurement is not allowed to reach into either — so the standing local
    material stands in, and it carries the same object: a Bahn the Tintenpfad
    delivered, with the slot the decode gave every one of its samples. The
    substitution is named in the §14 entry rather than hidden here.

    What is compared is the ASSIGNMENT and nothing else. The Bahn, the seed,
    the eight settled switches and the root are one stack; the matching rule is
    the one knob — and, with `wobble_xh`, the same knob over a Bahn pushed off
    the seed (`wobbled`), because the clean reading is an upper bound by
    construction.
    """
    from tools.eigenhand.pfad import KONFIGURATION
    from tools.pairlab.tintenpfad import TintenpfadWeights, follow_case
    from tools.wordbench.roots import root_digest
    from tools.wordlab.cases import fixture_root_for, iter_fixture_word_cases

    root = fixture_root_for(which=which, style=style, fixtures_root=fixtures_root)
    digest = root_digest(root)
    manifest = json.loads((root / "manifest.json").read_text())
    print(f"root: {root}\n  exported_at={manifest.get('exported_at')} digest={digest[:12]}", flush=True)
    weights = TintenpfadWeights(**KONFIGURATION)
    cases = iter_fixture_word_cases(which=which, style=style, only=only, fixtures_root=fixtures_root)

    # „clean" is the Bahn as the follower delivered it; „wobble" is the same
    # Bahn pushed off the seed. The two are separate arms rather than two runs,
    # so one follow of the frozen words answers both — the follow is 2–3 s per
    # word and it is the same Bahn either way.
    variants = ["clean"] + (["wobble"] if wobble_xh > 0.0 else [])
    per_arm: dict[str, dict[str, list]] = {
        f"{method}/{variant}": {"agreement": [], "samples": [], "hits": [], "seams": [], "seed": []}
        for method in methods
        for variant in variants
    }
    followed = skipped = 0
    for case in cases:
        info = follow_case(case, weights)
        nested = info.get("meta", {}).get("letter_spans")
        if info.get("status") != "ok" or not nested or len(nested) != len(info["strokes"]):
            skipped += 1
            print(f"  {case.id:<14} no reference assignment ({info.get('status')})", flush=True)
            continue
        registration, xh_px = info["registration_px"], float(info["xh_px"])
        drawn = [crop_points(stroke, registration, xh_px) for stroke in info["strokes"]]
        if flat_spans(nested, info["strokes"]) is None:
            skipped += 1
            print(f"  {case.id:<14} the follower's own spans no longer cover its capped strokes", flush=True)
            continue
        reference = _labels_from_nested(nested, info["strokes"])
        built = seed_for_case(case, weights)
        if built is None:
            skipped += 1
            print(f"  {case.id:<14} the composition could not be registered", flush=True)
            continue
        seed_xy, seed_slot, _ = built
        followed += 1
        line = [f"  {case.id:<14}"]
        bahnen = {"clean": drawn, "wobble": wobbled(drawn, xh_px, wobble_xh, case.id)}
        total = int(sum(len(theirs) for theirs in reference))
        for variant in variants:
            bahn = bahnen[variant]
            for method in methods:
                matched = [match_seed(stroke, seed_xy, method=method) for stroke in bahn]
                filled = _labels_from_nested(runs_of([seed_slot[picked] for picked in matched]), info["strokes"])
                hits = int(sum(int((mine == theirs).sum()) for mine, theirs in zip(filled, reference, strict=True)))
                bucket = per_arm[f"{method}/{variant}"]
                bucket["hits"].append(hits)
                bucket["samples"].append(total)
                bucket["agreement"].append(hits / total if total else 0.0)
                bucket["seams"].extend(_seam_displacement_xh(filled, reference, bahn, xh_px))
                bucket["seed"].extend(
                    float(value)
                    for stroke, picked in zip(bahn, matched, strict=True)
                    if len(stroke)
                    for value in seed_distance_xh(stroke, seed_xy, picked, xh_px)
                )
                line.append(f"{method}/{variant} {hits / total if total else 0.0:.3f}")
        print(" · ".join(line), flush=True)

    result: dict[str, Any] = {
        "root": str(root),
        "root_digest": digest,
        "exported_at": manifest.get("exported_at"),
        "words_measured": followed,
        "words_skipped": skipped,
        "konfiguration": dict(KONFIGURATION),
        "wobble_xh": wobble_xh,
        "arms": {},
    }
    for arm, bucket in per_arm.items():
        pooled = sum(bucket["hits"]) / sum(bucket["samples"]) if sum(bucket["samples"]) else 0.0
        result["arms"][arm] = {
            "pooled_agreement": round(pooled, 4),
            "word_agreement": _reading(bucket["agreement"]),
            "words_perfect": int(sum(1 for value in bucket["agreement"] if value >= 1.0)),
            "seam_displacement_xh": _reading(bucket["seams"]),
            "seed_distance_xh": _reading(bucket["seed"]),
        }
    return result


def main(argv: list[str] | None = None) -> int:
    from tools.wordlab.cases import DEFAULT_FIXTURES_DIR

    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--check", action="store_true", help="run the §14 round: the frozen words, assigned as if drawn")
    ap.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES_DIR, help="the frozen fixture root to read")
    ap.add_argument("--style", default="suetterlin")
    ap.add_argument("--set", dest="which", default="words")
    ap.add_argument("--word", action="append", default=None, help="only this fixture id or word (repeatable)")
    ap.add_argument("--method", action="append", default=None, choices=list(METHODS), help="repeatable; default: both")
    ap.add_argument(
        "--wobble",
        type=float,
        default=DEFAULT_WOBBLE_XH,
        help="amplitude of the drift that pushes the Bahn off the seed, in x-heights (0 = the clean arm only)",
    )
    ap.add_argument("--json", type=Path, default=None, help="where the round's numbers are filed")
    args = ap.parse_args(argv)

    if not args.check:
        ap.error("this module measures; pass --check (the assigner itself runs from `tools.eigenhand.pfad --spans`)")
    result = check(
        args.fixtures,
        style=args.style,
        which=args.which,
        only=args.word,
        methods=args.method or list(METHODS),
        wobble_xh=args.wobble,
    )
    print(json.dumps(result["arms"], indent=1, ensure_ascii=False), flush=True)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
        print(f"filed to {args.json}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
