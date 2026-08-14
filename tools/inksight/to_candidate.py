"""Stage 3 of the InkSight pipeline: raw model strokes → tracebench candidates.

Runs in the REPO environment (no TensorFlow): it inverts the affine
`prepare.py` recorded, converts crop pixels into the stored `word_instances`
trace frame and writes ONE candidate file per prompt in the stage-C provider
shape (tintenfolger.md §2.4).

    uv run python -m tools.inksight.to_candidate
        [--frames tools/inksight/out/frames.json] [--raw tools/inksight/out/raw]
        [--out tools/inksight/out/candidates]

Why `tx = 0`, `ty = 0`: the stored `(u,v)` labels are NOT canonical — `tx`
comes out of the composer's grid search and the word editor folds `ty` into
`baseline_row` (tintenfolger.md §2.1). InkSight's output is positioned in the
CROP, so its registration is the crop's own: x measured from the crop's left
edge, the baseline row derived from the frozen fixture entry
(`baseline_row = baseline_y - rect[1]`, `xh = baseline_y - midband_y`), which
is exactly the frame the bench re-expresses every trace in.

The conversion itself goes through `tools.laufform.harvest._px_to_word_units` —
the same function the harvest and the follower use. A private import on
purpose: a second implementation of the frame conversion is precisely the kind
of drift a measurement pipeline cannot afford.

Strokes are emitted EXACTLY as the model produced them: no cleanup, no
resampling, no merging, no dropping of degenerate runs. The only judgement
applied is the wire contract of `api.schemas.WordInstanceItem` (1..128 strokes,
2..4096 points each, |coordinate| <= 100) — a row that violates it is kept and
stamped `status: "failed"` with the reason, because a silently repaired
candidate would make the model look better than it is.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from tools.inksight.prepare import DEFAULT_FIXTURES_ROOT, DEFAULT_OUT, Affine, model_to_crop
from tools.laufform.harvest import _px_to_word_units


TOOL_NAME = "inksight-smallp-raw"
CANDIDATE_FRAME = "word_registration"

# `api.schemas.WordInstanceItem`'s wire contract.
MAX_WORD_STROKES = 128
MIN_STROKE_POINTS = 2
MAX_STROKE_POINTS = 4096
MAX_ABS_COORD = 100.0


def affine_of(frame: dict) -> Affine:
    """The affine record of one `frames.json` entry."""
    return Affine(
        ratio=float(frame["ratio"]),
        scale_x=float(frame["scale_x"]),
        scale_y=float(frame["scale_y"]),
        dx=int(frame["dx"]),
        dy=int(frame["dy"]),
    )


def registration_of(word_json: dict) -> tuple[dict, float]:
    """The crop-local registration and x-height of one frozen fixture entry."""
    baseline_y = float(word_json["baseline_y"])
    midband_y = float(word_json["midband_y"])
    xh = baseline_y - midband_y
    if xh <= 0:
        raise ValueError(f"non-positive x-height for {word_json.get('id')}: {xh}")
    return {"tx": 0, "ty": 0, "baseline_row": baseline_y - float(word_json["rect"][1])}, xh


def strokes_to_word_units(
    strokes_224: list[list[list[float]]], affine: Affine, registration: dict, xh: float
) -> list[list[list[float]]]:
    """Model-frame strokes → the word's registration frame, stroke for stroke."""
    out: list[list[list[float]]] = []
    for stroke in strokes_224:
        if not stroke:
            out.append([])
            continue
        crop = np.array([model_to_crop(float(u), float(v), affine) for u, v in stroke], dtype=float)
        out.append(_px_to_word_units(crop[:, 0], crop[:, 1], xh, registration).tolist())
    return out


