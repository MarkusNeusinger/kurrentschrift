---
name: release
description: Cut a release — preview the pending changelog section, fold the fragments with tools.changelog release, ship the version bump as a PR, then after the merge tag the merge commit and publish a GitHub release whose notes are the section CONDENSED, never copied. Use when asked to cut, prepare or publish a release, bump the version, tag a version, or write release notes.
---

# Cut a release

The changelog fold, the version bump and the tag are one procedure with a
tool doing the mechanical half. What is NOT mechanical is the GitHub release
text: it is the changelog section condensed, and that rule (author,
2026-08-28) is the reason this skill exists rather than a one-liner.

Version numbers are product communication, not library SemVer. The project
has been walking minor versions (`v0.27.0` on 2026-08-28) for feature
batches; patch for fix-only rounds.

## 1 · See what is pending

```bash
uv run python -m tools.changelog preview
```

This prints `[Unreleased]` exactly as the cut would write it — the fragments
under `changelog.d/` folded newest-first within each category. Read it as
the release's table of contents and sanity-check it against the merges since
the last tag:

```bash
git fetch origin
git log v<last>..origin/main --oneline --no-merges
```

Anything notable that no fragment covers is a missing fragment: add it to
`changelog.d/` first, then preview again. Do not write bullets into
`CHANGELOG.md` by hand — that is the shared line every sibling merge used to
conflict on, and the CI job refuses it.

## 2 · Cut it on a branch

Never on `main`. Branch first (`release/vX.Y.Z`), then:

```bash
uv run python -m tools.changelog release X.Y.Z --title "…" --dry-run   # look first
uv run python -m tools.changelog release X.Y.Z --title "…"
```

One command does all of it: folds the fragments under the new version
heading, bumps `pyproject.toml` (`project.version` — `/docs` reads it at
runtime), `uv.lock` and `CITATION.cff` (`version` + `date-released`), and
deletes the fragments. `--dry-run` prints the plan and the new section
without writing.

The title is the release's theme, a short phrase — it appears in the
changelog heading and again in the GitHub release title, so pick it once
(`v0.27.0` used "Lotse + chain v5 in the tracing duel, the Eigenhand capture
chain, the site opened to machines").

Then ship it through `/open-pr` like any other change. The diff should be
exactly the changelog fold plus the three version files. **The release PR
itself needs no fragment** — it consumes them.

## 3 · After the merge: tag and publish

Both steps happen on the MERGE commit, so they wait for the author's merge.

```bash
git fetch origin
git tag -a vX.Y.Z <merge-sha> -m "vX.Y.Z — <title>"
git push origin vX.Y.Z
```

Then the GitHub release, from a notes file (never a shell-quoted body):

```bash
gh release create vX.Y.Z --title "vX.Y.Z — <title>" --notes-file <file>
gh release view vX.Y.Z                                   # verify it rendered
```

## 4 · The notes are CONDENSED, never copied

The full text stays in `CHANGELOG.md`; the release page is the index into
it. The shape (author rule, 2026-08-28):

- an **intro line**: the merge count, the PR range, and a link to
  `CHANGELOG.md`;
- **the section's own headings**, unchanged;
- **one bullet per NOTABLE entry** — chores, dependency bumps and small
  fixes are left out, and there is no fixed count;
- **at most two lines each**: the bold title, one clause carrying the
  essence or the headline number, the PR reference;
- a **compare link** at the end.

Copying the section verbatim is the failure this rule names. So is padding
it to a fixed number of bullets.

## Gotchas

- **Never merge the release PR yourself** — the author merges live, as with
  every PR. Tag and publish only after the merge actually landed.
- **Tag the merge commit, not your branch tip.** A squash merge creates a
  new commit; tagging the pre-merge head points the release at a commit that
  is not on `main`.
- **The fragments are deleted by the cut.** If the command runs and the PR
  is then abandoned, restore them with `git checkout` rather than rewriting
  them from the folded section.
- Catching up on releases that were never cut: tag the historical boundary
  commits, then `gh release create` them oldest first, so the "Latest" badge
  ends up on the newest.
