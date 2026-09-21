"""The Wortvorrat — the committed, curated word pool of the Eigenhand-Erfassung.

Real words only, no drill syllables: the goal is writing real text, old and
modern, mainly German with a tagged English share (owner decisions,
docs/proposals/eigenhand-erfassung.md). Curation layers, merged by
``pool_entries()`` with their provenance tags:

* ``mvp9``        — the architektur.md §9 MVP word set (incl. ``denen``)
* ``bench-abb19`` — the 63-word bench set of the 1922 plates (50 distinct);
                    doubles as the later H5 bridge to the historical hand
* ``quizbank``    — the full quiz word bank, imported mechanically from
                    ``tools.quizgen.corpus`` (own curation, reused verbatim;
                    era/fugen/note carried over, distractors dropped)
* ``rare-join``   — words hunted specifically for joins the natural sample
                    misses (compounds incl. Fugen words, loanwords, English);
                    candidates come from ``python -m tools.eigenhand.gaps``,
                    the selection stays a human act
* ``haeufig``     — German function/short words the quiz bank (a reading-quiz
                    curation) skips, found by hunting JOIN gaps: du, jetzt,
                    schon, über …
* ``alltag``      — the Grundwortschatz the join hunt could not find, because
                    a short frequent word carries nothing rare: ich, ist,
                    nicht, in, auf and the rest of what every sentence is made
                    of. Grouped by word class, each group with a floor the
                    builder owes it (``alltag_floors``)
* ``english``     — a common-English layer beyond the rare-join hunting, so
                    modern mixed-language text stays writable (owner goal);
                    all ``lang: en``, filterable
* ``zeichen``     — digits and punctuation in real text use (years, a date,
                    a price, signs at words); detached glyphs, so they carry
                    glyph-position Soll but no joins
* ``pin``         — words the author wants written FIRST for their own sake,
                    not for their coverage (``PINNED_FIRST``); they skip the
                    quota-driven fill via ``tools.eigenhand.pool pin``. Most of
                    them reach the pool through another layer already — the
                    tag then says "also wanted early", and the earlier layer
                    keeps the gloss

Frequency LISTS are never committed (quiz-wortbank.md §4 — protectable
databases, often NC); this pool is an own, merely *informed* curation and
therefore own expression under the repo licence. The consulted corpora are
documented in ``data/corpora/*/SOURCE.md``.

The pool is TRAINING data, not a measurement set: it grows in waves, and no
bench headline ever reads from it (frozen-reference doctrine untouched).
"""

from __future__ import annotations

import re
from typing import TypedDict

from tools.quizgen.corpus import ENTRIES as _QUIZ_ENTRIES
from tools.tracebench.sets import TRACEBENCH_DEV_IDS


class PoolEntry(TypedDict, total=False):
    word: str
    lang: str  # 'de' | 'en' (default 'de')
    era: str  # 'modern' | 'historic' (default 'modern')
    fugen: str  # morpheme marker when an inner s must render round ("Donners|tag")
    note: str  # gloss for historic words / why a rare-join word earns its place
    tags: list[str]  # provenance tags, see module docstring


# --- architektur.md §9: the MVP word set plus the generalisation word --------
_MVP9_WORDS = ["lesen", "das", "den", "lese", "lasen", "als", "dann", "denen"]

# --- the 63 Abb.-19 bench words (50 distinct), verbatim incl. period forms ---
# ``daß`` (pre-1996 orthography), ``han`` (elided ``haben`` of the song) and the
# capitalised ``Galoppieren`` stay exactly as the plate writes them.
_BENCH_ABB19_WORDS = [
    "Einen",
    "Feinde",
    "Galoppieren",
    "Gaul",
    "Gewehr",
    "Kugel",
    "Pulver",
    "Seiten",
    "Silber",
    "Soldaten",
    "Sporn",
    "Sprünge",
    "Säbel",
    "Wer",
    "Zaum",
    "Zorn",
    "Zügel",
    "an",
    "auch",
    "das",
    "daß",
    "der",
    "die",
    "ein",
    "einen",
    "einer",
    "er",
    "fechten",
    "haben",
    "han",
    "im",
    "kann",
    "laden",
    "linken",
    "macht",
    "mit",
    "muß",
    "regieren",
    "scharfen",
    "schießen",
    "schwer",
    "streiten",
    "und",
    "unter",
    "von",
    "wenn",
    "will",
    "zu",
    "zum",
    "zwei",
]

