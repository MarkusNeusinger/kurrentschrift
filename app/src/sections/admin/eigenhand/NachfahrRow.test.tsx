// @vitest-environment jsdom
//
// The three promises of a Nachfahr-Zeile that no type checker can keep.
//
// 1. A box the AUTHOR drew himself is never invited to be re-followed. That is
//    not a nicety: the follower would replace his own line with a generated
//    one, and an offer to do it with one tap is how it happens by accident
//    (archiv R7 of the Phase-2 recon). The row says what the terminal flag is
//    instead of hiding that a way exists.
// 2. „übersprungen: unautoriert" leaves this list. It is a Ground-Truth gap and
//    belongs on the Tafel, so the row links into the letter view FOR THE KEYS
//    THE SKIP NAMED — a button called „einrichten" without the letter would
//    leave the reader guessing (§6.4 „Umgeleitet").
// 3. A box off a Bogen printed before the cut geometry gets NO command. §6.4
//    calls it „nie machbar", and handing over a re-follow that reproduces the
//    same skip would dress a dead end up as work.
//
// Image-free like its siblings: nothing here may mount a crop.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import type { EigenhandTintentreue } from '@/lib/api';

import { NachfahrRow } from './NachfahrRow';
import type { StripBoxRow } from './stripBoxRows';

const urteil = (over: Partial<EigenhandTintentreue> = {}): EigenhandTintentreue => ({
  stufe: 'folgt nicht',
  grund: 'Absetzer (Bahn)',
  gemessen: true,
  sensor: 'Absetzer (Bahn)',
  sensoren: [{ name: 'Absetzer (Bahn)', wert: 8, soll: 3, gruen: null, gelb: null, stufe: 2 }],
  format: 2,
  schwellen_stand: '2026-09-20',
  vorlaeufig: true,
  ...over,
});

const row = (over: Partial<StripBoxRow> = {}): StripBoxRow => ({
  key: 'S0041/F02#2',
  strip: 'S0041',
  fassung: 'F02',
  sheet: 'B0001',
  rowIndex: 0,
  boxIndex: 2,
  word: 'kann',
  format: 2,
  gefolgt: true,
  absetzerSoll: 3,
  skipGrund: null,
  skipDetail: null,
  verfahren: 'tintenpfad',
  erzeugtAm: '2026-09-20',
  stale: false,
  offen: true,
  tintentreue: urteil(),
  severity: 'rot',
  missingKeys: [],
  korbOpen: 0,
  ...over,
});

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.clearAllMocks();
});

function render(one: StripBoxRow, expanded = false, onMark = () => {}): void {
  act(() => {
    root.render(
      <MemoryRouter>
        <NachfahrRow row={one} hand="mn-suetterlin" expanded={expanded} onToggle={() => {}} onMark={onMark} />
      </MemoryRouter>,
    );
  });
}

it('names the box and what the Ampel found, without a picture', () => {
  render(row());
  expect(container.textContent).toContain('kann');
  expect(container.textContent).toContain('S0041 · F02 · Kasten 2');
  // The step AND the sensor that named it: „folgt nicht" alone says what but
  // never which reading decided it.
  expect(container.textContent).toContain('folgt nicht');
  expect(container.textContent).toContain('Absetzer (Bahn)');
  expect(container.querySelectorAll('img')).toHaveLength(0);
});

it('offers the box command only where the Bahn is not the author’s own', () => {
  render(row(), true);
  expect(container.textContent).toContain('--box 2');

  render(
    row({
      verfahren: 'authored',
      severity: 'von-hand',
      offen: false,
      tintentreue: urteil({ stufe: 'nicht beurteilt', grund: 'von Hand gezeichnet', gemessen: false, sensor: null }),
    }),
    true,
  );
  expect(container.textContent).not.toContain('--box');
  expect(container.textContent).toContain('Von Hand gezogen');
  expect(container.textContent).toContain('--replace-authored');
});

