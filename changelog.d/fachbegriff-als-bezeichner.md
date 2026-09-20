### Changed

- **A German Fachbegriff with no established English term may now be an
  identifier — the language rule says so instead of contradicting the code.**
  `sprachregelung.md` said "Code: English, no exceptions" and carved out
  untranslatable domain terms only as "an English identifier and one
  explanatory comment", while merged code has practised the opposite since
  `core/laufform.py` and `core/eigenhand/befund.py` — `class Befund`,
  `def befund`, and in `core/eigenhand/tintentreue.py` `class Tintentreue`.
  Copilot reported the gap as a finding on #638, and every further module of
  the Eigenhand chain would have drawn the same one. Author decision of
  2026-09-20, now written into `sprachregelung.md` §5 as a dated Stand:
  **comments and docstrings stay English without exception**, and the
  identifier question is settled by one test — *is there an established
  English term a reader of this domain would recognise?* Yes gives
  `stroke_width` for Schwellzug, `slant_deg` for Schräglage, `apiErrorText`
  for Fehlerschicht, each keeping the older "English identifier + one
  explanatory comment" form unchanged; no leaves the German word standing,
  because `verdict` is a worse translation of „Befund" than the word itself
  and the terms are already the glossary's and three settled docs'.
- **The carve-out is per term, not per module — three terms qualify today.**
  §5.2 admits exactly Befund, Tintentreue and Laufform: glossary headwords
  that carry no English gloss there. §5.3 names the other German identifiers
  in those same modules for what they are — legacy, not licence. `deckung` is
  coverage (the glossary glosses it that way itself), `duktus` is the
  `ductus` the rest of `core/` writes, `kringel` is a loop (the same module
  already has `_loops`/`LOOP_*`), `unstetigkeit` is the discontinuity that
  `core/continuity.py` is named after, and `Schwellen`/`Kastenzaehler`/`rang`
  are thresholds, a box counter and a rank. They stay only because the
  language rule is forward-only and never restyle-swept, and they are no
  precedent for the next name. Further limits: identifiers only — schema keys
  stay English, the `GRUND_*` **values** remain the German display strings
  they were, and a German identifier without a glossary entry is not covered.
  The third Verworfen item in §3 is marked superseded and kept as history,
  since its reasoning is why §5 is cut this tightly. `CLAUDE.md`,
  `.github/copilot-instructions.md` and the `/write-docs` skill carry the
  corrected rule in the same commit — the Copilot guide with the full test and
  all three tables, since that reviewer reads the file and does not follow
  links — and `tests/test_agent_instructions.py` now pins the carve-out and
  its identifier-only boundary as a mirrored rule, so dropping it from one
  guide fails the suite.
