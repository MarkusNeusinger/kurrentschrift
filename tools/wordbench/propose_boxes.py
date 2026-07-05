"""Propose word/pair boxes + per-line lineature for the specimen plates.

Reads the committed page PNGs and the words.json sidecar — no DB. The ink mask
is derived exactly like the exporter derives its frozen reference
(binarize_adaptive + despeckle), so proposed geometry matches what a later
export freezes. The proposer emits numbered box proposals in words.json shape
plus overlay verification sheets for the labeling/QC pass; ``--validate``
scores the proposer against the already-committed rects (IoU + lineature
error) instead of writing proposals.

Pipeline: horizontal ink projection -> line cores (the dense x-height band of
each handwriting line; the printed caption is rejected by taking the topmost
``--expect-lines`` bands) -> connected components assigned to lines ->
x-gap agglomeration into word/pair clusters -> per-cluster ink bbox. Lineature
(baseline/midband) comes from the line core edges, not per word, so tall
capitals don't bias the midband. Foreign ink from a neighbouring line that
falls inside a proposed rect becomes an ``exclude`` rect (the "zum" case);
small components at baseline level trailing a cluster are dropped as
punctuation (commas stay out of the crops — the stored word carries letters
only).

Usage:
    uv run python -m tools.wordbench.propose_boxes --page words-abb19.png --expect-lines 12
    uv run python -m tools.wordbench.propose_boxes --page pairs-abb20.png --expect-lines 4
    uv run python -m tools.wordbench.propose_boxes --page words-abb19.png --expect-lines 12 --validate
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import find_objects
from scipy.ndimage import label as cc_label

from core.extract import binarize_adaptive
from tools.wordbench.export_fixtures import DESPECKLE_MIN_AREA_PX, REPO_ROOT, _despeckle, _load_page


DEFAULT_SOURCE_ID = "suetterlin-1922"
DEFAULT_OUT_DIR = Path("temp") / "propose"

# Line-core detection: rows whose smoothed ink count reaches CORE_FRAC of the
# plate's robust row maximum form a line's dense x-height band. Calibrated via
# --validate against the 15 committed Abb.19 rects.
ROW_SMOOTH_PX = 9
CORE_FRAC = 0.30
CORE_MERGE_GAP_PX = 14  # close dips inside one x-height band (e.g. between thin joins)
# Real x-height cores measure 35–39 px on both plates; the i-dot/umlaut zone
# floating above a line forms its own thin band (~11 px) that must not count
# as a line, and the printed caption lines are 28–30 px.
CORE_MIN_H_PX = 22

# Cluster agglomeration: components on the same line whose horizontal gap is
# below GAP_PX belong to one word/pair. Measured on the 15 committed Abb.19
# rects: intra-word whitespace runs are 0 px (words are fully connected, even
# across pen-lift breaks the strokes overlap horizontally). Inter-word gaps
# shrink to ~6 px in the tightest lines (und→von, zwei→Spor'n on line 10),
# so the threshold sits just below that: 5 px reproduces the full 63-word
# count of the plate.
GAP_PX = 5
BOX_PAD_PX = 3

# The committed rects' hand-measured lineature sits a hair inside the detected
# core band (validated: Δbaseline +3/+4 px, Δmidband −2…−4 px raw). Trim to
# match the committed convention — the bench scales by baseline−midband.
BASELINE_TRIM_PX = 3
MIDBAND_TRIM_PX = 3

# Punctuation heuristic: a small component at the START or END of a cluster
# whose ink lies at/below the midband is a comma/period (dropped, reported);
# small components above the midband are diacritics (kept).
PUNCT_MAX_AREA_PX = 260
DIACRITIC_MAX_DIST_PX = 90  # max gap between a floating mark and the core below it


@dataclass
class LineBand:
    index: int
    core_y0: int  # top of the dense x-height band == proposed midband_y
    core_y1: int  # bottom of the dense x-height band == proposed baseline_y

    @property
    def midband_y(self) -> int:
        return self.core_y0 + MIDBAND_TRIM_PX

    @property
    def baseline_y(self) -> int:
        return self.core_y1 - BASELINE_TRIM_PX


@dataclass
class Component:
    x0: int
    y0: int
    x1: int  # exclusive
    y1: int  # exclusive
    area: int
    line: int | None = None


@dataclass
class Proposal:
    number: int
    line: int
    x0: int
    y0: int
    x1: int
    y1: int
    baseline_y: int
    midband_y: int
    exclude: list[list[int]] = field(default_factory=list)
    dropped_punct: list[list[int]] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


def detect_lines(mask: np.ndarray, expect_lines: int) -> list[LineBand]:
    """Find the dense x-height band of each handwriting line, top to bottom.

    The printed Fraktur caption sits below all handwriting on both plates, so
    keeping the topmost ``expect_lines`` bands rejects it without any font
    classification.
    """
    rows = mask.sum(axis=1).astype(np.float64)
    kernel = np.ones(ROW_SMOOTH_PX) / ROW_SMOOTH_PX
    smooth = np.convolve(rows, kernel, mode="same")
    # Robust normaliser: near-max row density without single-row outliers.
    scale = float(np.percentile(smooth[smooth > 0], 99)) if (smooth > 0).any() else 0.0
    if scale <= 0:
        raise SystemExit("no ink found on the page")
    core = smooth >= CORE_FRAC * scale

    runs: list[list[int]] = []
    y = 0
    while y < len(core):
        if core[y]:
            y1 = y
            while y1 + 1 < len(core) and core[y1 + 1]:
                y1 += 1
            runs.append([y, y1 + 1])
            y = y1 + 1
        y += 1
    # Merge dips inside one band, then drop slivers.
    merged: list[list[int]] = []
    for run in runs:
        if merged and run[0] - merged[-1][1] < CORE_MERGE_GAP_PX:
            merged[-1][1] = run[1]
        else:
            merged.append(run)
    bands = [r for r in merged if r[1] - r[0] >= CORE_MIN_H_PX]
    if len(bands) < expect_lines:
        raise SystemExit(f"found only {len(bands)} line bands, expected {expect_lines} — tune CORE_FRAC")
    if len(bands) > expect_lines:
        print(f"note: {len(bands)} bands found, keeping the topmost {expect_lines} (caption rejected)")
    return [LineBand(i, y0, y1) for i, (y0, y1) in enumerate(bands[:expect_lines])]


def extract_components(mask: np.ndarray) -> list[Component]:
    labels, n = cc_label(mask)
    if not n:
        return []
    comps: list[Component] = []
    slices = find_objects(labels)
    sizes = np.bincount(labels.ravel())
    for i, sl in enumerate(slices, start=1):
        if sl is None:
            continue
        ys, xs = sl
        comps.append(Component(xs.start, ys.start, xs.stop, ys.stop, int(sizes[i])))
    return comps


def assign_lines(comps: list[Component], lines: list[LineBand]) -> None:
    """Attach each component to a line: max core overlap, else the nearest core
    below the component (floating diacritics sit above their line)."""
    for c in comps:
        overlaps = [(min(c.y1, ln.core_y1) - max(c.y0, ln.core_y0), ln.index) for ln in lines]
        best_overlap, best_line = max(overlaps)
        if best_overlap > 0:
            c.line = best_line
            continue
        center = (c.y0 + c.y1) / 2
        below = [(ln.core_y0 - center, ln.index) for ln in lines if ln.core_y0 >= center]
        if below:
            dist, idx = min(below)
            if dist <= DIACRITIC_MAX_DIST_PX:
                c.line = idx
                continue
        # Anything farther than the diacritic range from every core is not part
        # of a handwriting line (printed caption, verso ghost) — leave it
        # unassigned instead of gluing it to the nearest line.
        c.line = None


def cluster_line(
    comps: list[Component], band: LineBand, page_shape: tuple[int, int], gap_px: int = GAP_PX
) -> list[Proposal]:
    """Agglomerate one line's components into word/pair clusters by x-gap.

    Punctuation is filtered BEFORE clustering: a comma sits between two words
    with sub-GAP_PX gaps on both sides and would otherwise bridge them into
    one cluster. Small marks above the midband are diacritics (i-dots, umlaut
    breves, apostrophes) and stay — they overlap their word's x-range.
    """
    own = sorted((c for c in comps if c.line == band.index), key=lambda c: c.x0)

    def is_punct(c: Component) -> bool:
        return c.area <= PUNCT_MAX_AREA_PX and c.y1 > band.midband_y + 4

    dropped_all = [c for c in own if is_punct(c)]
    own = [c for c in own if not is_punct(c)]

    clusters: list[list[Component]] = []
    for c in own:
        if clusters and c.x0 - max(m.x1 for m in clusters[-1]) < gap_px:
            clusters[-1].append(c)
        else:
            clusters.append([c])

    proposals: list[Proposal] = []
    h, w = page_shape
    for cluster in clusters:
        if all(c.area <= PUNCT_MAX_AREA_PX for c in cluster):
            continue  # lone specks/marks are no word
        x0 = max(0, min(c.x0 for c in cluster) - BOX_PAD_PX)
        y0 = max(0, min(c.y0 for c in cluster) - BOX_PAD_PX)
        x1 = min(w, max(c.x1 for c in cluster) + BOX_PAD_PX)
        y1 = min(h, max(c.y1 for c in cluster) + BOX_PAD_PX)
        dropped = [[d.x0, d.y0, d.x1, d.y1] for d in dropped_all if d.x0 >= x0 - gap_px and d.x1 <= x1 + gap_px]
        flags = []
        small_kept = [c for c in cluster if c.area <= PUNCT_MAX_AREA_PX]
        if small_kept:
            flags.append(f"{len(small_kept)} small mark(s) kept (diacritic/apostrophe?)")
        proposals.append(Proposal(0, band.index, x0, y0, x1, y1, band.baseline_y, band.midband_y, [], dropped, flags))
    return proposals


def add_foreign_ink_excludes(proposals: list[Proposal], comps: list[Component]) -> None:
    """Foreign ink inside a proposed rect gets an exclude rect: a neighbouring
    line's descender/ascender bleeding in, or dropped punctuation that still
    overlaps the rect (the trailing period straddling a box edge). Components
    below the exporter's despeckle floor are skipped — despeckling removes
    them from the mask anyway, and a 2 px exclude sliver risks nipping real
    ink at a box border."""
    dropped_rects = [tuple(d) for p in proposals for d in p.dropped_punct]
    for p in proposals:
        for c in comps:
            if c.line == p.line and (c.x0, c.y0, c.x1, c.y1) not in dropped_rects:
                continue
            if c.area < DESPECKLE_MIN_AREA_PX:
                continue
            ix0, iy0 = max(p.x0, c.x0 - 1), max(p.y0, c.y0 - 1)
            ix1, iy1 = min(p.x1, c.x1 + 1), min(p.y1, c.y1 + 1)
            if ix0 < ix1 and iy0 < iy1:
                p.exclude.append([ix0, iy0, ix1, iy1])


def propose(
    page_path: Path, expect_lines: int, gap_px: int = GAP_PX
) -> tuple[list[LineBand], list[Proposal], np.ndarray]:
    mask = _despeckle(binarize_adaptive(_load_page(page_path)))
    lines = detect_lines(mask, expect_lines)
    comps = extract_components(mask)
    assign_lines(comps, lines)
    proposals: list[Proposal] = []
    for band in lines:
        proposals.extend(cluster_line(comps, band, mask.shape, gap_px))
    add_foreign_ink_excludes(proposals, comps)
    for n, p in enumerate(proposals, start=1):  # reading order: line asc, x asc
        p.number = n
    return lines, proposals, mask


# ----------------------------------------------------------------- rendering


def _font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    # Labels carry German umlauts/ß — prefer a unicode TTF over PIL's
    # ASCII-ish bitmap default.
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:  # pillow < 10.1
            return ImageFont.load_default()


def draw_sheet(
    page_path: Path,
    lines: list[LineBand],
    proposals: list[Proposal],
    out_path: Path,
    labels: dict[int, str] | None = None,
) -> None:
    img = Image.open(page_path).convert("RGB")
    d = ImageDraw.Draw(img)
    font = _font(26)
    for ln in lines:
        d.line([(0, ln.baseline_y), (img.width, ln.baseline_y)], fill=(60, 110, 200), width=2)
        d.line([(0, ln.midband_y), (img.width, ln.midband_y)], fill=(140, 180, 230), width=1)
    for p in proposals:
        d.rectangle([p.x0, p.y0, p.x1, p.y1], outline=(20, 130, 60), width=3)
        for ex in p.exclude:
            d.rectangle(ex, outline=(200, 40, 40), width=2)
        for dp in p.dropped_punct:
            d.rectangle(dp, outline=(235, 150, 30), width=2)
        text = labels.get(p.number, str(p.number)) if labels else str(p.number)
        d.text((p.x0 + 4, p.y0 - 30), text, fill=(20, 130, 60), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"sheet -> {out_path}")


def draw_strips(
    page_path: Path,
    lines: list[LineBand],
    proposals: list[Proposal],
    out_dir: Path,
    labels: dict[int, str] | None = None,
) -> None:
    """One zoomed strip per line for close QC of box edges and lineature."""
    img = Image.open(page_path).convert("RGB")
    for ln in lines:
        members = [p for p in proposals if p.line == ln.index]
        if not members:
            continue
        y0 = max(0, min(p.y0 for p in members) - 12)
        y1 = min(img.height, max(p.y1 for p in members) + 12)
        strip = img.crop((0, y0, img.width, y1)).resize((img.width * 2, (y1 - y0) * 2), Image.LANCZOS)
        d = ImageDraw.Draw(strip)
        font = _font(30)
        d.line([(0, (ln.baseline_y - y0) * 2), (strip.width, (ln.baseline_y - y0) * 2)], fill=(60, 110, 200), width=2)
        d.line([(0, (ln.midband_y - y0) * 2), (strip.width, (ln.midband_y - y0) * 2)], fill=(140, 180, 230), width=1)
        for p in members:
            d.rectangle([p.x0 * 2, (p.y0 - y0) * 2, p.x1 * 2, (p.y1 - y0) * 2], outline=(20, 130, 60), width=3)
            for ex in p.exclude:
                d.rectangle([ex[0] * 2, (ex[1] - y0) * 2, ex[2] * 2, (ex[3] - y0) * 2], outline=(200, 40, 40), width=2)
            for dp in p.dropped_punct:
                d.rectangle([dp[0] * 2, (dp[1] - y0) * 2, dp[2] * 2, (dp[3] - y0) * 2], outline=(235, 150, 30), width=2)
            text = labels.get(p.number, str(p.number)) if labels else str(p.number)
            d.text((p.x0 * 2 + 4, (p.y0 - y0) * 2 + 4), text, fill=(20, 130, 60), font=font)
        out = out_dir / f"strip-line{ln.index + 1:02d}.png"
        strip.save(out)
        print(f"strip -> {out}")


def sidecar_proposals(source_id: str, page: str) -> tuple[list[LineBand], list[Proposal], dict[int, str]]:
    """Rebuild sheet-drawable boxes from the COMMITTED words.json instead of
    proposing — the verification render of the final annotation state."""
    sidecar = json.loads((REPO_ROOT / "data" / "sources" / source_id / "words.json").read_text())
    entries = [w for w in sidecar["words"] if w["page"] == page]
    lineatures: dict[tuple[int, int], int] = {}
    proposals = []
    for w in sorted(entries, key=lambda w: (w["baseline_y"], w["x0"])):
        key = (w["baseline_y"], w["midband_y"])
        line = lineatures.setdefault(key, len(lineatures))
        proposals.append(
            Proposal(0, line, w["x0"], w["y0"], w["x1"], w["y1"], w["baseline_y"], w["midband_y"], w.get("exclude", []))
        )
    for n, p in enumerate(proposals, start=1):
        p.number = n
    lines = [
        LineBand(i, mid - MIDBAND_TRIM_PX, base + BASELINE_TRIM_PX)
        for (base, mid), i in sorted(lineatures.items(), key=lambda kv: kv[1])
    ]
    labels = {
        p.number: w.get("id", w["word"])
        for p, w in zip(proposals, sorted(entries, key=lambda w: (w["baseline_y"], w["x0"])), strict=True)
    }
    return lines, proposals, labels


# ---------------------------------------------------------------- validation


def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    if not inter:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)


def validate(source_id: str, page: str, proposals: list[Proposal]) -> None:
    sidecar = json.loads((REPO_ROOT / "data" / "sources" / source_id / "words.json").read_text())
    committed = [w for w in sidecar["words"] if w["page"] == page]
    if not committed:
        print(f"no committed rects for {page} — nothing to validate against")
        return
    ious, d_base, d_mid = [], [], []
    print(f"--- validate against {len(committed)} committed rects ---")
    for w in committed:
        ref = (w["x0"], w["y0"], w["x1"], w["y1"])
        best = max(proposals, key=lambda p: _iou(ref, (p.x0, p.y0, p.x1, p.y1)))
        iou = _iou(ref, (best.x0, best.y0, best.x1, best.y1))
        ious.append(iou)
        d_base.append(abs(best.baseline_y - w["baseline_y"]))
        d_mid.append(abs(best.midband_y - w["midband_y"]))
        print(
            f"{w['word']:<10} IoU {iou:.3f}  Δbaseline {best.baseline_y - w['baseline_y']:+3d}  "
            f"Δmidband {best.midband_y - w['midband_y']:+3d}  (proposal #{best.number})"
        )
    print(
        f"mean IoU {np.mean(ious):.3f}  median IoU {np.median(ious):.3f}  "
        f"mean |Δbaseline| {np.mean(d_base):.1f}px  mean |Δmidband| {np.mean(d_mid):.1f}px"
    )


# ----------------------------------------------------------------------- CLI


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--page", required=True, help="page PNG name, e.g. words-abb19.png")
    parser.add_argument("--expect-lines", type=int, required=True, help="handwriting lines on the plate")
    parser.add_argument("--gap-px", type=int, default=GAP_PX, help="min whitespace between words (px)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--strips", action="store_true", help="also render zoomed per-line strips")
    parser.add_argument("--validate", action="store_true", help="score against committed rects instead of proposing")
    parser.add_argument(
        "--from-sidecar",
        action="store_true",
        help="render the COMMITTED words.json boxes (labels instead of numbers) — the final verification sheet",
    )
    args = parser.parse_args()

    page_path = REPO_ROOT / "data" / "sources" / args.source / args.page
    if not page_path.exists():
        raise SystemExit(f"no page at {page_path}")

    if args.from_sidecar:
        lines, proposals, labels = sidecar_proposals(args.source, args.page)
        out_dir = args.out / (args.page.replace(".png", "") + "-final")
        out_dir.mkdir(parents=True, exist_ok=True)
        draw_sheet(page_path, lines, proposals, out_dir / "sheet.png", labels)
        if args.strips:
            draw_strips(page_path, lines, proposals, out_dir, labels)
        return

    lines, proposals, _ = propose(page_path, args.expect_lines, args.gap_px)
    print(f"{len(lines)} lines, {len(proposals)} boxes proposed")

    if args.validate:
        validate(args.source, args.page, proposals)
        return

    out_dir = args.out / args.page.replace(".png", "")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": args.source,
        "page": args.page,
        "lines": [{"line": ln.index + 1, "baseline_y": ln.baseline_y, "midband_y": ln.midband_y} for ln in lines],
        "words": [
            {
                "n": p.number,
                "line": p.line + 1,
                "word": "",
                "page": args.page,
                "x0": p.x0,
                "y0": p.y0,
                "x1": p.x1,
                "y1": p.y1,
                "baseline_y": p.baseline_y,
                "midband_y": p.midband_y,
                **({"exclude": p.exclude} if p.exclude else {}),
                **({"dropped_punct": p.dropped_punct} if p.dropped_punct else {}),
                **({"flags": p.flags} if p.flags else {}),
            }
            for p in proposals
        ],
    }
    (out_dir / "proposals.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    print(f"proposals -> {out_dir / 'proposals.json'}")
    draw_sheet(page_path, lines, proposals, out_dir / "sheet.png")
    if args.strips:
        draw_strips(page_path, lines, proposals, out_dir)


if __name__ == "__main__":
    main()
