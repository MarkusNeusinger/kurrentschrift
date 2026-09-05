# Serve-only API-Image? Der Import-Graph, nachgemessen (2026-09-04)

> **Status (2026-09-05): Befund-Journal, eine offene Messung nachgetragen.**
> Einmalige Messung zum Vorschlag aus
> dem Vollaudit vom 2026-09-02 (Rohbefund „Import-Graph zieht die Bild-Pipeline
> in jeden Prozessstart"), der für eine Aufteilung von `core/pipeline.py`
> „nochmals ~0,5–0,8 s" veranschlagt hat. Diese Runde misst nach, statt zu
> schätzen. **Es wurde nichts geändert** — kein Import verschoben, kein Image
> gebaut; der Entscheid steht beim Autor. Die eine offene Messung („`SERVE` und
> `BOTH` im Image selbst") ist am 2026-09-05 so weit nachgeholt worden, wie es
> ohne Docker geht: [Nachtrag 2026-09-05](#nachtrag-2026-09-05--die-offene-messung-in-einer-image-förmigen-venv).
> Sonst wird die Seite nicht fortgeschrieben, nur durch eine neue Messrunde
> abgelöst.

## Kurzfassung

Der Befund stimmt in der Beobachtung und nicht in der Zahl. Richtig ist: nach
`import api.main` stehen **alle fünf schweren Paketwurzeln** — scipy, numpy,
scikit-image, shapely, Pillow — im Prozess, und die fünf funktionslokalen Importe,
die es im Repo gibt, halten keine einzige davon draußen, weil jede Wurzel
mindestens einen Modulebenen-Pfad hat. Falsch ist die erwartete Ersparnis. Der
Render-Pfad selbst braucht `scipy.interpolate` und `shapely`
(`core/template.py`), und wer `scipy.interpolate` importiert, hat damit
`scipy._lib`, `linalg`, `sparse`, `special`, `optimize`, `spatial` und `fft`
schon im Prozess — 355 der 375 scipy-Module, die `api.main` am Ende lädt. Übrig
zum Weglassen bleiben `scipy.ndimage` und scikit-image.

**Gemessen: die trace-only-Fremdpakete kosten 8 ms, die gesamte Trace-Hälfte
inklusive der eigenen `core`-Module 46 ms — 5 % eines Imports von 910 ms.** Beide
Umbauvorschläge (funktionslokale Importe · Zwei-Image-Split) sind damit als
Kaltstart-Maßnahme nicht begründbar; als Image-Größen-Maßnahme trägt der Split
13,8 MB komprimiert.

Beide Zahlen sind **lokal** gemessen. Was 46 ms im Container werden, ist hier
nicht gemessen worden — dazu müssten beide Import-Sätze im Cloud-Run-Image selbst
laufen (siehe „Grenzen dieser Messung"). Der Vergleich, der ohne diesen Schritt
trägt, ist der lokale: 46 von 910 ms.

## Aufbau

Lokale venv (`uv sync --frozen`, CPython 3.13.12), `__pycache__` warm — das
entspricht dem ausgelieferten Image, seit die Dockerfile `UV_COMPILE_BYTECODE=1`
plus einen `compileall`-Lauf trägt. BLAS-Threads gepinnt, beide einzeln:

```bash
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

Jeder Satz in einem frischen Interpreter (Subprozess), damit `sys.modules` nie
zwischen zwei Messungen überlebt. **Kein Docker in dieser Sitzung**: die
Größenzahlen kommen aus der venv (gzip über die Paketverzeichnisse), nicht aus
`docker manifest` oder der Registry — die venv erreicht das Runtime-Image als ein
einziger `COPY --from=builder`-Layer, und Artifact Registry rechnet komprimiert
ab, also ist gzip der passende Stellvertreter. Zeiten als **Minimum aus 15
Läufen** (Prozessstart streut nur nach oben), Median daneben.

## (a) Was beim Prozessstart geladen wird — alles

`import api.main` → **1.540 Module**, davon aus den schweren Wurzeln:

| Paket | Module | Untermodule im Prozess |
|---|---|---|
| scipy | 375 | ndimage · interpolate · optimize · spatial · linalg · sparse · special · fft · constants |
| numpy | 144 | — |
| skimage | 67 | filters · morphology · draw · measure · transform · util · exposure |
| shapely | 35 | — |
| PIL | 16 | — |

Die auslösende Kette, aus `python -X importtime` rekonstruiert:

```
api.main → api.routers → api.routers.aggregates → api.rendering → core.pipeline
```

`core/pipeline.py` importiert auf Modulebene `scipy.ndimage` und zieht über
`core.chart` (PIL), `core.extract` (scipy.ndimage/spatial, skimage.filters/
morphology), `core.fit` (scipy.interpolate/ndimage/optimize/spatial, shapely) und
`core.quality` (skimage.draw) den ganzen Rest nach.

Ein AST-Lauf über `api/` und `core/` zählt **38 Importe schwerer Pakete auf
Modulebene** — alle in `core/` — gegen **5 funktionslokale**:
`core/aggregate.py::spline_basis_median` (`scipy.interpolate`), zweimal
`core/eigenhand/crop.py::without_rulings` (numpy, PIL), einmal `::cut_png` (PIL)
und `api/routers/eigenhand.py::_png_size` (PIL). In `api/` steht sonst kein
einziger direkter Import eines schweren Pakets; die API erbt sie alle.

Wichtig für jeden Umbau: eine Verlagerung in `core/pipeline.py` **allein bringt
nichts**, weil weitere Router dieselben Module auf Modulebene ziehen —
`api/routers/templates.py` (`core.fit`, `core.quality`,
`core.quality_suetterlin`, `core.suetterlin`, `core.laufform`),
`api/routers/word_samples.py` (`core.word_metric`, `core.chart`),
`api/routers/chart.py` und `api/routers/styles.py` (`core.chart`),
`api/routers/bboxes.py` (`core.pipeline`), `api/routers/aggregates.py`
(`core.laufform`). `chart.py` und `styles.py` bedienen **öffentliche** Reads —
Pillow kann also ohnehin nicht weg.

## (b) Größe

| Paket | installiert | gzip |
|---|---|---|
| scipy + `scipy.libs` | 117,6 MB | **36,9 MB** |
| numpy + `numpy.libs` | 60,6 MB | **17,8 MB** |
| scikit-image | 30,3 MB | **13,8 MB** |
| Pillow + `pillow.libs` | 19,9 MB | **7,0 MB** |
| shapely | 5,2 MB | **1,4 MB** |
| Summe | 233,6 MB | **76,9 MB** |

Zum Vergleich: die ganze site-packages dieser venv sind 375 MB installiert (mit
Dev-Extras, die das Image nicht bekommt — die Zeilen oben sind die belastbaren
Zahlen, die Summe unten nicht). Die Dockerfile hält für das Image selbst fest:
1,61 GB entpackt vorher, 531 MB nach der Zweistufen-Umstellung.

Davon **abtrennbar ist allein scikit-image**: 13,8 MB komprimiert. scipy hängt
am Render-Pfad, numpy an allem, Pillow an den öffentlichen Chart-Reads.

## (c) Was die Trace-Hälfte am Import kostet

Die Sätze wörtlich, damit eine spätere Runde denselben Vergleich fahren kann —
der Import-Cache macht die genaue Modulliste und ihre Reihenfolge material für
die Differenz. Jede Zeile lief 15×, jeweils
`subprocess.run([".venv/bin/python", "-c", <Satz>])` aus einem frischen
Interpreter:

```python
BARE   = "pass"
NUMPY  = "import numpy"
RENDER = "import numpy, shapely; from scipy.interpolate import CubicSpline"
TRACE  = RENDER + "; import scipy.ndimage, skimage.filters, skimage.morphology, skimage.draw"
WEBDB  = "import fastapi, jwt, httpx, orjson; import core.database"
SERVE  = ("import fastapi, jwt, httpx, orjson, PIL.Image; "
          "import core.database, core.template, core.widths, core.compose, core.shaping, core.rounding")
BOTH   = SERVE + ("; import core.pipeline, core.fit, core.chart, core.extract, core.quality, "
                  "core.quality_suetterlin, core.suetterlin, core.word_metric, core.laufform, core.aggregate")
MAIN   = "import api.main"
```

| Satz | min | Median |
|---|---|---|
| `BARE` — nackter Interpreter | 8 ms | 10 ms |
| `NUMPY` | 54 ms | 59 ms |
| `RENDER` — was `core/template.py` braucht | **305 ms** | 329 ms |
| `TRACE` — `RENDER` plus die trace-only-Fremdpakete | **313 ms** | 353 ms |
| `WEBDB` | 416 ms | 441 ms |
| `SERVE` — die Serve-Hälfte | **687 ms** | 711 ms |
| `BOTH` — `SERVE` plus die Trace-Hälfte | **733 ms** | 757 ms |
| `MAIN` — `import api.main`, wie es heute ist | **910 ms** | 937 ms |

Zwei Differenzen tragen den ganzen Befund:

- **313 − 305 = 8 ms.** So viel kosten `scipy.ndimage` und scikit-image, wenn
  numpy und der scipy-Unterbau ohnehin schon geladen sind.
- **733 − 687 = 46 ms.** So viel kostet die komplette Trace-Hälfte, die eigenen
  `core`-Module eingerechnet.

Warum die Schätzung „~0,5–0,8 s" so weit danebenliegt: sie hat die Kosten aus
einer Messung *gegen einen leeren Interpreter* gelesen (`scipy.ndimage` allein
187 ms, `skimage.filters+morphology` allein 228 ms). In einem Prozess, der numpy
und `scipy.interpolate` bereits geladen hat, ist davon fast nichts mehr übrig.

Dass `scipy.interpolate` und `shapely` wirklich zum Render-Pfad gehören, ist
nicht abkürzbar: `core/template.py:81` splined die Anker mit `CubicSpline`
(`sample_polyline`), und `capsule_union_rings`/`chisel_union_rings` bauen die
Silhouette mit `shapely.buffer`/`union_all` — beides ruft
`render_payload_for_template` über `multi_stroke_silhouettes` /
`multi_stroke_centerlines` auf, also der `/write`-Pfad selbst.

**Und gegen den Kaltstart?** Hier hört die Messung auf. `api/cloudbuild.yaml`
nennt p50 9.447 ms und p95 12.245 ms, davon 98 % Containerstart plus
Python-Import; die Bytecode-Umstellung hat davon ~2,2 s genommen. Die 46 ms sind
aber **lokal** gemessen, und wie sie im Container skalieren, ist offen: dort ist
alles langsamer, aber nicht notwendig gleichmäßig (kalter Seiten-Cache trifft
große `.so`-Dateien anders als kleine `.pyc`). Wer die Prozentzahl braucht, muss
`SERVE` und `BOTH` **im Image selbst** messen — ein Einzeiler im Container, den
diese Runde ohne Docker nicht fahren konnte.

Was ohne diesen Schritt trägt und für den Entscheid reicht: **46 von 910 ms sind
5 % des Imports**, und der Import ist nur ein Teil der 98 %. Selbst unter der
großzügigsten Annahme — die Anteile übertragen sich eins zu eins — landet man
unter einem Prozent des Kaltstarts; günstiger wird die Rechnung für den Umbau
nicht.

## Zwei Wege, und was sie kosten

### A · Funktionslokale Importe in den Handlern

Zu tun: `core/pipeline.py` (scipy.ndimage plus `core.chart/extract/fit/quality`)
**und** jeder Modulebenen-Import der Trace-Hälfte in den Routern (Liste in (a)).
`core.chart` bleibt, weil `chart.py`/`styles.py` öffentlich lesen.

Kosten: ~46 ms von einem lokalen Import von 910 ms, also 5 % der Importzeit und
weniger als ein Prozent eines Kaltstarts von 9,4 s (letzteres gerechnet, nicht
gemessen — siehe oben); die Latenzspitze wandert auf den
ersten Derive-/Trace-Aufruf; und ein dauerhafter Lesbarkeitspreis — CLAUDE.md
formuliert für die Werkzeug-Regel bereits „a deferred import inside a function is
the same bug, just later", das Idiom steht im Repo also unter Vorbehalt.

Urteil: **als Kaltstart-Maßnahme nicht begründbar.** Lohnend würde der Umbau
erst, wenn `core/template.py` `CubicSpline` und `shapely` vom Render-Pfad
lösen könnte — ein anderes, deutlich größeres Vorhaben.

### B · Zwei-Image-Split (Serve-Image ohne scikit-image)

Zu tun: eine `serve`-Dependency-Gruppe ohne `scikit-image`, ein zweites
Dockerfile-Target, ein zweiter Cloud-Run-Dienst oder eine Build-Arg-Matrix, das
Migrate-/Admin-Image weiterhin mit dem vollen Satz — **plus die gleiche
Import-Chirurgie wie A**, denn ein Serve-Image, das `core.extract` importiert,
stirbt beim Start statt beim Request. Dazu CI für beide Images.

Gewinn: 13,8 MB komprimiert von ~500 MB (≈3 %) und dieselben 8 ms. scipy, numpy
und Pillow bleiben in beiden Images.

Urteil: **der kleinste der drei Größenposten gegen ein zweites Image, das dauerhaft
ehrlich gehalten werden muss.** Als Kaltstart-Maßnahme trägt er nichts, was A
nicht auch trüge.

## Was den Kaltstart wirklich bewegen würde

- Die **416 ms** für `fastapi` + SQLAlchemy + `jwt` + `httpx` + `orjson` sind
  größer als die ganze Trace-Hälfte und standen im Audit nie im Blick. Ob davon
  etwas lazy werden kann (SQLAlchemy lädt 157 Module), ist die Frage mit dem
  größeren Hebel.
- Die **305 ms** für numpy + shapely + `scipy.interpolate` sind der Eigenpreis
  des Render-Pfads und schrumpfen nur, wenn sich ändert, womit
  `core/template.py` rechnet.
- Autoskalierungs-Kaltstarts sind durch `min-instances=1` bereits weg; was übrig
  bleibt, sind Recycle-Starts (zwei am 2026-09-01, 16,1 s und 11,0 s) —
  gegen die hilft eine Verkürzung des Imports um 46 ms ebenfalls nicht messbar.

## Grenzen dieser Messung

- Keine Docker-Instanz verfügbar: Größen aus der lokalen venv (gzip über die
  Paketverzeichnisse), nicht aus der Registry. Das Verhältnis ist der Befund,
  die absoluten Bytes sind ein guter Näherungswert für den venv-Layer.
- Zeiten auf einer WSL2-Entwicklungsmaschine mit warmem Seiten-Cache. Der
  Vergleich gilt **innerhalb dieser Umgebung**: alle acht Sätze liefen im selben
  Zustand, also ist die Differenz belastbar. Der Container ist langsamer, und ob
  sich das Verhältnis dorthin überträgt, ist **nicht gemessen** — die eine offene
  Messung, die diese Runde nicht fahren konnte. (`api/cloudbuild.yaml` nennt aus
  demselben Grund seine lokalen Bytecode-Zahlen eine Obergrenze für die dortige
  ERSPARNIS; hier geht es um die absolute Importdauer, das ist eine andere Größe
  — beides heißt aber dasselbe: die Absolutwerte sind lokal, das Verhältnis ist
  der Befund.)
- Gemessen wurde der Import, nicht der erste Request. Ein funktionslokaler
  Import verschiebt Zeit, er löscht sie nicht.
- Die Prozentzahlen gegen den Kaltstart sind gerechnet, nicht gemessen. Wer sie
  belastbar braucht, misst `SERVE` und `BOTH` im Cloud-Run-Image selbst.

---

## Nachtrag 2026-09-05 — die offene Messung, in einer image-förmigen venv

Die Runde oben schließt mit einer benannten offenen Messung: `SERVE` und `BOTH`
**im Image selbst**. Dieser Nachtrag holt davon nach, was ohne Container-Laufzeit
zu haben ist, und sagt genauso deutlich, was er nicht ist.

### Warum es kein Lauf im Image ist

Auf dieser Maschine gibt es **kein Docker und kein Podman** — das ausgelieferte
Image lässt sich also weder ziehen noch starten. Der zweite denkbare Weg, ein
`gcloud builds submit` mit einem Einzeiler im Image, ist für diese Runde
ausgeschlossen: er kostet Geld und fasst Infrastruktur an, und eine Messung ist
kein Grund dafür. Was gelesen wurde, ist reine Metadaten-Auskunft: der Dienst
`kurrentschrift-api` in `europe-west4` läuft auf
`kurrentschrift-api:a2a66996-052a-48d5-91ff-4e6cb30665b2`,
Digest `sha256:b23043d2ff2e…`, gebaut 2026-09-05T00:03 UTC.

### Was der Stellvertreter besser macht als die Runde vom 2026-09-04

Der Lauf vom 04. maß in der **Arbeits-venv** — die trägt `dev`, `test` und `viz`
(ruff, pytest, matplotlib, scipy-stubs), die das Image nie sieht. Dieser Lauf
baut die venv so, wie `api/Dockerfile` sie baut:

```bash
UV_PROJECT_ENVIRONMENT=<eigene venv> UV_COMPILE_BYTECODE=1 uv sync --frozen --no-dev
<venv>/bin/python -m compileall -q api core alembic
```

Also: derselbe `uv.lock`, **keine** Extras (88 Pakete statt der Arbeits-venv),
Bytecode vorkompiliert für die venv *und* für `api/`/`core/`/`alembic/` — genau
die zwei `compileall`-Schritte der Dockerfile. Interpreter CPython 3.13.12; das
Image bringt `python:3.13-slim`, dessen Patch-Stand hier nicht prüfbar ist.
Protokoll wie oben: BLAS gepinnt (`OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`),
jeder Satz in einem frischen Interpreter, **Minimum aus 31 Läufen**, und die
Sätze **verschachtelt** statt blockweise — ein Block von 31 dauert lange genug,
dass Maschinen-Drift auf einem Satz landet und auf dem anderen nicht, und die
Differenzen sind der ganze Befund.

Was er weiterhin nicht ist: eine Messung im Container. Der Seiten-Cache, die
CPU-Zuteilung und die Dateisystem-Schicht von Cloud Run bleiben ungemessen.

### Die acht Sätze, image-förmig

Wörtlich dieselben Sätze wie in (c), damit die Spalten vergleichbar sind.

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

`MAIN` reproduziert die alte Zahl auf 1 ms genau (911 gegen 910). Die Mediane
liegen diesmal deutlich über den Minima — die Maschine war unter Last —, deshalb
gilt hier wie dort: **belastbar ist das Minimum**, die Mediane stehen nur als
Streuungsangabe daneben.

Die zwei Differenzen, die den Befund tragen:

- **`BOTH` − `SERVE` = 52,7 ms** (2026-09-04: 46 ms). Die komplette Trace-Hälfte
  kostet **5,8 % eines Imports von 911 ms**.
- **`TRACE` − `RENDER` = 29,9 ms** (2026-09-04: 8 ms). Diese Differenz ist die
  wacklige der beiden: `RENDER` fällt in der schlanken venv um 38 ms, `TRACE` nur
  um 16 ms, und beide Zahlen sind Differenzen zweier Minima, nicht Minima einer
  Differenz. Für den Entscheid ändert die Spanne 8–30 ms nichts.

### Der Import, nach Modulen aufgeteilt

Neu gegenüber dem 04.: statt nur der Sätze auch die Aufteilung des einen Laufs.
`python -X importtime -c "import api.main"`, bester von sieben Läufen (975 ms
Wanduhr, 1445 Module, **791 ms Selbstzeit** in Summe). Gerechnet wird mit der
**Selbstzeit** (`self`), weil nur die additiv ist — die kumulierte Spalte zählt
jeden verschachtelten Import mehrfach.

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

Ein zweiter, unter höherer Last gefahrener Lauf (1324 ms Wanduhr) liefert dieselbe
Aufteilung: Bild-Pipeline 5,4 %, Rahmen 49,4 %. Die **Anteile sind stabil**, auch
wenn die Absolutwerte mit der Maschinenlast wandern.

**Zur Bündelung.** `shapely` gehört hier ausdrücklich **nicht** zur
Bild-Pipeline, sondern zum `/write`-Pfad: `core/template.py` importiert es auf
Modulebene für `capsule_union_rings`/`chisel_union_rings`, zusammen mit
`scipy.interpolate` für `sample_polyline`. Wer die vier Namen
„`scipy.ndimage`, skimage, `core.fit`, shapely" als eine Gruppe rechnet, rechnet
den Renderpfad in die Ersparnis hinein — das ist genau der Fehler, den die Runde
vom 04. an der ursprünglichen Schätzung gefunden hat. Abtrennbar sind
`scipy.ndimage` und scikit-image, und mit ihnen die zehn `core`-Module der
Trace-Hälfte.

### Urteil

**Der Befund von #523 hält, jetzt von zwei unabhängigen Seiten.** Der
Satz-Vergleich sagt 52,7 ms von 911 ms (5,8 %), die Modul-Aufteilung sagt 34,9 ms
von 791 ms (4,4 %) — die Differenz zwischen beiden ist der `core`-Anteil, den der
Satz `BOTH` mitzieht und den `-X importtime` feiner aufschlüsselt. Beide Wege
landen bei „einige Prozent des Imports", und der Import ist selbst nur ein Teil
der 98 % Containerstart. Weder das funktionslokale Verschieben (Weg A) noch der
Zwei-Image-Split (Weg B) ist als Kaltstart-Maßnahme begründbar. **Es wurde
wieder nichts geändert** — kein Import verschoben, kein trivialer Lazy-Import
gefunden, der ohne Verhaltensänderung etwas brächte: jede schwere Wurzel hat
weiterhin mindestens einen Modulebenen-Pfad, wie (a) auflistet.

### Was die Aufteilung neu zeigt

Die Runde vom 04. nannte die 416 ms für `fastapi`+SQLAlchemy+`jwt`+`httpx`
„die Frage mit dem größeren Hebel". Die Modul-Aufteilung schärft das:

- **Der Rahmen ist fast die Hälfte des Imports (47,9 %)**, die Bild-Pipeline ein
  Elftel davon. Wer den Kaltstart angehen will, fängt hier an, nicht bei
  scikit-image.
- **`api.routers.eigenhand` ist das teuerste Einzelmodul des ganzen Graphen**
  (64,9 ms Selbstzeit, im zweiten Lauf 72,6 ms) — mehr als `scipy.ndimage` und
  skimage zusammen, mehr als die gesamte Trace-Hälfte. Es hat keine eigenen
  Pydantic-Modelle; teuer ist der Modulrumpf mit seinen 17 Routen (der nächste
  Router hat 12 und kostet 14,6 ms). Ein Vorab-Import eines anderen Routers senkt
  die Zahl nicht — die Kosten sind seine eigenen, nicht ein geteilter
  Erstzugriff. Warum ausgerechnet dieser Router so aus der Reihe fällt, ist
  hier **nicht** geklärt und wäre die nächste lohnende Messung.
- `fastapi.openapi.models` (41,8 ms) und `api.schemas` (32,1 ms) sind die Plätze
  zwei und drei. Alle drei liegen im eigenen Code bzw. in seiner
  Schema-Erzeugung, nicht in der Wissenschaft.

### Grenzen dieses Nachtrags

- **Immer noch kein Lauf im Container.** Die Formfrage der venv ist geklärt (die
  Extras spielten keine Rolle: `MAIN` bewegt sich um 1 ms), die
  Laufzeitumgebung nicht. Dieser Nachtrag macht den Stellvertreter nur so eng,
  wie er ohne Docker werden kann.

  **Der Weg dorthin ist aber benannt und kostet nichts:** der CI-Job
  „Image (build + container smoke)" (`.github/workflows/ci.yml`) baut
  `api/Dockerfile` bereits bei jedem PR und lädt das Ergebnis in den lokalen
  Daemon (`load: true`), damit der Smoke-Test es starten kann. Ein einmaliger
  Schritt mit `docker exec -i api /app/.venv/bin/python` in genau diesem Job
  misst die acht Sätze **im echten Image** — dieselben Layer, derselbe
  Interpreter-Patchstand, derselbe vorkompilierte Bytecode —, kostet
  Runner-Minuten und fasst keine Infrastruktur an. Was er weiterhin nicht
  liefert, ist die Cloud-Run-Hardware; er schließt die Image-Frage, nicht die
  Maschinen-Frage. (In dieser Sitzung nicht gefahren: eine Änderung an einer
  geteilten CI-Datei ist ein eigener Entscheid, kein Nebenprodukt einer
  Messung.)
- Der Patch-Stand des Interpreters im Image (`python:3.13-slim`) ist nicht
  geprüft; hier lief 3.13.12.
- Die Größenzahlen aus (b) bleiben venv-gzip-Stellvertreter — Artifact Registry
  gibt über `gcloud artifacts docker images` keine komprimierte Größe heraus, und
  weiter zu gehen hieße, mit einem Zugriffstoken selbst an die Registry-API zu
  gehen. Nicht gemacht.
- Gemessen wurde wieder der Import, nicht der erste Request.
