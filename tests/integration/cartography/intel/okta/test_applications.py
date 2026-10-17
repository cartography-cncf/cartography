import json
import logging
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from okta.models.application_json_converter import ApplicationJsonConverter

import cartography.intel.okta.applications
from tests.data.okta.application import APP_GRANTS
from tests.data.okta.application import APPLICATIONS
from tests.data.okta.application import CLIENT_ROLES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789


def _create_common_job_parameters():
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OKTA_ORG_ID": TEST_ORG_ID,
    }


def _create_mock_application(app_id: str, name: str, label: str) -> MagicMock:
    """Create a mock OktaApplication object with all required nested structures."""
    app = MagicMock()
    app.id = app_id
    app.name = name
    app.label = label
    app.created = "2019-01-01T00:00:01.000Z"
    app.last_updated = "2019-01-01T00:00:01.000Z"
    app.features = []

    # Status
    app.status = MagicMock()
    app.status.value = "ACTIVE"

    # Activated timestamp
    app.activated = "2019-01-01T00:00:01.000Z"

    # Sign on mode
    app.sign_on_mode = MagicMock()
    app.sign_on_mode.value = "SAML_2_0"

    # Licensing (optional - uses hasattr check)
    app.licensing = MagicMock()
    app.licensing.seat_count = None

    # Accessibility
    app.accessibility = MagicMock()
    app.accessibility.error_redirect_url = None
    app.accessibility.login_redirect_url = None
    app.accessibility.self_service = False

    # Credentials with nested signing and user_name_template
    app.credentials = MagicMock()
    app.credentials.signing = MagicMock()
    app.credentials.signing.kid = None
    app.credentials.signing.last_rotated = None
    app.credentials.signing.next_rotation = None
    app.credentials.signing.rotation_mode = None
    app.credentials.signing.use = None
    app.credentials.user_name_template = MagicMock()
    app.credentials.user_name_template.push_status = None
    app.credentials.user_name_template.user_suffix = None
    app.credentials.user_name_template.template = None
    app.credentials.user_name_template.type = None

    # Settings with deeply nested structures
    app.settings = MagicMock()
    app.settings.app = MagicMock()
    app.settings.app.acs_url = None
    app.settings.app.button_field = None
    app.settings.app.login_url_regex = None
    app.settings.app.org_name = None
    app.settings.app.password_field = None
    app.settings.app.url = None
    app.settings.app.username_field = None
    app.settings.implicit_assignment = False
    app.settings.inline_hook_id = None
    app.settings.notifications = MagicMock()
    app.settings.notifications.vpn = MagicMock()
    app.settings.notifications.vpn.help_url = None
    app.settings.notifications.vpn.message = None
    app.settings.notifications.vpn.network = MagicMock()
    app.settings.notifications.vpn.network.connection = None
    app.settings.notifications.vpn.network.exclude = []
    app.settings.notifications.vpn.network.include = []
    app.settings.notes = MagicMock()
    app.settings.notes.admin = None
    app.settings.notes.enduser = None
    # sign_on is optional (uses hasattr + None check for SAML apps)
    app.settings.sign_on = None
    # oauth_client is optional (uses hasattr + None check)
    app.settings.oauth_client = None

    # Visibility
    app.visibility = MagicMock()
    app.visibility.app_links = {}
    app.visibility.auto_launch = False
    app.visibility.auto_submit_toolbar = False
    app.visibility.hide = MagicMock()
    app.visibility.hide.to_dict = MagicMock(return_value={})

    return app


