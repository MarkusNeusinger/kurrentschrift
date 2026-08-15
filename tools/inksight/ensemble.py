"""Stage 3b of the InkSight pipeline: N variant answers → one candidate (B1).

Runs in the REPO environment (no TensorFlow): it reads the per-variant raw
answers of an ensemble run, inverts each variant's own affine chain back to crop
pixels, RANKS them against the measured ink and writes the winner in exactly the
candidate contract `to_candidate.py` writes — `docs/proposals/tintenfolger.md`
§2.4, i.e. a `word_instances` row.

    uv run python -m tools.inksight.ensemble
        [--manifest tools/inksight/out/frames_ensemble.json]
        [--raw tools/inksight/out/raw] [--out tools/inksight/out/candidates]
        [--prompt derender] [--fixtures-root ...]

**The ranker grades against the INK, never against a reference trace.** This is
the load-bearing rule of the whole measure, so it is worth saying twice: the
frozen fixture entry carries `ref_skel.npz` (the thinning of `ref_mask.png`) —
the MEASURED ink of the specimen, the same artifact the bench's AIoU column
grades against — and that is the only target the selection ever sees. The
author's hand traces (`word_instances`, provenance `authored`) are the
EXAMINATION; selecting against them would be marking one's own homework, and the
resulting candidate could not be reported as a measurement at all. Nothing in
this module reads a reference trace, and nothing in it imports the trace bench's
reference loader.

**The rank number.** Per variant, both chamfer directions between the decoded
path (arc-length resampled to `RANK_RESAMPLE_PX` so a sparse polyline is
measured along its line rather than at its vertices) and the ink's skeleton
points, computed SEPARATELY and summed:

    rank = mean_{p in path} min_dist(p, ink) + mean_{q in ink} min_dist(q, path)

Kept apart until the sum because the two halves answer different questions and a
symmetric mean would hide exactly the failure this ensemble is meant to catch: a
decode that writes only half the word scores well on the first half (everything
it drew is on ink) and badly on the second (a lot of ink has nothing near it).
Both are in x-heights, so a row is readable beside the bench's own columns —
they are NOT the same numbers, though: the bench's `chamfer_*_xh` compare
candidate against the hand TRACE, these compare candidate against the INK.

**Contract violations disqualify, they do not crash.** A variant whose decode
cannot be stored (`api.schemas.WordInstanceItem`'s wire bounds — the `Wer`
single-point stroke of the T0 run is the concrete case) is ranked, reported and
then sorted BEHIND every conforming variant. It can still win, but only when no
member of the ensemble conforms; then the row travels as `status: "failed"`
exactly as the plain pipeline's would, because a repaired candidate would make
the model look better than it is.

**The winner is passed through UNCHANGED.** The resampling above exists for the
ranker and for nothing else: no cleanup, no merging, no smoothing, no dropping
of degenerate runs ever touches the emitted geometry. Best-of-N is a SELECTION
among decodes the model actually produced — the moment this module edits a path,
the number it reports stops being InkSight's.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from PIL import Image

from tools.inksight.augment import DEFAULT_MANIFEST_NAME, VariantFrame, model_to_crop_px, variant_frame_of
from tools.inksight.prepare import DEFAULT_FIXTURES_ROOT, DEFAULT_OUT
from tools.inksight.to_candidate import CANDIDATE_FRAME, derive_set_labels, registration_of, validate_strokes
from tools.pairlab.trace import _px_to_word_units
from tools.tracebench.metric import chamfer, resample_by_step


# The tool label of an ensembled candidate. Deliberately NOT `inksight-smallp-raw`:
# the geometry is still raw model output, but WHICH output was chosen is this
# pipeline's doing, and a candidate archive that cannot tell the two apart is
# worthless the day the two disagree.
TOOL_NAME = "inksight-smallp-bestofN"

# The frozen artifacts of a fixture entry that carry the MEASURED ink.
# `ref_skel.npz` is the thinning (a centerline, what a pen path should follow);
# `ref_mask.png` is the filled binarisation and only the fallback — its ink→path
# half is inflated by the stroke width, which is a bias, not an error, but it is
# a bias worth naming in the record.
SKELETON_FILE = "ref_skel.npz"
INK_MASK_FILE = "ref_mask.png"

# Arc-length step the ranker resamples a decoded path with, in CROP pixels. One
# pixel: fine enough that the ink→path half is measured against the line rather
# than against a vertex cloud, coarse enough that a 500-point answer stays a few
# thousand points against a few thousand skeleton pixels.
RANK_RESAMPLE_PX = 1.0

DEFAULT_PROMPT_KEY = "derender"


def load_ink_points(entry_dir: Path) -> tuple[np.ndarray, str]:
    """The measured ink of one entry as `(N, 2)` crop pixels `(x, y)`, and its source.

    Skeleton first, mask second, nothing third: an entry with neither is not
    rankable, and the caller must report it rather than fall back to a variant
    chosen by grid order.
    """
    skeleton = entry_dir / SKELETON_FILE
    if skeleton.is_file():
        with np.load(skeleton) as data:
            rows, cols = np.nonzero(np.asarray(data["skel"], dtype=bool))
        if len(rows):
            return np.column_stack([cols, rows]).astype(float), SKELETON_FILE
    mask = entry_dir / INK_MASK_FILE
    if mask.is_file():
        with Image.open(mask) as image:
            rows, cols = np.nonzero(np.asarray(image.convert("L")) > 127)
        if len(rows):
            return np.column_stack([cols, rows]).astype(float), INK_MASK_FILE
    raise FileNotFoundError(f"no measured ink in {entry_dir} ({SKELETON_FILE} / {INK_MASK_FILE})")


def strokes_to_crop_px(strokes_224: list[list[list[float]]], frame: VariantFrame) -> list[list[list[float]]]:
    """Model-frame strokes → crop pixels, through THIS variant's own chain."""
    return [[list(model_to_crop_px(float(u), float(v), frame)) for u, v in stroke] for stroke in strokes_224]


