### Added

- **Die Werkbank lässt sich mit der Tastatur bedienen.** Die vier
  Übersichten sind **Roving-Listen**: die ganze Liste ist EIN Tab-Stopp, die
  Pfeile gehen darin weiter (↑/↓ zwischen Zeilen, ←/→ zwischen den
  Bedienelementen einer Zeile, `Home`/`End` an die Enden), Tab führt wieder
  hinaus. Gemessen auf 1440 × 900, gleicher Stapel, gleiche Daten:
  Buchstaben **77 → 19** Stopps, Übergänge **142 → 44**, Wörter **67 → 21**,
  Streifen-Galerie **22 → 19** (dort nur fünf Kacheln im Prüfstapel; die
  Ersparnis wächst mit der Trefferzahl). Der Fokus hängt am
  Zeilenschlüssel statt am Index, überlebt also Filter und Seitenwechsel und
  landet nie auf `<body>`. Eine umbrechende Kachelfläche bekommt nur ←/→:
  ein Flex-Grid hat keine feste Spaltenzahl, und ein ↓ über sechs Kacheln
  bei 1440 px und drei bei 1024 px wäre schlechter als keins — und sie
  heißt gegenüber einem Screenreader eine benannte Symbolleiste, sonst
  bliebe der im Lesemodus und reichte die Pfeile gar nicht erst weiter.
  **Nicht dabei:**
  die Kartenwand hinter „Galerie" (154 → 156 Stopps — die zwei kommen vom
  Schalter und vom Stepper) und die Nachfahr-Übersicht; beide sind
  Kartenlisten derselben Form und die nächste Anwendung des Hooks.
- **Jedes Detail hat einen Subjekt-Stepper** — ‹ › um den Gegenstand und
  dieselbe Bewegung auf **Alt + Umschalt + ← / →**. Übergänge und Wörter
  hatten bisher gar keinen. Er folgt der Reihenfolge der Übersicht, aus der
  der Leser kam, Filter und Sortierung eingeschlossen, und weil dieselben
  zwei Pfeile damit nach einem Filterklick etwas anderes bedeuten, nennt der
  Kopf die Reihenfolge sichtbar. Nicht `Alt+←/→`: das ist Zurück/Vorwärts
  des Browsers, von dem die Verlinkungs-Doktrin des Admins lebt.
- **Ein Schalter „Kurztasten" am Ende der Scope-Leiste**, Zustand als
  sichtbares Wort, die Kombination als Beschriftung daneben. Voreinstellung
  an, je Browser gemerkt. Aus ist nichts gebunden; die ‹ ›-Knöpfe arbeiten
  weiter, und die Roving-Listen bleiben — sie sind Struktur, keine
  Kurztaste. Die Bindung feuert nie in einem Eingabefeld oder einem offenen
  Dialog: Wizard und Bahn-Editor besitzen ihre Tasten selbst.
- **Die beiden Messgitter kennen die Werkbank** (`--admin`). Ein eigener
  Lauf, nicht die Vorgabeliste: ohne `VITE_ADMIN_TOKEN` ist jede Admin-Route
  der Boot-Fehler, und ein Lauf darüber meldete 11 statt 411 Ziele — der
  Typo-Boden sogar „alle Routen sauber", ohne ein einziges Bedienelement
  gesehen zu haben.

### Fixed

- **Der Statuspunkt im Buchstabenraster trug seinen Zustand nur als Farbe.**
  Grün gegen Orange bei 7 px ist für einen Deuteranopen dasselbe Grau. Jetzt
  ist „canonical" eine gefüllte Scheibe und „nur Bbox" ein hohler Ring
  gleicher Größe — Form trägt, Farbe bestätigt. Der offene Fall aus
  design-system.md §9.4 bleibt als Autorentscheid offen: das Raster liest
  der Autor täglich, und der alte Zwei-Farben-Punkt ist ein Einzeiler weit.
- **Vier Bedienelemente unter dem 44-px-Boden, vom ersten Admin-Lauf
  gefunden:** das „Öffnen" der Galerie-Karte (64 × 32,5, zwanzigmal je
  Seite), „Laufform überschreiben" im Buchstaben-Detail (163 × 32,5),
  „Erneut versuchen" auf dem Boot-Fehlerschirm (125,6 × 36,5, in beiden
  Schalen) und „Seite neu laden" auf dem Routen-Fehlerschirm (112 × 36,5).
  Die letzten beiden sind der gleiche blinde Fleck: ein Routenlauf misst nur
  Zustände, die eine Route von selbst erreicht, und keine Route erreicht
  ihren eigenen Fehlerschirm — beide sind dort das EINZIGE Bedienelement.
- **Die technische Meldung eines Fehlers stand auf 13 px**, unter dem
  Caption-Boden von 14 — sowohl die Zusammenfassung zum Aufklappen als auch
  die Rohzeile darunter.
