### Added

- **The Übergänge and Wörter overviews are work lists too, and their state
  lives in the URL.** `/admin/woerter` now opens as one row per Wortprobe —
  word, specimen, stored Bahnen, Nachfahr-Status, „Andere Hand" for the
  Abb.-22 plates, open basket items and the Loss once a sweep has paid for one
  — with no image at all; a row expands in place to the same two faces
  (Original · Wie geschrieben) the card wall showed, and `?ansicht=galerie`
  brings that wall back as the opt-in. `/admin/uebergaenge` keeps its letter
  bar and its free-text field, but a matrix cell now STATES what is known
  about its combination instead of composing a picture of it: how often the
  plates wrote it, whether the library stores an override (`generiert` ·
  `Entwurf` · `Override`) and how many basket items point at it, each as a
  word rather than a border colour — which is the one piece of state on that
  page a red-green-deficient reader could not read at all. Mini renders stay
  one switch away in the gallery and under a focused join. Everything is
  derived from reads the admin already makes: no new route, no new request.
- **Six URL axes for the Wörter list, because it genuinely has six.**
  `ansicht` · `sort` · `seite` · `filter` (the free-text „Proben filtern") ·
  `status` (Alle · Offen · Nachgefahren · Unvollständig) · `reiter` (which of
  the three tabs) — the author's decision Q5 (a), spelled out in German
  because a link the author pastes somewhere has to stay readable. The shared
  `shell/listState.ts` grew those three axes as declared parts of a view's
  `ListSpec` rather than a second mechanism beside it, so one reader and one
  writer still keep the rules that make a link work: an unknown value falls
  back to the default, a default never appears in the URL, and a parameter the
  view does not declare travels through it untouched.
- **Both overviews carry their filter chips' honesty rules.** A chip counts
  how many rows it alone would select, and carries no number while the read
  behind it has not answered; a cell prints no „0 Vorkommen" and no
  „generiert" on a read that never landed; and „nichts gefunden" says whether
  the source is empty, the selection matches nothing, or the evidence is still
  missing — only the first two can be undone with „Filter zurücksetzen".

### Fixed

- **„Alle Kombinationen ansehen" no longer drops the letter it was asked
  about.** The button navigated to `/admin/uebergaenge?l=a`, a half-given pair
  was read as no focus at all, and the matrix opened on whatever authored
  letter came first — so the one question the button exists for was answered
  about a different letter. The anchor is the URL's `l=` now, the way back out
  of a join keeps it, and the matrix's own letter bar writes it.
- **Opening a join or a word no longer wipes the rest of the query string.**
  Both views rewrote the whole query on every focus change, which is how an
  overview's filter, sort and page were gone the moment a subject was opened
  and back again. They merge now, exactly as the Buchstaben view already does.
- **A failed override read no longer reports every combination as
  „generiert".** The matrix answered an admin-gated 401 with an empty list of
  stored overrides, which every cell then stated as a fact about the library.
  It stays unknown instead, and the grid says so once above itself.
