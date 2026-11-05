import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.neon.util import get_json
from cartography.intel.neon.util import get_paginated
from cartography.intel.neon.util import iso_to_datetime
from cartography.intel.neon.util import TOLERATED_STATUSES
from cartography.intel.neon.util import warn_unavailable
from cartography.models.neon.apikey import NeonApiKeySchema
from cartography.models.neon.organization import NeonOrganizationSchema
from cartography.models.neon.organizationmember import NeonOrganizationMemberSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_MEMBERS_PAGE_SIZE = 500


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    org_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Sync the organizations in scope and return them so the caller can fan out per
    organization.

    With an explicit ``org_ids`` list each organization is read directly. That is
    the only path an organization API key can take, because
    ``/users/me/organizations`` belongs to a user and answers 4xx to an
    organization key. Without one, every organization the key's user belongs to
    is synced.
    """
    base_url = common_job_parameters["BASE_URL"]
    if org_ids:
        organizations = [get_organization(api_session, base_url, o) for o in org_ids]
    else:
        organizations = get(api_session, base_url)

    load_organizations(
        neo4j_session,
        transform_organizations(organizations),
        common_job_parameters["UPDATE_TAG"],
    )
    return organizations


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return get_json(api_session, f"{base_url}/users/me/organizations")["organizations"]


@timeit
def get_organization(
    api_session: requests.Session,
    base_url: str,
    org_id: str,
) -> dict[str, Any]:
    return get_json(api_session, f"{base_url}/organizations/{org_id}")


def transform_organizations(
    organizations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "id": org["id"],
            "name": org["name"],
            "handle": org.get("handle"),
            "plan": org.get("plan"),
            "managed_by": org.get("managed_by"),
            "require_mfa": org.get("require_mfa"),
            "allow_hipaa_projects": org.get("allow_hipaa_projects"),
            "created_at": iso_to_datetime(org.get("created_at")),
            "updated_at": iso_to_datetime(org.get("updated_at")),
        }
        for org in organizations
    ]


@timeit
def load_organizations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NeonOrganizationSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def sync_members(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    org_id = common_job_parameters["ORG_ID"]
    members = get_members(api_session, common_job_parameters["BASE_URL"], org_id)
    if members is None:
        warn_unavailable("organization members", org_id)
        return
    load_members(
        neo4j_session,
        transform_members(members),
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    GraphJob.from_node_schema(
        NeonOrganizationMemberSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def get_members(
    api_session: requests.Session,
    base_url: str,
    org_id: str,
) -> list[dict[str, Any]] | None:
    return get_paginated(
        api_session,
        f"{base_url}/organizations/{org_id}/members",
        "members",
        _MEMBERS_PAGE_SIZE,
        tolerate=TOLERATED_STATUSES,
    )


def transform_members(members: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for entry in members:
        member = entry["member"]
        user = entry.get("user") or {}
        result.append(
            {
                "id": member["id"],
                "user_id": member["user_id"],
                "org_id": member["org_id"],
                "role": member.get("role"),
                "joined_at": iso_to_datetime(member.get("joined_at")),
                "email": user.get("email"),
                "has_mfa": user.get("has_mfa"),
                "deactivated_at": iso_to_datetime(user.get("deactivated_at")),
            },
        )
    return result


@timeit
def load_members(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NeonOrganizationMemberSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def sync_api_keys(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync the organization's API keys. Run after projects and members are loaded so
    the SCOPED_TO and OWNED_BY edges have something to attach to.
    """
    org_id = common_job_parameters["ORG_ID"]
    keys = get_api_keys(api_session, common_job_parameters["BASE_URL"], org_id)
    if keys is None:
        warn_unavailable("organization API keys", org_id)
        return
    load_api_keys(
        neo4j_session,
        transform_api_keys(keys),
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    GraphJob.from_node_schema(NeonApiKeySchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def get_api_keys(
    api_session: requests.Session,
    base_url: str,
    org_id: str,
) -> list[dict[str, Any]] | None:
    return get_json(
        api_session,
        f"{base_url}/organizations/{org_id}/api_keys",
        tolerate=TOLERATED_STATUSES,
    )


def transform_api_keys(keys: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for key in keys:
        created_by = key.get("created_by") or {}
        result.append(
            {
                "id": str(key["id"]),
                "name": key["name"],
                "created_at": iso_to_datetime(key.get("created_at")),
                "created_by_id": created_by.get("id"),
                "created_by_name": created_by.get("name"),
                "last_used_at": iso_to_datetime(key.get("last_used_at")),
                "last_used_from_addr": key.get("last_used_from_addr") or None,
                "project_id": key.get("project_id"),
            },
        )
    return result


@timeit
def load_api_keys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NeonApiKeySchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
