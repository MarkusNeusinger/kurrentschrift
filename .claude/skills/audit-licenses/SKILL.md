---
name: audit-licenses
description: Audit the repo for license and data-provenance violations before going public or after any commit touching /data or adding binary assets — verify nothing copyrighted is tracked (in HEAD or history), every data source has a complete SOURCE.md, the gitignore boundaries for corpora/NC-SA hold, and all bundled fonts are covered by notices. Use when asked to audit licenses, check data rights, verify provenance, or prepare the repo for publishing.
---

# License & data-provenance audit

Code is MIT; **data is not** — each source carries its own license.
The binding rules live in `docs/reference/quellen-und-rechte.md` and
`docs/reference/datenablage.md` (plus the CLAUDE.md data section);
read them fresh when judging — this skill only encodes the audit
*procedure*. All commands run from the repo root. Findings are
**reported, never silently deleted**.

## 1 · Hard checks (run the battery)

**Gitignore boundaries** — each path must be ignored individually
(`git check-ignore` with multiple paths exits 0 if *any* one matches,
so a combined call can print a false OK; hypothetical paths are fine):

```bash
for p in data/corpora/some-corpus.csv data/derived/from-nc-sa/stats.json; do git check-ignore -q "$p" && echo "OK ignored: $p" || echo "VIOLATION: not ignored: $p"; done
```

**Tracked binaries, three nets** — extension sweep, content-type
sweep (catches extensionless/renamed binaries), and size list
(catches payloads hiding in text files). Every hit must fall into an
allowed bucket (§2):

```bash
git ls-files | grep -E '\.(png|jpe?g|woff2?|ttf|otf|eot|pdf|gif|webp|svg|ico|zip|tar|t?gz|bz2|xz|wasm|mp[34]|avif|tiff?|bmp|csv|parquet)$'
git ls-files -z | xargs -0 file | awk -F': +' '$2 !~ /text|JSON|SVG|empty|source|script|program|CSV/ {print}'
git ls-files -z | xargs -0 -I{} du -k "{}" 2>/dev/null | sort -rn | head -20
```

**Hidden payloads** — base64 data-URIs in tracked text and raster
images smuggled inside SVGs:

```bash
git grep -nlI ';base64,' -- . ':!docs/reference/kurrentschrift-landing.html' || echo "OK: no new data-URI embeddings"
git grep -nE '<image|data:image' -- '*.svg' || echo "OK: no raster payload in tracked SVGs"
```

(The one excluded file is a known, documented embedding — the landing
prototype carries GL-GermanCursive as a data-URI; see baseline.)

**History** — publishing exposes every blob ever committed, not just
HEAD. First command: binaries that existed but are gone from HEAD
(must be empty). Second: all deleted paths, eyeballed for protected
names:

```bash
comm -23 <(git rev-list --objects --all | awk '{print $2}' | grep -iE '\.(png|jpe?g|woff2?|ttf|otf|eot|pdf|gif|webp|zip|tar|t?gz|bz2|xz)$' | sort -u) <(git ls-files | sort)
git log --diff-filter=D --name-only --pretty=format: | sort -u
```

**Bundled fonts vs. notices** — npm-delivered fonts (`@fontsource/*`)
never appear in `git ls-files`, so check the imports against
`app/THIRD_PARTY_NOTICES.md` directly:

```bash
for pkg in $(grep -roh '@fontsource/[a-z-]*' app/src app/package.json | sort -u); do grep -q "$pkg" app/THIRD_PARTY_NOTICES.md && echo "OK in notices: $pkg" || echo "MISSING from notices: $pkg"; done
```

**No protected work as a file** (prose mentions are bibliographic
references and explicitly allowed; files are not):

```bash
git ls-files | grep -i -E 'suess|süß|suss' || echo "OK: no such file"
```

**SOURCE.md required fields per source** (License, Retrieved,
Origin/Direct permalink; attribution may live in per-file lines):

