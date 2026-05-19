# kurrentschrift

**→ [kurrentschrift.ink](https://kurrentschrift.ink)**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-pre--spike-orange.svg)](docs/concepts/architektur.md)

> Reading and re-inking historical German Kurrent script via ductus-model template fitting on scans.

---

## What this is

Two problems live under "historical German handwriting":

1. **Read it.** Already solved. [Transkribus](https://transkribus.org/) ships public Kurrent models at ~5–7% CER; a custom model needs ~50 transcribed pages. Integration work, not research.
2. **Write it — so the output looks like ink, not a font.** No off-the-shelf product exists. This is where the project sits.

The hard part of (2) is the **crossing problem**: from a still image of cursive script, the skeleton alone can't tell which stroke passed under which at a loop crossing. Blind skeleton tracing fails. OpenType fonts with contextual alternates fake connections and never look inked. ML synthesis (e.g. Cursive Transformer, 2025) needs *online* stroke data — pen path over time — but historical material is offline, image only.

## The approach: analysis-by-synthesis with a ductus prior

The image supplies geometry + ink width. The **ductus** — stroke order and pen-lift points — is known *a priori* for normed pre-1900 Kurrent and supplies the missing dimension. A canonical ductus template is fitted to the scan's skeleton and distance-transform profile.

The library unit is `(glyph, position, variant)`, not just glyph:

- **Position** (allograph): initial / medial / final. Medial `ſ` and final `s` are *different glyphs* with different ductus — not one `s` with a context switch.
- **Variant**: sanctioned form-of-the-norm choices (the "A = A" on teaching charts). Distinct topology, not deviation.
- **Per-instance deviation**: how a single fit departs from the canonical.

Transitions between glyphs aren't data — they fall out of `exit`/`entry` tangents + coupling height, so there's no bigram explosion. The closed set of taught ligature units (`ch`, `ck`, `tz`, `ſt`, `qu`, `ß`) is the exception: those are first-class library entries.

Two channels stay separate. **Width** (pressure / Schwellzug) is measured on the binarized mask via skeleton + distance transform — independent of darkness, robust to fading. **Darkness** is the ink-quantity trace from the dip pen refill cycle. Different signals, different purposes.

## The honest open question

How tight to make the template:

- Too rigid → won't fit real historical hands (every scribe breaks the norm).
- Too loose → crossing resolution becomes ambiguous again — the very problem the prior was supposed to solve.

This trade-off has to be found empirically. It's the project's research kernel; the spike below is designed to find or falsify it cheaply.

## Status

Pre-spike. Design docs are settled; no code yet.

**Next: the [§8 spike](docs/concepts/architektur.md#8-der-spike-kleinster-validierender-schritt).** Model medial `ſ` and final `s` as two ductus templates, fit both across ~10 instances of the author's own hand, check that the norm-generated transition curve connects cleanly to the next glyph. A weekend, not a quarter. If it holds → kernel validated, rest is engineering. If not → valuable negative result in days.

Test pair: `lesen` (medial ſ, repeated `e`, ascender, u/n-confusable final `n`) + `das` (final `s`).

## Project structure (planned)

```
kurrentschrift/
├── core/       # Python: extractor, library, connection engine
├── api/        # Backend (FastAPI)
├── app/        # Reading/practice frontend (Transkribus integration first)
├── spike/      # The minimal validating experiment
├── data/       # Sources, variants, samples (own licensing — see below)
└── docs/       # Design rationale (German)
```

## Documentation

- **[Architektur-Referenz](docs/concepts/architektur.md)** — schema, three-stage quality pipeline, research risk, build order
- **[Naming und OSS-Setup](docs/concepts/naming-und-setup.md)** — name, domain, license rationale, what was rejected and why
- **[Quellen- und Rechte-Policy](docs/reference/quellen-und-rechte.md)** — what may enter the public repo
- **[Datenablage](docs/reference/datenablage.md)** — `/data` layout, commit classes, `SOURCE.md` fields
- **[Sprachregelung](docs/reference/sprachregelung.md)** — German/English per artifact

Docs are in German (the domain is German). Code, commit messages, and this README are English.

## Data & licensing

Code is MIT. **Data is not.** Each source under `/data/sources/` carries its own license (see its `SOURCE.md`); corpora live outside git; NC-SA-derived materials never reach committed outputs.

First source: the [Loth 1866 Kurrent table](data/sources/loth-1866/SOURCE.md) — Public Domain Mark 1.0, via Wikimedia Commons — the geometry baseline for the spike. Modern copyrighted teaching books (Süß and similar) stay out of the repo entirely; bibliographic reference only.

## Contributing

This is a pre-spike portfolio project — issues and discussion are welcome, PRs are premature. See **[Contributing Guide](docs/contributing.md)** for what's useful to send right now.

## Citation

If the methodology is useful to your work, see [CITATION.cff](CITATION.cff) for citation metadata.

## License

MIT — see [LICENSE](LICENSE). **Data is separately licensed** (each source under `/data/` carries its own; see [DATA_PROVENANCE.md](data/DATA_PROVENANCE.md)).

---

**Built by [Markus Neusinger](https://linkedin.com/in/markus-neusinger/)**
