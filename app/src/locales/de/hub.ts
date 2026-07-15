// Strings for the two area hubs (/lesen, /schreiben). Each hub is a small
// overview page that groups its tools as cards, so the top nav stays at three
// entries (Schriftkunde · Lesen · Schreiben). Tone follows the site's quiet,
// turn-of-the-century editorial voice (see /impressum) — warm, not officious.

export const hub = {
  lesen: {
    title: 'Lesen',
    lead: 'Alte deutsche Handschrift entziffern — Schritt für Schritt. Vom einzelnen Buchstaben bis zum ganzen Wort.',
    cards: {
      quiz: {
        title: 'Buchstaben-Quiz',
        body: 'Erkenne die Buchstaben in einem kurzen Abfragespiel — vom einzelnen Zeichen bis zum ganzen Wort.',
        cta: 'Quiz öffnen',
      },
      tafel: {
        title: 'Schreibtafel',
        body: 'Die drei historischen Vorlagen auf einen Blick — die Sütterlin schreibt sich Zug um Zug selbst. Zum Vergleichen und Nachschlagen.',
        cta: 'Zur Tafel',
      },
    },
  },
  schreiben: {
    title: 'Schreiben',
    lead: 'Selbst zur Feder greifen. Übe die Züge auf dem ausgedruckten Übungsblatt — oder sieh der Feder beim Schreiben zu.',
    cards: {
      worksheet: {
        title: 'Übungsblatt',
        body: 'Erzeuge ein Übungsblatt mit Lineatur als PDF — Verhältnis, Schräglinien und Federwinkel frei wählbar, fertig zum Ausdrucken.',
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
