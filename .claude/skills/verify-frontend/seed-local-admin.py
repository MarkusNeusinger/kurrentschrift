#!/usr/bin/env python
"""Seed a THROWAWAY local admin with a synthetic Eigenhand chain.

Why this exists: `alembic upgrade head` gives a fresh local Postgres the three
styles, the four chart sources and the quiz words — and nothing else. Templates,
bboxes, occurrences, hands and every Eigenhand row are the RESERVED dataset and
are not seeded by any migration, so a freshly migrated local admin opens on
empty views and no admin WRITE flow can be driven in the browser. This script
puts enough synthetic material in front of the Eigenhand view to click it.

Everything it writes is made up: a flat grey rectangle stands in for a scanned
strip, the pen paths are three-point polylines, and the Tintenpfad sensor
numbers are invented and deliberately spread over a good, a middling and a bad
WORD BOX so a chip, a traffic light or a sort order has something to
distinguish. The cycle turns per box and starts one step later per row, so a
single strip already shows all three levels side by side.

Nothing is read from the shared database, from the private archive or from
`data/samples/own-hand/`, and nothing it writes may ever be measured.

It is a SKILL ASSET, not a `tools/` module, on purpose: `tools/` is the
measurement layer and writes no DB (CLAUDE.md), and a `tools/` entry would owe
`docs/reference/werkzeuge.md` a row for something no measurement round ever
runs. It lives beside the manual that explains it — `/verify-frontend` §1b.

Run it only inside the exported throwaway shell of that section:

    uv run python .claude/skills/verify-frontend/seed-local-admin.py

A second helping on the same stack needs a Fassung of its own, because
`uq_eigenhand_fassung` is unique on (hand, strip, fassung):

    … seed-local-admin.py --reseed --fassung F02

Three guards keep this away from real data: any `--api` that is not loopback is
refused before the first request; `--hand` must sit in the reserved `wegwerf-`
namespace, so no real hand can be named; and a hand this run did not write
itself stops it dead — the last one is NOT reachable by `--reseed`, because a
foreign hand is the signature of the shared database rather than of a re-run.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from PIL import Image


# Run by path rather than as a module (`.claude` cannot be a package name), so
# `sys.path[0]` is this skill's directory and `core` is out of reach. Adding the
# repo root keeps the one import that matters: the frame arithmetic behind a
# stored path must not be spelled a second time here.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from core.eigenhand.ids import is_fassung_id, is_hand_id  # noqa: E402
from core.eigenhand.pfad import PFAD_FORMAT, frame_for_box  # noqa: E402


PX_PER_MM = 300.0 / 25.4
LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})

# Deliberately NOT the author's `mn-suetterlin`: the first call this script
# makes is `PUT /eigenhand/setups/<hand>`, which the API documents as a plain
# overwrite, and the body carries only `label`/`feder`/`tinte` — so a run that
# reached production would blank that hand's `papier`, `geraet` and `note`. A
# `wegwerf-` id is a legal hand id (`core/eigenhand/ids.py`) that production
# can never hold, so the collision simply does not exist.
#
# The prefix is ENFORCED, not just defaulted: the foreign-hand guard below
# compares what the API reports against `--hand`, so a `--hand mn-suetterlin`
# would re-label the author's own hand as „mine" and hand `--reseed` the
# overwrite it is meant to refuse. Reserving a namespace closes that door
# without needing to know which ids production holds.
RESERVED_HAND_PREFIX = "wegwerf-"
DEFAULT_HAND = "wegwerf-suetterlin"
DEFAULT_STRIPS = ("S0001", "S0002", "S0003")
DEFAULT_SHEET_DATE = "2026-01-01"
# `uq_eigenhand_fassung` is unique on (hand, strip, fassung), so a second run
# over the same hand needs a Fassung of its own — hence the flag rather than a
# constant. Measured: a re-run on F01 fails with a 500 from that constraint.
DEFAULT_FASSUNG = "F01"

# Invented sensor readings in the shape `tools/eigenhand/pfad.py` writes, spread
# from clean to unusable. A `0.0` and a `None` are in here deliberately: a
# reader that treats them with `||` turns the best row into „not measured" and
# a missing sensor into a zero, which is the bug a Rohzahlen reader is most
# likely to ship.
#
# All EIGHT sensors since Streifen-Pfad format 2, and the spread is aimed at the
# traffic light's provisional bounds (`core.eigenhand.tintentreue.VORLAEUFIG`):
# the rows read „folgt" · „folgt teils" · „folgt nicht", so the throwaway stack
# shows the three steps rather than three shades of grey. Whoever re-calibrates
# those bounds moves these numbers with them — they are a fixture of the light,
# not measurements of anything.
TINTENPFAD_SPREAD: tuple[dict[str, Any], ...] = (
    {
        "runs": 3,
        "strands": 1,
        "jumps": 0,
        "hairpins": 0,
        "paper_lifts": 2,
        "ink_unvisited_share": 0.0,
        "paper_excursion_xh": 0.08,
        "aiou": 0.86,
    },
    {
        "runs": 5,
        "strands": 2,
        "jumps": 1,
        "hairpins": None,
        "paper_lifts": 4,
        "ink_unvisited_share": 0.07,
        "paper_excursion_xh": 0.28,
        "aiou": 0.71,
    },
    {
        "runs": 9,
        "strands": 5,
        "jumps": 4,
        "hairpins": 3,
        "paper_lifts": 8,
        "ink_unvisited_share": 0.31,
        "paper_excursion_xh": 0.62,
        "aiou": 0.41,
    },
)

# One pen-down stretch in template units — baseline 0, midband 1, x from the
# word's own origin, the frame `word_instances.strokes` uses. Seven samples
# rather than three since the strip editor shipped: the letter boundaries index
# SAMPLES, so a three-point line leaves a boundary nowhere to be dragged to and
# the correction surface cannot be driven locally at all.
SYNTHETIC_STROKE = [[0.0, 0.0], [0.25, 0.5], [0.5, 1.0], [0.75, 0.5], [1.0, 0.0], [1.25, 0.5], [1.5, 1.0]]

# How many letters the synthetic boundaries cut that stretch into, at most. The
# slots are made up like everything else here — a real assignment comes from the
# Span-Zuordner (`tools.eigenhand.pfad --spans`), which does not exist yet — and
# they exist so the editor's „Grenzen" mode has something to show and to move.
MAX_SYNTHETIC_SPANS = 3


def synthetic_spans(word: str, samples: int) -> list[dict[str, Any]] | None:
    """Cut one synthetic stroke into `letter_spans`, evenly and without a gap.

    Even cuts, because nothing here means anything: what matters is that the
    spans are ADJACENT (that is what makes a seam draggable), that they stay
    inside the stroke, and that they claim no sample twice — the three things
    `core.eigenhand.pfad.check_paths` refuses on the way in.

    `None` rather than `[]` where there is nothing to cut: a null says the
    boundaries were never assigned, an empty list would say they were assigned
    and came back empty — the same distinction the Fleckenmaske draws.
    """
    slots = max(1, min(MAX_SYNTHETIC_SPANS, len(word)))
    if slots < 2 or samples < slots:
        return None
    size = samples // slots
    spans: list[dict[str, Any]] = []
    for slot in range(slots):
        first = slot * size
        last = samples - 1 if slot == slots - 1 else first + size - 1
        spans.append({"stroke": 0, "slot": slot, "first": first, "last": last, "herkunft": "auto"})
    return spans


class AdminApi:
    """The throwaway admin API over plain urllib — loopback only, by construction."""

    def __init__(self, base: str, token: str) -> None:
        self.base = checked_base(base)
        self.token = token

    def request(
        self, method: str, path: str, body: dict[str, Any] | None = None, *, if_match: str | None = None
    ) -> Any:
        return self.answer(method, path, body, if_match=if_match)[0]

    def answer(
        self, method: str, path: str, body: dict[str, Any] | None = None, *, if_match: str | None = None
    ) -> tuple[Any, str | None]:
        """The parsed body and the answer's `ETag` — a guarded write needs both.

        The Streifen-Pfad routes refuse a write that cannot say which stored
        list it was made on (428) and one that names an older list (412), so a
        seeder that only ever saw bodies could not push a path at all.
        """
        payload = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(f"{self.base}{path}", data=payload, method=method)
        request.add_header("X-Admin-Token", self.token)
        if payload is not None:
            request.add_header("Content-Type", "application/json")
        if if_match is not None:
            request.add_header("If-Match", if_match)
        try:
            # The URL was checked to be loopback in `checked_base`; nothing here
            # can be pointed at a remote host by a flag.
            with urllib.request.urlopen(request) as response:
                raw = response.read()
                etag = response.headers.get("ETag")
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")[:400]
            raise SystemExit(f"{method} {path} → {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise SystemExit(f"{method} {path} → no answer from {self.base}: {error.reason}") from error
        return (json.loads(raw) if raw else None), etag


def checked_base(base: str) -> str:
    """Refuse anything but loopback — the whole point of a throwaway seeder.

    `tools/eigenhand/apiclient.py` defaults to production and this script writes
    where that one would; the two must not be one typo apart.
    """
    parts = urlsplit(base)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise SystemExit(f"--api {base!r} is not an http(s) URL")
    if parts.hostname not in LOOPBACK_HOSTS:
        raise SystemExit(
            f"refusing --api {base!r}: {parts.hostname!r} is not loopback. "
            "This script writes synthetic rows and must never reach a shared database."
        )
    return base.rstrip("/")


def synthetic_png(width_px: int, height_px: int, shade: int = 235) -> bytes:
    """A stand-in for a scanned strip — grayscale, the mode `ingest` files."""
    buffer = io.BytesIO()
    Image.new("L", (width_px, height_px), color=shade).save(buffer, format="PNG")
    return buffer.getvalue()


def strip_geometry(layout_row: dict[str, Any]) -> dict[str, Any]:
    """The crop a local ingest run would cut from this printed row, at 300 DPI.

    The same arithmetic `tools/eigenhand/ingest.py` uses, so the stored width
    and height match what the endpoint re-derives from `crop_origin_mm`.
    """
    x0, y0, x1, y1 = layout_row["cut_mm"]
    return {
        "crop_origin_mm": [round(x0, 3), round(y0, 3)],
        "width_px": int(round(x1 * PX_PER_MM)) - int(round(x0 * PX_PER_MM)),
        "height_px": int(round(y1 * PX_PER_MM)) - int(round(y0 * PX_PER_MM)),
    }


def pfad_entries(layout_row: dict[str, Any], geometry: dict[str, Any], spread_offset: int) -> list[dict[str, Any]]:
    """One synthetic path per word box of this row, with invented sensor numbers."""
    entries: list[dict[str, Any]] = []
    for box_index in range(len(layout_row.get("boxes") or [])):
        frame = frame_for_box(
            layout_row, geometry["crop_origin_mm"], geometry["width_px"], geometry["height_px"], box_index
        )
        tintenpfad = TINTENPFAD_SPREAD[(spread_offset + box_index) % len(TINTENPFAD_SPREAD)]
        entries.append(
            {
                "box_index": box_index,
                "word": frame["word"],
                "strokes": [SYNTHETIC_STROKE],
                "registration_px": {
                    "tx": float(frame["rect_px"][0]),
                    "ty": 0.0,
                    "baseline_row": float(frame["baseline_row"]),
                },
                "xh_px": float(frame["xh_px"]),
                "verfahren": "tintenpfad",
                "konfiguration": {"source": "seed-local-admin", "synthetic": True},
                # The CHECKED field of format 2 — invented like everything else
                # here, and the only way the editor's boundary correction can be
                # driven on a throwaway stack at all (the real assignment comes
                # from the Span-Zuordner, which is not built yet).
                "letter_spans": synthetic_spans(frame["word"], len(SYNTHETIC_STROKE)),
                # A null `letter_spans` in the free `meta` on purpose: format 2
                # keeps the boundaries in a checked field of the entry and
                # refuses a copy here, but a NULL is legitimate and is what a
                # row written by the pre-format-2 tool carries. A reader has to
                # survive it rather than read it as an empty boundary list.
                "meta": {"letter_spans": None, "tintenpfad": dict(tintenpfad)},
                "erzeugt_am": DEFAULT_SHEET_DATE,
                "flecken_n": 0,
            }
        )
    return entries


def seed(api: AdminApi, hand: str, strips: list[str], fassung: str, with_paths: bool) -> None:
    """Print one Bogen, accept every row, store its pixels, and follow its words."""
    api.request(
        "PUT", f"/eigenhand/setups/{hand}", {"label": "Wegwerf-Stack", "feder": "synthetic", "tinte": "synthetic"}
    )
    printed = api.request("POST", "/eigenhand/sheets", {"hand": hand, "strips": strips, "date": DEFAULT_SHEET_DATE})
    sheet = printed["sheets"][0]["sheet"]
    layout = api.request("GET", f"/eigenhand/sheets/{hand}/{sheet}/layout")

    rows = layout["rows"]
    api.request(
        "POST",
        "/eigenhand/fassungen",
        {
            "hand": hand,
            "fassungen": [
                {"strip": row["strip"], "fassung": fassung, "sheet": sheet, "row_index": index, "status": "angenommen"}
                for index, row in enumerate(rows)
            ],
        },
    )

    for index, row in enumerate(rows):
        geometry = strip_geometry(row)
        png = synthetic_png(geometry["width_px"], geometry["height_px"])
        api.request(
            "PUT",
            f"/eigenhand/strips/{hand}/{row['strip']}/{fassung}",
            {
                "sheet": sheet,
                "row_index": index,
                "png_base64": base64.b64encode(png).decode(),
                "width_px": geometry["width_px"],
                "height_px": geometry["height_px"],
                "dpi": 300.0,
                "crop_origin_mm": geometry["crop_origin_mm"],
                "sha256": hashlib.sha256(png).hexdigest(),
            },
        )
        if not with_paths:
            continue
        # Read first, then push against the list that read returned: the path
        # write demands the token of the list it was made on (428 without one,
        # 412 when the stored list has moved since). The seeded row is empty
        # here, but the seeder pushes the way the tools do rather than the way
        # that happens to work on a fresh database.
        pfade_path = f"/eigenhand/strips/{hand}/{row['strip']}/{fassung}/pfade"
        _stored, token = api.answer("GET", pfade_path)
        api.request(
            "PUT", pfade_path, {"format": PFAD_FORMAT, "pfade": pfad_entries(row, geometry, index)}, if_match=token
        )
        print(
            f"seeded {row['strip']}/{fassung}: {geometry['width_px']}×{geometry['height_px']} px, {len(row['boxes'])} boxes"
        )

    bestand = api.request("GET", f"/eigenhand/bestand/{hand}")
    print(f"Bogen {sheet} · strips belegt: {bestand['strips']['belegt']} · Fassungen: {bestand['fassungen']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api", default="http://localhost:8000", help="loopback base URL of the throwaway API")
    parser.add_argument(
        "--hand",
        default=DEFAULT_HAND,
        help=f"hand id to seed (default: %(default)s); must start with {RESERVED_HAND_PREFIX!r}",
    )
    parser.add_argument(
        "--strips", default=",".join(DEFAULT_STRIPS), help="comma-separated strip ids of the frozen plan"
    )
    parser.add_argument("--without-paths", action="store_true", help="store the strip images but follow no paths")
    parser.add_argument(
        "--fassung",
        default=DEFAULT_FASSUNG,
        help="Fassung id to write (default: %(default)s); a re-run needs a fresh one",
    )
    parser.add_argument(
        "--reseed", action="store_true", help="write although the API already holds THIS hand (only for a re-run)"
    )
    args = parser.parse_args(argv)

    if not args.hand.startswith(RESERVED_HAND_PREFIX) or not is_hand_id(args.hand):
        raise SystemExit(
            f"--hand {args.hand!r} is not a throwaway hand: it must start with {RESERVED_HAND_PREFIX!r} and end in a "
            "known style, e.g. wegwerf-suetterlin. Naming a real hand would let --reseed overwrite it."
        )
    if not is_fassung_id(args.fassung):
        raise SystemExit(f"--fassung {args.fassung!r} is not a Fassung id (F + at least two digits)")

    token = os.environ.get("ADMIN_TOKEN", "")
    if not token:
        raise SystemExit("ADMIN_TOKEN is not exported — the admin routes answer 503 without it")

    api = AdminApi(args.api, token)
    strips = [strip.strip() for strip in args.strips.split(",") if strip.strip()]
    if not strips:
        raise SystemExit("--strips named nothing")

    # The positive discriminator: a freshly migrated local database has NO hand,
    # because no migration seeds the reserved dataset. Anything else on a
    # supposedly throwaway stack means the process found `.env` after all —
    # `checked_base` cannot see that, because a loopback uvicorn started without
    # the `DATABASE_URL` export serves the SHARED database on localhost.
    hands = api.request("GET", "/eigenhand/hands")["hands"]
    foreign = [hand for hand in hands if hand != args.hand]
    if foreign:
        # `--reseed` deliberately does NOT cover this branch: a hand this run did
        # not write is the signature of the shared database, and no re-run flag
        # should be able to talk past it.
        raise SystemExit(
            f"this API already holds hands {foreign} that this run did not write — a fresh throwaway database "
            "has none, so this may well be the SHARED database. Stopping before anything is written."
        )
    if hands and not args.reseed:
        raise SystemExit(
            f"this API already holds {args.hand} — pass --reseed together with a fresh --fassung (F02, F03, …) if "
            "those rows are your own throwaway from an earlier run of this script."
        )

    seed(api, args.hand, strips, args.fassung, with_paths=not args.without_paths)
    return 0


if __name__ == "__main__":
    sys.exit(main())
