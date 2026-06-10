# Quellen- und Rechte-Policy

Begleitdokument zu [`architektur.md`](../concepts/architektur.md) und
[`naming-und-setup.md`](../concepts/naming-und-setup.md). Hält fest, *welches Quellmaterial
ins öffentliche Repo darf*, was nicht, und wie auf Originale verwiesen
wird — damit beim Öffentlich-Machen nichts nachträglich aufgerollt
werden muss.

*(Keine Rechtsberatung — Einordnung zur eigenen Entscheidung.)*

---

## 0. Leitprinzip

Geschützt ist die **Darstellung**, nicht das **Schriftsystem**.

Die genormte Kurrent vor 1900 (Duktus, Allographe, Ligatur-Einheiten) ist
ein historisches System und niemandes Eigentum. Geschützt ist immer nur
die konkrete *Ausgestaltung* einer Quelle (die Zeichnungen eines
modernen Lehrbuchs, ein bestimmter Scan, ein bestimmtes Vorlagenheft).

Daraus folgt die Trennung, die das ganze Dokument trägt:

| | Status | Konsequenz |
|---|---|---|
| Konkrete Tafeln/Zeichnungen/Satz einer Quelle | geschützter Ausdruck | **nicht ins Repo** |
| Das Kurrent-Formensystem als solches | historisch, gemeinfrei | frei modellierbar |
| **Eigene** Darstellung des Systems (`canonical`) | dein Copyright | Kern des Repos, frei lizenziert |

---

## 1. Moderne Lehrwerke (urheberrechtlich geschützt)

Diese Regeln gelten für **jedes** geschützte moderne Werk zur deutschen
Schreibschrift — Lehrbücher, Übungshefte, Vereinsmaterial, Grafiken von
Websites. Benannter Beispielfall ist Harald Süß, *Deutsche
Schreibschrift*: das Lehrbuch, mit dem der Projektautor die Schrift
gelernt hat — es taucht deshalb in Docs und Gesprächen oft als
Referenz auf, und genau darum braucht es die klare Grenze.

- Tafeln, Glyphenzeichnungen und Satz eines solchen Werks = geschützter
  Ausdruck. **Nicht** ins Repo — auch nicht als daraus extrahierte oder
  abgezeichnete Glyphenbilder.
- Privat damit lernen und **lokal** dagegen fitten = *Nutzung*, nicht
  *Verbreitung*. Die Grenze ist der öffentliche Commit des fremden
  Ausdrucks, nicht das Lernen daraus.
- Verweis erlaubt und erwünscht: als **bibliografische Referenz**
  (Autor, Titel, Auflage) in README/Quellen/Docs — Fakten und
  Bibliografie sind frei. Kein Scan, kein Auszug, kein Reprint
  der Tafeln.

### Der eigentliche Trennstrich: Norm vs. Fassung des Lehrwerks

Handabschrift wäscht Urheberrecht **nicht**. Eine selbst geschriebene
Seite, die erkennbar *die Tafel eines bestimmten Lehrwerks* ist (dessen
Auswahl, Anordnung, stilistische Eigenheiten — nur mit der Hand
nachgezogen), bleibt eine Kopie dieses Ausdrucks. Das Medium rettet
nichts.

Die entscheidende Frage ist nicht „abgeschrieben ja/nein", sondern:
**bildest du die Norm ab oder die konkrete Fassung der Norm aus einem
geschützten Werk?**

- Einzelne Standardformen in eigener, natürlicher Hand, als die
  *historische Norm* geschrieben → deine Darstellung eines gemeinfreien
  Systems. Unkritisch, auch wenn es „wie eine Kurrent-Tabelle aussieht".
- Das spezifische Layout, die Variantenauswahl oder die Komposition
  eines Lehrwerks nachgebaut → fremder Ausdruck. Nicht ins Repo.

Praktische Absicherung: Formen gegen eine **gemeinfreie** Quelle (§6)
gegenchecken, nicht gegen das moderne Lehrwerk. Damit ist nachweisbar,
dass die Formen die geteilte Norm sind, die auch das Lehrwerk nur
abbildet. Das Risiko skaliert mit dem Anteil fremder kreativer
Entscheidungen, den du mitnimmst — isolierte historische
Buchstabenformen sind nicht schützbar.

---

## 2. Was ins Repo darf

**Uneingeschränkt:**

- Das `canonical` Duktus-Template (§3 der Referenz) — **deine eigene
  Autorenleistung**: deine Darstellung eines gemeinfreien Systems.
  Nicht aus einer Quelle kopiert, sondern modelliert.
- Eigenhändig geschriebene Vorlagen + deren Scans/Fotos (z. B. `lesen`,
  `das` aus §9). Dein Copyright → unter Repo-Lizenz freigebbar.
- Abgeleitete Daten: Kontrollpunkte, Breitenprofile, Fit-Parameter,
  Statistik — sofern aus eigenhändigem oder gemeinfreiem Material.

