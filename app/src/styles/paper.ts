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
  // Derived for contrast, not a period hex: viridian darkened until running
  // TEXT passes WCAG AA on the paper grounds (5.15:1 on bg, 5.85:1 on hi,
  // 6.27:1 on cardSurface — #40826d itself is only 3.28:1 on bg). Use this
  // wherever viridian is body-size text (CTAs, confirmations, scores);
  // #40826d stays for large display/initials, borders, fills and focus rings.
  viridianText: '#2e6152',
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

// Quiz answer-surface tokens — the buttons, chips and result pills on the quiz
// "Arbeitsfläche" (design handoff "Tinte & Vergleich"). A work-surface palette,
// intentionally a touch cleaner than the paper identity; kept here as the single
// source so the setup/play/results panels can't drift apart on these values.
export const quiz = {
  face: '#fdfbf6', // unanswered answer button + result pill face
  border: '#c2ad84', // answer button + setup chip border
  pillBorder: '#e0d2b2', // result confusion/miss pill border
  resolvedFace: '#f4eddd', // answered-but-not-picked button face
  // Derived for contrast, not a period hex: the buttons stay enabled after
  // answering, so the label must clear WCAG AA (5.5:1 on resolvedFace —
  // the previous #8a795f sat at 3.61:1).
  resolvedText: '#6e5c42', // answered-but-not-picked button text
} as const;

// One radius across the quiz surface — the chips, answer buttons and result
// pills used to mix 5/6/7px; this aligns them with the 6px cards + InkButton.
export const quizRadius = '6px';

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

// ——— Overlay layers over a work surface (Ebenen-Token) ———
// A layer is one reading drawn ON TOP of a crop, scan or sketch. Every overlay
// ground is white or plate ink (§5 surface rule), so a layer hue has to clear
// 3:1 against BOTH (WCAG 1.4.11, non-text graphical object) — which is what the
// set this replaces did not: `#00b37e` sat at 2.71:1 on white, and it met the
// engine's red at a deuteranope separation no reader with a red-green
// deficiency can use. The hues below sit on the blue↔yellow axis, the one that
// survives every dichromacy, and NONE of them is the only channel: each layer
// also carries a stroke style (`layerDash`) and a named legend entry.
export const layer = {
  // Spur — the human-traced pen path, the one line drawn on both grounds.
  // Preußischblau lifted in its own hue until it clears both (4.62:1 on #fff,
  // 3.70:1 on paper.ink). Derived for contrast, not a period hex.
  trace: '#1b7abb',
  // Pfad — the far end of the writing-order ramp, which starts at the Spur's
  // own colour. Blue → Ocker is the one diverging ramp that keeps its direction
  // under every dichromacy, so the writing ORDER stays legible.
  path: pigment.ochre,
  // Engine — what the composer writes over the ink. Always DASHED where it lies
  // over a crop: Ocker and Zinnober collapse onto one another for a deuteranope
  // and the ramp's far end can meet the engine line on the same word card.
  engine: pigment.vermilion,
} as const;

// One stroke style per layer — the redundant channel, so colour is never the
// only carrier. `strokeDasharray` FACTORS, multiplied by the caller's own line
// width, so they hold at every x-height; `null` is a solid line. Spur and Pfad
// share the solid line on purpose: they are the same drawn line, and the Pfad
// adds its own channels (order ramp, start dot, arrow heads) rather than a
// second stroke style.
export const layerDash = {
  trace: null,
  path: null,
  engine: [4, 3],
} as const;

// The Absetzer — the connector between two pen-down stretches. NOT a layer: it
// is the Pfad layer's second mark, it carries no reading of its own and it has
// no entry in the legend, so the pairwise colour-vision rule (which is about
// telling two readings apart) does not apply to it. What does apply is the
// ground rule — it is drawn on white and over ink like everything else.
//
// The violet is load-bearing twice over. It is a hue the Spur→Pfad ramp never
// passes through, which a neutral grey is not: that ramp runs blue → Ocker and
// goes through `#74796f` in the middle, so a graphite lift and the middle
// stretch of a three-part path came out the same colour (measured in the
// browser, 2026-09-19). And a lift can never be READ as a stretch anyway: half
// the line's width, dotted, drawn UNDER the strokes, and geometrically joining
// the end of one stretch to the start of the next.
export const absetzer = { color: '#8a5cd0', dash: [2, 2] } as const;

// ——— Die drei Rollen (Rollen-Token) ———
// Tafel · Platte · Eigenhand as colour + stroke + label. No role carries
// Viridian: it is accent, `success` and focus ring at once. Roles are read on
// PAPER grounds (chips, list rows, dots), never over ink, so they are the dark
// end of the period set in three separated lightness steps — lightness is the
// one channel every dichromacy keeps. The label is mandatory beside them
// (Strichart-Regel, design-system.md §2).
//
// A role colours the MARK — dot, border, dash — and never running text: the
// floor asserted below is WCAG 1.4.11's 3:1 for a non-text graphical object,
// and `eigenhand` sits at 3.99:1 on paper.hi, short of the 4.5:1 a body-size
// label needs. A coloured label wants a derived `roleText` sibling first, the
// way `paper.viridianText` sits beside viridian.
export const role = {
  tafel: pigment.prussianBlue, // 11.02:1 on paper.hi
  platte: pigment.oxblood, // 8.41:1 on paper.hi
  // Ocker lifted for contrast (3.99:1 on paper.hi; the raw pigment reaches
  // 2.77). Derived for contrast, not a period hex — deliberately the same
  // lifted Ocker as `imprint.ochreDark` in theme/palette.ts, so the app has one
  // dark Ocker rather than two that drift apart.
  eigenhand: '#a85f17',
} as const;

export const roleDash = { tafel: null, platte: [4, 3], eigenhand: [2, 2] } as const;

// The one place the identity serif is the wrong tool: `--`, `-m`, `_` and `.`
// are exactly the characters that slip while typing in a proportional antiqua
// (audit 2026-09-02, finding 29). A SYSTEM stack, not a shipped face — §2's
// font delivery ships one woff2 per cut under app/public/fonts/, and a mono
// webfont would be a new file, a new @font-face, a new preload and a new OFL
// notice for a handful of admin surfaces. Size comes from the variant
// (`body2` = 17 px), never from an ad-hoc fontSize (§3).
export const mono = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace";

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
