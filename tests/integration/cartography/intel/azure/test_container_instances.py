from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.container_instances as container_instances
from tests.data.azure.container_instances import MOCK_CONTAINER_GROUPS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.container_instances.get_container_instances")
def test_sync_container_instances(mock_get, neo4j_session):
    """
    Test that we can correctly sync Azure Container Instance data and relationships.
    """
    # Arrange
    mock_get.return_value = MOCK_CONTAINER_GROUPS

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
    container_instances.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes
    expected_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerInstance/containerGroups/my-test-aci",
            "my-test-aci",
            "unknown",
            "unknown",
            None,
        ),
    }
    actual_nodes = check_nodes(
        neo4j_session,
        "AzureContainerInstance",
        [
            "id",
            "name",
            "architecture",
            "architecture_normalized",
            "architecture_source",
        ],
    )
    assert actual_nodes == expected_nodes

    # Assert Relationships
    expected_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerInstance/containerGroups/my-test-aci",
        ),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureContainerInstance",
        "id",
        "RESOURCE",
    )
    assert actual_rels == expected_rels

    record = neo4j_session.run(
        """
        MATCH (c:AzureContainerInstance {name: 'my-test-aci'})
        RETURN c.image_refs AS image_refs, c.image_digests AS image_digests
        """
    ).single()
    assert record["image_refs"] == [
        "mcr.microsoft.com/oss/nginx/nginx:1.25.3-amd64",
        "myregistry.azurecr.io/team/worker@sha256:abc123",
    ]
    assert record["image_digests"] == ["sha256:abc123"]


def test_load_container_instance_tags(neo4j_session):
    """
    Test that we can correctly sync Azure Container Instance tags.
    """
    # 1. Arrange: Create the prerequisite AzureSubscription node
    neo4j_session.run(
        """
        MERGE (s:AzureSubscription{id: $sub_id})
        SET s.lastupdated = $update_tag
        """,
        sub_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    transformed_data = container_instances.transform_container_instances(
        MOCK_CONTAINER_GROUPS
    )

    container_instances.load_container_instances(
        neo4j_session, transformed_data, TEST_SUBSCRIPTION_ID, TEST_UPDATE_TAG
    )

    # 2. Act: Load the tags
    container_instances.load_container_instance_tags(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        transformed_data,
        TEST_UPDATE_TAG,
    )

    # 3. Assert: Check for the 2 unique tags
    expected_tags = {
        f"{TEST_SUBSCRIPTION_ID}|env:prod",
        f"{TEST_SUBSCRIPTION_ID}|service:container-instance",
    }
    tag_nodes = neo4j_session.run("MATCH (t:AzureTag) RETURN t.id")
    actual_tags = {n["t.id"] for n in tag_nodes}
    assert actual_tags == expected_tags

    # 4. Assert: Check the relationship
    expected_rels = {
        (MOCK_CONTAINER_GROUPS[0]["id"], f"{TEST_SUBSCRIPTION_ID}|env:prod"),
        (
            MOCK_CONTAINER_GROUPS[0]["id"],
            f"{TEST_SUBSCRIPTION_ID}|service:container-instance",
        ),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureContainerInstance",
        "id",
        "AzureTag",
        "id",
        "TAGGED",
    )
    assert actual_rels == expected_rels


def test_transform_container_instances_accepts_camel_case_properties():
    data = [
        {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerInstance/containerGroups/camel",
            "name": "camel",
            "location": "eastus",
            "type": "Microsoft.ContainerInstance/containerGroups",
            "properties": {
                "provisioningState": "Succeeded",
                "ipAddress": {"ip": "20.1.1.1"},
                "osType": "Linux",
                "containers": [
                    {
                        "name": "app",
                        "image": "myregistry.azurecr.io/team/app@sha256:def456",
                    }
                ],
            },
            "tags": {},
        }
    ]

    transformed = container_instances.transform_container_instances(data)
    assert transformed == [
        {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerInstance/containerGroups/camel",
            "name": "camel",
            "location": "eastus",
            "type": "Microsoft.ContainerInstance/containerGroups",
            "provisioning_state": "Succeeded",
            "ip_address": "20.1.1.1",
            "os_type": "Linux",
            "architecture": "unknown",
            "architecture_normalized": "unknown",
            "architecture_raw": None,
            "architecture_source": None,
            "image_refs": ["myregistry.azurecr.io/team/app@sha256:def456"],
            "image_digests": ["sha256:def456"],
            "tags": {},
        }
    ]
