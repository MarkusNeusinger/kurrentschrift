// Guards for the crawler pages (src/lib/seo/prerender.ts → app/prerender/).
// (a) COVERAGE: every public route in paths.ts has a page, plus the 404.
// (b) COMPLETENESS: the content pages mirror every string leaf of their
//     locale namespace unless a SKIP names it — a new section turns this red
//     until it is rendered or deliberately skipped.
// (c) DRIFT: the committed app/prerender/*.html equal a fresh render byte for
//     byte, and nothing else lies in that directory ("npm run prerender"
//     regenerates). CI runs tests before the build, so this checks the
//     committed files — exactly right, because the API image ships THOSE.
// (d) HEAD + CHROME: title, description, canonical/noindex, the marker the
//     bot-serving check looks for, the site nav on every page, the in-band
//     rights note.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

import { CONFIG } from '../../global-config.ts';
import { schriftkunde } from '../../locales/de/schriftkunde.ts';
import { paths } from '../../routes/paths.ts';
import {
  COMPLETENESS,
  escapeHtml,
  KENNWERTE_LEGEND,
  kennwerte,
  ORIGIN,
  PAGES,
  PRERENDER_MARKER,
  PUBLIC_API,
  PUBLIC_SOURCE_ID,
  renderAll,
  UNIT_PEN_ANGLE,
  UNIT_SLANT,
} from './prerender.ts';

const appDir = fileURLToPath(new URL('../../../', import.meta.url));
const sitemap = readFileSync(join(appDir, 'public/sitemap.xml'), 'utf8');
const rendered = renderAll(sitemap);
const publicRoutes = Object.values(paths).filter((v): v is string => typeof v === 'string');

function leaves(node: unknown, path: string, out: Array<{ path: string; value: string }>) {
  if (typeof node === 'string') {
    out.push({ path, value: node });
  } else if (Array.isArray(node)) {
    node.forEach((v, i) => leaves(v, `${path}.${i}`, out));
  } else if (node && typeof node === 'object') {
    for (const [k, v] of Object.entries(node)) leaves(v, path ? `${path}.${k}` : k, out);
  }
}

const walk = (dir: string, prefix = ''): string[] =>
  readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    return statSync(full).isDirectory() ? walk(full, `${prefix}${name}/`) : [`${prefix}${name}`];
  });

