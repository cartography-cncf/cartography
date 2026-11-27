from unittest.mock import MagicMock
from unittest.mock import patch

from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.errors import HttpError

from cartography.intel.googleworkspace.apps_script import (
    sync_googleworkspace_apps_script,
)
from tests.data.googleworkspace.apps_script import DEPLOYMENTS_ANON_OWNER
from tests.data.googleworkspace.apps_script import DEPLOYMENTS_DOMAIN_USER
from tests.data.googleworkspace.apps_script import DEPLOYMENTS_HEAD_ONLY
from tests.data.googleworkspace.apps_script import FAKE_DEPLOYMENT_ID
from tests.data.googleworkspace.apps_script import PROJECT_ANON_OWNER
from tests.data.googleworkspace.apps_script import PROJECT_DOMAIN_USER
from tests.data.googleworkspace.apps_script import PROJECT_HEAD_ONLY
from tests.integration.cartography.intel.googleworkspace.test_tenant import (
    _ensure_local_neo4j_has_test_tenant,
)
from tests.integration.cartography.intel.googleworkspace.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CUSTOMER_ID = "ABC123CD"


def _make_http_error(status: int) -> HttpError:
    resp = MagicMock()
    resp.status = status
    resp.reason = "Forbidden"
    return HttpError(resp=resp, content=b'{"error": "forbidden"}')


def _make_service_account_creds() -> MagicMock:
    creds = MagicMock(spec=ServiceAccountCredentials)
    creds.with_scopes.return_value = creds
    creds.with_subject.return_value = creds
    return creds


def _make_user_services(
    projects_by_id: dict[str, tuple[dict, list[dict]]],
) -> tuple[MagicMock, MagicMock]:
    drive = MagicMock()
    drive.files.return_value.list.return_value.execute.return_value = {
        "files": [{"id": script_id} for script_id in projects_by_id],
    }

    script = MagicMock()
    script.projects.return_value.get.side_effect = lambda scriptId: MagicMock(
        execute=MagicMock(return_value=projects_by_id[scriptId][0])
    )
    script.projects.return_value.deployments.return_value.list.side_effect = (
        lambda scriptId, **kwargs: MagicMock(
            execute=MagicMock(return_value={"deployments": projects_by_id[scriptId][1]})
        )
    )
    return drive, script


