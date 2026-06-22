// Schriftkunde page (/schriftkunde) — a compact, fully-sourced primer on the
// German cursive scripts and the three Ausgangsschriften the project starts
// from. All facts are condensed from the project's Schriftkunde docs
// (docs/schriftkunde/*), where each claim carries its individual citation; the
// source links below point at the same freely-available primary references.
//
// Copyrighted modern works (Süß 2002) are named bibliographically and linked to
// their neutral library record (DNB) — never reproduced. See
// docs/reference/quellen-und-rechte.md.
//
// Key tree mirrors a future i18next `schriftkunde` namespace (pre-i18n catalog,
// see locales/index.ts). German prose only — code identifiers stay English.

// Shared source references, reused by the per-section citation lines and the
// consolidated Quellen list, so a link lives in exactly one place.
const SRC = {
  kurrent: { label: 'Wikipedia: Deutsche Kurrentschrift', href: 'https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift' },
  suetterlin: { label: 'Wikipedia: Sütterlinschrift', href: 'https://de.wikipedia.org/wiki/S%C3%BCtterlinschrift' },
  offenbacher: { label: 'Wikipedia: Offenbacher Schrift', href: 'https://de.wikipedia.org/wiki/Offenbacher_Schrift' },
  lineatur: { label: 'Wikipedia: Lineatur', href: 'https://de.wikipedia.org/wiki/Lineatur' },
  feder: { label: 'Wikipedia: Schreibfeder', href: 'https://de.wikipedia.org/wiki/Schreibfeder' },
  redis: { label: 'Wikipedia: Redisfeder', href: 'https://de.wikipedia.org/wiki/Redisfeder' },
  eisengallus: { label: 'Wikipedia: Eisengallustinte', href: 'https://de.wikipedia.org/wiki/Eisengallustinte' },
  langesS: { label: 'Wikipedia: Langes s', href: 'https://de.wikipedia.org/wiki/Langes_s' },
  ziffern: {
    label: 'Staatsbibliothek zu Berlin: Kurrent-Alphabetblatt (PDF)',
    href: 'https://etahoffmann.staatsbibliothek-berlin.de/wp-content/uploads/alphabet-kurrent.pdf',
  },
  pfennig: { label: 'Wikipedia: Pfennig (₰)', href: 'https://de.wikipedia.org/wiki/Pfennig' },
  nasalstrich: { label: 'Wikipedia: Nasalstrich', href: 'https://de.wikipedia.org/wiki/Nasalstrich' },
  rotunda: { label: 'Wikipedia: R rotunda', href: 'https://de.wikipedia.org/wiki/R_rotunda' },
  mark: { label: 'Wikipedia: Mark (1871)', href: 'https://de.wikipedia.org/wiki/Mark_(1871)' },
  schreibschrift: { label: 'Wikipedia: Schreibschrift', href: 'https://de.wikipedia.org/wiki/Schreibschrift' },
  ausgangsschrift: { label: 'Wikipedia: Ausgangsschrift', href: 'https://de.wikipedia.org/wiki/Ausgangsschrift' },
  hadernpapier: { label: 'Wikipedia: Hadernpapier', href: 'https://de.wikipedia.org/wiki/Hadernpapier' },
  schiefertafel: { label: 'Wikipedia: Schiefertafel', href: 'https://de.wikipedia.org/wiki/Schiefertafel' },
  erlass: { label: 'Wikipedia: Normalschrifterlass', href: 'https://de.wikipedia.org/wiki/Normalschrifterlass' },
  koch1928: {
    label: 'Rudolf Koch: Die Offenbacher Schrift (1928), Wikimedia Commons (gemeinfrei)',
    href: 'https://commons.wikimedia.org/wiki/File:Rudolf_Koch_Die_Offenbacher_Schrift_1928.pdf',
  },
  // Harald Süß, Deutsche Schreibschrift — the reference textbook. Linked to its
  // neutral, non-commercial DNB catalogue record (locatable in any library); no
  // material from it is reproduced (quellen-und-rechte.md §1).
  suess: { label: 'Harald Süß: Deutsche Schreibschrift (DNB-Katalog)', href: 'https://d-nb.info/969965451' },
} as const;

