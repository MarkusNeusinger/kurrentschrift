"""Print a Bogen locally — the CLI half of ``core.eigenhand.bogen``.

Composition (queue, layout, PDF) is pure and lives in core, because the admin
view prints the same Bögen through the API. What is local here is the
persistence: every Bogen writes ``bogen.pdf`` (what the printer gets) and
``layout.json`` (the importer's sole geometry contract) under
``<dataroot>/<hand>/blaetter/<B>/``, and the Kartei records the print.

``--repeat K`` prints every selected strip K times in a row — several attempts
of the same content on one sheet, any subset acceptable at the Siebung.
``--strips`` overrides the queue entirely (ids may repeat). ``--sheets N``
prints a whole session's stack in ONE selection (the pages continue the queue,
so no strip lands on two sheets) and, besides every Bogen's own files, ONE
multi-page ``stapel-<first>-<last>.pdf`` for the printer. A job always starts
at the front of the queue: a Bogen printed earlier but never written holds
nothing back. ``--no-hints`` drops the Fugen hint form from the labels.

Bogen ids are minted from the Kartei this CLI sees. The admin view mints from
the DB, so print from ONE of the two at a time (or push the local prints up
with ``tools.eigenhand.sync`` before printing there).

    uv run python -m tools.eigenhand.sheet --hand mn-suetterlin --date 2026-08-22
"""

from __future__ import annotations

import argparse

from core.eigenhand import bogen, geometry
from core.eigenhand.plan import load_plan
from tools.eigenhand.kartei import load_kartei, save_kartei
from tools.eigenhand.pool import soll_model
from tools.eigenhand.store import hand_dir, style_of_hand, universe_path
from tools.eigenhand.store import sheet_dir as store_sheet_dir
from tools.eigenhand.universe import load_universe


def local_soll() -> tuple[dict[str, float], dict[str, int]] | None:
    """The Übergangsraum-weighted Soll where this machine has the weight table.

    The local file (derived from consult-only corpora, never committed); the
    server reads the same table from the row `universe --push` stored. Without
    either, the print queue ranks repetitions by fewest Fassungen instead of
    by weighted Soll gain.
    """
    return soll_model(load_universe()["items"]) if universe_path().exists() else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True, help="hand id, e.g. mn-suetterlin")
    ap.add_argument("--style", default=None, help="style id (default: inferred from the hand id)")
    ap.add_argument("--rows", type=int, default=None, help="rows on the sheet (default: what fits, breathing)")
    ap.add_argument("--repeat", type=int, default=1, help="print each selected strip K times (attempts)")
    ap.add_argument("--strips", nargs="*", default=None, help="explicit strip ids (override the queue; may repeat)")
    ap.add_argument("--date", required=True, help="print date, ISO (explicit for deterministic output)")
    ap.add_argument("--no-hints", action="store_true", help="plain word labels without the Fugen hint form")
    ap.add_argument("--sheets", type=int, default=1, help="print this many Bögen in one go (default: %(default)s)")
    args = ap.parse_args(argv)

    style = args.style or style_of_hand(args.hand)
    if style not in geometry.PRESETS:
        raise SystemExit(f"unknown style {style!r}")
    if args.sheets < 1:
        ap.error("--sheets must be at least 1")
    if args.sheets > 1 and args.strips:
        ap.error("--strips names the rows of ONE sheet; use it without --sheets")

    stack = print_stack(
        hand=args.hand,
        style=style,
        date=args.date,
        sheets=args.sheets,
        rows=args.rows,
        repeat=args.repeat,
        strips=args.strips,
        hints=not args.no_hints,
    )
    for sheet in stack["sheets"]:
        print(
            f"wrote {sheet['pdf']} ({sheet['bytes']:,} bytes), {len(sheet['strips'])} rows: {' '.join(sheet['strips'])}"
        )
    if stack["stack_pdf"] is not None:
        print(
            f"{len(stack['sheets'])} Bögen in one document: {stack['stack_pdf']} "
            f"({', '.join(row['sheet'] for row in stack['sheets'])})"
        )
    return 0


def print_stack(
    *,
    hand: str,
    style: str,
    date: str,
    sheets: int = 1,
    rows: int | None = None,
    repeat: int = 1,
    strips: list[str] | None = None,
    hints: bool = True,
) -> dict:
    """Compose a stack in one selection and file every Bogen in the data root + Kartei.

    Each Bogen keeps its own ``bogen.pdf`` + ``layout.json`` (what ``pull``,
    ``ingest`` and the archive work with); a stack of more than one also gets
    the multi-page ``stapel-<first>-<last>.pdf`` beside the Bogen folders.
    """
    plan = load_plan()
    kartei = load_kartei(hand, style)
    stack = bogen.compose_stack(
        plan=plan,
        kartei=kartei,
        hand=hand,
        style=style,
        date=date,
        sheets=sheets,
        rows=rows,
        repeat=repeat,
        strips=strips,
        hints=hints,
        soll=local_soll(),
    )

    filed = []
    for composed in stack["sheets"]:
        out_dir = store_sheet_dir(hand, composed["sheet"])
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "layout.json").write_text(bogen.layout_text(composed["layout"]), encoding="utf-8")
        (out_dir / "bogen.pdf").write_bytes(composed["pdf"])
        kartei["sheets"][composed["sheet"]] = {
            "printed": date,
            "strips": composed["strips"],
            "layout_sha256": composed["layout_sha256"],
            "scans": [],
        }
        filed.append(
            {
                "sheet": composed["sheet"],
                "pdf": out_dir / "bogen.pdf",
                "bytes": len(composed["pdf"]),
                "strips": composed["strips"],
            }
        )
    save_kartei(hand, kartei)

    stack_pdf = None
    if len(filed) > 1:
        # Beside the Kartei, NOT inside `blaetter/`: everything under that
        # folder is read as a Bogen directory (snapshot, sync, restore).
        stack_pdf = hand_dir(hand) / f"stapel-{filed[0]['sheet']}-{filed[-1]['sheet']}.pdf"
        stack_pdf.write_bytes(stack["pdf"])
    return {"sheets": filed, "stack_pdf": stack_pdf}


def print_sheet(
    *,
    hand: str,
    style: str,
    date: str,
    rows: int | None = None,
    repeat: int = 1,
    strips: list[str] | None = None,
    hints: bool = True,
) -> dict:
    """Compose one Bogen and file it — the stack of one."""
    return print_stack(
        hand=hand, style=style, date=date, sheets=1, rows=rows, repeat=repeat, strips=strips, hints=hints
    )["sheets"][0]


if __name__ == "__main__":
    raise SystemExit(main())
