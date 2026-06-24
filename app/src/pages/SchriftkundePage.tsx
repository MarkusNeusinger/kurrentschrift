// Thin route mount for `/schriftkunde` — the actual UI lives in sections/schriftkunde.

import { usePageMeta } from '@/hooks/usePageMeta';
import { de } from '@/locales';
import { SchriftkundeView } from '@/sections/schriftkunde/SchriftkundeView';

// Default export for React.lazy route splitting (routes/sections).
export default function SchriftkundePage() {
  usePageMeta(de.seo.schriftkunde);
  return <SchriftkundeView />;
}
