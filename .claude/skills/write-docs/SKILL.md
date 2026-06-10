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
├── concepts/    # Architektur, Philosophie, getroffene Entscheidungen
├── reference/   # Nachschlage-Dokumente (Stack, Regeln, Pipelines)
├── notes/       # Operativer Zustand, Journale (z. B. deploy-bootstrap-status)
└── proposals/   # Offene Vorschläge, noch nicht entschieden
```

Checklist for adding or renaming a doc:

1. Pick the layer: settled decision → `concepts/`, look-up material →
   `reference/`, operational state → `notes/`, not-yet-decided →
   `proposals/`.
2. **Add it to the Quick-Links table and the structure tree in
   `docs/index.md`** — with one exception: `notes/` is deliberately
   outside the index tree (research/state material, referenced in
   prose only); only `concepts/`, `reference/` and `proposals/` docs
   get index entries.
3. If it records a decision, include a „Verworfen“ section for the
   rejected alternatives — that is what makes the decision binding
   (see below).

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

- `docs/index.md` quick-links table ↔ the actual file tree. List the
  tree to compare against the index:

  ```bash
  find docs -name '*.md' | sort
  ```

- **When a concept, § number, or term changes, sweep the whole doc
  surface for the old form** — don't rely on remembering which docs
  cite it (a targeted edit once left contributing.md, datenablage.md
  and orthographie-regeln.md stale until the user asked). Explicitly
  include `proposals/` and `notes/` even though they're outside the
  index tree:

  ```bash
  grep -rn '<old term or § number>' docs/ CLAUDE.md .github/copilot-instructions.md README.md
  ```

- Anything touching `/data` or licensing must agree with
  `docs/reference/quellen-und-rechte.md` + `docs/reference/datenablage.md`
  — and remember the hard rule: Süß' Lehrbuch and similar copyrighted
  works never enter the repo — not as scans, not as redrawn glyphs,
  not as derived images; bibliographic references in prose are fine.

## Gotchas

- **Relative dates rot.** Docs like `notes/deploy-bootstrap-status.md`
  are state journals — write absolute dates (2026-06-10), never
  „aktuell“ or „letzte Woche“.
- **The architecture doc is sectioned (§1–§17) and other docs cite
  those § numbers** (so do CLAUDE.md and commit messages). Don't
  renumber sections; append.
- **German doc, English identifiers** also applies to file paths and
  schema keys quoted in prose — don't translate `position: "medial"`
  into German inside a German sentence.
