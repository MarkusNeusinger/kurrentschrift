### Changed

- **What the scientific stack actually costs the API's process start, measured.**
  The 2026-09-02 audit proposed splitting `core/pipeline.py` so `/write` would
  stop dragging scipy, scikit-image and the rest into every start, and put the
  saving at „another ~0.5–0.8 s". The observation holds — nothing is deferred,
  and `import api.main` loads 1540 modules, 637 of them from numpy, scipy,
  scikit-image, shapely and Pillow — but the estimate does not: the render path
  needs `scipy.interpolate` and `shapely` itself (`core/template.py` splines the
  anchors and unions the silhouette), and importing `scipy.interpolate` already
  brings 355 of scipy's 375 modules. Min-of-15 runs with a warm bytecode cache
  put the trace-only third-party extras at **8 ms** and the whole trace half at
  **46 ms** of a 910 ms import — 0.5 % of a p50 cold start. `docs/notes/`
  carries the numbers, the compressed package sizes, and both candidate
  remedies with their measured price; no import was moved.
