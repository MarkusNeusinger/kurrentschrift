"""Rebuild the frozen word-bench fixtures over the DEPLOYED API — no DB needed.

`export_fixtures.py` is the canonical exporter and reads Cloud SQL directly.
Wherever that egress is closed — a claude.ai/code cloud session, a laptop
without DB credentials — the same fixture roots can be rebuilt from the READ
endpoints of https://api.kurrentschrift.ink. This module is that sibling, not a
modification: it writes the SAME roots in the SAME layout, imports the
exporter's own helpers (`load_sidecar_entries`, `freeze_entry`, `_shape_entry`,
`pair_instances_payload`, `_write_pair_instances`, `_set_name`, …) instead of
restating them, and only replaces the DB block with HTTP GETs. Everything the
runner, `pairmeas`, `wordlab` and `pairlab` read therefore stays byte-compatible.

Read map (every call is a GET; nothing here ever writes to DB or API):

    crop / ref_mask.png / ref_skel.npz  local page bytes + words.json    -
    slots (word.json)                   local core.shaping               -
    style_ratio / style_id              GET /sources/{id}                public
    width_resolver                      GET /styles/{style_id}           public
    glyph inventory                     GET /sources/{id}/templates      public
    templates.json                      GET /sources/{id}/templates/{k}  ADMIN
    templates_laufform.json             GET …/templates/{k}?variant=100  ADMIN
                                        (fallback: /hands/{h}/aggregates) ADMIN
    constant_nib_units                  GET /sources/{id}/render-context ADMIN
                                        (fallback: …/write/glyphs)       public
    pair_instances.json                 GET /sources/{id}/pair-instances ADMIN
    word_instances.json                 GET /sources/{id}/word-instances ADMIN

The occurrence reads joined the ADMIN column on 2026-08-28 (reserved dataset,
quellen-und-rechte.md §5) — in practice no change for a fixture rebuild, which
needed `ADMIN_TOKEN` for the templates all along.

Two artifacts have two provenances; the manifest says which:

* the LAUFFORM_VARIANT rows — read VERBATIM off the stored variant-100
  templates via the `variant` parameter on the single-template GET
  (`laufform_precision: "stored"`, issue #311: read, don't rebuild — the same
  philosophy as the render-context nib read). A deployment predating that
  parameter silently serves the variant-0 row instead (an unknown query
  parameter is ignored), which the response's own `variant` field exposes; the
  old reconstruction then takes over (`"reconstructed"`): each row is rebuilt
  from the chart row plus the aggregate's `laufform_anchors` through the very
  function the write path uses, `api.routers.templates.build_laufform_canonical`.
  That rebuild is byte-true only while the chart row still matches the one the
  apply step derived from — a resample between apply and fetch shifts
  `trace_meta`/widths/entry/exit under the reconstruction, which is exactly the
  divergence #311 measured.
* `constant_nib_units` — the source-pooled Gleichzug nib is a DB aggregate over
  ALL templates of the source, including variant rows no read endpoint serves.
  The admin-gated `GET /sources/{id}/render-context` returns it unrounded
  (`"nib_precision": "exact"`), which is what this module asks for first. An API
  deployment that predates that endpoint 404s, and the old reconstruction takes
  over: under `width_resolver == "constant"` the render payload sets every half
  width to exactly the nib, so a one-glyph `/write/glyphs` readback recovers it
  — at the payload's 4-decimal rounding (`"nib_precision": "4dp-readback"`,
  ≤5e-5 xh). The nib does not enter any centerline, only mask/stroke widths.

Because a wrong reconstruction would be invisible in a diff, `--verify` is the
acceptance gate, in two layers (see `verify`): every rebuilt row is rendered
locally and held against `GET /write/glyphs` (bit-exact), and rebuilt cases are
composed locally and held against `GET /write/word` — letter shape bit-exact,
and glyph placement bit-tight too on an `exact` nib (only a 4dp readback is
allowed the jitter it causes). A mismatch is a hard failure. The gate compares
the full fixture rows: since issue #289 the write path builds its rows through
the same `core.database.models.template_render_row` shape, `glyph` included,
so the fluent body widening (`core.pipeline._fluent_widen`) applies on both
sides — `--verify` therefore needs a deployed API at or after that fix. Both
layers put the API's 4-decimal wire rounding (`core.rounding`) on the LOCAL
side before comparing, so the gate measures the row and the composition and
never the serialisation.

`ADMIN_TOKEN` is read from the environment and sent as `X-Admin-Token`. It is
never printed, logged or echoed into an error message.

Usage:
    uv run python -m tools.wordbench.fetch_fixtures --source suetterlin-1922 \
        --set all --api https://api.kurrentschrift.ink
    uv run python -m tools.wordbench.fetch_fixtures --set all --verify
    uv run python -m tools.wordbench.fetch_fixtures --set all --verify --no-fetch
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import time
import urllib.error
import urllib.request
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

import numpy as np

from api.routers.templates import build_laufform_canonical
from api.routers.write import MAX_BATCH_KEYS
from core.database.models import LAUFFORM_VARIANT
from core.rounding import round_wire_numbers
from core.shaping import GlyphSlot, glyph_keys_of
from tools.wordbench.export_fixtures import (
    DEFAULT_OUT_DIR,
    DEFAULT_SOURCE_ID,
    ONLY_CHOICES,
    REPO_ROOT,
    _entry_id,
    _kind,
    _refresh_instance_artifacts,
    _root_name,
    _set_name,
    _shape_entry,
    _write_pair_instances,
    _write_word_instances,
    freeze_entry,
    load_page,
    load_sidecar_entries,
)


DEFAULT_API_BASE = "https://api.kurrentschrift.ink"
# Cloudflare rejects the stdlib default agent; name the tool instead.
USER_AGENT = "kurrentschrift-fetch-fixtures/1.0"
RETRY_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})
RETRY_BACKOFF_S = 0.75
# What the manifest records about the nib's provenance (see the module docstring).
NIB_EXACT = "exact"  # read unrounded off GET /sources/{id}/render-context
NIB_READBACK = "4dp-readback"  # recovered from a rounded /write/glyphs payload
NIB_NONE = "none"  # no pooled nib exists (a pressure/broad-nib source)
# … and about the Laufform rows' provenance (issue #311, see the module docstring).
LAUFFORM_STORED = "stored"  # the variant-100 rows themselves, verbatim
LAUFFORM_RECONSTRUCTED = "reconstructed"  # rebuilt from the hand's aggregates (older API)
# Provenance stamped into the reconstructed Laufform rows' `trace_meta.laufform`.
LAUFFORM_META = {"derived_from": "hand-aggregates", "via": "fetch_fixtures"}
# The verify gate needs a real sample, not a token one (plan §B6: ≥10 cases).
MIN_VERIFY_CASES = 10
DEFAULT_VERIFY_CASES = 12
# Letter SHAPE must be bit-exact: a rebuilt row and the stored row go through
# the same renderer, so any difference beyond float noise is a wrong row.
DEFAULT_SHAPE_TOL = 1e-9
# Glyph PLACEMENT is the one thing the nib's 4-decimal readback does perturb.
# Placement reads the silhouette rings (simplified capsule unions), where a
# 5th-decimal width change can flip a knife-edge ink-clearance decision — the
# effect is chaotic, not monotone, so it cannot be calibrated away by rounding
# the readback differently, only by learning the nib itself. Observed maximum
# over 30 cases across all three sets: 0.0148 xh, zero for every isolated
# letter pair. This bound is twice that, and a real reconstruction error lands
# in the SHAPE channel anyway (a stale Laufform row moves anchors by ~0.07 xh
# WITHIN the glyph).
DEFAULT_PLACEMENT_TOL = 0.03
# With an `exact` nib there is no approximated input left: local and served
# render from identical numbers through identical code, so placement is
# reproducible bit-for-bit and the gate says so. Measured before the endpoint
# existed, by sweeping the nib across the readback bracket [0.07305, 0.07315]
# and composing 12 pair cases against /write/word at each step: at one value
# near 0.0730988 — and only there — all 12 matched with a worst placement
# deviation of exactly 0.0, while the readback's 0.0731 left 5 of them off by up
# to 1.3e-3. The plateau is narrow (a 4e-16 change of that value already flips
# three of the cases: the ink-clearance decision reads silhouette rings rounded
# to 2 decimals, so a tie at that boundary tips either way), which is precisely
# why the nib has to be TRANSPORTED rather than estimated — JSON round-trips a
# double exactly, an estimate cannot. Applies per fixture root (the manifest
# records the provenance); an explicit --placement-tol wins.
EXACT_PLACEMENT_TOL = 1e-9


class ApiClient:
    """Read-only JSON client: GETs only, retried with exponential backoff.

    Deliberately stdlib-only — `requests`/`httpx` are not project dependencies —
    and deliberately without any write verb, so this module cannot mutate the
    deployed system even by accident. Proxy settings come from the environment
    (urllib's default `getproxies`); a custom CA bundle from `SSL_CERT_FILE` or
    `REQUESTS_CA_BUNDLE`. Verification is never disabled.
    """

    def __init__(self, base_url: str, *, token: str | None = None, timeout: float = 120.0, retries: int = 4) -> None:
        self.base_url = base_url.rstrip("/")
        if not self.base_url.startswith("https://"):
            # The admin token travels in a header; never allow a scheme that could carry it in plaintext.
            raise SystemExit(f"API base must be https://, got {self.base_url!r}")
        self.timeout = timeout
        self.retries = retries
        self._token = token or None
        # Refusing redirects keeps the admin header from ever being resent to a
        # host other than base_url; build_opener keeps the environment's proxy
        # handlers. A 3xx therefore fails hard instead of being followed.
        self._opener = urllib.request.build_opener(
            _NoRedirectHandler(), urllib.request.HTTPSHandler(context=_ssl_context())
        )

    def get(
        self, path: str, params: dict[str, Any] | None = None, *, admin: bool = False, allow_404: bool = False
    ) -> Any:
        """GET one JSON document. `None` on 404 when `allow_404`; SystemExit otherwise."""
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        if admin:
            if not self._token:
                raise SystemExit(f"GET {path} is admin-gated — set ADMIN_TOKEN in the environment")
            headers["X-Admin-Token"] = self._token

        last = ""
        for attempt in range(self.retries + 1):
            try:
                request = urllib.request.Request(url, headers=headers, method="GET")  # noqa: S310 — https, fixed scheme
                with self._opener.open(request, timeout=self.timeout) as response:
                    return json.loads(response.read())
            except urllib.error.HTTPError as exc:
                if exc.code == 404 and allow_404:
                    return None
                if exc.code not in RETRY_STATUS:
                    # The token lives in a header only — no URL or reason can carry it.
                    raise SystemExit(f"GET {url} → HTTP {exc.code} {exc.reason}") from None
                last = f"HTTP {exc.code} {exc.reason}"
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                last = f"{type(exc).__name__}: {exc}"
            if attempt < self.retries:
                time.sleep(RETRY_BACKOFF_S * 2**attempt)
        raise SystemExit(f"GET {url} failed after {self.retries + 1} attempts ({last})")


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Turn every 3xx into an HTTPError instead of following it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, ANN201
        return None


def _ssl_context() -> ssl.SSLContext:
    ca_bundle = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    return ssl.create_default_context(cafile=ca_bundle) if ca_bundle else ssl.create_default_context()


# --------------------------------------------------------------- pure mappers


@dataclass
class _ChartTemplateView:
    """Attribute view of a fetched chart row for `build_laufform_canonical`.

    That function is the ONE derivation of a running-form row and takes the ORM
    `Template`; sharing it (rather than copying its arithmetic) is the whole
    point, so the fetched dict is presented with the attributes it reads.
    """

    glyph: str
    anchors: list[list[float]]
    half_widths: list[float]
    advance: float
    entry: dict = field(default_factory=dict)
    exit_pt: dict = field(default_factory=dict)
    trace_meta: dict = field(default_factory=dict)


def template_row_from_payload(payload: dict) -> dict:
    """`GET /templates/{key}` (TemplateOut) → the exporter's fixture row shape.

    Field-for-field the DB exporter's `_template_dict`, minus `updated_at`:
    the response carries no timestamp and every consumer treats that field as
    informational (`WordCase.extra`), never as geometry.
    """
    return {
        "glyph_key": payload["glyph_key"],
        "glyph": payload["glyph"],
        "advance": payload["advance"],
        "entry": payload.get("entry") or {},
        "exit_pt": payload.get("exit_pt") or {},
        "anchors": payload["anchors"],
        "half_widths": payload["half_widths"],
        "trace_meta": payload.get("trace_meta") or {},
        "updated_at": None,
    }


def laufform_row_from_payload(
    chart_row: dict,
    anchors: list[list[float]],
    meta: dict | None = None,
    *,
    end_window: float | None = None,
    transverse_only: bool | None = None,
) -> dict:
    """Reconstruct one LAUFFORM_VARIANT fixture row from the chart row + median anchors.

    Uses `api.routers.templates.build_laufform_canonical` — the same derivation
    `POST …/aggregates/apply-laufform` used to write the stored variant-100 row
    — so widths, stroke topology and the entry/exit/advance shift are identical
    by construction rather than by re-derivation. `end_window` / `transverse_only`
    override the builder's end-blend window and mode (a candidate map on the
    pre-registered ladder, §14 LF5/LF6); None keeps the builder's defaults.
    """
    kwargs: dict = {}
    if end_window is not None:
        kwargs["end_window"] = end_window
    if transverse_only is not None:
        kwargs["transverse_only"] = transverse_only
    view = _ChartTemplateView(
        glyph=chart_row["glyph"],
        anchors=chart_row["anchors"],
        half_widths=chart_row["half_widths"],
        advance=chart_row.get("advance") or 0.0,
        entry=chart_row.get("entry") or {},
        exit_pt=chart_row.get("exit_pt") or {},
        trace_meta=chart_row.get("trace_meta") or {},
    )
    canonical = build_laufform_canonical(view, anchors, dict(meta or LAUFFORM_META), **kwargs)
    return {
        "glyph_key": chart_row["glyph_key"],
        "glyph": canonical["glyph"],
        "advance": canonical["advance"],
        "entry": canonical["entry"],
        "exit_pt": canonical["exit_pt"],
        "anchors": canonical["anchors"],
        "half_widths": canonical["half_widths"],
        "trace_meta": canonical["trace_meta"],
        "updated_at": None,
    }


def laufform_rows_from_aggregates(aggregates: list[dict], templates: dict[str, dict]) -> dict[str, dict]:
    """Every reconstructable running form of one hand, keyed by glyph_key.

    Skips — loudly — what cannot be derived: a non-base variant (never a
    Laufform source), a glyph the engine has no running form for yet, and an
    anchor count that no longer matches the chart row (the same guard the
    apply endpoint applies before writing).
    """
    rows: dict[str, dict] = {}
    for aggregate in aggregates:
        key = aggregate["glyph_key"]
        anchors = aggregate.get("laufform_anchors")
        chart = templates.get(key)
        if not anchors or aggregate.get("variant", 0) != 0 or chart is None:
            continue
        if len(anchors) != len(chart["anchors"]):
            print(f"  skip laufform {key}: {len(anchors)} median anchors vs {len(chart['anchors'])} on the chart row")
            continue
        rows[key] = laufform_row_from_payload(chart, anchors)
    return rows


def stored_laufform_rows(
    client: ApiClient, source_id: str, summaries: list[dict], keys: set[str]
) -> dict[str, dict] | None:
    """The STORED variant-100 rows, verbatim (issue #311: read, don't rebuild).

    The public summary list already names every variant a glyph has, so the
    keys with a Laufform row are known without an extra probe; each row then
    comes off the admin single-template GET with `variant=LAUFFORM_VARIANT`.
    Returns None when the deployed API predates that parameter: an older
    FastAPI ignores the unknown query parameter and serves the variant-0 chart
    row instead, which its own `variant` field exposes — silently freezing a
    chart row as a Laufform would corrupt every bench number downstream.
    """
    wanted = sorted({row["glyph_key"] for row in summaries if row.get("variant") == LAUFFORM_VARIANT} & keys)
    rows: dict[str, dict] = {}
    for key in wanted:
        payload = client.get(
            f"/sources/{quote(source_id, safe='')}/templates/{quote(key, safe='')}",
            {"variant": LAUFFORM_VARIANT},
            admin=True,
        )
        if payload.get("variant") != LAUFFORM_VARIANT:
            return None
        rows[key] = template_row_from_payload(payload)
    return rows


def hand_id_for(source: dict, pair_rows: list[dict], override: str | None = None) -> str | None:
    """The hand whose statistics belong to this source.

    `sources.hand_id` is null for the teaching charts, so the hand is DERIVED
    from the occurrences exactly like the admin workbench derives it: the modal
    non-null `hand_id` over the source's measured joins.
    """
    if override:
        return override
    hands = Counter(row["hand_id"] for row in pair_rows if row.get("hand_id"))
    if hands:
        return hands.most_common(1)[0][0]
    return source.get("hand_id")


def payload_mismatch(local: dict, served: dict, tolerance: float = 1e-9) -> str | None:
    """Compare a locally rendered template payload against the served one.

    The sharp half of the gate: it holds the REBUILT ROW itself against what the
    API renders from the stored row, field for field, with no composition in
    between — so a wrong anchor, a stale Laufform derivation or a shifted
    advance shows up here rather than as a vague word-level wobble. Widths
    (`half_widths_template`, `outline_paths`) are deliberately not compared: the
    pooled nib is only readable at 4 decimals (see `pooled_nib_units`).
    """
    if abs(float(local["advance"]) - float(served["advance"])) > tolerance:
        return f"advance {local['advance']} vs {served['advance']}"
    for name in ("entry", "exit_pt"):
        a = (local.get(name) or {}).get("xy") or []
        b = (served.get(name) or {}).get("xy") or []
        if len(a) != len(b) or any(abs(x - y) > tolerance for x, y in zip(a, b, strict=True)):
            return f"{name} {a} vs {b}"
    for name in ("anchors_template", "centerlines_template"):
        a, b = local[name], served[name]
        if name == "centerlines_template":
            if len(a) != len(b) or [len(s) for s in a] != [len(s) for s in b]:
                return f"{name}: {[len(s) for s in a]} local strokes vs {[len(s) for s in b]} served"
            flat_a = [p for stroke in a for p in stroke]
            flat_b = [p for stroke in b for p in stroke]
        else:
            if len(a) != len(b):
                return f"{name}: {len(a)} local vs {len(b)} served"
            flat_a, flat_b = a, b
        deviation = float(np.abs(np.asarray(flat_a, dtype=float) - np.asarray(flat_b, dtype=float)).max())
        if deviation > tolerance:
            return f"{name} deviates by {deviation:.3g}"
    return None


def composition_mismatch(
    local_items: list[dict],
    remote_items: list[dict],
    *,
    shape_tol: float = DEFAULT_SHAPE_TOL,
    placement_tol: float = DEFAULT_PLACEMENT_TOL,
) -> tuple[str | None, float, float]:
    """Compare two composed item lists, splitting SHAPE from PLACEMENT.

    A letter item's deviation decomposes into a constant offset (where the
    composer put the glyph) and the spread around it (what the glyph looks
    like). Only the first is perturbed by the pooled nib's readback precision
    (see `DEFAULT_PLACEMENT_TOL`), so the two are measured apart and the shape
    channel stays bit-tight. A connector is GENERATED from the placement and
    inherits its jitter wholesale, so it only feeds the placement channel.
    Returns (error, worst shape deviation, worst placement deviation).
    """
    if len(local_items) != len(remote_items):
        return f"{len(local_items)} local items vs {len(remote_items)} served", float("inf"), float("inf")
    worst_shape = 0.0
    worst_placement = 0.0
    for index, (local, remote) in enumerate(zip(local_items, remote_items, strict=True)):
        a = np.asarray(local.get("centerline") or [], dtype=float)
        b = np.asarray(remote.get("centerline") or [], dtype=float)
        if a.shape != b.shape:
            return f"item {index}: {a.shape} local points vs {b.shape} served", float("inf"), float("inf")
        if not len(a):
            continue
        delta = a - b
        worst_placement = max(worst_placement, float(np.abs(delta).max()))
        if "glyph_key" in local:
            worst_shape = max(worst_shape, float(np.abs(delta - np.median(delta, axis=0)).max()))
    if worst_shape > shape_tol:
        return f"letter shape deviates by {worst_shape:.3g} > {shape_tol:g}", worst_shape, worst_placement
    if worst_placement > placement_tol:
        return f"placement deviates by {worst_placement:.3g} > {placement_tol:g}", worst_shape, worst_placement
    return None, worst_shape, worst_placement


# ------------------------------------------------------------------- fetching


def pooled_nib_units(client: ApiClient, source_id: str, width_resolver: str, keys: set[str]) -> float | None:
    """The source-pooled Gleichzug nib, read back off a render payload (§B3).

    The FALLBACK path since the API serves the value exactly (see
    `exact_nib_units`): kept because a deployment older than that endpoint must
    still be fetchable. Only meaningful for a `constant` source: there
    `render_payload_for_template` overwrites every half width with the pooled
    nib, so any authored glyph's payload carries it — rounded to the payload's
    4 decimals. A `pressure`/`broad_nib` source has no pooled nib to read back
    — the fixtures record None, exactly as those runs use it.
    """
    if width_resolver != "constant" or not keys:
        return None
    probe = "a" if "a" in keys else sorted(keys)[0]
    payload = client.get(f"/sources/{source_id}/write/glyphs", {"keys": probe})
    glyphs = payload.get("glyphs") or []
    half_widths = glyphs[0].get("half_widths_template") if glyphs else None
    return float(half_widths[0]) if half_widths else None


def exact_nib_units(client: ApiClient, source_id: str) -> float | None:
    """The pooled nib UNROUNDED, from the admin render-context read.

    The pool spans every template of the source — including variant rows no
    read endpoint serves — so it cannot be recomputed from the fetched chart
    rows; the API has to state it. `None` when the deployment predates the
    endpoint (404) or the style has no constant nib, which is exactly when the
    readback fallback applies.
    """
    context = client.get(f"/sources/{quote(source_id, safe='')}/render-context", admin=True, allow_404=True)
    if not context:
        return None
    value = context.get("constant_nib_units")
    return None if value is None else float(value)


def resolve_nib(client: ApiClient, source_id: str, width_resolver: str, keys: set[str]) -> tuple[float | None, str]:
    """The nib to freeze plus the provenance label the manifest records.

    Exact first, 4-decimal readback second — the difference is invisible in the
    fixtures but decides whether an offline composition reproduces a served one
    bit-for-bit (module docstring; `EXACT_PLACEMENT_TOL`).
    """
    if width_resolver != "constant":
        return None, NIB_NONE
    exact = exact_nib_units(client, source_id)
    if exact is not None:
        return exact, NIB_EXACT
    print("  render-context unavailable — falling back to the 4-decimal nib readback")
    nib = pooled_nib_units(client, source_id, width_resolver, keys)
    return nib, (NIB_READBACK if nib is not None else NIB_NONE)


def fetch(
    source_id: str, out_dir: Path, which: str, client: ApiClient, *, hand_id: str | None = None, only: str | None = None
) -> str:
    """Rebuild the fixture roots of `which` from the API. Returns the style id."""
    entries = load_sidecar_entries(source_id, which)
    source = client.get(f"/sources/{quote(source_id, safe='')}")
    style_id = source["style_id"]

    if only:
        # Additive refresh of EXISTING roots — crops, masks, slots and
        # templates stay untouched, so no headline number is re-baselined.
        # Only the endpoints the selected artifact(s) need are read; the
        # branch itself is the exporter's, imported so the two paths cannot
        # drift apart.
        pair_rows = (
            client.get(f"/sources/{quote(source_id, safe='')}/pair-instances", admin=True)
            if only in ("pair-instances", "instances")
            else []
        )
        word_rows = (
            client.get(f"/sources/{quote(source_id, safe='')}/word-instances", admin=True)
            if only in ("word-instances", "instances")
            else []
        )
        _refresh_instance_artifacts(only, entries, out_dir / style_id, source_id, pair_rows, word_rows)
        return style_id

    style = client.get(f"/styles/{quote(style_id, safe='')}")
    pair_rows = client.get(f"/sources/{quote(source_id, safe='')}/pair-instances", admin=True)
    word_rows = client.get(f"/sources/{quote(source_id, safe='')}/word-instances", admin=True)

    summaries = client.get(f"/sources/{quote(source_id, safe='')}/templates")
    have = {row["glyph_key"] for row in summaries if row.get("variant", 0) == 0}

    # Shape every entry against the CURRENT inventory (ligature-decompose
    # fallback included) and freeze the resulting slots, like the exporter.
    shaped: dict[str, list[dict]] = {}
    needed: dict[str, dict[str, None]] = {}
    for w in entries:
        slots = _shape_entry(w, have)
        shaped[_entry_id(w)] = [asdict(s) for s in slots]
        for key in glyph_keys_of(slots):
            needed.setdefault(_set_name(w), {}).setdefault(key)

    all_keys = [k for k in {k: None for keys in needed.values() for k in keys} if k in have]
    templates: dict[str, dict] = {}
    for key in all_keys:
        payload = client.get(f"/sources/{quote(source_id, safe='')}/templates/{quote(key, safe='')}", admin=True)
        templates[key] = template_row_from_payload(payload)
    print(f"fetched {len(templates)} chart templates ({len(have)} authored keys on the source)")

    hand = hand_id_for(source, pair_rows, hand_id)
    stored = stored_laufform_rows(client, source_id, summaries, set(all_keys))
    if stored is not None:
        laufform = stored
        laufform_precision = LAUFFORM_STORED
        print(f"fetched {len(laufform)} stored laufform rows")
    else:
        # A deployment without the variant read cannot serve the stored rows —
        # the pre-#311 aggregate reconstruction takes over, and the manifest
        # says so (the verify gate may then deviate wherever a chart row moved
        # since the apply step; see the module docstring).
        laufform_precision = LAUFFORM_RECONSTRUCTED
        laufform = {}
        print("  stored-variant read unavailable — reconstructing laufform rows from the hand's aggregates")
        if hand:
            aggregates = client.get(f"/hands/{quote(hand, safe='')}/aggregates", admin=True)
            laufform = laufform_rows_from_aggregates(aggregates, templates)
            print(f"reconstructed {len(laufform)} laufform rows from hand {hand!r} ({len(aggregates)} aggregates)")
        else:
            print("no hand derivable from the occurrences — fixtures freeze without laufform rows")

    constant_nib_units, nib_precision = resolve_nib(client, source_id, style["width_resolver"], set(templates))

    pages: dict[str, np.ndarray] = {}
    page_shas: dict[str, str] = {}
    for w in entries:
        page = w["page"]
        if page not in pages:
            page_path = REPO_ROOT / "data" / "sources" / source_id / page
            pages[page] = load_page(page_path)
            page_shas[page] = hashlib.sha256(page_path.read_bytes()).hexdigest()

    for set_name in sorted(needed):
        set_entries = [w for w in entries if _set_name(w) == set_name]
        if not set_entries:
            continue
        fixture_root = out_dir / style_id / _root_name(source_id, set_name)
        fixture_root.mkdir(parents=True, exist_ok=True)
        set_templates = {k: templates[k] for k in needed[set_name] if k in templates}
        (fixture_root / "templates.json").write_text(json.dumps(set_templates, ensure_ascii=False))
        set_laufform = {k: laufform[k] for k in needed[set_name] if k in laufform}
        (fixture_root / "templates_laufform.json").write_text(json.dumps(set_laufform, ensure_ascii=False))
        n_measured = _write_pair_instances(
            fixture_root, pair_rows, {_kind(w) for w in set_entries}, {_entry_id(w) for w in set_entries}
        )
        n_authored, n_traced, n_stale = _write_word_instances(
            fixture_root,
            word_rows,
            {_kind(w) for w in set_entries},
            {_entry_id(w) for w in set_entries},
            {_entry_id(w): w for w in set_entries},
        )

        index = []
        for w in set_entries:
            entry_id = _entry_id(w)
            slots = [GlyphSlot(**s) for s in shaped[entry_id]]
            missing = [k for k in glyph_keys_of(slots) if k not in templates]
            index.append(freeze_entry(fixture_root / entry_id, w, pages[w["page"]], shaped[entry_id], missing))

        manifest = {
            "exported_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "source_id": source_id,
            "style_id": style_id,
            "set": set_name,
            "page_sha256": {p: s for p, s in page_shas.items() if any(w["page"] == p for w in set_entries)},
            "style_ratio": source.get("style_ratio") or style.get("default_style_ratio"),
            "width_resolver": style.get("width_resolver"),
            "constant_nib_units": constant_nib_units,
            "laufform_keys": sorted(set_laufform),
            "words": index,
            # Provenance of THIS root: rebuilt over the API rather than pooled
            # in SQL, at which precision the pooled nib came back, and whether
            # the Laufform rows are the stored ones or a reconstruction.
            "exported_via": "api",
            "api_base": client.base_url,
            "nib_precision": nib_precision,
            "laufform_precision": laufform_precision,
            "hand_id": hand,
        }
        (fixture_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
        unscorable = [w for w in index if not w["scorable"]]
        print(
            f"fetched {len(index)} {set_name} to {fixture_root} "
            f"({len(unscorable)} unscorable, {len(set_laufform)} laufform keys, {n_measured} measured joins, "
            f"{n_authored} authored + {n_traced} traced word traces, {n_stale} frame-stale)"
        )
        if unscorable:
            print(f"  missing templates: {[(w['id'], w['missing_at_export']) for w in unscorable]}")
    return style_id


# ------------------------------------------------------------- acceptance gate


def _placement_tol_for(root: Path) -> float:
    """The placement bound a fixture root's own nib provenance earns.

    A root frozen with the exact nib has no approximated input left, so its
    compositions must reproduce bit-for-bit; a 4-decimal readback keeps the
    documented jitter allowance. An unstamped (pre-`nib_precision`) or
    DB-exported root reads as the conservative bound.
    """
    try:
        manifest = json.loads((root / "manifest.json").read_text())
    except (OSError, ValueError):
        return DEFAULT_PLACEMENT_TOL
    return EXACT_PLACEMENT_TOL if manifest.get("nib_precision") == NIB_EXACT else DEFAULT_PLACEMENT_TOL


def _bust_token() -> str:
    """One fresh cache-buster per verify run.

    The public /write responses ride Cache-Control through the Cloudflare edge,
    so an unbusted gate can hold the fixtures against a response cached BEFORE
    the write round it is supposed to verify (#311's first symptom report mixed
    exactly such stale hits into the count). A never-seen `bust` value forces
    every gate read to the origin; the API ignores the parameter.
    """
    return uuid.uuid4().hex[:12]


def verify_rows(client: ApiClient, source_id: str, root: Path, bust: str) -> list[str]:
    """Layer 1 of the gate: every rebuilt row against what the API renders from the stored one."""
    from core.pipeline import render_payload_for_template

    manifest = json.loads((root / "manifest.json").read_text())
    style_ratio = manifest.get("style_ratio") or [1, 1, 1]
    width_resolver = manifest.get("width_resolver") or "pressure"
    nib = manifest.get("constant_nib_units")
    failures: list[str] = []
    for filename, variant in (("templates.json", 0), ("templates_laufform.json", LAUFFORM_VARIANT)):
        rows = json.loads((root / filename).read_text())
        keys = sorted(rows)
        bad = 0
        served: dict[str, dict] = {}
        for start in range(0, len(keys), MAX_BATCH_KEYS):
            batch = keys[start : start + MAX_BATCH_KEYS]
            response = client.get(
                f"/sources/{quote(source_id, safe='')}/write/glyphs",
                {"keys": ",".join(batch), "variant": variant, "bust": bust},
            )
            served.update({g["glyph_key"]: g for g in response["glyphs"]})
            for key in response["missing"]:
                failures.append(f"{root.name}/{filename}: {key!r} has no variant-{variant} row on the API")
                bad += 1
        for key in keys:
            if key not in served:
                continue
            # Same 4-decimal walk the API puts on at serialisation
            # (`core.rounding`) — without it the gate would fail on the wire
            # contract instead of on the row: the fluent widening leaves
            # `advance`/`entry`/`exit_pt` unrounded, and the served copy is
            # rounded, which is a 5e-5 gap against a 1e-9 tolerance.
            local = round_wire_numbers(render_payload_for_template(rows[key], style_ratio, width_resolver, nib))
            error = payload_mismatch(local, served[key])
            if error:
                failures.append(f"{root.name}/{filename}: {key!r} {error}")
                bad += 1
        print(f"  rows {root.name}/{filename}: {len(keys)} rendered, {bad} bad")
    return failures


def verify(
    source_id: str,
    out_dir: Path,
    style_id: str,
    which: str,
    client: ApiClient,
    *,
    n_cases: int = DEFAULT_VERIFY_CASES,
    shape_tol: float = DEFAULT_SHAPE_TOL,
    placement_tol: float | None = None,
) -> None:
    """Hold the rebuilt fixtures against the deployed API — two layers, hard failure.

    The reconstructions this module performs (Laufform rows, pooled nib) cannot
    be diffed against a DB export that does not exist here, so they are checked
    against the only ground truth available: what the API itself renders and
    composes, through the very same `core.pipeline` / `core.compose` code.

    1. **rows** — every rebuilt template and Laufform row, rendered locally, must
       match `GET /write/glyphs` bit-for-bit (anchors, centerlines, entry/exit,
       advance). The sharp layer: a stale or mis-derived row fails here with no
       composition noise in between.
    2. **compositions** — at least `MIN_VERIFY_CASES` fixture cases across the
       sets, composed locally, must match `GET /write/word` item for item, with
       letter SHAPE bit-tight and PLACEMENT held to the precision the root's
       nib was frozen at: bit-tight on an `exact` nib, the documented jitter
       bound on a 4-decimal readback (see `composition_mismatch`,
       `EXACT_PLACEMENT_TOL`, `DEFAULT_PLACEMENT_TOL`). An explicit
       `placement_tol` overrides both.

    Both layers compare the full fixture rows, `glyph` included — production
    builds its rows through the same shape since issue #289 (see the module
    docstring), so the fluent body widening applies on both sides.
    Every gate read is cache-busted (see `_bust_token`): ground truth is the
    origin, never whatever the edge cache still holds from before a write round.
    """
    from tools.wordlab.cases import iter_fixture_word_cases
    from tools.wordlab.derive import derive_word

    set_names = sorted({_set_name(w) for w in load_sidecar_entries(source_id, which)})
    per_set = max(1, -(-n_cases // len(set_names)))
    bust = _bust_token()
    failures: list[str] = []
    checked = 0
    exact = 0
    worst_shape = 0.0
    worst_placement = 0.0

    for set_name in set_names:
        root = out_dir / style_id / _root_name(source_id, set_name)
        if not root.exists():
            failures.append(f"{set_name}: no fixture root at {root}")
            continue
        failures += verify_rows(client, source_id, root, bust)
        root_tol = placement_tol if placement_tol is not None else _placement_tol_for(root)
        cases = [
            c for c in iter_fixture_word_cases(which=set_name, style=style_id, fixtures_root=out_dir) if c.scorable
        ]
        if not cases:
            failures.append(f"{set_name}: no scorable fixture case to verify")
            continue
        stride = max(1, len(cases) // per_set)
        for case in cases[::stride][:per_set]:
            served = client.get(f"/sources/{quote(source_id, safe='')}/write/word", {"text": case.word, "bust": bust})
            # The local composition goes through the same 4-decimal walk the
            # API applies at serialisation (`core.rounding`): composition does
            # not round, so without this the two sides differ by up to 5e-5 xh
            # of serialisation noise alone — a bit-tight root would fail the
            # gate on the wire format rather than on a wrong row.
            local_items = round_wire_numbers(derive_word(case).composed["items"])
            error, shape, placement = composition_mismatch(
                local_items, served["items"], shape_tol=shape_tol, placement_tol=root_tol
            )
            checked += 1
            exact += placement == 0.0
            if placement != float("inf"):
                worst_shape = max(worst_shape, shape)
                worst_placement = max(worst_placement, placement)
            label = "ok  " if error is None else "FAIL"
            print(
                f"  {label} {set_name}/{case.id}: {len(served['items'])} items, "
                f"shape {shape:.2g}, placement {placement:.3g} (tol {root_tol:g})"
            )
            if error is not None:
                failures.append(f"{set_name}/{case.id} ({case.word!r}): {error}")

    if failures:
        # A root frozen with the exact nib is held bit-tight, so name the escape
        # hatch when that is what failed — an environment drift (numpy/shapely
        # in the API image vs. here) is not the operator's typo.
        tight = any(f"> {EXACT_PLACEMENT_TOL:g}" in f for f in failures)
        hint = (
            f"\n(placement held bit-tight because the nib was frozen exact; "
            f"--placement-tol {DEFAULT_PLACEMENT_TOL:g} restores the readback-era allowance)"
            if tight
            else ""
        )
        raise SystemExit(
            "verify FAILED — the rebuilt fixtures do not match the API:\n  " + "\n  ".join(failures) + hint
        )
    if checked < MIN_VERIFY_CASES:
        raise SystemExit(f"verify inconclusive: only {checked} cases checked, the gate needs {MIN_VERIFY_CASES}")
    print(
        f"verify ok: every rebuilt row renders identically and {checked} compositions match /write/word "
        f"({exact} bit-exact; worst letter shape {worst_shape:.2g}, worst placement {worst_placement:.3g} xh)"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE_ID, help="source id (default: suetterlin-1922)")
    parser.add_argument(
        "--set", dest="which", default="words", help="sidecar set to freeze (words | pairs | a custom set name | all)"
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR, help="fixtures output dir")
    parser.add_argument(
        "--api",
        default=os.environ.get("API_BASE_URL") or DEFAULT_API_BASE,
        help=f"API base (default: {DEFAULT_API_BASE})",
    )
    parser.add_argument(
        "--hand", help="hand id for the laufform reconstruction (default: modal hand of the occurrences)"
    )
    parser.add_argument(
        "--only",
        choices=ONLY_CHOICES,
        help="refresh JUST the measured joins and/or stored word traces in the EXISTING fixture roots "
        "('instances' = both) — an older set gains them without re-freezing (and thereby re-baselining) "
        "crops, masks, slots and templates",
    )
    parser.add_argument("--verify", action="store_true", help="run the acceptance gate against GET /write/word")
    parser.add_argument("--no-fetch", action="store_true", help="skip the rebuild and only verify what is on disk")
    parser.add_argument("--verify-cases", type=int, default=DEFAULT_VERIFY_CASES, help="cases to check in the gate")
    parser.add_argument(
        "--shape-tol", type=float, default=DEFAULT_SHAPE_TOL, help="letter-shape tolerance of the gate (xh units)"
    )
    parser.add_argument(
        "--placement-tol",
        type=float,
        default=None,
        help="glyph-placement tolerance of the gate (xh units); default: per root, "
        f"{EXACT_PLACEMENT_TOL:g} on an exact nib and {DEFAULT_PLACEMENT_TOL:g} on a 4-decimal readback",
    )
    args = parser.parse_args()

    client = ApiClient(args.api, token=os.environ.get("ADMIN_TOKEN"))
    if args.no_fetch:
        if not args.verify:
            raise SystemExit("--no-fetch does nothing without --verify")
        style_id = client.get(f"/sources/{quote(args.source, safe='')}")["style_id"]
    else:
        style_id = fetch(args.source, args.out, args.which, client, hand_id=args.hand, only=args.only)
    if args.verify:
        verify(
            args.source,
            args.out,
            style_id,
            args.which,
            client,
            n_cases=args.verify_cases,
            shape_tol=args.shape_tol,
            placement_tol=args.placement_tol,
        )


if __name__ == "__main__":
    main()
