### Fixed

- **The word round drew every loop interior solid.** A pen stroke's silhouette
  is an exterior ring plus the counters it encloses — the `Z` of "Zorn" ships
  155 + 36 + 16 points — and the arm file flattened them into independent
  shapes, so the page filled each one and the writing came out a blob wherever
  it has a loop. The rings now stay grouped per pen stroke and are drawn as one
  `fill-rule="evenodd"` path, the same contract the SPA has always used
  (`app/src/lib/svg.ts::ringsToPathD`). Caught by the author on the first page
  he opened, before any round was judged.
- **A flat ring list is refused rather than read as a single-ring shape.** That
  is the shape of the bug above, and it parses perfectly — it would have failed
  silently on every screen with a loop, which is the one thing a judging
  session cannot afford. The arm format is now 2 and names the old one in the
  error, so an arm gets re-produced instead of judged.
