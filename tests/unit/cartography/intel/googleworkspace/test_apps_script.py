import json
import logging
from unittest.mock import MagicMock
from unittest.mock import patch

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials as OAuth2Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.errors import HttpError

from cartography.intel.googleworkspace.apps_script import (
    sync_googleworkspace_apps_script,
)
from cartography.intel.googleworkspace.apps_script import transform_apps_script_project
from tests.data.googleworkspace.apps_script import DEPLOYMENTS_ANON_OWNER
from tests.data.googleworkspace.apps_script import DEPLOYMENTS_DOMAIN_USER
from tests.data.googleworkspace.apps_script import DEPLOYMENTS_HEAD_ONLY
from tests.data.googleworkspace.apps_script import DEPLOYMENTS_MULTI_DEPLOY
from tests.data.googleworkspace.apps_script import DEPLOYMENTS_NONE
from tests.data.googleworkspace.apps_script import FAKE_DEPLOYMENT_ID
from tests.data.googleworkspace.apps_script import PROJECT_ANON_OWNER
from tests.data.googleworkspace.apps_script import PROJECT_DOMAIN_USER
from tests.data.googleworkspace.apps_script import PROJECT_HEAD_ONLY
from tests.data.googleworkspace.apps_script import PROJECT_MULTI_DEPLOY
from tests.data.googleworkspace.apps_script import PROJECT_NO_DEPLOYMENTS


def _make_http_error(status: int) -> HttpError:
    resp = MagicMock()
    resp.status = status
    resp.reason = "Error"
    return HttpError(resp=resp, content=b'{"error": "error"}')


def _make_service_account_creds() -> MagicMock:
    creds = MagicMock(spec=ServiceAccountCredentials)
    creds.with_scopes.return_value = creds
    creds.with_subject.return_value = creds
    return creds


def test_transform_head_only_excluded():
    result = transform_apps_script_project(
        "user-1", PROJECT_HEAD_ONLY, DEPLOYMENTS_HEAD_ONLY
    )
    assert result == {
        "id": "script-head-only-1",
        "title": "Head Only Script",
        "create_time": "2024-01-10T00:00:00Z",
        "update_time": "2024-01-11T00:00:00Z",
        "parent_id": "folder-parent-1",
        "creator_email": "mbsimpson@simpson.corp",
        "owner_user_id": "user-1",
        "versioned_deployment_count": 0,
        "webapp_access": None,
        "webapp_execute_as": None,
        "is_anonymous_webapp_running_as_deployer": False,
        "api_executable_access": None,
    }


def test_transform_anonymous_webapp_running_as_deployer():
    result = transform_apps_script_project(
        "user-1", PROJECT_ANON_OWNER, DEPLOYMENTS_ANON_OWNER
    )
    assert result["versioned_deployment_count"] == 1
    assert result["webapp_access"] == "ANYONE_ANONYMOUS"
    assert result["webapp_execute_as"] == "USER_DEPLOYING"
    assert result["is_anonymous_webapp_running_as_deployer"] is True
    assert result["api_executable_access"] is None
    assert result["parent_id"] is None
    assert FAKE_DEPLOYMENT_ID not in repr(result)


def test_transform_domain_user_accessing():
    result = transform_apps_script_project(
        "user-2", PROJECT_DOMAIN_USER, DEPLOYMENTS_DOMAIN_USER
    )
    assert result["versioned_deployment_count"] == 1
    assert result["webapp_access"] == "DOMAIN"
    assert result["webapp_execute_as"] == "USER_ACCESSING"
    assert result["is_anonymous_webapp_running_as_deployer"] is False


def test_transform_widest_access_and_api_executable():
    result = transform_apps_script_project(
        "user-2", PROJECT_MULTI_DEPLOY, DEPLOYMENTS_MULTI_DEPLOY
    )
    assert result["versioned_deployment_count"] == 2
    assert result["webapp_access"] == "ANYONE"
    assert result["webapp_execute_as"] == "USER_ACCESSING"
    assert result["is_anonymous_webapp_running_as_deployer"] is False
    assert result["api_executable_access"] == "DOMAIN"


