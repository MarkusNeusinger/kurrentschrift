// Lehrbuch page (/lehrbuch) — a compact, fully-sourced primer on the German
// cursive scripts and the three Ausgangsschriften the project starts from.
// All facts are condensed from the project's Schriftkunde docs
// (docs/schriftkunde/*), where each claim carries its individual citation; the
// source links below point at the same freely-available primary references.
//
// Key tree mirrors a future i18next `lehrbuch` namespace (pre-i18n catalog, see
// locales/index.ts). German prose only — code identifiers stay English.

// Shared source references, reused by the per-section citation lines and the
// consolidated Quellen list, so a link lives in exactly one place.
const SRC = {
  kurrent: { label: 'Wikipedia: Deutsche Kurrentschrift', href: 'https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift' },
  suetterlin: { label: 'Wikipedia: Sütterlinschrift', href: 'https://de.wikipedia.org/wiki/S%C3%BCtterlinschrift' },
  offenbacher: { label: 'Wikipedia: Offenbacher Schrift', href: 'https://de.wikipedia.org/wiki/Offenbacher_Schrift' },
  lineatur: { label: 'Wikipedia: Lineatur', href: 'https://de.wikipedia.org/wiki/Lineatur' },
  feder: { label: 'Wikipedia: Schreibfeder', href: 'https://de.wikipedia.org/wiki/Schreibfeder' },
  erlass: { label: 'Wikipedia: Normalschrifterlass', href: 'https://de.wikipedia.org/wiki/Normalschrifterlass' },
  koch1928: {
    label: 'Rudolf Koch: Die Offenbacher Schrift (1928), Wikimedia Commons (gemeinfrei)',
    href: 'https://commons.wikimedia.org/wiki/File:Rudolf_Koch_Die_Offenbacher_Schrift_1928.pdf',
  },
} as const;

