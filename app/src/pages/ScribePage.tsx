// Thin route mount for `/federprobe` — the live-writing UI lives in
// sections/scribe. No data provider needed: WrittenWord fetches the site-wide
// source's diagnostics directly (CONFIG.sourceId), like WrittenGlyph.

import { usePageMeta } from '@/hooks/usePageMeta';
import { de } from '@/locales';
import { ScribeView } from '@/sections/scribe/ScribeView';

// Default export for React.lazy route splitting (routes/sections).
export default function ScribePage() {
  usePageMeta(de.seo.federprobe);
  return <ScribeView />;
}
