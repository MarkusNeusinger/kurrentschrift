# Verfahrensseite Übergänge

> **Status (2026-09-09): lebend.** Register-Seite der Route „Übergänge“
> (Konvention: [`verfahren.md`](verfahren.md)), angelegt auf
> **Autor-Entscheid A43 vom 2026-09-09**: Seit `aug29` misst die Kampagne
> Übergänge-Arme, ohne dass eine Verfahrensseite sie geführt hätte — die
> Ablage der Runde 7 (#582) hat das als Befund benannt. Nachzieh-Pflicht:
> Jeder §14-Eintrag der Route „Übergänge“ (adoptiert oder verworfen)
> ergänzt hier seine Ledger-Zeile; eine Adoption aktualisiert zusätzlich
> „Aktueller Stand“ und die Stand-Spalte in [`verfahren.md`](verfahren.md).
> Das Gate dazu ist `tools.docs_register check` (CI-Job „Docs-Register“),
> das diese Route seit demselben PR kennt — ein J- oder S-Eintrag ohne
> Ledger-Zeile schifft nicht mehr.

## Steckbrief

- **Anzeige-Name:** Übergänge — und ausdrücklich **keine Duell-Route.**
  Kette, Lotse, InkSight und Nullprobe treten gegeneinander an, um der
  Tinte eines geschriebenen Wortes zu folgen; die Übergänge sind die
  Schicht darunter, auf der alle vier aufsetzen: die Join-Grammatik der
  Komposition (`../proposals/tintenfolger.md` §7.2, „der Top-Hebel“). Sie
  bekommt trotzdem eine Verfahrensseite, weil ihre Arme adoptierte
  DEFAULTS bewegen und damit jede `/write/word`-Antwort.
- **Technisch:** `core/compose.py` — die generierten Verbinder zwischen
  zwei Buchstaben und die Klassen, die davon ausgenommen sind
  (`CAP_RESTART_BASES`, `EXIT_TRIM_EXCLUDED_BASES` …). Die Schalter von
  `compose_word`: `exit_trim` (Default **True** seit A37),
  `apex_handover` und `stem_depart` (aus, A36), `seam_negotiation` (aus,
  zweimal gefallen). Gemessen wird mit `tools/wordbench` (Wort- und
  Paar-Lineal, Naht-Sensor `seam.py`), `tools/pairlab` (Dissektion über
  `prodconn`, Spannen über `spanmeas`) und `tools/humanbench` (blinde
  Wortrunden).
- **Rolle:** Die Doktrin ist „Übergänge sind Konsequenz, keine Daten“
  (Glossar): ein Übergang wird aus `exit`/`entry`-Tangenten und
  Kopplungshöhe ERZEUGT, nie als Paar autoriert
  (`../concepts/architektur.md` §4). Ein Arm dieser Route ändert deshalb
  immer eine REGEL für eine ganze Klasse, nie eine Stelle — Paar-Overrides
  sind der letzte Ausweg, nicht das Werkzeug.
- **Nachbar-Dokumente:** der ältere Paar-Befund
  [`../proposals/uebergaenge-befund.md`](../proposals/uebergaenge-befund.md)
  (Befund-Journal vom 2026-07-11: Platzierung dominiert, Klassen statt
  Paare) und die drei Sensoren, die aus dieser Route hervorgegangen sind
  — Naht-Winkel `seam_deg`, `dspan` (S1) und der Unstetigkeits-Sensor S2.
  Alle drei sind reine Report-Spalten; kein eingefrorenes Lineal wurde für
  sie geändert.

## Warum diese Seite keine Versionsnummern trägt

Die Arme heißen seit `aug29` **J1 … J6** (Regel-Arme) und **S1/S2**
(Sensoren), dazu die Korb-Runde `aug30` aus dem Auftragskorb des Autors.
Konvention Nr. 3 in [`verfahren.md`](verfahren.md) verbietet die
rückwirkende Umnummerierung, also bleiben sie unter diesen Namen. Der
**Stand** der Route ist darum keine Versionsnummer, sondern die Menge
ihrer adoptierten Regeln — das, was ein Bench-Lauf mit committeten
Konstanten produziert.

## Aktueller Stand (2026-09-09): zwei adoptierte Regeln, drei Schalter aus

**Adoptiert: der Austritts-Trim** (`exit_trim`, Autor-Entscheid **A37**
vom 2026-09-06). Der Verbinder beginnt erst dort, wo die
Buchstaben-Richtung mit der Sehne zum Kopplungspunkt übereinstimmt
(`EXIT_TRIM_WINDOW` 0,05 xh, `EXIT_TRIM_TOL_DEG` 3,0); der Stumpf davor
fällt weg. Zahlen auf UNVERÄNDERTER Wurzel, also gepaart (§14 „Übergänge
J4 `sep06`“, Nachtrag „Adoption“): **Wörter 0,108444 → 0,109026, Paare
byte-gleich**, `seam_dep_median` +7,59 → **−0,70** (absolut 12,67 →
2,30), `gleichzug_doublings` 14 = 14; Golden deklariert neu gebacken.
Das Wort-Lineal steigt bewusst — die blinde Runde 5 ging 34 : 2 für den
Trim, und der ganze Lineal-Verlust sitzt in genau der Klasse, in der das
Auge 26 : 2 dagegen entscheidet. `EXIT_TRIM_MIN_KINK_DEG` bleibt 0,0
(die Verengung wurde in derselben Runde gemessen und verworfen). Die
Adoptions-Zahlen stehen auf den Wurzeln `eaa195aa7c84…` /
`0fbde2d72b64…`; die aktuelle Headline ist seit der `sep07`-Re-Baseline
der REFERENZ (Komma-Ausschluss, Wort-Wurzel `ccb036a5eb20…`, Paar-Wurzel
unangetastet) **Wörter 0,108153 · Paare 0,148236** — dieselbe Regel,
eine andere Referenz-Tinte (§14 Headline-Ledger; die Headline selbst
wohnt an ihrer einen Stelle in
[`qualitaetsmetrik.md`](qualitaetsmetrik.md)).

**Adoptiert: B ohne Restart** (`aug30`, Korb #8). Das B verlässt
`CAP_RESTART_BASES`, weil sein autorisierter Duktus auf Mittellinienhöhe
in einem steigenden Abgang endet; der Join ist wieder die normale
Kleinbuchstaben-Grammatik ab dem Duktus-Ende. Zahlen (§14 „Übergänge
Korb-Runde `aug30`“): Wörter **0,106400 unverändert** — kein Abb.-19-Wort
enthält ein gebundenes B —, Paare 0,146580 → 0,148467; die Wurzel dieser
Messung ist **undeklariert** (stehender Autorenschritt,
`../proposals/tintenfolger.md` §7.11).

**Aus, per Entscheid oder Gate.** `apex_handover` und `stem_depart`
bleiben aus (Autor-Entscheid **A36** vom 2026-09-05 nach Runde 6: alle
Gates grün, das Auge trotzdem 20 : 1 für die Basis).
`seam_negotiation` bleibt aus — der Arm ist zweimal gefallen, `sep06` an
Gate (c) und `sep08` am Auge; der engere Arm J6b wurde per
Vorregistrierung nicht eröffnet.

**Offen.** Die Rettungswege der drei Negative stehen in
[`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) §7.9, die
noch nicht vorregistrierten Arme in §7.11 (die J4-Konversionen, die zwei
J5-Konversionen, die vier J6-Konversionen). Fällig aus der A37-Adoption
bleibt der S2-Bezug: die S2-Zahlen beschreiben die Komposition VOR dem
Trim und sind dort korrekt abgelegt.

## Ledger (datierte Arme und Entscheide; Belege in §14)

| Datum | Arm/Maßnahme | Ein Knopf / Mechanismus | Verdikt | §14-Eintrag |
|---|---|---|---|---|
| aug29 | J1 Prior-Landerichtung | die Landerichtung des Verbinders aus dem Duktus-Prior statt aus der Kopplungshöhe (Korb #7, t nach n) | nicht adoptiert: (a) grün mit −0,0010, (c) rot — `ALIGN_MAX_ENTRY_Y` sperrt das t | „Übergänge J1 `aug29`“ |
| aug29 | J2 Anstrich-Verlängerung in den Schaft | der Anstrich läuft in den Schaft des Folgebuchstabens hinein | verworfen: +0,0041, und die Dissektionen zeigen, dass die Hand auf Fußhöhe ankommt | „Übergänge J2 `aug29`“ |
| aug29 | J3 tiefe Schaft-Kopplung (zweiter Arm zu Korb #7) | Kopplung tiefer am Schaft statt am Kopf | nicht adoptiert: (d) rot, `dconn` in 7/7 schlechter — der Haken ist die ZEILE, nicht der Join (t-Kopf 104° gegen 37°) | „Übergänge J3 `aug29`“ |
| aug30 | **Korb-Runde: B verlässt die Restart-Klasse** (Korb #8) + St-Ligatur (Korb #9) | `CAP_RESTART_BASES` ohne B — der Join ist ab dem Duktus-Ende wieder die normale Kleinbuchstaben-Grammatik | **ADOPTIERT** (Stufe `join_rule`): Wörter 0,106400 unverändert, Paare 0,146580 → 0,148467; beide H2-Sensoren des Drills werden besser (`doff` 0,130 → 0,095, `dconn` 0,499 → 0,344), während das Pixel-Lineal den höher liegenden Bogen bestraft. St bleibt Autorenfall (Wizard-Nachfahren) | „Übergänge Korb-Runde `aug30`“ |
| sep02 | **J4 Austritts-Kollinearität** (`exit_trim`) | der Verbinder beginnt erst dort, wo die Buchstaben-Richtung mit der Sehne zum Kopplungspunkt übereinstimmt; der Stumpf davor fällt weg | verworfen an Gate (b), 4 von 5 Gates grün: Wörter −0,000535, `seam_dep` +12,52 → −1,39 — aber `dconn` fällt nur in 20 % statt der geforderten 60 %. Der Fund darunter: `dconn` kann über eine Naht, die die Grenze zwischen Buchstabe und Verbinder VERSCHIEBT, konstruktiv nicht urteilen | „Übergänge J4 `sep02`“ |
| sep02 | J4b enge Klasse (POST-HOC) | derselbe Trim, nur auf Joins mit ≥ 20° Knick | verworfen: der Schnitt rettet den Arm nicht — `dconn` 43 %, `seam_dep` der Klasse nur +8,02; drei Rettungswege in §7.9 | „Übergänge J4b `sep02`“ |
| sep04 | **J5 Tafelform-Klassenregel** (Autor-Entscheid A4): Apex-Übergabe + d-Säulenabgang | `apex_handover` (B-seitige Chart-Stumpf-Regel für den langen ungeschlungenen Anstrich t/ſ/k **und ß**) · `stem_depart` (der d-Auslauf als Generator) | gemessen: **Säulenabgang alle Gates grün** (−0,000100 / −0,001441, Abgang 1,139 → 0,945, 10/10 + 8/8 im Platten-Band) — Adoption war damit Autor-Ja; **Apex-Übergabe verworfen** an zwei Gates (+0,001808 / **+0,002420**, Zacken 13 → 17; die Verengung auf ß/ſſ macht ihn RÖTER, 3 : 8). Golden unberührt, Runde 6 ungerichtet vorregistriert. `r` passt messbar nicht und bleibt Autorenfall | „Übergänge J5 `sep04`“ (Vorregistrierung + gemessen) |
| sep04 | **S1 `dspan`** (ausdehnungs-normierte Formdistanz) | Rettungsweg 2 des J4-Negativs: gemeinsamer Abschnitt statt Start-Ausrichtung, damit ein verschobener Naht-Ort das Maß nicht mehr trägt | **Sensor validiert, J4 bleibt verworfen**: Δ`dspan` +0,0036 (Gate ≤ 0,010), Fallquote 48,8 % (Gate ≥ 40 %) gegen 19,8 % roh und 51 % handbereinigt — die 60 % des J4-Gates erreicht auch die saubere Lesung nicht | „Übergänge S1 `sep04`“ (Vorregistrierung + gemessen) |
| sep04 | P-Spiegel: pairlab misst wieder den Produktions-Verbinder *(Werkzeug-Re-Baseline, kein Arm)* | `tools/pairlab/prodconn.py` ruft den Composer selbst auf, statt den eingefrorenen Spiegel `analyze._generate_connector` zu messen | Audit-Befund 18 beziffert und behoben: 89 von 248 Nähten wichen ab (Median 0,0562 xh, Majuskeln 1,0365), `gen_chamfer` 0,0434 → 0,0392. Der Kette-Init bleibt auf dem eingefrorenen Spiegel (Autor-Frage) | „Übergänge P-Spiegel `sep04`“ |
| sep04 | J4 Wortrunde als benannter Rettungsweg (Pre-Reg) | Rettungsweg 3 zum `dconn`-Negativ: das Auge statt des Sensors, blinde Wortrunde nach `menschliche-bewertung.md` | vorregistriert; auf der LF11-Wurzel neu vermessen (`seam_dep` +7,99 → +0,02, Wörter +0,000248 mit gedrehtem Vorzeichen, Paare byte-gleich). **Runde gefahren `sep06`** — Ergebnis in der Zeile „J4 Runde 5“ unten | „Übergänge J4 `sep04`“ |
| sep05 | **J5 Runde 6 geurteilt** | blinde Wortrunde, Basis gegen `apex_handover` + `stem_depart` bei gepinnter Platzierung | **ehrliches Negativ · Autor-Entscheid A36:** Basis 20 : Kandidat 1 von 21 entschiedenen (4,8 % gegen ≥ 60 %), je Klasse `apex` 1/12 und `stem` **0/7 — bei ALLEN grünen Gates**; 12/12 Nullproben richtig erkannt, aber 4 < 6 Wiederholungspaare, also kein Adoptionsanspruch. Das Auge verwirft, was das Lineal belohnt (die 5 Apex-Gewinner des Wort-Lineals gehen 5 : 0 an die Basis). Gemessener Grund: die Übergabe ist auf 1,67–1,84 xh schnurgerade (Pfeilhöhe 0,001–0,002 xh) statt den Anstrich-Bogen zu tragen. **A36: `stem_depart` wird NICHT Default**, der angekündigte Golden-Bake ist gegenstandslos | „Übergänge J5 `sep05`“ |
| sep06 | **S2 Unstetigkeits-Sensor** | `cont_*` — Knick, Wackler und Bogen-Verlust an der Naht; Fenster aus der FEDER (halbe/eine/zwei Federn 0,0725 · 0,145 · 0,29), θ = arcsin(0,2) = 11,537°, federunabhängig | **validiert; kein Lineal geändert.** Alle fünf Gates bestehen, aber keine EINZELNE Spalte ist der Richter: N1/N2 exakt, P1 `naht-stark` `kink_max_deg` 36,89 → **27,86** bei 28/28 fallendem `kink_count`, P2 `naht-schwach` nur 17 statt 24 von 29 Wörtern bewegt, P3 `apex` `bow_join` 0,0066 → **0,0034 in 12/12**. Ehrliche Hälfte: `bow_join` fällt in BEIDEN Runden, hätte Runde 6 also allein falsch entschieden | „Übergänge S2 `sep06`“ (Vorregistrierung + gemessen) |
| sep06 | **J6 Nahtverhandlung** (`seam_negotiation`) | die Autorenregel vom 2026-09-06 in Geometrie: Buchstabe und Verbinder einigen sich am Nahtpunkt auf den Kompromisswinkel (zirkulärer Mittelwert über 0,05 xh) und drehen beide dorthin — der Buchstabe höchstens 8° über 0,3 xh, der Verbinder den Rest; über 45° Uneinigkeit bleibt die Regel weg. Der Nahtpunkt ist der Drehpunkt, also bewegt sich keine Kopplungshöhe | **ehrliches Negativ, Gate (c) rot.** Die Naht ist zu: über alle 240 Nähte fällt der Betrags-Median des Abgangs 2,67 → **0,01°** und der Ankunft 10,80 → **0,01°**, keine verlässt das 3°-Band. Gefallen an den Verdopplungen der Paare 3 → 5, zurechenbar auf `dp`/`ds`, wo der Verbinder die 32,9° bzw. 31,9° tragen muss, die der 8°-Deckel dem Buchstaben verwehrt. Nebenbefund mit Adressat nach A37: **J6 löst die Austrittsseite OHNE den Trim und billiger** — die beiden Regeln sind Alternativen, keine Ergänzungen | „Übergänge J6 `sep06`“ (Vorregistrierung + gemessen) |
| sep06 | **J4 Runde 5 geurteilt** | dieselbe blinde Wortrunde, Basis gegen `exit_trim` bei gepinnter Platzierung | **Kandidat 34 : Basis 2** von 36 entschiedenen (94,4 % gegen ≥ 60 %), unentschieden 42,9 % gegen ≤ 25 % — `adopt: false` an der Tie-Schranke, klassenweise löst es sich auf: `naht-stark` 26 : 2 bei **9,7 %** Ties, `naht-schwach` 8 : 0 bei 72,4 % (die Klasse, für die die Pre-Reg Unsichtbarkeit beschrieben hatte). Instrument sauber (3/3 Kontrollwörter, 10/12 gleicher Arm bei 12 ≥ 6 Paaren). **Der ganze Lineal-Verlust sitzt in der starken Klasse** (+0,036888 gegen −0,000262). Klassenregel `exit_trim_min_kink_deg` in derselben Runde gemessen und verworfen: sie reichert an, TRENNT aber bei keiner Schwelle. Adoption damit Autor-Entscheid (LF11-Präzedenz) | „Übergänge J4 `sep06`“ |
| sep06 | **J4 Adoption — `exit_trim` wird Default** (Autor-Entscheid A37) | `compose_word(exit_trim=True)`; die Messwerkzeuge tauschen `--exit-trim` gegen `--no-exit-trim`, ein Lauf ohne Flags misst also, was die Produktion schreibt | **ADOPTIERT · deklarierte Re-Baseline** (Wörter + Golden). Gepaart auf unveränderter Wurzel: Wörter 0,108444 → **0,109026**, Paare **byte-gleich**, `seam_dep_median` +7,59 → **−0,70** (absolut 12,67 → 2,30), Verdopplungen 14 = 14; Golden neu gebacken (10 der 11 Wörter, kein Draw-Item mehr oder weniger). **S2 stimmt unabhängig zu**, am selben Tag auf der UNGETRIMMTEN Komposition abgenommen: `cont_kink_total` 402 → **337**, `cont_bow_join_median` 0,0091 → **0,0042** (Report-Spalte, kein Gate). Die Kette ist per Messung ausgenommen (Kompositions-Soll 0 von 126) | „Übergänge J4 `sep06`“, Nachtrag „Adoption“ |
| sep08 | **J6 Runde 7 geurteilt** | blinde Wortrunde: die ausgelieferte Produktion (A37, Trim an) gegen denselben Stapel plus Nahtverhandlung | **ehrliches Negativ zum zweiten Mal; J6b nicht geöffnet.** Basis 14 : Kandidat 9 von 23 entschiedenen (39,1 % gegen ≥ 60 %), unentschieden **40 von 63 = 63,5 %** gegen ≤ 25 %, und klassenweise löst sich NICHTS auf (`naht-stark` 9 : 10 bei 34,5 % Ties, `naht-schwach` 0 : 4 bei 85,7 %, `nullprobe` 6/6 richtig). Instrument sauber: 12 Paare, 10/12 gleicher Arm, und die 7 Seiten-Übereinstimmungen SIND die 7 Doppel-Ties. **Der Grund ist Dosis, nicht Richtung:** der Arm bewegt die Zeichnung um 0,0221 xh im Median gegen den 0,1186-Boden der starken Klasse aus Runde 5. Die Vorregistrierung lizenzierte J6b nur bei ≥ 60 %, also bleibt auch der engere Arm zu. Autor wörtlich: „nicht besser nur bischen weniger wellen mal da oder dort“ | „Übergänge J6 `sep08`“ |

## Stehende Arme (`../proposals/tintenfolger.md` §7.9/§7.11)

Die offenen J4-Konversionen (die Ankunftsseite ist seit `sep06` von J6
mitgemessen) · die zwei J5-Konversionen (Konversion 2 ist mit S2
**erledigt**: das Instrument steht, das Gate bleibt) · die vier
J6-Konversionen, Sensor-Population zuerst. Leitplanke wie überall:
Konversion heißt neuer MECHANISMUS, neue EVIDENZ oder neuer SENSOR mit
frischer Vorregistrierung — nie derselbe Knopf mit weicheren Gates.

Nicht jede Route der Register-Spalte hat eine Seite: **Laufform**,
**Lineal** und **Feder** führen ihre Historie weiter allein in §14. Das
ist kein Versäumnis, sondern die Grenze der Konvention — eine
Verfahrensseite entsteht, wo ein Ledger einen wiederkehrenden Stand
zusammenfasst, und diese drei haben ihren Stand anderswo
(`qualitaetsmetrik.md` §2 für das Lineal,
`../concepts/federmodelle.md` für die Feder, die Laufform-Zeilen in der
DB).
