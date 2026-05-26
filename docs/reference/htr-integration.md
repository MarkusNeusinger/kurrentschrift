# HTR-Integration

Technische Spezifikation des Recognition-Stacks für Volltext aus Vision §6
(„Lese-Hilfe") und Vision §8 („Lese-Lupe"). Ergänzt
[`architektur.md`](../concepts/architektur.md) §13 und §14.

**Kernprinzip:** kein Eigenbau. „Lesen ist gelöst, keine Forschung"
([`architektur.md`](../concepts/architektur.md) §1).

---

## 1. Default-Pfad: Transkribus Text Recognition API

### API-Endpoints

- `POST /processes` — Job anlegen (Modell-ID + Bild-URL/Base64 + Optionen).
- `GET /processes/{processId}` — Status pollen (PENDING / RUNNING / FINISHED /
  FAILED).
- `GET /processes/{processId}/results` — PAGE-XML, ALTO, TEI, Plaintext.
- Auth: OpenID-Connect-Bearer-Token; pro App-Instanz eine Service-Account-
  Credential.

### Modelle (Auswahl)

| Modell | Trainingsdaten | CER (publiziert) | Engine |
|---|---|---|---|
| **German Kurrent 17th–20th c.** | ~3 Mio. Wörter, gemischt | 5,4 % | PyLaia |
| **German_Kurrent_XIX_pylaia** | 19. Jh., Schwerpunkt | 6,9 % | PyLaia |
| **German Kurrent 17th–18th** | älterer Schwerpunkt | 5,5 % | PyLaia |
| **Swiss German Kurrent 18th** | Schweizer Kanzlei-Hände | 5,9 % | PyLaia |
| **German Genius** (Supermodel) | mehrere Schulen kombiniert | ≈ 5,5 % | PyLaia |

Modellwahl pro Source-Eigenschaft (Jahrhundert, Region) konfigurierbar.
Default: `German Kurrent 17th–20th c.`.

### Kosten

- **Credit-Pack:** 250 Credits = **59,50 €** → 0,238 €/Credit.
- UI: **1 Credit pro Seite Handschrift**.
- **API: 50 % des UI-Preises = ≈ 0,12 €/Seite**.
- 1–4-seitiger Brief: **0,12 – 0,48 €**.

### Latenz

- Queue-basiert, in der Praxis Sekunden bis wenige Minuten pro Seite.
- Interaktiv genug für Vision §6 („Sofort-Nutzen" für Genealogie-
  Zielgruppe).

### Output-Formate

- **PAGE-XML** (Primärformat, interne Repräsentation). TextRegions →
  TextLines → Words mit Polygonen + Baseline + Recognition-Text.
- ALTO 4.2 (Sekundär, für externe Konsumenten).
- TEI (für DH-Konsumenten).
- Plaintext (für simple Anzeige).

---

## 2. Free-Tier-Logik in unserer App

### Quoten-Modell

- **Default-Quote:** 5 Seiten pro Nutzer pro Monat (Gelegenheitsnutzer).
- **Power-User:** Anlegen eigener Transkribus-Credentials in
  Account-Settings → unbegrenzt auf eigene Kosten.
- **Anonyme Nutzer:** 1 Probe-Seite ohne Account (Demo).

### Rate-Limiter

- FastAPI-Middleware mit Postgres-backed counter pro Nutzer pro Monat.
- Soft-Limit-Warnung bei 80 %, Hard-Stop bei 100 % mit Hinweis auf
  Credit-Kauf-Option.

### Caching

- PAGE-XML-Cache pro Bild-Hash (SHA-256 des Bytes).
- Gleicher Brief, gleiche Modellwahl → Cache-Hit, kein Doppel-Bezug von
  Credits.
- Cache liegt in Postgres als JSONB-Spalte auf `transcriptions`-Tabelle
  (kommt mit P1-Implementierung).

---

## 3. Optionaler Self-Hosted-Pfad (post-MVP)

### TrOCR `dh-unibe/trocr-kurrent`

- Universität Bern, HuggingFace.
- **CER: 2,65 %** (publiziert) — deutlich besser als die öffentlichen
  Transkribus-Modelle.
- Transformer-basiert (ViT + GPT2-style decoder).
- Inferenz pro Zeile: ~600 ms auf V100 GPU; **~1–3 s auf modernem CPU**.
- Modell-Größe: ~558 MB (TrOCR-large) bzw. ~334 MB (TrOCR-base).

### Architektur als Job-System

- **Synchron ist auf CPU nicht tragbar:** 4-Seiten-Brief × 30 Zeilen/Seite ×
  ~2 s/Zeile = 4 Minuten. Daher Job-basiert.
- `POST /htr/jobs` → Job-ID; Frontend pollt Status oder erhält Notification.
- Kein Background-Worker im MVP — kann später mit Celery/RQ/dramatiq
  ausgebaut werden.

