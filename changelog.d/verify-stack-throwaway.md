### Changed

- **`/verify-frontend` can now drive an admin write flow without touching the
  shared database.** A new §1b brings up a throwaway Postgres and a local API
  and SPA in one exported shell, with two preflights — one refusing any
  `DATABASE_URL` outside loopback or a `/var/tmp` throwaway socket, one asking
  the database itself whether it already holds the reserved dataset, because a
  Cloud SQL Auth Proxy puts the shared database on `127.0.0.1` too — a positive
  discriminator (a freshly migrated database has no hand, because no migration
  seeds the reserved dataset), a teardown and the `/dbsnapshot` trap that made
  an almost-empty archive look like safety. Local dev shares one database with
  production, so until now "verified in the browser" either meant a read-only
  click-through or a write into the author's hand-made data; the gap `CLAUDE.md`
  lists as one without a loop now has a recipe, and the guardrail line itself
  follows once the recipe has survived a few PRs.
- **The browser probe finds the local Chromium too.** `cloud-probe.mjs` looked
  only under `PLAYWRIGHT_BROWSERS_PATH`/`/opt/pw-browsers`, which exists in the
  cloud container and not on the machine where the admin is actually clicked —
  so a session without the chrome-devtools MCP had no browser gate at all and
  quietly fell back to "built and type-checked". It now also looks under
  `~/.cache/ms-playwright`, and its default viewports are the three the skill
  names once: 1440×900, 1024×768 (the tablet the author re-traces on) and
  390×844.
- **`/verify-frontend` §3 gained a colour-vision-deficiency pass.** Three
  ordered questions — is hue the only channel, does the mark clear 3:1 against
  its own (white) ground, does each pair survive a deuteranope simulation —
  because the overlay colours are judged against paper while the work surfaces
  are white, and the second red/green pair travels through tokens rather than a
  literal hex.

### Added

- **`.claude/skills/verify-frontend/seed-local-admin.py`, a loopback-only
  seeder for the throwaway stack.** A migrated local database holds the styles,
  the chart sources and the quiz words and nothing else, so the Eigenhand view
  opens empty and no write flow can be clicked. The script prints a Bogen,
  accepts its rows, stores a synthetic strip image per row and follows every
  word, with invented `meta.tintenpfad` numbers spread over a good, a middling
  and a bad word box — including the `0.0` and the `null` that a `||` reader
  gets wrong. Its `--hand` is confined to a reserved `wegwerf-` namespace, so no
  real hand can be named, and it refuses to write when the API reports a hand it
  did not create. It is a skill asset rather than a `tools/` module because
  `tools/` is the measurement layer and writes no database, and nothing it
  writes may ever be measured.
- **`tests/test_seed_local_admin.py` covers the seeder's guards.** They are what
  stands between a mistyped flag and a plain overwrite of the author's hand
  setup, and they are pure enough to test: loopback and remote URLs, a hand
  outside the reserved namespace, a foreign hand that `--reseed` must not talk
  past, a malformed Fassung id, and the reruns that are meant to succeed.
