from __future__ import annotations

import asyncio
import logging
from typing import Any

import neo4j
from okta.client import Client as OktaClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.okta.common import collect_raw_paginated
from cartography.intel.okta.common import is_missing_scope_error
from cartography.intel.okta.common import OktaApiError
from cartography.models.okta.network_zone import OktaNetworkZoneSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def _get_okta_network_zones(okta_client: OktaClient) -> list[dict[str, Any]]:
    # Raw JSON: the SDK's IP service category enum would reject new categories.
    return await collect_raw_paginated(okta_client, "/api/v1/zones")


def _addresses(addresses: list[dict[str, Any]] | None) -> list[str]:
    return [address["value"] for address in addresses or [] if address.get("value")]


def _location(location: dict[str, Any]) -> str | None:
    return location.get("region") or location.get("country")


def _locations(locations: list[dict[str, Any]] | None) -> list[str]:
    return [
        code for code in (_location(location) for location in locations or []) if code
    ]


def _include_exclude(value: Any) -> tuple[list, list]:
    # DYNAMIC zones use plain lists; DYNAMIC_V2 zones use {include, exclude}.
    if isinstance(value, dict):
        return value.get("include") or [], value.get("exclude") or []
    return value or [], []


def _transform_okta_network_zones(
    zones: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for zone in zones:
        asns_include, asns_exclude = _include_exclude(zone.get("asns"))
        locations_include, locations_exclude = _include_exclude(zone.get("locations"))
        categories_include, categories_exclude = _include_exclude(
            zone.get("ipServiceCategories"),
        )
        transformed.append(
            {
                "id": zone["id"],
                "name": zone.get("name"),
                "type": zone.get("type"),
                "status": zone.get("status"),
                "usage": zone.get("usage"),
                "system": zone.get("system"),
                "created": zone.get("created"),
                "okta_last_updated": zone.get("lastUpdated"),
                "gateways": _addresses(zone.get("gateways")),
                "proxies": _addresses(zone.get("proxies")),
                "use_as_exempt_list": zone.get("useAsExemptList"),
                "asns_include": [str(asn) for asn in asns_include],
                "asns_exclude": [str(asn) for asn in asns_exclude],
                "locations_include": _locations(locations_include),
                "locations_exclude": _locations(locations_exclude),
                "proxy_type": zone.get("proxyType"),
                "ip_service_categories_include": categories_include,
                "ip_service_categories_exclude": categories_exclude,
            },
        )
    return transformed


def _load_okta_network_zones(
    neo4j_session: neo4j.Session,
    zones: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    load(
        neo4j_session,
        OktaNetworkZoneSchema(),
        zones,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
    )


def _cleanup_okta_network_zones(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        OktaNetworkZoneSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_okta_network_zones(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Okta network zones.

    Run before the policy sync: policy rules link to the zones loaded here.
    """
    logger.info("Syncing Okta network zones")
    try:
        raw_zones = asyncio.run(_get_okta_network_zones(okta_client))
    except OktaApiError as exc:
        # Zone listing requires okta.networkZones.read. Existing tokens often
        # lack it; skip this sub-sync so the rest of Okta ingestion still runs.
        if is_missing_scope_error(exc):
            logger.warning(
                "Unable to sync Okta network zones - api token needs "
                "okta.networkZones.read",
            )
            return
        raise
    zones = _transform_okta_network_zones(raw_zones)
    _load_okta_network_zones(neo4j_session, zones, common_job_parameters)
    _cleanup_okta_network_zones(neo4j_session, common_job_parameters)
    logger.info("Loaded %s Okta network zones", len(zones))
