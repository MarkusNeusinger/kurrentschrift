# Serve-only API-Image? Der Import-Graph, nachgemessen (2026-09-04)

> **Status (2026-09-04): Befund-Journal.** Einmalige Messung zum Vorschlag aus
> dem Vollaudit vom 2026-09-02 (Rohbefund „Import-Graph zieht die Bild-Pipeline
> in jeden Prozessstart"), der für eine Aufteilung von `core/pipeline.py`
> „nochmals ~0,5–0,8 s" veranschlagt hat. Diese Runde misst nach, statt zu
> schätzen. **Es wurde nichts geändert** — kein Import verschoben, kein Image
> gebaut; der Entscheid steht beim Autor. Wird nicht fortgeschrieben, nur durch
> eine neue Messrunde abgelöst.

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
