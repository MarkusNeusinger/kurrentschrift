#!/usr/bin/env node
// touch-targets — the standing check under design-system.md §9.3 (binding since
// 2026-09-03): an interactive target measures at least 44px in its smaller edge.
//
// It sweeps EVERY interactive element on every public route. An earlier version
// checked a hand-kept inventory of the controls wearing `hitArea()`, which was
// the wrong shape: a list can pass while the rule is broken somewhere it does
// not name, and it did.
//
// The rule has exactly ONE exception — a link in RUNNING PROSE — and the sweep
// draws it from two signals together, because neither alone is enough:
//   · the link is underlined (the theme gives every `MuiLink`
//     `underline: 'always'`; chrome that only looks like a link opts out with
//     `textDecoration: none`), AND
//   · it does not sit in a `<nav>`. The Schriftkunde jump list is underlined
//     too, but it is navigation, not prose, and it must meet the floor.
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
// Invisible does not mean uninteractive: MUI's Switch and Checkbox put a native
// `opacity: 0` input over the drawn control, and that input IS the target. They
// are measured like everything else and `elementFromPoint` decides.
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

// Routes whose controls change with the screen's state get several PHASES, and
// every phase is swept. The quiz is the reason: its setup chips vanish the
// moment the round starts, and its results screen is three states further on —
// sweeping only the middle state would leave two whole control sets unmeasured
// while the run still claimed to have covered the site.
// Every phase declares `ready`: the state it is supposed to measure, as a
// predicate. `goto()` only waits for <main> to mount, and a phase's own action
// may take a while to have an effect, so sweeping after a fixed delay would let
// a slow API leave the screen empty while the run still reported it measured —
// the exact "claims coverage it does not have" failure this file exists to
// prevent. A phase whose `ready` never comes true fails the run.
const PHASES = {
  '/quiz': [
    {
      name: 'Einrichtung',
      // Wait for the start button WITHOUT clicking it: its presence is what
      // says the word bank arrived and the setup chips are on screen.
      ready: "[...document.querySelectorAll('button')].some((b) => /Quiz starten/.test(b.innerText))",
    },
    {
      name: 'Runde',
      action:
        "(() => { const b = [...document.querySelectorAll('button')].find((x) => /Quiz starten/.test(x.innerText)); if (!b) return false; b.click(); return true; })()",
      // The play panel is up once its „beenden" affordance exists.
      ready: "[...document.querySelectorAll('button')].some((b) => b.innerText.trim() === 'beenden')",
    },
    {
      name: 'Auswertung',
      // One attempt only: the action below already loops inside the page for as
      // long as a round takes. Retrying it from out here would multiply a
      // 40-second play-out by the retry budget and look like a hang.
      attempts: 1,
      // Results are only worth measuring once they carry the pills — an empty
      // evaluation would sweep a screen without the targets this round is for.
      ready: "[...document.querySelectorAll('button')].some((b) => /Einstellungen ändern/.test(b.innerText)) && /verwechselt|Mühe/.test(document.body.innerText)",
      // A round has no fixed length — it runs until „beenden", and `finish()`
      // only shows results once at least one question has been seen. So:
      // answer, then quit. (Playing to an end that does not exist was the
      // earlier version's mistake; it timed out and skipped the screen.)
      //
      // It must answer WRONGLY at least once. The answer grid is shuffled, so
      // picking the first button is a coin toss, and a CORRECT pick
      // auto-advances after 650ms — quitting then leaves `misses`/`confusions`
      // empty and the results screen renders without the very pills this round
      // is here to measure. So: keep answering until a wrong pick registers
      // (the grid marks it with ✕), and only then quit.
      action: `(async () => {
        const nap = (ms) => new Promise((r) => setTimeout(r, ms));
        const byText = (re) => [...document.querySelectorAll('button')].find((b) => re.test(b.innerText));
        const missMarked = () => [...document.querySelectorAll('main button')].some((b) => b.innerText.includes('✕'));
        if (byText(/Einstellungen ändern/)) return true;

        let missed = false;
        for (let question = 0; question < 12 && !missed; question += 1) {
          const answer = [...document.querySelectorAll('main button')].find(
            (b) => !b.disabled && b.innerText.trim().length > 0 && b.innerText.trim().length <= 12 && !/beenden|Weiter/.test(b.innerText),
          );
          if (!answer) { await nap(400); continue; }
          answer.click();
          await nap(900);
          if (missMarked()) { missed = true; break; }
          // Right answer: the panel has already auto-advanced to the next one.
        }
        if (!missed) return false;

        const quit = byText(/^beenden$/);
        if (!quit) return false;
        quit.click();
        await nap(900);
        // Results are only useful to this sweep if they actually carry pills.
        return !!byText(/Einstellungen ändern/) && /verwechselt|Mühe/.test(document.body.innerText);
      })()`,
    },
  ],
};

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

