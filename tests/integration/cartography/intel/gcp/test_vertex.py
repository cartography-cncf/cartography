from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.vertex.datasets
import cartography.intel.gcp.vertex.deployed_models
import cartography.intel.gcp.vertex.endpoints
import cartography.intel.gcp.vertex.feature_groups
import cartography.intel.gcp.vertex.instances
import cartography.intel.gcp.vertex.models
import cartography.intel.gcp.vertex.training_pipelines
import tests.data.gcp.vertex
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "test-project"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "PROJECT_ID": TEST_PROJECT_ID,
}


@patch.object(
    cartography.intel.gcp.vertex.models,
    "get_vertex_ai_locations",
    return_value=tests.data.gcp.vertex.VERTEX_LOCATIONS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.vertex.models,
    "get_vertex_ai_models_for_location",
    return_value=tests.data.gcp.vertex.VERTEX_MODELS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.vertex.endpoints,
    "get_vertex_ai_locations",
    return_value=tests.data.gcp.vertex.VERTEX_LOCATIONS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.vertex.endpoints,
    "get_vertex_ai_endpoints_for_location",
    return_value=tests.data.gcp.vertex.VERTEX_ENDPOINTS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.vertex.instances,
    "get_workbench_api_locations",
    return_value=tests.data.gcp.vertex.VERTEX_LOCATIONS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.vertex.instances,
    "get_workbench_instances_for_location",
    return_value=tests.data.gcp.vertex.VERTEX_WORKBENCH_INSTANCES_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.vertex.training_pipelines,
    "get_vertex_ai_locations",
    return_value=tests.data.gcp.vertex.VERTEX_LOCATIONS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.vertex.training_pipelines,
    "get_vertex_ai_training_pipelines_for_location",
    return_value=tests.data.gcp.vertex.VERTEX_TRAINING_PIPELINES_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.vertex.feature_groups,
    "get_vertex_ai_locations",
    return_value=tests.data.gcp.vertex.VERTEX_LOCATIONS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.vertex.feature_groups,
    "get_feature_groups_for_location",
    return_value=tests.data.gcp.vertex.VERTEX_FEATURE_GROUPS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.vertex.datasets,
    "get_vertex_ai_locations",
    return_value=tests.data.gcp.vertex.VERTEX_LOCATIONS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.vertex.datasets,
    "get_vertex_ai_datasets_for_location",
    return_value=tests.data.gcp.vertex.VERTEX_DATASETS_RESPONSE,
)
def test_sync_vertex_ai_end_to_end(
    _mock_get_datasets,
    _mock_get_datasets_locations,
    _mock_get_feature_stores,
    _mock_get_feature_stores_locations,
    _mock_get_training_pipelines,
    _mock_get_training_pipelines_locations,
    _mock_get_notebooks,
    _mock_get_notebooks_locations,
    _mock_get_endpoints,
    _mock_get_endpoints_locations,
    _mock_get_models,
    _mock_get_models_locations,
    neo4j_session,
):
    """
    End-to-end test for Vertex AI sync.
    Tests the full happy path: mocked API responses -> sync -> verify nodes and relationships.
    """
    # Clean up any existing Vertex AI data in the database
    neo4j_session.run(
        """
        MATCH (n) WHERE n:GCPVertexAIModel OR n:GCPVertexAIEndpoint OR n:GCPVertexAIDeployedModel
            OR n:GCPVertexAIWorkbenchInstance OR n:GCPVertexAITrainingPipeline OR n:GCPVertexAIFeatureGroup
            OR n:GCPVertexAIDataset
        DETACH DELETE n
        """
    )

    # Mock the aiplatform client
    mock_aiplatform_client = MagicMock()

    # Create prerequisite nodes inline
    # Create test GCP Project
    neo4j_session.run(
        """
        MERGE (project:GCPProject{id: $project_id})
        ON CREATE SET project.firstseen = timestamp()
        SET project.lastupdated = $update_tag
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create test GCS bucket (for model STORED_IN relationship)
    neo4j_session.run(
        """
        MERGE (bucket:GCPBucket{id: $bucket_id})
        ON CREATE SET bucket.firstseen = timestamp()
        SET bucket.lastupdated = $update_tag,
            bucket.name = $bucket_id
        """,
        bucket_id="test-bucket",
        update_tag=TEST_UPDATE_TAG,
    )

    # Create test service account (for notebook relationship)
    neo4j_session.run(
        """
        MERGE (sa:GCPServiceAccount{email: $email})
        ON CREATE SET sa.firstseen = timestamp()
        SET sa.lastupdated = $update_tag
        """,
        email="test-service-account@test-project.iam.gserviceaccount.com",
        update_tag=TEST_UPDATE_TAG,
    )

    # Run all Vertex AI sync functions
    cartography.intel.gcp.vertex.datasets.sync_vertex_ai_datasets(
        neo4j_session,
        mock_aiplatform_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    cartography.intel.gcp.vertex.models.sync_vertex_ai_models(
        neo4j_session,
        mock_aiplatform_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    endpoints_raw = cartography.intel.gcp.vertex.endpoints.sync_vertex_ai_endpoints(
        neo4j_session,
        mock_aiplatform_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    cartography.intel.gcp.vertex.deployed_models.sync_vertex_ai_deployed_models(
        neo4j_session,
        endpoints_raw,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    cartography.intel.gcp.vertex.instances.sync_workbench_instances(
        neo4j_session,
        mock_aiplatform_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    cartography.intel.gcp.vertex.training_pipelines.sync_training_pipelines(
        neo4j_session,
        mock_aiplatform_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    cartography.intel.gcp.vertex.feature_groups.sync_feature_groups(
        neo4j_session,
        mock_aiplatform_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    # Verify all nodes were created
    assert check_nodes(neo4j_session, "GCPVertexAIModel", ["id"]) == {
        ("projects/test-project/locations/us-central1/models/1234567890",),
    }

    assert check_nodes(neo4j_session, "GCPVertexAIEndpoint", ["id"]) == {
        ("projects/test-project/locations/us-central1/endpoints/9876543210",),
    }

    assert check_nodes(neo4j_session, "GCPVertexAIDeployedModel", ["id"]) == {
        (
            "projects/test-project/locations/us-central1/endpoints/9876543210/deployedModels/deployed-1",
        ),
    }

    assert check_nodes(neo4j_session, "GCPVertexAIWorkbenchInstance", ["id"]) == {
        ("projects/test-project/locations/us-central1/instances/test-instance-123",),
    }

    assert check_nodes(neo4j_session, "GCPVertexAITrainingPipeline", ["id"]) == {
        ("projects/test-project/locations/us-central1/trainingPipelines/training-123",),
    }

    assert check_nodes(neo4j_session, "GCPVertexAIFeatureGroup", ["id"]) == {
        (
            "projects/test-project/locations/us-central1/featureGroups/test-feature-group",
        ),
    }

    assert check_nodes(neo4j_session, "GCPVertexAIDataset", ["id"]) == {
        ("projects/test-project/locations/us-central1/datasets/dataset-456",),
    }

    # Verify Project -> Resource relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPVertexAIModel",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_PROJECT_ID,
            "projects/test-project/locations/us-central1/models/1234567890",
        ),
    }

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPVertexAIEndpoint",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_PROJECT_ID,
            "projects/test-project/locations/us-central1/endpoints/9876543210",
        ),
    }

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPVertexAIDataset",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_PROJECT_ID,
            "projects/test-project/locations/us-central1/datasets/dataset-456",
        ),
    }

    # Verify Model -> GCS Bucket relationship
    assert check_rels(
        neo4j_session,
        "GCPVertexAIModel",
        "id",
        "GCPBucket",
        "id",
        "STORED_IN",
        rel_direction_right=True,
    ) == {
        (
            "projects/test-project/locations/us-central1/models/1234567890",
            "test-bucket",
        ),
    }

    # Verify Endpoint -> DeployedModel relationship
    assert check_rels(
        neo4j_session,
        "GCPVertexAIEndpoint",
        "id",
        "GCPVertexAIDeployedModel",
        "id",
        "SERVES",
        rel_direction_right=True,
    ) == {
        (
            "projects/test-project/locations/us-central1/endpoints/9876543210",
            "projects/test-project/locations/us-central1/endpoints/9876543210/deployedModels/deployed-1",
        ),
    }

    # Verify DeployedModel -> Model relationship
    assert check_rels(
        neo4j_session,
        "GCPVertexAIDeployedModel",
        "id",
        "GCPVertexAIModel",
        "id",
        "INSTANCE_OF",
        rel_direction_right=True,
    ) == {
        (
            "projects/test-project/locations/us-central1/endpoints/9876543210/deployedModels/deployed-1",
            "projects/test-project/locations/us-central1/models/1234567890",
        ),
    }

    # Verify Workbench Instance -> ServiceAccount relationship
    assert check_rels(
        neo4j_session,
        "GCPVertexAIWorkbenchInstance",
        "id",
        "GCPServiceAccount",
        "email",
        "USES_SERVICE_ACCOUNT",
        rel_direction_right=True,
    ) == {
        (
            "projects/test-project/locations/us-central1/instances/test-instance-123",
            "test-service-account@test-project.iam.gserviceaccount.com",
        ),
    }

    # Verify TrainingPipeline -> Dataset relationship
    assert check_rels(
        neo4j_session,
        "GCPVertexAITrainingPipeline",
        "id",
        "GCPVertexAIDataset",
        "id",
        "READS_FROM",
        rel_direction_right=True,
    ) == {
        (
            "projects/test-project/locations/us-central1/trainingPipelines/training-123",
            "projects/test-project/locations/us-central1/datasets/dataset-456",
        ),
    }

    # Verify TrainingPipeline -> Model relationship
    assert check_rels(
        neo4j_session,
        "GCPVertexAITrainingPipeline",
        "id",
        "GCPVertexAIModel",
        "id",
        "PRODUCES",
        rel_direction_right=True,
    ) == {
        (
            "projects/test-project/locations/us-central1/trainingPipelines/training-123",
            "projects/test-project/locations/us-central1/models/1234567890",
        ),
    }
