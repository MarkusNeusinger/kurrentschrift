# Handmodell-Stufenplan 2026-07-31 — Duktus-Prior, Laufformen, Statistik pro Glyphe und Paar, eigene Hand

**Status: Richtung entschieden (Nutzer, 2026-07-31) für H1 + H2 —
Vorkommen speichern, nicht nur Mediane, auf ALLEN drei Ebenen:** pro
Glyphe, pro Paar *und* pro Wort wird jedes saubere Vorkommen als Zeile
abgelegt (Glyphen → die bestehende `instances`-Tabelle, Fokus die Form
selbst und ihre Varianten; Paare → eigene additive Tabelle, Fokus der
natürliche Übergang; Wörter → `word_instances`, die vollständige
Lern-Schablone: Specimen-Crop + nachgefahrener Schreibpfad +
Slot-Labels). Nicht alle Kombinationen werden vorkommen — gespeichert
wird, was die Vorlagen hergeben, und der Bestand wächst über die
Nachfahr-Schleife (s. H2-Absatz „Trainingsmenge"). Umsetzung der
Persistenz: PR #250. **H0 umgesetzt** (Bench + wordlab komponieren mit
den eingefrorenen Laufform-Varianten; Re-Baseline Wörter 0,1169 ·
Paare 0,1645, Zerlegung in qualitaetsmetrik.md §6 „H0-Anschluss").
**Auch der Aggregations-Schritt aus H1 ist umgesetzt:** die
admin-gesicherten Endpunkte `GET/POST
/hands/{hand_id}/aggregates[/rebuild]` füllen die seit `0004` leere
`aggregates`-Tabelle aus den gespeicherten `instances` (Median-Anker +
MAD-Hülle + gepoolte Schicht-1-Statistik, Rechenkern
`core/aggregate.py`); Migration `0021` schlüsselt die Tabelle auf
`(hand_id, glyph_key, variant)` um, und der Prüfstein steht als
`laufform_dev_xh` je Glyphe in der Rebuild-Antwort (Abstand
rekonstruierter Median ↔ gespeicherte Laufform). **Damit ist H1
vollständig:** `POST /hands/{hand_id}/aggregates/apply-laufform`
(admin-gesichert) leitet die Varianten-100-Zeilen aus den
*gespeicherten* Aggregaten ab — Median-Anker als Geometrie, Breiten,
Strich-Topologie und entry/exit/advance weiter aus der Tafel-Zeile,
über denselben Helfer `build_laufform_canonical`, den auch der manuelle
`PUT …/templates/{key}/laufform` benutzt. Bewusst ein *eigener*
Schritt, nicht Teil des Rebuilds: Aggregate sind Statistik, die
Laufform-Zeile ist Render-Zustand. Nur Basis-Varianten speisen sie
(eine Varianten-100-Beobachtung würde die Zeile aus sich selbst
ableiten); Schlüssel ohne Tafel-Zeile oder mit abweichender Ankerzahl
werden mit Grund gemeldet statt geraten, und die Antwort nennt je
Glyphe den Abstand *vor* dem Schreiben. Ein anschließender Rebuild
meldet den Prüfstein als 0. **Auch der Aggregations-Schritt aus H2 ist
umgesetzt:** die ebenfalls admin-gesicherten Endpunkte `GET/POST
/hands/{hand_id}/pair-aggregates[/rebuild]` verdichten die
`pair_instances` einer Hand über alle Quellen hinweg je
`(left_key, right_key)` in die eigene additive Tabelle
`pair_aggregates` (Migration `0023`) — Median-Offset,
bogenlängen-gleichmäßig nachgesampelter Median-Connector, MAD-Hüllen
für beides und gepoolte Dissektions-QC (`gen_chamfer` als
Audit-Zahl „gemessen vs. komponiert", Ink-Lücken-Anteil,
Wort-/Paar-Platten-Histogramm). `min_n` ist hier 1 statt 4, weil Paare
dünn belegt sind (87 Vorkommen auf 45 Paare der 1922er Platten) — die
Zeile nennt `n_instances`, damit jeder Leser gewichten kann. Bewusst
**ohne** Apply-Gegenstück: die Paar-Statistik ist rein lesend,
`glyph_pairs` bleibt der verbatim übernommene Override (R3) und der
§4-Generator bleibt Default; am Rendering ändert der Schritt nichts.
**Erste Nutzung, rein lesend:** beide Statistik-Schichten sind seit der
Werkbank-Stufen-Einsicht in `/admin/werkbank` einsehbar — die
Buchstaben-Linse zeigt den Aggregat-Median mit MAD-Streuung und
gepoolter Schicht-1-Statistik, die Paar-Linse die gemessene
Median-Verbindung über ihren Vorkommen samt Dissektions-QC
(`gen_chamfer` als Audit-Zahl); Neuaufbau je Schicht per Knopf,
`apply-laufform` bewusst nicht (optimierungs-werkbank.md §7, W5).
**Damit ist die zweite Hälfte der ersten Nutzung ebenfalls
umgesetzt:** der Verbindungen-Tab von `/admin/vergleich` trägt je
Paar-Karte die Zeile „Gemessen" zwischen Kopf und Bild —
Vorkommenszahl (Aggregat-`n_instances`, ersatzweise die zugeordneten
Vorkommen) und `gen_chamfer`-Mittel als Chips, die ausführlichen
Zahlen (Streuung, Ernte-Abstand, Fit-Rest, Versatz ± MAD,
Ink-Lücke, Platten-Histogramm) im Tooltip, dazu „Fit unsicher", wenn
das Vorkommen *dieser* Vorlage keinen sauberen Fit hat. Geladen wird
einmal je Quelle (öffentliche `pair-instances` + admin-gesicherte
`pair-aggregates` der aus den Zeilen abgeleiteten Hand), nie je Karte;
ohne Admin-Lesezugang bleiben die Vorkommenszahlen stehen. Bewusst nur
Zahlen: die Median-Skizze bleibt der Werkbank-Linse vorbehalten, eine
registrierte Überlagerung von gemessenem Connector und komponiertem
Paar unterbleibt (verschiedene Rahmen — eine falsche Deckung läse sich
als Beleg). H3–H5 bleiben Vorschlag.
Konsolidiert die
Laufform-Runde vom 30./31.07.2026 (PR #246/#247: Median-Laufformen als
Template-Variante 100, `laufform_by_key` im Composer) und die
Quellen-Recherche
([`../notes/quellen-recherche-2026-07.md`](../notes/quellen-recherche-2026-07.md))
zu einem Stufenplan. Er ändert **keine** getroffenen Entscheidungen —
er füllt die seit Migration `0004` angelegte, bislang leere
Statistik-Schicht (`instances`/`aggregates`, architektur.md §3/§12)
mit dem inzwischen real existierenden Fit-Werkzeug. Die
R-Nummerierung von
[`schreibsystem-redesign.md`](schreibsystem-redesign.md) (R1–R5, alle
umgesetzt) wird nicht fortgesetzt; dieses Dokument nummeriert H0–H5.

## 1. Anlass

Drei Fragen aus der Laufform-Runde:

1. **„Ist die Idee grob richtig?"** — Tafel-Glyphen ausschneiden und
   nachfahren liefert den Duktus (Strichfolge, Kreuzungen) und die
   idealisierte Einzelform; für Wörter reicht Aneinanderkleben nicht,
   es braucht handangepasste Varianten (gedehnt, geneigt …) plus
   Statistik pro Glyphe und pro Buchstabenpaar.
2. **„Wenn wir so viele verschiedene Hände haben — taugt das noch als
   Vorbild?"** — nach der Recherche-Runde liegen neben der
   1922er-Normhand u. a. 17 Galerie-Seiten fremder Hände im Repo.
3. **Komplexitäts-Sorge:** „das ganze wird immer besser, aber der Code
   auch immer komplexer" — jede Stufe muss sich auch daran messen
   lassen, ob sie Sonderfälle abbaut statt aufbaut.

## 2. Das Rollenmodell (Bestätigung, keine Neuerung)

Die Idee ist nicht nur „grob richtig" — sie ist die dokumentierte
Architektur. Drei Rollen, alle bereits festgelegt:

| Rolle | Artefakt | Beleg |
|---|---|---|
| **Duktus-Prior** — Strichfolge, Pen-Lifts, Kreuzungs-Auflösung, idealisierte Einzelform | Tafel-Zelle → `templates` (Anker, `raw_path`, `stroke_starts`) | architektur.md §2/§3: „Analysis-by-Synthesis mit Duktus-Prior" |
| **Form-Vorbild fürs Geschriebene** — wie die Buchstaben im verbundenen Wort wirklich aussehen | Wortproben **einer** Hand → M4-Fits → Laufformen/Statistik | §3: „Per-Instanz-Abweichung: der konkrete Fit (Statistik)"; empirisch: Laufform-Runde (Wörter-Bench 0,1208 → 0,1136 mit Median-Formen) |
| **Kontext, nie Vorbild** — fremde Hände | Hände-Galerie, Abb.-22-Schülerhand, künftige Quellen | §12: Statistik strikt **pro Hand** (`aggregates` unique je `(hand, glyph, …)`), hand-übergreifend nur Vergleich/Heatmaps; quellen-und-rechte.md §7: nie über Hände mitteln |

Damit ist auch Frage 2 beantwortet: **Viele Hände machen das Vorbild
nicht unscharf, weil nie über Hände gemittelt wird.** Eine gerenderte
Schrift hängt immer an genau *einer* Hand (Modell); jede weitere Hand
ist Vergleichsmaterial — und später ein weiteres *wählbares* Modell.
Genau deshalb gilt in der Wordbench die Same-Hand-Headline-Disziplin
(qualitaetsmetrik.md §6).

**Zielbild pro Schriftfamilie — drei wählbare Stimmen, eine
Pipeline:**

1. die **Tafel-Idealform** (Einzelbuchstaben zeigen/lehren — Tafel,
   Schriftkunde, Quiz),
2. eine **historische Hand** als Wort-Modell (Tafel-Duktus, an die
   Wortproben dieser Hand angepasst),
3. die **eigene Hand** (Vision Ziel 6: „In meiner Hand, aber jeden
   Text").

Quellenlage: Für Sütterlin ist die same-hand Wortprobe erschöpfend
vermessen (Abb. 19/20); für Kurrent und Offenbacher sind Kandidaten
derselben Hand vorrecherchiert (federmodelle.md §4: Loth 1866 S. 14,
Koch-Heft PDF-S. 38–39 — extern gesichtet, im Repo noch nicht
vermessen; Same-Hand-Eigenschaft, Wortzahl und Rechte pro Abbildung
vor Nutzung zu verifizieren).

## 3. Ist-Stand: was schon steht, was fehlt

Bereits umgesetzt (Idee-Element → Artefakt):

- Tafel ausschneiden + nachfahren → Einrichtungs-Wizard, `bboxes` +
  `templates`; Einzelform öffentlich via `/write/glyphs`.
- „Aneinanderkleben sieht unnatürlich aus" → §4-Übergangs-Generator +
  Verbindungsklassen-Runden (Girlande, Gabel-Joins, Bar-Exits,
  Kapital-Übergabe; qualitaetsmetrik.md §6, Juli 2026) +
  `glyph_pairs`-Overrides (R3) für beobachtete Paare.
- „Glyphen gedehnt/gedreht ans Wort angepasst" → Median-Laufformen als
  Template-Variante `100` (`LAUFFORM_VARIANT`), im Composer über
  `laufform_by_key` nur in fließenden Läufen (Run ≥ 3); dazu die
  handdestillierten Konstanten `LAUFFORM_SX`, `FLUENT_BODY_PITCH`,
  `ASCENDER_LEAN_*`.
- Ernte-Werkzeug → `tools/laufform/harvest.py`: M4-Fit **jedes**
  Buchstaben-Vorkommens der Abb.-19-Fixtures (Gates: konvergiert,
  RMSE ≤ 2,2 px, nicht am Rand, n ≥ 4), zentriert („shapes, not
  placements"), dann per-Anker-Median.

Die drei Lücken:

1. **Die Einzel-Fits werden weggeworfen.** Nach dem Median verwirft
   die Ernte genau das, was die Statistik-Schicht braucht: die
   gefitteten Anker pro Vorkommen, Placement-Offsets, RMSE,
   Wort-/Slot-Kontext. `instances` (Schema seit `0004` bereit, Repo
   nur lesend) bleibt leer; `hands` ist leer, also kann auch
   `aggregates` (FK auf `hands`) nicht befüllt werden.
2. **Paar-Statistik hat kein Zuhause.** `glyph_pairs.geometry` ist
   *ein* verbatim-Override, keine Verteilung; §12 kennt
   Übergangswinkel nur hand-weit, nicht pro Paar. Dass Übergänge
   paarabhängig sind, zeigen die pairlab-Befunde
   ([`uebergaenge-befund.md`](uebergaenge-befund.md)) — gemessen wird
   es längst, gespeichert nie.
3. **Hand-Wissen lebt als Code-Konstanten.** `LAUFFORM_SX`,
   `FLUENT_BODY_PITCH`, `FORK_*`, `BAR_*`, `CAP_*` … sind aus Platten
   destillierte Mediane **der 1922er-Normhand**, eingefroren als
   globale Konstanten in `core/compose.py` (bzw. `FLUENT_BODY_PITCH`
   im Render-Pfad, `core/pipeline.py`). Für eine zweite Hand
   müssten sie neu gemessen werden — heute nur per Code-Änderung.
   Das ist zugleich der Kern der Komplexitäts-Sorge.

## 4. Stufen

### H0 — Bench-Anschluss der Laufformen (Abschluss der laufenden Runde)

Wordbench komponiert mit den Varianten-100-Laufformen (Fixture-Export
+ `laufform_by_key` in `tools/wordbench/run.py`), dokumentierte
Re-Baseline in qualitaetsmetrik.md §6 (erwartet ~0,1136). Kein neues
Konzept — der Messstand holt den Produktionsstand ein.

### H1 — Einzel-Fits persistieren (`instances` + `hands` befüllen)

- Eine `hands`-Zeile je Vorbild-Hand, zuerst `suetterlin-1922-norm`.
- Die Laufform-Ernte schreibt zusätzlich pro sauberem Fit eine
  `instances`-Zeile: `anchors` (gefittet), Crop-Region,
  `measurements` (JSONB: `ddx/ddy`, `geo_rmse_px`, Wort-Id + Slot,
  Nachbar-Keys, §12-Schicht-1-Größen). Position bleibt hier legitime
  Beobachtungs-Dimension (§3).
- Aggregation je `(hand, glyph_key)`: Median-Anker (= heutige
  Laufform), Streuung pro Anker (Hülle), `n_instances` →
  `aggregates`; die Varianten-100-Zeile wird zur **Ableitung** aus dem
  Aggregat statt Endprodukt der Ernte.
- Prüfstein: aus den `instances` reproduzierter Median ==
  gespeicherte Laufform; Bench unverändert.

### H2 — Paar-Statistik

Pro beobachtetem Join der Wort-/Paar-Fixtures (Datenquelle: die
pairlab-Dissektion — beide Buchstaben unabhängig gefittet):
Koppelhöhe, Ink-Lücke, Verbindungslänge/-winkel, Dehnung des
Nachbar-Auslaufs. Ablage konsequent im Instance→Aggregate-Muster:
**entschieden (2026-07-31) ist die eigene additive Tabelle**
(`pair_instances`: je beobachtetem Join eine Zeile mit
Connector-Geometrie relativ zum linken Exit, Placement-Offset und
QC-Messwerten — der natürliche Übergang selbst, nicht die
Buchstaben); Aggregate je `(hand, left_key, right_key)` sind
**umgesetzt** — eigene additive Tabelle `pair_aggregates` (Migration
`0023`), gefüllt über die admin-gesicherten Endpunkte `GET/POST
/hands/{hand_id}/pair-aggregates[/rebuild]`: Median-Offset,
bogenlängen-nachgesampelter Median-Connector, MAD-Hüllen und gepoolte
Dissektions-QC, `min_n` 1 wegen der dünnen Beleglage.
`glyph_pairs.geometry` bleibt unangetastet
(verbatim-Override, R3). Erste Nutzung rein **lesend**: die
Audit-/Report-Spalten der Wordbench und der Vergleichs-Tab zeigen
„gemessen vs. komponiert" pro Paar (Vergleichs-Tab umgesetzt, s.
Status oben). Rahmen bleibt
[`planaenderungen.md`](planaenderungen.md) Vorschlag B: der Generator
bleibt Default, keine Bigram-Datenbank (architektur.md §2, verworfen).

**Wort-Ebene + Trainingsmenge (Entscheid 2026-07-31):** Zusätzlich hält
`word_instances` je Specimen-Wort die vollständige Lern-Schablone —
Slot-Labels + der nachgefahrene Schreibpfad im Registrierungs-Rahmen
des Worts, gepaart mit dem Crop, den die word-samples-Endpunkte schon
liefern. Die Engine fährt Wörter selbständig nach (Duktus-Prior +
M4-Fit, „wie mit einem Stift, absetzen nur wo nötig") → Provenienz
`traced`; wo sie scheitert, fährt der Admin manuell nach → `authored`,
von keiner Neu-Ernte je überschrieben. Für Paare existiert diese
manuelle Schleife bereits (Paar-Editor, R3); der Wort-Editor im Admin
ist inzwischen umgesetzt (Werkbank W3, aus jeder Belege-Karte). So wächst die Trainingsmenge (Buchstaben ·
Paare · Wörter, je Statistik + Crop + Nachfahrung) kontinuierlich —
zugleich die Datengrundlage für den späteren generativen Writer
([`kurrent-writer-and-recognizer.md`](kurrent-writer-and-recognizer.md)).
Zwei bewusste Vertagungen: **Schriftdicken** entlang des
nachgefahrenen Pfads (aus der `width_map` des Specimens sampelbar,
Spalten/JSONB sind vorbereitet) bleiben zunächst leer — für Sütterlin
(Gleichzug, eine Nib-Breite) tragen sie kaum Information; relevant
werden sie mit den Schwellzug-Schriften. Und der gesamte
Vorkommens-Aufbau läuft **erst für Sütterlin** (die eine vermessene
Normhand); Kurrent/Offenbacher folgen erst, wenn das Ergebnis
überzeugt (H4).

### H3 — Konstanten werden Hand-Parameter (Vereinfachungs-Runde)

Compose-Parameter, die messbare Hand-Eigenschaften sind, wandern aus
dem Code in die Aggregate der jeweiligen Hand (Fallback: heutige
Konstante). Kandidaten in Reihenfolge des erwarteten Abbaus:
`LAUFFORM_SX` (sollte in den gespeicherten Laufform-Breiten
aufgehen), `FLUENT_BODY_PITCH` (dito Rundform-Breiten), danach
geprüft: Girlanden-/Gabel-/Kapital-Bänder. **Gate je Parameter:**
Umzug nur, wenn (a) die Bench nicht verschlechtert **und** (b) netto
Code entfällt oder ein Sonderfall verschwindet. Was das Gate nicht
besteht, bleibt Konstante — die Klassen-Grammatik selbst (Gabel, Bar,
Kapital …) ist Duktus-Wissen und bleibt Code.

### H4 — Zweite historische Hand als eigenes Modell (Generalisierungs-Beweis)

Dieselbe Ernte-Pipeline auf eine zweite same-hand Quelle — Kandidaten
laut Vorrecherche (federmodelle.md §4): Loth 1866 S. 14 (Kurrent)
oder Koch-Heft PDF-S. 38–39 (Offenbacher; dort vermerkte §66-Prüfung
vor jedem Commit). Vorab pro Abbildung verifizieren: Same-Hand-
Eigenschaft, Wortzahl, Rechte. Dann Sidecar nach dem
words.json-Muster, eigenes Bench-Set mit eigener Kennzahl
(abb22-Disziplin), eigene `hands`-Zeile, eigene Aggregate. Beweisziel:
die Pipeline ist hand-generisch, nichts Sütterlin-Spezifisches ist in
H1–H3 eingesickert. (Neue Quellen darüber hinaus — Berger, Dressel —
nur nach eigenem Entscheid, siehe Recherche-Notiz.)

### H5 — Die eigene Hand

Der Vision-Ziel-6-Pfad („Neuer Stil als Basis", §12) auf dem dann
geübten Weg: eigene Proben (S-Pen-Erfassung existiert; Wortliste =
Bench-Wörter + paardichte Sätze), committebar als
`data/samples/own-hand/`, eigene `hands`-Zeile → Fits → Aggregate →
„meine Version" als drittes wählbares Modell. Der strukturelle
Vorteil gegenüber jeder historischen Hand: **beliebig viel
Nachschub** — die Statistik-Tiefe (Varianz pro Anker, seltene Paare),
die Abb. 19/20 mit n = 4–39 pro Buchstabe (die meisten ≤ 20, Seltenes
fällt ganz unters n-≥-4-Gate) nie liefern können, ist hier nur eine
Schreibsitzung entfernt.

## 5. Prüfsteine (bindend über alle Stufen)

- **Nie über Hände mitteln.** Aggregate sind je Hand; Fremdhände
  werden verglichen, nie verrechnet (quellen-und-rechte.md §7,
  architektur.md §12).
- **Same-Hand-Headline unangetastet.** Neue Hände/Sets bekommen eigene
  Kennzahlen (abb22-Muster); Metrik + Fixtures bleiben während
  Optimierungs-Loops eingefroren (qualitaetsmetrik.md).
- **Vereinfachung ist ein Gate, kein Nebeneffekt** (H3-Regel oben).
- **Duktus bleibt Prior:** Laufformen/Statistik verformen die
  Template-Topologie, sie ersetzen sie nicht — Strichfolge,
  Pen-Lifts und Kreuzungen kommen weiter aus der Tafel-Zelle.
- **Rechte-Battery vor jedem neuen Daten-Ingest** (`/audit-licenses`,
  SOURCE.md-Pflichtfelder).

## 6. Verworfen (im Rahmen dieses Plans)

- **Gepooltes Mehr-Hand-Vorbild** („alle Hände zusammen als
  Statistik"): widerspricht §12/quellen-und-rechte.md §7 und würde
  gerade die Handschrift-Identität zerstören, die das Projekt
  synthetisiert.
- **Vollständige Bigram-Datenbank:** bleibt verworfen (architektur.md
  §2); H2 speichert Statistik nur für *beobachtete* Paare, der
  Generator bleibt Default.
- **Neue Stufen vor H0:** erst muss der Messstand (Bench) den
  Produktionsstand (Laufform-Rendering) abbilden, sonst optimiert
  jede weitere Runde gegen eine veraltete Zahl.
