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
    wordCaption: '— ein deutsches Wort, von Hand mit der Feder geschrieben.',
    title: 'Die Schrift unserer Briefe — wieder lesen und schreiben.',
    leadBeforeBold: 'Eine offene Bibliothek der deutschen Kurrentschrift —',
    leadBold: 'kein Font, sondern der Schreibvorgang selbst',
    leadAfterBold: ': die Gestalt der Buchstaben aus historischen Vorlagen, der Strich aus handkuratiertem Duktus.',
    ctaWrite: 'Schreiben üben',
    ctaRead: 'Buchstaben lesen',
    replay: '↻ noch einmal schreiben',
  },
  // The thesis — the three-way combination that makes this project different.
  pillarsHeading: 'Was hier entstehen soll',
  pillars: [
    { num: 'i.', title: 'Tinte statt Font', desc: 'Schwellzug, Strichfolge und die Buchstabenformen je nach Stellung im Wort — Schrift wie aus der Feder, nicht aus dem Setzkasten.' },
    { num: 'ii.', title: 'Statistik statt Bauchgefühl', desc: 'Schräglage, Schwellzug und Buchstabenformen der eigenen Hand — gemessen, nicht geschätzt.' },
    { num: 'iii.', title: 'Lineatur zum Text', desc: 'Jeder Text mit der passenden Lineatur in einem Zug — druckfertige Vorlagen, dem Inhalt angemessen.' },
  ],
  // Tools that exist today (the component attaches the route paths).
  toolsHeading: 'Was heute schon bereitsteht',
  tools: {
    worksheet: {
      title: 'Lineatur-Vorlage',
      cta: 'Übungsblatt erstellen →',
      desc: 'Hilfslinien für deutsche Schreibschrift auf A4 — das Verhältnis frei wählbar, auf Wunsch mit Schräglinien, als druckfertiges PDF.',
    },
    scribe: {
      title: 'Federprobe',
      cta: 'Wort schreiben lassen →',
      desc: 'Tippe ein beliebiges Wort und sieh, wie der synthetisierte Duktus es Zug um Zug in Sütterlin schreibt — mit den Übergängen zwischen den Buchstaben.',
    },
    quiz: {
      title: 'Buchstaben-Quiz',
      cta: 'Quiz starten →',
      desc: 'Lies echte Kurrent-Buchstaben aus historischer Vorlage; am Ende zeigt die Auswertung, was dir Mühe machte.',
    },
  },
  // Roadmap — staged honestly, no dead links (badge: common.soon).
  roadmapHeading: 'In Vorbereitung',
  roadmap: [
    { title: 'Einstieg & Alphabet', desc: 'Die Geschichte in zwei Sätzen, eine Alphabet-Tafel, die wichtigsten Regeln — eine kleine Fibel.' },
    { title: 'Animierte Tafel', desc: 'Strichfolge, Ansatzpunkte und Schwellzug — der Feder beim Schreiben zugesehen.' },
    { title: 'Lese-Lupe', desc: 'Historische Scans, Zeile für Zeile übertragen — mit Erklärung zu jedem Buchstaben.' },
    { title: 'Schrift-Analyse', desc: 'Die eigene Hand in Zahlen — Schräglage, Schwellzug, Verteilung.' },
    { title: 'Offene Daten', desc: 'Die Glyph-Daten — Anker, Schwellzug, Duktus — offen und zitierbar.' },
  ],
  footer: {
    scripts: 'Kurrent · Sütterlin · Offenbacher Schrift',
    disclaimer: 'Synthese, klar gekennzeichnet — nachgebildete Schrift, kein historisches Original.',
  },
} as const;
