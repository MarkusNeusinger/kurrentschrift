# Corpus: frequencywords-2018

- Title:     FrequencyWords — Frequenzlisten aus OpenSubtitles2018
             (Hermit Dave), Teilmengen Deutsch 50k und Englisch 50k
- Author:    Hermit Dave (Listen); zugrunde liegendes Korpus:
             OpenSubtitles2018 via OPUS (P. Lison & J. Tiedemann 2016,
             „OpenSubtitles2016: Extracting Large Parallel Corpora from
             Movie and TV Subtitles", LREC)
- Year:      2018 (Korpusstand), Listen-Repo fortlaufend
- License:   Repo MIT; die Listen sind abgeleitete Datenbanken aus dem
             OPUS-OpenSubtitles-Korpus (Attribution erbeten)
- License-Rationale: Frequenzlisten sind in der EU als Datenbanken
             schutzfähig (quiz-wortbank.md §4); die Rechtekette der
             Untertitel-Quelle ist nicht restlos klärbar. Darum
             KONSULTATIONS-QUELLE: die Bytes bleiben gitignored
             (`/data/corpora/**`), die daraus berechnete Gewichtstabelle
             (Übergangsraum) wird nie committet. Committet ist nur der
             eigene, lediglich informierte Wortvorrat (eigene Auswahl,
             eigene Glossen) in `tools/eigenhand/corpus.py` — eigene
             Schöpfung unter Repo-Lizenz. Gleiches Vertrauensmodell wie
             `quiz_words.json` (eingefrorener Output ohne committete
             Ableitungs-Inputs).
- Nachtrag 2026-08-26 (Autor-Entscheid 2026-08-25): die Gewichtstabelle
             darf neben der lokalen Kopie (`data/samples/own-hand/
             universe/uebergangsraum.json`) auch in der PRIVATEN, geteilten
             Datenbank liegen (`eigenhand_uebergangsraum`, Push mit
             `tools.eigenhand.universe --push`). „Nie committet" war eine
             Aussage über das REPO, nicht über den Speicherort: Repo und
             DB sind beide nicht öffentlich, der Unterschied ist der Ort,
             nicht die Rechtslage. Was sich bewegt, ist ein abgeleitetes
             Aggregat (~1 300 Zahlen Item → Summengewicht, mit den
             Listen-Prüfsummen als Provenienz), keine wesentliche
             Entnahme der Liste; es bleibt admin-gesichert, hat keinen
             öffentlichen Endpunkt und gehört NICHT zu einer späteren
             Ziel-7-Veröffentlichung (quellen-und-rechte.md §5). Die
             Korpus-Bytes selbst bleiben, wo sie sind: gitignored, nie in
             der DB.
- Retrieved: 2026-08-22 (erhoben = per Skript abrufbar; Abrufdatum des
             jeweiligen lokalen Stands steht im Fetch-Log)

## de_50k.txt — 50 000 Zeilen `wort anzahl`

- Origin:    https://github.com/hermitdave/FrequencyWords
- Direct:    https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/de/de_50k.txt
- SHA256:    d9e50546fd7e8b6fe6542a2b33c51d1331092b2a3916ec09f80d97856068705b
- Processing: unverändert abgelegt; Auswertung (Filter auf reine
             Buchstabenwörter, Shaping, Gewichtssummen) erst in
             `tools/eigenhand/universe.py`. Die Liste ist durchgehend
             kleingeschrieben — Versal-Übergänge betreten den
             Übergangsraum deshalb über den kuratierten Wortvorrat,
             nicht über dieses Korpus (universe.py-Docstring).
- Note:      Modernes Hochfrequenz-Deutsch (Untertitel-Register). Die
             historische Schicht kommt nicht von hier, sondern über die
             era-getaggten Wortvorrat-Einträge (Kaeding 1897/98 nur als
             Literatur-Konsultation, siehe quiz-wortbank.md).

## en_50k.txt — 50 000 Zeilen `wort anzahl`

- Direct:    https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/en_50k.txt
- SHA256:    5351ff405b1126ef555791dd4d9798a48e3e9a501a9fc481a9da957752cfb458
- Processing: wie oben; im Übergangsraum mit dem Faktor `EN_WEIGHT`
             gedämpft (hauptsächlich Deutsch, Englisch als getaggter
             Anteil — Owner-Entscheidung 2026-08-22).
- Note:      Englische Hochfrequenzliste für die `lang: en`-Einträge und
             die englischen Selten-Join-Kandidaten.
