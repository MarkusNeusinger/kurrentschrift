# Source: own-hand (Eigenhand-Erfassung)

- Title:     Eigenhandschrift des Projektautors — Streifen-Scans der
             Eigenhand-Erfassung (Bögen, Fassungen, Kartei)
- Author:    Projektautor (Hand-IDs `mn-<stil>`, z. B. `mn-suetterlin`)
- Year:      ab 2026 (fortlaufende Erhebung)
- License:   Alle Rechte vorbehalten — Teil des reservierten Datensatzes
             (Open-Core-Vorbehalt, README „License" +
             quellen-und-rechte.md §5)
- License-Rationale: Eigenes Urheberrecht — nach datenablage.md §1 WÄRE
             dieser Ordner committierbar (Klasse 1). Die Bytes bleiben
             trotzdem draußen (Owner-Entscheidung 2026-08-22, dokumentiert
             in docs/proposals/eigenhand-erfassung.md §8): der Scan-Strom
             ist unbegrenzt („beliebig viel Nachschub", Stufenplan H5) und
             die eigene Hand gehört zum reservierten Datensatz wie die
             DB-Inhalte. Sicherung: privates Archiv-Repository
             (dbsnapshot-Disziplin, `tools/eigenhand/snapshot.py`), in dem
             auch die DB-Snapshots liegen — der gesamte gelernte Datensatz
             an einem Ort.
- Retrieved: erhoben (kein Abruf); Erhebungsdaten je Schreibsitzung stehen
             in `kartei.json` und den `meta.json` der Fassungen

## Abweichung vom SOURCE.md-Schema

Die Pflicht-Blöcke je Datei (Origin/Direct/SHA256/Processing) entfallen
hier, weil die Dateien nicht committet sind. Ihre Entsprechung führt die
Werkzeugkette selbst: `kartei.json` (Bögen, Fassungen, Sitzungen) und je
Fassung `meta.json` mit SHA256 des Streifen-PNGs, Scan-Prüfsumme,
Schreibsitzung (Datum · Feder · Tinte · Papier · Gerät) und Provenienz
(Tool-Commit, Layout-Hash). `tools/eigenhand/snapshot.py` verifiziert die
Prüfsummen vor jedem Archiv-Lauf.

## Was hier liegt (lokal, nie committet)

    <hand>/kartei.json                        Zustandsquelle (Streifenkartei)
    <hand>/blaetter/B*/bogen.pdf + layout.json (+ scans/ nur mit --keep-scan)
    <hand>/fassungen/S*/F*/streifen.png + meta.json   (nur angenommene Zeilen;
                                              Verwürfe stehen pixelfrei in der
                                              Kartei)
    universe/uebergangsraum.json              lokale Gewichtstabelle
                                              (Ableitung aus Konsultations-
                                              korpora, nie committet —
                                              quiz-wortbank.md §4)

Betrieb: `README.md` daneben. Konzept: `docs/proposals/eigenhand-erfassung.md`.
