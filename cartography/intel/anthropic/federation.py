from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.anthropic.util import paginated_get_by_page
from cartography.models.anthropic.federationissuer import (
    AnthropicFederationIssuerSchema,
)
from cartography.models.anthropic.federationrule import AnthropicFederationRuleSchema
from cartography.util import timeit

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    issuers = get_issuers(api_session, common_job_parameters["BASE_URL"])
    for issuer in issuers:
        transform_issuer(issuer)
    load_issuers(
        neo4j_session,
        issuers,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )

    rules = get_rules(api_session, common_job_parameters["BASE_URL"])
    for rule in rules:
        enablements = get_rule_workspaces(
            api_session,
            common_job_parameters["BASE_URL"],
            rule["id"],
        )
        transform_rule(rule, enablements)
    load_rules(
        neo4j_session,
        rules,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )

    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_issuers(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/organizations/federation_issuers",
        timeout=_TIMEOUT,
    )


@timeit
def get_rules(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/organizations/federation_rules",
        timeout=_TIMEOUT,
    )


@timeit
def get_rule_workspaces(
    api_session: requests.Session,
    base_url: str,
    federation_rule_id: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/organizations/federation_rules/{federation_rule_id}/workspaces",
        timeout=_TIMEOUT,
    )


def transform_issuer(issuer: dict[str, Any]) -> None:
    """Flatten the jwks discriminated union into scalar properties."""
    jwks = issuer.pop("jwks", None) or {}
    issuer["jwks_type"] = jwks.get("type")
    # Only the explicit_url variant carries a url; discovery derives it from the
    # issuer, and inline embeds the keys directly.
    issuer["jwks_url"] = jwks.get("url")


def transform_rule(rule: dict[str, Any], enablements: list[dict[str, Any]]) -> None:
    """Flatten the claims matcher and collect every workspace the rule is enabled on."""
    claims = (rule.get("match") or {}).get("claims") or {}
    rule["match_claims"] = sorted(f"{key}={value}" for key, value in claims.items())

    workspace_ids = {e["workspace_id"] for e in enablements}
    workspace_ids.update(rule.get("workspace_ids") or [])
    # Rules predating the multi-workspace sub-resource carry a single legacy binding.
    legacy_workspace_id = rule.get("workspace_id")
    if legacy_workspace_id:
        workspace_ids.add(legacy_workspace_id)
    rule["workspace_ids"] = sorted(workspace_ids)


@timeit
def load_issuers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicFederationIssuerSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=ORG_ID,
    )


@timeit
def load_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicFederationRuleSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=ORG_ID,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    # Rules first: they reference the issuers.
    GraphJob.from_node_schema(
        AnthropicFederationRuleSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        AnthropicFederationIssuerSchema(), common_job_parameters
    ).run(neo4j_session)
