"""Follow the pen path of a written Streifen and push it into the workbench.

The author asked to see the PATH in the admin — for the harvested words and
for his own hand's strips (2026-09-12). For a word the path is already stored
(``word_instances.strokes``); for a strip nothing about it existed, and the
server can never compute one: the API image does not ship ``tools``, and the
Tintenfolger lives here. So this is the local half — follow the ink, then push
the result through the admin-gated ``PUT /eigenhand/strips/…/pfade``.

    # look first, write nothing (the DEFAULT)
    uv run python -m tools.eigenhand.pfad --hand mn-suetterlin --strip S0001

    # the same run, stored in the shared DB
    ADMIN_TOKEN=… uv run python -m tools.eigenhand.pfad --hand mn-suetterlin --strip S0001 --apply

DRY RUN BY DEFAULT, like ``tools.wordbench.shift_registrations``: every write
lands in the SHARED Cloud SQL database, so ``--apply`` is a deliberate act and
an archive snapshot (``/dbsnapshot``) belongs in front of it.

A path the author drew BY HAND survives every run: this tool merges around
such a box and the server refuses a push that would displace one (409). Only
``--replace-authored`` gives one up, and that is the whole surface — there is
no button for it in the workbench. Since the archive chain exists, that flag
also REFUSES while the box is not archived (author decision B, 2026-09-20):
a drawing cannot be followed again, so handing it over while the only copy
sits in the shared database would make it none. One command fixes it —

    ADMIN_TOKEN=… uv run python -m tools.eigenhand.pull --hand mn-suetterlin --pfade

— and there is deliberately no second „I know what I am doing" flag beside it.

The LETTER BOUNDARIES the author corrected by hand survive every run too, and
without a flag: they are protected as a field of their own since PFAD_FORMAT 2,
so a re-follow of such a box carries them onto its own result instead of
dropping them. Where the fresh Bahn cannot hold them, the stored entry is kept
whole and the run says so.

A SECOND MODE, ``--spans``, assigns the boundaries themselves —

    ADMIN_TOKEN=… uv run python -m tools.eigenhand.pfad --hand mn-suetterlin --strip S0001 --spans

— and it follows nothing. A Bahn this tool laid brings its boundaries with it,
because the decode assigned them on the way; a Bahn the AUTHOR drew has no
decode behind it and would otherwise reach the editor with no seam to drag at
all. So the mode reads the stored list, labels the Bahnen it holds against the
same composed seed the follower decodes against (``tools.eigenhand.spans``) and
puts every path back exactly as it found it — a ``--spans`` run cannot move one
coordinate of anyone's Bahn, which is what makes it safe to point at hand-drawn
work. A box whose boundaries the author corrected is left alone WHOLE, and the
run names it; ``--replace-authored`` is refused beside this mode, because there
is nothing here to give up.

WHAT IT READS. Everything over the admin API, nothing off a local scan: the
strip listing (geometry, words, box rectangles), the Bogen layout (the printed
ruling), the strip PNG itself — served with the Fleckenmaske applied and, for
a colour strip, without its cyan rulings, so the follower reads the hand's ink
and not the printer's — and the ductus SEED, the style's authored chart
templates with their Laufform rows: the stroke order and direction the
Tintenpfad needs a prior for. It is a seed and not a claim about this hand,
and the workbench says so beside every drawn path.

THE SEED IS READ LIVE, and that is the one place a strip parts ways with a
bench specimen. A bench word is SCORED against the frozen dev-19 reference, so
it has to compose out of the frozen word fixtures — reference and templates
move together or the number means nothing — and that root deliberately carries
only the 34 glyph keys its 63 bench words need. A strip is the author's own
ink and is never scored against that ruler; refusing to follow his own
`immediately` because the word bench has no use for `y` was a bench rule
leaking into his hand (2026-09-13). So the templates come off the same admin
API everything else about the strip does, and the frozen root is left with the
style-level constants its manifest is the only written record of (`style_ratio`,
`width_resolver`, `constant_nib_units`). The bench paths — `tools.wordlab.cases`,
`tracebench`, `pairlab` — keep reading the frozen root, unchanged.

WHAT IT WRITES. One entry per word box: the strokes in the word's own units
(baseline 0, midband 1 — the frame ``word_instances.strokes`` uses), the
registration in the STRIP's pixels, the Verfahren, the configuration and the
day. The strip's own bytes are never touched; the path is data beside them
(``core.eigenhand.pfad``, proposal §7.5).

AND ONE ENTRY PER BOX IT COULD NOT FOLLOW. Since Streifen-Pfad format 2 a box
without a path says so in the same list (the Skip-Eintrag: ``status`` +
``grund``) instead of simply being absent, so the three situations this tool
can run into — the Bogen has no cut geometry, the word needs glyphs the plate
does not carry yet, the follower gave up — stop being one indistinguishable
„no entry". They are not the same work: one needs a Bogen re-measured, one is
a jump to the plate, and only the third is follower work at all.

WHAT IT MEASURES BESIDE THE PATH. Four sensors come out of the follower's own
diagnosis; two are measured HERE, against the strip's own ink mask — how far
the Bahn strays from the ink (``tools.tracebench.excursions``) and how well it
covers it (AIoU, ``tools.tracebench.metric``). Both are read afterwards by the
Tintentreue traffic light (``core.eigenhand.tintentreue``), which derives a
verdict and computes nothing: „Gemessen wird gespeichert, beurteilt wird
abgeleitet" (author decision D, 2026-09-20). Neither sensor touches the
followed geometry — they read the Bahn the follower delivered.

THE CONFIGURATION is the one the campaign settled on for the reversal corners
(messjournal §14, rounds of 10–11 September): ``tip_read`` · ``rail=tentfit``
· ``edt_upsample=4`` · ``ink_bridge_xh=1.0`` · ``hairpin_tip`` · ``ride_back``
· ``tip_grey_stop`` · ``self_jump``. It travels INTO the stored row, so a path
says out of itself what produced it.
"""

from __future__ import annotations

import os


# Before numpy is pulled in anywhere below: the chain solve is not
# bit-reproducible across thread environments, so a followed path would differ
# between two machines for no reason a reader could see (CLAUDE.md, the BLAS
# rule of 2026-08-16). Defaults only — an operator who exports otherwise is
# taken at their word.
for _var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import argparse  # noqa: E402
import json  # noqa: E402
import shlex  # noqa: E402
from collections.abc import Mapping  # noqa: E402
from datetime import date as date_cls  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402
from urllib.parse import quote  # noqa: E402

import numpy as np  # noqa: E402

