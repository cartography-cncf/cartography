import json

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
