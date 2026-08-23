"""Print a Bogen locally — the CLI half of ``core.eigenhand.bogen``.

Composition (queue, layout, PDF) is pure and lives in core, because the admin
view prints the same Bögen through the API. What is local here is the
persistence: every Bogen writes ``bogen.pdf`` (what the printer gets) and
``layout.json`` (the importer's sole geometry contract) under
``<dataroot>/<hand>/blaetter/<B>/``, and the Kartei records the print.

``--repeat K`` prints every selected strip K times in a row — several attempts
of the same content on one sheet, any subset acceptable at the Siebung.
``--strips`` overrides the queue entirely (ids may repeat). ``--sheets N``
prints a whole session's stack, each Bogen recorded before the next selects,
so no strip lands on two sheets. ``--no-hints`` drops the Fugen hint form from
the labels.

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
from tools.eigenhand.store import sheet_dir as store_sheet_dir
from tools.eigenhand.store import style_of_hand, universe_path
from tools.eigenhand.universe import load_universe


def local_soll() -> tuple[dict[str, float], dict[str, int]] | None:
    """The Übergangsraum-weighted Soll where this machine has the weight table.

    Only the local chain has it (derived from consult-only corpora, never
    committed, never uploaded), so this is also what the server does without:
    the print queue then ranks repetitions by fewest Fassungen instead of by
    weighted Soll gain.
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

    printed = []
    for _ in range(args.sheets):
        sheet = print_sheet(
            hand=args.hand,
            style=style,
            date=args.date,
            rows=args.rows,
            repeat=args.repeat,
            strips=args.strips,
            hints=not args.no_hints,
        )
        printed.append(sheet)
        print(
            f"wrote {sheet['pdf']} ({sheet['bytes']:,} bytes), {len(sheet['strips'])} rows: {' '.join(sheet['strips'])}"
        )
    if args.sheets > 1:
        print(f"{len(printed)} Bögen: {', '.join(row['sheet'] for row in printed)}")
    return 0


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
    """Compose one Bogen and file it in the local data root + Kartei."""
    plan = load_plan()
    kartei = load_kartei(hand, style)
    composed = bogen.compose_sheet(
        plan=plan,
        kartei=kartei,
        hand=hand,
        style=style,
        date=date,
        rows=rows,
        repeat=repeat,
        strips=strips,
        hints=hints,
        soll=local_soll(),
    )

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
    save_kartei(hand, kartei)
    return {
        "sheet": composed["sheet"],
        "pdf": out_dir / "bogen.pdf",
        "bytes": len(composed["pdf"]),
        "strips": composed["strips"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
