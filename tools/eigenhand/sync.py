"""Push the local Kartei to the API — the bookkeeping always, the strips on request.

The judging happens locally (the strips are there); this is what makes the
result visible in the admin view. Three pushes, in this order:

1. every Bogen printed locally, registered with its layout — so the server
   stops handing out an id the paper on the desk already carries;
2. every judged row as a Fassung: strip, sheet, row index, verdict, reason, the
   effective nib/ink/paper, the local file's SHA256. No scan, no pixels;
3. with ``--mit-streifen``, the strip images of the accepted Fassungen.

Idempotent throughout: a Bogen with the same layout is a no-op, a row whose
verdict already matches is skipped, a strip whose bytes are already stored is
skipped, and a CONTRADICTION is refused rather than overwritten (the API
answers 409). Run it as often as you like.

The order matters and is enforced on the server: a verdict has to name a row
that was actually printed, and a strip has to name a row that was judged. A
Bogen whose ``layout.json`` is missing here is skipped, and its verdicts are
held back rather than sent into a 404; they go up on a later run.

Uploading the strips is opt-in, not default. They are the reserved own-hand
dataset, they are ~350 KB each, and the private ARCHIVE — not the DB — is
their master copy; the DB copy exists so the workbench can show a written
Streifen the way it shows a chart crop.

    ADMIN_TOKEN=… uv run python -m tools.eigenhand.sync --hand mn-suetterlin
    ADMIN_TOKEN=… uv run python -m tools.eigenhand.sync --hand mn-suetterlin --mit-streifen

RESTORING after a DB loss reads the same push out of an archive snapshot
instead of the working data root — repo + archive is the guarantee, and this
is the path that redeems it (`docs/proposals/eigenhand-erfassung.md` §8.1):

    ADMIN_TOKEN=… uv run python -m tools.eigenhand.sync --hand mn-suetterlin \
        --from ~/kurrentschrift-archive/own-hand/mn-suetterlin/2026-08-24-1830 \
        --mit-streifen
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

from tools.eigenhand.apiclient import admin_token, api_base, request_json
from tools.eigenhand.kartei import load_kartei
from tools.eigenhand.store import check_hand_id, hand_dir, sheet_dir


def _source(hand: str, snapshot: Path | None) -> tuple[dict, Path]:
    """The Kartei and the root its Fassung/Bogen paths hang off.

    Two shapes, one reader. The working data root is
    ``<dataroot>/<hand>/``; an archive snapshot is
    ``own-hand/<hand>/<stamp>/`` with the same ``fassungen/`` and
    ``blaetter/`` layout beneath it (`tools/eigenhand/snapshot.py`). Making
    them interchangeable here is what keeps the restore path from being a
    second, untested implementation of the sync.
    """
    if snapshot is None:
        return load_kartei(hand), hand_dir(hand)
    root = snapshot.expanduser().resolve()
    kartei_file = root / "kartei.json"
    if not kartei_file.exists():
        raise SystemExit(f"{kartei_file} missing — point --from at a snapshot directory, not at its parent")
    kartei = json.loads(kartei_file.read_text(encoding="utf-8"))
    if kartei.get("hand") != hand:
        raise SystemExit(f"snapshot holds hand {kartei.get('hand')!r}, not {hand!r} — refusing to push it as {hand}")
    return kartei, root


def _layout_file(root: Path, hand: str, sheet_id: str, snapshot: bool) -> Path:
    return (root / "blaetter" / sheet_id / "layout.json") if snapshot else (sheet_dir(hand, sheet_id) / "layout.json")


def _fassung_rows(kartei: dict) -> list[dict]:
    return [
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
            # The effective setup of THIS row, as the Siebung recorded it.
            **{key: (f.get("session") or {}).get(key) or None for key in ("feder", "tinte", "papier", "geraet")},
        }
        for strip, record in sorted(kartei["strips"].items())
        for f in record.get("fassungen", [])
    ]


def _push_strips(base: str, token: str, hand: str, root: Path, kartei: dict, sendable: set[str]) -> tuple[int, int]:
    """Upload the strip images whose bytes the server does not hold yet.

    Skipping is decided by SHA256, not by presence: a hash already stored is
    the same file, and re-sending it would be bytes over the wire for nothing.
    A file whose hash disagrees with the Kartei is not sent at all — that is a
    local corruption, and the server is not the place to discover it.

    An accepted Fassung whose ``streifen.png``/``meta.json`` is MISSING is not
    skipped quietly (Copilot review, PR #410): `apply.py` files both for every
    accepted row, so their absence means a damaged data root or a snapshot that
    was filed incomplete — and on the restore path that is exactly the case
    where a silent skip would report success while leaving strips out of the
    DB. Everything that IS there still goes up (a single gap must not hide the
    rest), then the run fails naming what was missing.
    """
    stored = {
        f"{row['strip']}/{row['fassung']}": row["sha256"]
        for row in request_json("GET", f"{base}/eigenhand/strips/{hand}", token).get("strips", [])
    }
    sent = skipped = 0
    missing: list[str] = []
    for strip, record in sorted(kartei["strips"].items()):
        for f in record.get("fassungen", []):
            if f["status"] != "angenommen" or f["sheet"] not in sendable:
                continue
            png_file = root / "fassungen" / strip / f["id"] / "streifen.png"
            meta_file = png_file.with_name("meta.json")
            if not png_file.exists() or not meta_file.exists():
                absent = [p.name for p in (png_file, meta_file) if not p.exists()]
                missing.append(f"{strip}/{f['id']} ({', '.join(absent)})")
                continue
            png = png_file.read_bytes()
            digest = hashlib.sha256(png).hexdigest()
            if f.get("png_sha256") and f["png_sha256"] != digest:
                raise SystemExit(
                    f"{png_file} has changed since it was filed (Kartei says {f['png_sha256'][:10]}…, "
                    f"file is {digest[:10]}…) — refusing to push a strip that no longer matches its record"
                )
            if stored.get(f"{strip}/{f['id']}") == digest:
                skipped += 1
                continue
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            width, height = _png_size(png)
            request_json(
                "PUT",
                f"{base}/eigenhand/strips/{hand}/{strip}/{f['id']}",
                token,
                {
                    "sheet": f["sheet"],
                    "row_index": f["row_index"],
                    "png_base64": base64.b64encode(png).decode(),
                    "width_px": width,
                    "height_px": height,
                    "dpi": float(meta.get("scan", {}).get("dpi_estimate") or 300.0),
                    "crop_origin_mm": meta.get("crop_origin_mm") or [0.0, 0.0],
                    "sha256": digest,
                },
            )
            sent += 1
    if missing:
        raise SystemExit(
            f"{len(missing)} accepted Fassung(en) of {hand} have no filed strip: {', '.join(missing)}\n"
            f"{sent} strip(s) were uploaded before this; the run is INCOMPLETE. `apply.py` files "
            "streifen.png and meta.json for every accepted row, so this is a damaged data root or an "
            "archive snapshot that was filed incomplete — check the source before treating the DB copy "
            "as whole."
        )
    return sent, skipped


def _png_size(png: bytes) -> tuple[int, int]:
    """Width and height straight out of the IHDR — no image library needed."""
    if not png.startswith(b"\x89PNG\r\n\x1a\n") or png[12:16] != b"IHDR":
        raise SystemExit("filed strip is not a PNG with a leading IHDR chunk")
    return int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--api", default=None, help="API base URL (default: $EIGENHAND_API or production)")
    ap.add_argument("--token", default=None, help="admin token (default: $ADMIN_TOKEN)")
    ap.add_argument("--dry-run", action="store_true", help="show what would be pushed, push nothing")
    ap.add_argument(
        "--mit-streifen",
        dest="with_strips",
        action="store_true",
        help="also upload the strip images of the accepted Fassungen (reserved dataset — opt-in)",
    )
    ap.add_argument(
        "--from",
        dest="snapshot",
        type=Path,
        default=None,
        help="read from an ARCHIVE SNAPSHOT directory instead of the working data root (restore path)",
    )
    args = ap.parse_args(argv)

    hand = check_hand_id(args.hand)
    kartei, root = _source(hand, args.snapshot)
    base = api_base(args.api)
    fassungen = _fassung_rows(kartei)

    if args.dry_run:
        print(
            f"would push {len(kartei['sheets'])} Bögen and {len(fassungen)} Fassungen for {hand} to {base}"
            + (" (with strip images)" if args.with_strips else "")
            + (f" from {root}" if args.snapshot else "")
        )
        return 0
    token = admin_token(args.token)

    imported = 0
    known: set[str] = set()
    for sheet_id, sheet in sorted(kartei["sheets"].items()):
        # The layout is the geometry contract; without it the server would hold
        # a Bogen it could neither re-render nor hand back to an ingest run.
        layout_file = _layout_file(root, hand, sheet_id, args.snapshot is not None)
        if not layout_file.exists():
            print(f"skip {sheet_id}: no layout.json {'in the snapshot' if args.snapshot else 'on this machine'}")
            continue
        result = request_json(
            "PUT",
            f"{base}/eigenhand/sheets/{hand}/{sheet_id}",
            token,
            {
                "style": kartei["style"],
                "printed_on": sheet["printed"],
                "strips": sheet["strips"],
                "layout": json.loads(layout_file.read_text(encoding="utf-8")),
                "layout_sha256": sheet["layout_sha256"],
            },
        )
        known.add(sheet_id)
        imported += 1 if result.get("imported") else 0

    # Hold back the verdicts of a Bogen the server does not know: it would
    # refuse them anyway (a Fassung has to name a printed row), and one 404
    # would abort an otherwise fine sync.
    sendable = [f for f in fassungen if f["sheet"] in known]
    held = len(fassungen) - len(sendable)
    pushed = request_json("POST", f"{base}/eigenhand/fassungen", token, {"hand": hand, "fassungen": sendable})
    line = (
        f"{hand}: {imported} new Bögen registered ({len(kartei['sheets'])} known), "
        f"{pushed['recorded']} Fassungen recorded, {pushed['skipped']} already there"
        + (f", {held} held back (Bogen not registered)" if held else "")
    )
    if args.with_strips:
        sent, skipped = _push_strips(base, token, hand, root, kartei, known)
        line += f", {sent} strips uploaded, {skipped} already stored"
    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
