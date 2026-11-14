from datetime import datetime
from datetime import timedelta
from datetime import timezone
from unittest.mock import patch

import pytest

import cartography.intel.langsmith
from cartography.config import Config
from cartography.rules.data.rules import langsmith_security
from cartography.rules.spec.model import Rule
from tests.data.langsmith.deployments import SUPPORT_DEPLOYMENT_ID
from tests.data.langsmith.deployments import TRIAGE_DEPLOYMENT_ID
from tests.data.langsmith.fake_client import FakeLangSmithClient
from tests.data.langsmith.fake_client import SIMPSON_CORP_ROUTES
from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.organizations import LANGSMITH_ORG_INFO
from tests.data.langsmith.roles import CUSTOM_ROLE_ID
from tests.data.langsmith.workspace_resources import PUBLIC_REPO_ID
from tests.data.langsmith.workspace_resources import PUBLIC_RUN_ID
from tests.data.langsmith.workspaces import WORKSPACE_DEV_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID

FACTS = {
    fact.id: fact
    for rule in vars(langsmith_security).values()
    if isinstance(rule, Rule)
    for fact in rule.facts
}

SSO_PROVIDER_ID = "9a9a9a9a-0001-4001-8001-9a9a9a9a9a9a"
PAT_ID = "7a7a7a7a-0001-4001-8001-7a7a7a7a7a7a"
TRACING_KEY_ID = "8b8b8b8b-0001-4001-8001-8b8b8b8b8b8b"
WORKSPACE_KEY_ID = "9b9b9b9b-0001-4001-8001-9b9b9b9b9b9b"
TRIAGE_CREDENTIAL_ID = "cc11cc11-0003-4003-8003-cc11cc11cc11"
PLAINTEXT_PROMPT_WEBHOOK_ID = "ae11ae11-0002-4002-8002-ae11ae11ae11"
TRACE_EXPORT_ID = "af11af11-0001-4001-8001-af11af11af11"

NOW = datetime.now(timezone.utc)


def _days_ago(days: int) -> str:
    return (NOW - timedelta(days=days)).isoformat()


def _key(key_id: str, *, created: int, used: int | None, expires: int | None = None):
    return {
        "id": key_id,
        "short_key": f"lsv2_sk_{key_id[:4]}",
        "created_at": _days_ago(created),
        "last_used_at": _days_ago(used) if used is not None else None,
        "expires_at": _days_ago(expires) if expires is not None else None,
        "revoked_at": None,
        "access_scope": "organization",
    }


def _org_info(**settings):
    return {("/api/v1/orgs/current/info", None): {**LANGSMITH_ORG_INFO, **settings}}


ONLY_THESE_SERVICE_KEYS = {
    ("/api/v1/orgs/current/members/personal-access-tokens", None): [],
    ("/api/v1/platform/orgs/current/scim/tokens", None): [],
    ("/api/v1/orgs/current/tracing-keys", None): [],
    ("/api/v1/api-key", WORKSPACE_PROD_ID): [],
    ("/api/v1/api-key", WORKSPACE_DEV_ID): [],
    ("/api/v1/orgs/current/service-keys", None): [
        _key("aaaa0001-0000-4000-8000-000000000000", created=400, used=1),
        _key("aaaa0002-0000-4000-8000-000000000000", created=400, used=200),
        _key("aaaa0003-0000-4000-8000-000000000000", created=60, used=None),
        _key("aaaa0004-0000-4000-8000-000000000000", created=1, used=None),
        # Expired: no longer usable, so no longer worth flagging as unused.
        _key("aaaa0005-0000-4000-8000-000000000000", created=400, used=200, expires=1),
    ],
}

DEPLOY_CAPABLE_DEFAULT_ROLE = {
    ("/api/v1/orgs/current/roles", None): [
        (
            {**role, "permissions": [*role["permissions"], "deployments:create"]}
            if role["id"] == CUSTOM_ROLE_ID
            else role
        )
        for role in SIMPSON_CORP_ROUTES[("/api/v1/orgs/current/roles", None)]
    ],
}

TRIAGE_WITH_AWS_KEYS = {
    ("/v2/deployments", WORKSPACE_DEV_ID): [
        {
            **SIMPSON_CORP_ROUTES[("/v2/deployments", WORKSPACE_DEV_ID)][0],
            "secrets": [
                {"name": "AWS_ACCESS_KEY_ID", "value": "unused"},
                {"name": "OPENAI_API_KEY", "value": "unused"},
            ],
        },
    ],
}

EXPORT_WITH_ACCESS_KEYS = {
    ("/api/v1/bulk-exports/destinations", WORKSPACE_PROD_ID): [
        {
            **destination,
            "config": {**destination["config"], "aws_role_arn": None},
            "credentials_keys": ["access_key_id", "secret_access_key"],
        }
        for destination in SIMPSON_CORP_ROUTES[
            ("/api/v1/bulk-exports/destinations", WORKSPACE_PROD_ID)
        ]
    ],
}

