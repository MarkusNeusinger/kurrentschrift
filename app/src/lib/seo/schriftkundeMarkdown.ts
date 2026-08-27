// Markdown mirror of the /schriftkunde page for clients without JavaScript
// (crawler-richtlinie.md: the AI retrieval agents the policy welcomes fetch
// raw HTML — a Vite SPA hands them an empty shell). The renderer walks the
// SAME locale catalogue the page renders, in the page's DOM order
// (SchriftkundeView.tsx), one rule per view component. It is PURE — no fs, no
// process — so `tsc`, ESLint and Vitest cover it, while the Node build script
// (scripts/build-schriftkunde-md.mjs) imports it via type stripping.
//
// Relative imports WITH the .ts extension on purpose (not the house `@/`
// alias): plain Node knows neither the alias nor extensionless resolution;
// `allowImportingTsExtensions` covers this, and Vite/Vitest resolve it too.
// Erasable syntax only (no enums/namespaces/parameter properties) — Node's
// type stripping rejects anything else.
import { seo } from '../../locales/de/seo.ts';
import { schriftkunde } from '../../locales/de/schriftkunde.ts';
import { TRY_TARGETS } from '../../sections/schriftkunde/tryTargets.ts';

const ORIGIN = 'https://kurrentschrift.ink';
const t = schriftkunde;

type SourceRef = { readonly label: string; readonly href: string };
type TermItem = { readonly term: string; readonly desc: string };

// Locale leaves that are deliberately NOT mirrored — the completeness test
// walks every string leaf and consults this list. Keep each entry justified:
//  - the two fallback strings describe an ERROR state of the live page (cold
//    engine) that a static file cannot be in;
//  - the ids are technical keys, not prose.
export const SKIP_PATHS: readonly RegExp[] = [
  /^specimen\.suetterlinCaptionFallback$/,
  /^specimen\.suetterlinWordFallback$/,
  /^variants\.\d+\.id$/,
  /^tryCards\.\d+\.id$/,
];

