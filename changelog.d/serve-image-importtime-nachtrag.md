### Changed

- **The one measurement the serve-image note left open, taken — and it confirms
  the verdict.** #523 measured the API's import graph in the working venv, which
  carries the `dev`/`test`/`viz` extras the image never sees, and named the open
  item: run the sets inside the Cloud Run image. There is no container runtime on
  the measuring machine and a build submission is not a measurement budget, so
  the next honest thing was built instead — a venv shaped like the image
  (`uv sync --frozen` with no extras, `UV_COMPILE_BYTECODE=1`, `compileall` over
  `api`/`core`/`alembic`, the same lockfile), sets interleaved rather than
  blocked, min of 31. `import api.main` reproduces to the millisecond (911 against
  910), the whole trace half costs **52.7 ms of 911 ms**, and a new
  `-X importtime` split puts it at **34.9 ms of 791 ms of self time — 4.4 %**.
  The split also shows what the estimate never looked at: the web/DB/API frame is
  **47.9 %** of the import, and `api.routers.eigenhand` alone (64.9 ms) costs more
  than `scipy.ndimage` and scikit-image together. The extras turned out not to
  matter, the conclusion stands, and nothing was moved — the note carries the
  dated addendum.
