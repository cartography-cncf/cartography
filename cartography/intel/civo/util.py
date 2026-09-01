import logging
from typing import Any

import requests

from cartography.util import timeit

logger = logging.getLogger(__name__)

_TIMEOUT = (60, 60)
_MAX_PAGINATION_PAGES = 100

# The feature keys this module actually filters regions by (via
# region_codes_for_feature - see instances.py/kubernetes.py/volumes.py/
# objectstores.py/loadbalancers.py/databases.py). Deliberately NOT civogo's
# full Feature struct (region.go lists 9 keys including `gpu`/`paas`/
# `public_ip_node_pools`, none of which this module uses): live-tested
# against a real Civo account and confirmed the real /v2/regions response
# does not carry a fixed key set per region at all - e.g. `fra1` was missing
# `public_ip_node_pools` entirely while `mum1` carried extra keys
# (`advanced_networking`, `custom_storage_class`) that don't even appear in
# civogo's struct. Validating against civogo's full set as if it were a
# closed, guaranteed schema was itself the bug: it made every sync against
# that real account fail outright. Only the keys this module actually reads
# are validated below.
_FEATURES_USED_BY_THIS_MODULE = frozenset(
    {
        "iaas",
        "kubernetes",
        "object_store",
        "loadbalancer",
        "dbaas",
        "volume",
    }
)