def test_transform_tie_prefers_user_deploying():
    deployments = [
        {
            "deploymentId": "FAKE-TIE-1",
            "deploymentConfig": {"versionNumber": 1},
            "entryPoints": [
                {
                    "entryPointType": "WEB_APP",
                    "webApp": {
                        "url": "https://script.google.com/macros/s/FAKE-TIE-1/exec",
                        "entryPointConfig": {
                            "access": "ANYONE_ANONYMOUS",
                            "executeAs": "USER_ACCESSING",
                        },
                    },
                }
            ],
        },
        {
            "deploymentId": "FAKE-TIE-2",
            "deploymentConfig": {"versionNumber": 2},
            "entryPoints": [
                {
                    "entryPointType": "WEB_APP",
                    "webApp": {
                        "url": "https://script.google.com/macros/s/FAKE-TIE-2/exec",
                        "entryPointConfig": {
                            "access": "ANYONE_ANONYMOUS",
                            "executeAs": "USER_DEPLOYING",
                        },
                    },
                }
            ],
        },
    ]
    result = transform_apps_script_project("user-1", PROJECT_ANON_OWNER, deployments)
    assert result["webapp_access"] == "ANYONE_ANONYMOUS"
    assert result["webapp_execute_as"] == "USER_DEPLOYING"
    assert result["is_anonymous_webapp_running_as_deployer"] is True


def test_transform_no_deployments():
    result = transform_apps_script_project(
        "user-1", PROJECT_NO_DEPLOYMENTS, DEPLOYMENTS_NONE
    )
    assert result["versioned_deployment_count"] == 0
    assert result["webapp_access"] is None
    assert result["webapp_execute_as"] is None
    assert result["is_anonymous_webapp_running_as_deployer"] is False
    assert result["api_executable_access"] is None


@patch("cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.load_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script._get_active_users_for_tenant")
def test_sync_skips_oauth_credentials(mock_get_users, mock_load, mock_cleanup, caplog):
    oauth_creds = MagicMock(spec=OAuth2Credentials)
    with caplog.at_level(
        logging.INFO, logger="cartography.intel.googleworkspace.apps_script"
    ):
        sync_googleworkspace_apps_script(
            MagicMock(),
            oauth_creds,
            123,
            {"UPDATE_TAG": 123, "CUSTOMER_ID": "ABC123CD"},
        )

    mock_get_users.assert_not_called()
    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any("Skipping Apps Script sync" in r.getMessage() for r in caplog.records)


@patch("cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.load_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.googleapiclient.discovery.build")
@patch(
    "cartography.intel.googleworkspace.apps_script._get_active_users_for_tenant",
    return_value=[{"id": "user-1", "primary_email": "mbsimpson@simpson.corp"}],
)
def test_sync_unauthorized_client_on_first_user_skips_all(
    _mock_get_users, mock_build, mock_load, mock_cleanup, caplog
):
    drive_mock = MagicMock()
    drive_mock.files.return_value.list.return_value.execute.side_effect = RefreshError(
        "unauthorized_client: Client is unauthorized to retrieve access tokens"
    )
    mock_build.side_effect = [drive_mock]

    with caplog.at_level(
        logging.INFO, logger="cartography.intel.googleworkspace.apps_script"
    ):
        sync_googleworkspace_apps_script(
            MagicMock(),
            _make_service_account_creds(),
            123,
            {"UPDATE_TAG": 123, "CUSTOMER_ID": "ABC123CD"},
        )

    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()
    info_text = " ".join(r.getMessage() for r in caplog.records)
    assert "drive.metadata.readonly" in info_text
    assert "script.projects.readonly" in info_text
    assert "script.deployments.readonly" in info_text


