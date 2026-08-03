---
name: write-docs
description: Conventions and checklist for writing or updating the internal design docs under docs/ — German language rules, where a new doc goes, keeping docs/index.md and the CLAUDE.md/copilot-instructions pair in sync, and what is settled (verworfen) and must not be re-litigated. Use when asked to write, add, update, or restructure documentation, concepts, or reference docs.
---

# Write or update the internal docs

`docs/` is the design source of truth — decisions live there, code
follows. There is no build step: plain Markdown, read in the repo/on
GitHub. Nothing to launch; this skill is the editing contract.

## Language (strict, from `docs/reference/sprachregelung.md`)

- Docs under `docs/`: **German** (deliberate — the domain is German).
- Code samples inside docs: English identifiers, like all code.
- README + GitHub-facing text: English.
- German technical terms keep their German name in prose (Schwellzug,
  Lineatur, Ductus); in code they get an English identifier plus one
  explanatory comment.
- Glyphs are data, not code: schema keys English, values the actual
  characters (`ſt`, `a-medial`).

## Where a new doc goes

```
docs/
├── concepts/     # Architektur, Philosophie, getroffene Entscheidungen
├── reference/    # Nachschlage-Dokumente (Stack, Regeln, Pipelines)
├── schriftkunde/ # Quellengestützte Faktenblätter zu den Schriften
├── notes/        # Operativer Zustand, Journale (z. B. stifte-fuer-unterwegs)
└── proposals/    # Offene Vorschläge, noch nicht entschieden
```

Checklist for adding or renaming a doc:

1. Pick the layer: settled decision → `concepts/`, look-up material →
   `reference/`, source-backed script facts → `schriftkunde/`,
   operational state → `notes/`, not-yet-decided → `proposals/`.
2. **Add it to the Quick-Links table and the structure tree in
   `docs/index.md`** — all five layers are indexed there (the tree
   plus a prose section per layer, incl. `notes/`); keep both in sync
   with the file system.
3. If it records a decision, include a „Verworfen“ section for the
   rejected alternatives — that is what makes the decision binding
   (see below).
4. Give it a status blockquote directly under its H1 (see „Status headers“
   below) — a new doc without one is incomplete. The only exception is a
   `schriftkunde/` factsheet, which stays header-free and carries its own
   „Stand:“ line instead. If the status is `lebend`, also add the file and
   its update trigger to the table in `docs/index.md` § „Dokument-Status“.

## Status headers (the lifecycle duty)

Every doc under `docs/` opens with one status blockquote directly below its
H1 — always the same shape, always an absolute date:

```markdown
> **Status (2026-08-03): teil-umgesetzt.** <one or two sentences: what is
> built, with PR/migration evidence.> <what is still future, or what must be
> pulled along when the code changes.>
```

Vocabulary (small on purpose — do not invent new words):

| Status | Meaning |
|---|---|
| `bindend` | Settled decision; changes only via a new decision, Verworfen lists stay closed. |
| `lebend` | Describes the current code and carries a **named** update trigger. |
| `teil-umgesetzt` | Part is built, the rest is explicitly future — the header says which. |
| `umgesetzt-historisch` | Fully worked off or superseded — decision/measurement record, not a plan. |
| `offen` | Nothing of it is built. |
| `Befund-Journal` | Dated snapshot; never continued, only replaced by a new round. |
| `statisch` | Source-backed look-up material that does not follow the code. |

Rules:

1. **Implementing part of a proposal updates its header and its status tag in
   `docs/index.md` — in the SAME PR as the code.** A shipped stage that still
   reads „offen“ is how a reader plans work that already exists.
2. **A new proposal starts at `offen`** and gets its entry (plus tag) in the
   index in the same commit.
3. **Absolute dates only** in the header — bump the date whenever you touch
   the status, never write „aktuell“ or „zuletzt“.
4. The `schriftkunde/` factsheets stay header-free: the „Dokument-Status“
   section in `docs/index.md` covers that layer as a whole (they carry their
   own „Stand:“ line). The one exception is `orthographie-regeln.md`, which
   documents rules that are not implemented yet.
