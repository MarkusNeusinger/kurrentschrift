### Fixed

- **Words no longer collide when the next one starts with a left-reaching
  capital.** `SPACE_ADV` advanced the cursor — the end of the Endstrich to
  the next letter's entry point — but several Sütterlin capitals carry their
  bow far left of their own origin (K −1.64, C −1.42, F −1.16, G/Q/O/A ≈
  −0.8, I −0.45, X −0.18 x-height), so "Die Federprobe" wrote the F inside
  "Die". The word gap is now measured between INK: the first glyph after a
  space is placed at whichever is further right, the anchor advance or the
  new `WORD_INK_GAP` floor past the previous word's rightmost ink. The floor
  (0.43) sits below every boundary the anchor advance already writes wide
  enough — the tightest is 0.4395 after a final t, the common case 0.4777 —
  so ordinary words stay byte-identical; the mirrored case moves too, where
  a word ending in w or v used to leave its bow inside the next word.
