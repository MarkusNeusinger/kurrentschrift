### Added

- **`apply-laufform` keeps a running form with the hand it belongs to.**
  `templates` is keyed per style and carries no hand dimension, so a second
  hand's apply would have written over the plate's running forms. A hand now
  writes a style's Laufform row only if it is the hand registered on the
  style's teaching chart (`sources.hand_id`) or the row's own stamp
  (`trace_meta.laufform.hand_id`) names it; a row without a stamp — every row
  the manual harvest PUT ever wrote — belongs to the registered plate hand.
  The stamp clause holds without any registration, so a row derived from
  another hand is protected either way; registering a chart adds the first
  clause, which is how a plate hand takes such a row back. Reported in the
  endpoint's existing per-key idiom (200 with a `foreign_hand` skip naming
  `owner_hand_id`) rather than a route-level refusal, because a hand can own
  some of a style's rows by stamp and not the rest. Inert on today's data,
  where exactly one hand exists and wrote the stamps itself.
