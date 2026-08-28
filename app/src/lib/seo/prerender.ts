// Prerendered HTML for clients without JavaScript — search crawlers, AI
// assistants and their user-directed fetchers, link previews. nginx routes a
// mapped crawler user agent (app/nginx.conf `$is_bot`, the list shared verbatim
// with anyplot) to the API's `/seo-proxy/{route}`, which serves the file this
// module rendered at build time; humans get the SPA at the same URL. Doctrine:
// docs/reference/crawler-richtlinie.md §3, docs/reference/frontend-stack.md §6.
//
// The renderer walks the SAME locale catalogue the pages render, in each
// page's DOM order — one rule per view component — so the crawler reads what
// the visitor reads. It is PURE (no fs, no process): `tsc`, ESLint and Vitest
// cover it, while the Node build script (scripts/build-prerender.mjs) imports
// it via type stripping and writes app/prerender/*.html. Those files are
// COMMITTED (the API image ships them, api/Dockerfile) and pinned by the
// drift guard in prerender.test.ts.
//
// Relative imports WITH the .ts extension on purpose (not the house `@/`
// alias): plain Node knows neither the alias nor extensionless resolution;
// `allowImportingTsExtensions` covers this, and Vite/Vitest resolve it too.
// Erasable syntax only (no enums/namespaces/parameter properties) — Node's
// type stripping rejects anything else.
import { common } from '../../locales/de/common.ts';
import { hub } from '../../locales/de/hub.ts';
import { impressum } from '../../locales/de/impressum.ts';
import { landing } from '../../locales/de/landing.ts';
import { quiz } from '../../locales/de/quiz.ts';
import { schriftkunde } from '../../locales/de/schriftkunde.ts';
import { scribe } from '../../locales/de/scribe.ts';
import { seo } from '../../locales/de/seo.ts';
import { tafel } from '../../locales/de/tafel.ts';
import { worksheet } from '../../locales/de/worksheet.ts';
import { paths } from '../../routes/paths.ts';
import { TRY_TARGETS } from '../../sections/schriftkunde/tryTargets.ts';

export const ORIGIN = 'https://kurrentschrift.ink';
// The public API host and the source the public pages write from — the same
// values as CONFIG in global-config.ts, restated here because that module
// reads `import.meta.env`, which the Node-run build has no notion of;
// prerender.test.ts holds the two in step.
export const PUBLIC_API = 'https://api.kurrentschrift.ink';
export const PUBLIC_SOURCE_ID = 'suetterlin-1922';
// The site card index.html declares — route-independent on purpose, so link
// previews (which never run JS) always get the same image.
const OG_IMAGE = `${ORIGIN}/og.png`;
const OG_IMAGE_ALT = 'Kurrentschrift — die alte deutsche Schreibschrift lesen und schreiben lernen';
// First line of every prerendered file. The daily bot-serving check
// (.github/workflows/bot-serving-check.yml) looks for exactly this string to
// tell a prerendered page from the SPA shell — keep it stable.
export const PRERENDER_MARKER = '<!-- kurrentschrift.ink prerender -->';

type SourceRef = { readonly label: string; readonly href: string };
type TermItem = { readonly term: string; readonly desc: string };

// ---------------------------------------------------------------- escaping

export function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
const e = escapeHtml;
// Text inside <pre><code>: only the three characters that would break the
// document — quotes stay quotes, so an HTML→Markdown converter hands a model
// the JSON verbatim.
const escapeCode = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
// `</` inside a <script> would end it early; the escape is plain JSON and
// parses back to the identical string.
const jsonLd = (payload: object) =>
  `<script type="application/ld+json">${JSON.stringify(payload).replace(/<\//g, '\\u003c/')}</script>`;

// ---------------------------------------------------------------- stand date

// The Stand date is read from sitemap.xml's <lastmod> for the route —
// deterministic (no new Date(); the files must not change on every build)
// and coupled to the already-maintained rule "bump <lastmod> when a page's
// content changes". Exported so the build script and the drift test parse it
// identically.
export function standFromSitemap(sitemapXml: string, route: string): string {
  const loc = route === '/' ? `${ORIGIN}/` : `${ORIGIN}${route}`;
  const re = new RegExp(`<loc>${loc.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}</loc>\\s*<lastmod>([0-9-]+)</lastmod>`);
  const m = sitemapXml.match(re);
  if (!m) throw new Error(`sitemap.xml carries no <lastmod> for ${route} — the prerender needs it as its Stand date`);
  return m[1];
}

