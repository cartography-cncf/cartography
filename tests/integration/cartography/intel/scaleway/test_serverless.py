from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.serverless.containers
import cartography.intel.scaleway.serverless.functions
import cartography.intel.scaleway.serverless.jobs
from cartography.client.core.tx import load
from cartography.models.scaleway.container_registry.image import (
    ScalewayContainerRegistryImageSchema,
)
from tests.data.scaleway.serverless import SCALEWAY_CONTAINER_NAMESPACES
from tests.data.scaleway.serverless import SCALEWAY_CONTAINERS
from tests.data.scaleway.serverless import SCALEWAY_FUNCTION_NAMESPACES
from tests.data.scaleway.serverless import SCALEWAY_FUNCTIONS
from tests.data.scaleway.serverless import SCALEWAY_JOB_DEFINITIONS
from tests.data.scaleway.serverless import TEST_CONTAINER_ID
from tests.data.scaleway.serverless import TEST_CONTAINER_NAMESPACE_ID
from tests.data.scaleway.serverless import TEST_FUNCTION_ID
from tests.data.scaleway.serverless import TEST_FUNCTION_NAMESPACE_ID
from tests.data.scaleway.serverless import TEST_JOB_DEFINITION_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
# Matches SCALEWAY_CONTAINERS[0].registry_image.
TEST_CONTAINER_IMAGE_URI = "rg.fr-par.scw.cloud/contscwdemo/demo:latest"
TEST_CONTAINER_IMAGE_DIGEST = (
    "sha256:2222222222222222222222222222222222222222222222222222222222222222"
)


@patch.object(
    cartography.intel.scaleway.serverless.functions,
    "get",
    return_value=(SCALEWAY_FUNCTION_NAMESPACES, SCALEWAY_FUNCTIONS),
)
@patch.object(
    cartography.intel.scaleway.serverless.containers,
    "get",
    return_value=(SCALEWAY_CONTAINER_NAMESPACES, SCALEWAY_CONTAINERS),
)
@patch.object(
    cartography.intel.scaleway.serverless.jobs,
    "get",
    return_value=SCALEWAY_JOB_DEFINITIONS,
)
def test_load_scaleway_serverless(
    _mock_jobs_get, _mock_containers_get, _mock_functions_get, neo4j_session
):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    # A registry image (digest node) the container's registry_image resolves to.
    load(
        neo4j_session,
        ScalewayContainerRegistryImageSchema(),
        [{"digest": TEST_CONTAINER_IMAGE_DIGEST}],
        lastupdated=TEST_UPDATE_TAG,
        PROJECT_ID=TEST_PROJECT_ID,
    )

    # Act
    for module in (
        cartography.intel.scaleway.serverless.functions,
        cartography.intel.scaleway.serverless.jobs,
    ):
        module.sync(
            neo4j_session,
            client,
            common_job_parameters,
            org_id=TEST_ORG_ID,
            projects_id=[TEST_PROJECT_ID],
            update_tag=TEST_UPDATE_TAG,
        )
    cartography.intel.scaleway.serverless.containers.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
        registry_image_digests={TEST_CONTAINER_IMAGE_URI: TEST_CONTAINER_IMAGE_DIGEST},
    )

    # Assert nodes
    assert check_nodes(
        neo4j_session, "ScalewayServerlessFunctionNamespace", ["id", "name"]
    ) == {(TEST_FUNCTION_NAMESPACE_ID, "demo-fn-namespace")}
    assert check_nodes(
        neo4j_session, "ScalewayServerlessFunction", ["id", "name", "privacy"]
    ) == {(TEST_FUNCTION_ID, "demo-function", "public")}
    assert check_nodes(
        neo4j_session, "ScalewayServerlessContainerNamespace", ["id", "name"]
    ) == {(TEST_CONTAINER_NAMESPACE_ID, "demo-container-namespace")}
    assert check_nodes(
        neo4j_session, "ScalewayServerlessContainer", ["id", "name", "privacy"]
    ) == {(TEST_CONTAINER_ID, "demo-container", "public")}
    assert check_nodes(
        neo4j_session,
        "ScalewayServerlessJobDefinition",
        ["id", "name", "cron_schedule"],
    ) == {(TEST_JOB_DEFINITION_ID, "demo-job", "0 0 * * *")}

    # Project ownership.
    for label in (
        "ScalewayServerlessFunctionNamespace",
        "ScalewayServerlessFunction",
        "ScalewayServerlessContainerNamespace",
        "ScalewayServerlessContainer",
        "ScalewayServerlessJobDefinition",
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

    # Namespace -> Function
    assert check_rels(
        neo4j_session,
        "ScalewayServerlessFunctionNamespace",
        "id",
        "ScalewayServerlessFunction",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_FUNCTION_NAMESPACE_ID, TEST_FUNCTION_ID)}

    # Namespace -> Container
    assert check_rels(
        neo4j_session,
        "ScalewayServerlessContainerNamespace",
        "id",
        "ScalewayServerlessContainer",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_CONTAINER_NAMESPACE_ID, TEST_CONTAINER_ID)}

    # Container -[:HAS_IMAGE]-> registry Image (digest resolved from registry_image)
    assert check_rels(
        neo4j_session,
        "ScalewayServerlessContainer",
        "id",
        "ScalewayContainerRegistryImage",
        "id",
        "HAS_IMAGE",
        rel_direction_right=True,
    ) == {(TEST_CONTAINER_ID, TEST_CONTAINER_IMAGE_DIGEST)}
