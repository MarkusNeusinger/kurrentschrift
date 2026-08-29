// Strings for the two area hubs (/lesen, /schreiben). Each hub is a small
// overview page that groups its tools as cards, so the top nav stays at three
// entries (Schriftkunde · Lesen · Schreiben). Tone follows the site's quiet,
// turn-of-the-century editorial voice (see /impressum) — warm, not officious.

// `title` is the area's short name (nav, breadcrumbs, the eyebrow over the
// hub's H1); `heading` is the H1 itself and carries the search term (SEO audit
// 2026-08-29, seo.ts); `about` is the one explanatory paragraph a hub owes a
// person — and a search engine — who lands here first: what the script is, for
// whom the tools are, in the words of the Schriftkunde (facts from there).
export const hub = {
  lesen: {
    title: 'Lesen',
    heading: 'Alte deutsche Schrift lesen lernen',
    lead: 'Alte deutsche Handschrift entziffern — Schritt für Schritt. Vom einzelnen Buchstaben bis zum ganzen Wort.',
    about:
      'Kurrent und Sütterlin — die deutsche Schreibschrift, die bis 1941 in der Schule gelehrt wurde — liest heute kaum noch jemand: Die Buchstaben haben andere Formen, und f, ſ, n, u und e sehen einander zum Verwechseln ähnlich. Wer alte Briefe, Postkarten, Kirchenbücher oder Tagebücher entziffern will, übt hier vom einzelnen Buchstaben bis zum ganzen Wort: Das Quiz fragt ab und erklärt jeden Fehlgriff, die Schreibtafel zeigt jede Vorlage Buchstabe für Buchstabe. Was Kurrent, Sütterlin und Offenbacher unterscheidet, erklärt die Schriftkunde.',
    cards: {
      quiz: {
        title: 'Lese-Quiz',
        body: 'Erkenne die Buchstaben in einem kurzen Abfragespiel — vom einzelnen Zeichen bis zum ganzen Wort.',
        cta: 'Quiz öffnen',
      },
      tafel: {
        title: 'Schreibtafel',
        body: 'Die drei historischen Vorlagen auf einen Blick — die Sütterlin schreibt sich Zug um Zug selbst. Zum Vergleichen und Nachschlagen.',
        cta: 'Zur Tafel',
      },
      vergleichen: {
        title: 'Lesart prüfen',
        body: 'Ein Wort aus deinem Brief, eine Vermutung — die Feder schreibt sie, und daneben die Lesarten, die genauso aussehen könnten.',
        cta: 'Lesart prüfen',
      },
    },
  },
  schreiben: {
    title: 'Schreiben',
    heading: 'Kurrent und Sütterlin selbst schreiben',
    lead: 'Selbst zur Feder greifen. Übe die Züge auf dem ausgedruckten Übungsblatt — oder sieh der Feder beim Schreiben zu.',
    about:
      'Die deutsche Schreibschrift lernt man wie damals: auf der Lineatur, Zug um Zug. Das Übungsblatt druckt die Lineatur der gewählten Ausgangsschrift als PDF — Kurrent (2 : 1 : 2, geneigt), Sütterlin (1 : 1 : 1, aufrecht) oder Offenbacher — mit Schräglinien und Federwinkel nach Wahl, auf Wunsch mit deinem Text als Vorschrift in den Zeilen. Die Federprobe schreibt jeden getippten Text in Sütterlin vor, mit allen Übergängen zwischen den Buchstaben: zum Abschauen, bevor die eigene Feder ansetzt.',
    cards: {
      worksheet: {
        title: 'Übungsblatt',
        body: 'Erzeuge ein Übungsblatt mit Lineatur als PDF — Verhältnis, Schräglinien und Federwinkel frei wählbar, auf Wunsch mit deinem Text als Vorschrift, fertig zum Ausdrucken.',
        cta: 'Blatt erzeugen',
      },
      federprobe: {
        title: 'Federprobe',
        body: 'Tippe einen beliebigen Text — die Feder schreibt ihn dir lebendig in Sütterlin, mit allen Übergängen.',
        cta: 'Feder ansetzen',
      },
    },
  },
} as const;
