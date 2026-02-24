BACKEND_SERVICE_RESPONSE = {
    "id": "projects/test-cloud-run-483700/global/backendServices",
    "items": [
        {
            "name": "test-backend-service",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/test-cloud-run-483700/global/backendServices/test-backend-service",
            "loadBalancingScheme": "EXTERNAL",
            "protocol": "TCP",
            "securityPolicy": "https://www.googleapis.com/compute/v1/projects/test-cloud-run-483700/global/securityPolicies/test-armor-policy",
            "backends": [
                {
                    "group": "https://www.googleapis.com/compute/v1/projects/test-cloud-run-483700/zones/us-central1-a/instanceGroups/test-instance-group",
                },
            ],
        },
    ],
}

INSTANCE_GROUP_RESPONSES = [
    {
        "id": "projects/test-cloud-run-483700/zones/us-central1-a/instanceGroups",
        "items": [
            {
                "name": "test-instance-group",
                "selfLink": "https://www.googleapis.com/compute/v1/projects/test-cloud-run-483700/zones/us-central1-a/instanceGroups/test-instance-group",
                "zone": "https://www.googleapis.com/compute/v1/projects/test-cloud-run-483700/zones/us-central1-a",
                "network": "https://www.googleapis.com/compute/v1/projects/test-cloud-run-483700/global/networks/default",
                "subnetwork": "https://www.googleapis.com/compute/v1/projects/test-cloud-run-483700/regions/us-central1/subnetworks/default",
                "_members": [
                    {
                        "instance": "https://www.googleapis.com/compute/v1/projects/test-cloud-run-483700/zones/us-central1-a/instances/vm-private-1",
                    },
                    {
                        "instance": "https://www.googleapis.com/compute/v1/projects/test-cloud-run-483700/zones/us-central1-a/instances/vm-private-2",
                    },
                ],
            },
        ],
    },
]

CLOUD_ARMOR_RESPONSE = {
    "id": "projects/test-cloud-run-483700/global/securityPolicies",
    "items": [
        {
            "name": "test-armor-policy",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/test-cloud-run-483700/global/securityPolicies/test-armor-policy",
            "type": "CLOUD_ARMOR",
        },
    ],
}
