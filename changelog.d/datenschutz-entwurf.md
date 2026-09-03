### Added

- **The privacy section names its legal ground, the right to object and the
  right to complain.** It listed purposes, retention and recipients but never
  said what permits any of it, and neither Art. 21 nor Art. 77 appeared at all.
  The operator writes from Switzerland, so the revised Swiss FADP and — for
  readers in the EU — the GDPR are both named, along with the EDÖB and the
  visitor's own supervisory authority (#507).
- **The three technical defences added on 2026-09-02/03 are declared.** Rate
  limiting counts requests per address at the edge and at the origin, the CSP
  report endpoint receives browser reports with query and fragment cut off, and
  the origin guard carries no visitor data. Each touches an IP or a URL, so
  each is stated rather than left to be found in the code (#507).

### Changed

- **The Cloudflare location claim now says only what is known.** „Alle Dienste
  laufen in EU-Rechenzentren" was not defensible for a worldwide Anycast
  network — the promise holds only with Regional Services enabled, which
  nothing in the repo documents. Hosting, database and analytics are named with
  their actual region (europe-west4, Netherlands); for Cloudflare the text says
  European locations are used as a rule and stops there (#507).
