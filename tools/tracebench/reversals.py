"""The paper-reversal inventory: where a candidate's path zig-zags in the PAPER.

The sensor round 9 asked for (§14 „Kette K-E `sep09`"). The judge described the
defect as „richtig schlimm" scribble, and the first, ad-hoc count of it was
withdrawn on his own objection because it counted the DUCTUS: `Galoppieren`
led that table with 23 reversals, and every one of them sits at a real turning
point INSIDE the ink. A reversal in the ink is a pen event; only a reversal
whose vertex lies in the PAPER is the zig-zag the eye reads as a defect.

Per word: consecutive segments of the candidate's own polyline (vertices, not
the ruler's resampling — resampling would erase exactly the short back-and-forth
this counts) are thinned to segments of at least `MIN_SEGMENT_PX`, and a vertex
whose two adjacent segment directions have `cos < COS_MAX` is a reversal. It
counts as a PAPER reversal when its pixel is paper, and paper is read off the
frozen crop against the midpoint between that crop's ink and paper grey levels
(`--paper mask` reads the frozen `ref_mask` instead).

This is a REPORT, not a ruler: it is bound to no gate, it enters no
`bench_loss`, and a round quoting it says so. Reads only fixtures and candidate
files — no DB, no network, no solve.

    uv run python -m tools.tracebench.reversals temp/candidate.json
    uv run python -m tools.tracebench.reversals a.json b.json --words-file w.json
        [--paper mask] [--expect-root <digest-prefix>]

Like every bench tool it names the root it read (``root:`` / ``digest=``) before
the first count and accepts ``--expect-root`` to make that base a precondition.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from tools.tracebench.candidates import file_provider
from tools.tracebench.reference import DEFAULT_FIXTURES_DIR, Reference, ReferenceEntry, load_reference
from tools.tracebench.run import find_fixture_root
from tools.wordbench.roots import add_expect_root_argument, announce_roots


# A segment shorter than this carries no direction worth trusting — it is the
# solver's discretisation, not a stroke — so the vertex closing it is folded
# into its predecessor before any angle is read. 0.5 crop px is half the pixel
# the paper test itself resolves; the count is flat over 0.3 … 0.5 (§14 „Kette
# K-G `sep09`"), which is what makes the choice reportable rather than tuned.
MIN_SEGMENT_PX = 0.5
# Two directions count as a reversal below this cosine — 134° and sharper. The
# ductus' own sharpest corners (Sütterlin cusps) sit well above it; a retrace
# doubles straight back and sits at −1.
COS_MAX = -0.7
PAPER_SOURCES = ("grey", "mask")


def _paper_test(entry: ReferenceEntry, source: str) -> tuple[np.ndarray, str]:
    """A boolean image that is True where a pixel counts as PAPER."""
    mask = entry.ink_mask()
    if source == "mask":
        return ~mask, "frozen ref_mask"
    with Image.open(entry.directory / "crop.png") as img:
        crop = np.asarray(img.convert("L"), dtype=float) / 255.0
    # The midpoint between the two grey levels of THIS crop, not a global
    # constant: the plate's exposure varies per rect, and a fixed threshold
    # would count faded ink as paper on the pale crops and nothing on the dark.
    ink_level = float(crop[mask].mean()) if mask.any() else 0.0
    paper_level = float(crop[~mask].mean()) if (~mask).any() else 1.0
    return crop > 0.5 * (ink_level + paper_level), "crop grey midpoint"


def reversal_vertices(points_px: np.ndarray) -> np.ndarray:
    """The reversal vertices of one polyline, in the same frame it came in."""
    if len(points_px) < 3:
        return np.empty((0, 2), dtype=float)
    kept = [points_px[0]]
    for point in points_px[1:]:
        if float(np.hypot(*(point - kept[-1]))) >= MIN_SEGMENT_PX:
            kept.append(point)
    thinned = np.asarray(kept, dtype=float)
    if len(thinned) < 3:
        return np.empty((0, 2), dtype=float)
    seg = np.diff(thinned, axis=0)
    norm = np.linalg.norm(seg, axis=1)
    unit = seg / np.where(norm > 0, norm, 1.0)[:, None]
    turns = np.einsum("ij,ij->i", unit[:-1], unit[1:])
    hits = np.nonzero(turns < COS_MAX)[0] + 1
    return thinned[hits] if len(hits) else np.empty((0, 2), dtype=float)


def inventory(
    candidate_path: Path, reference: Reference, *, paper: str = "grey", only: list[str] | None = None
) -> dict[str, dict[str, float]]:
    """`{specimen_id: {"paper": n, "ink": n, "paper_len_xh": l}}` — reversals and Papier-Strecke per word."""
    cands = file_provider(str(candidate_path))(reference, reference.order)
    wanted = reference.order if only is None else [s for s in reference.order if s in set(only)]
    rows: dict[str, dict[str, float]] = {}
    for sid in wanted:
        cand, entry = cands.get(sid), reference.entries.get(sid)
        if cand is None or not cand.ok or entry is None:
            continue
        is_paper, _ = _paper_test(entry, paper)
        n_paper = n_ink = 0
        paper_len_px = 0.0
        for stroke in entry.frame.trace_to_bench(cand.strokes, cand.registration_px, cand.xh_px):
            crop_px = entry.frame.bench_to_crop_px(np.asarray(stroke, dtype=float))
            paper_len_px += paper_length_px(crop_px, is_paper)
            verts = reversal_vertices(crop_px)
            if not len(verts):
                continue
            row = np.clip(np.round(verts[:, 1]).astype(int), 0, is_paper.shape[0] - 1)
            col = np.clip(np.round(verts[:, 0]).astype(int), 0, is_paper.shape[1] - 1)
            hits = int(is_paper[row, col].sum())
            n_paper += hits
            n_ink += len(verts) - hits
        rows[sid] = {"paper": n_paper, "ink": n_ink, "paper_len_xh": round(paper_len_px / float(cand.xh_px), 3)}
    return rows


def paper_length_px(points_px: np.ndarray, is_paper: np.ndarray) -> float:
    """The Papier-Strecke of one polyline: its length over paper pixels, in px.

    The night loop's second sensor (`sep10`): a straight chord through the
    paper reverses nowhere and counts zero reversals, but it has length. Each
    segment is walked at one-pixel steps so a long chord is measured along its
    whole run, not only at its two vertices.
    """
    p = np.asarray(points_px, dtype=float).reshape(-1, 2)
    if len(p) < 2:
        return 0.0
    seg = np.diff(p, axis=0)
    lengths = np.linalg.norm(seg, axis=1)
    total = 0.0
    h, w = is_paper.shape
    for (x0, y0), (dx, dy), length in zip(p[:-1], seg, lengths, strict=True):
        n = max(1, int(np.ceil(length)))
        ts = (np.arange(n) + 0.5) / n
        xs = np.clip(np.round(x0 + dx * ts).astype(int), 0, w - 1)
        ys = np.clip(np.round(y0 + dy * ts).astype(int), 0, h - 1)
        total += float(is_paper[ys, xs].sum()) * (length / n)
    return total


def main() -> None:
    parser = argparse.ArgumentParser(prog="tracebench.reversals", description=__doc__)
    parser.add_argument("candidates", nargs="+", type=Path, help="tracebench file-provider candidate JSONs")
    parser.add_argument("--paper", choices=PAPER_SOURCES, default="grey", help="how a pixel counts as paper")
    parser.add_argument("--words-file", type=Path, help="humanbench occurrence JSON — restrict to its entries")
    parser.add_argument("--top", type=int, default=15, help="rows to print per candidate (default 15)")
    parser.add_argument("--json", type=Path, help="write the full inventory here")
    add_expect_root_argument(parser)
    args = parser.parse_args()

    root = find_fixture_root(DEFAULT_FIXTURES_DIR, "suetterlin", "words")
    announce_roots([root], args.expect_root)
    reference = load_reference(root)
    only = None
    if args.words_file:
        rows = json.loads(args.words_file.read_text())
        only = sorted({str(r["entry"]) for r in rows if not r.get("repeat_of")})
        print(f"restricted to {len(only)} entries from {args.words_file.name}")

    out: dict[str, dict[str, dict[str, float]]] = {}
    for path in args.candidates:
        rows = inventory(path, reference, paper=args.paper, only=only)
        out[path.name] = rows
        total_paper = sum(r["paper"] for r in rows.values())
        total_ink = sum(r["ink"] for r in rows.values())
        total_len = sum(float(r["paper_len_xh"]) for r in rows.values())
        print(f"== {path.name} ({len(rows)} words)  paper {total_paper}  ink {total_ink}  paper_len_xh {total_len:.2f}")
        ranked = sorted(rows.items(), key=lambda kv: (-kv[1]["paper"], -float(kv[1]["paper_len_xh"]), kv[0]))
        for sid, row in ranked[: args.top]:
            if not row["paper"] and float(row["paper_len_xh"]) < 0.05:
                break
            print(
                f"  {sid:14s} paper {row['paper']:3d}   ink {row['ink']:3d}   len {float(row['paper_len_xh']):6.3f} xh"
            )
    if len(args.candidates) == 2:
        a, b = (out[p.name] for p in args.candidates)
        print("-- paired, paper reversals only (words at 0 : 0 omitted)")
        for sid in sorted(set(a) | set(b)):
            pa, pb = a.get(sid, {}).get("paper", 0), b.get(sid, {}).get("paper", 0)
            if pa or pb:
                print(f"  {sid:14s} {pa:3d} : {pb:3d}")
        print(f"  {'SUM':14s} {sum(r['paper'] for r in a.values()):3d} : {sum(r['paper'] for r in b.values()):3d}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(out, indent=1, ensure_ascii=False))
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
