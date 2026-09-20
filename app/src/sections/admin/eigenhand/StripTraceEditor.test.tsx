// @vitest-environment jsdom
//
// The FIRST component test for a re-tracing surface. Q6 (b) promises „die
// Suiten ziehen im selben PR mit" — for this surface there was nothing to pull
// along: no `*.test.tsx` in the repository referenced the plate editor either,
// so the suite this PR owes is the one below.
//
// Eight promises, each of which fails silently if it breaks — the editor would
// still look like it works:
//
//  1. THE ROUND TRIP. What is drawn on the crop is stored in the STRIP's frame,
//     so a Bahn saved and read back has to land on the same pixels. An
//     off-by-the-rectangle looks like a shaky hand on screen.
//  2. „SPEICHERN & WEITER" walks to the next box of the list's order and uses
//     the `ETag` the save handed back — no second read between two boxes of one
//     Fassung, and no stale token either.
//  3. A DRAGGED boundary goes out as the author's, an untouched one does not.
//     `herkunft: 'authored'` survives every later re-follow, so a wrongly
//     stamped one is a follower's guess frozen into the training set.
//  4. THE ABSETZER WARNING fires on a mismatch. Without it, tracing quietly
//     delivers a new stroke order by picture — the one thing the Duktus-Prior
//     exists to prevent (Prüfstein 7).
//  5. A 412 REACHES THE AUTHOR as something to act on, with his drawing still
//     on the canvas. A silent loss there is the whole reason the token exists.
//  6. THERE IS NO CANVAS WITHOUT THIS BOX'S PICTURE under it — not while the
//     protected crop is in flight, not after it failed, and never the previous
//     box's. A Bahn drawn over a blank or a stranger's crop looks exactly like
//     one drawn over the right ink.
//  7. A STRAY TAP IS NOT A CHANGE. The canvas drops a pen-down that never
//     moved; if the „geändert" survived it, a save would rewrite an untouched
//     follower Bahn as the author's own and drop its sensors.
//  8. THE BOUNDARIES BELONG TO THE RUN THEY SIT ON — given up when that run is
//     redrawn, however many samples the replacement happens to have, and kept
//     across an Anpassen drag, which moves points and no run.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import { ApiError } from '@/lib/api/client';
import type { EigenhandPfad, EigenhandPfadList, EigenhandPfadSpan } from '@/lib/api/types';

import { StripTraceEditor } from './StripTraceEditor';
import type { StripTraceTarget } from './stripBoxRows';

const readPfade = vi.fn();
const patchPfad = vi.fn();
const fetchStrip = vi.fn();

// The editor's three doors to the server. Mocked at the barrel, which is the
// only place this component reaches through.
vi.mock('@/lib/api', () => ({
  getEigenhandPfadeWithEtag: (...args: unknown[]) => readPfade(...args),
  patchEigenhandPfad: (...args: unknown[]) => patchPfad(...args),
  fetchEigenhandStrip: (...args: unknown[]) => fetchStrip(...args),
}));

const RECT = [120, 30, 320, 190];
// The crop is 200 × 160 px and the frame is xh 40, tx 20, baseline 124 — so a
// client pixel IS a crop pixel in this test, and trace u = (px − 20) / 40.
const CROP_W = 200;
const CROP_H = 160;

const LINE: number[][] = [
  [0, 0],
  [0.25, 0.5],
  [0.5, 1],
  [0.75, 0.5],
  [1, 0],
  [1.25, 0.5],
  [1.5, 1],
];

const SPANS: EigenhandPfadSpan[] = [
  { stroke: 0, slot: 0, first: 0, last: 2, herkunft: 'auto' },
  { stroke: 0, slot: 1, first: 3, last: 4, herkunft: 'auto' },
  { stroke: 0, slot: 2, first: 5, last: 6, herkunft: 'auto' },
];

const pfad = (over: Partial<EigenhandPfad> = {}): EigenhandPfad => ({
  box_index: 0,
  word: 'lesen',
  status: 'ok',
  grund: null,
  detail: null,
  strokes: [LINE],
  letter_spans: null,
  registration_px: { tx: 140, ty: 4, baseline_row: 150 },
  xh_px: 40,
  verfahren: 'tintenpfad',
  konfiguration: {},
  meta: { tintenpfad: { paper_lifts: 0 } },
  erzeugt_am: '2026-09-19',
  flecken_n: 0,
  ...over,
});

