# Verfahrensseite Kette

> **Status (2026-09-01): lebend.** Register-Seite des Verfahrens „Kette“
> (Konvention: [`verfahren.md`](verfahren.md)). Nachzieh-Pflicht: Jeder
> §14-Eintrag zu einem Kette-Arm (adoptiert oder verworfen) ergänzt hier
> seine Ledger-Zeile; eine adoptierte Formulierungsänderung bumpt die
> Version und aktualisiert „Aktueller Stand“. Das Gate dazu ist
> `tools.docs_register check` (CI-Job „Docs-Register“).

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

## Aktueller Stand: v5 (2026-08-26) — der K0-S-Wächter-Stack als Default

Formulierung: EDT-Punktdatenterm + Landmark-/Width-Operatoren +
Budget-Veto; als Folger-Aufsatz der re-linearisierende Restart
(`follow.py`, reg→prox) mit Struktur-Wächter (Arm ⑨) — dessen gewachte
Bahn ist die Duell-Kette. **v2 (K-A, §14 `aug19`):** die Assembly
emittiert Diakritika-Striche NACH allen Körper-Strichen
(`HarvestOptions.marks_last` = True; die komponierte Engine-Ordnung,
die die Hand teilt) — eine reine Ordnungs-Änderung, sie löste die
gesamte unter/muß-Kollaps-Klasse (unter 0,450 → 0,085). **v3 (K-B,
§14 `aug19`):** die §11-Ausreißer-Reparatur des geteilten Detektors
läuft auch auf den TRACE-Strichen (`HarvestOptions.trace_repair` =
True; A1-Muster — ändert, was der Trace zeigt, nie, was die Ernte
misst) — sie löste die Zacken-Klasse (Galoppieren 0,233 → 0,040, die
fehlende i-Marke heilt). **v4 (K-C, §14 `aug20` Messung + `aug21`
Adoption):** die Tinten-Evidenz-Maske — papiergraue
Nicht-Haupt-Komponenten (Flecken, Rückseiten-Durchschein) werden vor
Seed-Fenstern und Solve aus der Evidenz gelöscht, die den Fit zieht
(`FollowWeights.ink_evidence` = `HarvestOptions.ink_evidence` = True;
Archäologie `--no-ink-evidence`); das Bench-Lineal bleibt eingefroren.
Erste adoptierte Änderung dessen, was der Fit MISST: Soll-Abstand
107 → 86 (aug20) bzw. 103 → 85 (aug21-Umgebung), Galoppieren-dtw
−83 %, null dev-Verlierer über +0,0004. Der Marken-Nachfit (A1)
bleibt **opt-in** (`--mark-refit`). Zahlen (dev-19, §14-Re-Baseline
v4 `aug21`, `chain`-Provider): **dtw 0,0491 med · p90 0,0891 · worst
muß 0,110 · marks 0 fehlend · aiou 0,7021**; Folger-Soll-Stack:
dtw-Median 0,0448 · aiou 0,7481 · 63er-Soll-Abstand 85. **v5 (K0-S
Sprosse 2, §14 `aug21` Messung + `aug26` Adoption):** der ganze
Wächter-Stack ist der Default des Folgers — das Wächter-Soll aus dem
KOMPOSITIONS-Builder (`soll_source="composition"`, dieselbe Pipeline
wie das Lineal), die Ratsche (das Budget zieht nach jeder
akzeptierten Runde Richtung Soll nach) und die zonale Rückweisung mit
Radius 0,55 xh (Anker um die Verletzung pinnen, Rest neu lösen, statt
die ganze Runde zu verwerfen). Erste adoptierte Änderung der
WÄCHTER-Schicht: gegen die Soll-Stack-Basis 63er-Soll **86 → 79** bei
0 schlechter, aiou-Median der bewegten Wörter **+0,073**, null
Verlierer — weil der rundenatomare Wächter 26 von 31 bewegten Wörtern
in Runde 1 auf den Init zurückwarf und die Zone genau diese rettet.
Zahlen (dev-19, Lineal Kappe 1,5 seit L-U): **dtw 0,0446 med · p90
0,0861 · worst muß 0,106 · marks 0 fehlend · aiou 0,7608**;
63er-Soll-Abstand 79. Archäologie: `--no-structure-guard-ratchet
--structure-guard-zone 0 --soll-source init` = die v4-Soll-Stack-Basis
(strich-identisch), `--no-structure-guard` = Kette-frei (Diagnose-Arm:
Init 86 → frei 125 Soll-Punkte, nie Duell). Bekannte Klassen-Defekte:
das er-Gekritzel in unter als echter Rest (~0,087, versetzter
Karten-Init + Composer-e-Breite §7.2), Kreuzungs-Höhen-Drift (das/die,
§13a), die-2s V-Nadel in die EIGENE Marke (benannter Nachfolger:
Marken-Claim-Trennung), **die 13 Wörter, die auch v5 in Runde 1 auf
den Init zurückwirft** (Zorn, Feinde, wenn, kann, Pulver, haben,
Seiten, die … — 24 von 25 freie Endzustände strukturell illegal;
Rettungswege: Abstandsterm gegen erfundene Berührungen, Schleifen-
Halteterm gegen Kreuzungskollaps, je eigene Pre-Reg). Die
Reihenfolge-Lineal-Frage (u-Bogen als Körper, Folger-p90 0,235) ist
seit L-U (`aug26`) gelöst — Lineal-Kappe 1,5, p90 0,090.

