// German strings for the public landing page (sections/landing/*).
// Pre-i18n message catalog — key tree mirrors a future i18next `landing`
// namespace. Long prose (pillars, tools, roadmap) lives here as data; the
// component keeps only the layout logic.

export const landing = {
  hero: {
    // The brand word the hero writes live with the pen. Engine-first: the
    // synthesis engine writes it stroke by stroke (WrittenWord); on a cold or
    // incomplete backend the GL-GermanCursive show-font wipes in instead (a
    // marked specimen, per the legibility rule). `wordCaption` belongs to the
    // fallback, `wordCaptionEngine` to the live engine — the caption switches
    // with the mode so the page never claims a live synthesis over a static
    // font. `wordAria` is the plain-text label for screen readers/title attr.
    // Long-s (ſ) at the syllable start of "-ſchrift" per the Kurrent rule.
    word: 'Kurrentſchrift',
    wordAria: 'Kurrentschrift',
    wordCaption: '— ein deutsches Wort im Schriftbild von vor hundert Jahren.',
    wordCaptionEngine:
      '— eben live geschrieben von der Synthese-Engine: heute in Sütterlin, laufend verfeinert — Kurrent und Offenbacher folgen.',
    title: 'Alte Briefe wieder lesen — und selbst zur Feder greifen.',
    // The lead answers „was" and — since the website audit 2026-09-02 (owner
    // decision 2026-09-03) — „für wen": the Kirchenbucheintrag and the named
    // Familienforschung are what the core audience arrives with. Tone stays a
    // preface around 1900, so the reasons are an aside between dashes, not a
    // target-group pitch.
    leadBeforeBold:
      'Kurrent, Sütterlin und Offenbacher: die Schriften, in denen unsere Vorfahren ihre Briefe, Kirchenbucheinträge und Urkunden niederschrieben — und die heute',
    leadBold: 'kaum noch jemand entziffert',
    leadAfterBold:
      '. Hier lernst du — ob für die Familienforschung, im Archiv oder aus Neugier —, sie wieder zu lesen, mit der Feder nachzuschreiben und Zug um Zug zu verstehen.',
    ctaWrite: 'Schreiben',
    ctaRead: 'Lesen',
    replay: '↻ noch einmal schreiben',
    // Shown after ~3 s while a cold backend still composes the word — the
    // hero waits for the WRITTEN word instead of swapping in a static font
    // (owner decision 2026-08-27).
    waiting: 'die Feder setzt an — einen Moment …',
  },
  // Section 0: the way through the site, in the order the top nav names the
  // three areas (Schriftkunde · Lesen · Schreiben). The landing answered „was"
  // in ten seconds but never „wie fange ich an" — five tool cards of equal
  // rank and no path through them (website audit 2026-09-02, owner decision
  // 2026-09-03). One sentence and one link per step; the steps point at the
  // ENTRY of each area, not at every tool it holds — the cards below still do
  // the full inventory.
  howHeading: 'So geht es',
  howSteps: {
    nachschlagen: {
      title: 'Nachschlagen',
      desc: 'Die Schriftkunde sagt dir, welche Schrift vor dir liegt; die Schreibtafel zeigt jeden Buchstaben — zum Danebenlegen, auch als PDF.',
      cta: 'Zur Schriftkunde →',
    },
    lesen: {
      title: 'Lesen',
      desc: 'Das Lese-Quiz übt die Formen, an denen jeder stolpert; die Lesart-Prüfung hilft bei dem einen Wort, das sich nicht entziffern lassen will.',
      cta: 'Zu den Lese-Übungen →',
    },
    schreiben: {
      title: 'Schreiben',
      desc: 'Das Übungsblatt bringt die Lineatur aufs Papier, die Federprobe schreibt dir jeden Zug vor.',
      cta: 'Zu den Schreib-Übungen →',
    },
  },
  // Section 1: the scripts. "Kurrent(schrift)" is really an umbrella over a
  // whole family of German cursive hands; these three make good starters
  // because each is written with a *different* pen. Each card LINKS to its own
  // Grundtafel (paths.tafel#<styleId>) like the tool cards do; the honest state
  // rides the link text (`cta`) AND an explicit `status` line on the card:
  // Sütterlin is already written by the engine and being optimised (viridian,
  // `written`), Kurrent/Offenbacher are not started — only the historical
  // Vorlage to look at (muted) — neither is in the quiz yet, so no "lesen" claim.
  scriptsHeading: 'Drei Schriften, drei Federn',
  scriptsIntro:
    '„Kurrentschrift“ fasst eine ganze Familie deutscher Schreibschriften zusammen. Drei davon zum Anfangen — jede mit ihrer eigenen Feder. Das Ziel: keine als Font, sondern Zug um Zug nachgebildet — die Sütterlin schreibt hier schon und wird laufend verfeinert; Kurrent und Offenbacher sind noch nicht begonnen.',
  scripts: [
    {
      name: 'Kurrent',
      styleId: 'kurrent',
      feder: 'Spitzfeder',
      cta: 'Historische Vorlage ansehen →',
      status: 'noch nicht begonnen',
      written: false,
      desc: 'Die alte Alltagsschrift, ohne einheitliche Norm. Aus dem Druck der Spitzfeder wächst der Schwellzug — fein im Aufstrich, breit im Abstrich.',
    },
    {
      name: 'Sütterlin',
      styleId: 'suetterlin',
      feder: 'Gleichzugfeder',
      cta: 'Schon geschrieben — ansehen →',
      status: 'in aktiver Optimierung',
      written: true,
      desc: 'Aufrecht und gleichmäßig, ohne Schwellung — 1911 entworfen, ab 1915 Schulschrift. Sie wird hier schon lebendig geschrieben.',
    },
    {
      name: 'Offenbacher',
      styleId: 'offenbacher',
      feder: 'Breitfeder',
      cta: 'Historische Vorlage ansehen →',
      status: 'noch nicht begonnen',
      written: false,
      desc: 'Der Strichkontrast kommt aus dem Winkel der Breitfeder, nicht aus dem Druck. Nie weit verbreitet — aber ein schöner Einstieg in die Breitfeder-Kalligrafie.',
    },
  ],
  // Section 2: what already works today (the component attaches the route paths).
  toolsHeading: 'Schon zur Hand',
  toolsIntro: 'Vom Nachschlagen und Lesen bis zum ersten eigenen Federstrich — was heute schon bereitsteht.',
  tools: {
    worksheet: {
      title: 'Übungsblatt',
      cta: 'Übungsblatt erstellen →',
      desc: 'Hilfslinien für die deutsche Schreibschrift auf einem Bogen A4 — das Verhältnis frei gewählt, auf Wunsch mit Schräglinien und deinem Text als Vorschrift in Sütterlin, druckfertig als PDF.',
    },
    scribe: {
      title: 'Federprobe',
      cta: 'Wort schreiben lassen →',
      desc: 'Ein Wort oder einen kurzen Satz eingeben — und zusehen, wie die Feder es Zug um Zug in Sütterlin schreibt, samt den Übergängen von Buchstabe zu Buchstabe.',
    },
    quiz: {
      title: 'Lese-Quiz',
      cta: 'Quiz starten →',
      desc: 'Echte Buchstaben und ganze Wörter der alten Schreibschrift lesen; am Ende zeigt die Auswertung, was Mühe bereitete.',
    },
    schriftkunde: {
      title: 'Schriftkunde',
      cta: 'Zur Schriftkunde →',
      desc: 'Die drei Schriften im Überblick — Lineatur, Federn, Tinte und ihre Geschichte, quellengestützt.',
    },
    tafel: {
      title: 'Schreibtafel',
      cta: 'Zur Tafel →',
      desc: 'Die drei historischen Vorlagen auf einen Blick — die Sütterlin schreibt sich Zug um Zug selbst.',
    },
  },
  // Section 3: an honest word on the state + a short list of genuinely-future
  // features. Deliberately NO items that already exist (the Schriftkunde primer,
  // the quiz) — those live under "Schon zur Hand". Badge: common.soon.
  roadmapHeading: 'Noch im Werden',
  roadmapNote:
    'Ein junges Werk: Das Schreiben-Lassen kann bisher nur Sütterlin — sie steht in laufender Optimierung und schreibt noch nicht fehlerfrei. Kurrent und Offenbacher sind noch nicht begonnen. Vieles, was kommen soll, ist erst Plan:',
  roadmap: [
    { title: 'Mehr Hände schreiben', desc: 'Auch Kurrent und Offenbacher Zug um Zug geschrieben, nicht nur gelesen — und sauberer als heute.' },
    { title: 'Animierte Tafel', desc: 'Strichfolge, Ansatzpunkte und Schwellzug — der Feder bei der Arbeit zugesehen.' },
    { title: 'Lese-Lupe', desc: 'Alte Scans, Zeile um Zeile übertragen — mit einer Erläuterung zu jedem Buchstaben.' },
    { title: 'Schrift-Analyse', desc: 'Die eigene Hand in Zahlen — Schräglage, Schwellzug und Verteilung.' },
  ],
} as const;
