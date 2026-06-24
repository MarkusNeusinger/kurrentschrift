// Thin route mount for `/impressum` — the actual UI lives in sections/impressum.

import { usePageMeta } from '@/hooks/usePageMeta';
import { de } from '@/locales';
import { ImpressumView } from '@/sections/impressum/ImpressumView';

// Default export for React.lazy route splitting (routes/sections).
export default function ImpressumPage() {
  usePageMeta(de.seo.impressum);
  return <ImpressumView />;
}
