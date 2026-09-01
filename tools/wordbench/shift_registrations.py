"""Move stored word traces with a repaired rect — the other half of `repair_boxes`.

A trace registers in CROP-local pixels (`measurements.registration_px`: `tx` is
the word origin's crop column, `baseline_row` its Grundlinie row). The crop
starts at the sidecar rect's origin, so repairing a rect — growing it upward to
enclose a cut-off i-Strich, leftward to catch an Anstrich — moves that origin
and leaves every stored trace of the specimen sitting `dx`/`dy` px off the crop
it belongs to. A vertical drift at least surfaces: the SPA badges it „Rahmen
veraltet" ("frame out of date") and the fixture export drops the row from the
bench (`export_fixtures._frame_stale_reason`). A horizontal one nothing catches
at all, which is why this has to be exact rather than merely close.

Nothing about the pen path changed, so nothing needs re-tracing: the correction
is exactly the origin's shift, `tx += dx` and `baseline_row += dy`.

WHICH crop a row is currently expressed in is the whole difficulty, and it is
answered by recording it: a shifted row carries `measurements.rect_origin`, the
`[x0, y0]` it now belongs to. A row without that marker predates this tool and
belongs to the BASELINE sidecar — which is why `--baseline` is required rather
than a precomputed shift list. Both axes are then exact and the run is
idempotent, including a repair that moved only `x0` (a `baseline_row` test
alone cannot see that one: `das` and `und` are left-edge repairs, and reading
only the row would silently leave their `tx` behind).

    git show <ref>:data/sources/suetterlin-1922/words.json > temp/old.json

    # dry run — prints every row it would move, writes nothing
    uv run python -m tools.wordbench.shift_registrations --baseline temp/old.json

    # against the deployed API (the apex 302s at the Access edge; use the api host)
    ADMIN_TOKEN=… uv run python -m tools.wordbench.shift_registrations \\
        --baseline temp/old.json --api https://api.kurrentschrift.ink --apply

`--apply` WRITES TO THE SHARED DATABASE. Ask the author first: local dev and
the deployed API talk to the same Cloud SQL instance.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

from tools.wordbench.export_fixtures import REPO_ROOT
from tools.wordbench.fetch_fixtures import USER_AGENT, ApiClient, _NoRedirectHandler, _ssl_context


DEFAULT_SOURCE_ID = "suetterlin-1922"
DEFAULT_API = "http://localhost:8000"

# Stamped into a shifted row: the crop origin its registration is expressed in.
# A registration is meaningless without it — the crop it counts from is the one
# thing the numbers themselves do not say.
ORIGIN_KEY = "rect_origin"


def put_json(base_url: str, path: str, token: str, body: dict) -> Any:
    """The one write this tool makes.

    Reads go through `fetch_fixtures.ApiClient`, which has no write verb ON
    PURPOSE — so that module cannot mutate the deployed system even by
    accident, and it must stay that way. Hence this separate writer; it borrows
    that client's redirect and TLS handlers rather than restating them, because
    a second implementation is a second place for the property to go missing
    (the archive tool's docstring makes the same point). A plain urllib request
    also gets a 403 from the edge: the User-Agent is part of what gets through.
    """
    if not base_url.startswith("https://"):
        raise SystemExit(f"API base must be https://, got {base_url!r}")
    opener = urllib.request.build_opener(_NoRedirectHandler(), urllib.request.HTTPSHandler(context=_ssl_context()))
    request = urllib.request.Request(  # noqa: S310 — https, fixed scheme
        f"{base_url}{path}",
        data=json.dumps(body).encode(),
        method="PUT",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Admin-Token": token,
        },
    )
    try:
        with opener.open(request, timeout=120) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:  # surface the API's own detail, not a bare 4xx
        # The token lives in a header only — no URL or reason can carry it.
        raise SystemExit(f"PUT {path} → HTTP {exc.code}: {exc.read()[:400].decode(errors='replace')}") from None


def origins(path: Path) -> dict[str, tuple[int, int]]:
    """Every specimen's crop origin in one sidecar version."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(w.get("id") or w["word"]): (int(w["x0"]), int(w["y0"])) for w in data["words"]}


def plan(
    rows: list[dict], baseline: dict[str, tuple[int, int]], current: dict[str, tuple[int, int]]
) -> list[tuple[dict, tuple[int, int]]]:
    """The rows whose registration still counts from an older crop origin, each
    with the correction it needs."""
    todo: list[tuple[dict, tuple[int, int]]] = []
    for row in rows:
        sid = row["specimen_id"]
        if sid not in current:
            continue
        measurements = row.get("measurements") or {}
        if not measurements.get("registration_px"):
            continue  # no measured registration: the reader falls back to the
            # sidecar's own lineature, which is current by definition
        stamped = measurements.get(ORIGIN_KEY)
        was = tuple(stamped) if isinstance(stamped, (list, tuple)) and len(stamped) == 2 else baseline.get(sid)
        if was is None:
            continue
        dx, dy = int(was[0]) - current[sid][0], int(was[1]) - current[sid][1]
        if (dx, dy) != (0, 0):
            todo.append((row, (dx, dy)))
    return todo


def hand_body(hand: dict) -> dict:
    """The writer as the batch write wants it back — read from the API, never
    invented.

    The endpoint's `hand` is a get-or-CREATE and it OVERWRITES `label`/`era`/
    `note` with whatever the body carries. A placeholder label would therefore
    rename the writer as a side effect of moving a registration; `label` is
    also required, so leaving it out is not an option either. `style_id` is not
    accepted in the body at all — the server takes it from the source."""
    return {k: hand[k] for k in ("id", "label", "era", "note") if hand.get(k) is not None}


def shifted(row: dict, delta: tuple[int, int], origin: tuple[int, int]) -> dict:
    dx, dy = delta
    measurements = dict(row.get("measurements") or {})
    reg = dict(measurements["registration_px"])
    reg["tx"] = float(reg.get("tx", 0)) + dx
    reg["baseline_row"] = float(reg.get("baseline_row", 0)) + dy
    measurements["registration_px"] = reg
    measurements[ORIGIN_KEY] = [int(origin[0]), int(origin[1])]
    return {
        "kind": row["kind"],
        "specimen_id": row["specimen_id"],
        "word": row["word"],
        "slots": row["slots"],
        "strokes": row["strokes"],
        # Echoed, never coerced: an authored row must stay authored, or the
        # next harvest would overwrite the author's own pen work.
        "provenance": row["provenance"],
        "measurements": measurements,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE_ID)
    parser.add_argument(
        "--baseline",
        type=Path,
        required=True,
        help="the words.json version an unstamped row's registration counts from "
        "(git show <ref>:data/sources/<id>/words.json > old.json)",
    )
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("--token-env", default="ADMIN_TOKEN")
    parser.add_argument("--apply", action="store_true", help="WRITE the corrected registrations (shared DB!)")
    args = parser.parse_args()

    token = os.environ.get(args.token_env, "")
    if not token:
        raise SystemExit(f"no admin token in ${args.token_env}")

    baseline = origins(args.baseline)
    current = origins(REPO_ROOT / "data" / "sources" / args.source / "words.json")
    moved = {sid for sid, xy in current.items() if baseline.get(sid) not in (None, xy)}
    if not moved:
        print("no rect origin moved since the baseline — nothing to do")
        return

    api = ApiClient(args.api, token=token)
    rows = api.get(f"/sources/{args.source}/word-instances", admin=True)
    todo = plan(rows, baseline, current)
    print(f"{len(moved)} specimen(s) moved, {len(rows)} stored trace(s), {len(todo)} to correct:")
    for row, (dx, dy) in todo:
        print(f"  {row['specimen_id']:<18} {row['provenance']:<10} tx{dx:+d} baseline_row{dy:+d}")
    if not todo:
        return
    if not args.apply:
        print("\ndry run — pass --apply to write (this writes to the SHARED database)")
        return

    by_hand: dict[str | None, list[dict]] = defaultdict(list)
    for row, delta in todo:
        by_hand[row.get("hand_id")].append(shifted(row, delta, current[row["specimen_id"]]))
    for hand_id, items in by_hand.items():
        if not hand_id:
            print(f"skipping {len(items)} row(s) without a hand — the batch write needs one", file=sys.stderr)
            continue
        result = put_json(
            api.base_url,
            f"/sources/{args.source}/word-instances",
            token,
            {"hand": hand_body(api.get(f"/hands/{hand_id}", admin=True)), "replace": False, "items": items},
        )
        print(f"hand {hand_id}: stored {result['stored']}, skipped {result['skipped']}")


if __name__ == "__main__":
    main()
