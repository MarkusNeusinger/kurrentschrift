# Kurzglossar — die Begriffe, die im Code stehen

> **Status (2026-09-04): lebend.** Die Kurzfassung von
> [`glossar.md`](glossar.md) für den Einstieg in eine Sitzung: **79
> Begriffe**, je ein bis zwei Sätze, jeder mit dem Sprung in seinen
> Themenblock des vollen Glossars. Nachzieh-Anlass: ein Begriff wandert
> hierher, sobald er die Zwei-von-drei-Schwelle unten erreicht und in
> keine der drei Ausschluss-Klassen fällt — und wieder heraus, sobald er
> unter die Schwelle fällt. Das volle Glossar bleibt die
> Nachschlage-Instanz und behält seinen alphabetischen Schnellindex; hier
> steht **nichts**, was dort nicht ausführlicher stünde.

**Warum es diese Datei gibt.** `glossar.md` trägt über 300 Einträge und
kostet rund 56 000 Token — mehr als die Hälfte der Pflichtlektüre. Wer
eine Sitzung beginnt, braucht aber nicht das Vokabular des ganzen
Projekts, sondern die Wörter, die ihm in der nächsten halben Stunde
begegnen: in einem Modulkommentar, in einer Auftragszeile, in einer
Skill-Anweisung. Genau die stehen hier.

**Wie die Auswahl entstanden.** In zwei Schritten, beide nachvollziehbar.

**Schritt 1 — gezählt.** Für jeden Eintragstitel des vollen Glossars (samt
seiner Zweitnamen und der Identifier in seiner ersten Zeile) wurde mit
Wortgrenzen gezählt, wie oft er in drei Quellen vorkommt: (1) `core/`,
`api/`, `tools/`, `alembic/`, `app/src/` (`.py`/`.ts`/`.tsx`, Identifier
und Kommentare), (2) die Agenten-Dateien `CLAUDE.md`,
`.github/copilot-instructions.md` und `.claude/**`, (3) die
Beschreibungen der letzten 40 gemergten PRs. **92 Einträge** kommen in
mindestens zwei der drei Quellen vor — das ist die Kandidatenliste.

**Schritt 2 — drei benannte Ausschlüsse.** Aus den 92 fallen heraus:

1. **Wortfalle** — Titel, deren Trefferzahl aus gewöhnlicher deutscher
   Prosa stammt statt aus dem Fachgebrauch (`einen`, `Quelle`,
   `Register`, `Bogen`, `Schriftkunde`, `Offenbacher`).
2. **schon abgedeckt** — Titel, deren Inhalt hier unter einem anderen
   Eintrag steht (`tracebench` in der Bench-Familie, `Oberlinie ·
   Mittellinie · …` in **Lineatur**, `Anker` in **Anker · Sample ·
   Schritt**, `glyph_key` mit Backticks geschrieben).
3. **Ein-Arm-Etiketten** — Messnamen, die genau ein §14-Abschnitt
   benutzt (`Plateau-Anker`, `Entdrillung`, `Stack-Sensor`,
   `Karten-Soll-Vollständigkeit`, `Marken-endständige Assembly`,
   `zonale Rückweisung`, `Lineal-Soll-Budget`, `Deckungslücke`,
   `Austritts-Trim`, `Spike-Verhältnis`, `Sprung-Gate`,
   `Nachbarbindung`, `Vorkommensschranke`, `like-for-like Gate`,
   `Apex-Übergabe`, `Säulenabgang`). Sie gehören ins volle Glossar, nicht
   in den Einstieg — auch dann, wenn ihr Identifier in `core/` steht:
   `Austritts-Trim` (`exit_trim`) ist der Präzedenzfall.

Dazu kommen die Begriffe, die `CLAUDE.md` namentlich als
nachschlagenswert ausweist (Duktus-Prior, Schwellzug,
`gen_chamfer`/`doff`/`dconn`, Bézier-Handle-Floor, Cusp-Connector, M1–M4,
AIoU/LDTW). Ergebnis: **77 Einträge**. Wer die Zählung wiederholt, prüft
jeden fehlenden Kandidaten gegen eine dieser drei Klassen.

