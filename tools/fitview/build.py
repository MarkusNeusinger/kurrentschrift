"""Build the fitview comparison page — see the package docstring.

Selection: the judged screens of `data/humanbench/runde-<n>-urteile.txt`, read
with their committed slim keys (`runde-<n>-vorkommen.json`, record format in
`data/humanbench/SOURCE.md`). Blind repeats are deduplicated on the occurrence
identity (glyph, word, slot) — the panel header lists every uid and its own
category string, because two judgements of one occurrence are two data points.

Fitting mirrors `tools.pairlab.bindab`: compose the fixture case once
(`derive_word`), take the per-slot grid windows (`_grid_fits`), fit every
chainable run that contains a judged slot as ONE chain
(`fit_word_chain(..., keep_solve=True)`), and read the letter's anchors off the
solved problem in crop pixels exactly as `bindab.off_ink_share` does — the
ANCHOR positions via `x_origin_px`/`baseline_y_px`/`unit_px`, never
`problem.to_pixels` (that is the sample row). The repair runs on the letter
slice of `problem.free_anchors(params)` (units) with the stroke starts of that
letter's `ChainSegmentSpec`, so a pen lift is never bridged.

The panel frame replicates `tools.humanbench.build`: window from the letter's
own points padded by ``max(6, round(0.4 * xh))`` crop pixels, shown at 4x zoom
(the parameters of both archived rounds, see `runde-0*-stempel.md`). A clicked
marker ``#x,y`` from a judgement line is drawn as a blue cross at the position
that frame math implies.
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from tools.laufform.harvest import _chainable_runs, _grid_fits
from tools.pairlab.anchors import repair_stranded_anchors
from tools.pairlab.chain import fit_word_chain
from tools.wordlab.cases import WordCase, iter_fixture_word_cases
from tools.wordlab.derive import derive_word


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "humanbench"

# The frame both archived rounds were judged in (runde-01/02-stempel.md): the
# crop window is padded proportionally to the x-height and shown at 4x zoom.
ZOOM = 4
PAD_XH = 0.4

ROUNDS = ("01", "02")
STYLE = "suetterlin"
# Judged specimens live in the words set; a handful are Abb.-20 pair drills,
# which freeze into the sibling pairs root — both are searched, id-keyed.
FIXTURE_SETS = ("words", "pairs")

# One result line of the befund page: `<uid>:<categories>[#x,y][@Ns][ "note"]`.
JUDGEMENT_RE = re.compile(
    r'^(?P<uid>[SR]\d+):(?P<cats>[GAWBEKU]+)(?:#(?P<mx>\d+),(?P<my>\d+))?(?:@\d+s)?(?:\s+"(?P<note>.*)")?$'
)

COLOR_BEFORE = (204, 34, 34)  # red — the fit as-is
COLOR_AFTER = (26, 127, 55)  # green — with the stranded-anchor repair
COLOR_MARKER = (21, 101, 192)  # blue — the owner's clicked marker
COLOR_REPAIRED = (230, 81, 0)  # orange — circles on the repaired indices


# ------------------------------------------------------------------ selection


@dataclass
class Judgement:
    """One judged screen, joined with its slim-key row."""

    round_id: str
    uid: str
    categories: str
    marker: tuple[int, int] | None
    note: str | None
    glyph: str
    word: str
    slot: int
    repeat_of: str | None

    @property
    def label(self) -> str:
        return f"{self.round_id}/{self.uid}"


@dataclass
class Occurrence:
    """One judged occurrence — blind repeats merged on (glyph, word, slot)."""

    glyph: str
    word: str
    slot: int
    judgements: list[Judgement] = field(default_factory=list)

    @property
    def sort_key(self) -> tuple[str, str]:
        first = min(self.judgements, key=lambda j: (j.round_id, j.uid))
        return (first.round_id, first.uid)


def parse_round(round_id: str) -> list[Judgement]:
    """Join one round's result lines with its committed slim key."""
    result_path = DATA_DIR / f"runde-{round_id}-urteile.txt"
    key_path = DATA_DIR / f"runde-{round_id}-vorkommen.json"
    key = {row["uid"]: row for row in json.loads(key_path.read_text(encoding="utf-8"))}
    judgements: list[Judgement] = []
    for line in result_path.read_text(encoding="utf-8").splitlines():
        match = JUDGEMENT_RE.match(line.strip())
        if match is None:
            continue  # the BEFUND header and round 2's trailing count block
        uid = match["uid"]
        row = key.get(uid)
        if row is None:
            raise SystemExit(f"runde-{round_id}: uid {uid} has no slim-key entry in {key_path.name}")
        marker = (int(match["mx"]), int(match["my"])) if match["mx"] is not None else None
        judgements.append(
            Judgement(
                round_id=round_id,
                uid=uid,
                categories=match["cats"],
                marker=marker,
                note=match["note"],
                glyph=str(row["glyph"]),
                word=str(row["word"]),
                slot=int(row["slot"]),
                repeat_of=row.get("repeat_of"),
            )
        )
    return judgements


