# Deploy-Bootstrap — Statusbericht

Stand: **2026-06-10**. Schritt 6 (Cloudflare Access) + Schritt 7 (Plausible-Proxy) sind seit **2026-05-29 live** — `kurrentschrift.ink` läuft hinter Cloudflare, Admin hinter Zero-Trust-Access (verifiziert; Edge-Checks am 2026-06-10 erneut grün: Landing 200, `/admin` 302, `/js/script.js` 200). Plausible empfängt Besucher (bestätigt 2026-06-10). Seit PR #18 führt die Deploy-Pipeline Migrationen automatisch aus (Job `kurrentschrift-migrate`, s. u.).

Dieses Dokument ist ein operativer Schnappschuss: was läuft, was noch fehlt, welche IDs/URLs man im Kopf haben muss. Pendant zum ursprünglichen Bootstrap-Plan (lokale Plan-Notiz des Betreibers, nicht im Repo).

## Aktuell live

| Dienst | URL | Status |
|---|---|---|
| Landing + Admin-SPA | https://kurrentschrift.ink/ | 200, proxied (Cloudflare); `/admin*` hinter Access |
| API | https://api.kurrentschrift.ink/health | `{status:"healthy", database_configured:true}`, proxied |
| Direkt (break-glass) | `*-3yau3h6oyq-ez.a.run.app` (app + api) | weiterhin erreichbar, umgeht Cloudflare/Access |
| DB | `kurrentschrift` auf `anyplot:europe-west4:anyplot-db` | Reachable via Cloud SQL Connector (Cross-Project IAM) |

Schreib-Endpoints (PUT/POST/DELETE auf `bboxes` + `glyphs`) sind gegen `require_admin` (FastAPI Depends) gesichert. **Beide Pfade aktiv:** Cloudflare-Access-JWT (Google-Login via geteilte anyplot-Org, Allowlist = nur die Betreiber-E-Mail, s. Access-Policy) **und** `X-Admin-Token`-Fallback. Verifiziert am 2026-05-29 über die CF-Edge: eingeloggter Bbox-PUT → 200, gefälschtes JWT → 401.

## Was eingerichtet ist

### GCP-Projekt `kurrentschrift`

- Projekt-ID: `kurrentschrift`, Projekt-Nummer: `661695800706`
- Billing-Account: `01C36E-578B56-0054F8` (Markus Konto)
- Aktivierte APIs: `run`, `cloudbuild`, `artifactregistry`, `sqladmin`, `secretmanager`
- Artifact Registry: `kurrentschrift` (Docker, `europe-west4`)
- Region für alles: `europe-west4`

### Service-Accounts und IAM

| SA | Zweck | Rollen im `kurrentschrift`-Projekt |
|---|---|---|
| `661695800706@cloudbuild.gserviceaccount.com` | Cloud Build Default (Legacy) | run.admin, iam.serviceAccountUser, secretmanager.secretAccessor, artifactregistry.writer |
| `661695800706-compute@developer.gserviceaccount.com` | Trigger-SA (Build-Zeit, 2nd-gen verlangt user-managed SA) | run.admin, iam.serviceAccountUser, secretmanager.secretAccessor, artifactregistry.writer, storage.admin, logging.logWriter |
| `kurrentschrift-runtime@kurrentschrift.iam.gserviceaccount.com` | Cloud-Run-Runtime (Lese Secrets, sprich Cloud SQL) | secretmanager.secretAccessor; `roles/cloudsql.client` im `anyplot`-Projekt (Cross-Project) |

`actAs`-Berechtigungen:
- Cloud-Build-SA + Compute-SA dürfen beide als `kurrentschrift-runtime` deployen (`iam.serviceAccountUser` auf der SA-Ressource).

### Cloud SQL (Cross-Project)

- DB `kurrentschrift` liegt auf `anyplot:europe-west4:anyplot-db` (anyplot-Projekt).
- Eigener Postgres-User `kurrentschrift` mit Ownership der Datenbank.
- Tabellen-Ownership wurde am **2026-06-04** vom `anyplot`- auf den `kurrentschrift`-User übertragen; zusätzlich `ALTER DEFAULT PRIVILEGES` für künftige Migrationen.

### Secret Manager

Vier Secrets im `kurrentschrift`-Projekt:

