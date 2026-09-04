# Verfahrensseite Lotse

> **Status (2026-09-01): lebend.** Register-Seite des Verfahrens „Lotse“
> (Konvention: [`verfahren.md`](verfahren.md)). Nachzieh-Pflicht: Jeder
> §14-Eintrag zu einem Lotse-Arm (adoptiert oder verworfen) ergänzt hier
> seine Ledger-Zeile; eine Adoption aktualisiert „Aktueller Stand“. Das
> Gate dazu ist `tools.docs_register check` (CI-Job „Docs-Register“).

## Steckbrief

- **Anzeige-Name:** Lotse *(Arbeitstitel)* — Owner-Idee 2026-08-16
  (tintenfolger.md §7.8).
- **Technisch:** `tools/inkpilot` — Karte (komponierte Bahn) +
  Wasserweg (routeg-Skelettgraph) + Ritt (Viterbi über die
  Sample-Kette). Reine Messschicht, Kandidat über den File-Provider.
- **Rolle:** die Doktrin „Geometrie aus der Tinte, Ordnung aus dem
  Prior" radikaler als die Kette: direkt auf der Tinten-Mitte fahren,
  den Duktus nur an Entscheidungsstellen als KARTE fragen.

## Aktueller Stand: v0.17 (2026-08-20)

