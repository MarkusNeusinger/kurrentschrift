# Write-API — die öffentlichen Render-Endpunkte

> **Status (2026-08-03): lebend.** Beschreibt die ausgelieferten
> `/write/*`-Endpunkte; jede Änderung an `api/routers/write.py` (inkl.
> `compose_word_payload`), `core/shaping.py`, `core/compose.py`, dem
> Render-Payload oder den Cache-Headern muss hier nachgezogen werden.
> Der Abschnitt [„Ratenbegrenzung“](#ratenbegrenzung--zwei-buckets-eng-vor-weit)
> beschreibt seit dem 2026-09-02 die Buckets der GANZEN API, nicht nur die des
> Kompositionspfads — er ist die eine Stelle, an der das Limit dokumentiert
> ist, und gehört zu `api/rate_limit.py`.

Dieses Dokument beschreibt den ausgelieferten Stand; die Design-Geschichte
und verworfenen Alternativen stehen im Proposal
[`schreibsystem-und-wortbench.md`](../proposals/schreibsystem-und-wortbench.md).

Die Write-API ist der chart-freie Render-Pfad hinter allen öffentlichen
„as written“-Flächen (Federprobe, Schreibtafel, Quiz-Prompts, das
Sütterlin-Specimen auf `/schriftkunde`). Sie liest ausschließlich
`templates`-Zeilen — kein Chart-I/O, keine Bild-Pipeline — und ist
deshalb schnell genug für Cache-Control + gzip.

## Endpunkte

| Endpunkt | Zweck |
|---|---|
| `GET /sources/{id}/write/glyphs?keys=a,n,…[&variant=100]` | Batch: pro `glyph_key` (Basis-Keys seit R2, z. B. `a`, `longs`, `ch`) das Render-Payload eines einzelnen Buchstabens; nicht autorisierte Keys landen in `missing`, nie als Fehler. `variant` wählt die gespeicherte Form — Default 0 ist der autorisierte Tafel-Duktus, den jede öffentliche Fläche schreibt; `100` (`LAUFFORM_VARIANT`) die abgeleitete Laufform, die die Admin-Buchstabenansicht daneben zeigt. Eine Glyphe ohne Zeile für die gefragte Variante verhält sich wie ein unbekannter Key: sie landet in `missing`, statt still auf die Tafel-Form zurückzufallen |
| `GET /sources/{id}/write/glyphs/{glyph_key}` | Einzel-Read: das Render-Payload EINES Buchstabens; antwortet **404**, wenn noch kein Canonical getraced ist (anders als der Batch, der fehlende Keys in `missing` meldet) |
| `GET /sources/{id}/write/glyphs/{glyph_key}.svg` | Derselbe Buchstabe als **SVG-Bild** (`image/svg+xml`, seit 2026-08-28): die Silhouetten-Ringe des Payloads als `<path fill-rule="evenodd">` auf der Lineatur der Schrift (Grundlinie durchgezogen, Mittellinie gestrichelt, Ober-/Unterlinie gepunktet), Viewbox in Template-Einheiten (Mittellänge = 1) — jeder Buchstabe einer Schrift steht damit auf derselben Lineatur im selben Maßstab. Für Clients, die die SPA nicht ausführen (ein Assistent, der zeigen soll, wie das Sütterlin-e aussieht): dieselbe Geometrie wie das JSON, derselbe Vorbehalt — aber nur Browser-Cache, kein Edge (`BROWSER_ONLY_CACHE`, siehe unten). `api/glyph_svg.py`; in der Router-Reihenfolge VOR dem JSON-Einzel-Read deklariert, weil `{glyph_key}` sonst `e.svg` als Key schluckt. 404 wie das JSON |
| `GET /sources/{id}/write/word?text=…` | Ein ganzes Wort/eine Zeile, serverseitig komponiert |
| `GET /sources/{id}/write/word.svg?text=…` | Dasselbe Wort als **SVG-Bild** (seit 2026-08-28): die Draw-Items der Komposition — Buchstaben-Silhouetten gefüllt (`evenodd`), generierte Übergänge als gestrichene Mittellinie mit ihrer konstanten Breite und runden Kappen, genau wie `WrittenWord` im Browser — auf der Lineatur der Schrift; `bounds`/`guides` aus der Komposition. Gleicher Eingabevertrag wie `/word` (`_normalized_text`: NFC, trim, ≤ 160 Zeichen → 422). Buchstaben ohne Canonical bleiben Lücken; ein Text, aus dem sich NICHTS schreiben lässt, antwortet **404** mit den fehlenden Keys statt eines leeren Bildes. `api/glyph_svg.py::word_svg` |

Alle fünf sind **öffentliche Reads** (kein Admin-Gate). Die drei
JSON-Reads tragen den geteilten Cache-Header (`api/http.py`
`CACHE_CONTROL`; Browser ≈ 5 min, Edge `s-maxage` = 1 Tag —
Template-Geometrie ändert sich nur durch einen Admin-Re-Trace, dann gilt
das dokumentierte Stale-Fenster von bis zu einem Tag am CDN). Die beiden
**SVG-Reads** tragen `BROWSER_ONLY_CACHE` (`private, max-age=300`) —
Browser ja, Edge nein: Cloudflare cacht diesen Host per Regel, und ein
Edge-HIT erreicht die zählende Middleware (`asset_fetch`,
[`frontend-stack.md`](frontend-stack.md) §6) nie; am 2026-08-28 waren
drei von vier Assistenten-Abrufen genau solche HITs. Die SPA fragt die
SVGs nie an, also verliert nichts Menschliches den Edge-Cache. Der Admin
behält den ungecachten `/diagnostic`.

### Ratenbegrenzung — zwei Buckets, eng vor weit

`api/rate_limit.py` hält **zwei In-Process-Token-Buckets je Client**, beide als
Middleware angewandt und deshalb für JEDE Methode wirksam, HEAD eingeschlossen.
Geprüft wird eng zuerst, damit eine abgelehnte Anfrage nicht auch noch ein
Token des weiten Buckets kostet.

| Bucket | Gilt für | Default | Abschalten |
|---|---|---|---|
| **eng** | `GET /sources/{id}/write/word` + `…/word.svg` | 60/min, Burst 20 — **je Komposition von bis zu 160 Zeichen** | `WRITE_RATE_LIMIT_PER_MIN=0` |
| **weit** | **alle übrigen Routen**, GET und HEAD eingeschlossen | 600/min, Burst 120 (je Anfrage) | `PUBLIC_RATE_LIMIT_PER_MIN=0` |

Der **enge** Bucket sitzt vor dem einzigen öffentlichen Read, dessen Kosten der
Aufrufer bestimmt: ein eindeutiger Text ist bauartbedingt ein Cache-MISS, und
ein 155-Zeichen-Text kostete am 2026-09-01 live 0,80 s TTFB und 1.653.798 Bytes.

Ein Token kauft dort **eine Komposition voller Länge**, ein kürzerer Text kostet
anteilig weniger (`composition_cost`, seit 2026-09-04; Untergrenze ein Achtel
Token, damit Ein-Zeichen-Anfragen keine freie Spur werden). Die Zahlen bleiben,
sie lesen sich nur nicht mehr als „60 Anfragen": Was gemessen wurde, skaliert
mit dem TEXT, nicht mit der Anfrage — dieselbe Zeile kostet gleich viel, ob sie
am Stück oder in vier Teilen kommt. Sichtbar gemacht hat das die
Postkarten-Federprobe: 480 Zeichen brechen in bis zu ~57 geschriebene Zeilen um,
jede eine eigene Kompositionsanfrage (jede Zeile ein eigener durchgehender
Federzug, design-system.md §7) — pro Anfrage gezählt sprengte **ein einziger
Seitenaufruf** den Burst. Nach Länge gezählt kostet dieselbe Postkarte **3 bis 7
Token**: 3 auf der kleinen Stufe (Zeilen von ~26 Zeichen), rund 7 auf der
großen, deren ~9-Zeichen-Zeilen je die Untergrenze zahlen statt ihrer Länge.
Gemessen an der laufenden API: 45 kurze Zeilenanfragen gehen durch, wo derselbe
Burst vorher 429 lieferte. Der Missbrauchsfall ist unberührt (eine Anfrage
voller Länge kostet weiter genau ein Token), und die Anzahl der Anfragen
begrenzt weiterhin der weite Bucket.

Der **weite** Bucket (Owner-Entscheid 2026-09-02: „soll nur extreme Nutzung
blocken, damit mir keine riesigen Kosten entstehen können oder jemand alles
lahmlegen kann“) schließt den Rest der Fläche: `/write/glyphs` batcht bis zu 80
Keys, jeder Katalog-Read geht an die DB, und nichts hinderte ein Skript daran,
die API in einer Schleife abzugehen. 600/min mit Burst 120 ist eine
Größenordnung über dem, was das Blättern auf der Website erzeugt — ein
Tafel-Seitenaufruf sind ein paar gebatchte Anfragen, eine Quizrunde eine — und
deutlich unter dem, was eine Ernte braucht. **Vorschlag, keine Messung.**

**Ausgenommen sind beide Buckets** für `/health` (Deploy-Smoke und
Uptime-Probe: den Health-Check zu drosseln, um einen lauten Client zu
bestrafen, macht aus einer Ratenbegrenzung einen Ausfall) und für
`/seo-proxy/…` (die vorgerenderten Crawler-Seiten kommen ALLE über das nginx
der Website herein und teilen sich damit EINEN Schlüssel — ein Bucket würde den
gesamten Crawler-Trichter samt täglichem Bot-Wächter wie einen einzigen
Missbrauchsfall drosseln; billiger als ein Dateiaufruf von 8 KB ohne DB ist
ohnehin keine Route).

Über dem Limit antwortet die Route **429** mit `Retry-After` (die ehrliche
Wartezeit, aufgerundet) und `private, no-store` — eine Ablehnung gilt dem
Aufrufer, nicht der URL, und darf nicht für den nächsten Besucher gecacht
werden. Die Middleware sitzt INNERHALB von CORS, damit ein Browser die 429 auch
als 429 lesen kann statt als undurchsichtigen Netzwerkfehler.

**Am 200 ändert sich nichts.** Der Zähler steht am **Origin**: eine am Edge
beantwortete Anfrage erreicht ihn nie, Cloudflare cacht die öffentlichen Reads
unverändert weiter, und nur Cache-MISSES kosten ein Token. Kein Header, kein
`Vary`, keine Cache-Klasse einer durchgelassenen Antwort wird angefasst.

Der Schlüssel (`api/request_context.py::rate_limit_key`) verbindet ZWEI Header,
weil keiner allein auf beiden erreichbaren Wegen zugleich fälschungssicher und
pro-Client ist: den **rechtesten gültigen** `x-forwarded-for`-Eintrag (der Hop,
der die Verbindung wirklich angenommen hat — nicht fälschbar, hinter Cloudflare
aber eine von vielen geteilte Edge-Adresse) und `cf-connecting-ip` (auf dem
Cloudflare-Weg der echte Besucher, auf der `run.app`-URL vom Aufrufer selbst
geschrieben). Verbunden schließt jeder das Loch des anderen: wer über `run.app`
eine fremde `cf-connecting-ip` fälscht, trägt seine EIGENE Adresse in der ersten
Hälfte des Schlüssels und landet nie im Bucket des Opfers. Der linkeste
XFF-Eintrag wird nie benutzt — er ist client-gesteuert.

Beide Buckets wirken **pro Prozess**: bei `--max-instances=3` liegt die
effektive Decke bis zu dreimal so hoch. Sie messen nicht exakt, sondern
begrenzen, was ein Aufrufer aus EINEM Container ziehen kann. Das ist Absicht —
beide Cloud-Run-Dienste stehen mit `ingress=all` im Netz, eine
Cloudflare-Regel wäre über die `run.app`-URL umgehbar, diese Buckets nicht.

## Pipeline

1. **Shaping** (`core/shaping.py`): Text → geordnete `glyph_keys` —
   Lang-s-Regel + Fugen-Marker `|`, geschlossenes Ligatur-Set,
   Positionszuweisung pro Joins-Run, Ziffern/Satzzeichen als
   `joins: false`-Glyphen. Python-Zwilling des Quiz-Shapings
   `app/src/domain/shaping.ts`, gepinnt durch
   `tests/fixtures/shaping_cases.json`.
   **Ligatur-Zerfall als Rückfall:** Fehlt der Canonical eines Clusters
   aus dem geschlossenen Satz (`ch` · `ck` · `tz` · `ſt` · `St` · `qu` ·
   `ß` — Ausnahme ß, siehe unten; `St` ist das eine Groß-Cluster,
   architektur.md §4), zerfällt der Slot in seine
   Einzelbuchstaben — das Wort schreibt sich
   dann mit einem generierten Übergang weiter, statt eine Lücke mit
   gebrochenen Verbindungsstrichen zu hinterlassen. Die Teilbuchstaben
   behalten ihre Schreibung (`St` zerfällt in großes S + t) und
   erben die Wortposition des Clusters (der erste behält `initial`, der
   letzte `final`, die dazwischen sind medial). `ß` bleibt bewusst
   ATOMAR: sein historischer ſs/ſz-Zerfall ist selbst eine
   Allographen-Frage, und ein naiver Split schriebe mitten im Wort ſſ.
   `core/shaping.py::decompose_ligature_slot` (nur noch Python — der
   TS-Zwilling hat seinen Zerfall mit dem serverseitigen Compose-Umzug
   abgegeben).
2. **Komposition** (`core/compose.py::compose_word`): freigegebene
   Paar-Overrides (`glyph_pairs`, Redesign R3) werden pro Wort in EINER
   Query geladen und ersetzen für genau ihr Nachbarpaar den generierten
   Übergang samt Platzierung (Vorrang links-nach-rechts); ohne Override
   bleibt der Generator-Pfad byte-identisch. Danach Grundlinien-
   Platzierung, generierte Übergänge aus `exit`/`entry`-Tangenten +
   Koppelhöhe, Diakritika-Deferral, Ink-Clearance für nicht-joinende
   Glyphen; optionaler `pen`-Parameter färbt GENERIERTE Striche pro
   Schrift ein. Die **Wortlücke** ist dabei eine Lücke zwischen TINTE:
   das erste Zeichen nach einem Leerzeichen steht am weiter rechts
   liegenden von Anker-Vorschub (`SPACE_ADV`) und Tintenboden
   (`WORD_INK_GAP` hinter der rechtesten Tinte des Vorwortes), sonst
   schriebe eine linkslastige Majuskel (K/C/F/G/Q/O/A/I/X) in das Wort
   davor hinein. DIE einzige Kompositionsquelle — gepinnt durch das
   Golden-Fixture `tests/fixtures/compose_golden.json.gz`.
   **Laufform-Varianten** (jul31): `/write/word` lädt zusätzlich die
   `templates`-Zeilen mit `variant=100` (`LAUFFORM_VARIANT` seit PR #247;
   Median-Laufformen aus den Specimen-Wörtern, geschrieben via
   `PUT /sources/{id}/templates/{key}/laufform`, Tool
   `tools/laufform/harvest.py`) und reicht sie als `laufform_by_key` an
   `compose_word`: Glyphen in einem gebundenen Lauf ≥ 3 rendern die
   Laufform, Solo-Payloads (`/write/glyphs`), Tafel und kurze Drills
   bleiben chart-treu. Ohne Zeilen bleibt alles byte-identisch.
3. **Payload** (`core/pipeline.py::render_payload_for_template`):
   Silhouetten (`outline_paths`, Ringlisten mit `fill-rule: evenodd`),
   `centerlines_template`, `entry`/`exit_pt`, `advance`,
   `template_guides`. Auf dem Gleichzug-Pfad (`width_resolver:
   "constant"`) wendet der Payload-Schritt die **Fluent-Weitung** an
   (`FLUENT_BODY_PITCH`, qualitaetsmetrik.md „Fluent-Weitung"): die
   Chart-Zelle quetscht die Rundkörper e/a/u/o; beim Rendern strecken sie
   auf den an den Wortproben (Abb. 19) gemessenen Pitch der fließenden
   Schrift, `entry`/`exit_pt`/`advance` rücken mit. Die Template-Zeile dafür baut
   überall `core.database.models.template_render_row` — der EINE
   Produktions-Row-Builder inkl. `glyph`-Feld, auf dem die Weitung keyt
   (#289: zwei handgerollte Kopien ohne das Feld hatten sie auf `/write`
   still deaktiviert; Parität Exporter↔Produktion pinnt
   `tests/test_render_row.py`).

Stil-Auflösung + der pro `(style, source)` gepoolte Nib/Pen leben in
`api/rendering.py` (memoisiert, TTL 10 min, invalidiert bei
Trace/Resample/Delete).

Alle Zahlen im Payload sind auf **4 Nachkommastellen** gerundet (Anker,
Halbbreiten, Centerlines, Silhouetten-Ringe — `core/pipeline.py`,
`core/template.py`): die Rundung ist Teil des eingefrorenen
Render-Vertrags (Golden-Fixture, Bench-Referenzen) und wird nicht
angefasst, um irgendwo eine Stelle mehr zu gewinnen.

Wer denselben Render **offline bit-genau reproduzieren** muss, liest den
aufgelösten Render-Kontext direkt: `GET /sources/{id}/render-context`
(**admin-gated**, ungecacht, `api/routers/sources.py`) liefert
`style_id`, `style_ratio`, `slant_deg`, `width_resolver`, den gepoolten
`constant_nib_units` **ungerundet** und den gepoolten `pen`. Kein
öffentlicher Read braucht das — der Nib ist über alle autorisierten
Templates der Quelle gemessene Geometrie (quellen-und-rechte.md §5) und
lässt sich aus den ausgelieferten Zeilen nicht nachrechnen, weil der Pool
auch Varianten-Zeilen umfasst, die kein Endpunkt ausliefert. Einziger
Konsument ist der Fixture-Rebuild ohne DB-Zugang
(`tools/wordbench/fetch_fixtures.py`): dort entschied früher die
4-Stellen-Rückrechnung aus `half_widths_template` über knappe
Ink-Clearance-Entscheidungen und damit über bis zu ~0,02 xh
Platzierungs-Jitter.

## Wire-Format (Auszug)

`/write/glyphs` antwortet `{glyphs: [...], missing: [...]}` — nicht
autorierte Keys landen in `missing`, nie als Fehler. `/write/word`
antwortet `{text, items, bounds, guides, missing}`; fehlende Glyphen
komponieren als Lücke mit gebrochenem Verbindungsstrich (sichtbar,
nicht stillschweigend übersprungen). Die TS-Wire-Typen liegen in
`app/src/lib/api/types.ts` und sind hand-synchron mit
`api/schemas.py`.

## Konsum im Frontend

Alle „as written“-Flächen holen ihre Daten über den EINEN geteilten
Render-Cache `app/src/lib/api/renderCache.ts` (Batching pro
Wort/Tafel über `/write/glyphs`, Wort-Cache FIFO-gekappt, Cold-Start-
Retry). Kein privater Render-Cache außerhalb dieses Moduls.

Der Cache-Schlüssel von `fetchRenderGlyphs` umfasst `variant` **und**
`bust` — erst diese Schlüsselung macht einen Batch über das ganze
Alphabet in der Laufform (Variante 100) und cache-umgehende
Live-Vorschauen über den EINEN geteilten Cache überhaupt möglich.
