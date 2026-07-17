// Admin-side message catalog: the public namespaces plus `admin` and `wizard`.
// Split from the public barrel (see index.ts) so the admin/wizard strings only
// load with the lazy /admin chunks. Admin code imports { de, fmt, ... } from
// '@/locales/admin' — same shape as the public barrel, superset of namespaces,
// so the eventual i18next migration stays mechanical.

import { admin } from './de/admin';
import { wizard } from './de/wizard';
import { de as publicDe } from './index';

export const de = { ...publicDe, admin, wizard } as const;

// Re-export the shared helpers so admin files need exactly one locales import.
export { fmt } from './index';
export {
  COUPLING_LABELS,
  LINEATUR_LABELS,
  STYLE_LABELS,
  ZONE_LABELS,
  couplingLabel,
  styleLabel,
} from './de/common';
