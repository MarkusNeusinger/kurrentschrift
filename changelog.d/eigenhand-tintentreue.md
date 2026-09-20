### Added

- **Die Tintentreue — one ink-fidelity verdict per written word box.**
  `core/eigenhand/tintentreue.py` derives it on READ out of the sensors the
  follower stored, the way `befund.py` derives its verdict sheet: three
  measured steps (`folgt` · `folgt teils` · `folgt nicht`), one grey state
  carrying its reason in words, and the worst sensor deciding — a good one
  never buys a bad one a step. The thresholds are dated module constants per
  hand and ship under the label „vorläufig": they are borrowed from the plate
  and from the dev-19 set, not measured on this hand, and the blind
  calibration round replaces them once per hand. The Fassung gets a counter
  („3 von 4 Kästen folgen") and deliberately no colour of its own, which would
  be a second verdict beside `befund.vorschlag`. A shared fixture
  (`tests/fixtures/tintentreue_cases.json`) holds the Python reader and the
  SPA's `pfadRohzahlen.ts` to the same answer on the same unvalidated blob,
  as `shaping_cases.json` does for the two shapers. The pre-registration of
  the provisional bounds — with their provenance, the gates and the rulers
  that must not move — is `messjournal.md` §14 „Tintentreue `sep20`".