const list = (over: Partial<EigenhandPfadList> = {}): EigenhandPfadList => ({
  hand: 'wegwerf-suetterlin',
  strip: 'S0041',
  fassung: 'F02',
  format: 2,
  pfade: [pfad()],
  boxes: [
    { index: 0, word: 'lesen', items: [], rect_px: RECT, nominal_baseline_row: 152, nominal_xh_px: 38 },
    { index: 1, word: 'das', items: [], rect_px: RECT, nominal_baseline_row: 152, nominal_xh_px: 38 },
  ],
  ...over,
});

const TARGETS: StripTraceTarget[] = [
  { key: 'S0041/F02#0', strip: 'S0041', fassung: 'F02', boxIndex: 0, word: 'lesen', absetzerSoll: 1 },
  { key: 'S0041/F02#1', strip: 'S0041', fassung: 'F02', boxIndex: 1, word: 'das', absetzerSoll: 1 },
];

let container: HTMLDivElement;
let root: Root;
let onSaved: ReturnType<typeof vi.fn>;

beforeEach(() => {
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  onSaved = vi.fn();
  readPfade.mockResolvedValue({ list: list(), etag: '"first"' });
  patchPfad.mockResolvedValue({ list: list(), etag: '"second"' });
  fetchStrip.mockResolvedValue(new Blob(['png'], { type: 'image/png' }));
  // The reserved pixels reach the browser as a blob; jsdom has no object URLs.
  globalThis.URL.createObjectURL = vi.fn(() => 'blob:strip');
  globalThis.URL.revokeObjectURL = vi.fn();
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.clearAllMocks();
});

/** Mount the editor and let its two reads land — without asking for a canvas,
 * because whether there IS one is a question some of the cases below ask. */
async function mount(
  targets = TARGETS,
  startKey = TARGETS[0].key,
  onClose: () => void = () => {},
): Promise<void> {
  await act(async () => {
    root.render(
      <StripTraceEditor
        open
        hand="wegwerf-suetterlin"
        targets={targets}
        startKey={startKey}
        onClose={onClose}
        onSaved={onSaved}
      />,
    );
  });
}

/** Mount the editor and let its first read land. */
async function open(
  targets = TARGETS,
  startKey = TARGETS[0].key,
  onClose: () => void = () => {},
): Promise<void> {
  await mount(targets, startKey, onClose);
  // The dialog renders into a portal, so everything below reads document.body.
  canvas();
}

// jsdom has no layout: without a box the pointer maths cannot map a client
// coordinate into the crop at all, and no pen sample would ever be taken. Armed
// on every lookup rather than once at mount, because the surface is REMOUNTED
// whenever it waits for the next box's picture.
const canvas = (): SVGSVGElement => {
  const found = document.body.querySelector('[data-trace-canvas] svg');
  if (!found) throw new Error('no drawing surface');
  const svg = found as SVGSVGElement;
  svg.getBoundingClientRect = () =>
    ({ left: 0, top: 0, right: CROP_W, bottom: CROP_H, width: CROP_W, height: CROP_H, x: 0, y: 0 }) as DOMRect;
  svg.setPointerCapture = () => {};
  svg.releasePointerCapture = () => {};
  return svg;
};

/** Whether there is a surface to draw on at all. */
const drawable = (): boolean => document.body.querySelector('[data-trace-canvas]') !== null;

const text = (): string => document.body.textContent ?? '';

const button = (label: string): HTMLButtonElement => {
  const found = [...document.body.querySelectorAll('button')].find((b) => b.textContent?.trim() === label);
  if (!found) throw new Error(`no button „${label}"`);
  return found;
};

/** One pen event on the canvas — jsdom knows no PointerEvent, and React reads
 * `pointerId`/`pointerType` off whatever native event carries the name. */
function pen(type: 'pointerdown' | 'pointermove' | 'pointerup', x: number, y: number): void {
  const event = new MouseEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y });
  Object.defineProperty(event, 'pointerId', { value: 1 });
  Object.defineProperty(event, 'pointerType', { value: 'pen' });
  act(() => {
    canvas().dispatchEvent(event);
  });
}

