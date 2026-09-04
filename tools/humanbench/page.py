"""Render a judgement payload into ONE self-contained HTML page.

    uv run python -m tools.humanbench.page --payload items.json --out befund.html
    uv run python -m tools.humanbench.page --payload pairs.json --out vergleich.html --round 3

Or from a builder::

    from tools.humanbench.page import write_page
    write_page(items, Path("befund.html"), round_label="3")

The page carries everything it needs: the crops are inlined as ``data:`` URIs,
the styles and the script are inline, and there is no font, no CDN and no
network call of any kind. That is not tidiness — the page is published as an
Artifact under a strict CSP that blocks every external host, and it has to keep
working on a phone with no connection halfway through a pass.

Two modes, chosen by the payload rather than by a flag, because the payload is
what decides which question can be asked:

* **single** (one panel per item) — the six categories of
  ``docs/reference/menschliche-bewertung.md`` §2 with their keys 1-7, multiple
  choice, plus an optional spot marker: one point per image, clicking elsewhere
  moves it, clicking it again removes it.
* **paired** (two panels per item) — the categories are replaced by a two-way
  preference (left better / right better / no difference). The panels are
  labelled „Links"/„Rechts" and nothing else: no arm name, no order hint, and
  the emitted payload is stripped to the geometry that gets drawn, so the
  assignment cannot be read out of the page source either. Which side was the
  new one lives in the builder's key file, never here.

A paired page asks ONE of two questions, and which one is part of the record
rather than a detail of the wording (``menschliche-bewertung.md`` §8): while
there are unambiguous defects the question is „welche Linie folgt der Tinte
besser?" (``question="ink"``, tag ``VERGLEICH``); once both lines lie on the
ink equally well that question measures nothing, and it becomes „welche sieht
echter geschrieben aus?" (``question="authentic"``, tag ``ECHTHEIT``). The two
measure different properties — accuracy can even run against authenticity, a
line that follows every skeleton jag being more accurate and less written — so
their rounds are not comparable, and the TAG carries the difference into the
result file's header so no round can later be filed under the wrong question.

A panel may draw filled ``fills`` and per-stroke ``widths`` beside its
polylines. That is what the word round needs: the defects it exists for (a
stroke a quarter too thin, a saw-toothed running form, the kink at a
connector's seam) are properties of the INK, and a hairline centerline shows
none of the first two.

Properties that carry over from the pass-2 instrument, each for its reason:

* **Cartographic casing.** A light halo under the line and under the marker, so
  both stay legible INSIDE near-black ink and not only where they leave it.
  Without it every wobble judgement would secretly be an off-ink judgement.
* **Per-judgement timing.** Fatigue and drift are measured, not assumed away.
  The clock runs only while the page is actually visible, so a coffee break in
  the middle of an item is not recorded as a slow judgement.
* **Resumable.** The whole cost of the instrument is human patience; losing it
  to a tab crash at item 130 is the most expensive bug it could have. State is
  written after every step and restored on load, keyed by a fingerprint of the
  payload so a different pass never resumes into a stale state.
* **Reachable on a phone.** The image is clamped in ``vh`` and the controls
  shrink, so the buttons stay on screen without scrolling; in paired mode the
  two panels stay side by side at every width, because a comparison you can
  only see half of is not a comparison.

The user-facing text is German (the judge is the German-speaking author);
identifiers, docstrings and comments are English per
``docs/reference/sprachregelung.md``.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Artifact pages are capped at 16 MB including the inlined crops; warn early
# enough that a builder can drop the zoom or the item count before publishing.
SIZE_WARN_MB = 15.0


@dataclass(frozen=True)
class Category:
    """One verdict button of the single-item mode.

    ``kind`` decides the behaviour, not the code: ``solo`` answers the whole
    question on its own (picking one clears the findings), ``finding`` items add
    up, and ``modifier`` combines with anything including a solo.
    """

    code: str
    key: str
    label: str
    kind: str
    tally: str
    tone: str = ""
    key_note: str = ""


@dataclass(frozen=True)
class Choice:
    """One button of the paired mode's two-way preference."""

    code: str
    keys: tuple[str, ...]
    label: str
    tally: str
    key_note: str = ""
    why: str = ""


# The six categories of the labelling pass, in RESULT order (the order their
# letters appear in an item's verdict string). Their on-screen order is derived
# from `kind` further down, so the solo pair keeps the top row.
CATEGORIES: tuple[Category, ...] = (
    Category("G", "1", "Gut", "solo", "Gut", tone="good"),
    Category("A", "2", "Einzelner Ausreißer", "finding", "Ausreißer"),
    Category("W", "3", "Gewackel", "finding", "Gewackel"),
    Category("B", "4", "Bereich daneben", "finding", "Bereich"),
    # Separate from a peak on purpose: at a stroke end the template runs past
    # the specimen's ink, so there is nothing left to fit to — a different cause
    # from a runaway in the middle of a stroke, where ink exists and the fit
    # left it anyway.
    Category("E", "5", "Knick nur am Rand", "finding", "Knick am Rand"),
    # Not a severity but a disqualifier: there is nothing to judge there.
    Category("K", "6", "Komplett daneben — nicht bewertbar", "solo", "Komplett daneben", tone="dim"),
    Category("U", "7", "Unsicher", "modifier", "davon unsicher", key_note="7 · zu jeder Wahl"),
)

# The paired mode's answers. Deliberately three: a winner each way and the
# claim that there is none. Anything finer would ask the judge to rank a
# difference they just said they cannot see.
#
# The accuracy question — the one to ask while unambiguous defects are still
# there, because an outlier or a misplaced arc is exactly what accuracy means.
CHOICES: tuple[Choice, ...] = (
    Choice("L", ("1", "ArrowLeft"), "Links folgt besser", "Links besser", key_note="1 oder ←"),
    Choice("R", ("2", "ArrowRight"), "Rechts folgt besser", "Rechts besser", key_note="2 oder →"),
    Choice(
        "N",
        ("3",),
        "Kein Unterschied erkennbar",
        "Kein Unterschied",
        key_note="Taste 3",
        why="der Streit liegt unter der Sichtbarkeit",
    ),
)

# The authenticity question — the project's actual yardstick, and the one the
# frozen rulers cannot stand in for. Same three answers and the same codes, so
# a result file parses identically; only the wording moves, because the
# property being judged is a different one.
AUTHENTIC_CHOICES: tuple[Choice, ...] = (
    Choice("L", ("1", "ArrowLeft"), "Links sieht echter aus", "Links echter", key_note="1 oder ←"),
    Choice("R", ("2", "ArrowRight"), "Rechts sieht echter aus", "Rechts echter", key_note="2 oder →"),
    Choice(
        "N",
        ("3",),
        "Kein Unterschied erkennbar",
        "Kein Unterschied",
        key_note="Taste 3",
        why="der Streit liegt unter der Sichtbarkeit",
    ),
)

QUESTIONS: dict[str, tuple[Choice, ...]] = {"ink": CHOICES, "authentic": AUTHENTIC_CHOICES}

_KIND_ORDER = {"solo": 0, "finding": 1, "modifier": 2}


@dataclass
class PageMeta:
    """Everything the page says about itself, resolved from payload + CLI."""

    mode: str
    question: str
    tag: str
    eyebrow: str
    headline: str
    lede: str
    lede_fine: str
    store: str
    title: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)