_BENCH_NOTES: dict[str, PoolEntry] = {
    "daß": {"era": "historic", "note": "alte Schreibung von dass (vor 1996)"},
    "muß": {"era": "historic", "note": "alte Schreibung von muss (vor 1996)"},
    "han": {"era": "historic", "note": "verkürztes haben (Liedform der Vorlage)"},
}

# --- rare-join hunting: real words carrying joins the natural sample misses --
# Every entry names its target joins in ``note`` so the curation stays
# auditable; candidates were surfaced by ``tools.eigenhand.gaps`` over the
# consulted corpora, the selection is hand-checked real vocabulary.
_RARE_JOIN_ENTRIES: list[PoolEntry] = []  # extended below, kept separate per language


_RARE_JOIN_DE: list[PoolEntry] = [
    {"word": "Erbse", "note": "joins b>longs, longs>e"},
    {"word": "Absicht", "note": "joins b>longs, longs>i"},
    {"word": "obwohl", "note": "join b>w"},
    {"word": "abzüglich", "note": "join b>z"},
    {"word": "Herbst", "note": "joins b>longst, r>b"},
    {"word": "hübsch", "note": "join b>longs"},
    {"word": "Radfahrer", "note": "join d>f"},
    {"word": "Handzettel", "note": "join d>z"},
    {"word": "Grundzug", "note": "join d>z"},
    {"word": "Erdkunde", "note": "join d>k"},
    {"word": "Landkarte", "note": "join d>k"},
    {"word": "Feldpost", "note": "joins d>p, o>longst"},
    {"word": "Wildpark", "note": "join d>p"},
    {"word": "Nordpol", "note": "join d>p"},
    {"word": "Handtuch", "note": "join d>t"},
    {"word": "Stadtplan", "note": "joins d>t, t>p"},
    {"word": "Erdöl", "note": "join d>oe"},
    {"word": "Fremdwort", "note": "join d>w"},
    {"word": "Erdbeere", "note": "join d>b"},
    {"word": "würdig", "note": "join d>i"},
    {"word": "Widmung", "note": "join d>m"},
    {"word": "Erdnuss", "note": "join d>n"},
    {"word": "Mondschein", "note": "join d>longs"},
    {"word": "vorpreschen", "note": "join r>p"},
    {"word": "Kurpfalz", "note": "joins r>p, f>a"},
    {"word": "Herzog", "note": "join r>z"},
    {"word": "Arzt", "note": "joins r>z, z>t"},
    {"word": "Warze", "note": "join r>z"},
    {"word": "Erbe", "note": "join r>b"},
    {"word": "Farbe", "note": "join r>b"},
    {"word": "Marxismus", "note": "joins r>x, x>i"},
    {"word": "Sarg", "note": "join r>g"},
    {"word": "Berg", "note": "join r>g"},
    {"word": "Salbe", "note": "join l>b"},
    {"word": "halb", "note": "join l>b, b-final"},
    {"word": "Kalb", "note": "join l>b"},
    {"word": "Volk", "note": "join l>k"},
    {"word": "welk", "note": "join l>k"},
    {"word": "Kelch", "note": "join l>ch"},
    {"word": "Milch", "note": "join l>ch"},
    {"word": "Wolf", "note": "join l>f"},
    {"word": "Hilfe", "note": "join l>f"},
    {"word": "Pilz", "note": "join l>z"},
    {"word": "Holz", "note": "join l>z"},
    {"word": "Bild", "note": "join l>d"},
    {"word": "Geld", "note": "join l>d"},
    {"word": "Vulkan", "note": "joins u>l, l>k"},
    {"word": "Quarz", "note": "joins qu>a, r>z"},
    {"word": "quengeln", "note": "join qu>e"},
    {"word": "Qualle", "note": "join qu>a"},
    {"word": "Xylophon", "note": "joins X>y, y>l — seltener Versal"},
    {"word": "Hexe", "note": "joins e>x, x>e"},
    {"word": "Taxi", "note": "joins a>x, x>i"},
    {"word": "boxen", "note": "joins o>x, x>e"},
    {"word": "Ochse", "note": "joins ch>longs — ch vor s"},
    {"word": "wachsen", "note": "join ch>longs"},
    {"word": "Häcksel", "note": "joins ck>longs, longs>e"},
    {"word": "Yacht", "note": "joins Y>a, a>ch"},
    {"word": "Physik", "note": "joins h>y, y>longs"},
    {"word": "Rhythmus", "note": "joins y>t, t>h"},
    {"word": "Pyjama", "note": "joins y>j, j>a"},
    {"word": "Kajak", "note": "joins a>j, j>a"},
    {"word": "Injektion", "note": "joins n>j, j>e"},
    {"word": "Objekt", "note": "joins b>j, j>e"},
    {"word": "Subjekt", "note": "joins b>j"},
    {"word": "Pizza", "note": "joins i>z, z>z — z-Doppel ohne tz-Ligatur"},
    {"word": "Skizze", "note": "joins z>z, k>i"},
    {"word": "Puzzle", "lang": "en", "note": "Lehnwort; joins z>z, z>l"},
    {"word": "Mokka", "note": "joins k>k — kk ohne ck-Ligatur"},
    {"word": "Sakko", "note": "join k>k"},
    {"word": "Vase", "note": "joins V>a, longs>e"},
    {"word": "Vogel", "note": "join V>o"},
    {"word": "Klavier", "note": "joins v>i, a>v"},
    {"word": "Pulver", "note": "joins v>e, l>v"},
    {"word": "Sklave", "note": "joins k>l, v>e"},
    {"word": "Löwe", "note": "joins oe>w, w>e"},
    {"word": "Möwe", "note": "join oe>w"},
    {"word": "ewig", "note": "joins e>w, w>i"},
    {"word": "Umzug", "note": "join m>z"},
    {"word": "Amtszeit", "fugen": "Amts|zeit", "note": "joins t>s (Fugen-s), s>z"},
    {"word": "Bahnhof", "note": "join n>h"},
    {"word": "Anzug", "note": "join n>z"},
    {"word": "Konzert", "note": "join n>z"},
    {"word": "Signal", "note": "join g>n"},
    {"word": "Magnet", "note": "join g>n"},
    {"word": "Dogma", "note": "join g>m"},
    {"word": "möglich", "note": "join g>l"},
    {"word": "Vogtland", "note": "joins g>t, t>l"},
    {"word": "Jagd", "note": "joins g>d, d-final"},
    {"word": "Magd", "note": "join g>d"},
    {"word": "Hemd", "note": "join m>d"},
    {"word": "fremd", "note": "join m>d"},
    {"word": "Amt", "note": "join m>t"},
    {"word": "Leumund", "note": "joins u>m, m>u"},
    {"word": "Obst", "note": "joins b>longst — b vor st"},
    {"word": "Papst", "note": "join p>longst"},
    {"word": "Haupt", "note": "joins u>p, p>t"},
    {"word": "Rezept", "note": "joins p>t, z>e"},
    {"word": "Adjektiv", "note": "joins d>j, v-final"},
    {"word": "Efeu", "note": "joins f>e, e>u"},
    {"word": "Ufer", "note": "join f>e"},
    {"word": "Ofen", "note": "join f>e"},
    {"word": "Sofa", "note": "join f>a"},
    {"word": "Pfote", "note": "joins p>f, f>o"},
    {"word": "Apfel", "note": "joins p>f, f>e"},
    {"word": "Kupfer", "note": "join p>f"},
    {"word": "Föhn", "note": "joins oe>h, h>n"},
    {"word": "Lärm", "note": "joins ae>r, r>m"},
    {"word": "Bäcker", "note": "joins ae>ck, ck>e"},
    {"word": "Mühle", "note": "joins ue>h, h>l"},
    {"word": "Süden", "note": "join ue>d"},
    {"word": "Öfen", "note": "joins Oe>f — Versal-Umlaut"},
    {"word": "Übung", "note": "joins Ue>b — Versal-Umlaut"},
    {"word": "Ähre", "note": "joins Ae>h — Versal-Umlaut", "era": "modern"},
    {"word": "Autobus", "note": "joins A>u, b>u, s-final"},
    {"word": "Europa", "note": "joins E>u, o>p"},
    {"word": "Quelle", "note": "join Q-Versal via qu-Ligatur: qu>e"},
]

