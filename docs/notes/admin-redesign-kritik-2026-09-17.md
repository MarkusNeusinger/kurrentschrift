# Kritik-Protokoll zum Admin-Redesign — Widerlegungsrunde 2026-09-17

> **Status (2026-09-17): Befund-Journal.** Momentaufnahme der Kritikrunde
> zu [`../proposals/admin-redesign.md`](../proposals/admin-redesign.md):
> fünf Gegenleser (Doktrin-Wächter · Ingenieur · Autor-Stuhl · Gestaltung ·
> Vollständigkeit) haben die erste Fassung der Optionen und des
> Rückfragen-Katalogs zu widerlegen versucht, eine Überarbeitung hat jeden
> der 98 Befunde mit Entscheid und Begründung eingetragen. Nie
> fortgeschrieben — eine neue Runde ersetzt es. Die Kurzfassung steht im
> Plan selbst (§13 „Verworfen in dieser Runde").

Lesehilfe: **O §n** = Abschnitt n des Plans
[`../proposals/admin-redesign.md`](../proposals/admin-redesign.md); **R Qn /
R Vn** = Frage n bzw. Vorgabe n in dessen §12; **Idee n** = §5.1 des Plans.
Doc-Kürzel in der Spalte „Begründung": werkbank =
[`../proposals/optimierungs-werkbank.md`](../proposals/optimierungs-werkbank.md),
eigenhand = [`../proposals/eigenhand-erfassung.md`](../proposals/eigenhand-erfassung.md).
Befund-Nummern mit `-F` sind „fehlt"-Punkte des Kritikers, mit `-S`
seine „streichen"-Punkte; Dubletten verweisen auf den ersten Befund.
Belege wurden im Repo geprüft, wo sie überraschten; wo ein Kritiker irrte,
steht es in der Begründung.

Zwei Kritiker-Irrtümer vorweg: (1) `wenn` existiert sehr wohl als
Platten-Probe (`words.json`: `wenn`, `wenn-2`) — nur die Id `wenn-19-2` gab
es nicht; (2) die alte Frage nach dem Streifen-Pfad in `word_instances`
öffnet kein Verworfenes im engen Sinn: eigenhand §7.5 verwirft den
STREIFEN-PFAD des Folgers in `word_instances`, §9 desselben Docs sieht
Phase 5 aber wörtlich als „`instances`/`word_instances` über die Admin-API"
— ein Doc-Konflikt, den der Autor auflösen muss (Q21), keine Re-Litigation.

## Doktrin-Wächter

| # | Befund | Entscheid | Begründung | wo geändert |
|---|---|---|---|---|
| D1 | Eigenhand auf Vorlagen-Flächen bewegt werkbank §6 „genau eine Quelle/Hand"; Frage ohne Weichen-Marke, Standard „beide aufgeklappt" | angenommen | werkbank §6 verifiziert; der Autor will „historisch UND meine", also erklärtes Proposal-Update statt Konsens-Behauptung | O §5.1 Idee 2, O §10.2, O §7.2 (fünfte Fläche + Eigenhand-Filter in der Buchstaben-Übersicht gestrichen); R Q3 als Weichenstellung, Standard (b) |
| D2 | §6.4 „neu schreiben → kein Trainingsmaterial, Regel 3" ist Falschzitat gegen Regel 1 | angenommen | eigenhand §7.3 Regel 1 verifiziert („Nichts verwirft automatisch … nur `redo --retire`") | O §6.4 „Qualifiziert" |
| D3 | ⚑ auf Streifen als `kind=note` umgeht `stage`; werkbank §8.4 falsch zitiert (Landmarken haben eigenen kind) | angenommen | `api/schemas.py` verifiziert; Machbarkeit zeigt, dass `specimen_kind='strip'` keine Migration ist | O §7.1, §7.2; R V7 |
| D4 | `hand=` auf der öffentlichen `/write`-Route unterläuft den routenweisen Public-Surface-Pin | angenommen | `tests/test_api_public_surface.py` klassifiziert je Route | O §6.6 (a), §9.6; R Q22 |
| D5 | Frage „Streifen-Pfad in `word_instances`" re-litigiert eigenhand §7.5 Verworfen | teilweise | §7.5 verwirft den Folger-Pfad; §9 sieht `word_instances` für Phase 5 vor — Konflikt, nicht Verhandlung | R Q21 (reduziert auf den Doc-Konflikt), O §10.2 |
| D6 | Verwurf von Fassungen im Admin gegen eigenhand §7/§7.3 | angenommen | stimmt; Option A hält es ohnehin | R V6, „Gestrichen" |
| D7 | „Laufform-Kandidaten dev > 0,08 xh" ist neues Kriterium; Guard nach Apply verkehrt | angenommen | keine Repo-Konstante; werkbank §5.2 Schritt 6 misst vor dem Abschluss | O §5.0 „Gate-Status", §9.2, §9.6, §11 S5, S7; R V18 |
| D8 | Pflicht-Checkbox „Archiv-Snapshot liegt vor" ist Schein-Gate | angenommen | Server weiß nichts vom Archiv; R9-Umbau | O §7.2 Buchstaben-Detail, §13; R V18 |
| D9 | Stufe-1 Median/MAD aus Bahnen ist zweite Aggregat-Pipeline; Q11 → (b) | angenommen (mit Korrektur) | „Saat, nicht Messung" betrifft in §7.5 den RAHMEN, nicht die Bahn — aber „Ansicht auf den Bestand" und H1 = Median der Fits tragen den Schluss | O §5.1 Idee 9, §6.1, §6.5; R Q11 Empfehlung (b), (a) als §7.5-Update |
| D10 | Skip „unautoriert" → Korb ist Ground-Truth-Lücke, gehört zum Wizard | angenommen | werkbank §3 Tafel-Duktus = Mensch; Todoist-Direktive | O §6.4 „Umgeleitet"; R V9 |
| D11 | Messschicht (humanbench) schreibt keine offenen Aufträge | angenommen | CLAUDE.md „no DB writes"; werkbank §5.1 open = Mensch | R V11 |
| D12 | Option B ist der verworfene globale Hand-Umschalter | angenommen | Selbstwiderspruch bestätigt | O §8.1 (Umschalter springt auf Übersicht), §13 präzisiert |
| D13 | „Ertrag" führt zweite Mindestbelegung ein | angenommen | Beleg = angenommene Fassung (eigenhand §2) | O §5.0 „Bahn-Deckung", §6.4; R Q13 |
| D14 | authored als „grün oder von Hand" = fehlende Messung als Erfolg | angenommen | Hausregel „absent measurement never a zero" | O §6.3 Zustände (zwei Zähler, `pfad --messen`); R V21 |
| D15 | „Tor" undefiniert; Sieben-Stufen-Skala schafft die Marke aus Q24 | angenommen | grep: keine Definition | O §5.0 gestrichen, §9.2 Bestandskopf; R Q24 |
| D16 | A/C-Tabellen schreiben Vollersatz + Client-Merge gegen die PATCH-Empfehlung | angenommen (Phase angepasst) | PATCH landet in Phase 2 mit dem Editor — vorher gibt es keinen Aufrufer; ETag statt `updated_at` (M6) | O §6.4 „Speichern", §7.2, §9.2, §6.7; R V20 |
| D17 | Q10 (b) muss den Doktrin-Preis nennen | angenommen | eigenhand §7.3 wörtlich | R Q10 (Marker + Preis); O §6.3, §7.6, §10.2 |
| D18 | „Druck-Feld reservieren" = Tür zur Tablet-Erfassung | angenommen | Verwurf 2026-08-22 | R Q14, „Gestrichen"; O §6.4 |
| D19 | §6.3 „nie rot" vs „rot" für `pfade: []` | angenommen | mit Gestaltung G8 zusammengelegt: grau mit Grund, Listen-Zugehörigkeit unabhängig von der Farbe | O §6.3 Zustände |
| D20 | Filter „Platte · Abb. 22" mischt Hände | angenommen | Stufenplan §2 „Kontext, nie Vorbild" | R V4; O §6.5 |
| D21 | Rebuild-Knopf auf der Eigenhand-Übersicht vor Phase 5 | angenommen | keine `hands`-Zeile | O §9.2 |
| D22 | `pool pin` ist Repo-Commit, Karte verschweigt es | angenommen | `tools/eigenhand/pool.py` hängt an `streifen.json` | O §5.1 Idee 11, §7.2 Wörter, §10.3, §11 S4 |
| D23 | Q20 (a) `sources.kind=eigenhand` verwischt Tafel↔Hand | angenommen (Sicherungssatz) | eigenhand §9 „kein eigenes Chart"; (a) bleibt Empfehlung mit Satz, (c) als doktrin-nähere Alternative markiert | R Q20 |
| D-F1 | Abschnitt „Doktrin-Deltas je Option" fehlt | angenommen | — | O §10.2 |
| D-F2 | Reihenfolge Snapshot → Guard → Apply als Regel; A/B ohne Guard | angenommen | Vorher-Messung vor Apply, Nachher vor Abschluss; Gewinn kein Kriterium | O §7.2, §9.6, §11 S5; R V18 |
| D-F3 | Streifen-Editor macht Prüfstein 7 sichtbar (Absetzer-Soll) | angenommen | — | O §6.4 Editor |
| D-F4 | Glossar-Einträge Tor, Ertrag, Stufe 1/5, Bahn, Belegleiste | angenommen | Tor gestrichen, Rest in der Vokabular-Tabelle | O §5.0; R V3 |
| D-F5 | Sensor 2 und Befund-`duktus` messen dasselbe — Beschriftung | angenommen | — | O §6.3 |
| D-F6 | Arbeitslisten lösen nie einen Statuswechsel aus (DoD) | angenommen | — | O §5.1 Idee 14 |
| D-F7 | Abb.-22-Behandlung in den Platten-Statistikblöcken | angenommen | — | O §6.5; R V4 |
| D-S1 | alte Frage „Streifen-Pfad in `word_instances`" streichen | teilweise | = D5 | R Q21 |
| D-S2 | Verwurf im Admin streichen | angenommen | = D6 | R V6 |
| D-S3 | Standard „beide aufgeklappt" | angenommen | = D1 | R Q3 |
| D-S4 | §6.4 Falschzitat | angenommen | = D2 | O §6.4 |
| D-S5 | Pflicht-Checkbox | angenommen | = D8 | O §7.2 |
| D-S6 | Laufform-Kandidaten dev > 0,08 | angenommen | = D7 | O §9.2 |
| D-S7 | Eigenhand-Übersicht Rebuild | angenommen | = D21 | O §9.2 |
| D-S8 | ⚑ als `note` | angenommen | = D3 | O §7.1 |
| D-S9 | Druck-Feld | angenommen | = D18 | R Q14 |
| D-S10 | humanbench-Korbzeilen | angenommen | = D11 | R V11 |