it('offers no command at all for a Bogen printed before the cut geometry', () => {
  // §6.4 calls this one „nie machbar": `frame_for_box` raises for exactly this
  // Bogen, so a re-follow would write the same Skip-Eintrag again.
  render(row({ skipGrund: 'no_geometry', skipDetail: 'box 2 has no rect_px', severity: 'grau' }), true);
  expect(container.textContent).not.toContain('--box');
  expect(container.textContent).toContain('vor der Schnitt-Geometrie');
});

it('sends an unauthored skip to the letter view for the keys it named', () => {
  render(row({ skipGrund: 'unauthored', skipDetail: 'sz ch', missingKeys: ['sz', 'ch'], severity: 'grau' }));
  const links = [...container.querySelectorAll('a')].map((a) => a.getAttribute('href'));
  expect(links).toEqual(['/admin/buchstaben?g=sz&h=mn-suetterlin', '/admin/buchstaben?g=ch&h=mn-suetterlin']);
  expect(container.textContent).toContain('Tafel fehlt: sz ch');
  // …and offers no flag beside it: a Ground-Truth gap is „kein Korb-Eintrag"
  // (V9), so the plate is the step INSTEAD of the basket, not next to it.
  expect(container.textContent).not.toContain('⚑');
});

it('calls a skipped box an attempt, never a Bahn', () => {
  // `_skip` stamps the follower onto the entry it writes, but there is no path
  // — „Bahn: Tintenpfad" would contradict the verdict and the „Ohne Bahn"
  // status in the same line.
  render(row({ skipGrund: 'gave_up', skipDetail: 'no_ink: nothing found', severity: 'nichts-gefunden' }));
  expect(container.textContent).toContain('Keine Bahn · Versuch: automatisch (Tintenpfad)');
  expect(container.textContent).not.toContain('Bahn: automatisch');
  // A followed box keeps saying where its Bahn comes from.
  render(row());
  expect(container.textContent).toContain('Bahn: automatisch (Tintenpfad) · 2026-09-20');
});

it('keeps „Maske geändert" beside the verdict rather than inside it', () => {
  // The grey state of a hand-drawn box is „von Hand gezeichnet"; that the mask
  // has changed since is true all the same, and the row is where both fit.
  render(row({ stale: true }));
  expect(container.textContent).toContain('Maske geändert');
  // Opened, it also says what to do about it — and what that costs: the row
  // hands over the DRY RUN, the way every Übergabekarte does, and names
  // `--apply` with the snapshot that belongs in front of it.
  render(row({ stale: true }), true);
  expect(container.textContent).toContain('erst neu folgen lassen');
  expect(container.textContent).toContain('--box 2');
  expect(container.textContent).toContain('--apply');
});

it('does not say „Maske geändert" twice when that IS the Ampel’s reason', () => {
  // Nothing greyer stands in front of it, so the verdict already carries the
  // sentence — a chip beside it would be the doubling this PR removes from the
  // strip caption, one row further down.
  render(
    row({
      stale: true,
      severity: 'grau',
      tintentreue: urteil({ stufe: 'nicht beurteilt', grund: 'Maske geändert', gemessen: false, sensor: null }),
    }),
  );
  expect(container.textContent?.match(/Maske geändert/g)).toHaveLength(1);
});

it('says the thresholds are borrowed wherever it shows a reading', () => {
  render(row(), true);
  expect(container.textContent).toContain('Schwellen vorläufig');
  expect(container.textContent).toContain('Absetzer-Soll 3');
});

it('files the box itself when the ⚑ is pressed', () => {
  const onMark = vi.fn();
  render(row(), false, onMark);
  const mark = [...container.querySelectorAll('button')].find((b) => b.textContent?.includes('⚑'));
  expect(mark).toBeDefined();
  act(() => (mark as HTMLButtonElement).click());
  expect(onMark).toHaveBeenCalledTimes(1);
});