from core.database.models import LAUFFORM_VARIANT  # noqa: E402
from core.eigenhand.ids import style_of_hand  # noqa: E402
from core.eigenhand.pfad import (  # noqa: E402
    FIELD_SPANS,
    MAX_DETAIL,
    SKIP_GAVE_UP,
    SKIP_NO_GEOMETRY,
    SKIP_UNAUTHORED,
    STATUS_OK,
    STATUS_SKIPPED,
    authored_spans,
    frame_for_box,
    is_authored,
    push_body,
)
from core.eigenhand.plan import load_plan, shaping_form_of  # noqa: E402
from core.eigenhand.tintentreue import KEY_AIOU, KEY_EXKURSION  # noqa: E402
from tools.eigenhand.apiclient import (  # noqa: E402
    StaleRead,
    admin_token,
    api_base,
    request_bytes,
    request_json,
    request_json_with_etag,
)
from tools.eigenhand.kartei import archived_pfade, load_kartei  # noqa: E402
from tools.eigenhand.spans import DEFAULT_METHOD, METHODS, assign, flat_spans  # noqa: E402
from tools.eigenhand.store import check_hand_id, hand_dir  # noqa: E402


# The settled arms, spelled out so the run is readable without opening the
# follower. Kept as a dict rather than a constructed dataclass so importing
# this module costs nothing: `tools.pairlab.tintenpfad` pulls in the whole
# solver stack, and the dry run should fail on a missing fixture root before
# that happens.
KONFIGURATION: dict[str, Any] = {
    "tip_read": True,
    "rail": "tentfit",
    "edt_upsample": 4,
    "ink_bridge_xh": 1.0,
    "hairpin_tip": True,
    "ride_back": True,
    "tip_grey_stop": True,
    "self_jump": True,
}

VERFAHREN = "tintenpfad"

# The follower's own diagnosis, projected rather than stored whole: `diag` holds
# dozens of keys, most of them decoder internals nobody reads twice, and a row
# of the shared database is not a dumping ground for them.
FOLLOWER_SENSORS = ("runs", "strands", "jumps", "hairpins", "paper_lifts", "ink_unvisited_share")
# The two this tool measures itself, named off the module that GRADES them so
# the two sides cannot drift: a sensor stored under another key reads as „never
# measured" and the box stays grey forever (`core.eigenhand.tintentreue`).
MEASURED_SENSORS = (KEY_EXKURSION, KEY_AIOU)
# The projection is a FIXED list, and that is why it is spelled here: a sensor
# missing from it is computed, printed, and then silently never reaches the
# database — indistinguishable afterwards from „measured 0". Pinned by
# `tests/test_eigenhand_pfad.py` against every key the traffic light reads.
STORED_SENSORS = (*FOLLOWER_SENSORS, *MEASURED_SENSORS)


def _strip_rows(base: str, token: str, hand: str, strip: str, fassung: str | None) -> list[dict]:
    """The stored Fassungen of one strip — refused loudly where there are none."""
    listing = request_json("GET", f"{base}/eigenhand/strips/{hand}?strip={quote(strip)}", token) or {}
    rows = [row for row in listing.get("strips", []) if fassung is None or row["fassung"] == fassung]
    if not rows:
        which = f"{strip}/{fassung}" if fassung else strip
        raise SystemExit(
            f"{hand} has no stored strip {which} — a path is followed on the ink, so push the image first: "
            f"uv run python -m tools.eigenhand.sync --hand {hand} --mit-streifen"
        )
    return rows


def _strip_plane(base: str, token: str, hand: str, row: dict) -> np.ndarray:
    """The strip as the plane a reading runs on — masked, and without rulings.

    The Fleckenmaske is applied by the server (the default), and a colour strip
    comes back as its blue plane with the cyan rulings lifted to paper: a
    ruling read as ink would put a straight line through every word.
    """
    from core.eigenhand.crop import working_plane

    url = f"{base}/eigenhand/strips/{hand}/{row['strip']}/{row['fassung']}?lineatur=ohne"
    return working_plane(request_bytes("GET", url, token))


def _style_constants(style: str) -> dict[str, Any]:
    """The style-level render constants — off the frozen word fixtures' manifest.

    `style_ratio`, `width_resolver` and the source-pooled `constant_nib_units`,
    plus the `source_id` they were pooled from. Only these: the TEMPLATES come
    live off that source (`LiveDuctus`), because a strip is not scored against
    the frozen reference and must not inherit the bench's glyph subset — see
    the module docstring.

    The roots are gitignored, so this is the one failure an operator will
    actually hit on a fresh machine; it names the command that fixes it rather
    than raising a traceback out of a missing file.
    """
    from tools.wordlab.cases import fixture_root_for

    rebuild = (
        "the style constants come from the frozen word fixtures, and those roots are gitignored. Rebuild:\n"
        "  uv sync --all-extras\n"
        "  uv run python -m tools.wordbench.fetch_fixtures --set all --verify"
    )
    # `fixture_root_for` raises KeyError where the style has no root at all and
    # hands back a directory that may still be empty — both are the same
    # situation for an operator, and both have to name the command.
    try:
        root = fixture_root_for(which="words", style=style)
    except KeyError as exc:
        raise SystemExit(f"no word fixtures for {style}: {exc} — {rebuild}") from exc
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"no frozen word fixtures for {style} under {root} — {rebuild}")
    manifest = json.loads(manifest_path.read_text())
    source_id = manifest.get("source_id")
    if not source_id:
        raise SystemExit(f"{manifest_path} names no source_id — the live templates have no source to come from")
    return {"manifest": manifest, "source_id": source_id}


