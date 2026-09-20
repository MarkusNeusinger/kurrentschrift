"""Die Tintentreue — „folgt der Bahn die Tinte?", one traffic light per word box.

A stored Streifen-Pfad says in which ORDER the pen laid the ink down. Whether
that order is worth anything is a second question, and this module answers it:
per WORD BOX, out of the sensors the follower left behind, derived on READ.

Three rules bind everything below, and each of them is somebody's decision.

1. **Referenzfrei.** A written strip has no reference trace by doctrine
   (`docs/proposals/eigenhand-erfassung.md` §12, Prüfstein 2), so every sensor
   here reads the Bahn against the strip's OWN ink. `dtw_xh`, Chamfer and LDTW
   are reference-bound and deliberately absent (`admin-redesign.md` §6.3).
2. **Der schlechteste Sensor entscheidet.** No weighted measure: green only
   where every sensor is inside its green bound, yellow where every sensor is
   inside its yellow one, red the moment ONE crosses it. A good sensor never
   buys a bad one a step. The twin of `befund.befund`'s
   `severity = max(...)` plus its name tiebreak — NOT of `befund._summarise`,
   which folds WORDS and is weighted inside one word (correction of
   2026-09-20).
3. **Die Ampel liest keine Bench-Zahl und speist keine** (`admin-redesign.md`
   §6.3). Nothing here touches `core.quality`, `core.quality_suetterlin` or
   `core.word_metric`, no fixture root is read, and no number computed here
   may travel into a bench report. The thresholds are calibrated to ONE hand
   and are never comparable across hands — a cross-hand „Tintentreue-
   Verteilung" would be the same mistake as a shared `bench_loss`.

WHAT IS GRADED, AND WHAT IS ONLY READ. Five sensors, of which four carry a
pre-registered bound:

* **Absetzer (Bahn)** — the Bahn's own run count (`paper_lifts + 1`) against
  the runs the script joins this word into (`befund.body_runs_expected`, the
  BODY runs only: i-Punkt and Umlaut are not in it). The Befund measures the
  same thing on the INK and calls it „Absetzer (Tinte)" — one defect, two
  labels, never two names (§6.3).
* **Tinte ohne Bahn** — the share of the ink skeleton the Bahn never travels.
* **Papier-Exkursion** — how far the Bahn strays from the ink, in x-heights.
* **AIoU** — the rasterised Bahn against the ink mask.
* **Sprünge und Haken** — strand changes and retrace turns. READ AND SHOWN,
  never graded: the pre-registration carries eight numbers for four sensors
  and none for this one, and a threshold with no anchor is the one thing a
  pre-registration exists to prevent. Its bound is an open item of the
  calibration round (`messjournal.md` §14 „Tintentreue `sep20`").

MEASURED VS DERIVED, and where the numbers come from. Nothing here computes
anything from pixels. The sensors are measured OFFLINE by the follower
(`tools.eigenhand.pfad` over `tools.pairlab.tintenpfad`, which `core` may
never import) and stored in the free-form `pfade[].meta.tintenpfad`; this
module reads them and derives a verdict — the same split `befund` follows
(„Gemessen wird gespeichert, beurteilt wird abgeleitet").

NO SCALAR. The payload is a step, the sensor that names it and the raw
readings — never a 0–100 number. One would end up beside `befund.guete` on
the same screen and be added to it within the month.

NO COLOUR FOR A FASSUNG. A Fassung gets a COUNTER („3 von 4 Kästen folgen"),
never a traffic light of its own (author decision E, 2026-09-20): that would
be a second verdict with its own vocabulary beside `befund.vorschlag` over
the same Fassung, and the common case is the contradictory one — cleanly
written, badly followed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

from core.eigenhand.befund import body_runs_expected
from core.eigenhand.pfad import is_authored


TINTENTREUE_FORMAT = 1

# The PFAD_FORMAT from which a stored row carries ALL the sensors this module
# grades. Rows written before it were followed with three of them, so a colour
# read off those three would claim a verdict for sensors nothing ever computed
# — they stay grey („Format 1 — unvollständig gemessen") until the Fassung is
# followed again. A literal rather than `PFAD_FORMAT`, which is the number of
# the format the running image WRITES and moves: this one is a property of the
# rule below and moves only when the rule gains a sensor.
VOLLSTAENDIG_AB_FORMAT = 2

# Where the sensors live inside the unvalidated `meta` blob, and under which
# keys. The first four are what `tools/eigenhand/pfad.py` has projected since
# the Bahn existed; the last two arrive with PFAD_FORMAT 2 and are named HERE
# so the writing side has one place to read them off.
META_BLOCK = "tintenpfad"
KEY_UNBESUCHT = "ink_unvisited_share"
KEY_ABSETZER = "paper_lifts"
KEY_SPRUENGE = "jumps"
KEY_HAKEN = "hairpins"
KEY_EXKURSION = "paper_excursion_xh"
KEY_AIOU = "aiou"

# ------------------------------------------------------------- the vocabulary
# German, because it is shown in the German admin — and three steps, not four:
# the grey state is not a fourth step but the absence of a measurement, which
# is why it carries its reason in words rather than a colour (§6.3).
STUFEN = ("folgt", "folgt teils", "folgt nicht")
STUFE_UNGEMESSEN = "nicht beurteilt"

SENSOR_ABSETZER = "Absetzer (Bahn)"
SENSOR_UNBESUCHT = "Tinte ohne Bahn"
SENSOR_EXKURSION = "Papier-Exkursion"
SENSOR_AIOU = "AIoU"
SENSOR_SPRUENGE = "Sprünge und Haken"
# Which sensor NAMES a box when two are equally bad. Decided with this module
# (routine engineering, no author decision behind it) and ordered by how much
# of the ductus the defect destroys, after `befund`'s rule 3 „Duktus-Treue
# schlägt Glätte":
#   1. Absetzer      — a wrong number of runs is a wrong ductus, which is the
#                      one thing a Bahn is kept for.
#   2. Tinte ohne Bahn — a stroke the Bahn never travelled is a missing letter
#                      part; it is also the sensor with the measured anchor.
#   3. Papier-Exkursion — the Bahn invents ink where there is none, but locally.
#   4. AIoU          — an area average that notices 2 and 3 again and blurs
#                      where; it may confirm, it should not name.
#   5. Sprünge/Haken — decoder tics on the right ink, the least of the five.
#                      Listed although it is never graded today, so the order
#                      is complete the day it gains a bound.
SENSOR_ORDER = (SENSOR_ABSETZER, SENSOR_UNBESUCHT, SENSOR_EXKURSION, SENSOR_AIOU, SENSOR_SPRUENGE)
# …and which of them a bound exists for. Named rather than inferred from the
# presence of a threshold field: „this sensor is graded" is a decision of the
# pre-registration, and reading it off a `None` would make it a side effect.
SENSOREN_MIT_SCHWELLE = (SENSOR_ABSETZER, SENSOR_UNBESUCHT, SENSOR_EXKURSION, SENSOR_AIOU)

GRUND_NICHTS = "nichts fällt auf"
GRUND_KEIN_EINTRAG = "kein Eintrag"
GRUND_VON_HAND = "von Hand gezeichnet"
GRUND_MASKE = "Maske geändert"
GRUND_UNVOLLSTAENDIG = "unvollständig gemessen"
GRUND_FORMAT = "Format {format} — unvollständig gemessen"


# ------------------------------------------------- the provisional thresholds


@dataclass(frozen=True)
class Schwellen:
    """The eight bounds of one hand, with the day they were set.

    In the CODE and never in the database: `Hand` has no settings column, and
    a threshold behind a DB row is a Regler with an extra step — which
    `docs/proposals/eigenhand-erfassung.md` forbids in as many words („nie ein
    Regler in der Oberfläche, Schwellen sind Mess-Provenienz"). In code, `git
    blame` answers „which bound held on which day", which is the question a
    re-read of an old verdict actually asks.
    """

    stand: str
    # True while the numbers are BORROWED rather than measured on this hand.
    # It travels in the payload so a surface can say so instead of implying a
    # calibration that has not happened.
    vorlaeufig: bool
    unbesucht_gruen: float
    unbesucht_gelb: float
    absetzer_gelb: int
    exkursion_gruen_xh: float
    exkursion_gelb_xh: float
    aiou_gruen: float
    aiou_gelb: float


# The start values of `admin-redesign.md` §6.3, pre-registered in
# `messjournal.md` §14 „Tintentreue `sep20`" before the first computed light.
# NONE of them is measured on the author's hand — three are read off the
# PLATE at 30–35 px x-height and one off the dev-19 set, while a strip is
# scanned at 300 dpi, so every one of them is provisional by construction:
#
#   unbesucht 0,05 / 0,15  around the worst measured share the repo holds for
#                          this sensor, 0,096 at `kann` (`messjournal.md` §14
#                          „Tintenpfad-Arme `sep11`", 0,095 on the adopted
#                          `sep12` stand) — itself a known coverage failure.
#                          Yellow sits ABOVE `werkzeuge.md`'s declared skip
#                          line of 0,10 on purpose: a skip is the FOLLOWER
#                          giving up, this light judges what it did produce
#   Absetzer  = Soll / ±1  one unexplained pen event tolerated, two not
#   Exkursion        0,35  the pre-registered inventory bound
#                          `tools/tracebench/excursions.py::EXCURSION_THRESHOLDS`
#                          (the K-D closure), in x-heights and thus scale-free
#                          in the unit but not in what a scan resolves
#             0,20         NO anchor of its own — a reading of the comment
#                          beside that tuple („ordinary on-ink riding stays
#                          well under 0.35"), and the weakest of the eight
#   AIoU      0,75 / 0,65  around the dev-19 median 0,7929 (`verfahren.md`)
#
# They are replaced ONCE per hand by the calibrated set of the blind round
# (author decision Q10 b, 2026-09-18; the instrument is PR 13 of Phase 2), and
# the label falls in the same commit that dates the new numbers.
VORLAEUFIG = Schwellen(
    stand="2026-09-20",
    vorlaeufig=True,
    unbesucht_gruen=0.05,
    unbesucht_gelb=0.15,
    absetzer_gelb=1,
    exkursion_gruen_xh=0.20,
    exkursion_gelb_xh=0.35,
    aiou_gruen=0.75,
    aiou_gelb=0.65,
)

# One calibrated set per hand, keyed by `hands.id`. Empty until the first
# blind round has run — a hand with no row is graded with the borrowed values
# above and says so through `vorlaeufig`. A calibration is written here as a
# new `Schwellen(...)` with its own date; an existing one is never edited,
# because the verdicts printed under it were printed under those numbers.
SCHWELLEN_JE_HAND: dict[str, Schwellen] = {}


def schwellen_of(hand: str) -> Schwellen:
    """The bounds that hold for this hand — the calibrated ones, or the borrowed."""
    return SCHWELLEN_JE_HAND.get(hand, VORLAEUFIG)


# ------------------------------------------------------- reading a free blob


def _zahl(value: Any) -> float | None:
    """A finite number, or None for everything else the blob may hold.

    `meta` is stored unvalidated — `core.eigenhand.pfad.check_paths` passes it
    straight through — so this has to refuse strings, booleans and the two
    floats that are `typeof number` and still not a reading. The twin in the
    SPA (`app/src/sections/admin/eigenhand/pfadRohzahlen.ts`) refuses exactly
    the same set; `tests/fixtures/tintentreue_cases.json` pins that both do.

    `bool` is excluded explicitly because in Python it IS an int, which is the
    one place the two languages would otherwise disagree: `true` is not a
    number in JavaScript.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except OverflowError:
        # A JSON integer wider than a float64. `json.loads` builds it as an
        # arbitrary-precision int and `JSON.parse` turns the same literal into
        # `Infinity`, which the twin already refuses — so the conversion has to
        # refuse it too, or the two answers differ AND the read path dies on a
        # blob somebody pushed.
        return None
    return number if isfinite(number) else None


def _sensorblock(pfad: Mapping[str, Any]) -> Mapping[str, Any]:
    """`meta.tintenpfad` as a mapping, or an empty one.

    A follower writing a LIST here would read as an empty sensor set in
    JavaScript (an array is an object too) — the TS twin has to test for that
    explicitly, a Python `Mapping` check refuses it by itself. Stated because
    the two guards are one rule and a reader of either should find the other.
    """
    meta = pfad.get("meta")
    if not isinstance(meta, Mapping):
        return {}
    block = meta.get(META_BLOCK)
    return block if isinstance(block, Mapping) else {}


@dataclass(frozen=True)
class Rohzahlen:
    """The four sensors the follower has written since the Bahn existed.

    The twin of `pfadRohzahlen.ts`, field for field, and `gemessen` is its
    `measured`: „did a follower leave its diagnosis block behind at all",
    NOT „were all five sensors computed" — that second question is what the
    row's stored format answers. Keeping the two apart is the whole point:
    `ink_unvisited_share: 0` is the BEST reading a Bahn can get, and the
    follower stores a sensor it did not compute as `null`, so a reader that
    collapses the two lets an unmeasured box claim the perfect path.
    """

    ink_unvisited_share: float | None
    paper_lifts: float | None
    jumps: float | None
    hairpins: float | None
    gemessen: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def rohzahlen(pfad: Mapping[str, Any]) -> Rohzahlen:
    """The stored sensors of one word box, read defensively."""
    block = _sensorblock(pfad)
    werte = {
        "ink_unvisited_share": _zahl(block.get(KEY_UNBESUCHT)),
        "paper_lifts": _zahl(block.get(KEY_ABSETZER)),
        "jumps": _zahl(block.get(KEY_SPRUENGE)),
        "hairpins": _zahl(block.get(KEY_HAKEN)),
    }
    return Rohzahlen(**werte, gemessen=any(wert is not None for wert in werte.values()))


# ---------------------------------------------------------------- the sensors


@dataclass(frozen=True)
class Sensorwert:
    """One sensor's reading and what it earns.

    `stufe` is None where the sensor carries no reading OR no bound; the two
    are told apart by `wert`, and neither may quietly count as green.
    """

    name: str
    wert: float | None
    soll: float | None
    gruen: float | None
    gelb: float | None
    stufe: int | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _hoechstens(wert: float | None, gruen: float, gelb: float) -> int | None:
    """Grade a sensor where SMALLER is better."""
    if wert is None:
        return None
    if wert <= gruen:
        return 0
    return 1 if wert <= gelb else 2


def _mindestens(wert: float | None, gruen: float, gelb: float) -> int | None:
    """Grade a sensor where LARGER is better."""
    if wert is None:
        return None
    if wert >= gruen:
        return 0
    return 1 if wert >= gelb else 2


def _absetzer(wert: float | None, soll: float, gelb: int) -> int | None:
    """Grade the run count against the runs the script joins the word into."""
    if wert is None:
        return None
    abweichung = abs(wert - soll)
    if abweichung == 0:
        return 0
    return 1 if abweichung <= gelb else 2


def sensoren_of(pfad: Mapping[str, Any], schwellen: Schwellen) -> list[Sensorwert]:
    """The five sensors of one word box, in `SENSOR_ORDER`.

    The word for the Absetzer-Soll comes from the entry itself: `check_paths`
    has already held it against the printed box and against the frozen plan,
    so it is the one field of a stored path that cannot disagree with the
    strip. A path without a word falls back to one run, as `befund` does.
    """
    block = _sensorblock(pfad)
    wort = pfad.get("word")
    soll = float(body_runs_expected(wort)) if isinstance(wort, str) and wort else 1.0
    absetzer = _zahl(block.get(KEY_ABSETZER))
    # The Bahn's runs, not its lifts: `n` lifts cut a path into `n + 1` runs,
    # and the Soll counts runs. Comparing lifts against runs would read every
    # correctly followed one-run word as one run short.
    zuege = None if absetzer is None else absetzer + 1
    unbesucht = _zahl(block.get(KEY_UNBESUCHT))
    exkursion = _zahl(block.get(KEY_EXKURSION))
    aiou = _zahl(block.get(KEY_AIOU))
    spruenge = _zahl(block.get(KEY_SPRUENGE))
    haken = _zahl(block.get(KEY_HAKEN))
    return [
        Sensorwert(
            name=SENSOR_ABSETZER,
            wert=zuege,
            soll=soll,
            gruen=None,
            gelb=float(schwellen.absetzer_gelb),
            stufe=_absetzer(zuege, soll, schwellen.absetzer_gelb),
        ),
        Sensorwert(
            name=SENSOR_UNBESUCHT,
            wert=unbesucht,
            soll=None,
            gruen=schwellen.unbesucht_gruen,
            gelb=schwellen.unbesucht_gelb,
            stufe=_hoechstens(unbesucht, schwellen.unbesucht_gruen, schwellen.unbesucht_gelb),
        ),
        Sensorwert(
            name=SENSOR_EXKURSION,
            wert=exkursion,
            soll=None,
            gruen=schwellen.exkursion_gruen_xh,
            gelb=schwellen.exkursion_gelb_xh,
            stufe=_hoechstens(exkursion, schwellen.exkursion_gruen_xh, schwellen.exkursion_gelb_xh),
        ),
        Sensorwert(
            name=SENSOR_AIOU,
            wert=aiou,
            soll=None,
            gruen=schwellen.aiou_gruen,
            gelb=schwellen.aiou_gelb,
            stufe=_mindestens(aiou, schwellen.aiou_gruen, schwellen.aiou_gelb),
        ),
        # Read and shown, never graded — see the module docstring. The reading
        # is the sum: a strand change and a retrace turn are the same class of
        # decoder event, and no bound distinguishes them today. A sum needs
        # BOTH halves, though: filling a missing one in with 0 would print the
        # measured half as if the other had been counted and found empty —
        # exactly the 0-vs-missing collapse `Rohzahlen` exists to prevent.
        Sensorwert(
            name=SENSOR_SPRUENGE,
            wert=None if spruenge is None or haken is None else spruenge + haken,
            soll=None,
            gruen=None,
            gelb=None,
            stufe=None,
        ),
    ]


# ---------------------------------------------------------------- the verdict


@dataclass(frozen=True)
class Tintentreue:
    """One word box's traffic light, derived on read.

    `stufe` is one of `STUFEN` or `STUFE_UNGEMESSEN`; `grund` is the naming
    sensor where there is one and the reason for the grey state otherwise —
    always a sentence a surface can print without a lookup table.
    """

    stufe: str
    grund: str
    gemessen: bool
    sensor: str | None
    sensoren: list[Sensorwert]
    format: int
    schwellen_stand: str
    vorlaeufig: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _grau(
    grund: str, *, sensoren: list[Sensorwert], pfade_format: int, schwellen: Schwellen, sensor: str | None = None
) -> Tintentreue:
    return Tintentreue(
        stufe=STUFE_UNGEMESSEN,
        grund=grund,
        gemessen=False,
        sensor=sensor,
        sensoren=sensoren,
        format=pfade_format,
        schwellen_stand=schwellen.stand,
        vorlaeufig=schwellen.vorlaeufig,
    )


def tintentreue(pfad: Mapping[str, Any] | None, *, hand: str, pfade_format: int, maske_n: int | None) -> Tintentreue:
    """Whether this word box's Bahn follows its ink.

    `pfad` is one stored entry of `eigenhand_strips.pfade` (None where the box
    carries none), `pfade_format` the ROW's own marker
    (`eigenhand_strips.pfade_format`, migration 0032) and `maske_n` the size of
    the Fleckenmaske the Fassung carries TODAY, against which the entry's own
    `flecken_n` is held. `maske_n` has no default on purpose: `None` disables
    the „Maske geändert" state, so a caller that simply forgot it would hand
    out a GREEN box for an entry followed over other ink — the one wrong green
    that costs the author nothing and therefore never gets found. Not knowing
    today's mask is a decision, and it is written as `maske_n=None`.

    The grey states are ordered by what the reader should DO about them, not
    by how they were found:

    1. `kein Eintrag` — nothing to judge. Four causes produce it today (`--box`
       not chosen · no Bogen geometry · unauthored glyphs · the follower gave
       up), and they are indistinguishable until the Skip entries of
       PFAD_FORMAT 2 are written, so exactly ONE grey state may claim them
       (`admin-redesign.md` §6.3, correction of 2026-09-20).
    2. `von Hand gezeichnet` — an UNMEASURED authored Bahn: „von Hand" is a
       Herkunft and never a colour, and there is nothing to grade until the
       tool has run over it. What greys the box is therefore the missing
       measurement, NOT the origin: `verfahren` stays `authored` for good —
       `pfad.displaced_authored` depends on exactly that — so keying the grey
       on the Herkunft would grey a re-traced box forever, and the author
       would get no feedback on the trace he just made by hand (V21: „sie
       tragen dann dieselbe Ampel; bis dahin zwei Zähler").
    3. `Maske geändert` — the entry was followed under a Fleckenmaske of a
       different size, so its numbers describe other ink than the picture now
       shows. Taken over from the free-standing warning chip the SPA computes
       today (`app/src/sections/admin/eigenhand/PfadCaption.tsx`), which the
       list PR removes so there is one statement rather than two.
    4. `Format 1 — unvollständig gemessen` — followed before two of the four
       graded sensors existed.
    5. `unvollständig gemessen` — the row claims a complete format and a
       graded sensor is missing anyway. Under-claiming on purpose: the missing
       one could have been the worst.
    """
    schwellen = schwellen_of(hand)
    if pfad is None:
        return _grau(GRUND_KEIN_EINTRAG, sensoren=[], pfade_format=pfade_format, schwellen=schwellen)
    sensoren = sensoren_of(pfad, schwellen)
    if is_authored(pfad) and not rohzahlen(pfad).gemessen:
        return _grau(GRUND_VON_HAND, sensoren=sensoren, pfade_format=pfade_format, schwellen=schwellen)
    flecken_n = pfad.get("flecken_n")
    if isinstance(flecken_n, int) and not isinstance(flecken_n, bool) and maske_n is not None and flecken_n != maske_n:
        return _grau(GRUND_MASKE, sensoren=sensoren, pfade_format=pfade_format, schwellen=schwellen)
    if pfade_format < VOLLSTAENDIG_AB_FORMAT:
        grund = GRUND_FORMAT.format(format=pfade_format)
        return _grau(grund, sensoren=sensoren, pfade_format=pfade_format, schwellen=schwellen)
    bewertet = [wert for wert in sensoren if wert.name in SENSOREN_MIT_SCHWELLE]
    fehlend = [wert.name for wert in bewertet if wert.stufe is None]
    if fehlend:
        return _grau(
            GRUND_UNVOLLSTAENDIG,
            sensoren=sensoren,
            pfade_format=pfade_format,
            schwellen=schwellen,
            sensor=min(fehlend, key=SENSOR_ORDER.index),
        )
    findings = [(wert.stufe, wert.name) for wert in bewertet if wert.stufe]
    severity = max((stufe for stufe, _ in findings), default=0)
    sensor = min((name for stufe, name in findings if stufe == severity), key=SENSOR_ORDER.index) if findings else None
    return Tintentreue(
        stufe=STUFEN[severity],
        grund=sensor or GRUND_NICHTS,
        gemessen=True,
        sensor=sensor,
        sensoren=sensoren,
        format=pfade_format,
        schwellen_stand=schwellen.stand,
        vorlaeufig=schwellen.vorlaeufig,
    )


@dataclass(frozen=True)
class Kastenzaehler:
    """How a FASSUNG reports its boxes: counted, never coloured.

    Author decision E of 2026-09-20. A colour here would be a second verdict
    beside `befund.vorschlag` over the same Fassung, with its own vocabulary —
    and „sauber geschrieben, schlecht gefolgt" is the common case, not the
    exception.
    """

    kaesten: int
    gemessen: int
    folgt: int
    # Hand-drawn AND not yet measured — V21's „j von Hand (ungemessen)" half of
    # the two counters. A re-traced Bahn the tool HAS measured counts in
    # `gemessen` like any other; its origin stays readable off `verfahren`,
    # which is where the SPA's Herkunfts-Chip takes it from.
    von_hand: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def zaehler(urteile: Sequence[Tintentreue]) -> Kastenzaehler:
    """„3 von 4 Kästen folgen" — over the boxes that were measured at all."""
    return Kastenzaehler(
        kaesten=len(urteile),
        gemessen=sum(1 for urteil in urteile if urteil.gemessen),
        folgt=sum(1 for urteil in urteile if urteil.stufe == STUFEN[0]),
        von_hand=sum(1 for urteil in urteile if urteil.grund == GRUND_VON_HAND),
    )
