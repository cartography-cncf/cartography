import json
from unittest.mock import patch

import requests

import cartography.intel.github.organizations
import cartography.intel.github.util
from cartography.intel.github.organizations import GITHUB_ORG_DOMAINS_PAGINATED_GRAPHQL
from cartography.intel.github.organizations import GITHUB_ORG_IP_ALLOW_LIST_GRAPHQL
from cartography.intel.github.organizations import (
    GITHUB_ORG_NOTIFICATION_RESTRICTION_GRAPHQL,
)
from tests.data.github.organizations import ACTIONS_PERMISSIONS
from tests.data.github.organizations import COPILOT_BILLING
from tests.data.github.organizations import ORG_DOMAINS_PAGE_1
from tests.data.github.organizations import ORG_DOMAINS_PAGE_2
from tests.data.github.organizations import ORG_DOMAINS_PARTIAL
from tests.data.github.organizations import ORG_FORBIDDEN
from tests.data.github.organizations import ORG_IP_ALLOW_LIST
from tests.data.github.organizations import ORG_NOTIFICATION_RESTRICTION
from tests.data.github.organizations import ORG_REST
from tests.data.github.organizations import SELECTED_ACTIONS
from tests.data.github.organizations import WORKFLOW_PERMISSIONS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://api.github.com/graphql"
TEST_ORGANIZATION = "simpsoncorp"
FAKE_TOKEN = "fake-pat"
ORG_URL = "https://github.com/simpsoncorp"
ORG_DATA = {"url": ORG_URL, "login": TEST_ORGANIZATION}

OWNER_REST_RESPONSES = {
    "/orgs/simpsoncorp": ORG_REST,
    "/orgs/simpsoncorp/actions/permissions": ACTIONS_PERMISSIONS,
    "/orgs/simpsoncorp/actions/permissions/selected-actions": SELECTED_ACTIONS,
    "/orgs/simpsoncorp/actions/permissions/workflow": WORKFLOW_PERMISSIONS,
    "/orgs/simpsoncorp/copilot/billing": COPILOT_BILLING,
}


def _owner_graphql(query, variables, token, api_url):
    if query == GITHUB_ORG_IP_ALLOW_LIST_GRAPHQL:
        return ORG_IP_ALLOW_LIST
    if query == GITHUB_ORG_NOTIFICATION_RESTRICTION_GRAPHQL:
        return ORG_NOTIFICATION_RESTRICTION
    if query == GITHUB_ORG_DOMAINS_PAGINATED_GRAPHQL:
        if json.loads(variables).get("cursor") == "cursor-1":
            return ORG_DOMAINS_PAGE_2
        return ORG_DOMAINS_PAGE_1
    raise AssertionError("unexpected query")


def _member_graphql(query, variables, token, api_url):
    return ORG_FORBIDDEN


def _http_error(status):
    response = requests.Response()
    response.status_code = status
    return requests.exceptions.HTTPError(response=response)


def _owner_rest(endpoint, token, api_url):
    return OWNER_REST_RESPONSES[endpoint]


def _member_rest(endpoint, token, api_url):
    if endpoint == "/orgs/simpsoncorp":
        # Non-owners only see public organization fields.
        return {
            "login": "simpsoncorp",
            "html_url": ORG_URL,
            "name": "Simpson Corp",
            "is_verified": True,
        }
    raise _http_error(403)


