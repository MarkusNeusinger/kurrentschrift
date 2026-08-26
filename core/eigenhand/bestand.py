"""The Bestand — what one hand already holds, as a structure rather than a print.

Three numbers, one definition each, shared by the terminal report
(``tools/eigenhand/report.py``) and the admin view, so the two surfaces can
never disagree about the same hand:

* **Ist** — the coverage items of the accepted Fassungen, shaped through the
  plan's own forms; withdrawn and rejected rows never count.
* **Möglich** — the items the COMMITTED strip plan carries. That is the honest
  denominator for "how many are there in total": what this hand will hold once
  every planned strip is written, capitals · digits · signs included.
* **Soll** — the two-tier target model, weighted by the Übergangsraum. The
  weight table is derived from consult-only corpora and never committed; the
  local chain reads its file, the server the row `tools.eigenhand.universe
  --push` stored (author's decision 2026-08-25). So ``quoten`` is optional:
  without a table the Bestand still answers how much of the plan is written,
  just not how much of real German that is.

Pure: a plan and a Kartei-shaped dict in, JSON-ready data out. Where the
Kartei comes from — ``kartei.json`` locally, the ``eigenhand_*`` tables on the
server — this module never learns.
"""

from __future__ import annotations

from collections import Counter

from core.eigenhand import coverage
from core.eigenhand.bogen import select_strips
from core.eigenhand.kartei import accepted_fassungen, strip_state
from core.eigenhand.plan import shaping_form_of


# The order the admin view lists the glyph classes in — plain letters first,
# then the classes a natural word list under-serves (owner, 2026-08-22: "auch
# Sonderzeichen, Zahlen").
BUCKETS = ("klein", "gross", "ligatur", "ziffer", "zeichen")


def ist_counts(kartei: dict, plan: dict) -> Counter[str]:
    """Item → Beleg count over the hand's accepted Fassungen (shaped forms).

    THE definition of "written": a strip counts as often as it was accepted,
    and its words are shaped before they are counted, so a Fuge or a long ſ
    contributes the joins it really produces.
    """
    counts: Counter[str] = Counter()
    for strip, _fassung in accepted_fassungen(kartei):
        for word in plan["strips"][strip]["words"]:
            counts.update(coverage.word_items(shaping_form_of(plan, word)))
    return counts


def quoten(ist: Counter[str], weights: dict[str, float], targets: dict[str, int]) -> dict[str, float | int]:
    """Erstbeleg- and Ausbau-Quote, each unweighted and Übergangsraum-weighted.

    The weighted number is the honest headline: the corpus tail cannot drag it
    down faster than its real-text relevance warrants.
    """
    total_weight = sum(weights.values()) or 1.0
    erstbeleg = sum(1 for item in weights if ist[item] > 0)
    soll_sum = sum(targets.values())
    ausbau = sum(min(ist[item], targets[item]) for item in targets)
    ausbau_num = sum(min(ist[item], targets[item]) * (weights[item] / total_weight) for item in targets)
    ausbau_den = sum(targets[item] * (weights[item] / total_weight) for item in targets) or 1.0
    # `erstbeleg`, `ausbau`, `belege` and `soll` are the project's own counting
    # units (glossar.md) and stay German; everything around them is English.
    return {
        "items": len(weights),
        "erstbeleg": erstbeleg,
        "erstbeleg_share": erstbeleg / max(1, len(weights)),
        "erstbeleg_weighted": sum(w for item, w in weights.items() if ist[item] > 0) / total_weight,
        "soll_belege": soll_sum,
        "ausbau": ausbau,
        "ausbau_share": ausbau / max(1, soll_sum),
        "ausbau_weighted": ausbau_num / ausbau_den,
    }


def _glyph_layer(ist: Counter[str], planned: Counter[str]) -> dict[str, dict]:
    """Per bucket: how many of the plan's keys are written, and every key by name."""
    layer: dict[str, dict] = {bucket: {"covered": 0, "possible": 0, "belege": 0, "keys": []} for bucket in BUCKETS}
    # Iterating the PLAN (not the Ist) is what makes the empty ones visible: a
    # key nobody has written yet has to appear with 0, or the view answers
    # "which letters exist" with a list of the letters that exist.
    for key in sorted(planned, key=lambda k: (coverage.classify_key(k), k)):
        bucket = layer[coverage.classify_key(key)]
        bucket["possible"] += 1
        bucket["belege"] += ist[key]
        bucket["covered"] += 1 if ist[key] else 0
        bucket["keys"].append({"key": key, "belege": ist[key], "planned": planned[key]})
    return layer


def _join_layer(ist: Counter[str], planned: Counter[str]) -> dict:
    """The joins the same way, listed in full — the whole point is which are missing."""
    rows = [
        {"item": item, "belege": ist[item], "planned": planned[item]}
        for item in sorted(planned, key=lambda i: (-planned[i], i))
    ]
    return {
        "covered": sum(1 for row in rows if row["belege"]),
        "possible": len(rows),
        "belege": sum(row["belege"] for row in rows),
        "rows": rows,
    }


def bestand(
    plan: dict, kartei: dict, queue_rows: int = 9, soll: tuple[dict[str, float], dict[str, int]] | None = None
) -> dict:
    """One hand's whole Bestand: strips, Fassungen, Bögen, glyphs, joins, Quoten."""
    ist = ist_counts(kartei, plan)
    ist_glyphs, ist_joins = coverage.split_items(ist)
    plan_glyphs, plan_joins = coverage.split_items(coverage.plan_items(plan))

    states = Counter(strip_state(kartei, strip) for strip in plan["strips"])
    fassungen = [f for record in kartei["strips"].values() for f in record.get("fassungen", [])]
    sheets = sorted(kartei["sheets"])

    return {
        "hand": kartei["hand"],
        "style": kartei["style"],
        # `belegt` · `unterwegs` · `geplant` and `angenommen` · `verworfen` ·
        # `zurueckgezogen` are the Kartei's own state and status VALUES
        # (kartei.strip_state, apply.py) — data, not identifiers invented here.
        "strips": {
            "total": len(plan["strips"]),
            "belegt": states["belegt"],
            "unterwegs": states["unterwegs"],
            "geplant": states["geplant"],
        },
        "fassungen": {
            "angenommen": len(accepted_fassungen(kartei)),
            "verworfen": sum(1 for f in fassungen if f["status"] == "verworfen"),
            "zurueckgezogen": sum(1 for f in fassungen if f["status"] == "zurueckgezogen"),
        },
        "sheets": {"printed": len(sheets), "last": sheets[-1] if sheets else None},
        "glyphs": _glyph_layer(ist_glyphs, plan_glyphs),
        "joins": _join_layer(ist_joins, plan_joins),
        "quoten": quoten(ist, *soll) if soll else None,
        "queue": select_strips(plan, kartei, queue_rows, 1, soll),
        "redo": [entry["strip"] for entry in kartei["redo"]],
    }
