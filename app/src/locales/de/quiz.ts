// German strings for the public reading drill (sections/quiz/*). Pre-i18n
// message catalog — key tree mirrors a future i18next `quiz` namespace.

export const quiz = {
  title: 'Buchstaben-Quiz',
  // Quiz option lists (quizTypes.ts) — script + difficulty labels.
  scripts: {
    kurrent: 'Kurrent',
    suetterlin: 'Sütterlin',
    offenbacher: 'Offenbacher',
  },
  difficulties: {
    clean: { label: 'Sauber', hint: 'klare Lehrtafel' },
    worn: { label: 'Geübt', hint: 'flüssige Alltagshand' },
    messy: { label: 'Krakelig', hint: 'unsaubere, schwer lesbare Hand' },
  },
  setup: {
    intro:
      'Erkenne die Buchstaben der alten deutschen Schreibschrift: Jeder wird dir Zug um Zug vorgeschrieben — in der Reihenfolge der Feder — und du tippst oder wählst, welcher es ist. Ist es richtig, geht es weiter; wenn nicht, versuchst du es noch einmal. Am Ende siehst du, welche Buchstaben dir Mühe gemacht haben.',
    scriptLabel: 'Schrift',
    // Combined Modus + Groß-/Kleinschreibung selector: case options plus the
    // "Wörter" mode in one row, so the setup stays compact.
    taskLabel: 'Aufgabe',
    modeLabel: 'Modus',
    modeLetters: 'Buchstaben',
    modeWords: 'Wörter',
    lettersLabel: 'Buchstaben',
    answerLabel: 'Antwort',
    difficultyLabel: 'Schwierigkeit',
    caseLower: 'Klein ({{count}})',
    caseUpper: 'Groß ({{count}})',
    caseMixed: 'Gemischt',
    answerType: 'Tippen',
    answerChoice: 'Auswahl (Multiple Choice)',
    difficultyHint:
      'Höhere Stufen zeigen denselben Buchstaben in unsaubereren Handschriften — sobald solche Vorlagen vorliegen.',
    noLetters: 'Für diese Auswahl sind noch keine Buchstaben freigegeben.',
    noLettersUpper: 'Großbuchstaben erscheinen hier, sobald sie im Admin-Bereich fertig kalibriert und gesperrt sind.',
    noLettersOther: 'Buchstaben erscheinen hier, sobald sie im Admin-Bereich fertig kalibriert und gesperrt sind.',
    start: 'Quiz starten',
  },
  play: {
    emptyPool: 'Keine Buchstaben für diese Auswahl.',
    back: 'zurück',
    score: 'Richtig {{correct}}/{{seen}}',
    // Followed by the streak count in the chip label.
    streak: 'Serie',
    quit: 'beenden',
    solutionIs: 'Das ist',
    cropAlt: 'Buchstabe in alter Schreibschrift',
    // Prompt view toggle: the synthesised pen vs. the real chart cutout.
    viewWritten: 'Geschrieben',
    viewCrop: 'Original',
    viewToggleAria: 'Zwischen geschriebener Form und Original-Ausschnitt wechseln',
    wrong: 'Nicht ganz — versuch es noch einmal.',
    inputPlaceholder: 'Welcher Buchstabe?',
    check: 'Prüfen',
    nextTooltip: 'Nächster Buchstabe',
    next: 'Weiter',
    reveal: 'Lösung zeigen',
  },
  results: {
    heading: 'Auswertung',
    score: '{{correct}} von {{seen}} richtig',
    hitRate: '{{pct}}% Trefferquote',
    // Followed by the best-streak count in the chip label.
    bestStreak: 'Beste Serie',
    missesHeading: 'Diese Buchstaben machten Mühe',
    noMisses: 'Kein einziger Fehler — tadellos gelesen!',
    // Preceded by the miss count ("3× falsch").
    timesWrong: '× falsch',
    confusionsHeading: 'Häufig verwechselt',
    // "ſ für f gehalten" — composed around the two glyphs in the component.
    confusedFor: 'für',
    confusedAs: 'gehalten',
    replay: 'Nochmal',
    settings: 'Einstellungen',
  },
} as const;
