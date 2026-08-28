// Renders the Markdown mirror of /schriftkunde into public/schriftkunde.md.
// Runs as `npm run schriftkunde:md` and automatically via `prebuild` — the
// generated file is COMMITTED (dev server and PR review see it; the drift
// test in src/lib/seo/schriftkundeMarkdown.test.ts fails when it is stale).
// Importing the .ts renderer works via Node's native type stripping
// (Node >= 22.18; the Dockerfile builder runs node:22 accordingly).
import { readFileSync, writeFileSync } from 'node:fs';

const { renderSchriftkundeMarkdown, schriftkundeStandFromSitemap } = await import(
  '../src/lib/seo/schriftkundeMarkdown.ts'
);

const sitemap = readFileSync(new URL('../public/sitemap.xml', import.meta.url), 'utf8');
const stand = schriftkundeStandFromSitemap(sitemap);
const md = renderSchriftkundeMarkdown({ stand });
writeFileSync(new URL('../public/schriftkunde.md', import.meta.url), md);
console.log(`schriftkunde:md — public/schriftkunde.md erzeugt (Stand ${stand}, ${md.length} Bytes).`);
