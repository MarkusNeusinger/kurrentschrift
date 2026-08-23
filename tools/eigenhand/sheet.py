"""Compose and print a Bogen — one A4 training sheet of pending Streifen.

Selection order of the print queue (proposal §5): redo-queue entries first,
then never-recorded strips in plan order (preserving the wave's coverage
velocity), then repetition candidates (fewest accepted Fassungen first).
``--repeat K`` prints every selected strip K times in a row — several
attempts of the same content on one sheet, any subset acceptable at the
Siebung. ``--strips`` overrides the queue entirely (ids may repeat).

Every Bogen writes two files under ``<dataroot>/<hand>/blaetter/<B>/``:
``bogen.pdf`` (what the printer gets) and ``layout.json`` — the importer's
SOLE geometry contract (mm coordinates of Passmarken, rows and boxes;
registration instead of detection). The Kartei records the print.

Clear-text labels are plain Latin (legibility doctrine; WinAnsi has no ſ).
A label shows the Fugen hint form where one exists (``Amts*|zeit``: ``*`` =
round s forced at the boundary) — the one case where shaping deviates from
the default rules the writer learns once; ``--no-hints`` shows clean words.

    uv run python -m tools.eigenhand.sheet --hand mn-suetterlin --date 2026-08-22
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from dataclasses import asdict

from core.config import REPO_ROOT
from tools.eigenhand import coverage, geometry, pdfgen
from tools.eigenhand.corpus import pool_entries
from tools.eigenhand.kartei import accepted_fassungen, load_kartei, next_sheet_id, save_kartei, strip_state
from tools.eigenhand.pool import load_plan, soll_model
from tools.eigenhand.store import STREIFEN_JSON, hand_dir, style_of_hand
from tools.eigenhand.universe import load_universe


LAYOUT_FORMAT = 1
MARGIN_MM = 15.0
ROW_ID_SIZE_MM = 2.5
LABEL_SIZE_MM = 3.0
HEADER_SIZE_MM = 3.5
FOOTER_SIZE_MM = 2.8
MARK_CAPTION_SIZE_MM = 2.4
MARK_CAPTION = "ok"  # one box per row: ticked = ok, empty = not ok


def _git_commit() -> str:
    try:
        done = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=10
        )
        return done.stdout.strip() if done.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def hint_label(word: str, fugen: str | None) -> str:
    """The printed label: the Fugen hint form where one exists (``Amts*|zeit``)."""
    if not fugen:
        return word
    return fugen.replace("s|", "s*|")


def _repetition_ranking(plan: dict, kartei: dict, ordered: list[str]) -> list[str]:
    """Already-recorded strips ranked by the weighted Soll gain of one more Fassung.

    "Which strips should be written more often because their words are so
    frequent" (owner, 2026-08-22): a strip whose words carry frequent items
    with open Soll outranks one whose items are already saturated. Falls
    back to fewest-Fassungen order when no Übergangsraum table exists.
    """
    forms = {e["word"]: e.get("fugen") or e["word"] for e in pool_entries()}
    accepted_count = {
        sid: sum(1 for f in kartei["strips"].get(sid, {}).get("fassungen", []) if f["status"] == "angenommen")
        for sid in ordered
    }
    try:
        universe = load_universe()
    except SystemExit:
        return sorted(ordered, key=lambda s: (accepted_count[s], int(s[1:])))
    weights, targets = soll_model(universe["items"])
    max_weight = max(weights.values(), default=1.0) or 1.0
    ist: dict[str, int] = {}
    for strip, _fassung in accepted_fassungen(kartei):
        for word in plan["strips"][strip]["words"]:
            for item in coverage.word_items(forms.get(word, word)):
                ist[item] = ist.get(item, 0) + 1

    def gain(sid: str) -> float:
        total = 0.0
        for word in plan["strips"][sid]["words"]:
            for item in coverage.word_items(forms.get(word, word)):
                if ist.get(item, 0) < targets[item]:
                    total += weights[item] / max_weight
        return total

    return sorted(ordered, key=lambda s: (-gain(s), accepted_count[s], int(s[1:])))


def select_strips(plan: dict, kartei: dict, rows: int, repeat: int) -> list[str]:
    """The print queue: redo > never recorded (plan order) > weighted repetition gain."""
    queue: list[str] = [entry["strip"] for entry in kartei["redo"] if entry["strip"] in plan["strips"]]
    ordered = sorted(plan["strips"], key=lambda sid: int(sid[1:]))
    queue += [sid for sid in ordered if sid not in queue and strip_state(kartei, sid) == "geplant"]
    queue += [sid for sid in _repetition_ranking(plan, kartei, ordered) if sid not in queue]
    distinct = max(1, rows // repeat)
    picked = queue[:distinct]
    return [sid for sid in picked for _ in range(repeat)][:rows]


def build_layout(
    sheet_id: str, hand: str, style: str, strip_rows: list[str], plan: dict, date: str, hints: bool
) -> dict:
    """The layout sidecar — every mm the PDF draws and the importer registers."""
    preset = geometry.PRESETS[style]
    entries = {e["word"]: e for e in pool_entries()}
    pitch = geometry.row_pitch_mm(preset)
    attempts_total = {sid: strip_rows.count(sid) for sid in strip_rows}
    seen: dict[str, int] = {}

    rows = []
    for index, sid in enumerate(strip_rows):
        seen[sid] = seen.get(sid, 0) + 1
        words = plan["strips"][sid]["words"]
        band = geometry.row_band(preset, MARGIN_MM + index * pitch)
        boxes = [
            {
                "word": word,
                "label": hint_label(word, entries.get(word, {}).get("fugen")) if hints else word,
                "x0_mm": round(x0, 3),
                "x1_mm": round(x1, 3),
            }
            for word, (x0, x1) in zip(words, geometry.boxes_for_row(words, preset, MARGIN_MM), strict=True)
        ]
        rows.append(
            {
                "strip": sid,
                "attempt": seen[sid],
                "attempts": attempts_total[sid],
                "mark_mm": [round(v, 3) for v in geometry.mark_box(band)],
                "band_mm": {
                    "asc_top": round(band.asc_top, 3),
                    "waist": round(band.waist, 3),
                    "baseline": round(band.baseline, 3),
                    "desc_bot": round(band.desc_bot, 3),
                },
                "boxes": boxes,
            }
        )

    config = {"preset": asdict(preset), "margin_mm": MARGIN_MM, "advances": dict(sorted(geometry.ADVANCE_XH.items()))}
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:10]
    return {
        "format": LAYOUT_FORMAT,
        "sheet": sheet_id,
        "hand": hand,
        "style": style,
        "page_mm": {"width": geometry.A4_WIDTH_MM, "height": geometry.A4_HEIGHT_MM},
        "fiducials": {
            "size_mm": geometry.FIDUCIAL_SIZE_MM,
            "hole_mm": geometry.FIDUCIAL_HOLE_MM,
            "donut": geometry.FIDUCIAL_DONUT,
            "centers_mm": {k: list(v) for k, v in geometry.FIDUCIAL_CENTERS.items()},
        },
        "rows": rows,
        "provenance": {
            "date": date,
            "commit": _git_commit(),
            "config_hash": config_hash,
            "streifen_sha256": hashlib.sha256(STREIFEN_JSON.read_bytes()).hexdigest(),
        },
    }


def render_pdf(layout: dict) -> bytes:
    """The printable Bogen from its layout sidecar (same numbers, one source)."""
    style = geometry.ROLE_STYLES
    preset = geometry.PRESETS[layout["style"]]
    rects: list[pdfgen.Rect] = []
    lines: dict[str, list[pdfgen.Line]] = {
        role: [] for role in ("slant", "ascender", "descender", "waist", "baseline", "box")
    }
    texts: list[pdfgen.Text] = []

    # Passmarken: solid squares, the donut gets a white hole on top.
    fid = layout["fiducials"]
    half = fid["size_mm"] / 2
    for corner, (cx, cy) in fid["centers_mm"].items():
        rects.append(pdfgen.Rect(cx - half, cy - half, fid["size_mm"], fid["size_mm"], "#000000"))
        if corner == fid["donut"]:
            hole = fid["hole_mm"] / 2
            rects.append(pdfgen.Rect(cx - hole, cy - hole, fid["hole_mm"], fid["hole_mm"], "#FFFFFF"))

    display = {"kurrent": "Kurrent", "suetterlin": "Sütterlin", "offenbacher": "Offenbacher"}[layout["style"]]
    sheet_no = int(layout["sheet"][1:])
    machine_id = f"{layout['hand']}-{layout['sheet']}"
    texts.append(pdfgen.Text(MARGIN_MM, 11.0, HEADER_SIZE_MM, f"{display} · Bogen {sheet_no}", style["meta"][0]))
    right_header = f"{machine_id} · {layout['provenance']['date']}"
    header_x = geometry.A4_WIDTH_MM - MARGIN_MM - pdfgen.helv_width_mm(right_header, HEADER_SIZE_MM)
    texts.append(pdfgen.Text(header_x, 11.0, HEADER_SIZE_MM, right_header, style["meta"][0]))
    # Column caption for the verdict boxes, printed once above the first row.
    if layout["rows"]:
        caption_y = layout["rows"][0]["band_mm"]["asc_top"] - 1.5
        rect = layout["rows"][0]["mark_mm"]
        centre = (rect[0] + rect[2]) / 2 - pdfgen.helv_width_mm(MARK_CAPTION, MARK_CAPTION_SIZE_MM) / 2
        texts.append(pdfgen.Text(centre, caption_y, MARK_CAPTION_SIZE_MM, MARK_CAPTION, style["meta"][0]))

    for row in layout["rows"]:
        band = row["band_mm"]
        row_id = row["strip"] if row["attempts"] == 1 else f"{row['strip']} ({row['attempt']}/{row['attempts']})"
        texts.append(pdfgen.Text(2.0, band["baseline"], ROW_ID_SIZE_MM, row_id, style["meta"][0]))
        for box in row["boxes"]:
            x0, x1 = box["x0_mm"], box["x1_mm"]
            top = band["asc_top"] - geometry.BOX_OVERHANG_MM
            bot = band["desc_bot"] + geometry.BOX_OVERHANG_MM
            for role, y in (
                ("ascender", band["asc_top"]),
                ("waist", band["waist"]),
                ("baseline", band["baseline"]),
                ("descender", band["desc_bot"]),
            ):
                color, width, dash = style[role]
                lines[role].append(pdfgen.Line(x0, y, x1, y, color, width, dash))
            color, width, dash = style["box"]
            lines["box"] += [
                pdfgen.Line(x0, top, x0, bot, color, width, dash),
                pdfgen.Line(x1, top, x1, bot, color, width, dash),
            ]
            if preset.show_slant:
                s_color, s_width, s_dash = style["slant"]
                dx = (bot - top) * math.tan(math.radians(90 - preset.slant_deg))
                xb = x0 - abs(dx)
                while xb <= x1 + abs(dx):
                    clipped = geometry.clip_to_rect(xb, bot, xb + dx, top, x0, top, x1, bot)
                    if clipped:
                        lines["slant"].append(pdfgen.Line(*clipped, s_color, s_width, s_dash))
                    xb += preset.slant_spacing_mm
            label_x = (x0 + x1) / 2 - pdfgen.helv_width_mm(box["label"], LABEL_SIZE_MM) / 2
            texts.append(pdfgen.Text(label_x, band["desc_bot"] + 4.0, LABEL_SIZE_MM, box["label"], style["label"][0]))
        # Verdict box in the right margin — tick it with the pen right after
        # writing the row; the importer reads it at Siebung time.
        mark_color, mark_width, _mark_dash = style["box"]
        mx0, my0, mx1, my1 = row["mark_mm"]
        lines["box"] += [
            pdfgen.Line(mx0, my0, mx1, my0, mark_color, mark_width, None),
            pdfgen.Line(mx1, my0, mx1, my1, mark_color, mark_width, None),
            pdfgen.Line(mx1, my1, mx0, my1, mark_color, mark_width, None),
            pdfgen.Line(mx0, my1, mx0, my0, mark_color, mark_width, None),
        ]

    prov = layout["provenance"]
    footer_left = f"kurrentschrift eigenhand · {prov['commit'] or 'no-commit'} · cfg {prov['config_hash']}"
    texts.append(pdfgen.Text(MARGIN_MM, geometry.A4_HEIGHT_MM - 9.0, FOOTER_SIZE_MM, footer_left, style["meta"][0]))
    footer_right = machine_id
    footer_x = geometry.A4_WIDTH_MM - MARGIN_MM - pdfgen.helv_width_mm(footer_right, FOOTER_SIZE_MM)
    texts.append(pdfgen.Text(footer_x, geometry.A4_HEIGHT_MM - 9.0, FOOTER_SIZE_MM, footer_right, style["meta"][0]))

    ordered_lines = [
        line for role in ("slant", "ascender", "descender", "waist", "baseline", "box") for line in lines[role]
    ]
    return pdfgen.build_pdf(rects, ordered_lines, texts)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True, help="hand id, e.g. mn-suetterlin")
    ap.add_argument("--style", default=None, help="style id (default: inferred from the hand id)")
    ap.add_argument("--rows", type=int, default=None, help="rows on the sheet (default: what fits, breathing)")
    ap.add_argument("--repeat", type=int, default=1, help="print each selected strip K times (attempts)")
    ap.add_argument("--strips", nargs="*", default=None, help="explicit strip ids (override the queue; may repeat)")
    ap.add_argument("--date", required=True, help="print date, ISO (explicit for deterministic output)")
    ap.add_argument("--no-hints", action="store_true", help="plain word labels without the Fugen hint form")
    args = ap.parse_args(argv)

    style = args.style or style_of_hand(args.hand)
    if style not in geometry.PRESETS:
        raise SystemExit(f"unknown style {style!r}")
    plan = load_plan(STREIFEN_JSON)
    kartei = load_kartei(args.hand, style)
    rows = args.rows or geometry.max_rows(geometry.PRESETS[style], MARGIN_MM)

    if args.strips:
        unknown = [sid for sid in args.strips if sid not in plan["strips"]]
        if unknown:
            raise SystemExit(f"unknown strips: {', '.join(unknown)}")
        strip_rows = args.strips[:rows]
    else:
        strip_rows = select_strips(plan, kartei, rows, max(1, args.repeat))
    if not strip_rows:
        raise SystemExit("nothing to print — the plan has no strips")

    sheet_id = next_sheet_id(kartei)
    layout = build_layout(sheet_id, args.hand, style, strip_rows, plan, args.date, not args.no_hints)
    pdf = render_pdf(layout)

    out_dir = hand_dir(args.hand) / "blaetter" / sheet_id
    out_dir.mkdir(parents=True, exist_ok=True)
    layout_text = json.dumps(layout, ensure_ascii=False, indent=1) + "\n"
    (out_dir / "layout.json").write_text(layout_text, encoding="utf-8")
    (out_dir / "bogen.pdf").write_bytes(pdf)

    kartei["sheets"][sheet_id] = {
        "printed": args.date,
        "strips": strip_rows,
        "layout_sha256": hashlib.sha256(layout_text.encode()).hexdigest(),
        "scans": [],
    }
    save_kartei(args.hand, kartei)
    print(f"wrote {out_dir / 'bogen.pdf'} ({len(pdf):,} bytes), {len(layout['rows'])} rows: {' '.join(strip_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
