import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.langsmith.util import LangSmithClient
from cartography.models.langsmith.organization import LangSmithOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: LangSmithClient,
    org_id_override: str | None,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """Load every organization the credential can see and return them for per-org syncs."""
    org_ids = get_organization_ids(client, org_id_override)
    organizations = [
        transform_organization(org_id, get_info(client, org_id)) for org_id in org_ids
    ]
    load_organizations(
        neo4j_session, organizations, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
    return organizations


@timeit
def get_organization_ids(
    client: LangSmithClient,
    org_id_override: str | None,
) -> list[str]:
    if org_id_override:
        return [org_id_override]
    # /api/v1/orgs is not reachable with a personal access token: it is gated on a UI
    # session JWT and returns 403 for both X-Api-Key and bearer PAT auth. The workspace
    # listing is reachable and carries organization_id, so organizations are discovered
    # from there instead.
    workspaces = client.get("/api/v1/workspaces")
    org_ids = {
        workspace["organization_id"]
        for workspace in workspaces
        if workspace.get("organization_id")
    }
    return sorted(org_ids)


@timeit
def get_info(client: LangSmithClient, org_id: str) -> dict[str, Any]:
    return client.get("/api/v1/orgs/current/info", org_id=org_id)


def transform_organization(org_id: str, info: dict[str, Any]) -> dict[str, Any]:
    """
    Shape an organization for ingest.

    OrganizationInfo.id is nullable, so the id is taken from the organization we scoped the
    request to rather than from the response body.
    """
    return {
        "id": org_id,
        "display_name": info.get("display_name"),
        "tier": info.get("tier"),
        "disabled": info.get("disabled"),
        "is_personal": info.get("is_personal"),
        "sso_only": info.get("sso_only"),
        "jit_provisioning_enabled": info.get("jit_provisioning_enabled"),
        "invites_enabled": info.get("invites_enabled"),
        "workspace_admin_can_invite_to_org": info.get(
            "workspace_admin_can_invite_to_org"
        ),
        "pat_creation_disabled": info.get("pat_creation_disabled"),
        "public_sharing_disabled": info.get("public_sharing_disabled"),
        "max_api_key_expiry_days": info.get("max_api_key_expiry_days"),
        "max_pat_expiry_days": info.get("max_pat_expiry_days"),
        "max_service_key_expiry_days": info.get("max_service_key_expiry_days"),
        "ip_allowlist_enabled": info.get("ip_allowlist_enabled"),
        "sso_login_slug": info.get("sso_login_slug"),
        "security_contact": info.get("security_contact"),
    }


@timeit
def load_organizations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        LangSmithOrganizationSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(LangSmithOrganizationSchema(), common_job_parameters).run(
        neo4j_session
    )