@patch("cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.load_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.googleapiclient.discovery.build")
@patch(
    "cartography.intel.googleworkspace.apps_script._get_active_users_for_tenant",
    return_value=[
        {"id": "user-1", "primary_email": "mbsimpson@simpson.corp"},
        {"id": "user-2", "primary_email": "hjsimpson@simpson.corp"},
    ],
)
def test_sync_one_user_403_loads_others_and_skips_cleanup(
    _mock_get_users, mock_build, mock_load, mock_cleanup, caplog
):
    drive_user1 = MagicMock()
    drive_user1.files.return_value.list.return_value.execute.side_effect = (
        _make_http_error(403)
    )

    drive_user2 = MagicMock()
    drive_user2.files.return_value.list.return_value.execute.return_value = {
        "files": [{"id": "script-domain-user-3"}],
    }
    script_user2 = MagicMock()
    script_user2.projects.return_value.get.return_value.execute.return_value = (
        PROJECT_DOMAIN_USER
    )
    script_user2.projects.return_value.deployments.return_value.list.return_value.execute.return_value = {
        "deployments": DEPLOYMENTS_DOMAIN_USER,
    }

    mock_build.side_effect = [drive_user1, drive_user2, script_user2]

    with (
        caplog.at_level(
            logging.DEBUG, logger="cartography.intel.googleworkspace.apps_script"
        ),
        patch(
            "cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects_of_users"
        ) as mock_scoped_cleanup,
    ):
        sync_googleworkspace_apps_script(
            MagicMock(),
            _make_service_account_creds(),
            123,
            {"UPDATE_TAG": 123, "CUSTOMER_ID": "ABC123CD"},
        )

    # Only user-2 was read completely, so only user-2's stale projects may be removed
    mock_scoped_cleanup.assert_called_once()
    assert mock_scoped_cleanup.call_args[0][1] == ["user-2"]

    mock_load.assert_called_once()
    loaded_data = mock_load.call_args[0][1]
    assert len(loaded_data) == 1
    assert loaded_data[0]["id"] == "script-domain-user-3"
    assert loaded_data[0]["owner_user_id"] == "user-2"

    mock_cleanup.assert_not_called()
    assert any(
        "user-1" in r.getMessage() and "mbsimpson@simpson.corp" not in r.getMessage()
        for r in caplog.records
        if r.levelno == logging.DEBUG
    )
    assert any(
        r.levelno == logging.WARNING and "cleanup" in r.getMessage().lower()
        for r in caplog.records
    )


@patch("cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.load_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.googleapiclient.discovery.build")
@patch(
    "cartography.intel.googleworkspace.apps_script._get_active_users_for_tenant",
    return_value=[{"id": "user-2", "primary_email": "hjsimpson@simpson.corp"}],
)
def test_sync_drive_and_deployments_pagination(
    _mock_get_users, mock_build, mock_load, mock_cleanup
):
    drive_mock = MagicMock()
    drive_mock.files.return_value.list.return_value.execute.side_effect = [
        {"files": [{"id": "script-multi-deploy-4"}], "nextPageToken": "drive-page-2"},
        {"files": [{"id": "script-no-deploy-5"}]},
    ]

    script_mock = MagicMock()
    script_mock.projects.return_value.get.return_value.execute.side_effect = [
        PROJECT_MULTI_DEPLOY,
        PROJECT_NO_DEPLOYMENTS,
    ]
    script_mock.projects.return_value.deployments.return_value.list.return_value.execute.side_effect = [
        {"deployments": [DEPLOYMENTS_MULTI_DEPLOY[0]], "nextPageToken": "dep-page-2"},
        {"deployments": [DEPLOYMENTS_MULTI_DEPLOY[1]]},
        {"deployments": []},
    ]

    mock_build.side_effect = [drive_mock, script_mock]

    sync_googleworkspace_apps_script(
        MagicMock(),
        _make_service_account_creds(),
        123,
        {"UPDATE_TAG": 123, "CUSTOMER_ID": "ABC123CD"},
    )

    mock_load.assert_called_once()
    loaded_data = mock_load.call_args[0][1]
    assert len(loaded_data) == 2
    by_id = {item["id"]: item for item in loaded_data}
    assert by_id["script-multi-deploy-4"]["versioned_deployment_count"] == 2
    assert by_id["script-multi-deploy-4"]["webapp_access"] == "ANYONE"
    assert by_id["script-multi-deploy-4"]["api_executable_access"] == "DOMAIN"
    assert by_id["script-no-deploy-5"]["versioned_deployment_count"] == 0

    mock_cleanup.assert_called_once()