_RARE_JOIN_EN: list[PoolEntry] = [
    {"word": "jazz", "lang": "en", "note": "joins a>z, z>z"},
    {"word": "quiz", "lang": "en", "note": "joins qu>i, z-final"},
    {"word": "sky", "lang": "en", "note": "joins k>y, y-final"},
    {"word": "style", "lang": "en", "note": "joins t>y, y>l"},
    {"word": "yellow", "lang": "en", "note": "joins y>e, w-final"},
    {"word": "young", "lang": "en", "note": "joins y>o, n>g"},
    {"word": "system", "lang": "en", "note": "joins y>longs, longst via st"},
    {"word": "rhythm", "lang": "en", "note": "joins y>t, h>m, m-final"},
    {"word": "oxygen", "lang": "en", "note": "joins x>y, y>g"},
    {"word": "pixel", "lang": "en", "note": "joins i>x, x>e"},
    {"word": "expect", "lang": "en", "note": "joins x>p, c>t"},
    {"word": "subway", "lang": "en", "note": "joins b>w, a>y"},
    {"word": "cowboy", "lang": "en", "note": "joins w>b, o>y"},
    {"word": "vodka", "lang": "en", "note": "joins d>k, v>o"},
    {"word": "update", "lang": "en", "note": "joins p>d, u>p"},
    {"word": "headline", "lang": "en", "note": "joins d>l, a>d"},
    {"word": "midnight", "lang": "en", "note": "joins d>n, g>h"},
    {"word": "welcome", "lang": "en", "note": "joins l>c, c>o"},
    {"word": "obvious", "lang": "en", "note": "joins b>v, v>i"},
    {"word": "awkward", "lang": "en", "note": "joins w>k, k>w"},
    {"word": "Iraq", "lang": "en", "note": "bare q without u (blocks the qu ligature), q word-final"},
    {"word": "Niqab", "note": "bare q medial — Duden-listed loanword; second real q carrier"},
    {"word": "Iraqi", "lang": "en", "note": "bare q medial before i"},
]

