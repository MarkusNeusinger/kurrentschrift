# Planänderungen — Vorschläge

Staging-Bereich für **vorgeschlagene** Anpassungen an den beschlossenen
Konzept-Dokumenten unter [`docs/concepts/`](../concepts/). Solange ein
Vorschlag hier steht, ist er **nicht** Teil der Architektur. Erst nach
Freigabe wandert ein Vorschlag in das jeweilige Konzept-Dokument und
wird hier gestrichen.

Zweck: §10 von [`architektur.md`](../concepts/architektur.md) sagt
„erst der kleinste lauffähige Kern, dann alles andere"; CLAUDE.md sagt
„do not re-litigate decisions that have an explicit 'verworfen'
section". Beides gilt weiter. Diese Datei ist der saubere Ort, an dem
neue Beobachtungen formuliert werden können, ohne die settled docs
vorzeitig zu mutieren.

Stand: Mai 2026. Anlass: Beobachtung des Nutzers, dass das Rund-s nicht
nur am Wortende, sondern auch an Morphemgrenzen in Komposita auftritt
(`Aus-flug`, `Haus-thür`); siehe [`orthographie-regeln.md`](../schriftkunde/orthographie-regeln.md)
§1.

---

## Vorschlag A — `architektur.md` §3: `position` als Lehrtafel-Rolle präzisieren ✓ FREIGEGEBEN

**Status:** in `architektur.md` §3 (Mai 2026) eingearbeitet. Hier nur zur
Nachvollziehbarkeit aufgeführt; **nicht mehr offen**.

`position` (initial/medial/final) ist jetzt als **Lehrtafel-Rolle** der
Allograph-Form definiert — *wo Loth (oder eine vergleichbare Vorlage) diese
Form auf der Tafel zeigt*. Die orthographische Frage „welche Vorlage gilt
für einen konkreten Slot im Lauftext" liegt in
[`orthographie-regeln.md`](../schriftkunde/orthographie-regeln.md) und wird
von Vorschlag D (`core/orthography.py`) konsumiert.

---

## Vorschlag B — `architektur.md` §2 und §4: systematische Bigramm-Extraktion aus Beispieltext

**Status:** größer, betrifft zwei Festlegungen. Diskussion offen.
**Mess-Evidenz (2026-07-08, Beobachtung — keine Übernahme):** Der erste
Compose-Loop hat die per-Paar-Residualtabelle über alle 48 scorbaren
Abb.-19-Wörter erzeugt (Segment-Attribution, beste Generator-Settings;
`tools/wordbench/runs/loop-jul08/vorschlag-b-residuals.tsv`, Zusammenfassung
in `qualitaetsmetrik.md` §6). Kein Paar weicht dramatisch ab; die Ausreißer
(`h→r` 0.33, `r→f` 0.32, `l→v` 0.31, `e→h` 0.30 — alle n=1) sind eher
Einzelglyph-/Bogenbreiten-Effekte als systematische Paarformen. Die
Haupt-Abweichung liegt laut Loop **in den Bogenbreiten der Glyphen selbst**
(Chart-Zelle vs. fließende Schrift), nicht in den Übergängen — ein Argument
GEGEN gespeicherte Paar-Overrides beim heutigen Stand. Overrides bleiben
gegated; nichts wurde gespeichert.
**Mess-Evidenz (2026-07-11, `tools/pairlab` — Beobachtung, keine
Übernahme):** die platzierungsbereinigte Paar-Sektion
([`uebergaenge-befund.md`](uebergaenge-befund.md)) bestätigt: kein
Kleinbuchstaben-Paar verhält sich idiosynkratisch — die Abweichungen
gruppieren sich nach Exit-KLASSEN (generisch lösbar). Stärkste Kandidaten
für echte gefittete Paarformen sind die Versal-Verbindungen (B→i 0.258,
I→n 0.249, D→u 0.195), die laut MVP-Scope ohnehin später kommen.

### Heutige Festlegung

- §2 verwirft pauschal „Bigram-Datenbank aller Buchstabenkombinationen:
  kombinatorisch unmöglich und unnötig".
- §4 erklärt Übergänge zur Konsequenz, nicht zum Datensatz: „Übergänge
  zwischen Buchstaben sind essenziell — aber **kein eigenes Objekt** und
  **kein zu sammelnder Datensatz**." Begründung: `exit`+`entry` mit
  Tangente und Kopplungshöhe erzeugen den Übergang geometrisch; der
  geschlossene Ligatur-Satz (§4 Ausnahme) ist die einzige Erweiterung.

### Beobachtung des Nutzers

Beim Import von **Beispieltext** (echte Handschrift, nicht Lehrtafel)
fallen ohnehin Bigramme als Nebenprodukt an: jedes Buchstabenpaar im
Wort hat eine konkret beobachtete Verbindungsgeometrie in derselben
Hand. Zwei Argumente für ihre systematische Erfassung:

