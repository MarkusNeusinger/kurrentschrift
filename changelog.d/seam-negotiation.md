### Added

- **The two sides of a join now agree on an angle instead of one dictating
  it.** The author's rule of 2026-09-06 — „in der letzten Kurve wird etwas
  weiter gedreht oder im Eingang, so dass sich beide Seiten auf einen
  Kompromiss einigen und die Verbindungslinie in einem perfekten Winkel raus-
  und wieder reinfließt" — becomes `compose_word(seam_negotiation=True)`
  (default off, so nothing production renders moves). At each end of a
  generated join the letter and the connector read their direction over the
  same 0.05 xh the eye reads the seam on, meet at the circular mean, and both
  turn there: the letter by at most 8° over its last (or first) 0.3 xh, the
  connector by whatever is left. The turn is a planar twist about the seam
  POINT, which therefore does not move — no coupling height and no placement
  changes, the failure that closed the P3 entry rules. Past 45° of
  disagreement the rule keeps its hands off: that is a turn the ductus writes.
  Measured under „Übergänge J6" in `docs/reference/messjournal.md` §14 — the
  eye-scale seam angle falls from 12.67°/10.80° (departure/arrival) to
  0.01°/0.01° over 240 joins, and the arm is NOT adopted: it costs two extra
  `gleichzug_doublings` on the two-letter drills, where a connector has to
  absorb 30–37° next to the `d`'s own ink. `--seam-negotiation` on
  `tools.wordbench.run` and `tools.humanbench.wordarm`, with
  `--seam-negotiation-max-jump` for the narrower post-hoc J6b arm that trades
  the biggest arrival class for that constraint. Side finding worth the
  author's attention now that the exit trim ships (A37): the negotiation
  closes the departure seam WITHOUT it and more cheaply — 12.67° → 0.02°
  against the trim's 2.30°, at +0.000376 on the word ruler against its
  +0.000582, and without its measured side effect on the arrival. The two
  rules aim at the same seam from opposite sides and are alternatives rather
  than complements.
