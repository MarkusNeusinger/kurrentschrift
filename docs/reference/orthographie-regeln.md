# Orthographie-Regeln (Kurrent, ca. 1850–1941)

Sammlung typischer Lese- und Schreibregeln der deutschen Kurrentschrift
des 19. und frühen 20. Jahrhunderts. Geltungsbereich: ca. 1850 bis
zur Umstellung auf Lateinschrift 1941.

Diese Datei katalogisiert Regeln, die später vom geplanten
Text→Template-Mapping-Modul `core/orthography.py` (M4+, siehe
[`mvp-roadmap.md`](../concepts/mvp-roadmap.md)) konsumiert werden. Sie
sind **kein** Bestandteil des Glyph-Schemas und ändern die
Lehrtafel-Templates (`(glyph, position, variant)` aus
[`architektur.md`](../concepts/architektur.md) §3) **nicht**.

Quellenhinweis: die Regeln sind seit Generationen in deutschen
Schreiblehrbüchern und Lese-Hilfen codifiziert (z. B. Süß, *Deutsche
Schreibschrift lesen und schreiben*; Grun, *Leseschlüssel zu unserer
alten Schrift*). Es werden hier ausschließlich die Regeln selbst in
eigener Formulierung wiedergegeben — keine Übernahme fremder Prosa, keine
Scans oder redrawn Glyphen (siehe [Quellen- und
Rechte-Policy](quellen-und-rechte.md) und `CLAUDE.md`).

---

## 1. s-Allographe (ſ und s)

