---
name: dbsnapshot
description: Take an archive snapshot of the hand-made DB data before anything that can overwrite geometry — an apply-laufform run, a migration with DROP or a rewrite, a harvest with replace, any DDL, or after an authoring session — and know the create-only rules that govern the private archive. Use when asked to take, file or check a DB snapshot, to back up the templates or bboxes, or before applying a Laufform, a destructive migration or a bulk re-derive.
---

# Take an archive snapshot (create freely, never destroy)

`tools/dbsnapshot` is not a measurement tool — it is the backup of what no
recomputation brings back: the `bboxes` rectangles and `templates.raw_path`,
the author's own traced geometry. Cloud SQL's own backups are instance-wide
and keep 7 days; this project's failure mode is slower — a bad apply noticed
weeks later — so the archive is what actually covers it.

The snapshot goes into a PRIVATE archive clone **outside the working tree**.
That placement is deliberate: `git clean -xfd` deletes gitignored files, and
the archive must survive it.

## 0 · The rules (author directive, 2026-08-08 — read before acting)

- **Take one freely.** A snapshot costs minutes and is never wrong to have.
- **Take one BEFORE anything that can overwrite geometry:** an
  `apply-laufform`, a migration carrying a DROP or a table rewrite, a
  harvest run with `replace`, any DDL against the shared DB — and AFTER an
  authoring session in which letters were traced.
- **Every snapshot is a new timestamped directory. Never write into an
  existing one, never delete, move or rename one** — not to tidy up, not
  when the disk is short. Report the situation instead of acting on it.
- **Check plausibility before filing** (row counts per table). A silently
  empty snapshot is worse than none, because it looks like safety.
- **Never print archive contents into the transcript.** That is the
  reserved dataset (`docs/reference/quellen-und-rechte.md` §5).
- **Restoring is prod-touching** and needs the author's explicit say-so in
  the same session.

## 1 · Take the snapshot

```bash
uv run python -m tools.dbsnapshot.fetch [--archive <private-clone>] [--push]
```

`fetch.py` pulls over the DEPLOYED read API and needs `ADMIN_TOKEN`. Without
`--archive` (or `KURRENTSCHRIFT_ARCHIVE`) the snapshot stays in the staging
directory under `--out` and is NOT yet safe — filing it in the archive clone
is what makes it a backup.

**The module path is `tools.dbsnapshot.fetch`, not `tools.dbsnapshot`** —
the package has no `__main__.py`, so the bare form aborts with "is a package
and cannot be directly executed".

The tool checks plausibility itself: a run that would file FEWER rows than
the previous manifest fails unless `--allow-shrink` is passed. Treat that
refusal as a finding to report, never as a flag to add reflexively — a
shrunk snapshot means either the DB lost rows or the pull was partial, and
both are worth knowing before they are overwritten by a "successful" run.

The `eigenhand_*` tables travel WITHOUT the PNG column, plus a
`strip_hashes` manifest: the master of the strip images is the `own-hand/`
tree of the same archive, and those hashes are what a restore verifies them
against — and what reveals that DB and archive have drifted apart before the
day comes when it matters (`docs/proposals/eigenhand-erfassung.md` §8.1).

## 2 · Restoring is a drill, not a routine

```bash
uv run python -m tools.dbsnapshot.restore <snapshot-dir> --database-url postgresql://… [--apply] [--replace]
```

`restore.py` is built for drills against a throwaway PostgreSQL (spin one up
the way `/verify-migrations` §1 does). Its guards: the target URL must be
passed explicitly (`--database-url`, deliberately never read from the
environment), it refuses a URL equal to `DATABASE_URL`, it refuses an
occupied target without `--replace`, and it writes nothing without
`--apply`.

**A restore in the direction of production is prod-touching**: name the
exact snapshot, the target and the command, and get the author's go-ahead in
the same session before running it. Do not infer that go-ahead from the task
that led you here.

## Gotchas

- **This skill describes an archive operation; it does not license a write
  to the shared DB.** The snapshot itself only reads. Everything it protects
  against — the apply, the migration, the harvest — still needs its own
  confirmation.
- **The archive lives outside the working tree**, so a worktree-isolated
  agent may not be able to reach it at all. Then the honest outcome is to
  report that the snapshot must be taken from the main checkout, not to
  proceed without one.
- **Do not "clean up" the archive.** Old snapshots are the point: the
  failure this guards against is discovered late, so the value of a snapshot
  grows with its age.
- Related gates: `/verify-migrations` §2a (before a DROP/rewrite revision)
  and `/work-basket` (before an `apply-laufform`).
