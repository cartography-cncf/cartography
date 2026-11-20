from unittest.mock import patch

import pytest

import cartography.intel.langsmith
from cartography.config import Config
from tests.data.langsmith.agent_auth import GITHUB_PROVIDER_ID
from tests.data.langsmith.agent_auth import GOOGLE_PROVIDER_ID
from tests.data.langsmith.deployments import SUPPORT_AGENT_ID
from tests.data.langsmith.deployments import SUPPORT_DEPLOYMENT_ID
from tests.data.langsmith.deployments import TRIAGE_AGENT_ID
from tests.data.langsmith.deployments import TRIAGE_DEPLOYMENT_ID
from tests.data.langsmith.fake_client import FakeLangSmithClient
from tests.data.langsmith.fake_client import SIMPSON_CORP_ROUTES
from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.roles import CUSTOM_ROLE_ID
from tests.data.langsmith.roles import ORG_ADMIN_ROLE_ID
from tests.data.langsmith.roles import WORKSPACE_VIEWER_ROLE_ID
from tests.data.langsmith.users import BART_LS_USER_ID
from tests.data.langsmith.users import HOMER_LS_USER_ID
from tests.data.langsmith.users import MARGE_LS_USER_ID
from tests.data.langsmith.workspaces import LANGSMITH_WORKSPACES
from tests.data.langsmith.workspaces import WORKSPACE_DEV_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
NEXT_UPDATE_TAG = TEST_UPDATE_TAG + 1

ORG_ADMIN_ROLE = f"{LANGSMITH_ORG_ID}|{ORG_ADMIN_ROLE_ID}"
WORKSPACE_VIEWER_ROLE = f"{LANGSMITH_ORG_ID}|{WORKSPACE_VIEWER_ROLE_ID}"
CUSTOM_ROLE = f"{LANGSMITH_ORG_ID}|{CUSTOM_ROLE_ID}"

SUPPORT_AGENT = f"{LANGSMITH_ORG_ID}|{SUPPORT_AGENT_ID}"
TRIAGE_AGENT = f"{LANGSMITH_ORG_ID}|{TRIAGE_AGENT_ID}"
TRIAGE_CREDENTIAL_ID = "cc11cc11-0003-4003-8003-cc11cc11cc11"


def _sync(
    neo4j_session,
    client: FakeLangSmithClient,
    update_tag: int = TEST_UPDATE_TAG,
    org_id: str | None = None,
) -> None:
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        langsmith_pat="lsv2_pt_fake",
        langsmith_org_id=org_id,
    )
    with patch.object(
        cartography.intel.langsmith, "LangSmithClient", return_value=client
    ):
        cartography.intel.langsmith.start_langsmith_ingestion(neo4j_session, config)


def _ids(neo4j_session, label: str) -> set[str]:
    return {node_id for (node_id,) in check_nodes(neo4j_session, label, ["id"]) or ()}


@pytest.fixture(autouse=True)
def _empty_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def test_sync_loads_the_organization_its_workspaces_and_roles(neo4j_session):
    # Act
    _sync(neo4j_session, FakeLangSmithClient())

    # Assert
    assert check_nodes(neo4j_session, "LangSmithOrganization", ["id", "name"]) == {
        (LANGSMITH_ORG_ID, "Simpson Corp"),
    }
    assert check_rels(
        neo4j_session,
        "LangSmithOrganization",
        "id",
        "LangSmithWorkspace",
        "name",
        "RESOURCE",
    ) == {
        (LANGSMITH_ORG_ID, "Production"),
        (LANGSMITH_ORG_ID, "Development"),
    }
    assert check_nodes(
        neo4j_session, "LangSmithRole", ["id", "name", "is_custom", "role_type"]
    ) == {
        (ORG_ADMIN_ROLE, "Organization Admin", False, "builtin"),
        (WORKSPACE_VIEWER_ROLE, "Viewer", False, "builtin"),
        (CUSTOM_ROLE, "Deployment Auditor", True, "custom"),
    }
    assert check_rels(
        neo4j_session, "LangSmithRole", "id", "LangSmithPermission", "name", "GRANTS"
    ) == {
        (ORG_ADMIN_ROLE, "organization:manage"),
        (ORG_ADMIN_ROLE, "organization:read"),
        (WORKSPACE_VIEWER_ROLE, "workspaces:read"),
        (CUSTOM_ROLE, "workspaces:read"),
        (CUSTOM_ROLE, "deployments:read"),
    }


