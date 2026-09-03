"""Stage 1 of the InkSight pipeline: fixture crops → model inputs + frames.

Runs in the REPO environment (no TensorFlow, no network, no DB): it reads the
frozen wordbench fixture root, writes one 224x224 white-padded PNG per word and
one `frames.json` carrying the affine each crop was mapped with — the record
`to_candidate.py` inverts to get back to crop pixels.

    uv run python -m tools.inksight.prepare
        [--fixtures-root tools/wordbench/fixtures/suetterlin/suetterlin-1922]
        [--ids die laden ...] [--extra-ids lesen] [--out tools/inksight/out]

The scale+pad recipe replicates InkSight's own `utils/io.py::load_and_pad_img_dir`
(github.com/google-research/inksight): long side to 224 by
`ratio = min(224/w, 224/h)`, `int()`-truncated resize, centred paste on white.
Deviating from it would feed the model something it was not trained on — so the
inversion accounts for the truncation instead of "fixing" the forward map:
`ratio` is the nominal factor, `scale_x`/`scale_y` are the EFFECTIVE ones
(`new_side / crop_side`), and those are what the affine uses in both directions.

The 225-level token grid over that 224 px frame is the pipeline's resolution
floor. `grid_step_crop_px` states it per word in crop pixels — for a crop wider
than 224 px one token step is more than one crop pixel, i.e. the candidate
cannot be more precise than that number no matter how good the model is.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image

from tools.tracebench.sets import TRACEBENCH_DEV_IDS


# The model frame. 224 px is InkSight's input resolution; the ink tokens
# quantise it into 225 levels per dimension (see `tokens.py`).
MODEL_SIZE = 224

DEFAULT_FIXTURES_ROOT = Path("tools/wordbench/fixtures/suetterlin/suetterlin-1922")
DEFAULT_OUT = Path("tools/inksight/out")


def dev_ids() -> tuple[str, ...]:
    """The frozen tracebench development split (tintenfolger.md §1), in a fixed order.

    `sorted`, not the set's iteration order: the caller writes the ids as the
    key order of `frames.json` and as the console log, so an unordered source
    made the artifact of a measurement differ between two runs over identical
    inputs. The split itself is a `frozenset` — this is the one place that
    turns it into a sequence, so it is the one place that has to decide.

    The import is top-level and unguarded on purpose. It used to be a
    `try/except ImportError` over a ten-id literal, from the days before
    `tools/tracebench` existed; the bench has been importable since
    2026-08-14, and the fallback could only ever fire as a run that silently
    measured 10 of the 19 words and said so nowhere.
    """
    return tuple(sorted(TRACEBENCH_DEV_IDS))


@dataclass(frozen=True)
class Affine:
    """Crop pixels ⇄ the 224 px model frame for ONE word.

    `ratio` is the nominal scale factor; `scale_x`/`scale_y` are the effective
    ones after the reference implementation's `int()` truncation, and `dx`/`dy`
    the centred paste offset in model pixels.
    """

    ratio: float
    scale_x: float
    scale_y: float
    dx: int
    dy: int


def plan_affine(crop_w: int, crop_h: int, size: int = MODEL_SIZE) -> tuple[Affine, int, int]:
    """The affine for a crop of this size, plus the resized (width, height)."""
    if crop_w <= 0 or crop_h <= 0:
        raise ValueError(f"degenerate crop {crop_w}x{crop_h}")
    ratio = min(size / crop_w, size / crop_h)
    new_w = max(1, int(crop_w * ratio))
    new_h = max(1, int(crop_h * ratio))
    affine = Affine(
        ratio=ratio, scale_x=new_w / crop_w, scale_y=new_h / crop_h, dx=(size - new_w) // 2, dy=(size - new_h) // 2
    )
    return affine, new_w, new_h


def crop_to_model(x: float, y: float, affine: Affine) -> tuple[float, float]:
    """Crop pixel → model frame pixel."""
    return x * affine.scale_x + affine.dx, y * affine.scale_y + affine.dy


def model_to_crop(u: float, v: float, affine: Affine) -> tuple[float, float]:
    """Model frame pixel → crop pixel (the exact inverse of `crop_to_model`)."""
    return (u - affine.dx) / affine.scale_x, (v - affine.dy) / affine.scale_y


def grid_step_crop_px(affine: Affine) -> float:
    """One token step of the 225-level grid, expressed in crop pixels.

    Derived from the EFFECTIVE scales (the `int()`-truncated resize makes them
    differ from the nominal ratio, and the truncation always makes the resized
    side smaller, i.e. the true step slightly COARSER than the nominal one);
    the worse of the two axes is the honest floor. Clamped at 1.0: below one
    crop pixel the crop's own resolution is the binding limit, and claiming
    sub-pixel precision there would be a fiction.
    """
    return max(1.0, 1.0 / affine.scale_x, 1.0 / affine.scale_y)


def pad_to_model_frame(image: Image.Image, size: int = MODEL_SIZE) -> tuple[Image.Image, Affine]:
    """Scale the long side to `size` and centre the result on white."""
    rgb = image.convert("RGB")
    affine, new_w, new_h = plan_affine(rgb.width, rgb.height, size)
    resized = rgb.resize((new_w, new_h))
    padded = Image.new("RGB", (size, size), (255, 255, 255))
    padded.paste(resized, (affine.dx, affine.dy))
    return padded, affine


def _load_word_json(root: Path, entry_id: str) -> dict:
    return json.loads((root / entry_id / "word.json").read_text(encoding="utf-8"))


def prepare_entry(root: Path, entry_id: str, inputs_dir: Path, size: int = MODEL_SIZE) -> dict:
    """Write one model input PNG and return its `frames.json` record."""
    meta = _load_word_json(root, entry_id)
    with Image.open(root / entry_id / "crop.png") as crop:
        padded, affine = pad_to_model_frame(crop, size)
        crop_w, crop_h = crop.width, crop.height
    inputs_dir.mkdir(parents=True, exist_ok=True)
    padded.save(inputs_dir / f"{entry_id}.png")
    return {
        "id": entry_id,
        "word": meta["word"],
        "kind": meta.get("kind", "word"),
        "crop_w": crop_w,
        "crop_h": crop_h,
        **asdict(affine),
        "grid_step_crop_px": round(grid_step_crop_px(affine), 4),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fixtures-root", type=Path, default=DEFAULT_FIXTURES_ROOT)
    parser.add_argument("--ids", nargs="*", default=None, help="fixture ids (default: the tracebench dev set)")
    parser.add_argument("--extra-ids", nargs="*", default=[], help="extra ids; a missing one warns instead of failing")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--engine-render",
        action="append",
        default=[],
        metavar="WORD",
        help="NOT IMPLEMENTED — engine-rendered control inputs come with the T0 run itself",
    )
    args = parser.parse_args(argv)

    if args.engine_render:
        # TODO(T0): render `word` through `core.compose` (the same composition
        # `/write/word` serves), rasterise it at the plates' px-per-unit and
        # feed it as a control input — a crop whose ground-truth trace we own
        # exactly, which separates model error from specimen ambiguity. Not
        # stubbed silently: the flag fails until it does that.
        parser.error("--engine-render is not implemented yet (see the TODO in prepare.py)")

    root: Path = args.fixtures_root
    if not root.is_dir():
        parser.error(f"fixtures root not found: {root}")

    ids = list(args.ids) if args.ids is not None else list(dev_ids())
    missing = [i for i in ids if not (root / i / "word.json").is_file()]
    if missing:
        # The dev set is frozen and load-bearing: a missing member is a broken
        # fixture root, not something to work around.
        parser.error(f"fixture entries missing in {root}: {', '.join(missing)}")

    for extra in args.extra_ids:
        if (root / extra / "word.json").is_file():
            ids.append(extra)
        else:
            print(f"  ! extra id skipped (not in this fixture root): {extra}")

    inputs_dir: Path = args.out / "inputs"
    frames = [prepare_entry(root, entry_id, inputs_dir) for entry_id in ids]

    args.out.mkdir(parents=True, exist_ok=True)
    payload = {"model_size": MODEL_SIZE, "fixtures_root": str(root), "frames": {frame["id"]: frame for frame in frames}}
    (args.out / "frames.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"prepared {len(frames)} inputs → {inputs_dir}")
    for frame in frames:
        print(
            f"  {frame['id']:<12} {frame['crop_w']:>4}x{frame['crop_h']:<4} "
            f"ratio {frame['ratio']:.4f}  pad ({frame['dx']},{frame['dy']})  "
            f"grid step {frame['grid_step_crop_px']:.2f} crop px"
        )
    print(f"frames → {args.out / 'frames.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
