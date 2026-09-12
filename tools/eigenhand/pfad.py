"""Follow the pen path of a written Streifen and push it into the workbench.

The author asked to see the PATH in the admin — for the harvested words and
for his own hand's strips (2026-09-12). For a word the path is already stored
(``word_instances.strokes``); for a strip nothing about it existed, and the
server can never compute one: the API image does not ship ``tools``, and the
Tintenfolger lives here. So this is the local half — follow the ink, then push
the result through the admin-gated ``PUT /eigenhand/strips/…/pfade``.

    # look first, write nothing (the DEFAULT)
    uv run python -m tools.eigenhand.pfad --hand mn-suetterlin --strip S0001

    # the same run, stored in the shared DB
    ADMIN_TOKEN=… uv run python -m tools.eigenhand.pfad --hand mn-suetterlin --strip S0001 --apply

DRY RUN BY DEFAULT, like ``tools.wordbench.shift_registrations``: every write
lands in the SHARED Cloud SQL database, so ``--apply`` is a deliberate act and
an archive snapshot (``/dbsnapshot``) belongs in front of it.

WHAT IT READS. Everything over the admin API, nothing off a local scan: the
strip listing (geometry, words, box rectangles), the Bogen layout (the printed
ruling) and the strip PNG itself — served with the Fleckenmaske applied and,
for a colour strip, without its cyan rulings, so the follower reads the hand's
ink and not the printer's. The ductus SEED comes from the frozen word fixtures
of the style: the chart's stroke order and direction, which is what the
Tintenpfad needs a prior for. It is a seed and not a claim about this hand,
and the workbench says so beside every drawn path.

WHAT IT WRITES. One entry per word box: the strokes in the word's own units
(baseline 0, midband 1 — the frame ``word_instances.strokes`` uses), the
registration in the STRIP's pixels, the Verfahren, the configuration and the
day. The strip's own bytes are never touched; the path is data beside them
(``core.eigenhand.pfad``, proposal §7.5).

THE CONFIGURATION is the one the campaign settled on for the reversal corners
(messjournal §14, rounds of 10–11 September): ``tip_read`` · ``rail=tentfit``
· ``edt_upsample=4`` · ``ink_bridge_xh=1.0`` · ``hairpin_tip`` · ``ride_back``
· ``tip_grey_stop`` · ``self_jump``. It travels INTO the stored row, so a path
says out of itself what produced it.
"""

from __future__ import annotations

import os


# Before numpy is pulled in anywhere below: the chain solve is not
# bit-reproducible across thread environments, so a followed path would differ
# between two machines for no reason a reader could see (CLAUDE.md, the BLAS
# rule of 2026-08-16). Defaults only — an operator who exports otherwise is
# taken at their word.
for _var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import argparse  # noqa: E402
import json  # noqa: E402
from datetime import date as date_cls  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402
from urllib.parse import quote  # noqa: E402

import numpy as np  # noqa: E402

from core.eigenhand.ids import style_of_hand  # noqa: E402
from core.eigenhand.pfad import PFAD_FORMAT, frame_for_box  # noqa: E402
from core.eigenhand.plan import load_plan, shaping_form_of  # noqa: E402
from tools.eigenhand.apiclient import admin_token, api_base, request_bytes, request_json  # noqa: E402
from tools.eigenhand.store import check_hand_id, hand_dir  # noqa: E402


# The settled arms, spelled out so the run is readable without opening the
# follower. Kept as a dict rather than a constructed dataclass so importing
# this module costs nothing: `tools.pairlab.tintenpfad` pulls in the whole
# solver stack, and the dry run should fail on a missing fixture root before
# that happens.
KONFIGURATION: dict[str, Any] = {
    "tip_read": True,
    "rail": "tentfit",
    "edt_upsample": 4,
    "ink_bridge_xh": 1.0,
    "hairpin_tip": True,
    "ride_back": True,
    "tip_grey_stop": True,
    "self_jump": True,
}

VERFAHREN = "tintenpfad"


def _strip_rows(base: str, token: str, hand: str, strip: str, fassung: str | None) -> list[dict]:
    """The stored Fassungen of one strip — refused loudly where there are none."""
    listing = request_json("GET", f"{base}/eigenhand/strips/{hand}?strip={quote(strip)}", token) or {}
    rows = [row for row in listing.get("strips", []) if fassung is None or row["fassung"] == fassung]
    if not rows:
        which = f"{strip}/{fassung}" if fassung else strip
        raise SystemExit(
            f"{hand} has no stored strip {which} — a path is followed on the ink, so push the image first: "
            f"uv run python -m tools.eigenhand.sync --hand {hand} --mit-streifen"
        )
    return rows


