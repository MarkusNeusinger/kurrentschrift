"""The Bestandsbericht — Soll/Ist per glyph position and join, plus the queue.

Ist = shaped Belege over all ``angenommen`` Fassungen of one hand (withdrawn
ones do not count). Soll = the shared two-tier model (``pool.soll_model``).
Headlines:

* **Erstbeleg-Quote** — share of Soll items with ≥1 Beleg; reported both
  UNWEIGHTED and WEIGHTED by Übergangsraum frequency. The weighted number is
  the honest headline: the corpus tail (rare-but-real items) cannot drag it
  down faster than its real-text relevance warrants.
* **Ausbau-Quote** — Σ min(Ist, Soll) / Σ Soll, weighted the same way.

The print recommendation reuses sheet.py's queue so „was als Nächstes
drucken?“ and „was druckt --next wirklich?“ can never diverge.

    uv run python -m tools.eigenhand.report --hand mn-suetterlin
"""

from __future__ import annotations

import argparse
from collections import Counter

from tools.eigenhand import coverage
from tools.eigenhand.corpus import pool_entries
from tools.eigenhand.kartei import accepted_fassungen, load_kartei
from tools.eigenhand.pool import load_plan, soll_model
from tools.eigenhand.sheet import select_strips
from tools.eigenhand.store import STREIFEN_JSON
from tools.eigenhand.universe import load_universe


def ist_counts(kartei: dict, plan: dict) -> Counter[str]:
    """Item → Beleg count over the hand's accepted Fassungen (shaped forms)."""
    forms = {e["word"]: e.get("fugen") or e["word"] for e in pool_entries()}
    counts: Counter[str] = Counter()
    for strip, _fassung in accepted_fassungen(kartei):
        for word in plan["strips"][strip]["words"]:
            counts.update(coverage.word_items(forms.get(word, word)))
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--top", type=int, default=25, help="largest weighted deficits to list (default: %(default)s)")
    ap.add_argument("--next", type=int, default=9, dest="next_rows", help="print-queue preview length")
    args = ap.parse_args(argv)

    plan = load_plan(STREIFEN_JSON)
    kartei = load_kartei(args.hand)
    universe = load_universe()
    weights, targets = soll_model(universe["items"])
    ist = ist_counts(kartei, plan)

    total_weight = sum(weights.values()) or 1.0
    erstbeleg = sum(1 for item in weights if ist[item] > 0)
    erstbeleg_weighted = sum(w for item, w in weights.items() if ist[item] > 0) / total_weight
    soll_sum = sum(targets.values())
    ausbau = sum(min(ist[item], targets[item]) for item in targets)
    ausbau_weighted_num = sum(min(ist[item], targets[item]) * (weights[item] / total_weight) for item in targets)
    ausbau_weighted_den = sum(targets[item] * (weights[item] / total_weight) for item in targets) or 1.0

    n_fassungen = len(accepted_fassungen(kartei))
    print(f"Bestandsbericht {args.hand} — {n_fassungen} angenommene Fassungen")
    print(
        f"  Erstbeleg-Quote: {erstbeleg}/{len(weights)} items "
        f"({erstbeleg / max(1, len(weights)):.1%} ungewichtet · {erstbeleg_weighted:.1%} gewichtet)"
    )
    print(
        f"  Ausbau-Quote:    {ausbau}/{soll_sum} Belege "
        f"({ausbau / max(1, soll_sum):.1%} ungewichtet · {ausbau_weighted_num / ausbau_weighted_den:.1%} gewichtet)"
    )

    deficits = sorted(
        ((targets[item] - ist[item], weights[item], item) for item in targets if ist[item] < targets[item]),
        key=lambda row: (-row[1], -row[0], row[2]),
    )
    print(f"\n  größte gewichtete Fehlstellen (top {args.top}):")
    print(f"  {'Item':<18} {'Ist':>4} {'Soll':>5} {'Gewicht':>12}")
    for _deficit, weight, item in deficits[: args.top]:
        print(f"  {item:<18} {ist[item]:>4} {targets[item]:>5} {weight:>12.1f}")

    queue = select_strips(plan, kartei, args.next_rows, 1)
    print(f"\n  Druckvorschlag (nächste {args.next_rows} Zeilen): {' '.join(queue)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
