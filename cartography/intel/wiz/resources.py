import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.wiz.api import get_paginated
from cartography.intel.wiz.util import epoch_days_ago_iso
from cartography.intel.wiz.util import filter_by_project_ids
from cartography.intel.wiz.util import project_ids
from cartography.intel.wiz.util import project_names
from cartography.intel.wiz.util import tags_to_strings
from cartography.models.wiz.resources import WizResourceSchema
from cartography.models.wiz.tenant import WizTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_QUERY = """
query WizCloudResources($first: Int, $after: String, $filterBy: CloudResourceV2Filters, $orderBy: CloudResourceOrder) {
  cloudResourcesV2(first: $first, after: $after, filterBy: $filterBy, orderBy: $orderBy) {
    nodes {
      id
      name
      externalId
      type
      cloudPlatform
      status
      tags { key value }
      projects { id name }
      createdAt
      updatedAt
      isOpenToAllInternet
      isAccessibleFromInternet
      hasAccessToSensitiveData
      hasAdminPrivileges
      hasHighPrivileges
      hasSensitiveData
      cloudAccount {
        id
        name
        cloudProvider
        externalId
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""


@timeit
def get(
    session: requests.Session,
    graphql_url: str,
    token: str,
    since_iso: str,
    project_id_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    raw = get_paginated(
        session,
        graphql_url,
        token,
        _QUERY,
        "cloudResourcesV2",
        filter_by={"updatedAt": {"after": since_iso}},
    )
    return filter_by_project_ids(raw, project_id_filter)


def transform(raw_resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for resource in raw_resources:
        cloud_account = resource.get("cloudAccount") or {}
        projects = resource.get("projects") or []
        result.append(
            {
                "id": resource["id"],
                "name": resource.get("name"),
                "external_id": resource.get("externalId"),
                "resource_type": resource.get("type"),
                "cloud_platform": resource.get("cloudPlatform"),
                "cloud_provider_url": resource.get("cloudProviderURL"),
                "status": resource.get("status"),
                "region": resource.get("region"),
                "cloud_account_id": cloud_account.get("id"),
                "cloud_account_name": cloud_account.get("name"),
                "cloud_account_provider": cloud_account.get("cloudProvider"),
                "cloud_account_external_id": cloud_account.get("externalId"),
                "project_ids": project_ids(projects),
                "project_names": project_names(projects),
                "tags": tags_to_strings(resource.get("tags")),
                "created_at": resource.get("createdAt"),
                "updated_at": resource.get("updatedAt"),
                "is_open_to_all_internet": resource.get("isOpenToAllInternet"),
                "is_accessible_from_internet": resource.get(
                    "isAccessibleFromInternet",
                ),
                "has_access_to_sensitive_data": resource.get(
                    "hasAccessToSensitiveData",
                ),
                "has_admin_privileges": resource.get("hasAdminPrivileges"),
                "has_high_privileges": resource.get("hasHighPrivileges"),
                "has_sensitive_data": resource.get("hasSensitiveData"),
            },
        )
    return result


@timeit
def load_resources(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    graphql_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        WizTenantSchema(),
        [{"id": tenant_id, "graphql_url": graphql_url}],
        lastupdated=update_tag,
    )
    load(
        neo4j_session,
        WizResourceSchema(),
        data,
        lastupdated=update_tag,
        WIZ_TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(WizResourceSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    graphql_url: str,
    token: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    lookback_days: int,
    project_id_filter: list[str] | None = None,
    *,
    do_cleanup: bool = True,
) -> None:
    logger.info("Syncing Wiz resources for tenant %s", tenant_id)
    since_iso = epoch_days_ago_iso(update_tag, lookback_days)
    raw_resources = get(session, graphql_url, token, since_iso, project_id_filter)
    resources = transform(raw_resources)
    load_resources(neo4j_session, resources, tenant_id, graphql_url, update_tag)
    if do_cleanup:
        cleanup(neo4j_session, common_job_parameters)
