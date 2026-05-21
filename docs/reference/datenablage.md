# Datenablage und Quellen-Verlinkung im Repo

Kurzspezifikation zu [`quellen-und-rechte.md`](quellen-und-rechte.md): *wo* Quellen
und Varianten physisch liegen und *wie* verlinkt wird. Variante 0
(Loth 1866) ist die Basis für alle ersten Tests (MVP §8, Testwörter §9).

---

## 1. Trennung Code ↔ Daten

Daten liegen **außerhalb** von `/core`, `/api`, `/app`, `/alembic`
(Naming-Setup §3) in einem eigenen `/data`-Baum. Grund: die MIT-Lizenz
gilt für Code, **nicht** automatisch für Daten — jede Quelle trägt ihre
eigene Lizenz (Quellen-Rechte §5).

```
/data
  DATA_PROVENANCE.md          # Index: jedes Artefakt -> Herkunft + Lizenz
  /sources                    # nur PD/CC0 — darf committet werden
    /loth-1866
      SOURCE.md               # Permalink, Lizenz, Attribution, Abrufdatum
      chart.svg               # die PD-SVG (committet, weil PD)
  /corpora                    # GITIGNORED — nie committen (Größe + Lizenz)
    /zenodo-17252677
      SOURCE.md               # committet: nur Metadaten, kein Datenfile
      fetch_corpus.py         # lädt v1.0.0 vom DOI-Permalink
  /variants
    /v0-loth-1866             # = canonical-Basis, Variante 0
      README.md               # welche Quelle, welcher Scope
    # spätere Hände: /v1-... (eigener Varianten-Auswahlvektor, Referenz §10)
  /samples
    /own-hand                 # eigene Schreibvorlagen (dein Copyright)
      lesen.png  das.png      # Testwörter §9
  /derived                    # extrahierte Statistik
    /from-cc-by               # committet OK (CC-BY/CC0-Anteil + Attribution)
    /from-nc-sa               # GITIGNORED — lokal/look-only, nie committen
```

Drei Committ-Klassen, scharf getrennt:

- `/sources`, `/samples/own-hand` → committet (PD bzw. eigenes Copyright).
- `/corpora` → **gitignored**. Nur `SOURCE.md` + `fetch_corpus.py`
  committet, nie das 7,8-GB-Datenfile. Skript-Download ändert keine
  Lizenz (Quellen-Rechte §7) — der Grund ist Größe + Reproduzierbarkeit
  über die gepinnte DOI-Version, kein Schlupfloch.
- `/derived` → committet **nur** aus dem CC-BY-4.0/CC0-Anteil. Was aus
  dem NC-SA-Subkorpus stammt, bleibt in `/derived/from-nc-sa` und ist
  gitignored — sonst NC/SA-Kollision mit MIT.

Süß erscheint **nirgends** als Datei — nur als Literaturzeile in
README/Quellen (Quellen-Rechte §1).

---

## 2. `SOURCE.md` pro Quelle (Pflichtfelder)

Eine Datei je Quelle unter `/data/sources/<id>/SOURCE.md`:

```markdown
# Source: loth-1866

- Title:        Deutsche Kurrentschrift (aus „Der Damen-Briefsteller")
- Author:       Johann Thomas Loth (zugeschrieben)
- Year:         1866
- File in repo: chart.svg  (redrawn SVG, not a scan)
- Origin URL:   https://commons.wikimedia.org/wiki/File:Deutsche_Kurrentschrift.svg
- License:      Public Domain (PD-old / Public Domain Mark 1.0)
- Attribution:  Vektorisierung: AndreasPraefcke, Wikimedia Commons
- Retrieved:    2026-05-19
- Note:         Original 1866 gemeinfrei; SVG ist Neuzeichnung,
                kein Reproduktionsfoto -> §72 UrhG unkritisch.
```

`DATA_PROVENANCE.md` ist nur der **Index** darüber (eine Tabellenzeile
pro Artefakt, verweist auf das jeweilige `SOURCE.md`).

Für ein **Korpus** (gitignored, nur Metadaten committet) zusätzlich die
gemischte Lizenz explizit pro Teilkorpus:

```markdown
# Source: zenodo-17252677  (NOT committed — fetched by fetch_corpus.py)

- Title:       HTR Set German Kurrent 19th c.
- Creator:     Myriam Gantner, TU Wien
- DOI:         10.5281/zenodo.17252677   (pin: v1.0.0)
- Origin URL:  https://zenodo.org/records/17252677
- Retrieved:   2026-05-19
- License (per subcorpus):
    - DTA subset .............. CC BY 4.0      -> derived/ committable
    - Digitale Schriftkunde images ... CC0     -> committable
    - Digitale Schriftkunde transcr .. CC BY-NC-SA 4.0 -> NC-SA, do NOT commit derivatives
    - Senatsprotokolle ........ CHECK ubtue/Ground-Truth repo license
- Commit rule: only /derived/from-cc-by may be committed.
```

---

## 3. Verlinkungsregel

- **PD-Quelle (Loth, Faulmann, Keferstein):** Datei *darf* im Repo
  liegen — zusätzlich immer `Origin URL` als stabiler Permalink im
  `SOURCE.md`. Original referenzieren, nicht nur die Repo-Kopie.
- **Website:** die PD-SVG darf gezeigt werden, mit sichtbarer
  Attribution + Link auf die Commons-Quelle.
- **Geschütztes (Süß):** nur bibliografische Referenz im Text. Kein
  Link auf einen Scan, kein Embed, keine abgezeichnete Tafel.
- **Eigene Hand:** als solche kennzeichnen („author's own hand") — die
  stärkere Portfolio-Story (Naming-Setup §3).

---

## 4. Konsequenz für die ersten Tests

- Variante 0 = `v0-loth-1866`. Daraus die **Geometrie** für `canonical`;
  der Ductus-Prior wird selbst darübergelegt (Referenz §2 — Bild liefert
  Geometrie, nicht Strichreihenfolge).
- MVP §8 (6-Buchstaben-Kern-Alphabet, sieben Wörter + ein
  generalisierendes Wort, drei Validierungs-Gates): gegen `own-hand`
  fitten, Formreferenz = Loth 1866. Rechtlich vollständig sauber, da
  PD + eigene Hand.
- Testwörter §9 (Pflicht-Anker `lesen`, `das` + Coverage-Wörter `den`,
  `lese`, `lasen`, `als`, `dann` + Generalisierungs-Wort `denen`)
  liegen unter `/samples/own-hand` und hängen an Variante 0.
- Spätere historische Hände = neue `/variants/vN-...` über demselben
  Kanon (Varianten-Auswahlvektor, Referenz §10) — gleiche Ablage- und
  Lizenzregel, kein Sonderfall.
- **Erste Statistik (§6):** zuerst eigene Hand (Glyph 20–30× → Streuung),
  null Lizenzrisiko. Echte historische Varianz erst danach aus dem
  Zenodo-Korpus, und nur der CC-BY/CC0-Anteil committet — pro Hand
  gerechnet, nicht über Hände gemittelt (Konsistenz-Prior, Referenz §7).
