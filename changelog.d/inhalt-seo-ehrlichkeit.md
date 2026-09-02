### Fixed

- **The crawler's quiz page no longer offers scripts and difficulty levels
  the site does not have.** Its option list advertised Kurrent, Offenbacher
  and three handwriting levels that the setup panel has hidden since #447,
  so bots and AI answers read a Kurrent quiz with three levels — against the
  page's own title. The option tables moved into `sections/quiz/
  quizOptions.ts`, which the React-free prerender now reads too: one
  `offersChoice` rule, one set of facts, for the SPA and the crawler alike
  (#483).
- **Erlass and Rundschreiben of 1941 were swapped on the Schriftkunde page.**
  The Normalschrifterlass of 3 January was Bormann's circular ending the
  broken PRINT types; the school ban on Kurrent came as a decree of the
  education ministry to 1 September. The page claims every statement is
  sourced and its own timeline said it correctly three paragraphs down. Two
  further claims now follow `docs/schriftkunde/` as well: groundwood paper
  from the MIDDLE of the 19th century, and the Sütterlin as a simplified
  Ausgangsschrift — same look-alikes, not the same proportions (#483).
- **The Lesen hub promised an explanation for every miss.** The quiz explains
  the documented look-alike pairs and never a whole word („no explanation is
  better than an invented one“), so the paragraph now names the pairs it
  really covers (#483).

### Added

- **Explanatory paragraphs on /quiz and /federprobe, and a guard that keeps
  the sitemap honest.** The two tool pages carried 111 and 129 words of main
  content; they now open like the hubs do, in the SPA and in the prerender.
  Each `<lastmod>` is a page's visible „Stand“ line, so `npm run prerender`
  runs `scripts/check-sitemap-lastmod.mjs`, which holds every date against
  the git history of the files that page renders (`PageSpec.sources`) and
  steps aside on a shallow clone (#483).
- **A glossary section for the public product names.** Schreibtafel,
  Lesetafel and Grundtafel meant three different things with no entry
  anywhere, and „Tafel · Chart“ is a fourth; §7 names them, with Federprobe,
  Lese-Quiz, Lesart prüfen, Übungsblatt and the „Zug um Zug“ motif — which is
  a promise, not decoration: what it labels must be a real composition, never
  the fallback font (#483).

### Changed

- **Meta descriptions are capped at 155 characters, not 200.** Google
  truncates a longer one mid-sentence and the clause it drops is usually the
  promise; five descriptions had grown to 190 under the old gate. Shortened
  and pinned in `seoCoverage.test.ts` (#483).
- **One name per thing in the public copy.** „langes ſ / rundes s“ instead of
  „Lang-s, Schluss-s“, „die Feder“ in prose with „Synthese“ kept for the
  provenance captions, one spelling of the 1922 source, the spaced ratio
  „2 : 1 : 2“ everywhere, „Lese-Quiz“ in llms.txt and its two straight quotes
  closed. The Impressum's source list now names all four public-domain plates
  the site actually writes from, not two (#483).
