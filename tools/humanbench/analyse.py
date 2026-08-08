"""analyse — the pre-registered evaluation of a humanbench SINGLE pass.

    uv run python -m tools.humanbench.analyse \\
        --result round2/result.txt --key round2/key.json \\
        --rows round2/rows.json --spots round2/spots.json

``page.py`` collects the judgement and ``build.py`` decides what gets judged;
this is the third piece — it turns the emitted result text back into numbers,
in the order the analysis plan fixed BEFORE the labels existed. That order is
the whole point: an evaluation written after seeing the labels can always be
reordered until it says something, and then nobody can tell the finding from
the search for one. Here the order is code, so a later round re-runs the same
analysis rather than a new one.

Six steps, in the plan's binding order:

1. **Reliability first** — the blind repeats give the test-retest agreement,
   whole verdict and per category. Every later per-category number is reported
   underneath its own ceiling: if the judge disagrees with themselves about a
   category, a PERFECT detector for it cannot score better than that agreement,
   and „our metrics are blind to X" would be unfalsifiable.
2. **Occupancy** — how often each category was actually set. Below
   ``MIN_POSITIVES`` a category gets the words „too few" instead of a number,
   so a class with five members never turns into a finding later on.
3. **Gate validation** — precision and recall of a shipped metric threshold
   against one category AND against „any finding". The cheapest
   decision-relevant output there is: does the gate throw away occurrences a
   human would have kept?
4. **Coverage matrix** — one AUC per category × metric with its
   Hanley-McNeil standard error, so „sees it at all" can be told from „does
   not". Not a threshold search: at ~15 positives the SE is ≈ 0.09, and two
   AUCs within it are the same number. Two categories the pass shows to be
   inseparable are scored as their UNION (`--union`): confusability then costs
   resolution instead of destroying the statement.
5. **Place check** — over the voluntarily clicked markers only, the one part
   of the pass that is independent of the metrics: does the human's point sit
   where the metric's own maximum sits, and does it sit at a stroke boundary?
6. **Drift** — category mix, marker rate and judging time over the sequence,
   reported rather than assumed away.

Three standing rules are wired in rather than left to the caller:

* **An unset marker is never negative evidence.** Not marked means „not
  marked", not „nothing wrong there" — unmarked items are dropped from the
  place check and the marker rate is reported beside it, because a rate that
  falls over the sequence is fatigue and says nothing about the images.
* **An item with more than one finding drops out of the CATEGORY place check.**
  One point and two findings cannot be attributed to either; such items still
  count in the overall „boundary yes/no" question.
* **„Komplett daneben" (K) is excluded from every other category's
  evaluation** — there is nothing to judge there, so it neither counts as a
  positive nor pads the negatives.

No database, no API, no network. The per-occurrence metrics arrive as a file
the caller supplies, which is also what keeps the learned geometry out of this
repo (``docs/reference/quellen-und-rechte.md`` §5): the module reads numbers,
it never derives them.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from tools.humanbench.page import CATEGORIES, CHOICES


# The verdict vocabulary comes from the instrument itself, so the parser cannot
# drift away from the page that produced the file.
CATEGORY_CODES: tuple[str, ...] = tuple(c.code for c in CATEGORIES)
FINDING_CODES: tuple[str, ...] = tuple(c.code for c in CATEGORIES if c.kind == "finding")
CHOICE_CODES: tuple[str, ...] = tuple(c.code for c in CHOICES)
CATEGORY_LABEL: dict[str, str] = {c.code: c.tally for c in CATEGORIES}

GOOD = "G"  # the verdict that says nothing is wrong
UNRATABLE = "K"  # „komplett daneben" — excluded from every other category
UNSURE = "U"  # a modifier on a verdict, never a verdict of its own

# A category needs this many positives before it gets a number instead of the
# words „too few" (analysis plan step 3).
MIN_POSITIVES = 8

# Test-retest bands for the whole verdict and for a single category, as
# fractions of the repeat pairs: at or above `RELIABLE` the label carries an
# AUC, at or below `COIN_FLIP` it carries nothing.
RELIABLE_AGREEMENT = 10 / 12
COIN_FLIP_AGREEMENT = 7 / 12

# Below this many repeat pairs that carried the category AT ALL, its agreement
# is agreement about the negatives and says nothing about the category. The
# number is the stratification target the next round was specified with: three
# positive pairs per category.
MIN_REPEAT_POSITIVES = 3

# Place check: how close to a stroke boundary still counts as „at the boundary",
# and how close to the metric's own maximum still counts as the same spot.
EDGE_ANCHORS = 3
ARGMAX_TOLERANCE = 4

# Where along the anchor chain the head and the tail of a stroke begin.
HEAD_FRACTION = 0.10
TAIL_FRACTION = 0.90

DRIFT_BLOCKS = 3

# The per-occurrence metrics of the round that produced this module. A rows
# file without one of them simply drops that line from the matrix; a rows file
# with more of them is served by `--metrics`.
DEFAULT_METRICS: tuple[str, ...] = ("peak", "med", "p90", "off10", "off20", "geo", "cov", "spike")

# The shipped harvest gate, as `metric>=threshold:category`
# (`tools/laufform/harvest.py::MAX_ANCHOR_SPIKE_RATIO`, which rejects strictly
# ABOVE the threshold; `>=` and `>` pick the same occurrences unless one sits
# exactly on it, and `--gate` spells out whichever the round needs).
DEFAULT_GATE = "spike>=8.0:A"

RESULT_HEAD = re.compile(r"^(?P<tag>\S+)\s+geprueft=(?P<judged>\d+)\s+von\s+(?P<total>\d+)\s*$")
RESULT_LINE = re.compile(
    r"^(?P<uid>[A-Za-z][A-Za-z0-9_-]*):(?P<verdict>-|[A-Z]*)"
    r"(?:#(?P<sx>-?\d+),(?P<sy>-?\d+))?"
    r"(?:@(?P<seconds>\d+)s)?"
    r'(?: "(?P<note>.*)")?$'
)
GATE_SPEC = re.compile(
    r"^(?P<metric>[A-Za-z_][A-Za-z0-9_]*)(?P<op>>=|<=)(?P<value>[-+0-9.eE]+)(?::(?P<category>[A-Z]))?$"
)


class ResultFormatError(ValueError):
    """The result text does not parse as a humanbench pass."""


# ------------------------------------------------------------------- parsing


@dataclass(frozen=True)
class Verdict:
    """One judged screen, exactly as the page emitted it."""

    uid: str
    codes: tuple[str, ...]
    spot: tuple[int, int] | None
    seconds: int | None
    note: str | None
    position: int  # index in the judged sequence, for the drift step

    @property
    def findings(self) -> tuple[str, ...]:
        return tuple(c for c in self.codes if c in FINDING_CODES)

    @property
    def unratable(self) -> bool:
        return UNRATABLE in self.codes

    @property
    def unsure(self) -> bool:
        return UNSURE in self.codes

    @property
    def flagged(self) -> bool:
        """Anything but „gut" — findings and „komplett daneben" alike."""
        return bool(self.findings) or self.unratable


@dataclass(frozen=True)
class ParsedResult:
    tag: str
    judged: int
    total: int
    verdicts: tuple[Verdict, ...]


def parse_result(text: str) -> ParsedResult:
    """Parse the text the page's „fertig" screen emits.

    Format, one line per judged screen (``page.py::finish``)::

        <uid>:<codes>[#<x>,<y>][@<secs>s][ "note"]

    preceded by a header ``<TAG> geprueft=<judged> von <total>``. The codes are
    the category letters in the page's own order; a paired pass writes a single
    choice letter instead and is rejected here — it answers a different
    question and has no categories to evaluate.
    """
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ResultFormatError("empty result")
    head = RESULT_HEAD.match(lines[0])
    if not head:
        raise ResultFormatError(f"no header line, got {lines[0]!r}")

    verdicts: list[Verdict] = []
    seen: set[str] = set()
    for position, line in enumerate(lines[1:]):
        match = RESULT_LINE.match(line)
        if not match:
            raise ResultFormatError(f"line {position + 2} does not parse: {line!r}")
        raw = match.group("verdict")
        codes = tuple(dict.fromkeys(raw)) if raw != "-" else ()
        unknown = [c for c in codes if c not in CATEGORY_CODES]
        if unknown and all(c in CHOICE_CODES for c in unknown):
            raise ResultFormatError(
                f"line {position + 2} carries the paired-mode verdict {raw!r}; analyse.py evaluates single passes"
            )
        if unknown:
            raise ResultFormatError(f"line {position + 2}: unknown category code(s) {''.join(unknown)}")
        uid = match.group("uid")
        if uid in seen:
            raise ResultFormatError(f"line {position + 2}: {uid} judged twice")
        seen.add(uid)
        spot = (int(match.group("sx")), int(match.group("sy"))) if match.group("sx") is not None else None
        seconds = int(match.group("seconds")) if match.group("seconds") else None
        verdicts.append(Verdict(uid, codes, spot, seconds, match.group("note"), position))

    if len(verdicts) != int(head.group("judged")):
        raise ResultFormatError(f"header claims {head.group('judged')} judged, file carries {len(verdicts)}")
    return ParsedResult(head.group("tag"), int(head.group("judged")), int(head.group("total")), tuple(verdicts))


def load_key(entries: Iterable[dict]) -> dict[str, dict]:
    """Index the round's key by display id."""
    return {e["uid"]: e for e in entries}


def index_by_uid(entries: Iterable[dict]) -> dict[str, dict]:
    return {e["uid"]: e for e in entries if e.get("uid")}


# ------------------------------------------------------------------- statistics


def roc_auc(positive: Sequence[float], negative: Sequence[float]) -> float | None:
    """Mann-Whitney AUC with mid-ranks for ties; None when either side is empty."""
    n_pos, n_neg = len(positive), len(negative)
    if not n_pos or not n_neg:
        return None
    merged = sorted([*positive, *negative])
    rank: dict[float, float] = {}
    i = 0
    while i < len(merged):
        j = i
        while j + 1 < len(merged) and merged[j + 1] == merged[i]:
            j += 1
        rank[merged[i]] = (i + j) / 2.0 + 1.0
        i = j + 1
    rank_sum = sum(rank[v] for v in positive)
    return (rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def hanley_mcneil_se(auc: float, n_pos: int, n_neg: int) -> float | None:
    """Standard error of an AUC (Hanley & McNeil 1982, the exponential form)."""
    if n_pos < 1 or n_neg < 1:
        return None
    q1 = auc / (2.0 - auc)
    q2 = 2.0 * auc * auc / (1.0 + auc)
    var = (auc * (1.0 - auc) + (n_pos - 1) * (q1 - auc * auc) + (n_neg - 1) * (q2 - auc * auc)) / (n_pos * n_neg)
    return math.sqrt(max(var, 0.0))


# ------------------------------------------------------------------- the steps


def _shown(verdicts: Sequence[Verdict], key: dict[str, dict]) -> list[Verdict]:
    """The pass proper: every screen that is not a blind repeat of another."""
    return [v for v in verdicts if not (key.get(v.uid) or {}).get("repeat_of")]


def _evaluated(verdicts: Sequence[Verdict]) -> list[Verdict]:
    """Everything a category can be judged on — „komplett daneben" removed."""
    return [v for v in verdicts if not v.unratable]


def reliability(verdicts: Sequence[Verdict], key: dict[str, dict]) -> dict[str, Any]:
    """Step 1 — test-retest agreement from the blind repeats.

    Per category a pair is one of three things: both readings set it (``yes``),
    neither did (``no``), or they disagree. The agreement rate alone hides
    which: at 10 % prevalence a category nobody ever set scores a perfect
    12/12. `carried` counts the pairs that set it at least once, and below
    `MIN_REPEAT_POSITIVES` the warning says so instead of the number claiming
    reliability it cannot have.
    """
    by_uid = {v.uid: v for v in verdicts}
    pairs: list[tuple[Verdict, Verdict]] = []
    missing: list[str] = []
    for entry in key.values():
        first, repeat = entry.get("repeat_of"), entry["uid"]
        if not first:
            continue
        if first in by_uid and repeat in by_uid:
            pairs.append((by_uid[first], by_uid[repeat]))
        else:
            missing.append(repeat)

    exact = sum(1 for a, b in pairs if set(a.codes) == set(b.codes))
    per_category: dict[str, dict[str, Any]] = {}
    for code in CATEGORY_CODES:
        both = sum(1 for a, b in pairs if code in a.codes and code in b.codes)
        neither = sum(1 for a, b in pairs if code not in a.codes and code not in b.codes)
        disagree = len(pairs) - both - neither
        carried = both + disagree
        agree = both + neither
        per_category[code] = {
            "agree": agree,
            "pairs": len(pairs),
            "rate": (agree / len(pairs)) if pairs else None,
            "yes": both,
            "no": neither,
            "disagree": disagree,
            "carried": carried,
            "band": _reliability_band(agree, len(pairs)),
            "too_few_positives": carried < MIN_REPEAT_POSITIVES,
        }
    return {
        "pairs": len(pairs),
        "missing_repeats": missing,
        "exact": exact,
        "exact_rate": (exact / len(pairs)) if pairs else None,
        "per_category": per_category,
    }


def _reliability_band(agree: int, pairs: int) -> str | None:
    if not pairs:
        return None
    rate = agree / pairs
    if rate >= RELIABLE_AGREEMENT:
        return "reliable"
    if rate <= COIN_FLIP_AGREEMENT:
        return "coin flip"
    return "middling"


def occupancy(verdicts: Sequence[Verdict], key: dict[str, dict]) -> dict[str, Any]:
    """Step 2 — how often each category was set, over the pass proper.

    `flagged` counts every screen that is not „gut" (findings AND „komplett
    daneben"), because that is the population the marker rate belongs to.
    """
    shown = _shown(verdicts, key)
    total = len(shown)
    per_category = {}
    for code in CATEGORY_CODES:
        n = sum(1 for v in shown if code in v.codes)
        per_category[code] = {"n": n, "share": (n / total) if total else None, "too_few": n < MIN_POSITIVES}
    flagged = [v for v in shown if v.flagged]
    marked = [v for v in flagged if v.spot]
    sizes = Counter(len(set(v.codes) - {UNSURE}) for v in shown)
    overlap = {}
    for i, left in enumerate(FINDING_CODES):
        for right in FINDING_CODES[i + 1 :]:
            both = sum(1 for v in shown if left in v.codes and right in v.codes)
            union = sum(1 for v in shown if left in v.codes or right in v.codes)
            overlap[f"{left}&{right}"] = {"both": both, "union": union, "share": (both / union) if union else None}
    return {
        "total": total,
        "per_category": per_category,
        "flagged": len(flagged),
        "good_with_finding": sum(1 for v in shown if GOOD in v.codes and v.findings),
        "unsure": sum(1 for v in shown if v.unsure),
        "verdict_sizes": dict(sorted(sizes.items())),
        "marker_on_flagged": len(marked),
        "marker_rate": (len(marked) / len(flagged)) if flagged else None,
        "overlap": overlap,
    }


def parse_gate(spec: str) -> tuple[str, str, float, str | None]:
    """``metric>=value[:category]`` -> (metric, op, value, category)."""
    match = GATE_SPEC.match(spec)
    if not match:
        raise ValueError(f"gate spec {spec!r} is not <metric>>=<value>[:<category>]")
    return match.group("metric"), match.group("op"), float(match.group("value")), match.group("category")


def gate_validation(
    verdicts: Sequence[Verdict], key: dict[str, dict], rows: dict[str, dict], spec: str
) -> dict[str, Any]:
    """Step 3 — precision and recall of a shipped threshold against the labels.

    Reported twice: against the category the gate was built for, and against
    „any finding". The second is the one that answers whether the gate throws
    away occurrences a human would have kept — a rejection that carries some
    OTHER finding is not a false alarm in that sense, and calling it one would
    understate the gate.
    """
    metric, op, threshold, category = parse_gate(spec)
    pool = [v for v in _evaluated(_shown(verdicts, key)) if _value(rows, v.uid, metric) is not None]
    rejected = [v for v in pool if _rejects(_value(rows, v.uid, metric), op, threshold)]

    targets: dict[str, dict[str, Any]] = {}
    for name, hit in (
        (category or "-", lambda v: bool(category) and category in v.codes),
        ("any finding", lambda v: bool(v.findings)),
    ):
        if name == "-":
            continue
        positives = [v for v in pool if hit(v)]
        caught = [v for v in rejected if hit(v)]
        missed = sorted((_value(rows, v.uid, metric) for v in positives if v not in caught), reverse=True)
        targets[name] = {
            "positives": len(positives),
            "caught": len(caught),
            "precision": (len(caught) / len(rejected)) if rejected else None,
            "recall": (len(caught) / len(positives)) if positives else None,
            "missed_values": missed,
        }
    return {
        "metric": metric,
        "op": op,
        "threshold": threshold,
        "category": category,
        "evaluated": len(pool),
        "rejected": len(rejected),
        "rejected_verdicts": sorted(Counter("".join(v.findings) or "-" for v in rejected).items()),
        "targets": targets,
    }


def _rejects(value: float, op: str, threshold: float) -> bool:
    return value >= threshold if op == ">=" else value <= threshold


def _value(rows: dict[str, dict], uid: str, metric: str) -> float | None:
    raw = (rows.get(uid) or {}).get(metric)
    return float(raw) if isinstance(raw, (int, float)) and not isinstance(raw, bool) else None


def union_name(codes: Sequence[str]) -> str:
    """The column name of a union of categories, e.g. ``W∪B``."""
    return "∪".join(codes)


def parse_union(spec: str) -> tuple[str, ...]:
    """``"W,B"`` -> ``("W", "B")``, validated against the finding categories."""
    codes = tuple(part.strip().upper() for part in spec.split(",") if part.strip())
    if len(codes) < 2:
        raise ValueError(f"union {spec!r} needs at least two categories")
    unknown = [c for c in codes if c not in FINDING_CODES]
    if unknown:
        raise ValueError(f"union {spec!r}: {''.join(unknown)} is not a finding category ({''.join(FINDING_CODES)})")
    if len(set(codes)) != len(codes):
        raise ValueError(f"union {spec!r} names a category twice")
    return codes


def coverage_matrix(
    verdicts: Sequence[Verdict],
    key: dict[str, dict],
    rows: dict[str, dict],
    metrics: Sequence[str],
    flags: Sequence[str] | None = None,
    unions: Sequence[Sequence[str]] = (),
) -> dict[str, Any]:
    """Step 4 — one AUC per category × metric, „komplett daneben" excluded.

    Columns are the finding categories that clear `MIN_POSITIVES`, then any
    requested UNION of categories, then „any finding"; a thinner column is named
    as too few rather than given a number nobody could read.

    The unions are the plan's step 6, the pre-registered fallback: if the blind
    repeats or the co-occurrence counts of step 2 show that two categories are
    not being told apart, they are evaluated TOGETHER. A category the judge
    cannot separate reliably caps every AUC built on it — but the union of the
    two is a label they do agree with themselves on, so confusability costs
    resolution instead of destroying the statement. It is a fallback and not a
    default: asked for by the caller, after the numbers that justify it.

    A BOOLEAN row field (`at_edge` and its like) is a degenerate metric — an
    AUC over two values says less than the two rates do — so those are reported
    as „share of the category that carries the flag, against the share of
    everything else", which is the form the pre-registered expectations were
    written in.
    """
    pool = _evaluated(_shown(verdicts, key))
    columns: list[str] = []
    too_few: list[str] = []
    tests: list[tuple[str, Any]] = []
    for code in FINDING_CODES:
        n = sum(1 for v in pool if code in v.codes)
        if n >= MIN_POSITIVES:
            columns.append(code)
            tests.append((code, (lambda c: lambda v: c in v.codes)(code)))
        else:
            too_few.append(code)
    for group in unions:
        codes = tuple(group)
        name = union_name(codes)
        n = sum(1 for v in pool if any(c in v.codes for c in codes))
        if n >= MIN_POSITIVES:
            columns.append(name)
            tests.append((name, (lambda cs: lambda v: any(c in v.codes for c in cs))(codes)))
        else:
            too_few.append(name)
    tests.append(("any", lambda v: bool(v.findings)))

    cells: dict[str, dict[str, Any]] = {}
    skipped: list[str] = []
    for metric in metrics:
        available = [v for v in pool if _value(rows, v.uid, metric) is not None]
        if not available:
            skipped.append(metric)
            continue
        row: dict[str, Any] = {}
        for name, hit in tests:
            positive = [_value(rows, v.uid, metric) for v in available if hit(v)]
            negative = [_value(rows, v.uid, metric) for v in available if not hit(v)]
            auc = roc_auc(positive, negative)
            row[name] = {
                "auc": auc,
                "se": hanley_mcneil_se(auc, len(positive), len(negative)) if auc is not None else None,
                "n_pos": len(positive),
                "n_neg": len(negative),
            }
        row["_n"] = len(available)
        cells[metric] = row

    flag_cells: dict[str, dict[str, Any]] = {}
    for flag in flags if flags is not None else _boolean_fields(rows):
        available = [v for v in pool if isinstance((rows.get(v.uid) or {}).get(flag), bool)]
        if not available:
            continue
        row = {}
        for name, hit in tests:
            positive = [v for v in available if hit(v)]
            negative = [v for v in available if not hit(v)]
            row[name] = {
                "set": sum(1 for v in positive if rows[v.uid][flag]),
                "n_pos": len(positive),
                "set_elsewhere": sum(1 for v in negative if rows[v.uid][flag]),
                "n_neg": len(negative),
            }
        flag_cells[flag] = row
    return {
        "evaluated": len(pool),
        "columns": [*columns, "any"],
        "too_few": too_few,
        "metrics": cells,
        "flags": flag_cells,
        "missing_metrics": skipped,
    }


def _boolean_fields(rows: dict[str, dict]) -> list[str]:
    """Row fields that are booleans everywhere they appear, in first-seen order."""
    seen: dict[str, bool] = {}
    for record in rows.values():
        for name, value in record.items():
            seen[name] = seen.get(name, True) and isinstance(value, bool)
    return [name for name, ok in seen.items() if ok]


def place_check(verdicts: Sequence[Verdict], key: dict[str, dict], geometry: dict[str, dict]) -> dict[str, Any]:
    """Step 5 — where the human clicked, over the set markers only.

    Two rules from the plan are enforced here rather than trusted to the
    reader: an unset marker is dropped instead of counted as „nothing wrong
    there", and a screen carrying more than one finding is dropped from the
    per-category table because its one point cannot be attributed.
    """
    shown = _shown(verdicts, key)
    marked = [v for v in shown if v.spot]
    usable = [v for v in marked if _has_place(geometry.get(v.uid))]
    without = [v.uid for v in marked if v not in usable]

    hits = sum(1 for v in usable if abs(geometry[v.uid]["idx"] - geometry[v.uid]["argmax_idx"]) <= ARGMAX_TOLERANCE)
    boundary = sum(1 for v in usable if geometry[v.uid]["edge_dist"] <= EDGE_ANCHORS)

    single = [v for v in usable if len(v.findings) == 1 and not v.unratable]
    per_category: dict[str, dict[str, Any]] = {}
    for code in FINDING_CODES:
        group = [v for v in single if code in v.codes]
        head = sum(1 for v in group if geometry[v.uid]["rel"] < HEAD_FRACTION)
        tail = sum(1 for v in group if geometry[v.uid]["rel"] > TAIL_FRACTION)
        per_category[code] = {
            "n": len(group),
            "head": head,
            "middle": len(group) - head - tail,
            "tail": tail,
            "at_boundary": sum(1 for v in group if geometry[v.uid]["edge_dist"] <= EDGE_ANCHORS),
            "too_few": len(group) < MIN_POSITIVES,
        }
    return {
        "shown": len(shown),
        "marked": len(marked),
        "marker_rate": (len(marked) / len(shown)) if shown else None,
        "usable": len(usable),
        "without_geometry": without,
        "argmax_hits": hits,
        "argmax_rate": (hits / len(usable)) if usable else None,
        "at_boundary": boundary,
        "boundary_rate": (boundary / len(usable)) if usable else None,
        "single_finding": len(single),
        "per_category": per_category,
    }


def _has_place(record: dict | None) -> bool:
    return bool(record) and all(
        k in record and record[k] is not None for k in ("idx", "rel", "edge_dist", "argmax_idx")
    )


def drift(verdicts: Sequence[Verdict], key: dict[str, dict], blocks: int = DRIFT_BLOCKS) -> dict[str, Any]:
    """Step 6 — category mix, marker rate and judging time over the sequence."""
    shown = _shown(verdicts, key)
    n = len(shown)
    bounds = [round(i * n / blocks) for i in range(blocks + 1)]
    out = []
    for lo, hi in zip(bounds[:-1], bounds[1:], strict=True):
        block = shown[lo:hi]
        times = [v.seconds for v in block if v.seconds is not None]
        out.append(
            {
                "range": [lo, hi],
                "n": len(block),
                "categories": {code: sum(1 for v in block if code in v.codes) for code in CATEGORY_CODES},
                "marked": sum(1 for v in block if v.spot),
                "timed": len(times),
                "median_seconds": statistics.median(times) if times else None,
            }
        )
    return {"blocks": out}


def notes(verdicts: Sequence[Verdict], key: dict[str, dict]) -> list[dict[str, Any]]:
    """The free-text remarks, verbatim, with their screen's glyph and verdict."""
    return [
        {
            "uid": v.uid,
            "glyph": (key.get(v.uid) or {}).get("glyph"),
            "word": (key.get(v.uid) or {}).get("word"),
            "codes": "".join(v.codes),
            "note": v.note,
        }
        for v in verdicts
        if v.note
    ]


def analyse(
    parsed: ParsedResult,
    key: dict[str, dict],
    rows: dict[str, dict],
    geometry: dict[str, dict],
    *,
    metrics: Sequence[str] = DEFAULT_METRICS,
    flags: Sequence[str] | None = None,
    unions: Sequence[Sequence[str]] = (),
    gate: str = DEFAULT_GATE,
    drop_unsure: bool = False,
) -> dict[str, Any]:
    """Run the six steps in the plan's order and return every number."""
    verdicts = list(parsed.verdicts)
    unknown = sorted({v.uid for v in verdicts} - set(key))
    if unknown:
        raise ResultFormatError(f"result carries {len(unknown)} screen(s) the key does not know: {unknown[:5]}")
    # „Not judged" is a property of the RESULT text, so it is read off the
    # parsed verdicts — before `--drop-unsure` removes any. A screen the judge
    # answered with a shrug was judged; reporting it as unjudged as well would
    # count the same screen under two different complaints.
    unjudged = [uid for uid in key if uid not in {v.uid for v in verdicts}]
    dropped: list[str] = []
    if drop_unsure:
        dropped = [v.uid for v in verdicts if v.unsure]
        verdicts = [v for v in verdicts if not v.unsure]
    return {
        "pass": {
            "tag": parsed.tag,
            "judged": parsed.judged,
            "total": parsed.total,
            "key_entries": len(key),
            "unjudged": unjudged,
            "dropped_unsure": dropped,
            "metric_rows": len(rows),
            "place_records": len(geometry),
        },
        "reliability": reliability(verdicts, key),
        "occupancy": occupancy(verdicts, key),
        # Steps 3 and 4 need the per-occurrence metrics, which are learned data
        # and therefore live outside the repository. The judgements and the slim
        # key ARE committed, so the tool runs on them alone and says which steps
        # it had to leave out — degrading to what the data supports beats
        # demanding a file the archive deliberately does not carry.
        "gate": gate_validation(verdicts, key, rows, gate) if rows else None,
        "coverage": coverage_matrix(verdicts, key, rows, metrics, flags, unions) if rows else None,
        # Step 5 is NOT gated the same way, because its primary datum is not
        # external: the marker sits in the result line itself (`#x,y`), which is
        # committed. Only the anchor-index geometry comes from `--spots`, and
        # `place_check` already degrades to „0 with place geometry" plus the
        # `without_geometry` list. Gating the whole step would drop the marker
        # RATE — the one number the plan requires reported beside the check,
        # because a rate that falls over the sequence is fatigue.
        "place": place_check(verdicts, key, geometry),
        "drift": drift(verdicts, key),
        "notes": notes(verdicts, key),
    }


# ------------------------------------------------------------------- report


# How many of a gate's missed positives the report prints before it stops: the
# tail of a long miss list is the prevalence, not a threshold argument.
MISSED_SHOWN = 12


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{100 * value:.1f}%"


def format_report(result: dict[str, Any]) -> str:
    """The six steps as a plain-text report, in the plan's order."""
    out: list[str] = []
    meta = result["pass"]
    out.append(f"=== {meta['tag']} — {meta['judged']} of {meta['total']} screens judged ===")
    out.append(
        f"  key {meta['key_entries']} entries · metric rows {meta['metric_rows']} · place records {meta['place_records']}"
    )
    if meta["unjudged"]:
        out.append(f"  ! {len(meta['unjudged'])} screen(s) in the key were not judged: {meta['unjudged'][:8]}")
    if meta["dropped_unsure"]:
        out.append(f"  dropped as unsure: {len(meta['dropped_unsure'])}")

    rel = result["reliability"]
    out.append("")
    out.append("=== 1. reliability — the blind repeats (every later number sits under this ceiling) ===")
    out.append(f"  whole verdict identical: {rel['exact']}/{rel['pairs']} pairs")
    if rel["missing_repeats"]:
        out.append(f"  ! repeats without both readings: {rel['missing_repeats']}")
    for code, cell in rel["per_category"].items():
        line = f"  {code} {CATEGORY_LABEL[code]:<18} {cell['agree']}/{cell['pairs']}"
        line += f"  yes {cell['yes']} · no {cell['no']} · disagree {cell['disagree']}"
        if cell["band"]:
            line += f"  [{cell['band']}]"
        out.append(line)
        if cell["too_few_positives"]:
            carried = f"only {cell['carried']} pair" if cell["carried"] else "no pair"
            out.append(f"      ! {carried} carried {code} — that agreement is agreement about the negatives")

    occ = result["occupancy"]
    out.append("")
    out.append(f"=== 2. occupancy — {occ['total']} screens (repeats excluded) ===")
    for code, cell in occ["per_category"].items():
        mark = "   too few — descriptive only" if cell["too_few"] else ""
        out.append(f"  {code} {CATEGORY_LABEL[code]:<18} {cell['n']:>3}  {_pct(cell['share']):>5}{mark}")
    out.append(
        f"  screens carrying something: {occ['flagged']} · {GOOD} together with a finding: {occ['good_with_finding']}"
    )
    out.append(f"  verdict sizes: {occ['verdict_sizes']}")
    out.append(
        f"  marker set on {occ['marker_on_flagged']}/{occ['flagged']} flagged screens ({_pct(occ['marker_rate'])})"
    )
    for pair, cell in occ["overlap"].items():
        if cell["both"]:
            out.append(f"  {pair}: {cell['both']} of {cell['union']} ({_pct(cell['share'])} of the union)")

    gate = result["gate"]
    out.append("")
    if gate is None:
        out.append("=== 3. gate validation — skipped: no --rows (per-occurrence metrics) ===")
    else:
        out.append(
            f"=== 3. gate validation — {gate['metric']} {gate['op']} {gate['threshold']:g}"
            f" ({gate['evaluated']} evaluated, {UNRATABLE} excluded) ==="
        )
        out.append(f"  rejects {gate['rejected']}; their findings: {gate['rejected_verdicts']}")
        for name, cell in gate["targets"].items():
            out.append(
                f"  vs {name:<12} precision {cell['caught']}/{gate['rejected']} = {_ratio(cell['precision'])}"
                f" · recall {cell['caught']}/{cell['positives']} = {_ratio(cell['recall'])}"
            )
            if cell["missed_values"]:
                shown = ", ".join(f"{v:.1f}" for v in cell["missed_values"][:MISSED_SHOWN])
                rest = len(cell["missed_values"]) - MISSED_SHOWN
                out.append(f"      missed {gate['metric']}: {shown}" + (f" (+{rest} more)" if rest > 0 else ""))

    cov = result["coverage"]
    out.append("")
    if cov is None:
        out.append("=== 4. coverage matrix — skipped: no --rows (per-occurrence metrics) ===")
    else:
        out.append(f"=== 4. coverage matrix — AUC ± Hanley-McNeil SE ({cov['evaluated']} evaluated) ===")
        if cov["too_few"]:
            out.append(f"  no column for {', '.join(cov['too_few'])}: fewer than {MIN_POSITIVES} positives")
        if cov["missing_metrics"]:
            out.append(f"  metrics absent from the rows file: {', '.join(cov['missing_metrics'])}")
        header = "  " + "metric".ljust(8) + "".join(f"{name:>16}" for name in cov["columns"])
        out.append(header)
        for metric, row in cov["metrics"].items():
            line = "  " + metric.ljust(8)
            for name in cov["columns"]:
                cell = row[name]
                line += f"{cell['auc']:>10.2f}±{cell['se']:.2f}" if cell["auc"] is not None else f"{'—':>16}"
            out.append(line)
        if cov["metrics"]:
            first = next(iter(cov["metrics"].values()))
            out.append("  n positive: " + ", ".join(f"{name} {first[name]['n_pos']}" for name in cov["columns"]))
        for flag, row in cov["flags"].items():
            out.append(f"  flag {flag} — share carrying it, category against everything else:")
            for name in cov["columns"]:
                cell = row[name]
                here = cell["set"] / cell["n_pos"] if cell["n_pos"] else None
                there = cell["set_elsewhere"] / cell["n_neg"] if cell["n_neg"] else None
                out.append(
                    f"    {name:<4} {cell['set']:>3}/{cell['n_pos']:<3} {_pct(here):>6}"
                    f"   vs {cell['set_elsewhere']:>3}/{cell['n_neg']:<3} {_pct(there):>6}"
                )

    place = result["place"]
    out.append("")
    # Always reported, even without `--spots`: the marker itself comes from the
    # result line, only the anchor geometry is external, and `place_check`
    # degrades to „0 with place geometry" on its own.
    out.append("=== 5. place check — the clicked markers only (an unset marker is not a datum) ===")
    out.append(
        f"  markers set on {place['marked']}/{place['shown']} screens ({_pct(place['marker_rate'])});"
        f" {place['usable']} with place geometry"
    )
    if place["without_geometry"]:
        out.append(f"  ! no place geometry for {len(place['without_geometry'])}: {place['without_geometry'][:8]}")
    out.append(
        f"  click within {ARGMAX_TOLERANCE} anchors of the metric's own maximum:"
        f" {place['argmax_hits']}/{place['usable']} ({_pct(place['argmax_rate'])})"
    )
    out.append(
        f"  click within {EDGE_ANCHORS} anchors of a stroke boundary:"
        f" {place['at_boundary']}/{place['usable']} ({_pct(place['boundary_rate'])})"
    )
    out.append(
        f"  per category, only screens with exactly ONE finding ({place['single_finding']} of {place['usable']}):"
    )
    out.append(f"    {'':<4}{'n':>4}{'head':>7}{'middle':>8}{'tail':>6}{'boundary':>10}")
    for code, cell in place["per_category"].items():
        mark = "  too few" if cell["too_few"] else ""
        out.append(
            f"    {code:<4}{cell['n']:>4}{cell['head']:>7}{cell['middle']:>8}{cell['tail']:>6}"
            f"{cell['at_boundary']:>10}{mark}"
        )

    out.append("")
    out.append(f"=== 6. drift — the sequence in {len(result['drift']['blocks'])} blocks ===")
    for block in result["drift"]["blocks"]:
        mix = " ".join(f"{code} {n}" for code, n in block["categories"].items() if n)
        median = "—" if block["median_seconds"] is None else f"{block['median_seconds']:g}s"
        out.append(
            f"  {block['range'][0]:>3}–{block['range'][1]:<3} n {block['n']:>3} · {mix}"
            f" · marked {block['marked']} · median {median} (n {block['timed']})"
        )

    if result["notes"]:
        out.append("")
        out.append("=== notes (verbatim) ===")
        for note in result["notes"]:
            out.append(f'  {note["uid"]} ({note["glyph"]}, {note["word"]}, {note["codes"]}) "{note["note"]}"')
    return "\n".join(out)


def _ratio(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}"


# ------------------------------------------------------------------- CLI


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--result", type=Path, required=True, help="the text the page's final screen emitted")
    parser.add_argument("--key", type=Path, required=True, help="the round's key (uid -> occurrence, repeats marked)")
    parser.add_argument(
        "--rows",
        type=Path,
        help="per-occurrence metrics, one record per uid; without it steps 3-4 are skipped, step 5"
        " degrades to the marker rate, and reliability, occupancy, drift and the notes run in full",
    )
    parser.add_argument("--spots", type=Path, help="per-marker place geometry (idx, rel, edge_dist, argmax_idx)")
    parser.add_argument("--metrics", help=f"comma-separated metric names (default: {','.join(DEFAULT_METRICS)})")
    parser.add_argument("--flags", help="comma-separated boolean row fields (default: every boolean field found)")
    parser.add_argument(
        "--union",
        action="append",
        default=[],
        metavar="W,B",
        help="score these categories together as one column (the plan's fallback for two the judge does "
        "not separate); repeatable",
    )
    parser.add_argument("--gate", default=DEFAULT_GATE, help=f"gate to validate, default {DEFAULT_GATE}")
    parser.add_argument("--drop-unsure", action="store_true", help="repeat the whole analysis without the U verdicts")
    parser.add_argument("--json", dest="json_out", type=Path, help="also write every number as JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    parsed = parse_result(args.result.read_text(encoding="utf-8"))
    key = load_key(json.loads(args.key.read_text(encoding="utf-8")))
    rows = index_by_uid(json.loads(args.rows.read_text(encoding="utf-8"))) if args.rows else {}
    geometry = dict(rows)
    if args.spots:
        for uid, record in index_by_uid(json.loads(args.spots.read_text(encoding="utf-8"))).items():
            geometry[uid] = {**geometry.get(uid, {}), **record}

    metrics = tuple(m.strip() for m in args.metrics.split(",") if m.strip()) if args.metrics else DEFAULT_METRICS
    flags = tuple(f.strip() for f in args.flags.split(",") if f.strip()) if args.flags else None
    unions = tuple(parse_union(spec) for spec in args.union)
    result = analyse(
        parsed,
        key,
        rows,
        geometry,
        metrics=metrics,
        flags=flags,
        unions=unions,
        gate=args.gate,
        drop_unsure=args.drop_unsure,
    )
    print(format_report(result))
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
