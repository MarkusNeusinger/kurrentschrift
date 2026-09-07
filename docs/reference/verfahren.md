# Verfahrensseiten: die Tintenfolger-Routen und ihre Versionen

> **Status (2026-09-01): lebend.** Übersicht und Versions-Konvention der
> Duell-Verfahren; je stehendem Verfahren existiert eine eigene Seite
> (unten). Nachzieh-Pflicht: Jeder §14-Eintrag, der einen Arm oder eine
> Stufe eines Verfahrens misst (adoptiert ODER verworfen), ergänzt im
> selben PR die Ledger-Zeile der betroffenen Verfahrensseite und — bei
> Adoption — deren „Aktueller Stand“ sowie die Stand-Spalte unten.
> Seit 2026-09-01 ist das ein CI-Gate: `uv run python -m
> tools.docs_register check` verlangt für jeden §14-Eintrag einer
> Duell-Route die Ledger-Zeile seines Datums auf der zugehörigen Seite
> (Job „Docs-Register“). Die Spalte **seit** hält fest, wann der
> ausgewiesene Stand adoptiert wurde — ein Blick auf die Seite genügt
> damit für den Abgleich.

Die Tintenfolger-Kampagne ([`../proposals/tintenfolger.md`](../proposals/tintenfolger.md))
lässt mehrere Verfahren gegeneinander antreten; ihre Historie wächst als
datierte Einträge in [`messjournal.md`](messjournal.md) §14.
Diese Seiten sind das **Register darüber**: je Verfahren ein Steckbrief
(was es ist, wo es wohnt, was heute adoptiert ist) plus ein
**Versions-Ledger** (welcher Arm wann gemessen wurde, mit welchem
Verdikt). Die Seiten tragen KEINE eigenen Zahlen-Wahrheiten — jede
Zahl hier ist ein datiertes Zitat, der Beleg wohnt im benannten
§14-Eintrag. Wer eine Zahl prüfen oder fortschreiben will, geht dorthin.

## Die Versions-Konvention

1. **Eine Versionsnummer je vorregistriertem Arm eines Verfahrens** —
   so, wie die Lotse-Praxis sie etabliert hat (v0.1 … v0.9): Die Nummer
   entsteht mit der Vorregistrierung, VOR der ersten Zahl, und bleibt
   auch bei einem Verwerfen stehen (ein verworfener Arm ist Teil der
   Historie, keine Lücke).
2. **Der STAND eines Verfahrens ist die Menge seiner adoptierten
   Mechanismen/Konstanten** — das, was ein Bench-Lauf mit committeten
   Konstanten produziert und die Duell-Seite zeigt. Verworfene
   Versionen ändern den Stand nicht.
3. **Keine rückwirkende Umnummerierung.** Die historischen Namen
   (die Folger-Arme ①–⑨, die Wellen-Maßnahmen K1/K1b/A1/B1/P1–P3)
   bleiben in Code und datierten §14-Einträgen unverändert — das
   Register listet sie unter ihren Namen. Verfahren, deren Historie
   vor dieser Konvention lag (die Kette), beginnen bei ihrem heutigen
   Stand (v1) und zählen ab jetzt nur bei ADOPTIERTEN
   Formulierungsänderungen hoch.
4. **Lineal-Versionen sind getrennt.** Die Strukturzähler-Stände
   v1/v2/v2.1 (und jede künftige Lineal-Re-Baseline) gehören dem
   Bench, nicht einem Verfahren — sie stehen ausschließlich in §14.
5. **Die Nullprobe hat bewusst keine Versionen** — die Kontrolle wird
   grundsätzlich nicht optimiert (tintenfolger.md §7.6); genau das
   dokumentiert ihre Seite.

## Die Verfahren

| Anzeige-Name | Seite | Stand (2026-09-07, dev-19, Lineal-Kappe 1,5 seit L-U `aug26`) | seit |
|---|---|---|---|
| **Kette** | [`verfahren-kette.md`](verfahren-kette.md) | **v5** (`aug26`, K0-S-Wächter-Stack: Kompositions-Soll + Ratsche + Zone 0,55) — Zahlen re-baselined `sep07` auf der Wurzel `ccb036a5eb20…` (nach dem Komma-Ausschluss; ziffernweise wie die A37-Nachmessung auf `eaa195aa7c84…`): dtw 0,045881 med · p90 0,088356 · worst `muß` 0,106372 · marks 0 · aiou 0,7660 · Netto-Kreuzungsdefekte 20 · 63er-Soll-Abstand 85 | 2026-08-26 (Zahlen 2026-09-07) |
| **Lotse** | [`verfahren-lotse.md`](verfahren-lotse.md) | **v0.17** (`aug20`, Reservierungs-Veto) — Zahlen nachgemessen `sep07` auf derselben Wurzel wie die Kette (`ccb036a5eb20…`), die seit A37 fällige Karten-Nachmessung: dtw **0,053386** med · p90 0,116668 · aiou 0,7473 · `cross_missing` 0 / `cross_spurious` 4 · `retrace_missing` 5. Die `sep05`-Zeile nannte 0,053393 / 0,116199 / 0,7493 — dieselbe Route, vor A37 (§14 „Komma-Ausschluss `sep07`") | 2026-08-20 (Zahlen 2026-09-07) |
| **InkSight** | [`verfahren-inksight.md`](verfahren-inksight.md) | T0 (roh) — dtw 0,0951 med · 5/19 failed · Galoppieren-B2-Kollaps; **auf Lineal-Kappe 1,5 unvermessen**, die Zahlen sind archiviert und nicht vergleichbar | 2026-08-17 (Lineal 0,8) |
| **Nullprobe** | [`verfahren-nullprobe.md`](verfahren-nullprobe.md) | unversioniert (Kontrolle) — dtw 0,8198 med · p90 1,0267 auf den 10 von 19 dev-Wörtern, die die gespeicherte Nullprobe abdeckt | 2026-08-26 |

Geplante Verfahren (Zögling · Vier Augen · Chor) haben noch keinen
Kandidaten und darum keine Seite — ihr Stand wohnt in der
Duell-Namen-Tabelle (tintenfolger.md §7.8, Glossar „Duell-Namen“);
die erste Vorregistrierung eines solchen Verfahrens legt seine Seite
im selben PR an.
