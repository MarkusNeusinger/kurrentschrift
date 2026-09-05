### Security

- **The Content-Security-Policy is enforcing.** The header is
  `Content-Security-Policy` instead of `Content-Security-Policy-Report-Only`;
  the directive string is byte-identical, `report-uri` included, so a source
  that is actually blocked still reports and `api/routers/csp.py` keeps
  logging the `disposition` that separates an enforced block from a watched
  one. The switch is five days earlier than the week the file planned, and it
  rests on what the report channel said rather than on confidence: Report-Only
  since 2026-09-02, 40 hours of it on the nonce path, produced no report from
  the site's own code — only the deliberate probe, and once two reports from a
  single client whose injected Cloudflare JavaScript Detections script had not
  been stamped, where every fetch since shows all five script tags including
  Cloudflare's carrying the header's nonce. Under enforcement such a client
  simply does not run Cloudflare's bot script, and the page is unaffected. What
  a report channel cannot see was read out of the code instead: no Workers, no
  WebAssembly, no `eval` and no `new Function`, and `createObjectURL` only for
  downloads and images, which `blob:` in `img-src` already allows. The sister
  site has run the same policy enforcing since 2026-09-04 without a report of
  its own.

- **The rollback is written down where the switch is.** `app/security-headers.conf`
  now carries both halves: rename the header back and deploy, or — faster than
  a build — put the traffic back on the previous Cloud Run revision with
  `gcloud run services update-traffic`. `tests/test_csp_policy.py` gained the
  check that pins which of the two names the repository is shipping, so the
  file can never quietly disagree with what the edge serves.
