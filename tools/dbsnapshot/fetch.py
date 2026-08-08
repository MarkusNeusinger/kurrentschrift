"""Pull one archive snapshot over the DEPLOYED API and file it, append-only.

Every call is a GET. The client is `tools.wordbench.fetch_fixtures.ApiClient`,
imported rather than restated on purpose: it has no write verb at all and it
refuses redirects, so the admin header can never be resent to another host.
A second, "simpler" client here would be a second place for that property to go
missing — which is the one bug an archiving tool must not have.

Why HTTP and not psycopg: the archive has to be creatable from wherever the
work happens, and a cloud session has no Cloud SQL egress at all. The same
split already exists one level down (`export_fixtures` over the DB,
`fetch_fixtures` over HTTPS); a direct-DB sibling can be added later as
redundancy for "API down, database up", but it must never be the only path.

Safety properties, in the order they matter:

* **Append-only.** Each run writes a new timestamped directory. An existing
  directory is never opened for writing, never overwritten, never removed. The
  tool has no delete path — not as a flag, not as a cleanup step.
* **A shrinking snapshot is an error.** The dangerous failure is not a crash,
  it is a snapshot that succeeds while the API quietly returns less than it
  did — an empty archive looks exactly like a full one in a directory listing.
  Counts are therefore compared against the newest existing manifest and the
  run fails unless `--allow-shrink` says the loss is intended.
* **Contents never reach stdout.** The archive holds the reserved data; the
  tool prints counts and paths only.

Restoring is deliberately NOT implemented here. Writing to the database is a
production action that needs a human decision each time, not a flag on a
backup tool.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.wordbench.fetch_fixtures import DEFAULT_API_BASE, ApiClient


REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_SUBDIR = "db-snapshots"
SNAPSHOT_FORMAT = 1

# The two tables no recomputation brings back: the wizard's crop work and the
# stylus-drawn ductus. A snapshot without them is not a snapshot, so an empty
# one of these fails the run rather than being filed.
PRIMARY_TABLES = ("bboxes", "templates")

# Everything below derives from the primaries plus the committed chart bytes,
# but it is small and it makes a snapshot self-contained enough to diff, so it
# rides along. `quiz_words` is deliberately absent: it is seeded from
# tools/quizgen through a migration and lives in the public repo already.
PER_SOURCE_READS: tuple[tuple[str, str, bool], ...] = (
    # (table name, path suffix, admin)
    ("bboxes", "/bboxes", False),
    ("pairs", "/pairs", False),
    ("instances", "/instances", False),
    ("pair_instances", "/pair-instances", False),
    ("word_instances", "/word-instances", False),
)
GLOBAL_READS: tuple[tuple[str, str, bool], ...] = (
    ("sources", "/sources", False),
    ("styles", "/styles", False),
    ("hands", "/hands", False),
    ("work_items", "/work-items", True),
)


def _git(*args: str, cwd: Path) -> str:
    """Run one git command and return its stdout, or "" if git is unavailable."""
    try:
        done = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=60, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


def _restore_inheritance(sources: list[dict[str, Any]], styles: list[dict[str, Any]]) -> int:
    """Turn the API's RESOLVED source fields back into the DB's null-means-inherit.

    `Source.style_ratio` and `Source.slant_deg` are nullable per-source
    overrides, and `GET /sources` returns them already resolved against the
    style's defaults. Archiving that resolved value and restoring it would turn
    „inherits the style" into „overrides the style with today's default" —
    invisible in any render comparison, and only noticed later, when an edit to
    the style default stops propagating. So a value equal to its style's default
    is written back as null.

    The one case this cannot get right is an explicit override that happens to
    equal the default: through this API it is indistinguishable from inheriting,
    and is normalised to inheriting. The manifest says so.
    """
    by_id = {s["id"]: s for s in styles}
    inheriting = 0
    for source in sources:
        style = by_id.get(source.get("style_id")) or {}
        for field, default_field in (("style_ratio", "default_style_ratio"), ("slant_deg", "default_slant_deg")):
            if default_field in style and source.get(field) == style[default_field]:
                source[field] = None
                inheriting += 1
    return inheriting


def collect(client: ApiClient) -> tuple[dict[str, Any], dict[str, int]]:
    """Read every archived table. Returns (payload tree, per-table row counts)."""
    payload: dict[str, Any] = {"global": {}, "sources": {}}
    counts: dict[str, int] = {}

    for name, path, admin in GLOBAL_READS:
        rows = client.get(path, admin=admin)
        payload["global"][name] = rows
        counts[name] = len(rows) if isinstance(rows, list) else 0

    # Deliberately NOT in `counts`: that dict is row counts, and the shrink
    # check fails a run whose numbers went down. This one legitimately goes
    # down the moment a source gains a real override — a safety net that cries
    # wolf is one nobody reads.
    payload["inherited_fields"] = _restore_inheritance(payload["global"]["sources"], payload["global"]["styles"])

    for source in payload["global"]["sources"]:
        sid = source["id"]
        per: dict[str, Any] = {}
        for name, suffix, admin in PER_SOURCE_READS:
            rows = client.get(f"/sources/{sid}{suffix}", admin=admin)
            per[name] = rows
            counts[name] = counts.get(name, 0) + (len(rows) if isinstance(rows, list) else 0)

        payload["sources"][sid] = per

    # Templates hang off the STYLE, not the source — the unique key is
    # (style_id, glyph_key, variant), and two sources of one style therefore
    # serve the same rows. Reading them per source would duplicate every
    # Kurrent template and collide on restore, so they are archived per style,
    # read through one source of that style.
    payload["styles"] = {}
    # Which source each style's rows were read through. `provenance_source_id`
    # is not in the response, and it is NOT decoration: `api.rendering.pooled_pen`
    # pools the source's own templates into the Gleichzug nib, so a restore that
    # leaves it empty renders every width slightly wrong. Recording the source
    # we read through restores it exactly for a single-source style; for a style
    # with several sources it is an approximation, and the manifest says so.
    read_via: dict[str, str] = {}
    by_style: dict[str, str] = {}
    for source in payload["global"]["sources"]:
        by_style.setdefault(source["style_id"], source["id"])
    for style_id, sid in sorted(by_style.items()):
        # One request per row: the list is summaries without geometry by
        # design, and `raw_path` — the whole point of the archive — exists only
        # on the single-template read.
        summaries = client.get(f"/sources/{sid}/templates")
        wanted = {(s["glyph_key"], int(s.get("variant", 0))) for s in summaries if s.get("has_data")}
        rows = []
        for glyph_key, variant in sorted(wanted):
            row = client.get(
                f"/sources/{sid}/templates/{glyph_key}",
                {"variant": variant} if variant else None,
                admin=True,
                allow_404=True,
            )
            if row is not None:
                rows.append(row)
        payload["styles"][style_id] = {"templates": rows}
        read_via[style_id] = sid
        counts["templates"] = counts.get("templates", 0) + len(rows)
        counts["templates_with_raw_path"] = counts.get("templates_with_raw_path", 0) + sum(
            1 for r in rows if r.get("raw_path")
        )

    per_style = Counter(s["style_id"] for s in payload["global"]["sources"])
    payload["templates_read_via"] = read_via
    payload["ambiguous_styles"] = sorted(style for style, n in per_style.items() if n > 1)
    return payload, counts


def latest_manifest(archive: Path) -> dict[str, Any] | None:
    """The newest existing snapshot's manifest, or None if the archive is empty."""
    root = archive / ARCHIVE_SUBDIR
    if not root.is_dir():
        return None
    stamps = sorted(p for p in root.iterdir() if p.is_dir() and (p / "manifest.json").is_file())
    if not stamps:
        return None
    return json.loads((stamps[-1] / "manifest.json").read_text())


