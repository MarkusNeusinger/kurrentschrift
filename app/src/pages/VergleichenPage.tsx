// Thin route mount for `/lesen/vergleichen` — the Lesart page lives in
// sections/vergleichen. No data provider needed: WrittenWord and the specimen
// strips fetch from the site-wide source directly (CONFIG.sourceId).

import { usePageMeta } from '@/hooks/usePageMeta';
import { de } from '@/locales';
import { VergleichenView } from '@/sections/vergleichen/VergleichenView';

// Default export for React.lazy route splitting (routes/sections).
export default function VergleichenPage() {
  usePageMeta(de.seo.vergleichen);
  return <VergleichenView />;
}