export function latestStand(sitemapXml: string): string {
  const dates = [...sitemapXml.matchAll(/<lastmod>([0-9-]+)<\/lastmod>/g)].map((m) => m[1]).sort();
  if (dates.length === 0) throw new Error('sitemap.xml carries no <lastmod> at all');
  return dates[dates.length - 1];
}

// ---------------------------------------------------------------- fragments

const abs = (route: string) => `${ORIGIN}${route}`;
const a = (href: string, label: string) => `<a href="${e(href)}">${e(label)}</a>`;
const p = (text: string) => `<p>${e(text)}</p>`;
const h2 = (text: string) => `<h2>${e(text)}</h2>`;
const h3 = (text: string) => `<h3>${e(text)}</h3>`;
const em = (text: string) => `<p><em>${e(text)}</em></p>`;
const rows = (items: readonly TermItem[]) =>
  `<ul>${items.map((it) => `<li><strong>${e(it.term)}</strong> — ${e(it.desc)}</li>`).join('')}</ul>`;
const triplet = (items: readonly TermItem[]) => items.map((it) => `${h3(it.term)}${p(it.desc)}`).join('');
const sourceLine = (sources: readonly SourceRef[]) =>
  `<p class="sources"><em>${e(schriftkunde.sourcesLabel)} ${sources.map((s) => a(s.href, s.label)).join(' · ')}</em></p>`;
// The interactive tools exist only in the SPA; a crawler is told so plainly.
const NEEDS_JS = 'Dieses Werkzeug läuft im Browser mit JavaScript — unter derselben Adresse.';

// ---------------------------------------------------------------- pages

export interface PageSpec {
  readonly route: string | null; // null = the 404 page (no route, no canonical)
  readonly file: string; // relative to app/prerender/
  readonly title: string;
  readonly description: string;
  readonly noindex?: boolean;
  readonly breadcrumbs?: readonly { readonly route: string; readonly label: string }[];
  readonly jsonLd?: object; // page-specific structured data, beside the site/breadcrumb node
  readonly body: () => string;
}

// ---------------------------------------------------------------- Kennwerte

// The three scripts' key figures as data — the locale's typed `data` per
// variant, plus identity and sources. Rendered twice on the Schriftkunde page:
// as JSON-LD in the head and as a visible JSON block in the body, because the
// converters assistants fetch pages with (HTML → Markdown) drop <script> and
// keep <pre> — the head alone was invisible to the reviewer that asked for
// this. Numbers and prose are held together by prerender.test.ts.
export const KENNWERTE_LEGEND =
  'Winkel in Grad zur Grundlinie (90 = senkrecht); Lineatur = Oberlänge : Mittellänge : Unterlänge; ' +
  'Federwinkel = Winkel der Federkante zur Schreiblinie, nicht die Schräglage.';

export function kennwerte() {
  return schriftkunde.variants.map((v) => ({
    id: v.id,
    name: v.name,
    period: v.period,
    ...v.data,
    sources: v.sources.map((s) => s.href),
  }));
}

// Two angle units — the whole point of the Kennwerte: a slant is measured to
// the baseline, the pen angle to the writing line (the nib's edge). Naming
// them differently in the structured data is what keeps a consumer from
// merging "75–80°" and "15–20°" into one figure.
export const UNIT_SLANT = 'Grad zur Grundlinie (90 = senkrecht)';
export const UNIT_PEN_ANGLE = 'Grad zur Schreiblinie (Federkante, nicht die Schräglage)';
const unitFor = (key: string) => (key === 'penAngleDeg' ? UNIT_PEN_ANGLE : UNIT_SLANT);

function kennwerteLd(): object {
  return {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: `${schriftkunde.variantsHeading} — Kennwerte`,
    description: KENNWERTE_LEGEND,
    itemListElement: kennwerte().map((k, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      item: {
        '@type': 'DefinedTerm',
        name: k.name,
        description: k.period,
        url: `${abs(paths.schriftkunde)}#${k.id}`,
        additionalProperty: Object.entries(k)
          .filter(([key]) => !['id', 'name', 'period', 'sources'].includes(key))
          .map(([key, value]) => ({
            '@type': 'PropertyValue',
            name: key,
            value: Array.isArray(value) ? value.join(key === 'lineature' || key === 'lineatureAlt' ? ':' : '–') : value,
            ...(key.endsWith('Deg') ? { unitText: unitFor(key) } : {}),
          })),
        sameAs: k.sources,
      },
    })),
  };
}

// ---------------------------------------------------------------- Buchstaben

