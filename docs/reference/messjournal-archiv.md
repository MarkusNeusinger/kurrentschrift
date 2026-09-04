# Messjournal-Archiv — abgeschlossene Arme

> **Status (2026-09-04): lebend.** Der abgelegte Teil des
> [Messjournals](messjournal.md). Nachzieh-Anlass: ein Abschnitt zieht
> hierher, sobald sein Arm abgeschlossen ist (die drei Bedingungen
> unten); seine Registerzeile bleibt im Journal stehen und zeigt ab dann
> hierher. **Stand 2026-09-04: noch kein Eintrag.**

Das Journal wächst mit jeder Runde, und die meisten Abschnitte sind nach
ihrem Verdikt fertig — sie werden nachgeschlagen, nicht fortgeschrieben.
Damit die eine Datei, die eine Runde anfasst, nicht ewig weiterwächst,
ziehen fertige Abschnitte hierher.

**Die drei Bedingungen, alle zusammen.** Ein Abschnitt gilt als
abgeschlossen, wenn

1. sein **Verdikt gebucht** ist (adoptiert · nicht adoptiert · verworfen
   · gegenstandslos · geschrieben — das Vokabular des Registers),
2. seine **Rettungswege** in
   [`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) §7.9
   stehen, sofern er als ehrliches Negativ geschlossen hat, und
3. er seit mindestens **vier Wochen unberührt** ist: kein neuer Nachtrag,
   kein Arm, der ihn wieder aufnimmt.

**Stand 2026-09-04.** Kein Abschnitt erfüllt (3): der älteste der
Kampagne trägt `aug14` und ist 21 Tage alt. Die erste Prüfung lohnt am
2026-09-11, dann für den Block `aug14`–`aug16`.

**Wie umgezogen wird.** Wort für Wort, nie umgeschrieben — dieselbe
Regel wie beim Umzug des Journals selbst. Der Abschnitt behält seine
Überschrift und damit seinen Anker; die Registerzeile im Journal bleibt
die eine Zeile je Eintrag und bekommt nur den Dateinamen vor das
`#`-Fragment (`messjournal-archiv.md#anker`). Zitate der Form „§14
«Titel»“ bleiben gültig: das Archiv ist Teil von §14, nur in einer
zweiten Datei. Das Gate
(`uv run python -m tools.docs_register check`) liest beide Dateien und
verlangt für jeden Abschnitt hier dieselbe Registerzeile wie für einen
im Journal.
