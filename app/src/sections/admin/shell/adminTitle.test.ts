import { describe, expect, it } from 'vitest';

import { adminTitle } from './adminTitle';

describe('admin tab titles', () => {
  it('names the subject of each detail view', () => {
    expect(adminTitle('/admin/buchstaben', '?g=n')).toBe('Buchstabe n · Werkbank');
    expect(adminTitle('/admin/uebergaenge', '?l=e&r=n')).toBe('Übergang e → n · Werkbank');
    expect(adminTitle('/admin/woerter', '?w=lesen')).toBe('Wort lesen · Werkbank');
  });

  it('spells a letter key back into its character, as the h1 does', () => {
    expect(adminTitle('/admin/buchstaben', '?g=longs')).toBe('Buchstabe ſ · Werkbank');
  });

  it('falls back to the overview title when the URL carries no subject', () => {
    expect(adminTitle('/admin/buchstaben', '')).toBe('Buchstaben · Werkbank');
    expect(adminTitle('/admin/uebergaenge', '')).toBe('Übergänge · Werkbank');
    expect(adminTitle('/admin/woerter', '')).toBe('Wörter · Werkbank');
  });

  it('treats an unknown or half-given subject as no subject', () => {
    expect(adminTitle('/admin/buchstaben', '?g=nonsense')).toBe('Buchstaben · Werkbank');
    // A half-given pair has no join to show (focus.ts), so the tab says so too.
    expect(adminTitle('/admin/uebergaenge', '?l=e')).toBe('Übergänge · Werkbank');
    expect(adminTitle('/admin/woerter', '?w=%20%20')).toBe('Wörter · Werkbank');
  });

  it('names the hand-scoped view and the Vorlage picker', () => {
    expect(adminTitle('/admin/eigenhand', '')).toBe('Eigenhand · Werkbank');
    expect(adminTitle('/admin', '')).toBe('Werkbank');
  });

  it('tolerates a trailing slash and an unknown admin path', () => {
    expect(adminTitle('/admin/woerter/', '?w=das')).toBe('Wort das · Werkbank');
    // The retired URLs redirect, but the title must not be empty in the frame
    // before the redirect lands.
    expect(adminTitle('/admin/werkbank', '')).toBe('Werkbank');
  });
});