def test_sync_loads_members_with_per_workspace_roles(neo4j_session):
    # Act
    _sync(neo4j_session, FakeLangSmithClient())

    # Assert
    # The pending invite has no ls_user_id yet and must not become a user.
    assert check_nodes(neo4j_session, "LangSmithUser", ["id", "email"]) == {
        (MARGE_LS_USER_ID, "mbsimpson@simpson.corp"),
        (HOMER_LS_USER_ID, "hjsimpson@simpson.corp"),
        (BART_LS_USER_ID, "bjsimpson@simpson.corp"),
    }
    assert check_nodes(
        neo4j_session, "LangSmithOrgMembership", ["ls_user_id", "is_disabled"]
    ) == {
        (MARGE_LS_USER_ID, False),
        (HOMER_LS_USER_ID, False),
        (BART_LS_USER_ID, True),
    }
    assert check_rels(
        neo4j_session,
        "LangSmithOrgMembership",
        "ls_user_id",
        "LangSmithRole",
        "id",
        "HAS_ROLE",
    ) == {(MARGE_LS_USER_ID, ORG_ADMIN_ROLE)}
    assert check_rels(
        neo4j_session, "LangSmithUser", "id", "LangSmithWorkspace", "id", "MEMBER_OF"
    ) == {
        (MARGE_LS_USER_ID, WORKSPACE_PROD_ID),
        (MARGE_LS_USER_ID, WORKSPACE_DEV_ID),
        (HOMER_LS_USER_ID, WORKSPACE_PROD_ID),
        (BART_LS_USER_ID, WORKSPACE_DEV_ID),
    }
    # The same custom role is held in two workspaces by two people, which a plain
    # user-to-role edge could not express.
    role_by_membership = neo4j_session.run(
        """
        MATCH (u:LangSmithUser)-[:HAS_MEMBERSHIP]->(m:LangSmithWorkspaceMembership)
              <-[:RESOURCE]-(w:LangSmithWorkspace)
        MATCH (m)-[:HAS_ROLE]->(r:LangSmithRole)
        RETURN u.id AS user, w.id AS workspace, r.id AS role
        """
    ).data()
    assert {(r["user"], r["workspace"], r["role"]) for r in role_by_membership} == {
        (MARGE_LS_USER_ID, WORKSPACE_PROD_ID, CUSTOM_ROLE),
        (HOMER_LS_USER_ID, WORKSPACE_PROD_ID, WORKSPACE_VIEWER_ROLE),
        (BART_LS_USER_ID, WORKSPACE_DEV_ID, CUSTOM_ROLE),
    }


def test_sync_attributes_every_credential_to_its_owner(neo4j_session):
    # Act
    _sync(neo4j_session, FakeLangSmithClient())

    # Assert
    # Only the non-secret short prefix is stored; SCIM tokens report theirs as short_token.
    assert check_nodes(neo4j_session, "LangSmithApiKey", ["short_key", "key_type"]) == {
        ("lsv2_sk_abcd", "service_key"),
        ("lsv2_pt_wxyz", "pat"),
        ("lsv2_sc_1234", "scim_token"),
        ("lsv2_ws_prod", "workspace_key"),
    }
    # created_by holds an identity UUID, an ls_user_id or a bare username depending on
    # the route. All three resolve to the same kind of user node.
    assert check_rels(
        neo4j_session, "LangSmithApiKey", "short_key", "LangSmithUser", "id", "OWNED_BY"
    ) == {
        ("lsv2_sk_abcd", MARGE_LS_USER_ID),
        ("lsv2_sc_1234", MARGE_LS_USER_ID),
        ("lsv2_pt_wxyz", BART_LS_USER_ID),
        ("lsv2_ws_prod", HOMER_LS_USER_ID),
    }
    assert check_rels(
        neo4j_session, "LangSmithApiKey", "short_key", "LangSmithRole", "id", "ASSUMES"
    ) == {
        ("lsv2_sk_abcd", CUSTOM_ROLE),
        ("lsv2_pt_wxyz", ORG_ADMIN_ROLE),
    }
    assert check_rels(
        neo4j_session,
        "LangSmithWorkspace",
        "id",
        "LangSmithApiKey",
        "short_key",
        "CONTAINS",
    ) == {
        (WORKSPACE_PROD_ID, "lsv2_sk_abcd"),
        (WORKSPACE_PROD_ID, "lsv2_ws_prod"),
    }
    assert check_rels(
        neo4j_session,
        "LangSmithServiceAccount",
        "name",
        "LangSmithWorkspace",
        "id",
        "DEFAULT_WORKSPACE",
    ) == {("ci-deployer", WORKSPACE_PROD_ID)}


