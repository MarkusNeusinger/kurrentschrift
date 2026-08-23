"""Ingest one capture of a printed Bogen: rectify, cut rows, build the payload.

Pipeline (proposal §6): load the scan/photo (grayscale) → detect the four
Passmarken (fiducial.py) → orient by the donut → estimate the homography
against the layout sidecar's mm centers → warp into mm-space at the working
resolution (300 DPI: a 6 mm x-height lands at ~71 px, the mvp-roadmap M1
floor) → cut one strip crop per row plus per-box QC flags → write the
review payload the Siebung page renders.

QC flags (``leer`` · ``beschnitten`` · ``blass``) are WARNINGS, never
auto-verdicts — auto-rejecting would be exactly the selective drop the
Sieb-Disziplin forbids; the human decides on the page.

The crops stay unmodified grayscale (two-channel doctrine: binarisation is
downstream derivation, never baked into the stored strip).

    uv run python -m tools.eigenhand.ingest --hand mn-suetterlin --sheet B0001 scan.jpg \
        --feder "Brause 511" --tinte "Eisengallus" --papier "90g" --geraet scanner
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from skimage import transform

from core.extract import load_grayscale
from tools.eigenhand.fiducial import FiducialError, detect_fiducials, orient_corners
from tools.eigenhand.store import crop_name as row_crop_name
from tools.eigenhand.store import hand_dir


PAYLOAD_FORMAT = 1
WORK_DPI = 300.0
PX_PER_MM = WORK_DPI / 25.4
ROW_PAD_MM = 2.0
# The stored strip is SELF-ATTRIBUTING pixels: it starts left of the printed
# row id (x = 2 mm) and reaches below the clear-text label zone, so a strip
# PNG names itself and its words even with every sidecar lost. QC still runs
# on the writing band only (printed text must not fake ink flags).
STRIP_X0_MM = 1.0
STRIP_LABEL_BELOW_MM = 5.0
LINE_MASK_MM = 0.4  # printed-geometry mask half-width for the QC ink measure
INK_THRESHOLD = 0.55  # grayscale below this counts as ink for the QC flags
# The rulings are printed in pale cyan (geometry.CAPTURE_STYLES). Cyan's blue
# component is nearly paper (0.93), so reading a COLOUR capture through its
# blue channel drops the guide lines out of the image altogether — no
# threshold, no masking, nothing left to subtract later. Ink survives it:
# black 0.10, iron-gall brown 0.14, even blue ink 0.55 at the very edge —
# which is why the sheet asks for black or brown ink, not blue.
CHANNELS = {"blau": 2, "gruen": 1, "rot": 0}
MIN_DPI_WARN = 250.0
LEER_MIN_INK_PX = 40
# Verdict box (geometry.mark_box): a tick covers a good part of the box, a
# stray speck does not. Measured on the INNER area only, so the printed
# outline itself can never read as a mark.
MARK_INSET_MM = 0.9
MARK_MIN_FRACTION = 0.04


def _mm(px_value: float) -> float:
    return px_value / PX_PER_MM


def _px(mm_value: float) -> int:
    return round(mm_value * PX_PER_MM)


def load_capture(path: Path, channel: str = "auto") -> tuple[np.ndarray, str]:
    """Load a capture as float32 [0,1], dropping the cyan rulings when possible.

    ``auto`` takes the blue channel of a colour capture — where the pale cyan
    rulings sit at paper level — and falls back to plain grayscale for a
    greyscale scan, where the channels no longer exist. Returns the plane and
    the name of what was used, so the payload can record it.
    """
    image = Image.open(path)
    if channel != "grau" and image.mode not in ("L", "1", "I;16"):
        index = CHANNELS["blau"] if channel == "auto" else CHANNELS[channel]
        plane = np.asarray(image.convert("RGB"), dtype=np.float32)[:, :, index] / 255.0
        return plane, ("blau" if channel == "auto" else channel)
    return load_grayscale(str(path)), "grau"


def rectify(gray: np.ndarray, layout: dict) -> tuple[np.ndarray, float, dict[str, tuple[float, float]]]:
    """Warp the capture into mm-space at WORK_DPI; returns (image, dpi_estimate, marks)."""
    corners = orient_corners(detect_fiducials(gray))
    centers_mm = layout["fiducials"]["centers_mm"]
    src = np.array([[centers_mm[c][0] * PX_PER_MM, centers_mm[c][1] * PX_PER_MM] for c in ("tl", "tr", "bl", "br")])
    dst = np.array([list(corners[c].center) for c in ("tl", "tr", "bl", "br")])

    # Effective capture resolution from the fiducial spacing (before warping).
    mm_dist = []
    px_dist = []
    keys = ("tl", "tr", "bl", "br")
    for i in range(4):
        for j in range(i + 1, 4):
            a, b = centers_mm[keys[i]], centers_mm[keys[j]]
            mm_dist.append(float(np.hypot(a[0] - b[0], a[1] - b[1])))
            pa, pb = corners[keys[i]].center, corners[keys[j]].center
            px_dist.append(float(np.hypot(pa[0] - pb[0], pa[1] - pb[1])))
    dpi_estimate = float(np.mean([p / m for p, m in zip(px_dist, mm_dist, strict=True)]) * 25.4)

    tform = transform.ProjectiveTransform.from_estimate(src, dst)
    if not tform:
        raise FiducialError("homography estimation failed on the detected fiducials")
    out_shape = (_px(layout["page_mm"]["height"]), _px(layout["page_mm"]["width"]))
    warped = transform.warp(gray, tform, output_shape=out_shape, order=3, mode="constant", cval=1.0)
    marks = {k: corners[k].center for k in keys}
    return warped.astype(np.float32), dpi_estimate, marks


def _printed_mask(shape: tuple[int, int], row: dict, x0_px: int, y0_px: int) -> np.ndarray:
    """True where the crop shows PRINTED geometry (guide lines, box edges, row id)."""
    mask = np.zeros(shape, dtype=bool)
    band = row["band_mm"]
    half = _px(LINE_MASK_MM)
    # Everything above the ascender line is printed matter, not handwriting:
    # that frame carries the strip id sheet.py prints in the Schnittband's top
    # pad. Counting its pixels would fake ink and suppress the `leer` flag.
    above_band = _px(band["asc_top"]) - y0_px - half
    if above_band > 0:
        mask[:above_band, :] = True
    for box in row["boxes"]:
        bx0, bx1 = _px(box["x0_mm"]) - x0_px, _px(box["x1_mm"]) - x0_px
        for y_mm in (band["asc_top"], band["waist"], band["baseline"], band["desc_bot"]):
            y = _px(y_mm) - y0_px
            mask[max(0, y - half) : y + half + 1, max(0, bx0 - half) : bx1 + half + 1] = True
        for x in (bx0, bx1):
            mask[:, max(0, x - half) : x + half + 1] = True
    return mask


def qc_flags(crop: np.ndarray, row: dict, x0_px: int, y0_px: int) -> list[str]:
    ink = (crop < INK_THRESHOLD) & ~_printed_mask(crop.shape, row, x0_px, y0_px)
    flags: list[str] = []
    if int(ink.sum()) < LEER_MIN_INK_PX:
        flags.append("leer")
        return flags
    edge = np.zeros_like(ink)
    margin = _px(0.8)
    edge[:margin, :] = edge[-margin:, :] = edge[:, :margin] = edge[:, -margin:] = True
    if bool((ink & edge).any()):
        flags.append("beschnitten")
    if float(crop[ink].mean()) > 0.45:
        flags.append("blass")
    return flags


def read_pen_mark(warped: np.ndarray, row: dict) -> str | None:
    """The writer's own tick for one row, read off the rectified page.

    One box per row (owner, 2026-08-23): a cross or check in it means
    ``angenommen``, an empty box ``verworfen``. Unlike the QC flags this DOES
    pre-fill the Siebung — the tick is a human judgement made at the best
    possible moment, right after the row was written — and the review page
    still lets it be overridden. A layout without a mark box (a sheet printed
    before the boxes existed) yields ``None``: undecided, as before.
    """
    rect = row.get("mark_mm")
    if not rect:
        return None
    x0, y0, x1, y1 = rect
    inset = _px(MARK_INSET_MM)
    patch = warped[_px(y0) + inset : _px(y1) - inset, _px(x0) + inset : _px(x1) - inset]
    fraction = float((patch < INK_THRESHOLD).mean()) if patch.size else 0.0
    return "angenommen" if fraction >= MARK_MIN_FRACTION else "verworfen"


def build_payload(
    hand: str,
    sheet: str,
    layout: dict,
    warped: np.ndarray,
    scan: Path,
    session: dict,
    dpi: float,
    keep_scan: bool = False,
    channel: str = "grau",
) -> dict:
    sheet_dir = hand_dir(hand) / "blaetter" / sheet
    import_dir = sheet_dir / "import"
    import_dir.mkdir(parents=True, exist_ok=True)

    rows_out = []
    for index, row in enumerate(layout["rows"]):
        band = row["band_mm"]
        # Crop bounds come from the row's Schnittband — layout.json is the SOLE
        # geometry contract, no margin constant duplicated here (Copilot
        # finding, PR #406). Cropping exactly where the scissors go makes the
        # digital strip and the paper strip the same object, and every filed
        # streifen.png of a style comes out at identical pixel dimensions.
        boxes_x0 = min(box["x0_mm"] for box in row["boxes"])
        boxes_x1 = max(box["x1_mm"] for box in row["boxes"])
        cut = row.get("cut_mm")
        if cut:
            x0_px, y0_px, x1_px, y1_px = (_px(cut[0]), _px(cut[1]), _px(cut[2]), _px(cut[3]))
        else:  # a sheet printed before the Schnittband existed
            x0_px = _px(STRIP_X0_MM)
            x1_px = _px(boxes_x1 + ROW_PAD_MM)
            y0_px = _px(band["asc_top"] - ROW_PAD_MM)
            y1_px = _px(band["desc_bot"] + STRIP_LABEL_BELOW_MM)
        crop = warped[y0_px:y1_px, x0_px:x1_px]
        # QC runs on the writing band only — the printed row id and labels in
        # the wider strip must not fake ink flags. It therefore has its OWN
        # origin: the Schnittband reaches further up and down than this.
        qx0_px = _px(boxes_x0 - ROW_PAD_MM)
        qy0_px = _px(band["asc_top"] - ROW_PAD_MM)
        qy1_px = _px(band["desc_bot"] + ROW_PAD_MM)
        qc_crop = warped[qy0_px:qy1_px, qx0_px : _px(boxes_x1 + ROW_PAD_MM)]
        pen_mark = read_pen_mark(warped, row)
        crop_name = row_crop_name(index)
        Image.fromarray((np.clip(crop, 0.0, 1.0) * 255).astype(np.uint8), mode="L").save(import_dir / crop_name)
        rows_out.append(
            {
                "uid": f"{sheet}-r{index:02d}",
                "row_index": index,
                "strip": row["strip"],
                "attempt": row["attempt"],
                "attempts": row["attempts"],
                "words": [box["word"] for box in row["boxes"]],
                "qc": qc_flags(qc_crop, row, qx0_px, qy0_px),
                "pen_mark": pen_mark,
                "crop": crop_name,
                "crop_origin_mm": [round(_mm(x0_px), 3), round(_mm(y0_px), 3)],
            }
        )

    header = warped[0 : _px(14.0), :]
    Image.fromarray((np.clip(header, 0.0, 1.0) * 255).astype(np.uint8), mode="L").save(import_dir / "header.png")
    preview = Image.fromarray((np.clip(warped, 0.0, 1.0) * 255).astype(np.uint8), mode="L")
    preview.thumbnail((900, 1300))
    preview.save(import_dir / "page.png")

    # Filed are only the relevant strips (owner decision) — the full-page scan
    # is NOT kept unless asked for; its checksum stays recorded regardless.
    if keep_scan:
        scan_copy = sheet_dir / "scans" / scan.name
        scan_copy.parent.mkdir(parents=True, exist_ok=True)
        if not scan_copy.exists():
            shutil.copy2(scan, scan_copy)

    return {
        "format": PAYLOAD_FORMAT,
        "hand": hand,
        "sheet": sheet,
        "style": layout["style"],
        "rows": rows_out,
        "session": session,
        "scan": {
            "file": scan.name,
            "sha256": hashlib.sha256(scan.read_bytes()).hexdigest(),
            "dpi_estimate": round(dpi, 1),
            "channel": channel,  # which plane the strips were cut from
        },
        "layout_provenance": layout["provenance"],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("scan", type=Path, help="capture file (PNG/JPEG/TIFF; export HEIC as JPEG first)")
    ap.add_argument("--hand", required=True)
    ap.add_argument("--sheet", required=True, help="sheet id, e.g. B0001 (printed in the header)")
    ap.add_argument("--feder", default="", help="nib used in this Schreibsitzung")
    ap.add_argument("--tinte", default="", help="ink")
    ap.add_argument("--papier", default="", help="paper")
    ap.add_argument("--geraet", default="scanner", choices=("scanner", "kamera"), help="capture device")
    # --datum stays as an alias: the family's other tools were written with it,
    # and the English spelling is the one the language rules ask for.
    ap.add_argument(
        "--date", "--datum", dest="date", default="", help="session date, ISO (default: the sheet's print date)"
    )
    ap.add_argument("--keep-scan", action="store_true", help="also keep the full-page scan under scans/")
    ap.add_argument(
        "--channel",
        choices=["auto", "blau", "gruen", "rot", "grau"],
        default="auto",
        help="colour plane to read (default: blue for a colour capture — drops the cyan rulings)",
    )
    args = ap.parse_args(argv)

    layout_path = hand_dir(args.hand) / "blaetter" / args.sheet / "layout.json"
    if not layout_path.exists():
        raise SystemExit(f"{layout_path} missing — was sheet {args.sheet} generated for hand {args.hand}?")
    layout = json.loads(layout_path.read_text(encoding="utf-8"))

    gray, channel_used = load_capture(args.scan, args.channel)
    if channel_used == "grau":
        print("note: greyscale capture — the cyan rulings stay in the image (scan in colour to drop them)")
    try:
        warped, dpi, _marks = rectify(gray, layout)
    except FiducialError:
        raise
    if dpi < MIN_DPI_WARN:
        print(f"WARNING: effective capture resolution ~{dpi:.0f} DPI is under {MIN_DPI_WARN:.0f} — rescan if possible")

    session = {
        "date": args.date or layout["provenance"]["date"],
        "feder": args.feder,
        "tinte": args.tinte,
        "papier": args.papier,
        "geraet": args.geraet,
    }
    payload = build_payload(
        args.hand, args.sheet, layout, warped, args.scan, session, dpi, args.keep_scan, channel_used
    )
    import_dir = hand_dir(args.hand) / "blaetter" / args.sheet / "import"
    (import_dir / "payload.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ticked = sum(1 for row in payload["rows"] if row.get("pen_mark") == "angenommen")
    flagged = sum(1 for row in payload["rows"] if row["qc"])
    print(
        f"wrote {import_dir / 'payload.json'}: {len(payload['rows'])} rows, {ticked} ticked ok on the sheet, "
        f"{flagged} with QC flags (~{dpi:.0f} DPI)"
    )
    print(f"next: uv run python -m tools.eigenhand.page --hand {args.hand} --sheet {args.sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
