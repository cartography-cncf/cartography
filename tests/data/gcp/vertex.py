# flake8: noqa
# Mock data for Vertex AI resources

# Mock response from get_vertex_ai_locations()
VERTEX_LOCATIONS_RESPONSE = ["us-central1", "us-east1"]

# Mock response from get_vertex_ai_models_for_location()
VERTEX_MODELS_RESPONSE = [
    {
        "name": "projects/test-project/locations/us-central1/models/1234567890",
        "displayName": "test-model",
        "description": "Test model for integration testing",
        "createTime": "2024-01-01T00:00:00Z",
        "updateTime": "2024-01-02T00:00:00Z",
        "etag": "test-etag-123",
        "artifactUri": "gs://test-bucket/model-artifacts/",
        "deployedModels": [
            {
                "endpoint": "projects/test-project/locations/us-central1/endpoints/9876543210",
                "deployedModelId": "deployed-1",
            },
        ],
        "supportedExportFormats": [
            {"id": "tf-saved-model"},
        ],
        "containerSpec": {
            "imageUri": "gcr.io/test-project/prediction-image:latest",
        },
    },
]

# Mock response from get_vertex_ai_endpoints_for_location()
VERTEX_ENDPOINTS_RESPONSE = [
    {
        "name": "projects/test-project/locations/us-central1/endpoints/9876543210",
        "displayName": "test-endpoint",
        "description": "Test endpoint for integration testing",
        "createTime": "2024-01-01T00:00:00Z",
        "updateTime": "2024-01-02T00:00:00Z",
        "etag": "test-etag-456",
        "network": "projects/test-project/global/networks/default",
        "deployedModels": [
            {
                "id": "deployed-1",
                "model": "projects/test-project/locations/us-central1/models/1234567890",
                "displayName": "deployed-test-model",
                "createTime": "2024-01-01T00:00:00Z",
                "dedicatedResources": {
                    "machineSpec": {
                        "machineType": "n1-standard-2",
                    },
                    "minReplicaCount": 1,
                    "maxReplicaCount": 1,
                },
                "enableAccessLogging": False,
            },
        ],
    },
]

# Mock response from get_workbench_instances_for_location() - v2 API format
VERTEX_WORKBENCH_INSTANCES_RESPONSE = [
    {
        "name": "projects/test-project/locations/us-central1/instances/test-instance-123",
        "creator": "test-service-account@test-project.iam.gserviceaccount.com",
        "createTime": "2024-01-01T00:00:00Z",
        "updateTime": "2024-01-02T00:00:00Z",
        "state": "ACTIVE",
        "healthState": "HEALTHY",
        "gceSetup": {
            "serviceAccounts": [
                {"email": "test-service-account@test-project.iam.gserviceaccount.com"},
            ],
        },
    },
]

# Mock response from get_vertex_ai_training_pipelines_for_location()
VERTEX_TRAINING_PIPELINES_RESPONSE = [
    {
        "name": "projects/test-project/locations/us-central1/trainingPipelines/training-123",
        "displayName": "test-training-pipeline",
        "createTime": "2024-01-01T00:00:00Z",
        "updateTime": "2024-01-02T00:00:00Z",
        "startTime": "2024-01-01T00:00:00Z",
        "endTime": "2024-01-01T02:00:00Z",
        "state": "PIPELINE_STATE_SUCCEEDED",
        "inputDataConfig": {
            "datasetId": "dataset-456",
        },
        "modelId": "1234567890",
        "modelToUpload": {
            "displayName": "test-model",
        },
        "trainingTaskDefinition": "gs://google-cloud-aiplatform/schema/trainingjob/definition/automl_tabular_1.0.0.yaml",
    },
]

# Mock response from get_feature_groups_for_location()
VERTEX_FEATURE_GROUPS_RESPONSE = [
    {
        "name": "projects/test-project/locations/us-central1/featureGroups/test-feature-group",
        "createTime": "2024-01-01T00:00:00Z",
        "updateTime": "2024-01-02T00:00:00Z",
        "etag": "test-etag-789",
        "bigQuery": {
            "bigQuerySource": {
                "inputUri": "bq://test-project.test_dataset.test_table",
            },
            "entityIdColumns": ["entity_id"],
            "timeSeries": {
                "timestampColumn": "feature_timestamp",
            },
        },
    },
]

# Mock response from get_vertex_ai_datasets_for_location()
VERTEX_DATASETS_RESPONSE = [
    {
        "name": "projects/test-project/locations/us-central1/datasets/dataset-456",
        "displayName": "test-dataset",
        "createTime": "2024-01-01T00:00:00Z",
        "updateTime": "2024-01-02T00:00:00Z",
        "etag": "test-etag-dataset",
        "dataItemCount": "1000",
        "metadataSchemaUri": "gs://google-cloud-aiplatform/schema/dataset/metadata/tabular_1.0.0.yaml",
        "metadata": {
            "inputConfig": {
                "gcsSource": {
                    "uri": ["gs://test-bucket/dataset/data.csv"],
                },
            },
        },
        "encryptionSpec": {
            "kmsKeyName": "projects/test-project/locations/us-central1/keyRings/test-ring/cryptoKeys/test-key",
        },
    },
]
