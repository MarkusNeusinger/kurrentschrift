<!--
Dependabot bumps ignore this template — the changelog gate skips them by author
and their versions are what the release notes leave out anyway.
-->

## Summary

<!-- 1-3 bullet points: what changed and why. -->

-

## Test plan

<!--
How was this verified? Name the verify skill that matches what the diff touches:
app/ -> /verify-frontend · api/ -> /verify-api · core/ or tests/ -> /verify-core ·
alembic/ -> /verify-migrations (BEFORE the shared DB sees a revision) ·
docs/ or CLAUDE.md -> /write-docs · data or licenses -> /audit-licenses.
-->

- [ ]

## Checklist

- [ ] Changelog fragment added under `changelog.d/<slug>.md` (never a bullet in
      `CHANGELOG.md` itself), or the PR carries the `skip-changelog` label
- [ ] Any new Fachbegriff, metric or named failure mode has its entry in
      `docs/reference/glossar.md` (themed section + alphabetical Schnellindex)
- [ ] The matching `/verify-*` skill was run for what this diff touches
- [ ] Documentation that owns the changed behaviour is updated in the same PR
      (a `/write/*` route -> `docs/reference/write-api.md`, a metric ->
      `docs/reference/qualitaetsmetrik.md`, a migration -> its revision file)

<!--
Add `Fixes #N` below when this PR closes an issue — the closing keyword belongs
in the body, not only in the title.
-->
