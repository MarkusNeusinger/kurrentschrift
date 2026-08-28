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

import { paths } from '../../routes/paths.ts';
import { COMPLETENESS, escapeHtml, ORIGIN, PAGES, PRERENDER_MARKER, renderAll } from './prerender.ts';

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

  it('never leaves an unescaped angle bracket from the locale in the body', () => {
    // A locale string with "<" would break the document; escapeHtml is the
    // only path from locale to HTML, so a leak means a helper bypassed it.
    for (const [file, html] of rendered) {
      const body = html.slice(html.indexOf('<main>'), html.indexOf('</main>'));
      expect(body, file).not.toMatch(/<(?![a-z/!])/);
    }
  });
});
