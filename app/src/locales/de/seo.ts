// Per-route SEO copy (title + meta description), consumed by usePageMeta in the
// thin page mounts. One place for every public page's <title>/description so the
// catalogue stays consistent — the descriptions read for a human in a search
// result, ~150 characters, German (the site is German, see sprachregelung.md).
// Keyed by page, mirroring routes/paths.ts.
//
// Title rule (SEO audit 2026-08-29, frontend-stack.md §4): the search term a
// person would type comes FIRST (Sütterlin, Kurrent, alte deutsche Schrift,
// Übungsblatt PDF …), the brand last after „ · ", ≤ 80 characters — a title
// that only says „Lese-Quiz · kurrentschrift.ink" is findable by nobody who
// does not know the site. The ONE deliberate exception is the home page: it
// IS the brand, so it leads with the name and the terms follow („kurrent-
// schrift.ink — deutsche Kurrent & Sütterlin lesen und schreiben"). Nav labels
// and breadcrumbs keep the short page names; the H1 of each page carries the
// search term too (its own `heading` in the page's locale). Pinned by
// routes/seoCoverage.test.ts.

export const seo = {
  home: {
    title: 'kurrentschrift.ink — deutsche Kurrent & Sütterlin lesen und schreiben',
    description:
      'Alte deutsche Schreibschrift lesen und schreiben lernen — Kurrent, Sütterlin, Offenbacher: mit Quiz, Schreibtafel, Übungsblatt und einer Feder, die live schreibt.',
  },
  schriftkunde: {
    title: 'Alte deutsche Schrift: Kurrent, Sütterlin, Offenbacher · kurrentschrift.ink',
    description:
      'Ein quellengestützter Überblick über die deutschen Schreibschriften — Kurrent, Sütterlin und Offenbacher: Lineatur, Federn, Tinte, Buchstaben-Besonderheiten und ihre Geschichte.',
  },
  lesen: {
    title: 'Alte deutsche Schrift lesen lernen · kurrentschrift.ink',
    description:
      'Alte deutsche Handschrift lesen lernen — Schritt für Schritt vom einzelnen Buchstaben bis zum Wort: das Lese-Quiz und die Schreibtafel.',
  },
  quiz: {
    title: 'Sütterlin-Quiz: alte deutsche Schrift lesen üben · kurrentschrift.ink',
    description:
      'Erkenne Buchstaben und ganze Wörter der alten deutschen Schreibschrift in einem kurzen Quiz — viele davon Zug um Zug von der Feder live geschrieben.',
  },
  tafel: {
    title: 'Sütterlin-Alphabet und Kurrent-Alphabet: die Schreibtafel · kurrentschrift.ink',
    description:
      'Die drei historischen Vorlagen der deutschen Schreibschrift auf einen Blick — die Sütterlin Zug um Zug von der Feder geschrieben, zum Vergleichen und Nachschlagen.',
  },
  vergleichen: {
    title: 'Alte deutsche Schrift entziffern: Lesart prüfen · kurrentschrift.ink',
    description:
      'Ein Wort aus einem alten Brief, eine Vermutung — die Feder schreibt sie in Sütterlin und daneben die Lesarten, die genauso aussehen könnten (n/u, e/n, f/ſ). Zum Vergleichen mit dem Original.',
  },
  schreiben: {
    title: 'Kurrent und Sütterlin schreiben lernen · kurrentschrift.ink',
    description:
      'Deutsche Schreibschrift selbst üben: ein Übungsblatt als PDF erzeugen oder der Feder beim Schreiben in Sütterlin zusehen.',
  },
  worksheet: {
    title: 'Übungsblatt Sütterlin & Kurrent als PDF · kurrentschrift.ink',
    description:
      'Erzeuge ein Übungsblatt als PDF — Lineatur mit frei wählbarem Verhältnis, Schräglinien und Federwinkel, auf Wunsch mit deinem Text als Vorschrift in Sütterlin, fertig zum Ausdrucken.',
  },
  federprobe: {
    title: 'Text in Sütterlin schreiben lassen: die Federprobe · kurrentschrift.ink',
    description:
      'Tippe einen beliebigen Text — die Feder schreibt ihn dir live in Sütterlin, mit allen Übergängen zwischen den Buchstaben.',
  },
  impressum: {
    title: 'Impressum & Datenschutz · kurrentschrift.ink',
    description: 'Impressum, Datenschutz, Quellen und Lizenzen von kurrentschrift.ink.',
  },
  notFound: {
    title: 'Seite nicht gefunden · kurrentschrift.ink',
    description: 'Unter dieser Adresse liegt nichts — der Link ist veraltet oder vertippt.',
    // Soft-404 (nginx answers 200): keep it out of the index, see usePageMeta.
    noindex: true,
  },
} as const;
