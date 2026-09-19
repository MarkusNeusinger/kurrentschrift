### Changed

- **`/admin/eigenhand` is four sub-views behind `?ansicht=`.** Bestand,
  Streifen, Statistik and Drucken now share the route instead of standing
  under each other on one very long page; a bare `/admin/eigenhand` — and any
  unknown value — lands on Bestand, exactly the way `focus.ts` sends an
  unknown subject to a view's overview. The switch is a `ToggleButtonGroup` of
  links, so each view is linkable, middle-clickable and walked by the back
  button, and a coverage cell that used to scroll down to the strips gallery
  now navigates to it with the filter in the URL (`item`/`wort`). The hand,
  the single Bestand read behind all four views and the last print job's sheet
  ids stay in the shell: reading per view would have fetched the same payload
  four times and lost the `angenommen` counter the gallery breaks its cache
  on, and a hop to the Bestand and back would have left the printed Bögen on
  the server with nothing on screen able to name them.

### Added

- **The Eigenhand statistics view reports the hand's pen.** The new Statistik
  sub-view derives the median nib half width per hand from the `befund.nib`
  readings the strip listing already carries, beside labelled placeholders
  naming the three figures that need compute still to be written. A Fassung
  that could not be measured is dropped rather than averaged in — `befund.py`
  files an unmeasured pen as `0.0`, and counting those would quietly report a
  hairline hand.
