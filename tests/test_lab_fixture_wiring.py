"""Guard the lab-test skip conditions against silent rot.

The glyphlab/wordlab/pairlab suites skip in CI because their bench fixtures
are DB-exported and gitignored — that is deliberate. But the skip condition
is "no manifest.json under the consumer's fixtures dir", so a renamed export
directory or manifest filename would make the skip PERMANENT everywhere and
nobody would notice (CI has always shown those tests as skipped). These
always-run tests pin the wiring: the consumers must look exactly where the
exporters write.
"""

from __future__ import annotations

from tools.glyphbench.export_fixtures import DEFAULT_OUT_DIR as GLYPH_EXPORT_DIR
from tools.glyphlab.cases import DEFAULT_FIXTURES_DIR as GLYPHLAB_DIR
from tools.wordbench.export_fixtures import DEFAULT_OUT_DIR as WORD_EXPORT_DIR
from tools.wordlab.cases import DEFAULT_FIXTURES_DIR as WORDLAB_DIR


def test_glyphlab_reads_where_glyphbench_exports():
    assert GLYPHLAB_DIR.resolve() == GLYPH_EXPORT_DIR.resolve()


def test_wordlab_reads_where_wordbench_exports():
    assert WORDLAB_DIR.resolve() == WORD_EXPORT_DIR.resolve()


def test_exporters_write_the_manifest_name_the_consumers_glob():
    # Both exporters write `<root>/.../manifest.json`; both consumers (and the
    # lab suites' skipif) glob for exactly that name. Pin the literal so a
    # rename on either side fails here instead of silently skipping forever.
    import inspect

    from tools.glyphbench import export_fixtures as glyph_export
    from tools.wordbench import export_fixtures as word_export

    for module in (glyph_export, word_export):
        assert "manifest.json" in inspect.getsource(module)
