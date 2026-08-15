"""Stage 1b of the InkSight pipeline: one crop → N augmented model inputs (B1).

Runs in the REPO environment (no TensorFlow, no network, no DB), beside
`prepare.py` rather than instead of it: `prepare.py` writes the ONE plain input
per word, this module writes a whole named variant grid per word plus the
extended sidecar `frames_ensemble.json` that carries the full affine chain of
every variant — the record `ensemble.py` inverts to get back to crop pixels.

    uv run python -m tools.inksight.augment
        [--fixtures-root tools/wordbench/fixtures/suetterlin/suetterlin-1922]
        [--ids die laden ...] [--extra-ids lesen] [--out tools/inksight/out]
        [--rotations 0 -2 2 -4 4] [--scales 1.0 0.92]

**Why augmentations at all** (`docs/proposals/tintenfolger.md` §7.4, measure B1):
the released Small-p checkpoint is a frozen black box — no training, no exposed
decoder parameters — so the only handle left on it is its INPUT. Rotation and
scale jitter are the family of perturbations InkSight's own training pipeline
applies, which is what makes an augmented crop in-distribution rather than an
adversarial poke: N decodes of the same word, ranked against the measured ink,
and the best one kept (Afonin et al., ICDAR 2023, is the precedent from the same
group). The neighbourhood is deliberately SMALL — ±4°, 8 % — large enough to
move the 224 px quantisation grid against the ink and to hand the decoder a
slightly different aspect ratio, small enough that a Sütterlin word keeps its
measured slant and stays the word it is.

**Where each axis has to be applied, and why it is not obvious:**

* *Rotation* goes on the CROP, before `scale_and_pad`: rotating the padded
  224 px frame instead would resample an already-quantised image and would push
  ink into the pad. Rotating first also changes the bounding box the long-side
  normalisation then reads, which is exactly the aspect-ratio nudge B2 is about.
* *Scale* CANNOT go on the crop. `scale_and_pad` normalises the long side to
  224 px, so a uniform scale applied to the crop is undone again in the next
  step — it would survive only as integer-rounding noise. The one place a scale
  jitter survives is the FILL FACTOR of the model frame: `scale = 0.92` means the
  content spans 92 % of the frame's long side and sits on a wider white margin.
  That is what the model sees as "smaller writing", and it costs 8 % of the token
  resolution — a real price, so the ranker only pays it where the shape is read
  better for it.

**The chain, and that it is exactly invertible.** Two steps, each with a
closed-form inverse and no shared state:

    crop px --Rotation--> rotated px --Affine--> 224 px model frame

`Rotation` is rigid (`p' = R(θ)·(p − c) + t`, y down, `t` chosen so the rotated
bounding box starts at the origin); `Affine` is `prepare.py`'s own record and
`prepare.py`'s own helpers do that half in both directions — the affine maths of
the plain pipeline is REUSED here, never re-derived, because two implementations
of a frame conversion are precisely the drift a measurement pipeline cannot
afford. Because `R` is orthogonal it changes no singular value, so the token
grid step in crop pixels is still `prepare.grid_step_crop_px(affine)` — the
identity variant reproduces the plain pipeline's number exactly.

The identity variant (`rot+0_s100`) is in the grid ON PURPOSE and comes FIRST:
it is byte-identical to what `prepare.py` writes, so the ensemble always
contains the plain baseline and "best of N" can never be worse than the plain
decode by construction (and a run cut short still has the baseline).
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from PIL import Image

from tools.inksight.prepare import (
    DEFAULT_FIXTURES_ROOT,
    DEFAULT_OUT,
    MODEL_SIZE,
    Affine,
    crop_to_model,
    dev_ids,
    grid_step_crop_px,
    model_to_crop,
    plan_affine,
)


# The variant grid. A NAMED, DETERMINISTIC list — no RNG anywhere in this
# module: a measurement whose inputs cannot be re-derived from the manifest
# cannot be re-checked. Rotations are ordered by absolute angle and the scales
# start at 1.0, so the identity variant is the first element of the product.
DEFAULT_ROTATIONS: tuple[float, ...] = (0.0, -2.0, 2.0, -4.0, 4.0)
DEFAULT_SCALES: tuple[float, ...] = (1.0, 0.92)

# The plain-pipeline member of the grid, by name.
IDENTITY_VARIANT = "rot+0_s100"

# Resampling for the rotation warp and the resize. BICUBIC because
# `prepare.pad_to_model_frame` resizes with PIL's default, which is BICUBIC —
# the augmented inputs must not differ from the plain one in filter choice.
RESAMPLE = Image.Resampling.BICUBIC
WHITE = (255, 255, 255)

DEFAULT_INPUTS_DIRNAME = "inputs_ensemble"
DEFAULT_MANIFEST_NAME = "frames_ensemble.json"


@dataclass(frozen=True)
class Rotation:
    """Crop pixels → rotated image pixels: `p' = R(θ)·(p − c) + t`.

    Rigid (no scale), in image coordinates with y pointing DOWN, so a positive
    `degrees` turns the ink clockwise on screen. `cx`/`cy` are the crop centre,
    `tx`/`ty` the translation that puts the rotated bounding box's top-left
    corner on the origin, and `width`/`height` are that box rounded up — the
    size of the image the next stage is handed.
    """

    degrees: float
    cx: float
    cy: float
    tx: float
    ty: float
    width: int
    height: int

    @property
    def is_identity(self) -> bool:
        """True when this rotation maps every point onto itself."""
        return self.degrees == 0.0 and self.tx == self.cx and self.ty == self.cy


@dataclass(frozen=True)
class VariantFrame:
    """One named member of the grid: the whole chain crop px → model frame."""

    name: str
    rotation: Rotation
    scale: float  # share of the model frame's long side the content spans
    affine: Affine

    @property
    def is_identity(self) -> bool:
        """True for the member that equals the plain `prepare.py` recipe."""
        return self.rotation.is_identity and self.scale == 1.0


def variant_name(rotation_deg: float, scale: float) -> str:
    """The stable name of one grid member, e.g. `rot-4_s092`.

    Deliberately free of dots and path separators: the name travels through a
    file name (`<id>.<variant>.<prompt>.json`) and through a JSON key.
    """
    degrees = float(rotation_deg)
    rot = f"{degrees:+.0f}" if degrees.is_integer() else f"{degrees:+.1f}".replace(".", "p")
    return f"rot{rot}_s{round(float(scale) * 100):03d}"


def _rotation_matrix(degrees: float) -> tuple[float, float]:
    """`(cos, sin)` of the angle — the whole of `R(θ)` for a rigid 2-D turn."""
    radians = math.radians(float(degrees))
    return math.cos(radians), math.sin(radians)


def plan_rotation(crop_w: int, crop_h: int, degrees: float) -> Rotation:
    """The rigid turn of a crop of this size, with the box it lands in."""
    if crop_w <= 0 or crop_h <= 0:
        raise ValueError(f"degenerate crop {crop_w}x{crop_h}")
    cos, sin = _rotation_matrix(degrees)
    cx, cy = crop_w / 2.0, crop_h / 2.0
    corners = ((0.0, 0.0), (float(crop_w), 0.0), (float(crop_w), float(crop_h)), (0.0, float(crop_h)))
    turned = [((x - cx) * cos - (y - cy) * sin, (x - cx) * sin + (y - cy) * cos) for x, y in corners]
    min_x = min(p[0] for p in turned)
    min_y = min(p[1] for p in turned)
    max_x = max(p[0] for p in turned)
    max_y = max(p[1] for p in turned)
    return Rotation(
        degrees=float(degrees),
        cx=cx,
        cy=cy,
        tx=-min_x,
        ty=-min_y,
        width=max(1, math.ceil(max_x - min_x - 1e-9)),
        height=max(1, math.ceil(max_y - min_y - 1e-9)),
    )


def crop_to_rotated(x: float, y: float, rotation: Rotation) -> tuple[float, float]:
    """Crop pixel → rotated image pixel."""
    cos, sin = _rotation_matrix(rotation.degrees)
    dx, dy = x - rotation.cx, y - rotation.cy
    return dx * cos - dy * sin + rotation.tx, dx * sin + dy * cos + rotation.ty


def rotated_to_crop(x: float, y: float, rotation: Rotation) -> tuple[float, float]:
    """Rotated image pixel → crop pixel (the exact inverse of `crop_to_rotated`)."""
    cos, sin = _rotation_matrix(rotation.degrees)
    dx, dy = x - rotation.tx, y - rotation.ty
    return dx * cos + dy * sin + rotation.cx, -dx * sin + dy * cos + rotation.cy


def plan_variant(crop_w: int, crop_h: int, rotation_deg: float, scale: float, size: int = MODEL_SIZE) -> VariantFrame:
    """The full chain for one grid member of one crop.

    The scale is the fill factor: the content is normalised onto an INNER square
    of `round(scale * size)` px, and that square is centred in the `size` px
    model frame. The extra centring is folded into the affine's own paste offset,
    so the record stays one `Affine` and `prepare.py`'s inversion applies to it
    unchanged.
    """
    if not 0.0 < float(scale) <= 1.0:
        raise ValueError(f"scale must be in (0, 1]: {scale}")
    rotation = plan_rotation(crop_w, crop_h, rotation_deg)
    inner = max(1, round(float(scale) * size))
    affine, _, _ = plan_affine(rotation.width, rotation.height, inner)
    pad_x, pad_y = (size - inner) // 2, (size - inner) // 2
    affine = replace(affine, dx=affine.dx + pad_x, dy=affine.dy + pad_y)
    return VariantFrame(name=variant_name(rotation_deg, scale), rotation=rotation, scale=float(scale), affine=affine)


def crop_to_model_px(x: float, y: float, frame: VariantFrame) -> tuple[float, float]:
    """Crop pixel → model frame pixel, through the whole chain."""
    rx, ry = crop_to_rotated(x, y, frame.rotation)
    return crop_to_model(rx, ry, frame.affine)


def model_to_crop_px(u: float, v: float, frame: VariantFrame) -> tuple[float, float]:
    """Model frame pixel → crop pixel (the exact inverse of `crop_to_model_px`)."""
    rx, ry = model_to_crop(u, v, frame.affine)
    return rotated_to_crop(rx, ry, frame.rotation)


def variant_grid(
    rotations: tuple[float, ...] = DEFAULT_ROTATIONS, scales: tuple[float, ...] = DEFAULT_SCALES
) -> tuple[tuple[float, float], ...]:
    """The `(rotation_deg, scale)` pairs of the grid, in decode order.

    Scale-major so that the whole rotation fan of the untouched scale is decoded
    first; with the shipped defaults that puts the identity variant first. Names
    must be unique — a collision would silently overwrite one member's PNG and
    one member's answer, and the ensemble would quietly shrink.
    """
    pairs = tuple((float(rot), float(scale)) for scale in scales for rot in rotations)
    names = [variant_name(rot, scale) for rot, scale in pairs]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"variant names collide: {', '.join(duplicates)}")
    return pairs


def render_variant(image: Image.Image, frame: VariantFrame, size: int = MODEL_SIZE) -> Image.Image:
    """The 224 px model input of one grid member.

    The identity member short-circuits both steps, so its PNG is byte-identical
    to `prepare.pad_to_model_frame`'s — the ensemble's baseline is literally the
    plain pipeline's input, not a re-rendered lookalike.
    """
    rgb = image.convert("RGB")
    rotation = frame.rotation
    if rotation.is_identity:
        rotated = rgb
    else:
        cos, sin = _rotation_matrix(rotation.degrees)
        # PIL maps OUTPUT pixels back into the input, so the coefficients are
        # the inverse map `p = R(-θ)·(p' - t) + c`, written out row by row.
        offset_x = rotation.cx - (cos * rotation.tx + sin * rotation.ty)
        offset_y = rotation.cy - (-sin * rotation.tx + cos * rotation.ty)
        rotated = rgb.transform(
            (rotation.width, rotation.height),
            Image.Transform.AFFINE,
            (cos, sin, offset_x, -sin, cos, offset_y),
            resample=RESAMPLE,
            fillcolor=WHITE,
        )
    new_w = max(1, round(rotated.width * frame.affine.scale_x))
    new_h = max(1, round(rotated.height * frame.affine.scale_y))
    padded = Image.new("RGB", (size, size), WHITE)
    padded.paste(rotated.resize((new_w, new_h)), (frame.affine.dx, frame.affine.dy))
    return padded


def variant_record(frame: VariantFrame, image_name: str) -> dict:
    """One variant's manifest entry — everything `ensemble.py` needs to invert."""
    return {
        "variant": frame.name,
        "rotation_deg": frame.rotation.degrees,
        "scale": frame.scale,
        "rotation": asdict(frame.rotation),
        "affine": asdict(frame.affine),
        "grid_step_crop_px": round(grid_step_crop_px(frame.affine), 4),
        "image": image_name,
    }


