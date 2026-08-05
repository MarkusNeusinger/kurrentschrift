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

### Nachtrag: degenerierte Solves — M1 ist 0,754, nicht 0,690

Der oben als „echte Eigenschaft des gekoppelten Problems" eingestufte
M1-Rückstand war zu rund zwei Dritteln **ein Fehler in der Initialisierung**.
`analyze._generate_connector` gibt seine volle Bézier-Unterteilung aus, gleich
wieviel Platz die Komposition zwischen den Buchstaben lässt, und begrenzt seinen
Griff nach unten auf 0,05 xh; wo zwei Buchstaben aufeinander sitzen, überschreibt
dieser Boden den eigenen Entwurfswert `0,4·Sehne`, die Kubik greift weiter aus
als die Sehne lang ist und kehrt um — zwei Dutzend Anker in einer Kuspe von
~0,05 xh Bogenlänge, Nachbarpunkte 8·10⁻⁵ xh auseinander.
`chain._second_difference_operator` skaliert mit 1/ds², der Glättungsblock geht
damit rund 10⁷-fach steifer in die Hesse-Matrix ein als bei einem normalen
Übergang: `e_smooth(x0)` 5,2·10⁶ gegen 53,7, `f(x0)` 51,9 gegen 0,026. **24 der
248 Vorkommen** — jedes `c→h`, `r→e`, `m→u`, `n→e` — verbrauchten ihr gesamtes
Iterationsbudget auf das Geraderichten dieses Verbinders und beendeten den Solve
mit `e_geo`, `e_cov` und `e_wid` unverändert auf sechs Nachkommastellen: die
Buchstaben bewegten sich überhaupt nicht. Sichtbar wurde das erst, nachdem
`chainbench` die Abbruchmeldung des Optimierers exportierte — die Zeilen lasen
bis dahin einen Schlüssel `status`, den `chain.py` nie schreibt.

`chain.regularise_connector_anchors` diskretisiert einen Verbinder unterhalb von
`CHAIN_CONNECTOR_MIN_SPAN_UNITS` Sehne neu: dieselbe Kurve, bogenlängen-treu auf
die Ankerzahl abgetastet, die diese Sehne tragen kann. Die Form bleibt, die
Endpunkte bleiben exakt (die Nahtanker sind mit den Buchstaben geteilt), oberhalb
der Schwelle wird nichts angefasst — die anderen 224 Zeilen kommen Feld für Feld
identisch wieder heraus, kein einziger Konvergenz-Umschlag.

| Gruppe (buchstabenlokales Gate) | n | Basislinie | Kette vorher | Kette nachher |
|---|---:|---:|---:|---:|
| degenerierte Solves | 24 | 0,542 | 0,167 | **0,833** |
| übrige | 224 | 0,768 | 0,746 | 0,746 |
| **gepoolt** | 248 | 0,746 | 0,690 | **0,754** |

Damit ist **M1 erfüllt**: die Kette konvergiert gleichnamig gemessen häufiger als
zwei unabhängige Fits (paarweise 21 nur Kette gegen 19 nur Basislinie statt 15
gegen 29). M3 bogengleich verschlechtert sich dabei nicht (Kette 0,040 → 0,038,
paarweiser Median +0,011 → +0,008). Die Auflage 1 oben bleibt inhaltlich
bestehen, ihre Untergrenze ist jetzt **0,754** statt 0,690. Was der Befund
„M1 ist bestätigt statt entkräftet" richtig gesehen hat, steht in §5c weiter:
`c`, `p` und ein Teil der `e` scheitern schon in der Basislinie an der Deckung —
das ist Autorenarbeit an den Chart-Zeilen, kein Solver-Thema.

### Nachtrag: loop-exit — die Klasse war zweimal falsch gemessen

