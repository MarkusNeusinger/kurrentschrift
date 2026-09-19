### Added

- **Rohzahlen-Chip: the follower's sensors per word box, as numbers.** With
  „Pfad zeigen" on, the Eigenhand strip panel now prints one chip line per
  Kasten — ink the Bahn never visits (percent), Absetzer, Sprünge, Haken —
  read out of the path data the switch already loads, so it costs no extra
  request. Labelled „Zahl, kein Urteil": nothing here is coloured or judged,
  because the Tintentreue traffic light lands in the same place later and the
  two must not be confused. A single sensor the follower never wrote reads as
  a dash and a Bahn carrying none at all as „nicht gemessen" — never as 0,
  because `ink_unvisited_share: 0` is the best reading a Bahn can get and the
  two would otherwise look alike. Over a whole strip each line names its
  Kasten by the index `--box` takes, so a row holding the same word twice
  still says which cut a reading belongs to.
