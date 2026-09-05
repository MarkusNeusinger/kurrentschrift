# Der Import von `api.main`, image-förmig gemessen und nach Modulen aufgeteilt (2026-09-05)

> **Status (2026-09-05): Befund-Journal.** Die zweite Runde zur Frage aus dem
> Vollaudit vom 2026-09-02, ob ein Serve-only-Image lohnt. Sie löst die eine
> offene Messung der ersten Runde ein
> ([`serve-image-importgraph-2026-09-04.md`](serve-image-importgraph-2026-09-04.md),
> „Grenzen dieser Messung": `SERVE` und `BOTH` im Image selbst) — so weit, wie es
> ohne Container-Laufzeit geht — und teilt den Import erstmals nach Modulen auf.
> **Es wurde nichts geändert**: kein Import verschoben, kein Image gebaut, kein
> CI-Job angefasst. Wird nicht fortgeschrieben, nur durch eine neue Runde
> abgelöst. Die Zahlen der ersten Runde bleiben gültig; diese Runde bestätigt
> ihr Urteil und schärft es an einer Stelle.

## Kurzfassung

Die erste Runde maß in der **Arbeits-venv** — der mit `dev`, `test` und `viz`,
die das Image nie sieht — und schloss mit einer benannten offenen Messung.
Diese Runde baut die venv so, wie `api/Dockerfile` sie baut, und misst neu:
`import api.main` reproduziert die alte Zahl auf 1 ms genau (**911 gegen
910 ms**), die Extras spielten also keine Rolle. Die Trace-Hälfte kostet
**52,7 ms von 911 ms**, und eine neue Aufteilung des Imports über
`-X importtime` legt die Bild-Pipeline bei **34,9 ms von 791 ms Selbstzeit —
4,4 %** ab. **Das Urteil von 2026-09-04 hält**, jetzt von zwei Seiten belegt.

Die Aufteilung zeigt zusätzlich, was die ursprüngliche Schätzung nie im Blick
hatte: der **Web-/DB-/API-Rahmen ist 47,9 %** des Imports — die Hälfte —, und
`api.routers.eigenhand` allein kostet mehr als `scipy.ndimage` und
scikit-image zusammen.

## Warum es kein Lauf im Image ist

Auf dieser Maschine gibt es **kein Docker und kein Podman** — das ausgelieferte
Image lässt sich also weder ziehen noch starten. Der zweite denkbare Weg, ein
`gcloud builds submit` mit einem Einzeiler im Image, ist für diese Runde
ausgeschlossen: er kostet Geld und fasst Infrastruktur an, und eine Messung ist
kein Grund dafür. Was gelesen wurde, ist reine Metadaten-Auskunft: der Dienst
`kurrentschrift-api` in `europe-west4` läuft auf
`kurrentschrift-api:a2a66996-052a-48d5-91ff-4e6cb30665b2`,
Digest `sha256:b23043d2ff2e…`, gebaut 2026-09-05T00:03 UTC.

## Aufbau — was der Stellvertreter besser macht als die erste Runde

Die venv wird gebaut, wie `api/Dockerfile` sie baut:

```bash
UV_PROJECT_ENVIRONMENT=<eigene venv> UV_COMPILE_BYTECODE=1 uv sync --frozen --no-dev
<venv>/bin/python -m compileall -q api core alembic
```

Also: derselbe `uv.lock`, **keine** Extras, Bytecode vorkompiliert für die venv
*und* für `api/`/`core/`/`alembic/` — genau die zwei `compileall`-Schritte der
Dockerfile. Interpreter CPython 3.13.12; das Image bringt `python:3.13-slim`,
dessen Patch-Stand hier nicht prüfbar ist.

Protokoll wie in der ersten Runde: BLAS gepinnt (`OPENBLAS_NUM_THREADS=1`,
`OMP_NUM_THREADS=1`), jeder Satz in einem frischen Interpreter, **Minimum aus
31 Läufen** — und die Sätze **verschachtelt** statt blockweise: ein Block von 31
dauert lange genug, dass Maschinen-Drift auf einem Satz landet und auf dem
anderen nicht, und die Differenzen sind der ganze Befund.

Was er weiterhin nicht ist: eine Messung im Container. Der Seiten-Cache, die
CPU-Zuteilung und die Dateisystem-Schicht von Cloud Run bleiben ungemessen.

## Die acht Sätze, image-förmig

Wörtlich dieselben Sätze wie in Abschnitt (c) der ersten Runde, damit die
Spalten vergleichbar sind.

| Satz | min | Median | zum Vergleich: 2026-09-04 (min) |
|---|---|---|---|
| `BARE` | 8,4 ms | 11,5 ms | 8 ms |
| `NUMPY` | 50,2 ms | 69,8 ms | 54 ms |
| `RENDER` | 267,1 ms | 378,1 ms | 305 ms |
| `TRACE` | 297,0 ms | 432,9 ms | 313 ms |
| `WEBDB` | 408,6 ms | 591,6 ms | 416 ms |
| `SERVE` | **665,8 ms** | 946,2 ms | 687 ms |
| `BOTH` | **718,5 ms** | 1060,2 ms | 733 ms |
| `MAIN` | **911,1 ms** | 1312,5 ms | 910 ms |

Die Mediane liegen diesmal deutlich über den Minima — die Maschine war unter
Last —, deshalb gilt hier wie dort: **belastbar ist das Minimum**, die Mediane
stehen nur als Streuungsangabe daneben.

Die zwei Differenzen, die den Befund tragen:

- **`BOTH` − `SERVE` = 52,7 ms** (2026-09-04: 46 ms). Die komplette
  Trace-Hälfte kostet **5,8 % eines Imports von 911 ms**.
- **`TRACE` − `RENDER` = 29,9 ms** (2026-09-04: 8 ms). Diese Differenz ist die
  wacklige der beiden: `RENDER` fällt in der schlanken venv um 38 ms, `TRACE`
  nur um 16 ms, und beide Zahlen sind Differenzen zweier Minima, nicht Minima
  einer Differenz. Für den Entscheid ändert die Spanne 8–30 ms nichts.

## Der Import, nach Modulen aufgeteilt

Neu gegenüber der ersten Runde: statt nur der Sätze auch die Aufteilung eines
einzelnen Laufs. `python -X importtime -c "import api.main"`, bester von sieben
Läufen (975 ms Wanduhr, 1445 Module, **791 ms Selbstzeit** in Summe). Gerechnet
wird mit der **Selbstzeit** (`self`), weil nur die additiv ist — die kumulierte
Spalte zählt jeden verschachtelten Import mehrfach.

Die zehn teuersten Einzelmodule:

| Modul | Selbstzeit |
|---|---|
| `api.routers.eigenhand` | 64,9 ms |
| `fastapi.openapi.models` | 41,8 ms |
| `api.schemas` | 32,1 ms |
| `core.database.models` | 23,4 ms |
| `scipy.special._support_alternative_backends` | 17,3 ms |
| `scipy.ndimage._support_alternative_backends` | 16,9 ms |
| `api.routers.templates` | 14,6 ms |
| `numpy.f2py.crackfortran` | 14,3 ms |
| `charset_normalizer.api` | 10,8 ms |
| `core.database.repositories` | 10,2 ms |

Und dieselben 791 ms nach Zweck gebündelt:

| Bündel | Selbstzeit | Anteil |
|---|---|---|
| **Web-/DB-/API-Rahmen** — `api` 166,6 · sqlalchemy 109,0 · fastapi+starlette+pydantic 103,2 | **378,8 ms** | **47,9 %** |
| **`/write`-Renderpfad** — scipy ohne `ndimage` 134,8 · numpy 56,1 · `core` Serve-Hälfte 37,9 · PIL 7,7 · shapely 6,3 | **242,8 ms** | **30,7 %** |
| **Bild-Pipeline (nur Trace)** — `scipy.ndimage` 21,1 · skimage 9,0 · `core` Trace-Hälfte 4,8 (davon `core.fit` 1,8) | **34,9 ms** | **4,4 %** |
| Rest (stdlib, charset_normalizer, anyio, cryptography …) | 134,9 ms | 17,0 % |

Ein zweiter, unter höherer Last gefahrener Lauf (1324 ms Wanduhr) liefert
dieselbe Aufteilung: Bild-Pipeline 5,4 %, Rahmen 49,4 %. Die **Anteile sind
stabil**, auch wenn die Absolutwerte mit der Maschinenlast wandern.

**Zur Bündelung.** `shapely` gehört ausdrücklich **nicht** zur Bild-Pipeline,
sondern zum `/write`-Pfad: `core/template.py` importiert es auf Modulebene für
`capsule_union_rings`/`chisel_union_rings`, zusammen mit `scipy.interpolate` für
`sample_polyline`. Wer die vier Namen „`scipy.ndimage`, skimage, `core.fit`,
shapely" als eine Gruppe rechnet, rechnet den Renderpfad in die Ersparnis
hinein — genau der Fehler, den die erste Runde an der ursprünglichen Schätzung
gefunden hat. Abtrennbar sind `scipy.ndimage` und scikit-image, und mit ihnen
die zehn `core`-Module der Trace-Hälfte.

## Urteil

**Das Urteil der ersten Runde hält, jetzt von zwei unabhängigen Seiten.** Der
Satz-Vergleich sagt 52,7 ms von 911 ms (5,8 %), die Modul-Aufteilung sagt
34,9 ms von 791 ms (4,4 %).

Die beiden Zahlen messen dasselbe auf zwei Wegen und stimmen nicht auf die
Millisekunde überein — **der Abstand ist keinem Modul zuzuschlagen**: `BOTH`
zieht die `core`-Trace-Module mit, und die 34,9 ms enthalten sie ebenfalls
(4,8 ms). Was die Differenz erklärt, ist die Methode: 52,7 ms ist die Differenz
zweier **Prozess-Minima** (Prozessstart und Interpreter-Boot stecken in beiden
Summanden und kürzen sich nur näherungsweise), 34,9 ms eine Aufteilung
**innerhalb eines Laufs**; dazu die Streuung, die auf dieser Maschine sichtbar
ist. Für den Entscheid trägt beides dasselbe: einige Prozent des Imports, und
der Import ist selbst nur ein Teil der 98 % Containerstart. Weder das
funktionslokale Verschieben (Weg A der ersten Runde) noch der Zwei-Image-Split
(Weg B) ist als Kaltstart-Maßnahme begründbar.

**Es wurde wieder nichts geändert** — kein Import verschoben, kein trivialer
Lazy-Import gefunden, der ohne Verhaltensänderung etwas brächte: jede schwere
Wurzel hat weiterhin mindestens einen Modulebenen-Pfad, wie Abschnitt (a) der
ersten Runde auflistet.

## Was die Aufteilung neu zeigt

Die erste Runde nannte die 416 ms für `fastapi`+SQLAlchemy+`jwt`+`httpx` „die
Frage mit dem größeren Hebel". Die Modul-Aufteilung schärft das:

- **Der Rahmen ist fast die Hälfte des Imports (47,9 %)**, die Bild-Pipeline ein
  Elftel davon. Wer den Kaltstart angehen will, fängt hier an, nicht bei
  scikit-image.
- **`api.routers.eigenhand` ist das teuerste Einzelmodul des ganzen Graphen**
  (64,9 ms Selbstzeit, im zweiten Lauf 72,6 ms) — mehr als `scipy.ndimage` und
  skimage zusammen, mehr als die gesamte Trace-Hälfte. Es hat keine eigenen
  Pydantic-Modelle; teuer ist der Modulrumpf mit seinen 17 Routen (der nächste
  Router hat 12 und kostet 14,6 ms). Ein Vorab-Import eines anderen Routers
  senkt die Zahl nicht — die Kosten sind seine eigenen, nicht ein geteilter
  Erstzugriff. Warum ausgerechnet dieser Router so aus der Reihe fällt, ist
  hier **nicht** geklärt und wäre die nächste lohnende Messung.
- `fastapi.openapi.models` (41,8 ms) und `api.schemas` (32,1 ms) sind die Plätze
  zwei und drei. Alle drei liegen im eigenen Code bzw. in seiner
  Schema-Erzeugung, nicht in der Wissenschaft.

## Grenzen dieser Runde

- **Immer noch kein Lauf im Container.** Die Formfrage der venv ist geklärt (die
  Extras spielten keine Rolle: `MAIN` bewegt sich um 1 ms), die Laufzeitumgebung
  nicht.

  **Der Weg dorthin ist aber benannt und kostet nichts:** der CI-Job
  „Image (build + container smoke)" (`.github/workflows/ci.yml`) baut
  `api/Dockerfile` bereits bei jedem PR und lädt das Ergebnis in den lokalen
  Daemon (`load: true`), damit der Smoke-Test es starten kann. Ein einmaliger
  Schritt mit `docker exec -i api /app/.venv/bin/python` in genau diesem Job
  misst die acht Sätze **im echten Image** — dieselben Layer, derselbe
  Interpreter-Patchstand, derselbe vorkompilierte Bytecode —, kostet
  Runner-Minuten und fasst keine Infrastruktur an. Was er weiterhin nicht
  liefert, ist die Cloud-Run-Hardware; er schließt die Image-Frage, nicht die
  Maschinen-Frage. (In dieser Runde nicht gefahren: eine Änderung an einer
  geteilten CI-Datei ist ein eigener Entscheid, kein Nebenprodukt einer
  Messung.)
- Der Patch-Stand des Interpreters im Image (`python:3.13-slim`) ist nicht
  geprüft; hier lief 3.13.12.
- Die Größenzahlen der ersten Runde bleiben venv-gzip-Stellvertreter — Artifact
  Registry gibt über `gcloud artifacts docker images` keine komprimierte Größe
  heraus, und weiter zu gehen hieße, mit einem Zugriffstoken selbst an die
  Registry-API zu gehen. Nicht gemacht.
- Gemessen wurde wieder der Import, nicht der erste Request. Ein
  funktionslokaler Import verschiebt Zeit, er löscht sie nicht.
