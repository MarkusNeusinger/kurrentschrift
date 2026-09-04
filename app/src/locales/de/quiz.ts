// German strings for the public reading drill (sections/quiz/*). Pre-i18n
// message catalog — key tree mirrors a future i18next `quiz` namespace.

export const quiz = {
  // `title` is the short name (nav, cards, breadcrumbs); `heading` the page's
  // H1 with the search term in it (SEO audit 2026-08-29, locales/de/seo.ts).
  title: 'Lese-Quiz',
  heading: 'Sütterlin lesen üben: das Lese-Quiz',
  // The explanatory paragraph under the H1 (SPA: over the setup; prerender:
  // over the option list). It says what a round looks like, what is explained
  // after a miss — the DOCUMENTED look-alikes, never „jeden Fehlgriff“
  // (lesefallen.ts) — and which script is drilled today, so neither a person
  // nor a crawler is promised a Kurrent quiz (website audit 2026-09-02).
  about:
    'Das Quiz zeigt dir einen Buchstaben oder ein ganzes Wort, wie es die Feder nach der Sütterlin-Ausgangsschrift von 1922 schreibt, und fragt: Welcher ist das? Vier Antworten stehen zur Wahl, darunter meist der Verwechsler, mit dem Leseanfänger die Form am häufigsten vertauschen — n und u, e und n, das lange ſ und das f. Liegst du daneben, stehen beide Formen nebeneinander; bei den klassischen Verwechslern kommt das Merkmal dazu, das sie trennt: der Bogen über dem u, die Schleife und der Querstrich des f. Bei den Wörtern kommen neben Alltagswörtern die Vokabeln alter Briefe an die Reihe — Muhme, Wittib, ergebenst — mit kurzer Erklärung. Am Ende zeigt die Auswertung, welche Formen Mühe machten. Geübt wird bislang nur die Sütterlin; Kurrent und Offenbacher folgen, sobald ihre Vorlagen nachgeschrieben sind.',
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
    // Counts no "Handgriffe": the setup shows only the rows that offer a choice
    // (today one), so the copy must not promise a number.
    introLead: 'Such dir aus, was du heute üben magst —',
    introRest: ' dann geht’s los.',
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
    // Summary line above the start button, followed by the labels of the rows
    // actually on screen (QuizSetupPanel shows a row only when it offers a
    // choice) — today "dein Quiz · Buchstaben"; the script is named by
    // `sourceNote` below.
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
        'Das lange ſ läuft oben spitz zu und hat keinen Querstrich — das f trägt oben eine Schleife und in der Mitte den Querstrich. Das ſ steht am Silbenanfang und im Silbeninneren, das runde s nur am Silbenende.',
      fAsLongs: 'Die Schleife oben und der Querstrich in der Mitte machen das f — das lange ſ läuft spitz zu und hat beides nicht.',
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
      // The two halves of one owner-approved sentence (2026-09-04), each
      // direction leading with the form on the card.
      gAsP: 'Das g schließt unten eine runde Schleife — das p geht mit geradem Abstrich unter die Zeile und trägt seinen Bogen rechts oben.',
      pAsG: 'Das p geht mit geradem Abstrich unter die Zeile und trägt seinen Bogen rechts oben — das g schließt unten eine runde Schleife.',
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
    // Under the two result blocks: every letter card leads to that letter on
    // the Schreibtafel (/tafel?g=<key>), where it writes itself stroke by
    // stroke — the way on after a misread.
    tafelHint: 'Eine Form antippen: die Schreibtafel schreibt sie Zug um Zug vor.',
    // Aria label of such a card (interpolates the letter's name).
    tafelLinkAria: '{{form}} auf der Schreibtafel ansehen',
    replay: 'Weiter üben',
    settings: 'Einstellungen ändern',
  },
} as const;
