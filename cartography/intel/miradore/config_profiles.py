import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.miradore.tenant import load_tenant
from cartography.intel.miradore.util import get_paginated_miradore_items
from cartography.intel.miradore.util import required_int_id
from cartography.intel.miradore.util import scoped_id
from cartography.models.miradore.config_profile import MiradoreConfigProfileSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_ITEM = "ConfigProfile"
_SELECT = ",".join(
    (
        "ID",
        "Name",
        "ConfigurationType",
        "Description",
        "OSCategory",
        "Status",
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
    for profile in api_result:
        miradore_id = required_int_id(profile, "ConfigProfile")
        result.append(
            {
                "id": scoped_id(site_name, miradore_id),
                "miradore_id": miradore_id,
                "name": profile.get("Name"),
                "configuration_type": profile.get("ConfigurationType"),
                "description": profile.get("Description"),
                "os_category": profile.get("OSCategory"),
                "status": profile.get("Status"),
            }
        )
    return result


def load_config_profiles(
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
        MiradoreConfigProfileSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(MiradoreConfigProfileSchema(), common_job_parameters).run(
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
    config_profiles = transform(raw_data, site_name)
    load_config_profiles(neo4j_session, config_profiles, site_name, update_tag)
    cleanup(neo4j_session, common_job_parameters)
