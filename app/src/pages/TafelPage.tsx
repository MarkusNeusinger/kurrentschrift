// Thin route mount for `/tafel` — the actual composition lives in sections/tafel.

import { TafelView } from '@/sections/tafel/TafelView';

// Default export for React.lazy route splitting (routes/sections).
export default function TafelPage() {
  return <TafelView />;
}
