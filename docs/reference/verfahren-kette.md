# Verfahrensseite Kette

> **Status (2026-08-18): lebend.** Register-Seite des Verfahrens „Kette“
> (Konvention: [`verfahren.md`](verfahren.md)). Nachzieh-Pflicht: Jeder
> §14-Eintrag zu einem Kette-Arm (adoptiert oder verworfen) ergänzt hier
> seine Ledger-Zeile; eine adoptierte Formulierungsänderung bumpt die
> Version und aktualisiert „Aktueller Stand“.

## Steckbrief

- **Anzeige-Name:** Kette (Glossar „Duell-Namen“). Owner-Entscheid
  2026-08-16: „Kette+ ist die einzige Kette“ — die Duell-Seite zeigt
  ausschließlich die struktur-**gewachte** Variante.
- **Technisch:** der Stage-B-Kettenfit — `tools/pairlab/chain.py` über
  den Harvest-Codepfad (`tools/laufform/harvest.py --path chain`);
  Duell-Kandidat via `tools/pairlab/follow.py --rounds 0`
  (Byte-Identitäts-Pin) bzw. der `chain`-Provider des Tracebench.
- **Rolle:** ein **Mess-Fit**, kein geborener Tintenfolger — seine
  Tikhonov-Regularisierung zieht absichtlich Richtung Vorlagenform,
  damit die Hand-Statistik robust bleibt (tintenfolger.md §1). Im Duell
  ist er die prior-geführte Referenz-Route (Route A) und in der
  Produktion die Quelle der `traced`-Zeilen.

## Aktueller Stand: v1 (2026-08-17)

Formulierung: EDT-Punktdatenterm + Landmark-/Width-Operatoren +
Budget-Veto; als Folger-Aufsatz der re-linearisierende Restart
(`follow.py`, reg→prox) mit Struktur-Wächter (Arm ⑨) — dessen gewachte
Bahn ist die Duell-Kette. Der Marken-Nachfit (A1) ist adoptiert, aber
**opt-in** (`--mark-refit`), nicht Teil des Duell-Defaults. Zahlen
(dev-19, §14 „Re-Baseline aug17“): dtw 0,0579 med · p90 0,236 ·
worst unter 0,450; bekannte Klassen-Defekte: muß-Klasse (seit `aug19`
als ORDNUNGS-dominiert autopsiert — der verbundene ü-Deckbogen sitzt
bei der Hand am Wortende; Referenz-Eigenschaft, §14
„L2-Rest-Autopsie“), Kreuzungs-Höhen-Drift (das/die, §13a),
Galoppieren 5 verlorene Kreuzungen, unter-Stapel (Init-/Basin-Klasse).

**Versionierung ab hier:** v1 ist der heutige Stand; die Nummer bumpt
nur bei einer ADOPTIERTEN Formulierungsänderung (die A-Kandidaten
unten). Die abgeschlossenen Gewichts-Arme werden nicht rückwirkend
nummeriert (Konvention Nr. 3).

## Ledger (datierte Arme und Entscheide; Belege in §14)

| Datum | Arm/Maßnahme | Ein Knopf / Mechanismus | Verdikt | §14-Eintrag |
|---|---|---|---|---|
| aug14 | Baseline (Freeze-Akt) | Kettenfit gegen die Hand, 10er-Dev | Baseline eingefroren (dtw 0,062 med) | „Baseline aug14“ |
| aug14 | Arm ① λ_prox-Leiter | reg→prox-Gewicht | verworfen (Formulierung v1 des Folgers; Tinten-Zug validiert) | „Arm ① aug14“ |
| aug14 | Arme ⑤+⑥ | overlap · landmark | Overlap freigesprochen; Korrespondenz-Kappe gefunden | „Arme ⑤ + ⑥ aug14“ |
| aug15 | Arm ⑥b | klassenbewusste Korrespondenz | Hypothese bestätigt, keine Adoption | „Arm ⑥b aug15“ |
| aug15 | A1 Marken-Nachfit | Mini-Fit der Marken auf die Restmaske | **adoptiert (opt-in)**, −55 % Marken-Ortsfehler | „Welle 1 · A1 aug15“ |
| aug16 | Arm ⑨ Topologie-Wächter | Struktur-Budget als Veto | Route-A-Fazit: Formulierung am struktur-sicheren Optimum; **gewachte Variante = Duell-Kette** | „Arm ⑨ aug16“ |
| aug16 | Wächter als Produktions-Kette | `structure_guard` als Harvest-Default | GEMESSEN: einseitig vom eigenen Kill verworfen (3 Kreuzungs-Kollapse ungestraft), zweiseitig Pareto-sicher, aber „irgendwo strikt besser“ formal unerfüllbar — Owner-Abwägung (a)/(b)/(c) offen | „Wächter als Produktions-Kette aug16“ |
| aug17 | Re-Baseline 19er-Dev-Satz | — | dev-19-Zahlen oben | „Re-Baseline aug17“ |
| aug19 | A1-Nachmessung dev-19 | dieselbe opt-in Variante, §7.7-Protokoll | Marken-Ortsfehler-Median 0,111 → 0,030 (−73 %), Körper/Struktur byte-neutral — der Welle-1-Gewinn generalisiert | „Welle 1 · A1 aug15“ (Nachtrag) |
| aug19 | soll-bewusster K0-Wächter | `--structure-guard-soll`: Intervall je Klasse zwischen Init-Budget und Kompositions-Soll | vorregistriert; Messung dieser Runde | „Wächter als Produktions-Kette aug16“ (Nachtrag `aug19`) |

## Stehende v2-Anwärter (Formulierungsänderungen, tintenfolger.md §7.3)

A2 (SDM + Dichtebewusstheit, Welle 2) · A3 (Kreuzungen als explizite
Variablen — jetzt mit der das/die-Höhenstapel-Evidenz aus §7.10) ·
A5 (Zwei-Pass-Zwang aus Breiten-Evidenz) · A4 (Barriere statt Veto) ·
A6 (GNC-Schedule). NICHT wieder aufgenommen werden Gewichts-Sweeps der
alten Formulierung — durch ①⑤⑥⑥b⑨ erschöpfend negativ beantwortet.