_RARE_JOIN_ENTRIES = _RARE_JOIN_DE + _RARE_JOIN_EN

# --- high-frequency German the quiz bank skips (gaps.py finding, wave 0) -----
_COMMON_DE_WORDS = [
    "du",
    "ihr",
    "ihn",
    "ihm",
    "ihnen",
    "uns",
    "dir",
    "mir",
    "man",
    "wer",
    "was",
    "wo",
    "jetzt",
    "schon",
    "also",
    "durch",
    "über",
    "überall",
    "überhaupt",
    "übrigens",
    "hast",
    "habt",
    "gibt",
    "bleibt",
    "kommt",
    "geht",
    "steht",
    "lässt",
    "heißt",
    "musst",
    "musste",
    "wusste",
    "konnte",
    "sollte",
    "wollte",
    "dachte",
    "brachte",
    "letzte",
    "letzten",
    "nächste",
    "abends",
    "morgens",
    "damals",
    "deshalb",
    "trotzdem",
    "vielleicht",
    "natürlich",
    "wirklich",
    "ziemlich",
    "plötzlich",
    "verletzt",
    "jemand",
    "niemand",
    "etwas",
    "nichts",
    "alles",
    "beide",
    "genug",
    "hätte",
    "hätten",
    "wäre",
    "wären",
    "während",
    "müssen",
    "müsste",
    "müde",
    "Schlüssel",
    "Hände",
    "hält",
    "erwartet",
    "unterwegs",
    "los",
    "willst",
    "sollst",
    "spielst",
    "verrückt",
    "geschickt",
    "versteckt",
    "gefällt",
    "gefährlich",
    "fährt",
    "Gefängnis",
    # capital-C carriers — no other pool word starts with C (progression
    # finding 2026-08-22); the capital blocks the ch ligature, so these
    # also cover the C>h and C>o joins.
    "Computer",
    "Chef",
    "Camping",
]

# --- Grundwortschatz: the words everyday writing is actually made of --------
# Why a second German layer beside `haeufig`: that one came out of a `gaps`
# run and hunted JOINS, so it caught `du, jetzt, schon, über` and missed
# `ich, ist, nicht, in, auf` — a gap the author found the only way it can be
# found, by writing the first sheets and noticing they are all long compounds
# (2026-09-21). Measured before the repair: of the 50 most frequent German
# words 28 were in the pool, 13 were planned at all, and exactly ONE stood in
# the first 40 strips.
#
# Own curation, not a copied list (quiz-wortbank.md §4 — frequency lists are
# never committed): the consulted corpus is OpenSubtitles-derived and skews
# to spoken dialogue, so its top is full of `okay`, `hey`, `sir` and swearing
# that a Kurrent training sheet has no use for. What stands here is grouped by
# word class, filtered by hand, and topped up with what letters need and a
# film corpus undercounts (`Brief`, `Woche`, `Grund`, `Antwort`). Each group
# carries its own floor: how often the plan must have asked for the word
# before the builder stops owing it (`ALLTAG_FLOORS`).

