# Cloudflare — the edge in front of both Cloud Run services

> **Status (2026-09-02): live.** This directory is the SOURCE for Cloudflare
> configuration that would otherwise exist only in the dashboard. It was created
> because the Worker went unmentioned in the repo until the origin gate's
> rollout (PR #493), so nobody without dashboard access could see what it does.
>
> English, like `changelog.d/README.md` and unlike the German documents under
> `docs/` — the repo's convention is that a README is English
> (`docs/reference/sprachregelung.md` §1).

Two services stand behind the edge and both have an origin gate now. The API's
is in Python (`api/origin_gate.py`), armed since 2026-09-03; the site's is in
nginx (`app/origin-gate.conf.template`) and ships switched off. They share one
secret, one set of five verdicts and one rollout procedure — the app's is
[at the end of this file](#the-sites-own-origin-kurrentschrift-app).

## What is here

| File | Role |
|---|---|
| `kurrentschrift-api-proxy.js` | the Worker behind the route `kurrentschrift.ink/api/*` |

**The `.js` mirrors the deployed bytes; it is not a draft.** Change it and
deploy it; change it in the dashboard and pull it back here. That is also why
the file carries no provenance header of its own: a comment there would make
every `diff` between the repo and the running script read "different" forever,
and that diff is the point of keeping a mirror.

> **After merging this PR the Worker needs a redeploy.** The
> `headers.delete('X-Origin-Secret')` line is newer than the running script (see
> "Why it strips the header first"), so repo and deployment are out of step
> until it is pushed.

## The Worker

**Purpose.** `kurrentschrift.ink/api/*` is the ADMIN path to the API. It exists
because the Cloudflare Access cookie on the apex is host-only: it travels under
that host and nowhere else, and only there does Access inject the verifying JWT
(→ [`frontend-stack.md`](../../docs/reference/frontend-stack.md) §5). The Worker
strips the `/api` prefix and forwards to `https://api.kurrentschrift.ink`.
Public pages do not use it; they read the open subdomain directly
(`CONFIG.publicApiBase`).

**Why it stamps the origin secret itself.** This is the finding this directory
exists for:

> A Worker subrequest to a host in the **same zone** bypasses that zone's
> Transform Rules.

The Transform Rule stamps `X-Origin-Secret` on everything Cloudflare forwards
for `api.kurrentschrift.ink` — but not on a `fetch()` issued from inside a
Worker. Without those lines in the Worker, arming the gate would have taken the
whole admin down. It was measured on `/api/health` (see "Measuring" below):
first `off`, then `off-seen` once the Worker had its secret binding, then `ok`
after arming.

**Why it strips the header first.** `headers` is cloned from the incoming
request, so without `headers.delete('X-Origin-Secret')` a caller could supply
that header itself and have it forwarded whenever the binding is unset. Two
consequences, one of them subtle: the documented "unset binding stamps nothing"
would be false, and an unarmed `/health` probe would report a spurious
`off-seen` — corrupting the one measurement the rollout hangs on.

**Why the binding is guarded by `if (env.ORIGIN_SECRET)`.** A missing binding
stamps nothing rather than sending an empty header, which makes the Worker
harmless while the gate is not yet armed. It is **NOT a rollback.** As long as
the Cloud Run service is armed, every admin request without the header gets a
403: removing the binding takes the admin down rather than freeing it. Rolling
back always happens on the API side — remove `ORIGIN_SECRET` from the service
**and promote the resulting revision** (two commands;
[`frontend-stack.md`](../../docs/reference/frontend-stack.md) §5). The ordering
holds in both directions: the Worker starts stamping before the gate is armed,
and stops only after it is disarmed.

## Settings (dashboard)

| | |
|---|---|
| Script name | `kurrentschrift-api-proxy` |
| Route | `kurrentschrift.ink/api/*` (zone `kurrentschrift.ink`) |
| Binding | `secret_text` **`ORIGIN_SECRET`** — value = Secret Manager `ORIGIN_SECRET`, the same one the Cloud Run service gets |
| `compatibility_date` | `2024-11-01` |
| Module type | ES module (`export default { fetch }`) |

## Deploying

**Dashboard** (the usual way): Workers & Pages → `kurrentschrift-api-proxy` →
Edit code → paste the contents of `kurrentschrift-api-proxy.js` → Deploy. The
secret binding is created once under Settings → Variables as a *Secret*; it
survives later deploys.

**API** (when it has to be scriptable) — multipart of metadata plus module. The
secret is never typed: it is read from Secret Manager at execution time, stays
in a shell variable, and reaches `curl` through stdin, so it lands in no shell
history, no file and no process list.

It runs in a fail-fast subshell for a reason: a script `PUT` replaces the
bindings, so a failed or empty secret read would deploy an EMPTY binding, the
Worker would stop stamping, and the armed admin route would go down — the very
outage this gate exists to avoid. Every step is therefore checked before the
next one runs.

```bash
(
  set -euo pipefail

  # Command substitution strips the trailing newline gcloud may print — the
  # same newline that once made ADMIN_TOKEN unusable in a header (2026-08).
  ORIGIN_SECRET=$(gcloud secrets versions access latest \
    --secret=ORIGIN_SECRET --project=kurrentschrift)
  [ -n "$ORIGIN_SECRET" ] || { echo "empty ORIGIN_SECRET — refusing to deploy"; exit 1; }

  ORIGIN_SECRET="$ORIGIN_SECRET" python3 -c '
import json, os, sys
json.dump({
    "main_module": "worker.js",
    "compatibility_date": "2024-11-01",
    "bindings": [
        {"type": "secret_text", "name": "ORIGIN_SECRET", "text": os.environ["ORIGIN_SECRET"]},
    ],
}, sys.stdout)' | curl --fail-with-body -sS -X PUT \
    "https://api.cloudflare.com/client/v4/accounts/{account}/workers/scripts/kurrentschrift-api-proxy" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -F 'metadata=<-;type=application/json' \
    -F 'worker.js=@infra/cloudflare/kurrentschrift-api-proxy.js;filename=worker.js;type=application/javascript+module'
)
```

`pipefail` so a failing `python3` cannot be masked by a succeeding `curl`;
`--fail-with-body` so an HTTP error is a non-zero exit AND still prints
Cloudflare's JSON reason, which plain `-f` swallows.

**`filename=worker.js` in that `-F` is load-bearing**, and it is the one line in
this recipe that fails in a way nobody guesses (measured live 2026-09-04).
`metadata` names `"main_module": "worker.js"`, and Cloudflare matches that
against the multipart part's **filename**, not against its field name. Without
it curl sends the local path as the filename, the upload is accepted as far as
parsing and then refused with

```
No such module: worker.js
```

Then measure before trusting it:

```bash
curl -s https://kurrentschrift.ink/api/health   # expect "origin_gate":"ok"
```

If that reads like more machinery than the job deserves, it is — deploy from the
dashboard instead. The API path exists for the day it has to run unattended.

A script `PUT` **replaces** the bindings wholesale: omitting one removes it —
the same trap that made the Cloud Run side swap `--set-secrets` for
`--update-secrets` (`api/cloudbuild.yaml`). So either send every binding or
deploy from the dashboard.

## Measuring: did the header take this path?

`/health` is exempt from the origin gate and reports its verdict on the request
it was asked with — **never the value**:

| `origin_gate` | meaning |
|---|---|
| `off` | gate not armed, **no** header arrived |
| `off-seen` | gate not armed, the header arrived — the state to be in before arming |
| `ok` | gate armed, header matches |
| `missing` | gate armed, no header — this path would now be dead |
| `mismatch` | gate armed, wrong value (half-applied rotation) |

```bash
curl -s https://api.kurrentschrift.ink/health   # the public path
curl -s https://kurrentschrift.ink/api/health   # THIS Worker (with the Access cookie)
curl -s https://<api-run-url>/health            # must stay "off"/"missing": the closed door
```

After any change to the Worker, the Transform Rule or the secret: measure
first, arm second. The order and the rollback are in
[`frontend-stack.md`](../../docs/reference/frontend-stack.md) §5.

---

## The site's own origin (`kurrentschrift-app`)

The same door, on the other service. `kurrentschrift-app` also stands with
`ingress=all`, so `https://kurrentschrift-app-661695800706.europe-west4.run.app`
serves the whole site with no bot challenge, no WAF and no rate limit — and a
crawler user agent sent there is relayed by `@seo_proxy` to
`https://api.kurrentschrift.ink`, where the edge stamps the API's secret
legitimately. The API gate cannot see that: the request it receives really did
come through the front door. Every such relay is a prerender read on the API
plus the crawler Plausible event it reports, on someone else's terms.

`app/origin-gate.conf.template` is the enforcing half. It is a template because
nginx cannot read the environment; the base image already ships the official
entrypoint's `20-envsubst-on-templates.sh`, so the secret arrives as an ordinary
Cloud Run environment variable and nothing new runs at container start.

**Modes.** `ORIGIN_GATE` unset, or anything that is not some casing of `on`, =
off; `ORIGIN_GATE=on` (or `On`, or `ON` — a plain `map` key is matched without
regard to case, and that is the direction to be wrong in) = 403 without a
matching header. `ORIGIN_SECRET` is the value. Unset means off, which is the
rollback and the state the code ships in. `ORIGIN_GATE=on` with no secret fails
CLOSED — the map keys are tagged so an empty secret cannot become "match
anything".

**There is a length ceiling on the secret**, and it is worth knowing before a
rotation rather than during one. nginx cannot hash a `map` key longer than one
bucket; the key here is `presented:` plus the whole secret, and the template
therefore sets `map_hash_bucket_size 512`. A secret past roughly 500 characters
makes nginx refuse to start — with the gate *off* it starts fine, because the
key is short then, so the failure would appear only at the moment of arming.
Cloud Run keeps the previous revision serving in that case, so it is a safe
failure rather than an outage, and the `app-image` job in
`.github/workflows/ci.yml` runs a production-length secret on every PR.

**Why a header and not a `Host` rule.** `kurrentschrift.ink` is a Cloud Run
**domain mapping**, so Cloudflare forwards the original Host and `$host` really
does tell the edge from the raw URL. A Host rule still cannot be the mechanism:
`.github/workflows/bot-serving-check.yml` probes this origin with crawler user
agents *because* Cloudflare 403s GitHub-runner IPs, it cannot spoof the Host
either, and any exception keyed on something public — a header it invents, a
user agent — is public with this repository. The exception has to be the shared
secret; and once the workflow carries the secret, the Host rule buys nothing the
header does not.

### Hostnames this container serves

The Transform Rule has to cover every one of them, or arming the gate locks out
the visitors it was meant to protect.

| Hostname | Reaches the container via | Transform Rule |
|---|---|---|
| `kurrentschrift.ink` | Cloud Run domain mapping, proxied by Cloudflare | **required** — this is the only one |
| `www.kurrentschrift.ink` | nothing today — there is no domain mapping for it. `app/nginx.conf` has a single catch-all `server_name _`, so the block would serve it the moment one existed | none today; add it in the same breath as the mapping, or arming locks that hostname out |
| `kurrentschrift.ink/api/*` | the apex Worker — but it forwards to `api.kurrentschrift.ink`, **not** to this container | none, and the Worker needs no change (see below) |
| `kurrentschrift.ink/{js/script.js,pa/event}` | a second Worker, straight to `plausible.io` — it does not reach this origin either (`app/index.html`) | none |
| `kurrentschrift-app-661695800706.europe-west4.run.app` | direct | none — this is the door being closed |
| the service's other `*.run.app` form (`gcloud run services describe kurrentschrift-app --format='value(status.url)'`) | direct | none, same door |
| `candidate---kurrentschrift-app-661695800706.europe-west4.run.app` | direct, the pre-traffic tag URL | none — `app/cloudbuild.yaml` sends the header itself |

The rule is a **Set**, not an Add: a caller that supplies its own
`X-Origin-Secret` must have it replaced, not appended.

**Why no Worker change here, unlike the sister project.** anyplot's apex Worker
forwards one path — `/api/event` — back to its own site origin, and a Worker
subrequest inside the zone carries no Transform Rule header, so arming without
stamping that branch would have answered every analytics pageview with a 403.
This zone is arranged differently: `kurrentschrift-api-proxy.js` sends **every**
path to `api.kurrentschrift.ink`, and analytics runs over its own Worker
straight to `plausible.io` — neither ever reaches this container. That is a
property of the code, so `tests/test_app_origin_gate.py` pins it: the day a
branch forwards a path back to this origin, the test says it has to stamp.

### Callers that reach this origin without the edge

Each one is legitimate, each one would be 403'd into silence, and each now
carries the header itself.

| Caller | What it now sends |
|---|---|
| `app/cloudbuild.yaml` pre-traffic smoke | reads `ORIGIN_SECRET` from Secret Manager **inside the step** (not `availableSecrets`, which resolves at build start and would fail every build until the secret exists) and sends `X-Origin-Secret` on every probe. It asks `/_health` for the verdict before any content probe. The build service account `661695800706-compute@developer.gserviceaccount.com` already holds `roles/secretmanager.secretAccessor` on the secret — it is the account both triggers run as, and the API build already reads it. |
| `.github/workflows/bot-serving-check.yml` | sends the header from the `ORIGIN_SECRET` **repository secret** (to be created — it does not exist yet) and reads `/_health` first, so a missing or half-rotated secret fails with a message naming itself instead of reddening all 32 crawler checks. |
| Cloud Run startup probe | nothing, and needs nothing: this service's startup probe is a TCP check on 8080, not an HTTP one, so there is no probe path to exempt. Re-confirm with `gcloud run services describe kurrentschrift-app --format=yaml` before arming. |
| IndexNow (`.github/workflows/indexnow-submit.yml`, and Bing's verification fetch) | nothing, and needs nothing: both go to `https://kurrentschrift.ink/<key>.txt`, i.e. through the edge. |
| the CLS / Lighthouse measurements in `docs/reference/frontend-stack.md` | nothing: they are run with real Chrome against `https://kurrentschrift.ink`, through the edge. After arming, that stays the way to measure — or curl with the header. |

### Measuring: `/_health`

`/_health` is the gate's one exempt path — exact match, no prefix — and reports
`X-Origin-Gate` with the same five verdicts as the API's `/health`, for the
request it was asked with, never the value.

```bash
curl -sI https://kurrentschrift.ink/_health | grep -i x-origin-gate    # edge
curl -sI https://kurrentschrift-app-661695800706.europe-west4.run.app/_health \
  | grep -i x-origin-gate
#   the second one must stay "off" and become "missing": it is the closed door
```

### Rollout

Ordered so that nothing is armed before it has been measured. Steps (a)–(c) are
safe on their own and can sit for days.

```bash
# (a) merge and deploy. Nothing is armed: the image defaults ORIGIN_GATE=off,
#     and the service declares no environment variables at all.
curl -sI https://kurrentschrift.ink/_health | grep -i x-origin-gate      # expect: off

# (b) widen the Transform Rule from api.kurrentschrift.ink to kurrentschrift.ink
#     as well (dashboard: Rules -> Transform Rules -> Modify Request Header,
#     action Set). Then measure EVERY path — each must read off-seen, or stay
#     off where that is the point, before anything is armed:
curl -sI https://kurrentschrift.ink/_health | grep -i x-origin-gate                     # off-seen
curl -sI https://kurrentschrift-app-661695800706.europe-west4.run.app/_health \
  | grep -i x-origin-gate                                                               # off
curl -s -o /dev/null -w '%{http_code}\n' https://kurrentschrift.ink/                    # 200
curl -s -A 'Mozilla/5.0 (compatible; Googlebot/2.1)' https://kurrentschrift.ink/quiz \
  | grep -c 'kurrentschrift.ink prerender'                                              # 1
curl -s https://kurrentschrift.ink/api/health | grep -o '"origin_gate":"[a-z-]*"'       # ok (API, unchanged)

# (c) the GitHub repository secret, which does NOT exist yet — the value is the
#     same one the API gate and the Worker already carry:
gh secret list --repo MarkusNeusinger/kurrentschrift | grep ORIGIN_SECRET || \
  gcloud secrets versions access latest --secret=ORIGIN_SECRET --project=kurrentschrift \
    | gh secret set ORIGIN_SECRET --repo MarkusNeusinger/kurrentschrift
gcloud secrets get-iam-policy ORIGIN_SECRET --project=kurrentschrift   # compute SA has secretAccessor
gh workflow run bot-serving-check.yml --repo MarkusNeusinger/kurrentschrift  # expect "origin gate: off-seen"

# (d) arm — the block below, not two flags. See "Arming, in full".

# (e) verify, in this order:
curl -sI https://kurrentschrift.ink/_health | grep -i x-origin-gate                      # ok
curl -s -o /dev/null -w '%{http_code}\n' https://kurrentschrift.ink/                     # 200
curl -s -o /dev/null -w '%{http_code}\n' \
  https://kurrentschrift-app-661695800706.europe-west4.run.app/                          # 403
curl -s -A 'Mozilla/5.0 (compatible; Googlebot/2.1)' https://kurrentschrift.ink/quiz \
  | grep -c 'kurrentschrift.ink prerender'                                               # 1
gh workflow run bot-serving-check.yml --repo MarkusNeusinger/kurrentschrift              # green
gcloud run services describe kurrentschrift-app --project=kurrentschrift \
  --region=europe-west4 --format="value(status.traffic)"

# (f) rollback — also its own block, below.
```

### Arming, in full

`gcloud run services update` alone is **not** the arm, and the reason is the
same one [`frontend-stack.md`](../../docs/reference/frontend-stack.md) §5 writes
out for the API: this service pins traffic to a named revision
(`app/cloudbuild.yaml` promotes with `--to-revisions=<name>=100`), so an update
creates a revision that serves nothing, and `/_health` would still answer `off`
while everything looked done. Three more things each cost a comparable rollout
somewhere, so the block mirrors the API's, and it runs fail-fast because half of
these commands feed the next one.

```bash
(
set -euo pipefail
SERVICE=kurrentschrift-app
LOC="--project=kurrentschrift --region=europe-west4"

# 0. Do not race the deploy pipeline: a build that already deployed its
#    candidate promotes it at the end, and that revision was cloned from the
#    pre-arm template — the promote would silently undo the arm, and its own
#    smoke accepts `off` by design.
gcloud builds list --project=kurrentschrift --region=europe-west4 --ongoing --format="value(id)" | grep -q . && {
  echo "a Cloud Build is in flight; wait for it to finish (or fail) before arming."
  exit 1
}

# 1. Build the new revision from the image that is SERVING, not from whatever is
#    latest: `services update` clones the latest template, and this pipeline
#    deliberately leaves each build's smoked-but-unpromoted candidate there.
read -r SERVING LATEST <<<"$(gcloud run services describe "$SERVICE" $LOC --format=json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
      t=[x for x in d['status']['traffic'] if x.get('percent')==100]; \
      print(t[0]['revisionName'], d['status']['latestReadyRevisionName'])")"
IMAGE=$(gcloud run revisions describe "$SERVING" $LOC --format="value(spec.containers[0].image)")
test -n "$SERVING" && test -n "$IMAGE" || { echo "could not resolve the serving revision or its image"; exit 1; }
test "$SERVING" = "$LATEST" || echo "note: latest ($LATEST) is not serving ($SERVING) — image pinned to the serving one"

# 2. Pin the secret to a NUMBER, never `:latest`. Cloud Run resolves a
#    secret-backed variable when each instance starts, so with `:latest` a new
#    secret version reaches new instances while older ones keep the old value —
#    and since the edge stamps exactly one value, that shows up as intermittent
#    403s inside a single revision.
VERSION=$(gcloud secrets versions list ORIGIN_SECRET --project=kurrentschrift \
  --filter="state=ENABLED" --sort-by=~createTime --limit=1 --format="value(name)")
test -n "$VERSION" || { echo "no ENABLED version of ORIGIN_SECRET"; exit 1; }

# 3. Update DARK, then promote BY NAME. `--to-latest` would hand traffic to
#    whatever the pipeline last built.
#
#    `--no-traffic` is belt and braces, and it is worth saying which half is
#    which. The braces: after every build this service's traffic block names a
#    REVISION (`app/cloudbuild.yaml` promotes with `--to-revisions=…=100`), and
#    a new revision therefore serves nothing until it is named — measured, not
#    assumed, during the API gate's own rollout (#493), where `services update`
#    alone produced a revision that answered no request at all. The belt: this
#    block reads `status.traffic` to find the SERVING revision but never
#    inspects the traffic SPEC, and a service that was last touched by a plain
#    `gcloud run deploy` outside the pipeline carries `latestRevision: true`
#    instead — where the update would arm production immediately, before step 4
#    could measure anything. Passing the flag makes the block right in both
#    shapes; where traffic is already by name it is a no-op.
SUFFIX="arm-$(date -u +%Y%m%d%H%M)"
gcloud run services update "$SERVICE" $LOC --image="$IMAGE" \
  --update-secrets="ORIGIN_SECRET=ORIGIN_SECRET:$VERSION" \
  --update-env-vars="ORIGIN_GATE=on" --revision-suffix="$SUFFIX" --no-traffic
gcloud run services update-traffic "$SERVICE" $LOC --to-revisions="$SERVICE-$SUFFIX=100"

# 4. Confirm, and confirm which revision answered. A build that promoted over
#    the arm shows up here as `off` on a path that carries the header.
curl -sI https://kurrentschrift.ink/_health | grep -i x-origin-gate
gcloud run services describe "$SERVICE" $LOC --format="value(status.traffic)"
)
```

If the rendered config were invalid, nginx would not start, the revision would
never become ready, and the `update-traffic` would fail with traffic still on
the old revision — a safe failure, and the reason step 4 is not optional.

### Rolling back

Its own block, not the one above with a flag swapped: it has to run in the worst
state the service can be in, which includes the secret having been disabled
during the incident, so it looks nothing up.

```bash
(
set -euo pipefail
SERVICE=kurrentschrift-app
LOC="--project=kurrentschrift --region=europe-west4"

SERVING=$(gcloud run services describe "$SERVICE" $LOC --format=json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
      print(next(x['revisionName'] for x in d['status']['traffic'] if x.get('percent')==100))")
IMAGE=$(gcloud run revisions describe "$SERVING" $LOC --format="value(spec.containers[0].image)")
test -n "$IMAGE" || { echo "could not resolve the serving image"; exit 1; }

# `--no-traffic` here for the same reason as in the arm block, and it costs a
# rollback nothing: the disarmed revision has to become READY before it is worth
# promoting, and a revision that cannot start (a bad image pin, a quota) must
# not take traffic off a working one on its way to failing. The promotion below
# is the step that ends the incident.
SUFFIX="disarm-$(date -u +%Y%m%d%H%M)"
gcloud run services update "$SERVICE" $LOC --image="$IMAGE" \
  --remove-env-vars=ORIGIN_GATE --revision-suffix="$SUFFIX" --no-traffic
gcloud run services update-traffic "$SERVICE" $LOC --to-revisions="$SERVICE-$SUFFIX=100"

curl -sI https://kurrentschrift.ink/_health | grep -i x-origin-gate   # expect "off" or "off-seen"
)
```

Removing `ORIGIN_GATE` is enough; the secret may stay attached, which is what
makes re-arming one flag rather than two.

`--update-secrets` and `--update-env-vars`, never the `--set-` forms: those
replace the whole set, so the next deploy would strip whatever was attached out
of band — the same trap `api/cloudbuild.yaml` documents for the API side.
`app/cloudbuild.yaml` names neither variable, so a deploy carries both forward
untouched.

**Rotation** is roll back, rotate, arm again, and there are now **five** copies
of one value: Secret Manager, the API service, the app service, the Worker
binding and the GitHub repository secret. The gate is off in between, which is
the documented safe state.
