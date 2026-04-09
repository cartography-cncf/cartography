MOCK_SERVICES = {
    "services": [
        {
            "name": "projects/test-project/locations/us-central1/services/test-service",
            "labels": {
                "env": "prod",
                "team": "api",
            },
            "description": "Test Cloud Run service",
            "uri": "https://test-service-abc123-uc.a.run.app",
            "ingress": "INGRESS_TRAFFIC_ALL",
            "latestReadyRevision": "projects/test-project/locations/us-central1/services/test-service/revisions/test-service-00001-abc",
        },
    ],
}

MOCK_REVISIONS = {
    "revisions": [
        {
            "name": "projects/test-project/locations/us-central1/services/test-service/revisions/test-service-00001-abc",
            "service": "test-service",
            "containers": [
                {
                    "image": "gcr.io/test-project/test-image:latest",
                },
            ],
            "serviceAccount": "test-sa@test-project.iam.gserviceaccount.com",
            "logUri": "https://console.cloud.google.com/logs/viewer?project=test-project",
        },
    ],
}

MOCK_JOBS = {
    "jobs": [
        {
            "name": "projects/test-project/locations/us-west1/jobs/test-job",
            "labels": {
                "env": "staging",
                "team": "batch",
            },
            "template": {
                "template": {
                    "containers": [
                        {
                            "image": "gcr.io/test-project/batch-processor:v1",
                        },
                    ],
                    "serviceAccount": "batch-sa@test-project.iam.gserviceaccount.com",
                },
            },
        },
    ],
}

TEST_REVISION_DIGEST = (
    "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
)
TEST_JOB_DIGEST = (
    "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
)

MOCK_REVISION_WITH_DIGEST = [
    {
        "name": "projects/test-project/locations/us-central1/services/test-service/revisions/test-service-00001-abc",
        "service": "test-service",
        "containers": [
            {
                "image": f"gcr.io/test-project/test-image@{TEST_REVISION_DIGEST}",
            },
        ],
        "serviceAccount": "test-sa@test-project.iam.gserviceaccount.com",
        "logUri": "https://console.cloud.google.com/logs/viewer?project=test-project",
    },
]

MOCK_JOB_WITH_DIGEST = [
    {
        "name": "projects/test-project/locations/us-west1/jobs/test-job",
        "labels": {},
        "template": {
            "template": {
                "containers": [
                    {
                        "image": f"gcr.io/test-project/batch-processor@{TEST_JOB_DIGEST}",
                    },
                ],
                "serviceAccount": "batch-sa@test-project.iam.gserviceaccount.com",
            },
        },
    },
]

MOCK_EXECUTIONS = {
    "executions": [
        {
            "name": "projects/test-project/locations/us-west1/jobs/test-job/executions/test-job-exec-001",
            "cancelledCount": 0,
            "failedCount": 0,
            "succeededCount": 5,
        },
        {
            "name": "projects/test-project/locations/us-west1/jobs/test-job/executions/test-job-exec-002",
            "cancelledCount": 1,
            "failedCount": 3,
            "succeededCount": 2,
        },
    ],
}
