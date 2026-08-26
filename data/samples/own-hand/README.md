# Eigenhand-Erfassung — Betrieb

Die eigene Hand als Trainingsdaten erfassen: Bögen drucken, mit echter
Feder schreiben, einscannen (oder fotografieren), zeilenweise sieben,
Streifen ablegen. Konzept und Begriffe:
[`docs/proposals/eigenhand-erfassung.md`](../../../docs/proposals/eigenhand-erfassung.md).
Alles hier ist **lokal und gitignored** (nur `SOURCE.md` + dieses README
sind committet — Begründung in der `SOURCE.md`).

## Der Kreislauf

`ADMIN_TOKEN` und `KURRENTSCHRIFT_ARCHIVE` liest die Werkzeugfamilie selbst
aus `.env` (seit 2026-08-25) — kein `set -a; . .env` mehr davor. Eine im
Terminal gesetzte Variable gewinnt weiterhin.

```bash
# einmalig: Konsultationskorpora holen und den Übergangsraum bauen —
# --push schiebt ihn danach in die geteilte DB (vorher tools.dbsnapshot.fetch),
# damit die Werkbank Quoten und die gewichtete Warteschlange zeigt
uv run python data/corpora/frequencywords-2018/fetch_frequencywords.py
uv run python -m tools.eigenhand.universe --push

# einmalig je Hand, VOR der ersten Sitzung: das stehende Setup erklären.
# Danach liest ingest Feder/Tinte/Papier von hier; Fassungen, die davor
# eingelesen werden, tragen diese Angaben nicht.
uv run python -m tools.eigenhand.setup --hand mn-suetterlin \
    --feder "Kaweco Classic Sport, Stahlfeder M" \
    --tinte "Platinum Carbon Ink Black (Karbonpigment)" \
    --papier "Clairefontaine Clairalfa A4 90 g/m²" --geraet scanner
#    auf einem zweiten Rechner nur holen:  --pull
#    nachsehen, ohne Netz:                 --show
#    Im Admin gesetzt? Dann hier trotzdem einmal --pull: der Browser-PUT
#    schreibt den Server, nicht die lokale setup.json, aus der ingest liest.

# 1. Bogen drucken (Warteschlange: Redo > nie belegt > wenigste Fassungen)
uv run python -m tools.eigenhand.sheet --hand mn-suetterlin --date 2026-08-22
#    Mehrfach-Versuche derselben Streifen:  --repeat 3
#    gezielte Streifen:                     --strips S0037 S0037 S0055
#    ODER im Admin: /admin/eigenhand → „Bögen erzeugen" → PDF öffnen; danach
#    den Bogen einmal herunterholen, damit ingest dagegen registrieren kann:
#    uv run python -m tools.eigenhand.pull --hand mn-suetterlin --sheet B0007
#    Drucken: FARBdrucker (die Lineatur ist Cyan), A4, „Tatsächliche Größe“ —
#    NIE „An Seite anpassen“, siehe „Regeln“.

# 2. schreiben — und JEDE gelungene Zeile gleich rechts abhaken (ein Kästchen).
#    Der Import liest die Haken. Haken/Kreuz = angenommen; ohne Haken zählt
#    die Zeile nicht (sie bleibt offen und steht wieder in der Warteschlange).
#    Normalfall danach: `apply --haken` — die Siebungsseite brauchst du nur,
#    wenn du eine Zeile ausdrücklich verwerfen oder kommentieren willst.
#    Dann einscannen/fotografieren (Passmarken müssen mit drauf sein)

# 3. einlesen (entzerrt, schneidet Zeilen, prüft QC). Feder/Tinte/Papier
#    kommen aus dem stehenden Setup; nur eine ABWEICHUNG dieser Sitzung
#    ausdrücklich mitgeben:  --feder "Brause 511"
uv run python -m tools.eigenhand.ingest --hand mn-suetterlin --sheet B0001 scan.jpg \
    --date 2026-08-25 --keep-scan
#    --date: OHNE ihn erben alle Fassungen das DRUCKdatum des Bogens — falsch,
#            sobald Druck- und Schreibtag auseinanderfallen, und nichts
#            korrigiert es später (Kartei, Archiv und DB tragen es).
#    --keep-scan: legt den Ganzseiten-Scan unter scans/ ab. Ohne ihn ist er
#            NIRGENDS gesichert — das Archiv überspringt import/ grundsätzlich.

# 4. Siebung: Seite im Browser öffnen, je Zeile urteilen, Ergebnis laden.
#    Erst zu Ende sieben, dann erst denselben Bogen wieder einlesen: ingest
#    überschreibt payload.json und alle Zeilen-Crops.
uv run python -m tools.eigenhand.page --hand mn-suetterlin --sheet B0001

# 5. Ergebnis einspielen (legt Fassungen an, aktualisiert die Kartei).
#    Der Browser lädt die Datei in sein Download-Verzeichnis, nicht ins Repo.
uv run python -m tools.eigenhand.apply --hand mn-suetterlin --sheet B0001 ~/Downloads/siebung-B0001.txt

# 6. NACH JEDER SITZUNG: ins private Archiv sichern (create-only, inkrementell)
uv run python -m tools.eigenhand.snapshot --hand mn-suetterlin --push

# 7. hochschieben, damit /admin/eigenhand den Bestand zeigt (Bögen + Verdikte;
#    idempotent, beliebig oft wiederholbar)
uv run python -m tools.eigenhand.sync --hand mn-suetterlin
#    zusätzlich die Streifenbilder (opt-in — reservierter Datensatz; damit
#    zeigt die Werkbank den geschriebenen Streifen und jedes einzelne Wort):
uv run python -m tools.eigenhand.sync --hand mn-suetterlin --mit-streifen

# Stand & nächster Druck
uv run python -m tools.eigenhand.report --hand mn-suetterlin

# „Streifen 37 und 55 waren nicht optimal“ — neu aufnehmen
uv run python -m tools.eigenhand.redo --hand mn-suetterlin S0037 S0055 --reason "nicht optimal"
#    alte angenommene Fassungen zusätzlich zurückziehen:  --retire
```

