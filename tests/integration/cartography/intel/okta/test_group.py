from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.groups
from cartography.graph.job import GraphJob
from cartography.models.okta.group import OktaGroupSchema
from tests.data.okta.groups import create_test_group
from tests.data.okta.groups import create_test_group_member
from tests.data.okta.groups import create_test_group_role
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789


def _create_common_job_parameters():
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OKTA_ORG_ID": TEST_ORG_ID,
    }


@patch.object(cartography.intel.okta.groups, "_get_okta_groups", new_callable=AsyncMock)
@patch.object(
    cartography.intel.okta.groups, "_get_okta_group_members", new_callable=AsyncMock
)
@patch.object(
    cartography.intel.okta.groups, "_get_okta_group_roles", new_callable=AsyncMock
)
@patch.object(
    cartography.intel.okta.groups, "_get_okta_group_rules", new_callable=AsyncMock
)
def test_sync_okta_groups(
    mock_get_rules, mock_get_roles, mock_get_members, mock_get_groups, neo4j_session
):
    """
    Test that Okta groups and their members are synced correctly to the graph.
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

    # Create test users in the graph first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u1:OktaUser{id: 'user-001'})
        SET u1.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u2:OktaUser{id: 'user-002'})
        SET u2.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Create test members
    member1 = create_test_group_member()
    member1.id = "user-001"
    member2 = create_test_group_member()
    member2.id = "user-002"

    # Mock the API calls
    mock_get_groups.return_value = [test_group_1, test_group_2]
    mock_get_members.return_value = [member1, member2]
    mock_get_roles.return_value = []
    mock_get_rules.return_value = []

    okta_client = MagicMock()
    common_job_parameters = _create_common_job_parameters()

    # Act - Call the main sync function
    cartography.intel.okta.groups.sync_okta_groups(
        okta_client,
        neo4j_session,
        common_job_parameters,
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
    result = neo4j_session.run(
        """
        MATCH (u:OktaUser)-[:MEMBER_OF_OKTA_GROUP]->(g:OktaGroup)
        RETURN g.id as group_id, u.id as user_id
        """,
    )
    user_group_pairs = {(r["user_id"], r["group_id"]) for r in result}

    # Each of the 2 users should be in both groups (4 relationships total)
    assert len(user_group_pairs) == 4
    for user_id in ["user-001", "user-002"]:
        assert (user_id, "group-001") in user_group_pairs
        assert (user_id, "group-002") in user_group_pairs


@patch.object(cartography.intel.okta.groups, "_get_okta_groups", new_callable=AsyncMock)
@patch.object(
    cartography.intel.okta.groups, "_get_okta_group_members", new_callable=AsyncMock
)
@patch.object(
    cartography.intel.okta.groups, "_get_okta_group_roles", new_callable=AsyncMock
)
@patch.object(
    cartography.intel.okta.groups, "_get_okta_group_rules", new_callable=AsyncMock
)
def test_sync_okta_groups_with_roles(
    mock_get_rules, mock_get_roles, mock_get_members, mock_get_groups, neo4j_session
):
    """
    Test that Okta group roles are synced correctly.
    """
    # Arrange - Create test data
    test_group = create_test_group()
    test_group.id = "group-with-role"
    test_group.profile.name = "Admin Group"

    # Create test role
    test_role = create_test_group_role()
    test_role.id = "role-001"
    test_role.label = "App Admin"
    test_role.type.value = "APP_ADMIN"
    test_role.assignee = "group-with-role"

    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock the API calls
    mock_get_groups.return_value = [test_group]
    mock_get_members.return_value = []
    mock_get_roles.return_value = [test_role]
    mock_get_rules.return_value = []

    okta_client = MagicMock()
    common_job_parameters = _create_common_job_parameters()

    # Act
    cartography.intel.okta.groups.sync_okta_groups(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Verify role was created
    expected_roles = {("role-001", "App Admin")}
    actual_roles = check_nodes(neo4j_session, "OktaGroupRole", ["id", "label"])
    assert actual_roles == expected_roles

    # Assert - Verify group has role relationship
    expected_role_rels = {("group-with-role", "role-001")}
    actual_role_rels = check_rels(
        neo4j_session,
        "OktaGroup",
        "id",
        "OktaGroupRole",
        "id",
        "HAS_ROLE",
        rel_direction_right=True,
    )
    assert actual_role_rels == expected_role_rels


@patch.object(cartography.intel.okta.groups, "_get_okta_groups", new_callable=AsyncMock)
@patch.object(
    cartography.intel.okta.groups, "_get_okta_group_members", new_callable=AsyncMock
)
@patch.object(
    cartography.intel.okta.groups, "_get_okta_group_roles", new_callable=AsyncMock
)
@patch.object(
    cartography.intel.okta.groups, "_get_okta_group_rules", new_callable=AsyncMock
)
def test_cleanup_okta_groups(
    mock_get_rules, mock_get_roles, mock_get_members, mock_get_groups, neo4j_session
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
    mock_get_roles.return_value = []
    mock_get_rules.return_value = []

    okta_client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": NEW_UPDATE_TAG,
        "OKTA_ORG_ID": TEST_ORG_ID,
    }

    # Act - Run sync which will load fresh group then cleanup removes stale
    cartography.intel.okta.groups.sync_okta_groups(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Only the fresh group should exist
    expected_groups = {("fresh-group",)}
    assert check_nodes(neo4j_session, "OktaGroup", ["id"]) == expected_groups


@patch.object(cartography.intel.okta.groups, "_get_okta_groups", new_callable=AsyncMock)
@patch.object(
    cartography.intel.okta.groups, "_get_okta_group_members", new_callable=AsyncMock
)
@patch.object(
    cartography.intel.okta.groups, "_get_okta_group_roles", new_callable=AsyncMock
)
@patch.object(
    cartography.intel.okta.groups, "_get_okta_group_rules", new_callable=AsyncMock
)
def test_cleanup_okta_group_memberships(
    mock_get_rules, mock_get_roles, mock_get_members, mock_get_groups, neo4j_session
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
        MERGE (o)-[:RESOURCE]->(u1:OktaUser{id: 'stale-user', lastupdated: $NEW_UPDATE_TAG})
        MERGE (o)-[:RESOURCE]->(u2:OktaUser{id: 'fresh-user', lastupdated: $NEW_UPDATE_TAG})
        MERGE (u1)-[r1:MEMBER_OF_OKTA_GROUP]->(g)
        MERGE (u2)-[r2:MEMBER_OF_OKTA_GROUP]->(g)
        SET r1.lastupdated = $OLD_UPDATE_TAG,
            r2.lastupdated = $NEW_UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        OLD_UPDATE_TAG=OLD_UPDATE_TAG,
        NEW_UPDATE_TAG=NEW_UPDATE_TAG,
    )

    # Don't sync any new data, just run cleanup using GraphJob
    common_job_parameters = {
        "UPDATE_TAG": NEW_UPDATE_TAG,
        "OKTA_ORG_ID": TEST_ORG_ID,
    }
    GraphJob.from_node_schema(OktaGroupSchema(), common_job_parameters).run(
        neo4j_session
    )

    # Assert - Only the fresh-user relationship should remain
    result = neo4j_session.run(
        """
        MATCH (u:OktaUser)-[:MEMBER_OF_OKTA_GROUP]->(g:OktaGroup{id: 'test-group'})
        RETURN u.id as user_id
        """,
    )
    remaining_users = {r["user_id"] for r in result}
    assert remaining_users == {"fresh-user"}