def select_occurrences(judgements: list[Judgement], category: str) -> list[Occurrence]:
    """Occurrences with at least one judgement carrying every requested letter.

    Merging runs over ALL judgements of an identity, so a repeat whose original
    was judged differently still shows both verdicts in the panel header.
    """
    by_identity: dict[tuple[str, str, int], Occurrence] = {}
    for j in judgements:
        occ = by_identity.setdefault((j.glyph, j.word, j.slot), Occurrence(j.glyph, j.word, j.slot))
        occ.judgements.append(j)
    selected = [
        occ for occ in by_identity.values() if any(all(c in j.categories for c in category) for j in occ.judgements)
    ]
    return sorted(selected, key=lambda occ: occ.sort_key)


# -------------------------------------------------------------------- fitting


@dataclass
class SlotFit:
    """The judged letter's anchors off one solved chain, before/after repair."""

    key: str
    before_px: np.ndarray  # (K, 2) crop pixels, the fit as-is
    after_px: np.ndarray  # (K, 2) crop pixels, repair applied
    repaired: list[int]  # anchor indices the repair moved
    stroke_starts: list[int]
    xh: float


def load_cases(wanted_ids: set[str]) -> dict[str, WordCase]:
    """The fixture cases the judged words name, id-keyed, over both sets."""
    cases: dict[str, WordCase] = {}
    for which in FIXTURE_SETS:
        try:
            found = iter_fixture_word_cases(which=which, style=STYLE, only=sorted(wanted_ids))
        except KeyError as exc:
            print(f"WARNING: no {which!r} fixture root — {exc}")
            continue
        for case in found:
            cases.setdefault(case.id, case)
    return cases


def _anchors_px(problem, units: np.ndarray) -> np.ndarray:
    """Anchor UNITS → crop pixels, the way `bindab.off_ink_share` reads them."""
    px = problem.x_origin_px + units[:, 0] * problem.unit_px
    py = problem.baseline_y_px - units[:, 1] * problem.unit_px
    return np.column_stack([px, py])


