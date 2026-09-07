"""Fetch what the admin view holds down to this machine — a Bogen, or the Fleckenmasken.

**A Bogen** (``--sheet``): the admin view mints and stores it, the ingest chain
needs it on disk — ``layout.json`` (the geometry contract a scan is registered
against) and ``bogen.pdf`` (what the printer gets). Both are written into
``<dataroot>/<hand>/blaetter/<B>/`` and the print is recorded in the local
Kartei, so ``ingest`` → Siebung → ``apply`` then run exactly as for a locally
printed sheet.

Never overwrites: a Bogen already on disk is only verified (the layout hash
must match), because a scan may already have been registered against it.

    ADMIN_TOKEN=… uv run python -m tools.eigenhand.pull --hand mn-suetterlin --sheet B0007

**The Fleckenmasken** (``--flecken``): the one field of the capture chain whose
master is the SERVER. The specks are found at import, but the author erases
them with the brush in the workbench (proposal §7.4), so the corrected mask
only exists up there. This brings every hand-edited list back into the local
``kartei.json`` and into the Fassungen's ``meta.json``, which is what puts them
into the next archive snapshot — and from there back into a restored DB, since
``sync --from`` reads the Kartei.

    ADMIN_TOKEN=… uv run python -m tools.eigenhand.pull --hand mn-suetterlin --flecken

Nothing else of a Fassung is touched: the verdict, the Befund and the pixels
are local facts, and only the mask ever changes after filing.
"""

from __future__ import annotations

import argparse
import hashlib
import json

from core.eigenhand.bogen import layout_text
from tools.eigenhand.apiclient import admin_token, api_base, request_bytes, request_json
from tools.eigenhand.kartei import load_kartei, save_kartei
from tools.eigenhand.store import check_hand_id, check_sheet_id, hand_dir, sheet_dir


def pull_sheet(hand: str, sheet: str, base: str, token: str) -> int:
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


def pull_flecken(hand: str, base: str, token: str) -> int:
    """Bring the server's Fleckenmasken down into the Kartei and every meta.json.

    Only the mask moves, and only where it actually differs — a Fassung the
    server has no mask for keeps whatever it has locally, because a NULL up
    there means „nobody has looked", never „the list is empty".
    """
    archive = request_json("GET", f"{base}/eigenhand/archive/{hand}", token) or {}
    server = {
        (row["strip"], row["fassung"]): row["flecken"]
        for row in archive.get("fassungen", [])
        if row.get("flecken") is not None
    }
    if not server:
        print(f"{hand}: the server holds no Fleckenmaske yet — nothing to pull")
        return 0

    kartei = load_kartei(hand, archive.get("style"))
    changed = metas = 0
    for strip, record in kartei["strips"].items():
        for fassung in record.get("fassungen", []):
            circles = server.get((strip, fassung["id"]))
            if circles is None or fassung.get("flecken") == circles:
                continue
            fassung["flecken"] = circles
            changed += 1
            # The Fassung directory only exists for accepted rows; a rejected
            # one is a Kartei record and nothing else.
            meta_file = hand_dir(hand) / "fassungen" / strip / fassung["id"] / "meta.json"
            if meta_file.exists():
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                meta["flecken"] = circles
                meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
                metas += 1
    if changed:
        save_kartei(hand, kartei)
    print(f"{hand}: {changed} Fleckenmaske(n) updated in the Kartei, {metas} meta.json rewritten")
    if changed:
        print(
            f"reminder: snapshot so the archive carries them — uv run python -m tools.eigenhand.snapshot --hand {hand}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--sheet", default=None, help="Bogen id, e.g. B0007")
    ap.add_argument(
        "--flecken",
        action="store_true",
        help="fetch the hand-edited Fleckenmasken back into the Kartei and the Fassungen's meta.json",
    )
    ap.add_argument("--api", default=None, help="API base URL (default: $EIGENHAND_API or production)")
    ap.add_argument("--token", default=None, help="admin token (default: $ADMIN_TOKEN)")
    args = ap.parse_args(argv)

    if bool(args.sheet) == bool(args.flecken):
        ap.error("give either --sheet <B…> or --flecken")

    hand = check_hand_id(args.hand)
    token = admin_token(args.token)
    base = api_base(args.api)
    if args.flecken:
        return pull_flecken(hand, base, token)
    return pull_sheet(hand, check_sheet_id(args.sheet), base, token)


if __name__ == "__main__":
    raise SystemExit(main())
