// German UI terminology for the admin (DIN 16552-1 / Süß-Lehrbuch lineature).
// Code identifiers stay English (project language rule); these map the English
// keys used in data/code to the German labels shown to the user.
//
// The four guide lines, top to bottom: Oberlinie · Mittellinie · Grundlinie ·
// Unterlinie. The three zones between them: Oberlänge (Ober↔Mittel),
// Mittellänge (Mittel↔Grund, the x-height body), Unterlänge (Grund↔Unter).
// In our data, `baseline` = Grundlinie (where x-height letters sit) and
// `midband`/`waist` = Mittellinie (top of the x-height body).

export const LINEATUR_LABELS = {
  baseline: 'Grundlinie',
  midband: 'Mittellinie',
  ascender: 'Oberlinie',
  descender: 'Unterlinie',
} as const;

export const ZONE_LABELS = {
  ascender: 'Oberlänge',
  xheight: 'Mittellänge',
  descender: 'Unterlänge',
} as const;

// Coupling height (where a neighbouring letter joins) — same four lines.
export const COUPLING_LABELS: Record<string, string> = {
  baseline: 'Grundlinie',
  midband: 'Mittellinie',
  ascender: 'Oberlinie',
  descender: 'Unterlinie',
};

export const POSITION_LABELS: Record<string, string> = {
  initial: 'Anfang',
  medial: 'Mitte',
  final: 'Ende',
};

export const couplingLabel = (key: string): string => COUPLING_LABELS[key] ?? key;
export const positionLabel = (key: string): string => POSITION_LABELS[key] ?? key;
