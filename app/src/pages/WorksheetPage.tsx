// Thin route mount for `/schreiben` — the actual UI lives in sections/worksheet.

import { useEffect } from 'react';

import { de } from '@/locales';
import { WorksheetView } from '@/sections/worksheet/WorksheetView';

// Default export for React.lazy route splitting (routes/sections).
export default function WorksheetPage() {
  useEffect(() => {
    document.title = de.worksheet.pageTitle;
  }, []);

  return <WorksheetView />;
}
