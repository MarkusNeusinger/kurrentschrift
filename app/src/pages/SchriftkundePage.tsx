// Thin route mount for `/schriftkunde` — the actual UI lives in sections/schriftkunde.

import { useEffect } from 'react';

import { de } from '@/locales';
import { SchriftkundeView } from '@/sections/schriftkunde/SchriftkundeView';

// Default export for React.lazy route splitting (routes/sections).
export default function SchriftkundePage() {
  useEffect(() => {
    document.title = de.schriftkunde.pageTitle;
  }, []);

  return <SchriftkundeView />;
}
