### Fixed

- **The Lesart page called a reading „wohl eindeutig" while it had no
  dictionary to look in.** Live, `GET /lesarten?text=Muhme` answers
  `{"readings": [], "dictionary": null}`, and the page printed „Kein Wort im
  Wörterbuch sieht dieser Lesart zum Verwechseln ähnlich — sie ist wohl
  eindeutig" with the note that the dictionary was not loaded right
  underneath it — a conclusion drawn from an empty shelf, and worse than a
  visible outage because a genealogist would have believed it. The two
  states are exclusive now: without a dictionary the page says so once and
  points at what it can still do (write the guess, show the confusable
  pairs), and the provenance line appears only where words actually came
  from. The decision is a pure function with its own test over all five
  states, so „no dictionary" can never fall back into „nothing looks like
  it" again. Loading the vocabulary itself remains the author's step
  (`tools.lesarten.sync` against the shared database) (#476).
- **„Lesetafel als PDF" produced no PDF at all.** The page showed each chart
  as a plain `<img>` while `useLesetafelPdf` rasterised the same URL with
  `crossOrigin='anonymous'`. A browser keys its HTTP cache by CORS mode, so
  the display image filed a no-CORS entry, the PDF's CORS-mode request was
  answered from it, found no `Access-Control-Allow-Origin` and was blocked —
  the printable sheet to lay beside an old letter, which is what most
  visitors come for, ended in „Das PDF konnte gerade nicht erstellt werden."
  The display image now loads in CORS mode itself, so both share one cache
  entry. A test pins the attribute on the rendered image, and the comment in
  the PDF hook names why it has to live over there (#476).
- **More than half the letters had no „im Wort sehen" link.** The example
  word came from the modern layer of the quiz word bank alone, which left j
  k p q v x y z ä ö ü ß and 19 capitals without the bridge into the
  Federprobe. It is a ladder now: modern bank word, else a historic one
  (marked as such in the link, so „Magd" is not passed off as everyday
  German), else a checked constant. Whether a word shows the letter is asked
  of the shaper instead of the spelling, which is what makes „sein" a ſ-word
  but „Fenster" an ſt-word, and „Buch" no h-word at all — the h there is
  written inside the ch ligature, where nobody can point at it. A test holds
  every letter, capital and ligature to having an example (#476).

### Changed

- **The Schreibtafel reserves each plate's box before its bytes arrive.**
  The three scans carried no dimensions while their sizes were known all
  along, so the page jumped by up to 1145 px per plate as they landed
  (desktop CLS 0.47, the route's only Lighthouse failure). The ratio comes
  from the source's own `chart_size` rather than a copied constant, so it
  cannot drift from the file the API serves (#476).
- **The quiz results lead somewhere.** „Häufig verwechselt" and „Machte
  Mühe" showed the forms and stopped there — the whole results screen held
  not one link. Each letter card is now a link to that letter on the
  Schreibtafel (`/tafel?g=<key>`), which writes it stroke by stroke beside
  its look-alikes; word tallies stay plain, having no single letter to look
  at. Quiz → Tafel → Federprobe is one loop instead of three tools standing
  next to each other (#476).
- **The Lesen hub and `llms.txt` no longer promise readings unconditionally.**
  Both described the list of look-alike words as a given; they now name what
  the page always does and make the readings conditional on a loaded
  dictionary, and `llms.txt` says what the API answers while there is none
  (#476).
