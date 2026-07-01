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
  englischeSchreibschrift: { label: 'Wikipedia: Englische Schreibschrift', href: 'https://de.wikipedia.org/wiki/Englische_Schreibschrift' },
  lateinischeAusgangsschrift: { label: 'Wikipedia: Lateinische Ausgangsschrift', href: 'https://de.wikipedia.org/wiki/Lateinische_Ausgangsschrift' },
  fraktur: { label: 'Wikipedia: Fraktur', href: 'https://de.wikipedia.org/wiki/Fraktur_(Schrift)' },
  antiquaFraktur: { label: 'Wikipedia: Antiqua-Fraktur-Streit', href: 'https://de.wikipedia.org/wiki/Antiqua-Fraktur-Streit' },
  liechtenstein: { label: 'Historisches Lexikon Liechtenstein: Schrift', href: 'https://historisches-lexikon.li/Schrift' },
  // Scholarly / archive / museum references (the authoritative base behind the
  // facts; Wikipedia above is the convenient overview pointer).
  adfontesKursive: {
    label: 'ad fontes (Univ. Zürich): Bastarda und gotische Kursive',
    href: 'https://www.adfontes.uzh.ch/tutorium/schriften-lesen/schriftgeschichte/bastarda-und-gotische-kursive',
  },
  adfontesKurrent: {
    label: 'ad fontes (Univ. Zürich): Deutsche Kurrentschrift',
    href: 'https://www.adfontes.uzh.ch/tutorium/schriften-lesen/schriftgeschichte/deutsche-kurrentschrift',
  },
  ottweiler: {
    label: 'Schulmuseum Ottweiler: Vorschriften & Musterbücher',
    href: 'https://schulmuseum-ottweiler.net/magazin/buchstabentabellen-vorschriften-und-musterbuecher',
  },
  zbZuerich: {
    label: 'Zentralbibliothek Zürich: „Keine Angst vor alten Schriften" (PDF)',
    href: 'https://www.zb.uzh.ch/storage/app/media/ueber-uns/Citizen-Science/Schulzeitreisen/20210621_Keine_Angst_vor_alten_Schriften/Arbeitsblatt.pdf',
  },
  kunsthalleKarlsruhe: { label: 'Kunsthalle Karlsruhe: Glossar Eisengallustinte', href: 'https://www.kunsthalle-karlsruhe.de/glossar/eisengallustinte/' },
  klingspor: { label: 'Klingspor-Museum Offenbach: Rudolf Koch', href: 'https://www.offenbach.de/microsite/klingspor_museum/bibliothek/Rudolf-Koch.php' },
  // Practitioner / learning resources (for people who want to learn it, not
  // factual citations) — surfaced under Weiterlernen.
  muecke: { label: 'M. Mücke: Kurrent lesen und schreiben lernen', href: 'http://www.kurrent-lernen-muecke.de/' },
  adfontesLernen: { label: 'ad fontes (Univ. Zürich): alte Schriften lesen lernen', href: 'https://www.adfontes.uzh.ch/tutorium/schriften-lesen' },
  bfdsLese: { label: 'Bund für deutsche Schrift und Sprache: Leseübungen', href: 'https://www.bfds.de/veroeffentlichungen/leseuebungen/' },
  kurrentschriftNet: { label: 'kurrentschrift.net: Übungsblätter zum Schreiben', href: 'http://www.kurrentschrift.net/' },
  // Harald Süß, Deutsche Schreibschrift — the reference textbook. Linked to its
  // neutral, non-commercial DNB catalogue record (locatable in any library); no
  // material from it is reproduced (quellen-und-rechte.md §1).
  suess: { label: 'Harald Süß: Deutsche Schreibschrift (DNB-Katalog)', href: 'https://d-nb.info/969965451' },
} as const;

