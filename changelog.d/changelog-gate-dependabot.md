### Fixed

- **The changelog gate no longer sits red on every Dependabot batch.** Since the
  fragment rule landed, the CI job „Changelog (fragment)" failed on each of
  Monday's bumps (#468: `no changelog fragment`) — a bot can neither write
  `changelog.d/<slug>.md` nor reach for the `skip-changelog` label, so the one
  way out of the gate was closed to exactly the PRs that have nothing to say.
  The job now skips by PR author (`dependabot[bot]`) the same way it skips a
  labelled PR, because a routine version bump is precisely what the release
  notes leave out anyway; a bump that DOES deserve a line (the peer-dep override
  of #235) still reaches the changelog through the human PR carrying the fix.
