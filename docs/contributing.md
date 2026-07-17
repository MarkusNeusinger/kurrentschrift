# Contributing

**kurrentschrift is a portfolio project**, currently mid-MVP. The public site (Schriftkunde primer, reading quiz, Schreibtafel, Federprobe live writer, worksheet generator) is live at [kurrentschrift.ink](https://kurrentschrift.ink), the admin UI runs, canonical extraction and the template fit routine work, the design docs (vision + architecture §1–§17 + roadmap) are settled. That shapes what's useful to send right now.

## Welcome

- **Issues** for: factual corrections to the design docs, paleography pointers (especially around the form-variant question — see [Architektur §7](concepts/architektur.md)), public-domain source suggestions, or noting where a description in the docs doesn't match reality once more code is in place.
- **Discussion of the approach.** The "honest open question" in the README isn't rhetorical — empirical input on how tight a ductus template can be while still fitting real historical hands is genuinely useful.
- **Forking** for your own historical-handwriting project — encouraged, that's why the license is MIT.

## Not yet useful

- **Pull requests from outside** — the four MVP gates ([§8](concepts/architektur.md#8-der-mvp-kleinster-lauffähiger-renderkern)) need to land first. Once stability, allograph separation, word rendering and the slim animation playback are validated, this changes.
- **Feature requests for the post-MVP website pillars** (animation, HTR, style analysis, comparison, open data — [Architektur §10](concepts/architektur.md#10-reihenfolge--post-mvp-roadmap)). The five-phase order is intentional: render kernel first, then user-facing pillars in the documented sequence.

## Data contributions

If you have **public-domain** Kurrent material useful as a variant or reference, raise an issue with the source link and license. See [Quellen- und Rechte-Policy](reference/quellen-und-rechte.md) for what may enter the repo and [Datenablage](reference/datenablage.md) for how it's structured.

**Copyrighted material** (modern teaching books such as Süß) cannot be accepted — bibliographic references in prose only.

## Language

Code, comments, and commit messages: English. Internal design docs under `docs/`: German. See [Sprachregelung](reference/sprachregelung.md). Issues and PRs in either language are fine.

## Contact

GitHub Issues are the primary channel — for discussion of the approach as much as for bug reports. For substantial methodology questions, [LinkedIn](https://linkedin.com/in/markus-neusinger/) also works.