@patch("cartography.intel.googleworkspace.apps_script.googleapiclient.discovery.build")
def test_sync_googleworkspace_apps_script_nodes_rels_and_cleanup(
    mock_build, neo4j_session
):
    _ensure_local_neo4j_has_test_tenant(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    creds = _make_service_account_creds()

    # Run 1: user-1 has 2 projects (head-only + anon-owner), user-2 has 1 project (domain-user)
    drive_u1, script_u1 = _make_user_services(
        {
            "script-head-only-1": (PROJECT_HEAD_ONLY, DEPLOYMENTS_HEAD_ONLY),
            "script-anon-owner-2": (PROJECT_ANON_OWNER, DEPLOYMENTS_ANON_OWNER),
        }
    )
    drive_u2, script_u2 = _make_user_services(
        {
            "script-domain-user-3": (PROJECT_DOMAIN_USER, DEPLOYMENTS_DOMAIN_USER),
        }
    )
    mock_build.side_effect = [drive_u1, script_u1, drive_u2, script_u2]

    sync_googleworkspace_apps_script(
        neo4j_session,
        creds,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "CUSTOMER_ID": TEST_CUSTOMER_ID},
    )

    assert check_nodes(
        neo4j_session,
        "GoogleWorkspaceAppsScriptProject",
        [
            "id",
            "title",
            "versioned_deployment_count",
            "webapp_access",
            "webapp_execute_as",
            "is_anonymous_webapp_running_as_deployer",
        ],
    ) == {
        ("script-head-only-1", "Head Only Script", 0, None, None, False),
        (
            "script-anon-owner-2",
            "Public Webhook",
            1,
            "ANYONE_ANONYMOUS",
            "USER_DEPLOYING",
            True,
        ),
        (
            "script-domain-user-3",
            "Internal Tool",
            1,
            "DOMAIN",
            "USER_ACCESSING",
            False,
        ),
    }

    assert check_rels(
        neo4j_session,
        "GoogleWorkspaceAppsScriptProject",
        "id",
        "GoogleWorkspaceTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("script-head-only-1", TEST_CUSTOMER_ID),
        ("script-anon-owner-2", TEST_CUSTOMER_ID),
        ("script-domain-user-3", TEST_CUSTOMER_ID),
    }

    assert check_rels(
        neo4j_session,
        "GoogleWorkspaceUser",
        "id",
        "GoogleWorkspaceAppsScriptProject",
        "id",
        "OWNS",
        rel_direction_right=True,
    ) == {
        ("user-1", "script-head-only-1"),
        ("user-1", "script-anon-owner-2"),
        ("user-2", "script-domain-user-3"),
    }

    # Verify no node property contains FAKE-DEPLOYMENT-ID-123
    props_result = neo4j_session.run(
        "MATCH (p:GoogleWorkspaceAppsScriptProject) RETURN properties(p) AS props"
    )
    for record in props_result:
        for val in record["props"].values():
            assert FAKE_DEPLOYMENT_ID not in str(val)

    # Run 2 (incomplete): user-1 returns 403, user-2 has only script-domain-user-3 -> stale nodes kept
    drive_u1_403 = MagicMock()
    drive_u1_403.files.return_value.list.return_value.execute.side_effect = (
        _make_http_error(403)
    )
    drive_u2_r2, script_u2_r2 = _make_user_services(
        {
            "script-domain-user-3": (PROJECT_DOMAIN_USER, DEPLOYMENTS_DOMAIN_USER),
        }
    )
    mock_build.side_effect = [drive_u1_403, drive_u2_r2, script_u2_r2]

    sync_googleworkspace_apps_script(
        neo4j_session,
        creds,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "CUSTOMER_ID": TEST_CUSTOMER_ID},
    )

    assert check_nodes(neo4j_session, "GoogleWorkspaceAppsScriptProject", ["id"]) == {
        ("script-head-only-1",),
        ("script-anon-owner-2",),
        ("script-domain-user-3",),
    }

    # Run 3 (complete): user-1 has only script-anon-owner-2 -> script-head-only-1 removed
    drive_u1_r3, script_u1_r3 = _make_user_services(
        {
            "script-anon-owner-2": (PROJECT_ANON_OWNER, DEPLOYMENTS_ANON_OWNER),
        }
    )
    drive_u2_r3, script_u2_r3 = _make_user_services(
        {
            "script-domain-user-3": (PROJECT_DOMAIN_USER, DEPLOYMENTS_DOMAIN_USER),
        }
    )
    mock_build.side_effect = [drive_u1_r3, script_u1_r3, drive_u2_r3, script_u2_r3]

    sync_googleworkspace_apps_script(
        neo4j_session,
        creds,
        TEST_UPDATE_TAG + 2,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 2, "CUSTOMER_ID": TEST_CUSTOMER_ID},
    )

    assert check_nodes(neo4j_session, "GoogleWorkspaceAppsScriptProject", ["id"]) == {
        ("script-anon-owner-2",),
        ("script-domain-user-3",),
    }


@patch("cartography.intel.googleworkspace.apps_script.googleapiclient.discovery.build")
def test_partial_sync_cleans_up_only_users_read_completely(mock_build, neo4j_session):
    _ensure_local_neo4j_has_test_tenant(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    creds = _make_service_account_creds()

    # Arrange: user-1 owns script-anon-owner-2, user-2 owns script-domain-user-3
    drive_u1, script_u1 = _make_user_services(
        {"script-anon-owner-2": (PROJECT_ANON_OWNER, DEPLOYMENTS_ANON_OWNER)}
    )
    drive_u2, script_u2 = _make_user_services(
        {"script-domain-user-3": (PROJECT_DOMAIN_USER, DEPLOYMENTS_DOMAIN_USER)}
    )
    mock_build.side_effect = [drive_u1, script_u1, drive_u2, script_u2]
    sync_googleworkspace_apps_script(
        neo4j_session,
        creds,
        TEST_UPDATE_TAG + 10,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 10, "CUSTOMER_ID": TEST_CUSTOMER_ID},
    )

    # Act: user-1 cannot be read; user-2 is read and has deleted its only script
    drive_u1_403 = MagicMock()
    drive_u1_403.files.return_value.list.return_value.execute.side_effect = (
        _make_http_error(403)
    )
    drive_u2_empty, _ = _make_user_services({})
    mock_build.side_effect = [drive_u1_403, drive_u2_empty]
    sync_googleworkspace_apps_script(
        neo4j_session,
        creds,
        TEST_UPDATE_TAG + 11,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 11, "CUSTOMER_ID": TEST_CUSTOMER_ID},
    )

    # Assert: user-1's unread project is kept, user-2's deleted project is removed
    assert check_nodes(neo4j_session, "GoogleWorkspaceAppsScriptProject", ["id"]) == {
        ("script-anon-owner-2",),
    }
