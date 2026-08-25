"""Archive of the hand-made data: what no amount of recomputation brings back.

Cloud SQL's own backups cover the fast failures — an accidental drop, a bad
migration, a zone outage — but only for seven days, they die with the instance,
and they cannot be read without restoring one. The failure this project
actually has is slower: an apply or a re-harvest writes bad geometry, nobody
notices for weeks, and by then the window has closed. So this is an ARCHIVE
rather than a backup: readable, diffable, per-file history, pushed to a private
repository outside the GCP project.

Only two things in the database are irreplaceable, and they are what this
archives first:

* `bboxes` — the crop, the eraser and ink strokes, the donor patches, the
  lineature and slant. The wizard work.
* `templates.raw_path` — the stylus-drawn ductus. The project's own
  contribution over the public-domain plates.

Everything else falls back out of those two plus the committed chart bytes:
anchors and half-widths via the canonical derivation, occurrences via the
harvest over the committed plates, aggregates via the rebuild endpoints,
running forms via apply-laufform. Authored rows are the exception and are
archived too — an authored pair override or word trace is hand work, not a
derivation.

The snapshot itself never enters the public repository (open-core reservation,
docs/reference/quellen-und-rechte.md §5). The TOOL is public; its output is
not — the same split the bench fixtures already use.

``.env`` is read here for the same reason as in ``tools/eigenhand``: both the
admin read (``ADMIN_TOKEN``) and the destination (``KURRENTSCHRIFT_ARCHIVE``)
are recorded there, and a backup that only runs when the environment was
sourced by hand is a backup that gets skipped. ``load_dotenv`` leaves an
already-set variable alone.
"""

from dotenv import load_dotenv


load_dotenv()