export const schriftkunde = {
  pageTitle: 'Schriftkunde — kurrentschrift.ink',

  eyebrow: 'Schriftkunde',
  title: 'Die deutsche Schreibschrift',
  lead: 'Vom frühen 16. bis zur Mitte des 20. Jahrhunderts war die Kurrent die allgemeine Verkehrs- und Geschäftsschrift des deutschen Sprachraums. Diese Schriftkunde gibt einen knappen, durchweg belegten Überblick über ihre Formen, ihr Werkzeug und ihre Geschichte — für die Tiefe führen die Quellen weiter. Das Projekt selbst beginnt bei drei Ausgangsschriften: Kurrent, Sütterlin und Offenbacher.',

  // --- Grundbegriffe ---------------------------------------------------------
  conceptsHeading: 'Grundbegriffe',
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
  conceptsSources: [SRC.lineatur, SRC.schreibschrift, SRC.feder],

  // --- Die drei Schriften ----------------------------------------------------
  variantsHeading: 'Die drei Schriften',
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

  // --- Federn & Striche ------------------------------------------------------
  federnHeading: 'Federn & Striche',
  federnLead: 'Jede der drei Schriften gehört zu ihrer Feder — das Werkzeug entscheidet, ob und wie der Strich an- und abschwillt.',
  federn: [
    {
      term: 'Spitzfeder',
      desc: 'Elastische Metallspitze. Die Strichstärke kommt aus dem Druck, nicht aus der Richtung: leichte Aufstriche bleiben dünn, kräftige Abstriche werden dick (Schwellzug). Sie prägt die Kurrent des 19. Jahrhunderts.',
    },
    {
      term: 'Gleichzugfeder',
      desc: 'Kugelspitzfeder (kugeliger Kopf) oder Redisfeder (runde Schreibplatte). Sie hält überall dieselbe Strichstärke — ganz ohne Druckwechsel. Drucklos und kindgerecht: die Feder der Sütterlin, die sich mit ihr in den 1920er Jahren durchsetzte.',
    },
    {
      term: 'Bandzugfeder',
      desc: 'Breite, flache Schreibkante (auch Breitfeder). Die Strichstärke wechselt mit der Richtung — am breitesten quer zur Kante, am feinsten längs. Bei der Offenbacher wird die Kante in 15–20° zur Grundlinie geführt.',
    },
  ],
  federnSources: [SRC.feder, SRC.redis],

  // --- Tinte & Papier --------------------------------------------------------
  materialHeading: 'Tinte & Papier',
  materialLead: 'Womit und worauf geschrieben wurde — und warum alte Schrift heute oft blass und braun aussieht.',
  material: [
    {
      term: 'Eisengallustinte',
      desc: 'Die wichtigste Tinte vom Mittelalter bis ins 20. Jahrhundert. Frisch geschrieben ist sie blass; das tiefe Schwarz bildet sich erst beim Trocknen an der Luft. Ein blauer Hilfsfarbstoff machte sie zunächst sichtbar („blauschwarz") und verblasst später — gealtert erscheint die Schrift braun.',
    },
    {
      term: 'Tintenfraß',
      desc: 'Aus dem Eisenvitriol der Tinte entsteht mit der Luftfeuchte Schwefelsäure. Sie zerfrisst das Papier genau dort, wo die Schrift steht, und schwächt den Kontrast.',
    },
    {
      term: 'Zwei Kanäle',
      desc: 'Weil ein verblasster Abstrich einst dick war, misst dieses Projekt Strichbreite (aus dem Federdruck) und Schwärze (die Tintenmenge) getrennt — sonst läse man einen ausgebleichten Schwellzug fälschlich als Haarlinie.',
    },
    {
      term: 'Papier & Tafel',
      desc: 'Geschrieben wurde auf reißfestem Hadernpapier, ab dem 19. Jahrhundert auf vergilbendem Holzschliffpapier. Das Schreiben gelernt wurde auf der Schiefertafel und im vierlinigen Schönschreibheft.',
    },
  ],
  materialSources: [SRC.eisengallus, SRC.hadernpapier, SRC.schiefertafel],

  // --- Buchstaben-Besonderheiten ---------------------------------------------
  lettersHeading: 'Buchstaben-Besonderheiten',
  lettersLead: 'Ein paar Eigenheiten, an denen die deutsche Schreibschrift zu erkennen ist — und über die jeder Leseanfänger stolpert.',
  letters: [
    {
      term: 'Langes ſ und rundes s',
      desc: 'Das lange ſ steht am Silbenanfang und im Silbeninneren, das runde s nur am Silbenende: leſen, aber das. Vom f unterscheidet es nur der fehlende Querstrich — eine häufige Lesefalle.',
    },
    {
      term: 'Der u-Bogen',
      desc: 'Klein-u und Klein-n sind formgleich. Damit man sie auseinanderhält, trägt das u einen kleinen Bogen über sich.',
    },
    {
      term: 'Das e und die Umlaute',
      desc: 'Das Kurrent-e hat eine eigene, an ein n erinnernde Form. Aus dem klein übergeschriebenen e sind die heutigen Pünktchen über ä, ö, ü entstanden.',
    },
    {
      term: 'Das ß',
      desc: 'Das Eszett ist historisch eine Ligatur aus langem ſ und z (ſʒ) — nicht aus ſ und s.',
    },
    {
      term: 'Reduplikationsstrich',
      desc: 'Ein gerader Strich über n oder m verdoppelt den Buchstaben: n̄ steht für nn.',
    },
  ],
  lettersSources: [SRC.kurrent, SRC.langesS],

  // --- Zahlen & Zeichen ------------------------------------------------------
  signsHeading: 'Zahlen & Zeichen',
  signsLead: 'Was in alten Dokumenten neben den Buchstaben steht.',
  signs: [
    {
      term: 'Ziffern',
      desc: 'Es gibt kein eigenes Kurrent-Ziffernsystem. Geschrieben wurden die gewöhnlichen arabischen Ziffern 0–9, in der geneigten Handschriftform der Zeit.',
    },
    {
      term: 'Geldzeichen',
      desc: 'Der Pfennig ist ein geschriebenes d mit Abschwung (₰, von lat. denarius), die Mark erscheint als „Mk" oder ℳ — die Kürzel alter Rechnungen.',
    },
    {
      term: 'Kürzungen',
      desc: 'Ein waagrechter Strich über einem Buchstaben (Nasalstrich) ergänzt oder verdoppelt ein m oder n; „ꝛc." stand für „etc.". Solche Kürzungen waren in Handschriften gebräuchlich.',
    },
  ],
  signsSources: [SRC.ziffern, SRC.pfennig, SRC.mark, SRC.nasalstrich, SRC.rotunda],

  // --- Chronologie -----------------------------------------------------------
  timelineHeading: 'Chronologie',
  timeline: [
    { year: '13.–16. Jh.', text: 'Aus der gotischen Kursive entsteht über die Kanzleibastarda die deutsche Kurrent.' },
    { year: '1714', text: 'Preußen führt mit den Vorlagen von Hilmar Curas die erste Normschrift für den Schreibunterricht ein.' },
    { year: '19. Jh.', text: 'Die metallene Spitzfeder lässt die Kurrent stärker nach rechts neigen — die Schulvorschriften streuen weit, von 45° bis 75°.' },
    { year: 'um 1900', text: 'Die klassische Kurrent steht auf der Lineatur 2:1:2 und einer Schräglage von 60–70°.' },
    { year: '1911', text: 'Ludwig Sütterlin entwirft im preußischen Auftrag seine bewusst aufrechte Ausgangsschrift.' },
    { year: '1915 / 1918', text: 'Einführung in Preußen — erst probeweise, dann verbindlich.' },
    { year: '1927', text: 'Rudolf Koch entwirft die Offenbacher Schrift als künstlerischen Gegenentwurf.' },
    { year: '1935', text: 'Eine modifizierte Sütterlin wird als „Deutsche Volksschrift" Bestandteil des Schulunterrichts.' },
    { year: '1941', text: 'Lehrverbot der Kurrentschriften zum 1. September; ab 1941/42 gilt die lateinische „Deutsche Normalschrift".' },
    { year: 'nach 1945', text: 'Vereinzelt als Zweitschrift wiederbelebt (etwa Koch-Hermersdorf in Bayern), ohne dauerhaften Erfolg.' },
  ],
  timelineNote:
    'Im deutschen Sprachraum verlief das Ende verschieden: Österreich lehrte bis 1938/39 die traditionelle Kurrent (nicht die Sütterlin), die Schweiz gab sie schon um 1900 kantonsweise auf.',
  timelineSources: [SRC.kurrent, SRC.suetterlin, SRC.offenbacher, SRC.ausgangsschrift, SRC.erlass],

  // --- Quellen ---------------------------------------------------------------
  sourcesHeading: 'Quellen',
  sourcesIntro:
    'Jede Angabe auf dieser Seite ist belegt. Die ausführlichen Faktenblätter mit Einzelnachweisen liegen in der Schriftkunde des Projekts; die Links unten führen zu denselben frei zugänglichen Primärquellen.',
  sources: [SRC.kurrent, SRC.suetterlin, SRC.offenbacher, SRC.lineatur, SRC.feder, SRC.eisengallus, SRC.langesS, SRC.erlass, SRC.koch1928],
  sourcesRepo:
    'Gemeinfreie Geometrie-Vorlagen im Projekt: Loth-Tafel 1866 (Kurrent) und Sütterlin-Ausgangsschrift 1922.',

  // --- Weiterlernen (Empfehlung) ---------------------------------------------
  recommendation: {
    heading: 'Weiterlernen',
    before: 'Wer die deutsche Schreibschrift nicht nur betrachten, sondern wirklich lesen und schreiben lernen möchte, dem sei ',
    linkLabel: 'Harald Süß’ „Deutsche Schreibschrift. Lesen und Schreiben lernen"',
    href: SRC.suess.href,
    after: ' ans Herz gelegt — das Lehrbuch, aus dem auch der Autor dieses Projekts die Kurrent gelernt hat. Hier geht es bewusst nur um den Überblick; die Tiefe steht dort.',
  },

  sourcesLabel: 'Quellen:',
} as const;
