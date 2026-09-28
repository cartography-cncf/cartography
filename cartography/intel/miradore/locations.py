import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.miradore.tenant import load_tenant
from cartography.intel.miradore.util import get_nested
from cartography.intel.miradore.util import get_paginated_miradore_items
from cartography.intel.miradore.util import parse_datetime
from cartography.intel.miradore.util import parse_int
from cartography.intel.miradore.util import required_int_id
from cartography.intel.miradore.util import scoped_id
from cartography.models.miradore.location import MiradoreLocationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_ITEM = "Location"
_SELECT = ",".join(
    (
        "ID",
        "Name",
        "FullName",
        "Status",
        "Created",
        "Modified",
        "Parent.ID",
    )
)


@timeit
def get(
    api_session: requests.Session,
    base_uri: str,
    site_name: str,
    api_key: str,
) -> list[dict[str, Any]]:
    return get_paginated_miradore_items(
        api_session,
        base_uri,
        site_name,
        api_key,
        _ITEM,
        _SELECT,
    )


def transform(api_result: list[dict[str, Any]], site_name: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for location in api_result:
        miradore_id = required_int_id(location, "Location")
        result.append(
            {
                "id": scoped_id(site_name, miradore_id),
                "miradore_id": miradore_id,
                "name": location.get("Name"),
                "full_name": location.get("FullName"),
                "status": location.get("Status"),
                "created": parse_datetime(location.get("Created")),
                "modified": parse_datetime(location.get("Modified")),
                "parent_id": scoped_id(
                    site_name, parse_int(get_nested(location, "Parent", "ID"))
                ),
            }
        )
    return result


def load_locations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load_tenant(neo4j_session, tenant_id, update_tag)
    if not data:
        return
    load(
        neo4j_session,
        MiradoreLocationSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(MiradoreLocationSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_uri: str,
    site_name: str,
    api_key: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_data = get(api_session, base_uri, site_name, api_key)
    locations = transform(raw_data, site_name)
    load_locations(neo4j_session, locations, site_name, update_tag)
    cleanup(neo4j_session, common_job_parameters)