```bash
for d in data/sources/*/; do
  s="${d}SOURCE.md"
  if [ ! -f "$s" ]; then echo "MISSING: $s"; continue; fi
  ok=1
  for field in 'License' 'Retrieved' 'Origin\|Direct'; do
    grep -q -i "$field" "$s" || { ok=0; echo "$s: missing field: $field"; }
  done
  [ "$ok" -eq 1 ] && echo "OK: $s"
done
```

**Every tracked data file is metadata or covered by a SOURCE.md, and
every source is indexed in DATA_PROVENANCE.md:**

```bash
git ls-files data/ | grep -v -E '(SOURCE\.md|README\.md|DATA_PROVENANCE\.md|fetch_[a-z_]+\.py)$' | while read f; do
  d=$(dirname "$f")
  if [ -f "$d/SOURCE.md" ]; then echo "covered by SOURCE.md: $f"; else echo "UNCOVERED: $f"; fi
done
for d in data/sources/*/; do id=$(basename "$d"); grep -q "$id" data/DATA_PROVENANCE.md && echo "OK in index: $id" || echo "MISSING from index: $id"; done
```

## 2 · Judging the hits

Every binary-sweep hit must be one of:

1. **PD/CC0 source bytes** under `data/sources/<id>/` with a complete
   `SOURCE.md` next to them.
2. **Own-hand samples** under `data/samples/own-hand/` (author's
   copyright, SOURCE.md).
3. **Bundled fonts** covered by `app/THIRD_PARTY_NOTICES.md` (note:
   it lives under `app/`, not the repo root) with license texts in
   `app/public/fonts/`.
4. **Own-created assets** (e.g. `app/src/assets/paper-grain.png`) —
   own expression, MIT-covered.

Anything else — and any hidden-payload, history, or notices finding —
is judged against the rules in `quellen-und-rechte.md` /
`datenablage.md` (read fresh, don't paraphrase from memory). Two
judgment flags that greps can't raise:

- Code or docs that *describe* extracting from a copyrighted teaching
  book are a red flag even with no file committed — the derived
  geometry would be the protected expression.
- `data/derived/from-cc-by/` commits need the attribution carried in
  the derived artifact itself, not only in the source's SOURCE.md.

## Verified baseline (2026-06-10)

Binary sweep returns exactly five tracked files, all accounted for:
`data/sources/loth-1866/chart.{jpg,svg}` (PD, SOURCE.md complete),
`app/src/assets/fonts/gl-germancursive.woff2` (notices),
`app/src/assets/paper-grain.png` (own), plus one known wart:
`docs/reference/gl-germancursive.woff2` — an **orphaned duplicate**
(license-clean but unreferenced; the prototype HTML embeds the font
as base64 instead; same git blob as the assets copy). History is
clean (the comm check is empty; deleted paths are own code plus
`mvp/canonical/*.json`, author-traced geometry over the PD chart).
Both `@fontsource` packages are in the notices. All other checks
print only OK lines.

## Gotchas

- **Filter on the type field, not the whole `file` line.** The path
  `data/sources/…` contains the word "source", so a naive
  `grep -v source` over `file` output silently drops `chart.jpg` —
  that's why the type net uses `awk -F': +'` on field 2.
- **`git check-ignore` with several paths exits 0 if any one is
  ignored** — always loop per path (see battery).
- **Don't rely on the size ranking to catch data-URIs** — the known
  64 KB embedding sits mid-list and new ones can be smaller; the
  direct `;base64,` grep is the detector.
- **A `git rm` does not purge history** — that's what the history
  sweep exists for. If it ever returns a protected blob, stop:
  publishing still exposes it; the user must decide on a history
  rewrite before going public.

## Troubleshooting

- A sweep hit has no SOURCE.md and no notices entry → that *is* the
  finding; report it with the bucket you expected it to land in, and
  do not delete it yourself.
