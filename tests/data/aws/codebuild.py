GET_PROJECTS = [
    {
        "name": "frontend-build",
        "arn": "arn:aws:codebuild:eu-west-1:123456789012:project/frontend-build",
        "description": "Builds front-end assets",
        "source": {
            "type": "GITHUB",
            "location": "https://github.com/example/frontend",
            "gitCloneDepth": 1,
            "reportBuildStatus": True,
        },
        "environment": {
            "type": "LINUX_CONTAINER",
            "image": "aws/codebuild/nodejs:14",
            "computeType": "BUILD_GENERAL1_SMALL",
            "environmentVariables": [
                {
                    "name": "NODE_ENV",
                    "value": "production",
                    "type": "PLAINTEXT",
                }
            ],
        },
        "serviceRole": "arn:aws:iam::123456789012:role/CodeBuildServiceRole",
        "created": "2023-06-01T12:34:56Z",
        "lastModified": "2023-06-02T11:22:33Z",
        "logsConfig": {
            "cloudWatchLogs": {
                "status": "ENABLED",
                "groupName": "/aws/codebuild/frontend-build",
            },
            "s3Logs": {"status": "DISABLED"},
        },
    },
    {
        "name": "backend-deploy",
        "arn": "arn:aws:codebuild:eu-west-1:123456789012:project/backend-deploy",
        "description": "Deploys backend services",
        "source": {
            "type": "CODECOMMIT",
            "location": "https://git-codecommit.us-east-1.amazonaws.com/v1/repos/backend",
            "reportBuildStatus": False,
        },
        "environment": {
            "type": "LINUX_CONTAINER",
            "image": "aws/codebuild/python:3.8",
            "computeType": "BUILD_GENERAL1_MEDIUM",
            "environmentVariables": [
                {
                    "name": "DEPLOY_ENV",
                    "value": "staging",
                    "type": "PLAINTEXT",
                },
                {
                    "name": "AWS_SECRET_ACCESS_KEY",
                    "value": "wJalrXUtnFEMI/K7MDENGEXAMPLEKEY",
                    "type": "PLAINTEXT",
                },
            ],
        },
        "serviceRole": "arn:aws:iam::123456789012:role/CodeBuildDeployRole",
        "created": "2023-05-15T08:00:00Z",
        "lastModified": "2023-05-20T09:15:00Z",
        "logsConfig": {
            "s3Logs": {
                "status": "ENABLED",
                "location": "my-s3-logs-bucket/backend-deploy",
            },
        },
    },
]

FRONTEND_BUILD_UUID = "3f1c2b7e-8d4a-4c1e-9b2a-6e5f7d8c9a01"
FRONTEND_PREVIOUS_BUILD_UUID = "a7d9e0f1-2b3c-4d5e-8f90-1a2b3c4d5e6f"
FRONTEND_REVISION = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
FRONTEND_PREVIOUS_REVISION = "9c1185a5c5e9fc54612808977ee8f548b2258d31"

GET_BUILDS = [
    {
        "id": f"frontend-build:{FRONTEND_BUILD_UUID}",
        "arn": f"arn:aws:codebuild:eu-west-1:123456789012:build/frontend-build:{FRONTEND_BUILD_UUID}",
        "buildNumber": 42,
        "buildStatus": "SUCCEEDED",
        "projectName": "frontend-build",
        "sourceVersion": "main",
        "resolvedSourceVersion": FRONTEND_REVISION,
        "source": {
            "type": "GITHUB",
            "location": "https://github.com/example/frontend.git",
        },
    },
    {
        "id": f"frontend-build:{FRONTEND_PREVIOUS_BUILD_UUID}",
        "arn": f"arn:aws:codebuild:eu-west-1:123456789012:build/frontend-build:{FRONTEND_PREVIOUS_BUILD_UUID}",
        "buildNumber": 41,
        "buildStatus": "SUCCEEDED",
        "projectName": "frontend-build",
        "sourceVersion": "main",
        "resolvedSourceVersion": FRONTEND_PREVIOUS_REVISION,
        "source": {
            "type": "GITHUB",
            "location": "https://github.com/example/frontend.git",
        },
    },
]
