// What the loading skeleton has to keep true, rendered to static markup (no DOM
// needed): every script the page shows must have a reserved plate box, and the
// box must carry that script's own aspect ratio. Without a ratio a section would
// reserve nothing, the footer would stand inside the viewport again and the CLS
// this page was measured for would come straight back (frontend-stack.md,
// „CLS auf /tafel").

import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { TafelSkeleton } from './TafelSkeleton';
import { RESERVED_CHART_RATIO, STYLE_ORDER } from './useGrundtafeln';

describe('TafelSkeleton', () => {
  const html = renderToStaticMarkup(<TafelSkeleton waking={false} />);

  it('reserves a plate box for every script the page shows', () => {
    // Emotion prints the ratio without the spaces the token carries.
    const css = html.replace(/\s*\/\s*/g, '/');
    for (const styleId of STYLE_ORDER) {
      const ratio = RESERVED_CHART_RATIO[styleId];
      expect(ratio, `no reserved ratio for ${styleId}`).toBeDefined();
      expect(css).toContain(`aspect-ratio:${ratio.replace(/\s*\/\s*/g, '/')}`);
    }
  });

  it('names the scripts while they load, so the headings never move in', () => {
    expect(html).toContain('Kurrent');
    expect(html).toContain('Sütterlin');
    expect(html).toContain('Offenbacher');
  });

  it('says nothing about a cold start until there is one', () => {
    expect(html).not.toContain('Der Server wacht gerade auf');
    const waking = renderToStaticMarkup(<TafelSkeleton waking />);
    expect(waking).toContain('Der Server wacht gerade auf');
  });
});
