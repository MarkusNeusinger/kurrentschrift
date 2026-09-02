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
git grep -nIE ';base64,[A-Za-z0-9+/]{200,}' -- . ':!.claude/skills/audit-licenses/SKILL.md' || echo "OK: no embedded data-URI payload"
git grep -nE '<image|data:image' -- '*.svg' || echo "OK: no raster payload in tracked SVGs"
```

**Match the payload class, not a file list.** A bare `;base64,` grep hits
every generator in the repo — the tools and tests that BUILD a data-URI at
runtime (`"data:image/png;base64," + b64encode(...)`) — and the exclusion
list to suppress them has to grow with each new generator. It had fallen
five files behind by 2026-09-02, so the OK branch could never fire and each
run ended in hits a human re-judged by hand. The length bound is the honest
discriminator instead: a real embedded payload carries hundreds of literal
base64 characters right after the marker, while a generator has an
identifier or a quote there. Verified 2026-09-02 — zero hits repo-wide,
and it still catches a synthetic 400-character embedding.

**History** — publishing exposes every blob ever committed, not just
HEAD. First command: binaries that existed but are gone from HEAD
(must be empty). Second: all deleted paths, eyeballed for protected
names:

```bash
comm -23 <(git rev-list --objects --all | awk '{print $2}' | grep -iE '\.(png|jpe?g|woff2?|ttf|otf|eot|pdf|gif|webp|zip|tar|t?gz|bz2|xz)$' | sort -u) <(git ls-files | sort)
git log --diff-filter=D --name-only --pretty=format: | sort -u
```

**Those two nets only see BINARY extensions and deleted paths — the
reserved dataset leaks as text.** The learned data travels as JSON or
TypeScript, so a third net searches history by CONTENT for the payload keys
that only a template dump carries:

```bash
for pat in skeleton_polyline_px pixel_anchors half_widths_px anchors_template outline_paths; do
  echo "== $pat"; git log --all -S"$pat" --diff-filter=A --name-only --pretty=format:'%h %ad %s' --date=short
done
```

**The rule: a hit under `core/`, `api/`, `app/`, `tools/`, `tests/`,
`docs/`, `alembic/` or `.claude/` is code, a test or prose about the
format — anything else is a finding**, because nothing outside those trees
has a reason to carry a rendered template.

**This net is now a test, so run the test rather than the loop above:**
`uv run --extra test pytest tests/test_reserved_history.py`. It walks every
blob ever committed outside the code trees and reports each one carrying a
render payload — a payload key AND a long run of numbers, so a mere mention
of a field name in prose or in a generator script does not fire. The blobs
already on record are pinned there by hash; anything else fails.

`.design-sync/previews/_writtenGlyphData.ts` (added 2026-06-20 in 84c6332 /
PR #108, 32219 bytes, the diagnostic payloads of two templates; removed
from HEAD 2026-07-31 by PR #254 but NOT from history, and the repo has been
public since 2026-05-19) is **known and ACCEPTED — author's decision of
2026-09-02, documented in `docs/reference/quellen-und-rechte.md` §5. Do not
re-report it as a finding and do not propose a purge again**: rewriting a
public `main` would not unmake the copies that clones and forks already
hold, the README reservation stays the legal boundary either way, and what
is actually prevented is the repetition. The same holds for the four
`mvp/canonical/*_v0.json` blobs of the pre-DB prototype — **accepted on
2026-09-03 on the same reasoning**, likewise settled, likewise not to be
re-raised.

Adding a hash to that allowlist is a licensing decision of the author's,
never a way to get a red test green. The binary-extension net above cannot
see a `.ts` or `.json` file at all, which is why this class went unreported
for two months.

**Bundled fonts vs. notices** — since 2026-08-27 the Garamond/Playfair
subsets are self-hosted as TRACKED verbatim copies in `app/public/fonts/`
(the `@fontsource/*` packages remain devDependencies as source and update
channel; nothing in `app/src` imports them anymore). Check both directions:
every tracked font file is covered by `app/THIRD_PARTY_NOTICES.md`, and the
copies still match their package source byte-for-byte:

```bash
for f in $(git ls-files 'app/public/fonts/*.woff2' 'app/public/fonts/*.ttf'); do b=$(basename "$f"); grep -qE "(fonts/|files/)?$b|@fontsource" app/THIRD_PARTY_NOTICES.md && echo "OK covered: $b" || echo "MISSING from notices: $b"; done
cd app && npm run fonts:sync && git diff --exit-code public/fonts/ && node -p '"OK: copies byte-identical to @fontsource v" + require("./node_modules/@fontsource/eb-garamond/package.json").version'
```

**No protected work as a file** (prose mentions are bibliographic
references and explicitly allowed; files are not):

```bash
git ls-files | grep -i -E 'suess|süß|suss' || echo "OK: no such file"
```

**SOURCE.md required fields per source** (License, Retrieved,
Origin/Direct permalink; attribution may live in per-file lines):

```bash
for d in data/sources/*/ data/corpora/*/ data/samples/*/ data/humanbench/ data/variants/*/; do
  [ -d "$d" ] || continue
  s="${d}SOURCE.md"
  if [ ! -f "$s" ]; then echo "MISSING: $s"; continue; fi
  ok=1
  for field in 'License' 'Retrieved' 'Origin\|Direct'; do
    grep -q -i "$field" "$s" || { ok=0; echo "$s: missing field: $field"; }
  done
  [ "$ok" -eq 1 ] && echo "OK: $s"
done
```

**Every recorded SHA256 still matches its bytes** — the only net that
catches a source image quietly swapped for a different one:

```bash
for s in data/sources/*/SOURCE.md; do
  d=$(dirname "$s")
  grep -E '^- SHA256:' "$s" | grep -oE '[0-9a-f]{64}' | while read h; do
    found=""
    for f in $(find "$d" app/src/assets/specimens -type f ! -name '*.md' 2>/dev/null); do
      [ "$(sha256sum "$f" | cut -d' ' -f1)" = "$h" ] && found="$f"
    done
    [ -n "$found" ] && echo "OK hash: $found" || echo "UNMATCHED hash in $s: ${h:0:16}…"
  done