def strokes_to_word_units(
    strokes_px: list[list[list[float]]], registration: dict, xh: float
) -> list[list[list[float]]]:
    """Crop-pixel strokes → the word's registration frame, stroke for stroke.

    Goes through `_px_to_word_units`, the function the harvest and the follower
    use, imported from its DEFINITION site rather than re-implemented — the same
    reason `to_candidate.py` gives, and the same reason route G gives.
    """
    out: list[list[list[float]]] = []
    for stroke in strokes_px:
        if not stroke:
            out.append([])
            continue
        pts = np.asarray(stroke, dtype=float)
        out.append(_px_to_word_units(pts[:, 0], pts[:, 1], xh, registration).tolist())
    return out


def rank_points(strokes_px: list[list[list[float]]], step: float = RANK_RESAMPLE_PX) -> np.ndarray:
    """The point cloud the ranker reads: every stroke resampled by arc length.

    Per stroke, so a pen lift is never bridged — the gap between two strokes is
    not a line the model drew and must not be credited as ink coverage.
    """
    chunks = [resample_by_step(np.asarray(stroke, dtype=float), step) for stroke in strokes_px if len(stroke)]
    return np.vstack(chunks) if chunks else np.empty((0, 2), dtype=float)


def rank_against_ink(strokes_px: list[list[list[float]]], ink_points: np.ndarray, xh: float) -> dict:
    """The two chamfer halves against the measured ink, in x-heights, plus their sum.

    An answer with no points at all is unrankable rather than perfect: it gets an
    infinite score, which sorts it last however the rest of the ensemble did.
    """
    cloud = rank_points(strokes_px)
    if not len(cloud) or not len(ink_points):
        return {"chamfer_cand_ink_xh": math.inf, "chamfer_ink_cand_xh": math.inf, "rank_sum_xh": math.inf}
    cand_ink, ink_cand = chamfer(cloud, ink_points)
    return {
        "chamfer_cand_ink_xh": cand_ink / xh,
        "chamfer_ink_cand_xh": ink_cand / xh,
        "rank_sum_xh": (cand_ink + ink_cand) / xh,
    }


