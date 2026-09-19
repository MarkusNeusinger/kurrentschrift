### Changed

- **The Admin-Redesign plan books Phase 1's three author decisions and the
  delivered Phase 0.** `docs/proposals/admin-redesign.md` gains §4.6 for the
  decisions of 2026-09-19 and pulls the affected Vorgaben along in the same
  pass, so no surface is specified twice. The Eigenhand sub-views move from
  `?ansicht=` to `?reiter=` (V2, V7, §7.1–§7.2, §15.1): `ansicht` stays with
  the list/gallery display mode of the overviews, and `reiter` means "which
  tab of this page" everywhere — the two meanings would otherwise have met in
  one URL on the strips surface, which already has two display modes. The
  Scope-Leiste's `Hand:` field always names the Eigenhand, with the role gloss
  on it, because the plate hand is derived per Vorlage and keeps being named
  at its own statistics panels; one label meaning two things depending on the
  route is the confusion the bar exists to end. And the subject stepper moves
  to `Alt+Shift+←/→` (V24, §5.1 idea 18, §9.2): `Alt+←/→` is Back/Forward in
  Chrome, Edge and Firefox on Windows and Linux, and the admin's whole linking
  doctrine rests on the back button. The same note retires the plan's WCAG
  2.1.4 citation for the shortcuts switch — SC 2.1.4 exempts modifier-based
  bindings — and puts the real reason in its place.

- **Phase 0 is recorded as delivered, with what is still open.** §15.2 ticks
  its nine rows with their PR numbers and names the one outstanding step: the
  prod data step V1 (`UPDATE sources.hand_id`), which has no admin route and
  is therefore SQL on the shared Cloud SQL, awaiting the author's in-session
  confirmation with a snapshot first. §15.3 records that the Freigabe-Maschine
  proposal now exists, that its six Rückfragen FM1–FM6 are open and block the
  Phase 5 build, and the two findings its schema PR must carry — the public
  `GET /sources/{id}/templates` lists every variant (a second leak beside
  `/write/glyphs?variant=`), and `glyph_pairs` is unique over
  `(style_id, left_key, right_key, variant)`, so Q23's `hand_id` has to enter
  the KEY rather than sit beside it. A new §15.4 carries the eight-PR slice of
  Phase 1 in merge order.

- **Three plan claims corrected against the code.** The origin chip says
  `automatisch (Tintenpfad)` only on the STRIP, where `eigenhand_strips.pfade`
  stores the Verfahren per box; on the PLATE it says plain `automatisch`,
  because `word_instances` has no follower column (`provenance` is
  `traced | authored`) and the harvest writes that provenance as a constant —
  naming a method there would be an unbacked claim. Q17's wording called
  `lesen`, `das` and `denen` "MVP-Anker"; `architektur.md` §9 names `lesen` +
  `das` the Pflicht-Anker pair and `denen` the Generalisierungs-Wort, and the
  1922 plate sidecar writes neither `lesen` nor `denen`, so the pin closes a
  three-way bridge for the dev words and a two-way one for those two. The
  decision itself stands; all fourteen words stay pinned. And V23's working
  name `paper.layer.*` is retired: the token PR shipped seven sibling exports
  (`layer`, `layerDash`, `role`, `roleDash`, `mono`, `strokeStyle`,
  `layerAlpha`), with the 3:1 floor holding for opaque marks and two named
  exceptions carrying their measured numbers.
