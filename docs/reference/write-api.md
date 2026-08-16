# Write-API — die öffentlichen Render-Endpunkte

> **Status (2026-08-03): lebend.** Beschreibt die ausgelieferten
> `/write/*`-Endpunkte; jede Änderung an `api/routers/write.py` (inkl.
> `compose_word_payload`), `core/shaping.py`, `core/compose.py`, dem
> Render-Payload oder den Cache-Headern muss hier nachgezogen werden.

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
| `GET /sources/{id}/write/word?text=…` | Ein ganzes Wort/eine Zeile, serverseitig komponiert |

Alle drei sind **öffentliche Reads** (kein Admin-Gate) und tragen den
geteilten Cache-Header (`api/http.py`; Browser ≈ 5 min, Edge
`s-maxage` = 1 Tag — Template-Geometrie ändert sich nur durch einen
Admin-Re-Trace, dann gilt das dokumentierte Stale-Fenster von bis zu
einem Tag am CDN). Der Admin behält den ungecachten `/diagnostic`.

## Pipeline

1. **Shaping** (`core/shaping.py`): Text → geordnete `glyph_keys` —
   Lang-s-Regel + Fugen-Marker `|`, geschlossenes Ligatur-Set,
   Positionszuweisung pro Joins-Run, Ziffern/Satzzeichen als
   `joins: false`-Glyphen. Python-Zwilling des Quiz-Shapings
   `app/src/domain/shaping.ts`, gepinnt durch
   `tests/fixtures/shaping_cases.json`.
   **Ligatur-Zerfall als Rückfall:** Fehlt der Canonical eines Clusters
   aus dem geschlossenen Satz (`ch` · `ck` · `tz` · `ſt` · `qu` · `ß`
   — Ausnahme ß, siehe unten), zerfällt der Slot in seine
   Einzelbuchstaben — das Wort schreibt sich
   dann mit einem generierten Übergang weiter, statt eine Lücke mit
   gebrochenen Verbindungsstrichen zu hinterlassen. Die Teilbuchstaben
   erben die Wortposition des Clusters (der erste behält `initial`, der
   letzte `final`, die dazwischen sind medial). `ß` bleibt bewusst
   ATOMAR: sein historischer ſs/ſz-Zerfall ist selbst eine
   Allographen-Frage, und ein naiver Split schriebe mitten im Wort ſſ.
   `core/shaping.py::decompose_ligature_slot`, im TS-Zwilling
   `decomposeLigatureSlot`.
2. **Komposition** (`core/compose.py::compose_word`): freigegebene
   Paar-Overrides (`glyph_pairs`, Redesign R3) werden pro Wort in EINER
   Query geladen und ersetzen für genau ihr Nachbarpaar den generierten
   Übergang samt Platzierung (Vorrang links-nach-rechts); ohne Override
   bleibt der Generator-Pfad byte-identisch. Danach Grundlinien-
   Platzierung, generierte Übergänge aus `exit`/`entry`-Tangenten +
   Koppelhöhe, Diakritika-Deferral, Ink-Clearance für nicht-joinende
   Glyphen; optionaler `pen`-Parameter färbt GENERIERTE Striche pro
   Schrift ein. DIE einzige Kompositionsquelle — gepinnt durch das
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
