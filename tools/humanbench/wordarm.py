"""wordarm — compose ONE arm of a humanbench word round from the frozen fixtures.

    uv run python -m tools.humanbench.wordarm --arm Basis --out temp/basis.json
    uv run python -m tools.humanbench.wordarm --arm LF11 --laufform temp/lf11.json \\
        --registration-from temp/basis.json --out temp/lf11.json
    uv run python -m tools.humanbench.wordarm --arm Platten-Nib --nib 0.097 --out temp/nib.json

The reference producer of the arm-file contract that
``tools/humanbench/build.py`` draws a word round from. It is a producer and
not a part of the instrument: the builder never composes anything itself, so
an arm can equally be written by whatever tool a candidate lives in — the file
is the interface, this module is the one that covers the two arms available
today (a candidate Laufform card and a different nib) plus the base they are
measured against.

Composition mirrors ``tools/wordbench/run.py`` line for line and by IMPORT, not
by restatement: same frozen templates, same Laufform overlay, same
``compose_word``, and the placement is the word bench's own bounded
registration (``core.word_metric.score_word``). An arm composed a second way
would be judged against a specimen the ruler never scored, and the human
verdict could then not be held against the numbers at all.

Two things are deliberately NOT in the arm file: any name of the mechanism per
word, and any score. The file carries geometry and a registration; which side
of a screen it lands on is the builder's seed, and what it means is the key.

``--synthetic-defect`` exists for ONE purpose — accepting the instrument
without a real candidate. It writes a loudly labelled arm (``synthetic`` in the
file and in the builder's stamp) whose deviation from the base is known in
advance, so „the page renders and the analysis reproduces the pre-registered
decision" can be checked before an author spends a session on it. It is never a
candidate: a defect somebody injected is not a change anybody proposed.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from core.compose import compose_word
from core.pipeline import render_payload_for_template
from core.shaping import GlyphSlot
from core.word_metric import score_word
from tools.humanbench.build import DEFAULT_FIXTURES, DEFAULT_STYLE, REPO_ROOT, WORD_ARM_FORMAT, load_fixture_words


DEFAULT_SOURCE_ID = "suetterlin-1922"

# How far a synthetic zigzag pushes each successive vertex off the drawn path,
# in x-heights. Chosen at the size of the defect it stands in for: the
# anchor-median jitter of a Laufform row measures a few hundredths of an
# x-height, which is exactly the range every frozen ruler resamples away.
ZIGZAG_AMPLITUDE = 0.02


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _payload_cache(rows: dict[str, dict], ratio: list, resolver: str, nib: float | None):  # noqa: ANN202
    cache: dict[str, dict | None] = {}

    def payload_for(key: str) -> dict | None:
        if key not in cache:
            row = rows.get(key)
            cache[key] = render_payload_for_template(row, ratio, resolver, nib) if row else None
        return cache[key]

    return payload_for


def compose_arm(
    root: Path,
    *,
    laufform: dict[str, dict] | None = None,
    no_laufform: bool = False,
    nib: float | None = None,
    entries: set[str] | None = None,
) -> tuple[dict[str, dict], dict]:
    """Compose every scorable fixture word once, and place it the ruler's way.

    Returns the arm's ``words`` block plus the settings that produced it. The
    Laufform overlay replaces exactly the keys the draft names and leaves the
    rest on their frozen rows — the word bench's ``--laufform`` discipline,
    because an overlay that silently dropped the unnamed keys would compose a
    different letter set from the base and the round would compare two things.
    """
    manifest = load_json(root / "manifest.json")
    templates = load_json(root / "templates.json")
    laufform_path = root / "templates_laufform.json"
    rows: dict[str, dict] = {} if no_laufform or not laufform_path.exists() else load_json(laufform_path)
    for key, row in (laufform or {}).items():
        rows[key] = row
    resolver = manifest.get("width_resolver") or "pressure"
    ratio = manifest.get("style_ratio") or [1, 1, 1]
    frozen_nib = manifest.get("constant_nib_units")
    used_nib = frozen_nib if nib is None else nib

    payload_for = _payload_cache(templates, ratio, resolver, used_nib)
    laufform_for = _payload_cache(rows, ratio, resolver, used_nib)

    words: dict[str, dict] = {}
    failed: list[str] = []
    for entry in load_fixture_words(root):
        entry_id = entry["id"]
        if entries is not None and entry_id not in entries:
            continue
        word_dir = root / entry_id
        meta = load_json(word_dir / "word.json")
        slots = [GlyphSlot(**s) for s in meta["slots"]]
        skel = np.load(word_dir / "ref_skel.npz")["skel"]
        try:
            composed = compose_word(
                slots,
                {s.key: payload_for(s.key) for s in slots if s.key},
                laufform_by_key={s.key: lf for s in slots if s.key and (lf := laufform_for(s.key)) is not None} or None,
            )
            report = score_word(
                composed,
                {"rect": meta["rect"], "baseline_y": meta["baseline_y"], "midband_y": meta["midband_y"]},
                skel,
                used_nib,
            )
        except Exception as exc:  # noqa: BLE001 — a word that will not compose is a result, named
            failed.append(f"{entry_id} ({type(exc).__name__})")
            continue
        if report.get("failed") or not report.get("registration"):
            failed.append(f"{entry_id} (missing {composed['missing']})")
            continue
        words[entry_id] = arm_drawing(composed, report["registration"])
    settings = {
        "width_resolver": resolver,
        "nib_units": used_nib,
        "nib_overridden": nib is not None,
        "laufform": "none" if no_laufform else ("overlay" if laufform else "frozen"),
        "laufform_overlay_keys": sorted(laufform) if laufform else [],
        "exported_at": manifest.get("exported_at"),
        "failed": failed,
    }
    return words, settings


def arm_drawing(composed: dict, registration: dict) -> dict:
    """One composed word as INK: filled silhouettes plus the capsule strokes.

    A glyph body ships as ``rings`` (its own silhouette, Schwellzug included);
    a generated connector ships as a centerline with the constant width the
    composer inked it at. Drawing the ink rather than the centerline is the
    whole point of the word mode — a stroke a quarter too thin is invisible on
    a hairline, and the authenticity question is about how the writing looks.
    """
    strokes, fills = [], []
    for item in composed["items"]:
        rings = item.get("rings")
        if rings:
            fills.extend([[list(map(float, p)) for p in ring] for ring in rings])
        else:
            strokes.append(
                {
                    "points": [list(map(float, p)) for p in item["centerline"]],
                    "width": float(item.get("stroke_width") or 0.0),
                }
            )
    return {
        "registration": {
            "xh_px": float(registration["xh_px"]),
            "tx": float(registration["tx"]),
            "ty": float(registration["ty"]),
        },
        "strokes": strokes,
        "fills": fills,
    }


def pin_registration(words: dict[str, dict], reference: dict[str, dict]) -> list[str]:
    """Take the registration of another arm, word by word; report what it lacks.

    Blindness leaks through placement: a candidate that sits systematically
    lower is readable as a group across a round even though the seed randomises
    the sides. A mechanism that does not move the placement therefore borrows
    the base's registration instead of searching its own.
    """
    missing = []
    for entry_id, drawing in words.items():
        pinned = reference.get(entry_id)
        if pinned is None:
            missing.append(entry_id)
            continue
        drawing["registration"] = dict(pinned["registration"])
    return missing


def zigzag(words: dict[str, dict], amplitude: float = ZIGZAG_AMPLITUDE) -> None:
    """Push every second vertex off the path — the injected zigzag, in place.

    The stand-in for the defect the audit of 2026-09-02 named first: the
    per-anchor median of a Laufform row leaves a saw-tooth that every frozen
    ruler resamples away. Applied to the drawn ink (strokes AND silhouette
    rings), because that is what a human sees.
    """
    for drawing in words.values():
        for stroke in drawing["strokes"]:
            stroke["points"] = _saw(stroke["points"], amplitude)
        drawing["fills"] = [_saw(ring, amplitude) for ring in drawing["fills"]]


def _saw(points: list[list[float]], amplitude: float) -> list[list[float]]:
    array = np.asarray(points, dtype=float)
    if len(array) < 3:
        return points
    tangents = np.gradient(array, axis=0)
    lengths = np.hypot(tangents[:, 0], tangents[:, 1])
    lengths[lengths == 0] = 1.0
    normals = np.column_stack([-tangents[:, 1] / lengths, tangents[:, 0] / lengths])
    signs = np.where(np.arange(len(array)) % 2 == 0, 1.0, -1.0)[:, None]
    return [[round(float(x), 6), round(float(y), 6)] for x, y in array + amplitude * signs * normals]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.humanbench.wordarm",
        description="Compose one arm of a humanbench word round from a frozen word bench fixture root.",
    )
    parser.add_argument(
        "--arm", required=True, help="the arm's name; it appears in the KEY and the stamp, never on the page"
    )
    parser.add_argument("--out", required=True, type=Path, help="arm file to write")
    parser.add_argument("--fixtures", default=DEFAULT_FIXTURES, help=f"fixture root [{DEFAULT_FIXTURES}]")
    parser.add_argument("--style", default=DEFAULT_STYLE, help=f"fixture style directory [{DEFAULT_STYLE}]")
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID, help=f"fixture set directory [{DEFAULT_SOURCE_ID}]")
    parser.add_argument("--entries", default=None, help="comma-separated fixture entry ids to compose")
    parser.add_argument(
        "--laufform", type=Path, default=None, help="candidate Laufform rows, as the word bench takes them"
    )
    parser.add_argument(
        "--no-laufform", action="store_true", help="compose chart-only, without the frozen running forms"
    )
    parser.add_argument(
        "--nib", type=float, default=None, help="constant nib half-width in x-heights [the frozen pooled one]"
    )
    parser.add_argument(
        "--registration-from",
        type=Path,
        default=None,
        help="reuse this arm file's placement instead of searching one — for a mechanism that does not move it",
    )
    parser.add_argument(
        "--synthetic-defect",
        choices=("zigzag",),
        default=None,
        help="INSTRUMENT ACCEPTANCE ONLY: inject a known defect into the composed ink; never a candidate",
    )
    parser.add_argument("--stamp", default=None, help="build timestamp [the system clock]")
    return parser


def load_laufform_draft(path: Path) -> dict[str, dict]:
    """Accept both shapes the word bench accepts: full rows or a harvest draft."""
    raw = load_json(path)
    rows = raw.get("rows") if isinstance(raw, dict) and "rows" in raw else raw
    if not isinstance(rows, dict):
        raise SystemExit(f"{path}: expected a mapping glyph_key → row")
    return rows


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    fixtures = Path(args.fixtures) if Path(args.fixtures).is_absolute() else REPO_ROOT / args.fixtures
    root = fixtures / args.style / args.source_id
    entries = {e.strip() for e in args.entries.split(",") if e.strip()} if args.entries else None
    laufform = load_laufform_draft(args.laufform) if args.laufform else None

    words, settings = compose_arm(root, laufform=laufform, no_laufform=args.no_laufform, nib=args.nib, entries=entries)
    if not words:
        raise SystemExit(f"{root}: nothing composed — {settings['failed'][:5]}")
    if args.registration_from:
        reference = load_json(args.registration_from).get("words") or {}
        missing = pin_registration(words, reference)
        settings["registration"] = f"pinned to {args.registration_from}"
        if missing:
            print(f"WARNING: {len(missing)} word(s) had no pinned registration and keep their own: {missing[:8]}")
    else:
        settings["registration"] = "own (searched by the word bench ruler)"
    if args.synthetic_defect == "zigzag":
        zigzag(words)

    payload = {
        "format": WORD_ARM_FORMAT,
        "arm": args.arm,
        "style": args.style,
        "source_id": args.source_id,
        "fixture_root": str(root),
        "tool": "tools.humanbench.wordarm",
        "built_at": args.stamp or datetime.now(UTC).isoformat(timespec="seconds"),
        "settings": settings,
        "words": words,
    }
    if args.synthetic_defect:
        # Said in the file itself, because the builder copies the arm's metadata
        # into the round's stamp: a round built on an injected defect must never
        # be readable later as a round about a real candidate.
        payload["synthetic"] = {"defect": args.synthetic_defect, "amplitude_xh": ZIGZAG_AMPLITUDE}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")

    print(f"arm {args.arm}: {len(words)} words from {root.name} → {args.out} ({args.out.stat().st_size / 1e6:.1f} MB)")
    print(f"  nib {settings['nib_units']:.5f}{' (overridden)' if settings['nib_overridden'] else ''}")
    print(f"  laufform {settings['laufform']} · registration {settings['registration']}")
    if settings["failed"]:
        print(f"  WARNING: {len(settings['failed'])} word(s) did not compose: {', '.join(settings['failed'][:8])}")
    if args.synthetic_defect:
        print(f"  SYNTHETIC {args.synthetic_defect} injected — instrument acceptance only, never a candidate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