class LiveDuctus:
    """The authored chart templates of one source, read over the admin API.

    The inventory comes first (one public summary read): which glyph keys the
    source has a chart row for, and which of them carry a Laufform row. That
    set is what a ligature decays AGAINST — the same test `api.routers.write`
    and `tools.wordlab.cases` make — and it is also the honest definition of
    „unauthored" for a strip, where the bench's frozen subset is not.

    The rows themselves are fetched per glyph on first use and cached for the
    run: a strip needs a handful of keys, and the whole source is ~60 rows of
    dense geometry nobody asked for. `template_row_from_payload` is borrowed
    from the fixture fetcher so a live row is shaped exactly like a frozen one
    and the composer cannot tell which it was handed.
    """

    def __init__(self, base: str, token: str, source_id: str, get=request_json) -> None:
        self._base = base
        self._token = token
        self._source = quote(source_id, safe="")
        self._get = get  # the seam the tests call through; every caller uses the default
        self._chart: dict[str, dict] = {}
        self._laufform: dict[str, dict] = {}
        # A list, not an object — `request_json` hands back whatever the route
        # answers with, and the summary route answers with the row list.
        summaries: list[dict] = self._get("GET", f"{base}/sources/{self._source}/templates", token) or []
        self.have = {row["glyph_key"] for row in summaries if row.get("variant", 0) == 0}
        self._has_laufform = {row["glyph_key"] for row in summaries if row.get("variant") == LAUFFORM_VARIANT}

    def _fetch(self, key: str, variant: int) -> dict | None:
        """One stored template row, or None where the API will not serve THAT variant.

        An API predating the `variant` parameter ignores it and answers with the
        chart row instead — the guard `tools.wordbench.fetch_fixtures` carries.
        Seeding a Laufform slot with a chart row would be a silent render flip,
        so the wrong row is worse than none.
        """
        url = f"{self._base}/sources/{self._source}/templates/{quote(key, safe='')}?variant={variant}"
        payload = self._get("GET", url, self._token) or {}
        return payload if payload.get("variant") == variant else None

    def rows_for(self, keys: list[str]) -> tuple[dict[str, dict], dict[str, dict]]:
        """The chart rows and the Laufform rows for `keys`, fetching what is new.

        Keys the source has no chart row for are simply absent from the result
        — that is what the caller reports as unauthored.
        """
        from tools.wordbench.fetch_fixtures import template_row_from_payload

        for key in keys:
            if key in self._chart or key not in self.have:
                continue
            chart = self._fetch(key, 0)
            if chart is None:
                print(f"  no chart row for {key!r} this API will serve — its words read as unauthored", flush=True)
                continue
            self._chart[key] = template_row_from_payload(chart)
            if key in self._has_laufform:
                laufform = self._fetch(key, LAUFFORM_VARIANT)
                if laufform is None:
                    print(f"  no stored Laufform row for {key!r} on this API — seeding with the chart form", flush=True)
                    continue
                self._laufform[key] = template_row_from_payload(laufform)
        return (
            {key: self._chart[key] for key in keys if key in self._chart},
            {key: self._laufform[key] for key in keys if key in self._laufform},
        )


def _case_for_box(prior: dict, plane: np.ndarray, frame: dict, word: str, form: str, case_id: str):
    """One word box of a strip as a `WordCase` — the seam to the follower.

    The specimen half is cut out here rather than loaded from a fixture: crop,
    binarised mask, skeleton and half-width map, the same four the bench
    freezes (`tools.wordbench.export_fixtures`) and through the same entry
    points, so a strip is read exactly as a plate crop is.

    The lineature is the Bogen's PRINTED ruling. That is a seed for the
    registration the fit then refines, never a measurement of where the hand
    actually wrote — see `core.eigenhand.pfad`.
    """
    from core.extract import binarize_adaptive, skeleton_and_width
    from core.shaping import decompose_ligature_slot, glyph_keys_of, shape_text
    from core.word_metric import despeckle
    from tools.wordlab.cases import WordCase

    x0, y0, x1, y1 = frame["rect_px"]
    crop = np.ascontiguousarray(plane[y0:y1, x0:x1], dtype=np.float64)
    mask = despeckle(binarize_adaptive(crop))
    skel, width_map = skeleton_and_width(mask)
    seed: LiveDuctus = prior["seed"]
    slots = shape_text(form)
    # Ligature decay, exactly as `api.routers.write` and `tools.wordlab.cases`
    # do it: a closed-set cluster with no canonical of its own splits into its
    # letters and composes with a generated Übergang. Without it every word
    # holding a `ch` was refused as unauthored — the author's own
    # `Kurrentschrift` among them — although `ch` is authored nowhere by
    # design (the combination is a library entry only where it really differs,
    # as in `St`). `decompose_ligature_slot` keeps ß atomic.
    if any(sl.ligature and sl.key and sl.key not in seed.have for sl in slots):
        slots = [
            out
            for sl in slots
            for out in (
                (decompose_ligature_slot(sl) or [sl]) if sl.ligature and sl.key and sl.key not in seed.have else [sl]
            )
        ]
    keys = glyph_keys_of(slots)
    templates, laufform = seed.rows_for(keys)
    missing = [key for key in keys if key not in templates]
    manifest = prior["manifest"]
    return (
        WordCase(
            id=case_id,
            word=word,
            kind="word",
            slots=slots,
            templates=templates,
            laufform=laufform,
            style_ratio=manifest.get("style_ratio") or [1, 1, 1],
            width_resolver=manifest.get("width_resolver") or "pressure",
            nib_units=manifest.get("constant_nib_units"),
            origin=f"eigenhand:live:{prior['source_id']}",
            scorable=not missing,
            rect=[x0, y0, x1, y1],
            baseline_y=int(round(frame["baseline_row"])),
            midband_y=int(round(frame["waist_row"])),
            crop=crop,
            skel=skel,
            width_map=width_map,
            mask=mask,
        ),
        missing,
    )


def _crop_px(points: Any, reg: Mapping[str, Any], xh_px: float) -> np.ndarray:
    """Word units → the CROP's own pixels — the inverse of the follower's mapping.

    `tools.pairlab.trace._px_to_word_units` read the other way, and deliberately
    spelled out rather than imported from there: this is the one arithmetic both
    sensors below stand on, and a private function of the follower is not a
    contract. The CROP's frame, not the strip's — `_entry` adds the crop origin
    back for storage, the mask these are measured against is the crop's own.
    """
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    tx, ty, baseline_row = float(reg["tx"]), float(reg.get("ty", 0.0)), float(reg["baseline_row"])
    return np.column_stack([pts[:, 0] * xh_px + tx, baseline_row + ty - pts[:, 1] * xh_px])


def _reading(value: float | None, digits: int = 3) -> str:
    """One sensor as the run prints it — „—" where it was not measured.

    Never a 0 in that place: „the Bahn left no ink unvisited" is the best
    reading this row can carry and „nothing computed it" is no reading at all,
    and the two must not look alike at the terminal either.
    """
    return "—" if value is None else f"{float(value):.{digits}f}"


def _paper_sensors(mask: np.ndarray, info: dict) -> dict[str, float | None]:
    """The two sensors measured HERE: paper excursion and AIoU, against this strip's ink.

    Both grade the Bahn against the word box's OWN binarised mask — the one
    `_case_for_box` already cut for the follower — because a written strip has
    no reference trace by doctrine (`docs/proposals/eigenhand-erfassung.md` §12,
    Prüfstein 2). `dtw_xh` and Chamfer are reference-bound and deliberately not
    here.

    Neither is a new metric. The excursion kernel is the bench's standing K-D
    sensor with its fixture wiring left behind (`tools.tracebench.excursions`),
    and the AIoU is the ruler's own, which takes an ink mask and no reference at
    all. Measured on the DELIVERED strokes — the capped ones that are actually
    stored — so the number describes the Bahn a reader will see rather than one
    that existed only inside the follower.

    The two are imported inside the function like the follower itself: a dry run
    should fail on a missing fixture root before the heavy stack is pulled in.
    """
    from tools.tracebench.excursions import excursion_readings, ink_distance_px
    from tools.tracebench.metric import aiou

    strokes, xh_px = info["strokes"], float(info["xh_px"])
    reg = info["registration_px"]
    if not strokes or not any(len(stroke) for stroke in strokes):
        return dict.fromkeys(MEASURED_SENSORS)
    ink = np.asarray(mask, dtype=bool)
    reading = excursion_readings(strokes, lambda points: _crop_px(points, reg, xh_px), ink_distance_px(ink), xh_px)
    value = aiou([_crop_px(stroke, reg, xh_px) for stroke in strokes], ink)
    return {
        # Rounded like the follower's own excursion reading, and for the same
        # reason: three decimals of an x-height is a thousandth of a letter,
        # and the digits past it are the EDT's grid, not the hand's.
        KEY_EXKURSION: None if reading is None else round(reading["max"], 3),
        KEY_AIOU: round(float(value.value), 4),
    }


