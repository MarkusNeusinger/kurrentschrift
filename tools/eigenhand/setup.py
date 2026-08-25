"""The hand's standing setup: nib, ink, paper, capture device — typed once.

Ink, paper and nib are photometric parameters of a whole campaign, not details
of a single import: a change mid-campaign splits the corpus into cohorts that
cannot be compared on width or darkness (`docs/proposals/eigenhand-erfassung.md`
§6). So they are declared once, kept on the server (`eigenhand_hands`), and
cached next to the local data root so `ingest` can default to them at a desk
with a scanner and no reason to be online.

    # declare it (writes the server record AND the local cache)
    ADMIN_TOKEN=… uv run python -m tools.eigenhand.setup --hand mn-suetterlin \
        --feder "Brause 361 Steno" --tinte "Platinum Carbon Black" \
        --papier "Clairefontaine Clairalfa 90 g" --geraet scanner

    # fetch it onto another machine
    ADMIN_TOKEN=… uv run python -m tools.eigenhand.setup --hand mn-suetterlin --pull

    # what would ingest use right now?
    uv run python -m tools.eigenhand.setup --hand mn-suetterlin --show

`--show` is the only offline mode; it reads the cache alone. Everything else
talks to the admin API, because the record lives there — the tool family never
writes to the DB itself.

An update overwrites rather than adding a cohort row: the standing setup
answers „what do I reach for now". The historical truth lives per Fassung,
where a real change shows up as a visible break in the data.
"""

from __future__ import annotations

import argparse

from tools.eigenhand.apiclient import admin_token, api_base, request_json
from tools.eigenhand.store import check_hand_id, load_setup, save_setup, style_of_hand


FIELDS = ("label", "feder", "tinte", "papier", "geraet", "note")


def format_setup(hand: str, setup: dict) -> str:
    if not setup:
        return f"{hand}: no standing setup recorded"
    lines = [f"{hand} ({setup.get('style', '?')})"]
    lines += [f"  {name:8s} {setup[name]}" for name in FIELDS if setup.get(name)]
    if setup.get("updated_at"):
        lines.append(f"  {'stand':8s} {setup['updated_at']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--show", action="store_true", help="print the local cache and stop (offline)")
    ap.add_argument("--pull", action="store_true", help="fetch the record from the API into the local cache")
    ap.add_argument("--label", default=None, help='a human name for this hand, e.g. „Markus, Sütterlin 2026"')
    ap.add_argument("--feder", default=None, help='nib, e.g. „Brause 361 Steno"')
    ap.add_argument("--tinte", default=None, help='ink, e.g. „Platinum Carbon Black"')
    ap.add_argument("--papier", default=None, help='paper, e.g. „Clairefontaine Clairalfa 90 g"')
    ap.add_argument("--geraet", default=None, choices=("scanner", "kamera"), help="capture device")
    ap.add_argument("--note", default=None, help="anything else worth remembering about the setup")
    ap.add_argument("--api", default=None, help="API base URL (default: $EIGENHAND_API or production)")
    ap.add_argument("--token", default=None, help="admin token (default: $ADMIN_TOKEN)")
    args = ap.parse_args(argv)

    hand = check_hand_id(args.hand)
    if args.show:
        print(format_setup(hand, load_setup(hand)))
        return 0

    token = admin_token(args.token)
    base = api_base(args.api)
    changes = {name: getattr(args, name) for name in FIELDS if getattr(args, name) is not None}

    if args.pull or not changes:
        setup = request_json("GET", f"{base}/eigenhand/setups/{hand}", token, allow_404=True)
        if setup is None:
            print(f"{hand}: no standing setup recorded on the server yet — declare one with --feder/--tinte/--papier")
            return 1
    else:
        # A PUT replaces the record, so anything not named on this run has to
        # be carried over explicitly — otherwise correcting one typo would
        # silently blank the other fields. Carried over from the SERVER, not
        # from the local cache: the cache may be older than the record.
        current = request_json("GET", f"{base}/eigenhand/setups/{hand}", token, allow_404=True) or {}
        body = {"style": style_of_hand(hand)} | {name: current.get(name) for name in FIELDS} | changes
        setup = request_json("PUT", f"{base}/eigenhand/setups/{hand}", token, body)

    path = save_setup(hand, setup)
    print(format_setup(hand, setup))
    print(f"cached in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
