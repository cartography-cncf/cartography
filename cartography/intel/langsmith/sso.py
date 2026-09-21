import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.langsmith.util import LangSmithClient
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
    providers = transform_providers(get_sso_settings(client, org_id))
    policies = transform_policies(get_access_policies(client, org_id))
    data_planes = get_data_planes(client, org_id)
    load_sso(
        neo4j_session,
        providers,
        policies,
        data_planes,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_sso_settings(client: LangSmithClient, org_id: str) -> list[dict[str, Any]]:
    return client.get("/api/v1/orgs/current/sso-settings", org_id=org_id)


@timeit
def get_access_policies(client: LangSmithClient, org_id: str) -> list[dict[str, Any]]:
    payload = client.get("/api/v1/platform/orgs/current/access-policies", org_id=org_id)
    return payload.get("access_policies") or []


@timeit
def get_data_planes(client: LangSmithClient, org_id: str) -> list[dict[str, Any]]:
    payload = client.get("/orgs/current/data-planes", org_id=org_id)
    if isinstance(payload, dict):
        return payload.get("data_planes") or []
    return payload


def transform_providers(providers: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                "default_workspace_role_id": provider.get("default_workspace_role_id"),
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


def transform_policies(policies: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                "role_ids": policy.get("role_ids") or [],
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


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    for schema in (
        LangSmithSSOProviderSchema(),
        LangSmithAccessPolicySchema(),
        LangSmithDataPlaneSchema(),
    ):
        GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)
