# Quellen- und Rechte-Policy

> **Status (2026-08-03): bindend.** Rechte-Policy (§0–§4, §6–§8); Änderung
> nur über eine neue Entscheidung.
> Ausnahme §5 „Open-Core-Absicherung“: die dort aufgezählte technische
> Gating-Oberfläche ist Ist-Stand und muss bei jeder Änderung an Admin-Gates
> auf Lese-Endpunkten, am Origin-Gate davor (`api/origin_gate.py`,
> `infra/cloudflare/`), an den gitignorten Bench-Fixtures oder an committeten
> gerenderten Artefakten nachgezogen werden.

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
- **Copyleft-Wortlisten als Serverdaten** (Autor-Entscheid 2026-08-30):
  Die Lesart-Seite braucht ein Wörterbuch, und die freien deutschen sind
  Copyleft (igerman98: GPL 2/3; Wiktionary: CC BY-SA). Was die Lizenz
  hergibt: Nutzung ohne Bedingungen, Pflichten erst bei *Weitergabe* der
  Liste. „Nicht ins Repo, aber auf der Seite" ist dabei rechtlich kein
  Unterschied — beides ist öffentlich; der Unterschied ist, *was* beim
  Besucher ankommt. Darum: die Liste liegt nur in der geteilten DB
  (`lesart_forms`), geladen über die Admin-API, und der öffentliche
  Endpunkt `GET /lesarten?text=` gibt je Anfrage eine Handvoll Wörter
  zurück, nie die Liste — keine Weitergabe, kein Bundle, kein Image-
  Inhalt. Der MIT-Code ist kein abgeleitetes Werk der Liste. Nicht
  gewählt: die Frequenzliste (Rechtekette unklar, `frequencywords-2018/
  SOURCE.md` — Konsultationsquelle, „kein öffentlicher Endpunkt" bleibt)
  und NC-Listen (Leipzig, DeReWo, SUBTLEX — NC bleibt ausgeschlossen).
  Ablage: [datenablage.md §1](datenablage.md), Quelle:
  `data/corpora/igerman98/SOURCE.md`.

Dieses explizite Provenance-Handling ist zugleich das
„ich kenne die Trade-offs"-Portfolio-Signal aus dem Naming-Doc.

### Open-Core-Absicherung (technisch)

Das README reserviert die **gelernten Daten** (autorierte Duktus-
Templates, Laufformen, Vorkommens-Statistik — der DB-Inhalt) ausdrücklich
außerhalb der MIT-Lizenz. Damit ein Repo-Klon nicht trotzdem „perfekt
losschreiben" kann, gilt technisch:

- **Bench-Fixtures bleiben gitignored** (`tools/glyphbench/fixtures/`,
  `tools/wordbench/fixtures/` — sie enthalten die autorierten Templates;
  Regeneration braucht DB-Zugang). Ernte-Artefakte
  (`laufform_*.json`, Harvest-Reports) werden nie committet.
- **Jeder API-Read, der den Bestand trägt, ist admin-gegatet — und die
  Trennlinie ist getestet.** `tests/test_api_public_surface.py`
  klassifiziert JEDE GET-Route der API als öffentlich oder reserviert
  (eine Route in keiner der beiden Listen lässt den Test fallen), fordert
  für jede öffentliche eine Antwort ohne Berechtigung und für jede
  reservierte den 401 — seit 2026-08-28 ist das der eine Mechanismus,
  auf dem der Vorbehalt technisch ruht, denn die Crawler-Politik der
  Seite ist offen ([`crawler-richtlinie.md`](crawler-richtlinie.md) §2).
  Reserviert: `GET /sources/{id}/templates/{glyph_key}` (vollständiges
  Template inkl. Roh-Stylus-Pfad) und der ungecachte Stapel-Read
  `GET /sources/{id}/templates/quality` → `list[TemplateQualityOut]`
  (der **gespeicherte** Score direkt aus `templates.trace_meta["quality"]`
  über `TemplateRepository.list_quality`, per JSON-Index statt der dichten
  `pixel_anchors`/`half_widths_px` — das ganze Alphabet in einer Anfrage,
  0,145 s für 80 Zeilen gegenüber 0,44 s für EINE Glyphe über das
  nachrechnende `/{glyph_key}/quality`); seit 2026-08-28 zusätzlich die
  Vorkommen (`/instances`, `/pair-instances`, `/word-instances` — gemessene
  Fits über den autorierten Templates, der Referenzsatz der
  Tintenfolger-Kampagne), die Bbox-Zeilen (`/bboxes`, `/bboxes/{key}` —
  die Crop-Arbeit des Wizards, die keine Neuberechnung zurückbringt), die
  Paar-Overrides (`/pairs`, `/pairs/{l}/{r}` — autorierte
  Verbindungsgeometrie) und das Schreiberregister (`/hands`,
  `/hands/{id}`). Das Gate selbst (`api.auth.require_admin`) stempelt
  jede gegatete Antwort mit `Cache-Control: private, no-store` — kein
  reservierter Read kann in einem geteilten Cache landen, und keine Route
  kann den Header vergessen. Öffentlich bleibt, was die
  öffentlichen Seiten brauchen: die Template-Summaries ohne Geometrie
  (`/templates`), die Verfügbarkeits-Flags (`/bboxes/status`), die
  PD-Tafel und ihre Crops (`/chart`, `/bboxes/{key}/crop`), die
  Wort-Specimens, deren Sidecar ohnehin im öffentlichen Repo liegt
  (`/word-samples`), die aus dem Repo geseedete Quiz-Wortbank und die
  `/write`-Renders.
- **Die Statistik-Schicht liest ausschließlich admin-gegatet:**
  `GET /hands/{hand_id}/aggregates` und
  `GET /hands/{hand_id}/pair-aggregates` (samt ihren
  `…/rebuild`-Endpunkten, v0.22.0) verlangen `require_admin` — ein
  Aggregat ist gelernte Geometrie und damit derselbe reservierte Bestand
  wie die autorierten Templates, auch wenn der Read nichts rendert.
- **Der ganze Eigenhand-Zweig ist admin-gegatet, Lesen eingeschlossen:**
  `/eigenhand/*` — Bestand, Bögen, Layouts, das stehende Setup und seit
  Migration `0025` die STREIFENBILDER selbst
  (`GET /eigenhand/strips/{hand}/{strip}/{fassung}`, wahlweise auf ein Wort
  zugeschnitten). Ein Bestand ist das Inventar des reservierten Datensatzes,
  ein Streifen ist er selbst; die Bild-Antworten tragen zusätzlich
  `Cache-Control: private, no-store`, damit sie in keinem geteilten Cache
  und auf keiner fremden Platte liegen bleiben. Ins Repo kommen sie nie
  (datenablage.md §1); ihr Master bleibt das private Archiv
  ([eigenhand-erfassung.md §7.2, §8.1](../proposals/eigenhand-erfassung.md)).
- **Öffentliche `/write`-Payloads sind bewusste Produkt-Oberfläche**
  (die SPA rendert clientseitig): gerenderte Geometrie, unter dem
  README-Nutzungsvorbehalt + Cloudflare-Schutz. Die Seite selbst ist seit
  2026-08-28 offen (`ai-train=yes`); die eine abweichende Zeile liegt auf
  dem API-Host: `api.kurrentschrift.ink/robots.txt` (`api/routers/seo.py`)
  erlaubt alles, trägt aber `ai-train=no`, weil die komponierten Züge aus
  dem vorbehaltenen Bestand abgeleitet sind — abrufen und zitieren ja,
  Trainingsmaterial nein ([`crawler-richtlinie.md`](crawler-richtlinie.md)
  §2). Wer massenhaft abgreift, verletzt den Vorbehalt — das ist die
  rechtliche, nicht die technische Grenze.
- **Bekannte, akzeptierte Ausnahme:** `tests/fixtures/compose_golden.json.gz`
  pinnt die Composer-Parität mit 11 gerenderten Wörtern. Die Datei enthält
  je Wort die Render-Payloads der benutzten Glyphen — `anchors_template`,
  `half_widths_template`, `centerlines_template`, `outline_paths`,
  `template_guides`, `entry`/`exit_pt`, `advance` —, zusammen **27
  glyph_keys** der Sütterlin-Grundvorlage (`G M S a b c ch ck d e g h i k l
  longs n o r s t tz u ue v w z`, gemessen 2026-09-02). Das ist
  strukturgleich mit der öffentlichen Antwort von
  `GET /sources/{id}/write/glyphs` und geht damit nicht über die bewusst
  offene Produkt-Oberfläche hinaus — liegt aber, anders als jene, offline im
  Klon. Die frühere Beschreibung „keine Templates, nicht generalisierbar"
  war sachlich falsch und ist hier durch den gemessenen Stand ersetzt; die
  Entscheidung selbst bleibt unangetastet. Folgeaufgabe unverändert: das
  Golden auf synthetische Test-Templates umstellen, dann verschwindet auch
  das.
- **Bekannte, akzeptierte Ausnahme in der ÖFFENTLICHEN HISTORIE**
  (Entscheid des Autors 2026-09-02): `.design-sync/previews/_writtenGlyphData.ts`
  — Blob `4e02e1a7be720d34c3f161c17afe821a1032df1b`, 32 219 Bytes,
  hinzugefügt am 2026-06-20 mit Commit `84c6332` (PR #108), am 2026-07-31
  von PR #254 („Harden the open-core moat") nur aus HEAD entfernt, **nie
  aus der Historie**. Die Datei trägt die Diagnose-Payloads zweier
  Templates (`eMedial`, `tMedial` in der Vor-`0017`-Benennung) mit
  `skeleton_polyline_px`, `half_widths_px`, `anchors` und `outline` — also
  genau die Route, die heute als reserviert gepinnt ist. Das Repository ist
  seit 2026-05-19 öffentlich, der Blob damit in jedem Klon per
  `git show 84c6332:…` lesbar.

  **Warum angenommen und nicht gepurgt:** Ein Purge
  (`git filter-repo` + Force-Push) schriebe die Historie eines
  ÖFFENTLICHEN `main` um und macht die Kopie trotzdem nicht ungeschehen —
  jeder bestehende Klon und jeder Fork behält sie, ein Purge senkt nur die
  Auffindbarkeit. Dem stünde der Preis gegenüber, dass jede fremde Kopie
  des Repos unbrauchbar wird. Inhaltlich geht es um zwei von rund 80
  Glyphen in einer längst überholten Geometrie. Die rechtliche Schranke
  bleibt unverändert der Vorbehalt im README („License") — der gilt
  unabhängig davon, ob Bytes irgendwo abrufbar sind; technisch verhindert
  wird nur die WIEDERHOLUNG.
- **Ebenfalls angenommen** (Entscheid des Autors 2026-09-03, dieselbe
  Begründung wie oben): die handnachgefahrenen Kanonischen des ersten
  Prototyps aus der Zeit vor der Datenbank, hinzugefügt am 2026-05-20 mit
  Commit `4dc98c7`, aus HEAD verschwunden am 2026-05-22 mit `9365b65`
  (Umzug `/mvp/` → `/core/` + Postgres). Der Entscheid gilt den drei
  DATEIEN `e-medial_v0.json`, `s-final_v0.json`, `s-medial_v0.json` und
  damit allen ihren Fassungen — je vier Revisionen, zusammen zwölf Blobs.
  Namentlich per Hash gepinnt sind sie in `tests/test_reserved_history.py`;
  dort steht die maßgebliche Liste, nicht hier, damit die beiden nicht
  auseinanderlaufen können.

  Das Audit vom 2026-09-02 hatte sie als „0,9–1,1 KB große Hand-Seeds"
  beiseitegelegt; nachgemessen reichen sie bis über 50 KB mit je 50
  `pixel_anchors` und `half_widths_px` — dieselbe Klasse autorierter
  Geometrie wie der Blob darüber, kein Stummel. Aufgefallen ist die
  Fehlangabe erst, als das Nachweis-Netz unten sie als INHALT statt als
  Dateigröße prüfte; und die vier Revisionen je Datei wurden erst sichtbar,
  als es den Zahlenlauf schlüsselnah statt global suchte.

  **Das Nachweis-Netz** dazu ist `tests/test_reserved_history.py`: Es geht
  alle je committeten Blobs außerhalb der Code-Bäume durch und meldet
  jeden, der einen Render-Payload trägt (Payload-Schlüssel **plus** einen
  Zahlenlauf DIREKT dahinter — eine bloße Erwähnung des Feldnamens in Prosa
  oder in einem Generator-Skript ist ausdrücklich erlaubt). Schlüsselnah
  (Umkreis 300 Bytes) statt global, und die Mindest-Zahlenzahl steht **je
  Schlüssel**, weil die Schemata sich unterscheiden: `InstanceItem.anchors`
  hat `min_length` 4, also acht Koordinaten, während ein
  `WordInstanceItem.strokes` schon mit einem Zwei-Punkt-Zug schema-gültig ist
  — vier Zahlen. Zwischen zwei Einträgen brechen JSON-Schlüssel jeden
  längeren Lauf, deshalb ließe eine globale 40-Zahlen-Schwelle kleine
  Vorkommens-Dumps durch, während sie behauptet, sie abzudecken. Die
  Schlüsselliste deckt auch die Render-Geometrie mit ab (`silhouette_px`,
  `outline_polygon(s)`, `fitted_outline_px` aus `core/pipeline.py` und
  `core/fit.py`). Die oben genannten
  Blobs sind per Hash gepinnt, alles andere lässt den Test rot werden.
  Gepinnt wird per Blob-Hash und nicht per Pfad: Eine Pfad-Ausnahme ließe
  einen NEUEN Dump unter demselben Pfad durch — genau den Fall, den das
  Netz verhindern soll. Der Zahlenlauf erlaubt ausdrücklich auch Klammern
  zwischen den Zahlen, denn dichte Geometrie steht ebenso oft verschachtelt
  (`anchors_template: [[x, y], …]`) wie flach; ein reines Komma-Muster bräche
  an jedem `],[` und ließe einen Dump aus lauter Koordinatenpaaren durch.
  `data/` wird mitgeprüft und ist ausdrücklich KEIN Code-Baum — dort läge
  eine autorierte Payload am naheliegendsten. Die Schlüsselliste deckt
  ALLE hier vorbehaltenen Wire-Formen ab, nicht nur die Tafel-Templates:
  Templates und ihre Renders (`skeleton_polyline`, `anchors*`,
  `half_widths*`, `centerlines*`, `outline_paths`), die Vorkommen
  (`anchors`, `half_widths`, `strokes`) und die Hand-Aggregate
  (`cluster_center`, `connector_center`) — gemessen ohne einen einzigen
  Fehlalarm über die gesamte Historie. Und der Test **überspringt sich
  nicht selbst**: nur ein fehlendes `git` (oder ein flacher Klon) gilt als
  „hier nicht prüfbar", jeder Fehler von `rev-list`/`cat-file` macht ihn
  rot — ein Wächter, der bei eigenen Fehlern schweigt, hielte CI grün,
  ohne je hingesehen zu haben.
- **Seit 2026-09-02 liegt eine Schicht DAVOR: das Origin-Geheimnis.** Alle
  bisherigen Punkte beschreiben, was die API einem Aufrufer antwortet. Sie
  galten aber nur, solange man die API überhaupt nur über den Edge erreicht —
  und beide Cloud-Run-Dienste stehen mit `ingress=all` im Netz, die rohe
  `*.run.app`-Adresse antwortete also an Cloudflare vorbei: ohne
  Rate-Limiting-Regel, ohne WAF, ohne Cache. Eine Transform-Rule stempelt
  jetzt `X-Origin-Secret` auf jeden Request, den Cloudflare für
  `api.kurrentschrift.ink` weiterreicht (der Apex-Worker vor dem Admin-Weg
  stempelt selbst — ein Worker-Subrequest umgeht die Regeln der eigenen Zone,
  [`infra/cloudflare/`](../../infra/cloudflare/README.md)), und
  `api/origin_gate.py` beantwortet alles andere mit **403** — vor dem Limiter,
  vor `require_admin`, vor jeder DB-Abfrage. Das ändert an der öffentlich/reserviert-Trennung NICHTS (der
  Header sagt nur „durch die Vordertür", nicht wer da kommt); es sorgt dafür,
  dass die Trennung überhaupt an der einzigen Stelle greift, an der sie
  gemessen wird. Ausgenommen bleiben `/health` (sonst schlägt jeder Deploy-
  Smoke geschlossen fehl, er probt die `run.app`-Tag-URL) und `/seo-proxy/…`
  (Crawler-Pfad; Details und Rollout in
  [`frontend-stack.md`](frontend-stack.md) §5). Ohne gesetzte
  `ORIGIN_SECRET`-Env ist die Prüfung aus — das ist der Rollback.
- Ein öffentlicher Datensatz entsteht nur als **bewusster
  Ziel-7-Release** (architektur.md §17, eigene Lizenz, Zenodo) — nie
  implizit über Repo oder API.

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