def _make_google_error(
    status: int, message: str, reason: str | None = None
) -> HttpError:
    resp = MagicMock()
    resp.status = status
    resp.reason = "Error"
    error: dict = {"code": status, "message": message, "status": "PERMISSION_DENIED"}
    if reason is not None:
        error["details"] = [
            {"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": reason}
        ]
    return HttpError(resp=resp, content=json.dumps({"error": error}).encode())


_USER_API_OFF_MESSAGE = (
    "User has not enabled the Apps Script API. Enable it by visiting "
    "https://script.google.com/home/usersettings then retry."
)


def _drive_listing(script_ids: list[str]) -> MagicMock:
    drive = MagicMock()
    drive.files.return_value.list.return_value.execute.return_value = {
        "files": [{"id": script_id} for script_id in script_ids],
    }
    return drive


def _script_with_project(project: dict, deployments: list) -> MagicMock:
    script = MagicMock()
    script.projects.return_value.get.return_value.execute.return_value = project
    script.projects.return_value.deployments.return_value.list.return_value.execute.return_value = {
        "deployments": deployments,
    }
    return script


_TWO_USERS = [
    {"id": "user-1", "primary_email": "mbsimpson@simpson.corp"},
    {"id": "user-2", "primary_email": "hjsimpson@simpson.corp"},
]


@patch("cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.load_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.googleapiclient.discovery.build")
@patch(
    "cartography.intel.googleworkspace.apps_script._get_active_users_for_tenant",
    return_value=_TWO_USERS,
)
def test_sync_user_without_apps_script_api_setting_keeps_that_users_projects(
    _mock_get_users, mock_build, mock_load, mock_cleanup
):
    # Arrange: user-1 never turned on the per-user Apps Script API setting
    script_user1 = MagicMock()
    script_user1.projects.return_value.get.return_value.execute.side_effect = (
        _make_google_error(403, _USER_API_OFF_MESSAGE)
    )
    mock_build.side_effect = [
        _drive_listing(["script-a", "script-b"]),
        script_user1,
        _drive_listing(["script-domain-user-3"]),
        _script_with_project(PROJECT_DOMAIN_USER, DEPLOYMENTS_DOMAIN_USER),
    ]

    # Act
    with patch(
        "cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects_of_users"
    ) as mock_scoped_cleanup:
        sync_googleworkspace_apps_script(
            MagicMock(),
            _make_service_account_creds(),
            123,
            {"UPDATE_TAG": 123, "CUSTOMER_ID": "ABC123CD"},
        )

    # Assert: the setting blocks every project of user-1, so only one call is made
    assert script_user1.projects.return_value.get.return_value.execute.call_count == 1
    loaded_data = mock_load.call_args[0][1]
    assert [item["id"] for item in loaded_data] == ["script-domain-user-3"]
    # user-1's projects could not be read, so they must not be cleaned up
    mock_cleanup.assert_not_called()
    mock_scoped_cleanup.assert_called_once()
    assert mock_scoped_cleanup.call_args[0][1] == ["user-2"]


@patch("cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.load_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.googleapiclient.discovery.build")
@patch(
    "cartography.intel.googleworkspace.apps_script._get_active_users_for_tenant",
    return_value=[{"id": "user-2", "primary_email": "hjsimpson@simpson.corp"}],
)
def test_sync_project_deleted_after_listing_still_allows_cleanup(
    _mock_get_users, mock_build, mock_load, mock_cleanup
):
    # Arrange
    script = MagicMock()
    script.projects.return_value.get.return_value.execute.side_effect = [
        _make_http_error(404),
        PROJECT_DOMAIN_USER,
    ]
    script.projects.return_value.deployments.return_value.list.return_value.execute.return_value = {
        "deployments": DEPLOYMENTS_DOMAIN_USER,
    }
    mock_build.side_effect = [
        _drive_listing(["script-deleted", "script-domain-user-3"]),
        script,
    ]

    # Act
    sync_googleworkspace_apps_script(
        MagicMock(),
        _make_service_account_creds(),
        123,
        {"UPDATE_TAG": 123, "CUSTOMER_ID": "ABC123CD"},
    )

    # Assert
    loaded_data = mock_load.call_args[0][1]
    assert [item["id"] for item in loaded_data] == ["script-domain-user-3"]
    mock_cleanup.assert_called_once()


