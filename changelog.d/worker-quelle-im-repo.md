### Added

- **The Cloudflare Worker in front of the admin route is in the repo.** The
  apex `kurrentschrift.ink/api/*` reaches the API through a Worker
  (`kurrentschrift-api-proxy`) that existed only in the Cloudflare dashboard:
  nothing in the repo said it was there, what it did, or that the whole admin
  UI depends on it. `infra/cloudflare/kurrentschrift-api-proxy.js` is now its
  source — a mirror of the deployed bytes, so a `diff` against the running
  script stays meaningful — beside a README with the route, the `secret_text`
  binding, `compatibility_date`, both deploy paths (dashboard and the multipart
  script `PUT`) and the `off`/`off-seen`/`ok` measurement that verifies a path
  before the origin gate is armed (#NNN).

### Fixed

- **The origin gate's documentation said the admin route was covered by the
  Transform Rule. It was not.** A Worker subrequest to a host in the SAME zone
  skips that zone's Transform Rules, so the rule that stamps `X-Origin-Secret`
  for `api.kurrentschrift.ink` never reached the `fetch()` inside the Worker —
  `/api/health` still answered `off` after the rule went live. The Worker now
  stamps the header itself from a secret binding (`off-seen`, then `ok` once
  armed), and `frontend-stack.md` §5 records the finding instead of the
  assumption. This is what the `off-seen` verdict was built for: the measurement
  caught it before arming the gate could have taken the admin down (#NNN).