Adoptierte Konstanten (`tools/inkpilot/pilot.py`):
`TAIL_RUNOUT_MAX_UNITS` = 1,0 (Schienen-Auslauf) ·
`RIDE_DOUBLE_MAP_PRIORITY` = True (v0.5) ·
`RIDE_DOUBLE_ZONE_MARGIN_UNITS` = 0,35 (v0.7) ·
`MAP_CROSSING_WINDOW_UNITS` = 0,35 + `MAP_CROSSING_PIN` = True (v0.9) ·
`MAP_RUN_PIN_KNOTS` = **"bridges"** + `PIN_KNOT_PLATEAU_UNITS` = 0,35
(v0.11/v0.16 — Knoten-Anker mit Plateau-Feld in Fenster-Läufen UND
allen natürlichen Brücken) · `UNTWIST_WINDOW_UNITS` = 0,5 (v0.13 —
paarweise Entdrillung) · `UNTWIST_SOLL_BUDGET` = True (v0.16 —
**Lineal-Soll-Budget**: die Entdrillung darf keine Nachbarschaft
unter ihr Karten-Soll ziehen, gezählt vom gefrorenen
Kreuzungs-Detektor auf der Karte) · `UNTWIST_SOLL_MATCHING` =
"reserve" (v0.17 — **Reservierungs-Veto**: das Soll wird je Pass
eins-zu-eins auf die Events gematcht, reservierte Events sind
unpaarbar; adoptiert bei Zähler-Parität per vorregistrierter
Konstruktions-Regel). Zahlen (dev-19, gefrorener Root) — **zwei
Lineal-Stände, beide mit Datum**: auf der alten Marken-Kappe 0,8
(§14 „Lotse v0.16/v0.17 `aug20`") dtw 0,0585 med · p90 **0,1122**;
auf der heutigen Kappe 1,5 (§14 „Lineal L-U `aug26`") dtw **0,0545**
med · p90 **0,1164** · worst muß-2 0,1457.

**Der „Sprung" 0,0585 → 0,0545 ist am `sep04` aufgelöst und war
keiner** (§14 „Lotse-Sprung `sep04`"): 0,0545 ist der dtw-Wert des
Wortes `laden` — Rang 9 der 19, während der Median Rang 10 ist
(`will`, 0,0585). Die `aug20`-Artefakte liegen noch vor, kein
Lotse-Report jenes Abends misst 0,0545, und das einzige Wort, das den
Median hätte verschieben können (`will`), ist zwischen den beiden
Daten beweisbar unbewegt. Die L-U-Zahl ist also ein Rang-Griff
daneben beim Übertragen. **Gültig für `aug26` ist 0,058522 auf Kappe
0,8**, wie am `aug20`; die Kappe verschiebt weiterhin nur p90 und
worst.

**Die Zahlen dieses Abschnitts sind damit trotzdem nicht die
heutigen.** Sie stammen von der `aug14`-Wurzel, hinter der inzwischen
drei Neu-Exporte liegen (`sep01` §15-Rechteck-Reparatur, `sep02`
LF11-Write, `sep03` Neubau). Frisch geritten misst der Lotse am
`sep04` dtw-Median **0,056080** (auf beiden Kappen), p90 0,111440 /
**0,115527**, worst muß-2 0,151524 / **0,157229**, aiou **0,7527**,
`cross_spurious` **1**. Bis eine Duell-Runde beide Routen auf
derselben heutigen Wurzel nachmisst, sind die `aug26`-Zahlen nur
untereinander vergleichbar.
Unverändert über beide Stände: **Netto-Kreuzungsdefekte 6**
(missing 1 — nur unters letzter Ritt-Rest) ·
Kreuzungs-Ortsfehler-Median **0,066 xh** ·
`marks_missing` 0 · aiou 0,740 — Struktur WORTGLEICH zu v0.13,
kein Wort verliert (beste dtw-Gewinne −0,0035..−0,0059: muß-2,
Galoppieren, mit, muß-3; aiou bis +0,0117). Rest-Spurious:
Gewebe-Duplikate über dem 0,5-Fenster — warten auf die
Platzierungs-Reparatur der Karte (dann Fenster-Wiedervorlage). **Paarung seit den
Kette-v2/v3-Re-Baselines (`aug19`, Assembly-Ordnung +
Trace-Reparatur): die Kette führt knapp auf Median (0,0491 gegen
0,0585) und p90 (0,089 gegen 0,112 nach v0.16)** (der
−24-%/−18-%-Vorsprung gegen v1 bestand fast vollständig aus
deren Kandidaten-Schicht-Artefakten); der Lotse behält Struktur
(6 gegen 21 Netto-Defekte), aiou (0,743 gegen 0,699) und den
Kreuzungs-Ortsfehler (0,066 gegen 0,083 xh).

## Ledger (Versionen; Belege in §14 „Route Lotse …“)

| Datum | Version/Arm | Ein Knopf / Mechanismus | Verdikt |
|---|---|---|---|
| aug16 | v0.1 | Grundimplementierung: Karte → Skelett-Ritt | Gate verfehlt (dtw 0,119 vs. Kette 0,062), aber unter-Fund 0,450 → 0,064; Route offen |
| aug16 | v0.2 (A5) | `DOUBLE_PASS_OFFSET_FRACTION` — Parallel-Versatz aus Breiten-Evidenz | verworfen (fast-parallele Züge kreuzen nie transversal) |
| aug16 | v0.3 | `JUNCTION_CHORD_RADIUS_FRACTION` — Knoten-Sehne | verworfen (aiou-Kill; Fund: lange geteilte Schienen) |
| aug16 | v0.4 | `MAP_PRIORITY_IN_RETRACE` — Karten-Vorfahrt in Karten-Retrace-Zonen | verworfen (falscher Trigger) |
| aug16 | Schienen-Auslauf *(Owner-Fund-Arm, ohne v-Nummer)* | `TAIL_RUNOUT_MAX_UNITS` | **adoptiert 1,0** (dtw 0,119 → 0,101; und 0,343 → 0,087) |
| aug16 | v0.5 | `RIDE_DOUBLE_MAP_PRIORITY` — Karten-Geometrie in Ritt-Doppelzonen | **adoptiert** (0,101 → 0,085; 5 Kreuzungen zurück; arc ratio 2,48 → 1,66) |
| aug16 | v0.6 | `SMOOTH_ITERATIONS` — Feinschliff | verworfen (das Lineal sieht den Zickzack nie; Glättung = Darstellungsstufe beim Konsumenten) |
| aug17 | v0.7 | `RIDE_DOUBLE_ZONE_MARGIN_UNITS` — Zonen-Ausweitung | **adoptiert 0,35** (Defekte 35 → 32; ehrlicher Teilbefund: nur Punkt-Pinch-Klasse) |
| aug17 | v0.8 | `MAP_CROSSING_WINDOW_UNITS` roh — Karten-Vorfahrt an Karten-Selbstschnitten | verworfen (aiou-Kill; Topologie voll bestätigt: Defekte 32 → 4) |
| aug17 | v0.9 | dieselben Fenster, ans Ink **gepinnt** (`MAP_CROSSING_PIN`) | **adoptiert 0,35** (dtw 0,0578, gepaart −24 %, Defekte 7) |
| aug19 | v0.10 (L1d) | `MAP_RUN_PIN_KNOTS` roh — Knoten-Anker als Punkt-Knoten (Owner-Fund: k-Kringel/W/r) | verworfen (Punkt-Feld schert an der Kreuzung: Merge/Oskulation in dichten Clustern; Gewinnseite real: aiou +0,027, Ortsfehler halbiert, Spurious-Heilung) |
| aug19 | v0.11 (L1e) | dieselben Anker als **Plateau-Feld** (starre Cluster-Translation, global fusioniert) | **adoptiert "windows"** (Defekte 7, missing 3 → 1 inkl. Galoppieren-p-Rückkehr, Ortsfehler −43 %, k-Kringel nachgefahren; "all" um ein Doppel-X verworfen) |
| aug19 | v0.12 (L1f) | `PIN_PLATEAU_CHORD` — Plateau-Sehne gegen die Doppel-X-Duplikate | verworfen (der Wackel WAR das X: Sehnen an Schleifenschlüssen parallel, missing 1 → 8, Retraces zerstört; Rettungswege Entdrillung/asymmetrische Sehne benannt) |
| aug19 | v0.13 (L1g) | `UNTWIST_WINDOW_UNITS` — paarweise Entdrillung der Gewebe-Duplikate (Spiegelung des Wiggle-Bogens an der Paar-Sehne) | **adoptiert 0,5** (Netto-Defekte 7 → 6, wills Duplikat heilt; 0,8 vom Kill verworfen — Geometrie trennt Gewebe nicht von echten engen Doppeln → soll-budgetierte Entdrillung als Rettungsweg) |
| aug19 | v0.14 | „all" + Entdrillung — Zonen-Rides/Brücken mit Knoten-Plateau-Pinnung | verworfen per Gate (Netto 8 > 6: G-Kopf-X stirbt an der formfremden G-Karte, p erfindet eines) — aber aiou +0,012 und der stärkste Sichtbeweis der Runde (das G fast hand-gleich geritten); Wiedervorlage nach den Karten-Form-Autorenschritten |
| aug19 | v0.15 (L1h) | `UNTWIST_SOLL_BUDGET` — Entdrillung nur, wo die Nachbarschaft nicht unter ihr Karten-Soll fällt | verworfen (das Budget erbt die Karten-Platzierungsfehler: unters echtes Paar stirbt trotz Budget, wills Fix wird fälschlich vetiert — dritte Bestätigung der Karten-Form-Decke; Wiedervorlage mit v0.14 nach den Autorenschritten) |
| aug19 | Wiedervorlage v0.14 auf der LF3b-Karte | `MAP_RUN_PIN_KNOTS` = "all" auf der topologie-reparierten Kandidaten-Karte (§14 LF3b) | verworfen per Gate (Netto 7 > 5, Riss WIEDER Galoppieren) — **die Karten-Form-These der „all"-Stufe ist damit widerlegt**: der Bruch liegt im Ritt des dichten G-Knoten-Komplexes; Tinten-Gewinne erneut bestätigt (aiou +0,004, p90 −0,001, kein dtw-Verlierer) → G-Kopf-Ritt-Autopsie, dann selektive Pinn-Stufe |
| aug20 | G-Kopf-Ritt-Autopsie *(Befund, kein Arm)* | instrumentierte Pinn-Schicht + Entdrillungs-Forensik auf der stroke-gleich reproduzierten LF3b-Karte | **der Riss ist die parität-blinde ENTDRILLUNG, nicht die Pinnung** (vor der Entdrillung hat „all" das G-Kopf-X und den sichtbar saubersten Ritt; die Paar-Spiegelung frisst echtes X + Duplikat, 2 → 0 wo die Hand 1 schreibt); v0.15s Fehlschlag = Soll-DOPPELZÄHLUNG (will roh 10 gegen wahre 4); 0,8-Fenster erneut tot mit Mechanismus (unter verliert alle drei X — Platzierungs-Decke, 4. Bestätigung) |
| aug20 | v0.16 (L1i) | selektive Pinn-Leiter (`bridges` · `zones` · `all`) mit **Lineal-Soll-Budget** (§7.7-Wiedervorlage v0.14+v0.15; Soll-Quelle = der gefrorene Kreuzungs-Detektor auf der Karte) | **adoptiert "bridges"+Budget** (Struktur stellen-identisch zur Basis, kein Wort verliert; p90 0,1129 → 0,1122, chamfer 0,0410 → 0,0404, vier Wörter −0,0035..−0,0059 dtw, mits Retrace heilt); zones/all verworfen per Gate (Netto 6 > 5 — exakt die eine Galoppieren-p-Oskulation; **das G-Kopf-X überlebt dort unter Budget**) → Zonen-Stufe nach dem K1-p-Platzierungs-Arm wiedervorlegen |
| aug20 | Karten-Soll-Autopsie *(Befund, kein Arm)* | Platzierungskarte dev-19 (Lineal-Soll ↔ Hand-X) + Veto-Forensik an unter@0,8 | **die „Platzierungs-Decke" ist eine SOLL-VOLLSTÄNDIGKEITS-Lücke**: die Karte kennt 40/41 Hand-X (Ortsfehler median 0,150 xh; blind nur das zweite X von unters t-Stamm-Doppel); die p-„0,85-Kreuzungen" waren Artefakte der rohen Doppelzählung; jedes Zähl-Veto (Radius UND Delta) fällt an unters 12-Events-über-1-Soll-Cluster als Commons-Problem; das 0,8-Fenster bleibt auch mit Reservierung tot (t-Stamm-Doppel: Hand 2 X, Karte kennt 1) → **Karten-Soll-Vollständigkeit an Join- und Rückpass-Schleifen = Composer-Arm** |
| aug20 | v0.17 (L1j) | **Reservierungs-Veto** (`UNTWIST_SOLL_MATCHING` = "reserve"): Soll je Pass eins-zu-eins auf die Events gematcht, reservierte Events unpaarbar | **adoptiert per vorregistrierter Paritäts-Regel** (beide Roots zähler-identisch je Wort, alle Gates PASS; die Schutzklasse im Unit-Test gepinnt, Spiegelungen sinken: Galoppieren 15 → 11) — das Budget-Veto erfüllt seine Semantik jetzt konstruktiv |
| aug20 | t-Stamm-Ritt-Autopsie *(Befund, kein Arm)* | Schicht-Triage an unters letztem missing (dem zweiten t-Stamm-X) | **die „Vollständigkeits-Lücke" ist eine AUFLÖSUNGS-Grenze**: die rohe Komposition führt das t-Doppel überall (Platzierungskarte auf ROHER Karte: 41/41 Hand-X, median 0,159 xh) — `SAMPLE_STEP_UNITS` = 0,12 ist gröber als das 0,06-xh-X-Paar, in Soll-Quelle UND Ritt-Bahn; ein „Soll-Quelle roh"-Zwischenknopf war an den Proben wirkungslos (Symptom, nicht Wurzel) |
| aug20 | v0.18 (L1k) | **Auflösungs-Leiter** `SAMPLE_STEP_UNITS` {0,06 · 0,04} | verworfen per Gate — die Struktur-These bestätigt sich exakt (Netto 5 → **3**, unters missing heilt, ein Galoppieren-Gewebe fällt: die beste Netto-Zahl der Route), aber der Schritt ist kein freier Knopf: die Ritt-ÖKONOMIE ist sample-denominiert (`RIDE_DOUBLE_MIN_GAP` in Samples, Brücken-Preis pro Sample) → dtw-Verlierer bis +0,035 (muß-Familie), aiou-Median −0,004, neue Retrace-Defekte; 0,04 verschärft (Ökonomie-Drift, keine Konvergenz). Rettungsweg (a) „feine Emission" an den Proben verworfen (rohe Karte trägt Mikrostruktur: 32 Spurious); stehend bleibt (b) **schritt-invariante Reskalierung**, dann Wiedervorlage |
| aug20 | v0.19 (L1l) | **schritt-invariante Ökonomie** (Emissions-Skala `Schritt/0,12` · `MAX_RIDE_UNITS` 0,96 · `RIDE_DOUBLE_MIN_GAP_UNITS` 0,48) + §7.7-Wiedervorlage der Leiter {0,06 · 0,04} | **Re-Denominierung BLEIBT** (Sprosse 0 byte-identisch zu v0.17 auf beiden Roots — bewiesen neutraler Grundlagen-Refactor); **Leiter erneut verworfen**: der Drift ist umverteilt, nicht beseitigt (Wer +0,031, muß-2 +0,022; Galoppieren gewinnt diesmal einen Spurious) — die letzte Kopplung ist die EMISSIONS-Feinheit selbst (feinere Brücken emittieren Karten-Mikrostruktur; Struktur-Gewinn und Geometrie-Verlust hängen an derselben Auflösung). 0,12 bleibt der Betriebspunkt; Rettungsweg: **Karten-Glättung auf Zähler-Skala vor der Feinabtastung** |
| aug20 | Glättungs-Proben *(Befund, kein Arm)* | `smooth_map_strokes` (Box entlang der Bahn, Endpunkte exakt, deklariert-off) an 5 Proben-Worten, Fenster × Schritt | **die Auflösungs-Familie ist GESCHLOSSEN**: der Feinschritt-Drift besteht auf geglätteter Karte fort (Wer +0,033, Fenster egal) — die letzte Kopplung ist die ENTSCHEIDUNGS-GRANULARITÄT des Viterbi (mehr Samples = mehr Umsteigepunkte); kein weiterer Leiter-Anlauf ohne anderen Solver. Nebenbefund: Glättung AM Betriebspunkt gemischt-groß (mit aiou +0,097, muß-2-Retraces heilen, unters t-X2 erscheint · Wer +0,031 dtw, Galoppieren tauscht ein X) → eigener Kandidat mit eigener Pre-Reg. **Zweiter Nachtrag: auch dieser Kandidat an der Fenster-Feinleiter verworfen** — kein Fenster ohne Verlierer (die 3-Punkte-Box-Stufe „Kernel-3", auf die alle Fenster < 0,06 quantisieren: Galoppieren/mit zahlen; 0,06: Wer kippt), die Effekte sind Entscheidungs-Kipp-Punkte; die Karten-/Abtastungs-Familie ist ERSCHÖPFT, die Route sitzt in einem empfindlichen Optimum |
| aug26 | **L-U Lineal-Nachmessung** *(Lineal-Re-Baseline, kein Lotse-Arm)* | Marken-Kappe `MARK_MAX_ARC_UNITS` 0,8 → 1,5 — der u-Bogen zählt nicht mehr als Marke (§14 „Lineal L-U `aug26`") | Route selbst unberührt, aber ihre Zahlen wandern: dtw **0,0545 → 0,0545**, p90 **0,1122 → 0,1164**, worst muß-2 0,1404 → 0,1457; 16 Struktur-Spalten byte-gleich. Der L-U-Gewinn liegt auf der Kette (p90 0,2355 → 0,0896), der Lotse verliert minimal — das ist der vorregistrierte, akzeptierte Preis einer Instrumenten-Reparatur |
| aug26 | **LF3b-W Schreib-Karte** *(Laufform-Arm, hier nur die Wirkung)* | die 13 topologie-reparierten Laufform-Zeilen ohne p, geschrieben (§14 „Laufform LF3b-W `aug26`") | Gate (c) PASS: dtw 0,0545 / p90 0,1164 unverändert, **aiou 0,7398 → 0,7484**, spurious 5 → 4 (Galoppieren 3 → 2), `retrace_missing` 5 → 3, missing 1 = 1, Marken unverändert; bewegt nur die drei Schreib-Glyph-Wörter (das, linken, Galoppieren). Zahlengleich mit der trockenen LF3b-Karte vom `aug19` |
| sep04 | **Absprung-Forensik** *(Autopsie, kein Arm)* | Herkunfts-Sensor je emittiertem Punkt + Tintenkörper-Abstand (`tools/inkpilot/forensics.py`), gegen `pilot_word` bit-gleich gespiegelt **`bridge_no_rail` kommt auf dev-19 kein einziges Mal vor** (die Karte hat überall eine Schiene in Bord-Reichweite), und der Schienen-Auslauf liegt in 201 Punkten NIE daneben. Was danebenliegt, ist Karten-Vorfahrt — und die Ritt-Doppelzone ist mit 1,3 % Weganteil in **49,5 %** ihrer Punkte außerhalb der Tinte (Fenster: 8,9 %, gewöhnlicher Ritt: 0,03 %). Von den 39 Ereignissen sind 23 GEERBT (Karten-Abdrift; bei der Zonen-Klasse ist der Überschuss über die Karte im Median exakt +0,0000 — der Folger ist ein treuer Bote, die Ursache liegt in der Komposition), 15 macht die starre Pinnung selbst (Fenster-Versatz, Median +0,0928 xh, max +0,2146 — und dieselbe Pinnung zieht in 12 anderen Fenstern um −0,0165 zurück) |
| sep04 | **Lotse-Sprung** *(Autopsie, kein Arm)* | Nachmessung der `aug20`-Artefakte + der `aug20`-Kandidatenbytes auf der heutigen Wurzel | **gegenstandslos** — 0,0545 ist `laden` (Rang 9), der Median ist Rang 10 = 0,058522; kein `aug20`-Report misst 0,0545 und `will` ist zwischen den Daten beweisbar unbewegt. Zweitbefund: 15 der 19 Wörter reproduzieren aus `aug20`-Bytes ziffergleich, vier nicht (`das` 0,0307 → 0,2504, `und`, `Wer`, `zwei`) — die `sep01`-Rechteck-Reparatur, also ist keine dev-19-Zahl von vor `sep01` mit einer danach vergleichbar |

Benannter Fehlermodus der Route: **Junction-Pinch** (Glossar) — die
v0.7/v0.8/v0.9-Kette ist seine vollständige Abarbeitung; seit v0.11
ist das **Doppel-X-Duplikat** (Glossar) die dominante
Rest-Spurious-Klasse. Seit der `sep04`-Forensik sind zusätzlich die
beiden Klassen benannt, in denen die Route die TINTE verlässt:
**Karten-Abdrift** (geerbt, die Zonen-Vorfahrt reicht die
Platzierungsfehler der Karte wörtlich durch) und **Fenster-Versatz**
(selbst gemacht, die starre Pinnung trägt den Bauch des
Fenster-Laufs hinaus) — beide im Glossar.

## Offene Blöcke

- **Rest-Duplikate** (Gewebe über dem 0,5-Fenster): Budget
  (v0.16) und Reservierungs-Veto (v0.17) sind adoptiert, aber das
  FENSTER bleibt 0,5 — die `aug20`-Autopsie zeigt 0,8 auch mit
  Reservierung tot: Galoppieren würde komplett heilen (−2), aber
  das zweite X von unters t-Stamm-Doppel fällt, weil die KARTE
  dort nur eine Kreuzung führt, wo die Hand zwei schreibt
  (Abstieg + 0,07-xh-versetzter Rückpass, der K1b-Befund).
  **Präzisiert von der t-Stamm-Autopsie (`aug20` spät):** die
  rohe Komposition führt das Doppel überall (41/41 Hand-X auf
  ROHER Karte) — die „Lücke" ist die 0,12-xh-ABTASTUNG (Soll-
  Quelle und Ritt-Bahn); der Composer ist unschuldig.
  **Endstand (`aug20` nacht):** die Auflösungs-Familie ist
  GESCHLOSSEN (v0.18/v0.19/Glättungs-Proben — die Kopplung ist
  die Entscheidungs-Granularität des Viterbi); der einzige
  benannte Weg zum t-X2 UND damit zur Fenster-Wiedervorlage ist
  der Betriebspunkt-Glättungs-Kandidat (Glättungs-Proben-Zeile:
  unters t-X2 erscheint dort), eigene Pre-Reg.
- **Zonen-Stufe** (der Rest der „all"-Familie): die
  `aug20`-Autopsie hat den v0.14-Riss aufgelöst (parität-blinde
  Entdrillung, nicht die Pinnung) und v0.16 hat „bridges"+Budget
  adoptiert; „zones"/„all" scheitern nur noch an EINEM
  Struktur-Preis — der Galoppieren-p-Oskulation (die
  Zonen-Pinnung zieht die zwei Pässe von 0,17 auf 0,01 xh
  zusammen, der Pierce-Zähler kippt; Platzierungs-Familie).
  Das G-Kopf-X überlebt dort unter Budget, die Tinten-Werte
  wären die stärksten der Route (chamfer 0,0371, aiou-Median
  +0,0038). Wiedervorlage NACH dem K1-p-Platzierungs-Arm.
- **Karten-Form-Klasse** (Katalog nach der Owner-Sichtrunde `aug19`,
  Karten-Overlays; **präzisiert im späten Nachtrag**, §14 v0.15):
  überwiegend eine **Laufform-Lücke, kein Chart-Fehler** — 43 von 62
  Glyphen (alle Versalien, k, s, v, x …) komponieren aus der rohen
  Chart-Form, weil ihnen die Laufform-Variante fehlt (G: 3 QC-Fits
  unter min-n 4, k/W: je 1); das Chart-G ist gut, DIESE Hand
  schreibt das Oval ~65 % breiter. Die Autopsien des Abends (§14
  „Dritter Nachtrag") ziehen ALLE drei Owner-Stellen auf dieselbe
  Schicht: **G/W/k = Laufform-LÜCKE** (der alte
  K3-„W-Trace"-Autorenschritt ist zurückgezogen — die Referenz
  zeigt keinen Ansatz-Retrace, und der vermutete W→e-Join-Ballon
  reproduziert nicht: die komponierte W-Form liegt ~0,4 xh links
  der Hand-Apexe) und **p = Laufform-AGGREGATIONS-Defekt** (das
  Chart-p kreuzt, die gespeicherte p-Laufform hat den Durchstoß an
  den Anker-Median verloren). **Noch am selben Abend gemessen
  (§14 LF1/LF2/LF3/LF3b):** LF1 (Lücken-Schluss roh) und LF2
  (Topologie-Wächter als Voll-Entfernung) sind ehrliche Negative
  mit scharfen Funden (der rohe Anker-Median frisst
  Schleifenschluss-Topologie — h, p gespeichert, G-Draft frisch);
  **LF3b (Topologie-Reparatur am Kompositions-Orakel) besteht
  alle Gates und ist als Kandidaten-Karte adoptiert** (trocken:
  Galoppieren-Soll 6 → 8 = Hand, aiou 0,7398 → 0,7484,
  wordbench −0,0010; DB-Write hinter dbsnapshot + Owner-Go).
  Offen bleiben die Platzierungs-Klassen: e→r-Platzierung in
  `unter` · o→r-Höhe · Vorschub-Drift. Autorenschritt im engen
  Sinn bleibt nur der Bestätigungssatz.
- ~~Rest-Autopsie muß-Klasse~~ **erledigt `aug19`, Attribution noch
  am selben Tag korrigiert** (§14 „L2-Rest-Autopsie"): die
  Kollaps-Klasse (unter + muß×3) ist ORDNUNGS-dominiert — aber
  KETTEN-seitig: die Harvest-Assembly emittiert den abgesetzten
  Deckbogen zwischen den Runs; Hand und Engine-Ordnung (die der
  Lotse als Karte fährt) setzen ihn ans Ende. Die Referenzen sind
  sauber; der Lotse-Vorsprung auf unter/muß schlägt dort zum Teil
  ein Ketten-Assembly-Artefakt (Kandidat „marken-endständige
  Assembly" auf der Kette-Seite, verfahren-kette.md).
- Der **Bestätigungssatz** (A, dann B) als Schlussstein, bevor aus dem
  Dev-Gewinn eine Adoptionsentscheidung jenseits der Routen-Konstanten
  wird (Versiegelung: tintenfolger.md §2.5).
- Fusion „Vier Augen“: Orakel-Decke 0,0491 (aug17); der referenzfreie
  Auswähler bleibt bis zum Bestätigungssatz gesperrt.
