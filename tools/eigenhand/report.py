"""The Bestandsbericht — Soll/Ist per glyph position and join, plus the queue.

Ist = shaped Belege over all ``angenommen`` Fassungen of one hand (withdrawn
ones do not count). Soll = the shared two-tier model (``pool.soll_model``).
Headlines:

* **Erstbeleg-Quote** — share of Soll items with ≥1 Beleg; reported both
  UNWEIGHTED and WEIGHTED by Übergangsraum frequency. The weighted number is
  the honest headline: the corpus tail (rare-but-real items) cannot drag it
  down faster than its real-text relevance warrants.
* **Ausbau-Quote** — Σ min(Ist, Soll) / Σ Soll, weighted the same way.

The print recommendation reuses sheet.py's queue so "what to print next"
and "what --next actually prints" can never diverge.

    uv run python -m tools.eigenhand.report --hand mn-suetterlin
"""

from __future__ import annotations

import argparse

from core.eigenhand.bestand import ist_counts, quoten
from core.eigenhand.bogen import select_strips
from core.eigenhand.plan import load_plan
from tools.eigenhand.kartei import accepted_fassungen, load_kartei
from tools.eigenhand.pool import soll_model
from tools.eigenhand.universe import load_universe


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--top", type=int, default=25, help="largest weighted deficits to list (default: %(default)s)")
    ap.add_argument("--next", type=int, default=9, dest="next_rows", help="print-queue preview length")
    args = ap.parse_args(argv)

    plan = load_plan()
    kartei = load_kartei(args.hand)
    universe = load_universe()
    weights, targets = soll_model(universe["items"])
    ist = ist_counts(kartei, plan)

    # The same numbers the admin view shows — one definition, two surfaces.
    q = quoten(ist, weights, targets)

    n_fassungen = len(accepted_fassungen(kartei))
    print(f"Bestandsbericht {args.hand} — {n_fassungen} angenommene Fassungen")
    print(
        f"  Erstbeleg-Quote: {q['erstbeleg']}/{q['items']} items "
        f"({q['erstbeleg_share']:.1%} ungewichtet · {q['erstbeleg_weighted']:.1%} gewichtet)"
    )
    print(
        f"  Ausbau-Quote:    {q['ausbau']}/{q['soll_belege']} Belege "
        f"({q['ausbau_share']:.1%} ungewichtet · {q['ausbau_weighted']:.1%} gewichtet)"
    )

    deficits = sorted(
        ((targets[item] - ist[item], weights[item], item) for item in targets if ist[item] < targets[item]),
        key=lambda row: (-row[1], -row[0], row[2]),
    )
    print(f"\n  größte gewichtete Fehlstellen (top {args.top}):")
    print(f"  {'Item':<18} {'Ist':>4} {'Soll':>5} {'Gewicht':>12}")
    for _deficit, weight, item in deficits[: args.top]:
        print(f"  {item:<18} {ist[item]:>4} {targets[item]:>5} {weight:>12.1f}")

    queue = select_strips(plan, kartei, args.next_rows, 1, (weights, targets))
    print(f"\n  Druckvorschlag (nächste {args.next_rows} Zeilen): {' '.join(queue)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
