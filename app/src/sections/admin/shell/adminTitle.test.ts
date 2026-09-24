import { describe, expect, it } from 'vitest';

import { adminTitle, joinSubject } from './adminTitle';

describe('admin tab titles', () => {
  it('names the subject of each detail view', () => {
    expect(adminTitle('/admin/buchstaben', '?g=n')).toBe('Buchstabe n · Werkbank');
    expect(adminTitle('/admin/uebergaenge', '?l=e&r=n')).toBe('Übergang e → n · Werkbank');
    expect(adminTitle('/admin/woerter', '?w=lesen')).toBe('Wort lesen · Werkbank');
  });

  it('spells a letter key back into its character, as the h1 does', () => {
    expect(adminTitle('/admin/buchstaben', '?g=longs')).toBe('Buchstabe ſ · Werkbank');
  });

  it('spells both keys of a join back into their characters', () => {
    // The registry key `longs` is an identifier, not what anyone writes: the
    // tab said „Übergang longs → t" while the pickers beside it showed ſ.
    expect(adminTitle('/admin/uebergaenge', '?l=longs&r=t')).toBe('Übergang ſ → t · Werkbank');
    expect(adminTitle('/admin/uebergaenge', '?l=e&r=longs')).toBe('Übergang e → ſ · Werkbank');
  });

  it('gives the join h1 the very words of the tab', () => {
    expect(joinSubject('longs', 't')).toBe('Übergang ſ → t');
    // A key the registry does not know stays visible instead of leaving a gap.
    expect(joinSubject('nonsense', 't')).toBe('Übergang nonsense → t');
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
    // Three segments since the `?reiter=` split: a bare /admin/eigenhand IS
    // the Bestand, so the tab says so rather than naming the area twice.
    expect(adminTitle('/admin/eigenhand', '')).toBe('Eigenhand · Bestand · Werkbank');
    expect(adminTitle('/admin', '')).toBe('Werkbank');
  });

  it('names the Eigenhand sub-view, and falls back like focus.ts does', () => {
    expect(adminTitle('/admin/eigenhand', '?reiter=streifen')).toBe('Eigenhand · Streifen · Werkbank');
    expect(adminTitle('/admin/eigenhand', '?reiter=statistik')).toBe('Eigenhand · Statistik · Werkbank');
    expect(adminTitle('/admin/eigenhand', '?reiter=drucken')).toBe('Eigenhand · Drucken · Werkbank');
    expect(adminTitle('/admin/eigenhand', '?reiter=quatsch')).toBe('Eigenhand · Bestand · Werkbank');
    // The display mode of a later overview must not be read as a sub-view.
    expect(adminTitle('/admin/eigenhand', '?ansicht=streifen')).toBe('Eigenhand · Bestand · Werkbank');
    // The strips filter is not the subject — it must not reach the tab.
    expect(adminTitle('/admin/eigenhand', '?reiter=streifen&item=a%3Eb')).toBe('Eigenhand · Streifen · Werkbank');
    expect(adminTitle('/admin/eigenhand/', '?reiter=drucken')).toBe('Eigenhand · Drucken · Werkbank');
  });

  it('never lets the hand move the title', () => {
    // `h=` is a scope, not a subject: the tab names WHAT is being looked at,
    // and that did not change because the hand did. Two tabs on the same
    // letter under two hands are told apart by the Scope-Leiste, not here.
    expect(adminTitle('/admin/buchstaben', '?g=n&h=mn-suetterlin')).toBe('Buchstabe n · Werkbank');
    expect(adminTitle('/admin/buchstaben', '?h=mn-suetterlin')).toBe('Buchstaben · Werkbank');
    expect(adminTitle('/admin/uebergaenge', '?l=e&r=n&h=mn-suetterlin')).toBe('Übergang e → n · Werkbank');
    expect(adminTitle('/admin/woerter', '?w=lesen&h=mn-suetterlin')).toBe('Wort lesen · Werkbank');
    expect(adminTitle('/admin/eigenhand', '?reiter=streifen&h=mn-suetterlin')).toBe(
      'Eigenhand · Streifen · Werkbank',
    );
  });

  it('tolerates a trailing slash and an unknown admin path', () => {
    expect(adminTitle('/admin/woerter/', '?w=das')).toBe('Wort das · Werkbank');
    // The retired URLs redirect, but the title must not be empty in the frame
    // before the redirect lands.
    expect(adminTitle('/admin/werkbank', '')).toBe('Werkbank');
  });
});
