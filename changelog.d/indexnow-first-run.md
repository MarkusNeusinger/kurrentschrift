### Fixed

- **The IndexNow workflow survives its first run.** Three findings from the
  rollout in both repos: IndexNow verifies a new key file asynchronously and
  answers `403 SiteVerificationNotCompleted` for a while — the submission is
  now retried for up to ten minutes before the run fails visibly; the
  submission body goes through a file instead of a command-line argument (ten
  URLs fit either way, but anyplot's full sitemap did not: ~260 KB against
  Linux's 128 KB cap per argument, and curl never ran); and the key-file
  readiness probe records the real HTTP status — curl already prints `000` on
  a transport failure, so the previous `|| echo 000` logged `000000` (#494).
