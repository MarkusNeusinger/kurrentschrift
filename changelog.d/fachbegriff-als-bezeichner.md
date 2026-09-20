### Changed

- **A German Fachbegriff with no established English term may now be an
  identifier — the language rule says so instead of contradicting the code.**
  `sprachregelung.md` said "Code: English, no exceptions" and carved out
  untranslatable domain terms only as "an English identifier and one
  explanatory comment", while merged code has practised the opposite since
  `core/laufform.py` and `core/eigenhand/befund.py` — `class Befund`,
  `def befund`, `vorschlag`/`grund`/`guete`, `VORSCHLAEGE`/`GRUND_*`, and in
  `core/eigenhand/tintentreue.py` `class Schwellen`, `sensoren_of`,
  `class Kastenzaehler`, `STUFEN`/`SENSOR_*`. Copilot reported the gap as a
  finding on #638, and every further module of the Eigenhand chain would have
  drawn the same one. Author decision of 2026-09-20, now written into
  `sprachregelung.md` §5 as a dated Stand: **comments and docstrings stay
  English without exception**, and the identifier question is settled by one
  test — *is there an established English term a reader of this domain would
  recognise?* Yes gives `stroke_width` for Schwellzug, `slant_deg` for
  Schräglage, `apiErrorText` for Fehlerschicht, each keeping the older
  "English identifier + one explanatory comment" form unchanged; no leaves the
  German word standing, because `verdict` is a worse translation of „Befund"
  than the word itself and the terms are already the glossary's and three
  settled docs'. The carve-out is deliberately narrow: identifiers only —
  schema keys stay English, the `GRUND_*` **values** remain the German display
  strings they were, a German identifier without a glossary entry is not
  covered, and the rule is forward-only rather than a renaming sweep in either
  direction. The third Verworfen item in §3 is marked superseded and kept as
  history, since its reasoning is why §5 is cut this tightly. `CLAUDE.md` and
  `.github/copilot-instructions.md` carry the corrected rule in the same
  commit — the Copilot guide with the full test and both example tables, since
  that reviewer reads the file and does not follow links.
