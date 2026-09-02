#!/usr/bin/env node
// touch-targets — the standing check under design-system.md §9.3 (binding since
// 2026-09-03): an interactive target measures at least 44px in its smaller edge.
//
// It sweeps EVERY interactive element on every public route. An earlier version
// checked a hand-kept inventory of the controls that wear `hitArea()`, which was
// the wrong shape: a list can pass while the rule is broken somewhere it does
// not name, and it did — the Lesart example chips and the Tafel step buttons
// were both under the floor while the check reported the site clear. A rule that
// is only enforced where someone remembered to look is not enforced.
//
// The rule has exactly ONE exception, and the sweep encodes it the way §9.2
// makes it recognisable: a link in running prose is underlined (the theme gives
// every `MuiLink` `underline: 'always'`), while chrome that only looks like a
// link — the header areas, the footer row — opts out with `textDecoration:
// none`. So: an <a> that is underlined is prose and is skipped. Everything else
// must reach the floor. On the public routes that exempts 84 source links and
// leaves 26 real controls.
//
// The probe is the real hit area, not a computed size: for each axis where the
// element is drawn under 44px it asks `document.elementFromPoint` at the
// inclusive edge of the 44px square — 22px from the centre, less a hundredth of
// a pixel so the probe sits inside rather than on the exclusive boundary — and
// requires the element itself to answer. That catches the one way this rule
// breaks silently: an `overflow: hidden` clips the `hitArea()` pseudo-element,
// the drawing is unchanged, and the target shrinks back. A computed-size check
// would sail past it. Axes where the box already exceeds 44px are not probed —
// there nothing is load-bearing, and a neighbour may legitimately win the point.
//
//   node scripts/touch-targets.mjs                        # localhost:3000, 390px
//   node scripts/touch-targets.mjs --base https://kurrentschrift.ink
//
// Needs a reachable API: half these controls only exist once the engine has
// written something. Like `type-floor.mjs` this is a local check, not a CI gate.

import { setTimeout as sleep } from 'node:timers/promises';

import { launchChrome, openPage, splitFlag } from './browser.mjs';

/** The binding floor in CSS px (design-system.md §9.3). */
const TOUCH_TARGET = 44;

const DEFAULT_ROUTES = [
  '/',
  '/schriftkunde',
  '/lesen',
  '/lesen/vergleichen',
  '/quiz',
  '/tafel',
  '/tafel?g=n',
  '/schreiben',
  '/schreiben/uebungsblatt',
  '/federprobe',
  '/impressum',
  '/gibt-es-nicht-404',
];

// Routes that hide controls behind a first interaction. Kept tiny on purpose —
// every entry here is a control the sweep would otherwise never see.
const SETUP = {
  '/quiz':
    "(() => { const b = [...document.querySelectorAll('button')].find((x) => /Quiz starten/.test(x.innerText)); if (!b) return false; b.click(); return true; })()",
};

// The one KNOWN shortfall, named rather than silently skipped: the Schreibtafel
// renders the alphabet as SVG cells that tile their row edge to edge (measured
// at 390px: 41–98px wide, gaps of 0). They are 73px tall, so they clear WCAG 2.2
// SC 2.5.8 comfortably, but the narrowest are ~41px wide. Neither remedy is
// free — an invisible overlay would reach into the neighbouring letter and steal
// its tap, and widening the cells reflows the reference grid the page exists to
// show. That is an author's call on the tafel's layout, not a fix to make in
// passing, so it is listed here where it stays visible instead of quietly
// passing. See design-system.md §9.3 „Offen".
const KNOWN_SHORTFALL = {
  // Must evaluate to a BOOLEAN: `a && el.closest(...)` would put a DOM node in
  // the result and the row could not be serialised out of the page.
  match: "el.tagName.toLowerCase() === 'g' && !!el.closest('svg')",
  why: 'Schreibtafel-Zellen (SVG, kacheln lückenlos) — Autor-Entscheid offen',
};

