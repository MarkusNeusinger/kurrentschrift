### Added

- **Der Streifen-Pfad: the followed pen path of a written word, stored as data
  beside the image.** A Fassung carried a picture, a verdict, a Befund and a
  Fleckenmaske — but no ductus; the image said WHERE the ink is and never in
  which order the pen laid it down. `eigenhand_strips.pfade` (migration `0031`)
  now holds, per written word box, the strokes in the word's own units — the
  same frame `word_instances.strokes` uses — the registration in the strip's
  pixels, the Verfahren, the follower configuration, the day, and the size of
  the Fleckenmaske it was followed under. It is computed offline and stored
  through `PUT /eigenhand/strips/{hand}/{strip}/{fassung}/pfade`, because the
  API image ships no `tools` and the server can therefore never follow a path
  itself. The column is deferred beside the PNG, so no Bestand read drags every
  path of every Fassung along, and a path deliberately never enters
  `word_instances`: that table's rows are the frozen Tintenfolger reference set.
- **`tools.eigenhand.pfad` — follow, look, and only then write.** It reads the
  strip image, the Bogen layout and the box rectangles over the admin API, cuts
  each word out and runs the Tintenpfad over it with the configuration the
  campaign settled on (`tip_read` · `rail=tentfit` · `edt_upsample=4` ·
  `ink_bridge_xh=1.0` · `hairpin_tip` · `ride_back` · `tip_grey_stop` ·
  `self_jump`), which travels into the stored row. A dry run is the default;
  `--apply` writes the shared database and belongs behind an archive snapshot.
- **One path overlay, two surfaces.** „Pfad" joins the layer buttons in Wörter
  and „Pfad zeigen" lays the same drawing over strips and word crops in
  Eigenhand: a colour ramp in writing order, a dot where the pen touched down,
  an arrow head at each stroke's end and **dashed connectors for the Absetzer**
  — the part a single flat colour hides completely, because a lift looks
  exactly like a corner. Herkunft and date stand beside it; `WordInstanceOut`
  carries its `updated_at` for that, and the strip listing every box's pixel
  rectangle.
