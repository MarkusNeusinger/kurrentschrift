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
  // Section 1: the scripts. "Kurrent(schrift)" is really an umbrella over a
  // whole family of German cursive hands; these three make good starters
  // because each is written with a *different* pen. Honest about which can be
  // written by the engine yet (Sütterlin only) — `state` drives a small badge.
  scriptsHeading: 'Drei Schriften, drei Federn',
  scriptsIntro:
    '„Kurrentschrift" fasst eine ganze Familie deutscher Schreibschriften zusammen. Drei davon zum Anfangen — jede mit ihrer eigenen Feder, und keine als Font, sondern Zug um Zug nachgebildet.',
  scripts: [
    {
      name: 'Kurrent',
      feder: 'Spitzfeder',
      state: 'noch zum Lesen',
      written: false,
      desc: 'Die ältere Norm. Aus dem Druck der Spitzfeder wächst der Schwellzug — fein im Aufstrich, breit im Abstrich.',
    },
    {
      name: 'Sütterlin',
      feder: 'Gleichzugfeder',
      state: 'schon schreibbar',
      written: true,
      desc: 'Aufrecht und gleichmäßig, ohne Schwellung — die Schulschrift von 1911. Sie wird hier schon lebendig geschrieben.',
    },
    {
      name: 'Offenbacher',
      feder: 'Breitfeder',
      state: 'noch zum Lesen',
      written: false,
      desc: 'Der Strichkontrast kommt aus dem Winkel der Breitfeder, nicht aus dem Druck. Nie weit verbreitet — aber ein schöner Einstieg.',
    },
  ],
  // Section 2: what already works today (the component attaches the route paths).
  toolsHeading: 'Schon zur Hand',
  toolsIntro: 'Vom Nachschlagen und Lesen bis zum ersten eigenen Federstrich — was heute schon bereitsteht.',
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
    schriftkunde: {
      title: 'Schriftkunde',
      cta: 'Zur Schriftkunde →',
      desc: 'Die drei Schriften im Überblick — Lineatur, Federn, Tinte und ihre Geschichte, quellengestützt.',
    },
    tafel: {
      title: 'Schreibtafel',
      cta: 'Zur Tafel →',
      desc: 'Die ganze Vorlage auf einen Blick — jeder Buchstabe, wie ihn die Feder schreibt.',
    },
  },
  // Section 3: an honest word on the state + a short list of genuinely-future
  // features. Deliberately NO items that already exist (the Schriftkunde primer,
  // the quiz) — those live under "Schon zur Hand". Badge: common.soon.
  roadmapHeading: 'Noch im Werden',
  roadmapNote:
    'Ein junges Werk: Das Schreiben-Lassen kann bisher nur Sütterlin — und noch nicht fehlerfrei. Vieles, was kommen soll, ist erst Plan:',
  roadmap: [
    { title: 'Mehr Hände schreiben', desc: 'Auch Kurrent und Offenbacher Zug um Zug geschrieben, nicht nur gelesen — und sauberer als heute.' },
    { title: 'Animierte Tafel', desc: 'Strichfolge, Ansatzpunkte und Schwellzug — der Feder bei der Arbeit zugesehen.' },
    { title: 'Lese-Lupe', desc: 'Alte Scans, Zeile um Zeile übertragen — mit einer Erläuterung zu jedem Buchstaben.' },
    { title: 'Schrift-Analyse', desc: 'Die eigene Hand in Zahlen — Schräglage, Schwellzug und Verteilung.' },
    { title: 'Offene Daten', desc: 'Die Glyph-Daten — Anker, Schwellzug, Duktus — offen und frei zu zitieren.' },
  ],
  footer: {
    scripts: 'Kurrent · Sütterlin · Offenbacher',
    disclaimer: 'Eine private Liebhaberei — offen und frei.',
  },
} as const;