export const schriftkunde = {
  eyebrow: 'Schriftkunde',
  title: 'Die deutsche Schreibschrift',
  // Warm opener for newcomers (period tone, second person) — placed above the
  // factual lead so a curious finder of an old letter is met first.
  intro: 'Sie haben einen alten Brief, eine Postkarte oder ein Tagebuch gefunden und erkennen kaum einen Buchstaben? Das ist meist die deutsche Kurrentschrift — über vierhundert Jahre lang ganz gewöhnlich, heute für die meisten ein Rätsel. Diese Seite erklärt in Ruhe, was das ist, wie es funktioniert und warum wir heute nicht mehr so schreiben.',
  lead: 'Vom frühen 16. bis zur Mitte des 20. Jahrhunderts war die Kurrent die allgemeine Verkehrs- und Geschäftsschrift des deutschen Sprachraums — ein knapper, durchweg belegter Überblick über ihre Formen, ihr Werkzeug und ihre Geschichte; für die Tiefe führen die Quellen weiter. Das Projekt selbst beginnt bei drei Ausgangsschriften: Kurrent, Sütterlin und Offenbacher.',

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
      sources: [SRC.kurrent, SRC.ottweiler],
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
      sources: [SRC.offenbacher, SRC.klingspor, SRC.koch1928],
    },
  ],

  // Specimen captions, keyed by variant id (rendered next to the visual).
  specimen: {
    kurrentCaption: 'Schauschrift-Font (GL German Cursive)',
    suetterlinCaption: 'live geschrieben aus der gemeinfreien Vorlage von 1922 — die Synthese-Engine des Projekts',
    // Shown when the engine can't render (cold/unreachable API) and the card
    // falls back to the bundled Sütterlin font — kept truthful about what's on
    // screen. That font maps the long ſ onto the plain 's' key (round End-s is on
    // '#'), so the word's word-initial 's' renders as the correct long ſ.
    // Keep any fallback word's s non-final — a final s would wrongly render as ſ.
    suetterlinCaptionFallback: 'Vorschau in der Sütterlin-Schrift von H. J. Zinken — die Synthese-Engine ist gerade nicht erreichbar',
    // The script's own name, written live. The server-side shaping
    // (core/shaping.py behind GET /write/word) resolves the word-initial 's' to
    // the long ſ. If a glyph of the word has no canonical (surfaced in the
    // response's `missing`), the composition leaves a blank advance there and
    // breaks the connecting stroke: a visible gap mid-word, NOT a seamless
    // omission. The full-font fallback only kicks in when nothing renders at
    // all. Tracing the letter in the admin closes such a gap.
    suetterlinWord: 'sütterlin',
    suetterlinWordFallback: 'sütterlin',
    // Offenbacher: a marked excerpt from Koch's own 1928 public-domain plate
    // (lowercase a–f), the genuine historical hand rather than a synthesised glyph.
    offenbacherCaption: 'Originaltafel von Rudolf Koch, 1928 (Ausschnitt)',
    offenbacherAlt: 'Ausschnitt der Offenbacher-Schrifttafel von Rudolf Koch (1928): die Kleinbuchstaben a–f',
  },

  // --- Einordnung & Abgrenzung ----------------------------------------------
  classifyHeading: 'Einordnung & Abgrenzung',
  classifyLead: 'Was diese Schrift eigentlich ist — und wie sie sich von dem unterscheidet, was man anderswo schrieb.',
  classify: [
    {
      term: 'Deutsch oder lateinisch',
      desc: 'Die Kurrent ist eine gebrochene, eckige Schrift aus der gotischen Tradition. Ihr Gegenstück ist die runde, lateinische Schreibschrift — die englische Copperplate ist deren bekannteste Ausprägung. Eckig-gebrochen gegen rund-geschwungen: daran erkennt man einen deutschen und einen englischen Brief desselben Jahres auf den ersten Blick.',
    },
    {
      term: 'Beide zugleich gelernt',
      desc: 'Deutschsprachige lernten zwei Schreibschriften nebeneinander — die Kurrent fürs Deutsche, die lateinische für Fremdwörter und fremde Namen. In ein und demselben Brief konnte die Schrift mitten im Satz wechseln.',
    },
    {
      term: 'Druck oder Hand',
      desc: 'Die kantige Fraktur ist eine gedruckte Schrift, die Kurrent ihre handgeschriebene Schwester desselben Zeitraums. „Altdeutsche Schrift" meint beides zusammen — ein Sammelbegriff, kein Fachwort.',
    },
  ],
  classifySources: [SRC.adfontesKursive, SRC.schreibschrift, SRC.englischeSchreibschrift, SRC.lateinischeAusgangsschrift, SRC.fraktur],

  // --- Wo wurde so geschrieben ----------------------------------------------
  geographyHeading: 'Wo wurde so geschrieben',
  geographyLead: 'Die Kurrent war die Schrift des gesamten deutschen Sprachraums — ihr Ende verlief aber in jedem Land anders. Auch deshalb sehen alte Briefe je nach Herkunft verschieden aus.',
  geography: [
    {
      term: 'Deutschland',
      desc: 'Bis zum Lehrverbot 1941 die allgemeine Schrift; ab den 1920er Jahren löste die Sütterlin in den Schulen die ältere Kurrent ab.',
    },
    {
      term: 'Österreich',
      desc: 'Lehrte bis 1938/39 die traditionelle Kurrent als erste Schrift — nicht die preußische Sütterlin. Nach 1945 nur noch selten als Zweitschrift.',
    },
    {
      term: 'Schweiz',
      desc: 'Gab die Kurrent schon um 1900 auf — kein Verbot, sondern kantonale Schulbeschlüsse. Die Sütterlin wurde hier nie eingeführt.',
    },
    {
      term: 'Liechtenstein',
      desc: 'Im Alltag bis ins 20. Jahrhundert üblich; die Schule stellte 1935 von sich aus auf die lateinische Schrift um — noch vor dem deutschen Erlass.',
    },
  ],
  geographySources: [SRC.kurrent, SRC.ausgangsschrift, SRC.zbZuerich, SRC.liechtenstein],

  // --- Warum wir heute nicht mehr so schreiben ------------------------------
  endHeading: 'Warum wir heute nicht mehr so schreiben',
  endParagraphs: [
    'Die Kurrent und die Sütterlin verschwanden nicht allmählich, sondern fast auf einen Schlag: Ein Erlass vom Januar 1941 beendete die gebrochenen Druckschriften, ein Rundschreiben vom 1. September 1941 untersagte, die Kurrent in der Schule zu lehren. Ab dem Schuljahr 1941/42 lernten alle Kinder nur noch die lateinische „Deutsche Normalschrift".',
    'Begründet wurde das Verbot mit der Behauptung, die gebrochenen Schriften seien „Schwabacher Judenlettern" — eine erfundene, sachlich falsche Propaganda. Als sachlichen Grund nannte die Reichskanzlei dagegen, dass im Ausland kaum jemand die eckige deutsche Schrift lesen könne.',
    'Die Folge: Wer ab 1941/42 eingeschult wurde, lernte die alte Schrift gar nicht mehr. Innerhalb einer einzigen Generation wurde aus einer Alltagsschrift eine, die heute nur noch wenige lesen können — deshalb wirkt ein alter Brief oft wie eine Geheimschrift.',
  ],
  endSources: [SRC.erlass, SRC.antiquaFraktur, SRC.suetterlin],

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
      term: 'Papier & Tafel',
      desc: 'Geschrieben wurde auf reißfestem Hadernpapier, ab dem 19. Jahrhundert auf vergilbendem Holzschliffpapier. Das Schreiben gelernt wurde auf der Schiefertafel und im vierlinigen Schönschreibheft.',
    },
  ],
  materialSources: [SRC.eisengallus, SRC.kunsthalleKarlsruhe, SRC.hadernpapier, SRC.schiefertafel],

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
  timelineSources: [SRC.adfontesKursive, SRC.ottweiler, SRC.kurrent, SRC.suetterlin, SRC.offenbacher, SRC.ausgangsschrift, SRC.erlass],

  // --- Quellen ---------------------------------------------------------------
  sourcesHeading: 'Quellen',
  sourcesIntro:
    'Jede Angabe auf dieser Seite ist belegt. Die Fakten stützen sich auf paläographische und archivische Quellen — ein Universitäts-Tutorium (ad fontes, Univ. Zürich), Schulmuseen und Archive, Museen, das Lehrbuch von Süß sowie die gemeinfreien Originaltafeln. Die Wikipedia-Artikel sind der frei zugängliche Überblick dazu, nicht die Grundlage. Die ausführlichen Faktenblätter mit Einzelnachweisen liegen in der Schriftkunde des Projekts.',
  sourcesScholarlyHeading: 'Wissenschaft, Archive & Museen',
  sourcesScholarly: [
    SRC.adfontesKursive,
    SRC.adfontesKurrent,
    SRC.ottweiler,
    SRC.zbZuerich,
    SRC.liechtenstein,
    SRC.klingspor,
    SRC.kunsthalleKarlsruhe,
    SRC.ziffern,
    SRC.koch1928,
    SRC.suess,
  ],
  sourcesWikipediaHeading: 'Wikipedia (Überblicksartikel)',
  sourcesWikipedia: [
    SRC.kurrent,
    SRC.suetterlin,
    SRC.offenbacher,
    SRC.lineatur,
    SRC.schreibschrift,
    SRC.feder,
    SRC.redis,
    SRC.eisengallus,
    SRC.langesS,
    SRC.englischeSchreibschrift,
    SRC.lateinischeAusgangsschrift,
    SRC.fraktur,
    SRC.ausgangsschrift,
    SRC.erlass,
    SRC.antiquaFraktur,
    SRC.nasalstrich,
    SRC.rotunda,
    SRC.pfennig,
    SRC.mark,
    SRC.hadernpapier,
    SRC.schiefertafel,
  ],
  sourcesRepo:
    'Als gemeinfreie Originaltafeln arbeitet das Projekt mit der Loth-Tafel 1866 (Kurrent), der Sütterlin-Ausgangsschrift 1922 und der Offenbacher-Tafel von Rudolf Koch (1928).',

  // --- Weiterlernen (Empfehlung) ---------------------------------------------
  recommendation: {
    heading: 'Weiterlernen',
    before: 'Wer die deutsche Schreibschrift nicht nur betrachten, sondern wirklich lesen und schreiben lernen möchte, dem sei ',
    linkLabel: 'Harald Süß’ „Deutsche Schreibschrift. Lesen und Schreiben lernen"',
    href: SRC.suess.href,
    after: ' ans Herz gelegt — das Lehrbuch, aus dem auch der Autor dieses Projekts die Kurrent gelernt hat. Hier geht es bewusst nur um den Überblick; die Tiefe steht dort.',
    practiceIntro: 'Zum kostenlosen Lesen- und Schreibenlernen gibt es im Netz mehrere gute Anlaufstellen:',
    practiceLinks: [SRC.muecke, SRC.adfontesLernen, SRC.bfdsLese, SRC.kurrentschriftNet],
  },

  sourcesLabel: 'Quellen:',
} as const;
