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

## Aktueller Stand: v2 (2026-08-19) — die marken-endständige Assembly

Formulierung: EDT-Punktdatenterm + Landmark-/Width-Operatoren +
Budget-Veto; als Folger-Aufsatz der re-linearisierende Restart
(`follow.py`, reg→prox) mit Struktur-Wächter (Arm ⑨) — dessen gewachte
Bahn ist die Duell-Kette. **v2 (K-A, §14 `aug19`):** die Assembly
emittiert Diakritika-Striche NACH allen Körper-Strichen
(`HarvestOptions.marks_last` = True; die komponierte Engine-Ordnung,
die die Hand teilt) — eine reine Ordnungs-Änderung, kein Punkt bewegt
sich; sie löste die gesamte unter/muß-Kollaps-Klasse (unter 0,450 →
0,085). Der Marken-Nachfit (A1) bleibt **opt-in** (`--mark-refit`).
Zahlen (dev-19, §14 „Kette K-A `aug19`"-Re-Baseline): dtw 0,0576 med ·
**p90 0,0988** · worst Galoppieren 0,233; bekannte Klassen-Defekte:
das er-Gekritzel in unter als echter Rest (~0,085, versetzter
Karten-Init), Kreuzungs-Höhen-Drift (das/die, §13a), Galoppieren 5
verlorene Kreuzungen, Zacken-Klasse (Ausreißer-Anker im Trace —
i-Punkt-V, p-Nadel; die Statistik-Schicht repariert sie längst, der
Trace zeigt sie absichtlich roh).

**Versionierung:** v2 seit 2026-08-19 (erste adoptierte
Formulierungsänderung). Die abgeschlossenen Gewichts-Arme werden nicht
rückwirkend nummeriert (Konvention Nr. 3).

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
| aug19 | soll-bewusster K0-Wächter | `--structure-guard-soll`: Intervall je Klasse zwischen Init-Budget und Kompositions-Soll | GEMESSEN: 4 von 5 Gates bestehen (7 strikte dev-dtw-Gewinne, aiou nie negativ, dev-Median 0,0576 → 0,0494) — Struktur friert 107 = 107, „strikt besser" scheitert an der runden-ATOMAREN Rückweisung (unter-Protokoll); als sichere Produktions-Bahn dominiert er den zweiseitigen; Rettungsweg zonale Rückweisung (§7.9) | „Wächter als Produktions-Kette aug16“ (Nachtrag `aug19`) |
| aug19 | **K-A marken-endständige Assembly** | `HarvestOptions.marks_last` — Diakritika hinter alle Körper-Striche (reine Ordnungs-Änderung) | **ADOPTIERT als v2** (alle Gates exakt: die vier Kollaps-Wörter −0,12 bis −0,37, alles andere byte-gleich; p90 0,236 → 0,099; der Lotse-Vorsprung gegen v1 erweist sich als Artefakt — gepaart gegen v2 Gleichstand) | „Kette K-A `aug19`“ |

## Stehende v3-Anwärter (Formulierungsänderungen, tintenfolger.md §7.3)

**Zacken-Reparatur im Trace** (neu `aug19`: die Ausreißer-Anker-Klasse
— i-Punkt-V, p-Nadel — mit dem geteilten Detektor
`tools.pairlab.anchors` auch in der TRACE-Schicht reparieren, nach dem
A1-Muster „ändert, was der Trace ZEIGT, nie, was die Ernte MISST";
eigene Pre-Reg) · A2 (SDM + Dichtebewusstheit, Welle 2 — Ziele
Stranding/Doppelpass, NICHT muß/unter) · A3 (Kreuzungen als explizite
Variablen — jetzt mit der das/die-Höhenstapel-Evidenz aus §7.10) ·
A5 (Zwei-Pass-Zwang aus Breiten-Evidenz) · A4 (Barriere statt Veto) ·
A6 (GNC-Schedule). NICHT wieder aufgenommen werden Gewichts-Sweeps
der alten Formulierung — durch ①⑤⑥⑥b⑨ erschöpfend negativ
beantwortet.
