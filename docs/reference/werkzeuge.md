# Werkzeuge — die Dev-Tools unter `tools/`

> **Status (2026-08-03): lebend.** Index über die Dev-Tools unter `tools/`;
> jedes neue, umbenannte oder entfernte Werkzeug und jede geänderte CLI
> (Flags, Modulpfade, `viz`-Extra, `--live`) gehört hier hinein.

Einstiegspunkt für die Entwickler-Werkzeuge, die bislang nur in den
Agenten-Guides (`CLAUDE.md`, `.github/copilot-instructions.md`)
dokumentiert waren. Jedes Tool hat eine eigene README im jeweiligen
`tools/<name>/`-Verzeichnis mit allen Optionen; hier steht das Wesentliche.

Alle Labs rendern matplotlib-PNGs nach `temp/` (git-ignoriert; Pfad wird
ausgegeben). matplotlib ist das dev-only `viz`-Extra — Aufruf immer mit
`uv run --extra viz`. `--live` liest die Datenbank **nur lesend** (braucht
`DATABASE_URL`, `.env` wird automatisch geladen); Labs, Benches und
Generator schreiben nie in die DB. Einzige schreibende Gattung sind die
beiden **Ernte-Werkzeuge** weiter unten — und auch die schreiben nicht
selbst, sondern über die admin-gegateten Endpunkte, damit deren Validierung
greift.

## Die drei Inspektions-Labs (sehen, nicht nur messen)

**`tools/glyphlab`** — Overlays der Ableitung EINES Buchstabens
(Crop · Skelett · Centerline · Ecken · gefüllte Silhouette), aus einer
Fixture oder live aus der DB. Annotiert jedes Panel mit seiner
Penalty-Kategorie: die Bench-Zahl sagt *wie viel*, das Overlay *warum*.

```bash
uv run --extra viz python -m tools.glyphlab <key> [--live] [--stages] [--style dots]
```

**`tools/wordlab`** — das Wort-Level-Pendant: zeichnet ein KOMPONIERTES
Wort (Platzierung + generierte Übergänge aus `core/shaping.py` +
`core/compose.py`) über seine Wordbench-Vorlage, mit Penalty-Callouts pro
Konnektor. `--sweep` variiert eine Compose-Konstante spaltenweise.

```bash
uv run --extra viz python -m tools.wordlab <id> [--set pairs] [--live] [--sweep core.compose.CONST=v1,v2]
```

**`tools/pairlab`** — seziert EINEN Buchstaben-Übergang gegen seine echten
Vorkommen in den Vorlagen, jeder Buchstabe UNABHÄNGIG neu eingepasst:
trennt Konnektor-Form von Platzierungsfehler und misst, wie weit die echte
Feder Schwanz/Kopf der Glyphen für den Join umformt. Befund + Optionen in
[`../proposals/uebergaenge-befund.md`](../proposals/uebergaenge-befund.md).

```bash
uv run --extra viz python -m tools.pairlab re [longs,a] [--set words|pairs|all]
```

## Die zwei Ernte-Werkzeuge (Vorlage → DB, über die Admin-API)

Beide lesen die eingefrorenen Wordbench-Fixtures, sezieren die echten
Vorkommen und schreiben das Ergebnis als **Entwürfe** durch die
admin-gegateten Endpunkte (`ADMIN_TOKEN` nötig). Ohne `--apply` entsteht nur
ein JSON-Report zum Nachsehen — die Freigabe bleibt Menschensache.

**`tools/laufform/harvest.py`** — die Laufform- und Vorkommens-Ernte
(PR #246, um die Vorkommens-Schicht erweitert in PR #250): M4-fittet jedes
Buchstaben-Vorkommen der Abb.-19-Wörter und schreibt drei Artefakte —
die per-Buchstabe-Mediane als Laufform-Varianten
(`PUT /sources/{id}/templates/{key}/laufform`, `variant=100`), jeden
sauberen Einzelfit als `instances`-Zeile und je Vorlage eine nachgefahrene
Wortspur als `word_instance` (`authored`-Zeilen bleiben unangetastet).
Die Laufform-Zeilen wirken **sofort** auf jedes fließende `/write/word` —
gegen Prod nur mit ausdrücklicher Freigabe.

```bash
uv run python -m tools.laufform.harvest [--style suetterlin] [--min-n 4]
    [--rmse-max 2.2] [--apply --base-url http://localhost:8000 --source-id <id>]
```

**`tools/pairlab/harvest.py`** — die Erstbefüllung der Paar-Schicht
(Redesign R3, PR #220; `--store-occurrences` seit PR #250): leitet aus jeder
sezierten Paar-Vorlage eine `PairGeometry` ab (Offset aus den beiden
starren Einzelfits, Konnektor aus dem echten Verbindungsstrich) und legt sie
als **nicht freigegebene** `glyph_pairs`-Entwürfe mit `provenance:
harvested` + Specimen-Beleg ab; `--approve left:right` gibt nur gemessene
Gewinner frei, `--store-occurrences` schreibt zusätzlich die
`pair_instances`. Freigabe sonst im Paar-Editor unter `/admin/paare`.

```bash
uv run python -m tools.pairlab.harvest [--style suetterlin] [--sets pairs]
    [--ids Bi,Du] [--apply] [--store-occurrences] [--approve B:i,D:u]
```

## Benches und Generator (Verweise)

- **`tools/glyphbench`** — bewertet jeden autorisierten Buchstaben gegen
  eingefrorene Referenzen, EIN Skript pro Lauf; Metrik + Baseline-Historie
  in [`qualitaetsmetrik.md`](qualitaetsmetrik.md).
- **`tools/wordbench`** — bewertet KOMPONIERTE Wörter/Paare gegen die
  Abb.-19/-20-Vorlagen (gleiche Hand); Metrik + Doku in
  [`qualitaetsmetrik.md`](qualitaetsmetrik.md) §6. Drei Module hängen
  **Report-Spalten** an, die nie in den Loss eingehen (eigener try/except,
  hinter dem stabilen Block): `slant.py` (Schräglage Vorlage vs. komponiert,
  90° = senkrecht; R5), `gleichzug.py` (Ein-Fluss-/Ein-Breite-Audit auf der
  komponierten Centerline, ohne Vorlagenbezug; `jul30`) und `pairmeas.py`
  („gemessen vs. komponiert“ — die komponierten Joins gegen die sezierten
  `pair_instances` derselben Vorlagen; `aug02`).
- **`tools/quizgen`** — generiert die Lese-Quiz-Wortbank (~500 Wörter);
  Quellen + Distraktor-Modell in [`quiz-wortbank.md`](quiz-wortbank.md).
