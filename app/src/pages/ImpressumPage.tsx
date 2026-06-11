// Thin route mount for `/impressum` — the actual UI lives in sections/impressum.

import { useEffect } from 'react';

import { de } from '@/locales';
import { ImpressumView } from '@/sections/impressum/ImpressumView';

// Default export for React.lazy route splitting (routes/sections).
export default function ImpressumPage() {
  useEffect(() => {
    document.title = de.impressum.pageTitle;
  }, []);

  return <ImpressumView />;
}
