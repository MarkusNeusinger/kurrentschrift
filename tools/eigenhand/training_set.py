"""Der Trainingssatz — the Bahnen the author drew, as material the follower learns from.

WHY THIS EXISTS. The author, 2026-09-18, verbatim: „die hand nachgefahrenen
linien dienen auch als trainingsmenge um den folger nachhaltig immer besser zu
machen". A Bahn he traced in the workbench is not only a corrected record — it
is ground truth about HIS pen, and the only such truth this project will ever
have about a living hand. The drawing surface landed with the Streifen-Editor;
this is the other half: the drawings, cut out as a local, gitignored set the
follower and the Span-Zuordner can be trained and measured on (proposal §7.5,
„Und er ist Trainingsmenge").

    # draw the split ONCE — no network, no Bahn needed, and refuses a second time
    uv run python -m tools.eigenhand.training_set --hand mn-suetterlin --draw mn-2026-09

    # export whatever hand work exists today
    ADMIN_TOKEN=… uv run python -m tools.eigenhand.training_set --hand mn-suetterlin

NOT A BENCH ROOT, and that is the load-bearing sentence of the whole module.
A strip has no reference trace — that is Prüfstein 2 of the capture doctrine
(`docs/proposals/eigenhand-erfassung.md` §12), and `core.eigenhand.pfad` says
the same where it refuses to route a strip path into `word_instances`. So a
number measured against a hand-drawn Bahn is NOT a bench number, and nothing
here may ever reach a bench headline. Three things keep that from happening by
accident rather than by discipline: this tree lives outside every
`tools/*/fixtures` root, its manifest is deliberately NOT called
`manifest.json` — which is exactly what the lab loaders glob for, one level
down — and `tests/test_eigenhand_training_set.py` pins both, the way
`tests/test_lab_fixture_wiring.py` pins the bench wiring it must not be
confused with.

TWO HOLD-OUT SETS, disjoint, and one of them is not ours to spend. Author
decision of 2026-09-20, against the recommendation in the Phase-2 plan and
answering FM3 of the Freigabe-Maschine in the same direction: the follower's
improvement gets its own Rückhaltemenge, and the release check of the
Freigabe-Maschine gets a second one. So three sets in all — `practice` is what
is left to train on, `holdout-follower` is held back from every follower
experiment, `holdout-release` is held back from everything until a hand is
released.

THE DRAW IS AN ACT, never a side effect. It is a separate command, it takes a
KEY, it writes the memberships down, and it refuses to run twice for one hand.
The alternative — a split that quietly happens on whichever run first finds a
Bahn — is the worst shape available: nobody registered it, nobody can reproduce
it, and it was drawn after the material was already in view.

THE UNIT IS THE STREIFEN, not the word box and not the Fassung. Every Fassung
of one strip is a REPETITION of the same words in the same hand, and the boxes
of one strip were written in one stroke at one sitting — splitting inside a
strip would put near-identical writing on both sides of the line, which is the
leak a hold-out set exists to prevent. It is also the unit FM3 asks for
(„Streifen, die nie geerntet werden").

WHICH IS WHY THE DRAW NEEDS NEITHER NETWORK NOR DATA. It runs over the strips
of the committed, append-never plan (`core/eigenhand/streifen.json`), so it can
be — and should be — drawn before the first Bahn exists: a split decided while
the material is still unwritten cannot be steered by anybody, least of all by
the person drawing it.

AND WHAT HAPPENS WHEN NEW BAHNEN ARRIVE AFTERWARDS: nothing at all. Their strip
already has a side, assigned by a key that was fixed before anyone had seen
them. Only a new STRIP — a later `pool` wave appending to the plan — is
genuinely new, and it falls where the same key puts it, is written into the
record with the date it joined, and is named by the run that adds it. Nothing
is ever re-drawn, and a recorded membership this build no longer reproduces
stops the run instead of being quietly replaced: the RECORD is the authority.

WHERE THE RECORD LIVES. In the hand's `kartei.json`, beside the pulled Bahnen
and for the same reason (author decision A, 2026-09-20): an archive run copies
the Kartei in FULL every time, while a filed Fassung directory is an immutable
copy unit it skips by relative path. The split is the one thing here that is
NOT regenerable — the exported cases are cut from material the archive holds,
but a draw that is lost is a draw that has to be made again, after the data.

THE STATUS FILTER comes from the archive read (`GET /eigenhand/archive/{hand}`)
and from nowhere else: the strip listing carries no status at all, and a
withdrawn Fassung must not travel (`tools.eigenhand.redo --retire` says so —
„excluded from Ist counts and training exports"). Only `angenommen` Fassungen
are exported.

NOT ONE BYTE OF THIS TREE ENTERS THE REPO. It is cut from the reserved own-hand
pixels and from the authored Bahnen of the shared database — the learned
dataset, reserved outside the MIT grant (`docs/reference/quellen-und-rechte.md`
§5). It is gitignored, it is regenerable from the archive plus the database,
and it is NOT part of the archive chain: the only thing here worth backing up
is the draw, and that rides in the Kartei.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from collections.abc import Mapping
from datetime import date as date_cls
from pathlib import Path
from typing import Any
from urllib.parse import quote

import numpy as np
from PIL import Image

from core.config import REPO_ROOT
from core.eigenhand.follower_input import ink_of, label_zones_px, zones_in_crop
from core.eigenhand.ids import ACCEPTED
from core.eigenhand.pfad import authored_spans, frame_for_box, is_authored
from core.eigenhand.plan import load_plan, shaping_form_of
from tools.eigenhand.apiclient import admin_token, api_base, request_json
from tools.eigenhand.kartei import load_kartei, save_kartei

# The word box is cut EXACTLY as the follower cuts it — same crop, same
# binarisation, same printed labels cleared, same shaped slots — because
# training material that does not look like what the follower is fed is
# training material for something else. Imported rather than copied, and the
# private names are deliberate: this seam is the follower's own, and a second
# spelling of it would drift the day either side changes.
# `tools/eigenhand/pfad.py` is not edited from here.
from tools.eigenhand.pfad import LiveDuctus, _case_for_box, _strip_plane, _style_constants
from tools.eigenhand.snapshot import ARCHIVE_SUBDIR
from tools.eigenhand.store import check_hand_id, style_of_hand


# The three sets. „Trainingssatz" and „Rückhaltemenge" stay German in the DOCS,
# where the domain vocabulary lives; the identifiers here are English because
# „training set" and „hold-out set" are exactly the established terms a reader
# recognises (`docs/reference/sprachregelung.md` §5, author decision
# 2026-09-20 — the carve-out is Befund · Tintentreue · Laufform and nothing
# else). `practice` is the remainder and therefore has no share of its own; the
# two hold-out sets are named apart because they are spent by different people
# at different times — one by every follower experiment, one once per hand at
# its release (FM3 (b)).
SET_PRACTICE = "practice"
SET_HOLDOUT_FOLLOWER = "holdout-follower"
SET_HOLDOUT_RELEASE = "holdout-release"
# ORDER IS PART OF THE DRAW: the lot of a strip falls into the first set whose
# cumulative share it undercuts, so swapping these two names would silently
# re-assign every strip in the band between them. It is pinned by a test.
HOLDOUT_SETS = (SET_HOLDOUT_FOLLOWER, SET_HOLDOUT_RELEASE)
SETS = (SET_PRACTICE, *HOLDOUT_SETS)

# What a fifth of the plan buys at 188 strips: ~38 strips per hold-out set,
# ~112 left to train on. The shares are recorded WITH the draw, so this is the
# default of the day the draw is made and never a knob afterwards — changing it
# later would mean a second draw, which this tool refuses.
DEFAULT_SHARES: dict[str, float] = {SET_HOLDOUT_FOLLOWER: 0.2, SET_HOLDOUT_RELEASE: 0.2}

# The Kartei's envelope around the draw — versioned apart from KARTEI_FORMAT
# exactly as the pulled Bahnen are, so an older tool simply does not see the
# key instead of refusing the whole file.
HOLDOUT_FORMAT = 1

# The export's own manifest version, and its FILE NAME. The name is a guard,
# not a taste: `tools.glyphlab.cases` and `tools.wordlab.cases` find a fixture
# root by globbing `<root>/*/manifest.json`, so a file of that name one level
# under this tree would make it loadable as a bench root by anyone who pointed
# `--fixtures` here. Pinned by `tests/test_eigenhand_training_set.py`.
#
# Format 2 (2026-09-24): `ink.png` has the printed labels cleared, because the
# follower's input does since the author's decision of that day, and each case
# names how many printed label zones of its row were cleared. Format 1 exported the
# unmasked ink; nothing about the two looks different from the outside, so the
# number is the only way a reader can tell a stale tree from a current one.
TRAINING_SET_FORMAT = 2
MANIFEST_NAME = "training_set.json"

# Said inside the artefact, not only in this docstring: the manifest is what a
# later reader opens, and the one sentence they must not miss is that these
# numbers may never become a bench number. German, because it is a sentence for
# the author to read, not an identifier.
MANIFEST_NOTE = (
    "Trainingsmaterial, kein Mess-Satz: ein Streifen hat keine Referenzspur "
    "(docs/proposals/eigenhand-erfassung.md §12, Prüfstein 2). Eine Zahl gegen eine von Hand "
    "gezeichnete Bahn ist keine Bench-Zahl, und keine Bench-Wurzel zeigt hierher."
)

CASE_JSON = "path.json"
CASE_CROP = "crop.png"
CASE_MASK = "ink.png"


# The one path inside the repository this tree may occupy, because it is the
# one path `.gitignore` excludes. Everything else goes outside the checkout.
DEFAULT_EXPORT_ROOT = REPO_ROOT / "tools" / "eigenhand" / "training-sets"


def export_root() -> Path:
    """The local training-set root (gitignored; env-overridable for tests).

    Under `tools/`, as the proposal settles it (§7.5, „als lokaler, gitignorter
    Export unter `tools/`"), and deliberately NOT under `tools/*/fixtures`: a
    fixture-shaped tree next to the bench roots is an invitation to point a
    bench at it.
    """
    override = os.environ.get("EIGENHAND_TRAINING_SET")
    return Path(override) if override else DEFAULT_EXPORT_ROOT


def hand_export_dir(hand: str, root: Path | None = None) -> Path:
    return (root or export_root()) / check_hand_id(hand)


def checked_out(out: Path) -> Path:
    """Refuse a target inside the checkout that the gitignore rule does not cover.

    „No byte of this tree enters the repo" is a licensing promise
    (`quellen-und-rechte.md` §5), and up to here it rested entirely on one
    `.gitignore` line — while `--out .` and `EIGENHAND_TRAINING_SET` could
    both put reserved own-hand crops anywhere in the checkout as untracked,
    unignored files that the next wide `git add -A` would stage. Outside the
    repository nothing needs guarding; inside it, only the one ignored root
    does.
    """
    resolved = out.expanduser().resolve()
    if resolved.is_relative_to(REPO_ROOT.resolve()) and not resolved.is_relative_to(DEFAULT_EXPORT_ROOT.resolve()):
        raise SystemExit(
            f"{resolved} is inside the repository but outside the gitignored training root "
            f"{DEFAULT_EXPORT_ROOT} — this export is cut from reserved own-hand material and no byte of it "
            "may enter the repo (docs/reference/quellen-und-rechte.md §5). Export outside the checkout, or "
            "leave --out unset."
        )
    return out


def case_id(strip: str, fassung: str, box_index: int) -> str:
    """One word box of one Fassung, as a directory name — sortable, flat."""
    return f"{strip}-{fassung}-b{box_index:02d}"


def set_for_strip(key: str, hand: str, strip: str, shares: Mapping[str, float]) -> str:
    """Which set a strip belongs to — a pure function of the draw's key and its id.

    Deterministic rather than shuffled, and that is what makes the split
    honest for material that does not exist yet: a strip written next year
    falls where a key fixed today puts it, with nobody in a position to look
    first. The digest is taken over the HAND as well, so two hands drawn under
    one key do not hold out the same strips.
    """
    digest = hashlib.sha256(f"{key}\x00{hand}\x00{strip}".encode()).digest()
    lot = int.from_bytes(digest[:8], "big") / 2**64
    boundary = 0.0
    for set_name in HOLDOUT_SETS:
        boundary += float(shares.get(set_name, 0.0))
        if lot < boundary:
            return set_name
    return SET_PRACTICE


def _checked_shares(shares: Mapping[str, Any]) -> dict[str, float]:
    """The two shares, or a refusal — a draw with no training half is not a draw."""
    out: dict[str, float] = {}
    for set_name in HOLDOUT_SETS:
        value = shares.get(set_name)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.0 < float(value) < 1.0:
            raise SystemExit(f"share of {set_name} must be a fraction strictly between 0 and 1, got {value!r}")
        out[set_name] = float(value)
    if sum(out.values()) >= 1.0:
        raise SystemExit(
            f"the two Rückhaltemengen would take {sum(out.values()):.2f} of every strip — "
            f"nothing would be left to train on"
        )
    return out


def holdout_of(kartei: Mapping[str, Any]) -> dict[str, Any] | None:
    """The hand's draw as this machine holds it, or None where none was made.

    Refuses a record in a shape it does not know rather than reading it as „no
    draw": a missing split is the one answer that must never be given wrongly,
    because the run after it would draw a second one. Unknown means NEWER —
    every shape up to the current one stays readable, the same rule
    `tools.eigenhand.kartei.pfade_of` follows for an archived Kartei.
    """
    record = kartei.get("holdout")
    if record is None:
        return None
    if not isinstance(record, dict):
        raise SystemExit("Kartei: `holdout` is not a record — refusing to read the draw")
    version = record.get("format")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise SystemExit(f"Kartei: the Rückhalt draw declares no format ({version!r}) — refusing to read it")
    if version > HOLDOUT_FORMAT:
        raise SystemExit(
            f"Kartei: the Rückhalt draw is in format {version}, this tool reads up to {HOLDOUT_FORMAT} — "
            "that Kartei was written by a NEWER tool; update this one"
        )
    strips = record.get("strips")
    if not isinstance(strips, dict):
        raise SystemExit("Kartei: the Rückhalt draw carries no strip memberships — refusing to read it")
    for strip, row in strips.items():
        if not isinstance(row, dict) or row.get("set") not in SETS:
            raise SystemExit(f"Kartei: strip {strip} of the Rückhalt draw names no known set — refusing to read it")
    return record


def archived_holdout(hand: str, archive: str | None = None) -> tuple[dict, Path] | None:
    """The newest archived draw of this hand, or None where the archive holds none.

    The refusal of a second draw reads the LOCAL Kartei, and that is not enough
    on its own: `sync --from <snapshot>` — the restore path — reads an archived
    Kartei and pushes it to the API without ever writing the local one
    (`tools/eigenhand/sync.py`). A lost data root therefore leaves the
    authoritative draw sitting in the archive while `load_kartei` hands back an
    empty structure, and the create-once guarantee would fall to a fresh draw
    over a hand that already has one (found in review, PR #647).

    Every snapshot carries a COMPLETE Kartei by construction, and stamps sort
    chronologically, so the newest one that names this hand is the authority —
    the same rule `sync._source` follows. Where no archive is configured this
    answers None and the caller says that it could not look.
    """
    value = archive or os.environ.get("KURRENTSCHRIFT_ARCHIVE")
    if not value:
        return None
    hand_archive = Path(value).expanduser() / ARCHIVE_SUBDIR / hand
    if not hand_archive.is_dir():
        return None
    for snapshot in sorted(hand_archive.iterdir(), key=lambda entry: entry.name, reverse=True):
        kartei_file = snapshot / "kartei.json"
        if not kartei_file.is_file():
            continue
        try:
            filed = json.loads(kartei_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            # A half-written or unreadable snapshot is not evidence of absence;
            # keep looking rather than concluding „no draw", which is the one
            # answer that must never be given wrongly.
            continue
        if filed.get("hand") != hand:
            continue
        record = holdout_of(filed)
        if record is not None:
            return record, snapshot
    return None


def _refuse_if_archived(hand: str, archive: str | None) -> None:
    """Stop where the archive holds a draw this data root has lost."""
    filed = archived_holdout(hand, archive)
    if filed is None:
        return
    record, snapshot = filed
    counts = _counts(record)
    raise SystemExit(
        f"this data root holds no draw for {hand}, but the ARCHIVE does: key {record.get('key')!r}, drawn on "
        f"{record.get('drawn_on')} ({', '.join(f'{set_name} {counts[set_name]}' for set_name in SETS)}), in {snapshot}.\n"
        f"That draw is the authority and it is not regenerable. Restore this hand's Kartei from that snapshot "
        f"before drawing or exporting — `sync --from` pushes an archived Kartei UP to the API and does not "
        f"write the local one, so it is not the restore that matters here."
    )


def draw(hand: str, kartei: dict, key: str, shares: Mapping[str, float], today: str) -> dict:
    """Draw the split once, over every strip of the committed plan.

    Mutates `kartei` and hands back the record. Refusing a second draw is the
    whole mechanism: a re-draw after the first Bahn exists would move material
    across the line that has already been trained on, and no later reader could
    tell.
    """
    if not key.strip():
        raise SystemExit("the draw needs a key — it is what makes the split reproducible")
    existing = holdout_of(kartei)
    if existing is not None:
        counts = _counts(existing)
        raise SystemExit(
            f"{hand} was already drawn on {existing.get('drawn_on')} under key {existing.get('key')!r} "
            f"({', '.join(f'{set_name} {counts[set_name]}' for set_name in SETS)}) — refusing to draw again. "
            "A second draw moves strips across a line that material has already been trained on, and "
            "nothing downstream could tell. There is deliberately no override."
        )
    shares = _checked_shares(shares)
    strips = {
        strip: {"set": set_for_strip(key, hand, strip, shares), "since": today}
        for strip in sorted(load_plan()["strips"])
    }
    record = {"format": HOLDOUT_FORMAT, "key": key, "drawn_on": today, "shares": shares, "strips": strips}
    kartei["holdout"] = record
    return record


def _counts(record: Mapping[str, Any]) -> dict[str, int]:
    strips = record.get("strips") or {}
    return {set_name: sum(1 for row in strips.values() if row.get("set") == set_name) for set_name in SETS}


def extend(hand: str, record: dict, today: str) -> list[tuple[str, str]]:
    """Give every plan strip the draw does not know yet its side. Returns the new ones.

    Not a second draw: the key is the one already recorded, so a strip appended
    to the plan by a later `pool` wave falls exactly where it would have fallen
    had it existed on the day of the draw. What is NEW is only that this run is
    the first to ask.

    A membership already on record that this build no longer reproduces stops
    the run. That is a code change, not a data change, and the record is the
    authority — silently re-assigning would move strips across the line.
    """
    shares = _checked_shares(record.get("shares") or {})
    key = record.get("key")
    if not isinstance(key, str) or not key:
        raise SystemExit("Kartei: the Rückhalt draw names no key — its memberships cannot be checked")
    strips: dict[str, dict] = record["strips"]
    drifted = [
        strip for strip, row in sorted(strips.items()) if row.get("set") != set_for_strip(key, hand, strip, shares)
    ]
    if drifted:
        raise SystemExit(
            f"{len(drifted)} recorded membership(s) do not reproduce under the recorded key "
            f"({', '.join(drifted[:8])}{' …' if len(drifted) > 8 else ''}) — the draw rule has moved. "
            "The RECORD is the authority; fix the rule, never the record."
        )
    added = [
        (strip, set_for_strip(key, hand, strip, shares))
        for strip in sorted(load_plan()["strips"])
        if strip not in strips
    ]
    for strip, set_name in added:
        strips[strip] = {"set": set_name, "since": today}
    return added


def _accepted(archive: Mapping[str, Any]) -> set[tuple[str, str]]:
    """The (strip, Fassung) pairs that count as training data — off the ARCHIVE read.

    The strip listing carries no status at all, so this is the only place the
    answer exists: a Fassung the author withdrew (`redo --retire`) keeps its
    file and its row and leaves every training export
    (`tools.eigenhand.redo`), and a rejected one was never training data.
    """
    return {
        (row["strip"], row["fassung"])
        for row in archive.get("fassungen", [])
        if row.get("status") == ACCEPTED and row.get("strip") and row.get("fassung")
    }


def _hand_work(entries: list[dict]) -> list[dict]:
    """The entries carrying the author's own hand — a drawn Bahn or corrected boundaries.

    The same two pieces the archive chain pulls (`tools.eigenhand.pull
    --pfade`): a followed Bahn is a derivation and can be made again, so it is
    not what the follower has to learn from. A Skip-Eintrag carries no path at
    all and is excluded by having no strokes.
    """
    return [entry for entry in entries if (is_authored(entry) or authored_spans(entry)) and entry.get("strokes")]


def _write_case(target: Path, payload: dict, crop: np.ndarray, mask: np.ndarray) -> None:
    """One case on disk: what the box says, and the two planes it says it about.

    The crop and the ink mask travel, the skeleton and the half-width map do
    not — they are one call away (`core.extract.skeleton_and_width`) and
    freezing a derived plane is what a BENCH does. Nothing in this tree is
    frozen; it is regenerated from the archive and the database whenever it is
    wanted.
    """
    target.mkdir(parents=True, exist_ok=True)
    (target / CASE_JSON).write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    Image.fromarray((np.clip(crop, 0.0, 1.0) * 255).astype(np.uint8), mode="L").save(target / CASE_CROP)
    Image.fromarray((np.asarray(mask) * 255).astype(np.uint8), mode="L").save(target / CASE_MASK)


def _followed_ink(case: Any, zones: list) -> np.ndarray:
    """The box's ink with the printed labels cleared — the mask the follower is handed by default.

    Stage 1 of `core.eigenhand.follower_input`, called the way
    `tools.eigenhand.pfad.adapt_case` calls it: the row's zones in the box's
    own crop pixels, the grey crop binarised UNPAINTED and the zones cleared
    after, and with no zone at all the mask `_case_for_box` already cut. Only
    stage 1, because it is the only one the follower runs by default (author
    decision of 2026-09-24) and the only one that moves no pixel of the frame
    — a resampled crop would no longer be the rectangle `rect_px` names, and
    `registration_px` would stop landing on it. The crop itself stays
    unpainted in the export, as it does for the follower.
    """
    if not zones:
        return case.mask
    mask, _skel, _width_map = ink_of(case.crop, zones)
    return mask


def _occupant(hand_dir: Path) -> str | None:
    """The hand whose export already sits here, or None where none does.

    The default target is per hand (`<root>/<hand>`), but `--out` is a
    documented flag and `<root>` is the obvious thing to type — and a case id
    carries no hand, so two hands sharing one directory would interleave in the
    same `<set_name>/` folders and each run would prune the other's cases away.
    Refusing costs nothing: the manifest has named the hand all along.
    """
    manifest = hand_dir / MANIFEST_NAME
    if not manifest.exists():
        return None
    try:
        return json.loads(manifest.read_text(encoding="utf-8")).get("hand")
    except (OSError, ValueError) as exc:
        raise SystemExit(
            f"{manifest} cannot be read ({exc}) — refusing to export over a tree it cannot identify"
        ) from exc


def _check_target(out: Path, hand: str) -> None:
    """Refuse a target that is not this hand's — BEFORE the first case is cut."""
    occupant = _occupant(out)
    if occupant is not None and occupant != hand:
        raise SystemExit(
            f"{out} already holds the export of {occupant!r} — two hands in one directory would prune each "
            f"other's cases away, because a case id names no hand. Leave --out unset (the default is per hand) "
            f"or point it at a directory of its own."
        )


def _prune(hand_dir: Path, keep: set[str], hand: str) -> list[str]:
    """Drop case directories this run did not write — and only inside our own tree.

    A withdrawn Fassung has to LEAVE the export, or the status filter would
    hold for a first run and quietly stop holding for every later one. Deleting
    is safe exactly here and nowhere else: this tree is regenerable, it is not
    the archive, and the guard below refuses to remove anything under a
    directory that does not carry this tool's own manifest for this very hand —
    a mistyped `--out` then finds nothing to destroy.
    """
    if _occupant(hand_dir) != hand:
        return []
    dropped: list[str] = []
    for set_name in SETS:
        set_dir = hand_dir / set_name
        if not set_dir.is_dir():
            continue
        for path in sorted(set_dir.iterdir()):
            if path.is_dir() and path.name not in keep:
                shutil.rmtree(path)
                dropped.append(f"{set_name}/{path.name}")
    return dropped


def _case_payload(
    hand: str,
    style: str,
    set_name: str,
    row: Mapping[str, Any],
    entry: Mapping[str, Any],
    frame: Mapping[str, Any],
    # `Any` rather than `WordCase`: naming the type would import the lab module
    # at module level for a hint, and `tools.eigenhand.pfad` keeps the same seam
    # untyped for the same reason.
    case: Any,
    missing: list[str],
    pfad_format: int | None,
    label_zones: int,
) -> dict:
    """Everything about one box that is not a plane — the entry, plus its address.

    The stored entry's own field names are kept verbatim rather than
    translated: a consumer of this set reads the same `strokes`,
    `registration_px` and `letter_spans` it would read off the API, and the
    only additions are the identity of the box and the shaping context its
    `letter_spans[].slot` indexes into.
    """
    return {
        "format": TRAINING_SET_FORMAT,
        # The ROW's own Streifen-Pfad format, kept apart from this file's
        # envelope version exactly as `kartei.pfad_record` keeps it apart from
        # `PFAD_ARCHIVE_FORMAT`. Without it a reader cannot tell „this box has
        # no corrected boundaries" from „this row predates `letter_spans` and
        # the two sensors" — both look like `authored_boundaries: 0` and a thin
        # `meta`, and `core.eigenhand.tintentreue` greys a whole box out on the
        # difference.
        "pfad_format": pfad_format,
        "hand": hand,
        "style": style,
        "set": set_name,
        "strip": row["strip"],
        "fassung": row["fassung"],
        "sheet": row["sheet"],
        "row_index": row["row_index"],
        "box_index": entry["box_index"],
        "word": entry.get("word") or frame["word"],
        "drawn": is_authored(entry),
        "authored_boundaries": len(authored_spans(entry)),
        "strokes": entry.get("strokes") or [],
        "registration_px": entry.get("registration_px"),
        "xh_px": entry.get("xh_px"),
        "letter_spans": entry.get("letter_spans"),
        "verfahren": entry.get("verfahren"),
        "erzeugt_am": entry.get("erzeugt_am"),
        "flecken_n": entry.get("flecken_n"),
        "konfiguration": entry.get("konfiguration") or {},
        "meta": entry.get("meta") or {},
        # The box inside the STRIP's pixels, and the printed ruling of the row.
        # `registration_px` above maps the strokes into the same frame, so a
        # reader needs this rectangle to put them over the exported crop.
        "rect_px": list(frame["rect_px"]),
        "baseline_row": frame["baseline_row"],
        "waist_row": frame["waist_row"],
        # The shaped slots `letter_spans[].slot` counts into, and the glyph
        # keys the plate does not carry. A box whose word is unauthored is not
        # a defect here — it is the most interesting case in the set, because
        # it is one the follower could not have produced at all.
        "slots": [
            {"key": slot.key, "text": slot.text, "position": slot.position, "ligature": slot.ligature}
            for slot in case.slots
        ],
        "unauthored_glyphs": missing,
        # How many printed label zones of the row were cleared from `ink.png`
        # — the count the follower records in `meta.input.label_zones`. Zero
        # is a row printed without text in its cut, not a mask left off.
        "label_zones": label_zones,
        "images": {"crop": CASE_CROP, "mask": CASE_MASK},
    }


def export(hand: str, base: str, token: str, out: Path, today: str, archive: str | None = None) -> int:
    """Cut every hand-drawn box of one hand into its set. Returns the case count."""
    checked_out(out)
    _check_target(out, hand)
    kartei = load_kartei(hand)
    record = holdout_of(kartei)
    if record is None:
        # Before telling anyone to draw, make sure this is a hand that never
        # was drawn rather than one whose Kartei is simply gone: sending the
        # operator to `--draw` in the second case is how a second draw
        # happens.
        _refuse_if_archived(hand, archive)
        raise SystemExit(
            f"{hand} has no Rückhalt draw — a training export without a hold-out set is homework handed in "
            f"as an exam. Draw it once (no network, no Bahn needed):\n"
            f"  uv run python -m tools.eigenhand.training_set --hand {hand} --draw <key>"
        )
    added = extend(hand, record, today)
    if added:
        save_kartei(hand, kartei)
        print(
            f"{len(added)} strip(s) appended to the plan since the draw, assigned under its key: "
            f"{', '.join(f'{strip} → {set_name}' for strip, set_name in added)}",
            flush=True,
        )
    memberships: dict[str, dict] = record["strips"]

    style = style_of_hand(hand)
    constants = _style_constants(style)
    prior = {**constants, "seed": LiveDuctus(base, token, constants["source_id"])}
    plan = load_plan()

    archive = request_json("GET", f"{base}/eigenhand/archive/{quote(hand)}", token) or {}
    accepted = _accepted(archive)
    listing = request_json("GET", f"{base}/eigenhand/strips/{quote(hand)}", token) or {}

    layouts: dict[str, dict] = {}
    written: list[dict] = []
    keep: set[str] = set()
    skipped = {"not_accepted": 0, "no_hand_work": 0, "no_geometry": 0, "not_in_plan": 0}
    for row in sorted(listing.get("strips", []), key=lambda item: (item["strip"], item["fassung"])):
        strip, fassung = row["strip"], row["fassung"]
        if (strip, fassung) not in accepted:
            skipped["not_accepted"] += 1
            continue
        url = f"{base}/eigenhand/strips/{quote(hand)}/{quote(strip)}/{quote(fassung)}/pfade"
        answered = request_json("GET", url, token) or {}
        pfad_format = answered.get("format")
        entries = _hand_work(answered.get("pfade") or [])
        if not entries:
            skipped["no_hand_work"] += 1
            continue
        membership = memberships.get(strip)
        if membership is None:
            # The plan is the draw's population, so a strip outside it has no
            # side — and inventing one here would be a draw made by a tool.
            print(f"  {strip}/{fassung}: not in the strip plan, so not in the draw — left out", flush=True)
            skipped["not_in_plan"] += 1
            continue
        set_name = membership["set"]
        if row["sheet"] not in layouts:
            layouts[row["sheet"]] = (
                request_json("GET", f"{base}/eigenhand/sheets/{quote(hand)}/{quote(row['sheet'])}/layout", token) or {}
            )
        layout = layouts[row["sheet"]]
        layout_row = (layout.get("rows") or [])[row["row_index"]]
        plane = _strip_plane(base, token, hand, row)
        # Once per row, in STRIP pixels, exactly as `pfad.follow_row` reads
        # them: the labels are printed per row and each box only shifts them
        # into its own crop.
        label_zones = label_zones_px(layout, layout_row, row["crop_origin_mm"], row["width_px"], row["height_px"])
        for entry in entries:
            index = entry["box_index"]
            ident = case_id(strip, fassung, index)
            try:
                frame = frame_for_box(layout_row, row["crop_origin_mm"], row["width_px"], row["height_px"], index)
            except ValueError as exc:
                # A drawing on a Bogen printed before the cut geometry existed:
                # it cannot be placed in the strip's pixels, so it cannot be
                # cut out either. One such box must not take the run down.
                print(f"  {ident}: {exc} — left out", flush=True)
                skipped["no_geometry"] += 1
                continue
            word = frame["word"]
            case, missing = _case_for_box(prior, plane, frame, word, shaping_form_of(plan, word), ident)
            zones = zones_in_crop(label_zones, frame["rect_px"])
            payload = _case_payload(hand, style, set_name, row, entry, frame, case, missing, pfad_format, len(zones))
            _write_case(out / set_name / ident, payload, case.crop, _followed_ink(case, zones))
            keep.add(ident)
            written.append(payload)
            print(
                f"  {ident:<22} {set_name:<20} {word:<16} "
                f"{'gezeichnet' if payload['drawn'] else 'gefolgt'}, "
                f"{payload['authored_boundaries']} Grenze(n) von Hand",
                flush=True,
            )

    dropped = _prune(out, keep, hand)
    manifest = {
        "format": TRAINING_SET_FORMAT,
        "note": MANIFEST_NOTE,
        "hand": hand,
        "style": style,
        "exported_on": today,
        "api": base,
        "source_id": constants["source_id"],
        "holdout": {
            "key": record.get("key"),
            "drawn_on": record.get("drawn_on"),
            "shares": record.get("shares"),
            "strips": _counts(record),
        },
        "sets": {
            set_name: {
                "cases": sum(1 for filed in written if filed["set"] == set_name),
                "strips": len({filed["strip"] for filed in written if filed["set"] == set_name}),
            }
            for set_name in SETS
        },
        "cases": [
            {
                "id": case_id(filed["strip"], filed["fassung"], filed["box_index"]),
                "set": filed["set"],
                "strip": filed["strip"],
                "fassung": filed["fassung"],
                "box_index": filed["box_index"],
                "word": filed["word"],
                "drawn": filed["drawn"],
                "authored_boundaries": filed["authored_boundaries"],
            }
            for filed in written
        ],
        "skipped": skipped,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if dropped:
        # Loud, because this is the status filter DOING something: a withdrawn
        # Fassung leaving the export is the point, and a silent removal would
        # look like a tool losing files.
        print(f"dropped {len(dropped)} case(s) this run no longer exports: {', '.join(dropped)}", flush=True)
    counts = manifest["sets"]
    print(
        f"{hand}: {len(written)} case(s) in {out} — "
        + " · ".join(f"{set_name} {counts[set_name]['cases']}" for set_name in SETS)
        + f" (skipped: {skipped['not_accepted']} not accepted, "
        f"{skipped['no_hand_work']} without hand work"
        + (f", {skipped['no_geometry']} without Bogen geometry" if skipped["no_geometry"] else "")
        + (f", {skipped['not_in_plan']} outside the plan" if skipped["not_in_plan"] else "")
        + ")"
    )
    return len(written)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True, help="hand id, e.g. mn-suetterlin")
    ap.add_argument(
        "--draw",
        default=None,
        metavar="KEY",
        help="draw the two hold-out sets ONCE under this key (local; refuses a second draw)",
    )
    ap.add_argument(
        "--share-follower",
        type=float,
        default=DEFAULT_SHARES[SET_HOLDOUT_FOLLOWER],
        help="share held back for the follower's own measurements (draw only)",
    )
    ap.add_argument(
        "--share-release",
        type=float,
        default=DEFAULT_SHARES[SET_HOLDOUT_RELEASE],
        help="share held back for the Freigabe-Maschine's release check (draw only)",
    )
    ap.add_argument("--out", type=Path, default=None, help="export directory (default: the gitignored local root)")
    ap.add_argument("--api", default=None, help="API base URL (default: $EIGENHAND_API or production)")
    ap.add_argument("--token", default=None, help="admin token (default: $ADMIN_TOKEN)")
    ap.add_argument(
        "--archive",
        default=None,
        help="archive clone root (default: $KURRENTSCHRIFT_ARCHIVE) — read only, to see a draw this data root lost",
    )
    ap.add_argument(
        "--date", "--datum", dest="date", default=None, help="ISO date (default: today; explicit for tests)"
    )
    args = ap.parse_args(argv)

    hand = check_hand_id(args.hand)
    today = args.date or date_cls.today().isoformat()
    if args.draw:
        kartei = load_kartei(hand)
        if holdout_of(kartei) is None:
            _refuse_if_archived(hand, args.archive)
        shares = {SET_HOLDOUT_FOLLOWER: args.share_follower, SET_HOLDOUT_RELEASE: args.share_release}
        record = draw(hand, kartei, args.draw, shares, today)
        save_kartei(hand, kartei)
        counts = _counts(record)
        print(
            f"{hand}: drawn under key {args.draw!r} over {len(record['strips'])} plan strips — "
            + " · ".join(f"{set_name} {counts[set_name]}" for set_name in SETS)
        )
        print(
            "recorded in the Kartei, which every archive snapshot copies in full. It is drawn once and "
            "never again — pre-registration: messjournal.md §14 „Trainingssatz `sep20`"
        )
        # The draw is the one artefact of this tool nothing can make again, and
        # until it is filed it exists on exactly one machine. `pull --pfade`
        # prints the same line for the same reason.
        print(
            f"reminder: snapshot NOW so the archive carries it — "
            f"uv run python -m tools.eigenhand.snapshot --hand {hand}"
        )
        if not (args.archive or os.environ.get("KURRENTSCHRIFT_ARCHIVE")):
            print("(no archive configured, so this run could not check whether one was already filed elsewhere)")
        return 0

    export(
        hand,
        api_base(args.api),
        admin_token(args.token),
        args.out or hand_export_dir(hand),
        today,
        archive=args.archive,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
