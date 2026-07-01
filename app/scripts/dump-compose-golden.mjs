// Golden-fixture generator for the TS→Python composer port: runs the SPA's
// shaping + composeWord on real glyph payloads (fetched once from the local
// API, then FROZEN into the fixture) and records the composed output per word.
// tests/test_compose_golden.py pins core/shaping.py + core/compose.py against
// this file — regenerate ONLY deliberately (a re-run against a changed DB
// changes the inputs, not the contract):
//
//   1. uv run uvicorn api.main:app --port 8000   (local API)
//   2. node app/scripts/dump-compose-golden.mjs
//
// Loads app/src/domain/{shaping,compose}.ts through vite's SSR module loader
// (resolves the `@` alias, no separate bundler), mirrors WrittenWord's
// ligature-decompose fallback, and writes tests/fixtures/compose_golden.json.

import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';
import { createServer } from 'vite';

const APP = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const REPO = resolve(APP, '..');
const API = process.env.API_BASE ?? 'http://localhost:8000';
const SOURCE_ID = 'suetterlin-1922';

// Coverage set: §9 anchors + repeats (lesen/das/denen/dann), diacritics + a
// real ligature template (üben, Glück/ck), a decompose fallback (sitzen/tz),
// a missing capital (Schule/S), midband exits (wovon), capital + descenders
// (Morgen), and one inter-word space.
const WORDS = ['lesen', 'das', 'denen', 'dann', 'üben', 'sitzen', 'Schule', 'wovon', 'Glück', 'Morgen', 'das Glück'];

const vite = await createServer({ root: APP, server: { middlewareMode: true }, logLevel: 'error' });
const { shapeText, glyphKeysOf, decomposeLigatureSlot } = await vite.ssrLoadModule('/src/domain/shaping.ts');
const { composeWord } = await vite.ssrLoadModule('/src/domain/compose.ts');

async function fetchGlyphs(keys) {
  if (!keys.length) return new Map();
  const url = `${API}/sources/${SOURCE_ID}/write/glyphs?keys=${encodeURIComponent([...keys].sort().join(','))}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${url}`);
  const out = await res.json();
  const map = new Map(out.glyphs.map((g) => [g.glyph_key, g]));
  for (const k of keys) if (!map.has(k)) map.set(k, null);
  return map;
}

// Round every float in the EXPECTED output to 9 decimals — far below the
// test's 1e-6 tolerance, far above double noise, and it halves the fixture.
function round9(v) {
  if (typeof v === 'number') return Math.round(v * 1e9) / 1e9;
  if (Array.isArray(v)) return v.map(round9);
  if (v && typeof v === 'object') return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, round9(x)]));
  return v;
}

const entries = [];
for (const text of WORDS) {
  let slots = shapeText(text.normalize('NFC').trim());
  let data = await fetchGlyphs(glyphKeysOf(slots));
  // Mirror WrittenWord's resolveSlots: decompose missing closed-set ligatures.
  if (slots.some((s) => s.ligature && s.key && data.get(s.key) === null)) {
    slots = slots.flatMap((s) =>
      s.ligature && s.key && data.get(s.key) === null ? decomposeLigatureSlot(s) ?? [s] : [s],
    );
    const extra = glyphKeysOf(slots).filter((k) => !data.has(k));
    for (const [k, v] of await fetchGlyphs(extra)) data.set(k, v);
  }
  const composed = composeWord(slots.map((s) => ({ key: s.key, space: s.space, data: s.key ? data.get(s.key) ?? null : null })));
  entries.push({
    text,
    slots: slots.map((s) => ({ key: s.key, text: s.text, position: s.position, ligature: s.ligature, space: s.space })),
    payloads: Object.fromEntries(data),
    composed: round9(composed),
  });
  console.log(`${text}: ${composed.items.length} items, missing=[${composed.missing}]`);
}

await vite.close();

const outPath = resolve(REPO, 'tests', 'fixtures', 'compose_golden.json.gz');
await mkdir(dirname(outPath), { recursive: true });
await writeFile(outPath, gzipSync(JSON.stringify({ source_id: SOURCE_ID, words: entries }), { level: 9 }));
console.log(`wrote ${outPath}`);
