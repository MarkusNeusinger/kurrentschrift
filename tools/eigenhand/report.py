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

Since the Streifen-Befund (proposal §7.3) the report closes the loop the other
way round as well: **which of the strips already written is worth writing
again**. Per accepted Fassung it prints the suggestion, the ONE reason that
dominates it and the Fassung's rank among the Fassungen of its strip; then the
rewrite list, weakest first. Nothing here changes a verdict — the tick on the
paper stays the judgement, and a Fassung leaves the training data only through
an explicit `redo --retire`.

    uv run python -m tools.eigenhand.report --hand mn-suetterlin
    uv run python -m tools.eigenhand.report --hand mn-suetterlin --befund
"""

from __future__ import annotations

import argparse

from core.eigenhand.befund import befund_index, hand_nib_median, weakest_fassungen
from core.eigenhand.bestand import ist_counts, quoten
from core.eigenhand.bogen import select_strips
from core.eigenhand.plan import load_plan
from core.landmarks import PLATE_PEN_HALF_WIDTH_UNITS
from tools.eigenhand.kartei import accepted_fassungen, load_kartei
from tools.eigenhand.pool import soll_model
from tools.eigenhand.universe import load_universe


def print_befunde(kartei: dict, limit: int) -> None:
    """Per accepted Fassung its verdict sheet, then what to write again.

    The pen every „zu dünn"/„zu dick" is measured against is this hand's OWN
    median (`hand_nib_median`), stated in the header so the number can be read:
    a campaign written with a finer nib than the 1922 plate is not wrong, it is
    a different pen, and only a Fassung that leaves its own campaign is a
    finding.
    """
    index = befund_index(kartei)
    if not index:
        print("\n  Streifen-Befund: noch keine gemessene Fassung (apply misst beim Ablegen)")
        return
    reference = hand_nib_median(kartei)
    print(
        f"\n  Streifen-Befund — Feder dieser Hand: {reference:.4f} xh"
        f" ({reference / PLATE_PEN_HALF_WIDTH_UNITS:.0%} der Tafelfeder)"
        if reference
        else "\n  Streifen-Befund"
    )
    print(f"  {'Streifen':<10} {'Fassung':<8} {'Rang':>5} {'Güte':>6}  {'Vorschlag':<13} Grund")
    for strip, found in index.items():
        for fassung, row in sorted(found.items()):
            place = f"{row.rang}/{row.von}"
            trailer = f" · abgelöst durch {row.abgeloest_von}" if row.abgeloest_von else ""
            print(f"  {strip:<10} {fassung:<8} {place:>5} {row.guete:>6.1f}  {row.vorschlag:<13} {row.grund}{trailer}")
    weak = weakest_fassungen(index)
    if not weak:
        print("\n  neu zu schreiben: nichts — jede gemessene Fassung ist sauber")
        return
    print(f"\n  neu schreiben (schwächste zuerst, {min(limit, len(weak))} von {len(weak)}):")
    for strip, fassung, row in weak[:limit]:
        print(f"  {strip} {fassung}: {row.grund} ({row.vorschlag}, Güte {row.guete:.1f})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--top", type=int, default=25, help="largest weighted deficits to list (default: %(default)s)")
    ap.add_argument("--next", type=int, default=9, dest="next_rows", help="print-queue preview length")
    ap.add_argument(
        "--befund",
        action="store_true",
        help="print the Streifen-Befund per Fassung and the rewrite list instead of the Soll/Ist tables",
    )
    args = ap.parse_args(argv)

    if args.befund:
        kartei = load_kartei(args.hand)
        print(f"Streifen-Befund {args.hand} — {len(accepted_fassungen(kartei))} angenommene Fassungen")
        print_befunde(kartei, args.top)
        return 0

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
    print_befunde(kartei, args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
