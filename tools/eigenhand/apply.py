"""File the Siebung result: accepted and rejected rows become Fassungen.

Reads the uid-keyed result text the page produced, joins rows via uid (never
via order), and files one Fassung per judged row under
``<dataroot>/<hand>/fassungen/<strip>/<Fxx>/``:

* ``streifen.png`` — the unmodified grayscale row crop from the rectified
  scan (two-channel doctrine: no binarisation baked in)
* ``meta.json``   — words, geometry, verdict, QC flags, Schreibsitzung,
  scan checksum, provenance

Only ACCEPTED rows get files — "only the relevant strips are filed"
(owner decision 2026-08-22). A rejected row is recorded in the
Kartei only (verdict + reason + QC flags, no pixels), which keeps the
Sieb-Disziplin auditable by counts without hoarding discarded ink. Rows
judged ``spaeter`` stay open for a later apply of an updated result.

Idempotent: a row whose Fassung already exists (same sheet + row index) is
skipped when the verdict matches and refused when it conflicts; an existing
Fassung directory is never overwritten. Only local files are written — the
house ``--apply`` gate is for DB writes, which this tool has none of.

    uv run python -m tools.eigenhand.apply --hand mn-suetterlin --sheet B0001 siebung-B0001.txt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from tools.eigenhand.kartei import load_kartei, next_fassung_id, save_kartei
from tools.eigenhand.store import check_crop_name, hand_dir


META_FORMAT = 1
_RESULT_LINE = re.compile(
    r"^(?P<uid>[A-Za-z0-9-]+):(?P<verdict>angenommen|verworfen|spaeter)"
    r"(?:#(?P<reason>[^\s\"]+))?(?:\s+\"(?P<note>.*)\")?$"
)


def parse_result(text: str, sheet: str) -> dict[str, dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or not lines[0].startswith("SIEBUNG/1 "):
        raise SystemExit("result file does not start with a SIEBUNG/1 header line")
    header = lines[0]
    match = re.search(r"bogen=(\S+)", header)
    if not match or match.group(1) != sheet:
        raise SystemExit(f"result header names sheet {match.group(1) if match else '?'} — expected {sheet}")
    verdicts: dict[str, dict] = {}
    for line in lines[1:]:
        parsed = _RESULT_LINE.match(line)
        if not parsed:
            raise SystemExit(f"unparseable result line: {line!r}")
        uid = parsed.group("uid")
        if uid in verdicts:
            raise SystemExit(f"duplicate uid in result: {uid}")
        verdicts[uid] = {
            "verdict": parsed.group("verdict"),
            "reason": parsed.group("reason"),
            "note": parsed.group("note") or "",
        }
    return verdicts


def _existing_fassung(kartei: dict, strip: str, sheet: str, row_index: int) -> dict | None:
    for fassung in kartei["strips"].get(strip, {}).get("fassungen", []):
        if fassung["sheet"] == sheet and fassung["row_index"] == row_index:
            return fassung
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("result", type=Path, help="the downloaded siebung-<sheet>.txt")
    ap.add_argument("--hand", required=True)
    ap.add_argument("--sheet", required=True)
    args = ap.parse_args(argv)

    sheet_dir = hand_dir(args.hand) / "blaetter" / args.sheet
    payload = json.loads((sheet_dir / "import" / "payload.json").read_text(encoding="utf-8"))
    layout = json.loads((sheet_dir / "layout.json").read_text(encoding="utf-8"))
    verdicts = parse_result(args.result.read_text(encoding="utf-8"), args.sheet)

    # The result file already names its Bogen (parse_result); the payload and
    # the layout have to name the same hand and sheet, or a stale copy would
    # file rows into someone else's dataset without a word of warning.
    for name, document in (("payload", payload), ("layout", layout)):
        if (document.get("hand"), document.get("sheet")) != (args.hand, args.sheet):
            raise SystemExit(
                f"{name}.json is for {document.get('hand')}/{document.get('sheet')}, "
                f"not {args.hand}/{args.sheet} — refusing to file into the wrong hand"
            )

    unknown = set(verdicts) - {row["uid"] for row in payload["rows"]}
    if unknown:
        raise SystemExit(f"result names unknown uids: {', '.join(sorted(unknown))}")
    # Every crop name is turned into a path below. Check them all up front, so
    # a tampered payload fails before a single directory has been created.
    for row in payload["rows"]:
        check_crop_name(row["crop"], row["row_index"])

    kartei = load_kartei(args.hand, payload["style"])
    filed = recorded = skipped = 0
    for row in payload["rows"]:
        judgement = verdicts.get(row["uid"])
        if judgement is None or judgement["verdict"] == "spaeter":
            continue
        strip = row["strip"]
        existing = _existing_fassung(kartei, strip, args.sheet, row["row_index"])
        if existing is not None:
            if existing["status"] != judgement["verdict"]:
                raise SystemExit(
                    f"{row['uid']}: already filed as {existing['status']} ({existing['id']}) — "
                    "conflicting verdict; withdraw explicitly via tools.eigenhand.redo --retire instead"
                )
            skipped += 1
            continue

        fassung_id = next_fassung_id(kartei, strip)
        png_sha256: str | None = None
        accepted = judgement["verdict"] == "angenommen"
        layout_row = layout["rows"][row["row_index"]]
        if accepted:
            # Only accepted rows get files; the meta.json makes the strip
            # attributable on its own, sidecar-free (words, geometry, session).
            fassung_dir = hand_dir(args.hand) / "fassungen" / strip / fassung_id
            if fassung_dir.exists():
                raise SystemExit(f"{fassung_dir} already exists — refusing to overwrite")
            fassung_dir.mkdir(parents=True)
            shutil.copy2(sheet_dir / "import" / row["crop"], fassung_dir / "streifen.png")
            png_sha256 = hashlib.sha256((fassung_dir / "streifen.png").read_bytes()).hexdigest()
            meta = {
                "format": META_FORMAT,
                "hand": args.hand,
                "style": payload["style"],
                "strip": strip,
                "fassung": fassung_id,
                "sheet": args.sheet,
                "row_index": row["row_index"],
                "attempt": row["attempt"],
                "attempts": row["attempts"],
                "words": row["words"],
                "status": judgement["verdict"],
                "reason": judgement["reason"],
                "note": judgement["note"],
                "qc": row["qc"],
                "pen_mark": row.get("pen_mark"),
                "band_mm": layout_row["band_mm"],
                "boxes": layout_row["boxes"],
                "crop_origin_mm": row["crop_origin_mm"],
                "scan": {**payload["scan"], "geraet": payload["session"]["geraet"]},
                "session": payload["session"],
                "png_sha256": png_sha256,
                "provenance": payload["layout_provenance"],
            }
            (fassung_dir / "meta.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
            )

        record = kartei["strips"].setdefault(strip, {"fassungen": []})
        record["fassungen"].append(
            {
                "id": fassung_id,
                "sheet": args.sheet,
                "row_index": row["row_index"],
                "attempt": row["attempt"],
                "attempts": row["attempts"],
                "status": judgement["verdict"],
                "reason": judgement["reason"],
                "note": judgement["note"],
                "png_sha256": png_sha256,
                "filed": payload["session"]["date"],
                "session": payload["session"],
            }
        )
        if accepted:
            kartei["redo"] = [entry for entry in kartei["redo"] if entry["strip"] != strip]
            filed += 1
        else:
            recorded += 1

    scans = kartei["sheets"].setdefault(args.sheet, {"printed": "", "strips": [], "layout_sha256": "", "scans": []})
    if payload["scan"]["file"] not in scans["scans"]:
        scans["scans"].append(payload["scan"]["file"])
    save_kartei(args.hand, kartei)

    open_rows = sum(
        1 for row in payload["rows"] if row["uid"] not in verdicts or verdicts[row["uid"]]["verdict"] == "spaeter"
    )
    print(
        f"filed {filed} accepted Fassungen, recorded {recorded} rejection(s) in the Kartei "
        f"({skipped} already judged, {open_rows} still open)"
    )
    print("reminder: snapshot after the session — uv run python -m tools.eigenhand.snapshot --hand " + args.hand)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