// Retrieval recipes for the letters themselves — the public API surface a
// client without JavaScript can read: the inventory, the public-domain chart
// crop of each letter, its written form as an image, the geometry, a whole
// word. Rendered on the Tafel page and repeated in llms.txt.
function letterRecipes(): string {
  const src = `${PUBLIC_API}/sources/${PUBLIC_SOURCE_ID}`;
  const row = (label: string, url: string, note: string) =>
    `<li><strong>${e(label)}:</strong> ${a(url, url)} — ${e(note)}</li>`;
  return [
    h2('Buchstaben für Maschinen'),
    p(
      `Die geschriebenen Buchstaben und ihre gemeinfreie Vorlage sind ohne JavaScript abrufbar — beides je Quelle. ` +
        `Die Pfade unten zeigen „${PUBLIC_SOURCE_ID}“ (Sütterlin-Ausgangsschrift 1922), mit der auch die Seite ` +
        `schreibt; für eine andere Quelle den Namen aus der Quellenliste einsetzen. Vollständig geschrieben ist heute ` +
        `nur die Sütterlin; loth-1866 (Kurrent) und koch-1928 (Offenbacher) haben erst einzelne Buchstaben — das ` +
        `Inventar der Quelle sagt mit has_data, welche. {glyph_key} ist der Schlüssel aus dem Inventar (a … z, ` +
        `Großbuchstaben, longs = langes ſ, sz = ß, Ligaturen wie ch, ck, tz).`,
    ),
    '<ul>',
    row('Quellen', `${PUBLIC_API}/sources`, 'JSON, alle Vorlagen mit Schrift (style_id), Lizenz und Herkunft'),
    row('Inventar', `${src}/templates`, 'JSON, ein Eintrag je glyph_key mit has_data'),
    row('Vorlage (Original-Ausschnitt)', `${src}/bboxes/{glyph_key}/crop`, 'PNG, gemeinfreie Tafel von 1922'),
    row('Geschriebene Form', `${src}/write/glyphs/{glyph_key}.svg`, 'SVG auf der Lineatur (Grundlinie, Mittellinie)'),
    row('Geometrie', `${src}/write/glyphs?keys=a,n`, 'JSON: Umriss-Ringe, Mittellinie, Anschlüsse'),
    row('Ganzes Wort', `${src}/write/word?text=lesen`, 'JSON, serverseitig komponiert'),
    row('Ganzes Wort als Bild', `${src}/write/word.svg?text=lesen`, 'SVG auf der Lineatur, mit den generierten Übergängen'),
    `<li><strong>Beispiel:</strong> ${a(`${src}/write/glyphs/e.svg`, 'das Sütterlin-e, geschrieben')} · ${a(`${src}/bboxes/e/crop`, 'seine Vorlage')}</li>`,
    '</ul>',
    em(
      'Die komponierten Züge sind aus dem vorbehaltenen Bestand abgeleitet — abrufen und zitieren ja, Trainingsmaterial nein ' +
        '(api.kurrentschrift.ink/robots.txt). Die Vorlagen-Ausschnitte sind gemeinfrei.',
    ),
  ].join('\n');
}

const crumbHome = { route: '/', label: 'Startseite' };
const crumbLesen = { route: paths.lesen, label: hub.lesen.title };
const crumbSchreiben = { route: paths.schreiben, label: hub.schreiben.title };

const landingBody = () => {
  const t = landing;
  const scriptRows = t.scripts
    .map(
      (s) =>
        `${h3(`${s.name} (${s.feder})`)}${p(s.desc)}<p>${e(s.status)} · ${a(`${abs(paths.tafel)}#${s.styleId}`, s.cta)}</p>`,
    )
    .join('');
  const toolRoutes: Record<keyof typeof t.tools, string> = {
    schriftkunde: paths.schriftkunde,
    quiz: paths.quiz,
    tafel: paths.tafel,
    worksheet: paths.worksheet,
    scribe: paths.scribe,
  };
  // The page's card order (LandingView), not the locale's key order.
  const toolOrder: (keyof typeof t.tools)[] = ['schriftkunde', 'quiz', 'tafel', 'worksheet', 'scribe'];
  const toolRows = toolOrder
    .map((k) => `${h3(t.tools[k].title)}${p(t.tools[k].desc)}<p>${a(abs(toolRoutes[k]), t.tools[k].cta)}</p>`)
    .join('');
  return [
    `<h1>${e(t.hero.title)}</h1>`,
    `<p>${e(t.hero.leadBeforeBold)} <strong>${e(t.hero.leadBold)}</strong>${e(t.hero.leadAfterBold)}</p>`,
    // The written brand word: on the page the engine writes it live; here the
    // fact is stated, not faked with a font.
    `<p><em>„${e(t.hero.word)}“ ${e(t.hero.wordCaptionEngine)}</em></p>`,
    `<p>${a(abs(paths.schreiben), t.hero.ctaWrite)} · ${a(abs(paths.lesen), t.hero.ctaRead)}</p>`,
    h2(t.scriptsHeading),
    p(t.scriptsIntro),
    scriptRows,
    h2(t.toolsHeading),
    p(t.toolsIntro),
    toolRows,
    h2(t.roadmapHeading),
    p(t.roadmapNote),
    `<ul>${t.roadmap.map((r) => `<li><strong>${e(r.title)}</strong> — ${e(r.desc)}</li>`).join('')}</ul>`,
  ].join('\n');
};

