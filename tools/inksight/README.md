# inksight — route B of the Tintenfolger duel (T0, measurement only)

Runs the released **InkSight Small-p** checkpoint over the frozen wordbench
crops and turns its derendered ink into `tools/tracebench` candidates. This is
the T0 probe of `docs/proposals/tintenfolger.md` §4: the model raw, unadapted,
against 1922 Sütterlin — a documented out-of-distribution baseline the two own
routes (chain fit, follower) are measured beside.

**Nothing here is production code.** The derendered geometry stays in the
measurement layer: it never enters `core/`, the database or rendering, and it
is never a ductus source — stroke order and crossing resolution remain the
prior's job (`architektur.md` §2). That boundary is also what InkSight's own
model card asks for in its ethics note. The weights are third-party bytes and
are **not committed**; `.gitignore` keeps `.venv/`, `weights/` and `out/` out
of the repo.

## Why three stages

TensorFlow pins a whole environment: `tensorflow-text` ships no wheels for the
repo's interpreter (the repo needs Python >= 3.13, tf-text caps at 3.11), and a
600 MB ML runtime has no business anywhere near the API image. So the pipeline
is split at the process boundary, and only two small pure modules cross it
(`tokens.py`, the affine helpers in `prepare.py`):

| stage | script | environment | what it does |
|---|---|---|---|
| 1 | `prepare.py` | repo | fixture crops → 224×224 white-padded PNGs + `frames.json` (the affine per word) |
| 2 | `run_inksight.py` | **isolated venv** | PNG × prompt → raw `<ink_token_N>` decode → `out/raw/<id>.<prompt>.json` |
| 3 | `to_candidate.py` | repo | invert the affine, convert to the stored trace frame → one candidate file per prompt |

## Environment recipe

```bash
# 1. The isolated venv (Python 3.11 — tensorflow-text is the binding constraint)
uv python install 3.11
uv venv --python 3.11 tools/inksight/.venv
uv pip install -p tools/inksight/.venv/bin/python -r tools/inksight/requirements.txt

# 2. The weights (518 MB, NOT committed — see "Provenance" below)
mkdir -p tools/inksight/weights
curl -fL -o tools/inksight/weights/small-p-cpu.zip \
  https://storage.googleapis.com/derendering_model/small-p-cpu.zip
( cd tools/inksight/weights && unzip -q small-p-cpu.zip )   # → weights/small-p-cpu/
```

**Verified triple (2026-08-14, this machine):** Python 3.11.15 ·
`tensorflow-cpu` 2.20.0 · `tensorflow-text` 2.20.1 (numpy 2.2.6, pillow
11.3.0). The SavedModel loads in ~7 s (warm page cache) and exposes
`serving_default` with the kwargs `input_text` and `image_encoded` (the tensor
is named `image/encoded` — the model card's dict key; `run_inksight.py`
resolves the names from the signature instead of hard-coding either).

### The XLA trap (correctness, not performance)

On TensorFlow >= 2.18 two HLO passes change the autoregressive decode, so the
same checkpoint silently emits **different ink** than the reference
implementation — the worst possible failure mode for a measurement project.
InkSight's `utils/tensorflow.py` (github.com/google-research/inksight, issue
\#29) disables them via `XLA_FLAGS` **before the first TensorFlow import**;
`run_inksight.py::configure_xla_flags` replicates that setup (the file is not
vendored):

```
--xla_gpu_autotune_level=0
--xla_disable_hlo_passes=custom-kernel-fusion-rewriter,custom_kernel-fusion-autotuner
```

Existing user flags are preserved, a conflicting autotune level is replaced.
If you ever call the model from your own script, set the flags first — the run
will look perfectly healthy without them.

## Running it

