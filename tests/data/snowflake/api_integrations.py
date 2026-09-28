"""Raw Snowflake API integration payloads, as `GET /api/v2/api-integrations` returns them."""

from typing import Any

SNOWFLAKE_API_INTEGRATION_ROLE_ARN = (
    "arn:aws:iam::000000000000:role/SnowflakeExternalFunctionRole"
)

SNOWFLAKE_API_INTEGRATIONS: list[dict[str, Any]] = [
    {
        "name": "PLANT_GATEWAY_INTEGRATION",
        "enabled": True,
        "api_allowed_prefixes": [
            "https://abc123.execute-api.us-east-2.amazonaws.com/prod/reactor/",
        ],
        "api_blocked_prefixes": [],
        "created_on": "2026-08-03T17:10:00.000+00:00",
        "comment": "Calls the reactor scram API",
        "api_hook": {
            "type": "AWS",
            "api_provider": "aws_api_gateway",
            "api_aws_role_arn": SNOWFLAKE_API_INTEGRATION_ROLE_ARN,
            "api_aws_iam_user_arn": "arn:aws:iam::999999999999:user/snowflake-extfn",
            "api_aws_external_id": "SPRINGFIELD_NUCLEAR_SFCRole=3_ghijkl==",
        },
    },
    # A Git repository integration, which authenticates with a secret rather than by
    # assuming a cloud role.
    {
        "name": "SPRINGFIELD_GIT_INTEGRATION",
        "enabled": True,
        "api_allowed_prefixes": ["https://github.com/springfield/"],
        "api_blocked_prefixes": [],
        "created_on": "2026-08-03T17:12:00.000+00:00",
        "comment": None,
        "api_hook": {
            "type": "GIT",
            "api_provider": "git_https_api",
            "allowed_authentication_secrets": [
                "SPRINGFIELD.NUCLEAR_PLANT.MOE_TAB_LOGIN",
            ],
            "allowed_api_authentication_integrations": [],
        },
    },
]
