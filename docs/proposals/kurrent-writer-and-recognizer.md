# Kurrent: Generative Writer → Cheap Recognizer

> Sprache: Englisch (Recherche-Notiz, Ausnahme gemäß sprachregelung.md §1).

Reference notes for **kurrentschrift.ink**. Two questions answered here:

1. Why Alex Graves' 2013 handwriting-synthesis paper is the right anchor for the **writer**.
2. The argument that ties the writer to a cheap, browser-runnable **recognizer** ("train the reader on what the writer produces").

---

## The one-line idea

> The generative writer is also a **synthetic data engine**. Use it to emit unlimited Kurrent images *with perfect ground-truth labels*, then train a small discriminative recognizer on that output — **one cheap forward pass** at inference instead of expensive analysis-by-synthesis.

---

## 1. Why Graves 2013 is the anchor for the writer

**Graves, A. (2013). _Generating Sequences With Recurrent Neural Networks_. arXiv:1308.0850.**
The seminal work on neural handwriting generation (~4,000+ citations). It happens to solve the exact three sub-problems the writer has.

### a) Handwriting as a pen trajectory, not pixels
Graves models *online* handwriting as a sequence of pen moves: each step predicts an offset `(Δx, Δy)` plus a binary **pen-up / end-of-stroke** flag. This is literally the "computer holds the feather and moves through the letters" framing. If you build an explicit stroke/trajectory model, this is the canonical representation to base it on.

### b) Variance via a Mixture Density Network (MDN)
Instead of predicting a single next point, the output layer predicts a **probability distribution** over the next pen offset (a mixture of bivariate Gaussians + a Bernoulli for pen-up). Sampling from it is what makes output look hand-written instead of mechanical.

This is the formal version of the "variance" problem — and it matches the **global-style + local-jitter** intuition exactly: the distribution encodes where the pen *tends* to go; sampling supplies the natural deviation. A sampling **bias** parameter trades legibility against diversity (higher bias → sharper distributions → neater, less varied output).

### c) Writing *arbitrary* text via attention (the synthesis trick)
The plain prediction network just scribbles plausible-looking handwriting. Graves' **synthesis** network adds a soft Gaussian "window" (attention) that aligns the input character string to the pen trajectory, so it writes *the text you give it*. This is precisely what a fixed font cannot do for connected script, and what lets a user type a modern message and get Kurrent out.

### The honest caveat — online vs. offline data
Graves trains on **online** trajectories (the IAM-OnDB dataset: real pen paths recorded on a smart whiteboard). Historical Kurrent is **offline** — images, no pen path — so you can't train his synthesis net directly on old scans. Two ways out:

- **Author the stroke model by hand** (current plan): define glyph skeletons + variance statistics yourself. No trajectory training data required.
- **Collect your own online data**: record yourself or a calligrapher writing Kurrent on a tablet/stylus. That yields an IAM-OnDB-equivalent for Kurrent *and* sidesteps the earlier "recover the stroke order from old images" problem entirely — because you capture the trajectory at the source.

Either way, Graves is the blueprint: **trajectory representation, MDN for variance, attention for text conditioning.**

---

## 2. The connecting argument: writer ⇒ recognizer

This is the part that ties everything together (and fixes the running-cost problem).

**The data problem.** A from-scratch Kurrent *recognizer* (image → text) needs many labeled lines. Real historical material is scarce, old, and tedious to transcribe.

**The trick.** The writer already produces Kurrent from arbitrary text — so it can emit *unlimited* lines, and **you know the exact text of every one**. That is a free, perfectly-labeled training corpus.

**Train a small discriminative recognizer on it.** Standard, well-trodden architectures:

- CNN (visual features) → BiLSTM (sequence) → **CTC** loss, or
- a compact encoder–decoder **Transformer** (TrOCR-style).

**Why CTC matters here.** CTC (Connectionist Temporal Classification — Graves, Fernández, Gomez & Schmidhuber, ICML 2006) trains sequence recognition **without pre-segmenting** the input. That directly dodges **Sayre's paradox**: you can't segment connected letters without recognizing them, and vice versa. Neat detail — Graves underpins *both* halves of the system: synthesis (2013) and the recognizer loss (2006).

**Why this is the cheap path.** A discriminative recognizer is **one forward pass per line**: fast, batchable, and small enough to export to **ONNX** and run **in the browser** via `onnxruntime-web` / WASM. Server-side inference cost → ≈ 0, which is the entire point for a hobby budget.

Contrast with **analysis-by-synthesis** (render text hypotheses and match against the ink): correct in spirit, but many render-and-compare iterations per image = expensive at runtime — the exact cost driver to avoid in production.

**The generative model still earns its keep** — as a **verification / explanation layer**: overlay the synthesized rendering of the predicted text onto the original ink to show "this reading matches the strokes." Interpretable, and a nice UI moment.

---

## 3. The main risk: synthetic-to-real domain gap

A recognizer trained only on **synthetic** Kurrent can overfit to the look of your renderer and underperform on real scans (paper texture, ink bleed, fading, scanner noise, real-hand quirks the model never generates).

Mitigations, cheapest first:

- **Domain randomization** during synthesis: randomize paper/background, ink color & texture, stroke-width noise, blur, contrast, baseline wobble, slant, line spacing. The wider the synthetic distribution, the more the real distribution falls *inside* it.
- **Standard augmentation** on top (elastic distortion, noise, JPEG artifacts).
- **A small set of real labeled lines** for (a) fine-tuning and (b) — non-negotiable — a **real held-out validation set**, so you measure real-world accuracy, not synthetic accuracy.
- Later, if needed: unsupervised domain adaptation.

**Rule of thumb:** *train on synthetic, validate on real.* If real-validation accuracy tracks synthetic accuracy, your randomization is wide enough.

---

## 4. Open questions to resolve next

- **Nib type.** Do your source samples use a **broad-edge** nib (width = geometry of *nib angle vs. stroke direction*, ~constant pressure) or a **pointed/flexible** nib (width = *pressure*, thick downstroke / thin upstroke)? This decides the stroke-width model and can largely be hard-wired.
- **Authoring vs. capture.** Hand-author glyph skeletons, or collect tablet trajectories? Only the capture route lets you train a Graves-style net directly.
- **Phasing.** Writer first (the unique, shareable, reputation asset); recognizer is phase 2 and reuses the writer as its data source.

---

## References

- **Graves, A. (2013).** *Generating Sequences With Recurrent Neural Networks.* arXiv:1308.0850 — handwriting synthesis, MDN output, attention-based text conditioning. *The anchor.*
- **Graves, A., Fernández, S., Gomez, F., Schmidhuber, J. (2006).** *Connectionist Temporal Classification: Labelling Unsegmented Sequence Data with Recurrent Neural Networks.* ICML '06. doi:10.1145/1143844.1143891 — segmentation-free sequence recognition (CTC).
- **Graves, A. & Schmidhuber, J. (2008).** *Offline Handwriting Recognition with Multidimensional Recurrent Neural Networks.* NIPS 21 — the classic discriminative offline-recognition baseline.
- **Kotani, A., Tellex, S., Tompkin, J. (2020).** *Generating Handwriting via Decoupled Style Descriptors.* arXiv:2008.11354 — modern approach to explicitly separating **style** from **content**; directly relevant to variance/style control.
- **TrOCR** (Microsoft) — transformer-based OCR; a modern alternative to CNN-BiLSTM-CTC for the recognizer.
- **IAM-OnDB** — the online-handwriting dataset Graves used; the template for collecting your own Kurrent trajectories.

---

*Status: working map, not gospel. Check details against the primary sources before committing architecture.*
