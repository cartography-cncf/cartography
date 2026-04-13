from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.group_containers as group_containers
from tests.data.azure.container_instances import MOCK_CONTAINER_GROUP_WITH_CONTAINERS
from tests.data.azure.container_instances import TEST_CONTAINER_GROUP_ID
from tests.data.azure.container_instances import TEST_GROUP_CONTAINER_DIGEST
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789
TEST_CONTAINER_ID = f"{TEST_CONTAINER_GROUP_ID}/my-container"


@patch("cartography.intel.azure.group_containers.get_container_groups")
def test_has_image_rel(mock_get, neo4j_session):
    mock_get.return_value = MOCK_CONTAINER_GROUP_WITH_CONTAINERS

    neo4j_session.run(
        "MERGE (s:AzureSubscription {id: $id}) SET s.lastupdated = $tag",
        id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (g:AzureContainerInstance {id: $id}) SET g.lastupdated = $tag",
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

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    group_containers.sync_group_containers(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_rels(
        neo4j_session,
        "AzureGroupContainer",
        "id",
        "ECRImage",
        "digest",
        "HAS_IMAGE",
    ) == {(TEST_CONTAINER_ID, TEST_GROUP_CONTAINER_DIGEST)}

    assert check_rels(
        neo4j_session,
        "AzureGroupContainer",
        "id",
        "GCPArtifactRegistryContainerImage",
        "digest",
        "HAS_IMAGE",
    ) == {(TEST_CONTAINER_ID, TEST_GROUP_CONTAINER_DIGEST)}
