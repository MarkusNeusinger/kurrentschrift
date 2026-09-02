### Added

- **A test now guards the public history against reserved-data leaks.**
  `tests/test_reserved_history.py` walks every blob ever committed outside
  the code trees and fails on any that carries a render payload — a payload
  key AND a long run of numbers, so prose or a generator script that merely
  names a field does not fire. Known blobs are pinned by content hash, never
  by path: a path exemption would wave through a NEW dump written to the same
  place, which is the mistake being guarded against. `data/` is scanned like
  anything else — it holds data by definition and is the likeliest home for
  such a file. It covers every reserved wire shape, not just templates:
  occurrences (`anchors`, `half_widths`, `strokes`) and aggregates
  (`cluster_center`, `connector_center`) too. Only a missing `git` or a
  shallow clone lets it skip; an error from `rev-list` or `cat-file` fails it,
  because a guard that skips on its own errors keeps CI green without ever
  looking. Two batched `cat-file` calls put the whole sweep at about three
  seconds (#NNN).

### Changed

- **The reserved blob in the public history is accepted, not purged**
  (author's decision, 2026-09-02). `.design-sync/previews/_writtenGlyphData.ts`
  — added 2026-06-20, untracked again 2026-07-31, never removed from history —
  stays. Rewriting a public `main` would not unmake the copies that clones and
  forks already hold, so a purge lowers findability at the cost of breaking
  every existing clone; the README reservation remains the legal boundary
  either way, and what is actually prevented is the repetition. The reasoning,
  the blob's identity and the net that enforces it are in
  `docs/reference/quellen-und-rechte.md` §5, and `/audit-licenses` now reports
  it as settled instead of re-raising it (#NNN).
- **Four further payload blobs surfaced, and were accepted too** (author's
  decision, 2026-09-03, same reasoning). The 2026-09-02 audit had set
  `mvp/canonical/*_v0.json` aside as "0.9–1.1 KB hand seeds"; measured, they
  are 6.5–53 KB carrying 50 `pixel_anchors` plus `half_widths_px` each — the
  same class of authored geometry as the first blob, not stubs. The error
  only showed once the net checked content instead of trusting a size (#NNN).