Die Kurrentschrift kennt zwei Formen für den Laut `s`: das **lange ſ**
und das **runde s**. Sie sind im Schema getrennte Glyphen
([`architektur.md`](../concepts/architektur.md) §3, „Allographe sind
getrennte Glyphen"). Auf der Lehrtafel von Loth 1866 erscheint ſ in
medialer Position, das runde s in finaler Position — das ist die
**Lehrtafel-Rolle**, nicht die einzige zulässige Text-Position.

### 1.1 Grundregel

- **ſ** steht wortintern und am Silbenanfang innerhalb des Wortes.
- **s** (rund) steht am Wortende.

Beispiele: `leſen`, `Haus`, `ſein`.

### 1.2 Sonderfall A — Rund-s an Morphem-/Silbengrenze in Komposita

Im Inneren eines zusammengesetzten oder abgeleiteten Wortes steht am
Silbenschluss **Rund-s** statt ſ, wenn es das Ende einer
Bestandteilseinheit markiert und die folgende Silbe mit einem
Konsonanten beginnt. Operativ gemeint sind Komposita und Ableitungen,
in denen das Rund-s eine Morphem- oder Silbengrenze innerhalb des
Wortes sichtbar macht.

Beispiele: `Aus-flug`, `Aus-ſpruch`, `Haus-thür`, `häus-lich`.

Implikation fürs Mapping: eine naive Längen-Heuristik („s am Wortende →
Rund-s, sonst ſ") reicht nicht. Voraussetzung ist eine Morphem- oder
mindestens Silbenanalyse der Eingabe.

### 1.3 Sonderfall B — Rund-s vor ausgefallenem h

Älterer Schreibgebrauch: wenn ein `h` nach dem `s` elidiert wurde, steht
ebenfalls Rund-s statt ſ.

Beispiel: `Aus-nahm` für (heutiges) `Ausnehmen`.

### 1.4 Konsequenz für das Schema

Es gibt weiterhin nur **eine** Rund-s-Vorlage und **eine** Lang-ſ-Vorlage
pro Hand — der Ductus selbst ändert sich an der Morphemgrenze nicht. Die
Auswahl, welche Vorlage für einen Text-Slot gilt, ist eine Regel-Schicht
(M4+), kein zusätzliches Template.

---

## 2. Geschlossener Ligatur-Satz

Bestimmte Buchstabenpaare werden in der Kurrentschrift als
**eigenständige Lehreinheiten** geschrieben, nicht als verbundene
Einzelbuchstaben. Sie sind in [`architektur.md`](../concepts/architektur.md)
§4 als „Ausnahme — geschlossener Satz gelehrter Ligatur-Einheiten"
fixiert: erste-Klasse-Bibliothekseinträge mit eigenem Ductus, nicht
durch `exit→entry`-Verkettung generiert.

Der Satz: `ch · ck · tz · ſt · qu · ß`.

`ß` ist genaugenommen eine ſ+s-Ligatur (langes ſ + rundes s) und folgt
historisch derselben Logik wie die übrigen Einträge.

---

## 3. Verwechselbare Buchstabengruppen (Lesefallen)

Keine Regel, sondern Hinweis für die Erkennungs-Closed-Loop in
[`architektur.md`](../concepts/architektur.md) §6.2. Typische
Verwechslungspaare in flüchtiger Schrift:

- `n` / `u` — bei zügiger Schrift formgleich; nur Kontext entscheidet.
- `D` / `u` — der kleine Bogen über `D` und der spitze Fuß bei `u`
  liefern manchmal die einzigen Unterscheidungsmerkmale.
- `B` / `V` — beide mit ähnlicher Schleifen-Topologie.
- `L`, `K`, `R` sowie `N`, `M` — als Verwechslungs-Cluster bekannt.

Diese Hinweise sind **keine** Vorlagen-Trennungen, sondern Anker für die
spätere Closed-Loop-Validierung („sieht plausibel aus, ist aber
topologisch falsch").

---

## 4. Schriftmischung (Mischschriften)

Fremd- und Eigennamen wurden in deutschsprachigen Texten häufig in
**lateinischer Schrift** inmitten von Kurrent gesetzt — vor allem in
Drucken, gelegentlich auch in Handschriften des späten 19. und frühen
20. Jahrhunderts.

Bekannte Sonderfälle innerhalb des Wortes:

- `r` aus der lateinischen Schrift kann ein `n` ersetzen.
- Die Ligatur aus `s` und `z` (Lateinschrift) erscheint statt einer
  Kurrent-Folge.

Im MVP-Scope ([`mvp-roadmap.md`](../concepts/mvp-roadmap.md) §MVP-Scope)
nicht abgedeckt. Hier nur als bekannte Limitierung dokumentiert; die
spätere Pipeline muss Mischschrift erkennen können, bevor sie Templates
zuweist.

---

## 5. Rechtschreibung vor 1901

Vor der orthographischen Konferenz von 1901 gab es in den
deutschsprachigen Ländern keine gemeinsamen verbindlichen
Rechtschreibregeln. Aus dieser Zeit stammen Schreibungen, die heute
unüblich oder unverständlich wirken (z. B. `Thür`, `Theil`). Beim
Text→Template-Mapping sind solche Formen Eingabe-seitig zu erwarten und
zu akzeptieren; sie sind keine Schreibfehler.

---

## 6. Ältere Buchstabenformen (vor ca. 1850)

In Schriftstücken vor ca. 1850 tauchen vereinzelt **ältere Glyphformen**
auf, die in der hier behandelten Periode ungebräuchlich sind. Beispiele:
ein `e`, das wie `r` aussieht; ein `G` mit eigener Ausprägung; ein
„Mittel-/Unter-H" mit Bogen statt Aufstrich. Diese Formen bilden keine
neue Regel-Klasse, sondern erweitern bei Bedarf den
Allograph-Satz — als zusätzliche `variant`-Werte im Schema oder als
eigene Glyph-Einträge, je nachdem ob die Topologie strukturell abweicht
oder nicht ([`architektur.md`](../concepts/architektur.md) §3, „Form-
varianten sind eigene Templates, nicht Auslenkung").

---

## 7. Verhältnis zum Lehrtafel-Template-Schema

Die Regeln aus §1 (Rund-s an Morphemgrenze) und §5 (vor-1901-Schreibung)
sind der Anlass, warum `glyphs.position` ([`architektur.md`](../concepts/architektur.md)
§3) **nicht** als Text-Position interpretiert werden darf, sondern als
Lehrtafel-Rolle der Allograph-Form. Die Abbildung Text-Slot → Template
ist eine separate Schicht und gehört genau hier — in eine
maschinenlesbare Encodierung dieser Datei.

Für Vorschläge zur Schärfung dieses Punkts in `architektur.md` siehe
[`planaenderungen.md`](../proposals/planaenderungen.md).

---

## Querverweise

- [`architektur.md`](../concepts/architektur.md) §3 (Schema,
  Allograph-Trennung), §4 (Ligatur-Ausnahme), §6 (Qualitätspipeline,
  insb. Closed-Loop)
- [`mvp-roadmap.md`](../concepts/mvp-roadmap.md) §MVP-Scope (Ligaturen
  und Großbuchstaben außerhalb des MVP)
- [`planaenderungen.md`](../proposals/planaenderungen.md) (Vorschläge zur
  Anpassung der Konzept-Docs, die sich aus dieser Regel-Sammlung ergeben)
- [`quellen-und-rechte.md`](quellen-und-rechte.md) (keine Übernahme
  fremder Prosa oder redrawn Glyphen)
