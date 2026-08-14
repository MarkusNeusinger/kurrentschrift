"""Stage 3 of route G: recovered crop-pixel strokes → a tracebench candidate.

Runs in the REPO environment: it reads the per-word answers stage 2 wrote and
converts them into the stage-C provider shape (`docs/proposals/tintenfolger.md`
§2.4), which is literally a `word_instances` row.

    uv run python -m tools.routeg.to_candidate
        [--frames tools/routeg/out/frames.json] [--raw tools/routeg/out/raw]
        [--out tools/routeg/out/candidates] [--tool routeg-graph]

The frame handling is `tools/inksight/to_candidate.py`'s, deliberately copied
rather than re-derived — a second implementation of the frame conversion is
exactly the drift a measurement pipeline cannot afford. The conversion itself
goes through `_px_to_word_units`, the function the harvest and the follower use;
imported from its DEFINITION site `tools.pairlab.trace` rather than from the
`tools.laufform.harvest` re-export the InkSight stage uses, because that module
pulls `tools.wordlab` and with it matplotlib — a `viz` extra has no business in
a frame conversion. Two further differences, both because route G reads the crop
at its own resolution:

* there is no affine to invert (stage 2 already answers in crop pixels), so the
  model-frame step of the InkSight pipeline simply does not exist here;
* consequently no `grid_step_crop_px` — the control's resolution floor is one
  crop pixel, the crop's own.

Why `tx = 0`, `ty = 0`: the stored `(u, v)` labels are NOT canonical — `tx` comes
out of the composer's grid search and the word editor folds `ty` into
`baseline_row` (tintenfolger.md §2.1). A recovered trace is positioned in the
CROP, so its registration is the crop's own: x measured from the crop's left
edge, the baseline row derived from the frozen fixture entry
(`baseline_row = baseline_y - rect[1]`, `xh = baseline_y - midband_y`), which is
exactly the frame the bench re-expresses every trace in.

Strokes are emitted EXACTLY as stage 2 recovered them: no cleanup, no
resampling, no merging, no dropping of degenerate runs. The only judgement
applied is the wire contract of `api.schemas.WordInstanceItem` (1..128 strokes,
2..4096 points each, |coordinate| <= 100) — a row that violates it is kept and
stamped `status: "failed"` with the reason, because a silently repaired
candidate would make the control look better than it is.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from tools.pairlab.trace import _px_to_word_units
from tools.routeg.prepare import DEFAULT_FIXTURES_ROOT, DEFAULT_OUT, ENTRY_FILE


# Named for what actually produced the geometry. NOT `routeg-wor`: the reference
# implementation is MATLAB and was never run here (README § "Provenance"), and a
# candidate file that claims a method it did not use is the one label error a
# measurement archive cannot recover from.
TOOL_NAME = "routeg-graph"
CANDIDATE_FRAME = "word_registration"

# `api.schemas.WordInstanceItem`'s wire contract.
MAX_WORD_STROKES = 128
MIN_STROKE_POINTS = 2
MAX_STROKE_POINTS = 4096
MAX_ABS_COORD = 100.0


def registration_of(word_json: dict) -> tuple[dict, float]:
    """The crop-local registration and x-height of one frozen fixture entry."""
    baseline_y = float(word_json["baseline_y"])
    midband_y = float(word_json["midband_y"])
    xh = baseline_y - midband_y
    if xh <= 0:
        raise ValueError(f"non-positive x-height for {word_json.get('id')}: {xh}")
    return {"tx": 0, "ty": 0, "baseline_row": baseline_y - float(word_json["rect"][1])}, xh


def strokes_to_word_units(
    strokes_px: list[list[list[float]]], registration: dict, xh: float
) -> list[list[list[float]]]:
    """Crop-pixel strokes → the word's registration frame, stroke for stroke."""
    out: list[list[list[float]]] = []
    for stroke in strokes_px:
        if not stroke:
            out.append([])
            continue
        pts = np.asarray(stroke, dtype=float)
        out.append(_px_to_word_units(pts[:, 0], pts[:, 1], xh, registration).tolist())
    return out


def validate_strokes(strokes: list[list[list[float]]]) -> str | None:
    """The wire-contract violation of this trace, or None when it is clean."""
    if not strokes:
        return "no strokes recovered"
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
    """One candidate row from one recovered answer."""
    registration, xh = registration_of(word_json)
    meta = dict(raw.get("meta") or {})
    detail = raw.get("error")
    if detail:
        # Stage 2 could not recover this word at all. The row travels as a
        # FAILURE rather than being dropped: a control that silently covers
        # nine of ten words would report a better median for the nine.
        strokes: list[list[list[float]]] = []
    else:
        strokes = strokes_to_word_units(raw.get("strokes_px") or [], registration, xh)
        detail = validate_strokes(strokes)
    if detail:
        meta["detail"] = detail
    return {
        "kind": frame.get("kind", "word"),
        "specimen_id": raw["id"],
        "word": raw.get("word", frame.get("word")),
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
    parser.add_argument("--label", default=None, help="candidate label (default: the tool name)")
    parser.add_argument("--version", default=None, help="default: today (UTC)")
    args = parser.parse_args(argv)

    payload = json.loads(args.frames.read_text(encoding="utf-8"))
    frames = payload["frames"]
    root = args.fixtures_root or Path(payload.get("fixtures_root", DEFAULT_FIXTURES_ROOT))
    style, source_id, set_name = derive_set_labels(root)

    rows: list[dict] = []
    for path in sorted(args.raw.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        frame = frames.get(raw["id"])
        if frame is None:
            print(f"  ! {path.name}: no frame record for id {raw['id']} — skipped")
            continue
        word_json = json.loads((root / raw["id"] / ENTRY_FILE).read_text(encoding="utf-8"))
        rows.append(build_row(raw, frame, word_json))

    if not rows:
        print(f"no recovered answers in {args.raw}")
        return 1

    rows.sort(key=lambda row: row["specimen_id"])
    document = {
        "tool": args.tool,
        "label": args.label or args.tool,
        "version": args.version or datetime.now(UTC).date().isoformat(),
        "style": style,
        "source_id": source_id,
        "set": set_name,
        "frame": CANDIDATE_FRAME,
        "rows": rows,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / f"{args.tool}.json"
    target.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
    failed = [row for row in rows if row["status"] != "ok"]
    print(f"{target}  rows {len(rows)}  failed {len(failed)}")
    for row in failed:
        print(f"  ! {row['specimen_id']}: {row['meta'].get('detail')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