def _entry(info: dict, frame: dict, flecken_n: int | None, today: str, sensors: Mapping[str, float | None]) -> dict:
    """One followed word as the row the API stores.

    The follower registers against the CROP it was handed; the stored frame is
    the STRIP's, so the crop's own origin is added back. One stored frame
    serves both views — the whole strip and any word cut out of it — and the
    crop's padding never has to be remembered along with the path.

    `meta.letter_spans` is NOT written. Under format 2 a box's letter boundaries
    are a checked field of the entry, and the free-meta copy is refused outright
    (`core.eigenhand.pfad.check_paths`) — one box, one set of boundaries. The
    follower's own assignment goes into the CHECKED field instead: it comes out
    of the decode for free (every emitted sample inherits the slot of the seed
    sample that put it there), and without it a followed Bahn reaches the editor
    with no seam to drag and the author would have to place every boundary by
    hand on a box the machine had already labelled.

    It is dropped where the delivered strokes can no longer carry it
    (`tools.eigenhand.spans.flat_spans`): the follower labels the path it
    decoded and stores the CAPPED one, so a Bahn past `cap_word_strokes`' bounds
    has boundaries pointing at ink that was re-cut underneath them. An `auto`
    boundary is a derivation the next run makes again — that is what makes
    dropping it acceptable, and what the author corrected BY HAND unthinkable
    (carried through untouched by `_carry_spans`).
    """
    reg = info["registration_px"]
    x0, y0 = frame["rect_px"][0], frame["rect_px"][1]
    diagnosis = info.get("meta", {}).get("tintenpfad", {})
    readings = {**{key: diagnosis.get(key) for key in FOLLOWER_SENSORS}, **sensors}
    spans = flat_spans(info.get("meta", {}).get(FIELD_SPANS) or [], info["strokes"])
    return {
        "box_index": frame["index"],
        "word": frame["word"],
        "status": STATUS_OK,
        "strokes": info["strokes"],
        FIELD_SPANS: spans,
        "registration_px": {
            "tx": round(float(reg["tx"]) + x0, 2),
            "ty": round(float(reg.get("ty", 0.0)), 2),
            "baseline_row": round(float(reg["baseline_row"]) + y0, 2),
        },
        "xh_px": float(info["xh_px"]),
        "verfahren": VERFAHREN,
        "konfiguration": dict(KONFIGURATION),
        "meta": {"tintenpfad": {key: readings.get(key) for key in STORED_SENSORS}},
        "erzeugt_am": today,
        "flecken_n": flecken_n,
    }


def _skip(index: int, word: str, grund: str, detail: str, flecken_n: int | None, today: str, *, ran: bool) -> dict:
    """One box this run could not follow, as the entry that says why.

    A Skip-Eintrag, not an absence: the same list, one state per box (author
    decision C, 2026-09-20). It carries no registration and no x-height even
    where a nominal frame existed — those are the FOLLOWER's output, and the
    printed ruling put in their place would be a measurement of where the hand
    was asked to write (`core.eigenhand.pfad`, „NOMINAL, NOT MEASURED").

    `ran` says whether the follower actually got as far as reading ink. Only
    then does the configuration travel into the row: on an unauthored word or a
    Bogen without geometry the arms had no bearing on the outcome, and storing
    them would suggest they did.
    """
    return {
        "box_index": index,
        "word": word,
        "status": STATUS_SKIPPED,
        "grund": grund,
        # Cut rather than refused: the reason is what the triage runs on, the
        # detail is only what a human reads afterwards, and a follower message
        # longer than the bound must not cost the whole run a 422.
        "detail": detail[:MAX_DETAIL] or None,
        "strokes": [],
        "verfahren": VERFAHREN,
        "konfiguration": dict(KONFIGURATION) if ran else {},
        "meta": {},
        "erzeugt_am": today,
        "flecken_n": flecken_n,
    }


def _row_context(base: str, token: str, hand: str, row: dict) -> tuple[dict, np.ndarray]:
    """The printed row and the strip plane — what any reading of one Fassung stands on.

    Held in one place because the two passes over a Fassung need exactly the
    same two things: the follow, and the boundary assignment over the Bahnen it
    already holds. A second copy would be a second chance to read the layout row
    off a different index.
    """
    layout = request_json("GET", f"{base}/eigenhand/sheets/{hand}/{row['sheet']}/layout", token) or {}
    return (layout.get("rows") or [])[row["row_index"]], _strip_plane(base, token, hand, row)


