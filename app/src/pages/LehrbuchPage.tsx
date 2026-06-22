// Thin route mount for `/lehrbuch` — the actual UI lives in sections/lehrbuch.

import { useEffect } from 'react';

import { de } from '@/locales';
import { LehrbuchView } from '@/sections/lehrbuch/LehrbuchView';

// Default export for React.lazy route splitting (routes/sections).
export default function LehrbuchPage() {
  useEffect(() => {
    document.title = de.lehrbuch.pageTitle;
  }, []);

  return <LehrbuchView />;
}
