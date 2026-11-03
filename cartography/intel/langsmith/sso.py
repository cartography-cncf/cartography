import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.intel.langsmith.util import cleanup_if_complete
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.intel.langsmith.util import org_scoped_id
from cartography.models.langsmith.accesspolicy import LangSmithAccessPolicySchema
from cartography.models.langsmith.dataplane import LangSmithDataPlaneSchema
from cartography.models.langsmith.ssoprovider import LangSmithSSOProviderSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: LangSmithClient,
    org_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_providers, providers_complete = get_sso_settings(client, org_id)
    raw_policies, policies_complete = get_access_policies(client, org_id)
    data_planes, data_planes_complete = get_data_planes(client, org_id)
    load_sso(
        neo4j_session,
        transform_providers(raw_providers, org_id),
        transform_policies(raw_policies, org_id),
        data_planes,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup_if_complete(
        neo4j_session,
        LangSmithSSOProviderSchema(),
        providers_complete,
        common_job_parameters,
    )
    cleanup_if_complete(
        neo4j_session,
        LangSmithAccessPolicySchema(),
        policies_complete,
        common_job_parameters,
    )
    cleanup_if_complete(
        neo4j_session,
        LangSmithDataPlaneSchema(),
        data_planes_complete,
        common_job_parameters,
    )


def _get_optional(client: LangSmithClient, org_id: str, path: str) -> tuple[Any, bool]:
    """
    Fetch an organization-level listing that a credential or plan may not expose.

    A 404 means the route is not served for this organization (no SSO configured, no
    hybrid data plane, or a plan without access policies), which is a complete empty
    answer. A 401/403 means the listing exists but is hidden, so it is reported incomplete.
    """
    try:
        return client.get(path, org_id=org_id), True
    except LangSmithFetchError as err:
        logger.warning("Skipping LangSmith %s: %s", path, err)
        return None, err.not_found


@timeit
def get_sso_settings(
    client: LangSmithClient, org_id: str
) -> tuple[list[dict[str, Any]], bool]:
    payload, complete = _get_optional(
        client, org_id, "/api/v1/orgs/current/sso-settings"
    )
    return payload or [], complete


@timeit
def get_access_policies(
    client: LangSmithClient, org_id: str
) -> tuple[list[dict[str, Any]], bool]:
    payload, complete = _get_optional(
        client, org_id, "/api/v1/platform/orgs/current/access-policies"
    )
    return (payload or {}).get("access_policies") or [], complete


@timeit
def get_data_planes(
    client: LangSmithClient, org_id: str
) -> tuple[list[dict[str, Any]], bool]:
    """
    Fetch the organization's registered data planes.

    Data planes only exist for hybrid and self-hosted deployments, and the route is not
    served for organizations without one.
    """
    payload, complete = _get_optional(client, org_id, "/orgs/current/data-planes")
    if isinstance(payload, dict):
        return payload.get("data_planes") or [], complete
    return payload or [], complete


def transform_providers(
    providers: list[dict[str, Any]], org_id: str
) -> list[dict[str, Any]]:
    """
    Shape SSO providers for ingest.

    The provider's SAML metadata XML is reduced to a boolean: it is configuration detail that
    would bloat the graph, and its presence is the only part worth querying.
    """
    transformed = []
    for provider in providers:
        transformed.append(
            {
                "id": provider["id"],
                "provider_id": provider["provider_id"],
                "metadata_url": provider.get("metadata_url"),
                "has_metadata_xml": bool(provider.get("metadata_xml")),
                "attribute_mapping_load_error": provider.get(
                    "attribute_mapping_load_error"
                ),
                "sso_groups_enabled": provider.get("sso_groups_enabled"),
                "sso_groups_claim_field": provider.get("sso_groups_claim_field"),
                "sso_groups_required": provider.get("sso_groups_required"),
                "sso_groups_role_sync_enabled": provider.get(
                    "sso_groups_role_sync_enabled"
                ),
                "default_workspace_role_id": org_scoped_id(
                    org_id, provider.get("default_workspace_role_id")
                ),
                "default_workspace_ids": provider.get("default_workspace_ids") or [],
            }
        )
    return transformed


def _summarize_conditions(condition_groups: list[dict[str, Any]] | None) -> str | None:
    """
    Render a policy's nested attribute condition groups as one readable line.

    The raw structure is arbitrarily nested JSON, which Neo4j cannot store as a property, so
    it is flattened into a summary rather than dropped entirely.
    """
    if not condition_groups:
        return None
    parts: list[str] = []
    for group in condition_groups:
        for condition in group.get("conditions") or []:
            attribute = condition.get("attribute") or condition.get("key")
            operator = condition.get("operator") or "="
            value = condition.get("value") or condition.get("values")
            parts.append(f"{attribute} {operator} {value}")
    return " AND ".join(parts) if parts else None


def transform_policies(
    policies: list[dict[str, Any]], org_id: str
) -> list[dict[str, Any]]:
    transformed = []
    for policy in policies:
        transformed.append(
            {
                "id": policy["id"],
                "name": policy.get("name"),
                "description": policy.get("description"),
                "effect": policy.get("effect"),
                "condition_summary": _summarize_conditions(
                    policy.get("condition_groups")
                ),
                "role_ids": [
                    org_scoped_id(org_id, role_id)
                    for role_id in policy.get("role_ids") or []
                ],
            }
        )
    return transformed


@timeit
def load_sso(
    neo4j_session: neo4j.Session,
    providers: list[dict[str, Any]],
    policies: list[dict[str, Any]],
    data_planes: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        LangSmithSSOProviderSchema(),
        providers,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
    load(
        neo4j_session,
        LangSmithAccessPolicySchema(),
        policies,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
    load(
        neo4j_session,
        LangSmithDataPlaneSchema(),
        data_planes,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
