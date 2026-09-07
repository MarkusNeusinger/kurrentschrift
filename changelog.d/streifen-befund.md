### Added

- **Der Streifen-Befund: was eine geschriebene Fassung über sich sagt.** Beim
  Ablegen misst `apply` je Fassung sechs Felder an der Tinte selbst — Feder
  (Median-Halbbreite gegen die Tafelfeder UND gegen den eigenen Median der
  Hand), Unstetigkeit (Knick · Wackler · Bogen · Krümmungsverlust, die
  eingefrorene #558-Arithmetik), Kringel (die eingeschlossenen Löcher gegen
  die per-Schleifen-Erwartung der Kringel-Landmarke), Duktus (Körper-Züge
  gegen die Zahl, in die die Schrift das Wort verbindet), Deckung und
  Lesbarkeit — und daraus einen **Vorschlag** (`sauber` · `brauchbar` ·
  `neu schreiben`) mit dem EINEN Grund, der ihn dominiert, in den Worten des
  Autors („Knick im Übergang", „Kringel zu", „Strichfolge weicht ab", „Feder
  zu dünn/dick", „wackelig"). Damit darf hochgeladen werden, was noch nicht
  perfekt ist: die Schleife schreiben → scannen → Befund → Haken → das
  Schwächste neu schreiben macht sichtbar, welche Fassung eines Streifens die
  schwächste ist, statt den Bestand auf perfekte Bögen warten zu lassen.
  **Nichts verwirft automatisch** — der Haken auf dem Blatt bleibt das Urteil,
  „ersetzt durch F0n" heißt nur, dass eine spätere Fassung sauberer ausfiel,
  und aus den Trainingsdaten nimmt eine Fassung weiterhin nur
  `redo --retire`. Gespeichert wird ausschließlich die MESSUNG
  (`eigenhand_fassungen.befund`, Migration `0029`); Vorschlag, Grund, Güte und
  der Rang unter den Fassungen eines Streifens entstehen beim Lesen — dieselbe
  Doktrin wie beim abgeleiteten Streifen-Zustand, weil ein Rang sich in dem
  Moment ändert, in dem eine bessere Fassung ankommt. Sichtbar in
  `report --befund` (mit der Liste „neu schreiben, schwächste zuerst") und in
  `/admin/eigenhand` als Chips je Fassung, wahlweise danach sortiert.
  Vorregistrierte Schwellen aus der physischen Skala, keine an den Streifen
  des Autors angepasst; keine Bench-Kopfzahl liest daraus.

### Changed

- **Die Stetigkeits-Arithmetik und der Skelettgraph ziehen nach `core/`.** Der
  Unstetigkeits-Sensor der Wortbank und die Schreibreihenfolge-Erkennung
  rechneten beide Dinge, die der Streifen-Befund braucht — und das API-Abbild
  liefert `core/` aus, nicht `tools/`. `core/continuity.py` (Knick · Wackler ·
  Pfeilhöhe · Krümmungsverlust mit ihrer eingefrorenen Fensterleiter) und
  `core/skeleton_graph.py` (Knoten und Kanten einer ausgedünnten
  Tintenmaske) sind jetzt die eine Quelle; `tools/wordbench/continuity.py` und
  `tools/routeg/graph.py` lesen von dort, ohne dass sich eine Zahl bewegt hat.
  Ebenso hat die Tafelfeder (0,0968 xh) mit `core/widths.py` einen einzigen
  Ort, an dem Kringel-Katalog und Befund sie finden, und die Tintenschwelle
  des Imports steht dort, wo Tinte gelesen wird. Tests halten jede der vier
  Verbindungen als IDENTITÄT fest, damit aus einem Umzug nie eine Kopie wird.
