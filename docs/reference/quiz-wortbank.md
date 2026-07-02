# Quiz-Wortbank — Quellen, Kuration, Distraktoren

Referenz für die Wortbank des Lese-Quiz (Wörter-Modus): woher die Wörter
kommen, nach welchen Regeln sie kuratiert werden und wie die
Antwortoptionen entstehen. Implementiert in `tools/quizgen/` (Generator),
`quiz_words`-Tabelle (Seed über Alembic 0010/0011, öffentlich unter
`GET /quiz-words`) und `useQuizEngine.ts` (Runtime-Ziehung); der
SPA-Fallback ist `app/src/sections/quiz/wordBank.ts`.

Stand 2026-07-02: ~500 Wörter, ca. 60 % `modern` / 40 % `historic`.

---

## 1. Die Mischung „modern + um 1900“

Die Bank mischt zwei Hälften, jedes Wort trägt ein `era`-Tag:

- **`modern`** — hochfrequenter Alltagswortschatz. Der Glücksfall der
  Domäne: die klassische Häufigkeitsstatistik von **Kaeding (1897/98,
  ~11 Mio. ausgezählte Wörter)** ist *Sprache von genau um 1900* — ihr
  Grundwortschatz ist gleichzeitig „modern häufig“ und zeitgenössisch
  zur Kurrent-Ära. Kurze, gut lesbare Wörter bevorzugt (Grundwortschatz-
  Niveau), denn das Quiz will Buchstabenformen prüfen, nicht Vokabeln.
- **`historic`** — Wortschatz alter Briefe, der aus der Alltagssprache
  verschwunden ist, aber in genau den Dokumenten wiederkehrt, für die
  diese App existiert. Gemint aus den genealogietypischen Feldern:
  Anreden/Kurialien (Wohlgeboren, ergebenst), Grußformeln (verbleibe,
  gehorsamst), Verwandtschaft (Muhme, Base, Oheim, Wittib), Berufe und
  Stände (Tagelöhner, Häusler, Büttner, Magd), Haus & Hof (Stube,
  Zuber, Webstuhl), Zeit (Hornung, weiland, alsbald), Kirche/Krankheit/
  Tod (Taufe, Schwindsucht, Begräbnis), Geld/Amt/Recht (Taler, Zehnt,
  Obrigkeit, Mitgift). **Jedes historische Wort trägt eine `note`** —
  eine deutsche Glosse, die erst in der Auflösung gezeigt wird, damit
  sie die Frage nicht verrät (der Generator erzwingt das).

### Konsultierte Quellen

Die Listen dienen als *Referenz für die eigene Kuration*; committet
wird keine davon (siehe §4).

