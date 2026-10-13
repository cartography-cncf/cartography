from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from google.api_core.exceptions import NotFound

from cartography.intel.gcp.artifact_registry.artifact import get_apt_artifacts
from cartography.intel.gcp.artifact_registry.artifact import get_go_modules
from cartography.intel.gcp.artifact_registry.artifact import get_yum_artifacts


def _make_os_package_client(package_name: str, version_name: str) -> MagicMock:
    client = MagicMock()
    package_resource_name = f"projects/test-project/locations/us-east1/repositories/repo/packages/{package_name}"
    client.list_packages.return_value = [
        SimpleNamespace(
            name=package_resource_name,
            data={
                "name": package_resource_name,
                "displayName": package_name,
            },
        )
    ]
    client.list_versions.return_value = [
        SimpleNamespace(
            name=f"{package_resource_name}/versions/{version_name}",
            data={
                "name": f"{package_resource_name}/versions/{version_name}",
                "createTime": "2024-01-06T00:00:00Z",
                "updateTime": "2024-01-06T00:00:00Z",
            },
        )
    ]
    return client


def _proto_message_to_dict(message):
    return message.data


@pytest.fixture(autouse=True)
def proto_message_to_dict(monkeypatch):
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.artifact.proto_message_to_dict",
        _proto_message_to_dict,
    )


@pytest.mark.parametrize(
    "getter,package_name,version_name,expected_version_name,expected_versions_parent",
    [
        (
            get_apt_artifacts,
            "curl",
            "7.88.1",
            "projects/test-project/locations/us-east1/repositories/repo/packages/curl/versions/7.88.1",
            "projects/test-project/locations/us-east1/repositories/repo/packages/curl",
        ),
        (
            get_yum_artifacts,
            "bash",
            "5.2.26",
            "projects/test-project/locations/us-east1/repositories/repo/packages/bash/versions/5.2.26",
            "projects/test-project/locations/us-east1/repositories/repo/packages/bash",
        ),
        (
            get_go_modules,
            "example.com/foo",
            "v1.2.3",
            "projects/test-project/locations/us-east1/repositories/repo/packages/example.com/foo/versions/v1.2.3",
            "projects/test-project/locations/us-east1/repositories/repo/packages/example.com/foo",
        ),
    ],
    ids=["apt", "yum", "go"],
)
def test_get_os_package_artifacts_uses_packages_and_versions(
    getter,
    package_name,
    version_name,
    expected_version_name,
    expected_versions_parent,
):
    # Arrange
    client = _make_os_package_client(package_name, version_name)

    # Act
    artifacts = getter(
        client,
        "projects/test-project/locations/us-east1/repositories/repo",
    )

    # Assert
    assert artifacts == [
        {
            "name": expected_version_name,
            "createTime": "2024-01-06T00:00:00Z",
            "updateTime": "2024-01-06T00:00:00Z",
            "packageName": package_name,
        }
    ]
    client.list_packages.assert_called_once_with(
        parent="projects/test-project/locations/us-east1/repositories/repo",
    )
    client.list_versions.assert_called_once_with(
        parent=expected_versions_parent,
    )


def test_get_go_modules_skips_package_deleted_before_versions_list():
    client = MagicMock()
    deleted_package = SimpleNamespace(
        name="projects/test-project/locations/us-east1/repositories/repo/packages/deleted",
        data={
            "name": "projects/test-project/locations/us-east1/repositories/repo/packages/deleted",
            "displayName": "deleted",
        },
    )
    kept_package = SimpleNamespace(
        name="projects/test-project/locations/us-east1/repositories/repo/packages/kept",
        data={
            "name": "projects/test-project/locations/us-east1/repositories/repo/packages/kept",
            "displayName": "kept",
        },
    )
    kept_version = SimpleNamespace(
        name="projects/test-project/locations/us-east1/repositories/repo/packages/kept/versions/v1.0.0",
        data={
            "name": "projects/test-project/locations/us-east1/repositories/repo/packages/kept/versions/v1.0.0",
            "createTime": "2024-01-06T00:00:00Z",
            "updateTime": "2024-01-06T00:00:00Z",
        },
    )
    client.list_packages.return_value = [deleted_package, kept_package]
    client.list_versions.side_effect = [NotFound("deleted"), [kept_version]]

    modules = get_go_modules(
        client,
        "projects/test-project/locations/us-east1/repositories/repo",
    )

    assert modules == [
        {
            "name": "projects/test-project/locations/us-east1/repositories/repo/packages/kept/versions/v1.0.0",
            "createTime": "2024-01-06T00:00:00Z",
            "updateTime": "2024-01-06T00:00:00Z",
            "packageName": "kept",
        }
    ]
