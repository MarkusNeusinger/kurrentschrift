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
    // Six short paragraphs, no sub-headings and no article numbers in the
    // prose (author's call, 2026-09-03: the first draft read like a legal
    // filing, which is not how this page speaks). The facts behind each
    // sentence are unchanged and still verifiable — logs and their thirty
    // days, the per-IP counting and the browser's security reports, the
    // cookieless count over the site's own path, the Netherlands and
    // Cloudflare in front of them — only the apparatus is gone.
    data:
      'Zweierlei fällt beim Besuch trotzdem an. Der Server schreibt jeden Abruf mit: IP-Adresse, Seite, Browser-Kennung. Das braucht es, um die Seite vor Überlastung und Missbrauch zu schützen — dazu zählt er auch mit, wie viele Anfragen von einer Adresse kommen, und nimmt die Sicherheitsmeldungen entgegen, die der Browser schickt, wenn auf einer Seite etwas Unerlaubtes geladen würde. Diese Aufzeichnungen löschen sich nach dreißig Tagen von selbst.',
    analyticsBeforeLink:
      'Und gezählt wird, was sich ohne Namen zählen lässt: Seitenaufrufe, nicht Personen. Dafür sorgt Plausible — ohne Cookies, ohne Verfolgung über fremde Seiten hinweg, eingebunden über einen eigenen Zwischenweg auf dieser Domain, damit kein fremdes Script mitlädt. Die Zählung steht ',
    analyticsLinkText: 'jedermann offen',
    analyticsUrl: 'https://plausible.io/kurrentschrift.ink',
    analyticsAfterLink: ' — wer mag, sieht genau das, was ich sehe.',
    hosting:
      'Das alles läuft auf Google Cloud in den Niederlanden; davor liegt Cloudflare als Schutzschicht — ein weltweites Netz, das Besucher aus Europa in aller Regel über europäische Standorte bedient.',
    basis:
      'Wir tun das, weil ein Betreiber seine Seite schützen und wissen darf, wie oft sie gelesen wird; es gilt das Schweizer Datenschutzgesetz, für Besucher aus der EU zusätzlich die DSGVO.',
    rights:
      'Du kannst jederzeit fragen, was gespeichert ist, der Verarbeitung widersprechen und dich bei der Aufsicht beschweren — in der Schweiz beim Eidgenössischen Datenschutz- und Öffentlichkeitsbeauftragten, in der EU bei der Behörde an deinem Wohnort. Ein paar Zeilen per E-Mail genügen.',
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
    // Was still promising „EU-Rechenzentren" flatly, which this revision
    // withdrew three paragraphs above — two answers on one page (Copilot
    // review, #507). Now it names what runs where and leaves the edge to the
    // Hosting section.
    text:
      'kurrentschrift.ink ist das Werk eines Einzelnen, offen für alle. Server und Datenbank stehen in den Niederlanden — React im Browser, Python und PostgreSQL auf Google Cloud; davor liegt Cloudflares weltweites Netz, wie oben beschrieben. Google und Cloudflare sind US-Anbieter, zertifiziert nach dem EU-US Data Privacy Framework. Fragen, Hinweise und Berichtigungen sind jederzeit willkommen — ich freue mich über Post.',
  },
  lastUpdated: 'Visp, im September 2026',
} as const;
