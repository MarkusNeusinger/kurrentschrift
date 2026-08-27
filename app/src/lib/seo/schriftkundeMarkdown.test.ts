// Freshness + completeness guard for the Schriftkunde Markdown mirror.
// (a) COMPLETENESS: every string leaf of the locale must appear in the
//     rendering unless a SKIP_PATHS entry names it — a new locale section
//     turns this red until it is mirrored or deliberately skipped.
// (b) DRIFT: the committed public/schriftkunde.md must equal a fresh render
//     byte for byte ("npm run schriftkunde:md" regenerates it). CI runs tests
//     before the build, so it checks the committed file — exactly right.
// (c) CITABILITY: the head must carry canonical, Stand and the in-band
//     ai-train=no reservation.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

import { schriftkunde } from '../../locales/de/schriftkunde.ts';
import {
  escapeMarkdown,
  renderSchriftkundeMarkdown,
  schriftkundeStandFromSitemap,
  SKIP_PATHS,
} from './schriftkundeMarkdown.ts';

const pub = (rel: string) => readFileSync(fileURLToPath(new URL(`../../../public/${rel}`, import.meta.url)), 'utf8');

const stand = schriftkundeStandFromSitemap(pub('sitemap.xml'));
const rendered = renderSchriftkundeMarkdown({ stand });

function leaves(node: unknown, path: string, out: Array<{ path: string; value: string }>) {
  if (typeof node === 'string') {
    out.push({ path, value: node });
  } else if (Array.isArray(node)) {
    node.forEach((v, i) => leaves(v, `${path}.${i}`, out));
  } else if (node && typeof node === 'object') {
    for (const [k, v] of Object.entries(node)) leaves(v, path ? `${path}.${k}` : k, out);
  }
}

describe('schriftkunde markdown mirror', () => {
  it('mirrors every locale leaf (or names it in SKIP_PATHS)', () => {
    const all: Array<{ path: string; value: string }> = [];
    leaves(schriftkunde, '', all);
    expect(all.length).toBeGreaterThan(300);
    const missing = all.filter(
      ({ path, value }) =>
        !SKIP_PATHS.some((re) => re.test(path)) &&
        !rendered.includes(escapeMarkdown(value)) &&
        !rendered.includes(value),
    );
    expect(missing.map((m) => m.path), 'Locale-Blätter fehlen im Spiegel').toEqual([]);
  });

  it('matches the committed public/schriftkunde.md byte for byte', () => {
    expect(pub('schriftkunde.md'), 'app/public/schriftkunde.md ist veraltet — `npm run schriftkunde:md` ausführen').toBe(rendered);
  });

  it('carries canonical, Stand and the rights reservation in the head', () => {
    const head = rendered.slice(0, 2000);
    expect(head).toContain('https://kurrentschrift.ink/schriftkunde');
    expect(head).toContain(`- Stand: ${stand}`);
    expect(head).toContain('ai-train=no');
    expect(head).toContain('Art. 4');
  });
});
