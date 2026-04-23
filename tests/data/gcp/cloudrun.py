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
            "template": {
                "serviceAccount": "test-sa@test-project.iam.gserviceaccount.com",
                "containers": [
                    {
                        "image": "us-central1-docker.pkg.dev/test-project/runtime-repo/test-image:latest",
                    },
                ],
            },
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
                    "image": "us-central1-docker.pkg.dev/test-project/runtime-repo/test-image:latest",
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
                            "image": "us-west1-docker.pkg.dev/test-project/runtime-repo/batch-processor:v1",
                        },
                    ],
                    "serviceAccount": "batch-sa@test-project.iam.gserviceaccount.com",
                },
            },
        },
    ],
}

TEST_REVISION_PRIMARY_DIGEST = (
    "sha256:1111111111111111111111111111111111111111111111111111111111111111"
)
TEST_REVISION_SIDECAR_DIGEST = (
    "sha256:2222222222222222222222222222222222222222222222222222222222222222"
)
TEST_JOB_PRIMARY_DIGEST = (
    "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
)
TEST_JOB_SIDECAR_DIGEST = (
    "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
)

MOCK_REVISION_WITH_DIGEST = [
    {
        "name": "projects/test-project/locations/us-central1/services/test-service/revisions/test-service-00001-abc",
        "service": "test-service",
        "containers": [
            {
                "image": "us-central1-docker.pkg.dev/test-project/runtime-repo/test-image"
                f"@{TEST_REVISION_PRIMARY_DIGEST}",
            },
            {
                "image": "us-central1-docker.pkg.dev/test-project/runtime-repo/log-sidecar"
                f"@{TEST_REVISION_SIDECAR_DIGEST}",
            },
        ],
        "serviceAccount": "test-sa@test-project.iam.gserviceaccount.com",
        "logUri": "https://console.cloud.google.com/logs/viewer?project=test-project",
    },
]

# Service mock whose template mirrors MOCK_REVISION_WITH_DIGEST (the latestReadyRevision spec
# is exposed inline as service.template in the v2 API).
MOCK_SERVICE_WITH_DIGEST = [
    {
        "name": "projects/test-project/locations/us-central1/services/test-service",
        "labels": {},
        "description": "Test Cloud Run service",
        "uri": "https://test-service-abc123-uc.a.run.app",
        "ingress": "INGRESS_TRAFFIC_ALL",
        "latestReadyRevision": "projects/test-project/locations/us-central1/services/test-service/revisions/test-service-00001-abc",
        "template": {
            "serviceAccount": "test-sa@test-project.iam.gserviceaccount.com",
            "containers": [
                {
                    "image": "us-central1-docker.pkg.dev/test-project/runtime-repo/test-image"
                    f"@{TEST_REVISION_PRIMARY_DIGEST}",
                },
                {
                    "image": "us-central1-docker.pkg.dev/test-project/runtime-repo/log-sidecar"
                    f"@{TEST_REVISION_SIDECAR_DIGEST}",
                },
            ],
        },
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
                        "image": "us-west1-docker.pkg.dev/test-project/runtime-repo/batch-processor"
                        f"@{TEST_JOB_PRIMARY_DIGEST}",
                    },
                    {
                        "image": "us-west1-docker.pkg.dev/test-project/runtime-repo/otel-sidecar"
                        f"@{TEST_JOB_SIDECAR_DIGEST}",
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
