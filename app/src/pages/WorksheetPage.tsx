// Thin route mount for `/schreiben` — the actual UI lives in sections/worksheet.

import { useEffect } from 'react';

import { WorksheetView } from '@/sections/worksheet/WorksheetView';

// Default export for React.lazy route splitting (routes/sections).
export default function WorksheetPage() {
  useEffect(() => {
    document.title = 'Lineatur-Vorlage · kurrentschrift';
  }, []);

  return <WorksheetView />;
}
