"""Request-scoped helpers shared across routers and middleware.

Mirrors `api/request_context.py` in the sister project anyplot; only the
analytics half is needed here (there is no rate limiter keyed by client IP
yet — when one arrives, its `client_ip` takes the RIGHTMOST forwarded entry
for the reasons anyplot documents, and the two must not be merged).
"""

import ipaddress

from fastapi import Request


def visitor_ip(request: Request) -> str:
    """Resolve the IP to report to analytics.

    Plausible documents that it uses "the first valid IP address from the
    list" and that "if you forward a server, hosting provider, or CDN IP
    address instead of the actual visitor IP, Plausible's bot filtering will
    drop the event". So this takes the LEFTMOST valid forwarded entry — the
    actual visitor — never the rightmost, which is our own infrastructure and
    would get every event silently discarded (anyplot found out by sending
    probe events and watching them vanish).

    Spoofing is not a concern in this direction: a forged value skews a
    geolocation bucket, nothing more.

    Order: the leftmost valid `x-forwarded-for` entry FIRST — then
    `cf-connecting-ip`, then the socket peer. Not the other way round, as
    anyplot has it: on this host the crawler reads arrive through the site's
    nginx (Cloud Run app → Cloudflare → this API), so `cf-connecting-ip` is
    that container's Google egress address, and Plausible drops events
    forwarded with a hosting-provider IP — verified 2026-08-28 with probe
    events (34.90.x / 35.204.x dropped, a home IP kept): nearly every crawler
    read vanished. nginx forwards the crawler in `x-forwarded-for`
    (app/nginx.conf `@seo_proxy`); for a direct client behind Cloudflare the
    leftmost entry and `cf-connecting-ip` are the same address anyway.
    """
    for entry in request.headers.get("x-forwarded-for", "").split(","):
        candidate = entry.strip()
        if _is_ip(candidate):
            return candidate
    cf_ip = request.headers.get("cf-connecting-ip", "").strip()
    if _is_ip(cf_ip):
        return cf_ip
    return request.client.host if request.client else ""


def _is_ip(value: str) -> bool:
    """Whether the token is a real address.

    Proxies do insert non-addresses — `unknown` is the classic — and Plausible
    uses "the first **valid** IP address from the list". Forwarding a
    non-address gets the event discarded or mis-located, so a malformed entry
    is skipped rather than passed on.
    """
    if not value:
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True
