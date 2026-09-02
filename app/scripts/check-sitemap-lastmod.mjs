// Holds app/public/sitemap.xml's <lastmod> dates against the git history of
// the files each page actually renders (PageSpec.sources in
// src/lib/seo/prerender.ts).
//
// Why this is not mere bookkeeping: prerender.ts reads <lastmod> as the
// crawler page's visible "Stand" line. A date left behind therefore tells every
// bot and every AI answer that the text is older than it is — four routes had
// drifted up to two weeks by the website audit 2026-09-02, because four merged
// PRs changed the copy and none touched the sitemap. `npm run prerender` runs
// this right after writing the files, so the bump is demanded at the moment the
// stale page is produced, not in review.
//
// Two sources of truth for "when did this page last change":
//   * the working tree — a modified/added source file counts as TODAY, which is
//     what makes the check bite while you are still editing;
//   * git history — the newest commit date (%cs, committer date, YYYY-MM-DD)
//     over the page's source files.
// A shallow clone has no usable history (every file looks like it changed in
// the single fetched commit), so there the git half is skipped rather than
// turned into ten false alarms; the working-tree half still runs.
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const { PAGES, ORIGIN, standFromSitemap } = await import('../src/lib/seo/prerender.ts');

const appDir = fileURLToPath(new URL('../', import.meta.url));
const sitemap = readFileSync(new URL('../public/sitemap.xml', import.meta.url), 'utf8');

const git = (args) => execFileSync('git', args, { cwd: appDir, encoding: 'utf8' }).trim();

let history = true;
let dirty = new Set();
try {
  if (git(['rev-parse', '--is-shallow-repository']) === 'true') {
    // CI checks out with fetch-depth 1, where every file looks as if it
    // changed in the single fetched commit — ten false alarms, not a guard.
    history = false;
    console.log('sitemap-lastmod — flache Klonung ohne Historie, nur der Arbeitsbaum wird geprüft');
  }
  // Paths come back relative to the repo root; PageSpec.sources are relative
  // to app/, so translate through the repo root once.
  const repoRoot = git(['rev-parse', '--show-toplevel']);
  const prefix = relative(repoRoot, resolve(appDir));
  dirty = new Set(
    git(['status', '--porcelain', '--', '.'])
      .split('\n')
      .filter(Boolean)
      .map((line) => line.slice(3).trim())
      // A rename reads "old -> new"; the new path is the one that matters.
      .map((path) => (path.includes(' -> ') ? path.split(' -> ')[1] : path))
      .map((path) => relative(prefix, path)),
  );
} catch {
  // Not a git checkout (an unpacked tarball, a Docker build context): nothing
  // to compare against, so the guard steps aside instead of failing the build.
  history = false;
  console.log('sitemap-lastmod — keine Git-Historie verfügbar, Prüfung übersprungen');
}

const newestCommit = (files) => {
  if (!history) return null;
  const dates = files
    .map((file) => {
      try {
        return git(['log', '-1', '--format=%cs', '--', file]);
      } catch {
        return '';
      }
    })
    .filter(Boolean)
    .sort();
  return dates.length ? dates[dates.length - 1] : null;
};

const today = new Date().toISOString().slice(0, 10);
const stale = [];
for (const page of PAGES) {
  // The 404 has no <loc> of its own; it carries the file's newest date.
  if (page.route === null) continue;
  const lastmod = standFromSitemap(sitemap, page.route);
  const touched = page.sources.filter((file) => dirty.has(file));
  const changed = touched.length ? today : newestCommit(page.sources);
  if (changed && changed > lastmod) {
    const why = touched.length ? `${touched.join(', ')} (ungespeichert geändert)` : page.sources.join(', ');
    stale.push({ route: page.route, lastmod, changed, why });
  }
}

if (stale.length) {
  console.error('\nsitemap.xml — <lastmod> ist älter als der Inhalt der Seite:\n');
  for (const s of stale) {
    console.error(`  ${ORIGIN}${s.route}\n    <lastmod> ${s.lastmod}, Inhalt vom ${s.changed}\n    ${s.why}`);
  }
  console.error(
    '\nJedes <lastmod> steht als „Stand“-Zeile auf der Crawler-Seite — bitte in app/public/sitemap.xml' +
      ' nachziehen und `npm run prerender` erneut laufen lassen.\n',
  );
  process.exit(1);
}

console.log(`sitemap-lastmod — ${PAGES.length - 1} Routen geprüft, alle Daten aktuell`);
