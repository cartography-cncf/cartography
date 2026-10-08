"""
Sync GitHub organization security settings and domains.

Most of these settings are only visible to organization owners or to
credentials with organization administration permissions. Each source is
fetched independently: a source the credential cannot read leaves its
properties null (unknown), while any other request failure propagates so a
transient error never overwrites known settings.
"""

import logging
from typing import Any
from urllib.parse import quote

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.github.util import call_github_rest_api_or_none
from cartography.intel.github.util import fetch_page
from cartography.intel.github.util import handle_rate_limit_sleep
from cartography.models.github.domains import GitHubOrganizationDomainSchema
from cartography.models.github.orgs import GitHubOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# Each setting is queried on its own: both fields are non-nullable, so a
# FORBIDDEN error on one of them nulls the whole organization object. $cursor is
# unused but declared because fetch_page always sends it.
GITHUB_ORG_IP_ALLOW_LIST_GRAPHQL = """
    query($login: String!, $cursor: String) {
        organization(login: $login) {
            ipAllowListEnabledSetting
        }
    }
    """

GITHUB_ORG_NOTIFICATION_RESTRICTION_GRAPHQL = """
    query($login: String!, $cursor: String) {
        organization(login: $login) {
            notificationDeliveryRestrictionEnabledSetting
        }
    }
    """

GITHUB_ORG_DOMAINS_PAGINATED_GRAPHQL = """
    query($login: String!, $cursor: String) {
        organization(login: $login) {
            domains(first: 100, after: $cursor) {
                pageInfo {
                    endCursor
                    hasNextPage
                }
                nodes {
                    id
                    domain
                    isVerified
                    isApproved
                    isRequiredForPolicyEnforcement
                    createdAt
                    updatedAt
                }
            }
        }
    }
    """

# REST fields copied onto the node under the same name.
_ORG_REST_FIELDS = (
    "name",
    "is_verified",
    "two_factor_requirement_enabled",
    "default_repository_permission",
    "members_can_create_repositories",
    "members_can_create_public_repositories",
    "members_can_create_private_repositories",
    "members_can_create_internal_repositories",
    "members_can_fork_private_repositories",
    "members_can_create_public_pages",
    "web_commit_signoff_required",
    "deploy_keys_enabled_for_repositories",
    "advanced_security_enabled_for_new_repositories",
    "dependabot_alerts_enabled_for_new_repositories",
    "dependabot_security_updates_enabled_for_new_repositories",
    "dependency_graph_enabled_for_new_repositories",
    "secret_scanning_enabled_for_new_repositories",
    "secret_scanning_push_protection_enabled_for_new_repositories",
    "secret_scanning_push_protection_custom_link_enabled",
)

# (settings source, node property, REST field) for fields that are renamed.
_PREFIXED_FIELDS = (
    ("actions_permissions", "actions_enabled_repositories", "enabled_repositories"),
    ("actions_permissions", "actions_allowed_actions", "allowed_actions"),
    ("actions_permissions", "actions_sha_pinning_required", "sha_pinning_required"),
    ("selected_actions", "actions_github_owned_allowed", "github_owned_allowed"),
    ("selected_actions", "actions_verified_allowed", "verified_allowed"),
    ("selected_actions", "actions_patterns_allowed", "patterns_allowed"),
    (
        "workflow_permissions",
        "actions_default_workflow_permissions",
        "default_workflow_permissions",
    ),
    (
        "workflow_permissions",
        "actions_can_approve_pull_request_reviews",
        "can_approve_pull_request_reviews",
    ),
    ("copilot", "copilot_plan_type", "plan_type"),
    ("copilot", "copilot_seat_management_setting", "seat_management_setting"),
    ("copilot", "copilot_public_code_suggestions", "public_code_suggestions"),
    ("copilot", "copilot_ide_chat", "ide_chat"),
    ("copilot", "copilot_platform_chat", "platform_chat"),
    ("copilot", "copilot_cli", "cli"),
)


def _query_organization(
    token: Any,
    api_url: str,
    organization: str,
    query: str,
    cursor: str | None = None,
) -> dict[str, Any] | None:
    """
    Run a single-organization GraphQL query and return the organization object,
    or None when GitHub reported any error. A FORBIDDEN error means the
    credential is not an organization owner; a resolver error can leave the
    object partially populated, which must not be mistaken for a complete
    snapshot. Request failures propagate.
    """
    response = fetch_page(token, api_url, organization, query, cursor)
    errors = response.get("errors") or []
    if errors:
        logger.warning(
            "GitHub did not return organization settings for org %s. "
            "This usually means the credential is not an organization owner. %s",
            organization,
            "; ".join(str(error.get("message", "")) for error in errors),
        )
        return None
    return (response.get("data") or {}).get("organization")


@timeit
def get_domains(
    token: Any,
    api_url: str,
    organization: str,
) -> list[dict[str, Any]] | None:
    """
    Return all domains configured on the organization, or None when the list
    is unavailable. Only organization owners can read domains.
    """
    domains: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        org = _query_organization(
            token,
            api_url,
            organization,
            GITHUB_ORG_DOMAINS_PAGINATED_GRAPHQL,
            cursor,
        )
        connection = org.get("domains") if org else None
        if connection is None:
            return None
        domains.extend(node for node in connection.get("nodes") or [] if node)
        page_info = connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            return domains
        cursor = page_info.get("endCursor")


