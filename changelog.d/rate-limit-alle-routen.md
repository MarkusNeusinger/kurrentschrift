### Security

- **The rate limit now covers every route, not only the compose path.** A
  second, much wider token bucket per client (600 requests per minute, burst
  120, `PUBLIC_RATE_LIMIT_PER_MIN`) sits in front of the whole API — GET and
  HEAD included — beside the narrow one that guards `/write/word*` (60/min,
  burst 20). The narrow bucket left the rest of the surface open: `/write/glyphs`
  batches up to 80 keys, every catalogue read hits the DB, and nothing stopped a
  script from walking the API in a loop and running up the bill or saturating
  the three instances (owner decision, 2026-09-02). Both are checked by one
  middleware, narrow first, so a request the narrow bucket refuses does not also
  spend a wide token, and the 429 names the limit the caller actually broke.
  A middleware rather than route dependencies because a dependency reaches only
  the routes it is written on, runs after routing (so a flood of 404s would cost
  nothing to produce), and never sees HEAD — which must spend a token exactly
  like the GET it stands for, or the limit is one header away from being evaded.
  `/health` stays exempt so throttling a busy client can never turn into a
  failing uptime probe, and `/seo-proxy/…` stays exempt because every
  prerendered crawler page arrives through the site's nginx and therefore shares
  ONE key — a bucket there would throttle the entire crawler funnel and the
  daily bot-serving guard as if they were a single abusive client. Measured
  against a local server: 40 parallel reads of a cached route stay 200; 700
  requests fired in 2 s give 130 × 200 and 570 × 429, the first refusal on
  request 121, exactly the burst. Nothing about a 200 changes — the limiter
  counts at the origin, so edge-cached responses never reach it and only cache
  misses spend a token, and no header, `Vary` or cache class of a response it
  lets through is touched (#NNN).
