# Optimierungs-Werkbank 2026-07-31 — eine Admin-Fläche, Stufen-Doktrin, Auftragskorb

> **Status (2026-09-07): bindend.** W1–W6 sind umgesetzt
> (PR #252 · #255 · #261 · #264 · #266); §3–§5 **und §6** sind bindende
> Doktrin, §3–§5 werden seit W4 von der API erzwungen
> (`check_transition`) — deshalb „bindend" und nicht
> „umgesetzt-historisch": dieses Doc bleibt Pflichtlektüre vor jeder
> Korb-Arbeit (`/work-basket`). Jüngste Zusätze: die **Landmarken-Linse**
> in §8 (Autor-Wunsch 2026-09-07) — die generierte Struktur-Ebene wird auf
> der geschriebenen Form sichtbar und bekommt mit `kind = "landmark"` eine
> fünfte Korb-Ebene und mit `landmark_detector` eine achte Stufe im
> §5-Vokabular —, davor die Sperr-Doktrin in §6 (Autor-Entscheid
> 2026-09-03): die Sperre ist eine Warnung mit Rückfrage, kein Riegel.
> Das in §2/§6 angekündigte Aufgehen von `/admin/vergleich`, `/admin/paare`
> und `/admin/belege` in der Werkbank ist mit dem Admin-Redesign
> („aus einem Guss", 2026-08) vollzogen: der ganze Admin IST jetzt die
> Werkbank — eine Vorlagen-Auswahl unter `/admin` und darunter die drei
> Ansichten **Buchstaben · Übergänge · Wörter**, jede nach dem Muster
> Übersicht ⇄ Detail, mit dem Auftragskorb im Header über allen dreien.
> Die alten Pfade bleiben als Redirects. Zwei Ergänzungen gegenüber dem
> Zielbild unten: das Rückgrat/Linsen-Nebeneinander wurde zu drei
> gleichberechtigten Ansichten mit Quer-Absprüngen (das Subjekt steht in der
> URL, statt in einer Linse rechts), und jede Ebene nimmt **frei
> eingetippte** Ziele an — eine Kombination oder ein Wort, das keine Platte
> je geschrieben hat, muss trotzdem richtig aussehen und bemängelbar sein.
> Die Routen-Karte steht in
> [`frontend-stack.md`](../reference/frontend-stack.md) §2.

**Richtungsentscheid des Nutzers (2026-07-31, zwei Fragen):
(1) EINE neue Werkbank-Seite `/admin/werkbank`** — Wort-Rückgrat +
umschaltende Kontext-Linse + Auftragskorb; die bestehenden Seiten
(`/admin/vergleich`-Tabs, `/admin/paare`, `/admin/belege`) bleiben, bis
die Werkbank sie schrittweise ersetzt. **(2) Der Auftragskorb lebt als
DB-Tabelle `work_items`** mit Admin-API — die KI liest offene Aufträge
am Rundenstart und meldet je Auftrag erledigt. Umsetzung: W1–W5
umgesetzt (§7). §3–§5 sind die **bindende Stufen-/Rollen-Doktrin** für
Mensch UND KI — Pflichtlektüre, bevor ein `work_items`-Auftrag
bearbeitet wird; seit W4 erzwingt die API den §5-Ablauf, statt ihn zu
erhoffen.

## 1. Anlass

Nutzer-Befund: Die Admin-Ansicht ist über Tabs und Seiten fragmentiert
(Vergleich · Paar-Matrix · Belege), obwohl die Fragen beim Optimieren
immer quer laufen — „wie sieht dieser Buchstabe in Wörtern aus?", „der
Übergang im Wort passt nicht, zeig die Paare". Und Feedback an die KI
lief über Screenshots („nicht immer Screenshot in Paint"). Seit der
Vorkommens-Persistenz (Migration `0019`, PR #250) sind alle drei Ebenen
in der DB verknüpft (`instances` · `pair_instances` · `word_instances`,
gemeinsame `specimen_id`/Slots) — die Quer-Navigation ist reine
UI-Arbeit, keine Datenfrage mehr.

## 2. Zielbild (Mockup-Runde 1, gebilligt)

- **Wort-Rückgrat** (links): die Belege-Karten — jedes Wort-Vorkommen
  über seinem Platten-Crop, nachgefahrener Pfad als Overlay,
  schlechteste zuerst. Wörter sind der Ort, wo Fehler *sichtbar* werden.
- **Kontext-Linse** (rechts, schaltet auf Klick): Buchstaben-Box im
  Wort → Buchstaben-Linse (Tafel-Form · Laufform · alle
  `instances`-Vorkommen als Schnipsel mit RMSE, Absprünge in Wizard und
  Diagnose); Übergangs-Punkt → Paar-Linse (alle
  `pair_instances`-Vorkommen · Generator-Stand · Paar-Editor-Einstieg).
  Rückweg: Vorkommen anklicken → springt ins Wort.
- **Auftragskorb** (⚑, schwebend): jedes Element (Buchstabe · Übergang
  · Wort) ist markierbar; ein Eintrag speichert strukturiert Ebene,
  Ziel-Schlüssel, Specimen-Bezug und Notiz (§5).

## 3. Die Stufen des Schreibwegs — wer liefert was

Grundregel: **Manuell hinzufügen nur, wo Ground Truth entsteht, die das
System nicht selbst herleiten kann. Alles Generierte wird bemängelt** —
ein Mangel schärft die Regel für alle Wörter, ein manueller Eingriff
repariert genau eine Stelle.

| Stufe | Artefakt | Wer liefert | Änderungsweg |
|---|---|---|---|
| Tafel-Duktus | `templates` (Wizard-Trace) | **Mensch** — Strichfolge/Kreuzungen sind Autoren-Wissen | selbst im Wizard nachbessern |
| Laufform | `templates` Variante 100 (Median der Fits) | automatisch | nur bemängeln |
| Übergangs-Grammatik | Klassenregeln in `core/compose.py` | Algorithmus | nur bemängeln |
| Paar-Override | `glyph_pairs` (Paar-Editor) | Mensch, **sparsame Ausnahme** | zeichnen nur als letztes Mittel |
| Komposition | Platzierung/Abstände/Rhythmus | Algorithmus | nur bemängeln |
| Wort-Trace | `word_instances` (`traced`) | automatisch — außer wo der Fit scheitert | **Mensch** fährt rote Fälle nach (`authored`) |

## 4. Entscheidungshilfe nach Symptom

- **Buchstabe sieht schon solo falsch aus** → Tafel-Ebene: selbst im
  Wizard nachbessern (der eigene Duktus ist die Wahrheit).
- **Buchstabe stimmt solo, aber in Wörtern nicht** (zu schmal, geneigt,
  verformt) → Buchstabe **bemängeln** — Laufform/Fit/Verformungsmodell
  ist Algorithmus-Territorium.
- **Ein Übergangstyp wiederholt falsch** → Übergang **bemängeln**, gern
  mit zwei, drei Beispielwörtern — daraus wird eine Klassenregel, die
  viele Paare auf einmal hebt.
- **Ein einzelnes Paar bleibt trotz Regel eigen** (die Platte zeigt
  eine idiosynkratische Form) → erst dann Paar-Editor: Override
  zeichnen, freigeben. Bewusst die Ausnahme — jeder Override friert
  eine Stelle ein, jede Regel verbessert alle.
- **Wortbild insgesamt** (Rhythmus, Grundlinie, Abstände) → Wort
  **bemängeln**.
- **Rote Chips im Wort** (Auto-Fit gescheitert) → Wort **manuell
  nachfahren** (Wort-Editor): der `authored`-Trace ist Ground Truth für
  Statistik und Training, kein Rendering-Patch.

**Entlastungsregel:** Der Mensch muss die Stufe NICHT diagnostizieren.
Die Korb-Ebene heißt „wo gesehen", nicht „wo verursacht" — markiert
wird, wo es weh tut; die Stufen-Triage ist Teil des KI-Auftrags (§5).
Der ⚑-Dialog stellt genau eine Vorsortier-Frage („Sieht der Buchstabe
einzeln auch falsch aus?") und schlägt danach Korb-Auftrag oder
Wizard-/Editor-Absprung vor.

## 5. Auftragskorb-Protokoll (`work_items`)

**Mensch-Seite:** Ein Eintrag = Ebene (`letter`/`pair`/`word`) +
Ziel-Schlüssel + Specimen-Bezug (wo gesehen) + freie Notiz. Status
`open`. Mehr ist nicht gefordert.

**Fünfte Ebene `landmark`:** eine Beschwerde über EINE erkannte Struktur
eines Buchstabens. Sie trägt den `glyph_key` wie ein Buchstaben-Eintrag,
und welche Landmarke gemeint ist, schreibt die Linse in die ersten zwei
Zeilen der Notiz — Einzelheiten und Begründung in §8.4.

**Vierte Ebene `note`:** ein Eintrag ganz ohne Ziel — eine allgemeine
Kleinigkeit (eine Admin-UI-Falte, ein schiefes Wort in der Oberfläche,
ein „später ansehen"), die zu keiner Glyphe gehört und für die sich ein
GitHub-Issue nicht lohnt. Ihr ganzer Inhalt ist der Notiztext, den die
API deshalb als einziges Feld verlangt; angelegt wird sie direkt im
Korb („Notiz anlegen"), weil ⚑ immer etwas Bestimmtes markiert. Grund:
Der Korb ist die Schublade, die unterwegs eh offen ist — was hier nicht
hineinpasst, geht verloren.

**KI-Seite:** Der Rest ist Protokoll — und zwar erzwungenes. Die API
weist ein unvollständiges Abschließen mit 422 ab (`check_transition` in
`api/routers/work_items.py`); die Regeln unten sind also keine Bitte,
sondern die Bedingung, unter der die Zeile überhaupt geschrieben wird.
Grund: Eine geschlossene Zeile ist der einzige dauerhafte Ertrag der
Runde. Wer nur „erledigt" hinterlässt, hat die Arbeit gemacht und das
Wissen weggeworfen.

### 5.1 Zustände

| Status | Wer setzt ihn | Pflichtfelder |
|---|---|---|
| `open` | Mensch (Ablegen) · Mensch (Zurückweisen) | — |
| `ack` | KI, **bevor** sie etwas ändert | `understanding` + `reproduced` |
| `done` | KI, nach getaner Arbeit | `understanding` (liegt vor) + `stage` + `resolution` |
| `returned` | KI, wenn Ground Truth fehlt | wie `done` |

`stage` kommt aus dem festen Vokabular der §3-Tabelle, in der
Triage-Reihenfolge: `chart_ductus` · `laufform` · `join_rule` ·
`composition` · `pair_override` · `word_trace` — dann
`landmark_detector` (§8.4: der Buchstabe stimmte, der Erkenner nicht; die
einzige Stufe, die keinen Schritt des Schreibwegs benennt) — plus
`not_reproducible`, das ehrliche Ergebnis, wenn die Beschwerde nicht
auftrat. Ein geschlossenes Vokabular macht aus dem Archiv eine Abfrage
(„welche Stufe verursacht die meisten Aufträge?") statt einer Lesearbeit.
Für einen `note`-Eintrag entfällt `stage` als Pflichtfeld — jede Stufe
des Vokabulars benennt eine Stufe des SCHREIBWEGS und hätte über eine
UI-Kleinigkeit nichts Wahres zu sagen; erlaubt bleibt sie, wo sie
zutrifft. Die Rückspiegelung (`ack`) gilt unverändert.

Drei Regeln machen den Ablauf unumgehbar: Protokollfelder reisen **nur
mit ihrem Statuswechsel** (ein PATCH ohne `status` darf die Notiz
ändern und sonst nichts); `done`/`returned` verlangen ein bereits
**gespeichertes** `understanding` — Zurückspiegeln und Abschließen in
einem Aufruf lehnt die API ab; und jedes verlangte Feld muss **in
diesem PATCH stehen**, nie im schon gespeicherten Zustand. Die dritte
Regel ist die, die die zweite Runde trägt: Beim Zurückweisen setzt der
Korb die Zeile auf `open` zurück und lässt `understanding`, `stage` und
`resolution` bewusst stehen — ein Rückgriff auf den Bestand ließe ein
nacktes `{"status":"done"}` genau die Rückspiegelung wieder in Kraft
setzen, die der Autor gerade zurückgewiesen hat. Alle drei schützen
dasselbe: Die Rückspiegelung ist nur etwas wert, solange sie dasteht,
während sie noch korrigiert werden kann — und nach einer Korrektur
erst recht.

### 5.2 Ablauf, bindend bei jedem Auftrag

1. **Aufträge lesen** — `GET /work-items?status=open`, quer über alle
   Quellen, ohne Vorwissen über `source_id`. Jede Zeile trägt ihre
   Quelle mit. (Die quellenbezogene Route bleibt für die SPA.)
2. **Nachprüfen, nicht nacherzählen.** Den Beleg ansehen (Werkbank-Karte,
   `GET …/word-samples/{id}/score`, `tools/wordlab`, `tools/pairlab`) und
   festhalten, ob die Beschwerde auftritt: `reproduced` = `yes`/`partly`/`no`.
3. **Zurückspiegeln** — `PATCH /work-items/{id}` mit `status: "ack"`,
   `understanding` in eigenen Worten und `reproduced`. Danach sofort
   weiterarbeiten; das ist keine Freigabeschleife. Hält der Mensch das
   Verständnis für falsch, weist er es im Korb zurück — die Zeile steht
   wieder auf `open`, mit seiner Korrektur in der Notiz.
4. **Triage-Pflicht** entlang §3, in dieser Reihenfolge prüfen:
   Tafel-Duktus falsch? → Laufform/Fit? → Klassenregel? → Platzierung?
   → erst zuletzt: Paar idiosynkratisch (Override)?
5. **Regel-Fix vor Override.** Ein Override ohne vorherige
   Regel-Prüfung ist ein Doktrin-Verstoß.
6. Wirkung messen (Wordbench-Guard; Metrik/Fixtures bleiben
   eingefroren) und visuell belegen (Vorher/Nachher).
7. **Abschließen** — `status: "done"` mit `stage` und `resolution`.
8. Ergibt die Triage eine **Ground-Truth-Lücke** (Tafel-Duktus falsch,
   Fit ohne manuellen Trace unmöglich): `status: "returned"` statt
   `done`, `resolution` nennt den konkret benötigten manuellen Schritt
   (Wizard-Glyphe X, Wort Y nachfahren). Die Zeile bleibt sichtbar im
   Korb — sie wartet auf den Autor, nicht auf den Algorithmus.

### 5.3 Wie ein guter Eintrag aussieht

`understanding` — drei Sätze, kein Absatz: was ich als Beschwerde
verstehe · was ich beim Nachprüfen gesehen habe · welche Stufe ich
zuerst verdächtige. Ohne einleitendes „Verstanden als:" — der Korb
beschriftet das Feld bereits, die Wiederholung stünde doppelt da.

> Das `n` in „wenn" wirkt zu flach, nicht der Übergang davor.
> Nachgeprüft an `wenn-19-2`: Score 0.19, die Segment-Attribution legt
> 0.11 auf den zweiten n-Bogen, der Übergang d→n liegt im Schnitt.
> Verdacht zuerst auf der Laufform, nicht auf der Tafel-Form — solo
> stimmt das n.

`resolution` — Stufe, Änderung, PR, Messstand:

> Laufform: Median über 41 Vorkommen neu abgeleitet und angewandt
> (`apply-laufform`), Bogenhöhe +0,08 xh. PR #265. Wörter-Bench
> 0.1240 → 0.1214, `wenn-19-2` 0.19 → 0.14. Vorher/Nachher als
> wordlab-Overlay im PR.

**Quer-Verweis-Regel:** `resolution` nennt die PR, die PR-Beschreibung
nennt `Korb #<id>`. Damit ist das Archiv von beiden Seiten auffindbar —
vom Symptom zur Änderung und zurück.

## 6. Leitplanken

- **Die Sperre ist eine Warnung, kein Riegel** (Autor, 2026-09-03). Eine
  gesperrte Glyphe bleibt im Wizard **vollständig angeboten** und trägt
  das Schloss sichtbar — im Titel als Chip, auf dem Weg-Schritt als
  Hinweis, und der Speichern-Knopf sagt es in seiner Beschriftung. Wer
  überschreiben will, beantwortet **eine** Rückfrage („Trotzdem
  überschreiben"); erst diese Antwort schickt `force=true` an die
  bestehende Route. Grund: Die Sperre soll vor dem *versehentlichen*
  Überschreiben eines fertigen Wegs schützen, nicht vor dem gewollten —
  der alte Weg (erst in der Tafel entsperren, zurück in den Wizard,
  zeichnen, danach wieder sperren) kostete vier Schritte für eine
  Entscheidung, die in einem Satz steht, und die Tafel-Entsperrung ließ
  die Glyphe obendrein offen zurück. Der Boden bleibt der Server: ohne
  `force` antwortet er weiter mit 423 (`api/routers/templates.py`
  `_reject_locked_unless_forced`), gepinnt in
  `tests/test_api_admin_writes.py`. Die Regel dahinter gilt für die
  ganze Werkbank: **`force` setzt nur eine Fläche, die vorher
  ausdrücklich danach fragt.** Das sind genau drei — die Rückfrage im
  Wizard (neu), das „Neu ableiten & speichern" der Diagnose und der
  Bulk-Dialog „Alle neu ableiten"; die beiden letzten sind schon immer
  bewusst aufgerufene Aktionen und sagen es in ihrem Hinweistext. Ein
  Knopf, der nebenbei schreibt, bekommt das Flag nicht.
- Manuelle Beiträge (`authored`-Traces, Overrides) gehen **nie** in die
  eingefrorenen Metrik-Referenzen ein — die Messlatte bleibt die Platte
  (qualitaetsmetrik.md).
- Statistik bleibt je Hand (quellen-und-rechte.md §7); die Werkbank
  zeigt immer genau eine Quelle/Hand.
- Die Werkbank ersetzt die Alt-Seiten erst, wenn ihre Funktion dort
  vollständig angekommen ist — bis dahin koexistieren sie.
- **Eine Laufform-Zeile wird nur über das Zeilen-Gate aufgenommen**
  (messjournal.md §14 LF7/LF8, Glossar „Zeilen-Gate (Laufform)"):
  Boden n ≥ 3 — oder die ausdrückliche Autor-Aussage
  `?min_occurrences=N` in der Anfrage — UND Sprung-Ratio unter
  `LAUFFORM_SPIKE_RATIO_MAX`, auf beiden Schreibpfaden, ohne Override.
  **Ein Wort-Gewinn am Pixel-Lineal ist KEIN Aufnahmekriterium für eine
  Zeile** (Autor, 2026-08-29): so kam das n=1-K in den Schreibweg — der
  Buchstabe war sichtbar schlechter als seine Tafelform, das Wort-Lineal
  sah nur die Deckung. Was das Gate nicht sieht (Form-Drift ohne
  Sprung), entscheidet der Autor am Bild der Bestandsaufnahme
  (`tools/laufform/inventory.py --png`).

## 7. Umsetzung

- **W1 — Backend** (umgesetzt): Migration `0020` `work_items` (Ebene,
  Schlüssel, Specimen, Notiz, Status `open`/`done`, `resolution`) +
  admin-gegatete Endpunkte + Tests.
- **W2 — Seite `/admin/werkbank`** (umgesetzt): Rückgrat (aus PR #251) +
  Linsen + Korb-UI inkl. Vorsortier-Frage. Offen bleibt allein das danach
  angekündigte schrittweise Aufgehen von Vergleich/Paaren/Belegen — die drei
  Seiten sind unverändert geroutet.
- **W3 — Wort-Editor** (umgesetzt): Crop als Unterlage, S-Pen-Nachfahren
  → `authored`-`word_instances` (Endpunkt + Überschreib-Schutz waren
  bereits live). Der Editor (`WordTraceEditorDialog`) öffnet aus jeder
  Belege-Karte: Registrierungs-Rahmen des Vorkommens (Grundlinie +
  Mittellinie) über dem Ausschnitt, die gespeicherte Spur als
  Ausgangspunkt, jedes Absetzen beginnt einen neuen Zug (wie im
  Wizard-Schritt „Weg"), Zug-weises Zurücknehmen und Zurücksetzen.
  Gespeichert wird mit **einem** Item ohne `replace` — genau dieses
  Vorkommen wird ersetzt, alle anderen Zeilen (und jede andere
  `authored`-Spur) bleiben unberührt; Slot-Labels und Registrierung
  wandern mit, die Fit-Kennzahlen des ersetzten Pfads nicht.
  Seit aug16 zusätzlich: ein **Anpassen-Modus** (dritter Schalter neben
  Schreiben/Verschieben, der Mechanismus des Wizard-„Anpassen"): die
  Bahn an einer Stelle mit dem Stift ziehen, Punkte im einstellbaren
  Radius (xh-Einheiten) folgen mit Smoothstep-Falloff — ein
  Tablet-Wackler lässt sich glätten, ohne das Wort neu zu fahren. Züge
  werden dabei nie geteilt, zusammengelegt, umgeordnet oder umgekehrt
  (der Trace-Bench misst Absetz-Struktur und Schreibrichtung), Punkte
  nur verschoben, nie erzeugt oder verworfen. Bei den zehn eingefrorenen
  Entwicklungssatz-Wörtern (`tools/tracebench/sets.py`) warnt der Editor
  vor dem Speichern einmal explizit — ein Save dort verändert das
  Lineal (datierter §14-Re-Baseline + Fixture-Abgleich fällig). Einen
  veralteten Registrierungs-Rahmen (Frame-Gate des Fixture-Exports)
  heilt der Editor beim Öffnen: die Bahn wird durch den alten Rahmen in
  den aktuellen der Wortprobe umgerechnet (gleiche Lage im Ausschnitt),
  Speichern schreibt den frischen Rahmen fest. Und die
  **Nachfahr-Übersicht** (dritter Tab der Wörter-Übersicht,
  `AuthoredTraceReview`): alle `authored`-Bahnen der Quelle
  untereinander über ihrem Crop — wahlweise „Nur die Bahn" auf Weiß —
  als Qualitäts-Sichtung der eigenen Stiftarbeit, mit
  Entwicklungssatz-Kennzeichnung, „Rahmen veraltet"-Badge (die
  Frame-Gate-Toleranzen des Fixture-Exports, client-seitig gerechnet)
  und direktem Absprung in den Editor.
- **W4 — Protokoll** (umgesetzt): §5 als erzwungener Ablauf statt
  Doku-Appell. Migration `0022` ergänzt `understanding` · `reproduced` ·
  `stage` · `acked_at` · `closed_at`; die API weist ein Abschließen ohne
  Verständnis, Stufe oder Ergebnis mit 422 ab; der Korb zeigt die
  Rückspiegelung mit einem „missverstanden"-Knopf, der die Zeile mit der
  Korrektur zurück auf `open` legt. Dazu der quellenfreie Lesepfad
  `GET /work-items` (eine Sitzung soll ihre Aufgaben lesen können, ohne
  vorher eine `source_id` zu erraten) und das Skill
  `.claude/skills/work-basket/`, das den Ablauf führt.
- **W5 — Stufen-Einsicht** (umgesetzt): die Linsen zeigen jetzt auch die
  Statistik-Schichten des Handmodells (handmodell-stufenplan.md H1/H2),
  damit zwischen Tafel-Form und geschriebenem Wort keine Stufe mehr
  unsichtbar bleibt. **Buchstaben-Linse:** unter der Tafel-Form der
  Aggregat-Median der Hand als Ankerkette mit MAD-Kreisen über Grund-
  und Mittellinie („Aggregat-Median (Laufform-Quelle)") plus die
  gepoolte Schicht-1-Statistik (n, Vorlagen, RMSE ⌀/max, x-Höhe,
  Positions-Histogramm). **Paar-Linse:** „Gemessen vs. komponiert" —
  jede geladene Vorkommens-Verbindung dünn, der Median-Connector
  kräftig darüber, der Median-Versatz als Punkt mit MAD-Whisker (alles
  im selben Rahmen relativ zum Abgang des linken Glyphs, also ohne
  Registrierung), daneben die Dissektions-QC mit `gen_chamfer` als
  Audit-Zahl, Ernte-Abstand, Fit-Rest, Ink-Lücken-Anteil und
  Herkunfts-Histogramm. Die Hand wird aus den geladenen Vorkommen
  abgeleitet (häufigste `hand_id`, §6 „genau eine Quelle/Hand"), nie
  fest verdrahtet — und in jedem Block **benannt**, samt ruhiger
  Warnzeile, sobald die geladenen Vorkommen mehr als eine Hand nennen
  (die Abb.-22-Schülerhand kommt irgendwann unter eigener id dazu;
  stilles Mischen wäre eine Lüge über die Zahlen). Fehlt die Hand oder
  scheitert der admin-gegatete Read, bleibt die Seite vollständig
  bedienbar und die Blöcke zeigen eine ruhige Zeile. Beide Schichten
  laden getrennt: ein Neuaufbau holt nur seine eigene Liste nach, die
  bisherigen Zeilen bleiben derweil stehen (die andere Linse und die
  Ergebnis-Zeile des Neuaufbaus bleiben unberührt). Gezeichnet wird nur,
  was der Neuaufbau auch verdichtet hat — als `fit_bad` übersprungene
  Vorkommen fehlen in der Paar-Skizze und in ihren Grenzen (Zahl steht
  in der Bildunterschrift), in der Liste darunter bleiben sie stehen;
  eine fehlende MAD wird nicht als „± 0,00" ausgegeben. Je Schicht gibt
  es einen leisen Neuaufbau-Knopf
  (`POST …/aggregates/rebuild`, `POST …/pair-aggregates/rebuild`) — das
  ist Wartung an der Statistik, kein Arbeitsschritt. **`apply-laufform`
  fehlt hier bewusst:** es ändert Rendering und ist damit genau der
  Griff, den §3 auf dieser Fläche verbietet — angeschaut und
  reklamiert wird hier, gerechnet und übernommen woanders.
- **W6 — Nachfahr-Stand** (umgesetzt): die Wörter-Übersicht beantwortet
  „was fehlt noch?" als Auswahl statt als Scrollarbeit. Neben dem
  Suchfeld steht ein Status-Filter **Alle · Offen · Nachgefahren ·
  Unvollständig** über den Wortproben des Tabs; „Offen" ist damit die
  Arbeitsliste des Nachfahr-Durchgangs. Der Stand einer Probe ist genau
  dreiwertig (`traceStatusOf`, `shell/model.ts`): eine gespeicherte
  `authored`-Bahn heißt fertig (ein automatischer Fit **nicht** — er ist
  das, was der Durchgang ersetzt), ein im Sidecar als `incomplete`
  markierter Beleg heißt „geht nie", alles andere ist offen. Der
  Markierungs-Grund: manche Proben lassen sich gar nicht nachfahren,
  weil die eigene Tinte angeschnitten ist — der i-Punkt fehlt, der
  letzte Buchstabe läuft aus dem Rechteck. Ohne Kennzeichnung sitzen sie
  für immer als unerreichbares „offen" in der Liste und im Zähler; mit
  ihr fallen sie aus beiden heraus (`{{done}}/{{total}} von Hand
  nachgefahren · n unvollständig`), bleiben aber Beleg: der heile Teil
  ist weiter messbar, und Karte wie Wort-Detail tragen den Chip
  „unvollständig" mit dem Sidecar-`note` als Begründung.
  Die Markierung ist **Daten, nicht Klick** — `"incomplete": true` plus
  `note` an der Zeile in `data/sources/<id>/words.json`, committet wie
  jede andere Beleg-Metadatenzeile (`exclude`, Lineatur), und der
  öffentliche Read `/word-samples` reicht beide Felder durch. Die
  Rechteck-Ecken sind eingefrorene Bench-Fixtures: eine angeschnittene
  Probe wird darum markiert, nicht stillschweigend größer geschnitten —
  ein anderes Rechteck wäre ein Re-Baseline des Wort-Benchs
  (`messjournal.md` §14) und braucht dessen Verfahren.

## 8. Landmarken-Linse — die generierte Struktur wird sichtbar

**Autor-Wunsch, 2026-09-07:** „Im Admin-Bereich sollte bei den Tafeln
jeweils pro Buchstabe angezeigt werden, was für Landmarks es gibt, mit
sichtbaren Markierungen, wo genau Kreuzung, Kringel … erkannt wurde, damit
ich das sehe und per Korb bemängeln kann, wenn mir was auffällt."

Die Lücke, die er benennt, ist eine Doktrin-Lücke. Ein Buchstabe hat eine
feste **Struktur** — eine Schleife hier, eine Kreuzung dort, ein Stück, das
die Feder zweimal schreibt —, und die ist eine Duktus-Tatsache und keine
freie Variable irgendeines Fits (§3). Gemessen wurde sie längst: die
Tintenfolger-Zähler erkennen sie auf beiden Seiten eines Duells, der
Kringel-Katalog schreibt je Schleife fest, ob die Platte sie offen hält,
der Duktus-Soll stellt die Erwartung daneben. **Sichtbar war sie nur im
Messlauf.** Wer den Duktus autort, sah nie, ob die Erkennung ihn richtig
liest — und die Ebene, die nach §3 ausschließlich bemängelt werden darf,
war die einzige, die man nicht anschauen konnte.

### 8.1 Was die Linse zeigt

In der Buchstaben-Ansicht (`/admin/buchstaben?g=<key>`) steht unter „Wie es
geschrieben wird“ ein Schalter **Landmarken**. Aufgeklappt zeichnet er die
erkannten Strukturen **auf die geschriebene Form** — nicht daneben, nicht
in eine Tabelle:

| Marke | Darstellung | Woher |
|---|---|---|
| **Kreuzung** | Ring am Punkt, Mittelpunkt gefüllt | `crossing_landmarks` — die durchstoßende Selbstkreuzung (§14 v2) |
| **Retrace-Zone** | Band entlang der Bahn | `classified_pass_points`, Klasse `retrace` |
| **Berührung** | dasselbe Band, gepunktet | Klasse `touch` — vorbei, nicht darüber |
| **Verschmelzung** | schraffiertes Band | Klasse `overlap` — Partner im ANDEREN Federzug |
| **Absetzen** | Strich am Wiederaufsetz-Punkt | `trace_meta.stroke_starts` |
| **Umkehrecke** | Quadrat auf dem Anker | `trace_meta.corner_anchors` |
| **Kringel** | Kreis im Maß der Öffnungsweite `D0` | `loop_apertures` + Katalog-Urteil |

Jede Marke trägt ihre Zahlen (Kreuzungswinkel und die beiden Züge, die sich
trafen; Bogenlänge einer Zone; `D0`, Größenklasse, Zustand, Platten-`D0`
und Vorkommen einer Schleife) und ist anklickbar; die Legende ist zugleich
der Filter je Klasse. Der Schalter **Tafel-Duktus ⇄ Laufform** zeigt
dieselbe Ebene auf der jeweils anderen gespeicherten Zeile — beide kommen
in EINEM Read, weil zwei Round-Trips zwei verschiedene Momente desselben
Buchstabens zeigen würden.

**Drei Dinge zeigt die Linse ausdrücklich, statt sie zu verschweigen:**

1. Ein Buchstabe, in dem die Erkennung nichts findet, sagt das — statt als
   leerer Buchstabe zu erscheinen.
2. Eine Katalog-Schleife, der keine erkannte Schleife zugeordnet werden
   konnte, bleibt als **unzugeordnete Zeile** stehen („Im Katalog, hier
   nicht gefunden“), mit ihrer Klasse, ihrem Zustand und dem Hinweis „kein
   Schleifenbereich erkannt“. Das **`t`** ist der stehende Fall: die Platte
   hält drei Binnenflächen, der raster-freie Schleifenfinder
   (`core/aggregate.py::loop_ranges`) hat für den Buchstaben überhaupt
   keinen Bereich, und der Katalog trägt diese Uneinigkeit seit `sep06` in
   seinem eigenen Kopf (`ductus_loops_per_glyph`). Nichts zu zeigen hieße
   zu behaupten, der Buchstabe habe keinen Kringel.
3. Fehlt der Kringel-Katalog für die gewählte Vorlage — er ist an EINER
   Hand mit EINER Feder abgelesen —, kommen die Schleifen ohne Urteil
   („unbekannt“) statt mit einem geratenen.

### 8.2 Die Route

`GET /sources/{source_id}/templates/{glyph_key}/landmarks` — admin-gegatet
aus demselben Open-Core-Grund wie die Roh-Zeile, aus der sie abgeleitet ist
(`quellen-und-rechte.md` §5), damit `private, no-store` und im
Public-Surface-Test als RESERVED festgenagelt. Antwort: `glyph_key`,
`style_id`, ein `catalogue`-Block (welcher Katalog geantwortet hat oder
warum keiner) und `rows` — Variante 0 und, wo vorhanden, Variante 100, je
mit `landmarks` (Art · Index · Position · `numbers` · `points` einer Zone),
`loop_ranges` und `unmatched_catalogue`. Alle Koordinaten in
**Template-Einheiten** (Grundlinie 0, Mittelband 1, y nach oben), also im
Rahmen, in dem die Seite den Buchstaben zeichnet.

Gerechnet wird auf der **gerenderten** Geometrie
(`render_payload_for_template`), nicht auf den gespeicherten Ankern: der
Gleichzug-Weg weitet Rundformen zur Renderzeit (`_fluent_widen`), und eine
Marke, die dort sitzt, wo die Tinte NICHT ist, ist schlechter als keine.
Eine Folge davon gehört dazu gesagt: die Schleifenbereiche werden damit auf
der gerenderten Zeile gezählt, wo der Katalog-Kopf sie auf der rohen
Tafelzeile gezählt hat.

### 8.3 Warum die Erkenner nach `core/` gezogen sind

`core/`, `api/` und `alembic/` dürfen `tools/` nicht importieren — das
API-Image liefert es nicht aus (`tests/test_imports.py`). Die Erkenner
lagen aber genau dort. Sie sind deshalb **unverändert** nach
`core/landmarks.py` gezogen worden, und die drei bisherigen Heimatmodule
re-exportieren sie unter ihren alten Namen:

- `tools/pairlab/landmarks.py` — die Selbstkreuzungen (§13a-Zensus);
- `tools/tracebench/counters.py` — Durchstoß-Test und die
  Retrace-/Berührungs-/Verschmelzungs-Klassifikation (§14 `aug16`);
- `tools/tracebench/kringel.py` — Öffnungsweite, Größenklasse, Zustand,
  Katalog-Leser (§14 `sep06`).

Damit lesen Linse und Messlauf **dieselbe Funktion**, nicht zwei Kopien.
Was in den Werkzeugen bleibt, ist, was nur ein Duell oder ein ganzes Wort
braucht: die Match-Radien und die Eins-zu-eins-Zuordnung zweier
Populationen, die Slot-Zerlegung eines komponierten Worts, die
Bench-Zeilenfelder. **Jede Schwelle in `core/landmarks.py` ist eingefrorene
Mess-Provenienz** — sie zu ändern justiert keinen Admin-Overlay, sondern
setzt Tintenfolger und Kringel-Katalog neu auf.

Der Katalog selbst bleibt, wo er gebaut wurde
(`tools/tracebench/kringel_catalogue.json`), und wird per PFAD gelesen
statt importiert; das API-Image kopiert die eine Datei mit, wie es die
Quiz-Saat schon mitkopiert. Fehlt sie, kostet das die Urteilsspalte, nie
die Antwort.

Eine bewusste Ausnahme von „ein Detektor, eine Stelle“:
`core.geometry.resample_by_step` ist ein Zwilling von
`tools/tracebench/metric.py`, weil dieses Modul eine **festgenagelte
Reinheitsklausel** trägt (das Lineal importiert nichts aus dem Projekt, das
es benotet). Die beiden werden per Test byte-gleich gehalten — dasselbe
Verfahren, mit dem `frames.DIACRITIC_MIN_Y` seine wiederholte Konstante
absichert.

### 8.4 Bemängeln — die fünfte Korb-Ebene

Die Landmarken-Ebene ist **generiert**. Nach §3 heißt das: nur bemängeln,
nie von Hand patchen — und die Linse trägt genau einen Griff, ⚑. Jede
Marke bietet ihn, und der **leere Bereich des Buchstabens** bietet ihn
auch: ein Klick ins Leere meldet, dass an dieser Stelle eine Marke FEHLT.
Das ist die Beschwerde, die eine reine Marker-Fläche gar nicht annehmen
könnte, und sie ist die häufigere Hälfte des Autor-Wunsches.

Ein solcher Eintrag ist `kind = "landmark"` und trägt den `glyph_key` wie
ein Buchstaben-Auftrag. **Keine eigene Spalte, keine Migration:** die
Landmarken-Ebene ist aus genau dieser Zeile abgeleitet, eine zweite
Schlüsselspalte wäre ein zweiter Name für dasselbe. WELCHE Landmarke mit
welchen Zahlen gemeint ist, schreibt die Linse selbst in die ersten zwei
Zeilen der Notiz — Zeile 1 die Identität, Zeile 2 die Messwerte:

> ```
> Landmarke: Kringel #0 (loop#0) · t · Tafel-Duktus (Variante 0)
> x 0.3592 · y 0.4027 · d0 0.2475 · size_class klein · state offen · d0_plate 0.3761 · occurrences 9
>
> Der Kringel läuft hier fast zu — die Platte hält ihn offen.
> ```

Zeile 1 ist zugleich die Überschrift der Korb-Zeile, deshalb die Teilung:
ein Auftrag, dessen ganze Identität in einer Wand aus Zahlen steckt, liest
sich nicht. Der Korb verlinkt die Zeile auf ihren Buchstaben, und die API
verlangt für `landmark` einen nichtleeren Notiztext — ein Auftrag, der
nicht sagt, WELCHE Landmarke, ist unbearbeitbar.

**Neue Stufe im §5-Vokabular: `landmark_detector`.** Sie benennt als
einzige keinen Schritt des Schreibwegs, sondern den Ausgang „der Buchstabe
war richtig, der Erkenner falsch“. Sie steht in der Triage-Reihe zuletzt
vor `not_reproducible`, weil die Reihenfolge auch hier gilt: erst fragen,
ob der autorierte Duktus stimmt (`chart_ductus` — und dann ist es eine
**Rückgabe an den Autor**, kein Fix), dann die Laufform, dann die
Klassenregel, und erst zuletzt den Sensor verdächtigen, der das alles
liest.
