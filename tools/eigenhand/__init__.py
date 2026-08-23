"""Eigenhand-Erfassung — collect the author's own hand as training data.

The tool family behind ``docs/proposals/eigenhand-erfassung.md``: a curated,
growing word pool (Wortvorrat) is partitioned into stable strips (Streifen),
printed as A4 sheets (Bogen) with per-word lineature boxes and corner
fiducials (Passmarken), written with a real dip pen, scanned or photographed,
rectified, reviewed row by row (Siebung), and filed as strip recordings
(Fassung) in a local, gitignored data root — the reserved own-hand dataset.

Module map (each CLI module is its own entrypoint, humanbench-style):

* ``corpus``    — the committed word pool (curation source of truth)
* ``coverage``  — shaped join / glyph-position bookkeeping (core.shaping)
* ``universe``  — build the local Übergangsraum weight table from corpora
* ``pool``      — build/append the committed strip plan ``streifen.json``
* ``gaps``      — list uncovered joins + real carrier-word candidates
* ``geometry``  — mm page layout (port of app/src/lib/lineatur.ts)
* ``pdfgen``    — dependency-free PDF 1.4 writer (twin of app/src/lib/pdf.ts)
* ``sheet``     — compose and print a Bogen (PDF + layout.json sidecar)
* ``fiducial``  — Passmarken detection (scikit-image only, no OpenCV)
* ``ingest``    — scan/photo → rectified mm-space crops + review payload
* ``page``      — the self-contained HTML review page (Siebung)
* ``apply``     — file reviewed rows as Fassungen, update the Kartei
* ``kartei``    — the local manifest (single state source, never committed)
* ``report``    — Bestandsbericht: Soll/Ist per glyph position and join
* ``redo``      — queue strips for re-recording, optionally retire Fassungen
* ``snapshot``  — incremental, create-only copy into the private archive

Invariants (docs/reference/werkzeuge.md): measurement/authoring layer only —
these tools never write to the database; everything they produce lives under
the gitignored data root ``data/samples/own-hand/`` or ``temp/``.
"""