### Bild → Linien-Segmentierung davor

Bevor TrOCR auf die Zeilen losgelassen werden kann, muss das Bild in Zeilen
zerlegt werden. Optionen (alle CPU-fähig):

- **Kraken** (kraken.re) — etabliert, PAGE-XML out, gute Doku via UB
  Mannheim eScriptorium.
- **Loghi-Laypa** (knaw-huc/loghi) — KNAW-HuC, Docker-Pipeline.
- **docTR** (mindee/doctr) — Mindee, schlanker und neuer.

**Default-Wahl:** Kraken, weil PAGE-XML-Output direkt mit dem Transkribus-
Pfad kompatibel ist (gleiche interne Repräsentation).

---

## 4. FastAPI-Adapter

### Router `/htr/`

```
POST   /htr/transcribe        # Synchron-Versuch (Transkribus default)
POST   /htr/jobs              # Async-Job anlegen (TrOCR self-hosted)
GET    /htr/jobs/{job_id}     # Status pollen
GET    /htr/quota             # Free-Tier-Stand des aktuellen Nutzers
```

### Backend-Abstraktion

```python
# Pseudo-Code
class HtrBackend(ABC):
    async def transcribe(self, image: bytes, model_id: str) -> PageXml: ...

class TranskribusBackend(HtrBackend): ...  # default
class TrOcrBackend(HtrBackend): ...        # post-MVP, optional
```

Backend-Wahl pro Request über User-Setting oder Server-Default.

### Interne Repräsentation: PAGE-XML

Wir halten *einen* Standard intern. Beide Backends müssen nach PAGE-XML
mappen — bei Transkribus geht das nativ, bei TrOCR brauchen wir eine
PAGE-XML-Konstruktion aus den Linien-Bounding-Boxes (Kraken liefert das)
plus den TrOCR-Texten.

Frontend konsumiert nur PAGE-XML (über Annotorious + `react-iiif-viewer`-
ähnliche Komponente). Andere Formate (ALTO, TEI, Plaintext) werden
on-demand aus PAGE-XML abgeleitet.

---

## 5. Beziehung zur Lese-Lupe (§14)

Die Lese-Lupe konsumiert das **gleiche PAGE-XML**. Wort-Polygone werden als
klickbare Annotorious-Annotations dargestellt. Bei Klick:

1. Wort-Text aus PAGE-XML extrahieren.
2. (Optional, post-MVP) Wort-Region als Crop an die *eigene* Glyph-
   Erkennung schicken (analysis-by-synthesis rückwärts —
   [`architektur.md`](../concepts/architektur.md) §14).
3. Regel-Lookup aus
   [`orthographie-regeln.md`](orthographie-regeln.md) (Daten-konsumierende
   Schicht): „warum sieht das so aus, wie es aussieht".

---

## 6. Was wir nicht machen

- **Eigenes HTR-Modell trainieren.** Trainingsdaten-Sammlung ist nicht im
  Vision-Scope; Vendor-Modelle decken die Reichweite.
- **OCR.space / Google Vision / Azure OCR / AWS Textract.** Diese sind für
  Druckschrift, nicht historische Handschrift — CER wäre katastrophal.
- **Eigenen Layout-Analyzer.** Kraken/docTR sind ausreichend; Layout ist
  kein Forschungs-Hebel für uns.

---

## 7. Quellen

- Transkribus Plans/Pricing: <https://www.transkribus.org/plans>
- Text Recognition API: <https://www.transkribus.org/text-recognition-api>
- metagrapho: <https://www.transkribus.org/metagrapho>
- Credit System: <https://help.transkribus.org/credit-system>
- Public Models (Kurrent):
  <https://app.transkribus.org/models/public/text/german-kurrent-and-sutterlin-17th-20th-century>,
  <https://www.transkribus.org/models/swiss-german-kurrent-18th-century>
- 3 AI-Modelle für deutsche Schrift (Blog):
  <https://blog.transkribus.org/en/3-ai-models-for-transcribing-german-text-in-fraktur-kurrent-and-sutterlin>
- TrOCR Kurrent: <https://huggingface.co/dh-unibe/trocr-kurrent>,
  <https://huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII>
- TrOCR-Paper: <https://arxiv.org/pdf/2109.10282>
- Kraken: <https://kraken.re>
- eScriptorium UB Mannheim (de):
  <https://ub-mannheim.github.io/eScriptorium_Dokumentation/>
- Loghi: <https://github.com/knaw-huc/loghi>
- docTR: <https://github.com/mindee/doctr>
- HTR-Vergleichsstudie 2025:
  <https://link.springer.com/article/10.1007/s42803-025-00100-0>
- PAGE/ALTO-Konverter: <https://github.com/UB-Mannheim/ocr-fileformat>
