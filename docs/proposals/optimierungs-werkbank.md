# Optimierungs-Werkbank 2026-07-31 — eine Admin-Fläche, Stufen-Doktrin, Auftragskorb

**Status: Richtungsentscheid des Nutzers (2026-07-31, zwei Fragen):
(1) EINE neue Werkbank-Seite `/admin/werkbank`** — Wort-Rückgrat +
umschaltende Kontext-Linse + Auftragskorb; die bestehenden Seiten
(`/admin/vergleich`-Tabs, `/admin/paare`, `/admin/belege`) bleiben, bis
die Werkbank sie schrittweise ersetzt. **(2) Der Auftragskorb lebt als
DB-Tabelle `work_items`** mit Admin-API — die KI liest offene Aufträge
am Rundenstart und meldet je Auftrag erledigt. Umsetzung: W1–W4
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
`composition` · `pair_override` · `word_trace` — plus
`not_reproducible`, das ehrliche Ergebnis, wenn die Beschwerde nicht
auftrat. Ein geschlossenes Vokabular macht aus dem Archiv eine Abfrage
(„welche Stufe verursacht die meisten Aufträge?") statt einer Lesearbeit.

Zwei Regeln machen den Ablauf unumgehbar: Protokollfelder reisen **nur
mit ihrem Statuswechsel** (ein PATCH ohne `status` darf die Notiz
ändern und sonst nichts), und `done`/`returned` verlangen ein bereits
**gespeichertes** `understanding` — Zurückspiegeln und Abschließen in
einem Aufruf lehnt die API ab. Beides schützt dasselbe: Die
Rückspiegelung ist nur etwas wert, solange sie dasteht, während sie
noch korrigiert werden kann.

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

- Manuelle Beiträge (`authored`-Traces, Overrides) gehen **nie** in die
  eingefrorenen Metrik-Referenzen ein — die Messlatte bleibt die Platte
  (qualitaetsmetrik.md).
- Statistik bleibt je Hand (quellen-und-rechte.md §7); die Werkbank
  zeigt immer genau eine Quelle/Hand.
- Die Werkbank ersetzt die Alt-Seiten erst, wenn ihre Funktion dort
  vollständig angekommen ist — bis dahin koexistieren sie.

## 7. Umsetzung

- **W1 — Backend** (in Arbeit): Migration `0020` `work_items` (Ebene,
  Schlüssel, Specimen, Notiz, Status `open`/`done`, `resolution`) +
  admin-gegatete Endpunkte + Tests.
- **W2 — Seite `/admin/werkbank`**: Rückgrat (aus PR #251) + Linsen +
  Korb-UI inkl. Vorsortier-Frage; danach schrittweises Aufgehen von
  Vergleich/Paaren/Belegen.
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
- **W4 — Protokoll** (umgesetzt): §5 als erzwungener Ablauf statt
  Doku-Appell. Migration `0022` ergänzt `understanding` · `reproduced` ·
  `stage` · `acked_at` · `closed_at`; die API weist ein Abschließen ohne
  Verständnis, Stufe oder Ergebnis mit 422 ab; der Korb zeigt die
  Rückspiegelung mit einem „missverstanden"-Knopf, der die Zeile mit der
  Korrektur zurück auf `open` legt. Dazu der quellenfreie Lesepfad
  `GET /work-items` (eine Sitzung soll ihre Aufgaben lesen können, ohne
  vorher eine `source_id` zu erraten) und das Skill
  `.claude/skills/work-basket/`, das den Ablauf führt.
