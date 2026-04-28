import json
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.vertex.models import get_vertex_ai_locations
from cartography.intel.gcp.vertex.models import sync_vertex_ai_models
from cartography.intel.gcp.vertex.models import transform_vertex_ai_models


def test_transform_vertex_ai_models_serializes_labels_and_map_training_pipeline():
    models = [
        {
            "name": "projects/test/locations/us-central1/models/123",
            "labels": {"team": "ml", "env": "prod"},
            "trainingPipeline": {
                "model_type": "binary_classifier",
                "timestamp": "20250710084340",
            },
            "artifactUri": "gs://test-bucket/path",
        }
    ]

    transformed = transform_vertex_ai_models(models)

    assert len(transformed) == 1
    item = transformed[0]
    assert item["labels"] == json.dumps({"team": "ml", "env": "prod"})
    assert item["training_pipeline"] == json.dumps(
        {"model_type": "binary_classifier", "timestamp": "20250710084340"}
    )
    assert item["gcs_bucket_id"] == "test-bucket"


def test_transform_vertex_ai_models_keeps_string_training_pipeline():
    models = [
        {
            "name": "projects/test/locations/us-central1/models/456",
            "trainingPipeline": "projects/test/locations/us-central1/trainingPipelines/tp-1",
            "artifactUri": "gs://bucket-2/path",
        }
    ]

    transformed = transform_vertex_ai_models(models)
    assert transformed[0]["training_pipeline"] == (
        "projects/test/locations/us-central1/trainingPipelines/tp-1"
    )


def test_get_vertex_ai_locations_uses_service_reported_locations():
    aiplatform = MagicMock()
    aiplatform.projects.return_value.locations.return_value.list.return_value.execute.return_value = {
        "locations": [
            {"locationId": "global"},
            {"locationId": "us"},
            {"locationId": "us-central1"},
            {"locationId": "europe-west9"},
            {"locationId": "us-central1"},
            {"locationId": "me-west1"},
            {"locationId": "eu"},
            {},
        ],
    }

    locations = get_vertex_ai_locations(aiplatform, "test-project")

    assert locations == ["europe-west9", "me-west1", "us-central1"]


@patch("cartography.intel.gcp.vertex.models.cleanup_vertex_ai_models")
@patch("cartography.intel.gcp.vertex.models.load_vertex_ai_models")
@patch(
    "cartography.intel.gcp.vertex.models.fetch_vertex_ai_resources_for_locations",
    return_value=[],
)
@patch("cartography.intel.gcp.vertex.models.get_vertex_ai_locations")
def test_sync_vertex_ai_models_uses_cached_locations_when_provided(
    mock_get_locations,
    mock_fetch,
    mock_load,
    mock_cleanup,
):
    neo4j_session = MagicMock()
    aiplatform = MagicMock()
    common_job_parameters = {"PROJECT_ID": "test-project", "UPDATE_TAG": 123}

    sync_vertex_ai_models(
        neo4j_session=neo4j_session,
        aiplatform=aiplatform,
        project_id="test-project",
        gcp_update_tag=123,
        common_job_parameters=common_job_parameters,
        locations=["us-central1"],
    )

    mock_get_locations.assert_not_called()
    mock_fetch.assert_called_once()
    mock_load.assert_called_once_with(neo4j_session, [], "test-project", 123)
    mock_cleanup.assert_called_once_with(neo4j_session, common_job_parameters)


@patch("cartography.intel.gcp.vertex.models.cleanup_vertex_ai_models")
@patch("cartography.intel.gcp.vertex.models.load_vertex_ai_models")
@patch("cartography.intel.gcp.vertex.models.fetch_vertex_ai_resources_for_locations")
@patch("cartography.intel.gcp.vertex.models.get_vertex_ai_locations", return_value=None)
def test_sync_vertex_ai_models_skips_on_location_discovery_failure(
    mock_get_locations,
    mock_fetch,
    mock_load,
    mock_cleanup,
):
    neo4j_session = MagicMock()
    aiplatform = MagicMock()
    common_job_parameters = {"PROJECT_ID": "test-project", "UPDATE_TAG": 123}

    sync_vertex_ai_models(
        neo4j_session=neo4j_session,
        aiplatform=aiplatform,
        project_id="test-project",
        gcp_update_tag=123,
        common_job_parameters=common_job_parameters,
    )

    mock_get_locations.assert_called_once_with(aiplatform, "test-project")
    mock_fetch.assert_not_called()
    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()