_DEFAULTS: dict[str, dict[str, str]] = {
    "single": {
        "tag": "BEFUND",
        "eyebrow": "Befund-Durchgang",
        "headline": "Was stimmt hier nicht?",
        "lede": (
            "*Mehrfachauswahl* — die mittlere Reihe addiert sich, Gewackel und ein Ausreißer "
            "schließen sich nicht aus. Die obere Reihe beantwortet die Frage allein. "
            "*„Knick nur am Rand“* heißt: der Knick sitzt im allerersten oder allerletzten Stück."
        ),
        "lede_fine": (
            "Nachbartinte im Fenster ist normal — beurteile die Linie nur gegen *ihren eigenen* "
            "Buchstaben. Bei völlig danebenliegenden Fits folgt der Ausschnitt dem Fit, der "
            "Buchstabe kann also angeschnitten sein."
        ),
    },
    "paired": {
        "tag": "VERGLEICH",
        "eyebrow": "Blindvergleich",
        "headline": "Welche Linie folgt der Tinte besser?",
        "lede": (
            "Zwei Anpassungen desselben Buchstabens, beide vom System berechnet. Welche folgt der "
            "Tinte besser? *Alle drei Antworten sind vollwertig* — „kein Unterschied“ ist ein "
            "Ergebnis, keine Ausrede."
        ),
        "lede_fine": (
            "Welche Seite welche Rechnung zeigt, steht nirgends auf dieser Seite — auch nicht im "
            "Quelltext. Die Zuordnung liegt beim Auswerter."
        ),
    },
    "authentic": {
        "tag": "ECHTHEIT",
        "eyebrow": "Blindvergleich — Echtheit",
        "headline": "Welche Zeile sieht echter geschrieben aus?",
        "lede": (
            "Dasselbe Wort der Vorlage, zweimal vom System geschrieben. Gefragt ist *nicht*, welche "
            "genauer auf der Tinte liegt, sondern welche *nach Hand aussieht* — Strichstärke, "
            "Schwung, die Übergänge. *Alle drei Antworten sind vollwertig* — „kein Unterschied“ ist "
            "ein Ergebnis, keine Ausrede."
        ),
        "lede_fine": (
            "Die Vorlage liegt als Hintergrund darunter; sie ist der Maßstab dafür, wie geschrieben "
            "aussieht, nicht das Ziel, das getroffen werden soll. Welche Seite welche Rechnung zeigt, "
            "steht nirgends auf dieser Seite — auch nicht im Quelltext."
        ),
    },
}


# --- payload normalisation -------------------------------------------------


def _data_uri(raw: Any, where: str) -> str:
    """Return an inline ``data:`` URI for a panel image.

    Accepts raw PNG bytes, a bare base64 string (what the builders produce) or a
    finished ``data:`` URI. Everything else is refused: a page that reaches for
    a file or a host is exactly the page that breaks under the Artifact CSP.
    """
    if isinstance(raw, bytes | bytearray):
        return "data:image/png;base64," + base64.b64encode(bytes(raw)).decode("ascii")
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"{where}: 'img' must be base64 text, PNG bytes or a data: URI")
    if raw.startswith("data:"):
        return raw
    if "://" in raw or raw.startswith("//"):
        raise ValueError(f"{where}: 'img' points at {raw[:40]!r} — the page must not load anything external")
    try:
        base64.b64decode(raw, validate=True)
    except Exception as exc:  # noqa: BLE001 - the message matters more than the class
        raise ValueError(f"{where}: 'img' is neither a data: URI nor valid base64 ({exc})") from exc
    return "data:image/png;base64," + raw


def _paths(raw: Any, where: str, field: str, minimum: int) -> list[list[list[float]]]:
    """Validate one panel's path set and round it to display precision.

    Coordinates are in the panel's own pixel frame (0..w, 0..h). Sub-pixel
    precision beyond two decimals is invisible at any zoom the page uses and
    only inflates the file, which is the scarce resource here.
    """
    if not isinstance(raw, Sequence) or isinstance(raw, str):
        raise ValueError(f"{where}: {field!r} must be a list of paths")
    out: list[list[list[float]]] = []
    for si, path in enumerate(raw):
        if not isinstance(path, Sequence) or isinstance(path, str):
            raise ValueError(f"{where}: {field} {si} is not a list of points")
        pts: list[list[float]] = []
        for point in path:
            if not isinstance(point, Sequence) or isinstance(point, str) or len(point) != 2:
                raise ValueError(f"{where}: {field} {si} has a point that is not [x, y]")
            pts.append([round(float(point[0]), 2), round(float(point[1]), 2)])
        if len(pts) >= minimum:  # a one-point stroke draws nothing; a pen lift is a new stroke
            out.append(pts)
    return out


def _strokes(raw: Any, where: str) -> list[list[list[float]]]:
    """The judged polylines of one panel; at least one is required."""
    out = _paths(raw, where, "strokes", 2)
    if not out:
        raise ValueError(f"{where}: no drawable stroke (each needs at least two points)")
    return out


def _shapes(raw: Any, where: str) -> list[list[list[list[float]]]]:
    """Filled shapes of one panel: per pen stroke its exterior ring plus counters.

    The nesting is load-bearing and is therefore required rather than guessed
    at. A pen stroke's silhouette is one exterior with the loop interiors it
    encloses; drawn as independent shapes they fill in solid, and the writing
    reads as a blob exactly where it has a loop. Grouped, the page draws them
    as ONE evenodd path and the counters stay paper — the same contract
    production has always used (``app/src/lib/svg.ts::ringsToPathD``).

    A FLAT ring list is refused instead of read as a single-ring shape: it
    parses perfectly and fails silently, which is the one thing a judging
    session cannot afford.
    """
    if not isinstance(raw, Sequence) or isinstance(raw, str):
        raise ValueError(f"{where}: 'fills' must be a list of shapes")
    out: list[list[list[list[float]]]] = []
    for si, shape in enumerate(raw):
        if not isinstance(shape, Sequence) or isinstance(shape, str):
            raise ValueError(f"{where}: fill {si} is not a list of rings")
        if shape and all(_looks_like_point(ring) for ring in shape):
            raise ValueError(
                f"{where}: fill {si} is a flat ring, not a list of rings — its loop counters would be "
                f"drawn filled; group each pen stroke's rings into one shape"
            )
        rings = _paths(shape, f"{where} fill {si}", "rings", 3)
        if rings:
            out.append(rings)
    return out


def _looks_like_point(value: Any) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, str)
        and len(value) == 2
        and all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in value)
    )


def _widths(raw: Any, where: str, n_strokes: int) -> list[float]:
    """Per-stroke widths in panel pixels, or an empty list for the hairline.

    Pinned to the stroke count on purpose: a short widths array would silently
    ink the tail of a word at the wrong weight, and stroke weight is the very
    thing a word round is asked to judge.
    """
    if raw is None:
        return []
    if not isinstance(raw, Sequence) or isinstance(raw, str):
        raise ValueError(f"{where}: 'widths' must be a list of numbers")
    if len(raw) != n_strokes:
        raise ValueError(f"{where}: {len(raw)} widths for {n_strokes} strokes — one per stroke or none")
    return [round(float(value), 2) for value in raw]


