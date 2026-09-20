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

**The hand-drawn Bahnen** (``--pfade``): the one datum of the whole capture
chain that is born UP THERE. Scan, verdict and mask are made at this desk and
pushed; a Bahn the author traces in the workbench exists only in
``eigenhand_strips.pfade``, nothing can follow it again, and neither the
own-hand archive nor the DB snapshot carries it (`api/schemas.py`,
``EigenhandArchiveOut``, says so itself). So it has to be pulled before an
archive run can see it — this is the first link of the chain
``pull --pfade → snapshot → sync --from`` (proposal §7.5/§8.1).

    ADMIN_TOKEN=… uv run python -m tools.eigenhand.pull --hand mn-suetterlin --pfade

Only ``verfahren: "authored"`` entries come down. A FOLLOWED path is a
derivation — strip, layout and follower are all in the archive, so it can be
made again — and filing it would put a second truth beside the one that
regenerates it.

They land as a record in the central ``kartei.json`` and NOWHERE else (author
decision A, 2026-09-20): the Kartei is copied in full by every archive run,
while a filed Fassung directory is an immutable copy unit the run skips by
relative path — a file written into one would never reach the archive and the
run would still report success (`tools/eigenhand/snapshot.py`).

Nothing else of a Fassung is touched: the verdict, the Befund and the pixels
are local facts, and only the mask and the hand-drawn Bahn ever change after
filing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date as date_cls
from urllib.parse import quote

from core.eigenhand.bogen import layout_text
from core.eigenhand.pfad import is_authored
from tools.eigenhand.apiclient import admin_token, api_base, request_bytes, request_json
from tools.eigenhand.kartei import fassung_record, load_kartei, pfad_record, pfade_of, save_kartei
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


def _declared_format(answer: dict, where: str) -> int:
    """The Streifen-Pfad format the API answered under — never guessed.

    An artefact whose semantics this run cannot name is worse than no artefact:
    a restore would push it back declaring a format nobody checked it against.
    """
    declared = answer.get("format")
    if not isinstance(declared, int) or isinstance(declared, bool):
        raise SystemExit(
            f"{where}: the API declared no Streifen-Pfad format — refusing to file a Bahn whose semantics "
            "this run cannot name; update the API before pulling"
        )
    return declared