def _strip_plane(base: str, token: str, hand: str, row: dict) -> np.ndarray:
    """The strip as the plane a reading runs on — masked, and without rulings.

    The Fleckenmaske is applied by the server (the default), and a colour strip
    comes back as its blue plane with the cyan rulings lifted to paper: a
    ruling read as ink would put a straight line through every word.
    """
    from core.eigenhand.crop import working_plane

    url = f"{base}/eigenhand/strips/{hand}/{row['strip']}/{row['fassung']}?lineatur=ohne"
    return working_plane(request_bytes("GET", url, token))


def _fixture_prior(style: str) -> dict[str, Any]:
    """The chart ductus the follower seeds with — off the frozen word fixtures.

    The roots are gitignored, so this is the one failure an operator will
    actually hit on a fresh machine; it names the command that fixes it rather
    than raising a traceback out of a missing file.
    """
    from tools.wordlab.cases import fixture_root_for

    rebuild = (
        "the ductus seed comes from the frozen word fixtures, and those roots are gitignored. Rebuild:\n"
        "  uv sync --all-extras\n"
        "  uv run python -m tools.wordbench.fetch_fixtures --set all --verify"
    )
    # `fixture_root_for` raises KeyError where the style has no root at all and
    # hands back a directory that may still be empty — both are the same
    # situation for an operator, and both have to name the command.
    try:
        root = fixture_root_for(which="words", style=style)
    except KeyError as exc:
        raise SystemExit(f"no word fixtures for {style}: {exc} — {rebuild}") from exc
    manifest = root / "manifest.json"
    if not manifest.exists():
        raise SystemExit(f"no frozen word fixtures for {style} under {root} — {rebuild}")
    laufform = root / "templates_laufform.json"
    return {
        "root": root,
        "manifest": json.loads(manifest.read_text()),
        "templates": json.loads((root / "templates.json").read_text()),
        "laufform": json.loads(laufform.read_text()) if laufform.exists() else {},
    }


def _case_for_box(prior: dict, plane: np.ndarray, frame: dict, word: str, form: str, case_id: str):
    """One word box of a strip as a `WordCase` — the seam to the follower.

    The specimen half is cut out here rather than loaded from a fixture: crop,
    binarised mask, skeleton and half-width map, the same four the bench
    freezes (`tools.wordbench.export_fixtures`) and through the same entry
    points, so a strip is read exactly as a plate crop is.

    The lineature is the Bogen's PRINTED ruling. That is a seed for the
    registration the fit then refines, never a measurement of where the hand
    actually wrote — see `core.eigenhand.pfad`.
    """
    from core.extract import binarize_adaptive, skeleton_and_width
    from core.shaping import glyph_keys_of, shape_text
    from core.word_metric import despeckle
    from tools.wordlab.cases import WordCase

    x0, y0, x1, y1 = frame["rect_px"]
    crop = np.ascontiguousarray(plane[y0:y1, x0:x1], dtype=np.float64)
    mask = despeckle(binarize_adaptive(crop))
    skel, width_map = skeleton_and_width(mask)
    slots = shape_text(form)
    keys = glyph_keys_of(slots)
    missing = [key for key in keys if key not in prior["templates"]]
    manifest = prior["manifest"]
    return (
        WordCase(
            id=case_id,
            word=word,
            kind="word",
            slots=slots,
            templates=prior["templates"],
            laufform=prior["laufform"],
            style_ratio=manifest.get("style_ratio") or [1, 1, 1],
            width_resolver=manifest.get("width_resolver") or "pressure",
            nib_units=manifest.get("constant_nib_units"),
            origin=f"eigenhand:{prior['root'].name}",
            scorable=not missing,
            rect=[x0, y0, x1, y1],
            baseline_y=int(round(frame["baseline_row"])),
            midband_y=int(round(frame["waist_row"])),
            crop=crop,
            skel=skel,
            width_map=width_map,
            mask=mask,
        ),
        missing,
    )


def _entry(info: dict, frame: dict, flecken_n: int | None, today: str) -> dict:
    """One followed word as the row the API stores.

    The follower registers against the CROP it was handed; the stored frame is
    the STRIP's, so the crop's own origin is added back. One stored frame
    serves both views — the whole strip and any word cut out of it — and the
    crop's padding never has to be remembered along with the path.
    """
    reg = info["registration_px"]
    x0, y0 = frame["rect_px"][0], frame["rect_px"][1]
    return {
        "box_index": frame["index"],
        "word": frame["word"],
        "strokes": info["strokes"],
        "registration_px": {
            "tx": round(float(reg["tx"]) + x0, 2),
            "ty": round(float(reg.get("ty", 0.0)), 2),
            "baseline_row": round(float(reg["baseline_row"]) + y0, 2),
        },
        "xh_px": float(info["xh_px"]),
        "verfahren": VERFAHREN,
        "konfiguration": dict(KONFIGURATION),
        "meta": {
            "letter_spans": info.get("meta", {}).get("letter_spans"),
            "tintenpfad": {
                key: info.get("meta", {}).get("tintenpfad", {}).get(key)
                for key in ("runs", "strands", "jumps", "hairpins", "paper_lifts", "ink_unvisited_share")
            },
        },
        "erzeugt_am": today,
        "flecken_n": flecken_n,
    }


