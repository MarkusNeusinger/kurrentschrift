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
(`Aus-flug`, `Haus-thür`); siehe [`orthographie-regeln.md`](../reference/orthographie-regeln.md)
§1.

---

## Vorschlag A — `architektur.md` §3: `position` als Lehrtafel-Rolle präzisieren

**Status:** offen, klein, isoliert umsetzbar.

### Heutiger Wortlaut (§3, Punkt 1)

> **Position (Allograph):** initial/medial/final — z. B. ſ vs. finales s.
> *Aus dem Kontext bekannt* (s mitten im Wort → medial).

### Problem

Die Klammerbemerkung „s mitten im Wort → medial" suggeriert eine
1:1-Abbildung zwischen Lehrtafel-Position und Text-Position. Die in
[`orthographie-regeln.md`](../reference/orthographie-regeln.md) §1.2/§1.3
gesammelten Sonderfälle (Rund-s an Morphemgrenze, Rund-s vor elidiertem
`h`) brechen diese Identität: das Rund-s erscheint in echtem Text auch
wortintern.

### Vorgeschlagener neuer Wortlaut

`position` (initial/medial/final) als **Lehrtafel-Rolle** der Allograph-
Form benennen — also: *wo Loth (oder eine vergleichbare Vorlage) diese
Form auf der Tafel zeigt*. Die Frage „welche Vorlage gilt für einen
konkreten Slot im Lauftext" ist eine separate Schicht, die in
[`orthographie-regeln.md`](../reference/orthographie-regeln.md)
beschrieben ist und vom geplanten Modul `core/orthography.py` (siehe
Vorschlag D) konsumiert wird.

„Allographe sind getrennte Glyphen" (§3, Folge-Festlegung) bleibt
unverändert gültig — präzisiert wird nur, *was* die Achse `position`
genau bezeichnet.

### Blast Radius bei Freigabe

- 3–5 Zeilen Prosa in `architektur.md` §3.
- Kein Code, kein Schema, keine Migration.
- Bereits umgesetzt im Plan dieses PRs: Klarstellungs-Kommentar in
  [`app/src/constants.ts`](../../app/src/constants.ts) über `KNOWN_GLYPHS`.

---

## Vorschlag B — `architektur.md` §2 und §4: systematische Bigramm-Extraktion aus Beispieltext

**Status:** größer, betrifft zwei Festlegungen. Diskussion offen.

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
[`orthographie-regeln.md`](../reference/orthographie-regeln.md)
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

### Verantwortung

Mappt einen Eingabetext (deutscher Text in moderner oder vor-1901-
Schreibung) auf eine Sequenz von Glyph-Slots der Form
`(glyph_key, allograph_role, segmentation_context)`. Konsumiert die
Regeln aus [`orthographie-regeln.md`](../reference/orthographie-regeln.md)
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
- [`orthographie-regeln.md`](../reference/orthographie-regeln.md)
  (Quelle der Anlässe für die Vorschläge in dieser Datei)
- [`CLAUDE.md`](../../CLAUDE.md) — „do not re-litigate decisions"-Regel
  begründet, warum Änderungen an settled docs den Umweg über diese Datei
  nehmen.
