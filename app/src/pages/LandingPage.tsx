// Thin route mount for `/` — the actual composition lives in sections/landing.

import { usePageMeta } from '@/hooks/usePageMeta';
import { de } from '@/locales';
import { LandingView } from '@/sections/landing/LandingView';

// Default export for React.lazy route splitting (routes/sections).
export default function LandingPage() {
  usePageMeta(de.seo.home);
  return <LandingView />;
}