**Nur mit passender Lizenz:**

- Historische Primärquellen vor ~1900, **explizit** als PD/CC0
  freigegeben (z. B. Wikimedia Commons PD-Tafeln, offen lizenzierte
  Archivdigitalisate, gemeinfreie Vorlagenhefte 18./19. Jh.,
  Hilmar Curas 1714).

**Nie:**

- Scans/Auszüge/abgezeichnete Tafeln aus urheberrechtlich geschützten
  Werken (Süß und vergleichbare moderne Lehrbücher).

---

## 3. Stolperstein: Scan ≠ automatisch frei (DE-Recht)

Historisch konnte ein originalgetreuer Scan einer **gemeinfreien**
2D-Vorlage in Deutschland ein eigenes Leistungsschutzrecht des
Digitalisierers tragen (§72 UrhG, ~50 Jahre; vgl. Reiss-Engelhorn-
Museen, BGH 2018). **Seit dem 07.06.2021 gilt §68 UrhG** (Umsetzung
Art. 14 DSM-RL): Vervielfältigungen gemeinfreier **visueller Werke**
genießen keine verwandten Schutzrechte mehr — der originalgetreue
Repro-Scan einer PD-Tafel ist damit selbst frei; Reiss-Engelhorn ist
insoweit überholt. Rest-Vorsicht bleibt bei Alt-Digitalisaten (Streit
um Vor-2021-Fälle) und bei **nicht** originalgetreuen Bearbeitungen
(eigene Schöpfungshöhe möglich).

Deshalb in dieser Reihenfolge bevorzugen:

1. **Eigene Hand** — eliminiert das Thema vollständig (empfohlen für den
   MVP, §8).
2. Quelle **explizit** als PD/CC0 ausgezeichnet.
3. **Eigenes Foto** eines gemeinfreien Originals (PD-Werk → dein Foto,
   du lizenzierst).

„Alt genug, also frei" greift zu kurz — die Freigabe des *Digitalisats*
muss separat stimmen.

---

## 4. Verlinken statt Einbinden

Originale werden **referenziert, nicht reproduziert**:

- Stabiler Link auf die Originalquelle (Archiv-Permalink, Commons-URL,
  Bibliografieeintrag), nicht die Datei im Repo.
- Lizenz der Quelle benennen (PD / CC0 / CC-BY … + Attribution wie
  gefordert).
- Bei eigener Hand: als solche kennzeichnen — das ist die stärkere
  README-Story („fitted against the author's own hand", inkl. GIF).

---

## 5. Repo-Mechanik

- **`DATA_PROVENANCE.md`** getrennt von der MIT-Code-Lizenz. Pro Sample:
  Herkunft · Lizenz · Attribution · Datum.
- Code: MIT (wie in Naming-Setup §3 entschieden).
- Daten/Samples: eigene Lizenzzeile je Eintrag — Code-Lizenz deckt
  Daten **nicht** automatisch ab.
- Gebündelte Drittanbieter-Assets im Frontend (Fonts etc.): Eintrag in
  `app/THIRD_PARTY_NOTICES.md` + Lizenztext unter `app/public/fonts/`
  (siehe [`style-guide.md`](../concepts/style-guide.md)) — die dritte
  Lizenz-Oberfläche neben Code (MIT) und `/data`.
- Faustregel vor jedem Commit: *Ist das mein Ausdruck oder der einer
  geschützten Quelle?* Im Zweifel → nicht committen, nur verlinken.

Dieses explizite Provenance-Handling ist zugleich das
„ich kenne die Trade-offs"-Portfolio-Signal aus dem Naming-Doc.

---

## 6. Konkrete gemeinfreie Quellen

**Variante 0 (Basis aller ersten Tests): Loth 1866.**
„Deutsche Kurrentschrift"-Tafel aus *Der Damen-Briefsteller*, 1866
(zugeschr. Johann Thomas Loth), Wikimedia Commons.

- Bevorzugt die **SVG**-Fassung (`File:Deutsche_Kurrentschrift.svg`):
  eine **Neuzeichnung**, kein originalgetreues Reproduktionsfoto → der
  §72-Stolperstein (§3) greift konzeptionell nicht; die Nachzeichnung
  ist vom Vektorisierer ohne eigenen Rechtsvorbehalt unter
  PD-Kennzeichnung publiziert und erreicht als originalgetreue
  Vektorisierung keine eigene Schöpfungshöhe. Original 1866 gemeinfrei
  → committen *und* auf der Website zeigen erlaubt (mit Attribution).
  Das ebenfalls committete `chart.jpg` (Pipeline-Input) ist die
  Commons-Reproduktion desselben PD-Originals — seit §68 UrhG ohne
  eigenes Reproduktionsschutzrecht (§3).
- Inhaltlich passend: enthält Alphabet, Umlaute **und** die
  Ligatur-Einheiten (ch, ck, th, sch, sz, st) → überschneidet sich
  weitgehend mit dem „geschlossenen Satz" aus Referenz §4 (sz ≙ ß,
  st ≙ ſt; tz und qu fehlen auf der Tafel und brauchen eine andere
  PD-Referenz oder eigene Autorenleistung). 1866 liegt in der Normform-
  Scheibe (Naming-Setup §1).
