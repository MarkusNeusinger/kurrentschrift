### Added

- **The training export of the hand-drawn Bahnen, with two hold-out sets.**
  `tools.eigenhand.trainingssatz` cuts every word box the author traced by
  hand — a drawn Bahn or letter boundaries he corrected — into a local,
  gitignored tree, exactly as the follower reads it: the crop, its ink mask
  and the entry's own fields beside the shaped slots its `letter_spans` index
  into. It answers the author's own addition to Q4 („die hand nachgefahrenen
  linien dienen auch als trainingsmenge"): a Bahn he drew is not only a
  corrected record, it is the material the follower learns from. The status
  filter comes from the archive read and nowhere else — the strip listing
  carries no status — so a withdrawn Fassung never travels, and one withdrawn
  after an export leaves the tree on the next run.
- **`trainingssatz --ziehen <key>` draws the split once, and refuses a
  second time.** Two separate Rückhaltemengen (author decision of
  2026-09-20, which answers FM3 of the Freigabe-Maschine in the same
  direction): `rueckhalt-folger` for measuring a follower improvement,
  `rueckhalt-freigabe` for a hand's release check, the rest `uebung`. The
  unit is the STREIFEN, because every Fassung of one is a repetition of the
  same words and its boxes were written in one stroke — splitting inside one
  would put near-identical writing on both sides of the line. Membership is a
  pure function of key, hand and strip id, drawn over the strips of the FROZEN
  plan, so it needs neither the network nor a single Bahn and is best fixed
  before the first one exists: a strip appended by a later `pool` wave then
  falls where that key would always have put it, joins the record with its
  date and is named by the run. The record lives in the Kartei, which every
  archive snapshot copies in full, and it is the one thing here that is not
  regenerable — so the draw prints the snapshot command, and both commands
  read the archive before concluding that a hand was never drawn: `sync
  --from` pushes an archived Kartei up to the API and never writes the local
  one, so a lost data root would otherwise look exactly like a fresh hand.
  Pre-registration: `messjournal.md` §14 „Trainingssatz `sep20`".
- **The export tree is pinned apart from the benches.** Its root is outside
  every `tools/*/fixtures` root and carries no `fixtures` in its name, its
  manifest is deliberately not called `manifest.json` — which is what the lab
  loaders glob for one level down — and `tests/test_eigenhand_trainingssatz.py`
  pins all of it, including the gitignore rule and a lab loader pointed at the
  tree finding nothing. A strip has no reference trace, so a number measured
  against a drawn Bahn is not a bench number (`core/eigenhand/pfad.py`;
  eigenhand-erfassung.md §12, Prüfstein 2), and a fixture-shaped tree beside
  the bench roots is how that gets forgotten. The export also refuses a target
  inside the checkout that the one gitignore rule does not cover, and a second
  hand in the same `--out`.

### Changed

- **FM3 of the Freigabe-Maschine is decided: (b), two separate hold-out
  sets.** `docs/proposals/freigabe-maschine.md` §10 recommended one set for
  both the follower and the release check; the author decided against that on
  2026-09-20. The question is struck from its Stand block, and with it the
  hard ordering constraint „FM3 before Schritt 4": the draw runs over the
  frozen strip plan rather than over a harvest, so it hangs on no step.
