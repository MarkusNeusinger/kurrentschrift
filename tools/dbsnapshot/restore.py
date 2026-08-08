"""Load an archive snapshot back into a database — for drills, not for production.

An archive nobody has ever restored is a guess. This is the other half of
`fetch.py`: it exists so a snapshot can be PROVEN restorable against a
throwaway PostgreSQL, which is a test with no production exposure at all.

It restores the two irreplaceable tables and their parents — `bboxes` and
`templates`, hanging off `styles`/`sources`. Everything else in a snapshot is
re-derivable from those plus the committed chart bytes (occurrences via the
harvest, aggregates via the rebuild endpoints, running forms via
apply-laufform) and is archived for reading, not for reloading.

Three independent guards, because the damage from restoring over live data is
exactly the damage the archive exists to prevent:

1. `--database-url` is REQUIRED and is never read from the environment. The
   deployment's own URL lives in `DATABASE_URL`; a tool that falls back to it
   can wipe production through a forgotten flag.
2. A URL equal to `DATABASE_URL` is refused outright.
3. A target that already holds rows in the primary tables is refused unless
   `--replace` says so, and nothing is written at all without `--apply`
   (a dry run is the default).

Restoring into the real database therefore stays a deliberate human act,
performed with the guards consciously overridden — which is what a production
write should feel like.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import Integer, delete, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.database.models import Bbox, Hand, Source, Style, Template


# Restored in this order: a template points at a style, a bbox at a source.
PARENTS = ((Style, "styles"), (Hand, "hands"), (Source, "sources"))
PRIMARY = ((Bbox, "bboxes"), (Template, "templates"))


def _columns(model: type) -> set[str]:
    """Column names of a model, so a payload can be mapped by intersection.

    Mapping by intersection rather than by a hand-written field list means a new
    column shows up in restores as soon as the API serves it, and a column the
    API does not serve is simply left at its default instead of raising.
    """
    return {c.key for c in model.__table__.columns}


def rows_for(model: type, payload: list[dict[str, Any]], extra: dict[str, Any]) -> list[dict[str, Any]]:
    """Payload rows reduced to what this model can store, plus injected keys.

    An INTEGER primary key is a generated row number and is dropped — carrying
    it over would pin the restore to the old sequence. A STRING primary key is
    the identity itself (`suetterlin-1922`, `kurrent`) and is kept, which is
    also what lets the seeded parent rows be merged rather than duplicated.
    """
    generated = {c.key for c in model.__table__.primary_key.columns if isinstance(c.type, Integer)}
    keep = _columns(model) - generated
    return [{**{k: v for k, v in row.items() if k in keep}, **extra} for row in payload]


def read_snapshot(root: Path) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """Read one snapshot directory into (manifest, table -> rows)."""
    manifest = json.loads((root / "manifest.json").read_text())
    tables: dict[str, list[dict[str, Any]]] = {}
    for model, name in PARENTS:
        path = root / f"{name}.json"
        # Reduce to storable columns here too: the API's Out schemas carry
        # resolved, computed fields (`authorable`, `style_ratio`, …) that have
        # no column behind them.
        tables[name] = rows_for(model, json.loads(path.read_text()), {}) if path.is_file() else []

    for _, name in PRIMARY:
        tables[name] = []
    # Bboxes belong to a source, templates to a style — the same split the
    # unique keys use, and the reason the snapshot is laid out that way.
    for source_dir in sorted((root / "sources").iterdir()) if (root / "sources").is_dir() else []:
        path = source_dir / "bboxes.json"
        if path.is_file():
            tables["bboxes"].extend(rows_for(Bbox, json.loads(path.read_text()), {"source_id": source_dir.name}))
    read_via = manifest.get("templates_read_via") or {}
    for style_dir in sorted((root / "styles").iterdir()) if (root / "styles").is_dir() else []:
        path = style_dir / "templates.json"
        if path.is_file():
            # `provenance_source_id` is not served by the API but IS load-bearing:
            # the Gleichzug nib is pooled over a source's own templates, so a row
            # without it renders every width slightly wrong. The manifest records
            # which source the rows were read through; that is exact for a
            # single-source style (see `ambiguous_styles`).
            extra = {"style_id": style_dir.name, "provenance_source_id": read_via.get(style_dir.name)}
            tables["templates"].extend(rows_for(Template, json.loads(path.read_text()), extra))
    return manifest, tables


async def _counts(session: Any) -> dict[str, int]:
    out = {}
    for model, name in (*PARENTS, *PRIMARY):
        out[name] = int((await session.execute(select(func.count()).select_from(model))).scalar_one())
    return out


async def run(url: str, root: Path, *, apply: bool, replace: bool) -> int:
    manifest, tables = read_snapshot(root)
    engine = create_async_engine(url, future=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as session:
            before = await _counts(session)
            occupied = [name for _, name in PRIMARY if before[name] > 0]
            if occupied and not replace:
                print(f"target already holds rows in {', '.join(occupied)} — refusing (pass --replace to overwrite)")
                return 1

            print(f"snapshot {root.name} (taken {manifest.get('taken_at')}, code {manifest.get('code_commit')})")
            for _, name in (*PARENTS, *PRIMARY):
                print(f"  {name:12s} {before[name]:5d} in target  ->  {len(tables[name]):5d} from snapshot")
            if not apply:
                print("dry run — nothing written. Pass --apply to restore.")
                return 0

            for model, _ in reversed(PRIMARY):
                await session.execute(delete(model))
            for model, name in (*PARENTS, *PRIMARY):
                rows = [r for r in tables[name] if r]
                if not rows:
                    continue
                for row in rows:
                    if name in {"styles", "hands", "sources"}:
                        # Migrations seed these, so a drill target already has
                        # them: merge by primary key instead of colliding.
                        await session.merge(model(**row))
                    else:
                        session.add(model(**row))
            await session.commit()
            after = await _counts(session)
        print("restored:", ", ".join(f"{k} {v}" for k, v in after.items()))
        return 0
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.dbsnapshot.restore",
        description="Restore an archive snapshot into a THROWAWAY database (drill), never into production by default.",
    )
    parser.add_argument("snapshot", help="path to one snapshot directory (the one holding manifest.json)")
    parser.add_argument("--database-url", required=True, help="target DB; deliberately not read from the environment")
    parser.add_argument("--apply", action="store_true", help="actually write (default is a dry run)")
    parser.add_argument("--replace", action="store_true", help="allow a target that already holds primary rows")
    args = parser.parse_args(argv)

    live = os.environ.get("DATABASE_URL")
    if live and args.database_url.strip() == live.strip():
        raise SystemExit("--database-url equals DATABASE_URL — that is the live database, refusing")
    return asyncio.run(run(args.database_url, Path(args.snapshot).resolve(), apply=args.apply, replace=args.replace))


if __name__ == "__main__":
    raise SystemExit(main())