| Name | Inhalt | Befüllt? |
|---|---|---|
| `DATABASE_URL` | Cloud SQL Unix-Socket URL für `kurrentschrift`-User | ✅ |
| `ADMIN_TOKEN` | Random 32-byte hex, fallback für `X-Admin-Token` | ✅ |
| `CF_ACCESS_TEAM_DOMAIN` | `anyplot.cloudflareaccess.com` (geteilte Zero-Trust-Org — eine Org pro CF-Account) | ✅ v2 — korrigiert (war fälschl. `kurrentschrift.…`) |
| `CF_ACCESS_AUD` | AUD der Access-App „kurrentschrift admin" (Wert nur im Secret) | ✅ v2 — befüllt |

Alle Secrets sind dem Runtime-SA via `secretmanager.secretAccessor` zugänglich.

### Cloud Run Services

Beide deployt aus `main` via die Trigger:

- `kurrentschrift-api` — Python 3.13, FastAPI, port 8000, mem 1Gi, min=0, max=1, gen2, runtime SA = `kurrentschrift-runtime`, Cloud SQL connected
- `kurrentschrift-app` — nginx-unprivileged auf statischem Vite-Build, port 8080, mem 512Mi, min=0, max=1

Aktuelle Revisions: api `00003` (lädt CF-Access-Secrets v2), app `00004`+ (Plausible-Endpoint-Fix `0e00b03` im Deploy). URLs siehe oben.

IAM: beide haben `allUsers:roles/run.invoker` (manuell gesetzt — `--allow-unauthenticated` im Deploy hat das im Cloud-Build-Lauf nicht gebunden, einmalige `gcloud run services add-iam-policy-binding`-Korrektur war nötig; bleibt bestehen über künftige Revisions).

### Cloud Build

Connection (2nd-gen GitHub host):
- `kurrentschrift-github` in `europe-west4` — verbunden mit `MarkusNeusinger/kurrentschrift`

Trigger (beide in `europe-west4`, Branch-Pattern `^main$`):
- `deploy-api` → `api/cloudbuild.yaml`, included files: `api/**, core/**, pyproject.toml, uv.lock, .dockerignore, .gcloudignore`
- `deploy-app` → `app/cloudbuild.yaml`, included files: `app/**`

