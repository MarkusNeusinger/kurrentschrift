"""Minimal, dependency-free PDF writer — Python twin of ``app/src/lib/pdf.ts``.

Same construction as the TS original (PDF 1.4, built-in Helvetica with
WinAnsiEncoding so German umlauts render without font embedding, Latin-1
body so xref byte offsets equal string lengths), plus the one operator the
Übungsblatt writer never needed: filled rectangles (``re f``) for the
Passmarken. Deterministic bytes for identical inputs — nothing here reads a
clock (dates arrive as explicit strings), so golden-file tests can pin the
output.

Note: WinAnsi has no long s (ſ) — clear-text labels stay plain Latin, which
is what the legibility doctrine wants on a printed sheet anyway.
"""

from __future__ import annotations

from dataclasses import dataclass


PT_PER_MM = 72 / 25.4
A4_W_PT = 210 * PT_PER_MM
A4_H_PT = 297 * PT_PER_MM

# Helvetica (base-14) advance widths in 1000-unit em — ported verbatim from
# pdf.ts HELV_WIDTH; unknown glyphs fall back to 556.
_HELV_WIDTH: dict[str, int] = {
    " ": 278,
    "!": 278,
    '"': 355,
    "#": 556,
    "$": 556,
    "%": 889,
    "&": 667,
    "'": 191,
    "(": 333,
    ")": 333,
    "*": 389,
    "+": 584,
    ",": 278,
    "-": 333,
    ".": 278,
    "/": 278,
    ":": 278,
    ";": 278,
    "<": 584,
    "=": 584,
    ">": 584,
    "?": 556,
    "@": 1015,
    "[": 278,
    "\\": 278,
    "]": 278,
    "^": 469,
    "_": 556,
    "`": 333,
    "{": 334,
    "|": 260,
    "}": 334,
    "~": 584,
    "°": 400,
    "·": 278,
    "A": 667,
    "B": 667,
    "C": 722,
    "D": 722,
    "E": 667,
    "F": 611,
    "G": 778,
    "H": 722,
    "I": 278,
    "J": 500,
    "K": 667,
    "L": 556,
    "M": 833,
    "N": 722,
    "O": 778,
    "P": 667,
    "Q": 778,
    "R": 722,
    "S": 667,
    "T": 611,
    "U": 722,
    "V": 667,
    "W": 944,
    "X": 667,
    "Y": 667,
    "Z": 611,
    "a": 556,
    "b": 556,
    "c": 500,
    "d": 556,
    "e": 556,
    "f": 278,
    "g": 556,
    "h": 556,
    "i": 222,
    "j": 222,
    "k": 500,
    "l": 222,
    "m": 833,
    "n": 556,
    "o": 556,
    "p": 556,
    "q": 556,
    "r": 333,
    "s": 500,
    "t": 278,
    "u": 556,
    "v": 500,
    "w": 722,
    "x": 500,
    "y": 500,
    "z": 500,
    "ä": 556,
    "ö": 556,
    "ü": 556,
    "ß": 556,
    "Ä": 667,
    "Ö": 778,
    "Ü": 722,
}


def helv_width_mm(text: str, size_mm: float) -> float:
    """Rendered width of Helvetica text at a given cap size in mm."""
    # Measured over the WinAnsi mapping, i.e. the characters the reader draws:
    # a non-cp1252 "digit" arrives as "?" and must be measured as one. ASCII
    # digits keep the uniform Helvetica figure advance.
    units = sum(556 if ch in "0123456789" else _HELV_WIDTH.get(ch, 556) for ch in winansi(text))
    return units / 1000 * size_mm


@dataclass(frozen=True)
class Line:
    x1: float
    y1: float
    x2: float
    y2: float
    color: str
    width_mm: float
    dash: tuple[float, float] | None = None


@dataclass(frozen=True)
class Rect:
    """Filled axis-aligned rectangle, mm top-left origin (x, y = top-left corner)."""

    x: float
    y: float
    w: float
    h: float
    color: str


