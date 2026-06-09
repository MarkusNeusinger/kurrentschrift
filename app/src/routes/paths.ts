// Centralized route constants — the single place URLs live, so links, redirects
// and the route map never drift apart. Grows with the public pages planned in
// docs/reference/frontend-stack.md §2 (/lernen, /animation, /lese-hilfe, …);
// the /de//en i18n prefixes (post-MVP) will wrap these in one place too.
export const paths = {
  home: '/',
  worksheet: '/schreiben',
  quiz: '/quiz',
  admin: {
    root: '/admin',
    chart: '/admin/chart',
  },
} as const;