describe('crawler prerender', () => {
  it('covers every public route plus the 404, with unique files', () => {
    const routes = PAGES.map((s) => s.route).filter((r): r is string => r !== null);
    expect(new Set(routes)).toEqual(new Set(publicRoutes));
    expect(PAGES.some((s) => s.route === null && s.noindex)).toBe(true);
    const files = PAGES.map((s) => s.file);
    expect(new Set(files).size).toBe(files.length);
  });

  for (const { file, catalogue, skip } of COMPLETENESS) {
    it(`${file} mirrors every locale leaf (or names it in SKIP)`, () => {
      const html = rendered.get(file)!;
      const all: Array<{ path: string; value: string }> = [];
      leaves(catalogue, '', all);
      expect(all.length).toBeGreaterThan(5);
      const missing = all.filter(
        ({ path, value }) =>
          !skip.some((re) => re.test(path)) && !html.includes(escapeHtml(value)) && !html.includes(value),
      );
      expect(missing.map((m) => m.path), `Locale-Blätter fehlen in ${file}`).toEqual([]);
    });
  }

  it('matches the committed app/prerender/ byte for byte, with nothing extra', () => {
    const dir = join(appDir, 'prerender');
    const onDisk = walk(dir).filter((f) => f.endsWith('.html')).sort();
    expect(onDisk, 'app/prerender/ enthält andere Dateien als der Renderer erzeugt').toEqual([...rendered.keys()].sort());
    for (const [file, html] of rendered) {
      expect(readFileSync(join(dir, file), 'utf8'), `app/prerender/${file} ist veraltet — \`npm run prerender\` ausführen`).toBe(
        html,
      );
    }
  });

  it('carries head, marker, nav and rights note on every page', () => {
    for (const spec of PAGES) {
      const html = rendered.get(spec.file)!;
      expect(html.startsWith(PRERENDER_MARKER), spec.file).toBe(true);
      expect(html).toContain(`<title>${escapeHtml(spec.title)}</title>`);
      expect(html).toContain(`<meta name="description" content="${escapeHtml(spec.description)}">`);
      if (spec.route === null) {
        expect(html).toContain('<meta name="robots" content="noindex,follow">');
        expect(html).not.toContain('rel="canonical"');
      } else {
        const url = spec.route === '/' ? `${ORIGIN}/` : `${ORIGIN}${spec.route}`;
        expect(html).toContain(`<link rel="canonical" href="${url}">`);
        expect(html).toContain(`<meta property="og:url" content="${url}">`);
        expect(html).not.toContain('noindex');
      }
      for (const route of publicRoutes.filter((r) => r !== '/')) {
        expect(html, `${spec.file} nav lacks ${route}`).toContain(`href="${ORIGIN}${route}"`);
      }
      expect(html).toContain('ai-train=yes');
      expect(html).toContain('gesondert vorbehalten');
      expect(html).toContain('<html lang="de">');
    }
  });

  it('restates the API host and public source the SPA uses', () => {
    // prerender.ts cannot import global-config (import.meta.env) under Node.
    expect(PUBLIC_API).toBe(CONFIG.publicApiBase);
    expect(PUBLIC_SOURCE_ID).toBe(CONFIG.sourceId);
  });

  it('holds the Kennwerte and the prose facts together, with every angle naming its reference', () => {
    // A model reading one script's card alone must find the convention on
    // the card, and must never take a pen-edge angle for a slant.
    for (const v of schriftkunde.variants) {
      const fact = (k: string) => v.facts.find((f) => f.k === k)?.v ?? '';
      const slant = fact('Schräglage') || fact('Schriftlage');
      expect(slant, v.id).toContain('zur Grundlinie');
      for (const n of v.data.slantDeg) expect(slant, v.id).toContain(String(n));
      if ('slantAround1900Deg' in v.data) for (const n of v.data.slantAround1900Deg) expect(slant).toContain(String(n));
      expect(fact('Lineatur'), v.id).toContain(v.data.lineature.join(':'));
      if ('lineatureAlt' in v.data) expect(fact('Lineatur')).toContain(v.data.lineatureAlt.join(':'));
      expect(fact('Feder'), v.id).toContain(v.data.pen);
      if ('penAngleDeg' in v.data) {
        for (const n of v.data.penAngleDeg) expect(fact('Feder')).toContain(String(n));
        expect(fact('Feder')).toContain('Federkante');
      }
      expect(fact('Strich'), v.id).toContain(v.data.stroke);
    }
    expect(kennwerte().map((k) => k.id)).toEqual(schriftkunde.variants.map((v) => v.id));
  });

  it('renders the Kennwerte as a visible JSON block and as JSON-LD on the Schriftkunde page', () => {
    const html = rendered.get('schriftkunde.html')!;
    expect(html).toContain('<pre><code class="language-json">');
    expect(html).toContain('&quot;slantDeg&quot;'.replace(/&quot;/g, '"')); // quotes stay quotes in the block
    expect(html).toContain(escapeHtml(KENNWERTE_LEGEND));
    expect(html).toContain('"@type":"ItemList"');
    // Two angle units, never one: the slant to the baseline, the pen angle to
    // the writing line — the JSON-LD must say which is which per property.
    const ld = JSON.parse(html.match(/<script type="application\/ld\+json">(\{"@context":"https:\/\/schema.org","@type":"ItemList"[\s\S]*?)<\/script>/)![1]);
    const units = new Map<string, string>();
    for (const item of ld.itemListElement) {
      for (const prop of item.item.additionalProperty) if (prop.unitText) units.set(prop.name, prop.unitText);
    }
    expect(units.get('slantDeg')).toBe(UNIT_SLANT);
    expect(units.get('slantAround1900Deg')).toBe(UNIT_SLANT);
    expect(units.get('penAngleDeg')).toBe(UNIT_PEN_ANGLE);
    expect(UNIT_PEN_ANGLE).not.toBe(UNIT_SLANT);
    // The block parses back to the locale's data.
    const block = html.match(/<pre><code class="language-json">([\s\S]*?)<\/code><\/pre>/)![1];
    const parsed = JSON.parse(block.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&'));
    expect(parsed.map((k: { id: string }) => k.id)).toEqual(['kurrent', 'suetterlin', 'offenbacher']);
  });

  it('gives machines the letter recipes on the Tafel page and in llms.txt', () => {
    const html = rendered.get('tafel.html')!;
    const src = `${PUBLIC_API}/sources/${PUBLIC_SOURCE_ID}`;
    for (const url of [
      `${PUBLIC_API}/sources`,
      `${src}/templates`,
      `${src}/bboxes/{glyph_key}/crop`,
      `${src}/write/glyphs/{glyph_key}.svg`,
      `${src}/write/glyphs?keys=a,n`,
      `${src}/write/word?text=lesen`,
    ]) {
      expect(html, url).toContain(escapeHtml(url));
    }
    const llms = readFileSync(join(appDir, 'public/llms.txt'), 'utf8');
    expect(llms).toContain(`${src}/write/glyphs/{glyph_key}.svg`);
    expect(llms).toContain(`${src}/bboxes/{glyph_key}/crop`);
  });

  it('never leaves an unescaped angle bracket from the locale in the body', () => {
    // A locale string with "<" would break the document; escapeHtml is the
    // only path from locale to HTML, so a leak means a helper bypassed it.
    for (const [file, html] of rendered) {
      const body = html.slice(html.indexOf('<main>'), html.indexOf('</main>'));
      expect(body, file).not.toMatch(/<(?![a-z/!])/);
    }
  });
});
