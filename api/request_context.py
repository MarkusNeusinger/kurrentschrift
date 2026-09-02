"""Request-scoped helpers shared across routers and middleware.

Mirrors `api/request_context.py` in the sister project anyplot. Two functions
that answer OPPOSITE questions about the same request and must never be merged:
`rate_limit_key` keys the `/write/word` bucket (`api/rate_limit.py`) and builds
from the RIGHTMOST forwarded entry, `visitor_ip` keys analytics and takes the
leftmost. Each docstring says why.
"""

import ipaddress

from fastapi import Request


def rate_limit_key(request: Request) -> str:
    """The bucket key for rate limiting — deliberately not `visitor_ip`, and
    deliberately not a single header either.

    Two headers, joined, because neither alone is both trustworthy AND
    per-client on both paths this service is reachable on:

    1. **The rightmost VALID `x-forwarded-for` entry** — appended by the hop
       that actually accepted the TCP connection, so it cannot be forged: a
       client-supplied prefix stays to its left. Behind Cloudflare that is a
       Cloudflare edge address, shared by many visitors, which is why it cannot
       be the whole key. Non-addresses (`unknown`, empty entries from a
       malformed "1.2.3.4, ") are skipped, so nobody can force everyone into
       one shared bucket by sending garbage. `request.client.host` is the last
       resort when there is no forwarded header at all.
    2. **`cf-connecting-ip`** — on proxied traffic Cloudflare overwrites
       whatever the client sent, so it is the real visitor and gives the key
       its per-client resolution. On its own it is NOT safe: both Cloud Run
       services stand with `ingress=all`, and a caller reaching the `run.app`
       URL directly writes that header itself.

    Joined, each closes the other's hole. A caller on the `run.app` path who
    forges `cf-connecting-ip` to a victim's address still carries its OWN
    address in the first half of the key, and the victim's requests (which come
    through Cloudflare and therefore carry a Cloudflare edge address there) can
    never land in the same bucket. Impersonation is out; all that is left is
    scattering one's own requests across buckets, which is no better than
    rotating source IPs and is what the bucket table's eviction is sized for.

    This is where the sister project's `client_ip` is deliberately NOT copied:
    anyplot returns `cf-connecting-ip` first and argues the forgery only
    scatters the caller's own requests. That holds only where the origin cannot
    be reached without the edge — here it can, so the same forgery lands in a
    victim's bucket (Copilot review, PR #481). Transfer candidate back to
    anyplot if its origin is ever reachable directly.
    """
    hop = _rightmost_valid_forwarded(request) or (request.client.host if request.client else "")
    cf_ip = request.headers.get("cf-connecting-ip", "").strip()
    return f"{hop}|{cf_ip}" if _is_ip(cf_ip) else hop


def _rightmost_valid_forwarded(request: Request) -> str:
    """The last real address in `x-forwarded-for`, or "" if there is none."""
    for entry in reversed(request.headers.get("x-forwarded-for", "").split(",")):
        candidate = entry.strip()
        if _is_ip(candidate):
            return candidate
    return ""


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
    geolocation bucket, where forging the rate-limit key would lock people out.

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