def test_sync_links_sso_and_access_policies_to_roles(neo4j_session):
    # Act
    _sync(neo4j_session, FakeLangSmithClient())

    # Assert
    assert check_rels(
        neo4j_session,
        "LangSmithSSOProvider",
        "name",
        "LangSmithRole",
        "id",
        "DEFAULT_ROLE",
    ) == {("okta-saml", CUSTOM_ROLE)}
    assert check_rels(
        neo4j_session,
        "LangSmithSSOProvider",
        "name",
        "LangSmithWorkspace",
        "id",
        "PROVISIONS_INTO",
    ) == {
        ("okta-saml", WORKSPACE_PROD_ID),
        ("okta-saml", WORKSPACE_DEV_ID),
    }
    assert check_rels(
        neo4j_session,
        "LangSmithAccessPolicy",
        "name",
        "LangSmithRole",
        "id",
        "ATTACHED_TO",
    ) == {("Production projects only", CUSTOM_ROLE)}


def test_sync_links_deployments_to_the_agents_they_run(neo4j_session):
    # Act
    _sync(neo4j_session, FakeLangSmithClient())

    # Assert
    # The support deployment names its agent in an agent block; the triage deployment
    # has agent: null, the common case, so its agent is found only by listing assistants.
    assert check_nodes(
        neo4j_session, "LangSmithAgent", ["id", "graph_id", "environment"]
    ) == {
        (SUPPORT_AGENT, "support_graph", "production"),
        (TRIAGE_AGENT, "triage_graph", None),
    }
    assert check_rels(
        neo4j_session, "LangSmithDeployment", "id", "LangSmithAgent", "id", "RUNS"
    ) == {
        (SUPPORT_DEPLOYMENT_ID, SUPPORT_AGENT),
        (TRIAGE_DEPLOYMENT_ID, TRIAGE_AGENT),
    }
    assert check_rels(
        neo4j_session,
        "LangSmithWorkspace",
        "id",
        "LangSmithDeployment",
        "id",
        "RESOURCE",
    ) == {
        (WORKSPACE_PROD_ID, SUPPORT_DEPLOYMENT_ID),
        (WORKSPACE_DEV_ID, TRIAGE_DEPLOYMENT_ID),
    }


def test_sync_shows_which_agent_can_act_as_which_human(neo4j_session):
    # Act
    _sync(neo4j_session, FakeLangSmithClient())

    # Assert
    grants = neo4j_session.run(
        """
        MATCH (a:LangSmithAgent)-[:HAS_CREDENTIAL]->(c:LangSmithAgentCredential)
              -[:FOR_PROVIDER]->(p:LangSmithOAuthProvider)
        MATCH (c)-[:ON_BEHALF_OF]->(u:LangSmithUser)
        RETURN a.id AS agent, u.id AS user, p.id AS provider, c.scopes AS scopes
        """
    ).data()
    assert {
        (r["agent"], r["user"], r["provider"], tuple(r["scopes"])) for r in grants
    } == {
        (SUPPORT_AGENT, MARGE_LS_USER_ID, GITHUB_PROVIDER_ID, ("repo", "read:org")),
        (
            SUPPORT_AGENT,
            HOMER_LS_USER_ID,
            GOOGLE_PROVIDER_ID,
            ("https://www.googleapis.com/auth/gmail.readonly",),
        ),
        (TRIAGE_AGENT, BART_LS_USER_ID, GITHUB_PROVIDER_ID, ("repo",)),
    }


def test_deactivating_a_member_does_not_revoke_agent_credentials(neo4j_session):
    # Act
    _sync(neo4j_session, FakeLangSmithClient())

    # Assert
    acting_for_disabled = neo4j_session.run(
        """
        MATCH (m:LangSmithOrgMembership {is_disabled: true})<-[:HAS_MEMBERSHIP]-
              (u:LangSmithUser)<-[:ON_BEHALF_OF]-(:LangSmithAgentCredential)
              <-[:HAS_CREDENTIAL]-(a:LangSmithAgent)
        RETURN u.id AS user, a.id AS agent
        """
    ).data()
    assert [(r["user"], r["agent"]) for r in acting_for_disabled] == [
        (BART_LS_USER_ID, TRIAGE_AGENT),
    ]