Die letzte offene Auflage („`pair_aggregates` bleibt für Ketten-Verbinder zu,
solange der Schleifen-Exit mit +0,17 xh danebenliegt") stützte sich auf
bogengleich **0,058 → 0,228 xh** über 26 Vorkommen. Beides ist Messfehler, in
zwei gestapelten Schichten; der Ketten-Verbinder ist auf dieser Klasse nicht
schlechter, sondern besser als der erzeugte.

**Schicht 1 — die ink-gelesene Referenz war blind.** `analyze._real_join` liest
die Feder-Spur nur innerhalb `JOIN_BAND_Y` (Deckel 0,8 xh). Das ist das
Freiraumband des Komponisten, keine Aussage darüber, wo Übergänge liegen: ein
Schleifen-Exit verlässt die Form bei y ≈ 1,04–1,13 xh und sein Übergang läuft
eben bei ≈ 0,9–1,0 xh — komplett darüber. Gemessen über alle 248 Vorkommen sah
der Tracker in der Klasse nur **4 von 18** Spalten der Lücke (Arkaden-Diagonale
6/6), jedes `d→*` lieferte 0–5 Punkte, und `connector_points` fiel damit auf die
gerade Sehne exit→entry zurück. M3 maß auf `d→*` also „Abstand zu einer Geraden",
und der erzeugte Verbinder gewann, weil er selbst fast eine ist. Zusätzlich wurde
`seed_y` auf den Deckel geklemmt, ein Viertel xh unter dem echten Abgang, worauf
die Nächster-y-Regel auf die Tinte **unter** dem Übergang sprang — bei `b→p` auf
die Unterlänge des p, bei `o→r` ins Leere. Der Deckel folgt jetzt dem Exit
(`max(JOIN_BAND_Y[1], exit_y)`) — keine neue Konstante, und da er nur steigen
kann, bleibt jedes Paar mit Exit im Band Feld für Feld identisch. Betroffen sind
32 Zeilen: alle 17 `d→*`, 14 Deckstrich/Arm (b/o/r bei 0,83–0,97) und `D→u`;
die `longs→*` mit ihrem Unterlängen-Exit hatten ihre Referenz immer schon.

**Schicht 2 — „bogengleich" war spannengleich, nicht bogengleich.**
`chainbench.dconn_matched_arc` schnitt alle drei Kurven auf **ein x-Intervall**.
Das ist nur so lange ein Bogenschnitt, wie eine Kurve in x eindeutig ist — die
ink-gelesene ist es als Spalten-Track immer, die erzeugte meist, der
Ketten-Verbinder eines Schleifen-Exits **nicht**: er besitzt den Abstieg von der
Schleife und den Sturz in den Folgebuchstaben, beide nahezu senkrecht. Im Band
trug sein Stück deshalb das **1,69-fache** des Referenzbogens bei gleicher
x-Spanne (Arkade: 0,91-fach), und `dconn` verglich nach dem
Bogenlängen-Resampling schlicht verschiedene Orte. Jetzt definiert die Referenz
die Strecke: sie wird wie bisher auf die Tintenlücke geschnitten, die beiden
anderen Kurven werden auf denselben Schreibabschnitt getrimmt
(`trim_to_reference_arc`, Schnitt zwischen den nächsten Punkten zu den beiden
Referenz-Enden).

| M3 bogengleich (gen → Kette) | vorher | nachher |
|---|---|---|
| Arkaden-Diagonale (n 132) | 0,027 → 0,034 | 0,026 → 0,029 |
| Deckstrich/Arm (n 29) | 0,022 → 0,029 | 0,023 → 0,033 |
| Versal (n 17) | 0,059 → 0,060 | 0,055 → 0,065 |
| **Schleifen-Exit (n 24)** | 0,058 → **0,228** | **0,074 → 0,050** |
| gepoolt, paarweiser Median | +0,008 (66/126, p 3·10⁻⁵) | **+0,002 (94/105, p 0,48)** |

Auf den 63 Wort-Tafeln allein — dem Korpus, um den es geht — steht der
Schleifen-Exit bei **gen 0,081 → Kette 0,034** (n 14, paarweiser Median
−0,0425). Der erzeugte Verbinder ist dort nach der Korrektur die **schlechteste**
aller vier Klassen: er sackt unter die Tinte, während die Kette auf ihr liegt
(Overlays `das`, `der-3`, `laden`, `die`). Das ist ein eigener, offener
Generator-Befund — O2 aus §6 bleibt damit gültig und ist jetzt beziffert —, aber
er ändert das Rendering und gehört nicht in diese Messschicht.

M1, M2-Ausbeute, M4 und alle drei Kill-Blöcke sind unberührt: `chain.py` liest
`_real_join` nicht. M1 buchstabenlokal bleibt exakt **0,754**, jedes
Konvergenz-, Residuen-, Energie- und Stub-Feld kommt Feld für Feld identisch
wieder heraus; nur M2s Nenner sinkt von 38 auf **32** leere Übergänge (28/32
= 88 % Ausbeute), weil sechs davon jetzt lesbare Tinte haben.

**Die Auflage bleibt trotzdem — aus einem neuen, hier erst sichtbaren Grund.**
Die Klasse ist entlastet, aber die Aufschlüsselung nach Tafelart legt etwas
anderes frei: auf den **Paar-Übungen der Abb. 20** entgleist der Ketten-Verbinder
in **11 von 23** Vorkommen (Schleifen-Exit 0,052 → 0,345, Deckstrich 0,018 →
0,112) — eine lange gerade Diagonale quer durch beide Buchstaben, teils
rückwärts laufend. Auf den Wort-Tafeln passiert das in 3 % der Zeilen. Keine
dieser elf Zeilen wird von der heutigen QC erwischt: alle melden
`chain_c_converged` und `chain_connector_yielded` wahr und liegen auf keiner
Schranke. Da `pair_aggregates` Wortfuge und Paar-Übung bewusst unter demselben
`kind` poolt, würde genau dieser Satz die Auditzahl `gen_chamfer` verseuchen.
Die Auflage steht also weiter, ihre Begründung wechselt aber vollständig: nicht
mehr „der Schleifen-Exit liegt daneben" (das war die Messung), sondern
**„der Ketten-Fit degeneriert auf isolierten Paar-Übungen"** — dieselbe Familie
wie der Nachtrag darüber, anderer Auslöser (kein kurzer Sehnenabstand, sondern
die komponierte Platzierung zweier freistehender Buchstaben). Das ist die
nächste Vorbedingung, und sie ist klassenunabhängig.

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

### Nachtrag: Stufe B, Runde 1 — Teilschreibung (2026-08-04)

Die erste Ernte über den Ketten-Pfad ist gelaufen und **teilweise** geschrieben.
Kommando: `uv run python -m tools.laufform.harvest --sets words,pairs --path chain --jobs 8`,
96 Fälle, 344 Slot-Zeilen, **232 Vorkommen** (213/277 Wörter, 19/67 Paare, alle
Identitäten eindeutig).

**Torstand: 5 bestanden · 4 verfehlt · kein Kill ausgelöst.** Verfehlt sind die
Detektorrate auf den Wort-Tafeln (7,5 % gegen die 3-%-Schranke), die
Detektorrate auf den Paar-Tafeln (18/34, davon 17 links von `d b longs r D`),
der **Iterationsdeckel** (87/96 Solves brechen bei `maxiter=300` ab,
`optimizer_success` 9,4 %) und die Ausbeute auf `e` (−10) und `n` (−5). Kein
Kill-Kriterium hat gefeuert: M1 buchstabenlokal 0,754 gegen Basislinie 0,746,
Chart-Verformung Kette 0,0207 gegen Slot 0,0272, `tail_stub` paarweise −0,0040,
G3 `laufform_dev` Median 0,0068 / Max 0,0118 über die zwölf geschriebenen
Bestandsschlüssel.

**Der Iterationsdeckel hat eine zweite, erst jetzt sichtbare Folge.** Er stand
ohnehin als Punkt 1 der Runde-2-Liste, weil ein gedeckelter Solve nicht im
stationären Punkt endet. Genau das macht die Ernte aber auch **nicht
bit-reproduzierbar**: der Endpunkt eines abgeschnittenen Solves ist eine
Funktion seines Startpunkts, und der Startpunkt ist die komponierte
Platzierung. Eine Wiederholung desselben Laufs auf identischem Code, aber mit
Fixtures aus dem **exakten** statt dem 4-stellig zurückgelesenen Nib —
ein Init-Unterschied von 8,75e-6 xh — reproduzierte alles Robuste exakt
(96/96 Fälle, 344/344 Slot-Zeilen, 19/67 Paare, 16 von 18 Schlüsselzahlen,
jede `laufform_dev` innerhalb 0,0006) und bewegte genau drei Zahlen um je
genau 1: `e` 29→28, `a` 13→12, Gesamtstand 233→232. Das ist die Signatur von
Grenzfall-Kippern an den Toren (`converged_local`, `geo_rmse ≤ 2,2`,
Konnektor-Degeneriertheit), nicht die anderer Daten. **Konsequenz für die
Doktrin:** solange 87/96 Solves am Deckel abbrechen, ist „dieselben Zahlen wie
letztes Mal" kein erreichbares Reproduktionskriterium — jede Fixture-Änderung
verschiebt einige Grenzfälle. Ein Reproduktions-Gate muss deshalb auf die
robusten Größen zielen (Fallzahl, Slot-Zeilen, Schlüsselzahlen ±1,
`laufform_dev`-Toleranz), nicht auf Bit-Gleichheit.

**Geschrieben wurde** (Freigabe des Eigentümers, in-session): 232 Vorkommen
(`instances`, `replace`), 77 Wortspuren (`word_instances`, `replace`, erstmals
mit Verbinder-Zügen), Aggregat-Neuaufbau auf 35 Schlüssel und
`apply-laufform` auf **genau 15**: `a d e g h i l m n r u w` plus die
Neuanlagen `S` `sz` `z`. Bench-Wirkung gegen die frische Nulllinie desselben
Fixture-Standes: **Wörter 0,116886 → 0,115623 (−0,001263)**, Paare 0,164506 →
0,165519 (Details und die Nib-Komponente in qualitaetsmetrik.md §6,
Re-Baseline `aug04`).

**Nicht geschrieben:** `t` (Stichprobe 8→3, unter jedem sinnvollen `min_n`, und
der einzige Schlüssel über seinem eigenen MAD — seine Laufform steht jetzt
bewusst veraltet), `o` (+0,00177 allein), `c` (+0,00022, aber der größte
Ausbeutegewinn 1→7 und deshalb ein Ansehen-Fall), `b` (±0). Alles mit
`min_n < 4` bleibt ohnehin außen vor.

**Runde-2-Liste**, in dieser Reihenfolge:

1. **Iterationsdeckel** — 87/96 abgeschnitten; billigste offene Frage und nach
   dem Obigen zugleich die Ursache der fehlenden Bit-Reproduzierbarkeit.
2. `e` (−10) und `n` (−5) — zwei Drittel des Ausbeuteverlusts, keine
   Grenzfälle (Verhältnis-Median 1,50, 11 Blowouts > 2,0); fällt vermutlich
   mit Punkt 1.
3. Detektorrate 7,5 % auf den Wort-Tafeln, konzentriert auf `t`-Deckstrich
   und `e`.
4. Erst danach `o`, `c`, `b` und die `min_n < 4`-Kandidaten — und die oben
   benannte Vorbedingung, die Degeneration des Ketten-Verbinders auf den
   isolierten Paar-Übungen.

### Nachtrag: Stufe B, Runde 2 — der Deckel ist erledigt, das Tor nicht (2026-08-04)

Punkt 1 der Liste ist gemessen und abgeräumt, und die Messung hat die
Reihenfolge der restlichen Punkte umgeworfen.

**Der Deckel war der bindende Stopp — deutlicher als vermutet.** Sweep über die
eingefrorenen `words,pairs`-Fixtures (96 Solves, 344 Slot-Zeilen), je ein
`--diag-csv`-Lauf, mit den neuen Spalten `iterations` / `hit_iteration_cap`:

| `maxiter` | am Deckel | `not_converged_local` | akzeptiert | `geo_rmse` Median | CPU |
|---|---|---|---|---|---|
| 300 | 87 (91 %) | 47 | 232 | 1,063 px | 1942 s |
| 900 | 63 (66 %) | 38 | 238 | 1,030 px | 5315 s |
| 2700 | 10 (10 %) | 35 | 241 | 1,027 px | 10145 s |
| **8100** | **0 (0 %)** | 35 | 241 | 1,027 px | 10608 s |

300 war nicht knapp, sondern lag **unter dem Median dessen, was ein
konvergierender Ketten-Solve braucht**: Median 1211 Iterationen, p25 680,
p90 2518, Maximum 4215. Neuer Default `CHAIN_MAX_ITER = 8100` in
`tools/pairlab/chain.py` — ein EIGENES Budget, nicht
`core.fit.DEFAULT_MAX_ITER`, denn das ist ein Pro-Glyph-Budget und darf sich
durch eine Ketten-Messung nicht mitbewegen (es speist Wizard, `/fit`,
`/diagnostic`).

**Warum 8100 und nicht der Punkt, an dem der Ertrag aufhört zu steigen:** Ein
Deckel, der überhaupt bindet, ist der falsche Knopf. L-BFGS-B hört bei seinem
eigenen Kriterium auf, also kostet ein hoher Deckel für jeden bereits
konvergierenden Solve **nichts** — nur der schwere Rest zahlt. Gemessen ist
dieser Rest billig: 2700 → 8100 kauft „kein Solve wird mehr abgeschnitten"
für **+5 % CPU**, bei ~1,9-facher Reserve über dem beobachteten Maximum.

**Und es richtet nachweislich keinen Schaden an** — der Teil, den man prüfen
und nicht annehmen muss: 305 der 344 Slot-Zeilen sind gegenüber 2700
**bit-identisch**; die 39 bewegten gehören ausschließlich zu den zehn vorher
gedeckelten Belegen; die Bewegung ist Setzrauschen (Median +0,0010 px,
schlimmster Fall +0,0240 px, 22 Zeilen schlechter gegen 17 besser); und
**alle 344 Gate-Urteile sind unverändert**. Das Ergebnis hört auf, die Antwort
des Budgets zu sein, und wird die des Modells — ohne eine andere zu werden.
Die zehn befreiten Solves brauchen 2701–4215 Iterationen, lagen also samt und
sonders knapp *oberhalb* von 2700; der Wert hätte mitten in der Häufung
gelegen. Die Geometrie ist über die ganze Leiter stabil: 228 der 241
akzeptierten Slots werden bei allen Budgets akzeptiert.

**Punkt 2 ist damit zu einem Drittel erklärt, nicht erledigt.** Der Deckel holt
von `e` 4 der 9 fehlenden Vorkommen zurück (30 → 34) und von `n` 3 von 5
(29 → 31). Der Rest ist kein Konvergenzproblem.

**Der eigentliche Befund: das Ausbeutedefizit ist fast vollständig EIN Tor.**
Gleicher Fixture-Stand, gleiche Sets, gleiche `--rmse-max`, Slot-Pfad gegen
Ketten-Pfad:

| | akzeptiert |
|---|---|
| Slot-Pfad | 270 |
| Kette @2700 | 241 |
| Kette + nur vom Konnektor-Wächter verworfen | **287** |

Die 46 Differenzzeilen sind **ausschließlich** an `connector_degenerate`
gescheitert — dem letzten Tor der Kaskade. Sie haben `converged_local`
bestanden, liegen unter `--rmse-max`, sind nicht am Anschlag und haben
passende Ankerzahl; ihr `geo_rmse`-Median ist 1,131 px gegen 1,027 px bei den
akzeptierten, also schlechter, aber weit innerhalb der 2,2-px-Schranke. Der
Slot-Pfad kennt dieses Tor **gar nicht**. Auf den gemeinsamen Toren liegt die
Kette also nicht hinten, sondern mit 287 gegen 270 vorn.

Verteilung der 46: 23 Wort-, 23 Paar-Zeilen — bei 277 Wort- gegen 67
Paar-Zeilen ist die Rate auf den Paar-Übungen rund viermal so hoch (32,8 %
gegen 7,9 %; die 7,9 % bestätigen die 7,5 % der Runde 1). Gründe:
`seam_share` 25, `backward_arc` 22, `arc_vs_gap` 2.

**Konsequenz für die Reihenfolge:** Punkt 3 der Runde-1-Liste ist keine
Aufräumarbeit am Rand, sondern der dominante Ausbeuteterm und rückt vor Punkt 2
und 4. Die Frage ist nicht „warum verliert die Kette `e`", sondern **„ist der
Konnektor-Wächter auf den Paar-Übungen kalibriert oder feuert er dort auf eine
legitime Form"** — die Paar-Drills sind nah an der Tafelform geschrieben, mit
kurzen oder fehlenden Verbindern, also genau der Fall, für den die Schwellen
nicht kalibriert wurden.

**Reproduktion:**

```
uv run python -m tools.wordbench.fetch_fixtures --set all --verify
for CAP in 300 900 2700 8100; do
  KS_CHAIN_MAX_ITER=$CAP uv run python -m tools.laufform.harvest \
    --sets words,pairs --path chain --jobs 4 --diag-csv temp/diag_$CAP.csv \
    --out temp/drafts_$CAP.json --occ-out temp/occ_$CAP.json --word-out temp/words_$CAP.json
done
uv run python -m tools.laufform.harvest --sets words,pairs --path slot --jobs 4 \
  --diag-csv temp/diag_slot.csv --out temp/drafts_slot.json \
  --occ-out temp/occ_slot.json --word-out temp/words_slot.json
```

Nichts davon berührt die DB oder das Rendering — reine Messung.

### Nachtrag: Stufe B, Runde 2 — der Wächter hat recht, die Kette nicht (2026-08-05)

Der Ausbeuteterm aus dem Nachtrag darüber ist untersucht: zwei unabhängige
Studien über dieselben 46 Ablehnungen, eine blind pro Zeile mit adversarialem
Widerlegungslauf, eine systematisch über Schwellen, Regime und Provenienz.

**Ergebnis: der Konnektor-Wächter ist kein Fehlalarm, sondern meldet einen
Platzierungskollaps der Kette.** Entschieden hat eine externe Referenz, die
vorher niemand benutzt hatte — die **gemessenen** Tinten-Verbinder in
`pair_instances.json` der Fixtures. 232 der 248 Verbindungen haben einen
Zwilling, alle 38 geflaggten eingeschlossen.

| | geflaggt (38) | sauber (194) |
|---|---|---|
| `dconn` Kette↔Tinte, startgleich, 24 Punkte | **0,403** | 0,093 |
| **gemessener** Vorwärtsweg der Tinte | **+0,280 xh** | +0,283 xh |
| Tintenlücke der **Kette** | **0,012 xh** | 0,229 xh |

AUC 0,900 gepoolt (0,924 Wort, 0,890 Paar). Die entscheidende Zeile benutzt
gar kein Formmaß: der Vorwärtsweg der **Tinte** ist auf geflaggten und sauberen
Zeilen statistisch identisch, während die **Kette** die Lücke auf null drückt
(17 von 38 exakt null). Die Vorlage sagt, diese Buchstaben berühren sich nicht;
die Kette hat sie übereinandergeschoben, und der Verbinder musste rückwärts
laufen, um anzukommen.

**Der Mechanismus, zweifach gemessen, zeigt auf dieselbe Stelle:**

* *Pro Verbindung* — die **Exit-Höhe des linken Glyphen**. Die Hoch-Exit-Klassen
  (`b d D S longs t k`) werden auf Worttafeln zu 40 % geflaggt und auf den
  Paar-Übungen zu **16/16**; alles andere zu 8 % bzw. 10 %. Die Paar-Übungen
  überrepräsentieren diese Klasse schlicht (61,5 % gegen 20,5 %) — das ist die
  ganze Wort/Paar-Asymmetrie, kein eigenes Regime.
* *Pro Solve* — die **Lauflänge**. Wort-Flags 2/78 = 2,6 % bei Lauf ≤ 4 gegen
  19/136 = 14,0 % bei Lauf ≥ 5 (Fisher p = 0,0074), und **flach über die ganze
  Iterationsleiter** (9,3/10,3/9,8/9,8 % bei 300→8100, während
  `hit_iteration_cap` von 325 auf 0 fällt) — also kein Solver-Rauschen.

**Was NICHT hilft, mit Preisschild** (alle Zahlen sind Replays über die
gespeicherten Rohsignale, keine Schätzungen):

| Änderung | freie Slots | was dadurch durchrutscht |
|---|---|---|
| `min_forward_ratio` 0,0 → −0,3 | +7 | 6 Verbindungen, 3 über der sauberen p95, schlimmste `dconn` 0,601 |
| `min_forward_ratio` aus | +21 | 16 Verbindungen, 7 über p95 — die §5c-Fehler wörtlich |
| `min_chord_units` 0,25 → 0,5 | +13 | 10 Verbindungen, Median `dconn` **0,401** |
| Wächter ganz aus | +46 | alle 38, davon 21 über p95, schlimmste 0,726 |
| `max_seam_total_units` 1,3 → 1,5 | +4 | 3 beurteilbare, `dconn` 0,062 / 0,069 / 0,249 |

Nur die letzte Zeile ist billig — und sie ist die einzige, bei der sich die
beiden Studien **widersprachen**. Die blinde Adjudikation hat genau diese vier
Zeilen als echte Degenerationen bestätigt; ihre Widerleger verglichen aber
gegen den *generierten* Verbinder und gegen akzeptierte Kontrollen, nicht gegen
die Tinte. Nachgerechnet gegen die gemessene Tinte liegen `streiten|0` (0,062)
und `ssi|0` (0,069) **besser als der Median einer sauberen Verbindung**, `ssi|1`
innerhalb p95, und `ssi|2` hat keinen Zwilling. Auf der stärkeren Referenz
gewinnt die systematische Studie. **Die Schwelle bleibt trotzdem vorerst
stehen:** +4 Slots rechtfertigen es nicht, eine kalibrierte Schwelle gegen einen
adversarialen Lauf zu bewegen, solange derselbe Befund 15–18 Slots an anderer
Stelle ausweist — und solange die Schwäche des Wächters nachweislich auf der
**Recall**-Seite liegt (16 Stub-Verbinder mit `forward_ratio < 0` liefern
heute 25 *akzeptierte* Slots, nur weil ihre Sehne unter `min_chord_units`
bleibt).

**Zwei bekannte Messdefekte, beide null Slots wert** — verifiziert, damit die
nächste Runde sie nicht erneut herleitet: die Doppelzählung des geteilten
Bogens bei Überlappung (`seam_total > arc` auf 30 von 248, bis exakt 2,0×, alle
bei Lücke 0) — gekappt fallen die betroffenen Zeilen sofort in `backward_arc`;
und die Höhenbandlücke, durch die der Rücklauf einer `longs`-Unterlänge als
Überschreiben des linken Buchstabens verbucht wird.

**Die 2-für-1-Regel bleibt, mit umgekehrter Begründung.** Der Code sagt, der
Verbinder habe sich aus dem Schwanz des Buchstabens bezahlt; die Residuen
widerlegen das (die verworfenen Buchstaben sitzen ihrer Tinte nicht schlechter
auf als im Einzelfit). Richtig ist: der Defekt ist die **relative Platzierung
des Paares** — eine Eigenschaft der Verbindung, nicht eines Buchstabens —,
also sind beide per Konstruktion betroffen und kein Pro-Buchstabe-Residuum kann
darüber entscheiden. Strukturell gilt ausnahmslos: „eigener Grund" ist immer
der LINKE Slot, „Nachbarschaft" immer der rechte; es ist dieselbe Entscheidung
von zwei Seiten.

**Und die Ernte-Statistik gibt dem Wächter recht:** bei gleicher Schlüsselzahl
komponiert sein Schnitt **besser** (Bench 0,118368 gegen 0,120651 für
„alles behalten", 14 Schlüssel). Sein Schaden ist **Abdeckung, nicht
Geometrie** — er drückt 7 von 14 Glyphen unter `min_n ≥ 4` (`t` 9→3,
`longs` 8→3, `b` 5→3, …). Das ist ein Fall für `min_n`, nicht für die Schwellen.

**Neue Runde-2-Liste**, nach dieser Messung:

1. **Der Platzierungskollaps der Kette** — 16 der 38 geflaggten Verbindungen
   haben eine gefittete Lücke von exakt 0, während die komponierte
   Initialisierung bei +0,19 … +0,94 vorwärts stand. Zwei konkrete Ansätze:
   Neu-Initialisierung aus der unabhängigen M4-Platzierung, wo die komponierte
   Lücke > 0 ist und die gefittete kollabiert; und `regularise_connector_anchors`
   von der Cusp- auf die Hoch-Exit-Klasse ausweiten. Erwartung 15–18 Slots
   **ohne Recall-Kosten**, weil es den Defekt behebt statt den Alarm abzustellen.
2. **Lauflänge** — ob eine Zerlegung langer Wortketten denselben Effekt hat.
3. Erst danach Schwellen, und dann als Recall- statt Precision-Frage.
4. Die offene Messung: die Kette müsste ihre Anker auch für *abgelehnte* Slots
   ausgeben (reine Diagnose, kein Gate-Wechsel), damit „linken Buchstaben
   behalten, rechten verwerfen" überhaupt bezifferbar wird — heute liegen nur
   die akzeptierten Fits auf Platte.

### Nachtrag: Grid-Seed-A/B — der Kollaps ist eine Eigenschaft des Objektivs (2026-08-05)

Ansatz 1a aus der Liste ist gebaut und gemessen: `fit_word_chain` kann seine
Translationsblöcke jetzt an der **Grid-Platzierung des Buchstabens auf seiner
eigenen Tinte** starten statt bei null (= komponierte Platzierung) —
`--chain-seed grid`, Objektiv unangetastet, nur das betretene Becken ändert
sich. A/B über die eingefrorenen `words,pairs`-Fixtures, identischer Code,
Budget 8100, vorab festgelegte Kriterien.

**Ergebnis: der Seed heilt Verbinder, aber keine Ausbeute — und die
Nachprüfung zeigt warum.**

| | composed | grid |
|---|---|---|
| akzeptiert | 241 | **241 (±0)** |
| geflaggte Verbindungen | 38 | 34 (8 befreit, 4 neu) |
| `not_converged_local` | 35 | **28 (−7)** |
| `geo_rmse` / `at_bound` / `connector_degenerate` | 21 / 1 / 46 | 24 / 3 / 48 |
| `geo_rmse` Median (akzeptiert) | 1,027 px | 1,030 px |
| Lauflängen-Gradient (Wort, ≥ 5) | 14,0 % | **11,0 %** |

Die 8 befreiten Verbindungen sind **echt geheilt**, nicht nur entflaggt —
`Seiten|4` Lücke 0 → 0,065 und Vorwärtslauf −0,441 → +0,098, `Silber|4`
0 → 0,060 und −0,919 → +0,323, `Säbel|2` 0 → 0,425 und −0,466 → +0,403. Und
7 Buchstaben mehr konvergieren. Aber die Tor-Kaskade verschiebt nur: die
gewonnenen Zeilen fallen in `geo_rmse`/`at_bound`/`connector_degenerate`, 4
neue Verbindungen entgleisen (`Galoppieren|8` seamR 0 → 2,761), Netto-Ausbeute
exakt null, pro Schlüssel ein Nullsummen-Tausch (+5/−5).

**Die entscheidende Nachmessung:** Buchstaben neben noch geflaggten
Verbindungen wandern **1,8× weiter über ihren Seed hinaus** als saubere
(Median 0,048 gegen 0,027 xh, p90 0,331 gegen 0,184), und **alle 11** noch
kollabierten Verbindungen hatten einen gesunden Grid-Seed — die Solves sind
vom richtigen Start **aktiv in den Kollaps gelaufen**. Der Kollaps ist damit
keine Initialisierungs-Panne, sondern **das Objektiv bevorzugt das gestapelte
Becken**: wo zwei Buchstaben dieselbe Tinte belegen, bekommen beide
Deckungs-Gutschrift — Tinte ist doppelt beanspruchbar, und Stapeln ist billig.

**Konsequenz:** `--chain-seed` bleibt als Messinstrument im Werkzeug (Default
`composed`, per Vorregistrierung: kein Kriterium für einen Default-Wechsel
erfüllt). Der nächste Hebel ist **objektivseitig** — entweder
Deckungs-Exklusivität (ein Skelettpixel zahlt nur einmal, an das nächste
Segment) oder die Zerlegung langer Ketten (Punkt 2, deren Gradient auch der
Seed nur von 14,0 auf 11,0 % drückt). Beides ändert, was die Kette *misst*,
und braucht darum vorab dieselbe Sorte A/B mit Tinten-Gegenprobe wie hier.

Reproduktion: `--chain-seed {composed,grid}` auf demselben Kommando wie oben;
Seeds und Rest-Reiseweg stehen je Slot im `--diag-csv`
(`seed_x/y_units` gegen `shift_x/y_units`).

### Nachtrag: der Überlappungsterm — die Exklusivität, die dem Objektiv fehlte (2026-08-05)

Der objektivseitige Weg (Eigentümer-Entscheid: „das perfekte Ergebnis, nicht
das schnelle") ist gegangen, in vier Schritten, jeder vorregistriert.

**1. Beckensonde — die Behauptung bewiesen, bevor gebaut wurde.** Fünf
bekannte Kollaps-Fälle (`do` `bp` `sg` · `Seiten` `unter`), je zweimal gelöst:
frei gegen „Platzierung an der eigenen Tinte festgeheftet" (Blöcke per Bounds
am Grid-Seed, Anker und Verbinder frei). **5/5: die kollabierte Lösung ist
billiger — und zwar in *jedem* Term, Deckung eingeschlossen** (Paare bis
5,3×, Wörter ~1,3×). Damit war die Diagnose eine Ebene tiefer gelegt: nicht
„Tinte absorbiert beliebig viel Modell", sondern **Zuordnungsblindheit** —
das Objektiv prüft die Vereinigung der Segmente gegen die Vereinigung der
Tinte; ein Buchstabe, der Verbinder-Tinte schluckt, und ein Verbinder, der
den Buchstabenstrich nachfährt, lesen sich beide als gute Deckung. Und der
Kollaps wandelt regulierte Anker-Verformung in unregulierte, kostenlose
Block-Translation um (`e_reg` ist einer der beiden Hauptfinanziers).

**2. Der Term.** `e_overlap`: quadratischer Hinge auf Sample-Paare
**verschiedener** Segmente innerhalb `CHAIN_OVERLAP_RADIUS_UNITS` (0,15 xh —
innerhalb eines gezeichneten Haarstrichs, Masken-Durchmesser ~0,16). Zwei
Freistellungen, beide begründet: die Nahtbänder benachbarter Segmente (die
gemessene 0,2–0,4-xh-Stub-Zone; aus der **Init**-Geometrie, damit der
analytische Gradient exakt bleibt) — und Buchstabe-auf-Buchstabe **nie**,
denn Stapeln ist der Fehler, den der Term bepreist. Paarmenge pro Evaluation
per KD-Baum, stückweise konstant — dieselbe f.ü.-exakte Behandlung wie die
Deckungszuordnung. Der tragende FD-Gradiententest läuft auf einer
überlappenden Konfiguration mit zahlendem Term.

**3. Kalibrier-Sweep** (5 Kollaps- + 2 Kontrollfälle × w ∈ {0; 0,05; 0,2; 1;
5}) — mit einer Selbstkorrektur: die x-Ausdehnungs-Lücke war als
Kollaps-Messer **falsch**, denn verschachtelte, aber zentrallinien-getrennte
Buchstaben (diese Hand schiebt das `k` legitim unter den `d`-Deckstrich,
Runde-1-Befund `dk`) sind kein Doppelschreiben. Ab w = 1 zeigt sich das
Über-stark-Regime: Buchstaben werden von legitim geteilter Tinte
weggedrückt (`unter` Slot 4: rmse 0,96 → 1,97 px).

**4. Das A/B** (volle `words,pairs`-Fixtures, w ∈ {0; 0,2; 1,0}):

| w | akzeptiert | Flags (38 Basis) | geheilt / neu | rmse p50 |
|---|---|---|---|---|
| 0 | 241 | 38 | — | 1,027 px |
| **0,2** | **245** | **34** | **4 / 0** | 1,030 px |
| 1,0 | 242 | 34 | 6 / 2 | 1,034 px |

**Bei w = 0,2 heilen exakt die vier Verbindungen, die die
Tinten-Adjudikation als die Grenzfälle des Wächters benannt hatte**
(`streiten|0`, `ssi|0`, `ssi|1`, `regieren|3`) — und zwar mechanisch, nicht
statistisch: der Naht-Anteil verschwindet aus der Lösung selbst
(`streiten|0` seam_left 1,178 → 0,136 xh; `ssi|0` 1,360 → 0,258). **Keine
Schwelle wurde bewegt; die Geometrie wurde repariert, und der Wächter stimmt
von selbst zu.** Ausbeute +4 (`longs` 3 → 6 — einer der wächter-ausgehungerten
Schlüssel), null neue Flags, `at_bound` 1 → 0, rmse p50 +0,003 px. Default:
`CHAIN_OVERLAP_WEIGHT = 0,2`.

**Offen, mit Namen:** die verschachtelten Paar-Übungs-Stapel (`do`, `bp`,
`dp` …) heilen NICHT — ihre Zentrallinien liegen weiter auseinander als der
Radius, und nach dem Radius-Rational ist das benachbartes Schreiben, kein
Doppelschreiben. Ob ihr Ausdehnungs-Überlapp legitimes Unterschieben (wie
`dk`) oder echter Kollaps ist, entscheidet keine Radius-Vergrößerung, sondern
bessere Bodenwahrheit — eine autorisierte Nachfahrung dieser Übungen oder die
Ausgabe der Ketten-Anker für abgelehnte Slots (Punkt 4 der Liste oben).

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
