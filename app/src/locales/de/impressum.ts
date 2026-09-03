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
      'Was die Technik beim Besuch nebenher notiert — IP-Adresse, abgerufene Seite, Browser-Kennung —, dient allein der Sicherheit und Fehlersuche und verschwindet nach dreißig Tagen von selbst (Google Cloud Logging, Standard-Aufbewahrung).',
    // Added by the website audit 2026-09-02 (finding 36): the page named
    // purposes, retention and recipients, but never the legal ground. The
    // operator sits in Visp (Schweiz), so the Swiss revDSG applies and the
    // GDPR reaches the site through Art. 3(2) for visitors from the EU —
    // both are named because both are true, and a visitor should not have to
    // work out which one covers them.
    basisTitle: 'Worauf sich das stützt',
    basis:
      'Betrieben wird die Seite aus der Schweiz; für sie gilt das revidierte Schweizer Datenschutzgesetz, und weil sie sich auch an Leserinnen und Leser in der EU richtet, daneben die europäische Datenschutz-Grundverordnung. Beides erlaubt, was hier geschieht, aus demselben schlichten Grund: dem berechtigten Interesse, die Seite sicher, erreichbar und in Ordnung zu halten (Art. 6 Abs. 1 lit. f DSGVO). Eine Einwilligung wird nicht eingeholt, weil nichts erhoben wird, das eine bräuchte — keine Cookies, keine Konten, keine Profile.',
    // The three technical defences added on 2026-09-02/03 (rate limiting,
    // the CSP report endpoint, the origin guard). They touch an IP or a URL,
    // so they are named rather than left to be discovered in the code.
    securityTitle: 'Was die Seite zu ihrem Schutz tut',
    security: [
      'Damit niemand die Seite durch schiere Menge lahmlegt oder Kosten auftürmt, wird gezählt, wie viele Anfragen von einer Adresse kommen — am Rand des Netzes und noch einmal auf dem Server. Diese Zähler leben im Arbeitsspeicher, für Minuten, und werden nirgends gespeichert.',
      'Der Browser darf melden, wenn auf einer Seite etwas geladen würde, das die Sicherheitsregeln der Seite verbieten. Solche Meldungen nehmen wir entgegen, um Fehler in eben diesen Regeln zu finden; die gemeldete Adresse wird dabei um alles hinter „?“ und „#“ gekürzt, damit kein eingegebener Text mitkommt.',
      'Ein technischer Schlüssel zwischen Schutznetz und Server stellt sicher, dass Anfragen den vorgesehenen Weg nehmen. Er enthält keine Angaben über Besucher.',
    ],
    hostingTitle: 'Hosting & Dienste',
    // Honest about Cloudflare: it is a worldwide Anycast network, and the
    // promise „EU-Rechenzentren" only holds with Regional Services switched
    // on, which nothing in this repo documents (audit finding 36). So the
    // sentence says what is known and stops there.
    hostingIntro:
      'Hosting, Datenbank und Statistik liegen in europäischen Rechenzentren; der Server steht in den Niederlanden (Google Cloud, Region europe-west4). Cloudflare, das der Seite als Schutzschild und Zwischenspeicher vorgelagert ist, betreibt ein weltweites Netz und bedient Besucher aus Europa in aller Regel über europäische Standorte — verbürgt ist die Region dort nicht. Google und Cloudflare sind US-Anbieter, zertifiziert nach dem EU-US Data Privacy Framework:',
    hosting: [
      { label: 'Hosting', value: 'Google Cloud Run (Niederlande, europe-west4)' },
      { label: 'Datenbank', value: 'Google Cloud SQL (Niederlande)' },
      { label: 'Schutz & Zwischenspeicher', value: 'Cloudflare (weltweites Netz, europäische Standorte für Besucher aus Europa)' },
      { label: 'Statistik', value: 'Plausible Analytics (Server in der EU, über einen eigenen Zwischenweg eingebunden)' },
    ],
    notCollectedTitle: 'Was hier nicht gesammelt wird',
    notCollected: [
      'keine Konten, keine Profile',
      'keine Cookies',
      'keine personenbezogenen Daten über die nach dreißig Tagen gelöschten Server-Logs hinaus, keine Weitergabe an Dritte',
      'kein Training von KI-Modellen mit Besucherdaten',
    ],
    rightsTitle: 'Deine Rechte',
    // Art. 21 (Widerspruch) and Art. 13 Abs. 2 lit. d (Beschwerde) were both
    // missing (audit finding 36). Named for the EU and for Switzerland,
    // because the site is subject to both.
    rights:
      'Auskunft, Berichtigung, Löschung, Widerspruch: Über die nach dreißig Tagen gelöschten Server-Logs hinaus ist nichts über dich gespeichert — es gibt also fast nie etwas auszuhändigen oder zu tilgen. Bei Fragen genügen ein paar Zeilen per E-Mail.',
    rightsObjection:
      'Gegen die Verarbeitung, die sich auf das berechtigte Interesse stützt, kannst du jederzeit Widerspruch einlegen (Art. 21 DSGVO) — eine Nachricht genügt, Gründe brauchst du nicht zu nennen.',
    rightsComplaint:
      'Und wer sich beschweren möchte, kann das tun, ohne mich zu fragen: in der Schweiz beim Eidgenössischen Datenschutz- und Öffentlichkeitsbeauftragten (EDÖB), in der EU bei der Aufsichtsbehörde des eigenen Wohnsitzes oder Arbeitsplatzes (Art. 77 DSGVO).',
  },
  sources: {
    heading: 'Quellen & Lizenzen',
    // All FOUR public-domain plates the project works from, not two: the API's
    // /sources lists koch-1928, loth-1866, petzendorfer-1889 and
    // suetterlin-1922, and the Tafel shows the Koch plate (website audit
    // 2026-09-02). Keep this list and llms.txt in step.
    geometry:
      'Die Gestalt der Buchstaben folgt gemeinfreien Schreibvorlagen: der Sütterlin-Ausgangsschrift von 1922, den Kurrent-Tafeln von Loth (1866) und Petzendorfer (1889) und der Offenbacher-Tafel von Rudolf Koch (1928). Der Duktus — Strichfolge und Schreibrichtung — ist meine eigene, handkuratierte Arbeit darüber. Historische Quellen behalten ihre eigene Lizenz; gemeinfreie Vorlagen bleiben gemeinfrei.',
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
  lastUpdated: 'Visp, im September 2026',
} as const;