/** A second stroke, drawn the way a pen draws one. */
function drawStroke(): void {
  pen('pointerdown', 30, 120);
  pen('pointermove', 60, 100);
  pen('pointermove', 90, 120);
  pen('pointerup', 90, 120);
}

/** A run of exactly `points` samples — 10 crop px apart, far above the pen's
 * own minimum step, so every one of them is kept. */
function drawRun(points: number): void {
  const x = (i: number): number => 20 + i * 10;
  const y = (i: number): number => (i % 2 === 0 ? 120 : 100);
  pen('pointerdown', x(0), y(0));
  for (let i = 1; i < points; i += 1) pen('pointermove', x(i), y(i));
  pen('pointerup', x(points - 1), y(points - 1));
}

/** The path the editor handed to the write door. */
const sentPfad = (call = 0): Omit<EigenhandPfad, 'verfahren'> =>
  patchPfad.mock.calls[call][4] as Omit<EigenhandPfad, 'verfahren'>;

it('stores what was drawn in the STRIP’s frame, and the seeded Bahn unchanged', async () => {
  await open();
  drawStroke();

  await act(async () => button('Speichern').click());

  expect(patchPfad).toHaveBeenCalledTimes(1);
  const [hand, strip, fassung, box, , etag, format] = patchPfad.mock.calls[0];
  expect([hand, strip, fassung, box]).toEqual(['wegwerf-suetterlin', 'S0041', 'F02', 0]);
  // The token of the list it was drawn on, and the ROW's own format — a
  // constant here would answer 409 on a format-1 row.
  expect(etag).toBe('"first"');
  expect(format).toBe(2);

  const sent = sentPfad();
  // Back into the strip's own pixels: the box rectangle goes on again and the
  // row shift rides in `baseline_row`, which is where every reader adds it.
  expect(sent.registration_px).toEqual({ tx: 140, ty: 0, baseline_row: 154 });
  expect(sent.xh_px).toBe(40);
  // The stored stroke travels back untouched; the drawn one is beside it.
  expect(sent.strokes[0]).toEqual(LINE);
  expect(sent.strokes).toHaveLength(2);
  // `status: null` is „ok" under format 2 and the only thing format 1 admits.
  expect(sent.status).toBeNull();
  // The follower's sensors describe the Bahn this save replaces — carrying
  // them would give a hand-drawn line a verdict measured on another one.
  expect(sent.meta).toEqual({});
  expect(onSaved).toHaveBeenCalledWith('S0041/F02#0');
});

it('warns when the drawn Bahn disagrees with the Absetzer-Soll', async () => {
  await open();
  // Seeded: one stroke, and the script writes „lesen" in one body run.
  expect(text()).toContain('1 Züge · Soll (Körper) 1');
  expect(text()).not.toContain('Markenzüge');

  drawStroke();

  expect(text()).toContain('2 Züge · Soll (Körper) 1');
  // The sentence says what the target does NOT count, because that is why two
  // runs can still be right (correction T5).
  expect(text()).toContain('i-Punkt, Umlaut');
});

it('walks to the next box on „Speichern & weiter", on the token the save handed back', async () => {
  await open();
  drawStroke();

  await act(async () => button('Speichern & weiter').click());

  // The next box of the list's own order, and no second read: the write
  // answered with the whole list AND the next token (#642).
  expect(text()).toContain('das');
  expect(text()).toContain('2 von 2');
  expect(readPfade).toHaveBeenCalledTimes(1);

  drawStroke();
  await act(async () => button('Speichern').click());
  expect(patchPfad).toHaveBeenCalledTimes(2);
  expect(patchPfad.mock.calls[1][3]).toBe(1);
  expect(patchPfad.mock.calls[1][5]).toBe('"second"');
});

