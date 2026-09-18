### Added

- **The path form of the word reads: `GET /sources/{id}/write/word/{text}`
  and `…/write/word/{text}.svg`.** The same answer as `?text=…`, with the
  text as the last path segment — for clients that lose the query string on
  the way. A strict AI fetch client (Claude's web_fetch, 2026-09-18)
  normalises an unseen URL to the closest one it has already seen and drops
  the query; the API then answers a correct 422 that such a client shows
  only as a status code, so an assistant asked to show a word in Sütterlin
  failed silently. Cache-key normalisation and corporate proxies do the
  same, so the fix removes the failure mode rather than working around one
  client. The query form stays; the narrow rate-limit bucket meters the
  path form by its text like the query form (`api/rate_limit.py`), the
  public/reserved split lists both routes, and llms.txt plus the Tafel
  page's machine block carry ready-made example URLs, because the same
  client also refuses paths it has never seen.

### Changed

- **A 422 for a request that arrived with no query string at all says so.**
  When every reported problem is a missing query parameter and the request
  carried no query, the body is `{"error": "no_query_string", "missing":
  [...], "hint": ...}` with the path form named where the route has one
  (`api/http.py::no_query_string_body`), `private, no-store`, instead of
  FastAPI's default `detail` list; every other validation failure keeps
  that list. The hint is conditional — the server sees only that no query
  arrived, not who lost it — and llms.txt keys its one-line rule on the
  `error` value, not on the status: a 422 carrying `no_query_string` means
  the query string was lost on the way, use the path form. Agents read
  that file before they touch the API. The bot asset telemetry
  (`classify_asset`) counts the path form under the same `word_svg` /
  `word_json` assets as the query form.
