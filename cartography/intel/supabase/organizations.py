import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.supabase.util import get_json
from cartography.models.supabase.organization import SupabaseOrganizationSchema
from cartography.models.supabase.organizationmember import (
    SupabaseOrganizationMemberSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    org_allowlist: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Sync the organizations reachable with this access token and return them so the
    caller can fan out per organization.
    """
    base_url = common_job_parameters["BASE_URL"]
    organizations = get(api_session, base_url)
    if org_allowlist:
        organizations = [o for o in organizations if o["slug"] in org_allowlist]
        logger.info(
            "Restricting Supabase sync to %d of the available organizations",
            len(organizations),
        )

    details = [get_details(api_session, base_url, o["slug"]) for o in organizations]
    transformed = transform_organizations(organizations, details)
    load_organizations(
        neo4j_session,
        transformed,
        common_job_parameters["UPDATE_TAG"],
    )
    return organizations


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return get_json(api_session, f"{base_url}/v1/organizations")


@timeit
def get_details(
    api_session: requests.Session,
    base_url: str,
    slug: str,
) -> dict[str, Any]:
    return get_json(api_session, f"{base_url}/v1/organizations/{slug}")


def transform_organizations(
    organizations: list[dict[str, Any]],
    details: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    details_by_id = {d["id"]: d for d in details}
    result: list[dict[str, Any]] = []
    for org in organizations:
        detail = details_by_id.get(org["id"], {})
        result.append(
            {
                "slug": org["slug"],
                "organization_id": org["id"],
                "name": org["name"],
                "plan": detail.get("plan"),
                "opt_in_tags": detail.get("opt_in_tags"),
                "allowed_release_channels": detail.get("allowed_release_channels"),
            },
        )
    return result


@timeit
def load_organizations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseOrganizationSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def sync_members(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    org_slug = common_job_parameters["ORG_SLUG"]
    members = get_members(api_session, common_job_parameters["BASE_URL"], org_slug)
    transformed = transform_members(members, org_slug)
    load_members(
        neo4j_session,
        transformed,
        org_slug,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup_members(neo4j_session, common_job_parameters)


@timeit
def get_members(
    api_session: requests.Session,
    base_url: str,
    org_slug: str,
) -> list[dict[str, Any]]:
    return get_json(api_session, f"{base_url}/v1/organizations/{org_slug}/members")


def transform_members(
    members: list[dict[str, Any]],
    org_slug: str,
) -> list[dict[str, Any]]:
    # Scope the node id to the organization: role_name is a per-organization fact,
    # so a user belonging to several organizations needs one node per membership.
    return [
        {
            "id": f"{org_slug}/{member['user_id']}",
            "user_id": member["user_id"],
            "email": member.get("email"),
            "user_name": member.get("user_name"),
            "role_name": member.get("role_name"),
            "mfa_enabled": member.get("mfa_enabled"),
        }
        for member in members
    ]


@timeit
def load_members(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_slug: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseOrganizationMemberSchema(),
        data,
        lastupdated=update_tag,
        ORG_SLUG=org_slug,
    )


@timeit
def cleanup_members(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        SupabaseOrganizationMemberSchema(),
        common_job_parameters,
    ).run(neo4j_session)