@timeit
def list_all_pages(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch every page from a paginated Civo API endpoint.

    Civo list endpoints return ``{"page": int, "per_page": int, "pages": int,
    "items": [...]}``. Walks ``page`` from 1 up to (and including) ``pages``,
    accumulating ``items`` from each response.

    Raises if a response's ``items`` isn't actually a list: a malformed but
    HTTP-200 response (e.g. ``{"items": {}, ...}``) would otherwise pass
    through ``list.extend()`` silently - a dict contributes nothing (or its
    keys, if non-empty) instead of raising, so this endpoint would be
    treated as an authoritative empty (or corrupted) inventory, and a
    subsequent cleanup would delete every previously-ingested resource of
    that type as if it had vanished upstream.

    Also raises if Civo reports more than ``_MAX_PAGINATION_PAGES`` pages.
    This mirrors the official civogo SDK's 100-page safety cap and prevents a
    malformed page count from causing an effectively unbounded request loop.
    Failing instead of truncating is required because cleanup must never run
    against a partial inventory.
    """
    all_items: list[dict[str, Any]] = []
    base_params: dict[str, Any] = dict(params or {})
    page = 1

    while True:
        request_params = {**base_params, "page": page}
        resp = api_session.get(url, params=request_params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        items = data["items"]
        if not isinstance(items, list):
            raise ValueError(
                f"Civo GET {url} returned a non-list `items` "
                f"({type(items).__name__}). Refusing to sync: this endpoint "
                "would otherwise be treated as an authoritative (possibly "
                "empty) inventory, and cleanup() would delete every "
                "previously-ingested resource of this type.",
            )
        total_pages = data["pages"]
        if total_pages > _MAX_PAGINATION_PAGES:
            raise RuntimeError(
                f"Civo GET {url} reports {total_pages} pages; maximum is "
                f"{_MAX_PAGINATION_PAGES}. Refusing to return a partial "
                "inventory.",
            )

        all_items.extend(items)

        if page >= total_pages:
            break
        page += 1

    return all_items


@timeit
def get_json_array(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch a Civo list endpoint that returns a bare JSON array, not the
    ``{"page", "per_page", "pages", "items"}`` wrapper. Confirmed against
    civogo (civo/civogo on GitHub) that not every list endpoint paginates -
    e.g. firewalls, networks, subnets, volumes, DNS domains/records, and load
    balancers all return a bare array, while instances, ssh keys, kubernetes
    clusters, object stores, object store credentials, databases, and IPs are
    paginated. Use this for the former, ``list_all_pages`` for the latter -
    don't assume every endpoint shares one shape.

    Raises if the response body isn't actually a JSON array: a malformed but
    HTTP-200 response (e.g. ``{}``) would otherwise be returned as-is and
    treated by every caller as an authoritative (empty) inventory, and a
    subsequent cleanup would delete every previously-ingested resource of
    that type.
    """
    resp = api_session.get(url, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError(
            f"Civo GET {url} returned a non-array response body "
            f"({type(data).__name__}). Refusing to sync: this endpoint "
            "would otherwise be treated as an authoritative (possibly "
            "empty) inventory, and cleanup() would delete every "
            "previously-ingested resource of this type.",
        )
    return data


@timeit
def get_regions(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    """
    Fetch every region from GET /v2/regions (a bare array), full objects -
    not just codes - since each carries a `features` map saying which
    products that region actually supports. The key set is not fixed across
    regions (live-tested against a real account: some regions carry keys
    others don't, and neither matches civogo's Feature struct exactly) -
    this module only ever reads `_FEATURES_USED_BY_THIS_MODULE`. Use
    `region_codes_for_feature` to filter per module.

    Most Civo list endpoints are region-scoped: Kubernetes clusters and
    Object Stores *require* a `region` param, and Instances/Volumes/
    Firewalls/Networks silently default to a *random* region if it's omitted
    (confirmed against Civo's own API docs, not assumed) - so a sync that
    doesn't iterate every region only ever sees one arbitrary region's
    resources, and cleanup would then delete real resources that simply live
    in a different region.

    Raises if the account has zero regions: silently proceeding with an
    empty list would make every regional fan-out load nothing, while
    cleanup() still runs and deletes every previously-ingested regional
    resource - failing loudly here is far safer than that silent data loss.

    Also raises if any region is missing its `features` object entirely, or
    has a non-boolean value (e.g. `null`) for one of the feature keys this
    module actually reads (`_FEATURES_USED_BY_THIS_MODULE`).
    `region_codes_for_feature` treats an explicit `false`, a missing key,
    and a non-bool value as identical (all mean "not supported here") -
    correct for a genuinely absent/unsupported flag (confirmed live: real
    regions legitimately omit keys they don't support), but a non-bool
    value or a wholly missing `features` object is a malformed response,
    which would otherwise silently exclude a region that may actually
    support the feature, and cleanup() would then delete that region's
    already-ingested resources as if they'd vanished upstream. Deliberately
    does NOT require every key in `_FEATURES_USED_BY_THIS_MODULE` to be
    present - a missing key is exactly what "not supported" looks like on
    the real API.
    """
    regions = get_json_array(api_session, f"{base_url}/v2/regions")
    for region in regions:
        code = require_non_empty(region.get("code"), "region code")
        features = region.get("features")
        if not isinstance(features, dict):
            raise ValueError(
                f"Civo region {code!r} is missing its `features` object "
                "(or it isn't a JSON object). Refusing to sync: treating "
                "this the same as every feature being explicitly false "
                "would wrongly exclude this region from every regional "
                "module's fetch, and cleanup() would then delete any of "
                "its already-ingested resources as if they'd vanished "
                "upstream.",
            )
        non_bool_keys = sorted(
            key
            for key in _FEATURES_USED_BY_THIS_MODULE
            if key in features and not isinstance(features[key], bool)
        )
        if non_bool_keys:
            raise ValueError(
                f"Civo region {code!r} has non-boolean value(s) for feature "
                f"key(s) {non_bool_keys} in its `features` object (e.g. "
                "`null`). Refusing to sync: a non-boolean value can't be "
                "distinguished from an explicit false by "
                "region_codes_for_feature, and would wrongly exclude this "
                "region from any module gated on that feature.",
            )
    if not regions:
        raise ValueError(
            "Civo GET /v2/regions returned no regions. Refusing to sync: "
            "proceeding with an empty region list would load nothing from "
            "every regional endpoint, and cleanup() would then delete every "
            "previously-ingested regional resource as if it were gone "
            "upstream.",
        )
    return regions


def region_codes_for_feature(
    regions: list[dict[str, Any]],
    feature: str | None,
) -> list[str]:
    """
    Returns the region codes that support `feature` (one of the keys in a
    region's `features` map, e.g. "kubernetes", "object_store", "dbaas",
    "volume", "loadbalancer", "iaas"). Pass `feature=None` for resources with
    no corresponding Features flag (Firewalls, Networks, Subnets, IPs -
    civogo's Feature struct has no such key for any of these), which returns
    every region unfiltered.

    An empty result here is expected and not an error: it legitimately means
    this Civo account has no region enabled for that specific product, so
    that resource type's inventory - and any previously-ingested but now
    stale nodes, via cleanup() - should legitimately be empty. Only a
    completely empty *regions* list (see `get_regions`) is treated as a
    failure.
    """
    if feature is None:
        return [region["code"] for region in regions]
    return [
        region["code"]
        for region in regions
        if (region.get("features") or {}).get(feature)
    ]


def _with_region(item: dict[str, Any], region_code: str) -> dict[str, Any]:
    """
    Tags a raw API record with the region it was fetched from. Many Civo
    resource types (Firewall, Network, Volume, ObjectStore, LoadBalancer,
    IP, Database) carry no `region` field of their own at all, so without
    this the region information used to fetch them - the only copy of it
    that exists - would simply be discarded. Prefers the item's own `region`
    field when present (e.g. Instance) and non-empty, since that's a
    per-object ground truth the query parameter can't override; falls back
    to the query's region otherwise.
    """
    return {**item, "region": item.get("region") or region_code}


@timeit
def fan_out_paginated_across_regions(
    api_session: requests.Session,
    url: str,
    region_codes: list[str],
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Calls a paginated ({page,per_page,pages,items}) list endpoint once per
    region and combines the results, deduplicated by id and tagged with the
    region each came from (see `_with_region`). civogo's own client notes
    region is "generally safe to add as an unused query param if not needed
    by a specific endpoint" - so this is applied to every region-scoped
    endpoint uniformly rather than special-casing which ones actually filter
    by it.
    """
    all_items: list[dict[str, Any]] = []
    seen_ids: set[Any] = set()
    for region_code in region_codes:
        region_params = {**(params or {}), "region": region_code}
        for item in list_all_pages(api_session, url, params=region_params):
            item_id = item.get("id")
            if item_id is not None:
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
            all_items.append(_with_region(item, region_code))
    return all_items


@timeit
def fan_out_array_across_regions(
    api_session: requests.Session,
    url: str,
    region_codes: list[str],
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Calls a bare-array list endpoint once per region and combines the
    results, deduplicated by id and tagged with the region each came from
    (see `_with_region`). See `fan_out_paginated_across_regions` for why
    every region-scoped endpoint is treated uniformly this way.
    """
    all_items: list[dict[str, Any]] = []
    seen_ids: set[Any] = set()
    for region_code in region_codes:
        region_params = {**(params or {}), "region": region_code}
        for item in get_json_array(api_session, url, params=region_params):
            item_id = item.get("id")
            if item_id is not None:
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
            all_items.append(_with_region(item, region_code))
    return all_items


def require_non_empty(value: Any, field_name: str) -> Any:
    """
    Raise if a required field is missing or empty, rather than silently
    accepting an empty string as a graph identity (a real bug caught in this
    session's Fly.io module review: empty ids/hostnames/names were accepted
    and produced malformed synthetic identities downstream).
    """
    if value is None or value == "":
        raise ValueError(f"Civo record is missing required non-empty {field_name}.")
    return value
