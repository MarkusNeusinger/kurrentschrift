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
// built-in WebSocket. Point CHROME_PATH at a binary if the search below misses.
//
// Deliberately NOT reported: the 13px `overline` variant (eyebrows, worksheet
// section labels). It is written into the type ladder of design-system.md §3 and
// is therefore sanctioned, not drift — see EXEMPT_CLASSES.

import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';

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

const CHROME_CANDIDATES = [
  process.env.CHROME_PATH,
  '/usr/bin/google-chrome',
  '/usr/bin/google-chrome-stable',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
  '/snap/bin/chromium',
];

// ── arguments ───────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const opts = { base: 'http://localhost:3000', floor: 14, width: 390, height: 844, routes: DEFAULT_ROUTES };
  for (let i = 0; i < argv.length; i += 1) {
    const [flag, inline] = argv[i].split('=');
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

// ── a very small CDP client ─────────────────────────────────────────────────

class Cdp {
  constructor(socket) {
    this.socket = socket;
    this.seq = 0;
    this.pending = new Map();
    socket.addEventListener('message', (event) => {
      const msg = JSON.parse(event.data);
      const waiter = this.pending.get(msg.id);
      if (!waiter) return;
      this.pending.delete(msg.id);
      if (msg.error) waiter.reject(new Error(msg.error.message));
      else waiter.resolve(msg.result);
    });
  }

  static async connect(url) {
    const socket = new WebSocket(url);
    await new Promise((resolve, reject) => {
      socket.addEventListener('open', resolve, { once: true });
      socket.addEventListener('error', () => reject(new Error(`cannot open ${url}`)), { once: true });
    });
    return new Cdp(socket);
  }

  send(method, params = {}) {
    const id = ++this.seq;
    this.socket.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }

  async evaluate(expression) {
    const { result, exceptionDetails } = await this.send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (exceptionDetails) throw new Error(exceptionDetails.text ?? 'evaluation failed');
    return result.value;
  }
}

function findChrome() {
  const found = CHROME_CANDIDATES.find((p) => p && existsSync(p));
  if (!found) {
    throw new Error(
      'no Chrome found — install one or set CHROME_PATH (candidates: ' +
        CHROME_CANDIDATES.filter(Boolean).join(', ') +
        ')',
    );
  }
  return found;
}

async function launch(port, { width, height }) {
  const child = spawn(
    findChrome(),
    [
      '--headless=new',
      `--remote-debugging-port=${port}`,
      `--window-size=${width},${height}`,
      '--no-sandbox',
      '--disable-gpu',
      `--user-data-dir=${join(tmpdir(), `type-floor-${port}`)}`,
      'about:blank',
    ],
    { stdio: 'ignore' },
  );
  // The port is not listening the moment spawn returns; poll the HTTP endpoint.
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (res.ok) return child;
    } catch {
      // not up yet
    }
    await sleep(250);
  }
  child.kill();
  throw new Error('Chrome did not open its debugging port within 15s');
}

// ── run ─────────────────────────────────────────────────────────────────────

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  const port = 9222 + Math.floor(Math.random() * 500);
  const chrome = await launch(port, opts);
  let violations = 0;

  try {
    const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
    const cdp = await Cdp.connect(target.webSocketDebuggerUrl);
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    await cdp.send('Emulation.setDeviceMetricsOverride', {
      width: opts.width,
      height: opts.height,
      deviceScaleFactor: 1,
      mobile: opts.width < 700,
    });

    console.log(`type floor ${opts.floor}px · ${opts.base} · ${opts.width}x${opts.height}\n`);

    for (const route of opts.routes) {
      await cdp.send('Page.navigate', { url: opts.base + route });
      // The SPA mounts after the load event; wait for real content, then let
      // fonts settle (a fallback face can report a different size).
      for (let attempt = 0; attempt < 40; attempt += 1) {
        const ready = await cdp.evaluate(
          "document.readyState === 'complete' && !!document.querySelector('main, [role=main], h1')",
        );
        if (ready) break;
        await sleep(250);
      }
      await cdp.evaluate('document.fonts ? document.fonts.ready.then(() => true) : true');
      await sleep(300);

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