@patch.object(
    cartography.intel.okta.applications,
    "_get_okta_applications",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_users",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_groups",
    new_callable=AsyncMock,
)
def test_sync_okta_applications(
    mock_get_groups,
    mock_get_users,
    mock_get_apps,
    neo4j_session,
):
    """
    Test that Okta applications are synced correctly to the graph.
    """
    # Arrange - Create test applications
    test_app_1 = _create_mock_application("app-001", "salesforce", "Salesforce")
    test_app_2 = _create_mock_application("app-002", "github", "GitHub")

    # Mock the API calls
    mock_get_apps.return_value = [test_app_1, test_app_2]
    mock_get_users.return_value = []
    mock_get_groups.return_value = []

    # Create the OktaOrganization node first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    okta_client = MagicMock()
    common_job_parameters = _create_common_job_parameters()

    # Act - Call the main sync function
    result = cartography.intel.okta.applications.sync_okta_applications(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Verify applications were created with correct properties
    assert result.app_ids == {"app-001", "app-002"}
    expected_apps = {
        ("app-001", "salesforce", "Salesforce"),
        ("app-002", "github", "GitHub"),
    }
    actual_apps = check_nodes(neo4j_session, "OktaApplication", ["id", "name", "label"])
    assert actual_apps == expected_apps

    # Assert - Verify applications are connected to organization
    expected_org_rels = {
        (TEST_ORG_ID, "app-001"),
        (TEST_ORG_ID, "app-002"),
    }
    actual_org_rels = check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaApplication",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert actual_org_rels == expected_org_rels


@patch.object(
    cartography.intel.okta.applications,
    "_get_okta_applications",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_users",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_groups",
    new_callable=AsyncMock,
)
def test_sync_okta_applications_with_users(
    mock_get_groups,
    mock_get_users,
    mock_get_apps,
    neo4j_session,
):
    """
    Test that application-to-user relationships are created correctly.
    """
    # Arrange - Create test application
    test_app = _create_mock_application("app-with-users", "test_app", "Test App")

    # Create test users in the graph first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u1:OktaUser{id: 'user-001'})
        SET u1.email = 'user1@example.com', u1.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u2:OktaUser{id: 'user-002'})
        SET u2.email = 'user2@example.com', u2.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock the API calls
    # _get_application_assigned_users returns a list of user ID strings
    mock_get_apps.return_value = [test_app]
    mock_get_users.return_value = ["user-001", "user-002"]
    mock_get_groups.return_value = []

    okta_client = MagicMock()
    common_job_parameters = _create_common_job_parameters()

    # Act
    cartography.intel.okta.applications.sync_okta_applications(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Verify APPLICATION relationships between users and application
    expected_user_app_rels = {
        ("user-001", "app-with-users"),
        ("user-002", "app-with-users"),
    }
    actual_user_app_rels = check_rels(
        neo4j_session,
        "OktaUser",
        "id",
        "OktaApplication",
        "id",
        "APPLICATION",
        rel_direction_right=True,
    )
    assert actual_user_app_rels == expected_user_app_rels


@patch.object(
    cartography.intel.okta.applications,
    "_get_okta_applications",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_users",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_groups",
    new_callable=AsyncMock,
)
def test_sync_okta_applications_with_groups(
    mock_get_groups,
    mock_get_users,
    mock_get_apps,
    neo4j_session,
):
    """
    Test that application-to-group relationships are created correctly.
    """
    # Arrange - Create test application
    test_app = _create_mock_application("app-with-groups", "test_app", "Test App")

    # Create test groups in the graph first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(g1:OktaGroup{id: 'group-001'})
        SET g1.name = 'Engineering', g1.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(g2:OktaGroup{id: 'group-002'})
        SET g2.name = 'Product', g2.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock the API calls
    # _get_application_assigned_groups returns a list of group ID strings
    mock_get_apps.return_value = [test_app]
    mock_get_users.return_value = []
    mock_get_groups.return_value = ["group-001", "group-002"]

    okta_client = MagicMock()
    common_job_parameters = _create_common_job_parameters()

    # Act
    cartography.intel.okta.applications.sync_okta_applications(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Verify APPLICATION relationships between groups and application
    expected_group_app_rels = {
        ("group-001", "app-with-groups"),
        ("group-002", "app-with-groups"),
    }
    actual_group_app_rels = check_rels(
        neo4j_session,
        "OktaGroup",
        "id",
        "OktaApplication",
        "id",
        "APPLICATION",
        rel_direction_right=True,
    )
    assert actual_group_app_rels == expected_group_app_rels


@patch.object(
    cartography.intel.okta.applications,
    "_get_okta_applications",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_users",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_groups",
    new_callable=AsyncMock,
)
def test_sync_okta_applications_updates_existing(
    mock_get_groups,
    mock_get_users,
    mock_get_apps,
    neo4j_session,
):
    """
    Test that syncing updates existing applications rather than creating duplicates.
    """
    # Arrange - Create an existing application in the graph
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(app:OktaApplication{id: 'app-existing'})
        SET app.name = 'old_name',
            app.label = 'Old Label',
            app.status = 'INACTIVE',
            app.lastupdated = 111111
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Create updated application data
    test_app = _create_mock_application("app-existing", "updated_name", "Updated Label")

    mock_get_apps.return_value = [test_app]
    mock_get_users.return_value = []
    mock_get_groups.return_value = []

    okta_client = MagicMock()
    common_job_parameters = _create_common_job_parameters()

    # Act
    cartography.intel.okta.applications.sync_okta_applications(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Application should be updated, not duplicated
    result = neo4j_session.run(
        """
        MATCH (app:OktaApplication{id: 'app-existing'})
        RETURN app.name as name, app.label as label, app.status as status, app.lastupdated as lastupdated
        """,
    )
    apps = [dict(r) for r in result]
    assert len(apps) == 1  # Should be only one application
    app_data = apps[0]
    assert app_data["name"] == "updated_name"
    assert app_data["label"] == "Updated Label"
    assert app_data["status"] == "ACTIVE"
    assert app_data["lastupdated"] == TEST_UPDATE_TAG


# Okta answers an OAuth token without an endpoint's scope with a bare 403, and a
# credential whose admin role does not allow a request with E0000006.
INSUFFICIENT_SCOPE = SimpleNamespace(
    status=403,
    response_headers={
        "WWW-Authenticate": 'DPoP scope="okta.appGrants.read", error="insufficient_scope"',
    },
)
ADMIN_ROLE_REFUSED = SimpleNamespace(error_code="E0000006")


class _FakeOktaClient:
    """
    Stands in for the Okta SDK client: the typed list methods and the request
    executor behind the raw JSON helpers.
    """

    def __init__(self, refusals: dict[str, Any] | None = None) -> None:
        self.applications = [
            ApplicationJsonConverter.from_dict(app) for app in APPLICATIONS
        ]
        self.bodies: dict[str, Any] = {
            **{
                f"/oauth2/v1/clients/{client_id}/roles": roles
                for client_id, roles in CLIENT_ROLES.items()
            },
            **{
                f"/api/v1/apps/{app_id}/grants": grants
                for app_id, grants in APP_GRANTS.items()
            },
        }
        # Errors returned for every path that starts with a given prefix.
        self.refusals = refusals or {}
        self.raw_paths: list[str] = []

    async def list_applications(self, **kwargs: Any) -> tuple[Any, Any, Any]:
        return self.applications, SimpleNamespace(headers={}), None

    async def list_application_users(self, **kwargs: Any) -> tuple[Any, Any, Any]:
        return [], SimpleNamespace(headers={}), None

    async def list_application_group_assignments(
        self,
        **kwargs: Any,
    ) -> tuple[Any, Any, Any]:
        return [], SimpleNamespace(headers={}), None

    def get_request_executor(self) -> "_FakeOktaClient":
        return self

    async def create_request(
        self,
        method: str,
        url: str,
        body: Any,
        headers: Any,
    ) -> tuple[dict[str, str], None]:
        return {"url": url}, None

    async def execute(self, request: dict[str, str]) -> tuple[Any, Any, Any]:
        path = request["url"]
        self.raw_paths.append(path)
        response = SimpleNamespace(links={})
        for prefix, error in self.refusals.items():
            if path.startswith(prefix):
                return response, None, error
        return response, json.dumps(self.bodies.get(path, [])), None


def _seed_org(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        "MERGE (o:OktaOrganization {id: $org_id}) SET o.lastupdated = $update_tag",
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )


def _granted_scopes(neo4j_session) -> dict[str, list[str] | None]:
    result = neo4j_session.run(
        "MATCH (a:OktaApplication) RETURN a.id AS id, a.granted_scopes AS scopes",
    )
    return {record["id"]: record["scopes"] for record in result}


def test_sync_okta_applications_loads_privileges_and_client_auth(neo4j_session):
    # Arrange
    _seed_org(neo4j_session)
    okta_client = _FakeOktaClient()

    # Act
    result = cartography.intel.okta.applications.sync_okta_applications(
        okta_client,
        neo4j_session,
        _create_common_job_parameters(),
    )

    # Assert
    assert result.roles_synced is True
    assert result.grants_synced is True
    assert check_nodes(
        neo4j_session,
        "OktaApplication",
        [
            "id",
            "credentials_oauth_client_token_endpoint_auth_method",
            "settings_oauth_client_dpop_bound_access_tokens",
        ],
    ) == {
        ("0oaService", "private_key_jwt", True),
        ("0oaWeb", "client_secret_basic", False),
        ("0oaFeatures", None, None),
    }
    assert _granted_scopes(neo4j_session) == {
        "0oaService": ["okta.apps.read", "okta.users.read"],
        "0oaWeb": ["okta.users.manage"],
        # A SAML app has no OAuth client, so it has no grants to read.
        "0oaFeatures": None,
    }
    assert check_nodes(
        neo4j_session,
        "OktaApplicationRole",
        ["id", "assignment_id", "role_type", "label", "assignment_type"],
    ) == {
        (
            "0oaService:KNKVARKSL5AUITKJJY",
            "KNKVARKSL5AUITKJJY",
            "SUPER_ADMIN",
            "Super Administrator",
            "CLIENT",
        ),
    }
    assert check_rels(
        neo4j_session,
        "OktaApplication",
        "id",
        "OktaApplicationRole",
        "id",
        "HAS_ROLE",
    ) == {("0oaService", "0oaService:KNKVARKSL5AUITKJJY")}
    assert check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaApplicationRole",
        "id",
        "RESOURCE",
    ) == {(TEST_ORG_ID, "0oaService:KNKVARKSL5AUITKJJY")}
    assert check_nodes(neo4j_session, "PermissionRole", ["id"]) == {
        ("0oaService:KNKVARKSL5AUITKJJY",),
    }
    # Only a service app can hold an admin role, and only OIDC apps have grants.
    assert sorted(okta_client.raw_paths) == [
        "/api/v1/apps/0oaService/grants",
        "/api/v1/apps/0oaWeb/grants",
        "/oauth2/v1/clients/0oaService/roles",
    ]


def test_sync_okta_applications_skips_roles_and_grants_without_permission(
    neo4j_session,
    caplog,
):
    # Arrange
    _seed_org(neo4j_session)

    # Act: a privileged credential reads the service app's role.
    cartography.intel.okta.applications.sync_okta_applications(
        _FakeOktaClient(),
        neo4j_session,
        _create_common_job_parameters(),
    )

    # Assert
    assert check_nodes(neo4j_session, "OktaApplicationRole", ["id"]) == {
        ("0oaService:KNKVARKSL5AUITKJJY",),
    }

    # Arrange: the next credential's admin role cannot read roles, and its
    # access token lacks okta.appGrants.read.
    refusing_client = _FakeOktaClient(
        refusals={
            "/oauth2/v1/clients/": ADMIN_ROLE_REFUSED,
            "/api/v1/apps/": INSUFFICIENT_SCOPE,
        },
    )

    # Act
    with caplog.at_level(logging.WARNING):
        result = cartography.intel.okta.applications.sync_okta_applications(
            refusing_client,
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "OKTA_ORG_ID": TEST_ORG_ID},
        )

    # Assert
    assert result.roles_synced is False
    assert result.grants_synced is False
    assert "Unable to sync Okta application roles" in caplog.text
    assert "Unable to sync Okta application scope grants" in caplog.text
    # The role read with the previous credential is stale and removed.
    assert check_nodes(neo4j_session, "OktaApplicationRole", ["id"]) == set()
    # Unknown, not empty: the grants could not be read.
    assert _granted_scopes(neo4j_session) == {
        "0oaService": None,
        "0oaWeb": None,
        "0oaFeatures": None,
    }