def test_deployment_secret_values_never_reach_the_graph(neo4j_session):
    # Act
    _sync(neo4j_session, FakeLangSmithClient())

    # Assert
    secret_names = neo4j_session.run(
        """
        MATCH (n:LangSmithDeployment)
        RETURN n.id AS id, n.secret_names AS secret_names
        """
    ).data()
    assert {r["id"]: r["secret_names"] for r in secret_names} == {
        SUPPORT_DEPLOYMENT_ID: ["OPENAI_API_KEY", "SLACK_BOT_TOKEN"],
        TRIAGE_DEPLOYMENT_ID: [],
    }
    # No property of any node may hold a secret value from the fixture. List properties
    # are flattened so their elements are checked too.
    leaked = neo4j_session.run(
        """
        MATCH (n)
        UNWIND keys(n) AS k
        WITH n, k, n[k] AS v
        WITH n, k, CASE WHEN v IS :: LIST<ANY> THEN v ELSE [v] END AS values
        WHERE any(x IN values WHERE toString(x) CONTAINS 'SENTINEL-MUST-NOT-BE-INGESTED')
        RETURN labels(n) AS labels, k AS property
        """
    ).data()
    assert leaked == []


def test_sync_loads_workspace_resources(neo4j_session):
    # Act
    _sync(neo4j_session, FakeLangSmithClient())

    # Assert
    assert check_rels(
        neo4j_session, "LangSmithWorkspace", "id", "LangSmithSecret", "name", "RESOURCE"
    ) == {
        (WORKSPACE_PROD_ID, "OPENAI_API_KEY"),
        (WORKSPACE_PROD_ID, "SLACK_BOT_TOKEN"),
        (WORKSPACE_DEV_ID, "OPENAI_API_KEY"),
    }
    assert check_rels(
        neo4j_session,
        "LangSmithWorkspace",
        "id",
        "LangSmithResourceTag",
        "value",
        "RESOURCE",
    ) == {(WORKSPACE_PROD_ID, "prod")}
    assert check_nodes(neo4j_session, "LangSmithResourceTag", ["key", "value"]) == {
        ("environment", "prod"),
    }
    # OAuth clients are registered against the organization, not a workspace.
    assert check_rels(
        neo4j_session,
        "LangSmithOrganization",
        "id",
        "LangSmithOAuthClient",
        "id",
        "RESOURCE",
    ) == {(LANGSMITH_ORG_ID, "langsmith-mcp-client")}
    assert check_rels(
        neo4j_session,
        "LangSmithWorkspace",
        "id",
        "LangSmithMcpServer",
        "name",
        "RESOURCE",
    ) == {(WORKSPACE_PROD_ID, "Internal Docs")}
    assert check_nodes(neo4j_session, "LangSmithMcpServer", ["name", "vendor"]) == {
        ("Internal Docs", "arcade"),
    }


# Each case names a route, what it returns once the resource is deleted upstream, and a
# node that route alone feeds.
STALE_CASES = [
    pytest.param(
        ("/api/v1/workspaces/current/secrets", WORKSPACE_PROD_ID),
        [{"key": "OPENAI_API_KEY"}],
        "LangSmithSecret",
        f"{WORKSPACE_PROD_ID}|SLACK_BOT_TOKEN",
        id="workspace-secret",
    ),
    pytest.param(
        ("/api/v1/orgs/current/members/personal-access-tokens", None),
        [],
        "LangSmithApiKey",
        "7a7a7a7a-0001-4001-8001-7a7a7a7a7a7a",
        id="personal-access-token",
    ),
    pytest.param(
        ("/api/v1/service-accounts", None),
        [],
        "LangSmithServiceAccount",
        "5a5a5a5a-0001-4001-8001-5a5a5a5a5a5a",
        id="service-account",
    ),
    pytest.param(
        ("/api/v1/workspaces/current/members", WORKSPACE_DEV_ID),
        {"members": [], "pending": []},
        "LangSmithWorkspaceMembership",
        f"{BART_LS_USER_ID}|{WORKSPACE_DEV_ID}",
        id="workspace-membership",
    ),
    pytest.param(
        ("/api/v1/platform/orgs/current/access-policies", None),
        {"access_policies": []},
        "LangSmithAccessPolicy",
        "ab11ab11-0001-4001-8001-ab11ab11ab11",
        id="access-policy",
    ),
    pytest.param(
        ("/v2/deployments", WORKSPACE_DEV_ID),
        [],
        "LangSmithDeployment",
        TRIAGE_DEPLOYMENT_ID,
        id="deployment",
    ),
    pytest.param(
        (f"/v2/auth/agents/{TRIAGE_AGENT_ID}/connections", WORKSPACE_DEV_ID),
        {"data": []},
        "LangSmithAgentCredential",
        TRIAGE_CREDENTIAL_ID,
        id="agent-credential",
    ),
    pytest.param(
        ("/api/v1/platform/oauth/clients", None),
        {"clients": []},
        "LangSmithOAuthClient",
        "langsmith-mcp-client",
        id="oauth-client",
    ),
]


