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

## Aktueller Stand: v0.13 (2026-08-19)

Adoptierte Konstanten (`tools/inkpilot/pilot.py`):
`TAIL_RUNOUT_MAX_UNITS` = 1,0 (Schienen-Auslauf) ·
`RIDE_DOUBLE_MAP_PRIORITY` = True (v0.5) ·
`RIDE_DOUBLE_ZONE_MARGIN_UNITS` = 0,35 (v0.7) ·
`MAP_CROSSING_WINDOW_UNITS` = 0,35 + `MAP_CROSSING_PIN` = True (v0.9) ·
`MAP_RUN_PIN_KNOTS` = "windows" + `PIN_KNOT_PLATEAU_UNITS` = 0,35
(v0.11 — Knoten-Anker mit Plateau-Feld in den Fenster-Läufen) ·
`UNTWIST_WINDOW_UNITS` = 0,5 (v0.13 — paarweise Entdrillung der
Gewebe-Duplikate). Zahlen (dev-19, §14 „Lotse v0.13 aug19“, lokale
Basis): dtw 0,0585 med · p90 **0,113** ·
**Netto-Kreuzungsdefekte 6** (missing 1 — nur unters letzter
Ritt-Rest; wills Duplikat entdrillt) · Kreuzungs-Ortsfehler-Median
**0,066 xh** · `marks_missing` 0 · aiou 0,740. Rest-Spurious:
3 Gewebe-Duplikate über dem 0,5-Fenster (Galoppieren, mit-2) —
warten auf die soll-budgetierte Entdrillung. **Paarung seit den
Kette-v2/v3-Re-Baselines (`aug19`, Assembly-Ordnung +
Trace-Reparatur): Δ-Median +0,0016, Sign 12:7 — die Kette führt
erstmals knapp auf Median (0,0491) und p90 (0,089 gegen 0,113)**
(der −24-%/−18-%-Vorsprung gegen v1 bestand fast vollständig aus
deren Kandidaten-Schicht-Artefakten); der Lotse behält Struktur
(7 gegen 21 Netto-Defekte), aiou (0,743 gegen 0,699) und den
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

Benannter Fehlermodus der Route: **Junction-Pinch** (Glossar) — die
v0.7/v0.8/v0.9-Kette ist seine vollständige Abarbeitung; seit v0.11
ist das **Doppel-X-Duplikat** (Glossar) die dominante
Rest-Spurious-Klasse.

## Offene Blöcke

- **Rest-Duplikate** (3 Gewebe über dem 0,5-Fenster): die
  paarweise Entdrillung (v0.13) heilt wills Duplikat; das weite
  Fenster (0,8) scheiterte am Diskriminator (Geometrie trennt
  Gewebe nicht von echten engen Doppeln wie mits t-Paar) — der
  benannte Weg ist die **soll-budgetierte Entdrillung** (§7.9).
- **„all"-Stufe (v0.14)**: gemessen und per Gate verworfen — die
  Tinten-Gewinne sind real (aiou +0,012, das G erstmals fast
  hand-gleich geritten, Sichtbeweis in der Chronik), aber die
  Struktur kippt exakt an den zwei schlimmsten
  Karten-Form-Regionen (G-Kopf, p). Wiedervorlage NACH den
  Karten-Form-Autorenschritten — die zahlen damit doppelt.
- **Karten-Form-Klasse** (Katalog nach der Owner-Sichtrunde `aug19`,
  Karten-Overlays): die k-Kopfschleife (tiefer/schmaler), das
  Galoppieren-G (Oval ~halb so breit wie der Beleg, Unterschleife
  spitz), die e→r-Strecke in `unter` (r-Kringel rechts neben der
  Tinte), die W→e-Schleife in `Wer` (K3) und der Vorschub-Drift der
  Galoppieren-Endsilben (~0,2–0,3 xh) — überall fährt der Lotse in
  Zonen/Brücken die formfremde Karte roh („windows" pinnt nur
  Fenster), und die Kette erbt dieselben Stellen als Init.
  Kompositions-/Autorenschiene (Todoist „Karten-Form-Klasse"), kein
  Ritt-Fehler; die „all"-Stufe würde die SICHTBARKEIT beim Lotsen
  dämpfen, hängt hinter der Entdrillung.
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
