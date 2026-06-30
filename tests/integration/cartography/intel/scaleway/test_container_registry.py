from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.container_registry.namespaces
from tests.data.scaleway.container_registry import SCALEWAY_REGISTRY_IMAGES
from tests.data.scaleway.container_registry import SCALEWAY_REGISTRY_NAMESPACES
from tests.data.scaleway.container_registry import TEST_IMAGE_ID
from tests.data.scaleway.container_registry import TEST_NAMESPACE_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@patch.object(
    cartography.intel.scaleway.container_registry.namespaces,
    "get",
    return_value=(SCALEWAY_REGISTRY_NAMESPACES, SCALEWAY_REGISTRY_IMAGES),
)
def test_load_scaleway_container_registry(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.container_registry.namespaces.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert nodes
    assert check_nodes(
        neo4j_session,
        "ScalewayContainerRegistryNamespace",
        ["id", "name", "is_public"],
    ) == {(TEST_NAMESPACE_ID, "demo-namespace", True)}
    assert check_nodes(
        neo4j_session, "ScalewayContainerRegistryImage", ["id", "name"]
    ) == {(TEST_IMAGE_ID, "demo-image")}

    # Cross-cloud ontology label.
    assert check_nodes(neo4j_session, "ContainerRegistry", ["id"]) == {
        (TEST_NAMESPACE_ID,)
    }

    # Normalized _ont_* fields populated from the ContainerRegistry mapping.
    assert check_nodes(
        neo4j_session,
        "ContainerRegistry",
        ["_ont_name", "_ont_uri", "_ont_location", "_ont_size_bytes", "_ont_source"],
    ) == {
        (
            "demo-namespace",
            "rg.fr-par.scw.cloud/demo-namespace",
            "fr-par",
            1024,
            "scaleway",
        )
    }

    # Project ownership.
    for label in (
        "ScalewayContainerRegistryNamespace",
        "ScalewayContainerRegistryImage",
    ):
        assert check_rels(
            neo4j_session,
            label,
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        ), f"{label} not linked to project"

    # Namespace -> Image
    assert check_rels(
        neo4j_session,
        "ScalewayContainerRegistryNamespace",
        "id",
        "ScalewayContainerRegistryImage",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_NAMESPACE_ID, TEST_IMAGE_ID)}
