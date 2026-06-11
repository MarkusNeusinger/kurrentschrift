// Centralized route constants — the single place URLs live, so links, redirects
// and the route map never drift apart. Grows with the public pages planned in
// docs/reference/frontend-stack.md §2 (/lernen, /animation, /lese-hilfe, …);
// the /de/ and /en/ i18n prefixes (post-MVP) will wrap these in one place too.
export const paths = {
  home: '/',
  worksheet: '/schreiben',
  quiz: '/quiz',
  impressum: '/impressum',
  admin: {
    root: '/admin',
    chart: '/admin/chart',
  },
} as const;
