"""Build the frozen Kringel catalogue from ONE frozen fixture root.

    uv run python -m tools.tracebench.kringelcat \\
        --root tools/wordbench/fixtures/suetterlin/suetterlin-1922 \\
        --expect-root eaa195aa7c84 --out tools/tracebench/kringel_catalogue.json

Per loop of every glyph that carries one, over every occurrence in the root's
word specimens: how wide the loop is on the PLATE, how wide the composition
draws it, and how often the plate holds it open. The classes and states come
from `tools/tracebench/kringel.py`, so the catalogue and the sensor can never
disagree about what `klein` or `punkt` means.

Three rulers carry the reading, each declared because each could be wrong:

1. **Which loops exist** — the raster finder `kringel.loop_apertures` on the
   letter WITH the connector each side, splinters under
   `kringel.SPLITTER_FLOOR_UNITS` dropped. The ductus finder
   `core.aggregate.loop_ranges` (#552) is read alongside and its per-glyph
   count is stored, because the two disagree in both directions and the
   disagreement is a finding: it merges nested loops into one range, and it
   has no range at all for the `t` or for parts of the capitals.
2. **Which slot a plate counter belongs to** — the slot whose OWN body strokes
   span its x, the nearest body only breaking a tie. Nearest body alone hands
   a letter's counter to its neighbour whenever the letter's own loop is
   missing, which is exactly the case the catalogue is about.
3. **Which loop inside that slot** — one-to-one by centre distance, closest
   first, with no radius constant: the letter is the cap. #553 showed a flat
   0.45 xh window reaching a neighbour's loop.

A plate counter that no loop of its own slot claims is an ORPHAN and is
reported per glyph as a TOPOLOGY loss — the composition draws no loop where
the plate holds one. It never enters an aperture.

Measurement layer only: reads a frozen root, writes one JSON, never the DB,
never the root, never a scored number. Apertures, counts and classes only —
no anchors, no centerlines (`docs/reference/quellen-und-rechte.md` §5).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from tools.tracebench.kringel import (
    PLATE_PEN_HALF_WIDTH_UNITS,
    PLATE_PEN_WIDTH_UNITS,
    SPLITTER_FLOOR_UNITS,
    loop_apertures,
    loop_state,
    size_class,
    slot_loop_lines,
)
from tools.wordbench.roots import announce_roots


# A plate hole under this many pixels is paper grain inside the ink, not a
# counter (#551's floor, kept so the two readings stay comparable).
HOLE_MIN_PX = 3
# Below this a composed loop is the raster's own noise — two nearly touching
# polylines leaving a 2-4 px hole at 1200 px per x-height. Splinters between it
# and `SPLITTER_FLOOR_UNITS` are the interesting ones (a loop the composition
# has COLLAPSED), so only those are reported.
RASTER_NOISE_FLOOR_UNITS = 0.005
# The background is labelled 4-connected, as everywhere in this measurement.
_BG_STRUCT = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)


def plate_counters(mask: np.ndarray, skel: np.ndarray, width_map: np.ndarray) -> list[dict[str, Any]]:
    """Every counter of the binarised plate ink, in PIXELS.

    Each carries the aperture of the ink hole, the aperture of the medial-axis
    loop around it (`skeletonize`'s answer, which at a fused counter is NOT the
    pen path — the Verschmelzungs-Anzeiger of #552) and the local half width.
    """
    from scipy.ndimage import binary_dilation, distance_transform_edt  # noqa: PLC0415
    from scipy.ndimage import label as cc_label  # noqa: PLC0415

    labels, count = cc_label(~mask, structure=_BG_STRUCT)
    border = set(labels[0, :]) | set(labels[-1, :]) | set(labels[:, 0]) | set(labels[:, -1])
    edt = distance_transform_edt(~mask)
    skel_labels, _ = cc_label(~skel, structure=_BG_STRUCT)
    skel_border = set(skel_labels[0, :]) | set(skel_labels[-1, :]) | set(skel_labels[:, 0]) | set(skel_labels[:, -1])
    skel_edt = distance_transform_edt(~skel)
    out: list[dict[str, Any]] = []
    for i in range(1, count + 1):
        if i in border:
            continue
        sel = labels == i
        if sel.sum() < HOLE_MIN_PX:
            continue
        dist = np.where(sel, edt, -1.0)
        idx = int(np.argmax(dist))
        cy, cx = np.unravel_index(idx, dist.shape)
        row: dict[str, Any] = {
            "ink_px": 2.0 * float(dist.flat[idx]),
            "px": (float(cx), float(cy)),
            "skel_px": None,
            "half_px": None,
        }
        lab = int(skel_labels[cy, cx])
        if lab and lab not in skel_border:
            ring_of = skel_labels == lab
            row["skel_px"] = 2.0 * float(skel_edt[ring_of].max())
            ring = binary_dilation(ring_of, structure=np.ones((3, 3), bool)) & skel
            if ring.any():
                row["half_px"] = float(np.median(width_map[ring]))
        out.append(row)
    return out


def _measure_root(root: Path) -> dict[str, Any]:
    """Every loop of every occurrence, with the plate counter it accounts for."""
    from PIL import Image  # noqa: PLC0415

    from core.aggregate import loop_ranges  # noqa: PLC0415
    from core.compose import compose_word  # noqa: PLC0415
    from core.pipeline import render_payload_for_template  # noqa: PLC0415
    from core.shaping import GlyphSlot  # noqa: PLC0415
    from core.word_metric import score_word  # noqa: PLC0415

    manifest = json.loads((root / "manifest.json").read_text())
    ratio = manifest["style_ratio"]
    resolver = manifest["width_resolver"]
    nib = float(manifest["constant_nib_units"])
    charts = json.loads((root / "templates.json").read_text())
    laufforms = json.loads((root / "templates_laufform.json").read_text())
    chart_cache: dict[str, Any] = {}
    lauf_cache: dict[str, Any] = {}

    def chart_payload(key: str) -> Any:
        if key not in chart_cache:
            chart_cache[key] = render_payload_for_template(charts[key], ratio, resolver, nib) if key in charts else None
        return chart_cache[key]

    def lauf_payload(key: str) -> Any:
        if key not in lauf_cache:
            lauf_cache[key] = (
                render_payload_for_template(laufforms[key], ratio, resolver, nib) if key in laufforms else None
            )
        return lauf_cache[key]

    ductus = {
        key: len(
            loop_ranges(
                row["anchors"],
                row["half_widths"],
                (row.get("trace_meta") or {}).get("stroke_starts"),
                (row.get("trace_meta") or {}).get("corner_anchors"),
            )
        )
        for key, row in charts.items()
    }

    records: list[dict[str, Any]] = []
    orphans: list[dict[str, Any]] = []
    splinters: list[dict[str, Any]] = []
    half_widths: list[float] = []
    counters_total = counters_claimed = 0
    for entry in manifest["words"]:
        if not entry.get("scorable", True):
            continue
        word_id = entry["id"]
        word_dir = root / word_id
        meta = json.loads((word_dir / "word.json").read_text())
        npz = np.load(word_dir / "ref_skel.npz")
        skel, width_map = npz["skel"], npz["width_map"]
        mask = np.asarray(Image.open(word_dir / "ref_mask.png")) > 127
        xh = float(meta["baseline_y"] - meta["midband_y"])
        baseline_row = float(meta["baseline_y"] - meta["rect"][1])
        half_widths.extend((width_map[skel] / xh).tolist())

        slots = [GlyphSlot(**s) for s in meta["slots"]]
        by_key = {s.key: payload for s in slots if s.key and (payload := lauf_payload(s.key)) is not None}
        data = {s.key: chart_payload(s.key) for s in slots if s.key}
        composed = compose_word(slots, data, provenance=True, laufform_by_key=by_key or None)
        report = score_word(composed, meta, skel, nib)
        if report.get("failed"):
            continue
        tx, ty = report["registration"]["tx"], report["registration"]["ty"]

        counters = plate_counters(mask, skel, width_map)
        counters_total += len(counters)
        # plate counter centres, crop pixels -> the composition's own units
        centres = [(((c["px"][0] - tx) / xh), ((baseline_row + ty - c["px"][1]) / xh)) for c in counters]

        grouped = sorted(slot_loop_lines(composed["items"]).items())
        bodies = {
            slot: [np.asarray(it["centerline"], float) for it in composed["items"] if it.get("slot_index") == slot]
            for slot, _ in grouped
        }
        spans = {
            slot: (float(np.vstack(lines)[:, 0].min()), float(np.vstack(lines)[:, 0].max()))
            for slot, lines in bodies.items()
        }

        pending: list[dict[str, Any]] = []
        in_slot: dict[int, list[int]] = {}
        for slot, (key, lines) in grouped:
            kept = []
            for loop in loop_apertures(lines, floor=RASTER_NOISE_FLOOR_UNITS):
                if loop.d0 < SPLITTER_FLOOR_UNITS:
                    splinters.append({"word": word_id, "glyph": key, "d0": round(loop.d0, 4)})
                else:
                    kept.append(loop)
            for rank, loop in enumerate(kept):
                in_slot.setdefault(slot, []).append(len(pending))
                pending.append(
                    {
                        "word": word_id,
                        "glyph": key,
                        "loop": rank,
                        "d0": loop.d0,
                        "cx": loop.cx,
                        "cy": loop.cy,
                        "ink": None,
                        "skel": None,
                    }
                )

        owner: dict[int, int] = {}
        for ci, (x, y) in enumerate(centres):
            inside = [slot for slot, (lo, hi) in spans.items() if lo <= x <= hi]
            pool = inside or list(spans)
            owner[ci] = min(
                pool, key=lambda slot: min(float(np.min(np.hypot(b[:, 0] - x, b[:, 1] - y))) for b in bodies[slot])
            )
        for slot, ris in in_slot.items():
            cis = [ci for ci, s in owner.items() if s == slot]
            pairs = sorted(
                (float(np.hypot(pending[ri]["cx"] - centres[ci][0], pending[ri]["cy"] - centres[ci][1])), ri, ci)
                for ri in ris
                for ci in cis
            )
            took_loop: set[int] = set()
            took_counter: set[int] = set()
            for _d, ri, ci in pairs:
                if ri in took_loop or ci in took_counter:
                    continue
                took_loop.add(ri)
                took_counter.add(ci)
                counter = counters[ci]
                pending[ri]["ink"] = counter["ink_px"] / xh
                pending[ri]["skel"] = None if counter["skel_px"] is None else counter["skel_px"] / xh
            counters_claimed += len(took_counter)
            for ci in cis:
                if ci not in took_counter:
                    orphans.append(
                        {
                            "word": word_id,
                            "glyph": pending[ris[0]]["glyph"],
                            "ink": round(counters[ci]["ink_px"] / xh, 4),
                        }
                    )
        for ci, slot in owner.items():
            if slot not in in_slot:
                key = next(k for s, (k, _) in grouped if s == slot)
                orphans.append({"word": word_id, "glyph": key, "ink": round(counters[ci]["ink_px"] / xh, 4)})
        records.extend(pending)

    return {
        "nib": nib,
        "ductus_loops": ductus,
        "pen_half_width_measured": float(np.median(np.asarray(half_widths))),
        "counters_total": counters_total,
        "counters_claimed": counters_claimed,
        "records": records,
        "orphans": orphans,
        "splinters": splinters,
    }


def _catalogue_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        grouped[(rec["glyph"], rec["loop"])].append(rec)
    rows: list[dict[str, Any]] = []
    for (glyph, loop), group in sorted(grouped.items()):
        with_counter = [r for r in group if r["ink"] is not None]
        composed = np.array([r["d0"] for r in group])
        if not with_counter:
            # No occurrence of this loop is answered by the plate: it gets no
            # expectation rather than a guessed one.
            rows.append(
                {
                    "glyph": glyph,
                    "loop": loop,
                    "size_class": "unbelegt",
                    "state": "unbelegt",
                    "occurrences": len(group),
                    "with_counter": 0,
                    "share_open": 0.0,
                    "d0_plate": None,
                    "ink_plate_median": None,
                    "ink_plate_min": None,
                    "ink_plate_max": None,
                    "d0_skeleton_median": None,
                    "d0_composed_median": round(float(np.median(composed)), 4),
                    "d0_composed_min": round(float(composed.min()), 4),
                    "d0_composed_max": round(float(composed.max()), 4),
                    "thin": len(group) < 3,
                }
            )
            continue
        ink = np.array([r["ink"] for r in with_counter])
        skeleton = [r["skel"] for r in with_counter if r["skel"] is not None]
        d0_plate = float(np.median(ink)) + PLATE_PEN_WIDTH_UNITS
        rows.append(
            {
                "glyph": glyph,
                "loop": loop,
                "size_class": size_class(d0_plate),
                "state": loop_state(len(group), len(with_counter)),
                "occurrences": len(group),
                "with_counter": len(with_counter),
                "share_open": round(len(with_counter) / len(group), 3),
                "d0_plate": round(d0_plate, 4),
                "ink_plate_median": round(float(np.median(ink)), 4),
                "ink_plate_min": round(float(ink.min()), 4),
                "ink_plate_max": round(float(ink.max()), 4),
                "d0_skeleton_median": round(float(np.median(skeleton)), 4) if skeleton else None,
                "d0_composed_median": round(float(np.median(composed)), 4),
                "d0_composed_min": round(float(composed.min()), 4),
                "d0_composed_max": round(float(composed.max()), 4),
                "thin": len(group) < 3,
            }
        )
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, required=True, help="the frozen fixture root to read")
    parser.add_argument("--expect-root", help="digest prefix the root MUST start with")
    parser.add_argument("--out", type=Path, required=True, help="where to write the catalogue")
    args = parser.parse_args(argv)

    root_meta = announce_roots([args.root], args.expect_root)
    measured = _measure_root(args.root)
    rows = _catalogue_rows(measured["records"])
    orphans = Counter(o["glyph"] for o in measured["orphans"])
    payload = {
        "_source": {
            "title": "Kringel-Katalog — Größenklasse und Zustand je Buchstabe und Schleife",
            "what": (
                "Per loop of a suetterlin-1922 glyph: how wide the plate holds it (D0), which size class that "
                "is in widths of the plate's own pen, and — read off the plate over all occurrences — whether "
                "it is offen, wechselnd or a Punktkringel. Apertures, counts and classes only; no geometry."
            ),
            "built_by": "tools/tracebench/kringelcat.py",
            "sensor": "tools/tracebench/kringel.py",
            "measured_on": root_meta,
            "pen_half_width_units": PLATE_PEN_HALF_WIDTH_UNITS,
            "pen_half_width_measured": round(measured["pen_half_width_measured"], 4),
            "splinter_floor_units": SPLITTER_FLOOR_UNITS,
            "delivered_nib_units": measured["nib"],
            "plate_counters": measured["counters_total"],
            "plate_counters_claimed": measured["counters_claimed"],
            "ductus_loops_per_glyph": dict(sorted(measured["ductus_loops"].items())),
            "topology_losses_per_glyph": dict(sorted(orphans.items())),
            "collapsed_loops_per_glyph": dict(sorted(Counter(s["glyph"] for s in measured["splinters"]).items())),
            "license": (
                "Derived from the author's own ductus templates and the public-domain Suetterlin 1922 plates. "
                "A table of apertures and classes, reserved with the learned dataset "
                "(docs/reference/quellen-und-rechte.md §5); it carries no geometry."
            ),
            "doc": 'docs/reference/messjournal.md §14 „Kringel-Landmarke `sep06`"',
        },
        "loops": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    classes = Counter(r["size_class"] for r in rows)
    states = Counter(r["state"] for r in rows)
    print(f"{len(rows)} loops over {len({r['glyph'] for r in rows})} glyphs -> {args.out}")
    print(f"  classes {dict(sorted(classes.items()))}   states {dict(sorted(states.items()))}")
    print(
        f"  plate counters {measured['counters_total']}, claimed {measured['counters_claimed']}, "
        f"topology losses {len(measured['orphans'])}, splinters {len(measured['splinters'])}"
    )


if __name__ == "__main__":
    main()
