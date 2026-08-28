// Route targets for the closing "Jetzt ausprobieren" cards (copy in the
// locale, URLs from the central route constants — same split as the hub
// pages). Keyed by the locale's literal card ids, so adding/renaming a card
// without its route (or vice versa) fails to compile.
//
// Lives in its own module (not the view) so the Node-run crawler prerender
// (lib/seo/prerender.ts) can read the same mapping without importing React.
// Relative imports WITH the .ts extension on purpose: the prerender is loaded
// by a plain Node script via type stripping, which knows neither the @/ alias
// nor extensionless resolution (`allowImportingTsExtensions` covers this in
// tsconfig).
import { schriftkunde } from '../../locales/de/schriftkunde.ts';
import { paths } from '../../routes/paths.ts';

export const TRY_TARGETS: Record<(typeof schriftkunde.tryCards)[number]['id'], string> = {
  quiz: paths.quiz,
  tafel: paths.tafel,
  federprobe: paths.scribe,
};
