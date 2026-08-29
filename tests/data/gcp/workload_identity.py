TEST_PROJECT_NUMBER = "123456789012"

LIST_WORKLOAD_IDENTITY_POOLS_RESPONSE = {
    "workloadIdentityPools": [
        {
            "name": f"projects/{TEST_PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool",
            "displayName": "GitHub Actions",
            "description": "Pool for GitHub Actions OIDC federation",
            "state": "ACTIVE",
            "disabled": False,
            "sessionDuration": "3600s",
        },
        {
            "name": f"projects/{TEST_PROJECT_NUMBER}/locations/global/workloadIdentityPools/aws-pool",
            "displayName": "AWS Federation",
            "description": "Pool for AWS workload federation",
            "state": "ACTIVE",
            "disabled": False,
            "sessionDuration": "3600s",
        },
    ],
}

LIST_WORKLOAD_IDENTITY_PROVIDERS_RESPONSE = {
    f"projects/{TEST_PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool": {
        "workloadIdentityPoolProviders": [
            {
                "name": (
                    f"projects/{TEST_PROJECT_NUMBER}/locations/global/"
                    "workloadIdentityPools/github-pool/providers/github-oidc"
                ),
                "displayName": "GitHub OIDC",
                "description": "OIDC provider for github.com",
                "state": "ACTIVE",
                "disabled": False,
                "attributeCondition": "assertion.repository_owner == 'subimagesec'",
                "oidc": {
                    "issuerUri": "https://token.actions.githubusercontent.com",
                    "allowedAudiences": [
                        "https://iam.googleapis.com/projects/example/locations/global/workloadIdentityPools/github-pool/providers/github-oidc",
                    ],
                },
            },
        ],
    },
    f"projects/{TEST_PROJECT_NUMBER}/locations/global/workloadIdentityPools/aws-pool": {
        "workloadIdentityPoolProviders": [
            {
                "name": (
                    f"projects/{TEST_PROJECT_NUMBER}/locations/global/"
                    "workloadIdentityPools/aws-pool/providers/aws-prod"
                ),
                "displayName": "AWS Prod",
                "description": "AWS provider for prod account",
                "state": "ACTIVE",
                "disabled": False,
                "aws": {"accountId": "111122223333"},
            },
        ],
    },
}


def fake_get_providers(_iam_client, pool_name):
    """Test helper used as side_effect for the get_workload_identity_providers mock."""
    return LIST_WORKLOAD_IDENTITY_PROVIDERS_RESPONSE.get(pool_name, {}).get(
        "workloadIdentityPoolProviders", []
    )


# Policy binding members that reference the github pool: both a per-subject
# principal and a principalSet covering all identities in the pool.
WIF_BINDING_MEMBERS = [
    (
        "principal://iam.googleapis.com/projects/"
        f"{TEST_PROJECT_NUMBER}/locations/global/workloadIdentityPools/"
        "github-pool/subject/repo:subimagesec/cartography:ref:refs/heads/main"
    ),
    (
        "principalSet://iam.googleapis.com/projects/"
        f"{TEST_PROJECT_NUMBER}/locations/global/workloadIdentityPools/"
        "github-pool/attribute.repository_owner/subimagesec"
    ),
]

WIF_GITHUB_POOL_ID = (
    f"projects/{TEST_PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool"
)
