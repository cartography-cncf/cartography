from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.portkey.util import list_workspace_members
from cartography.intel.portkey.util import list_workspaces
from cartography.models.portkey.workspace import PortkeyUserWorkspaceMembershipMatchLink
from cartography.models.portkey.workspace import PortkeyWorkspaceSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    workspaces = list_workspaces(api_session, common_job_parameters["BASE_URL"])
    memberships: list[dict[str, Any]] = []
    for workspace in workspaces:
        members = list_workspace_members(
            api_session,
            common_job_parameters["BASE_URL"],
            workspace["id"],
        )
        for member in members:
            memberships.append(
                {
                    "user_id": member["id"],
                    "workspace_id": workspace["id"],
                    "role": member.get("role"),
                    "org_role": member.get("org_role"),
                    "status": member.get("status"),
                    "created_at": member.get("created_at"),
                    "last_updated_at": member.get("last_updated_at"),
                }
            )
    load_workspaces(
        neo4j_session,
        workspaces,
        common_job_parameters["PORTKEY_ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    load_memberships(
        neo4j_session,
        memberships,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return workspaces


@timeit
def load_workspaces(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        PortkeyWorkspaceSchema(),
        data,
        lastupdated=update_tag,
        PORTKEY_ORG_ID=org_id,
    )


@timeit
def load_memberships(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        PortkeyUserWorkspaceMembershipMatchLink(),
        data,
        lastupdated=update_tag,
        _sub_resource_label="PortkeyOrganization",
        _sub_resource_id="global",
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(PortkeyWorkspaceSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_matchlink(
        PortkeyUserWorkspaceMembershipMatchLink(),
        sub_resource_label="PortkeyOrganization",
        sub_resource_id="global",
        update_tag=common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
