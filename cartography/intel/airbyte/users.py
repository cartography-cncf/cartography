import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.airbyte.util import AirbyteClient
from cartography.models.airbyte.user import AirbyteUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: AirbyteClient,
    org_id: str,
    common_job_parameters: Dict[str, Any],
) -> None:
    users = get(api_session, org_id=org_id)
    for user in users:
        permissions = get_permissions(api_session, user["id"], org_id=org_id)
        org_admin, workspace_admin, workspace_member = transform_permissions(
            permissions
        )
        user["adminOfOrganization"] = org_admin
        user["adminOfWorkspace"] = workspace_admin
        user["memberOfWorkspace"] = workspace_member
    load_users(neo4j_session, users, org_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: AirbyteClient,
    org_id: str,
) -> List[Dict[str, Any]]:
    return api_session.get("/users", params={"organizationId": org_id})


@timeit
def get_permissions(
    api_session: AirbyteClient,
    user_id: str,
    org_id: str,
) -> List[Dict[str, Any]]:
    return api_session.get(
        "/permissions",
        params={"organizationId": org_id, "userId": user_id},
    )


@timeit
def transform_permissions(
    permissions: List[Dict[str, Any]],
) -> Tuple[
    List[str],  # org_admin
    List[str],  # workspace_admin
    List[str],  # workspace_member
]:
    org_admin: list[str] = []
    workspace_admin: list[str] = []
    workspace_member: list[str] = []

    for permission in permissions:
        # workspace
        if permission["scope"] == "workspace":
            if permission["permissionType"] in ("workspace_owner", "workspace_admin"):
                workspace_admin.append(permission["scopeId"])
            workspace_member.append(permission["scopeId"])
        # organization
        elif permission["scope"] == "organization":
            if permission["permissionType"] in ("organization_admin",):
                org_admin.append(permission["scopeId"])
    return org_admin, workspace_admin, workspace_member


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Airbyte Users into Neo4j.", len(data))
    load(
        neo4j_session,
        AirbyteUserSchema(),
        data,
        ORG_ID=org_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AirbyteUserSchema(), common_job_parameters).run(
        neo4j_session
    )