@pytest.mark.parametrize("route, deleted_payload, label, node_id", STALE_CASES)
@pytest.mark.parametrize(
    "answered_with",
    # An empty listing, or a 404 for a feature the organization no longer has.
    ["empty", "404"],
)
def test_resync_removes_what_was_deleted_upstream(
    neo4j_session, route, deleted_payload, label, node_id, answered_with
):
    # Arrange
    _sync(neo4j_session, FakeLangSmithClient(), TEST_UPDATE_TAG)
    assert node_id in _ids(neo4j_session, label)
    if answered_with == "empty":
        deleted = FakeLangSmithClient(
            routes={**SIMPSON_CORP_ROUTES, route: deleted_payload}
        )
    else:
        deleted = FakeLangSmithClient(failures={route: 404})

    # Act
    _sync(neo4j_session, deleted, NEXT_UPDATE_TAG)

    # Assert
    assert node_id not in _ids(neo4j_session, label)


@pytest.mark.parametrize("route, deleted_payload, label, node_id", STALE_CASES)
@pytest.mark.parametrize("status", [401, 403, None], ids=["401", "403", "timeout"])
def test_resync_preserves_what_could_not_be_read(
    neo4j_session, route, deleted_payload, label, node_id, status
):
    # Arrange
    _sync(neo4j_session, FakeLangSmithClient(), TEST_UPDATE_TAG)
    unreadable = FakeLangSmithClient(failures={route: status})

    # Act
    _sync(neo4j_session, unreadable, NEXT_UPDATE_TAG)

    # Assert
    # The data may still exist, so a failed read must not be treated as a deletion.
    assert node_id in _ids(neo4j_session, label)


def test_resync_keeps_agents_on_a_deployment_that_did_not_answer(neo4j_session):
    # Arrange
    _sync(neo4j_session, FakeLangSmithClient(), TEST_UPDATE_TAG)
    cold = FakeLangSmithClient(
        cold_deployment_urls=frozenset({"https://triage-bot.us.langgraph.app"})
    )

    # Act
    _sync(neo4j_session, cold, NEXT_UPDATE_TAG)

    # Assert
    # A scaled-to-zero deployment timing out is not evidence its agent was deleted.
    assert TRIAGE_AGENT in _ids(neo4j_session, "LangSmithAgent")
    assert TRIAGE_CREDENTIAL_ID in _ids(neo4j_session, "LangSmithAgentCredential")
    assert (TRIAGE_DEPLOYMENT_ID, TRIAGE_AGENT) in check_rels(
        neo4j_session, "LangSmithDeployment", "id", "LangSmithAgent", "id", "RUNS"
    )


def test_resync_keeps_agents_on_a_deployment_that_stopped_serving(neo4j_session):
    # Arrange
    _sync(neo4j_session, FakeLangSmithClient(), TEST_UPDATE_TAG)
    triage = {
        **SIMPSON_CORP_ROUTES[("/v2/deployments", WORKSPACE_DEV_ID)][0],
        "status": "UNUSED",
    }
    stopped = FakeLangSmithClient(
        routes={**SIMPSON_CORP_ROUTES, ("/v2/deployments", WORKSPACE_DEV_ID): [triage]}
    )

    # Act
    _sync(neo4j_session, stopped, NEXT_UPDATE_TAG)

    # Assert
    # The deployment still exists, so its agent and that agent's live credentials do too;
    # they just cannot be listed until it serves again.
    assert TRIAGE_AGENT in _ids(neo4j_session, "LangSmithAgent")
    assert TRIAGE_CREDENTIAL_ID in _ids(neo4j_session, "LangSmithAgentCredential")
    assert (TRIAGE_DEPLOYMENT_ID, TRIAGE_AGENT) in check_rels(
        neo4j_session, "LangSmithDeployment", "id", "LangSmithAgent", "id", "RUNS"
    )


