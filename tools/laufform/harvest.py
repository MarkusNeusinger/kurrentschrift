"""Laufform harvest: median running forms + per-occurrence rows.

The jul31 doctrine split (qualitaetsmetrik.md §6): the chart cell is the
DUCTUS PRIOR (stroke order, crossings), the written specimen words are the
FORM MODEL. This tool M4-fits every letter occurrence of the frozen Abb.-19
word fixtures onto the plates and produces two artefacts:

* per-letter MEDIANS over the clean fits (the running shape with the
  template's own topology intact), written as `templates` Laufform-variant
  DRAFT rows through the admin API
  (`PUT /sources/{id}/templates/{key}/laufform`), and
* every clean per-occurrence fit itself (handmodell plan H1 — occurrences,
  not just medians), written as `instances` rows in one batch
  (`PUT /sources/{id}/instances`, `replace: true`) under the specimen hand, and
* one traced WORD record per specimen (the full learning template: slot
  labels + the fitted letter strokes in the word's registration frame),
  written as `word_instances` rows (`PUT /sources/{id}/word-instances` —
  authored rows survive, the endpoint skips them).

Dry run prints the per-letter stats and writes ``laufform_drafts.json`` +
``laufform_occurrences.json``; ``--apply`` PUTs both (requires ``--base-url``
and the ``ADMIN_TOKEN`` env var). Never run against prod without an explicit
go — the composer picks the Laufform rows up immediately for every flowing
/write/word (the occurrence rows never affect rendering).

    uv run python -m tools.laufform.harvest [--style suetterlin]
        [--min-n 4] [--rmse-max 2.2] [--out laufform_drafts.json]
        [--occ-out laufform_occurrences.json]
        [--apply --base-url http://localhost:8000 --source-id <id>
         --hand-id suetterlin-1922-norm]
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


def _strokes_to_word_units(
    fitted: np.ndarray, stroke_starts: list[int], fit_frame: dict, registration: dict
) -> list[list[list[float]]]:
    """The fitted letter path in the WORD's registration frame (template units,
    baseline = 0, x from the word origin), one polyline per pen-down stroke.

    The fit returns anchors in its own letter frame (x_origin_px = px of
    template x 0, baseline_y_px = px of the baseline incl. the letter nudge);
    going through page px and back into the shared word frame keeps every
    letter on the word's common axes."""
    xh = fit_frame["xh"]
    px_x = fit_frame["x_origin_px"] + fitted[:, 0] * xh
    px_y = fit_frame["baseline_y_px"] - fitted[:, 1] * xh
    ux = (px_x - registration["tx"]) / xh
    uy = (registration["baseline_row"] + registration["ty"] - px_y) / xh
    pts = np.column_stack([ux, uy]).round(4)
    bounds = [*list(stroke_starts), len(pts)]
    return [pts[a:b].tolist() for a, b in zip(bounds, bounds[1:], strict=False) if b - a >= 2]


