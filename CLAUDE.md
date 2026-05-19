# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

Pre-spike: only design docs exist so far. No code, no build, no tests. The planned monorepo layout (per `docs/concepts/naming-und-setup.md` §3) is:

- `/core` — Python: extractor, library, connection engine
- `/api` — Backend (FastAPI), mirrors anyplot's `api/`
- `/app` — Reading/practice frontend (Transkribus integration first)
- `/spike` — The minimal validating experiment (`docs/concepts/architektur.md` §8)
- `/data` — Sources, corpora, variants, samples, derived stats (see Data & licensing below)

The first thing to build is **the spike**, not the library or website. See `docs/concepts/architektur.md` §8 and §10 — order matters.

## Read these before substantive work

The design is already settled in the docs; do not re-litigate decisions that have an explicit "verworfen" (rejected) section. Start at `docs/index.md`.

- `docs/concepts/architektur.md` — architecture. §2 (analysis-by-synthesis), §3 (library schema), §4 (ligature exception), §5 (Schwellzug vs ink), §6 (3-stage quality pipeline), §7 (the one real research risk), §8 (spike), §9 (test words), §10 (build order)
- `docs/concepts/naming-und-setup.md` — repo/name/license/layout decisions
- `docs/reference/sprachregelung.md` — language rules (see below)
- `docs/reference/quellen-und-rechte.md` + `docs/reference/datenablage.md` — data/licensing rules (see below)

## Language conventions (strict)

From `docs/reference/sprachregelung.md`:

- **Code (identifiers, docstrings, comments): English, no exceptions.** Including commit messages.
- **README + GitHub description: English** (audience includes English-speaking genealogy).
- **Internal docs under `docs/`: German.** This is deliberate — the domain is German.
- **Website v1: German.**

German technical terms without an established English translation get an English identifier and one explanatory comment, e.g. `width_profile  # Schwellzug: pressure-driven stroke-width modulation`.

Characters themselves are *data, not code* — schema keys stay English, but values are the actual glyphs: `{"glyph": "ſt", "position": "medial", "variant": 0}`.

## The core architectural commitment

**Analysis-by-synthesis with a ductus prior.** The image supplies geometry + ink width; the canonical ductus template supplies stroke order and crossing resolution. The library unit is `(glyph, position, variant)`, not just glyph. Allographs (e.g. medial ſ vs. final s) are *separate glyphs* with separate ductus, not one glyph with variants. Positionally-sanctioned form variants (the "A = A" on teaching charts) are separate templates, not parameter deviations.

The closed ligature set (`ch`, `ck`, `tz`, `ſt`, `qu`, `ß`) are first-class library entries, not exit→entry chains. Enumerate, don't generate. Arbitrary letter pairs *are* generated from `exit`/`entry` tangents + coupling height — that's the whole point of avoiding a bigram explosion.

When in doubt about what's a glyph vs. a variant vs. a deviation, re-read `docs/concepts/architektur.md` §3 and §4.

## Data & licensing (this repo is unusual here)

Code is MIT. **Data is not covered by the code license** — each source carries its own. The `/data` tree lives outside `/core`, `/api`, `/app`, `/spike` precisely to keep this boundary visible.

Three commit classes, kept strictly separate (see `docs/reference/datenablage.md` §1):

1. **Committable:** `/data/sources/` (public-domain only, e.g. Loth 1866 SVG) and `/data/samples/own-hand/` (author's own copyright). Each gets a `SOURCE.md` with permalink, license, attribution, retrieval date.
2. **Gitignored:** `/data/corpora/` — only `SOURCE.md` + `fetch_corpus.py` are committed, never the data files. Pin DOI versions.
3. **Mixed:** `/data/derived/from-cc-by/` is committable; `/data/derived/from-nc-sa/` is gitignored (NC-SA collides with MIT).

Hard rules:

- **Süß' Lehrbuch and similar copyrighted works never enter the repo** — not as scans, not as redrawn glyphs, not as derived images. Bibliographic reference in prose is fine.
- A scan is not automatically free under German law (§72 UrhG). Prefer in order: own hand → explicit PD/CC0 → own photo of a PD original.
- "Script-downloaded" ≠ "license-free." The license of the bytes follows the bytes, not the fetch mechanism.
- Variant 0 (`v0-loth-1866`) is the canonical geometry baseline for first tests. The ductus prior is *the author's own contribution layered over* this PD geometry — Loth supplies shapes, not stroke order.

Before any data commit: *is this my expression or the expression of a protected source?* If unclear, link to the original rather than committing it.

## Test words

`lesen` (medial ſ, repeated e, ascender, u/n confusable final n) + `das` (final s) is the minimal allograph test pair for the spike. See `docs/concepts/architektur.md` §9.

## Two channels, kept separate

- **Width = pressure (Schwellzug):** from `skeletonize` + `distance_transform_edt`, measured on the mask, independent of darkness. Robust to fading.
- **Darkness = ink quantity:** separate grayscale channel; carries the dip-pen refill trace. For authentic rendering, not for geometry.

Binarization is the trap: too aggressive and a faded thick downstroke disappears, the skeleton breaks, and it gets misread as a hairline. Adaptive binarization + keep the intensity channel alongside.
