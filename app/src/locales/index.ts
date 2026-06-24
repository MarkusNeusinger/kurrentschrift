// Pre-i18n message catalog. Plain `as const` objects whose key tree mirrors
// the future i18next namespaces (docs/reference/frontend-stack.md plans
// react-i18next with /de + /en URL prefixes post-MVP), so the migration is
// mechanical: de.quiz.setup.start → useTranslation('quiz') + t('setup.start').
// Deliberately NO i18next and NO provider yet.

import { admin } from './de/admin';
import { common } from './de/common';
import { hub } from './de/hub';
import { impressum } from './de/impressum';
import { landing } from './de/landing';
import { quiz } from './de/quiz';
import { schriftkunde } from './de/schriftkunde';
import { scribe } from './de/scribe';
import { seo } from './de/seo';
import { tafel } from './de/tafel';
import { wizard } from './de/wizard';
import { worksheet } from './de/worksheet';

export const de = { common, landing, schriftkunde, hub, worksheet, scribe, quiz, tafel, admin, wizard, impressum, seo } as const;

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