def evaluate_variant(
    raw: dict, record: dict, registration: dict, xh: float, ink_points: np.ndarray, order: int
) -> dict:
    """One variant's decode: inverted, validated and ranked. No geometry edited."""
    frame = variant_frame_of(record)
    strokes_px = strokes_to_crop_px(raw.get("strokes_224") or [], frame)
    strokes = strokes_to_word_units(strokes_px, registration, xh)
    detail = validate_strokes(strokes)
    return {
        "variant": frame.name,
        "order": order,
        "rotation_deg": frame.rotation.degrees,
        "scale": frame.scale,
        "grid_step_crop_px": record.get("grid_step_crop_px"),
        "status": "failed" if detail else "ok",
        "detail": detail,
        "strokes": strokes,
        "raw": raw,
        **rank_against_ink(strokes_px, ink_points, xh),
    }


def rank_key(evaluation: dict) -> tuple[int, float, int]:
    """Sort key: conforming first, then the rank sum, then the grid order.

    The grid order is the tie-break so a rerun over the same answers picks the
    same winner — with the shipped grid that also means the plain, unaugmented
    variant wins a tie, which is the conservative choice.
    """
    return (0 if evaluation["status"] == "ok" else 1, evaluation["rank_sum_xh"], evaluation["order"])


def _rank_report(evaluation: dict) -> dict:
    """One line of the meta ranking table — numbers only, no geometry."""
    line = {
        "variant": evaluation["variant"],
        "status": evaluation["status"],
        "n_ink_tokens": evaluation["raw"].get("n_ink_tokens"),
        "n_strokes": len(evaluation["strokes"]),
    }
    for key in ("rank_sum_xh", "chamfer_cand_ink_xh", "chamfer_ink_cand_xh"):
        value = evaluation[key]
        line[key] = None if math.isinf(value) else round(value, 6)
    if evaluation["detail"]:
        line["detail"] = evaluation["detail"]
    return line


def build_ensemble_row(
    evaluations: list[dict], frame_record: dict, word_json: dict, ink_source: str, n_planned: int
) -> dict:
    """The winning candidate row of one word, with the whole ranking in its meta."""
    if not evaluations:
        raise ValueError("build_ensemble_row needs at least one evaluated variant")
    registration, xh = registration_of(word_json)
    ranked = sorted(evaluations, key=rank_key)
    winner = ranked[0]
    raw = winner["raw"]
    meta = {
        "prompt": raw.get("prompt"),
        "prompt_key": raw.get("prompt_key"),
        "n_ink_tokens": raw.get("n_ink_tokens"),
        "n_invalid_tokens": raw.get("n_invalid_tokens"),
        "grid_step_crop_px": winner["grid_step_crop_px"],
        "recognized_text": raw.get("recognized_text"),
        "variant": winner["variant"],
        "rotation_deg": winner["rotation_deg"],
        "scale": winner["scale"],
        "ensemble_n": len(evaluations),
        "ensemble_n_planned": n_planned,
        "ensemble_n_valid": sum(1 for item in evaluations if item["status"] == "ok"),
        # Named in full so a reader of the archive never has to guess what the
        # selection was made against.
        "rank_metric": "chamfer_sum_xh_vs_measured_ink",
        "ink_source": ink_source,
        "rank_resample_px": RANK_RESAMPLE_PX,
        "ranking": [_rank_report(item) for item in ranked],
    }
    if winner["detail"]:
        meta["detail"] = winner["detail"]
    return {
        "kind": frame_record.get("kind", "word"),
        "specimen_id": frame_record["id"],
        "word": frame_record["word"],
        "registration_px": registration,
        "xh_px": xh,
        "strokes": winner["strokes"],
        "status": winner["status"],
        "meta": meta,
    }


