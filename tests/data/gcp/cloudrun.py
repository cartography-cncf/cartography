MOCK_SERVICES = {
    "services": [
        {
            "name": "projects/test-project/locations/us-central1/services/test-service",
            "template": {
                "containers": [
                    {
                        "image": "gcr.io/test-project/test-image:latest",
                    },
                ],
                "serviceAccount": "test-sa@test-project.iam.gserviceaccount.com",
            },
        },
    ],
}

MOCK_REVISIONS = {
    "revisions": [
        {
            "name": "projects/test-project/locations/us-central1/services/test-service/revisions/test-service-00001-abc",
            "service": "projects/test-project/locations/us-central1/services/test-service",
            "template": {
                "containers": [
                    {
                        "image": "gcr.io/test-project/test-image:latest",
                    },
                ],
                "serviceAccount": "test-sa@test-project.iam.gserviceaccount.com",
            },
            "logUri": "https://console.cloud.google.com/logs/viewer?project=test-project",
        },
    ],
}

MOCK_JOBS = {
    "jobs": [
        {
            "name": "projects/test-project/locations/us-west1/jobs/test-job",
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

MOCK_EXECUTIONS = {
    "executions": [
        {
            "name": "projects/test-project/locations/us-west1/jobs/test-job/executions/test-job-exec-001",
            "completionStatus": "SUCCEEDED",
            "cancelledCount": 0,
            "failedCount": 0,
            "succeededCount": 5,
        },
        {
            "name": "projects/test-project/locations/us-west1/jobs/test-job/executions/test-job-exec-002",
            "completionStatus": "FAILED",
            "cancelledCount": 1,
            "failedCount": 3,
            "succeededCount": 2,
        },
    ],
}
