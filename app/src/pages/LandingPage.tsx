// Thin route mount for `/` — the actual composition lives in sections/landing.

import { LandingView } from '@/sections/landing/LandingView';

// Default export for React.lazy route splitting (routes/sections).
export default function LandingPage() {
  return <LandingView />;
}
