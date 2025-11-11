# Mock response for get_cloud_run_locations()
MOCK_LOCATIONS = [
    {
        "locationId": "us-central1",
        "name": "projects/test-project/locations/us-central1",
    },
    {
        "locationId": "europe-west1",
        "name": "projects/test-project/locations/europe-west1",
    },
]

# Mock response for get_cloud_run_services() in us-central1
MOCK_SERVICES_LOC1 = [
    {
        "name": "projects/test-project/locations/us-central1/services/carto-test-service",
        "description": "Test service",
        "uri": "https://carto-test-service-abc.a.run.app",
        "latestReadyRevision": "projects/test-project/locations/us-central1/services/carto-test-service/revisions/carto-test-service-00001-abc",
        "traffic": [
            {
                "revision": "projects/test-project/locations/us-central1/services/carto-test-service/revisions/carto-test-service-00001-abc",
                "percent": 100,
            },
        ],
    },
]

# Mock response for get_cloud_run_revisions()
MOCK_REVISIONS = [
    {
        "name": "projects/test-project/locations/us-central1/services/carto-test-service/revisions/carto-test-service-00001-abc",
        "containers": [{"image": "gcr.io/test-project/hello@sha256:12345"}],
        "serviceAccount": "test-sa@test-project.iam.gserviceaccount.com",
        "logUri": "https://console.cloud.google.com/logs?...",
    },
]

# Mock response for get_cloud_run_jobs() in us-central1
MOCK_JOBS = [
    {
        "name": "projects/test-project/locations/us-central1/jobs/carto-test-job",
        "template": {
            "template": {
                "containers": [{"image": "gcr.io/test-project/hello@sha256:12345"}],
                "serviceAccount": "test-sa@test-project.iam.gserviceaccount.com",
            },
        },
    },
]

# Mock response for get_cloud_run_executions()
MOCK_EXECUTIONS = [
    {
        "name": "projects/test-project/locations/us-central1/jobs/carto-test-job/executions/carto-test-job-xyz",
        "completionTime": "2025-01-01T00:00:00Z",
        "succeededCount": 1,
    },
]

# Mock response for get_cloud_run_domain_mappings() in us-central1
MOCK_DOMAIN_MAPPINGS = [
    {
        "name": "projects/test-project/locations/us-central1/domainmappings/carto.example.com",
        "spec": {"routeName": "carto-test-service"},
    },
]