def pull_pfade(hand: str, base: str, token: str) -> int:
    """Bring the hand-drawn Bahnen down into the Kartei — the one datum born up there.

    One read per stored Fassung, which is a handful: the path list is loaded on
    demand up there (it is a few thousand points per word) and the strip listing
    deliberately does not carry it.

    NEVER deletes, and per BOX, not per Fassung (Copilot review, PR #635). A
    Fassung the server holds no authored Bahn for keeps whatever this machine
    has — but so does a single box of one: if the author hands box 0 to a
    follower and keeps drawing box 1, the server answers with box 1 alone, and
    writing that answer as the record would drop the only remaining copy of
    box 0. The pulled entries are merged over the held ones by `box_index`.

    That merge needs one format policy. The entries carry the API's own
    `PFAD_FORMAT`, one declaration for the whole record, so entries written
    under an older one cannot be carried under a newer declaration without
    mislabelling them. Where that happens AND boxes would have to be retained,
    the Fassung is left untouched and named at the end — a decision for the
    operator, not for this loop.
    """
    listing = request_json("GET", f"{base}/eigenhand/strips/{quote(hand)}", token) or {}
    rows = listing.get("strips", [])
    if not rows:
        print(f"{hand}: the server holds no strip yet — nothing to pull")
        return 0

    kartei = load_kartei(hand)
    today = date_cls.today().isoformat()
    bahnen = fassungen = unchanged = 0
    homeless: list[str] = []
    clashes: list[str] = []
    retained_boxes: list[str] = []
    for row in sorted(rows, key=lambda item: (item["strip"], item["fassung"])):
        strip, fassung = row["strip"], row["fassung"]
        where = f"{strip}/{fassung}"
        url = f"{base}/eigenhand/strips/{quote(hand)}/{quote(strip)}/{quote(fassung)}/pfade"
        answer = request_json("GET", url, token) or {}
        authored = [entry for entry in (answer.get("pfade") or []) if is_authored(entry)]
        record = fassung_record(kartei, strip, fassung)
        if not authored:
            # The server answers with no drawing here — it never had one, or
            # every box has been given up. Either way the Kartei keeps what it
            # has, and when it has something it is now the last copy anywhere.
            # Said out loud in this shape too, not only in the partial one.
            retained_boxes += [f"{where} box {entry['box_index']}" for entry in (pfade_of(record) if record else [])]
            continue
        if record is None:
            # Loud, not skipped: a Bahn whose Fassung this machine does not know
            # cannot be filed anywhere, and a silent skip is the exact failure
            # this chain exists to prevent.
            homeless.append(where)
            continue
        declared = _declared_format(answer, where)
        held = pfade_of(record)
        held_format = (record.get("pfade") or {}).get("pfad_format")
        answered = {entry["box_index"] for entry in authored}
        retained = [entry for entry in held if entry["box_index"] not in answered]
        if retained and held_format is not None and held_format != declared:
            clashes.append(
                f"{where} (box {', '.join(str(entry['box_index']) for entry in retained)}, "
                f"held under Streifen-Pfad format {held_format}, the API answers {declared})"
            )
            continue
        # Said on every run, not only when something changed: „the server no
        # longer answers here" is a standing fact about the last copy, and the
        # run that reports it is the one before the next snapshot.
        retained_boxes += [f"{where} box {entry['box_index']}" for entry in retained]
        merged = sorted([*authored, *retained], key=lambda entry: entry["box_index"])
        if held == merged and held_format == declared:
            unchanged += len(merged)
            continue
        record["pfade"] = pfad_record(merged, declared, today)
        bahnen += len(authored)
        fassungen += 1

    if fassungen:
        save_kartei(hand, kartei)
    print(
        f"{hand}: {bahnen} hand-drawn Bahn(en) in {fassungen} Fassung(en) pulled into the Kartei, "
        f"{unchanged} already there"
    )
    if retained_boxes:
        # The give-up signal: the server no longer answers with a drawing this
        # machine holds, so the Kartei is now its only copy anywhere.
        print(
            f"kept (the server no longer holds a drawing there — this Kartei is the last copy): "
            f"{', '.join(retained_boxes)}"
        )
    if fassungen:
        print(
            f"reminder: snapshot so the archive carries them — uv run python -m tools.eigenhand.snapshot --hand {hand}"
        )
    stop: list[str] = []
    if homeless:
        stop.append(
            f"{len(homeless)} Fassung(en) carry a hand-drawn Bahn this machine does not know: "
            f"{', '.join(homeless)}\nEverything else was written; these Bahnen are NOT archived. Their Kartei "
            "rows are missing here — restore this hand's data root first (`sync --from <snapshot>` is the "
            "other direction) or run this on the machine that holds it."
        )
    if clashes:
        stop.append(
            f"{len(clashes)} Fassung(en) hold boxes the API no longer answers for, under an OLDER "
            f"Streifen-Pfad format: {', '.join(clashes)}\nThey were left untouched, so nothing is lost — but "
            "one record declares one format, and carrying those entries under the new one would mislabel "
            "them. Archive this Kartei as it is, then decide per box whether the old drawing is still wanted."
        )
    if stop:
        raise SystemExit("\n\n".join(stop))
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
    ap.add_argument(
        "--pfade",
        action="store_true",
        help="fetch the hand-drawn Bahnen (`verfahren: authored`) into the Kartei, so a snapshot carries them",
    )
    ap.add_argument("--api", default=None, help="API base URL (default: $EIGENHAND_API or production)")
    ap.add_argument("--token", default=None, help="admin token (default: $ADMIN_TOKEN)")
    args = ap.parse_args(argv)

    chosen = [bool(args.sheet), args.flecken, args.pfade]
    if sum(chosen) != 1:
        ap.error("give exactly one of --sheet <B…>, --flecken or --pfade")

    hand = check_hand_id(args.hand)
    token = admin_token(args.token)
    base = api_base(args.api)
    if args.flecken:
        return pull_flecken(hand, base, token)
    if args.pfade:
        return pull_pfade(hand, base, token)
    return pull_sheet(hand, check_sheet_id(args.sheet), base, token)


if __name__ == "__main__":
    raise SystemExit(main())
