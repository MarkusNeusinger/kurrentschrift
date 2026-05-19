# Architektur-Referenz

Zusammenfassung der bisher getroffenen Entscheidungen und ihrer Begründung.
Sprache: Deutsch (Prosa) / Englisch (Code, Schema, Identifier).

---

## 1. Problemaufteilung

Das Projekt zerfällt in zwei sehr unterschiedlich schwere Teile, die getrennt
behandelt werden:

| Teil | Status | Charakter |
|---|---|---|
| **Lesen / Transkribieren** | gelöst | Integration, keine Forschung |
| **Schreiben „wie Tinte auf Papier"** | offen | der Forschungskern |

- **Lesen:** Transkribus hat öffentliche Kurrent-Modelle (CER ≈ 5–7 %);
  ein eigenes Modell ist mit ca. 50 selbst transkribierten Seiten trainierbar.
  Open-Source-Alternativen für volle Kontrolle: Kraken/eScriptorium, PyLaia,
  TrOCR-Fine-Tuning. → frühes, motivierendes Feature der Website.
- **Schreiben:** kein integrierbares Standardprodukt. Hier liegt der echte
  Mehrwert (siehe §7).

---

## 2. Architekturentscheidung: ductus-modellbasierte Extraktion

Kernidee: **Analysis-by-Synthesis.** Pro Buchstabe ist a priori bekannt,
in welcher Reihenfolge, mit welchen Absetzpunkten und mit welchem Lauf
(= Ductus) er in der normierten Kurrent vor 1900 geschrieben wurde. Aus dem
Foto/Scan wird *nicht* blind eine Polyline aus dem Skelett gezogen — stattdessen
wird ein kanonisches Ductus-Template an Skelett + Breitenprofil **gefittet**.

- Das **Bild** liefert: Geometrie + Tinten-*Breite*.
- Das **Ductus-Modell** liefert: Strichreihenfolge + Auflösung der Kreuzungen.

Damit wird das aus einem Standbild *unterbestimmte* Kreuzungsproblem
(welcher Ast gehört zu welchem Strich, was kam zuerst) durch den Ductus-Prior
*eindeutig*. Persönliche Varianz = Abweichung von der Norm, nicht Beliebigkeit.

**Bewusst NICHT gewählt — und warum:**

- *OpenType-Font mit Kontextalternativen:* scheitert an echten Verbindungen
  und Varianz; sieht nie „getuscht" aus.
- *ML-Synthese (Graves / Cursive Transformer) zuerst:* braucht Online-Daten
  (Stiftbahn über Zeit); historisches Material ist offline (nur Bild). Bleibt
  optionales Spätstadium, nicht der Einstieg.
- *Blindes Skelett-Tracing:* genau hier liegt das Kreuzungsproblem, das der
  Ductus-Prior löst.
- *Bigram-Datenbank aller Buchstabenkombinationen:* kombinatorisch unmöglich
  und unnötig (siehe §4).

---

## 3. Die Bibliothekseinheit (Schema)

Die natürliche Einheit ist **nicht der Buchstabe**. Eine Einheit ist ein
gefittetes Ductus-Template einer **(Allograph, Formvariante)**-Kombination,
plus deren Abweichung von der Norm. Drei orthogonale Achsen:

1. **Position (Allograph):** initial/medial/final — z. B. ſ vs. finales s.
   *Aus dem Kontext bekannt* (s mitten im Wort → medial).