def _reset_and_seed_graph(neo4j_session):
    neo4j_session.run(
        "MATCH (n) WHERE n:GitHubOrganization OR n:GitHubOrganizationDomain "
        "DETACH DELETE n",
    )
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization {id: $org_url})
        SET org.username = 'simpsoncorp', org.lastupdated = 1
        MERGE (stale:GitHubOrganizationDomain {id: 'VD_stale'})
        SET stale.domain = 'old.example', stale.lastupdated = 1
        MERGE (org)-[:RESOURCE {lastupdated: 1}]->(stale)
        """,
        org_url=ORG_URL,
    )


@patch.object(cartography.intel.github.organizations, "handle_rate_limit_sleep")
@patch.object(cartography.intel.github.util, "handle_rate_limit_sleep")
@patch.object(
    cartography.intel.github.util,
    "call_github_rest_api",
    side_effect=_owner_rest,
)
@patch.object(
    cartography.intel.github.util,
    "call_github_api",
    side_effect=_owner_graphql,
)
def test_sync_organization_settings(mock_graphql, mock_rest, _, __, neo4j_session):
    # Arrange
    _reset_and_seed_graph(neo4j_session)

    # Act
    cartography.intel.github.organizations.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
        ORG_DATA,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "GitHubOrganization",
        [
            "id",
            "username",
            "name",
            "two_factor_requirement_enabled",
            "default_repository_permission",
            "members_can_create_public_repositories",
            "members_can_fork_private_repositories",
            "secret_scanning_push_protection_enabled_for_new_repositories",
            "ip_allow_list_enabled",
            "notification_delivery_restricted",
            "verified_domain_count",
        ],
    ) == {
        (
            ORG_URL,
            "simpsoncorp",
            "Simpson Corp",
            False,
            "write",
            True,
            True,
            False,
            False,
            True,
            1,
        ),
    }
    assert check_nodes(
        neo4j_session,
        "GitHubOrganization",
        [
            "id",
            "actions_enabled_repositories",
            "actions_allowed_actions",
            "actions_sha_pinning_required",
            "actions_github_owned_allowed",
            "actions_verified_allowed",
            "actions_default_workflow_permissions",
            "actions_can_approve_pull_request_reviews",
        ],
    ) == {
        (
            ORG_URL,
            "all",
            "selected",
            False,
            True,
            False,
            "write",
            True,
        ),
    }
    patterns = neo4j_session.run(
        "MATCH (o:GitHubOrganization {id: $id}) RETURN o.actions_patterns_allowed AS p",
        id=ORG_URL,
    ).single()["p"]
    assert patterns == ["simpsoncorp/*", "docker/login-action@*"]
    assert check_nodes(
        neo4j_session,
        "GitHubOrganization",
        [
            "id",
            "copilot_plan_type",
            "copilot_seat_management_setting",
            "copilot_seat_count",
            "copilot_public_code_suggestions",
            "copilot_cli",
        ],
    ) == {(ORG_URL, "business", "assign_selected", 12, "allow", "disabled")}
    assert check_nodes(
        neo4j_session,
        "GitHubOrganizationDomain",
        ["id", "domain", "is_verified", "is_approved"],
    ) == {
        ("VD_kwDOAAABcc4AAAAA", "simpsoncorp.com", True, False),
        ("VD_kwDOAAABcc4AAAAB", "springfield-nuclear.example", False, True),
    }
    assert check_rels(
        neo4j_session,
        "GitHubOrganization",
        "id",
        "GitHubOrganizationDomain",
        "domain",
        "RESOURCE",
    ) == {
        (ORG_URL, "simpsoncorp.com"),
        (ORG_URL, "springfield-nuclear.example"),
    }


@patch.object(cartography.intel.github.organizations, "handle_rate_limit_sleep")
@patch.object(cartography.intel.github.util, "handle_rate_limit_sleep")
@patch.object(
    cartography.intel.github.util,
    "call_github_rest_api",
    side_effect=_member_rest,
)
@patch.object(
    cartography.intel.github.util,
    "call_github_api",
    side_effect=_member_graphql,
)
def test_sync_organization_settings_without_owner_access(
    mock_graphql, mock_rest, _, __, neo4j_session
):
    # Arrange
    _reset_and_seed_graph(neo4j_session)

    # Act
    cartography.intel.github.organizations.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
        ORG_DATA,
    )

    # Assert - unavailable settings are unknown, not false.
    assert check_nodes(
        neo4j_session,
        "GitHubOrganization",
        [
            "id",
            "name",
            "is_verified",
            "two_factor_requirement_enabled",
            "members_can_create_public_repositories",
            "actions_allowed_actions",
            "copilot_public_code_suggestions",
            "verified_domain_count",
        ],
    ) == {(ORG_URL, "Simpson Corp", True, None, None, None, None, None)}
    # Assert - an unavailable domain list preserves previously synced domains.
    assert check_nodes(neo4j_session, "GitHubOrganizationDomain", ["id"]) == {
        ("VD_stale",),
    }


def _partial_domains_graphql(query, variables, token, api_url):
    if query == GITHUB_ORG_DOMAINS_PAGINATED_GRAPHQL:
        return ORG_DOMAINS_PARTIAL
    return _owner_graphql(query, variables, token, api_url)


@patch.object(cartography.intel.github.organizations, "handle_rate_limit_sleep")
@patch.object(cartography.intel.github.util, "handle_rate_limit_sleep")
@patch.object(
    cartography.intel.github.util,
    "call_github_rest_api",
    side_effect=_owner_rest,
)
@patch.object(
    cartography.intel.github.util,
    "call_github_api",
    side_effect=_partial_domains_graphql,
)
def test_sync_organization_settings_partial_domain_page_skips_cleanup(
    mock_graphql, mock_rest, _, __, neo4j_session
):
    # Arrange
    _reset_and_seed_graph(neo4j_session)

    # Act
    cartography.intel.github.organizations.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
        ORG_DATA,
    )

    # Assert - a page with resolver errors is not a complete list: the domain
    # count is unknown and previously synced domains survive.
    assert check_nodes(
        neo4j_session, "GitHubOrganization", ["id", "verified_domain_count"]
    ) == {(ORG_URL, None)}
    assert check_nodes(neo4j_session, "GitHubOrganizationDomain", ["id"]) == {
        ("VD_stale",),
    }