it('sends a dragged boundary as the author’s and leaves the others alone', async () => {
  readPfade.mockResolvedValue({ list: list({ pfade: [pfad({ letter_spans: SPANS })] }), etag: '"first"' });
  await open();

  act(() => button('Grenzen').click());
  // The first seam sits on sample 2 — trace (0.5, 1), which is crop (40, 84).
  pen('pointerdown', 40, 84);
  // …dragged onto sample 3, trace (0.75, 0.5) = crop (50, 104).
  pen('pointermove', 50, 104);
  pen('pointerup', 50, 104);

  await act(async () => button('Speichern').click());

  const spans = sentPfad().letter_spans;
  expect(spans).toEqual([
    { stroke: 0, slot: 0, first: 0, last: 3, herkunft: 'authored' },
    { stroke: 0, slot: 1, first: 4, last: 4, herkunft: 'authored' },
    // Untouched, and therefore still the follower's own assignment — a
    // re-follow may replace it, which is the whole point of the difference.
    { stroke: 0, slot: 2, first: 5, last: 6, herkunft: 'auto' },
  ]);
  // The strokes are unchanged, so the boundaries still index real samples and
  // go out with them rather than being given up.
  expect(sentPfad().strokes).toEqual([LINE]);
});

it('surfaces a 412 as something to act on, with the drawing still standing', async () => {
  await open();
  drawStroke();
  patchPfad.mockRejectedValueOnce(new ApiError(412, '412: the stored paths have moved on since this was read'));

  await act(async () => button('Speichern').click());

  // Not „Speichern fehlgeschlagen": the save did not fail, the list it was
  // made on moved — and the answer is a re-read, not a retry.
  expect(text()).toContain('Auf diese Fassung wurde geschrieben');
  expect(button('Stand neu einlesen')).toBeTruthy();
  // The drawn Bahn is still on the canvas — that is the loss this whole token
  // dance exists to prevent.
  expect(text()).toContain('2 Züge');

  // The re-read refreshes the token WITHOUT re-seeding: the drawing survives
  // it too, and the next save goes out against the fresh list.
  readPfade.mockResolvedValue({ list: list(), etag: '"third"' });
  await act(async () => button('Stand neu einlesen').click());
  expect(text()).toContain('2 Züge');
  expect(text()).not.toContain('Auf diese Fassung wurde geschrieben');

  await act(async () => button('Speichern').click());
  expect(patchPfad.mock.calls[1][5]).toBe('"third"');
});

it('keeps the drawing in the frame it was DRAWN in when the conflict re-read brings another', async () => {
  await open();
  drawStroke();
  const drawn = () => sentPfad(patchPfad.mock.calls.length - 1);
  patchPfad.mockRejectedValueOnce(new ApiError(412, '412: the stored paths have moved on since this was read'));
  await act(async () => button('Speichern').click());

  // What the conflict announces („danach ersetzt Speichern, was inzwischen in
  // diesem Kasten steht"): a re-follow replaced this box's entry, and its Bahn
  // carries its OWN registration. The author's coordinates were made in the
  // frame he sees — re-reading must not silently re-interpret them in a
  // stranger's, or the save writes a line lying beside the ink.
  readPfade.mockResolvedValue({
    list: list({ pfade: [pfad({ registration_px: { tx: 200, ty: 0, baseline_row: 90 }, xh_px: 25 })] }),
    etag: '"third"',
  });
  await act(async () => button('Stand neu einlesen').click());

  await act(async () => button('Speichern').click());
  expect(drawn().registration_px).toEqual({ tx: 140, ty: 0, baseline_row: 154 });
  expect(drawn().xh_px).toBe(40);
  // …and the seeded stroke it was drawn beside is still the one it was drawn
  // beside, not the other writer's.
  expect(drawn().strokes[0]).toEqual(LINE);
});

it('keeps corrected boundaries when a run is drawn beside the ones they sit on', async () => {
  readPfade.mockResolvedValue({
    list: list({ pfade: [pfad({ letter_spans: [...SPANS.slice(0, 2), { ...SPANS[2], herkunft: 'authored' }] })] }),
    etag: '"first"',
  });
  await open();

  // The Absetzer-Soll asks for exactly this when a mark stroke is missing. It
  // appends, so every span index stays valid — and an `authored` seam given up
  // here is deleted by the write, which replaces the entry whole.
  drawStroke();

  await act(async () => button('Speichern').click());
  const spans = sentPfad().letter_spans;
  expect(spans).toHaveLength(3);
  expect(spans?.[2].herkunft).toBe('authored');
  // The two runs go out together; only the boundaries' own stroke matters.
  expect(sentPfad().strokes).toHaveLength(2);
});