const schriftkundeBody = () => {
  const t = schriftkunde;
  const out: string[] = [];
  const push = (...parts: string[]) => out.push(...parts);

  // --- PageHeader: eyebrow + title + intro + lead ---
  push(`<p class="eyebrow">${e(t.eyebrow)}</p>`, `<h1>${e(t.title)}</h1>`, p(t.intro), p(t.lead));

  // --- Grundbegriffe (TripletGrid) ---
  push(h2(t.conceptsHeading), triplet(t.concepts), sourceLine(t.conceptsSources));

  // --- Die drei Schriften (variant cards) ---
  push(h2(t.variantsHeading));
  for (const v of t.variants) {
    push(h3(v.name), em(v.period));
    // Specimen: never embed an image — one honest description line per card
    // (mirrors SpecimenBlock's three branches; the Koch plate additionally
    // links its public-domain source).
    if (v.id === 'kurrent') {
      push(em(`Schriftprobe auf der Webseite: ${t.specimen.kurrentCaption}`));
    } else if (v.id === 'suetterlin') {
      push(
        em(`Schriftprobe auf der Webseite: das Wort „${t.specimen.suetterlinWord}“ — ${t.specimen.suetterlinCaption}`),
      );
    } else {
      // The plate's public-domain source is already in this card's source
      // list — looked up by host rather than by index, so a reordering of the
      // locale's sources array cannot silently link the wrong reference.
      const commons = v.sources.find((s) => s.href.includes('commons.wikimedia.org'));
      const plate = commons ? ` Gemeinfreie Originaltafel: ${a(commons.href, commons.label)}` : '';
      push(
        `<p><em>Schriftprobe auf der Webseite: ${e(t.specimen.offenbacherAlt)} — ${e(t.specimen.offenbacherCaption)}.${plate}</em></p>`,
      );
    }
    push(p(v.essence), `<ul>${v.facts.map((f) => `<li><strong>${e(f.k)}:</strong> ${e(f.v)}</li>`).join('')}</ul>`);
    if ('note' in v && v.note) push(em(v.note));
    push(sourceLine(v.sources));
  }
  // The same figures as data — see kennwerte(); the legend states the
  // conventions once more right next to the numbers.
  // Pretty-printed, but numeric arrays on one line ("[75, 80]") — a
  // three-line array per angle would triple the block for nothing.
  const json = JSON.stringify(kennwerte(), null, 2).replace(/\[\s*((?:-?\d+(?:\.\d+)?,\s*)*-?\d+(?:\.\d+)?)\s*\]/g, (_, nums: string) =>
    `[${nums.split(/,\s*/).join(', ')}]`,
  );
  push(
    h3('Kennwerte (maschinenlesbar)'),
    p(KENNWERTE_LEGEND),
    `<pre><code class="language-json">${escapeCode(json)}</code></pre>`,
    `<p>${e('Die Buchstaben selbst — geschrieben und als Original-Ausschnitt — sind auf der Tafel-Seite maschinenlesbar verlinkt: ')}${a(abs(paths.tafel), 'Buchstaben für Maschinen')}.</p>`,
  );

  push(h2(t.classifyHeading), p(t.classifyLead), rows(t.classify), sourceLine(t.classifySources));
  push(h2(t.geographyHeading), p(t.geographyLead), rows(t.geography), sourceLine(t.geographySources));
  push(h2(t.endHeading), ...t.endParagraphs.map(p), sourceLine(t.endSources));
  push(h2(t.federnHeading), p(t.federnLead), triplet(t.federn), sourceLine(t.federnSources));
  push(h2(t.materialHeading), p(t.materialLead), rows(t.material), sourceLine(t.materialSources));
  push(h2(t.lettersHeading), p(t.lettersLead), rows(t.letters), sourceLine(t.lettersSources));
  // Method only — no source line, like the page; the in-prose Tafel pointer
  // gets an absolute route.
  push(
    h2(t.decipherHeading),
    p(t.decipherLead),
    rows(t.decipher),
    `<p>${e(t.decipherTafel.before)}${a(abs(paths.tafel), t.decipherTafel.linkLabel)}${e(t.decipherTafel.after)}</p>`,
  );
  push(h2(t.signsHeading), p(t.signsLead), rows(t.signs), sourceLine(t.signsSources));
  push(
    h2(t.timelineHeading),
    `<ul>${t.timeline.map((r) => `<li><strong>${e(r.year)}</strong> — ${e(r.text)}</li>`).join('')}</ul>`,
    em(t.timelineNote),
    sourceLine(t.timelineSources),
  );
  // Quellen (group headings are <p> on the page, so bold — not headings)
  push(h2(t.sourcesHeading), p(t.sourcesIntro));
  for (const group of [
    { label: t.sourcesScholarlyHeading, items: t.sourcesScholarly as readonly SourceRef[] },
    { label: t.sourcesWikipediaHeading, items: t.sourcesWikipedia as readonly SourceRef[] },
  ]) {
    push(`<p><strong>${e(group.label)}</strong></p>`, `<ul>${group.items.map((s) => `<li>${a(s.href, s.label)}</li>`).join('')}</ul>`);
  }
  push(em(t.sourcesRepo));
  // Weiterlernen (the viridian-rule aside becomes a blockquote)
  push(
    h2(t.recommendation.heading),
    `<blockquote><p>${e(t.recommendation.before)}${a(t.recommendation.href, t.recommendation.linkLabel)}${e(t.recommendation.after)}</p></blockquote>`,
    p(t.recommendation.practiceIntro),
    `<ul>${t.recommendation.practiceLinks.map((s) => `<li>${a(s.href, s.label)}</li>`).join('')}</ul>`,
  );
  // Jetzt ausprobieren (cards → h3 + absolute route links)
  push(h2(t.tryHeading), p(t.tryLead));
  for (const card of t.tryCards) {
    push(h3(card.title), p(card.body), `<p>${a(abs(TRY_TARGETS[card.id]), `${card.cta} →`)}</p>`);
  }
  return out.join('\n');
};