- **Wichtig:** Die Tafel liefert nur **Geometrie**, keinen Duktus
  (Strichreihenfolge/Absetzpunkte). Das ist die §2-Aufteilung der
  Referenz — der Duktus-Prior ist deine Eigenleistung *über* dieser
  PD-Geometrie, nicht aus dem Bild ableitbar.

**Reserve / Vergleichshände:**

- *Das Buch der Schrift*, Karl Faulmann, 1880 — hochaufgelöste
  PD-Scans auf Commons; zweite Vergleichshand.
- *Keferstein*-Tafeln (Commons) — Kurrent nach Wortposition
  (initial/medial/final) getrennt → direkt für die `position`-Achse
  aus Referenz §3, falls gegen PD validiert werden soll.

Jede genutzte Quelle erhält einen `SOURCE.md`-Eintrag (Permalink,
Lizenz, Attribution, Abrufdatum) — siehe separates Repo-Layout-Dokument.

---

## 7. Transkribierte Korpora — eigene Lizenz, oft gemischt

Dritte Quellenkategorie neben „PD-Tafel" und „eigene Hand". Liefert
*viele Instanzen pro Glyph* → Statistik-Schicht (Referenz §6). Andere
Lizenzform: kein PD, sondern je Teilkorpus eigene CC-Lizenz, Bildrechte
teils separat vom Transkriptionsrecht.

**Primär: Zenodo „HTR Set German Kurrent 19th c."**
(DOI 10.5281/zenodo.17252677, Myriam Gantner, TU Wien, v1.0.0).
9.317 Zeilen, PNG + PageXML. **Gemischte Lizenz:**

- Deutsches-Textarchiv-Anteil: **CC BY 4.0** (frei, auch kommerziell,
  nur Attribution).
- Digitale-Schriftkunde-Anteil: Bilder CC0, Transkriptionen
  **CC BY-NC-SA 4.0**.
- Senatsprotokoll-Anteil (`ubtue/Ground-Truth`): Lizenz separat im
  Quell-Repo prüfen — nicht auf der Zenodo-Seite genannt.

**Zwei harte Regeln daraus:**

1. **Skript-Download ≠ lizenzfrei.** Per Skript vom Permalink laden
   statt zu vendorn ist gute Praxis (Größe, gepinnte DOI-Version,
   reproduzierbare Provenienz) — ändert aber **keine** Lizenzpflicht.
   Nutzung ist Nutzung, egal wo die Bytes liegen. Gleiches Prinzip wie
   §1 (Mechanismus wäscht keine Rechte).
2. **NC-SA kollidiert mit MIT.** Was zu einem *committeten*
   Repo-Artefakt wird (extrahierte Statistik), darf **nur** aus dem
   CC-BY-4.0- und CC0-Anteil stammen. Der NC-SA-Teil bleibt lokal /
   look-only und speist keine committeten Outputs — sonst Widerspruch
   zur MIT-Code-Lizenz (NC verbietet, was MIT erlaubt; SA zwingt
   Fremdlizenz auf).

*Graubereich (keine Rechtsberatung):* reine statistische Maße sind
eher Messung/Faktum als kreatives Derivat; das verarbeitete Material
(Bild + Transkription) ist aber lizenziert. Risiko sitzt ganz im
NC-SA-Subkorpus → dort Vorsicht, beim CC-BY-Teil unkritisch mit
Attribution.

**Multi-Hand-Hinweis:** Korpus = viele Hände. Statistik (§6) *pro
Hand/Dokument* rechnen, nicht über alle Hände mitteln — sonst mischt
Varianten-Differenz (Konsistenz-Prior, Referenz §7) in die
Per-Instanz-Streuung.

---

## 8. Quellen (rechtlicher Rahmen)

- §72 UrhG (Lichtbilder) / Urteil Reiss-Engelhorn-Museen (BGH 2018) zur
  Schutzfähigkeit originalgetreuer Reproduktionsfotos.
- Wikimedia Commons: Lizenz-/PD-Kennzeichnung pro Datei maßgeblich.
  Loth-1866-Tafel dort als PD-old / Public Domain Mark 1.0.
- Hilmar Curas, preußische Normschrift 1714 — gemeinfrei (vgl.
  Naming-Setup §1).
- Zenodo DOI 10.5281/zenodo.17252677 — Lizenz laut Datensatz:
  CC BY 4.0 (DTA-Teil) bzw. CC BY-NC-SA 4.0 (Digitale-Schriftkunde-
  Transkriptionen) bzw. CC0 (deren Bilder).
- CC BY 4.0 / CC BY-NC-SA 4.0 / CC0 Lizenztexte — creativecommons.org.