def _panel(raw: Any, where: str, shared: dict[str, Any]) -> dict[str, Any]:
    """One drawable panel, stripped to what the page actually draws.

    The stripping is the point, not a side effect: everything the payload knows
    about the occurrence — glyph, word, the metric that disagreed, which arm a
    variant came from — stays out of the page. In paired mode that is what makes
    the comparison blind even to a judge who opens the page source.

    ``shared`` holds the item-level ``w``/``h``/``img`` a panel may inherit. A
    paired item normally draws both fits on ONE crop image: cropping each side
    separately would give the two panels different pixel dimensions and a
    different view of the neighbouring ink — a tell that has nothing to do with
    the fits, and one a judge learns within a dozen screens.
    """
    if not isinstance(raw, dict):
        raise ValueError(f"{where}: panel must be an object")
    merged = {**shared, **raw}
    try:
        width = int(merged["w"])
        height = int(merged["h"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{where}: panel needs integer 'w' and 'h' ({exc})") from exc
    if width <= 0 or height <= 0:
        raise ValueError(f"{where}: panel size {width}x{height} is not drawable")
    if "img" not in merged:
        raise ValueError(f"{where}: panel needs an 'img' (its own or the item's)")
    strokes = _paths(merged.get("strokes", []), where, "strokes", 2)
    # A filled silhouette is ink too: the word mode draws letter bodies as
    # rings and only the generated connectors as capsules, so a panel may
    # legitimately carry no polyline at all — but never neither.
    fills = _shapes(merged.get("fills", []), where)
    if not strokes and not fills:
        # Both counts named, because the two ways to be empty look identical
        # from the outside: a stroke set whose polylines are all single points,
        # and a fill set whose rings are all too short to enclose anything.
        raise ValueError(f"{where}: nothing drawable — a panel needs a stroke (2+ points) or a ring (3+ points)")
    return {
        "w": width,
        "h": height,
        "img": _data_uri(merged["img"], where),
        "strokes": strokes,
        "widths": _widths(merged.get("widths"), where, len(strokes)),
        "fills": fills,
        # Optional, and validated only when present: a panel with no surrounding
        # pen path is legitimate (a word of one letter, or a round built without
        # traces), whereas a panel with no JUDGED line is a broken screen.
        "context": _strokes(merged["context"], f"{where} context") if merged.get("context") else [],
    }


def _panels_of(raw: dict[str, Any], where: str) -> list[dict[str, Any]]:
    """Accept the three payload shapes and return fully resolved panels."""
    # `context` is shared like the image: it is the specimen's own measured pen
    # path, identical for both panels, so hoisting it cannot leak which side is
    # which — and drawing it once is what keeps a joined letter from appearing
    # to stop short (see `build.py::context_strokes`).
    # `strokes`/`widths`/`fills` are deliberately NOT shareable: they are the
    # two things being compared, and a panel that inherited them would draw the
    # other arm's ink.
    shared = {k: raw[k] for k in ("w", "h", "img", "context") if k in raw}
    if "panels" in raw:
        panels = raw["panels"]
        if not isinstance(panels, Sequence) or isinstance(panels, str) or not 1 <= len(panels) <= 2:
            raise ValueError(f"{where}: 'panels' must hold one or two panels")
        return [_panel(p, f"{where} panel {i}", shared) for i, p in enumerate(panels)]
    if "left" in raw or "right" in raw:
        if "left" not in raw or "right" not in raw:
            raise ValueError(f"{where}: a paired item needs both 'left' and 'right'")
        return [_panel(raw["left"], f"{where} links", shared), _panel(raw["right"], f"{where} rechts", shared)]
    return [_panel(raw, where, {})]


def _pack(item_id: str, panels: list[dict[str, Any]]) -> dict[str, Any]:
    """Emit an item, hoisting an image both panels share out of the panels.

    Two identical inlined crops would double the page's weight for nothing, and
    the file size is the scarce resource: an Artifact stops at 16 MB, and a
    round is 250 screens.
    """
    first = panels[0]
    same = all(p["w"] == first["w"] and p["h"] == first["h"] and p["img"] == first["img"] for p in panels[1:])
    # The context is hoisted ONLY when every panel carries the same one. The
    # builder always shares it (it is the specimen's own measured pen path), but
    # `_panel` accepts a per-panel context, and hoisting the first would then
    # silently draw one panel's surroundings around the other — the same class
    # of error as showing a letter without its connectors at all.
    shared_context = all(p["context"] == first["context"] for p in panels[1:])
    if same and shared_context:
        item = {
            "id": item_id,
            "w": first["w"],
            "h": first["h"],
            "img": first["img"],
            # Only the fields a panel actually carries: a letter round's panel
            # stays `{"strokes"}`, which is what keeps its payload as narrow as
            # the blindness rule (§3.8) promises.
            "panels": [{key: p[key] for key in ("strokes", "widths", "fills") if p[key]} for p in panels],
        }
        if first["context"]:
            item["context"] = first["context"]
        return item
    return {"id": item_id, "panels": panels}


def normalise(payload: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Split a raw payload into normalised items and its own metadata.

    Accepts a bare list of items, or an envelope ``{"items": [...], ...}`` whose
    remaining keys are page metadata (``tag``, ``eyebrow``, ``headline``,
    ``lede``, ``lede_fine``, ``round``, ``title``, ``store``).
    """
    meta: dict[str, Any] = {}
    if isinstance(payload, dict):
        raw_items = payload.get("items", payload.get("payload"))
        if raw_items is None:
            raise ValueError("payload object has neither 'items' nor 'payload'")
        meta = {k: v for k, v in payload.items() if k not in {"items", "payload"}}
    else:
        raw_items = payload
    if not isinstance(raw_items, Sequence) or isinstance(raw_items, str):
        raise ValueError("payload items must be a list")
    if not raw_items:
        raise ValueError("payload is empty — there is nothing to judge")

    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(raw_items):
        where = f"item {index}"
        if not isinstance(raw, dict):
            raise ValueError(f"{where}: must be an object")
        item_id = str(raw.get("id") or "").strip()
        if not item_id:
            raise ValueError(f"{where}: needs a non-empty 'id' — the result line is joined on it")
        if item_id in seen_ids:
            # A repeat is a SECOND id pointing at the same occurrence (that is
            # how test-retest works); two items sharing one id would silently
            # merge two judgements in the result.
            raise ValueError(f"{where}: duplicate id {item_id!r}")
        seen_ids.add(item_id)
        items.append(_pack(item_id, _panels_of(raw, f"{where} ({item_id})")))

    widths = {len(item["panels"]) for item in items}
    if len(widths) > 1:
        raise ValueError("payload mixes one-panel and two-panel items — that would change the question mid-pass")
    return items, meta


def _fingerprint(tag: str, items: list[dict[str, Any]]) -> str:
    """Short stable digest of what this page asks, for the resume key.

    The TAG is folded in, not just the mode and the item ids: two word rounds
    over the same fixture set draw the same 63 words in the same order under
    the same display ids, so on ids alone they would share a resume key and the
    second round would open on the first one's answers. The tag carries the
    round number, which is the one thing that always differs — and when it does
    not, the builder hands in an explicit `store` (see `build.py`).
    """
    digest = hashlib.sha256()
    digest.update(tag.encode())
    for item in items:
        digest.update(b"\x00")
        digest.update(item["id"].encode())
    return digest.hexdigest()[:10]


# --- page assembly ---------------------------------------------------------


def _emphasise(text: str) -> str:
    """Escape running text, then read ``*bold*`` as the one bit of markup.

    The lede is metadata a builder can override, so it is escaped rather than
    trusted; emphasis still has to survive, because the multi-select rule is the
    sentence the judge has to actually read.
    """
    escaped = html.escape(text)
    parts = escaped.split("*")
    if len(parts) % 2 == 0:  # unbalanced marker — leave it alone rather than guess
        return escaped
    return "".join(part if i % 2 == 0 else f"<b>{part}</b>" for i, part in enumerate(parts))


def _category_buttons() -> str:
    """Markup for the six categories plus the modifier, in on-screen order."""
    ordered = sorted(CATEGORIES, key=lambda c: (_KIND_ORDER[c.kind], CATEGORIES.index(c)))
    rows = []
    for cat in ordered:
        classes = "cat mod" if cat.kind == "modifier" else "cat"
        rows.append(
            f'<button class="{classes}" data-c="{html.escape(cat.code)}" data-kind="{cat.kind}" '
            f'data-tone="{cat.tone}" type="button" aria-pressed="false">'
            f"<span>{html.escape(cat.label)}</span>"
            f'<span class="k">{html.escape(cat.key_note or cat.key)}</span></button>'
        )
    return "\n      ".join(rows)


def _choice_buttons(choices: tuple[Choice, ...]) -> str:
    """Markup for the paired mode's two-way preference."""
    rows = []
    for choice in choices:
        why = f'<span class="why">{html.escape(choice.why)}</span>' if choice.why else ""
        rows.append(
            f'<button class="choice" data-c="{html.escape(choice.code)}" type="button" aria-pressed="false">'
            f"<span>{html.escape(choice.label)}</span>{why}"
            f'<span class="k">{html.escape(choice.key_note or choice.keys[0])}</span></button>'
        )
    return "\n      ".join(rows)


def _hint(mode: str, choices: tuple[Choice, ...]) -> str:
    if mode == "paired":
        keys = " / ".join(c.keys[0] for c in choices)
        return f"Tasten {keys} · Pfeiltasten · Rücktaste = zurück"
    keys = [c.key for c in CATEGORIES]
    return f"Tasten {keys[0]}–{keys[-1]} · Enter = weiter · Rücktaste = zurück"


def _js_json(value: Any) -> str:
    """Embed a value in an inline ``<script>`` without ever closing it early."""
    return json.dumps(value, separators=(",", ":"), ensure_ascii=True).replace("<", "\\u003c")


def _resolve_meta(items: list[dict[str, Any]], payload_meta: dict[str, Any], overrides: dict[str, Any]) -> PageMeta:
    mode = "paired" if len(items[0]["panels"]) == 2 else "single"

    question = str(overrides.get("question") or payload_meta.get("question") or "ink")
    if question not in QUESTIONS:
        raise ValueError(f"question {question!r} is not one of {sorted(QUESTIONS)}")
    if mode == "single" and question != "ink":
        raise ValueError("a category round asks the categories; the two-way questions need two panels")
    # The question, not just the panel count, decides how the page speaks and
    # what its result file is tagged: two paired rounds on different questions
    # measure different properties and must not be filed as one series (§8).
    voice = mode if question == "ink" else question
    defaults = _DEFAULTS[voice]

    def pick(name: str) -> str:
        for source in (overrides, payload_meta):
            value = source.get(name)
            if value not in (None, ""):
                return str(value)
        return defaults.get(name, "")

    round_label = pick("round_label") or str(payload_meta.get("round") or "")
    tag = pick("tag")
    headline = pick("headline")
    full_tag = f"{tag}/{round_label}" if round_label else tag
    # The tag opens the result file's header line, which the analyser reads as a
    # single whitespace-free token. Refused HERE, at build time, because the
    # alternative is discovering it after a pass has been judged: the page would
    # emit `BEFUND/2 (nachtrag) geprueft=…` and no header would parse.
    if not full_tag or full_tag.split() != [full_tag]:
        raise ValueError(f"tag {full_tag!r} must be one whitespace-free token — it heads the result file")
    # The round is SAID on the page, not only in the emitted result text: the
    # judge has to be able to tell at a glance that the tab in front of him is
    # today's round and not a page he left open before a fix — the doubt the
    # LF11 round could not resolve afterwards (§3.6b).
    eyebrow = pick("eyebrow")
    if round_label and round_label not in eyebrow:
        eyebrow = f"{eyebrow} · Runde {round_label}"
    return PageMeta(
        mode=mode,
        question=question,
        tag=full_tag,
        eyebrow=eyebrow,
        headline=headline,
        lede=pick("lede"),
        lede_fine=pick("lede_fine"),
        store=pick("store") or f"humanbench-{_fingerprint(full_tag, items)}",
        title=pick("title") or headline,
        items=items,
    )


def build_page(payload: Any, **overrides: Any) -> str:
    """Return the finished, self-contained HTML for ``payload``.

    Keyword overrides (all optional, all strings): ``question`` (``ink`` or
    ``authentic``), ``tag``, ``round_label``, ``eyebrow``, ``headline``,
    ``title``, ``lede``, ``lede_fine``, ``store``.
    """
    items, payload_meta = normalise(payload)
    meta = _resolve_meta(items, payload_meta, overrides)
    choices = QUESTIONS[meta.question]
    config = {
        "mode": meta.mode,
        "question": meta.question,
        "tag": meta.tag,
        "store": meta.store,
        "order": [c.code for c in CATEGORIES],
        "categories": [
            {"code": c.code, "key": c.key, "kind": c.kind, "tally": c.tally}
            for c in (CATEGORIES if meta.mode == "single" else ())
        ],
        "choices": [
            {"code": c.code, "keys": list(c.keys), "tally": c.tally} for c in (choices if meta.mode == "paired" else ())
        ],
    }
    fine = f'<span class="fine"><br>{_emphasise(meta.lede_fine)}</span>' if meta.lede_fine else ""
    replacements = {
        "__TITLE__": html.escape(meta.title),
        "__EYEBROW__": html.escape(meta.eyebrow),
        "__HEADLINE__": html.escape(meta.headline),
        "__LEDE__": _emphasise(meta.lede) + fine,
        "__MODE__": meta.mode,
        "__HINT__": html.escape(_hint(meta.mode, choices)),
        "__CATEGORY_BUTTONS__": _category_buttons() if meta.mode == "single" else "",
        "__CHOICE_BUTTONS__": _choice_buttons(choices) if meta.mode == "paired" else "",
        "__CONFIG__": _js_json(config),
        "__ITEMS__": _js_json(items),
    }
    out = _TEMPLATE
    for needle, value in replacements.items():
        out = out.replace(needle, value)
    return out


def write_page(payload: Any, out_path: str | Path, **overrides: Any) -> Path:
    """Build the page and write it to ``out_path``; returns the path written."""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_page(payload, **overrides), encoding="utf-8")
    return path


def load_payload(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a judgement payload into one self-contained HTML page.")
    parser.add_argument("--payload", required=True, type=Path, help="JSON payload (list of items or an envelope)")
    parser.add_argument("--out", required=True, type=Path, help="HTML file to write")
    parser.add_argument("--round", dest="round_label", default="", help="pass number, e.g. 3 -> 'BEFUND/3'")
    parser.add_argument(
        "--question",
        default="",
        choices=("", *sorted(QUESTIONS)),
        help="which paired question is asked: ink = follows the ink better, authentic = looks more "
        "genuinely written [the payload's own, else ink]",
    )
    parser.add_argument("--tag", default="", help="result header tag (default BEFUND / VERGLEICH / ECHTHEIT)")
    parser.add_argument("--title", default="", help="browser tab title (default: the headline)")
    parser.add_argument("--headline", default="", help="the page's own question")
    parser.add_argument("--eyebrow", default="", help="small line above the headline")
    args = parser.parse_args(argv)

    try:
        payload = load_payload(args.payload)
        items, _ = normalise(payload)
        path = write_page(
            payload,
            args.out,
            round_label=args.round_label,
            tag=args.tag,
            title=args.title,
            headline=args.headline,
            eyebrow=args.eyebrow,
            question=args.question,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    mode = "paired" if len(items[0]["panels"]) == 2 else "single"
    size_mb = path.stat().st_size / 1e6
    print(f"wrote {path} — {mode} mode, {len(items)} screens, {size_mb:.2f} MB")
    if size_mb > SIZE_WARN_MB:
        print(
            f"warning: {size_mb:.2f} MB is close to the 16 MB Artifact limit — fewer items or less zoom",
            file=sys.stderr,
        )
    return 0


# The page itself. A raw string: it is JavaScript and CSS verbatim, so no
# backslash or brace in here may be read as Python.
_TEMPLATE = r"""<title>__TITLE__</title>
<style>
  /* Palette from the project's own tokens (app/src/styles/paper.ts). The plate
     crops are work surfaces and opt out onto a neutral ground per that file's
     own rule — and they stay light in dark mode: a scan is not inverted. */
  :root {
    --paper: #e7dabf; --paper-hi: #f1e8d4; --ink: #241a10; --ink-soft: #473420;
    --sepia: #5e4726; --line: #b6a079; --viridian: #2e6152; --viridian-fill: #40826d;
    --surface: #f7f4ee; --surface-edge: #cbbf9f; --shadow: rgba(36,26,16,.13);
    --good: #3f7d52; --dim: #8a6a3a;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --paper: #1b1712; --paper-hi: #241f18; --ink: #ece2cf; --ink-soft: #c3b49a;
      --sepia: #b09a73; --line: #4a3f2e; --viridian: #7fc0a8; --viridian-fill: #56a288;
      --surface-edge: #55492f; --shadow: rgba(0,0,0,.45); --good: #6fbe86; --dim: #c9a468;
    }
  }
  :root[data-theme="dark"] {
    --paper: #1b1712; --paper-hi: #241f18; --ink: #ece2cf; --ink-soft: #c3b49a;
    --sepia: #b09a73; --line: #4a3f2e; --viridian: #7fc0a8; --viridian-fill: #56a288;
    --surface-edge: #55492f; --shadow: rgba(0,0,0,.45); --good: #6fbe86; --dim: #c9a468;
  }

  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--paper); color: var(--ink);
    font: 400 16px/1.55 ui-sans-serif, system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  .wrap { max-width: 800px; margin: 0 auto; padding: 18px 20px 44px; }
  [data-mode="paired"].wrap { max-width: 1180px; }

  /* One template serves both modes; each hides the other's controls. */
  [data-mode="single"] .only-paired { display: none; }
  [data-mode="paired"] .only-single { display: none; }

  header { display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px 16px; }
  h1 {
    margin: 0; font-size: 22px; line-height: 1.2; font-weight: 600; text-wrap: balance;
    font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  }
  .eyebrow { font-size: 11.5px; letter-spacing: .13em; text-transform: uppercase; color: var(--sepia); font-weight: 600; }
  .count { margin-left: auto; font-variant-numeric: tabular-nums; color: var(--sepia); font-size: 14px; }
  .count b { color: var(--ink); }
  .rail { height: 4px; background: var(--line); border-radius: 2px; margin: 12px 0 0; overflow: hidden; }
  .rail span { display: block; height: 100%; width: 0; background: var(--viridian-fill); transition: width .18s; }

  .lede { color: var(--ink-soft); margin: 9px 0 0; font-size: 14px; }
  .lede b { color: var(--ink); font-weight: 600; }

  .pair { display: grid; grid-template-columns: 1fr; gap: 12px; }
  /* The panels stay side by side at EVERY width. Stacking them would destroy
     the comparison — you cannot judge two lines against each other while only
     one is on screen. On a phone they shrink instead. */
  [data-mode="paired"] .pair { grid-template-columns: 1fr 1fr; gap: 14px; }
  .panel {
    background: var(--surface); border: 1px solid var(--surface-edge); border-radius: 3px;
    padding: 12px; margin-top: 12px; display: flex; flex-direction: column;
    justify-content: center; align-items: center; gap: 8px;
    box-shadow: 0 1px 3px var(--shadow);
  }
  .panel .tag { font-size: 11.5px; letter-spacing: .13em; text-transform: uppercase; color: #6b5c3f; font-weight: 700; }
  .stage { width: 100%; display: flex; justify-content: center; }
  .stage svg { max-width: 100%; max-height: min(37vh, 320px); width: auto; height: auto; }
  [data-mode="paired"] .stage svg { max-height: min(40vh, 360px); }

  /* Multiple choice: these coexist. „Gut" and „komplett daneben" answer the
     whole question on their own, so picking either clears the rest — the others
     are findings that add up. */
  .cats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 7px; margin-top: 10px; }
  button.cat[data-kind="solo"] { grid-column: span 2; }
  button.cat.mod { grid-column: span 4; border-style: dashed; font-weight: 600; }
  button.cat.mod[aria-pressed="true"] { border-style: solid; }
  button.cat, button.choice {
    font: inherit; font-size: 14px; font-weight: 600; cursor: pointer;
    background: var(--paper-hi); color: var(--ink);
    border: 1px solid var(--line); border-radius: 3px; padding: 8px 8px;
    display: flex; flex-direction: column; gap: 3px; align-items: center; text-align: center;
    transition: border-color .12s, background .12s;
  }
  button.cat:hover, button.choice:hover { border-color: var(--viridian-fill); }
  button.cat .k, button.choice .k { font-size: 11px; font-weight: 700; letter-spacing: .08em; color: var(--sepia); }
  button.cat[aria-pressed="true"], button.choice[aria-pressed="true"] {
    border-color: var(--viridian-fill); border-width: 2px; padding: 7px 7px;
    background: color-mix(in srgb, var(--viridian-fill) 15%, transparent);
  }
  button.cat[data-tone="good"][aria-pressed="true"] {
    border-color: var(--good); background: color-mix(in srgb, var(--good) 16%, transparent);
  }
  button.cat[data-tone="dim"][aria-pressed="true"] {
    border-color: var(--dim); background: color-mix(in srgb, var(--dim) 16%, transparent);
  }
  button:focus-visible { outline: 2px solid var(--viridian-fill); outline-offset: 2px; }

  .choices { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 12px; }
  .choices .why { font-size: 12.5px; font-weight: 400; color: var(--ink-soft); }

  .bar { display: flex; align-items: center; gap: 10px; margin-top: 9px; flex-wrap: wrap; }
  button.next {
    font: inherit; font-weight: 700; cursor: pointer; background: var(--viridian-fill); color: #fff;
    border: 1px solid var(--viridian-fill); border-radius: 3px; padding: 9px 18px;
  }
  button.next[disabled] { opacity: .4; cursor: default; }
  button.ghost {
    font: inherit; font-size: 14px; cursor: pointer; background: none; color: var(--viridian);
    border: 1px solid transparent; border-radius: 3px; padding: 6px 10px; font-weight: 600;
  }
  button.ghost:hover { border-color: var(--line); }
  button.ghost[disabled] { color: var(--sepia); opacity: .5; cursor: default; border-color: transparent; }
  button.stop { border-color: var(--line); }
  .hint { color: var(--sepia); font-size: 13px; }
  .quiet { color: var(--viridian); font-size: 13px; margin-top: 6px; min-height: 1.2em; font-weight: 600; }

  .note { width: 100%; margin-top: 8px; }
  .note textarea {
    width: 100%; font: inherit; font-size: 14px; color: var(--ink); background: var(--paper-hi);
    border: 1px dashed var(--line); border-radius: 3px; padding: 8px 10px; resize: vertical; min-height: 38px;
  }
  .note textarea::placeholder { color: var(--sepia); opacity: .8; }

  .done-card { background: var(--paper-hi); border: 1px solid var(--line); border-radius: 3px; padding: 20px; margin-top: 18px; }
  .done-card h2 { margin: 0 0 8px; font-size: 19px; font-weight: 600; font-family: "Iowan Old Style", Palatino, Georgia, serif; }
  .done-card p { margin: 0; color: var(--ink-soft); }
  code.result {
    display: block; margin: 12px 0 0; padding: 12px 14px; border-radius: 3px;
    background: var(--surface); color: #241a10; border: 1px solid var(--surface-edge);
    font: 600 13px/1.65 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    white-space: pre-wrap; word-break: break-all; user-select: all; max-height: 40vh; overflow-y: auto;
  }
  .tally { display: flex; gap: 16px; margin-top: 12px; flex-wrap: wrap; color: var(--ink-soft); font-size: 14px; }
  .tally b { color: var(--ink); font-variant-numeric: tabular-nums; }
  .hidden { display: none; }

  /* Narrow screens: the image gives up height so the buttons stay reachable
     without scrolling. Everything below the crop is the instrument; a judgement
     that needs a scroll between looking and answering is a slower, worse one. */
  @media (max-width: 760px) {
    .wrap { padding: 12px 10px 28px; }
    .cats { grid-template-columns: repeat(2, 1fr); gap: 6px; }
    .choices { gap: 6px; }
    .panel { padding: 6px; margin-top: 8px; }
    .stage svg { max-height: 20vh; }
    [data-mode="paired"] .pair { gap: 8px; }
    [data-mode="paired"] .stage svg { max-height: 24vh; }
    /* The one exception to „side by side at every width": a WORD is wide and
       short, and at 390 px two of them side by side are two thumbnails nobody
       can judge a stroke weight from. The rule's reason is that both have to be
       on screen at once — for this aspect ratio stacking is what achieves that,
       and side by side is what defeats it. Set per item from the crop's own
       proportions, so a letter round is untouched. */
    [data-mode="paired"][data-wide="1"] .pair { grid-template-columns: 1fr; }
    [data-mode="paired"][data-wide="1"] .stage svg { max-height: 20vh; }
    h1 { font-size: 18px; }
    .lede { font-size: 13px; margin-top: 6px; }
    button.cat, button.choice { font-size: 12.5px; padding: 7px 3px; line-height: 1.25; }
    button.cat.mod { padding: 5px 4px; }
    /* The caveats are read once; on a phone the screen is the scarce resource
       and the choice rule is what has to stay visible. */
    .lede .fine, .choices .why, .hint { display: none; }
    .note { margin-top: 6px; }
    .note textarea { min-height: 30px; font-size: 13px; padding: 5px 8px; }
    .quiet { font-size: 12px; margin-top: 4px; min-height: 1em; }
    .bar { margin-top: 8px; gap: 8px; }
  }
  @media (prefers-reduced-motion: reduce) {
    button.cat, button.choice, .rail span { transition: none; }
  }
</style>

<div class="wrap" id="wrap" data-mode="__MODE__">
  <header>
    <div>
      <div class="eyebrow">__EYEBROW__</div>
      <h1>__HEADLINE__</h1>
    </div>
    <div class="count"><b id="pos">1</b> von <span id="total">0</span></div>
  </header>
  <div class="rail"><span id="fill"></span></div>

  <p class="lede">__LEDE__</p>
  <p class="lede hidden" id="resumed"></p>

  <section id="task">
    <div class="pair">
      <div class="panel">
        <div class="tag only-paired">Links</div>
        <div class="stage" id="stage-0"></div>
      </div>
      <div class="panel only-paired">
        <div class="tag">Rechts</div>
        <div class="stage" id="stage-1"></div>
      </div>
    </div>

    <div class="cats only-single">
      __CATEGORY_BUTTONS__
    </div>
    <div class="choices only-paired">
      __CHOICE_BUTTONS__
    </div>

    <div class="quiet only-single" id="spot"></div>
    <div class="note"><textarea id="note" rows="1" placeholder="Nörgeln, falls nötig — freier Text, landet beim Befund"></textarea></div>
    <div class="bar">
      <button class="next only-single" id="next" type="button" disabled>Weiter &rarr;</button>
      <button class="ghost" id="back" type="button" disabled>&larr; Zurück</button>
      <button class="ghost stop" id="stop" type="button">Aufhören und Ergebnis zeigen</button>
      <span class="hint">__HINT__</span>
    </div>
  </section>

  <section id="done" class="hidden">
    <div class="done-card">
      <h2>Befund</h2>
      <p>Schick mir das zurück — mit dieser Zeile prüfe ich, welche Kennzahl dein Urteil trifft
         und welche nicht.</p>
      <code class="result" id="result"></code>
      <div class="tally" id="tally"></div>
      <div class="bar">
        <button class="ghost" id="resume" type="button">Weitermachen</button>
      </div>
    </div>
  </section>
</div>

<script>
const CONFIG = __CONFIG__;
const ITEMS = __ITEMS__;
const PAIRED = CONFIG.mode === 'paired';
const CATS = CONFIG.categories;
const CHOICES = CONFIG.choices;
const SOLO = CATS.filter((c) => c.kind === 'solo').map((c) => c.code);
const MOD = CATS.filter((c) => c.kind === 'modifier').map((c) => c.code);
const KEYS = {};
CATS.forEach((c) => { KEYS[c.key] = c.code; });
CHOICES.forEach((c) => c.keys.forEach((k) => { KEYS[k] = c.code; }));

// Radius (in panel pixels) within which a click counts as hitting the marker
// rather than placing a new one.
const MARKER_HIT = 14;

const picks = ITEMS.map(() => new Set());   // single mode: the categories ticked
const answers = ITEMS.map(() => null);      // paired mode: L / R / N
const notes = ITEMS.map(() => '');
const spots = ITEMS.map(() => null);        // where the judge saw it
const seen = ITEMS.map(() => false);
const spent = ITEMS.map(() => 0);           // ms of attention, not wall clock
let at = 0;
let shownAt = 0;

const $ = (id) => document.getElementById(id);
$('total').textContent = ITEMS.length;

// The whole cost of this instrument is human patience, so losing it to a tab
// crash at item 130 is the most expensive bug it could have. Everything is
// written on each step and restored on load; the key carries a fingerprint of
// the payload, so a different pass never resumes into a stale state.
function save() {
  try {
    localStorage.setItem(CONFIG.store, JSON.stringify({
      n: ITEMS.length, at, seen, notes, spent, spots, answers,
      picks: picks.map((s) => [...s]),
    }));
  } catch (e) { /* private mode — the pass still works, it just cannot resume */ }
}

function restore() {
  try {
    const raw = JSON.parse(localStorage.getItem(CONFIG.store) || 'null');
    if (!raw || raw.n !== ITEMS.length) return 0;
    (raw.picks || []).forEach((cs, i) => cs.forEach((c) => picks[i].add(c)));
    (raw.answers || []).forEach((v, i) => { answers[i] = v; });
    (raw.notes || []).forEach((v, i) => { notes[i] = v; });
    (raw.seen || []).forEach((v, i) => { seen[i] = v; });
    (raw.spent || []).forEach((v, i) => { spent[i] = v; });
    (raw.spots || []).forEach((v, i) => { spots[i] = v; });
    at = Math.min(raw.at || 0, ITEMS.length);
    return seen.filter(Boolean).length;
  } catch (e) { return 0; }
}

// Timing is per judgement, and only while the page is actually on screen: a
// judgement interrupted by a coffee break is not a slow judgement, and the
// difference decides whether a fatigue curve means anything.
function clockIn() { shownAt = Date.now(); }
function clockOut() {
  if (shownAt && at < ITEMS.length) spent[at] += Date.now() - shownAt;
  shownAt = 0;
}
document.addEventListener('visibilitychange', () => {
  if (document.hidden) clockOut(); else if (at < ITEMS.length) clockIn();
});

function answered(i) {
  if (PAIRED) return answers[i] !== null && answers[i] !== undefined;
  // „Unsicher" alone is not a verdict — it qualifies one.
  return [...picks[i]].some((c) => !MOD.includes(c));
}

// A panel inherits the item's crop image unless it brought its own — which is
// the normal case in paired mode, where both fits are drawn on ONE image so the
// two sides are pixel-identical apart from the line.
function panelOf(item, i) {
  const p = item.panels[i];
  return {
    w: p.w || item.w, h: p.h || item.h, img: p.img || item.img,
    // Never inherited from the item: the drawn ink is what the two panels are
    // being compared on, so a panel that borrowed it would show the other arm.
    strokes: p.strokes || [], widths: p.widths || [], fills: p.fills || [],
    context: p.context || item.context || [],
  };
}

function drawPanel(el, panel, interactive) {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', '0 0 ' + panel.w + ' ' + panel.h);
  svg.setAttribute('width', panel.w);
  svg.setAttribute('height', panel.h);
  svg.setAttribute('role', 'img');
  // A panel that draws INK (the word mode) fades the specimen instead of casing
  // its own strokes: a halo around a filled silhouette changes how heavy the
  // silhouette looks, and stroke weight is exactly what such a round judges.
  // Faded, the composed ink never has to fight a near-black ground, so it can
  // be drawn at its true weight — and the specimen stays there as the reference
  // for what written looks like.
  const INKED = panel.fills.length > 0 || panel.widths.length > 0;
  svg.setAttribute('aria-label', INKED
    ? 'Ausschnitt der Schriftplatte mit der darübergeschriebenen Komposition'
    : 'Ausschnitt der Schriftplatte mit der berechneten Mittellinie');
  const img = document.createElementNS(ns, 'image');
  img.setAttribute('href', panel.img);
  img.setAttribute('width', panel.w);
  img.setAttribute('height', panel.h);
  if (INKED) img.setAttribute('opacity', '0.45');
  svg.appendChild(img);
  // Cartographic casing: a light halo under the line so it stays legible INSIDE
  // the near-black stroke, not only where it leaves the ink. Without this the
  // eye can only find off-ink deviation and every wobble judgement would really
  // be an off-ink judgement. Fixed colours on purpose — the crop is a light
  // work surface in both themes.
  // The surrounding pen path FIRST and underneath: the letter was fitted inside
  // it, so without it a joined letter looks as if it stopped short — the round-1
  // defect. Grey, thin and unhaloed so it reads as context and can never be
  // mistaken for the line under judgement.
  for (const stroke of panel.context) {
    const c = document.createElementNS(ns, 'polyline');
    c.setAttribute('points', stroke.map((q) => q.join(',')).join(' '));
    c.setAttribute('fill', 'none');
    c.setAttribute('stroke', '#7a7268');
    c.setAttribute('stroke-width', '1');
    c.setAttribute('stroke-opacity', '0.7');
    c.setAttribute('stroke-dasharray', '3 3');
    c.setAttribute('stroke-linecap', 'round');
    svg.appendChild(c);
  }
  // Filled silhouettes are the word mode's letter bodies — the INK, not a
  // centerline, because a stroke a quarter too thin is invisible on a hairline.
  // Drawn flat and uncased: see INKED above for why a halo would be the wrong
  // safeguard here.
  // ONE path per pen stroke, fill-rule evenodd: a silhouette is an exterior
  // plus the counters it encloses, so drawn as separate polygons every loop
  // interior fills in solid and the writing reads as a blob. Same contract as
  // production (app/src/lib/svg.ts::ringsToPathD).
  for (const shape of panel.fills) {
    const g = document.createElementNS(ns, 'path');
    g.setAttribute('d', shape.map((ring) => 'M' + ring.map((q) => q.join(',')).join(' L') + ' Z').join(' '));
    g.setAttribute('fill', '#8f2d2d');
    g.setAttribute('fill-rule', 'evenodd');
    g.setAttribute('stroke', 'none');
    svg.appendChild(g);
  }
  // A per-stroke width is the composed stroke's own weight, in panel pixels;
  // without one the stroke is a judged CENTERLINE and keeps the cased hairline
  // the letter modes have always drawn (§3.5).
  if (panel.widths.length) {
    panel.strokes.forEach((stroke, i) => {
      const p = document.createElementNS(ns, 'polyline');
      p.setAttribute('points', stroke.map((q) => q.join(',')).join(' '));
      p.setAttribute('fill', 'none');
      p.setAttribute('stroke', '#8f2d2d');
      p.setAttribute('stroke-width', String(Math.max(1, panel.widths[i])));
      p.setAttribute('stroke-linecap', 'round');
      p.setAttribute('stroke-linejoin', 'round');
      svg.appendChild(p);
    });
  } else {
    for (const pass of [{ c: '#fdf6e8', w: 5, o: 0.85 }, { c: '#b03a3a', w: 2, o: 1 }]) {
      for (const stroke of panel.strokes) {
        const p = document.createElementNS(ns, 'polyline');
        p.setAttribute('points', stroke.map((q) => q.join(',')).join(' '));
        p.setAttribute('fill', 'none');
        p.setAttribute('stroke', pass.c);
        p.setAttribute('stroke-width', String(pass.w));
        p.setAttribute('stroke-opacity', String(pass.o));
        p.setAttribute('stroke-linecap', 'round');
        p.setAttribute('stroke-linejoin', 'round');
        svg.appendChild(p);
      }
    }
  }
  if (interactive && spots[at]) {
    for (const ring of [{ c: '#fdf6e8', w: 6 }, { c: '#2e6152', w: 2.5 }]) {
      const m = document.createElementNS(ns, 'circle');
      m.setAttribute('cx', spots[at][0]);
      m.setAttribute('cy', spots[at][1]);
      m.setAttribute('r', '11');
      m.setAttribute('fill', 'none');
      m.setAttribute('stroke', ring.c);
      m.setAttribute('stroke-width', String(ring.w));
      svg.appendChild(m);
    }
  }
  if (interactive) {
    svg.style.cursor = 'crosshair';
    svg.addEventListener('click', (ev) => {
      const r = svg.getBoundingClientRect();
      const x = Math.round(((ev.clientX - r.left) / r.width) * panel.w);
      const y = Math.round(((ev.clientY - r.top) / r.height) * panel.h);
      const cur = spots[at];
      // Clicking the marker again removes it; anywhere else moves it.
      spots[at] = cur && Math.hypot(cur[0] - x, cur[1] - y) < MARKER_HIT ? null : [x, y];
      save();
      render();
    });
  }
  el.replaceChildren(svg);
}

function render() {
  clockOut();
  if (at >= ITEMS.length) { finish(); return; }
  const item = ITEMS[at];
  const first = panelOf(item, 0);
  // Wide and short (a whole word) stacks on a phone instead of shrinking to two
  // thumbnails — see the `[data-wide="1"]` rule in the stylesheet.
  $('wrap').dataset.wide = first.h && first.w / first.h >= 2 ? '1' : '0';
  drawPanel($('stage-0'), first, !PAIRED);
  if (PAIRED) drawPanel($('stage-1'), panelOf(item, 1), false);
  $('pos').textContent = at + 1;
  $('fill').style.width = (100 * at / ITEMS.length) + '%';
  $('back').disabled = at === 0;
  $('note').value = notes[at];
  if (PAIRED) {
    document.querySelectorAll('button.choice').forEach((b) => {
      b.setAttribute('aria-pressed', String(answers[at] === b.dataset.c));
    });
  } else {
    document.querySelectorAll('button.cat').forEach((b) => {
      b.setAttribute('aria-pressed', String(picks[at].has(b.dataset.c)));
    });
    $('next').disabled = !answered(at);
    $('spot').textContent = spots[at]
      ? 'Stelle markiert — woanders klicken verschiebt sie, draufklicken löscht sie.'
      : 'Freiwillig: klick die Stelle an, die dir zuerst auffällt.';
  }
  clockIn();
}

function commitNote() {
  if (at < ITEMS.length) notes[at] = $('note').value.trim();
}

function toggle(code) {
  if (PAIRED || at >= ITEMS.length) return;
  const set = picks[at];
  if (set.has(code)) {
    set.delete(code);
  } else if (MOD.includes(code)) {
    set.add(code);
  } else if (SOLO.includes(code)) {
    const keep = MOD.filter((m) => set.has(m));   // the modifier survives a solo
    set.clear();
    set.add(code);
    keep.forEach((m) => set.add(m));
  } else {
    SOLO.forEach((s) => set.delete(s));
    set.add(code);
  }
  save();
  render();
}

function advance() {
  if (at >= ITEMS.length || !answered(at)) return;
  commitNote();
  clockOut();
  seen[at] = true;
  at += 1;
  save();
  render();
}

function choose(code) {
  if (!PAIRED || at >= ITEMS.length) return;
  answers[at] = code;
  advance();
}

function back() {
  if (at === 0) return;
  commitNote();
  clockOut();
  at -= 1;
  save();
  render();
}

function finish() {
  commitNote();
  clockOut();
  save();
  $('task').classList.add('hidden');
  $('done').classList.remove('hidden');
  const lines = [];
  ITEMS.forEach((item, i) => {
    if (!seen[i]) return;
    const verdict = PAIRED ? (answers[i] || '-') : CONFIG.order.filter((c) => picks[i].has(c)).join('');
    const spot = (!PAIRED && spots[i]) ? '#' + spots[i][0] + ',' + spots[i][1] : '';
    const secs = spent[i] ? '@' + Math.max(1, Math.round(spent[i] / 1000)) + 's' : '';
    // The result is ONE line per screen, and a bare Enter in the note textarea
    // is a newline by design (see the keydown handler). Flattened here rather
    // than in the parser: the emitted file has to BE the format it claims to
    // be, and it is committed verbatim. Left unflattened, a single Enter in a
    // free-text remark makes the whole round unparseable — after the human has
    // already spent the hours the round costs.
    const note = notes[i] ? ' "' + notes[i].replace(/\s+/g, ' ').replace(/"/g, "'") + '"' : '';
    lines.push(item.id + ':' + verdict + spot + secs + note);
  });
  const head = CONFIG.tag + ' geprueft=' + lines.length + ' von ' + ITEMS.length;
  $('result').textContent = [head].concat(lines).join('\n');
  const counted = PAIRED ? CHOICES : CATS;
  // Built as nodes rather than as markup: the labels are the page's own, but a
  // tally that cannot inject is one less thing to think about when a builder
  // starts passing its own.
  $('tally').replaceChildren(...counted.map((c) => {
    const n = ITEMS.filter((_, i) => seen[i] && (PAIRED ? answers[i] === c.code : picks[i].has(c.code))).length;
    const span = document.createElement('span');
    span.textContent = c.tally + ': ';
    const b = document.createElement('b');
    b.textContent = String(n);
    span.appendChild(b);
    return span;
  }));
}

document.querySelectorAll('button.cat').forEach((b) => {
  b.addEventListener('click', () => toggle(b.dataset.c));
});
document.querySelectorAll('button.choice').forEach((b) => {
  b.addEventListener('click', () => choose(b.dataset.c));
});
$('next').addEventListener('click', advance);
$('back').addEventListener('click', back);
$('stop').addEventListener('click', () => { if (at < ITEMS.length) finish(); });
$('resume').addEventListener('click', () => {
  $('done').classList.add('hidden');
  $('task').classList.remove('hidden');
  render();
});

document.addEventListener('keydown', (e) => {
  if (e.altKey) return;
  if (e.target && e.target.tagName === 'TEXTAREA') {
    // Ctrl/Cmd+Enter advances from inside the note; a bare Enter is a newline,
    // so a half-written thought is never submitted by reflex.
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); advance(); }
    return;
  }
  if (e.ctrlKey || e.metaKey) return;
  const code = KEYS[e.key];
  if (code) { e.preventDefault(); if (PAIRED) choose(code); else toggle(code); }
  else if (e.key === 'Enter') { e.preventDefault(); advance(); }
  else if (e.key === 'Backspace') { e.preventDefault(); back(); }
});

const resumed = restore();
if (resumed) {
  const box = $('resumed');
  box.textContent = 'Fortgesetzt — ' + resumed + ' bereits beurteilt, weiter bei Stück ' + (at + 1)
    + '. Der Stand wird nach jedem Schritt gespeichert.';
  box.classList.remove('hidden');
}
render();
</script>
"""


if __name__ == "__main__":
    raise SystemExit(main())
