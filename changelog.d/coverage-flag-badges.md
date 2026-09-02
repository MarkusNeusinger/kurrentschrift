### Changed

- **The README shows coverage per flag instead of one blended number.** The
  single codecov badge reported a repo total that mixed a well-tested backend
  with a barely-tested SPA; since the frontend re-baseline it would have read
  as one uninformative middle figure. Two flag badges — backend (`core/` +
  `api/`) and frontend (`app/src/`) — say which half is which, so the strong
  number is not diluted and the gap is named rather than averaged away
  (audit question F8, author's decision).
