// German strings for the public Lesart page (/lesen/vergleichen,
// sections/vergleichen/*): a person with an old letter on the desk types what
// they believe a word says, the engine writes it in Sütterlin, and beside it
// the readings that would look the same on the page (lib/lesarten.ts). Plus
// the classic confusable pairs written side by side. Pre-i18n message catalog
// — key tree mirrors a future i18next `vergleichen` namespace.
//
// Facts in the pair sentences come from the Schriftkunde
// (locales/de/schriftkunde.ts „Buchstaben-Besonderheiten") and
// docs/schriftkunde/orthographie-regeln.md §1/§3; no new historical claims.

export const vergleichen = {
  // `title` is the short name (nav, hub card, breadcrumb); `heading` the H1
  // with the search term (locales/de/seo.ts rule).
  title: 'Lesart prüfen',
  heading: 'Lesart prüfen: Was steht da wirklich?',
  lead: 'Du hast ein Wort in einem alten Brief, einer Urkunde oder einem Kirchenbuch vor dir und eine Vermutung, was es heißt. Tippe sie ein: Die Feder schreibt sie in Sütterlin — und daneben die Lesarten, die in dieser Schrift genauso aussehen könnten, weil sich n und u, e und n, f und ſ zum Verwechseln ähneln. Dann vergleiche mit deinem Original.',

  // --- Deine Lesart ---------------------------------------------------------
  guessHeading: 'Deine Lesart',
  inputLabel: 'Deine Vermutung',
  inputPlaceholder: 'Muhme',
  examplesLabel: 'Beispiele:',
  // Words a genealogist meets — all letters traced in the public source.
  examples: ['Muhme', 'Wittib', 'Taufe', 'Häusler'],
  writtenCaption: 'So schreibt es die Sütterlin-Vorlage von 1922 — vergleiche mit deinem Original.',
  // Some letters have no canonical yet (interpolates {{letters}}).
  missingNote: 'Diese Buchstaben sind noch nicht nachgeschrieben und bleiben darum frei: {{letters}}',
  emptyHint: 'Tippe oben, was du zu lesen glaubst.',
  loadError: 'Der Schreibdienst ist gerade nicht erreichbar — die Feder muss kurz pausieren.',
  retry: 'Erneut versuchen',

  // --- Lesarten -------------------------------------------------------------
  // Real words only (owner decision 2026-08-30): the API answers with the
  // dictionary words that differ from the guess by look-alike letters alone.
  lesartenHeading: 'Wörter, die genauso aussehen könnten',
  lesartenIntro: 'Echte Wörter, die sich von deiner Lesart nur in Verwechslern unterscheiden — n und u, e und n, f und ſ, die Umlautzeichen. Welches passt zu deinem Original? Ein Klick macht es zur neuen Lesart.',
  // Caption under a reading card (interpolates the swapped letters).
  swapNote: '{{to}} statt {{from}}',
  takeOver: 'als Lesart übernehmen',
  // A reading from the project's own curated bank (quiz words) — the historic layer the dictionary lacks.
  bankMark: 'aus der Wortbank',
  lesartenLoading: 'Wörter werden gesucht …',
  lesartenError: 'Die Wörter lassen sich gerade nicht abfragen — der Server ist nicht erreichbar.',
  noLesarten: 'Kein Wort im Wörterbuch sieht dieser Lesart zum Verwechseln ähnlich — sie ist wohl eindeutig.',
  // Where the words come from (interpolates {{forms}}, the live vocabulary's size).
  dictionaryNote: 'Wortformen aus dem freien deutschen Wörterbuch igerman98 ({{forms}} Formen) und der Wortbank dieser Seite; Namen und alte Wörter, die beide nicht kennen, fehlen hier.',
  dictionaryMissing: 'Das Wörterbuch ist noch nicht geladen — es kommen nur Wörter der eigenen Wortbank.',

  // --- Die klassischen Verwechsler ------------------------------------------
  pairsHeading: 'Die klassischen Verwechsler',
  pairsIntro: 'Die Paare, an denen das Entziffern am häufigsten hängt — nebeneinander geschrieben, mit dem Merkmal, das sie unterscheidet.',
  pairsNote: 'Die Buchstaben schreibt die Engine live aus der Sütterlin-Vorlage von 1922; der Antiqua-Buchstabe darunter benennt jede Form, ein Klick schreibt sie noch einmal.',
  // `specimens`: glyph_keys of the public source + Antiqua labels (SpecimenStrip).
  pairs: [
    {
      term: 'ſ und f',
      specimens: [
        { key: 'longs', label: 'ſ' },
        { key: 'f', label: 'f' },
      ],
      desc: 'Das f trägt oben eine Schleife und in der Mitte den Querstrich; das lange ſ läuft oben spitz zu und hat beides nicht. Das ſ steht am Silbenanfang und im Silbeninneren, das runde s nur am Silbenende.',
    },
    {
      term: 'n und u',
      specimens: [
        { key: 'n', label: 'n' },
        { key: 'u', label: 'u' },
      ],
      desc: 'n und u sind formgleich — das u trägt zur Unterscheidung einen kleinen Bogen über sich. Fehlt er, ist es ein n.',
    },
    {
      term: 'e und n',
      specimens: [
        { key: 'e', label: 'e' },
        { key: 'n', label: 'n' },
      ],
      desc: 'Das e erinnert an ein n, steht aber enger: zwei schmale Züge, wo das n zwei gleich weite Bögen hat.',
    },
    {
      term: 's und ſ',
      specimens: [
        { key: 's', label: 's' },
        { key: 'longs', label: 'ſ' },
      ],
      desc: 'Das runde s steht nur am Silben- und Wortende (das), im Wortinneren schreibt man das lange ſ (leſen) — ein rundes s mitten im Wort zeigt meist eine Silbengrenze an.',
    },
    {
      term: 't und l',
      specimens: [
        { key: 't', label: 't' },
        { key: 'l', label: 'l' },
      ],
      desc: 'Das t hat einen Querbalken und keine Schleife; das l steigt mit einer Schleife auf.',
    },
    {
      term: 'h und f',
      specimens: [
        { key: 'h', label: 'h' },
        { key: 'f', label: 'f' },
      ],
      desc: 'Das h hat oben eine Schleife und unten eine Unterlängen-Schleife, aber keinen Querstrich — der gehört zum f.',
    },
    {
      term: 'm und n',
      specimens: [
        { key: 'm', label: 'm' },
        { key: 'n', label: 'n' },
      ],
      desc: 'Das m hat drei Züge, das n zwei — in flüchtiger Schrift hilft nur Zählen.',
    },
  ],

  // --- Weiter ---------------------------------------------------------------
  moreHeading: 'Weiter',
  moreDecipher: 'Einen alten Brief entziffern — die Schritte in der Schriftkunde',
  moreQuiz: 'Lesen üben im Lese-Quiz',
  // Honest provenance note, mirroring the Federprobe's.
  disclaimer: 'Synthese, klar gekennzeichnet — nachgebildete Schrift aus der Sütterlin-Ausgangsschrift 1922, kein historisches Original. Briefe des 19. Jahrhunderts stehen in der stärker geneigten Kurrent mit Schwellzug; die Buchstabenformen und ihre Verwechsler sind dieselben.',
} as const;
