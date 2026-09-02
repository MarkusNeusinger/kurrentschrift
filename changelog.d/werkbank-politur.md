### Fixed

- **An unsaved Weg no longer vanishes without a word.** Escape, a backdrop
  click and „Schließen" all went straight through the Einrichten wizard and
  dropped whatever was drawn — the one step in the whole project where manual
  work creates ground truth and nobody else can repeat it. All three now ask
  first, naming what is lost and what is not (everything but the Weg
  live-commits), and even a deliberate discard tucks the strokes into
  sessionStorage so the next opening offers them back.
- **A locked glyph says so before the work, not after it.** Tracing on a locked
  glyph ran to completion and then failed with a literal
  `Error: 423 Locked: glyph 'longs' is locked; pass force=true to overwrite`
  in a blue-grey `info` box. The lock is now a chip in the wizard title and a
  warning on the Weg step, and the failure is red.
- **The workbench answers in German, keeping the server's own line.** All 18
  admin surfaces rendered `String(err)` verbatim; `apiFehlertext` turns a status
  into one sentence that names the next step, with the raw English detail folded
  into a „Technische Meldung" `<details>` underneath — the sentence answers, the
  detail proves. The 404 branches read the typed status instead of sniffing the
  message for "404".
- **„Keine Hand an den Vorkommen hinterlegt" no longer greets a fresh Vorlage.**
  With zero occurrences there is nothing that could name a hand, so the sentence
  blamed an impossible cause on every card; `no-occurrences` is now its own state
  naming the next step (harvest).
- **A join with no authored letters explains itself.** `/admin/uebergaenge?l=x&r=y`
  showed a mute white box although the API reports `missing` — the panel now
  carries the same „fehlend:" chip the word cards have, and a full sentence when
  neither letter exists.
- **„Weg gespeichert." stopped announcing itself on every visit.** The green
  alert stood whenever a canonical existed and nothing was drawn, so opening a
  glyph traced months ago replayed it as fresh news through an assertive live
  region — and stood just as green on a locked glyph. The standing state is a
  quiet present-tense caption now; the event keeps the alert bar.
- **„Tafel öffnen" scrolls the plate into view.** It added ~650px below the fold
  and changed nothing on screen but its own label — on a letter without a crop,
  that button is the only way in.
- **Step 4 no longer sits under a horizontal scrollbar.** A fractional cell width
  rounded up over the edge and clipped „Überlagert", the one cell that answers
  the step's question.
- **Eigenhand: `semicolon` was printed as a word.** The view kept its own copy of
  the key-to-character map and had drifted by two entries; it is derived from the
  glyph registry now, so the class of bug is gone rather than patched. The
  „Quoten" panel also printed its own title as its caption.
- **The Auftragskorb protocol can no longer be re-enacted after a rejection.**
  `check_transition` fell back to the stored fields, so a rejected row — which
  keeps its old `understanding`/`stage`/`resolution` on purpose — accepted a bare
  `{"status":"done"}` and put the just-rejected restatement back in force. Every
  required field is now read from the PATCH alone (`docs/proposals/optimierungs-werkbank.md` §5.1).

### Changed

- **The workbench is reachable by heading and by name.** The three detail views
  had no `h1` at all (their visible head is a ReactNode), nine of ten sliders and
  both chart-zoom buttons had no accessible name, 63 buttons were called „Öffnen"
  with no subject, and the Korb toggle was named after the heading beside it
  rather than its own effect. `ViewHeader` takes a `titleText`, the controls carry
  their labels, and the toggle reports `aria-expanded`.
- **Eigenhand's terminal commands can be copied.** The three shell lines sat
  inside running sentences in a proportional antiqua, where `--`, `-m` and `.`
  are exactly what slips while typing; each is now a monospace block with a copy
  button.
