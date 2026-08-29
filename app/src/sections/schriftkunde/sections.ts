// The Schriftkunde page's section anchors — one stable id per <section>, in
// page order, paired with the section's heading from the locale. The view
// hangs the ids on its sections and builds the "Auf dieser Seite" jump list
// from this table; the crawler prerender (lib/seo/prerender.ts) puts the SAME
// ids on its <h2>s and the same list into a <nav>, so a fragment URL such as
// /schriftkunde#buchstaben lands on the same place for a person and a bot.
//
// Ids are German, kebab-case, and part of the public URL surface once linked
// (a shared /schriftkunde#entziffern must keep resolving) — rename with care.
//
// Lives beside tryTargets.ts for the same reason: the Node-run prerender reads
// it without React, so relative imports WITH the .ts extension (type stripping
// knows neither the @/ alias nor extensionless resolution).
import { schriftkunde } from '../../locales/de/schriftkunde.ts';

export const SECTION_IDS = {
  concepts: 'grundbegriffe',
  variants: 'schriften',
  classify: 'einordnung',
  geography: 'verbreitung',
  end: 'ende',
  federn: 'federn',
  material: 'tinte-und-papier',
  letters: 'buchstaben',
  decipher: 'entziffern',
  signs: 'zahlen-und-zeichen',
  timeline: 'chronologie',
  sources: 'quellen',
  recommendation: 'weiterlernen',
  try: 'ausprobieren',
} as const;

export type SectionId = (typeof SECTION_IDS)[keyof typeof SECTION_IDS];

export interface SectionAnchor {
  readonly id: SectionId;
  readonly heading: string;
}

// Page order — the jump list follows the DOM, so the view's Section sequence
// and this table must agree (prerender.test.ts checks the ids against the
// rendered <h2>s in order).
export const SCHRIFTKUNDE_SECTIONS: readonly SectionAnchor[] = [
  { id: SECTION_IDS.concepts, heading: schriftkunde.conceptsHeading },
  { id: SECTION_IDS.variants, heading: schriftkunde.variantsHeading },
  { id: SECTION_IDS.classify, heading: schriftkunde.classifyHeading },
  { id: SECTION_IDS.geography, heading: schriftkunde.geographyHeading },
  { id: SECTION_IDS.end, heading: schriftkunde.endHeading },
  { id: SECTION_IDS.federn, heading: schriftkunde.federnHeading },
  { id: SECTION_IDS.material, heading: schriftkunde.materialHeading },
  { id: SECTION_IDS.letters, heading: schriftkunde.lettersHeading },
  { id: SECTION_IDS.decipher, heading: schriftkunde.decipherHeading },
  { id: SECTION_IDS.signs, heading: schriftkunde.signsHeading },
  { id: SECTION_IDS.timeline, heading: schriftkunde.timelineHeading },
  { id: SECTION_IDS.sources, heading: schriftkunde.sourcesHeading },
  { id: SECTION_IDS.recommendation, heading: schriftkunde.recommendation.heading },
  { id: SECTION_IDS.try, heading: schriftkunde.tryHeading },
];