def follow_row(base: str, token: str, hand: str, row: dict, prior: dict, boxes: list[int] | None) -> list[dict]:
    """Follow every asked-for word of one Fassung. One bad word is not a bad row.

    A box that could not be followed comes back as a Skip-Eintrag naming its
    reason, so the Nachfahr-Liste can route the work: `unauthored` is a jump to
    the plate, `no_geometry` needs the Bogen re-measured, `gave_up` is the only
    one that is follower work at all.

    `not_selected` is deliberately NOT written here. `--box` is a narrowing of
    THIS run, not a finding about the other boxes, and the write is a full
    replacement: declaring them skipped would make a one-word re-follow overwrite
    the rest of the row with „not selected". A box nothing has ever followed
    carries no entry, which is the same statement without the damage.
    """
    # FIRST, before a single byte is fetched: a `--box` that names nothing
    # would follow no word, and the write is a FULL replacement — so with
    # `--apply` a typo would erase this Fassung's stored paths and report
    # success (Copilot review, PR #598).
    known = {box["index"] for box in row.get("boxes", [])}
    unknown = sorted(set(boxes or []) - known)
    if unknown:
        raise SystemExit(
            f"{row['strip']}/{row['fassung']} has boxes {sorted(known)} — no box "
            f"{', '.join(str(i) for i in unknown)}; refusing to replace its paths with nothing"
        )

    # Aliased: `STATUS_OK` at module level is the stored ENTRY's status, this
    # one is the FOLLOWER's verdict on a word, and the two answer different
    # questions on adjacent lines.
    from tools.pairlab.follow import STATUS_OK as FOLLOWER_OK
    from tools.pairlab.tintenpfad import TintenpfadWeights, follow_case

    plan = load_plan()
    layout_row, plane = _row_context(base, token, hand, row)
    weights = TintenpfadWeights(**KONFIGURATION)
    flecken_n = len(row["flecken"]) if row.get("flecken") is not None else None
    today = date_cls.today().isoformat()

    entries: list[dict] = []
    for box in row.get("boxes", []):
        index = box["index"]
        if boxes is not None and index not in boxes:
            continue
        case_id = f"{row['strip']}/{row['fassung']}#{index}"
        try:
            frame = frame_for_box(layout_row, row["crop_origin_mm"], row["width_px"], row["height_px"], index)
        except ValueError as exc:
            # A Bogen printed before the cut or ruling geometry existed has no
            # frame to seed with. One such row must not take the whole run down.
            print(f"  {case_id:<18} skipped   {exc}", flush=True)
            printed = layout_row.get("boxes") or []
            if not 0 <= index < len(printed):
                # The OTHER way that call refuses: the strip listing (built from
                # the frozen plan) names a box the layout row does not have. An
                # entry for it would be refused by `check_paths` — and take the
                # whole Fassung's push down with it, where the box alone is what
                # is in doubt. So that disagreement stays a gap in the list
                # (found in review, this PR).
                continue
            # The word comes from the LAYOUT, like `_entry`'s: `check_paths`
            # holds the entry against the printed box, so an entry built from
            # the other source could be refused for disagreeing with it.
            entries.append(
                _skip(index, printed[index].get("word", ""), SKIP_NO_GEOMETRY, str(exc), flecken_n, today, ran=False)
            )
            continue
        case, missing = _case_for_box(prior, plane, frame, box["word"], shaping_form_of(plan, box["word"]), case_id)
        if missing:
            print(f"  {case_id:<18} skipped   unauthored: {' '.join(missing)}", flush=True)
            entries.append(_skip(index, frame["word"], SKIP_UNAUTHORED, " ".join(missing), flecken_n, today, ran=False))
            continue
        info = follow_case(case, weights)
        if info["status"] != FOLLOWER_OK:
            print(f"  {case_id:<18} {info['status']:<9} {info['detail']}", flush=True)
            detail = f"{info['status']}: {info['detail']}" if info.get("detail") else str(info["status"])
            entries.append(_skip(index, frame["word"], SKIP_GAVE_UP, detail, flecken_n, today, ran=True))
            continue
        entry = _entry(info, frame, flecken_n, today, _paper_sensors(case.mask, info))
        readings = entry["meta"]["tintenpfad"]
        print(
            f"  {case_id:<18} ok        {box['word']:<14} {len(entry['strokes']):2d} Züge · "
            f"{_reading(readings['paper_lifts'], 0)} Absetzer · "
            f"unvisited {_reading(readings['ink_unvisited_share'], 2)} · "
            f"Exkursion {_reading(readings[KEY_EXKURSION])} xh · AIoU {_reading(readings[KEY_AIOU])}",
            flush=True,
        )
        entries.append(entry)
    return entries


def _wants_spans(entry: Mapping[str, Any]) -> bool:
    """Whether the assigner has anything to do on this stored box.

    Three „no"s, and only the first is about the assigner at all. A box the
    author has corrected is left whole — not „the corrected boundaries are
    kept", which the field guard would do anyway, but untouched: a boundary is
    only meaningful next to the ones beside it, so re-deriving its neighbours
    under a correction would move the seams the author placed. A box that
    already carries boundaries needs none (an `auto` set is a derivation, and
    re-deriving it would only churn the row), and a box with no Bahn has
    nothing to label.
    """
    return (
        entry.get("status", STATUS_OK) == STATUS_OK
        and bool(entry.get("strokes"))
        and not entry.get(FIELD_SPANS)
        and not authored_spans(entry)
    )


def assign_row_spans(
    base: str,
    token: str,
    hand: str,
    row: dict,
    prior: dict,
    stored: list[dict],
    boxes: list[int] | None,
    *,
    method: str = DEFAULT_METHOD,
) -> list[dict]:
    """Letter boundaries over the Bahnen one Fassung already holds — and never a Bahn.

    This is the Span-Zuordner's own pass, and it is deliberately NOT part of a
    follow. A followed Bahn brings its boundaries with it, because the decode
    assigned them on the way; a Bahn the AUTHOR drew has no decode behind it and
    would otherwise reach the editor with no seam to drag at all. So the pass
    reads what is stored, labels it, and puts the Bahn back exactly as it found
    it — a `--spans` run cannot change a single coordinate of anyone's path,
    which is the property that makes it safe to point at hand-drawn work.

    A box whose boundaries the author corrected is skipped whole and named. The
    server would refuse a push that displaced one anyway (`displaced_authored`),
    but the tool does not get as far as trying: see `_wants_spans`.
    """
    from tools.pairlab.tintenpfad import TintenpfadWeights

    protected = sorted(entry["box_index"] for entry in stored if authored_spans(entry))
    if protected:
        print(
            f"  leaving box {', '.join(str(index) for index in protected)} alone — the author corrected the letter "
            "boundaries there, and a boundary is only meaningful next to the ones beside it",
            flush=True,
        )
    wanted = [entry for entry in stored if _wants_spans(entry) and (boxes is None or entry["box_index"] in boxes)]
    if not wanted:
        print("  no box of this Fassung is waiting for letter boundaries", flush=True)
        return list(stored)

    plan = load_plan()
    layout_row, plane = _row_context(base, token, hand, row)
    weights = TintenpfadWeights(**KONFIGURATION)
    by_box = {entry["box_index"]: entry for entry in wanted}
    out: list[dict] = []
    for entry in stored:
        index = entry["box_index"]
        if index not in by_box:
            out.append(entry)
            continue
        case_id = f"{row['strip']}/{row['fassung']}#{index}"
        try:
            frame = frame_for_box(layout_row, row["crop_origin_mm"], row["width_px"], row["height_px"], index)
        except ValueError as exc:
            print(f"  {case_id:<18} no frame    {exc}", flush=True)
            out.append(entry)
            continue
        case, missing = _case_for_box(prior, plane, frame, frame["word"], shaping_form_of(plan, frame["word"]), case_id)
        if missing:
            print(f"  {case_id:<18} unauthored  {' '.join(missing)} — no seed to assign against", flush=True)
            out.append(entry)
            continue
        # The stored frame is the STRIP's; the seed is built in the crop the
        # composition was registered on. The inverse of what `_entry` adds.
        stored_reg = entry["registration_px"]
        reg = {
            "tx": float(stored_reg["tx"]) - frame["rect_px"][0],
            "ty": float(stored_reg.get("ty", 0.0)),
            "baseline_row": float(stored_reg["baseline_row"]) - frame["rect_px"][1],
        }
        spans, diag = assign(case, entry["strokes"], reg, float(entry["xh_px"]), weights, method=method)
        if spans is None:
            print(f"  {case_id:<18} none        {diag['reason']}", flush=True)
            out.append(entry)
            continue
        print(
            f"  {case_id:<18} ok          {frame['word']:<14} {diag['spans']:2d} Grenzen · "
            f"Saat-Abstand {_reading(diag['seed_distance_median_xh'])} xh med · "
            f"{_reading(diag['seed_distance_p90_xh'])} xh p90 · {diag['method']}",
            flush=True,
        )
        out.append({**entry, FIELD_SPANS: spans})
    return out