const hubBody = (h: typeof hub.lesen | typeof hub.schreiben, routes: Record<string, string>) => () =>
  [
    `<h1>${e(h.title)}</h1>`,
    p(h.lead),
    ...Object.entries(h.cards).map(([k, c]) => `${h2(c.title)}${p(c.body)}<p>${a(abs(routes[k]), c.cta)}</p>`),
  ].join('\n');

const quizBody = () => {
  const t = quiz;
  const d = t.difficulties;
  return [
    `<h1>${e(t.title)}</h1>`,
    p(seo.quiz.description),
    p(`${t.setup.introLead}${t.setup.introRest}`),
    '<dl>',
    `<dt>${e(t.setup.scriptLabel)}</dt><dd>${[t.scripts.kurrent, t.scripts.suetterlin, t.scripts.offenbacher].map(e).join(' · ')} — ${e(t.setup.scriptHint)}</dd>`,
    `<dt>${e(t.setup.taskLabel)}</dt><dd>${e(t.setup.modeLetters)} · ${e(t.setup.modeWords)} — ${e(t.setup.taskHint)}</dd>`,
    `<dt>${e(t.setup.difficultyLabel)}</dt><dd>${[d.clean, d.worn, d.messy].map((x) => `${e(x.label)} (${e(x.hint)})`).join(' · ')} — ${e(t.setup.difficultyShortHint)}</dd>`,
    '</dl>',
    p(t.setup.difficultyHint),
    p(t.setup.sourceNote),
    em(NEEDS_JS),
  ].join('\n');
};

const tafelBody = () => {
  const t = tafel;
  // Which script is already written comes from the landing's script cards —
  // the one place that states the engine's honest status per script.
  const state = (written: boolean) => (written ? t.state.written : t.state.original);
  return [
    `<h1>${e(t.title)}</h1>`,
    p(t.intro),
    p(t.note),
    `<ul>${landing.scripts
      .map((s) => `<li><strong>${e(s.name)}</strong> — ${e(t.feder[s.styleId] ?? s.feder)} · ${e(state(s.written))}</li>`)
      .join('')}</ul>`,
    em(NEEDS_JS),
    letterRecipes(),
  ].join('\n');
};

