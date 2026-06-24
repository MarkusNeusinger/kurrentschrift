// Thin route mount for `/lesen` — the Lesen hub (Quiz + Tafel). The actual
// layout lives in sections/hub/HubView; this wrapper joins the hub strings
// (locales/de/hub) with the tool URLs (routes/paths).

import { usePageMeta } from '@/hooks/usePageMeta';
import { de } from '@/locales';
import { paths } from '@/routes/paths';
import { HubView } from '@/sections/hub/HubView';

const t = de.hub.lesen;

// Default export for React.lazy route splitting (routes/sections).
export default function LesenPage() {
  usePageMeta(de.seo.lesen);

  return (
    <HubView
      title={t.title}
      lead={t.lead}
      cards={[
        { ...t.cards.quiz, to: paths.quiz },
        { ...t.cards.tafel, to: paths.tafel },
      ]}
    />
  );
}
