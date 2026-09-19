### Fixed

- **The word detail shows a Wortprobe that carries no trace yet.** The detail
  of `/admin/woerter` built its list from the stored `word_instances`, so a
  sample the harvest never traced answered the overview's own deep link into
  it with „keine nachgefahrene Wortprobe" — no crop, no occurrence boxes, no
  way into the editor, in the one place where that tracing is done. The list
  is now built from the plate's word SAMPLES, each paired with its stored
  trace where one exists, and the spine card draws the trace-only parts (pen
  path, Herkunft, fit chips, Abstandsprofil) only where there is a trace
  instead of vanishing with it. A sample from another writer's plate (Abb. 22)
  says so on its own chip and is counted under its own name, never into this
  hand's numbers and never offered the editor — it stands as context, which is
  all it may ever be. An Abb.-20 pair drill of the same two letters stays in
  the Übergänge view unless it already carries a trace.

### Changed

- **The word editor opens on an untraced Wortprobe, seeded.** It is handed a
  starting row in the shape it already takes — identity and registration
  frame off the sidecar, slot labels from the shaper, no strokes — so the
  tested write flow is called rather than rebuilt: the same props, the same
  single-item `PUT`, and the first authored trace of a specimen simply
  creates its row, which the server has always accepted. The hand comes from
  the source's own occurrences, with `sources.hand_id` behind it; where
  neither resolves, saving stays disabled with the reason on screen rather
  than writing under a guessed writer.
- **The word detail counts „n Bahnen" beside „n Wortproben".** „Beleg" is the
  Eigenhand Bestand's counting unit and was doing double duty as the name for
  a plate trace (author decision 2026-09-18, Q8 a). The head of the detail now
  says how many samples this hand has of the text and how many of them already
  carry a stored Bahn — the gap between the two is the work that is left — with
  a foreign writer's samples on a third chip of their own. Only this chip is
  renamed, and **Bahn** enters the glossary with it.
