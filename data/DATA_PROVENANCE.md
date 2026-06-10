# Data Provenance

Index aller Datenartefakte im Repo. Jede Zeile zeigt auf die jeweilige
`SOURCE.md` mit den Pflichtfeldern (Permalink, Lizenz, Attribution,
Abrufdatum). Spezifikation: [`docs/reference/datenablage.md`](../docs/reference/datenablage.md);
Rechte-Policy: [`docs/reference/quellen-und-rechte.md`](../docs/reference/quellen-und-rechte.md).

**Code-Lizenz (MIT) deckt diese Daten nicht.** Jede Quelle trägt ihre
eigene Lizenz; siehe jeweilige `SOURCE.md`.

## Commit-Klassen

1. **Committed (PD/CC0/eigene Hand):** `/data/sources/`,
   `/data/samples/own-hand/`.
2. **Gitignored (Größe + Lizenzmix):** `/data/corpora/` (nur `SOURCE.md`
   und `fetch_corpus.py` werden committet, nie die Daten selbst).
3. **Gemischt:** `/data/derived/from-cc-by/` committet,
   `/data/derived/from-nc-sa/` gitignored (NC-SA kollidiert mit MIT).

Siehe [`docs/reference/datenablage.md`](../docs/reference/datenablage.md) §1.

## Index

| ID | Pfad | Typ | Lizenz | Quelle |
|---|---|---|---|---|
| `loth-1866` | [`sources/loth-1866/`](sources/loth-1866/SOURCE.md) | PD-Tafel (JPG + SVG) | PD-old / Public Domain Mark 1.0 | Wikimedia Commons |
| `petzendorfer-1889` | [`sources/petzendorfer-1889/`](sources/petzendorfer-1889/SOURCE.md) | PD-Tafel (JPG) | PD (anonym §66 UrhG + Kompilator † 1918; SLUB: PDM 1.0) | archive.org (Zweitdigitalisat: SLUB Dresden) |
| `vos-1903` | [`sources/vos-1903/`](sources/vos-1903/SOURCE.md) | PD-Tafel (JPG) | PD (anonyme Tafel §66 UrhG; Autor † 1945; PD-US) | Wikimedia Commons |
| `joynes-1887` | [`sources/joynes-1887/`](sources/joynes-1887/SOURCE.md) | PD-Tafeln (2× JPG) | PD (Autor † 1917; anonyme Stiche 1887; PDM 1.0) | Wikimedia Commons |

## Varianten (kein Datenartefakt — Modellier-Scope über einer Quelle)

| Variante | Basisquelle | Status |
|---|---|---|
| `v0-loth-1866` ([README](variants/v0-loth-1866/README.md)) | `loth-1866` | aktiv (MVP-Basis) |
