// Renders the crawler pages (src/lib/seo/prerender.ts) into app/prerender/.
// Runs as `npm run prerender` and automatically via `prebuild` — the
// generated files are COMMITTED (the API image ships them via api/Dockerfile,
// PR review sees them, and the drift test in src/lib/seo/prerender.test.ts
// fails when they are stale). Stale .html files that no page produces any
// more are removed, so a renamed route leaves no ghost behind.
// Importing the .ts renderer works via Node's native type stripping
// (--experimental-strip-types below; unflagged from Node 22.18).
import { mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const { renderAll } = await import('../src/lib/seo/prerender.ts');

const root = fileURLToPath(new URL('../prerender/', import.meta.url));
const sitemap = readFileSync(new URL('../public/sitemap.xml', import.meta.url), 'utf8');
const pages = renderAll(sitemap);

mkdirSync(root, { recursive: true });
for (const [file, html] of pages) {
  mkdirSync(dirname(join(root, file)), { recursive: true });
  writeFileSync(join(root, file), html);
}

// Remove leftovers: any .html under app/prerender/ that is not a rendered page.
const walk = (dir, prefix = '') =>
  readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    return statSync(full).isDirectory() ? walk(full, `${prefix}${name}/`) : [`${prefix}${name}`];
  });
let removed = 0;
for (const rel of walk(root)) {
  if (rel.endsWith('.html') && !pages.has(rel)) {
    rmSync(join(root, rel));
    removed += 1;
  }
}

const bytes = [...pages.values()].reduce((n, html) => n + Buffer.byteLength(html), 0);
console.log(
  `prerender — ${pages.size} Seiten nach app/prerender/ geschrieben (${bytes} Bytes)` +
    (removed ? `, ${removed} veraltete Datei(en) entfernt` : ''),
);