Migrationen: `api/cloudbuild.yaml` führt vor dem Deploy den Cloud-Run-Job **`kurrentschrift-migrate`** aus (`alembic upgrade head` im frisch gebauten Image, seit PR #18) — Schema-Änderungen laufen also automatisch mit dem API-Deploy, nie ad-hoc.

Beide nutzen den Compute-SA als Build-SA (2nd-gen verlangt user-managed SA — die default Cloud-Build-SA wird abgelehnt).

### Code-Stand auf `main`

- `api/auth.py` — CF-Access-JWT-Verify (JWKS-cached) + `X-Admin-Token`-Fallback
- `api/routers/{bboxes,glyphs}.py` — `Depends(require_admin)` auf Write-Endpoints
- `core/config.py` — Settings für CF-Access + Admin-Auth, CORS um Production-Origins erweitert
- `app/src/router.tsx` — `/` Landing, `/admin/chart`, `/admin/edit/:glyphKey`
- `app/src/pages/LandingPage.tsx` — schlichte Coming-Soon-Karte
- `app/src/api.ts` — alle Fetches mit `credentials: 'include'` (für CF-Access-Cookie-Forwarding)
- `app/index.html` — Plausible-Snippet (hostname-gated; Script `/js/script.js`, Events `/pa/event` — bewusst **nicht** `/api/event`, da `/api/*` Access-gated ist)
- `.dockerignore` + `.gcloudignore` — Source-Upload von 157 MiB → 1.1 MiB
- `.env.example` — saubere Vorlage (anyplot-Werte raus)

## Was erledigt ist — Cloudflare (Schritt 6 + 7, 2026-05-29)

Der Infomaniak-Anycast-Blocker hatte sich aufgelöst (NS standen am 29.05. auf Cloudflare: `ali`/`guss.ns.cloudflare.com`). Das Setup wurde per Cloudflare-API (Account-owned Token) als Spiegel von anyplot gebaut.

**Topologie:** Beide Zonen liegen im **selben CF-Account** (Konto des Betreibers; Account-ID im CF-Dashboard) → **eine** Zero-Trust-Org `anyplot` (Team-Domain `anyplot.cloudflareaccess.com`). Ein eigenes Team = ein eigener Account (eine Org pro Account); verworfen — rein kosmetisch (nur die Admin-Login-Seite zeigt das Team-Domain), und End-User-Login wäre ohnehin App-Ebene, unabhängig davon.

### Schritt 6 — Cloudflare Access (Admin-Gate)

1. **Cloud-Run-Domain-Mappings**: `kurrentschrift.ink`→`kurrentschrift-app`, `api.kurrentschrift.ink`→`kurrentschrift-api`. Apex bekam A/AAAA (Google-Frontend-IPs), `api` ein CNAME → `ghs.googlehosted.com`. Google-Managed-Certs ausgestellt (dafür war das DNS kurz **grau/DNS-only**).
2. DNS dann auf **proxied (orange)** geflippt, **SSL-Mode `strict`**, `always_use_https` on.
3. **Worker `kurrentschrift-api-proxy`** auf Route `kurrentschrift.ink/api/*` → rewrite `/api/X` zu `https://api.kurrentschrift.ink/X`, leitet alle Header inkl. `Cf-Access-Jwt-Assertion` weiter (so erreicht das JWT die API auf der Subdomain; Access sitzt davor und injiziert es). Spiegel von `anyplot-api-proxy`.
4. **Access-App „kurrentschrift admin"** (`self_hosted`; App-ID im CF-Dashboard): Domains `kurrentschrift.ink/admin`, `/admin/*`, `/api/*`; Google-IdP von anyplot wiederverwendet (UUID im CF-Dashboard); Session 730h; Policy „Allow <Betreiber-E-Mail>". **AUD**: vollständig im Secret `CF_ACCESS_AUD`.
5. Secrets `CF_ACCESS_AUD` + `CF_ACCESS_TEAM_DOMAIN` befüllt (v2), `kurrentschrift-api` redeployt (rev `00003`).

> **Guardrail:** anyplots App/Worker/Zone/DNS wurden nur **gelesen**, nie verändert; geschrieben wurde ausschließlich an der kurrentschrift-Zone (Zone-ID im CF-Dashboard), den kurrentschrift-Secrets und einer **neuen** App in der geteilten Org.

### Schritt 7 — Plausible (self-hosted Proxy)

- **Eigener** Worker `kurrentschrift-plausible-proxy` (getrennt vom API-Proxy → Blast-Radius isoliert, anyplots Worker bleibt unberührt). Routen:
  - `kurrentschrift.ink/js/script.js` → fetch `https://plausible.io/js/pa-8wj7-QdkR8vj4z_19QBCd.js` (Custom-Bundle)
  - `kurrentschrift.ink/pa/event` → forward an `https://plausible.io/api/event`, `X-Forwarded-For` aus `CF-Connecting-IP`
- `app/index.html`: Events gehen auf **`/pa/event`** (Commit `0e00b03`) — **nicht** `/api/event`, da das mit der `/api/*`-Access-Sperre kollidiert hätte (öffentliche Besucher → 302 statt Tracking).
- ✅ **Erledigt (2026-06-10):** Plausible-Site `kurrentschrift.ink` ist registriert, Besucher kommen im Dashboard an.

### ⚠️ Cert-Renewal-Tripwire (prüfen ~2026-08-17)

Cloud-Run-Managed-Certs erneuern alle ~90 Tage und validieren über öffentliches DNS, das auf Google zeigt. Hinter **orange-cloud** sieht Google sich evtl. nicht selbst → Renewal kann **still** fehlschlagen → Full(strict) bricht mit 526. Check:

```bash
gcloud beta run domain-mappings describe --domain=kurrentschrift.ink --region=europe-west4 --project=kurrentschrift \
  --format="value(status.conditions)" | grep -i Certificate
```

Fix falls pending/failed: betroffene DNS-Records temporär auf **grau (DNS-only)** stellen, Renewal abwarten, zurück auf orange.

### Schritt 8 — End-to-End-Smoke-Test

Validiert am 2026-05-29 über die Cloudflare-Edge:
- ✅ `https://kurrentschrift.ink/` → 200, `server: cloudflare` (proxied), Landing rendert
- ✅ `/admin` → 302 → `anyplot.cloudflareaccess.com/cdn-cgi/access/login/…` (AUD stimmt mit Secret `CF_ACCESS_AUD` überein)
- ✅ `/api/*` ohne Auth → 302 (Access sitzt vor dem Worker)
- ✅ Eingeloggter **Bbox-PUT → 200** (kompletter JWT-Pfad: Worker leitet Assertion weiter, FastAPI verifiziert AUD + Issuer + E-Mail-Allowlist — per API-Logs bestätigt)
- ✅ Gefälschtes JWT auf api-Subdomain → 401 (Defense-in-Depth)
- ✅ `/js/script.js` → 200 `application/javascript`; `/pa/event` proxyt zu Plausible

Nachgeprüft:
- [x] Plausible-Dashboard zeigt Pageviews für `kurrentschrift.ink` (bestätigt 2026-06-10)
- [x] Lokaler Browser: nach Ablauf der DNS-TTL (300 s) gegenstandslos — Admin lädt (Stand 2026-06-10)

Einziger offener Punkt: der **Cert-Renewal-Check ~2026-08-17** (Tripwire oben).

## Wichtige IDs und Pfade (Cheat-Sheet)

```
GCP-Projekt:       kurrentschrift                                 (Nummer 661695800706)
Billing:           01C36E-578B56-0054F8
Region:            europe-west4
Artifact Registry: europe-west4-docker.pkg.dev/kurrentschrift/kurrentschrift
Runtime-SA:        kurrentschrift-runtime@kurrentschrift.iam.gserviceaccount.com
Cloud-SQL:         anyplot:europe-west4:anyplot-db (DB: kurrentschrift, User: kurrentschrift)
GitHub:            MarkusNeusinger/kurrentschrift
Cloud-Build-Conn:  kurrentschrift-github  (region europe-west4)
Triggers:          deploy-api, deploy-app  (region europe-west4, branch ^main$)
Anyplot-Referenz:  Schwester-Repo `anyplot` (lokales Checkout)  + GCP-Projekt `anyplot`

CF-Account:        Konto des Betreibers (Account-/Zone-IDs im CF-Dashboard)
CF-Zone (ks):      kurrentschrift.ink (Zone-ID im CF-Dashboard)
ZT-Team-Domain:    anyplot.cloudflareaccess.com   (geteilte Org, eine pro Account)
Google-IdP:        von anyplot wiederverwendet (UUID im CF-Dashboard)
Access-App:        "kurrentschrift admin"  (App-ID im CF-Dashboard, AUD im Secret CF_ACCESS_AUD)
Worker (api):      kurrentschrift-api-proxy         route kurrentschrift.ink/api/*
Worker (plausib):  kurrentschrift-plausible-proxy   routes /js/script.js + /pa/event
```

Häufig gebrauchte Befehle:

```bash
# Manueller Trigger-Lauf (wenn man nicht pushen will)
gcloud builds triggers run deploy-api --branch=main --region=europe-west4 --project=kurrentschrift
gcloud builds triggers run deploy-app --branch=main --region=europe-west4 --project=kurrentschrift

# Service-URL holen
gcloud run services describe kurrentschrift-api --region=europe-west4 --project=kurrentschrift --format='value(status.url)'

# Logs streamen
gcloud beta run services logs tail kurrentschrift-api --region=europe-west4 --project=kurrentschrift

# Secret-Version aktualisieren (Beispiel CF_ACCESS_AUD)
echo -n "<UUID>" | gcloud secrets versions add CF_ACCESS_AUD --data-file=- --project=kurrentschrift
# Danach Cloud Run neu deployen damit das neue Secret geladen wird
gcloud run services update kurrentschrift-api --region=europe-west4 --project=kurrentschrift
```

## Architektur-Entscheidungen die hier gefallen sind

- **Auth-Pattern**: Cloudflare Access + JWT-Validation in FastAPI (Defense-in-Depth, identisch zu anyplot). `--allow-unauthenticated` auf Cloud Run, echte Autorisierung serverseitig. Geteilte Zero-Trust-Org (`anyplot.cloudflareaccess.com`); kurrentschrift ist eine **eigene** Access-App mit eigener AUD → Auth pro App isoliert trotz geteilter Org.
- **DB-Boundary**: Eigener Postgres-User `kurrentschrift`, eigene Datenbank, aber gemeinsam mit anyplot auf einer Cloud-SQL-Instanz (Kosten). Cross-Project-IAM bindet das sauber.
- **min=0, max=1 Instances**: Personal-Projekt, Cold-Start (~3s API, ~1s nginx) akzeptabel. Spart Idle-Kosten.
- **Plausible via Worker**: Adblocker-Bypass via self-hosted Proxy. **Eigener** Worker `kurrentschrift-plausible-proxy` (nicht anyplots — Blast-Radius-Isolation). Events auf `/pa/event` statt `/api/event` (Kollision mit dem `/api/*`-Access-Gate).
- **2nd-gen Cloud Build**: User-managed Compute-SA als Build-SA. Die Legacy `PROJECT_NUMBER@cloudbuild.gserviceaccount.com` wird von 2nd-gen-Triggern abgelehnt.
