# Freigabe-Maschine 2026-09-19 — Stände, Auslieferungs-Zeiger, Regression je Hand, Rollback

> **Status (2026-09-19): offen.** Nichts davon ist gebaut — kein Schema,
> keine Route, kein Werkzeug. Das Doc ist Schritt 1 des Phase-5-Gleises
> ([`admin-redesign.md`](admin-redesign.md) §15.3) und der Auftrag aus dem
> Autor-Entscheid Q24 (i) vom 2026-09-18: das Zielbild JETZT, vor dem
> Schema-PR, damit das Varianten-Band (Q19 a) und die Hand-Vorschau (Q22 a)
> passend geschnitten werden. Wird ein Teil gebaut, wechselt der Status im
> selben PR auf `teil-umgesetzt` — Kopfzeile hier und Status-Zelle in
> [`../index.md`](../index.md).
>
> **Was vorgeschlagen ist.** Ein **Stand** ist ein vollständiger,
> create-only Satz der Laufform EINER Hand unter EINER Varianten-Nummer;
> sein Kopf ist das Änderungsprotokoll der Applies (§4.1, §4.4). **Band:**
> `hands.laufform_variant` ist die Basis, Stand-Nummer = Basis + Index, 100
> je Hand, nie wiederverwendet, null DDL auf `templates` (§4.2). Ein Apply
> kopiert-dann-fügt-ein, statt zu überschreiben (§4.3). Der
> **Auslieferungs-Zeiger** ist ein anhängendes Protokoll, aufgelöst als
> Quelle → Hand → jüngste Zeile — nicht je Schrift, weil das Quiz bei 1922
> bleibt (§5.1). Öffentlich ist genau der ausgelieferte Stand, sonst nichts
> ≥ 100; dazu ein zweites, bisher ungenanntes Leck in der öffentlichen
> Template-Liste (§3 Zeile 6, §5.2). Randcache: die Auslieferungs-Nummer
> als vom Server geprüfter URL-Stempel (§5.3). Regression je Hand: die Platte am
> eingefrorenen Lineal, die Eigenhand OHNE Kopfzahl (§6). Rollback = eine
> angehängte Zeile; das Archiv bleibt create-only und ist nicht mehr der
> Rollback (§7). Der Admin zeigt Zahlen, Stände und Protokoll — keine Marke,
> kein Schalter; ausliefern bleibt Terminal- und Autor-Akt (§8).
>
> **Was offen ist.** Noch fünf der sechs Rückfragen an den Autor (§10): FM1
> Paare im Stand · FM2 Feder · FM4 blinder Durchgang · FM5 Randcache · FM6
> zwei Platten-Hände in einer Schrift. **FM3 Rückhaltemenge ist am
> 2026-09-20 entschieden: (b)**, zwei getrennte Mengen — gezogen wird nicht
> mehr vor der Ernte, sondern ist gezogen, sobald der Autor den Schlüssel
> setzt (§10 FM3). Bau-Reihenfolge und die zwei harten Zwänge: §11. Jede Aussage über den heutigen Code ist am 2026-09-19 an
> `origin/main` gelesen (§3).

## 1 Anlass

**Leitsatz 2 des Autors** (2026-09-18, [`admin-redesign.md`](admin-redesign.md)
§4.5): die Eigenhand ist das Optimierungsziel — beliebig viele Beispiele,
dauerhaft wachsend, „bis das system sie perfekt schreiben kann"; die Platte
bleibt Maßstab und „so ok". Eine Hand, die dauerhaft wächst, wird nicht
einmal umgeschaltet, sondern immer wieder: neue Ernte → neuer Stand →
vergleichen → ausliefern, oder zurücknehmen. Der Rollenwechsel aus
[`../concepts/vision.md`](../concepts/vision.md) „Drei Rollen" ist damit
kein Schalter, sondern die ERSTE von vielen Auslieferungen.

Heute gibt es dafür nicht einmal ein Protokoll. Szenario S10
([`admin-redesign.md`](admin-redesign.md) §11) beschreibt den schlechten
Tag: falsches öffentliches Schriftbild → welcher Apply war es? Kein
Änderungsprotokoll → Restore des ganzen Archiv-Snapshots mit Rückfrage →
Caches → Re-Baseline. Die Maschine ersetzt diesen Tag durch eine
angehängte Zeile.

Entstanden ist das Doc aus drei unabhängigen Entwurfs-Skizzen
(Datenmodell · Freigabe-Sicherheit · der Tag des Autors) und einer
Gegenlesung jeder Code-Behauptung. Was übernommen und was verworfen
wurde: §9.

## 2 Die Maschine in einem Absatz

Heute schreibt jeder Apply ÜBER die Zeilen, mit denen die Seite schreibt.
Künftig schreibt ein Apply nie mehr über etwas drüber: er legt einen neuen
**Stand** an — einen vollständigen, nummerierten Satz der Laufform EINER
Hand, mit einem Protokoll-Kopf. Welcher Stand öffentlich schreibt, sagt der
**Auslieferungs-Zeiger**, und der ist selbst ein Protokoll: ausliefern
heißt eine Zeile anhängen, zurücknehmen heißt eine Zeile anhängen, die auf
einen älteren Stand zeigt. Gelöscht wird nie. Vor jeder Auslieferung wird
verglichen — je Hand mit dem, was für diese Hand gemessen werden DARF. Der
Admin zeigt Stände, Protokoll und die doktrinierten Zahlen; ausliefern
bleibt ein erklärter Akt des Autors am Rechner.

    Ernte → rebuild → Apply ──▶ Stand 203   (neu, create-only, nicht öffentlich)
                                   │  Vergleich mit dem ausgelieferten Stand 202 (§6)
                                   ▼
                   Auslieferung:  Zeiger-Zeile  „mn-suetterlin → 203"
                                   │  schlechter Tag?
                                   ▼
                   Rollback:      Zeiger-Zeile  „mn-suetterlin → 202"

**Zum Wort.** „Freigabe" heißt der ganze Zyklus. Den einzelnen Akt nennt
dieses Doc **Auslieferung**, weil „Freigabe" im Code schon vergeben ist: so
heißt das `approved`-Häkchen einer Paar-Übersteuerung
(`core/database/models.py::GlyphPair`).

## 3 Ist-Befund am Code (gelesen 2026-09-19)

| # | Befund | Wo | Folge für die Maschine |
|---|---|---|---|
| 1 | `templates` ist eindeutig über `(style_id, glyph, variant)` und `(style_id, glyph_key, variant)` — keine Hand, keine Versionsachse außer `variant`. Formvarianten belegen 0..n (Sütterlin Q und ü tragen 1 + 2); die Laufform ist die KONSTANTE `LAUFFORM_VARIANT = 100` | `core/database/models.py` | `variant` ist die einzige vorhandene create-only-Achse; Q19 (a) macht aus der Konstanten ein Datum der Hand |
| 2 | `apply-laufform` ist ein Upsert an Ort und Stelle auf `(style, glyph_key, 100)`. Der Bericht (angewandt mit `n_instances` und `laufform_dev_xh`, übersprungen mit Grund und Gate-Zahlen, ausgeschlossen) lebt nur in der HTTP-Antwort; dauerhaft bleibt allein `trace_meta.laufform`, und das überschreibt der nächste Apply | `api/routers/aggregates.py::apply_laufform` | S10 hat in den Daten keine Antwort — das Änderungsprotokoll ist eine Persistenz-Lücke, keine neue Rechnung |
| 3 | DREI Schreiber treffen Variante 100: der Apply, das manuelle `PUT …/templates/{key}/laufform` (baut den Stempel neu, ohne `hand_id`) und `DELETE …/laufform` | `api/routers/templates.py` | alle drei müssen Stand-Operationen werden, sonst bleibt eine Hintertür ins Ausgelieferte |
| 4 | `/write/word` liest drei Dinge: die Tafel-Zeilen (Variante 0), die freigegebenen Paar-Übersteuerungen — je SCHRIFT, Variante 0, ohne Hand — und die Zeilen `variant=LAUFFORM_VARIANT`. Fehlt einer Glyphe die Laufform-Zeile, schreibt die Tafel-Form | `api/routers/write.py::compose_word_payload`, `GlyphPairRepository.approved_for_pairs` | „was die Seite schreibt" ist mehr als die Laufform-Zeilen; ein Stand muss ein VOLLSTÄNDIGER Satz sein, sonst stuft ein Teil-Apply alle unberührten Glyphen still auf die Tafel zurück |
| 5 | Das öffentliche `GET …/write/glyphs?variant=` nimmt 0..999 und liefert, was dort liegt; die Einzel-Reads kennen nur Variante 0. Keine öffentliche Seite fragt eine Variante ≥ 100 — nur drei Admin-Flächen tun es, über die ÖFFENTLICHE Route | `api/routers/write.py`; `letters/LetterView.tsx`, `compare/GlyphComparison.tsx`, `letters/LandmarkPanel.tsx` | das Leck aus Q19; die Admin-Flächen ziehen auf eine reservierte Route um (§5.2) |
| 6 | **Ein zweites Leck, das Q19 nicht nennt:** das öffentliche `GET /sources/{id}/templates` listet JEDE Variante der Schrift mit `glyph_key`, `variant` und `advance` | `TemplateRepository.list_summaries`; PUBLIC in `tests/test_api_public_surface.py` | ein Eigenhand-Stand wäre mit Existenz und Vorschub öffentlich sichtbar, auch wenn `/write/glyphs` ihn ablehnt |
| 7 | `hands` trägt `id · style_id · label · era · note` — kein Band, keine Art. `sources.hand_id` gibt es seit Migration `0004`, im Seed ist es NULL (der Prod-Schritt V1 steht aus) | `core/database/models.py` | die Kette Quelle → Hand (§5.1) setzt V1 voraus |
| 8 | `glyph_pairs` ist eindeutig über `(style_id, left_key, right_key, variant)`. Eine schlichte Spalte `hand_id` (Q23 a) trennt zwei Hände NICHT: ihre Übersteuerungen desselben Paars kollidieren weiter | `core/database/models.py::GlyphPair` | der Schema-PR muss den Schlüssel um `hand_id` erweitern (§4.5) |
| 9 | Die gepoolte Feder liest die `half_widths` aller Templates mit `(style_id, provenance_source_id)` — OHNE Varianten-Filter. Eine Laufform-Zeile kopiert die Breiten ihrer Tafel-Zeile wörtlich und trägt deren Herkunft | `TemplateRepository.half_widths_for_source`, `api/rendering.py`, `build_laufform_canonical` | jeder aufbewahrte Stand gewichtet den Pool neu — eine stille Breitenänderung der öffentlichen Tafel (§4.5, FM2) |
| 10 | Prozess-Caches: Feder je `(style, source)`, Payload-Memo je Template-`id` + `updated_at`, TTL 600 s, je Prozess. Rand: jede `/write`-JSON-Antwort trägt `public, max-age=300, s-maxage=86400, stale-while-revalidate=604800`; die SVGs nur `private, max-age=300`. Einen Purge-Weg gibt es im Repo nicht. Vorbilder für einen Stempel gibt es zwei: `STATUS_CACHE` (30 s) und das `?v=`/`&t=` der Wortproben- und Admin-Reads | `api/rendering.py`, `api/http.py`, `app/src/lib/api/endpoints.ts` | neue Zeilen sind nie veraltet; veraltet ist der RAND — bis zu einem Tag, mit Revalidierung bis zu einer Woche (§5.3) |
| 11 | `tools/dbsnapshot` findet die zu sichernden `(glyph_key, variant)` über die öffentliche Liste aus Zeile 6 und liest dann je Zeile einmal admin-gegatet. `templates` ist PRIMARY. Der Restore ist ein Ganz-Tabellen-Werkzeug: er verweigert die Live-URL, löscht mit `--replace` beide Primärtabellen und lädt `glyph_pairs` gar nicht zurück | `tools/dbsnapshot/fetch.py`, `restore.py` | das Archiv ist der Boden für Katastrophen, nicht der Rollback; und versteckt die öffentliche Liste künftig Stände, braucht der Snapshot ein reserviertes Inventar (§7) |
| 12 | Wer heute „100" liest: `tools/wordbench/fetch_fixtures.py` (`templates_laufform.json`), `tools/wordlab/cases.py`, `tools/eigenhand/pfad.py` (die Saat des Folgers) und zwei SPA-Konstanten | jeweils dort | jeder dieser Leser nennt künftig den Stand, den er gelesen hat (§6.3) |
| 13 | `rebuild` ersetzt die Aggregate einer Hand vollständig (`delete_for_hand`, dann Upsert) | `api/routers/aggregates.py` | ein Aggregat ist keine eingefrorene Basis — ein Stand hält fest, woraus er wurde (§4.4) |

