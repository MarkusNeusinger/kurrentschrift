### Security

- **The direct `*.run.app` address no longer bypasses the edge.** Both Cloud Run
  services stand with `ingress=all` — there is no load balancer, and one would
  cost more per month than the project — so the API answered on two addresses,
  and everything Cloudflare enforces (the rate-limiting rule, the WAF, the
  cache) was one URL away from being skipped; the 2026-09-02 audit measured a
  `run.app` response without a single `cf-` header. A Cloudflare Transform Rule
  now stamps `X-Origin-Secret` onto every request it proxies for
  `api.kurrentschrift.ink`, and `api/origin_gate.py` answers everything else
  with 403 — before the rate limiter, before `require_admin`, before any
  database query. It is not authentication: the header says "you came through
  the front door", nothing about who you are, and `api/auth.py` still decides
  what a caller may do. **Unset means off**: without `ORIGIN_SECRET` in the
  Cloud Run environment the check is inert, which is what lets the code ship
  before the rule and the secret exist and is also the rollback — remove the
  variable, no deploy needed. `/health` stays exempt because the deploy's
  pre-traffic smoke probes the candidate revision on its `run.app` tag URL,
  which by definition never passes the edge, and `/seo-proxy/…` stays exempt as
  belt and braces on the crawler path. `/health` also reports `origin_gate`
  (`off` · `off-seen` · `ok` · `missing` · `mismatch`, never the value), so
  every route into the service — the `api.` host, the apex `/api/*` behind
  Cloudflare Access, the site's nginx, the raw `run.app` — can be checked
  BEFORE the gate is armed: with the Transform Rule live but the gate still
  off, each path that must keep working has to answer `off-seen` first.
  Break-glass over the direct URL now needs both `X-Admin-Token` and the origin
  header; both live in Secret Manager (#NNN).

### Changed

- **The deploy smoke carries the origin header, and checks that it is the right
  one.** `api/cloudbuild.yaml` reads `ORIGIN_SECRET` from Secret Manager inside
  the step rather than through `availableSecrets`, which resolves at build start
  and would fail every build until the secret exists. A missing secret or a
  missing `secretAccessor` leaves the probes bare — correct while the gate is
  off, and loud at the first `/styles` once it is on. The smoke additionally
  asserts that the secret the BUILD can read is the one the SERVICE was given,
  so a rotation applied to only one side surfaces there instead of as a
  mysterious 403 after the promote. The deploy also switched from
  `--set-secrets` to `--update-secrets`: the former replaces the whole binding
  set and would have stripped the hand-attached `ORIGIN_SECRET` from every
  revision the pipeline creates, silently disarming the gate on the next deploy
  (#NNN).
