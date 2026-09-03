// Holds app/public/sitemap.xml's <lastmod> dates against the git history of
// the page a crawler is actually served — the rendered `app/prerender/*.html`.
//
// Why this is not mere bookkeeping: prerender.ts reads <lastmod> as the
// crawler page's visible "Stand" line. A date left behind therefore tells every
// bot and every AI answer that the text is older than it is — four routes had
// drifted up to two weeks by the website audit 2026-09-02, because four merged
// PRs changed the copy and none touched the sitemap. `npm run prerender` runs
// this right after writing the files, so the bump is demanded at the moment the
// stale page is produced, not in review.
//
// The evidence used to be a hand-kept list per page (PageSpec.sources: the
// locale and data modules a body reads). That list drifted in both directions —
// a shared file like seo.ts marked pages stale whose text had not moved, and a
// body reaching for an unlisted module changed the page unseen. The rendered
// file needs no list: it IS the page. One consequence to expect: a change to
// the site chrome (a nav label, the rights note) rewrites all ten files and
// therefore asks for all ten dates — which is what did happen to the pages a
// crawler reads, so the ask is right rather than noise.
//
// Two sources of truth for "when did this page last change":
//   * the working tree — the build just rewrote the files, so a page whose
//     bytes moved counts as TODAY, which is what makes the check bite while
//     you are still editing;
//   * git history — the newest commit date (%cs, committer date, YYYY-MM-DD)
//     of that one file.
// A shallow clone has no usable history (every file looks like it changed in
// the single fetched commit), so there the git half is skipped rather than
// turned into ten false alarms; the working-tree half still runs.
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const { PAGES, ORIGIN, staleLastmods } = await import('../src/lib/seo/prerender.ts');

const appDir = fileURLToPath(new URL('../', import.meta.url));
const sitemapXml = readFileSync(new URL('../public/sitemap.xml', import.meta.url), 'utf8');

const git = (args) => execFileSync('git', args, { cwd: appDir, encoding: 'utf8' }).trim();
// `git status --porcelain` lines are "XY PATH" and X is a SPACE for a change
// that is only in the working tree — so the output must not be trimmed as a
// whole: that eats the first line's status column and shifts its path by one
// character ("app/…" became "pp/…"), which silently emptied `dirty`.
const gitLines = (args) =>
  execFileSync('git', args, { cwd: appDir, encoding: 'utf8' })
    .split('\n')
    .map((line) => line.replace(/\r$/, ''))
    .filter((line) => line.length > 0);

let history = true;
let dirty = new Set();
try {
  if (git(['rev-parse', '--is-shallow-repository']) === 'true') {
    // CI checks out with fetch-depth 1, where every file looks as if it
    // changed in the single fetched commit — ten false alarms, not a guard.
    history = false;
    console.log('sitemap-lastmod — flache Klonung ohne Historie, nur der Arbeitsbaum wird geprüft');
  }
  // The paths the guard compares are relative to app/, so every reported path
  // has to land in that frame. `--porcelain` reports repo-root-relative paths
  // and ignores status.relativePaths (verified: `git -c
  // status.relativePaths=true status --porcelain` still answers "app/src/…"
  // from inside app/) — but the translation does not rely on that. A path is
  // read from the repo root first, and anything that does not resolve under
  // app/ is retried as already-app-relative, because the failure this guard
  // exists to prevent is a SILENT one: a frame mismatch would empty `dirty`
  // and quietly disarm it.
  const repoRoot = git(['rev-parse', '--show-toplevel']);
  const appAbs = resolve(appDir);
  const toAppRelative = (path) => {
    const fromRoot = relative(appAbs, resolve(repoRoot, path));
    return fromRoot.startsWith('..') ? path : fromRoot;
  };
  dirty = new Set(
    gitLines(['status', '--porcelain', '--', '.'])
      // "XY PATH": two status columns and one space, then the path.
      .map((line) => line.slice(3))
      // A rename reads "old -> new"; the new path is the one that matters.
      .map((path) => (path.includes(' -> ') ? path.split(' -> ')[1] : path))
      // Porcelain quotes a path with unusual characters ("src/a\tb.ts").
      .map((path) => (path.startsWith('"') && path.endsWith('"') ? JSON.parse(path) : path))
      .map(toAppRelative),
  );
} catch {
  // Not a git checkout (an unpacked tarball, a Docker build context): nothing
  // to compare against, so the guard steps aside instead of failing the build.
  history = false;
  console.log('sitemap-lastmod — keine Git-Historie verfügbar, Prüfung übersprungen');
}

const newestCommit = (file) => {
  if (!history) return null;
  try {
    return git(['log', '-1', '--format=%cs', '--', file]) || null;
  } catch {
    return null;
  }
};

const today = new Date().toISOString().slice(0, 10);
const stale = staleLastmods(PAGES, { sitemapXml, dirty, newestCommit, today });

if (stale.length) {
  console.error('\nsitemap.xml — <lastmod> ist älter als der Inhalt der Seite:\n');
  for (const s of stale) {
    const why = s.uncommitted ? `${s.file} (ungespeichert geändert)` : s.file;
    console.error(`  ${ORIGIN}${s.route}\n    <lastmod> ${s.lastmod}, Inhalt vom ${s.changed}\n    ${why}`);
  }
  console.error(
    '\nJedes <lastmod> steht als „Stand“-Zeile auf der Crawler-Seite — bitte in app/public/sitemap.xml' +
      ' nachziehen und `npm run prerender` erneut laufen lassen.\n',
  );
  process.exit(1);
}

console.log(`sitemap-lastmod — ${PAGES.length - 1} Routen geprüft, alle Daten aktuell`);
