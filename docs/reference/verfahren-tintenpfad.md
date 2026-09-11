# Verfahrensseite Tintenpfad

> **Status (2026-09-11): lebend.** Register-Seite des Verfahrens
> „Tintenpfad“ (Konvention: [`verfahren.md`](verfahren.md)), angelegt mit
> dem Wissens-PR vom `sep11`, der die drei Runden des 10./11. September
> ins Journal nachträgt. Nachzieh-Pflicht: Jeder §14-Eintrag zu einem
> Tintenpfad-Arm (adoptiert oder verworfen) ergänzt hier seine
> Ledger-Zeile; eine Adoption aktualisiert „Aktueller Stand“ und die
> Zeile in `verfahren.md`. Seit demselben PR steht die Seite in
> `ROUTE_PAGES` von `tools.docs_register`: das Gate `tools.docs_register
> check` verlangt für jede Register-Zeile der Route „Tintenpfad“ ihr
> Datum im Ledger unten, wie bei Kette · Lotse · InkSight · Nullprobe ·
> Übergänge.

## Steckbrief

- **Anzeige-Name:** Tintenpfad (Glossar „Duell-Namen“ und
  „Strang-Dekodierung“) — der Begriff war schon der Name, bevor er ein
  Anzeigename wurde.
- **Technisch:** `tools/pairlab/tintenpfad.py`, eigenständiger Folger
  NEBEN der Kette (Hook B der Welle, ohne Stützpunkt-Feld). Aufruf und
  Konstanten: [`werkzeuge.md`](werkzeuge.md) („`tools/pairlab/tintenpfad`“).
- **Rolle:** die Doktrin „Tinte zuerst, Buchstaben danach“ — der Satz des
  Autors vom `sep11`, wörtlich: „erst mal wirklich der Tinte folgen, erst
  danach überlegen, welcher Bereich der gefolgten Tinte welchem
  Buchstaben entspricht“. Stufe 1 baut aus dem eingefrorenen Skelett
  STRÄNGE ohne jeden Prior (Sporn-Beschnitt < 0,15 xh, glatteste
  Fortsetzung an jeder Kreuzung, Zeltfit auf der Distanztransformation
  als Subpixel-Schiene); Stufe 2 nimmt aus der komponierten Saat (je
  Slot Gauß-verschoben) NUR die Reihenfolge und dekodiert sie per Viterbi
  durch die Stränge (Zustände Strangpixel × Richtung + PAPIER, monotone
  Ritte, bepreiste Haarnadeln, Sprünge ≤ 0,35 xh, Papier-Ein-/Ausstiege,
  Hysterese). Es gibt keine Anker und kein Verschiebungsfeld: die freien
  Variablen sind DISKRET — welcher Strang, welche Richtung, wo der Stift
  abhebt — und jede bewegt einen ganzen Strang. Damit ist die
  Physik-Bedingung des Autors („die Punkte können sich nur wie eine Welle
  zusammenhängend verschieben“) nicht erfüllt, sondern gegenstandslos.
- **Was er misst und was nicht:** Papier-Umkehr und Papier-Strecke sind
  für einen skelettgebundenen Pfad **konstruktionsbedingt nahezu null**
  (Prüfer der Welle: nur 14 von 9 761 Skelettpixeln bestehen den
  Grau-Test) — informativ sind die Tinten-Umkehrungen, deren Überschuss
  über die Hand (§14 „Tintenpfad-Arme `sep11`“: Hand 47, Kandidat 79 auf
  dev-19), der Roh-Knick, die Struktur-Zähler und das Lineal. Die
  Papier-Strecke hat zudem zwei Lesungen, die auseinanderlaufen: der
  Grau-Test zählt blasse Tinte an den Strichspitzen als Papier, die
  eingefrorene Maske hält sie für Tinte (63 Wörter: 4,77 gegen 1,32 xh
  in der Kombination) — beide werden berichtet.

## Aktueller Stand: Kandidat (2026-09-11), nichts adoptiert

