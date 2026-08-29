GCF_RESPONSE = {
    "functions": [
        {
            "name": "projects/test-project/locations/us-central1/functions/function-1",
            "description": "Test function one",
            "status": "ACTIVE",
            "runtime": "python310",
            "entryPoint": "hello_world_http",
            "httpsTrigger": {
                "url": "https://us-central1-test-project.cloudfunctions.net/function-1",
            },
            "updateTime": "2023-01-01T10:00:00Z",
            "serviceAccountEmail": "service-1@test-project.iam.gserviceaccount.com",
            "availableMemoryMb": 256,
            "timeout": "60s",
            "labels": {"team": "security", "env": "prod"},
        },
        {
            "name": "projects/test-project/locations/us-east1/functions/function-2",
            "description": "Test function two",
            "status": "ACTIVE",
            "runtime": "nodejs16",
            "entryPoint": "handler_event",
            "eventTrigger": {
                "eventType": "google.cloud.pubsub.topic.v1.messagePublished",
                "resource": "projects/test-project/topics/my-topic",
            },
            "updateTime": "2023-02-01T11:00:00Z",
            "serviceAccountEmail": "service-2@test-project.iam.gserviceaccount.com",
            "availableMemoryMb": 512,
            "timeout": "120s",
        },
        {
            # Fractional-second Duration (legal in the protobuf Duration format
            # used by the REST API). Exercises the float path of timeout parsing.
            "name": "projects/test-project/locations/us-west1/functions/function-3",
            "description": "Test function three (fractional timeout)",
            "status": "ACTIVE",
            "runtime": "go121",
            "entryPoint": "Handler",
            "httpsTrigger": {
                "url": "https://us-west1-test-project.cloudfunctions.net/function-3",
            },
            "updateTime": "2023-03-01T12:00:00Z",
            "serviceAccountEmail": "service-3@test-project.iam.gserviceaccount.com",
            "availableMemoryMb": 128,
            "timeout": "3.5s",
        },
    ],
}
