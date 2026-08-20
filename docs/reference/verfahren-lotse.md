# Verfahrensseite Lotse

> **Status (2026-08-18): lebend.** Register-Seite des Verfahrens „Lotse“
> (Konvention: [`verfahren.md`](verfahren.md)). Nachzieh-Pflicht: Jeder
> §14-Eintrag zu einem Lotse-Arm (adoptiert oder verworfen) ergänzt hier
> seine Ledger-Zeile; eine Adoption aktualisiert „Aktueller Stand“.

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
Konstruktions-Regel). Zahlen (dev-19, gefrorener Root,
§14 „Lotse v0.16/v0.17 aug20"): dtw 0,0585 med · p90 **0,1122** ·
**Netto-Kreuzungsdefekte 6** (missing 1 — nur unters letzter
Ritt-Rest) · Kreuzungs-Ortsfehler-Median **0,066 xh** ·
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
| aug20 | Karten-Soll-Autopsie *(Befund, kein Arm)* | Platzierungskarte dev-19 (Lineal-Soll ↔ Hand-X) + Veto-Forensik an unter@0,8 | **die „Platzierungs-Decke" ist eine SOLL-VOLLSTÄNDIGKEITS-Lücke**: die Karte kennt 40/41 Hand-X (Ortsfehler median 0,150 xh; blind nur unters e→r); die p-„0,85-Kreuzungen" waren Artefakte der rohen Doppelzählung; jedes Zähl-Veto (Radius UND Delta) fällt an unters 12-Events-über-1-Soll-Cluster als Commons-Problem; das 0,8-Fenster bleibt auch mit Reservierung tot (unters u-n-Doppel: Hand 2 X, Karte kennt 1) → **Karten-Soll-Vollständigkeit an Join-Schleifen = Composer-Arm** |
| aug20 | v0.17 (L1j) | **Reservierungs-Veto** (`UNTWIST_SOLL_MATCHING` = "reserve"): Soll je Pass eins-zu-eins auf die Events gematcht, reservierte Events unpaarbar | **adoptiert per vorregistrierter Paritäts-Regel** (beide Roots zähler-identisch je Wort, alle Gates PASS; die Schutzklasse im Unit-Test gepinnt, Spiegelungen sinken: Galoppieren 15 → 11) — das Budget-Veto erfüllt seine Semantik jetzt konstruktiv |

Benannter Fehlermodus der Route: **Junction-Pinch** (Glossar) — die
v0.7/v0.8/v0.9-Kette ist seine vollständige Abarbeitung; seit v0.11
ist das **Doppel-X-Duplikat** (Glossar) die dominante
Rest-Spurious-Klasse.

## Offene Blöcke

- **Rest-Duplikate** (Gewebe über dem 0,5-Fenster): Budget
  (v0.16) und Reservierungs-Veto (v0.17) sind adoptiert, aber das
  FENSTER bleibt 0,5 — die `aug20`-Autopsie zeigt 0,8 auch mit
  Reservierung tot: Galoppieren würde komplett heilen (−2), aber
  unters linkes u-n-Doppel fällt, weil die KARTE dort nur eine
  Kreuzung führt, wo die Hand zwei schreibt (Soll-
  VOLLSTÄNDIGKEIT, nicht Platzierung — die Platzierungskarte
  matcht 40/41 Hand-X bei 0,150 xh). Weg: der
  **Karten-Soll-Vollständigkeits-Arm** (Composer: Join-Schleifen-
  Kreuzungen — u-n-Doppel, e-Einläufe, unters e→r; der
  aug15-Befund „Hand 34 > Komposition 25"), dann das Fenster
  wiedervorlegen (§7.9).
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
