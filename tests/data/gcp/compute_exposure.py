BACKEND_SERVICE_RESPONSE = {
    "id": "projects/sample-project-123456/global/backendServices",
    "items": [
        {
            "name": "test-backend-service",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/global/backendServices/test-backend-service",
            "loadBalancingScheme": "EXTERNAL",
            "protocol": "TCP",
            "securityPolicy": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/global/securityPolicies/test-armor-policy",
            "backends": [
                {
                    "group": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/zones/us-central1-a/instanceGroups/test-instance-group",
                },
            ],
        },
    ],
}

INSTANCE_RESPONSES = [
    {
        "id": "projects/sample-project-123456/zones/us-central1-a/instances",
        "items": [
            {
                "name": "vm-private-1",
                "selfLink": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/zones/us-central1-a/instances/vm-private-1",
                "networkInterfaces": [],
            },
            {
                "name": "vm-private-2",
                "selfLink": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/zones/us-central1-a/instances/vm-private-2",
                "networkInterfaces": [],
            },
        ],
    },
]

INSTANCE_GROUP_RESPONSES = [
    {
        "id": "projects/sample-project-123456/zones/us-central1-a/instanceGroups",
        "items": [
            {
                "name": "test-instance-group",
                "selfLink": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/zones/us-central1-a/instanceGroups/test-instance-group",
                "zone": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/zones/us-central1-a",
                "network": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/global/networks/default",
                "subnetwork": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/regions/us-central1/subnetworks/default",
                "_members": [
                    {
                        "instance": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/zones/us-central1-a/instances/vm-private-1",
                    },
                    {
                        "instance": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/zones/us-central1-a/instances/vm-private-2",
                    },
                ],
            },
        ],
    },
]

CLOUD_ARMOR_RESPONSE = {
    "id": "projects/sample-project-123456/global/securityPolicies",
    "items": [
        {
            "name": "test-armor-policy",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/global/securityPolicies/test-armor-policy",
            "type": "CLOUD_ARMOR",
        },
    ],
}

GLOBAL_FORWARDING_RULES_RESPONSE = {
    "id": "projects/sample-project-123456/global/forwardingRules",
    "items": [
        {
            "name": "ext-fr",
            "IPAddress": "35.1.2.3",
            "IPProtocol": "TCP",
            "loadBalancingScheme": "EXTERNAL",
            "network": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/global/networks/default",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/global/forwardingRules/ext-fr",
        },
    ],
}

REGIONAL_FORWARDING_RULES_RESPONSE = {
    "id": "projects/sample-project-123456/regions/us-central1/forwardingRules",
    "items": [
        {
            "name": "int-fr",
            "region": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/regions/us-central1",
            "IPAddress": "10.0.0.10",
            "IPProtocol": "TCP",
            "loadBalancingScheme": "INTERNAL",
            "network": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/global/networks/default",
            "subnetwork": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/regions/us-central1/subnetworks/default",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/sample-project-123456/regions/us-central1/forwardingRules/int-fr",
        },
    ],
}
