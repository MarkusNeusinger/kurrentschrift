// Identity tokens for the "paper & ink" look — aged cream paper, aged iron-gall
// brown as the writing ink, viridian as the single sparing accent. These are the
// single source of truth for the palette: the global MUI theme (theme.ts), the
// shared <PaperBackground> texture and PublicHeader all read from here, so the
// identity carries across every page (style-guide §8). Only the work surfaces
// (A4 preview, letter crops, chart scan) opt out with their own neutral ground.
// These are tunable dials — adjust freely while the look settles, then mirror the
// chosen values into the guide.

export const paper = {
  bg: '#e7dabf',
  hi: '#f1e8d4',
  lo: '#d8c7a3',
  ink: '#241a10', // iron-gall ink, aged — primary writing/body
  inkSoft: '#473420',
  sepia: '#6f5230',
  sepiaFaint: '#9a8259',
  viridian: '#40826d', // the single accent (chromium-oxide green)
  line: '#b6a079',
} as const;

export const garamond = "'EB Garamond', Georgia, 'Times New Roman', serif";
export const script = "'GLKurrent', cursive"; // showpiece only
// Display / headline + brand wordmark — more contrast and character than EB Garamond
// at large sizes. Falls back to EB Garamond if Cormorant fails to load.
export const display = "'Cormorant Garamond', 'EB Garamond', Georgia, 'Times New Roman', serif";
