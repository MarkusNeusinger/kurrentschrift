### Added

- **Übergabekarte: the local step that is due, shown instead of hidden.** The
  Eigenhand Bestand now carries a block „Am Rechner weiter" — one card per
  step the server can see is open, with the title, the doctrine reason, the
  command in monospace with its REAL parameters and a copy button, „Danach
  hier: …" and the order hint. Which cards are due is decided once and
  server-side (`core/eigenhand/faellig.py`, Phase 1: fetch the standing setup ·
  push the Übergangsraum weights · pull the OLDEST outstanding Bogen, with any
  further open ones named beside it so an abandoned sheet cannot hide the one
  just printed · sync the
  strip images that never came up); the list rides on the existing Bestand read
  as `faellig`, so there is no new route and no second request to keep in sync.
  The commands are built in Python beside the rules because a command is code;
  the German copy lives in the locale keyed by the rule id, and an id this
  bundle does not know renders no card rather than a blank one. A card is
  invisible while nothing is due, and it shows only what the server SEES — a
  snapshot or a local ingest leaves no trace in the database and is named in
  the order hint instead of pretended to be confirmable.
- **`report --faellig`: the same list, printed at the machine.** The
  clipboard does not reach from the tablet to the writing machine, so the
  Bestandsbericht gains the terminal twin of the cards: it asks the server
  (`--api`/`--token` through the existing admin client, never the database) and
  prints the due commands in the server's own order. Deliberately the ONE mode
  of this tool that reads the API — a due list answers „what has not reached
  the server yet", which read locally would always look done — while every
  other mode stays fully offline and makes no HTTP call at all.

### Changed

- **The four standing terminal hints in the Eigenhand views became state.**
  `setup --pull` under the setup panel (shown on every hand, saved row or not),
  the `pull --sheet` line under the print result (gone after a reload, while
  the Bogen stayed outstanding for days), the `universe --push` command in the
  Quoten panel and the `sync --mit-streifen` line under an empty strip list
  (all-or-nothing, never „4 of 37") are now cards that appear because a state
  is open and disappear when it closes. The panels still say WHAT is missing
  and where the step stands, so the same step is no longer stated in two
  places. The sentence that carried a command with „…" instead of the strip
  and Fassung is now a card at the Fassung itself, with the real ids — and it
  copies the dry run: pushing what was written up is the point of the chain, so
  a card may hand over a write, but never one that REPLACES what is there.
  `pfad --apply` stays in the order hint behind the snapshot that belongs in
  front of it, and `universe --push` — the one eigenhand write that overwrites
  an existing build — names that snapshot too.