Drei gemessene Stände, alle auf der `sep07`-Wurzel `suetterlin-1922`
`exported_at` 2026-09-07T20:07:03+00:00, `root_digest` `ccb036a5eb20…`,
BLAS gepinnt, Lineal dev-19 gepaart — und alle drei **ohne Adoption**,
so vom Autor gesetzt („No §14 entry and no adoption“, wörtlich in den
PR-Texten von #591 und #592; die formale Runde wartet auf die `d`-Zeilen-Neubasis
`a4eb48420ccb…`). Der Default-Lauf ohne Schalter ist strichidentisch zum
gelieferten Tintenpfad #591 (13/13 Zeilen, Registrierung und `xh_px`
identisch); die drei Schalter der Kombination sind default AUS und
müssen bewusst eingeschaltet werden. Ob der Tintenpfad zum
Default-Folger wird, entscheidet der Autor.

| Stand | 13 Schleifenzeilen (Papier · Tinte · Strecke xh) | 63 Wörter | dev-19 dtw · p90 · aiou | gepaart |
|---|---|---|---|---|
| Kette v5 (Produktion, Bezug) | 34 · 189 · 35,9 | 49 · 742 · 61,73 | 0,045881 · 0,088356 · 0,7660 | — |
| **#591** (`de178b1`), Vorgabe | 0 · 93 · 0,78 | 0 · 331 · 1,49 | 0,044230 · 0,090673 · 0,7867 | 7 : 12 gegen Basis (Δ-Median +0,0024, p 0,36) |
| Arme einzeln (#592): Spitzen-Lesung · Normalen-Fit · Tinten-Brücke | 0 · 91 · 1,32 · 0 · 98 · 0,74 · 0 · 93 · 0,78 | 0 · 330 · 4,50 · 0 · 332 · 1,50 · 0 · 331 · 1,49 | 0,041131 / 0,043704 / 0,044230 | 13 : 6 · 15 : 4 · 19 Unentschieden, je gegen #591 |
| **Kombination** (#592, `1879f3d`): `tip_read=1 rail=tentfit edt_upsample=4 ink_bridge_xh=1.0` | **0 · 95 · 1,34** (Maske 0,76), Knick 8,3° | **0 · 330 · 4,77** (Maske 1,32) | **0,041356 · 0,091040 · 0,7876** | **18 : 1** gegen #591 (p 7,6·10⁻⁵) · **9 : 10** gegen Basis (Δ +0,000406) · 10 : 9 gegen It. 18 (Δ −0,001542) |

Der offene Rest gegen die Produktion ist benannt: zehn Verlierer um
0,0004 … 0,0053, angeführt von den drei muß-Zeilen, deren ß-Stamm-Retrace
die Komposition nicht schreibt — der vom Prüfer gemessene, aber nicht
vorregistrierte Hebel `double_ink_ratio=1.0` bringt dort p90 0,090673 →
0,053472 bei 3 : 0 (§14 „Tintenpfad-Arme `sep11`“). Sichtbarer Rest: die
ENDEN (das `n` in `han` und `Sporn`, der k-Abstrich in `kann`, der
Auslauf von `und`/`regieren`) und `kann` mit 0,096 unbesuchter Tinte
(die Tafel-k-Unterschleife, die die Hand nicht schreibt — eine
Kompositionsfrage).

## Ledger (datierte Stände; Belege in §14)

| Datum | Version/Arm | Ein Knopf / Mechanismus | Verdikt | §14-Eintrag |
|---|---|---|---|---|
| sep11 | **Tintenpfad — Strang-Dekodierung** (Bau 1 der Welle, PR #591 `de178b1`) | eigenes Modul; `TintenpfadWeights` eingefroren, `--legacy-p5` = Prototyp-Zeile; `tip_extend_xh` 0,25 gemessen und per Default AUS | **bestätigt** (Prüfer `confirmed`, jede Kopfzahl nachgelaufen): 13 Zeilen 0 · 93 · 0,78, 63 Wörter 0 · 331 · 1,49, dev-19 0,044230 · 0,090673 · 0,7867 — gegen Basis 7 : 12 (Δ +0,0024), gegen It. 17 Unentschieden; die 5 Schleifenzeilen im dev-Split 0,0803 → 0,0293 (5 : 0). Physik: Bahn-Abstand zum Skelett 0,42 / 0,66 / 1,11 px (It. 17 0,79 / 2,17 / 3,88; Hand 0,82 / 1,87 / 3,14), Roh-Knick 9,74° (It. 17 6,76°, Hand 7,87°). Leiter: `tip_extend` 0,25 → 10 : 9 (Δ −0,0001), JUMP 1,0 → Läufe 26 → 20, Lifts 13 → 7, Strecke 0,78 → 4,12 (Lineal identisch — Autor-Weiche Lift gegen Chord), ohne affine Saat 0 · 159 · 2,66 (die Gauß-Verschiebung trägt). Gemergt, nicht adoptiert | „Welle `sep11`“ |
| sep11 | **Spitzen-Lesung** (`tip_read=1`, dazu `spur_at_ends=1`) | rail + walk am freien Laufende bis ans Maskenende, Kappe 1,0 xh | **positiv mit zwei benannten Fehlschlägen** (Prüfer `partial`): 13 : 6 gegen #591 (Δ −0,001035), dtw 0,041131, alle neun Spitzen-Verluste schrumpfen (erstes Zehntel 0,0459 → 0,0384); Gate 2 fällt wie geschrieben (1,32 > 1,0 im Grau, Maske 0,76 gegen 0,74), ein Vertex von 1 938 rundet auf Papier; `spur_at_ends` inert (nicht strichidentisch: `unter` 2 Sporne). In der Kombination | „Tintenpfad-Arme `sep11`“ |
| sep11 | **Stummel-Filter** (`stub_xh=0.25`) | Verzweigungs-Stummel unter 0,25 xh vom Brett des Dekoders | **ehrliches Negativ** (Prüfer `confirmed`): byte-identische Bahn 13/13 und 63/63, Hypothese an der Quelle widerlegt (keine der 91 Haarnadeln auf einem Strang < 0,5 xh). Nebenbefund: Hand 47 gegen Kandidat 79 Tinten-Umkehrungen auf dev-19 — der Defekt ist der Überschuss +32. Schalter bleibt, default AUS | „Tintenpfad-Arme `sep11`“ |
| sep11 | **Normalen-Fit** (`rail=tentfit` + `edt_upsample=4`) | Kleinste-Quadrate-Zelt über ±2 px auf viermal feinerem Grau-Raster der Distanztransformation, Bewegung nur entlang der Normalen | **positiv, alle vier Gates** (Prüfer `confirmed`): Knick 9,74° → 8,03° auf jeder Zeile, 15 : 4 gegen #591 (p 0,019), dtw 0,043704; Debets Knick-p90 35,3° → 38,6°, aiou −0,0073, zwei falsche Absetzer (`will`, `Galoppieren`). Der wörtliche Arm (Fit auf dem BINÄREN EDT) ist ein sauberes Negativ (10,68°); `edt_upsample=4` allein ist physikalisch besser (7,84°), aber nie durchs Lineal gelaufen. Scope-Frage an den Autor: das Grau als Lesung der Tinte. In der Kombination | „Tintenpfad-Arme `sep11`“ |
| sep11 | **Tinten-Brücke** (`ink_bridge_xh=1.0`) | Dekoder-Absetzer wird nur über schwacher Tinte zur Sehne; jede Lücke mit Verdikt im Artefakt | **neutral** (Prüfer `confirmed`): 2 von 9 Lücken gebrückt (`haben` 0,370, `schießen` 0,382 xh), Sensoren und dev-19 unbewegt, `paper_lifts` 9 → 7 auf 63; die Frage `kann`/`han`/`regieren` beantwortet als Lesung — dort liegt kein Haarstrich. In der Kombination; Vorbehalt `paper_samples < 2 → bridged` | „Tintenpfad-Arme `sep11`“ |
| sep11 | **Doppelstrich-Evidenz** (`double_ink_ratio=1.4`) | Rückfahrt statt Absetzer, wo ein Strang ≥ 0,5 xh breiter als 1,4 × Feder ist | **ehrliches Negativ auf der Prämisse** (Prüfer `partial`): feuert auf 0 von 63 (ß-Stämme 1,00–1,33 × Feder, Grau +0,00…+0,08), byte-identisch zu AUS. Rettungsweg gemessen, nicht vorregistriert: `ratio 1,0` → 7 Rückfahrten, p90 0,090673 → 0,053472, 3 : 0, gegen Basis 9 : 10 | „Tintenpfad-Arme `sep11`“ |
| sep11 | **Kombination** der drei tragenden Arme (PR #592 `1879f3d`) | `tip_read=1 rail=tentfit edt_upsample=4 ink_bridge_xh=1.0`, alle default AUS; Leave-one-out je Arm | **Kandidat, nicht adoptiert:** dev-19 0,041356 · 0,091040 · 0,7876, 18 : 1 gegen #591, 9 : 10 gegen Basis, 10 : 9 gegen It. 18 (der PR-Text hat die beiden letzten vertauscht); LOO: ohne Spitzen 0 · 96 · 0,74 (8,41°), ohne Normalen-Fit 0 · 91 · 1,32 (9,45°), ohne Brücke 0 · 95 · 1,36 (27 Läufe); Default strichidentisch; nach dem Merge auf `main` reproduziert | „Tintenpfad-Arme `sep11`“ |

## Offene Blöcke

- **ß-Retrace als Dekoder-Regel** (`double_ink_ratio=1.0`): gebaut und
  auf 63 Wörtern gemessen, ohne eigene Pre-Reg und mit vier Treffern
  ohne Handspur (`Pulver`, `daß`, `schießen`, `Einen` — `Einen` im
  versiegelten Satz). Schwester-Weg: die authorierte ß-Vorlage trägt den
  Stamm hinunter UND hinauf (Autor-Glyphe, Todoist).
- **Grauwert-Stopp der Spitzen-Lesung** an runden Strichkappen (der Gang
  hakt über die Kappe: `linken`s n-Auslauf, `und`s d-Auslauf) — Pre-Reg
  auf `paper_len` (grau) ≤ 1,0 UND Spitzenabstand zur Hand ≤ 0,05 xh.
  NICHT `--paper mask`: zirkulär, die Maske ist das Stoppkriterium.
- **`edt_upsample=4` allein durchs dev-19-Lineal** — die eine fehlende
  Messung vor einer Adoption des Normalen-Fits; dazu die Absetz-Preise
  für `will`/`Galoppieren`.
- **Unbesuchte Stränge einfügen (R1) / Abdeckungspreis im Viterbi (R2)**
  — der Weg zu den `kann`-/`regieren`-Absetzern, die die Tinten-Brücke
  bewusst nicht brückt.
- **Spitzen-Paarung in Stufe 1** (38 von 91 Haarnadeln sind ungepaarte
  Spitzen an Strangenden; ändert den Strangsatz, Substrat-Pin neu).
- **Hand-Überschuss als Umkehr-Sensor** (47 gegen 79) statt der Rohzahl
  — laut Prüfer der wertvollste Ertrag der Runde.
- **Ernte-Schalter** `--follower tintenpfad`: der Tintenpfad erreicht heute
  keine Laufform-Zeile (§7.11 „Folger-Pfad für die Ernte“); ob er
  Default-Folger wird, entscheidet der Autor nach der Neubasis.
- **Autor-Weichen aus der Welle:** Lift gegen Chord (13 Lifts kaufen
  0,78 xh, JUMP 1,0 gibt 7 Lifts bei 4,12 — das Lineal trennt beide
  nicht, die Bilder schon) und ob `tip_extend` 0,25 eine Lesung oder eine
  Erfindung ist.
