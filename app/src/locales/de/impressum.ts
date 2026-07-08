// German strings for the legal page (sections/impressum/*).
// Pre-i18n message catalog — key tree mirrors a future i18next `impressum`
// namespace. All legal prose lives here as data; the component keeps only
// the layout logic. Deliberately approachable (the audience is far less
// technical than e.g. anyplot's): short paragraphs, no legalese walls.

export const impressum = {
  title: 'Impressum & Datenschutz',
  // Footer link split in two so it stays one row on mobile: `footerLink` always
  // shows, `footerLinkRest` only on sm+ (PublicFooter hides it at xs).
  footerLink: 'Impressum',
  footerLinkRest: ' & Datenschutz',
  imprint: {
    heading: 'Impressum',
    operatorLabel: 'Betreiber',
    operatorName: 'Markus Neusinger',
    operatorPlace: 'Visp, Schweiz',
    contactLabel: 'Schreib mir',
    email: 'admin@kurrentschrift.ink',
    linkedinLabel: 'LinkedIn',
    linkedinHandle: 'markus-neusinger',
    linkedinUrl: 'https://www.linkedin.com/in/markus-neusinger/',
    // The operator's other project, listed with the operator info so it is
    // actually findable (a mid-paragraph mention further down was too hidden).
    projectsLabel: 'Weiteres Projekt',
    anyplotLabel: 'anyplot.ai',
    anyplotUrl: 'https://anyplot.ai',
    disclaimer:
      'kurrentschrift.ink ist eine private Liebhaberei: der Versuch, die deutsche Kurrentschrift wieder lesbar und schreibbar zu machen. Alle gezeigten Schriftzüge sind mit Sorgfalt nachgebildet und als Synthese gekennzeichnet — kein historisches Original.',
  },
  privacy: {
    heading: 'Datenschutz',
    intro:
      'Wer diese Seiten besucht, bleibt unbehelligt: kein Konto, keine Cookies, kein Verzeichnis der Besucher. Verantwortlich für die Datenverarbeitung ist der oben genannte Betreiber.',
    analyticsTitle: 'Besucherstatistik',
    analyticsBeforeLink:
      'Gezählt wird nur, was sich ohne Namen zählen lässt: Seitenaufrufe, nicht Personen. Dafür sorgt Plausible Analytics — ohne Cookies, ohne Verfolgung über fremde Seiten hinweg. Die Zählung steht ',
    analyticsLinkText: 'jedermann offen',
    analyticsUrl: 'https://plausible.io/kurrentschrift.ink',
    analyticsAfterLink: ' — wer mag, sieht genau das, was ich sehe.',
    logsTitle: 'Server-Logs',
    logs:
      'Was die Technik beim Besuch nebenher notiert — IP-Adresse, abgerufene Seite, Browser-Kennung —, dient allein der Sicherheit und Fehlersuche und verschwindet nach dreißig Tagen von selbst (Google Cloud Logging).',
    hostingTitle: 'Hosting & Dienste',
    hostingIntro: 'Sämtliche Dienste laufen in der EU:',
    hosting: [
      { label: 'Hosting', value: 'Google Cloud Run (Niederlande)' },
      { label: 'Datenbank', value: 'Google Cloud SQL (Niederlande)' },
      { label: 'CDN / Schutz', value: 'Cloudflare (EU-Rechenzentren für EU-Besucher)' },
      { label: 'Statistik', value: 'Plausible Analytics (EU)' },
    ],
    notCollectedTitle: 'Was hier nicht gesammelt wird',
    notCollected: [
      'keine Konten, keine Profile',
      'keine Cookies',
      'keine personenbezogenen Daten, keine Weitergabe an Dritte',
      'kein Training von KI-Modellen mit Besucherdaten',
    ],
    rightsTitle: 'Deine Rechte',
    rights:
      'Auskunft, Berichtigung, Löschung: Wo nichts über dich gespeichert ist, gibt es auch nichts auszuhändigen oder zu tilgen. Bei Fragen genügen ein paar Zeilen per E-Mail.',
  },
  sources: {
    heading: 'Quellen & Lizenzen',
    geometry:
      'Die Gestalt der Buchstaben folgt gemeinfreien Schreibvorlagen: der Sütterlin-Ausgangsschrift (Leitfaden 1922) und der Kurrent-Tafel von Loth (1866). Der Duktus — Strichfolge und Schreibrichtung — ist meine eigene, handkuratierte Arbeit darüber. Historische Quellen behalten ihre eigene Lizenz; gemeinfreie Vorlagen bleiben gemeinfrei.',
    fonts:
      'Schriften: EB Garamond und Playfair Display (SIL Open Font License) sowie GL-GermanCursive (Gutenberg-Labo, freie Lizenz) und die Sütterlin-Schrift von H. J. Zinken (Freeware, Verbreitung gestattet).',
    // The repository is public now — the paragraph names and links it
    // (split around the link, same pattern as privacy.analytics*).
    codeBeforeLink:
      'Was offen ist, darf mit Quellenangabe genutzt werden: der Quellcode steht unter MIT-Lizenz, die gemeinfreien Vorlagen sind ohnehin frei. Das Repository liegt offen einsehbar auf ',
    codeLinkText: 'GitHub',
    codeUrl: 'https://github.com/MarkusNeusinger/kurrentschrift',
    codeAfterLink: '.',
    reserved:
      'Die hier gelernten Daten dagegen — die kuratierten Glyph-Vorlagen, der Duktus und die Schrift-Statistik, die im Hintergrund entstehen und die Grundlage der Synthese bilden, ebenso die daraus trainierten Lese-Modelle zur Buchstabenerkennung — bleiben meine eigene, vorbehaltene Arbeit. Sie sind nicht Teil der MIT-Lizenz, auch wenn das Repository offen einsehbar ist; eine Nachnutzung nur nach Rücksprache.',
  },
  transparency: {
    heading: 'Transparenz',
    text:
      'kurrentschrift.ink ist das Werk eines Einzelnen, offen für alle. Die Website läuft vollständig in der EU — React im Browser, Python und PostgreSQL auf Google Cloud in den Niederlanden. Fragen, Hinweise und Berichtigungen sind jederzeit willkommen — ich freue mich über Post.',
  },
  lastUpdated: 'Visp, im Juni 2026',
} as const;
