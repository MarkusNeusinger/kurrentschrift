# Cloudflare — der Apex-Worker vor der API

> **Status (2026-09-02): lebend.** Dieses Verzeichnis ist die *Quelle* für
> Cloudflare-Konfiguration, die sonst nur im Dashboard existiert. Angelegt,
> weil der Worker beim Rollout des Origin-Gates (PR #493) nirgends im Repo
> stand und niemand ohne Dashboard-Zugang sehen konnte, was er tut.

## Was hier liegt

| Datei | Rolle |
|---|---|
| `kurrentschrift-api-proxy.js` | der Worker hinter der Route `kurrentschrift.ink/api/*` |

**Die `.js` ist ein Spiegel der ausgelieferten Bytes, kein Entwurf.** Wer sie
ändert, deployt sie auch — und wer im Dashboard etwas ändert, zieht sie hier
nach. Genau deshalb steht kein Kopfkommentar mit Provenienz in der Datei
selbst: so bleibt ein `diff` zwischen Repo und laufendem Script aussagekräftig
statt ständig „unterschiedlich".

## Der Worker

**Zweck.** `kurrentschrift.ink/api/*` ist der ADMIN-Weg zur API. Er existiert,
weil das Cloudflare-Access-Cookie auf der Apex host-only gesetzt ist: nur unter
diesem Host reist es mit, und nur dort injiziert Access das verifizierende JWT
(→ [`frontend-stack.md`](../../docs/reference/frontend-stack.md) §5). Der Worker
schneidet das Präfix `/api` ab und reicht den Request an
`https://api.kurrentschrift.ink` weiter. Öffentliche Seiten benutzen ihn nicht;
die lesen direkt die offene Subdomain (`CONFIG.publicApiBase`).

**Warum er das Origin-Geheimnis selbst stempelt.** Das ist der Befund, für den
dieses Verzeichnis entstanden ist:

> Ein Worker-Subrequest an einen Host **derselben Zone** läuft an den
> Transform-Rules der Zone **vorbei**.

Die Transform-Rule stempelt `X-Origin-Secret` auf alles, was Cloudflare für
`api.kurrentschrift.ink` weiterreicht — aber eben nicht auf ein `fetch()` aus
einem Worker heraus. Ohne die vier Zeilen im Worker hätte das Scharfschalten des
Gates den ganzen Admin lahmgelegt. Gemessen wurde das an `/api/health` (siehe
Messvorschrift unten): erst `off`, nach dem Worker-Update mit Secret-Binding
`off-seen`, nach dem Scharfschalten `ok`.

Die Bindung wird bewusst als `if (env.ORIGIN_SECRET)` geprüft: eine fehlende
Bindung stempelt nichts, statt einen leeren Header zu senden — dasselbe
„unset heißt aus" wie auf der API-Seite, und derselbe Rollback.

## Einstellungen (Dashboard)

| | |
|---|---|
| Script-Name | `kurrentschrift-api-proxy` |
| Route | `kurrentschrift.ink/api/*` (Zone `kurrentschrift.ink`) |
| Binding | `secret_text` **`ORIGIN_SECRET`** — Wert = Secret Manager `ORIGIN_SECRET`, derselbe, den der Cloud-Run-Dienst bekommt |
| `compatibility_date` | `2024-11-01` |
| Modultyp | ES-Modul (`export default { fetch }`) |

## Deploy

**Dashboard** (der übliche Weg): Workers & Pages → `kurrentschrift-api-proxy` →
Edit code → Inhalt von `kurrentschrift-api-proxy.js` einfügen → Deploy. Die
Secret-Bindung wird einmalig unter Settings → Variables als *Secret* angelegt;
sie überlebt spätere Deploys.

**API** (wenn es skriptbar sein soll) — Multipart aus Metadaten + Modul:

```bash
# Der Secret-Wert steht im Secret Manager; nie in ein Log oder eine Datei.
curl -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/{account}/workers/scripts/kurrentschrift-api-proxy" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -F 'metadata={
        "main_module": "worker.js",
        "compatibility_date": "2024-11-01",
        "bindings": [
          {"type": "secret_text", "name": "ORIGIN_SECRET", "text": "<Wert>"}
        ]
      };type=application/json' \
  -F 'worker.js=@infra/cloudflare/kurrentschrift-api-proxy.js;type=application/javascript+module'
```

Die Bindungen sind bei einem Script-`PUT` **vollständig ersetzend**: wer sie
weglässt, entfernt sie — genau die Falle, die auf der Cloud-Run-Seite
`--set-secrets` gegen `--update-secrets` getauscht hat
(`api/cloudbuild.yaml`). Also entweder alle Bindungen mitschicken oder im
Dashboard deployen.

## Messvorschrift: hat der Header den Weg genommen?

`/health` ist vom Origin-Gate ausgenommen und meldet sein Urteil über den
Request, mit dem es gefragt wurde — **nie den Wert**:

| `origin_gate` | heißt |
|---|---|
| `off` | Gate nicht scharf, **kein** Header angekommen |
| `off-seen` | Gate nicht scharf, Header ist angekommen — der Zustand, in dem man vor dem Scharfschalten stehen will |
| `ok` | Gate scharf, Header stimmt |
| `missing` | Gate scharf, kein Header — dieser Weg wäre jetzt tot |
| `mismatch` | Gate scharf, falscher Wert (halb angewendete Rotation) |

```bash
curl -s https://api.kurrentschrift.ink/health   # der öffentliche Weg
curl -s https://kurrentschrift.ink/api/health   # DIESER Worker (mit Access-Cookie)
curl -s https://<api-run-url>/health            # muss "off"/"missing" bleiben: die geschlossene Tür
```

Nach jeder Änderung am Worker, an der Transform-Rule oder am Secret gilt: erst
messen, dann scharf schalten. Reihenfolge und Rollback stehen in
[`frontend-stack.md`](../../docs/reference/frontend-stack.md) §5.
