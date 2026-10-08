"""
Sync GitHub organization security settings and domains.

Most of these settings are only visible to organization owners or to
credentials with organization administration permissions. Each source is
fetched independently: an unavailable source leaves its properties null
(unknown) and never fails the GitHub sync.
"""

import json
import logging
from typing import Any
from typing import cast
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.github.util import call_github_api
from cartography.intel.github.util import call_github_rest_api
from cartography.intel.github.util import handle_rate_limit_sleep
from cartography.models.github.domains import GitHubOrganizationDomainSchema
from cartography.models.github.orgs import GitHubOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


GITHUB_ORG_IDENTITY_GRAPHQL = """
    query($login: String!) {
        organization(login: $login) {
            url
            login
        }
    }
    """

# Each setting is queried on its own: both fields are non-nullable, so a
# FORBIDDEN error on one of them nulls the whole organization object.
GITHUB_ORG_IP_ALLOW_LIST_GRAPHQL = """
    query($login: String!) {
        organization(login: $login) {
            ipAllowListEnabledSetting
        }
    }
    """

GITHUB_ORG_NOTIFICATION_RESTRICTION_GRAPHQL = """
    query($login: String!) {
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


def _query_organization(
    token: Any,
    api_url: str,
    organization: str,
    query: str,
    cursor: str | None = None,
) -> dict[str, Any] | None:
    """
    Run a single-organization GraphQL query and return the organization object,
    or None if GitHub did not return it (missing permission or request failure).
    """
    variables: dict[str, Any] = {"login": organization}
    if cursor is not None:
        variables["cursor"] = cursor
    try:
        handle_rate_limit_sleep(token, api_url)
        response = call_github_api(query, json.dumps(variables), token, api_url)
    except requests.exceptions.RequestException as err:
        logger.warning(
            "GitHub GraphQL request for org %s failed: %s", organization, err
        )
        return None
    org = (response.get("data") or {}).get("organization")
    if org is None:
        messages = "; ".join(
            str(error.get("message", "")) for error in response.get("errors") or []
        )
        logger.warning(
            "GitHub did not return organization settings for org %s. "
            "This usually means the credential is not an organization owner. %s",
            organization,
            messages,
        )
        return None
    return cast(dict[str, Any], org)


def _get_rest_object(
    token: Any,
    api_url: str,
    endpoint: str,
    description: str,
) -> dict[str, Any] | None:
    try:
        return call_github_rest_api(endpoint, token, api_url)
    except requests.exceptions.RequestException as err:
        response = getattr(err, "response", None)
        status = response.status_code if response is not None else None
        logger.warning(
            "Skipping GitHub %s (%s): HTTP %s. The credential may lack the "
            "required permission, or the feature is not enabled.",
            description,
            endpoint,
            status,
        )
        return None


@timeit
def get_organization_identity(
    token: Any,
    api_url: str,
    organization: str,
) -> dict[str, Any] | None:
    """Return the canonical organization `url` and `login`, as used by the users sync."""
    return _query_organization(
        token, api_url, organization, GITHUB_ORG_IDENTITY_GRAPHQL
    )


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
    actions_permissions = _get_rest_object(
        token,
        api_url,
        f"{org_path}/actions/permissions",
        "Actions permissions",
    )
    selected_actions = None
    if (actions_permissions or {}).get("allowed_actions") == "selected":
        selected_actions = _get_rest_object(
            token,
            api_url,
            f"{org_path}/actions/permissions/selected-actions",
            "Actions allowed-actions list",
        )
    ip_allow_list = _query_organization(
        token, api_url, organization, GITHUB_ORG_IP_ALLOW_LIST_GRAPHQL
    )
    notification_restriction = _query_organization(
        token, api_url, organization, GITHUB_ORG_NOTIFICATION_RESTRICTION_GRAPHQL
    )
    return {
        "organization": _get_rest_object(
            token, api_url, org_path, "organization settings"
        ),
        "ip_allow_list": ip_allow_list,
        "notification_restriction": notification_restriction,
        "domains": get_domains(token, api_url, organization),
        "actions_permissions": actions_permissions,
        "selected_actions": selected_actions,
        "workflow_permissions": _get_rest_object(
            token,
            api_url,
            f"{org_path}/actions/permissions/workflow",
            "Actions default workflow permissions",
        ),
        "copilot": _get_rest_object(
            token,
            api_url,
            f"{org_path}/copilot/billing",
            "Copilot settings",
        ),
    }


def _enabled_setting(value: Any) -> bool | None:
    if value == "ENABLED":
        return True
    if value == "DISABLED":
        return False
    return None


def transform_organization(
    identity: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    org = settings.get("organization") or {}
    actions = settings.get("actions_permissions") or {}
    selected = settings.get("selected_actions") or {}
    workflow = settings.get("workflow_permissions") or {}
    copilot = settings.get("copilot") or {}
    domains = settings.get("domains")
    ip_allow_list = settings.get("ip_allow_list") or {}
    notification_restriction = settings.get("notification_restriction") or {}
    return {
        "url": identity["url"],
        "login": identity["login"],
        "name": org.get("name"),
        "is_verified": org.get("is_verified"),
        "two_factor_requirement_enabled": org.get("two_factor_requirement_enabled"),
        "default_repository_permission": org.get("default_repository_permission"),
        "members_can_create_repositories": org.get("members_can_create_repositories"),
        "members_can_create_public_repositories": org.get(
            "members_can_create_public_repositories"
        ),
        "members_can_create_private_repositories": org.get(
            "members_can_create_private_repositories"
        ),
        "members_can_create_internal_repositories": org.get(
            "members_can_create_internal_repositories"
        ),
        "members_can_fork_private_repositories": org.get(
            "members_can_fork_private_repositories"
        ),
        "members_can_create_public_pages": org.get("members_can_create_public_pages"),
        "web_commit_signoff_required": org.get("web_commit_signoff_required"),
        "deploy_keys_enabled_for_repositories": org.get(
            "deploy_keys_enabled_for_repositories"
        ),
        "advanced_security_enabled_for_new_repositories": org.get(
            "advanced_security_enabled_for_new_repositories"
        ),
        "dependabot_alerts_enabled_for_new_repositories": org.get(
            "dependabot_alerts_enabled_for_new_repositories"
        ),
        "dependabot_security_updates_enabled_for_new_repositories": org.get(
            "dependabot_security_updates_enabled_for_new_repositories"
        ),
        "dependency_graph_enabled_for_new_repositories": org.get(
            "dependency_graph_enabled_for_new_repositories"
        ),
        "secret_scanning_enabled_for_new_repositories": org.get(
            "secret_scanning_enabled_for_new_repositories"
        ),
        "secret_scanning_push_protection_enabled_for_new_repositories": org.get(
            "secret_scanning_push_protection_enabled_for_new_repositories"
        ),
        "secret_scanning_push_protection_custom_link_enabled": org.get(
            "secret_scanning_push_protection_custom_link_enabled"
        ),
        "ip_allow_list_enabled": _enabled_setting(
            ip_allow_list.get("ipAllowListEnabledSetting")
        ),
        "notification_delivery_restricted": _enabled_setting(
            notification_restriction.get(
                "notificationDeliveryRestrictionEnabledSetting"
            )
        ),
        "domain_count": len(domains) if domains is not None else None,
        "verified_domain_count": (
            sum(1 for domain in domains if domain.get("isVerified"))
            if domains is not None
            else None
        ),
        "actions_enabled_repositories": actions.get("enabled_repositories"),
        "actions_allowed_actions": actions.get("allowed_actions"),
        "actions_sha_pinning_required": actions.get("sha_pinning_required"),
        "actions_github_owned_allowed": selected.get("github_owned_allowed"),
        "actions_verified_allowed": selected.get("verified_allowed"),
        "actions_patterns_allowed": selected.get("patterns_allowed"),
        "actions_default_workflow_permissions": workflow.get(
            "default_workflow_permissions"
        ),
        "actions_can_approve_pull_request_reviews": workflow.get(
            "can_approve_pull_request_reviews"
        ),
        "copilot_plan_type": copilot.get("plan_type"),
        "copilot_seat_management_setting": copilot.get("seat_management_setting"),
        "copilot_seat_count": (copilot.get("seat_breakdown") or {}).get("total"),
        "copilot_public_code_suggestions": copilot.get("public_code_suggestions"),
        "copilot_ide_chat": copilot.get("ide_chat"),
        "copilot_platform_chat": copilot.get("platform_chat"),
        "copilot_cli": copilot.get("cli"),
    }


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
        if domain.get("id")
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
) -> None:
    identity = get_organization_identity(token, api_url, organization)
    if not identity or not identity.get("url") or not identity.get("login"):
        logger.warning(
            "Skipping GitHub organization settings for org %s: could not "
            "resolve the organization.",
            organization,
        )
        return
    update_tag = common_job_parameters["UPDATE_TAG"]
    settings = get(token, api_url, organization)
    load_organization(
        neo4j_session,
        transform_organization(identity, settings),
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
    load_domains(
        neo4j_session,
        transform_domains(domains),
        identity["url"],
        update_tag,
    )
    cleanup_domains(neo4j_session, identity["url"], update_tag)
