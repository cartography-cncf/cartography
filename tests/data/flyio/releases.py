RELEASES_RESPONSE = {
    "app": {
        "releases": {
            "nodes": [
                {
                    "id": "YgoYklRLL8Xo3fBPg6AoX28AG",
                    "version": 35,
                    "stable": True,
                    "inProgress": False,
                    "reason": "deploy",
                    "description": "Deploy image",
                    "status": "succeeded",
                    "deploymentStrategy": "rolling",
                    "evaluationId": "eval_01KJQC1W6NXAK34WQ739F0ERSP",
                    "createdAt": "2026-07-31T06:40:00Z",
                    "imageRef": (
                        "registry.fly.io/nhmhvxo3b9:"
                        "deployment-01JMWNHS84ZCCV89XYH9SQ48FX"
                    ),
                    "user": {
                        "id": "user_123",
                        "name": "Jonathan Femi",
                        "email": "jonathanfemi@example.com",
                    },
                },
                {
                    "id": "release_previous",
                    "version": 34,
                    "stable": False,
                    "inProgress": False,
                    "reason": "secrets",
                    "description": "Update secrets",
                    "status": "failed",
                    "deploymentStrategy": "immediate",
                    "evaluationId": None,
                    "createdAt": "2026-07-30T06:40:00Z",
                    "imageRef": None,
                    "user": None,
                },
            ],
        },
    },
}