# The closed classes and the auxiliaries — the words that recur in every
# single sentence, and therefore the ones worth the highest floor.
_ALLTAG_KERN = [
    # personal and possessive pronouns
    "ich",
    "du",
    "er",
    "sie",
    "es",
    "wir",
    "man",
    "mich",
    "dich",
    "sich",
    "euch",
    "ihm",
    "ihn",
    "mir",
    "mein",
    "meine",
    "dein",
    "deine",
    "sein",
    "seine",
    "unsere",
    # articles and determiners
    "der",
    "die",
    "das",
    "den",
    "dem",
    "des",
    "ein",
    "eine",
    "einen",
    "einem",
    "einer",
    "kein",
    "keine",
    "keinen",
    "dieser",
    "diese",
    "dieses",
    "alle",
    "andere",
    "jeder",
    "viele",
    # conjunctions and subjunctions
    "und",
    "oder",
    "aber",
    "denn",
    "wenn",
    "weil",
    "dass",
    "als",
    "ob",
    "damit",
    "obwohl",
    "sondern",
    "bevor",
    "bis",
    "sobald",
    # question words
    "wie",
    "wo",
    "wann",
    "welche",
    # prepositions, including the contracted forms that carry their own joins
    "in",
    "an",
    "auf",
    "aus",
    "bei",
    "mit",
    "nach",
    "von",
    "zu",
    "um",
    "vor",
    "unter",
    "für",
    "ohne",
    "gegen",
    "zwischen",
    "am",
    "im",
    "ins",
    "beim",
    "zum",
    "zur",
    "vom",
    # negation, degree, quantity
    "nicht",
    "nie",
    "mehr",
    "viel",
    "wenig",
    "sehr",
    "fast",
    "immer",
    # sein · haben · werden
    "ist",
    "sind",
    "war",
    "waren",
    "bin",
    "bist",
    "seid",
    "hat",
    "habe",
    "hast",
    "hatte",
    "hatten",
    "wird",
    "werden",
    "wurde",
    "wurden",
    "worden",
    # the modals, in the forms a letter uses
    "kann",
    "kannst",
    "könnte",
    "muss",
    "soll",
    "sollen",
    "will",
    "wollen",
    "darf",
    "dürfen",
    "mag",
    "möchte",
]

# The everyday full verbs. Infinitive, third person, past — three forms per
# verb is what makes the joins vary without turning the layer into a
# conjugation drill (§10: no drill syllables, and this stays real words).
_ALLTAG_FORMEN = [
    "gehen",
    "geht",
    "ging",
    "kommen",
    "kam",
    "gekommen",
    "machen",
    "macht",
    "machte",
    "gemacht",
    "sagen",
    "sagt",
    "sagte",
    "gesagt",
    "sehen",
    "sieht",
    "sah",
    "gesehen",
    "stehen",
    "stand",
    "geben",
    "gab",
    "gegeben",
    "nehmen",
    "nimmt",
    "nahm",
    "finden",
    "findet",
    "fand",
    "gefunden",
    "bleiben",
    "blieb",
    "geblieben",
    "schreiben",
    "schreibt",
    "schrieb",
    "geschrieben",
    "liest",
    "las",
    "gelesen",
    "denken",
    "denkt",
    "gedacht",
    "glauben",
    "glaubt",
    "glaubte",
    "wissen",
    "weiß",
    "heißen",
    "hieß",
    "fragen",
    "fragt",
    "fragte",
    "gefragt",
    "hören",
    "hört",
    "arbeiten",
    "arbeitet",
    "gearbeitet",
    "wohnen",
    "wohnt",
    "lieben",
    "liebt",
    "geliebt",
    "brauchen",
    "braucht",
    "gebraucht",
    "bekommen",
    "bekommt",
    "bringen",
    "bringt",
    "gebracht",
    "halten",
    "hielt",
    "ließ",
    "fahren",
    "fuhr",
    "gefahren",
    "laufen",
    "läuft",
    "lief",
    "liegen",
    "liegt",
    "lag",
    "sitzen",
    "sitzt",
    "saß",
    "essen",
    "isst",
    "gegessen",
    "trinken",
    "trinkt",
    "trank",
    "schläft",
    "schlief",
    "helfen",
    "hilft",
    "geholfen",
    "spielen",
    "spielt",
    "gespielt",
    "lernen",
    "lernt",
    "gelernt",
    "leben",
    "lebt",
    "gelebt",
    "warten",
    "wartet",
    "gewartet",
    "suchen",
    "sucht",
    "gesucht",
    "zeigen",
    "zeigt",
    "gezeigt",
]

