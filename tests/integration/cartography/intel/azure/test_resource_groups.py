from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.resource_groups as resource_groups
from tests.data.azure.resource_group import MOCK_RESOURCE_GROUPS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.resource_groups.get_resource_groups")
def test_sync_resource_groups(mock_get, neo4j_session):
    """
    Test that we can correctly sync Azure Resource Group data and relationships.
    """
    # Arrange
    mock_get.return_value = MOCK_RESOURCE_GROUPS

    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        """
        MERGE (s:AzureSubscription{id: $sub_id})
        SET s.lastupdated = $update_tag
        """,
        sub_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    resource_groups.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes
    expected_nodes = {
        ("/subscriptions/00-00-00-00/resourceGroups/TestRG1", "TestRG1"),
        ("/subscriptions/00-00-00-00/resourceGroups/TestRG2", "TestRG2"),
    }
    actual_nodes = check_nodes(neo4j_session, "AzureResourceGroup", ["id", "name"])
    assert actual_nodes == expected_nodes

    # Assert Relationships
    expected_rels = {
        (TEST_SUBSCRIPTION_ID, "/subscriptions/00-00-00-00/resourceGroups/TestRG1"),
        (TEST_SUBSCRIPTION_ID, "/subscriptions/00-00-00-00/resourceGroups/TestRG2"),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureResourceGroup",
        "id",
        "RESOURCE",
    )
    assert actual_rels == expected_rels


def test_load_resource_group_tags(neo4j_session):
    """
    Test that tags are correctly loaded for Resource Groups.
    """
    # 1. Arrange
    neo4j_session.run(
        """
        MERGE (s:AzureSubscription{id: $sub_id})
        SET s.lastupdated = $update_tag
        """,
        sub_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    transformed_groups = resource_groups.transform_resource_groups(MOCK_RESOURCE_GROUPS)

    resource_groups.load_resource_groups(
        neo4j_session, transformed_groups, TEST_SUBSCRIPTION_ID, TEST_UPDATE_TAG
    )

    # 2. Act
    resource_groups.load_resource_group_tags(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        transformed_groups,
        TEST_UPDATE_TAG,
    )

    # 3. Assert
    expected_tags = {
        f"{TEST_SUBSCRIPTION_ID}|env:prod",
        f"{TEST_SUBSCRIPTION_ID}|service:resource-group",
    }
    tag_nodes = neo4j_session.run("MATCH (t:AzureTag) RETURN t.id")
    actual_tags = {n["t.id"] for n in tag_nodes}
    assert actual_tags == expected_tags

    # 4. Check Relationship
    expected_rels = {
        # Relationships for TestRG1
        (MOCK_RESOURCE_GROUPS[0]["id"], f"{TEST_SUBSCRIPTION_ID}|env:prod"),
        (
            MOCK_RESOURCE_GROUPS[0]["id"],
            f"{TEST_SUBSCRIPTION_ID}|service:resource-group",
        ),
        # Relationships for TestRG2
        (MOCK_RESOURCE_GROUPS[1]["id"], f"{TEST_SUBSCRIPTION_ID}|env:prod"),
        (
            MOCK_RESOURCE_GROUPS[1]["id"],
            f"{TEST_SUBSCRIPTION_ID}|service:resource-group",
        ),
    }

    actual_rels = check_rels(
        neo4j_session,
        "AzureResourceGroup",
        "id",
        "AzureTag",
        "id",
        "TAGGED",
    )
    assert actual_rels == expected_rels