def fit_judged_slots(case: WordCase, wanted: set[int]) -> tuple[dict[int, SlotFit], dict[int, str]]:
    """Chain-fit every run containing a judged slot; return per-slot results.

    Mirrors `tools.pairlab.bindab._rows_for_arm` at the baseline weight: same
    composition, same grid windows, same solver. Slots that produce no fit come
    back in the error map with the reason instead of crashing the page.
    """
    fits: dict[int, SlotFit] = {}
    errors: dict[int, str] = {}
    try:
        result = derive_word(case)
        grids = _grid_fits(case, result)
    except Exception as exc:  # noqa: BLE001 — one bad case must not end the page
        return {}, dict.fromkeys(wanted, f"derivation failed: {exc}")

    for run in _chainable_runs(case, grids):
        judged = set(run) & wanted
        if not judged:
            continue
        try:
            fit = fit_word_chain(
                case, run, result=result, windows_px={s: grids[s]["window"] for s in run}, keep_solve=True
            )
        except Exception as exc:  # noqa: BLE001
            errors.update(dict.fromkeys(judged, f"chain fit raised: {exc}"))
            continue
        if fit is None:
            errors.update(dict.fromkeys(judged, f"chain fit returned None for run {run}"))
            continue
        problem, params = fit.problem, fit.params
        free = problem.free_anchors(params)
        letters = [seg for seg in fit.segments if seg.kind == "letter"]
        specs = [s for s in problem.specs if s.kind == "letter"]
        for n, (seg, spec) in enumerate(zip(letters, specs, strict=True)):
            slot_index = fit.slots[n]
            if slot_index not in judged:
                continue
            a0, a1 = seg.anchor_slice
            units = free[a0:a1]
            repaired_units, repaired = repair_stranded_anchors(units, spec.stroke_starts)
            fits[slot_index] = SlotFit(
                key=str(seg.key),
                before_px=_anchors_px(problem, units),
                after_px=_anchors_px(problem, repaired_units),
                repaired=repaired,
                stroke_starts=[int(s) for s in spec.stroke_starts],
                xh=float(problem.unit_px),
            )
    for slot_index in wanted - fits.keys() - errors.keys():
        errors[slot_index] = "slot is in no chainable run (unauthored template or no composed body strokes)"
    return fits, errors


# ------------------------------------------------------------------ rendering


def crop_window(points: np.ndarray, xh: float, crop_shape: tuple[int, ...]) -> tuple[int, int, int, int]:
    """`tools.humanbench.build.crop_window` at the rounds' pad — the judged frame."""
    pad = max(6, int(round(PAD_XH * xh)))
    x0 = max(0, int(points[:, 0].min()) - pad)
    x1 = min(crop_shape[1], int(points[:, 0].max()) + pad)
    y0 = max(0, int(points[:, 1].min()) - pad)
    y1 = min(crop_shape[0], int(points[:, 1].max()) + pad)
    return x0, y0, x1, y1


def _stroke_bounds(k: int, stroke_starts: list[int]) -> list[tuple[int, int]]:
    bounds = sorted({0, *(s for s in stroke_starts if 0 < s < k), k})
    return list(zip(bounds[:-1], bounds[1:], strict=False))