# The everyday nouns, adjectives and adverbs a letter is written out of. The
# nouns carry their capital because German spells them that way — unlike the
# sentence openers below, which are the same word twice, cased two ways, and
# are deliberately two pool entries (see `pool_entries`).
_ALLTAG_SACHEN = [
    "ja",
    "nein",
    "bitte",
    "danke",
    "gut",
    "besser",
    "gern",
    "gleich",
    "genau",
    "richtig",
    "falsch",
    "wieder",
    "oft",
    "bald",
    "lange",
    "kurz",
    "weit",
    "spät",
    "früher",
    "heute",
    "gestern",
    "hier",
    "dort",
    "dann",
    "eben",
    "zusammen",
    "groß",
    "klein",
    "alt",
    "neu",
    "jung",
    "schön",
    "warm",
    "kalt",
    "Brief",
    "Jahr",
    "Jahre",
    "Zeit",
    "Tag",
    "Tage",
    "Nacht",
    "Abend",
    "Woche",
    "Stunde",
    "Haus",
    "Mann",
    "Frau",
    "Kind",
    "Kinder",
    "Vater",
    "Mutter",
    "Bruder",
    "Schwester",
    "Freund",
    "Freunde",
    "Arbeit",
    "Geld",
    "Leute",
    "Welt",
    "Stadt",
    "Land",
    "Dorf",
    "Wort",
    "Worte",
    "Name",
    "Hand",
    "Herz",
    "Weg",
    "Ort",
    "Sache",
    "Frage",
    "Antwort",
    "Grund",
    "Teil",
    "Buch",
    "Schule",
    "Kirche",
    "Wetter",
    "Garten",
    "Mensch",
    "Menschen",
    "Leben",
    "Sonne",
    "Regen",
]

# Sentence openers: the same function words with the capital they get at the
# start of a sentence. Case-distinct pool entries on purpose — `Ich` and `ich`
# shape to different glyph sequences, and a letter begins with the capital one
# in every second line.
_ALLTAG_SATZANFANG = [
    "Ich",
    "Du",
    "Er",
    "Sie",
    "Es",
    "Wir",
    "Der",
    "Die",
    "Das",
    "Ein",
    "Eine",
    "Und",
    "Aber",
    "Wenn",
    "Als",
    "Nun",
    "So",
    "Da",
    "Dann",
    "Heute",
    "Gestern",
    "Morgen",
    "Ja",
    "Nein",
    "Bitte",
    "Danke",
]

# word → how often the whole plan must have asked for it. Same shape as the
# per-glyph floor `GLYPH_MIN_PLANNED` (owner, 2026-08-23: "a q only once is
# unacceptable") and the same kind of promise: a guarantee, not a preference.
# The Kern words get more because they come back in every sentence and their
# joins are what fluent writing is made of; the builder spends only a bounded
# share of each wave on them (`pool.ALLTAG_WAVE_SHARE`), so the floor fills
# over several waves instead of starving the even build-out.
_ALLTAG_GROUPS: list[tuple[list[str], int]] = [
    (_ALLTAG_KERN, 3),
    (_ALLTAG_FORMEN, 2),
    (_ALLTAG_SACHEN, 2),
    (_ALLTAG_SATZANFANG, 2),
]

# Curation order, deduplicated: the everyday wave writes them in this order,
# so a Bogen's row stays a run of related words rather than a random mix.
ALLTAG_WORDS: list[str] = list(dict.fromkeys(word for words, _ in _ALLTAG_GROUPS for word in words))


def alltag_floors() -> dict[str, int]:
    """Grundwortschatz word → the minimum number of planned uses it is owed.

    A word listed in two groups keeps the HIGHER floor: the groups say what a
    word is for, and being needed twice over is not a reason to ask for it
    less often.
    """
    floors: dict[str, int] = {}
    for words, floor in _ALLTAG_GROUPS:
        for word in words:
            floors[word] = max(floors.get(word, 0), floor)
    return floors


# --- common English beyond the rare-join hunting (lang: en, filterable) ------
_COMMON_EN_WORDS = [
    "what",
    "who",
    "when",
    "why",
    "where",
    "which",
    "how",
    "this",
    "that",
    "then",
    "can",
    "could",
    "would",
    "should",
    "because",
    "about",
    "after",
    "before",
    "come",
    "came",
    "call",
    "good",
    "look",
    "took",
    "make",
    "made",
    "know",
    "knew",
    "still",
    "stay",
    "start",
    "stand",
    "understand",
    "last",
    "least",
    "past",
    "over",
    "love",
    "move",
    "people",
    "someone",
    "anyone",
    "nice",
    "place",
    "once",
    "since",
    "city",
    "police",
    "music",
    "office",
    "close",
    "clear",
    "clean",
    "crazy",
    "secret",
    "story",
    "history",
    "stop",
    "help",
    "keep",
    "deep",
    "down",
    "town",
    "own",
    "job",
    "join",
    "just",
    "guys",
    "days",
    "always",
    "says",
    "does",
    "goes",
    "question",
    "pretty",
    "party",
    "change",
    "check",
    "chance",
    "children",
    "drink",
    "drive",
    "dream",
    "ready",
    "already",
    "somebody",
    "family",
    "money",
    "very",
    "sorry",
    "every",
    "really",
    "only",
    "my",
    "myself",
    "new",
    "news",
    "newspaper",
    "year",
    "years",
    "world",
    "work",
    "right",
    "night",
    "beautiful",
    "full",
    "fun",
    "husband",
    "hurt",
    "hurry",
    "excuse",
    "difficult",
    "remember",
    "number",
    "things",
    "feelings",
    "ship",
    "trip",
    "sleep",
    "slow",
    "trying",
    "saying",
    "playing",
    "road",
    "boat",
    "board",
    "wedding",
    "middle",
    "watch",
    "catch",
    "kitchen",
    "answer",
    "sweet",
    "swear",
    "doctor",
    "local",
    "building",
    "guilty",
    "build",
    "by",
    "baby",
    "goodbye",
    "cut",
    "scared",
    "scene",
    "escape",
    "snow",
    "special",
    "immediately",
    "service",
    "nervous",
    "maybe",
    "everybody",
    "wrong",
    "write",
    "wrote",
    "perhaps",
]

