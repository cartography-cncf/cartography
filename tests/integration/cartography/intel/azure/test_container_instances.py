from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.container_instances as container_instances
from tests.data.azure.container_instances import MOCK_CONTAINER_GROUP_WITH_CONTAINERS
from tests.data.azure.container_instances import TEST_CONTAINER_GROUP_ID
from tests.data.azure.container_instances import TEST_GROUP_CONTAINER_DIGEST
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789
TEST_CONTAINER_ID = f"{TEST_CONTAINER_GROUP_ID}/my-container"


@patch("cartography.intel.azure.container_instances.get_container_instances")
def test_has_image_rel(mock_get, neo4j_session):
    mock_get.return_value = MOCK_CONTAINER_GROUP_WITH_CONTAINERS

    neo4j_session.run(
        "MERGE (s:AzureSubscription {id: $id}) SET s.lastupdated = $tag",
        id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (g:AzureGroupContainer {id: $id}) SET g.lastupdated = $tag",
        id=TEST_CONTAINER_GROUP_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (img:ECRImage {id: $digest, digest: $digest}) SET img.lastupdated = $tag",
        digest=TEST_GROUP_CONTAINER_DIGEST,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (img:GCPArtifactRegistryContainerImage {id: $digest, digest: $digest}) SET img.lastupdated = $tag",
        digest=TEST_GROUP_CONTAINER_DIGEST,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (img:GCPArtifactRegistryPlatformImage {id: $digest, digest: $digest}) SET img.lastupdated = $tag",
        digest=TEST_GROUP_CONTAINER_DIGEST,
        tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    container_instances.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_rels(
        neo4j_session,
        "AzureContainerInstance",
        "id",
        "ECRImage",
        "digest",
        "HAS_IMAGE",
    ) == {(TEST_CONTAINER_ID, TEST_GROUP_CONTAINER_DIGEST)}

    assert check_rels(
        neo4j_session,
        "AzureContainerInstance",
        "id",
        "GCPArtifactRegistryContainerImage",
        "digest",
        "HAS_IMAGE",
    ) == {(TEST_CONTAINER_ID, TEST_GROUP_CONTAINER_DIGEST)}

    assert check_rels(
        neo4j_session,
        "AzureContainerInstance",
        "id",
        "GCPArtifactRegistryPlatformImage",
        "digest",
        "HAS_IMAGE",
    ) == {(TEST_CONTAINER_ID, TEST_GROUP_CONTAINER_DIGEST)}


@patch("cartography.intel.azure.container_instances.get_container_instances")
def test_container_ontology_mapping(mock_get, neo4j_session):
    mock_get.return_value = MOCK_CONTAINER_GROUP_WITH_CONTAINERS

    neo4j_session.run(
        "MERGE (s:AzureSubscription {id: $id}) SET s.lastupdated = $tag",
        id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    container_instances.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(neo4j_session, "Container", ["id"]) == {(TEST_CONTAINER_ID,)}

    result = neo4j_session.run(
        """
        MATCH (c:AzureContainerInstance {id: $id})
        RETURN c._ont_name AS name,
               c._ont_image AS image,
               c._ont_image_digest AS image_digest,
               c._ont_state AS state,
               c._ont_source AS source
        """,
        id=TEST_CONTAINER_ID,
    )
    ont_data = [dict(r) for r in result][0]
    assert ont_data == {
        "name": "my-container",
        "image": f"myregistry.azurecr.io/myimage@{TEST_GROUP_CONTAINER_DIGEST}",
        "image_digest": TEST_GROUP_CONTAINER_DIGEST,
        "state": "Running",
        "source": "azure",
    }
