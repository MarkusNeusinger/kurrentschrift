# Werkzeuge — die Dev-Tools unter `tools/`

Einstiegspunkt für die Entwickler-Werkzeuge, die bislang nur in den
Agenten-Guides (`CLAUDE.md`, `.github/copilot-instructions.md`)
dokumentiert waren. Jedes Tool hat eine eigene README im jeweiligen
`tools/<name>/`-Verzeichnis mit allen Optionen; hier steht das Wesentliche.

Alle Labs rendern matplotlib-PNGs nach `temp/` (git-ignoriert; Pfad wird
ausgegeben). matplotlib ist das dev-only `viz`-Extra — Aufruf immer mit
`uv run --extra viz`. `--live` liest die Datenbank **nur lesend** (braucht
`DATABASE_URL`, `.env` wird automatisch geladen); keines der Tools
schreibt je in die DB.

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

## Benches und Generator (Verweise)

- **`tools/glyphbench`** — bewertet jeden autorisierten Buchstaben gegen
  eingefrorene Referenzen, EIN Skript pro Lauf; Metrik + Baseline-Historie
  in [`qualitaetsmetrik.md`](qualitaetsmetrik.md).
- **`tools/wordbench`** — bewertet KOMPONIERTE Wörter/Paare gegen die
  Abb.-19/-20-Vorlagen (gleiche Hand); Metrik + Doku in
  [`qualitaetsmetrik.md`](qualitaetsmetrik.md) §6.
- **`tools/quizgen`** — generiert die Lese-Quiz-Wortbank (~500 Wörter);
  Quellen + Distraktor-Modell in [`quiz-wortbank.md`](quiz-wortbank.md).
