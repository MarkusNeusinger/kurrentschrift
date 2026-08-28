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

    Order: `cf-connecting-ip`, which Cloudflare overwrites on proxied traffic
    and is therefore both real and unforgeable; then the leftmost valid
    `x-forwarded-for` entry; then the socket peer.
    """
    cf_ip = request.headers.get("cf-connecting-ip", "").strip()
    if _is_ip(cf_ip):
        return cf_ip
    for entry in request.headers.get("x-forwarded-for", "").split(","):
        candidate = entry.strip()
        if _is_ip(candidate):
            return candidate
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
