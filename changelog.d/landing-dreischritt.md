### Added

- **A „So geht es“ three-step on the landing, between the hero and the three
  scripts.** The page answered what this is in ten seconds but never where to
  start: five tool cards of equal rank and no path through them. The step
  carries one sentence and one link per area, in the order the top nav names
  them — Nachschlagen, Lesen, Schreiben — and points at each area's entry
  rather than repeating the inventory the cards below already hold. Built from
  the existing `PaperCardLink`, so the focus ring, the link colour and the
  touch target come from the theme instead of a new component (#NNN).

### Changed

- **The landing lead now says who this is for.** „Für wen" was only implicit in
  „unsere Vorfahren", while family research is the audience the site is built
  around. The Kirchenbucheintrag joins the letters and deeds, and the reasons —
  Familienforschung, Archiv, Neugier — sit as an aside between dashes, so the
  sentence keeps the tone of a preface around 1900 rather than turning into a
  pitch (#NNN).

### Fixed

- **The Übungsblatt page's sitemap date was left behind by its own change.**
  #499 rewrote `worksheet.ts` but not the `<lastmod>` that the prerender prints
  as that page's visible „Stand" line. The guard added in #483 caught it on the
  next build, which is what it is for (#NNN).