def variant_frame_of(record: dict) -> VariantFrame:
    """The chain of one manifest entry, read back from JSON."""
    rotation = record["rotation"]
    affine = record["affine"]
    return VariantFrame(
        name=str(record["variant"]),
        rotation=Rotation(
            degrees=float(rotation["degrees"]),
            cx=float(rotation["cx"]),
            cy=float(rotation["cy"]),
            tx=float(rotation["tx"]),
            ty=float(rotation["ty"]),
            width=int(rotation["width"]),
            height=int(rotation["height"]),
        ),
        scale=float(record["scale"]),
        affine=Affine(
            ratio=float(affine["ratio"]),
            scale_x=float(affine["scale_x"]),
            scale_y=float(affine["scale_y"]),
            dx=int(affine["dx"]),
            dy=int(affine["dy"]),
        ),
    )


def _load_word_json(root: Path, entry_id: str) -> dict:
    return json.loads((root / entry_id / "word.json").read_text(encoding="utf-8"))


def prepare_variants(
    root: Path,
    entry_id: str,
    inputs_dir: Path,
    rotations: tuple[float, ...] = DEFAULT_ROTATIONS,
    scales: tuple[float, ...] = DEFAULT_SCALES,
    size: int = MODEL_SIZE,
) -> dict:
    """Write every variant PNG of one word and return its manifest record."""
    meta = _load_word_json(root, entry_id)
    inputs_dir.mkdir(parents=True, exist_ok=True)
    variants: dict[str, dict] = {}
    with Image.open(root / entry_id / "crop.png") as crop:
        rgb = crop.convert("RGB")
        crop_w, crop_h = rgb.width, rgb.height
        for rotation_deg, scale in variant_grid(rotations, scales):
            frame = plan_variant(crop_w, crop_h, rotation_deg, scale, size)
            image_name = f"{entry_id}.{frame.name}.png"
            render_variant(rgb, frame, size).save(inputs_dir / image_name)
            variants[frame.name] = variant_record(frame, image_name)
    return {
        "id": entry_id,
        "word": meta["word"],
        "kind": meta.get("kind", "word"),
        "crop_w": crop_w,
        "crop_h": crop_h,
        "variants": variants,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fixtures-root", type=Path, default=DEFAULT_FIXTURES_ROOT)
    parser.add_argument("--ids", nargs="*", default=None, help="fixture ids (default: the tracebench dev set)")
    parser.add_argument("--extra-ids", nargs="*", default=[], help="extra ids; a missing one warns instead of failing")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--rotations", nargs="*", type=float, default=list(DEFAULT_ROTATIONS), help="degrees, y down (clockwise +)"
    )
    parser.add_argument(
        "--scales", nargs="*", type=float, default=list(DEFAULT_SCALES), help="share of the model frame's long side"
    )
    args = parser.parse_args(argv)

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

    rotations = tuple(args.rotations)
    scales = tuple(args.scales)
    try:
        pairs = variant_grid(rotations, scales)
    except ValueError as error:
        parser.error(str(error))

    inputs_dir: Path = args.out / DEFAULT_INPUTS_DIRNAME
    frames = [prepare_variants(root, entry_id, inputs_dir, rotations, scales) for entry_id in ids]

    args.out.mkdir(parents=True, exist_ok=True)
    payload = {
        "model_size": MODEL_SIZE,
        "fixtures_root": str(root),
        # Named here so the model stage needs no second path argument that has
        # to agree with this one.
        "inputs_dir": str(inputs_dir),
        "grid": {
            "rotations_deg": list(rotations),
            "scales": list(scales),
            "variants": [variant_name(rot, scale) for rot, scale in pairs],
            "identity": IDENTITY_VARIANT if IDENTITY_VARIANT in {variant_name(r, s) for r, s in pairs} else None,
        },
        "frames": {frame["id"]: frame for frame in frames},
    }
    manifest = args.out / DEFAULT_MANIFEST_NAME
    manifest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"prepared {len(frames)} words x {len(pairs)} variants → {inputs_dir}")
    for frame in frames:
        steps = [variant["grid_step_crop_px"] for variant in frame["variants"].values()]
        print(
            f"  {frame['id']:<12} {frame['crop_w']:>4}x{frame['crop_h']:<4} "
            f"variants {len(frame['variants']):>3}  grid step {min(steps):.2f}..{max(steps):.2f} crop px"
        )
    print(f"manifest → {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
