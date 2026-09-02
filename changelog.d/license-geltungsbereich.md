### Changed

- **`LICENSE` now states its own scope** (author's decision, 2026-09-03). A
  short paragraph above the untouched MIT text says what MIT covers: the code.
  Data under `/data/` is licensed per source, and the learned dataset —
  authored ductus templates, Laufformen, occurrence statistics, trained
  reading models — is reserved outside the grant. Until now that reservation
  lived only in README prose while `LICENSE` and `CITATION.cff` reported
  "MIT" machine-readably for the whole repository, and those are exactly the
  files that get read automatically: GitHub's licence detection, SPDX
  scanners, citation tooling. The MIT text itself is unchanged so GitHub
  still detects "MIT License", `CITATION.cff` gains a `license-url` pointing
  at the file (still valid against schema 1.2.0), and the README and
  `quellen-und-rechte.md` §5 both point at it (#NNN).