```bash
# 1. Crops → model inputs (repo env). Default ids = the frozen tracebench dev
#    set (die · laden · linken · mit · muß · und · unter · Wer · will · zwei).
uv run python -m tools.inksight.prepare \
  --fixtures-root tools/wordbench/fixtures/suetterlin/suetterlin-1922

# 2. The model (isolated venv, run from the repo root so `tools.` imports).
#    All three prompts per crop by default.
tools/inksight/.venv/bin/python -m tools.inksight.run_inksight

# 3. Raw strokes → candidate files (repo env)
uv run python -m tools.inksight.to_candidate
```

The three prompts, all asked per crop:

| key | prompt | why |
|---|---|---|
| `derender` | `Derender the ink.` | the plain task |
| `r+d` | `Recognize and derender.` | also reports what the model *read* — the OOD gap in words |
| `text` | `Derender the ink: <word>` | we know the true word from `words.json`; this is the model's ceiling with recognition taken out |

**Measured CPU cost** (8-core WSL2, `tensorflow-cpu`, no GPU): see
"Measured on the smoke run" below. The first call also traces the graph and is
reported separately from the rest.

## The quantisation caveat (report it, never hide it)

The model answers in `<ink_token_N>` tokens: a **225-level grid over the
224 px padded frame**, i.e. one token step per model pixel. A crop whose long
side exceeds 224 px is therefore downscaled, and one token step becomes *more
than one crop pixel* — the resolution floor of every candidate this pipeline
can produce, independent of how good the model is. `prepare.py` computes it per
word (`grid_step_crop_px`, clamped at 1.0) and `to_candidate.py` carries it
into every row's `meta`. On the current dev set it is 1.00–1.38 crop px
(worst: `linken`, 310 px wide).

The other ceiling is the decoder context of 1024 tokens ≈ 500 points. A word
that hits it is silently truncated ink, so `n_ink_tokens` is logged per call
and travels into `meta` — a short stroke list with a token count at the
ceiling is a truncation, not a model opinion.

## Frames and the candidate contract

`to_candidate.py` inverts the affine per word (model frame → crop px) and then
converts crop px into the stored `word_instances` trace frame through
**`tools.laufform.harvest._px_to_word_units`** — the same function the harvest
and the follower use, deliberately imported rather than re-implemented.

Registration is `{tx: 0, ty: 0, baseline_row: baseline_y - rect[1]}` with
`xh = baseline_y - midband_y`, both read from the frozen fixture `word.json`.
`tx = 0` is not a placeholder: stored `(u,v)` labels are *not* canonical (the
composer's grid search moves `tx`, the word editor folds `ty` into
`baseline_row` — tintenfolger.md §2.1), while InkSight's output is positioned
in the crop. The crop's own frame is therefore the honest registration, and it
is the one the bench re-expresses every trace in.

Output: `out/candidates/inksight-smallp-raw.<prompt>.json`

```json
{"tool": "inksight-smallp-raw", "version": "2026-08-14", "style": "suetterlin",
 "source_id": "suetterlin-1922", "set": "words", "frame": "word_registration",
 "rows": [{"kind": "word", "specimen_id": "die", "word": "die",
           "registration_px": {"tx": 0, "ty": 0, "baseline_row": 72.0},
           "xh_px": 31.0, "strokes": [[[0.61, 0.05], [0.63, 0.91]]], "status": "ok",
           "meta": {"prompt": "...", "n_ink_tokens": 412,
                    "grid_step_crop_px": 1.0, "recognized_text": null}}]}
```

**Strokes are exactly what the model emitted** — no cleanup, no resampling, no
merging, no dropping of degenerate runs. The only judgement applied is the wire
contract of `api.schemas.WordInstanceItem` (1..128 strokes, 2..4096 points
each, |coordinate| <= 100); a row that violates it keeps its geometry and is
stamped `status: "failed"` with the reason in `meta.detail`. That is a sharp
edge on purpose: a stray single-point stroke fails its row instead of being
quietly deleted, because a repaired candidate would make the model look better
than it is. Consumers must respect `status`.

## Provenance of the weights

* **Model:** InkSight Small-p, Google Research — <https://github.com/google-research/inksight>,
  model card <https://huggingface.co/Derendering/InkSight-Small-p>
