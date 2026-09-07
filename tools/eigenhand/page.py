"""Render the Siebung page — ONE self-contained HTML file for the row review.

humanbench pattern: crops embedded as data: URIs, CSS/JS inline, no network
at view time; resume state saved after every click (localStorage, keyed by a
payload fingerprint so a different import never resumes into this one); the
result is a uid-keyed text file — never joined by order — downloaded from
the page or copied out of the textarea.

The page opens with the header crop next to the EXPECTED sheet id: the
human confirms the match before any verdict (the guard against misfiling a
whole sheet). The Sieb-Disziplin is printed verbatim above the rows.

Every payload string is HTML-escaped and the page uses delegated event
listeners instead of inline handlers, so no word, id or note can break the
markup or smuggle script into the offline page.

    uv run python -m tools.eigenhand.page --hand mn-suetterlin --sheet B0001
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
from pathlib import Path

from tools.eigenhand.store import WORK_DPI, check_crop_name
from tools.eigenhand.store import sheet_dir as store_sheet_dir


REASONS = ("verschrieben", "verrutscht", "Klecks", "sonstiges")

_CSS = """
body { font-family: system-ui, sans-serif; margin: 0; background: #f4f2ec; color: #1a1a17; }
header { padding: 14px 18px; background: #fff; border-bottom: 2px solid #d6d4cb; }
h1 { font-size: 18px; margin: 0 0 6px; }
.confirm { display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }
.confirm img { max-width: 480px; width: 100%; border: 1px solid #d6d4cb; background: #fff; }
.sieb { margin: 10px 18px; padding: 10px 14px; background: #fff8e6; border: 1px solid #e5d9a8; font-size: 14px; }
.row { margin: 14px 18px; padding: 12px; background: #fff; border: 1px solid #d6d4cb; border-radius: 4px; }
.row img { width: 100%; image-rendering: auto; border: 1px solid #eee; background: #fff; display: block; }
/* The detected Fleckenmaske, drawn OVER the crop and never into it: the
   circles ride on an SVG scaled to the strip's own millimetres, so what the
   eye checks here is the same list the workbench's brush later edits. */
.crop { position: relative; }
.crop svg { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
.crop circle { fill: none; stroke: #c0392b; stroke-width: 0.12; opacity: 0.85; }
.flecken { color: #a05a00; font-size: 13px; }
.rowhead { display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap; margin-bottom: 6px; }
.rowhead b { font-size: 15px; }
.qc { color: #a05a00; font-size: 13px; }
.pen { font-size: 12.5px; color: #2c5a2c; background: #eaf3ea; border: 1px solid #cadfca;
  border-radius: 999px; padding: 1px 9px; }
.verdicts { margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
button { font-size: 14px; padding: 6px 12px; border: 1px solid #999; background: #fafafa; border-radius: 4px; cursor: pointer; }
button.on-angenommen { background: #2c7a2c; color: #fff; border-color: #2c7a2c; }
button.on-verworfen { background: #a03030; color: #fff; border-color: #a03030; }
button.on-spaeter { background: #666; color: #fff; border-color: #666; }
.reasons { display: none; gap: 6px; flex-wrap: wrap; }
.reasons.show { display: flex; }
.reasons button.picked { background: #a03030; color: #fff; border-color: #a03030; }
input.note { flex: 1 1 220px; font-size: 13px; padding: 5px; border: 1px solid #bbb; border-radius: 4px; }
footer { margin: 18px; padding: 14px; background: #fff; border: 1px solid #d6d4cb; }
textarea { width: 100%; height: 140px; font-family: ui-monospace, monospace; font-size: 12px; }
.count { font-weight: 600; }
"""

# No inline handlers: verdict/reason clicks and note edits are delegated and
# read their uid from the surrounding row's data attribute — the Python side
# never interpolates strings into JavaScript.
_JS = """
const FP = document.body.dataset.fingerprint;
const KEY = "eigenhand-siebung-" + FP;
let state = {};
try { state = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { state = {}; }
function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} render(); }
function setVerdict(uid, v) {
  const s = state[uid] || {};
  s.verdict = (s.verdict === v) ? null : v;
  if (s.verdict !== "verworfen") s.reason = null;
  state[uid] = s; save();
}
function setReason(uid, r) {
  const s = state[uid] || {}; s.reason = (s.reason === r) ? null : r; state[uid] = s; save();
}
function setNote(uid, text) { const s = state[uid] || {}; s.note = text; state[uid] = s; save(); }
function resultText() {
  const rows = Array.from(document.querySelectorAll(".row"));
  let done = 0; const lines = [];
  for (const row of rows) {
    const uid = row.dataset.uid; const s = state[uid] || {};
    if (!s.verdict) continue;
    done += 1;
    let line = uid + ":" + s.verdict;
    if (s.verdict === "verworfen") line += "#" + (s.reason || "sonstiges");
    // Flattened here rather than in the parser (humanbench page.py does the
    // same): the emitted file has to BE the one-row-per-line format it claims
    // to be. A pasted line break in a remark would otherwise make the whole
    // Siebung unparseable — after the sheet has already been judged.
    if (s.note) line += ' "' + s.note.replace(/\\s+/g, " ").replace(/"/g, "'").trim() + '"';
    lines.push(line);
  }
  const head = "SIEBUNG/1 bogen=" + document.body.dataset.sheet + " geprueft=" + done + " von " + rows.length;
  return head + "\\n" + lines.join("\\n") + (lines.length ? "\\n" : "");
}
function render() {
  for (const row of document.querySelectorAll(".row")) {
    const uid = row.dataset.uid; const s = state[uid] || {};
    for (const b of row.querySelectorAll("[data-verdict]")) {
      b.className = (s.verdict === b.dataset.verdict) ? "on-" + s.verdict : "";
    }
    const reasons = row.querySelector(".reasons");
    reasons.classList.toggle("show", s.verdict === "verworfen");
    for (const b of reasons.querySelectorAll("[data-reason]")) {
      b.classList.toggle("picked", s.reason === b.dataset.reason);
    }
    const note = row.querySelector("input.note");
    if (document.activeElement !== note) note.value = s.note || "";
  }
  document.getElementById("result").value = resultText();
  const total = document.querySelectorAll(".row").length;
  const done = Object.values(state).filter((s) => s && s.verdict).length;
  document.getElementById("count").textContent = done + " / " + total;
}
function download() {
  const blob = new Blob([resultText()], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "siebung-" + document.body.dataset.sheet + ".txt";
  a.click();
}
document.addEventListener("click", (ev) => {
  const target = ev.target;
  if (!(target instanceof Element)) return;
  if (target.closest("#download")) { download(); return; }
  const button = target.closest("button[data-verdict], button[data-reason]");
  if (!button) return;
  const row = button.closest(".row");
  if (!row) return;
  if (button.dataset.verdict) setVerdict(row.dataset.uid, button.dataset.verdict);
  else setReason(row.dataset.uid, button.dataset.reason);
});
document.addEventListener("input", (ev) => {
  const target = ev.target;
  if (!(target instanceof Element) || !target.classList.contains("note")) return;
  const row = target.closest(".row");
  if (row) setNote(row.dataset.uid, target.value);
});
// The pen mark on the sheet IS the writer's own judgement, made right after
// row was written — it seeds the verdict. A stored (clicked) verdict always
// wins, so a correction on screen is never overwritten by a reload.
function seedFromPen() {
  for (const row of document.querySelectorAll(".row")) {
    const uid = row.dataset.uid;
    const pen = row.dataset.pen;
    if (!pen) continue;
    const s = state[uid] || {};
    if (!s.verdict && !s.seeded) {
      s.verdict = pen; s.seeded = true; state[uid] = s;
    }
  }
  try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
}
document.addEventListener("DOMContentLoaded", () => { seedFromPen(); render(); });
"""


def _data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def _png_size_mm(path: Path) -> tuple[float, float]:
    """The crop's size in millimetres, straight out of the IHDR chunk.

    No image library: the page is a rendering step of a tool family that runs
    without one, and the crops come out of `ingest` at exactly `WORK_DPI`.
    """
    header = path.read_bytes()[:24]
    if not header.startswith(b"\x89PNG\r\n\x1a\n") or header[12:16] != b"IHDR":
        raise SystemExit(f"{path} is not a PNG with a leading IHDR chunk")
    scale = WORK_DPI / 25.4
    return (int.from_bytes(header[16:20], "big") / scale, int.from_bytes(header[20:24], "big") / scale)


def _flecken_svg(circles: list[dict], path: Path) -> str:
    """The detected specks as an overlay — a hint for the eye, never a change to the crop."""
    if not circles:
        return ""
    width_mm, height_mm = _png_size_mm(path)
    marks = "".join(
        f'<circle cx="{float(c["x_mm"]):.2f}" cy="{float(c["y_mm"]):.2f}" r="{float(c["r_mm"]) * 2.5:.2f}"/>'
        for c in circles
    )
    return (
        f'<svg viewBox="0 0 {width_mm:.2f} {height_mm:.2f}" preserveAspectRatio="none" aria-hidden="true">{marks}</svg>'
    )


def build_page(payload: dict, import_dir: Path) -> str:
    esc = html.escape  # escapes quotes too — safe for text AND attribute contexts
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    machine_id = esc(f"{payload['hand']}-{payload['sheet']}")

    rows_html = []
    for row in payload["rows"]:
        # A crop name with path components would let a tampered payload embed
        # arbitrary local files into the page.
        crop_name = check_crop_name(row["crop"], row["row_index"])
        attempt = f" · Versuch {row['attempt']}/{row['attempts']}" if row["attempts"] > 1 else ""
        qc = f'<span class="qc">⚠ {esc(", ".join(row["qc"]))}</span>' if row["qc"] else ""
        # Only a tick is a statement from the sheet; an empty box says nothing
        # and seeds nothing (owner, 2026-08-26). Normalised here, so a payload
        # written by the older ingest (`pen_mark: "verworfen"`) can never
        # auto-reject a row through `seedFromPen()`.
        pen = "angenommen" if row.get("pen_mark") == "angenommen" else ""
        pen_chip = '<span class="pen">Stift auf dem Blatt: Haken</span>' if pen else ""
        reason_buttons = "".join(f'<button type="button" data-reason="{esc(r)}">{esc(r)}</button>' for r in REASONS)
        # The detected Fleckenmaske: circled on the crop so the eye can check
        # the finding, and named in the head so a row with specks says so. It
        # changes nothing here — the crop is the captured one, the mask is data
        # (proposal §7.4), and the workbench's brush is where it is corrected.
        specks = list(row.get("flecken") or [])
        speck_note = (
            f'<span class="flecken">● {len(specks)} Fleck(en) erkannt — im Admin-Bereich radierbar</span>'
            if specks
            else ""
        )
        rows_html.append(f"""
<div class="row" data-uid="{esc(row["uid"])}" data-pen="{esc(pen)}">
  <div class="rowhead"><b>{esc(row["strip"])}{attempt}</b> <span>{esc(" · ".join(row["words"]))}</span> {pen_chip} {qc} {speck_note}</div>
  <div class="crop">
    <img src="{_data_uri(import_dir / crop_name)}" alt="{esc(row["strip"])}">
    {_flecken_svg(specks, import_dir / crop_name)}
  </div>
  <div class="verdicts">
    <button type="button" data-verdict="angenommen">Annehmen</button>
    <button type="button" data-verdict="verworfen">Verwerfen</button>
    <button type="button" data-verdict="spaeter">Später</button>
    <div class="reasons">{reason_buttons}</div>
    <input class="note" placeholder="Anmerkung (optional)">
  </div>
</div>""")

    apply_cmd = esc(
        f"uv run python -m tools.eigenhand.apply --hand {payload['hand']} "
        f"--sheet {payload['sheet']} siebung-{payload['sheet']}.txt"
    )
    haken_cmd = esc(
        f"uv run python -m tools.eigenhand.apply --hand {payload['hand']} --sheet {payload['sheet']} --haken"
    )
    return f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Siebung {machine_id}</title><style>{_CSS}</style></head>
<body data-sheet="{esc(payload["sheet"])}" data-fingerprint="{fingerprint}">
<header>
  <h1>Siebung · {machine_id}</h1>
  <div class="confirm">
    <img src="{_data_uri(import_dir / "header.png")}" alt="Bogen-Kopf">
    <div>Erwartet: <b>{machine_id}</b> — stimmt die Bogen-ID im Kopf? Wenn nicht: abbrechen,
    richtigen Bogen mit <code>--sheet</code> angeben.</div>
  </div>
</header>
<div class="sieb"><b>Vom Blatt übernommen:</b> Haken im Kästchen am rechten Rand → angenommen
(vorbelegt, überschreibbar). Ohne Haken zählt die Zeile nicht — sie bleibt offen und kommt auf dem
nächsten Bogen wieder; <i>Verwerfen</i> nur, wenn du einen Fehler festhalten willst.<br>
<b>Sieb-Disziplin:</b> Verworfen wird nur nach Schreibqualität (verschrieben,
verrutscht) — nie, weil Buchstaben eng am Nachbarn sitzen. Enge Verbindung ist Signal, nicht
Müll. Ausfälle müssen zufällig sein, nicht selektiv.</div>
{"".join(rows_html)}
<footer>
  <div>Beurteilt: <span id="count" class="count">0 / 0</span></div>
  <p>Normalfall — nur die Haken vom Blatt verbuchen, ohne diese Seite:<br>
  <code>{haken_cmd}</code></p>
  <p>Nur wenn du hier ausdrücklich verworfen oder Anmerkungen gesetzt hast: Ergebnis herunterladen
  und einspielen mit:<br>
  <code>{apply_cmd}</code></p>
  <button type="button" id="download">Ergebnis herunterladen</button>
  <textarea id="result" readonly></textarea>
</footer>
<script>{_JS}</script>
</body></html>
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--out", type=Path, default=None, help="output HTML (default: <sheet>/import/siebung.html)")
    args = ap.parse_args(argv)

    import_dir = store_sheet_dir(args.hand, args.sheet) / "import"
    payload_path = import_dir / "payload.json"
    if not payload_path.exists():
        raise SystemExit(f"{payload_path} missing — run tools.eigenhand.ingest first")
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    out = args.out or import_dir / "siebung.html"
    out.write_text(build_page(payload, import_dir), encoding="utf-8")
    print(f"wrote {out} — open in a browser (offline), judge, download the result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
