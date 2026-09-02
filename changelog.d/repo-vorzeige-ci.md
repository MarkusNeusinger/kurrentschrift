### Added

- **CI builds the shipped API image and smokes it before the merge.** A fifth,
  parallel `image` job builds `api/Dockerfile` without pushing (GHA-cached) and
  runs a container smoke that needs no database: `/health` answers, the OpenAPI
  `info.version` must equal the `pyproject.toml` version — the exact assert
  that would have caught the missing `pyproject.toml` COPY of #473, which a
  reviewer found and no gate did — and the files the runtime stage is expected
  to serve or run must be present, pinning the COPY list against a future stage
  rebuild. hadolint runs over both Dockerfiles at threshold `warning` with the
  four current findings named and excepted, so a new warning blocks while the
  deliberate ones do not.
- **The app deploy runs the candidate chain the API already ran.**
  `app/cloudbuild.yaml` deploys with `--no-traffic --tag=candidate
  --revision-suffix=b$BUILD_ID`, smokes the candidate URL (a human UA gets the
  SPA shell, Googlebot gets the prerender marker through `@seo_proxy`,
  `/robots.txt` still carries the Bytespider rule, `/llms.txt` declares a utf-8
  charset) and only then shifts traffic. That service carries the whole crawler
  path in `app/nginx.conf` — the file whose breakage served every bot an HTTP
  502 for four weeks in the sister project — and went live unchecked until now.
- **A code of conduct and a pull-request template.** Contributor Covenant 2.1
  with the same contact address as `SECURITY.md`, and a template naming this
  repo's three actual PR duties: a fragment under `changelog.d/`, a glossary
  entry for a new Fachbegriff, and the matching `/verify-*` skill.

### Changed

- **The bot-serving watcher derives its expectations from the repo.** It checks
  out the repo and reads route and expected `<title>` per page out of the
  committed `app/prerender/*.html` instead of carrying hard-coded literals. All
  11 prerendered pages are covered instead of 4, and a copy change can never
  drift the watcher again. A failure now opens one fixed-title issue (or
  comments on it) and the next green run closes it — the job had
  `permissions: contents: read` and no alarm path at all.
- **Frontend coverage measures the whole SPA source.** `app/vite.config.ts`
  gains a `test.coverage` block (provider v8, `include: ['src/**/*.{ts,tsx}']`
  — Vitest 4's replacement for `all: true`). The reported figure drops from
  82.7 % to the honest 19.2 %, because Vitest was measuring only the modules a
  test happened to import. `codecov.yml` swaps `project: auto` for fixed floors
  per flag so the one-time re-baselining does not red every open PR.
- **Every CI job has a `timeout-minutes` and every action is pinned to a commit
  SHA.** GitHub's 360-minute default let a hung job burn six hours and report
  nothing; the caps sit generously over the measured maximum of 491 s. The
  movable action tags were a write handle into runners that hand
  `CODECOV_TOKEN` to the environment.
- **`:latest` moves only after the promote step** in both cloudbuild files.
  Pushed before the rollout, the tag named an image that a failing migrate or
  smoke may have stopped from ever serving a request.
- **Project metadata says what the project is.** `app/package.json` no longer
  describes the SPA as an admin UI for stylus input, and `pyproject.toml` gains
  trove classifiers and the Documentation/Changelog/Issues URLs.

### Fixed

- **The README described a data model that migration 0017 removed.** It called
  the library unit `(glyph, position, variant)`; the key is `(style, glyph,
  variant)` and the word position has been pure render context since the R2
  position removal. It was the only document saying otherwise.
