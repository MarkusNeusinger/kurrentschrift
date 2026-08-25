# Eigenhand-Erfassung — Betrieb

Die eigene Hand als Trainingsdaten erfassen: Bögen drucken, mit echter
Feder schreiben, einscannen (oder fotografieren), zeilenweise sieben,
Streifen ablegen. Konzept und Begriffe:
[`docs/proposals/eigenhand-erfassung.md`](../../../docs/proposals/eigenhand-erfassung.md).
Alles hier ist **lokal und gitignored** (nur `SOURCE.md` + dieses README
sind committet — Begründung in der `SOURCE.md`).

## Der Kreislauf

```bash
# einmalig: Konsultationskorpora holen und den Übergangsraum bauen
uv run python data/corpora/frequencywords-2018/fetch_frequencywords.py
uv run python -m tools.eigenhand.universe

# einmalig je Hand, VOR der ersten Sitzung: das stehende Setup erklären.
# Danach liest ingest Feder/Tinte/Papier von hier; Fassungen, die davor
# eingelesen werden, tragen diese Angaben nicht.
ADMIN_TOKEN=… uv run python -m tools.eigenhand.setup --hand mn-suetterlin \
    --feder "Brause 361 Steno" --tinte "Platinum Carbon Black" \
    --papier "Clairefontaine Clairalfa 90 g" --geraet scanner
#    auf einem zweiten Rechner nur holen:  --pull
#    nachsehen, ohne Netz:                 --show

# 1. Bogen drucken (Warteschlange: Redo > nie belegt > wenigste Fassungen)
uv run python -m tools.eigenhand.sheet --hand mn-suetterlin --date 2026-08-22
#    Mehrfach-Versuche derselben Streifen:  --repeat 3
#    gezielte Streifen:                     --strips S0037 S0037 S0055
#    ODER im Admin: /admin/eigenhand → „Bögen erzeugen" → PDF öffnen; danach
#    den Bogen einmal herunterholen, damit ingest dagegen registrieren kann:
#    ADMIN_TOKEN=… uv run python -m tools.eigenhand.pull --hand mn-suetterlin --sheet B0007

# 2. schreiben — und JEDE gelungene Zeile gleich rechts abhaken (ein Kästchen).
#    Der Import liest die Marken und belegt die Siebung damit vor.
#    Haken/Kreuz = angenommen, leeres Kästchen = verworfen (am Bildschirm
#    jederzeit überschreibbar — ein vergessener Haken kostet nur den Streifen,
#    der dann wieder in der Druck-Warteschlange steht).
#    Dann einscannen/fotografieren (Passmarken müssen mit drauf sein)

# 3. einlesen (entzerrt, schneidet Zeilen, prüft QC). Feder/Tinte/Papier
#    kommen aus dem stehenden Setup; nur eine ABWEICHUNG dieser Sitzung
#    ausdrücklich mitgeben:  --feder "Brause 511"
uv run python -m tools.eigenhand.ingest --hand mn-suetterlin --sheet B0001 scan.jpg

# 4. Siebung: Seite im Browser öffnen, je Zeile urteilen, Ergebnis laden
uv run python -m tools.eigenhand.page --hand mn-suetterlin --sheet B0001

# 5. Ergebnis einspielen (legt Fassungen an, aktualisiert die Kartei)
uv run python -m tools.eigenhand.apply --hand mn-suetterlin --sheet B0001 siebung-B0001.txt

# 6. NACH JEDER SITZUNG: ins private Archiv sichern (create-only, inkrementell)
uv run python -m tools.eigenhand.snapshot --hand mn-suetterlin --push

# 7. hochschieben, damit /admin/eigenhand den Bestand zeigt (Bögen + Verdikte;
#    idempotent, beliebig oft wiederholbar)
ADMIN_TOKEN=… uv run python -m tools.eigenhand.sync --hand mn-suetterlin
#    zusätzlich die Streifenbilder (opt-in — reservierter Datensatz; damit
#    zeigt die Werkbank den geschriebenen Streifen und jedes einzelne Wort):
ADMIN_TOKEN=… uv run python -m tools.eigenhand.sync --hand mn-suetterlin --mit-streifen

# Stand & nächster Druck
uv run python -m tools.eigenhand.report --hand mn-suetterlin

# „Streifen 37 und 55 waren nicht optimal“ — neu aufnehmen
uv run python -m tools.eigenhand.redo --hand mn-suetterlin S0037 S0055 --reason "nicht optimal"
#    alte angenommene Fassungen zusätzlich zurückziehen:  --retire
```

## Regeln

- **Stiftmarke schlägt Gedächtnis:** das Kästchen am rechten Zeilenrand
  direkt nach dem Schreiben abhaken, wenn die Zeile taugt — Haken oder
  Kreuz heißt angenommen, leer heißt verworfen. Dann steht das Urteil
  fest, solange du noch weißt, was schiefging. Am Bildschirm ist es
  vorbelegt und jederzeit überschreibbar.
