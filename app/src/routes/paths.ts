// Centralized route constants — the single place URLs live, so links, redirects
// and the route map never drift apart. Grows with the public pages planned in
// docs/reference/frontend-stack.md §2 (/lernen, /animation, /lese-hilfe, …);
// the /de/ and /en/ i18n prefixes (post-MVP) will wrap these in one place too.
export const paths = {
  home: '/',
  schriftkunde: '/schriftkunde',
  // Two area hubs group the four tools so the top nav stays at three entries
  // (Schriftkunde · Lesen · Schreiben). Lesen = Quiz + Tafel, Schreiben =
  // Übungsblatt + Federprobe; each hub is a small overview page, not a dropdown.
  lesen: '/lesen',
  schreiben: '/schreiben',
  // The worksheet generator moved under the Schreiben hub (it used to own
  // /schreiben). /federprobe, /tafel, /quiz keep their stable standalone URLs.
  worksheet: '/schreiben/uebungsblatt',
  scribe: '/federprobe',
  tafel: '/tafel',
  quiz: '/quiz',
  // The reading aid under the Lesen hub: a guessed word written, beside the
  // readings that would look the same (website audit 2026-08-29, 4/8).
  vergleichen: '/lesen/vergleichen',
  impressum: '/impressum',
  // The admin is one workbench in three views — Buchstaben · Übergänge ·
  // Wörter — over one chosen Vorlage; /admin itself is the Vorlage picker the
  // area is entered through. Each view carries its subject in the query string
  // (sections/admin/shell/focus.ts), so every link between them is a plain URL.
  // Eigenhand sits beside them rather than inside: it belongs to a HAND, not
  // to a Vorlage — the own-hand capture chain's Bestand and its Bogen printer.
  admin: {
    root: '/admin',
    letters: '/admin/buchstaben',
    joins: '/admin/uebergaenge',
    words: '/admin/woerter',
    eigenhand: '/admin/eigenhand',
  },
  // Retired admin URLs, kept only as redirect sources so older bookmarks,
  // notes and work-item links still land on the view that absorbed them.
  adminLegacy: {
    chart: '/admin/chart',
    compare: '/admin/vergleich',
    pairs: '/admin/paare',
    belege: '/admin/belege',
    werkbank: '/admin/werkbank',
  },
} as const;
