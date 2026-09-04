# Messjournal — Tintenfolger-Bench (§14)

> **Status (2026-09-04): lebend.** Das Journal der Mess-Kampagne. Seit
> 2026-09-04 eine eigene Datei; bis dahin war es §14 von
> [`qualitaetsmetrik.md`](qualitaetsmetrik.md), Wort für Wort dieselbe
> Sektion.
>
> **Diese Datei liest man nicht.** Sie trägt 81 datierte Abschnitte und
> rund 143 000 Token. Der Einstieg ist das **Register** direkt unter der
> nächsten Überschrift — eine Zeile je Abschnitt mit Datum, Route, Typ ·
> Verdikt und dem Befund in einer Zeile —, und daneben der
> **Headline-Ledger** mit der Zahlen-Historie samt Fixture-Wurzeln.
> Beide zusammen kosten rund 10 000 Token; ein einzelner Abschnitt
> 2 000–3 500. Wer aus dem Register springt, lädt also ein Fünfzehntel
> statt der ganzen Datei — dafür ist sie geteilt.
>
> **Was gilt (Stand `sep02`).** Der Duell-Stand: Kette **v5** (`aug26`,
> Kompositions-Soll + Ratsche + Zone 0,55 sind der Default) · Lotse
> **v0.17** (`aug20`) · Lineal **v2.1**/**L-U** (`aug16`/`aug26`) ·
> Laufform **LF11** („glatte Zeile“, `sep02`, geschrieben). Die
> Headline-Zahlen selbst stehen an genau EINER Stelle, im
> Status-Blockquote von [`qualitaetsmetrik.md`](qualitaetsmetrik.md); der
> Ledger hier indexiert sie, er mintet sie nicht.
>
> **Was offen ist.** Die offenen Arme, die Autorenschritte und die
> stehenden Rettungswege der Kampagne führt
> [`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) (§7.9
> Rettungswege, §7.11 offene Arme) — nicht dieses Journal. Die
> Routen-Ledger mit Verdikt je Version stehen auf den Verfahrensseiten
> ([`verfahren.md`](verfahren.md)). Das Archiv der abgeschlossenen Arme
> ist [`messjournal-archiv.md`](messjournal-archiv.md) und heute leer.
>
> **Nachzieh-Anlass.** Jede Runde (`tracebench`, `wordbench`, Laufform,
> Übergänge) hängt ihren datierten `###`-Abschnitt ans Dateiende und
> ergänzt im selben PR ihre Registerzeile, eine bewegte Headline
> zusätzlich die Ledger-Zeile und die Zeile ihrer Verfahrensseite. Gate:
> `uv run python -m tools.docs_register check`.

**Warum die Sektionsnummer mitgezogen ist.** Titel und Anker der
Abschnitte werden im Repo rund 350-mal zitiert, fast immer als „§14
«Titel»“. Die Nummer ist damit ein Zitierschlüssel und keine Position in
dieser Datei. Daraus folgt die Lesehilfe für alles, was unten steht:
**jede andere §-Nummer im Text meint einen Abschnitt von
`qualitaetsmetrik.md`** — §15 etwa das Wort-Bench-Re-Baseline vom
`aug31`, §11b die Vorregistrierungs-Praxis.

**Nachtrag 2026-09-04 zur Platzierungsregel.** Der Satz weiter unten,
§14 ende an der §15-Überschrift, beschreibt den Stand bis zum Umzug.
Jetzt ist §14 die **letzte und einzige** Sektion dieser Datei: eine neue
Runde hängt ihren Abschnitt also ans Dateiende an — genau das, was eine
Runde ohnehin tut, womit der Fehlgriff von `sep02` hier gar nicht mehr
entstehen kann. Das Gate meldet weiterhin jede `###`-Überschrift hinter
§14; das kann nur noch eintreten, wenn jemand eine neue `## `-Sektion
aufmacht. Ein abgeschlossener Arm zieht nicht ans Dateiende, sondern in
[`messjournal-archiv.md`](messjournal-archiv.md).

## 14. Tintenfolger-Bench (`tracebench`): der nachgefahrene Referenzsatz als Maßstab (`aug14`)

Vorregistrierung VOR der ersten Zahl (die §11b-Praxis): Definitionen,
Split, Kriterien und Kill-Kriterien stehen hier, BEVOR irgendein
Kandidat gemessen wurde. Plan und Begründungen:
[`../proposals/tintenfolger.md`](../proposals/tintenfolger.md); die
Werkzeuge: `tools/tracebench/`.

### Register der Einträge (Index, keine Zahl-Heimat)

Diese Sektion trägt 81 datierte Abschnitte und ist die eine Heimat der
Kampagnen-Zahlen; die Tabelle hier ist ihr **Index** — sie wiederholt
keine Zahl, sie zeigt, wo eine steht. Ihre Reihenfolge ist die der
Datei, also die Reihenfolge, in der die Abschnitte angehängt wurden; die
Datums-Spalte macht dort, wo das von der Chronologie abweicht (LF9 vor
LF7/LF8), genau diese Abweichung sichtbar.

**§14 ist eine geschlossene Sektion** und endet an der §15-Überschrift.
Das war eine Zeit lang nicht so: eine Runde hängt ihren Abschnitt ans
Dateiende, und seit §15 dort steht, landeten die vier `sep02`-Einträge
(LF11 ×2, J4, J4b) und später die LF11-Adoption dahinter. Der Autor hat
am 2026-09-03 entschieden, §14 wieder zu schließen — die Abschnitte
stehen seither vor §15, Wort für Wort unverändert und mit ihren Ankern.
Wer die nächste Runde schreibt, hängt sie also nicht ans Dateiende,
sondern vor §15. Das Gate schaut dafür über die Sektionsgrenze hinaus:
**jede** `###`-Überschrift hinter §14 wird als verrutschter Eintrag
gemeldet („sits AFTER §14“) — sie fällt nicht still aus dem Fenster. Ob
eine Überschrift „nach Journal aussieht“, entscheidet das Gate bewusst
nicht: diese Datei trägt schon 26 datierte `###`-Überschriften außerhalb
von §14, das Datum trennt also nichts. Bekommt eine spätere Sektion
einmal eine eigene Unterüberschrift, wird sie in
`tools/docs_register` (`POST_JOURNAL_SUBHEADINGS`) eingetragen — eine
Zeile, die im Review sichtbar ist. Die fehlende Registerzeile ist die
andere, eigene Meldung und greift für Abschnitte INNERHALB von §14.

**Nachzieh-Pflicht: jeder neue `###`-Abschnitt dieser Sektion ergänzt im
selben PR seine Registerzeile**, und jeder Eintrag, der einen Arm einer
Duell-Route misst, zusätzlich die Ledger-Zeile seiner Verfahrensseite
([`verfahren.md`](verfahren.md)). Das Gate dazu ist
`uv run python -m tools.docs_register check --base origin/main`, in der
CI der Job „Docs-Register“.

Titel und Anker werden **nicht** umgeschrieben — sie werden außerhalb
dieser Datei rund 350-mal zitiert; ein Eintrag wird nie gelöscht oder
umsortiert, sondern nur durch einen späteren datierten Nachtrag ergänzt.

**Typ · Verdikt** benutzt ein kleines Vokabular: **Pre-Reg**
(Vorregistrierung vor der ersten Zahl) · **gemessen** · **Autopsie**
(Ursachensuche ohne eigenen Arm) · **Adoption** (der Mechanismus wird
Default) · **Re-Baseline** (deklarierte Verschiebung der
Vergleichsbasis); dahinter das Verdikt — **adoptiert** · **nicht
adoptiert** · **verworfen** · **gegenstandslos** · **geschrieben** (in
die DB) — mit seiner Bedingung.

| Datum | Route | Arm (Link → Abschnitt) | Typ · Verdikt | Befund in einer Zeile |
|---|---|---|---|---|
| aug14 | Lineal | [Rahmen](#was-gemessen-wird--und-in-welchem-rahmen) | Pre-Reg | Bench-Frame definiert (Registrierung je Bahn, xh aus word.json) |
| aug14 | Lineal | [Maße](#die-maße-definitionen-verbatim-keine-referenziert-publizierte-zahlen) | Pre-Reg | dtw_xh · aiou · Chamfer beidseitig · Marken/Kreuzungs-/Retrace-Zähler definiert |
| aug14 | Lineal | [Split](#split-append-never) | Pre-Reg | TRACEBENCH_DEV_IDS = 10 Wörter, append-never |
| aug14 | Lineal | [Kriterien](#kriterien-relativ-gepaart-je-wort-gegen-die-chain-baseline) | Pre-Reg | Primär dtw ≥ 20 % Fall; Co-Primär Marken/Kreuzungen; Struktur vetot Distanz |
| aug14 | Lineal | [Kill-Kriterien](#kill-kriterien) | Pre-Reg | Struktur schlägt Distanz; Bestätigungssatz; Identitäts-Gate |
| aug14 | Lineal | [Freeze-Deklaration](#freeze-deklaration) | Pre-Reg | Metrik-Module + Fixture-Roots frieren mit erster Baseline |
| aug14 | Lineal | [Grenze](#was-der-bench-nicht-beantwortet) | Pre-Reg | Duktus-Wahrheit sieht kein Bahnmaß; humanbench bleibt Endkriterium |
| aug14 | Kette | [Baseline (Freeze-Akt)](#baseline-aug14--der-kettenfit-gegen-die-hand-freeze-akt) | gemessen | Kette dtw 0,062 med, p90 0,262, 19 erfundene Kreuzungen (v1-Zähler); Schritt 0,02 gepinnt |
| aug14 | Kette | [Folger-Arme ①–⑧](#vorregistrierung-der-folger-arme-aug14-vor-dem-ersten-sweep) | Pre-Reg · ②③④⑦⑧ abgeschrieben (`sep03`) | Arm-Reihenfolge + Kill-Kriterien; fünf Arme nie gemessen und am 2026-09-03 per Autor-Entscheid abgeschrieben — Gewichts-Sweeps derselben Formulierung, die ①⑤⑥⑥b⑨ erschöpfend negativ beantwortet haben (Nachtrag im Abschnitt, §7.9/§7.11) |
| aug14 | Kette | [Arm ① λ_prox](#arm-①-aug14--die-λ_prox-leiter-formulierung-v1-verworfen-der-tinten-zug-validiert) | gemessen · verworfen | Struktur-Veto auf jeder Sprosse (26→43–66); Tinten-Zug +0,10 aiou validiert |
| aug14 | Kette | [Arme ⑤+⑥](#arme-⑤--⑥-aug14--overlap-freigesprochen-die-korrespondenz-kappe-gefunden) | gemessen · verworfen | Overlap freigesprochen; Korrespondenz-Kappe (12/21 Ziele ohne Kreuzung) |
| aug14 | Kette | [Arm ⑥b](#arm-⑥b-aug14--vorregistrierung-klassenbewusste-korrespondenz) | Pre-Reg | Klassenbewusste Korrespondenz (Touch/T-Junction Gewicht 0) |
| aug15 | Kette | [Arm ⑥b](#arm-⑥b-aug15--die-kappe-war-die-schranke-klassenbewusst-ist-der-term-punktweise-kostenlos-adoptiert-wird-trotzdem-nichts) | gemessen · nicht adoptiert | Hypothese bestätigt (punktweise kostenlos), Struktur-Veto vs. Baseline bleibt |
| aug16 | Lineal | [Struktur-Zähler v2 / v2.1](#struktur-zähler-v2-aug16--vorregistrierung--re-baseline-deklaration) | Re-Baseline (Lineal) | Durchstoß-/Retrace-Regeln; Kette m+s 26→18→11; Berührung/Überlagerung als Klassen |
| aug15 | InkSight | [Route B T0](#route-b-t0-aug15--inksight-small-p-roh-auf-den-dev-wörtern) | gemessen | derender 0,0956 = 1,5× Kette; text schlechter; Retraces verloren, Kreuzungen sauber |
| aug16 | Kette | [Arm ⑨ Topologie-Wächter](#arm-⑨-aug16--vorregistrierung-der-topologie-wächter) | Pre-Reg + gemessen · verworfen | Kontrakt hält, dtw-Δ exakt 0 → Route-A-Fazit; Nachtrag datiert aug15 (vor Abschnitt) |
| aug14 | Nullprobe | [Route G](#route-g-aug14--die-prior-freie-kontrolle-was-der-duktus-prior-kauft) | gemessen | 0,820 = 13× Kette; 15/23 Kreuzungen, alle Retraces verloren; aiou 0,833 (Skelett-Mitte) |
| aug15 | Komposition | [Welle 1 · K1 Balken-Überstand](#welle-1--k1-aug15--vorregistrierung-t-balken-schnitt-mit-überstand) | Pre-Reg + gemessen · adoptiert | Erwartung widerlegt, Attribution-Argument; wordbench 0,110703→0,110992 |
| aug15 | InkSight | [Welle 1 · B1 Best-of-N](#welle-1--b1-aug15--vorregistrierung-best-of-n-über-input-augmentierungen-inksight) | Pre-Reg + gemessen · verworfen | Δ +0,0000; Orakel −0,0124 bewiesen, Ranker ordnungs-blind → „Chor“ |
| aug15 | Kette | [Welle 1 · A1 Marken-Nachfit](#welle-1--a1-aug15--vorregistrierung-der-marken-nachfit) | Pre-Reg + gemessen · adoptiert (opt-in) | Marken-Ortsfehler −55 %; Nachtrag aug19: −73 % auf dev-19 |
| aug15 | Komposition | [Welle 1 · K1b Stamm-Rückpass](#welle-1--k1b-aug15--vorregistrierung-der-versetzte-stamm-rückpass-des-t) | Pre-Reg + gemessen · adoptiert | soll_cross unter 2→3, mit 1→2 = Hand; wordbench 0,110983 |
| aug15 | Komposition | [Welle 2 · P1/P1b Vorschub](#welle-2--p1-aug15--vorregistrierung-die-vorschub-kalibrierung-aus-den-gemessenen-joins) | Pre-Reg + gemessen · 3 adoptiert, 1 verworfen | Bowl-Tuck · w/v-Rückwärts · Balken-Steigung; Arkaden-Luft verworfen; words 0,108446, pairs 0,146602 |
| aug15 | Komposition | [Welle 2 · P2 align-Klasse](#welle-2--p2-aug15--vorregistrierung-die-align-klasse-und-der-arkaden-varianz-befund) | Pre-Reg + gemessen · Floor adoptiert, Trim neutral | words 0,108091; Arkaden-Luft = Beleg-Varianz (geschlossen) |
| aug16 | Komposition | [Welle 2 · P3 Koartikulation K1/K3/K2](#welle-2--p3-aug16--vorregistrierung-kopf-koartikulation-als-entry-klassenregeln) | Pre-Reg + gemessen · 3× verworfen | Alle drei Entry-Regeln negativ; Verbinderform-Hypothese + O2-Jitter stehend |
| aug16/aug19 | Kette | [Wächter als Produktions-Kette (einseitig · zweiseitig · soll-bewusst)](#wächter-als-produktions-kette-aug16--vorregistrierung-die-gewachte-bahn-wird-die-gespeicherte) | Pre-Reg + gemessen · nicht adoptiert | BLAS-Reproduzierbarkeits-Fund; 107=107 Struktur friert; Owner-Abwägung → zonale Rückweisung |
| aug16 | Lotse | [Route Lotse v0.1 · v0.2 (A5) · v0.3 · v0.4 · Schienen-Auslauf](#route-lotse-aug16--vorregistrierung-skelett-fahren-duktus-als-karte) | Pre-Reg + gemessen | v0.1 verworfen (unter −0,386); v0.2/v0.3/v0.4 verworfen; Auslauf 1,0 adoptiert (0,1192→0,1007) |
| aug16 | Lotse | [v0.5 Ritt-Doppelzonen](#route-lotse-v05-aug16--vorregistrierung-karten-geometrie-in-ritt-doppelzonen) | Pre-Reg + gemessen · adoptiert | 0,1007→0,0853; Fusions-Orakel 0,0563; Auswähler-Diagnostik ohne Ergebnis |
| aug16 | Lotse | [v0.6 Feinschliff](#route-lotse-v06-aug16--vorregistrierung-der-feinschliff) | Pre-Reg + gemessen · verworfen | Lineal blind für Zickzack; Glättung ist Darstellungsstufe beim Konsumenten |
| aug16 | Komposition | [O2-Trim-Jitter](#o2-trim-jitter-aug16--vorregistrierung-der-bugfix-der-auch-verlieren-darf) | Pre-Reg + gemessen · Toleranz bleibt 0 | Bug = zufällige Klassenregel (n hoch, r tief); Klassenregel als Pre-Reg stehend |
| aug17 | alle Routen | [Re-Baseline 19er-Dev-Satz](#re-baseline-aug17--der-19er-dev-satz-dev-erweiterung-aktiviert-alle-stehenden-routen-neu-vermessen) | Re-Baseline | Kette 0,0579 · Lotse 0,0850 · Nullprobe 0,619 · InkSight 0,0951 (5 failed) · Orakel 0,0491 |
| aug17 | Lotse | [v0.7 Zonen-Ausweitung](#route-lotse-v07-aug17--vorregistrierung-die-zonen-ausweitung-der-kartenfahrt-l1) | Pre-Reg + gemessen · adoptiert 0,35 | Defekte 35→32; nur Punkt-Pinch-Klasse |
| aug17 | Lotse | [v0.8 Karten-Selbstschnitt roh](#route-lotse-v08-aug17--vorregistrierung-karten-vorfahrt-an-karten-selbstschnitten-l1b) | Pre-Reg + gemessen · verworfen | Defekte 32→4, dtw unter Kette – aiou-Kill um 0,003 |
| aug17 | Lotse | [v0.9 gepinnte Fenster](#route-lotse-v09-aug17--vorregistrierung-gepinnte-selbstschnitt-fenster-l1c) | Pre-Reg + gemessen · adoptiert 0,35 | dtw 0,0578, gepaart −24 %, Netto 7 – „stärkste Zahl der Kampagne“ |
| aug19 | Lotse | [v0.10 Punkt-Knoten-Pinnung](#route-lotse-v010-aug19--vorregistrierung-knoten-anker-pinnung-der-karten-läufe-l1d) | Pre-Reg + gemessen · verworfen | Offset-Feld schert; aiou +0,027, Ortsfehler halbiert |
| aug19 | Lotse | [v0.11 Plateau-Anker](#route-lotse-v011-aug19--vorregistrierung-plateau-anker-stückweise-starre-fenster-l1e) | Pre-Reg + gemessen · adoptiert „windows“ | missing 3→1, Ortsfehler −43 %; „all“ um ein Doppel-X verworfen |
| aug19 | Lotse | [v0.12 Plateau-Sehne](#route-lotse-v012-aug19--vorregistrierung-die-plateau-sehne-doppel-x-begradigung-l1f) | Pre-Reg + gemessen · verworfen | Der Wackel WAR das X (missing 1→8) |
| aug19 | Kette | [L2-Rest-Autopsie](#l2-rest-autopsie-aug19--die-kollaps-klasse-unter--muß3-ist-ordnungs-dominiert-der-deckbogen-sitzt-in-der-ketten-assembly-an-der-falschen-sequenz-position) | Autopsie | Kollaps-Klasse = Assembly-Ordnung (unter 0,450→0,085 per Permutation); Referenzen sauber |
| aug19 | Kette | [K-A marken-endständige Assembly](#kette-k-a-aug19--vorregistrierung-die-marken-endständige-assembly-owner-go-weiter-optimieren) | Pre-Reg + gemessen · adoptiert v2 | unter −0,365, muß-Familie −0,11…−0,13; Geometrie byte-gleich |
| aug19 | Kette | [K-B Zacken-Reparatur + Re-Baseline v2/v3](#kette-k-b-aug19--vorregistrierung-die-zacken-reparatur-im-trace) | Pre-Reg + gemessen · adoptiert v3 · Re-Baseline | Galoppieren 0,233→0,040; v3 dtw 0,0491 / p90 0,0894 |
| aug19 | Lotse | [v0.13 Entdrillung / v0.14 „all“](#route-lotse-v013v014-aug19--vorregistrierung-die-entdrillung-dann-die-all-stufe-owner-go-weiter-mit-lotse-neben-ink) | Pre-Reg + gemessen | v0.13 0,5 adoptiert (Netto 7→6), 0,8 verworfen; v0.14 verworfen (G-Kopf-X) |
| aug19 | Lotse/Laufform | [v0.15 soll-budgetierte Entdrillung + 3 Nachträge](#route-lotse-v015-aug19--vorregistrierung-die-soll-budgetierte-entdrillung-l1h) | Pre-Reg + gemessen · verworfen · Autopsie | Budget erbt Karten-Fehler; Nachträge: 43/62 Glyphen ohne Laufform, W/p auf Laufform-Schicht |
| aug19 | Laufform | [LF1 Lücken-Schluss](#laufform-lf1-aug19--vorregistrierung-der-lücken-schluss-evidenz-boden-der-scan-fits) | Pre-Reg + gemessen · verworfen | wordbench −0,0024 (n=1) aber G verliert 2. Kreuzung |
| aug19 | Laufform | [LF2 Topologie-Wächter](#laufform-lf2-aug19--vorregistrierung-der-topologie-wächter-h--p) | Pre-Reg + gemessen · verworfen | Galoppieren-Soll 6→8 erreicht, aber Marken-Gate (i-Punkt kippt) |
| aug19 | Laufform | [LF3 Topologie-Reparatur (Buchstaben-Orakel)](#laufform-lf3-aug19--vorregistrierung-die-topologie-reparatur-lokale-chart-rückblendung) | Pre-Reg + gemessen · nicht adoptiert | Mechanismus richtig, Orakel zu schwach (Komp.-Soll bleibt 6) |
| aug19 | Laufform | [LF3b Kompositions-Orakel](#laufform-lf3b-aug19--vorregistrierung-die-topologie-reparatur-am-kompositions-orakel) | Pre-Reg + gemessen · adoptiert (Kandidaten-Karte, trocken) | p t=0,578; Galoppieren-Soll 8; Lotse aiou 0,7484 |
| aug19 | Lotse | [Wiedervorlage v0.14 auf LF3b-Karte](#wiedervorlage-v014-aug19--vorregistrierung-die-all-stufe-auf-der-lf3b-karte) | Pre-Reg + gemessen · verworfen | Karten-Form-These widerlegt (Netto 7 > 5) |
| aug20 | Lotse | [G-Kopf-Ritt-Autopsie](#lotse-g-kopf-ritt-autopsie-aug20--der-riss-ist-die-parität-blinde-entdrillung-nicht-die-pinnung) | Autopsie | Riss = parität-blinde Entdrillung; v0.15-Soll doppelt gezählt; Fenster 0,8 tot |
| aug20 | Lotse | [v0.16 selektive Pinn-Leiter + Lineal-Soll-Budget](#lotse-v016-l1i-aug20--vorregistrierung-selektive-pinn-leiter-mit-lineal-soll-budget-77-wiedervorlage) | Pre-Reg + gemessen · adoptiert „bridges“ | p90 0,1129→0,1122, kein Verlierer; zones/all an p-Oskulation |
| aug20 | Lotse | [Karten-Soll-Autopsie](#lotse-karten-soll-autopsie-aug20--die-platzierungs-decke-ist-präziser-eine-soll-vollständigkeits-lücke) | Autopsie | 40/41 Hand-X gematcht; Reservierungs-Semantik; Blocker = Soll-Vollständigkeit |
| aug20 | Lotse | [v0.17 Reservierungs-Veto](#lotse-v017-l1j-aug20--vorregistrierung-das-reservierungs-veto) | Pre-Reg + gemessen · adoptiert (Parität) | zähler-identisch, Spiegelungen 15→11 |
| aug20 | Lotse | [t-Stamm-Ritt-Autopsie](#lotse-t-stamm-ritt-autopsie-aug20--die-vollständigkeits-lücke-ist-eine-auflösungs-grenze) | Autopsie | 0,12-Abtastung kollabiert 0,06-X-Doppel; Komposition führt 41/41 |
| aug20 | Lotse | [v0.18 Auflösungs-Leiter](#lotse-v018-l1k-aug20--vorregistrierung-die-auflösungs-leiter) | Pre-Reg + gemessen · verworfen | Netto 3 (Bestwert), aber Ökonomie sample-denominiert (dtw +0,035) |
| aug20 | Lotse | [v0.19 schritt-invariante Ökonomie + Glättungs-Proben](#lotse-v019-l1l-aug20--vorregistrierung-die-schritt-invariante-ökonomie--wiedervorlage-der-auflösungs-leiter) | Pre-Reg + gemessen · Refactor bleibt, Leiter verworfen | Familie geschlossen: Entscheidungs-Granularität des Viterbi; Betriebspunkt-Kandidat verworfen |
| aug20 | Kette | [K0-Z zonale Rückweisung](#kette-k0-z-aug20--vorregistrierung-die-zonale-rückweisung) | Pre-Reg + gemessen · verworfen per Gate | Soll 107→102, dev 0,0494→0,0472; Risse daß 2→3, ein −0,0049 |
| aug20 | Kette | [K0-Z-R Ratschen-Budget](#kette-k0-z-r-aug20--vorregistrierung-das-ratschen-budget) | Pre-Reg + gemessen · verworfen per Gate | Soll 107→99, null aiou-Verlierer; Fund: ZWEI Soll-Quellen |
| aug20 | Kette | [K-C Tinten-Evidenz-Maske (Autopsie „Flecken“)](#kette-k-c-aug20--vorregistrierung-die-tinten-evidenz-maske-autor-fund-flecken) | Autopsie + Pre-Reg + gemessen · alle Gates grün | Soll 107→86, dev 0,0494→0,0453, Galoppieren −83 %; Adoption wartet Autor-Go |
| aug21 | Kette | [Kette v4 Adoption K-C](#kette-v4-aug21--adoption-k-c-die-tinten-evidenz-maske-wird-default-datierte-re-baseline) | Adoption · Re-Baseline | Soll 103→85; Folger dev 0,0491→0,0448, aiou 0,7481; chain-Provider 0,0491/0,0891 |
| aug21 | Kette | [K-E1 Marken-Claim-Trennung](#kette-k-e-aug21--vorregistrierung-tinten-zuweisung-per-strecke-stufe-1-die-marken-claim-trennung) | Pre-Reg + gemessen · verworfen (Gate 3) | die-2 heilt (Soll 4→1, dtw −0,028); 4 diffuse aiou-Risse |
| aug21 | Kette | [K-E2 ohne Breitenfeld-Split](#kette-k-e2-aug21--vorregistrierung-die-marken-claim-trennung-ohne-breitenfeld-split-ein-faktor-konversion) | Pre-Reg + gemessen · verworfen | Breiten-Hypothese widerlegt (55/63 byte-gleich); Familie geschlossen |
| aug21 | Kette | [K0-S Soll-Quellen-Autopsie + EINE Soll-Pipeline](#kette-k0-s-aug21--soll-quellen-autopsie-daß--vorregistrierung-eine-soll-pipeline-und-die-k0-z-r-wiedervorlage) | Autopsie + Pre-Reg + gemessen · alle Gates grün | daß-Riss = Init-Splitter; 40/63 Runs divergieren; Soll 85→77, dev-aiou +0,0216; wartet Autor-Go |
| aug21 | Kette | [K-D Tinten-Korridor](#kette-k-d-aug21--vorregistrierung-der-tinten-korridor-mit-dem-gegenstands-test-zuerst) | Pre-Reg + Gegenstands-Test · gegenstandslos | Exkursions-Inventar max 0,33 xh; Sensor excursions.py bleibt |
| aug25 | Lineal | [L-U u-Bogen als Marke](#lineal-l-u-aug25--vorregistrierung-der-u-bogen-als-marke-autor-entscheid-zur-bogen-klassifikation) | Pre-Reg (Lineal) | Kappe 0,8→1,5 aus Breitenmodell; 6 Gates, keines ein Routen-Ergebnis |
| aug26 | Lineal | [L-U gemessen](#lineal-l-u-aug26--gemessen-alle-sechs-gates-bestanden-der-gewinn-liegt-auf-einer-route) | gemessen · adoptiert · Re-Baseline (Lineal) | Kette p90 0,2355→0,0896, unter 0,450→0,088; Lotse/Nullprobe leicht schlechter; InkSight NICHT nachgemessen |
| aug26 | Kette | [Kette v5 Adoption K0-S Sprosse 2](#kette-v5-aug26--adoption-k0-s-sprosse-2-kompositions-soll--ratsche--zone-055-wird-default-datierte-re-baseline) | Adoption · Re-Baseline | dtw 0,0446 / p90 0,0861 / aiou 0,7608 / Soll 79; Umweg falsche Basis → Stack-Sensor; 13 Rückweisungen offen |
| aug26 | Laufform | [LF3b-W Schreib-Karte](#laufform-lf3b-w-aug26--vorregistrierung-die-schreib-karte-neuableitung-unter-kette-v4-und-lineal-15) | Pre-Reg + gemessen · 14er verworfen, 13er geschrieben | Kette cross_missing 13→14 (eine Kreuzung); 13 Zeilen ohne p geschrieben (Snapshot 2026-08-26T11-13-38Z); p → LF4 |
| aug29 | Laufform | [LF5 Endblende + K0](#laufform-lf5-aug29--vorregistrierung-die-endblende-chart-rückblendung-an-den-freien-strichenden-korb-7) | Pre-Reg + gemessen · verworfen; K0 geschrieben | wordbench +0,0114/+0,0220 (Breite ist Hand); K-Zeile in Prod gelöscht; Wurzel 2026-08-29: 0,106720/0,146506 |
| aug29 | Laufform | [LF6 Quer-Endblende](#laufform-lf6-aug29--vorregistrierung-die-quer-endblende-nur-der-quer-anteil-der-end-drift-geht-zurück) | Pre-Reg + gemessen · verworfen | +0,0132/+0,0286; globale Endregel falscher Ort |
| aug29 | Übergänge | [J1 Prior-Landerichtung](#übergänge-j1-aug29--vorregistrierung-die-prior-landerichtung-korb-7-t-nach-n) | Pre-Reg + gemessen · nicht adoptiert | (a) −0,0010 grün, (c) rot: ALIGN_MAX_ENTRY_Y sperrt t |
| aug29 | Übergänge | [J2 Anstrich-Verlängerung](#übergänge-j2-aug29--vorregistrierung-die-anstrich-verlängerung-in-den-schaft) | Pre-Reg + gemessen · verworfen | +0,0041; Hand kommt auf Fußhöhe an (Dissektionen) |
| aug29 | Übergänge | [J3 tiefe Schaft-Kopplung](#übergänge-j3-aug29--vorregistrierung-die-tiefe-schaft-kopplung-korb-7-t-nach-n-zweiter-arm) | Pre-Reg + gemessen · nicht adoptiert | (d) rot dconn 7/7; Haken ist die Zeile (t-Kopf 104° vs 37°) |
| aug29 | Laufform | [LF9 Kopf-Gate](#laufform-lf9-aug29--vorregistrierung-das-kopf-gate-auf-der-zeile-korb-7-der-t-haken) | Pre-Reg + gemessen · adoptiert (τ 15°, gerendert) | Anker-Sensor stirbt an Kill; t/E/f/v/k in Prod gelöscht (Autor); Neuexport = erklärte Re-Baseline (Vorschau 0,107995) |
| aug29 | Laufform | [LF7 Zeilen-Gate (Natürlichkeits-Lücke)](#laufform-lf7-aug29--vorregistrierung-das-zeilen-gate-aufnahme-einer-laufform-zeile) | Pre-Reg + gemessen · verworfen | τ 0,31 verfehlt K (+0,237); Sprung-Ratio trennt |
| aug29 | Laufform | [LF8 Sprung-Gate](#laufform-lf8-aug29--vorregistrierung-das-sprung-gate-auf-der-zeile) | Pre-Reg + gemessen · adoptiert τ 2,95 | ue/F/ae/b in Prod gelöscht; v/E/P/k bleiben (Form-Abstand-Arm offen) |
| aug30 | Übergänge | [Korb-Runde B-Kringel (#8) + St-Ligatur (#9)](#übergänge-korb-runde-aug30--b-verlässt-die-restart-klasse-korb-8--st-ligatur-korb-9) | gemessen · adoptiert (join_rule); St → Autor | Wörter 0,106400 „unverändert“ (Wurzel undeklariert), Paare 0,146580→0,148467 |
| sep01 | Laufform | [LF10 Form-Abstand auf der Zeile](#laufform-lf10-sep01--vorregistrierung-der-form-abstand-auf-der-zeile) | Pre-Reg | Form-Drift ohne Sprung in Nib-Radien messen; Kill-Klausel: P muss über τ_form liegen |
| sep01 | Laufform | [LF10 gemessen](#laufform-lf10-sep01--gemessen-die-vorhersage-i-ist-falsch-der-form-abstand-wird-nicht-adoptiert) | gemessen · nicht adoptiert | Vorhersage (i) falsch: τ_form 1,40 (w), P nur 1,01 — Rang 5 von 22; sechs Empfindlichkeitsprüfungen kehren nichts um |
| sep02 | Laufform | [LF11 glatte Zeile (Spline-Basis-Median)](#laufform-lf11-sep02--vorregistrierung-die-glatte-zeile-spline-basis-median-statt-per-anker-median) | Pre-Reg | Zeile als Median in glatter B-Spline-Basis statt je Anker; Leiter über die Knotenweite Δs |
| sep02 | Laufform | [LF11 gemessen](#laufform-lf11-sep02--gemessen-eine-sprosse-besteht-alle-gates-und-sie-repariert-die-zeilen-gates-gleich-mit) | Pre-Reg + gemessen · Sprosse Δs 0,16 besteht alle Gates; Adoption offen | Zacken/xh 6,86→0,45, Wörter 0,109218 · Paare 0,148198, keine Kreuzung verloren; Karte trocken, wartet auf die humanbench-Wort-Runde |
| sep02 | Übergänge | [J4 Austritts-Kollinearität (`exit_trim`)](#übergänge-j4-sep02--vorregistrierung-die-austritts-kollinearität-exit_trim) | Pre-Reg + gemessen · verworfen | 4 von 5 Gates grün (Wörter −0,000535, seam_dep +12,52→−1,39), (b) rot: `dconn` fällt nur in 20 % statt 60 % |
| sep02 | Übergänge | [J4b enge Klasse](#übergänge-j4b-sep02--post-hoc-die-enge-klasse-nur-die-joins-die-wirklich-knicken) | POST-HOC · verworfen | Schnitt bei 20° Knick rettet den Arm nicht: `dconn` 43 %, seam_dep der Klasse nur +8,02 — Rettungswege in §7.9 |
| sep02 | Laufform | [LF11 humanbench-Runde und Adoption](#laufform-lf11-sep02--humanbench-wortrunde-instrumentdefekt-und-adoption-prod-write--re-baseline) | **ADOPTIERT auf Autor-Entscheid** (kein formales Instrument-Verdikt) · Prod-Write + Re-Baseline | Runde verlässlich (10/12 Arm) und Richtung erdrückend (40 : 1), aber die Tie-Schranke fällt in JEDER Lesart (34,9 % gesamt, 25,6 % in der günstigsten Teilmenge, gegen ≤ 25 %) — `adopt: false`; ob ein Teil der Runde auf der defekten Anzeige „gefüllte Ringe" lief, ist zwischen Protokoll und Bestand ungeklärt (offener Punkt); Write nach Snapshot `2026-09-02T21-58-16Z`, Readback 22/22; Wörter 0,109218 · Paare 0,148198 |
| sep04 | Übergänge | [P-Spiegel: pairlab auf den Produktions-Verbinder](#übergänge-p-spiegel-sep04--pairlab-misst-wieder-den-produktions-verbinder-werkzeug-re-baseline-kein-arm) | Werkzeug-Re-Baseline · kein Arm | Audit-Befund 18 beziffert und behoben: 89 von 248 Nähten wichen ab (Median 0,0562 xh, Majuskeln 1,0365), `gen_chamfer` 0,0434 → 0,0392; Kette-Init bleibt auf dem eingefrorenen Spiegel (Autor-Frage) |
| sep04 | Übergänge | [S1 `dspan` (ausdehnungs-normierte Formdistanz)](#übergänge-s1-sep04--vorregistrierung-dspan-die-ausdehnungs-normierte-formdistanz) | Pre-Reg | Rettungsweg 2 von #488: gemeinsamer Abschnitt statt Start-Ausrichtung; Gates P1/P2/P3(a,b) und Nullproben N1/N2 vor der ersten Zahl |
| sep04 | Übergänge | [S1 gemessen](#übergänge-s1-sep04--gemessen-der-sensor-ist-validiert-und-er-rettet-j4-trotzdem-nicht) | gemessen · Sensor validiert, J4 bleibt verworfen | Δ`dspan` +0,0036 (Gate ≤ 0,010), Fallquote 48,8 % (Gate ≥ 40 %) gegen 19,8 % roh und 51 % handbereinigt — aber die 60 % des J4-Gates erreicht auch die saubere Lesung nicht |
| sep04 | Feder | [Platten-Nib A3 (Wortrunde)](#platten-nib-a3-sep04--vorregistrierung-die-wortrunde-über-die-strichbreite) | Pre-Reg · Runde gebaut, Urteil offen | Halbbreite 0,097 statt 0,07251. Das Lineal ist nicht blind, sondern EINSEITIG: dem Lineal die breitere Feder nennen senkt bei unveränderter Geometrie 0,109218 → 0,101560. Nebenbedingung des Audits schon trocken gerissen (`gleichzug_doublings` 13 → 21) — ein ≥ 60 % lizenziert nur den Folgearm „Ink-Clearance an die Feder koppeln", nicht den Write |
| sep04 | Übergänge | [J4 Wortrunde (Rettungsweg 3)](#übergänge-j4-sep04--vorregistrierung-die-wortrunde-als-benannter-rettungsweg) | Pre-Reg · Runde gebaut, Urteil offen | Der §7.9-Rettungsweg zum `dconn`-Negativ; auf der LF11-Wurzel neu vermessen: `seam_dep` +7,99 → +0,02, Wörter +0,000248 (Vorzeichen gedreht), Paare byte-gleich |

### Headline-Ledger (die Wordbench-Zahlen und ihre Wurzeln)

Die Wordbench-Headline (`word_loss` über 63 Wortproben · `pair_loss`
über 33 Paar-Drills) wandert seit `aug14` nur noch im Fließtext dieser
Sektion; §6 endet bei der `aug14`-Zeile, die dort angekündigte
Nachführung blieb aus. Hier steht die Kette am Stück — die Belege
bleiben in den verlinkten Abschnitten, diese Tabelle zitiert sie nur.

**Kopfregel seit `sep02`:** jeder Eintrag, der eine Headline bewegt,
nennt das `exported_at` seiner Fixture-Wurzel und die ersten zwölf
Stellen ihres `root_digest`. Die Wurzeln sind gitignored — ohne diese
zwei Angaben hinterlässt ein Neu-Export keine Spur, und genau daran ist
die `aug30`-Zeile unten gescheitert. Beides druckt jeder Lauf von
`tools.wordbench.run` und `fetch_fixtures --verify` vor der ersten
Komposition; `--expect-root <präfix>` macht die erwartete Basis zur
Vorbedingung (Glossar „Wurzel-Digest“, `tools/wordbench/README.md`).

| Datum | PR | Wurzel / Re-Baseline | Wörter | Paare | Beleg |
|---|---|---|---|---|---|
| aug14 | #337 | Voll-Re-Export nach #334/#336 — deklarierte Doppel-Re-Baseline (wordbench + tracebench) | 0,110703 | 0,165688 | §6, Absatz „Headline gegen den dokumentierten `aug07`-Stand“ |
| aug15 | #358 | dieselbe Wurzel | 0,110992 | 0,165688 | §14 „Welle 1 · K1“ |
| aug15 | #359 | dieselbe Wurzel | 0,110983 | 0,165725 | §14 „Welle 1 · K1b“ |
| aug15 | #361 | dieselbe Wurzel | 0,108991 | 0,146602 | §14 „Welle 2 · P1“ |
| aug15 | #361 | dieselbe Wurzel | 0,108446 | 0,146602 | §14 „Welle 2 · P1“ (P1b) |
| aug15 | #363 | dieselbe Wurzel — Stand bis `aug26` | 0,108091 | 0,146602 | §14 „Welle 2 · P2“ |
| aug29 | #443 | Neu-Export nach dem LF3b-W-Write (Wurzel 2026-08-29, `--set all --verify`), Vergleich läuft wurzel-intern | 0,106720 | 0,146506 | §14 „Laufform LF5“, Absatz „Basis“ |
| aug30 | #463 | **undeklariert** — kein Eintrag nennt den Wechsel von der `aug29`-Wurzel | 0,106400 | 0,146580 | §14 „Übergänge Korb-Runde“; Nachtrag unten |
| aug30 | #463 | dieselbe undeklarierte Wurzel, nach B-Kringel + Nachschärfung | 0,106400 | 0,148467 | §14 „Übergänge Korb-Runde“ |
| sep01 | #472 | **Re-Baseline**: sieben reparierte Wort-Rechtecke, Bahnen nachgezogen, Wurzeln neu gebaut | 0,109255 | 0,148433 | §15 |
| sep02 | dieser PR | Wurzeln neu gebaut (`fetch_fixtures --set all --verify`), `exported_at` 2026-09-02T08:00:29+00:00, `root_digest` `28ba1afebc53…` (`suetterlin-1922`) / `f0cf3d53414c…` (`suetterlin-1922-pairs`) — **keine** Re-Baseline: §15 wird exakt reproduziert | 0,109255 | 0,148433 | dieser Ledger-Eintrag |
| sep02 | #501 | **Re-Baseline nach dem LF11-Write**: 22 Laufform-Zeilen auf Spline-Basis-Mediane umgestellt (Snapshot `2026-09-02T21-58-16Z`, Readback 22/22), Wurzeln neu gebaut: `suetterlin-1922` `exported_at` 2026-09-02T22:13:54+00:00 `root_digest` `2e3581287bed…`, `suetterlin-1922-pairs` `exported_at` 2026-09-02T22:13:53+00:00 `root_digest` `cee9d363f497…`; trifft die trockene LF11-Vorhersage exakt | 0,109218 | 0,148198 | §14 „Laufform LF11 — humanbench-Wortrunde, Instrumentdefekt und Adoption“ |
| sep03 | #516 | Wurzeln neu gebaut (`fetch_fixtures --set all --verify`, 12/12 bit-exakt) im Zuge der Glyph-Bench-Re-Baseline (Audit A15): `suetterlin-1922` `exported_at` 2026-09-03T21:28:30+00:00 `root_digest` `57402ae7dd41…`, `suetterlin-1922-pairs` gleicher Zeitstempel `f176e191d4bf…` — **keine** Re-Baseline der Wort-Zahlen: beide reproduzieren exakt, nur die Wurzel-Identität ist neu | 0,109218 | 0,148198 | §5 „Re-Baseline 2026-09-03“ |

**Nachtrag `sep02` — die `aug30`-Wurzel ist eine undeklarierte
Re-Baseline.** Zwischen der `aug29`-Wurzel (0,106720 / 0,146506, im
LF5-Eintrag datiert deklariert) und dem `aug30`-Messstand (0,106400 /
0,146580) liegt ein Wurzelwechsel, den kein Abschnitt nennt — obwohl
LF8/LF9 den fälligen Neu-Export nach den Prod-Löschungen ausdrücklich
als „erklärte Re-Baseline“ ankündigen (Vorschau 0,107995) und §2 wie
`tintenfolger.md` §6 einen datierten Eintrag verlangen. Rekonstruieren
lässt er sich nicht: die Wurzeln sind gitignored, und bis `sep02` trug
keine Kennzahl die Identität ihrer Basis. **Bis zur Antwort des Autors
gilt: undeklarierte Re-Baseline — Zahlen ab `aug30` sind nur
untereinander vergleichbar**, nicht gegen `aug29` und früher. Der
`aug30`-Eintrag selbst bleibt unverändert stehen (append-only); was sich
ändert, ist ihre Lesart. Verhindert wird die Wiederholung durch die
Kopfregel oben.

**Nachtrag `sep02` — die lokal liegende Wurzel war nicht die der
Headline.** Die Fixture-Wurzeln, die bis heute in dieser Arbeitskopie
lagen, tragen `exported_at` 2026-08-14, also den Stand VOR den
Rechteck-Reparaturen (#471) und dem Re-Baseline (#472); auf ihnen misst
der Bench 0,108091 / 0,148489 — die `aug15`-Wortzahl und eine
Paar-Zahl, die in keinem Eintrag steht. Wer die §15-Headline
reproduzieren will, baut die Wurzeln zuerst neu; die `sep02`-Zeile oben
ist genau dieser Lauf. Auch das ist ein Argument für die Kopfregel: eine
Zahl ohne `exported_at` sagt nicht, welche Platte sie gemessen hat.

### Was gemessen wird — und in welchem Rahmen

Ein **Kandidat** ist eine automatische Wortbahn über einem Specimen-Crop
(wörtlich eine `word_instances`-Zeile: Strokes + Registrierung + xh);
der **Maßstab** ist die manuell per S-Pen nachgefahrene `authored`-Bahn
desselben Specimens. Verglichen wird NIE in den gespeicherten
`(u,v)`-Labels (die Registrierung ist Composer-Buchhaltung): jede Bahn
wird über ihre EIGENE Registrierung nach Crop-px und von dort in den
**Bench-Frame** gemappt (`xh = baseline_y − midband_y`, Grundlinie =
`baseline_y − rect[1]` aus der eingefrorenen `word.json`) — der Frame
hängt damit nur an committeten Daten, ein veralteter Export kann das
Lineal nicht korrumpieren.

### Die Maße (Definitionen verbatim; keine referenziert publizierte Zahlen)

- **`dtw_xh`** — unconstrained DTW, euklidische Punktdistanz in xh
  (nicht quadriert), symmetric-1-Schritte, beide Enden verankert, kein
  Band; **normalisiert durch die Länge T des optimalen Warping-Pfads**
  (die LDTW-Normalisierung aus PEN-Net Eq. 1). Beide Seiten vorher
  arc-length-uniform resampelt (`TRACE_RESAMPLE_UNITS`; Startwert 0,02
  xh, einmaliger dokumentierter Schrittweiten-Sweep 0,02/0,03/0,05 im
  Baseline-Lauf). **Nur vorwärts** — die Richtung ist Duktus-Wahrheit;
  `dtw_reversed_better` (Kandidat rückwärts besser?) ist eine reine
  Report-Spalte. QC-Spalte `dtw_max_absorption` (max. Punkte einer
  Seite auf EIN Sample der anderen — der Singularitäts-Wächter der
  Konkatenation). EIGENER Name, bewusst nicht „LDTW": Resampling und
  xh-Einheit machen die Zahl mit publizierten Werten unvergleichbar.
- **`aiou`** — papertreu nach PEN-Net §3.1, gegen die eingefrorene
  **Tintenmaske** (`ref_mask.png`), nie gegen eine Referenzbahn:
  Kandidat 1 px gerastert (Pen-Lifts nie überbrückt), 3×3-Dilatation
  iterativ, `max_k IoU(ink, dilate^k(cand))`. Funktioniert deshalb auf
  allen Wörtern ohne Nachfahrung; Raster = Crop-px (mitreportet).
- **Chamfer, beide Richtungen getrennt** — `chamfer_cand_ref_xh`
  (Precision: liegt der Kandidat auf der menschlichen Bahn) und
  `chamfer_ref_cand_xh` (Recall: deckt er alles ab — ein fehlender
  i-Punkt bläht NUR diese Hälfte). Kein symmetrisches Mittel.
- **Strich-Behandlung** — Marken (nicht-erster Strich, komplett über
  `DIACRITIC_MIN_Y`, Bogen ≤ 0,8 xh: i-Punkt/-Strich, Umlaut,
  u-Deckstrich) werden VOR dem Body-DTW herausgelöst
  (Delayed-Strokes-Praxis; entschärft zugleich die Ordnungsfalle der
  deferred Diakritika der Engine) und per Zentroid mit Refusal
  gematcht (Radius 0,6 xh, Margin 0,25 xh). Body beider Seiten in
  Schreibreihenfolge konkateniert; Pen-Lifts bleiben AUSSERHALB der
  DTW-Kosten → `lift_delta`, `lift_pos_err_xh`.
- **Fehlerzähler** (je: ref/cand/matched/missing/spurious/ambiguous +
  Median-Positionsfehler): **Kreuzungen**
  (`landmarks.landmark_crossings`, Schwellen UNVERÄNDERT aus dem
  §13a-Zensus; Match 0,55 xh als Eins-zu-eins-Assignment über beide
  POPULATIONEN — die Refusal-Marge gehört allein den Marken, deren
  Einzelziel-Rahmen sie gebaut wurde; präzisiert nach dem ersten
  Identitätslauf, s. Baseline unten), **Marken** (s. o., Match mit
  Refusal 0,6/0,25 xh), **Retraces**
  (`core.geometry.detect_retrace_pairs`, prox 0,15 xh, ≥ 3 Paare;
  Zonen-Matching wie Kreuzungen; robusteste Zahl `retrace_arc_ratio`).
- **Validierung ohne Referenz-Implementierung:** Es existiert weltweit
  keine (PEN-Net-Repo: nur Training; TRACE: kein Repo) — die
  Unit-Tests kalibrieren gegen synthetische Verzerrungen nach PEN-Nets
  eigenem Fig.-1-Rezept (halbe Punkte um festen Betrag verschoben:
  AIoU muss deutlich fallen, wo RMSE konstruktionsbedingt flach
  bleibt).

### Split (append-never)

`TRACEBENCH_DEV_IDS` = **die · laden · linken · mit · muß · und ·
unter · Wer · will · zwei** (die 10 am 2026-08-13 nachgefahrenen
Wörter) — committete Konstante. Jedes SPÄTER nachgefahrene Wort ist
per Definition Bestätigungsmaterial und wandert NIE in den Dev-Satz
(eine nach den Zahlen umdefinierbare Rückhaltemenge ist keine).
`--split confirm` verweigert unter 5 Wörtern; Startup-Assertion: jede
Dev-Id muss als authored, nicht-`frame_stale` Zeile im Artefakt sein —
sonst harter Fehler (das Lineal hat ein Wort verloren). Benannte
Abdeckungslücke des Dev-Satzes: kein Umlaut, kein langes ſ, ein
einziger Versal — erster Punkt des Bestätigungs-Briefs.

### Kriterien (relativ, gepaart je Wort gegen die Chain-Baseline)

| Rolle | Größe | Schwelle |
|---|---|---|
| Primär (Nutzen) | `dtw_xh`, Median der gepaarten Differenzen | ≥ 20 % relativer Fall |
| Co-Primär (Gate) | `marks_missing` gesamt | kein Netto-Anstieg |
| Co-Primär (Gate) | `cross_missing + cross_spurious` gesamt | kein Netto-Anstieg |
| Kosten | p90 der gepaarten `dtw_xh`-Differenzen | ≤ +10 % |
| Kosten | `aiou`-Median · `chamfer_ref_cand`-Median | fällt nicht |
| Kosten | `retrace_arc_ratio`-Abstand zu 1,0 | wächst nicht |
| Sanity | `dtw_reversed_better` | 0 |
| Sanity | failed/skipped-Wörter | kein Netto-Anstieg |

Bei n = 10 ist der Median der gepaarten Differenzen die ehrliche
Statistik; ein Sign-Test wird berichtet, nie als Gate gelesen. **Ein
Strukturdefekt (verlorene Marke, verlorene/erfundene Kreuzung,
kollabierter Deckstrich, doppelter Strich) vetot jeden
Distanzgewinn.**

### Kill-Kriterien

- Geometrie besser, aber Marken/Kreuzungen verloren → die Änderung ist
  verworfen, nicht nachgestimmt (Struktur schlägt Distanz).
- Ein Gewinn überlebt den Bestätigungssatz nicht → verworfen (§11b
  wörtlich).
- `authored` vs. `authored` ist keine exakte Identität (dtw = 0, alle
  Zähler matched) → das LINEAL ist kaputt; keine Kandidaten-Zahl wird
  gelesen, bis es repariert ist.

### Freeze-Deklaration

Mit dem Commit der ersten Baseline-Tabelle friert das Lineal:
`tools/tracebench/{metric,frames,counters,sets}.py`,
`tools/pairlab/landmarks.py`, `core/geometry.py`,
`core/quality_suetterlin.py` (der Retrace-Zähler importiert dessen
`MIN_RETRACE_PAIRS`) und die Fixture-Roots. Jede spätere Änderung an einem davon ist eine datierte
Re-Baseline (wordbench UND tracebench — die Roots sind geteilt).
VOR diesem Commit sind Lineal-Bugfixes frei: ein kaputter Frame beim
ersten Lauf ist Debugging, kein p-Hacking — der Unterschied ist HIER
festgehalten, nicht hinterher.

### Was der Bench nicht beantwortet

Einen historisch falschen, aber glatten Duktus sieht kein Bahnmaß
(bildsynthese-und-stiftbahn.md §7); das Endkriterium bleibt der blinde
Paarvergleich nach humanbench-Methode (Folger ununterscheidbar vom
manuellen Nachfahren) — mit dem benannten Bias, dass der Autor eigene
Nachfahrungen beurteilt (Abkühl-Abstand oder Zweitrichter).

### Baseline `aug14` — der Kettenfit gegen die Hand (Freeze-Akt)

**Vorspiel, wie §14 es vorsah:** Der erste `--candidate authored`-Lauf
schlug an — auf `unter`/`mit`/`linken` verweigerte der Kreuzungs-Matcher
die IDENTITÄT (je 2 missing/spurious/ambiguous), weil zwei ECHTE
Kreuzungen dieser Wörter näher als die 0,20-xh-Refusal-Marge beieinander
liegen und `nearest_unique_point` dann selbst bei Distanz 0 verweigert.
Diagnose: Die Marge gehört dem Einzelziel-Rahmen der Landmarken („dieser
Duktuspunkt → WELCHER Ast"); Kreuzungs- und Retrace-Zählung sind ein
anderer Rahmen — beide Seiten tragen die Population DESSELBEN Detektors,
und zwei Strukturen eine Strichbreite auseinander sind zwei Strukturen,
keine Ambiguität. Reparatur (im vorregistrierten freien Fenster VOR der
ersten Baseline): `frames.match_points_one_to_one` — greedy nach
aufsteigender Distanz, Radius-Cap 0,55 xh, eins-zu-eins; Marken behalten
die Refusal-Semantik. Danach: **Identitäts-Gate PASS** (dtw 0, beide
Chamfer 0, alle Zähler voll gematcht, `direction_uncertain` 0 — die 10
Nachfahrungen stimmen überall mit der Duktus-Richtung des Priors
überein).

**Fixture-Qualitätsbefund `marks_uncertain` (4/10):** `zwei`, `und`,
`unter`, `muß` — die Slots erwarten eine Marke (i-Strich bzw.
u-Deckstrich), die authored-Bahn trägt keinen eigenen schwebenden
Strich: der Autor hat die Marke verbunden gezeichnet bzw. unterhalb der
Diakritika-Schwelle angesetzt. Kein Kandidatenfehler; ihre Marken-Zähler
sind flag-markiert. Für den Bestätigungssatz gilt der Hinweis: Marken
mit eigenem Absetzen zeichnen, wie die Tafel es tut.

**Die erste Baseline** (`--candidate chain --split dev`, Schritt 0,02,
446 s, 10/10 gescort, 0 failed):

```
dtw_xh_median:   0.061985    aiou_median:              0.6831
dtw_xh_p90:      0.261818    chamfer_cand_ref_median:  0.0398
dtw_xh_worst:    unter 0.4389 chamfer_ref_cand_median: 0.0467
marks_missing:   0  (+1 spurious)
cross_missing:   7   cross_spurious:   19
retrace_missing: 4   retrace_spurious: 21
retrace_arc_ratio_median: 1.513
lift_delta_total: 3  dtw_reversed_better: 0  dtw_max_absorption_max: 132
```

Je Wort (dtw · aiou · cross m/s · retrace-Ratio): unter **0,439** ·
0,676 · 0/7 · 1,51 — laden 0,075 · 0,686 · 0/8 · 1,75 — muß **0,242** ·
0,680 · 2/0 · 0,24 — zwei 0,076 · 0,602 · 2/1 · 1,86 — die 0,077 ·
0,622 · 0/3 · 1,71 — mit 0,042 · 0,756 · 1/0 · 0,53 — und 0,049 ·
0,696 · 0/0 · — — linken 0,049 · 0,745 · 1/0 · 1,03 — Wer 0,044 ·
0,675 · 1/0 · 0,80 — will 0,045 · 0,755 · 0/0 · 2,15.

**Lesart — die vorregistrierte Erwartung in Zahlen:** Die Punktdistanz
ist meist ordentlich (Median 0,062 xh); die Beschwerde sitzt in der
STRUKTUR. Die Kette erfindet 19 Kreuzungen und 21 Retrace-Zonen, die
die Hand nicht schreibt, und retraced 51 % mehr Bogen als der Autor
(`retrace_arc_ratio` 1,51) — Kollaps-Doppelungen und
Verbinder-Schleifen, nicht Mess-Rauschen. Zwei Wörter tragen den p90:
`unter` 0,439 (der bekannte Kollaps-Probefall, `dtw_max_absorption`
132 — die Singularitäts-Wache zeigt genau dorthin) und `muß` 0,242
(ß-Schleife, dazu 2 verlorene Kreuzungen). Das sind die Ziele der
Folger-Arme (①–⑧): Struktur zuerst, Distanz als Wächter.

**Schrittweiten-Sweep (einmalig, dokumentiert):** 0,02 → 0,03 → 0,05
bewegt `dtw_xh` nur 0,0620 → 0,0631 → 0,0650 (+5 %) und `aiou` gar
nicht; die Kreuzungszähler wackeln um ±2; das Retrace-Bogen-Maß hängt
dagegen klar am Schritt (1,51 → 1,37 → 1,17 — gröbere Abtastung
verschluckt schmale Zonen über die ≥-3-Samples-Schwelle). **0,02 bleibt
der gepinnte Schritt** — fein genug fürs Strukturmaß, und die Laufzeit
(447 s vs. 387 s über 10 Wörter) kauft nichts, was die Vergleichbarkeit
wert wäre.

**Hiermit friert das Lineal** (die Freeze-Deklaration oben ist aktiv):
Metrik-Module, `landmarks.py`, `core/geometry.py`,
`core/quality_suetterlin.py`, Fixture-Roots. Jede spätere Änderung ist
eine datierte Re-Baseline. Artefakte des Laufs:
`temp/tracebench-baseline-chain.{json,csv}` (gitignoriert), Kommandos in
`tools/tracebench/README.md`.

### Vorregistrierung der Folger-Arme (`aug14`, VOR dem ersten Sweep)

Das Experiment-Protokoll für die Verfeinerungsstufe
(`tools/pairlab/follow.py`,
[`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) §3),
festgehalten
BEVOR irgendein Arm gelaufen ist. Es gilt die Ein-Knopf-Regel (§11c/§11d:
dieses Projekt lernt nur aus Ein-Faktor-Leitern) und die §14-Kriterien
oben — gepaart je Wort gegen die eingefrorene `aug14`-Chain-Baseline,
**ein Strukturdefekt vetot jeden Distanzgewinn**, Adoption erst nach dem
Bestätigungssatz.

**Framing (damit das Experiment sich nicht selbst falsch liest):** Die
Baseline zeigt die Beschwerde in der STRUKTUR (19 erfundene Kreuzungen,
21 erfundene Retrace-Zonen, Bogen-Verhältnis 1,51) und in zwei
Kollaps-Wörtern (`unter` 0,439 · `muß` 0,242); die Fläche der
Punktdistanz ist eng (Median 0,062). Erwartete Gewinne sitzen in den
Ausreißern und den Struktur-Zählern; ein Arm, der nur den Median poliert
und Struktur verliert, ist per Veto tot.

**Reihenfolge der Arme** (v1 ändert genau EINE Sache: reg → prox):

| # | Knopf | Stufen | Pflicht-Kostenspalten |
|---|---|---|---|
| ① | λ_prox | {0 · 1 % · 10 % · 50 % von e_geo am Solve-1-Optimum (gradlab-Zerlegung) · Chain-Kontrolle} | Zick-Zack-Sichtung, stranded_anchors |
| ② | rounds | 1 / 2 / until-still (+ absteigende λ-Schedule als Unterarm) | Rundenprotokoll (Motion je Runde) |
| ③ | samples/Anker | 1,5 / 2,5 / 4 | Laufzeit |
| ④ | coverage | 0,3 / 0,6 / 1,0 | **stranded_anchors** (§11a: 32× anti-aligned — Reg-Release nimmt die Bremse) |
| ⑤ | overlap | 0,2 / 0 | §13a-Kreuzungshöhen-Statistik auf die/laden/und (§13-Bremse-Hypothese) |
| ⑥ | landmark | 0 / kalibriert, Ziele = extrapolierte Schnittpunkte (nie rohe Branch-Points) | Drop-Reasons der Korrespondenz |
| ⑦ | width | Term wie Chain / als Modulator des Ridge-Pulls | Width-Residual auf Hochkrümmungs-Samples |
| ⑧ | bind | 0 / kalibriert — NUR falls Zick-Zack λ_prox überlebt | §11d-Statistik in der Trace-Währung neu messen (Pflicht) |

**Erwartete Fehlermodi je Wort** (benannt, damit ein Negativ lesbar ist):
`unter` Stapel-Kollaps (max_absorption 132) · `laden` eingefrorene
Kreuzungshöhe (+8 spurious) · `muß` ß-Schleifen-Refusal (2 verlorene
Kreuzungen) · `Wer` Retrace-Prefix ins Leere · `die`/`mit`/`will`/
`linken` i-Marken-Attribution · `mit`/`unter` kollabierter t-Deckstrich ·
`zwei` Grat-Reiten (Width-Residual-Spalte) · `will` Retrace-Ratio 2,15.

**Kill-Kriterien der Formulierung**
([`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) §3):
bestes kalibriertes Setting verliert den gepaarten Sign-Test oder ist
auf > 2/10 Wörtern schlechter ODER erzeugt einen neuen Strukturdefekt
auf ≥ 2 Wörtern → Formulierung verworfen, nicht nachgestimmt. λ_prox = 0
≈ bestes λ_prox → die Release-Prämisse ist widerlegt; das ehrliche
Negativ kommt hierher, und die nächste Hypothese ist die
Attributions-/Sampling-Schicht, nicht mehr Gewichts-Tuning.
stranded_anchors über der Chain-Baseline → der Arm fällt, unabhängig von
jeder anderen Zahl.

**Was ein Arm-Lauf abliefert:** die `--compare`-Paartabelle gegen
`temp/tracebench-baseline-chain.json`, die Kostenspalten des Arms, und
einen datierten Eintrag HIER — auch (gerade) bei einem Negativ.

**Nachtrag 2026-09-03 — die Arme ②③④⑦⑧ sind abgeschrieben
(Autor-Entscheid).** Von den acht hier vorregistrierten Armen wurden fünf
nie einzeln gemessen: ② · ③ · ④ · ⑦ · ⑧. Sie bleiben es auch. Der Grund
ist kein Zeitmangel, sondern ein Ergebnis: die fünf sind allesamt
GEWICHTS-Arme derselben Formulierung, und genau diese Formulierung haben
①⑤⑥⑥b⑨ erschöpfend negativ beantwortet — Arm ⑨ schloss die Reihe mit dem
Route-A-Fazit ab, dass der Kettenfit am struktur-sicheren Optimum DIESER
Formulierung steht (dtw-Δ exakt 0). Ein weiterer Gewichts-Sweep könnte
das nur bestätigen; was die Route seither bewegt hat, waren
Formulierungs- und Evidenz-Änderungen (K-A · K-B · K-C · K0-S), nicht
Gewichte. Die Abschreibung stand bis heute nur auf
[`verfahren-kette.md`](verfahren-kette.md) und ist damit hier im Journal
angekommen; die Registerzeile oben trägt sie, die Rettungswege
`tintenfolger.md` §7.9, der Status §7.11. **Wiederaufnahme nur mit einer
frischen Vorregistrierung**, und die bräuchte einen Grund, den die
Gewichts-Familie bisher nicht geliefert hat — eine neue Formulierung, in
der ein Gewicht überhaupt etwas anderes tun kann.

### Arm ① `aug14` — die λ_prox-Leiter: Formulierung v1 verworfen, der Tinten-Zug validiert

Erster Lauf des vorregistrierten Protokolls — mit EINER benannten
Abweichung in der Sprossen-Wahl: Die Vorregistrierung wollte λ so
kalibrieren, dass e_prox ≈ {1 %, 10 %, 50 %} von e_geo AM
Solve-1-Optimum liegt; an einem Restart ist das aber schlecht
definiert, weil e_prox(x0) dort per Konstruktion 0 ist (δ = 0) und der
Zielwert erst am unbekannten Folger-Optimum entsteht. Gefahren wurde
deshalb die Dekaden-Leiter **{0 · 0,01 · 0,1 · 1,0} × Chain-λ** und je
Sprosse das REALISIERTE Verhältnis am Ende gelesen — die
§11c-konforme Lesart (am Optimum messen statt per Analogie wählen),
als Abweichung hier festgehalten statt wegdefiniert. Rounds 2, alles
andere Chain-Default; je Sprosse `--compare` gepaart gegen die
eingefrorene `aug14`-Baseline; Artefakte je Sprosse in der Chronik.

| λ_prox | `dtw_xh` Δmed (gepaart) | Sign | `aiou` | `cross_missing`+`spurious` | `retrace_arc_ratio` |
|---|---|---|---|---|---|
| Chain (Referenz) | — | — | 0,683 | 7+19 = 26 | 1,51 |
| 0,0 | +0,0001 | 6/4 p=0,75 | **0,784** | 8+43 = **51** | **3,04** |
| 0,01 | +0,00001 | 5/5 p=1,0 | 0,782 | 9+57 = **66** | 2,58 |
| 0,1 | +0,00002 | 5/5 p=1,0 | 0,778 | 10+52 = **62** | 2,55 |
| 1,0 | −0,0008 (−1,5 %) | 3/7 p=0,34 | 0,777 | 10+33 = **43** | 2,09 |

**Verdikt nach den vorregistrierten Kriterien — verworfen, nicht
nachgestimmt:** Jede Sprosse reißt das Co-Primär-Gate (Netto-Anstieg
`cross_missing + cross_spurious`, 26 → 43–66), und das Primärkriterium
(≥ 20 % dtw-Fall) ist mit bestenfalls −1,5 % nirgends in Sicht. Die
beiden Kollaps-Wörter heilen nicht (`unter` 0,439 → 0,417, `muß`
0,242 → 0,236). Marken bleiben überall vollständig (0 missing),
`dtw_reversed_better` überall 0.

**Was der Arm POSITIV bewiesen hat:** Der Tinten-Zug wirkt — AIoU
steigt auf JEDER Sprosse um ~+0,10 (0,683 → 0,777–0,784): punktweise
schmiegt sich die freigelassene Bahn deutlich enger an die Tinte. Der
Preis ist erfundene STRUKTUR (Zick-Zack-Kreuzungen, verdoppelte
Züge) — die dokumentierte Degenerierung, jetzt beziffert, und schon
1 % Chain-λ ist keine Bremse (66 statt 51 bei λ=0 liegt im Rauschen
der Zonen-Zerlegung).

**Prämissen-Lesart (die λ=0-Probe):** λ=0 ist NICHT ≈ bestes λ — die
Struktur verschlechtert sich monoton mit fallendem λ. Die
Release-Prämisse ist damit in verschärfter Form bestätigt: Die
Form-Regularisierung hält nicht nur die Bahn von der Tinte fern,
sie ist derzeit auch das EINZIGE, was die Struktur zusammenhält.
Der vorregistrierte nächste Schritt gilt wörtlich: Die Struktur muss
aus den DATENTERMEN kommen — Arm ⑤ (Overlap-Hypothese §13) und vor
allem Arm ⑥ (Landmark-Term mit extrapolierten Schnittpunkt-Zielen),
BEVOR irgendeine weitere λ-Feinabstimmung sinnvoll ist. Kein Default
wird adoptiert; `FOLLOW_*` bleibt `provisional`.

### Arme ⑤ + ⑥ `aug14` — Overlap freigesprochen, die Korrespondenz-Kappe gefunden

**Arm ⑤ (Overlap {0,2 · 0}, ein Faktor gegen die λ=1,0-Schwester):** Die
§13-Hypothese „Overlap als selbstgebaute Bremse“ ist BEANTWORTET — der
Term ist es nicht. Ihn abzuschalten macht alles mild besser (isoliert:
dtw −0,2 %, Sign 6/8; Kreuzungen m+s 43 → 38, Retrace-Ratio
2,09 → 1,87), aber gegen die Chain-Baseline bleibt das Struktur-Veto
(26 → 38). Keine Adoption; der Freispruch des Terms ist der Befund.

**Arm ⑥ (Landmark 0 / kalibriert, extrapolierte vs. rohe Ziele):**
Zwei Vorstufen, beide gemessen statt geglaubt: (a) Die Kalibrierung
(Parität w = 0,507; Sprossen {0,005 · 0,051 · 0,507}) lief nach der
§11c-Disziplin am Optimum. (b) Die Extrapolation feuerte auf echter
Tinte zuerst 0/21 — Diagnose auf den realen Skeletten ergab drei
Mechanismen (euklidisches Annulus-Verschweißen der Schenkel; Thinning
spaltet eine Kreuzung in zwei Y-Junctions mit 1,2–1,7 Strichbreiten
Brücke; Sehnen- statt Krümmungstoleranz), Fix per geodätischem Walk +
krümmungs-abgeleiteter 35°-Toleranz → 8 der 9 verfeinerbaren
Junctions feuern (Verschiebungen 2,6–4,5 px, im publizierten
Junction-Bound). Messung dann: mittlere Sprosse isoliert NULL
(p = 1,0, ext ≡ raw im Rauschen); volle Parität punktweise SIGNIFIKANT
schlechter (dtw +0,9 %, Sign 8/9, p = 0,039) bei milder
Strukturlinderung (m+s 43 → 39, bester Folger-Wert — Veto vs. Baseline
26 bleibt). Keine Adoption, `FOLLOW_*` bleibt `provisional`.

**Der Befund, der beide Arme überragt — die Korrespondenz-Kappe:**
12 der 21 Landmark-Korrespondenzen der Dev-Wörter zeigen auf Tinte,
die GAR KEINE Kreuzung trägt (5 Touch-Points mit 2 Schenkeln, 7
T-Junctions mit 3) — die Bahn kreuzt sich dort, die Tinte nur berührt
sich. Solange die Korrespondenz diese Klassen nicht kennt, zieht jeder
Landmark-Zug an der Hälfte der Ziele in eine Struktur, die es nicht
gibt — das deckelt jeden möglichen Effekt und erklärt das
Voll-Paritäts-Ergebnis. **Nächste vorregistrierte Hypothese:
Klassenbewusstsein der Korrespondenz** (Touch-Points/T-Junctions gar
nicht erst als Kreuzungsziele; folger-seitig umsetzbar, die
eingefrorene `landmarks.py` bleibt unberührt) — NICHT mehr Gewicht,
nicht mehr λ-Feinabstimmung. Artefakte: Chronik `arm5-overlap` +
`arm6-landmark`.

### Arm ⑥b `aug14` — Vorregistrierung: Klassenbewusste Korrespondenz

Geschrieben und committet VOR der ersten Zahl dieses Arms (§11b-Disziplin).

**Hypothese (aus der Korrespondenz-Kappe des ⑤/⑥-Eintrags):** Die Kappe
ist die bindende Schranke des Landmark-Terms. Erwartung, falsifizierbar:
Mit klassenbewusster Korrespondenz — Touch-Points und T-Junctions tragen
Gewicht 0 — verschwindet die punktweise Verschlechterung der vollen
Parität (Arm ⑥: dtw +0,9 %, Sign 8/9, p = 0,039 gegen die
λ=1,0-Schwester), und die milde Strukturlinderung (m+s 43 → 39) bleibt
oder verbessert sich.

**Umsetzung (folger-seitig, das Lineal unberührt):** neuer Zielmodus
`extrapolated_classed` in `tools/pairlab/follow.py` — die extrapolierte
Zielbildung selbst unverändert, danach Gewicht 0 für jede Zeile, deren
Verfeinerungsgrund eine By-Design-Nichtkreuzung der Tinte ist
(`LANDMARK_NONCROSSING_REASONS` = `touch_point` · `t_junction`); die
1/σ²-Gewichte der behaltenen Zeilen werden über die BEHALTENEN auf
Mittel 1 renormiert. Gewicht 0 wirkt über das bestehende Pre-Whitening
(√w skaliert Operator-Zeile UND Ziel), also ohne jede Änderung an
`chain.py` oder der eingefrorenen `landmarks.py`. Die Walk-Fehlschläge
(`few_branches` · `no_continuation_pair` · `no_junction` ·
`ill_conditioned` · `far_from_branch`) behalten ihr rohes Ziel wie
bisher — dort KANN die Tinte eine Kreuzung tragen, nur die Verfeinerung
fand sie nicht.

**Protokoll:** Kalibrierung nach §11c am eigenen Optimum der
λ=1,0-Schwester (Term inert, classed-Parität gemessen — die Parität
ändert sich, weil `e_landmark` nur noch die behaltenen Zeilen zählt);
zwei Sprossen {0,1·Parität · Parität}, Basis identisch mit Arm ⑥
(prox 1 · rounds 2 · coverage 0,3). Gepaart über die 10 Dev-Wörter
gegen die λ=1,0-Schwester UND die eingefrorene Chain-Baseline;
Co-Primär-Gates, Kosten-Wächter und Struktur-Veto unverändert.

**Kill-Kriterien:** Bleibt die volle classed-Parität punktweise
signifikant schlechter als die Schwester → die Kappe war nicht die
bindende Schranke, Hypothese verworfen — und mit ihr die Gewichts-Route
des Landmark-Terms in dieser Formulierung (die nächste Hypothese wäre
dann die Korrespondenz-Bildung selbst, nicht ihr Gewicht). Steigen
`marks_missing` oder `cross_missing+spurious` netto gegen die
Schwester → verworfen. Keine Adoption eines `FOLLOW_*`-Defaults ohne
Owner-Go, unabhängig vom Ausgang.

### Arm ⑥b `aug15` — die Kappe WAR die Schranke: klassenbewusst ist der Term punktweise kostenlos, adoptiert wird trotzdem nichts

**Messung (Protokoll wie vorregistriert):** classed-Parität am inerten
Optimum 0,3704 (Kalibrierung §11c im eigenen Modus; der Zensus ist
exakt die Kappe: 8 ok · 1 `no_continuation_pair` · 7 `t_junction` · 5
`touch_point` = 12/21 klassifiziert raus — in den re-linearisierten
Runde-2-Problemen, deren Korrespondenz der frische Detektor-Lauf neu
bildet, 11/15). Sprossen {0,037 · 0,370}, Basis prox 1 · rounds 2 ·
coverage 0,3, gepaart über die 10 Dev-Wörter.

**Ergebnis — die Vorhersage trifft ein:** Die volle classed-Parität
ist gegen die λ=1,0-Schwester punktweise NICHT mehr schlechter
(dtw Δ-Median 0,000, Sign 4/2 bei 4 Ties, p = 0,69; die per-Wort-Deltas
sind gemischtes Rauschen ±0,002 — Arm ⑥ voll war 8/9 schlechter,
p = 0,039), bei erhaltener Strukturlinderung: cross m+s 43 → 39 (der
beste Folger-Wert, jetzt ohne punktweise Kosten), Marken 0 → 0,
AIoU/Chamfer flach. Der Schaden des Arm-⑥-Volllaufs kam also aus den
12 falschen Zielen, nicht aus dem Gewicht. Ehrlich daneben: (a) die
Mittelsprosse 0,037 ist isoliert strukturell SCHLECHTER als die
Schwester (m+s 43 → 47) — die Zähler sind über die Leiter nicht
monoton; (b) der Retrace-Ratio-Abstand zu 1,0 wächst auf beiden
Sprossen (1,09 → 1,32 bzw. 1,46) — der Kosten-Wächter meldet, dass
der Term Retrace-Zonen leicht auseinanderzieht.

**Verdikt:** Hypothese BESTÄTIGT im falsifizierbaren Sinn — und
trotzdem keine Adoption: gegen die eingefrorene Chain-Baseline steht
das Struktur-Veto in voller Höhe (cross m+s 26 → 39, Retrace-Gap
0,51 → 1,32; dtw −1,5 % rel, n. s.; AIoU +0,094 = der validierte
Tinten-Zug). Der Landmark-Term zielt jetzt sauber und kostet nichts —
aber die ERFUNDENE Struktur des Folgers entsteht nicht an seinen
Zielen, sondern in den Datentermen des Form-Release selbst (der
Arm-①-Befund, hier ein zweites Mal bestätigt). `FOLLOW_*` bleibt
`provisional`; für jeden KÜNFTIGEN Landmark-Arm ist
`extrapolated_classed` der empfohlene Modus (kostenlos schlägt
schädlich), der Default bleibt bis zum Owner-Go unverändert.
Artefakte: Chronik `arm6b-classed`.

### Struktur-Zähler v2 `aug16` — Vorregistrierung & Re-Baseline-Deklaration

Anlass: das manuelle Owner-Audit der 10 Dev-Wörter über die
Duell-Seite — die erste systematische Prüfung der Zähler gegen das
Duktus-Wissen statt gegen sich selbst. Befund: v1 zählte KONSISTENT
(dieselben Detektoren auf beiden Seiten, Identitäts-Gate intakt), aber
teils die falschen Kategorien: ein 17,8°/0,48-xh-Grenzgänger am
unter-e ist eine Retrace-Ablösung, keine Kreuzung; die
15°-Winkel-Schwelle schneidet am linken-k mitten durch dieselbe
Abzweig-Geometrie (12,1°/14,0°/9,0° verworfen, 82°/72° gezählt); der
mit-Kringel gegen den t-Anstrich (Partner-Lücke 4,3 xh entlang des
Wegs) ist Vorbeischreiben, kein Retrace; die laden-l-a-Spitze
(Pass-Arc 0,16/0,24 xh) ist eine auseinanderlaufende Spitze, keine
Zone.

**Die drei Regeln (Owner-Spezifikation, wörtlich übernommen):**

1. **Kreuzung nur bei DURCHSTOSS** — eine Linie kommt eindeutig auf
   einer Seite herein und auf der anderen wieder heraus. Formal: TLS-
   Gerade durch das ±`PIERCE_WINDOW_UNITS`-Fenster (0,25 xh, nie über
   eine Strichgrenze) JEDES Passes; die Fensterenden des jeweils
   anderen Passes müssen auf ENTGEGENGESETZTEN Seiten liegen, beide
   mit |Abstand| ≥ `PIERCE_MARGIN_UNITS` = 0,05 xh (≈ halbe
   Strichbreite: der andere Strich muss jenseits der eigenen Tinte
   wieder austreten). Beide Pässe müssen durchstoßen. Die
   15°-Winkel-Schwelle ENTFÄLLT als eigene Regel — Fenster × Marge
   implizieren einen ehrlichen Konditionierungs-Boden von
   arcsin(0,05/0,25) ≈ 11,5°, unter dem sich zwei Linien im
   Viertel-xh nicht über die halbe Strichbreite trennen und die Tinte
   die Frage selbst nicht beantwortet; die Bogen-Trennung ≥ 0,35 xh
   bleibt (der Wobble-Pin bleibt gültig). Gemessen an den Dev-Händen:
   die Owner-Streitfälle fallen richtig (der tangentiale unter-e-Ring
   raus, die und-d-Schleife bleibt), und am linken-k entscheidet EINE
   Regel statt einer Schwelle: die Schleifen-Schlüsse des Kringels
   durchstoßen (bleiben), die bloßen Abzweig-Gabelungen nicht (fallen
   — beide Klassen gleich beurteilt, was die v1-Winkelschwelle nicht
   leistete).
2. **Retrace nur bei bogen-nahem Partner** — Hin-und-zurück heißt: die
   Partner-Samples liegen entlang des Wegs UNMITTELBAR daneben.
   Pass-Klassifikation: Partner im ANDEREN Strich →
   **Überlagerung**; Partner-Lücke > `RETRACE_MAX_PARTNER_GAP_UNITS`
   = 1,0 xh → **Berührung** (Vorbeischreiben, mit oder ohne
   Tinten-Kontakt); Pass-Arc < `RETRACE_MIN_PASS_ARC_UNITS` = 0,30 xh
   → Spitzen-Graze, keine Zone. Konstanten aus der Messung: echte
   Zonen haben Lücke 0,38–0,66 und Arc ≥ 0,36; die Owner-Fälle Lücke
   1,16–8,34 bzw. Arc ≤ 0,24 — der Schnitt bei 1,0/0,30 liegt
   jeweils mitten im leeren Band.
3. **Berührung und Überlagerung sind eigene, BERICHTETE Klassen** —
   gezählt und ausgewiesen (Report/Seite), nie Teil eines Loss.

**Validierung (vorregistriert):** die Owner-Verdikte werden als Tests
gepinnt — unter-e: keine Kreuzung (tangentialer Dip); linken-k: beide
Abzweig-Klassen nach DERSELBEN Regel beurteilt; mit-t: genau EINE
Retrace-Zone im selben Strich, die Querstrich-Fälle Überlagerung,
Kringel-gegen-Anstrich Berührung; laden-l-a: keine Zone; der
Wobble-Out-and-back bleibt Retrace ohne Ring; und-d bleibt Kreuzung.
Das Identitäts-Gate (`--candidate authored`) muss exakt bestehen
bleiben. dtw/aiou/Chamfer/Marken/Lifts sind NICHT berührt.

**Re-Baseline-Deklaration:** `tools/tracebench/counters.py` verlässt
mit diesem Eintrag DATIERT den Freeze — die v1-Strukturzahlen der
`aug14`-Baseline und der Arme ①⑤⑥⑥b bleiben gültig und archiviert
(Chronik), sind aber mit v2-Zahlen NICHT vergleichbar; die
v2-Baseline-Tabelle folgt in diesem Eintrag nach der Implementierung.
`landmarks.py`, `core/geometry.py` und der Landmark-Term des Folgers
bleiben eingefroren (der Chain-Korrespondenz-Zensus §13a behält seine
eigenen Schwellen).

**v2-Baseline (Kette gegen die Hand, 10 Dev-Wörter; gemessen nach der
Implementierung, alle Verdikt-Pins grün, Identitäts-Gate PASS):**
`dtw_xh` 0,061985 med / 0,2618 p90 — byte-gleich zur v1-Baseline, wie
deklariert (nur die Strukturzähler änderten die Bedeutung). Struktur:

| Zähler | Hand (Σ) | Kette (Σ) | missing+spurious |
|---|---|---|---|
| Kreuzungen (Durchstoß) | 27 | 35 | 5+13 = 18 (v1: 26) |
| Retrace-Zonen | 15 | 18 | 2+5 = 7 (v1: 21 erfunden) |
| Berührungen | 8 | 17 | berichtet, nie Loss |
| Überlagerungen | 0 | 6 | berichtet, nie Loss |

**Nachtrag v2.1 (Owner-Audit der v2-Seite, gleicher Tag):** Drei Ringe
überlebten v2, die Abzweig-Ablösungen sind (unter-t 44,8° · mit-t
35,0° · zwei-w-Ende 24,0°). Die Regel, die sie trifft, ist die
wörtliche Anwendung des Owner-Prinzips auf den Ring selbst: Ein Ring,
dessen beide Chords EINANDER Antiparallel-Partner des
Retrace-Detektors sind (`CROSS_PARTNER_NEAR_UNITS` 0,16 xh ≈ die
eigene Proximity des Detektors, ≥ 2 Treffer beidseitig), ist der
beiläufige Selbstschnitt eines Hin-und-zurück-mit-Ablösung —
retrace-intern, keine Struktur-Kreuzung. Ein Retrace durch FREMDE
Tinte (linkens Kringel-Durchgänge) behält seine Ringe: seine Chords
partnern mit den eigenen Rückschenkeln, nicht miteinander. Gemessen
fallen exakt die beanstandeten Ringe (plus der gleichartige
linken-k-Ausgang, 53,1°; Partner-Hits 4–13 beidseitig), jeder
behaltene liest 0/0. Ehrliche Konsequenz: Für antiparallel-benachbarte
Paare steigt der effektive Ring-Boden auf die Antiparallel-Toleranz
des Detektors (25°) — alle echten Hand-Ringe liegen ≥ 45°, der
13°-Durchstoß-Pin wurde entsprechend auf die v2.1-Semantik
umgeschrieben. Zwei Entscheidungen dokumentiert: (a) Gezählt werden
Kreuzungs-ORTE, nicht -Ereignisse — linkens „runter 2× gekreuzt, dann
zurück-retraced = eigentlich 4" ist als Ereigniszählung richtig, aber
der Ort ist die stabile Währung: das Duktus-Budget hinge sonst an der
Retrace-Anzahl, und das Positions-Matching kann ko-lokalisierte
Ereignisse ohnehin nicht trennen. (b) Berührungen und Überlagerungen
stehen seither auch in der Zahlen-Tabelle der Duell-Seite.

**v2.1-Baseline (nach dem Nachtrag; Identitäts-Gate PASS, dtw
byte-gleich):** Hand 23 Kreuzungen · 15 Retrace-Zonen · 8 Berührungen ·
0 Überlagerungen; Kette 20 · 18 · 17 · 6. Missing+spurious: Kreuzungen
7+4 = 11 (v2: 18, v1: 26), Zonen 2+5 = 7. Der Löwenanteil der
v1-„Erfindungen" an den Stapel-Wörtern war RETRACE-INTERN — die
überlappenden Striche der Kette partnern antiparallel und schneiden
sich beiläufig; die präzise Klage lautet seither: 4 erfundene Ringe,
5 erfundene Zonen, 9 erfundene Berührungen (zu enges Vorbeischreiben),
6 Überlagerungen. Hand je Wort: die 1 · laden 3 · linken 3 (der
k-Ausgang fiel als Ablösung; das Soll rechnet mit denselben Zählern
und zieht mit) · mit 2 · muß 1 · und 1 · unter 3 · Wer 3 · will 3 ·
zwei 3 (= z2+w1).

Lesart (v2-Stand vor dem Nachtrag): Von den 19 „erfundenen Kreuzungen"
der v1-Kette waren 6 tangentiale Artefakte, die der Durchstoß nicht
mehr zählt — 13 echte Erfindungen bleiben die Klage. Die 21 „erfundenen
Retrace-Zonen" der v1 zerlegen sich in 5 echte Erfindungen, **9
erfundene Berührungen** (die Komposition schreibt Buchstaben zu eng
aneinander vorbei — eine präzisere Diagnose als „Retrace") und 6
Überlagerungen. `retrace_arc_ratio` med fällt 1,51 → 0,83: die Kette
retraced jetzt WENIGER Bogen als die Hand — die ehrliche Richtung,
denn die echten Hand-Retraces (t-Stamm, ß) sind lang, und die
Erfindungen sind in ihre eigenen Klassen umgezogen. Hand-seitig
rücken die Zählungen auf die Duktus-Budgets (Wer 5 → 3 = W2+r1,
muß 3 → 1 = ß-Budget, unter 5 → 4). Kandidat der Baseline ist die
verifizierte Chain-Identität (`follow --rounds 0`,
Byte-Identitäts-Pin) über den File-Provider.

### Route B T0 `aug15` — InkSight Small-p roh auf den Dev-Wörtern

Der T0-Prüfstein aus tintenfolger.md §4: das veröffentlichte
Small-p-Checkpoint (Apache 2.0), unadaptiert, CPU, über die
`tools/inksight`-Pipeline (#340) — Umgebung wie im README verifiziert
(Python 3.11 · tf-cpu 2.20.0 · tf-text 2.20.1, XLA-Flags gesetzt).
Laufzeit-Befund: `derender`/`text` ≈ 2–6 min je Wort auf 8 Kernen;
der `r+d`-Prompt (erst Texterkennung, dann Tinte) ≈ 43 min je Wort und
wurde nach EINEM Datenpunkt abgebrochen — der eine genügt für die
OOD-Diagnose: das Modell liest das Sütterlin-„Wer" als „Olomi".
Kein Call erreichte den 1024-Token-Deckel (max. 441, linken); die
Gitter-Auflösung lag bei 1,00–1,41 Crop-px je Wort.

| Kandidat | dtw med | p90 | AIoU | cross m+s | Zonen m+s | Lifts Δ |
|---|---|---|---|---|---|---|
| Kette (v2.1-Baseline) | 0,0620 | 0,262 | 0,683 | 7+4 | 2+5 | +3 |
| **InkSight derender** | **0,0956** | 0,391 | 0,697 | **9+1** | 11+2 | +21 |
| InkSight text | 0,1145 | 0,383 | 0,680 | **5+1** | 12+1 | +20 |
| routeg-Kontrolle | 0,8198 | 1,027 | 0,833 | 15+3 | 15+0 | +90 |

Lesart: (a) Roh und nie auf deutscher Kurrentschrift trainiert landet
Small-p bei **1,5× der Kette** und **8,6× vor der prior-freien
Kontrolle** — die Route-B-Prämisse (gelernte Verfahren tragen echtes
Geometrie-Wissen bei) ist damit bestätigt, nicht nur behauptet.
(b) Überraschung gegen die Paper-Ablation: der `text`-Prompt („Derender
the ink: <wort>") ist SCHLECHTER als das nackte `derender` — die
Wort-Konditionierung zieht das Modell bei einer Schrift, deren
Buchstabenformen es nicht kennt, Richtung lateinischer Schreibung
statt zur Tinte. (c) Die KREUZUNGS-Struktur des Modells ist sauberer
als die der Kette (nur 1 erfundener Ring auf beiden Prompts, text
verpasst nur 5 von 23) — was fehlt, sind die RETRACES (11–12 von 15
verloren; das Modell setzt ab statt zurückzufahren, +20 Lifts, 3–9
Striche je Wort) — exakt die Klasse, die der Duktus-Prior beherrscht.
Schlechtestes Wort beider Prompts: und (0,395/0,396 — es schreibt das
„und" als lateinisches Wortbild). Konsequenz wie in §4b geplant: T0
ist die dokumentierte OOD-Basislinie; der nächste Route-B-Schritt
bleibt das EIGENE kleine Trajektorien-Modell auf Engine-Paaren
(Fine-Tuning von Small-p ist ohne Trainingscode unmöglich).
Artefakte: Chronik `inksight-t0`; Kandidaten/Rohantworten bleiben
unter `tools/inksight/out/` (gitignored, Messschicht).

### Arm ⑨ `aug16` — Vorregistrierung: der Topologie-Wächter

Geschrieben und committet VOR der ersten Zahl dieses Arms.

**Befund, der den Arm begründet (v2.1-Zähler):** Schon die
λ=1,0-Schwester ERFINDET Struktur gegenüber ihrer eigenen
Chain-Initialisierung — Berührungen 17 → 27, erfundene Zonen 5 → 10,
Kreuzungen m+s 11 → 15 — und Arm ① zeigte, dass jede Release-Sprosse
am Struktur-Veto scheitert, während der Tinten-Zug selbst validiert
ist (AIoU +0,10 überall). Die Hypothese, falsifizierbar: **Die
Distanz-/AIoU-Gewinne des Release sind von seinen
Struktur-Erfindungen trennbar.** Der Owner-Satz dazu: Kringel,
Kreuzungen und Retraces sind duktus-fix und ändern sich durch das
Verfeinern nicht.

**Mechanismus (folger-seitig, opt-in, kein neuer Objective-Term):**
eine Runden-AKZEPTANZREGEL statt einer Kraft. Vor Runde 1 wird das
Struktur-Budget der Initialisierung gemessen — die v2.1-Klassenzählung
(Kreuzungen · Retrace-Zonen · Berührungen · Überlagerungen,
`tools.tracebench.counters` auf den assemblierten Pen-down-Polylinien
des Runs, in xh-Einheiten). Eine gelöste Runde wird nur AKZEPTIERT,
wenn keine Klassenzahl ihr Budget übersteigt; eine verletzende Runde
wird mit HALBIERTEN Reisebudgets (`max_delta`/`connector_max_delta`)
neu gelöst, höchstens zweimal; verletzt sie weiter, behält der Run die
Geometrie der Vorrunde und die Runde ist als `structure_rejected`
protokolliert (die Schleife endet — dieselbe Bewegung würde erneut
scheitern). `FollowWeights.structure_guard` (bool, default False =
byte-identisch, Pin) schaltet den Wächter je Arm zu; das Lineal misst,
der Wächter entscheidet — derselbe Zähler, keine zweite Semantik.

**Protokoll:** Sprossen prox ∈ {0,01 · 0,1} (die Release-Sprossen, auf
denen Arm ① die größten Gewinne bei tödlichem Veto zeigte) und die
1,0-Schwester als Kontrolle (der Wächter sollte auch ihren
27-Berührungs-Drift einfangen), Basis sonst Arm-⑥-identisch. Gepaart
über die 10 Dev-Wörter gegen die eingefrorene v2.1-Chain-Baseline;
`stranded_anchors` bleibt Pflicht-Kostenspalte.

**Kriterien:** Primär `dtw_xh` (Median der gepaarten Differenzen)
fällt gegenüber der Chain-Baseline; Co-Primär Marken und Kreuzungen
ohne Netto-Verschlechterung; der Wächter-KONTRAKT ist selbst messbar:
jede Klassenzahl des Kandidaten ≤ der Chain-eigenen Zahl (Berührungen
≤ 17, Zonen-spurious ≤ 5 …). Kosten-Wächter wie §14 üblich.

**Kill-Kriterien:** Blockiert der Wächter auf den Release-Sprossen
jede Bewegung (dtw im Rauschen der Kette, `max_anchor_motion` ≈ 0) →
die Gewinne WAREN die Erfindungen, Formulierung verworfen, ehrliches
Negativ. Laufen die meisten Runden in die Retry-Erschöpfung → der
Mechanismus (Akzeptanz statt Kraft) ist ungeeignet, nächste Hypothese
wäre ein differenzierbarer Abstands-Term, nicht mehr Retries. Keine
Adoption eines Defaults ohne Owner-Go.

**Ergebnis (`aug16`, beide Kill-Kriterien gefeuert — das wertvollste
Negativ der Kampagne):** Der Wächter-KONTRAKT hält perfekt: Auf allen
drei Sprossen bleibt jede Klassenzahl ≤ der Chain-eigenen (Kreuzungen
m+s exakt 7+4, Berührungen ≤ 17, Zonen ≤ 7) — zum ersten Mal besteht
ein released Folger das Struktur-Gate. Aber der Preis beantwortet die
Hypothese abschlägig: dtw-Δ gegen die Kette ist EXAKT null (Δ-Median
0,000000; 6–8 von 10 Wörtern byte-identisch, Sign-Test p = 1,0 auf
allen Sprossen), weil 13 von ~21 Runden nach Retry-Erschöpfung
zurückgewiesen wurden (26–28 Retries je Arm). Nur der AIoU-Rest der
akzeptierten, gedämpften Runden bleibt (+0,033 bei prox 0,1 — ein
Drittel des ungewachten +0,10). **Die Tinten-Gewinne des Release und
seine Struktur-Erfindungen sind nicht trennbar: die Bewegung zur
Tinte hin IST das Erfinden** — engeres Aneinander-vorbei-Schreiben
senkt die Distanz und erzeugt exakt die Berührungen, die die Hand
nicht hat. Konsequenz für Route A: Der Kettenfit steht bereits am
struktur-sicheren Optimum dieser Formulierung; die verbleibende
dtw-Lücke zur Hand ist mit „Form-Prior lösen" in keiner der fünf
gemessenen Varianten (①⑤⑥⑥b⑨) zu kaufen. Die nächsten Hebel liegen
COMPOSER-seitig (Platzierung/Joins — die Soll-Abweichler t · W ·
join-Schleifen, plus die 9 erfundenen Berührungen der Komposition
selbst) und bei fundamental anderen Kandidaten (Route B). Der
Wächter selbst bleibt als Werkzeug im Repo (`structure_guard`,
default False): er ist das erste Instrument, das einen Folger-Lauf
GARANTIERT struktur-sauber hält, und der prox-0,1-Lauf ist als
einziger struktur-sauberer Release-Kandidat auf der Duell-Seite.
Artefakte: Chronik `arm9-wächter`.

**Nachtrag `aug15` — korrigierte Attribution der Berührungen.** Die
Formulierung „die 9 erfundenen Berührungen der Komposition selbst"
oben ist falsch zugeordnet: nachgemessen mit den eingefrorenen
v2.1-Zählern über die Fixtures schreibt die KOMPOSITION der 10
Dev-Wörter nur 2 Berührungen (beide w-intern: `will` x≈1,95, `zwei`
x≈3,10) und 4 Überlagerungen (alle t-Balken-gegen-Stamm in
`mit`/`unter`) vor — keine einzige zwischen zwei Buchstaben. Der
Überschuss von 8 auf 17 Berührungen gehört dem KETTENFIT
(`touch_cand` 17 gegen Hand 8). Der Composer-Hebel bleibt real,
liegt aber bei den Schnitt-Klassenregeln und der Kopplung
(Unter-Kreuzen), nicht bei den Berührungen; Plan in
`../proposals/tintenfolger.md` §7.

### Route G `aug14` — die prior-freie Kontrolle: was der Duktus-Prior kauft

Der Kontrollkandidat aus
[`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) §4b, jetzt
gemessen. **Was gelaufen ist, ist nicht der publizierte Code:** Das
Referenz-Repo (Diaz et al. 2022) ist MATLAB 2016a+ mit Image Processing
Toolbox — MIT lizenziert, aber hier und in CI nicht ausführbar, also
wäre eine `wor()`-Zahl von niemandem nachrechenbar (Befund und
Belegstellen im §4b-Nachtrag). Gelaufen ist die eigene Minimalfassung
`tools/routeg`: eingefrorenes Skelett → Segmentgraph (benachbarte
Verzweigungspixel = EIN Knoten) → Greedy-Traversierung, drei
Entscheidungen (linkester Endpunkt · ein Skalarprodukt am Knoten ·
Absetzen bei Sackgasse), **kein gelernter Anteil, kein Template, keine
Ground Truth**. Das Kandidatenlabel heißt darum `routeg-graph`, nicht
`routeg-wor`.

Lauf: `--candidate file --candidate-file temp/routeg-t0.json --label
routeg-t0 --split dev`, Schritt 0,02, 175 s, 10/10 gescort, 0 failed.
Referenzseite identisch zur v2.1-Baseline (23 Kreuzungen · 15
Retrace-Zonen · 8 Berührungen · 0 Überlagerungen) — dieselben
eingefrorenen Zähler, also ist die Gegenüberstellung wörtlich
vergleichbar. Nach den Soll-Spalten (#353) einmal nachgemessen: **jede
Zahl byte-gleich**, nur die zwei neuen Report-Zeilen kommen hinzu
(`soll_cross_agree` 7/10, `soll_zones_agree` 6/10) — die
Report-Spalten-Regel hält also auch für diesen Kandidaten.

```
dtw_xh_median:   0.819847    aiou_median:              0.8333
dtw_xh_p90:      1.026691    chamfer_cand_ref_median:  0.0365
dtw_xh_worst:    die 1.0355  chamfer_ref_cand_median:  0.0411
marks_missing:   0   marks_spurious:   4
cross_missing:   15  cross_spurious:   3
retrace_missing: 15  retrace_spurious: 0
retrace_arc_ratio_median: 0.000
lift_delta_total: 90  dtw_reversed_better: 0  dtw_max_absorption_max: 222
touch_ref 8 / touch_cand 4 · overlap_ref 0 / overlap_cand 25
```

Je Wort (dtw · aiou · Kreuzungen gefunden/Soll · Striche
Kandidat/Hand): die **1,036** · 0,854 · 0/1 · 6/2 — linken **1,026** ·
0,821 · 1/3 · 18/2 — zwei 0,907 · 0,813 · 1/3 · 13/1 — laden 0,833 ·
0,859 · 2/3 · 11/1 — will 0,832 · 0,841 · 0/3 · 9/2 — Wer 0,808 ·
0,880 · 0/3 · 11/1 — muß 0,681 · 0,829 · 1/1 · 11/2 — unter 0,656 ·
0,829 · 1/3 · 16/2 — und 0,428 · 0,838 · 1/1 · 9/2 — mit 0,414 ·
0,801 · 1/2 · 7/2.

**Gegenüberstellung** (gleiche Wörter, gleiches Lineal). Der Kettenfit
wurde für diese Zeile am selben Tag NEU gerechnet
(`--candidate chain --split dev`, 2808 s) statt aus der v2.1-Baseline
abgeschrieben — und reproduziert sie exakt: dtw 0,061985 · aiou 0,6831 ·
p90 0,261818 · worst `unter` 0,438926 · Chamfer 0,0398/0,0467 ·
Kreuzungen 7 fehlend/4 erfunden · Zonen 2/5 · `retrace_arc_ratio` 0,830 ·
Berührungen 8/17 · Überlagerungen 0/6 · `lift_delta_total` 3. Die
Gegenüberstellung ist damit gemessen, nicht zitiert:

| | Hand (Referenz) | Kettenfit | Route G |
|---|---|---|---|
| `dtw_xh` Median | 0 (Identitäts-Gate) | **0,062** | **0,820** |
| `aiou` Median | 0,685 | 0,683 | **0,833** |
| Kreuzungen (Soll 23) | 23 | 20 · 7 fehlen, 4 erfunden | 8 · **15 fehlen**, 3 erfunden |
| Retrace-Zonen (Soll 15) | 15 | 18 · 2 fehlen, 5 erfunden | 0 · **15 fehlen**, 0 erfunden |
| Absetz-Differenz Σ | 0 | 3 | **90** |

**Lesart — die Kontrolle tut genau, was eine Kontrolle soll.** Drei
Dinge stehen nebeneinander, und nur zusammen ergeben sie einen Satz:

1. **`aiou` ist HÖHER als die der Hand gegen sich selbst** (0,833 gegen
   0,685). Das ist kein Sieg, sondern der Beweis, dass die Spalte
   Tintendeckung misst und nicht Schreiben: Die Traversierung läuft
   qua Konstruktion auf dem Skelett, die Handbahn ist ein Stiftweg, der
   die Tinte nicht deckungsgleich abfährt. **Auf der Tinte zu liegen
   ist nicht dasselbe wie sie zu schreiben** — die schärfste verfügbare
   Warnung davor, `aiou` je als Kopfzahl zu lesen.
2. **`dtw_xh` ist 13× so groß wie beim Kettenfit** (0,820 gegen 0,062).
   Das ist die Zahl, für die Route G gebaut wurde: So weit ist der Weg
   durch dieselbe Tinte, wenn niemand weiß, wie man schreibt.
   architektur.md §2 hat damit erstmals eine Messzahl statt eines
   Architektur-Arguments.
3. **Die Struktur bricht ganz weg.** 15 der 23 Kreuzungen verloren, alle
   15 Retrace-Zonen verloren (bauartbedingt — die Traversierung läuft
   jede Kante genau einmal), und 90 zusätzliche Absetzer (`lift_delta`
   zählt Körperstriche, Marken sind ausklassifiziert; über alle Striche
   gerechnet sind es 111 gegen 17). Die Hand schreibt diese Wörter in
   **1–2 Zügen**, die Kontrolle braucht **6–18**. Genau hier — nicht in
   der Distanz — sitzt der Unterschied
   zwischen „Tinte nachfahren" und „Schreiben".

**Was das für die Folger-Arme heißt:** Die Kill-Kriterien des §14 sind
gegen den Kettenfit vorregistriert, und Route G bestätigt deren
Richtung ohne sie zu berühren — der Prior schlägt die prior-freie
Kontrolle klar (der Fall „schlägt ihn NICHT klar" aus §4b tritt nicht
ein), und zwar in der STRUKTUR deutlicher als in der Distanz. Route G
ist damit erledigt als Frage und bleibt als Bodenmarke: Ein Folgerarm,
der Struktur gegen Distanz eintauscht, kann an dieser Zeile ablesen,
wo das endet.

**Grenzen dieser Zahl, ehrlich benannt:** (a) Die Kontrolle ist eine
REDUKTION des publizierten Verfahrens, keine Reimplementierung — ohne
gewichtete `π_ij`-Fortsetzung, ohne Cluster-Rang-Klassifikation, ohne
Dijkstra durch den Cluster und ohne Retrace-Modell. Die echte WOR-Zahl
läge besser, und **um wie viel, ist hier NICHT gemessen**: Die ersten
drei fehlenden Bausteine adressieren die Astwahl (also `dtw` und die
Kreuzungsspalte), das fehlende Retrace-Modell dagegen genau die beiden
Zeilen, die hier am lautesten sind — Retrace-Zonen und Absetz-Differenz.
Wer die Lücke zum Prior beziffern will, statt sie nur zu sehen, muss
diese Zahl mit MATLAB nachziehen; bis dahin ist die Aussage die
schwächere und sichere: **so weit ist der Weg mindestens.** (b) Sie ist auf
denselben 10 Dev-Wörtern gemessen wie alles andere und trägt deren
blinde Flecken (kein Umlautwort, kein langes ſ, eine Majuskel).
(c) `marks_uncertain` gilt für dieselben 4 Wörter wie in der Baseline.
Artefakte: `temp/routeg-t0.json`, `temp/tb-routeg-t0.{json,txt}`
(gitignoriert); Rezept in `tools/routeg/README.md`.

### Welle 1 · K1 `aug15` — Vorregistrierung: t-Balken-Schnitt mit Überstand

Geschrieben und committet VOR der ersten Zahl dieser Maßnahme
(Plan: `../proposals/tintenfolger.md` §7.2).

**Hypothese.** Das gebundene t unter-kreuzt, weil die
Balken-Schnittregel (`BAR_EXIT_BASES`, `core/compose.py`) den
Deckstrich exakt AN seiner Kreuzung mit dem Stamm endet — für den
Durchstoß-Zähler (`PIERCE_MARGIN_UNITS` 0,05 xh) ist ein Endpunkt
keine Kreuzung. Ein kleiner Überstand jenseits des Schnittpunkts
stellt die duktus-fixe Kreuzung wieder her, ohne die
B-Platzierung zu bewegen (deren Anker bleibt der STAMM,
`stem_launch`); der Join startet an der neuen Balkenspitze statt am
Stamm — wie auf den Platten, wo der Balken durch den Stamm läuft und
erst dahinter in die Verbindung übergeht.

**Konstante, gemessen statt gewählt.** `BAR_CROSS_OVERRUN_UNITS =
0.2`: In der authored-Referenz von `mit` (wortfinales t, der Balken
endet frei) liegt die Balkenspitze 0,16–0,22 xh rechts der beiden
Stamm-Pässe (Spitze x≈4,78 gegen Kreuzungen x≈4,56/4,62). Die
authored-Referenz von `unter` (gebundenes t) präzisiert die
MECHANIK: die Hand schreibt keinen toten Balken — der Deckstrich ist
eine Schleife (Stamm runter/retrace hoch, kleine Linksschleife auf
Mittelhöhe), deren Auslauf-Pass den Stamm DURCHSTICHT (Kreuzungen
mit Abstrich x≈4,63 und Aufstrich x≈4,70), ~0,1 xh danach frei von
der Stammtinte ist und ohne Absatz als die jul30-gemessene
16–27°-Join-Haarlinie weitersteigt. Der jul30-Ink-Befund („0,00–0,03
xh Balkentinte rechts des Stamms") und diese Bahn beschreiben
DIESELBE Tinte — verschieden ist die Topologie: die Platte hat dort
Join-Tinte, und der Stift läuft DURCH den Stamm, nicht bis an ihn.
Überstand + Join-Start an der Spitze reproduzieren diese Topologie
mit minimalem Eingriff (der Balken bleibt der authored Chart-Strich;
die Linksschleifen-Form selbst wäre eine Chart-Duktus-Frage). 0,2
liegt im Beleg-Bereich beider Wörter und komfortabel über der
Pierce-Marge.

**Erwartung.** `unter` `soll_cross` 2→3 (= Übereinstimmung mit der
Hand); `mit` bleibt 1 (das dortige Defizit ist ein Join-Effekt, K2).
Die `soll_overlap`-Einträge der t-Wörter (heute 2× `mit`, 2×
`unter`, alle Balken-gegen-Stamm) können sich umklassifizieren —
berichtet, nicht Kriterium.

**Messgrößen und Kill-Kriterien.**
(a) `soll_cross_agree`/`soll_zones_agree` JE WORT über die 10
Dev-Wörter: kein Wort außer den t-Wörtern darf seine
Übereinstimmung verlieren, sonst verworfen.
(b) wordbench `uv run python -m tools.wordbench.run --style
suetterlin --set all`: `word_loss` und `pair_loss` dürfen nicht über
Rausch-Niveau regressieren (> +0,002 auf einer Headline =
verworfen); erwartet ist Bewegung NUR in t-Wörtern.
(c) Das compose-golden-Fixture bricht bauartbedingt (gebundene
t-Geometrie ändert sich) — der Regen (`REGEN_GOLDEN=1`) ist Teil des
PRs und wird hier als deklarierte Re-Baseline geführt; er ist KEIN
Akzeptanzkriterium.
(d) Sichtprüfung der beiden t-Wörter auf der Duell-/Werkbank-Seite
(der Balken darf nicht als abgesetzter Stummel wirken).

**Ergebnis (gemessen nach dem Commit oben).** Die registrierte
Erwartung ist WIDERLEGT — und die Widerlegung ist der Fund. Auf
WORT-Ebene ändert der Überstand die Topologie exakt gar nicht: die
Kreuzungspunkte der komponierten `unter` sind vor und nach K1
byte-nah identisch ((4,72 · 0,28) und (7,70 · 0,26)), `soll_cross`
bleibt 2, die Agree-Zeilen bleiben 7/10 und 6/10. Der Grund: die
t-Kreuzung EXISTIERTE schon immer — der Stift-Weg
Balken-Rücklauf → Schnittpunkt → Join-Haarlinie ist EIN
Pen-down-Zug und durchstößt den Stamm; verbucht war sie nur beim
JOIN (`comp − Σ Buchstaben`), weil der Balken als eigener Strich am
Schnittpunkt endete. K1 verschiebt die Kreuzung in den Buchstaben
(Σ Buchstaben 1→2, die per-Letter-Zelle des gebundenen t wird 1/1
und trägt damit den Duktus-Fingerabdruck selbst; der scheinbare
„Join-Beitrag +1" bei `unter` war eine Fehlbuchung dieser
Balken-Kreuzung, kein d/e-artiger Schleifenbeitrag). Das ECHTE
Defizit (`unter` 2 vs 3, `mit` 1 vs 2) sitzt im STAMM-RETRACE: die
Hand schreibt den t-Stamm hinunter und VERSETZT wieder hinauf
(Abstrich x≈4,60, Aufstrich x≈4,65 — der Auslauf durchsticht ZWEI
Pässe und die Rückkehr kreuzt den Abstrich ein drittes Mal), die
Komposition überbrückt den Rückweg KOLLINEAR auf dem Stamm — für
den Zähler unsichtbar. Kandidat K1b (eigene Vorregistrierung, nicht
Teil dieses Ergebnisses): die generierte Stamm-Rückkehr als
versetzten Pass führen (~0,05 xh, innerhalb der Schwellzug-Breite —
auf der Platte unsichtbar, im Zähler zwei Pässe). Gates: Headline
`bench_loss` 0,110703 → 0,110992 (+0,0003, Kill-Schwelle 0,002),
`pair_loss` byte-gleich 0,165688, bewegt haben sich AUSSCHLIESSLICH
t-Wörter (Seiten +0,00001 · Soldaten +0,0007 · streiten +0,0036 ·
unter +0,0038 · fechten +0,0100); kein Nicht-t-Wort verliert
Übereinstimmung. ENTSCHEIDUNG: BEHALTEN — kein Kill-Kriterium
feuert, die Tinte ist quasi unverändert (der Join beginnt an der
Spitze statt am Schnittpunkt, derselbe Weg), und die
Buchstaben-Attribution stimmt jetzt mit der Hand überein; das
compose-golden-Fixture wurde als deklarierte Re-Baseline
regeneriert. K1b ist der nächste Composer-Kandidat der Welle.
*(Datierter Nachtrag `aug19`: die v2.1-Retrace-Filterrunde hat
die t-Ring-Zählungen, die K1s Zähler-Begründung trugen, wieder
entfernt (§ „Struktur-Zähler v2" Nachtrag) — K1 bleibt adoptiert
allein auf dem Attributions-Argument: die Balken-Kreuzung gehört
in den Buchstaben, nicht in den Join.)*

### Welle 1 · B1 `aug15` — Vorregistrierung: Best-of-N über Input-Augmentierungen (InkSight)

Geschrieben und committet VOR der ersten Zahl dieser Maßnahme
(Plan: `../proposals/tintenfolger.md` §7.4; Infrastruktur
`tools/inksight/{augment,ensemble}.py`, Ranker ausschließlich gegen
die gemessene Tinte).

**Hypothese.** Ein einzelner Decode ist ein Zug aus einer auf
Sütterlin instabilen bedingten Verteilung; N deterministische
Augmentierungs-Varianten (Rotation ±2/±4° × Füllgrad — exakt die
InkSight-eigenen Trainings-Augmentierungen) plus ein Tinten-Ranker
(beidseitiges Chamfer gegen `ref_skel`, Kontraktverletzung
disqualifiziert) verbessern die Bahn. Präzedenz: Afonin et al.,
ICDAR 2023 (dieselbe Forschungsgruppe, „more than halving the
character error rate").

**Owner-Direktive (2026-08-15).** Gemessen wird nicht nur der
Gewinner: ALLE Varianten werden einzeln gegen die Handbahn
gebencht. Die ORAKEL-Spalte — die per Hand-dtw beste Variante je
Wort gegen die Wahl des Tinten-Rankers — beziffert, was die
ehrliche Tinten-Auswahl kostet; die Handbahn bleibt Prüfung, die
Tinte das einzige Auswahlsignal.

**Messgrößen und Kill-Kriterien** (Dev-Split, Vergleich gegen die
eingefrorene T0-derender-Zeile `temp/tb-inksight-derender.json`,
dtw-Median 0,0956, 9 gewertete Wörter + `Wer` failed):
(a) Primär: gepaarter dtw_xh-Median Best-of-N vs. T0-derender;
Median-Δ ≥ 0 (keine Verbesserung) = Maßnahme verworfen.
(b) Struktur netto: `cross_missing+spurious` und
`retrace_missing+spurious` dürfen sich in Summe nicht
verschlechtern.
(c) `Wer` (T0: failed an einem Ein-Punkt-Strich): erwartet geheilt,
sobald EIN konformes Ensemble-Mitglied existiert; bleibt es failed,
wird das berichtet, ist aber kein Kill.
(d) Die Orakel-Lücke (Median der gepaarten Differenz
Ranker-Wahl − Hand-Orakel) wird berichtet — eine große Lücke ist
ein Befund über das Auswahlsignal, kein Kill.
(e) Determinismus-Gate: die Identitäts-Variante `rot+0_s100` muss
tokengleich zur T0-Antwort decodieren; weicht sie ab, ist der
LAUF ungültig (nicht die Maßnahme).

**Ergebnis (gemessen nach dem Commit oben).** Der Lauf ist GÜLTIG,
die Maßnahme ist nach ihrer eigenen Regel VERWORFEN — und der Fund
steckt in der Orakel-Spalte, die genau dafür vorregistriert war.

*Gate (e) zuerst:* die Identitäts-Variante `rot+0_s100` decodiert
bei ALLEN zehn Wörtern tokengleich zur eingefrorenen T0-Antwort
(rekonstruierte Token-Sequenz, `n_ink_tokens` 149…441 identisch,
`n_invalid_tokens` überall 0, Strichlisten punktgleich; die
Eingabe-PNGs sind ohnehin byte-identisch zu denen von `prepare.py`).
100/100 Rohantworten geparst, 10 Varianten je Wort, ein
Decoder-Deckel-Treffer (`laden`/`rot+4_s092`, 1023 von 1024 Token =
abgeschnittene Tinte, ohnehin kontraktverletzend).

*Gate (a), die Entscheidung:* gepaarter dtw_xh-Median Best-of-N
gegen T0-derender **+0,0000** (9 gepaarte Wörter; 4 besser, 4
schlechter, 1 unverändert; Vorzeichentest p = 1,0; Median absolut
0,0956 → 0,0960). Δ ≥ 0 heißt laut Vorregistrierung: **verworfen**.
Die Tinten-Zahlen bewegen sich dabei ALLE in die erwartete Richtung
— `aiou` 0,6969 → 0,7057, `chamfer_cand_ref` 0,0430 → 0,0388, die
Ranker-Summe je Wort 0 bis −40 % gegen die Identität. Der Ranker
hat also genau das optimiert, was ihm aufgetragen war; nur ist das
nicht, was dtw misst.

*Gate (b):* Struktur netto NICHT schlechter — auf denselben neun
Wörtern Kreuzungen (missing+spurious) 10 → 6, Retraces 13 → 14,
Summe 23 → 20. Der Zehn-Wort-Block liest 23 → 25, weil `Wer`
überhaupt erst gewertet werden KANN und seine eigenen Defekte
mitbringt; die Like-for-like-Spalte ist die Antwort auf „wurde es
schlechter".

*Gate (c):* `Wer` ist GEHEILT — T0 scheiterte an einem
Ein-Punkt-Strich, Best-of-N liefert eine speicherbare Zeile (dtw
0,1378 über `rot-2_s092`). Von zehn Varianten waren dort genau zwei
kontraktkonform: das Ensemble hat die Heilung mit seinem letzten
Mitglied bezahlt, nicht mit Redundanz.

*Gate (d), der eigentliche Befund — die Orakel-Lücke.* Je Wort
Ranker-Wahl (dtw) · Hand-Orakel (dtw) · T0: `Wer` `rot-2_s092`
0,1378 · dieselbe 0,1378 · failed | `die` `rot+2_s092` 0,0385 ·
`rot+0_s092` 0,0312 · 0,0395 | `laden` `rot+0_s100` 0,0607 ·
dieselbe · 0,0607 | `linken` `rot-2_s100` 0,1081 · dieselbe ·
0,1227 | `mit` `rot-2_s100` 0,0758 · `rot+4_s092` 0,0361 · 0,0421 |
`muß` `rot+4_s100` 0,0886 · `rot+0_s100` 0,0808 · 0,0808 | `und`
`rot+4_s100` 0,3795 · dieselbe · 0,3952 | `unter` `rot-4_s100`
0,3966 · `rot-2_s100` 0,0813 · 0,3898 | `will` `rot+4_s100` 0,0960
· `rot-4_s100` 0,0516 · 0,0956 | `zwei` `rot+4_s100` 0,1129 ·
`rot+2_s100` 0,1069 · 0,1193. Median der gepaarten Differenz
(Ranker − Orakel) **+0,0067 xh**, Treffer in 4 von 10 Wörtern. Und
die Kehrseite derselben Tabelle: das ORAKEL hätte einen gepaarten
Median von **−0,0124** geliefert (7 von 9 Wörtern besser, Median
absolut 0,0808) — Gate (a) also klar bestanden. Die N Antworten
ENTHALTEN die Verbesserung; das Auswahlsignal findet sie nicht.

*Warum nicht — an einem Wort abzulesen.* Bei `unter` stehen vier
kontraktkonforme Varianten zur Wahl; der Tinten-Ranker setzt
`rot-4_s100` (Chamfer-Summe 0,0759) vor `rot-2_s100` (0,0841), also
10 % Abstand im Auswahlmaß — in der Handbahn liegen zwischen beiden
0,3966 gegen 0,0813, ein Faktor 4,9. Bei `mit` dasselbe Muster mit
8 % Chamfer-Abstand und +0,0337 dtw gegen T0 (die größte
Einzelregression des Laufs). Das ist keine Kalibrierfrage: ein
beidseitiges Chamfer gegen das Skelett misst ÜBERDECKUNG und Nähe,
dtw misst Reihenfolge und Korrespondenz. Wo eine Variante die Tinte
gleich gut bedeckt, sie aber in anderer Ordnung durchläuft, ist der
Ranker per Konstruktion blind — und genau diese Wörter (`unter`,
`mit`) sind die Berührungs-/Überlagerungsfälle aus §7.1.

*Zweiter Befund: die Augmentierung kostet Kontraktkonformität.* Nur
`rot+0_s100` und `rot-2_s100` schaffen 9 von 10 Wörtern; die
Füllgrad-Varianten kommen auf 3–4. Nach Disqualifikation bleiben im
Median 4 von 10 Mitgliedern, bei fünf Wörtern ≤ 4 und bei `und`,
`laden`, `Wer` nur 2 — das Ensemble schrumpft ausgerechnet dort, wo
es gebraucht würde. Einziges Wort mit 10/10 gültigen Mitgliedern ist
`die` (kleinster Crop, 154 px). Die Ein-Punkt-Striche sind also kein
`Wer`-Sonderfall, sondern die Reaktion des Modells auf verschobene
Eingaben. Repariert wird nichts (§2.4): eine geflickte Zeile ließe
das Modell besser aussehen, als es ist.

*Kein systematischer Gewinner.* Der Ranker wählt 7× reine Rotation,
2× Füllgrad, 1× die Identität; das Orakel verteilt sich auf ACHT
verschiedene Varianten. Es gibt keine bessere feste Vorverarbeitung,
die man einfach adoptieren könnte — der Gewinn ist wortweise und
steht und fällt mit der Auswahl.

**ENTSCHEIDUNG: VERWORFEN** als Default (Gate (a) feuert; nichts in
`core/`, an der DB oder am Rendering wird berührt — die Maßnahme
lebte ohnehin nur im Messlayer). Behalten wird die INFRASTRUKTUR
(`tools/inksight/{augment,ensemble}.py` inkl. `--per-variant`), denn
sie hat die eigentliche Frage erst messbar gemacht. Der Nachfolger
ist NICHT „mehr Varianten", sondern das Auswahlsignal: ein Ranker,
der Reihenfolge sieht (Soll-Duktus-Struktur statt reiner
Überdeckung), gemessen gegen die hier gemessene Orakel-Lücke von
+0,0067 xh als Zielgröße und −0,0124 als Deckel. `Wer` bleibt als
Nebenergebnis geheilt, ist aber allein keine Adoption wert.

### Welle 1 · A1 `aug15` — Vorregistrierung: der Marken-Nachfit

Geschrieben und committet VOR der ersten Zahl dieser Maßnahme
(Plan: `../proposals/tintenfolger.md` §7.3; Infrastruktur
`tools/pairlab/marks.py`, opt-in `--mark-refit`, default byte-identisch).

**Hypothese.** Die Marken des Kettenfit-Kandidaten stehen an ihrer
Kompositions-Position statt auf der gemessenen Marken-Tinte
(`mark_pos_err_xh` Median 0,129 gegen 0,046 der prior-freien
Kontrolle; bei muß/und/unter/zwei matcht keine Marke). Ein rigider
Nachfit (reine Translation) jeder Marke auf die vom Körper nicht
beanspruchte Skelett-Tinte, mit Verweigerung bei Ambiguität
(Suchradius 0,6 xh = die Match-Grenze des Lineals, Margin 0,25),
senkt den Ortsfehler, ohne irgendetwas anderes zu bewegen.

**Nachfit-Ziel ist ausschließlich die TINTE** (ref_skel), nie die
authored-Referenz — gemessen wird ausschließlich GEGEN die Hand.

**Messgrößen und Kill-Kriterien** (gepaart über die 10 Dev-Wörter
des eingefrorenen Splits, Vergleich gegen die deklarierte
Post-K1-Kettenbaseline `tb-chain-r1-postk1`):
(a) Primär: `mark_pos_err_xh`-Median fällt; `marks_matched` steigt
oder bleibt (ein VERLORENES Match = verworfen).
(b) Do-no-harm: `dtw_xh` byte-gleich auf Wörtern ohne bewegte Marke
und ohne Netto-Verschlechterung insgesamt; Strukturzähler
(cross/zones/touch/overlap) exakt unverändert — der Nachfit bewegt
nur Marken-Striche; jede Abweichung = verworfen.
(c) `marks_spurious` darf nicht steigen (zwei 1,0 heute).
(d) Verweigerungen werden gezählt und benannt (meta.mark_refit),
nie still übergangen.

**Ergebnis (gemessen nach dem Commit oben, Lauf `tb-a1-marks`
gegen `tb-chain-r1-postk1`).** Die Hypothese ist BESTÄTIGT, mit
einer Einschränkung, die erst der Lauf sichtbar gemacht hat.
Primär: `mark_pos_err_xh` Median **0,1285 → 0,0576** (−55 %; Mittel
0,1217 → 0,0530), und zwar auf JEDEM der vier Wörter, die das Lineal
überhaupt paaren kann — `die` 0,0675 → 0,0560 · `mit` 0,1071 →
0,0194 · `linken` 0,1624 → 0,0592 · `will` 0,1499 → 0,0775.
`marks_matched` bleibt 4/4 (kein Match verloren), `marks_missing` 0,
`marks_spurious` 1 → 1, `marks_ambiguous` 0. Damit schließt A1 rund
86 % des Abstands zur prior-freien Kontrolle (0,046): der Kettenfit
konnte die Markentinte immer lesen, er hat sie nur nie gefragt.
Do-no-harm hält vollständig: die Strukturzähler sind über ALLE zehn
Wörter exakt unverändert (0 abweichende Zellen über
cross/retrace/touch/overlap/soll/lift), `dtw_xh` ist auf 7 von 10
Wörtern byte-gleich, der gepaarte Median-Δ ist 0,0000 und der
Vorzeichentest n=3/pos 2/neg 1 mit p=1,0. Nebenbei verbessern sich
die tintenseitigen Spalten (`aiou` 0,6831 → 0,6884, beide Chamfer-
Mediane −0,0003) — genau das Vorzeichen, das „die Marke sitzt jetzt
auf Tinte" erwarten lässt. Verweigerungen: KEINE. Acht der zehn
Wörter tragen genau eine Marke, alle acht wurden bewegt (Median-
Verschiebung 0,073–0,127 xh, alle weit innerhalb des 0,6-xh-Radius),
`laden` und `Wer` haben gar keine.

**Die Einschränkung, und sie ist der eigentliche Fund.** Das
PRIMÄRMASS ruht auf 4 der 10 Wörter: bei `unter`, `und`, `muß` und
`zwei` steht `marks_uncertain` — die AUTHORED-Referenz enthält dort
gar keinen als Marke klassifizierten Strich (die Hand schreibt den
u-Bogen angebunden, nicht schwebend), also gibt es nichts zu paaren.
Genau diese Wörter zeigen den zweiten Effekt: die Harvest-Regel
`_is_diacritic` (schwebt über der Mittellinie, KEINE Bogenlängen-
Grenze) nimmt den langen u-Bogen als Marke, das Lineal
(`classify_strokes`, Deckel 0,8 xh) zählt ihn als Körper — deshalb
landet seine Verschiebung dort in der Körper-DTW statt in der
Marken-Spalte: `unter` −0,0008 (besser), `und` +0,0010, `muß`
+0,0020. Das ist der gesamte dtw-Effekt des Laufs; er hebt den
Headline-Median um +0,0005 (0,061985 → 0,062474), weil `und` zufällig
auf der Median-Position sitzt. Bei den fünf i-Punkt-Wörtern bleibt
die DTW byte-gleich, weil das Lineal die Marke vor der Körper-DTW
heraustrennt. Kandidat A1b (eigene Vorregistrierung, NICHT Teil
dieses Ergebnisses, weil er nach Sicht der Daten formuliert ist): den
Nachfit auf Striche mit Bogenlänge ≤ `MARK_MAX_ARC_UNITS`
beschränken, also auf genau die Klasse, die „Marke" heißt — der
u-Bogen wäre dann wieder Sache des Körper-Solves.

ENTSCHEIDUNG: **BEHALTEN.** Kein Kill-Kriterium feuert (kein
verlorenes Match, kein zusätzliches `marks_spurious`, Strukturzähler
exakt gleich, keine Netto-dtw-Verschlechterung), und das Primärmaß
mehr als halbiert sich. Der Schalter bleibt vorerst opt-in
(`--mark-refit`, `HarvestOptions.mark_refit`, default AUS): der
Kettenfit-Kandidat ist die eingefrorene Baseline, und ob A1 in die
GESPEICHERTE Bahn wandert, ist ein eigener Autoren-Entscheid — der
Bestätigungssatz (`--split confirm`) ist die Bedingung dafür, weil
vier gepaarte Wörter eine schmale Grundlage für eine Adoption sind.

**Nachmessung `aug19` auf dem 19er-Dev-Satz** (§7.7
Nachkalibrierungs-Protokoll; kein neuer Knopf, dieselbe opt-in
Variante `--mark-refit`, lokale Basis der v0.10/v0.11-Runde):
`mark_pos_err_xh`-Median **0,111 → 0,030 (−73 %)**, ALLE sechs
markentragenden Dev-Wörter verbessern sich (die 0,072 → 0,036 ·
mit 0,106 → 0,019 · linken 0,160 → 0,059 · will 0,150 → 0,078 ·
mit-2 0,116 → 0,023 · die-2 0,055 → 0,019); Körper byte-neutral
(dtw-Δ-Median 0,0000, 10 ties), Marken- und Strukturzähler exakt
unverändert (Galoppierens fehlende i-Marke bleibt fehlend — der
Nachfit repariert Positionen, erfindet keine Striche). Der
Welle-1-Gewinn generalisiert damit auf die 9 neuen Nachfahrungen,
stärker als auf dem 10er-Satz (−55 %). Die Adoptionsbedingung
(Bestätigungssatz) bleibt; die Grundlage ist jetzt 6 statt 4
gepaarte Wörter.

### Welle 1 · K1b `aug15` — Vorregistrierung: der versetzte Stamm-Rückpass des t

Geschrieben und committet VOR der ersten Zahl dieser Maßnahme
(der in K1s Ergebnis benannte Kandidat; Plan
`../proposals/tintenfolger.md` §7.2).

**Hypothese.** Das verbleibende t-Defizit (`unter` `soll_cross` 2
vs. Hand 3 · `soll_zones` 2 vs. 3; `mit` 1 vs. 2 · 1 vs. 2; dazu
`lift_delta` +1 der Kette auf beiden Wörtern) kommt daher, dass die
Komposition zwischen Stammfuß und Deckstrich ABSETZT, wo die Hand
den Stamm mit VERSATZ retraced: Abstrich x≈4,60, Aufstrich x≈4,65,
der Auslauf durchsticht BEIDE Pässe (Kreuzungs-Sites 0,07 xh
auseinander). Ein generierter Rückpass — der Balkenstrich verliert
seinen Lift und wird stattdessen mit einer Brücke Stammfuß →
Balkenstart als Präfix versehen, nach rechts ausgebuchtet um
`BAR_RETRACE_BULGE_UNITS` — stellt Zonen, Kreuzungen und Strichzahl
der Hand wieder her. Vorbild ist der Capital-Retrace
(`cap_retrace`): das Präfix ist generierte Centerline OHNE eigene
Silhouette, die gedruckte Tinte ändert sich nicht (der Versatz
bleibt innerhalb der Schwellzug-Breite).

**Konstante, gemessen statt gewählt.** `BAR_RETRACE_BULGE_UNITS =
0.06`: der Aufstrich der Hand liegt 0,05–0,07 xh rechts des
Abstrichs (unter x≈4,60→4,65; die zwei Kreuzungs-Sites der Hand
liegen 0,07 auseinander und werden vom Zähler als getrennte Sites
geführt — ein kleinerer Versatz würde zu EINER Site verschmelzen).
Nur Basis t; das Präfix wird nur gebaut, wenn der vorige Strich
unterhalb des Balkenstarts endet und horizontal nahe liegt
(Stamm-Geometrie), sonst bleibt der Lift.

**Erwartung.** `soll_cross`: `unter` 2→3, `mit` 1→2 (= Hand);
`soll_zones`: `unter` 2→3, `mit` 1→2 (= Hand);
`soll_cross_agree` 7/10 → 9/10, `soll_zones_agree` 6/10 → 8/10;
Ketten-`lift_delta` auf mit/unter −1 (erst im nächsten
Kettenlauf sichtbar).

**Messgrößen und Kill-Kriterien.**
(a) Die Erwartungs-Zellen oben JE WORT; jedes NICHT-t-Wort, das
eine Übereinstimmung verliert → verworfen. Ein Über-Kreuzen
(`unter` > 3 oder `mit` > 2) → verworfen (Versatz zu groß oder
Präfix kreuzt selbst).
(b) wordbench `--set all`: Headlines nicht > +0,002; Bewegung nur
in t-Wörtern.
(c) compose-golden bricht bauartbedingt → deklarierte Re-Baseline
im selben PR, kein Akzeptanzkriterium.
(d) Die deklarierte Post-K1-Kettenbaseline
(`temp/tb-chain-r1-postk1.json`, Kaskade aus K1) ist der
Vergleichspunkt des nächsten Kettenlaufs; K1b selbst wird zuerst
auf Soll-Ebene abgenommen.

**Ergebnis (gemessen nach dem Commit oben).** Die Erwartung trifft
Zelle für Zelle ein: `soll_cross` `unter` 2→**3** und `mit` 1→**2**
(beide = Hand), `soll_zones` `unter` 2→**3** und `mit` 1→**2**
(beide = Hand), `soll_cross_agree` 7/10 → **9/10**,
`soll_zones_agree` 6/10 → **8/10**; kein Über-Kreuzen, kein
Nicht-t-Wort bewegt. Die per-Letter-Zelle des t wird 2/1 — der
Auslauf durchsticht jetzt Abstrich UND versetzten Aufstrich, wie
die Hand. Unangekündigter Bonus: die 4 `soll_overlap`-Einträge der
t-Wörter (Balken-gegen-Stamm) verschwinden vollständig (Hand hat
dort ebenfalls 0), je eine Berührung bleibt (`mit` 1 vs Hand 2,
`unter` 1 = Hand 1). Verbleibende Abweichler sind die bekannten
Chart-Fälle: `linken` (k zählt im Soll eine Kreuzung mehr als die
Hand schreibt), `Wer` (W-Ansatz-Retrace, Chart-Lücke, Korb) und
`zwei` (z-Retrace, mutmaßlich dieselbe Klasse — bei der
W-Neutracierung mitprüfen). Gates: wordbench `bench_loss` 0,110992
→ 0,110983 (−0,00001), `pair_loss` 0,165688 → 0,165725 (+0,00004,
Schwelle 0,002), bewegt ausschließlich t-Wörter (macht · mit ·
mit-2 · Seiten · Soldaten · fechten · streiten · unter, alle
≤ ±0,0005); compose-golden regeneriert (deklarierte Re-Baseline);
1240 Tests grün. ENTSCHEIDUNG: BEHALTEN. — Nebenbefund, hier
deklariert: die Post-K1-KETTENbaseline `r1` (der Vergleichspunkt
aller folgenden Kettenläufe) unterscheidet sich von `r0` in genau
EINEM Wort: `unter` dtw 0,4389 → 0,4690 (+0,0301) bei einer
erfundenen Kreuzung WENIGER (`cross_spurious` 4→3); die übrigen 9
Wörter sind byte-identisch. Der ohnehin chaotische unter-Fit
reagiert auf die veränderte Initialisierung — die dtw-Zahl der
Kette ist dort schlechter, ihre Topologie besser; der als nächstes
anstehende Kettenlauf (A1) vergleicht gegen r1.

### Welle 2 · P1 `aug15` — Vorregistrierung: die Vorschub-Kalibrierung aus den gemessenen Joins

Geschrieben und committet VOR der ersten Zahl der Maßnahme.
Anlass ist ein Owner-Fund an den K1b-Sichtprüfungs-Overlays: auf
langen Wörtern wandert die Komposition nach hinten sichtbar rechts
von der Specimen-Tinte weg („das Rot muss auf dem Ink liegen").

**Befund (Diagnose-Skripte, Session `aug15`).** (a) Drift-Profil
über die 63 Bench-Wörter — je Slot der best-passende x-Versatz der
komponierten Buchstaben gegen das Specimen-Skelett, ZUSÄTZLICH zur
globalen Registrierung des Lineals: Drift-Median −0,10 xh
(Mittel −0,25), −0,0375 xh je Slot; Vorsicht Arkaden-Aliasing (i/n/m
rasten beim Best-Fit um einen ganzen Bogen, Einzelsprünge ±1 xh sind
Artefakte). (b) Die identitäts-sichere Zahl: die SIGNIERTE
doff-Verteilung über 218 gemessene Joins (pairmeas-Frame, Betrag
durch Vorzeichen ersetzt): Median **+0,05 xh je Join**, 138/218 zu
weit — aber KEIN globaler Faktor, sondern zwei Klassenfehler in
Gegenrichtung: zu WEIT laufen Ausgänge aus Rundkörpern/Schleifen und
Eingänge in e/r (b→e +0,41 · f→e +0,31 · o→r +0,30 · c→h +0,25 n=6 ·
w→e +0,20 · t→e +0,15 · e→r +0,14 n=13 · d→e +0,12); zu ENG laufen
Eingänge in die Arkaden (e→n −0,13 n=12 · u→n −0,23 · i→n −0,24 ·
n→n −0,21 · u→m −0,31) sowie r→e (−0,66 n=3 — Verdacht
Frame-Kaveat des Arm-Fuse, vor jeder Korrektur visuell prüfen).

**Maßnahme in zwei Stufen.**
(i) MECHANISMUS-ATTRIBUTION statt additiver Fudges: die Komposition
bekommt unter `provenance=True` ein report-only Feld, das je
platziertem Glyph benennt, WELCHE Platzierungsregel gefeuert hat
(Fork/Bar-Rise/Arm-Fuse/Girlande/High-Couple …) und ob der
Ink-Clearance-Floor gebunden hat; die 218 signierten Fehler werden
danach gruppiert. Erwartung: die Zu-weit-Klasse korreliert mit
gebundenem Clearance-Floor bzw. einer benennbaren Kopplungsregel,
die Zu-eng-Klasse mit der Girlanden-Kopplung. Sonderfrage: hat K1s
Balken-Tail den t→e-Vorschub über den Ink-Floor verschoben?
(ii) REGEL-FIX der(s) verantwortlichen Mechanismus(se) — Klassen-
regel, kein Pair-Override, Konstanten aus den gemessenen Medianen.

**Messgrößen und Kill-Kriterien.**
(a) Primär: wordbench `word_loss` fällt (trans ist die größte
Komponente); ein Fix, der `word_loss` nicht senkt, wird verworfen.
(b) Die signierte doff-Verteilung: Klassen-Mediane bewegen sich
Richtung 0, der Gesamt-Median |≤ 0,02|; keine Klasse darf das
Vorzeichen ÜBERSCHIESSEN (neuer Betrag > alter Betrag = verworfen).
(c) Struktur-Wächter: `soll_cross_agree`/`soll_zones_agree`
unverändert (Platzierung darf keine Topologie kaufen).
(d) `pair_loss` nicht über +0,002; compose-golden bricht
bauartbedingt → deklarierte Re-Baseline im selben PR.
(e) Stufe (i) ist report-only und muss headline-byte-identisch
sein; zusätzlich wird eine report-only DRIFT-Spalte im Bench
erwogen (eigener, kleiner Schritt — nie Teil eines Loss).
(f) Kill für Stufe (ii): erklärt kein Mechanismus die Mehrheit
seines Klassenfehlers, wird NICHT gefixt, sondern der Befund als
ehrliches Negativ dokumentiert und die Frage an die nächste
Werkzeug-Stufe (H2-Klassen-Statistik) zurückgegeben.

**Stufe (i) gemessen — die Attribution trennt sauber** (Feld
`placement` am Konnektor unter `provenance`, golden/Payload
byte-identisch, 73 Tests grün). Die 218 signierten Fehler nach
entscheidender Regel: `clearance_floor` **n=116** (der
Ink-Clearance-Floor entscheidet die HÄLFTE aller Platzierungen),
median +0,048 — aber gespalten: nach RUNDEM linken Buchstaben
**+0,206 (n=47)**, in ARKADEN (n/m) **−0,182 (n=31)**, in e +0,104
(n=18). Dazu `backward_clearance` **+0,189 (n=19)** (w/v-Bögen),
`bar_rise` **+0,159 (n=6)** (die t-Steiglinie), `align(_floor)`
+0,07 (n=36, mild), `connect_gap` −0,042 (n=26, fein),
`arm_fuse` **−0,507 (n=5)** — wie vorregistriert VOR jeder
Korrektur visuell zu prüfen (Frame-Kaveat-Verdacht). Lesart: der
EINE Floor trägt beide Klassenfehler mit entgegengesetztem
Vorzeichen — die Hand lässt Arkaden MEHR Luft und taucht nach
Rundkörpern ENGER in die Lücke, als die einheitliche Clearance
erlaubt; dazu zwei klar überschießende Spezialregeln (Rückwärts-
Clearance, Balken-Steiglinie). Stufe (ii) kalibriert genau diese
vier Stellen aus den gemessenen Medianen; `arm_fuse` erst nach
Sichtprüfung.

**Stufe (ii) gemessen — Einzelzerlegung, drei adoptiert, eine
ehrlich verworfen.** Vorab die `arm_fuse`-Sichtprüfung: das
Defizit ist REAL (Drift +0,49 und doff −0,66 zeigen in dieselbe
Richtung, das fusionierte e sitzt sichtbar zu nah am r), aber mit
der LÄNGE des r-Arms im Template verschränkt — eine reine
Platzierungskorrektur risse die Berührung auf; bleibt draußen
(eigener Kandidat, mutmaßlich Chart-/Laufform-Stufe). Der
Gesamt-Fix aller vier Kalibrierungen verletzte Gate (a)
(`word_loss` 0,110983 → 0,114252 bei `pair_loss` −0,023) — die
Einzelzerlegung fand die Ursachen: **Bowl-Voll-Tuck** (Clearance
−0,06, erlaubte Überlappung) allein: words +0,0015 / pairs −0,022
— die Überlappung kollidiert im Wortkontext; **gebundener Tuck**
(Clearance 0,0, Berührung statt Überlappung): words −0,0001 /
pairs **−0,018** — hält fast den ganzen Paar-Gewinn ohne
Wort-Kosten → ADOPTIERT. **Arkaden-Luft** (0,32) allein: words
+0,0043, pairs unbewegt → VERWORFEN als ehrliches Negativ (das
per-Dissektion gemessene Defizit −0,18 bleibt stehen und
unerklärt adressiert; Wiedervorlage am Bestätigungssatz).
**Rückwärts-Clearance** 0,30 → 0,11: words −0,0019 / pairs
−0,0013 → ADOPTIERT (die jul-11-Kalibrierung 0,30 war gegen das
Overlay der Vor-Registrierungs-Ära gelesen). **Balken-Steigung**
0,55 → 0,69: ruler-neutral (words +0,00003), doff-wahr →
ADOPTIERT. **Endstand A′+C+D:** `word_loss` 0,110983 →
**0,108991** (Gate a ✓), `pair_loss` 0,165725 → **0,146602**
(größte Paar-Verbesserung der Bench-Historie), `meas_doff`-Median
0,195 → **0,131**; signierte Klassen-Mediane: gesamt +0,050 →
**+0,010** (Ziel |≤0,02| ✓), backward +0,189 → −0,001, bar
+0,159 → −0,040, Bowl-Floor +0,206 → +0,049 — nichts überschießt
(Gate b ✓). Gate (c): `soll_cross_agree` 9/10 unverändert,
`soll_zones_agree` 8/10 → **9/10** — `zwei` gewinnt durch die
kalibrierte w-Platzierung seine zweite Retrace-Zone (= Hand); die
einzigen Rest-Abweichler sind die zwei Chart-Fälle (linken-k,
Wer-W). compose-golden als deklarierte Re-Baseline regeneriert,
1260 Tests grün. Die Werte-Historie der Wordbench-Headline wird in
§6 beim nächsten Release-Schnitt nachgeführt. Ehrliche
per-Wort-Streuung der Median-Kalibrierung, benannt statt
versteckt: `unter` 0,107 → 0,083 und `fechten` 0,222 → 0,173
gewinnen groß, `streiten` verliert einzeln 0,114 → 0,189 — es ist
das einzige Dev-Wort mit ZWEI t-Exits (t→r und t→e), die
Steigungs-Kalibrierung wirkt doppelt und die globale Registrierung
verteilt den Rest übers Wort (longs→t springt von 0,03 auf 0,36,
ohne dass eine adoptierte Regel diesen Join berührt). Die
t-Join-Stichprobe ist dünn (n=6, Spanne +0,15…+0,21) — der
Bestätigungssatz prüft die 0,69 nach.

**Nachtrag P1b `aug15` — der streiten-Fund des Owners korrigiert
die Rückwärts-Klasse.** Die t-Exit-Attribution des Absatzes oben
war FALSCH: die per-Join-Nachmessung an `streiten` selbst zeigt
die t-Joins nach der Kalibrierung fast perfekt (t→r −0,067 ·
t→e −0,040) — der Schuldige ist `longs→t`, denn der
longs-Abschwung exitiert RÜCKWÄRTS und fiel mit in die pauschal
reduzierte Rückwärts-Clearance (−0,156 per Dissektion, und die
globale Registrierung schob das ganze Wort neben die Tinte —
Owner: „gleich der erste Buchstabe liegt nicht übereinander").
Die Klassen-Nachmessung je linkem Buchstaben: w/v (n=12) wollen
die 0,11 (jetzt +0,02, alt +0,21), Versal-W will sie ebenfalls
(per Ruler UND Dissektion), die übrigen Versalien sind
n=1-Singletons mit Ruler-Dissektions-Konflikt und bleiben beim
Ruler-Präferenzwert 0,11 — die benannte AUSNAHME ist `longs`
(`LONGS_BACKWARD_CLEARANCE` 0,30): sein Abschwung-Rücklauf
braucht den alten Raum (die zwei Bench-longs-Wörter splitten ihr
Ruler-Votum ±0,03, die einzige dissezierte longs-Zeile stimmt für
0,30; Wiedervorlage am Bestätigungssatz). Endstand P1b:
`word_loss` 0,108991 → **0,108446**, `pair_loss` unverändert
0,146602, gegen den gemergten P1-Stand bewegt sich EXAKT ein Wort
(`streiten` 0,189 → 0,154), Soll-Agree unverändert 9/10 · 9/10,
compose-golden regeneriert (deklarierte Re-Baseline). Der
Fehlversuch dazwischen — ALLE Nicht-w/v-Rückwärts-Exits auf 0,30
zurück — wurde gemessen und verworfen (words +0,0009, drei Wörter
regressieren): auch eine Korrektur-Klasse kann zu breit
geschnitten sein.

### Welle 2 · P2 `aug15` — Vorregistrierung: die align-Klasse und der Arkaden-Varianz-Befund

Geschrieben und committet VOR der ersten Zahl der Maßnahme; setzt
die Owner-Direktive „die x-Verschiebung ist noch real, weitermachen"
um. Zwei Teile — eine Kalibrierung und ein GESCHLOSSENER Befund.

**(A) Arkaden-Luft — geschlossen als Hand-Varianz, KEIN
Kalibrierfehler.** Die Dissektion verlangt +0,18 Luft vor Arkaden,
das Lineal lehnt jede getestete Dosis ab (0,32: words +0,0037 ·
0,23: +0,0008). Der Mechanismus-Test löst den Widerspruch: unter
Luft wird `wenn` besser (−0,030) und `wenn-2` — DASSELBE Wort,
anderer Beleg — deutlich schlechter (+0,089); die vier
`und`-Belege stimmen gemischt ab; die dissezierten
Arkaden-Deltas streuen MAD 0,096 (p10..p90 −0,13..+0,12) bei
Median −0,004 unter Luft. Die Hand schreibt die Arkaden-Weite von
Beleg zu Beleg ±0,1 xh verschieden — die Komposition kann nur
EINEN Punkt im Band wählen und bleibt am Ruler-Punkt. Keine
Konstante wird geändert; Wiedervorlage ausschließlich mit dem
Bestätigungssatz.

**(B) align-Klasse — die letzte kalibrierbare Vorschub-Masse.**
36 gemessene Joins, Median +0,072, und der Fehler ist
STEIGUNGS-UNABHÄNGIG (klein-rise +0,069 / groß-rise +0,074,
Korrelation −0,28) — also ADDITIV, kein Steigungsproblem wie beim
Balken. Zwei Unter-Mechanismen, je ein Knopf, Einzelzerlegung wie
P1: (i) die reine Durchlauf-Diagonale (`align`, n=19, +0,074) —
ein gemessener Abzug `ALIGN_ADVANCE_TRIM_UNITS = 0.07` auf das
Diagonalen-Ziel; (ii) der gebundene align-Floor (`align_floor`,
n=17, +0,069) — `ALIGN_MIN_CLEARANCE` 0,06 → **0,0**: dieselbe
Berührungs-Semantik wie der adoptierte Bowl-Tuck (Spalten dürfen
sich berühren, nie überlappen).

**Messgrößen und Kill-Kriterien** (identisch zur P1-Familie):
(a) wordbench `word_loss` fällt gegen 0,108446, sonst verworfen —
je Knopf einzeln UND in Kombination gemessen; (b) die
align-Klassen-Mediane bewegen sich Richtung 0 ohne Überschießen;
(c) `pair_loss` nicht > +0,002; (d) `soll_*_agree` unverändert;
(e) compose-golden bricht bauartbedingt → deklarierte Re-Baseline.
Erwartete Ausreißer, vorab benannt: `Z→a` +0,94 und `a→n` −0,645
sind n=1-Extreme und werden von keiner Konstante gejagt.

**Ergebnis (gemessen nach dem Commit oben).** Einzelzerlegung wie
registriert: Knopf (i), der Diagonalen-Trim, wird vom Lineal bei
jeder Dosis abgelehnt (0,07 allein: +0,0020 · 0,035 auf dem Floor:
+0,0011) — dasselbe Beleg-Varianz-Verdikt wie die Arkaden-Luft;
die Konstante bleibt DEKLARIERT-ABER-NEUTRAL (0,0), die
Dissektions-Forderung steht für den Bestätigungssatz im Protokoll.
Knopf (ii), der Berührungs-Floor (`ALIGN_MIN_CLEARANCE` 0,06 →
0,0), BESTEHT: `word_loss` 0,108446 → **0,108091**, `pair_loss`
byte-gleich, `soll_*_agree` unverändert 9/10 · 9/10. Die Streuung:
9 Wörter besser (voran `fechten` 0,173 → **0,144** — sein
f→e-align_floor war der +0,31-Ausreißer; kumuliert seit Beginn der
Vorschub-Runde 0,222 → 0,144), größter Einzelverlierer `Zaum`
+0,022 (der vorab benannte `Z→a`-Ausreißer reagiert auf den
Floor). compose-golden regeneriert (deklarierte Re-Baseline),
1260 Tests grün. ENTSCHEIDUNG: Floor ADOPTIERT, Trim NEUTRAL.
Damit ist die kalibrierbare Vorschub-Masse der 218 gemessenen
Joins abgearbeitet: adoptiert Bowl-Tuck · w/v-Rückwärts ·
longs-Ausnahme · Balken-Steigung · align/nested-Floor; als
Beleg-Varianz geschlossen Arkaden-Luft · Diagonalen-Trim; offen
bleiben die zwei NICHT-Kalibrier-Fälle `arm_fuse`/r-Arm-Länge
(Chart-Frage) und `descender_ride` (n=2, zu dünn).

### Welle 2 · P3 `aug16` — Vorregistrierung: Kopf-Koartikulation als Entry-Klassenregeln

Geschrieben und committet VOR der ersten Zahl der Maßnahme.
Owner-Priorität „zeitnah" (2026-08-15): kontextabhängige
Kopf-/Schwanz-Flexibilität der Buchstaben als nächster
Composer-Baustein nach der Vorschub-Runde.

**Vorstudie (Session `aug15`, 248 Vorkommen / 134 Paare über
words+pairs).** Werkzeug: `pairlab.dissect_occurrence(trace=True)`
über alle Fixture-Vorkommen, mit Zerlegung der M4-Ankerverschiebung
in starren Anteil (Median über die Körperanker), Längs-/Quer-
Residuum an der Template-Tangente und die verschiebungs-invariante
Reichweite des ganzen Anschluss-Strichs; Permutationstests;
Skripte im Session-Scratchpad (`coart.py --against laufform`,
Rohdaten `coart_lauf.json`). Der Befund ist eine ASYMMETRIE:

(a) Der SCHWANZ (linke Seite) ist KEINE Koartikulation: die
Umformung hängt nicht vom Nachfolger ab (p = 0,19–0,55) und ist je
Exit-Klasse eine Konstante mit winzigem MAD (Arkaden +0,079 ±
0,011 · d −0,144 ± 0,010 · Balken −0,053 ± 0,010). Das ist eine
Chart-/Laufform-Frage und AUSSERHALB dieses Eintrags — ebenso der
pauschale +7–10-%-Reichweitenzuwachs des Anschluss-Strichs.
(b) Der KOPF (rechte Seite) IST Koartikulation: nach einem
Hoch-Exit (Balken, d-Schleife, Deckstrich-Bogen, r-Arm) sitzt der
Ankunftspunkt +0,10 xh weiter rechts und +0,10 xh höher, der
Eingangs-Strich ist 0,09–0,15 xh kürzer als nach flachem Exit
(p < 0,0001 in jeder geprüften Population). Die Laufform trägt
davon nur ein Viertel des Betrags und nichts vom Senkrechten
(Δ 0,084 xh, p < 0,00002) — sie KANN es bauartbedingt nicht
tragen, weil sie eine Form je Glyph ist. Deshalb Klassenregeln im
Composer; alle Konstanten LAUFFORM-relativ erhoben (pairlab misst
gegen die Chart-Zeile, komponiert wird die Laufform).

**Die drei vorregistrierten Entry-Regeln** (Median ± MAD in xh;
Basislinie `arkade→arkade` n = 65: Reichweite +0,093 ± 0,017,
cp dx −0,046 ± 0,010, Ankunft y 0,570 ± 0,033). Umsetzungs-
Reihenfolge **K1 → K3 → K2** (K1 = schärfster Effekt, K3 = reine
Höhenregel = billigster Eingriff, K2 = riskantester wegen des
zweimal verworfenen Stub-Trims), je Regel EIN Knopf mit eigener
Leiter, gepaart gemessen, erst adoptieren, dann die nächste:

* **P3-K1 · Balken → Rundkörper** (`BAR_EXIT_BASES` t/f → e/a/o
  …): gemessen cp dx **+0,157 ± 0,002**, cp dy +0,075 ± 0,011,
  Kopfstrich-Reichweite −0,089 ± 0,005 (n = 7: t→e, f→e);
  compose-relativer Ankunftswinkel **+126,1° ± 4,3** — der Zug
  kommt heute praktisch aus der Gegenrichtung an. Regel: nach
  Balken-Exit koppelt der Verbinder TIEFER auf der Anstiegsflanke
  (Soll-Ankunft y ≈ 0,56 statt einheitlich `ENTRY_COUPLE_Y` 0,78)
  und der Entry-Stub verliert ≈ 0,09 Reichweite. Knopf: klassen-
  eigenes `BAR_ENTRY_COUPLE_Y`, Leiter 0,50 / 0,56 / 0,62 / 0,78
  (= aus).
* **P3-K3 · Deckstrich-Bogen → Arkade** (o/b/v/w → n/m/i/r):
  gemessen cp dy **+0,074 ± 0,022** bei cp dx +0,038 ± 0,011 und
  Reichweite −0,001 ± 0,027 (n = 6: o→n, b→i, w→i, o→r),
  Soll-Ankunft y 0,685 gegen Basislinie 0,570. Reine HÖHEN-Regel,
  kein Längeneingriff. Knopf: Anhebung des Arkaden-Ankunftspunkts
  nach Deckstrich-Exit, Leiter +0,00 / +0,07 / +0,11.
* **P3-K2 · Schleifen-Exit → Rundkörper** (d → e/a/o): gemessen
  Kopfseite cp dx +0,080 ± 0,025, cp dy +0,052, Reichweite −0,086
  (n = 8), Soll-Ankunft y 0,628; A-Seite d-Abgangswinkel
  compose-relativ **+48,0° ± 0,8** bei Reichweiten-Wachstum in
  0 von 18 Vorkommen. **Ausdrücklich: der reine d-Stub-Trim ist
  zweimal gemessen-und-verworfen (`jul11`, `jul17`/PR #220) und
  wird NICHT wiederholt** — das neue Signal ist der WINKEL, nicht
  die Länge. Knopf: Drehung des d-Abgangswinkels Richtung
  gemessener Tangente, Leiter +0° (= aus) / +24° / +48°.

**Nicht in dieser Vorregistrierung** (benannt, damit es niemand
hineinliest): (a) `arm_fuse`/r→e — die Formeffekte erklären ≤ 20 %
der −0,51-Lücke, bleibt Platzierung/Armlänge, wie P1 schloss;
(b) der pauschale Reichweitenzuwachs (Chart-/Laufform-Frage);
(c) alle Versal-Paare (n=1-Singletons).

**Messgrößen und Kill-Kriterien** (wie die P1-Familie).
(a) Primär: wordbench `word_loss` UND `pair_loss` (eingefrorenes
Lineal) dürfen nicht steigen; Erwartung ist Verbesserung auf den
Wörtern der jeweiligen Klasse. (b) Die signierte doff-Attribution
der betroffenen Klasse bewegt sich Richtung 0, ohne das Vorzeichen
zu ÜBERSCHIESSEN. (c) Struktur-Wächter: `soll_cross_agree`/
`soll_zones_agree` je Wort unverändert (eine Entry-Regel darf
keine Topologie kaufen). (d) Sichtprüfung der betroffenen Wörter.
(e) Jede Regel bricht deklariert das compose-golden (Entry-
Kopplung ändert komponierte Bahnen): REGEN_GOLDEN=1-Re-Baseline im
selben PR, letter-only bleibt byte-identisch. (f) Kill: eine
Regel, die ihre eigene Klasse verbessert, aber `word_loss`/
`pair_loss` verschlechtert, wird verworfen, nicht nachgestimmt;
ein K2, dessen Winkel-Drehung das Fehlerbild der verworfenen
Stub-Trims reproduziert, widerlegt die Winkel-Hypothese —
ehrliches Negativ mit Datum; keine Adoption allein auf der
Klassen-Metrik.

**Grenzen (aus der Vorstudie übernommen).** Zensur bei ≈ 0,17 xh:
das M4-Trace-Fenster ist Körperbreite ± 0,15 xh, das |cp dx|-
Histogramm bricht genau dort ab — alle Beträge sind UNTERE
Schranken. Konfundierte Köpfe h/d/l (nur ein Kontext) begründen
keine Regel — trennbar sind e (7 Kontexte), i (5), r (4), a (3).
Eine Hand, eine Norm (96 Proben). Kleine Klassen-n (K1 n=7 ·
K3 n=6 · K2 n=8+18) → das Nachkalibrierungs-Protokoll
(tintenfolger.md §7.7) greift, sobald der Bestätigungssatz
nachgefahren ist.

**P3-K1 gemessen `aug16` — verworfen per eigenem Kill, der Fund
ist die Frame-Brücke.** Umsetzung als geteilter Kopplungsindex
(`BAR_ENTRY_COUPLE_Y`; Platzierung und Verbinder lesen denselben
Anker; die Steig-Wächter für den flachen K1-Zug klassenbewusst
gelockert), Feuer-Nachweis exakt in der Klasse und nirgends sonst
(fechten f→e + t→e, streiten/unter/Seiten/Soldaten/scharfen t→e
bzw. f→e; macht/mit mit wortfinalem t byte-identisch; das
compose-golden deckt die Klasse mit keinem seiner Wörter ab und
blieb daher UNGEBROCHEN — die „bricht bauartbedingt"-Erwartung
der Vorregistrierung war falsch herum). Leiter gegen die
P2-Baseline 0,108091: 0,50 feuert nie (e-Anstrich startet über
dem Ziel — die Leiterstufe war leer), 0,56 → 0,108145 · 0,62 →
0,108190 · 0,78 → 0,108120; `pair_loss` byte-identisch (die
Abb.-20-Drills enthalten kein Balken→Rund-Paar), doff-Median
0,130 → 0,132, nicht-monoton je Wort (fechten −0,0059 bei 0,56,
+0,0023 bei 0,62, −0,0041 bei 0,78). Auf JOIN-Ebene stimmen die
Belege GEGENEINANDER: fechtens t→e halbiert sich (0,12 → 0,06),
streitens verschlechtert sich (0,04 → 0,07), unter bevorzugt
0,78 (0,11 → 0,10). Kill (a) feuert (word_loss steigt bei jedem
feuernden Arm, die Klasse verbessert sich nicht kohärent), also
VERWORFEN; `BAR_ENTRY_COUPLE_Y` bleibt DEKLARIERT-ABER-NEUTRAL
(None) für die Bestätigungssatz-Nachkalibrierung (K1 ruht auf
n = 7). Der Fund: die Vorstudien-Konstanten sind im FIT-Frame
kohärent (MAD 0,002!), aber die Brücke in den Composer — der
Kopplungshöhen-Knopf bei gebundener Floor-Platzierung
(`bar_rise_floor` bindet in allen Klassenwörtern) — reproduziert
sie nicht: dieselbe Arkaden-Lektion (Beleg-Varianz am
Ruler-Punkt) eine Klasse weiter, PLUS die neue Hypothese, dass
nicht die KOPPLUNGSHÖHE, sondern die VERBINDERFORM (gekrümmter
Einfall statt gerader Balken-Linie) den +126°-Ankunftsfehler
trägt — das wäre ein anderer Knopf und braucht seine eigene
Vorregistrierung. K3 und K2 werden trotzdem gemessen (andere
Mechanismen), mit entsprechend gedämpfter Erwartung.

**P3-K3 gemessen `aug16` — verworfen am Paar-Gate; der Fund ist
der Wort/Drill-Split.** Vorab die Diagnose: die Klasse koppelt
heute INKONSISTENT — o→r trimmt auf den generischen 0,78-Punkt
(ÜBER dem Soll-Band 0,685), o→n/w→i koppeln am Chart-Fuß
(0,58–0,63, darunter), weil ein Spline-Resampling-Zittern von
0,0004 xh den strengen Monotonie-Wächter von
`_entry_couple_index` abbrechen lässt — der generische O2-Trim
ist für Arkaden-Köpfe still deaktiviert (eigener
Bugfix-Kandidat, nicht in dieser Regel behoben; K3 nutzt einen
jitter-toleranten lokalen Scan, Schwelle 0,02/Sample). Regel
umgesetzt als klassen-einheitliche Kopplung bei Fuß + Lift
(ersetzt beide Fehlstände), Feuer-Nachweis exakt in der Klasse
(von o→n · will w→i · Zorn/Sporn o→r · Drills on/bi/wi),
Kontrollen (kann/wenn/schwer/zwei) byte-identisch, das
compose-golden bricht hier WIRKLICH (wovon/Morgen tragen die
Klasse). Leiter: words 0,108091 → 0,108082 (0,07) → 0,107971
(0,11) — die WÖRTER stimmen erstmals größtenteils GLEICHGERICHTET
für die Regel (von −0,0090 · will −0,0019 · Sporn +0,0002 ·
Zorn +0,0031); aber pairs 0,146602 → 0,147337 (0,07) → 0,147162
(0,11), getragen vom Drill `on` (+0,0172, dazu bi +0,0018,
wi −0,0006). Gate (a) verlangt BEIDE Lineale → VERWORFEN,
`COVER_ARCADE_ENTRY_LIFT` bleibt DEKLARIERT-ABER-NEUTRAL (0,0)
für die Bestätigungssatz-Nachkalibrierung (K3 ruht auf n = 6).
Der Fund: das Wort `von` und der Drill `on` — nach H2-Doktrin
DERSELBE Übergang derselben Hand — stimmen am Ruler
GEGENEINANDER (−0,0090 vs. +0,0172); die Beleg-Varianz-Serie
(Arkaden-Luft · K1 · K3) hat damit ihre dritte Ausprägung:
Wort-Platte vs. Paar-Drill. Offen bleibt der gemessene
o→r-Überstand (0,78 komponiert vs. 0,685 Soll), den Zorn beim
Absenken trotzdem ablehnt.

**P3-K2 gemessen `aug16` — eindeutig verworfen: beide Lineale
monoton gegen die Drehung.** Umsetzung als gedrehter Abgang auf
dem geretteten Chord (`LOOP_ROUND_EXIT_ROT_DEG`; der d→Rund-Zug
ist heute der High-Reversal-gerettete STRAIGHT-Chord — die Kubik
krümmt mit gedrehtem d_out den Start, die Ankunft behält ihren
Chord; der zweimal verworfene Stub-Trim blieb unangetastet).
Feuer-Nachweis exakt in der Klasse (laden/der d→e · das/Soldaten
d→a · Drill do; die d→i still), nur das Verbinder-Item bewegt
sich. Leiter: words 0,108091 → 0,108286 (+24°) → 0,108409
(+48°), pairs 0,146602 → 0,146694 → 0,146764 — BEIDE Lineale
monoton schlechter, ohne Klassen-Split. Kill (a) feuert glatt →
VERWORFEN, Konstante bleibt deklariert-aber-neutral (0,0). Damit
ist die P3-Runde KOMPLETT: alle drei vorregistrierten
Entry-Regeln sind gemessen und ehrlich negativ — die im
FIT-Frame hochkohärenten Kopf-Konstanten der Vorstudie
überleben die Brücke in den Composer an KEINEM der drei
registrierten Knöpfe am aktuellen Ruler-Punkt. Stehend bleiben:
(i) die Verbinderform-Hypothese für den +126°-Balken-Fehler
(eigene Pre-Reg), (ii) der Jitter-Bugfix am O2-Trim (eigene
Pre-Reg, latent für ALLE Arkaden-Köpfe), (iii) die
Nachkalibrierung aller drei Knöpfe am Bestätigungssatz
(Klassen-n 6–8 sind der wahrscheinlichste Grund, warum
Median-Regeln gegen Beleg-Varianz verlieren).

### Wächter als Produktions-Kette `aug16` — Vorregistrierung: die gewachte Bahn wird die gespeicherte

Geschrieben und committet VOR der ersten Zahl der Messung.
Owner-Entscheid der Namensrunde (2026-08-16): „Kette+ sollte
einfach das einzige Kette sein" — fit-erfundene Kreuzungen sind
nie richtig (join-gebildete stecken im Soll-Budget, Hand-vs-
Komposition-Lücken sind Composer-Defekte). Die Duell-Seite zeigt
das schon; DIESER Eintrag misst die PRODUKTIONS-Seite: sollen die
`traced`-`word_instances` (die 53 nicht nachgefahrenen Wörter +
Drills) künftig die STRUKTUR-GEWACHTE Bahn speichern statt der
rohen Kettenfit-Bahn?

**Konfiguration.** Exakt die Ebene, die die Duell-Seite als
„Kette" führt: `follow_word_chain` mit `structure_guard` (Arm ⑨,
Budget aus der eigenen Chain-Initialisierung, Retry-Leiter wie
released) auf der Basis `prox 0.1 · rounds 2 · coverage 0.3`;
Kontroll-Arm die rohe Kette (`rounds 0`, derselbe Codepfad).
Beide über ALLE 63 Wörter des words-Sets (nicht nur die 17
Dev-Fälle — die Produktion speichert alle).

**Bindende Leitplanke (aus §2.2 der Kampagne):** der Tausch darf
NUR `word_record["strokes"]` betreffen — `occurrences`,
`letter_gate`, `instances` und alle Messungen bleiben die des
Kettenfits; `pair_aggregates` sieht Chain-Verbinder ohnehin nie.
Kein DB-Write in diesem Schritt: die Messung läuft offline über
die eingefrorenen Fixtures; der Re-Harvest selbst braucht
Owner-Go + dbsnapshot und `provenance` bleibt `traced`
(`fit_path` würde die gewachte Herkunft tragen).

**Messgrößen.** (a) Auf den 10 authored-Referenzen: `dtw_xh`
gepaart gewacht vs. roh — Arm ⑨ maß Δ exakt 0 auf den Dev-Fällen,
erwartet wird NEUTRALITÄT. (b) Auf ALLEN 63 Wörtern (referenzfrei
messbar): die Strukturzähler v2.1 gegen das je-Wort-SOLL
(`soll_cross`/`soll_zones`-Abstände) — die rohe Kette erfand auf
den Dev-Wörtern ~21 Kreuzungen über ihre eigene Initialisierung
(laden 3→11, unter 3→12); erwartet wird, dass die gewachte Bahn
je Wort näher am Soll liegt und NIRGENDS weiter. (c) `aiou`
gegen die Tintenmaske je Wort (darf nicht fallen — der Wächter
darf Ink-Deckung nicht kaufen, indem er sie opfert). (d) Marken:
`marks_missing/spurious` unverändert. (e) Laufzeit je Wort
(Produktions-Tauglichkeit; die Retry-Leiter kostet).

**Gates und Kill-Kriterien.** Adoptions-Empfehlung nur wenn:
(i) dev-`dtw_xh` gepaart |Median-Δ| ≤ 0,002 und kein Einzelwort
über +0,01; (ii) Struktur-Abstand zum Soll (Kreuzungen + Zonen,
je Wort) gewacht ≤ roh ÜBERALL und irgendwo strikt besser;
(iii) `aiou`-Median fällt nicht (> −0,005); (iv) Marken
unverändert; (v) kein Wort scheitert (failed/skipped) das roh
durchläuft. Kill: EIN Wort mit MEHR Soll-Abstand als roh →
nicht adoptiert (der Wächter-Kontrakt wäre gebrochen — das wäre
ein Bug, kein Tuning-Fall); Laufzeit im Mittel > 5 min/Wort →
Empfehlung nur mit benanntem Budget. Ergebnis wird hier datiert
nachgetragen; die ADOPTION selbst (Re-Harvest, DB) bleibt ein
eigener Schritt hinter Owner-Go.

**Gemessen `aug16` — drei Gates bestehen glänzend, das
Struktur-Gate findet die LÜCKE des einseitigen Wächters.** Beide
Läufe 63/63 ok (roh 87 min · gewacht 5,3 h = 302 s/Wort — HAARE
über dem 5-min-Budget von Gate (e), benannt). (i) dev-`dtw_xh`:
Median-Δ exakt 0,0000, drei Wörter BESSER (unter −0,0300 ·
und −0,0077 · mit −0,0003), keins schlechter — mehr als
Neutralität. (iii) `aiou` fällt NIRGENDS (min-Δ 0,0000, max
+0,1103). (iv) Marken byte-gleich. ABER Gate (ii): 1 Wort näher
am Soll (unter 3→2, eine Zonen-Erfindung weg), 59 gleich,
**3 Wörter WEITER weg** — und alle drei sind Kreuzungs-VERLUSTE
(Sporn cross 3→2 bei Soll 3 · einer 1→0 bei Soll 1 · er-3 1→0
bei Soll 1): der released Wächter deckelt nur ERFINDUNGEN über
das Init-Budget, die Tinten-Anziehung darf aber ungestraft eine
kleine Schleife KOLLABIEREN. Per Kill-Kriterium NICHT adoptiert.
Rettungsweg (benannt nach §7.9-Regel, hier sofort ausgeführt):
**der zweiseitige Wächter** — die K0-Invariante sagt, die
Strukturzahl ist deterministisch aus dem Duktus, also ist das
Init-Budget in BEIDE Richtungen bindend; ein Round, der eine
Init-Kreuzung verliert, wird genauso zurückgewiesen wie einer,
der eine erfindet.

**Vorregistrierter Folge-Arm (zweiseitig), VOR seiner ersten
Zahl:** identische Konfiguration, `structure_guard` prüft
Gleichheit statt Obergrenze (`--structure-guard-two-sided`,
Retry-Leiter unverändert). Erwartung: die drei Verluste
verschwinden (Retry oder Rückfall auf die Vorrunden-Geometrie),
unter behält seinen Gewinn, dev-dtw bleibt im (i)-Band —
plausibel opfert `unter` einen Teil der −0,0300, wo der Gewinn
aus einem Verlust-Round kam. Gates unverändert die von oben;
Kill unverändert: EIN Wort weiter vom Soll als roh → nicht
adoptiert.

**Zweiseitig gemessen `aug16` — erst der Umgebungs-Fund, dann
ein sauberes Pareto-Bild.** Der erste Vergleich (2s gegen die
Nacht-Baseline) zeigte 6 scheinbare Regressionen — die Isolation
entlarvte sie als MESSFEHLER DES AUFBAUS: **der Ketten-Solve ist
über BLAS-Thread-Umgebungen hinweg nicht bit-reproduzierbar**
(dasselbe Wort, derselbe Code, rounds 0: capped-1-job vs.
uncapped-3-jobs ergeben verschiedene Bahnen; an
Struktur-Grenzfällen kippen dann Zähler). Der Revert-Pfad des
Wächters ist dagegen KORREKT (Isolations-Paar rounds-0 vs.
zweiseitig-revertiert byte-identisch). Zwei Konsequenzen,
stehend: Solve-Vergleiche nur noch in IDENTISCHER Umgebung
(`OPENBLAS_NUM_THREADS`/`OMP_NUM_THREADS` gepinnt), und eine
Produktions-Verdrahtung muss die Thread-Zahl pinnen. Nebenbei
löste der Pin das Laufzeit-Gate (e) vollständig: die
Thread-Übersättigung (3 Worker × ~15 Threads auf 8 Kernen) war
der ganze Kostentreiber — gedeckelt läuft die rohe Kette über
63 Wörter in 2,7 min und der ZWEISEITIGE Wächter in 18,3 min
(≈ 17 s/Wort, weit unter dem 5-min-Budget; einseitig-ungedeckelt
waren es 5,3 h).

Der SAUBERE Vergleich (Kette und 2s-Wächter in identischer
Umgebung, 63/63 ok): Gate (ii) Struktur: **0 besser · 63 gleich ·
0 schlechter** — Gesamt-Soll-Abstand exakt 104 = 104; der
beidseitige Veto friert die Struktur konstruktionsbedingt auf
Init-Niveau ein (auch unters Zonen-REPARATUR aus dem einseitigen
Lauf wird vetiert — der Preis der Symmetrie). Gate (i) dev-dtw:
Median-Δ 0,0000, max-Δ 0,0000, zwei Wörter besser (und −0,0077 ·
mit −0,0003), keins schlechter. Gate (iii) aiou: min-Δ −0,0023
(Sporn, über der −0,005-Schranke), max +0,1199. Gate (iv) Marken
byte-gleich. FORMAL: die Adoptionsbedingung verlangt „irgendwo
strikt besser" auf der Struktur-Achse — die kann ein
beidseitiger Veto NIE erfüllen; der Arm ist damit nach dem
Buchstaben der Vorregistrierung NICHT adoptiert, obwohl er auf
jeder gemessenen Achse gleich-oder-besser ist (nie schlechter:
Struktur eingefroren, Tinte näher, Hand-Abstand nie größer).
LESART: der zweiseitige Wächter ist die SICHERE Produktions-Bahn
(primum non nocere gegenüber der rohen Kette), und die
Entscheidung wird eine Owner-Abwägung statt eines Gate-Automatismus:
(a) zweiseitig adoptieren (sicher, tinten-näher, Struktur =
Kette), (b) rohe Kette behalten, (c) der benannte RETTUNGSWEG
für „strikt besser": der **soll-bewusste K0-Wächter** —
Struktur-Änderung nur zulassen, wenn sie sich dem
Kompositions-Soll NÄHERT (die Richtung, die die
Kreuzungs-Invariante ohnehin vorzeichnet; als „Topologie-Budget
K0" seit aug15 als künftiger Arm benannt). Der wäre eine eigene
Vorregistrierung; bis dahin bleibt die Produktions-Adoption
offen und der Re-Harvest hinter Owner-Go + dbsnapshot.

**Vorregistrierung `aug19` — der soll-bewusste K0-Wächter
(Rettungsweg (c)), VOR seiner ersten Zahl.** EIN Knopf:
`--structure-guard-soll` (`FollowWeights.structure_guard_soll`,
impliziert den Wächter; Basis-Konfiguration unverändert die der
Produktions-Messung: prox 0,1 · rounds 2 · coverage 0,3). Die
Akzeptanzregel wird ein INTERVALL je Klasse: mit B = Zählung am
Chain-Optimum (dem Init der Runden, wie bisher) und S = Zählung
der KOMPONIERTEN Init-Geometrie (die Bahn bei x0 = 0, durch
DENSELBEN Assembler und DIESELBEN v2.1-Zähler wie Budget und
Runden — das Soll ist duktus-deterministisch und hier ohne jede
Zweitimplementierung ablesbar) muss jede Klasse c des
Runden-Ergebnisses in [min(B_c, S_c), max(B_c, S_c)] liegen:
Bewegung nur RICHTUNG Soll, nie darüber hinaus, nie davon weg;
bei B_c = S_c friert die Klasse exakt (der zweiseitige
Spezialfall). Retry-Leiter unverändert.

**Messplan.** Beide Arme über alle 63 Wörter des words-Sets in
EINER gepinnten Umgebung (`OPENBLAS_NUM_THREADS=1`,
`OMP_NUM_THREADS=1` — die aug16-Lehre): Kontrolle = rounds 0
(die rohe Kette durch denselben Codepfad), Kandidat =
soll-bewusst gewacht; `--candidate-out` beider Läufe, Zahlen
über den tracebench-File-Provider (dev-19) plus eine
referenzfreie Auswertung über alle 63 (Strukturzähler vs.
Soll-Spalten aus `tools.tracebench.soll`, `aiou` gegen
`ref_mask.png`). Die 9 versiegelten authored-Zeilen werden dabei
NICHT als Trace-Referenz gelesen (dev-Gate nur über die 19
Dev-Zeilen; Maske und Soll sind referenzfrei).

**Gates (die der Produktions-Messung, unverändert):**
(i) dev-`dtw_xh` gepaart |Median-Δ| ≤ 0,002, kein Dev-Wort über
+0,01; (ii) Struktur-Abstand zum Soll je Wort
(|cross−soll| + |zones−soll|) gewacht ≤ roh ÜBERALL und irgendwo
strikt besser; (iii) `aiou` je Wort min-Δ > −0,005; (iv) Marken
unverändert; (v) kein Wort scheitert, das roh durchläuft;
Laufzeit-Budget 5 min/Wort (gepinnt erwartet ≈ 20 s). Kill wie
gehabt: EIN Wort weiter vom Soll als roh → nicht adoptiert (das
wäre ein Wächter-Bug). Erwartung: unters Zonen-Reparatur aus dem
einseitigen Lauf kehrt zurück (Init 12 → Richtung Soll), die
drei Kreuzungs-Kollapse (Sporn/einer/er-3) bleiben vetiert,
„irgendwo strikt besser" wird damit erstmals erfüllbar. Besteht
alles, ist die Adoptions-EMPFEHLUNG automatisch erfüllt; der
Re-Harvest selbst bleibt Owner-Go + dbsnapshot.

**Gemessen `aug19` — vier von fünf Gates bestehen (Gate (i)
sogar mit SIEBEN strikten dtw-Gewinnen), die Struktur-Klausel
bleibt formal unerfüllbar — und das Runden-Protokoll benennt
den Mechanismus exakt.** Beide Arme 63/63 ok, identisch
gepinnte Umgebung, gewacht 651 s gesamt (≈ 10,3 s/Wort — weit
im Budget). (i) dev-19 gepaart: Median-Δ 0,0000, KEIN Wort
schlechter, sieben strikt besser (das −0,0123 · und −0,0074 ·
muß-2 −0,0065 · und-3 −0,0041 · will/mit/und-2 klein); der
eigene dev-Median fällt 0,0576 → 0,0494. (iii) `aiou` je Wort
NIE negativ, bis +0,108 (und), dev-Median +0,024; beide
Chamfer-Hälften besser. (iv) Marken byte-gleich 1+1.
(ii) ABER: Gesamt-Soll-Abstand exakt **107 = 107** (0 besser ·
63 gleich · 0 schlechter) — wieder friert die Struktur. Das
`unter`-Protokoll zeigt warum: Runde 1 bewegt overlap 3 → 2
(RICHTUNG Soll 0, im Intervall erlaubt), bündelt das aber im
selben Solve mit touch 3 → 6 (WEG vom Soll 0) — die
runden-ATOMARE Rückweisung (auch nach zwei Halbierungs-Retries)
verwirft die Reparatur mitsamt der Verletzung. Die Soll-Richtung
ist also nicht die Schranke; die ATOMARITÄT ist es. NICHT
adoptiert (nach dem Buchstaben der Klausel), aber als
PRODUKTIONS-KandIDAT dominiert der soll-bewusste Wächter den
zweiseitigen auf jeder gemessenen Achse (nirgends schlechter,
sieben Dev-Wörter strikt tinten-näher, aiou bis +0,11, Struktur
= Kette). Die Owner-Abwägung erweitert sich auf: (a) zweiseitig
· (b) roh · (c′) **soll-bewusst (die beste sichere Bahn dieser
Messreihe)** · (d) der benannte nächste Mechanismus für „strikt
besser": **zonale Rückweisung** — nicht der ganze Round wird
verworfen, sondern nur die Anker-Nachbarschaft der
VERLETZENDEN Zone wird auf die Vorrunden-Geometrie zurückgesetzt
bzw. eingefroren und nachgelöst, sodass eine gebündelte
Soll-Reparatur den Round überlebt (eigene Vorregistrierung,
§7.9-Zeile im selben PR).

### Route „Lotse" `aug16` — Vorregistrierung: Skelett fahren, Duktus als Karte

Geschrieben und committet VOR der ersten Bench-Zahl. Owner-Idee
(2026-08-16, tintenfolger.md §7.8): nicht Buchstabe auflegen und
verformen (Kette), sondern wie die Nullprobe DIREKT auf der
Tinten-Mitte fahren und nur an Entscheidungsstellen den Duktus als
KARTE fragen. Arm ⑨s Fazit („Tinten-Gewinn und Struktur-Erfindung
in DIESER Formulierung untrennbar") benannte genau diese andere
Formulierung als Rettungsweg (§7.9).

**Implementierung** (`tools/inkpilot`, Anzeige-Name „Lotse"):
Karte = die komponierte Bahn in Crop-px (wordlab-Transform auf der
gefitteten Registrierung der Zeile); Wasserweg = der
routeg-Skelettgraph; Ritt = GLOBALE Zuordnung Karten-Sample →
Grat-Punkt (Viterbi über die Sample-Kette: Graph-Fahrkosten +
Karten-Abweichung + Brücken-Zustand), verbunden über kürzeste
Pixelketten-Wege — der Abbiege-Entscheid an jeder Kreuzung fällt
aus der Route der Karte; Kanten dürfen doppelt gefahren werden
(Retrace); wo keine Tinte liegt, überbrückt die Karte; führende und
folgende Brücken ohne Wieder-Aufstieg werden GETRIMMT (komponierte
Luft ist kein Federstrich). Kein #278-Bruch: Ordnung, Richtung und
Marken-Zuweisung kommen vollständig vom Prior. v0-Konstanten
(unkalibriert, deklariert): `SAMPLE_STEP` 0,12 xh · `BOARD_RADIUS`
0,6 xh · `DEVIATION_WEIGHT` 2 · `BRIDGE_EMIT` 2,5×Radius ·
`MAX_RIDE_FACTOR` 8. Laufzeit ~0,1–0,3 s/Wort (kein Solver).
Unit-Tests auf dem synthetischen Kreuz: Gleistreue, Karten-Abbiegen
an der Kreuzung, Luft-Trimm, Lücken-Brücke, Frame-Roundtrip.

**Messgrößen (Dev-Split, gegen die eingefrorene Baseline).**
(a) `dtw_xh` gepaart Lotse vs. Kette (Baseline 0,062 med) — die
Hypothese der Route: Tinten-Mitte + Karten-Ordnung schlägt den
Mess-Fit als NACHFAHRER. (b) Strukturzähler + Soll-Spalten (die
Karte bringt das Soll mit; erfundene Kreuzungen wären
Graph-Artefakte). (c) `marks_missing/spurious` (Marken per Karte
zugewiesen). (d) `aiou` (konstruktionsbedingt hoch — Erwartung ≥
Kette). (e) Brücken-Anteil je Wort als QC-Spalte — viel Brücke
heißt, die KARTE verließ die Tinte: ein Kompositions-Defizit, kein
Lotse-Fehler, report-only ausgewiesen.

**Gates und Kill-Kriterien (relativ, keine publizierten Zahlen).**
Ernst zu nehmen ist die Route, wenn `dtw_xh` gepaart die Kette
schlägt (Median der Differenzen < 0, Sign-Test beschreibend) OHNE
Netto-Verschlechterung bei Kreuzungen und Marken. Kill:
Struktur-Erfindungen über der Kette (Graph-Grate erzeugen
Falsch-Kreuzungen) oder Marken-Verluste → Formulierung zurück ans
Reißbrett, ehrliches Negativ mit Fund. Erwartete Fehlermodi
benannt: der Pixel-Zickzack der 8er-Skelettkette (kostet dtw
wenig, ist der benannte Feinschliff-Kandidat), Doppelpass-Zonen
(das Skelett hat EINE Linie, wo die Hand zwei schrieb — der Ritt
fährt sie zweimal, korrekt per Karte, aber deckungsgleich statt
versetzt), der ß-Kringel in muß.

**v0.1 gemessen `aug16` — Gate verfehlt, aber mit dem stärksten
Einzelwort-Fund der Kampagne.** Dev-Split, 10/10 ok, 22,5 s
Gesamtlauf. `dtw_xh` Median 0,119 gegen Kette 0,062 — die Route
verliert den Median klar (8/10 Wörter schlechter). ABER die
Verteilung erzählt zwei Geschichten: **unter — das
Katastrophen-Wort der Kette (0,4501, der Stapel-Kollaps) — fällt
auf 0,0641 (−0,386)**, muß ebenfalls besser (−0,021), und `aiou`
steigt fast überall (laden 0,686 → 0,801 · will 0,753 → 0,816 —
die Tinten-Mitte hält, was die Nullprobe versprach). Die zwei
Verlust-Mechanismen, beide vorregistriert erwartet, einer davon in
voller Stärke: (1) **`cross_cand = 0 auf JEDEM Wort** — 23
Hand-Kreuzungen fehlen komplett: wo Striche sich kreuzen, teilen
sich die Ritte die SELBEN Skelett-Pixelketten durch den Knoten,
zwei Pässe fallen deckungsgleich zusammen und schneiden sich nie
transversal (stattdessen 12 unechte Retrace-Zonen,
`retrace_arc_ratio` 2,49). (2) `und` bricht aus (+0,294) —
Autopsie: die Geometrie ist praktisch PERFEKT (Chamfer beidseitig
0,031/0,053, besser als die Kette), der dtw-Ausreißer besteht aus
einem 4,15-xh-Deckungs-Doppelritt am d-Stamm (der A5-Fall in
Reinform) plus einem Klassifikations-Kipp: der
skelett-VERKÜRZTE u-Deckbogen des Lotsen (Skelett endet eine
halbe Strichbreite vor der Tintenspitze) fällt unter die
0,8-xh-Marken-Schwelle, der längere der Hand nicht — die
Body-Mengen unterscheiden sich strukturell und das forward-DTW
zahlt den ganzen Umweg. Kill-Kriterium „Struktur-Erfindung"
feuert NICHT (0 unechte Kreuzungen, 0 Marken-Verluste) — aber das
Gate (Kette schlagen ohne Struktur-Netto-Verlust) ist verfehlt:
VERWORFEN als v0.1, Route NICHT geschlossen. Rettungswege
(§7.9-Regel): (i) **der versetzte Doppelpass aus Breiten-Evidenz**
— genau §7-Maßnahme A5: auf mehrfach gefahrenen Kanten die Pässe
um einen Bruchteil der GEMESSENEN lokalen Strichbreite
(`width_map` liegt im Fixture!) senkrecht auseinanderlegen, dann
schneiden sich die Züge transversal wie die Hand; (ii) der
Feinschliff über den Pixel-Zickzack; (iii) die und-Autopsie.

**Vorregistrierter v0.2-Arm (A5, versetzter Doppelpass), VOR
seiner ersten Zahl.** EIN Knopf: `DOUBLE_PASS_OFFSET_FRACTION` —
jeder Ritt-Punkt auf einem Skelett-Pixel, das im WORT insgesamt
mehrfach befahren wird, weicht um diesen Bruchteil der lokalen
EDT-HALBBREITE (`width_map` des Fixtures) NACH RECHTS seiner
Fahrtrichtung aus; gegenläufige Pässe trennen sich dadurch von
selbst auf gegenüberliegende Seiten (die Vorzeichen-Konvention
der Hand), gleichläufige (Overlap-Klasse) bleiben deckungsgleich,
Einfachpässe und Brücken bleiben unberührt (Tinten-Mitte hält).
Leiter 0,0 (= aus) / 0,35 / 0,5. Erwartung: die 23 fehlenden
Kreuzungen kehren mehrheitlich zurück (transversale Schnitte an
den getrennten Pässen), `retrace_arc_ratio` fällt Richtung 1,
`und` verliert seinen Doppelritt-Anteil; `aiou` darf dafür
minimal nachgeben (der Versatz verlässt den Grat um < eine halbe
Strichbreite — per Definition innerhalb der Tinte). Gates wie
v0.1; Zusatz-Kill: sinkt `aiou` im Median um > 0,02, kauft der
Versatz Struktur mit Tinten-Deckung und wird verworfen.

**A5-Arm gemessen `aug16` — verworfen; der Parallel-Versatz ist
der falsche Mechanismus, der richtige heißt Knoten-Sehne.**
Leiter (dev, 10/10 ok): 0,35 → dtw 0,1156 · aiou −0,018 (hält
das Zusatz-Kill knapp) · aber nur **3 von 23 Kreuzungen kehren
zurück** (+2 unechte); 0,5 → 13 fehlend (+6 unechte), aiou
−0,032 → vom eigenen Zusatz-Kill VERWORFEN. Die Erwartung
(„mehrheitlich zurück") verfehlen beide klar, Konstante bleibt
0,0. Der Fund: versetzte Pässe sind getrennte, aber weiterhin
FAST PARALLELE Züge — der Kreuzungs-Detektor verlangt zu Recht
einen echten Schnittwinkel (≥ 15°), und den erzeugt ein
Parallel-Versatz nur an den flachen Zonen-Enden, nicht dort, wo
die Hand kreuzt. Die Hand kreuzt am KNOTEN in echten Winkeln:
zwei Pässe treten aus vier verschiedenen Richtungen durch die
Kreuzungs-Nachbarschaft, das Skelett zwingt beide auf dieselbe
geteilte Schiene und knickt sie um die Ecke. Der präzisere
Rettungsweg (benannt, eigene Messung): **der Knoten-Sehnen-
Schnitt** — wo ein Ritt einen Verzweigungsknoten durchquert,
lokal die SEHNE seines eigenen Eintritts→Austritts fahren statt
der geteilten Knoten-Schiene (die Kreuzung entsteht dann von
selbst, wo sich zwei Sehnen schneiden — die Extrapolations-Idee
der §13a-Landmark-Ziele, hier als Konstruktion statt als
Zielterm).

**Vorregistrierter v0.3-Arm (Knoten-Sehne), VOR seiner ersten
Zahl.** EIN Knopf: `JUNCTION_CHORD_RADIUS_FRACTION` — um jeden
VERZWEIGUNGS-Knoten (≥ 3 einlaufende Kanten) wird eine
Nachbarschaft vom Radius Knopf × lokale EDT-Halbbreite gelegt;
jeder maximale Lauf von Ritt-Punkten innerhalb dieser
Nachbarschaft (eine Knoten-Durchquerung) wird durch die GERADE
SEHNE seiner beiden Randpunkte ersetzt, sofern der Lauf kurz ist
(Bogen < 4 × Radius — ein Zug, der den Knoten nur streift, bleibt
unangetastet). Zwei Pässe aus verschiedenen Richtungspaaren
erzeugen zwei verschiedene Sehnen, die sich in echtem Winkel
schneiden; auch der EINFACH-Pass profitiert (die Sehne begradigt
den Umweg, den die geteilte Skelett-Schiene der Feder andichtet
— die publizierte Junction-Verschiebung um ±Strichbreite).
Leiter 0,0 (= aus) / 1,0 / 1,5. Erwartung: fehlende Kreuzungen
kehren am KNOTEN zurück (nicht an Zonen-Enden wie beim
Parallel-Versatz), dtw fällt auch auf kreuzungsarmen Wörtern
leicht (Umweg-Begradigung); `aiou` gibt in der
Knoten-Nachbarschaft nach — dieselbe Zusatz-Kill-Schranke wie
A5 (Median-Δ > −0,02 verworfen). Übrige Gates wie v0.1.

**v0.3 gemessen `aug16` — verworfen; der Fund lokalisiert die
fehlenden Kreuzungen endgültig.** Leiter (dev, 10/10 ok):
1,0 → dtw 0,1211 · aiou 0,702 (−0,045!) · Kreuzungen 23 → 21
fehlend; 1,5 → dtw 0,1252 · aiou 0,637 (−0,110) · 19 fehlend.
Beide Stufen vom aiou-Zusatz-Kill VERWORFEN, beide Knöpfe bleiben
0,0. Der Fund: nur 2–4 der 23 fehlenden Kreuzungen sitzen an
Punkt-Knoten — die Mehrheit liegt auf **LANGEN geteilten
Schienen** (bis 4 xh: der Schleife-auf-Stamm-Kollaps der
Skelettierung verschmilzt die zwei Pässe der Hand über die ganze
Überlappungsstrecke), und dort erreicht keine lokale
Knoten-Chirurgie sie; die Sehnen kosten dafür ÜBERALL Deckung
(auch Einfach-Pässe durch gekrümmte Knoten werden begradigt, wo
die Feder wirklich kurvte). Damit sind die drei Lotse-Verluste
mechanisch vollständig kartiert und die zwei ehrlichen Wege
benannt (§7.9): (i) **Sub-Strich-Trennung aus Breiten-Evidenz
über ganze Zonen** — wo die gemessene Breite die
Einfachstrich-Breite deutlich übersteigt, liegen zwei Pässe in
der Tinte; ihre Trennung ist ein eigenes Forschungsstück (die
A5-Intuition war über die EVIDENZ richtig und über die GEOMETRIE
falsch); (ii) pragmatisch die **Karten-Vorfahrt in
Doppelpass-Zonen** — der Lotse hält die Karte ohnehin in der
Hand, und die Karte HAT die Kreuzung (das Soll ist
duktus-deterministisch): in Zonen, die die Karte als Doppelpass
ausweist, fährt der Zug die KARTE statt der degenerierten
Schiene — der Brücken-Modus, gezielt eingesetzt. Beides eigene
Vorregistrierungen; v0.1 bleibt der gemessene Stand der Route. Der
unter-Befund steht unabhängig davon: wo der Ketten-Fit
strukturell scheitert, liefert die Karten-Fahrt bereits jetzt
eine um Faktor 7 bessere Bahn — die Fusion („Vier Augen") hat
damit ihr erstes gemessenes Argument.

**Vorregistrierter v0.4-Arm (Karten-Vorfahrt in Doppelpass-Zonen),
VOR seiner ersten Zahl.** Der v0.3-Fund lokalisierte die fehlenden
Kreuzungen auf den LANGEN geteilten Schienen (Skelett verschmilzt
die zwei Pässe der Hand über die ganze Überlappungsstrecke); dort
ist die Schiene DEGENERIERT und die KARTE hat die Wahrheit (das
Struktur-Soll ist duktus-deterministisch, die Komposition schreibt
den Doppelpass mit Kreuzung). EIN Knopf: `MAP_PRIORITY_IN_RETRACE`
(aus/an) — Karten-Samples, die in einer SELBST-Retrace-Zone der
Karte liegen (Zonen via `core.geometry.detect_retrace_pairs` auf
den Karten-Strichen, dem Detektor des eingefrorenen Lineals, hier
nur LESEND auf der Karte), bekommen im Viterbi ausschließlich den
Brücken-Zustand: der Zug fährt dort die Karte selbst, mit ihrer
komponierten Kreuzung und ihrem versetzten Doppelpass; außerhalb
der Zonen ändert sich nichts. Erwartung: die Schienen-Klasse der
fehlenden Kreuzungen kehrt zurück (und der 4-xh-Doppelritt in
`und` verschwindet), `aiou` gibt nur INNERHALB der Zonen nach —
dieselbe Zusatz-Kill-Schranke (Median-Δ > −0,02 verworfen);
übrige Gates wie v0.1. Zusätzliche QC-Spalte: Karten-Anteil je
Wort (Brücken-Bogen/Gesamt-Bogen), report-only.

**Vorregistrierter Zusatz-Arm (Schienen-Auslauf), VOR seiner
ersten Zahl — Owner-Fund an der v0.1-Sichtprüfung (2026-08-16):
„beim d geht die Linie nach der Kreuzung nicht weiter bis zum
Ende".** Diagnose: die KARTE endet dort, wo die Komposition den
gebundenen Schleifen-Abgang an der Kreuzung trimmt (Loop-Exit-
Regel) bzw. wo der komponierte Auslauf generell kürzer reicht als
die Tinte (der +7–10-%-Reichweiten-Befund der P3-Vorstudie) — und
der Lotse fährt nur, wohin die Karte führt; die getintete Spitze
hinter dem letzten Karten-Sample bleibt ungeritten. EIN Knopf:
`TAIL_RUNOUT_MAX_UNITS` — endet ein Ritt-Strich auf einer
Schiene, die ohne Verzweigung in einen Grad-1-ENDPUNKT des
Skeletts ausläuft, und liegt dieser näher als der Knopf (in xh),
fährt der Zug bis zum Schienen-Ende weiter (symmetrisch am
Strich-ANFANG). Leiter 0,0 (= aus) / 0,6 / 1,0. Erwartung: die
d-Spitzen und Wort-Ausläufe schließen (sichtbar + `dtw` an den
betroffenen Wörtern), `aiou` steigt eher (mehr getintete Bahn
gedeckt), keine Struktur-Änderung (ein Grad-1-Auslauf kann weder
kreuzen noch retracen). Kill: verlängert der Auslauf in
Wirklichkeit einen SPORN des Skeletts (unechte Marken/Spitzen —
`marks_spurious` oder `dtw` netto schlechter), wird er verworfen.

**Beide Arme gemessen `aug16` — der Owner-Fund-Arm ADOPTIERT, die
Karten-Vorfahrt ehrliche Null.** (a) Schienen-Auslauf (dev,
10/10 ok): 0,6 → dtw 0,1053 · 1,0 → **dtw 0,1007** (v0.1: 0,1192),
`und` **0,3428 → 0,0874** — die fehlende d-/Auslauf-Spitze WAR der
Ausreißer —, `aiou` 0,747 → 0,765, `marks_spurious` 3 → 1 (der
verlängerte u-Deckbogen springt zurück über die
0,8-xh-Marken-Schwelle: auch der Klassifikations-Kipp der
und-Autopsie heilt), Kreuzungen exakt unverändert (23 fehlend —
wie konstruiert), `retrace_spurious` 12 → 14 (+2, benannt: zwei
verlängerte Enden fallen in Deckungs-Zonen). Gates bestanden →
**ADOPTIERT, `TAIL_RUNOUT_MAX_UNITS` = 1,0.** (b) Karten-Vorfahrt:
dtw 0,1179 · aiou −0,014 · Kreuzungen 22 statt 23 fehlend (+1
unecht) · `und` UNVERÄNDERT — die SELBST-Retraces der Karte sind
in den Dev-Wörtern zu selten (das t mit Stamm-Rückpass kommt nur
in mit/unter/streiten vor, unds Doppelritt entsteht RITT-seitig
an einer Tinten-Schleife, die die Karte nur EINMAL passiert): der
Karten-Trigger war die falsche Zone. VERWORFEN (Erwartung klar
verfehlt), Knopf bleibt False; benannter Nachfolger: dieselbe
Karten-Fahrt, aber in RITT-seitig erkannten Doppelzonen (die
A5-Erkennung, die v0.4-Geometrie — Kombination, eigene Pre-Reg).
Stand der Route damit: dev-dtw 0,101 gegen Kette 0,062 (Lücke
2,0× → 1,6×), `aiou` klar über der Kette, Kreuzungs-Kollaps auf
geteilten Schienen bleibt DER offene Block.

### Route „Lotse" v0.5 `aug16` — Vorregistrierung: Karten-Geometrie in Ritt-Doppelzonen

Geschrieben und committet VOR der ersten Zahl. Die benannte
Kombination aus den zwei verworfenen Armen: die ERKENNUNG des A5
(wo besucht der Ritt dasselbe Skelett-Pixel mehrfach — dort ist
die Schiene degeneriert, das Skelett hat die zwei Hand-Pässe
verschmolzen) mit der GEOMETRIE des v0.4 (dort die Karte fahren,
die den Doppelpass MIT Kreuzung komponiert). EIN Knopf:
`RIDE_DOUBLE_MAP_PRIORITY` (aus/an) — die Sample-Zuweisungen des
Wortes werden in SCHREIB-Reihenfolge durchlaufen; ein Sample,
dessen zugewiesenes Schienen-Pixel im Wort schon einmal besetzt
wurde, fährt statt der Schiene die KARTE (sein eigenes
Karten-Sample, brücken-gleich verbunden) — der ERSTE Pass bleibt
auf der Tinten-Mitte, jeder SPÄTERE fährt die komponierte
Geometrie mit ihrer Kreuzung. Erwartung: die Schienen-Klasse der
23 fehlenden Kreuzungen kehrt substanziell zurück, `und`s
Rest-Doppelritt verschwindet, `retrace_arc_ratio` fällt Richtung
Hand-Niveau; `aiou` gibt nur in den Doppelzonen nach — dieselbe
Zusatz-Kill-Schranke (Median-Δ > −0,02 verworfen). Kill
zusätzlich: erzeugt die Karten-Geometrie in den Zonen UNECHTE
Kreuzungen über das Soll (`cross_spurious` netto > +2), ist die
Karten-Platzierung dort zu schlecht — verworfen, zurück zur
Sub-Strich-Trennung. Basis ist der adoptierte Stand (Auslauf 1,0).

**Gemessen `aug16` — ALLE Gates bestehen, ADOPTIERT.** Dev,
10/10 ok: dtw-Median 0,1007 → **0,0853**; `und` 0,0874 →
**0,0431** — schlägt dort erstmals die KETTE (0,0491); **5 der 23
fehlenden Kreuzungen kehren zurück** (18 fehlend, +1 unecht —
innerhalb der ≤+2-Schranke); `retrace_spurious` 14 → 11,
`retrace_arc_ratio` 2,48 → **1,66** (Richtung Hand, wie
vorregistriert); `aiou` −0,002 (weit innerhalb der Schranke).
`RIDE_DOUBLE_MAP_PRIORITY` = True. Routen-Stand: **0,0853 gegen
Kette 0,0620 (Lücke 1,4×)**, und die Komplementarität ist jetzt
messbar scharf — der Lotse schlägt die Kette auf genau den
STRUKTUR-schweren Wörtern (unter −0,387 · muß −0,129 ·
und −0,006), verliert auf den einfachen (die glatte
Regularisierung der Kette gewinnt, wo nichts kollabiert):
mit +0,042 · will +0,081 · zwei +0,056. Das ORAKEL der Fusion
(je Wort das bessere Verfahren, nur als Decke, kein Ergebnis):
Median **0,0563** — besser als jede Einzelroute, schlechtestes
Wort 0,113 statt 0,450 (Kette) bzw. 0,132 (Lotse). „Vier Augen"
hat damit seine erste bezifferte Decke; der ehrliche
Auswahl-Mechanismus (ohne Referenz!) ist die offene Frage — die
Lehre aus B1 (der ordnungs-blinde Ranker) gilt hier wörtlich.

**Auswähler-Diagnostik `aug16` (explorativ, KEIN Ergebnis —
festgehalten, damit die Sackgassen benannt sind):** drei
referenzfreie Signale auf den 10 Dev-Wörtern geprüft, keines
trennt: (i) Soll-Distanz der Kette (zwei hat 4 und die Kette
gewinnt trotzdem; die drei Lotse-Siege liegen bei 0–1);
(ii) p90-Tinten-Restfehler der Kette (Lotse-Siege bei
0,057–0,068, aber die/zwei gewinnen für die Kette im selben
Band); (iii) Lotse-eigene `retrace_arc_ratio` flaggt zuverlässig
nur die GROSSEN Lotse-Niederlagen (≥ 4 ⇒ Kette, 4/4), die
resultierende Einweg-Regel bleibt aber unter der Kette (Median
0,0746), weil die kleinen Ketten-Siege (Wer/linken/mit,
+0,03–0,04) mitverloren gehen. Struktur des Problems:
asymmetrische Einsätze (Kette gewinnt 7/10 knapp, Lotse 3/10
riesig) — der Auswähler braucht ein Signal für „die Kette
scheitert HIER" mit sehr niedriger Falsch-Positiv-Rate.
Kandidaten für die echte Pre-Reg, wenn der Bestätigungssatz da
ist: fit-interne Flags der Kette (at_bound/Konvergenz je Slot)
und die Kombination arc-ratio-Einweg + Restfehler. Auf n=10 wird
KEINE Regel adoptiert (Dev-Fishing-Verbot).

### Route „Lotse" v0.6 `aug16` — Vorregistrierung: der Feinschliff

Geschrieben und committet VOR der ersten Zahl. Der benannte
Kandidat aus der Duell-Review (Owner: Mikro-Wackler sichtbar,
„wenn der Schreiber der Linie mit fester Stiftdicke nachgeht,
sieht man die Wackler in der dicken Linie"): die 8er-Pixelkette
des Skeletts zickzackt mit ±0,5 px; auf den GLATTEN Wörtern, wo
die Kette heute noch gewinnt, ist das ein flächiger dtw-Beitrag.
EIN Knopf: `SMOOTH_ITERATIONS` — je Iteration das lokale Mittel
x_i ← (x_{i−1} + 2·x_i + x_{i+1}) / 4 über jeden Ritt-Strich,
ENDPUNKTE FIX (der adoptierte Schienen-Auslauf bleibt exakt);
Leiter 0 (= aus) / 2 / 4. Struktur-Wächter als Gate statt als
Code: `cross/retrace/touch/overlap`-Zähler und Marken müssen
byte-gleich bleiben (eine 1-px-Glättung, die eine Kreuzung
unmacht, ist verworfen — Ecken und Retraces sind ECHTE Merkmale,
die Doktrin der Natürlichkeitsmetrik in §5); `aiou`-Median-Δ >
−0,02 = verworfen. Erwartung: dtw fällt breit (auch auf den
Ketten-Siegen), `aiou` ~neutral (die Glättung bleibt binnen
halber Strichbreite).

**Gemessen `aug16` — beide Stufen verworfen; die
Zickzack-Hypothese ist fürs LINEAL widerlegt.** it2 → dtw 0,0860
· aiou −0,022 · Zähler NICHT byte-gleich (cross 18→17 fehlend,
1→0 unecht; retrace 0→1 fehlend); it4 → dtw 0,0869 · aiou −0,029
· retrace 0→3 fehlend. Alle drei Gates verletzt, Konstante bleibt
0. Die Lehre: das 0,02-xh-Arc-Resampling des `dtw_xh` schluckt
den ±0,5-px-Zickzack ohnehin (beide Seiten werden identisch
abgetastet) — die Glättung kauft auf der Messachse NICHTS und
bezahlt mit Tinten-Deckung und Grenzfall-Struktur. Der
Mikro-Wackler ist damit als SICHT-Problem des späteren
NACHSCHREIBERS eingeordnet, nicht als Mess-Problem: der
Feinschliff gehört, wenn überhaupt, an den KONSUMENTEN der Bahn
(Renderer/Editor-Anzeige, eine reine Darstellungsstufe), nie in
den gemessenen Kandidaten. §7.9-Zeile entsprechend.

### O2-Trim-Jitter `aug16` — Vorregistrierung: der Bugfix, der auch verlieren darf

Geschrieben und committet VOR der ersten Zahl. Der K3-Nebenfund
(§14 „Welle 2 · P3"): `_entry_couple_index` bricht seinen
Flanken-Aufstieg bei JEDEM Mini-Rückgang ab (`y[i] < y[i−1]`,
ohne Toleranz) — das Spline-Resampling der komponierten Bahnen
trägt aber ±0,0004-xh-Zittern, und so ist der generische
O2-0,78-Trim für Arkaden-Köpfe (deren Anstriche das Zittern im
ersten Schritt zeigen) STILL DEAKTIVIERT: Hoch-Exits in n/m/i/r
koppeln heute am Chart-Fuß statt am beabsichtigten 0,78-Punkt.
EIN Knopf: `ENTRY_FLANK_DIP_TOL` — der Aufstiegs-Wächter toleriert
Rückgänge bis zu diesem Betrag je Sample (in xh); ein echter
Kopf-Umschwung fällt weit schneller. Leiter 0,0 (= heutiges
Verhalten) / 0,02 (die Schwelle, die der K3-Lokalscan bereits
verwendet). BEIDE Ausgänge sind vorregistriert gültig:
(a) Bench besser oder gleich → Bugfix ADOPTIERT (die beabsichtigte
O2-Semantik gilt wieder); (b) Bench schlechter → der Bug ist
TRAGEND (das Lineal bevorzugt die Fuß-Kopplung, die der Bug
zufällig herstellt — dann ist nicht die Toleranz falsch, sondern
die O2-Zielhöhe für Arkaden-Köpfe, und DAS wird als eigener
Befund verbucht; Konstante bleibt 0, Rethink benannt). Gates:
wordbench `word_loss` + `pair_loss` (eingefroren), `soll_*_agree`
unverändert, Sichtprüfung der bewegten Wörter; compose-golden
bricht, wo Hoch-Exit→Arkade in den golden-Wörtern vorkommt
(wovon o→n! Morgen o→r!) → deklarierte Re-Baseline bei Adoption.

**Gemessen `aug16` — Ausgang (b), und der Bug erweist sich als
ZUFÄLLIGE KLASSENREGEL.** Toleranz 0,02: `word_loss` 0,108091 →
0,108095 (+4e−6, hauchdünn schlechter), `pair_loss` byte-gleich,
genau DREI Wörter bewegen sich — und sie spalten sich exakt
entlang der K3-Ankunfts-Leiter: **von (o→n) −0,0126** (der
reparierte 0,78-Trim ist für o→n ein klarer Gewinn — mehr als
K3s 0,685-Lift je holte), aber **Zorn (o→r) +0,0112** und Sporn
(o→r) +0,0017 (o→r will TIEFER ankommen, wie K3 maß). Der
Jitter-Bug implementiert heute unabsichtlich genau diesen Split
(n-Anstriche zittern im ersten Schritt → Fuß; r-Anstriche nicht →
0,78), und das Lineal bevorzugt ihn netto um Mikrometer.
VERDIKT: Toleranz bleibt 0,0 (per Kriterium (b)); der eigentliche
Befund ist, dass die UNIFORME O2-Zielhöhe für Arkaden-Köpfe falsch
ist und die richtige Struktur eine KLASSENREGEL wäre (n hoch,
r tiefer — von-Gewinn ernten, ohne Zorn zu bezahlen). Die gehört
als eigene Pre-Reg auf den Tisch, ehrlicherweise erst mit dem
Bestätigungssatz (dieselbe n≤8-Vorsicht wie bei P3); bis dahin
trägt der Bug — dokumentiert statt still.

### Re-Baseline `aug17` — der 19er-Dev-Satz: Dev-Erweiterung aktiviert, alle stehenden Routen neu vermessen

**Anlass und Deklaration.** Der Autor hat den kompletten Dev-Satz der
§2.5-Zuordnung nachgefahren (alle 19 Vorkommen `authored`, inkl. der
zwei neuen Wörter **Galoppieren** und **das** und aller
Wiederholungs-Vorkommen; Bestätigung A stand bei 5/20, B bei 4/24 —
beide bleiben versiegelt). Owner-Go in Session (2026-08-17): die
Dev-Erweiterung tritt VOR der Voll-Autorisierung in Kraft
(Aktivierungs-Nachtrag in tintenfolger.md §2.5 — die Zuordnung war
seit 2026-08-16 fixiert und performance-blind, Galoppieren/das nie
gebencht, der Weg Dev → Bestätigung existiert nicht).
`TRACEBENCH_DEV_IDS` führt seither 19 Ids (Wiederholungen splitten
als WORT, §2.5). Zugleich ist dies die deklarierte
**Doppel-Re-Baseline** der Betriebsregeln: die Fixture-Roots wurden
in der Cloud-Session über `fetch_fixtures --set all --verify` neu
gebaut (kein `--only`-Refill möglich — frischer Klon hat keine
Roots; Verify: 12 Kompositionen und alle Template-Zeilen bit-exakt
gegen die deployte API), die Vorher-Zahlen (`aug14`/`aug16`-Stände)
sind mit den heutigen NICHT vergleichbar. Alle Routen laufen mit
gepinnten BLAS-Threads (`OPENBLAS_NUM_THREADS=1`,
`OMP_NUM_THREADS=1`).

**Identitäts-Gate (vor jeder Kandidaten-Zahl): PASS auf 19/19** —
dtw 0, beide Chamfer 0, alle Zähler voll gematcht,
`direction_uncertain` 0 (auch die 9 neuen Nachfahrungen stimmen
überall mit der Duktus-Richtung des Priors überein — Galoppieren
eingeschlossen). Fixture-Qualitätssignale, keine Kandidatenfehler:
`marks_uncertain` 9/19 (der Autor zeichnet Marken teils verbunden
bzw. unter der Diakritika-Schwelle — der Bestätigungs-Brief-Hinweis
„Marken mit eigenem Absetzen" gilt weiter); `soll_cross_agree`
16/19, `soll_zones_agree` 18/19 (Abweichler unten je Wort).

**Die Kette auf dem 19er-Satz** (`--candidate chain --split dev`,
Schritt 0,02, 19/19 gescort, 0 failed, 163 s):

```
dtw_xh_median:   0.057853    aiou_median:              0.6940
dtw_xh_p90:      0.236331    chamfer_cand_ref_median:  0.0380
dtw_xh_worst:    unter 0.4503 chamfer_ref_cand_median: 0.0400
marks_missing:   1  marks_spurious: 1
cross_missing:   15  cross_spurious: 7
retrace_missing: 7   retrace_spurious: 13
retrace_arc_ratio_median: 0.641
touch 13 Hand / 24 Kette · overlap 0 Hand / 8 Kette
lift_delta_total: +7  dtw_reversed_better: 0  max_absorption_max: 93
```

Je Wort (dtw · cross matched/ref+spurious · Auffälligkeit):
unter **0,4503** · 1/3 · der bekannte Stapel-Kollaps, unverändert —
muß **0,2421** / muß-2 **0,2082** / muß-3 **0,2337** · je 1/1 ·
die ß-Retrace-Zone fehlt in ALLEN drei Vorkommen (0/1 gematcht,
r 0,18–0,24): der Defekt ist reproduzierbar klassenhaft, kein
Einzel-Beleg — **Galoppieren 0,2349** · **3/8** (5 verlorene
Kreuzungen, die schwerste Struktur-Zahl des Satzes) · dazu die
fehlende i-Marke (0/1), lift +1, r 1,84 — das 22,7-s-Solve ist auch
der Laufzeit-Ausreißer — das 0,0579 · 3/3**+2** · zwei erfundene
Kreuzungen — die 0,0745/die-2 0,0746 · je +1/+2 erfundene —
laden 0,0746 · 1/3+2 — zwei 0,0761 · 1/3 — will 0,0451 · 1/3 —
mit 0,0426/mit-2 0,0376 · 1/2 bzw. 1/1 — Wer 0,0432 · 3/3 —
und-Familie 0,0280–0,0491 · 1/1 · sauber.

Lesart: Der Median sinkt leicht (0,0620 → 0,0579), weil die
Wiederholungs-Vorkommen mehrheitlich leichte Wörter sind — die
KLAGE wächst trotzdem: die muß-Klasse trägt jetzt dreifach, und
Galoppieren bringt eine neue Fehlerklasse (Versal-Kette + lange
Wortspanne) mit 5 verlorenen Kreuzungen und einem
Berührungs-/Überlagerungs-Aufwuchs (touch 24 vs. 13, overlap 8
vs. 0), den die 10er-Baseline so nicht zeigte.

**Der Lotse auf dem 19er-Satz** (adoptierter Stand: Auslauf 1,0 +
Ritt-Doppelzonen-Kartenfahrt; 19/19 ok, 83 s): dtw-Median
**0,0850** · p90 0,1273 · worst muß-2 0,1466 · aiou **0,7631**
(klar über der Kette 0,6940) · `marks_missing` 0 ·
`cross_missing` **31** (+4 unecht) · `retrace_spurious` 22 ·
touch 41 (Hand 13). Gepaart gegen die Kette: Δ-Median +0,0099,
Sign-Test 10:9 — zahlenmäßig unentschieden, aber die Einsätze
bleiben asymmetrisch, jetzt mit VIER großen Lotse-Siegen statt
drei: **unter −0,387 · muß −0,129 · muß-3 −0,121 · Galoppieren
−0,112 · muß-2 −0,062 · die-2 −0,044**, dagegen 10 kleine bis
mittlere Niederlagen (max. will +0,081). Die muß-Klasse gewinnt
der Lotse GESCHLOSSEN (alle drei Vorkommen ~0,11–0,15 gegen
0,21–0,24) — der Komplementaritäts-Befund der 10er-Runde
generalisiert auf die neuen Belege, statt zu verschwinden.
Diagnose-Spalten: `direction_uncertain` 3 = exakt die drei
muß-Vorkommen (je 1 von 2 geprüften Strichen — der ß-Bereich;
Autopsie-Kandidat, kein Gate-Bruch); `will` trägt r = 14,9
(pathologischer Deckungs-Doppelritt), laden 6,4 · Galoppieren 6,3
· die 4,5. **Die Kreuzungs-Verlustkarte ist vollständig:** JEDES
Wort verliert (31 von 46 Hand-Kreuzungen fehlen), Galoppieren
alle 8, zwei/Wer/will/unter je 3/3 bzw. 0 gematcht — und auch die
join-gebildete die-Kreuzung (soll_letters 0) fällt dem
Schienen-Kollaps zum Opfer. Der offene Block der Route (v0.3-Fund:
lange geteilte Schienen, Schleifen-Kollaps der Skelettierung) ist
damit auf dem größeren Satz DER dominante Verlustmechanismus.

**Die Nullprobe auf dem 19er-Satz** (routeg, 19/19 ok): dtw-Median
0,6189 — alle 19 Wörter schlechter als die Kette (Sign-Test 19:0),
rel. Median **+1092 %**; aiou 0,8290 (wie immer die beste
Tinten-Deckung — Skelett-Mitte), `cross_missing` 27,
`lift_delta` +167. Galoppieren ohne Prior: **1,906**. Der Wert
des Duktus-Priors, auf 19 Wörtern neu beziffert: Faktor ~11 im
Median, am langen Versal-Wort Faktor 8 gegen die Kette bzw. 15
gegen den Lotsen.

**Das Orakel der Fusion, neu beziffert** (je Wort das bessere aus
Kette/Lotse — Decke, kein Ergebnis): Median **0,0491** · p90
0,115 · schlechtestes Wort muß-2 0,1466 (statt 0,450 Kette bzw.
0,147 Lotse). Die Decke liegt weiter unter beiden Einzelrouten;
der referenzfreie Auswähler bleibt die offene Frage (die
`aug16`-Diagnostik gilt: kein Signal trennt auf Dev-n, keine
Regel wird auf dem Dev-Satz adoptiert).

**InkSight T0 auf dem 19er-Satz** (derender-Prompt, CPU 4 Kerne,
median 429 s/Wort — deutlich über den 2–6 min der 8-Kern-Messung;
`to_candidate` unverändert): **14/19 gescort, 5 failed** am
Ein-Punkt-Strich-Kontraktbruch — und zwar die GESAMTE und-Familie
(und, und-3, und-4) plus muß-2 und die-2; die T0-Klasse, die auf
dem 10er-Satz `Wer` traf, wandert mit den Crops (Wer scort
diesmal 0,1033). dtw-Median 0,0951 (10er-Satz: 0,0956 —
konsistent) · p90 0,297 · worst unter 0,390 · aiou 0,6955 ·
`retrace_missing` 18 (r ≈ 0 fast überall) · **lift_delta +47** —
die bekannte Signatur: das Modell setzt ab, statt zurückzufahren.
Kreuzungen weiter vergleichsweise sauber (15 fehlend/2 unecht auf
14 Wörtern). Stärken bleiben komplementär: die muß-Klasse schlägt
die Kette klar (muß 0,081 · muß-3 0,097 gegen 0,242/0,234), die
0,039. **Der B2-Prüffall ist bestätigt, deutlicher als erwartet:
Galoppieren (Crop-Ratio 4,34 > Trainingsfiltergrenze 4,0) kollabiert
flächig** — aiou **0,347** (jedes andere Wort ≥ 0,59), beide
Chamfer ~0,11 (3× Satz-Median), +13 Lifts, cross 2/8, Marken
0/1+1: die Langseiten-Skalierung verschenkt die halbe
y-Token-Auflösung, das Wortbild zersplittert. Die
§7.4-B2-Maßnahme (Tiling auf w/h ≤ 2) hat damit ihren gemessenen
Probestein; Priorität unverändert Welle 2. Diagnose-Spalte:
`direction_uncertain` 3 = wieder exakt die muß-Klasse (wie beim
Lotsen — ein Hinweis auf die ß-Strich-Zerlegung dieser Referenzen,
Autopsie-Kandidat der L2-Restliste). Damit sind ALLE stehenden
Routen auf dem 19er-Dev-Satz vermessen; der Eintrag ist
vollständig.

### Route „Lotse" v0.7 `aug17` — Vorregistrierung: die Zonen-Ausweitung der Kartenfahrt (L1)

Geschrieben und committet VOR der ersten Zahl. Die Autopsie der
Re-Baseline (tintenfolger.md §7.10, Befund 3) lokalisiert die 31
fehlenden Kreuzungen im **Junction-Pinch**: der Viterbi routet
beide Pässe eines Schleifenschlusses über dieselben 1–3
Korridor-Pixel; die adoptierte v0.5-Kartenfahrt triggert dort
korrekt, aber nur auf 1–2 Samples — ein einzelnes
karten-gerittenes Sample macht aus den zwei tangentialen
Y-Zusammenläufen kein transversales X (Instrumentierung `will`:
4 von 173 Samples map-priorisiert, je 1 pro l-Schleifenschluss;
Fenster-Bilder will/die/muß). Neuer MECHANISMUS im Sinne der
§7.9-Leitplanke: nicht der Trigger wird weicher, seine WIRKUNG
wird räumlich ausgeweitet.

**EIN Knopf: `RIDE_DOUBLE_ZONE_MARGIN_UNITS`** — jedes
v0.5-getriggerte Sample weitet die Karten-Vorfahrt auf seine
Nachbar-Samples innerhalb dieses Bogenabstands (in xh, entlang
der Sample-Kette desselben Strichs) aus; der spätere Pass fährt
damit die KARTE durch den ganzen Pinch statt durch 1–2 Punkte,
und das X entsteht mit dem Kreuzungswinkel der komponierten
Karte. Einfachpässe, Brücken und alles außerhalb der geweiteten
Zonen bleiben unberührt; der erste Pass bleibt auf der
Tinten-Mitte. Leiter 0,0 (= aus, heutiges Verhalten) / 0,35 /
0,7.

**Erwartung (benannt, damit ein Negativ lesbar ist):** die
Junction-Pinch-Klasse der 31 fehlenden Kreuzungen kehrt
substanziell zurück — konkret erwartete Rückkehrer: die zwei
l-Schleifen in `will` (4,22/5,28), die d-Schleifen in
die/die-2/das/laden, die z/w-Schlüsse in `zwei`, Anteile der 8
Galoppieren-Kreuzungen und die ß-Stamm-Kreuzung der muß-Klasse
(dann entfällt L2 teilweise); `retrace_spurious` (22) und
`touch_cand` (41) fallen Richtung Hand-Niveau; dtw auf den
Struktur-Wörtern fällt oder hält. `aiou` gibt nur INNERHALB der
geweiteten Zonen nach.

**Gates und Kills (wie v0.1/v0.5):** Kette-Vergleich gepaart
gegen die `aug17`-Baseline; Co-Primär-Gates Marken und
`cross_missing+spurious` ohne Netto-Anstieg gegenüber dem
v0.5-Lotse-Stand (31+4); **Zusatz-Kill `aiou`-Median-Δ < −0,02
gegenüber dem v0.5-Stand (0,7631) = verworfen**; erzeugt die
Karten-Geometrie in den Zonen netto > +2 unechte Kreuzungen über
das Soll, ist die Karten-Platzierung dort zu schlecht —
verworfen, zurück zur Sub-Strich-Trennung (§7.9). Beide
Leiter-Stufen werden gemessen, adoptiert wird höchstens EINE
(die bessere, sofern sie alle Gates besteht).

**Gemessen `aug17` — 0,35 ADOPTIERT (alle Gates bestanden), 0,7
vom aiou-Kill verworfen; die Erwartung traf nur TEILWEISE — der
Fund präzisiert die Schleifen-Klasse endgültig.** Leiter (dev-19,
je 19/19 ok): 0,35 → dtw 0,0858 (v0.5: 0,0850, +0,0008) · aiou
0,7493 (−0,0138, hält) · **cross_missing 31 → 27, Netto-Defekte
35 → 32** · retrace 5+22 → 4+21 · **`retrace_arc_ratio`-Gap
0,285 → 0,044** (Median 0,956 — praktisch Hand-Niveau) · touch
41 → 38, overlap 2 → 1 · p90 +1,1 %. 0,7 → aiou 0,7404
(−0,0227) → Zusatz-Kill. Struktur vor Distanz, alle Wächter im
Rahmen → `RIDE_DOUBLE_ZONE_MARGIN_UNITS` = 0,35. ABER: die
Rückkehrer (Wer +2, Galoppieren +1, die-2 +1) sind die
PUNKT-Pinch-Unterklasse — die erwarteten Schleifen-Rückkehrer
(will 2× l, zwei, die, unter, muß-Stamm) blieben ALLE bei 0.
Autopsie-Bild (will, v0.5 vs. m035): der Aufwärts-Pass BOARDET
die verschmolzene Schiene genau auf Kreuzungshöhe — unterhalb
des Schleifenschlusses existiert gar keine Pixel-Wiederbelegung,
die ein Occupancy-Trigger sehen könnte; der Selbstschnitt der
Karte wird beim Aufsteigen durch einen tangentialen Board-Hop
ERSETZT. Ein Occupancy-Mechanismus kann diese Klasse
prinzipiell nicht erreichen — der Rettungsweg ist ein ANDERER
Trigger (unten), keine weichere Schwelle.

### Route „Lotse" v0.8 `aug17` — Vorregistrierung: Karten-Vorfahrt an Karten-Selbstschnitten (L1b)

Geschrieben und committet VOR der ersten Zahl. Der v0.7-Fund:
die Schleifen-Klasse der fehlenden Kreuzungen (will/zwei/die/
unter/muß u. a., der Großteil der verbleibenden 27) entsteht
NICHT durch Doppel-Belegung, sondern durch den Board-Hop — der
Ritt ersetzt den Selbstschnitt der Karte durch ein tangentiales
Aufsteigen auf die verschmolzene Schiene. Die KARTE hat die
Kreuzung (das Soll ist duktus-deterministisch, ihre
Selbstschnitte sind berechenbar); der neue TRIGGER ist darum der
**Karten-Selbstschnitt selbst**: Um jeden Selbstschnittpunkt der
komponierten Karten-Striche bekommen die Karten-Samples BEIDER
beteiligter Pässe innerhalb eines Bogenfensters im Viterbi
ausschließlich den Brücken-Zustand (die v0.4-Geometrie, mit dem
richtigen Auslöser) — beide Züge fahren die Karte durch die
Kreuzung, das X ist das X der Karte, mit ihrem Winkel; außerhalb
der Fenster ändert sich nichts, v0.5 + v0.7 bleiben aktiv.

**EIN Knopf: `MAP_CROSSING_WINDOW_UNITS`** (0,0 = aus). Leiter
0,35 / 0,6. Erwartung: die Schleifen-Klasse kehrt zurück —
konkret will (2× l-Schleife), zwei, die/die-2, unter (bis 3),
die muß-Stamm-Kreuzung (×3) und weitere Galoppieren-Anteile;
`cross_missing` fällt klar unter 27, Ziel-Richtung ≤ 15 (das
Ketten-Niveau). Benanntes Risiko: an Soll-Kreuzungen, die DIESE
Hand nicht schreibt (linken 4 vs 3, mit-2 2 vs 1), zeichnet das
Fenster ein X, das die Hand nicht hat → +spurious dort ist
erwartbar und im Gate enthalten. **Gates:** Marken und
`cross_missing+spurious` ohne Netto-Anstieg gegenüber dem
v0.7-Stand (27+5 = 32); aiou-Median-Δ < −0,02 gegenüber 0,7493 =
verworfen; p90-Wächter ≤ +10 % gegen die Kette wie gehabt;
`dtw_reversed_better` = 0. Kill: bleibt die Schleifen-Klasse
auch mit erzwungener Karten-Fahrt aus (die Karte selbst liegt
dann zu weit von der Tinte), ist der ehrliche Rest die
Sub-Strich-Trennung aus Breiten-Evidenz (§7.9) — und die
Karten-PLATZIERUNG wird als eigener Befund an die
Kompositions-Schiene zurückgegeben.

**Gemessen `aug17` — BEIDE Stufen vom aiou-Kill verworfen; die
Topologie-Hypothese ist zugleich SO STARK bestätigt wie kein
Arm zuvor.** Leiter (dev-19, je 19/19 ok): w0,35 →
**cross_missing 27 → 2, spurious 5 → 2** (Netto-Defekte 32 → 4),
`retrace_spurious` 21 → 3, touch 38 → 20, **dtw-Median 0,0858 →
0,0576** — erstmals unter der Kette (0,0579; gepaart Δ-Median
−0,0075, Sign 11:8), p90 0,1187 gegen Kette 0,2363 — aber aiou
0,7493 → 0,7264 (Δ −0,0229 < −0,02) und Recall-Chamfer 0,0492 →
0,0522: **Kill feuert um 0,003.** w0,6 → gleiche Strukturzahlen
(2+2), aiou 0,6744 (−0,075) → tiefer Kill. Der Sichtbeweis
(will/muß-Fenster): alle drei will-Kreuzungen und die
ß-Stamm-Kreuzung kehren zurück — die Schleifen-Klasse ist
GENAU die vorregistrierte. Diagnose des Kills: die Fenster
fahren die ROHE Karte, und deren lokaler Versatz zur Tinte
(bis ~0,5 xh — die bekannte Platzierungs-Toleranz der
Komposition) verlässt den Tintenkörper; der Wächter tut exakt
seinen Dienst — „Geometrie aus der Tinte" ist in den Fenstern
verletzt. Rettungsweg (benannt, eigene Pre-Reg unten): die
Fenster ans Ink PINNEN — Topologie und Winkel von der Karte,
die Lage von den Board-Punkten der Tinte. §7.9-Zeile im selben
PR.

### Route „Lotse" v0.9 `aug17` — Vorregistrierung: gepinnte Selbstschnitt-Fenster (L1c)

Geschrieben und committet VOR der ersten Zahl. Der v0.8-Befund:
die Selbstschnitt-Fenster liefern die Struktur vollständig
(Netto-Defekte 32 → 4), bezahlen aber mit der ROHEN
Karten-Geometrie — deren lokaler Versatz kostet Tinten-Deckung
(aiou-Kill). v0.9 behält Trigger und Fenster UNVERÄNDERT und
ändert allein die GEOMETRIE der Fenster-Strecke: jeder maximale
Fenster-Lauf wird als Ganzes so verschoben, dass seine Enden auf
den benachbarten BOARD-Punkten der Tinte liegen (linear
interpolierter Versatz zwischen beiden End-Offsets; Läufe an
Strich-Enden nehmen den einen verfügbaren Offset konstant; reine
Karten-Striche bleiben roh). Damit stammen Topologie und
Kreuzungswinkel weiter von der Karte, die LAGE aber von der
Tinte — „Geometrie aus der Tinte, Ordnung aus dem Prior", auf
das Fenster selbst angewandt. Natürliche Brücken (fehlende
Tinte) bleiben unangetastet; die adoptierten v0.5/v0.7-Zonen
ebenso.

**EIN Knopf: dieselbe `MAP_CROSSING_WINDOW_UNITS`-Leiter 0,35 /
0,6, jetzt mit Pinning (`MAP_CROSSING_PIN` fest an, kein eigener
Suchknopf).** Erwartung: Strukturzahlen ~wie v0.8 (2+2 bleibt),
aiou kehrt Richtung v0.7-Niveau zurück (der Versatz war die
einzige benannte Kostenquelle), dtw hält oder fällt weiter.
**Gates unverändert wie v0.8** (Netto-Defekte ≤ 32, aiou-Δ ≥
−0,02 gegen 0,7493, p90 ≤ +10 % gegen Kette, Marken, reversed
= 0). Kill: bleibt aiou auch gepinnt unter der Schranke, liegt
der Versatz nicht in der Karten-LAGE, sondern die Karte ist im
Fenster FORMfremd — dann ist die ehrliche Grenze erreicht und
der Rest gehört der Sub-Strich-Trennung (§7.9).

**Gemessen `aug17` — 0,35 ADOPTIERT (alle Gates bestanden), 0,6
vom aiou-Kill verworfen (−0,039). Die stärkste Zahl der
Kampagne.** Leiter (dev-19, je 19/19 ok): w0,35 gepinnt → dtw
**0,0578** (Ketten-Niveau 0,0579; gepaart gegen die Kette
**Δ-Median −0,0183 = −24 %** — erstmals erfüllt eine Route das
Primär-Kriterium „≥ 20 % Fall") · p90 **0,1179** (Kette 0,2363)
· worst muß-2 0,1473 · `cross_missing` 3, `spurious` 4
(Netto-Defekte 32 → **7**) · `marks_missing` 0 (die Kette
verliert 1 — der Lotse findet Galoppierens i-Punkt per Karte) ·
retrace 5+4 · touch 20 · aiou 0,7351 (Δ −0,0142, hält) ·
reversed 0. Die Wort-Tabelle dreht das Komplementaritäts-Bild:
der Lotse gewinnt jetzt JEDES strukturschwere Wort (unter
−0,376 · Galoppieren −0,147 · muß −0,126 · muß-3 −0,109 ·
muß-2 −0,061 · die-2 −0,041 · die −0,035 · das −0,024 · zwei
−0,018 · laden −0,018) und verliert die glatten nur noch
mikroskopisch (will +0,006 statt +0,081 — die gepinnten
Fenster reparierten auch die Schleifen-GEOMETRIE; Maximum
linken +0,019). Sign-Test 10:9 (beschreibend). w0,6 →
cross_missing 1, aber aiou 0,7106 (−0,0387) → Kill.
`MAP_CROSSING_WINDOW_UNITS` = 0,35, `MAP_CROSSING_PIN` = True.

**Die verbleibenden 7 Defekte sind kartiert und fast
vollständig SOLL-Differenzen, keine Ritt-Fehler:** Galoppieren
2/8 fehlend = exakt die p-Unterlängen-Kreuzungen, die schon der
KOMPOSITION fehlen (kein Fenster ohne Karten-Kreuzung — der
G1-Autorenschritt aus §7.10 ist jetzt der limitierende Faktor
dieses Worts); linken +3 und mit-2 +1 unecht = exakt die
vorbenannten Soll-Kreuzungen, die DIESE Hand nicht schreibt
(Beleg-Varianz, im v0.8-Risiko benannt); unter 1/3 fehlend als
letzter echter Ritt-Rest. Routen-Stand nach der Runde: **der
Lotse steht auf dem 19er-Dev-Satz erstmals GLEICHAUF mit der
Kette im Median, halbiert ihren p90, schlägt sie gepaart um
24 % und trägt die sauberere Struktur** — die
Bestätigungssätze (A, dann B) bleiben der Schlussstein, bevor
daraus eine Adoptionsentscheidung jenseits der
Routen-Konstanten wird.

### Route „Lotse" v0.10 `aug19` — Vorregistrierung: Knoten-Anker-Pinnung der Karten-Läufe (L1d)

Geschrieben und committet VOR der ersten Zahl. Anlass: der
Owner-Sichtbefund an der Duell-Ansicht (2026-08-19) — „beim k wird
der untere Kringel nicht nachgefahren", das W in `Wer` „macht
Quatsch", der r/e-Auslauf in `Galoppieren` fährt eckige Luft-Züge.
Die Kategorien-Autopsie (Instrumentierung: jedes Sample nach
Mechanismus eingefärbt — Schiene · Brücke · Doppelzonen-Ride ·
Fenster) lokalisiert die Exkursionen vollständig in der
KARTEN-Geometrie, in zwei Klassen:

1. **Verschmolzene Fenster-Läufe.** `map_crossing_masks` legt um
   JEDEN Karten-Selbstschnitt ±0,35 xh; wo Selbstschnitte dicht
   stehen, ketten die Fenster zu EINEM Lauf (linken: 4,32 xh am
   k-Komplex aus Kopfschleife + Kringel + Stamm — 71 von 253
   Samples; mit: 2,76 xh am t-Rückpass; Galoppieren: 3,72 und
   2,64 xh; ein Einzel-Fenster wäre 0,96 xh). Die v0.9-Pinnung
   interpoliert NUR zwischen den Lauf-ENDEN — über solche Läufe
   reicht sie die rohe (bis ~0,5 xh versetzte) Karten-Form im
   Innern durch: exakt die „Quatsch"-Züge des Sichtbefunds.
2. **Rohe Doppelzonen-Rides und Brücken.** Die adoptierten
   v0.5/v0.7-Zonen-Rides und die natürlichen Brücken zeichnen die
   Karte weiterhin UNGEPINNT (Wer: 13, Galoppieren: 32
   Zone-Samples) — dieselbe Fehlerklasse, die v0.9 für die
   Fenster bereits behoben hat.

**Anker-Evidenz (vor der Maßnahme gemessen):** jeder
Karten-Selbstschnitt der vier Verlierer-Wörter hat einen
Skelett-VERZWEIGUNGSKNOTEN in ≤ 0,6 xh (Median 0,06–0,19; mit
6/6, linken 16/16, Wer 10/10, Galoppieren 32/32 innerhalb 1,0 xh)
— die Tinte benennt den Ort der Kreuzung selbst, das Fenster muss
ihn nur ansteuern.

**EIN Mechanismus: die verallgemeinerte Pinnung.** Jeder
Karten-Lauf wird über eine Offset-Polylinie mit KNOTEN gepinnt:
die Lauf-Grenzen (benachbarte Board-Punkte — die v0.9-Mathematik,
unverändert) PLUS je Karten-Selbstschnitt im Lauf ein ANKER
(Offset = nächster Verzweigungsknoten − Selbstschnittpunkt,
Suchradius `PIN_KNOT_NODE_RADIUS_UNITS` = 1,0 xh fest, kein
Suchknopf; ohne Knoten in Reichweite entfällt der Anker). Linear
zwischen benachbarten Knoten, konstant jenseits der äußersten;
ein Lauf ganz ohne Knoten bleibt roh (wie v0.9s „Strich ganz aus
Karte"). Beide Pässe eines Selbstschnitts erhalten denselben
Anker — das X der Karte landet konstruktiv auf dem Knoten der
Tinte (die §13a-Extrapolations-Idee als Konstruktion, dieselbe
Verwandtschaft wie beim v0.3-Arm, jetzt ohne dessen
Flächen-Kosten, weil nur KARTEN-Läufe bewegt werden, nie
Schienen-Ritte).

**Leiter (`MAP_RUN_PIN_KNOTS`): "off" (= v0.9) / "windows" (nur
Fenster-Läufe bekommen Knoten-Pinnung) / "all" ("windows" +
dieselbe Knoten-Pinnung für Doppelzonen-Rides und natürliche
Brücken).** Beide Stufen werden gemessen, adoptiert wird
höchstens EINE. Erwartung: linken/mit/mit-2/Wer/Galoppieren
fallen in dtw (die fünf tragen die größten Ketten-Vorsprünge des
v0.9-Stands), `aiou` steigt (weniger Luft), Kreuzungs-ZAHLEN
unverändert (Topologie bleibt die der Karte), Kreuzungs-Ortsfehler
fällt; keine neue Struktur.

**Umgebungs-Deklaration.** Diese Runde läuft lokal (WSL2, BLAS
gepinnt); die aug17-Zahlen stammen aus der Cloud-Session. Neu
gemessene lokale Basis: Kette dtw 0,0576 med (aug17: 0,0579 —
Solver-Umgebungsvarianz, dokumentierte Klasse), Lotse v0.9
0,0578 · aiou 0,7351 · cross 3+4 · marks 0+1 (deterministisch,
BYTE-gleich mit aug17). Alle gepaarten Vergleiche dieser Runde
laufen gegen die LOKALE Kette.

**Gates (wie v0.9):** Marken und `cross_missing+spurious` ohne
Netto-Anstieg gegenüber dem v0.9-Stand (3+4 = 7);
`aiou`-Median-Δ ≥ −0,02 gegen 0,7351; p90 ≤ +10 % gegen die
Kette; `dtw_reversed_better` = 0. Zusatz-Kill: `cross_spurious`
netto > +2 → die Anker greifen den falschen Knoten (das benannte
Risiko der dichten Regionen — Galoppieren p90-Ankerabstand
0,51 xh) → verworfen, Rettungsweg wäre ein kleinerer Suchradius
NUR mit frischer Vorregistrierung.

**Gemessen `aug19` — BEIDE Stufen vom Kreuzungs-Gate verworfen;
der Fund benennt den Degenerierungs-Mechanismus präzise und die
Gewinnseite ist die stärkste Tinten-Deckung der Route.** Leiter
(dev-19, je 19/19 ok): "windows" → Netto-Kreuzungsdefekte 6+3 =
9 (> 7) · aiou 0,7616 (+0,027!) · dtw gepaart gegen Kette
−0,0097 (schlechter als v0.9s −0,0182); "all" → Defekte 5+5 =
10 (> 7) · aiou 0,7616 · gepaart gegen v0.9: 14 von 19 Wörtern
besser (Δ-Median −0,0037, Sign 14:5, p=0,064), beide
Chamfer-Hälften besser, `retrace_arc_ratio`-Gap −0,047,
**Kreuzungs-Ortsfehler-Median 0,116 → 0,083 xh** und die
SPURIOUS-Klasse heilt (linken 3 → 1, mit-2 1 → 0 — wo die Hand
das Soll-X nicht schreibt, hat die Tinte keinen Knoten, und der
Anker degeneriert das Karten-X von selbst: der Mechanismus
arbeitet in beide Richtungen). Der Sichtbefund bestätigt: der
k-Kringel in `linken` wird erstmals nachgefahren, der
V-Spike unter die Grundlinie ist weg. ABER die Anker KOSTEN
Kreuzungen genau dort, wo sie dicht stehen: `mit` verliert eins
der zwei nur 0,07 xh getrennten t-X (auf einen Punkt gezogen →
Detektor-Merge), `zwei` beide z-Unterschleifen-X (0,25 xh
Abstand, gemittelte Offsets → Berührung statt Durchstoß),
`will` das zweite l-X (Punktlandung beider Pässe auf dem Knoten
→ oskulierend statt piercend), und `Galoppieren` fabriziert 4
unechte an Interpolations-Knicken des dichten „ieren"-Clusters.
Diagnose in einem Satz: **das Offset-Feld der Punkt-Knoten
variiert nahe der Kreuzung zu schnell — Scherung und Mittelung
zerstören genau die Transversalität, die der Anker herstellen
soll.** VERWORFEN (beide Stufen), `MAP_RUN_PIN_KNOTS` bleibt
"off". Rettungsweg (benannt, eigene Pre-Reg unten): das
Offset-Feld um jeden Anker lokal KONSTANT machen — reine
Translation erhält jedes X exakt (v0.11); §7.9-Zeile im selben
PR.

### Route „Lotse" v0.11 `aug19` — Vorregistrierung: Plateau-Anker (stückweise-starre Fenster, L1e)

Geschrieben und committet VOR der ersten Zahl. Der v0.10-Fund:
Anker-Offsets als PUNKT-Knoten scheren das Offset-Feld an genau
den Stellen, deren Transversalität sie sichern sollen — eine
Kreuzung überlebt eine lokal REINE TRANSLATION dagegen exakt
(beide Pässe verschieben sich gleich, das X wandert starr mit).
Der neue MECHANISMUS: jedes Anker-Offset wirkt als **Plateau**
konstanter Breite statt als Punkt — `PIN_KNOT_PLATEAU_UNITS` =
0,35 xh beidseitig (= der Fensterradius, deklariert fest, kein
Suchknopf); überlappende Plateaus VERSCHMELZEN zu einem
Intervall mit dem Mittel ihrer Anker-Offsets (der dichte
Cluster wird als Ganzes starr verschoben — beide X bleiben
erhalten, jedes landet ≤ halber Clusterbreite neben seinem
Knoten, weit innerhalb des 0,55-xh-Matchers); zwischen Plateaus
und zu den Lauf-Grenzen wird weiter linear interpoliert — die
Scherung wandert in die kreuzungsfreien Zwischenstrecken.
Mittelung je EINZEL-Index entfällt (sie war die zweite
Degenerierungsquelle).

**Leiter: dieselben zwei Stufen wie v0.10 ("windows" / "all"),
jetzt mit Plateau-Feld.** Gates unverändert (Netto-Defekte ≤ 7,
aiou-Δ ≥ −0,02 gegen 0,7351, p90 ≤ +10 % gegen Kette, Marken,
reversed = 0, `cross_spurious` netto ≤ +2). Erwartung: die
v0.10-Gewinne bleiben (aiou ~0,76, Ortsfehler ~0,083,
Spurious-Heilung, k-Kringel), die vier Verlust-Stellen
(mit-t-Doppel, zwei-z-Doppel, will-l2, Galoppieren-Knicke)
kehren auf den v0.9-Stand zurück. Kill: verliert auch das
Plateau-Feld Kreuzungen in den dichten Clustern, ist die
Anker-Idee an der Dichte-Grenze ehrlich gescheitert und der
Rest gehört der Karten-FORM (Kompositions-Schiene: der
k-Kopfschleifen-Bogen bleibt auch gepinnt formfremd —
eigener Befund unten).

**Gemessen `aug19` — "windows" ADOPTIERT (alle Gates bestanden),
"all" um genau ein Doppel-X verworfen; eine
Semantik-Korrektur unterwegs, beide Messungen berichtet.** Die
Erstmessung implementierte die Verschmelzung LAUF-lokal — kreuzende
Pässe konnten so verschiedene Plateau-Mittel bekommen, und `mit`/
`zwei` verloren weiter je ein echtes X: die deklarierte Semantik
(„der dichte Cluster wird als Ganzes starr verschoben") verlangt
die GLOBALE Fusion über alle beteiligten Pässe (Union-Find über
die Anker-Identitäten). Mit der deklarierten Semantik (dev-19,
je 19/19 ok):

- **"windows": Netto-Kreuzungsdefekte 1+6 = 7 (= v0.9-Stand,
  Gate hält), `cross_missing` 3 → 1** — mit/zwei/will vollständig
  zurück, und **Galoppierens zwei Kompositions-fehlende
  p-Unterlängen-X kehren als einzige ECHTE Struktur-Neuheit der
  Route zurück** (das Plateau-Feld öffnet den Karten-Retrace zur
  Schleife, wie die Tafel sie schreibt — der G1-Autorenschritt
  verliert seinen Rang als limitierender Faktor); Rest-Missing
  ist allein unters letzter Ritt-Rest. Kreuzungs-Ortsfehler-Median
  **0,116 → 0,066 xh (−43 %)** · aiou 0,7434 (+0,0083) · p90
  0,1179 → **0,1129** · marks 0+1 unverändert · rev 0 · gepaart
  gegen v0.9: Δ-Median −0,0018, Sign 13:6. Kosten, ehrlich:
  eigener dtw-Median 0,0578 → 0,0596, gepaart gegen die Kette
  −0,0137 = **−18,0 %** (v0.9: −24 %) — der Präzedenzfall ist
  v0.7 („Struktur vor Distanz"); `retrace_missing` 5 → 6; und die
  Spurious-Klasse wechselt ihren Charakter: 6 statt 4, davon
  linken 3 → 1 GEHEILT, aber 4 der 6 sind **Doppel-X-Duplikate**
  (dieselbe Kreuzung zweimal gezeichnet, weil die gepinnten
  Pässe durch den Knoten doppelt wackeln: Galoppieren 2, mit-2 1,
  will 1) plus ein echtes Erfundenes (Galoppieren u≈13,4).
  `MAP_RUN_PIN_KNOTS` = "windows".
- **"all"**: identische Heilung, aiou sogar 0,7521, aber
  Galoppieren trägt ein viertes Spurious → Netto 8 > 7,
  VERWORFEN um genau dieses eine Doppel-X. Die Zonen-Rides und
  Brücken (der Rest-Kasten in Galoppieren x≈360, die
  Wer-Diagonale) bleiben damit roh — ihr Pinning ist hinter der
  Doppel-X-Frage eingereiht, nicht verworfen.

Sichtbefund zum Owner-Anlass: **der k-Kringel in `linken` wird
nachgefahren**, der V-Spike ist weg; verbleibend fährt die
k-KOPFSCHLEIFE als flacher Bogen durchs Schleifen-Innere — die
KARTE selbst ist dort formfremd (der komponierte k-Bogen liegt
tiefer/schmaler als diese Hand schreibt): ein
Kompositions-/Laufform-Befund, kein Ritt-Fehler, notiert für die
Kompositions-Schiene. Offene Blöcke nach der Runde:
(i) die Doppel-X-Duplikate — der benannte nächste Mechanismus
ist EIN X je Knoten-Cluster (Begradigung der Fenster-Teilbahn je
Pass durch den Knoten), er würde zugleich die "all"-Stufe
freischalten; (ii) die Karten-Form-Klasse (k-Kopfschleife,
W-Ansatz = K3, Autorenschritt). §7.9-Zeilen im selben PR.

### Route „Lotse" v0.12 `aug19` — Vorregistrierung: die Plateau-Sehne (Doppel-X-Begradigung, L1f)

Geschrieben und committet VOR der ersten Zahl. Der v0.11-Rest:
4 der 6 Spurious sind Doppel-X-Duplikate — die gepinnte
Fenster-Teilbahn eines Passes WACKELT durch die
Knoten-Nachbarschaft und schneidet den anderen Pass zweimal
(Kreuzungs-Orte 0,06–0,11 xh auseinander), dazu ein an einem
Interpolations-Knick erfundenes X (Galoppieren u≈13,4). Der neue
MECHANISMUS: **innerhalb jedes (verschmolzenen) Plateau-Intervalls
wird die Teilbahn jedes Passes durch ihre SEHNE ersetzt**
(Interior-Samples linear zwischen den beiden Intervall-Rändern des
eigenen Passes) — zwei Sehnen schneiden sich höchstens EINMAL, das
Doppel-X ist konstruktiv unmöglich. Verwandt mit dem verworfenen
v0.3 (Knoten-Sehne), aber ohne dessen Flächen-Kosten: v0.3
begradigte SCHIENEN-Ritte überall (aiou-Kill −0,045); die
Plateau-Sehne begradigt nur KARTEN-Geometrie, die bereits im
starren Plateau liegt — die Abweichung ist durch die Plateau-Breite
(±0,35 xh) gedeckelt, und Schienen-Ritte bleiben unberührt.

**Leiter: "windows"+Sehne / "all"+Sehne** (EIN Knopf
`PIN_PLATEAU_CHORD` aus/an; die "all"-Wiedervorlage ist der in
§7.9 benannte Rettungsweg — die Zonen-Rides und Brücken werden
erst gepinnt, wenn die Sehne die Doppel-X-Quelle schließt).
**Gates gegen den v0.11-Stand:** Netto-Kreuzungsdefekte ≤ 7 UND
`cross_spurious` ≤ 6 (kein Anstieg); `cross_missing` ≤ 1 (die
geheilte Missing-Klasse darf nicht zurückfallen);
`aiou`-Median-Δ ≥ −0,02 gegen 0,7434; Marken ohne Netto-Anstieg;
p90 ≤ +10 % gegen die Kette; `dtw_reversed_better` = 0.
Erwartung: die 4 Duplikate verschwinden (spurious → ~2), dtw
~neutral, aiou ~neutral (Sehne bleibt im Plateau); bei "all"
zusätzlich der Galoppieren-Rest-Kasten (x≈360) und die
Wer-Diagonale gepinnt, aiou eher steigend. Adoptiert wird
höchstens EINE Stufe (die bessere, sofern alle Gates bestehen).
Kill: kostet die Sehne Missing-Kreuzungen (der Wackel WAR das X)
oder aiou, bleibt v0.11 stehen und die Duplikat-Frage geht als
ehrliches Negativ mit benanntem Rest in §7.9.

**Gemessen `aug19` — BEIDE Stufen verworfen, das benannte Kill
feuert in voller Stärke: der Wackel WAR das X.** Leiter (dev-19,
je 19/19 ok): "windows"+Sehne → `cross_missing` 1 → **8**,
spurious 6 → 1, `retrace_missing` 6 → **12**, dtw auf 16 von 19
Wörtern schlechter (Δ-Median +0,0014, Sign 3:16, p=0,004), aiou
−0,0075; "all"+Sehne → 7 missing / 2 spurious, gleiches Bild. Die
Diagnose ist geometrisch eindeutig: an den Sütterlin-Schleifen-
schlüssen laufen beide Pässe TANGENTIAL durch die Knoten-
Nachbarschaft (die Junction-Pinch-Geometrie) — ihre Sehnen sind
nahe-parallel und schneiden sich GAR NICHT; erst der Wiggle der
Karten-Teilbahn stellt die Transversalität her, und er trägt
Kreuzung UND Duplikat untrennbar. Zugleich zerstören die Sehnen
die Retrace-Zonen im Plateau (12 fehlend). VERWORFEN,
`PIN_PLATEAU_CHORD` bleibt False; v0.11 "windows" bleibt der
adoptierte Stand. Rettungswege (§7.9-Regel, je eigene Pre-Reg):
(i) **Entdrillung statt Begradigung** — Duplikat-PAARE desselben
Pass-Paars (Kreuzungs-Orte < 0,3 xh) topologisch entdrillen, indem
der kleinere Wiggle-Bogen zwischen den beiden Schnittpunkten
EINES Passes gespiegelt wird (entfernt genau ein X, erhält das
andere samt Winkel); (ii) **asymmetrische Sehne** — nur der
SPÄTERE Pass wird begradigt, der frühere behält seine Kurve
(bricht die Parallel-Degenerierung, weil nur eine Seite
linearisiert). Beides bleibt hinter der Feststellung eingereiht,
dass die 4 Duplikate KEINE Topologie-Erfindung sind (das X ist
real, nur doppelt gezählt) — der Leidensdruck ist entsprechend
klein, und die "all"-Wiedervorlage wartet auf den Mechanismus,
der die Duplikate schließt, ohne das X zu kosten.

### L2-Rest-Autopsie `aug19` — die Kollaps-Klasse (unter + muß×3) ist ORDNUNGS-dominiert: der Deckbogen sitzt in der Ketten-Assembly an der falschen Sequenz-Position

Befund, kein Knopf (die in §7.10 L2 und in der `aug17`-Re-Baseline
benannte Rest-Autopsie, ausgeführt und noch am selben Tag um eine
FALSCHE Erst-Attribution korrigiert — beide Fassungen stehen der
Ehrlichkeit halber im Verlauf dieses Branches). Auslöser der
Korrektur: die Owner-Frage „das er von unter ist ja ganz schlecht —
war das schon immer so?" und der Lotse-Widerspruch (0,063 auf
derselben Referenz — ein Referenz-Defekt hätte JEDE Route deckeln
müssen).

**Die Erst-Fassung war doppelt falsch:** (1) das Diagnose-Skript
resampelte NACH der Body-Konkatenation statt je Strich — die
Absetz-Sprünge wurden zu synthetischen Bogen-Zonen (das Lineal
selbst resampelt je Strich, `summary.score_word` →
`resampled_strokes`; die „Rücklauf-Zonen" bis 6,75 xh waren zum
Teil Artefakt); (2) der ü-/u-Deckbogen ist NICHT verbunden
gezeichnet — er ist in allen betroffenen Referenzen ein eigener,
ABGESETZTER Strich (unter: 54 Samples · Bogen 1,10 xh; muß: 59
Samples), liegt damit aber über der 0,8-xh-Marken-Schwelle von
`classify_strokes` und bleibt zu Recht im Body (die bekannte
und-Autopsie-Klasse „Deckbogen über der Marken-Schwelle").

**Der wirkliche Mechanismus — mit Beweis-Messung.** Die
Body-Sequenzen: Hand = [Wort, Deckbogen] (Bogen ZULETZT; dieselbe
Ordnung fährt der Lotse, dessen Karte die komponierte
Engine-Ordnung mit endständigen Marken übernimmt — darum sein
0,063). Der KETTEN-Kandidat assembliert dagegen je RUN
zusammenhängender Slots und emittiert den Deckbogen ZWISCHEN den
Runs: unter = [u..t (12,6 xh) · Bogen (1,0 xh) · e..r (12,8 xh)],
muß-Familie analog [erster Teil · Bogen · Rest]. Das forward-DTW
konkateniert in Schreibreihenfolge (die Ordnung IST die Wahrheit)
und zahlt die Sequenz-Inversion voll — `dtw_max_absorption` 132
(der Singularitäts-Wächter zeigte seit `aug14` exakt hierhin).
Beweis durch die Ordnungs-Permutation (Geometrie byte-identisch,
NUR der Bogen ans Ende sortiert): **unter 0,4503 → 0,0854 ·
muß 0,2419 → 0,1096 · muß-2 0,2084 → 0,0877 · muß-3 0,2339 →
0,0962**; der Permutations-Sweep über ALLE 19 Dev-Wörter findet
außerhalb dieser vier keinen einzigen Ordnungs-Gewinn — die
Klasse ist vollständig und exakt die Kollaps-Klasse der Baseline.
`unter` war seit der ersten Zahl so (aug14: 0,4389 „der bekannte
Kollaps-Probefall"); es war nie primär das sichtbare
er-Gekritzel — das kostet den REST (~0,085, der echte
Berührungs-/Überlagerungs-Stapel bleibt die zweite, kleinere
Baustelle).

**Einordnung.** (a) Die Kollaps-Headline der Kette (59,8 % des
Fehlers, §7.1) ist zu ~2/3 eine ASSEMBLY-Eigenschaft des
Kandidaten, kein Fit- und kein Referenz-Defekt; auch die
gespeicherten `traced`-Produktionszeilen tragen dieselbe
Strichfolge. (b) Benannter Kandidat (eigene Vorregistrierung,
nicht Teil dieses Befunds): **die marken-endständige
Ketten-Assembly** — der Kandidat emittiert abgesetzte
Deckbogen-/Markenstriche NACH allen Runs, in der komponierten
Engine-Ordnung, die Lotse und Hand ohnehin teilen. Erwartung aus
der Permutations-Probe: Kette p90 0,236 → ~0,11, unter −0,36,
muß-Klasse −0,11 bis −0,13; das ist eine Änderung des
EINGEFRORENEN Baseline-Kandidaten und damit eine deklarierte
Re-Baseline (alle gepaarten Routen-Vergleiche verschieben sich —
ehrlich gesagt: der Lotse-Vorsprung auf unter/muß schrumpft
entsprechend, er schlug dort zum Teil ein Assembly-Artefakt).
(c) Die Referenzen sind SAUBER — der Todoist-Entscheid
„muß neu nachfahren" ist gegenstandslos und wird zurückgezogen;
der Brief-Hinweis „Marken mit eigenem Absetzen" bleibt für
KÜNFTIGE Nachfahrungen sinnvoll (kleine Marken unter der
Schwelle profitieren vom Zentroid-Matching). (d) A2 (SDM/DCD)
bleibt für muß/unter zurückgestuft — Stranding/Doppelpass sind
seine Ziele. KEINE Gate- oder Lineal-Änderung aus dieser
Autopsie.

### Kette K-A `aug19` — Vorregistrierung: die marken-endständige Assembly (Owner-Go „weiter optimieren")

Geschrieben und committet VOR der ersten Zahl. Der benannte
Top-Kandidat aus der (korrigierten) L2-Rest-Autopsie:
`assemble_word_strokes` läuft heute JE RUN, und die
Diakritika-Striche eines Runs (der eigene Assembler-Begriff:
alle Samples über `DIACRITIC_MIN_Y` = 1,0) landen dadurch
ZWISCHEN den Runs in der Schreibreihenfolge — Hand und
komponierte Engine-Ordnung schreiben sie am WORTENDE. **EIN
Knopf: `HarvestOptions.marks_last`** (CLI `--marks-last`,
Label `chain+order` — wie `--mark-refit` eine Variante der
Baseline, nie die Baseline selbst): die assemblierten Striche
des Wortes werden stabil partitioniert, Diakritika (der
Assembler-eigene Begriff, auf den Word-Unit-Strichen
angewandt) hinter alle Körper-Striche, Reihenfolge innerhalb
beider Gruppen unverändert. Reine ORDNUNGS-Änderung: kein
Punkt bewegt sich.

**Erwartung (aus der Permutations-Probe der Autopsie):**
unter −0,36 (0,4503 → ~0,085), muß-Familie −0,11 bis −0,13;
alle geometrie-basierten Spalten IDENTISCH (aiou, Chamfer,
Struktur- und Markenzähler — dieselbe Segmentmenge), einzig
`dtw_xh` (und die Lift-Positionsspalten) bewegen sich; kein
anderes Dev-Wort ändert sich über ±0,002 (der Sweep fand
keinen weiteren Ordnungs-Gewinn).

**Gates:** (i) die vier Kollaps-Wörter fallen je um > 0,05;
(ii) KEIN Dev-Wort steigt um > 0,002; (iii) aiou/Chamfer/
Zähler byte-gleich (eine Abweichung wäre ein Bug der
Partition, kein Tuning-Fall — Kill); (iv) `dtw_reversed_better`
= 0. Bestehen alle: ADOPTION als Kette v2 (die erste
Formulierungsänderung der Route) mit datierter Re-Baseline —
deklariert: ALLE gepaarten Routen-Vergleiche rechnen ab dann
gegen die v2-Kette, die alten Zahlen bleiben als
v1-Geschichte lesbar; der PRODUKTIONS-Re-Harvest (DB) bleibt
davon getrennt hinter Owner-Go + dbsnapshot.

**Gemessen `aug19` — ALLE Gates bestehen exakt wie
vorregistriert, ADOPTIERT als Kette v2.** Dev-19, gepaart gegen
die v1-Baseline: **unter 0,4503 → 0,0854 (−0,365) · muß-3
0,2339 → 0,0962 · muß 0,2419 → 0,1096 · muß-2 0,2084 →
0,0877**; die übrigen 15 Wörter Δ exakt 0,0000, und JEDE
Geometrie-Spalte byte-gleich (aiou 0,6929, beide Chamfer,
cross 14+7, marks 1+1, retrace 6+13, touch 25, reversed 0) —
die Partition bewegt keinen Punkt, nur die Reihenfolge.
`HarvestOptions.marks_last` = True ist der v2-Default (False
bleibt als Archäologie-Knopf, das Mess-CLI-Flag entfällt mit
der Adoption).

### Kette K-B `aug19` — Vorregistrierung: die Zacken-Reparatur im Trace

Geschrieben und committet VOR der ersten Zahl. Die Zacken-Klasse
des Owner-Sichtbefunds (Galoppieren: das V in den i-Punkt — EIN
Polylinien-Punkt springt 0,44 xh weg und zurück —, die Nadel am
Kopf des ersten p — drei Punkte, 6–11× der Median-Schrittweite)
ist exakt die §11-Ausreißer-Form, für die der geteilte Detektor
`tools.pairlab.anchors` gebaut und an 17 von 22 Owner-Markierungen
validiert wurde. Die STATISTIK-Schicht repariert sie seit §11e;
der Trace zeigt sie bisher absichtlich roh („inspection layer,
needle and all") — eine Doktrin von VOR der Tintenfolger-Kampagne,
in der der Trace zum PRODUKT wurde. **EIN Knopf:
`HarvestOptions.trace_repair`** (CLI `--trace-repair`, Label
`chain+repair` — das A1-Muster: ändert, was der Trace ZEIGT, nie,
was die Ernte MISST): `repair_stranded_anchors` — DIESELBE
geteilte Funktion, kein Zweitbau; das Kriterium ist skalenfrei
(Schritt-Verhältnisse je Strich) — läuft je assembliertem
Trace-Strich; Läufe konsekutiv geflaggter Punkte werden als ein
Stück auf die Sehne der ungeflaggten Nachbarn interpoliert, nie
auf Tinte gesnappt, Anzahl geloggt (`trace_repaired` im Meta).

**Erwartung:** die beiden Galoppieren-Zacken verschwinden
(sichtbar + dtw dort leicht runter); der i-Punkt-Strich fällt
ohne Ausreißer unter die 0,8-xh-Marken-Schwelle — die fehlende
i-Marke DARF heilen (`marks_missing` 1 → 0); alle übrigen
Dev-Wörter ±0,002; `aiou` ~neutral (Zacken liegen in Luft).
**Gates:** kein Dev-Wort schlechter als +0,002; Struktur- und
Markenzähler ohne Netto-Verlust; `aiou`-Median-Δ > −0,005;
reversed = 0. Kill: kostet die Reparatur irgendwo eine ECHTE
Struktur (ein „Spike", der in Wahrheit ein Kreuzungsschenkel
war), ist der Polylinien-Einsatz des Detektors verworfen und der
Weg zurück die Anker-Ebene (keep_solve-Plumbing, eigene
Pre-Reg). Bestehen alle Gates: Adoption als **Kette v3** (die
Trace-Doktrin-Zeile in `chain_word_strokes` wird im selben
Commit umgeschrieben — der Trace ist seit der Kampagne Produkt,
die Inspektion der rohen Nadel bleibt über
`trace_repair=False` erreichbar).

**Gemessen `aug19` — alle Gates bestehen, ADOPTIERT als Kette
v3; die Zacken trugen fast den ganzen Galoppieren-Rest.**
Dev-19, gepaart gegen v2: **Galoppieren 0,2329 → 0,0401
(−0,193)** — die V-Zacke in den i-Punkt und die p-Nadel waren
sein dominanter Fehler, und wie vorregistriert erhofft fällt
der reparierte i-Punkt-Strich unter die Marken-Schwelle:
**`marks_missing` 1 → 0**, `lift_delta` Galoppieren +1 → 0 —
dazu die-2 −0,026, zwei −0,015; kein Wort über +0,0016 (unter,
im Rahmen des +0,002-Gates). Zähler: `retrace_spurious` 13 → 6
und `touch` 25 → 21 (die Zacken WAREN die unechten Zonen),
Kreuzungen exakt unverändert, `aiou` +0,006,
`max_absorption` 94 → 79. Ehrlich benannt: `retrace_missing`
6 → 7 — die Autopsie (Flag-Positionen + Sichtprüfung) verortet
alle sieben unter-Reparaturen bei u 5,6–6,6 IM er-Gekritzel
(der echte t-Stamm-Retrace bei u 4,7–5,1 bleibt unberührt):
eine ZUFALLS-Korrespondenz von Tangle-Geometrie löst sich, die
Netto-Retrace-Defekte fallen 19 → 13 — das Kill („echte
Struktur") feuert nicht. `trace_repair` = True ist der
v3-Default (False = Nadel-Archäologie), die Doktrin-Zeile in
`chain_word_strokes` ist umgeschrieben.

**Re-Baseline Kette v3 `aug19` (deklariert):** dtw-Median
**0,0491** · p90 **0,0894** · worst **muß 0,1096** · marks 0+1
· aiou 0,6987 · cross 14+7 · retrace 7+6 · touch 21. Gepaarte
Vergleiche gegen v3: **Lotse v0.11 Δ-Median +0,0016 (Sign
12:7)** — nach zwei reinen Trace-Schicht-Fixes führt die KETTE
erstmals auf Median UND p90; der Lotse behält Struktur (7
gegen 21 Netto-Kreuzungsdefekte), aiou (0,743) und
Kreuzungs-Ortsfehler (0,066 gegen 0,083 xh). Tagesbogen der
Route: 0,0576/0,2355 → 0,0491/0,0894, ohne dass sich ein
einziger Fit-Parameter bewegt hat — beide Gewinne lagen in der
KANDIDATEN-SchICHT (Ordnung + Ausreißer), nicht im Solver.

**Re-Baseline Kette v2 `aug19` (deklariert, lokale Umgebung der
Runde):** dtw-Median 0,0576 (unverändert — die Median-Wörter
waren nie betroffen) · **p90 0,2355 → 0,0988** · worst jetzt
**Galoppieren 0,2329** (der echte unter-Rest: 0,0854, das
er-Gekritzel aus dem versetzten Karten-Init) · Struktur- und
Markenspalten identisch zu v1. **Gepaarte Routen-Vergleiche
gegen v2:** Lotse v0.11 Δ-Median **+0,0007** (Sign 10:9,
p=1,0) — der −18-%-Vorsprung der Lotse-Route gegen v1 bestand
zu praktisch 100 % aus dem Assembly-Artefakt; die Routen
stehen jetzt im Median GLEICHAUF, die Kette führt beim p90
(0,0988 gegen 0,1129), der Lotse behält die Struktur (7 gegen
21 Netto-Kreuzungsdefekte), die Marken (0 gegen 1 fehlend),
aiou (0,7434 gegen 0,6929) und den Kreuzungs-Ortsfehler
(0,066 gegen 0,083 xh). Das Fusions-Orakel und die
InkSight-/Nullprobe-Paarungen sind mit ihrer nächsten Messung
gegen v2 neu zu beziffern (lokal nicht neu gerechnet — die
absoluten Wortwerte dieser Routen ändern sich nicht, nur ihre
Deltas). Der PRODUKTIONS-Re-Harvest der `traced`-Zeilen mit
v2-Ordnung bleibt hinter Owner-Go + dbsnapshot (die
Fixture-`traced`-Zeilen tragen bis dahin die v1-Ordnung —
der Bench rechnet den `chain`-Kandidaten ohnehin frisch).

### Route „Lotse" v0.13/v0.14 `aug19` — Vorregistrierung: die Entdrillung, dann die „all"-Stufe (Owner-Go „weiter mit lotse neben ink")

Geschrieben und committet VOR der ersten Zahl. Ziel ist der
letzte Owner-Punkt der Runde: der Lotse fährt in Doppelzonen und
Brücken noch die ROHE Karte („windows" pinnt nur Fenster) — die
G-Kästen, die r-Geraden, der Galoppieren-Kasten, die
Wer-Diagonale. Die „all"-Stufe scheiterte am 19. um genau EIN
Doppel-X; der Blocker sind die Duplikate.

**Autopsie vor dem Mechanismus (Roh-Ereignis-Zählung, proper
segment intersections der Body-Kette, 0,35-xh-Eigenbogen-Floor):**
die Duplikat-Orte sind GEWEBE — mehrere Schnitt-Ereignisse
desselben Pass-Paars in kleinem Fenster: mit-2 trägt DREI
Ereignisse, wo die Hand einmal kreuzt (Orte 5,08/5,14) · will
trägt neben dem echten Schnitt (1,94) drei Gewebe-Ereignisse um
2,2–2,3 · Galoppieren fünf um 8,7–9,1 (Hand 1) und sechs um
13,3–13,5 (Hand 0). Der v0.12-Befund erklärt sich damit
vollständig: die Sehne entfernte ALLE Schnitte einer Stelle —
die Parität verlangt aber PAARWEISES Entfernen (3 → 1 · 5 → 1 ·
6 → 0), das genau die topologisch nötige Kreuzung stehen lässt.

**Der Mechanismus (v0.13, EIN Knopf `UNTWIST_WINDOW_UNITS`,
0 = aus, Leiter 0,5 / 0,8):** Auf den assemblierten
Kandidaten-Strichen werden Schnitt-Ereignis-PAARE gesucht, deren
BEIDE Bogenabstände ≤ Knopf und deren Schnittpunkte ≤ Knopf/2
auseinanderliegen (echte getrennte Kreuzungen wie wills
l-Schleifen liegen weit darüber und bleiben unberührt). Je Paar
wird der Wiggle-Bogen zwischen seinen beiden
Ereignis-Parametern an der Sehne P1→P2 GESPIEGELT — der Bogen
wechselt die Seite, beide Schnitte des Paars verschwinden,
Richtung und Parametrisierung bleiben erhalten, die Geometrie
bleibt in der Wiggle-Amplitude (< Fenster). Iterativ bis kein
Paar mehr feuert (Deckel 8 Durchläufe je Wort), Anzahl geloggt.
*Präzisierung VOR der ersten Bench-Zahl (Synthetik-Fund des
Unit-Tests, im Test gepinnt):* „der Wiggle" ist die Seite mit
der GRÖSSEREN maximalen Sehnen-Abweichung — die ursprüngliche
„kürzere-Bogen"-Heuristik ist degeneriert (die sehnen-nahe
Gegenseite hat Bogenlänge ≈ Sehnenlänge und die Spiegelung
wäre ein No-op); eine Seite ohne messbare Abweichung ist nie
der Wiggle.

**Stufen:** v0.13 = "windows" + Entdrillung; v0.14 = "all" +
Entdrillung (die §7.9-Wiedervorlage: Zonen-Rides und natürliche
Brücken bekommen die Knoten-Plateau-Pinnung der Fenster).
Adoptiert wird höchstens EINE Konfiguration (die beste, die alle
Gates besteht).

**Gates v0.13 (gegen den v0.11-Stand):** `cross_missing` ≤ 1
(NICHTS Echtes verlieren — steigt es, feuert das Kill),
`cross_spurious` fällt netto (Erwartung 6 → ≤ 3), Marken
unverändert, Retrace-Zähler ohne Netto-Anstieg, `aiou`-Median-Δ
≥ −0,02 gegen 0,7434, dtw je Wort ±0,003, p90 ≤ 0,113
(v0.11-Stand), reversed 0. **Gates v0.14 (gegen den
v0.13-Stand):** Netto-Kreuzungsdefekte ≤ v0.13, `aiou` steigt
oder hält (die Zonen verlassen die Luft — fällt aiou, ist die
Pinnung dort falsch verdrahtet), dtw-Median hält (±0,003),
Sichtprüfung der vier Owner-Stellen (G · unter/Galoppieren-r ·
Galoppieren-Kasten x≈360 · Wer-Diagonale) wird dem Ergebnis
beigelegt. Paarungen beschreibend gegen die Kette v3
(0,0491/0,0894). Kill v0.14: erzeugt die Zonen-Pinnung neue
Netto-Defekte, bleibt v0.13 (bzw. v0.11) stehen und der Rest
gehört der Karten-Form-Schiene.

**Gemessen `aug19` — v0.13 bei 0,5 ADOPTIERT; 0,8 vom eigenen
Kill verworfen und der Diskriminator sauber benannt; v0.14 per
Gate verworfen, mit dem stärksten SICHTBEWEIS der Runde.**

*v0.13 (dev-19, je 19/19 ok):* **w0,5** (16 Paare entdrillt) →
`cross_missing` 1 (unverändert), `cross_spurious` 6 → **5**
(wills Duplikat heilt), Marken/Retrace unverändert, `aiou`
−0,0036, dtw je Wort ≤ ±0,0011, p90 0,1129 — ALLE Gates
bestehen, **Netto-Defekte 7 → 6**, `UNTWIST_WINDOW_UNITS` =
0,5. **w0,8** (32 Paare) → spurious 6 → 2, aber
`cross_missing` 1 → **6**: das weite Fenster entdrillt auch
GENUIN nahe ECHTE Paare (mits t-Doppel bei 0,07 xh, unters und
Galoppierens enge X) — vom eigenen Kill verworfen. Der Befund
benennt die Grenze exakt: GEOMETRIE allein kann ein
Gewebe-Duplikat nicht von einem echten engen Doppel
unterscheiden — der ehrliche Diskriminator ist das SOLL (die
Karte weiß, wie viele Kreuzungen in eine Nachbarschaft
gehören: mits Doppel steht im Soll, die Gewebe nicht) →
Rettungsweg **soll-budgetierte Entdrillung**, eigene Pre-Reg
(§7.9-Zeile im selben PR).

*v0.14 („all" + Entdrillung 0,5; 13 Paare):* die
Tinten-Gewinne kommen wie erhofft — `aiou` 0,7398 → **0,7521**,
Precision-Chamfer −0,0021, dtw 8:1 Wörter besser (mit-2/mit
−0,009, muß-2/-3, Galoppieren, Wer), und der SICHTBEWEIS ist
der stärkste der Runde: **das G wird erstmals fast wie von der
Hand geritten** (Oval, Kopfschleife, Stamm, Unterschleife am
Ink — alle Luft-Kästen weg), auch der Galoppieren-Rest-Kasten
und die er-Region legen sich an. ABER die Strukturzähler
kippen in GENAU den zwei schlimmsten Karten-Form-Regionen:
Galoppieren verliert das G-Kopf-X ((1,6·1,67) — die gepinnte,
formfremde G-Karte schließt die Schleife nicht, wo die Tafel
kreuzt) und erfindet eines am p (7,97·0,83) — Netto 6 → 8 >
Gate, VERWORFEN wie vorregistriert („der Rest gehört der
Karten-Form-Schiene", hier wörtlich eingetreten). Konstanten:
`MAP_RUN_PIN_KNOTS` bleibt "windows". Rettungsweg:
**Wiedervorlage von v0.14 NACH den
Karten-Form-Autorenschritten** (G-Chart/Laufform,
p-Unterlängen — exakt die beiden Gate-Brecher; §7.7-Protokoll
misst dann neu) — der Sichtbeweis verdoppelt den Ertrag dieser
Autorenschritte: sie reparieren Komposition UND schalten die
saubere Zonen-Fahrt frei.

### Route „Lotse" v0.15 `aug19` — Vorregistrierung: die soll-budgetierte Entdrillung (L1h)

Geschrieben und committet VOR der ersten Zahl (nach dem
Owner-Merge von #387 und „weiter"; Cherry-pick-Recovery des
Squash-Rennens dokumentiert im Branch). Der v0.13-Fund: das
0,8-Fenster heilt alle Duplikate, tötet aber genuin nahe ECHTE
Paare (mits t-Doppel, 0,07 xh) — Geometrie allein trennt die
Klassen nicht. Der vorregistrierte Diskriminator ist das SOLL:
die KARTE kennt ihre eigenen Selbstschnitte, also weiß der
Kandidat, wie viele Kreuzungen in eine Nachbarschaft gehören
(mits Doppel steht in der Karte, die Gewebe nicht).

**EIN Knopf: `UNTWIST_SOLL_BUDGET`** (False = v0.13-Verhalten;
True = Budget-Regel). Die Regel: ein Ereignis-Paar darf nur
entdrillt werden, wenn die Nachbarschaft danach nicht UNTER ihr
Soll fällt — `n_events_near − 2 ≥ n_soll_near`, mit
`n_events_near` = Kandidaten-Schnitt-Ereignisse und
`n_soll_near` = Karten-Selbstschnitte im festen Radius
`UNTWIST_SOLL_RADIUS_UNITS` = 0,55 xh um den Paar-Mittelpunkt
(der Matcher-Radius des Lineals, als deklarierter Snapshot,
kein Suchknopf). Damit ist mits Doppel konstruktiv geschützt
(3 − 2 < 2), während die Gewebe (Soll 0–1, Ereignisse 3–6)
paarweise fallen.

**Leiter: Budget an × Fenster {0,5 · 0,8}** — die Hypothese ist,
dass das weite Fenster ERST mit dem Budget sicher wird und dann
auch mit-2s und Galoppierens Rest-Duplikate erreicht. Gates
gegen den v0.13-Stand (missing 1 · spurious 5 · Netto 6):
`cross_missing` ≤ 1 (steigt es, hat auch das Budget ein echtes
Paar nicht geschützt — Kill, Rettungsweg wäre Matching gegen
die Soll-POSITIONEN statt Zählungen); `cross_spurious` fällt
netto (Erwartung ≤ 3); Marken unverändert; Retrace ohne
Netto-Anstieg; `aiou`-Median-Δ ≥ −0,02 gegen 0,7398; dtw je
Wort ±0,003; p90 ≤ 0,113; reversed 0. Adoptiert wird höchstens
EINE Stufe.

**Gemessen `aug19` — BEIDE Stufen verworfen; der Fund schließt
den Tag mit der dritten unabhängigen Bestätigung derselben
Wurzel.** Leiter (dev-19, je 19/19 ok): w0,5+Budget → nur noch
6 statt 16 Paare entdrillt, `cross_spurious` 5 → **6** — das
Budget VETIERT ausgerechnet wills bereits geheilten Fix: die
feste 0,55-Radius-Zählung wirft das benachbarte ECHTE
l-Kreuzungs-X (0,28 xh entfernt) mit in die
Gewebe-Nachbarschaft, und die Arithmetik wird fälschlich
konservativ. w0,8+Budget → zusätzlich `cross_missing` 1 → **2**:
in unters e→r-Region — der am schlechtesten platzierten
Karten-Stelle der Runde — liegen die Karten-Selbstschnitte
NEBEN der Tinte, das echte Paar hat dort kein Soll in
Reichweite und stirbt trotz Budget: **das Soll-Budget erbt
exakt die Karten-Platzierungsfehler, die v0.14 schon als
Gate-Brecher maß.** Beide Stufen von ihren Gates verworfen,
`UNTWIST_SOLL_BUDGET` bleibt False (Knopf + Test bleiben
deklariert); v0.13 (Geometrie-only, 0,5) bleibt der adoptierte
Stand. Die Lehre in einem Satz: Punkt-, Zonen- und jetzt auch
BUDGET-Verfeinerungen des Lotsen sind alle an derselben Decke —
die drei verbleibenden Duplikate und die „all"-Stufe warten auf
die KARTEN-FORM-Autorenschritte, danach sind v0.14 und eine
soll-geführte Entdrillung (dann mit vertrauenswürdiger Karte,
Positions- statt Zähl-Matching) gemeinsam wiedervorzulegen.
§7.9-Zeile im selben PR.

**Nachtrag `aug19` spät — die Karten-Form-Decke ist präzisiert:
überwiegend eine LAUFFORM-LÜCKE, kein Chart-Fehler
(Owner-Einwand „das G-Template sieht doch gut aus" — bestätigt).**
Diagnose in der DB (nur lesend): **43 von 62 Glyphen haben KEINE
Laufform-Variante** — darunter ALLE Versalien, k, s, v, x, b, f,
q, j und die Umlaute; die Komposition setzt dort die rohe
Chart-Form ein. Ursache je Owner-Stelle: G hat 3 QC-Fits (unter
`--min-n` 4), k und W je EINEN. Das Chart-G selbst ist gut
(chart-treu); DIESE Tafel-Hand schreibt das Oval aber ~65 %
breiter (Beleg ~1,76 xh gegen Karte ~1,06), und die Schicht, die
Hand-Breite trägt, ist per Architektur die LAUFFORM — die beim G
mangels n fehlt. Die drei vorhandenen G-Fits ziehen in die
richtige Richtung (u-Breite 1,74–1,96 gegen Template 1,69), sind
als Mess-Fits aber chart-regularisiert. Das r hat dagegen eine
Laufform (18 Fits) — seine Abweichungen bleiben die
dokumentierten o→r-/Platzierungs-Klassen. Konsequenz für die
Rettungswege: der „G-Chart-Autorenschritt" ENTFÄLLT (kein
Re-Trace — Chart bleibt kanonisch); an seine Stelle tritt der
messbare Kandidat **Versalien-Laufform-Ausnahme** (`--min-n` 3
für Versalien bzw. eine G-Laufform aus den 3 Fits, eigene
Pre-Reg mit wordbench-Gates + Owner-Go vor dem DB-Write). ECHTE
Autorenschritte bleiben: der W-Ansatz-Retrace (K3 —
Duktus-INHALT, nicht Breite), der p-Unterlängen-Entscheid und
der Bestätigungssatz.

**Zweiter Nachtrag `aug19` spät — auch W und p lösen sich auf
(Owner-Einwand „W und p sehen auch gut aus", je Detektor-Daten
und Bild geprüft):** (1) **W**: Die aktuelle Wer-Referenz hat
KEINEN Ansatz-Retrace am W — die K3-These stammt aus der Zeit
VOR der 19er-Nachfahrung. Die fehlende Soll-Zone (Wer 1 vs 2)
ist die doppelt gefahrene e→r-DIAGONALE der Hand
(Zonen-Mitte 2,96 · 0,62 — Schreibgewohnheit, Beleg-Eigenschaft);
das reale W-Problem ist der **W→e-JOIN der Komposition**, der
die e-Schleife zu einem Ballon über volle Oberlänge aufbläst
(Join-Grammatik nach Kapital-Exit — eigener Kompositions-Arm,
kein Autorenschritt). Der „W-Trace"-Autorenschritt ist damit
zurückgezogen. (2) **p**: Die Komposition fährt die große
Unterschleife MIT (Soll-Retrace-Zonen 7,34/8,82 decken sich mit
der Hand); der ganze Unterschied ist ein DURCHSTOSS-Detail —
die Hand-Rückkehr durchsticht die Abwärtslinie (X bei v 0,10
bzw. 0,17), die komponierte Rückkehr läuft tangential ein und
zählt darum als Retrace statt als Kreuzung. Das ist die
K1-Klasse („Schnitt mit Überstand", am t-Balken gemessen und
adoptiert): ein an beiden p-Belegen nachmessbarer
Rückkehr-Überstand als Composer-Klassenregel, eigene Pre-Reg
mit `soll_cross_agree`-je-Wort- und wordbench-Gates — der
G1-„Autorenentscheid" reduziert sich auf die Abnahme dieser
gemessenen Regel. Nach den drei Owner-Einwänden dieses Abends
bleibt vom ursprünglichen Autoren-Katalog damit als
Autorenschritt im engen Sinn nur noch der BESTÄTIGUNGSSATZ;
alles andere (Versalien-Laufform · W→e-Join · p-Überstand ·
e→r-Platzierung · o→r-Höhe · Vorschub-Drift) ist als messbarer
Kompositions- oder Laufform-Arm eingeordnet.

**Dritter Nachtrag `aug19` spät — die Autopsien korrigieren BEIDE
Mechanismen des zweiten Nachtrags; die Wurzel wird dadurch
einheitlicher, nicht kleiner.** Zwei unabhängige Code-Autopsien
(Recon-Runde, je mit Repro auf der eingefrorenen Karte) drehen
die Detail-Diagnosen:

(1) **W: der Join balloniert NICHT.** Auf der komponierten
Wer-Karte bleibt der W→e-Verbinder in y ≤ 0,56, das komponierte e
endet normal bei 0,943, Entry-Trim 0 — der „Oberlängen-Ballon"
des zweiten Nachtrags war die dritte W-SCHLEIFE DER REFERENZ über
der zu weit links komponierten e-Position. Der echte Befund: die
komponierten W-Apexe liegen bei x 0,45/1,16/2,38 gegen die Hand
0,81/1,51/2,82 (~0,4 xh links, Höhen binnen 0,05 xh), das
komponierte e startet bei x 2,88 MITTEN in der dritten
Hand-Schleife. Das ist die Laufform-Lücke des W (1 QC-Fit, kein
`LAUFFORM_SX`-Eintrag) — der „W→e-Join-Arm" entfällt, das W fällt
in den Lücken-Schluss (LF1).

(2) **p: kein Composer-Klassenfall — die gespeicherte p-LAUFFORM
hat den Durchstoß an den Median verloren.** p steht in KEINER
Klassentabelle (`LOOP_EXIT_BASES` = {d, s}; die
Descender-Maschinerie feuert bei Exit-y +0,79 nie) — die Rückkehr
ist authored Geometrie. Die komponierten p-Kreuzungen EXISTIEREN
sogar (2,5–4,8× über der Pierce-Marge) und fallen erst am
v2.1-Retrace-Filter: die Schenkel laufen vor dem X zu eng/parallel
(Partner-Kriterium 0,16 xh). Wurzel: das CHART-p behält isoliert
seine Kreuzung (1), die gespeicherte LAUFFORM verliert sie (0) —
der Anker-Median hat den Schleifenschluss glattgebügelt
(Annäherungs-Spalt 0,126 → 0,081 xh). Das Hand-Soll, an beiden
p-Belegen gemessen: Kreuzungswinkel 67,6°/65,6°, 0,05-xh-Freigang
nach 0,073/0,065 xh Bogen, die Rückkehr steigt bis v ≈ 0,92 in
den Join. Der im zweiten Nachtrag skizzierte
K1c-Composer-Überstand ist damit UNGEMESSEN zurückgezogen (nie
vorregistriert, keine Zahl erzeugt); an seine Stelle tritt der
Laufform-Arm **LF2 „p-Topologie"** — Autopsie des
Occurrence-Stapels zuerst (verlieren die Einzel-Fits das X, oder
frisst erst der Median es?), dann eigene Pre-Reg.

Damit ziehen ALLE drei Owner-Stellen des Abends (G, W, p) auf
DIESELBE Schicht: die Laufform — als Lücke (G/W/k: 15 der 34
Fixture-Glyphen ohne Variante 100, darunter alle Versalien) und
als Aggregations-Defekt (p). Der Karten-Form-Katalog des Abends
besteht aus zwei Laufform-Armen (LF1/LF2) plus den
Platzierungs-Klassen (e→r · o→r · Vorschub-Drift).

### Laufform LF1 `aug19` — Vorregistrierung: der Lücken-Schluss (Evidenz-Boden der Scan-Fits)

Geschrieben und committet VOR der ersten Zahl (Owner-Go „weiter
ohne Pause die Punkte abarbeiten" nach den drei Einwänden;
Rettungsweg-Konversion der §7.9-Zeilen v0.14/v0.15 und des ersten
Nachtrags „Versalien-Laufform-Ausnahme").

**Hypothese.** 15 der 34 Fixture-Glyphen (alle Versalien, dazu
ae · b · f · k · s · ue · v) haben keine Laufform-Variante — die
Komposition setzt dort die rohe Chart-Form ein, und die Schicht,
die per Architektur die Hand-Breite trägt, schweigt. Die drei
schlimmsten Karten-Form-Stellen der Lotse-Runde (G-Kopf, W-Apexe,
k-Kringel) liegen alle in dieser Lücke. Der Harvest
(`tools/laufform/harvest.py`, offline gegen die eingefrorene
Root, keine DB) kann die Lücke aus den vorhandenen Scan-Fits
schließen; blockiert hat bisher allein sein CLI-Boden
`--min-n 4` (G: 3 QC-Fits; der SERVER-Boden für echte Writes ist
`LAUFFORM_MIN_OCCURRENCES` = 3).

**EIN Knopf: der Evidenz-Boden `--min-n`, Leiter {3 · 1}** —
angewendet ausschließlich auf LÜCKEN-Glyphen (ohne gespeicherte
Variante 100); gespeicherte Laufformen werden nie überlagert.
Stufe 3 ist die „Versalien-Laufform-Ausnahme" des ersten
Nachtrags (erwartet: G); Stufe 1 die Dünn-Evidenz-Stufe
(erwartet zusätzlich W, k, …— die Fit-Zahl je Glyph wird
berichtet, eine n=1-„Laufform" ist der eine Fit selbst). Evidenz
sind NUR die M4/Chain-Scan-Fits der eingefrorenen Tinte — keine
authored Traces, also keine Zirkularität gegen das
tracebench-Lineal; Pfad `--path chain --sets words` (die
Produktions-Evidenz der 245 gespeicherten Instanzen), BLAS
gepinnt.

**Messung (alles TROCKEN, kein DB-Write).**
(a) wordbench `--style suetterlin --set all --laufform <drafts>`
— per Doktrin §6 eine OFF-HEADLINE-Kandidatenzahl. Gates:
`word_loss`/`pair_loss` ≤ +0,002 gegen die stehende Basis
0,108091 / 0,146602; bewegen dürfen sich nur Wörter/Paare mit
Lücken-Glyphen.
(b) Soll-Abgleich auf einer gepatchten Kopie der Fixture-Root
(templates_laufform.json + Drafts): `soll_cross_agree`/
`soll_zones_agree` JE WORT — kein Wort verliert Übereinstimmung.
(c) Lotse auf der Kandidaten-Karte (Treiber über gepatchte
Cases, adoptierter v0.13-Stand): dev-19 gegen die v0.13-Basis —
`cross_missing` ≤ 1 · Netto-Kreuzungsdefekte ≤ 6 ·
aiou-Median-Δ ≥ −0,02 gegen 0,7398 · Marken unverändert · dtw je
Wort ±0,003 außer in Wörtern mit Lücken-Glyphen · reversed 0.
Deklariertes Registrierungs-Kaveat: das Overlay bewegt Karte UND
tx/ty-Registrierung (word_metric-Gridsearch) — die Vergleiche
messen Karten- plus Platzierungs-Effekt gemeinsam, so gewollt.
(d) Sichtprüfung der G/W/k-Wörter (Overlay-Bilder).

**Adoption/Write.** Adoptiert wird höchstens EINE Stufe, und nur
als KANDIDATEN-Zustand (trocken). Ein DB-Write (PUT laufform je
Glyph bzw. `apply-laufform`) ist ein separater Schritt hinter
`dbsnapshot` + explizitem Owner-Go; für n<3-Zeilen erzwingt der
Endpoint `?min_occurrences=1` als ausdrückliche Owner-Aussage.
Danach (und erst danach) die vorregistrierte Wiedervorlage
v0.14 + soll-geführte Entdrillung (§7.9) — trocken auf der
Kandidaten-Karte bereits in dieser Runde vormessbar.

**Gemessen `aug19` — BEIDE Stufen verworfen, an EINEM exakt
lokalisierten Riss; die Gewinnseite ist die größte der
Lotse-Kampagne.** Harvest offline (211/277 Fits akzeptiert):
JEDES Lücken-Glyph hat ≥ 1 Fit — Stufe 3 = {G n=3, Z n=3},
Stufe 1 = alle 15. **Stufe 3:** wordbench 0,108091 → 0,107215
(pair byte-gleich; nur Lücken-Wörter: Z-Wörter −0,012…−0,017,
Gewehr −0,0096, Galoppieren −0,0061, Gaul +0,0049). Lotse:
Galoppieren dtw −0,010, `cross_spurious` 5 → 3 (die
G-Kopf-Duplikate heilen!) — ABER `cross_missing` 1 → 2 und
Galoppieren-Soll 6 → 5: **der frische G-Median verliert die
zweite Chart-G-Kreuzung** — Gate (c) verletzt, Stufe verworfen.
**Stufe 1:** wordbench 0,108091 → 0,105664 (18 Wörter besser,
6 schlechter — die n=1-Drafts streuen: Wer +0,0267, das
+0,0094, kann +0,0066 gegen Sprünge −0,0392, Zügel −0,0201,
Pulver −0,0143, Einen −0,0140, linken −0,0127). Lotse:
dtw-Median 0,0585 → 0,0572, **aiou 0,7398 → 0,7527**,
spurious 5 → 3, linken-Soll 4 → 3 = Übereinstimmung (Hand 3),
Marken sauber — und DASSELBE G-Gate (`cross_missing` 2) →
verworfen. Befund: die Verwerfungs-Ursache ist in beiden Stufen
die TOPOLOGIE der aggregierten Form, nie die Breite — der
G-Median zählt 1 statt 2, und die drei G-Einzelfits zählen
selbst nur 0/1/1 (auch die chart-regularisierte M4-Passung
erhält die gezählte Kreuzung nicht zuverlässig). Rettungsweg:
LF3 (Topologie-Reparatur), §7.9-Zeile im selben PR.

### Laufform LF2 `aug19` — Vorregistrierung: der Topologie-Wächter (h & p)

Geschrieben und committet VOR der ersten Gate-Zahl; die
Autopsie-Zahlen darunter sind Diagnostik (wie die
L2-Rest-Autopsie), keine Arm-Messung.

**Autopsie-Befund.** (1) Auf ANKER-Ebene ist die p-Topologie
intakt (Chart X=3, Laufform X=3, beide akzeptierten
Occurrence-Fits X=5/3, frischer Median X=3) — verloren geht das
GEZÄHLTE X erst nach Spline-Sampling an den v2.1-Kriterien: der
Median verengt den Annäherungs-Spalt der Schenkel
(Anker 0,029 → 0,022, gesampelt 0,126 → 0,081 xh), und der
Retrace-Filter kippt. Es ist also KEIN Fit-Defekt, sondern ein
Schwellen-Kipp durch die Median-Verengung. (2) Der Lineal-Sweep
(per-Letter-Soll-Zellen aller 63 Wörter, mit gegen ohne
gespeicherte Laufformen) findet GENAU ZWEI Verlierer und keinen
Gewinner: **h 2 → 0 gezählte Kreuzungen in JEDEM der 10 Slots**
und **p 1 → 0 in allen 4** (Galoppieren ×2, Sporn, Sprünge).
(3) Gegenprobe Hand: die authored h-Wörter kreuzen real (haben
und scharfen je 1 Ascender-X bei v ≈ 0,91/0,95) — die
h-Laufform löscht eine geschriebene Kreuzung. (Das Chart zählt
am h 2; ob die Hand die zweite schreibt, prüft der
Soll-Abgleich mit — berichtet, nicht Kriterium.)

**Mechanismus.** Die Schichtungs-Doktrin (architektur.md §3/§5,
jul31-Split): das Chart trägt den DUKTUS (Strichfolge,
Kreuzungs-Auflösung), die Laufform trägt die HAND-BREITE. Eine
Laufform-Zeile, die eine gezählte Chart-Kreuzung ihres Glyphen
löscht, überschreibt den Prior statt ihn zu weiten. Der Wächter
setzt die Schichtung durch: solche Zeilen werden nicht
komponiert (Fallback: rohe Chart-Form), bis eine
topologie-erhaltende Aggregation existiert.

**EIN Knopf: der Wächter an/aus.** Die Wirkmenge ist
DETERMINISTISCH aus dem Sweep (keine Handauswahl): {h, p}.

**Messung (trocken, Root-Kopie ohne h/p-Laufform).**
(a) wordbench `--set all --fixtures <wächter-root>`
(Off-Headline): `word_loss`/`pair_loss` ≤ +0,002; erwartete
Bewegung nur in h/p-Wörtern. Die Erwartung ist zweiseitig
ehrlich: der Wächter KOSTET die h-Laufbreite — die Tinte darf
es spüren, die Struktur muss es zurückzahlen.
(b) Soll-Abgleich je Wort: erwartet Galoppieren 6 → 8 (die zwei
p-Rückkehr-X der Hand), Sporn/Sprünge +1, h-Wörter +2 je h;
kein Wort verliert Übereinstimmung.
(c) Lotse auf der Wächter-Karte gegen die v0.13-Basis:
`cross_missing` ≤ 1 · Netto-Defekte ≤ 6 · aiou-Median-Δ ≥ −0,02
· Marken unverändert · dtw je Wort ±0,003 außer h/p-Wörtern ·
reversed 0.
**Benannter Rettungsweg im Verwerfungsfall:** die
topologie-erhaltende Aggregation (Median mit
Kreuzungs-Anker-Ausrichtung statt roher Anker-Median) als
eigener Arm — der Wächter bliebe dann als Write-Path-Guard
(eine Zeile, die Topologie verliert, wird nie gespeichert).

**Gemessen `aug19` — Kern-Erwartung erfüllt, trotzdem VERWORFEN
in der Voll-Entfernungs-Form (Marken-Gate).**
(a) wordbench 0,108091 → 0,109448 (+0,00136, unter der
Kill-Schwelle; nur h/p-Wörter bewegen sich — zweiseitig wie
registriert: han −0,0103, Gewehr −0,0080, macht/schwer/haben
−0,003 gegen schießen +0,0340, Galoppieren +0,0256, fechten
+0,0237, auch-2 +0,0158 — der Preis der vollen
Breiten-Entfernung ist real).
(b) **Galoppieren-Soll 6 → 8 = Übereinstimmung mit der Hand (8)
erreicht** — die registrierte Kern-Erwartung; die h-Zellen
zählen konstruktionsbedingt wieder 2 (Chart-Form).
(c) Lotse: netto 4 (spurious 5 → 3) bei `cross_missing` 1,
aiou unverändert — ABER der Galoppieren-i-PUNKT fällt aus dem
Ritt (Kandidat 2 Strokes → 1, `marks_missing` 0 → 1): die
Karten-Verschiebung um die chart-p-Unterschleifen kippt eine
marginale Ritt-Komponente. „Marken unverändert" ist verletzt →
verworfen. Der Wächter bleibt als WRITE-PATH-Prinzip richtig
(nie eine Zeile speichern, die Topologie verliert); als
Kompositions-Fallback kostet er Breite und kippt den Ritt.
Rettungsweg (bereits oben benannt, jetzt quantifiziert):
**Reparatur statt Entfernung** — LF3, §7.9-Zeile im selben PR.

### Laufform LF3 `aug19` — Vorregistrierung: die Topologie-Reparatur (lokale Chart-Rückblendung)

Geschrieben und committet VOR der ersten Zahl. Konversion der
LF1/LF2-Negative: drei unabhängig gemessene Instanzen desselben
Mechanismus (gespeicherte h- und p-Laufform, frischer G-Draft)
zeigen, dass der rohe Anker-Median gezählte Chart-Kreuzungen
glattbügelt; LF2 hat bewiesen, dass die Topologie-Rückkehr die
Struktur zahlt (Galoppieren-Soll 8, netto 4), die volle
Chart-Rücksetzung aber Tinte kostet und den Ritt kippt.

**Mechanismus.** Für jede Laufform-Form (gespeicherte Zeile ODER
Lücken-Draft), die eine gezählte Chart-Kreuzung ihres Glyphen
verliert (Detektor = der LF2-Sweep), wird der Median nicht
verworfen und nicht ersetzt, sondern LOKAL repariert: die Anker
im festen Bogen-Fenster (0,5 xh) um die verlorene
Chart-Kreuzung blenden minimal zur Chart-Geometrie zurück —
`t` per Bisektion als KLEINSTES t ∈ [0, 1], das die gezählte
Kreuzung wiederherstellt (linearer Falloff zum Fensterrand;
deterministisch, kein Handknopf; findet die Bisektion kein t,
fällt das Glyph auf die Chart-Form zurück = LF2-Verhalten als
Restfall). Breite bleibt Laufform, Topologie bleibt Chart — die
Schichtungs-Doktrin als Konstruktion statt als Filter.

**EIN Knopf: Reparatur an/aus.** Wirkmenge deterministisch aus
dem Detektor: gespeicherte {h, p} plus jeder Lücken-Draft, der
ihn reißt (aktuell G; Z passiert unrepariert). Kandidaten-Karte:
eingefrorene Root + reparierte h/p + alle 15 Lücken-Drafts
(reparierte, wo nötig) — alles durch den EINEN kanonischen
Builder (`laufform_row_from_payload`).

**Messung (trocken).**
(a) wordbench `--set all` mit der Kandidaten-Menge: Headlines
≤ +0,002 gegen 0,108091 / 0,146602; Erwartung: die h/p-Wörter
BEHALTEN ihre Laufform-Gewinne (der LF2-Preis verschwindet).
(b) Soll je Wort: Galoppieren → 8, kein Wort verliert; die
Frage der zweiten Hand-h-Kreuzung wird berichtet.
(c) Lotse gegen die v0.13-Basis: `cross_missing` ≤ 1 ·
Netto-Defekte ≤ 6 · **Marken unverändert** (der i-Punkt-Kipp
von LF2 darf nicht wiederkehren) · aiou-Median-Δ ≥ −0,02 ·
dtw je Wort ±0,003 außer Laufform-Wörtern · reversed 0.
(d) Sichtprüfung G/W/k/h/p.
Hält LF3 seine Gates, ist seine Karte die KANDIDATEN-KARTE der
vorregistrierten v0.14-Wiedervorlage (§7.9) — trocken noch in
derselben Runde; ein DB-Write bleibt hinter dbsnapshot +
Owner-Go (LF1-Regeln gelten fort).

**Gemessen `aug19` — (a) und (c) bestehen vollständig, (b)
verfehlt das Kompositions-Soll: nicht adoptiert wie gemessen,
der Riss ist auf die ORAKEL-EBENE lokalisiert.** Reparatur-Lauf:
F t=0,133 · K t=0,352 · k t=0,219 · f t=0,484 · b t=0,703 ·
**p t=0,562** repariert; E/P/S/W/Z/ae/s/ue/v passieren
unberührt; **G und h sind im 0,5-Fenster unreparierbar** →
Chart-Fallback (der registrierte Restfall — auch der frische
Detektor-Fund: die Drafts F/K/b/f/k hätten ihre Topologie
ebenso still verloren). Zahlen: wordbench 0,108091 → 0,107089
(pair byte-gleich; nur Laufform-Wörter; die Z/S/P/E/K-Gewinne
bleiben, h zahlt seinen LF2-Preis fort, weil unreparierbar →
Chart). Lotse: dtw-Median 0,0585 → 0,0573 · aiou 0,7398 →
0,7470 · spurious 5 → 4 (netto 5) · `cross_missing` 1 ·
**Marken unverändert — der LF2-i-Punkt-Kipp kehrt NICHT
zurück** · linken-Soll 4 → 3 = Übereinstimmung. Aber
Galoppieren: `soll_cross_letters` 5 → 7 (beide p-Zellen zurück)
bei KOMPOSITIONS-Soll unverändert 6 — das minimale t des
Buchstaben-Zellen-Orakels überlebt den Kompositions-Kontext
(Verbinder, Trims, Retrace-Partner benachbarter Züge) nicht;
LF2 (volles Chart-p) erreichte dort 8. Der Mechanismus ist
richtig, das Orakel zu schwach — Konversion LF3b unten.

### Laufform LF3b `aug19` — Vorregistrierung: die Topologie-Reparatur am Kompositions-Orakel

Geschrieben und committet VOR der ersten Zahl. Identischer
Mechanismus wie LF3 (lokale Chart-Rückblendung, 0,5-xh-Fenster,
minimales t per Bisektion, Chart-Fallback als Restfall) mit
EINER Präzisierung: das Bisektions-Orakel ist das
**KOMPOSITIONS-Soll des Repräsentanten-Wortes** (die
„Komposition (mit Verbindern)"-Zählung des Lineals) statt der
Buchstaben-Zelle — repariert ist eine Form erst, wenn die
Kreuzung im komponierten Wort zählt, nicht nur im
Buchstaben-Frame. Erwartung: p repariert bei höherem t
(0,56 < t ≤ 1), die übrigen Reparaturen ziehen ggf. nach.
Risiko, ehrlich benannt: je näher t an 1, desto näher rückt die
Karte an das LF2-Verhalten — der Galoppieren-i-Punkt-Kipp wird
explizit mitgeprüft. Gates unverändert LF3 (a)–(d), inklusive
„Marken unverändert" und Galoppieren-KOMPOSITIONS-Soll → 8.
Hält LF3b, ist SEINE Karte die Kandidaten-Karte der
v0.14-Wiedervorlage.

**Gemessen `aug19` — ALLE Gates bestehen: LF3b ist der erste
adoptierte Laufform-Arm (Kandidaten-Zustand, trocken).**
Reparatur-Lauf am Kompositions-Orakel: **p t=0,578 gegen
Kompositions-Ziel 8** · F 0,391 · K 0,328 · k 0,250 · f 0,477 ·
b 0,672 · P 0,008; E/S/W/Z/ae/s/ue/v passieren; G und h bleiben
unreparierbar → Chart-Fallback. Zahlen: (a) wordbench 0,108091
→ 0,107105, pair byte-gleich, nur Laufform-Wörter. (b)
**Galoppieren KOMPOSITIONS-Soll 6 → 8 = Übereinstimmung mit der
Hand**, `soll_cross_agree` 16 → 17/19, kein Wort verliert. (c)
Lotse gegen v0.13: dtw-Median 0,0585 → **0,0573** · aiou 0,7398
→ **0,7484** · spurious 5 → 4 (Netto 5) · `cross_missing` 1 ·
**Marken unverändert** (der i-Punkt bleibt — das minimale t
liegt unter dem LF2-Kipp-Punkt) · Wer +0,007/linken −0,003
(beide Laufform-Wörter, Ausnahme greift) · reversed 0.
Einordnung: Galoppieren zählt jetzt spurious 2 statt 3 bei
soll-treuer Karte; der Wer-dtw-Preis kommt vom verrauschten
n=1-W-Draft (wordbench Wer +0,0267) — für den späteren DB-Write
bleibt die Stufen-/Glyphen-Auswahl eine Owner-Entscheidung je
Glyph (LF1-Regeln). Die LF3b-Karte ist die Kandidaten-Karte der
Wiedervorlage unten.

### Wiedervorlage v0.14 `aug19` — Vorregistrierung: die „all"-Stufe auf der LF3b-Karte

Geschrieben und committet VOR der ersten Zahl. Einlösung der
stehenden §7.9-Zeilen (v0.11-„all", v0.14, v0.15): die
Wiedervorlage NACH den Laufform-Armen, trocken auf der
injizierten Kandidaten-Karte. Der originale v0.14-Bruch lag
exakt an den zwei Laufform-Defekten (G-Kopf-X stirbt an der
formfremden Karte, p erfindet eines) — auf der LF3b-Karte fährt
G die Chart-Form und p die reparierte Laufform.

**EIN Knopf: `MAP_RUN_PIN_KNOTS` = "all"** (der deklarierte
v0.11-Schalter; Zonen-Rides und Brücken werden mitgepinnt),
alles andere der adoptierte v0.13-Stack; Karte = LF3b.
**Vergleichsbasis ist der v0.13-Stack AUF DERSELBEN
LF3b-Karte** (die Zahlen des LF3b-Blocks oben: Netto 5,
missing 1, aiou 0,7484, dtw 0,0573) — karten-gleich, also ohne
Laufform-Ausnahmen. Gates: Netto-Defekte < 5 (echter
Struktur-Gewinn, sonst kein Grund für „all") · `cross_missing`
≤ 1 · aiou-Median-Δ ≥ −0,02 · Marken unverändert · dtw je Wort
±0,003 · reversed 0. Erwartung aus dem v0.14-Sichtbeweis: das
G-Kopf-X wird jetzt hand-gleich geritten UND zählt; scheitert
es erneut, ist die Karten-Form als Ursache widerlegt und der
Riss liegt im Ritt selbst (neuer Befund, eigener Rettungsweg).

**Gemessen `aug19` — verworfen per Gate, und die registrierte
Falsifikation feuert: die Karten-Form ist als Ursache der
„all"-Bruchstelle WIDERLEGT.** Auf der LF3b-Karte gewinnt die
„all"-Stufe erneut Tinte (aiou 0,7484 → 0,7521 · p90 0,1129 →
0,1117 · chamfer 0,0410 → 0,0371 · dtw-Verbesserungen −0,004
bis −0,009 in Galoppieren, mit, mit-2, muß-2, muß-3 — KEIN
dtw-Verlierer; Marken unverändert; reversed 0) — aber die
Struktur kippt WIEDER und WIEDER in Galoppieren: missing 1 → 2
(das G-Kopf-X), spurious 4 → 5, Netto 7 > 5. Dieselbe
Bruchstelle auf der jetzt topologie-sauberen Chart-G-Karte
heißt: nicht die Karten-FORM bricht den G-Kopf, sondern der
RITT im dichten G-Knoten-Komplex unter der „all"-Pinnung.
Rettungswege: (a) **G-Kopf-Ritt-Autopsie unter „all"**
(Instrumentierung wie die will-Autopsie der v0.7-Runde), dann
(b) eine SELEKTIVE Stufe (Brücken und Zonen-Rides getrennt
pinnen — der deklarierte Schalter kennt die Trennung noch
nicht, sie wäre ein neuer, vorzuregistrierender Mechanismus).
Die drei Gewebe-Rest-Duplikate und die soll-geführte
Entdrillung (Positions-Matching auf der jetzt
vertrauenswürdigen Karte) bleiben die stehenden nächsten Arme
(§7.9). §7.9-Zeile aktualisiert im selben PR.

### Lotse G-Kopf-Ritt-Autopsie `aug20` — der Riss ist die parität-blinde Entdrillung, nicht die Pinnung

Einlösung des Rettungswegs (a) der Wiedervorlage oben.
Messanordnung: die LF3b-Kandidaten-Karte deterministisch neu
gebaut (alle Reparatur-t identisch: p 0,578 · F 0,391 · K 0,328 ·
k 0,250 · f 0,477 · b 0,672 · P 0,008; G/h Chart-Fallback),
`pilot_word` mit offengelegter Pinn-Schicht instrumentiert
(Knoten, Läufe, Offsets, Prä-/Post-Entdrillung), Zähl-Matching
mit dem Lineal (`count_crossings`). Reproduktion exakt:
windows matched 8/8 +2 spurious, „all" verliert das G-Kopf-X
(1,60·1,67) und gewinnt das p-Spurious (7,97·0,83).

**Befund 1 — die Pinnung bricht das X nicht, sie macht die
Geometrie sogar sauberer; die Entdrillung frisst es.** VOR der
Entdrillung hat „all" das G-Kopf-X (und sichtbar den saubersten
G-Ritt: die windows-Zickzack-Ausreißer durchs G-Oval fehlen).
Am X-Ort liegen unter „all" 2 Roh-Events (windows: 3, die Hand:
1). Die paarweise Entdrillung (v0.13) entfernt Paare
parität-blind: „all" 2 → 0 (das echte X stirbt mit seinem
Doppel-X-Duplikat), windows überlebt durch Paritäts-GLÜCK
(3 → 1). Post-Entdrillung fehlt das X exakt dann, wenn die
Stufe „all" heißt — der ganze v0.14-Riss ist eine
Entdrillungs-Interaktion.

**Befund 2 — der v0.15-Budget-Fehlschlag ist eine
Soll-Doppelzählung, kein Platzierungs-Problem (an DIESEN
Stellen).** `map_self_intersections` zählt rohe Segment-Schnitte
und liefert jeden Karten-Schnitt ~doppelt (will: roh 10, nach
Lineal-Zählung 4; Galoppieren: 28 gegen 12). wills falsches Veto
(v0.15) kommt exakt daher: Paar-Nachbarschaft 4 Events − 2 <
6 „Soll" → Veto, obwohl das wahre Soll 2 ist. Mit dem **Lineal
selbst als Soll-Quelle** (`crossing_points` auf der xh-skalierten
Karte: Pierce-Filter, Arc-Floor, Merge) löst sich wills Veto
(net 0, Entdrillung läuft), das G-Kopf-Veto feuert korrekt
(„all"+Budget: matched 8/8, missing 0), mits echtes t-Doppel
bleibt konstruktiv geschützt, und die adoptierte windows-Stufe
ist auf allen Prüfworten (unter · mit · will · mit-2 ·
Galoppieren) zähler-identisch — das Budget kostet dort nichts.

**Befund 3 — Zerlegung der „all"-Stufe:** „zones"
((bridge∧forced)∨zone) trägt BEIDES — den G-Kopf-Gewinn UND den
p-Oskulations-Preis (die Zonen-Pinnung zieht die zwei Pässe am
p-Rückgrat von 0,17 auf 0,01 xh zusammen, der Pierce-Zähler
kippt); „bridges" (alle natürlichen Brücken) ist auf allen
Prüfworten struktur-neutral. bridges ∪ zones = all.

**Befund 4 — Fenster 0,8 bleibt tot, jetzt mit Mechanismus:**
Mit Lineal-Budget heilt 0,8 Galoppieren komplett (net 2 → 0,
beide Rest-Gewebe fallen, alle 8 X matched) und schützt mit —
aber unter verliert ALLE drei X (net 1 → 3), und das Budget kann
nicht schützen, weil die Karte unters Kreuzungs-ORTE nicht kennt
(vierte Bestätigung der Platzierungs-Decke). Der Punkt-Abstand
trennt die Klassen nicht (unters Killer-Paare 0,27–0,29 xh gegen
Galoppierens Heiler-Paare 0,17–0,32 xh — überlappend). Kein
Fenster-Arm ohne Platzierungs-Reparatur; §7.9-Zeile (v0.13-0,8)
im selben PR nachgezogen. Artefakte: `temp/tb-aug20/`
(Forensik-Overlays, `galopp-autopsy.json`).

### Lotse v0.16 (L1i) `aug20` — Vorregistrierung: selektive Pinn-Leiter mit Lineal-Soll-Budget (§7.7-Wiedervorlage)

Geschrieben und committet VOR der ersten dev-19-Zahl.
§7.7-Wiedervorlage zweier verworfener Arme, deren Fehlschläge
die Autopsie oben auf EINE Wurzel zieht: v0.14 „all" (2×
verworfen — der Riss war die parität-blinde Entdrillung, nicht
die Pinnung) und v0.15 Soll-Budget (verworfen — die
Doppelzählung der Soll-Quelle, nicht die Budget-Idee).

**Mechanismus:** (1) Die Soll-Quelle des Entdrillungs-Budgets
wird das Lineal selbst — `crossing_points` auf der komponierten
Karte (xh-skaliert) statt roher Segment-Schnitte; die deklarierte
Korrektur des v0.15-Mechanismus. (2) `MAP_RUN_PIN_KNOTS` lernt
die selektiven Stufen **"bridges"** (alle natürlichen Brücken)
und **"zones"** ((bridge∧forced)∨zone); bridges ∪ zones = all —
der Rettungsweg (b) der Wiedervorlage. **EIN wirksamer Knopf:
die Pinn-Stufe;** das Budget ist in allen Sprossen AN.

**Leiter** auf der LF3b-Karte, dev-19, BLAS gepinnt.
**Vergleichsbasis: der v0.13-Stack auf DERSELBEN Karte** (§14
LF3b: Netto 5, missing 1, aiou 0,7484, dtw 0,0573) — zusätzlich
Identitäts-Check der neu gebauten Karte gegen die
`aug19`-Kandidaten-Rows. Sprossen: **0** windows+Budget
(Erwartung: zähler-identisch — jede Regression tötet das Budget
und beendet die Leiter) · **A** bridges+Budget · **B**
zones+Budget · **C** all+Budget.

**Gates je Sprosse:** Netto-Defekte ≤ 5 · `cross_missing` ≤ 1 ·
Marken unverändert · reversed 0 · dtw je Wort ±0,003 ·
aiou-Median-Δ ≥ 0. **Adoption: die höchste Sprosse, die alle
Gates hält;** unter gleichwertigen entscheidet mehr Tinte
(aiou), dann weniger Pinnung. Ehrliche Erwartung aus der
Autopsie: B/C retten das G-Kopf-X (missing → 0), zahlen aber die
p-Oskulation (+1 Spurious, voraussichtlich Netto 6 → Negativ);
**A ist die Kandidaten-Sprosse** für einen reinen Tinten-Gewinn
ohne Struktur-Preis. Vorregistrierte Falsifikation: hält auch A
kein Gate, ist die Pinn-Familie auf dieser Karte erschöpft und
jeder weitere Weg führt über die p-Platzierung (K1-Arm,
tintenfolger.md §7.9). Wordbench ist unberührt (reine
Kandidaten-Schicht, kein `core/`-Anfassen).

**Gemessen `aug20` — Sprosse A (bridges+Budget) ADOPTIERT; die
Zonen-Sprossen scheitern exakt an der vorhergesagten
p-Oskulation, aber das Budget rettet das G-Kopf-X auf dev-19.**
Identitäts-Check: die neu gebaute LF3b-Karte reproduziert die
`aug19`-Kandidaten-Rows STROKE-GLEICH, die Identitäts-Sprosse
und Sprosse 0 (windows+Budget) sind zähler- und zahlengleich mit
der Basis — die Messkette steht, und das Budget ist auf der
windows-Stufe gratis. **Sprosse A:** Struktur an JEDER Stelle
identisch zur Basis (Netto 5, missing 1, Marken unverändert,
reversed 0, Ortsfehler 0,069 =), dazu reine Gewinne: p90 0,1129
→ **0,1122** · chamfer 0,0410 → **0,0404** · dtw-Mittel 0,0660 →
0,0651 · aiou-Mittel 0,7199 → 0,7216 · vier Wörter gewinnen dtw
−0,0035 bis −0,0059 (muß-2, Galoppieren, mit, muß-3) und aiou
bis +0,0117 — **kein einziges Wort verliert** (schlechteste
dtw-Änderung ±0,0000, keine aiou-Verluste), mits Retrace-Zone
heilt (`retrace_missing` 1 → 0). Ehrliche Protokoll-Notiz: das
Gate „dtw je Wort ±0,003" war ZWEISEITIG formuliert und wird
ausschließlich auf der GEWINN-Seite durchbrochen; es wird nach
seinem dokumentierten Schutzzweck (kein Wort VERLIERT > 0,003)
gelesen, künftige Pre-Regs formulieren es einseitig.
Tie-Break r0/A („mehr Tinte"): aiou-Median gleich, je Wort aber
4 Gewinne / 0 Verluste → A. **Sprossen B/C: verworfen per Gate**
(Netto 6 > 5 — genau der eine Galoppieren-p-Oskulations-Spurious
(7,97·0,83), die Zonen-Pinnung zieht die zwei Pässe von 0,17 auf
0,01 xh zusammen und der Pierce-Zähler kippt); die Kern-These
der Autopsie bestätigt sich auf dev-19: **das G-Kopf-X überlebt
unter Budget in BEIDEN Zonen-Sprossen** (Galoppieren missing
0 → 0 statt v0.14s 0 → 1). C trägt die stärksten Tinten-Werte
der Route (chamfer 0,0371, p90 0,1117, aiou-Median +0,0038,
mit-2 dtw −0,0090/aiou +0,0321), zahlt aber zusätzlich zwei
kleine dtw-Preise (Wer +0,0018, die +0,0017). Rettungsweg der
Zonen-Stufe: NACH der p-Platzierungs-Reparatur (K1-Arm)
wiedervorlegen — der einzige Struktur-Preis gehört der
Platzierungs-Familie, nicht dem Ritt. Neuer adoptierter Stack:
`MAP_RUN_PIN_KNOTS = "bridges"` + `UNTWIST_SOLL_BUDGET = True`
(Lineal-Soll). Artefakte: `temp/tb-aug20/lotse-v16-*`.

### Lotse Karten-Soll-Autopsie `aug20` — die „Platzierungs-Decke" ist präziser eine SOLL-VOLLSTÄNDIGKEITS-Lücke

Fortsetzung der Morgen-Autopsie, Anlass: der als Schlüssel
benannte „K1-p-Platzierungs-Arm". Drei Messungen korrigieren die
These:

**(1) Die Karte kennt die ORTE.** Die Platzierungskarte über
dev-19 (Lineal-Soll der komponierten LF3b-Karte gegen die
Hand-Kreuzungen, eins-zu-eins am 0,55-Matcher): **40 von 41
Hand-X gematcht (98 %), Ortsfehler median 0,150 xh, p90 0,242.**
Karten-blind ist genau EIN X: das ZWEITE X von unters
t-Stamm-Doppel (4,98 · 0,37, direkt am t-Exit) — die Hand kreuzt
den t-Stamm mit Abstieg UND 0,07-xh-versetztem Rückpass (der
K1b-Befund „zwei Kreuzungs-Orte, einzeln gezählt"), die
komponierte Karte führt EINE Balken-Stamm-Kreuzung. Auch die p-Höhen-These des
Vorabends fällt: Chart-p und LF3b-p kreuzen bei v = −0,01, das
komponierte Galoppieren-Soll bei v ≈ 0,00 gegen Hand 0,10/0,17
(0,2 xh) — die „X bei v 0,85" der Morgen-Notiz waren Artefakte
der rohen Doppelzähl-Enumeration (Beinahe-Berührungen, die der
Lineal-Detektor verwirft). Die p-Oskulation der Zonen-Stufe ist
damit eine Karten-BEINAHE-BERÜHRUNG (Soll: keine Kreuzung), die
die Zonen-Pinnung zur falschen Kreuzung zusammenpresst — kein
Platzierungsfehler.

**(2) Der 0,8-Kill bei unter war die STUMPFE ZÄHLUNG — aber auch
die Positions-Delta-Zählung fällt (Commons-Problem).** unters
t-Region trägt 12 Ritt-Events über 1 Soll; ein Veto, das je Paar
die Match-Zahl vorher/nachher vergleicht, findet für JEDE
einzelne Entfernung einen Ersatz-Matcher — die Kaskade räumt die
Stelle trotzdem leer (matched 2 → … → 0, Event-Dump im
Autopsie-Protokoll). Die tragfähige Semantik ist die
**RESERVIERUNG**: das Lineal-Soll wird einmal pro Pass
eins-zu-eins auf die Events gematcht, reservierte Events sind
unpaarbar („die Karte kennt diese Kreuzung — sie ist
unantastbar"; Unit-Test mit der nachgestellten unter-Klasse).

**(3) Das 0,8-Fenster bleibt AUCH mit Reservierung tot — am
dritten Glied derselben Kette.** Proben @0,8+Reservierung:
Galoppieren heilt komplett (Netto 2 → 0, beide Rest-Gewebe),
mit/will/mit-2 stabil, unter rettet ein X zurück (3 → 2 missing
— besser als die Zählung), verliert aber weiter das ungedeckte
zweite t-Stamm-X: die Hand kreuzt dort ZWEIMAL, die Karte kennt
EINE Kreuzung — Reservierung kann nur schützen, was das Soll
führt. Der gemeinsame Nenner ALLER Rest-Blocker
(Zonen-p-Oskulation · 0,8-unter · unters t-Stamm-Doppel) ist die
**Karten-Soll-VOLLSTÄNDIGKEIT an Join- und Rückpass-Schleifen**
(der aug15-Composer-Befund „Hand 34 > Komposition 25": die
generierten Joins und Rückpässe unter-kreuzen, wo die echte Hand
schleift — t-Stamm-Doppel, e-Einläufe, ß) — ein COMPOSER-Arm mit
wordbench-Gates, kein Ritt-Arm.

### Lotse v0.17 (L1j) `aug20` — Vorregistrierung: das Reservierungs-Veto

Geschrieben und committet VOR der ersten dev-19-Zahl. Einlösung
des stehenden §7.9-Rettungswegs („Positions- statt
Zähl-Matching"), Mechanismus per Autopsie oben: **EIN Knopf,
`UNTWIST_SOLL_MATCHING` = "reserve"** — das Entdrillungs-Veto
wird von der Radius-Zählung auf die Soll-Reservierung
umgestellt; Fenster bleibt 0,5, Stack sonst der adoptierte
v0.16. Gemessen auf dev-19, LF3b-Karte UND gefrorener Root,
BLAS gepinnt; Basen = die v0.16-Läufe (`aug20`).

**Gates:** kein Wort verliert irgendeinen Zähler (cross/marks/
retrace je Wort ≥ Basis-Stand) · kein Wort verliert mehr als
0,003 dtw (einseitig, die v0.16-Protokoll-Lektion) ·
aiou-Median-Δ ≥ 0 · reversed 0. **Adoptions-Regel (vorab
deklariert): Adoption AUCH bei reiner Zähler-Parität**, weil die
Reservierung die deklarierte Budget-Semantik KONSTRUKTIV erfüllt
(ein soll-gematchtes Event kann bauartbedingt nie fallen),
die die Radius-Zählung nur approximiert — der Unit-Test pinnt
die Klasse, die Proben zeigen Parität mit weniger Spiegelungen
(Galoppieren 15 → 11). Ehrliche Erwartung: Zähler-Parität,
leichte Geometrie-Schonung; jede Regression tötet den Arm.

**Gemessen `aug20` — ADOPTIERT per Paritäts-Regel.** Auf beiden
Roots (LF3b-Karte und gefrorener Root) ist die
Reservierungs-Sprosse **zähler-identisch je Wort** (kein Zähler
bewegt sich, keine dtw-Bewegung > 0,0015, aiou-Median-Δ +0,0000,
reversed 0 — alle Gates PASS; LF3b: Netto 5, dtw 0,0573,
p90 0,1122; frozen: Netto 6, dtw 0,0585). Der neue Default:
`UNTWIST_SOLL_MATCHING = "reserve"` — das Budget-Veto erfüllt
seine Semantik jetzt konstruktiv statt approximativ; die
Schutzklasse (Radius-Zählung tötet ein soll-gedecktes Paar unter
Event-Inflation) ist im Unit-Test gepinnt. Der nächste benannte
Hebel bleibt der Karten-Soll-Vollständigkeits-Arm (Composer,
Join- und Rückpass-Schleifen — Autopsie oben); dahinter warten 0,8-Fenster und
Zonen-Stufe als Wiedervorlagen. Artefakte:
`temp/tb-aug20/lotse-v17-*`.

### Lotse t-Stamm-Ritt-Autopsie `aug20` — die „Vollständigkeits-Lücke" ist eine AUFLÖSUNGS-Grenze

Fortsetzung am Nachmittag; die Kette der Korrekturen wird eine
Stufe tiefer einheitlich. Drei Messungen:

**(1) Die KOMPOSITION führt das t-Stamm-Doppel — überall.** Auf
den rohen Kompositions-Centerlines zählt das Lineal an unters t
ZWEI Soll-X ((4,72·0,28)+(4,78·0,30), 0,06 xh auseinander;
Bar × Abstieg und Bar × Rückpass-Brücke) — und die
Platzierungskarte auf ROHER Karte matcht **41 von 41** Hand-X
(Ortsfehler median 0,159 xh). Die „Soll-Vollständigkeits-Lücke"
des Vormittags war KEINE Kompositions-Lücke: das 0,12-xh-
Resampling der Soll-Quelle kollabiert das 0,06-Doppel zu einem
Punkt (40/41). Ein Zwischen-Mechanismus „Soll-Quelle = rohe
Karte" wurde gebaut und an den Proben gemessen: WIRKUNGSLOS
(unter@0,8 unverändert) — er behebt nur das Soll-Symptom,
nicht die Wurzel; verworfen vor jeder dev-Zahl, nicht
eingecheckt.

**(2) Die Wurzel: `SAMPLE_STEP_UNITS` = 0,12 ist gröber als die
feinste zählbare PUNKT-Struktur.** Der Schritt wurde am
ARC-Floor der Zähler (0,35 xh) bemessen — aber ein X-PAAR mit
0,06 xh Punkt-Abstand kann auf einer 0,12-xh-Polyline nicht
existieren: die RITT-BAHN selbst entsteht aus diesen Samples.
Der t-Ritt (Bild `temp/tb-aug20/t-stem-ride.png`): der gesamte
Fuß-Brücke-Balken-Komplex ist eine natürliche Brücke (board
None), die gepinnte Karte trägt beide X — die 0,12er-Abtastung
verschmilzt sie; unters missing 1 („letzter Ritt-Rest") ist
exakt dieses zweite t-X.

**(3) Der Ein-Wort-Beweis (halber Schritt, 0,06):** unter
matched 3/3 — **der letzte missing des Dev-Satzes heilt**;
Galoppieren spurious 2 → 1 (ein Rest-Gewebe verschwindet mit);
mit stabil; Laufzeit +8 % (2,2 → 2,3 s bzw. 13,0 → 14,1 s).

### Lotse v0.18 (L1k) `aug20` — Vorregistrierung: die Auflösungs-Leiter

Geschrieben und committet VOR der ersten dev-19-Zahl. **EIN
Knopf: `SAMPLE_STEP_UNITS`, Leiter {0,06 · 0,04}** (0,12 =
Basis-Stand v0.17), alles andere der adoptierte Stack. Gemessen
auf dev-19, LF3b-Karte UND gefrorener Root, BLAS gepinnt;
Basen = die v0.17-Läufe.

**Gates je Sprosse:** Netto ≤ Basis (LF3b 5 · frozen 6) ·
`cross_missing` ≤ Basis (1) · Marken unverändert · reversed 0 ·
kein Wort verliert mehr als 0,003 dtw (einseitig) ·
aiou-Median-Δ ≥ 0 · Laufzeit-Report (kein Gate, aber
dokumentiert). **Adoption: die Sprosse mit dem besten Netto;
bei Gleichstand die GRÖBERE** (Laufzeit). Ehrliche Erwartung
aus den Proben: 0,06 heilt unters missing und ein
Galoppieren-Gewebe (Netto-Erwartung LF3b 5 → 3); 0,04 ist die
Kontroll-Sprosse gegen Auflösungs-Fischerei — gewinnt sie
NICHT weiter, ist 0,06 der Punkt, an dem die Struktur
auskonvergiert.

**Gemessen `aug20` — BEIDE Sprossen verworfen per Gate; die
Auflösungs-These bestätigt sich, aber der Schritt ist kein
freier Knopf.** Die Kreuzungs-Struktur liefert exakt die
Erwartung: 0,06 → **Netto 3** (LF3b; frozen 6 → 3), unters
missing heilt (der letzte des Dev-Satzes), Galoppieren verliert
ein Gewebe — die stärkste Netto-Zahl der Route. Aber die
GEOMETRIE zahlt flächig: dtw-Verlierer weit über dem Gate
(muß-2 +0,0352 · muß-3 +0,0156 · mit +0,0142 · Galoppieren
+0,0087), aiou-Median −0,0044, p90 0,1122 → 0,1153, und NEUE
Retrace-Defekte (Galoppieren `retrace_missing`/`spurious`
0 → 2/2, laden +1). 0,04 verschärft alles (aiou-Median −0,0274,
will verliert sogar ein X) — die Kontroll-Sprosse feuert: das
ist ÖKONOMIE-Drift, keine Konvergenz. Befund: die
Ritt-Ökonomie ist SAMPLE-DENOMINIERT — `RIDE_DOUBLE_MIN_GAP`
ist in Samples definiert (4 Samples = 0,48 xh bei 0,12, nur
0,24 bei 0,06), und `BRIDGE_EMIT_FACTOR` bepreist Brücken PRO
SAMPLE (gleiche Brücken-LÄNGE kostet bei halbem Schritt das
Doppelte → der Viterbi meidet Brücken, klebt an Schienen, die
muß-Familie kippt). Rettungswege: (a) **feine Emission** —
Entscheidungs- und AUSGABE-Auflösung trennen: der Ritt
entscheidet auf 0,12, gepinnte Strecken emittieren die ROHE
Karte plus Offset-Feld. **Noch am selben Nachmittag gebaut und
an den Proben VERWORFEN:** die rohe Karten-Geometrie trägt
Kompositions-MIKROSTRUKTUR (Nahtstellen, Mini-Gewebe), die die
0,12-Glättung bisher stillschweigend versteckt hat — Galoppieren
explodiert auf 32 Spurious, mit +3, und unters t-X2 erscheint
trotzdem nicht; Code zurückgebaut, nie dev-gemessen. Der
stehende Weg ist damit (b): **schritt-invariante Reskalierung**
der sample-denominierten Ökonomie (`RIDE_DOUBLE_MIN_GAP` in xh
statt Samples, Brücken-Preis pro ARC statt pro Sample), dann die
Auflösungs-Leiter wiedervorlegen — eigene Pre-Reg. Nebenbefund
fürs Protokoll: dieselbe Glättung, die die Mikrostruktur
versteckt, ist auch der Grund, warum die Karte als
RITT-GRUNDLAGE funktioniert — Auflösung ist beim Lotse kein
freies Gut, sondern Teil des Filters. §7.9-Zeile im selben PR.
Artefakte: `temp/tb-aug20/lotse-v18-*`.

### Lotse v0.19 (L1l) `aug20` — Vorregistrierung: die schritt-invariante Ökonomie + Wiedervorlage der Auflösungs-Leiter

Geschrieben und committet VOR der ersten dev-19-Zahl.
§7.7-Wiedervorlage der v0.18-Leiter mit dem im Negativ benannten
Mechanismus. Die Kostenmodell-Lektüre präzisiert die
v0.18-Diagnose: Emissionen (Schienen-Abweichung UND
Brückenpreis) zählen PRO SAMPLE, Transitionen (Ritt) pro BOGEN —
bei halbem Schritt verdoppeln sich die Emissions-Summen relativ
zu den Ritt-Kosten (Schienen werden relativ billiger: das
gemessene „klebt an Schienen"); dazu sind `MAX_RIDE_FACTOR`
(8 × Schritt: die Ritt-Reichweite halbiert sich) und
`RIDE_DOUBLE_MIN_GAP` (4 Samples: die Doppel-Uhr wird
schärfer) explizit schritt-denominiert.

**Mechanismus (die deklarierte Re-Denominierung, bei 0,12
byte-neutral):** (1) Emissions-Skala `SAMPLE_STEP_UNITS / 0,12`
auf beide Emissions-Terme — die Pfad-Summen werden
schritt-invariant, bei 0,12 exakt 1; (2) `MAX_RIDE_UNITS` =
0,96 xh (= 8 × 0,12) statt des Schritt-Faktors; (3)
`RIDE_DOUBLE_MIN_GAP_UNITS` = 0,48 xh (= 4 × 0,12), zur
Laufzeit in Samples gerundet. **EIN wirksamer Knopf bleibt der
Schritt.** Leiter auf beiden Roots: **Sprosse 0** = 0,12 mit
Re-Denominierung — MUSS byte-identische Kandidaten-Rows zu
v0.17 liefern (harter Identitäts-Check des Refactors; jede
Abweichung tötet den Arm) · **A** = 0,06 · **B** = 0,04.

**Gates je Sprosse (wie v0.18):** Netto ≤ Basis (LF3b 5 ·
frozen 6) · `cross_missing` ≤ 1 · Marken unverändert ·
reversed 0 · kein Wort verliert mehr als 0,003 dtw (einseitig)
· aiou-Median-Δ ≥ 0 · Laufzeit-Report. **Adoption: die Sprosse
mit dem besten Netto, bei Gleichstand die gröbere.** Ehrliche
Erwartung: die v0.18-Struktur-Ernte (Netto → 3) OHNE den
Ökonomie-Drift; scheitert die Geometrie erneut, liegt eine
weitere, noch unbenannte Schritt-Abhängigkeit vor (eigene
Autopsie, kein Knopf-Nachdrehen).

**Gemessen `aug20` — Sprosse 0 byte-identisch (die
Re-Denominierung BLEIBT als bewiesen neutrale Grundlage);
die Leiter-Sprossen erneut verworfen, und die vorregistrierte
Falsifikation benennt die letzte Kopplung.** Sprosse 0
reproduziert die v0.17-Kandidaten-Rows auf BEIDEN Roots
stroke-für-stroke — der Refactor ist am Betriebspunkt exakt
neutral und macht künftige Schritt-Arme erst sauber messbar;
`MAX_RIDE_UNITS` = 0,96 · `RIDE_DOUBLE_MIN_GAP_UNITS` = 0,48 ·
Emissions-Skala `Schritt/0,12` sind der neue Stand. **A (0,06):
verworfen** — unters missing heilt weiter (LF3b-Netto bleibt
aber 5, weil Galoppieren jetzt einen Spurious GEWINNT statt
eines Gewebes zu verlieren), und der Geometrie-Drift ist nicht
beseitigt, nur umverteilt (Wer +0,0309, muß-2 +0,0221, mit
+0,0101; neue Retrace-Defekte; frozen-aiou-Median −0,0049).
**B (0,04): klar schlechter** (Netto steigt beidseitig,
aiou-Median −0,024/−0,030). Befund: die verbleibende
Schritt-Abhängigkeit ist die EMISSIONS-FEINHEIT selbst —
feinere Brücken-/Zonen-Strecken emittieren die
Karten-MIKROSTRUKTUR mit (die abgeschwächte Form des
fine-emission-Befunds: dieselbe Feinheit, die das t-Doppel
trägt, trägt die Kompositions-Wiggle). Struktur-Gewinn und
Geometrie-Verlust sind über die Auflösung GEKOPPELT; 0,12
bleibt der Betriebspunkt, unters t-X2 die dokumentierte
Auflösungs-Grenze. Rettungsweg: **Karten-Glättung auf
Zähler-Skala VOR der Feinabtastung** (eine Glättung ENTLANG der
Bahn erhält Pass-Versätze wie das 0,06-t-Doppel, frisst aber
Intra-Pass-Wiggle) — eigene Pre-Reg; §7.9-Zeile im selben PR.
Artefakte: `temp/tb-aug20/lotse-v19-*`.

**Nachtrag `aug20` nacht — die Glättungs-Proben schließen die
Auflösungs-Familie.** Der Glätter wurde gebaut
(`smooth_map_strokes`: 0,02-xh-Grid, Box-Fenster entlang der
Bahn, Endpunkte exakt; `MAP_SMOOTH_WINDOW_UNITS`, deklariert-off)
und mit vollem Lineal an fünf Proben-Worten gemessen (unter ·
Galoppieren · mit · Wer · muß-2; Fenster {0,06 · 0,12} ×
Schritt {0,06 · 0,12}): **Der Feinschritt-Drift besteht auf
geglätteter Karte UNVERÄNDERT fort** (Wer +0,0331, muß-2
+0,0219, mit +0,0126 — Fensterbreite ohne Einfluss; Galoppieren
sogar mit neuen Retrace-Defekten). Damit ist die dritte und
letzte Kopplung benannt: nicht Ökonomie (v0.19 ✓ invariant),
nicht Emission, nicht Karten-Geometrie — die
**ENTSCHEIDUNGS-GRANULARITÄT des Viterbi selbst** (mehr Samples
= mehr Umsteigepunkte = andere Pfade). Die Auflösungs-Familie
ist vollständig ausgemessen und GESCHLOSSEN; 0,12 ist der
Betriebspunkt, unters zweites t-Stamm-X die bleibende
Auflösungs-Grenze (kein weiterer Leiter-Anlauf ohne
grundsätzlich anderen Solver). Nebenbefund als NEUER, eigener
Kandidat: die Glättung AM Betriebspunkt (Fenster 0,06 · Schritt
0,12) zeigt gemischte, teils große Effekte — mit aiou +0,0967
und dtw −0,0275, muß-2 heilt beide Retrace-Defekte, unters
t-X2 erscheint; aber Wer +0,0309 dtw und Galoppieren tauscht
ein X ein. Falls aufgegriffen: eigene Pre-Reg als
Betriebspunkt-Arm mit Fenster-Leiter, kein Anhängsel der
Auflösungs-Familie. Der Glätter bleibt deklariert-off im Code.
Artefakte: `temp/tb-aug20/probe-v20-*`.

**Zweiter Nachtrag `aug20` nacht — auch der Betriebspunkt-
Kandidat ist an den Proben verworfen.** Die Fenster-Feinleiter
{0,02 · 0,03 · 0,04 · 0,06} bei Schritt 0,12 (fünf Proben-Worte,
volles Lineal) zeigt: (1) die Fenster unter 0,06 sind
KERNEL-QUANTISIERT identisch (alle drei → dieselbe 3-Punkte-Box
auf dem 0,02-Grid, im Folgenden „Kernel-3"); (2) **kein Fenster
ist ohne Verlierer** — Kernel-3
gewinnt Wer (dtw −0,0035/aiou +0,0251) und unter (das t-X2
erscheint), zahlt aber bei Galoppieren (+0,0065 dtw, Spurious
+1, neue Retrace-Defekte) und mit (aiou −0,0158); Fenster 0,06
gewinnt mit (aiou +0,0967), kippt Wer (+0,0309). Die Effekte
springen nichtlinear und gegenläufig zwischen den Sprossen —
das sind ENTSCHEIDUNGS-KIPP-PUNKTE des Viterbi (jede
Karten-Störung verschiebt Board-Entscheidungen chaotisch),
keine systematische Verbesserung; wort-weise Optima wären
Fischerei. Gesamtbefund des Tages damit geschlossen: **die
Route sitzt am Betriebspunkt in einem empfindlichen Optimum —
Karten- und Abtastungs-Manipulationen sind als Familie
erschöpft.** Die verbliebenen Lotse-Wege führen über andere
Schichten (Zonen-Stufe nach p-Oskulations-Mechanik, anderer
Solver); die nächsten Mess-Arme der Kampagne liegen auf der
KETTE (K0-zonale Rückweisung, §7.9) und bei InkSight.
Artefakte: `temp/tb-aug20/probe-v20-w0*`.

### Kette K0-Z `aug20` — Vorregistrierung: die zonale Rückweisung

Geschrieben und committet VOR der ersten Zahl. Einlösung des
stehenden §7.9-Rettungswegs der K0-Wächter-Zeile: Das
aug19-Protokoll bewies die RUNDEN-ATOMARE Rückweisung als Decke —
unters gebündelte Soll-Reparatur (overlap 3 → 2 erlaubt UND
touch 3 → 6 verboten, beides in EINEM Solve) wird als Ganzes
verworfen, die Struktur friert (107 = 107).

**Mechanismus.** Nach den bestehenden Halbierungs-Retries
(`STRUCTURE_GUARD_MAX_RETRIES`), VOR dem Voll-Revert: (1) Die
Klassen-PUNKTE des Kandidaten und der Vorrunden-Geometrie werden
durch DASSELBE Assemblat und DIESELBEN Zähler bestimmt wie Budget
und Soll (`crossing_points`-Positionen, `structure_zones`-Mids —
keine Zweitimplementierung); Verletzungs-Orte sind je verletzter
Klasse die per Eins-zu-eins-Matching (0,55-Lineal-Radius)
überzähligen Kandidaten-Events bzw. verlorenen Vorrunden-Events.
(2) Alle freien Anker im ZONEN-Radius um einen Verletzungs-Ort
werden auf die Vorrunden-Geometrie gepinnt (Delta-Bounds (0,0)).
(3) EIN Nach-Solve mit den Original-Bounds der Runde für die
übrigen Anker; hält das Budget, ist die Runde ANGENOMMEN — sonst
Voll-Revert wie bisher. **EIN Knopf:**
`structure_guard_zone_units`, Leiter {0,55 · 1,0}; 0 = heutiges
Verhalten (Identitäts-Erwartung: byte-gleiche Kandidaten).

**Messanordnung.** 63 Wörter (`--all`), Stack
`--structure-guard-soll` + Zone, BLAS gepinnt; **Basis = der
aug19-K0-soll-Lauf** (`temp/tb-aug19/k0-soll-cand.json`;
`follow.py` seit #387 unverändert, zusätzlich der
Zone-0-Identitäts-Check). Bewertung nach dem k0-Protokoll
(referenzfrei: Soll-Abstand = |cross − Kompositions-Soll| +
|retrace − Zonen-Soll| je Wort; aiou gegen die Tinte) plus
dev-19-Referenzbench.

**Gates:** Gesamt-Soll-Abstand sinkt IRGENDWO strikt und steigt
je Wort NIRGENDS · aiou je Wort ≥ −0,003 · dev-19: kein Wort
verliert mehr als 0,003 dtw (einseitig), Marken unverändert,
reversed 0, Netto-Kreuzungsdefekte ≤ Basis · Laufzeit-Report.
**Adoption: die Sprosse mit dem besten Gesamt-Soll-Abstand, die
alle Gates hält; Gleichstand → kleinerer Radius.** Ehrliche
Erwartung: unters Bündel-Fall überlebt zonal (die touch-Zone
friert, die overlap-Reparatur bleibt); benanntes Risiko: die
Pinn-NÄHTE (Grenze gepinnt/frei) können eigene Artefakte formen
— genau dafür stehen die je-Wort-Gates.

**Gemessen `aug20` nacht — beide Sprossen verworfen per Gate,
an ZWEI knappen Rissen gegen den größten Tinten-Gewinn der
Ketten-Geschichte; die Konversion ist präzise benannt.**
Identität: Zone 0 reproduziert den aug19-K0-soll-Lauf
BYTE-GLEICH (Messkette validiert). **Die Substanz:** Zone 1,0
rettet 59 von 79 bisher rundenatomar verworfenen Runden
(0,55: 53/77), Gesamt-Soll-Abstand 107 → **102** (5 besser ·
1 schlechter), und die geretteten Runden tragen die
Tinten-Verfeinerung, die die atomare Rückweisung mit
verwarf: **aiou +0,05 bis +0,154 über das halbe Set**
(Gewehr +0,154 · an +0,115 · Kugel +0,112 · Wer +0,100 ·
muß +0,097; Median +0,0030), dev-19 VOLLSTÄNDIG grün
(schlechtester dtw-Verlust +0,0008, Netto 21 → 20, dtw-Median
0,0494 → **0,0472** — Bestwert der Route, Marken unverändert,
reversed 0). **Die zwei Gate-Risse:** (a) daß Soll-Dist 2 → 3 —
die INTERVALL-RÜCKWÄRTS-Klasse: das Akzeptanz-Intervall
[min(Budget,Soll), max] ist über die Runden STATISCH, eine
akzeptierte Runde darf eine Klasse legal vom bereits erreichten
Stand ZURÜCK Richtung Budget tragen (retrace 1 → 2 im Intervall
[1,2]); (b) „ein" aiou −0,0049 (einziger Verlierer, knapp über
der 0,003-Schwelle). Protokoll-Notiz: die Erstauswertung las
die Follow-Registrierung fälschlich unter `measurements`
(top-level ist richtig — das dokumentierte aug19-Gotcha) und
verwusch die aiou-Deltas; korrigiert vor jeder Entscheidung.
Konversion: **K0-Z-R, das Ratschen-Budget** (unten).

### Kette K0-Z-R `aug20` — Vorregistrierung: das Ratschen-Budget

Geschrieben und committet VOR der ersten Zahl. Der benannte
Fix der Intervall-Rückwärts-Klasse: **nach jeder AKZEPTIERTEN
Runde wird das Budget auf deren Klassen-Stände gesetzt** — das
Intervall der Folgerunde ist [min(Stand, Soll), max(Stand,
Soll)], Bewegung geht nur noch WEITER Richtung Soll, nie
zurück (die daß-Klasse stirbt konstruktiv). **EIN Knopf:**
`structure_guard_ratchet` (bool, nur mit Soll-Guard sinnvoll);
Leiter: Ratsche+Zone {0 · 0,55 · 1,0} — Sprosse 0 isoliert die
Ratsche auf dem heutigen atomaren Guard. Messanordnung und
Gates unverändert K0-Z (Basis bleibt der aug19-K0-soll-Lauf).
Ehrliche Erwartung: Zone-1,0+Ratsche hält das daß-Gate; das
„ein"-aiou-Gate (−0,0049) entscheidet über Adoption — es wird
NICHT aufgeweicht.

**Gemessen `aug20` nacht — verworfen per Gate; die
daß-Autopsie findet die Wurzel eine Ebene tiefer: ZWEI
SOLL-QUELLEN divergieren.** Die Ratsche allein (Zone 0) ist
exakt neutral (107 = 107 — der atomare Guard bewegte sich nie
rückwärts). **Ratsche+0,55 ist die stärkste Sprosse der
Ketten-Geschichte: Gesamt-Soll-Abstand 107 → 99** (7 besser ·
1 schlechter), **NULL aiou-Verlierer** (min −0,0017, „ein"
dreht auf +0,0118), Tinten-Gewinne bis +0,131 — und reißt
trotzdem zwei Gates: daß bleibt 2 → 3, und dev-19 zeigt zwei
+0,0142 dtw (bei aiou +0,0920 ebendort — der Tinte-gegen-
Bahn-Trade) plus unter `retrace_missing` 1 → 2. Ratsche+1,0:
dev-19 vollständig grün, aber 63er-Risse (daß · „ein"
−0,0049). **Die daß-Runden-Records klären den hartnäckigen
Riss:** Die zonal gerettete Runde ist gegen das GUARD-Soll
völlig legal (retrace → 2; `structure_zones` zählt am
komponierten daß-Init 2 Retrace-Zonen), aber die
k0-METRIK rechnet mit `ductus_soll` comp.zones = **1** —
zwei Pipelines, dieselbe Komposition, verschiedene
Zonen-Zahl. Der Guard tut, was sein Soll sagt; die Metrik
bestraft es. Das ist DASSELBE „zwei Lineale"-Muster, das am
Morgen die Lotse-Soll-Quelle kostete. Rettungswege: (1)
**Soll-Quellen-Autopsie** (welche der beiden Zählungen der
daß-Komposition ist die richtige — Assembly-Detail oder
Detektor-Floor?), dann die Wiedervorlage mit VEREINHEITLICHTER
Quelle (Budget, Guard-Soll, Runden-Counts und Metrik durch
EINE Pipeline); (2) der zwei-dtw-Trade als eigene Frage
(+0,0142 Bahn gegen +0,0920 Tinte — ggf. ein Fall für den
humanbench-Tie-Breaker, §7.9 Methodik-Zeile). Implementierung
bleibt deklariert-off (`zone 0` byte-identisch bewiesen,
Ratsche default False). Artefakte: `temp/tb-aug20/k0z*`.

### Kette K-C `aug20` — Vorregistrierung: die Tinten-Evidenz-Maske (Autor-Fund „Flecken")

Geschrieben und committet VOR der ersten Zahl. **Anlass:** der
Autor sah sich am Abend die K0-Z-R-Augenschein-Seite (Hand ·
Kette-Basis · Ratsche 0,55/1,0, 19 Dev-Wörter) an und meldete
vier Stellen: zwei (w-Fuß: „riesiger Ausschlag weit weg von der
Tinte", w-Eck oben Richtung Papier — „sind Flecken
verantwortlich?"), die-2 (Kreuzung: „Punkte werden zum i-Punkt
gezogen"), Galoppieren (i-Punkt-Ausreißer Richtung Fleck),
unter (e→r „total falsch"). Hypothese des Autors: Fremdtinte
zieht den Folger an → eine Maske/„weiße Zone" um die Schrift,
außerhalb derer nichts mehr zieht.

**Autopsie (aug20 spät, vier Wort-Agenten + Code-Karte,
Skripte/Bilder im Scratchpad `flecken/`): drei von vier
bestätigt, die vierte ist ein anderer Fund.** (a) zwei w-Fuß
= GLOBALES Maximum (0,374 xh Kette / 0,480 Ratsche; 45 bzw.
107 absorbierte Kandidatenpunkte): eine Nadel 19/29 px
senkrecht ins Papier, Spitze 0,084/0,044 xh von Komponente C4
(36 px, Grau 171–210, nie so dunkel wie Tinte); der komponierte
Seed kreuzt die Grundlinie nirgends — der Fit erzeugt die
Nadel; Prox-Kosten MIT Fleck im Feld 2,9× (Kette) / 9,8×
(Ratsche) billiger als ohne; 6 der 300 Coverage-Ziele gehören
C4. w-Eck: zweite Nadel 9 px aufwärts, Spitze 0,085 xh von C2
(27 px). (b) die-2: V-Nadel aus der d-Schleife, Spitze
0,051 xh von der i-Punkt-MASKE, Achse 3,2° parallel zum
Punkt-Strich, ohne den Punkt im Feld 4,2× teurer — der Magnet
ist die EIGENE Marke, kein Papierfleck (die fremde Komponente
des Crops, 41 px, bewegt 0,00 px). (c) Galoppieren: kein
Fleck, **Durchschein der Rückseite** — sechs Fragmente (26–44
px, Grau 0,75–0,81 gegen 0,40 Tinte) überleben Schwelle und
24-px-Despeckle; DREI von vier Exkursionen > 0,25 xh enden auf
einem Fragment (0,02 / 0,05 / 0,12 xh; kontrafaktische EDT ohne
Fremdtinte: +0,83 / +0,52 / +0,42 xh), die vierte (p→p-Naht)
ist ketteneigen (Δ 0,00). EIN Punkt des i-Punkt-Strichs springt
auf Fragment #2 → Strichbogen 0,53 → 1,82 xh > 0,8 → als KÖRPER
klassifiziert (marks_missing 1) und 75 % des dtw (0,2329 →
0,0573 ohne diese Paare). (d) **unter: KEINE Fremdtinte** (genau
2 Komponenten: Körper + u-Bogen), die Bahn verlässt die
Tinte nie um > 0,19 xh — sie liegt auf der FALSCHEN Tinte: das
komponierte e ist 1,32 xh breit, das der Hand 0,65 xh; der
Seed-Fehler am e-Ausgang (0,81 xh) übersteigt `max_delta`
(0,75 xh), kein Abstieg holt das e zurück, es wird auf
Verbinder + r-Abstrich geknautscht, der e→r-Verbinder läuft
RÜCKWÄRTS (−7,6 px), das r startet 10 px zu früh und endet
14 px (0,46 xh) zu kurz; in Wer (e der Hand 0,81 xh, Überschuss
0,17 xh, im Budget) fittet dasselbe Paar sauber — obwohl Wers
Crop einen echten Fleck trägt, der nichts bewegt (nächster
Kandidatenpunkt 0,52 xh). Nebenfunde unter, beide LINEAL-Fragen:
81 % der 0,45 sind Strich-REIHENFOLGE (Hand schreibt den
u-Bogen zuletzt, Kette in der Mitte; Bogenlänge 1,10 xh >
`MARK_MAX_ARC_UNITS` 0,8 → Körper statt Marke, monotone DTW
paart Bogen gegen e/r: nur Reihenfolge korrigiert 0,450 →
0,084); r-Auslauf in unter UND Wer 0,46–0,49 xh zu kurz
(komponierter r-Auslauf). → Composer-Auftrag e-Breite (§7.2),
Autor-Entscheid zur Bogen-Klassifikation (eingefrorenes Lineal,
hier NICHT angefasst).

**Mechanik (Code-Karte).** Kette und Folger lesen die Tinte an
je EINER Stelle über `case.skel`/`case.width_map`
(`tools/pairlab/chain.py` `_prepare_fields`: Spaltenband in x,
keine Zeilen-, keine Komponentenbeschränkung) — Zugfeld,
Coverage-Ziele (alle Skelettpixel, 300/Segment), Breitenfeld
(nächste Tinte propagiert) und Landmark-Kandidaten kommen von
dort; `_grid_fits` (Seed-Fenster) liest denselben Skelett-EDT.
Der COVERAGE-Term ist der Zieher (jeder Fremdpixel zieht die
nächste Probe zu sich, 25 Pixel = 8 % des Terms, ohne
Gegenkraft); das Abstandsfeld hält nur fest, was schon da ist.
Einzige Filter heute, beide beim Export und komposition-blind:
`despeckle` (< 24 px) und die handgesetzten `exclude`-Rechtecke.
**Messung über alle 63 Fixtures: 90 Nicht-Haupt-Komponenten —
FLÄCHE trennt nicht (echte Marken 62–250 px, Fremdtinte 24–55
px, Wers Marke 62 vs schwers Fleck 55), DUNKELHEIT trennt
vollständig:** auf der Skala `rel = (Median-Grau Komponente −
Median-Grau Hauptinte) / (Median-Grau Papier − Median-Grau
Haupttinte)` liegen die 46 echten (i-Punkte, u-Bögen, ß-Paare,
die 800-px-Bruchstücke in han/Sporn) bei 0,01–0,38 und die 44
fremden bei 0,74–0,92 — eine Lücke von 0,36, nichts darin; alle
hand-beanspruchten Komponenten der 28 authored-Wörter (Abstand
zur Hand ≤ 0,01 xh) liegen ≤ 0,12.

**Maßnahme K-C.** `tools/pairlab/ink_evidence.py`: Komponenten
von `width_map > 0` (≡ `ref_mask.png`, kein neuer Dateizugriff),
größte Komponente = das Wort, immer behalten; jede andere mit
`rel > 0,5` wird aus `skel` UND `width_map` gelöscht
(`paper_fraction` ist KEIN Knopf, sondern die Mitte der
gemessenen Lücke — jeder Wert in (0,38 · 0,74) wählt dieselben
Komponenten; Kontrast < 0,05 → nichts wird beurteilt).
Einsatzpunkt je Route genau EINER: `follow_derived`
(+ Kalibrierpfad) bzw. `harvest.chain_word_strokes`, NACH
`derive_word` (das eingefrorene wordbench-Lineal und die
Registrierung entstehen auf der vollen Tinte) und VOR
`_grid_fits` — Seed-Fenster, Solve-Felder, Coverage und
Marken-Nachfit sehen EINE Evidenz. Aus = Objekt-Identität
(derselbe `WordCase`), ebenso „an, aber nichts gedroppt" →
Wörter ohne Fremdtinte sind konstruktionsbedingt
BYTE-IDENTISCH (testbare Vorhersage, unten). Flags:
`FollowWeights.ink_evidence` (`--ink-evidence`),
`HarvestOptions.ink_evidence` (declared-off; erste Option auf
dem Harvest, die das MESSEN ändert — Adoption in den Speicher-
Trace ist eine eigene Entscheidung). Drop-Liste je Wort im
Report (`meta.ink_evidence`: Fläche, Skelettpixel, Zentroid,
Grau, `rel`) — ein stiller Drop wäre der Fehlermodus, der ein
späteres Negativ unlesbar macht. Der Lineal-Maskenstand
(`ref_mask`/`ref_skel`, AIoU, Zähler) bleibt unverändert: die
Torpfosten stehen (§1), nur das, was den FIT zieht, ändert sich.
Lotse hat dieselbe Exposition (`pilot.py` `PilotGraph(case.skel)`)
mit anderer Fehlerform (Fleck = Kandidaten-Schiene, durch den
Bridge-Preis strukturell robuster; die Zähler lesen aber
Fremdknoten mit) — eigene Sprosse, eigene Pre-Reg.

**Messanordnung.** 63 Wörter (`--all`), Stack
`--structure-guard-soll` (= K0-Z-Basis), BLAS gepinnt, Basis =
`temp/tb-aug20/k0z-ident-cand.json` (≡ aug19-K0-soll); Läufe:
Identität (Flag aus, neuer Code) und K-C (`--ink-evidence`).
Bewertung: k0-Protokoll (Soll-Abstand + aiou je Wort, 63) +
dev-19-Referenzbench (Basis NEU gescored, siehe Lineal-Notiz)
+ Drop-Liste + Hand-Claim-Prüfung (28 authored: keine
gedroppte Komponente näher als 0,1 xh an einem Hand-Strich).

**Gates:** (1) Identität: Flag aus = byte-gleich zur Basis;
(2) Wörter OHNE Drops byte-gleich (Konstruktions-Vorhersage —
reißt sie, ist die Messkette falsch, nicht die Maßnahme);
(3) 63er: Soll-Abstand je Wort NIRGENDS schlechter, aiou je
Wort ≥ −0,003; (4) dev-19: kein Wort verliert > 0,003 dtw,
`marks_missing + marks_spurious` je Wort nicht schlechter,
reversed 0, Netto-Kreuzungsdefekte ≤ Basis; (5) Hand-Claim
0 Treffer; (6) Laufzeit-Report. **Adoption: alle Gates → Autor-
Go → Kette v4 (`ink_evidence=True` als Folger-Default, datierte
Re-Baseline) und derselbe Default auf dem Harvest.**

**Ehrliche Erwartung.** zwei: beide Nadeln verschwinden (2
unechte Retrace-Zonen weg, dtw 0,076 → Größenordnung 0,05);
Galoppieren: i-Punkt-Strich bleibt kompakt → Marke 1/1, E1/E3
weg, dtw 0,233 → um 0,06; Wer: byte-identisch? NEIN — Wers
Fleck wird gedroppt, also ein neuer Solve, erwartet ≈ gleich
(der Fleck bewegte nichts); unter, mit, und, will, laden,
linken, das, die, muß-Familie: byte-identisch (keine
Fremdtinte). **die-2 wird von K-C NICHT geheilt** — der Magnet
ist die eigene, dunkle Marke; der benannte Nachfolger ist die
**Marken-Claim-Trennung** (Körper-Evidenz ohne Marken-
Komponenten, Marken-Striche mit ihrer eigenen), ein Eingriff
in `_prepare_fields` je Segment, eigene Pre-Reg. Zweiter
benannter Nachfolger, Autor-Idee vom selben Abend: **K-D
Tinten-Korridor** — eine Sperrzone um die erweiterte Tinte,
die die Bahn nicht durchstoßen darf (Barriere auf
`dist_raw > r`), gegen Schräg-Abkürzungen durch Gegenschleifen
(unters e) und gegen Nadeln ins Papier unabhängig von der
Maske; benanntes Risiko: ein versetzter Seed (unter: 0,65 xh)
kann die Tinte dann nicht mehr über Papier erreichen und wird
auf der falschen Tinte eingesperrt — unters Wurzel ist die
Composer-e-Breite, die kein Korridor heilt. Risiken von K-C:
eine echte Komponente in der Lücke (nie beobachtet; Drop-Liste
+ Hand-Gate decken es); die Coverage-Dichte steigt auf der
behaltenen Tinte (300 Ziele auf weniger Pixel) — Teil der
Maßnahme, aber `cov_rmse`-Diagnosen sind über das Flag hinweg
nicht vergleichbar.

**Lineal-Notiz (aug20 Abend):** der Autor hat den beim
Nachfahren vergessenen i-Punkt von zwei nachgeholt (live: 2
Striche, 1161 + 34 Punkte). Refill ohne Re-Baseline per
`fetch_fixtures --set words --only word-instances`
(`werkzeuge.md`, der erste Akt einer Runde): 63 Bahnen, 28
authored, 0 frame-stale; ändert für zwei `marks_expected`
0 → 1, keine Körperbahn. Alle dev-19-Zahlen dieses Eintrags
sind gegen den Refill-Stand gescored, die K0-Z-R-Zahlen oben
gegen den Vor-Stand (zwei-Marken-Spalte nicht vergleichbar).

**Gemessen `aug20` nacht — ALLE SECHS GATES BESTANDEN; die
größte Struktur- UND Tintenbewegung der Ketten-Geschichte, bei
null Verlierern.** Artefakte `temp/tb-aug20/kc-*`
(`kc-ident*` · `kc-on*` · `kc-eval.txt` · `kc-*-dev*`), BLAS
gepinnt, 4 Worker, 63 Wörter in 958 s (Identität) / 969 s
(K-C, +1 %). **(1) Identität:** Flag aus = 63/63 Wörter
byte-gleich zur K0-Z-Basis. **(2) Konstruktions-Vorhersage:**
23 Wörter tragen Fremdtinte (44 Komponenten, exakt die 44 der
Vorab-Messung), die 40 anderen sind unter dem Flag 40/40
byte-gleich. **(3) 63er, k0-Protokoll: Gesamt-Soll-Abstand
107 → 86** (11 besser · 52 gleich · 0 schlechter — K0-Z-R
erreichte 99 und riss dabei Gates): Galoppieren 7 → 2, kann
5 → 3, regieren 4 → 2, zwei 4 → 2, Einen 2 → 0, Zaum 2 → 0,
schwer 2 → 0, wenn-2 1 → 0, Soldaten/die-2/schießen je −1.
**aiou: kein einziges Wort unter ±0, Median der 23 bewegten
+0,02, Maximum Wer +0,0991** (macht +0,078, Einen +0,081,
wenn-2 +0,081, und-4 +0,068, er-3 +0,040). **(4) dev-19:**
dtw-Median 0,0494 → **0,0453** (Bestwert der Route; K0-Z-R:
0,0472), aiou-Median 0,717 → **0,747**, schlechtester
dtw-Verlust **+0,0002** (die-2), Marken `missing` 1 → 0 (der
Galoppieren-Punkt), `spurious` 0 = 0, reversed 0, Netto-
Kreuzungsdefekte 21 → 19, **unechte Retrace-Zonen 13 → 7**,
Lifts Δ 7 → 6. Je Wort: **Galoppieren 0,2329 → 0,0383**
(−83 %, i-Punkt-Strich kompakt, E1/E3-Nadeln weg, Retrace
0/4 → 0/0), **zwei 0,0726 → 0,0558** (beide w-Nadeln weg:
Retrace 0/2 → 0/0, aiou +0,027), Wer 0,0435 → 0,0363 (aiou
+0,099), und-4 0,0433 → 0,0393 (aiou +0,068), die-2
0,0746 → 0,0748 (aiou +0,008, Kreuzung 2/0 → 1/0 — die
V-Nadel bleibt, wie vorhergesagt: ihr Magnet ist die eigene
Marke). **(5) Hand-Claim:** 0 Treffer — die nächste gedroppte
Komponente liegt 0,53 xh von einer Hand-Bahn (zweis C2), alle
anderen ≥ 0,76 xh. **(6)** Laufzeit +1 %.

Die Vorhersagen der Pre-Reg hielten wörtlich: Wörter ohne
Fremdtinte byte-gleich, zwei/Galoppieren geheilt, Wer „≈
gleich" war zu vorsichtig (+0,099 aiou — der Fleck HATTE
gezogen, nur nicht die nächste Bahn, sondern die Coverage),
die-2 ungeheilt. **Status: alle Gates bestanden → Adoption
wartet auf das Autor-Go (Kette v4 = `ink_evidence=True` als
Folger-Default, datierte Re-Baseline aller Ketten-Zahlen;
derselbe Default auf dem Harvest).** Bis dahin declared-off.
*(Eingelöst `aug21`: Autor-Go, Flip und Re-Baseline im Eintrag
„Kette v4 `aug21`" unten.)* Lesart für die Kampagne: die
Fremdtinte war eine
Störquelle UNTER allen bisherigen Kettenarmen — K0-Z-R, die
λ-Leiter, die Wächter-Runden haben gegen sie gemessen; die
Wiedervorlage der stärksten verworfenen Sprosse (K0-Z-R 0,55)
auf K-C-Evidenz ist der naheliegende nächste Arm, NACH der
Soll-Quellen-Autopsie, die K0-Z-R ohnehin braucht.

### Kette v4 `aug21` — Adoption K-C: die Tinten-Evidenz-Maske wird Default (datierte Re-Baseline)

**Autor-Go (2026-08-21, Kampagnen-Auftrag):** K-C wird als
Kette v4 geflippt. Der Flip: `FollowWeights.ink_evidence = True`
(CLI-Archäologie `--no-ink-evidence`, das
`retrace_guard`-Muster), `HarvestOptions.ink_evidence = True`
(erreicht den `chain`-Provider des Tracebench über die
Options-Defaults; neues Provider-Kwarg `ink_evidence` für
Archäologie-Läufe, das `marks_last`/`trace_repair`-Muster), die
Default-Pins in `test_pairlab_ink_evidence` /
`test_tracebench_candidates` auf v4 gedreht. Kein
Algorithmus-Code bewegt sich — nur Defaults und CLI-Verdrahtung.

**Messanordnung.** Frische Cloud-Umgebung (die aug20-Artefakte
liegen dort nicht vor), darum BEIDE Arme neu gemessen — erster
Akt `fetch_fixtures --set all --verify` (bit-exakt, 12/12
Kompositionen), dann in EINER gepinnten Umgebung
(`OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `--jobs 4`):
Vor-Flip-Basis und Nach-Flip-v4 je 63 Wörter auf dem
K-C-Stack (`--structure-guard-soll`), dazu der `chain`-Provider
dev-19 vor/nach dem Flip; Bewertung k0-Protokoll (Soll-Abstand +
aiou je Wort, 63) + dev-19-File-Provider, gepaart.

**Validierung der Messkette:** (1) Der Vor-Flip-`chain`-Provider
reproduziert die deklarierte v3-Baseline EXAKT (dtw-Median
0,049135 · p90 0,0891 · worst muß 0,1097; die kleinen
Zähler-Abweichungen — marks 0+0 statt 0+1, cross 15+6, touch 22 —
sind der dokumentierte zwei-i-Punkt-Refill des Lineals).
(2) Identitäts-Gate: der Nach-Flip-Archäologie-Lauf
(`--no-ink-evidence`, volle 63) ist byte-gleich zum
Vor-Flip-Default — der Flip ist eine reine Default-Änderung.
(3) Konstruktions-Vorhersage: 23 Wörter tragen Drops, 44
Komponenten — EXAKT die aug20-Zählung; alle 40 drop-freien
Wörter byte-gleich, 4 gedroppte ohne Bahnwirkung (Sporn, Zügel,
im, von: Fremdkomponente außerhalb jedes Run-Bandes), 19 bewegt.

**Gemessen (gepaart, Basis → v4, diese Umgebung):** 63er
k0-Protokoll: **Gesamt-Soll-Abstand 103 → 85** (11 besser · 51
gleich · 1 schlechter) — Galoppieren 7 → 2, zwei 4 → 2,
kann 4 → 3, regieren 3 → 2, schwer/Einen/Zaum je 2 → 0,
wenn-2 1 → 0, Soldaten/schießen/fechten je −1; der eine
Verlierer ist die-2 3 → 4 (unten). **aiou der 19 bewegten:
Median +0,0245, Maximum Wer +0,0985** (Einen +0,0964, wenn-2
+0,0830, macht +0,0785, und-4 +0,0691, er-3 +0,0577); EIN
Verlierer streiten −0,0075. **dev-19 (File-Provider): dtw-Median
0,0491 → 0,0448**, aiou-Median 0,7161 → **0,7481**, Marken
`missing` 1 → 0 (der Galoppieren-Punkt), `spurious` 0 = 0,
reversed 0, **unechte Retrace-Zonen 13 → 7**, Lifts Δ 7 → 6,
Kreuzungen 15+7 → 14+8 (netto 22 = 22); je Wort: **Galoppieren
0,2349 → 0,0385**, zwei 0,0726 → 0,0556, Wer 0,0432 → 0,0369,
und-4 0,0433 → 0,0390, schlechtester Verlust **die-2 +0,0004**,
14/19 byte-gleich. `chain`-Provider dev-19 (die
rounds-0-Produktionsfläche): Median-Δ 0,0000 (zwei −0,0024,
Galoppieren −0,0011, und-4 −0,0009, die-2 +0,0009), aiou-Median
0,6993 → 0,7021, p90/worst unverändert — der große K-C-Hebel
liegt erwartungsgemäß im FOLGER (Coverage-Zieher), nicht im
rounds-0-Kettenfit. Laufzeit 63er: 752 s Basis, 628 s v4.

**Umgebungs-Ehrlichkeit.** Die aug20-Messung lief in einer
anderen Umgebung; die dokumentierte Solver-Sensitivität
(aug16-Lehre) zeigt sich als kleine je-Wort-Varianz der BASIS
(Soll-Abstand dort 107, hier 103; kann/regieren-Basis je −1)
und an zwei Stellen im Delta: die-2 dort −1, hier +1
Soll-Abstand (bei dev-dtw +0,0004 — der Magnet der V-Nadel ist
die EIGENE Marke, K-C heilt sie vorhersagegemäß nicht; genau
dafür steht die Marken-Claim-Trennung als benannter Nachfolger),
und streiten dort ±0, hier aiou −0,0075. Die Adoption stützt
sich auf das bestandene aug20-Sechs-Gates-Protokoll plus die
heutige Reproduktion des Muster-Kerns (18 Punkte Soll-Gewinn,
null dev-dtw-Verlierer über +0,0004, aiou-Median +0,03) in einer
zweiten Umgebung; die gepaarten Deltas sind innerhalb JE einer
gepinnten Umgebung gültig, nie zwischen beiden.

**Re-Baseline Kette v4 `aug21` (deklariert):** `chain`-Provider
dev-19: dtw-Median **0,0491** · p90 **0,0891** · worst
**muß 0,1097** · aiou 0,7021 · marks 0+0 · cross 14+7 ·
retrace 7+6 · touch 21. Folger auf dem Soll-Stack
(`--structure-guard-soll`, die Duell-Kette): dtw-Median
**0,0448** · aiou-Median **0,7481** · marks 0+0 · cross 14+8 ·
retrace 7+7 · 63er-Soll-Abstand **85**. Der p90/worst des
Folger-Kandidaten (0,2354 / unter 0,4503) trägt die bekannte
REIHENFOLGE-Lineal-Frage der K-C-Autopsie (u-Bogen/Deckbogen als
Körper mitten im Wort; der Chain-Provider zeigt sie dank
`marks_last` nicht) — der Autor-Entscheid zur
Bogen-Klassifikation steht unverändert aus. Gepaarte Vergleiche
anderer Routen (Lotse, InkSight, Nullprobe) sind mit ihrer
nächsten Messung gegen v4 neu zu beziffern; der
PRODUKTIONS-Re-Harvest der `traced`-Zeilen bleibt hinter
Owner-Go + dbsnapshot. Nächste Kettenarme
(Kampagnen-Reihenfolge): Marken-Claim-Trennung
(Tinten-Zuweisung per Strecke, eigene Pre-Reg), dann
Soll-Quellen-Autopsie (daß) → K0-Z-R-Wiedervorlage auf
K-C-Evidenz → K-D Tinten-Korridor.

### Kette K-E `aug21` — Vorregistrierung: Tinten-Zuweisung per Strecke, Stufe 1: die Marken-Claim-Trennung

Geschrieben und committet VOR der ersten Zahl. **Anlass
(Autor-Fund, Kampagnen-Auftrag 2026-08-21):** die K-C-Autopsie
benannte den Magneten, den keine Fremdtinten-Maske erreichen
kann: in die-2 zieht der EIGENE i-Punkt die d-Schleife (die
V-Nadel — Spitze 0,051 xh von der Punkt-Maske, Achse 3,2°
parallel zum Punkt-Strich, ohne den Punkt im Feld 4,2× teurer;
unter v4 der EINZIGE 63er-Verlierer, Soll-Abstand 3 → 4, dev-dtw
+0,0004). Der Autor vermutet dasselbe PLATTGEZOGEN in kleinen
Kringeln — Kandidat für die 7 verbliebenen unechten
Retrace-Zonen des v4-Stands. K-C hat die fremde Tinte entfernt;
die eigene, dunkle Marke bleibt konstruktionsbedingt im Feld.
Die Wurzel ist keine Masken-, sondern eine ZUWEISUNGS-Frage:
heute sehen ALLE Samples eines Runs EIN Feld und EINEN
Coverage-Topf (`_prepare_fields`: ein Spaltenband;
`build_chain_problem`: ein `dist_smooth` für alle Samples, und
jeder Coverage-Punkt zieht das NÄCHSTE Sample, egal welcher
Strecke es gehört).

**Maßnahme (Stufe 1 — nur Marken, wo der Duktus die Zuweisung
eindeutig macht).** (1) Marken-STRECKEN: Striche eines
Buchstaben-Segments, deren komponierte Init-Geometrie das
Assembler-Kriterium erfüllt (`trace.diacritic_stroke_units`,
alle Punkte > 1,0 xh — die K-A-Regel, keine
Zweitimplementierung): der i-Punkt (Anker 100–120 des i), der
u-Bogen (97–120 des u); der t-Querbalken fällt korrekt NICHT
darunter (durchquert das Mittelband). (2) Marken-KOMPONENTEN:
Nicht-Haupt-Komponenten der v4-Evidenz (NACH der
Tinten-Evidenz-Maske — eine Evidenz, ein Stand), deren
minimaler Abstand zur Init-Marken-Strecke ≤ 0,6 xh liegt
(`MARK_MATCH_RADIUS_UNITS`, der Marken-Radius des Lineals —
KEIN neuer Knopf); konkurrieren zwei Strecken, gewinnt die
nächste. (3) Ein CLAIM (Strecke ↔ Komponente) schaltet BEIDE
Zug-Kanäle um: die Komponente verlässt Distanz- und Breitenfeld
und Coverage-Topf der Körper-Samples; die Marken-Samples der
Strecke lesen ausschließlich das Feld IHRER Komponente, und
deren Coverage-Punkte ziehen nur noch diese Samples. OHNE Claim
ändert sich NICHTS: eine Marken-Strecke ohne dunkle Komponente
behält das Körperfeld (der heutige Suchweg — die
nicht-geschriebene Marke wird nicht neu behandelt), eine
Komponente ohne Marken-Strecke bleibt Körper-Evidenz (die
han/Sporn-Bruchstücke). Landmarks lesen das Körper-Skelett ohne
geclaimte Komponenten (Punkte tragen keine Verzweigungen).
Einsatzpunkt genau EINER: der Feld-Aufbau in `fit_word_chain`
(`_prepare_fields` → `build_chain_problem`,
Sample-Klassen-Maske nach dem `width_mask`-Muster), vom Folger
über `_fields_of` in jede Runde weitergereicht; Seed-Fenster und
Grid-Fits unverändert (die Marke gehört ihrem Buchstaben — die
Fensterung war nie das Problem). EIN Knopf: `mark_claim`
(`FollowWeights.mark_claim`, CLI `--mark-claim`;
`HarvestOptions.mark_claim` declared-off — das K-C-Muster:
erst der Folger, die Ernte-Adoption ist eine eigene
Entscheidung). Claim-Liste je Wort im Report
(Strecke, Komponente, Fläche, Abstand) — ein stiller Claim wäre
der Fehlermodus, der ein Negativ unlesbar macht.

**Messanordnung.** Basis = der aug21-v4-Stand DIESER Umgebung
(§14 „Kette v4": Folger-Soll-Stack-Kandidat `kc-v4-cand` +
dev-19-Scores); Läufe in derselben gepinnten Umgebung (BLAS 1,
`--jobs 4`), Stack `--structure-guard-soll`, 63 Wörter:
Identität (Flag aus — byte-gleich zur v4-Basis) und K-E
(`--mark-claim`). Bewertung: k0-Protokoll (Soll-Abstand + aiou
je Wort) + dev-19-File-Provider, gepaart; Augenschein die-2.

**Gates (Autor-Vorgabe + Standard):** (1) Identität: Flag aus =
byte-gleich; (2) Wörter ohne feuernden Claim byte-gleich
(Konstruktions-Vorhersage — reißt sie, ist die Messkette
falsch); (3) kein aiou-Verlierer (je Wort ≥ −0,003); (4)
dev-19-dtw nicht schlechter: kein Wort über +0,003, Median
nicht schlechter; (5) **die-2 gewinnt messbar:** Soll-Abstand
4 → ≤ 3 ODER dtw ≤ −0,005, UND die V-Nadel im Augenschein weg;
(6) Marken nicht schlechter, reversed 0, Netto-Kreuzungsdefekte
≤ Basis; (7) Laufzeit-Report. Adoption: alle Gates → Autor-Go
(dann Folger-Default, das v4-Muster); Stufe 2 (Kringel) wird
NUR bei haltender Stufe 1 vorregistriert.

**Ehrliche Erwartung.** die-2 heilt (der Magnet verliert beide
Kanäle — die d-Schleife hat keinen Grund mehr, die V zu
formen); Galoppieren: der i-Punkt-Strich wird
komponentengebunden (Rest ~0,038 → gleich oder leicht besser);
unter/kann u. a. bewegen sich über den u-Bogen-Claim (das
Körperfeld ändert sich um den Bogen), erwartet klein; von den 7
unechten Retrace-Zonen dürfen NUR die marken-verursachten
fallen — die Kringel-Klasse (Schleifenbuchstaben) bleibt
stehen und wird als Diagnose-Spalte für Stufe 2 ausgewiesen.
Benannte Risiken: (a) ein Claim auf ein Körper-Bruchstück —
der 0,6-xh-Radius von einer FLOATENDEN Strecke deckt das ab,
die Claim-Liste macht es lesbar; (b) eine Marke, deren Tinte
den Körper BERÜHRT (eine Komponente mit der Haupttinte) —
kein Claim möglich, heutiges Verhalten, benannte
Stufe-1-Grenze; (c) die Körper-Coverage-Dichte verschiebt sich
(Marken-Pixel verlassen den Topf) — Teil der Maßnahme,
`cov_rmse` über das Flag hinweg nicht vergleichbar.

**Stufe 2 (nur wenn Stufe 1 hält, eigene Pre-Reg):** die
Kringel — die Zuweisung, wo sie NICHT eindeutig ist (zwei
Körper-Strecken teilen sich dieselbe Tinte einer kleinen
Schleife, und der Coverage-Topf lässt einen Pass die Arbeit
beider erledigen); braucht den Duktus-Prior als
VERBRAUCHS-ZUORDNUNG (jeder Tinten-Punkt wird von genau einer
Strecke verbraucht); Messgröße: unechte Retrace-Zonen an
Schleifenbuchstaben.

**Gemessen `aug21` — per Gate (3) VERWORFEN in dieser Form, an
vier diffusen aiou-Rissen; die benannten Ziele heilen
spektakulär, und die Autopsie benennt den Konversions-Weg.**
Artefakte Scratchpad `tb-aug21/ke-*`, BLAS gepinnt, 4 Worker,
Identität 844 s · K-E 905 s (+7 %). **(1) Identität:** Flag aus
= 63/63 byte-gleich zur v4-Basis. **(2)
Konstruktions-Vorhersage:** 37 Wörter feuern Claims (i-Punkte,
u-Bögen, Umlaut-Doppelstriche je zwei; alle Abstände ≤ 0,50 xh),
die 26 claimfreien sind 26/26 byte-gleich — die Klassen decken
sich EXAKT mit der Claim-Liste. **(5) die-2 — das benannte
Ziel — heilt auf JEDER Achse: Soll-Abstand 4 → 1, dtw
0,0750 → 0,0469 (−0,0281), aiou +0,0229, die V-Nadel im
Augenschein WEG** (übrig ein kleiner Zickzack am
d-Schleifenschluss — die Kringel-Klasse). Dazu die
0,0745 → 0,0586, `cross_spurious` 8 → 5, `cross_missing`
14 → 13 (netto 22 → 18), **Retrace 7+7 → 6+6**, Marken 0+0,
reversed 0, 63er-Soll 85 → 82 (4 besser · 56 gleich · 3
schlechter: unter/Seiten/Sprünge je +1 — Seiten und Sprünge
tragen die beiden WEITESTEN Claims, 0,30/0,50 xh). **(4)
dev-19: Median EXAKT gehalten** (0,044785 = 0,044785, das
Median-Wort byte-gleich), schlechtester Verlust muß-2 +0,0026
(unter der Schwelle). **ABER (3): vier aiou-Verlierer unter
−0,003** — auch −0,0270, schießen −0,0269, Einen −0,0146,
muß-2 −0,0131 (15 weitere Verlierer sind ≤ 0,003 =
Messrauschen; über die 37 bewegten: min −0,0270 · Median
−0,0002 · max +0,0229). **Autopsie (Deckungs-Differenz je
Pixel, klassifiziert nach geclaimter Komponente):** verloren
geht in allen vier Fällen KÖRPER-Tinte (64–184 px), diffus
über die GANZE Wortbreite (bbox = Wort), die Marken-Komponenten
selbst bleiben gedeckt — kein lokaler Marken-Effekt, sondern
eine Basin-Umverteilung des Körper-Solves nach dem Entzug.
Verdächtige Kanäle, in Reichweite EINER Formulierungs-Frage:
(a) der BREITENFELD-Split — der einzige Kanal, der Messziele
(nicht Anziehung) über die gesamte Voronoi-Region der Marke
umschreibt (v4 propagierte die Marken-Breite auf
Körper-Samples: eine Korruption, aber eine, gegen die der Fit
kalibriert war); (b) die Coverage-NORMIERUNG (die Marken-Ziele
verwässern jeden Körper-Zug um 1–3 %). Die Gates werden nicht
aufgeweicht: NICHT adoptiert; `mark_claim` bleibt declared-off.
Rettungswege (§7.9-Zeile im selben PR): (1) **K-E2** — der
Ein-Faktor-Konversionsarm direkt darunter; (2) der
humanbench-Tie-Breaker für den Rest-Trade, falls K-E2 die
diffuse Klasse nicht schließt (Median −0,0002 über die
bewegten = Lineal-Indifferenz bei starken Struktur-Gewinnen);
(3) Claim-Schärfung für Bogen-Strecken (die
Seiten/Sprünge-Soll-Risse korrelieren mit Claim-Distanz ≥ 0,3
xh) — erst NACH K-E2, eigene Pre-Reg.

### Kette K-E2 `aug21` — Vorregistrierung: die Marken-Claim-Trennung ohne Breitenfeld-Split (Ein-Faktor-Konversion)

Geschrieben und committet VOR der ersten Zahl. Die K-E1-Autopsie
(oben) verortet den diffusen Körper-Deckungsverlust NICHT an den
Marken, sondern in der Basin-Umverteilung des Körper-Solves;
der verdächtigste Kanal ist der Breitenfeld-Split, weil die
Breite ein MESSZIEL ist (Soll-Ist-Vergleich je Sample), kein
Anziehungsfeld: sein Split ändert Ziele über die gesamte
Voronoi-Region jeder Marke, auch weit weg von jeder Nadel.

**Maßnahme (EIN Faktor gegenüber K-E1):** die Breitenfelder
bleiben UNGETEILT — Körper- wie Marken-Samples lesen das
historische, aus ALLER behaltenen Tinte propagierte
`width_raw`/`width_smooth`; Distanzfeld und Coverage-Topf
bleiben exakt wie in K-E1 getrennt (die beiden Kanäle, die
die-2s Nadel-Magneten trugen). Derselbe Knopf `mark_claim`
(der K-E1-Mechanismus ist nie adoptiert worden und bleibt als
Archäologie in der Git-Historie); Claim-Regel, Radius und
Claim-Liste unverändert.

**Messanordnung:** unverändert K-E1 (Basis = v4-Kandidat
dieser Umgebung, Soll-Stack, BLAS gepinnt, `--jobs 4`; 63er
k0-Protokoll + dev-19-File-Provider gepaart + Augenschein
die-2). **Gates: IDENTISCH zu K-E1, keines weicher.** Ehrliche
Erwartung: die vier Risse schließen sich, wenn die Breite der
Treiber war; die-2/die/Struktur-Gewinne bleiben (sie hängen an
Distanz+Coverage). Bleiben die Risse, ist der Treiber die
Coverage-Umverteilung selbst → K-E-Familie schließt, der
Rest-Trade geht den humanbench-Weg (§7.9).

**Gemessen `aug21` — verworfen per Gate (3), die
Breiten-Hypothese ist SAUBER WIDERLEGT, die Familie schließt
nach der eigenen Vorregistrierung.** Artefakte
`tb-aug21/ke2-*`, 931 s. Die Heilungen bleiben exakt bestehen
(die-2: Soll 4 → 2, dtw −0,0282, V-Nadel weg im Augenschein;
die −0,0161; dev-Median exakt gehalten; netto-Kreuzungen
22 → 19; Retrace 6+6; 63er-Soll 85 → 81, Sprünges
K-E1-Soll-Riss heilt, unter/Seiten je +1 bleiben) — und die
vier aiou-Risse bleiben ebenso: auch −0,0270, schießen
−0,0255, Einen −0,0147, muß-2 −0,0131. **Der Beweis-Kern: 55
der 63 K-E2-Kandidaten sind BYTE-GLEICH zu K-E1 — darunter
auch und muß-2, zwei der vier Verlierer:** für sie war der
Breitenfeld-Split nachweislich vollständig inert (kein Sample
ihrer Solves las je einen abweichenden Breitenwert); bei
Einen/schießen bewegt die Breite das Wort minimal und der Riss
bleibt in gleicher Höhe. Der Treiber des diffusen
Körper-Deckungsverlusts ist damit die
Distanzfeld-/Coverage-UMVERTEILUNG selbst — die beiden Kanäle,
die zugleich die Heilung tragen: Gewinn und Verlust dieser
Formulierung sind nicht weiter trennbar, exakt das
Arm-⑨-Muster eine Schicht tiefer. `mark_claim` bleibt
declared-off (K-E2-Mechanik im Code, nie adoptiert). **Stufe 2
(Kringel) wird NICHT eröffnet** — die Autor-Bedingung „nur
wenn Stufe 1 hält" ist nicht erfüllt. Rettungswege (§7.9
aktualisiert im selben PR): (1) der **humanbench-Tie-Breaker**
— der Fall ist der vorregistrierte Methodik-Fall in Reinform
(aiou-Median der bewegten −0,0002 = Lineal-Indifferenz; vier
lokale aiou-Verluste −0,013…−0,027 gegen die-2-Heilung,
netto-Kreuzungen −3, Retrace −2: ob ein Mensch die
K-E-Bahnen als besser beurteilt, kann nur die blinde Runde
sagen); (2) **Distanzfeld-NUR-Claim** (neuer Mechanismus:
Coverage-Topf bleibt völlig unangetastet = v4-Ökonomie, nur
das Anziehungsfeld wird je Klasse getrennt — die
die-2-V-Nadel war laut Autopsie 4,2× distanzfeld-getrieben;
frische Pre-Reg, Risiko: die Coverage-Drag-Hälfte der
Nadel-Klasse bleibt); (3) Claim-Schärfung für Bogen-Strecken
(gegen die verbliebenen unter/Seiten-Soll-Risse; nachrangig).

### Kette K0-S `aug21` — Soll-Quellen-Autopsie (daß) + Vorregistrierung: EINE Soll-Pipeline und die K0-Z-R-Wiedervorlage

**Die Autopsie (VOR dieser Pre-Reg, Skript/Bilder Scratchpad
`tb-aug21/soll_autopsy.py` + `dass-soll-autopsy.png`): der
K0-Z-R-daß-Riss war ein INIT-ARTEFAKT im Wächter-Soll — die
Metrik hatte recht.** Beide Pipelines nutzen DIESELBEN Zähler
(`tools.tracebench.counters`); die Divergenz liegt allein in
der Eingabe-Geometrie. An daß (d·a·ſz): die Metrik-Quelle
(`ductus_soll` auf den komponierten Items, lift-gesplittet)
zählt cross 3 · retrace 1 (ſz-Zone bei 3,74/1,48) · touch 0;
die Wächter-Quelle (Ketten-Init bei x0 = 0 durch
`_stroke_polylines_px` + Assembler) zählt cross 3 · retrace 2
· touch 1 — die zusätzliche Zone bei (1,22 · 1,20) plus die
Berührung bei (1,17 · 1,16) sitzen am d-KOPF: die
Init-Geometrie (Chart-Anker + generierter Verbinder) drückt
den d-Schleifenschluss zu einem PLATTGEZOGENEN SPLITTER
(zwei fast parallele Pässe), den der 0,15-xh-Detektor korrekt
als Retrace + Touch liest; die kanonische Komposition kreuzt
dort sauber und trägt nichts. (Nebenbefund, notiert für die
Kringel-Frage: der Splitter ist exakt die Geometrie-Klasse
„Kringel plattgezogen" — hier als Artefakt der Init, nicht
der Tinte.) Die Architektur ist eindeutig: `core/compose` ist
DIE Kompositions-Quelle der Wahrheit; das aug19-Wächter-Soll
las stattdessen die Init-Nachbildung (Chart-Anker samt
Laufform-Wrinkle) — der „ohne Zweitimplementierung"-Anspruch
galt für die ZÄHLER, nicht für die Geometrie.

**Maßnahme K0-S (EIN Knopf).** `FollowWeights.soll_source`
(`--soll-source`, Default `"init"` = heutiges Verhalten,
byte-identisch): bei `"composition"` kommt das Wächter-Soll
aus dem KOMPOSITIONS-Builder — die Item→Strich-Logik wird aus
`tools/tracebench/soll.py::ductus_soll` als
`composition_strokes` herausfaktorisiert (reiner Refactor,
`ductus_soll` selbst bleibt byte-identisch) und vom Folger je
Run auf den zusammenhängenden Item-Span der Run-Slots
angewandt (Slots des Runs plus die Verbinder-Items zwischen
ihnen, lift-gesplittet, Marken-Items an ihrem Item-Ort).
Damit gilt: BUDGET = Init-Zählung (die Runden starten dort),
RUNDEN-COUNTS = Kandidaten-Zählung (was gelöst wurde), SOLL =
Kompositions-Zählung — drei Messungen, EIN Zähler-Satz, und
das Soll kommt erstmals aus der kanonischen Quelle. Das
Akzeptanz-Intervall je Klasse bleibt [min(B,S), max(B,S)] —
es enthält B immer, der Wächter verlangt nie Unerreichbares.

**Messanordnung (Leiter, Basis = v4-Stand dieser Umgebung,
BLAS gepinnt, `--jobs 4`, Soll-Stack).** Sprosse 0:
**Divergenz-Karte** — beide Soll-Zählungen je Wort über alle
63, ohne Solve (wo divergieren Init und Komposition noch,
außer an daß?); referenzfrei, reine Diagnose. Sprosse 1:
`--structure-guard-soll --soll-source composition` (der
atomare Soll-Wächter auf der neuen Quelle). Sprosse 2:
dieselbe Quelle + `--structure-guard-ratchet
--structure-guard-zone 0.55` — **die K0-Z-R-Wiedervorlage**
(§7.9-Rettungsweg der stärksten je gemessenen Sprosse: Soll
107 → 99 bei NULL aiou-Verlierern, damals an daß und dem
zwei-Trade gerissen; beide Risse sind seither adressiert —
daß durch diese Quelle, zweis Fremdtinten-Magneten durch v4).

**Gates (unverändert K0-Z, keines weicher):** Identität
(`soll_source=init` byte-gleich zur v4-Basis) · Soll-Abstand
sinkt IRGENDWO strikt und steigt je Wort NIRGENDS (auf der
EINEN Metrik — Soll-Quelle jetzt für Wächter und k0-Protokoll
identisch) · aiou je Wort ≥ −0,003 · dev-19: kein Wort über
+0,003 dtw, Marken nicht schlechter, reversed 0,
Netto-Kreuzungsdefekte ≤ Basis · Laufzeit-Report. Adoption:
die beste Sprosse, die alle Gates hält; Gleichstand → die
einfachere (Sprosse 1 vor 2).

**Ehrliche Erwartung.** Die daß-Klasse stirbt konstruktiv
(Intervall [1,2] statt [2,2] — Bewegung nur noch Richtung
Komposition); die Divergenz-Karte zeigt vermutlich weitere
Init-Artefakt-Solls (jede weitere Divergenz ÖFFNET ein
Intervall — Teil der Maßnahme, die Karte macht es lesbar);
die alte K0-Z-R-Substanz ist auf v4-Evidenz NEU zu beziffern
— zweis damaliger dtw-Trade hing an Fremdtinten-Magneten, die
v4 gedroppt hat, ob er verschwindet, entscheidet die Messung.
Benannte Risiken: (a) ein Kompositions-Soll, das strukturell
über dem Init liegt (S > B), erlaubt der Ratsche Bewegung
NACH OBEN Richtung Soll — gewollt, aber neu; die je-Wort-Gates
decken es; (b) die Run-Restriktion der Items (Mehr-Run-Wörter)
ist neue Mechanik — der Identitäts-Pfad und die
Divergenz-Karte prüfen sie, bevor ein Solve sie sieht.

**Gemessen `aug21` — ALLE GATES bestehen auf BEIDEN Sprossen;
die Wiedervorlage holt die K0-Z-R-Substanz ohne einen einzigen
Riss, und der alte zwei-Trade INVERTIERT.** Artefakte
`tb-aug21/k0s-*`, BLAS gepinnt, 4 Worker. **Sprosse 0
(Divergenz-Karte, ohne Solve): 40 der 63 Runs divergieren** —
daß war Muster, nicht Ausreißer: JEDES d-Wort (die · das ·
der×3 · laden · daß · die-2 · Feinde) trägt die
daß-Signatur (Init zählt am d-Kopf +1 Retrace/+1 Touch, die
Komposition nicht — der plattgezogene Init-Splitter ist
systematisch); in der Gegenrichtung verliert die Init
Strukturen, die die Komposition trägt (mit/mit-2/wenn/wenn-2/
will/zwei: je +1 Kreuzung/Retrace/Touch im Kompositions-Soll),
dazu beidseitige Kreuzungs-Divergenzen (haben 5 → 3, han/auch/
auch-2 3 → 1 als Init-Mehrzählung; Soldaten/unter/streiten
+1 in der Komposition). **Identität:** `soll_source=init`
byte-gleich zur v4-Basis (4-Wort-Spot inkl. daß, 4/4; der neue
Code berührt nur den Soll-Zweig). **Sprosse 1 (atomarer
Soll-Wächter, Kompositions-Quelle, 642 s): Soll 85 → 80** (4
besser · 59 gleich · **0 schlechter**; bewegt nur Kugel,
Silber, Soldaten, das), aiou-Ausschlag einzig das −0,0005
(Rauschen), Maximum +0,1045; dev-19 praktisch byte-neutral
(Median-Δ 0, 18/19 ties, `cross_spurious` 8 → 6). **Sprosse 2
(Ratsche + Zone 0,55, Kompositions-Quelle, 897 s = +6 %):
Soll 85 → 77 (7 besser · 0 schlechter), 30 Wörter bewegt,
aiou-Median der bewegten +0,0589, Maximum +0,1316, einziger
Ausschlag das −0,0005; dev-19: aiou-Median 0,7481 → 0,7697
(+0,0216 — der größte dev-Tintengewinn der Kampagne), beide
Chamfer-Hälften besser, dtw-Median-Δ 0,0000, schlechtester
Verlust +0,0014 (und-2), Gewinne muß-3 −0,0154 · zwei −0,0100
· die −0,0068 · muß −0,0030; Marken 0+0, reversed 0,
Kreuzungen 14+5 (netto 22 → 19), Retrace 7+7 unverändert.**
Der K0-Z-R-Trade von zwei (+0,0142 dtw gegen +0,092 aiou) ist
INVERTIERT (−0,0100 dtw UND Tinten-Gewinn): seine Magneten
waren die Fremdtinte, die v4 seither droppt — beide
aug20-Risse (daß-Soll, zwei-Trade) sind damit als GELÖST
gemessen, nicht weggeschwellt. **Adoption: Sprosse 2 ist die
beste Sprosse, die alle Gates hält → wartet auf das Autor-Go
(Kette v5 = Soll-Stack `soll_source=composition` + Ratsche +
Zone 0,55 als Duell-/Folger-Konfiguration, datierte
Re-Baseline).** Bis dahin bleibt alles declared-off
(`soll_source` Default `init`, Ratsche/Zone Default aus).

### Kette K-D `aug21` — Vorregistrierung: der Tinten-Korridor, mit dem Gegenstands-Test zuerst

Geschrieben und committet VOR der ersten Zahl. **Anlass
(Autor-Idee 2026-08-20, §7.3 A8):** eine Sperrzone um die
erweiterte Tinte, die die Bahn nicht durchstoßen darf —
Barriere auf dem Abstandsfeld statt weichem Zug: verbietet
Schräg-Abkürzungen durch Gegenschleifen (unters e) und Nadeln
ins Papier unabhängig von der Maske. **Die Idee entstand VOR
der K-C-Messung** — und v4 hat die autopsierte Nadel-Klasse
(zwei-w-Füße, Galoppieren-Exkursionen: alles
Fremdtinten-Magneten) seither an der Wurzel geheilt, K0-S hat
die Bahnen weiter bewegt. Ob der Korridor noch einen
GEGENSTAND hat, ist darum die erste Frage, nicht die
Implementierung.

**Sprosse 0 — das Exkursions-Inventar (kein Solve, keine neue
Mechanik).** Auf den EXISTIERENDEN Kandidaten dieser Umgebung
(v4-Basis `kc-v4-cand` und v5-Anwärter `k0s-r2-cand`): je Wort
die auf den Lineal-Schritt resampelte Bahn gegen die
v4-Evidenz-Tinte (die K-C-bereinigte Maske — Fremdtinte zählt
nicht als Tinte), Messgrößen je Wort: maximale Exkursion (xh)
und Bogenlänge der Samples jenseits {0,35 · 0,5} xh.
**Entscheidungsregel, VOR der Zahl:** eine substanzielle
Ziel-Klasse liegt vor, wenn mindestens EIN Wort eine
Papier-Exkursion ≥ 0,5 xh trägt ODER mindestens DREI Wörter
≥ 0,35 xh (auf dem v5-Anwärter gezählt — der Stack, auf dem
der Korridor leben würde). Darunter wird K-D als
**GEGENSTANDSLOS NACH v4** geschlossen (kein Negativ der
Mechanik — die Wurzelbehandlung K-C/K0-S war schneller als das
Symptom-Verbot; Wiedervorlage-Auslöser: ein künftiges
Inventar oder ein neuer Arm zeigt eine neue
Papier-Nadel-Klasse; §7.9-Zeile im selben PR).

**Sprosse 1 (NUR bei substanzieller Klasse):** die Barriere
als glattes Hinge-Potential im Solve — je Sample
`max(0, d_smooth − r)²`, gemittelt, Gewicht fest 10× des
Geo-Terms (deklariert provisorisch), EIN Knopf
`corridor_units` (0 = aus = byte-identisch; Leiter
{0,5 · 0,35}), Einsatz in `build_chain_problem` neben dem
Geo-Term (analytischer Gradient aus demselben Feld-Lookup).
Gates: Identität (0 byte-gleich) · kein aiou-Verlierer je Wort
≥ −0,003 · dev-19 kein Wort über +0,003 dtw · Marken nicht
schlechter, reversed 0, Netto-Kreuzungsdefekte ≤ Basis ·
Soll-Abstand je Wort nirgends schlechter · ZIEL-Gate: die
maximale Exkursion sinkt strikt an den Inventar-Wörtern ·
Laufzeit-Report. **Benanntes Risiko (Autor, wörtlich aus der
K-C-Pre-Reg):** ein versetzter Seed (unter: 0,65 xh) erreicht
seine Tinte nicht mehr über Papier und wird auf der falschen
Tinte eingesperrt — unters Wurzel ist die Composer-e-Breite
(§7.2), die kein Korridor heilt; unter steht darum unter
gesonderter Beobachtung und ein unter-Riss wäre ein
erwartetes, benanntes Negativ, kein Überraschungsfund.

**Gemessen `aug21` — Sprosse 0 schließt den Arm:
GEGENSTANDSLOS NACH v4.** Inventar (als stehender Sensor ins
Repo übernommen: `tools/tracebench/excursions.py`; 63 Wörter,
Lineal-Schritt 0,02, gegen die K-C-bereinigte Evidenz): **kein einziges Wort
erreicht eine der Schwellen — auf KEINEM der beiden
Kandidaten.** Maximum des gesamten Sets: zum 0,332 xh
(v4-Basis) bzw. 0,312 (v5-Anwärter), zweitgrößter Wert han
0,269, alles Weitere ≤ 0,25; `arc>0,35` durchgehend 0,00.
Die autopsierte aug20-Nadel-Klasse (zwei-w-Fuß 0,5–0,75 xh
ins Papier, Galoppieren-Exkursionen bis 0,83 xh
kontrafaktisch) existiert nicht mehr: die WURZELBEHANDLUNG
(K-C: die Magneten aus der Evidenz) hat das Symptom
beseitigt, bevor sein Verbot (der Korridor) gebaut war. Die
Entscheidungsregel feuert eindeutig → **K-D geschlossen ohne
Implementierung** — kein Negativ der Mechanik, ein positiver
Befund über den Zustand der Route. Rettungsweg/
Wiedervorlage-Auslöser (§7.9-Zeile im selben PR): ein
künftiges Inventar oder ein neuer Arm zeigt eine neue
Papier-Nadel-Klasse (`tools/tracebench/excursions.py` ist der
stehende Sensor und läuft in Minuten auf jedem Kandidaten);
erst dann lohnt die Barriere, mit frischer Pre-Reg und dem
unveränderten unter-Risiko.

### Lineal L-U `aug25` — Vorregistrierung: der u-Bogen als Marke (Autor-Entscheid zur Bogen-Klassifikation)

Geschrieben und committet VOR der ersten Zahl. **Anlass:** die
K-C-Autopsie (`aug20`) legte den Befund offen und ließ die
Konsequenz ausdrücklich offen — „81 % der 0,45 sind
Strich-REIHENFOLGE (Hand schreibt den u-Bogen zuletzt, Kette in
der Mitte; Bogenlänge 1,10 xh > `MARK_MAX_ARC_UNITS` 0,8 →
Körper statt Marke) … Autor-Entscheid zur Bogen-Klassifikation
(eingefrorenes Lineal, hier NICHT angefasst)". Die Kette-v4-
Re-Baseline führt denselben Posten als offen (p90 0,2354 /
unter 0,4503). Der Autor hat am **2026-08-25** entschieden: das
Lineal wird geändert. Nach dem Klassen-Zensus unten hat er die
Entscheidung präzisiert — die Kappe wird **angehoben, nicht
gestrichen** (Begründung unter „Warum nicht streichen").

**Zensus (deskriptiv, VOR jeder Routen-Zahl; Skript im
Scratchpad, Root `tools/wordbench/fixtures/suetterlin/
suetterlin-1922`, Export 2026-08-14 / word_instances 2026-08-20).**
Erhoben wurde ausschließlich die KLASSE jedes Strichs, keine
Metrik. Über alle schwebenden Nicht-Erst-Striche (das sind die
einzigen Kandidaten für die Marken-Klasse):

| Seite | Punkte/Umlaute | u-Bögen |
|---|---|---|
| authored (Hand), 28 Wörter | 13 Striche, 0,449–**0,652** xh | 9 Striche, **1,039**–1,313 xh |
| traced (Kette), 35 Wörter | 12 Striche, 0,281–**0,789** xh | 6 Striche, **0,897**–1,966 xh |

Die neun Hand-u-Bögen sind `muß` ×3, `und` ×4, `unter` (dev)
und `Kugel` (confirm) — je einer pro Wort, immer der letzte von
zwei Strichen, y-Minimum 1,41–1,60 xh. **Es wechselt nichts
außer u-Bögen die Klasse:** kein Versalien-Ornament, keine
Oberlängenschleife, kein Umlaut. Die einzigen weiteren
Nicht-Erst-Striche der Hand (`Säbel`, `Einen`) tauchen unter
1,0 xh ab und bleiben unabhängig von jeder Kappe Körper.

Zwei Befunde des Zensus, die für sich stehen:

- Die heutige Kappe 0,8 liegt **innerhalb der Marken-Population**,
  nicht zwischen Marke und Körper. Auf der Kandidatenseite fehlen
  ihr **elf Tausendstel** zum Fehlklassifizieren eines echten
  Umlauts (`Sprünge` Strich 2: 0,789 xh).
- Der Kandidaten-Ausreißer `Zaum` (1,966 xh) ist per Overlay ein
  u-Bogen mit langem Fehl-Ausläufer, der die Tinte verlässt —
  ein Fit-Defekt, keine andere Strichklasse.

**Mechanik.** `tools/tracebench/frames.py::classify_strokes` — `is_mark =
index > 0 and floating and arc_length(pts) <=
MARK_MAX_ARC_UNITS`, mit `DIACRITIC_MIN_Y = 1.0` und
`MARK_MAX_ARC_UNITS = 0.8`. Zwei Abnehmer: `summary.score_word`
und der Duell-Viewer. Betroffen sind damit `dtw_xh` (+
`dtw_path_len` / `dtw_max_absorption` / `dtw_reversed_better`),
die ganze Marken-Familie inkl. des Co-Primär-Gates
`marks_missing` und `mark_pos_err_xh`, `marks_uncertain`, die
Lift-Spalten und der Richtungs-Audit. **Nicht** betroffen, weil
sie die VOLLE Strichliste lesen: `aiou`, beide Chamfer-Hälften,
Kreuzungen, Retraces inkl. `retrace_arc_ratio`, touch/overlap,
die `soll_*`-Spalten sowie `k0eval` und `excursions`.

**Maßnahme L-U — ein Knopf.** `--mark-arc-cap <xh>`, Default
0,8 = heutiges Verhalten = byte-gleich. Gemessen wird bei
**1,5 xh**. Die Höhe ist aus dem BREITENMODELL abgeleitet, nicht
aus der beobachteten Verteilung und schon gar nicht aus einem
Routen-Ergebnis: ein Standard-Kleinbuchstabe misst laut
`geometry.ADVANCE_DEFAULT_XH` eine x-Höhe in der Breite; ein
Diakritikum steht über EINEM Buchstaben; ein schwebender Strich
von mehr als anderthalb Buchstabenbreiten ist deshalb kein
Akzent mehr. Dass 1,5 zwischen 1,313 (größter Hand-u-Bogen) und
1,966 (`Zaum`-Defekt) fällt, ist Folge, nicht Begründung — jeder
Wert in (1,313 · 1,966) verhält sich auf dieser Population
identisch.

**Warum nicht streichen.** Ohne Kappe wanderte der `Zaum`-Defekt
aus der Körper-DTW in die Markenspalte: ein Kandidat könnte
einen groben Formfehler aus dem Primärmaß herausschieben. Der
Galoppieren-Fall der K-C-Autopsie ist derselbe Mechanismus (ein
i-Punkt-Strich springt auf ein Durchschein-Fragment, Bogen
0,53 → 1,82 xh). Beide bleiben bei 1,5 im Körper und werden
bezahlt — das ist der Zweck der Kappe, und er bleibt erhalten.

**Kopplung, die im selben PR aufgelöst wird.**
`tools/pairlab/marks.py:70` importiert `MARK_MAX_ARC_UNITS` als
`_RULER_MAX_ARC` und leitet `MARK_MAX_INK_ARC_UNITS = 2 ×`
daraus ab (heute 1,6). Bliebe der Import stehen, änderte die
Lineal-Anhebung still die KANDIDATEN-Seite und das
Identitäts-Gate risse aus einem Grund, der nichts mit dem Lineal
zu tun hat. Der Marken-Nachfit bekommt deshalb eine eigene,
eigenständig begründete Konstante.

**Messanordnung.** Nur der **dev-Satz (19 Wörter)** — die
Bestätigungswörter (`Kugel`, `Zaum`, `Gaul`, `auch`, `auch-2`,
`zu`, `Pulver`) bleiben versiegelt (§2.5, Autor-Entscheid
2026-08-25); der Klassen-Zensus oben ist ein Strukturfakt und
kein Messlauf. Vorher- und Nachher-Lauf in DERSELBEN Umgebung
mit gepinnten BLAS-Threads (`OPENBLAS_NUM_THREADS` /
`OMP_NUM_THREADS`), weil der Ketten-Solve zwischen Umgebungen um
ganze Soll-Punkte wandert (`aug21`, „Umgebungs-Ehrlichkeit").

**Gates.** Alle sechs müssen halten; keines davon ist ein
Routen-Ergebnis:

1. **Identität** — bei Kappe 0,8 ist jede Zahl byte-gleich zur
   stehenden Baseline. Der Knopf ist im Aus-Zustand wirklich aus.
2. **Klasse** — bei 1,5 wechseln GENAU die oben aufgezählten
   Striche die Klasse: 9 Hand-u-Bögen, 5 Kandidaten-u-Bögen.
   Kein anderer Strich, auf keiner Seite.
3. **Defekt** — `Zaum` (1,966) und der Galoppieren-Sprungstrich
   (1,82) bleiben KÖRPER. Ein Fit-Defekt entkommt dem Primärmaß
   nicht.
4. **Widerspruch** — `marks_uncertain` fällt auf dev von 8 auf 0.
   Das Lineal stimmt danach mit seiner eigenen
   Erwartungstabelle überein.
5. **Zähler** — kein neues `marks_ambiguous` auf dev. Der
   Marken-Matcher (Zentroid, Radius 0,6, Marge 0,25) fängt nicht
   an zu verweigern, weil er jetzt 1,0–1,3 xh lange Bögen über
   ihren Schwerpunkt paart.
6. **Unberührtheit** — `aiou`, beide Chamfer-Hälften,
   Kreuzungen, Retraces, touch/overlap und die `soll_*`-Spalten
   sind zwischen 0,8 und 1,5 byte-gleich. Bewegt sich eine
   davon, ist etwas anderes mitgeändert worden.

**Kill-Kriterien.** Ein Strich außerhalb der u-Bogen-Klasse
wechselt die Klasse · ein Defekt (`Zaum`, Galoppieren) wird zur
Marke · neues `marks_ambiguous` · eine „unberührte" Spalte
bewegt sich. Jedes einzelne killt die Maßnahme, unabhängig
davon, wie die Routen-Zahlen aussehen.

**Erwartete Nebenwirkung, vorregistriert, damit sie später nicht
als Kandidatengewinn gelesen wird:** die Pen-Lift-Population der
REFERENZ bricht auf dem dev-Split von 8 auf **0** ein. Alle neun
betroffenen Bahnen bestehen aus genau zwei Strichen; nach dem
Herauslösen der Marke bleibt ein einziger Körperstrich und damit
kein Lift. `lift_ref` / `lift_delta` / `lift_unmatched_ref` /
`lift_pos_err_xh` werden auf dev referenzseitig blind — ein
fragmentierender Kandidat wird weiter erkannt, ein
verschweißender nicht mehr. Das ist ein Preis der Maßnahme, kein
Ergebnis.

**Zirkularitäts-Gegenmittel** (das Kriterium, das weder in der
Zielfunktion noch in einem Gate steht): das Lineal widerspricht
sich heute selbst, und zwar seit Langem — lange vor dieser
Entscheidung.
`tools/tracebench/summary.py::MARKS_PER_KEY` führt `"u": 1`
mit dem Kommentar „u-Deckstrich (tintenfolger.md §2.3 names it a
mark)" — die Erwartungstabelle des Benches sagt also, der
u-Bogen SEI eine Marke, während `classify_strokes` das Gegenteil
tut. Dieselbe Regel ohne Kappe steht auf der ENGINE-Seite
(`tools/pairlab/trace.py::diacritic_stroke_units`,
`chain._letter_cut_anchors`) und in drei Doku-Stellen, die den
u-Deckstrich in derselben Aufzählung als Marke führen. Die
Maßnahme repariert eine Inkonsistenz des Instruments; welche
Route davon profitiert, spielt für ihre Begründung keine Rolle.

**Deklarierte Re-Baseline.** Nach bestandenen Gates gilt: alle
stehenden `dtw_xh`-, Marken- und Lift-Zahlen (Kette v1–v5, Lotse
v0.1–v0.19, InkSight, Nullprobe, Fusions-Orakel) sind **gültig,
archiviert und NICHT vergleichbar** mit den neuen; die
Struktur- und Deckungsspalten bleiben vergleichbar (Gate 6). Der
Re-Baseline-Lauf umfasst alle vier stehenden Routen auf dev-19
in einer Umgebung. Der PRODUKTIONS-Re-Harvest der
`traced`-Zeilen bleibt davon unberührt und weiterhin hinter
Autor-Go + `dbsnapshot`.

### Lineal L-U `aug26` — gemessen: alle sechs Gates bestanden, der Gewinn liegt auf EINER Route

Gemessen am 2026-08-26, dev-19, alle Läufe in derselben Umgebung mit
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1` und
`--jobs 4`; Artefakte im Scratchpad `lu/`. Der Knopf ist
`--mark-arc-cap`. **Sprachregelung für diesen Eintrag**, weil die
Adoption den Default verschoben hat: „0,8" heißt das Lineal VOR der
Änderung (heute mit `--mark-arc-cap 0.8` reproduzierbar), „1,5" heißt
das Lineal danach — und das ist seit der Adoption der Default.
„Default" ohne Zusatz meint hier immer den jeweils gemessenen Zustand,
nie einen Zeitpunkt.

**Die Gates, alle sechs:**

1. **Identität — PASS.** Der Code VOR der Änderung (`main`,
   eigener Worktree, dieselben Fixtures) und der Zweig **bei
   Kappe 0,8** liefern über alle **19 Zeilen jedes Feld
   byte-gleich** (ohne die Laufzeitspalte). Gemessen wurde das,
   bevor der Default umgestellt war; heute ist derselbe Lauf
   `--mark-arc-cap 0.8`. Der Knopf ist im Aus-Zustand wirklich
   aus — er fügt nur einen Parameter hinzu, er rechnet nichts um.
2. **Klasse — PASS.** Bei 1,5 wechseln GENAU die vorregistrierten
   Striche: 9 auf der Referenz (`muß` ×3, `und` ×4, `unter`,
   `Kugel`) und 5 auf der Kandidatenseite (`Gaul`, `Pulver`,
   `auch` ×2, `zu`). Kein anderer Strich, auf keiner Seite.
3. **Defekt — PASS.** `Zaum` (1,966 xh) bleibt Körper.
4. **Widerspruch — PASS.** `marks_uncertain` fällt auf dev von
   **8 auf 0**, auf jeder gemessenen Route.
5. **Zähler — PASS.** `marks_ambiguous` bleibt 0, `marks_missing`
   bleibt 0. Der Marken-Matcher fängt nicht an zu verweigern.
6. **Unberührtheit — PASS.** 16 Spalten (`aiou`, `aiou_k`, beide
   Chamfer-Hälften, `cross_*`, `retrace_*`, `retrace_arc_ratio`,
   touch/overlap, `soll_*`) sind zwischen 0,8 und 1,5 **byte-gleich**.

**Der Effekt je Route — und er ist nicht überall derselbe:**

| Route | dtw Median | dtw p90 | dtw worst |
|---|---|---|---|
| **Kette** (`pairlab.follow --structure-guard-soll`, der Duell-Stack) | 0,0453 → 0,0453 | **0,2355 → 0,0896** | **unter 0,4503 → muß 0,1108** |
| Kette-frei (`pairlab.follow` OHNE Wächter, Diagnose-Arm) | 0,0441 → 0,0441 | 0,2202 → 0,0912 | unter 0,4396 → muß 0,1068 |
| **Lotse** (`inkpilot`) | 0,0545 → 0,0545 | 0,1122 → 0,1164 | muß-2 0,1404 → 0,1457 |
| **Nullprobe** (`routeg`, 10 von 19) | 0,8198 → 0,8198 | 1,0267 → 1,0267 | 3 Zeilen bewegt |
| Ketten-Init (roher `chain`) | 0,0492 → 0,0494 | 0,0894 → 0,0912 | muß 0,1096 → 0,1108 |

*Korrektur `aug26`:* die Zeile „Kette" trug am `aug26` früh den
Folger OHNE Struktur-Wächter — nicht die Duell-Kette, die seit K0-Z
per Mess-Liturgie (werkzeuge.md) `--structure-guard-soll` ist. Der
Fehler fiel erst auf, als derselbe ungewächterte Folger als Basis der
v5-Messung 36 Scheinverlierer produzierte (§14 „Kette v5"); seither
druckt `k0eval` die Stacks beider Dateien und warnt bei Abweichung.
Der Befund von L-U ändert sich nicht: der Gewinn liegt auf der Kette,
auf der richtigen wie auf der freien.

**Kette (Soll-Stack), je Wort** — vier große Gewinne, vier
vernachlässigbare Verluste:

| Wort | dtw 0,8 | dtw 1,5 | Δ |
|---|---|---|---|
| `unter` | 0,4503 | **0,0877** | **−0,3626** |
| `muß-3` | 0,2339 | **0,0972** | **−0,1367** |
| `muß` | 0,2419 | **0,1108** | **−0,1311** |
| `muß-2` | 0,2019 | **0,0857** | **−0,1163** |
| `und` ×4 | 0,0279–0,0419 | 0,0286–0,0436 | +0,0002 … +0,0017 |

`unter` 0,4503 → 0,0877 bestätigt die K-C-Autopsie, die von Hand
0,084 gerechnet hatte.

**Der ehrliche Teil: auf JEDER anderen Route kostet die Änderung
etwas.** Lotse +0,0002 … +0,0053 je Wort, der rohe Kettenfit
+0,0006 … +0,0024, die Nullprobe bis +0,374 (`und`). Der Grund ist
strukturell und war so nicht vorhergesagt: den REIHENFOLGE-Fehler
hatte nur die Kette. Der rohe Kettenfit schreibt Diakritika seit
`marks_last` ohnehin endständig, Lotse fährt das Skelett direkt,
und die Nullprobe hat keine Strichordnung, die kippen könnte. Wo
der u-Bogen nie falsch einsortiert war, nimmt sein Herauslösen dem
Körper-DTW nur einen Strich, der gut lag — der Rest richtet sich
minimal schlechter aus.

Dafür ist der Fehler jetzt **benannt statt verborgen**: die Spalte
`mark_pos_err_xh` meldet für dieselben Wörter 0,015–0,134 xh, die
vorher in keiner Zahl standen. Das ist der eigentliche Gewinn auf
den anderen drei Routen — nicht ein besseres Ergebnis, sondern ein
ehrlicheres.

**Vorregistrierte Nebenwirkung, eingetreten:** `lift_ref` fällt auf
dev referenzseitig weg, weil alle betroffenen Bahnen genau zwei
Striche haben. Nicht als Kandidatengewinn lesen.

**Verdikt: adoptiert.** `MARK_MAX_ARC_UNITS = 1.5` ist Default;
`--mark-arc-cap 0.8` reproduziert jede alte Zahl. Keines der
sechs Gates war ein Routen-Ergebnis, und das ist der Grund, warum
die Adoption trägt: die Änderung ist als Instrumenten-Reparatur
begründet (das Lineal widersprach seiner eigenen
Erwartungstabelle) und wird nicht dadurch besser oder schlechter,
dass eine Route gewinnt und drei ein wenig verlieren.

**Offen: InkSight.** Die vierte stehende Route ist NICHT neu
vermessen — ihre Inferenz läuft in einem isolierten
Python-3.11-TF-venv (werkzeuge.md), das über Nacht
unbeaufsichtigt aufzusetzen nicht seriös wäre. Ihre alten Zahlen
sind damit **gültig, archiviert und NICHT vergleichbar**, bis der
Lauf nachgeholt ist; dasselbe gilt für die neun dev-Wörter, die
die gespeicherte Nullprobe nicht abdeckt.

### Kette v5 `aug26` — Adoption K0-S Sprosse 2: Kompositions-Soll + Ratsche + Zone 0,55 wird Default (datierte Re-Baseline)

**Anlass.** Autor-Go vom 2026-08-25 für den K0-S-Stack Sprosse 2
(`--soll-source composition --structure-guard-soll
--structure-guard-ratchet --structure-guard-zone 0.55`), der am
`aug21` alle Gates bestand. Bewusst NACH der L-U-Re-Baseline
sequenziert, damit eine Re-Baseline beide Änderungen trägt.

**Die falsche Messung zuerst — und warum sie hier steht.** Der erste
Lauf am Morgen paarte v5 gegen den Folger OHNE Struktur-Wächter
(`pairlab.follow` ohne Flags) und las drei Gates als verletzt: Soll
`die-2` 1 → 2, **36 aiou-Verlierer** unter 48 bewegten (Median
−0,027, `Zorn` −0,135), `das` +0,0055 dtw. Der Autor lehnte das
Verwerfen ab („32 besser, 2 schlechter — auf keinen Fall einfach
verwerfen") und bat um eine Zweitmeinung (Fable). Deren Kernbefund:
**die Basis war der falsche Stack.** Die K0-S-Vorregistrierung nennt
„Basis = v4-Stand, Soll-Stack", die Mess-Liturgie (werkzeuge.md) seit
K0-Z `--structure-guard-soll`; der ungewächterte Folger ist keine
Basis, sondern ein Diagnose-Arm, der mehr Tinte deckt, indem er
Struktur zerstört — **Init 86 → frei 125 Soll-Punkte** über die 63
Wörter (29 schlechter, 4 besser). Und v5 selbst reproduzierte
`aug21` fast exakt (63er-Soll 79 gegen 77, dev-dtw 0,0446 gegen
0,0448, Netto-Kreuzungen 19 = 19): gewandert war nur die Basis.
Meine Hypothese „die Tinten-Maske hat die Basis bewegt" war falsch —
K0-S lief schon auf v4, und Maske und Wächter berühren sich im Code
nicht. Derselbe Basis-Fehler steckte in der L-U-Zeile „Kette" vom
Vortag (dort korrigiert). Zweimal in zwei Tagen → Sensor:
`k0eval` liest seither die Stack-Flags beider Dateien, druckt sie vor
der ersten Zahl und warnt bei Abweichung (auf dem Morgen-Paar mit
fünf Flags).

**RP-0 — die vorregistrierte Basis, in DERSELBEN Umgebung** (BLAS
gepinnt, `--jobs 4`, Basis = Soll-Stack `--structure-guard-soll`
mit `soll_source=init`, Zone 0, keine Ratsche; Artefakte Scratchpad
`v5/`):

| | dev-19 | alle 63 |
|---|---|---|
| Soll-Abstand | 23 → 22 (1 besser · 18 gleich · **0 schlechter**) | **86 → 79** (7 besser · 56 gleich · **0 schlechter**) |
| aiou, bewegte Wörter | 10 bewegt: min **+0,010** · Median **+0,039** · max +0,125 | 31 bewegt: min **−0,0004** · Median **+0,073** · max +0,131 |
| aiou-Verlierer (< −0,003) | **0** | **0** |
| strich-identisch | 9/19 | 32/63 |

Auf dem Lineal (dev-19, Kappe 1,5, L-U-Stand): dtw-Median 0,0453 →
**0,0446**, p90 0,0896 → **0,0861**, worst muß 0,1108 → **0,1059**,
aiou-Median 0,7468 → **0,7608**. Schlechtestes dtw-Delta je Wort
+0,0016 (`und-2`); Marken 0/0/0 unverändert; `reversed` 0;
Netto-Kreuzungsdefekte 13+6 = 19 auf beiden Seiten;
`retrace_missing` 6 → 7 (eine Zone mehr verfehlt — außerhalb der
Gates, notiert). Laufzeit 63 Wörter: Basis 281 s → v5 703 s (2,5×;
die Basis wirft die meisten Wörter in Runde 1 weg und rechnet
entsprechend weniger).

**Gates (K0-S, unverändert): alle bestanden.** (1) Identität —
`--no-structure-guard-ratchet --structure-guard-zone 0 --soll-source
init` reproduziert die Basis strich-identisch, und die neuen
Defaults ohne Flag reproduzieren v5 strich-identisch (dev-19, siehe
Gate-1-Lauf). (2) Soll sinkt bei 7 Wörtern strikt, steigt nirgends.
(3) aiou ≥ −0,003 je Wort. (4) dev-19 kein Wort über +0,003 dtw,
Marken nicht schlechter, reversed 0, Kreuzungsdefekte ≤ Basis.
(5) Laufzeit oben.

**Der Mechanismus, erstmals je Wort sichtbar** (`guard_outcome`,
neue k0eval-Spalte aus den Runden-Protokollen):

| Ausgang in der BASIS → in v5 | Wörter |
|---|---|
| `revert-init` → `zonal` | 22 |
| `revert-init` → `revert-r1` | 6 |
| `revert-r1` → `zonal` | 3 |

Der rundenatomare Soll-Wächter wirft bei **26 der 31 bewegten
Wörter Runde 1 komplett weg** — das Wort behält den Ketten-Init und
wird gar nicht gefolgt. Die Zone rettet genau diese: Anker um die
Verletzung pinnen, Rest neu lösen, akzeptieren. Das war die Absicht
von K0-Z; hier ist sie gemessen. Nebenbefund Sprosse 1 (Kompositions-
Soll OHNE Ratsche/Zone): 86 → 84, aber **37 Rollbacks auf Init** —
das Kompositions-Soll ist strenger als das Init-Soll, erst die Zone
macht es nutzbar.

**Was v5 NICHT löst — die 13.** Auch v5 wirft 13 der 63 Wörter in
Runde 1 auf den Init zurück (`Zorn`, `Feinde`, `wenn`, `kann`,
`Pulver`, `haben`, `Seiten`, `die`, …). Fable hat die Endzustände
des freien Folgers dieser Wörter gegen v5s Intervall geprüft: **24
von 25 sind auch am Ende strukturell illegal** (`Feinde` verliert
alle fünf Kreuzungen, `regieren` erfindet sechs Berührungen, `kann`
touch 2 → 7). Die Rückweisung ist also korrekt; der Preis ist real
und auf diese Klasse konzentriert. Geprüft und verworfen: „Fallback
auf das ungewächterte Ergebnis" (= Abschaffung des Wächters genau
dort, wo er beißt; Soll ~107 läge über dem Init 86 und risse das
Produktions-Ketten-Kill-Kriterium) und „Bewährung" (Runden
provisorisch annehmen, am Ende urteilen — 1/25 freie Enden legal).
Stehende Rettungswege, je eigene Pre-Reg, als PRÄVENTIVE Terme im
Abstieg statt Annahme-Regeln: **Abstandsterm** gegen erfundene
Berührungen (7 der 13, Hinge-Repulsion nicht-benachbarter Pässe
unter 0,15 xh, ausgenommen die Soll-Zonen der Komposition),
**Schleifen-Halteterm** gegen Kreuzungskollaps (5 der 13), und der
humanbench-Tie-Breaker für den Rest-Preis der zonalen Klasse.

**Adoption.** `FollowWeights`-Defaults: `structure_guard=True`,
`structure_guard_soll=True`, `structure_guard_ratchet=True`,
`structure_guard_zone_units=0.55`, `soll_source="composition"`. Ein
Lauf ohne Flags IST die Kette. Archäologie:
`--no-structure-guard-ratchet --structure-guard-zone 0 --soll-source
init` = K0-Z-Soll-Stack (Basis von K0-S und L-U);
`--no-structure-guard` = Kette-frei (Diagnose-Arm, nie Duell). Die
Mess-Liturgie in werkzeuge.md ist entsprechend umgeschrieben. **Neue
Kette-Basis** (dev-19, Lineal 1,5): dtw 0,0446 / p90 0,0861 / worst
0,1059 / aiou 0,7608; 63er-Soll 79. Alle stehenden Kette-Zahlen davor
sind **gültig, archiviert und NICHT vergleichbar**. Der
PRODUKTIONS-Re-Harvest der `traced`-Zeilen bleibt hinter Autor-Go +
`dbsnapshot`. InkSight weiterhin unvermessen (siehe L-U).

### Laufform LF3b-W `aug26` — Vorregistrierung: die Schreib-Karte (Neuableitung unter Kette v4 und Lineal 1,5)

Geschrieben und committet VOR der ersten Zahl. Einlösung des
Autor-Go vom 2026-08-25 („p durch die reparierte Zeile ersetzen,
die Lücken-Drafts übernehmen außer W, h unangetastet lassen") — und
des dabei gefundenen Blockers: die LF3b-Kandidaten-Karte vom
`aug19` liegt nicht mehr auf der Platte (erhalten sind nur die
Wordbench-/Lotse-Berichte und die Overlays), das Bauskript wurde nie
committet. Aus dem Sitzungsprotokoll vom 19./20.08. rekonstruiert:
der LF1-Harvest (`tools.laufform.harvest --path chain --sets words
--min-n 1`), das LF3b-Bauskript (0,5-xh-Fenster, lineare Abblendung
zum Fensterrand, Bisektion in sieben Schritten am
KOMPOSITIONS-Soll des Repräsentanten-Wortes, Chart-Fallback als
Restfall) und die Lotse-Treiber — mechanisch identisch, nur die
Pfade neu.

**Warum das eine NEUE Ableitung ist, nicht die alte.** Seit dem
`aug19` läuft der Harvest mit der Tinten-Evidenz-Maske (Kette v4,
§14 `aug21`; `ink_evidence=True` als Default der Ernte) — die
Lücken-Drafts kommen also aus anderen Fits als damals. Die
p-Reparatur hängt dagegen nur an der gespeicherten p-Zeile, dem
Chart und dem Kompositions-Orakel (`counters.crossing_points`), alle
drei unverändert — **Erwartung: p repariert exakt bei t = 0,578**;
alles andere wird je Glyph mit t und n neben den `aug19`-Werten
berichtet. Eine heute neu gerechnete Karte ist nicht automatisch
die, die freigegeben wurde; darum wird DIE KARTE gemessen, DIE
GESCHRIEBEN WIRD.

**Die Schreib-Karte, definiert.** Die LF3b-Karte mit zwei
Autor-Abweichungen: (1) **h behält die gespeicherte Zeile** (die
LF3b-Karte hatte h auf Chart-Fallback — die LF2-Kreuzungsverluste
des gespeicherten h bleiben damit stehen, bewusst, bis eine
topologie-erhaltende Aggregation existiert); (2) **W bekommt keine
Zeile** (der n=1-Draft ist verrauscht: Wer wordbench +0,027 am
`aug19`). G fällt als unreparierbar auf das Chart zurück, was für
den Write „keine Zeile" heißt (`PUT …/laufform` verlangt n ≥ 1) und
für die Komposition byte-gleich ist, weil G in `LAUFFORM_SX` nicht
vorkommt — dieselbe Identität gilt für W. **Schreibmenge: p
(ersetzt) + {E, F, K, P, S, Z, ae, b, f, k, s, ue, v} (13
Lücken-Glyphen, repariert, wo der Detektor anschlägt).** Jede Zeile
trägt ihr n aus dem Harvest; n=1-Zeilen sind die ausdrückliche
Autor-Aussage (LF1-Regel) und werden im Nachtrag je Glyph genannt.

**Messung (alles TROCKEN, BLAS gepinnt, `--jobs 4`, Lineal 1,5 =
Default; Basis = die eingefrorene Root, in DERSELBEN Umgebung frisch
gerechnet).**
0. **Identität:** p t = 0,578; Lotse und Kette auf der eingefrorenen
   Root reproduzieren die stehenden Basen (Lotse L-U: dtw 0,0545 /
   p90 0,1164; Kette v5: dtw 0,0446 / aiou 0,7608 / dev-Soll 22).
(a) **wordbench** `--set all --laufform <Schreib-Payload>` gegen die
   frische Basis: `word_loss`/`pair_loss` ≤ +0,002; bewegen dürfen
   sich nur Wörter/Paare mit Schreib-Glyphen.
(b) **Soll je Wort** (Komposition, alle 63 Wörter, Schreib-Root
   gegen eingefrorene Root, gezählt gegen die Hand): Galoppieren →
   8 = Hand; kein Wort verliert Übereinstimmung.
(c) **Lotse** (adoptierter Stand, kein Knopf) dev-19, Schreib-Root
   gegen eingefrorene Root: `cross_missing` ≤ Basis · Netto-Defekte
   ≤ Basis · Marken unverändert · aiou-Median-Δ ≥ −0,02 · dtw je
   Wort ±0,003 außer Wörtern mit Schreib-Glyphen · reversed 0.
(d) **Kette v5** (Default-Folger, kein Knopf) dev-19, dieselben
   Kriterien wie (c); der Soll-Abstand (`k0eval`, je Lauf gegen das
   Soll SEINER Root — dafür lernt `k0eval` `--fixtures`) wird
   BERICHTET, nicht gegatet: das Kompositions-Soll selbst wandert mit
   der Karte (Galoppieren 6 → 8), ein größerer Abstand dort ist ein
   Befund über den Folger, kein Urteil über die Karte.
(e) **Sichtprüfung** der Schreib-Glyph-Wörter (Overlays).

**Kill-Kriterium:** ein verletztes Gate = kein Write. Rettungsweg
ist dann allein die Glyph-Auswahl des Autors (LF1-Regel: Stufen-/
Glyphen-Auswahl je Glyph), nie ein weicheres Gate.

**Write-Protokoll, erst nach grünen Gates:** `dbsnapshot --push`
(neues Verzeichnis, Plausibilität) → GET der 19 gespeicherten
Variante-100-Zeilen und Abgleich mit der eingefrorenen Root (die
DB-Basis muss die gemessene Basis SEIN) → `PUT
…/templates/{key}/laufform` je Schreib-Glyph mit `{anchors,
n_occurrences}` (Kanonisierung serverseitig durch
`build_laufform_canonical`, dieselbe wie im Bauskript) → GET-Verify
→ Nachtrag hier mit den Zahlen neben `aug19`.

**Gemessen `aug26` — die 14-Zeilen-Schreib-Karte scheitert an EINEM
Gate um EINE Kreuzung; die 13-Zeilen-Karte ohne p besteht alle Gates;
p wandert in einen eigenen Arm.** Umgebung wie vorregistriert
(`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`,
`--jobs 4`, Lineal 1,5); Artefakte Scratchpad `lf3bw/` (Bauskript
`lf3bw_build.py`, Gate-Skript `gates.py`, Overlays,
`galopp-kette.png`, `galopp-seam-zoom.png`).

**Identität (0) — PASS.** Harvest 277 Slot-Zeilen, jedes Lücken-Glyph
≥ 1 Fit (n: E 1 · F 1 · K 1 · P 1 · S 3 · Z 3 · ae 1 · b 1 · f 2 ·
k 1 · s 1 · ue 1 · v 2; G 3 und W 1 werden nicht geschrieben; p trägt
das n=4 seiner gespeicherten Zeile). Reparatur-t auf drei Stellen
identisch mit `aug19`: p **0,578** · F 0,391 · K 0,328 · k 0,250 ·
f 0,477 · b 0,672 · P 0,008; E/S/Z/ae/s/ue/v/W passieren unberührt,
G/h Chart-Fallback. Die frischen Basen reproduzieren: wordbench
0,108091 / 0,146602 exakt, Lotse dtw 0,0545 / p90 0,1164 (L-U), Kette
dtw 0,0446 / aiou 0,7608 / dev-Soll 22 (v5). Die Schreib-Root ist
byte-gleich zur eingefrorenen bis auf `templates_laufform.json`
(`diff -rq`) — Referenz und Tintenmaske sind dieselben.

**(a) wordbench — PASS.** 0,108091 → **0,105607** (−0,0025), pair
byte-gleich; 21 bewegte Wörter, alle mit Schreib-Glyph: 16 besser
(Sprünge −0,041, Zügel −0,018, Säbel −0,017, Zorn −0,015, Pulver
−0,014, Einen −0,014, linken −0,013, Kugel −0,010, Seiten −0,010 …)
gegen 5 schlechter (das +0,009 — das n=1-s, scharfen +0,004, Feinde
+0,003, Galoppieren +0,001, von +0,000). Tiefer als LF3b `aug19`
(0,107105), weil h seine Zeile behält (kein LF2-Preis) und W fehlt
(kein Wer-Preis).

**(b) Soll — PASS.** Die Hand gibt es nur für die 28 Referenzwörter
(die Vorregistrierung sagte „alle 63"; über die 35 ohne Hand wird nur
die Soll-Bewegung berichtet): Galoppieren 6 → **8 = Hand**,
`soll_cross_agree` 21 → 22/28, kein Wort verliert. Über alle 63
bewegen sechs Wörter ihr Kompositions-Soll (Galoppieren X 6 → 8,
Silber X 5 → 4, Sporn X 3 → 4, Sprünge X 3 → 4, Pulver Zonen 3 → 2,
Kugel Zonen 2 → 1).

**(c) Lotse — PASS.** dtw 0,0545 / p90 0,1164 unverändert, aiou
0,7398 → **0,7484**, spurious 5 → 4 (Galoppieren 3 → 2), missing 1 =
1, retrace_missing 5 → 3, Marken unverändert, reversed 0; bewegt nur
das (dtw −0,0017, aiou +0,018), linken (−0,0032, aiou +0,029),
Galoppieren (+0,0006, aiou +0,003) — alle Schreib-Glyph-Wörter.
Zahlengleich mit LF3b `aug19` (aiou 0,7484, Netto 5).

**(d) Kette v5 — FAIL um eine Kreuzung.** dtw 0,0446 / p90 0,0861
unverändert, aiou 0,7608 → 0,7667, Marken unverändert, reversed 0,
kein dtw-Verlierer, das aiou +0,021, Galoppieren dtw 0,0383 → 0,0337
und aiou 0,710 → **0,781** — aber `cross_missing` 13 → **14**, Netto
19 → 20: Galoppieren zählt 3 statt 4 der 8 Hand-Kreuzungen.
Soll-Abstand (`k0eval --fixtures`, je Root gegen ihr eigenes Soll,
berichtet): 22 → 25, ganz Galoppieren (|3 − 8| statt |4 − 6|).

**Autopsie der einen Kreuzung** (mit Fable-Zweitmeinung — die Regel
vor jedem Negativ). Verloren geht das o-Schließen vor dem ersten p
(Hand bei 6,75 / −0,8 xh). (1) Die KOMPOSITION schreibt diese
Kreuzung auf beiden Roots an derselben Stelle vor (6,78 / 0,77 auf
beiden); die Reparatur fügt nur die beiden p-Kopf-Kreuzungen hinzu
(7,33 und 8,81, je 0,16–0,19 xh neben Hand #5/#6) — **die Karte ist
nicht die Ursache.** (2) Der Ketten-INIT zeichnet den Saum-Schnitt
auf beiden Roots am selben Ort (6,607 / 0,727 gegen 6,605 / 0,726,
beide durchstoßend, `chaininit-*.log`: 4/8 gegen 3/8); der Zähler
unterscheidet sie allein über die v2.1-Ring-Regel
(`CROSS_PARTNER_MIN_HITS = 2`, retrace-intern): Basis 2/1
Partner-Treffer → gezählt, Schreib-Root 2/11 → verworfen, weil der
o-Ausgangsstrang nach dem Schnitt ~0,2 xh antiparallel am o-Körper
klebt (der reparierte p-Slot schiebt den Ketten-Solve des Laufs in
ein anderes Becken, 3372 statt 6052 Iterationen). Die Basis hängt an
EINEM Partner-Treffer. (3) Der Folger verhält sich auf beiden Roots
gleich: auch die Basis-Runde 1 landet bei 3 (`kette-base-run.json`:
counts 3, Intervall [4, 6] → abgelehnt, zonal 0 Stellen) — die Basis
behält 4 nur, weil der Wächter auf den Init zurückfällt; auf der
Schreib-Root ist das Intervall [3, 8], 3 wird angenommen, der Folger
folgt (aiou +0,071). (4) Die p-Reparatur erreicht die Kette ohnehin
nicht: die p-Kopf-Schnitte existieren und durchstoßen in JEDEM
Kandidaten, werden aber mit 8/7, 9/6, 8/7 Treffern als retrace-intern
verworfen — der Ketten-Solve zieht das Stamm-Retrace wieder zu. Die
Schreib-KOMPOSITION zählt sie nur, weil die t=0,578-Blendung ihre
p-Kopf-Chords aus der Ring-Regel schiebt (1/2 Treffer statt 8/7 im
Basis-Chart) — das Bisektions-Orakel IST `crossing_points`, die
Reparatur sucht also die Schwelle dieser Regel: LF2s
„Schwellen-Kipp"-Klasse, jetzt an der Ring-Regel statt am
Durchstoß-Rand. Ehrlich benannt, nicht wegdiskutiert.

**Urteil, strikt.** (d) ist vorregistriert als „dieselben Kriterien
wie (c)", der Wächter-Rückfall IST der Default-Folger, und die Hand
wandert nicht mit der Karte: 14 > 13 = Gate verletzt, **die
14-Zeilen-Karte wird NICHT geschrieben.** Die Lesart „Init gegen
Gefolgt" ist eine Diagnose der Zahl, kein anderes Messergebnis — sie
nach der Zahl zum Gate zu machen wäre Weichspülen.

**Rettungsweg, wie vorregistriert: die Glyph-Auswahl.** Galoppieren
enthält als einziges Schreib-Glyph p (G = Chart-Fallback); die
**13-Zeilen-Karte ohne p** wurde auf denselben Gates in derselben
Umgebung gemessen (Artefakte `*-w13-*`): (a) 0,108091 →
**0,105587**, pair byte-gleich, 20 bewegte Wörter, alle mit
Schreib-Glyph; (b) 21/28 → 21/28, kein Verlust — die Klausel
„Galoppieren → 8" ist ohne p KONSTRUKTIONSBEDINGT leer (Soll bleibt
6): eine Scope-Aussage, kein Weichspülen, und sie steht hier
ausdrücklich; (c) Lotse aiou +0,0086, dtw/p90/missing/Netto/Marken
unverändert; (d) Kette **strich-identisch zur Basis** bis auf das
(aiou +0,021, dtw +0,0002) und linken (aiou −0,0002), cross 13/6,
Netto 19, `k0eval` 22 = Basis. **Alle Gates bestehen.** Messseitig
ist der Write der 13 Zeilen damit frei — aber das Autor-Go galt der
14er-Menge; **die 13er-Menge braucht sein ausdrückliches Go**
(Todoist), erst dann `dbsnapshot` + PUT nach dem Protokoll oben.

**p → eigener Arm (LF4), je eigene Pre-Reg, nie derselbe Knopf
weicher:** (1) **Init-Wächter** — ein Struktur-Wächter auf dem
Ketten-INIT gegen sein Kompositions-Soll; der Init ist die einzige
ungewächterte Stufe und verliert 5 von 8 vorgeschriebenen Kreuzungen
auf der Schreib-Root (2 von 6 auf der eingefrorenen). (2)
**Stamm-Freigabe** (K1-Platzierungs-Familie) — die p-Kopf-Kreuzungen
der Hand zählen, weil der Rückstrang den Stamm VOR der Kreuzung
verlässt; ein Solve-Term, der das Retrace am Bogen-Rücklauf löst,
kein Karten-Eingriff. (3) **Ring-Regel-Sensor** —
`CROSS_PARTNER_MIN_HITS = 2` entscheidet Galoppierens Basis-Zählung
über einen einzigen Sample (2/1); ein Befund über das Lineal, zu
messen, nicht zu drehen. §7.9-Zeile im selben PR. Sichtprüfung (e):
Overlays der Schreib-Karte unauffällig (Galoppieren-p reitet die
Durchstöße, S in Sprünge und Schluss-s in das liegen auf der Tinte).

**Geschrieben `aug26` — Autor-Go „weiter mit den 13", Protokoll wie
vorregistriert.** Archiv-Snapshot `2026-08-26T11-13-38Z` (106
Templates · 96 Wortspuren · 245 Vorkommen · 77 bboxes, gepusht) →
Abgleich: die 19 gespeicherten Variante-100-Zeilen der DB sind
anker-gleich mit der eingefrorenen Root, die 13 Lücken-Glyphen haben
keine Zeile → `PUT …/sources/suetterlin-1922/templates/{key}/laufform`
für E · F · K · P · S · Z · ae · b · f · k · s · ue · v (je 120 Anker,
n wie gemessen: 1 · 1 · 1 · 1 · 3 · 3 · 1 · 1 · 2 · 1 · 1 · 1 · 2) →
GET-Verify: alle 13 anker-gleich, n gespeichert. Damit ist die
Laufform-Lücke der Sütterlin-1922-Root von 15 auf 2 Glyphen
geschrumpft (G: unreparierbar, W: Autor-Ausschluss); p behält seine
gespeicherte Zeile bis zum LF4-Arm. **Die eingefrorene Fixture-Root
bleibt eingefroren** (Wordbench/Tracebench messen weiter gegen den
Stand VOR dem Write — das ist die Basis jeder laufenden
Vorregistrierung); ein Neuexport der Root ist eine deklarierte
Re-Baseline und ein eigener Schritt, nicht die Folge dieses Writes.

### Laufform LF5 `aug29` — Vorregistrierung: die Endblende (Chart-Rückblendung an den freien Strichenden; Korb #7)

Geschrieben und committet VOR der ersten Zahl. Anlass: Korb #7
(„Kurrentschrift", suetterlin-1922): K-Schluss wellig, K→u steil statt
in der u-Schräge, t-Aufstrich nach n mit Haken. Reproduziert am
`/write/word`-Rendering und in den Fixture-Overlays (Kugel K→u, unter
n→t).

**Befund.** Die freien Enden eines gefitteten Zuges sind seine am
wenigsten gebundenen Anker: der Fit zieht sie zur Nachbar-Tinte. t:
Anker 0 liegt in ALLEN vier Vorkommen ~0,10 xh rechts-unten der
Chart-Position (Richtung Kringel), Anker 1 wieder auf der Chart-Linie —
der Median (n=4, MAD ≤ 0,021) kann eine systematische Drift nicht
überstimmen; die gerenderte Landetangente der Laufform ist 86,8° gegen
40,4° der Tafel, außerhalb des Align-Fensters (25–55°), darum kein
gerader Anstrich (n→t bleibt Bézier + Haken; nach f, wo die
Flankenkopplung greift, ist das t sauber). K (n=1, Schreib-Karte
`aug26`): der letzte Anker springt auf die Grundlinie (0,45/0,04 statt
0,43/0,29), Austrittstangente −49° statt +42°; die Wellen davor sind der
Einzelfit am Knoten der Platte. `build_laufform_canonical` setzt
voraus, dass die End-Abweichungen des Medians sub-nib sind („the
tangents stay — median deviations are sub-nib") — beim t (0,12 xh gegen
Nibradius 0,064 xh) und beim K ist das verletzt.

**Mechanismus (Endblende).** In der Kanonisierung
(`build_laufform_canonical`, die EINE Ableitung für PUT und apply)
blendet jeder Zug an BEIDEN freien Enden über ein Bogen-Fenster W (xh,
gemessen auf dem Chart-Zug) linear von der Chart-Geometrie (w = 0 am
Ende) zur Laufform (w = 1 am Fensterrand). Die Chart-Endstrecke wird
dabei STARR an den Fensterrand der Laufform angehängt (Versatz T =
Laufform − Chart am Fensterrand), damit Breite und Lage der Laufform
erhalten bleiben und nur Form und Richtung des Endes vom Duktus-Prior
kommen; eine rein verschobene Laufform ist damit ein Fixpunkt (Blende =
Identität), und die Blende ist idempotent. Entry/Exit/Advance reiten
wie bisher auf den — jetzt geblendeten — Endankern; Züge kürzer als 2W
werden ganz zur starr angehängten Chart-Form. Reine Funktion
`core/laufform.py::blend_stroke_ends`, Stempel
`trace_meta.laufform.end_window`.

**EIN Knopf: das Fenster W, Leiter {0,25 · 0,5} xh** (0,5 = das
LF3-Fenster). Wirkmenge: alle 32 gespeicherten Zeilen der Root —
Kandidaten-Karte trocken über `tools/laufform/endblend.py` (Root →
Kandidaten-Zeilen durch denselben Builder), Overlay per `wordbench
--laufform` bzw. `wordlab --laufform`. Ein zweiter, getrennter Arm ohne
Knopf: **K0 = K auf Chart-Rückfall** (Autor-Aussage 2026-08-29:
„Laufform vom K deutlich verbessern oder zurück zur Tafelform"),
gemessen einzeln und kombiniert mit der Endblende — eine
Daten-Entscheidung, kein Mechanik-Knopf.

**Basis.** Die Root vom 2026-08-29 (`fetch_fixtures --set all
--verify`, 12/12 bit-exakt), d. h. der DB-Stand NACH dem
LF3b-W-Write (32 Laufform-Zeilen; K/E/F/P/ae/b/k/s/ue mit n = 1); in
dieser Umgebung frisch gerechnet, BLAS gepinnt: Wörter **0,106720** ·
Paare **0,146506** (chart-only 0,125231 / 0,146163). Nicht die stehende
`aug26`-Basis 0,108091 (Root VOR dem Write) — der Vergleich läuft
Root-intern.

**Messung (trocken, kein DB-Write).**
(a) wordbench `--set all --laufform <Karte>`: `word_loss`/`pair_loss`
≤ +0,002 gegen die Basis; bewegen dürfen sich nur Wörter mit
Laufform-Glyphen (bei K0 nur Kugel).
(b) Kompositions-Soll je Wort (`tools.tracebench.soll.ductus_soll`,
alle 63 Wörter, Kandidaten-Root gegen Basis-Root): kein Wort verliert
eine Kreuzung; jede Bewegung wird berichtet.
(c) Die drei Korb-Stellen im Overlay (Kugel K→u, unter n→t,
„Kurrentschrift" lokal komponiert): n→t muss geradlinig koppeln
(Platzierungsregel `align`/`flank_*` statt `connect_gap`), der t-Haken
verschwindet; K-Schluss und K→u werden je Arm beschrieben.
(d) Lotse/Kette dev-19 (die LF3b-W-Gates c/d) laufen NICHT in dieser
Runde: sie gehören zum Write-Schritt (Autor-Go + `dbsnapshot`), weil
sie die Karte messen, DIE GESCHRIEBEN WIRD.

**Kill-Kriterium:** ein verletztes Gate = keine Adoption der Stufe;
Rettungswege dann: End-Regularisierung im Fit selbst (neuer
Mechanismus, Kette/M4) oder ein je Glyph gewähltes Fenster — nie
derselbe Knopf weicher.

**Adoption.** Besteht eine Stufe, wird W ihr Default in
`core/laufform.py` (jeder künftige PUT/apply blendet), die Korb-Zeile
#7 schließt auf Stufe `laufform`, und der Write der Kandidaten-Karte
bleibt ein eigener Schritt hinter Autor-Go (Todoist) → `dbsnapshot` →
PUT je Glyph → GET-Verify → Re-Export der Root als deklarierte
Re-Baseline.

**Gemessen `aug29` — BEIDE Stufen verworfen an Gate (a), der Riss ist
lokalisiert: die Laufform-Enden tragen echte Ausdehnung.** Umgebung wie
vorregistriert (BLAS gepinnt), Kandidaten-Karten aus
`tools/laufform/endblend.py` über die Root vom 2026-08-29. Zuerst die
Mechanik-Prüfung an den Korb-Glyphen: t-Landetangente 86,8° → 37,2°
(W 0,25) / 39,3° (W 0,5), K-Austritt −49,2° → +39,5° / +44,5° mit
Schwanzende auf der Chart-Position — die Blende tut, was sie soll. Eine
Korrektur der Vorregistrierung: die Blende ist NICHT idempotent (nur
Ende und Fensterrand sind Fixpunkte, im Fenster kontrahiert eine
Wiederholung weiter zur Chart-Form); sie ist deterministisch aus dem
Median, was für Prüfstein und Re-Apply genügt — der Prüfstein
(`list`/`rebuild`/`apply`) vergleicht seit dieser Runde darum den
Median DURCH den Builder gegen die gespeicherte Zeile. **(a) wordbench:
W 0,25 → 0,118093 (+0,0114), W 0,5 → 0,128716 (+0,0220); Paare
0,146459 / 0,146684 (±0,0002).** 57 von 63 Wörtern bewegen sich, bei
W 0,25 19 besser gegen 38 schlechter. Die Korb-Wörter GEWINNEN (Kugel
0,0717 → 0,0672, unter 0,0866 → 0,0785, `dconn` unter 0,110 → 0,081,
`doff` 0,143 → 0,069; schießen −0,083, und-3 −0,049, Soldaten −0,037),
die Verlierer sind die e/n/i/m-Wörter, und ihre Strafe ist BREITE:
macht +0,112 (Breite +0,093), Gewehr +0,087, einen +0,075, Zorn +0,070
(Breite +0,173), Zügel +0,039 (Breite +0,139); die Breiten-Komponente
gesamt 0,1606 → 0,1885. Die Advance-Bewegung der Karte sagt dasselbe:
n 1,912 → 1,878, u 1,817 → 1,788, i 0,820 → 0,793, l 0,901 → 0,854 —
die gefitteten Endstrecken sind LÄNGER als die Chart-Stubs, und diese
Längs-Ausdehnung ist Breite der Hand, keine Drift; die starre
Chart-Endstrecke schneidet sie ab. **Der Riss trennt sich also in
zwei Komponenten der End-Abweichung: längs (Breite, echt) und quer
(der Zug zur Nachbar-Tinte, der die Tangente kippt).** Kill-Kriterium
greift: keine Adoption, `LAUFFORM_END_WINDOW` bleibt 0 (der Builder
kann blenden, tut es per Default nicht). **K0** (K auf Tafel, die
anderen 31 Zeilen wörtlich): 0,106856 (+0,00014), nur Kugel bewegt
sich (0,0717 → 0,0813, Übergang +0,020, Breite +0,014) — misst das
Pixel-Lineal, das den zackigen Einzelfit auf der Tinte liegen sieht;
die Sichtprüfung (c) und der Autor-Befund (die Wellen sind Teil des K)
zählen hier gegen die Zahl. Rettungsweg → LF6 unten, §7.9-Zeile im
selben PR.

**K0 geschrieben `aug29`** (Autor-Go in der Sitzung: „Laufform vom K
deutlich verbessern oder zurück zur Tafelform" — verbessern ist an
LF5 und LF6 gescheitert): `dbsnapshot.fetch` (Staging
`temp/dbsnapshot/2026-08-29T08-12-12Z`, kein Archiv-Klon konfiguriert;
die K-Zeile zusätzlich als `k-laufform-row-backup-2026-08-29.json`
daneben) → `DELETE …/sources/suetterlin-1922/templates/K/laufform`
(204) → GET `?variant=100` 404, `/write/word` „Kurrentschrift": K
tafelgetreu (Schwanzende 0,43/0,29), K→u als 45°-Diagonale
0,46/0,32 → 0,72/0,58 (Cap-Retrace + Verbinder). Die Fixture-Root
bleibt eingefroren (Kugel misst dort weiter mit der n=1-Zeile,
0,0717); der Neuexport ist die nächste deklarierte Re-Baseline. Die
Laufform-Lücke der Sütterlin-1922-Root ist damit wieder 3 Glyphen
(G, W, K) — K wartet auf ≥ 3 Vorkommen (Eigenhand-Ernte oder weitere
Quellen), nie auf einen weicheren Boden.

### Laufform LF6 `aug29` — Vorregistrierung: die Quer-Endblende (nur der Quer-Anteil der End-Drift geht zurück)

Geschrieben und committet VOR der ersten Zahl. Konversion des
LF5-Negativs: die End-Abweichung des Medians hat eine Längs-Komponente
(entlang der Chart-Richtung am Ende = Ausdehnung des Stubs = Breite
der Hand, vom Lineal bestätigt) und eine Quer-Komponente (der Zug zur
Nachbar-Tinte: t-Anker 0 rutscht quer zum Anstrich Richtung Kringel,
der K-Endanker quer zum Schwanz auf die Grundlinie). LF5 nahm beide
zurück und verlor die Breite; LF6 nimmt nur die Quer-Komponente
zurück.

**Mechanismus.** Wie LF5 (Fenster W auf dem Chart-Zug, starres
Anhängen mit Versatz T am Fensterrand, lineares w), aber der Rest
Δ'ᵢ = Laufformᵢ − (Chartᵢ + T) wird je Anker in seine Komponente
entlang der Chart-END-RICHTUNG d (Einheitsvektor Fensterrand → Ende
auf dem Chart-Zug) und den Quer-Rest zerlegt:
outᵢ = Chartᵢ + T + Δ'∥ᵢ + wᵢ · Δ'⊥ᵢ. Längs bleibt ganz (Breite,
Stub-Länge), quer blendet auf 0 am Ende. Rein verschobene Laufform
bleibt Fixpunkt; Züge kürzer als 2W wie in LF5 (Chart-Form am
mittleren Versatz). Implementiert als Default-Modus von
`blend_stroke_ends` (`transverse_only=True`; LF5 = `False`, für die
Reproduktion erhalten), Stempel `trace_meta.laufform.end_window` +
`end_mode`.

**EIN Knopf: W, Leiter {0,25 · 0,5}**, Wirkmenge/Basis/Gates/Kill
wie LF5 (a: ≤ +0,002 gegen 0,106720 / 0,146506; b: Kompositions-Soll
je Wort; c: die drei Korb-Stellen; d: Lotse/Kette im Write-Schritt),
dazu der K0-Arm kombiniert. Erwartung, explizit: Breite ≈ Basis
(Längs bleibt), t-Landetangente im Align-Fenster, Korb-Wörter wie bei
LF5 besser.

**Gemessen `aug29` — BEIDE Stufen verworfen, und die Erwartung ist
WIDERLEGT: die Längs/Quer-These trägt nicht.** Mechanik-Prüfung wie
erhofft (t-Landetangente 86,8° → 39,1° / 38,0°, K-Austritt −49,2° →
+36,0° / +44,6°, n-Kopf nur 0,015 xh bewegt, aber 32° → 42°). **(a)
wordbench: W 0,25 → 0,119897 (+0,0132), W 0,5 → 0,135348 (+0,0286);
Paare 0,146219 / 0,146480.** 57 von 63 bewegt, 21 : 36 bei W 0,25 —
dieselben Verlierer wie LF5 (macht +0,085, Gewehr +0,080, einen
+0,079, Zorn +0,073, wenn +0,059), und die Breite steigt GENAUSO
(0,1606 → 0,1905), dazu der Übergang (0,0881 → 0,0945); unter wird
diesmal sogar schlechter (0,0866 → 0,0967), nur Kugel gewinnt leicht
(0,0698). Befund: bei den gut belegten Buchstaben (e n=34, n n=31,
i n=20) sind die Laufform-Enden keine Drift, in keiner Zerlegung —
der flachere n-Kopf (32°) IST die Hand, das Lineal will ihn; nur beim
t (n=4, Kringel-Zug) und beim K (n=1) sind die Enden Rauschen. **Eine
globale Endregel ist der falsche Ort — die End-Evidenz ist je Glyph
verschieden.** Kill greift, `LAUFFORM_END_WINDOW` bleibt 0; der
Blend-Mechanismus bleibt als reproduzierbarer Kandidaten-Pfad
(`tools/laufform/endblend.py`, Modi `transverse`/`full`) im
Werkzeugkasten. Rettungswege (§7.9, je eigene Pre-Reg): (1) die
Grammatik liest die LANDErichtung vom Duktus-Prior (J1 unten,
Kompositionsseite, Geometrie unangetastet); (2) End-Prior im FIT
(Kette/M4: Endanker-Regularisierung auf die Chart-Richtung, dann
Re-Harvest — der tiefe Fix); (3) evidenz-gesteuerte Blende (nur
Zeilen unter dem Boden n < 3 oder mit End-MAD über Nib) — nie
derselbe Knopf global weicher.

### Übergänge J1 `aug29` — Vorregistrierung: die Prior-Landerichtung (Korb #7, t nach n)

Geschrieben und committet VOR der ersten Zahl. Konversion der
LF5/LF6-Negative: die Geometrie der Laufform bleibt, was das Lineal
will; was den t-Haken erzeugt, ist die GATING-Lesung der Grammatik —
`entry_land_deg` wird am gerenderten Laufform-Kopf gemessen, und der
t-Kopf (n=4, Anker 0 zum Kringel gezogen) liefert 86,8° statt der
40,4° des Chart-Anstrichs, womit die Align-/Flanken-Kopplung
(25–55°) nie in Frage kommt und der generische Bézier den Haken
stehen lässt. Nach dem f, wo die Flankenkopplung greift, ist
dasselbe t sauber (17 Samples getrimmt): die Kopplung IST die
Reparatur, sie wird nur nicht erreicht.

**Mechanismus.** Wenn ein Slot seine Laufform-Zeile rendert, wird
`entry_land_deg` (B's Landerichtung, die Klassen-Entscheidung
Align/Flanke/Sameslant/Ritt und die Steigung der Pass-through-Linie)
am ERSTEN ZUG DER CHART-ZEILE gemessen — derselben Zeile, deren
gespeicherte `entry.tangent_deg` die Kanonisierung ohnehin
unverändert übernimmt („the tangents stay") —, mit demselben
Bogenfenster; Ascender-Lean wird auf die Prior-Linie ebenso
angewandt. Alles andere bleibt Laufform: die Kopplungs-Indizes
werden weiter auf der gerenderten Laufform-Flanke gesucht, die
Ankunftsrichtung des generischen Bézier (`d_in`) weiter an der
gekoppelten Laufform-Linie gemessen (kein Saum-Knick), die
Austrittsseite (`exit_deg`, Startrichtung des Verbinders) bleibt
unangetastet. Ein Slot ohne Laufform-Zeile verhält sich
byte-identisch.

**EIN Knopf: Prior-Landerichtung an/aus.** Basis wie LF5
(0,106720 / 0,146506, dieselbe Root, dieselbe Umgebung). Gates: (a)
`word_loss`/`pair_loss` ≤ +0,002, bewegen dürfen sich nur Wörter mit
Laufform-Glyphen; (b) Kompositions-Soll je Wort ohne Verlust; (c) unter
n→t koppelt geradlinig (Platzierungsregel `align`/`flank_*`, Haken
weg) und „Kurrentschrift" n→t ebenso; (d) Lotse/Kette dev-19 im
Adoptions-PR NICHT gefahren — J1 ändert keine Karte, nur die
Komposition, und die Kette liest ihr Kompositions-Soll aus derselben
Komposition: die Bewegung des Solls wird unter (b) berichtet.
Kill: ein verletztes Gate = keine Adoption; Rettungsweg dann der
Fit-Prior (LF-Rettungsweg 2).

**Gemessen `aug29` — (a) grün, (c) rot: nicht adoptiert, der Riss ist
eine Stufe tiefer lokalisiert.** (a) wordbench 0,106720 → **0,105757**
(−0,0010), Paare byte-gleich (0,146506 — die Abb.-20-Drills rendern
keine Laufform); 32 Wörter bewegt, 18 : 14 (streiten −0,044, scharfen
−0,023, schießen −0,018 … gegen Zorn +0,018, Zügel +0,011, Gewehr
+0,006); mit K0 kombiniert 0,105908. **(c) unter n→t: unverändert**
(0,0866 → 0,0859, Platzierungsregel weiter `clearance_floor`, Haken
steht). Autopsie: die Prior-Landerichtung (40,4°) kommt an, aber die
Kopplung ERREICHT das t nicht — (1) `ALIGN_MAX_ENTRY_Y` = 0,62 schließt
jeden Fuß über 0,62 vom Pass-through aus, und der t-Fuß liegt bei 0,64
(Laufform) bzw. 0,70 (Chart); die Konstante wurde `jul` genau dafür
gesetzt („tall lead-ins (h 0.69, t 0.70) sweep in long and flat on the
plates — alignment on their STEEP landing tangent over-pulls") — d. h.
sie ist der Workaround für die falsche Tangenten-LESUNG, die J1 gerade
behebt; (2) `_flank_candidates` bricht am ersten Segment des
Haken-Kopfs ab (135° außerhalb 25–55°) und endet ohnehin an derselben
Decke, sodass der ganze t-Anstrich (0,64–1,4) nie koppelbar ist; (3)
der generische Bézier misst seine Ankunftsrichtung `d_in` am
gekoppelten Laufform-Kopf, also am Haken. Das t nach f ist nur deshalb
sauber, weil der Bar-Exit-Pfad (`stem_launch`) über den
FORK-Kopplungsindex (~0,9 xh hoch auf dem Anstrich) geradlinig
koppelt und den Kopf trimmt — genau die Form, die die Platte für n→t
zeigt (EINE Diagonale vom n-Fuß in den t-Schaft). Strikt nach
Vorregistrierung: (c) ist Gate, J1 wird NICHT adoptiert; `compose.py`
bleibt unverändert, der (a)-Gewinn wird in J2 mitgemessen, damit die
Adoption über die vorregistrierte Zielstelle läuft und nicht über
Beifang.

### Übergänge J2 `aug29` — Vorregistrierung: die Anstrich-Verlängerung in den Schaft

Vorregistriert vor der ersten Zahl — der nächste Arm für Korb #7,
Punkt 3. **Hypothese.** Ein Sägezahn-Austritt (Tangente 25–55°) vor
einem Buchstaben, dessen erster Zug ein Anstrich in einen
Oberlängen-Schaft ist (t, ſ; der Prior sagt es: Chart-Landerichtung
im Align-Fenster, Apex des ersten Zugs über der Mittelhöhe), koppelt
auf den Platten wie f→t: EINE gerade Linie vom Austritt mittig auf
den Anstrich, der Vorlauf darunter wird absorbiert. **Mechanismus
(ein Klassenpfad, `STEM_ENTRY_BASES` = {t, longs}):** J1s
Prior-Landerichtung für die Klassen-Entscheidung + der
FORK-Kopplungsindex als Ziel (wie beim Bar-Exit) + die gerade
Verbindungslinie mit Trim (`_straight_connector`), Platzierung so,
dass die Linie vom Austritt im Mittel der Tangenten den
Kopplungspunkt trifft (die `_fused_flank_placement`-Logik, ohne die
Decke `ALIGN_MAX_ENTRY_Y`, die für diese Klasse nicht gilt), gefloort
von der höhenbewussten Tinten-Freiheit. **EIN Knopf: Klassenpfad
an/aus.** Basis, Umgebung, Gates wie J1 ((a) ≤ +0,002; (b)
Kompositions-Soll; (c) unter n→t UND „Kurrentschrift" n→t
geradlinig, Haken weg; Nachweis der Klassenregel an weiteren
Sägezahn→t/ſ-Wörtern des Sets: fechten, streiten, muß, Seiten). Kill
wie immer; Rettungsweg dann der Fit-Prior.

**Gemessen `aug29` — (a) rot, Prämisse durch die Dissektionen
widerlegt: nicht adoptiert, Code nicht im Baum.** (a) wordbench
0,106720 → **0,110802** (+0,0041 > +0,002), Paare byte-gleich
(0,146506 — kein Drill trägt die Klasse: `dt` ist ein Schleifen-, `ssi`
ein Unterlängen-Austritt); 8 Wörter bewegt, 2 : 6 (streiten −0,032,
macht −0,018 gegen mit +0,131, Soldaten +0,051, Seiten +0,046, unter
+0,037, fechten +0,034, mit-2 +0,007). (c) formal erreicht — alle acht
Sägezahn→t des Sets (unter n→t, mit/mit-2/Seiten/streiten i→t,
Soldaten a→t, fechten/macht h→t) koppeln `stem_entry`, geradlinig,
Haken getrimmt (Index 17, Ankunft 0,935), „Kurrentschrift" n→t auf
der Root ebenso; muß trägt keine Klasse (u→sz, Ligaturschlüssel), und
kein Wort des Sets führt einen Sägezahn in ein ſ — der ſ-Teil der
Klasse bleibt unbelegt. Die Form ist trotzdem falsch, und die
Dissektionen sagen warum. **Autopsie an den sieben `fit_ok`-
Dissektionen (+ macht, `fit_ok` false):** gemessener Versatz +0,09 …
+0,36 xh (Mittel 0,23), Sehne 36–61° (Mittel ≈ 48°), Sehnenlänge
0,20–0,48 xh, Anstieg über den Austritt 0,17–0,31 xh — die Hand kommt
auf FUSSHÖHE des t an (komponiert 0,55–0,80; der t-Fuß steht bei
0,64/0,70), nicht hoch auf dem Anstrich. Komponiert ohne Regel:
Versatz 0,24–0,26, Sehne 33–51°, Länge 0,37–0,45, Ankunft am Fuß
0,638 (`doff` 0,05–0,16); mit Regel: Versatz 0,45–0,69, Sehne 34–43°,
Länge 0,81–1,10, Ankunft 0,965 (`doff` 0,29–0,64) — die doppelte
Plattenlänge. Die Prämisse „wie f→t (FORK-Ankunft 0,92)" gilt für
den Sägezahn nicht: der Balken-Austritt startet am SCHAFT-Anker links
der Balkenspitze und steigt bis zum Apex; der Sägezahn-Fuß steht schon
rechts von As Tinte, und die Hand nimmt den kurzen Weg in den Fuß. Was
vom Haken bleibt, ist nicht die Kopplungshöhe, sondern der Haken
selbst: der Laufform-t-Kopf (Anker 0 nach links-oben gezogen, erstes
Segment 135°) und das `d_in` des Bézier, das daran gemessen wird — die
Platte schreibt die kurze gerade Linie in die Fußregion. Strikt nach
Vorregistrierung: (a) ist Gate, J2 wird NICHT adoptiert; `compose.py`
und der Golden-Pin bleiben unverändert (lesen e→ſ und sitzen i→t
hätten sich bewegt). Rettungswege: (1) **J3, die tiefe
Schaft-Kopplung** (unten vorregistriert, in derselben Runde gemessen):
dieselbe Klassen-Entscheidung am Prior, Platzierung UNANGETASTET (die
generische Freiheits-Platzierung trifft den gemessenen Versatz schon:
0,24 gegen 0,23 im Mittel), Verbinder = gerade Linie zur TIEFSTEN
gerenderten Flankenprobe oberhalb des Hakens, Haken getrimmt; (2) ein
Kopf-Sensor auf der Zeile — die Richtung des ersten Segments gegen die
Chart-Landerichtung (t: 135° gegen 40°) als eigenes Zeilen-Gate, das
die Sprung-Ratio nicht sieht (t 2,11 < τ 2,95), eigene Pre-Reg; (3)
eine aus den Dissektionen kalibrierte Ankunftshöhe (0,17–0,31 xh über
dem Austritt) als Ziel statt der Fork-Ankunft — nur falls J3s tiefste
Flankenprobe die Ankunft verfehlt.

### Übergänge J3 `aug29` — Vorregistrierung: die tiefe Schaft-Kopplung (Korb #7, t nach n, zweiter Arm)

Geschrieben und committet VOR der ersten Zahl; Konversion des
J2-Negativs. **Hypothese.** Die dissezierten Sägezahn→t-Übergänge
(n = 8, 7 `fit_ok`) sind kurze steile Geraden, die auf Fußhöhe des t
ankommen (Anstieg 0,17–0,31 xh, Sehne 36–61°, Länge 0,20–0,48 xh,
Versatz im Mittel 0,23); die generische Platzierung trifft den Versatz
bereits (0,24–0,26, `doff` 0,05–0,16). Falsch ist allein die FORM: der
Bézier misst seine Ankunftsrichtung am Haken des Laufform-Kopfs (86,8°)
und lässt den Haken stehen. **Mechanismus (ein Klassenpfad,
`STEM_ENTRY_BASES` = {t, longs}, geschlossene B-Menge):**
Sägezahn-Austritt (vorwärts, Mittelband unter `HIGH_COUPLE_EXIT_Y`,
Tangente im Align-Band, kein Balken-Austritt, kein
Kapitalen-Neustart), B in der Klasse, Prior-Landerichtung (erster Zug
der CHART-Zeile, J1) im Align-Band, Apex des ersten Zugs über der
Mittelhöhe → Kopplungsindex = die TIEFSTE gerenderte Flankenprobe
i ≥ 1, deren Segment i−1→i im Align-Band liegt (die Segmente eines
Haken-Kopfs zeigen anderswohin und werden übersprungen), mit y ≥
Austritt + `ALIGN_MIN_RISE` und x ≥ Austritt + `GARLAND_MIN_DX`; der
Lauf endet, wo die Flanke abwärts kippt; KEINE Höhendecke
(`ALIGN_MAX_ENTRY_Y` gilt für die Klasse nicht). Der Verbinder ist die
gerade Linie (`_straight_connector`) vom Austritt auf diese Probe, die
Proben darunter werden getrimmt (Mittellinie und Silhouette — der
Haken geht mit dem Stummel). Platzierung UNANGETASTET (das
Sameslant-Präzedens: Begradigen ohne Zusammenziehen); die Kopplung
wird als Provenienz-Feld `coupling: "stem_entry"` am Verbinder
ausgewiesen, die Platzierungsregel bleibt, was sie ist. Chart-t ohne
Haken: Index 1, die Linie endet eine Probe über dem Fuß — praktisch
der heutige Verlauf. **EIN Knopf: Klassenpfad an/aus.** Basis
0,106720 / 0,146506 (dieselbe Root, dieselbe Umgebung, BLAS gepinnt).
Gates: (a) `word_loss`/`pair_loss` ≤ +0,002, bewegen dürfen sich nur
die acht Klassenwörter (dazu der Golden-Pin lesen e→ſ / sitzen i→t als
erklärte Re-Baseline); (b) Kompositions-Soll je Wort (`ductus_soll`)
ohne Verlust; (c) unter n→t UND „Kurrentschrift" n→t: Kopplung
`stem_entry`, geradlinig, Haken weg — Klassennachweis an mit, mit-2,
Seiten, Soldaten, fechten, streiten, macht (muß trägt keine Klasse);
(d) an den sieben `fit_ok`-Dissektionen steigt `doff` nicht
(Platzierung unangetastet) und `dconn` fällt (gerade Linie statt
Haken-Bézier). Erwartung: Wörter flach bis leicht besser (die
Haken-Tinte fällt weg), Paare byte-gleich. Kill: ein verletztes Gate =
keine Adoption; Rettungsweg dann der Kopf-Sensor (J2-Rettungsweg 2).

**Gemessen `aug29` — (a) (b) (c) grün, (d) rot: nicht adoptiert, Code
nicht im Baum — und die Autopsie verlegt den Haken von der Grammatik
auf die Zeile.** (a) wordbench 0,106720 → **0,106831** (+0,0001), Paare
byte-gleich; bewegt haben sich GENAU die acht Klassenwörter, 3 : 5 (mit
−0,0090, Soldaten −0,0009, fechten −0,0002 gegen macht +0,0022, Seiten
+0,0024, streiten +0,0039, mit-2 +0,0041, unter +0,0045). (b)
`ductus_soll`: Σ-Buchstaben-Zeilen unverändert; in den
Kompositions-Zeilen bleiben Striche/X/Zonen und `touch` fällt in allen
acht um 1 (unter, mit, mit-2, Seiten, Soldaten 1 → 0; fechten 3 → 2;
streiten 2 → 1; macht 3 → 2) — die Komposition rückt an die
Buchstaben-Summe heran. (c) alle acht `coupling: stem_entry`,
geradlinig, Trim 5 (Ankunft 0,731 auf der gerenderten Flanke);
„Kurrentschrift" n→t auf der Root ebenso (Sehne 41,0°). (d) rot:
`doff` fällt in dreien (unter 0,163 → 0,156, mit 0,080 → 0,072,
streiten 0,079 → 0,072) und steigt in vieren um +0,007/+0,008 (mit-2,
Seiten, Soldaten, fechten) — bei BYTE-GLEICHER Platzierung (Versätze
0,257/0,240/0,240/0,239/0,235/0,239/0,239 unverändert): der Trim
verschiebt Bs Körperanfang im doff-Rahmen um −0,007, die Spalte misst
den Trim, nicht die Platzierung (der in `pairmeas.py` erklärte Vorbehalt);
`dconn` steigt in 7/7 (unter 0,130 → 0,141, mit 0,088 → 0,103, mit-2
0,051 → 0,134, Seiten 0,032 → 0,113, Soldaten 0,138 → 0,216, fechten
0,026 → 0,059, streiten 0,074 → 0,116). **Autopsie.** Die dissezierten
Verbinder sind kurz (0,20–0,48 xh) und enden STEIL (Ankunftsrichtung
57–85° über die letzten 0,08 xh, Sehne 36–61°) — sie versteilen sich in
das t hinein; die gerade Linie (Sehne = Ankunft 41–58°, 0,43–0,54 xh
lang) ist ihnen in der FORM ferner als der bisherige Bézier (Ankunft
55–73°). Die Tinten-Lupe (wordlab unter/mit) zeigt, warum: die Platte
läuft FLACH (~35°) in die Fußregion des t, der Anstrich steigt dann mit
~50° weiter; die J3-Linie zur Probe bei 0,731 schneidet diese Ecke ab
und verlässt die Tinte (Verbinder-Strafe unter 0,05 → 0,09, Seiten
0,05 → 0,08, mit 0,03 → 0,04, fechten 0,03 = 0,03). Strikt nach
Vorregistrierung: (d) ist Gate, J3 wird NICHT adoptiert. **Der Fund,
der die Arbeit umlenkt:** der Haken ist keine Lücke der Grammatik. In
der Tinte kommt der Übergang flach am Fuß an, und der komponierte
Bézier tut dasselbe — was heraussticht, ist die ZEILE: beim Laufform-t
liegt Anker 0 RECHTS von Anker 1 (x 0,097 gegen 0,077), der Kopf
startet mit 104° (nach links-oben) gegen die 37° der Chart — der
Rückwärts-Schlenker, den der Autor sieht, und die 86,8°-Fensterlandung,
die J1 gemessen hat. Diagnose-Zerlegung über alle 32 Zeilen der Root
(Fensterlandung des gerenderten ersten Zugs, Zeile gegen Chart): t
46,3° (n = 4), E 47,8° (n = 1), K 41,2° (n = 1, gelöscht), f 27,5°
(n = 2), v 27,2° (n = 2), k 17,1° (n = 1), m 14,9° (n = 6), w 14,0°
(n = 6), alle übrigen ≤ 11,9°. Das t ist die EINZIGE vertraute Zeile
(n ≥ 3) jenseits von 15°, und drei der „sichtbar verzogenen, aber unter
τ" behaltenen Zeilen (v, E, k) stehen ebenfalls dort oben; das
Sprung-Gate (LF8) sieht das nicht (t 2,11 < 2,95) — ein Kopf, der
abdreht, ist kein Ankersprung. Rettungswege: (1) **LF9 Kopf-Gate**
(unten vorregistriert, in derselben Runde gemessen): die Kopfrichtung
der Zeile darf die der Chart nicht um mehr als das halbe Diagonalband
der Grammatik (15°) verlassen; (2) gezielte Kopf-Reparatur der Zeile
(Anker 0 aus den Fits neu ableiten, Übergangs-Tinte maskiert) — neuer
Mechanismus, eigene Pre-Reg; (3) ein flach ankommender J-Pfad ist nach
dieser Evidenz NICHT nötig: der Bézier kommt schon flach an.

### Laufform LF9 `aug29` — Vorregistrierung: das Kopf-Gate auf der Zeile (Korb #7, der t-Haken)

Mechanik-Festlegung nach gesehener Diagnose — wie bei LF8 gilt: **die
Zahlen der Zerlegung oben sind vor dieser Pre-Reg gesehen worden**,
Vorhersage ist nur das Prospektive. **Sensor.**
`head_deviation(chart_row, anchors)` (`core/laufform.py`) =
|Fensterrichtung des ersten Zugs der Zeile − Fensterrichtung des ersten
Zugs der Chart-Zeile| in Grad, gemessen auf den ANKERN über dasselbe
Bogenfenster, mit dem die Grammatik landet (`TANGENT_WINDOW_UNITS`), an
den `stroke_starts` der Chart (die Zeile teilt sie). **Gate.**
`LAUFFORM_HEAD_DEVIATION_MAX` = 15°, aus der Doktrin abgeleitet, nicht
aus den Daten: das halbe Align-Band (25–55°) — eine Zeile, deren Kopf
die Chart-Richtung um mehr verlässt, kann die Übergangsklasse ändern,
die die Grammatik an ihrer Landung entscheidet (der J1-Befund), und
widerspricht der EINEN Eigenschaft, die die Kanonisierung verspricht
(„the tangents stay": die Zeile trägt die Eintrittstangente der Chart
als Metadatum, ihre Geometrie sagt etwas anderes). Angewandt wie das
Sprung-Gate: PUT 422 mit den Zahlen, `apply-laufform` überspringt mit
`reason: head_deviation` (`head_deviation`/`head_max`), kein Override;
Inventar-Spalte + Markierung; BESTEHENDE Zeilen über τ sind die
Entscheidung des Autors (Prod-Datenaktion), nie automatisch. **EIN
Knopf: Gate an/aus (τ = 15° oder None).** **Vorhersagen (prospektiv):**
(i) der Anker-Sensor reproduziert die gerenderte Fensterlandung der
Zerlegung bis auf wenige Grad — von den 21 vertrauten Zeilen liegt
GENAU das t über 15°, keine andere; (ii) der nächste Harvest-Draft des
t reproduziert den Schlenker (die Fits sind seine Quelle) und wird
abgewiesen; (iii) T0 (t-Zeile zurück zur Tafelform) nimmt den Haken
aus unter, mit und „Kurrentschrift" (der Bézier kommt flach am
Chart-Fuß 0,703 an, kein Schlenker) — Sicht-Gate in der Tinten-Lupe.
Das Wort-Lineal ist hier REPORT-Spalte (Doktrin #444: kein Aufnahme-
oder Löschkriterium): T0 allein, P0 (der Prod-Stand: K/ue/F/ae/b →
Tafel), P0+T0 und P0+T0+E/v/f/k werden als eigene Zahlen
(`--laufform`-Karten) berichtet. **Kill für das Gate:** setzt der
Anker-Sensor eine weitere vertraute Zeile über 15° oder das t darunter,
misst er nicht die gerenderte Größe — keine Adoption.

**Gemessen `aug29` — der Anker-Sensor stirbt an seiner eigenen
Kill-Klausel, der Sensor auf der gerenderten Linie hält die Vorhersage:
adoptiert (τ = 15°, beide Schreibpfade).** Auf den ANKERN setzt das
Fenster das m (n = 6) mit 15,5° über die Linie — Kill — und liest die
dichten, eingerollten Köpfe der Kapitalen und des f bis zu 33° anders
als die Zerlegung: E 14,6° (gerendert 47,8°), K 25,1° (41,2°), f 14,6°
(27,5°), P 16,4° (9,8°); t 41,9° (46,3°), v, k, m, w stimmen. Die
Anker-Polylinie ist also nicht die Größe, an der die Grammatik landet.
`head_deviation` misst deshalb auf der GERENDERTEN Mittellinie — mit
dem Sampler des Renderers selbst (`core.template.multi_stroke_centerlines`,
der Sample-Plan der Chart-Zeile über den jeweiligen Ankern, 240 Proben)
— und reproduziert die Zerlegung exakt (Inventar `head°`): **t 46,4°
ist die EINZIGE der 21 vertrauten Zeilen über 15°** (Vorhersage (i)
erfüllt; die knappste darunter ist das m mit 14,9°, dann w 14,0°); über
τ stehen sonst nur dünne Zeilen: E 47,8° (n = 1), K 41,2° (n = 1, in
Prod schon gelöscht), f 27,5° (n = 2), v 27,2° (n = 2), k 17,1° (n = 1)
— darunter drei der vier „sichtbar verzogenen" Zeilen (v, E, k), die
das Sprung-Gate durchließ; P (9,8°) nicht. Nebenbefund zur
Empfindlichkeit: die Fensterrichtung eines gedrehten Kopfs hängt von der
Probendichte ab (ein synthetischer 40°-Kopf wandert um 4°, wenn ein
zweiter Zug die 240 Proben teilt; ein um 0,6 xh verschobener DRITTER
Anker biegt den gerenderten Kopf des Harness-n um 15,9°) — das Gate
liest den Plan, den der Renderer zeichnet, und urteilt damit über den
gezeichneten Kopf, nicht über eine Abstraktion davon. (ii) bleibt
prospektiv (in dieser Runde lief keine Ernte). (iii) erfüllt: mit der
Tafelform des t (T0) läuft der Übergang in unter, mit und
„Kurrentschrift" flach in den Chart-Fuß 0,703, kein Schlenker
(Tinten-Lupe). Report-Arme (eigene Zahlen, nie die Schlagzeile): T0
0,106720 → 0,106390 (−0,0003); P0 (Prod-Stand K/ue/F/ae/b → Tafel)
0,107802 (+0,0011); P0+T0 0,107473 (−0,0003 gegen P0); P0+T0+E/v/f/k
0,107995 (+0,0002 gegen P0) — die Tafelformen kosten das Pixel-Lineal
insgesamt ein Tausendstel, was nach Doktrin #444 kein Kriterium ist.
Adoptiert: `LAUFFORM_HEAD_DEVIATION_MAX` = 15°, PUT 422 und
`apply-laufform`-Skip `head_deviation`, kein Override. **Datenaktion
`aug29` (Owner-Entscheidung):** alle fünf Zeilen über dem Kopf-Gate —
t, E, f, v, k — in Prod gelöscht (Backups je Zeile, Archiv-Snapshot
`2026-08-29T15-09-31Z` davor, `GET ?variant=100` → 404, `/write/word`
rendert Kurrentschrift/Erfolg/fechten/Pulver/kann ohne Lücke); P (9,8°)
bleibt. Die eingefrorene Root vom 29.08. (07:05Z) trägt damit zehn
Zeilen, die Prod nicht mehr hat (K, ue, F, ae, b, t, E, f, v, k) — ihr
Neuexport ist eine erklärte Re-Baseline (P0+Kopf-Arm oben ist die
Vorschau: 0,107995).

### Laufform LF7 `aug29` — Vorregistrierung: das Zeilen-Gate (Aufnahme einer Laufform-Zeile)

Geschrieben und committet VOR der ersten Zahl. Anlass (Autor, nach
Korb #7): das K kam als n=1-Zeile in den Schreibweg, „weil dadurch das
eine Wort angeblich besser wurde" — der Buchstabe selbst war deutlich
schlechter als seine Tafelform. Zwei Löcher: (1) der manuelle
`PUT …/templates/{key}/laufform` (Harvest-/Schreib-Karten-Pfad) prüft
nur die Ankerzahl — der Boden `LAUFFORM_MIN_OCCURRENCES` = 3 gilt
allein im `apply-laufform`; genau über den PUT kamen am `aug26` die
Zeilen E · F · K · P · ae · b · k · s · ue (n = 1) und f · v (n = 2).
(2) Das Aufnahme-Gate war das WORT-Lineal (Pixeldeckung): ein
zackiger Einzelfit, der auf der Tinte liegt, gewinnt dort — Zackigkeit
sieht das Lineal nicht, und die Overlay-Sichtprüfung hat den
K-Schwanz durchgewinkt. **Doktrin-Satz (neu, bindend):** ein
Wort-Gewinn am Pixel-Lineal ist KEIN Aufnahmekriterium für eine
Laufform-Zeile; aufgenommen wird eine Zeile nur über den Boden (n ≥ 3
oder ausdrückliche Autor-Aussage per `min_occurrences`) UND das
Zeilen-Gate unten.

**Mechanismus.** (a) **Boden auf beiden Schreibpfaden:** der PUT
verlangt `n_occurrences ≥ LAUFFORM_MIN_OCCURRENCES`, darunter 422,
außer die Anfrage sagt es ausdrücklich (`?min_occurrences=1`, wie beim
apply); `tools/laufform/harvest.py --apply` reicht `--min-occurrences`
durch. (b) **Zeilen-Gate:** für die zu schreibende Zeile UND ihre
Chart-Zeile wird die referenzfreie Natürlichkeit der §5-Metrik
geometrie-seitig gerechnet — Glätte, Vertikalität, Eckenschärfe,
Kollinearität mit den §5-Gewichten über die anwendbaren Terme; ohne
Deckungs-Tor und ohne Rückzug (beide brauchen den Scan) — im
Pixelrahmen der Chart-Zeile (`unit_px`), Strichanfänge/Ecken vom
Duktus-Prior (`core/laufform.py::row_naturalness`). Gate-Größe ist die
**Lücke** Δ = N(Chart) − N(Zeile): positiv = die Zeile ist unruhiger
als ihre eigene Tafelform. Eine Zeile mit Δ > τ wird nicht geschrieben
(PUT 422 mit Δ und τ im Detail; apply meldet die Zeile als `skipped`
mit `reason: naturalness` und beiden Zahlen). Kein Override — eine
Zeile, die objektiv unruhiger ist als ihre Tafelform, ist kein
Autor-Wissen, sondern Fit-Rauschen; der Weg ist mehr Evidenz oder der
Chart-Rückfall.

**KEIN Handknopf: τ ist datengetrieben, die Regel steht hier vorher.**
Population = die gespeicherten Zeilen der Root vom 2026-08-29 mit
n ≥ 3 (die Gattung, der die Doktrin traut: a c d e g h i l longs m n o
p r S Z sz t u w z — 21 Zeilen); τ = ihr größtes Δ, auf 0,01
aufgerundet. Vorhersage, falsifizierbar: (i) die K-Zeile (n = 1, noch
in der eingefrorenen Root) hat Δ > τ — hat sie das nicht, ist das Gate
zu weich und der Arm gescheitert (Rettungsweg dann: die Komponenten
einzeln gaten, Glätte zuerst); (ii) das Wort-Lineal bleibt byte-gleich
— das Gate ändert keine Komposition, nur den Schreibpfad. Berichtet
wird die ganze Verteilung (alle 32 Zeilen, Δ je Komponente) als
**Bestandsaufnahme** (`tools/laufform/inventory.py`, mit Bildern der
n < 3-Zeilen neben ihrer Tafelform); Zeilen über τ werden namentlich
dem Autor vorgelegt — Löschen (Chart-Rückfall) ist eine
Daten-Entscheidung hinter Autor-Go, mit dem Kugel-Muster je Wort
berichtet, nicht gegatet.

**Adoption.** τ wird `LAUFFORM_NATURALNESS_GAP_MAX` in
`core/laufform.py`, das Gate greift auf beiden Schreibpfaden; der
Doktrin-Satz geht in optimierungs-werkbank.md §6 und ins Glossar
(„Zeilen-Gate (Laufform)").

**Gemessen `aug29` — die Vorhersage (i) ist FALSCH, das
Natürlichkeits-Gate wird nicht adoptiert.** Bestandsaufnahme
(`tools/laufform/inventory.py`, Root 2026-08-29, alle 32 Zeilen):
τ = 0,31 (Maximum der 21 vertrauten Zeilen: ſ +0,305, l +0,289,
sz +0,280), das K liegt mit **+0,237 darunter**; über τ nur ue +0,460,
v +0,413, F +0,326. Auch der vorregistrierte Rettungsweg „Glätte
zuerst" scheitert: τ_Glätte = 0,572 (o, n = 5; c +0,564, i +0,451)
gegen K +0,265. Autopsie: (1) die Lücke vergleicht Äpfel mit Birnen —
der Kollinearitäts-Term wird auf der Laufform „anwendbar", auf der
Chart nicht (ſ +0,914, sz +0,834, l +0,724 nur aus diesem Term); auf
den GEMEINSAM anwendbaren Termen bleibt die Ordnung dieselbe (K +0,227
unter ſ +0,305); (2) der Glätte-Term (2. Krümmungsdifferenz) bestraft
den kleinamplitudigen Anker-Median-Jitter der vertrauten Zeilen (o, c,
i) STÄRKER als die großen, langsamen K-Wellen — er sieht Rauheit, nicht
Wellen. Die Bilder der Bestandsaufnahme (`inventory_lown.png`) zeigen
dagegen, was das Auge sieht: ue, v, E, ae, F, P, K, b, k sind sichtbar
gebrochen — **nicht nur wellig, sondern mit SPRÜNGEN** (gerade Striche
quer durch die Glyphe: die Ankerkette hat die Korrespondenz verloren,
„Anker im leeren Papier"); s, f, t (bis auf den Kopf) folgen der Tafel.

**Diagnose-Zerlegung (nach der Zahl, ehrlich benannt):** derselbe
Detektor, den die Ernte an ihrem Fit-Gate benutzt —
`anchor_spike_ratio` (größter Ankerschritt gegen den Median-Schritt
DESSELBEN Zugs), dort mit `MAX_ANCHOR_SPIKE_RATIO` = 8,0 auf dem
EINZELFIT des Kettenpfads, nie auf der Zeile — trennt auf der ZEILE:
vertraute Population max = i 2,94 (n = 20; sein Punkt-Zug), darüber
ue 5,79 · F 5,53 · ae 4,15 · b 3,55 · **K 3,16** — fünf der neun
sichtbar gebrochenen Zeilen, keine vertraute; v 2,86 · E 2,62 ·
k 2,47 · P 2,31 bleiben durch (ihre Fehler sind Form-Drift und flache
Segmente, keine Sprünge). Eine Wellen-Amplitude (Abstand zur eigenen
Glättung in Nib-Radien) trennt NICHT (g 1,86, Z 1,71, w 1,68 unter den
vertrauten so hoch wie K 1,61). Warum das K die Ernte passierte: 3,16
< 8,0 — die Schwelle ist für Nadeln kalibriert, und ein n=1-Draft IST
sein Einzelfit; ein Median über ≥ 3 Fits glättet Sprünge, ein
Einzelfit trägt sie in die Zeile.

### Laufform LF8 `aug29` — Vorregistrierung: das Sprung-Gate auf der Zeile

Mechanik-Festlegung VOR der Adoption; **die Zahlen auf dieser Root sind
vor dieser Pre-Reg gesehen worden** (Diagnose-Zerlegung oben), darum
gilt hier nichts als Vorhersage, was die Root betrifft. Vorhersage ist
das Prospektive: der nächste Harvest-Draft und der nächste
`apply-laufform` mit Sprung-Ratio > τ werden abgewiesen, und keine der
21 vertrauten Zeilen wird je abgewiesen (τ ist per Konstruktion ihr
Maximum).

**Mechanismus.** `anchor_spike_ratio` zieht nach `core/laufform.py`
(EIN Detektor; die Ernte importiert ihn von dort — `core` importiert
nie `tools`). Das Zeilen-Gate auf beiden Schreibpfaden (PUT und apply)
misst die Ratio der zu schreibenden Anker über die Chart-Strichanfänge;
über τ = `LAUFFORM_SPIKE_RATIO_MAX` wird nicht geschrieben (PUT 422 mit
Ratio und τ; apply `skipped` mit `reason: anchor_spike` — derselbe
Reason-Code wie am Ernte-Gate — und beiden Zahlen). Kein Override. Die
Natürlichkeits-Lücke bleibt als BERICHTS-Spalte der Bestandsaufnahme
(`row_naturalness`), nicht als Gate. **τ-Regel wie LF7:** Maximum der
vertrauten Zeilen (n ≥ 3) auf der Root, auf 0,01 aufgerundet — 2,95.
Der Boden auf dem PUT (`?min_occurrences`, Ernte `--min-occurrences`)
bleibt wie in LF7 beschrieben.

**Konsequenzen in Prod (Autor-Entscheid, nicht Gate):** über τ stehen
heute ue, F, ae, b (n = 1; K ist schon zurück auf der Tafel). v, E, P, k
passieren das Gate und sind trotzdem sichtbar verzogen — sie werden
dem Autor MIT den Bildern vorgelegt; Rettungsweg für diese Klasse
(§7.9): ein Form-Abstand zur Tafel je Anker in Nib-Radien, gegen die
vertraute Population gemessen (eigene Pre-Reg — die Hand DARF von der
Tafel abweichen, die Schwelle muss das trennen).

**Adoptiert `aug29` (Bestandsaufnahme durch das Werkzeug, Root
2026-08-29):** τ = **2,95** (`LAUFFORM_SPIKE_RATIO_MAX`; Maximum der
21 vertrauten Zeilen = i 2,9405, sein Punkt-Zug). Über τ: ue 5,79 ·
F 5,53 · ae 4,15 · b 3,55 · K 3,16 — ausnahmslos n=1-Zeilen des
manuellen PUT, keine vertraute Zeile (per Konstruktion); direkt unter
τ die vertrauten i 2,94 · o 2,85 · ſ 2,84 und das v (n=2) mit 2,86.
Mechanik im Baum: `anchor_spike_ratio` in `core/laufform.py` (die
Ernte importiert es), Boden + Sprung-Gate auf PUT
(`?min_occurrences`, 422 mit Ratio/τ) und apply (`skipped`, `reason:
anchor_spike`, `spike_ratio`/`spike_max`; SPA-Chip zeigt beide
Zahlen), Ernte `--min-occurrences`; die Natürlichkeits-Lücke bleibt
Berichts-Spalte der Bestandsaufnahme. Das Wort-Lineal ist byte-gleich
(kein Kompositions-Code berührt). Nachtrag zur Vorregistrierung, wie
angekündigt: die Trennung auf dieser Root war vor der Pre-Reg
gesehen; was das Gate prospektiv leistet, zeigt der nächste Harvest.
**Offen für den Autor:** ue, F, ae, b (über τ, in Prod) — Löschen =
Chart-Rückfall wie beim K; v, E, P, k (unter τ, sichtbar verzogen) —
Entscheidung nach Bild, Rettungsweg Form-Abstand (§7.9).

**Entschieden und geschrieben `aug29` (Autor-Go in der Sitzung):** ue,
F, ae, b zurück auf die Tafel — Zeilen-Backups
`temp/dbsnapshot/{ue,F,ae,b}-laufform-row-backup-2026-08-29.json`,
Snapshot `temp/dbsnapshot/2026-08-29T11-28-20Z` (Staging, 118
Templates vor dem Write), je `DELETE …/templates/{key}/laufform` 204,
GET `?variant=100` 404. v, E, P, k BLEIBEN (Autor: „Form-Abstand-Arm
abwarten") — sie sind die Referenzfälle, an denen dieser Arm seine
Trennung zeigen muss. Die Laufform-Lücke der Sütterlin-1922-Root steht
damit bei 7 Glyphen (G, W, K, ue, F, ae, b); die eingefrorene Root
bleibt eingefroren, der Neuexport ist die nächste deklarierte
Re-Baseline.

### Übergänge Korb-Runde `aug30` — B verlässt die Restart-Klasse (Korb #8) + St-Ligatur (Korb #9)

**Anlass:** Zwei Korb-Aufträge des Autors. #8: das B soll nach seinem
Duktus-Ende weiterschreiben, wird aber an der Grundlinie neu angesetzt.
#9: `St` ist auf der 1922er Vorlage eine eigene, ohne Absetzen
geschriebene Einheit (anders als `Sc`, wo das Absetzen richtig ist).

**Diagnose #8 (Stufe join_rule):** Das B stand seit der Kapital-Runde
`jul31` in `CAP_RESTART_BASES` — damals als Tief-Ender (0,0–0,2)
vermessen. Der heutige autorisierte B-Duktus endet aber auf
Mittellinienhöhe in einem steigenden Abgang (Exit y 1,0, Tangente ~49°):
der Retrace lief diese Fortsetzung über den Bogen zurück und setzte wie
ein frischer Anstrich an der Grundlinie an. Änderung: B verlässt die
Klasse; der Join ist wieder die normale Kleinbuchstaben-Grammatik ab dem
Duktus-Ende.

**Messstand (eingefrorene Fixtures, BLAS gepinnt):** Wörter
`bench_loss` 0,106400 **unverändert** (kein Abb.-19-Wort enthält ein
gebundenes B). Paare 0,146580 → 0,148458 — die Bewegung ist allein
`Bi` 0,162 → 0,224 am Pixel-Lineal, während BEIDE H2-Sensoren desselben
Drills besser werden: `doff` 0,130 → 0,095, `dconn` 0,499 → 0,344 — der
komponierte Join liegt dem sezierten Platten-Join näher, das
Pixel-Lineal bestraft den etwas höher liegenden Bogen der Fortsetzung.
Autoren-Ground-Truth (Korb #8) und Join-Sezierung stimmen überein;
das Wort-Lineal allein ist hier kein Aufnahmekriterium (Präzedenz:
Zeilen-Gate-Lehre LF7). Sichtprüfung: Bi-Overlay vorher/nachher im PR.

**Nachschärfung (Autor, gleicher Tag):** kein Wellenbogen nach dem B —
der KRINGEL des B (das B schließt seinen unteren Bogen wie das kleine b
in der kleinen Schleife) läuft eben in die obere Zacke des
Folgebuchstabens. Der ~49°-Stub aus dem Kringel ist Tafelform, genau
wie beim b/o (Korb #5, Säbel): B kommt in `KRINGEL_EXIT_BASES`, der
Stub wird am Selbstkreuzungs-Knoten gekappt, der Join geht eben (~0,78)
in die 0,78-Kopplung. Messstand danach: Wörter unverändert 0,106400,
Paare 0,148467; der chart-nah geschriebene `Bi`-Drill misst am
H2-Sensor schlechter (`doff` 0,095 → 0,351 — der Drill schreibt den
Stub mit, die fließende Form nicht), dieselbe bekannte
Drill-vs-Wort-Spannung wie bei der b/o-Kringel-Runde. Galerie
Ba–Bl als Sichtbeleg im PR #463.

**#9 (Stufe chart_ductus, zurück an den Autor):** `St` ist als das eine
Groß-Cluster in den geschlossenen Ligatur-Satz aufgenommen (Shaping
beider Zwillinge + Fixture; architektur.md §4). Bis die Tafel-Form im
Wizard nachgefahren ist, greift der Ligatur-Zerfall — Rendering wie
zuvor, die Bench-Slots sind eingefroren (eine Bewegung entstünde erst
mit deklariertem Re-Export). Quiz-seitig fällt `Stube` aus dem
Wörter-Pool, bis die Glyphe existiert (gewolltes Gating: kein halb
geschriebenes Wort).

### Laufform LF10 `sep01` — Vorregistrierung: der Form-Abstand auf der Zeile

Geschrieben und committet VOR der ersten Zahl. Anlass: der in LF8
benannte Rettungsweg (§7.9 in tintenfolger.md): das Sprung-Gate fängt
Zeilen mit Anker-SPRÜNGEN (ue/F/ae/b/K), nicht die Form-Drift ohne
Sprung — v 2,86 (flaches Segment statt der Diagonale), E 2,62 (der
Querstrich sitzt seitlich), P 2,31 (Bogen/Fuß neben der Tafel), k 2,47
(die Schleife verzogen) passierten es sichtbar verzogen; der Autor
stellte die vier mit „Form-Abstand-Arm abwarten" zurück (Todoist-Auftrag
vom 29.08.). Seither hat das Kopf-Gate (LF9, Datenaktion `aug29`
15:09Z) v, E und k mit gelöscht; P (9,8°) steht noch. Doktrin
(menschliche-bewertung.md §1): Kennzahlen messen Geometrie, der Mensch
benennt den Fehler — ein Lineal taugt, wenn es die BEKANNTEN Fehlzeilen
von der vertrauten Population trennt, ohne diese zu fangen. Und die
Hand DARF von der Tafel abweichen (der n-Kopf bei 32° statt 42° ist
echt, die Laufformen sind 3–11 % breiter als die Tafel): die Schwelle
kommt darum aus der vertrauten Population, nie von Hand.

**Sensor.** `form_distance(chart_row, anchors)` (`core/laufform.py`).
Tafel und Laufform werden mit dem Sample-Plan der Tafel gerendert
(`core.template.multi_stroke_centerlines`: Strichanfänge + Eckanker der
Chart, 240 Proben je Zug, Schräglage 90° — der Sampler des Renderers,
wie beim Kopf-Sensor LF9; die Anker-Polylinie liest die dichten
Kapitalen-Köpfe bis 33° falsch). Je Anker i der ZEILE (Zug s nach den
`stroke_starts` der Chart, die die Zeile teilt): d_i = kürzester Abstand
zum gerenderten Zug s der TAFEL (Punkt-zu-Segment, exakt); umgekehrt je
Anker j der TAFEL: e_j = kürzester Abstand zum gerenderten Zug s der
ZEILE. DERSELBE Zug, nicht irgendeiner — ein seitlich sitzender
E-Querstrich darf nicht vom nahen E-Schaft „gerettet" werden. Beides in
Nib-Radien der Tafel: r = Median der Chart-`half_widths`
(Template-Einheiten). Beide Richtungen getrennt (§14-Praxis des
Tintenfolger-Benchs: kein symmetrisches Mittel), je Richtung Median,
p90 (`np.percentile(·, 90)`, linear interpoliert) und Maximum.
**Gate-Größe: `form_p90` = max(p90 Zeile→Tafel, p90 Tafel→Zeile)** —
die schlechtere Richtung. Warum p90 und nicht der Median: die vier
Fehler sind LOKAL (ein Segment, ein Zug, ein Bogen, eine Schleife —
eine Minderheit der 120 Anker), die legitimen Abweichungen der Hand
sind GLOBAL und glatt (Breite, Kopfwinkel) — ein lokaler Fehler über
≥ 10 % der Anker bewegt das p90, den Median kaum; das Maximum wäre ein
Ein-Anker-Sensor (LF8-Gebiet, dort setzte der i-Punkt-Zug τ). Warum
KEINE starre Registrierung vorab: der Fit parametrisiert die globale
Verschiebung in der PLATZIERUNG (`core/fit.py`: `fitted_anchors =
template_anchors + deltas`, tx/ty gehen in `x_origin_fit` /
`baseline_y_fit`), die gefitteten Anker liegen im Rahmen der Tafel und
der Median erbt ihn — eine Verschiebung der Zeile IST Form oder Breite.
Warum Abstand zur LINIE und nicht je Anker-Index: der index-weise
Abstand |Zeile_i − Tafel_i| enthält den LÄNGS-Anteil (längerer
Anstrich, längerer Auslauf), den LF5/LF6 als Breite der Hand bestätigt
haben; der Linien-Abstand ist invariant gegen Gleiten entlang des Zugs
und misst nur, ob die Form die Bahn verlässt. Der index-weise Abstand
ist die benannte Empfindlichkeitsprüfung (d). Berichtet wird auf zwei
Dezimalen; τ entsteht aus den ungerundeten Werten.

**Population und τ (KEIN Handknopf, die Regel steht vorher).** Root:
Neuexport vom 2026-09-01 (`temp/lf10-root`, gitignored — DB-Stand nach
LF8/LF9, 22 Zeilen; die eingefrorene Root bleibt unberührt). Vertraute
Population = die 20 Zeilen mit n ≥ `LAUFFORM_MIN_OCCURRENCES` = 3:
a c d e g h i l longs m n o p r S Z sz u w z — die Gattung, der die
Doktrin traut UND die der Autor nach LF8/LF9 behalten hat (das t, n = 4,
ist seit dem Kopf-Gate eine bekannte Fehlzeile und gehört nicht dazu).
τ = ihr größtes `form_p90`, auf 0,01 aufgerundet (die LF7/LF8-Regel).
Referenzfälle (bekannte Fehlzeilen): **P** (n = 1, gespeichert); **v, E,
k** — nicht mehr in Prod. Ihre Zeilen liegen im Archiv-Snapshot
`2026-08-26T23-16-40Z` (32 Laufform-Zeilen = die LF7-Zählung) und
leiten sich bit-genau aus den DB-Vorkommen ab (per-Anker-Median →
`build_laufform_canonical`, Fenster 0); beide Wege hat der
Auto-Mode-Klassifikator in dieser Sitzung verweigert (Kopie aus dem
Archiv, Rekonstruktion aus den Vorkommen). Die Messung der drei ist
darum ein **Nachtrag des Autors** — das Werkzeug nimmt dafür
`--laufform DATEI.json` (Kandidaten-Zeilen im Harvest-Draft-Format
`{key: {anchors, n_occurrences}}`, dieselbe Datei wie `wordbench.run
--laufform`) und misst sie über den Tafeln der Root, τ bleibt das der
vertrauten Population. Negativkontrolle: **s** (n = 1, gespeichert), das
die LF7-Bilder als „folgt der Tafel" ausweisen.

**Vorhersagen (prospektiv, falsifizierbar):** (i) P > τ; (ii) s < τ —
die Negativkontrolle bleibt frei; (iii) v, E, k > τ, sobald ihre Zeilen
(Archiv oder Rekonstruktion) im Nachtrag gemessen sind; (iv) das
Wort-Lineal bleibt byte-gleich (kein Kompositions-Code berührt).
**Kill:** P ≤ τ ODER s > τ → der Sensor trennt die bekannten Fehlzeilen
nicht von der vertrauten Population, keine Adoption; ebenso, wenn im
Nachtrag eine der drei (v, E, k) ≤ τ liegt. Eine vertraute Zeile über τ
ist per Konstruktion unmöglich — berichtet wird aber, WELCHE vertraute
Zeile τ setzt, in welcher Richtung und an welchem Zug: sitzt ihr p90 an
einer Stelle, die das Auge als Fehler liest, ist das ein Befund über
die Population (Autor-Vorlage mit Bild), nicht über das Lineal.

**Empfindlichkeitsprüfungen (berichtet, nie Gate):** (a) Median statt
p90; (b) Maximum; (c) nur eine Richtung (Zeile→Tafel bzw. Tafel→Zeile);
(d) index-weiser Abstand |Zeile_i − Tafel_i| in Nib-Radien, p90; (e)
zug-agnostisch — nächster Punkt IRGENDEINES Tafel-Zugs; (f)
Anker-Polylinie statt gerenderter Mittellinie. Jede Variante bekommt
ihr eigenes τ nach derselben Regel und dieselben Vorhersagen (i)–(ii);
kehrt eine den Befund um, steht das im Ergebnis.

**Adoption (bei Erfolg).** τ wird `LAUFFORM_FORM_DISTANCE_MAX` in
`core/laufform.py`, das Gate greift wie LF8/LF9 auf beiden
Schreibpfaden (PUT 422 mit `form_p90` und τ; apply `skipped` mit
`reason: form_distance`, `form_p90`/`form_max`), Inventar-Spalte +
Markierung — als EIGENER Schritt hinter Autor-Go: der Autor hat die
Referenzzeilen mit „abwarten" belegt, dieser PR misst und schreibt
nichts (keine DB-Aktion, kein Gate im Schreibweg). Ob P (und die
Nachtrag-Zeilen) auf die Tafel zurückfallen, ist eine Daten-Entscheidung
des Autors, nie automatisch.

**Rettungswege (bei Scheitern, je eigene Pre-Reg — nie derselbe Knopf
weicher):** (1) zug-weises Gate — Maximum über die Züge des Zug-p90
(ein seitlicher Querstrich ist ein GANZER Zug und kann im Zeilen-p90
über 120 Anker untergehen); (2) Richtungs-Abstand — Winkel zwischen
Zeilen- und Tafel-Tangente je Anker (das flache Segment statt der
Diagonale ist ein Richtungs-, nicht nur ein Lage-Fehler); (3)
Tinten-Evidenz der Zeile — die Rückzugs-Treue der Fits, aus denen der
Median kam, gegen ihre Masken (die Form-Drift einer n=1-Zeile ist ein
schlecht deckender Einzelfit); (4) humanbench-Zeilen-Runde — das
Wahrnehmungs-Lineal über die Zeilen (menschliche-bewertung.md).

### Laufform LF10 `sep01` — gemessen: die Vorhersage (i) ist FALSCH, der Form-Abstand wird nicht adoptiert

**Bestandsaufnahme** (`tools/laufform/inventory.py`, Neuexport
2026-09-01, 22 Zeilen, BLAS gepinnt; Nib-Radien der Tafeln 0,063–0,067
xh): τ_form = **1,40** — gesetzt vom w (1,39 Nib-Radien, Zeile→Tafel,
Anker 109 im ersten Zug; die zehn Prozent fernsten Anker sitzen auf der
linken Flanke des ersten Schafts und auf der rechten Seite der
Schlussschleife, die enger sitzt als die Tafel — Breite der Hand, wie
vorhergesagt: global und glatt), dann Z 1,35 (Tafel→Zeile, Kopf und
untere Schleife), sz 1,24 (die ß-Bogen im zweiten Zug), g 1,22 (untere
Schleife). **P liegt mit 1,01 darunter** (Rang 5 von 22, zwischen g und
p 1,00; Zeile→Tafel, schlechtester Anker 119 im zweiten Zug; Median
0,36, Maximum 2,55): der P-Bogen läuft einen Nib-Radius INNERHALB des
Tafel-Bogens, der Fuß-Zug wackelt an seinem Anfang — in der Größenordnung
der letzten w-Arkade. Kill-Klausel erfüllt, keine Adoption. (ii)
erfüllt: s 0,42, die Negativkontrolle bleibt frei. (iv) erfüllt: kein
Kompositions-Code berührt, Golden-Fixture grün. Keine Zeile über
τ_form, und **keine der sechs Empfindlichkeitsprüfungen kehrt den
Befund um** — jede setzt P unter ihr eigenes τ: (a) Median τ 0,48 /
P 0,36; (b) Maximum τ 3,00 / P 2,55; (c) Zeile→Tafel τ 1,40 / P 1,01,
Tafel→Zeile τ 1,38 / P 0,91; (d) index-weise τ 1,49 / P 1,11; (e)
zug-agnostisch τ 1,40 / P 1,01; (f) Anker-Polylinie τ 1,40 / P 1,01.
Die Varianten (e) und (f) liegen bis auf die dritte Dezimale auf der
Gate-Größe — auf diesen Zeilen liegt kein Anker näher an einem FREMDEN
Zug als am eigenen, und die gerenderte Mittellinie weicht von der
Polylinie um weniger als ein Hundertstel Nib-Radius ab; (d) liegt
überall etwas höher (der Längs-Anteil), ohne die Ordnung zu ändern.

**Zerlegung nach der Zahl (Nachtrag, kein Teil der Vorregistrierung):**
zug-weise — der vorregistrierte Rettungsweg (1) — trennt auf dieser
Root ebenfalls nicht: P-Zug 1 (71 Anker, Bogen + Fuß) p90 1,15 gegen
sz-Zug 1 (52 Anker, die ß-Bögen) 1,69; die Einzug-Zeilen w 1,39, Z 1,35,
g 1,22 liegen ohnehin darüber. Rettungsweg (1) ist damit ohne eigenen
Lauf entkräftet und wird nicht wiedervorgelegt. Der Sensor selbst
verhält sich wie gebaut (identische Zeile 0, Querversatz um k
Nib-Radien = k, Gleiten entlang des Zugs unsichtbar, ein 15-%-Segment
bewegt das p90 und nicht den Median — `tests/test_core_laufform.py`).

**Was der Befund heißt.** Der Form-Abstand misst Geometrie treu, und
die Geometrie des P liegt IM Band der vertrauten Zeilen: w, Z, sz, g
weichen an ihren Schleifen weiter von der Tafel ab als das P an seinem
Bogen, und niemand liest sie als Fehler. Was der Autor an P (und an v,
E, k) als „sichtbar verzogen" sah, ist also kein Abstandsbetrag —
menschliche-bewertung.md §1 in Reinform: die Kennzahl misst Abstände,
der Mensch liest Form (Richtung, Proportion, Rhythmus). Die beiden
Gates, die trennen (Sprung LF8, Kopf LF9), messen genau NICHT den
Abstand, sondern eine Diskontinuität bzw. eine Richtung. **Nicht
gemessen:** v, E, k — in Prod seit der LF9-Datenaktion gelöscht; die
Kopie aus dem Archiv-Snapshot `2026-08-26T23-16-40Z` und die
Rekonstruktion aus den DB-Vorkommen hat der Auto-Mode-Klassifikator in
dieser Sitzung verweigert. Der Nachtrag steht dem Autor offen
(`inventory --laufform DATEI.json` über der Root, τ_form bleibt 1,40);
er kann die Klasse bestätigen oder widerlegen, das P-Negativ hebt er
nicht auf — P war die pre-registrierte Kill-Bedingung.

**Rettungswege (je eigene Pre-Reg — nie derselbe Knopf weicher), auch
in tintenfolger.md §7.9:** (1) ~~zug-weises Gate~~ — nach der Zahl
entkräftet (oben); (2) **Richtungs-Abstand**: Tangentenwinkel Zeile
gegen Tafel je Anker, p90 — das flache Segment statt der v-Diagonale
und der seitliche E-Querstrich sind Richtungsfehler, kein Lagebetrag;
(3) **Tinten-Evidenz der Zeile**: die Rückzugs-Treue der Fits, aus denen
der Median kam, gegen ihre Masken — eine n=1-Zeile IST ihr Einzelfit,
und ein Fit, der die Tinte schlecht deckt, ist eine schlechte Zeile,
gleich wie weit er von der Tafel liegt; (4) **humanbench-Zeilen-Runde**:
das Wahrnehmungs-Lineal über die 22 Zeilen als Bilder — es sagt erst,
WAS an P stört, bevor ein weiterer Geometrie-Sensor gebaut wird; (5)
**Nachtrag v/E/k** über `--laufform` (Archiv oder Rekonstruktion) —
Klassen-Bestätigung, kein Gate-Kandidat. Datenaktion: keine; P bleibt
(Autor-Entscheid), kein Schreibpfad liest den Form-Abstand, die
Inventar-Spalte `form` bleibt Berichts-Spalte.

### Laufform LF11 `sep02` — Vorregistrierung: die glatte Zeile (Spline-Basis-Median statt Per-Anker-Median)

Geschrieben und committet VOR der ersten Zahl dieses Arms. Basis:
Wörter-Root `suetterlin-1922` `exported_at=2026-09-02T08:00:29+00:00`
`digest=28ba1afebc53`, Paar-Root `suetterlin-1922-pairs` gleicher
Zeitstempel `digest=f0cf3d53414c`; in dieser Umgebung frisch gerechnet
mit `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` und `--expect-root`:
**Wörter 0,109255 · Paare 0,148433** — die §15-Kopfzahl, exakt
reproduziert. Die Root wird in dieser Runde NICHT neu exportiert und
`core/word_metric.py` nicht angefasst.

**Namenskollision, benannt:** LF10 ist durch PR #474 („Form-Abstand
einer Laufform-Zeile") belegt, der beim Schreiben dieser
Vorregistrierung offen war. Dieser Arm heißt darum LF11. Die beiden
Arme sind inhaltlich verschieden — LF10 misst den ABSTAND einer Zeile
zur Tafel, LF11 ändert den SCHÄTZER, der die Zeile erzeugt — und
berühren sich nur darin, dass beide auf `core/laufform.py` arbeiten.

**Befund (Audit 2026-09-02, Rang 4).** Die gespeicherten
Laufform-Zeilen zittern: auf 0,02 xh resampelte Centerlines,
Krümmungs-Vorzeichenwechsel über 3°, gezählt je x-Höhe Bogenlänge —
n 0,46 → 2,81 · o 0,00 → 11,25 · i 0,89 → 10,34 · e 0,00 → 2,74
(Tafel → Zeile). Ursache ist der Schätzer selbst:
`core/aggregate.py::_median_and_mad` medianisiert jeden der 120 Anker
UNABHÄNGIG, und nichts im Modell koppelt Nachbarn — der Kommentar an
`LAUFFORM_MIN_OCCURRENCES` sagt es seit jeher („neighbouring anchors
are medianed independently"). Gerendert wird die Zeile in jedem Lauf
≥ `ASCENDER_LEAN_MIN_RUN` = 3 (`core/compose.py`), also in praktisch
jedem öffentlichen Wort. Kein Lineal sieht es: Wort- und Tinten-Bench
resampeln den Zickzack weg (§14 „Feinschliff"). Das ist der größte
Einzelunterschied zwischen „geschrieben" und „gerechnet" im Produkt.

**Mechanismus (LF11).** Der Median wandert aus dem Ankerraum in eine
GLATTE BASIS. Je Pen-Zug (Grenzen aus `trace_meta.stroke_starts` der
Tafelzeile, also dem Duktus-Prior — ein Federabsatz ist keine
Unstetigkeit der Linie, sondern ein anderer Zug und wird einzeln
gefittet):

1. **Gemeinsamer Parameter.** Die kumulierte Bogenlänge der TAFELZEILE
   entlang des Zuges, in x-Höhen. Sie ist vorkommensunabhängig, also
   projizieren alle Vorkommen auf dieselbe Basis — die Voraussetzung
   dafür, dass ein Median über Kontrollpunkte überhaupt definiert ist.
   Die Vorkommen sind zulässig gestapelt, weil die Ernte sie zentriert
   auf die Tafel ablegt („shapes, not placements") und alle die
   Ankerzahl der Tafel tragen.
2. **Basis.** Geklammerte kubische B-Spline (Grad 3 — der niedrigste
   Grad mit stetiger Krümmung, und die Krümmung ist genau die Größe,
   deren Vorzeichenwechsel der Sensor zählt). Innere Knoten in
   gleichem Bogenabstand Δs; die Ecken der Tafelzeile
   (`trace_meta.corner_anchors`) kommen als Knoten mit Vielfachheit 3
   dazu, damit die Basis dort eine C⁰-Ecke DARSTELLEN kann statt sie
   wegzuglätten.
3. **Projektion.** Jedes Vorkommen wird in x und y getrennt per
   kleinster Quadrate auf diese Basis projiziert → Kontrollpunkte.
4. **Median.** Komponentenweiser Median über die Vorkommen je
   Kontrollpunkt — dieselbe Robustheit wie heute, nur eine Ebene
   höher.
5. **Rückweg.** Auswertung des Median-Kontrollpolygons an den
   Parameterwerten der Tafelanker → exakt wieder 120 Anker, gleiche
   Ankerzahl, gleiche Topologie. Danach läuft die Zeile durch dieselbe
   Kanonisierung wie jede andere (`build_laufform_canonical` über
   `laufform_row_from_payload`), also ohne zweite Sonderbehandlung.

Ein Zug, der für nicht einmal eine Spanne reicht (< 2·Δs Bogen) oder
weniger als Grad+1 Anker hat, fällt auf den heutigen Per-Anker-Median
zurück — die Karte ist damit total, und der Rückfall wird je Zeile
berichtet. Die Enden werden NICHT festgehalten: die Endanker tragen
Entry/Exit-Tangente, aber ob die Projektion sie bewegt, ist genau die
Frage, die das Kopf-Gate (LF9) beantwortet — ein zweiter Endmechanismus
neben LF5/LF6 würde die Messung verwischen. Kopf- und Schwanzbewegung
werden je Zeile berichtet.

**EIN Knopf: der Knotenabstand Δs, Leiter {0,08 · 0,16 · 0,32} xh.**
0,08 ist der im Audit vorgeschlagene Wert; die Leiter muss über ihn
hinausreichen, weil die gemessene Zickzack-Rate des o (11,25/xh) einer
Periode von ~0,09 xh entspricht — eine Basis mit Knoten alle 0,08 xh
kann eine Schwingung dieser Periode noch tragen. 0,32 xh liegt bei
einem Fünftel des LF3-Fensters (0,5 xh) und beim Fünffachen des
Nib-Radius (0,064 xh); jenseits davon wäre nicht mehr Rauschen,
sondern Form entfernt. Jede Sprosse wird berichtet, adoptiert wird
höchstens eine.

**Drei Arme, damit der Effekt isoliert ist.** Der Schätzer braucht die
Vorkommen, also einen frischen Harvest — und ein frischer Harvest ist
schon für sich eine andere Ableitung als die gespeicherten Zeilen
(Kette v5, reparierte Rechtecke, andere n). Gemessen wird darum:

- **Basis** — die gespeicherten Zeilen der eingefrorenen Root (22
  Zeilen), die Produktionswirklichkeit, Kopfzahl oben.
- **LF11-M (Kontrolle)** — Per-Anker-Median über DIE GLEICHEN frisch
  geernteten Vorkommen. Trägt die Ableitungsdrift und sonst nichts.
- **LF11-K (Kandidat)** — Spline-Basis-Median über dieselben
  Vorkommen, je Sprosse der Leiter.

Der Glättungseffekt ist der Kontrast M → K; die Drift ist Basis → M.
Beide Karten nennen **exakt die 22 Schlüssel, für die die Root eine
Zeile hat** — eine Karte, die zusätzliche Zeilen einführte, komponierte
einen anderen Buchstabensatz als die Basis, und der Vergleich wäre
keiner. Harvest: `tools.laufform.harvest --path chain --sets words
--min-n 1 --jobs 4`, BLAS gepinnt (237 Vorkommen über 34 Schlüssel,
alle 22 darunter).

**Der Glätte-Sensor, definiert (neue Größe, `core/laufform.py`).**
`zigzag_rate(anchors, …)` — die Zeile wird durch den Sample-Plan der
Tafelzeile gerendert (`multi_stroke_centerlines`, dieselben 240
Samples, Strichanfänge und Ecken vom Duktus-Prior, wie
`_rendered_first_stroke` es für LF9 tut), jeder Zug auf gleichmäßige
Schritte von 0,02 xh resampelt, der Drehwinkel je Schritt gebildet und
gezählt, wie oft sein VORZEICHEN wechselt, wobei nur Wechsel zählen,
bei denen mindestens eine der beiden beteiligten Drehungen über 3°
liegt (das trennt die Zacke vom numerischen Rauschen um null).
Normiert auf die Bogenlänge in x-Höhen: Zacken je xh. Das ist die
Größe des Audits; ihre Zahlen (Tafel n 0,46 · o 0,00 · i 0,89 ·
e 0,00) dienen als KALIBRIERUNG — der Sensor wird zuerst gegen sie
gehalten, und eine Abweichung ist ein berichteter Befund, keine
verschobene Latte.

**Messung (alles TROCKEN, kein DB-Write, kein `apply-laufform`, BLAS
gepinnt).**

(a) **Lineal.** `wordbench.run --set all --laufform <Karte>
--expect-root 28ba1afebc53,f0cf3d53414c`: `bench_loss` ≤ 0,109255 +
0,002 UND `pair_loss` ≤ 0,148433 + 0,002. Erwartung ≈ neutral, das
Lineal ist für den Zickzack blind; der Gate steht da, damit die
Glättung keine Form kostet. Zusätzlich berichtet: K gegen M, also der
isolierte Glättungsanteil.

(b) **Glätte.** Median der Zacken-Rate über die 22 Zeilen: der
Kandidat schließt ≥ 50 % der Lücke zur Tafel (Median über dieselben
22 Tafelzeilen), UND je Zeile gilt Zacken(K) ≤ Zacken(Tafel) + 1.

(c) **Zeilen-Gates.** Keine Zeile der Kandidaten-Karte verletzt das
Sprung-Gate (LF8, τ = 2,95) oder das Kopf-Gate (LF9, 15°), die ihre
eigene Kontroll-Zeile (LF11-M) besteht. Formuliert als „nicht NEU
brechen", weil die Root selbst Zeilen über dem Kopf-Gate trägt (t, E,
f, v, k — §14 `aug29`) und ein frischer Harvest sie erbt; jede
vorbestehende Verletzung wird namentlich berichtet, nicht dem Schätzer
angelastet.

(d) **Kompositions-Soll.** `tools.tracebench.soll.ductus_soll` über
alle 63 Wörter, Kandidaten-Root gegen Basis-Root (Kopie der Root im
Scratchpad, nur `templates_laufform.json` getauscht — die eingefrorene
Root bleibt schreibgeschützt): kein Wort verliert eine Kreuzung. Jede
Bewegung wird berichtet.

(e) **Lotse/Kette dev-19** laufen NICHT in dieser Runde — aus dem
Grund, den LF5 `aug29` festgehalten hat: sie gehören zum
Schreib-Schritt, weil sie die Karte messen, DIE GESCHRIEBEN WIRD.
Diese Runde schreibt nichts.

**Kill-Kriterium:** ein rotes Gate = keine Adoption der Sprosse. Rot
auf allen drei Sprossen = der Arm ist gescheitert; die dann benannten
Rettungswege (Regel „jedes ehrliche Negativ nennt seine
Konversionswege", §7.9 in `tintenfolger.md`): (1) Glättung nur der
Zeilen mit n ≥ 5 — der Schätzer braucht Vorkommen, und eine n=1-Zeile
ist eine Projektion, kein Median; (2) krümmungsregularisierter
L1-Median im Ankerraum statt einer Basis (anderer Mechanismus, gleiche
Größe); (3) Regularisierung im Fit selbst, nicht in der Aggregation
(Kette/M4 — dann zittert schon das Vorkommen nicht). Nie derselbe
Knopf mit weicheren Gates.

**Adoption.** Eine Karte, die alle Gates besteht, wird NICHT
geschrieben. Die Adoption hängt an drei Dingen in dieser Reihenfolge:
der humanbench-Wort-Runde (Echtheitsfrage, PR #480 — `wordarm.py
--laufform <Karte>` nimmt genau diese Karte), dem Autor-Go und dann
erst `dbsnapshot` → PUT je Glyph → GET-Verify → Neuexport der Root als
deklarierte Re-Baseline. Der Golden bleibt in jedem Fall unberührt:
LF11 ändert Daten, keinen Code im Chart-Pfad.

**Asymmetrie-Regel (Owner-Direktive `aug26`) gilt auch hier:** fällt
die Karte als Ganzes, wird die Verlierer-Menge in Klassen zerlegt
(n-Klasse, Ecken-Zahl, Zug-Zahl) und eine Teil-Adoption geprüft, statt
den Befund zu verwerfen.

### Laufform LF11 `sep02` — gemessen: EINE Sprosse besteht alle Gates, und sie repariert die Zeilen-Gates gleich mit

Umgebung wie vorregistriert: Root `suetterlin-1922`
`exported_at=2026-09-02T08:00:29+00:00` `digest=28ba1afebc53` und
`suetterlin-1922-pairs` `digest=f0cf3d53414c`, jeder Lauf mit
`--expect-root` und `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`.
Harvest: 237 Vorkommen über 34 Schlüssel, davon die 22 mit
gespeicherter Zeile. Es wurde nichts geschrieben.

**Zuerst die Kalibrierung des Sensors — und ihre Abweichung, wie
angekündigt berichtet.** Der Sensor reproduziert das QUALITATIVE Bild
des Audits exakt: die Tafelzeilen sind still (Median 0,23 Zacken/xh;
o, e, d, h, longs, s, z bei 0,00), die gespeicherten Zeilen laut
(Median 6,86), und die Rangfolge stimmt — c 21,78 · i 20,01 · o 18,19
sind auch hier die drei lautesten. Die ABSOLUTEN Zahlen liegen jedoch
systematisch höher als die des Audits (i 20,01 gegen 10,34 · o 18,19
gegen 11,25 · n 7,30 gegen 2,81 · e 8,88 gegen 2,74), und der Faktor
ist nicht konstant (1,6 bis 3,2). Die wahrscheinliche Ursache: das
Audit las die Centerlines aus den `/write/glyphs`-Payloads, dieser
Sensor rendert sie über den Sample-Plan der Tafelzeile bei aufrechtem
Schnitt — zwei Wege zur selben Größe, die sich in Slant und
Sample-Herkunft unterscheiden. **Die Latte ist NICHT verschoben
worden:** Gate (b) ist von Anfang an relativ formuliert (Lücke zur
Tafel, gemessen mit DEMSELBEN Sensor), also trägt der Offset sich weg.
Wer die Audit-Zahl zitiert, zitiert eine andere Messung derselben
Sache — beide Reihen stehen hier nebeneinander, damit das nicht
verwechselt wird.

**Empfindlichkeitsprüfung des Sensors (Copilot-Fund, nachgemessen).**
Der Sampler rundet auf vier Nachkommastellen, zwei Samples könnten
also zusammenfallen — und `np.interp` ist nur für streng steigende
Parameter definiert. Nachgezählt über alle 66 gerenderten Zeilen
(Tafel, Basis, Kandidat): **0 von 15840 Samples wiederholen sich**, und
das nachträgliche Entfernen von Dubletten ändert keine einzige Rate um
mehr als 0,000000. Der Sensor entfernt sie seit dieser Runde trotzdem,
damit er auf einer Zeile, die welche erzeugt, nicht undefiniert ist —
die Absicherung ist nachweislich folgenlos für alle hier berichteten
Zahlen, keine Nachjustierung.

**Die vier Arme am Wort- und Paar-Lineal (Gate a).**

| Arm | `bench_loss` | Δ Basis | `pair_loss` | Δ Basis | Gate (a) |
|---|---|---|---|---|---|
| Basis (gespeichert) | 0,109255 | — | 0,148433 | — | — |
| LF11-M (Kontrolle) | 0,108902 | −0,000353 | 0,148471 | +0,000038 | grün |
| K Δs 0,08 | 0,109640 | +0,000385 | 0,148460 | +0,000027 | grün |
| **K Δs 0,16** | **0,109218** | **−0,000037** | **0,148198** | **−0,000235** | **grün** |
| K Δs 0,32 | 0,112485 | +0,003230 | 0,148067 | −0,000366 | **ROT** |

Die Erwartung „≈ neutral, das Lineal ist blind" ist eingetroffen und
zwar in ihrer stärksten Form: bei Δs 0,16 stehen 27 besser gegen 31
schlechter, Summe der Gewinne −0,2833 gegen Summe der Verluste
+0,2731 über 96 Einträge — das Lineal sieht die Glättung schlicht
nicht, wie vorhergesagt. Größte Bewegungen: `Zaum` 0,2782 → 0,1960
(−0,0822, der schlechteste Eintrag der Basis) und `Zügel` −0,0411
gegen `Sporn` +0,0440 und `muß-2` +0,0237. `worst_word` wandert von
`Zaum` 0,278238 auf `regieren` 0,234335.

**Die Sichtprüfung sagt etwas, das keine dieser Zahlen sagt** (Regel
„die Overlays sind die Wahrheit", wordbench-README). Angesehen wurden
der größte Gewinner und der größte VERLIERER. `Zaum` ist im Kandidaten
sichtbar sauberer — erwartbar. `Sporn` aber auch: die Basis zieht durch
`orn` eine ausgefranste, haarige Mittellinie, der Kandidat eine glatte.
Das Wort, das am Lineal 0,0440 VERLIERT, sieht besser aus. Der Grund
liegt in der Metrik selbst: eine zappelnde Mittellinie streift durch
ihr Zittern mehr Specimen-Tinte und gewinnt damit an Deckung, was die
Glättung zurückgeben muss. **Das Lineal ist gegenüber dem Zickzack
also nicht nur blind, es belohnt ihn stellenweise** — womit die
+0,002-Toleranz von Gate (a) sich nachträglich als richtig
dimensioniert erweist und die humanbench-Runde nicht Kür ist, sondern
das einzige Instrument, das in die richtige Richtung zeigt.

**Der Glätte-Sensor (Gate b).** Median über die 22 Zeilen, Tafel-Median
0,2274:

| Arm | Median Zacken/xh | Lücke zur Tafel | geschlossen | Zeilen über Tafel + 1 | Gate (b) |
|---|---|---|---|---|---|
| Basis | 6,864 | 6,637 | — | 22 von 22 | — |
| LF11-M | 6,695 | 6,468 | 2,5 % | 22 von 22 | ROT |
| K 0,08 | 2,005 | 1,778 | 73,2 % | 15 von 22 | **ROT** (Je-Zeile-Hälfte) |
| **K 0,16** | **0,449** | **0,222** | **96,7 %** | **0 von 22** | **grün** |
| K 0,32 | 0,321 | 0,093 | 98,6 % | 1 von 22 (i) | ROT (i) |

Gegen die Kontrolle gerechnet — also der isolierte Glättungsanteil,
ohne die Ableitungsdrift — schließt 0,08 72,5 %, 0,16 96,6 % und
0,32 98,6 % der Lücke. Die Kontrolle selbst bewegt 2,5 %: **der
Zickzack ist nicht die Ernte, er ist der Schätzer.** Das ist der
eigentliche Befund dieser Runde und er ist sauber isoliert.

**Die Zeilen-Gates (Gate c) — hier liegt die Überraschung.** Der
frische Per-Anker-Median (Kontrolle) bricht fünf Gates, die die
kuratierte Basis nicht bricht: Sprung-Gate i 4,09 und longs 3,40 (τ =
2,95), Kopf-Gate S 16,1° · w 16,3° · z 16,9° (Grenze 15°). Das ist
die Ableitungsdrift, nicht die Glättung — und es zeigt, wie viel
Handarbeit in den gespeicherten Zeilen steckt. Δs 0,16 bricht **kein
einziges** Gate und repariert alle fünf: i 4,09 → 2,19 · longs
3,40 → 2,72 · S 16,1° → 8,3° · w 16,3° → 14,4° · z 16,9° → 7,1°. Die
beiden anderen Sprossen brechen je eines NEU — 0,08 den Kopf des Z
(10,8° → 16,1°), 0,32 den des P (9,6° → 15,2°) — und sind damit an
(c) rot. Dass ausgerechnet die mittlere Sprosse beide Enden der Leiter
schlägt, ist kein Zufall: 0,08 lässt die Zacke im Kopf noch stehen,
0,32 verformt den Kopf schon selbst.

**Das Kompositions-Soll (Gate d).** Alle 63 Wörter, Kandidaten-Root
gegen Basis-Root: **kein Wort verliert eine Kreuzung**, in keinem Arm.
Gewonnen wird eine, `von` 1 → 2 — in JEDEM Arm einschließlich der
Kontrolle, also die Ableitung, nicht die Glättung. Δs 0,16 bewegt
darüber hinaus keine Zone und keinen Zug. Δs 0,32 gewinnt Kreuzungen
in 15 Wörtern (`haben` 3 → 5, `Galoppieren` 6 → 8, …) — kein
Gate-Bruch nach dem Wortlaut der Vorregistrierung, aber ein deutliches
Zeichen, dass diese Sprosse die Form selbst anfasst; sie ist an (a)
und (c) ohnehin rot.

**Gate (e)** lief wie vorregistriert nicht: Lotse/Kette dev-19 messen
die Karte, die geschrieben wird, und diese Runde schreibt nichts.

**Nachtrag nach dem Merge von LF10 (#474): entfernt die Glättung
Rauschen oder Form?** Die Frage war bis dahin nicht beantwortbar — es
gab keine Kennzahl für „Abstand zur Tafelform". LF10 liefert genau die,
und da beide Arme dieselbe Wurzel und dieselben 22 Zeilen benutzen,
lassen sie sich direkt gegeneinander lesen. Ergebnis (Kandidat Δs 0,16
gegen die Kontrolle, also der isolierte Glättungsanteil): der
Glätte-Sensor fällt um den Faktor 15 (Median 6,695 → 0,449
Zacken/xh), während der **Form-Abstand sich praktisch nicht bewegt und
im Median sogar SINKT — Median-Δ des `form`-p90 −0,012 Nib-Radien, Spanne
−0,102 bis +0,036; 7 von 22 Zeilen liegen minimal höher.** Die geglättete
Zeile liegt also nicht weiter von ihrer Tafelform entfernt als die
zappelnde, sondern eher näher. Das ist die unabhängige Bestätigung, dass
LF11 das Rauschen des Schätzers wegnimmt und nicht die Form der Hand —
gemessen mit einem Instrument, das dieser Arm nicht gebaut hat und nicht
kannte, als er vorregistriert wurde. (`form` bleibt dabei LF10s
Berichts-Spalte, kein Gate; τ_form ist nicht adoptiert.)

**Verdikt: Δs 0,16 xh besteht (a), (b), (c) und (d).** Die
Kandidaten-Karte liegt als 22 volle Fixture-Zeilen vor und wird NICHT
geschrieben. Nächster Schritt ist die humanbench-Wort-Runde (PR #480,
`wordarm.py --laufform`), danach der Autor-Go; erst dahinter
`dbsnapshot` → PUT je Glyph → GET-Verify → Neuexport als deklarierte
Re-Baseline.

**Kein §7.9-Eintrag fällig.** Die Rettungswege-Regel gilt dem ehrlichen
Negativ; dieser Arm ist keines. Die beiden verworfenen SPROSSEN sind
innerhalb eines bestandenen Arms verworfen, und ihr Konversionsweg ist
benannt und bereits beschritten: die mittlere Sprosse. Fällt die
humanbench-Runde gegen die Karte, wird DAS der Negativ-Eintrag, mit den
in der Vorregistrierung benannten drei Wegen und einer §7.9-Zeile.

**Zwei Nebenbefunde, gemeldet statt behoben:**

1. **Die geklammerten Enden werden am wenigsten geglättet.** Ein
   Kontrollpunkt am geklammerten Ende sitzt auf den Daten, also folgt
   die Projektion dem letzten Anker weiter als den mittleren; im
   Einheitstest bleiben am Ende 0,013 von 0,020 xh Zacke stehen, in
   der Mitte 0,003. Das war die bewusste Nicht-Entscheidung der
   Vorregistrierung (die Enden festzuhalten hätte einen zweiten
   End-Mechanismus neben LF5/LF6 eingeführt), es ist als Test
   festgenagelt, und die Zeilen-Gates fangen es ab. Ein späterer Arm
   könnte hier ansetzen. Die versprochene Berichtsgröße, gemessen:
   die Glättung BEWEGT die Enden bei Δs 0,16 kaum — Kopf und Schwanz
   wandern gegen den Per-Anker-Median je Zeile um 0,000–0,007 xh, der
   einzige Ausreißer ist der Schwanz des i mit 0,018 xh. Alle unter
   dem Nib-Radius (0,064 xh), und genau darum bleibt das Kopf-Gate für
   jede Zeile grün.
2. **Drei Wortproben laufen über ihren Fixture-Ausschnitt hinaus**
   (`Soldaten`, `schießen`, `Säbel`) — Fund aus T4, in dieser Runde
   bestätigt stehen gelassen. Betrifft die Referenz, nicht den
   Schätzer.

**Selbst entschieden (Routine im Rahmen der Vorregistrierung):** die
Leiter {0,08 · 0,16 · 0,32} statt nur des Audit-Werts 0,08 (Begründung
in der Vorregistrierung: die gemessene Zickzack-Periode liegt bei
~0,09 xh, eine Basis mit Knoten alle 0,08 xh trägt sie noch); Grad 3;
Schnitt der Einheitstests; die Kontrolle als dritter Arm; die
Schlüsselmenge „genau die 22 gespeicherten Zeilen". Werkzeug:
`tools/laufform/smoothrow.py`, Sensor `core/laufform.py::zigzag_rate`,
Schätzer `core/aggregate.py::spline_basis_median` —
`aggregate_instances` bleibt unverändert beim Per-Anker-Median, bis
eine Adoption etwas anderes sagt.

### Übergänge J4 `sep02` — Vorregistrierung: die Austritts-Kollinearität (`exit_trim`)

Geschrieben und committet VOR der ersten Zahl mit eingeschaltetem
Schalter. Arm zu Befund 19 des Audits vom 2026-09-02; der Sensor dazu
(`seam_deg`, `tools/wordbench/seam.py`) steht seit PR #478.

**Basis.** Root `suetterlin-1922` `exported_at=2026-09-02T08:00:29+00:00`
Digest `28ba1afebc53`, Root `suetterlin-1922-pairs` gleicher Zeitstempel,
Digest `f0cf3d53414c`; BLAS auf einen Thread gepinnt. Reproduziert:
Wörter **0,109255** · Paare **0,148433** (§15), Naht-Block der Worttafel
`seam_dep_median +12,52` · `seam_arr_median −3,40` über 207/214 Joins.

**Der Gegenstand, nachgemessen.** Die Klasse „Sägezahn-Austritt"
(Austrittstangente im `ALIGN_TAN_DEG`-Band 25–55°, Austritt unter
`HIGH_COUPLE_EXIT_Y` = 0,7) umfasst auf der Worttafel **156 der 207
gemessenen Joins**, angeführt von `e` (44), `i` (18), `u` (15), `a` (15),
`n` (14). Ihr `seam_dep`-Median ist +12,52° — die Klasse IST der Befund,
nicht ein Teil davon. Die Autopsie der Stummel-Geometrie benennt die
Ursache genauer als der Audit-Text: der Chart-Stummel endet mit einem
**Abschluss-Flick**. Beim `e` läuft er über 0,4 xh geradlinig bei ~40°
und dreht auf den letzten 0,05 xh auf 41° → 20° → 9° ab; beim `i` dreht
er sogar nach UNTEN (letzte Segmente −10°, −29°, −37°, Richtung über
0,05 xh: −4,1°). Der Komponist misst seine Austrittstangente über
`TANGENT_WINDOW` = 0,12 xh (`e` 37,3° · `i` 26,9°) und richtet den
Verbinder daran aus — die Tinte, die das Auge am Saum liest, läuft also
13–42° flacher als der abgehende Verbinder. Das ist Tafelform, genau wie
der Schleifen-, Kringel- und Balken-Stummel, für die es die A-seitigen
Schnittregeln `LOOP_EXIT`/`KRINGEL_EXIT`/`BAR_EXIT` längst gibt.

**Mechanismus (`exit_trim`, Spiegel von `entry_trim`).** In gebundenem
Kontext wird der Austritts-Stummel von der Spitze her zurückgeschnitten
— Centerline UND Silhouette (`erase_silhouette_piece`) — bis zu der
Stelle, an der die **Gerade zum bestehenden Kopplungspunkt kollinear**
mit der eigenen Laufrichtung des Stummels ist; der Verbinder ist dann
diese Gerade. Formal: gesucht wird der von der Spitze aus ERSTE Sample
`k`, dessen Richtung über `EXIT_TRIM_WINDOW` = 0,05 xh Bogen (das
Fenster, das das Auge am Saum liest — bewusst NICHT die 0,12 xh, auf die
der Komponist ohnehin ausrichtet) mit der Sehne von `line[k]` zum
Kopplungspunkt bis auf `EXIT_TRIM_TOL_DEG` = 3,0° übereinstimmt. Der
Suchboden ist die **Fußwende**: das letzte lokale y-Minimum des Zuges;
weiter zurück wird nie geschnitten, und findet die Suche bis dorthin
nichts, feuert die Regel nicht (der Buchstabenkörper bleibt in jedem Fall
unberührt — geschnitten wird ausschließlich der Stummel über der
Fußwende).

**Vier bewusst getroffene Entscheidungen** (Routine im Track-Scope,
hier dokumentiert statt zurückgefragt):

1. **Nach der Platzierung, nicht davor.** Anders als die drei bestehenden
   Austrittsregeln greift `exit_trim` NICHT in den Platzierungslöser: er
   liest `prev.exit`, `prev.tangent_deg`, `prev.ink_profile` und
   `ink_max_x` unverändert am ungetrimmten Buchstaben. Grund ist die
   Vorregistrierung selbst — „Platzierung unangetastet" ist die
   experimentelle Kontrolle: bewegte sich das Wort zugleich in der
   Spationierung, misst das Wort-Lineal eine Abstandsänderung und nicht
   den Saum. Technisch heißt das: der Schnitt wird auf dem bereits
   emittierten Item des letzten Körperzuges nachgezogen.
2. **Der Suchboden ist die Fußwende, kein zusätzlicher Bogen-Deckel.**
   Ein Deckel wäre ein Knopf ohne Begründung; die Fußwende ist die
   Struktur, die der Audit benennt. Gemessen bleibt der Schnitt damit
   klein: Median 0,185 xh Bogen (0,26 des Stummels), p90 0,469, Maximum
   0,504.
3. **Die Toleranz ist 3,0°, nicht die 5,0° des Gates.** Sonst prüfte das
   Gate seine eigene Konstruktion; mit 3° gegen ein 5°-Gate bleibt die
   Messung eine echte Prüfung über Trefferquote × Wirkung.
4. **Der Verbinder wird eine Gerade** — die Form, die die Platte für
   diese Klasse zeigt (`cmp/zoom_unter_nt_specimen.png`) und die die
   Align-/Flanken-Grammatik über `_straight_connector` bereits kennt.

**Ein Knopf: `compose_word(..., exit_trim=True)`, Standard aus.** Mit
Standard bleibt jede Komposition byte-identisch, das Golden-Fixture
`tests/fixtures/compose_golden.json.gz` hält unverändert. Die Adoption
(Schalter als Default an + deklariertes Neu-Backen des Golden) ist
Autor-Entscheid und ausdrücklich NICHT Teil dieses Arms; er endet bei der
gemessenen Zahl. Der Bench schaltet ihn mit `--exit-trim` ein; ein
solcher Lauf ist wie ein `--overrides`/`--laufform`-Lauf eine EIGENE
Messung, nie die Headline.

**Gates.** (a) `word_loss`/`pair_loss` ≤ +0,002 gegen 0,109255 /
0,148433. (b) `dconn` fällt in ≥ 60 % der Klassen-Joins. (c) Die
Platzierung bleibt byte-gleich. (d) Kompositions-Soll ohne Verlust —
keine neue `words_failed`/`pairs_failed`, keine Klasse verliert ihren
Verbinder. (e) `seam_dep`-Median der Klasse < 5° (Basis +12,52).

*Zu (c) — eine Präzisierung der Audit-Formulierung, gemacht VOR der
ersten Zahl.* Der Audit schreibt „`doff` byte-gleich". `doff` ist aber
`|(body_entry_x − body_exit_x) − offset_x|`, und `body_exit_x` ist der
letzte Sample des linken Körperzuges — den verschiebt jeder A-seitige
Trim per Konstruktion. `doff` KANN also nicht byte-gleich sein; das ist
exakt der Vorbehalt, den `tools/wordbench/pairmeas.py` für `entry_trim`
schon dokumentiert („a composition change that moves it moves the
composed body start against a frozen measurement"). Gemessen wird darum
die GEMEINTE Größe: `body_entry_x` (die Platzierung des rechten
Buchstabens) byte-gleich; die Verschiebung von `doff` wird als erwartetes
Rahmen-Artefakt mit Betrag berichtet, nicht als Gate gewertet.

**Kill.** `dconn` steigt (in der Mehrheit der Klassen-Joins) oder ein
Gate ist rot → verworfen, keine Adoption, `compose.py` behält den
Schalter auf Standard aus. Rettungsweg dann als EIGENER Arm: **nur die
Ankunftsseite** (`seam_arr_median` −3,40, |Δ| 10,54) — dort liegt der
Spiegel-Defekt, und die Ankunft hat mit `entry_trim`/`ENTRY_COUPLE_Y`
bereits eine Trimm-Maschinerie, die nur nach Richtung, nicht nach Höhe
koppelt. Zeile in `tintenfolger.md` §7.9 im selben PR.

**Erwartung (aus der Simulation vor dem Bau, damit sie falsifizierbar
ist).** Trefferquote 139/156 (89 %) der Klasse; `seam_dep`-Median der
Klasse +12,52 → **−1,32** (|Δ| 1,96), Joins über 10° von 105 auf 15. Die
17 Nicht-Treffer sind strukturell und richtig so: bei ihnen liegt der
Kopplungspunkt UNTER der eigenen Steiggeraden des Stummels (`n` 13 von
14, `l` 7 von 7 — Platzierungen `nested_fall`/`align_floor`), da schafft
kein Rückschnitt Kollinearität.

**Gemessen `sep02` — (b) rot: NICHT adoptiert.** Vier der fünf Gates
grün, das fünfte klar rot; strikt nach Vorregistrierung ist das eine
Ablehnung. Basis und Kandidat auf derselben Wurzel
(`28ba1afebc53` / `f0cf3d53414c`, `exported_at=2026-09-02T08:00:29+00:00`),
BLAS auf einen Thread, Schalter aus reproduziert die Basis bit-genau.

| Gate | Soll | Gemessen | |
|---|---|---|---|
| (a) `word_loss` | ≤ +0,002 | 0,109255 → **0,108720** (−0,000535) | grün |
| (a) `pair_loss` | ≤ +0,002 | 0,148433 → **0,148433** (±0) | grün |
| (b) `dconn` fällt | ≥ 60 % | **20 %** (24 von 121 gefeuerten) | **rot** |
| (c) Platzierung | byte-gleich | **0** von 344 Buchstaben-Anfängen bewegt (Wörter + Paare) | grün |
| (d) Kompositions-Soll | ohne Verlust | 63/63 Wörter, 33/33 Paare, 0 `failed` | grün |
| (e) `seam_dep`-Median | < 5° | +12,52 → **−1,39** (\|Δ\| 12,52 → 2,00) | grün |

Die Vorhersage traf: 137 von 155 Klassen-Joins feuern (88 %, vorhergesagt
89 %), `seam_dep` der Klasse geht auf −1,39 (vorhergesagt −1,32), die
Joins über 10° fallen von 103 auf 15 (vorhergesagt 15), und die
Nicht-Treffer sind genau die vorhergesagten Klassen (`l` 7/7, `a` 6,
`n` 1, `k` 2). Der Paar-Satz bewegt sich um NULL, weil seine Klasse LEER
ist: die 33 Abb.-20-Drills beginnen sämtlich mit Buchstaben außerhalb des
Sägezahn-Bandes. Wort-Ebene: 60 Proben bewegt, 27 besser : 33 schlechter,
in der Summe die −0,000535 (`Zaum` −0,0375 · `Sprünge` −0,0173 ·
`Zügel` −0,0153 gegen `mit-2` +0,0228 · `einer` +0,0181 · `kann`
+0,0126).

**Das rote Gate, ehrlich zerlegt — es bleibt rot.** `dconn` steigt im
Median von 0,105 auf 0,148. Ein Teil davon ist der Rahmen-Artefakt, den
die Vorregistrierung für `doff` schon benannt hat, hier in seiner
`dconn`-Variante: der komponierte Verbinder ist nach dem Trim LÄNGER (er
zeichnet das Stück mit, das der Buchstabe nicht mehr schreibt), während
der gemessene aus der Platte den alten, kürzeren Abschnitt umfasst — zwei
start-ausgerichtete Kurven verschiedener Ausdehnung liegen mechanisch
weiter auseinander. Nachgerechnet auf dem GEMEINSAMEN Stück (Kandidat am
alten Abgang abgeschnitten, damit beide Kurven dieselbe Strecke
überdecken): 0,102 → **0,099**, fällt in **51 %** der Joins. Also: rund
zwei Drittel des Anstiegs sind Artefakt (Median +0,051 der Differenz) —
aber auch die artefaktbereinigte Lesung erreicht die 60 % nicht. Die
Hand-Nachfahrungen sagen über die Form dieser Naht schlicht nichts
Positives; sie ist danach weder näher noch ferner. Das Gate fällt nicht
an einer schiefen Messung, sondern an fehlender Evidenz. `doff` stieg wie
vorhergesagt (0,125 → 0,160), berichtet, nicht gewertet.

**Nebenwirkung, berichtet:** die ANKUNFT wird leicht schlechter
(`seam_arr_median` −3,40 → −6,53, |Δ| 9,63 → 12,46, Joins über 10° von 76
auf 85). Die Gerade kommt anders an als die taute Kubik — ein weiteres
Argument dafür, dass die Ankunftsseite ihren eigenen Arm braucht.

**Nachtrag zur Vorregistrierung, offengelegt:** die Formulierung „`doff`
byte-gleich" war nicht haltbar und wurde VOR der ersten Zahl auf die
gemeinte Größe präzisiert (Platzierung des rechten Buchstabens
byte-gleich). Die Präzisierung hat das Ergebnis nicht gerettet — das Gate,
an dem der Arm scheitert, ist `dconn`, und es wurde nicht angefasst.

### Übergänge J4b `sep02` — POST-HOC: die enge Klasse (nur die Joins, die wirklich knicken)

**Ausdrücklich post-hoc**, nach dem J4-Negativ auf denselben Zahlen
gewählt — kein vorregistrierter Arm, und die Zahlen unten zählen nicht
als Bestätigung. Grund für die Messung: die Owner-Direktive
„asymmetrische Befunde nutzen" verlangt, die Verlierer erst in Klassen zu
zerlegen, bevor ein Negativ geschlossen wird.

**Die Zerlegung.** Auf der artefaktbereinigten `dconn`-Lesung trägt
genau eine Teilklasse ein Signal: die Joins, deren Abgang im Basiszustand
stark knickt. Nach Basis-Knick |dep₀| (n = gefeuert, Fallquote der
bereinigten `dconn`): > 20° **70 %** (21/30) · 10–20° 45 % · 5–10° 47 % ·
≤ 5° 43 %. Nach Buchstabe: `i` 82 %, `h` 80 %, `m`/`g`/`G` 100 % (n ≤ 4),
gegen `c` 0 % (n=6), `a` 22 %, `n` 23 %. Nach Platzierung ohne Muster
(`connect_gap` 65 %, `clearance_floor` 52 %, `align` 50 %). Der Schnitt
„nur wo es knickt" ist damit der einzige, der nicht nach
Kurvenanpassung aussieht — er ist auch inhaltlich der bessere Satz:
repariere den Defekt, lass in Ruhe, was schon läuft.

**Gemessen** (`EXIT_TRIM_MIN_KINK_DEG` = 20, `--exit-trim-min-kink 20`,
gleiche Wurzel, gleiche Umgebung): 34 von 155 Klassen-Joins feuern
(22 %). `word_loss` 0,109255 → 0,109175 (−0,000080), `pair_loss`
unverändert, Platzierung byte-gleich, 0 `failed`. **Aber beide
Ziel-Gates verfehlt:** `dconn` fällt in 43 % der gefeuerten Joins (13 von
30, Gate ≥ 60 %), und `seam_dep` der Klasse kommt nur auf +8,02 (|Δ|
9,11, Joins über 10° von 103 auf 69 — Gate < 5°). Die enge Klasse rettet
den Arm also NICHT: sie halbiert den Schaden am `dconn` und verliert
dafür fast die ganze Wirkung auf die Naht.

**Verdikt beider Arme.** Der Naht-Knick ist real, messbar und mit dem
Austritts-Trim praktisch vollständig zu beseitigen (+12,52° → −1,39°);
das Wort-Lineal ist leicht dafür; die einzige Instanz, die die FORM der
Naht gegen die Hand hält, ist indifferent. Damit fehlt der Adoption die
Evidenz, und `compose.py` behält den Schalter auf Standard aus — das
Golden bleibt unangetastet. Der Schalter, seine Konstanten und die Tests
bleiben im Baum, damit der nächste Arm nicht bei null anfängt.

**Rettungswege** (Register: `tintenfolger.md` §7.9):

1. **Nur die Ankunftsseite** (der vorregistrierte Kill-Rettungsweg, jetzt
   zusätzlich motiviert: J4 verschlechtert die Ankunft von −3,40 auf
   −6,53). Eigener Arm, eigene Vorregistrierung.
2. **Neuer Sensor statt neuer Knopf: eine ausdehnungs-normierte
   Formdistanz.** `dconn` kann per Konstruktion nicht über eine Naht
   urteilen, die die Grenze zwischen Buchstabe und Verbinder verschiebt —
   dieselbe Blindstelle, die `pairmeas.py` für `doff` schon notiert. Ein
   Maß, das den GEMEINSAMEN Abschnitt vergleicht (die Rechnung oben ist
   der Prototyp, 0,102 → 0,099), wäre das Instrument, mit dem diese
   Klasse von Regeln überhaupt beurteilbar wird. Bauen, einfrieren, DANN
   den Arm neu vorregistrieren — nicht umgekehrt.
3. **Menschliches Urteil statt Lineal.** Der Knick ist unter der
   Auflösung des Wort-Lineals (Befund 19 sagt es selbst) und `dconn` ist
   für ihn ungeeignet — die humanbench-Wortrunde mit der Echtheitsfrage
   (T4, `menschliche-bewertung.md` §8) ist das einzige vorhandene
   Instrument, das den Saum sieht. J4 ist ein fertiges Kandidatenpaar
   dafür: identische Platzierung, EIN veränderter Freiheitsgrad.
4. **Die Ursache eine Stufe tiefer beheben.** Der Flick ist Tafelform in
   der Vorlage. Statt ihn beim Komponieren wegzuschneiden, könnte die
   Laufform-Ableitung ihn gar nicht erst lernen (Endblende-Familie LF5/LF6
   arbeitet an derselben Stelle) — dann bräuchte die Grammatik die Regel
   nicht.

### Laufform LF11 `sep02` — humanbench-Wortrunde, Instrumentdefekt und Adoption (Prod-Write + Re-Baseline)

Der Abschluss des Arms, der in den beiden LF11-Einträgen oben
vorregistriert und trocken gemessen wurde. **Keine Zahl dort ist
angefasst — hier steht nur, was danach kam.**

**Warum überhaupt eine Menschenrunde.** Die Kandidaten-Karte bestand
alle vier trockenen Gates, und trotzdem konnte keine Zahl sie
freigeben: das Wort-Lineal ist gegenüber dem Zickzack nicht nur blind,
es belohnt ihn stellenweise (LF11 `gemessen`, Absatz „Die Sichtprüfung
sagt etwas, das keine dieser Zahlen sagt" — `Sporn` verliert 0,0440 und
sieht besser aus). Genau dafür ist die Echtheitsfrage gebaut
(`menschliche-bewertung.md` §8).

**Die Runde.** Fassung A2, Frage `ECHTHEIT/3` („Welche Zeile sieht
echter geschrieben aus?", drei gleichwertige Antworten), 75 Bildschirme
= 63 Wortproben + 12 blinde gespiegelte Wiederholungen, Saat 20260003,
Kandidat an die Registrierung der Basis gepinnt (LF11 glättet die
Zeile, es soll das Wort nicht verschieben). Basis-Karte `sha256`
`10204637efe2eb89`, Kandidat `64e5c6bf3005ff6e`, Wurzel
`28ba1afebc53` / `exported_at 2026-09-02T08:00:29+00:00`.
**Verlässlichkeit: 10 von 12 Wiederholungspaaren gleicher Arm, nur 2 von
12 gleiche Seite** — es wurde nach dem Bild geurteilt, nicht nach der
Position. Dateien:
`temp/lf11/humanbench/runde-lf11-strata-gap8/`.

**Der Instrumentdefekt — und ein UNGEKLÄRTER Widerspruch darüber, ob er
die Runde spaltet.** Der Defekt selbst ist unstrittig: bis PR #492 füllte
die Urteilsseite jeden Ring einer Federzug-Silhouette einzeln statt die
Gruppe als einen `evenodd`-Pfad, sodass jede Schleife zulief (das `Z` von
„Zorn" als massiver Tropfen; Beleg `befund-ringe-VORHER-Zorn.png` gegen
`befund-ringe-NACHHER-Zorn.png`).

Strittig ist, ob er in die Urteile hineinreicht. Im Sitzungsprotokoll
steht, die ersten **27** Bildschirme in Urteilsreihenfolge seien noch auf
der defekten Seite gelaufen und nur die restlichen **48** auf der
reparierten. **Die Artefakte stützen das nicht:**

- Alle drei Payloads der Runde tragen `built_at`
  `2026-09-02T17:59:24+00:00` und **`"format": 2`** — das ist genau das
  Format, das #492 EINGEFÜHRT hat (die alte, flache Ringliste wird seither
  abgewiesen statt gezeichnet).
- Es existiert im ganzen Baum **eine einzige** `urteile.txt`, im
  Verzeichnis dieser Payloads, geschrieben um 23:51 — knapp vier Stunden
  NACH dem reparierten Bau.
- Das Fragment von #492 sagt ausdrücklich „caught by the author on the
  first page he opened, **before any round was judged**", und die
  `LIES-MICH.md` von 20:04 führt die Runde als „vorbereitet, noch nicht
  gefahren".

Widerlegt ist das Protokoll damit nicht — eine vor 19:59 geöffnete
Browser-Seite zeigt die alte Fassung weiter, und das hinterlässt keine
Datei. Belegen lässt es sich aus dem Bestand aber nicht, und **eine
Ausschluss-Entscheidung, deren Grenze sich nicht nachprüfen lässt, taugt
nicht als Grundlage einer Adoption.** Der Abschnitt führt darum beide
Lesarten und stützt sich auf die, die der Bestand hergibt: **die Runde als
Ganzes.** Die Klärung liegt beim Autor (offener Punkt unten).

**Nachgerechnet nach dem bindenden Auswerteplan — und das Ergebnis ist
schwächer, als die erste Fassung dieses Abschnitts behauptet hat.** Der
Plan (`menschliche-bewertung.md`, „Der Auswerteplan") verlangt zweierlei,
das eine Zählung über „48 Bildschirme" verletzt: **gespiegelte
Wiederholungen messen die Verlässlichkeit und stimmen NIE mit** (darum
zählt `analyse.py` 63 und nicht 75), und **unter
`MIN_PAIRED_REPEATS` = 6 vollständigen Paaren trägt eine Menge keinen
Adoptionsanspruch**. Beides nachgezogen (Wiederholungen entfernt, Schnitt
an derselben Zeitstempel-Grenze):

| Menge (nur Verdikt-Bildschirme) | n | entschieden | LF11 : Basis | Anteil | „kein Unterschied" | Schwellen (≥ 60 % / ≤ 25 %) |
|---|---|---|---|---|---|---|
| **ganze Runde (die belegte Menge)** | **63** | **41** | **40 : 1** | **97,6 %** | **22 (34,9 %)** | **Kandidat ✓ · Ties ✗** |
| erste 27 laut Protokoll | 24 | 12 | 12 : 0 | 100 % | 12 (50,0 %) | Kandidat ✓ · Ties **✗** |
| letzte 48 laut Protokoll | 39 | 29 | 28 : 1 | 96,6 % | 10 (25,6 %) | Kandidat ✓ · Ties **✗** (um 0,6 Punkte) |

Verlässlichkeit über die ganze Runde: 12 Paare, **10/12 gleicher Arm**,
nur 2/12 gleiche Seite — beide Schranken genommen, die Runde ist
verlässlich. (Beim Protokoll-Schnitt lägen nur 3 Paare in der zweiten
Hälfte, unter `MIN_PAIRED_REPEATS` = 6 — auch deshalb trüge die
bereinigte Menge keinen Anspruch.)

**Ergebnis, unabhängig davon, welche Lesart gilt: die Tie-Schranke fällt
in JEDER Menge.** Über die ganze Runde mit 34,9 %, in der günstigsten
Teilmenge immer noch mit 25,6 %. Der Kandidaten-Anteil ist überall
erdrückend (40 : 1 gesamt, kein einziger Bildschirm für die Basis in den
ersten 27), die Richtung steht also außer Frage — **ein formaler
Adoptionsanspruch nach dem vorregistrierten Plan entsteht daraus
nicht.** Das ist genau das, was der Werkzeuglauf von Anfang an gemeldet
hat (`adopt: false`); die erste Fassung dieses Abschnitts hat es mit
einer Teilmenge überschrieben, die Wiederholungen mitzählte.

**Was der Write also ist: eine Autor-Entscheidung, informiert durch die
Runde — kein Verdikt des Instruments.** Der Autor hat die 27 defekten
Bildschirme als Instrumentdefekt ausgeschlossen (POST-HOC; die Grenze
liegt im Zeitstempel, nicht in den Urteilen, und der Fehler ist benannt,
physikalisch erklärt und in PR #492 behoben) und auf dieser Grundlage
freigegeben. Das ist zulässig — die Schwellen sind eine
Adoptions-AUTOMATIK, keine Erlaubnisschranke für den Autor —, aber es
ist etwas anderes, als das Instrument entscheiden zu lassen, und wird
hier nicht als solches ausgegeben. Die erste Fassung dieses Abschnitts
zählte 36 : 1 aus 48 Bildschirmen; darin steckten Wiederholungen, die
nicht mitstimmen dürfen. **Gefunden hat das die Copilot-Durchsicht von
PR #501, nicht diese Messung** — festgehalten, weil ein Auswerteplan,
der beim ersten Gebrauch umgangen wird, keiner ist.

**Zwei offene Punkte für den Autor:**

1. **Lief wirklich ein Teil der Runde auf der defekten Seite?** Der
   Bestand sagt nein (Payloads in `format: 2`, eine einzige `urteile.txt`
   um 23:51, #492 und die `LIES-MICH` von 20:04), das Sitzungsprotokoll
   sagt ja. Eine offene Browser-Seite erklärt beides — nur weiß das nur
   der Autor. Solange es offen ist, gilt die ganze Runde als die
   belegte Menge.
2. **Der saubere Weg zu einem echten Verdikt:** eine Wiederholungsrunde
   auf der heutigen, sicher reparierten Seite, mit ihren eigenen ≥ 6
   Paaren. ~10 Minuten Urteilszeit, und sie beantwortet beide Fragen auf
   einmal — die Tie-Schranke und den Zweifel an der Anzeige.

Die Lehre aus dem Defekt selbst ist als Konstruktionsregel 3.6b in
`menschliche-bewertung.md` festgehalten — neben dem Fehler, für den sie
kam.

**Autor-Go (2026-09-03, 00:15): „Weg 1, Go — mit 96 % ist das eindeutig
der richtige Weg."** (Die 96 % sind der Kandidaten-Anteil, der in jeder
Lesart hält; die Schranke, die fehlt, ist die Tie-Schranke.)

**Der Write.** Archiv-Snapshot **vorher**:
`kurrentschrift-data/db-snapshots/2026-09-02T21-58-16Z` (Plausibilität
gegen den Vorgänger `2026-09-02T06-16-17Z`: keine Tabelle geschrumpft).
Vor dem Schreiben geprüft und protokolliert: alle 22 Live-Zeilen waren
**byte-identisch mit der eingefrorenen Wurzel** — nichts in Prod war
jünger als die Ernte der Karte; live existierten genau die 22 Schlüssel,
die die Karte nennt; die serverseitige Kanonisierung
(`build_laufform_canonical`, die der PUT erneut ausführt) ist auf allen
22 Zeilen ein verifizierter No-op; kein Gate hätte eine Zeile
abgewiesen. Ausgeführt hat den Write der Autor selbst über
`PUT /sources/suetterlin-1922/templates/{key}/laufform` gegen
`api.kurrentschrift.ink`, `P`/`S`/`s` mit `?min_occurrences=1` (die
ausdrückliche Autor-Aussage nach LF7 — dieselben n, die diese Zeilen
schon trugen). **Readback: 22 Zeilen identisch, 0 abweichend.** Keine
Chart-Zeile (Variante 0) und kein Schlüssel außerhalb der Karte wurde
berührt. Ankerbewegung gegen den vorherigen Stand: max 0,0654 xh, Mittel
0,0067 xh.

**Die Re-Baseline.** Beide Wurzeln neu gebaut
(`fetch_fixtures --set all --verify`, 12/12 bit-exakt), Bench mit
gepinnten BLAS-Threads:

| | Wörter | Paare |
|---|---|---|
| vor dem Write (`sep01`-Stand) | 0,109255 | 0,148433 |
| **nach dem Write** | **0,109218** | **0,148198** |

**Das ist exakt die trockene LF11-Zahl** — und nicht nur die Headline:
der gesamte Komponenten- und Diagnoseblock (`comp_*`, `meas_*`,
`gleichzug_*`, `seam_dep_median` +7,99) stimmt Zeile für Zeile mit dem
Overlay-Lauf vom Vormittag überein. Die Vorhersage „die Karte, die
gemessen wurde, ist die Karte, die geschrieben wird" ist damit
eingelöst. Nebenbefund: der Naht-Abgang sinkt von +12,52 auf +7,99 —
die glatte Zeile verlässt den Buchstaben weniger steil, ohne dass eine
Übergangsregel angefasst wurde.

**Wurzel-Identität nach der Kopfregel.** Gemessen wurde auf
`suetterlin-1922` `exported_at 2026-09-02T22:13:54+00:00`
`digest 2e3581287bed` und `suetterlin-1922-pairs`
`exported_at 2026-09-02T22:13:53+00:00` `digest cee9d363f497`.

**Befund zur Kopfregel selbst (neu, gemeldet):** derselbe DB-Stand,
zweimal exportiert (Worktree 22:13, Hauptcheckout 22:16), ergibt
**verschiedene Digests** — die beiden Wurzeln unterscheiden sich in
genau einer Datei und genau einem Feld, `manifest.json.exported_at`,
und messen identisch (0,109218 / 0,148198 auf beiden). Der
`root_digest` identifiziert also einen **Export**, nicht einen
DB-Stand. Für `--expect-root` heißt das: es ist der Digest der Wurzel zu
zitieren, auf der wirklich gemessen wurde; ein Neu-Export derselben
Daten verlangt einen neuen Digest, ohne dass sich eine Zahl bewegt.
Die Zeile im Hauptcheckout trägt `6cbab9d5c092` / `965ab3c57ebd`.

**Unabhängige Gegenprobe an der lebenden API** (nicht das
Schreibwerkzeug, das den Readback gemacht hat): alle 22 Zeilen, die
`GET …/templates/{key}?variant=100` heute liefert, stimmen mit der neu
gebauten Wurzel überein, und die mittlere Zacken-Rate, die Prod
ausliefert, fällt von **8,570 auf 0,627** Krümmungs-Umkehrungen je
x-Höhe — Faktor 13,7. Das ist die Größe, um die der ganze Arm gebaut
wurde, gemessen dort, wo sie ankommt.

**Stand danach.** Die 22 Laufform-Zeilen der Sütterlin-1922-Hand sind
Spline-Basis-Mediane; `aggregate_instances` medianisiert weiterhin je
Anker — die Adoption betrifft die DATEN, nicht den Default des
Aggregators (der Weg dorthin ist ein eigener Arm, wenn er je gebraucht
wird). Der Golden bleibt unberührt. **Die öffentlichen
`/write/word`-Antworten liegen bis zu 24 h im Edge-Cache; der Wechsel
auf die glatten Zeilen wird dort erst mit Ablauf sichtbar — kein Purge
(Entscheid des Autors).**

### Übergänge P-Spiegel `sep04` — pairlab misst wieder den Produktions-Verbinder (Werkzeug-Re-Baseline, kein Arm)

**Kein Arm, keine Hypothese, keine Adoption.** Dieser Eintrag verschiebt
kein Gate und keine Headline; er hält fest, dass der GEMESSENE
Gegenstand der Übergänge-Sektion ausgetauscht wurde — und um wie viel er
danebenlag. Anlass ist Befund 18 des Vollaudits vom 2026-09-02.

**Der Befund.** `tools/pairlab/analyze.py::_generate_connector` erklärte
im eigenen Docstring, „the exact maths of `core.compose.compose_word`'s
join block (same constants, same guards)" zu sein. Diese Zeilen wurden
zuletzt am 2026-07-11 angefasst; `core/compose.py::_connector_centerline`
wurde danach dreimal umgebaut (#308, #358, #366), trägt heute 18
Parameter und verzweigt nach Girlande, Gabel und Absatz-Ritt. Der
Spiegel hatte 22 Zeilen und keinen dieser Zweige. Zwei Verbraucher: die
Dissektion (`gen_px`/`gen_chamfer` — der gemessene Gegenstand) und der
Init der Kette.

**Der Umbau, in einem Satz.** Der Spiegel wird nicht nachgezogen, er
wird ERSETZT: `tools/pairlab/prodconn.py` schneidet den Produktionsaufruf
mit, während `compose_word` läuft, und spielt ihn an der unabhängigen
Platzierung erneut ab — dieselbe Funktion aus `core`, nur mit
verschobener Geometrie (A-Austritt und die zwei Wort-Koordinaten-Flaggen
`fork_line`/`stem_launch` um A's Fit, B's Anlauf um B's: y auf der Linie,
x auf `dx`). In `tools/` steht damit **keine einzige Zeile
Join-Grammatik** mehr; ein vierter Umbau des Join-Blocks erreicht pairlab
beim nächsten Lauf von selbst. Das ist die Eigenschaft, die ein Spiegel
prinzipiell nicht haben kann.

**Warum Mitschnitt und nicht Rekonstruktion der Aufrufargumente.** Zwei
Eingaben sind in der Komposition nicht ablesbar. `first_line` ist B's
UNGETRIMMTER erster Zug, das emittierte Item ist aber bereits um
`entry_trim` gekürzt — den Rückgabewert des Verbinders selbst —, und das
feuert auf den eingefrorenen Sütterlin-Sätzen bei **88 von 248 Nähten
(35 %)**. Der Austritt einer Majuskel wiederum ist der
Ornament-Rücklaufpunkt, nicht das Körperende. Beides ließe sich nur
rekonstruieren, indem die Glyphen-Vorbereitung (Ascender-Lean,
Laufform-Breite) außerhalb von `core` nachgebaut wird — der
Spiegel-Fehler eine Etage tiefer.

**Der Paritäts-Beweis** (`tests/test_pairlab_connector_parity.py`, auf
dem committeten Golden, ohne DB und ohne Wurzel): der Mitschnitt ändert
die Komposition nicht (Item für Item identisch), ein Abspielen mit
Verschiebung null liefert die Produktionskurve **Punkt für Punkt**, und
eine gemeinsame Horizontal-Verschiebung beider Buchstaben verschiebt die
ganze Naht um genau diesen Betrag. Eine Vertikal-Verschiebung wird
bewusst NICHT als Invariante behauptet: die Schwellen der Grammatik
(`HIGH_EXIT_Y`, `DESCENDER_EXIT_Y`, die Grundlinie) sind absolute Höhen,
ein y-Versatz darf einen anderen Zweig wählen.

**Wie weit lag der Spiegel daneben.** Gemessen auf der eingefrorenen
Wurzel `suetterlin-1922` `exported_at 2026-09-02T22:13:54+00:00`
`digest 2e3581287bed` / `suetterlin-1922-pairs` `22:13:53+00:00`
`cee9d363f497` (die Wurzel des `sep02`-Re-Baselines; die `sep03`-Wurzel
`57402ae7dd41` ist dateiweise dieselbe bis auf `exported_at`), BLAS auf
einen Thread. Über alle **248** Nähte der Wort- und Paar-Sätze, an der
unabhängigen Platzierung, beide Kurven bogenlängen-gleich abgetastet:

| | Nähte | Median der punktweisen Distanz |
|---|---|---|
| identisch | 159 | 0 |
| verändert | **89** (36 %) | 0,0562 xh (p90 0,2333, max 1,0833) |
| davon über dem Lineal-Fenster (> 0,12 xh) | 23 | — |
| davon im Fenster (0,05–0,12) | 25 | — |
| davon darunter | 41 | — |

Die Klasse mit dem größten Abstand sind die **Majuskel-Nähte** (11 Stück:
`S→…`, `O→f`, `K→u`, `B→i`, `I→n`, `D→u`) mit einem Median von **1,0365
xh** — der Spiegel startete am Körperende, die Produktion am
Arbeits-Austritt hinter dem Ornament-Rücklauf. Die 78 Minuskel-Nähte
liegen bei 0,0450 xh im Median, maximal 0,2785 (`p→r`); danach
`ſ→i` 0,2420, `ſ→c` 0,1974, `b→e` 0,1861.

**Und der Spiegel war nicht nur anders, er war schlechter.** `gen_chamfer`
(mittlerer Skelettabstand des generierten Verbinders zur Vorlage) über
alle 248 Nähte: Median **0,0434 → 0,0392**, Mittel **0,0601 → 0,0523**.
Über die 89 bewegten Nähte: Median 0,0645 → 0,0460, Mittel 0,0785 →
0,0569, **60 besser : 27 schlechter : 2 gleich**. Die Übergänge-Sektion
hat also seit dem 10.07. einen Verbinder vermessen, der der Platte im
Mittel rund 13 % ferner steht als der, den die Produktion zeichnet.

Zur Einordnung, hermetisch nachprüfbar: auf den Golden-Wörtern (44
Nähte) liegen 6 auf oder über dem 0,05-Boden des Lineal-Fensters, zwei
über seiner 0,12-Decke — `sitzen` ſ→i 0,1774 Median / 0,3980 max und
`lesen` ſ→e 0,1734 / 0,3968.

**Was sich dadurch bewegt** (alles report-only, keine Headline):
`gen_chamfer` und `gen_px` der Dissektion, damit die Übergänge-Overlays,
die `gen_chamfer`-Spalte eines KÜNFTIGEN `pairlab.harvest`-Laufs (die
GESPEICHERTEN Werte bleiben, wie sie sind) und die
`base_gen_*`-Spalten der chainbench-Stufe-A-Zeilen.

**Ein blinder Fleck, benannt statt entdeckt.** Nicht jede Entscheidung
über eine Naht fällt INNERHALB von `_connector_centerline`. Der
Austritts-Trim (`exit_trim`, Arm J4) ERSETZT die zurückgegebene
Mittellinie danach, im Block von `compose_word` selbst — ein Abspielen
gibt also die Naht ohne diese Regel wieder, und jede künftige Regel, die
den Verbinder ebenso nachbearbeitet, wäre hier ebenso unsichtbar. Heute
folgenlos: der Schalter ist Standard aus, auf jedem Headline-Lauf ist das
Abspielen die ganze Geschichte. Wird eine solche Regel je Default, muss
`replay` dieselbe Nachbearbeitung mitbekommen, sonst misst die
Dissektion still die falsche Kurve. Der Sensor `dspan` umgeht die Frage
von vornherein, indem er den GEZEICHNETEN Zug liest und nur die zwei
Tinten-Zugaben zurücknimmt (§14 „Übergänge S1").

**Was ausdrücklich unberührt bleibt.** `core/` und `core/word_metric.py`
(keine Zeile), der Golden, `word_loss`/`pair_loss`, `doff`/`dconn` in
`tools/wordbench/pairmeas.py`, die gespeicherten Vorkommen — und der
**Init der Kette**: `chain._connector_spec` ruft weiter den
eingefrorenen Spiegel. Sein Docstring erklärt ihn seit jeher zur
INITIALISIERUNG und nie zum Ziel; ihn nachzuziehen verschöbe das
Startbecken jedes Kettenfits und wäre damit eine deklarierte
Re-Baseline der Kette. **Das ist eine offene Frage an den Autor, kein
Nebenbefund dieses Eintrags.** Der Spiegel bleibt darum stehen, jetzt
aber mit ehrlichem Docstring: „die taute Kubik, der Stand vor der
Girlanden-Grammatik", mit seinen zwei erlaubten Verbrauchern.

### Übergänge S1 `sep04` — Vorregistrierung: `dspan`, die ausdehnungs-normierte Formdistanz

Der zweite Rettungsweg des #488-Negativs (§14 „Übergänge J4b",
Rettungswege, Punkt 2): **bauen, einfrieren, DANN den Arm neu
vorregistrieren — nicht umgekehrt.** Dieser Eintrag ist der Bau und
seine Abnahme; er registriert KEINEN Arm und bewegt keine Regel.

**Der blinde Fleck, den der Sensor schließen soll.** `dconn` legt den
komponierten und den gemessenen Verbinder je auf den EIGENEN ersten Punkt
und vergleicht Punkt i mit Punkt i. Solange beide dieselbe Strecke Pen-Weg
überdecken, ist das richtig. Verschiebt eine Regel die Grenze zwischen
Buchstabe und Verbinder, ist es falsch: J4s Austritts-Trim nimmt dem
Buchstaben seinen Stummel, der Verbinder zeichnet das Stück mit, wird am
KOPF länger — und `dconn` bucht die Verlängerung als Formunterschied. §14
„Übergänge J4" hat das nachgerechnet: von den +0,043 xh, an denen das
Gate scheiterte, waren rund zwei Drittel (Median +0,051 der Differenz)
genau dieser Rahmen-Artefakt.

**Empfindlichkeitsfenster gegen Defektgröße — warum keine Schwelle das
löst.** Das Wort-Lineal ist zwischen **0,05 und 0,12 xh** empfindlich.
Die Trimm-Länge selbst liegt im Median bei **0,185 xh** (p90 0,469,
max 0,504). Der Artefakt ist also GRÖSSER als der Defekt, den er
verdeckt; er lässt sich nicht abschneiden, er muss aus dem Maß heraus.

**Was `dspan` ist.** Beide Verbinder einer Naht enden am selben Ereignis
— der Ankunft des Stifts auf B. Also ist die Ankunft der Anker, und der
gemeinsame Abschnitt ist die letzte `L = min(Bogenlänge)` beider Kurven.
Der Anker muss dafür der ECHTE sein: die komponierte Seite ist der
gezeichnete Zug **ohne seine zwei Tinten-Zugaben** — ohne die
Überlappungs-Verlängerung von `CONNECT_OVERLAP` = 0,05 xh, mit der
`compose_word` beide Enden über die Naht hinausschiebt, damit die runde
Kappe unter die Nachbartinte rutscht, und ohne den Rücklauf-Präfix einer
Majuskel, der Tinte des BUCHSTABENS ist. Beides gehört nicht zur Form der
Naht, und für ein Maß, das am Ende ankert, ist die Verlängerung genau der
Betrag, den das Wort-Lineal gerade noch nicht sieht. Der Austritts-Trim
selbst bleibt dagegen drin — er ist die Wirkung des Arms
(`spanmeas.drawn_join`). Der Rest:
(1) beide vom Ende her auf `L` zurückschneiden, den Schnittpunkt
interpoliert, damit eine grobe Abtastung ihn nicht verschiebt; (2) beide
bogengleich auf `PAIR_CONNECTOR_POINTS` abtasten — dasselbe Budget, das
`dconn` und die Paar-Aggregation benutzen; (3) jede auf ihren eigenen
ersten Punkt DIESES Abschnitts legen (start-ausgerichtet, also
translationsfrei — die Platzierung bleibt allein `doff`s Spalte);
(4) mittlere punktweise Distanz, Einheit xh. Modul:
`tools/pairlab/spanmeas.py`, report-only, `core/word_metric.py` und
`pairmeas.py` unberührt.

**Zwei Eigenschaften, vorab genannt, damit sie später nicht als
Entdeckung durchgehen.** `dspan` ist BLIND gegen eine reine
Kopf-Verlängerung — dafür ist er gebaut; ob eine Naht länger laufen
SOLL, ist eine Frage an den Abgangspunkt und an die Platzierung, nicht
an diese Spalte. Und `dspan` ist nicht „`dconn` mit Korrekturterm": wo
die Ausdehnungen ohnehin gleich sind, sind beide dasselbe; wo nicht,
beantwortet `dspan` die engere Frage (ist das gemeinsame Stück dieselbe
Form?) und beantwortet sie sauber.

**Was „der Sensor sieht den Defekt" heißt — die Gates, vor der ersten
Zahl.**

- **P1 — blind gegen die Ausdehnung** (synthetisch, deterministisch):
  eine Kurve, die nur am Kopf um `e` verlängert wurde, hat über den
  gemeinsamen Abschnitt dieselbe Form → `dspan` = 0,000 für
  `e` ∈ {0,05; 0,2; 0,5}, während `dconn` mit `e` monoton steigt.
- **P2 — empfindlich auf die Form** (synthetisch): derselbe Abschnitt um
  eine Rampe der Höhe δ verzogen → `dspan` = δ/2 ± 0,005, und monoton
  wachsend in δ.
- **P3 — der bekannte Defekt aus #488** (die eigentliche Abnahme, auf der
  Wurzel, auf der #488 gemessen wurde: `suetterlin-1922`
  `digest 28ba1afebc53` / `suetterlin-1922-pairs` `f0cf3d53414c`,
  `exported_at 2026-09-02T08:00:29+00:00`): Basis gegen
  `--exit-trim`-Kandidat, gepaart je `(id, slot)`.
  **(a)** Der Artefakt muss verschwinden: |Δ `dspan`| ≤ **0,010**, gegen
  `dconn`s +0,043 auf denselben Nähten. **(b)** Die Fallquote muss auf
  der Seite der handbereinigten Lesung liegen, nicht der rohen:
  `dspan` fällt in ≥ **40 %** der bewegten Nähte (roh `dconn` 20 %,
  handbereinigt 51 %).
  Die absoluten Niveaus des Eintrags (0,102 → 0,099) werden daneben
  BERICHTET, aber ausdrücklich nicht als Gate gesetzt: die
  Handbereinigung von #488 hat den Kandidaten am alten Abgang der BASIS
  geschnitten, `dspan` schneidet gegen die GEMESSENE Kurve — eine andere
  Normierungsreferenz, deren exakte Übereinstimmung niemand versprechen
  kann.
- **N1 — Nullprobe Identität**: der gemessene Verbinder selbst als
  komponierter eingespeist → `dspan` = 0,000. Ein Sensor, der auf
  Identität feuert, misst seine eigene Verrohrung.
- **N2 — Nullprobe Platzierung**: eine reine Translation des
  komponierten Verbinders → `dspan` unverändert (|Δ| < 1e-9).

**Kill.** Verfehlt P3 (a) oder (b), ist der Sensor NICHT validiert; der
Eintrag schließt dann als ehrliches Negativ, `spanmeas.py` bleibt als
Instrument im Baum, und der Rettungsweg 2 des #488-Eintrags gilt als
gegangen und gescheitert — mit eigenem Rettungsweg, nicht mit einer
nachgezogenen Schwelle.

### Übergänge S1 `sep04` — gemessen: der Sensor ist validiert, und er rettet J4 trotzdem nicht

**Umgebung.** Gemessen auf der Wurzel, auf der #488 gemessen hat —
`suetterlin-1922` `digest 28ba1afebc53`, `suetterlin-1922-pairs`
`f0cf3d53414c`, beide `exported_at 2026-09-02T08:00:29+00:00` —, BLAS auf
einen Thread (`OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`), eine
Schrift pro Lauf (`suetterlin`), Basis und Kandidat derselbe Stack mit
genau einem Knopf Unterschied (`--exit-trim`). `core/compose.py` ist seit
#488 unverändert (nur Kommentar-Verweise auf den Journal-Umzug).

**Zuerst der Nachweis, dass es DERSELBE Arm ist.** Vier Kennzahlen des
#488-Eintrags reproduzieren exakt: 188 von 214 Nähten vergleichbar
(11 durch das `fit_ok`-Gate ausgeschlossen), **121 Nähte bewegen sich**
unter dem Trim („121 gefeuerte"), `dconn` fällt in **24** davon
(**19,8 %**, dort „20 % — 24 von 121"), und der **Paar-Satz bewegt sich
um null** (dort: „seine Klasse ist LEER"). Der Bench-Lauf desselben Arms
liefert dazu `seam_dep_median` **+12,52 → −1,39** — Ziffer für Ziffer der
Wert des Eintrags.

**Ein Instrument-Defekt, VOR der Veröffentlichung gefunden und behoben —
offengelegt, weil er die Zahlen bewegt hat.** Die erste Fassung des
Sensors ankerte auf dem EMITTIERTEN Zug. Der trägt aber an beiden Enden
die Überlappungs-Zugabe von `CONNECT_OVERLAP` = 0,05 xh, während der
geerntete gemessene Verbinder exakt an B's Eintritt endet — der
End-Anker lag also um genau den Betrag daneben, den das Wort-Lineal
gerade noch nicht auflöst, und das ausgerechnet bei einem Maß, das
gegen diesen Betrag gebaut ist. Der Review-Durchgang des PR hat es
gesehen. Behoben durch `spanmeas.drawn_join`: die Zugabe wird exakt
zurückgenommen (`_overlap_extend` hängt einen Punkt im Abstand
`CONNECT_OVERLAP` an — ein Schluss-Segment genau dieser Länge ist die
Zugabe und sonst nichts), der Rücklauf-Präfix einer Majuskel entfällt
über den Abgangs-Anker aus der Provenance, und der Austritts-Trim bleibt
drin, weil er die Wirkung des Arms ist. **Kein Gate wurde angefasst**;
die Vorregistrierung stand vorher und steht unverändert. Die Zahlen
unten sind die des korrigierten Sensors — und der Befund dreht sich
nicht: die Gates waren in beiden Fassungen grün (vorher Δ +0,0040 und
46,3 %).

**P1/P2 · N1/N2 — grün.** Die vier synthetischen Kontrollen stehen als
Tests (`tests/test_pairlab_spanmeas.py`): eine nur am Kopf um 0,05/0,2/0,5
verlängerte Kurve liest `dspan` = 0,000, während `dconn` monoton mitsteigt;
eine um δ verzogene Kurve liest δ/2 ± 0,005 und wächst monoton in δ.
Zusätzlich auf ECHTEN Zeilen beider Sätze: der gemessene Verbinder als
komponierter eingespeist ergibt `dspan` = 0,000000 (N1, Maximum über die
185 Nähte, deren gemessene Kurve genug Punkte für den Schnitt hat), eine
Translation des komponierten um (+1,7 / −0,9) xh bewegt ihn um 0,000000
(N2, Maximum über alle 218).

**P3 — die Abnahme am bekannten Defekt.** Medianwerte über die 121
gefeuerten Nähte, und daneben über alle 188 vergleichbaren. Beide
Spalten laufen auf DENSELBEN Kurven (`drawn_join`), sodass zwischen
ihnen nur der Anker verschieden ist — `dconn` hier ist also die
Kontrolle für den Anker, nicht die Spalte, die der Bench druckt:

| Spalte | Basis | Kandidat (`--exit-trim`) | Δ | Fallquote |
|---|---|---|---|---|
| `dconn` (Anker-Kontrolle), 121 gefeuerte | 0,0814 | 0,1429 | +0,0615 | 38/121 = 31,4 % |
| **`dspan`**, 121 gefeuerte | **0,0331** | **0,0367** | **+0,0036** | 59/121 = **48,8 %** |
| `dconn`, alle 188 | 0,0884 | 0,1242 | +0,0358 | — |
| `dspan`, alle 188 | 0,0394 | 0,0446 | +0,0052 | — |

**Gate (a) grün:** |Δ `dspan`| = **0,0036** (0,0052 über alle) gegen die
vorregistrierte Schranke 0,010 — und gegen +0,0615 derselben Kurven bei
Start-Ausrichtung. **Gate (b) grün:** `dspan` fällt in **48,8 %** der
gefeuerten Nähte gegen die vorregistrierten ≥ 40 %. **Der Sensor ist
validiert.**

Die Leiter, die dabei sichtbar wird, ist der eigentliche Beleg — vier
Lesungen derselben 121 Nähte, nach zunehmender Bereinigung:

| Lesung | Fallquote |
|---|---|
| `dconn` des Benchs, auf dem gezeichneten Zug samt Zugaben | 19,8 % |
| start-ausgerichtet auf dem bereinigten Zug | 31,4 % |
| **`dspan`** (End-Anker + Ausdehnungs-Normierung) | **48,8 %** |
| die Handbereinigung von #488, ad hoc gegen die Basis geschnitten | 51 % |

Der generische Sensor landet also da, wo die Handrechnung landete, ohne
ihre Zutat zu brauchen (sie schnitt den Kandidaten am alten Abgang der
BASIS ab und braucht dafür einen Basislauf; `dspan` braucht nur die
gemessene Kurve). Wie groß der Unterschied zum Bisherigen ist: bei **51
der 121** gefeuerten Nähte geben die beiden Anker die ENTGEGENGESETZTE
Richtung an. Und die Größe des Artefakts, den er entfernt: der
komponierte Verbinder wächst je gefeuerter Naht am Kopf um **0,2482 xh
im Median** (p90 0,4549, max 0,4621) — mehr als die Decke des
Lineal-Fensters (0,12), also genau die Größenordnung, die der
Vorregistrierungs-Absatz als unabschneidbar benannt hat.

**Und jetzt der Teil, der nicht gefällt: J4 ist damit NICHT gerettet.**
Das Gate, an dem der Arm gescheitert ist, verlangte eine Fallquote von
**≥ 60 %**. `dspan` kommt auf 48,8 %. Der Sensor beseitigt den
Rahmen-Artefakt vollständig — die Regel wird beurteilbar —, und die
Antwort der Hand bleibt trotzdem: **indifferent**. Was hier gewonnen
wurde, ist das Instrument, nicht der Arm. Ein neuer Austritts-Arm ist
möglich, aber er braucht eine eigene Vorregistrierung mit `dspan`-Gates
von Anfang an; `exit_trim` bleibt Standard aus, `compose.py` unberührt,
der Golden unberührt. (Die humanbench-Wortrunde, Rettungsweg 3 derselben
Zeile, ist unabhängig davon gebaut — §14 „Übergänge J4 `sep04`".)

**Basis-Lesung auf der HEUTE eingefrorenen Wurzel** (`suetterlin-1922`
`2e3581287bed` / `suetterlin-1922-pairs` `cee9d363f497`, die
LF11-Wurzel), damit der Sensor an der aktuellen Basis verankert ist:
Wörter `dspan` **0,0407** (n = 188, `dconn` 0,0868), Paare `dspan`
**0,1054** (n = 30, `dconn` 0,1609). Die Paar-Drills stehen erwartbar
schlechter — sie sind Einzelnähte ohne Wortkontext.

**Nebenbefund, gemeldet und NICHT stillschweigend korrigiert:** drei
Zahlen des #488-Eintrags ließen sich in dieser Sitzung nicht
reproduzieren, obwohl Wurzel, Code und Flags dieselben sind und die
Kernzahlen (121/24/20 %, `seam_dep` +12,52 → −1,39, Paare null) exakt
stimmen. Der Bench-Lauf des Arms liest `meas_dconn_median` **0,169**
(Eintrag: 0,148), `meas_doff_median` **0,177** (Eintrag: 0,160) und
`seam_arr_median` **−5,85** (Eintrag: −6,53); der BASIS-Lauf liest
`meas_dconn_median` 0,106 und `meas_doff_median` 0,128 gegen die dort
genannten 0,105 und 0,125. Die Abweichung betrifft ausschließlich die
Kandidaten-Spalten und ändert das Verdikt von #488 nicht: rot war die
FALLQUOTE, und die reproduziert auf die Naht genau. Der Eintrag bleibt
nach der Append-only-Regel unverändert stehen; hier steht, was heute
gemessen wurde. **Frage an den Autor**, ob die drei Werte nachgetragen
oder erklärt werden sollen.

---

### Platten-Nib A3 `sep04` — Vorregistrierung: die Wortrunde über die Strichbreite

Geschrieben und committet VOR der Runde. Arm zu Befund 20 / Frage F5 des
Audits vom 2026-09-02, entschieden vom Autor am 2026-09-04. Die Runde
selbst führt der Autor; dieser Eintrag legt fest, was sie beantworten
darf.

**Der Gegenstand.** Die öffentliche Schrift setzt heute den
chart-gepoolten Gleichzug-Nib: Halbbreite **0,07251 xh**, also ein Strich
von 0,145 xh. Aus den Wortproben derselben Hand ist eine Halbbreite von
**0,097 xh** gemessen — Strich 0,194, rund ein Drittel mehr. Der Arm
schreibt dieselben 63 Wortproben mit diesem Nib und sonst unverändert
(`wordarm.py --nib 0.097`, `constant_nib_units` im Resolver — kein
Core-Eingriff, der Schalter ist der bestehende).

**Warum das kein Lineal entscheiden kann — und der Grund ist schlimmer
als Blindheit.** Die Federbreite betritt `score_word` an genau einer
Stelle: `stroke_px` beim Rastern der Komposition für den Rück-Chamfer.
Von dort wirkt sie aber auf ZWEI der drei Terme — `edt_composed` speist
`coverage` (`core/word_metric.py`, `rev`) und `transition` (`t_rev`);
nur `width` kennt sie nicht, denn es vergleicht die x-AUSDEHNUNG der
Mittellinien. Und die Wirkung ist **einseitig**: ein breiterer Strich
rastert eine Obermenge, das Distanzfeld wird punktweise kleiner, beide
Terme können nur fallen.

Gemessen, mit der Geometrie festgehalten und nur der dem Lineal
genannten Feder verändert (63 Wortproben, dieselbe Wurzel):

| | loss | `coverage` | `transition` | `width` |
|---|---|---|---|---|
| Geometrie 0,0725, Lineal 0,0725 | 0,109218 | 0,101559 | 0,091429 | 0,162645 |
| Geometrie 0,0725, **Lineal 0,097** | **0,101560** | 0,091857 | 0,081958 | 0,162645 |
| Geometrie 0,097, Lineal 0,097 | 0,100833 | 0,092061 | 0,085154 | 0,151460 |

Die mittlere Zeile ist der Beleg: **−0,0077, ohne dass sich ein Punkt
der Komposition bewegt hat** — zwanzigmal die Größenordnung, an der in
dieser Kampagne ganze Arme gestorben sind, und `width` bleibt
byte-gleich. **Das Lineal belohnt die dickere Feder, gleich ob die Probe
so dick ist.** Ein Maß, das den Kandidaten konstruktionsbedingt
bevorzugt, kann diese Frage nicht entscheiden; die Menschenrunde ist
deshalb hier nicht ein Tie-Breaker, sondern das einzige Instrument, das
den Gegenstand unvoreingenommen anfasst. (Die dritte Zeile — der volle
Kandidat, 0,100833 — ist aus demselben Grund **keine** Evidenz für ihn.)

**Basis.** Wurzel `suetterlin-1922` `exported_at
2026-09-02T22:16:06+00:00` Digest `6cbab9d5c092`, Paar-Wurzel
`965ab3c57ebd`; BLAS auf einen Thread gepinnt. Reproduziert: Wörter
**0,109218** · Paare **0,148198** — der Stand NACH der LF11-Adoption,
also die Kompositionen, die Prod heute schreibt.

**Die Nebenbedingung des Audits ist schon trocken gerissen — und das
steht hier, bevor ein Urteil fällt.** Der Audit-Vorschlag nennt eine
Nebenprüfung: `gleichzug_doublings` darf mit dem breiteren Strich nicht
steigen (die Platzierung hält `INK_CLEARANCE` = 0,14 ein, gemessen am
alten Nib). Gemessen über die 63 Wortproben: **13 → 21 Verdopplungen,
7 Wörter bekommen eine neue.** Zwei Dinge gehören dazu, und beide
gegen die eigene Bequemlichkeit:

* Der Detektor ist **nib-relativ konstruiert** — sein Band läuft von
  `max(0,035; 0,5·nib)` bis `1,35·nib` perpendikularen Abstands
  (`tools/wordbench/gleichzug.py`). Ein Teil des Anstiegs ist also die
  Definition, die der Feder folgt. Das ist kein Artefakt, sondern der
  Zweck: ob zwei Striche als ein Klecks gelesen werden, IST eine Frage
  an die Federbreite.
* Wie auch immer man es liest: **die Bedingung, wie sie im Audit steht,
  ist nicht erfüllt.**

**Was die Runde deshalb entscheiden darf — vorab festgelegt.** Ein
Ergebnis ≥ 60 % für den Kandidaten lizenziert **nicht** den Wechsel des
ausgelieferten Nibs, sondern ausschließlich den **Folgearm**: die
Ink-Clearance an die Feder koppeln (`INK_CLEARANCE` in Nib-Radien statt
als Konstante) und den Nib danach neu vorlegen. Ein Ergebnis < 60 %
schließt den Arm — dann ist die breitere Feder weder schöner noch
verträglich, und die gemessene Plattenbreite bleibt ein Befund über die
Platte, keine Vorgabe für die Ausgabe. Diese Zuordnung steht hier, weil
sie hinterher nicht mehr glaubwürdig zu treffen wäre.

**Aufbau.** `ECHTHEIT/4`, 75 Bildschirme = 63 Wortproben + 12 blinde
gespiegelte Wiederholungen, Saat 20260004, Zoom 2×, Frage
„Welche Zeile sieht echter geschrieben aus?". Arme: Basis
`sha256 8538513b46fbd10c`, Kandidat `243f87a4135cb17c`.

**Der Kandidat ist an die Registrierung der Basis gepinnt**, und das ist
hier keine Formalie: ungepinnt wandert er **systematisch nach links** —
51 von 63 Wörtern negativ, nur 2 positiv, Mittel −1,56 px bei 31 px
x-Höhe. Der Grund ist mechanisch (der breitere Strich verbreitert das
gerasterte Wort, die beschränkte Suche zentriert nach), die Wirkung
wäre eine über die Runde lesbare Gruppen-Eigenschaft — genau das Leck,
gegen das die Pinn-Regel steht. Gepinnt unterscheiden sich die beiden
Seiten nur noch in der Feder.

**Verdachtsklassen** (`--strata`, deklariert vor der Runde):

| Klasse | n | Warum |
|---|---|---|
| `dicht` | 13 | Unter einem der beiden Arme läuft in diesem Wort Tinte zusammen (`gleichzug_doublings` > 0). Hier hat der schwerere Strich etwas zu verderben; welche 7 die Verdopplung erst unter dem breiten Nib bekommen, steht je Wort im Klassen-Vorschlag. |
| `frei` | 50 | Keine Verdopplung in beiden Armen. Wenn die breitere Feder allein schon echter aussieht, dann hier. |

Feiner geschnitten wären die beiden Hälften von `dicht` (7 neu, 6 schon
vorher) je unter `MIN_PAIRED_PER_CLASS` = 8 geblieben und trügen keinen
Anteil; zusammen sind sie eine ehrliche Klasse.

**Auswerteplan.** Unverändert der bindende aus
[`menschliche-bewertung.md`](menschliche-bewertung.md) („Der
Auswerteplan"): Verlässlichkeit zuerst (≥ 6 vollständige
Wiederholungspaare, Arm-Übereinstimmung über dem Münzwurf), dann die
Seitenbilanz, dann **Adoption bei ≥ 60 % Kandidat unter den
ENTSCHIEDENEN Bildschirmen und ≤ 25 % „kein Unterschied" über alle**,
dann die Klassen, dann Drift. **Gespiegelte Wiederholungen messen die
Verlässlichkeit und stimmen nie mit** — gezählt werden 63, nicht 75.

**Was die Runde nicht beantwortet.** Ob 0,097 der richtige Wert ist
(gemessen wird EIN Paar, nicht eine Leiter), ob der breitere Strich am
Bildschirm besser lesbar ist (eine andere Frage als „echter"), und
nichts über Kurrent oder Offenbacher — die Zahl stammt aus den
Sütterlin-Wortproben und gilt für diese Hand.

---

### Übergänge J4 `sep04` — Vorregistrierung: die Wortrunde als benannter Rettungsweg

Geschrieben und committet VOR der Runde. Sie ist nicht ein neuer Arm,
sondern **Rettungsweg (3) der J4-Zeile in `tintenfolger.md` §7.9**,
wörtlich dort vorgemerkt: „der Knick liegt unter der Auflösung des
Wort-Lineals und J4 ist ein fertiges Kandidatenpaar mit EINEM
Freiheitsgrad". Der Arm selbst ist gemessen und verworfen (§14
„Übergänge J4 `sep02`"); **keine Zahl dort wird angefasst.**

**Warum die Runde und nicht noch eine Zahl.** J4 fiel an Gate (b):
`dconn` sank nur in 20 % der gefeuerten Joins statt in 60 %. Die
Autopsie desselben Eintrags nennt den Grund, und er ist konstruktiv:
`dconn` misst die Form des Verbinders start-ausgerichtet, der Trim
verschiebt aber die GRENZE zwischen Buchstabe und Verbinder — das
getrimmte Stück ist länger, und zwei Drittel des Anstiegs sind
Rahmen-Artefakt. Ein Maß, das über eine verschobene Grenze nicht
urteilen kann, kann den Arm weder freisprechen noch verurteilen. Der
zweite Rettungsweg (ein ausdehnungs-normierter Formsensor) ist zu bauen
und einzufrieren, bevor er zählt; die Menschenrunde ist heute verfügbar.

**Basis, neu — der Arm steht heute anders da als am 2. September.**
Wurzel `suetterlin-1922` `exported_at 2026-09-02T22:16:06+00:00` Digest
`6cbab9d5c092`, Paar-Wurzel `965ab3c57ebd`, BLAS gepinnt. Auf dieser
Wurzel (LF11 adoptiert) gemessen:

| | Wörter | Paare | `seam_dep_median` |
|---|---|---|---|
| Basis | **0,109218** | 0,148198 | **+7,99°** |
| J4 (`--exit-trim`) | 0,109466 (**+0,000248**) | 0,148198 (byte-gleich) | **+0,02°** |

Zwei Verschiebungen gegenüber `sep02` und beide gehören genannt: LF11
hat den Abgangsknick schon von +12,52 auf +7,99 halbiert, J4 hat also
weniger zu tun als damals — und der Wort-Verlust dreht das Vorzeichen
(damals −0,000535, heute +0,000248). Der Knick verschwindet trotzdem
praktisch vollständig. **Die Runde entscheidet damit genau die Frage,
die übrig ist: ist ein Saum ohne Knick das wert, was er auf dem Lineal
kostet?**

**Aufbau.** `ECHTHEIT/5`, 75 Bildschirme = 63 + 12 gespiegelte
Wiederholungen, Saat 20260005, Zoom 2×. Arme: Basis
`sha256 8538513b46fbd10c`, Kandidat `404abd38fa2ef59b`
(`wordarm.py --exit-trim`, der Schalter des Komponisten, Standard aus —
kein Core-Eingriff, das Golden bleibt unberührt).

**Registrierung gepinnt**, hier fast wirkungslos und deshalb billig: von
63 Wörtern bewegt die Regel die beschränkte Suche in 3 überhaupt, in x
wie in y. Gepinnt ist sie in 0 — womit „Platzierung unangetastet", die
experimentelle Kontrolle der J4-Vorregistrierung, auch auf dem
Bildschirm buchstäblich gilt.

**Verdachtsklassen** (`--strata`, geschnitten daran, wie weit die Regel
die Zeichnung bewegt — symmetrischer Abstand der beiden Arme in
x-Höhen):

| Klasse | n | Warum |
|---|---|---|
| `naht-stark` | 31 | Δ ≥ 0,106 xh (Median der bewegten Wörter). Wenn der Trim irgendwo sichtbar hilft, dann hier. |
| `naht-schwach` | 29 | Bewegt, aber unter dem Median. |
| `unberuehrt` | 3 | Δ ≤ 0,005 xh — die Regel feuert nicht. **Die Kontrolle:** wer hier einen Unterschied sieht, sieht nicht den Trim. Mit n = 3 unter `MIN_PAIRED_PER_CLASS` = 8 und damit **beschreibend, kein prüfbarer Anteil** — das ist der Preis dafür, dass die Regel auf 60 von 63 Wörtern feuert. |

**Auswerteplan.** Derselbe bindende Plan wie in der Runde davor,
einschließlich der Schwellen (≥ 60 % / ≤ 25 %) und der Vorbedingung aus
den Wiederholungen; Wiederholungen stimmen nie mit, gezählt werden 63.

**Was ein Ergebnis auslösen darf.** Die Adoption von J4 hieße:
`exit_trim` als Default an und das Golden-Fixture deklariert neu backen
— eine rendernde Änderung, also Autor-Entscheid, nicht Automatik. Ein
Ergebnis ≥ 60 % legt sie ihm vor; ein Ergebnis < 60 % schließt den
Rettungsweg (3) der §7.9-Zeile, und übrig bleiben (1) nur die
Ankunftsseite und (2) der Sensor.

**Was die Runde nicht beantwortet.** Ob der Trim auf der ANKUNFTSSEITE
richtig ist — J4 verschlechtert sie messbar (−3,40 → −6,53 auf der
`sep02`-Wurzel), und das bleibt ein eigener Arm. Und nichts über
`dconn`: das Maß ist dafür konstruktiv ungeeignet, das war der Anlass.