- **Schwarze oder braune Tinte, nicht blau:** die Lineatur ist in hellem
  Cyan gedruckt und verschwindet beim Import im Blau-Kanal des Farbscans.
  Schwarz (0,10) und Eisengallus-Braun (0,14) bleiben dort klar Tinte,
  blaue Tinte (0,55) liegt genau auf der Schwelle und würde teilweise
  mitverschwinden. **In Farbe scannen**, nicht in Graustufen — dann greift
  der Kanaltrick (Graustufen geht auch, die Linien bleiben dann als sehr
  helles Grau im Bild).
- **Schneiden nach den Randmarken:** die Striche links und rechts auf Höhe
  jeder Zeile markieren die beiden Querschnitte, die Striche in den Lücken
  zwischen den Zeilen die beiden Längsschnitte. Wer daran schneidet,
  bekommt Streifen mit exakt gleicher Höhe und Breite (Sütterlin
  185 × 29 mm) — dieselben Maße, die der Import digital ausschneidet.
  Zwischen zwei Streifen liegen 5 mm freies Papier: ein Schnitt darf
  wandern. Die Streifen-ID steht oben AUF dem Streifen, das Stift-Kästchen
  bleibt außerhalb.
- **Sieb-Disziplin (mvp-roadmap M2, wörtlich übernommen):** Verworfen wird
  nur nach Schreibqualität (verschrieben, verrutscht) — nie, weil
  Buchstaben eng am Nachbarn sitzen. Enge Verbindung ist Signal, nicht
  Müll. Ausfälle müssen zufällig sein, nicht selektiv.
- **Abgelegt werden nur die relevanten Streifen:** Bilddateien bekommen nur
  angenommene Zeilen; Verwürfe stehen als Urteil + Grund in der Kartei
  (zählbar für den Bias-Audit, ohne Pixel). Der Ganzseiten-Scan wird
  standardmäßig nicht übernommen (`--keep-scan` legt ihn zusätzlich ab).
  Jeder abgelegte Streifen ist für sich zuordenbar: die gedruckte
  Streifen-ID und die Klartext-Wörter stehen mit im Ausschnitt, und die
  `meta.json` daneben trägt Wörter, Geometrie, Sitzung und Prüfsummen.
- **Snapshot nach jeder Sitzung.** Bis zum Snapshot sind die Streifen die
  einzige Kopie. Das Archiv ist dieselbe private Clone wie die
  DB-Snapshots (`KURRENTSCHRIFT_ARCHIVE`), create-only, nie aufräumen.
- **Eine Kampagne, ein Setup:** gleiche Feder, gleiche Tinte, gleiches
  Papier — einmal mit `tools.eigenhand.setup` erklärt, danach von `ingest`
  gelesen. Ein Wechsel mittendrin teilt das Korpus in Kohorten, die man auf
  Strichbreite und Schwärzung nicht mehr vergleichen kann; wenn er sein
  muss, gehört er als Abweichung in den `ingest`-Aufruf, damit er an den
  betroffenen Fassungen steht.
- **Wiederherstellung:** ist die Datenbank weg, bringt Repo + Archiv sie
  zurück — `alembic upgrade head`, dann
  `sync --from <Archiv-Snapshot> --mit-streifen`. Rezept und Drill:
  Proposal §8.1.
- **Scan-Qualität:** ≥300 DPI anstreben (`ingest` warnt unter ~250
  effektiv); Handyfotos gehen dank Passmarken, das Blatt möglichst
  formatfüllend und gleichmäßig beleuchtet aufnehmen. HEIC vorher als
  JPEG exportieren.
- **Kartei nie von Hand editieren** — sie ist die einzige Zustandsquelle;
  Zustände (geplant · unterwegs · belegt) werden abgeleitet, nie gespeichert.
- **Der Wortvorrat wächst in Wellen** (`tools.eigenhand.pool build`),
  bestehende Streifen sind unantastbar (append-never). Kandidaten für
  neue Selten-Join-Wörter liefert `tools.eigenhand.gaps`.

## Ablage-Struktur

    mn-suetterlin/
      kartei.json                       Streifenkartei (Zustandsquelle)
      setup.json                        lokale Kopie des stehenden Setups
                                        (Feder/Tinte/Papier/Gerät; Vorgabe
                                        für ingest, Datensatz liegt auf dem
                                        Server)
      blaetter/B0001/
        bogen.pdf                       Druckdatei
        layout.json                     Geometrie-Vertrag des Importers
        scans/…                         Ganzseiten-Scans (nur mit --keep-scan)
        import/…                        Crops + Payload + Siebung-Seite
                                        (regenerierbar, nicht archiviert)
      fassungen/S0037/F01/              nur ANGENOMMENE Zeilen
        streifen.png                    unveränderter Graustufen-Crop, inkl.
                                        gedruckter Streifen-ID + Wortlabels
                                        (selbst-zuordenbar)
        meta.json                       Wörter, Geometrie, Urteil, Sitzung,
                                        Prüfsummen, Provenienz
    universe/uebergangsraum.json        lokale Gewichtstabelle (nie committet)