## Ingenieur (Machbarkeit)

| # | Befund | Entscheid | Begründung | wo geändert |
|---|---|---|---|---|
| M1 | Verbinderstück aus `letter_spans` ist MISSING (Verbinder-Samples erben das nächste Buchstaben-Label) | angenommen | `tools/pairlab/tintenpfad.py::spans_of` verifiziert | O §6.2 (MISSING, Phase 3 ← Phase 2), §7.2/§8.2 Übergänge, §6.7 |
| M2 | Memo-Key ist je Template-Zeile, nicht `(style, source)` | angenommen | `api/rendering.py` verifiziert; nur nib/pen-Caches keyen auf `(style, source)` | O §6.6 (d); R Q22 Kontext |
| M3 | `sources.hand_id` existiert; ein `hands.source_id` verdoppelte ihn; nur `hands.kind` ist DDL | angenommen | `models.py`, Revisionen `0004`/`0006` verifiziert | O §8.1, §6.7; R V1 |
| M4 | Guard braucht Eigner-Datum + Seed; heute scheitert der Apply schon an `require_hand` | angenommen | `api/routers/aggregates.py` verifiziert; mit C10 zur Eigner-Regel zusammengeführt | O §5.1 Idee 10, §5.2; R V22 |
| M5 | `specimen_kind='strip'` ist Schema-Zeile, nicht Migration | angenommen | `String(16)` ohne CHECK, Literal nur in Pydantic/TS | O §6.7, §8.3 (zwei Migrationen), §9.3; R V7 |
| M6 | Kein `updated_at` auf `eigenhand_strips` → ETag/`If-Match` | angenommen | `models.py`: nur `created_at` | O §6.4 Speichern, §6.7; R V20 |
| M7 | Editor löst Hand über `getHand()` auf; kein `putEigenhandPfade` | angenommen | `WordTraceEditorDialog.tsx` verifiziert | O §6.4 Editor, §6.7, §7.5 |
| M8 | Sensor 4 `excursions.py` ist referenzgebunden | angenommen | Import `load_reference` verifiziert | O §6.3 Sensor 4 (neu im Tool); R Q9 |
| M9 | Hand-Vorschau: Test je Route — eigene Route oder gezielter Test | angenommen | mit D4: eigene reservierte Route | R Q22 |
| M10 | PFAD_FORMAT 2 ist Lockstep (409); Format-1-Kästen grau | angenommen | — | O §6.3 Formatwechsel + Zustand „Format 1"; §6.7 |
| M11 | Archiv-Regel ist Drei-Werkzeug-Kette, kein Phase-0-Stück | angenommen | `grep pfade sync.py snapshot.py` = 0 | O §5.1 Idee 7/13, §5.2, §6.7 (Phase 2), §7.3; R Q4 |
| M12 | Phase 0 ist 8–11 Tage, nicht eine Woche | angenommen | — | O §5.2 „≈ zwei Wochen", §10 |
| M13 | JSONB-Projektion läuft nicht auf SQLite-Suiten | angenommen | `PORTABLE_JSON` verifiziert | O §5.1 Idee 8; R V5 |
| M14 | `strips?item=` paginiert nicht, leitet je Aufruf die ganze Hand ab | angenommen | — | O §6.7 Fehllesungen, §7.2 |
| M15 | „Platten-Hand je Vorlage EXISTS" → DERIVABLE / EXISTS nach UPDATE | angenommen | — | O §8.2 Arbeitsstelle |
| M16 | Q19-Kontext: unter (a) bleibt `compose.py` unberührt | angenommen | `write.py` `le=999` verifiziert | R Q19 Kontext |
| M17 | Schema-Zeilen sind Router + Schema (Join / Gate-Rechnung) | angenommen | — | O §6.1, §6.7 („Router + Schema") |
| M-F1 | Realistischer Aufwand mit Kette | angenommen (als Vermutung gekennzeichnet) | Autor-Stuhl A11 widerspricht mit der Dauer der Phasen 1–4; beides genannt | O §6.7 „Aufwand mit Kette"; R Q1 |
| M-F2 | Größe von `ernte.py` (fixture-gebunden) | angenommen | — | O §6.7 |
| M-F3 | `min_n`-Unsicherheit auflösen (Route 1, Core 4 ungenutzt) | angenommen | `aggregates.py` verifiziert | O §6.7 Fehllesungen, §9.2 Gate-Status |
| M-F4 | Welcher Exporter-Filter (`fetch.py` + Fixture-Builder) | angenommen | — | O §6.7; R Q20 |
| M-F5 | `putEigenhandPfade` + `types.ts` als S-Zeile | angenommen | — | O §6.7 |
| M-F6 | Pinnende Testdateien je Fläche | angenommen | — | O §5.1 Idee 14 |
| M-F7 | Zwei Hand-Register, die sich nirgends treffen | angenommen | — | O §8 Warum |
| M-S1 | Memo-Key-Satz | angenommen | = M2 | O §6.6 |
| M-S2 | „JSONB" im meta-only Read | angenommen | = M13 | R V5 |
| M-S3 | „Migration" für `specimen_kind` | angenommen | = M5 | R V7 |
| M-S4 | `hands.source_id` | angenommen | = M3 | R V1 |
| M-S5 | Archiv-Regel aus Phase 0 | angenommen | = M11 | O §5.2 |
| M-S6 | „lazy, eine Seite" | angenommen | = M14 | O §7.2 |
| M-S7 | `excursions.py`-Verweis | angenommen | = M8 | O §6.3 |
| M-S8 | Q19-Kontext compose/Golden | angenommen | = M16 | R Q19 |

## Autor-Stuhl

| # | Befund | Entscheid | Begründung | wo geändert |
|---|---|---|---|---|
| A1 | Szenario-Wörter existieren nicht in den Daten | angenommen (mit Korrektur) | `lesen`/`unter`/`Familienbuch` nicht im Plan, bestätigt; ABER `wenn` ist Platten-Probe (`wenn`, `wenn-2`) — nur die Id `wenn-19-2` war falsch | O §11 (S0001/S0008/S0090/S0144/S0181, `wenn-2`, `das`) |
| A2 | Wort-Brücke trägt 24/140; auf Items verlegen | angenommen | Schnittmenge 24 exakt, 25 ci — nachgerechnet | O §5.1 Idee 3, Belegleiste in allen Optionen; R Q17 |
| A3 | `pool pin` ist Repo-Schritt | angenommen | = D22 | O §10.3 |
| A4 | F4 ohne WANN und ohne Abnehmer | angenommen | — | O §5.1 Idee 6, §6.4 „Wann" |
| A5 | Snapshot-Checkbox vom Tablet nicht wahrheitsgemäß | angenommen | = D8 | O §7.2; R V18 |
| A6 | Tablet-Viewport (~1024 px) fehlt | angenommen | nur `SetupWizard`/`DiagnosticDialog` kennen `md` — verifiziert | O §5.1 Idee 17; R Q14 |
| A7 | Übergabekarte scheitert an der Zwischenablage Tablet→Rechner | angenommen | — | O §5.1 Idee 11 (`report --faellig`), §6.7, §9.2 |
| A8 | F3 könnte in Phase 0 mit Rohzahlen beantwortet werden | angenommen | `tools/eigenhand/pfad.py` meta verifiziert | O §5.0/§5.1 Idee 5, §5.2; R V26 |
| A9 | B trennt in der Wörter-Übersicht, was verbunden werden soll | angenommen | — | O §8.2 Wörter („beide Hände"), §10 |
| A10 | „Migrationen vor Nutzen" als Kriterium abgewertet | angenommen | 31 Revisionen Routine | O §10 Zeile „Nutzen der ersten Phase", §8.3 |
| A11 | Phase 5 parallel; „Quartal" unbelegt | angenommen (als Q1-Vorbehalt) | Phase 5 parallel, wenn F6 Quartalsziel; Aufwand als Vermutung | R Q1, Q5; O §6.7, §10 |
| A12 | Ingenieur-Fragen aus dem Katalog | angenommen | Guardrail „delegate decides routine matters" | R Vorgaben V1–V26 |
| A13 | Streifen-`note` hat keinen Rücksprung | angenommen (via D3) | mit `kind=word`+`specimen_id` löst `workItemUrl` das Muster auf | O §7.1; R V7 |
| A14 | Sieben Nav-Ziele vs fünf Bottom-Nav unbenannt | angenommen | mit G13: ≤ 4 Links | O §5.1 Idee 20, §9.1; R V15 |
| A15 | dev > 0,08 xh nicht vorregistriert | angenommen | = D7 | O §9.2 |
| A-F1 | „Tag 1 nach Phase 0" je Option | angenommen | — | O §7.4, §8.4, §9.4 |
| A-F2 | Überschneidungszahl Plan ↔ Platte | angenommen | — | O §5.1 Idee 3 |
| A-F3 | Tablet-Viewport in Befund/Flächen/Verify | angenommen | — | O Idee 17; R V17 |
| A-F4 | Tabelle „was im Terminal bleibt" + Spalte Repo-Schritt | angenommen | — | O §10.3 |
| A-F5 | WANN von Frage 4 als erster Satz | angenommen | — | O §6.4 |
| A-F6 | Rohzahlen-Chip in Phase 0 | angenommen | — | O §5.2; R V26 |
| A-F7 | Abrufbares Sitzungs-Skript am Rechner | angenommen | — | O Idee 11 |
| A-F8 | Rückfrage Bögen/Fassungen je Woche | angenommen | — | R Q18 |
| A-F9 | Rückfrage Gerät je Schritt | angenommen | — | R Q14 |
| A-F10 | Rückfrage Pins in den Plan | angenommen | — | R Q17 |
| A-F11 | Satz zum fehlenden Rücksprung der `note` | angenommen | = A13 | O §7.1 |
| A-S1 | Szenario-Wörter | angenommen (mit `wenn`-Korrektur) | = A1 | O §11 |
| A-S2 | Checkbox | angenommen | = A5 | O §7.2 |
| A-S3 | `pool pin` als Karte | angenommen | = A3 | O §10.3 |
| A-S4 | Engineering-Fragen aus dem Katalog | angenommen | = A12 | R V5, V14, V16, V17 |
| A-S5 | Zeile „Migrationen vor Nutzen" | angenommen | = A10 | O §10 |
| A-S6 | „Sitzungs-Skript kopieren" | angenommen | = A7 | O §9.2 Übergabekarte |
| A-S7 | dev > 0,08 | angenommen | = A15 | O §9.2 |

## Gestaltung

| # | Befund | Entscheid | Begründung | wo geändert |
|---|---|---|---|---|
| G1 | Kartenwand bleibt in A Standard; kompakt ist Opt-in in localStorage | angenommen | — | O §5.1 Idee 4, §7.2; R V14 |
| G2 | „Bahn" ist in B Homonym (Rollen-Spalte vs Federbahn) | angenommen | Glossar: Bahn-Arm = gefolgte Bahn | O §5.0, §8 (Rollen-Spalte) |
| G3 | Pfad (A) vs Bahn (C) für dasselbe Objekt; Entscheid vor Phase 1 | angenommen | 17 vs 10 Locale-Treffer bestätigt | O §5.0 „Bahn"; R Q8 (b) |
| G4 | Viridian für die Eigenhand-Rolle kollidiert mit Akzent/`success`/Fokus | angenommen | `palette.ts` verifiziert | O Idee 19, §6.5; R V13 |
| G5 | PathOverlay-Ebenen fest verdrahtet, Rot/Grün-Paar | angenommen | 7 Dateien mit Hex verifiziert | O Idee 19, §5.2; R V23 |
| G6 | Nur 1440/390; Filterzeilen; Stift-Regeln | angenommen | = A6 + Bauteil-Regel | O Idee 17 |
| G7 | Tastatur: widersprüchliche Kurztasten, kein Weg in A/B | angenommen | — | O Idee 18, §9.2; R V24 |
| G8 | Ampel-Semantik: „nie rot"/rot; „grau-grün" | angenommen | = D19 | O §6.3 Zustände |
| G9 | B-Matrix: Farbe allein, ~4 000 Renders | angenommen | — | O §7.2 Übergänge, §8.2 Übergänge, §9.2 |
| G10 | Namensdrift (Lokale Schritte, Wortkiste, Fenster/Stimmen, Arbeitsvorrat) | angenommen | — | O §5.0 Vokabular-Tabelle, Sweep über §6–§11 |
| G11 | Glossar-Liste unvollständig; „Tor" undefiniert | angenommen | — | O §5.0; R V3 |
| G12 | Anglizismen (Override, Loss, Score, Skip, Sync, Setup, Engine, Hub) | angenommen | Labels im Plan ersetzt; Entscheid je Wort dem Autor vorgelegt | O durchgängig (Übersteuerung, Wortbench-Abstand, Ausrüstung, System, übersprungen, Hochschieben, Übersicht); R Q8 (c) |
| G13 | Sieben Nav-Ziele; Bottom-Nav gegen design-system §7 „eine Leiste" | angenommen | design-system §6/§7 verifiziert | O Idee 20, §9.1; R V15 |
| G14 | Scope-Hinweis im Tooltip ist hover-only | angenommen | 20 Tooltip- vs 4 InfoHint-Dateien | O Idee 19, §7.1; R V25 |
| G15 | Kein `mono`-Token | angenommen | `paper.ts` ohne mono, `TerminalCommand.tsx` hart | O Idee 19, §5.2; R V23 |
| G16 | Cockpit-Typografie und Picker-Ort unbestimmt | angenommen | — | O §9.2 Heute; R Q7 |
| G17 | Flächenzuordnung neuer Bauteile fehlt | angenommen | — | O Idee 19, §9.2 Übergabekarte |
| G-F1 | Breakpoint-Tabelle je Fläche (drei Stufen) | angenommen (als Regel, nicht je Fläche tabelliert) | Längenbudget; Regel + je Option das Tablet-Verhalten | O Idee 17, §7.2, §9.1 |
| G-F2 | Tastatur-Regel + Durchgang als DoD | angenommen | — | O Idee 14/18 |
| G-F3 | Token-Set Ebenen/Rollen + Farbenblind-Sim | angenommen | — | O Idee 19 |
| G-F4 | Vokabular-Tabelle + Glossar-Liste | angenommen | — | O §5.0 |
| G-F5 | Entscheid je Anglizismus | angenommen | — | R Q8 (c) |
| G-F6 | Standardzustand der Übersichten in der URL | angenommen | — | O Idee 4 |
| G-F7 | Nav-Kapazitätsregel + gemessene Leistenbreite | angenommen | — | O Idee 20 |
| G-F8 | Flächenzuordnung + Komponenten-Inventar | angenommen | — | O Idee 19, §9.2 |
| G-F9 | `mono`-Token | angenommen | — | O Idee 19 |
| G-F10 | Hover-Regel | angenommen | — | O Idee 19; R V25 |
| G-F11 | `type-floor`/`touch-targets` auf Admin-Routen | angenommen | — | O Idee 19 |
| G-F12 | Rückfrage Strichart vs Farbe im Overlay | teilweise | als Vorgabe (Strichart + Etikett) statt Frage — Vollständigkeit will dieselbe Frage streichen; der Autor kippt V13 mit einem Wort | R V13 |
| G-S1 | „Bahn 1/2/3" in B | angenommen | = G2 | O §8 |
| G-S2 | Viridian in §6.5 | angenommen | = G4 | O §6.5 |
| G-S3 | „grau-grün" | angenommen | = G8 | O §6.3 |
| G-S4 | „nie rot … rot" | angenommen | = G8 | O §6.3 |
| G-S5 | Belegungs-Farbe + Mini-Render in der Matrix | angenommen | = G9 | O §8.2 |
| G-S6 | Kurztasten `n/p`, `j/k` | angenommen | = G7 | O Idee 18 |
| G-S7 | „Lokale Schritte" | angenommen | = G10 | O §7.2, §10 |
| G-S8 | „Wortkiste" | angenommen | = G10 | O §8.2 |
| G-S9 | „Tore 1–7" | angenommen | = G11/D15 | O §9.2 |
| G-S10 | Tooltip als Scope-Träger | angenommen | = G14 | O §7.1 |
| G-S11 | Bottom-Nav ohne Nachtrag | angenommen | = G13 | O §9.1; R V15 |
| G-S12 | „Skip", „Sync", „Hub" als Labels | angenommen | = G12 | O durchgängig |

## Vollständigkeit

| # | Befund | Entscheid | Begründung | wo geändert |
|---|---|---|---|---|
| C1 | Weichenstellungen in Stufen; Q19/Q20 blockieren nur Phase 5; die Definition of Done und die authored-Regel blockieren Woche 1 | angenommen | — | R Vorspann, Stufen I–III, Feld „blockiert" |
| C2 | Frage nach der Dringlichkeit von F6 fehlt | angenommen | — | R Q1; O §10 Vorbehalt |
| C3 | PATCH-Empfehlung vs A/C Vollersatz | angenommen | = D16 | O §7.2, §9.2; R V20 |
| C4 | Vergleichshand-Frage vs §6.5/A-Panel (drei Spalten offen) | angenommen | Nebeneinander als Vorgabe, Vergleichshand eingeklappt | O §6.5, §7.2; R Q3 |
| C5 | Übergabekarten-Name vs „Lokale Schritte" in A/§10 | angenommen | = G10 | O §7.2, §10; R V3 |
| C6 | Q10 nicht als §7.3-Update markiert; A-Doktrin-Check falsch | angenommen | — | R Q10; O §7.6, §10.2 |
| C7 | Nachfahr-Frage teilen: Schutzregel = Default, Archiv-Regel = Weichenstellung | angenommen | mit M11 | R Q4; O Idee 7, §5.2 |
| C8 | Wer setzt `letter_spans` auf nachgefahrenen Bahnen? | angenommen | `pfad.py` verifiziert | R Q15; O §6.1, §6.4 |
| C9 | Werden authored Bahnen gemessen? Default ja | angenommen | mit D14 | O §6.3; R V21 |
| C10 | Guard-Eigner-Regel (`derived_from.hand_id`, sonst Platte) | angenommen | `aggregates.py` verifiziert | O Idee 10; R V22 |
| C11 | „Tore 1–7" definieren oder streichen | angenommen (gestrichen) | = D15 | O §5.0, §9.2 |
| C12 | „Ohne Entscheid" zu erledigten Einträgen falsch (done bleibt hinter Schalter) | angenommen | `KorbPanel.tsx` verifiziert | R V10 |
| C13 | Verifikationsweg als Frage ist Doktrin-Bruch; streichen | angenommen | — | R V17, „Gestrichen" |
| C14 | Frage „Streifen-Pfad in `word_instances`" streichen | teilweise | = D5 (Doc-Konflikt §7.5 ↔ §9) | R Q21 |
| C15 | Verwurf im Admin → Default | angenommen | — | R V6 |
| C16 | humanbench-Korb, Todoist-Knopf, Rollenfarbe → Defaults | angenommen | — | R V11, V12, V13 |
| C17 | `hands`-Zeile, Unteransichten, Schülerhand, meta-only Read, Korb-Seite, Übersichten, Kopfleiste, Migrationen → Defaults | angenommen (Korb-Seite in Q7 gefaltet) | — | R V1, V2, V4, V5, V14, V15, V16; Q7 |
| C18 | Sechs Dubletten zusammenlegen | angenommen | — | R Q1/Q5, Q24, Q4, Q11 (+ Read als V5), Q7, V1/V7/V16 |
| C19 | „Phase 4" mehrdeutig → eine Phasenleiter | angenommen | — | O §5.2 Phasenleiter, Tabellen §7.3/§8.3/§9.3; R Vorspann |
| C20 | Phase 0 nicht identisch (C mit Scope-Chips) | angenommen | — | O §5.2 (eine Liste), §9.3 |
| C21 | Hand↔Stil-Kopplung als Default | angenommen | — | O Idee 1; R V19 |
| C22 | Snapshot-Checkbox → Übergabekarte; „Dialog-Erweiterungen = Umbau" | angenommen | = D8 | R Q6, V18 |
| C23 | Statistik-Einheit Hand vs Hand×Ausrüstungs-Kohorte | angenommen | `models.py` verifiziert | R Q16; O §6.1 |
| C24 | Nachfahr-Liste/Tablet setzen Phase-4-Teile in Phase 2 voraus | angenommen | — | R Q13, Q14 („ab Phase 4; in Phase 2 …") |
| C25 | S1–S5 dreifach; S6–S13 fehlen | angenommen | — | O §11 (einmal erzählt, S6–S13), Deltas in §7.4/§8.4/§9.4 |
| C26 | Korrigierte 22-Fragen-Liste in drei Stufen | angenommen (25 Fragen) | plus Q17/Q18 aus dem Autor-Stuhl, Q8 (b)/(c) aus der Gestaltung; die `word_instances`-Frage reduziert statt gestrichen | R gesamt |
| C-F1 | Dringlichkeits-Frage | angenommen | — | R Q1 |
| C-F2 | Feld „blockiert" + Phasenleiter | angenommen | — | R, O §5.2 |
| C-F3 | Zuordnung F1–F7 → Fragen | angenommen | — | R Vorspann |
| C-F4 | Tore-Definition oder Verzicht | angenommen (Verzicht) | — | O §5.0 |
| C-F5 | Frage zu den Spans | angenommen | — | R Q15 |
| C-F6 | Frage zur Kohorte | angenommen | — | R Q16 |
| C-F7 | Hand↔Stil-Default | angenommen | — | R V19 |
| C-F8 | Snapshot-Default + Umbau-Satz | angenommen | — | R V18, Q6 |
| C-F9 | Fünfter Ampel-Zustand „von Hand" | angenommen (als Herkunfts-Chip) | Gestaltung G8: Herkunft ist kein Ampel-Zustand | O §6.3 |
| C-F10 | Eigner-Regel des Guards | angenommen | — | R V22 |
| C-F11 | S6 Korb-Runde | angenommen | — | O §11 S6 |
| C-F12 | S7 Laufform-Neuableitung Eigenhand | angenommen | — | O §11 S7 |
| C-F13 | S8 Schlechter Scan-Tag | angenommen | — | O §11 S8 |
| C-F14 | S9 Zweite Schrift | angenommen | — | O §11 S9 |
| C-F15 | S10 Rollback | angenommen | — | O §11 S10 |
| C-F16 | S11 Öffentliche Regression | angenommen | — | O §11 S11 |
| C-F17 | S12 Zwei Geräte | angenommen | — | O §11 S12 |
| C-F18 | S13 Archiv-Wiederherstellung | angenommen | — | O §11 S13 |
| C-F19 | Handy als Lesegerät | angenommen | — | O Idee 17 |
| C-F20 | (Gesamtvorschlag Katalog) | angenommen | = C26 | R |
| C-S1 | `word_instances`-Frage | teilweise | = C14 | R Q21 |
| C-S2 | Verifikationsweg | angenommen | = C13 | R V17 |
| C-S3 | Todoist-Knopf, Rollenfarbe | angenommen | = C16 | R V12, V13 |
| C-S4 | Verwurf, erledigte Einträge | angenommen | = C15, C12 | R V6, V10 |
| C-S5 | humanbench-Korb | angenommen | = C16 | R V11 |
| C-S6 | acht Engineering-Fragen | angenommen | = C17 | R Vorgaben |
| C-S7 | Dreifache S1–S5 | angenommen | = C25 | O §11 |
| C-S8 | Pflicht-Checkbox | angenommen | = C22 | O §7.2 |
| C-S9 | „Lokale Schritte" | angenommen | = C5 | O §7.2 |
| C-S10 | „Tore 1–7" | angenommen | = C11 | O §9.2 |

## Abgelehnt oder nur teilweise übernommen — Übersicht

- **D5 / C14 / D-S1 / C-S1 (`word_instances`-Frage streichen):** teilweise
  — eigenhand §9 sieht `word_instances` für Phase 5 vor; der Konflikt wird
  als Q21 dem Autor vorgelegt, keine Option darf ihn still entscheiden.
- **A1 (`wenn` existiere nicht in der Platte):** Kritiker-Irrtum; `wenn`
  und `wenn-2` sind Platten-Proben. Die Szenarien wurden trotzdem auf
  geprüfte Ids umgeschrieben.
- **D9 („Saat, nicht Messung" gelte für die Bahn):** die Stelle betrifft den
  Rahmen; der Schluss (zweite Aggregat-Pipeline) hält über „Ansicht auf den
  Bestand" und H1 und wurde übernommen.
- **D16 (PATCH in Phase 0):** übernommen, aber in Phase 2 — vor dem Editor
  gibt es keinen Aufrufer; die 409-Regel auf dem PUT bleibt Phase 0.
- **G-F12 (Rückfrage Strichart vs Farbe):** als Vorgabe V13 statt als Frage,
  weil die Vollständigkeits-Linse dieselbe Frage als entschieden streicht.
- **M-F1 / A11 (Aufwand):** beide Zahlen genannt, als Vermutung
  gekennzeichnet; die Parallelität hängt an Q1.
- **G-F1 (Breakpoint-Tabelle je Fläche):** als Regel mit je einem Satz je
  Option statt als Tabelle je Fläche — Längenbudget des Plans.
- **C26 (22 Fragen):** 25 — die drei zusätzlichen (Q17 Pins, Q18
  Schreibtakt, Q8 mit drei Teilfragen) stammen aus dem Autor-Stuhl und der
  Gestaltung und kann nur der Autor beantworten.