def check_plausible(counts: dict[str, int], previous: dict[str, Any] | None) -> list[str]:
    """Reasons this snapshot must not be filed. Empty list means it may be."""
    problems = []
    for table in PRIMARY_TABLES:
        if counts.get(table, 0) == 0:
            problems.append(f"{table}: 0 rows — the API returned nothing for a table that cannot be empty")
    if counts.get("templates_with_raw_path", 0) == 0 and counts.get("templates", 0) > 0:
        problems.append("templates: not one row carries a raw_path — the admin read is probably unauthorised")
    if previous:
        for table, was in (previous.get("counts") or {}).items():
            now = counts.get(table, 0)
            if isinstance(was, int) and now < was:
                problems.append(f"{table}: {now} rows now, {was} in the previous snapshot — shrinking, refusing")
    return problems


def write_snapshot(out: Path, payload: dict[str, Any], manifest: dict[str, Any]) -> None:
    """Write one snapshot directory. Refuses to touch an existing one."""
    if out.exists():
        raise SystemExit(f"{out} already exists — snapshots are append-only, never rewritten")
    out.mkdir(parents=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    for name, rows in payload["global"].items():
        (out / f"{name}.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    for group in ("sources", "styles"):
        for key, tables in payload.get(group, {}).items():
            per = out / group / key
            per.mkdir(parents=True)
            for name, rows in tables.items():
                (per / f"{name}.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")


def file_into_archive(snapshot: Path, archive: Path, stamp: str, counts: dict[str, int], *, push: bool) -> str:
    """Move the snapshot into the archive repository and commit it."""
    target = archive / ARCHIVE_SUBDIR / stamp
    if target.exists():
        raise SystemExit(f"{target} already exists — refusing to file over it")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(snapshot), str(target))

    headline = ", ".join(f"{k} {counts.get(k, 0)}" for k in ("templates", "bboxes", "pairs", "instances"))
    _git("add", "--", f"{ARCHIVE_SUBDIR}/{stamp}", cwd=archive)
    _git("commit", "-m", f"snapshot {stamp} ({headline})", cwd=archive)
    if push:
        branch = _git("rev-parse", "--abbrev-ref", "HEAD", cwd=archive) or "main"
        out = _git("push", "-u", "origin", branch, cwd=archive)
        return f"committed and pushed to {branch}" + (f" ({out})" if out else "")
    return "committed (not pushed — pass --push)"


def _iter_lines(counts: dict[str, int]) -> Iterable[str]:
    for name in sorted(counts):
        yield f"  {name:26s} {counts[name]:5d}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.dbsnapshot.fetch",
        description="Pull one archive snapshot of the hand-made data over the deployed API.",
    )
    parser.add_argument("--api", default=os.environ.get("API_BASE_URL") or DEFAULT_API_BASE, help="API base URL")
    parser.add_argument(
        "--archive",
        default=os.environ.get("KURRENTSCHRIFT_ARCHIVE"),
        help="path to the PRIVATE archive repository clone; without it the snapshot stays in --out",
    )
    parser.add_argument("--out", default=str(REPO_ROOT / "temp" / "dbsnapshot"), help="staging directory")
    parser.add_argument("--push", action="store_true", help="push the archive repository after committing")
    parser.add_argument(
        "--allow-shrink",
        action="store_true",
        help="file the snapshot even though it holds fewer rows than the previous one",
    )
    args = parser.parse_args(argv)

    client = ApiClient(args.api, token=os.environ.get("ADMIN_TOKEN"))
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    archive = Path(args.archive).expanduser().resolve() if args.archive else None

    payload, counts = collect(client)
    problems = check_plausible(counts, latest_manifest(archive) if archive else None)
    shrink_only = problems and all("shrinking" in p for p in problems)
    if problems and not (args.allow_shrink and shrink_only):
        print("snapshot REJECTED — not filed:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    if problems:
        print("filing anyway (--allow-shrink):")
        for problem in problems:
            print(f"  {problem}")

    manifest = {
        "format": SNAPSHOT_FORMAT,
        "taken_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "api_base": args.api,
        "code_commit": _git("rev-parse", "--short", "HEAD", cwd=REPO_ROOT),
        "code_branch": _git("rev-parse", "--abbrev-ref", "HEAD", cwd=REPO_ROOT),
        "counts": counts,
        "primary_tables": list(PRIMARY_TABLES),
        # Stated rather than silently lost: what the read endpoints do not
        # serve, so a restore from this archive is known to be incomplete here.
        "templates_read_via": payload["templates_read_via"],
        "ambiguous_styles": payload["ambiguous_styles"],
        "inherited_fields": payload["inherited_fields"],
        # Stated rather than silently lost: what the read endpoints do not
        # serve, so a restore from this archive is known to be inexact here.
        # Both were found by an actual restore drill, not by reading the code.
        "known_gaps": [
            "templates.provenance_source_id is not served; the restore reconstructs it from"
            " templates_read_via, which is exact for a single-source style and a guess for"
            " the styles listed in ambiguous_styles",
            "entry/exit_pt lose the legacy `coupling` key on the way out (EndPointOut drops it);"
            " nothing reads it, so this changes no rendering",
            "sources.style_ratio/slant_deg are served RESOLVED against the style defaults; a value"
            " equal to its default is archived as null (inherit). An explicit override that happens"
            " to equal the default is indistinguishable through this API and becomes inherit",
            "aggregates / pair_aggregates are not archived — derived, rebuild them from the occurrences",
        ],
    }
    staged = Path(args.out).expanduser().resolve() / stamp
    write_snapshot(staged, payload, manifest)

    print(f"snapshot {stamp}")
    print("\n".join(_iter_lines(counts)))
    if archive:
        print(file_into_archive(staged, archive, stamp, counts, push=args.push))
        print(f"filed at {archive / ARCHIVE_SUBDIR / stamp}")
    else:
        print(f"staged at {staged} — pass --archive to file it into the private archive repository")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