1. **Strukturelle Andersartigkeit verketteter Formen.** Bestimmte
   Buchstaben (z. B. `C`, `H` in den gesichteten Vorlagen) sehen in
   Verkettung topologisch anders aus als isoliert — das ist mehr als
   eine Übergangs-Auslenkung. Vergleichbar mit den Ligaturen aus §4, nur
   ohne Lehrtafel-Definition.
2. **Wo Paar = bloße Verkettung, ist die Mitspeicherung billig.** Falls
   ein Paar nicht von der generierten Verbindung abweicht, geht durch
   das Speichern nichts verloren; im Renderer wird ohnehin der gleiche
   Default herauskommen. Wo das Paar abweicht (Fall 1), gewinnt das
   Rendering eine echte Beobachtung statt einer Generator-Annäherung.

### Vorgeschlagene Erweiterung

Beim Beispieltext-Import alle vorkommenden Bigramme parallel zur
Einzelglyph-Extraktion als **opportunistische Zusatz-Daten**
speichern. Render-Pfad:

1. Wenn ein gefittetes Paar in derselben Hand vorliegt → es nutzen.
2. Sonst → den §4-Default verwenden (Übergang aus `exit`/`entry`-
   Geometrie generieren).

### Auflösung der Spannung zu §2 und §4

