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

## Aktueller Stand: v0.11 (2026-08-19)

Adoptierte Konstanten (`tools/inkpilot/pilot.py`):
`TAIL_RUNOUT_MAX_UNITS` = 1,0 (Schienen-Auslauf) ·
`RIDE_DOUBLE_MAP_PRIORITY` = True (v0.5) ·
`RIDE_DOUBLE_ZONE_MARGIN_UNITS` = 0,35 (v0.7) ·
`MAP_CROSSING_WINDOW_UNITS` = 0,35 + `MAP_CROSSING_PIN` = True (v0.9) ·
`MAP_RUN_PIN_KNOTS` = "windows" + `PIN_KNOT_PLATEAU_UNITS` = 0,35
(v0.11 — Knoten-Anker mit Plateau-Feld in den Fenster-Läufen).
Zahlen (dev-19, §14 „Lotse v0.11 aug19“, lokale Basis): dtw 0,0596
med (gepaart gegen die Kette **−18 %**) · p90 **0,113** (Kette
0,236) · Netto-Kreuzungsdefekte **7**, davon `cross_missing` **1**
(nur unters letzter Ritt-Rest — Galoppierens p-Schleifen-X kehren
zurück, obwohl die Komposition sie nicht hat) ·
Kreuzungs-Ortsfehler-Median **0,066 xh** (v0.9: 0,116) ·
`marks_missing` 0 · aiou 0,743. Dominante Rest-Spurious-Klasse:
Doppel-X-Duplikate (4 von 6).

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

Benannter Fehlermodus der Route: **Junction-Pinch** (Glossar) — die
v0.7/v0.8/v0.9-Kette ist seine vollständige Abarbeitung; seit v0.11
ist das **Doppel-X-Duplikat** (Glossar) die dominante
Rest-Spurious-Klasse.

## Offene Blöcke

- **Doppel-X-Duplikate** (4 der 6 Spurious): die Plateau-Sehne
  (v0.12) ist daran gescheitert — der Wackel trägt Kreuzung und
  Duplikat untrennbar; benannte nächste Mechanismen sind Entdrillung
  bzw. asymmetrische Sehne (§7.9). Erst ein Erfolg dort schaltet die
  "all"-Stufe (Zonen-Rides/Brücken-Pinning) wieder frei. Die
  Duplikate sind keine Topologie-Erfindung (das X ist real, nur
  doppelt gezählt) — Leidensdruck klein.
- **Karten-Form-Klasse**: die k-Kopfschleife fährt auch gepinnt
  formfremd (komponierter Bogen tiefer/schmaler als diese Hand), der
  W-Ansatz bleibt K3 — Kompositions-/Autorenschiene, kein Ritt-Fehler.
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
