import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from urllib.parse import urlsplit

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.airbyte.util import AirbyteClient
from cartography.models.airbyte.user import AirbyteUserAdminOfOrganizationMatchLink
from cartography.models.airbyte.user import AirbyteUserAdminOfWorkspaceMatchLink
from cartography.models.airbyte.user import AirbyteUserMemberOfWorkspaceMatchLink
from cartography.models.airbyte.user import AirbyteUserSchema
from cartography.models.airbyte.user import AirbyteUserToOrganizationMatchLink
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
            # For the application's own user, Airbyte ignores organizationId and
            # returns every organization's permissions. Drop other organizations'
            # roles so this organization only writes edges about itself.
            # Workspace permissions are kept: the API does not say which
            # organization a workspace belongs to.
            permissions = [
                p
                for p in get_permissions(api_session, user["id"], org_id=org_id)
                if p["scope"] != "organization" or p["scopeId"] == org_id
            ]
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


# The user node is shared across organizations, so its organization and access
# edges are MatchLinks scoped to the organization that wrote them. See
# cartography/models/airbyte/user.py. Each MatchLink is paired with the user
# field holding its target ids; None means the organization being synced.
_MATCHLINKS = (
    (AirbyteUserToOrganizationMatchLink(), None),
    (AirbyteUserAdminOfOrganizationMatchLink(), "adminOfOrganization"),
    (AirbyteUserAdminOfWorkspaceMatchLink(), "adminOfWorkspace"),
    (AirbyteUserMemberOfWorkspaceMatchLink(), "memberOfWorkspace"),
)


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(neo4j_session, AirbyteUserSchema(), data, lastupdated=update_tag)
    for matchlink, field in _MATCHLINKS:
        load_matchlinks(
            neo4j_session,
            matchlink,
            [
                {"user_id": user["id"], "scope_id": scope_id}
                for user in data
                for scope_id in (user[field] if field else [org_id])
            ],
            lastupdated=update_tag,
            _sub_resource_label="AirbyteOrganization",
            _sub_resource_id=org_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    for matchlink, _ in _MATCHLINKS:
        GraphJob.from_matchlink(
            matchlink,
            "AirbyteOrganization",
            common_job_parameters["ORG_ID"],
            common_job_parameters["UPDATE_TAG"],
        ).run(neo4j_session)