// The one KNOWN shortfall, named rather than silently skipped: the Schreibtafel
// renders the alphabet as SVG cells that tile their row edge to edge (measured
// at 390px: 41–98px wide, gaps of 0). They are 73px tall, so they clear WCAG 2.2
// SC 2.5.8 comfortably, but the narrowest are ~41px wide. Neither remedy is
// free — an invisible overlay would reach into the neighbouring letter and steal
// its tap, and widening the cells reflows the reference grid the page exists to
// show. That is an author's call on the tafel's layout, not a fix to make in
// passing, so it is listed here where it stays visible. See §9.3 „Offen".
const KNOWN_SHORTFALL = {
  // Narrow on purpose, on two axes at once.
  //
  // WHICH elements: matched by the cell's own `rect.cellbg` background, not by
  // "is an SVG group" — a future undersized SVG control must FAIL rather than
  // inherit this exception. Must evaluate to a BOOLEAN; returning the element
  // would put a React fiber in the result and break serialisation.
  //
  // WHICH shortfall: only the documented one. What §9.3 excuses is the narrow
  // WIDTH of a cell that is otherwise generous — 73px tall and well past the
  // 24px WCAG 2.2 SC 2.5.8 baseline. A cell that lost its height, or shrank
  // under that baseline, is a new defect and must fail; otherwise this flag
  // would quietly cover regressions the author never agreed to.
  match: "el.tagName.toLowerCase() === 'g' && !!el.querySelector(':scope > rect.cellbg')",
  envelope: (floor) => `r.height >= ${floor} && r.width >= 24`,
  why: 'Schreibtafel-Zellen: schmale Breite bei voller Höhe — Autor-Entscheid offen',
};

