# Raw items of GET /context/{id}/environment-variable, keyed by context id.
# The API never returns secret values, only the variable name + metadata.
CIRCLECI_CONTEXT_ENV_VARS = {
    "ctx-1": [
        {
            "variable": "AWS_ACCESS_KEY_ID",
            "context_id": "ctx-1",
            "created_at": "2021-09-01T12:05:00Z",
            "updated_at": "2021-09-01T12:05:00Z",
        },
        {
            "variable": "AWS_SECRET_ACCESS_KEY",
            "context_id": "ctx-1",
            "created_at": "2021-09-01T12:06:00Z",
            "updated_at": "2021-09-01T12:06:00Z",
        },
    ],
    "ctx-2": [
        {
            "variable": "DEPLOY_TOKEN",
            "context_id": "ctx-2",
            "created_at": "2021-09-02T12:05:00Z",
            "updated_at": "2021-09-02T12:05:00Z",
        },
    ],
}