const worksheetBody = () => {
  const t = worksheet;
  return [
    `<h1>${e(t.title)}</h1>`,
    p(t.intro),
    h2(t.config.presetHeading),
    `<ul>${Object.values(t.presets)
      .map((pr) => `<li><strong>${e(pr.label)}</strong> — ${e(pr.note)}</li>`)
      .join('')}</ul>`,
    h2(t.config.lineSystemHeading),
    p(t.config.lineSystemHint),
    h2(t.config.penAngleToggle),
    p(t.config.penAngleHint),
    h2(t.config.rulingHeading),
    p(t.config.rulingNote),
    em(`${NEEDS_JS} ${t.config.download}.`),
  ].join('\n');
};

const scribeBody = () => {
  const t = scribe;
  return [
    `<h1>${e(t.heading)}</h1>`,
    p(t.lead),
    p(`${t.examplesLabel} ${t.examples.join(', ')}`),
    p(t.disclaimer),
    em(NEEDS_JS),
  ].join('\n');
};

const impressumBody = () => {
  const t = impressum;
  const sub = (text: string) => `<h3>${e(text)}</h3>`;
  return [
    `<h1>${e(t.title)}</h1>`,
    h2(t.imprint.heading),
    `<p><strong>${e(t.imprint.operatorLabel)}</strong><br>${e(t.imprint.operatorName)}<br>${e(t.imprint.operatorPlace)}</p>`,
    `<p><strong>${e(t.imprint.contactLabel)}</strong><br>${a(`mailto:${t.imprint.email}`, t.imprint.email)}<br>${e(t.imprint.linkedinLabel)}: ${a(t.imprint.linkedinUrl, t.imprint.linkedinHandle)}</p>`,
    em(t.imprint.disclaimer),
    sub(t.projects.heading),
    `<ul>${t.projects.items.map((pr) => `<li>${a(pr.url, pr.name)} — ${e(pr.description)}</li>`).join('')}</ul>`,
    h2(t.privacy.heading),
    p(t.privacy.intro),
    sub(t.privacy.analyticsTitle),
    `<p>${e(t.privacy.analyticsBeforeLink)}${a(t.privacy.analyticsUrl, t.privacy.analyticsLinkText)}${e(t.privacy.analyticsAfterLink)}</p>`,
    sub(t.privacy.logsTitle),
    p(t.privacy.logs),
    sub(t.privacy.hostingTitle),
    p(t.privacy.hostingIntro),
    `<ul>${t.privacy.hosting.map((r) => `<li><strong>${e(r.label)}:</strong> ${e(r.value)}</li>`).join('')}</ul>`,
    sub(t.privacy.notCollectedTitle),
    `<ul>${t.privacy.notCollected.map((x) => `<li>${e(x)}</li>`).join('')}</ul>`,
    sub(t.privacy.rightsTitle),
    p(t.privacy.rights),
    h2(t.sources.heading),
    p(t.sources.geometry),
    p(t.sources.fonts),
    `<p>${e(t.sources.codeBeforeLink)}${a(t.sources.codeUrl, t.sources.codeLinkText)}${e(t.sources.codeAfterLink)}</p>`,
    p(t.sources.reserved),
    h2(t.transparency.heading),
    p(t.transparency.text),
    em(t.lastUpdated),
  ].join('\n');
};

const notFoundBody = () =>
  [`<h1>${e(common.notFound.title)}</h1>`, p(common.notFound.body), `<p>${a(`${ORIGIN}/`, common.notFound.toHome)}</p>`].join(
    '\n',
  );

export const PAGES: readonly PageSpec[] = [
  { route: '/', file: 'index.html', ...seo.home, body: landingBody },
  {
    route: paths.schriftkunde,
    file: 'schriftkunde.html',
    ...seo.schriftkunde,
    breadcrumbs: [crumbHome],
    jsonLd: kennwerteLd(),
    body: schriftkundeBody,
  },
  {
    route: paths.lesen,
    file: 'lesen.html',
    ...seo.lesen,
    breadcrumbs: [crumbHome],
    body: hubBody(hub.lesen, { quiz: paths.quiz, tafel: paths.tafel }),
  },
  { route: paths.quiz, file: 'quiz.html', ...seo.quiz, breadcrumbs: [crumbHome, crumbLesen], body: quizBody },
  { route: paths.tafel, file: 'tafel.html', ...seo.tafel, breadcrumbs: [crumbHome, crumbLesen], body: tafelBody },
  {
    route: paths.schreiben,
    file: 'schreiben.html',
    ...seo.schreiben,
    breadcrumbs: [crumbHome],
    body: hubBody(hub.schreiben, { worksheet: paths.worksheet, federprobe: paths.scribe }),
  },
  {
    route: paths.worksheet,
    file: 'schreiben/uebungsblatt.html',
    ...seo.worksheet,
    breadcrumbs: [crumbHome, crumbSchreiben],
    body: worksheetBody,
  },
  { route: paths.scribe, file: 'federprobe.html', ...seo.federprobe, breadcrumbs: [crumbHome, crumbSchreiben], body: scribeBody },
  { route: paths.impressum, file: 'impressum.html', ...seo.impressum, breadcrumbs: [crumbHome], body: impressumBody },
  { route: null, file: '404.html', title: seo.notFound.title, description: seo.notFound.description, noindex: true, body: notFoundBody },
];

