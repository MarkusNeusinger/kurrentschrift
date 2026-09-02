#!/usr/bin/env node
// touch-targets — the standing check under design-system.md §9.3 (binding since
// 2026-09-03): an interactive target measures at least 44px in its smaller edge.
//
// It does NOT sweep every control on the site — the rule has exactly one
// exception, links in running prose, and a sweep would report every one of them
// forever. What it checks instead are the controls where the 44px is not
// obvious from the drawing and can therefore regress unnoticed:
//
//   · those that get their 44px from the invisible `hitArea()` pseudo-element
//     (app/src/styles/hitArea.ts) — remove the helper, or wrap the control in
//     something with `overflow: hidden`, and the drawing is unchanged while the
//     target quietly shrinks back;
//   · the header area links, which reach the floor through padding instead
//     (HeaderBar.tsx) — on phones the bar stacks into two rows, and an
//     invisible overlay there would have made the rows' targets overlap.
//
// Nothing on screen tells you when either of those breaks; this does.
//
// The probe is the real thing, not a computed size: for each axis where the
// element's own box is under 44px, it asks `document.elementFromPoint` at the
// inclusive edge of the 44px square — 22px from the centre, minus a hundredth
// of a pixel so the probe sits inside rather than on the exclusive boundary —
// and requires the answer to be the control itself. A clipped pseudo-element
// fails that; a computed-height check would not. Axes where the box already
// exceeds 44px are not probed: there the padding or the helper does nothing, and
// a neighbour's own target may legitimately win the point.
//
//   node scripts/touch-targets.mjs                        # localhost:3000, 390px
//   node scripts/touch-targets.mjs --base https://kurrentschrift.ink
//
// Needs a reachable API: the replay button only exists once a word has been
// written. Like `type-floor.mjs` this is a local check, not a CI gate.

import { setTimeout as sleep } from 'node:timers/promises';

import { launchChrome, openPage, splitFlag } from './browser.mjs';

/** The binding floor in CSS px (design-system.md §9.3). */
const TOUCH_TARGET = 44;

// Each target names an element by a browser-side expression. `wait` marks the
// ones that only appear once the engine has written something, so a slow API
// reads as "still coming" rather than as a failure.
//
// Not listed, deliberately: the quiz results screen's „Einstellungen ändern".
// It is the same `QuietButton` primitive as „beenden" below, and reaching it
// costs a full quiz round — the primitive is covered, the detour is not worth
// the runtime.
const CHECKS = [
  {
    // The area links are on every page; checking them once is enough. At this
    // width the bar stacks into two rows, which is the layout where they used
    // to fall short — and where an invisible overlay would have overlapped.
    route: '/lesen',
    targets: [
      { name: 'Kopf-Navigation (Schriftkunde)', find: "document.querySelector('header nav a')" },
      { name: 'Kopf-Navigation (Lesen)', find: "document.querySelectorAll('header nav a')[1]" },
    ],
  },
  {
    route: '/federprobe',
    targets: [
      { name: 'Beispiel-Chip (Federprobe)', find: "document.querySelector('.MuiChip-root')" },
      {
        name: '„Link kopieren"',
        find: "[...document.querySelectorAll('button')].find((b) => /Link kopieren/.test(b.innerText))",
      },
      { name: 'ReplayButton ↻', find: `document.querySelector('[aria-label="noch einmal schreiben"]')`, wait: true },
    ],
  },
  {
    route: '/schreiben/uebungsblatt',
    targets: [
      { name: 'InfoHint (i)', find: "document.querySelector('button[aria-haspopup=\"dialog\"]')" },
      {
        name: 'Umschaltgruppe (Ausgangsschrift)',
        find: "document.querySelector('.MuiToggleButtonGroup-root .MuiToggleButton-root')",
      },
    ],
  },
  {
    route: '/tafel?g=n',
    targets: [
      { name: '„Detail schließen"', find: `document.querySelector('[aria-label="Detail schließen"]')`, wait: true },
    ],
  },
  {
    route: '/quiz',
    // The quiz opens on its setup panel; „beenden" only exists in play.
    // Returns false until the button exists — the panel only renders once the
    // word bank has arrived, so a single click would race the API.
    setup: "(() => { const b = [...document.querySelectorAll('button')].find((x) => /Quiz starten/.test(x.innerText)); if (!b) return false; b.click(); return true; })()",
    targets: [{ name: '„beenden" (QuietButton)', find: "[...document.querySelectorAll('button')].find((b) => b.innerText.trim() === 'beenden')", wait: true }],
  },
];

