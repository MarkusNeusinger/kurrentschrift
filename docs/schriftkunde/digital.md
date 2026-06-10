# Kurrent digital — Unicode, Fonts, Transkription

Faktenblatt zur digitalen Repräsentation: Welche Zeichen haben
Codepoints, was ist Font-Sache, wie transkribiert man. Alle Angaben
quellenbelegt, Strittiges markiert. Stand: 2026-06-10.

## Unicode-Lage

- **Kurrent ist keine eigene Unicode-Schrift.** Kurrenttexte werden mit
  den normalen lateinischen Codepoints erfasst; das Schriftbild liefert
  der Font. Nur Zusatzzeichen ohne Codepoint liegen per Konvention in
  der Private Use Area (UNZ 1/MUFI, s. u.)
  ([Wikipedia: BfdS](https://de.wikipedia.org/wiki/Bund_f%C3%BCr_deutsche_Schrift_und_Sprache)).
- **Langes ſ = U+017F** (Latin Extended-A, seit Unicode 1.1/1993).
  Wichtig für Suche und Normalisierung: Uppercase-Mapping ist S,
  Kompatibilitätsdekomposition ist s — Case-Folding/NFKC führen ſ und s
  zusammen
  ([Wikipedia: Langes s](https://de.wikipedia.org/wiki/Langes_s),
  [compart: U+017F](https://www.compart.com/en/unicode/U+017F)).
  Das runde s ist das normale s (U+0073); Ersatzregel: wo ſ nicht
  darstellbar ist, steht s.
- **ß = U+00DF** (Latin-1 Supplement, seit 1.1); das **große ẞ =
  U+1E9E** kam mit Unicode 5.1 (2008) und ist seit 2017 Teil der
  amtlichen Rechtschreibung
  ([compart: U+00DF](https://www.compart.com/en/unicode/U+00DF),
  [Wikipedia: Großes ß](https://de.wikipedia.org/wiki/Gro%C3%9Fes_%C3%9F)).
- **Ligaturen ch/ck/tz haben keine Codepoints** — und bekommen keine:
  das Unicode-FAQ erklärt Ligaturbildung zur Font-Angelegenheit („No
  more will be encoded in any circumstances"); praktisch laufen sie
  über OpenType-Features oder PUA-Belegungen. U+FB05 (ſt) existiert nur
  aus Kompatibilitätsgründen und ist nicht zur aktiven Verwendung
  gedacht; U+200D (ZWJ) kann in Plain Text eine Ligatur *anfordern*
  ([Unicode-FAQ: Ligatures](https://www.unicode.org/faq/ligature_digraph.html),
  [Unicode Core Spec Kap. 23.2](https://www.unicode.org/versions/Unicode15.0.0/ch23.pdf),
  [Wikipedia: Langes s](https://de.wikipedia.org/wiki/Langes_s)).
- Sonderzeichen mit Codepoint: Doppelbindestrich **U+2E40** (Unicode
  7.0, eigens für Transkriptionen alter deutscher Texte), Nasalstrich
  als kombinierender Überstrich **U+0305**, Pfennigzeichen **U+20B0** —
  Details in [zahlen-und-zeichen.md](zahlen-und-zeichen.md).

**Projektbezug:** Genau deshalb gilt im Schema „Schriftzeichen sind
Daten" ([sprachregelung.md §2](../reference/sprachregelung.md)): der
Glyph-Key `ſt` ist der Plain-String aus U+017F + t, kein
Presentation-Form-Codepoint; die Ligatur als *Form* ist ein eigener
Library-Eintrag ([architektur.md §4](../concepts/architektur.md)).

## PUA-Normen und Fonts

- **UNZ 1** (BfdS, Erstausgabe 2008; erweitert als UNZ 1-2D mit
  Schreibschrift-Zusatzzeichen, 2013): belegt fehlende
  Ligaturen/Zusatzzeichen in der Private Use Area, als Teilmenge der
  MUFI-Belegung; Referenzfont MainzerFraktur (kostenlos)
  ([Wikipedia: BfdS](https://de.wikipedia.org/wiki/Bund_f%C3%BCr_deutsche_Schrift_und_Sprache),
  [bfds.de: Normung](https://www.bfds.de/bund-fuer-deutsche-schrift-und-sprache-e-v/normung-von-sonderzeichen-unicode/)).
- **MUFI** (Medieval Unicode Font Initiative, seit 2001): koordiniert
  die PUA-Belegung mediävistischer Sonderzeichen; Character
  Recommendation v4.0 (2015) mit 1512 Codepoints
  ([skaldic project](https://skaldic.org/m.php?p=doc&i=965)).
- **Freie Kurrent-Fonts:** Peter Wiegel bietet mehrere Kurrent-Fonts mit
  ſ/s und Ligaturen an (18th Century Kurrent, Greifswalder Deutsche
  Schrift u. a.); die Originalseite deklariert pauschal „Freeware",
  die OFL-Angabe stammt nur von Aggregatoren — **vor einer Einbindung
  Lizenz im Einzelfall klären**
  ([peter-wiegel.de](https://www.peter-wiegel.de/Fonts/index.html);
  Aggregator-Angabe: [1001fonts](https://www.1001fonts.com/wiegel-kurrent-font.html)).
  Das im Repo gebündelte GL-GermanCursive ist separat geregelt
  ([style-guide.md](../concepts/style-guide.md),
  `app/THIRD_PARTY_NOTICES.md`).

## Transkriptionspraxis (ſ → s oder nicht?)

- **Transkribus** schreibt keine Regel vor: ſ darf als s normalisiert
  oder formgetreu als ſ (U+017F) erfasst werden — entscheidend ist
  Konsistenz im Ground Truth; Ligaturen werden in Einzelbuchstaben
  aufgelöst
  ([Transkribus: Data Preparation](https://help.transkribus.org/data-preparation)).
- **adfontes (UZH)** normalisiert konsequent: ſ → s, ß → ss (Schweizer
  Tastatur), u/v nach Lautwert, übergeschriebene Zeichen als
  nachgestellter Vokal
  ([adfontes: Transkriptionsregeln](https://www.adfontes.uzh.ch/tutorium/schriften-lesen/transkriptionsregeln)).
- **Projektlinie:** unsere Glyph-Keys sind formgetreu (ſ ≠ s, eigene
  Allographe per [architektur.md §3](../concepts/architektur.md));
  die Lesetext-Schicht folgt
  [orthographie-regeln.md](orthographie-regeln.md).

## Nicht belastbar belegt

Ob U+017F schon in Unicode 1.0 (1991) enthalten war (Age-Daten nennen
1.1); die konkreten PUA-Codepoints einzelner UNZ-/MUFI-Ligaturen
(Normblatt nicht zeichengenau ausgewertet).
