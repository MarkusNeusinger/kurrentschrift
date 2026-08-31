"""Move stored word traces with a repaired rect — the other half of `repair_boxes`.

A trace registers in CROP-local pixels (`measurements.registration_px`: `tx` is
the word origin's crop column, `baseline_row` its Grundlinie row). The crop
starts at the sidecar rect's origin, so repairing a rect — growing it upward to
enclose a cut-off i-Strich, say — moves that origin and leaves every stored
trace of the specimen sitting `dy` px too high on the crop it belongs to. The
SPA badges it „Rahmen veraltet" and the fixture export drops it from the bench
(`export_fixtures._frame_stale_reason`).

Nothing about the pen path changed, so nothing needs re-tracing: the correction
is exactly the origin's shift, `tx += dx` and `baseline_row += dy`, which
`repair_boxes --registration-shift` writes out per specimen.

Idempotent by construction rather than by a marker: a row is only moved when
its stored `baseline_row` fits the OLD crop geometry better than the new one.
Run it twice and the second run finds nothing to do.

    # dry run — prints every row it would move, writes nothing
    uv run python -m tools.wordbench.shift_registrations --shift temp/shift.json

    # against the deployed API (the apex 302s at the Access edge; use the api host)
    ADMIN_TOKEN=… uv run python -m tools.wordbench.shift_registrations \\
        --shift temp/shift.json --api https://api.kurrentschrift.ink --apply

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


DEFAULT_SOURCE_ID = "suetterlin-1922"
DEFAULT_API = "http://localhost:8000"


def _request(url: str, token: str, method: str = "GET", body: dict | None = None) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("X-Admin-Token", token)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:  # surface the API's own detail, not a bare 4xx
        raise SystemExit(f"{method} {url} -> {e.code}: {e.read()[:400].decode(errors='replace')}") from e


def crop_baseline_rows(source_id: str, shift: dict[str, dict]) -> dict[str, tuple[int, int]]:
    """Per repaired specimen, the crop-local Grundlinie row BEFORE and AFTER the
    repair. `baseline_y` is a page row and did not move; the crop origin did."""
    sidecar = json.loads((REPO_ROOT / "data" / "sources" / source_id / "words.json").read_text(encoding="utf-8"))
    out: dict[str, tuple[int, int]] = {}
    for w in sidecar["words"]:
        sid = str(w.get("id") or w["word"])
        if sid not in shift:
            continue
        new_row = int(w["baseline_y"]) - int(w["y0"])
        out[sid] = (new_row - int(shift[sid]["dy"]), new_row)
    return out


def plan(rows: list[dict], shift: dict[str, dict], rows_by_id: dict[str, tuple[int, int]]) -> list[dict]:
    """The rows whose registration still describes the pre-repair crop."""
    todo = []
    for row in rows:
        sid = row["specimen_id"]
        if sid not in shift:
            continue
        reg = (row.get("measurements") or {}).get("registration_px")
        if not reg:
            continue  # a row without a measured registration falls back to the
            # sidecar's own lineature at read time and needs no correction
        old_row, new_row = rows_by_id[sid]
        stored = float(reg.get("baseline_row", 0))
        if abs(stored - old_row) >= abs(stored - new_row):
            continue  # already sits in the repaired crop — nothing to do
        todo.append(row)
    return todo


def shifted(row: dict, shift: dict[str, dict]) -> dict:
    d = shift[row["specimen_id"]]
    measurements = dict(row.get("measurements") or {})
    reg = dict(measurements["registration_px"])
    reg["tx"] = float(reg.get("tx", 0)) + d["dx"]
    reg["baseline_row"] = float(reg.get("baseline_row", 0)) + d["dy"]
    measurements["registration_px"] = reg
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
    parser.add_argument("--shift", type=Path, required=True, help="JSON from `repair_boxes --registration-shift`")
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("--token-env", default="ADMIN_TOKEN")
    parser.add_argument("--apply", action="store_true", help="WRITE the corrected registrations (shared DB!)")
    args = parser.parse_args()

    token = os.environ.get(args.token_env, "")
    if not token:
        raise SystemExit(f"no admin token in ${args.token_env}")
    shift = json.loads(args.shift.read_text(encoding="utf-8"))
    if not shift:
        print("nothing to shift")
        return

    base = f"{args.api.rstrip('/')}/sources/{args.source}"
    rows = _request(f"{base}/word-instances", token)
    todo = plan(rows, shift, crop_baseline_rows(args.source, shift))
    print(f"{len(rows)} stored trace(s), {len(todo)} to move:")
    for row in todo:
        d = shift[row["specimen_id"]]
        print(f"  {row['specimen_id']:<18} {row['provenance']:<10} tx+{d['dx']} baseline_row+{d['dy']}")
    if not todo:
        return
    if not args.apply:
        print("\ndry run — pass --apply to write (this writes to the SHARED database)")
        return

    by_hand: dict[str | None, list[dict]] = defaultdict(list)
    for row in todo:
        by_hand[row.get("hand_id")].append(row)
    for hand_id, group in by_hand.items():
        if not hand_id:
            print(f"skipping {len(group)} row(s) without a hand — the batch write needs one", file=sys.stderr)
            continue
        result = _request(
            f"{base}/word-instances",
            token,
            method="PUT",
            body={"hand": {"id": hand_id}, "replace": False, "items": [shifted(r, shift) for r in group]},
        )
        print(f"hand {hand_id}: stored {result['stored']}, skipped {result['skipped']}")


if __name__ == "__main__":
    main()
