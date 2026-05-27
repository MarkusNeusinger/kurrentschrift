# Deploy-Bootstrap — Statusbericht

Stand: **2026-05-27**, Branch `main` Commit `7a41af2` (Merge von PR #5 `feat/bootstrap-deploy`).

Dieses Dokument ist ein operativer Schnappschuss: was läuft, was noch fehlt, welche IDs/URLs man im Kopf haben muss. Pendant zum Plan unter `/home/tirao/.claude/plans/was-w-ren-gute-n-chste-quizzical-scone.md`.

## Aktuell live

| Dienst | URL | Status |
|---|---|---|
| Landing + Admin-SPA | https://kurrentschrift-app-3yau3h6oyq-ez.a.run.app/ | 200 (Landing rendert) |
| API | https://kurrentschrift-api-3yau3h6oyq-ez.a.run.app/ | `/health` → `{status:"healthy", database_configured:true}` |
| DB | `kurrentschrift` auf `anyplot:europe-west4:anyplot-db` | Reachable via Cloud SQL Connector (Cross-Project IAM) |

Schreib-Endpoints (PUT/POST/DELETE auf `bboxes` + `glyphs`) sind gegen `require_admin` (FastAPI Depends) gesichert — ohne `Cf-Access-Jwt-Assertion`-Header oder `X-Admin-Token` → 401. Aktuell läuft nur der Token-Pfad (CF-Access-AUD ist noch Platzhalter).

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
- Bestehende Tabellen (alembic_version, sources, bboxes, glyphs) gehören noch dem `anyplot`-User; `kurrentschrift`-User hat per `GRANT ALL ON ALL TABLES IN SCHEMA public` Zugriff plus `ALTER DEFAULT PRIVILEGES` für künftige Migrationen.

### Secret Manager

Vier Secrets im `kurrentschrift`-Projekt:

| Name | Inhalt | Befüllt? |
|---|---|---|
| `DATABASE_URL` | Cloud SQL Unix-Socket URL für `kurrentschrift`-User | ✅ |
| `ADMIN_TOKEN` | Random 32-byte hex, fallback für `X-Admin-Token` | ✅ |
| `CF_ACCESS_TEAM_DOMAIN` | `kurrentschrift.cloudflareaccess.com` | ✅ (Platzhalter — Team-Setup folgt in Schritt 6) |
| `CF_ACCESS_AUD` | Application-UUID aus Cloudflare Zero Trust | ⚠️ `PLACEHOLDER_FILL_AFTER_CLOUDFLARE_SETUP` — muss noch befüllt werden |

Alle Secrets sind dem Runtime-SA via `secretmanager.secretAccessor` zugänglich.

### Cloud Run Services

Beide deployt aus `main` via die Trigger:

- `kurrentschrift-api` — Python 3.13, FastAPI, port 8000, mem 1Gi, min=0, max=1, gen2, runtime SA = `kurrentschrift-runtime`, Cloud SQL connected
- `kurrentschrift-app` — nginx-unprivileged auf statischem Vite-Build, port 8080, mem 512Mi, min=0, max=1

Aktuelle Revisions: api `00002`, app `00003`. URLs siehe oben.

IAM: beide haben `allUsers:roles/run.invoker` (manuell gesetzt — `--allow-unauthenticated` im Deploy hat das im Cloud-Build-Lauf nicht gebunden, einmalige `gcloud run services add-iam-policy-binding`-Korrektur war nötig; bleibt bestehen über künftige Revisions).

### Cloud Build

Connection (2nd-gen GitHub host):
- `kurrentschrift-github` in `europe-west4` — verbunden mit `MarkusNeusinger/kurrentschrift`

Trigger (beide in `europe-west4`, Branch-Pattern `^main$`):
- `deploy-api` → `api/cloudbuild.yaml`, included files: `api/**, core/**, pyproject.toml, uv.lock, .dockerignore, .gcloudignore`
- `deploy-app` → `app/cloudbuild.yaml`, included files: `app/**`

Beide nutzen den Compute-SA als Build-SA (2nd-gen verlangt user-managed SA — die default Cloud-Build-SA wird abgelehnt).

### Code-Stand auf `main`

- `api/auth.py` — CF-Access-JWT-Verify (JWKS-cached) + `X-Admin-Token`-Fallback
- `api/routers/{bboxes,glyphs}.py` — `Depends(require_admin)` auf Write-Endpoints
- `core/config.py` — Settings für CF-Access + Admin-Auth, CORS um Production-Origins erweitert
- `app/src/router.tsx` — `/` Landing, `/admin/chart`, `/admin/edit/:glyphKey`
- `app/src/pages/LandingPage.tsx` — schlichte Coming-Soon-Karte
- `app/src/api.ts` — alle Fetches mit `credentials: 'include'` (für CF-Access-Cookie-Forwarding)
- `app/index.html` — Plausible-Snippet (hostname-gated, Worker-proxied)
- `.dockerignore` + `.gcloudignore` — Source-Upload von 157 MiB → 1.1 MiB
- `.env.example` — saubere Vorlage (anyplot-Werte raus)

## Was noch offen ist

### Schritt 6 — Cloudflare (blockiert)

Aktuell blockiert: Infomaniak lässt das Deaktivieren der Anycast-DNS nicht zu (vermutlich registrar-seitige Sperrzeit nach Neukauf, oder Mail/Hosting-Service hängt am Domain).

Sobald Cloudflare-NS gesetzt werden können:

1. Domain bei Cloudflare hinzufügen (Free Plan), Nameserver beim Registrar (Infomaniak) auf die zwei zugewiesenen Cloudflare-NS umstellen.
2. SSL/TLS-Mode: "Full (strict)".
3. DNS-Records (beide proxied / orange-cloud):
   - `kurrentschrift.ink` CNAME → `ghs.googlehosted.com` (Cloud Run Custom Domain) ODER `kurrentschrift-app-3yau3h6oyq-ez.a.run.app`
   - `api.kurrentschrift.ink` CNAME → analog für `kurrentschrift-api`
4. Custom Domain Mapping in Cloud Run (geht erst wenn die Domain bei Cloudflare aktiv ist):
   ```bash
   gcloud beta run domain-mappings create --service=kurrentschrift-app --domain=kurrentschrift.ink --region=europe-west4 --project=kurrentschrift
   gcloud beta run domain-mappings create --service=kurrentschrift-api --domain=api.kurrentschrift.ink --region=europe-west4 --project=kurrentschrift
   ```
5. Cloudflare Zero Trust:
   - Team: `kurrentschrift` (ergibt `kurrentschrift.cloudflareaccess.com`)
   - Identity Provider: Google (One-Click oder OAuth-Client aus GCP)
   - Access-Application "Admin" für `kurrentschrift.ink/admin*` — Policy: Allow `meakeiok@gmail.com`
   - Application Audience UUID kopieren → `CF_ACCESS_AUD` im Secret Manager befüllen, Service neu deployen

Plan-B falls Cloudflare partout nicht klappt: **GCP IAP** als Auth-Layer (in den docs erwähnt). Etwas weniger Komfort (kein Worker für Plausible-Adblock-Bypass), aber funktioniert mit Infomaniak-DNS direkt.

### Schritt 7 — Plausible + Worker-Proxy

- Im bestehenden Plausible-Account (gleicher Login wie anyplot) "+ Add a website" → `kurrentschrift.ink`.
- Cloudflare-Worker-Routen einrichten (kann der gleiche Worker sein wie für anyplot, einfach Routes hinzufügen):
  - `kurrentschrift.ink/js/script.js*` → fetch `https://plausible.io/js/pa-8wj7-QdkR8vj4z_19QBCd.js` (das Custom-Bundle aus dem Plausible-Dashboard)
  - `kurrentschrift.ink/api/event*` → POST forward an `https://plausible.io/api/event` mit `X-Forwarded-For` aus `CF-Connecting-IP`
- Worker-Routen müssen Vorrang vor dem `kurrentschrift.ink/api/*` → Cloud-Run-API-Routing haben (spezifischere Routes zuerst).

### Schritt 8 — End-to-End-Smoke-Test (teilweise grün)

Bereits validiert (auf `*.run.app`-URLs):
- ✅ Landing rendert
- ✅ `/health` 200 + DB connected
- ✅ Write-Endpoint ohne Auth → 401
- ✅ Auto-Deploy via push auf main funktioniert

Noch zu validieren (nach Cloudflare + Plausible):
- [ ] `https://kurrentschrift.ink/` rendert Landing + Plausible-Pageview im Network-Tab
- [ ] `https://kurrentschrift.ink/admin/chart` → CF-Access-Redirect → Google-Login → Chart lädt → Bbox speicherbar
- [ ] Direkter `*.run.app/...` Hit auf Write-Endpoint mit gefälschtem JWT → weiterhin 401 (Defense-in-Depth check)
- [ ] Plausible-Dashboard zeigt Pageview für `kurrentschrift.ink`

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
Anyplot-Referenz:  /home/tirao/anyplot/  + GCP-Projekt `anyplot`
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

- **Auth-Pattern**: Cloudflare Access + JWT-Validation in FastAPI (Defense-in-Depth, identisch zu anyplot). `--allow-unauthenticated` auf Cloud Run, echte Autorisierung serverseitig.
- **DB-Boundary**: Eigener Postgres-User `kurrentschrift`, eigene Datenbank, aber gemeinsam mit anyplot auf einer Cloud-SQL-Instanz (Kosten). Cross-Project-IAM bindet das sauber.
- **min=0, max=1 Instances**: Personal-Projekt, Cold-Start (~3s API, ~1s nginx) akzeptabel. Spart Idle-Kosten.
- **Plausible via Worker**: Adblocker-Bypass, gleicher Worker-Code-Base wie anyplot (Routes additiv).
- **2nd-gen Cloud Build**: User-managed Compute-SA als Build-SA. Die Legacy `PROJECT_NUMBER@cloudbuild.gserviceaccount.com` wird von 2nd-gen-Triggern abgelehnt.