---

## 1 · Schrift

**Duktus** — wie ein Buchstabe *geschrieben* wird: Strichreihenfolge,
Richtung, Absetzpunkte. Nicht die fertige Form, sondern der Weg dorthin.
Code-Identifier `ductus`. → [§1](glossar.md#1-schrift-und-paläografie)

**Duktus-Prior** — die Kernidee des Projekts: Aus einem Foto ist nicht
ablesbar, welcher Ast einer Kreuzung zu welchem Strich gehört, also gibt
man dieses Wissen vorher vor — als von Hand autorisierten Duktus je
Buchstabe. → [§1](glossar.md#1-schrift-und-paläografie) ·
architektur.md §2

**Allograph** — zwei gleichermaßen korrekte Schreibformen desselben
Buchstabens an verschiedenen Stellen (langes ſ innen, rundes s außen). Im
Repo **getrennte Glyphen** (`longs` vs. `s`), keine Varianten.
→ [§1](glossar.md#1-schrift-und-paläografie)

**Ligatur** — eine auf der Lehrtafel als eigene Einheit gelehrte
Verbindung; der geschlossene Satz ist `ch` · `ck` · `tz` · `ſt` · `St` ·
`qu` · `ß`. Eigene Glyphen mit eigenem Duktus („enumerieren, nicht
generieren“). → [§1](glossar.md#1-schrift-und-paläografie)

**Fuge** — die Naht im zusammengesetzten Wort (Donners·tag), wo trotz
Wortmitte das runde s steht. Manueller Marker `|` im Eingabetext,
`core/shaping.py::FUGE`. → [§1](glossar.md#1-schrift-und-paläografie)

**Lesart** — ein echtes Wort, das ein gelesenes ebenso gut sein könnte:
gleiche Länge, jeder Unterschied ein dokumentierter Verwechsler. Tabelle
`lesart_forms`, `GET /lesarten?text=`.
→ [§1](glossar.md#1-schrift-und-paläografie)

**Lineatur** — das Liniensystem: **Oberlinie · Mittellinie · Grundlinie ·
Unterlinie**, dazwischen Ober-, Mittel- und Unterlänge. Das Zonen-
Verhältnis ist ein Schriftmerkmal (Sütterlin 1:1:1, Offenbacher 2:3:2).
→ [§1](glossar.md#1-schrift-und-paläografie)

**Schräglage** — wie schräg die Schrift steht. **Messkonvention im ganzen
Repo: Winkel des Abstrichs zur Grundlinie, 90° = senkrecht.** Feld
`slant_deg`. → [§1](glossar.md#1-schrift-und-paläografie)

**Schwellzug** — das An- und Abschwellen der Strichbreite bei der
elastischen Spitzfeder (Druck spreizt die Zinken). Charakteristisch für
Kurrent. → [§1](glossar.md#1-schrift-und-paläografie)

**Gleichzug** — das Gegenteil: gleichbleibende Strichstärke mit der
Redisfeder, charakteristisch für Sütterlin. Zwei Schreibgeräte, deshalb
**zwei getrennte Metriken**.
→ [§1](glossar.md#1-schrift-und-paläografie)

**Federwinkel** *(`alpha`)* — Winkel der Bandzugfeder-Schneide zur
Schreiblinie; bei der Offenbacher lehrt Koch konstante 15°, woraus das
Breitengesetz folgt. `core/widths.py::BroadNib`, nie pro Quelle gefittet.
→ [§1](glossar.md#1-schrift-und-paläografie) · federmodelle.md §2

**Anstrich · Auslauf** — der Zustrich am Buchstabenanfang und der
Ausläufer am Ende. Im Wort **nicht gespeichert**, sondern vom Composer
aus dem Slot-Kontext gesetzt. → [§1](glossar.md#1-schrift-und-paläografie)

**Retrace** — die Feder fährt auf derselben Linie zurück (ſ, t, f). Für
die Bildanalyse ein Problemfall: zwei Striche als eine Tintenspur.
→ [§1](glossar.md#1-schrift-und-paläografie)

**Vorschrift** — auf einem Übungsblatt die vorgeschriebene Musterzeile,
die der Lernende darunter nachschreibt. `app/src/lib/uebungstext.ts`.
→ [§1](glossar.md#1-schrift-und-paläografie)

---

## 2 · Datenmodell

**Style** — die Grundvorlage/Schriftfamilie (Kurrent · Sütterlin ·
Offenbacher) mit ihren Voreinstellungen `width_resolver`,
`default_slant_deg`, `default_style_ratio`. Tabelle `styles`.
→ [§2](glossar.md#2-architektur-und-datenmodell)

**Template** — die kanonische Form einer Glyphe: **Anker**,
`half_widths`, `raw_path`, `entry`/`exit`/`advance`. Tabelle `templates`.
→ [§2](glossar.md#2-architektur-und-datenmodell)

**Variante** — eine zweite, von der Norm ebenfalls sanktionierte Form
desselben Buchstabens (die „A = A“ der Lehrtafeln), keine Abweichung.
Reserviert: **Variante 100 = Laufform**.
→ [§2](glossar.md#2-architektur-und-datenmodell)

**`glyph_key`** — der Schlüssel einer Glyphe als bare Basis (`a`,
`longs`, `ch`); seit Redesign R2 ohne Positions-Suffix.
→ [§2](glossar.md#2-architektur-und-datenmodell)

**Tafel · Chart · Chart-Zelle** — die gedruckte Buchstabentafel eines
Lehrbuchs und die Zelle darin, aus der ein Buchstabe geschnitten wird;
„Tafel-Form“ = die daraus autorisierte Grundform (Variante 0).
→ [§2](glossar.md#2-architektur-und-datenmodell)

**Specimen** — eine konkrete Wort- oder Paar-Probe auf einer Vorlage, mit
der gemessen wird (Sütterlin: 63 Wörter Abb. 19, 33 Paare Abb. 20, und
als **andere Hand** die 106 Wörter Abb. 22).
→ [§2](glossar.md#2-architektur-und-datenmodell)

**Instance** *(Vorkommen)* — ein beobachtetes Auftreten einer Glyphe auf
einer Vorlage samt Fit-Ergebnis. Rohdaten der Statistik; wirkt **nie**
direkt aufs Rendering. Tabelle `instances`.
→ [§2](glossar.md#2-architektur-und-datenmodell)

**Aggregat** — die verdichtete Statistik EINER Hand je `(glyph_key,
variant)`: Median-Anker, MAD-Hülle, `n_instances`. Tabelle `aggregates`,
Kern `core/aggregate.py`. → [§2](glossar.md#2-architektur-und-datenmodell)

**Hand** — der Schreiber, dem eine Vorlage zugerechnet wird; jede
Statistik ist hand-lokal. Auf der Duell-Seite heißt **Hand** zusätzlich
die eigene S-Pen-Nachfahrung, also die Referenz.
→ [§2](glossar.md#2-architektur-und-datenmodell) ·
[§4](glossar.md#4-metriken-und-benchmarks)

**Laufform** — die aus echten Wortvorkommen **gemessene** Form eines
Buchstabens (breiter, geneigter als die Tafelform). Liegt als
Template-Variante 100, `LAUFFORM_VARIANT = 100`, nur in fließenden Läufen.
→ [§2](glossar.md#2-architektur-und-datenmodell)

**Slot** — eine Position im komponierten Wort (ein `glyph_key` plus
Render-Kontext). Vorkommen und Übergänge werden über `(specimen_id,
slot)` zugeordnet. → [§2](glossar.md#2-architektur-und-datenmodell)

**Shaping** — Text → geordnete Glyph-Schlüssel: Lang-s-Regel,
Fugen-Marker, Ligatur-Erkennung, Positionszuweisung, Ligatur-Zerfall als
Rückfall. Existiert zweimal: `core/shaping.py` (maßgeblich) und
`app/src/domain/shaping.ts` (nur fürs Quiz), von einem Fixture
synchron gehalten. → [§2](glossar.md#2-architektur-und-datenmodell)

**Komposition** — Slots → fertiges Wort: Buchstaben setzen, Abstände
wählen, Übergänge erzeugen, Diakritika zurückstellen. `core/compose.py`
ist die **einzige** Quelle, gepinnt durch `compose_golden.json.gz`.
→ [§2](glossar.md#2-architektur-und-datenmodell)

**Übergang · Konnektor** — der Verbindungsstrich zwischen zwei
Buchstaben. Doktrin: **„Übergänge sind Konsequenz, keine Daten“** — sie
werden aus `exit`/`entry`-Tangenten erzeugt, nie gesammelt.
→ [§2](glossar.md#2-architektur-und-datenmodell) · architektur.md §4

**Klassenregel** — eine Regel für eine ganze Klasse von Übergängen (alle
d-Schleifen-Exits, alle Deckstrich-Bögen). Leitprinzip: **eine
Klassenregel hebt viele Paare, ein Override repariert eine Stelle.** Die
Buchstabenmengen in `core/compose.py` sind die Quelle.
→ [§2](glossar.md#2-architektur-und-datenmodell)

**Override** — eine für genau ein Buchstabenpaar hinterlegte, wörtlich
übernommene Verbindung (`glyph_pairs`); nur `approved`-Zeilen erreichen
den Composer, und der Regel-Fix geht immer vor.
→ [§2](glossar.md#2-architektur-und-datenmodell)

**Bbox** — die Zuschnitt-Konfiguration einer Chart-Zelle: Rechteck,
Radierer-Striche, gemalte Tinte, Lineatur-Kalibrierung, `patches`,
`locked`. Tabelle `bboxes`, Modul `core/chart.py`.
→ [§2](glossar.md#2-architektur-und-datenmodell)

**Provenance** — woher eine gespeicherte Geometrie stammt: `harvested` ·
`authored` · `traced`. Regel: eine `authored`-Zeile wird von einer neuen
Ernte **nie** überschrieben.
→ [§2](glossar.md#2-architektur-und-datenmodell)

**Open-Core-Moat** — Code ist MIT, die **gelernten Daten** sind es nicht:
Templates, Laufformen und Vorkommens-Statistik sind reserviert und
admin-gegatet. Der Moat ist die Datenbank, nicht die Webseite.
→ [§2](glossar.md#2-architektur-und-datenmodell) ·
quellen-und-rechte.md §5

---

## 3 · Fit und Messung

**Anker · Sample · Schritt** — die drei Punktsorten des Fits. **Anker**
sind die Freiheitsgrade (120 je Buchstabe), **Samples** liegen dazwischen
und sind die EINZIGEN Stellen, an denen die Zielfunktion Tinte abliest
(~180), **Schritt** ist der Ankerabstand. Wer am Ankerort misst,
beziffert eine Kraft, die nicht vorkommt.
→ [§4](glossar.md#4-metriken-und-benchmarks)

**M4-Fit** — die elastische Anpassung eines Templates an echte Tinte
(Warp auf das Skelett, Strichstruktur und Ecken bleiben erhalten).
`core/fit.py::fit_template_to_instance`, Tikhonov-regularisiert, L-BFGS-B.
Nicht die Kennzahl M4. → [§3](glossar.md#3-mess--und-fit-vokabular)

**Kettenfit** — Buchstabe → Verbinder → Buchstabe als EINE durchlaufende
Feder fitten statt als zwei Buchstaben plus zerlegten Strich. Reine
Messschicht, ändert kein Rendering.
→ [§3](glossar.md#3-mess--und-fit-vokabular)

**M1 · M2 · M3 · M4** — die vier Kettenfit-Kennzahlen (Konvergenz · heute
unmessbare Übergänge · Verbinderform · Buchstabenform gegen das Rauschen).
Gleiche Buchstaben wie die MVP-Meilensteine und der M4-Fit, andere
Bedeutung — im Zweifel den Kontext prüfen.
→ [§3](glossar.md#3-mess--und-fit-vokabular)

**Deckung** *(coverage)* — die Gegenrichtung des Fits: nicht nur „liegt
mein Template auf Tinte“, sondern „ist jede Tinte erklärt“. Ohne sie zieht
sich ein Fit auf einen Teilstrich zurück und sitzt dort perfekt.
→ [§3](glossar.md#3-mess--und-fit-vokabular)

**Stub · Kopplungs-Stub** — die kurzen An- und Absatzstriche an einer
isolierten Tafelzelle. Im verbundenen Wort existieren sie **nicht**; wer
über sie hinweg verbindet, baut ein „Shelf“ ins Wortbild.
→ [§3](glossar.md#3-mess--und-fit-vokabular)

**Bézier-Handle-Floor** — die Untergrenze 0,05 xh der Bézier-Griffe im
Verbinder-Generator. Bei fast aufeinandersitzenden Buchstaben überschreibt
sie den Entwurfswert, und die Kubik kehrt um.
→ [§3](glossar.md#3-mess--und-fit-vokabular)

**Cusp-Connector** — das Ergebnis davon: ein Verbinder, der in einer
Spitzkehre zusammenfällt. Als Bild egal, als Startwert für einen
Optimierer fatal. → [§3](glossar.md#3-mess--und-fit-vokabular)

**Tintenfolger** — die Verfeinerungsstufe ÜBER dem Kettenfit: Ordnung und
Kreuzungsauflösung aus dem Prior, Geometrie ganz aus der Tinte. Der
Maßstab ist der nachgefahrene Referenzsatz.
→ [§3](glossar.md#3-mess--und-fit-vokabular) · proposals/tintenfolger.md

---

## 4 · Kennzahlen und Benches

**Score · loss · `bench_loss`** — Score 0–100, `loss = 1 − score/100`,
`bench_loss` der **Mittelwert** (nicht Median) über alle Fixtures, damit
eine einzelne verschlechterte Glyphe die Kopfzahl bewegt. Absturz = 1,0.
→ [§4](glossar.md#4-metriken-und-benchmarks) · qualitaetsmetrik.md §1

**`pair_loss`** — dieselbe Kopfzahl für das getrennte Set der isolierten
Buchstabenpaare. Wörter und Paare werden **nie** gemittelt; der aktuelle
Stand steht nur im Status-Blockquote von `qualitaetsmetrik.md`.
→ [§4](glossar.md#4-metriken-und-benchmarks)

**`gen_chamfer`** — die Auditzahl „gemessen vs. komponiert“: Abstand
zwischen erzeugtem und aus der Vorlage gemessenem Übergang. Grundlage
jeder Entscheidung über eine Klassenregel, deshalb nie von
generator-abstammender Geometrie gespeist.
→ [§4](glossar.md#4-metriken-und-benchmarks)

**`doff`** — *Platzierung*: der horizontale Versatz zwischen komponierter
und gemessener Verbindung, im Körper-Rahmen abgelesen. Nur x.
→ [§4](glossar.md#4-metriken-und-benchmarks)

**`dconn`** — *Form*: mittlerer punktweiser Abstand der beiden
Verbindungs-Mittellinien, start-aligniert und damit translationsfrei — die
Platzierung ist allein Sache von `doff`.
→ [§4](glossar.md#4-metriken-und-benchmarks)

**`dspan`** — dasselbe Maß, aber nur über den GEMEINSAMEN Abschnitt: beide
Kurven vom gemeinsamen Ende auf `min(Bogenlänge)` zurückgeschnitten. Damit
blind gegen eine Regel, die den Verbinder am Kopf verlängert, ohne seine
Form zu ändern — der Artefakt, an dem `dconn` bei Arm J4 scheiterte.
→ [§4](glossar.md#4-metriken-und-benchmarks)

**`meas`** — die Report-Spalte, die `doff` und `dconn` je komponierter
Verbindung im Wordbench-Report ausweist, samt `meas_excluded` (gezählt,
nie stillschweigend). → [§4](glossar.md#4-metriken-und-benchmarks)

**`dtw_xh`** — die Headline-Distanz des tracebench: unconstrained DTW in
xh, normalisiert durch die Länge des optimalen Warping-Pfads, beide Bahnen
arc-length-uniform resampelt. **Nur vorwärts** — die Richtung ist
Duktus-Wahrheit. → [§4](glossar.md#4-metriken-und-benchmarks)

**DTW · LDTW · AIoU** — die externen Vergleichsmaße: DTW als Klassiker,
**LDTW** als längenunabhängige Variante (Divisor ist die Pfadlänge),
**AIoU** als adaptive Flächenüberdeckung. Publizierte Werte sind mit
unseren Wort-Zahlen **nicht** vergleichbar — deshalb der eigene Name
`dtw_xh`. → [§6](glossar.md#6-extern--forschung-und-vergleichsmaße)

**Marke** — die Strichklasse, die der tracebench VOR dem Body-Vergleich
herauslöst und separat zählt (i-Punkt, Umlaut, u-Deckstrich):
nicht-erster Strich über `DIACRITIC_MIN_Y`.
→ [§4](glossar.md#4-metriken-und-benchmarks)

**Frozen-Reference-Regel** — die Torpfosten stehen fest: Maske, Skelett,
EDT, geshapte Slots, Template-Zeilen, gepoolter Nib. Während eines
Optimierungs-Loops sind auch Metrik-Module und Tests eingefroren —
**geändert wird der Composer, nie das Lineal.**
→ [§4](glossar.md#4-metriken-und-benchmarks)

**Same-Hand-Disziplin** — Kopfzahlen entstehen nur gegen Vorlagen
**derselben Hand**; die Abb.-22-Schülerschrift läuft als eigenes Set mit
eigener Zahl. Fremde Hände sind Kontext, nie Maßstab.
→ [§4](glossar.md#4-metriken-und-benchmarks)

**Re-Baseline** — der bewusst entschiedene Neu-Export dieser Referenzen.
**Zahlen über eine Re-Baseline hinweg sind nicht vergleichbar** und werden
im Journal als solche markiert.
→ [§4](glossar.md#4-metriken-und-benchmarks)

**Vorregistrierung** — der Auswerteplan wird geschrieben, **bevor** die
Zahlen da sind. Was nicht im Plan steht, ist eine nachträgliche Idee und
wird datiert als solche gekennzeichnet.
→ [§4](glossar.md#4-metriken-und-benchmarks) ·
menschliche-bewertung.md §4

**Wurzel-Digest** *(`root_digest`)* — SHA-256 über die sortierte Liste
aus (Pfad, Größe, Byte-Hash) aller Dateien einer Fixture-Wurzel: man sieht
einer Kennzahl an, worauf sie gemessen wurde.
→ [§4](glossar.md#4-metriken-und-benchmarks)

**glyphbench · wordbench · tracebench · pairlab · chainbench ·
glyphlab/wordlab** — die Werkzeugfamilie. **Benches messen** (Buchstabe ·
komponiertes Wort · Wortbahn-Kandidat), **Labs zeigen** (matplotlib-PNGs
nach `temp/`, `--extra viz`). Keins schreibt je in die DB.
→ [§4](glossar.md#4-metriken-und-benchmarks) · werkzeuge.md

**Duell-Namen** — die lesbaren Verfahrensnamen der Tracing-Routen:
**Kette** (Kettenfit mit Struktur-Wächter, seit v5 der Default) ·
**Lotse** · **InkSight** · **Nullprobe** (die prior-freie Kontrolle,
technisch Route G). → [§4](glossar.md#4-metriken-und-benchmarks)

**Verfahrensseite** — die Registerseite einer Duell-Route
(`verfahren-kette.md` …): Steckbrief plus Versions-/Arm-Ledger mit Verdikt
und §14-Anker. Register, keine zweite Wahrheit — jede Zahl dort ist ein
datiertes Zitat. → [§4](glossar.md#4-metriken-und-benchmarks) ·
verfahren.md

**Bewertungsdurchgang** — eine Runde, in der ein Mensch gefittete
Buchstaben **blind** beurteilt (`tools/humanbench`), mit
sechsteiliger Fehler-Taxonomie und vorregistriertem Auswerteplan.
→ [§4](glossar.md#4-metriken-und-benchmarks) · menschliche-bewertung.md

**Messjournal** — die Datei [`messjournal.md`](messjournal.md), seit
2026-09-04 die Heimat von §14: 81 datierte Abschnitte, je einer pro
Mess-Runde. Einstieg ist das **Register** im Kopf, nicht die Datei.
→ [§5](glossar.md#5-werkbank-und-prozess)

---

## 5 · Werkbank und Prozess

**Werkbank** — der Admin als EINE Arbeitsfläche: Vorlagen-Auswahl und
darunter drei Ansichten (Buchstaben · Übergänge · Wörter), jede nach dem
Muster Übersicht ⇄ Detail mit dem Subjekt in der URL.
→ [§5](glossar.md#5-werkbank-und-prozess) · optimierungs-werkbank.md

**Auftragskorb** *(`work_items`)* — statt Screenshots eine Tabelle: Der
Autor markiert einen Buchstaben, ein Paar oder ein Wort und legt daraus
einen Auftrag ab. Mehr ist von der Mensch-Seite nicht gefordert.
→ [§5](glossar.md#5-werkbank-und-prozess)

**Auftragskorb-Protokoll** — der Rest ist Protokoll, und die API
**erzwingt** es: die Beanstandung zurückformulieren und sagen, ob sie sich
reproduzieren ließ, BEVOR gearbeitet wird; zum Schließen die diagnostizierte
Stufe plus `resolution`. → [§5](glossar.md#5-werkbank-und-prozess)

**Stufen-Doktrin** — **Manuell hinzufügen nur, wo Ground Truth entsteht,
die das System nicht selbst herleiten kann. Alles Generierte wird
bemängelt.** Tafel-Duktus und Wort-Nachfahren sind Menschenarbeit;
Laufform, Übergangs-Grammatik und Platzierung sind Algorithmus-Territorium.
→ [§5](glossar.md#5-werkbank-und-prozess) · optimierungs-werkbank.md §3

**Triage-Pflicht · Regel-Fix vor Override** — die Prüfreihenfolge:
Tafel-Duktus? → Laufform/Fit? → Klassenregel? → Platzierung? → **erst
zuletzt** ein Override. Ein Override ohne vorherige Regel-Prüfung ist ein
Doktrin-Verstoß. → [§5](glossar.md#5-werkbank-und-prozess)

**Rückgabe an Autor** *(`returned`)* — der ehrliche Ausgang, wenn die
Triage eine Ground-Truth-Lücke ergibt. Die Zeile bleibt im Korb sichtbar:
**sie wartet auf den Autor, nicht auf den Algorithmus.**
→ [§5](glossar.md#5-werkbank-und-prozess)

**Rettungsweg** — die beim VERWERFEN einer Maßnahme benannte Idee, die
sie doch noch ins Ziel bringen könnte: immer ein NEUER Mechanismus, neue
Evidenz oder ein neuer Sensor mit frischer Vorregistrierung — nie derselbe
Knopf mit weicheren Gates. Stehende Liste: tintenfolger.md §7.9.
→ [§5](glossar.md#5-werkbank-und-prozess)

**Verworfen** — Abschnitte mit dieser Überschrift sind **geschlossene**
Entscheidungen samt Begründung; sie werden nie geschwächt oder gelöscht.
Neue Argumente gehen nach `docs/proposals/`.
→ [§5](glossar.md#5-werkbank-und-prozess)

**Status-Vokabular der Docs** — jedes Doc trägt unter der Überschrift
einen Status mit absolutem Datum: bindend · lebend · teil-umgesetzt ·
umgesetzt-historisch · offen · Befund-Journal · statisch. Ab rund 10 000
Token wird der Kopf zum **Stand-Block** (bis zu 40 datierte Zeilen).
→ [§5](glossar.md#5-werkbank-und-prozess) ·
[dokument-status.md](../dokument-status.md)

**Changelog-Fragment** *(`changelog.d/<slug>.md`)* — der
Changelog-Beitrag einer PR als eigene Datei statt als Bullet unter
`[Unreleased]`, damit Geschwister-Merges sich nicht an einer Zeile
treffen. Kein `(#NNN)`-Platzhalter.
→ [§5](glossar.md#5-werkbank-und-prozess)

**Eigenhand-Erfassung** — die Kette, mit der der Autor seine eigene Hand
erfasst: Wortvorrat → Streifenplan → Bogen drucken → schreiben → einlesen
→ **Siebung** → Streifenkartei → Bestandsbericht. `tools/eigenhand/`.
→ [§5](glossar.md#5-werkbank-und-prozess) · eigenhand-erfassung.md

**Siebung** — der Annehmen/Verwerfen-Schritt je Bogenzeile. **Sieb-
Disziplin:** verworfen wird nur nach Schreibqualität, nie wegen
Verbindungsenge — Ausfälle müssen zufällig sein, nicht selektiv.
→ [§5](glossar.md#5-werkbank-und-prozess)

**Beleg (Eigenhand)** — ein Vorkommen eines Übergangsraum-Items in den
angenommenen Fassungen einer Hand; die Zähleinheit des Bestandsberichts.
→ [§5](glossar.md#5-werkbank-und-prozess)

---

## 6 · Öffentliche Seiten

**Federprobe** *(`/federprobe`)* — die Schreibfläche für beliebigen Text,
live in Sütterlin mit den generierten Übergängen. Die öffentliche
Kostprobe der Komposition.
→ [§7](glossar.md#7-öffentliche-seiten--die-produktnamen)

**Tintenboden** — 14 px x-Höhe: die Untergrenze, unter der eine
geschriebene Zeile nicht kleiner gesetzt, sondern umgebrochen wird
(`lib/lineWrap.ts` `MIN_XHEIGHT_PX`). Beim **Umbruch der Federprobe** ist
dann jede Zeile eine eigene Komposition und ein eigener durchgehender
Federzug — „Zug um Zug“ gilt je Zeile.
→ [§7](glossar.md#7-öffentliche-seiten--die-produktnamen)

**Schreibtafel** *(`/tafel`)* — die Alphabet-Seite: die drei Grundtafeln
nebeneinander; die Sütterlin schreibt sich dort Zug um Zug selbst.
→ [§7](glossar.md#7-öffentliche-seiten--die-produktnamen)

**Lese-Quiz** *(`/quiz`)* — eine geschriebene Form, vier Antworten, nach
einem Fehlgriff beide Formen nebeneinander. Erklärt wird nur bei
dokumentierten Verwechslerpaaren — „no explanation is better than an
invented one“. → [§7](glossar.md#7-öffentliche-seiten--die-produktnamen)

**HTR · CER** — Handwritten Text Recognition und Character Error Rate.
Geplanter Lesepfad: Transkribus als Default (CER 5–7 %),
`dh-unibe/trocr-kurrent` als self-hosted Fallback (CER 2,65 %).
→ [§6](glossar.md#6-extern--forschung-und-vergleichsmaße) ·
htr-integration.md