// ---------------------------------------------------------------- document

// Site-wide nav on every page so a crawler landing deep can walk the site
// without executing the SPA — the same three areas as the SPA's top nav plus
// their tools.
const NAV: readonly { route: string; label: string }[] = [
  { route: paths.schriftkunde, label: common.nav.schriftkunde },
  { route: paths.lesen, label: common.nav.read },
  { route: paths.quiz, label: quiz.title },
  { route: paths.tafel, label: tafel.title },
  { route: paths.schreiben, label: common.nav.write },
  { route: paths.worksheet, label: landing.tools.worksheet.title },
  { route: paths.scribe, label: scribe.heading },
  { route: paths.impressum, label: impressum.footerLink },
];

// The in-band rights note: the site's policy (open — ai-train=yes,
// crawler-richtlinie.md) and the reservation of the curated script data behind
// the API, so a page fetched without its robots.txt context still says both.
// Wording derived from robots.txt + README ("License") + the Impressum — no
// new grant is invented, deliberately no CC license.
const RIGHTS_NOTE =
  'Text und Zusammenstellung © Markus Neusinger, kurrentschrift.ink. Abruf, Zitat mit Quellenangabe und ' +
  'Verlinkung sind ausdrücklich erwünscht; die Seite ist auch als Trainingsmaterial für KI-Modelle ' +
  'freigegeben (ai-train=yes, siehe robots.txt). Der Quellcode des Projekts steht unter MIT-Lizenz; die ' +
  'kuratierten Schriftdaten hinter der API (Duktus, Vorlagen, Statistik) sind gesondert vorbehalten und ' +
  'nur mit Admin-Zugang lesbar.';

// A few lines of CSS so the page also reads well when a human lands on it
// (reader mode, curl -L in a browser, a cached copy) — not a design surface.
const STYLE =
  'body{max-width:42rem;margin:2rem auto;padding:0 1rem;font-family:Georgia,"Times New Roman",serif;' +
  'line-height:1.5;color:#2b2419;background:#f5efe1}a{color:#2c6e5b}nav a{margin-right:.75rem}' +
  '.sources,.eyebrow,footer{font-size:.9rem;color:#6b5f4c}pre{overflow-x:auto;font-size:.85rem}';

function breadcrumbLd(spec: PageSpec): object | null {
  if (!spec.breadcrumbs || spec.route === null) return null;
  const items = [...spec.breadcrumbs, { route: spec.route, label: spec.title.replace(/ · kurrentschrift\.ink$/, '') }];
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((c, i) => ({ '@type': 'ListItem', position: i + 1, name: c.label, item: abs(c.route) })),
  };
}

const WEBSITE_LD = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'kurrentschrift.ink',
  url: `${ORIGIN}/`,
  inLanguage: 'de',
  description: seo.home.description,
  publisher: { '@type': 'Person', name: impressum.imprint.operatorName },
  author: { '@type': 'Person', name: impressum.imprint.operatorName },
};

