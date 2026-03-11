from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import patch

from google.api_core.exceptions import GoogleAPICallError

from cartography.intel.gcp.artifact_registry.artifact import get_apt_artifacts
from cartography.intel.gcp.artifact_registry.artifact import get_yum_artifacts


def test_get_apt_artifacts_flattens_package_versions():
    client = MagicMock()
    client.list_packages.return_value = [
        {
            "name": "projects/test-project/locations/us-east1/repositories/apt-repo/packages/curl",
            "displayName": "curl",
        }
    ]
    client.list_versions.return_value = [
        {
            "name": "projects/test-project/locations/us-east1/repositories/apt-repo/packages/curl/versions/7.88.1",
            "createTime": "2024-01-06T00:00:00Z",
            "updateTime": "2024-01-06T00:00:00Z",
        }
    ]

    artifacts = get_apt_artifacts(
        client,
        "projects/test-project/locations/us-east1/repositories/apt-repo",
    )

    assert artifacts == [
        {
            "name": "projects/test-project/locations/us-east1/repositories/apt-repo/packages/curl/versions/7.88.1",
            "createTime": "2024-01-06T00:00:00Z",
            "updateTime": "2024-01-06T00:00:00Z",
            "packageName": "curl",
        }
    ]
    client.list_versions.assert_called_once_with(
        parent="projects/test-project/locations/us-east1/repositories/apt-repo/packages/curl"
    )


def test_get_yum_artifacts_returns_none_on_permission_issue():
    client = MagicMock()
    client.list_packages.side_effect = GoogleAPICallError("permission denied")

    artifacts = get_yum_artifacts(
        client,
        "projects/test-project/locations/us-east1/repositories/yum-repo",
    )

    assert artifacts is None


def test_go_modules_compatibility_client_is_built_once():
    mock_generated_client = MagicMock()
    repositories = [
        {
            "name": "projects/test-project/locations/us-central1/repositories/go-repo",
            "format": "GO",
        },
        {
            "name": "projects/test-project/locations/us-central1/repositories/second-go-repo",
            "format": "GO",
        },
    ]

    with (
        patch(
            "cartography.intel.gcp.artifact_registry.artifact.build_client",
            return_value=MagicMock(),
        ) as mock_build_client,
        patch(
            "cartography.intel.gcp.artifact_registry.artifact.get_go_modules",
            return_value=[],
        ) as mock_get_go_modules,
    ):
        from cartography.intel.gcp.artifact_registry.artifact import (
            sync_artifact_registry_artifacts,
        )

        result = sync_artifact_registry_artifacts(
            neo4j_session=MagicMock(),
            client=mock_generated_client,
            repositories=repositories,
            project_id="test-project",
            update_tag=123,
            common_job_parameters={"UPDATE_TAG": 123, "PROJECT_ID": "test-project"},
            credentials=MagicMock(),
        )

    assert result == []
    mock_build_client.assert_called_once_with(
        "artifactregistry",
        "v1",
        credentials=ANY,
    )
    assert mock_get_go_modules.call_count == 2