CONFIDENTIAL_CLIENT_WITH_LOOPBACK_REDIRECT = {
    ("/api/v1/platform/oauth/clients", WORKSPACE_PROD_ID): {
        "clients": [
            {
                **client,
                "redirect_uris": [
                    "https://tools.simpson.corp/callback",
                    "http://localhost:2024/callback",
                ],
            }
            for client in SIMPSON_CORP_ROUTES[
                ("/api/v1/platform/oauth/clients", WORKSPACE_PROD_ID)
            ]["clients"]
        ],
    },
}


def _sync(neo4j_session, client: FakeLangSmithClient) -> None:
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=123456789,
        langsmith_pat="lsv2_pt_fake",
    )
    with patch.object(
        cartography.intel.langsmith, "LangSmithClient", return_value=client
    ):
        cartography.intel.langsmith.start_langsmith_ingestion(neo4j_session, config)


@pytest.fixture(autouse=True)
def _empty_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")


@pytest.mark.parametrize(
    "fact_id, overrides, expected",
    [
        pytest.param(
            "langsmith_api_key_never_expires",
            {},
            {PAT_ID, TRACING_KEY_ID, WORKSPACE_KEY_ID},
            id="never-expires",
        ),
        pytest.param(
            "langsmith_api_key_unused",
            ONLY_THESE_SERVICE_KEYS,
            {
                "aaaa0002-0000-4000-8000-000000000000",
                "aaaa0003-0000-4000-8000-000000000000",
            },
            id="unused",
        ),
        pytest.param(
            "langsmith_key_lifetime_uncapped", {}, set(), id="lifetime-capped"
        ),
        pytest.param(
            "langsmith_key_lifetime_uncapped",
            _org_info(max_service_key_expiry_days=None),
            {LANGSMITH_ORG_ID},
            id="lifetime-uncapped",
        ),
        pytest.param("langsmith_sso_not_enforced", {}, set(), id="sso-enforced"),
        pytest.param(
            "langsmith_sso_not_enforced",
            _org_info(sso_only=False),
            {LANGSMITH_ORG_ID},
            id="sso-optional",
        ),
        pytest.param(
            "langsmith_sso_default_role_can_deploy",
            {},
            set(),
            id="default-role-read-only",
        ),
        pytest.param(
            "langsmith_sso_default_role_can_deploy",
            DEPLOY_CAPABLE_DEFAULT_ROLE,
            {SSO_PROVIDER_ID},
            id="default-role-can-deploy",
        ),
        pytest.param(
            "langsmith_public_share",
            _org_info(public_sharing_disabled=True),
            set(),
            id="sharing-disabled",
        ),
        pytest.param(
            "langsmith_public_share",
            {},
            {f"run|{PUBLIC_RUN_ID}", f"repo|{PUBLIC_REPO_ID}"},
            id="sharing-allowed",
        ),
        pytest.param(
            "langsmith_shareable_deployment",
            {},
            {SUPPORT_DEPLOYMENT_ID},
            id="shareable-deployment",
        ),
        pytest.param(
            "langsmith_deployment_static_cloud_credentials",
            {},
            set(),
            id="llm-keys-only",
        ),
        pytest.param(
            "langsmith_deployment_static_cloud_credentials",
            TRIAGE_WITH_AWS_KEYS,
            {TRIAGE_DEPLOYMENT_ID},
            id="aws-access-key",
        ),
        pytest.param(
            "langsmith_webhook_plaintext",
            {},
            {PLAINTEXT_PROMPT_WEBHOOK_ID},
            id="plaintext-webhook",
        ),
        pytest.param(
            "langsmith_oauth_client_insecure_redirect",
            {},
            set(),
            id="https-redirects",
        ),
        pytest.param(
            "langsmith_oauth_client_insecure_redirect",
            CONFIDENTIAL_CLIENT_WITH_LOOPBACK_REDIRECT,
            {"langsmith-mcp-client"},
            id="confidential-loopback-redirect",
        ),
        pytest.param(
            "langsmith_bulk_export_static_credentials",
            {},
            set(),
            id="export-assumes-role",
        ),
        pytest.param(
            "langsmith_bulk_export_static_credentials",
            EXPORT_WITH_ACCESS_KEYS,
            {TRACE_EXPORT_ID},
            id="export-access-keys",
        ),
        pytest.param(
            "langsmith_agent_credential_for_disabled_member",
            {},
            {TRIAGE_CREDENTIAL_ID},
            id="agent-credential",
        ),
        pytest.param(
            "langsmith_tracing_key_of_disabled_member",
            {},
            {TRACING_KEY_ID},
            id="tracing-key",
        ),
    ],
)
def test_fact_flags_exactly_the_risky_assets(
    neo4j_session, fact_id, overrides, expected
):
    # Arrange
    _sync(
        neo4j_session, FakeLangSmithClient(routes={**SIMPSON_CORP_ROUTES, **overrides})
    )
    fact = FACTS[fact_id]

    # Act
    rows = neo4j_session.run(fact.cypher_query).data()
    visual = neo4j_session.run(fact.cypher_visual_query).data()
    count = neo4j_session.run(fact.cypher_count_query).single()["count"]

    # Assert
    assert {row[fact.asset_id_field] for row in rows} == expected
    assert bool(visual) == bool(expected)
    assert count >= len(expected)
