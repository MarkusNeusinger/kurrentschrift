"""Build the Streifenplan — the committed, append-only strip plan.

Partitions the Wortvorrat into Streifen (stable word groups, one per sheet
row) so that the FIRST strips carry maximum coverage velocity and later
strips grow frequent AND rare items evenly:

* **Phase A — Startdeckung.** Greedy weighted set cover: repeatedly pick the
  pool word covering the most still-unseen items, weighted by Übergangsraum
  frequency plus a floor so rare joins are never drowned. Ends when every
  pool-reachable item has one planned Beleg.
* **Phase B — gleichmäßiger Aufbau.** Deficit-driven: pick the word that
  reduces the most remaining Soll (two-tier targets, coverage.py), words may
  repeat up to ``MAX_REPEAT_PER_WAVE`` times per wave — repetitions are the
  point (mvp-roadmap M1).
* **Packing.** The ordered word stream is cut into row-sized strips against
  the widest preset (Sütterlin, 6 mm x-height) so a strip fits every script.

Append-never: strips, once assigned, are immutable — an existing
``streifen.json`` is loaded verbatim, its planned coverage seeds the new
wave, and the builder refuses to renumber or rewrite anything it did not
create. The plan is TRAINING data, not a measurement set (proposal §4).

``pin`` is the exception the append-never rule leaves room for. A word the
author wants written NOW (``corpus.PINNED_FIRST``) cannot be pushed into a
frozen strip, so it gets its OWN appended strip, and that strip is registered
in ``plan["pins"]`` — the block ``plan.ordered_strips`` puts at the head of
plan order. Nothing existing moves; only what comes first changes. A pinned
strip leaves the front of the queue the ordinary way, by being written
(``belegt``).

    uv run python -m tools.eigenhand.pool build --strips 60
    uv run python -m tools.eigenhand.pool pin
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from core.eigenhand import coverage
from core.eigenhand.geometry import PRESETS, pack_words_into_rows
from core.eigenhand.plan import STREIFEN_JSON, dump_plan, empty_plan, load_plan, strip_id
from tools.eigenhand.corpus import PINNED_FIRST, pool_entries, shaping_form
from tools.eigenhand.universe import load_universe


PACKING_STYLE = "suetterlin"  # widest preset: what fits here fits every script
MAX_REPEAT_PER_WAVE = 4
FLOOR_GAIN = 0.05  # additive floor so rare items keep pulling in Phase A
DEFICIT_FLOOR = 0.01
# Breadth before repetition (owner wish 2026-08-22: repeat words as little
# as possible, so that eventually nearly every important word has been
# written at least once): a word already planned anywhere in the plan
# re-enters Phase B only when no fresh word delivers comparable benefit —
# its benefit is damped by this factor per prior planning, across ALL waves.
REPEAT_DAMPING = 0.3
# Hard per-GLYPH floor (owner, 2026-08-23: a glyph like q appearing once is
# unacceptable — every letter and sign at least three times): before the
# frequency-driven build-out, phase A2 tops every glyph key (summed over
# positions) up to this count. A guarantee, not a preference — repeat
# damping does not apply here; only MAX_REPEAT_PER_WAVE and the wave
# capacity bound it, and unmet leftovers are reported, never silent.
GLYPH_MIN_PLANNED = 3


def _planned_word_uses(plan: dict) -> Counter[str]:
    """How often each word is already planned, across all waves."""
    return Counter(word for strip in plan["strips"].values() for word in strip["words"])


def soll_weights(universe_items: dict[str, float]) -> dict[str, float]:
    """The Übergangsraum ∪ pool items — the complete weight table.

    Pool-only items (capitals, historic vocabulary the lowercased corpus
    cannot carry) enter at weight 0 → floor target. This union is what gets
    pushed to the server (`universe --push`): the server holds the COMPLETE
    table and never needs the pool, which lives in `tools/` where the API
    cannot import it.
    """
    weights = dict(universe_items)
    for entry in pool_entries():
        for item in coverage.word_items(shaping_form(entry)):
            weights.setdefault(item, 0.0)
    return weights


def soll_model(universe_items: dict[str, float]) -> tuple[dict[str, float], dict[str, int]]:
    """(weights, two-tier targets) over the Übergangsraum ∪ pool items.

    Shared by the wave builder, the Bestandsbericht and — through the stored
    table — the server, so Soll always means the same thing: the targets come
    from `coverage.soll_from_weights`, the one derivation on both surfaces.
    """
    return coverage.soll_from_weights(soll_weights(universe_items))


def build_wave(plan: dict, target_strips: int, universe_items: dict[str, float]) -> tuple[dict, dict]:
    """Append one wave of ``target_strips`` strips to the plan (pure, deterministic)."""
    entries = pool_entries()
    forms = {e["word"]: shaping_form(e) for e in entries}
    word_items: dict[str, list[str]] = {w: coverage.word_items(f) for w, f in forms.items()}

    weights = dict(universe_items)
    for items in word_items.values():
        for item in items:
            weights.setdefault(item, 0.0)
    max_weight = max(weights.values(), default=1.0) or 1.0
    norm = {item: w / max_weight for item, w in weights.items()}
    targets = {item: coverage.target_for_weight(w, max_weight) for item, w in weights.items()}

    planned = coverage.plan_items(plan)
    word_uses = _planned_word_uses(plan)
    usage_this_wave: Counter[str] = Counter()
    stream: list[str] = []
    preset = PRESETS[PACKING_STYLE]

    def packed_rows(extra: str | None = None) -> int:
        words = stream + ([extra] if extra else [])
        return len(pack_words_into_rows(words, preset, forms=forms))

    def try_add(word: str) -> bool:
        if packed_rows(word) > target_strips:
            return False
        stream.append(word)
        usage_this_wave[word] += 1
        word_uses[word] += 1
        planned.update(word_items[word])
        return True

    # --- Phase A: cover every reachable item once -----------------------------
    while True:
        best: tuple[float, int, str] | None = None
        for word, items in word_items.items():
            if usage_this_wave[word]:
                continue
            gain = sum(norm[item] + FLOOR_GAIN for item in set(items) if planned[item] == 0)
            if gain <= 0:
                continue
            rank = (-gain, len(word), word)
            if best is None or rank < (best[0], best[1], best[2]):
                best = rank
        if best is None:
            break
        if not try_add(best[2]):
            break

    # --- Phase A2: hard glyph floor — every glyph key planned >= GLYPH_MIN ----
    def glyph_totals() -> Counter[str]:
        totals: Counter[str] = Counter()
        for item, count in planned.items():
            if coverage.POSITION_SEP in item and coverage.JOIN_SEP not in item:
                totals[item.split(coverage.POSITION_SEP)[0]] += count
        return totals

    word_glyphs: dict[str, Counter[str]] = {
        w: Counter(i.split(coverage.POSITION_SEP)[0] for i in items if coverage.JOIN_SEP not in i)
        for w, items in word_items.items()
    }
    # The deficit runs over every REACHABLE key — every glyph any pool word can
    # supply — not just the ones phase A already planned. A key still at zero is
    # exactly the case the floor exists for; counting only the planned keys
    # would make it invisible instead.
    reachable = {key for keys in word_glyphs.values() for key in keys}
    floor_unmet: list[str] = []
    while True:
        totals = glyph_totals()
        under = {key: GLYPH_MIN_PLANNED - totals[key] for key in reachable if totals[key] < GLYPH_MIN_PLANNED}
        if not under:
            break
        best_floor: tuple[float, int, str] | None = None
        for word, keys in word_glyphs.items():
            if usage_this_wave[word] >= MAX_REPEAT_PER_WAVE:
                continue
            fills = sum(min(need, keys[key]) for key, need in under.items())
            if fills <= 0:
                continue
            rank = (-float(fills), len(word), word)
            if best_floor is None or rank < best_floor:
                best_floor = rank
        if best_floor is None or not try_add(best_floor[2]):
            floor_unmet = sorted(under)
            break
    # Not printed here — the leftovers travel in stats["floor_unmet"] and main()
    # warns, so this stays a pure function that a caller can run in a loop.

    # --- Phase B: even build-out toward the two-tier targets ------------------
    exhausted = False
    while not exhausted and packed_rows() < target_strips:
        candidates: list[tuple[float, int, str]] = []
        for word, items in word_items.items():
            if usage_this_wave[word] >= MAX_REPEAT_PER_WAVE:
                continue
            benefit = 0.0
            item_counts = Counter(items)
            for item, count in item_counts.items():
                deficit = targets[item] - planned[item]
                if deficit > 0:
                    benefit += min(deficit, count) * (norm[item] + DEFICIT_FLOOR)
            # Breadth before repetition: damp already-planned words hard.
            benefit *= REPEAT_DAMPING ** word_uses[word]
            if benefit > 0:
                candidates.append((-benefit, len(word), word))
        if not candidates:
            break
        candidates.sort()
        for _, _, word in candidates[:20]:
            if try_add(word):
                break
        else:
            exhausted = True

    strips = pack_words_into_rows(stream, preset, forms=forms)
    wave_no = len(plan["waves"])
    next_number = max((int(s[1:]) for s in plan["strips"]), default=0) + 1
    ids: list[str] = []
    for words in strips:
        sid = strip_id(next_number)
        next_number += 1
        plan["strips"][sid] = {"wave": wave_no, "words": words}
        ids.append(sid)
    plan["waves"].append({"wave": wave_no, "strips": ids})

    # The plan must be shapeable WITHOUT the curation source: `forms` carries
    # every planned word whose shaping form differs from its spelling, so a
    # reader that only has streifen.json (the API) still shapes `Amtszeit` as
    # `Amts|zeit`. Append-never like the strips — an existing entry is never
    # rewritten, so a later corpus edit cannot silently reshape frozen rows.
    frozen_forms = dict(plan.get("forms", {}))
    for strip in plan["strips"].values():
        for word in strip["words"]:
            if forms.get(word, word) != word:
                frozen_forms.setdefault(word, forms[word])
    plan["forms"] = dict(sorted(frozen_forms.items()))

    stats = {
        "wave": wave_no,
        "strips": len(ids),
        "words": len(stream),
        "distinct_words": len(set(stream)),
        "items_covered": sum(1 for item in weights if planned[item] > 0),
        "items_total": len(weights),
        "floor_unmet": floor_unmet,
    }
    return plan, stats


def pin_words(plan: dict, words: list[str]) -> tuple[dict, dict]:
    """Append the pinned words as leading strips (pure, deterministic).

    One word cannot be added to a frozen strip, so every pinned word gets a
    strip of its own, appended and registered in ``plan["pins"]``: plan order
    then starts with them, and the first Bogen printed after this carries them
    in its first rows. A word already planned anywhere is skipped — a pin says
    "write this early", not "write this again", and once it is on a strip it
    has a place in the queue.

    The pinned words must be curated pool words: the plan is the API's only
    word source, so an unknown word would leave the sheet without a shaping
    form and the Bestand without an entry.
    """
    entries = pool_entries()
    forms = {e["word"]: shaping_form(e) for e in entries}
    unknown = [word for word in words if word not in forms]
    if unknown:
        raise SystemExit(f"not in the Wortvorrat: {', '.join(unknown)} — curate it in corpus.py first")

    already = _planned_word_uses(plan)
    fresh = [word for word in dict.fromkeys(words) if not already[word]]
    ids: list[str] = []
    if fresh:
        wave_no = len(plan["waves"])
        next_number = max((int(sid[1:]) for sid in plan["strips"]), default=0) + 1
        # ONE strip per pinned word, not the row packing a wave uses: pins are
        # few and deliberate, and a word pinned for its own sake should get the
        # whole row width (the box generator hands the spare width back to the
        # words on the row). Packing two of them together would also make the
        # promise "its own strip" untrue the moment a second pin is added.
        for word in fresh:
            sid = strip_id(next_number)
            next_number += 1
            plan["strips"][sid] = {"wave": wave_no, "words": [word]}
            ids.append(sid)
        plan["waves"].append({"wave": wave_no, "strips": ids, "pin": True})
        plan["pins"] = list(plan.get("pins", [])) + ids
        frozen_forms = dict(plan.get("forms", {}))
        for word in fresh:
            if forms[word] != word:
                frozen_forms.setdefault(word, forms[word])
        plan["forms"] = dict(sorted(frozen_forms.items()))
    return plan, {"strips": ids, "pinned": fresh, "skipped": [w for w in words if w not in fresh]}


def verify_immutable(before: dict, after: dict) -> None:
    """Append-never guard: every pre-existing strip must survive verbatim."""
    for sid, strip in before["strips"].items():
        if after["strips"].get(sid) != strip:
            raise SystemExit(f"append-never violated: strip {sid} changed — refusing to write")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)
    build = sub.add_parser("build", help="append one wave to streifen.json")
    build.add_argument("--strips", type=int, default=60, help="row-sized strips this wave (default: %(default)s)")
    build.add_argument("--out", type=Path, default=STREIFEN_JSON, help="plan path (default: %(default)s)")
    build.add_argument("--universe", type=Path, default=None, help="Übergangsraum path (default: local)")
    pin = sub.add_parser("pin", help="append the pinned words as leading strips")
    pin.add_argument("--word", action="append", default=None, help="pin this word (default: corpus.PINNED_FIRST)")
    pin.add_argument("--out", type=Path, default=STREIFEN_JSON, help="plan path (default: %(default)s)")
    args = ap.parse_args(argv)

    plan = load_plan(args.out) if args.out.exists() else empty_plan()
    before = json.loads(json.dumps(plan))

    if args.cmd == "pin":
        plan, pinned = pin_words(plan, args.word or PINNED_FIRST)
        verify_immutable(before, plan)
        args.out.write_text(dump_plan(plan), encoding="utf-8")
        listed = ", ".join(f"{sid} ({' '.join(plan['strips'][sid]['words'])})" for sid in pinned["strips"])
        print(f"wrote {args.out}: {listed or 'no new strip'}; plan order now leads with {pinned['strips'] or '—'}")
        if pinned["skipped"]:
            print(f"already planned, not pinned again: {', '.join(pinned['skipped'])}")
        return 0

    universe = load_universe(args.universe)
    plan, stats = build_wave(plan, args.strips, universe["items"])
    verify_immutable(before, plan)
    args.out.write_text(dump_plan(plan), encoding="utf-8")
    print(
        f"wrote {args.out}: wave {stats['wave']} with {stats['strips']} strips, "
        f"{stats['words']} words ({stats['distinct_words']} distinct); "
        f"coverage {stats['items_covered']}/{stats['items_total']} items"
    )
    if stats["floor_unmet"]:
        print(
            f"WARNING: glyph floor {GLYPH_MIN_PLANNED} unmet for {', '.join(stats['floor_unmet'])} — "
            "add carrier words or strips"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
