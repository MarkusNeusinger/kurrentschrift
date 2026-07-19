"""Harvest glyph-pair overrides from the Abb.-20 specimens (redesign R3).

The pair layer's Erstbefüllung: for every adjacent joined letter pair in the
frozen pair fixtures, dissect the real occurrence (independent per-letter fits
+ M4 ductus traces, tools/pairlab/analyze.py) and derive a ``PairGeometry`` the
composer can replay verbatim:

* ``offset`` — where the right glyph's entry lands relative to the left
  glyph's exit, read off the two letters' INDEPENDENT rigid fits (the
  composer translates unwarped templates, so the placement must come from the
  rigid fits, not from the warped trace endpoints).
* ``connector`` — the specimen's own connecting stroke between the two ink
  columns, spliced to run exit → entry (template units, relative to the exit).

Every harvest lands as an UNAPPROVED draft with ``provenance: harvested`` and
the specimen id — review + Freigabe happen in the pair editor (/admin/paare),
which stays the human gate. Writes go through the admin API so its registry-key
and geometry validation applies; without ``--apply`` this only writes a JSON
report to inspect.

Usage:
    uv run python -m tools.pairlab.harvest [--style suetterlin] [--sets pairs]
        [--ids Bi,Du] [--out temp/pair_harvest.json]
        [--apply] [--api http://127.0.0.1:8000] [--source suetterlin-1922]
        [--approve B:i,D:u]

``--approve`` marks the named left:right pairs approved in the SAME upsert —
use only after eyeballing the draft (pair editor or wordlab): approved rows
render on the public /write path.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

from core.compose import _key_base
from core.shaping import is_registry_glyph_key
from tools.pairlab.analyze import JoinDissection, _edt_at, dissect_occurrence
from tools.wordlab.cases import WordCase, _load_dotenv, iter_fixture_word_cases


# A harvested connector is stored downsampled: enough points for a faithful
# curve (the real gaps span ~0.3-1.5 xh), far below the API's 500-point cap.
MAX_CONNECTOR_POINTS = 60
# Residual (xh) above which an independent letter fit is too poor to trust the
# derived placement — the occurrence is reported but flagged.
MAX_FIT_RESID_UNITS = 0.14


def _smooth_open(points: np.ndarray) -> np.ndarray:
    """Moving-average (window 3) over the interior points; endpoints stay put.

    The raw connector is a per-column skeleton track, so it carries one-pixel
    jitter the stored centerline should not replay."""
    if len(points) < 3:
        return points
    out = points.astype(float).copy()
    out[1:-1] = (points[:-2] + points[1:-1] + points[2:]) / 3.0
    return out


def connector_points(
    exit_u: tuple[float, float], entry_u: tuple[float, float], real_u: np.ndarray, end_dy: float = 0.0
) -> list[list[float]]:
    """The stored connector centerline: exit → specimen stroke → entry,
    relative to the exit point (PairGeometry's frame).

    ``real_u`` is the specimen's connecting stroke in absolute template units
    (may be empty when the letters touch on the plate — then the join is the
    direct exit→entry segment). ``end_dy`` corrects the end point into the
    composer's baseline-locked world: the specimen may write B vertically
    shifted against A, but the composer keeps both on the shared baseline, so
    the stored path must meet B's entry there — the correction is spread
    linearly along the horizontal progress."""
    pts = np.asarray(real_u, dtype=float).reshape(-1, 2)
    if len(pts):
        # Keep the strictly-between stretch: the tracked stroke starts at the
        # ink-column edges, which may sit inside/behind the template endpoints.
        keep = (pts[:, 0] > exit_u[0]) & (pts[:, 0] < entry_u[0])
        pts = pts[keep]
    path = np.vstack([[exit_u], pts, [entry_u]]) if len(pts) else np.asarray([exit_u, entry_u])
    path = _smooth_open(path)
    if len(path) > MAX_CONNECTOR_POINTS:
        idx = np.round(np.linspace(0, len(path) - 1, MAX_CONNECTOR_POINTS)).astype(int)
        path = path[idx]
    rel = path - np.asarray(exit_u, dtype=float)
    if end_dy:
        span = rel[-1, 0]
        progress = rel[:, 0] / span if abs(span) > 1e-9 else np.linspace(0.0, 1.0, len(rel))
        rel[:, 1] += end_dy * np.clip(progress, 0.0, 1.0)
    return [[round(float(x), 4), round(float(y), 4)] for x, y in rel]


def _px_to_units(pt: tuple[float, float], xh: float, tx: float, ty: float, baseline_row: float) -> tuple[float, float]:
    return ((pt[0] - tx) / xh, (baseline_row + ty - pt[1]) / xh)


def harvest_geometry(d: JoinDissection) -> dict:
    """PairGeometry + QC numbers for one dissected occurrence.

    Placement comes from the rigid independent fits (``exit_px``/``entry_px``
    are the template endpoints at each letter's own best placement); the
    connector shape from the specimen's tracked joining stroke. The harvest
    chamfer measures the FINAL stored centerline against the specimen skeleton
    so it is directly comparable to ``gen_chamfer`` (the generated connector at
    the same independent placement)."""
    xh = d.result.xh_px
    tx, ty = d.result.registration["tx"], d.result.registration["ty"]
    baseline_row = d.result.baseline_row

    exit_u = _px_to_units(d.exit_px, xh, tx, ty, baseline_row)
    entry_u = _px_to_units(d.entry_px, xh, tx, ty, baseline_row)
    real_u = (
        np.column_stack([(d.real_px[:, 0] - tx) / xh, (baseline_row + ty - d.real_px[:, 1]) / xh])
        if len(d.real_px)
        else np.zeros((0, 2))
    )
    # The composer renders both glyphs baseline-locked and applies only the
    # horizontal offset component, so the stored path must end at B's entry as
    # COMPOSED: undo the relative vertical fit shift at the end point (px y
    # grows downward, hence b - a in px equals a - b in units).
    end_dy = (d.b.ddy_px - d.a.ddy_px) / xh
    connector = connector_points(exit_u, entry_u, real_u, end_dy=end_dy)
    # offset[1] is baseline-locked too, so connector[-1] == offset exactly (the
    # editor draws both); the specimen's raw vertical relation is fit context,
    # not placement data.
    offset = [round(entry_u[0] - exit_u[0], 4), round(entry_u[1] - exit_u[1] + end_dy, 4)]

    edt = distance_transform_edt(~d.case.skel)
    abs_px = np.column_stack(
        [
            (np.asarray(connector)[:, 0] + exit_u[0]) * xh + tx,
            baseline_row + ty - (np.asarray(connector)[:, 1] + exit_u[1]) * xh,
        ]
    )
    harvest_chamfer = float(_edt_at(edt, abs_px).mean()) / xh

    return {
        "geometry": {"offset": offset, "connector": connector},
        "qc": {
            "specimen_id": d.case.id,
            "kind": d.case.kind,
            "slot": d.slot_a,
            "at_bound": bool(d.a.at_bound or d.b.at_bound),
            "a_resid": round(d.a.resid_after, 3),
            "b_resid": round(d.b.resid_after, 3),
            "fit_ok": bool(
                not (d.a.at_bound or d.b.at_bound) and max(d.a.resid_after, d.b.resid_after) <= MAX_FIT_RESID_UNITS
            ),
            "gap_ink": bool(len(d.real_px)),
            "gen_chamfer": round(d.gen_chamfer, 3),
            "harvest_chamfer": round(harvest_chamfer, 3),
            "trace_converged": bool(d.a_trace and d.b_trace and d.a_trace.converged and d.b_trace.converged),
        },
    }


def _adjacent_joined(case: WordCase) -> list[tuple[int, str, str]]:
    """(slot index, left base, right base) for every joined adjacent pair."""
    out = []
    for i in range(len(case.slots) - 1):
        s0, s1 = case.slots[i], case.slots[i + 1]
        if s0.space or s1.space or not s0.key or not s1.key or not (s0.joins and s1.joins):
            continue
        out.append((i, _key_base(s0.key, s0.position), _key_base(s1.key, s1.position)))
    return out


def _occurrence_rank(entry: dict) -> tuple:
    """Best specimen first: Abb.-20 pair plates over word occurrences, clean
    fits over flagged ones, then the tighter fit."""
    qc = entry["qc"]
    return (0 if qc["kind"] == "pair" else 1, 0 if qc["fit_ok"] else 1, max(qc["a_resid"], qc["b_resid"]))


def harvest_all(style: str, sets: tuple[str, ...], only_ids: set[str] | None) -> dict[tuple[str, str], dict]:
    """Dissect every joined pair occurrence in the given fixture sets and keep
    the best occurrence per (left, right)."""
    candidates: dict[tuple[str, str], list[dict]] = {}
    for which in sets:
        for case in iter_fixture_word_cases(which=which, style=style):
            if not case.scorable or not case.has_specimen:
                continue
            if only_ids and case.id not in only_ids:
                continue
            for slot_a, left, right in _adjacent_joined(case):
                if not (is_registry_glyph_key(left) and is_registry_glyph_key(right)):
                    print(f"  skip {case.id} slot {slot_a}: {left!r}->{right!r} not registry keys")
                    continue
                d = dissect_occurrence(case, slot_a, trace=True)
                if d is None:
                    print(f"  skip {case.id} slot {slot_a}: dissection failed (missing template?)")
                    continue
                entry = harvest_geometry(d)
                entry["left_key"] = left
                entry["right_key"] = right
                candidates.setdefault((left, right), []).append(entry)
    return {pair: sorted(entries, key=_occurrence_rank)[0] for pair, entries in sorted(candidates.items())}


def apply_drafts(
    harvested: dict[tuple[str, str], dict], api: str, source_id: str, token: str, approve: set[tuple[str, str]]
) -> None:
    """PUT every harvested pair as a draft (or approved, if listed) through the
    admin API — its registry-key + geometry validation is the gate."""
    for (left, right), entry in harvested.items():
        body = {
            "geometry": entry["geometry"],
            "provenance": "harvested",
            "specimen_id": entry["qc"]["specimen_id"],
            "approved": (left, right) in approve,
            "variant": 0,
        }
        url = f"{api}/sources/{source_id}/pairs/{left}/{right}"
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "X-Admin-Token": token},
            method="PUT",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
        except urllib.error.HTTPError as err:
            print(f"  PUT {left}->{right}: HTTP {err.code} {err.read().decode()[:200]}")
            continue
        flag = " (approved)" if body["approved"] else ""
        print(f"  PUT {left}->{right}: {status}{flag}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--style", default="suetterlin")
    parser.add_argument("--sets", default="pairs", help="comma-separated fixture sets to search (default: pairs)")
    parser.add_argument("--ids", help="comma-separated specimen ids to restrict to (e.g. Bi,Du)")
    parser.add_argument(
        "--out", type=Path, default=Path("temp/pair_harvest.json"), help="write the harvest report here"
    )
    parser.add_argument("--apply", action="store_true", help="PUT the drafts via the admin API")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--source", default="suetterlin-1922")
    parser.add_argument("--approve", help="left:right pairs to approve in the same write (e.g. B:i,D:u)")
    args = parser.parse_args()

    sets = tuple(s.strip() for s in args.sets.split(",") if s.strip())
    only_ids = {s.strip() for s in args.ids.split(",")} if args.ids else None
    harvested = harvest_all(args.style, sets, only_ids)

    for (left, right), entry in harvested.items():
        qc = entry["qc"]
        flags = [] if qc["fit_ok"] else ["fit?"]
        if not qc["gap_ink"]:
            flags.append("no-gap-ink")
        if not qc["trace_converged"]:
            flags.append("trace?")
        print(
            f"{left}->{right:<6} {qc['specimen_id']:<10} offset [{entry['geometry']['offset'][0]:+.2f}, "
            f"{entry['geometry']['offset'][1]:+.2f}]  pts {len(entry['geometry']['connector']):>2}  "
            f"chamfer gen {qc['gen_chamfer']:.3f} -> harvest {qc['harvest_chamfer']:.3f}"
            f"{('  [' + ' '.join(flags) + ']') if flags else ''}"
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps([{"left_key": k[0], "right_key": k[1], **v} for k, v in harvested.items()], indent=1)
    )
    print(f"{len(harvested)} pairs -> {args.out}")

    if args.apply:
        _load_dotenv()
        import os  # noqa: PLC0415

        token = os.environ.get("ADMIN_TOKEN", "")
        if not token:
            raise SystemExit("--apply needs ADMIN_TOKEN (set it in .env)")
        approve: set[tuple[str, str]] = set()
        if args.approve:
            for spec in args.approve.split(","):
                left, _, right = spec.strip().partition(":")
                if not left or not right:
                    raise SystemExit(f"--approve entry {spec!r}: expected left:right (e.g. B:i)")
                approve.add((left, right))
        apply_drafts(harvested, args.api.rstrip("/"), args.source, token, approve)


if __name__ == "__main__":
    main()
