"""Push the local Kartei to the API — the bookkeeping always, the strips on request.

The judging happens locally (the strips are there); this is what makes the
result visible in the admin view. Three pushes, in this order:

1. every Bogen printed locally, registered with its layout — so the server
   stops handing out an id the paper on the desk already carries;
2. every judged row as a Fassung: strip, sheet, row index, verdict, reason, the
   effective nib/ink/paper, the local file's SHA256, the Streifen-Befund and
   the Fleckenmaske. No scan, no pixels;
3. with ``--mit-streifen``, the strip images of the accepted Fassungen.

The Fleckenmaske is the one field with a DIRECTION: it goes up for a new row
and to fill a row that has none, never over an existing one. The author erases
specks in the workbench, so once a mask is there the server's copy is the
master — `tools.eigenhand.pull --flecken` is what brings it back down here.

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

RESTORING after a DB loss reads the same push out of the archive instead of the
working data root — repo + archive is the guarantee, and this is the path that
redeems it (`docs/proposals/eigenhand-erfassung.md` §8.1):

    ADMIN_TOKEN=… uv run python -m tools.eigenhand.sync --hand mn-suetterlin \
        --from ~/kurrentschrift-archive/own-hand/mn-suetterlin/2026-08-24-1830 \
        --mit-streifen

Name any snapshot: the archive is read as one LAYERED tree, that snapshot plus
its siblings, newest first. It has to be — `snapshot.py` files incrementally, so
only the first snapshot is ever self-contained while every later one carries a
complete Kartei beside just its increment. Reading one directory would restore
one increment and call it done. The Kartei itself is always taken from the
NEWEST snapshot of the hand, whichever one is named, and the run says so.

The restore is also the only path that pushes the HAND-DRAWN Bahnen back
(`verfahren: authored`, pulled into the Kartei by `pull --pfade`). A followed
path stays out — strip, layout and follower are all here, so it is made again
rather than restored. A drawing is not: nothing can follow it a second time, so
the run ends LOUDLY naming how many are still missing whenever the chain did
not close (proposal §7.5/§8.1). It fills only the boxes the server has no path
for; a box that already carries one is left exactly as it is and named.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import NamedTuple

from core.eigenhand.flecken import FLECKEN_FORMAT
from core.eigenhand.pfad import push_body
from tools.eigenhand.apiclient import admin_token, api_base, request_json
from tools.eigenhand.kartei import load_kartei, pfad_wire_format, pfade_of
from tools.eigenhand.store import WORK_DPI, check_hand_id, hand_dir, sheet_dir


def _source(hand: str, snapshot: Path | None) -> "tuple[dict, _Layers]":
    """The Kartei and the roots its Fassung/Bogen paths hang off.

    Two shapes, one reader. The working data root is
    ``<dataroot>/<hand>/``; an archive snapshot is
    ``own-hand/<hand>/<stamp>/`` with the same ``fassungen/`` and
    ``blaetter/`` layout beneath it (`tools/eigenhand/snapshot.py`). Making
    them interchangeable here is what keeps the restore path from being a
    second, untested implementation of the sync.

    The archive is read as a LAYERED whole, newest snapshot first, not as one
    directory. `snapshot.py` files INCREMENTALLY — a unit present in any
    earlier snapshot is skipped — so only the very first snapshot is ever
    self-contained; every later one holds just its increment, while its
    `kartei.json` still lists every Bogen and Fassung the hand has. Reading a
    single directory would therefore restore one increment and report success
    (found in review, PR #410). Pointing `--from` at any snapshot picks up its
    siblings automatically: the archive as a whole is the master, not any one
    stamp.

    The KARTEI is the one file where the newest layer wins outright rather than
    the named one. Every snapshot carries a complete Kartei by construction
    (`snapshot.py`), so an older one is a complete record of an EARLIER state —
    and reading it would silently restore that earlier state while the file
    layers around it stayed current. For the bookkeeping that only loses a
    verdict the next `sync` re-pushes; for a hand-drawn Bahn, which since this
    chain rides in the Kartei and nowhere else, it would drop a drawing nothing
    can make again and still report a clean run (found in review, PR #634).
    """
    if snapshot is None:
        return load_kartei(hand), _Layers([hand_dir(hand)])
    root = snapshot.expanduser().resolve()
    kartei_file = root / "kartei.json"
    if not kartei_file.exists():
        raise SystemExit(f"{kartei_file} missing — point --from at a snapshot directory, not at its parent")
    named = json.loads(kartei_file.read_text(encoding="utf-8"))
    if named.get("hand") != hand:
        raise SystemExit(f"snapshot holds hand {named.get('hand')!r}, not {hand!r} — refusing to push it as {hand}")
    layers = _snapshot_layers(root)
    newest = max(layers, key=lambda candidate: candidate.name)
    if newest == root:
        return named, _Layers(layers)
    print(f"Kartei read from {newest.name} — the newest snapshot of this hand; {root.name} was the one named")
    return json.loads((newest / "kartei.json").read_text(encoding="utf-8")), _Layers(layers)


def _snapshot_layers(snapshot: Path) -> "list[Path]":
    """The named snapshot plus its siblings in the same hand archive, newest first.

    A sibling counts only if it looks like a snapshot of the same hand (it has
    a `kartei.json` naming it), so pointing at a directory that merely happens
    to sit next to unrelated data cannot widen the read.
    """
    named = json.loads((snapshot / "kartei.json").read_text(encoding="utf-8")).get("hand")
    siblings = []
    for candidate in snapshot.parent.iterdir() if snapshot.parent.is_dir() else ():
        if candidate == snapshot or not candidate.is_dir():
            continue
        kartei = candidate / "kartei.json"
        if not kartei.is_file():
            continue
        try:
            if json.loads(kartei.read_text(encoding="utf-8")).get("hand") == named:
                siblings.append(candidate)
        except json.JSONDecodeError:
            continue
    # Stamps sort chronologically by name; newest first so the freshest copy of
    # a file wins, and the named snapshot leads regardless of where it sorts.
    return [snapshot, *sorted(siblings, key=lambda p: p.name, reverse=True)]


class _Layers:
    """An ordered stack of roots read as one tree — first hit wins."""

    def __init__(self, roots: "list[Path]"):
        self.roots = roots

    def find(self, *parts: str) -> Path | None:
        for root in self.roots:
            candidate = root.joinpath(*parts)
            if candidate.exists():
                return candidate
        return None

    def __str__(self) -> str:
        head = self.roots[0]
        return f"{head}" + (f" (+{len(self.roots) - 1} earlier snapshot(s))" if len(self.roots) > 1 else "")


def _layout_file(layers: _Layers, hand: str, sheet_id: str, snapshot: bool) -> Path | None:
    if not snapshot:
        found = sheet_dir(hand, sheet_id) / "layout.json"
        return found if found.exists() else None
    return layers.find("blaetter", sheet_id, "layout.json")


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
            # The Streifen-Befund's measurement, as `apply` read it off the
            # crop. Numbers, never pixels — the suggestion and the rank are
            # derived on the server exactly as they are in the terminal.
            "befund": f.get("befund"),
            # The Fleckenmaske, and only ever DOWNHILL of the server: the API
            # takes it for a new row and to fill a row that has none, never
            # over one that already carries a mask. The author's brush lives in
            # the workbench, so once a mask exists the server's copy is the
            # master and `pull --flecken` is the way back.
            #
            # Passed through as it is, an EMPTY list included: `[]` means
            # „looked, nothing to erase" — the state `pull --flecken` writes
            # once the author has removed every circle — and collapsing it to
            # `null` would restore it as „nobody has looked" and leave the
            # cleared master overwritable again (Copilot review, PR #568).
            "flecken": f.get("flecken"),
            "flecken_format": FLECKEN_FORMAT if f.get("flecken") is not None else None,
            # The effective setup of THIS row, as the Siebung recorded it.
            **{key: (f.get("session") or {}).get(key) or None for key in ("feder", "tinte", "papier", "geraet")},
        }
        for strip, record in sorted(kartei["strips"].items())
        for f in record.get("fassungen", [])
    ]


def _push_strips(
    base: str, token: str, hand: str, layers: _Layers, kartei: dict, sendable: set[str]
) -> tuple[int, int]:
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
            png_file = layers.find("fassungen", strip, f["id"], "streifen.png")
            meta_file = layers.find("fassungen", strip, f["id"], "meta.json")
            if png_file is None or meta_file is None:
                absent = [n for n, p in (("streifen.png", png_file), ("meta.json", meta_file)) if p is None]
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
                    # The RECTIFIED image's resolution, not the capture's.
                    # `scan.dpi_estimate` measures the original photo or scan
                    # before warping; what is uploaded is a crop of the
                    # rectified page, which ingest always produces at WORK_DPI
                    # (found in review, PR #410 — a 600-dpi flatbed would
                    # otherwise label a 185 mm strip as 92 mm wide).
                    "dpi": WORK_DPI,
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


def _pfad_rows(kartei: dict) -> list[tuple[str, str, int, list[dict]]]:
    """Every (strip, Fassung, wire format, Bahnen) the Kartei carries a drawing for."""
    rows: list[tuple[str, str, int, list[dict]]] = []
    for strip, record in sorted(kartei.get("strips", {}).items()):
        for fassung in record.get("fassungen", []):
            entries = pfade_of(fassung)
            if entries:
                rows.append((strip, fassung["id"], pfad_wire_format(fassung), entries))
    return rows


class _Restore(NamedTuple):
    """What one restore run did to the hand-drawn Bahnen of a hand."""

    restored: int
    already: int
    kept: int
    stuck: int
    why: list[str]
    left: list[str]


def _came_back(landed: dict | None, sent: dict) -> bool:
    """Whether the server answered with the Bahn it was handed.

    Not dict equality: a format-1 entry restored into a row that has to be
    declared format 2 comes back NORMALISED — `check_paths` fills in `status`,
    `grund`, `detail` and `letter_spans`, which is the format doing its job and
    not a changed Bahn. Equality read that as „stored changed, or not at all"
    and ended an otherwise perfect restore with a loud failure (found in
    review, PR #639).

    So every field that was SENT has to come back carrying the same value, and
    fields the server added beside them are allowed. A changed stroke, a
    dropped registration or a missing box still fails, which is the whole
    question this closing count answers.
    """
    if landed is None:
        return False
    return all(landed.get(key) == value for key, value in sent.items())


def _push_pfade(base: str, token: str, hand: str, kartei: dict) -> _Restore:
    """Put the archived hand-drawn Bahnen back into the boxes that have none.

    The RESTORE path only (`--from`). A hand-drawn Bahn is not bookkeeping this
    machine owns: it is made in the workbench, `pull --pfade` brings a copy
    down, and pushing that copy on every ordinary sync would quietly resurrect
    a drawing the author gave up on purpose with `--replace-authored`.

    A box the server ALREADY answers for is left exactly as it is, even when
    its path differs from the archived one — the same rule `_push_setup`
    follows. The archive is the master for what is missing, never for what is
    live: the differing path is either a drawing the author corrected in the
    workbench after the last `pull`, or a follow he deliberately handed the box
    over to, and overwriting either of them would revert a decision this
    machine knows nothing about (found in review, PR #634). Those boxes are
    counted and named; nothing is lost, the archived copy stays in the Kartei.

    Merged, not replaced: the write is a FULL replacement per Fassung, so the
    boxes that are being filled go up beside everything the server already
    holds. That also means the push can never trip the 409 — a stored
    `authored` box is never one of the boxes this writes.

    And because the body is a MERGE, the declaration cannot simply be the
    archive's: a live box written under a newer format travels up in that same
    push, and declaring the archive's older number over it would be refused
    outright (422) — the restore would die on a row it was not even asked to
    change (found in review, PR #639). So the push declares whichever of the
    two the CONTENT needs. It can only ever go up: a format-1 entry is a valid
    format-2 one, and `check_paths` normalises it, whereas the reverse would be
    the mislabelling the stored marker exists to prevent.

    A Fassung whose strip row is not up there cannot take a path at all (the
    route answers 404). Those are COUNTED and named rather than skipped: a
    drawing nothing can follow again is the one loss this whole chain exists to
    make impossible, so a partial restore has to end loudly.

    The counts are read off the ANSWER, not off the request. This closing line
    is the one number the chain is judged by, so „restored" has to mean the
    server handed the Bahn back, not that it was asked to take it.
    """
    restored = already = kept = stuck = 0
    why: list[str] = []
    left: list[str] = []
    for strip, fassung, wire_format, entries in _pfad_rows(kartei):
        url = f"{base}/eigenhand/strips/{hand}/{strip}/{fassung}/pfade"
        answer = request_json("GET", url, token, allow_404=True)
        if answer is None:
            stuck += len(entries)
            why.append(
                f"{strip}/{fassung}: no stored strip row up there — its image was never pushed "
                "(--mit-streifen), or its Bogen was held back for a missing layout (named above)"
            )
            continue
        stored = answer.get("pfade") or []
        by_box = {entry.get("box_index"): entry for entry in stored}
        fresh: list[dict] = []
        for entry in entries:
            live = by_box.get(entry["box_index"])
            if live is None:
                fresh.append(entry)
            elif live == entry:
                already += 1
            else:
                kept += 1
                left.append(f"{strip}/{fassung} box {entry['box_index']}")
        if not fresh:
            continue
        mine = {entry["box_index"] for entry in fresh}
        body = sorted(
            [*fresh, *(entry for entry in stored if entry.get("box_index") not in mine)],
            key=lambda item: item["box_index"],
        )
        body, content_format, _dropped = push_body(body)
        echo = request_json("PUT", url, token, {"format": max(wire_format, content_format), "pfade": body}) or {}
        landed = {entry.get("box_index"): entry for entry in (echo.get("pfade") or [])}
        for entry in fresh:
            if _came_back(landed.get(entry["box_index"]), entry):
                restored += 1
            else:
                stuck += 1
                why.append(
                    f"{strip}/{fassung} box {entry['box_index']}: the server did not answer with the Bahn "
                    "it was sent — it was stored changed, or not at all"
                )
    return _Restore(restored, already, kept, stuck, why, left)


def _push_setup(base: str, token: str, hand: str, layers: _Layers) -> bool:
    """Restore the hand's standing setup when the server has none.

    `eigenhand_hands` is the fourth own-hand table, and the restore recipe
    claims all four come back — but nothing carried it: `setup.json` is a local
    cache, not something the sync ever pushed (found in review, PR #410).

    Only when the server has NOTHING: this is a restore, not a sync of the
    setup. Pushing a cached copy over a live record would let a stale machine
    silently overwrite a nib the author changed somewhere else — and the record
    on the server is the master for this one, not the cache.
    """
    setup_file = layers.find("setup.json")
    if setup_file is None:
        return False
    if request_json("GET", f"{base}/eigenhand/setups/{hand}", token, allow_404=True) is not None:
        return False
    cached = json.loads(setup_file.read_text(encoding="utf-8"))
    body = {key: cached.get(key) for key in ("style", "label", "feder", "tinte", "papier", "geraet", "note")}
    request_json("PUT", f"{base}/eigenhand/setups/{hand}", token, body)
    return True


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
    kartei, layers = _source(hand, args.snapshot)
    base = api_base(args.api)
    fassungen = _fassung_rows(kartei)

    if args.dry_run:
        bahnen = sum(len(entries) for *_head, entries in _pfad_rows(kartei)) if args.snapshot else 0
        print(
            f"would push {len(kartei['sheets'])} Bögen and {len(fassungen)} Fassungen for {hand} to {base}"
            + (" (with strip images)" if args.with_strips else "")
            + (f", {bahnen} hand-drawn Bahn(en)" if bahnen else "")
            + (f" from {layers}" if args.snapshot else "")
        )
        return 0
    token = admin_token(args.token)

    imported = 0
    missing_layouts: list[str] = []
    known: set[str] = set()
    for sheet_id, sheet in sorted(kartei["sheets"].items()):
        # The layout is the geometry contract; without it the server would hold
        # a Bogen it could neither re-render nor hand back to an ingest run.
        layout_file = _layout_file(layers, hand, sheet_id, args.snapshot is not None)
        if layout_file is None:
            missing_layouts.append(sheet_id)
            print(f"skip {sheet_id}: no layout.json {'in the archive' if args.snapshot else 'on this machine'}")
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
        + (f", {pushed['flecken_filled']} Fleckenmasken filled in" if pushed.get("flecken_filled") else "")
        + (f", {held} held back (Bogen not registered)" if held else "")
    )
    if _push_setup(base, token, hand, layers):
        line += ", standing setup restored"
    if args.with_strips:
        sent, skipped = _push_strips(base, token, hand, layers, kartei, known)
        line += f", {sent} strips uploaded, {skipped} already stored"
    print(line)

    incomplete: list[str] = []
    if args.snapshot and missing_layouts:
        # On the restore path the archive is supposed to be complete, so a
        # Bogen the Kartei lists but the archive cannot describe means the run
        # did NOT bring the hand back whole — and the verdicts of those sheets
        # were held back above. Locally the same gap is only a warning: a sheet
        # can legitimately be waiting for its `pull`.
        incomplete.append(
            f"{len(missing_layouts)} Bogen(s) in the Kartei have no layout.json in the archive: "
            f"{', '.join(missing_layouts)}\nTheir verdicts and strips were held back — the restore is "
            "INCOMPLETE. Check that --from points into the hand's archive tree and that the snapshots "
            "around it are present."
        )
    if args.snapshot:
        bahnen = _push_pfade(base, token, hand, kartei)
        if bahnen.restored or bahnen.already or bahnen.kept or bahnen.stuck:
            print(
                f"hand-drawn Bahnen: {bahnen.restored} restored, {bahnen.already} already there"
                + (f", {bahnen.kept} left as the server has them" if bahnen.kept else "")
                + f", {bahnen.stuck} NOT restored"
            )
            if bahnen.left:
                print(
                    "  left alone (the server holds another path there — the archived copy stays in the "
                    f"Kartei): {', '.join(bahnen.left)}"
                )
        else:
            # Said out loud rather than left as silence: the archive carrying
            # no drawing and the hand never having had one look identical from
            # here, and only one of them is fine.
            print(
                "hand-drawn Bahnen: none in this archive — if this hand has one, `pull --pfade` "
                "never ran before the last snapshot"
            )
        if bahnen.stuck:
            incomplete.append(
                f"{bahnen.stuck} hand-drawn Bahn(en) are NOT restored: {'; '.join(bahnen.why)}\n"
                "Nothing can follow a hand-drawn Bahn again, so this is not a gap that closes itself — "
                "close the gap named above and run this again."
            )
    if incomplete:
        raise SystemExit("\n\n".join(incomplete))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