def test_resync_keeps_credential_providers_when_providers_cannot_be_read(
    neo4j_session,
):
    # Arrange
    _sync(neo4j_session, FakeLangSmithClient(), TEST_UPDATE_TAG)
    no_providers = FakeLangSmithClient(
        failures={
            ("/v2/auth/providers", WORKSPACE_PROD_ID): 403,
            ("/v2/auth/providers", WORKSPACE_DEV_ID): 403,
        }
    )

    # Act
    _sync(neo4j_session, no_providers, NEXT_UPDATE_TAG)

    # Assert
    assert (TRIAGE_CREDENTIAL_ID, GITHUB_PROVIDER_ID) in check_rels(
        neo4j_session,
        "LangSmithAgentCredential",
        "id",
        "LangSmithOAuthProvider",
        "id",
        "FOR_PROVIDER",
    )


DATA_PLANES = "/orgs/current/data-planes"
DATA_PLANE = {
    "id": "dd11dd11-0001-4001-8001-dd11dd11dd11",
    "name": "eu-hybrid",
    "status": "active",
    "created_at": "2026-02-01T09:00:00Z",
}


def test_a_denied_data_plane_listing_falls_back_to_the_summary_view(neo4j_session):
    # Arrange
    summary_row = {k: v for k, v in DATA_PLANE.items() if k != "created_at"}
    summary_only = FakeLangSmithClient(
        routes={
            **SIMPSON_CORP_ROUTES,
            (f"{DATA_PLANES}?view=SUMMARY", None): [summary_row],
        },
        failures={(DATA_PLANES, None): 403},
    )

    # Act
    _sync(neo4j_session, summary_only, TEST_UPDATE_TAG)

    # Assert
    # The full view needs organization:infrastructure:read; the summary view still names
    # the data plane, just without its creation time.
    assert check_nodes(neo4j_session, "LangSmithDataPlane", ["id", "name"]) == {
        (DATA_PLANE["id"], DATA_PLANE["name"])
    }


def test_the_summary_view_keeps_a_known_data_plane_creation_time(neo4j_session):
    # Arrange
    _sync(
        neo4j_session,
        FakeLangSmithClient(
            routes={**SIMPSON_CORP_ROUTES, (DATA_PLANES, None): [DATA_PLANE]}
        ),
        TEST_UPDATE_TAG,
    )
    summary_row = {k: v for k, v in DATA_PLANE.items() if k != "created_at"}
    summary_only = FakeLangSmithClient(
        routes={
            **SIMPSON_CORP_ROUTES,
            (f"{DATA_PLANES}?view=SUMMARY", None): [summary_row],
        },
        failures={(DATA_PLANES, None): 403},
    )

    # Act
    _sync(neo4j_session, summary_only, NEXT_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session, "LangSmithDataPlane", ["id", "created_at", "lastupdated"]
    ) == {(DATA_PLANE["id"], DATA_PLANE["created_at"], NEXT_UPDATE_TAG)}


def test_providers_are_cleaned_up_when_one_workspace_answers(neo4j_session):
    # Arrange
    _sync(neo4j_session, FakeLangSmithClient(), TEST_UPDATE_TAG)
    github_only = [
        provider
        for provider in SIMPSON_CORP_ROUTES[("/v2/auth/providers", WORKSPACE_DEV_ID)]
        if provider["id"] == GITHUB_PROVIDER_ID
    ]
    one_workspace = FakeLangSmithClient(
        routes={
            **SIMPSON_CORP_ROUTES,
            ("/v2/auth/providers", WORKSPACE_DEV_ID): github_only,
        },
        failures={
            ("/v2/auth/providers", WORKSPACE_PROD_ID): 403,
            ("/v2/auth/platform-providers", WORKSPACE_PROD_ID): 403,
        },
    )

    # Act
    _sync(neo4j_session, one_workspace, NEXT_UPDATE_TAG)

    # Assert
    # The provider listing is organization-wide, so one workspace answering is enough.
    providers = _ids(neo4j_session, "LangSmithOAuthProvider")
    assert GITHUB_PROVIDER_ID in providers
    assert GOOGLE_PROVIDER_ID not in providers