const SWEEP = (floor) => `(() => {
  const SEL = 'a[href], button, [role=button], [role=tab], [role=switch], input, select, textarea, [tabindex]:not([tabindex="-1"])';
  const reach = ${floor} / 2 - 0.01;
  const rows = [];
  const seen = new Set();
  for (const raw of document.querySelectorAll(SEL)) {
    if (raw.disabled) continue;
    const cs = getComputedStyle(raw);
    // NOTE: no opacity test. MUI's Switch/Checkbox lay a transparent native
    // input over the drawn control and that input is the real target; skipping
    // it would let the sweep claim coverage it does not have. Whether an
    // invisible element can actually be hit is exactly what the probe answers.
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;

    // §9.2's exception, read off the page: a link in running prose is
    // underlined AND outside <nav>. The jump list is underlined but is
    // navigation, so it is measured.
    if (raw.tagName.toLowerCase() === 'a' && cs.textDecorationLine.includes('underline') && !raw.closest('nav')) continue;

    // A control wrapped in a <label> is activated by tapping ANYWHERE on the
    // label, so the label is the honest target — this is what makes MUI's
    // transparent Switch/Checkbox input measurable at all.
    const el = raw.closest('label') ?? raw;
    // A label may hold several listed controls; measure it once.
    if (seen.has(el)) continue;
    seen.add(el);

    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;

    // The exception applies only to elements it names AND only within the
    // geometry §9.3 actually excuses (see KNOWN_SHORTFALL.envelope).
    const known = (${KNOWN_SHORTFALL.match}) && (${KNOWN_SHORTFALL.envelope(floor)});
    const label = (el.innerText || el.getAttribute('aria-label') || el.tagName).trim().slice(0, 30).replace(/\\s+/g, ' ');
    const drawn = [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10];
    if (Math.min(r.width, r.height) >= ${floor}) { rows.push({ label, drawn, ok: true, known }); continue; }

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
    rows.push({ label, drawn, ok: probes.every((p) => p[1]), known, missed: probes.filter((p) => !p[1]).map((p) => p[0]) });
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
  const unreachable = [];

  try {
    const cdp = await openPage(port, opts);
    console.log(`touch targets ${TOUCH_TARGET}px · ${opts.base} · ${opts.width}x${opts.height}\n`);

    for (const route of opts.routes) {
      await cdp.goto(opts.base + route);
      const phases = PHASES[route] ?? [{ name: '' }];

      for (const phase of phases) {
        if (phase.action) {
          let done = false;
          const attempts = phase.attempts ?? 24;
          for (let attempt = 0; !done && attempt < attempts; attempt += 1) {
            done = await cdp.evaluate(phase.action);
            if (!done && attempt + 1 < attempts) await sleep(500);
          }
          if (!done) {
            // A declared phase that cannot be reached is a FAILED run, not a
            // skipped one: silently passing here is exactly how the sweep used
            // to claim full coverage while a whole screen went unmeasured.
            unreachable.push(`${route} · ${phase.name}`);
            console.log(`  FAIL  ${route} · ${phase.name} — Zustand nicht erreicht, NICHT gemessen`);
            continue;
          }
        }

        // Wait for the state ITSELF, not for a fixed delay: `goto()` returns as
        // soon as <main> exists, and a slow API can leave the screen's controls
        // absent long past any sleep we would pick.
        if (phase.ready) {
          let up = false;
          for (let attempt = 0; !up && attempt < 40; attempt += 1) {
            up = await cdp.evaluate(phase.ready);
            if (!up) await sleep(500);
          }
          if (!up) {
            unreachable.push(`${route} · ${phase.name}`);
            console.log(`  FAIL  ${route} · ${phase.name} — Zustand nicht bereit, NICHT gemessen`);
            continue;
          }
        }
        // Engine-written surfaces (replay buttons, tafel cells) arrive late and
        // have no single readiness marker; this settles them.
        await sleep(1200);

        const rows = JSON.parse(await cdp.evaluate(SWEEP(TOUCH_TARGET)));
        const bad = rows.filter((r) => !r.ok && !r.known);
        const shortfall = rows.filter((r) => !r.ok && r.known);
        checked += rows.length;
        known += shortfall.length;

        const where = phase.name ? `${route} · ${phase.name}` : route;
        const note = shortfall.length ? ` (+${shortfall.length} bekannt)` : '';
        if (bad.length === 0) {
          console.log(`  ok    ${where.padEnd(30)} ${rows.length} Ziele${note}`);
          continue;
        }
        console.log(`  FAIL  ${where.padEnd(30)} ${rows.length} Ziele${note}`);
        for (const r of bad) {
          failures.push({ route: where, ...r });
          console.log(`          ${r.drawn[0]}×${r.drawn[1]} — „${r.label}" verfehlt: ${r.missed.join('/')}`);
        }
      }
    }
  } finally {
    chrome.kill();
  }

  console.log(`\n${checked} interaktive Ziele geprüft (Fließtext-Links nach §9.2 ausgenommen).`);
  if (known) console.log(`${known} benannte Ausnahme(n) darunter: ${KNOWN_SHORTFALL.why}`);
  if (unreachable.length) {
    console.log(`${unreachable.length} deklarierte(r) Zustand/Zustände nicht erreicht: ${unreachable.join(', ')}`);
  }
  // Never claim "all reach the floor" while a known shortfall was just counted —
  // the two lines together would contradict each other.
  const allGood = failures.length === 0 && known === 0 && unreachable.length === 0;
  console.log(
    allGood
      ? `Alle erreichen den ${TOUCH_TARGET}px-Boden.`
      : failures.length === 0 && unreachable.length === 0
        ? `Alle ÜBRIGEN erreichen den ${TOUCH_TARGET}px-Boden.`
        : `${failures.length} unter dem ${TOUCH_TARGET}px-Boden — design-system.md §9.3.`,
  );
  process.exitCode = failures.length === 0 && unreachable.length === 0 ? 0 : 1;
}

main().catch((error) => {
  console.error(String(error?.message ?? error));
  process.exitCode = 2;
});
