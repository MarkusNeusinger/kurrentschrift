# Corpus: igerman98 (de_DE_frami)

- Title:     igerman98 — das deutsche Ispell/Hunspell-Wörterbuch, in der
             LibreOffice-Fassung `de_DE_frami` (Basiswörterbuch + frami-Addon)
- Author:    Björn Jacke (Grundwörterbuch, https://www.j3e.de/ispell/igerman98/);
             Franz Michael Baumann (frami-Erweiterung)
- Year:      laufend; bezogen aus dem LibreOffice-Dictionaries-Repo,
             Commit `32b006a2c22a4ac7e8ed3f03346f7b3d85a970a4`
- License:   GNU GPL, Version 2 oder 3 (README_de_DE_frami.txt: „Das
             Wörterbuch und alle enthaltenen Wortlisten sind lizenziert
             unter der GNU GPL, Version 2 oder 3.")
- License-Rationale (Autor-Entscheid 2026-08-30): Die Wortliste ist
             SERVERDATEN der Lesart-Seite, nie Repo-Inhalt. Die GPL erlaubt
             die Nutzung ohne Bedingungen; Pflichten (Lizenztext, Quelle)
             entstehen erst bei WEITERGABE der Liste — die findet nicht
             statt: `tools.lesarten.sync` lädt die expandierten Formen über
             die Admin-API in die geteilte Datenbank (`lesart_forms`,
             Migration 0028), und `GET /lesarten?text=` antwortet je Anfrage
             mit höchstens einer Handvoll Wörtern, nie mit der Liste. Die
             Bytes bleiben gitignored (`/data/corpora/**`), kommen nicht ins
             Image und nicht ins Frontend-Bundle. Der MIT-Code ist kein
             abgeleitetes Werk der Liste (Daten, nicht Code).
             Was fehlt, wissentlich: freie Komposita (hunspell setzt
             Kirchenbuch, Taufschein zur Laufzeit aus Teilen zusammen — die
             Expansion in `tools/lesarten/expand.py` bildet nur die
             Affix-Formen) und Historisches (Muhme, Wittib, gehorsamst) —
             dafür wird die eigene Quiz-Bank (`tools/quizgen/quiz_words.json`)
             unique dazugenommen.
- Retrieved: 2026-08-30 (erhoben = per Skript abrufbar; Abrufdatum des
             lokalen Stands steht im Fetch-Log)

## de_DE_frami.dic — 258 200 Stämme mit Affix-Flags (ISO-8859-1)

- Origin:    https://github.com/LibreOffice/dictionaries/tree/32b006a2c22a4ac7e8ed3f03346f7b3d85a970a4/de
- Direct:    https://raw.githubusercontent.com/LibreOffice/dictionaries/32b006a2c22a4ac7e8ed3f03346f7b3d85a970a4/de/de_DE_frami.dic
- SHA256:    4ca3c958b0e5545910999bc246f668840bf8ede3df8e5e6790d05edd5a586c38
- Processing: unverändert abgelegt; die Expansion (SFX/PFX-Regeln der
             .aff, eine Affix-Schicht; Stämme mit `o` = nur in Komposita und
             `h` = nur mit Affix werden nicht als eigenes Wort gezählt) in
             `tools/lesarten/expand.py`. Gemessen 2026-08-30: 169 751
             eigenständige Buchstaben-Stämme, ≈ 807 000 Formen.

## de_DE_frami.aff — die Affix-Regeln (505 SFX/PFX-Zeilen)

- Direct:    https://raw.githubusercontent.com/LibreOffice/dictionaries/32b006a2c22a4ac7e8ed3f03346f7b3d85a970a4/de/de_DE_frami.aff
- SHA256:    646bf3333ac69c23e9d794533ee5241d6f755c359e8fe10a648f87613743d594

## README_de_DE_frami.txt — Lizenz- und Autorenhinweis

- Direct:    https://raw.githubusercontent.com/LibreOffice/dictionaries/32b006a2c22a4ac7e8ed3f03346f7b3d85a970a4/de/README_de_DE_frami.txt
- SHA256:    c141f4f79c428b7348b5012836f4ad3db4d124f288f15effc22696dc876512ae
