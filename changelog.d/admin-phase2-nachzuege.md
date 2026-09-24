### Fixed

- **The admin-redesign plan no longer says Phase 2 has two PRs open.**
  `docs/proposals/admin-redesign.md` said "geliefert bis auf zwei PRs" in its
  status blockquote and its §15 Stand, "Elf der dreizehn" in §14 step 9 and
  "Elf sind gemergt, zwei offen" above the second §15.6 table, while the same
  paragraphs said all thirteen had merged: #649 and #650 landed before #648,
  which booked the wave. All four places now say thirteen, each with a dated
  note on what it said before. The one open item is the calibration ROUND of
  PR 13. The plan had tied it to the first hand-drawn Bahn; it now states
  the code's rule, which is at least 30 boxes measured under format 2. Today
  only the follower measures, so a follower run is the only way to get
  there. A Bahn drawn by hand stays grey ("von Hand gezeichnet") while it is
  unmeasured, because `pfad --messen` (V21) is not built. Whether a
  hand-drawn Bahn belongs in the round once it is measured is new open
  question 34 in §15.7: `menschliche-bewertung.md` §8b names the follower's
  Bahn as the round's subject, and the calibration filter asks only whether
  a box was measured. §15.5 item 13
  now says that every script opens on its one hand, because `mn-kurrent` and
  `mn-offenbacher` exist as setups since 2026-09-23. The S9 scenario gets a
  dated note to the same effect. Two unreleased changelog fragments carried
  the same stale counts and are corrected in place.

- **Admin copy that still promised what has shipped.** The strip editor's
  "no letter boundaries" line said the Zuordner "kommt später", but
  `tools.eigenhand.pfad --spans` exists since #650, so the line now names the
  command. The Statistik view said the Tintentreue distribution "braucht die
  referenzfreie Ampel (Phase 2)", but the Ampel exists. The line now says
  where the per-box verdict is shown and that the hand-wide count is what is
  not built yet. The Rohzahlen hint said the Ampel would judge "später … an
  derselben Stelle", and now says where it judges today: in the list under
  "Nachfahren" and on the word crops of a filtered gallery. The whole-strip
  tile shows the same hint and has no Ampel, and the hint says so.

- **Lifts are called dotted, as they are drawn.** The Bewegung legend and two
  layer hints called the Absetzer "gestrichelt", while `liftConnector` draws
  them with `strokeStyle.dotted`. A legend that names the wrong stroke style
  fails the reader the Strichart rule is for.

- **The join detail spells its letters as glyphs.** The page's h1 and the
  browser tab read "Übergang longs → t" while the pickers beside them showed
  ſ. One function, `joinSubject`, now spells both from the glyph registry
  ("Übergang ſ → t"), and the two "Buchstabe …" buttons under the join do the
  same.

- **`/admin/edit/<key>` keeps its letter.** The retired chart-editor address
  redirected to the Buchstaben overview and dropped the subject. It now opens
  `/admin/buchstaben?g=<key>`, and the view's own reader still sends an
  unknown key to the overview.
