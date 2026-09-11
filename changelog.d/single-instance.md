### Changed

- **`kurrentschrift-api` and `kurrentschrift-app` run as one instance each.** The
  API goes from max 3 to max 1 with concurrency 30 (was 15), min stays 1; the app
  keeps max 1 and gets concurrency 80 (was 15). The scale-outs were the cold
  starts that min=1 had left: in the ten days to 2026-09-10 every one of the 14
  AUTOSCALING starts was the owner's admin page firing 10–30 calls at once while
  the warm instance sat at a concurrency of 2–3, and Cloud Run pinned one or two
  calls of each burst to a new instance for its full 8–14 s start. With one
  instance a burst queues on the warm one for a few hundred milliseconds; the
  heavy endpoints already run in the request threadpool. The old reasoning that
  max=1 forces a deploy to replace the only instance predates the candidate
  chain: the limit is per revision and the smoke warms the candidate before
  traffic moves. Owner decision 2026-09-11, mirrored in anyplot. (#593)