def harvest(style: str, min_n: int, rmse_max: float) -> tuple[dict[str, dict], list[dict], list[dict]]:
    """Per-letter median fitted anchors over the clean word occurrences, plus
    every clean fit as an occurrence record (`InstanceItem` wire shape), plus
    one traced word record per specimen (`WordInstanceItem` wire shape)."""
    per_key: dict[str, list[np.ndarray]] = defaultdict(list)
    tpl_by_key: dict[str, dict] = {}
    occurrences: list[dict] = []
    word_records: list[dict] = []
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
        word_strokes: list[list[list[float]]] = []
        fitted_slots: list[int] = []
        unfitted_slots: list[int] = []
        rmse_by_slot: dict[str, float] = {}
        for i, slot in enumerate(case.slots):
            items = _body_items(result, i)
            row = case.templates.get(slot.key) if slot.key else None
            if not items or row is None or case.width_map is None:
                if slot.key:
                    unfitted_slots.append(i)
                continue
            strokes_px = [_to_px(it["centerline"], xh, tx, ty, baseline_row) for it in items]
            ddx, ddy, at_bound, _before, _after = _fit_letter(edt, strokes_px, xh)
            if at_bound:
                unfitted_slots.append(i)
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
                unfitted_slots.append(i)
                continue
            payload = result.payloads.get(slot.key) or {}
            first_template = (payload.get("centerlines_template") or [[[0.0, 0.0]]])[0][0]
            dxc = items[0]["centerline"][0][0] - first_template[0]
            stroke_starts = meta.get("stroke_starts") or [0]
            baseline_y_px = baseline_row + ty + ddy
            x_origin_px = dxc * xh + tx + ddx - anchors[0, 0] * xh
            try:
                fr = fit_template_to_instance(
                    anchors,
                    np.asarray(row["half_widths"], dtype=float),
                    skel_local,
                    np.where(keep[None, :], case.width_map, 0.0),
                    unit_px=xh,
                    baseline_y_px=baseline_y_px,
                    x_origin_px=x_origin_px,
                    stroke_starts=stroke_starts,
                    corner_anchors=meta.get("corner_anchors") or [],
                )
            except Exception as exc:  # noqa: BLE001 — survey tool: skip, but say so
                print(f"  fit failed: {case.id} slot {i} ({slot.key}): {exc}", flush=True)
                unfitted_slots.append(i)
                continue
            if not fr.fit_meta.get("converged") or float(fr.fit_meta.get("geo_rmse_px", 99)) > rmse_max:
                unfitted_slots.append(i)
                continue
            fitted_raw = np.asarray(fr.anchors, dtype=float)
            if fitted_raw.shape != anchors.shape:
                unfitted_slots.append(i)
                continue
            shift = np.median(fitted_raw - anchors, axis=0)
            fitted = fitted_raw - shift  # shapes, not placements
            per_key[slot.key].append(fitted)
            tpl_by_key.setdefault(slot.key, row)
            # The word trace (handmodell word level): this letter's UNCENTERED
            # fitted strokes in the word's shared frame, in writing order.
            fitted_slots.append(i)
            rmse_by_slot[str(i)] = round(float(fr.fit_meta.get("geo_rmse_px", 0.0)), 3)
            word_strokes.extend(
                _strokes_to_word_units(
                    fitted_raw,
                    stroke_starts,
                    {"xh": xh, "x_origin_px": x_origin_px, "baseline_y_px": baseline_y_px},
                    {"tx": tx, "ty": ty, "baseline_row": baseline_row},
                )
            )
            # The occurrence row (handmodell H1): centered shape as anchors,
            # placement + fit context in measurements, crop in page pixels.
            rx, ry = (case.rect[0], case.rect[1]) if case.rect else (0, 0)
            prev_slot = case.slots[i - 1] if i > 0 else None
            next_slot = case.slots[i + 1] if i + 1 < len(case.slots) else None
            occurrences.append(
                {
                    "glyph_key": slot.key,
                    "glyph": row.get("glyph") or slot.key,
                    "position": slot.position or "medial",
                    "variant": 0,
                    "y0": int(round(body[:, 1].min())) + ry,
                    "y1": int(round(body[:, 1].max())) + ry,
                    "x0": int(round(body[:, 0].min())) + rx,
                    "x1": int(round(body[:, 0].max())) + rx,
                    "anchors": fitted.round(4).tolist(),
                    "half_widths": [],
                    "measurements": {
                        "specimen_id": case.id,
                        "slot": i,
                        "prev_key": prev_slot.key if prev_slot and not prev_slot.space else None,
                        "next_key": next_slot.key if next_slot and not next_slot.space else None,
                        "shift_xh": [round(float(shift[0]), 4), round(float(shift[1]), 4)],
                        "registration_px": [round(float(ddx), 2), round(float(ddy), 2)],
                        "geo_rmse_px": round(float(fr.fit_meta.get("geo_rmse_px", 0.0)), 3),
                        "xh_px": round(float(xh), 2),
                    },
                }
            )
        if word_strokes:
            word_records.append(
                {
                    "kind": case.kind,
                    "specimen_id": case.id,
                    "word": case.word,
                    "slots": [s.key for s in case.slots if s.key],
                    "strokes": word_strokes,
                    "provenance": "traced",
                    "measurements": {
                        "registration_px": {
                            "tx": round(float(tx), 2),
                            "ty": round(float(ty), 2),
                            "baseline_row": int(baseline_row),
                        },
                        "xh_px": round(float(xh), 2),
                        "fitted_slots": fitted_slots,
                        "unfitted_slots": unfitted_slots,
                        "geo_rmse_px_by_slot": rmse_by_slot,
                    },
                }
            )
        print(f"fitted {case.id}", flush=True)

    out: dict[str, dict] = {}
    for key, fits in sorted(per_key.items(), key=lambda kv: -len(kv[1])):
        if len(fits) < min_n:
            continue
        med = np.median(np.stack(fits), axis=0)
        tpl = np.asarray(tpl_by_key[key]["anchors"], dtype=float)
        out[key] = {"anchors": med.round(4).tolist(), "n_occurrences": len(fits)}
        print(f"{key:>6}  n={len(fits):>2}  median-vs-chart {float(np.hypot(*(med - tpl).T).mean()):.3f} xh")
    return out, occurrences, word_records


