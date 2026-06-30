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
    // Warm lead, ~1900 Vorwort tone — the second clause sits in a softer ink.
    introLead: 'Such dir aus, was du heute üben magst —',
    introRest: ' drei Handgriffe, dann geht’s los.',
    scriptLabel: 'Schrift',
    scriptHint: 'welche Schreibschrift-Familie',
    // Task selector: single letters or whole words.
    taskLabel: 'Aufgabe',
    taskHint: 'einzelne Zeichen oder ganze Wörter',
    modeLetters: 'Buchstaben',
    modeWords: 'Wörter',
    difficultyLabel: 'Schwierigkeit',
    difficultyShortHint: 'wie ordentlich die Handschrift ist',
    difficultyHint:
      'Höhere Stufen zeigen denselben Buchstaben in unsaubereren Handschriften — sobald solche Vorlagen vorliegen.',
    // Summary line above the start button: "dein Quiz · Kurrent · Buchstaben · Sauber".
    summaryPrefix: 'dein Quiz',
    noLetters: 'Für diese Auswahl sind noch keine Buchstaben freigegeben.',
    noLettersOther: 'Buchstaben erscheinen hier, sobald sie im Admin-Bereich fertig kalibriert und gesperrt sind.',
    noWords: 'Für diese Auswahl sind noch keine ganzen Wörter freigegeben.',
    noWordsOther: 'Ein Wort erscheint hier, sobald jeder seiner Buchstaben kalibriert und gesperrt ist.',
    start: 'Quiz starten',
  },
  play: {
    emptyPool: 'Keine Aufgaben für diese Auswahl.',
    back: 'zurück',
    // Score band: labels (uppercased in the UI) + bare counters beside them.
    scoreLabel: 'Richtig',
    streakLabel: 'Serie',
    quit: 'beenden',
    // The question prompt under the card.
    questionLetter: 'Welcher Buchstabe ist das?',
    questionWord: 'Welches Wort ist das?',
    // Verdict line: success, then the two miss variants.
    matchStrong: 'Super Übereinstimmung',
    solutionLetter: 'Das ist ein {{letter}}.',
    solutionWord: 'Das ist „{{word}}“.',
    // Side-by-side comparison labels on a wrong pick (uppercased in the UI).
    compareYours: 'deine Wahl',
    compareCorrect: 'richtig',
    // Advance affordances.
    autoNext: 'nächste Frage …',
    next: 'Weiter',
    cropAlt: 'Buchstabe in alter Schreibschrift',
  },
  results: {
    heading: 'Auswertung',
    hitRateLabel: 'Trefferquote',
    // Empty state (ended without answering anything).
    emptyHeading: 'Noch nichts gelesen.',
    emptyBody: 'Wähle eine Aufgabe und lies ein paar Formen — dann zeigt sich hier, was dir leicht fiel und was nicht.',
    emptyCta: 'Eine Runde lesen',
    confusionsHeading: 'Häufig verwechselt',
    confusionsHint: 'Diese Formen ähneln sich — hier hast du sie vertauscht.',
    missesHeading: 'Machte Mühe',
    // Clean run: shown instead of the miss blocks when nothing was missed.
    cleanNote: 'Keine Verwechslungen — sauber gelesen.',
    // Suffix after a count, e.g. "1×".
    times: '×',
    replay: 'Weiter üben',
    settings: 'Einstellungen ändern',
  },
} as const;
