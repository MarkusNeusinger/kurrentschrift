### Changed

- **What the scientific stack actually costs the API's process start, measured.**
  The 2026-09-02 audit proposed splitting `core/pipeline.py` so `/write` would
  stop dragging scipy, scikit-image and the rest into every start, and put the
  saving at „another ~0.5–0.8 s". The observation holds — all five heavy package
  roots stand in the process after `import api.main` (1540 modules, 637 of them
  from numpy, scipy, scikit-image, shapely and Pillow), and the five
  function-local imports the repo has keep none of those roots out, because
  every root also has a module-level path. The estimate does not hold: the
  render path needs `scipy.interpolate` and `shapely` itself
  (`core/template.py` splines the anchors and unions the silhouette), and
  importing `scipy.interpolate` already brings 355 of scipy's 375 modules.
  Min-of-15 runs with a warm bytecode cache put the trace-only third-party
  extras at **8 ms** and the whole trace half at **46 ms** of a 910 ms import —
  5 % of the import, all of it measured locally, so what it becomes inside the
  container is named as the one open measurement rather than asserted.
  `docs/notes/` carries the sets verbatim, the compressed package sizes, and
  both candidate remedies with their price; no import was moved.