const SWEEP = (floor) => `(() => {
  const SEL = 'a[href], button, [role=button], [role=tab], [role=switch], input, select, textarea, [tabindex]:not([tabindex="-1"])';
  const reach = ${floor} / 2 - 0.01;
  const rows = [];
  for (const el of document.querySelectorAll(SEL)) {
    if (el.disabled) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || cs.opacity === '0') continue;

    // §9.2's exception, read off the page: running-prose links are underlined,
    // chrome links set textDecoration: none.
    if (el.tagName.toLowerCase() === 'a' && cs.textDecorationLine.includes('underline')) continue;

    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;

    const known = ${KNOWN_SHORTFALL.match};
    const label = (el.innerText || el.getAttribute('aria-label') || el.tagName).trim().slice(0, 30).replace(/\\s+/g, ' ');
    const drawn = [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10];
    if (Math.min(r.width, r.height) >= ${floor}) { rows.push({ label, drawn, ok: true, wide: true, known }); continue; }

    el.scrollIntoView({ block: 'center', inline: 'center', behavior: 'instant' });
    const b = el.getBoundingClientRect();
    const cx = b.left + b.width / 2, cy = b.top + b.height / 2;
    const hit = (x, y) => {
      const at = document.elementFromPoint(x, y);
      return !!at && (at === el || el.contains(at));
    };
    const probes = [];
    if (b.height < ${floor}) probes.push(['oben', hit(cx, cy - reach)], ['unten', hit(cx, cy + reach)]);
    if (b.width < ${floor}) probes.push(['links', hit(cx - reach, cy)], ['rechts', hit(cx + reach, cy)]);
    rows.push({ label, drawn, ok: probes.every((p) => p[1]), wide: false, known, missed: probes.filter((p) => !p[1]).map((p) => p[0]) });
  }
  // Serialised here rather than handed back as an object: the Schreibtafel puts
  // 60+ rows in this array, and CDP's returnByValue gives up on a graph that
  // size with "Object reference chain is too long".
  return JSON.stringify(rows);
})()`;

function parseArgs(argv) {
  const opts = { base: 'http://localhost:3000', width: 390, height: 844, routes: DEFAULT_ROUTES };
  for (let i = 0; i < argv.length; i += 1) {
    const [flag, inline] = splitFlag(argv[i]);
    const value = inline ?? argv[++i];
    switch (flag) {
      case '--base':
        opts.base = value.replace(/\/+$/, '');
        break;
      case '--width':
        opts.width = Number(value);
        break;
      case '--height':
        opts.height = Number(value);
        break;
      case '--routes':
        opts.routes = value.split(',');
        break;
      default:
        throw new Error(`unknown argument: ${flag}`);
    }
  }
  return opts;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  const port = 9722 + Math.floor(Math.random() * 200);
  const chrome = await launchChrome(port, { ...opts, label: 'touch-targets' });
  let checked = 0;
  let known = 0;
  const failures = [];

  try {
    const cdp = await openPage(port, opts);
    console.log(`touch targets ${TOUCH_TARGET}px · ${opts.base} · ${opts.width}x${opts.height}\n`);

    for (const route of opts.routes) {
      await cdp.goto(opts.base + route);
      if (SETUP[route]) {
        for (let attempt = 0; attempt < 24; attempt += 1) {
          if (await cdp.evaluate(SETUP[route])) break;
          await sleep(500);
        }
        await sleep(1500);
      }
      // Engine-written surfaces (replay buttons, tafel cells) arrive late.
      await sleep(1200);

      const rows = JSON.parse(await cdp.evaluate(SWEEP(TOUCH_TARGET)));
      const bad = rows.filter((r) => !r.ok && !r.known);
      const shortfall = rows.filter((r) => !r.ok && r.known);
      checked += rows.length;
      known += shortfall.length;
      const note = shortfall.length ? ` (+${shortfall.length} bekannt)` : '';
      if (bad.length === 0) {
        console.log(`  ok    ${route.padEnd(26)} ${rows.length} Ziele${note}`);
        continue;
      }
      console.log(`  FAIL  ${route.padEnd(26)} ${rows.length} Ziele${note}`);
      for (const r of bad) {
        failures.push({ route, ...r });
        console.log(`          ${r.drawn[0]}×${r.drawn[1]} — „${r.label}" verfehlt: ${r.missed.join('/')}`);
      }
    }
  } finally {
    chrome.kill();
  }

  console.log(`\n${checked} interaktive Ziele geprüft (Fließtext-Links nach §9.2 ausgenommen).`);
  if (known) console.log(`${known} bekannte Unterschreitung(en): ${KNOWN_SHORTFALL.why}`);
  console.log(
    failures.length === 0
      ? `Alle erreichen den ${TOUCH_TARGET}px-Boden.`
      : `${failures.length} unter dem ${TOUCH_TARGET}px-Boden — design-system.md §9.3.`,
  );
  process.exitCode = failures.length === 0 ? 0 : 1;
}

main().catch((error) => {
  console.error(String(error?.message ?? error));
  process.exitCode = 2;
});
