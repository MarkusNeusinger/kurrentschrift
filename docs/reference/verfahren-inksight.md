# Verfahrensseite InkSight

> **Status (2026-08-18): lebend.** Register-Seite des Verfahrens
> „InkSight" (Konvention: [`verfahren.md`](verfahren.md)).
> Nachzieh-Pflicht: Jeder §14-Eintrag zu einer InkSight-Stufe oder
> -Maßnahme ergänzt hier seine Ledger-Zeile; eine adoptierte Stufe
> aktualisiert „Aktueller Stand".

## Steckbrief

- **Anzeige-Name:** InkSight (Glossar „Duell-Namen"); der
  `text`-Prompt ist Diagnose und von der Duell-Seite genommen.
- **Technisch:** `tools/inksight` — drei Stufen (`prepare` →
  `run_inksight` im isolierten Python-3.11-TF-venv → `to_candidate`),
  Small-p-Checkpoint (Apache 2.0), `derender`-Prompt. Reine
  Messschicht: die Ausgabe erreicht nie `core/`, die DB oder das
  Rendering (Grenze auch der Model-Card-Ethik-Notiz).
- **Rolle:** Route B1 des Duells — das gelernte Verfahren roh als
  Out-of-Distribution-Prüfstein; Duktus-Wahrheit bleibt IMMER beim
  Prior, gelernte Bahnen sind Geometrie-Material.
- **Versionen = T-Stufen:** T0 ist das unadaptierte Modell; eine
  adoptierte Anpassungsmaßnahme (z. B. B2-Tiling) definierte T1.
  Fine-Tuning ist KEINE Option (verworfen, tintenfolger.md §5 — kein
  Trainingscode); der gelernte Nachfolger ist die eigene Route
  „Zögling" (§7.5).

## Aktueller Stand: T0 (2026-08-17)

Zahlen (dev-19, §14 „Re-Baseline aug17", InkSight-Absatz):
**14/19 gescort, 5 failed** am Ein-Punkt-Strich-Kontraktbruch (die
ganze und-Familie + muß-2/die-2 — die Fehlerklasse wandert mit den
Crops) · dtw 0,0951 med (10er-Satz: 0,0956 — konsistent) ·
Retraces systematisch verloren (`retrace_missing` 18, `lift_delta`
+47) · Kreuzungen vergleichsweise sauber. Komplementäre Stärke: die
muß-Klasse klar vor der Kette (0,081/0,097 gegen 0,242/0,234).
**B2-Prüffall bestätigt:** Galoppieren (Crop-Ratio 4,34 >
Trainingsfiltergrenze 4,0) kollabiert flächig — aiou 0,347, beide
Chamfer ~3× Satz-Median, +13 Lifts.

## Ledger (Stufen und Maßnahmen; Belege in §14)

| Datum | Stufe/Maßnahme | Mechanismus | Verdikt | §14-Eintrag |
|---|---|---|---|---|
| aug15 | T0 (10er-Dev) | Small-p roh, `derender`/`text` | gemessen: 0,0956 med = 1,5× Kette; `text` schlechter als `derender`; Retraces verloren | „Route B T0 aug15" |
| aug15 | B1 Best-of-N | Ensemble über Input-Augmentierungen, Ranker gegen die Tinte | verworfen (ehrliches Negativ: Orakel −0,0124 bewiesen, Ranker ordnungs-blind → Rettungsweg „Chor", Welle 3) | „Welle 1 · B1 aug15" |
| aug17 | T0 (19er-Dev) | wie T0, neue Crops | gemessen: Zahlen oben; B2-Prüffall Galoppieren bestätigt | „Re-Baseline aug17" |

## Stehende Maßnahmen (tintenfolger.md §7.4)

B2 Tiling auf w/h ≤ 2 (Welle 2 — hat mit Galoppieren jetzt seinen
gemessenen Probestein) · B3 billige A/Bs (Padding, Kontrast) · B4
InkSight als segmentweise Init des eigenen Fits · B5
Retrace-Rückgewinnung über den Prior (Segment-Sequenz mit
Wiederholung). Bekannte Kontraktbruch-Klasse: Ein-Punkt-Striche
(`status: failed` je Wort — Zeile, nie Exception).