def apply_drafts(drafts: dict[str, dict], base_url: str, source_id: str, token: str) -> None:
    failed: list[str] = []
    for key, d in drafts.items():
        req = urllib.request.Request(
            f"{base_url}/sources/{source_id}/templates/{key}/laufform",
            data=json.dumps(d).encode(),
            method="PUT",
            headers={"Content-Type": "application/json", "X-Admin-Token": token},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                print(f"PUT {key}: {res.status}")
        except Exception as exc:  # noqa: BLE001 — keep going, report at the end
            print(f"PUT {key}: FAILED — {exc}")
            failed.append(key)
    if failed:
        raise SystemExit(f"{len(failed)} letters failed: {', '.join(failed)} — re-run --apply to retry")


def apply_batch(
    endpoint: str, items: list[dict], base_url: str, source_id: str, token: str, hand_id: str, hand_label: str
) -> None:
    """One replace-batch: the harvest walks ALL specimen words, so the stored
    rows are exactly this run's clean fits. (`word-instances` spares authored
    rows on replace and reports them as skipped — manual traces survive.)"""
    body = {"hand": {"id": hand_id, "label": hand_label, "era": "1922"}, "replace": True, "items": items}
    req = urllib.request.Request(
        f"{base_url}/sources/{source_id}/{endpoint}",
        data=json.dumps(body).encode(),
        method="PUT",
        headers={"Content-Type": "application/json", "X-Admin-Token": token},
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        print(f"PUT {endpoint}: {res.status} {res.read().decode()[:200]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--style", default="suetterlin")
    ap.add_argument("--min-n", type=int, default=4)
    ap.add_argument("--rmse-max", type=float, default=2.2)
    ap.add_argument("--out", type=Path, default=Path("laufform_drafts.json"))
    ap.add_argument("--occ-out", type=Path, default=Path("laufform_occurrences.json"))
    ap.add_argument("--word-out", type=Path, default=Path("laufform_words.json"))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--source-id")
    ap.add_argument("--hand-id", default="suetterlin-1922-norm")
    ap.add_argument("--hand-label", default="Suetterlin norm hand (Leitfaden 1922, Abb. 19/20)")
    args = ap.parse_args()

    drafts, occurrences, word_records = harvest(args.style, args.min_n, args.rmse_max)
    args.out.write_text(json.dumps(drafts))
    args.occ_out.write_text(json.dumps(occurrences))
    args.word_out.write_text(json.dumps(word_records))
    print(
        f"wrote {args.out} ({len(drafts)} letters) + {args.occ_out} ({len(occurrences)} occurrences)"
        f" + {args.word_out} ({len(word_records)} word traces)"
    )
    if args.apply:
        token = os.environ.get("ADMIN_TOKEN")
        if not token or not args.source_id:
            raise SystemExit("--apply needs --source-id and the ADMIN_TOKEN env var")
        base = args.base_url.rstrip("/")
        apply_drafts(drafts, base, args.source_id, token)
        apply_batch("instances", occurrences, base, args.source_id, token, args.hand_id, args.hand_label)
        apply_batch("word-instances", word_records, base, args.source_id, token, args.hand_id, args.hand_label)


if __name__ == "__main__":
    main()