def test_one_unreadable_workspace_does_not_block_cleanup_in_another(neo4j_session):
    # Arrange
    _sync(neo4j_session, FakeLangSmithClient(), TEST_UPDATE_TAG)
    prod_hidden_dev_emptied = FakeLangSmithClient(
        routes={
            **SIMPSON_CORP_ROUTES,
            ("/api/v1/workspaces/current/secrets", WORKSPACE_DEV_ID): [],
            ("/v2/deployments", WORKSPACE_DEV_ID): [],
        },
        failures={
            ("/api/v1/workspaces/current/secrets", WORKSPACE_PROD_ID): 403,
            ("/v2/deployments", WORKSPACE_PROD_ID): 403,
        },
    )

    # Act
    _sync(neo4j_session, prod_hidden_dev_emptied, NEXT_UPDATE_TAG)

    # Assert
    # Each workspace is cleaned up on its own: the readable one loses what was deleted,
    # and the unreadable one keeps everything it held.
    secrets = _ids(neo4j_session, "LangSmithSecret")
    assert f"{WORKSPACE_DEV_ID}|OPENAI_API_KEY" not in secrets
    assert f"{WORKSPACE_PROD_ID}|OPENAI_API_KEY" in secrets
    assert f"{WORKSPACE_PROD_ID}|SLACK_BOT_TOKEN" in secrets
    deployments = _ids(neo4j_session, "LangSmithDeployment")
    assert TRIAGE_DEPLOYMENT_ID not in deployments
    assert SUPPORT_DEPLOYMENT_ID in deployments


def test_a_deleted_workspace_takes_what_it_held_with_it(neo4j_session):
    # Arrange
    _sync(neo4j_session, FakeLangSmithClient(), TEST_UPDATE_TAG)
    prod_only = [w for w in LANGSMITH_WORKSPACES if w["id"] == WORKSPACE_PROD_ID]
    dev_deleted = FakeLangSmithClient(
        routes={**SIMPSON_CORP_ROUTES, ("/api/v1/workspaces", None): prod_only}
    )

    # Act
    _sync(neo4j_session, dev_deleted, NEXT_UPDATE_TAG)

    # Assert
    # Nothing can reach these nodes once their workspace is gone, so they go with it.
    assert WORKSPACE_DEV_ID not in _ids(neo4j_session, "LangSmithWorkspace")
    assert TRIAGE_DEPLOYMENT_ID not in _ids(neo4j_session, "LangSmithDeployment")
    assert f"{WORKSPACE_DEV_ID}|OPENAI_API_KEY" not in _ids(
        neo4j_session, "LangSmithSecret"
    )
    assert f"{BART_LS_USER_ID}|{WORKSPACE_DEV_ID}" not in _ids(
        neo4j_session, "LangSmithWorkspaceMembership"
    )
    assert SUPPORT_DEPLOYMENT_ID in _ids(neo4j_session, "LangSmithDeployment")


def test_the_migration_moves_an_older_graph_onto_its_workspaces(neo4j_session):
    # Arrange
    # Earlier versions hung workspace resources off the organization, linking them to
    # their workspace with CONTAINS (or IN_WORKSPACE for memberships).
    _sync(neo4j_session, FakeLangSmithClient(), TEST_UPDATE_TAG)
    neo4j_session.run(
        """
        MATCH (o:LangSmithOrganization {id: $org_id})-[:RESOURCE]->(w:LangSmithWorkspace)
              -[r:RESOURCE]->(n)
        DELETE r
        MERGE (o)-[:RESOURCE]->(n)
        WITH w, n
        FOREACH (_ IN CASE WHEN n:LangSmithWorkspaceMembership THEN [1] ELSE [] END |
            MERGE (n)-[:IN_WORKSPACE]->(w))
        FOREACH (_ IN CASE WHEN n:LangSmithWorkspaceMembership THEN [] ELSE [1] END |
            MERGE (w)-[:CONTAINS]->(n))
        """,
        org_id=LANGSMITH_ORG_ID,
    )
    prod_secrets_hidden = FakeLangSmithClient(
        failures={("/api/v1/workspaces/current/secrets", WORKSPACE_PROD_ID): 403}
    )

    # Act
    _sync(neo4j_session, prod_secrets_hidden, NEXT_UPDATE_TAG)

    # Assert
    # A secret that could not be re-read is still reachable from its workspace, so a
    # later sync can clean it up.
    assert (WORKSPACE_PROD_ID, f"{WORKSPACE_PROD_ID}|SLACK_BOT_TOKEN") in check_rels(
        neo4j_session, "LangSmithWorkspace", "id", "LangSmithSecret", "id", "RESOURCE"
    )
    leftovers = neo4j_session.run(
        """
        MATCH (:LangSmithOrganization)-[r:RESOURCE]->(n)
        WHERE n:LangSmithDeployment OR n:LangSmithSecret OR n:LangSmithResourceTag
           OR n:LangSmithMcpServer OR n:LangSmithWorkspaceMembership
        RETURN count(r) AS org_edges
        UNION ALL
        MATCH (:LangSmithWorkspace)-[r:CONTAINS]->(n)
        WHERE NOT n:LangSmithApiKey
        RETURN count(r) AS org_edges
        UNION ALL
        MATCH ()-[r:IN_WORKSPACE]->()
        RETURN count(r) AS org_edges
        """
    ).data()
    assert [row["org_edges"] for row in leftovers] == [0, 0, 0]