// Minimal Markdown escaping for prose leaves. The current catalogue contains
// none of these characters outside URLs (verified 2026-08-27), so this is
// pure insurance and changes nothing today; URLs are never escaped (they go
// into <…> link destinations verbatim).
export function escapeMarkdown(s: string): string {
  let out = s.replace(/([\\`*_[\]])/g, '\\$1');
  if (/^(#|-|>|\d+\.)/.test(out)) out = '\\' + out;
  return out;
}

// The `stand` date is read from sitemap.xml's <lastmod> for /schriftkunde —
// deterministic (no new Date(), the file must not change on every build) and
// coupled to the already-maintained rule "bump <lastmod> when a page's
// content changes". Exported here so the build script and the drift test
// parse it identically.
export function schriftkundeStandFromSitemap(sitemapXml: string): string {
  const m = sitemapXml.match(
    /<loc>https:\/\/kurrentschrift\.ink\/schriftkunde<\/loc>\s*<lastmod>([0-9-]+)<\/lastmod>/,
  );
  if (!m) {
    throw new Error(
      'sitemap.xml carries no <lastmod> for /schriftkunde — the mirror needs it as its Stand date',
    );
  }
  return m[1];
}

const e = escapeMarkdown;
// Link destinations always in <…>: uniform, and two catalogue hrefs contain
// parentheses (Mark_(1871), Fraktur_(Schrift)) that would end a bare
// destination early.
const link = (s: SourceRef) => `[${e(s.label)}](<${s.href}>)`;
const sourceLine = (sources: readonly SourceRef[]) =>
  `_${e(t.sourcesLabel)} ${sources.map(link).join(' · ')}_`;
const heading2 = (s: string) => `## ${e(s)}`;
const rows = (items: readonly TermItem[]) => items.map((it) => `- **${e(it.term)}** — ${e(it.desc)}`);
const triplet = (items: readonly TermItem[]) => items.flatMap((it) => [`### ${e(it.term)}`, '', e(it.desc), '']);

// The in-band rights note. A raw .md circulates without its robots.txt
// context, so the express ai-train=no reservation (Art. 4 (EU) 2019/790,
// crawler-richtlinie.md) must travel inside the file. Wording derived from
// robots.txt + README ("License") + the Impressum — no new grant is invented,
// deliberately no CC license.
const RIGHTS_NOTE =
  'Text und Zusammenstellung © Markus Neusinger, kurrentschrift.ink. Abruf, Zitat mit ' +
  'Quellenangabe und Verlinkung sind ausdrücklich erwünscht; die Nutzung zum Training von ' +
  'KI-Modellen ist untersagt (ai-train=no — ausdrücklicher Rechtevorbehalt nach Art. 4 der ' +
  'Richtlinie (EU) 2019/790). Der Quellcode des Projekts steht unter MIT-Lizenz; die ' +
  'kuratierten Schriftdaten sind gesondert vorbehalten. Zitierfähige Fassung: ' +
  `${ORIGIN}/schriftkunde`;

export function renderSchriftkundeMarkdown({ stand }: { stand: string }): string {
  const out: string[] = [];
  const push = (...lines: string[]) => out.push(...lines);
  const blank = () => out.push('');

  // --- head block ---
  push(
    '<!-- Generiert aus app/src/locales/de/schriftkunde.ts — nicht von Hand bearbeiten;',
    '     `npm run schriftkunde:md` erzeugt die Datei neu. -->',
    '',
    `# ${e(t.title)}`,
    '',
    `> ${e(seo.schriftkunde.description)}`,
    '',
    `- Bereich: ${e(t.eyebrow)}`,
    `- Kanonische Fassung: ${ORIGIN}/schriftkunde`,
    `- Stand: ${stand}`,
    '- Erzeugt aus: app/src/locales/de/schriftkunde.ts',
    '- Sprache: Deutsch',
    '',
    'Dies ist die Textfassung der Webseite für Clients ohne JavaScript. Die Bilder und die',
    'live geschriebenen Schriftproben der Seite fehlen hier; sie sind je Schrift als',
    'Beschreibung vermerkt.',
    '',
    RIGHTS_NOTE,
    '',
    '---',
    '',
  );

  // --- PageHeader: intro + lead ---
  push(e(t.intro), '', e(t.lead), '');

  // --- Grundbegriffe (TripletGrid) ---
  push(heading2(t.conceptsHeading), '', ...triplet(t.concepts), sourceLine(t.conceptsSources), '');

  // --- Die drei Schriften (variant cards) ---
  push(heading2(t.variantsHeading), '');
  for (const v of t.variants) {
    push(`### ${e(v.name)}`, '', `_${e(v.period)}_`, '');
    // Specimen: never embed an image — one honest description line per card
    // (mirrors SpecimenBlock's three branches; the Koch plate additionally
    // links its public-domain source).
    if (v.id === 'kurrent') {
      push(`_Schriftprobe auf der Webseite: ${e(t.specimen.kurrentCaption)}_`, '');
    } else if (v.id === 'suetterlin') {
      push(
        `_Schriftprobe auf der Webseite: das Wort „${e(t.specimen.suetterlinWord)}“ — ${e(t.specimen.suetterlinCaption)}_`,
        '',
      );
    } else {
      // The plate's public-domain source is already in this card's source
      // list — looked up by host rather than by index, so a reordering of the
      // locale's sources array cannot silently link the wrong reference.
      const commons = v.sources.find((s) => s.href.includes('commons.wikimedia.org'));
      const plate = commons ? ` Gemeinfreie Originaltafel: ${link(commons)}` : '';
      push(
        `_Schriftprobe auf der Webseite: ${e(t.specimen.offenbacherAlt)} — ${e(t.specimen.offenbacherCaption)}.${plate}_`,
        '',
      );
    }
    push(e(v.essence), '');
    for (const f of v.facts) push(`- **${e(f.k)}:** ${e(f.v)}`);
    blank();
    if ('note' in v && v.note) push(`_${e(v.note)}_`, '');
    push(sourceLine(v.sources), '');
  }

  // --- Einordnung & Abgrenzung ---
  push(heading2(t.classifyHeading), '', e(t.classifyLead), '', ...rows(t.classify), '', sourceLine(t.classifySources), '');

  // --- Wo wurde so geschrieben ---
  push(heading2(t.geographyHeading), '', e(t.geographyLead), '', ...rows(t.geography), '', sourceLine(t.geographySources), '');

  // --- Warum wir heute nicht mehr so schreiben ---
  push(heading2(t.endHeading), '');
  for (const p of t.endParagraphs) push(e(p), '');
  push(sourceLine(t.endSources), '');

  // --- Federn & Striche (TripletGrid) ---
  push(heading2(t.federnHeading), '', e(t.federnLead), '', ...triplet(t.federn), sourceLine(t.federnSources), '');

  // --- Tinte & Papier ---
  push(heading2(t.materialHeading), '', e(t.materialLead), '', ...rows(t.material), '', sourceLine(t.materialSources), '');

  // --- Buchstaben-Besonderheiten ---
  push(heading2(t.lettersHeading), '', e(t.lettersLead), '', ...rows(t.letters), '', sourceLine(t.lettersSources), '');

  // --- Einen alten Brief entziffern (method only — no source line, like the
  //     page) + the in-prose Tafel pointer with an ABSOLUTE route (a raw .md
  //     has no base URL to resolve against) ---
  push(heading2(t.decipherHeading), '', e(t.decipherLead), '', ...rows(t.decipher), '');
  push(
    `${e(t.decipherTafel.before)}[${e(t.decipherTafel.linkLabel)}](<${ORIGIN}/tafel>)${e(t.decipherTafel.after)}`,
    '',
  );

  // --- Zahlen & Zeichen ---
  push(heading2(t.signsHeading), '', e(t.signsLead), '', ...rows(t.signs), '', sourceLine(t.signsSources), '');

  // --- Chronologie ---
  push(heading2(t.timelineHeading), '');
  for (const row of t.timeline) push(`- **${e(row.year)}** — ${e(row.text)}`);
  blank();
  push(`_${e(t.timelineNote)}_`, '', sourceLine(t.timelineSources), '');

  // --- Quellen (group headings are <p> on the page, so bold — not headings) ---
  push(heading2(t.sourcesHeading), '', e(t.sourcesIntro), '');
  for (const group of [
    { label: t.sourcesScholarlyHeading, items: t.sourcesScholarly as readonly SourceRef[] },
    { label: t.sourcesWikipediaHeading, items: t.sourcesWikipedia as readonly SourceRef[] },
  ]) {
    push(`**${e(group.label)}**`, '');
    for (const s of group.items) push(`- ${link(s)}`);
    blank();
  }
  push(`_${e(t.sourcesRepo)}_`, '');

  // --- Weiterlernen (the viridian-rule aside becomes a blockquote) ---
  push(heading2(t.recommendation.heading), '');
  push(
    `> ${e(t.recommendation.before)}[${e(t.recommendation.linkLabel)}](<${t.recommendation.href}>)${e(t.recommendation.after)}`,
    '',
  );
  push(e(t.recommendation.practiceIntro), '');
  for (const s of t.recommendation.practiceLinks) push(`- ${link(s)}`);
  blank();

  // --- Jetzt ausprobieren (cards → h3 + absolute route links) ---
  push(heading2(t.tryHeading), '', e(t.tryLead), '');
  for (const card of t.tryCards) {
    push(`### ${e(card.title)}`, '', e(card.body), '', `[${e(card.cta)} →](<${ORIGIN}${TRY_TARGETS[card.id]}>)`, '');
  }

  // exactly one trailing newline
  return out.join('\n').replace(/\n+$/, '') + '\n';
}
