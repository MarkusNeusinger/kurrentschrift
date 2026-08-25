"""Compose a Bogen — one A4 training sheet of pending Streifen.

Two pure steps, no I/O: ``select_strips`` picks the rows, ``build_layout``
turns them into millimetres and ``render_pdf`` into bytes. Who stores the
result — the local CLI under ``tools/eigenhand/sheet.py`` writing
``bogen.pdf`` + ``layout.json`` into the data root, or the API writing the
sheet row into ``eigenhand_sheets`` — is the caller's business.

Selection order of the print queue (proposal §5): redo-queue entries first,
then never-recorded strips in plan order (preserving the wave's coverage
velocity), then repetition candidates. With Übergangsraum weights the
repetition candidates are ranked by the Soll gain of one more Fassung;
without them (the server has no local weight table) by fewest Fassungen —
the same order, minus the frequency preference.

The ``layout`` this builds is the importer's SOLE geometry contract (mm
coordinates of Passmarken, rows and boxes; registration instead of
detection), which is why it is also what gets stored rather than the PDF:
the bytes are reproducible from it, the geometry is not reproducible from
the bytes.

Clear-text labels are plain Latin (legibility doctrine; WinAnsi has no ſ).
A label shows the Fugen hint form where one exists (``Amts*|zeit``: ``*`` =
round s forced at the boundary) — the one case where shaping deviates from
the default rules the writer learns once.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import asdict

from core.config import REPO_ROOT
from core.eigenhand import coverage, geometry, pdfgen
from core.eigenhand.kartei import accepted_fassungen, next_sheet_id, strip_state
from core.eigenhand.plan import STREIFEN_JSON, ordered_strips, shaping_form_of


LAYOUT_FORMAT = 1
MARGIN_MM = 15.0
ROW_ID_SIZE_MM = 2.2
LABEL_SIZE_MM = 3.0
# Distance of the two printed captions from the writing band. Both moved away
# from it on 2026-08-23 without the strip growing (see geometry's pads): the
# id from 1.2 to 1.7 mm above the ascender line, the word from 4.0 to 4.6 mm
# below the descender line, so neither crowds the letters that reach for them.
ROW_ID_GAP_MM = 1.7
LABEL_GAP_MM = 4.6
HEADER_SIZE_MM = 3.5
FOOTER_SIZE_MM = 2.8
MARK_CAPTION_SIZE_MM = 2.4
MARK_CAPTION = "ok"  # one box per row: ticked = ok, empty = not ok
# The label hints, spelled out on the sheet (owner asked what Donners*|tag
# means — if it needs asking, it needs printing).
LEGEND = "| = Wortfuge (zusammengesetztes Wort)   * = rundes s statt langem ſ"


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


def _repetition_ranking(
    plan: dict, kartei: dict, ordered: list[str], soll: tuple[dict[str, float], dict[str, int]] | None
) -> list[str]:
    """Already-recorded strips ranked by the weighted Soll gain of one more Fassung.

    "Which strips should be written more often because their words are so
    frequent" (owner, 2026-08-22): a strip whose words carry frequent items
    with open Soll outranks one whose items are already saturated. Falls
    back to fewest-Fassungen order when the caller has no Übergangsraum
    table — which is the server's normal case: the weights are derived from
    consult-only corpora and stay on the machine that built them.
    """
    accepted_count = {
        sid: sum(1 for f in kartei["strips"].get(sid, {}).get("fassungen", []) if f["status"] == "angenommen")
        for sid in ordered
    }
    if soll is None:
        return sorted(ordered, key=lambda s: (accepted_count[s], int(s[1:])))
    weights, targets = soll
    max_weight = max(weights.values(), default=1.0) or 1.0
    ist: dict[str, int] = {}
    for strip, _fassung in accepted_fassungen(kartei):
        for word in plan["strips"][strip]["words"]:
            for item in coverage.word_items(shaping_form_of(plan, word)):
                ist[item] = ist.get(item, 0) + 1

    def gain(sid: str) -> float:
        total = 0.0
        for word in plan["strips"][sid]["words"]:
            for item in coverage.word_items(shaping_form_of(plan, word)):
                if ist.get(item, 0) < targets.get(item, 0):
                    total += weights.get(item, 0.0) / max_weight
        return total

    return sorted(ordered, key=lambda s: (-gain(s), accepted_count[s], int(s[1:])))


def select_strips(
    plan: dict, kartei: dict, rows: int, repeat: int, soll: tuple[dict[str, float], dict[str, int]] | None = None
) -> list[str]:
    """The print queue: redo > never recorded (plan order) > repetition gain."""
    queue: list[str] = [entry["strip"] for entry in kartei["redo"] if entry["strip"] in plan["strips"]]
    ordered = ordered_strips(plan)
    queue += [sid for sid in ordered if sid not in queue and strip_state(kartei, sid) == "geplant"]
    queue += [sid for sid in _repetition_ranking(plan, kartei, ordered, soll) if sid not in queue]
    distinct = max(1, rows // repeat)
    picked = queue[:distinct]
    return [sid for sid in picked for _ in range(repeat)][:rows]


def build_layout(
    sheet_id: str, hand: str, style: str, strip_rows: list[str], plan: dict, date: str, hints: bool
) -> dict:
    """The layout sidecar — every mm the PDF draws and the importer registers."""
    preset = geometry.PRESETS[style]
    pitch = geometry.row_pitch_mm(preset)
    attempts_total = {sid: strip_rows.count(sid) for sid in strip_rows}
    seen: dict[str, int] = {}

    # The plan's own fugen table: the form each word is asked to be written as,
    # which is what the box has to be wide enough for. It is the same table the
    # label is built from two lines below — one source, no drift.
    forms = plan.get("forms", {})

    rows = []
    for index, sid in enumerate(strip_rows):
        seen[sid] = seen.get(sid, 0) + 1
        words = plan["strips"][sid]["words"]
        band = geometry.row_band(preset, geometry.TOP_MARGIN_MM + index * pitch)
        boxes = [
            {
                "word": word,
                "label": hint_label(word, forms.get(word)) if hints else word,
                "x0_mm": round(x0, 3),
                "x1_mm": round(x1, 3),
            }
            for word, (x0, x1) in zip(words, geometry.boxes_for_row(words, preset, MARGIN_MM, forms), strict=True)
        ]
        rows.append(
            {
                "strip": sid,
                "attempt": seen[sid],
                "attempts": attempts_total[sid],
                "mark_mm": [round(v, 3) for v in geometry.mark_box(band)],
                "cut_mm": [round(v, 3) for v in geometry.cut_box(band)],
                "band_mm": {
                    "asc_top": round(band.asc_top, 3),
                    "waist": round(band.waist, 3),
                    "baseline": round(band.baseline, 3),
                    "desc_bot": round(band.desc_bot, 3),
                },
                "boxes": boxes,
            }
        )

    # The fingerprint has to cover EVERY constant that moves a printed box —
    # the per-key advances plus the fallbacks they fall back to and the two
    # spacings — otherwise a changed width model prints different geometry
    # under an unchanged `cfg` stamp.
    config = {
        "preset": asdict(preset),
        "margin_mm": MARGIN_MM,
        "advances": dict(sorted(geometry.ADVANCE_XH.items())),
        "advance_default_xh": geometry.ADVANCE_DEFAULT_XH,
        "advance_capital_xh": geometry.ADVANCE_CAPITAL_XH,
        "box_lead_mm": geometry.BOX_LEAD_MM,
        "box_gap_mm": geometry.BOX_GAP_MM,
    }
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
    style = geometry.CAPTURE_STYLES  # faint rulings, not the app's reading theme
    preset = geometry.PRESETS[layout["style"]]
    rects: list[pdfgen.Rect] = []
    lines: dict[str, list[pdfgen.Line]] = {
        role: [] for role in ("slant", "ascender", "descender", "waist", "baseline", "box", "cut")
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
    # Column caption for the verdict boxes, printed once ABOVE the first cut
    # line (owner, 2026-08-23) — sitting below it would put the caption level
    # with the first strip, where it reads as belonging to that row.
    if layout["rows"]:
        first = layout["rows"][0]
        caption_y = (first["cut_mm"][1] if first.get("cut_mm") else first["band_mm"]["asc_top"]) - 1.5
        rect = layout["rows"][0]["mark_mm"]
        centre = (rect[0] + rect[2]) / 2 - pdfgen.helv_width_mm(MARK_CAPTION, MARK_CAPTION_SIZE_MM) / 2
        texts.append(pdfgen.Text(centre, caption_y, MARK_CAPTION_SIZE_MM, MARK_CAPTION, style["meta"][0]))

    for row in layout["rows"]:
        band = row["band_mm"]
        row_id = row["strip"] if row["attempts"] == 1 else f"{row['strip']} ({row['attempt']}/{row['attempts']})"
        # The id rides in the Schnittband's top pad, INSIDE the strip: a cut
        # strip has to stay attributable on its own (proposal §7).
        cut = row.get("cut_mm")
        id_x, id_y = (cut[0] + 1.5, band["asc_top"] - ROW_ID_GAP_MM) if cut else (2.0, band["baseline"])
        texts.append(pdfgen.Text(id_x, id_y, ROW_ID_SIZE_MM, row_id, style["meta"][0]))
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
            label_y = band["desc_bot"] + LABEL_GAP_MM
            texts.append(pdfgen.Text(label_x, label_y, LABEL_SIZE_MM, box["label"], style["label"][0]))
        # Schnittmarken: four ticks in the margins, never inside the strip.
        cut_color, cut_width, _cut_dash = style["cut"]
        for tx0, ty0, tx1, ty1 in geometry.cut_ticks(tuple(cut)) if cut else ():
            lines["cut"].append(pdfgen.Line(tx0, ty0, tx1, ty1, cut_color, cut_width, None))

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

    # The two vertical cut lines are the same for every row, so they are marked
    # once above the first and once below the last strip.
    cut_color, cut_width, _cut_dash = style["cut"]
    page_cuts = [tuple(row["cut_mm"]) for row in layout["rows"] if row.get("cut_mm")]
    for tx0, ty0, tx1, ty1 in geometry.page_cut_ticks(page_cuts):
        lines["cut"].append(pdfgen.Line(tx0, ty0, tx1, ty1, cut_color, cut_width, None))

    # Legend for the two hint marks in the labels — they are the ONE place the
    # sheet asks for something the default shaping rules do not give, so the
    # sheet has to say what they mean rather than assume the writer remembers.
    if any(any(mark in box["label"] for mark in ("*", "|")) for row in layout["rows"] for box in row["boxes"]):
        texts.append(pdfgen.Text(MARGIN_MM, geometry.A4_HEIGHT_MM - 14.0, FOOTER_SIZE_MM, LEGEND, style["meta"][0]))

    prov = layout["provenance"]
    footer_left = f"kurrentschrift eigenhand · {prov['commit'] or 'no-commit'} · cfg {prov['config_hash']}"
    texts.append(pdfgen.Text(MARGIN_MM, geometry.A4_HEIGHT_MM - 9.0, FOOTER_SIZE_MM, footer_left, style["meta"][0]))
    footer_right = machine_id
    footer_x = geometry.A4_WIDTH_MM - MARGIN_MM - pdfgen.helv_width_mm(footer_right, FOOTER_SIZE_MM)
    texts.append(pdfgen.Text(footer_x, geometry.A4_HEIGHT_MM - 9.0, FOOTER_SIZE_MM, footer_right, style["meta"][0]))

    ordered_lines = [
        line for role in ("slant", "ascender", "descender", "waist", "baseline", "box", "cut") for line in lines[role]
    ]
    return pdfgen.build_pdf(rects, ordered_lines, texts)


def layout_text(layout: dict) -> str:
    """The layout as it is stored — one spelling, so its SHA256 means one thing."""
    return json.dumps(layout, ensure_ascii=False, indent=1) + "\n"


def compose_sheet(
    *,
    plan: dict,
    kartei: dict,
    hand: str,
    style: str,
    date: str,
    rows: int | None = None,
    repeat: int = 1,
    strips: list[str] | None = None,
    hints: bool = True,
    soll: tuple[dict[str, float], dict[str, int]] | None = None,
) -> dict:
    """Compose ONE Bogen: pick the rows, mint the id, build the layout, render it.

    Pure: takes a plan and a Kartei-shaped dict, writes nothing. The CLI puts
    the result into the data root, the API into ``eigenhand_sheets`` — one
    composition path, or the two surfaces would drift apart in the one place
    where drift means paper that the importer cannot read.
    """
    if style not in geometry.PRESETS:
        raise SystemExit(f"unknown style {style!r}")
    rows = rows or geometry.max_rows(geometry.PRESETS[style], MARGIN_MM)

    if strips:
        unknown = [sid for sid in strips if sid not in plan["strips"]]
        if unknown:
            raise SystemExit(f"unknown strips: {', '.join(unknown)}")
        strip_rows = strips[:rows]
    else:
        strip_rows = select_strips(plan, kartei, rows, max(1, repeat), soll)
    if not strip_rows:
        raise SystemExit("nothing to print — the plan has no strips")

    sheet_id = next_sheet_id(kartei)
    layout = build_layout(sheet_id, hand, style, strip_rows, plan, date, hints)
    pdf = render_pdf(layout)
    return {
        "sheet": sheet_id,
        "layout": layout,
        "pdf": pdf,
        "strips": strip_rows,
        "layout_sha256": hashlib.sha256(layout_text(layout).encode()).hexdigest(),
    }