@patch("cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.load_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.googleapiclient.discovery.build")
@patch(
    "cartography.intel.googleworkspace.apps_script._get_active_users_for_tenant",
    return_value=_TWO_USERS,
)
def test_sync_apps_script_api_disabled_in_cloud_project_skips_all(
    _mock_get_users, mock_build, mock_load, mock_cleanup, caplog
):
    # Arrange
    script = MagicMock()
    script.projects.return_value.get.return_value.execute.side_effect = _make_google_error(
        403,
        "Apps Script API has not been used in project 123 before or it is disabled.",
        reason="SERVICE_DISABLED",
    )
    mock_build.side_effect = [_drive_listing(["script-a"]), script]

    # Act
    with caplog.at_level(
        logging.WARNING, logger="cartography.intel.googleworkspace.apps_script"
    ):
        sync_googleworkspace_apps_script(
            MagicMock(),
            _make_service_account_creds(),
            123,
            {"UPDATE_TAG": 123, "CUSTOMER_ID": "ABC123CD"},
        )

    # Assert: no second user is tried, nothing is loaded or cleaned up
    assert mock_build.call_count == 2
    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any("Apps Script API" in r.getMessage() for r in caplog.records)


@patch("cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.load_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.googleapiclient.discovery.build")
@patch(
    "cartography.intel.googleworkspace.apps_script._get_active_users_for_tenant",
    return_value=[{"id": "user-2", "primary_email": "hjsimpson@simpson.corp"}],
)
def test_sync_unexpected_http_error_does_not_stop_googleworkspace_sync(
    _mock_get_users, mock_build, mock_load, mock_cleanup, caplog
):
    # Arrange
    drive = MagicMock()
    drive.files.return_value.list.return_value.execute.side_effect = _make_http_error(
        500
    )
    mock_build.side_effect = [drive]

    # Act: must not raise, so the Google Workspace sync does not fail
    with caplog.at_level(
        logging.WARNING, logger="cartography.intel.googleworkspace.apps_script"
    ):
        sync_googleworkspace_apps_script(
            MagicMock(),
            _make_service_account_creds(),
            123,
            {"UPDATE_TAG": 123, "CUSTOMER_ID": "ABC123CD"},
        )

    # Assert
    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any(r.levelno == logging.WARNING for r in caplog.records)


@patch("cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.load_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.googleapiclient.discovery.build")
@patch(
    "cartography.intel.googleworkspace.apps_script._get_active_users_for_tenant",
    return_value=_TWO_USERS,
)
def test_sync_unauthorized_client_after_failed_first_user_skips_all(
    _mock_get_users, mock_build, mock_load, mock_cleanup, caplog
):
    # Arrange: user-1 fails for another reason, so scope detection must not stop there
    drive_user1 = MagicMock()
    drive_user1.files.return_value.list.return_value.execute.side_effect = RefreshError(
        "invalid_grant: Invalid email or User ID"
    )
    drive_user2 = MagicMock()
    drive_user2.files.return_value.list.return_value.execute.side_effect = RefreshError(
        "unauthorized_client: Client is unauthorized to retrieve access tokens"
    )
    mock_build.side_effect = [drive_user1, drive_user2]

    # Act
    with caplog.at_level(
        logging.INFO, logger="cartography.intel.googleworkspace.apps_script"
    ):
        sync_googleworkspace_apps_script(
            MagicMock(),
            _make_service_account_creds(),
            123,
            {"UPDATE_TAG": 123, "CUSTOMER_ID": "ABC123CD"},
        )

    # Assert
    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any("script.projects.readonly" in r.getMessage() for r in caplog.records)


