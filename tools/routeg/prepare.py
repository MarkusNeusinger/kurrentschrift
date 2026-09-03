"""Stage 1 of route G: frozen fixture entries → skeleton images + a manifest.

Runs in the REPO environment (no network, no DB): it reads the frozen wordbench
fixture root and writes one thinned PNG per word plus one `frames.json` naming
exactly what stage 2 was fed.

    uv run python -m tools.routeg.prepare
        [--fixtures-root tools/wordbench/fixtures/suetterlin/suetterlin-1922]
        [--ids die laden ...] [--out tools/routeg/out] [--ink black|white]

The image written is the FROZEN skeleton (`ref_skel.npz`, the thinning of the
same `ref_mask.png` the bench's AIoU column grades against) — not a fresh
threshold over `crop.png`, and not the filled mask. Two reasons, and they point
the same way:

* re-binarising here would let the control and its ruler disagree about where
  the ink is, and that disagreement would be reported as tracing error;
* it is literally the input format the reference implementation documents.
  `wor(imagepath, …)` does no thinning of its own — `readAndBinarizeImage.m`
  only does `imbinarize(…, 0.5)` plus a one-pixel hole fill, and the shipped
  example `c-092-02__thin.png` is an 8-bit two-valued PNG with ink at 0. So the
  default `--ink black` writes exactly what a MATLAB run would consume, and the
  door to that run stays open even though this repository cannot walk through
  it (README § "Why the reference implementation is not what runs here").

Unlike the InkSight pipeline there is NO affine: the image keeps the crop's own
resolution, so a recovered point is already a crop pixel and the candidate
carries no quantisation floor of its own. The only frame conversion left is crop
px → the stored `word_instances` registration, which `to_candidate.py` does with
the harvest's own function.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from tools.tracebench.sets import TRACEBENCH_DEV_IDS


DEFAULT_FIXTURES_ROOT = Path("tools/wordbench/fixtures/suetterlin/suetterlin-1922")
DEFAULT_OUT = Path("tools/routeg/out")

# The frozen artifacts of a fixture entry. `ref_mask.png` carries the ink on the
# WHITE side (`> 127`, the same test `tools.tracebench.reference` applies);
# `ref_skel.npz` carries its thinning as a boolean array plus the EDT widths.
INK_MASK_FILE = "ref_mask.png"
SKELETON_FILE = "ref_skel.npz"
ENTRY_FILE = "word.json"


def dev_ids() -> tuple[str, ...]:
    """The frozen tracebench development split (tintenfolger.md §1), in a fixed order.

    Same contract as `tools.inksight.prepare.dev_ids` — the two routes must be
    fed the same words in the same order, or their artifacts are not
    comparable file by file. The guarded import over a ten-id literal that
    both packages carried is gone: it dated from before `tools/tracebench`
    existed and could only ever fire as a run that measured 10 of 19 words
    without saying so.
    """
    return tuple(sorted(TRACEBENCH_DEV_IDS))


def load_ink_mask(entry_dir: Path) -> np.ndarray:
    """The frozen binarised ink of one entry as a boolean image (True = ink)."""
    with Image.open(entry_dir / INK_MASK_FILE) as img:
        return np.asarray(img.convert("L")) > 127


def load_skeleton(entry_dir: Path) -> np.ndarray:
    """The frozen thinning of one entry as a boolean image (True = ink)."""
    with np.load(entry_dir / SKELETON_FILE) as data:
        return np.asarray(data["skel"], dtype=bool)


def to_image(mask: np.ndarray, ink: str) -> Image.Image:
    """A boolean image as an 8-bit two-valued PNG with ink on the named side.

    `ink="black"` is the scanned-document convention the reference
    implementation expects (`PointType.BLACK = 0`); `ink="white"` is the
    fixture's own polarity. Stated per run instead of assumed, because feeding a
    recovery algorithm the inverted image makes it trace the PAPER — which looks
    like a catastrophic result rather than the input error it is.
    """
    if ink not in ("black", "white"):
        raise ValueError(f"ink must be 'black' or 'white', not {ink!r}")
    values = np.where(mask, 0, 255) if ink == "black" else np.where(mask, 255, 0)
    return Image.fromarray(values.astype(np.uint8), mode="L")


def prepare_entry(root: Path, entry_id: str, inputs_dir: Path, ink: str) -> dict:
    """Write one thinned input PNG and return its `frames.json` record."""
    entry_dir = root / entry_id
    meta = json.loads((entry_dir / ENTRY_FILE).read_text(encoding="utf-8"))
    mask = load_ink_mask(entry_dir)
    skeleton = load_skeleton(entry_dir)
    if skeleton.shape != mask.shape:
        raise ValueError(f"{entry_id}: skeleton {skeleton.shape} does not match mask {mask.shape}")
    inputs_dir.mkdir(parents=True, exist_ok=True)
    to_image(skeleton, ink).save(inputs_dir / f"{entry_id}.png")
    height, width = mask.shape
    return {
        "id": entry_id,
        "word": meta["word"],
        "kind": meta.get("kind", "word"),
        "crop_w": int(width),
        "crop_h": int(height),
        "ink": ink,
        "ink_px": int(mask.sum()),
        "skeleton_px": int(skeleton.sum()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fixtures-root", type=Path, default=DEFAULT_FIXTURES_ROOT)
    parser.add_argument("--ids", nargs="*", default=None, help="fixture ids (default: the tracebench dev set)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--ink", default="black", choices=("black", "white"), help="which side of the binary image the ink is on"
    )
    args = parser.parse_args(argv)

    root: Path = args.fixtures_root
    if not root.is_dir():
        parser.error(f"fixtures root not found: {root}")

    ids = list(args.ids) if args.ids is not None else list(dev_ids())
    missing = [i for i in ids if not (root / i / ENTRY_FILE).is_file()]
    if missing:
        # The dev set is frozen and load-bearing: a missing member is a broken
        # fixture root, not something to work around.
        parser.error(f"fixture entries missing in {root}: {', '.join(missing)}")

    inputs_dir: Path = args.out / "inputs"
    frames = [prepare_entry(root, entry_id, inputs_dir, args.ink) for entry_id in ids]

    args.out.mkdir(parents=True, exist_ok=True)
    payload = {"fixtures_root": str(root), "ink": args.ink, "frames": {frame["id"]: frame for frame in frames}}
    (args.out / "frames.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"prepared {len(frames)} inputs → {inputs_dir}")
    for frame in frames:
        print(
            f"  {frame['id']:<12} {frame['crop_w']:>4}x{frame['crop_h']:<4} "
            f"ink {frame['ink_px']:>6} px  skeleton {frame['skeleton_px']:>4} px"
        )
    print(f"frames → {args.out / 'frames.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
