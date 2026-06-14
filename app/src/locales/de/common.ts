// German UI strings shared across surfaces (pre-i18n message catalog).
//
// Key tree mirrors a future i18next `common` namespace so the later migration
// is mechanical (de.common.boot.retry → t('boot.retry')). Plain objects only —
// no i18next, no provider (docs/reference/frontend-stack.md plans that
// post-MVP with /de + /en URL prefixes).

import type { Position } from '@/domain/glyphs';

// --- label maps (absorbed from lib/labels.ts + domain/glyphs.ts) -----------
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

// German label per position, shown wherever a position surfaces to the user
// (the wizard's unified/split choice, the sidebar's per-position sub-entries
// of a split letter). Front · middle · end of a word.
export const POSITION_LABEL: Record<Position, string> = {
  initial: 'Anfang',
  medial: 'Mitte',
  final: 'Ende',
};

export const POSITION_LABELS: Record<string, string> = POSITION_LABEL;

// Short script names keyed by style_id — the admin's source switcher shows
// these instead of the long source titles.
export const STYLE_LABELS: Record<string, string> = {
  kurrent: 'Kurrent',
  suetterlin: 'Sütterlin',
  offenbacher: 'Offenbacher',
};

export const couplingLabel = (key: string): string => COUPLING_LABELS[key] ?? key;
export const positionLabel = (key: string): string => POSITION_LABELS[key] ?? key;
export const styleLabel = (key: string): string => STYLE_LABELS[key] ?? key;

// --- shared strings ---------------------------------------------------------

export const common = {
  brand: {
    name: 'kurrentschrift',
    tld: '.ink',
  },
  nav: {
    write: 'Schreiben',
    read: 'Lesen',
  },
  // Marker for staged/disabled features ("coming soon").
  soon: 'bald',
  // The one recognizable (i) affordance (InfoHint) used across public + admin:
  // surfaces stay minimal, the detail sits a tap away.
  info: {
    open: 'Mehr dazu',
  },
  // Full-page boot states (BootStatus call sites in AdminLayout and QuizView).
  boot: {
    apiUnreachable: 'API nicht erreichbar',
    apiColdStart: 'API startet (Cold Start), einen Moment…',
    loadingSource: 'lade Quelle…',
    // Quiz variant talks about the Vorlage (the source chart), not the API.
    sourceUnreachable: 'Vorlage nicht erreichbar',
    sourceColdStart: 'Vorlage startet (Cold Start), einen Moment…',
    loadingTemplate: 'lade Vorlage…',
    retry: 'Erneut versuchen',
    apiUnreachableDetail: 'Die API (Cloud Run) konnte auch nach mehreren Versuchen nicht erreicht werden.',
    // Followed in JSX by the <code>uv run uvicorn …</code> dev-server hint.
    apiUnreachableDevHint: 'Im lokalen Dev läuft sie über',
  },
  // Router-level error surface (RouteError) — stale-deploy chunk load etc.
  routeError: {
    title: 'Da ist etwas schiefgegangen.',
    body: 'Vermutlich ist die Seite veraltet (neue Version veröffentlicht). Ein Neuladen behebt das in der Regel.',
    reload: 'Seite neu laden',
  },
  // 404 surface (NotFoundPage).
  notFound: {
    title: 'Seite nicht gefunden',
    body: 'Unter dieser Adresse liegt nichts — der Link ist veraltet oder vertippt.',
    toHome: 'Zur Startseite',
  },
  // WrittenGlyph — the "as written" ductus playback (quiz prompt today).
  writtenGlyph: {
    ariaLabel: 'Kurrent-Buchstabe, wie geschrieben',
    replay: 'noch einmal schreiben',
  },
} as const;