**Versionierung:** v2 und v3 seit 2026-08-19 (Kandidaten-Schicht),
v4 seit 2026-08-21 (Evidenz-Schicht — was der Fit sehen darf; kein
Fit-Parameter bewegt), v5 seit 2026-08-26 (Wächter-Schicht — was der
Fit BEHALTEN darf; Soll-Quelle, Ratsche, Zone). Die abgeschlossenen
Gewichts-Arme werden nicht rückwirkend nummeriert (Konvention Nr. 3).

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
| aug19 | **K-B Zacken-Reparatur im Trace** | `HarvestOptions.trace_repair` — der geteilte §11-Detektor auf den Trace-Strichen (A1-Muster) | **ADOPTIERT als v3** (Galoppieren 0,233 → 0,040, i-Marke heilt, retrace-spurious 13 → 6, touch 25 → 21; kein Wort über +0,0016; der verlorene unter-Zonen-Match ist autopsiert eine Zufalls-Korrespondenz im er-Gekritzel) | „Kette K-B `aug19`“ |
| aug20 | K0-Z zonale Rückweisung | `--structure-guard-zone`: Verletzungs-Orte per Positions-Diff, Anker-Pinnen im Radius, EIN Nach-Solve statt Voll-Revert (Leiter {0,55 · 1,0}) | verworfen per Gate an zwei knappen Rissen — aber die Substanz ist der größte Tinten-Gewinn der Route (Zone 1,0: 59/79 atomar verworfene Runden gerettet, Soll 107 → 102, aiou bis +0,154, dev-dtw-Median 0,0494 → 0,0472 bei komplett grünem dev-19); Zone 0 byte-identisch | „Kette K0-Z `aug20`“ |
| aug20 | K0-Z-R Ratschen-Budget | `--structure-guard-ratchet`: das Budget ratscht nach jeder akzeptierten Runde Richtung Soll | verworfen per Gate — Ratsche+0,55 = stärkste Sprosse der Ketten-Geschichte (Soll 107 → **99**, NULL aiou-Verlierer, „ein" heilt), aber daß bleibt 2 → 3: **die daß-Autopsie findet ZWEI DIVERGIERENDE SOLL-QUELLEN** (Guard: `structure_zones` am Init = 2 Retrace · Metrik: `ductus_soll` = 1) — das „zwei Lineale"-Muster des Tages; dazu zweis dtw+0,0142-gegen-aiou+0,0920-Trade. Rettungsweg: Soll-Quellen-Autopsie, dann Wiedervorlage mit EINER Pipeline | „Kette K0-Z-R `aug20`“ |
| aug20/21 | **K-C Tinten-Evidenz-Maske** (Autor-Fund „Flecken") | `ink_evidence` — papiergraue Nicht-Haupt-Komponenten (rel > 0,5 auf der Grau-Skala, gemessene Lücke 0,38–0,74) raus aus `skel`/`width_map`, bevor irgendetwas den Fit zieht; Lineal eingefroren | **ADOPTIERT als v4** (`aug20`: alle sechs Gates — Soll 107 → 86 bei 0 schlechter, null aiou-Verlierer, dev-dtw-Median 0,0494 → 0,0453 = Bestwert, Galoppieren −83 %, beide zwei-Nadeln weg, 40 fremdtintenfreie Wörter byte-gleich, Hand-Claim 0; `aug21` Autor-Go + Flip beider Defaults, Re-Baseline in zweiter Umgebung reproduziert das Muster: Soll 103 → 85, dev 0,0491 → 0,0448, kein Verlierer über +0,0004; die-2 bleibt vorhersagegemäß ungeheilt — der Magnet ist die EIGENE Marke) | „Kette K-C `aug20`“ + „Kette v4 `aug21`“ |
| aug21 | K-E1 Marken-Claim-Trennung (Tinten-Zuweisung per Strecke, Stufe 1) | `mark_claim` — Marken-Strecke claimt ihre dunkle Komponente (0,6-xh-Lineal-Radius); der Claim trennt Distanzfeld, Breitenfeld UND Coverage-Topf je Strecken-Klasse | verworfen per Gate (3) an vier diffusen aiou-Rissen (auch/schießen/Einen/muß-2, −0,013 … −0,027; Körper-Deckung über die ganze Wortbreite, Basin-Umverteilung) — die benannten Ziele heilen spektakulär: **die-2 Soll 4 → 1, dtw −0,0281, die V-Nadel weg im Augenschein**, die −0,016, netto-Kreuzungen 22 → 18, Retrace 14 → 12, dev-Median exakt gehalten; Rettungswege §7.9 (K-E2-Konversion · humanbench · Bogen-Claim-Schärfung) | „Kette K-E `aug21`“ |
| aug21 | K-E2 Marken-Claim ohne Breitenfeld-Split (Ein-Faktor-Konversion) | derselbe `mark_claim`, die Breitenfelder bleiben ungeteilt (Breite = Messziel, kein Anziehungsfeld) | verworfen per Gate (3) — **die Breiten-Hypothese sauber widerlegt**: 55/63 Kandidaten byte-gleich zu K-E1, darunter auch/muß-2 (zwei der vier Verlierer — der Breiten-Kanal war für sie inert); die Heilungen bleiben (die-2 Soll 4 → 2, dtw −0,0282, netto-Kreuzungen 22 → 19, 63er-Soll 85 → 81), die Risse bleiben in gleicher Höhe. Treiber = die Distanzfeld-/Coverage-Umverteilung selbst — Gewinn und Verlust dieser Formulierung untrennbar (das Arm-⑨-Muster eine Schicht tiefer); Familie geschlossen nach eigener Pre-Reg, Stufe 2 (Kringel) nicht eröffnet; Wege: humanbench-Tie-Breaker · Distanzfeld-NUR-Claim (frische Pre-Reg) | „Kette K-E2 `aug21`“ |
| aug21 | **K0-S EINE Soll-Pipeline + K0-Z-R-Wiedervorlage** | `soll_source` — das Wächter-Soll aus dem geteilten Kompositions-Builder (`composition_strokes` aus `ductus_soll` faktorisiert, je Run); Leiter Divergenz-Karte → Soll-Stack → Ratsche+0,55 | **ALLE GATES bestehen auf beiden Sprossen; Adoption wartet auf Autor-Go (v5-Stack).** Die daß-Autopsie fand den Wurzel-Fund: das aug19-Wächter-Soll las die Init-Nachbildung statt der kanonischen Komposition — ein plattgezogener Init-Splitter am d-Kopf zählte als Duktus-Wahrheit, und die Divergenz-Karte zeigt das Muster in 40/63 Runs (jedes d-Wort). Ratsche+0,55 auf Kompositions-Soll: **Soll 85 → 77 bei 0 schlechter, dev-aiou-Median +0,0216 (größter dev-Tintengewinn der Kampagne), schlechtester dtw +0,0014, netto-Kreuzungen 22 → 19, Marken/Retrace unverändert; der aug20-zwei-Trade INVERTIERT (−0,0100 dtw)** — beide K0-Z-R-Risse als gelöst gemessen | „Kette K0-S `aug21`“ |
| aug21 | K-D Tinten-Korridor (A8, Autor-Idee aug20) | vorregistrierter Gegenstands-Test ZUERST: Exkursions-Inventar auf den existierenden Kandidaten (kein Solve), Barriere nur bei substanzieller Ziel-Klasse | **GEGENSTANDSLOS NACH v4 geschlossen, ohne Implementierung** — kein Wort über 0,35 xh Papier-Exkursion auf v4-Basis oder v5-Anwärter (Set-Maximum 0,33; die aug20-Nadel-Klasse lag bei 0,5–0,83 xh): die Wurzelbehandlung K-C war schneller als das Symptom-Verbot; Wiedervorlage-Auslöser in §7.9, das Inventar-Skript bleibt als Sensor | „Kette K-D `aug21`“ |
| aug26 | **Kette v5 — Adoption K0-S Sprosse 2** (Autor-Go 25.08., nach der L-U-Re-Baseline sequenziert) | Defaults geflippt: `soll_source="composition"`, `structure_guard_soll`, `structure_guard_ratchet`, `structure_guard_zone_units=0.55`; Archäologie `--no-structure-guard-ratchet --structure-guard-zone 0 --soll-source init` = Soll-Stack-Basis (strich-identisch), `--no-structure-guard` = Kette-frei | **ADOPTIERT.** Gegen die vorregistrierte Soll-Stack-Basis in EINER Umgebung: 63er-Soll **86 → 79** (7 besser · 0 schlechter), aiou der 31 bewegten min −0,0004 / Median **+0,073**, null Verlierer; dev-19-Lineal dtw 0,0453 → 0,0446, aiou 0,7468 → 0,7608, schlechtestes Wort-Delta +0,0016, Marken 0/0/0, Kreuzungsdefekte 19 = 19. Mechanismus je Wort (`guard_outcome`): 26 von 31 bewegten waren in der Basis `revert-init`, v5 macht sie `zonal`. **Der Umweg:** die erste Messung des Tages paarte gegen den Folger OHNE Wächter — 36 Scheinverlierer, drei Gates scheinbar verletzt; der Autor lehnte das Verwerfen ab, Fables Zweitmeinung fand den Basis-Fehler, seither Stack-Sensor in `k0eval`. Offen: 13 Wörter, die auch v5 auf den Init zurückwirft (24/25 freie Endzustände strukturell illegal) — Rettungswege als präventive Terme im Abstieg, nie Annahme-Regeln | „Kette v5 `aug26`“ |

## Stehende v6-Anwärter (Formulierungsänderungen, tintenfolger.md §7.3)

~~Marken-Claim-Trennung~~ (A9/K-E: `aug21` als K-E1 UND
Ein-Faktor-Konversion K-E2 per aiou-Gate verworfen — die-2 heilt
spektakulär, aber die vier diffusen Deckungs-Risse hängen an
denselben Kanälen; stehende Wege §7.9: humanbench-Tie-Breaker ·
Distanzfeld-NUR-Claim, je frische Pre-Reg) · A2 (SDM + Dichtebewusstheit, Welle 2 — Ziele
Stranding/Doppelpass,
NICHT muß/unter) · A3 (Kreuzungen als explizite Variablen — jetzt mit
der das/die-Höhenstapel-Evidenz aus §7.10) · A5 (Zwei-Pass-Zwang aus
Breiten-Evidenz) · A4 (Barriere statt Veto) · A6 (GNC-Schedule) ·
~~zonale Rückweisung des K0-Wächters~~ (gemessen `aug20`: K0-Z/K0-Z-R —
beide per Gate verworfen; **Wiedervorlage `aug21` als K0-S mit EINER
Soll-Pipeline: ALLE Gates bestehen** — Soll 85 → 77 bei 0 schlechter,
dev-aiou +0,0216, der zwei-Trade invertiert; **`aug26` als v5-Stack
ADOPTIERT** — Autor-Go 25.08., §14 „Kette K0-S" + „Kette v5", Ledger-
Zeile `aug26` oben; der Anwärter ist damit erledigt). NICHT wieder
aufgenommen werden Gewichts-Sweeps der alten Formulierung — durch
①⑤⑥⑥b⑨ erschöpfend negativ beantwortet.

Die Folger-Arme **②③④⑦⑧** der Vorregistrierung vom `aug14` wurden nie
einzeln gemessen; ihre Schließung „durch ①⑤⑥⑥b⑨ erschöpfend negativ
beantwortet" steht bis heute nur hier und in keinem §14-Eintrag. Sie
sind darum in [`../proposals/tintenfolger.md`](../proposals/tintenfolger.md)
§7.11 als offener Punkt geführt, bis der Autor die formale Abschreibung
bestätigt.