done
```

Anchor on `^- SHA256:` specifically: a `Source-SHA256:` line records the
hash of the UPSTREAM original (the DNB page scan behind Abb. 22), which by
design has no counterpart in the repo and would otherwise report as
unmatched forever. Where a source ships a `SHA256SUMS` file — the 22
Leitfaden pages — `sha256sum -c SHA256SUMS` inside that directory is the
equivalent check. All 12 recorded hashes verified on 2026-09-02.

**Sweep every `data/` subtree, not just `data/sources/`.** Both this loop
and the index loop below used to run over `data/sources/*/` alone, so
`corpora/`, `samples/` and `humanbench/` were never checked — that blind
spot is exactly how the one source with real copyleft obligations
(`igerman98`, GPL 2/3) stayed out of the index unnoticed. Note the two
field sets when judging a hit: third-party sources additionally owe
Origin/Direct/SHA256/Processing per file, while own collections
(`own-hand`, `humanbench`) legitimately have no external file and no
SHA256 — a naive hash requirement produces false MISSING lines there.

**Every tracked data file is metadata or covered by a SOURCE.md, and
every source is indexed in DATA_PROVENANCE.md:**

```bash
git ls-files data/ | grep -v -E '(SOURCE\.md|README\.md|DATA_PROVENANCE\.md|fetch_[a-z_]+\.py)$' | while read f; do
  d=$(dirname "$f")
  if [ -f "$d/SOURCE.md" ]; then echo "covered by SOURCE.md: $f"; else echo "UNCOVERED: $f"; fi
done
for d in data/sources/*/ data/corpora/*/ data/samples/*/ data/humanbench/ data/variants/*/; do
  [ -d "$d" ] || continue; id=$(basename "$d")
  grep -q "$id" data/DATA_PROVENANCE.md && echo "OK in index: $id" || echo "MISSING from index: $id"
done
```

**Derived images shipped from the app tree need provenance too.** The
loops above only walk `data/`, so a PD excerpt cropped into
`app/src/assets/` is invisible to them although it is publicly served:

```bash
for f in app/src/assets/specimens/*; do
  b=$(basename "$f")
  grep -rqF "$b" data/sources/*/SOURCE.md 2>/dev/null && echo "OK provenance: $b" || echo "NO PROVENANCE: $b"
done
```

Every file there must be named in some `data/sources/*/SOURCE.md`, with its
derivation (which region of which original, scaling, quality), its
dimensions and its SHA256 — `datenablage.md` §2 requires both for any
altered original.

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

Binary sweep returned exactly five tracked files at the time, all
accounted for: `data/sources/loth-1866/chart.{jpg,svg}` (PD, SOURCE.md
complete), `app/src/assets/fonts/gl-germancursive.woff2` (notices),
`app/src/assets/paper-grain.png` (own), plus one known wart:
`docs/reference/gl-germancursive.woff2` — an orphaned duplicate of the
assets copy, **deleted together with the landing prototype in #209**
(the base64 exclude above moved accordingly). Sources committed since
(Sütterlin 1922 incl. plates + Leitfaden pages, Koch 1928,
Petzendorfer 1889, humanbench judgements) each carry their own
SOURCE.md and grow this list — re-run the sweep, don't trust the
count. History is
clean (the comm check is empty; deleted paths are own code plus
`mvp/canonical/*.json`, author-traced geometry over the PD chart).
Both `@fontsource` packages are in the notices. Since 2026-08-27 the
sweep additionally finds 18 tracked font binaries under
`app/public/fonts/`: 16 verbatim @fontsource v5.3.0 woff2 subsets
(EB Garamond + Playfair Display, latin/latin-ext — byte-identity is the
license condition, verified by `npm run fonts:sync`) plus the two show
fonts moved there from `app/src/assets/fonts/`
(`gl-germancursive.woff2`, `suetterlin-hjz-1911.ttf`) — all covered by
the notices.

**Re-verified 2026-09-02** (full battery, read-only): 7 sources under
`data/sources/` each with a complete SOURCE.md, every SHA256 recorded there
matching its bytes, `sha256sum -c SHA256SUMS` green for the 22 Leitfaden
pages, gitignore boundaries holding for own-hand/corpora/bench fixtures, no
raster payload in a tracked SVG, the Süß check empty, and 18 font binaries
all covered by the notices. Two nets were rebuilt in the same pass and are
the reason this section is dated twice: the base64 net now matches the
payload class instead of an exclusion list (it had fallen five files
behind), and the history sweep gained the content pickaxe that finally
names `.design-sync/previews/_writtenGlyphData.ts`. Both items that opened
on that day are closed: the `igerman98` index gap was filled, and that blob
was ACCEPTED by the author on 2026-09-02 and pinned in
`tests/test_reserved_history.py`. The same net then surfaced four
`mvp/canonical/*_v0.json` blobs of the pre-DB prototype, which the author
accepted on 2026-09-03 on the same reasoning; they are pinned there too.
Nothing in the history battery is open — everything prints only OK lines.

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