export function renderPage(spec: PageSpec, { stand }: { stand: string }): string {
  const url = spec.route === null ? null : abs(spec.route);
  const ld = spec.route === '/' ? WEBSITE_LD : breadcrumbLd(spec);
  const head = [
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    `<title>${e(spec.title)}</title>`,
    `<meta name="description" content="${e(spec.description)}">`,
    // The 404 must not become an indexable soft-404; every other page asks
    // for large image previews (the site card).
    `<meta name="robots" content="${spec.noindex ? 'noindex,follow' : 'max-image-preview:large'}">`,
    url ? `<link rel="canonical" href="${e(url)}">` : '',
    '<meta property="og:type" content="website">',
    '<meta property="og:site_name" content="kurrentschrift.ink">',
    '<meta property="og:locale" content="de_DE">',
    url ? `<meta property="og:url" content="${e(url)}">` : '',
    `<meta property="og:title" content="${e(spec.title)}">`,
    `<meta property="og:description" content="${e(spec.description)}">`,
    `<meta property="og:image" content="${OG_IMAGE}">`,
    '<meta property="og:image:width" content="1200">',
    '<meta property="og:image:height" content="630">',
    `<meta property="og:image:alt" content="${e(OG_IMAGE_ALT)}">`,
    '<meta name="twitter:card" content="summary_large_image">',
    `<meta name="twitter:title" content="${e(spec.title)}">`,
    `<meta name="twitter:description" content="${e(spec.description)}">`,
    `<meta name="twitter:image" content="${OG_IMAGE}">`,
    `<meta name="twitter:image:alt" content="${e(OG_IMAGE_ALT)}">`,
    ld ? jsonLd(ld) : '',
    spec.jsonLd ? jsonLd(spec.jsonLd) : '',
    `<style>${STYLE}</style>`,
  ]
    .filter(Boolean)
    .join('\n');
  const nav = `<nav aria-label="Bereiche">${NAV.map((n) => a(abs(n.route), n.label)).join('\n')}</nav>`;
  const footer =
    `<footer><p>${e(common.footer.tagline)}${e(common.footer.taglineRest)} ${a(common.footer.githubUrl, common.footer.github)}` +
    ` · ${a(abs(paths.impressum), `${impressum.footerLink}${impressum.footerLinkRest}`)}</p>` +
    `<p>Stand: ${e(stand)}${url ? ` · Kanonische Fassung: ${a(url, url)}` : ''}</p>` +
    `<p>${e(RIGHTS_NOTE)}</p></footer>`;
  return [
    PRERENDER_MARKER,
    '<!-- Vorgerendert für Clients ohne JavaScript (Crawler, KI-Agenten); die interaktive Seite ist die SPA',
    '     unter derselben URL. Generiert aus app/src/locales/de/* — nicht von Hand bearbeiten;',
    '     `npm run prerender` erzeugt die Dateien neu. -->',
    '<!DOCTYPE html>',
    '<html lang="de">',
    '<head>',
    head,
    '</head>',
    '<body>',
    `<header>${a(`${ORIGIN}/`, `${common.brand.name}${common.brand.tld}`)}</header>`,
    '<main>',
    spec.body(),
    '</main>',
    nav,
    footer,
    '</body>',
    '</html>',
    '',
  ].join('\n');
}

// Every page with its Stand date resolved — what the build script writes and
// what the drift test compares the committed files against.
export function renderAll(sitemapXml: string): Map<string, string> {
  const out = new Map<string, string>();
  for (const spec of PAGES) {
    const stand = spec.route === null ? latestStand(sitemapXml) : standFromSitemap(sitemapXml, spec.route);
    out.set(spec.file, renderPage(spec, { stand }));
  }
  return out;
}

// ---------------------------------------------------------------- completeness

// The CONTENT pages must mirror their whole locale namespace: every string
// leaf appears in the rendering unless a SKIP names it. The tool pages (quiz,
// tafel, worksheet, federprobe) are UI — their namespaces are mostly labels
// and error states, so they render a described allowlist instead and are not
// held to completeness (the drift guard still pins their output).
export const COMPLETENESS: readonly {
  readonly file: string;
  readonly catalogue: object;
  readonly skip: readonly RegExp[];
}[] = [
  {
    file: 'index.html',
    catalogue: landing,
    skip: [
      /^hero\.wordAria$/, // screen-reader label of the written word
      /^hero\.wordCaption$/, // caption of the font FALLBACK — an error state
      /^hero\.replay$/, // button
      /^hero\.waiting$/, // cold-start patience line — an interim state
      /^scripts\.\d+\.styleId$/, // technical key (used in the Tafel anchor)
    ],
  },
  {
    file: 'schriftkunde.html',
    catalogue: schriftkunde,
    skip: [
      /^specimen\.suetterlinCaptionFallback$/, // cold-engine error state
      /^specimen\.suetterlinWordFallback$/,
      /^variants\.\d+\.id$/, // technical keys
      /^tryCards\.\d+\.id$/,
    ],
  },
  { file: 'lesen.html', catalogue: hub.lesen, skip: [] },
  { file: 'schreiben.html', catalogue: hub.schreiben, skip: [] },
  {
    file: 'impressum.html',
    catalogue: impressum,
    skip: [/^footerLink(Rest)?$/], // the footer link on OTHER pages (rendered there)
  },
];
