#!/usr/bin/env node
// type-floor — the standing grid under design-system.md §9 ("Untergrenzen:
// Body >= 19px, Caption >= 14px").
//
// The audit of 2026-09-02 found three places below that floor (12.16px specimen
// captions, 13.6px landing status marks, 13px MUI-small chips and buttons). Each
// was a one-line drift that nobody could see without measuring, which is why the
// fix ships with this script rather than alone: it walks every public route in a
// real browser, reads the COMPUTED font size of every element that renders text
// of its own, and fails when one is under the floor. Run it after any type or
// theme change; `/verify-frontend` names it as its mobile step.
//
//   node scripts/type-floor.mjs                        # localhost:3000, 390px
//   node scripts/type-floor.mjs --base https://kurrentschrift.ink
//   node scripts/type-floor.mjs --width 1280 --floor 14
//
// No new dependency: it drives Chrome over the DevTools Protocol using Node 22's
// built-in WebSocket (`browser.mjs`, shared with `touch-targets.mjs`).
// Point CHROME_PATH at a binary if its search misses.
//
// Deliberately NOT reported: the 13px `overline` variant (eyebrows, worksheet
// section labels). It is written into the type ladder of design-system.md §3 and
// is therefore sanctioned, not drift — see EXEMPT_CLASSES.

import { launchChrome, openPage, splitFlag } from './browser.mjs';

const DEFAULT_ROUTES = [
  '/',
  '/schriftkunde',
  '/lesen',
  '/lesen/vergleichen',
  '/quiz',
  '/tafel',
  '/schreiben',
  '/schreiben/uebungsblatt',
  '/federprobe',
  '/impressum',
  '/gibt-es-nicht-404',
];

// ── arguments ───────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const opts = { base: 'http://localhost:3000', floor: 14, width: 390, height: 844, routes: DEFAULT_ROUTES };
  for (let i = 0; i < argv.length; i += 1) {
    const [flag, inline] = splitFlag(argv[i]);
    const value = inline ?? argv[++i];
    switch (flag) {
      case '--base':
        opts.base = value.replace(/\/+$/, '');
        break;
      case '--floor':
        opts.floor = Number(value);
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

// ── the measurement, evaluated inside the page ──────────────────────────────
// One entry per element that renders text of its own (a direct, non-blank text
// child) and computes to less than `floor` px. Elements are deduplicated by
// selector + size so a list of twelve identical chips reports as one row with a
// count, not twelve rows.

const MEASURE = (floor) => `(() => {
  // Sanctioned by the type ladder (design-system.md §3), not drift.
  const EXEMPT_CLASSES = ['MuiTypography-overline'];
  const rows = new Map();
  for (const el of document.querySelectorAll('body *')) {
    if (el.closest('svg')) continue;
    if (EXEMPT_CLASSES.some((c) => el.classList.contains(c))) continue;
    const ownText = Array.from(el.childNodes)
      .filter((n) => n.nodeType === Node.TEXT_NODE)
      .map((n) => n.textContent.trim())
      .join('');
    if (!ownText) continue;
    const style = getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none') continue;
    const px = parseFloat(style.fontSize);
    if (!(px < ${floor})) continue;
    const key = el.tagName.toLowerCase() + '|' + (el.className || '') + '|' + px;
    const row = rows.get(key);
    if (row) { row.count += 1; continue; }
    rows.set(key, {
      px: Math.round(px * 100) / 100,
      tag: el.tagName.toLowerCase(),
      cls: String(el.className || '').split(' ').filter(Boolean).slice(0, 3).join(' '),
      sample: ownText.slice(0, 48),
      count: 1,
    });
  }
  return Array.from(rows.values()).sort((a, b) => a.px - b.px);
})()`;

// ── run ─────────────────────────────────────────────────────────────────────

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  const port = 9222 + Math.floor(Math.random() * 500);
  const chrome = await launchChrome(port, { ...opts, label: 'type-floor' });
  let violations = 0;

  try {
    const cdp = await openPage(port, opts);

    console.log(`type floor ${opts.floor}px · ${opts.base} · ${opts.width}x${opts.height}\n`);

    for (const route of opts.routes) {
      await cdp.goto(opts.base + route);

      const rows = await cdp.evaluate(MEASURE(opts.floor));
      if (rows.length === 0) {
        console.log(`  ok    ${route}`);
        continue;
      }
      violations += rows.length;
      console.log(`  FAIL  ${route}`);
      for (const row of rows) {
        const times = row.count > 1 ? ` ×${row.count}` : '';
        console.log(`          ${String(row.px).padStart(6)}px  ${row.tag}${times}  ${row.cls}`);
        console.log(`                  „${row.sample}"`);
      }
    }
  } finally {
    chrome.kill();
  }

  console.log(
    violations === 0
      ? `\nAll routes clear of the ${opts.floor}px floor.`
      : `\n${violations} place(s) under the ${opts.floor}px floor — design-system.md §9.`,
  );
  process.exitCode = violations === 0 ? 0 : 1;
}

main().catch((error) => {
  console.error(String(error?.message ?? error));
  process.exitCode = 2;
});
