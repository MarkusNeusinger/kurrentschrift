"""The Wortvorrat — the committed, curated word pool of the Eigenhand-Erfassung.

Real words only, no drill syllables: the goal is writing real text, old and
modern, mainly German with a tagged English share (owner decisions,
docs/proposals/eigenhand-erfassung.md). Four curation layers, merged by
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
* ``haeufig``     — high-frequency German function/short words the quiz bank
                    (a reading-quiz curation) deliberately skips but everyday
                    writing needs constantly (du, jetzt, schon, über …)
* ``english``     — a common-English layer beyond the rare-join hunting, so
                    modern mixed-language text stays writable (owner goal);
                    all ``lang: en``, filterable
* ``zeichen``     — digits and punctuation in real text use (years, a date,
                    a price, signs at words); detached glyphs, so they carry
                    glyph-position Soll but no joins

Frequency LISTS are never committed (quiz-wortbank.md §4 — protectable
databases, often NC); this pool is an own, merely *informed* curation and
therefore own expression under the repo licence. The consulted corpora are
documented in ``data/corpora/*/SOURCE.md``.

The pool is TRAINING data, not a measurement set: it grows in waves, and no
bench headline ever reads from it (frozen-reference doctrine untouched).
"""

from __future__ import annotations

from typing import TypedDict

from tools.quizgen.corpus import ENTRIES as _QUIZ_ENTRIES


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

# --- digits and punctuation in REAL text use (owner, 2026-08-22: "Zahlen und
# Sonderzeichen brauchen wir am Ende auch") — never fantasy sequences: years,
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
    for word in _COMMON_EN_WORDS:
        add(word, "english", {"lang": "en"})
    for entry in _ZEICHEN_ENTRIES:
        add(entry["word"], "zeichen", entry)

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
