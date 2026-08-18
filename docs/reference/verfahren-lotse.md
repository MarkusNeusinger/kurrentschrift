# Verfahrensseite Lotse

> **Status (2026-08-18): lebend.** Register-Seite des Verfahrens „Lotse"
> (Konvention: [`verfahren.md`](verfahren.md)). Nachzieh-Pflicht: Jeder
> §14-Eintrag zu einem Lotse-Arm (adoptiert oder verworfen) ergänzt hier
> seine Ledger-Zeile; eine Adoption aktualisiert „Aktueller Stand".

## Steckbrief

- **Anzeige-Name:** Lotse *(Arbeitstitel)* — Owner-Idee 2026-08-16
  (tintenfolger.md §7.8).
- **Technisch:** `tools/inkpilot` — Karte (komponierte Bahn) +
  Wasserweg (routeg-Skelettgraph) + Ritt (Viterbi über die
  Sample-Kette). Reine Messschicht, Kandidat über den File-Provider.
- **Rolle:** die Doktrin „Geometrie aus der Tinte, Ordnung aus dem
  Prior" radikaler als die Kette: direkt auf der Tinten-Mitte fahren,
  den Duktus nur an Entscheidungsstellen als KARTE fragen.

## Aktueller Stand: v0.9 (2026-08-17)

Adoptierte Konstanten (`tools/inkpilot/pilot.py`):
`TAIL_RUNOUT_MAX_UNITS` = 1,0 (Schienen-Auslauf) ·
`RIDE_DOUBLE_MAP_PRIORITY` = True (v0.5) ·
`RIDE_DOUBLE_ZONE_MARGIN_UNITS` = 0,35 (v0.7) ·
`MAP_CROSSING_WINDOW_UNITS` = 0,35 + `MAP_CROSSING_PIN` = True (v0.9).
Zahlen (dev-19, §14 „Lotse v0.9 aug17"): dtw **0,0578** med
(Ketten-Niveau; gepaart **−24 %**, erstmals das §14-Primärkriterium
erfüllt) · p90 0,118 (Kette 0,236) · Netto-Kreuzungsdefekte **7** —
davon fast alle Soll-vs-Hand-Differenzen (Galoppierens p-Schleifen
fehlen der Komposition selbst; linken/mit-2-Soll-Kreuzungen, die diese
Hand nicht schreibt), keine Ritt-Fehler. `marks_missing` 0.

## Ledger (Versionen; Belege in §14 „Route Lotse …")

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

Benannter Fehlermodus der Route: **Junction-Pinch** (Glossar) — die
v0.7/v0.8/v0.9-Kette ist seine vollständige Abarbeitung.

## Offene Blöcke

- Rest-Autopsie muß-Klasse (`direction_uncertain` je 1 Strich — die
  ß-Strich-Zerlegung der Referenzen, §7.10 L2-Rest).
- Der **Bestätigungssatz** (A, dann B) als Schlussstein, bevor aus dem
  Dev-Gewinn eine Adoptionsentscheidung jenseits der Routen-Konstanten
  wird (Versiegelung: tintenfolger.md §2.5).
- Fusion „Vier Augen": Orakel-Decke 0,0491 (aug17); der referenzfreie
  Auswähler bleibt bis zum Bestätigungssatz gesperrt.
