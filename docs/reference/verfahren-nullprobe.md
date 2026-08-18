# Verfahrensseite Nullprobe

> **Status (2026-08-18): lebend.** Register-Seite des Verfahrens
> „Nullprobe“ (Konvention: [`verfahren.md`](verfahren.md)).
> Nachzieh-Pflicht: Jede §14-Messung, in der die Nullprobe mitläuft
> (Re-Baselines), ergänzt hier ihre Ledger-Zeile — Optimierungs-Arme
> gibt es für dieses Verfahren per Doktrin nicht.

## Steckbrief

- **Anzeige-Name:** Nullprobe (Glossar „Duell-Namen“).
- **Technisch:** `tools/routeg` — Skelett → Segmentgraph →
  Greedy-Traversierung per Gute-Fortsetzung; eigene Minimalfassung der
  Writing-Order-Recovery (Diaz et al. 2022), weil die MATLAB-Referenz
  hier nicht lauffähig ist (Begründung + Reduktions-Liste:
  `tools/routeg/README.md`).
- **Rolle:** die **prior-freie Kontrolle** (Route G) — sie rät Ordnung
  und Astwahl OHNE den Duktus-Prior; ihre Differenz zur Kette beziffert,
  was der Prior wirklich kauft (architektur.md §2 als Messung statt
  Architektur-Glaube).

## Warum diese Seite kein Versions-Ledger im engen Sinn hat

**Die Kontrolle wird grundsätzlich NICHT optimiert**
(tintenfolger.md §7.6): eine Nulllinie, die mitlernt, ist keine
Nulllinie mehr. Die Nullprobe hat darum bewusst keine Versionen und
bekommt keine Arme; jede Änderung an `tools/routeg`, die über
Bugfixes der Minimalfassung hinausgeht, wäre eine
Doktrin-Entscheidung, kein Arm. Genau das dokumentiert diese Seite —
damit niemand die Lücke im Register für ein Versäumnis hält.

## Ledger (Messungen; Belege in §14)

| Datum | Messung | Ergebnis | §14-Eintrag |
|---|---|---|---|
| aug14 | Kontrolllauf (10er-Dev) | dtw 0,8198 med = 13× Kette; aiou 0,833 (beste Tinten-Deckung — Skelett-Mitte); der Prior-Wert erstmals beziffert | „Route G aug14“ |
| aug17 | Re-Baseline (19er-Dev) | dtw 0,619 med, alle 19 Wörter schlechter als die Kette (Sign 19:0), rel. Median +1092 %; Galoppieren ohne Prior 1,906 | „Re-Baseline aug17“ |

Nebenrolle: ihr Skelettgraph (`tools/routeg/graph.py`) ist der
Wasserweg des Lotsen — Bausteine wandern, die Kontroll-Rolle nicht.
