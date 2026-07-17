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
  impressum: '/impressum',
  admin: {
    root: '/admin',
    chart: '/admin/chart',
    compare: '/admin/vergleich',
    pairs: '/admin/paare',
  },
} as const;