def render_panel(
    crop: np.ndarray,
    window: tuple[int, int, int, int],
    points_px: np.ndarray,
    stroke_starts: list[int],
    repaired: list[int],
    color: tuple[int, int, int],
    markers_crop_px: list[tuple[float, float]],
) -> bytes:
    """One panel PNG: the zoomed crop with the polyline drawn per pen-stroke."""
    x0, y0, x1, y1 = window
    sub = (np.clip(crop[y0:y1, x0:x1], 0.0, 1.0) * 255).astype(np.uint8)
    img = Image.fromarray(sub, "L").resize(((x1 - x0) * ZOOM, (y1 - y0) * ZOOM), Image.LANCZOS).convert("RGB")
    draw = ImageDraw.Draw(img)
    local = (points_px - np.array([x0, y0], dtype=float)) * ZOOM
    for a, b in _stroke_bounds(len(local), stroke_starts):
        if b - a >= 2:
            draw.line([tuple(p) for p in local[a:b]], fill=color, width=2)
    for i in repaired:
        cx, cy = local[i]
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], outline=COLOR_REPAIRED, width=2)
    for mx, my in markers_crop_px:
        sx, sy = (mx - x0) * ZOOM, (my - y0) * ZOOM
        draw.line([sx - 6, sy, sx + 6, sy], fill=COLOR_MARKER, width=2)
        draw.line([sx, sy - 6, sx, sy + 6], fill=COLOR_MARKER, width=2)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _data_uri(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode()


def occurrence_panel(occ: Occurrence, case: WordCase, slot_fit: SlotFit) -> dict:
    """Render one judged occurrence into its before/after panel pair."""
    window = crop_window(slot_fit.before_px, slot_fit.xh, case.crop.shape)
    x0, y0 = window[0], window[1]
    # A clicked marker is recorded in screen pixels of the round's 4x view; the
    # frame math above puts the window where the round's builder put it, so the
    # crop position is window origin + marker / zoom.
    markers = [(x0 + j.marker[0] / ZOOM, y0 + j.marker[1] / ZOOM) for j in occ.judgements if j.marker]
    before = render_panel(
        case.crop, window, slot_fit.before_px, slot_fit.stroke_starts, slot_fit.repaired, COLOR_BEFORE, markers
    )
    after = render_panel(
        case.crop, window, slot_fit.after_px, slot_fit.stroke_starts, slot_fit.repaired, COLOR_AFTER, markers
    )
    warning = None
    if slot_fit.key != occ.glyph:
        warning = f"key mismatch: chain fitted {slot_fit.key!r} at slot {occ.slot}, key names {occ.glyph!r}"
    return {
        "occ": occ,
        "n_repaired": len(slot_fit.repaired),
        "before": _data_uri(before),
        "after": _data_uri(after),
        "warning": warning,
        "error": None,
    }


def error_panel(occ: Occurrence, message: str) -> dict:
    return {"occ": occ, "n_repaired": 0, "before": None, "after": None, "warning": None, "error": message}


def _panel_header(panel: dict) -> str:
    occ: Occurrence = panel["occ"]
    uids = " · ".join(
        f"{j.label}:{j.categories}" + (f"#{j.marker[0]},{j.marker[1]}" if j.marker else "")
        for j in sorted(occ.judgements, key=lambda j: (j.round_id, j.uid))
    )
    parts = [
        f"<strong>{html.escape(occ.glyph)}</strong> in „{html.escape(occ.word)}“ · slot {occ.slot}",
        html.escape(uids),
        f"repaired: {panel['n_repaired']}",
    ]
    notes = [j.note for j in occ.judgements if j.note]
    header = " &nbsp;|&nbsp; ".join(parts)
    for note in notes:
        header += f'<div class="note">„{html.escape(note)}“</div>'
    if panel["warning"]:
        header += f'<div class="warn">{html.escape(panel["warning"])}</div>'
    return header


def render_html(panels: list[dict], meta: dict) -> str:
    blocks: list[str] = []
    for panel in panels:
        header = _panel_header(panel)
        if panel["error"]:
            body = f'<div class="error">{html.escape(panel["error"])}</div>'
        else:
            body = (
                '<div class="pair">'
                f'<figure><img src="{panel["before"]}" alt="before"><figcaption>before — fit as-is</figcaption></figure>'
                f'<figure><img src="{panel["after"]}" alt="after"><figcaption>after — repair applied</figcaption></figure>'
                "</div>"
            )
        blocks.append(f'<section class="item"><header>{header}</header>{body}</section>')
    summary = (
        f"rounds {html.escape(meta['rounds'])} · category {html.escape(meta['category'])} · "
        f"{meta['n_occurrences']} occurrences · {meta['n_errors']} failed · "
        f"{meta['n_with_repairs']} with ≥1 repaired anchor ({meta['n_repaired_total']} anchors)"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>fitview — stranded-anchor repair, before/after</title>
<style>
  body {{ font: 14px/1.45 system-ui, sans-serif; margin: 24px; background: #fafaf7; color: #222; }}
  h1 {{ font-size: 20px; margin: 0 0 4px; }}
  .summary {{ color: #555; margin-bottom: 20px; }}
  .legend span {{ margin-right: 16px; }}
  .swatch {{ display: inline-block; width: 12px; height: 12px; border-radius: 2px; vertical-align: -1px; }}
  .item {{ background: #fff; border: 1px solid #ddd; border-radius: 6px; padding: 12px 14px; margin-bottom: 18px; }}
  .item header {{ margin-bottom: 8px; }}
  .note {{ color: #6a5a2a; font-style: italic; margin-top: 2px; }}
  .warn {{ color: #b45309; margin-top: 2px; }}
  .error {{ color: #b91c1c; }}
  .pair {{ display: flex; gap: 14px; flex-wrap: wrap; }}
  figure {{ margin: 0; }}
  figcaption {{ color: #666; font-size: 12px; margin-top: 3px; }}
  img {{ max-width: 100%; height: auto; image-rendering: auto; border: 1px solid #eee; }}
</style>
</head>
<body>
<h1>fitview — stranded-anchor repair, before/after</h1>
<div class="summary">{summary}</div>
<div class="legend summary">
  <span><span class="swatch" style="background:rgb{COLOR_BEFORE}"></span> fit as-is</span>
  <span><span class="swatch" style="background:rgb{COLOR_AFTER}"></span> repaired</span>
  <span><span class="swatch" style="background:rgb{COLOR_REPAIRED}"></span> repaired anchor</span>
  <span><span class="swatch" style="background:rgb{COLOR_MARKER}"></span> owner's marker</span>
</div>
{"".join(blocks)}
</body>
</html>
"""


# ------------------------------------------------------------------------ CLI


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m tools.fitview", description=__doc__.splitlines()[0])
    parser.add_argument("--round", default="all", choices=[*ROUNDS, "all"], help="humanbench round(s) to read [all]")
    parser.add_argument("--category", default="A", help="required category letter(s), e.g. A or AW [A]")
    parser.add_argument("--out", type=Path, default=Path("temp/fitview"), help="output directory [temp/fitview]")
    parser.add_argument("--limit", type=int, default=0, help="cap the number of occurrences (0 = all)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rounds = list(ROUNDS) if args.round == "all" else [args.round]

    judgements: list[Judgement] = []
    for round_id in rounds:
        judgements.extend(parse_round(round_id))
    occurrences = select_occurrences(judgements, args.category)
    if args.limit:
        occurrences = occurrences[: args.limit]
    if not occurrences:
        raise SystemExit(f"no judged screen carries category {args.category!r} in round(s) {', '.join(rounds)}")

    cases = load_cases({occ.word for occ in occurrences})
    by_word: dict[str, list[Occurrence]] = defaultdict(list)
    for occ in occurrences:
        by_word[occ.word].append(occ)

    panels: list[dict] = []
    for word in sorted(by_word):
        occs = by_word[word]
        case = cases.get(word)
        if case is None:
            panels.extend(
                error_panel(occ, f"no fixture case with id {word!r} in {'/'.join(FIXTURE_SETS)}") for occ in occs
            )
            continue
        fits, errors = fit_judged_slots(case, {occ.slot for occ in occs})
        for occ in occs:
            slot_fit = fits.get(occ.slot)
            if slot_fit is None:
                panels.append(error_panel(occ, errors.get(occ.slot, "no fit produced")))
            else:
                panels.append(occurrence_panel(occ, case, slot_fit))
        print(f"  {word:<16} {len(occs)} judged slot(s), {sum(1 for o in occs if o.slot in fits)} fitted", flush=True)
    panels.sort(key=lambda p: p["occ"].sort_key)

    meta = {
        "rounds": "+".join(rounds),
        "category": args.category,
        "n_occurrences": len(panels),
        "n_errors": sum(1 for p in panels if p["error"]),
        "n_with_repairs": sum(1 for p in panels if p["n_repaired"]),
        "n_repaired_total": sum(p["n_repaired"] for p in panels),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    out_path = args.out / "index.html"
    out_path.write_text(render_html(panels, meta), encoding="utf-8")
    print(
        f"wrote {out_path} — {meta['n_occurrences']} occurrences, {meta['n_errors']} failed, "
        f"{meta['n_with_repairs']} with repairs ({meta['n_repaired_total']} anchors)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
