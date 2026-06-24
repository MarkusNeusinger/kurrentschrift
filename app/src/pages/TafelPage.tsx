// Thin route mount for `/tafel` — the actual composition lives in sections/tafel.

import { usePageMeta } from '@/hooks/usePageMeta';
import { de } from '@/locales';
import { TafelView } from '@/sections/tafel/TafelView';

// Default export for React.lazy route splitting (routes/sections).
export default function TafelPage() {
  usePageMeta(de.seo.tafel);
  return <TafelView />;
}
