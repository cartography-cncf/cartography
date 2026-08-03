from unittest.mock import patch

import requests

import cartography.intel.anthropic.invites
import tests.data.anthropic.invites
from tests.integration.cartography.intel.anthropic.test_organization import (
    _ensure_local_neo4j_has_test_organization,
)
from tests.integration.cartography.intel.anthropic.test_rbac import (
    _ensure_local_neo4j_has_test_rbac_groups,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "8834c225-ea27-405a-aea9-5ed5f07f4858"


@patch.object(
    cartography.intel.anthropic.invites,
    "get",
    return_value=(TEST_ORG_ID, tests.data.anthropic.invites.ANTHROPIC_INVITES),
)
def test_load_anthropic_invites(mock_api, neo4j_session):
    """
    Ensure that invites get loaded, including the groups they grant on acceptance
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.anthropic.com/v1",
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    _ensure_local_neo4j_has_test_rbac_groups(neo4j_session)

    # Act
    cartography.intel.anthropic.invites.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert invites exist. A pending one is an un-redeemed grant of its role.
    assert check_nodes(
        neo4j_session, "AnthropicInvite", ["id", "email", "role", "status"]
    ) == {
        (
            "invite_015gWxCN9Hfg2QhZwTK7Mdeu",
            "lisa@simpson.corp",
            "developer",
            "pending",
        ),
        (
            "invite_026hXyDO0Igh3RiAxUL8Nefv",
            "bart@simpson.corp",
            "admin",
            "accepted",
        ),
    }

    # Assert invites are linked to the correct org
    assert check_rels(
        neo4j_session,
        "AnthropicInvite",
        "id",
        "AnthropicOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("invite_015gWxCN9Hfg2QhZwTK7Mdeu", TEST_ORG_ID),
        ("invite_026hXyDO0Igh3RiAxUL8Nefv", TEST_ORG_ID),
    }

    # Assert only the invite carrying a group id edges to it
    assert check_rels(
        neo4j_session,
        "AnthropicInvite",
        "id",
        "AnthropicRbacGroup",
        "id",
        "GRANTS_MEMBERSHIP_OF",
        rel_direction_right=True,
    ) == {
        (
            "invite_015gWxCN9Hfg2QhZwTK7Mdeu",
            "rbac_group_012rppKaSVsmTo6NqRDXQXNF",
        ),
    }
