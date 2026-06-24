// German strings for the public landing page (sections/landing/*).
// Pre-i18n message catalog — key tree mirrors a future i18next `landing`
// namespace. Long prose (pillars, tools, roadmap) lives here as data; the
// component keeps only the layout logic.

export const landing = {
  hero: {
    // The brand word the hero writes live with the pen. Rendered in the
    // GL-GermanCursive show-script (a marked specimen, per the legibility rule);
    // `wordAria` is the plain-text label for screen readers and the title attr.
    // Long-s (ſ) at the syllable start of "-ſchrift" per the Kurrent rule.
    word: 'Kurrentſchrift',
    wordAria: 'Kurrentschrift',
    wordCaption: '— ein deutsches Wort, geschrieben wie vor hundert Jahren.',
    title: 'Alte Briefe wieder lesen — und selbst zur Feder greifen.',
    leadBeforeBold:
      'Kurrent, Sütterlin und Offenbacher — die Schriften, in denen unsere Vorfahren ihre Briefe und Urkunden festhielten und die heute',
    leadBold: 'kaum noch jemand entziffert',
    leadAfterBold:
      '. Diese Sammlung führt zurück: sie zu lesen, mit der Feder nachzuschreiben und Zug um Zug zu verstehen.',
    ctaWrite: 'Schreiben üben',
    ctaRead: 'Buchstaben lesen',
    replay: '↻ noch einmal schreiben',
  },
  // The thesis — the three-way combination that makes this project different.
  // Prose in the site's warm turn-of-the-century voice (meaning unchanged).
  pillarsHeading: 'Was hier entstehen soll',
  pillars: [
    { num: 'i.', title: 'Tinte statt Font', desc: 'Schwellzug, Strichfolge und die Form jedes Buchstabens nach seinem Platz im Wort — Schrift, wie sie der Feder entfließt, nicht wie sie der Setzkasten gießt.' },
    { num: 'ii.', title: 'Statistik statt Bauchgefühl', desc: 'Schräglage, Druck und Buchstabenform der eigenen Hand, in Zahlen gefasst — gemessen, nicht geschätzt.' },
    { num: 'iii.', title: 'Lineatur zum Text', desc: 'Zu jedem Text die rechte Lineatur, in einem Zuge — Vorlagen, druckfertig und dem Inhalt angemessen.' },
  ],
  // Tools that exist today (the component attaches the route paths).
  toolsHeading: 'Was schon zur Hand ist',
  tools: {
    worksheet: {
      title: 'Lineatur-Vorlage',
      cta: 'Übungsblatt erstellen →',
      desc: 'Hilfslinien für die deutsche Schreibschrift auf einem Bogen A4 — das Verhältnis frei gewählt, auf Wunsch mit Schräglinien, druckfertig als PDF.',
    },
    scribe: {
      title: 'Federprobe',
      cta: 'Wort schreiben lassen →',
      desc: 'Ein beliebiges Wort eingeben — und zusehen, wie der nachgebildete Duktus es Zug um Zug in Sütterlin schreibt, samt den Übergängen von Buchstabe zu Buchstabe.',
    },
    quiz: {
      title: 'Buchstaben-Quiz',
      cta: 'Quiz starten →',
      desc: 'Echte Kurrent-Buchstaben aus alter Vorlage lesen; am Ende weist die Auswertung, was Mühe bereitete.',
    },
  },
  // Roadmap — staged honestly, no dead links (badge: common.soon).
  roadmapHeading: 'In Vorbereitung',
  roadmap: [
    { title: 'Einstieg & Alphabet', desc: 'Die Geschichte in zwei Sätzen, eine Alphabet-Tafel und die wichtigsten Regeln — eine kleine Fibel zum Anfangen.' },
    { title: 'Animierte Tafel', desc: 'Strichfolge, Ansatzpunkte und Schwellzug — der Feder bei der Arbeit zugesehen.' },
    { title: 'Lese-Lupe', desc: 'Alte Scans, Zeile um Zeile übertragen — mit einer Erläuterung zu jedem Buchstaben.' },
    { title: 'Schrift-Analyse', desc: 'Die eigene Hand in Zahlen — Schräglage, Schwellzug und Verteilung, fein säuberlich vermessen.' },
    { title: 'Offene Daten', desc: 'Die Glyph-Daten — Anker, Schwellzug, Duktus — offen und frei zu zitieren.' },
  ],
  footer: {
    scripts: 'Kurrent · Sütterlin · Offenbacher Schrift',
    disclaimer: 'Synthese, deutlich als solche gekennzeichnet — nachgebildete Schrift, kein historisches Original.',
  },
} as const;
