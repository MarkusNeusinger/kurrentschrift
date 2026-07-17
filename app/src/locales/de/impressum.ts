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
    disclaimer:
      'kurrentschrift.ink ist eine private Liebhaberei: der Versuch, die deutsche Kurrentschrift wieder lesbar und schreibbar zu machen. Alle nachgebildeten Schriftzüge sind mit Sorgfalt synthetisiert und als Synthese gekennzeichnet; daneben zeigt die Seite gemeinfreie historische Originalvorlagen mit Quellenangabe.',
  },
  // "Other projects" block, mirroring the anyplot legal page (name — one-line
  // description; own sites are linked with noopener only to keep the referrer).
  projects: {
    heading: 'Weitere Projekte',
    items: [
      {
        name: 'anyplot.ai',
        url: 'https://anyplot.ai',
        description: 'eine Galerie von Datenvisualisierungs-Beispielen samt Code',
      },
      {
        name: 'cite-citadel',
        url: 'https://github.com/MarkusNeusinger/cite-citadel',
        description: 'ein LLM-gepflegtes, vollständig zitiertes persönliches Wiki',
      },
    ],
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
    hostingIntro:
      'Alle Dienste laufen in EU-Rechenzentren. Google und Cloudflare sind US-Anbieter, zertifiziert nach dem EU-US Data Privacy Framework:',
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
      'keine personenbezogenen Daten über die nach dreißig Tagen gelöschten Server-Logs hinaus, keine Weitergabe an Dritte',
      'kein Training von KI-Modellen mit Besucherdaten',
    ],
    rightsTitle: 'Deine Rechte',
    rights:
      'Auskunft, Berichtigung, Löschung: Über die nach dreißig Tagen gelöschten Server-Logs hinaus ist nichts über dich gespeichert — es gibt also fast nie etwas auszuhändigen oder zu tilgen. Bei Fragen genügen ein paar Zeilen per E-Mail.',
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
      'kurrentschrift.ink ist das Werk eines Einzelnen, offen für alle. Die Website läuft in EU-Rechenzentren — React im Browser, Python und PostgreSQL auf Google Cloud in den Niederlanden; Google und Cloudflare sind US-Anbieter, zertifiziert nach dem EU-US Data Privacy Framework. Fragen, Hinweise und Berichtigungen sind jederzeit willkommen — ich freue mich über Post.',
  },
  lastUpdated: 'Visp, im Juli 2026',
} as const;