def test_syncing_another_organization_keeps_this_organizations_graph(neo4j_session):
    # Arrange
    other_org_id = "00000000-0000-4000-8000-000000000002"
    other_workspace_id = "cccccccc-3333-4333-8333-cccccccccccc"
    # Marge also belongs to a second organization, whose roles grant a permission string
    # Simpson Corp's roles grant too.
    other_org = FakeLangSmithClient(
        routes={
            ("/api/v1/orgs/current/info", None): {"display_name": "Flanders Ltd"},
            ("/api/v1/orgs/current/roles", None): [
                # Built-in roles keep the same UUID in every organization.
                {
                    "id": WORKSPACE_VIEWER_ROLE_ID,
                    "name": "WORKSPACE_VIEWER",
                    "display_name": "Viewer",
                    "organization_id": None,
                    "access_scope": "workspace",
                    "permissions": ["workspaces:read"],
                },
                {
                    "id": "44444444-4444-4444-8444-444444444444",
                    "name": "CUSTOM",
                    "display_name": "Auditor",
                    "organization_id": other_org_id,
                    "access_scope": "workspace",
                    "permissions": ["workspaces:read"],
                },
            ],
            ("/api/v1/workspaces", None): [
                {
                    "id": other_workspace_id,
                    "organization_id": other_org_id,
                    "display_name": "Main",
                },
            ],
            ("/api/v1/orgs/current/members/active", None): [
                {
                    "id": "d9d9d9d9-0009-4009-8009-d9d9d9d9d9d9",
                    "ls_user_id": MARGE_LS_USER_ID,
                    "email": "mbsimpson@simpson.corp",
                    "is_disabled": False,
                    "tenant_ids": [other_workspace_id],
                },
            ],
            ("/api/v1/orgs/current/members/pending", None): [],
            ("/api/v1/workspaces/current/members", other_workspace_id): {
                "members": [],
                "pending": [],
            },
        },
    )
    _sync(neo4j_session, FakeLangSmithClient(), TEST_UPDATE_TAG)

    # Act
    _sync(neo4j_session, other_org, NEXT_UPDATE_TAG, org_id=other_org_id)

    # Assert
    assert check_rels(
        neo4j_session, "LangSmithUser", "id", "LangSmithWorkspace", "id", "MEMBER_OF"
    ) == {
        (MARGE_LS_USER_ID, WORKSPACE_PROD_ID),
        (MARGE_LS_USER_ID, WORKSPACE_DEV_ID),
        (MARGE_LS_USER_ID, other_workspace_id),
        (HOMER_LS_USER_ID, WORKSPACE_PROD_ID),
        (BART_LS_USER_ID, WORKSPACE_DEV_ID),
    }
    # Each organization owns its own role and permission nodes, so neither cleanup can
    # reach the other's, even for a built-in role both organizations share.
    assert (WORKSPACE_VIEWER_ROLE, f"{LANGSMITH_ORG_ID}|workspaces:read") in check_rels(
        neo4j_session, "LangSmithRole", "id", "LangSmithPermission", "id", "GRANTS"
    )
    assert {
        WORKSPACE_VIEWER_ROLE,
        f"{other_org_id}|{WORKSPACE_VIEWER_ROLE_ID}",
    } <= _ids(neo4j_session, "LangSmithRole")
    assert _ids(neo4j_session, "LangSmithPermission") == {
        f"{LANGSMITH_ORG_ID}|organization:manage",
        f"{LANGSMITH_ORG_ID}|organization:read",
        f"{LANGSMITH_ORG_ID}|workspaces:read",
        f"{LANGSMITH_ORG_ID}|deployments:read",
        f"{other_org_id}|workspaces:read",
    }
