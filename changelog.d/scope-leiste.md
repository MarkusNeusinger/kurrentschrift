### Added

- **Scope-Leiste: the admin says what each page is about.** A row under the
  workbench header with two fields — „Vorlage: Sütterlin · suetterlin-1922"
  and „Hand: mn-suetterlin (Eigenhand — meine Hand)" — that SHOW both scopes
  and never switch them; the field the open page is about carries
  `aria-current` and a viridian rule beside it, so the highlight survives a
  colour-vision pass. Until now the header named one scope and named it
  everywhere: the Vorlage chip and the Vorlage's basket kept standing over
  `/admin/eigenhand`, which belongs to a hand, while the hand was named on no
  other page at all. That is a labelling error, so the fix is a bar that
  states both rather than a control that changes one.
- **`h=` — the hand travels in every admin link.** All `focus.ts` builders
  take the hand as their last argument, so every URL without one stays
  byte-identical; the Auftragskorb's links always carry it, a subject change
  inside a view keeps it (`keepHand`), an id that cannot be one is dropped,
  and it never moves the tab title — the title names the subject, and the
  hand is not one.

### Changed

- **The own hand is workbench state, not a field on the Eigenhand page.** It
  lives in the outer admin provider, above the per-Vorlage remount, so two
  Vorlagen of one script share it; it is always a hand of the Vorlage's
  script, falling back to the last hand chosen for that script and otherwise
  to none (`handScope.ts::resolveHand`). The candidates are the union of
  `GET /eigenhand/hands` and `GET /eigenhand/setups`, because the first knows
  only hands that already have a sheet or a Fassung. The Eigenhand page keeps
  the picker — it is the one place the hand is chosen — and offers exactly
  the hands of the open Vorlage's script.
- **The Vorlagen-Chip left the header.** It was the same link to the same
  picker as the bar's Vorlage field, and dropping it is what buys the
  two-row phone header: the four area links now scroll with snap points
  instead of wrapping onto a third row.
- **The Auftragskorb says whose basket it counts.** The open count rides the
  bar's Vorlage field as visible text, and the header's ⚑ names the Vorlage
  in its label. Before, the scope was stated nowhere — not even in the
  tooltip.

### Fixed

- **No invented hand id any more.** The Eigenhand page defaulted to
  `` `mn-${styles[1] ?? 'suetterlin'}` `` — one writer's prefix plus a
  position in the styles array, an id no read had ever returned. A script
  without a written hand now says so.
