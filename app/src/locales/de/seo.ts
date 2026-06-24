// Per-route SEO copy (title + meta description), consumed by usePageMeta in the
// thin page mounts. One place for every public page's <title>/description so the
// catalogue stays consistent — the descriptions read for a human in a search
// result, ~150 characters, German (the site is German, see sprachregelung.md).
// Keyed by page, mirroring routes/paths.ts.

export const seo = {
  home: {
    title: 'kurrentschrift.ink — deutsche Kurrent & Sütterlin lesen und schreiben',
    description:
      'Lerne die alte deutsche Schreibschrift — Kurrent, Sütterlin, Offenbacher — lesen und schreiben: mit Schriftkunde, Buchstaben-Quiz, Schreibtafel, Übungsblättern und einer Feder, die live schreibt.',
  },
  schriftkunde: {
    title: 'Schriftkunde · kurrentschrift.ink',
    description:
      'Ein quellengestützter Überblick über die deutschen Schreibschriften — Kurrent, Sütterlin und Offenbacher: Lineatur, Federn, Tinte, Buchstaben-Besonderheiten und ihre Geschichte.',
  },
  lesen: {
    title: 'Lesen · kurrentschrift.ink',
    description:
      'Alte deutsche Handschrift lesen lernen — Schritt für Schritt vom einzelnen Buchstaben bis zum Wort: das Buchstaben-Quiz und die Schreibtafel.',
  },
  quiz: {
    title: 'Buchstaben-Quiz · kurrentschrift.ink',
    description:
      'Erkenne die Buchstaben der alten deutschen Schreibschrift in einem kurzen Quiz — jeder wird dir Zug um Zug von der Feder vorgeschrieben.',
  },
  tafel: {
    title: 'Schreibtafel · kurrentschrift.ink',
    description:
      'Die ganze Vorlage auf einen Blick: jeder Buchstabe der deutschen Schreibschrift, wie ihn die Feder schreibt — zum Vergleichen und Nachschlagen.',
  },
  schreiben: {
    title: 'Schreiben · kurrentschrift.ink',
    description:
      'Deutsche Schreibschrift selbst üben: ein Übungsblatt als PDF erzeugen oder der Feder beim Schreiben in Sütterlin zusehen.',
  },
  worksheet: {
    title: 'Übungsblatt · kurrentschrift.ink',
    description:
      'Erzeuge ein Übungsblatt als PDF — mit Lineatur und Wörtern zum Nachfahren, fertig zum Ausdrucken für die deutsche Schreibschrift.',
  },
  federprobe: {
    title: 'Federprobe · kurrentschrift.ink',
    description:
      'Tippe einen beliebigen Text — die Feder schreibt ihn dir live in Sütterlin, mit allen Übergängen zwischen den Buchstaben.',
  },
  impressum: {
    title: 'Impressum & Datenschutz · kurrentschrift.ink',
    description: 'Impressum, Datenschutz, Quellen und Lizenzen von kurrentschrift.ink.',
  },
} as const;
