### Added

- **The Freigabe-Maschine proposal — how an ever-growing hand gets released
  again and again (`docs/proposals/freigabe-maschine.md`, status `offen`,
  no code).** The author's decision Q24 (i) of 2026-09-18 asked for the
  target picture NOW, before the phase 5 schema PR, so that the per-hand
  variant band (Q19 a) and the hand preview route (Q22 a) are built to fit
  it. The reason is his second guiding sentence: the own hand is the
  optimisation target and keeps growing, so the role change of `vision.md`
  „Drei Rollen" is not a one-time switch but the first of many deliveries —
  and today there is not even a log of which `apply-laufform` changed what
  (scenario S10). The proposal settles what a Stand is (a complete,
  create-only set of ONE hand's running-form rows under ONE variant number
  in that hand's band, plus a header that keeps the apply report the HTTP
  response throws away today), how the band is cut (`hands.laufform_variant`
  is the band BASE, a Stand number is base + running index, 100 per hand,
  never reused, zero DDL on `templates`), and how a Stand comes to be
  (copy-then-insert, because `/write/word` reads a missing row as a chart
  fallback; the manual `PUT`/`DELETE …/laufform` become Stand operations;
  the first own-hand Stand starts empty, never as a relabelled plate form).
  The delivery pointer is an append-only log resolved as source → hand →
  newest row, NOT one pointer per style: the reading quiz stays with the
  1922 forms after the role change (author, 2026-09-07), so two hands of one
  script deliver at once, and `/write/word.svg` titles its picture with the
  source. Delivering and rolling back are the same act — one appended row
  with a mandatory reason — and stay a terminal act the author decides, never
  an admin button. Regression is per hand and deliberately different: a plate
  Stand runs the frozen word ruler as an A/B of two roots with identical
  references; an own-hand Stand gets NO headline (Prüfstein 2) but coverage,
  evidence, within-hand form movement, a pre-registered never-harvested
  holdout and the blind human pass — and an own-hand delivery must leave the
  plate's fixture rows and headline untouched. Archive snapshots stay
  create-only and stop being the rollback. It also names what the three
  design sketches proposed and the doc rejects, five questions only the
  author can answer (FM1–FM5), and a build order that slots into
  `admin-redesign.md` §15.3.
- **Reading the code for that proposal turned up four things the plan had
  not seen, recorded in its §3.** The public `GET /sources/{id}/templates`
  lists every variant of a script with its `advance`, so an undelivered
  own-hand Stand would be publicly visible even with `/write/glyphs` closed
  — a second leak beside the one Q19 names. A plain `glyph_pairs.hand_id`
  column (Q23 a) does not separate two hands, because the unique key
  `(style_id, left_key, right_key, variant)` does not contain it. The pooled
  pen reads `half_widths` without a variant filter while every running-form
  row copies its chart row's widths, so each retained Stand would silently
  re-weight the public stroke width. And the own hand's source pools nothing
  at all. None of it is fixed here; each lands in the schema PR or in a
  question to the author.

### Changed

- **The glossary's pre-written „Freigabe-Maschine (geplant)" entry points at
  the new proposal, and the terms it coins get their own entries**
  („Laufform-Stand", „Auslieferungs-Zeiger", „Vergleichsstreifen" — themed
  block plus Schnellindex, all still „geplant"). „Varianten-Band (geplant)"
  now carries the proposed cut and the Band-Regel. `docs/index.md` has the
  row, and `admin-redesign.md` §15.3 step 1 links the doc it asked for.