def _local_path(hand: str, strip: str, fassung: str) -> Path:
    """Where a dry run files its result — under the gitignored own-hand root."""
    return hand_dir(hand) / "pfade" / f"{strip}-{fassung}.json"


def _spans_fit(spans: list[dict], strokes: list) -> bool:
    """Whether these letter boundaries still index samples this Bahn has."""
    return all(
        isinstance(span.get("stroke"), int)
        and 0 <= span["stroke"] < len(strokes)
        and isinstance(span.get("last"), int)
        and span["last"] < len(strokes[span["stroke"]])
        for span in spans
    )


def _carry_spans(fresh: dict, stored: dict | None) -> dict | None:
    """This run's own result for one box, with the author's boundaries kept on it.

    The second half of the field rule (`core.eigenhand.pfad.displaced_authored`):
    a box whose letter boundaries the author corrected by hand may be followed
    again — but the boundaries are not the follower's to throw away, and the
    server refuses a push that drops them. So they ride along, and a hand-
    corrected STROKE keeps its boundaries whole: this run's own spans on that
    stroke step aside rather than being interleaved with them, because a letter
    boundary is only meaningful next to the ones beside it.

    „Whole" means the stroke's whole STORED set, not the corrected boundaries
    alone. A stroke usually carries one hand-corrected boundary among several
    the follower assigned; keeping only the corrected one would leave the
    letters beside it unlabelled and call that a rescue (found in review,
    PR #639). So every stored boundary of a stroke an authored one sits on
    travels together, and this run's own boundaries there step aside.

    Where the fresh Bahn cannot hold them at all — fewer strokes, or a stroke
    too short for the samples they name — `None` says so, and the caller keeps
    the STORED entry instead. Carrying them onto a Bahn they no longer fit would
    be refused as a desynchronised span (`check_paths`), and re-indexing them is
    the Span-Zuordner's job, not a silent repair inside a merge.
    """
    corrected = authored_spans(stored or {})
    if not corrected:
        return fresh
    owned = {span["stroke"] for span in corrected}
    held = [span for span in ((stored or {}).get(FIELD_SPANS) or []) if span.get("stroke") in owned]
    strokes = fresh.get("strokes") or []
    if not _spans_fit(held, strokes):
        return None
    mine = [span for span in (fresh.get(FIELD_SPANS) or []) if span.get("stroke") not in owned]
    return {**fresh, FIELD_SPANS: sorted(mine + held, key=lambda span: (span.get("stroke", 0), span.get("first", 0)))}


