// Two attributes of the Schreibtafel's plate image that nothing else can
// carry, rendered to static markup (no DOM needed for either of them):
//
//   - crossOrigin, without which „Lesetafel als PDF" cannot rasterise the
//     plate it is looking at — the display image would file a no-CORS cache
//     entry and the PDF's CORS-mode request would be answered from it and
//     blocked (website audit 2026-09-02, finding 2);
//   - the aspect ratio, which reserves the plate's box before its bytes land
//     (finding 30: three unmeasured scans, desktop CLS 0.47).

import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import type { SourceOut } from '@/lib/api';
import { OriginalScan } from './TafelView';

// The live Sütterlin plate, chart_size as GET /sources reports it.
const SOURCE: SourceOut = {
  id: 'suetterlin-1922',
  style_id: 'suetterlin',
  hand_id: null,
  kind: 'chart',
  title: 'Sütterlin-Ausgangsschrift 1922',
  license: 'PD',
  chart_path: 'data/sources/suetterlin-1922/chart.jpg',
  chart_size: { w: 1614, h: 1300 },
  style_ratio: [1, 1, 1],
  slant_deg: 90,
  attribution: null,
};

describe('OriginalScan', () => {
  const html = renderToStaticMarkup(<OriginalScan source={SOURCE} />);

  it('loads the plate in CORS mode, so the PDF can read the same bytes back', () => {
    expect(html).toContain('crossorigin="anonymous"');
  });

  it('reserves the plate box from the source own chart_size', () => {
    expect(html).toContain('aspect-ratio:1614 / 1300');
  });
});
