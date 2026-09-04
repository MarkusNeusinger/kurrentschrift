# Prime

> Lightweight orientation for everyday work on kurrentschrift. CLAUDE.md is auto-loaded — the repository map, the strict rules (German docs / English code, data-licensing tripwires, analysis-by-synthesis architecture) and the skill routing are already in context. This command adds only what CLAUDE.md cannot: the live state of the working tree, the PRs and the Auftragskorb.

## Run

```bash
git status --short --branch
git log --oneline -5
gh pr list --limit 5 2>/dev/null || echo "(no gh — on Claude Code web, list PRs via mcp__github__list_pull_requests instead)"
# The Auftragskorb: what the admin filed for a session to work off. Quiet
# without a token — nothing here blocks orientation.
[ -n "$ADMIN_TOKEN" ] && curl -fsS -H "X-Admin-Token: $ADMIN_TOKEN" \
  "https://api.kurrentschrift.ink/work-items?status=open" | python3 -c 'import json,sys
rows=json.load(sys.stdin)
print("Auftragskorb:", len(rows), "offen")
for r in rows: print("  #%s %s %s — %s" % (r["id"], r["kind"], r.get("glyph_key") or r.get("word") or "", r["note"][:60]))'
```

> If the basket is not empty and the user has not said otherwise, ask
> whether to work it off — the workflow is `/work-basket` (protocol in
> `docs/proposals/optimierungs-werkbank.md` §5). Filed tasks are the
> admin's replacement for screenshots; leaving them unread is how they
> silently rot.

> **Environment note:** locally the `gh` CLI is available; on Claude
> Code on the web it is **not** — use the GitHub MCP tools
> (`mcp__github__*`, loaded via `ToolSearch`) for any PR/issue/CI work
> there. `/open-pr` §0 has the full `gh` ↔ MCP mapping.

## Need more?

Everything descriptive lives elsewhere and is kept current there — this file
deliberately duplicates none of it:

- **The repo map, the rules, the skill routing** — `CLAUDE.md` (auto-loaded).
- **Where a module sits and what it does** — `docs/concepts/architektur.md`
  (§1 indexes all sections) and the pipeline walk-through in
  `docs/concepts/vom-scan-zum-schreiben.md`.
- **A single term** — `docs/reference/kurzglossar.md` (the 77 that occur in
  code and PRs), `docs/reference/glossar.md` for the full entry with its
  module anchor.
- **Which sections a given kind of work needs** — the reading-path table in
  `CLAUDE.md` § „Read these before substantive work“.
- **The public-UI build spec** — `docs/concepts/design-system.md` (binding).
- **Data and licensing** — `docs/reference/quellen-und-rechte.md` +
  `docs/reference/datenablage.md`.
- **Milestones** — `docs/concepts/mvp-roadmap.md`.
- **Tools** — `docs/reference/werkzeuge.md`.
- `/start` — start backend + frontend dev servers in the background.

The authoring wizard's own steps are defined in
`app/src/sections/admin/setup-wizard/wizardTypes.ts` (`STEPS`); read them
there rather than from a list that drifts.
