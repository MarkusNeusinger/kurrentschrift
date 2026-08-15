"""Stage 2 of the InkSight pipeline: model inputs → raw derendered strokes.

The ONLY file of this repo that imports TensorFlow, and it runs ONLY in the
isolated venv (`tools/inksight/.venv`, see `requirements.txt`) — from the repo
root, so that `tools.inksight.tokens` is importable:

    tools/inksight/.venv/bin/python -m tools.inksight.run_inksight \\
        [--model-dir tools/inksight/weights/small-p-cpu] \\
        [--inputs tools/inksight/out/inputs] \\
        [--frames tools/inksight/out/frames.json] \\
        [--out tools/inksight/out/raw] [--prompts all|derender|r+d|text]

The B1 ensemble (`docs/proposals/tintenfolger.md` §7.4) is the same call with
the extended sidecar instead of the plain one — the manifest names the variant
PNGs `augment.py` wrote, and every variant gets its own raw answer
`<id>.<variant>.<prompt>.json`:

    tools/inksight/.venv/bin/python -m tools.inksight.run_inksight \\
        --manifest tools/inksight/out/frames_ensemble.json \\
        --inputs tools/inksight/out/inputs_ensemble

The prompt default differs between the two modes ON PURPOSE: the plain run asks
all three prompts of ONE input, the ensemble run asks ONE prompt of N inputs.
Asking all three per variant would triple an already N-fold decode budget, and
the T0 measurement already found `derender` the best of the three on this
script — so `--prompts` defaults to `derender` in manifest mode and to `all`
without it. Everything else is shared: same model call, same decode, same record
shape (plus a `variant` field), so a plain run's output stays byte-identical.

DELIBERATELY NOT UNIT-TESTED: every line below either configures or calls
TensorFlow, which the repo environment cannot import at all (the repo needs
Python >= 3.13, tensorflow-text caps at 3.11). The testable parts live in
`tokens.py` (decode) and `prepare.py` (affine); what remains here is I/O and
one signature call, and the honest check for it is the smoke run recorded in
the README.

The XLA flag setup is the load-bearing part: on TF >= 2.18 two HLO passes
change the autoregressive decode, so the same checkpoint silently emits
DIFFERENT ink than the reference implementation. InkSight's own
`utils/tensorflow.py` (github.com/google-research/inksight, issue #29)
disables them; the same configuration is replicated here — not vendored —
and MUST run before the first TensorFlow import.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import statistics
import time
import traceback
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from tools.inksight.tokens import decode_ink


# The two HLO passes that alter the decode on TF >= 2.18.
XLA_DISABLED_PASSES = ("custom-kernel-fusion-rewriter", "custom_kernel-fusion-autotuner")

PROMPTS: dict[str, str] = {
    "derender": "Derender the ink.",
    "r+d": "Recognize and derender.",
    # Filled with the word we already know from words.json — the upper bound
    # the model can reach when recognition is taken out of the equation.
    "text": "Derender the ink: {word}",
}

DEFAULT_MODEL_DIR = Path("tools/inksight/weights/small-p-cpu")
DEFAULT_OUT = Path("tools/inksight/out")

# The prompt a manifest (ensemble) run asks when none is named — see the module
# docstring for why it is not `all`.
ENSEMBLE_DEFAULT_PROMPT = "derender"


@dataclass(frozen=True)
class _Job:
    """One model call's input: which image, for which word, under which name.

    `stem` is the raw answer's file stem before the prompt key — `<id>` for a
    plain run, `<id>.<variant>` for an ensemble run — and `variant` is None
    exactly when there is no augmentation, which is what keeps a plain run's
    record byte-identical to what it wrote before this mode existed.
    """

    entry_id: str
    word: str
    image_path: Path
    stem: str
    variant: str | None = None


def _plain_jobs(frames: dict, ids: list[str], inputs: Path) -> tuple[list[_Job], int]:
    """The classic one-input-per-word jobs, plus the count that had no input."""
    jobs: list[_Job] = []
    missing = 0
    for entry_id in ids:
        frame = frames.get(entry_id)
        image_path = inputs / f"{entry_id}.png"
        if frame is None or not image_path.is_file():
            print(f"  ! {entry_id}: no frame record or input image — skipped")
            missing += 1
            continue
        jobs.append(_Job(entry_id=entry_id, word=frame["word"], image_path=image_path, stem=entry_id))
    return jobs, missing


def _ensemble_jobs(frames: dict, ids: list[str], inputs: Path) -> tuple[list[_Job], int]:
    """One job per (word, variant) of the extended manifest.

    A variant whose PNG is missing is skipped and counted — the ensemble simply
    shrinks by one member, which `ensemble.py` reports as `n` rather than
    silently assuming N.
    """
    jobs: list[_Job] = []
    missing = 0
    for entry_id in ids:
        frame = frames.get(entry_id)
        if frame is None:
            print(f"  ! {entry_id}: no frame record — skipped")
            missing += 1
            continue
        for name, variant in frame["variants"].items():
            image_path = inputs / variant.get("image", f"{entry_id}.{name}.png")
            if not image_path.is_file():
                print(f"  ! {entry_id} [{name}]: no input image — skipped")
                missing += 1
                continue
            jobs.append(
                _Job(
                    entry_id=entry_id,
                    word=frame["word"],
                    image_path=image_path,
                    stem=f"{entry_id}.{name}",
                    variant=name,
                )
            )
    return jobs, missing


def configure_xla_flags(environ: dict[str, str] | None = None) -> str:
    """Set `XLA_FLAGS` the way InkSight's `utils/tensorflow.py` does.

    Existing user flags are preserved, a conflicting `--xla_gpu_autotune_level=`
    is replaced. Returns the value written, for logging.
    """
    env = os.environ if environ is None else environ
    flags = [f for f in shlex.split(env.get("XLA_FLAGS", "")) if not f.startswith("--xla_gpu_autotune_level=")]
    flags.append("--xla_gpu_autotune_level=0")
    flags.append(f"--xla_disable_hlo_passes={','.join(XLA_DISABLED_PASSES)}")
    value = shlex.join(flags)
    env["XLA_FLAGS"] = value
    return value


def _load_tensorflow():
    """Import TensorFlow AFTER the flags are set.

    `tensorflow_text` is mandatory even though nothing here calls it: the graph
    contains SentenceTokenizer ops that only exist once its kernels are
    registered, and without the import the load fails with a missing-op error.
    """
    import tensorflow as tf
    import tensorflow_text  # noqa: F401

    return tf


def _signature_arg_names(concrete_function) -> tuple[str, str]:
    """The signature's own kwarg names for (text, image).

    Resolved from `structured_input_signature` rather than hard-coded: the
    released checkpoint names the image tensor `image/encoded` but exposes it
    as the kwarg `image_encoded`, and a future export could differ again.
    """
    kwargs = concrete_function.structured_input_signature[1]
    text_name = next((k for k in kwargs if "text" in k), None)
    image_name = next((k for k in kwargs if "image" in k), None)
    if text_name is None or image_name is None:
        raise RuntimeError(f"unexpected signature inputs: {sorted(kwargs)}")
    return text_name, image_name


def _output_text(outputs: dict) -> str:
    """The single string output of the signature, decoded."""
    for value in outputs.values():
        if value.dtype.name == "string":
            flat = value.numpy().reshape(-1)
            return flat[0].decode("utf-8") if len(flat) else ""
    raise RuntimeError(f"no string output in {sorted(outputs)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument(
        "--inputs", type=Path, default=None, help="default: out/inputs — or the manifest's own `inputs_dir`"
    )
    parser.add_argument("--frames", type=Path, default=DEFAULT_OUT / "frames.json")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT / "raw")
    parser.add_argument(
        "--prompts",
        default=None,
        choices=["all", *PROMPTS],
        help=f"default: all — or {ENSEMBLE_DEFAULT_PROMPT} with --manifest",
    )
    parser.add_argument("--ids", nargs="*", default=None, help="restrict to these fixture ids")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="frames_ensemble.json — decode every augmented variant instead of the plain input (B1)",
    )
    args = parser.parse_args(argv)

    flags = configure_xla_flags()
    print(f"XLA_FLAGS={flags}")
    tf = _load_tensorflow()

    sidecar: Path = args.manifest or args.frames
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    frames = payload["frames"]
    ids = list(args.ids) if args.ids else list(frames)
    prompts = args.prompts or (ENSEMBLE_DEFAULT_PROMPT if args.manifest else "all")
    prompt_keys = list(PROMPTS) if prompts == "all" else [prompts]
    args.out.mkdir(parents=True, exist_ok=True)

    # The extended manifest names the directory `augment.py` wrote its variants
    # to, so the ensemble recipe needs no second path argument that must agree
    # with the first. An explicit `--inputs` still wins.
    default_inputs = (
        Path(payload["inputs_dir"]) if args.manifest and "inputs_dir" in payload else DEFAULT_OUT / "inputs"
    )
    inputs: Path = args.inputs or default_inputs

    build_jobs = _ensemble_jobs if args.manifest else _plain_jobs
    jobs, failures = build_jobs(frames, ids, inputs)
    if args.manifest:
        print(f"ensemble mode: {len(jobs)} inputs from {inputs} over {len(ids)} words, prompt {prompts!r}")

    load_started = time.perf_counter()
    model = tf.saved_model.load(str(args.model_dir))
    concrete_function = model.signatures["serving_default"]
    text_arg, image_arg = _signature_arg_names(concrete_function)
    print(f"model loaded in {time.perf_counter() - load_started:.1f}s (inputs: {text_arg}, {image_arg})")

    timings: list[float] = []
    for job in jobs:
        image = tf.io.decode_image(tf.io.read_file(str(job.image_path)), channels=3)
        encoded = tf.reshape(tf.io.encode_jpeg(image), (1, 1))

        for key in prompt_keys:
            prompt = PROMPTS[key].format(word=job.word)
            try:
                started = time.perf_counter()
                outputs = concrete_function(**{text_arg: tf.constant([prompt]), image_arg: encoded})
                elapsed = time.perf_counter() - started
                answer = _output_text(outputs)
            except Exception:  # noqa: BLE001 - one bad word must never kill the run
                failures += 1
                print(f"  ! {job.stem} [{key}]: call failed\n{traceback.format_exc()}")
                continue

            timings.append(elapsed)
            ink = decode_ink(answer)
            record = {
                "id": job.entry_id,
                "word": job.word,
                "prompt": prompt,
                "prompt_key": key,
                # Only the recognise-and-derender prompt is asked for text; for
                # the other two whatever is left over is not a reading.
                "recognized_text": ink.text_without_ink if key == "r+d" else None,
                "n_ink_tokens": ink.n_ink_tokens,
                "n_invalid_tokens": ink.n_invalid_tokens,
                "strokes_224": ink.strokes,
                "seconds": round(elapsed, 3),
                "model_dir": str(args.model_dir),
                "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            }
            if job.variant is not None:
                # Appended rather than woven in: a plain run writes the record
                # it always wrote, byte for byte.
                record["variant"] = job.variant
            (args.out / f"{job.stem}.{key}.json").write_text(
                json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            points = sum(len(s) for s in ink.strokes)
            # The decoder context is 1024 tokens (~500 points): a word that ran
            # into it is truncated ink, and the token count is what shows it.
            print(
                f"  {job.stem:<12} [{key:<8}] {elapsed:6.1f}s  "
                f"tokens {ink.n_ink_tokens:>4}  strokes {len(ink.strokes):>3}  points {points:>4}"
                + (f"  invalid {ink.n_invalid_tokens}" if ink.n_invalid_tokens else "")
                + (f"  text {ink.text_without_ink!r}" if key == "r+d" else "")
            )

    if timings:
        # The first call traces the graph and is not representative — it is
        # reported on its own so the per-word cost is an honest number.
        rest = timings[1:]
        print(f"\nfirst call {timings[0]:.1f}s (graph tracing included)")
        if rest:
            print(f"remaining {len(rest)} calls: median {statistics.median(rest):.1f}s, max {max(rest):.1f}s")
    print(f"wrote {len(timings)} answers → {args.out}" + (f" ({failures} failed/skipped)" if failures else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
