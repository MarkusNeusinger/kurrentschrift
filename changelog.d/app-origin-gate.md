### Security

- **The site container has an origin gate too, and it ships switched off.**
  `api/origin_gate.py` closed the API service's direct `*.run.app` door and
  named the app service's as the one it could not close from its own side:
  `kurrentschrift-app` stands with `ingress=all`, serves the whole site from
  its raw Cloud Run URL with no bot challenge, no WAF and no rate limit, and
  relays any crawler user agent through `@seo_proxy` to
  `api.kurrentschrift.ink` — where the edge stamps the API's secret
  legitimately, so the API gate cannot tell. `app/origin-gate.conf.template`
  is the nginx half of the same mechanism: same secret, same five verdicts
  (`off` · `off-seen` · `ok` · `missing` · `mismatch`), rendered at container
  start by the base image's own `20-envsubst-on-templates.sh`. Nothing is
  armed by merging it — the image defaults `ORIGIN_GATE=off`, the service
  declares no environment variables, and `/_health` already reports
  `X-Origin-Gate`, so every route into the container can be measured before
  anything is switched on. The runbook is `infra/cloudflare/README.md`
  § "The site's own origin".
- **Both callers that legitimately skip the edge now stamp their own header.**
  The pre-traffic smoke in `app/cloudbuild.yaml` reads `ORIGIN_SECRET` from
  Secret Manager inside the step (not through `availableSecrets`, which
  resolves at build start and would fail every build until the secret exists)
  and asks `/_health` for the verdict before any content probe, so a
  wired-up-wrong secret is reported as itself rather than as a mystifying 403
  on the home page. `.github/workflows/bot-serving-check.yml` sends the header
  from the `ORIGIN_SECRET` repository secret on all 32 probes and reads
  `/_health` first: `missing` and `mismatch` are hard failures with a message
  naming the secret, because an armed gate plus a missing secret would
  otherwise open an incident saying every crawler page is broken.

### Added

- **CI builds the app image and runs the gate against it.** `app/Dockerfile`
  was hadolinted but never *built* before Cloud Build, i.e. after the merge —
  and what it produces is not a program that fails to import but an nginx
  whose config is rendered at container start. The new `app-image` job runs
  the real image three ways: gate off (200, `off`, `off-seen`), armed (403
  bare, 403 with a wrong secret, 200 with the right one, `/_health` still
  exempt and naming each verdict) and armed with no secret (refused, which is
  what the tagged map keys buy). It also greps the refusal page and the
  container log for the secret and validates the rendered config with
  `nginx -t` — never `nginx -T`, which would print the secret into the log.
  `tests/test_app_origin_gate.py` holds the six files the mechanism is spread
  over against each other, including the rule that no `proxy_pass` may forward
  the gate header to an upstream.

### Fixed

- **The Worker deploy recipe was missing the one part that makes it work.**
  `infra/cloudflare/README.md`'s scripted `PUT` sent the module without
  `filename=worker.js`, so Cloudflare matched the `main_module` name against
  curl's local path instead and answered `No such module: worker.js`
  (measured live). The multipart part now carries the filename, with the
  reason beside it.
