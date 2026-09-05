### Added

- **The import weight of `api.main`, measured inside the real image on every
  PR.** Both serve-image rounds closed on the same gap: their numbers came from
  a venv shaped like the image, never from the image. The CI job „Image (build +
  container smoke)" already builds `api/Dockerfile` and loads it into the local
  daemon, so one `docker run` now pipes `.github/scripts/importtime_report.py`
  into the image's own interpreter and prints the total (min of 5 fresh
  interpreters), the ten most expensive modules by self time, and the
  SERVE-vs-BOTH split using the module sets the 2026-09-04 note fixed verbatim.
  BLAS threads pinned, ~17 s, and **output only** — a threshold on a shared
  runner would be noise with a veto, and the number is for a later round to
  quote. The script travels over stdin because the image deliberately does not
  ship `tools/`.

### Fixed

- **`api.routers.eigenhand` was never the most expensive module — that was the
  garbage collector.** The 2026-09-05 note put it at the top of the import graph
  with 64.9 ms of self time, "more than `scipy.ndimage` and scikit-image
  together", and left the cause open. Measured against `gc.disable()`, the module
  costs **15.1 ms** while every neighbour holds its number: two thirds of it is a
  generation-2 collection that falls due inside its body, and `-X importtime`
  bills every pause to whichever import it interrupts. The whole import pays
  71 ms to the collector and half of that lands on this one module, purely
  because it is the fifth router imported and registers 17 routes in a row — a
  throwaway route registered first moves the block elsewhere. What remains is
  0.89 ms per route against `api.routers.templates`' 1.00 ms: the biggest router,
  not the most expensive one. Nothing to defer, nothing changed; the finding is
  its own dated note, including the lesson that a single `-X importtime` self
  time is not a statement about a module until the GC pauses are measured out.