@timeit
def get(
    token: Any,
    api_url: str,
    organization: str,
) -> dict[str, Any]:
    """Fetch every organization settings source. Unavailable sources are None."""
    org_path = f"/orgs/{quote(organization, safe='')}"
    rest = {
        "organization": (org_path, "organization settings"),
        "actions_permissions": (
            f"{org_path}/actions/permissions",
            "Actions permissions",
        ),
        "workflow_permissions": (
            f"{org_path}/actions/permissions/workflow",
            "Actions default workflow permissions",
        ),
        "copilot": (f"{org_path}/copilot/billing", "Copilot settings"),
    }
    settings: dict[str, Any] = {
        key: call_github_rest_api_or_none(endpoint, token, api_url, description)
        for key, (endpoint, description) in rest.items()
    }
    settings["selected_actions"] = None
    if (settings["actions_permissions"] or {}).get("allowed_actions") == "selected":
        settings["selected_actions"] = call_github_rest_api_or_none(
            f"{org_path}/actions/permissions/selected-actions",
            token,
            api_url,
            "Actions allowed-actions list",
        )
    # These queries cost one GraphQL point each, so one budget check covers them.
    handle_rate_limit_sleep(token, api_url)
    settings["ip_allow_list"] = _query_organization(
        token, api_url, organization, GITHUB_ORG_IP_ALLOW_LIST_GRAPHQL
    )
    settings["notification_restriction"] = _query_organization(
        token, api_url, organization, GITHUB_ORG_NOTIFICATION_RESTRICTION_GRAPHQL
    )
    settings["domains"] = get_domains(token, api_url, organization)
    return settings


def _enabled_setting(value: Any) -> bool | None:
    return {"ENABLED": True, "DISABLED": False}.get(value)


def transform_organization(
    org_data: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    """
    :param org_data: The organization's ``url`` and ``login`` as reported by
        GitHub GraphQL; ``url`` is the node ID every other GitHub sync attaches to.
    """
    org = settings.get("organization") or {}
    domains = settings.get("domains")
    transformed: dict[str, Any] = {"url": org_data["url"], "login": org_data["login"]}
    transformed.update({field: org.get(field) for field in _ORG_REST_FIELDS})
    for source, prop, field in _PREFIXED_FIELDS:
        transformed[prop] = (settings.get(source) or {}).get(field)
    transformed.update(
        {
            "ip_allow_list_enabled": _enabled_setting(
                (settings.get("ip_allow_list") or {}).get("ipAllowListEnabledSetting")
            ),
            "notification_delivery_restricted": _enabled_setting(
                (settings.get("notification_restriction") or {}).get(
                    "notificationDeliveryRestrictionEnabledSetting"
                )
            ),
            "verified_domain_count": (
                sum(1 for domain in domains if domain.get("isVerified"))
                if domains is not None
                else None
            ),
            "copilot_seat_count": (
                (settings.get("copilot") or {}).get("seat_breakdown") or {}
            ).get("total"),
        }
    )
    return transformed


def transform_domains(domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": domain["id"],
            "domain": domain.get("domain"),
            "is_verified": domain.get("isVerified"),
            "is_approved": domain.get("isApproved"),
            "is_required_for_policy_enforcement": domain.get(
                "isRequiredForPolicyEnforcement"
            ),
            "created_at": domain.get("createdAt"),
            "updated_at": domain.get("updatedAt"),
        }
        for domain in domains
    ]


@timeit
def load_organization(
    neo4j_session: neo4j.Session,
    org: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitHubOrganizationSchema(),
        [org],
        lastupdated=update_tag,
    )


@timeit
def load_domains(
    neo4j_session: neo4j.Session,
    domains: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitHubOrganizationDomainSchema(),
        domains,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_domains(
    neo4j_session: neo4j.Session,
    org_url: str,
    update_tag: int,
) -> None:
    GraphJob.from_node_schema(
        GitHubOrganizationDomainSchema(),
        {"UPDATE_TAG": update_tag, "org_url": org_url},
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    token: Any,
    api_url: str,
    organization: str,
    org_data: dict[str, Any],
) -> None:
    """
    Load the organization node with its security settings and domains.

    This is the only sync that writes the ``GitHubOrganization`` node, so it runs
    before every sync that attaches resources to it.

    :param org_data: The organization's ``url`` and ``login`` from GitHub GraphQL.
    """
    update_tag = common_job_parameters["UPDATE_TAG"]
    org_url = org_data["url"]
    settings = get(token, api_url, organization)
    load_organization(
        neo4j_session,
        transform_organization(org_data, settings),
        update_tag,
    )
    domains = settings["domains"]
    if domains is None:
        logger.warning(
            "Skipping GitHub domain cleanup for org %s because the domain list "
            "was unavailable.",
            organization,
        )
        return
    load_domains(neo4j_session, transform_domains(domains), org_url, update_tag)
    cleanup_domains(neo4j_session, org_url, update_tag)
