# Übergangs-Befund 2026-07-11 — unabhängige Paar-Sektion (pairlab)

> **Status (2026-08-03): Befund-Journal.** Momentaufnahme aus `tools/pairlab`
> vom 2026-07-11, wird nicht fortgeschrieben: O1 und O2 (B-Seite) sind
> umgesetzt (Lauf `jul11`, PR #179), der A-seitige d-Stub-Trim wurde zweimal
> gemessen und verworfen (`jul11` und R4-Lauf `jul17`, PR #220), O3 ist
> überholt — die Paar-Overrides existieren seit Redesign R3 als sparsame
> `glyph_pairs`-Schicht, der §4-Generator bleibt Default.
> Der methodische Kern (Platzierung aus der Messung herausnehmen, Klassen
> statt Paare, §5b Duktus-Trace als Soll-Kopplung) bleibt Begründungsquelle
> für die Composer-Konstanten; der aktuelle Stand der Übergänge steht in
> [`../reference/qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md) §6.
> **Eine Fortschreibung gibt es doch — §5c (2026-08-03)**: die Kettenfit-Messung
> zu Issue #278 Stufe A setzt den §5b-Duktus-Trace direkt fort und wird deshalb
> hier und nicht in einem eigenen Dokument abgelegt.

O1 und O2 (B-Seite) sind umgesetzt — Compose-Loop `jul11`,
[`qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md) §6 (Wort-Headline
0,1253 → 0,1183; Joins mit ≥ 0,25 xh Soll-Korrektur 31 → 21). Der
A-seitige d-Stub-Trim wurde gemessen und VERWORFEN (Deckung besser,
Übergangs-Komponente bestraft die Spannen-Ausdehnung konstruktionsbedingt —
Details ebd.); O3 bleibt vertagt. Werkzeug:
`tools/pairlab` (Diagnostik). Bezieht sich auf
[`architektur.md`](../concepts/architektur.md) §4 („Übergänge sind
Konsequenz, keine Daten") und die offene Diskussion in
[`planaenderungen.md`](planaenderungen.md) Vorschlag B; Vorgeschichte in
[`qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md) §6 (Läufe `jul02`,
`jul08` inkl. Verworfen-Einträge E4/E6).

## 1. Fragestellung

Trotz des Übergangs-Redesigns (`jul02`) und des Endstrich-Laufs (`jul08`)
sind einzelne Sütterlin-Verbindungen sichtbar falsch. Die Nutzer-These: es
genügt womöglich **nicht**, zwischen dem letzten Punkt von Buchstabe A und
dem ersten Punkt von Buchstabe B einen Verbindungsstrich zu generieren —
schon das **letzte/erste Stück der Glyphen selbst** müsste sich für einen
sauberen Übergang anpassen. Zu klären:

1. Wo genau liegt der Fehler — Konnektor-Form, Platzierung oder
   Glyphen-Enden?
2. Ist das **generisch** lösbar (Regeln/Klassen) oder braucht es
   **pro Paar** hinterlegte Formen (viel Autoring-Arbeit, Spannung zu §4)?

## 2. Methode: die Platzierung aus der Messung herausnehmen

Die Wort-Bench bewertet den Übergang **an der komponierten Platzierung** —
ein schiefer Konnektor und ein falsch platzierter Buchstabe sind dort
untrennbar vermischt. Genau daran ist der E4-Lauf (`jul08`, Stub-Trim +
Diagonal-Platzierung, verworfen) gescheitert: der Eingriff an den Stubs
wurde durch das gleichzeitig veränderte Platzierungsmodell unmessbar.

`tools/pairlab` (neu) entfernt den Störfaktor: für jedes **echte Vorkommen**
eines Buchstabenpaars in den Abb.-19-Wörtern und Abb.-20-Paaren wird

1. das Wort mit dem Produktions-Composer komponiert (Provenance an),
2. **jeder Buchstabe unabhängig optimal eingepasst** (begrenzte
   Translations-Gittersuche seiner eigenen Körper-Centerlines gegen das
   eingefrorene Proben-Skelett, ±0,6 xh horizontal / ±0,2 xh vertikal),
3. der Produktions-Konnektor **zwischen den unabhängig platzierten
   Buchstaben neu generiert** (identische Konstanten/Guards wie
   `core/compose.py`) und sein Chamfer zur Probe gemessen,
4. der **echte Verbindungszug** der Probe extrahiert (Skelett-Verfolgung
   durch die Lücke zwischen den Tintenspalten) und
5. das **Anpassungs-Profil** gemessen: Abweichung des letzten Strichs von A
   bzw. des ersten Strichs von B von der Probe als Funktion der Bogenlänge
   ab dem Join — `tail_adapt`/`head_adapt` = Bogenlänge (xh), über die die
   echte Feder von der Template-Form abweicht (Schwelle 0,12 xh).

87 Vorkommen über 45 Paare vermessen (alle scorbaren Treffer der gefragten
Paare; Reproduktion s. §7). Overlays: `temp/pairlab_*.png`.

## 3. Befund 1 — die Platzierung ist der größte Einzelfehler

Median der nötigen horizontalen Korrektur (max. der beiden Buchstaben eines
Paars): **0,19 xh**; P75 0,36 xh, P90 0,52 xh. **39 von 87 Vorkommen
brauchen ≥ 0,25 xh Korrektur** — der Fehler akkumuliert entlang langer
Wörter (Advance-/Clearance-Modell), z. B. `Galoppieren` −0,52 xh am r.
Ein formal perfekter Konnektor landet dann trotzdem auf falscher Tinte:
ein Großteil der „sehr falschen" Übergänge im Live-Bild ist ein
Platzierungs-, kein Formfehler.

## 4. Befund 2 — die Standard-Diagonale ist generisch richtig

Für die Brot-und-Butter-Verbindungen liegt der neu generierte Konnektor
**nach** unabhängiger Platzierung praktisch auf der Probe (Chamfer ≤ 0,07,
Anpassung 0):

`e→r` 0.028 · `e→i` 0.040 · `e→n` 0.062 · `n→e` 0.042 · `n→n` 0.062 ·
`u→n` 0.043 · `i→e` 0.035 · `t→e` 0.032 · `f→e` 0.024 · `g→e` 0.014 ·
`h→a` 0.041 · `z→w` 0.031 · `w→e` 0.068 · `longs→a` 0.063 · `b→z`/`v→x`/`r→z` ≤ 0.054

Auch die Tangenten stimmen: generiert +36…+44°, Probe 33…53°. Die im
`jul08`-Loop als systematisch schlecht gemessenen `f→e`/`t→e` (0.220/0.204
an komponierter Platzierung) sind hier unauffällig — ihr Bench-Penalty war
Platzierung (t/f-Vorkommen brauchen ±0,3…0,6 xh Korrektur), nicht
Übergangs-Form. **§4 hält für diese Klasse:** exit/entry + Tangenten
erzeugen den richtigen Übergang.

## 5. Befund 3 — die Stubs: bei Hoch-Exits schreibt die Feder die
## Glyphen-Enden um (These bestätigt, aber klassenweise)

Die schlechten Paare gruppieren sich fast vollständig nach der
**Exit-Klasse des ERSTEN Buchstabens** — und die Abweichung sitzt in den
**Kopplungs-Stubs** der Chart-Zellen (Entry-Stub: Anstrich von halber Höhe
zum Bogenscheitel; Exit-Stub: Grundlinien-Fuß auf halbe Höhe), nicht im
Buchstabenkörper:

| Klasse (A-Exit) | Paare (gen-Chamfer) | tail_adapt | head_adapt |
|---|---|---|---|
| **d-Schleife** (hoher Schleifen-Exit) | d→e 0.170, d→p 0.200, d→z 0.162, d→f 0.140, d→x/d→o 0.11, d→s/d→t/d→k 0.06–0.09 | **0,17–0,31 konstant über ALLE d-Paare** | 0–0,43 (e 0,36, p 0,31) |
| **Deckstrich-Bogen** (o, b, v, w) | o→n 0.119, b→i 0.187, b→s 0.113, b→p 0.095, v→s 0.185, v→p 0.129, w→i 0.087 | b→i 0,22, w→i 0,21, sonst ~0 | 0,14–0,31 (n nach o 0,30) |
| **r-Arm** (Deckstrich auf x-Höhe) | r→e 0.115, r→x 0.119, r→p 0.107 | ~0 (der Arm ist echte Tinte) | **0,23–0,29** |
| **Versalien** | B→i 0.258, I→n 0.249, D→u 0.195, O→f 0.129 | 0,15–0,36 | 0–0,45 |
| Langes ſ → Unterlängen-Folge | longs→g 0.208 | 0 | 0,37 |

Geometrie des echten Zuges (Overlays `d→e` ×4, `o→n` ×2, `b→i`): die Feder
verlässt die Form **am letzten Strukturpunkt** (d: Schleifenkreuzung ~0,8 xh;
o/b/v/w: Bogenende; r: Armende) und fällt in **einer** Diagonale direkt in
den **Scheitel des ersten Abstrichs** des Folgebuchstabens. Beide Stubs —
A-Exit-Stub und B-Entry-Stub — existieren auf der Tafel **nicht**; unser
Konnektor überbrückt stattdessen die Stub-Spitzen (das „Shelf" aus dem
E4-Befund, hier erstmals platzierungsbereinigt und pro Paar quantifiziert:
Stub-Ersatzlänge 0,2–0,4 xh je Seite). Deutlichster Winkel-Beleg `b→i`:
generierter Abgang **+44°** (steigende Bogen-Tangente, trotz Launch-Clamp),
echter Zug **−60°** (fallend).

Sekundärbefund (Autoring, nicht Compose): die r-Form weicht mittig 0,1–0,2 xh
von der fließenden Probe ab (Profile `r→e`), passend zum offenen
buchstabenspezifischen Verdacht aus `jul08` Runde 2/3.

## 5b. Duktus-Trace: das echte Paar nachgefahren (Nachtrag, gleicher Tag)

Auf Nutzer-Vorschlag fährt pairlab die echten Paare jetzt zusätzlich **entlang
des bekannten Duktus nach**: der M4-Fit (`core/fit.py`,
`fit_template_to_instance` — Stroke-Struktur + Ecken bleiben erhalten,
Tikhonov-regularisiert) warpt beide Templates auf die Tinte der Probe
(buchstabenlokales Skelett-Fenster). Das gefittete Paar + der verfolgte
Verbindungszug IST der kontinuierliche **Soll-Pfad** des Vorkommens — die
perfekte Zielvorgabe für den Generator (violett in den Overlays; `fit
exit/entry` in Caption/JSON; `--no-trace` schaltet ab).

Abgelesene Soll-Kopplungen (gefittete Endpunkt-Geometrie, xh / Grad):

| Klasse | Soll-Abgang (A) | Soll-Ankunft (B) |
|---|---|---|
| Arkaden-Diagonale (e→n/e→r/u→n/n→e) | y 0,43–0,68 @ +29…+44° | y 0,47–0,67 @ +31…+52° |
| Deckstrich/Arm (r→e, o→n) | **y 0,81–0,87 @ +2…+13° (eben!)** | **y 0,60–0,72 = Scheitel**, nicht Stub-Fuß |
| Schleifen-Exit (d→e, b→i) | Fit-Endpunkt y 1,2–1,5 auf der Flanke — der Stub hat keine eigene Tinte (Trim-Signal); echter Abgang laut Zugverfolgung y ≈ 0,8 fallend | y 0,60–0,72 = Scheitel |

Lesart der beiden Kennwerte: bei braven Diagonalen stimmen Fit-Endpunkt und
Zugverfolgungs-Abgang überein; klafft dazwischen eine Lücke (d, b), wurde der
Exit-Stub vom Fit in die Schleifenflanke absorbiert — genau das ist die zu
trimmende Strecke. Die O2-Kopplungsanker sind damit nicht mehr Schätzwerte,
sondern **pro Klasse gemessen**; und für einen späteren Vorschlag-B-Import
liefert derselbe Fit die geernteten Paar-Geometrien gleich mit.

## 5c. Kettenfit: Buchstabe–Verbinder–Buchstabe als EIN Zug
## (Nachtrag 2026-08-03, Issue #278 Stufe A)

§5b fährt das echte Paar entlang des Duktus nach, aber in **zwei unabhängigen**
M4-Fits plus einer nachträglichen Zerlegung des Verbindungszuges
(`analyze._real_join`). Issue #278 fragt, was passiert, wenn stattdessen
**eine** Feder durchläuft. `tools/pairlab/chain.py` fittet dazu
`Buchstabe → Verbinder → Buchstabe` als EIN Problem:

* **Drei Segmente, ein Ankerfeld.** Links und rechts die **Chart-Zeile**
  (Variante 0 — bindende Randbedingung 2 des Issues, nie die Laufform), in der
  Mitte der bei der komponierten Platzierung erzeugte Verbinder, dessen 22
  innere Punkte **freie Anker ohne Formregularisierung** sind (Randbedingung 3).
* **Die Naht ist ein Ankerindex, keine Strafe.** Der letzte Anker des letzten
  NICHT-diakritischen Strichs von L und der erste von R sind mit den
  Verbinder-Endpunkten **dieselben Parameter** — C0-Stetigkeit gilt per
  Konstruktion, nicht per Gewicht. Damit wandert die Schnittstelle vom
  Tintenlücken-Kriterium (pro Vorkommen verschieden, bei Berührung undefiniert)
  auf einen überall gleichen Index.
* **Platzierung bleibt Platzierung.** Pro Slot ein eigener,
  **unregularisierter** Translationsblock in den Schranken des heutigen
  Rastersuchlaufs (`FIT_DX_UNITS` 0,6 / `FIT_DY_UNITS` 0,20); der Verbinder
  bekommt keinen eigenen Block, sondern eine bogenlängen-lineare Rampe zwischen
  den beiden Nachbarn.
* **Deckung paarweit und gekappt.** Das Skelettfenster ist die **Vereinigung**
  beider Buchstabenfenster mit geschlossenem Loch dazwischen, das
  Punktbudget skaliert mit der Segmentzahl, und die Deckungsdistanz ist
  Huber-gekappt (0,30 xh), damit fremde Tinte im Paarfenster begrenzte Hebelwirkung hat.

Gemessen mit `tools/pairlab/chainbench.py`, beide Pfade (heutiger
Unabhängig-Fit als Basislinie · Kette als Kandidat) über **dieselben**
Vorkommen derselben eingefrorenen Proben: **248 Vorkommen über 96 Proben und
134 verschiedene Paare** (214 aus den 63 Wörtern, 34 aus den 33 Paar-Übungen
der Abb. 20). Die Abb.-22-Schülerschrift ist eine **andere Hand** und bleibt
draußen.

### Kalibrierung: `CHAIN_CONNECTOR_SMOOTH_WEIGHT`

Der Verbinder darf nicht gegen seine erzeugte Form regularisiert werden (das
würde `gen_chamfer` zugunsten des Generators verfälschen), braucht aber
*irgendeine* Glättung, sonst zerfällt eine freie Polylinie im 1-px-geglätteten
EDT. Gewählt wurde eine reine **Krümmungsänderungs-Strafe** (zweite Differenz
über die eigenen Anker) — formfrei, aber wirksam. Ein Sweep über den
Paar-Satz (34 Vorkommen, Basislinien-M1 konstant 0,618):

| Gewicht | M1 Kette | beide/nur Kette/nur Basis/keins | M2 | Verbinder konv. | M3 dconn (Median) | Naht tail (Median) | tail P90 | Seiten > 0,4 xh |
|---|---|---|---|---|---|---|---|---|
| 0 | 0,676 | 20/3/1/10 | 8/8 | 34/34 | 0,223 | **0,700** | 2,132 | **54 %** |
| 3e-6 | 0,676 | 20/3/1/10 | 7/8 | 32/34 | 0,195 | **0,406** | 1,070 | 26 % |
| **1e-5** | **0,676** | **20/3/1/10** | **7/8** | **31/34** | **0,197** | **0,370** | 1,106 | 24 % |
| 3e-5 | 0,618 | 19/2/2/11 | 7/8 | 27/34 | 0,190 | 0,374 | 1,073 | 25 % |
| 1e-4 | 0,559 | 17/2/4/11 | 7/8 | 26/34 | 0,193 | 0,374 | 0,984 | 25 % |
| 3e-4 | 0,529 | 16/2/5/11 | 7/8 | 23/34 | 0,181 | 0,381 | 0,891 | 25 % |
| 1e-3 | 0,500 | 15/2/6/11 | 6/8 | 17/34 | 0,178 | 0,339 | 0,913 | 24 % |
| 3e-3 | 0,294 | 9/1/12/12 | 4/8 | 12/34 | 0,162 | 0,301 | 0,893 | 19 % |
| 1e-2 | 0,147 | 5/0/16/13 | 2/8 | 7/34 | 0,174 | 0,316 | 0,711 | 22 % |

Die beiden Enden sind je ein eigenes Versagen. **Ohne** Glättung frisst der
freie Verbinder den Auslauf des linken Buchstabens: Naht-Anteil im Median
0,70 xh, 54 % aller Seiten jenseits der in §5 gemessenen
Stub-Ersatzzone von 0,2–0,4 xh — die Segmentierung wäre dann eine Eigenschaft
des Lösers, keine der Hand. **Mit** starker Glättung versteift die geteilte
Naht die Buchstaben-Enden mit, und die Buchstaben-Konvergenz bricht ein
(0,50 bei 1e-3, 0,15 bei 1e-2). Gewählt nach der vorab festgelegten Rangfolge
(Nahtanteile im gemessenen Band → M1 maximal → M3 minimal):
**`CHAIN_CONNECTOR_SMOOTH_WEIGHT = 1e-5`** — das größte Gewicht, bei dem der
Naht-Median noch im Band liegt (0,370 xh; bei 3e-6 verlässt er es mit 0,406)
und die Buchstaben-Konvergenz auf ihrem Maximum steht. **Systematischer Effekt,
offen ausgewiesen:** ein etwas rauherer Verbinder — M3 dconn-Median 0,197 xh
statt 0,178 xh bei 1e-3 — und die Kalibrierung ist am Paar-Satz **in-sample**;
die Wort-Zahlen unten sind insoweit die ehrlicheren.

### Die vier Stufen-A-Kennzahlen

**M1 — Konvergenz (Ziel: ≥ heutige Trace-Rate). Verfehlt.**
Gepoolt Basislinie **0,746**, Kette **0,665** (n = 248); paarweise
beide 156 · nur Kette 9 · nur Basislinie 29 · keins 54, Vorzeichentest
p = 0,0017. Getrennt: Paar-Satz 0,618 → **0,676** (nur Kette 3, nur Basis 1,
p = 0,63 — der kalibrierte Satz), Wort-Satz 0,766 → **0,664** (nur Kette 6,
nur Basis 28, p = 0,0002). Die Diagnose ist wichtiger als die Zahl: von den 99
durchgefallenen Ketten-Buchstabensegmenten scheitern **70 an der Deckung** und
nur 29 an der Geometrie, und die Geometrie-Residuen sind praktisch gleich
(Kette 1,23 px vs. Basislinie 1,15 px im Median). Die Kette wird also nicht
schlechter, sondern **strenger benotet**: ihr Deckungsfenster schließt das Loch
zwischen den Buchstaben, und die Verbinder-Tinte wird per Nächster-Sample-Regel
teils den Buchstaben zugeschlagen, während das buchstabenlokale Fenster der
Basislinie sie nie sah. Ein Nebenbefund in dieselbe Richtung: die Kette liegt
in **0 von 248** Vorkommen auf einer Platzierungsschranke, der Rastersuchlauf
in 13.

**M2 — heute leere Übergänge (die eigentliche Begründung). Erfüllt.**
`_real_join` liefert bei **38 von 248** Vorkommen nichts (die Buchstaben
berühren sich), die Kette liefert dort in **33 Fällen (87 %)** einen
konvergierten Verbinder mit zugeordneter Tinte. Schwerpunkte: c→h 5/6, e→r 4/4,
e→n · e→l · n→d je 2/2. Das ist genau die Klasse von Übergängen, die heute
messtechnisch nicht existiert.

**M3 — Verbinderform gegen den aus der Tinte gelesenen Zug. Verfehlt.**
Wo beide existieren (n = 210): generiert Median **0,034 xh**, Kette **0,086 xh**;
paarweise Δ +0,046, besser 25 · schlechter 184, p ≈ 0. Nach Klasse
(gen → Kette): Arkaden-Diagonale 0,030 → 0,078 · Versal 0,063 → 0,095 ·
Deckstrich/Arm 0,029 → 0,117 · Schleifen-Exit 0,056 → **0,256**. Einschränkung
bei der Lesart: der Ketten-Verbinder überspannt **konstruktionsbedingt einen
anderen Bogen** als der ink-gelesene (er besitzt die Stub-Zone, der andere
beginnt erst an der Tintenlücke), ein Teil der Distanz ist also definitorisch
und nicht Formfehler. Als Kreuzvalidierung gegen Prior-Kontamination taugt die
Zahl damit nicht — und positiv belegt ist sie ebenfalls nicht.

**M4 — Buchstabenform gegen das MAD-Rauschen. Knapp verfehlt, aber ohne
Verzerrungssignal.** Rauschboden aus den H1-Aggregaten der Hand
(`GET /hands/suetterlin-1922-norm/aggregates`, 13 Schlüssel, gepoolter
Anker-MAD **0,0112 xh**). Kette vs. unabhängiger Trace: mittlere Δ im Median
**0,0269 xh** (P90-Δ im Median 0,0571), also gut das Doppelte des Bodens;
**55 %** der Anker bleiben innerhalb ihres eigenen MAD (aggregat-gestützt für
370 der 496 Seiten, Median dort 0,558). Entscheidend für die Deutung: die
**Verformung gegenüber der Chart-Zeile** ist bei der Kette *kleiner* als beim
unabhängigen Trace (0,0140 vs. 0,0170 xh). Die Kette verbiegt die Buchstaben
also nicht stärker, sie stellt sie anders hin.

### Kill-Kriterien: keines ausgelöst

* **Auslauf-Stubs.** Das Kill-Signal wäre ein systematisch *größerer*
  `tail_stub_delta` als beim unabhängigen Trace. Gemessen ist das Gegenteil:
  paarweise Δ Median **−0,0060 xh**, größer 47 · kleiner 192 · gleich 9,
  p ≈ 0. Nach Klasse Arkade −0,0070 · Versal −0,0015 · Deckstrich −0,0040 ·
  Schleifen-Exit +0,0030 (die einzige Klasse mit positivem, aber winzigem
  Vorzeichen).
* **Versalien.** n = 22, Basislinie **0,636**, Kette **0,636** — identisch;
  Geo-RMSE 1,30 px gegen 1,19 px bei den Kleinbuchstaben, maximale
  Ankerauslenkung 0,126 vs. 0,124. Keine Divergenz genau dort, wo der
  unabhängige Pfad ohnehin am schwächsten ist.
* **Nahtkalibrierung.** Naht-Anteil tail Median **0,080 xh** (P90 0,465),
  head 0,020 (P90 0,259); nur **9 %** aller Seiten liegen über 0,4 xh.
  Klassenmedian Deckstrich/Arm 0,300 · Schleifen-Exit 0,183 · Arkade 0,069 ·
  Versal 0,000. Auf dem Paar-Satz allein ist der tail-Median 0,370 — die
  Übungspaare haben die größeren Lücken. Die Naht bleibt im gemessenen Band
  bzw. darunter.

### Verdikt der Stufe A: **bedingtes Ja zu Stufe B**

*(Die beiden Vorbedingungen sind inzwischen abgearbeitet — die Nachmessung
darunter ersetzt die Empfehlung dieses Abschnitts.)*

Stufe A tötet die Idee nicht — kein einziges Kill-Kriterium schlägt an, und das
stärkste Einzelargument des Issues ist bestätigt: 87 % der heute
unmessbaren Übergänge werden messbar (M2), die Platzierung wird stabiler
(0 Schrankenfälle statt 13), die Buchstaben werden weniger verbogen als heute.
Aber drei der vier Kennzahlen gehen wörtlich genommen nicht auf, und zwei davon
aus benennbaren, behebbaren Gründen. Empfehlung deshalb **nicht** „go", sondern
**bedingtes go**, mit zwei Vorbedingungen vor Stufe B:

1. **M1 vergleichbar machen.** Die Deckungszuordnung entscheidet das Ergebnis,
   nicht die Fitqualität (70 von 99 Fehlschlägen sind Deckungs-, nicht
   Geometriefehler). Solange ein Buchstabe in der Kette gegen Tinte benotet
   wird, die ihm im Basislinien-Fenster nie zugerechnet wurde, ist „Konvergenz
   ≥ heute" keine gleichnamige Größe. Entweder das Buchstaben-Gate auf das
   buchstabenlokale Fenster zurückbinden oder das Basislinien-Gate auf dasselbe
   Vereinigungsfenster heben — und dann neu messen.
2. **M3 auf gleichem Bogen messen.** Erst der auf die Tintenlücken-Endpunkte
   beschnittene Ketten-Verbinder ist mit dem ink-gelesenen vergleichbar.
   Bis das gezeigt ist, dürfen Ketten-Verbinder **nicht** in `pair_aggregates`
   fließen — die Kreuzvalidierung gegen Prior-Kontamination steht aus, und
   `gen_chamfer` ist die Auditzahl, die genau davon lebt.

Ohnehin unverändert gilt: das ist eine **Messschicht**. Nichts hiervon ändert
das Rendering, `glyph_pairs` bleibt der sparsame Verbatim-Override, der
§4-Generator bleibt Default; der einzige Rückweg ins Schreiben bleibt
`apply-laufform` und die Klassenregeln.

Kostenhinweis für die Stufen-B-Planung: ein Ketten-Fit über ein Paar braucht
im Median 10,5 s bei ~530 Parametern (248 Vorkommen ≈ 42 min CPU, 7,7 min
mit `--jobs 8`). Ein siebenbuchstabiges Wort ist rund die vierfache
Parameterzahl.

### Nachmessung: die beiden Vorbedingungen (Nachtrag, gleicher Tag)

Beide Vorbedingungen sind abgearbeitet — als **Mess**änderung, nicht als
Modelländerung. Der Fit ist Zeile für Zeile derselbe: M2 (33/38), M4
(0,0269 xh gegen 0,0112 xh MAD-Boden, 0,0140 vs. 0,0170 xh Chart-Verformung)
und alle drei Kill-Blöcke kommen im neuen Lauf zahlengleich wieder heraus.
Verändert wurde ausschließlich, **woran** gemessen wird.

**Änderung 1 — das Buchstaben-Gate hängt am buchstabenlokalen Fenster.**
Über `chain.ChainSegmentSpec.cov_window_px` trägt jedes Buchstaben-Segment sein
eigenes `trace_letter_ductus`-Fenster (`body_px ± TRACE_WINDOW_MARGIN·xh`). Der
**Fit** sieht unverändert das Vereinigungsfenster — dass der Verbinder die Tinte
der Lücke besitzt, ist der ganze Zweck der Kette und darf nicht wegkalibriert
werden —, der **gemeldete** Deckungsrest eines Buchstabens zählt aber nur noch
Punkte aus seinem eigenen Fenster: genau dem Fenster, in dem der unabhängige
M4-Trace immer schon benotet wurde. Der Verbinder behält das Vereinigungs-Gate.
Zusätzlich als dritte Spalte die symmetrische Alternative — die
Basislinien-Traces gegen dieselben Deckungspunkte, mit derselben
Nächster-Sample-Zuordnung und demselben dritten Konkurrenten (dem erzeugten
Verbinder), also die Basislinie nach der Kettenregel benotet.

| Gate | Basislinie | Kette | beide/nur Kette/nur Basis/keins | p |
|---|---|---|---|---|
| Vereinigungsfenster (Stufe A) | 0,746 | 0,665 | 156/9/29/54 | 0,0017 |
| **buchstabenlokal (gleichnamig)** | 0,746 | **0,690** | 156/15/29/48 | 0,049 |
| Basislinie auf Vereinigung | 0,810 | 0,665 | 164/1/37/46 | 3·10⁻¹⁰ |

Nach Satz getrennt (buchstabenlokal): Wörter 0,766 → **0,692** (nur Kette 12,
nur Basis 28, p = 0,017), Paare 0,618 → 0,676 — bei den isolierten Übungspaaren
ändert das Fenster gar nichts, dort liegt zwischen den Buchstaben nichts, was
falsch zugeordnet werden könnte.

Das lokale Fenster streicht überhaupt nur bei **60 von 496** Buchstabenseiten
Punkte (im Mittel 0,5 % der zugeordneten Deckung) — und kippt damit 6 Vorkommen
ins Konvergierte. Es waren also wenige fremde Punkte, die den Deckungsrest über
die Schwelle zogen, nicht ein grundsätzlich anderer Maßstab. Die Fehlerzerlegung
liegt jetzt exakt vor (pro Zeile mit ihrem eigenen xh gegen `core.fit`s
Schwellen, nicht mehr überschlagen): von **99** durchgefallenen
Ketten-Buchstabensegmenten scheitern **58 nur an der Deckung, 12 nur an der
Geometrie, 29 an beidem**; unter dem lokalen Gate sind es 92 (51/12/29). Die
Stufe-A-Angabe „70 an der Deckung, 29 an der Geometrie" ist damit präzisiert:
die Deckung dominiert, aber ein knappes Drittel der Fehlschläge ist (auch)
Geometrie.

**Befund 1: der M1-Rückstand ist echt, nicht bloß Benotung.** Er schrumpft von
8,1 auf **5,6 Punkte** und bleibt signifikant; in die andere Richtung gemessen
wird er sogar größer (0,810 gegen 0,665). Die Stufe-A-Vermutung erklärt einen
Teil des Abstands, nicht das Ganze. **M1 bleibt verfehlt** — jetzt aber als
benannte Eigenschaft der Kette statt als Verdacht auf ein Messartefakt, und
lokalisiert: c (4/14), Z (1/3), m (5/9), p (6/12) tragen den Rückstand, während
u (20→22/28) und h (11→13/16) gerade die Buchstaben sind, denen das gleichnamige
Fenster hilft.

**Änderung 2 — M3 auf gleichem Bogen.** Der Ketten-Verbinder besitzt
konstruktionsbedingt die beiden Stub-Zonen, der ink-gelesene beginnt erst an der
Tintenlücke; ein Teil des Stufe-A-Abstands war deshalb definitorisch. Die
Nachmessung schneidet **alle drei** Kurven (erzeugt · Kette · ink-gelesen) auf
**ein** gemeinsames x-Intervall — die Tintenlücke der Probe
(`analyze._ink_extent_x`, dieselben Kanten, zwischen denen `_real_join` verfolgt)
geschnitten mit der eigenen x-Spanne jeder Kurve — und wendet danach die
unveränderte pairmeas-Formel an (Bogenlängen-Resampling auf
`PAIR_CONNECTOR_POINTS`, Startpunkt-Ausrichtung, mittlerer punktweiser Abstand).

| M3 | n | generiert | Kette | paarweise Δ | besser/schlechter | p |
|---|---|---|---|---|---|---|
| ganze Kurve (Stufe A) | 210 | 0,034 | 0,086 | +0,046 | 25/184 | ≈ 0 |
| **bogengleich** | 193 | **0,028** | **0,040** | **+0,011** | 63/125 | 1·10⁻⁵ |

Nach Klasse (bogengleich, gen → Kette): Arkaden-Diagonale 0,026 → **0,036** ·
Deckstrich/Arm 0,023 → **0,029** · Versal 0,058 → **0,060** ·
Schleifen-Exit 0,058 → **0,228**. Der gemeinsame Bogen ist im Median 0,181 xh
lang (Tintenlücke im Median 0,251 xh); 17 der 210 Vorkommen haben keinen
gemeinsamen Bogen und werden gezählt, nie gemittelt.

**Befund 2: rund drei Viertel des Stufe-A-Abstands waren definitorisch.** Der
Ketten-Verbinder liegt auf gleichem Bogen nur noch 0,011 xh hinter dem
generierten statt 0,046 xh, bei Deckstrich/Arm (+0,088 → +0,006) und Versalien
(+0,032 → +0,002) verschwindet der Unterschied praktisch ganz. Was übrig bleibt,
ist **eine** Klasse: der Schleifen-Exit (d, ſ) mit +0,170 xh — kein Messartefakt,
sondern derselbe Befund wie in §5, dass die Feder dort das Glyphen-Ende umschreibt
und die Kette diesen Bogen anders auflöst als die Tinte. M3 geht damit wörtlich
genommen weiterhin nicht auf, aber die Zahl ist jetzt **belastbar** und zeigt auf
eine Klasse statt auf das Verfahren.

### Empfehlung nach der Nachmessung: **Ja zu Stufe B, mit benannter Auflage**

Beide Vorbedingungen waren Forderungen an die *Messung*, und beide sind erfüllt.
Ihr Ergebnis ist gemischt und fällt in verschiedene Richtungen:

* **M3 ist weitgehend entlastet** — der Einwand war zu drei Vierteln
  definitorisch, der Rest ist auf den Schleifen-Exit konzentriert. Die
  Kreuzvalidierung gegen Prior-Kontamination ist damit erstmals möglich.
* **M1 ist bestätigt statt entkräftet** — der Rückstand ist kleiner, aber real.
  Die Kette konvergiert pro Buchstabe seltener als zwei unabhängige Fits, und
  das ist eine Eigenschaft des gekoppelten Problems, keine der Benotung.

Zusammen mit dem unverändert gültigen Rest der Stufe A (kein Kill-Kriterium,
87 % der heute unmessbaren Übergänge werden messbar, 0 statt 13 Schrankenfälle,
weniger Verformung gegenüber der Chart-Zeile) reicht das für ein **Ja zu
Stufe B** — aber mit zwei Auflagen, die jetzt *in* Stufe B mitlaufen statt
davor zu stehen:

1. **Das buchstabenlokale Gate ist ab sofort die M1-Schlagzeile.** Stufe B misst
   Konvergenz gleichnamig oder gar nicht, und darf 0,690 nicht unterschreiten —
   ein Wort-Kettenfit mit vier Nähten hat mehr Gelegenheiten, Buchstaben-Enden
   zu versteifen, nicht weniger.
2. **Der `pair_aggregates`-Bann bleibt, jetzt aber klassenscharf begründet.**
   Ketten-Verbinder fließen weiterhin nicht in die Paar-Statistik: nicht mehr,
   weil die Zahl unvergleichbar wäre (sie ist es jetzt), sondern weil der
   Schleifen-Exit mit +0,17 xh systematisch danebenliegt und `gen_chamfer`
   genau davon lebt, unkontaminiert zu sein. Fällt diese Klasse auf das Niveau
   der übrigen, entfällt die Auflage.

Unverändert gilt: das ist eine **Messschicht**. Nichts hiervon ändert das
Rendering, `glyph_pairs` bleibt der sparsame Verbatim-Override, der §4-Generator
bleibt Default.

### Reproduktion

```bash
# Kalibrier-Sweep (Konstante in tools/pairlab/chain.py zwischen den Läufen setzen)
uv run python -m tools.pairlab.chainbench --set pairs --json temp/cal_1e-5.json

# der Stufen-A-Lauf dieses Abschnitts
uv run python -m tools.pairlab.chainbench --set all --jobs 8 \
    --aggregates temp/aggregates.json \
    --json temp/stage_a_full.json --csv temp/stage_a_full.csv

# die Nachmessung (identischer Aufruf; M1 druckt jetzt drei Gates + die
# Fehlerzerlegung, M3 zusätzlich die bogengleichen Mediane pro Klasse)
uv run python -m tools.pairlab.chainbench --set all --jobs 8 \
    --aggregates temp/aggregates.json \
    --json temp/stage_b_pre.json --csv temp/stage_b_pre.csv
```

Die Nachmessung braucht keinen eigenen Schalter: beide Gates und beide
M3-Varianten stehen in jeder Zeile des JSON/CSV
(`chain_*_converged` / `chain_*_converged_local`, `base_converged_union`,
`dconn_*` / `dconn_*_matched`), ein Lauf liefert alle Spalten. Laufzeit
unverändert ~7,8 min mit `--jobs 8`.

Der MAD-Boden für M4 stammt aus `GET /hands/suetterlin-1922-norm/aggregates`
(admin-gated, als JSON abgelegt und über `--aggregates` gereicht); ohne die
Datei berichtet M4 die Deltas ohne gemessenen Boden und sagt das auch.
Fixtures: `tools/wordbench/fetch_fixtures.py` (API-Pfad, für Sessions ohne
Cloud-SQL-Zugang) oder `tools/wordbench/export_fixtures.py` (DB-Pfad).

## 6. Beantwortung der Kernfrage + Lösungsoptionen

**Generisch lösbar — als Klassenregel, nicht pro Paar.** Die Abweichungen
erklären sich durch wenige Exit-Klassen × eine Entry-Regel („kopple am
Scheitel des ersten Abstrichs"); kein Kleinbuchstaben-Paar verhält sich
idiosynkratisch (deckt sich mit der Vorschlag-B-Residualtabelle vom
2026-07-08). Nur die Versal-Verbindungen (post-MVP-Scope) sind Kandidaten
für echte Paar-/Verkettungsformen.

Empfohlene Reihenfolge:

1. **O1 — Platzierung zuerst** *(umgesetzt, Lauf `jul11`: Hoch-Exit-Tuck
   + Rückwärts-Exit-Clearance)*: das Advance-/
   Clearance-Modell gegen die gemessenen Ist-Abstände der Tafel kalibrieren
   (pairlab liefert die Soll-Verschiebungen pro Vorkommen). Erst danach ist
   jeder Form-Eingriff sauber messbar — die E4-Lektion.
2. **O2 — Kopplungsanker statt Stub-Spitzen** *(B-Seite umgesetzt, Lauf
   `jul11`: Anker auf der steigenden Flanke bei y 0,78 + Entry-Stub-Trim,
   dazu der Level-Auslauf am Wortende; der A-seitige d-Trim wurde gemessen
   und auf der eingefrorenen Metrik verworfen — s. Statuskopf)*
   (generisch, klassenbasiert):
   pro Template zur Renderzeit zwei ableitbare Ankerpunkte bestimmen —
   B-seitig der Scheitel des ersten Abstrichs (erstes lokales y-Maximum
   innerhalb ~0,5 xh Bogenlänge), A-seitig der letzte Strukturpunkt
   (Schleifenkreuzung/Bogenende statt Stub-Spitze). Ist der A-Exit hoch
   (≥ ~0,7 xh: d-Schleife, Deckstrich-Bögen, r-Arm), wird der Übergang
   **Anker→Anker** generiert und die Stub-Stücke im **gebundenen** Kontext
   weggelassen (gemessene Ersatzlänge 0,2–0,4 xh). Die Soll-Werte pro Klasse
   liegen seit dem Duktus-Trace (§5b) gemessen vor: Deckstrich-Klasse eben
   (+2…+13°) bei y ≈ 0,85 abgehen, am Scheitel y ≈ 0,6–0,7 ankommen.
   Wortanfangs-Stubs bleiben — sie SIND der Anstrich (E2-Erkenntnis). Nur
   Renderpfad, Template bleibt Chart-Messung (Prinzip wie
   `FLUENT_BODY_PITCH`); Absicherung über den Wort-Bench-Loop, `pair_loss`
   als Report.
3. **O3 — Paar-Overrides (Vorschlag B) vertagen:** nach O1+O2 neu messen;
   nach heutiger Evidenz für Kleinbuchstaben unnötig. Erst mit der
   Versal-Phase wieder prüfen (B→i/I→n/D→u sind die stärksten Kandidaten
   für echte gefittete Paare). Die Provenance-Naht in `core/compose.py`
   bleibt der Hook.

Nicht wieder anfassen (Verworfen-Einträge bleiben bindend): pauschaler
`CONNECT_GAP`, Ganzhöhen-Clearance, uniformer Wortanfangs-Anstrich (E2),
Level-Join-Begradigung (E6). O2 ist **nicht** E4: E4 trimte blind auf halbe
Höhe und änderte gleichzeitig die Platzierung; O2 koppelt an gemessenen
Strukturpunkten und setzt die separat gelöste Platzierung (O1) voraus.

## 7. Reproduktion

```bash
# einmalig: Fixtures einfrieren (DB nötig)
uv run python -m tools.wordbench.export_fixtures --set all

# Beispiele dieses Befunds
uv run --extra viz python -m tools.pairlab re de on bi --json temp/pairs.json
uv run --extra viz python -m tools.pairlab longs,g d,e --max-occ 4
```

Werkzeug-Doku: `tools/pairlab/README.md`. Die Zahlen dieses Dokuments:
87 Vorkommen, Batches als JSON unter `temp/pairlab_batch*.json`
(gitignored, reproduzierbar mit obigen Kommandos).
