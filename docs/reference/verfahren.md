# Verfahrensseiten: die Tintenfolger-Routen und ihre Versionen

> **Status (2026-08-18): lebend.** Übersicht und Versions-Konvention der
> Duell-Verfahren; je stehendem Verfahren existiert eine eigene Seite
> (unten). Nachzieh-Pflicht: Jeder §14-Eintrag, der einen Arm oder eine
> Stufe eines Verfahrens misst (adoptiert ODER verworfen), ergänzt im
> selben PR die Ledger-Zeile der betroffenen Verfahrensseite und — bei
> Adoption — deren „Aktueller Stand“.

Die Tintenfolger-Kampagne ([`../proposals/tintenfolger.md`](../proposals/tintenfolger.md))
lässt mehrere Verfahren gegeneinander antreten; ihre Historie wächst als
datierte Einträge in [`qualitaetsmetrik.md`](qualitaetsmetrik.md) §14.
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

| Anzeige-Name | Seite | Stand (2026-08-18, dev-19, §14 „Re-Baseline aug17“ ff.) |
|---|---|---|
| **Kette** | [`verfahren-kette.md`](verfahren-kette.md) | **v3** (`aug19`, Assembly-Ordnung + Trace-Reparatur) — dtw 0,0491 med · p90 0,089 · worst muß 0,110 · marks 0 |
| **Lotse** | [`verfahren-lotse.md`](verfahren-lotse.md) | v0.13-Stand — dtw 0,0585 med · p90 0,113 · Netto-Kreuzungsdefekte 6 (missing 1) · Kreuzungs-Ortsfehler 0,066 xh · aiou 0,740 |
| **InkSight** | [`verfahren-inksight.md`](verfahren-inksight.md) | T0 (roh) — dtw 0,0951 med · 5/19 failed · Galoppieren-B2-Kollaps |
| **Nullprobe** | [`verfahren-nullprobe.md`](verfahren-nullprobe.md) | unversioniert (Kontrolle) — dtw 0,619 med |

Geplante Verfahren (Zögling · Vier Augen · Chor) haben noch keinen
Kandidaten und darum keine Seite — ihr Stand wohnt in der
Duell-Namen-Tabelle (tintenfolger.md §7.8, Glossar „Duell-Namen“);
die erste Vorregistrierung eines solchen Verfahrens legt seine Seite
im selben PR an.
