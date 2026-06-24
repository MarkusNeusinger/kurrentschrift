// Thin route mount for `/schreiben` — the Schreiben hub (Übungsblatt +
// Federprobe). The actual layout lives in sections/hub/HubView; this wrapper
// joins the hub strings (locales/de/hub) with the tool URLs (routes/paths).

import { usePageMeta } from '@/hooks/usePageMeta';
import { de } from '@/locales';
import { paths } from '@/routes/paths';
import { HubView } from '@/sections/hub/HubView';

const t = de.hub.schreiben;

// Default export for React.lazy route splitting (routes/sections).
export default function SchreibenPage() {
  usePageMeta(de.seo.schreiben);

  return (
    <HubView
      title={t.title}
      lead={t.lead}
      cards={[
        { ...t.cards.worksheet, to: paths.worksheet },
        { ...t.cards.federprobe, to: paths.scribe },
      ]}
    />
  );
}
