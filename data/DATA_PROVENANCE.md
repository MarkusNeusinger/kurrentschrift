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
| `suetterlin-1922` | [`sources/suetterlin-1922/`](sources/suetterlin-1922/SOURCE.md) | PD-Tafeln (JPG + SVG + PNG): Alphabet-Tafel (Abb. 10), Wortprobe „im Zusammenhang geschrieben" (Abb. 19, mit `words.json`-Wort-Referenzen), Verbindungs-Paare (Abb. 20) und Schülerschrift-Wortprobe mit Breitkantfeder (Abb. 22, andere Hand nach derselben Norm — `words.json`-Set `abb22`) | PD-old-70 (Sütterlin † 1917; Text Fallersleben † 1874; normgetreue Schülerschrift ohne Schöpfungshöhe; DNB-Scan §68 UrhG; PDM 1.0) | Wikimedia Commons + DNB-Digitalisat |
| `koch-1928` | [`sources/koch-1928/`](sources/koch-1928/SOURCE.md) | PD-Tafel (JPG) — Offenbacher, dt. Alphabet | PDM 1.0 / PD-Art (Werk gemeinfrei, Koch † 1934; Scan-Vorbehalt §72 → SOURCE.md) | Wikimedia Commons |
| `suetterlin-leitfaden-1926` | [`sources/suetterlin-leitfaden-1926/`](sources/suetterlin-leitfaden-1926/SOURCE.md) | 22 Seiten (JPG) des Volldigitalisats des Leitfadens, 5. Aufl. 1926 — 21 Schriftproben + Vorwort-Seite als Lizenz-Beleg — Norm-Platten druckstock-identisch zu `suetterlin-1922` + Hände-Galerie (Goethe, Güll, Moltke, Bismarck, Thoma, Behrens u. a., alle † > 70 J.); Fremdhand-Kontext für Hände-Vergleich/Stilanalyse, nie Same-Hand-Bench-Referenz | PD-old-70 (Sütterlin † 1917, unverändert seit 1917; alle Galerie-Schreiber † ≤ 1940; SUB-Scan PDM 1.0, §68 UrhG) | SUB Hamburg (IIIF, URN urn:nbn:de:gbv:18-5-PPN10252453500) |

## Korpora (Commit-Klasse 2 — nur Metadaten committet)

| ID | Pfad | Typ | Lizenz | Quelle |
|---|---|---|---|---|
| `frequencywords-2018` | [`corpora/frequencywords-2018/`](corpora/frequencywords-2018/SOURCE.md) | Konsultations-Frequenzlisten de/en 50k (OpenSubtitles 2018) — Bytes gitignored, per `fetch_frequencywords.py` reproduzierbar (SHA256-gepinnt); Auswertung nur lokal (Übergangsraum der Eigenhand-Erfassung) | Repo MIT; Listen = abgeleitete Datenbanken aus OPUS-OpenSubtitles → Konsultations-Quelle, nie committet | hermitdave/FrequencyWords (OPUS, Lison & Tiedemann 2016) |
| `igerman98` | [`corpora/igerman98/`](corpora/igerman98/SOURCE.md) | Hunspell-Wörterbuch `de_DE_frami` (258 200 Stämme, ≈ 807 000 expandierte Formen) — Bytes gitignored, per `fetch_igerman98.py` reproduzierbar; die expandierten Formen sind **Serverdaten** in `lesart_forms` (Migration 0028), nie Repo-Inhalt, nie im Image, nie im Bundle | **GNU GPL 2 oder 3** — die einzige Quelle des Repos mit echten Pflichten; sie entstehen erst bei WEITERGABE, und die findet nicht statt: `GET /lesarten?text=` gibt je Anfrage eine Handvoll Wörter zurück, nie die Liste (Autor-Entscheid 2026-08-30, [`quellen-und-rechte.md`](../docs/reference/quellen-und-rechte.md) §5) | LibreOffice/dictionaries @ `32b006a2` (Björn Jacke; frami-Erweiterung F. M. Baumann) |

## Eigene Erhebungen (kein fremdes Werk — Commit-Klasse 1)

| ID | Pfad | Typ | Lizenz | Quelle |
|---|---|---|---|---|
| `own-hand` | [`samples/own-hand/`](samples/own-hand/SOURCE.md) | Eigenhand-Erfassung: Streifen-Scans der eigenen Hand (Bögen, Fassungen, Kartei) — Bytes bewusst NICHT committet (reservierter Datensatz; Sicherung im privaten Archiv via `tools/eigenhand/snapshot.py`); committet sind nur `SOURCE.md` + Betriebs-`README.md` | Alle Rechte vorbehalten (Open-Core-Vorbehalt; eigenes Urheberrecht) | eigene Erhebung, Konzept `docs/proposals/eigenhand-erfassung.md` |
| `humanbench` | [`humanbench/`](humanbench/SOURCE.md) | Menschliche Bewertungsdurchgänge über die gefitteten Vorkommen — je Runde der Ergebnistext (`runde-<n>-urteile.txt`), ein schmaler Schlüssel (`runde-<n>-vorkommen.json`: uid → Glyph, Vorlagenwort, `repeat_of` — ohne den wäre eine Ergebniszeile wie `S026:AW#81,76` unlesbar) und der Provenienz-Stempel (`runde-<n>-stempel.md`); enthält keine Geometrie und keine Kennzahlen, voller Schlüssel und Payload bleiben außerhalb des Repos | eigenes Urheberrecht des Projektautors (wie `/data/samples/own-hand`) | eigene Erhebung; beurteilt wurden Ausschnitte aus `sources/suetterlin-1922` |

## Varianten (kein Datenartefakt — Modellier-Scope über einer Quelle)

| Variante | Basisquelle | Status |
|---|---|---|
| `v0-loth-1866` ([README](variants/v0-loth-1866/README.md)) | `loth-1866` | aktiv (MVP-Basis) |
