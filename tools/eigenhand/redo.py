"""Queue strips for re-recording — "strips 37 and 55 once more".

Adds redo entries to the Kartei; the print queue serves them FIRST on the
next ``sheet.py`` run. By default the new Fassung ADDS to the existing ones
(more repetitions = better statistics — owner decision 2026-08-22);
``--retire`` additionally withdraws the strip's accepted Fassungen
(status ``zurückgezogen``: file kept, excluded from Ist counts and training
exports). A redo entry clears automatically once a new Fassung of its strip
is accepted.

    uv run python -m tools.eigenhand.redo --hand mn-suetterlin S0037 S0055 --reason "nicht optimal"
"""

from __future__ import annotations

import argparse
import datetime

from tools.eigenhand.kartei import load_kartei, save_kartei
from tools.eigenhand.pool import load_plan
from tools.eigenhand.store import STREIFEN_JSON


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
                if fassung["status"] == "angenommen":
                    fassung["status"] = "zurückgezogen"
                    fassung["retired"] = date
                    retired += 1
    save_kartei(args.hand, kartei)
    note = f", {retired} Fassungen zurückgezogen" if args.retire else ""
    print(f"queued {len(args.strips)} strip(s) for re-recording{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
