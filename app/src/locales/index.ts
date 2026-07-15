// Pre-i18n message catalog. Plain `as const` objects whose key tree mirrors
// the future i18next namespaces (docs/reference/frontend-stack.md plans
// react-i18next with /de + /en URL prefixes post-MVP), so the migration is
// mechanical: de.quiz.setup.start → useTranslation('quiz') + t('setup.start').
// Deliberately NO i18next and NO provider yet.

import { common } from './de/common';
import { hub } from './de/hub';
import { impressum } from './de/impressum';
import { landing } from './de/landing';
import { quiz } from './de/quiz';
import { schriftkunde } from './de/schriftkunde';
import { scribe } from './de/scribe';
import { seo } from './de/seo';
import { tafel } from './de/tafel';
import { worksheet } from './de/worksheet';

// PUBLIC namespaces only. The admin/wizard namespaces (~24 kB of source) are
// deliberately NOT part of this barrel: it loads with the first public route,
// and admin strings have no business in a visitor's bundle. Admin code imports
// the superset `de` from '@/locales/admin' instead (same shape plus
// `.admin`/`.wizard`), which lands in the lazy /admin chunks.
export const de = { common, landing, schriftkunde, hub, worksheet, scribe, quiz, tafel, impressum, seo } as const;

// Tiny interpolation helper for messages with embedded variables, mirroring
// i18next's {{name}} placeholder syntax.
export function fmt(template: string, params: Record<string, string | number>): string {
  return template.replace(/\{\{(\w+)\}\}/g, (_, key: string) => String(params[key] ?? ''));
}

// Label maps + helpers shared by admin/wizard code (absorbed from the former
// lib/labels.ts and domain/glyphs.ts POSITION_LABEL).
export {
  COUPLING_LABELS,
  LINEATUR_LABELS,
  POSITION_LABEL,
  POSITION_LABELS,
  STYLE_LABELS,
  ZONE_LABELS,
  couplingLabel,
  positionLabel,
  styleLabel,
} from './de/common';
