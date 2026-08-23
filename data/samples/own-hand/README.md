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

# 1. Bogen drucken (Warteschlange: Redo > nie belegt > wenigste Fassungen)
uv run python -m tools.eigenhand.sheet --hand mn-suetterlin --date 2026-08-22
#    Mehrfach-Versuche derselben Streifen:  --repeat 3
#    gezielte Streifen:                     --strips S0037 S0037 S0055

# 2. schreiben — und JEDE Zeile gleich rechts ankreuzen: „ok“ oder „nein“.
#    Der Import liest die Marken und belegt die Siebung damit vor.
#    Nicht angekreuzt = unentschieden, wird am Bildschirm gefragt.
#    Dann einscannen/fotografieren (Passmarken müssen mit drauf sein)

# 3. einlesen (entzerrt, schneidet Zeilen, prüft QC)
uv run python -m tools.eigenhand.ingest --hand mn-suetterlin --sheet B0001 scan.jpg \
    --feder "Brause 511" --tinte "Eisengallus" --papier "90g" --geraet scanner

# 4. Siebung: Seite im Browser öffnen, je Zeile urteilen, Ergebnis laden
uv run python -m tools.eigenhand.page --hand mn-suetterlin --sheet B0001

# 5. Ergebnis einspielen (legt Fassungen an, aktualisiert die Kartei)
uv run python -m tools.eigenhand.apply --hand mn-suetterlin --sheet B0001 siebung-B0001.txt

# 6. NACH JEDER SITZUNG: ins private Archiv sichern (create-only, inkrementell)
uv run python -m tools.eigenhand.snapshot --hand mn-suetterlin --push

# Stand & nächster Druck
uv run python -m tools.eigenhand.report --hand mn-suetterlin

# „Streifen 37 und 55 waren nicht optimal“ — neu aufnehmen
uv run python -m tools.eigenhand.redo --hand mn-suetterlin S0037 S0055 --reason "nicht optimal"
#    alte angenommene Fassungen zusätzlich zurückziehen:  --retire
```

## Regeln

- **Stiftmarke schlägt Gedächtnis:** die beiden Kästchen am rechten
  Zeilenrand direkt nach dem Schreiben ankreuzen — dann steht das Urteil
  fest, solange du noch weißt, was schiefging. Am Bildschirm ist es
  vorbelegt und jederzeit überschreibbar.
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
- **Eine Sitzung, ein Setup:** gleiche Feder, gleiche Tinte, gleiches
  Papier je Bogen; die Angaben gehören in den `ingest`-Aufruf.
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