* **License:** Apache 2.0
* **Retrieved:** 2026-08-14 from
  `https://storage.googleapis.com/derendering_model/small-p-cpu.zip`
  (518 MB, unzips to `weights/small-p-cpu/` — a frozen TF SavedModel; there is
  no training code and none is planned, see tintenfolger.md §5)
* **Not committed**, and not redistributed from here: the download is a
  documented step, `weights/` is gitignored. The repo's data rules
  (`docs/reference/quellen-und-rechte.md`) apply to model bytes as well —
  the license of the bytes follows the bytes.
* Loading goes through `tf.saved_model.load`, **not** `from_pretrained_keras`:
  `huggingface_hub` v1.0 removed the Keras-2 loader the model card documents.

## Tests

`tests/test_inksight_pipeline.py` (repo env, no TensorFlow) pins the parts that
must agree across the process boundary: the token decode (pair order, the
`+225` y offset, stroke starts, invalid-token filtering), the affine roundtrip
prepare → to_candidate, and the candidate contract (frame literal, wire bounds,
`status` on violation). `run_inksight.py` is deliberately not unit-tested —
it cannot even be imported in this environment; its check is the smoke run.

## Measured on the full T0 run (2026-08-15)

All ten dev words, this machine (WSL2, 8 cores, `tensorflow-cpu`): `derender`
and `text` cost ≈ 2–6 min per word; `r+d` cost ≈ 43 min per word (it decodes
recognition text first) and was cut after ONE data point — which suffices for
the OOD diagnosis: the model reads the Sütterlin „Wer" as `Olomi`. No call
reached the 1024-token ceiling (max 441, `linken`). Bench results and the
reading (raw Small-p at 1.5× the chain fit's dtw and 8.6× ahead of the
prior-free control; crossings cleaner than the chain, retraces lost; the
`text` prompt WORSE than plain `derender` on this out-of-distribution script)
live in `docs/reference/qualitaetsmetrik.md` §14 „Route B T0".

## Measured on the smoke run (2026-08-14)

Machine: WSL2, 8 cores, no GPU (`tensorflow-cpu`), the environment recipe
above. Word `die` (crop 154×86, `grid_step_crop_px` 1.00):

| prompt | seconds | ink tokens | strokes / points |
|---|---|---|---|
| `derender` (first call of the process) | **146.9 s** — includes graph tracing + the XLA compile | 149 | 3 / 73 |
| `r+d` | **113.7 s** — the steady-state price | 124 | 2 / 61 |
| `text` | **109.8 s** | 121 | 3 / 59 |

Model load 6.7 s; no invalid tokens in any answer; all three rows convert to
`status: "ok"` candidates. `r+d` *read* the word as `<extra_id_0> vin` — the
out-of-distribution gap in one word. The three answers segment the ink
differently but agree on where it is (`u 0.33..4.64`, `v ~0..1.97` xh in every
case), and the `derender` answer was reproduced token for token in a second
process — the decode is deterministic, as a measurement input must be.

**Read the cost honestly:** the tracing/compile is paid once per process, but it
is only ~30 s of the first call — the autoregressive decode dominates, so **~2
minutes per word and prompt** is the number to plan with. A full 63-word ×
3-prompt sweep is therefore several CPU hours, which is exactly what the
proposal's "measure the first half hour, then decide about the GPU" note is
about (tintenfolger.md §4).

`recognized_text` is the answer's leftover text verbatim, T5 sentinel tokens
included — not cleaned up, for the same reason the strokes are not.

**End-to-end frame check.** The candidate produced from that answer lands on
the author's own hand trace of the same word: converted back to crop pixels the
two ink bounding boxes are `x 10.3..143.7 / y 11.0..72.9` (InkSight) against
`x 10.3..143.1 / y 8.9..74.8` (the `authored` reference row) — agreement to
~1–2 crop px on all four edges. That says the padding, the affine inversion and
the registration chain are right; it says nothing yet about trace QUALITY (73
points against the reference's 703), which is the bench's job.

