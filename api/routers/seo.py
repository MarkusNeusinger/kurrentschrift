"""Machine-facing files of the API host: `robots.txt`.

Same slot as `api/routers/seo.py` in the sister project anyplot (which also
serves its crawler pages from here). The SITE's crawler policy is the static
`app/public/robots.txt` with its doctrine in docs/reference/crawler-richtlinie.md;
this file states the policy of `api.kurrentschrift.ink`, the host llms.txt
advertises as the machine interface (/docs, /openapi.json, the /write renders).
"""

from fastapi import APIRouter, Response

from api.http import CACHE_CONTROL


router = APIRouter(tags=["seo"])

# Nothing on this host is off-limits by robots rule — a robots line protects
# nothing and only stops the compliant assistants that llms.txt invites (the
# lesson anyplot's AI-access audit of 2026-08-19 drew from its old blanket
# Disallow). Everything reserved — the authored templates, the occurrences,
# the bboxes, the hands, the own-hand strips — is gated by AUTHENTICATION
# (`require_admin`), so a crawler gets 401 there whatever this file says.
#
# The one signal that differs from the site's robots.txt: `ai-train=no`. The
# composed geometry the public /write endpoints return is derived from the
# reserved dataset — it is product surface to retrieve and cite, not training
# material (README "License", docs/reference/quellen-und-rechte.md §5). The
# site's own text is open to training; this host's payloads are not.
ROBOTS_TXT = (
    "# api.kurrentschrift.ink — the open read API of kurrentschrift.ink.\n"
    "# Reserved data is gated by authentication, not by this file; the public\n"
    "# /write renders derive from that data and stay out of model training.\n"
    "User-agent: *\n"
    "Content-Signal: search=yes,ai-input=yes,ai-train=no\n"
    "Allow: /\n"
)


@router.get("/robots.txt", include_in_schema=False)
async def get_robots() -> Response:
    return Response(
        content=ROBOTS_TXT, media_type="text/plain; charset=utf-8", headers={"Cache-Control": CACHE_CONTROL}
    )
