# Write-API — die öffentlichen Render-Endpunkte

**Status:** Umgesetzt (2026-07). Dieses Dokument beschreibt den
ausgelieferten Stand; die Design-Geschichte und verworfenen Alternativen
stehen im Proposal
[`schreibsystem-und-wortbench.md`](../proposals/schreibsystem-und-wortbench.md).

Die Write-API ist der chart-freie Render-Pfad hinter allen öffentlichen
„as written“-Flächen (Federprobe, Schreibtafel, Quiz-Prompts, das
Sütterlin-Specimen auf `/schriftkunde`). Sie liest ausschließlich
`templates`-Zeilen — kein Chart-I/O, keine Bild-Pipeline — und ist
deshalb schnell genug für Cache-Control + gzip.

## Endpunkte

| Endpunkt | Zweck |
|---|---|
| `GET /sources/{id}/write/glyphs?keys=a,n,…` | Batch: pro `glyph_key` (Basis-Keys seit R2, z. B. `a`, `longs`, `ch`) das Render-Payload eines einzelnen Buchstabens; nicht autorisierte Keys landen in `missing`, nie als Fehler |
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
2. **Komposition** (`core/compose.py::compose_word`): Grundlinien-
   Platzierung, generierte Übergänge aus `exit`/`entry`-Tangenten +
   Koppelhöhe, Diakritika-Deferral, Ink-Clearance für nicht-joinende
   Glyphen; optionaler `pen`-Parameter färbt GENERIERTE Striche pro
   Schrift ein. DIE einzige Kompositionsquelle — gepinnt durch das
   Golden-Fixture `tests/fixtures/compose_golden.json.gz`.
3. **Payload** (`core/pipeline.py::render_payload_for_template`):
   Silhouetten (`outline_paths`, Ringlisten mit `fill-rule: evenodd`),
   `centerlines_template`, `entry`/`exit_pt`, `advance`,
   `template_guides`.

Stil-Auflösung + der pro `(style, source)` gepoolte Nib/Pen leben in
`api/rendering.py` (memoisiert, TTL 10 min, invalidiert bei
Trace/Resample/Delete).

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