// Runs in the page. Returns null while a `wait` target has not appeared yet.
//
// `elementFromPoint` works in VIEWPORT coordinates and answers null for
// anything outside it, so the element is centred first — otherwise a control
// below the fold reports "hit nothing" and looks like a violation it is not.
const PROBE = (find, floor) => `(() => {
  const el = ${find};
  if (!el) return null;
  el.scrollIntoView({ block: 'center', inline: 'center', behavior: 'instant' });
  const r = el.getBoundingClientRect();
  if (!r.width || !r.height) return null;
  const cx = r.left + r.width / 2;
  const cy = r.top + r.height / 2;
  // The 44px square is checked INCLUSIVELY: the probe sits a hair inside its
  // edge, not half a pixel in. A CSS pixel boundary is exclusive, so testing
  // exactly at centre+22 lands on the parent about half the time and would
  // report violations that are none; backing off by a whole 0.5px would have
  // been the opposite error — it passes a 43px target as if it were 44.
  const reach = ${floor} / 2 - 0.01;
  const hits = (x, y) => {
    const at = document.elementFromPoint(x, y);
    return { ok: !!at && (at === el || el.contains(at)), got: at ? at.tagName.toLowerCase() + (at.className && typeof at.className === 'string' ? '.' + at.className.split(' ')[0] : '') : 'nothing' };
  };
  const probes = [];
  // Only the axes where the drawn box falls short — that is where the invisible
  // hit area is load-bearing and can regress.
  if (r.height < ${floor}) {
    probes.push({ dir: 'oben', ...hits(cx, cy - reach) });
    probes.push({ dir: 'unten', ...hits(cx, cy + reach) });
  }
  if (r.width < ${floor}) {
    probes.push({ dir: 'links', ...hits(cx - reach, cy) });
    probes.push({ dir: 'rechts', ...hits(cx + reach, cy) });
  }
  return {
    box: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
    probes,
    ok: probes.every((p) => p.ok),
  };
})()`;

function parseArgs(argv) {
  const opts = { base: 'http://localhost:3000', width: 390, height: 844 };
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
  let failures = 0;
  let missing = 0;

  try {
    const cdp = await openPage(port, opts);
    console.log(`touch targets ${TOUCH_TARGET}px · ${opts.base} · ${opts.width}x${opts.height}\n`);

    for (const check of CHECKS) {
      await cdp.goto(opts.base + check.route);
      if (check.setup) {
        let done = false;
        for (let attempt = 0; !done && attempt < 24; attempt += 1) {
          done = await cdp.evaluate(check.setup);
          if (!done) await sleep(500);
        }
        await sleep(1200);
      }
      console.log(`  ${check.route}`);

      for (const target of check.targets) {
        let probe = await cdp.evaluate(PROBE(target.find, TOUCH_TARGET));
        // Engine-written surfaces need a moment; poll rather than guess a delay.
        for (let attempt = 0; target.wait && !probe && attempt < 24; attempt += 1) {
          await sleep(500);
          probe = await cdp.evaluate(PROBE(target.find, TOUCH_TARGET));
        }
        if (!probe) {
          missing += 1;
          console.log(`     ??  ${target.name} — not found (API asleep? selector stale?)`);
          continue;
        }
        const [w, h] = probe.box;
        if (probe.probes.length === 0) {
          console.log(`     ok  ${target.name} — ${w}×${h}, box already ≥ ${TOUCH_TARGET}px`);
          continue;
        }
        if (probe.ok) {
          console.log(`     ok  ${target.name} — ${w}×${h} drawn, ${TOUCH_TARGET}px reached (${probe.probes.map((p) => p.dir).join('/')})`);
          continue;
        }
        failures += 1;
        console.log(`   FAIL  ${target.name} — ${w}×${h} drawn, hit area does not reach ${TOUCH_TARGET}px`);
        for (const p of probe.probes.filter((x) => !x.ok)) {
          console.log(`           ${p.dir}: traf ${p.got}`);
        }
      }
    }
  } finally {
    chrome.kill();
  }

  if (missing) {
    console.log(`\n${missing} target(s) not found — check the site is up with a reachable API.`);
  }
  console.log(
    failures === 0
      ? `\nAll checked controls reach the ${TOUCH_TARGET}px floor.`
      : `\n${failures} control(s) under the ${TOUCH_TARGET}px floor — design-system.md §9.3.`,
  );
  process.exitCode = failures === 0 && missing === 0 ? 0 : 1;
}

main().catch((error) => {
  console.error(String(error?.message ?? error));
  process.exitCode = 2;
});