## Regeln

- **Farbdrucker, 100 %, und einmal nachmessen.** Die Lineatur ist Cyan —
  ein Mono-Laser druckt daraus Grau unbekannter Luminanz, und die Zusage
  „eine gedruckte Linie kann nie als Tinte zählen" gilt dann nicht mehr.
  Und: ein skalierter Druck („An Seite anpassen") wird von der Entzerrung
  STILL weggerechnet — die Passmarken werden ja auf ihre Soll-Millimeter
  abgebildet. Es gibt keine Fehlermeldung, nur ein um denselben Faktor
  verzogenes Verhältnis von Strichbreite zu x-Höhe, für die ganze
  Kampagne. Einziger Prüfstein ist das Lineal auf dem ersten Blatt:
  Passmarken-Zentren **190,0 mm** waagerecht (10,0 → 200,0) und
  **277,0 mm** senkrecht (10,0 → 287,0). Ein gleichmäßig skalierter Druck
  ist das eine, was der Scan selbst NICHT sehen kann — Marken und Abstände
  schrumpfen zusammen, das Verhältnis bleibt.
  Ein BESCHNITTENER Druck dagegen wird gemeldet: der Bogen verlangt 6 mm
  bedruckbaren Rand (`PRINT_SAFE_MM`), und `ingest` warnt, wenn eine
  Passmarke kleiner herauskommt, als ihr gemessener Abstand es zulässt.
- **Ein Bogen lässt sich nicht zurücknehmen.** `sheet` vergibt bei jedem
  Lauf eine neue Bogen-ID und nimmt Streifen aus der Warteschlange; es
  gibt kein Un-Drucken, und die Kartei wird nicht von Hand editiert. Der
  Probedruck für den Skalierungstest ist also ein Bogen, den du auch
  beschreiben solltest.
- **Ein Verwurf ist endgültig.** `--retire` fasst nur ANGENOMMENE
  Fassungen an. Eine irrtümlich verworfene Zeile — ein vergessener Haken,
  ein Fehlklick in der Siebung — lässt sich nicht nachträglich annehmen;
  der Streifen muss neu gedruckt und neu geschrieben werden.
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
  `sync --from <Archiv-Snapshot> --mit-streifen`. Irgendein Schnappschuss
  der Hand genügt: die Geschwister daneben werden mitgelesen, weil
  `snapshot` inkrementell ablegt. Der Lauf bricht mit Namen ab, wenn im
  Archiv etwas fehlt — Erfolg meldet er nur, wenn die Hand wirklich ganz
  zurück ist. Rezept und Drill: Proposal §8.1.
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
