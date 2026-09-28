import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from urllib.parse import urlsplit

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.graph.statement import GraphStatement
from cartography.intel.airbyte.util import AirbyteClient
from cartography.models.airbyte.user import AirbyteUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_USERS_URI = "/users"
_PERMISSIONS_URI = "/permissions"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: AirbyteClient,
    org_id: str,
    common_job_parameters: Dict[str, Any],
) -> bool:
    """
    Sync the users of an organization and their permissions.

    Listing users requires an organization role and reading another user's
    permissions requires Organization Admin, so the application's user may be
    denied here while still being able to read the organization's workspaces and
    pipelines. A 403 from GET /users or GET /permissions skips this organization's
    users entirely: nothing is loaded and cleanup does not run, so the previously
    ingested users and access relationships are preserved instead of being
    replaced by a partial snapshot. Any other error is re-raised.

    :return: True if users and permissions were fully collected, False if the
        API denied access and the organization's users were not refreshed.
    """
    try:
        users = get(api_session, org_id=org_id)
        for user in users:
            permissions = get_permissions(api_session, user["id"], org_id=org_id)
            org_admin, workspace_admin, workspace_member = transform_permissions(
                permissions
            )
            user["adminOfOrganization"] = org_admin
            user["adminOfWorkspace"] = workspace_admin
            user["memberOfWorkspace"] = workspace_member
    except requests.HTTPError as e:
        endpoint = _denied_identity_endpoint(api_session, e)
        if endpoint is None:
            raise
        logger.warning(
            "Airbyte denied GET %s for organization %s (HTTP 403). Skipping users "
            "and permissions for this organization; previously ingested Airbyte "
            "users and their access relationships are kept and not cleaned up. "
            "Collecting them requires the user that owns the Airbyte application "
            "to be an Organization Admin of this organization.",
            endpoint,
            org_id,
        )
        return False
    load_users(neo4j_session, users, org_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return True


def _denied_identity_endpoint(
    api_session: AirbyteClient,
    error: requests.HTTPError,
) -> str | None:
    """
    Return the endpoint if the error is a 403 on the users or permissions GET.

    The check uses the request that produced the response, so a 403 from the
    token exchange (POST /applications/token), which AirbyteClient.get() performs
    before the resource request, is not mistaken for an identity denial.
    """
    response = error.response
    if response is None or response.status_code != 403:
        return None
    request = response.request
    if request is None or request.method != "GET" or request.url is None:
        return None
    request_path = urlsplit(request.url).path
    for uri in (_USERS_URI, _PERMISSIONS_URI):
        if request_path == urlsplit(f"{api_session.base_url}{uri}").path:
            return uri
    return None


@timeit
def get(
    api_session: AirbyteClient,
    org_id: str,
) -> List[Dict[str, Any]]:
    return api_session.get(_USERS_URI, params={"organizationId": org_id})


@timeit
def get_permissions(
    api_session: AirbyteClient,
    user_id: str,
    org_id: str,
) -> List[Dict[str, Any]]:
    return api_session.get(
        _PERMISSIONS_URI,
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
    load(
        neo4j_session,
        AirbyteUserSchema(),
        data,
        ORG_ID=org_id,
        lastupdated=update_tag,
    )


# AirbyteUser ids are global, so one user node can belong to several
# organizations. The cleanup generated from AirbyteUserSchema is scoped by the
# user's RESOURCE edge only: while syncing one organization it would delete the
# stale ADMIN_OF/MEMBER_OF edges that another organization wrote for a shared
# user, and delete a shared user that left this organization. That is unsafe when
# the other organization's users could not be read this run. Workspaces cannot be
# used to tell the organizations apart because GET /workspaces is not filtered by
# organization. Instead:
# - a user is deleted only once no other organization lists it;
# - a user's stale access edges are deleted only when every other organization
#   that lists the user has already refreshed it in this run. The last
#   organization to sync a shared user cleans it up, and a user that belongs to
#   an organization whose users were not collected keeps its edges.
_CLEANUP_QUERIES = [
    """
    MATCH (:AirbyteOrganization {id: $ORG_ID})-[r:RESOURCE]->(n:AirbyteUser)
    WHERE r.lastupdated <> $UPDATE_TAG
        AND NOT EXISTS {
            MATCH (n)<-[:RESOURCE]-(other:AirbyteOrganization)
            WHERE other.id <> $ORG_ID
        }
    WITH n LIMIT $LIMIT_SIZE
    DETACH DELETE n;
    """,
    """
    MATCH (:AirbyteOrganization {id: $ORG_ID})-[:RESOURCE]->(n:AirbyteUser)
    WHERE NOT EXISTS {
        MATCH (n)<-[other_r:RESOURCE]-(other:AirbyteOrganization)
        WHERE other.id <> $ORG_ID AND other_r.lastupdated <> $UPDATE_TAG
    }
    MATCH (n)-[r:ADMIN_OF]->(:AirbyteOrganization)
    WHERE r.lastupdated <> $UPDATE_TAG
    WITH r LIMIT $LIMIT_SIZE
    DELETE r;
    """,
    """
    MATCH (:AirbyteOrganization {id: $ORG_ID})-[:RESOURCE]->(n:AirbyteUser)
    WHERE NOT EXISTS {
        MATCH (n)<-[other_r:RESOURCE]-(other:AirbyteOrganization)
        WHERE other.id <> $ORG_ID AND other_r.lastupdated <> $UPDATE_TAG
    }
    MATCH (n)-[r:ADMIN_OF|MEMBER_OF]->(:AirbyteWorkspace)
    WHERE r.lastupdated <> $UPDATE_TAG
    WITH r LIMIT $LIMIT_SIZE
    DELETE r;
    """,
    """
    MATCH (:AirbyteOrganization {id: $ORG_ID})-[r:RESOURCE]->(:AirbyteUser)
    WHERE r.lastupdated <> $UPDATE_TAG
    WITH r LIMIT $LIMIT_SIZE
    DELETE r;
    """,
]


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    parameters = {
        "ORG_ID": common_job_parameters["ORG_ID"],
        "UPDATE_TAG": common_job_parameters["UPDATE_TAG"],
    }
    GraphJob(
        "Cleanup AirbyteUser",
        [
            GraphStatement(
                query,
                parameters=parameters,
                iterative=True,
                iterationsize=10000,
                parent_job_name="AirbyteUser",
                parent_job_sequence_num=idx,
            )
            for idx, query in enumerate(_CLEANUP_QUERIES, start=1)
        ],
        "AirbyteUser",
    ).run(neo4j_session)
