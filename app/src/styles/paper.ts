// Identity tokens for the "paper & ink" look — aged cream paper, aged iron-gall
// brown as the writing ink, viridian as the single sparing accent. These are the
// single source of truth for the palette: the global MUI theme (theme/), the
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
  sepia: '#5e4726', // eyebrows + small labels; deepened for legibility (~6.3:1 on bg)
  sepiaFaint: '#9a8259', // ruling/Mittellinie tint only — too light for text (2.66:1)
  viridian: '#40826d', // the single accent (chromium-oxide green)
  line: '#b6a079',
} as const;

// ——— Period-grounded extension tokens ———
// Every hex below is either a named real-world referent or marked `approx`
// (screen approximation of described period behaviour / period artifacts —
// tuning dials, to be refined against scans: UB Heidelberg "Jugend" run,
// Pestalozzianum Schulwandbilder).

// Iron-gall school ink states. German school ink was "blauschwarz" by
// regulation (Reichs-Tintenprüfung 1888, supplemented 1912; Pelikan's 1892
// catalogue lists Schwarze Schultinte and Deutsche Reichstinte): it writes
// blue-black (an indigo provisional dye keeps it readable while wet),
// oxidizes to near-black within weeks and browns over decades.
// `paper.ink` above is the ~125-year aged state the site chrome wears.
export const inkState = {
  fresh: '#233044', // freshly written blue-black, indigo dye visible (approx)
  oxidized: '#1c1a17', // fully oxidized, weeks old (approx)
  aged: paper.ink, // decades-aged manuscript brown — the ambient text ink
} as const;

// Schulheft ruling — printed exercise-book ruling is documented from 1871,
// the red printed margin bar (Randleiste) from ~1900 (Schulmuseum Ottweiler
// collection survey; documented row spacings 7/11/15 mm). Hexes approximate
// faded period prints, not fresh process colours.
export const schulheft = {
  rulingBlue: '#8fa8c4', // printed writing-line blue (approx)
  rulingBlueFaded: '#a8bcd0', // recessive variant for context guides (approx)
  marginRed: '#b03a3a', // Randleiste: aged printed red margin bar (approx)
} as const;

// Quiz / worksheet work-surface card — a shade lighter and cleaner than the
// paper ground but still warm (not the stark #fff of a chart-crop frame). The
// single sanctioned lift from the paper tone for an on-page "Arbeitsfläche"
// (the quiz card, design handoff "Tinte & Vergleich"). Local rendering token,
// not part of the MUI palette.
export const cardSurface = '#f6f0e3';

// Period pigment set — the chromolithography palette of German school wall
// charts (Schulwandbilder) and period print. Named real pigments; hexes
// approximate aged prints. Any contrast derivative introduced downstream must
// carry a "derived for contrast, not a period hex" comment (style-guide:
// synthesis stays recognisable as such).
export const pigment = {
  vermilion: '#e34234', // Zinnober (named) — alarm/error family
  oxblood: '#6b2e2a', // Ochsenblut — deep red, usable as text
  ochre: '#cc7722', // Ocker (named) — warning family
  prussianBlue: '#003153', // Preußischblau, Berlin ~1706 (named) — info family
  chromeGreen: '#4a6741', // Chromgrün (chrome yellow + Prussian blue mix)
  oldGold: '#c9a227', // Altgold — Bronzedruck on charts and diplomas (approx)
} as const;

export const garamond = "'EB Garamond', Georgia, 'Times New Roman', serif";
export const script = "'GLKurrent', cursive"; // showpiece only
// Sütterlin show-script (Zinken HJZ 1911) — a genuine upright-ish Sütterlin
// school hand, distinct from the Kurrent-flavoured GLKurrent above. Specimen /
// cold-start fallback only. Note: in this face the plain 's' is the long ſ and
// the round End-s sits on '#'; feed plain ASCII (no U+017F).
export const suetterlin = "'Suetterlin', cursive";
// Display / headline + brand wordmark — Playfair Display: the high-contrast
// Didone/Scotch register of 19th-century (German) Antiqua book print, fully
// legible for readers who can't read the old scripts. User decision with an
// explicit open alternative: Sorts Mill Goudy (a genuine 1915 design, warmer
// and quieter) stays on the table if Playfair proves too sharp.
export const display = "'Playfair Display', 'EB Garamond', Georgia, 'Times New Roman', serif";

// Letterpress deboss for display headlines: a hairline of the paper's light
// tone below the ink, as pressed type catches the sheet's light. Derived from
// paper.hi (8-digit hex, ~35% alpha) so palette tuning carries through.
export const letterpress = `0 1px 0 ${paper.hi}59`;
