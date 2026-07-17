# Architektur-Referenz

Zusammenfassung der bisher getroffenen Entscheidungen und ihrer Begründung.
Sprache: Deutsch (Prosa) / Englisch (Code, Schema, Identifier).

Begleit-Doc zu [`vision.md`](vision.md) (*was* die Endnutzer-Website
unter [kurrentschrift.ink](https://kurrentschrift.ink) sein soll) und zu
[`mvp-roadmap.md`](mvp-roadmap.md) (*wann* welche Meilensteine fallen).

---

## 1. Problemaufteilung

Das Projekt zerfällt in fünf Säulen, die ein gemeinsamer Render-Kern speist.
§1 ist der Index zu allen folgenden Sektionen: jede Vision-Säule wird hier
genau einer (oder zwei) Sektion(en) zugeordnet.

| Säule | Vision-Bezug | Status | Charakter | Architektur-Sektionen |
|---|---|---|---|---|
| **Synthese** (Schreiben + Animation) | Vision §2, §3, §4 | offen | Forschungskern | §2 · §3 · §4 · §5 · §6 · §7 · §8 · §11 |
| **Erkennung** (Lesen + Lese-Lupe) | Vision §5 | gelöst (Integration) | Adapter | §13 · §14 |
| **Analyse** (Stil-Statistik, Hände-Vergleich) | Vision §6 | teil-gelöst | Statistik | §6 · §12 |
| **Inhalt** (Einstieg, Lese-Regeln, Glossar) | Vision §1 | Redaktion | Content | §16 (Frontend) |
| **Datenexport** (Open Data) | Vision §7 | offen | Release-Engineering | §17 |

**Schreiben (Synthese) — der Forschungskern.** Kein integrierbares
Standardprodukt; hier liegt der eigentliche Mehrwert (siehe §7). Die
Architektur-Entscheidung dazu — analysis-by-synthesis mit Duktus-Prior —
steht in §2.

**Lesen (Erkennung) — gelöst, keine Forschung.** Transkribus hat öffentliche
Kurrent-Modelle (CER ≈ 5–7 %); ein eigenes Modell ist mit ca. 50 selbst
transkribierten Seiten trainierbar. Open-Source-Alternativen für volle
Kontrolle: Kraken/eScriptorium, PyLaia, TrOCR-Fine-Tuning. → frühes,
motivierendes Feature der Website (§13). Die *Lese-Lupe* (§14) ist
didaktische Anwendung der eigenen Glyph-Library; sie macht Lesen **nicht zu
einem zweiten Forschungsproblem**.

**Analyse, Inhalt, Datenexport** sind Anwendungs- bzw. Auslieferungs-
Schichten *über* dem Render-Kern.

Produkt- und Zielgruppen-Bild — *was* die Endnutzer-Website damit sein
soll — steht in [`vision.md`](vision.md).

---

## 2. Architekturentscheidung: duktus-modellbasierte Extraktion

Kernidee: **Analysis-by-Synthesis.** Pro Buchstabe ist a priori bekannt,
in welcher Reihenfolge, mit welchen Absetzpunkten und mit welchem Lauf
(= Duktus) er in der normierten Kurrent vor 1900 geschrieben wurde. Aus dem
Foto/Scan wird *nicht* blind eine Polyline aus dem Skelett gezogen — stattdessen
wird ein kanonisches Duktus-Template an Skelett + Breitenprofil **gefittet**.

- Das **Bild** liefert: Geometrie + Tinten-*Breite*.
- Das **Duktus-Modell** liefert: Strichreihenfolge + Auflösung der Kreuzungen.

Damit wird das aus einem Standbild *unterbestimmte* Kreuzungsproblem
(welcher Ast gehört zu welchem Strich, was kam zuerst) durch den Duktus-Prior
*eindeutig*. Persönliche Varianz = Abweichung von der Norm, nicht Beliebigkeit.

**Bewusst NICHT gewählt — und warum:**

- *OpenType-Font mit Kontextalternativen:* scheitert an echten Verbindungen
  und Varianz; sieht nie „getuscht" aus.
- *ML-Synthese (Graves / Cursive Transformer) zuerst:* braucht Online-Daten
  (Stiftbahn über Zeit); historisches Material ist offline (nur Bild). Bleibt
  optionales Spätstadium, nicht der Einstieg.
- *Blindes Skelett-Tracing:* genau hier liegt das Kreuzungsproblem, das der
  Duktus-Prior löst.
- *Bigram-Datenbank aller Buchstabenkombinationen:* kombinatorisch unmöglich
  und unnötig (siehe §4).
- *SVG-Standardbibliotheken für Schreib-Animation* (Vivus.js, GSAP
  DrawSVG-Plugin, stroke-dashoffset auf statischen Pfaden): animieren einen
  vorgefertigten, **fixbreiten** Pfad. Passt nicht zu unserem generativen
  Schwellzug-Modell (variable Strichbreite über Zeit). Für die Animation
  brauchen wir einen eigenen Renderer, der pro Frame Offset-Kurven aus
  Centerline + Width-Profile erzeugt (§11). Eine abgespeckte Variante
  (`stroke-dashoffset` auf der Centerline, konstante Breite) genügt für das
  MVP-Gate 4.

---

## 3. Die Bibliothekseinheit (Schema)

Die natürliche Einheit ist **nicht der Buchstabe**. Eine Einheit ist ein
gefittetes Duktus-Template einer **(Allograph, Formvariante)**-Kombination,
plus deren Abweichung von der Norm. Drei orthogonale Achsen:

1. **Position (Allograph) — als Lehrtafel-Rolle:** initial/medial/final
   bezeichnet, *wo Loth (oder eine vergleichbare Vorlage) diese Form auf der
   Tafel zeigt*. Die orthographische Frage „welche Vorlage gilt für einen
   konkreten Slot im Lauftext" ist eine separate Schicht — sie wird in
   [`orthographie-regeln.md`](../schriftkunde/orthographie-regeln.md)
   beschrieben und vom (zukünftigen) Modul `core/orthography.py` konsumiert.
   Das ist wichtig: Rund-s erscheint auch an Morphemgrenzen innerhalb eines
   Wortes (`Aus-flug`, `Haus-thür`), seine *Tafelrolle* bleibt aber „final".
2. **Formvariante:** mehrere gleichberechtigte, **in der Norm sanktionierte**
   Duktus für denselben Buchstaben an derselben Tafelrolle (auf Lehrtafeln als
   „A = A" notiert: beide gültig, Schreiber-/Lehrtraditions-Wahl). Keine
   Abweichung, kein Fehler — Teil des kanonischen Modells. *Aus dem Kontext
   NICHT bekannt* (siehe §7).
3. **Per-Instanz-Abweichung:** der konkrete Fit (Statistik, §6).

```python
# One library entry = one fitted ductus instance of one (allograph, variant)
{
  "glyph": "s",
  "variant": 0,               # index into the norm's sanctioned form set
  "canonical": "<ref>",       # shared per (glyph,variant); fixed
  "control_points": [...],    # THIS sample's fit (deviation from canonical)
  "width_profile": [...],     # the Schwellzug (from distance transform)
  "entry": {"xy": (x, y), "tangent": deg, "coupling": "baseline"},
  "exit":  {"xy": (x, y), "tangent": deg, "coupling": "midband"},
}
```

Wichtige Festlegungen:

- **Allographe sind getrennte Glyphen.** Medial ſ (langes s im Wortinneren)
  und finales s (Wortende) sind nicht „dasselbe s mit anderem Übergang",
  sondern verschiedene Duktus. Positionsregel wie in arabischer Schrift.
- **entry/exit haben einen Punkt UND eine Tangente** (Richtung) UND eine
  **Kopplungshöhe** (Grundlinie vs. Mittelband). Manche Buchstaben (b, o, v, w)
  koppeln oben an — das ist eine Glyph-Eigenschaft, im Template festgelegt,
  von der Engine nur abgelesen.
- **Wiederholte Glyphen** (z. B. zwei `e` in einem Wort) teilen ein
  `canonical`, haben aber je einen eigenen `control_points`-Fit. Das speist
  die Statistik-Schicht (§6).
- **Formvarianten sind eigene Templates, nicht Auslenkung.** Die zwei F-
  oder c-Formen der Lehrtafel unterscheiden sich *strukturell* (andere
  Topologie/Strichfolge), nicht nur in der Kontrollpunkt-Auslenkung.
  Bibliotheksschlüssel ist daher `(style, glyph, variant)` — der
  Stil (Grundvorlage) ist die äußerste Achse (siehe unten).
- **Die Wort-Position ist Render-Kontext, kein Template-Schlüssel** (Redesign
  R2, [`schreibsystem-redesign.md`](../proposals/schreibsystem-redesign.md)):
  Ein Template pro Glyphe; `core/shaping.py` weist die Position
  (initial/medial/final) pro Slot zu und wählt darüber die Allographen
  (langes ſ = `longs` vs. Schluss-s = `s`) — die frühere
  Positions-Triplikation (`a-initial/-medial/-final`, Vorschlag A
  „Lehrtafel-Rolle") ist zurückgebaut (Migration `0017`).
- **Width-Profile-Resolver pro Stil.** Eine Stil-Eigenschaft entscheidet,
  wie das Breitenprofil interpretiert wird: **Kurrent** = druckabhängiger
  Schwellzug (Spitzfeder, `pressure`), **Sütterlin** = annähernd konstant
  (`constant`, Redisfeder), **Offenbacher** = winkelabhängig (`broad_nib`,
  Breitfeder). Gleiches Duktus-Template, austauschbarer Resolver beim
  Rendern (§5, §11). Liegt als `styles.width_resolver`.

**Datenbankschema (implementiert, Migration `0004`).** Die in §3 angelegte
Trennung *canonical ↔ control_points* ist jetzt schema-seitig verankert,
ebenso die früher (naming-und-setup §1) vertagte Stil-Dimension:

- `styles` — Grundvorlage / Schriftfamilie (Kurrent · Sütterlin · Offenbacher):
  `width_resolver`, `default_slant_deg`, `default_style_ratio`.
- `hands` — ein Schreiber (optional einem Stil zugeordnet); Sources,
  Instances und Aggregates hängen daran.
- `sources` — Herkunft der Bytes, `kind ∈ {chart, manuscript}`, hängt an einem
  Stil und optional an einer Hand; `style_ratio`/`slant_deg` überschreiben den
  Stil-Default pro Tafel.
- `bboxes` — die Admin-Crop-Konfiguration pro `(source, glyph_key)`:
  Crop-Rechteck, Radierer-`mask_strokes`, Lineatur-Kalibrierung
  (`baseline_y`/`midband_y`), `guides`, `n_anchors`, `locked`.
- `templates` — das kanonische `canonical` pro `(style, glyph,
  variant)`; `provenance_source_id` zeigt auf die getuschte Lehrtafel.
- `instances` — die `control_points`-Fits pro Beleg aus Originaltexten
  (§12 Schicht 1, `measurements`); viele pro `(glyph, position, variant)`.
- `aggregates` — Per-Hand-Aggregat (§12 Schicht 2): Cluster-Mittelpunkt +
  Hüllkurve pro `(hand, glyph, position, variant)`. Optional später
  textunabhängige Hand-Features (Hinge/Δn-Hinge nach Bulacu/Schomaker).

`instances`/`aggregates` sind angelegt, aber erst der post-MVP-Import füllt
sie (dort bleibt die Wort-Position eine legitime Beobachtungs-Dimension pro
Beleg). Seit dem Positions-Rückbau (R2) autorisiert der Admin genau EINE Form
pro Glyphe — die positionsabhängigen Verbindungsstriche werden aus
`entry`/`exit`-Tangenten *generiert* (§4), Anstrich/Auslauf setzt der
Composer aus dem Slot-Kontext.

---

## 4. Übergänge sind Konsequenz, keine Daten

Übergänge zwischen Buchstaben sind essenziell — aber **kein eigenes Objekt**
und **kein zu sammelnder Datensatz**. Wenn `exit` von Glyph A und `entry` von
Glyph B als Punkt **plus Tangente** durch die Norm definiert sind, ist der
Verbindungsstrich eine kurze, geometrisch determinierte Kurve zwischen zwei
festgelegten Punkten mit festgelegten Richtungen. Der Duktus *erzeugt* den
Übergang — deshalb keine Bigram-Explosion. Varianz: mehrere echte Fits pro
Glyph + leichtes Jitter auf der Verbindung.

**Ausnahme — geschlossener Satz gelehrter Ligatur-Einheiten.** Die Lehrtafel
zeigt `ch`, `ck`, `tz`, `ſt`, `qu`, `ß` als *eigene gelehrte Einheiten*, nicht
als verbundene Einzelbuchstaben. „Übergang = Konsequenz" gilt für *beliebige*
Buchstabenpaare — aber dieser **bekannte, endliche Satz** muss als eigene
Primär-Glyphen mit eigenem Duktus in die Bibliothek, NICHT als
exit→entry-Verkettung. Enumerieren, nicht generieren.

**Offene Erweiterung** (im Staging, siehe
[`proposals/planaenderungen.md`](../proposals/planaenderungen.md) Vorschlag B):
*opportunistische Bigramme* aus Beispieltext-Imports — Override-Schicht für
Buchstabenpaare, die in derselben Hand als konkret beobachtete Verbindung
vorliegen. Generator-Logik bleibt Default. Wird mit dem Beispieltext-Import
(post-MVP) relevant.

---

## 5. Schwellzug vs. Tinte — zwei getrennte Kanäle

- **Breite = Druck (Schwellzug).** Aus `skeletonize` (Strich-Centerline) +
  `distance_transform_edt` (halbe Strichbreite an jedem Punkt). Misst an der
  Maske, **unabhängig von der Schwärze** → robust gegen Ausbleichen.
- **Schwärze = Tintenmenge.** Separater Graustufenkanal. Trägt die Spur des
  Tintenfasses: frischer Tunk satt, dann ausbleichend bis zum nächsten
  Eintunken; harter Strichabbruch mitten im Wort. Fürs spätere Rendern
  wertvoll (Authentizität), nicht für die Geometrie.
- **Die Falle: Binarisierung.** Zu hart geschwellt → ein verblasster *dicker*
  Abstrich verschwindet, das Skelett zerreißt, er wird fälschlich als feiner
  Haarstrich gelesen. Gegenmaßnahme: adaptiv binarisieren, den
  Intensitätskanal parallel behalten.

**Width-Profile-Resolver pro Schriftfamilie.** Das gleiche Library-Schema
trägt drei Render-Modi:

- **Kurrent (Spitzfeder, 19. Jh.):** `width_profile` wird als
  *druckabhängiger Schwellzug* interpretiert — variable Strichbreite über
  die Bahn, abrupte Wechsel an Ansatz- und Endpunkten, charakteristische
  Haar-/Schattenstrich-Modulation pro Glyph.
- **Sütterlin (1911 ff., Redisfeder):** `width_profile` wird auf einen
  *konstanten* Wert (mittlere Breite pro Source) gesetzt — Sütterlin
  verzichtet bewusst auf Schwellzug. Gleiches Duktus-Template, anderer
  Resolver.
- **Offenbacher (Bandzugfeder, 1927 ff.):** Breite ist reine
  Richtungsfunktion des festen Federwinkels — beim Schreiben wird sie aus
  dem Federmodell *regeneriert*, die Messung kalibriert nur die Feder pro
  Source. Formel, Meißel-Sweep und Verworfenes in
  [`federmodelle.md`](federmodelle.md).

Die Wahl ist eine Stil-Eigenschaft (`styles.width_resolver`, siehe §3),
keine `glyph`-Eigenschaft. Der Renderer (§11) löst sie über den Stil der
Source auf und wählt den passenden Resolver — die Source kann nur Lineatur
(`style_ratio`) und Schräge (`slant_deg`) überschreiben, nicht den Resolver.

**Verfeinerung des gezeichneten Wegs (Snap + Kreuzungsauflösung der Breite).**
Der im Wizard gezeichnete Weg liefert den Duktus-Prior (Strichreihenfolge,
Absetzpunkte, Auflösung der Kreuzungen, §2), *nicht* die präzise Geometrie —
die steckt in der Tinte. `core.pipeline.canonical_from_path` zieht die
resampelten Anker deshalb in zwei Schritten auf die Tinte (beides nicht
destruktiv: `raw_path` bleibt wie gezeichnet, alles ist re-derivierbar;
`snap_to_ink=False` schaltet den Snap ab):

- **Medial-Axis-Snap** (`_snap_anchors_to_ink`): nutzt den regularisierten
  M4-Fit (§7) gegen den *eigenen* Crop des Traces. Auf sauberen Strecken zieht
  das EDT-Feld die Anker auf die Skelett-Centerline und entfernt das
  Handzittern; an einer Kreuzung ist das Feld flach und mehrdeutig, dort lässt
  der Tikhonov-Term den gezeichneten Weg gewinnen — genau da, wo die Zeichnung
  vertrauenswürdiger ist als der Skelett-Blob. Absetzpunkte werden nie
  überbrückt.
- **Kreuzungsauflösung des Breitenkanals** (`_resolve_crossing_widths`): An
  einer Kreuzung misst die `distance_transform_edt` den *Vereinigungs-Blob*
  beider Durchgänge statt des Strichs, zu dem der Anker gehört — das
  Breitenprofil franst vor und nach der Kreuzung aus (und *sieht* erst sauber
  aus, sobald der zweite Strich die Aufdickung optisch verdeckt; der
  gespeicherte Wert bleibt falsch). Wie die Geometrie wird auch die Breite über
  den Prior aufgelöst: Eine Messung gilt als kontaminiert, wenn ein anderer
  Durchgang des Traces nah, *entlang der Bahn weit entfernt* **und transversal**
  ist; kontaminierte Läufe werden aus den sauberen Breiten links und rechts
  interpoliert, pro Durchgang durch die Kreuzung.

**Sonderfall Retrace (gleicher Weg hin und zurück).** Läuft ein Durchgang
(anti)parallel über dieselbe Tinte (Retrace, z. B. schmaler Aufstrich über dem
breiten Abstrich — der Schwellzug der Spitzfeder), ist er *keine* Kreuzung: die
gemessene Breite ist echt und bleibt erhalten (Winkelschwelle
`CROSSING_MIN_ANGLE_DEG`). **Bekannte Grenze:** Der gemessene Wert ist die
Vereinigung beider Durchgänge, also die *Abstrich*-Breite; der Haarstrich
darunter ist im Standbild unsichtbar. Beide Durchgänge bekommen die
Union-Breite — fürs Rendern identisch, fürs Breitenprofil eine Überzeichnung
des Aufstrichs. Die Trennung braucht einen *richtungsabhängigen Breiten-Prior*
(Strichbreite über Laufwinkel + Laufrichtung, aggregiert über mehrere Glyphen)
— Post-MVP-Aufgabe in §12.

---

## 6. Qualitätspipeline (dreistufig, jede Stufe nachvollziehbar)

1. **Robuste Statistik** — kein ML. Pro Glyph viele Fits → Ausreißer
   (Schreibfehler, Klecks, verrutschter Fit) als Cluster-Ausreißer im
   Parameterraum entfernen: Mahalanobis-Distanz oder Median/MAD pro
   Kontrollpunkt. Vorteil: man sieht *warum* verworfen wurde.
2. **Erkennungs-Closed-Loop** — fängt den gefährlichen Fall: Fit sieht
   plausibel aus, ist aber topologisch falsch (falscher Ast an der Kreuzung),
   passiert durch jeden Statistikfilter. Extrahierten Glyph zurückrendern,
   vom Kurrent-Lese-Modell raten lassen. Falscher/„Rausch"-Output =
   falsche Kreuzungsauflösung. Schließt den Kreis zum Lese-Modell aus §1.
   *Grenze:* sagt *dass* falsch, nicht *wie korrigieren* — Filter/Signal,
   kein Reparaturwerkzeug.
3. **Handkuratierung** — der kleine Rest echter Mehrdeutigkeiten.

---

## 7. Offener Forschungskern / das Risiko

Der Mehrwert liegt **präzise in der Kombination** (Duktus-Prior + Skelett/
Distanztransformation + Allograph-Modell + getrennte Kanäle, für normierte
Kurrent vor 1900). Einzeln ist nichts davon neu; die Verbindung mit dieser
Domäne existiert nicht als fertiges Werkzeug.

**Das eine ungelöste Risiko (empirisch, nicht vorab beweisbar):** wie *eng*
das Duktus-Template gefasst wird.

- zu starr → fittet echte historische Hände nicht (jeder Schreiber bricht
  die Norm),
- zu locker → Kreuzungsauflösung wird wieder mehrdeutig — genau das Problem
  zurück, das der Prior lösen sollte.

Dieser Spannungsbogen ist *der* Forschungskern. Muss am MVP empirisch
gefunden werden (Validierungs-Gate 1, §8).

**Zweite Ausprägung desselben Risikos — Varianten-Modellselektion.**
Die Position kennt der Extraktor aus dem Kontext; die **Formvariante nicht**.
Bei einer geschriebenen Instanz muss er erst bestimmen, *welche* sanktionierte
Variante der Schreiber benutzte → alle Varianten-Templates probefitten, beste
wählen (Modellselektion). Zwei geometrisch nahe Varianten holen eine
kontrollierte Version der Kreuzungs-Mehrdeutigkeit zurück. Auffangnetz:
Erkennungs-Closed-Loop (§6).

**Auflösung über Konsistenz-Prior (wichtig):** Ein echter Schreiber ist
*intern konsistent* — er hat *eine* Variante pro Buchstabe gelernt und nutzt
sie durchgängig. Variante ist also **keine Per-Instanz-Zufallsgröße, sondern
eine pro Hand/Stil feste Wahl.** Die Modellselektion entscheidet daher nicht
pro Instanz isoliert, sondern pro Quelle/Hand gemeinsam (Mehrheit über alle
Instanzen eines Glyphs). Das macht das Problem deutlich gutmütiger und ist
zugleich der Hebel für Multi-Stil (§10, §12).

---

## 8. Der MVP (kleinster lauffähiger Renderkern)

Nicht Bibliothek/Engine/Website zuerst, sondern der kleinste lauffähige
Render-Kern: ein **6-Buchstaben-lowercase-Alphabet** plus der ſ/s-Allograph-
Split, mit dem ein kleines Wortset (§9) aus gefitteten Duktus-Templates und
norm-erzeugten Übergängen tatsächlich rekonstruiert wird — und ein darüber
hinaus *neues* Wort aus aggregierten Per-Hand-Stats. Spike-Essenz (billige
Risiko-Falsifikation aus §7) bleibt erhalten — als vier harte Validierungs-
Gates *innerhalb* des MVP.

**MVP-Alphabet:** `a · d · e · l · n · ſ · s` (ſ und s als getrennte Allographe
nach §3). Exakt das Letter-Set, das die §9-Pflicht-Anker `lesen` und `das`
brauchen — unter sechs geht nicht, ohne einen §9-Anker zu opfern. Keine
Ligaturen, keine Großbuchstaben — beide bilden eigene Allograph-Klassen und
kommen mit dem Rest-Alphabet danach.

**Datenstrategie:** Per-Instanz-Statistik fällt aus **Wort-Wiederholungen**,
nicht aus isolierten Glyph-Drills. Aus 5× `lesen` fallen automatisch 10
medial-e-Instanzen + 5 medial-ſ + 5 final-n heraus, jede mit echtem Wort-
kontext (= speist auch den Übergangstest).

**Validierungs-Gates (alle vier erfüllt → Kernel validiert; sonst Negativergebnis):**

1. **Stabilität:** Die drei §9-Kernglyphen (medial ſ, finales s, medial e)
   zeigen über je ≥10 Fits stabile Kontrollpunkt-Cluster.
2. **Allograph-Trennung (§7):** Cross-Fit zwischen medial ſ und finalem s
   trennt sauber pro Hand.
3. **Wort-Rendering:** Die Mehrheit der sieben MVP-Wörter (§9) wird aus den
   gefitteten Templates + norm-erzeugten Übergängen erkennbar wie die eigene
   Vorlage rekonstruiert — **und zusätzlich mindestens ein neues Wort** (etwa
   `denen`), das nicht in der Schreib-Vorlage stand, aus den per-Glyph-
   aggregierten Stats (Cluster-Mittelpunkt aus §6 Stufe 1) in derselben Hand.
   Damit ist *Scan → Stats → Generierung beliebiger Wörter in der Hand*
   demonstriert, nicht nur das Rekonstruieren der Eingabe.
4. **Animation (abgespeckt):** Eines der MVP-Glyphen spielt mit korrekter
   Schreibreihenfolge ab — `stroke-dashoffset` auf der Centerline, konstante
   Breite. Stroke-by-stroke-Sequenz, kein Schwellzug-Aufbau. Die volle
   Schwellzug-Animation (§11) kommt post-MVP zusammen mit dem Canvas-2D-
   Stroker. Gate 4 zeigt, dass das Schema die Render-Daten für Animation
   *bereits* liefert — der ganze Anker-/Outline-Apparat liegt im
   `/diagnostic`-Endpoint.

Tragen die Gates — Projektkern validiert, Rest ist Ingenieurarbeit. Wenn
nicht: in Tagen statt Monaten geklärt (wertvolles Negativergebnis). Aufwand:
ein bis zwei Wochenenden, kein Quartal.

> Operative Zerlegung in Schritt 0 + M0–M7 (M7 = abgespeckte Animation,
> Gate 4) siehe [`mvp-roadmap.md`](mvp-roadmap.md).

---

## 9. Testwörter

**Pflicht-Anker (§8-Validierung): `lesen` + `das`.**

`lesen` (thematisch passend — das Projekt lehrt Lesen):

| Pos | Glyph | position | Besonderheit / Testet |
|---|---|---|---|
| 1 | l | initial | Oberlängen-Schleife (Ascender), Abstrich = dicker Schwellzug |
| 2 | e | medial | Kurrent-e: kleine Schleife → **Kreuzungsfall** (Duktus-Prior) |
| 3 | ſ | **medial** | langes s — **Allograph**, eigener Duktus |
| 4 | e | medial | **2. Instanz** desselben `canonical`, eigener Fit (Statistik) |
| 5 | n | final | berühmte u/n-Verwechslung; Endposition |

`lesen` testet in einem Wort: Allograph (medial ſ), wiederholtes Glyph mit
zwei Fits, zwei Kreuzungsfälle (e), Ascender, und alle Übergänge als
norm-erzeugte Kurven.

`das` liefert das **finale s-Allograph**, das `lesen` nicht enthält — d
(Ascender), a, s in position `final`.

→ `lesen` + `das` = das minimale Allograph-Testpaar; tragen die §8-Validierungs-Gates 1+2.

### Coverage-Wörter (MVP-Wortset)

Zusätzlich zu den Pflicht-Ankern fünf weitere kurze lowercase-Wörter, die das
6-Buchstaben-Kern-Alphabet (§8) in allen vorkommenden Positionen exercieren:

| Wort | Schreibweise (Kurrent) | Glyph-Beitrag |
|---|---|---|
| `lesen` | l-e-ſ-e-n | l-init, e-med ×2, ſ-med, n-final |
| `das` | d-a-s | d-init, a-med, s-final |
| `den` | d-e-n | d-init, e-med, n-final |
| `lese` | l-e-ſ-e | l-init, e-med, ſ-med, **e-final** |
| `lasen` | l-a-ſ-e-n | l-init, a-med, ſ-med, e-med, n-final |
| `als` | a-l-s | **a-init**, **l-med**, s-final |
| `dann` | d-a-n-n | d-init, a-med, **n-med**, n-final |

**Position-Abdeckung über das Set:**

- **a:** initial (als), medial (das/lasen/dann)
- **d:** initial (das/den/dann)
- **e:** medial (mehrfach), **final (lese)**
- **l:** initial (lesen/lese/lasen), medial (als)
- **n:** **medial (dann)**, final (lesen/den/lasen/dann)
- **ſ:** medial (lesen/lese/lasen)
- **s:** final (das/als)

**Generalisierungs-Wort (§8 Gate 3, *nicht* in der Schreib-Vorlage):**

`denen` (d-init, e-med, n-med, e-med, n-final) — alle Positionen vom MVP
abgedeckt, aber nicht im Schreib-Set. Wird aus per-Glyph-aggregierten Stats
in derselben Hand gerendert; demonstriert *beliebige Wörter in der Hand*
statt nur Rekonstruktion der Eingabe.

**Bewusste Lücken im MVP** (kommen mit dem Rest-Alphabet):

- **ſ-initial:** wäre `ſie`/`ſehen`, braucht `i`/`h`.
- **d-final / d-medial / a-final / l-final** — kein lowercase-Wort aus dem
  Mini-Set deckt sie. Keine Show-Stopper, im MVP akzeptiert.

---

## 10. Reihenfolge / Post-MVP-Roadmap

1. **MVP** (§8): 6-Buchstaben-Alphabet, sieben Wörter + ein generalisierendes
   Wort, vier Validierungs-Gates (inkl. abgespeckter Animation). Vor allem
   anderen. Operative Zerlegung in [`mvp-roadmap.md`](mvp-roadmap.md).

Sobald der MVP validiert ist, folgt die Endnutzer-Website in fünf Phasen,
verzahnt mit Frontend-Infrastruktur (§16) als Querschnitt:

| Phase | Inhalt | Architektur | Vision-Bezug |
|---|---|---|---|
| **P1 — Lese-Hilfe** | HTR-Integration über Transkribus-API mit Free-Tier; Lese-Lupe (Wort-Granularität) als didaktische Anwendung. | §13 · §14 | Vision §5 |
| **P2 — Lineatur & Print** | Inhaltsbewusste Übungsblätter mit konfigurierbarer Lineatur; WeasyPrint im Backend; SVG-Glyph-Embedding. | §15 | Vision §2 |
| **P3 — Stil-Analyse** | Per-Hand-Aggregation der Per-Instanz-Stats (M5(C) ausbauen); optional Hinge-/Δn-Hinge-Features. „Optimieren"-Pfad der Vision §6. | §12 | Vision §6 |
| **P4 — Hände vergleichen** | Side-by-Side mehrerer trainierter Hände, Heatmaps für Schräglage/Schwellzug/Glyph-Frequenz; Animation derselben Glyphe in mehreren Händen (Anwendung von §11 + §12). | §11 · §12 | Vision §6 (Hände-Vergleich) |
| **P5 — Open-Data-Export** | Zenodo + GitHub-Release-Integration, CC-BY 4.0; JSON-Schema des Library-Eintrags primär, TEI-XML optional; HTR-United-Eintrag. | §17 | Vision §7 |

**Querschnitt:** Frontend-Infrastruktur (§16) wird parallel zu P1 aufgebaut.
Voller Animation-Render (§11) — Canvas-2D-Stroker mit Schwellzug — kommt
ebenfalls parallel zu P1–P2, sobald der MVP-`stroke-dashoffset`-Schritt steht
und der erste reale User-Bedarf da ist.

**Konsequenz für Multi-Stil (vormals teures Spätstadium):** Ein „Stil"/eine
„Hand" ist weitgehend ein **Varianten-Auswahlvektor** (welche Formvariante pro
Glyph) **+ Abweichungs-Hüllkurve** über demselben geteilten Kanon — kein
eigenes ML-Modell pro Stil. Damit wird das ursprüngliche Phase-4-Problem
(mehrere historische Stile) erheblich billiger. Der MVP (§8 Gate 3,
generalisierendes Wort `denen`) zeigt diese Mechanik bereits in Miniatur
für *eine* Hand: aggregierte Per-Glyph-Stats = personal canonical = jede neue
Wort-Komposition in der gleichen Hand.

---

## 11. Animation-Render-Pfad

Vision §3 verlangt animierte Buchstaben mit Schreibreihenfolge,
Ansatzpunkten und **Schwellzug-Aufbau** live. Direkter Effekt des Duktus-
Priors (§2): die Synthese liefert nicht nur das fertige Bild, sondern auch
*wie es entsteht*.

**MVP-Stand (Gate 4 in §8, implementiert als `WrittenGlyph`):** Die gefüllte
Schwellzug-Silhouette (`outline_polygons` aus der Diagnose-Pipeline) wird per
**Masken-Sweep** enthüllt — ein breiter Maskenpfad läuft via animiertem
`stroke-dashoffset` entlang der per-Stroke-`centerlines_template`, sodass die
Tinte in echter Schreibreihenfolge erscheint und an Absetzpunkten wirklich
abhebt. Sequenziert über CSS-Keyframes (Emotion), nicht WAAPI. Genügt für
„Buchstabe entsteht in richtiger Reihenfolge" mitsamt statischer
Schwellzug-Form; der *zeitvariable* Schwellzug-Aufbau bleibt dem vollen
Renderer vorbehalten.

**Post-MVP — voller Renderer:**

- **Pro Frame:** Centerline bis `t` abtasten, Width-Profile (`half_widths`)
  auswerten, zwei Offset-Kurven (links/rechts der Centerline) berechnen, als
  Canvas-2D-Polygon oder gefülltes SVG-`path` rendern.
- **Width-Profile-Resolver pro Stil** (§5): Kurrent = voller Schwellzug,
  Sütterlin = konstant.
- **Choreographie:** WAAPI-Timeline; SMIL wird abgeraten (Chromium-Deprecation,
  MDN-Empfehlung). Pause/Geschwindigkeit/Wiederholung als
  AnimationController-API.
- **Library-Optionen:** Eigener Canvas-2D-Stroker (klein, volle Kontrolle,
  ~60 fps); **CanvasKit (Skia-WASM)** als Premium-Engine mit
  `SkPaint::getFillPath()` für Profi-Qualität (~2–6 MB WASM-Payload, daher
  hinter Feature-Flag).
- **Ligaturen** (`ch`, `ck`, `ſt`, `tz`, `qu`, `ß`) als eigene Animationen mit
  eigenem Duktus (§4).

**UX-Vorlage (nicht Engine):** AnimCJK / Hanzi Writer — Quiz-Architektur,
Stroke-Matching-Score, Callback-API (`onCorrectStroke`, `onMistake`). Wir
übernehmen das UX-Modell, nicht ihre Render-Engine (die strickt fixbreite
Pfade).

> Algorithmus-Details, Schwellzug-Sampling und WAAPI-Choreographie:
> [`reference/animation-rendering.md`](../reference/animation-rendering.md).

---

## 12. Stil-Analyse-Pipeline

Vision §6 verlangt: Statistik über die eigene Hand zurückbekommen —
Glyphen-Verteilung, Übergangswinkel, Schräglagen-Verteilung, Schwellzug-
Profile. Derselbe §6 deckt Hände nebeneinander vergleichen mit Heatmaps ab.

**Drei Schichten:**

1. **Per-Instanz-Stats** — *liegt bereits vor.* `templates.measurements`
   (per Text-Vorkommen später `instances.measurements`) hält
   `slant_deg`, `mean_half_width_px`, `path_length_px`, `aspect_ratio` für
   jede gefittete Instanz. Erweiterungen pro neuer Größe folgen demselben
   JSONB-Pattern.
2. **Per-Hand-Aggregation** — *teilweise vorhanden.* Cluster-Mittelpunkt +
   Hüllkurve pro `(hand, glyph, position, variant)`. M5(C) der Roadmap
   liefert die erste Implementierung; voller Ausbau zur „personal
   canonical"-Schicht ist Phase-3-Aufgabe. Speicherung: Tabelle `aggregates`
   (siehe §3), gefüllt durch den Post-MVP-Aggregationsjob.
3. **Textunabhängige Writer-ID (optional, post-Phase-3):** **Hinge-** und
   **Δn-Hinge-Features** nach Bulacu/Schomaker — Joint-Distributionen
   benachbarter Konturwinkel, Goldstandard für textunabhängige Writer-
   Identification. Speicherung als Source-Level-Vector. Optional zusätzlich
   EfficientNet/ResNet-Embeddings (Triplet-Loss) für Hand-Ähnlichkeits-
   Suche — ML, nur wenn Bedarf da ist.

**Richtungsabhängiger Breiten-Prior (Folgearbeit aus §5).** Aus Schicht 1+2
lässt sich ohne Schema-Änderung eine Verteilung *Strichbreite über Laufwinkel
+ Laufrichtung* sammeln (die Anker liegen in Schreibreihenfolge mit Halbbreiten
vor, Tangente und Richtung sind daraus ableitbar). Zwei Anwendungen: (a) den im
Standbild unsichtbaren Aufstrich eines Retrace mit der Haarstrich-Breite aus der
Verteilung belegen statt mit der gemessenen Union-Breite (löst die in §5
benannte Grenze); (b) als Plausibilitätscheck für die interpolierten
Kreuzungs-Breiten und zum Flaggen von Profil-Ausreißern. Der Prior ist eine
*Stil*-Eigenschaft — für Kurrent (Spitzfeder, druckabhängig) wertvoll, für
Sütterlin (konstante Breite per Resolver) per Definition unnötig. Braucht eine
belastbare Datenbasis (mehrere autorisierte Glyphen mit Weg), daher Post-MVP.

**Heatmap-Output:**

- **Observable Plot** als Default für Standard-Verteilungen
  (Histogramme, Box-Plots, Violins).
- **D3.js** für maßgeschneiderte 2D-Heatmaps (Hinge-Joint-Distributions als
  2D-Histogramm) und Side-by-Side-Vergleiche „Hand A vs. Hand B".

**Anwendungs-Pfade aus Vision §6:**

- **„Optimieren":** Per-Instanz-Abweichung von der Per-Hand-Aggregation
  visualisieren („wo bist du am inkonsistensten?", „wo weichst du am
  stärksten von der Norm ab?"). Konkretes statt allgemeines Feedback.
- **„Neuer Stil als Basis":** Aus genug eigenen Proben einen Hand-Stil
  extrahieren → Personal Canonical (Schicht 2) → damit weitere Texte
  synthetisieren. „In meiner Hand, aber jeden Text."

**Konzeptionelle Vorlage:** **DigiPal / Archetype** (King's Digital Lab) —
allograph-basiertes Datenmodell für Paläografie, exakt unser
`(instance → allograph → abstract letter)`-Konzept. Nicht als Code-
Dependency übernehmen (Wartungslage unklar), aber als Referenz.

> Algorithmus-Details, Hinge-Feature-Definitionen und Heatmap-Layouts:
> [`reference/styleanalyse.md`](../reference/styleanalyse.md).

---

## 13. Recognition-Stack für Volltext (HTR-Integration)

Vision §5: Lese-Hilfe als motivierender Sofort-Nutzen für die Genealogie-
Zielgruppe. **Kein Eigenbau** — Integration vorhandener Modelle (siehe §1
„Lesen ist gelöst").

**Default-Pfad: Transkribus Text Recognition API.**

- REST mit `POST /processes` + `GET /processes/{id}`, OpenID-Connect-Bearer.
- Modellwahl per `modelId`: `German Kurrent 17th–20th` (CER ≈ 5,4 %),
  `German_Kurrent_XIX_pylaia` (CER ≈ 6,9 %), Supermodel `German Genius`.
- Outputs: PAGE-XML (interne Repräsentation), ALTO, TEI, Plaintext.
- Kosten: ≈ **0,12 €/Seite** über API (50 % des UI-Credit-Preises).
- Latenz: Sekunden bis wenige Minuten/Seite — *interaktiv genug* für Vision §5.

**Free-Tier in unserer App:**

- Default-Quote pro Nutzer (z.B. 5 Seiten/Monat) für Gelegenheitsnutzer.
- Power-User können eigene Transkribus-Credits hinterlegen.
- Rate-Limiter im FastAPI-Adapter; PAGE-XML-Cache pro Bild-Hash (gleicher
  Brief, gleiches Ergebnis — kein Doppel-Bezug von Credits).

**Optionaler Self-Hosted-Pfad (post-MVP):**

- **TrOCR** `dh-unibe/trocr-kurrent` (HuggingFace, CER **2,65 %**, gratis,
  MIT-kompatible Modell-Lizenz).
- CPU-Inferenz machbar, aber langsam (~1–3 s/Zeile) — daher Job-basiert mit
  Progress-Notification statt synchron.
- Bild → Linien-Segmentierung davor: **Kraken**, **Loghi-Laypa**, oder
  **docTR** (alle CPU-fähig).
- Für Datenschutz-Bedarf („Dokument darf das Haus nicht verlassen") und für
  Power-User, die viele Seiten lesen.

**Architektur des Adapters:**

- FastAPI-Router `/htr/*` mit zwei Backends austauschbar (Transkribus
  Default / TrOCR Self-Hosted Fallback).
- **PAGE-XML** als interne Repräsentation (Standard, gut tooling-unterstützt).
- Job-Modell mit Status-Polling im Frontend (Transkribus liefert async).

> API-Details, Latenz-Tabellen, Preise, Fallback-Konfiguration:
> [`reference/htr-integration.md`](../reference/htr-integration.md).

---

## 14. Lese-Lupe (didaktisches Killer-Feature)

Vision §5 (Lese-Lupe-Teil): Bild plus Overlay zur Lese-Hilfe (§13):
Klick auf einen verwirrenden Buchstaben → strukturierte Erklärung („das
ist medial ſ, kein f — hier fehlt der Querstrich"). Verbindet HTR-Output
mit den Regel-Erklärungen aus
[`orthographie-regeln.md`](../schriftkunde/orthographie-regeln.md).

**Display-Schicht:**

- **OpenSeadragon** als Deep-Zoom-Image-Viewer; bewährt für IIIF.
- **Annotorious v3** für Bbox/Polygon-Overlays; W3C-Web-Annotation-konform,
  Click-Handler-API.
- **IIIF Image API + Presentation API 3.0** für Bilder; macht die Lese-Lupe
  als Beifahrer zu nachnutzbaren IIIF-Manifesten.

**Glyph-Erkennung als didaktische Schicht — eigene
analysis-by-synthesis-rückwärts:**

- Für jeden klickbaren Glyph-Bereich: alle Library-Templates fitten, bestes
  Match nehmen, strukturierte Erklärung aus
  [`orthographie-regeln.md`](../schriftkunde/orthographie-regeln.md)
  zurückgeben.
- *Funktioniert sinnvoll erst, wenn die Library breit genug ist* —
  MVP-Stand mit 11 Templates reicht für Demo, nicht für ganze Briefe.
- Vorteil gegenüber fremden HTR: **Erklärbarkeit**. Wir können nicht nur
  *dass*, sondern *warum* dieser Buchstabe so erkannt wurde — direktes
  Bonusprodukt unseres generativen Duktus-Modells.

**Granularitäts-Stufen:**

- **MVP der Lese-Lupe:** Wort-Granularität (aus Transkribus-PAGE-XML);
  Klick auf Wort → dominanter Glyph wird gezeigt, Regel-Lookup aus
  Orthographie-Regeln.
- **Spätere Stufe:** Char-Granularität — entweder via Kraken hOCR (`x_bboxes`
  auf Zeichen-Ebene) oder eigener Glyph-Detektor (YOLO/DETR) sobald
  Trainingsdaten vorhanden.

**Verzahnung mit §13:** §13 liefert den Text (was steht da), §14 erklärt die
Glyphen (warum sieht das so aus). Beide bauen auf dem HTR-Adapter aus §13.

---

## 15. Print-Pipeline (Übungsblätter)

Vision §2 verlangt inhaltsbewusste Vorlagenblätter — Text und passende
Lineatur in einem Schritt, druckbar.

**Stack:**

- **WeasyPrint** (Python, in FastAPI eingebettet) — HTML+CSS → PDF, kein
  Chromium-Overhead. Docker-Image 200–400 MB statt 1,5–2 GB für Puppeteer/
  Playwright. Cold-Start ~250 ms.
- **CSS Print Media Queries** + **CSS Grid** für saubere A4-Pagination und
  konfigurierbare Lineatur über mehrere Seiten.
- **SVG-Glyph-Embedding** aus dem Renderer (§11) — die Vorlagen-Buchstaben
  werden als gefüllte Outline-SVGs erzeugt, die WeasyPrint nativ einbettet.

**Konfigurierbare Lineatur:**

- Verhältnis Ober-/Mittel-/Unterband frei wählbar (`style_ratio` auf
  `source` — siehe §3 / `core/template.template_guides`).
- Default 2:1:2; 2:3:2 (Offenbacher) und 1:1:1 (Sütterlin) als Presets; alle Verhältnisse zugelassen.
- Beliebiger Eingabetext (von Tagebuch bis Übungsphrase) wird via Renderer
  in Kurrent gesetzt und in die Lineatur eingebettet.

**API-Schicht:** Neue FastAPI-Route `POST /worksheet` — Konfiguration
(Wortliste, Lineatur-Ratio, Hand-Auswahl, Zeilenzahl) → PDF-Stream
(synchron, da Generierung schnell ist).

---

## 16. Frontend-Architektur

**anyplot-Stil** — der gleiche Stack wie `~/projects/anyplot/app/`, das
anyplot.ai auf Cloud Run trägt:

- **React 19** + **Vite (mit SWC-Plugin)** für schnellen Build/HMR.
- **MUI 9** + **Emotion** für Komponenten.
- **React Router 7** für Client-Side-Routing.
- **`react-helmet-async`** *(geplant, post-MVP)* für SEO-Meta-Tags pro
  Route. Google rendert JS und indexiert SPAs gut; Bing/DuckDuckGo lesen
  Meta-Tags. Für unsere Reichweite (Genealogie + Lernende) reicht das.
  SSG-Migration bleibt Option, falls Tooling-Bedarf entsteht.
- **`react-i18next`** *(geplant, post-MVP)* für DE/EN-Internationalisierung
  mit URL-Präfix (`/de/…`, `/en/…`); deutscher Default, englischer Pfad als
  zweiter Hebel. Bis dahin liegen die deutschen UI-Strings als
  Pre-i18n-Namespaces unter `locales/de/`.

**Routenstruktur** (die öffentliche Liste sind **Ziel-Routen für die
Post-MVP-Phasen P1+**; der Ist-Stand der IA — drei Bereiche, zwei Hubs,
die heutigen Pfade — steht in
[`design-system.md`](design-system.md) §6):

- **Öffentliche Ziel-Routen (P1+):** Einstieg, Lese-Regeln, Glossar,
  animierte Buchstaben-Tafel, Schreiben-üben (Lineatur-Konfigurator),
  Lese-Hilfe (Upload), Hände vergleichen, Open-Data-Export-Seite.
- **Admin-Routen (Auth-geschützt):** Bbox-Editor, Stylus-Trace,
  3-Spalten-Diagnostic, Source-Verwaltung. Code lebt weiter im
  Verzeichnis `/app/` (kein zweites Frontend); im URL-Raum wandern sie
  unter `/admin/*` mit Auth-Gate. Details:
  [`reference/frontend-stack.md`](../reference/frontend-stack.md) §2.

**Hosting & Deploy:**

- **GCP / Cloud Run** wie anyplot — eigenes GCP-Projekt.
- **Zwei Cloud-Run-Services** (live seit 2026-05-29): `kurrentschrift-app`
  serviert das statische Vite-Build hinter nginx (kurrentschrift.ink),
  `kurrentschrift-api` das FastAPI (api.kurrentschrift.ink) — je eigenes
  `Dockerfile` + `cloudbuild.yaml` unter `app/` bzw. `api/`.
- CI/CD über Cloud Build mit getrennten Triggern pro Service (Domains,
  Cloudflare Access, Migrate-Job).

> Build-Schritte, Komponenten-Map, Auth-Konfiguration:
> [`reference/frontend-stack.md`](../reference/frontend-stack.md).

---

## 17. Open-Data-Export

> **Status (Open-Core, Stand 2026-06):** Zurückgestellt. Das Projekt läuft
> aktuell **Open-Core** — Code MIT, der *gelernte* Datensatz (Glyph-Vorlagen,
> Duktus, Schrift-Statistik) und die daraus trainierten Lese-Modelle bleiben
> vorbehalten. Dieser Abschnitt beschreibt den *möglichen späteren*
> Open-Data-Pfad, kein aktuelles Vorhaben (Vision §7).

Vision §7: kanonische Glyph-Daten (Anker, Schwellzug, Duktus-Reihenfolge)
als zitierbares Open-Data-Paket für die Forschungs-Zielgruppe. Heute
nirgends öffentlich verfügbar — die ehrliche Lücke, die wir füllen können.

**Veröffentlichungs-Pfad:**

- **Zenodo + GitHub-Release-Integration.** Jeder Git-Tag erzeugt
  automatisch einen Zenodo-Eintrag mit eigener DOI; Top-Level-DOI für die
  Reihe, Versions-DOIs pro Release. Standard in Digital Humanities.
- **HTR-United Catalog** als Sichtbarkeits-Schicht, sobald Ground-Truth-
  Linien dazukommen.

**Lizenz: CC-BY 4.0** — DH-Standard für Datasets; Namensnennung erhalten,
maximale Nachnutzung. Konsistent mit
[`quellen-und-rechte.md`](../reference/quellen-und-rechte.md).

**Formate:**

- **Primär:** JSON-Schema unseres Library-Eintrags (Anker + Schwellzug-
  Profil + Duktus-Reihenfolge + entry/exit/coupling). Direkt aus den
  `templates`-Rows der DB exportierbar.
- **Optional zusätzlich:** TEI-XML mit `<msDesc>` / `<handDesc>` /
  `<scriptDesc>` für DH-Anschluss; **IIIF-Manifest** für Beispielzeilen, wo
  Bildmaterial mitveröffentlicht werden darf.

**Was wir nicht veröffentlichen:**

- Daten aus copyright-geschützten Quellen (siehe
  [`datenablage.md`](../reference/datenablage.md) §1, Klasse 2 + 3).
- Identifizierende Information über private Sample-Spender (sofern nicht
  ausdrücklich freigegeben).

---

## Quellen (externe Fakten)

- **Transkribus** Text Recognition API + Modelle: transkribus.org/plans,
  transkribus.org/text-recognition-api, blog.transkribus.org (3 AI-Modelle
  für deutsche Schrift). Eigenes Modell ab ~50 transkribierten Seiten.
- **TrOCR Kurrent:** huggingface.co/dh-unibe/trocr-kurrent (CER 2,65 %, UB
  Bern); huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII.
- **Hinge-Features:** Bulacu/Schomaker, *Writer Identification Using Edge-
  Based Directional Features*, IJDAR 2007; Groningen Δn-Hinge-Variante.
- **Annotorious v3 + IIIF:** annotorious.dev, iiif.io/api/presentation/3.0/,
  iiif.io/api/cookbook/recipe/0261-non-rectangular-commenting/.
- **AnimCJK / Hanzi Writer** als UX-Vorlage:
  github.com/parsimonhi/animCJK, hanziwriter.org.
- **CanvasKit / Skia-WASM:** skia.org/docs/user/modules/canvaskit/.
- **WeasyPrint:** weasyprint.org; HTML→PDF Benchmark 2026 pdf4.dev.
- **Astro vs. Next.js / Vite (Stand 2026):** alexbobes.com Astro/Next
  Deep-Dives — nicht eingesetzt, aber als Alternative für späteren Pivot
  dokumentiert.
- **Zenodo / HTR-United Catalog:** zenodo.org, htr-united.github.io.
- **DigiPal / Archetype:** kdl.kcl.ac.uk/projects/digipal,
  zenodo.org/records/5572558.
- **„Cursive Transformer" (2025):** brauchbare verbundene Schreibschrift aus
  ~3.500 Wörtern — arXiv 2504.00051. (Relevant nur für optionales ML-
  Spätstadium, siehe §2.)
