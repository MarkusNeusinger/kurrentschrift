// German strings for the public landing page (sections/landing/*).
// Pre-i18n message catalog — key tree mirrors a future i18next `landing`
// namespace. Long prose (pillars, tools, roadmap) lives here as data; the
// component keeps only the layout logic.

export const landing = {
  hero: {
    eyebrow: 'Gotische Kursive · seit jeher von Hand',
    // Headline lines, separated by <br /> in the component; `titleEm` is the
    // italic accent word opening line 3.
    titleLine1: 'Die Schrift',
    titleLine2: 'unserer Briefe',
    titleEm: 'wieder',
    titleLine3: 'lesen',
    titleLine4: '& schreiben.',
    leadBeforeBold: 'Eine offene Bibliothek der deutschen Kurrentschrift —',
    leadBold: 'kein Font, sondern der Schreibvorgang selbst',
    leadAfterBold: ': die Gestalt der Buchstaben aus historischen Vorlagen, der Strich aus handkuratiertem Duktus.',
    ctaWrite: 'Schreiben üben',
    ctaRead: 'Buchstaben lesen',
  },
  // Hero specimen — the word written onto a real Kurrent lineature.
  specimen: {
    word: 'Kurrent',
    subline: 'leſen · ſchreiben · verſtehen',
    caption: 'Synthese in echter Hand — hier: Loth, 1866.',
    replay: '↻ nochmal schreiben',
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
