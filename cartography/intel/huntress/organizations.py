import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.huntress.util import get_paginated_huntress_items
from cartography.intel.huntress.util import required_id
from cartography.models.huntress.organization import HuntressOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(api_session: requests.Session, base_uri: str) -> list[dict[str, Any]]:
    return get_paginated_huntress_items(
        api_session,
        base_uri,
        "organizations",
        "organizations",
    )


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for organization in api_result:
        result.append(
            {
                "id": required_id(organization, "Organization"),
                "name": organization.get("name"),
                "key": organization.get("key"),
                "agents_count": organization.get("agents_count"),
                "incident_reports_count": organization.get("incident_reports_count"),
                "identity_provider_tenant_id": organization.get(
                    "identity_provider_tenant_id"
                ),
                "created_at": organization.get("created_at"),
                "updated_at": organization.get("updated_at"),
            }
        )
    return result


def load_organizations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: int,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        HuntressOrganizationSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(HuntressOrganizationSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_uri: str,
    account_id: int,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_data = get(api_session, base_uri)
    organizations = transform(raw_data)
    load_organizations(neo4j_session, organizations, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