§2s Anti-Bigram-Argument zielt auf einen **a priori angelegten**
kompletten Bigram-Vorrat für alle theoretischen Buchstabenkombinationen
(„alle Buchstabenkombinationen"). Der Vorschlag legt aber kein solches
Universum an, sondern erntet ausschließlich, was in **konkreter
Handschrift** tatsächlich vorkommt — die Mächtigkeit ist datengetrieben
endlich.

§4s Generator-Logik bleibt als **Default** in voller Kraft; das
gefittete Paar ist ein **opt-in-Override** für jene Bigramme, für die
echte Beobachtungen in derselben Hand existieren. „Übergang als
Konsequenz" wird nicht negiert, sondern um eine
„Beobachtungs-Override"-Schicht ergänzt.

### Offene Punkte für die Diskussion

- **(a) Schema-Repräsentation.** Eigene Tabelle `glyph_pairs` (zwei
  Foreign-Key auf `glyphs` plus eigene Geometrie-Spalten) vs. erweiterte
  JSONB-Spalte in `glyphs`. Erstere ist sauberer für Statistik und
  Query-Patterns, letztere billiger einzuführen.
- **(b) Auswahlregel zur Render-Zeit.** Bei mehreren gefitteten Paaren
  derselben Hand: Mittelwert, Median, oder zufällige Auswahl pro
  Render-Lauf (Varianzerhaltung)?
- **(c) Schwelle „identisch genug, um identisch zu zählen".** Falls wir
  Speicher sparen wollen, brauchen wir eine Toleranz, ab der ein Paar
  als „nur Verkettung" zählt und nicht eigens persistiert wird.
  Andernfalls ist die Maximalmenge `|G|² × #Hände × #Instanzen`.
- **(d) Verhältnis zum geschlossenen Ligatur-Satz (§4 Ausnahme).** Der
  fixe Satz `ch · ck · tz · ſt · qu · ß` bleibt aus Norm-Gründen
  erstklassig; gefittete Paare sind eine zusätzliche Schicht *darüber*,
  ohne die Ligaturen zu ersetzen.
- **(e) Großbuchstaben-Klausel.** Die motivierende `C`/`H`-Beobachtung
  betrifft Großbuchstaben, die laut
  [`mvp-roadmap.md`](../concepts/mvp-roadmap.md) §MVP-Scope „explizit
  ausgeklammert" sind. Der Vorschlag wird daher erst mit der
  Großbuchstaben-Phase praktisch relevant; das Prinzip kann aber schon
  im MVP-Beispieltext (Kleinbuchstaben) verprobt werden.
- **(f) MVP-Gates.** Die drei Validierungs-Gates in
  [`mvp-roadmap.md`](../concepts/mvp-roadmap.md) §MVP-Validierungs-Gates
  bleiben unberührt; der Vorschlag fügt hinzu, ersetzt nicht.

### Blast Radius bei Freigabe

- Mittelgroß. `architektur.md` §2 und §4 brauchen eine
  Präzisierungs-Klausel („…gilt nicht für opportunistische Bigramme aus
  Sample-Imports"), nicht aber einen Umsturz.
- Schemaänderung erst bei Implementierung (Beispieltext-Import liegt
  jenseits von M3).

---

## Vorschlag C — `architektur.md` §3: Positions-Verteilung datengetrieben prüfen

**Status:** wird zusammen mit Vorschlag B beim Beispieltext-Import
relevant. Konzeptionell isoliert dokumentierbar.

### Heutige Annahme

Die Lehrtafel-Position eines Glyphs ist auch die orthographische
Wahrheit über sein Auftreten im Lauftext. Vorschlag A nimmt diese
Identität bereits prinzipiell zurück; Vorschlag C macht den
Korrektur-Mechanismus konkret.

### Beobachtung des Nutzers

Aus dem Beispieltext-Import fällt automatisch eine
**Häufigkeitsverteilung** pro Glyph an: wie oft wird er initial,
medial, final beobachtet? Damit lässt sich datengetrieben prüfen, ob
die a-priori-Annahmen aus der Lehrtafel der Realität standhalten — etwa,
ob ein als „nur final" geführter Glyph tatsächlich nie wortintern
auftaucht, oder ob er an Morphemgrenzen erscheint (Rund-s-Fall aus
§1.2 der Regeln).

### Vorgeschlagene Erweiterung

Im Glyph-Statistik-Layer der dreistufigen Qualitätspipeline
([`architektur.md`](../concepts/architektur.md) §6.1, „Robuste
Statistik") zusätzlich die **Text-Positions-Verteilung** mitführen.
Sichtbar im Editor und in Berichten — damit Abweichungen von der
Lehrtafel-Annahme sofort erkennbar werden und in
[`orthographie-regeln.md`](../schriftkunde/orthographie-regeln.md)
zurückfließen können.

### Verhältnis zu Vorschlag A

A definiert `position` als Lehrtafel-Rolle. C führt eine **zweite**,
parallele Größe ein: die empirisch beobachtete Text-Positions-Verteilung.
Beide koexistieren ohne Konflikt: A ist eine Eigenschaft des Templates,
C ist eine Statistik über Instanzen.

### Blast Radius bei Freigabe

- 1 Absatz in `architektur.md` §3 (Erwähnung der zusätzlichen Statistik)
  und 1 Absatz in §6.1 (Inhalts-Erweiterung der Statistik-Schicht).
- Schemaänderung minimal: eine Statistik-Aggregation, kein neues
  Glyph-Konzept.

---

## Vorschlag D — neues Modul `core/orthography.py` (M4+)

**Status:** Folge-Konsequenz aus A und (optional) B/C. Wird mit dem
Text→Template-Mapper in M4 designt — kein Code jetzt, kein Stub im
Voraus.

**Nachtrag (Juli 2026):** Der hier beschriebene Text→Glyph-Slot-Mapper
existiert inzwischen als pragmatischer Vorläufer in `core/shaping.py`
(Lang-s-Regel, Fuge-Marker `|`, geschlossenes Ligaturen-Set,
Positions-Zuweisung pro Joins-Klassen-Run; TS-Twin `shaping.ts`). Offen
bleibt die hier gemeinte **volle** silbenbewusste Orthographie-Schicht
(Regeln aus `orthographie-regeln.md` als Daten) — sie würde
`core/shaping.py` ablösen bzw. speisen. Hinweis zur Terminologie: die
im Text erwähnte `glyphs`-Tabelle heißt seit Migration 0004
`templates` (Schema in `core/database/models.py`);
„`glyphs.position` → `glyphs.chart_role`" liest sich heute als
`templates.position` → `templates.chart_role`.

### Verantwortung

Mappt einen Eingabetext (deutscher Text in moderner oder vor-1901-
Schreibung) auf eine Sequenz von Glyph-Slots der Form
`(glyph_key, allograph_role, segmentation_context)`. Konsumiert die
Regeln aus [`orthographie-regeln.md`](../schriftkunde/orthographie-regeln.md)
als Daten.

### Skizzierte Signatur (nur als Diskussionsgrundlage)

```python
def to_glyph_sequence(text: str) -> list[GlyphSlot]: ...
```

`GlyphSlot` hält mindestens: `glyph_key`, `chart_role`, ggf.
`pair_with_next` (wenn Vorschlag B umgesetzt ist).

### Begleit-Refactoring bei Implementierung

Wenn dieses Modul gebaut wird, ist auch der Moment, in dem
`glyphs.position` sinnvoll in `glyphs.chart_role` (oder ähnlich)
umbenannt werden kann — als eine Migration in derselben PR. **Nicht
jetzt**: ohne Aufrufer wäre die Schnittstelle geraten.

---

## Querverweise

- [`architektur.md`](../concepts/architektur.md) §2 (Bewusst NICHT
  gewählt), §3 (Schema), §4 (Übergänge), §6.1 (Statistik)
- [`mvp-roadmap.md`](../concepts/mvp-roadmap.md) §MVP-Scope,
  §MVP-Validierungs-Gates
- [`orthographie-regeln.md`](../schriftkunde/orthographie-regeln.md)
  (Quelle der Anlässe für die Vorschläge in dieser Datei)
- [`CLAUDE.md`](../../CLAUDE.md) — „do not re-litigate decisions"-Regel
  begründet, warum Änderungen an settled docs den Umweg über diese Datei
  nehmen.