@dataclass(frozen=True)
class Text:
    x: float
    y: float  # text baseline, mm from page top
    size_mm: float
    text: str
    color: str


def _rgb(hex_color: str) -> tuple[float, float, float]:
    value = int(hex_color.lstrip("#"), 16)
    return ((value >> 16 & 0xFF) / 255, (value >> 8 & 0xFF) / 255, (value & 0xFF) / 255)


def winansi(text: str) -> str:
    """The characters the PDF will actually DRAW — the metric's ground truth.

    The font is WinAnsi (cp1252), so the German quotes „ “ , the dashes – —
    and the typographic apostrophe ’ DO have byte encodings — map them via
    cp1252 instead of dropping everything above 0xFF (the pdf.ts twin only
    ever prints ASCII+umlauts and never needed this). Anything cp1252 cannot
    encode is drawn as "?".

    Deliberately NOT the escaped literal: escaping adds a backslash before
    ``( ) \\`` that the reader never draws, so measuring the escaped string
    would overstate the width of every text containing a parenthesis — and
    the row ids do ("S0001 (1/3)").
    """
    out = []
    for ch in text:
        if ord(ch) > 0xFF:
            try:
                out.append(chr(ch.encode("cp1252")[0]))
            except UnicodeEncodeError:
                out.append("?")
        else:
            out.append(ch)
    return "".join(out)


def _escape(text: str) -> str:
    """PDF literal-string escape, on top of the WinAnsi mapping."""
    out = []
    for ch in winansi(text):
        if ch in ("\\", "(", ")"):
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def _px(mm: float) -> str:
    return f"{mm * PT_PER_MM:.2f}"


def _py(mm: float) -> str:
    return f"{(297 - mm) * PT_PER_MM:.2f}"


def build_pdf(rects: list[Rect], lines: list[Line], texts: list[Text]) -> bytes:
    """One A4 page from pre-ordered primitives (rects under lines under text)."""
    ops: list[str] = ["1 J"]  # round line caps, as in pdf.ts

    for rect in rects:
        r, g, b = _rgb(rect.color)
        ops.append(f"{r:.3f} {g:.3f} {b:.3f} rg")
        ops.append(f"{_px(rect.x)} {_py(rect.y + rect.h)} {_px(rect.w)} {_px(rect.h)} re f")

    state: tuple | None = None
    for line in lines:
        key = (line.color, line.width_mm, line.dash)
        if key != state:
            r, g, b = _rgb(line.color)
            ops.append(f"{r:.3f} {g:.3f} {b:.3f} RG")
            ops.append(f"{_px(line.width_mm)} w")
            ops.append(f"[{_px(line.dash[0])} {_px(line.dash[1])}] 0 d" if line.dash else "[] 0 d")
            state = key
        ops.append(f"{_px(line.x1)} {_py(line.y1)} m {_px(line.x2)} {_py(line.y2)} l S")

    for text in texts:
        r, g, b = _rgb(text.color)
        ops.append(f"{r:.3f} {g:.3f} {b:.3f} rg")
        size_pt = text.size_mm * PT_PER_MM
        ops.append(f"BT /F1 {size_pt:.2f} Tf {_px(text.x)} {_py(text.y)} Td ({_escape(text.text)}) Tj ET")

    content = "\n".join(ops)
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {A4_W_PT:.2f} {A4_H_PT:.2f}] "
        "/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        # /Length counts only the stream data (ISO 32000-1 §7.3.8.1) — the EOL
        # before `endstream` is excluded, as in pdf.ts.
        f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]

    body = "%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets: list[int] = []
    for index, obj in enumerate(objects):
        offsets.append(len(body))
        body += f"{index + 1} 0 obj\n{obj}\nendobj\n"
    xref_offset = len(body)
    body += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for offset in offsets:
        body += f"{offset:010d} 00000 n \n"
    body += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    return body.encode("latin-1")
