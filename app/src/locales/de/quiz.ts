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
      'Erkenne die Kurrent-Buchstaben: Jeder Buchstabe wird dir Zug um Zug geschrieben — in der Reihenfolge der Feder — und du tippst (oder wählst), welcher es ist. Richtig → weiter, falsch → noch einmal. Am Ende zeigt dir die Auswertung, welche Buchstaben dir schwerfielen.',
    scriptLabel: 'Schrift',
    lettersLabel: 'Buchstaben',
    answerLabel: 'Antwort',
    difficultyLabel: 'Schwierigkeit',
    caseLower: 'Klein ({{count}})',
    caseUpper: 'Groß ({{count}})',
    caseMixed: 'Gemischt',
    answerType: 'Tippen',
    answerChoice: 'Auswahl (Multiple Choice)',
    difficultyHint:
      'Höhere Stufen zeigen denselben Buchstaben in unsaubereren Handschriften — sobald solche Vorlagen verfügbar sind.',
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
    inSource: 'in der Vorlage:',
    sourceCropAlt: 'Loth-Vorlage',
    cropAlt: 'Kurrent-Buchstabe',
    wrong: 'Nicht richtig — versuch es nochmal.',
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
    missesHeading: 'Diese Buchstaben fielen schwer',
    noMisses: 'Kein einziger Fehler — sauber gelesen!',
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
