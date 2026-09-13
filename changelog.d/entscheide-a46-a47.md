### Changed

- **Two author decisions on the Tintenpfad adoption round are booked where
  they bind.** **A46:** the `ride_back` decoder rule keeps riding back
  capital-letter stems (`Pulver`'s `P`, `Einen`'s `E`) exactly as it does the
  ß stem — no lowercase gate; the Ecken-Runde's open question and its
  `docs/proposals/tintenfolger.md` §7.11 line are closed. **A47:** Gate (4)
  of the Tintenpfad-Adoption round (`sep12`) stays booked as "not readable" —
  the adoption's verdict continues to rest on Gates (1)–(3) alone. A new open
  arm is filed in §7.11 for the rescue path: a follower-aware stack criterion
  for `tools.tracebench.k0eval` that recognizes when two different followers
  are being compared and either reads each follower's own flags or reports
  the check as not applicable, instead of firing a warning that means
  nothing — own pre-registration, own PR, not built here.