Nebenbefund ohne Folge für den Entwurf: der Modul-Docstring von
`api/rendering.py` spricht von „bis zu drei Instanzen", `api/cloudbuild.yaml`
setzt `_MAX_INSTANCES: "1"` (und nennt `max=2` als nächsten Schritt). Die
Maschine verlässt sich auf keins von beiden (§5.3).

## 4 Der Stand

### 4.1 Was ein Stand ist

Ein **Stand** (voll: Laufform-Stand) ist die create-only, versionierte
Antwort auf die Frage „womit schreibt diese Hand?". Er besteht aus:

1. **einem vollständigen Satz Laufform-Zeilen EINER Hand** unter EINER
   Varianten-Nummer im Band dieser Hand (§4.2) — vollständig, weil
   `/write/word` eine fehlende Zeile als Tafel-Rückfall liest (§3, Zeile 4);
2. **den Paar-Übersteuerungen dieser Hand**, wie sie beim Anlegen
   freigegeben waren — als eingefrorene Kopie oder als festgehaltener
   Fingerabdruck, je nach FM1 (§4.5);
3. **der Feder**, mit der er geprüft und ausgeliefert wird (§4.5, FM2);
4. **dem Kopf**: woraus er wurde, was der Apply dazu sagte, wer ihn wann
   anlegte (§4.4).

Was ein Stand NICHT einfriert, sind die Tafel-Zeilen (Variante 0). Sie sind
die Handarbeit des Autors im Wizard, wirken wie heute sofort und gehören
keiner Hand. Der Kopf hält aber je Glyphe fest, gegen welche Tafel-Zeile
(`id` + `updated_at`) abgeleitet wurde — so ist „die Tafel hat sich seit
diesem Stand geändert" eine ablesbare Tatsache statt einer Vermutung.

Ein Stand wird nach dem Anlegen nie geändert und nie gelöscht.

### 4.2 Wo er lebt — das Band und die Nummer

**Ein Stand IST eine Varianten-Nummer in `templates`.** Keine neue Spalte,
keine neue Tabelle für Geometrie, kein zweiter Lesepfad: ein Schreiben
unter einer NEUEN Nummer ist ein schlichtes INSERT, und
`uq_template_style_key_variant` ist dann die create-only-Garantie — ein
zweites Schreiben unter dieselbe Nummer ist ein Constraint-Fehler statt
eines stillen Überschreibens.

