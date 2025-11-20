from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.groups
from cartography.intel.okta.sync_state import OktaSyncState
from tests.data.okta.groups import create_test_group
from tests.data.okta.groups import GROUP_MEMBERS_SAMPLE_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789
TEST_API_KEY = "test-api-key"


@patch.object(cartography.intel.okta.groups, "_get_okta_groups")
@patch.object(cartography.intel.okta.groups, "get_okta_group_members")
@patch.object(cartography.intel.okta.groups, "create_api_client")
def test_sync_okta_groups(
    mock_api_client, mock_get_members, mock_get_groups, neo4j_session
):
    """
    Test that Okta groups and their members are synced correctly to the graph.
    This follows the recommended pattern: mock get() functions, call sync(), verify outcomes.
    """
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

    sync_state = OktaSyncState()

    # Act - Call the main sync function
    cartography.intel.okta.groups.sync_okta_groups(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
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

    # Assert - Verify users were created from group members
    expected_users = {
        ("OKTA_USER_ID_1", "Jeremy", "Clarkson"),
        ("OKTA_USER_ID_2", "James", "May"),
        ("OKTA_USER_ID_3", "Richard", "Hammond"),
    }
    assert (
        check_nodes(neo4j_session, "OktaUser", ["id", "first_name", "last_name"])
        == expected_users
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
    for user_id in ["OKTA_USER_ID_1", "OKTA_USER_ID_2", "OKTA_USER_ID_3"]:
        assert (user_id, "group-001") in user_group_pairs
        assert (user_id, "group-002") in user_group_pairs


@patch.object(cartography.intel.okta.groups, "_get_okta_groups")
@patch.object(cartography.intel.okta.groups, "get_okta_group_members")
@patch.object(cartography.intel.okta.groups, "create_api_client")
def test_cleanup_okta_groups(
    mock_api_client, mock_get_members, mock_get_groups, neo4j_session
):
    """
    Test that cleanup removes stale groups correctly.
    """
    # Arrange - Create an old group with an old update tag
    OLD_UPDATE_TAG = 111111
    NEW_UPDATE_TAG = 222222

    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $NEW_UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(g:OktaGroup{id: 'stale-group', lastupdated: $OLD_UPDATE_TAG})
        """,
        ORG_ID=TEST_ORG_ID,
        OLD_UPDATE_TAG=OLD_UPDATE_TAG,
        NEW_UPDATE_TAG=NEW_UPDATE_TAG,
    )

    # Create a fresh group via sync
    test_group = create_test_group()
    test_group.id = "fresh-group"
    test_group.profile.name = "Fresh Group"

    mock_get_groups.return_value = [test_group]
    mock_get_members.return_value = []
    mock_api_client.return_value = MagicMock()

    sync_state = OktaSyncState()

    # Act - Run sync which should update the fresh group and then cleanup should remove the stale one
    cartography.intel.okta.groups.sync_okta_groups(
        neo4j_session,
        TEST_ORG_ID,
        NEW_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Now run cleanup
    from cartography.intel.okta import cleanup_okta_groups

    common_job_parameters = {
        "UPDATE_TAG": NEW_UPDATE_TAG,
        "OKTA_ORG_ID": TEST_ORG_ID,
    }
    cleanup_okta_groups(neo4j_session, common_job_parameters)

    # Assert - Only the fresh group should exist
    expected_groups = {("fresh-group",)}
    assert check_nodes(neo4j_session, "OktaGroup", ["id"]) == expected_groups


@patch.object(cartography.intel.okta.groups, "_get_okta_groups")
@patch.object(cartography.intel.okta.groups, "get_okta_group_members")
@patch.object(cartography.intel.okta.groups, "create_api_client")
def test_cleanup_okta_group_memberships(
    mock_api_client, mock_get_members, mock_get_groups, neo4j_session
):
    """
    Test that cleanup removes stale group memberships correctly.
    """
    # Arrange - Create group with users having different update tags on their relationships
    OLD_UPDATE_TAG = 111111
    NEW_UPDATE_TAG = 222222

    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $NEW_UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(g:OktaGroup{id: 'test-group', lastupdated: $NEW_UPDATE_TAG})
        MERGE (g)<-[r1:MEMBER_OF_OKTA_GROUP]-(u1:OktaUser{id: 'stale-user', lastupdated: $OLD_UPDATE_TAG})
        MERGE (g)<-[r2:MEMBER_OF_OKTA_GROUP]-(u2:OktaUser{id: 'fresh-user', lastupdated: $NEW_UPDATE_TAG})
        SET r1.lastupdated = $OLD_UPDATE_TAG,
            r2.lastupdated = $NEW_UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        OLD_UPDATE_TAG=OLD_UPDATE_TAG,
        NEW_UPDATE_TAG=NEW_UPDATE_TAG,
    )

    # Don't sync any new data, just run cleanup
    from cartography.intel.okta import cleanup_okta_groups

    common_job_parameters = {
        "UPDATE_TAG": NEW_UPDATE_TAG,
        "OKTA_ORG_ID": TEST_ORG_ID,
    }
    cleanup_okta_groups(neo4j_session, common_job_parameters)

    # Assert - Only the fresh-user relationship should remain
    result = neo4j_session.run(
        """
        MATCH (u:OktaUser)-[:MEMBER_OF_OKTA_GROUP]->(g:OktaGroup{id: 'test-group'})
        RETURN u.id as user_id
        """,
    )
    remaining_users = {r["user_id"] for r in result}
    assert remaining_users == {"fresh-user"}
