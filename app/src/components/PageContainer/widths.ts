// The three calibrated content widths of the public pages (design-system.md §4):
// `text` (1152, most pages), `wide` (1280, landing/worksheet) and `narrow` (760,
// focused single-column drills like the quiz — also the ~66-character reading
// measure). Its own module because a component file that also exports a data
// object takes no Fast-Refresh update (react-refresh/only-export-components),
// and HeaderBar reads the widths without rendering a PageContainer at all.
export const PAGE_WIDTHS = { narrow: 760, text: 1152, wide: 1280 } as const;

export type PageWidth = keyof typeof PAGE_WIDTHS;
