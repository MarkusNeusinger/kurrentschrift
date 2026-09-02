# Cloudflare — the apex Worker in front of the API

> **Status (2026-09-02): live.** This directory is the SOURCE for Cloudflare
> configuration that would otherwise exist only in the dashboard. It was created
> because the Worker went unmentioned in the repo until the origin gate's
> rollout (PR #493), so nobody without dashboard access could see what it does.
>
> English, like `changelog.d/README.md` and unlike the German documents under
> `docs/` — the repo's convention is that a README is English
> (`docs/reference/sprachregelung.md` §1).

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
    -F 'worker.js=@infra/cloudflare/kurrentschrift-api-proxy.js;type=application/javascript+module'
)
```

`pipefail` so a failing `python3` cannot be masked by a succeeding `curl`;
`--fail-with-body` so an HTTP error is a non-zero exit AND still prints
Cloudflare's JSON reason, which plain `-f` swallows. Then measure before
trusting it:

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
