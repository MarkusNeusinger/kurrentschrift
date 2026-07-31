"""Laufform harvest: median running forms from the specimen words.

The jul31 doctrine split (qualitaetsmetrik.md §6): the chart cell is the
DUCTUS PRIOR (stroke order, crossings), the written specimen words are the
FORM MODEL. This tool M4-fits every letter occurrence of the frozen Abb.-19
word fixtures onto the plates, takes per-anchor medians over the clean fits —
the running shape with the template's own topology intact — and writes them
as `templates` variant-1 DRAFT rows through the admin API
(`PUT /sources/{id}/templates/{key}/laufform`).

Dry run prints the per-letter stats and writes ``laufform_drafts.json`` next
to nothing else; ``--apply`` PUTs the rows (requires ``--base-url`` and the
``ADMIN_TOKEN`` env var). Never run against prod without an explicit go —
the composer picks the rows up immediately for every flowing /write/word.

    uv run python -m tools.laufform.harvest [--style suetterlin]
        [--min-n 4] [--rmse-max 2.2] [--out laufform_drafts.json]
        [--apply --base-url http://localhost:8000 --source-id <id>]
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

from core.fit import fit_template_to_instance
from tools.pairlab.analyze import TRACE_WINDOW_MARGIN, _body_items, _fit_letter, _to_px
from tools.wordlab.cases import iter_fixture_word_cases
from tools.wordlab.derive import derive_word


def harvest(style: str, min_n: int, rmse_max: float) -> dict[str, dict]:
    """Per-letter median fitted anchors over the clean word occurrences."""
    per_key: dict[str, list[np.ndarray]] = defaultdict(list)
    tpl_by_key: dict[str, dict] = {}
    for case in iter_fixture_word_cases(which="words", style=style):
        if not case.scorable:
            continue
        result = derive_word(case)
        if result.composed["missing"] or result.report is None or result.report.get("failed"):
            continue
        xh = result.xh_px
        tx, ty = result.registration["tx"], result.registration["ty"]
        baseline_row = result.baseline_row
        edt = distance_transform_edt(~case.skel)
        for i, slot in enumerate(case.slots):
            items = _body_items(result, i)
            row = case.templates.get(slot.key) if slot.key else None
            if not items or row is None or case.width_map is None:
                continue
            strokes_px = [_to_px(it["centerline"], xh, tx, ty, baseline_row) for it in items]
            ddx, ddy, at_bound, _before, _after = _fit_letter(edt, strokes_px, xh)
            if at_bound:
                continue
            anchors = np.asarray(row["anchors"], dtype=float)
            meta = row.get("trace_meta") or {}
            body = np.vstack(strokes_px) + np.array([ddx, ddy])
            cols = np.arange(case.skel.shape[1])
            keep = (cols >= body[:, 0].min() - TRACE_WINDOW_MARGIN * xh) & (
                cols <= body[:, 0].max() + TRACE_WINDOW_MARGIN * xh
            )
            skel_local = case.skel & keep[None, :]
            if not skel_local.any():
                continue
            payload = result.payloads.get(slot.key) or {}
            first_template = (payload.get("centerlines_template") or [[[0.0, 0.0]]])[0][0]
            dxc = items[0]["centerline"][0][0] - first_template[0]
            try:
                fr = fit_template_to_instance(
                    anchors,
                    np.asarray(row["half_widths"], dtype=float),
                    skel_local,
                    np.where(keep[None, :], case.width_map, 0.0),
                    unit_px=xh,
                    baseline_y_px=baseline_row + ty + ddy,
                    x_origin_px=dxc * xh + tx + ddx - anchors[0, 0] * xh,
                    stroke_starts=meta.get("stroke_starts") or [0],
                    corner_anchors=meta.get("corner_anchors") or [],
                )
            except Exception:
                continue
            if not fr.fit_meta.get("converged") or float(fr.fit_meta.get("geo_rmse_px", 99)) > rmse_max:
                continue
            fitted = np.asarray(fr.anchors, dtype=float)
            if fitted.shape != anchors.shape:
                continue
            fitted = fitted - np.median(fitted - anchors, axis=0)  # shapes, not placements
            per_key[slot.key].append(fitted)
            tpl_by_key.setdefault(slot.key, row)
        print(f"fitted {case.id}", flush=True)

    out: dict[str, dict] = {}
    for key, fits in sorted(per_key.items(), key=lambda kv: -len(kv[1])):
        if len(fits) < min_n:
            continue
        med = np.median(np.stack(fits), axis=0)
        tpl = np.asarray(tpl_by_key[key]["anchors"], dtype=float)
        out[key] = {"anchors": med.round(4).tolist(), "n_occurrences": len(fits)}
        print(f"{key:>6}  n={len(fits):>2}  median-vs-chart {float(np.hypot(*(med - tpl).T).mean()):.3f} xh")
    return out


def apply_drafts(drafts: dict[str, dict], base_url: str, source_id: str, token: str) -> None:
    for key, d in drafts.items():
        req = urllib.request.Request(
            f"{base_url}/sources/{source_id}/templates/{key}/laufform",
            data=json.dumps(d).encode(),
            method="PUT",
            headers={"Content-Type": "application/json", "X-Admin-Token": token},
        )
        with urllib.request.urlopen(req) as res:
            print(f"PUT {key}: {res.status}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--style", default="suetterlin")
    ap.add_argument("--min-n", type=int, default=4)
    ap.add_argument("--rmse-max", type=float, default=2.2)
    ap.add_argument("--out", type=Path, default=Path("laufform_drafts.json"))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--source-id")
    args = ap.parse_args()

    drafts = harvest(args.style, args.min_n, args.rmse_max)
    args.out.write_text(json.dumps(drafts))
    print(f"wrote {args.out} ({len(drafts)} letters)")
    if args.apply:
        token = os.environ.get("ADMIN_TOKEN")
        if not token or not args.source_id:
            raise SystemExit("--apply needs --source-id and the ADMIN_TOKEN env var")
        apply_drafts(drafts, args.base_url.rstrip("/"), args.source_id, token)


if __name__ == "__main__":
    main()