def _read_answers(raw_dir: Path, entry_id: str, variants: dict, prompt_key: str) -> list[tuple[dict, dict]]:
    """`(raw answer, variant record)` for every variant of one word that decoded."""
    found: list[tuple[dict, dict]] = []
    for name, record in variants.items():
        path = raw_dir / f"{entry_id}.{name}.{prompt_key}.json"
        if not path.is_file():
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        found.append((raw, record))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUT / DEFAULT_MANIFEST_NAME)
    parser.add_argument("--raw", type=Path, default=DEFAULT_OUT / "raw")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT / "candidates")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT_KEY, help="which prompt's answers to ensemble")
    parser.add_argument("--ids", nargs="*", default=None, help="restrict to these fixture ids")
    parser.add_argument("--fixtures-root", type=Path, default=None, help="default: the root augment.py recorded")
    parser.add_argument("--tool", default=TOOL_NAME)
    parser.add_argument("--version", default=None, help="default: today (UTC)")
    args = parser.parse_args(argv)

    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    frames = payload["frames"]
    root = args.fixtures_root or Path(payload.get("fixtures_root", DEFAULT_FIXTURES_ROOT))
    style, source_id, set_name = derive_set_labels(root)
    ids = list(args.ids) if args.ids else list(frames)
    identity = (payload.get("grid") or {}).get("identity")

    rows: list[dict] = []
    skipped = 0
    for entry_id in ids:
        frame_record = frames.get(entry_id)
        if frame_record is None:
            print(f"  ! {entry_id}: not in the manifest — skipped")
            skipped += 1
            continue
        answers = _read_answers(args.raw, entry_id, frame_record["variants"], args.prompt)
        if not answers:
            print(f"  ! {entry_id}: no {args.prompt} answers in {args.raw} — skipped")
            skipped += 1
            continue
        entry_dir = root / entry_id
        try:
            ink_points, ink_source = load_ink_points(entry_dir)
        except FileNotFoundError as error:
            # Without measured ink there is nothing to rank against, and picking
            # by grid order would be a silent, unmarked non-selection.
            print(f"  ! {entry_id}: {error} — skipped")
            skipped += 1
            continue
        word_json = json.loads((entry_dir / "word.json").read_text(encoding="utf-8"))
        registration, xh = registration_of(word_json)
        evaluations = [
            evaluate_variant(raw, record, registration, xh, ink_points, order)
            for order, (raw, record) in enumerate(answers)
        ]
        row = build_ensemble_row(evaluations, frame_record, word_json, ink_source, len(frame_record["variants"]))
        rows.append(row)

        meta = row["meta"]
        table = {item["variant"]: item["rank_sum_xh"] for item in meta["ranking"]}
        best = table.get(meta["variant"])
        # The identity member is the plain pipeline's own input, so its score is
        # the honest "did the ensemble buy anything?" comparison.
        plain = table.get(identity) if identity else None
        gain = f"  plain {plain:.4f} ({(best - plain) / plain:+.1%})" if plain and best else ""
        print(
            f"  {entry_id:<12} winner {meta['variant']:<12} sum {'--' if best is None else f'{best:.4f}'} xh"
            f"  valid {meta['ensemble_n_valid']}/{meta['ensemble_n']}{gain}  [{row['status']}]"
        )

    if not rows:
        print(f"no ensembled rows produced from {args.raw}")
        return 1

    rows.sort(key=lambda row: row["specimen_id"])
    args.out.mkdir(parents=True, exist_ok=True)
    document = {
        "tool": args.tool,
        "version": args.version or datetime.now(UTC).date().isoformat(),
        "style": style,
        "source_id": source_id,
        "set": set_name,
        "frame": CANDIDATE_FRAME,
        "rows": rows,
    }
    target = args.out / f"{args.tool}.{args.prompt}.json"
    target.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
    failed = [row for row in rows if row["status"] != "ok"]
    print(f"{target}  rows {len(rows)}  failed {len(failed)}" + (f"  skipped {skipped}" if skipped else ""))
    for row in failed:
        print(f"  ! {row['specimen_id']}: {row['meta'].get('detail')} (no conforming variant in the ensemble)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
