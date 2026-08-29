// German strings for the public reading drill (sections/quiz/*). Pre-i18n
// message catalog — key tree mirrors a future i18next `quiz` namespace.

export const quiz = {
  title: 'Lese-Quiz',
  // Quiz option lists (quizTypes.ts) — script + difficulty labels.
  scripts: {
    kurrent: 'Kurrent',
    suetterlin: 'Sütterlin',
    offenbacher: 'Offenbacher',
  },
  difficulties: {
    clean: { label: 'Sauber', hint: 'klare Lehrtafel' },
    worn: { label: 'Flüssig', hint: 'geübte Alltagshand' },
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
    noLettersOther: 'Buchstaben erscheinen hier, sobald sie fertig nachgeschrieben und freigegeben sind.',
    noWords: 'Für diese Auswahl sind noch keine ganzen Wörter freigegeben.',
    noWordsOther: 'Ein Wort erscheint hier, sobald jeder seiner Buchstaben nachgeschrieben und freigegeben ist.',
    start: 'Quiz starten',
    // Provenance caption under the setup rows — names the source the letter
    // forms come from, like the Tafel and the Federprobe do.
    sourceNote: 'Nachgebildet aus der gemeinfreien Sütterlin-Ausgangsschrift von 1922.',
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
    matchStrong: 'Richtig gelesen.',
    solutionLetter: 'Das ist ein {{letter}}.',
    solutionWord: 'Das ist „{{word}}“.',
    // Side-by-side comparison labels on a wrong pick (uppercased in the UI).
    compareYours: 'deine Wahl',
    compareCorrect: 'richtig',
    // Lesefallen (sections/quiz/lesefallen.ts): the rule shown under the verdict
    // after a wrong pick — the feature that tells the shown form from the
    // guessed letter, in the words of docs/schriftkunde/orthographie-regeln.md
    // §1/§3 and the Schriftkunde page. Each sentence describes the form on the
    // card (the correct one), so a pair has one sentence per direction.
    rules: {
      longsAsF:
        'Das lange ſ und das f unterscheidet nur der Querstrich — hier fehlt er. Das ſ steht am Silbenanfang und im Silbeninneren, das runde s nur am Silbenende.',
      fAsLongs: 'Der Querstrich macht das f — ohne ihn wäre es ein langes ſ.',
      roundS: 'Das runde s steht nur am Silben- und Wortende; im Wortinneren schreibt man das lange ſ.',
      nAsU: 'n und u sind formgleich — nur das u trägt einen kleinen Bogen darüber. Hier fehlt er: ein n.',
      uAsN: 'n und u sind formgleich — das u trägt zur Unterscheidung seinen Bogen. Hier steht er: ein u.',
      eAsN: 'Das e erinnert an ein n, steht aber enger — zwei schmale Züge.',
      nAsE: 'Das n ist breiter als das e: zwei gleich weite Bögen.',
      mAsN: 'Das m hat drei Züge, das n nur zwei.',
      nAsM: 'Nur zwei Züge — das m hätte drei.',
      iAsJ: 'Das i bleibt auf der Grundlinie; das j hat eine Unterlänge.',
      jAsI: 'Die Unterlänge macht das j — das i bleibt auf der Grundlinie.',
      iAsE: 'Das i ist ein einzelner Zug mit dem Punkt darüber; das e hat zwei enge Züge.',
      tAsL: 'Das t hat einen Querbalken und keine Schleife; das l steigt mit einer Schleife auf.',
      lAsT: 'Die Schleife macht das l — das t hätte stattdessen einen Querbalken.',
      hAsF: 'Das h hat oben eine Schleife und unten eine Unterlängen-Schleife, aber keinen Querstrich — der gehört zum f.',
      fAsH: 'Der Querstrich in der Mitte macht das f; das h hat keinen.',
      fAsT: 'Das f reicht nach oben und nach unten und trägt seinen Querstrich in der Mitte; das t hat keine Unterlänge.',
      tAsF: 'Das t hat keine Unterlänge — das f würde unter die Grundlinie reichen.',
      vAsW: 'Das v hat zwei Züge, das w drei.',
      wAsV: 'Drei Züge — das v hätte nur zwei.',
      szAsS: 'Das ß ist eine Ligatur aus langem ſ und z (ſʒ) — daher der Name Eszett.',
      umlautShown:
        'Über dem Buchstaben stehen die Umlautzeichen — aus dem klein übergeschriebenen e entstanden: ein {{letter}}.',
      umlautGuessed: 'Ohne die Umlautzeichen darüber ist es das einfache {{letter}}.',
      capitalCluster:
        '{{letters}} sind ein bekanntes Verwechslungs-Cluster der deutschen Schreibschrift — nebeneinander zeigt sich der Unterschied.',
    },
    // Advance affordances.
    autoNext: 'nächste Frage …',
    next: 'Weiter',
    cropAlt: 'Buchstabe in alter Schreibschrift',
    // Word-prompt compose fetch failed (after the cold-start retries) — the
    // plain-type fallback would hand the solution to the learner, so the card
    // offers a retry instead.
    renderError: 'Das Wort lässt sich gerade nicht schreiben — der Server ist nicht erreichbar.',
    renderRetry: 'Erneut versuchen',
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
