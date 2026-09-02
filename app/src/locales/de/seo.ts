// Per-route SEO copy (title + meta description), consumed by usePageMeta in the
// thin page mounts. One place for every public page's <title>/description so the
// catalogue stays consistent — the descriptions read for a human in a search
// result, German (the site is German, see sprachregelung.md).
// Keyed by page, mirroring routes/paths.ts.
//
// Description rule: at most 155 characters — Google truncates a longer one
// mid-sentence, so the last clause is lost exactly where the promise usually
// sits. Pinned by routes/seoCoverage.test.ts (the gate allowed 200 until the
// website audit 2026-09-02 found five descriptions running to 190).
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
      'Alte deutsche Schrift lesen und schreiben lernen: Kurrent, Sütterlin, Offenbacher — Quiz, Schreibtafel, Übungsblatt und eine Feder, die live schreibt.',
  },
  schriftkunde: {
    title: 'Alte deutsche Schrift: Kurrent, Sütterlin, Offenbacher · kurrentschrift.ink',
    description:
      'Quellengestützter Überblick über Kurrent, Sütterlin und Offenbacher: Lineatur, Federn, Tinte, Buchstaben-Besonderheiten, Chronologie und das Verbot 1941.',
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
      'Sütterlin-, Kurrent- und Offenbacher-Alphabet auf einen Blick: die Sütterlin Zug um Zug geschrieben, mit Strichfolge je Buchstabe — als Lesetafel-PDF.',
  },
  vergleichen: {
    title: 'Alte deutsche Schrift entziffern: Lesart prüfen · kurrentschrift.ink',
    description:
      'Ein Wort aus einem alten Brief, eine Vermutung: Die Feder schreibt sie in Sütterlin — daneben die Wörter, die genauso aussehen könnten (n/u, e/n, f/ſ).',
  },
  schreiben: {
    title: 'Kurrent und Sütterlin schreiben lernen · kurrentschrift.ink',
    description:
      'Deutsche Schreibschrift selbst üben: ein Übungsblatt als PDF erzeugen oder der Feder beim Schreiben in Sütterlin zusehen.',
  },
  worksheet: {
    title: 'Übungsblatt Sütterlin & Kurrent als PDF · kurrentschrift.ink',
    description:
      'Übungsblatt für Sütterlin und Kurrent als PDF: Lineatur mit wählbarem Verhältnis, Schräglinien und Federwinkel, auf Wunsch mit deinem Text als Vorschrift.',
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
