"""Coverage progression over the strip plan — how the Soll fills, strip by strip.

Answers "after 10, 20, … strips, how often has every glyph (upper/lower),
digit, sign and join been written?" for the PLANNED sequence (plan order
S0001…), so sheets, curation waves and the packing can be optimized before
any ink flows — and re-run identically after every change (owner wish
2026-08-22: repeatable helpers).

Checkpoints every ``--step`` strips (plus the final partial one). Per
checkpoint: cumulative counts per glyph_key (bucketed klein · gross ·
ligatur · ziffer · zeichen), per join, and — when the local Übergangsraum
exists — the weighted/unweighted Erstbeleg and Ausbau quotas against the
shared Soll model. ``--json`` dumps the full structure (the artifact and
any later optimisation loop read that).

    uv run python -m tools.eigenhand.progression --step 10 --json temp/progression.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from tools.eigenhand import coverage, pool
from tools.eigenhand.corpus import pool_entries, shaping_form
from tools.eigenhand.pool import load_plan, soll_model
from tools.eigenhand.store import STREIFEN_JSON
from tools.eigenhand.universe import load_universe


_LIGATURES = {"ch", "ck", "tz", "longst", "qu", "sz"}
_LOWER_EXTRA = {"ae", "oe", "ue", "longs"}
_UPPER_EXTRA = {"Ae", "Oe", "Ue"}


def classify_key(key: str) -> str:
    """Bucket a glyph_key: klein · gross · ligatur · ziffer · zeichen."""
    if key in _LIGATURES:
        return "ligatur"
    if key.isdigit():
        return "ziffer"
    if key in _LOWER_EXTRA or (len(key) == 1 and key.islower()):
        return "klein"
    if key in _UPPER_EXTRA or (len(key) == 1 and key.isupper()):
        return "gross"
    return "zeichen"


def ordered_strips(plan: dict) -> list[str]:
    return sorted(plan["strips"], key=lambda sid: int(sid[1:]))


def checkpoints(plan: dict, step: int, universe_items: dict[str, float] | None) -> list[dict]:
    """Cumulative coverage at every ``step`` strips of the planned sequence."""
    forms = {e["word"]: shaping_form(e) for e in pool_entries()}
    soll = soll_model(universe_items)[0:2] if universe_items is not None else None
    weights, targets = soll if soll else ({}, {})
    total_weight = sum(weights.values()) or 1.0

    strips = ordered_strips(plan)
    marks = list(range(step, len(strips), step)) + [len(strips)]

    out: list[dict] = []
    items: Counter[str] = Counter()
    words_seen = 0
    done = 0
    for mark in marks:
        for sid in strips[done:mark]:
            for word in plan["strips"][sid]["words"]:
                items.update(coverage.word_items(forms.get(word, word)))
                words_seen += 1
        done = mark

        glyphs: dict[str, int] = {}
        joins: dict[str, int] = {}
        for item, count in items.items():
            if coverage.JOIN_SEP in item:
                joins[item] = joins.get(item, 0) + count
            else:
                key = item.split(coverage.POSITION_SEP)[0]
                glyphs[key] = glyphs.get(key, 0) + count
        buckets: dict[str, dict[str, int]] = {"klein": {}, "gross": {}, "ligatur": {}, "ziffer": {}, "zeichen": {}}
        for key, count in glyphs.items():
            buckets[classify_key(key)][key] = count

        checkpoint = {
            "strips": mark,
            "words": words_seen,
            "glyphs": {bucket: dict(sorted(keys.items())) for bucket, keys in buckets.items()},
            "joins": dict(sorted(joins.items())),
            "joins_distinct": len(joins),
            "joins_total": sum(joins.values()),
        }
        if soll:
            covered = sum(1 for item in weights if items[item] > 0)
            checkpoint["quotas"] = {
                "erstbeleg": covered / max(1, len(weights)),
                "erstbeleg_weighted": sum(w for item, w in weights.items() if items[item] > 0) / total_weight,
                "ausbau": sum(min(items[item], targets[item]) for item in targets) / max(1, sum(targets.values())),
            }
        out.append(checkpoint)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--step", type=int, default=10, help="checkpoint interval in strips (default: %(default)s)")
    ap.add_argument("--json", type=Path, default=None, help="write the full structure to this path")
    ap.add_argument("--no-universe", action="store_true", help="skip the quota columns (no Übergangsraum needed)")
    args = ap.parse_args(argv)
    if args.step < 1:
        ap.error("--step must be at least 1 strip")

    plan = load_plan(STREIFEN_JSON)
    universe_items = None
    if not args.no_universe:
        try:
            universe_items = load_universe()["items"]
        except SystemExit:
            print("note: no local Übergangsraum — quota columns skipped (run tools.eigenhand.universe)")
    points = checkpoints(plan, args.step, universe_items)

    header = f"{'Streifen':>8} {'Wörter':>7} {'klein':>6} {'gross':>6} {'Ligat.':>6} {'Ziffer':>6} {'Zeich.':>6} {'Joins':>6}"
    if universe_items is not None:
        header += f" {'Erstb.gew.':>10}"
    print(header)
    for point in points:
        row = (
            f"{point['strips']:>8} {point['words']:>7} "
            f"{len(point['glyphs']['klein']):>6} {len(point['glyphs']['gross']):>6} "
            f"{len(point['glyphs']['ligatur']):>6} {len(point['glyphs']['ziffer']):>6} "
            f"{len(point['glyphs']['zeichen']):>6} {point['joins_distinct']:>6}"
        )
        if "quotas" in point:
            row += f" {point['quotas']['erstbeleg_weighted']:>9.1%}"
        print(row)

    # The hard per-glyph floor (pool.GLYPH_MIN_PLANNED): name every key still
    # under it at the end of the plan — silence must mean "all covered".
    final = points[-1]
    totals = {key: count for bucket in final["glyphs"].values() for key, count in bucket.items()}
    floor = pool.GLYPH_MIN_PLANNED
    under = sorted(key for key, count in totals.items() if count < floor)
    if under:
        print(f"unter Mindestbelegung ({floor}): {', '.join(under)}")
    else:
        print(f"Mindestbelegung {floor} je Glyphe: erfüllt")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps({"format": 1, "step": args.step, "checkpoints": points}, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