export const lehrbuch = {
  pageTitle: 'Lehrbuch — kurrentschrift.ink',

  eyebrow: 'Lehrbuch',
  title: 'Die deutsche Schreibschrift',
  lead: 'Vom frühen 16. bis zur Mitte des 20. Jahrhunderts war die Kurrent die allgemeine Verkehrs- und Geschäftsschrift des deutschen Sprachraums. Dieses Projekt beginnt bei drei Ausgangsschriften — Kurrent, Sütterlin und Offenbacher.',

  // --- Grundbegriffe ---------------------------------------------------------
  conceptsHeading: 'Drei Grundbegriffe',
  concepts: [
    {
      term: 'Lineatur',
      desc: 'Vier Linien — Oberlinie · Mittellinie · Grundlinie · Unterlinie — bilden drei Zonen: Oberlänge · Mittellänge · Unterlänge. Die Verhältnisse sind in DIN 16552-1 genormt.',
    },
    {
      term: 'Schräglage',
      desc: 'Der Neigungswinkel wird zur Grundlinie gemessen: 90° heißt senkrecht, kleinere Werte heißen stärker nach rechts geneigt.',
    },
    {
      term: 'Schwellzug & Gleichzug',
      desc: 'Die elastische Spitzfeder schwillt unter Druck an — dünne Aufstriche, dicke Abstriche (Schwellzug). Die Gleichzugfeder hält überall dieselbe Strichstärke (Gleichzug).',
    },
  ],
  conceptsSources: [SRC.lineatur, SRC.feder],

  // --- Die drei Varianten ----------------------------------------------------
  variantsHeading: 'Die drei Varianten',
  variants: [
    {
      id: 'kurrent',
      name: 'Kurrent',
      period: 'frühes 16. Jh. – 1941',
      essence:
        'Über Jahrhunderte die allgemeine Gebrauchsschrift — ohne einheitlichen Duktus, sondern mit regional und zeitlich verschiedenen Schulvorschriften.',
      facts: [
        { k: 'Schräglage', v: '~45–75°; um 1900: 60–70°' },
        { k: 'Lineatur', v: '2:1:2 (große Ober-/Unterlängen)' },
        { k: 'Feder', v: 'ab dem 19. Jh. Spitzfeder' },
        { k: 'Strich', v: 'Schwellzug (druckabhängig)' },
      ],
      note: 'Der Wert 60–70° um 1900 nach Süß (2002).',
      sources: [SRC.kurrent],
    },
    {
      id: 'suetterlin',
      name: 'Sütterlin',
      period: 'entworfen 1911 · Schulschrift ~1915–1941',
      essence:
        'Ludwig Sütterlins bewusst aufrechte, vereinfachte Ausgangsschrift für den Schreibunterricht. Heute heißt umgangssprachlich fast jede Kurrent „Sütterlin" — gemeint ist aber nur diese eine, späte Variante.',
      facts: [
        { k: 'Schriftlage', v: 'senkrecht (90°)' },
        { k: 'Lineatur', v: '1:1:1' },
        { k: 'Feder', v: 'Gleichzugfeder (Kugelspitz-/Redisfeder)' },
        { k: 'Strich', v: 'Gleichzug (kein Druckwechsel)' },
      ],
      sources: [SRC.suetterlin],
    },
    {
      id: 'offenbacher',
      name: 'Offenbacher',
      period: 'entworfen 1927 von Rudolf Koch',
      essence:
        'Ein künstlerischer Gegenentwurf zur pädagogisch gedachten Sütterlin. Als allgemeine Schulschrift setzte sie sich nicht durch.',
      facts: [
        { k: 'Schräglage', v: '75–80°' },
        { k: 'Lineatur', v: '2:3:2 (auch 3:4:3), mittenbetont' },
        { k: 'Feder', v: 'Band-/Breitfeder, Kante 15–20°' },
        { k: 'Strich', v: 'richtungsabhängiger Bandzug' },
      ],
      sources: [SRC.offenbacher, SRC.koch1928],
    },
  ],

  // Specimen captions, keyed by variant id (rendered next to the visual).
  specimen: {
    kurrentCaption: 'Schauschrift-Font (GL German Cursive)',
    suetterlinCaption: 'live geschrieben aus der gemeinfreien Vorlage von 1922 — die Synthese-Engine des Projekts',
    // Shown when the engine can't render (cold/unreachable API) and the card
    // falls back to the show-script font — kept truthful about what's on screen.
    suetterlinCaptionFallback: 'Vorschau im Schauschrift-Font — die Synthese-Engine ist gerade nicht erreichbar',
    suetterlinWord: 'leſen',
    offenbacherPending:
      'Noch keine Vorlage im Repository. Gemeinfreie Primärquelle: Rudolf Koch, „Die Offenbacher Schrift" (1928).',
  },

  // --- Kurz-Chronologie ------------------------------------------------------
  timelineHeading: 'Kurz-Chronologie',
  timeline: [
    { year: '16. Jh.', text: 'Die Kurrent entsteht aus der Kanzleibastarda.' },
    { year: '1911', text: 'Ludwig Sütterlin entwirft seine Ausgangsschrift.' },
    { year: '1927', text: 'Rudolf Koch entwirft die Offenbacher Schrift.' },
    { year: '1941', text: 'Schul-Lehrverbot der Kurrentschriften (ab 1. September).' },
  ],
  timelineSources: [SRC.kurrent, SRC.erlass],

  // --- Quellen ---------------------------------------------------------------
  sourcesHeading: 'Quellen',
  sourcesIntro:
    'Jede Angabe auf dieser Seite ist belegt. Die ausführlichen Faktenblätter mit Einzelnachweisen liegen in der Schriftkunde des Projekts.',
  sources: [SRC.kurrent, SRC.suetterlin, SRC.offenbacher, SRC.lineatur, SRC.feder, SRC.erlass, SRC.koch1928],
  sourcesBiblio:
    'Harald Süß: Deutsche Schreibschrift. Lesen und Schreiben lernen. Augsburg 2002 — bibliographisch, kein Material im Repository.',
  sourcesRepo:
    'Gemeinfreie Geometrie-Vorlagen im Projekt: Loth-Tafel 1866 (Kurrent) und Sütterlin-Ausgangsschrift 1922.',

  sourcesLabel: 'Quellen:',
} as const;
