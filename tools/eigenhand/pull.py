"""Fetch a Bogen printed in the admin view down to this machine.

The admin view mints and stores the Bogen; the ingest chain needs it on disk —
``layout.json`` (the geometry contract a scan is registered against) and
``bogen.pdf`` (what the printer gets). This writes both into
``<dataroot>/<hand>/blaetter/<B>/`` and records the print in the local Kartei,
so ``ingest`` → Siebung → ``apply`` then run exactly as for a locally printed
sheet.

Never overwrites: a Bogen already on disk is only verified (the layout hash
must match), because a scan may already have been registered against it.

    ADMIN_TOKEN=… uv run python -m tools.eigenhand.pull --hand mn-suetterlin --sheet B0007
"""

from __future__ import annotations

import argparse
import hashlib
import json

from core.eigenhand.bogen import layout_text
from tools.eigenhand.apiclient import admin_token, api_base, request_bytes
from tools.eigenhand.kartei import load_kartei, save_kartei
from tools.eigenhand.store import check_hand_id, check_sheet_id, sheet_dir


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--sheet", required=True, help="Bogen id, e.g. B0007")
    ap.add_argument("--api", default=None, help="API base URL (default: $EIGENHAND_API or production)")
    ap.add_argument("--token", default=None, help="admin token (default: $ADMIN_TOKEN)")
    args = ap.parse_args(argv)

    hand, sheet = check_hand_id(args.hand), check_sheet_id(args.sheet)
    token = admin_token(args.token)
    base = api_base(args.api)

    layout = json.loads(request_bytes("GET", f"{base}/eigenhand/sheets/{hand}/{sheet}/layout", token).decode())
    text = layout_text(layout)
    digest = hashlib.sha256(text.encode()).hexdigest()

    out_dir = sheet_dir(hand, sheet)
    existing = out_dir / "layout.json"
    if existing.exists():
        local = hashlib.sha256(existing.read_text(encoding="utf-8").encode()).hexdigest()
        if local != digest:
            raise SystemExit(
                f"{existing} differs from the stored Bogen — refusing to overwrite a layout a scan may reference"
            )
        print(f"{sheet}: already on disk and identical")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    existing.write_text(text, encoding="utf-8")
    (out_dir / "bogen.pdf").write_bytes(request_bytes("GET", f"{base}/eigenhand/sheets/{hand}/{sheet}/pdf", token))

    kartei = load_kartei(hand, layout["style"])
    kartei["sheets"].setdefault(
        sheet,
        {
            "printed": layout["provenance"]["date"],
            "strips": [row["strip"] for row in layout["rows"]],
            "layout_sha256": digest,
            "scans": [],
        },
    )
    save_kartei(hand, kartei)
    print(f"wrote {out_dir / 'bogen.pdf'} and layout.json, {len(layout['rows'])} rows — ingest can register against it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
