// The Schriftkunde anchors and specimens are public surface: a fragment URL
// someone shared must keep resolving, and a specimen strip must name a glyph
// the source can actually write.
import { describe, expect, it } from 'vitest';

import { knownGlyph } from '@/domain/glyphs';
import { schriftkunde } from '@/locales/de/schriftkunde';
import { SCHRIFTKUNDE_SECTIONS, SECTION_IDS } from '@/sections/schriftkunde/sections';

describe('Schriftkunde sections', () => {
  it('has one unique, URL-safe id per section, every SECTION_IDS entry used once', () => {
    const ids = SCHRIFTKUNDE_SECTIONS.map((s) => s.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const id of ids) expect(id).toMatch(/^[a-z]+(-[a-z]+)*$/);
    expect([...ids].sort()).toEqual(Object.values(SECTION_IDS).sort());
    // The script cards share the fragment namespace (#kurrent …) — no clash.
    for (const v of schriftkunde.variants) expect(ids).not.toContain(v.id);
  });

  it('lists the sections under their own headings, none empty', () => {
    for (const s of SCHRIFTKUNDE_SECTIONS) expect(s.heading.trim().length).toBeGreaterThan(0);
    expect(SCHRIFTKUNDE_SECTIONS.map((s) => s.heading)).toContain(schriftkunde.lettersHeading);
  });

  it('names only known base glyph_keys in the letter specimens, each with a label', () => {
    for (const row of schriftkunde.letters) {
      if (!('specimens' in row)) continue;
      expect(row.specimens.length).toBeGreaterThan(0);
      for (const s of row.specimens) {
        expect(knownGlyph(s.key), `${row.term}: ${s.key}`).toBeDefined();
        expect(s.label.length).toBeGreaterThan(0);
      }
    }
  });
});