it('keeps the drawing surface closed while this box’s picture is not under it', async () => {
  // The crop is a SECOND read, admin-gated and slow enough to matter. A canvas
  // over a blank is not „almost right": the Bahn would be stored against ink
  // the author never saw, and nothing on screen would say so (Copilot review).
  fetchStrip.mockRejectedValue(new ApiError(503, '503: strip image unavailable'));
  await mount();

  expect(drawable()).toBe(false);
  expect(text()).toContain('Solange er fehlt, wird hier nicht gezeichnet');
});

it('never leaves the canvas standing over the PREVIOUS box’s picture', async () => {
  let release: (blob: Blob) => void = () => {};
  fetchStrip.mockImplementationOnce(() => Promise.resolve(new Blob(['png'], { type: 'image/png' })));
  fetchStrip.mockImplementationOnce(
    () =>
      new Promise<Blob>((resolve) => {
        release = resolve;
      }),
  );
  await open();
  drawStroke();

  await act(async () => button('Speichern & weiter').click());

  // „das" is on the title, its Bahnen are in hand — and its picture is not.
  // Drawing here would land on „lesen", which is the worse of the two losses.
  expect(text()).toContain('das');
  expect(drawable()).toBe(false);

  await act(async () => {
    release(new Blob(['png'], { type: 'image/png' }));
  });
  expect(drawable()).toBe(true);
});

it('does not call a stray tap a change — an untouched Bahn stays unsaveable', async () => {
  await open();
  expect(button('Speichern').disabled).toBe(true);

  // A pen-down that never moves is a lift, and the canvas drops the stroke
  // again on it. What must not survive it is the „geändert": saving here would
  // rewrite the follower's own line as `authored` and drop the sensors
  // measured on it — a measurement turned into hand work by a tap.
  pen('pointerdown', 40, 84);
  pen('pointerup', 40, 84);

  expect(text()).toContain('1 Züge');
  expect(button('Speichern').disabled).toBe(true);
});

it('gives the boundaries up when the run they sit on is REDRAWN with as many samples', async () => {
  readPfade.mockResolvedValue({ list: list({ pfade: [pfad({ letter_spans: SPANS })] }), etag: '"first"' });
  await open();

  // Undo the seeded run and draw another one with the same seven samples. A
  // count comparison calls that „unchanged" — and then the stored boundaries,
  // one of which may be the author's own, name samples of a line nobody
  // measured them on (Copilot review).
  act(() => button('Letzten Zug zurück').click());
  drawRun(LINE.length);

  // Said before it is done: the boundaries are given up, and the notice is now
  // true where it used to be a lie about a count.
  expect(text()).toContain('Die Züge sind neu gezeichnet');

  await act(async () => button('Speichern').click());

  const sent = sentPfad();
  expect(sent.strokes).toHaveLength(1);
  expect(sent.strokes[0]).toHaveLength(LINE.length);
  expect(sent.strokes[0]).not.toEqual(LINE);
  expect(sent.letter_spans).toBeNull();
});

it('keeps the boundaries across an Anpassen drag, which moves points and no run', async () => {
  readPfade.mockResolvedValue({ list: list({ pfade: [pfad({ letter_spans: SPANS })] }), etag: '"first"' });
  await open();

  act(() => button('Anpassen').click());
  pen('pointerdown', 40, 84);
  pen('pointermove', 44, 88);
  pen('pointerup', 44, 88);

  await act(async () => button('Speichern').click());

  // The run is the same run, so its boundaries still describe it — and an
  // `authored` one given up here is deleted by the write, which replaces the
  // entry whole.
  expect(sentPfad().letter_spans).toHaveLength(SPANS.length);
  expect(sentPfad().strokes[0]).not.toEqual(LINE);
});

it('asks before an unsaved drawing is thrown away, and closes when told to', async () => {
  const onClose = vi.fn();
  await open(TARGETS, TARGETS[0].key, onClose);
  drawStroke();

  act(() => button('Schließen').click());
  // A hand-drawn Bahn exists nowhere else — no follower run recreates it.
  expect(onClose).not.toHaveBeenCalled();
  expect(text()).toContain('Gezeichnete Bahn verwerfen?');

  act(() => button('Verwerfen und schließen').click());
  expect(onClose).toHaveBeenCalledTimes(1);
});
