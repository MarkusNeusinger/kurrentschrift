"""Queue strips for re-recording — "strips 37 and 55 once more".

Adds redo entries to the Kartei; the print queue serves them FIRST on the
next ``sheet.py`` run. By default the new Fassung ADDS to the existing ones
(more repetitions = better statistics — owner decision 2026-08-22);
``--retire`` additionally withdraws the strip's accepted Fassungen
(status ``zurueckgezogen``: file kept, excluded from Ist counts and training
exports). A redo entry clears automatically once a new Fassung of its strip
is accepted.

The status value is the ASCII one from ``core.eigenhand.ids.STATUSES``, not the
German spelling this file used until 2026-08-25. ``sync`` posts every Fassung's
status verbatim in ONE request, so a single umlaut made the API refuse the
whole batch with a 422 — and no verdict of that hand could ever be pushed
again, since the Kartei is not meant to be edited by hand.

    uv run python -m tools.eigenhand.redo --hand mn-suetterlin S0037 S0055 --reason "nicht optimal"
"""

from __future__ import annotations

import argparse
import datetime

from core.eigenhand.ids import ACCEPTED, RETIRED
from core.eigenhand.plan import STREIFEN_JSON, load_plan
from tools.eigenhand.kartei import load_kartei, save_kartei


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("strips", nargs="+", help="strip ids, e.g. S0037 S0055")
    ap.add_argument("--hand", required=True)
    ap.add_argument("--reason", default="", help="why (lands in the Kartei entry)")
    ap.add_argument("--retire", action="store_true", help="also withdraw the strips' accepted Fassungen")
    ap.add_argument(
        "--date", "--datum", dest="date", default=None, help="ISO date (default: today; explicit for tests)"
    )
    args = ap.parse_args(argv)

    plan = load_plan(STREIFEN_JSON)
    unknown = [sid for sid in args.strips if sid not in plan["strips"]]
    if unknown:
        raise SystemExit(f"unknown strips: {', '.join(unknown)}")

    date = args.date or datetime.date.today().isoformat()
    kartei = load_kartei(args.hand)
    retired = 0
    for sid in args.strips:
        if not any(entry["strip"] == sid for entry in kartei["redo"]):
            kartei["redo"].append({"strip": sid, "reason": args.reason, "queued": date})
        if args.retire:
            for fassung in kartei["strips"].get(sid, {}).get("fassungen", []):
                if fassung["status"] == ACCEPTED:
                    fassung["status"] = RETIRED
                    fassung["retired"] = date
                    retired += 1
    save_kartei(args.hand, kartei)
    note = f", {retired} Fassungen zurückgezogen" if args.retire else ""
    print(f"queued {len(args.strips)} strip(s) for re-recording{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
