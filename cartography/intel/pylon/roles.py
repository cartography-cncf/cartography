import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.pylon.util import paginated_get
from cartography.models.pylon.role import PylonRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_roles = get(api_session, base_url)
    roles = transform(raw_roles)
    load_roles(
        neo4j_session,
        roles,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return paginated_get(api_session, f"{base_url}/user-roles")


def transform(raw_roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    roles = []
    for role in raw_roles:
        permissions = role.get("permissions") or []
        issue_access_policy = role.get("issue_access_policy") or {}
        roles.append(
            {
                "id": role["id"],
                "name": role.get("name"),
                "slug": role.get("slug"),
                "permissions": sorted({p["action"] for p in permissions}),
                "filtered_permissions": sorted(
                    {
                        p["action"]
                        for p in permissions
                        if p.get("filter") or p.get("filter_unsupported")
                    },
                ),
                "field_restricted_permissions": sorted(
                    {
                        p["action"]
                        for p in permissions
                        if p.get("field_restrictions_unsupported")
                    },
                ),
                "issue_access_default_actions": sorted(
                    issue_access_policy.get("default_actions") or [],
                ),
                "issue_access_rule_count": len(
                    issue_access_policy.get("rules") or [],
                ),
            },
        )
    return roles


@timeit
def load_roles(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Pylon roles for organization %s", len(data), org_id)
    load(
        neo4j_session,
        PylonRoleSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(PylonRoleSchema(), common_job_parameters).run(
        neo4j_session,
    )
