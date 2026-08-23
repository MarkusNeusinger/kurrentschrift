"""Push the local Kartei's bookkeeping to the API — counts, never pixels.

The judging happens locally (the strips are there); this is what makes the
result visible in the admin view. Two pushes, in this order:

1. every Bogen printed locally, registered with its layout — so the server
   stops handing out an id the paper on the desk already carries;
2. every judged row as a Fassung: strip, sheet, row index, verdict, reason,
   the local file's SHA256. No image, no scan, no session details beyond the
   filing date.

Idempotent on both sides: a Bogen with the same layout is a no-op, a row whose
verdict already matches is skipped, and a CONTRADICTING verdict is refused
rather than overwritten (the API answers 409). Run it as often as you like.

    ADMIN_TOKEN=… uv run python -m tools.eigenhand.sync --hand mn-suetterlin
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request

from tools.eigenhand.kartei import load_kartei
from tools.eigenhand.store import check_hand_id, sheet_dir


DEFAULT_API = "https://api.kurrentschrift.ink"


def _request(method: str, url: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"X-Admin-Token": token}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)  # noqa: S310 — https URL from argv
    try:
        with urllib.request.urlopen(req, timeout=60) as res:  # noqa: S310
            return json.loads(res.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()[:400]
        raise SystemExit(f"{method} {url} → {exc.code}: {detail}") from exc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--api", default=os.environ.get("EIGENHAND_API", DEFAULT_API), help="API base URL")
    ap.add_argument("--token", default=os.environ.get("ADMIN_TOKEN"), help="admin token (default: $ADMIN_TOKEN)")
    ap.add_argument("--dry-run", action="store_true", help="show what would be pushed, push nothing")
    args = ap.parse_args(argv)

    hand = check_hand_id(args.hand)
    if not args.token and not args.dry_run:
        raise SystemExit("no admin token — set ADMIN_TOKEN or pass --token")
    kartei = load_kartei(hand)
    base = args.api.rstrip("/")

    fassungen = [
        {
            "strip": strip,
            "fassung": f["id"],
            "sheet": f["sheet"],
            "row_index": f["row_index"],
            "attempt": f.get("attempt", 1),
            "attempts": f.get("attempts", 1),
            "status": f["status"],
            "reason": f.get("reason"),
            "note": f.get("note"),
            "png_sha256": f.get("png_sha256"),
            "filed_on": f.get("filed"),
        }
        for strip, record in sorted(kartei["strips"].items())
        for f in record.get("fassungen", [])
    ]
    if args.dry_run:
        print(f"would push {len(kartei['sheets'])} Bögen and {len(fassungen)} Fassungen for {hand} to {base}")
        return 0

    imported = 0
    for sheet_id, sheet in sorted(kartei["sheets"].items()):
        # The layout is the geometry contract; without it the server would hold
        # a Bogen it could neither re-render nor hand back to an ingest run.
        layout_file = sheet_dir(hand, sheet_id) / "layout.json"
        if not layout_file.exists():
            print(f"skip {sheet_id}: no layout.json on this machine")
            continue
        result = _request(
            "PUT",
            f"{base}/eigenhand/sheets/{hand}/{sheet_id}",
            args.token,
            {
                "style": kartei["style"],
                "printed_on": sheet["printed"],
                "strips": sheet["strips"],
                "layout": json.loads(layout_file.read_text(encoding="utf-8")),
                "layout_sha256": sheet["layout_sha256"],
            },
        )
        imported += 1 if result.get("imported") else 0

    pushed = _request("POST", f"{base}/eigenhand/fassungen", args.token, {"hand": hand, "fassungen": fassungen})
    print(
        f"{hand}: {imported} new Bögen registered ({len(kartei['sheets'])} known), "
        f"{pushed['recorded']} Fassungen recorded, {pushed['skipped']} already there"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
