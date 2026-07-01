"""wordbench — hermetic quality benchmark for composed WORDS (transitions included).

Sibling of tools/glyphbench, one level up the writing stack: where glyphbench
scores each glyph's re-derived canonical against its own chart crop, wordbench
scores the COMPOSED word — placement + generated Übergänge from core/shaping.py
+ core/compose.py — against real connected-writing specimens of the same hand
(e.g. Sütterlin's own "Ausgangsschrift im Zusammenhang geschrieben", Abb. 19).
See docs/reference/qualitaetsmetrik.md §6 and tools/wordbench/README.md.
"""
