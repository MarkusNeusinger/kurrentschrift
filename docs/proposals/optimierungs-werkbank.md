# Optimierungs-Werkbank 2026-07-31 — eine Admin-Fläche, Stufen-Doktrin, Auftragskorb

**Status: Richtungsentscheid des Nutzers (2026-07-31, zwei Fragen):
(1) EINE neue Werkbank-Seite `/admin/werkbank`** — Wort-Rückgrat +
umschaltende Kontext-Linse + Auftragskorb; die bestehenden Seiten
(`/admin/vergleich`-Tabs, `/admin/paare`, `/admin/belege`) bleiben, bis
die Werkbank sie schrittweise ersetzt. **(2) Der Auftragskorb lebt als
DB-Tabelle `work_items`** mit Admin-API — die KI liest offene Aufträge
am Rundenstart und meldet je Auftrag erledigt. Umsetzung: W1 (Backend)
in Arbeit, W2 (Seite) nach Merge von W1 + PR #251 (Belege-Seite = das
Wort-Rückgrat). §3–§5 sind die **bindende Stufen-/Rollen-Doktrin** für
Mensch UND KI — Pflichtlektüre, bevor ein `work_items`-Auftrag
bearbeitet wird.

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

**KI-Seite — bindend bei jedem Auftrag:**

1. Offene Aufträge lesen: `GET /sources/{id}/work-items?status=open`.
2. **Triage-Pflicht** entlang §3, in dieser Reihenfolge prüfen:
   Tafel-Duktus falsch? → Laufform/Fit? → Klassenregel? → Platzierung?
   → erst zuletzt: Paar idiosynkratisch (Override)?
3. **Regel-Fix vor Override.** Ein Override ohne vorherige
   Regel-Prüfung ist ein Doktrin-Verstoß.
4. Wirkung messen (Wordbench-Guard; Metrik/Fixtures bleiben
   eingefroren) und visuell belegen (Vorher/Nachher).
5. `resolution` schreiben — benennt die diagnostizierte Stufe, die
   Änderung, die PR und den Messstand — und Status auf `done` PATCHen.
6. Ergibt die Triage eine **Ground-Truth-Lücke** (Tafel-Duktus falsch,
   Fit ohne manuellen Trace unmöglich): Status bleibt `open`,
   `resolution` beginnt mit „Rückgabe an Autor:" und nennt den konkret
   benötigten manuellen Schritt (Wizard-Glyphe X, Wort Y nachfahren).

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