# --- digits and punctuation in REAL text use (owner, 2026-08-22: digits and
# signs are needed in the end too) — never fantasy sequences: years,
# a date, a price, signs as they appear in letters and newspapers. Digits and
# punctuation are detached glyphs (no joins), so they carry glyph-position
# Soll only. Together the number entries cover every digit 0-9.
_ZEICHEN_ENTRIES: list[PoolEntry] = [
    {"word": "1866", "note": "Jahreszahl der Loth-Tafel; Ziffern 1 8 6"},
    {"word": "1922", "note": "Jahreszahl der Sütterlin-Platten; Ziffern 1 9 2"},
    {"word": "2026", "note": "Jahreszahl; Ziffern 2 0 6"},
    {"word": "47", "note": "Ziffern 4 7"},
    {"word": "3,50", "note": "Preisangabe; Komma zwischen Ziffern, Ziffern 3 5 0"},
    {"word": "31.12.1900", "note": "Datum; Punkt zwischen Ziffern", "era": "historic"},
    {"word": "§12", "note": "Paragraphenzeichen mit Zahl"},
    {"word": "(1922)", "note": "Klammern um eine Jahreszahl"},
    {"word": "ja!", "note": "Ausrufezeichen am Wort"},
    {"word": "nein?", "note": "Fragezeichen am Wort"},
    {"word": "also:", "note": "Doppelpunkt am Wort"},
    {"word": "erstens;", "note": "Semikolon am Wort"},
    {"word": "Ende.", "note": "Punkt am Satzende"},
    {"word": "„wohl“", "note": "deutsche Anführungszeichen"},
    # Apostrophe carrier is English on purpose: German elisions ("geht's")
    # end in s, and the positional rule would print a wrong final ſ hint.
    {"word": "don’t", "lang": "en", "note": "Apostroph in der Verkürzung"},
    {"word": "E-Mail", "note": "Bindestrich (geschrieben als historischer Doppelstrich)"},
]


# --- the project's reference words ------------------------------------------
# Architecture §9's three named words: the Pflicht-Anker pair `lesen` + `das`
# and, separately, the generalisation word `denen`. Two roles, so the list is
# named for what the three share — they are the §9 references — not "anchors".
_MVP_REFERENCE_WORDS = ["lesen", "das", "denen"]

_OCCURRENCE_SUFFIX = re.compile(r"-\d+$")


def _dev_split_words() -> list[str]:
    """The distinct word texts behind the frozen dev-19 specimen ids.

    The ids carry the occurrence number of a repeated word (`und-3`), which is
    a sample identity, not a word — three occurrences of `und` are one word to
    write. Derived rather than copied so the pin list cannot drift away from
    the split it names.
    """
    return sorted({_OCCURRENCE_SUFFIX.sub("", sample_id) for sample_id in TRACEBENCH_DEV_IDS})


# The project's reference words get an own-hand strip early (owner decision
# Q17, 2026-09-18). For the twelve dev-split words — `das` among them — that
# closes a three-way bridge: each exists as a 1922 plate sample and as a system
# rendering already, and the strip is what the pin adds, so a Tafel · Platte ·
# Eigenhand comparison has the same word on all three sides. `lesen` and
# `denen` are NOT on the plate (the sidecar `data/sources/suetterlin-1922/
# words.json` has neither); they gain the strip beside their rendering, a
# two-way comparison. Both halves are already curated above (`mvp9`,
# `bench-abb19`) — pinning only moves them to the head of the print queue.
#
# The dependency runs ONE way: the curation reads the frozen split, and no
# bench number ever reads the strip plan (proposal §12 Prüfstein 2). A
# reference word the plan already carries is NOT pinned — a pin says "write
# this early", not "write this again" (proposal §4), and `pool.pin_words`
# skips it.
REFERENCE_WORDS: list[str] = list(dict.fromkeys(_MVP_REFERENCE_WORDS + _dev_split_words()))