- Kaeding-Häufigkeitsstatistik 1897/98, via
  [Wikipedia: Liste der häufigsten Wörter der deutschen Sprache](https://de.wikipedia.org/wiki/Liste_der_h%C3%A4ufigsten_W%C3%B6rter_der_deutschen_Sprache)
- [Grundwortschatz 100/200/500](https://lernkarteien.de/grundwortschatz/grundwortschatz-500/)
  (Schul-Kernwortschatz) — kurz, lesbar, quiztauglich
- Leipzig Corpora / Wortschatz-Portal der Uni Leipzig und DWDS —
  Gegenprüfung aktueller Häufigkeit
- Genealogie-Felder: [altdeutsche-schrift.com — Beispiele alter Briefe](https://altdeutsche-schrift.com/en/old-german-examples/letters/),
  [Wikipedia: Kurialien](https://de.wikipedia.org/wiki/Kurialien),
  [Titulaturen und Anreden um 1900](http://www.juedischer-adel.de/titulaturen-und-anreden/)
- [Wikipedia: Langes s](https://de.wikipedia.org/wiki/Langes_s) — die
  ſ/s-Regel hinter den Fugen-Markern (§3)

## 2. Distraktoren: ein Anker gepinnt, der Rest zur Laufzeit

Ziel: ein falscher Klick ist eine *plausible Fehllesung*, keine
Schludrigkeit — und die vier Optionen wechseln von Runde zu Runde.

- **Gepinnt (im Seed):** pro Wort genau **ein** handkuratierter
  Distraktor (`distractors` in `quiz_words`), die beste Fehllesung oder
  ein bewusst thematischer Anker (Sonntag für Donnerstag). Pins gelten
  verbatim und dürfen die Ähnlichkeitsregeln biegen.
- **Zur Laufzeit (Engine):** `buildWordChoices` bietet immer einen Pin
  an und zieht die restlichen Slots aus der *gesamten* Bank — bewertet
  mit `similarity()`, gewichtet nach Score, mit Zufall ohne Zurücklegen.
  Starke Verwechslungen kommen öfter, schwache bleiben möglich; bei zu
  wenigen Nahformen füllt die Bank zufällig auf.

Die `similarity`-Regeln (Zwillinge: `tools/quizgen/similarity.py` ↔
`wordBank.ts`, synchron halten!):

1. echtes Wort, gleiche Groß-/Kleinschreibung, ≠ Lösung;
2. Länge ±1;
3. gemeinsamer Anfangs- *oder* Endbuchstabe;
4. positionsgleiche Abweichungen sind Kurrent/Sütterlin-Verwechsler
   (e↔n, n↔u, u↔a, n↔m, m↔w, h↔k, h↔b, b↔l, k↔l, f↔s/ſ, c↔e, r↔x, g↔z,
   i↔e, t↔l) — belohnt; beliebige Buchstabentausche — bestraft.

Regel für Pins mit innerem Morphem-s: ein Pin wie `Haustor` würde im
Vergleich falsch (`Hauſtor`, ſt-Ligatur) gerendert, weil nur
Bank-Einträge einen `fugen`-Marker tragen können. Also: **Pins mit
Fugen-s/Präfix-s müssen selbst Bank-Einträge mit Marker sein — oder
werden vermieden.**

## 3. Fugen-Marker (`fugen`)

Die Shaping-Regel setzt langes ſ automatisch überall außer am Wortende.
Das ist innerhalb eines Morphems korrekt (`Fenſter`, `Weſpe`, `einſt`),
liegt aber bei Komposita, Präfix- und Suffixgrenzen falsch
(`Donnerstag`, `Ausgang`, `Häuslein`): dort muss das Fugen-/Silbenend-s
rund bleiben. Solche Wörter tragen `fugen` mit `|` an der
Morphemgrenze (`Donners|tag`, `Aus|gang`, `Häus|ler`); `word` bleibt
die saubere Anzeigeform. Beim Erweitern der Bank jedes Wort mit
innerem s prüfen — der Generator kann die Morphemgrenze nicht raten.

## 4. Lizenz-Haltung

Konsistent mit [Quellen- und Rechte-Policy](quellen-und-rechte.md) und
[Datenablage](datenablage.md): Frequenz*listen* sind in der EU als
Datenbanken schutzfähig, und verbreitete Listen (Wortschatz Leipzig,
SUBTLEX-DE) tragen NC-Lizenzen — **keine dieser Listen wird ins Repo
committet.** Einzelne Alltagswörter sind nicht schutzfähig; die Bank in
`tools/quizgen/corpus.py` ist eine eigene, von den genannten Quellen
nur *informierte* Kuration (eigene Auswahl, eigene Glossen, eigene
Distraktoren) und damit eigene Ausdrucksform unter der Repo-Lizenz.

## 5. Workflow beim Erweitern

1. `tools/quizgen/corpus.py` editieren (Pin-Regeln §2, Fugen-Check §3,
   historisch ⇒ `note`).
2. `uv run python -m tools.quizgen.build` — regeneriert
   `quiz_words.json` deterministisch; `--check` ist der CI-Gate
   (`tests/test_quizgen.py`).
3. Bereits migrierte Datenbanken behalten ihre Zeilen: eine neue
   Re-Seed-Migration nach dem Muster von `0011_quiz_words_reseed.py`
   anlegen (Tabelle leeren, aus dem committeten JSON neu einspielen).

## Verworfen

- **Drei fest gespeicherte Distraktoren pro Wort** (Stand bis #148):
  erzeugt bei kleiner Bank immer dieselben Optionen; Variation gehört
  in die Laufzeit-Ziehung, nicht in den Seed. Der Seed pinnt nur noch
  den einen Anker.
- **Frequenzlisten als Dateien committen:** NC-Lizenzen bzw.
  Datenbankschutz kollidieren mit dem MIT-Repo; Listen bleiben
  Referenz, die Kuration ist die eigene Ausdrucksform (§4).
- **ſ/s im `word` kodieren:** die Allographen setzt das Shaping
  automatisch; nur Morphemgrenzen brauchen den `fugen`-Marker
  (Entscheidung aus dem Wortmodus-PR, bestätigt hier).
