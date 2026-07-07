DATABRICKS_ACCOUNT_FEDERATION_POLICIES = [
    {
        "name": "github-actions",
        "uid": "uid-account-1",
        "description": "Federate GitHub Actions OIDC into the account.",
        "oidc_policy": {
            "issuer": "https://token.actions.githubusercontent.com",
            "subject_claim": "sub",
            "audiences": ["https://accounts.cloud.databricks.com"],
        },
    },
]

# Keyed by service principal SCIM id, mirroring the per-SP federation policy API.
DATABRICKS_SP_FEDERATION_POLICIES = {
    "510001": {
        "policies": [
            {
                "name": "etl-oidc",
                "uid": "uid-sp-1",
                "description": "Federate CI into the etl-runner service principal.",
                "oidc_policy": {
                    "issuer": "https://token.actions.githubusercontent.com",
                    "subject_claim": "sub",
                    "audiences": ["api://etl"],
                },
            },
        ],
    },
}
