// Thin route mount for `/federprobe` — the live-writing UI lives in
// sections/scribe. No data provider needed: WrittenWord fetches the site-wide
// source's diagnostics directly (CONFIG.sourceId), like WrittenGlyph.

import { ScribeView } from '@/sections/scribe/ScribeView';

// Default export for React.lazy route splitting (routes/sections).
export default function ScribePage() {
  return <ScribeView />;
}
