// German strings for the public landing page (sections/landing/*).
// Pre-i18n message catalog — key tree mirrors a future i18next `landing`
// namespace. Long prose (pillars, tools, roadmap) lives here as data; the
// component keeps only the layout logic.

export const landing = {
  hero: {
    eyebrow: 'Gotische Kursive · seit jeher von Hand',
    // Headline lines, separated by <br /> in the component; `titleEm` is the
    // italic accent word.
    titleLine1: 'In echter Tinte',
    titleLine2: 'geschrieben.',
    titleEm: 'Nicht',
    titleLine3: 'als Font gesetzt.',
    leadBeforeBold: 'Eine offene Bibliothek der deutschen Kurrentschrift —',
    leadBold: 'kein Font, sondern der Schreibvorgang selbst',
    leadAfterBold: ': Geometrie aus historischen Vorlagen, Strichreihenfolge aus handkuratiertem Ductus.',
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
  pillarsHeading: 'Wohin das Projekt zielt',
  pillars: [
    { num: 'i.', title: 'Tinte statt Font', desc: 'Schwellzug, Schreibreihenfolge und Allographen — Hand-Synthese, keine Glyphe pro Codepoint.' },
    { num: 'ii.', title: 'Statistik statt Bauchgefühl', desc: 'Schräglage, Schwellzug-Profile und Glyph-Verteilung der eigenen Schrift, gemessen statt geschätzt.' },
    { num: 'iii.', title: 'Lineatur zum Text', desc: 'Beliebiger Text mit passender Lineatur in einem Schritt — druckbare Vorlagen, inhaltsbewusst.' },
  ],
  // Tools that exist today (the component attaches the route paths).
  toolsHeading: 'Jetzt schon nutzbar',
  tools: {
    worksheet: {
      title: 'Lineatur-Vorlage',
      cta: 'Übungsblatt erstellen →',
      desc: 'Hilfslinien für deutsche Schreibschrift auf A4 — Verhältnis frei wählbar, optional Schräglinien, als druckfertiges PDF.',
    },
    quiz: {
      title: 'Buchstaben-Quiz',
      cta: 'Quiz starten →',
      desc: 'Lies echte Kurrent-Buchstaben aus historischer Vorlage; am Ende zeigt die Auswertung, was dir schwerfiel.',
    },
  },
  // Roadmap — staged honestly, no dead links (badge: common.soon).
  roadmapHeading: 'In Arbeit',
  roadmap: [
    { title: 'Einstieg & Alphabet', desc: 'Geschichte in zwei Sätzen, Alphabet-Tafel, die wichtigsten Regeln.' },
    { title: 'Animierte Tafel', desc: 'Schreibreihenfolge, Ansatzpunkte und Schwellzug-Aufbau live.' },
    { title: 'Lese-Lupe', desc: 'Historische Scans transkribiert, mit Erklärung pro Buchstabe.' },
    { title: 'Schrift-Analyse', desc: 'Statistik über die eigene Hand — Schräglage, Schwellzug, Verteilung.' },
    { title: 'Offene Daten', desc: 'Kanonische Glyph-Daten — Anker, Schwellzug, Ductus — zitierbar.' },
  ],
  footer: {
    scripts: 'Kurrent · Sütterlin · Offenbacher Schrift',
    disclaimer: 'Synthese, klar gekennzeichnet — wir simulieren Schrift, nicht Provenienz.',
  },
} as const;