def follow_row(base: str, token: str, hand: str, row: dict, prior: dict, boxes: list[int] | None) -> list[dict]:
    """Follow every asked-for word of one Fassung. One bad word is not a bad row."""
    from tools.pairlab.follow import STATUS_OK
    from tools.pairlab.tintenpfad import TintenpfadWeights, follow_case

    plan = load_plan()
    layout = request_json("GET", f"{base}/eigenhand/sheets/{hand}/{row['sheet']}/layout", token) or {}
    layout_row = (layout.get("rows") or [])[row["row_index"]]
    plane = _strip_plane(base, token, hand, row)
    weights = TintenpfadWeights(**KONFIGURATION)
    flecken_n = len(row["flecken"]) if row.get("flecken") is not None else None
    today = date_cls.today().isoformat()

    entries: list[dict] = []
    for box in row.get("boxes", []):
        index = box["index"]
        if boxes is not None and index not in boxes:
            continue
        frame = frame_for_box(layout_row, row["crop_origin_mm"], row["width_px"], row["height_px"], index)
        case_id = f"{row['strip']}/{row['fassung']}#{index}"
        case, missing = _case_for_box(prior, plane, frame, box["word"], shaping_form_of(plan, box["word"]), case_id)
        if missing:
            print(f"  {case_id:<18} skipped   unauthored: {' '.join(missing)}", flush=True)
            continue
        info = follow_case(case, weights)
        if info["status"] != STATUS_OK:
            print(f"  {case_id:<18} {info['status']:<9} {info['detail']}", flush=True)
            continue
        entry = _entry(info, frame, flecken_n, today)
        diag = info.get("meta", {}).get("tintenpfad", {})
        print(
            f"  {case_id:<18} ok        {box['word']:<14} {len(entry['strokes']):2d} Züge · "
            f"{diag.get('paper_lifts', 0)} Absetzer · unvisited {diag.get('ink_unvisited_share', 0):.2f}",
            flush=True,
        )
        entries.append(entry)
    return entries


def _local_path(hand: str, strip: str, fassung: str) -> Path:
    """Where a dry run files its result — under the gitignored own-hand root."""
    return hand_dir(hand) / "pfade" / f"{strip}-{fassung}.json"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True, help="hand id, e.g. mn-suetterlin")
    ap.add_argument("--strip", required=True, help="strip id, e.g. S0001")
    ap.add_argument("--fassung", default=None, help="one Fassung (default: every stored one of this strip)")
    ap.add_argument("--box", type=int, action="append", default=None, help="only this word box (repeatable)")
    ap.add_argument("--api", default=None, help="API base URL (default: $EIGENHAND_API or production)")
    ap.add_argument("--token", default=None, help="admin token (default: $ADMIN_TOKEN)")
    ap.add_argument("--out", type=Path, default=None, help="where a dry run files its JSON")
    ap.add_argument(
        "--apply",
        action="store_true",
        help="store the followed paths in the SHARED database (takes a dbsnapshot first — see /dbsnapshot)",
    )
    args = ap.parse_args(argv)

    hand = check_hand_id(args.hand)
    style = style_of_hand(hand) or ""
    base = api_base(args.api)
    token = admin_token(args.token)
    prior = _fixture_prior(style)

    written = 0
    for row in _strip_rows(base, token, hand, args.strip, args.fassung):
        print(f"{row['strip']}/{row['fassung']} ({row['sheet']} row {row['row_index']}):", flush=True)
        entries = follow_row(base, token, hand, row, prior, args.box)
        if not args.apply:
            out = args.out or _local_path(hand, row["strip"], row["fassung"])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"format": PFAD_FORMAT, "pfade": entries}, ensure_ascii=False, indent=1) + "\n")
            print(f"  dry run — {len(entries)} path(s) written to {out}, nothing stored", flush=True)
            continue
        url = f"{base}/eigenhand/strips/{hand}/{row['strip']}/{row['fassung']}/pfade"
        stored = request_json("PUT", url, token, {"format": PFAD_FORMAT, "pfade": entries}) or {}
        written += len(stored.get("pfade") or [])
        print(f"  stored {len(stored.get('pfade') or [])} path(s) at {base}", flush=True)
    if args.apply:
        print(f'{written} path(s) in the shared database — the workbench shows them under "Pfad zeigen"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
