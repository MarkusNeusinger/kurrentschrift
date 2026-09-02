// A very small Chrome DevTools Protocol client, shared by the two design-system
// checks under `app/scripts/` (`type-floor.mjs` for §9 type sizes,
// `touch-targets.mjs` for §9.3 hit areas).
//
// Deliberately no dependency: both checks drive a real browser, and Node 22's
// built-in WebSocket plus the `/json` HTTP endpoints are enough for navigate +
// evaluate. Adding puppeteer/playwright for this would put a browser download
// into every `npm ci` for two scripts nobody runs in CI.
//
// Point CHROME_PATH at a binary if the search below misses.

import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';

const CHROME_CANDIDATES = [
  process.env.CHROME_PATH,
  '/usr/bin/google-chrome',
  '/usr/bin/google-chrome-stable',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
  '/snap/bin/chromium',
];

export class Cdp {
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

  /**
   * Navigate and wait until the SPA has actually mounted — the load event fires
   * long before React puts anything in #root — then let webfonts settle, since
   * a fallback face reports different metrics than the real one.
   */
  async goto(url) {
    await this.send('Page.navigate', { url });
    for (let attempt = 0; attempt < 40; attempt += 1) {
      const ready = await this.evaluate(
        "document.readyState === 'complete' && !!document.querySelector('main, [role=main], h1')",
      );
      if (ready) break;
      await sleep(250);
    }
    await this.evaluate('document.fonts ? document.fonts.ready.then(() => true) : true');
    await sleep(300);
  }
}

export function findChrome() {
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

/** Launch headless Chrome and wait for its debugging port to answer. */
export async function launchChrome(port, { width, height, label = 'ds-check' }) {
  const child = spawn(
    findChrome(),
    [
      '--headless=new',
      `--remote-debugging-port=${port}`,
      `--window-size=${width},${height}`,
      '--no-sandbox',
      '--disable-gpu',
      `--user-data-dir=${join(tmpdir(), `${label}-${port}`)}`,
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

/** Open a fresh tab on a launched browser and return a connected client. */
export async function openPage(port, { width, height }) {
  const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
  const cdp = await Cdp.connect(target.webSocketDebuggerUrl);
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('Emulation.setDeviceMetricsOverride', {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: width < 700,
  });
  return cdp;
}

/** Split `--flag=value` on the FIRST `=` only — a value may contain more. */
export function splitFlag(arg) {
  const eq = arg.indexOf('=');
  return eq === -1 ? [arg, undefined] : [arg.slice(0, eq), arg.slice(eq + 1)];
}
