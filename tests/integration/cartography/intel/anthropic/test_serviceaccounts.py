import copy
from unittest.mock import patch

import requests

import cartography.intel.anthropic.serviceaccounts
import tests.data.anthropic.serviceaccounts
from tests.integration.cartography.intel.anthropic.test_organization import (
    _ensure_local_neo4j_has_test_organization,
)
from tests.integration.cartography.intel.anthropic.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "8834c225-ea27-405a-aea9-5ed5f07f4858"
TEST_WORKSPACE_ID = "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ"


def _ensure_local_neo4j_has_test_service_accounts(neo4j_session):
    service_accounts = copy.deepcopy(
        tests.data.anthropic.serviceaccounts.ANTHROPIC_SERVICE_ACCOUNTS
    )
    for service_account in service_accounts:
        cartography.intel.anthropic.serviceaccounts.transform_service_account(
            service_account,
            tests.data.anthropic.serviceaccounts.ANTHROPIC_SERVICE_ACCOUNT_WORKSPACES[
                service_account["id"]
            ],
        )
    cartography.intel.anthropic.serviceaccounts.load_service_accounts(
        neo4j_session,
        service_accounts,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.anthropic.serviceaccounts,
    "get_service_account_workspaces",
    side_effect=lambda _session, _url, service_account_id: (
        tests.data.anthropic.serviceaccounts.ANTHROPIC_SERVICE_ACCOUNT_WORKSPACES[
            service_account_id
        ]
    ),
)
@patch.object(
    cartography.intel.anthropic.serviceaccounts,
    "get",
    return_value=copy.deepcopy(
        tests.data.anthropic.serviceaccounts.ANTHROPIC_SERVICE_ACCOUNTS
    ),
)
def test_load_anthropic_service_accounts(mock_api, mock_api_workspaces, neo4j_session):
    """
    Ensure that service accounts and their workspace memberships get loaded
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.anthropic.com/v1",
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)

    # Act
    cartography.intel.anthropic.serviceaccounts.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert service accounts exist. organization_role is the privilege signal: only
    # an admin service account can back an org:admin federation rule.
    expected_nodes = {
        ("svac_01Nb5RtYuIoPaSdFgHjKlZxC", "reactor-telemetry", "developer"),
        ("svac_01Pq8WeRtYuIoPaSdFgHjKlM", "cartography-collector", "admin"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "AnthropicServiceAccount",
            ["id", "name", "organization_role"],
        )
        == expected_nodes
    )

    # Assert service accounts are linked to the correct org
    expected_rels = {
        ("svac_01Nb5RtYuIoPaSdFgHjKlZxC", TEST_ORG_ID),
        ("svac_01Pq8WeRtYuIoPaSdFgHjKlM", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicServiceAccount",
            "id",
            "AnthropicOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert both are members of the workspace
    expected_rels = {
        ("svac_01Nb5RtYuIoPaSdFgHjKlZxC", TEST_WORKSPACE_ID),
        ("svac_01Pq8WeRtYuIoPaSdFgHjKlM", TEST_WORKSPACE_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicServiceAccount",
            "id",
            "AnthropicWorkspace",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert only the workspace_admin member administers it
    expected_rels = {
        ("svac_01Pq8WeRtYuIoPaSdFgHjKlM", TEST_WORKSPACE_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicServiceAccount",
            "id",
            "AnthropicWorkspace",
            "id",
            "ADMIN_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