@patch("cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.load_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.googleapiclient.discovery.build")
@patch(
    "cartography.intel.googleworkspace.apps_script._get_active_users_for_tenant",
    return_value=[{"id": "user-2", "primary_email": "hjsimpson@simpson.corp"}],
)
def test_sync_project_401_skips_project_and_cleanup(
    _mock_get_users, mock_build, mock_load, mock_cleanup
):
    # Arrange
    script = MagicMock()
    script.projects.return_value.get.return_value.execute.side_effect = [
        _make_http_error(401),
        PROJECT_DOMAIN_USER,
    ]
    script.projects.return_value.deployments.return_value.list.return_value.execute.return_value = {
        "deployments": DEPLOYMENTS_DOMAIN_USER,
    }
    mock_build.side_effect = [
        _drive_listing(["script-unauthorized", "script-domain-user-3"]),
        script,
    ]

    # Act
    with patch(
        "cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects_of_users"
    ) as mock_scoped_cleanup:
        sync_googleworkspace_apps_script(
            MagicMock(),
            _make_service_account_creds(),
            123,
            {"UPDATE_TAG": 123, "CUSTOMER_ID": "ABC123CD"},
        )

    # Assert: no user was read completely, so nothing is cleaned up
    loaded_data = mock_load.call_args[0][1]
    assert [item["id"] for item in loaded_data] == ["script-domain-user-3"]
    mock_cleanup.assert_not_called()
    mock_scoped_cleanup.assert_not_called()


@patch("cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.load_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.googleapiclient.discovery.build")
@patch(
    "cartography.intel.googleworkspace.apps_script._get_active_users_for_tenant",
    return_value=_TWO_USERS,
)
def test_sync_drive_api_disabled_in_cloud_project_skips_all(
    _mock_get_users, mock_build, mock_load, mock_cleanup, caplog
):
    # Arrange: the Drive listing of the first user reports the API as disabled
    drive = MagicMock()
    drive.files.return_value.list.return_value.execute.side_effect = _make_google_error(
        403,
        "Google Drive API has not been used in project 123 before or it is disabled.",
        reason="SERVICE_DISABLED",
    )
    mock_build.side_effect = [drive]

    # Act
    with caplog.at_level(
        logging.WARNING, logger="cartography.intel.googleworkspace.apps_script"
    ):
        sync_googleworkspace_apps_script(
            MagicMock(),
            _make_service_account_creds(),
            123,
            {"UPDATE_TAG": 123, "CUSTOMER_ID": "ABC123CD"},
        )

    # Assert: no second user is tried and no script client is built
    assert mock_build.call_count == 1
    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any("Drive API" in r.getMessage() for r in caplog.records)


@patch("cartography.intel.googleworkspace.apps_script.cleanup_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.load_apps_script_projects")
@patch("cartography.intel.googleworkspace.apps_script.googleapiclient.discovery.build")
@patch(
    "cartography.intel.googleworkspace.apps_script._get_active_users_for_tenant",
    return_value=[{"id": "user-1", "primary_email": "mbsimpson@simpson.corp"}],
)
def test_sync_skips_script_client_when_user_has_no_scripts(
    _mock_get_users, mock_build, mock_load, mock_cleanup
):
    # Arrange
    mock_build.side_effect = [_drive_listing([])]

    # Act
    sync_googleworkspace_apps_script(
        MagicMock(),
        _make_service_account_creds(),
        123,
        {"UPDATE_TAG": 123, "CUSTOMER_ID": "ABC123CD"},
    )

    # Assert: only the Drive client is built, and the user still counts as read
    assert mock_build.call_count == 1
    assert mock_build.call_args[0][0] == "drive"
    mock_load.assert_called_once()
    assert mock_load.call_args[0][1] == []
    mock_cleanup.assert_called_once()
