"""Test data for GitLab CI/CD variables module."""

TEST_GITLAB_URL = "https://gitlab.example.com"
TEST_GROUP_ID = 42
TEST_PROJECT_ID = 123

# Raw responses from /api/v4/groups/:id/variables. The `value` field is
# returned by the API but should not be ingested.
GET_GROUP_VARIABLES_RESPONSE = [
    {
        "key": "DEPLOY_TOKEN",
        "value": "should-not-be-stored",
        "variable_type": "env_var",
        "protected": True,
        "masked": True,
        "masked_and_hidden": False,
        "raw": False,
        "environment_scope": "*",
        "description": "Token for deploy automation",
    },
    {
        "key": "GROUP_OPEN_VAR",
        "value": "ok-to-leak",
        "variable_type": "env_var",
        "protected": False,
        "masked": False,
        "masked_and_hidden": False,
        "raw": False,
        "environment_scope": "*",
        "description": None,
    },
]

# Raw responses from /api/v4/projects/:id/variables. Includes a variable
# scoped to a specific environment AND another with the wildcard "*", so
# the wildcard match logic in step 3 can be tested.
GET_PROJECT_VARIABLES_RESPONSE = [
    {
        "key": "DATABASE_URL",
        "value": "should-not-be-stored",
        "variable_type": "env_var",
        "protected": True,
        "masked": True,
        "masked_and_hidden": True,
        "raw": False,
        "environment_scope": "production",
        "description": "Production database",
    },
    {
        "key": "DATABASE_URL",
        "value": "should-not-be-stored",
        "variable_type": "env_var",
        "protected": False,
        "masked": True,
        "masked_and_hidden": False,
        "raw": False,
        "environment_scope": "staging",
        "description": "Staging database",
    },
    {
        "key": "FEATURE_FLAG",
        "value": "true",
        "variable_type": "env_var",
        "protected": False,
        "masked": False,
        "masked_and_hidden": False,
        "raw": True,
        "environment_scope": "*",
        "description": None,
    },
    # File-type variable with no environment_scope returned (treated as "*")
    {
        "key": "CONFIG_FILE",
        "value": "yaml-content",
        "variable_type": "file",
        "protected": False,
        "masked": False,
        "masked_and_hidden": False,
        "raw": False,
        "description": None,
    },
]