5. `docs/contributing.md` keeps an **English** header — it is the
   `sprachregelung.md` §1 exception (linked from the README); all other
   headers are German like the docs they sit in.
6. When a status flips to `lebend`, add the file and its trigger to the table
   in `docs/index.md` § „Dokument-Status“; when it stops being `lebend`,
   remove it there.

## New terms go in the glossary (same PR)

`docs/reference/glossar.md` is the one place a reader looks up a term they
met in a doc, an issue, a PR or the admin UI. It only works if it does not
lag behind the prose that coins the words.

**Rule: any doc or PR that COINS a new Fachbegriff, metric, named
constant-with-a-story or repo idiom adds its glossary entry in the SAME
change.** Coining includes: naming a new measurement (`gen_chamfer`,
`doff`), naming a failure mode („degenerierte Solves“, „Cusp-Connector“),
naming a stage or gate („like-for-like Gate“, „Vereinfachungs-Gate“), and
renaming an existing concept.

Entry shape (German prose, English identifiers as-is):

```markdown
**Begriff** *(English twin, if one exists)* — one to three sentences that
assume no prior knowledge. *Technisch:* the formula name, the module or
constant it lives in (`core/fit.py::CONVERGED_GEO_RMSE_UNITS`), enough
anchor vocabulary that pasting the entry into any AI chat lets the reader
dig deeper. → owning-doc.md §n
```

Then: put the term into the alphabetical Schnellindex at the top of the
glossary, and file it under the right themed section (§1 Schrift · §2
Architektur · §3 Mess/Fit · §4 Metriken · §5 Werkbank · §6 Extern). Purely
internal identifiers with no story do **not** belong there — the glossary
is for terms a human meets in prose, not an API reference.

## What is settled

Sections titled **„Verworfen“** (and the recorded style rounds in
`docs/concepts/style-guide.md`) are closed decisions. Editing docs
never means weakening or deleting those; new arguments go to
`docs/proposals/` instead. When a change you're documenting
contradicts a Verworfen entry, stop and surface it to the user.

## Sync duties (the part everyone forgets)

- **`CLAUDE.md` ↔ `.github/copilot-instructions.md` MUST stay in
  sync** — both carry the same domain rules for different agents. If
  a docs change alters anything those files state (layout, milestones,
  rules), update both in the same commit. Quick drift check:

  ```bash
  git diff main -- CLAUDE.md .github/copilot-instructions.md
  ```

- **New terms ↔ `docs/reference/glossar.md`** (see the section above) —
  after writing, sweep your own diff for words a stranger could not
  resolve and check each one is in the glossary:

  ```bash
  grep -o '\*\*[^*]*\*\*' <the-doc-you-changed>.md | sort -u   # your coined terms
  grep -n '<term>' docs/reference/glossar.md                   # is it there?
  ```

- `docs/index.md` quick-links table ↔ the actual file tree. List the
  tree to compare against the index:

  ```bash
  find docs -name '*.md' | sort
  ```

- **When a concept, § number, or term changes, sweep the whole doc
  surface for the old form** — don't rely on remembering which docs
  cite it (a targeted edit once left contributing.md, datenablage.md
  and orthographie-regeln.md stale until the user asked). Explicitly
  include `proposals/` and `notes/`:

  ```bash
  grep -rn '<old term or § number>' docs/ CLAUDE.md .github/copilot-instructions.md README.md
  ```

- Anything touching `/data` or licensing must agree with
  `docs/reference/quellen-und-rechte.md` + `docs/reference/datenablage.md`
  — and remember the hard rule: Süß' Lehrbuch and similar copyrighted
  works never enter the repo — not as scans, not as redrawn glyphs,
  not as derived images; bibliographic references in prose are fine.

## Gotchas

- **Relative dates rot.** Docs under `notes/`
  are state journals — write absolute dates (2026-06-10), never
  „aktuell“ or „letzte Woche“.
- **The architecture doc is sectioned (§1–§17) and other docs cite
  those § numbers** (so do CLAUDE.md and commit messages). Don't
  renumber sections; append.
- **German doc, English identifiers** also applies to file paths and
  schema keys quoted in prose — don't translate `position: "medial"`
  into German inside a German sentence.
