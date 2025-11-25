from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.groups
from tests.data.okta.groups import create_test_group
from tests.data.okta.groups import GROUP_MEMBERS_SAMPLE_DATA
from tests.integration.cartography.intel.okta.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789
TEST_API_KEY = "test-api-key"


def _ensure_local_neo4j_has_test_groups(neo4j_session):
    """
    Helper function to pre-load test groups into Neo4j for tests that depend on groups existing.
    Also ensures test users exist since groups reference users.
    """
    # First ensure users exist (groups reference users)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Create test groups
    test_group_1 = create_test_group()
    test_group_1.id = "group-001"
    test_group_1.profile.name = "Engineering"
    test_group_1.profile.description = "Engineering team"

    test_group_2 = create_test_group()
    test_group_2.id = "group-002"
    test_group_2.profile.name = "Product"
    test_group_2.profile.description = "Product team"

    # Transform groups with member relationships to existing users
    group_members_map = {
        "group-001": ["user-001", "user-002"],
        "group-002": ["user-001", "user-002"],
    }
    group_list, _ = cartography.intel.okta.groups.transform_okta_group_list(
        [test_group_1, test_group_2],
        group_members_map,
    )
    cartography.intel.okta.groups._load_okta_groups(
        neo4j_session,
        TEST_ORG_ID,
        group_list,
        TEST_UPDATE_TAG,
    )


@patch.object(cartography.intel.okta.groups, "_get_okta_groups")
@patch.object(cartography.intel.okta.groups, "_get_okta_group_members")
@patch.object(cartography.intel.okta.groups, "create_api_client")
def test_sync_okta_groups(
    mock_api_client, mock_get_members, mock_get_groups, neo4j_session
):
    """
    Test that Okta groups and their members are synced correctly to the graph.
    This follows the recommended pattern: mock get() functions, call sync(), verify outcomes.
    """
    # Arrange - Ensure test users exist in the graph
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Arrange - Create test data
    test_group_1 = create_test_group()
    test_group_1.id = "group-001"
    test_group_1.profile.name = "Engineering"
    test_group_1.profile.description = "Engineering team"

    test_group_2 = create_test_group()
    test_group_2.id = "group-002"
    test_group_2.profile.name = "Product"
    test_group_2.profile.description = "Product team"

    # Mock the API calls
    mock_get_groups.return_value = [test_group_1, test_group_2]
    mock_get_members.return_value = GROUP_MEMBERS_SAMPLE_DATA
    mock_api_client.return_value = MagicMock()

    # Create the OktaOrganization node first (normally done by organization.create_okta_organization)
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Act - Call the main sync function
    cartography.intel.okta.groups.sync_okta_groups(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - Verify groups were created with correct properties
    expected_groups = {
        ("group-001", "Engineering"),
        ("group-002", "Product"),
    }
    assert check_nodes(neo4j_session, "OktaGroup", ["id", "name"]) == expected_groups

    # Assert - Verify groups are connected to organization
    expected_org_rels = {
        (TEST_ORG_ID, "group-001"),
        (TEST_ORG_ID, "group-002"),
    }
    assert (
        check_rels(
            neo4j_session,
            "OktaOrganization",
            "id",
            "OktaGroup",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_org_rels
    )

    # Assert - Verify users are members of groups
    # Note: Each group got the same members (because mock returns same data for both groups)
    result = neo4j_session.run(
        """
        MATCH (u:OktaUser)-[:MEMBER_OF_OKTA_GROUP]->(g:OktaGroup)
        RETURN u.id as user_id, g.id as group_id
        """,
    )
    user_group_pairs = {(r["user_id"], r["group_id"]) for r in result}

    # Each of the 3 users should be in both groups (6 relationships total)
    assert len(user_group_pairs) == 6
    for user_id in ["user-001", "user-002", "user-003"]:
        assert (user_id, "group-001") in user_group_pairs
        assert (user_id, "group-002") in user_group_pairs