def validate_strokes(strokes: list[list[list[float]]]) -> str | None:
    """The wire-contract violation of this trace, or None when it is clean."""
    if not strokes:
        return "no strokes decoded"
    if len(strokes) > MAX_WORD_STROKES:
        return f"{len(strokes)} strokes exceed the wire cap of {MAX_WORD_STROKES}"
    for index, stroke in enumerate(strokes):
        if not MIN_STROKE_POINTS <= len(stroke) <= MAX_STROKE_POINTS:
            return f"stroke {index} has {len(stroke)} points (allowed {MIN_STROKE_POINTS}..{MAX_STROKE_POINTS})"
        for point in stroke:
            if len(point) != 2:
                return f"stroke {index} has a point that is not an [x, y] pair"
            if not all(abs(float(value)) <= MAX_ABS_COORD for value in point):
                return f"stroke {index} leaves the coordinate range (|value| <= {MAX_ABS_COORD:g})"
    return None


def build_row(raw: dict, frame: dict, word_json: dict) -> dict:
    """One candidate row from one raw model answer."""
    registration, xh = registration_of(word_json)
    strokes = strokes_to_word_units(raw["strokes_224"], affine_of(frame), registration, xh)
    detail = validate_strokes(strokes)
    meta = {
        "prompt": raw.get("prompt"),
        "prompt_key": raw.get("prompt_key"),
        "n_ink_tokens": raw.get("n_ink_tokens"),
        "n_invalid_tokens": raw.get("n_invalid_tokens"),
        "grid_step_crop_px": frame.get("grid_step_crop_px"),
        "recognized_text": raw.get("recognized_text"),
    }
    if detail:
        meta["detail"] = detail
    return {
        "kind": frame.get("kind", "word"),
        "specimen_id": raw["id"],
        "word": raw["word"],
        "registration_px": registration,
        "xh_px": xh,
        "strokes": strokes,
        "status": "failed" if detail else "ok",
        "meta": meta,
    }


def derive_set_labels(fixtures_root: Path) -> tuple[str, str, str]:
    """(style, source_id, set) from a fixture root path like `<style>/<source>[-set]`."""
    name = fixtures_root.name
    style = fixtures_root.parent.name
    for suffix, set_name in (("-pairs", "pairs"), ("-abb22", "abb22")):
        if name.endswith(suffix):
            return style, name[: -len(suffix)], set_name
    return style, name, "words"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--frames", type=Path, default=DEFAULT_OUT / "frames.json")
    parser.add_argument("--raw", type=Path, default=DEFAULT_OUT / "raw")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT / "candidates")
    parser.add_argument("--fixtures-root", type=Path, default=None, help="default: the root prepare.py recorded")
    parser.add_argument("--tool", default=TOOL_NAME)
    parser.add_argument("--version", default=None, help="default: today (UTC)")
    args = parser.parse_args(argv)

    payload = json.loads(args.frames.read_text(encoding="utf-8"))
    frames = payload["frames"]
    root = args.fixtures_root or Path(payload.get("fixtures_root", DEFAULT_FIXTURES_ROOT))
    style, source_id, set_name = derive_set_labels(root)
    version = args.version or datetime.now(UTC).date().isoformat()

    by_prompt: dict[str, list[dict]] = {}
    for path in sorted(args.raw.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        frame = frames.get(raw["id"])
        if frame is None:
            print(f"  ! {path.name}: no frame record for id {raw['id']} — skipped")
            continue
        word_json = json.loads((root / raw["id"] / "word.json").read_text(encoding="utf-8"))
        key = raw.get("prompt_key") or path.stem.split(".")[-1]
        by_prompt.setdefault(key, []).append(build_row(raw, frame, word_json))

    if not by_prompt:
        print(f"no raw answers in {args.raw}")
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    for key, rows in sorted(by_prompt.items()):
        rows.sort(key=lambda row: row["specimen_id"])
        document = {
            "tool": args.tool,
            "version": version,
            "style": style,
            "source_id": source_id,
            "set": set_name,
            "frame": CANDIDATE_FRAME,
            "rows": rows,
        }
        target = args.out / f"{args.tool}.{key}.json"
        target.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
        failed = [row for row in rows if row["status"] != "ok"]
        print(f"{target}  rows {len(rows)}  failed {len(failed)}")
        for row in failed:
            print(f"  ! {row['specimen_id']}: {row['meta'].get('detail')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