def _merged(
    base: str,
    token: str,
    url: str,
    entries: list[dict],
    *,
    hand: str = "",
    where: str = "",
    archived: dict[int, dict] | None = None,
    replace_authored: bool = False,
    apply: bool = True,
    _get=request_json_with_etag,
) -> tuple[list[dict], bool, str | None]:
    """The freshly followed entries over the paths the Fassung holds, whether one was given up, and the read's token.

    The write is a FULL replacement — right for the boxes a run actually
    followed, wrong for every other one (Copilot review, PR #598). `--box`
    narrows the follow on purpose, but a WHOLE-ROW run drops boxes just as
    quietly: `follow_row` skips a box whose Bogen has no frame, whose glyphs
    are unauthored or whose follower gives up, and sending only what came back
    would delete those boxes' stored paths while reporting success. So every
    run reads the stored list first and replaces only what it followed — a run
    can add to a Fassung and improve it, never silently empty it.

    The same read answers the other direction: a box whose stored path the
    AUTHOR drew by hand keeps it, and this run's own result for that box is
    dropped. The server refuses such a push outright (409), so merging around
    the box here is what keeps a whole-row re-follow from failing over one
    hand-drawn word — and `--replace-authored` is the one way to hand it over
    anyway.

    That flag now REFUSES while the drawing is not archived (author decision B,
    2026-09-20). `archived` is what `tools.eigenhand.pull --pfade` has brought
    into this machine's Kartei, box by box; a drawing that exists only in the
    shared database has no second copy anywhere, and the terminal is not
    allowed to make it none. One command fixes it, and the refusal names it.

    The second half of the answer is whether this row actually handed a drawing
    over. Only then does the push need `?replace_authored=true`: the flag is
    set once for a whole strip, and putting the override on rows that carry no
    hand-drawn path at all would switch the server's 409 off for boxes the
    local guard never even looked at (found in review, PR #634).

    The LETTER BOUNDARIES the author corrected are kept separately and always
    (`_carry_spans`): they are the other field the server protects, they are not
    covered by `--replace-authored` — that flag hands over a Bahn, not the
    boundaries on someone else's — and with the override set the server's own
    refusal is switched off, so this merge is the only thing left between a
    re-follow and a silent loss.

    A SKIP never displaces a stored path, and that guard lives here for the same
    reason as all the others: the write is a full replacement. „Unauthored"
    depends on which glyphs the plate carries TODAY and „gave up" on the arms
    this run used, so a box that was followed cleanly last week can produce a
    skip this week — and storing it would throw a good Bahn away to record that
    this run did not reproduce it. The skip is dropped and the run says so; a
    box that holds nothing keeps the skip, which is where it is worth something.

    The third return value is the TOKEN of this very read (`ETag`). The push
    is guarded by it: between this read and the write the author can have drawn
    a box in the workbench, and a merge assembled from the older list would put
    that drawing back to what it was. The server refuses a push whose token no
    longer matches (412), so the merge is either made on the current list or
    not stored at all — which is why the token has to travel from the read that
    produced the merge rather than from a second one.

    `_get` is the seam the test calls through; every caller uses the default.
    """
    answer, etag = _get("GET", url, token)
    stored = (answer or {}).get("pfade") or []
    by_stored_box = {entry.get("box_index"): entry for entry in stored}
    over_a_path = sorted(
        entry["box_index"]
        for entry in entries
        if entry.get("status") == STATUS_SKIPPED and (by_stored_box.get(entry["box_index"]) or {}).get("strokes")
    )
    if over_a_path:
        print(
            f"  keeping the stored path at box {', '.join(str(index) for index in over_a_path)} — this run could "
            "not follow it, and a skip is a finding about the run, not a reason to give up a path",
            flush=True,
        )
        entries = [entry for entry in entries if entry["box_index"] not in set(over_a_path)]
    authored_boxes = {entry.get("box_index") for entry in stored if is_authored(entry)}
    hit = sorted(entry["box_index"] for entry in entries if entry["box_index"] in authored_boxes)
    if hit and replace_authored:
        by_box = {entry.get("box_index"): entry for entry in stored}
        # Not „is there a record" but „is THIS drawing the one on disk": a copy
        # pulled before the author corrected his own trace would archive a
        # different Bahn than the one being given up here.
        unarchived = [index for index in hit if (archived or {}).get(index) != by_box.get(index)]
        if unarchived:
            raise SystemExit(
                f"  --replace-authored: box {', '.join(str(index) for index in unarchived)} of {where or url} "
                "carries a hand-drawn Bahn this machine has not archived (or archived in an older shape). "
                "Nothing can follow a drawing again, so it would exist nowhere afterwards. Pull it first:\n"
                f"    ADMIN_TOKEN=… uv run python -m tools.eigenhand.pull --hand {hand or '<hand>'} --pfade\n"
                "  (`snapshot` is what carries the Kartei into the private archive after that.)"
            )
        # The DESTRUCTIVE path has to be the loud one. Nothing else in the run
        # names what is being given up, and a line the operator can read back
        # is all that stands between the flag and a quiet loss of the author's
        # own hand — the archived copy is a backup, not an undo.
        #
        # And it names the follow-up, the way the refusal above does: what the
        # check proves is that the drawing is in this machine's `kartei.json`,
        # on one disk, which is not yet archived (found in review, PR #634).
        #
        # A DRY run says „would", because nothing is given up until the PUT:
        # the line is assembled here, before the two paths part ways, and the
        # database copy is still there afterwards (Copilot review, PR #635).
        boxes = ", ".join(str(index) for index in hit)
        print(
            (
                f"  --replace-authored: handing the hand-drawn path at box {boxes} over to this run's own "
                "result. The only copy left is this machine's kartei.json — file it:\n"
                f"    uv run python -m tools.eigenhand.snapshot --hand {hand or '<hand>'}"
            )
            if apply
            else (
                f"  --replace-authored: an --apply run WOULD hand the hand-drawn path at box {boxes} over to "
                "this run's own result. This is a dry run — the drawing stays in the database."
            ),
            flush=True,
        )
    elif hit:
        print(
            f"  keeping the hand-drawn path at box {', '.join(str(index) for index in hit)} — "
            "this run's own result there is dropped (--replace-authored hands it over)",
            flush=True,
        )
        entries = [entry for entry in entries if entry["box_index"] not in authored_boxes]
    # A box whose Bahn is being handed over hands its boundaries over with it:
    # they were drawn on THAT Bahn and say nothing about this run's own.
    handed = set(hit) if replace_authored else set()
    carried: list[dict] = []
    for entry in entries:
        if entry["box_index"] in handed:
            carried.append(entry)
            continue
        with_spans = _carry_spans(entry, by_stored_box.get(entry["box_index"]))
        if with_spans is None:
            print(
                f"  keeping the hand-corrected letter boundaries at box {entry['box_index']} — this run's Bahn "
                "there cannot carry them (its strokes are shorter or fewer), so its own result is dropped",
                flush=True,
            )
            continue
        if with_spans is not entry:
            print(f"  carrying the hand-corrected letter boundaries at box {entry['box_index']} over", flush=True)
        carried.append(with_spans)
    entries = carried
    followed = {entry["box_index"] for entry in entries}
    kept = [entry for entry in stored if entry.get("box_index") not in followed]
    if kept:
        print(f"  keeping {len(kept)} stored path(s) for the boxes this run did not follow", flush=True)
    return sorted(entries + kept, key=lambda item: item["box_index"]), bool(hit and replace_authored), etag


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True, help="hand id, e.g. mn-suetterlin")
    ap.add_argument("--strip", required=True, help="strip id, e.g. S0001")
    ap.add_argument("--fassung", default=None, help="one Fassung (default: every stored one of this strip)")
    ap.add_argument("--box", type=int, action="append", default=None, help="only this word box (repeatable)")
    ap.add_argument("--api", default=None, help="API base URL (default: $EIGENHAND_API or production)")
    ap.add_argument("--token", default=None, help="admin token (default: $ADMIN_TOKEN)")
    ap.add_argument("--out", type=Path, default=None, help="where a dry run files its JSON")
    ap.add_argument(
        "--apply",
        action="store_true",
        help="store the followed paths in the SHARED database (takes a dbsnapshot first — see /dbsnapshot)",
    )
    ap.add_argument(
        "--replace-authored",
        action="store_true",
        help=(
            "also replace the paths the author drew BY HAND — the only way to, deliberately not a button, "
            "and refused while the box is not archived (`pull --pfade`)"
        ),
    )
    ap.add_argument(
        "--spans",
        action="store_true",
        help=(
            "assign the letter boundaries of the Bahnen this strip already holds instead of following — "
            "the mode for a Bahn the author DREW, and it never touches a path"
        ),
    )
    ap.add_argument(
        "--spans-method",
        default=DEFAULT_METHOD,
        choices=list(METHODS),
        help="the matching rule of --spans; the default is the one the §14 round of 2026-09-20 measured",
    )
    args = ap.parse_args(argv)

    if args.spans and args.replace_authored:
        # Not a compatibility detail: `--spans` is the mode that cannot lose a
        # path, and a flag whose entire purpose is to give one up must not be
        # able to ride along on it.
        raise SystemExit(
            "--spans never touches a path, so --replace-authored has nothing to give up — drop one of them"
        )

    hand = check_hand_id(args.hand)
    style = style_of_hand(hand) or ""
    base = api_base(args.api)
    token = admin_token(args.token)
    constants = _style_constants(style)
    seed = LiveDuctus(base, token, constants["source_id"])
    prior = {**constants, "seed": seed}
    # The seed is read LIVE, so it can move between two runs of the same strip
    # in a way the stored row does not record. Say which inventory this run
    # saw, so a log is enough to tell two runs apart.
    print(f"seed: {len(seed.have)} authored glyph keys, live off {constants['source_id']}", flush=True)

    # Read once, and only where it can matter: the Kartei is what the archive
    # chain files, so it is also what `--replace-authored` is held against.
    kartei = load_kartei(hand) if args.replace_authored else {}

    # Held rather than walked straight, because a run without `--fassung`
    # covers every stored Fassung of the strip: when one of them stops the run,
    # the ones behind it were never attempted, and an operator who is told
    # nothing about them would read the abort as „the strip is done except this
    # one" (found in review, this PR).
    rows = _strip_rows(base, token, hand, args.strip, args.fassung)

    written = 0
    for position, row in enumerate(rows):
        print(f"{row['strip']}/{row['fassung']} ({row['sheet']} row {row['row_index']}):", flush=True)
        url = f"{base}/eigenhand/strips/{hand}/{row['strip']}/{row['fassung']}/pfade"
        if args.spans:
            # The read is the whole body here. A `--spans` run replaces the
            # stored list with the same list plus boundaries, so there is
            # nothing to merge around and nothing that can go missing — but the
            # push is still a full replacement, so it is still made on the token
            # of the read it was assembled from.
            answer, etag = request_json_with_etag("GET", url, token)
            stored = (answer or {}).get("pfade") or []
            if not stored:
                print("  no stored path in this Fassung — a boundary needs a Bahn to sit on", flush=True)
            body, handed_over = (
                assign_row_spans(base, token, hand, row, prior, stored, args.box, method=args.spans_method),
                False,
            )
        else:
            entries = follow_row(base, token, hand, row, prior, args.box)
            # The body is assembled BEFORE the two paths part ways: the dry run
            # is the surface an operator reviews before deciding on `--apply`,
            # so the file it writes has to be the list that would be stored,
            # merge and all. Filing only the followed boxes made a run look like
            # a whole-row replacement — the exact thing `_merged` exists to
            # prevent (review of PR #598).
            body, handed_over, etag = _merged(
                base,
                token,
                url,
                entries,
                hand=hand,
                where=f"{row['strip']}/{row['fassung']}",
                archived=archived_pfade(kartei, row["strip"], row["fassung"]) if args.replace_authored else {},
                replace_authored=args.replace_authored,
                apply=args.apply,
            )
        # The declared format follows the BODY, not this image's own constant:
        # the merge carries stored entries and hand-corrected boundaries this
        # run did not produce, and declaring format 1 over them would be refused
        # by the content rule (`core.eigenhand.pfad.push_body`).
        body, wire_format, without_spans = push_body(body)
        if without_spans:
            # Named, never silent. `_entry` writes the CHECKED field, so every
            # boundary left to strip here is one an older run put in the free
            # `meta` and the merge carried along. The box keeps its Bahn; the
            # boundaries come back on a `--spans` run, which is exactly what a
            # box carrying none is waiting for.
            print(
                f"  Streifen-Pfad format {wire_format}: dropping the free-meta letter boundaries a stored entry "
                f"carries at box {', '.join(str(index) for index in without_spans)} — under this format they "
                "belong in the entry's own checked `letter_spans`, and a `--spans` run assigns them there "
                "(hand-corrected boundaries are never touched)",
                flush=True,
            )
        with_spans = sum(1 for entry in body if entry.get(FIELD_SPANS))
        if not args.apply:
            out = args.out or _local_path(hand, row["strip"], row["fassung"])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"format": wire_format, "pfade": body}, ensure_ascii=False, indent=1) + "\n")
            # The same split the `--apply` branch makes below: a Skip-Eintrag is
            # an entry, not a path, and one number over both would put the four
            # states back together on the very surface an operator reads before
            # deciding to store (found in review, this PR).
            paths = [entry for entry in body if entry.get("status") != STATUS_SKIPPED]
            skipped = len(body) - len(paths)
            here = (
                f"{with_spans} with letter boundaries"
                if args.spans
                else f"{sum(1 for entry in entries if entry.get('status') != STATUS_SKIPPED)} followed here"
            )
            print(
                f"  dry run — {len(paths)} path(s){f' and {skipped} skipped box(es)' if skipped else ''} "
                f"({here}) written to {out}, nothing stored",
                flush=True,
            )
            continue
        # The GET above needs no override — only the write can displace
        # anything, so the flag rides on the push and nowhere else. And only on
        # the rows that actually hand a drawing over: `--replace-authored`
        # covers every stored Fassung of the strip, and the server's 409 is the
        # one check that does not run on this machine.
        push_url = f"{url}?replace_authored=true" if handed_over else url
        # The token of the read this merge was made on. The server demands it
        # and refuses (412) when the stored list has moved since — a box the
        # author drew in the workbench while this run was following is exactly
        # that case, and the merge above cannot know about it. Re-run, and the
        # fresh read carries the drawing.
        try:
            stored = request_json("PUT", push_url, token, {"format": wire_format, "pfade": body}, if_match=etag) or {}
        except StaleRead as exc:
            # The server's refusal says what happened; this says what to do
            # about it, which is the sentence only the terminal can write. The
            # re-run deliberately drops `--replace-authored`: whatever landed
            # in between is exactly what a blanket override would give up
            # again, so getting it back has to be a fresh decision on a fresh
            # read.
            narrowed = "".join(f" --box {index}" for index in args.box or []) + (" --spans" if args.spans else "")
            unreached = [other["fassung"] for other in rows[position + 1 :]]
            raise SystemExit(
                f"{exc}\n"
                f"  Nothing of {row['strip']}/{row['fassung']} was stored. The list above was read before it "
                "moved — a box drawn in the workbench, or another run. Run it again; the fresh read carries "
                "what landed in between:\n"
                # The RESOLVED base, named explicitly rather than left to
                # `--api`'s fallback chain: without it the line re-runs against
                # `$EIGENHAND_API` or, failing that, production — so a drill
                # against a throwaway stack would hand the operator a command
                # that writes to the real database (found in review, this PR).
                f"    ADMIN_TOKEN=… uv run python -m tools.eigenhand.pfad --api {shlex.quote(base)} "
                f"--hand {hand} --strip {row['strip']} --fassung {row['fassung']}{narrowed} --apply"
                + (
                    # The line above is per Fassung, and this run was stopped
                    # part way through the strip. Naming the rest is the
                    # difference between „one Fassung to redo" and a silent
                    # gap the operator only finds in the workbench later.
                    f"\n  This run stopped there: {', '.join(unreached)} of {row['strip']} were not attempted. "
                    "Run them after the line above, or repeat the whole strip without --fassung."
                    if unreached
                    else ""
                )
            ) from exc
        # A skip is an entry, not a path. Counting the two together would put
        # the four states back into one number — which is the whole reason the
        # Skip-Eintrag exists (found in review, PR #639).
        entries = stored.get("pfade") or []
        paths = [entry for entry in entries if entry.get("status") != STATUS_SKIPPED]
        skipped = len(entries) - len(paths)
        written += with_spans if args.spans else len(paths)
        print(
            f"  stored {len(paths)} path(s){f' and {skipped} skipped box(es)' if skipped else ''} at {base}"
            + (f", {with_spans} of them with letter boundaries" if args.spans else ""),
            flush=True,
        )
    if args.apply:
        print(
            f"{written} box(es) with letter boundaries in the shared database — the workbench shows them in the editor"
            if args.spans
            else f'{written} path(s) in the shared database — the workbench shows them under "Pfad zeigen"'
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