2. **Formvariante:** mehrere gleichberechtigte, **in der Norm sanktionierte**
   Ductus für denselben Buchstaben an derselben Position (auf Lehrtafeln als
   „A = A" notiert: beide gültig, Schreiber-/Lehrtraditions-Wahl). Keine
   Abweichung, kein Fehler — Teil des kanonischen Modells. *Aus dem Kontext
   NICHT bekannt* (siehe §7).
3. **Per-Instanz-Abweichung:** der konkrete Fit (Statistik, §6).

```python
# One library entry = one fitted ductus instance of one (allograph, variant)
{
  "glyph": "s",
  "position": "final",        # initial | medial | final  -> distinct ductus!
  "variant": 0,               # index into the norm's sanctioned form set
  "canonical": "<ref>",       # shared per (glyph,position,variant); fixed
  "control_points": [...],    # THIS sample's fit (deviation from canonical)
  "width_profile": [...],     # the Schwellzug (from distance transform)
  "entry": {"xy": (x, y), "tangent": deg, "coupling": "baseline"},
  "exit":  {"xy": (x, y), "tangent": deg, "coupling": "midband"},
}
```

Wichtige Festlegungen:

- **Allographe sind getrennte Glyphen.** Medial ſ (langes s im Wortinneren)
  und finales s (Wortende) sind nicht „dasselbe s mit anderem Übergang",
  sondern verschiedene Ductus. Positionsregel wie in arabischer Schrift.
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
  Bibliotheksschlüssel ist daher `(glyph, position, variant)`.

---

## 4. Übergänge sind Konsequenz, keine Daten

Übergänge zwischen Buchstaben sind essenziell — aber **kein eigenes Objekt**
und **kein zu sammelnder Datensatz**. Wenn `exit` von Glyph A und `entry` von
Glyph B als Punkt **plus Tangente** durch die Norm definiert sind, ist der
Verbindungsstrich eine kurze, geometrisch determinierte Kurve zwischen zwei
festgelegten Punkten mit festgelegten Richtungen. Der Ductus *erzeugt* den
Übergang — deshalb keine Bigram-Explosion. Varianz: mehrere echte Fits pro
Glyph + leichtes Jitter auf der Verbindung.

**Ausnahme — geschlossener Satz gelehrter Ligatur-Einheiten.** Die Lehrtafel
zeigt `ch`, `ck`, `tz`, `ſt`, `qu`, `ß` als *eigene gelehrte Einheiten*, nicht
als verbundene Einzelbuchstaben. „Übergang = Konsequenz" gilt für *beliebige*
Buchstabenpaare — aber dieser **bekannte, endliche Satz** muss als eigene
Primär-Glyphen mit eigenem Ductus in die Bibliothek, NICHT als
exit→entry-Verkettung. Enumerieren, nicht generieren.

---

## 5. Schwellzug vs. Tinte — zwei getrennte Kanäle

- **Breite = Druck (Schwellzug).** Aus `skeletonize` (Mittellinie) +
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

Der Mehrwert liegt **präzise in der Kombination** (Ductus-Prior + Skelett/
Distanztransformation + Allograph-Modell + getrennte Kanäle, für normierte
Kurrent vor 1900). Einzeln ist nichts davon neu; die Verbindung mit dieser
Domäne existiert nicht als fertiges Werkzeug.

**Das eine ungelöste Risiko (empirisch, nicht vorab beweisbar):** wie *eng*
das Ductus-Template gefasst wird.

- zu starr → fittet echte historische Hände nicht (jeder Schreiber bricht
  die Norm),
- zu locker → Kreuzungsauflösung wird wieder mehrdeutig — genau das Problem
  zurück, das der Prior lösen sollte.

Dieser Spannungsbogen ist *der* Forschungskern. Muss am Spike empirisch
gefunden werden.

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
zugleich der Hebel für Multi-Stil (§10).

---

## 8. Der Spike (kleinster validierender Schritt)

Nicht Bibliothek/Engine/Website zuerst, sondern:

> Modelliere **medial ſ** und **finales s** als zwei Ductus-Templates,
> fitte beide aus *einer* Vorlage über ~10 Instanzen, und prüfe, ob die
> durch die Norm erzeugte Übergangskurve zum Folgebuchstaben sauber
> anschließt.

Trägt der Fit über 10 reale Varianten stabil und löst die Kreuzung —
Projektkern validiert, Rest ist Ingenieurarbeit. Wenn nicht: in Tagen
statt Monaten geklärt (wertvolles Negativergebnis). Aufwand: Wochenende,
kein Quartal.

---

## 9. Testwort

**Primär: `lesen`** (thematisch passend — das Projekt lehrt Lesen).

| Pos | Glyph | position | Besonderheit / Testet |
|---|---|---|---|
| 1 | l | — | Oberlängen-Schleife (Ascender), Abstrich = dicker Schwellzug |
| 2 | e | medial | Kurrent-e: kleine Schleife → **Kreuzungsfall** (Ductus-Prior) |
| 3 | ſ | **medial** | langes s — **Allograph**, eigener Ductus |
| 4 | e | medial | **2. Instanz** desselben `canonical`, eigener Fit (Statistik) |
| 5 | n | final | berühmte u/n-Verwechslung; Endposition |

`lesen` testet in einem Wort: Allograph (medial ſ), wiederholtes Glyph mit
zwei Fits, zwei Kreuzungsfälle (e), Ascender, und alle Übergänge als
norm-erzeugte Kurven.

**Kontrast: `das`** — d (Ascender), a, **s in position `final`**.
Liefert das *finale* s-Allograph, das `lesen` nicht enthält.

→ `lesen` + `das` = das minimale Allograph-Testpaar für den Spike aus §8.

---

## 10. Reihenfolge

1. **Spike** (§8): ſ vs. s, ~10 Fits, Übergang prüfen. Vor allem anderen.
2. Extraktions-Tool (Scan → Skelett+Distanztransformation → Template-Fit).
3. Bibliothek nach Schema §3 (Glyph + Positionsklasse + Fit + Abweichung).
4. Verbindungs-Engine (entry/exit + Tangente → Übergangskurve).
5. Qualitätspipeline §6 daraufsetzen.
6. Lese-Feature der Website (Transkribus-Integration) parallel — früher Win.
7. Übe-Schleife (moderne Quelle → Rendering) zuletzt, kaum Risiko.

**Konsequenz für Multi-Stil (vormals teures Spätstadium):** Ein „Stil"/eine
„Hand" ist weitgehend ein **Varianten-Auswahlvektor** (welche Formvariante pro
Glyph) **+ Abweichungs-Hüllkurve** über demselben geteilten Kanon — kein
eigenes ML-Modell pro Stil. Damit wird das ursprüngliche Phase-4-Problem
(mehrere historische Stile) erheblich billiger.

---

## Quellen (externe Fakten)

- Transkribus öffentliche Kurrent-Modelle, CER ≈ 5–7 %; eigenes Modell ab
  ~50 transkribierten Seiten — transkribus.org.
- „Cursive Transformer" (2025): brauchbare verbundene Schreibschrift aus
  ~3.500 Wörtern — arXiv 2504.00051. (Relevant nur für optionales
  ML-Spätstadium, siehe §2.)
