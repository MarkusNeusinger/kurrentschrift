// Thin route mount for `/schreiben/uebungsblatt` (under the Schreiben hub) —
// the actual UI lives in sections/worksheet.

import { usePageMeta } from '@/hooks/usePageMeta';
import { de } from '@/locales';
import { WorksheetView } from '@/sections/worksheet/WorksheetView';

// Default export for React.lazy route splitting (routes/sections).
export default function WorksheetPage() {
  usePageMeta(de.seo.worksheet);
  return <WorksheetView />;
}
