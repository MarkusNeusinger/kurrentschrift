# Warum `api.routers.eigenhand` das teuerste Modul des Import-Graphen zu sein schien (2026-09-05)

> **Status (2026-09-05): Befund-Journal.** Löst die eine Frage ein, die die
> Runde vom selben Tag offen ließ
> ([`serve-image-importtime-2026-09-05.md`](serve-image-importtime-2026-09-05.md),
> § „Was die Aufteilung neu zeigt": „Warum ausgerechnet dieser Router so aus der
> Reihe fällt, ist hier **nicht** geklärt und wäre die nächste lohnende
> Messung"). Antwort: **er fällt gar nicht aus der Reihe.** Die 64,9 ms sind zu
> gut zwei Dritteln eine GC-Pause, die `-X importtime` dem Modul zuschreibt, das
> gerade läuft. **Es wurde nichts geändert**: kein Import verschoben, keine
> Route umgebaut, kein `gc`-Aufruf eingebaut. Wird nicht fortgeschrieben, nur
> durch eine neue Runde abgelöst.

## Kurzfassung

`api.routers.eigenhand` stand mit **64,9 ms Selbstzeit** an der Spitze der
Modul-Aufteilung — „mehr als `scipy.ndimage` und skimage zusammen, mehr als die
gesamte Trace-Hälfte". Derselbe Import mit **abgeschaltetem Garbage Collector**
kostet das Modul **15,1 ms**, während jedes Nachbarmodul auf seiner Zahl bleibt.
Die Differenz ist keine Arbeit dieses Moduls: sie ist die Generationen-2-Sammlung,
die während seines Modulrumpfs fällig wird, und `-X importtime` bucht jede Pause
auf den Import, der sie unterbricht.

Was übrig bleibt, ist unauffällig: 15,1 ms für **17 Routen** — die meisten im
Repo — neben 12,0 ms für die 12 Routen von `api.routers.templates`. Pro Route
sind das 0,89 gegen 1,00 ms. **Der Router ist der größte, nicht der teuerste.**

Es gibt hier also **keinen aufschiebbaren Import zu finden**. Die Maßnahme, die
diese Zahl senken würde, ist eine Änderung am GC-Verhalten des Prozessstarts —
und die lohnt nach den Zahlen der ersten Runde nicht (siehe „Was daraus folgt").

## Aufbau

Rein lesend, nichts gebaut, nichts angefasst. Arbeits-venv dieses Rechners
(CPython 3.13.12), BLAS gepinnt (`OPENBLAS_NUM_THREADS=1`,
`OMP_NUM_THREADS=1`), jeder Satz in einem frischen Interpreter, **Minimum aus
9 Läufen** je Zelle. Die Absolutwerte liegen damit auf derselben Maschine und
demselben Protokoll wie die Runde vom 2026-09-05 und sind mit deren Spalten
vergleichbar; die venv ist die mit Extras, was `MAIN` laut jener Runde um
etwa 1 ms bewegt.

Zwei Sätze, ein Unterschied:

```bash
python -X importtime -c "import api.main"
python -X importtime -c "import gc; gc.disable(); import api.main"
```

## Die Messung

Selbstzeit je Modul, Minimum aus 9 Läufen:

| Modul | GC an | GC aus | Differenz |
|---|---|---|---|
| **`api.routers.eigenhand`** | **50,6 ms** | **15,1 ms** | **−35,5 ms** |
| `fastapi.openapi.models` | 37,7 ms | 37,6 ms | −0,1 ms |
| `api.schemas` | 26,8 ms | 25,4 ms | −1,4 ms |
| `api.routers.templates` | 11,8 ms | 12,0 ms | +0,2 ms |
| Summe aller Selbstzeiten | 738,4 ms | 667,3 ms | −71,1 ms |

Die letzte Zeile ist der Schlüssel: der ganze Import zahlt **71 ms** an den
Garbage Collector, und **die Hälfte davon landet auf diesem einen Modul**. Jedes
andere Modul der Liste steht still — die Differenzen dort sind Messrauschen.

Ohne GC sieht die Rangliste, die die Vorrunde aufstellte, anders aus:

| Rang | Modul | Selbstzeit (GC aus) |
|---|---|---|
| 1 | `fastapi.openapi.models` | 37,9 ms |
| 2 | `api.schemas` | 26,5 ms |
| 3 | `core.database.models` | 20,5 ms |
| 4 | `scipy.ndimage._support_alternative_backends` | 17,7 ms |
| 5 | `scipy.special._support_alternative_backends` | 15,0 ms |
| **6** | **`api.routers.eigenhand`** | **14,9 ms** |
| 7 | `numpy.f2py.crackfortran` | 13,0 ms |
| 8 | `api.routers.templates` | 12,1 ms |

Der Satz der Vorrunde — „mehr als `scipy.ndimage` und skimage zusammen" — hält
damit nicht: der Router liegt hinter dem `ndimage`-Shim allein.

## Der Beleg, dass die Pause nicht diesem Modul gehört

Zwei unabhängige Gegenproben, beide mit einem Zähler um
`APIRouter.add_api_route` (die Registrierung jeder Route, gemessen je Aufruf),
während `api.main` importiert wird:

1. **Die Pause wandert.** Registriert man vor dem Import eine einzige
   Wegwerf-Route mit Request-Body auf einem Wegwerf-Router, springt der ~35-ms-Block
   auf ein anderes Modul — in einem Lauf auf `api.routers.bboxes`, in einem
   anderen auf eine andere Route desselben Eigenhand-Routers. Auch **innerhalb**
   des Routers wechselt er von Lauf zu Lauf die Route
   (`/uebergangsraum` · `/setups/{hand}` · `/bestand/{hand}`). Ein Kostenblock,
   der bei gleichem Code die Adresse wechselt, gehört keiner Adresse.
2. **Ohne GC verschwindet er.** Die Registrierungszeit aller 90 Routen fällt von
   118–152 ms auf **81–91 ms**, und der Eigenhand-Router von 51–64 ms auf
   **15–17 ms**; `api.routers.templates` bleibt bei 22–27 ms und wird damit zum
   teuersten Router des Repos.

Und eine dritte, ungeplante: der **erste Lauf des neuen CI-Schritts** (derselbe
PR, „Import weight of api.main, measured in the image") misst im echten Image
auf fremder Hardware — und dort steht an der Spitze der Selbstzeiten
`api.routers.pairs` mit **74,5 ms** bei **vier** Routen, während
`api.routers.eigenhand` mit 30,6 ms auf Platz sieben liegt. Ein Router mit vier
Routen kann nicht das teuerste Modul eines 1468-Modul-Graphen sein; der Block
ist derselbe und hat nur wieder die Adresse gewechselt. (Nebenbei geklärt, was
die Vorrunde als ungeprüft notierte: der Interpreter im Image ist **CPython
3.13.15**, hier lief 3.13.12.)

Warum ausgerechnet dort: die Router werden alphabetisch importiert
(`api/routers/__init__.py`), `eigenhand` ist der fünfte. Bis dahin haben
`api.schemas`, die SQLAlchemy-Modelle und die vier Router davor die
Generation 2 gefüllt; die Schwelle reißt im Rumpf des ersten Routers, der
danach 17 Routen am Stück registriert. Das ist Zufall der Reihenfolge, keine
Eigenschaft des Codes — genau deshalb wandert der Block, sobald man vorher
irgendetwas anderes allokiert.

## Was daraus folgt

- **Kein aufschiebbarer Import.** Der Modulrumpf importiert nichts, was nicht
  ohnehin schon geladen wäre (`api.schemas`, `core.database`, `fastapi`,
  `core.eigenhand.*`), rechnet nichts auf Modulebene und liest keine Datei —
  `load_plan()` steht in den Handlern, nicht im Rumpf. Es gibt hier nichts
  byte-neutral nach unten zu schieben.
- **Die Route-Registrierung ist der echte Rest**, und sie ist FastAPIs
  Bauprinzip: `@router.get(response_model=…)` baut sein Serialisierungsmodell
  beim Import. 0,89 ms je Route ist der Hauspreis, nicht ein Ausreißer.
- **GC-Tuning beim Start wäre die einzige Maßnahme** (`gc.freeze()` vor der
  Router-Welle, oder `gc.disable()` über den Import). Sie ist **nicht
  begründbar**: 71 ms auf einen Import von rund 900 ms, und der Import ist nach
  der ersten Runde selbst nur ein Teil der 98 % Containerstart
  ([`serve-image-importgraph-2026-09-04.md`](serve-image-importgraph-2026-09-04.md)).
  Eine Verhaltensänderung am Prozessstart für zwei Prozent Kaltstart ist der
  falsche Handel — und sie einzubauen hieße, eine Zahl zu senken, statt eine
  Arbeit zu sparen.
- **Für spätere Runden ist das die Lehre am Werkzeug:** eine einzelne
  `-X importtime`-Selbstzeit ist keine Kostenaussage über ein Modul, solange die
  GC-Pausen nicht herausgerechnet sind. Wer eine Spitze in der Modul-Aufteilung
  erklären will, misst sie **zuerst mit `gc.disable()` gegen** — und
  vergleicht erst dann Module. Die Bündel-Anteile der Vorrunde (Rahmen 47,9 %,
  Renderpfad 30,7 %, Bild-Pipeline 4,4 %) bleiben davon unberührt: 71 ms
  verteilen sich zwar ungleich, aber ihr Urteil hing an Differenzen von über
  200 ms.

## Grenzen dieser Runde

- Die **GC-Gegenprobe** lief in der Arbeits-venv dieses Rechners, nicht im
  Container. Die Runde vom 2026-09-05 hat gezeigt, dass die Extras für `MAIN`
  etwa 1 ms ausmachen; der GC-Effekt ist um den Faktor 35 größer und hängt an
  Allokationszahlen, die von den Extras nicht berührt werden. Die dritte
  Gegenprobe oben kommt bereits aus dem echten Image, aber ohne
  `gc.disable()`-Arm — sie zeigt das Wandern, nicht die Differenz. Laufende
  Zahlen im Image liefert ab jetzt der CI-Schritt „Import weight of api.main,
  measured in the image" (Job „Image (build + container smoke)", Skript
  `.github/scripts/importtime_report.py`) — Ausgabe ohne Schwelle.
- Gemessen wurde wieder der **Import**, nicht der erste Request.
- Nicht gemessen: ob die GC-Pause bei kleinerem Speicher (Cloud Run 512 MB)
  anders fällt. Für den Entscheid ohne Belang, weil kein Entscheid ansteht.
