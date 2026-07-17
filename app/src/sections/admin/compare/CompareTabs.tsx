// /admin/vergleich shell — tabs over the two comparison surfaces: the classic
// per-letter view (chart crop vs written) and the connected-writing specimens
// (words / letter-pair joins / plates by another hand) vs the engine-composed
// word. The specimen tabs share one overlay toggle; GlyphComparison keeps its
// own header controls unchanged.

import { Box, FormControlLabel, Switch, Tab, Tabs, Typography } from '@mui/material';
import { useState } from 'react';

import { GlyphComparison } from '@/sections/admin/compare/GlyphComparison';
import { WordComparison } from '@/sections/admin/compare/WordComparison';
import type { WordCompareMode } from '@/sections/admin/compare/WordComparison';
import { de } from '@/locales/admin';

type TabKey = 'letters' | WordCompareMode;

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: 'letters', label: de.admin.compare.tabLetters },
  { key: 'words', label: de.admin.compare.tabWords },
  { key: 'pairs', label: de.admin.compare.tabPairs },
  { key: 'other', label: de.admin.compare.tabOther },
];

export function CompareTabs() {
  const [tab, setTab] = useState<TabKey>('letters');
  const [overlay, setOverlay] = useState(true);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: { xs: 2, md: 3 } }}>
        <Tabs value={tab} onChange={(_, v: TabKey) => setTab(v)} variant="scrollable" allowScrollButtonsMobile>
          {TABS.map((t) => (
            <Tab key={t.key} value={t.key} label={t.label} />
          ))}
        </Tabs>
      </Box>
      {tab === 'letters' ? (
        <Box sx={{ flex: 1, minHeight: 0 }}>
          <GlyphComparison />
        </Box>
      ) : (
        <Box sx={{ flex: 1, minHeight: 0, overflowY: 'auto', p: { xs: 2, md: 3 } }}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1, maxWidth: 1100 }}>
            <FormControlLabel
              control={<Switch size="small" checked={overlay} onChange={(e) => setOverlay(e.target.checked)} />}
              label={<Typography variant="caption">{de.admin.compare.overlayToggle}</Typography>}
            />
          </Box>
          <WordComparison mode={tab} overlay={overlay} />
        </Box>
      )}
    </Box>
  );
}