**Der Bandschnitt** (der Auftrag aus Q19 a, „so, dass mehrere Stände Platz
haben"):

- `hands.laufform_variant` ist die **Band-Basis** `B` der Hand — ein Datum
  JE HAND, nicht je Rolle: bei der Registrierung bekommt eine Hand das
  nächste freie Hundert ihrer Schrift. Für Sütterlin ist das genau der
  Entscheid: Platte 100, Eigenhand 200. Eindeutig je Schrift
  (`UNIQUE (style_id, laufform_variant)`), denn Varianten-Nummern gelten je
  Schrift: die Platten-Hände von Sütterlin und Kurrent dürfen beide bei 100
  liegen.
- **Eine Schrift mit mehreren Platten-Händen** ist die Randbedingung aus
  Q25 (a) und bei Kurrent schon angelegt: `loth-1866` und
  `petzendorfer-1889` sind zwei Tafel-Quellen EINER Schrift, nach Migration
  `0012` ausdrücklich zwei Hände. Jede Platten-Hand bekommt ihr eigenes
  Hundert (100, 200), eine Eigenhand das nächste (300). Die 100 trägt die
  Hand, der die heutigen Variante-100-Zeilen gehören — sie lassen sich nicht
  umnummerieren (§5.4). Die Rolle sagt das geplante `hands.kind`, nie die
  Nummer.
- Das Band einer Hand ist `[B, B + 99]`. **Stand-Nummer = B + Index**, der
  Index zählt die Stände dieser Hand in der Reihenfolge ihres Entstehens:
  100, 101, 102 … für die Platte; 200, 201 … für die Eigenhand.
- **Was die Nummer sagt:** die Hunderterstelle die Hand (innerhalb der
  Schrift), der Rest das Alter. **Was sie nicht sagt:** ob der Stand je
  ausgeliefert wurde — 203 kann existieren und nie öffentlich gewesen sein.
  Das sagt allein der Zeiger (§5).
- **Nummern werden nie wiederverwendet.** Ein Protokoll, dessen Zeile
  „203" morgen auf andere Geometrie zeigt, ist keins.
- Unter der heutigen Obergrenze `le=999` der beiden `?variant=`-Reads passen
  neun Hände je Schrift mit je 100 Ständen. Heute sind es zwei.

**Reicht das?** Ein Stand entsteht höchstens je Ernte-Runde — mit der
Planungsannahme aus Q18 (2 Bögen je Woche) höchstens einer je Woche, also
rund zwei Jahre; beim wahrscheinlicheren Monatsrhythmus acht. Ein Apply,
der NICHTS ändert, legt keinen Stand an (§4.3), und Ausprobieren braucht
keinen: `GET /hands/{id}/aggregates` und `rebuild` sagen mit
`laufform_dev_xh` schon heute, was ein Apply schreiben WÜRDE. Ab Index 80
warnt die Apply-Antwort; das Anschlussband ist dann ein eigener Entscheid —
ausdrücklich nie die Wiederverwendung.

**Der heutige Bestand wird Stand 100**, indem ihn eine Kopf-Zeile BENENNT:
null DDL und null UPDATE auf `templates`, der einen Tabelle, die sich nicht
neu autorisieren lässt. Sein Kopf sagt ehrlich `origin: "bestand"` — die
Vorgeschichte dieser Zeilen (ein Gemisch aus manuellen PUTs und Applies)
ist nicht mehr rekonstruierbar.

### 4.3 Wie ein Stand entsteht

Ein Apply wird **kopieren-dann-einfügen**, in EINER Transaktion, und je
Hand SERIALISIERT: die Transaktion sperrt zuerst die Zeile der Hand
(`SELECT … FOR UPDATE`; auf SQLite, wo die HTTP-Suiten laufen, ein
No-op — dort schreibt ohnehin nur einer). „Höchster Index + 1" ist sonst
ein Wettlauf: zwei gleichzeitige Applies läsen dasselbe Maximum. Die
Eindeutigkeit des Kopfs (§4.4) bleibt die zweite Sicherung — der Verlierer
bekommt ein sauberes 409 und nie einen halb geschriebenen Stand.

1. nächste Nummer = Band-Basis + (höchster Index + 1);
2. der **Vorgänger** ist die laufende **Arbeitslinie** der Hand: ihr jüngster
   Stand, sofern er NACH der letzten Zeiger-Bewegung der Hand entstanden ist
   (oder die Hand noch nie ausgeliefert hat); sonst der AUSGELIEFERTE Stand;
   hat die Hand keinen Stand, beginnt der neue LEER. Ein ausdrückliches
   `?parent=` übersteuert das; Apply-Antwort und Kopf nennen den Vorgänger
   immer;
3. die Zeilen des Vorgängers werden per `INSERT … SELECT` unter die neue
   Nummer kopiert — außer den Keys, die dieser Apply gleich schreibt;
4. die angewandten Keys werden eingefügt (dieselbe Ableitung wie heute,
   `build_laufform_canonical`, dieselben Gates in derselben Reihenfolge);
5. die Kopf-Zeile (§4.4). Commit.

Das entspricht der heutigen Semantik — ein übersprungener Key behält, was
er hatte, und ein zweiter Teil-Apply lässt den ersten stehen —, nur ohne
dass dabei etwas verloren geht. Die Teil-Applies zählen: `apply-laufform`
nimmt eine Auswahl (`glyph_keys`), Buchstaben-Stapel nacheinander sind ein
vorgesehener Arbeitsfluss. Nach einem Rollback erbt trotzdem nichts vom
zurückgenommenen Stand — er entstand VOR der Zeiger-Bewegung. Eine
verworfene Zwischenfassung, die nie ausgeliefert war, verlässt man
ausdrücklich mit `?parent=<ausgelieferter Stand>`; vergisst man es, steht
ihr vererbter Key im Vergleich als BEWEGT gegen den ausgelieferten Stand
(§6.2, Teil 3) — sichtbar. Die umgekehrte Regel (immer vom ausgelieferten
Stand kopieren) verlöre dagegen den ersten Stapel STILL: ein Key, der sich
nicht bewegt hat, fällt in keinem Vergleich auf.

- **Der erste Stand der Eigenhand beginnt leer, nie als Kopie der
  Platte.** Eine in das Eigenhand-Band kopierte Platten-Zeile wäre die
  „umbeschriftete Platten-Laufform", die [`admin-redesign.md`](admin-redesign.md)
  §6.6 und `vision.md` ausschließen. Glyphen ohne Eigenhand-Zeile fallen
  auf die TAFEL zurück; der Lücken-Chip aus §6.6 sagt es je Slot.
- **Ändert ein Apply nichts** (kein Key neu, keiner entfernt, jedes
  `laufform_dev_xh` = 0), entsteht kein Stand; die Antwort sagt das. Der
  Doppel-Apply aus einem veralteten Tab ist damit harmlos.
- **`PUT …/laufform` und `DELETE …/laufform` werden Stand-Operationen:**
  „Vorgänger mit diesem einen Key ersetzt" bzw. „… ohne diesen Key" (der
  gezielte Rückfall EINES Buchstabens auf die Tafel). Beide bekommen damit
  zum ersten Mal ein Protokoll.
- **Nichts schreibt je wieder in eine vergebene Nummer.**
  `TemplateRepository.upsert` BEKOMMT eine Sperre für Varianten ≥ 100 —
  heute hat es keine, und beide Schreiber (der Apply und `PUT …/laufform`)
  schreiben dort per Upsert; der Stand-Schreiber benutzt INSERT. In Python ausdrückbar, wie die Phase-0-Regel es verlangt
  (die HTTP-Suiten laufen auf SQLite).
- **Die Eigner-Regel wird zur Band-Regel.** Ein Apply schreibt nur in das
  Band SEINER Hand, und der Vorgänger gehört derselben Hand. Der Guard aus
  Phase 0 (`_may_write_laufform`) bleibt als zweite Sicherung stehen —
  sein Docstring sieht genau diesen Übergang vor. Die Apply-Triage „eine
  abgeleitete Zeile ist nie ihre eigene Eingabe" prüft künftig `variant ≥
  100` statt `== 100`.

Das ist ein Umbau getesteter Schreibflüsse (Laufform-Übernahme, manueller
PUT); nach Q6 (b) erlaubt, wenn `tests/test_api_aggregates.py`,
`tests/test_laufform_row_gate.py` und `tests/test_api_admin_writes.py` im
selben PR mitziehen und der PR-Text den Umbau nennt.

### 4.4 Der Kopf — das Änderungsprotokoll der Applies

Eine Tabelle `laufform_stands` (Arbeitsname; die Bezeichner entscheidet der
Schema-PR), eine Zeile je Stand, ohne UPDATE-Pfad:

| Feld | Inhalt |
|---|---|
| `hand_id` · `style_id` · `variant` | wem der Stand gehört und unter welcher Nummer er liegt (`variant` eindeutig je Schrift) |
| `parent_variant` | der Vorgänger, aus dem kopiert wurde (NULL beim ersten) |
| `origin` | `apply` · `manual_put` · `manual_delete` · `bestand` |
| `report` | die Antwort des Applies WÖRTLICH (`AggregateApplyOut`): angewandt mit `n_instances`, `laufform_dev_xh`, `created`; übersprungen mit Grund, `spike_ratio`, `head_deviation`, Eigner; ausgeschlossen |
| `basis` | je Key: `n_instances`, `updated_at` des Aggregats, `id` + `updated_at` der Tafel-Zeile; dazu `min_occurrences`, `end_window`, `end_mode` und die Build-Kennung der API |
| `pen` | die Feder beim Anlegen (§4.5) |
| `pairs` | Anzahl und Fingerabdruck der freigegebenen Paar-Übersteuerungen der Hand (§4.5) |
| `created_at` · `note` | wann, und ein Satz warum |

Das ist keine neue Rechnung — jede dieser Zahlen wird heute schon
berechnet und mit der HTTP-Antwort weggeworfen.

**Die Zugehörigkeit ist strukturell, nicht nur eine Routen-Prüfung** — wie
`uq_template_style_key_variant` es für die Templates hält: der Kopf ist
eindeutig über `(style_id, variant)` UND über `(hand_id, style_id,
variant)`; auf den zweiten Schlüssel zeigen zusammengesetzte Fremdschlüssel
— `(hand_id, style_id, parent_variant)` im Kopf selbst und `(hand_id,
style_id, stand_variant)` sowie `… previous_variant` im Zeiger (§5.1). Ein
Vorgänger oder eine Auslieferung, die auf einen fehlenden Stand oder auf
den einer ANDEREN Hand zeigt, ist damit ein Constraint-Fehler — auch für
eine Migration, einen Restore oder einen späteren Repository-Aufrufer, die
an der Route vorbeischreiben.

### 4.5 Was am Stand hängt: Paar-Übersteuerungen und Feder

**Paar-Übersteuerungen (Q23 a).** Zwei Dinge sind zu sagen.

Erstens eine Berichtigung für den Schema-PR: `glyph_pairs.hand_id` als
schlichte Pflichtspalte trennt die Hände nicht (§3, Zeile 8). Der
Eindeutigkeits-Schlüssel muss `(style_id, hand_id, left_key, right_key,
variant)` werden, sonst kann die Eigenhand ein Paar nicht übersteuern, das
die Platte schon übersteuert.

Zweitens die Frage, ob ein Stand die Übersteuerungen BINDET. Eine
Übersteuerung ist Geometrie relativ zum Austritt des linken Buchstabens —
gezeichnet gegen die Buchstabenformen, die an dem Tag galten. Nimmt ein
Rollback die Buchstaben zurück und lässt die neuen Verbindungen stehen,
passen beide am schlechten Tag nicht mehr zusammen. Die Empfehlung ist
darum die eingefrorene Kopie: beim Anlegen des Stands werden die
freigegebenen Übersteuerungen der Hand unter `variant = Stand-Nummer`
kopiert (die Spalte gibt es; die Render-Strecke liest heute nur 0), und
`/write/word` liest die Paare des ausgelieferten Stands. Das gilt auch für
den GESÄTEN Stand 100, der nicht über den Kopier-Pfad entsteht (§4.2): der
PR, der (a) einführt, kopiert die freigegebenen Übersteuerungen der
Platten-Hand einmalig nach `variant = 100` — ein INSERT, kein UPDATE; die
Zeilen unter `variant = 0` bleiben der Arbeitssatz des Paar-Editors. Ohne
diese Kopie fände die Render-Strecke für Stand 100 keine Paare
(`approved_for_pairs` liest heute `variant=0`), und jede freigegebene
Übersteuerung verschwände still aus dem öffentlichen Wortbild. Der Preis: eine
Freigabe im Paar-Editor wirkt nicht mehr sofort öffentlich, sondern mit der
nächsten Auslieferung. Das ist eine Änderung im Arbeitsalltag des Autors —
darum FM1.

**Feder.** Befund 9 aus §3 wird mit der Maschine zum Fehler: heute zählt
die eine Laufform-Zeile je Glyphe im Pool schon als zweite Kopie der
Breiten ihrer Tafel-Zeile, und mit jedem aufbewahrten Stand käme eine
weitere dazu. Die saubere Regel —
gepoolt wird nur über AUTORISIERTE Zeilen (Variante < 100), denn eine
Laufform-Zeile trägt keine eigene Breiten-Information — ändert die heutige
öffentliche Strichstärke einmalig um ein Weniges, weil Variante 100 heute
mitzählt. Das ist eine erklärte Re-Baseline mit Vorher-/Nachher-Zahlen und
gehört darum dem Autor (FM2, Unterpunkt i).

Für die Eigenhand kommt dazu: ihre Quelle (`kind='eigenhand'`, Q20 a) ist
keine Tafel, von ihr stammt kein Template — ihr Pool ist LEER, und eine
Gleichzug-Schrift fiele auf die schwankenden Einzelbreiten je Glyphe
zurück, die der Pool gerade beseitigt. `vision.md` nennt als ersten Vorzug
der Eigenhand die „bekannte Feder statt rekonstruierter"; die gemessene
Feder-Halbbreite ist eine der vier Stufe-1-Anzeigen aus Q11 (b). Die
Empfehlung: **die Feder ist ein Datum des Stands** — der Kopf hält sie
fest, die Auslieferung schreibt mit ihr, ein Rollback nimmt auch sie
zurück (FM2, Unterpunkt ii).

## 5 Der Auslieferungs-Zeiger

### 5.1 Die Kette: Quelle → Hand → ausgelieferter Stand

Eine Tabelle `hand_deliveries` (Arbeitsname), **nur anhängend**:
`hand_id · style_id · delivery_no · stand_variant · previous_variant ·
kind` (`auslieferung` | `rollback`) `· reason` (Pflicht) `· evidence`
(Verweise: §14-Anker, humanbench-Runde, Snapshot-Stempel) `·
delivered_at`. **Der ausgelieferte Stand einer Hand ist die jüngste Zeile
dieser Hand**; dass er existiert und ihr gehört, hält der zusammengesetzte
Fremdschlüssel aus §4.4. `delivery_no` ist die **Auslieferungs-Nummer** —
der Stempel für den Randcache (§5.3): je Hand fortlaufend, eindeutig, nie
wiederverwendet, vergeben unter derselben Hand-Sperre wie eine
Stand-Nummer (§4.3). Bewusst eine EIGENE Spalte und nicht der generierte
Primärschlüssel: der Restore des Archivs verwirft generierte
Integer-Schlüssel (`tools/dbsnapshot/restore.py::rows_for`), und eine
Nummer, die der Randcache kennt, darf nach einem Restore nicht neu vergeben
werden (§7).

Die öffentlichen Routen sind quellen-gebunden
(`/sources/{source_id}/write/*`). Die Auflösung ist darum:

    Quelle ──sources.hand_id──▶ Hand ──jüngste Zeile──▶ Stand ──▶ Zeilen + Paare + Feder

Eine Quelle ohne registrierte Hand, oder deren Hand nichts ausgeliefert
hat, schreibt nur mit der Tafel — das ist genau das heutige Verhalten
einer Schrift ohne Variante-100-Zeilen. In einer Schrift mit zwei
Platten-Händen (§4.2) löst jede Tafel-Quelle auf IHRE Hand auf: eine
Platte, deren Hand nichts ausgeliefert hat, schreibt mit der Tafel allein,
nie mit der Laufform der anderen Platte. Was das für die Saat heißt: §5.4.

**Warum nicht EIN Zeiger je Schrift** (so stand es in zwei der drei
Skizzen):

- **Das Quiz bleibt bei 1922.** Der Autor hat am 2026-09-07 entschieden
  (`vision.md` „Was am Rollenwechsel hängt", Punkt 3), dass das Lese-Quiz
  seine Aufgaben vorerst weiter in den Formen der Platte stellt, während
  Hero, Federprobe und Übungsblatt wechseln. Nach dem Rollenwechsel
  liefern in EINER Schrift also ZWEI Hände zugleich aus. Ein Zeiger je
  Schrift kann das nicht halten.
- **Die API weiß nicht, welche Fläche fragt** — die URL muss sich
  unterscheiden. Ein öffentlicher `hand=`-Parameter ist verworfen
  ([`admin-redesign.md`](admin-redesign.md) §13); die Quelle steht schon in
  der URL. Das Quiz fragt weiter `suetterlin-1922`, die Schreib-Flächen
  fragen die Quelle der Eigenhand. `WrittenWord`, `WrittenGlyph` und
  `useWorksheetText` nehmen `sourceId` heute schon als Prop mit
  `CONFIG.sourceId` als Vorgabe — das ist die „Umschaltung über `CONFIG`",
  die Q22 (a) nennt.
- **Ehrliche Beschriftung.** `/write/word.svg` betitelt sein Bild mit
  `source.title`. Eine Eigenhand unter der Quellen-Id der Platte trüge
  deren Titel (im Seed „Sütterlin Ausgangsschrift (Leitfaden 1922)") — die
  Bildunterschriften-Lüge, die `vision.md` ausschließt.
- **Die Feder ist schon je Quelle** (`resolve_render_context`).

### 5.2 Was die öffentlichen Routen ausliefern dürfen

Der Satz aus [`admin-redesign.md`](admin-redesign.md) §6.6 — die
öffentliche Route lehnt jedes Band ≥ 100 ab, das nicht das der
ausgelieferten Hand ist — wird mit dem Zeiger SCHÄRFER: öffentlich ist
nicht das Band, sondern **genau der ausgelieferte Stand**. Liefert die
Eigenhand Stand 203 aus, ist ihr Kandidat 204 so unlesbar wie ein fremdes
Band.

| Read | heute | mit der Maschine |
|---|---|---|
| `…/write/word` · `word.svg` · Pfad-Formen | Variante 0 + Paare der Schrift + Variante 100 | Variante 0 + die Zeilen des ausgelieferten Stands der Hand der Quelle, dazu die Paare DIESER Hand (eingefroren oder laufend: FM1) und ihre Feder (FM2); ohne Hand oder Auslieferung nur Variante 0. Weiterhin parameterfrei |
| `…/write/glyphs?variant=` | 0..999, was dort liegt | < 100 immer (Formvarianten der Tafel); ≥ 100 nur GENAU die Nummer des ausgelieferten Stands dieser Quelle. Alles andere antwortet wie eine leere Variante — alle Keys in `missing` —, damit die Route nicht einmal verrät, dass es den Stand gibt |
| `GET /sources/{id}/templates` | jede Variante | Varianten < 100 und der ausgelieferte Stand; sonst nichts |
| **neu, öffentlich:** `GET /sources/{id}/write/delivery` | — | `{"delivery": <Auslieferungs-Nummer>}`, `STATUS_CACHE` (30 s) — nur der Stempel, keine Geometrie (§5.3) |
| **reserviert:** `GET /hands/{hand_id}/write/word?stand=` und `…/write/glyphs?stand=` | — | die Hand-Vorschau aus Q22 (a), um `stand` erweitert (Vorgabe: der jüngste Stand der Hand); `require_admin`, `private, no-store`, RESERVED. Die drei Admin-Flächen aus §3, Zeile 5 ziehen hierher um |
| **reserviert:** `GET /hands/{hand_id}/stands` · `…/deliveries` | — | Inventar und Protokoll; der Snapshot liest das Inventar (§7) |
| **Admin-Schreiben:** `POST /hands/{hand_id}/deliveries` | — | hängt EINE Zeile an; prüft, dass der Stand existiert, der Hand gehört und `reason` gesetzt ist |

**Tests, im selben PR wie die jeweilige Regel:** eine gesäte Zeile in einem
fremden Band kommt über keine öffentliche Route zurück; ein nicht
ausgelieferter Stand im EIGENEN Band ebenso wenig; die öffentliche Liste
zeigt beide nicht; `tests/test_api_public_surface.py` führt die neuen
Routen in der richtigen Klasse. `write-api.md` zieht im selben PR nach.

### 5.3 Caches — der Prozess ist harmlos, der Rand nicht

**Prozess.** Ein neuer Stand sind neue Zeilen mit neuen `id`s; der
Payload-Memo keyt auf `id` + `updated_at` und verfehlt sie von selbst. Eine
Zeiger-Bewegung schreibt gar keine Geometrie. `invalidate_pooled_style`
wird bei Auslieferung und Rollback trotzdem gerufen — es räumt die
Payloads des abgelösten Stands und die Feder-Caches, und es kostet nichts.
Der Zeiger selbst wird je Anfrage gelesen — ein indizierter SELECT neben
denen, die `/write/word` ohnehin macht (Quelle, Schrift, Tafel-Zeilen,
Paare, Laufform-Zeilen). Ein Memo kommt nur, wenn eine Messung es verlangt,
und dann mit der TTL der Stempel-Route: `invalidate_*` erreicht nur die
Instanz, die den Schreibvorgang sah.

**Rand.** Hier liegt das echte Risiko, und es ist asymmetrisch falsch
herum: mit `s-maxage=86400` erscheint eine Auslieferung irgendwann
innerhalb eines Tages — und ein ROLLBACK genauso langsam, obwohl er der
eine Akt ist, der sofort wirken muss. Vorschlag (FM5):

- Die Auslieferungs-Nummer wandert als `&v=<n>` in die URLs der SPA — ein
  neuer Cache-Schlüssel je Zeiger-Bewegung. Die SPA holt sie einmal je
  Seitenaufruf von der Stempel-Route (30 s). Eine Auslieferung und ein
  Rollback sind damit nach etwa einer Minute überall sichtbar.
- **Die Nummer der AUSLIEFERUNG, nicht die des Stands.** Ein Rollback auf
  202 bekäme sonst den alten Schlüssel `v=202` zurück, und ein veralteter
  Client könnte einen Schlüssel mit dem Inhalt eines anderen Stands füllen.
  Eine Auslieferungs-Nummer kommt nie wieder.
- **Der Server PRÜFT `v`.** Die Nummern sind vorhersagbar: wer heute
  `&v=<nächste Nummer>` fragt, legte sonst den HEUTIGEN Stand unter dem
  künftigen Schlüssel in den Rand, und die nächste Auslieferung bekäme für
  diese URL einen Tag lang das alte Bild. Darum: stimmt ein mitgeschicktes
  `v` nicht mit der aktuellen Auslieferungs-Nummer der Hand überein,
  antwortet die Route mit dem aktuellen Inhalt, aber `no-store` — ein
  fremder Schlüssel wird nie gefüllt. Der Zeiger ist je Anfrage ohnehin
  gelesen, die Prüfung kostet nichts; ein Test pinnt beide Richtungen
  (künftige und veraltete Nummer). Ohne `v` bleibt alles wie heute.
- Kein Cloudflare-Zugang im API-Image. Für die URLs OHNE Stempel —
  Assistenten, fremde Clients — bleibt der Rand bis zu einem Tag alt; nach
  einem Rollback wegen eines sichtbar falschen Schriftbilds ist ein
  manueller Purge ein Runbook-Schritt (Prod-berührend, mit Rückfrage).
- Nicht: ein kürzeres `s-maxage` — es besteuerte jeden Tag für einen Akt,
  der selten ist.

### 5.4 Auslieferung Nr. 0 und Nr. 1

**Nr. 0 — der Zeiger wird Datum, nichts ändert sich.** Die Migration legt
die Tabellen an, benennt den Bestand als Stand 100 der Platten-Hand, setzt
deren Band-Basis und hängt die erste Zeiger-Zeile an. Danach liest
`compose_word_payload` den Zeiger statt der Konstanten. **Beweis der
Byte-Gleichheit:** die Golden-Parity-Fixture bleibt unberührt (`compose.py`
kennt die Nummer nicht), und ein `/write/word`-Payload-Test pinnt die
Antwort vor und nach der Umstellung — auch für ein Wort mit freigegebener
Paar-Übersteuerung (§4.5). Voraussetzung ist der Prod-Schritt V1 — ohne
registrierte Platten-Hand findet die Kette keinen Stand.

**Wem der Bestand gehört,** liest die Saat je Schrift aus den Zeilen
selbst: aus dem Stempel `trace_meta.laufform.hand_id`, sonst aus der Hand
der Tafel-Quelle in `provenance_source_id`. Bytegleich ist Nr. 0 nur, wenn
JEDE Tafel-Quelle der Schrift auf diese eine Hand auflöst: heute schreibt
jede Quelle einer Schrift mit denselben Variante-100-Zeilen
(`compose_word_payload` liest je `style_id`), nach M1b nur noch die
Quellen der Eigner-Hand. Die Migration bricht darum mit klarer Meldung AB,
statt die Laufform still zu verlieren, wenn in einer Schrift mit
Variante-100-Zeilen (a) die Zeilen auf keine oder auf mehr als eine Hand
auflösen, oder (b) eine Tafel-Quelle keine oder eine ANDERE Hand nennt als
den Eigner — der Fall zweier Platten-Hände (FM6). Quellen anderer Art, die
nicht auf den Eigner auflösen (die Handschrift einer fremden Hand), zählt
die Meldung auf, ohne abzubrechen: sie schreiben nach M1b mit der Tafel
allein, und das ist gewollt — die Laufform, mit der sie heute schreiben,
gehört nicht ihrer Hand. `/verify-migrations` fährt den guten Fall und
jeden Abbruch-Fall.

**Nr. 1 — der erklärte Rollenwechsel.** Er ist der erste echte Zug der
Maschine und bleibt ein eigener Autor-Entscheid (`vision.md`,
[`eigenhand-erfassung.md`](eigenhand-erfassung.md) §2). Zwei Hälften:

1. **Daten:** die erste Zeiger-Zeile für `mn-suetterlin`. Ab diesem
   Augenblick beantwortet die Quelle der Eigenhand öffentlich `/write/*` —
   das ist der Moment, in dem die Eigenhand-Formen öffentlich lesbar
   werden, auch wenn noch keine Seite sie zeigt.
2. **Repo-PR + Deploy:** ein zweites Config-Datum für die Schreib-Flächen
   (Hero, Federprobe, Übungsblatt-Vorschrift); die Bildunterschriften aus
   der Liste in `vision.md` „Was am Rollenwechsel hängt"; die
   Beispiel-Links in `app/src/lib/seo/prerender.ts` und ein frisch
   gerendertes `app/prerender/`; der datierte §14-Eintrag. Das Quiz bleibt,
   wo es ist.

Ehrlich dazu: einen STAND nimmt man in einer Minute zurück; die ROLLE
zurückzunehmen ist ein Revert-PR mit Deploy, weil die Bildunterschriften
im Bundle liegen. Das ist richtig so — die Rolle wechselt einmal, die
Stände oft.

## 6 Regression je Hand — was vor einer Auslieferung gemessen wird

Zwei Hände, zwei verschiedene Fragen, mit Absicht verschieden beantwortet.
Die Regel, die für beide gilt, steht in `optimierungs-werkbank.md` §6 und
wird hier nicht bewegt: **ein Verlust sperrt die Auslieferung oder
begründet den Rollback; ein Gewinn am Lineal ist KEIN Aufnahmekriterium.**
So kam das n = 1-K in den Schreibweg.

### 6.1 Ein Stand der Platte

Das vorhandene Lineal, unverändert: `tools/wordbench` gegen die
eingefrorenen Wortproben der Platte, `core/word_metric.py` wird nicht
angefasst. Gemessen wird der Kandidat als A/B — zwei Fixture-Wurzeln mit
IDENTISCHEN Referenzen und identischem Code, die eine mit den Zeilen des
ausgelieferten Stands, die andere mit denen des Kandidaten (der
Fixture-Export bekommt dafür `--stand`; Wurzeln sind wie Snapshots
create-only). Wird der Kandidat ausgeliefert, ist das eine **erklärte
Re-Baseline der Kopfzahl** mit §14-Eintrag und Ledger-Zeile
([`../reference/qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md) §2).
Nach Leitsatz 2 wird das selten sein: die Platte wird nicht weiter
perfektioniert.

### 6.2 Ein Stand der Eigenhand

**Keine Kopfzahl.** [`eigenhand-erfassung.md`](eigenhand-erfassung.md) §12,
Prüfstein 2: Eigenhand-Material ist Trainingsmenge, kein Mess-Satz —
gemessen wird darüber nur mit separat eingefrorener, vorregistrierter
Teilmenge. Und gegen die PLATTEN-Wörter misst man eine Eigenhand auch
nicht: das mäße, wie nah der Autor an 1922 schreibt, und verrechnete zwei
Hände (`optimierungs-werkbank.md` §6). Der Vergleich Kandidat ↔
ausgelieferter Stand besteht darum aus fünf Teilen, von denen nur einer
Tinte liest:

1. **Deckung.** Über die Referenztexte aus Q17 (a) — `lesen`, `das`,
   `denen`, der Entwicklungssatz — und das Alphabet: welche Slots tragen
   im Kandidaten eine Laufform-Zeile, welche fallen auf die Tafel zurück,
   was kommt dazu, was geht verloren. Rein aus `shaping` × Stand-Keys;
   keine Tinte, kein Lineal. Verlorene Deckung ist nie still.
2. **Beleglage.** Aus dem Kopf: `n_instances` je Key gegen den Vorgänger,
   die Gate-Verdikte, jede Unterschreitung von
   `LAUFFORM_MIN_OCCURRENCES`, die nur per ausdrücklicher Autor-Aussage
   durchging.
3. **Formbewegung.** `laufform_dev_xh` je Key zwischen Kandidat und
   ausgeliefertem Stand — eine Differenz INNERHALB einer Hand, also
   erlaubt. Sie ist kein Gütemaß; sie sagt, wohin das Auge zuerst schauen
   soll.
4. **Rückhalte-Messung** — die einzige Zahl über Tinte: eine
   vorregistrierte, eingefrorene Teilmenge der Streifen, die NIE geerntet
   wird (also weder Aggregate noch Folger trainiert), mit §14-Eintrag VOR
   der ersten Zahl. Sie ist eine eigene Zahl je Hand, nie Kopfzahl, nie
   mit der Platten-Zahl verrechnet. Welches Lineal und welche Kennzahl,
   legt die Vorregistrierung fest, nicht dieses Doc. Solange es die
   Teilmenge nicht gibt, steht hier ehrlich „nicht gemessen" (FM3) — und
   sie muss VOR der ersten Ernte geschnitten werden, sonst hat ihr Material
   die Aggregate schon gespeist.
5. **Das Auge.** Ein blinder Durchgang nach dem humanbench-Muster
   ([`../reference/menschliche-bewertung.md`](../reference/menschliche-bewertung.md)):
   Kandidat gegen ausgelieferten Stand auf den Referenztexten, Analyseplan
   vorregistriert. Wie oft, ist FM4.

### 6.3 Die Platte bleibt der Maßstab — auch bei einer Eigenhand-Auslieferung

Eine Auslieferung der Eigenhand darf die Zahlen der Platte nicht bewegen.
Das gilt per Bauart — anderes Band, eigene Paare, eigene Quelle — und wird
trotzdem geprüft: ein frischer Fixture-Export der Platte nach der
Auslieferung trägt dieselben Tafel-, Laufform- und Paar-Zeilen und dieselbe
Feder wie der davor, und die Wortbench-Kopfzahl ist bit-identisch. (Der
`root_digest` allein taugt dafür nicht: er hasht JEDE Datei der Wurzel,
also auch, was ein Export an Zeitstempeln schreibt.) Eine bewegte
Platten-Zahl nach einer Eigenhand-Auslieferung ist ein Fehler der Maschine,
kein Befund über die Schrift.

Dazu eine Herkunfts-Regel für jeden Leser aus §3, Zeile 12: **wer einen
Stand liest, nennt ihn.** Die Fixture-Wurzel in ihrem Manifest, der Folger
in `pfade[].meta` (er sät heute mit der Laufform der Platte — mit welchem
Stand er für die Eigenhand sät, ist ein Knopf im Sinn von „gleicher Stack,
ein Knopf" und gehört in die Vorregistrierung seiner Runde), wordlab in
seinem Fall. Eine Mess-Runde pinnt genau einen Stand.

## 7 Änderungsprotokoll und Rollback

Das Protokoll sind die zwei anhängenden Tabellen: `laufform_stands` (jeder
Apply, jeder manuelle PUT oder DELETE — was, woraus, mit welchem Bericht)
und `hand_deliveries` (jede Zeiger-Bewegung — wohin, warum, mit welchem
Beleg). **S10 neu gespielt:**

1. „Letzte Änderungen" (§8) zeigt: Auslieferung `mn-suetterlin` 202 → 203
   am Soundsovielten, Grund im Klartext.
2. Der Vergleich 203 ↔ 202 nennt die bewegten Keys — beide Stände
   existieren, die Differenz ist jederzeit neu rechenbar.
3. Rollback = `POST …/deliveries` mit `stand=202`, `kind=rollback`,
   Pflicht-Grund. Kein DELETE, kein Restore. Wirksam nach etwa einer
   Minute (§5.3).
4. Stand 203 bleibt liegen und trägt in der Liste „zurückgenommen am …"
   (abgeleitet aus dem Protokoll, kein eigenes Feld). Der nächste Apply
   kopiert vom ausgelieferten Stand 202 und erbt nichts von 203: der
   entstand VOR der Zeiger-Bewegung und ist darum nicht mehr die
   Arbeitslinie (§4.3).
5. Keine Re-Baseline der Platte — ihre Zahlen haben sich nie bewegt.

**Archiv-Snapshots: create freely, never destroy — unverändert.** Die
Maschine nimmt dem Snapshot eine Aufgabe ab, für die er nie gebaut war (den
Rollback), und lässt ihm die eigentliche: den Boden für Katastrophen.
Konkret:

- ein Snapshot VOR jeder Migration (wie immer) und NACH jedem neuen Stand
  und jeder Auslieferung — damit das Archiv Stand und Protokoll hält.
  Die Leitplanke „vor allem, was Geometrie überschreiben kann" bleibt
  wörtlich stehen; ein create-only Apply überschreibt nichts mehr, aber die
  Regel wird nicht gelockert, bevor die Bauart sich bewährt hat;
- `tools/dbsnapshot/fetch.py` lernt die zwei Tabellen — mit M1b, denn ab
  dort trägt der Zeiger die Seite — und liest die Stände über das
  reservierte Inventar, weil die öffentliche Liste sie künftig versteckt
  (§5.2): das VOR dem ersten Stand jenseits von 100 (M2), sonst sichert der
  Snapshot weniger, als existiert;
- weil nie ein Stand gelöscht wird, schlägt der Schrumpf-Alarm
  (`check_plausible`) durch die Maschine nie an;
- **`restore.py` zieht mit den zwei Tabellen mit (M1b).** Heute lädt es nur
  `bboxes` und
  `templates` zurück und verwirft generierte Integer-Schlüssel (`rows_for`)
  — alles Übrige gilt dort als wieder ableitbar. Kopf und Zeiger sind es
  NICHT: ein Restore ohne sie brächte die Stand-Zeilen zurück, aber keine
  Auslieferung, und die Seite schriebe still nur noch mit der Tafel. Beide
  Tabellen werden darum Teil des Restores (die Eltern zuerst: Hand, Kopf,
  dann Zeiger) — unter FM1 (a) auch `glyph_pairs`, die er heute gar nicht
  zurücklädt —, `delivery_no` kommt als Datum unverändert mit (§5.1), und
  ein Rundlauf-Test gegen das Wegwerf-Postgres beweist es: Snapshot →
  Restore → derselbe ausgelieferte Stand, dieselbe Auslieferungs-Nummer,
  bytegleiche `/write/word`-Antwort;
- der Restore bleibt Ganz-Tabellen-Werkzeug, Prod-berührend, mit
  Rückfrage — und kein Teil des ROLLBACKS.

**Kosten.** Ein Snapshot liest je Template-Zeile einmal; 100 Stände × rund
60 Zeilen sind einige tausend Anfragen. Das sind Minuten, nicht Stunden, und
es wächst über Jahre. Gekürzt wird dann am LESEN (ein unveränderlicher
Stand muss nicht jedes Mal neu geholt werden), nie an der DB.

## 8 Was der Admin zeigt — und was Terminal- oder Autor-Akt bleibt

Gesetzt durch [`admin-redesign.md`](admin-redesign.md) §5.1, Idee 16 und
Q24 (a): **der Rollenwechsel bleibt außerhalb des Admins — keine Marke,
kein Schalter.**

**Der Admin zeigt** (alles lesend; jeder neue Read `require_admin`,
`private, no-store`, RESERVED):

- **den Bestandskopf, nur Zahlen:** Mindestbelegung (Glyphen unter 3
  angenommenen Fassungen), gewichtete Erstbeleg-Quote, Ampel-Anteil der
  Tintentreue. Kein „Bedingung erfüllt", kein Fortschrittsbalken auf ein
  Ziel — eine Zahl nennt der Autor nach dem ersten vollen Bogen-Satz;
- **„Ausgeliefert" je Hand:** Stand-Nummer, seit wann, mit welchem Grund —
  als Text;
- **die Stände-Liste je Hand**, jüngster zuerst: Datum, Notiz, Vorgänger,
  angewandt /
  übersprungen, dünnste und mittlere Belegzahl, bewegte Keys gegen den
  ausgelieferten Stand, dazu als beschriftete Chips „ausgeliefert",
  „zurückgenommen am …", „Tafel seitdem geändert: a, n". Kein Zustand lebt
  nur in Farbe oder Tooltip;
- **„Letzte Änderungen"** — Stände und Zeiger-Bewegungen in einer Zeitleiste:
  der „erste sichtbare Schritt", den S10 vermisst;
- **den Vergleichsstreifen:** die Referenztexte aus Q17 (a), nebeneinander
  als Tinte (der Streifen-Ausschnitt) · ausgelieferter Stand · Kandidat,
  über die reservierte Vorschau mit `?stand=`. Bilder mit Etikett, keine
  Zahl;
- **Übergabekarten** für die lokalen Schritte, mit Befehl und Parametern
  ([`admin-redesign.md`](admin-redesign.md) §5.1, Idee 11).

**Der Admin zeigt NICHT:** Bench- oder Rückhalte-Zahlen (Lineale bleiben im
Terminal, §13 dort), eine Marke oder ein „bereit", einen Ausliefern- oder
Rollback-Knopf, eine Snapshot-Checkbox (das verworfene Schein-Gate).

**Was wessen Akt ist:**

| Akt | Wo | Wer |
|---|---|---|
| Apply → neuer Stand | Browser, wie heute (`LaufformApplyDialog`) — jetzt gefahrlos, weil er nichts Öffentliches berührt | Autor oder KI-Runde |
| Vergleich: Deckung · Beleglage · Formbewegung | Terminal (`tools/freigabe vergleich`, Arbeitsname), lesend über die Admin-API | KI-Runde |
| Platten-A/B · Rückhalte-Messung · blinder Durchgang | Terminal, mit der Disziplin von `/verify-trace` (gleicher Stack, ein Knopf), Eintrag in §14 | KI-Runde misst, der Autor urteilt |
| Snapshot davor und danach | Terminal (`/dbsnapshot`) | KI-Runde |
| **Auslieferung · Rollback** | Terminal → `POST …/deliveries`. Prod-berührend: exakte Hand, Stand und Grund in der Sitzung nennen, Rückfrage, dann erst handeln | **der Autor entscheidet**, in jeder Sitzung neu |
| Rollenwechsel (Nr. 1) | Autor-Entscheid + Repo-PR + Deploy (§5.4) | der Autor |

## 9 Verworfen

**Alternativen zum Datenmodell.**

- **Eine Versionsspalte auf `templates` (`stand_id`).** Schreibt
  `uq_template_style_key_variant` um, dessen Kommentar sagt, dass zwei
  Zeilen mit gleichem Schlüssel jedes öffentliche `/write` mit 500
  beantworten; jeder `scalar_one_or_none`-Read und das Konfliktziel des
  Upserts müssten die Dimension lernen. Größter Schadensradius auf der
  einen Tabelle, die sich nicht neu autorisieren lässt — für eine Achse,
  die `variant` schon bietet. (Als `templates.hand_id` schon Q19 b.)
- **Eine eigene Tabelle für Stand-Zeilen** (Q19 c in neuem Gewand).
  `template_render_row` ist der EINE Zeilen-Bauer jedes Produktions-Renders,
  gepinnt von `tests/test_render_row.py` und der Golden-Fixture; ein zweiter
  Speicher hieße ein zweiter Lesepfad, und er wäre für das Archiv
  unsichtbar, bis `PRIMARY_TABLES` ihn kennt.
- **Ein Manifest mit hineinkopierter Geometrie.** Eine zweite Wahrheit für
  Geometrie neben `templates`, die `architektur.md` §3 einzeln hält.
- **Zur Renderzeit aus den Aggregaten ableiten** — als Q19 (d) schon nicht
  gewählt; dazu kommt §3, Zeile 13: `rebuild` ersetzt die Aggregate, ein
  darauf gebauter Stand wäre nicht eingefroren.
- **Dünne Stände** (nur die geänderten Keys, aufgelöst als „jüngste
  Variante ≤ Zeiger"). Bricht den Ein-Abfrage-Vertrag `get_many(style,
  keys, variant=…)`, auf dem Render-Strecke und Werkbank stehen, und macht
  „was schreibt Stand 203?" zu einer Rechnung statt zu einem SELECT.
- **Ein Flag `is_delivered` oder eine Schrift je Hand.** Das Flag hat
  keine Geschichte und keinen atomaren Wechsel; eine Schrift je Hand
  spaltete die Metrik, die je Schrift gilt, und verzweigte Feder-Pool und
  Fixture-Wurzeln.

**Alternativen zum Ablauf.**

- **Beim Überschreiben bleiben, das Archiv ist der Rollback.** Der Restore
  verweigert die Live-URL, löscht beide Primärtabellen und lädt die Paare
  nicht zurück — ein Ganz-DB-Werkzeug für einen Buchstaben; und es gibt
  kein Protokoll, WOHIN man zurück will. §13 des Admin-Plans hat die
  Checkbox „Snapshot liegt vor" schon als Schein-Gate verworfen: der
  Server weiß nichts vom Archiv.
- **Ein kürzeres `s-maxage`** — besteuert jeden Tag für einen seltenen Akt.
- **Eine Marke oder „Tore" für den Rollenwechsel** — Q24 (b) ist nicht
  gewählt; die Zahl nennt der Autor.
- **Eine Güte-Zahl der Eigenhand ohne Rückhaltemenge** — Prüfstein 2.

**Aus den drei Skizzen nicht übernommen.**

- **Ein Zeiger je Schrift** (Datenmodell) und **eine Ein-Zeilen-Tabelle,
  die EINE ausliefernde Hand nennt** (Freigabe-Sicherheit): scheitern am
  Quiz-Entscheid vom 2026-09-07 und an der Beschriftung (§5.1).
- **`hands.delivered_variant` als veränderliche Zahl** (Tag des Autors,
  Freigabe-Sicherheit): ein UPDATE verliert wer, wann und warum — genau
  das, wonach S10 fragt. Übernommen ist die Absicht („eine Zeile, ein
  Schreibvorgang"), als anhängendes Protokoll.
- **Der Knopf „Ausliefern" in `/admin/eigenhand`** (Tag des Autors):
  widerspricht Idee 16, „kein Schalter".
- **„Auslieferungen brauchen keinen Snapshot mehr"** (Tag des Autors): das
  Archiv ist die einzige Kopie außerhalb der DB; richtig ist nur, dass der
  Snapshot nicht mehr der ROLLBACK ist (§7).
- **Ein Band von 20 Plätzen mit Wiederverwendung des ältesten** (Tag des
  Autors): Wiederverwendung ist Überschreiben mit Umweg.
- **Der Stand-Stempel `?v=<Stand-Nummer>`** (Tag des Autors): die Idee ist
  übernommen, der Schlüssel nicht — ein Rollback brächte eine alte Nummer
  zurück (§5.3); gestempelt wird die Auslieferungs-Nummer, und der Server
  prüft sie.
- **„Sechs Hände erschöpfen die 0..999"** (Datenmodell): Varianten-Nummern
  gelten je Schrift, nicht global (§4.2).
- **Ein Purge-Token in der API** (als Frage in Freigabe-Sicherheit): kein
  Cloudflare-Zugang im Image; der Purge bleibt ein Runbook-Schritt (FM5).

**Übernommen,** damit die Herkunft steht: aus dem Datenmodell das Rückgrat
(Stand = Varianten-Nummer, Kopf-Tabelle, null DDL auf `templates`,
kopieren-dann-einfügen); aus der Freigabe-Sicherheit der Dreiklang „Zeilen
+ Paare + Feder", der Pool-Befund und die zweigeteilte Regression; aus dem
Tag des Autors die schlechten Tage (allen voran „er liefert aus und nichts
ändert sich"), der Vergleichsstreifen fürs Auge und der harmlose
Doppel-Apply.

## 10 Rückfragen-Katalog

Nur, was allein der Autor entscheiden kann. Jede Frage nennt, was ohne
Entscheid gilt. Was Engineering ist, steht darunter als Vorgabe.

**FM1 — Bindet ein Stand die Paar-Übersteuerungen?** *(blockiert: den
Schema-PR nicht, aber M2)*
Kontext: eine Übersteuerung ist gegen die Buchstabenformen ihres Tages
gezeichnet; heute wirkt eine Freigabe im Paar-Editor sofort öffentlich und
steht in keinem Protokoll (§4.5).
Optionen: (a) der Stand friert die freigegebenen Übersteuerungen der Hand
als Kopie ein — eine Editor-Freigabe wird erst mit der nächsten
Auslieferung öffentlich, ein Rollback nimmt Buchstaben UND Verbindungen
zurück; (b) Übersteuerungen bleiben je Hand sofort wirksam wie heute; jede
Freigabe schreibt eine Zeile ins selbe Protokoll, der Stand hält nur ihren
Fingerabdruck fest, und das Rollback-Runbook nennt „nach Stand N
freigegebene Paare zurücknehmen".
Empfehlung: (a) — ein Stand ist erst dann die ganze Antwort auf „womit
schreibt die Hand".
Ohne Entscheid: (b) — der heutige Arbeitsfluss bleibt, das Protokoll kommt
dazu.

**FM2 — Die Feder** *(blockiert: M2 für (i), die erste
Eigenhand-Auslieferung für (ii))*
Kontext: der Feder-Pool zählt Laufform-Zeilen mit; mit jedem aufbewahrten
Stand verschöbe sich die öffentliche Strichstärke still. Und die Quelle der
Eigenhand hat einen leeren Pool (§4.5).
Unterpunkt (i), der Pool der Platte — Optionen: (a) nur autorisierte Zeilen
(Variante < 100): EINE erklärte Re-Baseline jetzt, mit Vorher-/Nachher-Zahl
von Feder und Wortbench, danach für immer ruhig; (b) autorisierte Zeilen
plus der ausgelieferte Stand: heute bytegleich, aber die Feder bewegt sich
mit jeder Auslieferung ein wenig; (c) nichts tun: stille Drift mit jedem
Stand.
Unterpunkt (ii), die Feder der Eigenhand — Optionen: (a) die gemessene
eigene Feder-Halbbreite, festgehalten im Stand; (b) der Pool der Platte,
im Stand so beschriftet.
Empfehlung: (i) a — (c) ist mit der Maschine nicht vertretbar; (ii) a,
sobald die Zahl aus Stufe 1 (Q11 b) vorliegt, bis dahin (b) mit Etikett.
Ohne Entscheid: (i) b, (ii) b.

**FM3 — Die Rückhaltemenge der Eigenhand** *(**entschieden 2026-09-20: (b)**
— gegen die Empfehlung unten)*
Kontext: die einzige Zahl über Eigenhand-Tinte braucht Streifen, die nie
geerntet werden (§6.2, Teil 4). Leitsatz 1 verlangt für den Folger
dieselbe Art Teilmenge.
Optionen: (a) EINE Rückhaltemenge je Hand für beides — Folger-Training und
Freigabe —, zufällig aus den angenommenen Fassungen gezogen, Größe und
Ziehung im §14-Eintrag; (b) zwei getrennte Mengen; (c) keine — dann gibt
es über die Eigenhand nie eine Tinten-Zahl, und eine Auslieferung stützt
sich auf Deckung, Beleglage, Formbewegung und das Auge.
Empfehlung war (a); der Autor hat am 2026-09-20 (b) entschieden: **zwei
getrennte Mengen**, `holdout-follower` für die Folger-Arbeit und
`holdout-release` allein für die Freigabe-Prüfung einer Hand. Eine Menge
für beides hätte die Freigabe-Zahl an Material gemessen, an dem der Folger
zuvor gearbeitet hat.
Was daraus folgt — und den „VOR Schritt 4"-Zwang aus §11 zugleich auflöst:
die Ziehung hängt nicht mehr an der Ernte. Sie läuft über die Streifen des
eingefrorenen Plans, also ohne Netz und ohne eine einzige Fassung, ist ein
eigener Akt mit Schlüssel (`tools/eigenhand/training_set.py --draw`) und
wird ein zweites Mal verweigert. Doktrin:
[`eigenhand-erfassung.md`](eigenhand-erfassung.md) §7.5; Vorregistrierung:
[`../reference/messjournal.md`](../reference/messjournal.md) §14
„Trainingssatz `sep20`". Die Größe der beiden Mengen (je 0,20) steht dort
und ist mit der Ziehung eingefroren.
Was offen BLEIBT: die Rückhalte-MESSUNG selbst (M5) — wie die Zahl gegen
`holdout-release` gebildet wird, braucht ihre eigene Vorregistrierung am
Tag der ersten Zahl.

**FM4 — Wie oft der blinde Durchgang?** *(blockiert: M5)*
Optionen: (a) bei jeder Auslieferung; (b) verpflichtend bei der ERSTEN
Auslieferung einer Hand — dem Rollenwechsel —, danach auf Zuruf des
Autors; (c) nie verpflichtend.
Empfehlung: (b) — der Vergleichsstreifen im Admin ist das Auge des
Alltags, die blinde Runde das des Rollenwechsels. Ausdrücklich KEINE
Schwelle „ab so viel Formbewegung": das wäre die Marke durch die Hintertür.
Ohne Entscheid: (b).

**FM5 — Der Randcache** *(blockiert: M4)*
Kontext: ohne Maßnahme ist ein Rollback bis zu einem Tag unsichtbar (§5.3).
Optionen: (a) der Stempel in der URL plus ein manueller Purge als
Runbook-Schritt für die ungestempelten URLs; (b) ein Purge-Token im Secret
Manager, die API räumt selbst; (c) nichts — ein Tag Verzug wird hingenommen.
Empfehlung: (a).
Ohne Entscheid: (a) ohne den Purge-Schritt.

**FM6 — Eine Schrift mit zwei Platten-Händen** *(blockiert: M1 — aber nur,
wenn der Lese-Sweep den Fall zeigt; heute käme allein Kurrent in Frage)*
Kontext: Kurrent hat zwei Tafel-Quellen zweier Hände, aber — wie jede
Schrift — EINEN Template-Satz: die Buchstaben von der einen Tafel, die
Ziffern nach Migration `0012` von der anderen (ob sie schon autorisiert
sind, ist nicht gelesen). Heute schreiben beide Quellen mit denselben Variante-100-Zeilen; mit dem
Zeiger je Hand schriebe die Quelle, deren Hand Stand 100 NICHT gehört, ab
M1b nur noch mit der Tafel (§5.4). Ob Kurrent überhaupt
Variante-100-Zeilen trägt, ist nicht gelesen (§12).
Optionen: (a) zwei Hände, zwei Bänder; die zweite Platten-Quelle schreibt
ab Nr. 0 mit der Tafel allein — eine ERKLÄRTE Änderung ihres öffentlichen
Bilds, mit Vorher/Nachher im PR-Text; (b) beide Tafel-Quellen nennen
vorerst EINE Platten-Hand „der Schrift" — bytegleich, aber die
Registrierung sagt dann, was Migration `0012` ausdrücklich verneint („another
hand"); (c) die Schrift bleibt ungesät und liest weiter die Konstante, bis
sie gebaut wird — ein zweiter Lesepfad.
Empfehlung: (a) — dieselbe Ehrlichkeit der Beschriftung, die §5.1 für die
Eigenhand verlangt.
Ohne Entscheid: die Saat bricht ab, statt zu raten (§5.4). Zeigt der Sweep
den Fall nicht, ist die Frage gegenstandslos, bis eine zweite Tafel-Quelle
einer Schrift eine Hand bekommt.

### 10.1 Vorgaben, die ohne Rückfrage gelten

Engineering-Defaults; der Autor kippt jede mit einem Wort.

- **FV1** Bandbreite 100, Stand-Nummer = Basis + Index, nie
  wiederverwendet; ab Index 80 warnt die Apply-Antwort (§4.2).
- **FV2** Es gibt keinen Löschpfad für Stände und keinen UPDATE-Pfad für
  Kopf und Protokoll. Dieselbe Regel wie fürs Archiv; wer sie ändern will,
  braucht einen neuen Entscheid.
- **FV3** Der Vorgänger eines neuen Stands ist die laufende Arbeitslinie
  der Hand — ihr jüngster Stand seit der letzten Zeiger-Bewegung, sonst der
  ausgelieferte; Teil-Applies sammeln sich wie heute, nach einem Rollback
  erbt nichts vom zurückgenommenen Stand. Der erste Stand einer Hand beginnt
  leer (§4.3).
- **FV4** Der Zeiger hängt an der Hand, aufgelöst über `sources.hand_id`
  (§5.1).
- **FV5** Eine abgelehnte Variante antwortet wie eine leere (§5.2).
- **FV6** Auslieferung und Rollback sind Terminal-Akte über eine
  admin-gegatete Route, nie ein Knopf, und Prod-berührend im Sinn der
  Leitplanke (§8).
- **FV7** Die Bezeichner dieses Docs (`laufform_stands`, `hand_deliveries`,
  `?stand=`, `tools/freigabe`) sind Arbeitsnamen; der jeweilige PR
  entscheidet und zieht das Glossar nach.

## 11 Bau-Reihenfolge — eingehängt in `admin-redesign.md` §15.3

| Stufe | Inhalt | Hängt an §15.3 | Verify · Prod |
|---|---|---|---|
| **M0** | dieses Doc | Schritt 1 | `/write-docs` · nein |
| **M1** Schema + Saat | im gebündelten Schema-PR: `hands.laufform_variant` als Band-BASIS mit `UNIQUE (style_id, laufform_variant)`; `laufform_stands`, `hand_deliveries`; die Saat „Bestand = Stand 100" + erste Zeiger-Zeile, mit Abbruch statt stillem Verlust (§5.4); `glyph_pairs.hand_id` MIT erweitertem Eindeutigkeits-Schlüssel (§4.5); der Satz in `architektur.md` §3. Der Lesepfad liest noch die Konstante | Schritt 3 — setzt den Prod-Schritt V1 voraus | `/verify-migrations`, Snapshot davor · ja (Migrations-Job) |
| **M1b** Zeiger lesen, Lecks schließen | `compose_word_payload` liest den Zeiger und die Paare der Hand der Quelle; die zwei öffentlichen Regeln aus §5.2 mit ihren Tests; `write-api.md`. Beweis: bytegleiche Antwort (§5.4). Im selben PR lernt `dbsnapshot` die zwei Tabellen — `fetch.py` UND `restore.py`, mit Rundlauf-Test (§7): ab hier trägt der Zeiger die Seite | direkt nach Schritt 3, vor Schritt 6 | `/verify-api`, `/verify-core` · nein |
| **M2** Apply schreibt Stände | kopieren-dann-einfügen unter der Hand-Sperre, Kopf-Zeile, kein Stand ohne Änderung; PUT/DELETE als Stand-Operationen; Band-Regel; reservierte Reads `stands` · `deliveries`; `dbsnapshot` liest die Stände über das reservierte Inventar (§7); der Feder-Pool nach FM2 (i). Umbau getesteter Flüsse, Suiten ziehen mit (Q6 b) | VOR Schritt 6 — damit schon der erste Eigenhand-Apply Stand 200 anlegt | `/verify-api`, `/verify-core`; bei FM2 (i) a Vorher-/Nachher-Zahlen · nein |
| **M3** Vorschau mit `?stand=` | die reservierte Hand-Vorschau für Wort und Glyphen; die drei Admin-Flächen ziehen von der öffentlichen Route um; die SPA-Konstante `LAUFFORM_VARIANT` wird ein Datum | = Schritt 7, um `stand` erweitert | `/verify-api`, `/verify-frontend` gegen den Wegwerf-Stack · nein |
| **M4** Auslieferung | `POST …/deliveries`; die Stempel-Route und `&v=` in der SPA (FM5); `tools/freigabe` (`status` · `vergleich` · `deliver` · `rollback`); Runbook als Skill. Die Werkzeug-Leser aus §3, Zeile 12 folgen dem Zeiger statt der Konstanten — VOR der ersten Auslieferung eines Stands ≠ 100, sonst finden sie nach ihr keine Laufform mehr | nach Schritt 7 | `/verify-api`, `/verify-frontend` · der erste echte Aufruf ja |
| **M5** Regression je Hand | Fixture-Export `--stand`; die Gegenprobe an der Platte (§6.3); der Bericht Deckung · Beleglage · Formbewegung; die Messung gegen `holdout-release` mit eigener §14-Vorregistrierung (FM3 (b) ist entschieden, die Ziehung liegt im Trainingssatz-Werkzeug); die blinde Runde für Nr. 1 (FM4) | nach Schritt 6 — die Ziehung selbst hängt an keinem Schritt mehr | `/verify-trace`-Disziplin · nein |
| **M6** Admin-Flächen | Bestandskopf, „Ausgeliefert", Stände-Liste, „Letzte Änderungen", Vergleichsstreifen, Übergabekarten (§8) | Phase 4 des Admin-Plans | `/verify-frontend` · nein |
| **M7** Auslieferung Nr. 1 | der erklärte Rollenwechsel (§5.4) | eigener Autor-Entscheid, nach M4–M6 | alles · **ja** |

Ein Reihenfolge-Zwang ist hart: **M2 vor Schritt 6** (sonst überschreibt
der erste Eigenhand-Apply noch an Ort und Stelle, nur eben in Band 200).
Der zweite — **FM3 vor Schritt 4** — ist seit dem Entscheid vom 2026-09-20
beantwortet und damit kein Reihenfolge-Zwang mehr: die Ziehung läuft über den
eingefrorenen Plan statt über die Ernte, hängt also an keinem Schritt (§10
FM3). An seine Stelle tritt eine engere Bedingung: **gezogen wird, bevor die
erste von Hand nachgefahrene Bahn existiert** — nicht erst vor der Ernte.
Gezogen ist bis heute nichts; das Werkzeug steht bereit, der Schlüssel und
der Tag sind Autor-Sache.

## 12 Risiken

- **Die Saat hängt an Prod-Daten, die dieses Doc nicht kennt.** Ob Kurrent
  oder Offenbacher Variante-100-Zeilen tragen, wessen Stempel sie tragen und
  ob ihre Tafel-Quellen eine Hand nennen — oder ZWEI (Kurrent: zwei Tafeln
  zweier Hände, FM6) —, zeigt erst ein Lese-Sweep vor M1 (über die
  Admin-API, mit Rückfrage). Die Migration bricht ab, statt zu raten (§5.4).
- **Das Fenster zwischen M1 und M2.** Solange der alte Apply lebt, schreibt
  er weiter an Ort und Stelle in Variante 100 — in den Stand, den die Saat
  gerade benannt hat. Eingefroren ist Stand 100 darum erst AB M2; bis dahin
  sagt sein Kopf nur „Bestand", und ein Apply in diesem Fenster steht in
  keinem Protokoll (wie heute). M1b und M2 gehören kurz hintereinander,
  und M2 kommt nie vor M1b: ein zweiter Stand, den der Lesepfad nicht
  kennt, wäre eine zweite Wahrheit.
- **Der Snapshot hinkt hinterher** — zweimal möglich. Liest M1b den Zeiger,
  bevor `fetch.py` und `restore.py` Kopf und Zeiger kennen, brächte ein
  Restore die Stand-Zeilen ohne Auslieferung zurück, und die Seite schriebe
  nur noch mit der Tafel. Und legt M2 Stände an, bevor der Snapshot das
  reservierte Inventar liest, wären Stände jenseits des ausgelieferten nicht
  gesichert. Beide Male gilt: EIN PR (§7, §11).
- **Die Tafel bewegt sich unter einem Stand weg.** Ein Wizard-Re-Trace
  ändert Variante 0 sofort; die Laufform-Zeile hält die ALTEN Breiten und
  Anschlüsse ihrer Tafel-Zeile. Das ist heute schon so und wird mit der
  Maschine nur sichtbar (der Chip „Tafel seitdem geändert"). Ob ein
  Re-Trace einen neuen Stand ANSTOSSEN soll, ist eine Frage für nach M6.
- **FM1 (a) verlangsamt die kleine Korrektur.** Ein einzelnes falsches Paar
  braucht dann Stand + Auslieferung. Gegenmittel ist ein schneller
  Werkzeug-Schritt, nicht ein Loch im Stand.