# --- pinned words: written FIRST, because the author wants them early -------
# Not a coverage argument and not pretending to be one — these words earn their
# place by what they are, so they bypass the quota-driven fill instead of
# waiting for it (owner, 2026-09-06). `tools.eigenhand.pool pin` puts each of
# them on its own appended strip and marks that strip as leading the plan; the
# frozen strips are not touched, and the words count in Bestand and coverage
# like every other word.
_PIN_ENTRIES: list[PoolEntry] = [
    # Shapes as `Kurrentſchrift`: the default rules already give the long ſ at
    # the start of the second morpheme (`-schrift`), so no fugen marker is
    # needed and the label prints plainly.
    {"word": "Kurrentschrift", "note": "Name des Vorhabens; steht im Hero der Seite"},
    # No note and no era/lang here: every reference word is already curated in
    # an earlier layer, and `pool_entries()` keeps the first writer's gloss —
    # a second note would be silently dropped. The `pin` tag unions on top.
    # That an earlier layer really carries each of them is a test, not a
    # promise (`test_every_reference_word_is_curated_outside_the_pin_layer`):
    # these rows put the words into the pool themselves, so the uncurated-word
    # guard in `pool.pin_words` can no longer catch a gap here.
    *({"word": word} for word in REFERENCE_WORDS),
]
PINNED_FIRST: list[str] = [entry["word"] for entry in _PIN_ENTRIES]


def pool_entries() -> list[PoolEntry]:
    """The merged pool: one entry per distinct word (case-sensitive), tags unioned.

    Case-sensitive identity is deliberate — ``Wer`` and ``wer`` shape to
    different glyph sequences (the capital) and are both worth training.
    First writer wins for era/lang/note (the quiz glosses are the richest and
    come first); a fugen marker must agree wherever it is stated twice.
    """
    merged: dict[str, dict] = {}

    def add(word: str, tag: str, extra: PoolEntry | None = None) -> None:
        entry = merged.setdefault(word, {"word": word, "tags": []})
        if tag not in entry["tags"]:
            entry["tags"].append(tag)
        for key in ("lang", "era", "fugen", "note"):
            value = (extra or {}).get(key)
            if value is None:
                continue
            if key == "fugen" and entry.get("fugen") not in (None, value):
                raise ValueError(f"{word}: conflicting fugen markers")
            entry.setdefault(key, value)

    for quiz in _QUIZ_ENTRIES:
        # Explicit lang so a spelling shared with the English layer ("still")
        # keeps de — the quiz bank is German by construction.
        extra: PoolEntry = {"era": quiz.get("era", "modern"), "lang": "de"}
        if quiz.get("fugen"):
            extra["fugen"] = quiz["fugen"]
        if quiz.get("note"):
            extra["note"] = quiz["note"]
        add(quiz["word"], "quizbank", extra)
    for word in _MVP9_WORDS:
        add(word, "mvp9")
    for word in _BENCH_ABB19_WORDS:
        add(word, "bench-abb19", _BENCH_NOTES.get(word))
    for entry in _RARE_JOIN_ENTRIES:
        add(entry["word"], "rare-join", entry)
    for word in _COMMON_DE_WORDS:
        add(word, "haeufig")
    for word in ALLTAG_WORDS:
        add(word, "alltag")
    for word in _COMMON_EN_WORDS:
        add(word, "english", {"lang": "en"})
    for entry in _ZEICHEN_ENTRIES:
        add(entry["word"], "zeichen", entry)
    for entry in _PIN_ENTRIES:
        add(entry["word"], "pin", entry)

    out: list[PoolEntry] = []
    for entry in sorted(merged.values(), key=lambda e: e["word"]):
        entry.setdefault("lang", "de")
        entry.setdefault("era", "modern")
        if entry.get("fugen") and entry["fugen"].replace("|", "") != entry["word"]:
            raise ValueError(f"{entry['word']}: fugen must strip to the word")
        out.append(entry)  # type: ignore[arg-type]
    return out


def shaping_form(entry: PoolEntry) -> str:
    """The form handed to core.shaping: the fugen-marked word where one exists."""
    return entry.get("fugen") or entry["word"]
